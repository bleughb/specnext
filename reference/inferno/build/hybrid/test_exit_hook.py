"""Hook 901C as assembled against the original LD IY,5C3A: registers, SP, RAM, layers hidden, slots and speed."""
import sys
sys.path.insert(0, '.')
import nexclash.inferno as I
from nexclash import simpool, z80n
from nexclash.dizzy6 import _rw_simulator
h = I.load_profile()['hooks']
code = bytes.fromhex(h['modalx'])
class M:
    def __init__(s, code, nr):
        s.rom = bytearray(16384); s.rom[0x1BE0:0x1BE0 + 0] = b''
        s.rom2 = code; s.page68 = bytearray(8192); s.ram = bytearray(65536); s.slot0 = 255; s.nr = dict(nr); s.sel = 0; s.speed = 0
    def __getitem__(s, a):
        if isinstance(a, slice): return [s[i] for i in range(*a.indices(65536))]
        if a < 0x2000: return s.page68[a] if s.slot0 == 68 else 0xFF
        if 0x3BE0 <= a < 0x3BE0 + len(s.rom2):
            if s.nr.get(0x51, 255) != 255: raise AssertionError('hook unmapped its own code')
            return s.rom2[a - 0x3BE0]
        return s.ram[a]
    def __setitem__(s, a, v):
        if a < 0x2000 and s.slot0 == 68: s.page68[a] = v
        elif a >= 0x4000: s.ram[a] = v
        else: raise AssertionError('wrote %04X' % a)
    def nextreg(s, r, v):
        if r == 0x50: s.slot0 = v
        elif r in (0x51, 0x52): s.nr[r] = v
        elif r == 7: s.speed = v
        else: s.nr[r] = v
    def read_port(s, regs, port): return s.nr.get(s.sel, 0) if port == 0x253B else 255
    def write_port(s, regs, port, v, *a):
        if port == 0x243B: s.sel = v
def run(code, nr, sp=0x86D5):
    m = M(code, nr); m.page68[0x3F7] = 0
    m.ram[0x4000:0x4004] = b'\x11\x22\x33\x44'
    m.page68[0x3F6] = 2
    r = [(i * 31 + 3) & 255 for i in range(30)]
    r[12], r[24], r[26], r[27] = sp, 0x3BE0, 1, 1
    sim = simpool.machine(_rw_simulator(), m, r, 'x'); sim.set_tracer(m); z80n.install(sim, m.nextreg)
    q = sim.registers; before = list(q); n = 0
    while q[24] != 0x9020:
        sim.opcodes[m[q[24]]](); n += 1
        assert n < 2000, 'no exit'
    bad = [i for i in range(24) if i not in (10, 11, 12, 15, 25, 24) and q[i] != before[i]]
    ok = not bad and q[12] == sp and q[10] == 0x5C and q[11] == 0x3A and m.slot0 == 255 and m.speed == 0 and not m.nr[0x6B] & 0x80 and not m.nr[0x15] & 1 and m.nr.get(0x52) == 10 and m.nr[0x62] == 0 and m.page68[0x3F6] == 0
    return ok, bad, q[12], m.nr
ok, *rest = run(code, {0x6B: 0x8B, 0x15: 1, 0x62: 0x40})
print('hook', ok, rest[:2])
assert ok
# negative controls
for name, broken in (('sprites not hidden', code.replace(bytes.fromhex('E6FEED9215'), bytes.fromhex('E6FFED9215'))), ('SP not restored', code.replace(bytes.fromhex('ED7BF003'), bytes(4)))):
    assert broken != code, name
    try:
        good = run(broken, {0x6B: 0x8B, 0x15: 1, 0x62: 0x40})[0]
    except Exception as e:
        good = False
    assert not good, 'control not informative: ' + name
    print('control detected:', name)
