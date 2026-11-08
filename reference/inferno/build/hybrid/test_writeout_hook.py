"""980B hook as assembled, on the CTC model: pad time against the original's write-out T, stack untouched, work slices taken
while the coroutine is pending, fallback without a CTC. From nexclash: python test_writeout_hook.py"""
import sys
sys.path.insert(0, '.')
import nexclash.inferno as I
from nexclash import simpool, z80n
from nexclash.dizzy6 import _rw_simulator
h = I.load_profile()['hooks']


def original_t(rows):
    """The original's T from 980B through RET, the formula the replays check (without the fitted 2,700)."""
    return 4 + sum(569 if a == 0 else 22 + 198 * a + 542 for a in rows) + 21 + 24


def run(rows, ctc=True, go=0, code=None):
    patch = I.CopierWindowPatch(code, work=True) if code else I.CopierWindowPatch(work=True)
    ram = list(bytes(65536))
    sp = 0xA000
    at = sp
    for a in rows:                     # a row: F (no carry), A, then 4 bytes per wide line, then 4
        ram[at], ram[at + 1] = 0x40 if a == 0 else 0, a
        at += 2 + 4 * a + 4
    ram[at], ram[at + 1] = 1, 0
    before = bytes(ram)
    rom = bytearray(patch.rom)
    stub = bytes.fromhex(h['wohook'])
    rom[0x3B90:0x3B90 + len(stub)] = stub
    patch.rom = rom
    mem = I.CopierWorkMemory(ram, bytearray(8192), patch, 1, 0, ctc, 0, 200)
    mem.mmu0 = 255
    mem.pages[I.CW_PAGE][0x1810] = 1 if ctc else 2     # CW_CLK
    mem.pages[I.CW_PAGE][0x1849] = go
    regs = [0] * 30
    regs[12], regs[24], regs[26], regs[27] = sp, 0x3B90, 1, 2
    sim = simpool.machine(_rw_simulator(), mem, regs, 'wo')
    sim.set_tracer(mem)
    z80n.install(sim, mem.nextreg)
    r = sim.registers
    elapsed, n = 0.0, 0
    while r[24] not in (0x9877, 0x980C):
        before_t, speed, reads = r[25], mem.speed, mem.fast_reads
        mem.wall = elapsed
        sim.opcodes[mem[r[24]]]()
        elapsed += I._cost(r, before_t, speed, reads, mem)
        n += 1
        assert n < 3_000_000, 'no exit'
    assert list(mem.ram[0xA000:at + 2]) == list(before[0xA000:at + 2]), 'write-out stack changed'
    run.state = mem.pages[69][I.WK_STATE], mem.pages[I.CW_PAGE][0x1849]
    return r[24], elapsed, r[12], mem.speed, mem.mmu0, n


cases = [[0] * 18, [10] * 18, [14] * 18, [3, 0, 7, 20, 0, 11] * 3]
for rows in cases:
    pc, t, sp, speed, page, n = run(rows)
    want = original_t(rows) + 2700
    assert pc == 0x9877 and sp == 0xA000 and speed == 0 and page == 255, (pc, sp, speed, page)
    assert abs(t - want) < 400, ('pad', t, want)
    print('rows', sum(rows), 'wide lines: hook %d T, original model + 2700 = %d T, error %+d' % (t, want, t - want))
pc, t, sp, speed, page, n = run([5] * 18, ctc=False)
assert pc == 0x980C and speed == 0 and page == 255, (pc, speed, page)
print('no CTC: original write-out taken')

pc, t, sp, speed, page, n = run([10] * 18, go=2)
want = original_t([10] * 18) + 2700
assert run.state == (2, 0), run.state                     # the pending coroutine finished in the write-out time
assert abs(t - want) < 400 and sp == 0xA000, (t, want)
print('work pending: finished, hook %d T, target %d T' % (t, want))
head = bytes.fromhex(h['cwhead'])
at = head.index(bytes.fromhex('219301'))                  # ld hl,403
pc, t, *_ = run([10] * 18, code=head[:at + 1] + bytes.fromhex('0100') + head[at + 3:])
assert abs(t - want) > 5000, ('control not informative', t, want)
print('control detected: fixed time wrong, %d T' % t)
