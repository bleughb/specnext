"""Castle Master M0 gate: the whole ported pipeline end to end, from RAM at the redraw-block start only (camera,
world records, constant tables) to the raster's input: the sorted list of output records (+ the full-screen
count 29523), compared with the game's at the raster call (34177, after the sort) for every redraw.
The raster itself is reused as is (Build design), so an equal list gives equal pixels.
Usage: python m0_pipeline.py [states file] [every N-th]
"""
import collections, sys
from m0_lib import states, Sandbox, w16
from m0_matrix import view_matrix
from m0_geom import sector_bounds
from m0_cube import objects, bbox
from m0_objects import build
from m0_sort import depth_sort


def port(ram):
    """-> (records in drawing order, full-screen count) from the block-start RAM alone"""
    m = ram
    cam = [w16(m, 27309), w16(m, 27311), w16(m, 27313)]
    yaw, pitch = m[27319], m[27318]
    M = view_matrix(yaw, pitch, bytes(m[29337:29337 + 146]))
    bounds = sector_bounds(yaw, pitch, cam) if m[27325] == 0 else None
    out = []
    for st, cnt in ((m[29494] | m[29495] << 8, m[29496]), (m[27345] | m[27346] << 8, m[27344])):
        if not cnt:
            continue
        for a, rec in objects(m, st, cnt):
            r = build(rec, cam, M, m, bounds)
            if isinstance(r, bytes):
                box, _ = bbox(rec, cam)
                out.append((r, [v & 0xFFFF for v in box]))
    full = sum(1 for r, _ in out if r[1] & 0x80)
    order = depth_sort(out, lambda e: e[1])
    return [r for r, _ in order], full


def record_at(m, p):
    n = m[p + 1] & 127
    q = p + 2
    for _ in range(n):
        q += 1 + 2 * (m[q] & 15)
    return bytes(m[p:q])


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else 'm0_states_3k.bin'
    every = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    res = collections.Counter()
    bad = []
    for k, (frame, regs, ram) in enumerate(states(name)):
        if k % every:
            continue
        sb = Sandbox(ram, regs)
        if not sb.to(34177):
            res['no sort reached'] += 1
            continue
        m = sb.m
        game = [record_at(m, m[26452 + 4 * i] | m[26453 + 4 * i] << 8) for i in range(m[29502])]
        mine, full = port(ram)
        ok = mine == game and full == m[29523]
        res['redraws %s' % ('EQUAL' if ok else 'DIFFER')] += 1
        res['polygons'] += sum(r[1] & 127 for r in game)
        if not ok and len(bad) < 5:
            bad.append((k, frame, len(game), len(mine), full, m[29523]))
    for kk, v in sorted(res.items()):
        print('  %-24s %d' % (kk, v))
    for b in bad:
        print('  differs: state %d frame %d game %d records, port %d; full-screen port %d game %d' % b)
    return 0 if not bad else 1


if __name__ == '__main__':
    sys.exit(main())
