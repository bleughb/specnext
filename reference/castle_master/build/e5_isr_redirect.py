"""Castle Master E5: ISR redirect while a sandbox copy of RAM is mapped (games/castle_master.md, Feasibility E5).

For every interrupt the RZX takes inside a redraw window (0x9776 .. 0x859F) - where on hardware the sandbox
renderer would be running - build two worlds in a Next MMU model:
  real    = 48K RAM just before that interrupt (pages 10, 11, 4, 5, 0, 1 in slots 2-7)
  sandbox = RAM at the start of that redraw (pages 32-37), camera moved and every ISR counter altered, its
            0xFDFD JP patched to the stub; the stub's saved SP / stack in 0x82C0-0x8400 (never touched by the game
            in all 167,135 frames)
deliver the interrupt in the sandbox world (IM 2, I=0xFE), run the stub (slot 1) to the return, and check:
  C1 real pages = the recording's own memory after its handler (dead stack below the interrupted SP excluded;
     differences in the ISR's R-driven blink delays 49173-49176 counted apart: cosmetic, R differs by the stub)
  C2 sandbox pages unchanged except the 2-byte return address and the stub's stack
  C3 every register back (R and T excepted), IFF 1, MMU back to the sandbox pages
Negative controls (each must fail): --neg noremap | noslot7 | nosp.
Usage: python e5_isr_redirect.py [--stop N] [--neg X] [--max K]
"""
import argparse, collections, sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import simrun, z80n
from skoolkit.simulator import Simulator

RZX = r'C:/dev/castlemaster/castle.rzx'
STUB = 0x2000
SV_SP, STK = 0x82C0, 0x8400
REAL = (10, 11, 4, 5, 0, 1)                         # slots 2-7, 48K layout on the Next
SAND = (32, 33, 34, 35, 36, 37)                     # the sandbox copy, slots 2-7
ISR_VARS = (29559, 27407, 27408, 27411, 49182, 49177, 49178, 49179, 49180, 29514, 29515, 27419, 29518,
            27353, 49173, 49174, 49175, 49176)
CAMERA = (27309, 27310, 27311, 27313, 27314, 27318, 27319)
BLINK = range(49173, 49177)


def stub_bytes(neg):
    b = [0xED, 0x73, SV_SP & 255, SV_SP >> 8,          # LD (SV_SP),SP
         0x31, STK & 255, STK >> 8]                    # LD SP,STK
    slots = [(0x52, REAL[0]), (0x53, REAL[1]), (0x56, REAL[4]), (0x57, REAL[5])]
    back = [(0x52, SAND[0]), (0x53, SAND[1]), (0x56, SAND[4]), (0x57, SAND[5])]
    if neg == 'noremap':
        slots, back = [], []
    elif neg and neg.startswith('noslot'):              # noslot2 / 3 / 6 / 7: that slot left on the sandbox
        k = {'2': 0, '3': 1, '6': 2, '7': 3}[neg[-1]]
        del slots[k], back[k]
    for r, v in slots:
        b += [0xED, 0x91, r, v]                        # NEXTREG r,v
    b += [0xCD, 0x1F, 0xC0]                            # CALL 0xC01F (the game's handler; its RETI returns here)
    b += [0xF3]                                        # DI
    for r, v in back:
        b += [0xED, 0x91, r, v]
    if neg != 'nosp':
        b += [0xED, 0x7B, SV_SP & 255, SV_SP >> 8]     # LD SP,(SV_SP)
    b += [0xFB, 0xC9]                                  # EI / RET
    return b


class Paged:
    """64K view through 8 MMU slots onto 8K pages; writes below 0x4000 dropped by SkoolKit itself."""

    def __init__(self, pages, mmu):
        self.p, self.mmu = pages, mmu

    def __len__(self):
        return 65536

    def __getitem__(self, a):
        return self.p[self.mmu[a >> 13]][a & 0x1FFF]

    def __setitem__(self, a, v):
        self.p[self.mmu[a >> 13]][a & 0x1FFF] = v


def world(mem_real, mem_sand, rom, neg):
    pages = {'rom0': bytearray(rom[:8192]), 'stub': bytearray(rom[8192:16384])}
    sb = stub_bytes(neg)
    pages['stub'][:len(sb)] = bytes(sb)
    for k, pg in enumerate(REAL):
        pages[pg] = bytearray(mem_real[0x4000 + k * 8192:0x6000 + k * 8192])
    for k, pg in enumerate(SAND):
        pages[pg] = bytearray(mem_sand[0x4000 + k * 8192:0x6000 + k * 8192])
    mmu = ['rom0', 'stub'] + list(SAND)
    return pages, mmu


def run_case(case, rom, neg):
    regs, mem_real, mem_sand, mem_after = case['regs'], case['before'], case['sand'], case['after']
    sand = bytearray(mem_sand)
    for a in CAMERA:
        sand[a] ^= 0x21
    for a in ISR_VARS:
        sand[a] ^= 0x5A
    sand[0xFDFD:0xFE00] = bytes([0xC3, STUB & 255, STUB >> 8])
    pages, mmu = world(mem_real, sand, rom, neg)
    sand0 = {pg: bytes(pages[pg]) for pg in SAND}
    mem = Paged(pages, mmu)
    sim = Simulator(mem, {})
    R = sim.registers
    for i in range(len(R)):
        R[i] = regs[i]

    def nextreg(reg, v):
        if 0x50 <= reg <= 0x57:
            mmu[reg - 0x50] = v
    z80n.install(sim, nextreg)
    pc0, sp0 = R[24], R[12]
    if not sim.accept_interrupt(R, mem, case['prev_pc']):
        return 'skip', []
    t0, stub_t, n = R[25], 0, 0
    ops = sim.opcodes
    while n < 3000000:
        pc = R[24]
        t = R[25]
        ops[mem[pc]]()
        if pc >> 13 == 1:
            stub_t += R[25] - t
        n += 1
        if R[24] == pc0 and R[12] == sp0 and pc >> 13 == 1:
            break
    else:
        return 'FAIL', ['runaway: no return to %04X' % pc0]
    errs = []
    # C3 registers / MMU
    for i in range(len(regs)):
        if i in (15, 25):                              # R, T
            continue
        if R[i] != regs[i]:
            errs.append('C3 register %d: %d != %d' % (i, R[i], regs[i]))
    if mmu[2:] != list(SAND):
        errs.append('C3 MMU not back: %s' % mmu[2:])
    # C1 real pages vs the recording's handler result
    dead = set(range((sp0 - 32) & 0xFFFF, sp0))
    blink, bad = 0, []
    for k, pg in enumerate(REAL):
        base = 0x4000 + k * 8192
        got, want = pages[pg], mem_after[base:base + 8192]
        if got != want:
            for i in range(8192):
                a = base + i
                if got[i] != want[i] and a not in dead:
                    if a in BLINK:
                        blink += 1
                    else:
                        bad.append(a)
    if bad:
        errs.append('C1 real RAM differs at %d byte(s): %s' % (len(bad), ' '.join('%04X' % a for a in bad[:10])))
    # C2 sandbox pages unchanged except the return address and the stub stack
    allowed = {(sp0 - 2) & 0xFFFF, (sp0 - 1) & 0xFFFF} | set(range(SV_SP, STK))
    for k, pg in enumerate(SAND):
        base = 0x4000 + k * 8192
        if pages[pg] != sand0[pg]:
            diff = [base + i for i in range(8192) if pages[pg][i] != sand0[pg][i] and base + i not in allowed]
            if diff:
                errs.append('C2 sandbox changed at %d byte(s): %s' % (len(diff), ' '.join('%04X' % a for a in diff[:10])))
    return ('FAIL' if errs else 'PASS'), errs, stub_t, R[25] - t0, blink


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stop', type=int, default=3000)
    ap.add_argument('--neg', default=None)
    ap.add_argument('--max', type=int, default=0, help='stop after K cases (0 = all)')
    a = ap.parse_args()
    from skoolkit.snapshot import get_snapshot
    rom = bytes(get_snapshot(r'C:/1NEXT/castle_master_work/castle_master.z80')[:16384])
    st = {'render': False, 'isr': False, 'cand': None, 'case': None, 'base': None, 'sim': None}
    res = collections.Counter()
    first_err = []
    stats = {'stub_t': [], 'blink': 0}

    def snap():
        m = st['sim'].memory
        return bytes(m[0:65536]) if isinstance(m, list) else bytes(m[i] for i in range(65536))

    class H:
        def on_sim(self, sim):
            st['sim'] = sim

        def on_interrupt(self, sim, prev_pc):
            if st['render'] and not st['isr']:
                st['cand'] = {'regs': list(sim.registers), 'prev_pc': prev_pc, 'before': snap(),
                              'sand': st['base']}

        def before(self, pc):
            if pc == 0x9776 and not st['isr'] and not st['render']:
                st['render'] = True
                st['base'] = snap()
            elif pc == 0x859F:
                st['render'] = False
            if pc == 0xFDFD and st['cand'] is not None:
                st['isr'], st['case'], st['cand'] = True, st['cand'], None
            elif pc == 0xC161 and st['isr']:
                st['isr'] = False
                case = st['case']
                st['case'] = None
                if case is None or (a.max and sum(res.values()) >= a.max):
                    return
                case['after'] = snap()
                r = run_case(case, rom, a.neg)
                res[r[0]] += 1
                if r[0] == 'PASS':
                    stats['stub_t'].append(r[2])
                    stats['blink'] += r[4]
                elif len(first_err) < 5:
                    first_err.append(r[1])

    simrun.play_rzx(RZX, H(), stop=a.stop)
    print('E5 neg=%s frames<=%d cases %s' % (a.neg, a.stop, dict(res)))
    if stats['stub_t']:
        s = sorted(stats['stub_t'])
        print('stub T (own instructions, 3.5 MHz T): min %d median %d max %d; blink-delay bytes differing: %d'
              % (s[0], s[len(s) // 2], s[-1], stats['blink']))
    for e in first_err:
        print('  ', e[:4])
    return 0 if (a.neg is None) == (res['FAIL'] == 0 and res['PASS'] > 0) else 1


if __name__ == '__main__':
    sys.exit(main())
