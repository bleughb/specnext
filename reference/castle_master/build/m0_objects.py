"""Castle Master M0: every object type, ported (0x85C9 dispatch + builders) and checked against the game's output
records (26452 list before the sort) at every redraw.

build(rec, cam, M, mem) -> 'skip' | 'sensor' | 'sector' | 'cull' | 'none' | record bytes
  mem: constant tables (edge templates 27486-27820) from the state's RAM.
Builders: cube 0x97F9 (m0_cube.cube), rectangle 0x9CB8, pyramids 4-9 0x9953 (point layouts per type, templates
27548 / 27592 / 27640 / 27688 by apex shape), lines / polygons 10-14 0x9C22 (two-sided, mode 2).
Usage: python m0_objects.py [states file] [every N-th state]
"""
import collections, sys
from m0_lib import states, Sandbox, s8, w16
from m0_geom import faces_record, outcode, sector_bounds, sector_cull, sw
from m0_cube import cube, bbox, origin, objects, game_records


def transform(M, pts):
    return [origin(M, [p[0], 0, p[1], 0, p[2], 0]) for p in pts]


def faces_at(mem, a, ncol=None):
    """face list at a: count, then (colour, n, refs)"""
    out = []
    p = a + 1
    for _ in range(mem[a]):
        n = mem[p + 1]
        out.append([mem[p], n, list(mem[p + 2:p + 2 + n])])
        p += 2 + n
    return out


def rect(rec, cam, M, mem):
    box, side = bbox(rec, cam)
    O = origin(M, box)
    A = [[sw(M[3 * r + k] * rec[4 + k]) for r in range(3)] for k in range(3)]
    if rec[4] == 0:
        u, v, c = A[2], A[1], side
    elif rec[5] == 0:
        u, v, c = A[0], A[2], side >> 2
    else:
        u, v, c = A[1], A[0], side >> 4
    if c & 1:
        col, tmpl_at = rec[9] & 15, 27778
    else:
        col, tmpl_at = rec[9] >> 4, 27769
    if not col:
        return 'none'
    v1 = [sw(O[i] + u[i]) for i in range(3)]
    v2 = [sw(v1[i] + v[i]) for i in range(3)]
    v3 = [sw(v2[i] - u[i]) for i in range(3)]
    V = [O, v1, v2, v3]
    orc = 0
    for x in V:
        orc |= outcode(x)
    if orc != 31:
        return 'cull'
    tmpl = bytes(mem[tmpl_at:tmpl_at + 9])
    return faces_record(rec[7], V, tmpl, [(col, 4, [0, 1, 2, 3])]) or 'none'


PYR = {  # (rec[12] == rec[14], rec[13] == rec[15]) -> edge template, face list, point count
    (True, True): (27548, 27565, 5), (True, False): (27640, 27659, 6),
    (False, True): (27592, 27611, 6), (False, False): (27688, 27713, 8)}


def pyramid(rec, cam, M, mem):
    t = rec[0] & 15
    box, _ = bbox(rec, cam)
    xmn, xmx, ymn, ymx, zmn, zmx = box
    i0, i1, i2, i3 = (rec[12] * 64, rec[13] * 64, rec[14] * 64, rec[15] * 64)
    P = [[0, 0, 0] for _ in range(8)]
    S = lambda idx, ax, val: P[idx].__setitem__(ax, sw(val))
    if t == 4:
        for k in (0, 1, 2, 3):
            S(k, 0, xmn)
        for k in (4, 5, 6, 7):
            S(k, 0, xmx)
        S(0, 2, zmx); S(3, 2, zmx); S(1, 2, zmn); S(2, 2, zmn)
        S(5, 2, zmn + i1); S(6, 2, zmn + i1); S(4, 2, zmn + i3); S(7, 2, zmn + i3)
        S(2, 1, ymx); S(3, 1, ymx); S(0, 1, ymn); S(1, 1, ymn)
        S(4, 1, ymn + i0); S(6, 1, ymn + i0); S(5, 1, ymn + i2); S(7, 1, ymn + i2)
    elif t in (6, 7):
        if t == 6:
            S(2, 0, xmx); S(3, 0, xmx); S(0, 0, xmn); S(1, 0, xmn)
            S(4, 0, xmn + i0); S(6, 0, xmn + i0); S(5, 0, xmn + i2); S(7, 0, xmn + i2)
            hi, lo = ymx, ymn
        else:
            S(0, 0, xmx); S(1, 0, xmx); S(2, 0, xmn); S(3, 0, xmn)
            S(4, 0, xmn + i2); S(6, 0, xmn + i2); S(5, 0, xmn + i0); S(7, 0, xmn + i0)
            hi, lo = ymn, ymx
        for k in (4, 5, 6, 7):
            S(k, 1, hi)
        for k in (0, 1, 2, 3):
            S(k, 1, lo)
        S(1, 2, zmx); S(2, 2, zmx); S(0, 2, zmn); S(3, 2, zmn)
        S(4, 2, zmn + i1); S(7, 2, zmn + i1); S(5, 2, zmn + i3); S(6, 2, zmn + i3)
    else:                                         # 8, 9
        if t == 8:
            S(0, 1, ymx); S(3, 1, ymx); S(1, 1, ymn); S(2, 1, ymn)
            S(5, 1, ymn + i1); S(6, 1, ymn + i1); S(4, 1, ymn + i3); S(7, 1, ymn + i3)
            hi, lo = zmx, zmn
        else:
            S(1, 1, ymx); S(2, 1, ymx); S(0, 1, ymn); S(3, 1, ymn)
            S(5, 1, ymn + i3); S(6, 1, ymn + i3); S(4, 1, ymn + i1); S(7, 1, ymn + i1)
            hi, lo = zmn, zmx
        for k in (4, 5, 6, 7):
            S(k, 2, hi)
        for k in (0, 1, 2, 3):
            S(k, 2, lo)
        S(2, 0, xmx); S(3, 0, xmx); S(0, 0, xmn); S(1, 0, xmn)
        S(4, 0, xmn + i0); S(6, 0, xmn + i0); S(5, 0, xmn + i2); S(7, 0, xmn + i2)
    if t == 5:
        raise NotImplementedError('type 5')
    et, fl, n = PYR[(rec[12] == rec[14], rec[13] == rec[15])]
    V = transform(M, P[:n])
    orc = 0
    for x in V:
        orc |= outcode(x)
    if orc != 31:
        return 'cull'
    tmpl = bytes(mem[et:fl])
    faces = faces_at(mem, fl)
    cb = list(rec[9:12])
    for f in range(len(faces)):
        b = cb[f >> 1]
        faces[f][0] = (b & 15) if f % 2 == 0 else b >> 4
    return faces_record(rec[7], V, tmpl, [tuple(x) for x in faces], mode=1) or 'none'


def polygon(rec, cam, M, mem):
    n = (rec[0] & 15) - 8
    pts = [[sw(rec[10 + 3 * i + k] * 64 - cam[k]) for k in range(3)] for i in range(n)]
    V = transform(M, pts)
    orc = 0
    for x in V:
        orc |= outcode(x)
    if orc != 31:
        return 'cull'
    refs = [0, 1, 2, 3, 4, 5][:n]
    if n == 2:
        return faces_record(rec[7], V, bytes(mem[27750:27755]), [(rec[9] & 15, 2, refs)]) or 'none'
    front, back = {3: (27755, 27762), 4: (27769, 27778)}.get(n, (27787, 27798))
    tf = bytes(mem[front:front + 1 + 2 * mem[front]])
    tb = bytes(mem[back:back + 1 + 2 * mem[back]])
    return faces_record(rec[7], V, tf, [(1, n, refs)], mode=2, colbyte=rec[9], tmpl_back=tb) or 'none'


def build(rec, cam, M, mem, bounds):
    t = rec[0] & 15
    if t == 0 or rec[0] & 0x40:
        return 'skip'
    if t == 2:
        return 'sensor'
    if bounds is not None and sector_cull(rec, bounds):
        return 'sector'
    if t == 1:
        return cube(rec, cam, M, bytes(mem[27486:27548]))
    if t == 3:
        return rect(rec, cam, M, mem)
    if t < 10:
        return pyramid(rec, cam, M, mem)
    return polygon(rec, cam, M, mem)


NAMES = {1: 'cube', 3: 'rect', 10: 'line', 11: 'triangle', 12: 'quad', 13: 'pentagon', 14: 'hexagon'}


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
        bounds = sector_bounds(m[27319], m[27318], cam) if m[27325] == 0 else None
        mem = bytes(m[0:65536])
        objs = []
        for st, cnt in ((m[29494] | m[29495] << 8, m[29496]), (m[27345] | m[27346] << 8, m[27344])):
            if cnt:
                objs += list(objects(m, st, cnt))
        sb.to(34174)
        game = game_records(sb.m)
        mine_ids = set()
        for a, rec in objs:
            t = rec[0] & 15
            kind = NAMES.get(t, 'pyramid %d' % t)
            try:
                mine = build(rec, cam, M, mem, bounds)
            except NotImplementedError as e:
                res['%s: NOT PORTED' % kind] += 1
                continue
            g = game.get(rec[7])
            if isinstance(mine, bytes):
                mine_ids.add(rec[7])
                if g == mine:
                    res['%s: match' % kind] += 1
                else:
                    res['%s: DIFFER' % kind] += 1
                    if len(ex) < 8:
                        ex.append((frame, kind, rec, g, mine))
            elif mine in ('cull', 'none', 'sector'):
                res['%s: not drawn (%s)%s' % (kind, mine, ', GAME DREW IT' if g else '')] += 1
        extra = set(game) - mine_ids
        res['game records not explained'] += len([i for i in extra if i not in mine_ids])
    for kk, v in sorted(res.items()):
        print('  %-45s %d' % (kk, v))
    for frame, kind, rec, g, mine in ex:
        print('frame %d %s rec %s\n  game %s\n  port %s' % (frame, kind, list(rec[:16]), list(g) if g else None,
                                                          list(mine)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
