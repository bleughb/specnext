"""Per update: OUT (254) values written by the copier at 97C5 - level changes (bits 3/4) and border bits."""
import collections, json, sys
sys.path.insert(0, sys.argv[1])
from nexclash.simrun import run
REF = sys.argv[1] + '/../specnext/reference/inferno/'

class P:
    def __init__(s):
        s.sim = None; s.cur = None; s.ups = []; s.t = 0; s.border = collections.Counter(); s.other = collections.Counter()
    def on_sim(s, sim): s.sim = sim
    def after(s, pc, dt): s.t += dt
    def before(s, pc):
        r = s.sim.registers
        if pc == 0x9790:
            s.cur = {'outs': 0, 'changes': 0, 'last': None, 't0': s.t, 'gaps': []}
        elif pc == 0x97C5 and s.cur is not None:
            a = r[0]
            c = s.cur; c['outs'] += 1; s.border[a & 7] += 1
            if c['last'] is not None and (a ^ c['last']) & 0x18:
                c['changes'] += 1
            c['last'] = a
        elif pc == 0x9907 and s.cur is not None:
            s.ups.append((s.cur['outs'], s.cur['changes'])); s.cur = None
        elif pc == 0x993C or pc == 0x9985:
            pass

p = P()
run(REF + 'Inferno%s.z80' % sys.argv[2], [REF + 'Inferno%s.rzx' % sys.argv[2]], p, stop=int(sys.argv[3]) if len(sys.argv) > 3 else None)
ch = sorted(u[1] for u in p.ups)
print(json.dumps({'updates': len(p.ups), 'outs_per_copier': dict(collections.Counter(u[0] for u in p.ups)),
                  'silent_copiers': sum(1 for c in ch if c == 0), 'changes_median': ch[len(ch)//2], 'changes_p90': ch[len(ch)*9//10],
                  'changes_max': ch[-1], 'border_values': dict(p.border)}))
