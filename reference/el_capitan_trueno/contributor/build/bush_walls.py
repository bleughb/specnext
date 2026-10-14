# The wall behind the bushes, computed on the PC (host's choice, 2026-10-13): the game builds a screen
# from a list of scenery objects (table 0x6914; groups nest), each leaf a scenery frame 0x80-0xD0
# plotted by 0x62BE; the bushes (frames 0x84-0x8B, one 8x8 cell each, attribute 0x44) come last and
# hide what was drawn there with black paper. The build only depends on the screen number (0xE60B):
# 0x6857 sets 0xE60D = 0 before it. Here the screen change 0x65C3 runs in the simulator twice per
# screen, normally and with the bush frames skipped; for every bush cell of the normal build (map
# 0xEF60 bit set, attribute & 0x47 = 0x44) the bush-free build gives the wall pixels and attribute.
# The bush itself comes from the host's sheet gfx/bush_tiles.png (+ .json, made by --sheet): a non-pink
# pixel is the bush (Layer 2 with priority, over the sprites), a pink one shows the wall (Layer 2
# without priority, under the sprites). Without the sheet: the old silhouette rule.
# Output build/bushwall.bin, Next pages from 60 (asm BWPAGE), read by the hooks at slot 2 (0x4000):
#   page 60  64 bytes: the page of each screen's cells, 0 = no bushes
#   page p   count, then per cell: row, column, 64 Layer 2 bytes (8 lines of 8)
# Usage: python bush_walls.py [--png out.png] [--sheet ../gfx/bush_tiles.png] [--propagate S C0 C1]
#   --propagate S C0 C1: the bush of screen S, columns C0-C1, gives its tiles to all other bush cells
#   --png: each bush screen normal | with the wall; --sheet: the host's bush sheet (+ .json)
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'nika', 'lib'))
import skoolkit.rzxplay as rz
from skoolkit.simulator import Simulator
from skoolkit.simutils import PC, SP

RZX = os.path.join(HERE, '..', 'trueno1.rzx')
FRAME = 5891                                # in the game (the .z80 is before the game's own init)
BUSH = set(range(0x84, 0x8C))
NSCR = 64
L2COL, L2NP = 16, 32                        # Layer 2 palette: colour 0-15 with / without priority
SHEET = os.path.join(HERE, '..', 'gfx', 'bush_tiles.png')


def build(ram, screen, skip=()):
    mem = bytearray(ram)
    mem[0xE60B] = screen
    sim = Simulator(mem)
    r = sim.registers
    r[SP] = 0xEEE0 - 2
    mem[r[SP]:r[SP] + 2] = b'\0\0'          # return to 0x0000 = done
    r[PC] = 0x65C3
    while r[PC]:
        if r[PC] == 0x62BE and r[0] in skip:
            sp = r[SP]
            r[PC] = mem[sp] | mem[sp + 1] << 8
            r[SP] = sp + 2
            continue
        sim.run()
    return mem


def bush_cells(mem):
    return [(r, c) for r in range(14) for c in range(30)
            if mem[0xEF60 + r * 4 + c // 8] & (0x80 >> c % 8) and mem[0xF13C + r * 30 + c] & 0x47 == 0x44]


def game_ram():
    got, n, nf = [], [0], rz.RZXTracer.next_frame

    def next_frame(self):
        n[0] += 1
        if n[0] == FRAME:
            got.append(bytearray(self.simulator.memory[0:65536]))
            raise SystemExit
        return nf(self)
    rz.RZXTracer.next_frame = next_frame
    try:
        rz.main(['--quiet', '--no-screen', '--fps', '0', RZX])
    except SystemExit:
        pass
    rz.RZXTracer.next_frame = nf
    return got[0]


def cell(mem, r, c):
    return bytes([mem[0xF13C + r * 30 + c]]) + bytes(mem[0xF2E0 + (r * 8 + y) * 30 + c] for y in range(8))


def main():
    ram = game_ram()
    shots = []
    for s in range(60):                     # screen 60 jumps away (the end)
        norm = build(ram, s)
        wall = build(ram, s, BUSH)
        cells = [(r, c) for r, c in bush_cells(norm) if cell(norm, r, c) != cell(wall, r, c)]
        if cells:                           # (screen 57: no bush frame, the colour only)
            shots.append((s, norm, wall, cells))
    if '--sheet' in sys.argv:
        sheet(shots, sys.argv[sys.argv.index('--sheet') + 1])
    if '--propagate' in sys.argv:
        a = sys.argv.index('--propagate')
        propagate(shots, *map(int, sys.argv[a + 1:a + 4]))
    drawn = read_sheet()
    table = {}                              # screen: [(row, column, 64 Layer 2 bytes)]
    for s, norm, wall, cells in shots:
        bush = drawn.get(s) or silhouette(norm, cells)
        for r, c in cells:
            a = wall[0xF13C + r * 30 + c]
            ink, paper = (a & 7) + (a >> 3 & 8), (a >> 3 & 7) + (a >> 3 & 8)
            px = bytearray()
            for i, v in enumerate(bush.get((r, c), [None] * 64)):
                b = wall[0xF2E0 + (r * 8 + i // 8) * 30 + c] & (0x80 >> i % 8)
                px.append(L2NP + (ink if b else paper) if v is None else L2COL + v)
            table.setdefault(s, []).append((r, c, bytes(px)))
        print('screen %d: %d bush cells, %s' % (s, len(cells), 'host sheet' if s in drawn else 'silhouette rule'))
    import fix_cells                        # fix cells (under the sprites; pink = see-through)
    fixes = fix_cells.fixes(ram)            # the host's sheet; a place not on it yet: no fix cells
    for s, cells in sorted(fixes.items()):
        for (r, c), px in sorted(cells.items()):
            table.setdefault(s, []).append((r, c, bytes(0xE3 if v is None else L2NP + v for v in px)))
        print('screen %d: %d fix cells' % (s, len(cells)))
    pages = [bytearray(256)]                # page 60: screen -> page (64 bytes), offset (64 words at 0x40),
    for s, cells in sorted(table.items()):  # then the blocks, packed; a block never crosses a page
        block = bytearray([len(cells)])
        for r, c, px in cells:
            block += bytes([r, c]) + px
        if len(pages[-1]) + len(block) > 8192:
            pages.append(bytearray())
        pages[0][s] = 60 + len(pages) - 1
        pages[0][0x40 + 2 * s:0x42 + 2 * s] = len(pages[-1]).to_bytes(2, 'little')
        pages[-1] += block
    head, pages = bytes(pages[0]).ljust(8192, bytes(1)), [bytes(p).ljust(8192, bytes(1)) for p in pages[1:]]
    open(os.path.join(HERE, 'bushwall.bin'), 'wb').write(bytes(head) + b''.join(pages))
    print('bushwall.bin: pages 60-%d' % (60 + len(pages)))
    if '--png' in sys.argv:
        png(shots, sys.argv[sys.argv.index('--png') + 1])


def propagate(shots, screen, c0, c1):
    """The bush cells are a few game tiles repeated (frames 0x84-0x8B, some mirrored). The sample bush
    (screen, columns c0-c1) as the host drew it gives each of its tiles; every other bush cell showing
    the same game tile (pixels + attribute) gets that drawing, on all screens; a cell showing a sample
    tile mirrored (the game plots bushes flipped too) gets the drawing mirrored. A tile drawn several ways
    in the sample: the most frequent drawing (ties: the first, top to bottom). The sheet is rewritten."""
    import json
    from collections import Counter
    from PIL import Image
    lay = json.load(open(os.path.splitext(SHEET)[0] + '.json'))
    pos = {(e['screen'], r, c): (e['x'] + (c - e['col']) * 8, e['y'] + (r - e['row']) * 8)
           for e in lay['screens'] for r, c in e['cells']}
    im = Image.open(SHEET).convert('RGB')
    key, drawings = {}, {}
    for s, norm, wall, cells in shots:
        for r, c in cells:
            key[(s, r, c)] = cell(norm, r, c)
    sample = sorted(pl for pl in key if pl[0] == screen and c0 <= pl[2] <= c1)
    for pl in sample:
        x0, y0 = pos[pl]
        drawings.setdefault(key[pl], []).append(tuple(im.getpixel((x0 + i % 8, y0 + i // 8)) for i in range(64)))
    new = {}
    for k, v in drawings.items():
        count = Counter(v)
        new[k] = max(count, key=lambda d: (count[d], -v.index(d)))
        if len(count) > 1:
            print('a sample tile drawn %d ways (%d cells): the most frequent used' % (len(count), len(v)))
    mirror = lambda k: bytes([k[0]]) + bytes(int(format(x, '08b')[::-1], 2) for x in k[1:])
    for k in set(key.values()) - set(new):
        if mirror(k) in new:
            d = new[mirror(k)]
            new[k] = tuple(d[y * 8 + 7 - x] for y in range(8) for x in range(8))
    n = 0
    for pl, k in key.items():
        if k in new and pl not in sample:
            x0, y0 = pos[pl]
            for i, v in enumerate(new[k]):
                im.putpixel((x0 + i % 8, y0 + i // 8), v)
            n += 1
    print('%d distinct game tiles in %d bush cells; the sample (%d cells) has %d -> %d other cells rewritten, '
          '%d keep their drawing' % (len(set(key.values())), len(key), len(sample), len(new), n,
                                     len(key) - len(sample) - n))
    im.save(SHEET)


PAL = [(0, 0, 0), (0, 0, 205), (205, 0, 0), (205, 0, 205), (0, 205, 0), (0, 205, 205), (205, 205, 0),
       (205, 205, 205), (0, 0, 0), (0, 0, 255), (255, 0, 0), (255, 0, 255), (0, 255, 0), (0, 255, 255),
       (255, 255, 0), (255, 255, 255)]
PINK = (255, 105, 180)


def window(mem, im, x0, y0, only=None, box=(0, 0, 14, 30)):
    r0, c0, nr, nc = box
    for r in range(r0, r0 + nr):
        for c in range(c0, c0 + nc):
            if only is not None and (r, c) not in only:
                continue
            a = mem[0xF13C + r * 30 + c]
            ink, paper = PAL[(a & 7) + (a >> 3 & 8)], PAL[(a >> 3 & 7) + (a >> 3 & 8)]
            for y in range(8):
                b = mem[0xF2E0 + (r * 8 + y) * 30 + c]
                for x in range(8):
                    im.putpixel((x0 + (c - c0) * 8 + x, y0 + (r - r0) * 8 + y), ink if b & (0x80 >> x) else paper)


def silhouette(mem, cells):
    """{cell: 64 colours (0-15) or None = see-through}: the hooks' old rule (pass 2b): per pixel line,
    every run of bush cells is solid from its leftmost to its rightmost ink pixel."""
    out = {rc: [None] * 64 for rc in cells}
    cs = set(cells)
    for r in range(14):
        for y in range(8):
            c = 0
            while c < 30:
                if (r, c) not in cs:
                    c += 1
                    continue
                c0 = c
                while (r, c) in cs:
                    c += 1
                byte = lambda cc: mem[0xF2E0 + (r * 8 + y) * 30 + cc]
                xs = [cc * 8 + x for cc in range(c0, c) for x in range(8) if byte(cc) & (0x80 >> x)]
                for px in range(min(xs), max(xs) + 1) if xs else ():
                    a = mem[0xF13C + r * 30 + px // 8]
                    on = byte(px // 8) & (0x80 >> px % 8)
                    out[(r, px // 8)][y * 8 + px % 8] = (a & 7 if on else a >> 3 & 7) + (a >> 3 & 8)
    return out


def read_sheet():
    """{screen: {cell: 64 colours (0-15) or None = pink}} from the host's sheet, if there is one."""
    import json
    if not os.path.exists(SHEET):
        return {}
    from PIL import Image
    im = Image.open(SHEET).convert('RGB')
    lay = json.load(open(os.path.splitext(SHEET)[0] + '.json'))
    pink = tuple(lay['pink'])
    near = lambda rgb: min(range(16), key=lambda i: sum((a - b) ** 2 for a, b in zip(rgb, PAL[i])))
    out = {}
    for e in lay['screens']:
        cells = {}
        for r, c in e['cells']:
            x0, y0 = e['x'] + (c - e['col']) * 8, e['y'] + (r - e['row']) * 8
            px = [im.getpixel((x0 + i % 8, y0 + i // 8)) for i in range(64)]
            cells[(r, c)] = [None if p == pink else near(p) for p in px]
        out[e['screen']] = cells
    return out


def sheet(shots, out):
    """The host's bush sheet: per screen, its bush cells in the cells' box as Layer 2 showed them (the
    silhouette rule; see-through and other cells pink), and beside it the same box without the bushes
    (reference, not read back). Never overwrites: the host edits it."""
    if os.path.exists(out):
        raise SystemExit(out + ' exists (the host edits it): not overwritten')
    import json
    from PIL import Image, ImageDraw
    boxes = []
    for s, norm, wall, cells in shots:
        r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
        boxes.append((r0, c0, max(r for r, c in cells) - r0 + 1, max(c for r, c in cells) - c0 + 1))
    lx, gap = 56, 8
    w = lx + max(2 * b[3] * 8 + gap for b in boxes)
    h = sum(b[2] * 8 + 14 for b in boxes)
    im = Image.new('RGB', (w, h), (200, 200, 200))
    d = ImageDraw.Draw(im)
    lay, y = [], 0
    for (s, norm, wall, cells), (r0, c0, nr, nc) in zip(shots, boxes):
        d.rectangle((lx, y, lx + nc * 8 - 1, y + nr * 8 - 1), fill=PINK)
        for (r, c), px in silhouette(norm, cells).items():
            for i, v in enumerate(px):
                if v is not None:
                    im.putpixel((lx + (c - c0) * 8 + i % 8, y + (r - r0) * 8 + i // 8), PAL[v])
        window(wall, im, lx + nc * 8 + gap, y, None, (r0, c0, nr, nc))
        d.text((0, y), 'Screen %d' % s, fill=(0, 0, 0))
        d.text((lx, y + nr * 8), 'bushes', fill=(0, 0, 0))
        d.text((lx + nc * 8 + gap, y + nr * 8), 'behind (reference)', fill=(0, 0, 0))
        lay.append(dict(screen=s, x=lx, y=y, row=r0, col=c0, rows=nr, cols=nc,
                        cells=[[r, c] for r, c in cells]))
        y += nr * 8 + 14
    im.save(out)
    json.dump(dict(pink=PINK, screens=lay), open(os.path.splitext(out)[0] + '.json', 'w'), indent=0)
    print(out, im.size)


def png(shots, out):
    from PIL import Image
    im = Image.new('RGB', (488, 120 * len(shots)), (200, 200, 200))
    for i, (s, norm, wall, cells) in enumerate(shots):
        window(norm, im, 0, i * 120)
        window(norm, im, 248, i * 120)
        window(wall, im, 248, i * 120, set(cells))
    im.save(out)


if __name__ == '__main__':
    main()
