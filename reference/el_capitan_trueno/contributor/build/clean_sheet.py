# Editable sheet for the host (1:1): each frame in a 40x40 cell (ink white, 1-pixel black outline,
# 8 neighbours; the rest pink), the frame number under the cell. The cell holds the shape's box grown
# by 1 pixel on each side, top-left aligned; layout in the .json next to the PNG.
# Usage: python clean_sheet.py [--raw] out.png GROUP=frames [GROUP=frames ...]   e.g. Captain=80-98
# --raw: the shape as the game draws it (ink in its colour, the game's mask black), not cleaned
# --colour: cleaned, but the ink in the figure's colour (a colour sheet, read like coins.png)
# (each group starts a new row, its name on the left of the row; frame numbers under the cells).
# Every shape is shown facing the same way: one stored mirrored (facing 1) is flipped back for the
# sheet ("flipped": true in the layout; flip it again when reading the edited cell).
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', '_docs', 'lib'))
from PIL import Image, ImageDraw
from clean_preview import clean

RAW = '--raw' in sys.argv
if RAW:
    sys.argv.remove('--raw')
COLOUR = '--colour' in sys.argv
if COLOUR:
    sys.argv.remove('--colour')
OUT = sys.argv[1]
SPECCY = [(0, 0, 0), (0, 0, 205), (205, 0, 0), (205, 0, 205), (0, 205, 0), (0, 205, 205), (205, 205, 0),
          (205, 205, 205), (0, 0, 0), (0, 0, 255), (255, 0, 0), (255, 0, 255), (0, 255, 0), (0, 255, 255),
          (255, 255, 0), (255, 255, 255)]


def raw(s):
    """Grid +1 pixel each side: None outside, an RGB colour for ink (its cell's attribute) or black."""
    g = [[None] * (s['w'] + 2) for _ in range(s['h'] + 2)]
    for y in range(s['h']):
        for x in range(s['w']):
            if s['ink'][y][x] == '1':
                a = s['cells'][(y + s['cy']) // 8][(x + s['cx']) // 8]
                a = s['attr'] if a < 0 else a
                g[y + 1][x + 1] = SPECCY[(a & 7) + (a >> 3 & 8)] if a & 7 else (0, 0, 0)
            elif s['mask'][y][x] == '1':
                g[y + 1][x + 1] = (0, 0, 0)
    return g
PINK, WHITE, BLACK = (255, 105, 180), (255, 255, 255), (0, 0, 0)
CELL, LAB, COLS, NAME = 40, 10, 10, 56


def frames_of(spec):
    out = []
    for part in spec.split(','):
        a, _, b = part.partition('-')
        out += list(range(int(a), int(b or a) + 1))
    return out


groups = [(g.partition('=')[0], frames_of(g.partition('=')[2])) for g in sys.argv[2:]]
shapes = {}
for s in json.load(open(os.path.join(HERE, 'shapes.json'))):
    shapes.setdefault(s['frame'], s)
CELL = max([CELL] + [max(shapes[f]['w'], shapes[f]['h']) + 2 for _, fr in groups for f in fr if f in shapes])
cells, row = [], 0
for name, fr in groups:
    fr = [f for f in fr if f in shapes]
    for i, f in enumerate(fr):
        cells.append((name if i == 0 else '', f, i % COLS, row + i // COLS))
    row += -(-len(fr) // COLS)
im = Image.new('RGB', (NAME + COLS * (CELL + 2), row * (CELL + LAB + 2)), (200, 200, 200))
d = ImageDraw.Draw(im)
layout = []
frames = [f for _, f, _, _ in cells]
for name, f, cx, cy in cells:
    ox, oy = NAME + cx * (CELL + 2), cy * (CELL + LAB + 2)
    if name:
        d.text((2, oy + 2), name, fill=BLACK)
    d.rectangle((ox, oy, ox + CELL - 1, oy + CELL - 1), fill=PINK)
    s = shapes[f]
    g = raw(s) if RAW else clean(s)
    if COLOUR:                          # ink in its cell's colour (the header colour off the cells)
        def inkc(y, x):
            r, c = min(max(y - 1, 0), s['h'] - 1), min(max(x - 1, 0), s['w'] - 1)
            a = s['cells'][(r + s['cy']) // 8][(c + s['cx']) // 8]
            a = s['attr'] if a < 0 else a
            return SPECCY[(a & 7) + (a >> 3 & 8)] if a & 7 else WHITE
        g = [[inkc(y, x) if v == 1 else v for x, v in enumerate(row)] for y, row in enumerate(g)]
    flip = s['facing'] == 1
    if flip:
        g = [row[::-1] for row in g]
    for y, row in enumerate(g):
        for x, v in enumerate(row):
            if RAW and v:
                im.putpixel((ox + x, oy + y), v)
            elif COLOUR and isinstance(v, tuple):
                im.putpixel((ox + x, oy + y), v)
            elif not RAW and v in (1, 2):
                im.putpixel((ox + x, oy + y), WHITE if v == 1 else BLACK)
    d.text((ox + 1, oy + CELL), str(f), fill=BLACK)
    layout.append(dict(frame=f, x=ox, y=oy, w=len(g[0]), h=len(g), flipped=flip))
im.save(OUT)
json.dump(dict(cell=CELL, pink=PINK, frames=layout), open(os.path.splitext(OUT)[0] + '.json', 'w'), indent=0)
print(len(frames), 'frames ->', OUT, im.size)
