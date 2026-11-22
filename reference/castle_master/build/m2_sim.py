"""Castle Master M2 integration test (host): the patched game, in the build's memory layout, from each recorded
redraw's block start (0x855E) to the block's end (0x859F), through the three hooks (geometry, raster, show).
Checks per redraw:
  - the Layer 2 bank shown afterwards = the raster model (m1_raster.py) run on the game's RAM as it is at the
    raster call, per pixel (byte = 2 x code + bit); stale pixels = the picture shown before; nothing written outside
    the view; the bank shown before is unchanged; a non-view screen leaves Layer 2 off
  - back in the game's state: MMU slots, speed, and (no interrupts) every register but R and the game's RAM equal
    to the ORIGINAL code's run from the same state (the sites, dead stack and R's uses apart)
  - every interrupt reaches 0xC01F with the game's pages, speed and stack (m2_lib); none lost
Usage: python m2_sim.py [states] [every N-th] [--irq | --storm] [--prefix cm2] [--show N] [--from K]
"""
import argparse, collections, random, statistics, sys, time
from m0_lib import states, Sandbox
from m1_raster import Raster, BUF, ROWS
from m1_raster_gate import code
from m2_lib import Next, assemble, syms, GAME, SITES, PC, T, SP, FRAME

STALE, TRANSP, POISON = 0x80, 0xE3, 0xEE
END = 0x859F


def bit(buf, r, p):
    return 1 if buf[BUF + 24 * r + (p >> 3)] & (0x80 >> (p & 7)) else 0


def prefill(nx, before):
    S = nx.S
    for first, shown in ((S['PG_LA'], True), (S['PG_LB'], False)):
        for k in range(6):
            nx.pages[first + k] = [TRANSP] * 8192
        for r in range(ROWS):
            line = 32 + r
            pg = nx.pages[first + (line >> 5)]
            base = (line & 31) * 256 + 32
            for p in range(192):
                pg[base + p] = STALE + bit(before, r, p) if shown and r < 112 else POISON if r < 112 else TRANSP


def view(nx, first):
    rows, outside = [], 0
    for r in range(112):
        line = 32 + r
        pg = nx.page(first + (line >> 5))
        base = (line & 31) * 256 + 32
        rows.append(list(pg[base:base + 192]))
    for k in range(6):
        pg = nx.page(first + k)
        for i, v in enumerate(pg):
            line, x = 32 * k + (i >> 8), i & 255
            if not (32 <= line <= 144 and 32 <= x < 224) and v != TRANSP:
                outside += 1
    return rows, outside


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('states', nargs='?', default='m0_states.bin')
    ap.add_argument('every', nargs='?', type=int, default=100)
    ap.add_argument('--irq', action='store_true', help='frame interrupts at the real rate')
    ap.add_argument('--storm', action='store_true', help='interrupts at about 4x the real rate, random phase')
    ap.add_argument('--prefix', default='cm2')
    ap.add_argument('--show', type=int, default=3)
    ap.add_argument('--from', dest='start', type=int, default=0)
    a = ap.parse_args()
    if a.prefix == 'cm2':
        assemble()
    S = syms(a.prefix)
    res = collections.Counter()
    bad, tt = [], []
    rng = random.Random(11)
    t0 = time.time()
    for k, (frame, regs, ram) in enumerate(states(a.states)):
        if k % a.every or k < a.start:
            continue
        period = FRAME // 4 if a.storm else FRAME if a.irq else 0
        nx = Next(ram, a.prefix, S, period=period, rng=rng if a.storm else None)
        nx.acc = rng.randrange(FRAME) if a.irq else 0
        R = nx.R
        for i in range(24):
            R[i] = regs[i]
        R[PC], R[T], R[26] = 34142, 0, 1 if (a.irq or a.storm) else 0
        got = {}

        def at_raster(n):
            got['before'] = bytearray(n.rom) + bytearray(n.game_ram())
            prefill(n, got['before'])
            got['t'] = R[T]
        inr = [0]

        def at_draw(n):                 # raster entry: after a copy the hidden view = the shown one
            wk = n.page(S['PG_W0']) + n.page(S['PG_W1'])
            if not wk[S['nfull'] - 0x4000] and not wk[S['in_sky'] - 0x4000]:
                got['copy'] = view(n, S['PG_LB'])[0] == view(n, S['PG_LA'])[0]

        def in_renderer(n):
            inr[0] += 1
        ok = nx.run(END, {0x8599: at_raster, S['isr_full']: in_renderer, S['raster']: at_draw}, max_ins=30_000_000 if period else 3_000_000)
        errs = list(nx.bad)
        if not ok or 'before' not in got:
            res['no raster call' if ok else 'did not end' if period else 'waits for an interrupt (not run here)'] += 1
            if not ok and period:
                bad.append((k, frame, errs[:4]))
            continue
        before = got['before']
        rz = Raster(bytearray(before), lightning_col=before[41970], clip_bolt=True)
        rz.run()
        want = [[STALE + bit(rz.m, r, p) if rz.src[r][p] == 0 else 2 * code(rz.src[r][p]) + bit(rz.m, r, p)
                 for p in range(192)] for r in range(112)]
        wk = nx.page(S['PG_W0']) + nx.page(S['PG_W1'])
        shown, hidden = wk[S['l2shown'] - 0x4000], wk[S['in_l2page'] - 0x4000]
        nonview = before[0x7349] != 0
        if nonview:
            res['non-view screens (Layer 2 off)'] += 1
            g = nx.game_ram()
            nd = 0
            for r in range(112):
                y = 32 + r
                sa = (y & 0xC0) << 5 | (y & 7) << 8 | (y & 0x38) << 2
                nd += sum(1 for c in range(24) if g[sa + 4 + c] != g[BUF - 0x4000 + 24 * r + c])
            res['  (0x7349) = %d: screen view %s the buffer at the end' % (before[0x7349], '=' if not nd else '!=')] += 1
            if nx.nr.get(0x69) != 0 or shown != S['PG_LA']:
                errs.append('non-view: NR 0x69 = %s, shown page %d' % (nx.nr.get(0x69), shown))
        else:
            if shown != S['PG_LB'] or hidden != S['PG_LA'] or nx.nr.get(0x12) != S['PG_LB'] // 2 or nx.nr.get(0x69) != 0x80:
                errs.append('flip: shown %d hidden %d NR 0x12 = %s NR 0x69 = %s' % (shown, hidden, nx.nr.get(0x12), nx.nr.get(0x69)))
            rows, outside = view(nx, S['PG_LB'])
            if outside:
                errs.append('%d bytes outside the view' % outside)
            if got.get('copy') is False:
                errs.append('the copy of the shown picture is wrong')
            if rows != want:
                d = [(r, p, want[r][p], rows[r][p]) for r in range(112) for p in range(192) if want[r][p] != rows[r][p]]
                errs.append('%d pixels differ %s' % (len(d), d[:6]))
            rows_a, outside_a = view(nx, S['PG_LA'])
            if outside_a or any(rows_a[r][p] != STALE + bit(before, r, p) for r in range(112) for p in range(192)):
                errs.append('the bank shown before has changed')
            attr = before[27353]
            if nx.pal.get(1) is None or len([i for i in range(68) if i in nx.pal]) != 68:
                errs.append('palette not written')
            res['  cleared' if before[27402] and not before[29523] else '  not cleared (full-screen record)' if before[29523]
                else '  not cleared (27402 = 0): copied'] += 1
        if nx.slots != GAME or nx.nr[7] & 3:
            errs.append('end state: slots %s speed %d' % (nx.slots, nx.nr[7] & 3))
        if not period:
            sb = Sandbox(ram, regs)
            if not sb.to(END):
                errs.append('reference did not reach the end')
            else:
                dr = [i for i in list(range(13)) + [14] + list(range(16, 25)) if R[i] != sb.R[i]]
                if dr:
                    errs.append('registers differ: %s' % dr)
                g, sp = nx.game_ram(), R[SP]
                skip = set()
                for ad, old, op, sym in SITES:
                    skip.update(range(ad, ad + 3))
                dm = [x for x in range(0x4000, 0x10000) if g[x - 0x4000] != sb.m[x] and x not in skip and not sp - 96 <= x < sp]
                if dm:
                    res['  redraws with RAM differences'] += 1
                    for x in dm:
                        res['    RAM %d (0x%04X)' % (x, x)] += 1
        else:
            res['interrupts'] += nx.irqs
            res['interrupts lost'] += nx.lost
            res['interrupts inside the renderer'] += inr[0]
        res['redraws %s' % ('OK' if not errs else 'FAILED')] += 1
        tt.append(R[T])
        if errs and len(bad) < a.show:
            bad.append((k, frame, errs[:4]))
    for kk, v in sorted(res.items()):
        print('  %-44s %d' % (kk, v))
    print('  (%.0f s)' % (time.time() - t0))
    for e in bad:
        print('  state %d frame %d: %s' % e)
    return 1 if bad or not res['redraws OK'] else 0


if __name__ == '__main__':
    sys.exit(main())
