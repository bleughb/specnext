"""Castle Master M3b probe: which overlay writers run while M3a shows Layer 2 over the view.

Layer 2 state as M3a decides it: at each show site 0x859C (and the second path's 0xB638), (0x7349) = 0 ->
Layer 2 on, else off. Census over the RZX, main code only (the ISR apart), by writer PC:
  buf   writes into the view buffer outside the render part of a redraw (34142 .. first copier call)
  scr   writes to the view's screen bytes by anything but the copiers 0xA38D-0xA3F3 / 0xB6C3
per writer: writes, frames, frames with Layer 2 on, the routine's entry (the last CALL target seen).
Also: copier calls with Layer 2 on whose buffer differs from the buffer at the raster's end (in-buffer overlays
that reach the screen), and how many bytes differ.
Usage: python -I m3b_probe.py [--stop N]
"""
import argparse, collections, sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import simrun

BLOCK, RAST_END, COPIER = 34142, 0x859C, 0xA38D
COPIERS = set(range(0xA38D, 0xA3F4)) | {0xB6C3}
BUF0, BUF1 = 0x5CBC, 0x6754


def view_scr(a):
    o = a - 0x4000
    y = ((o >> 11) << 6) | ((o >> 5) & 7) << 3 | (o >> 8) & 7
    return 32 <= y < 144 and 4 <= (o & 31) < 28


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stop', type=int, default=None)
    a = ap.parse_args()
    st = {'isr': False, 'f': 0, 'in': False, 'copied': False, 'l2': False, 'S': None, 'sim': None}
    W = collections.defaultdict(lambda: {'n': 0, 'frames': set(), 'l2frames': set()})
    cp = collections.Counter()
    ndiff = []

    class H:
        def on_sim(self, s):
            st['sim'] = s

        def on_frame(self, n):
            st['f'] = n

        def on_interrupt(self, s, p):
            st['isr'] = True

        def before(self, pc):
            if pc == 0xC161:
                st['isr'] = False
            if st['isr']:
                return
            m = st['sim'].memory
            if pc == BLOCK and not st['in']:
                st['in'], st['copied'] = True, False
            elif pc == 0x8599 and st['in']:          # the raster call: S after it (next stop at 0x859C)
                st['want_s'] = True
            elif pc in (0x859C, 0xB638):
                st['l2'] = m[0x7349] == 0
                if st.pop('want_s', False) or pc == 0xB638:
                    st['S'] = bytes(m[BUF0:BUF1])
            elif pc == COPIER:
                if st['in']:
                    st['copied'] = True
                if st['l2'] and st['S'] is not None:
                    d = sum(1 for x, y in zip(m[BUF0:BUF1], st['S']) if x != y)
                    cp['copies, Layer 2 on'] += 1
                    if d:
                        cp['  of them with buffer != S'] += 1
                        ndiff.append(d)
            elif pc == 0x859F:
                st['in'] = False

        def on_write(self, ad, v, pc, mem):
            if st['isr'] or pc in COPIERS:
                return
            kind = None
            if BUF0 <= ad < BUF1 and not (st['in'] and not st['copied']):
                kind = 'buf'
            elif 0x4000 <= ad < 0x5800 and view_scr(ad):
                kind = 'scr'
            if kind:
                w = W[(kind, pc)]
                w['n'] += 1
                w['frames'].add(st['f'])
                if st['l2']:
                    w['l2frames'].add(st['f'])

    simrun.play_rzx(r'C:/dev/castlemaster/castle.rzx', H(), stop=a.stop)
    for (kind, pc), w in sorted(W.items(), key=lambda kv: (kv[0][0], -len(kv[1]['l2frames']))):
        print('%s %04X writes %8d frames %6d with Layer 2 on %6d' % (kind, pc, w['n'], len(w['frames']), len(w['l2frames'])))
    for k, v in cp.items():
        print(k, v)
    if ndiff:
        ndiff.sort()
        print('bytes differing: median %d max %d' % (ndiff[len(ndiff) // 2], ndiff[-1]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
