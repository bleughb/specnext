# Which frames are plotted through 0x82DF in the RZX (visible descriptors only), by frame, flags and
# caller (return address on the stack). Slow: Python hook on every instruction (~10 min for the RZX).
# Usage: python plotstats.py trueno1.rzx out.json
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..', 'tk', 'nexclash-0.1.4'))
from nexclash import simrun


class H:
    sim = None
    n = 0
    stats = {}

    def on_sim(self, sim):
        self.sim = sim

    def on_frame(self, n):
        self.n = n

    def before(self, pc):
        if pc == 0x82DF:
            r, m = self.sim.registers, self.sim.memory
            ix = r[8] * 256 + r[9]
            if m[ix + 3] & 1:
                sp = r[12]
                key = '%d %d %04X' % (m[ix], m[ix + 3], m[sp] | m[sp + 1] << 8)
                s = self.stats.setdefault(key, [0, self.n])
                s[0] += 1


h = H()
simrun.play_rzx(sys.argv[1], h)
json.dump(h.stats, open(sys.argv[2], 'w'), indent=0)
frames = sorted({int(k.split()[0]) for k in h.stats})
print(len(h.stats), 'keys;', len(frames), 'frames plotted:', frames)
