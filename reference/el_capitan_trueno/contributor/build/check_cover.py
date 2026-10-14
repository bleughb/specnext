# Cover check over the RZX: at every screen copy, every buffer pixel the figures changed (buffer just
# before the copy vs the scenery after the game's restore) must lie under an opaque sprite pixel, as
# the hooks would show them (figure list from 0x82DF, pattern memory of 128 4-bit patterns with the
# same bump allocation / flush as asm/trueno_hooks.asm, blink phase, 128 sprites). Uncovered pixels
# show as figure pixels in scenery colours on the Next (the "white flashes").
# Usage: python check_cover.py RZX [--stop N] [--dump FRAME out.png]   (--dump: picture of the first bad render from FRAME)
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..', 'tk', 'nexclash-0.1.4'))
from nexclash import simrun

BUF, LEN = 0xF2E0, 3360
SD = open(os.path.join(HERE, 'shapedir.bin'), 'rb').read()
FD = open(os.path.join(HERE, 'fdir.bin'), 'rb').read()
BL = open(os.path.join(HERE, 'blink.bin'), 'rb').read()
PAT = open(os.path.join(HERE, 'patterns.bin'), 'rb').read()
s8 = lambda b: b - 256 if b > 127 else b


def opaque(page, first, cols, rows):
    """Opaque pixels of a shape's patterns: set of (x, y) in its cols*16 x rows*16 box."""
    out = set()
    for y in range(rows * 16):
        for x in range(cols * 16):
            n = first + (y // 16) * cols + x // 16
            b = PAT[page * 8192 + n * 128 + (y % 16) * 8 + (x % 16) // 2]
            if (b >> 4 if x % 2 == 0 else b & 15):
                out.add((x, y))
    return out


OPQ = {}


class Model:
    """The hooks' state: residency (normal / hit), next free pattern, blink counter."""

    def __init__(self):
        self.res, self.resf, self.next, self.blk = {}, {}, 0, 0

    def key(self, f, fl):
        if fl & 2 and not (BL[f] and self.blk & 1):
            return 'f'
        return 'n'

    def ensure(self, f, kind):
        table = self.resf if kind == 'f' else self.res
        if f in table or SD[8 * f] == 0xFF:
            return True
        n = SD[8 * f + 2] * SD[8 * f + 3]
        if self.next + n > 128:
            return False
        table[f] = self.next
        self.next += n
        return True

    def commit(self, figs):
        self.blk += 1
        ok = all(self.ensure(f, self.key(f, fl)) for f, x, y, fl in figs)
        flushed = False
        if not ok:
            self.res, self.resf, self.next = {}, {}, 0
            flushed = True
            for f, x, y, fl in figs:
                if not self.ensure(f, self.key(f, fl)):
                    break
        cover, s, missing = set(), 0, []
        for f, x, y, fl in figs:
            kind = self.key(f, fl)
            table = self.resf if kind == 'f' else self.res
            if f not in table:
                missing.append((f, 'no shape' if SD[8 * f] == 0xFF else 'not resident'))
                continue
            page, first, cols, rows, dx, dy, pads, mdx = SD[8 * f:8 * f + 8]
            facing, first = first >> 7, first & 0x3F
            if kind == 'f':
                page, first = FD[2 * f], FD[2 * f + 1]
            k = (page, first, cols, rows)
            if k not in OPQ:
                OPQ[k] = opaque(*k)
            mx = (fl >> 7 ^ facing) & 1
            my = fl >> 6 & 1
            bx = 4 * x - 128 + s8(mdx if mx else dx) - (pads & 15 if mx else 0)
            by = y - 68 + s8(dy) - (pads >> 4 if my else 0)
            W, H = cols * 16, rows * 16
            for px, py in OPQ[k]:
                if s >= 128:
                    break
                cover.add((bx + (W - 1 - px if mx else px), by + (H - 1 - py if my else py)))
            s += cols * rows
        return cover, missing, flushed


class H:
    sim = None
    n = 0
    figs = []
    b1 = None
    model = Model()
    renders = 0
    bad = collections.Counter()
    examples = []
    flushes = 0

    def on_sim(self, sim):
        self.sim = sim

    def on_frame(self, n):
        self.n = n

    def before(self, pc):
        m = self.sim.memory
        if pc == 0x82DF:
            r = self.sim.registers
            ix = r[8] * 256 + r[9]
            if m[ix + 3] & 1 and len(self.figs) < 64:
                self.figs.append((m[ix], m[ix + 1], m[ix + 2], m[ix + 3]))
        elif pc == 0x886F:                              # a render is copied now
            self.b1 = bytes(m[BUF:BUF + LEN]) if m[0xE60B] != 34 else None
            self.mode34 = m[0xE60B] == 34
            self.cm = self.model.commit(self.figs)
            self.cfigs, self.figs = self.figs, []
        elif pc == 0xA1F1 and self.b1 is not None:      # restored: compare
            b2 = bytes(m[BUF:BUF + LEN])
            cover, missing, flushed = self.cm
            self.renders += 1
            self.flushes += flushed
            unc = []
            for i, (a, b) in enumerate(zip(self.b1, b2)):
                if a != b:
                    y, c = divmod(i, 30)
                    for bit in range(8):
                        if (a ^ b) & (0x80 >> bit) and (c * 8 + bit, y) not in cover:
                            unc.append((c * 8 + bit, y))
            if unc:
                if DUMP and self.n >= DUMP[0] and not getattr(self, 'dumped', False):
                    self.dumped = True
                    dump(self.b1, b2, cover, DUMP[1])
                    print('dumped frame', self.n, 'figures', self.cfigs, 'uncovered', len(unc))
                why = ','.join(sorted({w for f, w in missing})) or 'position'
                self.bad[why] += 1
                if len(self.examples) < 30:
                    self.examples.append((self.n, len(unc), unc[:3], missing, self.cfigs))
            self.b1 = None


def dump(b1, b2, cover, path):
    sys.path.insert(0, os.path.join(HERE, '..', '..', '_docs', 'lib'))
    from PIL import Image
    im = Image.new('RGB', (240, 112))
    for i, (a, b) in enumerate(zip(b1, b2)):
        y, c = divmod(i, 30)
        for bit in range(8):
            x, m = c * 8 + bit, 0x80 >> bit
            if (a ^ b) & m:
                im.putpixel((x, y), (0, 255, 0) if (x, y) in cover else (255, 0, 0))
            elif (x, y) in cover:
                im.putpixel((x, y), (90, 90, 90))
            elif b & m:
                im.putpixel((x, y), (40, 40, 120))
    im.resize((960, 448), Image.NEAREST).save(path)


DUMP = (int(sys.argv[sys.argv.index('--dump') + 1]), sys.argv[sys.argv.index('--dump') + 2]) if '--dump' in sys.argv else None
stop = int(sys.argv[sys.argv.index('--stop') + 1]) if '--stop' in sys.argv else None
h = H()
simrun.play_rzx(sys.argv[1], h, stop=stop)
print('frames %d, renders %d, pattern flushes %d, renders with uncovered pixels %d' % (
    h.n, h.renders, h.flushes, sum(h.bad.values())))
print('by cause:', dict(h.bad))
for e in h.examples:
    print('frame %d: %d px uncovered, e.g. %s; missing %s; figures %s' % e)
