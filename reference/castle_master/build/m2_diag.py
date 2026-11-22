"""Castle Master M2 diagnostic build: the border is RED while the renderer state is active (r_enter .. r_leave),
black otherwise. On hardware the red band's height = the renderer's real time (a full screen of red = 1 frame).
Writes castle_master_m2_diag.nex. Usage: python m2_diag.py
"""
import sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import z80tonex as zt, nextboot
from m2_lib import W, assemble
import m2_build

T = '        '
NM = 'cm2d'
EDITS = [
    (T + 'ld a,e\n' + T + 'ld (g_spd),a\n' + T + 'HLIB_IFF_EI\n' + T + 'jp (hl)',
     T + 'ld a,e\n' + T + 'ld (g_spd),a\n' + T + 'ld a,2\n' + T + 'out (0xFE),a\n' + T + 'HLIB_IFF_EI\n' + T + 'jp (hl)'),
    ('r_leave:\n' + T + 'pop hl\n' + T + 'ld a,(g_spd)',
     'r_leave:\n' + T + 'pop hl\n' + T + 'xor a\n' + T + 'out (0xFE),a\n' + T + 'ld a,(g_spd)'),
]


def main():
    g = open(W + 'cm2_glue.asm').read()
    for a, b in EDITS:
        assert g.count(a) == 1, a
        g = g.replace(a, b)
    open(W + NM + '_glue.asm', 'w').write(g.replace('SAVEBIN "cm2_', 'SAVEBIN "%s_' % NM))
    c = open(W + 'cmr.asm').read()
    open(W + NM + '_cmr.asm', 'w').write(c.replace('INCLUDE "cm2_glue.asm"', 'INCLUDE "%s_glue.asm"' % NM)
                                         .replace('SAVEBIN "cmr.bin"', 'SAVEBIN "%s_cmr.bin"' % NM))
    open(W + NM + '.asm', 'w').write('        DEFINE M2\n        INCLUDE "%s_cmr.asm"\n' % NM)
    assemble(NM)
    out = W + 'castle_master_m2_diag.nex'
    z80 = W + 'castle_master.z80'
    snap, ta, tail, _ = zt.convert(z80, out, patch=m2_build.CastlePatch(NM), quiet=True)
    bad = nextboot.check(out, z80, m2_build.CastlePatch(NM), tail=(ta, ta + len(tail)))
    print('wrote', out, '- boot check:', 'OK' if not bad else bad)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
