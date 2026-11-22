"""Castle Master M3b: the build's overlay code along the whole recording (the sequence the per-redraw test misses).
One model of the build (sprites, ov_s, ov_nz kept) runs beside the ORIGINAL game's replay; at each of the
build's overlay points its own code runs on the game's RAM as it is there:
  show site 0x859C ((0x7349) = 0) / 0xB638      ov_capw
  after the copy (0x859F / 0xB63B)               ov_scan + ov_flip, sprites on       -> check
  non-view show (0x859C, (0x7349) != 0), 0xB66E  sprites off
  cursor draw / restore return (0xCDD2 / 0xCECD) the descriptor as at entry, ov_cur -> check (inside a show:
                                                 at the flip)
check = the sprites against the overlay rule (m3_sim.overlay_errors; S = the buffer at the show, the marker out).
Usage: python -I m3b_seq.py [--stop N] [--prefix cm3] [--show N]"""
import argparse, collections, sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
sys.path.insert(0, r'C:/1NEXT/castle_master_work')
from nexclash import simrun
from m0_lib import states
from m2_lib import Next, syms, GAME, PC, SP, IFF, VP
from m3_sim import overlay_errors, ULA16

BUF, N = 0x5CBC, 2688
MARK = [(53 + r) * 24 + 11 for r in range(3)] + [56 * 24 + 11, 56 * 24 + 12] + [(57 + r) * 24 + 11 for r in range(3)]
MARKX = [1, 1, 1, 0x0E, 0xE0, 1, 1, 1]
STUB, RET = 0xFE90, 0x5B10                # STUB: in the IM 2 table (seen in both states; the CPU reads only 0xFEFF)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stop', type=int, default=None)
    ap.add_argument('--prefix', default='cm3')
    ap.add_argument('--show', type=int, default=8)
    ap.add_argument('--debug', action='store_true')
    a = ap.parse_args()
    S = syms(a.prefix)
    ram0 = next(iter(states('m0_states.bin')))[2]
    nx = Next(ram0, a.prefix, S, period=0)
    st = {'sim': None, 'f': 0, 'on': False, 'S': None, 'cur': [], 'copy': None}
    res = collections.Counter()
    bad = []

    def call(names, cur=None):
        m, R = nx.mem, nx.R
        assert nx.slots == GAME, (nx.slots, bad[-3:], nx.bad[-3:])
        m[0x4000:0x10000] = list(st['sim'].memory[0x4000:0x10000])
        m[VP:VP + 40] = [0] * 40
        if cur:
            m[VP + 34:VP + 38] = cur
        code = []
        for nm in ['r_enter'] + names + ['r_leave']:
            code += [0xCD, S[nm] & 255, S[nm] >> 8]
        m[STUB:STUB + len(code) + 1] = code + [0xC9]
        R[SP], R[IFF] = 0x5BFE, 0
        R[SP] -= 2
        m[R[SP]], m[R[SP] + 1] = RET & 255, RET >> 8
        R[PC] = STUB
        if not nx.run(RET, max_ins=3_000_000):
            bad.append((st['f'], 'did not return from %s' % names))

    def check(kind):
        res[kind] += 1
        if not nx.nr.get(0x15, 0) & 1:
            bad.append((st['f'], kind + ': sprites off'))
            return
        e, n = overlay_errors(nx, nx.game_ram(), st['S'], st['sim'].memory[27353])
        if n:
            res[kind + ' with overlay pixels'] += 1
        if e and a.debug and not st.get('dbg'):
            st['dbg'] = 1
            wk = nx.page(S['PG_W0']) + nx.page(S['PG_W1'])
            o = S['ov_s'] - 0x4000
            g = nx.game_ram()
            print('DEBUG frame', st['f'], 'ov_s mark', [wk[o + i] for i in MARK], 'buf mark', [g[BUF - 0x4000 + i] for i in MARK],
                  'S mark', [st['S'][i] for i in MARK], 'nz', [wk[S['ov_nz'] - 0x4000 + k] for k in (41, 42)],
                  'new', [wk[S['ov_new'] - 0x4000 + k] for k in (41, 42)], '27405/9', st['sim'].memory[27405], st['sim'].memory[27409])
            print('pat41 rows 3-9', [bytes(nx.pat[41 * 128 + r * 8:41 * 128 + r * 8 + 8]).hex() for r in range(3, 10)])
            print('attr41', nx.sattr[41], 'attr0', nx.sattr[0], 'nr15', nx.nr.get(0x15), 'spal', {k: nx.spal.get(k) for k in (0, 1, 2)})
            from m3_sim import scr
            print('U row 53 bytes 10-11', [g[scr(32 + 53, 4 + c) - 0x4000] for c in (10, 11)], 'C', [g[BUF - 0x4000 + 53 * 24 + c] for c in (10, 11)])
        if e or nx.bad:
            res[kind + ' FAILED'] += 1
            bad.append((st['f'], kind + ': ' + '; '.join(e + nx.bad)[:300]))
            if len(bad) == 1:
                print('HIST', st.get('hist'))
            nx.bad.clear()

    class H:
        def on_sim(self, s):
            st['sim'] = s

        def on_frame(self, n):
            st['f'] = n

        def before(self, pc):
            s = st['sim']
            m = s.memory
            if pc in (0x859C, 0xB638, 0xB66E, 0xA38D, 0x9F19):
                st.setdefault('hist', []).append((st['f'], '%04X' % pc, m[0x7349]))
                st['hist'] = st['hist'][-12:]
            if pc in (0x859C, 0xB638):
                if pc == 0x859C and m[0x7349]:
                    st['on'] = False
                    nx.nextreg(0x15, 0)
                else:
                    Sb = bytearray(m[BUF:BUF + N])
                    if m[27405] == 0 and m[27409]:
                        for o, x in zip(MARK, MARKX):
                            Sb[o] ^= x
                    st['S'], st['on'] = Sb, True
                    st['copy'] = (0x859F if pc == 0x859C else 0xB63B, s.registers[SP])
                    call(['ov_cap'])
            elif pc == 0xB66E:
                st['on'] = False
                nx.nextreg(0x15, 0)
            elif pc in (0xCDD2, 0xCECD):
                sp = s.registers[SP]
                hl = s.registers[6] << 8 | s.registers[7]
                st['cur'].append((m[sp] | m[sp + 1] << 8, sp + 2, 'cursor ' + ('draw' if pc == 0xCDD2 else 'restore'),
                                  list(m[hl:hl + 4])))
            if st['copy'] and pc == st['copy'][0] and s.registers[SP] == st['copy'][1]:
                st['copy'] = None
                call(['ov_scan', 'ov_flip'])
                nx.nextreg(0x15, 1)
                at = m[27353]                   # as setpal at the flip: sprite palette 1 = paper, 2 = ink
                br = 8 if at & 0x40 else 0
                nx.spal[1], nx.spal[2] = ULA16[((at >> 3) & 7) + br], ULA16[(at & 7) + br]
                check('view shown')
            if st['cur'] and pc == st['cur'][-1][0] and s.registers[SP] == st['cur'][-1][1]:
                _, _, kind, d = st['cur'].pop()
                st.setdefault('hist', []).append((st['f'], kind, list(d), list(m[0x7594:0x759D])))
                st['hist'] = st['hist'][-12:]
                if st['on']:
                    call(['ov_cur'], d)
                    if st['copy']:              # inside a show (0x9F19 -> 0xB63D): Layer 2 still shows the last
                        res[kind + ' inside a show (checked at the flip)'] += 1     # view until ov_flip
                    else:
                        check(kind)

    simrun.play_rzx(r'C:/dev/castlemaster/castle.rzx', H(), stop=a.stop)
    for k, v in sorted(res.items()):
        print('%-40s %d' % (k, v))
    print('failures: %d' % len(bad))
    for f, e in bad[:a.show]:
        print('  frame %d: %s' % (f, e))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
