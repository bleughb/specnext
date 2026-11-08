"""Update time by phase, original game, T-states from the replay. From nexclash: python probe_budget.py LEVEL FRAMES"""
import json, sys
from types import SimpleNamespace
sys.path.insert(0, '.')
import skoolkit.rzxplay as rp
from skoolkit.snapshot import Snapshot
from nexclash.rzx import parse_rzx
level, frames = sys.argv[1], int(sys.argv[2])
blocks = parse_rzx('../specnext/reference/inferno/Inferno%s.rzx' % level)
while blocks and isinstance(blocks[-1].obj, Snapshot):
    blocks.pop()
FRAME = 69888
PTS = (0x8F7C, 0x8F92, 0x9907, 0x97FE, 0x8F95)
st = SimpleNamespace(t=0, last=None, cur={}, rows=[], outs=0, outs_tail=0)
def event(tf, context, fc, pc):
    now = context.simulator.registers[25]
    if st.last is not None:
        d = now - st.last
        st.t += d + FRAME if d < 0 else d
    st.last = now
    m = context.simulator.memory
    if pc in (0x97C5, 0x993C, 0xA459) and m[pc] in (0xD3, 0xED):
        st.outs_tail += 'tail' in st.cur
    if pc == 0x97FE:
        st.cur['tail'] = st.t
    if pc == 0x8F7C:
        if 'next' in st.cur:
            st.rows.append(dict(st.cur, end=st.t))
        st.cur = {'start': st.t, 'next': 1}
    elif pc in PTS and 'start' in st.cur:
        st.cur['%04X' % pc] = st.t
rp.trace_exec = event
ctx = rp.RZXContext(None)
ctx.total_frames = frames
ctx.tracefile = SimpleNamespace(write=lambda t: None)
opts = SimpleNamespace(cmio=False, python=True, quiet=True, stop=frames, force=False)
while blocks and not ctx.stop:
    rp.process_block(blocks.pop(0).obj, opts, 0, ctx)
R = [r for r in st.rows if all(k in r for k in ('8F92', '9907', '97FE', '8F95'))]
def q(f):
    v = sorted(f(r) for r in R)
    return dict(min=v[0], median=v[len(v) // 2], max=v[-1])
print(json.dumps(dict(level=level, updates=len(R), outs_in_tail=st.outs_tail,
    head=q(lambda r: r['9907'] - r['8F92']), slack=q(lambda r: r['97FE'] - r['9907']), tail=q(lambda r: r['8F95'] - r['97FE']),
    game_and_producers=q(lambda r: r['8F92'] - r['start'] + r['end'] - r['8F95']), update=q(lambda r: r['end'] - r['start']))))
