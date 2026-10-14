# The no-drawing map patch (0x87BE -> 0x3B00, all 0xFF in the ROM) must leave game memory as the
# original over a whole render cycle: from 0xA1F1 (a render starts) to the next 0xA1F1 (copied and
# restored), compare all RAM except the screen; report where they differ (the plotter's generated
# row code is expected to differ). Usage: python check_nodraw.py SNAP.z80 ...
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..', 'tk', 'nexclash-0.1.4'))
from skoolkit.snapshot import Snapshot
from skoolkit.simulator import Simulator
from nexclash.build import rom48


def run(path, patch):
    s = Snapshot.get(path)
    mem = list(rom48()) + list(s.ram(-1))
    if patch:
        mem[0x87BE], mem[0x87BF] = 0x00, 0x3B
    regs = {'A': s.a, 'F': s.f, 'BC': s.bc, 'DE': s.de, 'HL': s.hl, 'IX': s.ix, 'IY': s.iy, 'SP': s.sp,
            'PC': s.pc, 'I': s.i, 'R': s.r, '^AF': s.a2 * 256 + s.f2, '^BC': s.bc2, '^DE': s.de2, '^HL': s.hl2}
    sim = Simulator(mem, regs, {'im': s.im, 'iff': s.iff1, 'tstates': s.tstates})
    sim.run(stop=0xA1F1, interrupts=True)                 # a render starts
    sim.run(stop=0x886F, interrupts=True)                 # it is ready
    shot = bytes(mem[0x4000:0x5B00])
    sim.run(stop=0xA1F1, interrupts=True)                 # copied and restored
    return mem, list(sim.registers), shot


for path in sys.argv[1:]:
    a, ra, sa = run(path, False)
    b, rb, sb = run(path, True)
    diff = [x for x in range(0x5B00, 0x10000) if a[x] != b[x] and x not in (0x87BE, 0x87BF)]
    lo, hi = (min(diff), max(diff)) if diff else (0, 0)
    print('%s: RAM differences %d (0x%04X-0x%04X), registers differing %s, screen bytes differing %d' % (
        os.path.basename(path), len(diff), lo, hi, [i for i in range(24) if ra[i] != rb[i]],
        sum(x != y for x, y in zip(sa, sb))))
    groups = []
    for x in diff:
        if groups and x - groups[-1][1] <= 2:
            groups[-1][1] = x
        else:
            groups.append([x, x])
    print('   ', ' '.join('%04X-%04X' % tuple(g) for g in groups), '| SP', '%04X' % ra[12])
