"""Castle Master M3b: the dissolve copier 0xB66E, by caller, and the Layer 2 state M3 would have when it runs
(set at the show sites 0x859C / 0xB638: (0x7349) = 0 -> on). Usage: python -I m3b_dissolve.py [--stop N]"""
import argparse, collections, sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import simrun


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stop', type=int, default=None)
    a = ap.parse_args()
    st = {'sim': None, 'f': 0, 'l2': False, 'shows': 0}
    calls = collections.defaultdict(list)

    class H:
        def on_sim(self, s):
            st['sim'] = s

        def on_frame(self, n):
            st['f'] = n

        def before(self, pc):
            s = st['sim']
            if pc in (0x859C, 0xB638):
                st['l2'] = s.memory[0x7349] == 0
                st['shows'] += 1
            elif pc == 0xB66E:
                sp = s.registers[12]
                ret = s.memory[sp] | s.memory[sp + 1] << 8
                calls[ret - 3].append((st['f'], st['l2'], st['shows']))

    simrun.play_rzx(r'C:/dev/castlemaster/castle.rzx', H(), stop=a.stop)
    for c, v in sorted(calls.items()):
        on = [x for x in v if x[1]]
        print('caller %04X: %d calls, %d with Layer 2 on; frames %s' % (c, len(v), len(on), [x[0] for x in on][:12]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
