"""lowest renderer SP (work RAM, slots 2-3 = the renderer's) over one redraw: python m3b_sp.py STATE"""
import sys
from m0_lib import states
from m2_lib import Next, syms, PC, T, SP, FRAME
S = syms('cm3')
want = int(sys.argv[1])
low = [0xFFFF, 0]


class All(dict):                        # (non-empty: run() tests its truth)
    def __contains__(self, k):
        return True

    def __getitem__(self, k):
        return chk


def chk(n):
    if n.slots[2] == S['PG_W0'] and 0x4000 <= n.R[SP] < low[0]:
        low[0], low[1] = n.R[SP], n.R[PC]


for k, (frame, regs, ram) in enumerate(states('m0_states.bin')):
    if k != want:
        continue
    nx = Next(ram, 'cm3', S, period=FRAME)
    for i in range(24):
        nx.R[i] = regs[i]
    nx.R[PC], nx.R[T], nx.R[26] = 34142, 0, 1
    w = All()
    w[0] = chk
    ok = nx.run(0x859F, w, max_ins=3_000_000)
    print('ok', ok, 'lowest SP %04X at %04X' % tuple(low), 'm2_ram_end %04X' % S['m2_ram_end'])
    break
