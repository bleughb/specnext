"""Castle Master M1 unit checks: each cmr.asm routine against its M0 spec function (m0_*.py), on all inputs that
matter (matrix: all 72 x 72 angles) or random + edge inputs (seeded).
Usage: python m1_unit.py [--n N] [--only name,name]
"""
import argparse, random, sys
from m0_lib import states, s8
from m0_matrix import view_matrix
from m0_geom import sector_bounds, sector_cull, outcode, project, mul16, div32, sw
from m0_cube import bbox, origin
from m1_lib import assemble, Machine

EDGE = [0, 1, 2, -1, -2, 127, 128, -128, 255, 256, 32767, -32768, -32767, 16384, -16384, 1000, -1000]


def r16(rng):
    return rng.choice(EDGE) if rng.random() < 0.15 else rng.randint(-32768, 32767)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=20000)
    ap.add_argument('--only', default='')
    a = ap.parse_args()
    print(assemble().strip())
    ram = next(states('m0_states_3k.bin'))[2]
    mc = Machine(ram=ram)
    S, mem = mc.S, mc.mem
    rng = random.Random(1)
    only = set(a.only.split(',')) if a.only else None
    fails = {}
    T = {}

    def check(name, ok, info):
        k = fails.setdefault(name, [0, 0, []])
        k[0] += 1
        if not ok:
            k[1] += 1
            if len(k[2]) < 3:
                k[2].append(info)

    def run(name):
        return only is None or name in only

    if run('matrix'):
        table = bytes(ram[29337:29483])
        for yaw in range(72):
            for pitch in range(72):
                mc.b('in_yaw', yaw)
                mc.b('in_pitch', pitch)
                T['matrix'] = mc.call('matrix')
                got = [s8(mem[S['mat'] + i]) for i in range(9)]
                want = view_matrix(yaw, pitch, table)
                check('matrix', got == want, (yaw, pitch, got, want))
    if run('sector'):
        for _ in range(a.n // 4):
            yaw, pitch = rng.randrange(72), rng.randrange(72)
            cam = [r16(rng) for _ in range(3)]
            mc.b('in_yaw', yaw)
            mc.b('in_pitch', pitch)
            for k in range(3):
                mc.w(S['in_cam'] + 2 * k, cam[k])
            T['sector'] = mc.call('sector')
            got = list(mem[S['bounds']:S['bounds'] + 6])
            want = sector_bounds(yaw, pitch, cam)
            check('sector', got == want, (yaw, pitch, cam, got, want))
            for _ in range(4):
                rec = [rng.randrange(256) for _ in range(16)]
                if rng.random() < 0.3:
                    for k in range(3):
                        rec[1 + k] = (want[2 * k] + rng.randint(-2, 2)) & 255
                mem[0xC000:0xC010] = rec
                mc.call('t_secull', IX=0xC000)
                check('secull', bool(mem[S['tres']]) == sector_cull(rec, want), (rec, want))
    if run('bbox'):
        for _ in range(a.n):
            rec = [rng.randrange(256) for _ in range(16)]
            cam = [r16(rng) for _ in range(3)]
            for k in range(3):
                mc.w(S['in_cam'] + 2 * k, cam[k])
            mem[0xC000:0xC010] = rec
            T['bbox'] = mc.call('t_bbox', IX=0xC000)
            got = [mc.rw(S['box'] + 2 * i) for i in range(6)], mem[S['side']]
            want = bbox(rec, cam)
            check('bbox', got == (want[0], want[1]), (rec, cam, got, want))
    if run('xform'):
        Ms = []
        table = bytes(ram[29337:29483])
        for _ in range(64):
            Ms.append(view_matrix(rng.randrange(72), rng.randrange(72), table))
        Ms.append([rng.randint(-128, 127) for _ in range(9)])
        for _ in range(a.n):
            M = rng.choice(Ms) if rng.random() < 0.9 else [rng.randint(-128, 127) for _ in range(9)]
            for i in range(9):
                mem[S['mat'] + i] = M[i] & 255
            p = [r16(rng) for _ in range(3)]
            for k in range(3):
                mc.w(S['tpoint'] + 2 * k, p[k])
            T['xform'] = mc.call('t_xform')
            got = [mc.rw(S['tvert'] + 2 * k) for k in range(3)]
            want = origin(M, [p[0], 0, p[1], 0, p[2], 0])
            check('xform', got == want, (M, p, got, want))
    if run('outc') or run('proj'):
        for _ in range(a.n):
            z = rng.choice([0, 1, 2, 3, 100, 32767, rng.randint(0, 40), rng.randint(0, 32767)])
            if rng.random() < 0.5:
                v = [rng.randint(-z - 2, z + 2), rng.randint(-z - 2, z + 2), z]
            else:
                v = [r16(rng), r16(rng), r16(rng) if rng.random() < 0.3 else z]
            v = [sw(x) for x in v]
            for k in range(3):
                mc.w(S['tvert'] + 2 * k, v[k])
            mc.call('t_outc')
            check('outc', mem[S['tres']] == outcode(v), (v, mem[S['tres']], outcode(v)))
            if v[2] >= 0:
                T['proj'] = mc.call('t_proj')
                got = (mem[S['tres'] + 1], mem[S['tres']])
                check('proj', got == project(v), (v, got, project(v)))
    if run('mul16'):
        for _ in range(a.n):
            x, y = r16(rng), r16(rng)
            T['smul16'] = mc.call('smul16', HL=x & 0xFFFF, DE=y & 0xFFFF)
            got = mc.pair('DE') << 16 | mc.pair('HL')
            check('smul16', got == mul16(x, y) & 0xFFFFFFFF, (x, y, got, mul16(x, y)))
    if run('div32'):
        for _ in range(a.n):
            if rng.random() < 0.5:
                n = mul16(r16(rng), r16(rng))
            else:
                n = rng.randint(-(1 << 31), (1 << 31) - 1)
            d = r16(rng)
            if d == 0:
                continue
            T['div32'] = mc.call('div32', DE=(n >> 16) & 0xFFFF, HL=n & 0xFFFF, BC=d & 0xFFFF)
            got = sw(mc.pair('HL'))
            check('div32', got == div32(n, d), (n, d, got, div32(n, d)))
    bad = 0
    for k, (n, f, ex) in fails.items():
        print('  %-8s %7d checks, %d FAIL  (T last call %s)' % (k, n, f, T.get(k, '-')))
        for e in ex:
            print('      ', e)
        bad += f
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
