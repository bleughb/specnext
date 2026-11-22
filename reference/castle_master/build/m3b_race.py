"""Castle Master M3b: an interrupt at every point of ov_capw (pace window open: the handler's clock selects the
line registers on 0x243B) must leave slots 4-5 as they were and map no page twice (ov_in reads NR 0x54 / 0x55).
Usage: python m3b_race.py [prefix] [state]"""
import sys
from m0_lib import states
from m2_lib import Next, syms, GAME, PC, SP, FRAME, VP

RET = 0x5B10


def main():
    prefix = sys.argv[1] if len(sys.argv) > 1 else 'cm3'
    want = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    S = syms(prefix)
    for k, (frame, regs, ram) in enumerate(states('m0_states.bin')):
        if k == want:
            break
    bad, n, irq = [], 0, 0
    for d in range(0, 4000, 4):
        nx = Next(ram, prefix, S, period=FRAME)
        R, m = nx.R, nx.mem
        for i in range(24):
            R[i] = regs[i]
        R[26] = 1
        m[VP + 10] = 1                  # the window open
        nx.acc = FRAME - d
        R[SP] -= 2
        m[R[SP]], m[R[SP] + 1] = RET & 255, RET >> 8
        R[PC] = S['ov_capw']
        ok = nx.run(RET, max_ins=2_000_000)
        n += 1
        irq += nx.irqs > 0
        wk = nx.page(S['PG_W0']) + nx.page(S['PG_W1'])
        k54, k55 = wk[S['ov_k54'] - 0x4000], wk[S['ov_k55'] - 0x4000]
        e = ([] if ok else ['did not return']) + list(nx.bad) + \
            (['slots %s' % nx.slots] if nx.slots != GAME else []) + (['read %d %d' % (k54, k55)] if (k54, k55) != (4, 5) else [])
        if e:
            bad.append((d, e[:2]))
    print('ov_capw with an interrupt %d .. %d units in: %d runs, %d with an interrupt; %s' % (0, 4000, n, irq, 'PASS' if not bad else '%d FAIL %s' % (len(bad), bad[:3])))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
