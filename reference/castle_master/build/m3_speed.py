"""Where the CPU speed changes in one redraw (M3 build), with the window flag and the caller.
Usage: python m3_speed.py STATE PHASE"""
import sys
from m0_lib import states
from m2_lib import Next, syms, PC, T, SP, FRAME, VP
S = syms('cm3')
names = {v: k for k, v in S.items() if 0 <= v < 0x4000}
want, phase = int(sys.argv[1]), int(sys.argv[2])
for k, (frame, regs, ram) in enumerate(states('m0_states.bin')):
    if k != want:
        continue
    nx = Next(ram, 'cm3', S, sites=True, period=FRAME)
    nx.acc = phase
    for i in range(24):
        nx.R[i] = regs[i]
    nx.R[PC], nx.R[T], nx.R[26] = 34142, 0, 1
    orig = nx.nextreg
    last = [None]

    def nr(reg, v, nx=nx):
        if reg == 7 and v != nx.nr.get(7):
            sp = nx.R[SP]
            ret = nx.mem[sp] | nx.mem[sp + 1] << 8
            print('%7.3f  speed %d -> %d  PC %04X (%s)  window %d  [SP] %04X  slots %s' % (
                nx.clock / FRAME, nx.nr.get(7, 0) & 3, v & 3, nx.R[PC], names.get(last[0], '?'), nx.mem[VP + 10] if nx.slots[7] == 1 else -1, ret, nx.slots))
        orig(reg, v)
    nx.nextreg = nr
    from nexclash import z80n
    z80n.install(nx.sim, nextreg=nr)

    class Wt(dict):
        def __contains__(self, pc):
            if pc in names:
                last[0] = pc
            return False
    marks = {0x8599: 'rast site', 0x859C: 'show site', 0xB635: 'B635', 0xB638: 'B638'}
    for a, t in list(marks.items()) + [(S[n], n) for n in ('m3_begin', 'm3_mid', 'm3_show', 'm3_end', 'm3_wait_end', 'h_off')]:
        pass

    class W2(Wt):
        def __contains__(self, pc):
            Wt.__contains__(self, pc)
            if pc in marks:
                print('%7.3f  %s' % (nx.clock / FRAME, marks[pc]))
            return False
    nx.run(0x859F, W2({1: 1}), max_ins=60_000_000)
