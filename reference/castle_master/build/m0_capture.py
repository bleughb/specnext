"""Castle Master M0: RAM + registers at every redraw-block start (34142, (29503) bit 2 path), whole recording.
Each record lets m0_*.py rerun the original pipeline offline in a sandbox (E2: the block from these states
rebuilds the game's own result) and compare a ported stage against it.

File m0_states.bin: per record  'CMS0' | frame u32 | 29 regs u16 | zlen u32 | zlib(64K RAM)
Usage: python m0_capture.py [--stop N]
"""
import argparse, struct, sys, zlib
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import simrun

BLOCK, DONE = 34142, 0x859F
OUT = r'C:/1NEXT/castle_master_work/m0_states.bin'


def read_states(path=OUT):
    with open(path, 'rb') as f:
        while True:
            h = f.read(4)
            if not h:
                return
            assert h == b'CMS0'
            frame, = struct.unpack('<I', f.read(4))
            regs = list(struct.unpack('<29H', f.read(58)))
            n, = struct.unpack('<I', f.read(4))
            yield frame, regs, zlib.decompress(f.read(n))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stop', type=int, default=167134)
    a = ap.parse_args()
    st = {'sim': None, 'f': 0, 'isr': False, 'in': False, 'n': 0}
    out = open(OUT, 'wb')

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
            if pc == BLOCK and not st['in']:
                st['in'] = True
                s = st['sim']
                m = s.memory
                ram = bytes(m[0:65536]) if isinstance(m, (bytes, bytearray)) else bytes(m[i] for i in range(65536))
                z = zlib.compress(ram, 6)
                regs = [v & 0xFFFF for v in list(s.registers)[:29]] + [0] * max(0, 29 - len(s.registers))
                out.write(b'CMS0' + struct.pack('<I', st['f']) + struct.pack('<29H', *regs) + struct.pack('<I', len(z)) + z)
                st['n'] += 1
            elif pc == DONE:
                st['in'] = False

    simrun.play_rzx(r'C:/dev/castlemaster/castle.rzx', H(), stop=a.stop)
    out.close()
    print('states', st['n'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
