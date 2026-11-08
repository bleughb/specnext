"""Experiment 2: pattern identity. Content-deduplicated key vs (canonical image stream, chunk) key; validates
the tile-cell visibility mask the runtime would use against visible_patterns; sizes the chunk tables.
Run from nexclash: python ../specnext/reference/inferno/build/pipeline/probe_pattern_key.py LEVEL FRAMES
"""
import json, sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, '.')
import nexclash.inferno as I
import skoolkit.rzxplay as rp
from skoolkit.snapshot import Snapshot
from nexclash.rzx import parse_rzx

level, frames = sys.argv[1], int(sys.argv[2])
ref = Path('../specnext/reference/inferno')


def chunks(image_key):
    left, top, w, h, px = I.solid_image(image_key)
    out = {}
    for cy in range(0, h, 16):
        for cx in range(0, w, 16):
            pat, mask = bytearray(128), 0
            for y in range(min(16, h - cy)):
                for x in range(min(16, w - cx)):
                    c = px[(cy + y) * w + cx + x]
                    if c:
                        pat[y * 8 + x // 2] |= c << (4 if not x & 1 else 0)
                        mask |= 1 << (y // 8 * 2 + x // 8)
            out[cx, cy] = bytes(pat), mask
    return left, top, w, h, out


ram, regs, frame = I.driver_boundary_state(ref / ('Inferno%s.rzx' % level))
imgs = {}
for image, e in enumerate(I.driver_expected(ram)):
    if e not in (None, 'reject'):
        imgs.setdefault(e[0], image)
all_chunks = n_chunks = maxc = 0
content = set()
for stream, image in imgs.items():
    a = I.actor_descriptor(ram, image)
    _, _, _, _, c = chunks(tuple((x, y, I.raw_tile(ram, t)) for x, y, t in a['tiles']))
    nz = [v[0] for v in c.values() if v[1]]
    n_chunks += len(nz)
    maxc = max(maxc, len(c))
    content.update(nz)


class Store:
    def __init__(self):
        self.slots, self.age, self.clock, self.cur, self.pend, self.over, self.ups = set(), {}, 0, set(), set(), 0, []

    def finish(self, now):
        self.clock += 1
        prot = now | self.cur | self.pend
        self.over += len(prot) > 64
        new = now - self.slots
        for k in new:
            if len(self.slots) >= 64:
                free = [s for s in self.slots if s not in prot]
                if free:
                    self.slots.discard(min(free, key=lambda s: self.age[s]))
            self.slots.add(k)
        for k in now:
            self.age[k] = self.clock
        self.ups.append(len(new))
        self.pend, self.cur = set(now), self.pend


A, B = Store(), Store()
na, nb, active, mism = set(), set(), False, 0
blocks = parse_rzx(str(ref / ('Inferno%s.rzx' % level)))
while blocks and isinstance(blocks[-1].obj, Snapshot):
    blocks.pop()
ctx = rp.RZXContext(None)
ctx.total_frames = frames
ctx.tracefile = SimpleNamespace(write=lambda t: None)
maxv = 0


def event(tf, context, fc, pc):
    global active, na, nb, mism, maxv
    if pc == 0x8F7C:
        na, nb, active = set(), set(), True
    elif pc in (0x959B, 0x96A1) and active:
        sim = context.simulator
        m = sim.memory
        act = I.actor_tiles(m, sim.registers)
        key = tuple((dx, dy, I.raw_tile(m, t)) for dx, dy, t in act['tiles'])
        vis = I.visible_patterns(act, m)
        left, top, w, h, c = chunks(key)
        mine = {}
        for (cx, cy), (pat, mask) in c.items():
            for i in range(4):
                if mask & 1 << i:
                    col = (act['x'] + (left + cx) // 8 + (i & 1)) & 255
                    row = (act['y'] + (top + cy) // 8 + (i >> 1)) & 255
                    if col < 32 and row < 18:
                        mine[cx, cy] = pat
        if {k: v for k, v in vis.items() if any(v)} != {k: v for k, v in mine.items()} or left % 8 or top % 8:
            mism += 1
        maxv = max(maxv, len(vis))
        na |= set(vis.values())
        nb |= {(key, xy) for xy in vis}
    elif pc == 0x8F92 and active:
        A.finish(na)
        B.finish(nb)
        active = False


rp.trace_exec = event
opts = SimpleNamespace(cmio=False, python=False, quiet=True, stop=frames, force=False)
while blocks and not ctx.stop:
    rp.process_block(blocks.pop(0).obj, opts, 0, ctx)
q = lambda u, p: sorted(u)[min(len(u) - 1, int(len(u) * p))]
print(json.dumps(dict(level=level, frames=frames, updates=len(A.ups), images=len(imgs), nonblank_chunks=n_chunks,
                      distinct_content=len(content), max_chunks_per_image=maxc, max_visible_per_draw=maxv, mask_mismatch=mism,
                      content=dict(over=A.over, p99=q(A.ups, .99), max=max(A.ups)),
                      image_chunk=dict(over=B.over, p99=q(B.ups, .99), max=max(B.ups)))))
