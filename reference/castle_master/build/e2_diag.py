"""Castle Master E2 diagnosis: why a few sandbox renders differ from the game's frame.

For each full redraw block in frames [--from, --stop]: sandbox from S (RAM at 0x859F, as e2_sandbox.py) and
from B (RAM at the block's start 34142); and the bytes the ISR wrote during the block that non-ISR code read
afterwards inside the same block (ISR -> render dataflow), with the reader PCs. Prints only failing blocks.
Usage: python -I e2_diag.py --from F --stop N
"""
import argparse, collections, sys, runpy
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import simrun

E2 = runpy.run_path(r'C:/1NEXT/castle_master_work/e2_sandbox.py', run_name='e2lib')
sandbox, BLOCK, DONE, COPIER, BUF, CMP_END = (E2[k] for k in ('sandbox', 'BLOCK', 'DONE', 'COPIER', 'BUF', 'CMP_END'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--from', dest='frm', type=int, default=0)
    ap.add_argument('--stop', type=int, default=3500)
    a = ap.parse_args()
    st = {'sim': None, 'in': False, 'isr': False, 'frame': 0}
    blk = {}

    def snap():
        mm = st['sim'].memory
        return bytes(mm[i] for i in range(65536)) if not isinstance(mm, (bytes, bytearray, list)) else bytes(mm[:65536])

    class H:
        def on_sim(self, sim):
            st['sim'] = sim

        def on_frame(self, n):
            st['frame'] = n

        def on_interrupt(self, sim, prev_pc):
            st['isr'] = True

        def on_write(self, ad, v, pc, mem):
            if st['in']:
                if st['isr']:
                    blk['isrw'].add(ad)
                else:
                    blk['isrw'].discard(ad)        # the render wrote it again: no ISR -> render flow

        def on_read(self, ad, pc, mem):
            if st['in'] and not st['isr'] and ad in blk['isrw']:
                blk['flow'][(ad, pc)] += 1

        def before(self, pc):
            if pc == 0xC161:
                st['isr'] = False
            if st['frame'] < a.frm:
                return
            if pc == BLOCK and not st['in'] and not st['isr']:
                blk.update(regs=list(st['sim'].registers), B=snap(), G=None, isrw=set(),
                           flow=collections.Counter())
                st['in'] = True
            elif st['in'] and pc == COPIER and blk['G'] is None and not st['isr']:
                m = st['sim'].memory
                blk['G'] = bytes(m[x] for x in range(BUF, CMP_END))
            elif st['in'] and pc == DONE and not st['isr']:
                st['in'] = False
                if blk['G'] is None:
                    return
                S = snap()
                gs = sandbox(S, blk['regs'], None)[0]
                if gs == blk['G']:
                    return
                gb = sandbox(blk['B'], blk['regs'], None)[0]
                d = [BUF + i for i in range(len(gs)) if gs[i] != blk['G'][i]]
                print('frame %d: from S %d bytes differ (%s); from block start: %s' % (
                    st['frame'], len(d), ' '.join('%04X' % x for x in d[:6]),
                    'EQUAL' if gb == blk['G'] else '%d differ' % sum(1 for i in range(len(gb)) if gb[i] != blk['G'][i])))
                ch = [x for x in range(0x4000, 0x10000) if S[x] != blk['B'][x] and not (BUF <= x < 0x6754)]
                fl = sorted(blk['flow'].items(), key=lambda kv: -kv[1])
                print('   ISR->render reads (addr@pc:n):', ' '.join('%d@%04X:%d' % (k[0], k[1], n) for k, n in fl[:12]))
                print('   RAM changed B->S outside buffer: %d bytes, e.g. %s' % (len(ch), ' '.join('%d' % x for x in ch[:16])))
                def fails(sub):
                    m = bytearray(blk['B'])
                    for x in sub:
                        m[x] = S[x]
                    return sandbox(bytes(m), blk['regs'], None)[0] != blk['G']
                cur = ch                      # bisect to a minimal set of S bytes that breaks the render from B
                if fails(cur):
                    n = 2
                    while len(cur) > 1:
                        parts = [cur[i::n] for i in range(n)]
                        hit = next((p for p in parts if fails(p)), None)
                        if hit is not None:
                            cur, n = hit, 2
                        else:
                            comp = next((c for c in ([x for x in cur if x not in set(p)] for p in parts) if fails(c)), None)
                            if comp is not None:
                                cur, n = comp, max(n - 1, 2)
                            elif n < len(cur):
                                n = min(len(cur), n * 2)
                            else:
                                break
                    print('   culprit bytes (B value -> S value):', ' '.join('%d %d->%d' % (x, blk['B'][x], S[x]) for x in cur))

    simrun.play_rzx(r'C:/dev/castlemaster/castle.rzx', H(), stop=a.stop)


if __name__ == '__main__':
    main()
