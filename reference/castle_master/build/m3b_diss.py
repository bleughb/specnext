"""Castle Master M3b: the dissolve hook (0xB66E -> h_diss). From recorded states with Layer 2 and the sprites on:
the patched dissolve leaves Layer 2 (NR 0x69) and the sprites (NR 0x15) off, and the game's RAM + registers but R
equal to the ORIGINAL dissolve's (interrupts off; the sites' bytes and the dead stack apart).
Usage: python m3b_diss.py [every N-th state] [prefix] [portc]
portc: the portcullis hook (0xCFC2 -> h_portc), run to 0xCFC6 in both (its loop waits on interrupts)"""
import sys
from m0_lib import states, Sandbox
from m2_lib import Next, syms, sites_for, PC, SP, VP

RET = 0x5B10


def main():
    every = int(sys.argv[1]) if len(sys.argv) > 1 else 250
    prefix = sys.argv[2] if len(sys.argv) > 2 else 'cm3'
    pc_in, pc_out = (0xCFC2, 0xCFC6) if 'portc' in sys.argv[3:] else (0xB66E, RET)
    S = syms(prefix)
    skip = set()
    for a, old, op, sym in sites_for(S):
        skip |= set(range(a, a + len(old) // 2))
    skip |= set(range(VP, VP + 40))
    bad = n = 0
    for k, (frame, regs, ram) in enumerate(states('m0_states.bin')):
        if k % every:
            continue
        nx = Next(ram, prefix, S, period=0)
        nx.nr[0x69], nx.nr[0x15] = 0x80, 1
        R, m = nx.R, nx.mem
        for i in range(24):
            R[i] = regs[i]
        R[SP] -= 2
        m[R[SP]], m[R[SP] + 1] = RET & 255, RET >> 8
        R[PC] = pc_in
        ok = nx.run(pc_out, max_ins=5_000_000)
        sb = Sandbox(ram, regs)
        sb.R[12] -= 2
        sb.m[sb.R[12]], sb.m[sb.R[12] + 1] = RET & 255, RET >> 8
        sb.R[24] = pc_in
        ok2 = sb.to(pc_out)
        g = nx.game_ram()
        sp = R[SP]
        dm = [x for x in range(0x4000, 0x10000) if g[x - 0x4000] != sb.m[x] and x not in skip and not sp - 96 <= x < sp]
        dr = [i for i in list(range(13)) + [14] + list(range(16, 25)) if R[i] != sb.R[i]]
        errs = ([] if ok and ok2 else ['did not return']) + (['RAM differs %s' % ['%04X' % x for x in dm[:6]]] if dm else []) \
            + (['registers differ %s' % dr] if dr else []) + (['NR 0x69 %s NR 0x15 %s' % (nx.nr[0x69], nx.nr[0x15])] if nx.nr[0x69] or nx.nr[0x15] & 1 else []) \
            + list(nx.bad)
        n += 1
        bad += bool(errs)
        if errs:
            print('state %d frame %d: %s' % (k, frame, errs[:3]))
    print('%s hook: %d states, %s' % ('portcullis' if pc_in == 0xCFC2 else 'dissolve', n, 'PASS' if not bad else '%d FAIL' % bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
