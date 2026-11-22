"""Castle Master M1 raster sweeps beyond the recording: cmr.asm's rface (filler + span + line path) and rclear (sky /
ground, mountain band, lightning; pitch an angle 0-71: beyond it the band can read 2.5 KB past the panorama) against the raster model (m1_raster.py) on random input, compared per pixel
(source code + bit, Layer 2 byte = 2 * code + bit; undrawn pixels keep 0x80 + the old bit). Faces run in batches
on one view so state left by one face (slopes, points) carries into the next in both.
--irq: stepped, with the 2 bytes below SP overwritten at random instruction boundaries (what an interrupt entry
writes): the PUSH fill must still give the same picture.
Usage: python m1_raster_unit.py [--n N] [--seed S] [--bin NAME] [--irq]
"""
import argparse, collections, random, sys
from m0_lib import states
from m1_lib import Machine, assemble
from m1_raster import Raster, BUF, ROWS
from m1_raster_gate import expected, prefill, layer2, L2P

HIT = collections.Counter()
PATF = lambda c: 53825 + ((c - 1) * 4 & 255)


def faces_batch(rng):
    out = []
    for _ in range(rng.randint(1, 6)):
        n = rng.choice([1, 2, 2, 3, 3, 4, 4, 5, 6, 8, 12, 15])
        kind = rng.random()
        pts = []
        for _ in range(n):
            if kind < 0.1:                      # off-range x: rejected spans
                x = rng.randint(150, 255)
            elif kind < 0.2:                    # flat / degenerate
                x = rng.randint(0, 192)
            else:
                x = rng.choice([0, 1, 192, rng.randint(0, 192), rng.randint(0, 192)])
            y = rng.randint(0, 112)
            pts.append((x, y))
        if kind < 0.2 and n > 2:
            y = rng.randint(0, 112)
            pts = [(x, y if rng.random() < 0.8 else rng.randint(0, 112)) for x, _ in pts]
        out.append((rng.randint(0, 15), pts))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=3000)
    ap.add_argument('--seed', type=int, default=11)
    ap.add_argument('--bin', default='cmr')
    ap.add_argument('--irq', action='store_true', help='junk the 2 bytes below SP at random instants (interrupt entries)')
    a = ap.parse_args()
    if a.bin == 'cmr':
        assemble()
    ram = bytearray(next(states('m0_states_3k.bin'))[2])
    mc = Machine(a.bin, ram=ram)
    S, mem = mc.S, mc.mem
    rng = random.Random(a.seed)
    rng2 = random.Random(a.seed + 1)
    res = collections.Counter()
    ex = []
    pbase = S['outbuf']
    for i in range(a.n):
        before = bytearray(ram)
        for k in range(BUF, BUF + 24 * ROWS):
            before[k] = rng.randrange(256)
        for k in range(29654, 29730):           # the filler's own variables start equal (0) in both
            before[k] = 0
        for k in ('r_sl', 'r_sr', 'r_pts'):
            mem[S[k]:S[k] + (60 if k == 'r_pts' else 2)] = [0] * (60 if k == 'r_pts' else 2)
        rz = Raster(bytearray(before), lightning_col=rng.randrange(20), clip_bolt=True)
        prefill(mc, before)
        mem[S['l2pg']], mem[S['l2cur']] = L2P + 1, 255
        if rng.random() < 0.6:
            what = 'faces'
            for col, pts in faces_batch(rng):
                n = len(pts)
                rz.m[29501], rz.m[29544] = col, n
                ys = [y for _, y in pts]
                if n > 2 and len(set(ys)) == 1:
                    HIT['flat polygon'] += 1
                if any(x >= 193 for x, _ in pts):
                    HIT['an x >= 193'] += 1
                if col == 0:
                    HIT['colour 0 (pattern bytes past the table)'] += 1
                if any(((v << 4 | v >> 4) & 255) != v for v in rz.m[PATF(col):PATF(col) + 4]):
                    HIT['a pattern row with period 8'] += 1
                rz.face(pts)
                flat = [c for p in pts for c in p]
                mem[pbase:pbase + len(flat)] = flat
                if a.irq:
                    HIT['interrupts with SP in Layer 2'] += mc.call_irq('rface', rng2, A=col << 4 | n, HL=pbase)
                else:
                    mc.call('rface', A=col << 4 | n, HL=pbase)
                if mc.pair('HL') != pbase + len(flat):
                    res['rface HL wrong'] += 1
        else:
            what = 'clear'
            sky = rng.choice([0, rng.randrange(256), rng.randrange(16), rng.randrange(16) << 4])
            pitch = rng.choice([rng.randrange(72), rng.randrange(8), 4, 64 + rng.randrange(8)])   # an angle: 0-71
            yaw, mount, lflag = rng.randrange(256), rng.choice([0, 1, 1, 2]), rng.choice([0, 0, 1, 7])
            for addr, v in ((27402, sky), (27318, pitch), (27319, yaw), (27343, mount), (27391, lflag)):
                rz.m[addr] = v
            rz.clear()
            for name, v in (('in_sky', sky), ('in_pitch', pitch), ('in_yaw', yaw), ('in_mount', mount),
                            ('in_lflag', lflag), ('in_lcol', rz.lcol)):
                mem[S[name]] = v
            if a.irq:
                HIT['interrupts with SP in Layer 2'] += mc.call_irq('rclear', rng2)
            else:
                mc.call('rclear')
            what = 'clear %s' % ((sky, pitch, yaw, mount, lflag, rz.lcol, 'rows', rz.m[41964], rz.m[41965], rz.m[41966],
                                  rz.m[41967]),)
            if rz.m[41966]:
                HIT['lightning rows %s' % ('> 86' if rz.m[41966] > 86 else '<= 86')] += 1
            if rz.m[41964] and mount == 1:
                HIT['mountain band'] += 1
        want = expected(rz)
        got, outside = layer2(mc)
        ok = got == want and not outside
        res['%s %s' % (what.split()[0], 'EQUAL' if ok else 'DIFFER')] += 1
        if not ok and len(ex) < 4:
            diff = [(r, p, want[r][p], got[r][p]) for r in range(ROWS) for p in range(192) if want[r][p] != got[r][p]]
            ex.append((i, what, len(diff), diff[:6], outside))
    for k, v in sorted(res.items()):
        print('  %-40s %d' % (k, v))
    for k, v in sorted(HIT.items()):
        print('  hit: %-35s %d' % (k, v))
    for e in ex:
        print('  case %d %s: %d pixels differ %s; outside %d' % e)
    return 1 if any('DIFFER' in k or 'wrong' in k for k in res) else 0


if __name__ == '__main__':
    sys.exit(main())
