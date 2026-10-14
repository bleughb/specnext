# The foreground (bushes, grass, ...) of every screen in the RZX, as the game draws it: for each distinct
# foreground layer (the map 0xEF60 cells with the buffer's pixels in the scenery attribute 0xEF98's
# ink / paper), its bounding box of cells; outside the foreground cells pink. Taken at frame ends
# where the map has not changed for 25 frames (screen built), not in the clear mode.
# Usage: python bushes.py RZX out.png   (also out.json: first frame and box per layer)
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..', '..', '_docs', 'lib'))
import skoolkit.rzxplay as rz
from PIL import Image, ImageDraw

PAL = [(0, 0, 0), (0, 0, 205), (205, 0, 0), (205, 0, 205), (0, 205, 0), (0, 205, 205), (205, 205, 0),
       (205, 205, 205), (0, 0, 0), (0, 0, 255), (255, 0, 0), (255, 0, 255), (0, 255, 0), (0, 255, 255),
       (255, 255, 0), (255, 255, 255)]
PINK = (255, 105, 180)
layers, seen, n, last, stable = [], set(), [0], [None], [0]
nf = rz.RZXTracer.next_frame


def grab(m):
    cells = [(r, c) for r in range(14) for c in range(30) if m[0xEF60 + r * 4 + c // 8] & (0x80 >> c % 8)]
    if not cells:
        return None
    key = bytes(m[0xEF60:0xEF98]) + bytes(m[0xF2E0 + r * 240 + y * 30 + c] for r, c in cells for y in range(8)) \
        + bytes(m[0xEF98 + r * 30 + c] for r, c in cells)
    if key in seen:
        return None
    seen.add(key)
    r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
    c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
    im = Image.new('RGB', ((c1 - c0 + 1) * 8, (r1 - r0 + 1) * 8), PINK)
    for r, c in cells:
        a = m[0xEF98 + r * 30 + c]
        ink, paper = PAL[(a & 7) + (a >> 3 & 8)], PAL[(a >> 3 & 7) + (a >> 3 & 8)]
        for y in range(8):
            b = m[0xF2E0 + (r * 8 + y) * 30 + c]
            for x in range(8):
                im.putpixel(((c - c0) * 8 + x, (r - r0) * 8 + y), ink if b & (0x80 >> x) else paper)
    return im, (r0, c0)


def next_frame(self):
    n[0] += 1
    m = self.simulator.memory
    mp = bytes(m[0xEF60:0xEF98])
    stable[0] = stable[0] + 1 if mp == last[0] else 0
    last[0] = mp
    if stable[0] == 25 and m[0xE60B] != 34:
        g = grab(m)
        if g:
            layers.append((n[0], g[0], g[1]))
    return nf(self)


rz.RZXTracer.next_frame = next_frame
try:
    rz.main(['--quiet', '--no-screen', '--fps', '0', sys.argv[1]])
except SystemExit:
    pass
W = 248
y, rows = 0, []
for f, im, pos in layers:
    rows.append((y, f, im, pos))
    y += im.height + 12
sheet = Image.new('RGB', (W, y), (200, 200, 200))
d = ImageDraw.Draw(sheet)
meta = []
for yy, f, im, pos in rows:
    sheet.paste(im, (0, yy))
    d.text((0, yy + im.height), '@%d cells from row %d col %d' % (f, pos[0], pos[1]), fill=(0, 0, 0))
    meta.append(dict(first=f, y=yy, w=im.width, h=im.height, row=pos[0], col=pos[1]))
sheet.save(sys.argv[2])
json.dump(meta, open(os.path.splitext(sys.argv[2])[0] + '.json', 'w'), indent=0)
print(len(layers), 'foreground layers ->', sys.argv[2], sheet.size)
