"""Castle Master M0 stage 1: the view matrix (0x9776), ported and checked against the original at every redraw.

Original: 3x3 signed bytes, 64 = 1.0. Y = yaw rotation from the sin / cos table 29337 (2 bytes per 5-deg step:
sin, cos), P = pitch rotation, M = P x Y, then M = diag(40, 64, 32) x M (the constants at 38765). Each product
(41342) sums 8x8 signed products in 16 bits and keeps round((4 * sum) / 256) as a byte. Result at 24149.
Usage: python m0_matrix.py [states file]
"""
import sys
from m0_lib import states, Sandbox, s8

SINCOS = 29337


def mul(A, B):
    R = []
    for i in range(3):
        for j in range(3):
            w = sum(A[3 * i + k] * B[3 * k + j] for k in range(3)) & 0xFFFF
            u = (w << 2) & 0xFFFF
            d = ((u >> 8) + ((u >> 7) & 1)) & 0xFF
            R.append(s8(d))
    return R


def view_matrix(yaw, pitch, table):
    """table: the 146 bytes at 29337 (constant)"""
    sn = lambda a: s8(table[2 * a])
    cs = lambda a: s8(table[2 * a + 1])
    Y = [64, 0, 0, 0, 64, 0, 0, 0, 64]
    if yaw:
        Y[0] = Y[8] = cs(yaw)
        Y[6] = sn(yaw)
        Y[2] = s8(-sn(yaw) & 0xFF)
    if pitch:
        P = [64, 0, 0, 0, 64, 0, 0, 0, 64]
        P[4] = P[8] = cs(pitch)
        P[5] = sn(pitch)
        P[7] = s8(-sn(pitch) & 0xFF)
        Y = mul(P, Y)
    return mul([40, 0, 0, 0, 64, 0, 0, 0, 32], Y)


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else 'm0_states_3k.bin'
    ok = bad = 0
    seen = set()
    for frame, regs, ram in states(name):
        sb = Sandbox(ram, regs)
        if not sb.to(38774):
            continue
        yaw, pitch = sb.m[27319], sb.m[27318]
        sb.to(38904)
        got = [s8(sb.m[a]) for a in range(24149, 24158)]
        mine = view_matrix(yaw, pitch, bytes(sb.m[SINCOS:SINCOS + 146]))
        if got == mine:
            ok += 1
        else:
            bad += 1
            if bad <= 5:
                print('frame %d yaw %d pitch %d\n  game %s\n  port %s' % (frame, yaw, pitch, got, mine))
        seen.add((yaw, pitch))
    print('matrix: %d match, %d differ; %d distinct (yaw, pitch)' % (ok, bad, len(seen)))
    # all 72 x 72 angles against a sandbox run? the original's routine is pure: check every pair directly
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
