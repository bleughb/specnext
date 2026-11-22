"""step state 0 (m3_sim's phase / planted camera) up to where IFF goes off for good; print the last instructions"""
import random, collections
from m0_lib import states
from m2_lib import Next, syms, PC, FRAME, IFF, SP, T
from m3_sim import plant_prev
S = syms('cm3')
names = sorted((v, k) for k, v in S.items())
def nm(a):
    best = None
    for v, k in names:
        if v <= a: best = (k, a - v)
        else: break
    return '%s+%d' % best if best else '?'
rng = random.Random(11)
for k, (frame, regs, ram) in enumerate(states('m0_states.bin')):
    nx = Next(ram, 'cm3', S, period=FRAME)
    nx.acc = rng.randrange(FRAME)
    plant_prev(nx, ram, rng)
    for i in range(24):
        nx.R[i] = regs[i]
    nx.R[PC], nx.R[T], nx.R[26] = 34142, 0, 1
    while nx.clock < 19.43 * FRAME:
        nx.run(-1, max_ins=999)
    hist = collections.deque(maxlen=400)
    while nx.clock < 19.46 * FRAME:
        pc, iff, irq = nx.R[PC], nx.R[IFF], nx.irqs
        nx.run(-1, max_ins=0)
        hist.append(('%04X' % pc, nm(pc), 'IFF', iff, '->', nx.R[IFF], 'irqs', nx.irqs, 'pend', nx.pending))
        if nx.R[PC] == S['ptick'] and not nx.R[IFF]:
            for h in hist:
                if h[1].split('+')[0] not in ('hlib_line.r','hlib_now.r', 'hlib_since_c', 'hlib_since_c.p'): print(*h)
            print('slots', nx.slots, 'nr7', nx.nr[7])
            break
    break
