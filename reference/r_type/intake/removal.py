"""R-Type: test replacing figure pixels by a separate layer at the original copier.

Compares the game's own 8842 routine on captured live states with/without figure
pixels in its source. Restore those source pixels before comparing game memory.
This is a feasibility experiment, NOT an assembled-hook or timing proof.
"""
import collections
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'nexclash'))
from nexclash.rzx import trace
from skoolkit.simulator import Simulator

results = []
next_frame = 1300


def source(cx, line):
    # Derived from 8EA2/8EC2 and the eight INC D stores, not a linear buffer.
    row, within = divmod(line, 8)
    return ((0x60 + 8 * (row // 8) + within) << 8) + 32 * (row % 8) + cx


def run(memory, registers):
    sim = Simulator(memory)
    sim.registers[:] = registers
    r = sim.registers
    sp = r[12]
    ret = memory[sp] | memory[(sp + 1) & 65535] << 8
    n = 0
    while r[24] != ret or r[12] != (sp + 2) & 65535:
        sim.opcodes[memory[r[24]]]()
        n += 1
        if n > 200000:
            raise RuntimeError('copy did not return')
    return sim


def at_copy(pc, live):
    global next_frame
    frame = live.tracer.frame_index
    if frame < next_frame:
        return
    next_frame = frame + 2500
    original = [live.memory[a] for a in range(65536)]
    modified = original[:]
    fg = [(x, y) for y in range(20) for x in range(32)
          if 0 < original[0x7E00 + 32 * y + x] < 0xDC]
    for x, y in fg:
        for line in range(8):
            modified[source(x, 8 * y + line)] = 0
        modified[0x7800 + 32 * y + x] &= 0xC7  # Paper becomes the black scenery plane.
    o = run(original[:], list(live.registers))
    p = run(modified, list(live.registers))
    # The wrapper would restore temporary source changes after the original copy.
    expected = list(o.memory)
    for x, y in fg:
        for line in range(8):
            a = source(x, 8 * y + line)
            p.memory[a] = original[a]
            expected[a - 0x2000] = 0
        a = 0x7800 + 32 * y + x
        p.memory[a] = original[a]
        expected[a - 0x2000] &= 0xC7
    cmp = list(range(25)) + [26, 27, 28]  # R and alternate registers included; T/MEMPTR aside.
    rd = [(i, o.registers[i], p.registers[i]) for i in cmp if o.registers[i] != p.registers[i]]
    md = [a for a in range(0x4000, 65536) if o.memory[a] != p.memory[a] and not 0x4000 <= a < 0x5B00]
    vd = [a for a in range(0x4000, 0x5B00) if expected[a] != p.memory[a]]
    results.append(dict(frame=frame, cells=len(fg), registers=rd[:8], ram=md[:8], display=vd[:8],
                        original_T=o.registers[25] - live.registers[25]))
    print(json.dumps(results[-1]), flush=True)
    if md or rd or vd:
        (HERE / 'removal-first-failure.json').write_text(json.dumps(dict(frame=frame, registers=list(live.registers), memory=original)))
        raise RuntimeError('removal model differs: inspect saved state')


frames, desync = trace(str(HERE.parent / 'Rtype.rzx'), [0x8842], at_copy)
(HERE / 'removal.json').write_text(json.dumps(dict(frames=frames, desync=desync, cases=results), indent=2) + '\n')
print('frames', frames, 'desync', desync, 'cases', len(results))
