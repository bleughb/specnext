"""Castle Master M3 in JNext (headless): a NEX with random play; pictures every N frames (or every frame in a
window); a log line at the block's start (0x855E), the show site (0x859C), the block's end (0x859F) and, in the M3
build, at every view put on screen (flip). Prints: block time per update, views per update, views per second.
The same script runs the PLAIN conversion (--plain: no hooks) for the original's numbers.
Usage: python m3_jnext.py [nex] [--plain] [--frames 3000] [--every 100] [--burst F0 F1] [-o DIR] [--seed 1]
"""
import argparse, os, statistics, sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
W = r'C:/1NEXT/castle_master_work/'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('nex', nargs='?', default=W + 'castle_master_m3.nex')
    ap.add_argument('--plain', action='store_true')
    ap.add_argument('--frames', type=int, default=3000)
    ap.add_argument('--every', type=int, default=100)
    ap.add_argument('--burst', type=int, nargs=2, default=None)
    ap.add_argument('-o', default=None)
    ap.add_argument('--jnext', default=r'C:/1NEXT/jnext-1.3.0-windows-x64/jnext.exe')
    ap.add_argument('--card', default=r'C:/1NEXT/cspect-next-2gb.img')
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--prefix', default='cm3')
    a = ap.parse_args()
    out = a.o or W + ('m3_jnext_plain' if a.plain else 'm3_jnext')
    os.environ['NEXCLASH_JNEXT'] = a.jnext
    from nexclash import jnext
    from m2_lib import syms
    S = syms(a.prefix)
    off = jnext.start_frame(a.nex)
    sc = jnext.Script(off)
    sc.rule(jnext.counters())
    sc.start_line(a.nex)
    prof = dict(jnext.GENERIC)
    sc.start_keys(prof)
    sc.frame_input(jnext.schedule(prof, a.frames, a.seed))
    marks = [('B0', 0x855E), ('B1', 0x859C), ('B2', 0x859F), ('LW', 0x9F8C), ('SN', 0xC683)]
    if not a.plain:
        marks += [('FL', S['flip']), ('TW', S['tw_view']), ('WT', S['waittgt']), ('IR', S['isr_full'])]
    for tag, ad in marks:
        sc.rule('on execute %d do\n  log "%s F=${FRAME} C=${CYCLE} %s"\nend\n' % (ad, tag, jnext.CNT))
    os.makedirs(out, exist_ok=True)
    shots = set(range(0, a.frames, a.every))
    if a.burst:
        shots |= set(range(a.burst[0], a.burst[1]))
    for f in sorted(shots):
        sc.at(f, '  screenshot "f%06d.png"\n' % f)
    sc.exit_at(a.frames)
    p = jnext.launch(a.nex, sc.text(), out, a.frames, jnext.card(a.card))
    rc = p.wait(timeout=7200)
    log = os.path.join(out, 'run.log')
    rows = jnext.records(log)
    print('exit', rc, 'log lines', len(rows), 'start', jnext.check_start(log, a.nex), 'errors', jnext.errors(log)[:3])
    cnt = {}
    for t, d in rows:
        cnt[t] = cnt.get(t, 0) + 1
    print('counts', cnt)
    FR = 559104
    blocks, b0, b1 = [], None, None
    views, tws = [], 0
    for t, d in rows:
        if t == 'B0':
            b0, b1, tws, nfl = d, None, 0, 0
        elif t == 'B1' and b0:
            b1 = d
        elif t == 'TW':
            tws += 1
        elif t == 'FL':
            views.append(d['F'])
        elif t == 'B2' and b0 and b1:
            blocks.append((b1['C'] - b0['C'], d['C'] - b0['C'], d['F'] - b0['F'], tws, b0['F']))
            b0 = None
    if blocks:
        geo = [b[0] / FR for b in blocks]
        tot = [b[1] / FR for b in blocks]
        print('  updates %d: block start -> show site median %.2f frames (10%% %.2f, 90%% %.2f); -> block end median %.2f (90%% %.2f, max %.1f)'
              % (len(blocks), statistics.median(geo), sorted(geo)[len(geo) // 10], sorted(geo)[9 * len(geo) // 10],
                 statistics.median(tot), sorted(tot)[9 * len(tot) // 10], max(tot)))
        if not a.plain:
            tw = [b[3] for b in blocks]
            print('  in-between views per update: median %d  mean %.1f  max %d  updates with none %d'
                  % (statistics.median(tw), statistics.mean(tw), max(tw), sum(1 for x in tw if not x)))
            mv = [(b[3] + 1) / (b[1] / FR) * 50 for b in blocks if b[3]]
            if mv:
                print('  views per second inside an update with in-between views: median %.1f  10%% %.1f  90%% %.1f'
                      % (statistics.median(mv), sorted(mv)[len(mv) // 10], sorted(mv)[9 * len(mv) // 10]))
        print('  first blocks (start frame, start -> show site cycles, -> end cycles, in-between):',
              [(b[4], b[0], b[1], b[3]) for b in blocks[:8]])
    if rows:
        print('  last counters', rows[-1])
    return 0


if __name__ == '__main__':
    sys.exit(main())
