# The pre-copy restore (e_pre) must leave game memory as the original: from a state at 0x886F (render
# ready, copy next), run the original to 0xA1F1 (copied and restored), and again with the game's
# restore 0x88BA called first (AF kept, as e_pre does); compare all RAM except the screen and the
# stack bytes below SP (the call's return address). Usage: python check_prerestore.py SNAP.z80 ...
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
from skoolkit.snapshot import Snapshot
from skoolkit.simulator import Simulator


def at_copy(path):
    s = Snapshot.get(path)
    mem = [0] * 16384 + list(s.ram(-1))
    regs = {'A': s.a, 'F': s.f, 'BC': s.bc, 'DE': s.de, 'HL': s.hl, 'IX': s.ix, 'IY': s.iy, 'SP': s.sp,
            'PC': s.pc, 'I': s.i, 'R': s.r, '^AF': s.a2 * 256 + s.f2, '^BC': s.bc2, '^DE': s.de2, '^HL': s.hl2}
    sim = Simulator(mem, regs, {'im': s.im, 'iff': s.iff1, 'tstates': s.tstates})
    sim.run(stop=0x886F, interrupts=True)
    return mem, list(sim.registers)


def finish(mem, regs, pre):
    mem = list(mem)
    sim = Simulator(mem, None)
    r = sim.registers
    r[:] = regs
    if pre and mem[0xE60B] != 34:
        a, f = r[0], r[1]
        sp = (r[12] - 2) & 0xFFFF
        mem[sp], mem[sp + 1] = 0x6F, 0x88           # return to 0x886F
        r[12], r[24] = sp, 0x88BA
        sim.run(stop=0x886F)
        r[0], r[1] = a, f
    sim.run(stop=0xA1F1, interrupts=True)
    return mem, list(r)


for path in sys.argv[1:]:
    mem, regs = at_copy(path)
    a, ra = finish(mem, regs, False)
    b, rb = finish(mem, regs, True)
    sp = regs[12]
    diff = [x for x in range(0x5B00, 0x10000) if a[x] != b[x] and not sp - 64 <= x < sp]
    print('%s: mode %d, RAM differences outside screen/stack %d %s, registers differing (index) %s, screen bytes differ %d' % (
        os.path.basename(path), mem[0xE60B], len(diff), [hex(x) for x in diff[:5]], [i for i in range(24) if ra[i] != rb[i]],
        sum(a[x] != b[x] for x in range(0x4000, 0x5B00))))
