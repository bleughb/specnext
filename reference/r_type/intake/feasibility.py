"""R-Type intake: bound sprite-grid occupancy at every original refresh entry.

Run from nexclash with its 10.1 environment:
  python ../specnext/reference/r_type/intake/feasibility.py
Game-specific evidence, not a verifier of an assembled conversion.
"""
import collections
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'nexclash'))
from nexclash.rzx import trace

hist = collections.Counter()
inks = collections.Counter()
owners = collections.Counter()
paper = collections.Counter()
peak = {}
count = 0
previous = {}
changes = collections.Counter()
unique_hist = collections.Counter()
union_peak = {}


def address(x, y):
    return 0x6000 + ((y & 0xC0) << 5) + ((y & 7) << 8) + ((y & 0x38) << 2) + x


def at_copy(pc, sim):
    global count, previous
    m = sim.memory
    frame = sim.tracer.frame_index
    active = {}
    cells = 0
    for y in range(20):
        for x in range(32):
            owner = m[0x7E00 + 32 * y + x]
            if not 0 < owner < 0xDC:
                continue
            cells += 1
            owners[owner] += 1
            attr = m[0x7800 + 32 * y + x]
            inks[attr & 0x47] += 1
            paper[(attr >> 3) & 7] += 1
            # Four 8x8 cells in a 16x16 pattern; missing cells are transparent.
            slot = (y // 2) * 16 + x // 2
            key = active.setdefault(slot, bytearray(36))
            i = 2 * (y & 1) + (x & 1)
            key[i] = attr & 0x47
            for line in range(8):
                key[4 + (8 * (y & 1) + line) * 2 + (x & 1)] = m[address(x, 8 * y + line)]
    active = {s: bytes(k) for s, k in active.items() if any(k[4:])}
    distinct = set(active.values())
    union = distinct | set(previous.values())
    unique_hist[len(distinct)] += 1
    if len(union) > union_peak.get('patterns', -1):
        union_peak.update(patterns=len(union), frame=frame, old=len(set(previous.values())), new=len(distinct))
    n = len(active)
    hist[n] += 1
    changed = sum(previous.get(s) != k for s, k in active.items())
    changes[changed] += 1
    if n > peak.get('sprites', -1):
        peak.update(sprites=n, cells=cells, frame=frame)
    previous = active
    count += 1


frames, desync = trace(str(HERE.parent / 'Rtype.rzx'), [0x8842], at_copy)
result = dict(frames=frames, desync=desync, refreshes=count, peak=peak,
              sprite_counts=dict(sorted(hist.items())), changed_patterns=dict(sorted(changes.items())),
              inks=dict(inks), owners=dict(owners), papers=dict(paper),
              unique_patterns=dict(sorted(unique_hist.items())), union_peak=union_peak,
              scope='Original refresh entries only; 16x16 grid proposal, no assembled hook tested')
(HERE / 'sprite-budget.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
