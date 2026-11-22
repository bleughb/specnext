"""Castle Master M0 step 1: what the 3D pipeline reads, and the game's own polygon lists (games/castle_master.md,
Build design M0).

Window = the redraw block 34142 .. the raster entry 40611 (0x9EA3) inside it (ISR time left out).
Input = a byte read inside the window (not an instruction fetch) that the window did not write first.
Per input address: windows read in, reader PCs, and whether code outside the window (or the ISR) ever writes it
(live game state) or nothing writes it after load (constant: world data, tables).
Also: at each raster entry the polygon list as the raster consumes it (0x9484 entry: (29501) colour, (29544) n,
n (x, y) byte pairs at IX; y up, row = 112 - y) -> m0_polys.jsonl (frame, camera, polygons in draw order).
Usage: python m0_inputs.py [--stop N]      (writes m0_inputs.txt, m0_polys.jsonl)
"""
import argparse, collections, json, sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import simrun

BLOCK, RASTER, POLY = 34142, 40611, 38020
OUT = r'C:/1NEXT/castle_master_work/'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stop', type=int, default=15000)
    a = ap.parse_args()
    st = {'sim': None, 'f': 0, 'isr': False, 'win': False, 'n': 0, 'rec': None}
    wrote = bytearray(65536)                 # written inside the current window
    reads = collections.Counter()            # input address -> windows
    readers = collections.defaultdict(collections.Counter)
    seen_win = [0] * 65536                   # last window id that counted this address
    wr_out = bytearray(65536)                # written outside a window (main code)
    wr_isr = bytearray(65536)                # written by the ISR
    polys = open(OUT + 'm0_polys.jsonl', 'w')

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
            if pc == BLOCK and st['rec'] is None:
                st['win'] = True
                st['n'] += 1
                wrote[:] = bytes(65536)
            elif pc == 0x859F:
                st['win'] = False
            elif pc == RASTER and st['win']:
                st['win'] = False
                cam = [m[a] for a in range(27309, 27320)]
                st['rec'] = {'f': st['f'], 'cam': cam, 'np': m[29502], 'p23': m[29523], 'polys': []}
            elif pc == POLY and st['rec'] is not None:
                n = m[29544]
                ixv = getix(st['sim'])
                st['rec']['polys'].append([m[29501], n, [m[(ixv + k) & 0xFFFF] for k in range(2 * n)]])
            elif pc == 40715 and st['rec'] is not None:
                polys.write(json.dumps(st['rec']) + '\n')
                st['rec'] = None

        def on_read(self, ad, pc, mem):
            if not st['win'] or st['isr'] or 0 <= ad - pc < 4 or wrote[ad]:
                return
            if seen_win[ad] != st['n']:
                seen_win[ad] = st['n']
                reads[ad] += 1
            readers[ad][pc] += 1

        def on_write(self, ad, v, pc, mem):
            if st['isr']:
                wr_isr[ad] = 1
            elif st['win']:
                wrote[ad] = 1
            else:
                wr_out[ad] = 1

    simrun.play_rzx(r'C:/dev/castlemaster/castle.rzx', H(), stop=a.stop)
    polys.close()
    # group contiguous input addresses with the same class
    out = open(OUT + 'm0_inputs.txt', 'w')
    out.write('windows %d (frames <= %d); input addresses %d\n' % (st['n'], a.stop, len(reads)))
    out.write('start  end    bytes class   max-windows readers (top)\n')
    addrs = sorted(reads)
    i = 0
    while i < len(addrs):
        j = i
        cls = lambda x: ('isr' if wr_isr[x] else '') + ('live' if wr_out[x] else '') or 'const'
        c = cls(addrs[i])
        while j + 1 < len(addrs) and addrs[j + 1] - addrs[j] <= 2 and cls(addrs[j + 1]) == c:
            j += 1
        span = addrs[i:j + 1]
        rd = collections.Counter()
        for x in span:
            rd.update(readers[x])
        out.write('%5d  %5d  %5d  %-7s %6d  %s\n' % (span[0], span[-1], len(span), c, max(reads[x] for x in span),
                  ' '.join('%04X:%d' % (p, k) for p, k in rd.most_common(6))))
        i = j + 1
    out.close()
    print('windows', st['n'], 'inputs', len(reads))
    return 0


def getix(sim):
    R = sim.registers
    # skoolkit register order: A F B C D E H L IXh IXl IYh IYl SP I R xA xF xB xC xD xE xH xL PC T IFF IM HALT
    return R[8] << 8 | R[9]


if __name__ == '__main__':
    sys.exit(main())
