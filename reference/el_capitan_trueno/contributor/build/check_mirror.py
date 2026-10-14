# For every shape: plot it with the game mirrored (descriptor bit 7 flipped, and bit 6 = y mirror) and
# compare with the sprite's prediction (the shape flipped inside its own w x h box; x mirror at the
# box x the game uses mirrored, mdx). Reports per frame the pixels that differ and the best horizontal offset.
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import shapes as S

cat = json.load(open(os.path.join(HERE, 'gfx_catalog.json')))
shp = {}
for s in json.load(open(os.path.join(HERE, 'shapes.json'))):
    shp.setdefault(s['frame'], s)
base = S.base_state()
bad = []
for f, s in sorted(shp.items()):
    m0 = base[0]                            # the graphic with its own mask bytes (see shapes.py)
    e = 0xE290 + 4 * f
    a, w, hh = m0[e + 2] | m0[e + 3] << 8, m0[e] & 31, m0[e + 1]
    v = dict(flags=m0[e])
    g = dict(frame=f, flags=m0[e], addr=a, data=bytes(m0[a:a + 1 + w * hh]))
    for name, fl in (('x', 0x01 | (~v['flags'] & 0x80)), ('y', 0x41 | (v['flags'] & 0x80))):
        (b0, _), (b1, _) = S.plot(base, g, 0, fl), S.plot(base, g, 255, fl)
        bx, by = 4 * S.X0 - 128 + s['dx'], S.Y0 - 68 + s['dy']
        got = set()
        for y in range(S.H):
            for x in range(S.W):
                i = S.bit(b0, x, y)
                m = i | (1 - S.bit(b1, x, y))
                if m:
                    got.add((x, y, i))
        pred = set()
        for y in range(s['h']):
            for x in range(s['w']):
                if s['mask'][y][x] == '1':
                    mbx = 4 * S.X0 - 128 + s['mdx']
                    px, py = (mbx + s['w'] - 1 - x, by + y) if name == 'x' else (bx + x, by + s['h'] - 1 - y)
                    pred.add((px, py, int(s['ink'][y][x])))
        if got != pred:
            best = min(range(-8, 9), key=lambda d: len(got ^ {(x + d, y, i) for x, y, i in pred}))
            diff = len(got ^ {(x + best, y, i) for x, y, i in pred})
            bad.append((f, name, s['w'], len(got ^ pred), best, diff))
print('frames checked', len(shp), 'mismatches', len(bad))
for b in bad[:40]:
    print('frame %d mirror %s width %d: %d px differ; best x shift %+d -> %d px' % b)
