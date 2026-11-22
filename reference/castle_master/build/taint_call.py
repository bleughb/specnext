"""Taint census for one CALL: bytes last written inside the CALL's dynamic extent (interrupt time
left out) and later read by code outside it.

    python taint_call.py GAME.rzx CALL_ADDR FRAMES OUT.json   (run from the nexclash checkout)
"""
import collections
import json
import sys

sys.path.insert(0, '.')
from nexclash import simrun

rzx, call, frames, out = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3]), sys.argv[4]
ret = (call + 3) & 0xFFFF


class Probe:
    def __init__(self):
        self.sim = None
        self.routine = False
        self.call_sp = None
        self.isr = None
        self.calls = 0
        self.tainted = bytearray(65536)        # 1 = last written inside the routine
        self.writer = [0] * 65536              # pc of that write
        self.hits = collections.Counter()      # (reader pc, in isr) -> reads
        self.addrs = collections.defaultdict(collections.Counter)   # reader pc -> address -> reads
        self.wr = collections.defaultdict(collections.Counter)      # address -> writer pc -> reads consumed
        self.wpages = collections.Counter()

    def on_sim(self, sim):
        self.sim = sim

    def on_interrupt(self, sim, prev_pc):
        m, r = sim.memory, sim.registers
        refused = m[prev_pc] == 0xFB or (m[prev_pc] in (0xDD, 0xFD) and prev_pc == (r[24] - 1) & 0xFFFF)
        if r[26] and not refused and self.isr is None:
            self.isr = (r[24], r[12])

    def before(self, pc):
        r = self.sim.registers
        if self.isr is not None and pc == self.isr[0] and r[12] == self.isr[1]:
            self.isr = None
        if self.isr is not None:
            return
        if self.routine:
            if pc == ret and r[12] == self.call_sp:
                self.routine = False
        elif pc == call:
            self.routine, self.call_sp = True, r[12]
            self.calls += 1

    def on_write(self, a, v, pc, mem):
        a &= 0xFFFF
        if self.routine and self.isr is None and pc != call:
            self.tainted[a] = 1
            self.writer[a] = pc
            self.wpages[a >> 8] += 1
        else:
            self.tainted[a] = 0

    def on_read(self, a, pc, mem):
        a &= 0xFFFF
        if not self.tainted[a]:
            return
        if self.routine and self.isr is None:
            return
        if pc <= a <= pc + 3:
            return
        isr = self.isr is not None
        self.hits[(pc, isr)] += 1
        self.addrs[pc][a] += 1
        self.wr[a][self.writer[a]] += 1


p = Probe()
n = simrun.play_rzx(rzx, p, stop=frames)
readers = []
for (pc, isr), c in sorted(p.hits.items()):
    ad = p.addrs[pc]
    readers.append({'pc': '%04X' % pc, 'isr': isr, 'reads': c, 'distinct': len(ad),
                    'lo': '%04X' % min(ad), 'hi': '%04X' % max(ad)})
addresses = {'%04X' % a: {'reads': sum(w.values()), 'writers': sorted('%04X' % k for k in w),
                          'readers': sorted('%04X' % pc for pc in p.addrs if a in p.addrs[pc])}
             for a, w in sorted(p.wr.items())}
json.dump({'frames': n, 'calls': p.calls, 'readers': readers, 'addresses': addresses,
           'writer_pages': {'%02X' % k: v for k, v in sorted(p.wpages.items())}}, open(out, 'w'))
print('frames', n, 'calls', p.calls, 'readers', len(readers), 'addresses', len(addresses))
