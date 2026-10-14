# Debug one render: free-run a snapshot to the next screen copy, recording the buffer before/after every
# 0x82DF call; for each figure, the pixels it changed and how many of them the sprite (check_cover's
# geometry, no residency limits) leaves uncovered. Usage: python debug_render.py SNAP.z80
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..', 'tk', 'nexclash-0.1.4'))
from nexclash import simrun

BUF, LEN = 0xF2E0, 3360
SD = open(os.path.join(HERE, 'shapedir.bin'), 'rb').read()
PAT = open(os.path.join(HERE, 'patterns.bin'), 'rb').read()
s8 = lambda b: b - 256 if b > 127 else b


def sprite(f, x, y, fl):
    page, first, cols, rows, dx, dy, pads, mdx = SD[8 * f:8 * f + 8]
    facing, first = first >> 7, first & 0x3F
    mx, my = (fl >> 7 ^ facing) & 1, fl >> 6 & 1
    bx = 4 * x - 128 + s8(mdx if mx else dx) - (pads & 15 if mx else 0)
    by = y - 68 + s8(dy) - (pads >> 4 if my else 0)
    W, H = cols * 16, rows * 16
    out = set()
    for py in range(H):
        for px in range(W):
            n = first + (py // 16) * cols + px // 16
            b = PAT[page * 8192 + n * 128 + (py % 16) * 8 + (px % 16) // 2]
            if b >> 4 if px % 2 == 0 else b & 15:
                out.add((bx + (W - 1 - px if mx else px), by + (H - 1 - py if my else py)))
    return out


class Done(Exception):
    pass


class H:
    sim = None
    pend = None
    calls = []
    state = 0

    def on_sim(self, sim):
        self.sim = sim

    def before(self, pc):
        m, r = self.sim.memory, self.sim.registers
        if self.pend and pc == self.pend[0]:
            self.calls.append(self.pend[1:] + (bytes(m[BUF:BUF + LEN]),))
            self.pend = None
        if pc == 0x82DF and self.state == 1:
            ix = r[8] * 256 + r[9]
            sp = r[12]
            self.pend = (m[sp] | m[sp + 1] << 8, tuple(m[ix:ix + 4]), r[10] * 256 + r[11], bytes(m[BUF:BUF + LEN]))
        elif pc == 0xA1F1 and self.state == 0:
            self.state = 1                      # a render starts after this copy
            self.calls = []
        elif pc == 0x886F and self.state == 1:
            raise Done


h = H()
try:
    simrun.free_run(sys.argv[1], 400, h)
except Done:
    pass
for desc, iy, before, after in h.calls:
    f, x, y, fl = desc
    if not fl & 1:
        continue
    changed = {(c * 8 + bit, i // 30) for i, (a, b) in enumerate(zip(before, after)) if a != b
               for c in [i % 30] for bit in range(8) if (a ^ b) & (0x80 >> bit)}
    cov = sprite(f, x, y, fl)
    unc = sorted(changed - cov)
    print('frame %3d x %3d y %3d flags %02X IY %04X: changed %4d, uncovered %3d %s' % (
        f, x, y, fl, iy, len(changed), len(unc), unc[:6]))
    if unc and '--ascii' in sys.argv:
        pts = changed | cov
        x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
        y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
        print('   x from %d (box 4x-128 = %d)' % (x0, 4 * x - 128))
        for yy in range(y0, y1 + 1):
            print('   ' + ''.join('X' if (xx, yy) in changed and (xx, yy) not in cov else
                                  '#' if (xx, yy) in changed else 'o' if (xx, yy) in cov else '.'
                                  for xx in range(x0, x1 + 1)))


if '--identify' in sys.argv:
    import json
    shapes = {}
    for sh in json.load(open(os.path.join(HERE, 'shapes.json'))):
        shapes.setdefault(sh['frame'], sh)
    for desc, iy, before, after in h.calls:
        f, x, y, fl = desc
        if not fl & 1:
            continue
        changed = {(c * 8 + bit, i // 30) for i, (a, b) in enumerate(zip(before, after)) if a != b
                   for c in [i % 30] for bit in range(8) if (a ^ b) & (0x80 >> bit)}
        best = []
        for g, sh in shapes.items():
            for mirror in (0, 1):
                m = {((sh['w'] - 1 - xx) if mirror else xx, yy) for yy in range(sh['h']) for xx in range(sh['w'])
                     if sh['mask'][yy][xx] == '1'}
                for ox in range(4 * x - 128 - 8, 4 * x - 128 + 9):
                    for oy in range(y - 68 - 4, y - 68 + 5):
                        out = sum((px - ox, py - oy) not in m for px, py in changed)
                        best.append((out, g, mirror, ox - (4 * x - 128), oy - (y - 68)))
        best.sort()
        print('figure', desc, 'best fits (outside, frame, mirror, dx, dy):', best[:4])


if '--side' in sys.argv:
    import json
    shapes = {}
    for sh in json.load(open(os.path.join(HERE, 'shapes.json'))):
        shapes.setdefault(sh['frame'], sh)
    for desc, iy, before, after in h.calls:
        f, x, y, fl = desc
        if not fl & 1 or f not in shapes:
            continue
        sh = shapes[f]
        bx, by = 4 * x - 128 + sh['dx'], y - 68 + sh['dy']
        print('figure', desc, 'box', bx, by, sh['w'], sh['h'], 'facing', sh['facing'])
        for yy in range(by - 1, by + sh['h'] + 1):
            game = ''
            for xx in range(bx - 4, bx + sh['w'] + 4):
                i, m = yy * 30 + xx // 8, 0x80 >> (xx % 8)
                a, b = before[i] & m, after[i] & m
                game += '#' if b and not a else '-' if a and not b else ('.' if not b else ',')
            spr = ''
            for xx in range(bx - 4, bx + sh['w'] + 4):
                u, v = xx - bx, yy - by
                inside = 0 <= u < sh['w'] and 0 <= v < sh['h']
                spr += '#' if inside and sh['ink'][v][u] == '1' else 'o' if inside and sh['mask'][v][u] == '1' else '.'
            print('  ', game, '  ', spr)
