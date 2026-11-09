"""Copier-skip differential: at each 8F92 snapshot the machine; rerun that update with CALL 9790 skipped, no IRQs, feeding
the recording's IN values; compare with the original at the next 8F7C (or 8F92). Usage: python probe_skip.py LEVEL FRAMES"""
import json, sys
from collections import Counter
from types import SimpleNamespace
sys.path.insert(0, '.')
import skoolkit.rzxplay as rp
from skoolkit.simulator import Simulator
from skoolkit.snapshot import Snapshot
from nexclash.rzx import parse_rzx
level, frames = sys.argv[1], int(sys.argv[2])
MODE = sys.argv[3] if len(sys.argv) > 3 else 'none'
blocks = parse_rzx('../specnext/reference/inferno/Inferno%s.rzx' % level)
while blocks and isinstance(blocks[-1].obj, Snapshot):
    blocks.pop()
NAMES = {0:'A',1:'F',2:'B',3:'C',4:'D',5:'E',6:'H',7:'L',8:'IXh',9:'IXl',10:'IYh',11:'IYl',12:'SP',16:'A2',17:'F2',18:'B2',19:'C2',20:'D2',21:'E2',22:'H2',23:'L2'}
class Feed:
    def __init__(self, vals): self.vals, self.i, self.bad = vals, 0, False
    def read_port(self, registers, port):
        if self.i >= len(self.vals):
            self.bad = True
            return 255
        v = self.vals[self.i][1]; self.i += 1
        return v
    def write_port(self, *a): pass
    def write_memory(self, *a): pass
res = SimpleNamespace(rs=[], rn=0, tr=[], div=None, sim=None, ins=[], n=0, ok=0, desync=0, last=None, gaps=[], tot=0)
page, regdiff, examples, first = Counter(), Counter(), [], []
from nexclash import simpool
SKIP = lambda i: 0x4000 <= i < 0x5B00 or (i >> 8) in (0x98, 0x99, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA9, 0xAA, 0xAB, 0xAD) or i >= 0xFFE0
def event(tf, context, fc, pc):
    sim = context.simulator
    if not (0x9790 <= pc < 0x998B or 0x998B <= pc < 0x99BC or pc >= 0xFFF4):
        res.tr.append((pc, tuple(sim.registers[:12])))
        if sim.memory[pc] == 0xED and sim.memory[(pc + 1) & 65535] == 0x5F:
            res.rs.append(sim.registers[15])
    if pc == 0x8F95 and res.sim is not None and MODE != 'none':
        for k in (range(18, 24) if MODE == 'alt' else list(range(0, 12)) + list(range(16, 24))):
            res.sim.registers[k] = sim.registers[k]
    if pc == 0x8F92:
        res.tot += 1
        if res.last is not None:
            res.gaps.append(sim.registers[25] - res.last)
        res.last = sim.registers[25]
        if res.sim is None:
            r = list(sim.registers)
            res.sim = simpool.machine(Simulator, list(sim.memory), r, 'skip', copy=True)
            res.sim.registers[24] = 0x8F95
            res.ins = []
            res.tr = []
            res.rs = []
            return
        s = res.sim
        feed = Feed(res.ins)
        s.set_tracer(feed)
        q = s.registers
        steps = 0
        mine = []
        rcount = [0]
        while q[24] != 0x8F92 and steps < 3000000:
            mine.append((q[24], tuple(q[:12])))
            if s.memory[q[24]] == 0xED and s.memory[(q[24] + 1) & 65535] == 0x5F and rcount[0] < len(res.rs):
                q[15] = res.rs[rcount[0]]
                rcount[0] += 1
                res.rn += 1
            s.opcodes[s.memory[q[24]]]()
            steps += 1
        if res.div is None:
            ref = [x for x in res.tr]
            if ref and ref[-1][0] == 0x8F92: ref = ref[:-1]
            k = next((i for i, (a, b) in enumerate(zip(ref, mine)) if a[0] != b[0]), None)
            if k is None and len(ref) != len(mine): k = min(len(ref), len(mine))
            if k is not None:
                res.div = dict(update=res.n + 1, k=k, lens=(len(ref), len(mine)), last=['%04X' % ref[j][0] for j in range(max(0, k - 4), k)],
                               ref=(('%04X' % ref[k][0]) if k < len(ref) else None, ref[k][1] if k < len(ref) else None),
                               mine=(('%04X' % mine[k][0]) if k < len(mine) else None, mine[k][1] if k < len(mine) else None),
                               at=[hex(sim.memory[(ref[max(k-1,0)][0] + i) & 65535]) for i in range(4)])
        res.tr = []
        res.n += 1
        if steps >= 3000000 or feed.bad or feed.i != len(res.ins):
            res.desync += 1
            if not first: first.append(['IN or runaway', res.n, feed.i, len(res.ins), steps])
        diff = [i for i in range(16384, 65536) if s.memory[i] != sim.memory[i] and not SKIP(i)]
        for i in diff: page[i >> 8] += 1
        rd = [NAMES[k] for k in NAMES if s.registers[k] != sim.registers[k]]
        for k in rd: regdiff[k] += 1
        if not diff and not rd: res.ok += 1
        elif not first: first.append([res.n, ['%04X' % i for i in diff[:12]], rd])
        q[24] = 0x8F95
        res.ins = []
        res.rs = []
rp.trace_exec = event
_Tr = rp.RZXTracer if hasattr(rp, 'RZXTracer') else None
orig = _Tr.read_port
def rd(self, registers, port):
    v = orig(self, registers, port)
    res.ins.append((port, v))
    return v
_Tr.read_port = rd
ctx = rp.RZXContext(None)
ctx.total_frames = frames
ctx.tracefile = SimpleNamespace(write=lambda t: None)
opts = SimpleNamespace(cmio=False, python=True, quiet=True, stop=frames, force=False)
while blocks and not ctx.stop:
    rp.process_block(blocks.pop(0).obj, opts, 0, ctx)
g=sorted(res.gaps)
print(json.dumps(dict(level=level, updates=res.n, identical=res.ok, in_mismatch=res.desync, diff_pages=sorted(('%02X' % p, n) for p, n in page.items()), reg_diffs=dict(regdiff), first=first, div=res.div, r_reads=res.rn,
    frames_between_updates=dict(min=g[0], med=g[len(g)//2], p99=g[int(len(g)*.99)], max=g[-1], mean=round(sum(g)/len(g),2)))))
