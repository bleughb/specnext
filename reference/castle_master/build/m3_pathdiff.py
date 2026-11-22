"""Per-address main-line instruction counts, original against M3, for one redraw (the path check's differences).
Usage: python m3_pathdiff.py STATE PHASE"""
import sys, collections
from m0_lib import states
from m2_lib import Next, syms, PC, T, FRAME
S = syms('cm3')
want, phase = int(sys.argv[1]), int(sys.argv[2])
res = {}
for k, (frame, regs, ram) in enumerate(states('m0_states.bin')):
    if k != want:
        continue
    for name, sites in (('orig', False), ('m3', True)):
        nx = Next(ram, 'cm3', S, sites=sites, period=FRAME)
        nx.acc = phase
        for i in range(24):
            nx.R[i] = regs[i]
        nx.R[PC], nx.R[T], nx.R[26] = 34142, 0, 1
        cnt = collections.Counter()
        st = {'isr': False}

        class Wt(dict):
            def __contains__(self, pc):
                if pc == 0xC01F:
                    st['isr'] = True
                if pc >= 0x4000 and not st['isr'] and pc not in nx.skip_main and nx.slots[2] == 10:
                    cnt[pc] += 1
                if pc == 0xC161:
                    st['isr'] = False
                return False
        nx.run(0x859F, Wt({1: 1}), max_ins=60_000_000)
        res[name] = cnt
a, b = res['orig'], res['m3']
d = sorted(((a[x] - b[x], x) for x in set(a) | set(b) if a[x] != b[x]), key=lambda y: -abs(y[0]))
print('total orig %d m3 %d; addresses that differ: %d' % (sum(a.values()), sum(b.values()), len(d)))
for v, x in d[:25]:
    print('  %04X  orig %6d  m3 %6d' % (x, a[x], b[x]))
