"""Castle Master M0 side questions (Build design M0):
  1. who calls the raster 0x9EA3 (40611) and the second copier 0xB6C3, in which frames (caller = return address)
  2. does the game touch the ROM (0x0000-0x3FFF): instruction fetches and data reads, main code vs ISR
Usage: python m0_misc.py [--stop N]
"""
import argparse, collections, sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import simrun


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stop', type=int, default=167134)
    a = ap.parse_args()
    st = {'sim': None, 'f': 0, 'isr': False}
    calls = collections.defaultdict(list)           # (target, caller) -> frames
    rom_exec = collections.Counter()
    rom_read = collections.Counter()

    class H:
        read_filter = (0x4000, ())

        def on_sim(self, s):
            st['sim'] = s

        def on_frame(self, n):
            st['f'] = n

        def on_interrupt(self, s, p):
            st['isr'] = True

        def before(self, pc):
            if pc == 0xC161:
                st['isr'] = False
            if pc < 0x4000:
                rom_exec[(pc, st['isr'])] += 1
            if pc in (40611, 0xB6C3) and not st['isr']:
                s = st['sim']
                sp = s.registers[12]
                ret = s.memory[sp] | s.memory[(sp + 1) & 0xFFFF] << 8
                fl = calls[(pc, ret - 3)]
                if not fl or fl[-1] != st['f']:
                    fl.append(st['f'])

        def on_read(self, ad, pc, mem):
            if ad < 0x4000 and pc >= 0x4000:
                rom_read[(pc, st['isr'])] += 1

    simrun.play_rzx(r'C:/dev/castlemaster/castle.rzx', H(), stop=a.stop)
    print('calls (target <- caller): frames, first, last, sample')
    for (t, c), fl in sorted(calls.items()):
        print('  %04X <- %04X  %6d  %6d  %6d  %s' % (t, c, len(fl), fl[0], fl[-1], fl[:: max(1, len(fl) // 6)][:6]))
    print('ROM instruction fetches (pc, isr): %d distinct, %d total' % (len(rom_exec), sum(rom_exec.values())))
    for k, v in rom_exec.most_common(10):
        print('  %04X isr=%s %d' % (k[0], k[1], v))
    print('ROM data reads from RAM code (reader pc, isr): %d distinct, %d total' % (len(rom_read), sum(rom_read.values())))
    for k, v in rom_read.most_common(10):
        print('  %04X isr=%s %d' % (k[0], k[1], v))
    return 0


if __name__ == '__main__':
    sys.exit(main())
