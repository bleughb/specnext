# A round of the host's bush edits: every cell of gfx/bush_tiles.png that differs from build/bush_base.png
# (the sheet as last handed to him) wins and goes to every bush cell showing the same game tile (or its
# mirror, mirrored) on all screens. His sheet before is kept in snaps/bush_tiles.hostN.bak.png; the
# result becomes the new bush_base.png. Then: python bush_walls.py; python make_nex.py.
# Usage: python bush_round.py N   (N = round number for the backup name)
import json
import os
import shutil
import sys
from collections import Counter
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, T + '/build')
import bush_walls as b
from PIL import Image

cur = T + '/gfx/bush_tiles.png'
ram = b.game_ram()
shots = []
for s in range(4):
    norm, wall = b.build(ram, s), b.build(ram, s, b.BUSH)
    shots.append((s, norm, wall, [(r, c) for r, c in b.bush_cells(norm) if b.cell(norm, r, c) != b.cell(wall, r, c)]))
lay = json.load(open(T + '/gfx/bush_tiles.json'))
pos = {(e['screen'], r, c): (e['x'] + (c - e['col']) * 8, e['y'] + (r - e['row']) * 8)
       for e in lay['screens'] for r, c in e['cells']}
key = {(s, r, c): b.cell(n, r, c) for s, n, w, cells in shots for r, c in cells}
mirror = lambda k: bytes([k[0]]) + bytes(int(format(x, '08b')[::-1], 2) for x in k[1:])
flip = lambda d: tuple(d[y * 8 + 7 - x] for y in range(8) for x in range(8))


def get(img, pl):
    return tuple(img.getpixel((pos[pl][0] + i % 8, pos[pl][1] + i // 8)) for i in range(64))


def apply(now_path, old_path, out_path, say):
    im, old = Image.open(now_path).convert('RGB'), Image.open(old_path).convert('RGB')
    changed = {}
    for pl, k in key.items():
        if get(im, pl) != get(old, pl):
            changed.setdefault(k, []).append(get(im, pl))
            if say:
                print('changed: screen %d row %d col %d' % pl)
    new = {}
    for k, v in changed.items():
        cnt = Counter(v)
        if len(cnt) > 1 and say:
            print('one tile changed %d different ways - most frequent used' % len(cnt))
        new[k] = max(cnt, key=lambda d: (cnt[d], -v.index(d)))
    for k in list(new):
        if mirror(k) not in new:
            new[mirror(k)] = flip(new[k])
    n = 0
    for pl, k in key.items():
        if k in new and get(im, pl) != new[k]:
            for i, v in enumerate(new[k]):
                im.putpixel((pos[pl][0] + i % 8, pos[pl][1] + i // 8), v)
            n += 1
    im.save(out_path)
    if say:
        print('%d changed tiles (+ mirrors) -> %d cells rewritten' % (len(changed), n))


N = sys.argv[1]                             # round number for the backup name
os.makedirs(T + '/snaps', exist_ok=True)
shutil.copy(cur, T + '/snaps/bush_tiles.host%s.bak.png' % N)
apply(cur, T + '/build/bush_base.png', cur, True)
shutil.copy(cur, T + '/build/bush_base.png')
