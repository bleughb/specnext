# Cleaned-graphics preview (host's idea): keep the white (ink), add a 1-pixel black outline around it
# (8 neighbours), and show the enclosed areas (not reachable from outside the box) in blue for the
# host to decide on the fill. Rows: game's drawing (ink white, mask black) / cleaned / cleaned inverted.
# The game's mask stays black where the cleaned drawing leaves it (the ULA under the sprite shows it).
# Usage: python clean_preview.py FIRST LAST out.png
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '_docs', 'lib'))
from PIL import Image, ImageDraw

PINK, WHITE, BLACK, BLUE = (255, 105, 180), (255, 255, 255), (0, 0, 0), (40, 90, 255)
S, CW, CH = 4, 48, 52


def clean(s):
    """Grid +1 pixel each side: 0 outside, 1 ink, 2 outline, 3 enclosed."""
    w, h = s['w'] + 2, s['h'] + 2
    ink = [[0] * w for _ in range(h)]
    for y in range(s['h']):
        for x in range(s['w']):
            if s['ink'][y][x] == '1':
                ink[y + 1][x + 1] = 1
    g = [row[:] for row in ink]
    for y in range(h):
        for x in range(w):
            if not ink[y][x] and any(ink[yy][xx] for yy in range(max(0, y - 1), min(h, y + 2))
                                     for xx in range(max(0, x - 1), min(w, x + 2))):
                g[y][x] = 2
    out = [[False] * w for _ in range(h)]           # 4-connected from the border through empty cells
    st = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while st:
        x, y = st.pop()
        if 0 <= x < w and 0 <= y < h and not out[y][x] and g[y][x] == 0:
            out[y][x] = True
            st += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    for y in range(h):
        for x in range(w):
            if g[y][x] == 0 and not out[y][x]:
                g[y][x] = 3
    return g


def main():
    F, L, OUT = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    shapes = {}
    for s in json.load(open(os.path.join(HERE, 'shapes.json'))):
        shapes.setdefault(s['frame'], s)
    frames = [f for f in range(F, L + 1) if f in shapes]
    im = Image.new('RGB', (len(frames) * CW * S, 3 * CH * S), PINK)
    d = ImageDraw.Draw(im)
    px = lambda i, r, x, y, c: d.rectangle((i * CW * S + x * S, r * CH * S + y * S,
                                            i * CW * S + x * S + S - 1, r * CH * S + y * S + S - 1), fill=c)
    for i, f in enumerate(frames):
        s = shapes[f]
        for y in range(s['h']):
            for x in range(s['w']):
                if s['ink'][y][x] == '1':
                    px(i, 0, x + 1, y + 1, WHITE)
                elif s['mask'][y][x] == '1':
                    px(i, 0, x + 1, y + 1, BLACK)
        g = clean(s)
        for y in range(s['h']):
            for x in range(s['w']):
                if s['mask'][y][x] == '1' and g[y + 1][x + 1] == 0:
                    g[y + 1][x + 1] = 4               # game mask outside the new outline: black
        for y, row in enumerate(g):
            for x, v in enumerate(row):
                if v == 4:
                    px(i, 1, x, y, BLACK)
                    px(i, 2, x, y, BLACK)
                elif v:
                    px(i, 1, x, y, (None, WHITE, BLACK, BLUE)[v])
                    px(i, 2, x, y, (None, BLACK, WHITE, BLUE)[v])
        d.text((i * CW * S + 2, (CH - 4) * S), str(f), fill=BLACK)
    im.save(OUT)
    print(len(frames), 'frames')


if __name__ == '__main__':
    main()
