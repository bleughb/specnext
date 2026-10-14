# Draw shapes exactly as the Next sprites hold them (patterns.bin + shapedir/fdir) on a pink background.
# Usage: python show_sprites.py FIRST LAST out.png   (frames FIRST..LAST: normal row, then hit-flash row)
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '_docs', 'lib'))
from PIL import Image, ImageDraw

F, L, OUT = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
blob = open(os.path.join(HERE, 'patterns.bin'), 'rb').read()
sd = open(os.path.join(HERE, 'shapedir.bin'), 'rb').read()
fd = open(os.path.join(HERE, 'fdir.bin'), 'rb').read()
pal = open(os.path.join(HERE, 'palette.bin'), 'rb').read()
rgb = lambda c: ((c >> 5) * 255 // 7, (c >> 2 & 7) * 255 // 7, (c & 3) * 255 // 3)
PINK = (255, 105, 180)
S, CW, CH = 4, 48, 72
frames = [f for f in range(F, L + 1) if sd[8 * f] != 0xFF]
im = Image.new('RGB', (len(frames) * CW * S, 2 * CH * S), PINK)
d = ImageDraw.Draw(im)
for i, f in enumerate(frames):
    page, first, cols, rows = sd[8 * f], sd[8 * f + 1] & 0x3F, sd[8 * f + 2], sd[8 * f + 3]
    for row, (pg, fi) in enumerate(((page, first), (fd[2 * f], fd[2 * f + 1]))):
        for y in range(rows * 16):
            for x in range(cols * 16):
                n = fi + (y // 16) * cols + x // 16
                b = blob[pg * 8192 + n * 128 + (y % 16) * 8 + (x % 16) // 2]
                v = b >> 4 if x % 2 == 0 else b & 15
                if v:
                    X, Y = i * CW * S + x * S, row * CH * S + y * S
                    d.rectangle((X, Y, X + S - 1, Y + S - 1), fill=rgb(pal[v]))
        d.text((i * CW * S + 2, row * CH * S + (CH - 10) * S), str(f), fill=(0, 0, 0))
im.save(OUT)
print(len(frames), 'frames')
