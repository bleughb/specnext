"""Where interrupts are lost in one redraw (M3 build), with the clock state.
Usage: python m3_lost.py STATE PHASE"""
import sys
from m0_lib import states
from m2_lib import Next, syms, PC, T, FRAME, VP
S = syms('cm3')
names = sorted((v, k) for k, v in S.items() if 0 <= v < 0x4000)
want, phase = int(sys.argv[1]), int(sys.argv[2])


def name(pc):
    best = None
    for v, k in names:
        if v <= pc:
            best = (k, pc - v)
    return '%s+%d' % best if best else '?'


for k, (frame, regs, ram) in enumerate(states('m0_states.bin')):
    if k != want:
        continue
    nx = Next(ram, 'cm3', S, period=FRAME)
    nx.acc = phase
    for i in range(24):
        nx.R[i] = regs[i]
    nx.R[PC], nx.R[T], nx.R[26] = 34142, 0, 1
    nx.run(0x859F, max_ins=60_000_000)
    for c, pc, sl in nx.lost_at:
        print('%7.3f  PC %04X %s  slots %s' % (c / FRAME, pc, name(pc) if pc < 0x4000 else 'game', sl))
