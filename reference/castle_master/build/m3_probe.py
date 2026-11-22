"""M3 design probe: what runs inside the block 0x855E -> 0x859F that a 28 MHz block would change?
Port 0xFE writes outside the interrupt handler (sound), calls of the beeper routines, R reads, interrupts-off spans.
Usage: python m3_probe.py [every N-th]
"""
import collections, sys
from m0_lib import states
from m2_lib import Next, PC, T, SP, FRAME, IFF

END = 0x859F


def main():
    every = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    outs, calls, di, rreads = collections.Counter(), collections.Counter(), [], collections.Counter()
    n = 0
    for k, (frame, regs, ram) in enumerate(states('m0_states.bin')):
        if k % every:
            continue
        nx = Next(ram, 'cm2', sites=False)
        R = nx.R
        for i in range(24):
            R[i] = regs[i]
        R[PC], R[T], R[IFF] = 34142, 0, 1
        m = nx.mem
        orig = nx.write_port

        def wp(regs_, port, value, *x, nx=nx, R=R, m=m):
            if port & 1 == 0 and not m[29518] & 0x80:
                outs[R[PC]] += 1
            orig(regs_, port, value, *x)
        nx.write_port = wp
        nx.sim.set_tracer(nx)
        watch = {0xC821: lambda n_: calls.__setitem__(0xC821, calls[0xC821] + 1),
                 0xB374: lambda n_: calls.__setitem__(0xB374, calls[0xB374] + 1)}
        # step by hand to see IFF spans and LD A,R
        ops = nx.sim.opcodes
        t_di = None
        steps = 0
        while R[PC] != END and steps < 20_000_000:
            pc = R[PC]
            if m[pc] == 0xED and m[pc + 1] == 0x5F and not m[29518] & 0x80:
                rreads[pc] += 1
            if pc in watch:
                watch[pc](nx)
            inisr = m[29518] & 0x80
            if not R[IFF] and not inisr and t_di is None:
                t_di = (R[T], pc)
            elif (R[IFF] or inisr) and t_di is not None:
                di.append((R[T] - t_di[0], t_di[1]))
                t_di = None
            nx.run(None, max_ins=0) if False else None
            # one instruction through the model's run loop
            stop = None
            t0 = R[T]
            ops[m[pc]]()
            steps += 1
            dt = (R[T] - t0) * 8
            nx.acc += dt
            if nx.pending is None and nx.acc >= FRAME:
                nx.acc -= FRAME
                nx.pending = 256
                dt = 0
            if nx.pending is not None:
                nx.pending -= dt
                if R[IFF] and m[pc] != 0xFB:
                    nx.pending = None
                    nx.irqs += 1
                    R[IFF] = 0
                    sp = (R[SP] - 2) & 0xFFFF
                    m[sp], m[sp + 1] = R[PC] & 255, R[PC] >> 8
                    R[SP] = sp
                    R[PC] = m[0xFEFF] | m[0xFF00] << 8
                    R[T] += 19
                elif nx.pending <= 0:
                    nx.pending = None
                    nx.lost += 1
        n += 1
    print('blocks', n)
    print('port 0xFE writes outside the handler, by PC after:', {hex(a): c for a, c in outs.most_common(8)})
    print('calls', {hex(a): c for a, c in calls.items()})
    print('LD A,R outside the handler:', {hex(a): c for a, c in rreads.items()})
    di.sort(reverse=True)
    by = collections.Counter()
    for t, pc in di:
        by[pc] += 1
    print('interrupts-off spans outside the handler: n %d, longest (T at 3.5 MHz, start PC): %s' % (len(di), [(t, hex(p)) for t, p in di[:8]]))
    print('  by start PC:', {hex(a): c for a, c in by.most_common(8)})


if __name__ == '__main__':
    sys.exit(main())
