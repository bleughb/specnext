# Contact sheet of shapes.json: ink in the colour of the cell the game paints under it (attribute ink +
# bright; the header attribute where no cell is painted), mask black, grey
# background, frame number under each. Usage: python sheet.py out.png
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '_docs', 'lib'))
from PIL import Image, ImageDraw

PAL = [(0, 0, 0), (0, 0, 205), (205, 0, 0), (205, 0, 205), (0, 205, 0), (0, 205, 205), (205, 205, 0), (205, 205, 205),
       (0, 0, 0), (0, 0, 255), (255, 0, 0), (255, 0, 255), (0, 255, 0), (0, 255, 255), (255, 255, 0), (255, 255, 255)]
shapes = json.load(open(os.path.join(HERE, 'shapes.json')))
CW, CH, COLS, S = 40, 76, 16, 3
rows = -(-len(shapes) // COLS)
im = Image.new('RGB', (COLS * CW * S, rows * CH * S), (96, 96, 96))
d = ImageDraw.Draw(im)
for i, s in enumerate(shapes):
    ox, oy = i % COLS * CW * S, i // COLS * CH * S
    for y in range(s['h']):
        for x in range(s['w']):
            a = s['cells'][(y + s['cy']) // 8][(x + s['cx']) // 8]
            a = s['attr'] if a < 0 else a
            ink = PAL[(a & 7) + (a >> 3 & 8)]
            c = ink if s['ink'][y][x] == '1' else (0, 0, 0) if s['mask'][y][x] == '1' else None
            if c:
                d.rectangle((ox + x * S, oy + y * S, ox + x * S + S - 1, oy + y * S + S - 1), fill=c)
    d.text((ox + 2, oy + (CH - 10) * S), '%d%s' % (s['frame'], "'" if i and shapes[i - 1]['frame'] == s['frame'] else ''),
           fill=(255, 255, 255))
im.save(sys.argv[1])
print(im.size)
