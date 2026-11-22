"""Handler time in one redraw: the original's (0xC01F .. its RETI at 0xC161) against M3's held lines.
Usage: python m3_hcost.py STATE PHASE"""
import sys
from m0_lib import states
from m2_lib import Next, syms, PC, T, SP, FRAME, VP
S = syms('cm3')
want, phase = int(sys.argv[1]), int(sys.argv[2])
for k, (frame, regs, ram) in enumerate(states('m0_states.bin')):
    if k != want:
        continue
    for name, sites in (('orig', False), ('m3', True)):
        nx = Next(ram, 'cm3', S, sites=sites, period=FRAME)
        nx.acc = phase
        for i in range(24):
            nx.R[i] = regs[i]
        nx.R[PC], nx.R[T], nx.R[26] = 34142, 0, 1
        st = {'in': None, 'tot': 0, 'n': 0, 'each': [], 'show': None}

        def ent(n):
            st['in'] = n.clock

        def ext(n):
            if st['in'] is not None:
                d = n.clock - st['in']
                st['tot'] += d
                st['n'] += 1
                st['each'].append(round(d * 312 / FRAME))
                st['in'] = None

        def show(n):
            if st['show'] is None:
                st['show'] = (n.clock / FRAME, st['n'], st['tot'] * 312 / FRAME)
        nx.run(0x859F, {0xC01F: ent, 0xC161: ext, 0x859C: show}, max_ins=60_000_000)
        print('%s: end %.2f frames, handlers %d, handler lines %.0f (%.1f a call); at the show site %s'
              % (name, nx.clock / FRAME, st['n'], st['tot'] * 312 / FRAME, st['tot'] * 312 / FRAME / max(1, st['n']), st['show']))
        print('   each:', st['each'][:40])
