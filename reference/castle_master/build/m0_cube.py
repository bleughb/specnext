"""Castle Master M0 stage 2: cubes (type 1) on the no-clip path, ported and checked against the game's output
records (26452 list before the sort 0x9D8A) at every redraw.

Port of: bbox + side bits (0x85C9: 34313-34399), origin / edge vectors (0x930F), corners (0x97F9), outcodes
(0x93DE), faces from the edge template 27486 (0x8C74), projection (0x9294: 96 + 96x/z, 56 + 56y/z, truncating).
Usage: python m0_cube.py [states file]
"""
import collections, sys
from m0_lib import states, Sandbox, s8, w16
from m0_matrix import view_matrix
from m0_geom import faces_record, sector_bounds, sector_cull


def sw(v):
    v &= 0xFFFF
    return v - 65536 if v & 0x8000 else v


def objects(m, start, count):
    a = start
    for _ in range(count):
        yield a, bytes(m[a:a + m[a + 8]])
        a += m[a + 8]


def bbox(rec, cam):
    """6 words (min, max per axis, camera-relative) + side bits (bit 2k: min > 0, 2k+1: max < 0)"""
    box, side, bit = [], 0, 0
    for k in range(3):
        mn = sw(rec[1 + k] * 64 - cam[k])
        mx = sw(mn + rec[4 + k] * 64)
        box += [mn, mx]
        if mn > 0:
            side |= 1 << (2 * k)
        if mx < 0:
            side |= 1 << (2 * k + 1)
    return box, side


def origin(M, box):
    out = []
    for r in range(3):
        s = 0
        for c in range(3):
            if M[3 * r + c]:
                s += M[3 * r + c] * box[2 * c]
        s &= 0xFFFFFF
        out.append(sw((s << 2) >> 8))
    return out


def project(v):
    x, y, z = v
    if z == 0:
        return 96, 56

    def one(p, half, full):
        if p < 0:
            if sw(p + z - 1) < 0:
                return 0
        elif sw(p - z) >= 0:
            return full
        n = half * p
        q = abs(n) // z if z > 0 else -(abs(n) // -z)
        q = q if n >= 0 else -q
        return (half + q) & 0xFF
    return one(x, 96, 192), one(y, 56, 112)


def outcode(v):
    x, y, z = v
    a = 31
    if sw(x + z) < 0:
        a &= 15
    if sw(y + z) < 0:
        a &= 23
    if sw(y - z) >= 0:
        a &= 29
    if sw(x - z) >= 0:
        a &= 27
    if z < 0:
        a &= 30
    return a


def cube(rec, cam, M, tmpl):
    """-> ('cull' | 'clip' | 'none' | record bytes) like 0x97F9 + 0x8C74"""
    box, side = bbox(rec, cam)
    O = origin(M, box)
    A = [[sw(M[3 * r + k] * rec[4 + k]) for r in range(3)] for k in range(3)]
    add = lambda *vs: [sw(sum(c)) for c in zip(*vs)]
    V = [O, add(O, A[0]), add(O, A[0], A[1]), add(O, A[1]), add(O, A[2]), add(O, A[0], A[2]),
         add(O, A[0], A[1], A[2]), add(O, A[1], A[2])]
    codes = [outcode(v) for v in V]
    orc = 0
    for c in codes:
        orc |= c
    if orc != 31:
        return 'cull'
    cols = []
    for k in range(3):
        cols.append(rec[9 + k] & 15 if side >> (2 * k) & 1 else 0)
        cols.append(rec[9 + k] >> 4 if side >> (2 * k + 1) & 1 else 0)
    if not any(cols):
        return 'none'
    faces = []
    p = 26                                       # template: 12, 12 edge pairs, 6, faces (colour, n, edges)
    for f in range(6):
        n = tmpl[p + 1]
        faces.append((cols[f], n, list(tmpl[p + 2:p + 2 + n])))
        p += 2 + n
    return faces_record(rec[7], V, tmpl, faces) or 'none'


def game_records(m):
    """id -> output record bytes, from the 26452 list (emission order, before the sort)"""
    out = {}
    for i in range(m[29502]):
        p = m[26452 + 4 * i] | m[26453 + 4 * i] << 8
        n = m[p + 1] & 127
        q = p + 2
        for _ in range(n):
            q += 1 + 2 * (m[q] & 15)
        out[m[p]] = bytes(m[p:q])
    return out


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else 'm0_states_3k.bin'
    every = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    res = collections.Counter()
    ex = []
    for k, (frame, regs, ram) in enumerate(states(name)):
        if k % every:
            continue
        sb = Sandbox(ram, regs)
        if not sb.to(34160):
            continue
        m = sb.m
        cam = [w16(m, 27309), w16(m, 27311), w16(m, 27313)]
        M = [s8(m[a]) for a in range(24149, 24158)]
        tmpl = bytes(m[27486:27548])
        lists = [(m[29494] | m[29495] << 8, m[29496]), (m[27345] | m[27346] << 8, m[27344])]
        objs = []
        for st, cnt in lists:
            if cnt:
                objs += list(objects(m, st, cnt))
        culls = m[27325] == 0
        if culls:
            sbx = sector_bounds(m[27319], m[27318], cam)
            if sbx != list(m[29488:29494]):
                res['SECTOR BOUNDS DIFFER'] += 1
        sb.to(34174)
        game = game_records(sb.m)
        for a, rec in objs:
            if rec[0] & 15 != 1 or rec[0] & 0x40:
                continue
            g = game.get(rec[7])
            if culls and sector_cull(rec, sbx):
                res['sector cull, game %s' % ('DREW IT' if g else 'too')] += 1
                continue
            mine = cube(rec, cam, M, tmpl)
            if isinstance(mine, bytes):
                if g == mine:
                    res['match'] += 1
                    if mine[1] & 0x80:
                        res['  of which full-screen face'] += 1
                else:
                    res['DIFFER'] += 1
                    if len(ex) < 6:
                        ex.append((frame, rec[7], g, mine))
            elif mine == 'clip':
                res['clip path (later)'] += 1
            else:
                res['not drawn: %s, game %s' % (mine, 'drew it' if g else 'too')] += 1
    for k, v in sorted(res.items()):
        print('  %-40s %d' % (k, v))
    for frame, oid, g, mine in ex:
        print('frame %d id %d\n  game %s\n  port %s' % (frame, oid, list(g) if g else None, list(mine)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
