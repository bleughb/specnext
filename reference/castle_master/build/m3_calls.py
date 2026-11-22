"""Castle Master: T a call by routine from m3_sim.py --prof FILE (+ FILE.n). Usage: python m3_calls.py FILE [prefix] [top]"""
import json, sys, bisect, collections
from m2_lib import syms


def load(f, prefix):
    d = json.load(open(f))
    nn = json.load(open(f + '.n'))
    S = syms(prefix)
    lab = sorted((v, k) for k, v in S.items() if '.' not in k and v < 0x10000 and not k.isupper())
    addrs = [v for v, _ in lab]
    by, cnt = collections.Counter(), collections.Counter()
    for s0, s2, pc, t in d['prof']:
        if pc >= 0x4000 and s2 == 10:
            name = 'GAME'
        else:
            i = bisect.bisect_right(addrs, pc) - 1
            name = lab[i][1] if i >= 0 else '?'
        by[name] += t
    rev = {v: k for v, k in lab}
    for s0, s2, pc, c in nn:
        if not (pc >= 0x4000 and s2 == 10) and pc in rev:
            cnt[rev[pc]] += c
    return d['n'], by, cnt


def main():
    f = sys.argv[1]
    prefix = sys.argv[2] if len(sys.argv) > 2 else 'cm3'
    top = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    n, by, cnt = load(f, prefix)
    tot = sum(by.values())
    print('%d redraws, %.0f T a redraw' % (n, tot / n))
    for name, t in by.most_common(top):
        c = cnt.get(name, 0)
        print('  %-14s %9.0f T/redraw %5.1f %%  %8.1f calls/redraw  %8.0f T/call' % (name, t / n, 100 * t / tot, c / n, t / c if c else 0))


if __name__ == '__main__':
    main()
