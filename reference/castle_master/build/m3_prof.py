"""Castle Master: where the build's time goes. Reads m3_sim.py --prof FILE (28 MHz T by slot pages and PC).
Usage: python m3_prof.py FILE [prefix] [top N]"""
import json, sys, bisect, collections
from m2_lib import syms

GAME_R = [(0x8D4F, 'game sectors'), (0x9484, 'game filler'), (0x9696, 'game span'), (0x9776, 'game geometry'),
          (0x9D8A, 'game sort'), (0x9EA3, 'game raster top'), (0x9F19, 'game show'), (0xA1FD, 'game maths'),
          (0xA38D, 'game copy'), (0xA3F4, 'game clear'), (0xA569, 'game other A5-BF'), (0xC01F, 'game handler'),
          (0xC162, 'game C1-FF')]


def main():
    d = json.load(open(sys.argv[1]))
    S = syms(sys.argv[2] if len(sys.argv) > 2 else 'cm3')
    top = int(sys.argv[3]) if len(sys.argv) > 3 else 45
    lab = sorted((v, k) for k, v in S.items() if '.' not in k and v < 0x10000 and not k.isupper())
    addrs = [v for v, _ in lab]
    ga = [a for a, _ in GAME_R]
    by, grp = collections.Counter(), collections.Counter()
    for s0, s2, pc, t in d['prof']:
        game = s2 == 10
        if pc >= 0x4000 and game:
            i = bisect.bisect_right(ga, pc) - 1
            name = GAME_R[i][1] if i >= 0 else 'game below 8D4F'
            g = 'the game (own code, handler)'
        else:
            i = bisect.bisect_right(addrs, pc) - 1
            name = lab[i][1] if i >= 0 else '?%04X' % pc
            g = 'hooks (game pages)' if game else 'renderer + glue'
        by[name] += t
        grp[g] += t
    tot = sum(by.values())
    n = d['n']
    print('%d redraws, %.0f T (28 MHz) a redraw = %.2f frames of 559,104' % (n, tot / n, tot / n / 559104))
    for g, t in grp.most_common():
        print('  %-32s %5.1f %%' % (g, 100 * t / tot))
    print('by label (T a redraw, share):')
    for name, t in by.most_common(top):
        print('  %-24s %9.0f  %5.1f %%' % (name, t / n, 100 * t / tot))


if __name__ == '__main__':
    main()
