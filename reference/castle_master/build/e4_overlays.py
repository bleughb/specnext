"""Castle Master E4: who draws over the 3D view besides the renderer, how often, where (games/castle_master.md, E4).

Census over the RZX, by writer PC, main code / ISR apart:
  A  writes into the view buffer 0x5CBC-0x6753 outside the render part of a redraw (34142 .. first copier
     0xA38D call) - text / marker / overlay drawn INTO the buffer (shown only when it is next copied)
  B  writes to the screen bytes the copier 0xA38D writes (the view's screen area), by anything but the copier
  C  writes to the attributes of that area
Per writer: writes, frames, phase (outside a redraw / inside one after the copy), address extent (buffer:
row / byte; screen: pixel line / column), and whether the copier later copies its buffer writes (buffer A).
Usage: python -I e4_overlays.py [--stop N]
"""
import argparse, collections, sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import simrun

BLOCK, DONE, COPIER = 34142, 0x859F, 0xA38D
COPIER_CODE = range(0xA38D, 0xA3F4)
BUF0, BUF1 = 0x5CBC, 0x6754


def scr_yx(a):
    """screen address -> (pixel line, column)"""
    o = a - 0x4000
    return ((o >> 11) << 6) | ((o >> 5) & 7) << 3 | (o >> 8) & 7, o & 31


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stop', type=int, default=3000)
    a = ap.parse_args()
    st = {'isr': False, 'f': 0, 'in': False, 'copied': False, 'warm': True}
    view_scr = set()                             # screen bytes the copier writes
    W = collections.defaultdict(lambda: {'n': 0, 'frames': set(), 'phase': collections.Counter(), 'addrs': set()})

    class H:
        def on_frame(self, n):
            st['f'] = n

        def on_interrupt(self, s, p):
            st['isr'] = True

        def before(self, pc):
            if pc == 0xC161:
                st['isr'] = False
            if st['isr']:
                return
            if pc == BLOCK and not st['in']:
                st['in'], st['copied'] = True, False
            elif pc == COPIER and st['in']:
                st['copied'] = True
            elif pc == DONE:
                st['in'] = False

        def on_write(self, ad, v, pc, mem):
            isr = st['isr']
            if not isr and pc in COPIER_CODE and 0x4000 <= ad < 0x5800:
                view_scr.add(ad)
                return
            if BUF0 <= ad < BUF1:
                if not isr and st['in'] and not st['copied']:
                    return                       # the renderer's own work
                kind = 'A'
            elif 0x4000 <= ad < 0x5800:
                kind = 'Bpend'
            elif 0x5800 <= ad < 0x5B00:
                kind = 'Cpend'
            else:
                return
            phase = 'isr' if isr else ('redraw, after copy' if st['in'] else 'outside redraw')
            w = W[(kind, pc, 'isr' if isr else 'main')]
            w['n'] += 1
            if len(w['frames']) < 100000:
                w['frames'].add(st['f'])
            w['phase'][phase] += 1
            w['addrs'].add(ad)

    simrun.play_rzx(r'C:/dev/castlemaster/castle.rzx', H(), stop=a.stop)
    # resolve B / C against the copier's screen area
    lines = sorted({scr_yx(x)[0] for x in view_scr})
    cols = sorted({scr_yx(x)[1] for x in view_scr})
    attrs = {0x5800 + (y >> 3) * 32 + c for y in lines for c in cols}
    print('view on screen: pixel lines %d-%d, columns %d-%d (%d bytes); attribute cells %d' % (
        lines[0], lines[-1], cols[0], cols[-1], len(view_scr), len(attrs)) if view_scr else 'copier never ran')
    out = collections.defaultdict(list)
    for (kind, pc, ctx), w in W.items():
        if kind == 'Bpend':
            hit = w['addrs'] & view_scr
            if not hit:
                continue
            kind = 'B'
        elif kind == 'Cpend':
            hit = w['addrs'] & attrs
            if not hit:
                continue
            kind = 'C'
        else:
            hit = w['addrs']
        out[kind].append((pc, ctx, w, hit))
    for kind, title in (('A', 'A: writes into the view buffer outside the renderer'),
                        ('B', 'B: writes to the view\'s screen bytes, not by the copier'),
                        ('C', 'C: writes to the view\'s attribute cells')):
        print('\n' + title)
        for pc, ctx, w, hit in sorted(out[kind], key=lambda z: -len(z[2]['frames'])):
            if kind == 'A':
                rows = sorted({(x - BUF0) // 24 for x in hit})
                ext = 'buffer rows %d-%d bytes %d-%d' % (rows[0], rows[-1], min((x - BUF0) % 24 for x in hit),
                                                          max((x - BUF0) % 24 for x in hit))
            elif kind == 'B':
                yx = [scr_yx(x) for x in hit]
                ext = 'pixel lines %d-%d cols %d-%d' % (min(y for y, _ in yx), max(y for y, _ in yx),
                                                       min(x for _, x in yx), max(x for _, x in yx))
            else:
                ext = 'cells %d, rows %d-%d' % (len(hit), min((x - 0x5800) // 32 for x in hit), max((x - 0x5800) // 32 for x in hit))
            fr = sorted(w['frames'])
            print('  %04X %-4s writes %8d frames %6d (first %d, last %d) %s | %s' % (
                pc, ctx, w['n'], len(fr), fr[0], fr[-1], ext, dict(w['phase'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
