"""Castle Master M1: mutants of cmr.asm that the geometry gate (m1_gate.py) must reject. Each mutant changes one
exactness detail; every one must give DIFFER redraws on the sample (every N-th recorded redraw).
Usage: python m1_mutants.py [every N-th]
"""
import re, subprocess, sys
from m1_lib import W, assemble

MUT = {
    'A div32 truncates (no half-up)': ('        jr c,3F\n        inc hl\n3:      ld a,(dv_sign)',
                                       '        jr c,3F\n        nop\n3:      ld a,(dv_sign)'),
    'B projection: negative side off by one': ('2:      neg\n        add a,c\n        ret',
                                               '2:      cpl\n        add a,c\n        ret'),
    'C matrix without rounding': ('        ld a,h\n        bit 7,l\n        jr z,1F\n        inc a\n1:      ld hl,(m3out)',
                                  '        ld a,h\n        bit 7,l\n        jr z,1F\n        nop\n1:      ld hl,(m3out)'),
    'D sort ignores axis code 1': ('        cp 1\n        jr z,.no\n        or c',
                                   '        cp 1\n        jr z,.ax1\n        or c'),
    'E corners: no check against the first point': ('3:      call firstpt\n        ld a,b\n        cp d\n        jr nz,4F\n        ld a,c\n        cp e\n        jr z,.skip',
                                                    '3:      call firstpt\n        ld a,b\n        cp d\n        jr nz,4F\n        ld a,c\n        cp e\n        jr 4F'),
    'F facing: dot product to 32 bits only': ('        ld a,(acc48+5)\n        ld b,a',
                                              '        ld a,(acc48+3)\n        ld b,a'),
    'G sort cache: key takes b low bits from a': ('        ld a,c                          ; sort key b low',
                                                  '        ld a,e                          ; sort key b low'),
    'H sort cache: a swap result read as keep': ('        rra                             ; cached: bit 0 = keep',
                                                 '        scf                             ; cached: bit 0 = keep'),
}
# (an earlier F, the sign from bit 46 instead of 47, is equivalent in the reachable range: |dot| < 2^45)
ONLY = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None


def main():
    every = sys.argv[1] if len(sys.argv) > 1 else '20'
    src = open(W + 'cmr.asm').read()
    bad = 0
    for i, (name, (a, b)) in enumerate(MUT.items()):
        if ONLY and name[0] not in ONLY:
            continue
        if src.count(a) != 1:
            print('%s: pattern found %d times' % (name, src.count(a)))
            bad += 1
            continue
        s = src.replace(a, b).replace('SAVEBIN "cmr.bin"', 'SAVEBIN "cmr_mut%d.bin"' % i)
        if name.startswith('D'):
            s = s.replace('        ld de,4\n        add ix,de\n        add iy,de\n        djnz .ax',
                          '.ax1:   ld de,4\n        add ix,de\n        add iy,de\n        djnz .ax')
        open(W + 'cmr_mut%d.asm' % i, 'w').write(s)
        assemble('cmr_mut%d' % i)
        r = subprocess.run([sys.executable, 'm1_gate.py', 'm0_states.bin', every, '--bin', 'cmr_mut%d' % i,
                            '--show', '0'], cwd=W, capture_output=True, text=True)
        lines = [l.strip() for l in r.stdout.splitlines() if 'redraws' in l]
        killed = any('DIFFER' in l for l in lines)
        u = subprocess.run([sys.executable, 'm1_unit2.py', '--n', '4000', '--bin', 'cmr_mut%d' % i], cwd=W,
                           capture_output=True, text=True)
        ul = [l.strip() for l in u.stdout.splitlines() if 'DIFFER' in l]
        lines.append('sweeps: ' + (', '.join(ul) if ul else 'all equal'))
        killed = killed or bool(ul)
        print('%-48s %s  %s' % (name, 'FAILS (good)' if killed else 'PASSES (BAD)', '; '.join(lines)))
        bad += not killed
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
