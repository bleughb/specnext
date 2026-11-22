"""Castle Master M3b: the cursor descriptors the game passes to 0xCDD2 / 0xCECD in the recording (x, y, width,
rows) - the domain for the cursor sweep. Usage: python -I m3b_curdom.py [--stop N]"""
import argparse, collections, sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import simrun


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stop', type=int, default=None)
    a = ap.parse_args()
    st = {'sim': None}
    seen = collections.Counter()

    class H:
        def on_sim(self, s):
            st['sim'] = s

        def before(self, pc):
            if pc in (0xCDD2, 0xCECD):
                s = st['sim']
                hl = s.registers[6] << 8 | s.registers[7]
                m = s.memory
                seen[(pc, hl, m[hl], m[hl + 1], m[hl + 2], m[hl + 3])] += 1

    simrun.play_rzx(r'C:/dev/castlemaster/castle.rzx', H(), stop=a.stop)
    for pc in (0xCDD2, 0xCECD):
        ks = [k for k in seen if k[0] == pc]
        print('%04X: %d calls, descriptors at %s' % (pc, sum(seen[k] for k in ks), sorted({'%04X' % k[1] for k in ks})))
        for i, nm in ((2, 'x'), (3, 'y'), (4, 'width'), (5, 'rows')):
            v = sorted({k[i] for k in ks})
            print('   %s: %d values, %s' % (nm, len(v), v if len(v) < 40 else '%s .. %s' % (v[:12], v[-12:])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
