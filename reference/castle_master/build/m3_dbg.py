import sys
from m0_lib import states
from m2_lib import Next, syms, PC, T, SP, FRAME, VP
S = syms('cm3')
want = int(sys.argv[1])
for k, (frame, regs, ram) in enumerate(states('m0_states.bin')):
    if k != want:
        continue
    out = {}
    for name, sites in (('orig', False), ('m3', True)):
        nx = Next(ram, 'cm3', S, sites=sites, period=FRAME)
        nx.acc = int(sys.argv[2]) if len(sys.argv) > 2 else 12345
        for i in range(24):
            nx.R[i] = regs[i]
        nx.R[PC], nx.R[T], nx.R[26] = 34142, 0, 1
        log = []
        def mark(tag):
            def f(n):
                g = n.mem
                log.append((tag, round(n.clock / FRAME, 2), g[VP + 2] | g[VP + 3] << 8, g[VP + 14] | g[VP + 15] << 8))
            return f
        w = {0x8599: mark('rast'), 0x859C: mark('show site'), 0xC68B: mark('snd'), 0x9F6E: mark('lightning'), 0x9F92: mark('lw1 done'), 0x9FA3: mark('lw2 done'), 0x9F19: mark('9F19'), 0xB347: mark('B347'), 0xB63D: mark('B63D')}
        if sites:
            w.update({S['m3_show']: mark('m3_show'), S['waittgt']: mark('wait'), S['flip']: mark('flip'), S['m3_end']: mark('end')})
        nx.run(0x859F, w, max_ins=60_000_000)
        wk = nx.page(S['PG_W0']) + nx.page(S['PG_W1'])
        rd = lambda n: wk[S[n] - 0x4000] | wk[S[n] - 0x4000 + 1] << 8
        print(name, 'end', round(nx.clock / FRAME, 2), 'irqs', nx.irqs, 'lost', nx.lost, 'fast', rd('t_fast'), 'tgt', rd('t_tgt'), 'fin', rd('t_fin'), 'ni', nx.mem[VP + 26], 'h0', rd('t_h0'))
        for l in log[:24]:
            print('   ', l)
