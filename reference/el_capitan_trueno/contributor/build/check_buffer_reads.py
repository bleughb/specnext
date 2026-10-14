# Who reads the window buffer 0xF2E0-0xFFFF (pixels) in the RZX, by PC: count and first frame.
# Expected readers: the screen copy (0x8915..), the plotter (masked AND/OR), the restore; anything
# else may test figure pixels (collision) and would change if the figures were not drawn.
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
        if 0xF2E0 <= addr <= 0xFFFF and addr != pc:
            r = self.reads.get(pc)
            if r is None:
                self.reads[pc] = [1, self.n]
            else:
                r[0] += 1


h = H()
simrun.play_rzx(sys.argv[1], h)
for pc, (cnt, first) in sorted(h.reads.items()):
    print('PC 0x%04X x%d (first frame %d)' % (pc, cnt, first))
print('done,', h.n, 'frames')
