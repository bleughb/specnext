"""The loader's build_screen on the Z80 harness (run with py -3.13 from castle_master_work)."""
import os, sys, hashlib
os.environ.setdefault('NXC_ZX0_DIR', 'C:/1NEXT/castle_master_work/zx0bin')
os.environ.setdefault('TMPDIR', 'C:/1NEXT/castle_master_work/tmp')
sys.path.insert(0, 'C:/1NEXT/nxc/tests')
import nexclash_harness as H
F = 'Castle Master (1990)(Incentive)'
tape = open('nxc_out/%s/Castlemaster1.tap' % F, 'rb').read()
new = open('nxc_out_1.1/%s/%s.nxc' % (F, F), 'rb').read()
old = open('nxc_out/%s/%s.nxc' % (F, F), 'rb').read()
scr = open('cm_scr_a.scr', 'rb').read()
binary, symbols = H.assemble()
NEX = '$/tmp/nexclash.nex'
ok = True
def check(what, cond):
    global ok
    ok = ok and bool(cond)
    print(('ok   ' if cond else 'FAIL ') + what)
def run(patch, snap=()):
    m = H.Machine(binary, symbols, {'patch.nxc': patch, 'Castlemaster1.tap': tape}, keys=('enter',))
    shots = {}
    names = []
    for name in snap:
        def grab(name=name):
            shots.setdefault(name, (bytes(m.m.memory[0x4000:0x5B00]), m.ticks))
        m.callbacks[name] = grab
        names.append(name)
    m.set_phases(['zx0_decode'] + names)
    m.guard_iopage()
    m.m.unmark_addr(0x5C8D, m.m.WRITE_MARK)
    m.m.unmark_addr(0x5C48, m.m.WRITE_MARK)
    failed, message = m.run('"patch.nxc"', limit_seconds=120)
    return m, failed, message, shots
def cell(mem, col):
    return bytes(mem[0x10E0 + col + 256 * k] for k in range(8)), mem[0x1AE0 + col]
DOT = (bytes((0, 0, 0, 0x18, 0x18, 0, 0, 0)), 0x47)

m, failed, message, shots = run(new, snap=('unlock', 'load_bank_index', 'write_screen'))
check('1.1 patch: not refused (%r)' % message, not failed)
out = bytes(m.written.get(NEX, b''))
check('1.1 patch: output is castle_master_m3d_08.nex', out == open('castle_master_m3d_08.nex', 'rb').read())
at_enter, t0 = shots['unlock']
def judge(when, mem, dots):
    rows = []
    for r in range(24):
        rows.append(''.join(H.GLYPHS.get(bytes(mem[(r & 0x18) << 8 | (r & 7) << 5 | c | k << 8] for k in range(8)), '#') for c in range(32)))
    want = 'Patching' + '.' * dots
    check('%s: the last line starts %r' % (when, rows[23][:len(want) + 1]), rows[23].startswith(want) and rows[23][len(want)] != '.')
    diff = [i for i in range(6912) if mem[i] != scr[i]]
    allowed = set()
    for c in range(len(want)):
        allowed |= {0x10E0 + c + 256 * k for k in range(8)} | {0x1AE0 + c}
    check('%s: the loading screen, but for that text (%d bytes differ)' % (when, len(diff)), set(diff) <= allowed)
judge('at ENTER, before the game is checked', at_enter, 0)
final = bytes(m.m.memory[0x4000:0x5B00])
judge('at the end', final, 8)
check('ATTR_P and BORDCR white on black', m.m.memory[0x5C8D] == 7 and m.m.memory[0x5C48] == 7)
print('     clean():', m.clean())
t = {k: v[1] for k, v in shots.items()}
print('     28 MHz T-states, no file time: ENTER to unlock %d, unlock done %d, file made %d, end %d (%.2f s from ENTER to the end)' % (t['unlock'], t['load_bank_index'], t['write_screen'], m.ticks, (m.ticks - t['unlock']) / 28e6))
open('tmp/scr_enter.scr', 'wb').write(at_enter); open('tmp/scr_final.scr', 'wb').write(final)

m2, failed, message, shots2 = run(old, snap=('unlock',))
check('1.0 patch (no build_screen): not refused, output is castle_master_m3d_07.nex', not failed and bytes(m2.written.get(NEX, b'')) == open('castle_master_m3d_07.nex', 'rb').read())
check('1.0 patch: the screen is as it was at ENTER (the menu), sysvars untouched', bytes(m2.m.memory[0x4000:0x5B00]) == shots2['unlock'][0] and m2.clean() == [])
print('PASS' if ok else 'FAIL')
