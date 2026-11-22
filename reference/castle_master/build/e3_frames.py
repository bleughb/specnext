"""Castle Master E3: every RZX frame's simulator T length and interrupt count -> e3_frames.csv.
Short frames (Fuse closes a frame when an interrupt delayed by DI lands) make the RZX frame count run ahead of
real time; e3_fit.py --realtime uses this file to count such a frame by its T only.
Usage: python -I e3_frames.py [--stop N]
"""
import argparse, sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import simrun


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stop', type=int, default=167134)
    a = ap.parse_args()
    st = {'sim': None, 'f': 0, 'last': 0, 'ints': 0}
    out = open(r'C:/1NEXT/castle_master_work/e3_frames.csv', 'w')
    out.write('frame,t,ints\n')

    class H:
        def on_sim(self, s):
            st['sim'] = s

        def on_frame(self, n):
            if st['f']:
                out.write('%d,%d,%d\n' % (st['f'], st['last'], st['ints']))
            st['f'], st['ints'], st['last'] = n, 0, 0

        def on_interrupt(self, s, p):
            st['ints'] += 1

        def after(self, pc, dt):
            st['last'] = st['sim'].registers[25]

    simrun.play_rzx(r'C:/dev/castlemaster/castle.rzx', H(), stop=a.stop)
    out.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
