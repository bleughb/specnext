"""Hook cost profile: equivalent 3.5 MHz T per code region for 8F7C / 959B / 96A1 hooks (model)."""
import sys, pickle
from collections import Counter, defaultdict
sys.path.insert(0, '.')
import nexclash.inferno as I
from nexclash.dizzy6 import _rw_simulator
from nexclash import z80n, simpool
from skoolkit.simulator import Simulator
CACHE = 'C:/Users/micro/AppData/Local/Temp/claude/6237a019316583e8/40a53b24-c723-4977-82ff-466707bedd45/scratchpad/cwst.'
patch = I.CopierWindowPatch(work=True)
sy = patch.syms
inv = sorted((v, k) for k, v in sy.items())


def region(pc, page):
    if page == I.CW_PAGE:
        names = [k for v, k in inv if v <= pc and k.startswith('cw_')]
        return 'p80:' + (names[-1] if names else '?')
    if pc < 0x4000:
        names = [k for v, k in inv if v <= pc and v >= 0x3900 and not k.startswith(('wk_', 'cw_w'))]
        return 'rom:' + (names[-1] if names else hex(pc))
    return 'game'


tot = defaultdict(Counter)
n = Counter()
for lv in '146':
    d = pickle.loads(open(CACHE + lv, 'rb').read())[0x8F7C]
    for k in range(0, len(d), 60):
        ram, regs, port = d[k]
        # original to each hook site, take states
        o = simpool.machine(Simulator, bytearray(ram), regs, 'p.o', copy=True)
        states = []
        while o.registers[24] != 0x8F92 and len(states) < 6:
            pc = o.registers[24]
            if pc in (0x8F7C, 0x959B, 0x96A1):
                states.append((bytes(o.memory), list(o.registers)))
            o.opcodes[o.memory[pc]]()
        for m, r0 in states:
            site = r0[24]
            mem = I.CaptureMemory(patch.apply_memory(list(m)), bytearray(8192), patch, 1, True, (k * 7) % 32, k & 255)
            if site != 0x8F7C:
                mem.pages[I.STATE_PAGE][0x3F6] = 1
                mem.pages[I.STATE_PAGE][0x3F2:0x3F4] = (0x0900).to_bytes(2, 'little')
            sim = simpool.machine(_rw_simulator(), mem, r0, 'p.p')
            sim.set_tracer(mem)
            r = sim.registers
            z80n.install(sim, mem.nextreg)
            stop = patch.stops[site]
            el = 0.0
            while r[24] != stop:
                pc, page = r[24], mem.mmu0
                op = mem[pc]
                before, speed, reads = r[25], mem.speed, mem.fast_reads
                mem.wall = el
                sim.opcodes[op]()
                c = I._cost(r, before, speed, reads, mem)
                el += c
                key = 'speed switch' if (op == 0xED and mem.speed != speed) else region(pc, page)
                tot[site][key] += c
            n[site] += 1
for site in tot:
    print(hex(site), 'n', n[site], 'mean T %.0f' % (sum(tot[site].values()) / n[site]))
    for k, v in tot[site].most_common(12):
        print('   %-22s %7.1f' % (k, v / n[site]))
