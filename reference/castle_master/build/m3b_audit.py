"""Castle Master M3b: the overlay rule as the build applies it, over the whole recording (original game).
S = the buffer at the last show site (0x859C with (0x7349) = 0, or 0xB638), the centre marker taken out as ov_cap
does. Sprites on from such a show until a non-view show or the dissolve 0xB66E.
At each cursor draw / restore return (0xCDD2 / 0xCECD) and each view's copy end, with sprites on:
  - buffer bytes C != S in the view (all-opaque bytes), by the last writer's PC
  - the view's screen attribute (0x5884) against (27353), the attribute the build colours the sprites with
Usage: python -I m3b_audit.py [--stop N]"""
import argparse, collections, sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import simrun

BUF, N = 0x5CBC, 2688
MARK = [(53 + r) * 24 + 11 for r in range(3)] + [56 * 24 + 11, 56 * 24 + 12] + [(57 + r) * 24 + 11 for r in range(3)]
MARKX = [1, 1, 1, 0x0E, 0xE0, 1, 1, 1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stop', type=int, default=None)
    a = ap.parse_args()
    st = {'sim': None, 'f': 0, 'on': False, 'S': None, 'cur': [], 'isr': False}
    writer = {}
    ev = collections.Counter()
    by_pc = collections.Counter()
    ex = collections.defaultdict(list)
    attr = collections.Counter()

    def check(kind):
        m = st['sim'].memory
        S = st['S']
        d = [i for i in range(N) if m[BUF + i] != S[i]]
        ev[kind] += 1
        if d:
            ev[kind + ' with C != S'] += 1
            pcs = collections.Counter(writer.get(BUF + i, -1) for i in d)
            for pc, n in pcs.items():
                by_pc[(kind, pc)] += n
                if len(ex[(kind, pc)]) < 6:
                    ex[(kind, pc)].append((st['f'], n, min(d) // 24, max(d) // 24))
        a1, a2 = m[0x5884], m[27353]
        if a1 != a2:
            attr[(kind, a2, a1)] += 1

    class H:
        def on_sim(self, s):
            st['sim'] = s

        def on_frame(self, n):
            st['f'] = n

        def on_interrupt(self, s, p):
            st['isr'] = True

        def on_write(self, ad, v, pc, mem):
            if BUF <= ad < BUF + N:
                writer[ad] = pc | (0x10000 if st['isr'] else 0)

        def before(self, pc):
            s = st['sim']
            m = s.memory
            if pc == 0xC161:
                st['isr'] = False
            if pc in (0x859C, 0xB638):
                if pc == 0x859C and m[0x7349]:
                    st['on'] = False
                else:
                    S = bytearray(m[BUF:BUF + N])
                    if m[27405] == 0 and m[27409]:
                        for o, x in zip(MARK, MARKX):
                            S[o] ^= x
                    st['S'], st['on'] = S, True
                    st['copy'] = s.registers[12]
            elif pc == 0xB66E:
                st['on'] = False
            elif pc in (0xCDD2, 0xCECD):
                sp = s.registers[12]
                st['cur'].append((m[sp] | m[sp + 1] << 8, sp + 2, 'draw' if pc == 0xCDD2 else 'restore'))
            if st['cur'] and pc == st['cur'][-1][0] and s.registers[12] == st['cur'][-1][1]:
                _, _, kind = st['cur'].pop()
                if st['on']:
                    check('cursor ' + kind)
            if st.get('copy') is not None and pc in (0x859F, 0xB63B) and st['on']:
                st['copy'] = None
                check('view shown')

    simrun.play_rzx(r'C:/dev/castlemaster/castle.rzx', H(), stop=a.stop)
    for k, v in sorted(ev.items()):
        print('%-40s %d' % (k, v))
    print('all-opaque bytes by last writer (kind, PC: bytes; examples frame, bytes, rows):')
    for (kind, pc), n in sorted(by_pc.items(), key=lambda kv: -kv[1])[:30]:
        print('  %-16s %s %8d  %s' % (kind, ('ISR %04X' % (pc & 0xFFFF)) if pc > 0xFFFF else '%04X' % pc if pc >= 0 else 'none', n, ex[(kind, pc)][:4]))
    print('screen attribute != (27353) (kind, (27353), screen: count):')
    for k, n in attr.most_common(12):
        print('  %s %d' % (k, n))
    return 0


if __name__ == '__main__':
    sys.exit(main())
