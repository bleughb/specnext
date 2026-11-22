"""Castle Master E3 step 1: per main-loop iteration (0x8542 entry to the next), the recording's wall time and
the counters a pacing model could use.

Wall time: frames between the two 0x8542 entries, the fraction inside a frame taken from the simulator's T
(uncontended) - the RZX's own clock is the frame. Counters per iteration (main code / ISR apart):
  t_main, t_isr      simulator T (3.5 MHz, no contention)
  c_main, c_isr      memory accesses (fetch + data) to 0x4000-0x7FFF = contended on a 48K
  calls of the stages and of the maths / span / polygon routines; span bytes written by the filler.
Writes e3_iters.csv. Usage: python -I e3_probe.py [--stop N] [-o CSV]
"""
import argparse, collections, csv, sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import simrun

ENTRY = 0x8542
COUNT = {0xA1FD: 'm8x16', 0xA253: 'm16', 0xA2C1: 'div', 0xA348: 'm8x8', 0x9696: 'span', 0x9448: 'poly',
         0x85C9: 'obj', 0x8D4F: 'sect', 0x9776: 'matrix', 0x9D8A: 'clip', 0xBE03: 'panel', 0x9EA3: 'raster',
         0xA38D: 'copy', 0xA3F4: 'clear', 0x9F49: 'logic', 0xCA4E: 'print'}
FILLER = range(0x969E, 0x9732)
FIELDS = ['frame', 'pos0', 'pos1', 'frames', 'caller', 't_main', 't_isr', 'c_main', 'c_isr', 'ints',
          'span_bytes', 'dlist'] + sorted(set(COUNT.values()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stop', type=int, default=15000)
    ap.add_argument('-o', default=r'C:/1NEXT/castle_master_work/e3_iters.csv')
    a = ap.parse_args()
    st = {'sim': None, 'isr': False, 'frame': 0, 'ft': {}, 'cur': None}
    rows = []
    pending = []                                 # iterations waiting for their end frame's total T

    def pos(fr, t):
        return (fr, t)

    def new(caller):
        c = collections.Counter()
        c['caller'] = caller
        return c

    class H:
        def on_sim(self, sim):
            st['sim'] = sim

        def on_frame(self, n):                   # the replay resets T to 0 at each frame: keep each frame's length
            st['ft'][st['frame']] = st.get('lastT', 0)
            st['frame'] = n

        def on_interrupt(self, sim, prev_pc):
            st['isr'] = True
            if st['cur'] is not None:
                st['cur']['ints'] += 1

        def before(self, pc):
            if pc == 0xC161:
                st['isr'] = False
            if st['isr']:
                return
            c = st['cur']
            if pc == ENTRY:
                R = st['sim'].registers
                p = (st['frame'], R[25])
                m = st['sim'].memory
                caller = (m[R[12]] | m[R[12] + 1] << 8) - 3
                if c is not None:
                    c['end'] = p
                    pending.append(c)
                c = st['cur'] = new(caller)
                c['start'] = p
            if c is not None and pc in COUNT:
                c[COUNT[pc]] += 1
                if pc == 0x9EA3:
                    c['dlist'] += st['sim'].memory[29502]

        def after(self, pc, dt):
            st['lastT'] = st['sim'].registers[25]
            c = st['cur']
            if c is not None:
                c['t_isr' if st['isr'] else 't_main'] += dt

        def on_read(self, ad, pc, mem):
            c = st['cur']
            if c is not None and 0x4000 <= ad < 0x8000:
                c['c_isr' if st['isr'] else 'c_main'] += 1

        def on_write(self, ad, v, pc, mem):
            c = st['cur']
            if c is not None:
                if 0x4000 <= ad < 0x8000:
                    c['c_isr' if st['isr'] else 'c_main'] += 1
                if not st['isr'] and pc in FILLER and 0x5CBC <= ad < 0x6754:
                    c['span_bytes'] += 1

    simrun.play_rzx(r'C:/dev/castlemaster/castle.rzx', H(), stop=a.stop)
    ft = st['ft']

    def wall(p):
        fr, t = p
        if not ft.get(fr):
            return None
        return fr + t / ft[fr]
    with open(a.o, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(FIELDS)
        n = 0
        for c in pending:
            w0, w1 = wall(c['start']), wall(c['end'])
            if w0 is None or w1 is None:
                continue
            c['frame'], c['pos0'], c['pos1'], c['frames'] = c['start'][0], round(w0, 4), round(w1, 4), round(w1 - w0, 4)
            w.writerow([c[k] for k in FIELDS])
            n += 1
    print('iterations', n, 'frames', st['frame'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
