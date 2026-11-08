"""Experiment 1: how many sprite patterns must be uploaded per game update, with 64 hardware slots?
Replays a level; per update takes the visible 16x16 patterns of every actor (visible_patterns), keeps
a 64-slot store, evicting least recently used patterns not owned by the current or pending frame.
Run from nexclash: python ../specnext/reference/inferno/build/pipeline/probe_pattern_census.py LEVEL FRAMES
"""
import json
import sys
from collections import Counter
from types import SimpleNamespace
sys.path.insert(0, '.')
import nexclash.inferno as I
import skoolkit.rzxplay as rp
from skoolkit.snapshot import Snapshot
from nexclash.rzx import parse_rzx

level, frames = sys.argv[1], int(sys.argv[2])
blocks = parse_rzx('../specnext/reference/inferno/Inferno%s.rzx' % level)
while blocks and isinstance(blocks[-1].obj, Snapshot):
    blocks.pop()
ctx = rp.RZXContext(None)
ctx.total_frames = frames
ctx.tracefile = SimpleNamespace(write=lambda text: None)
slots, age, clock = set(), {}, 0
current, pending = set(), set()
now, active = set(), False
uploads, needed, over = [], [], 0


def finish():
    global clock, current, pending, over
    clock += 1
    protected = now | current | pending
    if len(protected) > 64:
        over += 1
    new = now - slots
    for key in new:
        if len(slots) >= 64:
            free = [k for k in slots if k not in protected]
            if free:
                slots.discard(min(free, key=lambda k: age[k]))
        slots.add(key)
    for key in now:
        age[key] = clock
    uploads.append(len(new))
    needed.append(len(now))
    pending, current = set(now), pending


def event(tf, context, fc, pc):
    global active, now
    if pc == 0x8F7C:
        now, active = set(), True
    elif pc in (0x959B, 0x96A1) and active:
        sim = context.simulator
        now |= set(I.visible_patterns(I.actor_tiles(sim.memory, sim.registers), sim.memory).values())
    elif pc == 0x8F92 and active:
        finish()
        active = False


rp.trace_exec = event
opts = SimpleNamespace(cmio=False, python=False, quiet=True, stop=frames, force=False)
while blocks and not ctx.stop:
    rp.process_block(blocks.pop(0).obj, opts, 0, ctx)
order = sorted(uploads)
q = lambda p: order[min(len(order) - 1, int(len(order) * p))]
print(json.dumps({'level': level, 'frames': frames, 'updates': len(uploads), 'max_needed': max(needed),
                  'uploads_median': q(.5), 'uploads_p90': q(.9), 'uploads_p99': q(.99), 'uploads_max': order[-1],
                  'updates_over_64_protected': over, 'first_update_uploads': uploads[0],
                  'histogram': sorted(Counter(uploads).items())}))
