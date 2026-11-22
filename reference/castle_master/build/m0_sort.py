"""Castle Master M0: the depth sort 0x9D8A, ported and checked against the game's list order at every redraw.

List 26452: (29502) entries of (output record ptr, bbox ptr); bbox = 6 camera-relative words (min, max per axis).
Bubble passes (at most count - 1), each over all neighbour pairs (a, b); per axis 2 bits (x high, z low):
  a.min - b.max >= 0 or b.min - a.max >= 0 (separated) ->
    a.min / a.max signs differ -> 1; b.min / b.max signs differ -> 2; a.min / b.min signs differ -> 0;
    else b.min - a.min (if 0: b.max - a.max, compared with b.max's sign) vs b.min's sign: same -> 1, else 2
  overlapping -> 0.
Kept in order iff the 6-bit code is one of 32, 8, 2, 40, 10, 34, 42 (some axis 2, none 1); else swapped.
Usage: python m0_sort.py [states file] [every N-th]
"""
import collections, sys
from m0_lib import states, Sandbox, w16
from m0_geom import sw


def neg(v):
    return 1 if v & 0x8000 else 0


def axis_code(a0, a1, b0, b1):
    """16-bit words as unsigned; -> 0, 1 or 2"""
    if neg(sw(a0 - b1) & 0xFFFF) and neg(sw(b0 - a1) & 0xFFFF):
        return 0
    if neg(a1) != neg(a0):
        return 1
    if neg(b0) != neg(b1):
        return 2
    if neg(b0) != neg(a0):
        return 0
    d = (b0 - a0) & 0xFFFF
    if d == 0:
        d2 = (b1 - a1) & 0xFFFF
        return 2 if neg(d2) != neg(b1) else 1
    return 1 if neg(d) == neg(b0) else 2


def ordered(a, b):
    code = 0
    for k in range(3):
        code = code << 2 | axis_code(a[2 * k], a[2 * k + 1], b[2 * k], b[2 * k + 1])
    return code in (32, 8, 2, 40, 10, 34, 42)


def depth_sort(items, box):
    """items: list (any), box(item) -> 6 unsigned words; returns the drawing order like 0x9D8A"""
    items = list(items)
    n = len(items)
    passes = n - 1
    while passes > 0:
        swapped = False
        for i in range(n - 1):
            if not ordered(box(items[i]), box(items[i + 1])):
                items[i], items[i + 1] = items[i + 1], items[i]
                swapped = True
        if not swapped:
            break
        passes -= 1
    return items


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else 'm0_states_3k.bin'
    every = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    res = collections.Counter()
    for k, (frame, regs, ram) in enumerate(states(name)):
        if k % every:
            continue
        sb = Sandbox(ram, regs)
        if not sb.to(34174):
            continue
        m = sb.m
        n = m[29502]
        ent = [(m[26452 + 4 * i] | m[26453 + 4 * i] << 8, m[26454 + 4 * i] | m[26455 + 4 * i] << 8) for i in range(n)]
        boxes = {e: [m[e[1] + 2 * j] | m[e[1] + 2 * j + 1] << 8 for j in range(6)] for e in ent}
        mine = depth_sort(ent, lambda e: boxes[e])
        sb.to(34177)
        got = [(sb.m[26452 + 4 * i] | sb.m[26453 + 4 * i] << 8, sb.m[26454 + 4 * i] | sb.m[26455 + 4 * i] << 8)
               for i in range(n)]
        res['lists %s' % ('equal' if got == mine else 'DIFFER')] += 1
        res['entries'] += n
        res['changed by the sort'] += got != ent
    for kk, v in sorted(res.items()):
        print('  %-30s %d' % (kk, v))
    return 0


if __name__ == '__main__':
    sys.exit(main())
