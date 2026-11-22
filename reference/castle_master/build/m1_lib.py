"""Castle Master M1 harness: assemble cmr.asm (the pinned sjasmplus) and run its routines in SkoolKit's Python
simulator with the Z80N handlers (nexclash.z80n). Memory as on the Next while the renderer runs (cmr.asm header):
code 0x0000-0x3FFF, work RAM 0x4000-0x7FFF (stack at its top), Layer 2 window 0x8000-0x9FFF (MMU slot 4, NR 0x54:
the 8K pages are kept here, swapped in and out on each write), world snapshot 0xC000-0xFFFF.
"""
import os, subprocess, sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import z80n
from skoolkit.simulator import Simulator

W = r'C:/1NEXT/castle_master_work/'
SJ = os.path.expanduser(r'~/.cache/nexclash/sjasmplus-1.24.0/sjasmplus')
SENT, SP0 = 0x3FFE, 0x7FFE
REG = {'A': 0, 'F': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'H': 6, 'L': 7, 'IXh': 8, 'IXl': 9, 'IYh': 10, 'IYl': 11}
PAIR = {'BC': 2, 'DE': 4, 'HL': 6, 'IX': 8, 'IY': 10}


def assemble(name='cmr'):
    r = subprocess.run([SJ, '--nologo', '--zxnext', '--sym=%s.sym' % name, '%s.asm' % name], cwd=W,
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stdout + r.stderr)
    return r.stdout


def syms(name='cmr'):
    d = {}
    for line in open(W + name + '.sym'):
        if ':' in line and 'EQU' in line:
            k, v = line.split(':', 1)
            d[k.strip()] = int(v.split('EQU')[1].strip().replace('0x', ''), 16)
    return d


class Machine:
    def __init__(self, name='cmr', ram=None):
        self.S = syms(name)
        self.mem = [0] * 65536
        if ram is not None:
            self.mem[0xC000:] = list(ram[0xC000:])
        b = open(W + name + '.bin', 'rb').read()
        self.mem[0:len(b)] = list(b)
        self.sim = Simulator(self.mem, {})
        self.pages, self.slot4, self.nr = {}, None, []
        z80n.install(self.sim, nextreg=self._nextreg)
        self.R = self.sim.registers
        if ram is not None:
            self.load_tables(ram)

    def load_tables(self, ram):
        """what the renderer's init copies from the game: templates 27486-27819, sin / cos 29337"""
        t, s = self.S['tmpl'], self.S['sincos']
        self.mem[t:t + 334] = list(ram[27486:27820])
        self.mem[s:s + 146] = list(ram[29337:29483])
        if 'pano' in self.S:
            self.mem[self.S['pano']:self.S['pano'] + 288] = list(ram[30660:30948])
            self.mem[self.S['lgfx']:self.S['lgfx'] + 688] = list(ram[31085:31773])

    def _nextreg(self, reg, v):
        self.nr.append((reg, v))
        if reg != 0x54:
            raise RuntimeError('NEXTREG %02X not modelled' % reg)
        self.map4(v)

    def map4(self, page):
        """MMU slot 4 = page (the window's old page saved first)"""
        m = self.mem
        if self.slot4 is not None:
            self.pages[self.slot4] = m[0x8000:0xA000]
        self.slot4 = page
        m[0x8000:0xA000] = self.pages.get(page) or [0] * 8192

    def flush4(self):
        if self.slot4 is not None:
            self.pages[self.slot4] = self.mem[0x8000:0xA000]

    def call(self, entry, **regs):
        R, m = self.R, self.mem
        if isinstance(entry, str):
            entry = self.S[entry]
        for k, v in regs.items():
            if k in PAIR:
                R[PAIR[k]], R[PAIR[k] + 1] = v >> 8 & 255, v & 255
            else:
                R[REG[k]] = v & 255
        m[SP0], m[SP0 + 1] = SENT & 255, SENT >> 8
        R[12] = SP0
        R[25] = 0
        self.sim.run(entry, SENT)
        return R[25]

    def call_irq(self, entry, rng, rate=0.02, **regs):
        """as call(), stepped; at random instruction boundaries an interrupt's entry is imitated: the 2 bytes
        below SP get a return address (here junk) - all a handler that switches stacks first may write there"""
        R, m = self.R, self.mem
        if isinstance(entry, str):
            entry = self.S[entry]
        for k, v in regs.items():
            if k in PAIR:
                R[PAIR[k]], R[PAIR[k] + 1] = v >> 8 & 255, v & 255
            else:
                R[REG[k]] = v & 255
        m[SP0], m[SP0 + 1] = SENT & 255, SENT >> 8
        R[12] = SP0
        R[24] = entry
        ops = self.sim.opcodes
        hits = 0
        while R[24] != SENT:
            ops[m[R[24]]]()
            if rng.random() < rate:
                sp = R[12]
                if sp >= 0x4002:
                    m[sp - 1], m[sp - 2] = rng.randrange(256), rng.randrange(256)
                    hits += 0x8000 <= sp < 0xA000
        return hits

    def pair(self, k):
        return self.R[PAIR[k]] << 8 | self.R[PAIR[k] + 1]

    def w(self, a, v):
        if isinstance(a, str):
            a = self.S[a]
        self.mem[a], self.mem[a + 1] = v & 255, v >> 8 & 255

    def rw(self, a, signed=True):
        if isinstance(a, str):
            a = self.S[a]
        v = self.mem[a] | self.mem[a + 1] << 8
        return v - 65536 if signed and v & 0x8000 else v

    def b(self, a, v=None):
        if isinstance(a, str):
            a = self.S[a]
        if v is None:
            return self.mem[a]
        self.mem[a] = v & 255
