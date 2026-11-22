"""state 0 hang probe: as m3_sim (--irq --tween, first state), stop at the instruction limit, show the clock state."""
import random
from m0_lib import states
from m2_lib import Next, syms, PC, T, FRAME, VP, IFF
from m3_sim import plant_prev
S = syms('cm3')
rng = random.Random(11)
for k, (frame, regs, ram) in enumerate(states('m0_states.bin')):
    phase = rng.randrange(FRAME)
    nx = Next(ram, 'cm3', S, period=FRAME)
    nx.acc = phase
    plant_prev(nx, ram, rng)
    for i in range(24):
        nx.R[i] = regs[i]
    nx.R[PC], nx.R[T], nx.R[26] = 34142, 0, 1
    seen = []
    def w(n, tag):
        seen.append((tag, round(n.clock / FRAME, 3), n.R[IFF], n.mem[VP + 30], n.mem[VP + 10], n.mem[VP + 27], n.irqs, n.lost))
    watch = {S[s]: (lambda n, s=s: w(n, s)) for s in ('wait_in', 'wait_out', 'ptick', 'prest', 'isr_pre', 'h_snd_in', 'h_snd_out')}
    ok = nx.run(0x859F, watch, max_ins=3_000_000)
    print('ok', ok, 'PC %04X' % nx.R[PC], 'IFF', nx.R[IFF], '7377', nx.mem[0x7377], 'irqs', nx.irqs, 'lost', nx.lost, 'nr7', nx.nr[7], 'slots', nx.slots)
    i0 = next(i for i, s in enumerate(seen) if s[0] in ("ptick", "prest") and s[2] == 0)
    for s in seen[max(0, i0 - 12):i0 + 3]:
        print(s)
    break
