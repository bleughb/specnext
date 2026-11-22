"""Trace the pace clock's readings in one redraw: who ticked, the video line, elapsed and held lines.
Usage: python m3_trace.py STATE PHASE [from-frame] [to-frame]"""
import sys
from m0_lib import states
from m2_lib import Next, syms, PC, T, SP, FRAME, VP
S = syms('cm3')
want, phase = int(sys.argv[1]), int(sys.argv[2])
f0 = float(sys.argv[3]) if len(sys.argv) > 3 else 0
f1 = float(sys.argv[4]) if len(sys.argv) > 4 else 1e9
for k, (frame, regs, ram) in enumerate(states('m0_states.bin')):
    if k != want:
        continue
    nx = Next(ram, 'cm3', S, sites=True, period=FRAME)
    nx.acc = phase
    for i in range(24):
        nx.R[i] = regs[i]
    nx.R[PC], nx.R[T], nx.R[26] = 34142, 0, 1
    def mark(tag):
        def f(n):
            fr = n.clock / FRAME
            if f0 <= fr <= f1:
                g = n.mem
                line = (n.acc * 312 // FRAME + 248) % 312
                print('%-10s %7.3f line %3d  el %5d held %5d last %3d  ml %d busy %d wait %d ni %d iff %d' % (
                    tag, fr, line, g[VP + 2] | g[VP + 3] << 8, g[VP + 14] | g[VP + 15] << 8, g[VP] | g[VP + 1] << 8,
                    g[VP + 29], g[VP + 27], g[VP + 30], g[VP + 26], n.R[26]))
        return f
    w = {0xC01F: mark('handler'), 0x859C: mark('show site'), 0xC68B: mark('snd in'), 0xB347: mark('B347'), 0xCA4E: mark('printer')}
    for nm in ('isr_tick', 'ptick', 'wait_in', 'wait_out', 'h_snd_out', 'isr_pre', 'isr_post', 'h_w77', 'h_w4a', 'm3_show'):
        w[S[nm]] = mark(nm)
    nx.run(0x859F, w, max_ins=60_000_000)
