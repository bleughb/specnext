"""Castle Master E3 step 2: model the original's wall time per update from e3_iters.csv (e3_probe.py).

Updates = main-loop iterations that ran the raster (0x9EA3). Fit on frames <= --train, test on the rest.
  physics   frames = (t_main + t_isr + k * (c_main + c_isr)) / 69888       (k = contention T per access)
  runtime   frames = b0 + sum b_i * counter_i  (counters a Next build can keep in its hooks: no T, no contention)
Reports per-update relative error (share within 2 %), and drift over runs of consecutive updates.
Usage: python -I e3_fit.py [--csv e3_iters.csv] [--train 15000]
"""
import argparse, csv, sys
import numpy as np

RUNTIME = ['span', 'span_bytes', 'poly', 'obj', 'clip', 'sect', 'matrix', 'panel', 'copy', 'clear', 'print',
           'm8x16', 'm16', 'div', 'm8x8', 'dlist']


def load(path):
    r = list(csv.DictReader(open(path)))
    return [{k: float(v) for k, v in x.items()} for x in r]


def report(name, y, p, frames_at):
    e = (p - y) / y
    within = np.mean(np.abs(e) <= 0.02)
    print('  %-26s n=%5d  within 2%%: %5.1f %%  median |err| %.2f %%  p95 %.2f %%  max %.1f %%  total %+.3f %%'
          % (name, len(y), 100 * within, 100 * np.median(np.abs(e)), 100 * np.percentile(np.abs(e), 95),
             100 * np.max(np.abs(e)), 100 * (p.sum() - y.sum()) / y.sum()))
    # drift over 10 consecutive updates (what a player walking 10 steps feels)
    if len(y) >= 10:
        k = len(y) // 10 * 10
        ys, ps = y[:k].reshape(-1, 10).sum(1), p[:k].reshape(-1, 10).sum(1)
        e10 = (ps - ys) / ys
        print('  %-26s 10-update runs: within 2%%: %5.1f %%  max %.2f %%' % ('', 100 * np.mean(np.abs(e10) <= 0.02),
                                                                          100 * np.max(np.abs(e10))))
    return e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', default=r'C:/1NEXT/castle_master_work/e3_iters.csv')
    ap.add_argument('--train', type=int, default=15000)
    ap.add_argument('--realtime', action='store_true', help='count a short RZX frame (< 30,000 T, e3_frames.csv) '
                    'by its own T, not as a whole frame')
    a = ap.parse_args()
    rows = [x for x in load(a.csv) if x['raster'] > 0 and x['frames'] > 0]
    if a.realtime:
        fl = {int(x['frame']): int(x['t']) for x in csv.DictReader(open(r'C:/1NEXT/castle_master_work/e3_frames.csv'))}
        n = max(fl) + 2
        w = np.array([1.0 if fl.get(f, 69888) >= 30000 else fl[f] / 69888 for f in range(n)])
        cum = np.concatenate([[0.0], np.cumsum(w)])            # real time at the start of frame f = cum[f]

        def real(pos):
            f = int(pos)
            return cum[f] + (pos - f) * w[f]
        nshort = 0
        for x in rows:
            r = real(x['pos1']) - real(x['pos0'])
            nshort += abs(r - x['frames']) > 0.05
            x['frames'] = r
        print('realtime: %d updates contain a short RZX frame' % nshort)
    tr = [x for x in rows if x['frame'] <= a.train]
    te = [x for x in rows if x['frame'] > a.train] or tr
    print('updates: %d train (frames <= %d), %d test; frames per update median %.1f, min %.2f, max %.1f' % (
        len(tr), a.train, len(te), np.median([x['frames'] for x in rows]), min(x['frames'] for x in rows),
        max(x['frames'] for x in rows)))

    def arr(xs, keys):
        return np.array([[x[k] for k in keys] for x in xs])
    # physics: frames*69888 - t = k*c  -> least squares for k
    y = np.array([x['frames'] for x in tr])
    t = np.array([x['t_main'] + x['t_isr'] for x in tr])
    c = np.array([x['c_main'] + x['c_isr'] for x in tr])
    k = float(np.dot(c, y * 69888 - t) / np.dot(c, c))
    print('physics: contention k = %.3f T per access to 0x4000-0x7FFF' % k)
    for nm, xs in (('physics train', tr), ('physics test', te)):
        yy = np.array([x['frames'] for x in xs])
        pp = np.array([(x['t_main'] + x['t_isr'] + k * (x['c_main'] + x['c_isr'])) / 69888 for x in xs])
        report(nm, yy, pp, None)
    tes = sorted(te, key=lambda x: -abs((x['t_main'] + x['t_isr'] + k * (x['c_main'] + x['c_isr'])) / 69888 / x['frames'] - 1))[:5]
    for x in tes:
        pp = (x['t_main'] + x['t_isr'] + k * (x['c_main'] + x['c_isr'])) / 69888
        print('    physics worst: frame %d frames %.2f pred %.2f ints %d t_isr/int %.0f print %d' % (
            x['frame'], x['frames'], pp, x['ints'], x['t_isr'] / max(1, x['ints']), x['print']))
    # hybrid (what a Next build can do): main-code T from a cycle timer (= t_main: same instructions; the E1
    # maths saving is added back per call), ISR = mean T per frame, contention = counters regression
    CC = ['span_bytes', 'span', 'poly', 'obj', 'print', 'copy', 'clear', 'dlist']
    Xc = np.hstack([np.ones((len(tr), 1)), arr(tr, CC)])
    yc = np.array([x['c_main'] + x['c_isr'] for x in tr])
    g, *_ = np.linalg.lstsq(Xc, yc, rcond=None)
    isr_pf = sum(x['t_isr'] for x in tr) / sum(x['frames'] for x in tr)
    print('hybrid: ISR %.0f T per frame (mean), contention from %s' % (isr_pf, ', '.join(CC)))
    for nm, xs in (('hybrid train', tr), ('hybrid test', te)):
        yy = np.array([x['frames'] for x in xs])
        ch = np.hstack([np.ones((len(xs), 1)), arr(xs, CC)]) @ g
        tm = np.array([x['t_main'] for x in xs])
        pp = (tm + k * ch) / (69888 - isr_pf)
        report(nm, yy, pp, None)
    for nm, xs in (('hybrid+ISR timed train', tr), ('hybrid+ISR timed test', te)):
        yy = np.array([x['frames'] for x in xs])
        ch = np.hstack([np.ones((len(xs), 1)), arr(xs, CC)]) @ g
        tm = np.array([x['t_main'] + x['t_isr'] for x in xs])
        e = report(nm, yy, (tm + k * ch) / 69888, None)
    hy = sorted(zip(np.abs(e), te), key=lambda z: -z[0])[:4]
    for ee, x in hy:
        print('    hybrid worst: frame %d frames %.2f err %.1f %% c_main %d span_bytes %d print %d' % (
            x['frame'], x['frames'], 100 * ee, x['c_main'], x['span_bytes'], x['print']))
    # runtime counters
    X = np.hstack([np.ones((len(tr), 1)), arr(tr, RUNTIME)])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    print('runtime model (frames): const %.3f, %s' % (b[0], ', '.join('%s %.5f' % (n, v) for n, v in zip(RUNTIME, b[1:]))))
    for nm, xs in (('runtime train', tr), ('runtime test', te)):
        Xs = np.hstack([np.ones((len(xs), 1)), arr(xs, RUNTIME)])
        e = report(nm, np.array([x['frames'] for x in xs]), Xs @ b, None)
    worst = sorted(zip(np.abs(e), te), key=lambda z: -z[0])[:5]
    for ee, x in worst:
        print('    worst: frame %d frames %.2f err %.1f %% spans %d clip %d print %d' % (
            x['frame'], x['frames'], 100 * ee, x['span'], x['clip'], x['print']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
