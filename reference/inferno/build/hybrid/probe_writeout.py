"""DI write-out at 980B to the RET at 9877-987B: T per update and its relation to the entries popped. From nexclash."""
import json, sys
from collections import Counter
from types import SimpleNamespace
sys.path.insert(0, '.')
import skoolkit.rzxplay as rp
from skoolkit.snapshot import Snapshot
from nexclash.rzx import parse_rzx
level, frames = sys.argv[1], int(sys.argv[2])
blocks = parse_rzx('../specnext/reference/inferno/Inferno%s.rzx' % level)
while blocks and isinstance(blocks[-1].obj, Snapshot):
    blocks.pop()
st = SimpleNamespace(t0=None, last=None, acc=0, loops=0, lines=0, rows=[], inside=False)
def event(tf, context, fc, pc):
    now = context.simulator.registers[25]
    if st.inside:
        d = now - st.last
        st.acc += d + 69888 if d < 0 else d
    st.last = now
    if pc == 0x980B:
        st.inside, st.acc, st.loops, st.lines = True, 0, 0, 0
        s = context.simulator
        m, sp = s.memory, s.registers[12]
        t, rows = 4, 0
        while True:
            af = m[sp] | m[sp + 1] << 8
            sp += 2
            if af & 1:                # C: the end marker
                t += 21
                break
            a, z = af >> 8, af & 0x40
            rows += 1
            if z:
                t += 27
            else:
                t += 22 + 198 * a
                sp += 4 * a
            t += 542
            sp += 4
        st.model = t + 24
    elif pc == 0x980C and st.inside:
        st.loops += 1
    elif pc == 0x9810 and st.inside:
        st.lines += 1
    elif pc == 0x8F95 and st.inside:
        st.rows.append((st.acc, st.loops, st.lines, st.acc - st.model))
        st.inside = False
rp.trace_exec = event
ctx = rp.RZXContext(None)
ctx.total_frames = frames
ctx.tracefile = SimpleNamespace(write=lambda t: None)
opts = SimpleNamespace(cmio=False, python=True, quiet=True, stop=frames, force=False)
while blocks and not ctx.stop:
    rp.process_block(blocks.pop(0).obj, opts, 0, ctx)
R = st.rows
v = sorted(r[0] for r in R)
print(json.dumps(dict(level=level, updates=len(R), T=dict(min=v[0], p10=v[len(v) // 10], median=v[len(v) // 2], max=v[-1]), sample=R[:6], errors=Counter(r[3] for r in R).most_common(6))))
