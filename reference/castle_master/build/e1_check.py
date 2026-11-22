"""Castle Master E1 step 2: the Z80N maths routines (e1_maths.bin, from e1_maths.asm) against the originals.

For every unique register input recorded by e1_capture.py (all 167,135 frames), run the original routine and the
new one in the simulator from that input and compare: all 16 main + alternate registers (F counted apart: no call
site reads it), SP, IX, IY, and memory outside the stack. The original's result must also equal the recording's
(the harness reproduces the real run). Then sweeps beyond the recording: edge values x random other registers,
random inputs, and 0xA348 exhaustively. T-states are the simulator's (Z80 timing, MUL D,E = 8).
Usage: python -I e1_check.py [--calls e1_calls.json] [--random N] [--bin MUTANT.bin] [--no-exhaustive]
"""
import argparse, collections, json, random, sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import z80n
from skoolkit.simulator import Simulator
from skoolkit.snapshot import get_snapshot

W = r'C:/1NEXT/castle_master_work/'
REGS = list(range(8)) + list(range(16, 24))
NEW = {}                                    # filled from the bin's .sym (sjasmplus --sym)
SYM = {0xA1FD: 'mul8x16', 0xA253: 'mul16x16', 0xA2C1: 'div24', 0xA348: 'mul8x8'}
NAME = {0xA1FD: 'A*HL', 0xA253: 'HL*DE', 0xA2C1: 'AHL/DE', 0xA348: 'H*L'}
SENT, SP0, STACK = 0x3FFE, 0x8400, range(0x8300, 0x8400)    # 0x82C0-0x8400 never touched by the game


class Box:
    def __init__(self, binf):
        self.mem = list(get_snapshot(W + 'castle_master.z80'))
        b = open(binf, 'rb').read()
        sym = {}
        for line in open(binf[:-4] + '.sym'):
            if ':' in line and 'EQU' in line:
                k, v = line.split(':', 1)
                sym[k.strip()] = int(v.split('EQU')[1].strip().replace('0x', ''), 16)
        NEW.update({rt: sym[n] for rt, n in SYM.items()})
        self.mem[0x2000:0x2000 + len(b)] = list(b)
        self.base = self.mem[:]
        self.sim = Simulator(self.mem, {})
        z80n.install(self.sim)

    def run(self, entry, rin, memcheck=False):
        R, mem = self.sim.registers, self.mem
        for i, v in zip(REGS, rin):
            R[i] = v
        R[8], R[9], R[10], R[11] = 0x12, 0x34, 0x5C, 0x3A
        R[12] = SP0 - 2
        mem[SP0 - 2], mem[SP0 - 1] = SENT & 255, SENT >> 8
        R[24], R[25] = entry, 0
        ops = self.sim.opcodes
        n = 0
        while R[24] != SENT:
            ops[mem[R[24]]]()
            n += 1
            if n > 100000:
                raise RuntimeError('runaway at %04X' % entry)
        out = tuple(R[i] for i in REGS)
        bad = None
        if memcheck:
            if mem[0x4000:0x8300] != self.base[0x4000:0x8300] or mem[0x8400:] != self.base[0x8400:]:
                bad = [a for a in range(0x4000, 0x10000) if a not in STACK and mem[a] != self.base[a]][:5]
                for a in bad:
                    mem[a] = self.base[a]
        return out, (R[12], R[8], R[9], R[10], R[11]), R[25], bad


def diff(o, n):
    """register indices (into REGS) that differ, F (index 1) kept apart."""
    d = [REGS[i] for i in range(16) if o[i] != n[i]]
    return [x for x in d if x != 1], 1 in d


class Tally:
    def __init__(self):
        self.cases = collections.Counter()
        self.fail = collections.Counter()
        self.fdiff = collections.Counter()
        self.ex = collections.defaultdict(list)
        self.t = collections.defaultdict(lambda: [0, 0, 0])     # weighted T orig, T new, calls

    def compare(self, box, rt, rin, kind, weight=0, memcheck=False, want=None):
        o, os_, to, bo = box.run(rt, rin, memcheck)
        n, ns, tn, bn = box.run(NEW[rt], rin, memcheck)
        k = (rt, kind)
        self.cases[k] += 1
        d, fd = diff(o, n)
        errs = []
        if d:
            errs.append('regs %s' % d)
        if os_ != ns:
            errs.append('SP/IX/IY %s %s' % (os_, ns))
        if bo or bn:
            errs.append('memory orig %s new %s' % (bo, bn))
        if want is not None and tuple(want) != o:
            errs.append('original != recording: %s' % (diff(tuple(want), o),))
        if errs:
            self.fail[k] += 1
            if len(self.ex[k]) < 4:
                self.ex[k].append((list(rin[:8]), errs))
        if fd:
            self.fdiff[k] += 1
        if weight:
            t = self.t[rt]
            t[0] += to * weight
            t[1] += tn * weight
            t[2] += weight


def s8(v):
    return v & 255


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--calls', default=W + 'e1_calls.json')
    ap.add_argument('--random', type=int, default=100000)
    ap.add_argument('--bin', default=W + 'e1_maths.bin', help='a mutant for the negative controls')
    ap.add_argument('--no-exhaustive', action='store_true')
    a = ap.parse_args()
    box, tl = Box(a.bin), Tally()
    calls = json.load(open(a.calls))
    print('recording: frames <= %s, capture odd %s' % (calls['stop'], calls['odd']))
    for rt in SYM:
        c = calls['%04X' % rt]
        print('%04X %-6s calls %d unique inputs %d sites %d' % (rt, NAME[rt], c['calls'], c['unique'], len(c['sites'])))
        for rin, cnt, rout in c['cases']:
            tl.compare(box, rt, rin, 'recorded', weight=cnt, memcheck=True, want=rout)
    rnd = random.Random(1986)
    edge8 = [0, 1, 2, 0x7F, 0x80, 0x81, 0xFE, 0xFF, 0x40, 0xC0]
    edge16 = [0, 1, 2, 0xFF, 0x100, 0x7FFF, 0x8000, 0x8001, 0xFFFF, 0xFFFE, 0xFF00, 0x00FF, 0x4000, 0xC000]
    edge24 = [0, 1, 0x7FFFFF, 0x800000, 0x800001, 0xFFFFFF, 0xFF0000, 0x00FFFF, 0x0000FF, 0x010000, 0x000100,
              0x8000, 0xFF8000]

    def regs(**kv):
        r = [rnd.randrange(256) for _ in range(16)]
        for k, v in kv.items():
            r['AFBCDEHL'.index(k)] = v
        return r

    for x in edge8:
        for y in edge16:
            tl.compare(box, 0xA1FD, regs(A=x, H=y >> 8, L=y & 255), 'edge')
    for x in edge16:
        for y in edge16:
            tl.compare(box, 0xA253, regs(H=x >> 8, L=x & 255, D=y >> 8, E=y & 255), 'edge')
    for x in edge24:
        for y in edge16:
            tl.compare(box, 0xA2C1, regs(A=x >> 16, H=x >> 8 & 255, L=x & 255, D=y >> 8, E=y & 255), 'edge')
    for _ in range(a.random):
        tl.compare(box, 0xA1FD, regs(), 'random')
        tl.compare(box, 0xA253, regs(), 'random')
        r = regs()
        if rnd.random() < 0.5:                    # half with small divisors, as the game's are
            r[4], r[5] = rnd.choice((0, 255)), rnd.randrange(256)
        tl.compare(box, 0xA2C1, r, 'random')
    for h in ([] if a.no_exhaustive else range(256)):
        for l in range(256):
            tl.compare(box, 0xA348, regs(H=h, L=l), 'exhaustive')
    ok = True
    print('\nroutine kind        cases     fail  F-differs')
    for k in sorted(tl.cases):
        print('%04X %-6s %-10s %8d %8d %8d' % (k[0], NAME[k[0]], k[1], tl.cases[k], tl.fail[k], tl.fdiff[k]))
        ok = ok and not tl.fail[k]
        for e in tl.ex[k]:
            print('     ', e)
    print('\nT per call over the recording (3.5 MHz T, call-weighted): original -> Z80N version')
    tot_o = tot_n = 0
    for rt in NEW:
        to, tn, n = tl.t[rt]
        tot_o, tot_n = tot_o + to, tot_n + tn
        print('%04X %-6s %8d calls  %6.1f -> %6.1f  (x%.2f)' % (rt, NAME[rt], n, to / n, tn / n, to / tn))
    print('all four: %d -> %d T (x%.2f)' % (tot_o, tot_n, tot_o / tot_n))
    print('E1', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
