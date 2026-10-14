# Round trip: rebuild every shape from patterns.bin + shapedir.bin and compare with shapes.json
# (ink pixels -> colour index from the painted cell, mask-only -> 1, outside -> 0).
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from patterns import colour_index

shapes = json.load(open(os.path.join(HERE, 'shapes.json')))
blob = open(os.path.join(HERE, 'patterns.bin'), 'rb').read()
sd = open(os.path.join(HERE, 'shapedir.bin'), 'rb').read()
bad = done = 0
seen = set()
for s in shapes:
    f = s['frame']
    if f in seen:
        continue
    seen.add(f)
    page, first, cols, rows, dx, dy, pad, mdx = sd[8 * f:8 * f + 8]
    facing, first = first >> 7, first & 0x3F
    assert page != 0xFF and cols * 16 - s['w'] == pad & 15 and rows * 16 - s['h'] == pad >> 4 and facing == s['facing']
    assert (mdx if mdx < 128 else mdx - 256) == s['mdx']
    assert (dx if dx < 128 else dx - 256) == s['dx'] and (dy if dy < 128 else dy - 256) == s['dy']
    for y in range(rows * 16):
        for x in range(cols * 16):
            n = first + (y // 16) * cols + x // 16
            b = blob[page * 8192 + n * 128 + (y % 16) * 8 + (x % 16) // 2]
            v = b >> 4 if x % 2 == 0 else b & 15
            e = 0
            if x < s['w'] and y < s['h']:
                if s['ink'][y][x] == '1':
                    a = s['cells'][(y + s['cy']) // 8][(x + s['cx']) // 8]
                    e = colour_index(s['attr'] if a < 0 else a)
                elif s['mask'][y][x] == '1':
                    e = 1
            bad += v != e
    done += 1
print('shapes checked', done, 'pixel mismatches', bad)
