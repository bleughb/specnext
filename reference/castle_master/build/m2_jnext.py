"""Castle Master M2 in JNext (headless): the NEX with random play; pictures every N frames; a log line at each hook
(renderer cycles per geometry / raster / show from JNext's master-cycle counter), interrupt and 28 MHz totals.
Usage: python m2_jnext.py [nex] [--frames 3000] [--every 100] [-o m2_jnext] [--jnext EXE] [--card IMG] [--seed 1]
"""
import argparse, os, re, statistics, sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
W = r'C:/1NEXT/castle_master_work/'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('nex', nargs='?', default=W + 'castle_master_m2.nex')
    ap.add_argument('--frames', type=int, default=3000)
    ap.add_argument('--every', type=int, default=100)
    ap.add_argument('-o', default=W + 'm2_jnext')
    ap.add_argument('--jnext', default=r'C:/1NEXT/jnext-1.3.0-windows-x64/jnext.exe')
    ap.add_argument('--card', default=r'C:/1NEXT/cspect-next-2gb.img')
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--keys', default='generic')
    a = ap.parse_args()
    os.environ['NEXCLASH_JNEXT'] = a.jnext
    from nexclash import jnext
    from m2_lib import syms
    S = syms()
    off = jnext.start_frame(a.nex)
    sc = jnext.Script(off)
    sc.rule(jnext.counters())
    sc.start_line(a.nex)
    prof = dict(jnext.GENERIC)
    sc.start_keys(prof)
    sc.frame_input(jnext.schedule(prof, a.frames, a.seed))
    for tag, sym in (('GE', 'h_geom'), ('RA', 'h_rast'), ('SH', 'h_show'), ('FL', 'h_flip'), ('ON', 'h_on'), ('OFF', 'h_off')):
        sc.rule('on execute %d do\n  log "%s F=${FRAME} C=${CYCLE} %s"\nend\n' % (S[sym], tag, jnext.CNT))
    for tag, ad in (('GX', 0x8561), ('RX', 0x859C), ('SX', 0x859F)):     # the instruction after each hooked CALL
        sc.rule('on execute %d do\n  log "%s F=${FRAME} C=${CYCLE} %s"\nend\n' % (ad, tag, jnext.CNT))
    sc.rule('on execute %d do\n  log "IR F=${FRAME} C=${CYCLE}"\nend\n' % S['isr_full'])
    os.makedirs(a.o, exist_ok=True)
    for f in range(0, a.frames, a.every):
        sc.at(f, '  screenshot "f%06d.png"\n' % f)
    sc.exit_at(a.frames)
    p = jnext.launch(a.nex, sc.text(), a.o, a.frames, jnext.card(a.card))
    rc = p.wait(timeout=3600)
    log = os.path.join(a.o, 'run.log')
    rows = jnext.records(log)
    print('exit', rc, 'log lines', len(rows), 'start', jnext.check_start(log, a.nex), 'errors', jnext.errors(log)[:3])
    cnt = {}
    for t, d in rows:
        cnt[t] = cnt.get(t, 0) + 1
    print('hook counts', cnt)
    last, dur = {}, {'GE': [], 'RA': [], 'ON': []}
    pair = {'GX': 'GE', 'RX': 'RA', 'SX': 'ON'}
    for t, d in rows:
        if t in dur:
            last[t] = d['C']
        elif t in pair and pair[t] in last:
            dur[pair[t]].append(d['C'] - last.pop(pair[t]))
    for t, name in (('GE', 'geometry hook + the game\'s 0x8D4F'), ('RA', 'raster hook + the game\'s raster'), ('ON', 'show (palette, flip)')):
        if dur[t]:
            v = dur[t]
            print('  %-36s n %d  median %d  max %d master cycles' % (name, len(v), statistics.median(v), max(v)))
    per, g0, fr, f0 = [], None, [], None
    for t, d in rows:
        if t in ('GE', 'GX') and g0 is None:
            g0, f0 = d.get('T28', 0), d['F']
        elif t == 'SX' and g0 is not None:
            per.append(d['T28'] - g0)
            fr.append(d['F'] - f0)
            g0 = None
    if per:
        q = sorted(per)
        print('  renderer per redraw (28 MHz time, JNext): n %d  median %d  90%% %d  max %d master cycles = %.2f / %.2f / %.2f frames'
              % (len(per), statistics.median(per), q[int(0.9 * (len(q) - 1))], max(per), statistics.median(per) / 559104,
                 q[int(0.9 * (len(q) - 1))] / 559104, max(per) / 559104))
        print('  frames per redraw (geometry call to block end): median %d  max %d' % (statistics.median(fr), max(fr)))
    if rows:
        print('  last counters', rows[-1])
    return 0


if __name__ == '__main__':
    sys.exit(main())
