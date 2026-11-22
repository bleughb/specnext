"""Castle Master M1 gate (raster): cmr.asm's whole renderer (render_geom + raster), run from the RAM at each redraw's
block start, must draw into Layer 2 exactly what the raster model (m1_raster.py, itself equal to the game's view
buffer at every redraw; here with the bolt clipped to the view: unclipped, the original's 255-row bolt at pitch 4
overwrites its own RAM, face list included) gives from the RAM at the game's raster call: per pixel the same source code and the same
original bit (byte = 2 * code + bit; a pixel the view does not draw keeps its old value, here 0x80 + the old bit).
The rest of the Layer 2 bank must stay untouched. Reports T per view (geometry, raster, total; Z80 timing).
Usage: python m1_raster_gate.py [states file] [every N-th] [--light] [--bin NAME] [--show N]
  --light: force (27391) = 0 where the sky is cleared (lightning drawn; the recording never has it)
"""
import argparse, collections, random, statistics, sys, time
from m0_lib import states, Sandbox
from m1_lib import Machine, assemble
from m1_gate import set_inputs
from m1_raster import Raster, BUF, ROWS

L2P = 18                                # Layer 2 = 16K bank 9 = 8K pages 18-23; view rows 0-112 on pages 19-22
STALE, TRANSP = 0x80, 0xE3


def code(src):
    if 1 <= src <= 16:
        return src - 1
    if 32 <= src < 48:
        return src - 16
    return {64: 32, 65: 33}[src]


def expected(rz):
    m = rz.m
    out = []
    for r in range(ROWS):
        row = []
        for p in range(192):
            bit = 1 if m[BUF + 24 * r + (p >> 3)] & (0x80 >> (p & 7)) else 0
            s = rz.src[r][p]
            row.append(STALE + bit if s == 0 else 2 * code(s) + bit)
        out.append(row)
    return out


def prefill(mc, before):
    mc.slot4 = None
    mc.pages = {L2P + k: [TRANSP] * 8192 for k in range(6)}
    for r in range(ROWS):
        line = 32 + r
        pg = mc.pages[L2P + (line >> 5)]
        base = (line & 31) * 256 + 32
        for p in range(192):
            pg[base + p] = STALE + (1 if before[BUF + 24 * r + (p >> 3)] & (0x80 >> (p & 7)) else 0)
    mc.map4(0)                          # something else in the window first


def layer2(mc):
    mc.flush4()
    rows = []
    for r in range(ROWS):
        line = 32 + r
        pg = mc.pages[L2P + (line >> 5)]
        base = (line & 31) * 256 + 32
        rows.append(pg[base:base + 192])
    outside = 0
    for k in range(6):
        pg = mc.pages[L2P + k]
        for i, v in enumerate(pg):
            line = 32 * k + (i >> 8)
            x = i & 255
            if not (32 <= line <= 32 + ROWS - 1 and 32 <= x < 224) and v != TRANSP:
                outside += 1
    return rows, outside


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('states', nargs='?', default='m0_states_3k.bin')
    ap.add_argument('every', nargs='?', type=int, default=1)
    ap.add_argument('--light', action='store_true')
    ap.add_argument('--bin', default='cmr')
    ap.add_argument('--show', type=int, default=3)
    a = ap.parse_args()
    if a.bin == 'cmr':
        assemble()
    mc = Machine(a.bin)
    S = mc.S
    rng = random.Random(5)
    res = collections.Counter()
    tg, tr, tt, tout = [], [], [], []
    bad = []
    t0 = time.time()
    for k, (frame, regs, ram) in enumerate(states(a.states)):
        if k % a.every:
            continue
        sb = Sandbox(ram, regs)
        if not sb.to(34198):
            res['no raster call'] += 1
            continue
        sb.R[24] = 34201
        if a.light and sb.m[27402] and not sb.m[29523]:
            sb.m[27391] = 0
        before = bytearray(sb.m)
        lcol = rng.randrange(20)
        rz = Raster(bytearray(before), lightning_col=lcol, clip_bolt=True)
        rz.run()
        want = expected(rz)
        set_inputs(mc, ram)
        for addr, name in ((27318, 'in_pitch'), (27319, 'in_yaw')):
            if before[addr] != ram[addr]:
                res['%s changed before the raster' % name] += 1
            mc.mem[S[name]] = before[addr]
        for addr, name in ((27402, 'in_sky'), (27343, 'in_mount'), (27391, 'in_lflag')):
            mc.mem[S[name]] = before[addr]
        mc.mem[S['in_lcol']] = lcol
        mc.mem[S['in_l2page']] = L2P
        prefill(mc, before)
        t1 = mc.call('render_geom')
        t2 = mc.call('raster')
        got, outside = layer2(mc)
        ok = got == want and not outside
        res['views %s' % ('EQUAL' if ok else 'DIFFER')] += 1
        if outside:
            res['  bytes written outside the view'] += outside
        sky = before[27402] and not before[29523]
        if rz.m[41966] > 86:
            res['  ... bolt past the buffer (clipped)'] += 1
        if sky:
            res['  cleared (sky / ground)'] += 1
            if before[27343] == 1:
                res['  ... with mountains'] += 1
            if before[27391] == 0:
                res['  ... with lightning'] += 1
        tg.append(t1)
        tr.append(t2)
        tt.append(t1 + t2)
        if sky:
            tout.append(t1 + t2)
        if not ok and len(bad) < a.show:
            diff = [(r, p, want[r][p], got[r][p]) for r in range(ROWS) for p in range(192) if want[r][p] != got[r][p]]
            bad.append((k, frame, len(diff), diff[:8], outside))
    for kk, v in sorted(res.items()):
        print('  %-34s %d' % (kk, v))
    for name, ts in (('geometry', tg), ('raster', tr), ('total', tt), ('total, cleared views', tout)):
        if ts:
            print('  T %-22s median %7d  mean %7d  max %8d  min %6d' % (
                name, statistics.median(ts), statistics.mean(ts), max(ts), min(ts)))
    if tout:
        q = sorted(tout)
        print('  cleared views: 90th percentile %d T; at 28 MHz (560k T a frame) median %.2f frames' % (
            q[int(0.9 * (len(q) - 1))], statistics.median(tout) / 560000))
    print('  (%.0f s)' % (time.time() - t0))
    for e in bad:
        print('  state %d frame %d: %d pixels differ %s; outside %d' % e)
    return 0 if not bad else 1


if __name__ == '__main__':
    sys.exit(main())
