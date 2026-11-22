"""Castle Master M1: the redraws with the highest geometry T, then a per-routine profile of them.
Usage: python m1_worst.py [states] [top N]"""
import bisect, collections, sys
from m0_lib import states
from m1_lib import Machine, assemble, SENT, SP0
from m1_gate import set_inputs

def main():
    name = sys.argv[1] if len(sys.argv) > 1 else 'm0_states.bin'
    top = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    assemble()
    mc = Machine('cmr'); S = mc.S
    ts = []
    for k, (frame, regs, ram) in enumerate(states(name)):
        set_inputs(mc, ram)
        ts.append((mc.call('render_geom'), k, mc.mem[S['nrec']]))
    ts.sort(reverse=True)
    print('top', [(t, k, n) for t, k, n in ts[:top]])
    import statistics
    print('nrec vs T: views with T > 1M: %d, > 700k: %d' % (sum(t > 1e6 for t, _, _ in ts), sum(t > 7e5 for t, _, _ in ts)))
    want = set(k for _, k, _ in ts[:top])
    labs = sorted((v, k) for k, v in S.items() if v < S['code_end'] and k != 'L2WIN')
    addrs = [a for a, _ in labs]
    prof = collections.Counter(); cnt = collections.Counter()
    R, mem, ops = mc.R, mc.mem, mc.sim.opcodes
    for k, (frame, regs, ram) in enumerate(states(name)):
        if k not in want: continue
        set_inputs(mc, ram)
        mem[SP0], mem[SP0 + 1] = SENT & 255, SENT >> 8
        R[12] = SP0; R[24] = S['render_geom']
        while R[24] != SENT:
            pc = R[24]; t = R[25]
            ops[mem[pc]]()
            i = bisect.bisect_right(addrs, pc) - 1
            g = labs[i][1].split('.')[0]
            prof[g] += R[25] - t
            if addrs[i] == pc: cnt[labs[i][1]] += 1
    tot = sum(prof.values())
    for k, v in prof.most_common(14):
        print('  %-10s %8d T/view %5.1f %%  entries/view %.1f' % (k, v / top, 100 * v / tot, cnt[k] / top))
main()
