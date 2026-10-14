# El Capitan Trueno: ink + mask of every figure shape, taken from the game's own plotter.
# For each shape in the catalogue (gfx_catalog.json, from gfxcat.py) the plotter 0x82DF is called in the
# simulator with a descriptor at 0xE600 on a buffer filled with 0x00 (set pixels = ink) and with 0xFF
# (cleared pixels = mask). The result is relative to the descriptor's position:
#   buffer x = 4 * (+1) - 128 + dx, buffer y = (+2) - 68 + dy  (box w x h, unmirrored)
# Output shapes.json: [{frame, key, attr, facing, dx, dy, w, h, ink, mask}] (ink/mask = rows of '0'/'1').
# Usage: python shapes.py   (from anywhere; SkoolKit from trueno/lib)
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
import skoolkit.rzxplay as rz
from skoolkit.simulator import Simulator

RZX = os.path.join(HERE, '..', 'trueno1.rzx')
FRAMES = 5000                           # the in-game state after this many frames of the recording (was the
                                        # snapshot f5000.z80; the title snapshot is before the game's init)
CATALOGUE = os.path.join(HERE, 'gfx_catalog.json')
OUT = os.path.join(HERE, 'shapes.json')
COPY_DUE, RESTORED = 0x886F, 0xA1F1     # ISR: before the screen copy / back in the task loop after it
PLOT = 0x82DF
BUF, BUF_LEN, ROW = 0xF2E0, 3360, 30    # window buffer: 30 bytes x 112 lines
FGMAP = 0xEF60                          # foreground cell map, 56 bytes
MODE = 0xE60B                           # 34 = clear mode
DESC = 0xE600
X0, Y0 = 40, 76                         # descriptor position used for every shape: box well inside and
                                        # cell-aligned (buffer x 32, y 8), so each graphic cell gets one attribute
ATTRS = 0xF13C                          # window attribute buffer, 30 x 14
W, H = 240, 112
IXH, IXL, SP, PC, IFF = 8, 9, 12, 24, 26


def base_state():
    """Memory and registers just after a screen copy and restore: a clean render cycle starts."""
    got, n, nf = [], [0], rz.RZXTracer.next_frame

    def next_frame(self):
        n[0] += 1
        if n[0] > FRAMES:
            got.append((list(self.simulator.memory[0:65536]), list(self.simulator.registers)))
            raise SystemExit
        return nf(self)
    rz.RZXTracer.next_frame = next_frame
    try:
        rz.main(['--quiet', '--no-screen', '--fps', '0', RZX])
    except SystemExit:
        pass
    rz.RZXTracer.next_frame = nf
    mem, regs = got[0]
    sim = Simulator(mem)
    sim.registers[:] = regs
    sim.run(stop=COPY_DUE, interrupts=True)
    sim.run(stop=RESTORED, interrupts=True)
    return mem, list(sim.registers)


def plot(base, gfx, fill, flags=None):
    """Plot one figure (frame, table entry and graphic given by gfx) on a buffer full of fill;
    flags = descriptor +3 (default: visible, facing as stored)."""
    mem0, regs0 = base
    mem = list(mem0)
    mem[BUF:BUF + BUF_LEN] = [fill] * BUF_LEN
    mem[ATTRS:ATTRS + 420] = [0xFF] * 420       # 0xFF = not painted
    mem[FGMAP:FGMAP + 56] = [0] * 56
    mem[MODE] = 0
    e = 0xE290 + 4 * gfx['frame']
    mem[e] = gfx['flags']
    mem[gfx['addr']:gfx['addr'] + len(gfx['data'])] = gfx['data']
    # descriptor facing = the stored facing, so the game does not mirror the graphic in place
    mem[DESC:DESC + 8] = [gfx['frame'], X0, Y0, 0x01 | gfx['flags'] & 0x80 if flags is None else flags, 0, 0, 0, 0]
    sim = Simulator(mem, None)
    r = sim.registers
    r[:] = regs0
    r[IXH], r[IXL] = DESC >> 8, DESC & 255
    sp = 0xEEC0
    mem[sp] = mem[sp + 1] = 0                   # return to 0x0000 = stop
    r[SP], r[PC], r[IFF] = sp, PLOT, 0
    sim.run(stop=0)
    if flags is None and bytes(mem[gfx['addr']:gfx['addr'] + len(gfx['data'])]) != gfx['data']:
        raise SystemExit('frame %d: graphic changed while plotting (mirrored in place?)' % gfx['frame'])
    return mem[BUF:BUF + BUF_LEN], mem[ATTRS:ATTRS + 420]


def bit(b, x, y):
    return b[y * ROW + x // 8] >> (7 - x % 8) & 1


def main():
    cat = json.load(open(CATALOGUE))
    base = base_state()
    shapes = []
    rev = [int('{:08b}'.format(b)[::-1], 2) for b in range(256)]
    for frame, variants in sorted(cat.items(), key=lambda kv: int(kv[0])):
        frame = int(frame)
        # The graphic as the base state holds it, with its own trailing mask bytes: the game mirrors
        # the graphic AND its mask data in place, so they must come from the same state (writing the
        # catalogue's graphic over a mirrored state paired it with a mirrored mask). The catalogue
        # only confirms it is the real drawing (its most frequent variant, or that mirrored);
        # frame 32's two drawings are mirrors of each other.
        main = sorted(variants, key=lambda v: -v['changes'])[0]
        mem0 = base[0]
        e = 0xE290 + 4 * frame
        fl, hh, a = mem0[e], mem0[e + 1], mem0[e + 2] | mem0[e + 3] << 8
        w = fl & 31
        data = bytes(mem0[a:a + 1 + w * hh])
        md = bytes.fromhex(main['data'])
        mirrored = md[:1] + b''.join(bytes(rev[b] for b in reversed(md[1 + r * w:1 + (r + 1) * w])) for r in range(hh))
        real = {md, mirrored} | {bytes.fromhex(v['data']) for v in variants if v['changes'] >= 100}
        if (fl & 31, hh, a) != (main['flags'] & 31, main['height'], main['addr']) or data not in real:
            print('frame %d: the base state does not hold its real graphic' % frame)
            continue
        for v in [dict(main, flags=fl, data=data.hex())]:
            gfx = dict(frame=frame, flags=fl, addr=a, data=data)
            (b0, at), (b1, _) = plot(base, gfx, 0), plot(base, gfx, 255)
            ink = [[bit(b0, x, y) for x in range(W)] for y in range(H)]
            mask = [[ink[y][x] | (1 - bit(b1, x, y)) for x in range(W)] for y in range(H)]
            pts = [(x, y) for y in range(H) for x in range(W) if mask[y][x]]
            if not pts:
                print('frame %d: nothing drawn' % frame)
                continue
            xs, ys = zip(*pts)
            x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
            if x0 == 0 or y0 == 0 or x1 == W - 1 or y1 == H - 1:
                print('frame %d: touches the window edge, may be clipped' % frame)
            # mirrored, the game flips the graphic inside its whole byte width, so the box moves:
            # take its x from the game (descriptor facing flipped)
            fl = 0x01 | (~v['flags'] & 0x80)
            (m0, _), (m1, _) = plot(base, gfx, 0, fl), plot(base, gfx, 255, fl)
            mx0 = min(x for y in range(H) for x in range(W) if bit(m0, x, y) or not bit(m1, x, y))
            shapes.append(dict(
                frame=frame, key=v['data'][2:18], attr=gfx['data'][0], facing=v['flags'] >> 7,
                dx=x0 - (4 * X0 - 128), dy=y0 - (Y0 - 68), w=x1 - x0 + 1, h=y1 - y0 + 1,
                mdx=mx0 - (4 * X0 - 128),
                ink=[''.join(map(str, ink[y][x0:x1 + 1])) for y in range(y0, y1 + 1)],
                mask=[''.join(map(str, mask[y][x0:x1 + 1])) for y in range(y0, y1 + 1)],
                # attribute painted in the cell under each box pixel (-1 = not painted)
                cells=[[at[(y // 8) * 30 + x // 8] if at[(y // 8) * 30 + x // 8] != 0xFF else -1
                        for x in range(x0 - x0 % 8, x1 + 1, 8)] for y in range(y0 - y0 % 8, y1 + 1, 8)],
                cx=x0 % 8, cy=y0 % 8, multi=v['flags'] >> 6 & 1))
    json.dump(shapes, open(OUT, 'w'), indent=0)
    print(len(shapes), 'shapes ->', OUT)


if __name__ == '__main__':
    main()
