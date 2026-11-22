"""Castle Master M1 gate (geometry): the Z80N renderer cmr.asm, run from the RAM at each redraw's block start (its
world snapshot 0xC000-0xFFFF + the published camera / list inputs + the tables its init copies), must give the
game's raster input: the sorted record list (bytes) and the full-screen count 29523, as at 34177 (after the sort).
Also reports the renderer's T-states per view (Z80 timing, MUL = 8 T; no 28 MHz wait states).
Usage: python m1_gate.py [states file] [every N-th] [--bin NAME]
"""
import argparse, collections, statistics, sys, time
from m0_lib import states, Sandbox
from m0_pipeline import record_at
from m1_lib import Machine, assemble


def set_inputs(mc, ram):
    S, m = mc.S, mc.mem
    m[0xC000:] = list(ram[0xC000:])
    mc.load_tables(ram)
    for k in range(3):
        m[S['in_cam'] + 2 * k] = ram[27309 + 2 * k]
        m[S['in_cam'] + 2 * k + 1] = ram[27310 + 2 * k]
    m[S['in_yaw']] = ram[27319]
    m[S['in_pitch']] = ram[27318]
    m[S['in_cull']] = ram[27325]
    m[S['in_alist']], m[S['in_alist'] + 1], m[S['in_acnt']] = ram[29494], ram[29495], ram[29496]
    m[S['in_glist']], m[S['in_glist'] + 1], m[S['in_gcnt']] = ram[27345], ram[27346], ram[27344]


def output(mc):
    S, m = mc.S, mc.mem
    out = []
    for i in range(m[S['nrec']]):
        e = m[S['list'] + 2 * i] | m[S['list'] + 2 * i + 1] << 8
        out.append(record_at(m, m[e] | m[e + 1] << 8))
    return out, m[S['nfull']]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('states', nargs='?', default='m0_states_3k.bin')
    ap.add_argument('every', nargs='?', type=int, default=1)
    ap.add_argument('--bin', default='cmr')
    ap.add_argument('--show', type=int, default=3)
    a = ap.parse_args()
    if a.bin == 'cmr':
        assemble()
    mc = Machine(a.bin)
    res = collections.Counter()
    ts, bad = [], []
    t0 = time.time()
    for k, (frame, regs, ram) in enumerate(states(a.states)):
        if k % a.every:
            continue
        sb = Sandbox(ram, regs)
        if not sb.to(34177):
            res['no sort reached'] += 1
            continue
        g = sb.m
        game = [record_at(g, g[26452 + 4 * i] | g[26453 + 4 * i] << 8) for i in range(g[29502])]
        set_inputs(mc, ram)
        t = mc.call('render_geom')
        mine, full = output(mc)
        ok = mine == game and full == g[29523]
        res['redraws %s' % ('EQUAL' if ok else 'DIFFER')] += 1
        res['polygons'] += sum(r[1] & 127 for r in game)
        ts.append(t)
        if not ok:
            if sorted(mine) == sorted(game) and full == g[29523]:
                res['  of which order only'] += 1
            if len(bad) < a.show:
                bad.append((k, frame, game, mine, full, g[29523]))
    for kk, v in sorted(res.items()):
        print('  %-24s %d' % (kk, v))
    if ts:
        print('  T per view: median %d, mean %d, max %d, min %d  (%.0f s)' % (
            statistics.median(ts), statistics.mean(ts), max(ts), min(ts), time.time() - t0))
    for k, frame, game, mine, full, gf in bad:
        print('state %d frame %d: full port %d game %d' % (k, frame, full, gf))
        gs, ms = set(game), set(mine)
        for r in game:
            if r not in ms:
                print('   game only', list(r))
        for r in mine:
            if r not in gs:
                print('   port only', list(r))
        if gs == ms:
            print('   order game', [r[0] for r in game])
            print('   order port', [r[0] for r in mine])
    return 0 if not bad else 1


if __name__ == '__main__':
    sys.exit(main())
