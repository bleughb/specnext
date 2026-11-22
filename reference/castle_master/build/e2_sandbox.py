"""Castle Master E2 (route A): a sandbox render at an unchanged camera = the game's own frame, byte for byte.

For every full redraw in the RZX (block 34142 .. 0x859F in 0x8542, taken when (29503) bit 2 is set):
  G = the view buffer 0x5CBC-0x6753 (incl. the filler's overrun) when the game's copier 0xA38D starts
  S = all RAM at 0x859F (the redraw done) = what route A copies into the sandbox after an update
Sandbox (SkoolKit CSimulator, no interrupts: E5 sends them to the real memory): RAM = S, view buffer
0x5CBC-0x673B filled with junk, registers = the game's at 34142, run 34142 -> 0x859F. Check: buffer at the
sandbox's first 0xA38D = G. Reported apart: which other RAM the re-run changes vs S (re-run side effects),
camera at 0x9776 vs at 0x859F, interrupts the game took during the block (the R / ISR-variable caveat).
Negative controls: --neg yaw (camera yaw +1 step in the sandbox: must differ) | noraster (0x9EA3 skipped: must
differ) | nojunk (no junk fill: a weaker test, informative only) | dlist (display list 0x6754-0x68FF junked
too: must still PASS - the block rebuilds it).
Usage: python -I e2_sandbox.py [--stop N] [--neg X] [--max K] [--timer] [--rsync] [--prevbuf]
"""
import argparse, collections, sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import simrun
import importlib.machinery, importlib.util
# The replay imports SkoolKit from C:/skoolkit-10.1 (no C build); load the compiled CSimulator from the
# pip-installed SkoolKit 10.1 directly (same version).
import glob as _g, os as _o, skoolkit as _sk
_CS = (_g.glob(_o.path.join(_o.path.dirname(_sk.__file__), 'csimulator*.pyd')) + [''])[0]   # SkoolKit's C simulator, wherever it is installed
_spec = importlib.util.spec_from_file_location('csimulator', _CS, loader=importlib.machinery.ExtensionFileLoader('csimulator', _CS))
_mod = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_mod)
CSimulator = _mod.CSimulator

RZX = r'C:/dev/castlemaster/castle.rzx'
BLOCK, DONE, COPIER = 34142, 0x859F, 0xA38D
BUF, BUF_END, CMP_END = 0x5CBC, 0x673C, 0x6754
CAMERA = (27309, 27310, 27311, 27312, 27313, 27314, 27318, 27319)


def sandbox(S, regs, neg, timer=None, rval=None, prev=None):
    m = bytearray(S)
    if timer is not None:                       # 27391 as the game's render read it (the ISR counts it down)
        m[27391] = timer
    if prev is not None:                        # the previous frame's buffer, as the game drew over it
        m[BUF:CMP_END] = prev
    elif neg != 'nojunk':
        m[BUF:BUF_END] = bytes([0x5A, 0xA5]) * ((BUF_END - BUF) // 2)
    if neg == 'dlist':                          # display list + object scratch junked too (expect PASS)
        m[0x6754:0x6900] = bytes([0xC3]) * (0x6900 - 0x6754)
    if neg == 'yaw':
        m[27319] = (m[27319] + 2) % 72
    if neg == 'noraster':                       # the CALL 40611 at 34201 -> 3 NOPs
        m[34201:34204] = b'\0\0\0'
    c = CSimulator(m)
    R = c.registers
    m = c.memory                                 # the C simulator works on its own copy
    for i in range(24):
        R[i] = regs[i]
    R[12] = regs[12]
    R[25] = 0
    R[26] = 0                                    # IFF off: no interrupt is accepted anyway (interrupts=False)
    if rval is not None:                         # R as the game had it at 0xA569 (LD A,R: random 0-19 -> 41970)
        c.run(BLOCK, 0xA569)
        R[15] = rval
        c.run(R[24], COPIER)
    else:
        c.run(BLOCK, COPIER)
    t_copy = R[25]
    got = bytes(m[BUF:CMP_END])
    c.run(R[24], DONE)
    return got, t_copy, R[25], m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stop', type=int, default=3000)
    ap.add_argument('--neg', default=None)
    ap.add_argument('--max', type=int, default=0)
    ap.add_argument('--prevbuf', action='store_true', help='buffer = the game buffer at the block start, not junk')
    ap.add_argument('--rsync', action='store_true', help="set R at 0xA569 to the game's value there")
    ap.add_argument('--timer', action='store_true', help="set 27391 to the value the game's render read at 42076")
    a = ap.parse_args()
    st = {'sim': None, 'in': False, 'regs': None, 'G': None, 'cam': None, 'ints': 0, 'frame': 0}
    res = collections.Counter()
    side = collections.Counter()
    ex = []
    tt = []

    def snap():
        mm = st['sim'].memory
        return bytes(mm[0:65536]) if isinstance(mm, (bytes, bytearray, list)) else bytes(mm[i] for i in range(65536))

    class H:
        def on_sim(self, sim):
            st['sim'] = sim

        def on_frame(self, n):
            st['frame'] = n

        def on_interrupt(self, sim, prev_pc):
            if st['in']:
                st['ints'] += 1

        def before(self, pc):
            if pc == BLOCK and not st['in']:
                st.update(**{'in': True, 'regs': list(st['sim'].registers), 'G': None, 'cam': None, 'ints': 0, 'timer': None, 'rval': None, 'nr': 0,
                             'prev': bytes(st['sim'].memory[x] for x in range(BUF, CMP_END))})
            elif not st['in']:
                return
            elif pc == 0xA569:
                st['nr'] += 1
                if st['rval'] is None:
                    st['rval'] = st['sim'].registers[15]
            elif pc == 42076 and st['timer'] is None:
                st['timer'] = st['sim'].memory[27391]
            elif pc == 0x9776 and st['cam'] is None:
                m = st['sim'].memory
                st['cam'] = bytes(m[x] for x in CAMERA)
            elif pc == COPIER and st['G'] is None:
                m = st['sim'].memory
                st['G'] = bytes(m[x] for x in range(BUF, CMP_END))
            elif pc == DONE:
                st['in'] = False
                if st['G'] is None or (a.max and sum(res.values()) >= a.max):
                    res['no copier'] += st['G'] is None
                    return
                S = snap()
                if bytes(S[x] for x in CAMERA) != st['cam']:
                    res['camera moved in block'] += 1
                got, t_copy, t_all, m = sandbox(S, st['regs'], a.neg, st['timer'] if a.timer else None,
                                                st['rval'] if a.rsync and st['nr'] == 1 else None,
                                                st['prev'] if a.prevbuf else None)
                if st['nr'] > 1:
                    res['0xA569 run more than once'] += 1
                if st['timer'] is not None and st['timer'] != S[27391]:
                    res['27391 changed during block'] += 1
                tt.append(t_all)
                if got == st['G']:
                    res['PASS'] += 1
                else:
                    res['FAIL'] += 1
                    d = [BUF + i for i in range(len(got)) if got[i] != st['G'][i]]
                    if len(ex) < 20:
                        ex.append('frame %d ints %d: %d bytes differ, first %s' % (
                            st['frame'], st['ints'], len(d), ' '.join('%04X game %02X sandbox %02X' % (
                                x, st['G'][x - BUF], got[x - BUF]) for x in d[:4])))
                if st['ints']:
                    res['blocks with interrupts'] += 1
                for x in range(0x4000, 0x10000):
                    if m[x] != S[x] and not (BUF <= x < CMP_END):
                        side[x >> 8] += 1

    simrun.play_rzx(RZX, H(), stop=a.stop)
    print('E2 neg=%s frames<=%d %s' % (a.neg, a.stop, dict(res)))
    if tt:
        s = sorted(tt)
        print('sandbox block T (3.5 MHz T): min %d median %d max %d' % (s[0], s[len(s) // 2], s[-1]))
    print('re-run side effects outside the buffer (RAM page: bytes, summed over renders):',
          ' '.join('%02X:%d' % kv for kv in sorted(side.items())))
    for e in ex:
        print('  ', e)
    ok = res['PASS'] > 0 and res['FAIL'] == 0
    return 0 if (a.neg in (None, 'dlist', 'nojunk')) == ok else 1


if __name__ == '__main__':
    sys.exit(main())
