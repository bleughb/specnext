# The hero's real poses: at every screen copy, the parts the hero composite drew in that render (every
# 0x82DF call between the composite entry 0x8AC0 with IY = 0xE644 (set at 0x8ABC) and its return: frame, x, y, flags),
# as a pose relative to its first part; every
# distinct pose is drawn assembled (ink white, mask black, mirrored as the game does) on pink, in order
# of first appearance, labelled "frames @rzx frame". Usage: python hero_poses.py RZX|poses.json out.png
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..', 'tk', 'nexclash-0.1.4'))
sys.path.insert(0, os.path.join(HERE, '..', '..', '_docs', 'lib'))
from nexclash import simrun
from PIL import Image, ImageDraw

SH = {}
for s in json.load(open(os.path.join(HERE, 'shapes.json'))):
    SH.setdefault(s['frame'], s)


class H:
    sim = None
    n = 0
    parts = []
    poses = {}
    ret = None

    def on_sim(self, sim):
        self.sim = sim

    def on_frame(self, n):
        self.n = n

    def before(self, pc):
        r, m = self.sim.registers, self.sim.memory
        if pc == 0x8AC0 and r[10] * 256 + r[11] == 0xE644:
            sp = r[12]
            self.ret = m[sp] | m[sp + 1] << 8
        elif pc == self.ret:
            self.ret = None
        elif pc == 0x82DF and self.ret is not None:
            ix = r[8] * 256 + r[9]
            if m[ix + 3] & 1:
                self.parts.append((m[ix], m[ix + 1], m[ix + 2], m[ix + 3] & 0xC0))
        elif pc == 0x886F:
            if self.parts:
                x0, y0 = self.parts[0][1], self.parts[0][2]
                key = tuple((f, x - x0, y - y0, fl) for f, x, y, fl in self.parts)
                self.poses.setdefault(key, self.n)
            self.parts = []


def draw(key, d, ox, oy, S):
    for f, rx, ry, fl in key:
        s = SH.get(f)
        if not s:
            continue
        mx, my = (fl >> 7) ^ s['facing'], fl >> 6 & 1
        bx = 4 * rx + (s['mdx'] if mx else s['dx'])
        by = ry + s['dy']
        for y in range(s['h']):
            for x in range(s['w']):
                c = (255, 255, 255) if s['ink'][y][x] == '1' else (0, 0, 0) if s['mask'][y][x] == '1' else None
                if c:
                    X = bx + (s['w'] - 1 - x if mx else x)
                    Y = by + (s['h'] - 1 - y if my else y)
                    d.rectangle((ox + X * S, oy + Y * S, ox + X * S + S - 1, oy + Y * S + S - 1), fill=c)


if sys.argv[1].endswith('.json'):          # redraw a saved pose list with the current shapes
    poses = [(tuple(tuple(p) for p in e['parts']), e['first']) for e in json.load(open(sys.argv[1]))]
else:
    h = H()
    simrun.play_rzx(sys.argv[1], h)
    poses = sorted(h.poses.items(), key=lambda kv: kv[1])
S, CW, CH, COLS = 3, 64, 76, 12
im = Image.new('RGB', (COLS * CW * S, -(-len(poses) // COLS) * CH * S), (255, 105, 180))
d = ImageDraw.Draw(im)
for i, (key, first) in enumerate(poses):
    ox, oy = (i % COLS) * CW * S, (i // COLS) * CH * S
    draw(key, d, ox + 16 * S, oy + 20 * S, S)
    d.text((ox + 2, oy + (CH - 9) * S), '%s @%d' % ('+'.join(str(k[0]) for k in key), first), fill=(0, 0, 0))
im.save(sys.argv[2])
json.dump([dict(parts=k, first=v) for k, v in poses], open(os.path.splitext(sys.argv[2])[0] + '.json', 'w'))
print(len(poses), 'poses')
