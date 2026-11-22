"""Main-line time per 256-byte code page, original (3.5 MHz, / 8) against M3 (28 MHz), block start to the show
site, handler time apart. Usage: python m3_cmp.py STATE PHASE"""
import sys, collections
from m0_lib import states
from m2_lib import Next, syms, PC, T, SP, FRAME, VP
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
        prof = collections.Counter()
        cnt = collections.Counter()
        last = [None, 0]
        depth = [0]

        class Wt(dict):
            def __contains__(self, pc):
                c = nx.clock
                if last[0] is not None:
                    prof[last[0]] += c - last[1]
                if pc == 0xC01F:
                    depth[0] = 1
                key = ('isr' if depth[0] else ('hook' if nx.slots[0] != 0xFF or pc < 0x4000 else pc >> 8))
                if pc == 0xC161:
                    depth[0] = 0
                last[0], last[1] = key, c
                cnt[key] += 1
                return False
        nx.run(0x859C, Wt({1: 1}), max_ins=60_000_000)
        res[name] = (prof, cnt)
po, co = res['orig']
pm, cm = res['m3']
keys = sorted(set(po) | set(pm), key=lambda x: str(x))
print('%-6s %10s %10s %8s   %9s %9s' % ('page', 'orig/8', 'm3', 'diff', 'ins orig', 'ins m3'))
for kk in keys:
    a, b = po.get(kk, 0) / 8, pm.get(kk, 0)
    if abs(a - b) > 2000 or co.get(kk, 0) != cm.get(kk, 0):
        print('%-6s %10.0f %10.0f %8.0f   %9d %9d' % (kk if isinstance(kk, str) else '%02X' % kk, a, b, a - b, co.get(kk, 0), cm.get(kk, 0)))
print('totals main (lines): orig/8 %.0f  m3 %.0f' % (sum(v for kk, v in po.items() if kk not in ('isr',)) / 8 * 312 / FRAME,
                                                   sum(v for kk, v in pm.items() if kk not in ('isr',)) * 312 / FRAME))
