"""The interrupt phase that lands an interrupt right after r_enter's NEXTREG 7,3 (the gap before the window
opens), for a build. Usage: python m3_rgap.py PREFIX STATE"""
import sys
from m0_lib import states
from m2_lib import Next, syms, PC, T, FRAME
pre, want = sys.argv[1], int(sys.argv[2])
S = syms(pre)
for k, (frame, regs, ram) in enumerate(states('m0_states.bin')):
    if k != want:
        continue
    nx = Next(ram, pre, S, period=FRAME)
    a = S['r_enter']
    m = nx.mem
    at = next(x for x in range(a, a + 40) if m[x:x + 4] == [0xED, 0x91, 0x07, 0x03]) + 4
    for i in range(24):
        nx.R[i] = regs[i]
    nx.R[PC], nx.R[T], nx.R[26] = 34142, 0, 0
    nx.run(at, max_ins=10000)
    print(FRAME - nx.clock)
