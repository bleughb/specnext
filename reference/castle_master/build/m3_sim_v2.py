"""Castle Master M3 integration test (host): the patched game in the build's memory layout, from each recorded
redraw's block start (0x855E) to the block's end (0x859F): the game's block at 28 MHz inside the pace window,
in-between views, the final view at the original's time.
Checks per redraw:
  - the Layer 2 bank shown at the end = the raster model (m1_raster.py) run on the game's RAM as it is at the
    raster call, per pixel; stale pixels = the last update's view; nothing outside the view; that bank unchanged
  - back in the game's state: MMU slots, 3.5 MHz, window closed; (no interrupts) every register but R and the
    game's RAM equal to the ORIGINAL code's run (sites, dead stack, the clock's bytes apart)
  - every interrupt reaches 0xC01F with the game's pages and stack; no execution inside a patched site
  - --pace: the time at the block's end against the ORIGINAL's from the same state and interrupt phase (K = 8:
    the host model has no 28 MHz wait states)
  - --tween: a previous camera is planted (a step back, a turn) so in-between views are drawn before the final one
  - M3b (a build with the sprite grid): the visible sprites' pixels = the overlay rule on the game's state at the
    end: opaque where the screen's bit differs from the buffer's, or in a byte where the buffer differs from the
    raster's (the buffer at 0x9F0B, before the marker); the area's ink where the screen's bit is set, else paper;
    nothing outside the view; sprites on with Layer 2, off without
Usage: python m3_sim.py [states] [every N-th] [--irq] [--pace] [--tween] [--prefix cm3] [--show N] [--from K]
"""
import argparse, collections, random, statistics, sys, time
from m0_lib import states, Sandbox
from m1_raster import Raster, BUF, ROWS
from m1_raster_gate import code
from m2_lib import Next, assemble, syms, GAME, sites_for, PC, T, SP, FRAME, VP

STALE, TRANSP, POISON = 0x80, 0xE3, 0xEE
END = 0x859F
ULA16 = [0x00, 0x02, 0xA0, 0xA2, 0x14, 0x16, 0xB4, 0xB6, 0x00, 0x03, 0xE0, 0xE2, 0x1C, 0x1F, 0xFC, 0xFF]


def scr(y, col):
    return 0x4000 + ((y & 0xC0) << 5) + ((y & 7) << 8) + ((y & 0x38) << 2) + col


def overlay_errors(nx, g, S_raster, attr):
    """the sprite layer against the overlay rule (g = the game's 0x4000-0xFFFF now; S_raster = the buffer at 0x9F0B)"""
    br = 8 if attr & 0x40 else 0
    ink, paper = ULA16[(attr & 7) + br], ULA16[((attr >> 3) & 7) + br]
    want = {}
    for r in range(112):
        for c in range(24):
            u = g[scr(32 + r, 4 + c) - 0x4000]
            b = g[BUF + 24 * r + c - 0x4000]
            m = (u ^ b) | (0xFF if b != S_raster[24 * r + c] else 0)
            for k in range(8):
                if m & (0x80 >> k):
                    want[(32 + 8 * c + k, 32 + r)] = ink if u & (0x80 >> k) else paper
    got = nx.sprite_pixels()
    if got == want:
        return [], len(want)
    d = sorted(set(got) ^ set(want)) + sorted(xy for xy in set(got) & set(want) if got[xy] != want[xy])
    return ['overlay sprites: %d pixels differ %s' % (len(d), [(xy, want.get(xy), got.get(xy)) for xy in d[:5]])], len(want)


def bit(buf, r, p):
    return 1 if buf[BUF + 24 * r + (p >> 3)] & (0x80 >> (p & 7)) else 0


def prefill(nx, before):
    S = nx.S
    for first, shown in ((S['PG_LA'], True), (S['PG_LB'], False), (S['PG_LC'], False)):
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


def wk_of(nx):
    S = nx.S
    return nx.page(S['PG_W0']) + nx.page(S['PG_W1'])


def plant_prev(nx, ram, rng):
    """a previous view in the same area: a step away, a turn of 2 units, sometimes a pitch unit"""
    S = nx.S
    w = nx.pages[S['PG_W0']] + nx.pages[S['PG_W1']]
    g = bytearray(15)
    g[0:6] = ram[27309:27315]
    g[6], g[7], g[8] = ram[27319], ram[27318], ram[27325]
    g[9:11], g[11], g[12:14], g[14] = ram[29494:29496], ram[29496], ram[27345:27347], ram[27344]
    kind = rng.randrange(4)
    if kind in (0, 3):
        for i in (0, 4):
            v = (int.from_bytes(g[i:i + 2], 'little') + rng.choice((-200, -120, 120, 200))) & 0xFFFF
            g[i:i + 2] = v.to_bytes(2, 'little')
    if kind in (1, 3):
        g[6] = (g[6] + rng.choice((-2, 2))) % 72
    if kind == 2:
        g[7] = (g[7] + rng.choice((-1, 1))) % 72
    o = S['prev'] - 0x4000
    w[o:o + 15] = g
    w[S['prev_ok'] - 0x4000] = 1
    nx.pages[S['PG_W0']], nx.pages[S['PG_W1']] = w[:8192], w[8192:]


def plant_ov(nx, rng):
    """M3b: a view shown before with overlays: sprites on, 12 random sprites opaque ink (ov_nz set): the build must
    clear what is stale and turn the sprites off over a non-view screen"""
    S = nx.S
    nx.nr[0x15] = 1
    w = nx.pages[S['PG_W0']] + nx.pages[S['PG_W1']]
    for k in rng.sample(range(84), 12):
        nx.pat[k * 128:(k + 1) * 128] = bytes([0x22]) * 128
        w[S['ov_nz'] - 0x4000 + k] = 1
    nx.pages[S['PG_W0']], nx.pages[S['PG_W1']] = w[:8192], w[8192:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('states', nargs='?', default='m0_states.bin')
    ap.add_argument('every', nargs='?', type=int, default=100)
    ap.add_argument('--irq', action='store_true', help='frame interrupts at the real rate')
    ap.add_argument('--pace', action='store_true', help='with --irq: the block\'s end time against the original\'s')
    ap.add_argument('--tween', action='store_true', help='plant a previous camera: in-between views are drawn')
    ap.add_argument('--prefix', default='cm3')
    ap.add_argument('--show', type=int, default=3)
    ap.add_argument('--noasm', action='store_true')
    ap.add_argument('--from', dest='start', type=int, default=0)
    ap.add_argument('--phase', type=int, default=None, help='a fixed interrupt phase (28 MHz T into the frame)')
    ap.add_argument('--only', default='', help='comma-separated state indices (in place of every N-th)')
    a = ap.parse_args()
    only = {int(x) for x in a.only.split(',') if x}
    if a.prefix == 'cm3' and not a.noasm:
        assemble('cm3')
    S = syms(a.prefix)
    res = collections.Counter()
    bad, tt, dpace, ntw, fins, minsp = [], [], [], [], [], 0xFFFF
    rng = random.Random(11)
    t0 = time.time()
    skip = set(range(VP, VP + 40))
    for ad, old, op, sym in sites_for(S):
        skip.update(range(ad, ad + len(old) // 2))
    for k, (frame, regs, ram) in enumerate(states(a.states)):
        if (k not in only if only else k % a.every) or k < a.start:
            continue
        period = FRAME if a.irq else 0
        phase = (rng.randrange(FRAME) if a.phase is None else a.phase) if a.irq else 0
        nx = Next(ram, a.prefix, S, period=period)
        nx.count_main = a.pace
        nx.acc = phase
        if a.tween:
            plant_prev(nx, ram, rng)
            if 'ov_up' in S:
                plant_ov(nx, rng)
        R = nx.R
        for i in range(24):
            R[i] = regs[i]
        R[PC], R[T], R[26] = 34142, 0, 1 if a.irq else 0
        got = {}

        def at_raster(n):
            got['before'] = bytearray(n.rom) + bytearray(n.game_ram())
            prefill(n, got['before'])

        def at_rend(n):                 # 0x9F0B: the raster done, before the centre marker
            got['S'] = bytes(n.game_ram()[BUF - 0x4000:BUF - 0x4000 + 2688])

        def at_draw(n):                 # the final raster's entry: after a copy the hidden view = the last one
            wk = wk_of(n)
            if wk[S['tw_on'] - 0x4000]:
                got['tw'] = got.get('tw', 0) + 1
                return
            if not wk[S['nfull'] - 0x4000] and not wk[S['in_sky'] - 0x4000]:
                got['copy'] = view(n, wk[S['in_l2page'] - 0x4000])[0] == view(n, wk[S['l2last'] - 0x4000])[0]
        inr = [0]

        def in_renderer(n):
            inr[0] += 1
        watch = {0x8599: at_raster, S['isr_full']: in_renderer, S['raster']: at_draw}
        if 'ov_up' in S:
            watch[0x9F0B] = at_rend
        ok = nx.run(END, watch,
                    max_ins=60_000_000 if period else 3_000_000)
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
        wk = wk_of(nx)
        shown, hidden, last = wk[S['l2shown'] - 0x4000], wk[S['in_l2page'] - 0x4000], wk[S['l2last'] - 0x4000]
        g = nx.game_ram()
        nonview = before[0x7349] != 0
        if nonview:
            res['non-view screens (Layer 2 off)'] += 1
            if nx.nr.get(0x69) != 0 or shown != S['PG_LA']:
                errs.append('non-view: NR 0x69 = %s, shown page %d' % (nx.nr.get(0x69), shown))
            if 'ov_up' in S and nx.nr.get(0x15, 0) & 1:
                errs.append('non-view: sprites on')
        else:
            if shown == S['PG_LA'] or hidden in (shown, S['PG_LA'] if False else shown) or last != shown \
                    or nx.nr.get(0x12) != shown // 2 or nx.nr.get(0x69) != 0x80:
                errs.append('flip: shown %d hidden %d last %d NR 0x12 = %s NR 0x69 = %s' % (shown, hidden, last, nx.nr.get(0x12), nx.nr.get(0x69)))
            rows, outside = view(nx, shown)
            if outside:
                errs.append('%d bytes outside the view' % outside)
            if got.get('copy') is False:
                errs.append('the copy of the last view is wrong')
            if rows != want:
                d = [(r, p, want[r][p], rows[r][p]) for r in range(112) for p in range(192) if want[r][p] != rows[r][p]]
                errs.append('%d pixels differ %s' % (len(d), d[:6]))
            rows_a, outside_a = view(nx, S['PG_LA'])
            if outside_a or any(rows_a[r][p] != STALE + bit(before, r, p) for r in range(112) for p in range(192)):
                errs.append('the bank shown before has changed')
            if nx.pal.get(1) is None or len([i for i in range(68) if i in nx.pal]) != 68:
                errs.append('palette not written')
            for other in (S['PG_LB'], S['PG_LC']):
                if other != shown and view(nx, other)[1]:
                    errs.append('bytes outside the view in bank %d' % other)
            res['  cleared' if before[27402] and not before[29523] else '  not cleared (full-screen record)' if before[29523]
                else '  not cleared (27402 = 0): copied'] += 1
            ntw.append(wk[S['tw_n'] - 0x4000])
            if a.tween and got.get('tw', 0) != wk[S['tw_n'] - 0x4000]:
                errs.append('in-between views: %s rasters, counter %d' % (got.get('tw'), wk[S['tw_n'] - 0x4000]))
            if 'ov_up' in S:
                if nx.nr.get(0x15) != 1:
                    errs.append('sprites: NR 0x15 = %s' % nx.nr.get(0x15))
                if 'S' not in got:
                    errs.append('no raster end (0x9F0B) seen')
                else:
                    e, n = overlay_errors(nx, g, got['S'], before[27353])
                    errs += e
                    if n:
                        res['  with overlay pixels'] += 1
        if nx.slots != GAME or nx.nr[7] & 3 or g[VP + 10 - 0x4000] or g[VP + 30 - 0x4000]:
            errs.append('end state: slots %s speed %d window %d wait %d' % (nx.slots, nx.nr[7] & 3, g[VP + 10 - 0x4000], g[VP + 30 - 0x4000]))
        if not period:
            sb = Sandbox(ram, regs)
            if not sb.to(END):
                errs.append('reference did not reach the end')
            else:
                dr = [i for i in list(range(13)) + [14] + list(range(16, 25)) if R[i] != sb.R[i]]
                if dr:
                    errs.append('registers differ: %s' % dr)
                sp = R[SP]
                dm = [x for x in range(0x4000, 0x10000) if g[x - 0x4000] != sb.m[x] and x not in skip and not sp - 96 <= x < sp]
                if dm:
                    res['  redraws with RAM differences'] += 1
                    for x in dm:
                        res['    RAM %d (0x%04X)' % (x, x)] += 1
        else:
            res['interrupts'] += nx.irqs
            res['interrupts lost'] += nx.lost
            res['interrupts inside the renderer'] += inr[0]
            minsp = min(minsp, nx.minsp)
            if a.pace:
                ox = Next(ram, a.prefix, S, sites=False, period=period)
                ox.count_main = True
                ox.acc = phase
                for i in range(24):
                    ox.R[i] = regs[i]
                ox.R[PC], ox.R[T], ox.R[26] = 34142, 0, 1
                if ox.run(END, max_ins=60_000_000):
                    dpace.append(((nx.clock - ox.clock) / FRAME, ox.clock / FRAME, (k, phase), nx.nmain == ox.nmain, nx.nmain - ox.nmain))
                    res['interrupts in the original'] += ox.irqs
                    res['interrupts lost in the original'] += ox.lost
        res['redraws %s' % ('OK' if not errs else 'FAILED')] += 1
        tt.append(R[T])
        if errs and len(bad) < a.show:
            bad.append((k, frame, errs[:4]))
    for kk, v in sorted(res.items()):
        print('  %-44s %d' % (kk, v))
    if ntw:
        print('  in-between views per redraw: median %d  max %d  redraws with any %d / %d'
              % (statistics.median(ntw), max(ntw), sum(1 for x in ntw if x), len(ntw)))
    if a.irq:
        print('  lowest SP at an interrupt entry: 0x%04X' % minsp)
    if dpace:
        d = sorted(x[0] for x in dpace)
        print('  block end, M3 - original (frames): median %+.2f  10%% %+.2f  90%% %+.2f  min %+.2f  max %+.2f  (n %d; original median %.1f frames)'
              % (statistics.median(d), d[len(d) // 10], d[9 * len(d) // 10], d[0], d[-1], len(d), statistics.median(x[1] for x in dpace)))
        for x in sorted(dpace, key=lambda x: -abs(x[0]))[:8]:
            print('    state %s: %+.2f frames (original %.1f)' % (x[2], x[0], x[1]))
        same = [x for x in dpace if x[3]]
        if same:
            d = sorted(x[0] for x in same)
            print('  the same game path (main-line instructions equal): n %d  median %+.2f  min %+.2f  max %+.2f frames'
                  % (len(d), statistics.median(d), d[0], d[-1]))
        oth = [x for x in dpace if not x[3]]
        if oth:
            print('  a different game path (real-time state read by the game; reported, not a pace error): n %d  worst %s'
                  % (len(oth), sorted(((round(x[0], 1), x[2], x[4]) for x in oth), key=lambda y: -abs(y[0]))[:5]))
        off = [x for x in same if not -1.0 <= x[0] <= 4.0]
        if off:
            print('  PACE: %d redraws on the same game path end more than 1 frame early or 4 late' % len(off))
            bad.append((off[0][2][0], 0, ['pace %+.2f frames' % off[0][0], str(sorted((round(x[0], 1), x[2]) for x in off))]))
    print('  (%.0f s)' % (time.time() - t0))
    for e in bad:
        print('  state %d frame %d: %s' % e)
    return 1 if bad or not res['redraws OK'] else 0


if __name__ == '__main__':
    sys.exit(main())
