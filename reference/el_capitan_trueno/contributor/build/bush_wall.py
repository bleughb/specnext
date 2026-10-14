# Preview of the bush rule "wall behind the bush": for every screen with bushes in the RZX, the window
# as the game draws it (left) and with the Layer 2 bush rule (right): per pixel line, every run of bush
# cells is solid from its leftmost to its rightmost ink pixel (as hooks pass 2b); the other pixels of a
# bush cell take the wall from the same row one repeat step (or more) away: the step is the horizontal
# period in cells with the fewest differing non-foreground cell pairs (2..15).
# Usage: python bush_wall.py RZX out.png
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
shots, seen, n, last, stable = [], set(), [0], [None], [0]
nf = rz.RZXTracer.next_frame


def colours(a):
    return PAL[(a & 7) + (a >> 3 & 8)], PAL[(a >> 3 & 7) + (a >> 3 & 8)]


def grab(m):
    fg = lambda r, c: m[0xEF60 + r * 4 + c // 8] & (0x80 >> c % 8)
    att = lambda r, c: m[0xEF98 + r * 30 + c]
    bush = lambda r, c: fg(r, c) and att(r, c) & 0x47 == 0x44
    byte = lambda r, y, c: m[0xF2E0 + (r * 8 + y) * 30 + c]
    if not any(bush(r, c) for r in range(14) for c in range(30)):
        return None
    key = bytes(m[0xEF60:0xEF98]) + bytes(m[0xF2E0:0xF2E0 + 3360]) + bytes(m[0xEF98:0xEF98 + 420])
    if key in seen:
        return None
    seen.add(key)
    before = Image.new('RGB', (240, 112))
    for r in range(14):
        for c in range(30):
            ink, paper = colours(att(r, c))
            for y in range(8):
                b = byte(r, y, c)
                for x in range(8):
                    before.putpixel((c * 8 + x, r * 8 + y), ink if b & (0x80 >> x) else paper)
    after = before.copy()
    cell = lambda r, c: bytes(byte(r, y, c) for y in range(8)) + bytes([att(r, c)])
    best = None                                     # the wall's repeat step: fewest differing cell pairs
    for p in range(2, 16):
        pairs = [(r, c) for r in range(14) for c in range(30 - p) if not fg(r, c) and not fg(r, c + p)]
        if len(pairs) < 20:
            continue
        bad = sum(cell(r, c) != cell(r, c + p) for r, c in pairs) / len(pairs)
        if best is None or bad < best[0] - 0.02:
            best = (bad, p)
    step = best[1] if best else 1
    print('@%d step %d (%.0f%% differ)' % (n[0], step, 100 * best[0] if best else 0))
    for r in range(14):
        src = {}
        for c in range(30):
            if not bush(r, c):
                continue
            for k in range(1, 30):
                s = [cc for cc in (c - k * step, c + k * step) if 0 <= cc < 30 and not fg(r, cc)]
                if s:
                    src[c] = s[0]
                    break
        miss = [c for c in range(30) if bush(r, c) and c not in src]
        if miss:
            print('  row %d: no source for columns %s' % (r, miss))
        for c, s in src.items():                    # wall first
            ink, paper = colours(att(r, s))
            for y in range(8):
                b = byte(r, y, s)
                for x in range(8):
                    after.putpixel((c * 8 + x, r * 8 + y), ink if b & (0x80 >> x) else paper)
        for y in range(8):                          # then the silhouette runs
            c = 0
            while c < 30:
                if not bush(r, c):
                    c += 1
                    continue
                c0 = c
                while c < 30 and bush(r, c):
                    c += 1
                xs = [cc * 8 + x for cc in range(c0, c) for x in range(8) if byte(r, y, cc) & (0x80 >> x)]
                if xs:
                    for px in range(min(xs), max(xs) + 1):
                        cc = px // 8
                        ink, paper = colours(att(r, cc))
                        on = byte(r, y, cc) & (0x80 >> px % 8)
                        after.putpixel((px, r * 8 + y), ink if on else paper)
    return before, after


def next_frame(self):
    n[0] += 1
    m = self.simulator.memory
    mp = bytes(m[0xEF60:0xEF98])
    stable[0] = stable[0] + 1 if mp == last[0] else 0
    last[0] = mp
    if stable[0] == 25 and m[0xE60B] != 34:
        g = grab(m)
        if g:
            shots.append((n[0],) + g)
    return nf(self)


rz.RZXTracer.next_frame = next_frame
try:
    rz.main(['--quiet', '--no-screen', '--fps', '0', sys.argv[1]])
except SystemExit:
    pass
sheet = Image.new('RGB', (2 * 240 + 8, len(shots) * 124), (200, 200, 200))
d = ImageDraw.Draw(sheet)
for i, (f, before, after) in enumerate(shots):
    sheet.paste(before, (0, i * 124))
    sheet.paste(after, (248, i * 124))
    d.text((0, i * 124 + 112), '@%d' % f, fill=(0, 0, 0))
sheet.save(sys.argv[2])
print(len(shots), 'screens ->', sys.argv[2], sheet.size)
