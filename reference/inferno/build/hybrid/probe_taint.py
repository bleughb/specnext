"""Taint census, from the first 8F7C: bytes last written by the copier/filler and then read by game code.
Usage from nexclash: python probe_taint.py LEVEL FRAMES OUT.json"""
import json, sys
from collections import Counter, defaultdict
from types import SimpleNamespace
sys.path.insert(0, '.')
import skoolkit.rzxplay as rp
from skoolkit.snapshot import Snapshot
from nexclash.rzx import parse_rzx
level, frames = sys.argv[1], int(sys.argv[2])
blocks = parse_rzx('../specnext/reference/inferno/Inferno%s.rzx' % level)
while blocks and isinstance(blocks[-1].obj, Snapshot):
    blocks.pop()
st = SimpleNamespace(pc=0, on=False, updates=0)
last = bytearray(65536)  # 0 other, 1 copier, 2 filler
hits = Counter(); span = defaultdict(lambda: [65536, -1])
cwr = Counter()
stack_reads = Counter()
def where(pc):
    if 0x9790 <= pc < 0x9907: return 1
    if 0x9907 <= pc < 0x998B: return 2
    return 0
class Mem(list):
    def __getitem__(self, a):
        v = list.__getitem__(self, a)
        if st.on and not isinstance(a, slice) and where(st.pc) == 0 and last[a & 65535] and not (st.pc <= a <= st.pc + 3):
            k = (st.pc, last[a & 65535])
            hits[k] += 1
            s = span[k]
            s[0], s[1] = min(s[0], a), max(s[1], a)
        return v
    def __setitem__(self, a, v):
        if not isinstance(a, slice):
            w = where(st.pc)
            last[a & 65535] = w
            if st.on and w:
                cwr[(w, a >> 8)] += 1
        list.__setitem__(self, a, v)
def event(tf, context, fc, pc):
    st.pc = pc
    if pc == 0x8F7C:
        st.on = True
        st.updates += 1
rp.trace_exec = event
_S = rp.Simulator
class TrSim(_S):
    def __init__(self, memory, *a, **k):
        super().__init__(Mem(memory), *a, **k)
rp.Simulator = TrSim
ctx = rp.RZXContext(None)
ctx.total_frames = frames
ctx.tracefile = SimpleNamespace(write=lambda t: None)
opts = SimpleNamespace(cmio=False, python=True, quiet=True, stop=frames, force=False)
while blocks and not ctx.stop:
    rp.process_block(blocks.pop(0).obj, opts, 0, ctx)
print(json.dumps(dict(level=level, updates=st.updates,
    readers=sorted(('%04X' % pc, 'copier' if w == 1 else 'filler', n, '%04X-%04X' % tuple(span[(pc, w)])) for (pc, w), n in hits.items()),
    writer_pages=sorted(('CF'[w - 1] + '%02X' % p, n) for (w, p), n in cwr.items()))))
