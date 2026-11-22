"""Castle Master M1 profile: T per label of cmr.asm (self time, PC-sampled per instruction) over sampled redraws.
Usage: python m1_prof.py [states] [every] [--top N]"""
import bisect, collections, sys
from m0_lib import states, Sandbox
from m1_lib import Machine, assemble, SENT, SP0
from m1_gate import set_inputs
from m1_raster_gate import prefill, L2P

def main():
    name = sys.argv[1] if len(sys.argv) > 1 else 'm0_states.bin'
    every = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    minobj = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    assemble()
    mc = Machine('cmr'); S = mc.S
    labs = sorted((v, k) for k, v in S.items() if v < S['code_end'] and k not in ('L2WIN',))
    addrs = [a for a, _ in labs]
    prof = collections.Counter(); cnt = collections.Counter()
    sim, R, mem = mc.sim, mc.R, mc.mem
    ops = sim.opcodes
    n = 0
    for k, (frame, regs, ram) in enumerate(states(name)):
        if k % every or ram[29496] + ram[27344] < minobj: continue
        sb = Sandbox(ram, regs)
        if not sb.to(34198): continue
        before = sb.m
        set_inputs(mc, ram)
        for addr, nm in ((27402, 'in_sky'), (27343, 'in_mount'), (27391, 'in_lflag')):
            mem[S[nm]] = before[addr]
        mem[S['in_l2page']] = L2P
        prefill(mc, before)
        mem[SP0], mem[SP0 + 1] = SENT & 255, SENT >> 8
        R[12] = SP0; R[24] = S['render']; n += 1
        while R[24] != SENT:
            pc = R[24]; t = R[25]
            ops[mem[pc]]()
            i = bisect.bisect_right(addrs, pc) - 1
            prof[labs[i][1]] += R[25] - t
            if addrs[i] == pc: cnt[labs[i][1]] += 1
    tot = sum(prof.values())
    print('views %d, T per view %d' % (n, tot / n))
    grp = collections.Counter()
    for k, v in prof.items(): grp[k.split('.')[0]] += v
    for k, v in grp.most_common(28):
        print('  %-12s %8d T/view %5.1f %%  entries/view %.1f' % (k, v / n, 100 * v / tot, cnt[k] / n))
main()
