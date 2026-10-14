# Which frames the composite figures use, by owner: IY at 0x82DF when IX = 0xE600 (temp descriptor):
# 0xE644 = the hero, 0xE7C2 + 40k = others. Usage: python hero_frames.py RZX
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..', 'tk', 'nexclash-0.1.4'))
from nexclash import simrun


class H:
    sim = None
    n = 0
    use = collections.defaultdict(collections.Counter)
    first = {}

    def on_sim(self, sim):
        self.sim = sim

    def on_frame(self, n):
        self.n = n

    def before(self, pc):
        if pc == 0x82DF:
            r, m = self.sim.registers, self.sim.memory
            ix, iy = r[8] * 256 + r[9], r[10] * 256 + r[11]
            if m[ix + 3] & 1:
                owner = 'hero' if ix == 0xE600 and iy == 0xE644 else \
                        'composite %04X' % iy if ix == 0xE600 else 'table'
                self.use[owner][m[ix]] += 1
                self.first.setdefault((owner, m[ix]), self.n)


h = H()
simrun.play_rzx(sys.argv[1], h)
for owner, c in sorted(h.use.items()):
    print(owner, ':', ' '.join('%d(%d,@%d)' % (f, k, h.first[(owner, f)]) for f, k in sorted(c.items())))
