"""Dependency census: replay a recording, record per 256-byte page who writes and who reads, split copier/filler/game.
Usage from nexclash: python probe_deps.py LEVEL FRAMES OUT.json"""
import json, sys
from collections import Counter
from types import SimpleNamespace
sys.path.insert(0, '.')
import skoolkit.rzxplay as rp
from skoolkit.snapshot import Snapshot
from nexclash.rzx import parse_rzx
level, frames, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
blocks = parse_rzx('../specnext/reference/inferno/Inferno%s.rzx' % level)
while blocks and isinstance(blocks[-1].obj, Snapshot):
    blocks.pop()
writes, reads, rpc, inpc, outpc = Counter(), Counter(), Counter(), Counter(), Counter()
screen_rd = Counter()
st = SimpleNamespace(pc=0, phase='boot', ready=False)
def where(pc):
    if 0x9790 <= pc < 0x9907: return 'copier'
    if 0x9907 <= pc < 0x998B: return 'filler'
    if 0x998B <= pc < 0x99BC or pc >= 0xFFF4: return 'isr'
    return 'game'
class Mem(list):
    def __getitem__(self, a):
        v = list.__getitem__(self, a)
        if not isinstance(a, slice) and not (st.pc <= a <= st.pc + 3):
            reads[(where(st.pc), a >> 8)] += 1
            if 0x4000 <= a < 0x5B00 and where(st.pc) == 'game':
                screen_rd[(st.pc, a >> 8)] += 1
        return v
    def __setitem__(self, a, v):
        if not isinstance(a, slice):
            writes[(where(st.pc), a >> 8)] += 1
        list.__setitem__(self, a, v)
started = [0]
def event(tf, context, fc, pc):
    sim = context.simulator
    st.pc = pc
    m = list.__getitem__(sim.memory, pc), list.__getitem__(sim.memory, (pc + 1) & 65535)
    if m == (0xED, 0x5F): rpc[pc] += 1
    if m[0] == 0xDB or (m[0] == 0xED and (m[1] & 0xC7) == 0x40): inpc[pc] += 1
    if m[0] == 0xD3 or (m[0] == 0xED and (m[1] & 0xC7) == 0x41): outpc[pc] += 1
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
cw = {p for (w, p) in writes if w in ('copier', 'filler')}
result = dict(level=level, frames=frames,
    copier_filler_write_pages=sorted('%02X' % p for p in cw),
    game_writes_to_same=sorted(('%02X' % p, n) for (w, p), n in writes.items() if w == 'game' and p in cw),
    game_reads_of_copier_pages=sorted(('%02X' % p, n) for (w, p), n in reads.items() if w == 'game' and p in cw),
    copier_reads_pages=sorted(('%02X' % p, n) for (w, p), n in reads.items() if w == 'copier'),
    ld_a_r={('%04X' % k): v for k, v in rpc.items()}, in_pcs={('%04X' % k): v for k, v in inpc.items()}, out_pcs={('%04X' % k): v for k, v in outpc.items()},
    game_screen_readers=sorted(('%04X' % pc, '%02X' % p, n) for (pc, p), n in screen_rd.items())[:80], total_reads=sum(reads.values()))
open(out, 'w').write(json.dumps(result, indent=0))
print('ok', result['total_reads'])
