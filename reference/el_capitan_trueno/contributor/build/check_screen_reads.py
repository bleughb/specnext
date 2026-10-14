# Who reads screen memory (0x4000-0x5AFF) in the RZX: PC -> (count, pixel/attr, first frame).
# Opcode/operand fetches are not reads of data (no code runs in screen memory anyway).
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..', 'tk', 'nexclash-0.1.4'))
from nexclash import simrun


class H:
    n = 0
    reads = collections.OrderedDict()

    def on_frame(self, n):
        self.n = n

    def on_read(self, addr, pc, mem):
        if 0x4000 <= addr < 0x5B00 and addr != pc:
            k = (pc, 'attr' if addr >= 0x5800 else 'pixel')
            r = self.reads.get(k)
            if r is None:
                self.reads[k] = [1, self.n, addr]
            else:
                r[0] += 1


h = H()
simrun.play_rzx(sys.argv[1], h)
for (pc, kind), (cnt, first, addr) in h.reads.items():
    print('PC 0x%04X reads %s x%d (first frame %d, e.g. 0x%04X)' % (pc, kind, cnt, first, addr))
print('done,', h.n, 'frames')
