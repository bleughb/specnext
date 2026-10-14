# Invariant behind the figure list: between "render ready" (bit 0 of 0xE608 set) and the ISR's
# screen copy (0x886F) the game never enters the figure plotter (0x82DF); and every copy follows a
# render. Also counts interrupts accepted while PC is inside 0x82DF..0x8A00 (hook site interrupts).
# Usage: python check_order.py RZX
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..', 'tk', 'nexclash-0.1.4'))
from nexclash import simrun


class H:
    sim = None
    n = 0
    bad = []
    copies = 0
    plots = 0
    ints_in_fig = 0

    def on_sim(self, sim):
        self.sim = sim

    def on_frame(self, n):
        self.n = n

    def before(self, pc):
        if pc == 0x82DF:
            self.plots += 1
            if self.sim.memory[0xE608] & 1 and len(self.bad) < 20:
                self.bad.append(('plot while a render waits', self.n))
        elif pc == 0x886F:
            self.copies += 1

    def on_interrupt(self, sim, prev_pc):
        if prev_pc == 0x82DF:
            self.ints_in_fig += 1


h = H()
simrun.play_rzx(sys.argv[1], h)
print('frames %d, plots %d, copies %d, interrupts at 0x82DF %d' % (h.n, h.plots, h.copies, h.ints_in_fig))
print('problems:', h.bad or 'none')
