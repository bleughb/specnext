"""Castle Master M1 unit sweeps beyond the recording: the face builder (faces + clipper + corners + facing +
winding), the edge clipper and the facing test of cmr.asm against M0's Python (m0_geom.py) on random scenes in
the world's coordinate range (camera-space words to +-16,000; the recording reaches |dot| < 2^38 only, and never
lets the first-point corner check decide). Counts how often each rare path was hit.
Usage: python m1_unit2.py [--n N] [--seed S] [--bin NAME]
"""
import argparse, collections, random, sys
import m0_geom
from m0_geom import faces_record, clip_edge, outcode, facing, sw
from m0_lib import states
from m1_lib import assemble, Machine

HIT = collections.Counter()
_corners = m0_geom.corners


def corners_count(pts, first, nx, ny):
    lx, ly = pts[-1]
    L = 1 if ly == 112 else 2 if lx == 0 else 3 if ly == 0 else 0
    H = 0 if nx == 192 else 1 if ny == 112 else 2 if nx == 0 else 3
    while L != H:
        c = m0_geom.CORNERS[L]
        if c != pts[-1] and c == first:
            HIT['corner skipped as the first point'] += 1
        L = (L + 1) & 3
    return _corners(pts, first, nx, ny)


faces_record.__globals__['corners'] = corners_count


LIM = (14500, 16000, 11500)         # camera-space reach: world 255 x 64 = 16,320 per axis, M rows scaled 40 / 64 / 32


def cl(v):
    return [max(-LIM[k], min(LIM[k], v[k])) for k in range(3)]


def rv(rng, kind):
    if kind == 'near':
        z = rng.randint(-600, 4000)
        r = abs(z) * 3 // 2 + 300
        return cl([rng.randint(-r, r), rng.randint(-r, r), z])
    if kind == 'wide':
        return cl([rng.randint(-16000, 16000) for _ in range(3)])
    return cl([rng.choice([-16000, -1, 0, 1, 16000, rng.randint(-200, 200)]) for _ in range(3)])


def scene(rng, mem):
    """-> (name, V, tmpl, faces, mode, colbyte, tmpl_back, fl bytes for the asm)"""
    kind = rng.choice(['near', 'near', 'wide', 'edge'])
    t = rng.random()
    if t < 0.4:                                   # cube: origin + three edge vectors (camera inside sometimes)
        if rng.random() < 0.3:
            O = [-rng.randint(1, 3000), -rng.randint(1, 3000), -rng.randint(1, 3000)]
            A = [[rng.randint(0, 6000) if i == k else rng.randint(-300, 300) for i in range(3)] for k in range(3)]
        else:
            O = rv(rng, kind)
            A = [[rng.randint(-3000, 3000) for _ in range(3)] for _ in range(3)]
        add = lambda *vs: [sw(sum(c)) for c in zip(*vs)]
        V = [cl(v) for v in (O, add(O, A[0]), add(O, A[0], A[1]), add(O, A[1]), add(O, A[2]), add(O, A[0], A[2]),
             add(O, A[0], A[1], A[2]), add(O, A[1], A[2]))]
        tmpl = bytes(mem[27486:27548])
        fl = bytes(mem[27511:27548])
        cols = [rng.choice([0, rng.randint(1, 15)]) for _ in range(6)]
        faces, p = [], 1
        for f in range(6):
            n = fl[p + 1]
            faces.append((cols[f], n, list(fl[p + 2:p + 2 + n])))
            p += 2 + n
        return 'cube', V, tmpl, faces, 0, 0, None, (27486, 27511), cols
    if t < 0.6:                                   # pyramid templates, random points, mode 1
        et, flp, n = rng.choice([(27548, 27565, 5), (27640, 27659, 6), (27592, 27611, 6), (27688, 27713, 8)])
        base = rv(rng, kind)
        V = [cl([base[k] + rng.randint(-2500, 2500) for k in range(3)]) for _ in range(n)]
        tmpl = bytes(mem[et:flp])
        cnt = mem[flp]
        faces, p = [], flp + 1
        cols = [rng.choice([0, rng.randint(1, 15)]) for _ in range(6)]
        for f in range(cnt):
            nn = mem[p + 1]
            faces.append((cols[f], nn, list(mem[p + 2:p + 2 + nn])))
            p += 2 + nn
        return 'pyramid', V, tmpl, faces, 1, 0, None, (et, flp), cols
    n = rng.choice([2, 3, 4, 5])                  # lines / polygons (two-sided)
    base = rv(rng, kind)
    V = [cl([base[k] + rng.randint(-4000, 4000) for k in range(3)]) for _ in range(n)]
    if n == 2:
        c = rng.randint(1, 15)
        return 'line', V, bytes(mem[27750:27755]), [(c, 2, [0, 1])], 0, 0, None, (27750, None), [c]
    front, back = {3: (27755, 27762), 4: (27769, 27778)}.get(n, (27787, 27798))
    tf = bytes(mem[front:front + 1 + 2 * mem[front]])
    tb = bytes(mem[back:back + 1 + 2 * mem[back]])
    cb = rng.randint(0, 255)
    return 'polygon', V, tf, [(1, n, list(range(n)))], 2, cb, tb, (front, back), cb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=20000)
    ap.add_argument('--seed', type=int, default=7)
    ap.add_argument('--bin', default='cmr')
    a = ap.parse_args()
    if a.bin == 'cmr':
        assemble()
    ram = next(states('m0_states_3k.bin'))[2]
    mc = Machine(a.bin, ram=ram)
    S, mem = mc.S, mc.mem
    T = lambda addr: S['tmpl'] + addr - 27486
    rng = random.Random(a.seed)
    res = collections.Counter()
    ex = []
    for i in range(a.n):
        name, V, tmpl, faces, mode, cb, tb, where, cols = scene(rng, ram)
        try:
            want = faces_record(77, V, tmpl, faces, mode, cb, tb)
        except ZeroDivisionError:
            res['skipped (divide by 0)'] += 1
            continue
        for v, (x, y, z) in enumerate(V):
            for k, c in enumerate((x, y, z)):
                mc.w(S['vtx'] + 6 * v + 2 * k, c)
        mem[S['nv']] = len(V)
        mc.w('f_tmpl', T(where[0]))
        mem[S['f_mode']] = mode
        mem[S['f_id']] = 77
        if name == 'line':
            mc.w('f_fl', S['linefl'])
            mem[S['cols']] = cols[0]
        elif name == 'polygon':
            n = len(V)
            mem[S['pfl']:S['pfl'] + 9] = [1, 0, n, 0, 1, 2, 3, 4, 5]
            mc.w('f_fl', S['pfl'])
            mc.w('f_back', T(where[1]))
            mem[S['f_cb']] = cb
        else:
            mc.w('f_fl', T(where[1]))
            mem[S['cols']:S['cols'] + 6] = cols
        mc.call('t_faces')
        got = None
        if mem[S['tres']]:
            p = S['outbuf']
            n = mem[p + 1] & 127
            q = p + 2
            for _ in range(n):
                q += 1 + 2 * (mem[q] & 15)
            got = bytes(mem[p:q])
        codes = [outcode(v) for v in V]
        clip = any(c != 31 for c in codes)
        res['%s %s' % (name, 'clip' if clip else 'inside')] += 1
        if want and want[1] & 0x80:
            res['full-screen face'] += 1
        ok = got == want
        res['EQUAL' if ok else 'DIFFER'] += 1
        if not ok and len(ex) < 4:
            ex.append((name, V, cols, list(want) if want else None, list(got) if got else None))
    # the clipper and the facing test alone, wide range
    for i in range(a.n):
        P, Q = rv(rng, rng.choice(['near', 'wide'])), rv(rng, rng.choice(['near', 'wide']))
        c0, c1 = outcode(P), outcode(Q)
        if c0 == 31 or c1 == 31 and rng.random() < 0.5:
            pass
        try:
            want = clip_edge(list(P), list(Q), c0, c1)
        except ZeroDivisionError:
            continue
        for k in range(3):
            mc.w(S['clp'] + 2 * k, P[k])
            mc.w(S['clp'] + 6 + 2 * k, Q[k])
        mem[S['cc0']], mem[S['cc1']] = c0, c1
        mc.call('t_clip')
        if mem[S['tres']]:
            got = None
        else:
            got = (tuple(mc.rw(S['clp'] + 2 * k) for k in range(3)), tuple(mc.rw(S['clp'] + 6 + 2 * k) for k in range(3)))
            want = (tuple(want[0]), tuple(want[1])) if want else None
        res['clip %s' % ('EQUAL' if got == want else 'DIFFER')] += 1
        if got != want and len(ex) < 8:
            ex.append(('clip', P, Q, c0, c1, want, got))
    tm = bytes(ram[27486:27548])
    for i in range(a.n):
        V = [rv(rng, 'wide') for _ in range(8)]
        refs = [rng.randrange(12) | rng.choice([0, 128]) for _ in range(2)]
        st = {'cover': 1}
        want = facing(V, tm, refs, st), st['cover']
        for v, (x, y, z) in enumerate(V):
            for k, c in enumerate((x, y, z)):
                mc.w(S['vtx'] + 6 * v + 2 * k, c)
        mc.w('ctmpl', S['tmpl'])
        mem[S['tpoint']:S['tpoint'] + 2] = refs
        mc.w('f_refs', S['tpoint'])
        mc.call('t_facing')
        got = mem[S['tres']], mem[S['tres'] + 1]
        res['facing %s' % ('EQUAL' if got == want else 'DIFFER')] += 1
        if got != want and len(ex) < 10:
            ex.append(('facing', V, refs, want, got))
    for k, v in sorted(res.items()):
        print('  %-36s %d' % (k, v))
    for k, v in sorted(HIT.items()):
        print('  hit: %-31s %d' % (k, v))
    for e in ex:
        print('  ', e)
    return 1 if any('DIFFER' in k for k in res) else 0


if __name__ == '__main__':
    sys.exit(main())
