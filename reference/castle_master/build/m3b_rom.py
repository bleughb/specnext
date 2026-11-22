"""Castle Master M3b: does the game read or execute the ROM (0x0000-0x3FFF) anywhere in the recording?
If not, the alt ROM below the free 0xFF area can hold more of the build's plain-state code.
Usage: python -I m3b_rom.py [--stop N]"""
import argparse, collections, sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import simrun


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stop', type=int, default=None)
    a = ap.parse_args()
    reads = collections.Counter()
    st = {'f': 0, 'first': {}}

    class H:
        read_filter = (0x4000, set())

        def on_frame(self, n):
            st['f'] = n

        def on_read(self, ad, pc, mem):
            if ad < 0x4000:
                k = ('exec' if ad == pc else 'read', pc, ad & 0xFF00)
                reads[k] += 1
                st['first'].setdefault(k, st['f'])

    simrun.play_rzx(r'C:/dev/castlemaster/castle.rzx', H(), stop=a.stop)
    print('ROM accesses:', sum(reads.values()))
    for k, n in reads.most_common(40):
        print('  %s pc %04X page %04X: %d (first frame %d)' % (k[0], k[1], k[2], n, st['first'][k]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
