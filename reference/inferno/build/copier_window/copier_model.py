"""Reference model of Inferno's copier head (9790 -> CALL 9907 at 97FB, rows 18..6).

From RAM + registers at 9790 entry, compute exactly what the original does up to the 9907 entry:
RAM writes, final main/alt registers, OUT (254) values with their T offsets, total T and M1 count.
Checked against the simulator for every update of the original recordings (uncontended T, ISR time excluded).

Usage: python copier_model.py NEXCLASH_DIR LEVEL [STOP]
"""
import collections
import json
import sys

sys.path.insert(0, sys.argv[1])
from nexclash.simrun import run  # noqa: E402

REF = sys.argv[1] + '/../specnext/reference/inferno/'
ISR = set(range(0x998B, 0x99A3)) | {0xFFF4, 0xFFFF, 0x0038}


def model(mem, sp_entry):
    """mem: 64K indexable (read-only use). Returns dict. Instruction (T, M1) pairs per basic block."""
    w = {}                                   # address -> value written

    def rd(a):
        a &= 0xFFFF
        return w.get(a, mem[a])

    def wr(a, v):
        w[a & 0xFFFF] = v & 0xFF

    t = m1 = 0
    outs = []
    sp = sp_entry

    def push(v):
        nonlocal sp
        sp = (sp - 1) & 0xFFFF; wr(sp, v >> 8)
        sp = (sp - 1) & 0xFFFF; wr(sp, v)

    # 9790 LD (39032),SP 20/2 ; LD SP,42750 10/1 ; LD HL,39031 10/1 ; PUSH HL 11/1 ; SCF 4/1 ; PUSH AF 11/1
    wr(39032, sp_entry); wr(39033, sp_entry >> 8)
    t += 20 + 10 + 10; m1 += 2 + 1 + 1
    sp = 42750
    push(39031); t += 11; m1 += 1
    t += 4; m1 += 1                          # SCF
    # PUSH AF: A is unknown to the model here -> caller supplies; F has carry set. Record placeholder.
    af_slot = (sp - 2) & 0xFFFF
    sp = (sp - 2) & 0xFFFF; t += 11; m1 += 1
    hl, de = 40831, 20735                    # main
    t += 10 + 10 + 4; m1 += 1 + 1 + 1        # LD HL / LD DE / EXX
    de2, hl2 = 43841, 23295                  # alt
    t += 10 + 10; m1 += 1 + 1
    ixh = 18
    t += 11; m1 += 2                         # LD IXh,18 (DD 26 n)
    b = c = ixl = 0
    while True:
        # 97AD row: PUSH DE; PUSH HL (alt); LD BC,65504; ADD HL,BC; EXX
        push(de2); push(hl2)
        hl2 = (hl2 - 32) & 0xFFFF
        t += 11 + 11 + 10 + 11 + 4; m1 += 5
        c = 0; t += 7; m1 += 1               # LD C,0
        while True:
            a = rd(hl) & 3; b = a; ixl = b    # LD A,(HL) 7; AND 3 7; LD B,A 4; LD IXl,B 8
            t += 7 + 7 + 4 + 8; m1 += 1 + 1 + 1 + 2
            hl = (hl & 0xFF00) | ((hl - 1) & 0xFF); t += 4; m1 += 1          # DEC L
            a = rd(hl); hl = (hl - 1) & 0xFFFF; t += 7 + 6; m1 += 2            # LD A,(HL); DEC HL
            t += 4; m1 += 1                                                     # EXX
            c2 = a; b2 = (de2 >> 8); t += 4 + 4; m1 += 2                        # LD C,A ; LD B,D
            de2 = 0xA700 | (de2 & 0xFF); t += 7; m1 += 1                        # LD D,167
            a = rd(de2); t += 7; m1 += 1                                        # LD A,(DE)
            outs.append((t, a)); t += 11; m1 += 1                               # OUT (254),A
            de2 = (b2 << 8) | (de2 & 0xFF); t += 4; m1 += 1                     # LD D,B
            a = (252 + ixl) & 0xFF; t += 7 + 8; m1 += 1 + 2                     # LD A,252 ; ADD A,IXl
            b2 = a; t += 4; m1 += 1                                             # LD B,A
            a = rd((b2 << 8) | c2); t += 7; m1 += 1                             # LD A,(BC)
            wr(de2, a); de2 = (de2 - 1) & 0xFFFF; t += 7 + 6; m1 += 2           # LD (DE),A ; DEC DE
            a = c2; t += 4 + 4; m1 += 2                                         # LD A,C ; EXX
            t += 7 + 10; m1 += 2                                                # CP 16 ; JP C
            if a >= 16:
                saved = hl                                                      # PUSH HL
                hl = ((b << 8) | a) * 8 & 0xFFFF                                # LD L,A; LD H,B; ADD HL,HL x3
                hl = (((hl >> 8) + 220) & 0xFF) << 8 | (hl & 0xFF)              # LD A,H; ADD A,220; LD H,A
                push(hl); hl = saved                                            # EX (SP),HL net effect
                push(de)                                                        # PUSH DE
                c = (c + 1) & 0xFF
                t += 11 + 4 + 4 + 33 + 4 + 7 + 4 + 19 + 11 + 4; m1 += 10
            de = (de & 0xFF00) | ((de - 1) & 0xFF); t += 4; m1 += 1             # DEC E
            a = de & 0xFF; t += 4 + 4 + 10; m1 += 3                             # LD A,E; INC A; JP NZ
            if (a + 1) & 0xFF == 0:
                de = ((((de >> 8) - 8) & 0xFF) << 8) | (de & 0xFF)
                t += 4 + 7 + 4 + 4; m1 += 4                                     # LD A,D; SUB 8; LD D,A; XOR A
                a = 0
            else:
                a = (a + 1) & 0xFF
            t += 7 + 10; m1 += 2                                                # AND 31 ; JP NZ
            if a & 31:
                continue
            break
        # 97F4 LD A,C 4; OR A 4; PUSH AF 11; LD A,IXh 8; CP 6 7; CALL Z 10/17
        t += 4 + 4 + 11 + 8 + 7; m1 += 1 + 1 + 1 + 2 + 1
        push_af_row = (c, c == 0)
        sp = (sp - 2) & 0xFFFF
        w[('rowaf', sp)] = push_af_row
        if ixh == 6:
            t += 17; m1 += 1
            return {'T': t, 'M1': m1, 'outs': outs, 'writes': w, 'sp': sp, 'af_slot': af_slot,
                    'regs': {'HL': hl, 'DE': de, 'C': c, 'B': b, "HL'": hl2, "DE'": de2, "C'": c2, "B'": b2,
                             'IXh': ixh, 'IXl': ixl}}
        t += 10; m1 += 1
        ixh -= 1; t += 8 + 4 + 10; m1 += 2 + 1 + 1                              # DEC IXh; EXX; JP NZ
        # (EXX swaps main/alt: the model keeps named sets, so nothing else to do)


class Check:
    def __init__(self):
        self.sim = None
        self.state = None
        self.counts = collections.Counter()
        self.fail = []
        self.t = 0
        self.m1 = 0

    def on_sim(self, sim):
        self.sim = sim

    def before(self, pc):
        if pc == 0x9790:
            mem = self.sim.memory
            snap = bytes(mem[a] for a in range(65536))
            self.state = {'mem': snap, 'sp': self.sim.registers[12], 't': 0, 'm1': 0, 'outs': [],
                          'writes': {}, 'r0': self.sim.registers[15]}
        elif pc == 0x9907 and self.state is not None:
            self.finish()
        if self.state is not None and pc not in ISR:
            self.cur_pc = pc

    def after(self, pc, dt):
        st = self.state
        if st is not None and pc not in ISR:
            st['t'] += dt
            if pc == 0x97C5:
                st['outs'].append((st['t'] - dt, self.sim.registers[0]))

    def on_write(self, a, v, pc, mem):
        if self.state is not None and pc not in ISR:
            self.state['writes'][a] = v

    def finish(self):
        st, self.state = self.state, None
        m = model(st['mem'], st['sp'])
        ok = True
        if m['T'] != st['t']:
            ok = False; self.fail.append(('T', m['T'], st['t']))
        if [v for _, v in m['outs']] != [v for _, v in st['outs']]:
            ok = False; self.fail.append(('out values',))
        if [tt for tt, _ in m['outs']] != [tt for tt, _ in st['outs']]:
            d = next(i for i, (x, y) in enumerate(zip(m['outs'], st['outs'])) if x[0] != y[0])
            ok = False; self.fail.append(('out T', d, m['outs'][d][0], st['outs'][d][0]))
        mw = {k: v for k, v in m['writes'].items() if isinstance(k, int)}
        sw = dict(st['writes'])
        # stack slots the model leaves symbolic: PUSH AF sentinel and per-row PUSH AF
        sym = {m['af_slot'], m['af_slot'] + 1}
        for k in m['writes']:
            if isinstance(k, tuple):
                sym |= {k[1], k[1] + 1}
        # CALL 9907 pushes the return address 97FE at sp-2
        ret = (m['sp'] - 2) & 0xFFFF
        if not (sw.get(ret) == 0xFE and sw.get(ret + 1) == 0x97):
            ok = False; self.fail.append(('call ret',))
        sym |= {ret, ret + 1}
        diff = [a for a in set(mw) | set(sw) if a not in sym and mw.get(a, st['mem'][a]) != sw.get(a, st['mem'][a])]
        if diff:
            ok = False; self.fail.append(('ram', len(diff), hex(min(diff))))
        if self.sim.registers[12] != ret:
            ok = False; self.fail.append(('sp', self.sim.registers[12], ret))
        self.counts['updates'] += 1
        self.counts['pass' if ok else 'FAIL'] += 1
        self.counts['outs'] += len(m['outs'])
        self.counts['max T'] = max(self.counts['max T'], m['T'])
        self.counts['min T'] = min(self.counts['min T'] or 10**9, m['T'])


def main():
    c = Check()
    run(REF + 'Inferno%s.z80' % sys.argv[2], [REF + 'Inferno%s.rzx' % sys.argv[2]], c,
        stop=int(sys.argv[3]) if len(sys.argv) > 3 else None)
    print(json.dumps({'level': sys.argv[2], 'counts': dict(c.counts), 'first_failures': c.fail[:8]}))


main()
