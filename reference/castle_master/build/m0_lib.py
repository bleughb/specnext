"""Castle Master M0 shared helpers: redraw states (m0_capture.py) and an offline sandbox of the original code.

Sandbox(state).to(pc) runs the original from the block start 34142 (no interrupts) until pc is reached; .m is
its memory, .R its registers. Used to read each pipeline stage's real output for a ported stage to match.
"""
import importlib.machinery, importlib.util, struct, zlib

import glob as _g, os as _o, skoolkit as _sk
_CS = (_g.glob(_o.path.join(_o.path.dirname(_sk.__file__), 'csimulator*.pyd')) + [''])[0]   # SkoolKit's C simulator, wherever it is installed
_spec = importlib.util.spec_from_file_location('csimulator', _CS, loader=importlib.machinery.ExtensionFileLoader('csimulator', _CS))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
CSimulator = _mod.CSimulator

BLOCK = 34142
WORK = r'C:/1NEXT/castle_master_work/'


def states(name='m0_states_3k.bin'):
    with open(WORK + name, 'rb') as f:
        while True:
            h = f.read(4)
            if not h:
                return
            assert h == b'CMS0'
            frame, = struct.unpack('<I', f.read(4))
            regs = list(struct.unpack('<29H', f.read(58)))
            n, = struct.unpack('<I', f.read(4))
            yield frame, regs, zlib.decompress(f.read(n))


def s8(b):
    return b - 256 if b > 127 else b


def w16(m, a):
    v = m[a] | m[a + 1] << 8
    return v - 65536 if v > 32767 else v


class Sandbox:
    def __init__(self, ram, regs):
        self.c = CSimulator(bytearray(ram))
        self.m = self.c.memory
        self.R = self.c.registers
        for i in range(24):
            self.R[i] = regs[i]
        self.R[12] = regs[12]
        self.R[24] = BLOCK
        self.R[25] = 0
        self.R[26] = 0

    def to(self, pc, max_t=50_000_000):
        """run until PC == pc (False if the block ends first or the T budget runs out)"""
        self.c.run(self.R[24], pc)
        return self.R[24] == pc
