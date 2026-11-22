"""Castle Master M1: mutants of cmr.asm's raster that m1_raster_gate.py (sample, also with lightning forced) or
m1_raster_unit.py (sweeps; also with interrupts injected) must reject. Each changes one exactness detail.
Usage: python m1_raster_mutants.py [every N-th] [sweep n] [letters]
"""
import subprocess, sys
from m1_lib import W, assemble

T = '        '
MUT = {
    'A span starts at lo (not max(lo, 1) - 1)': (
        T + 'jr z,2F\n' + T + 'dec a\n2:      ld e,a                          ; E = first pixel',
        T + 'jr z,2F\n' + T + 'nop\n2:      ld e,a                          ; E = first pixel'),
    'B span rejects an end >= 192': (
        T + 'ld a,d\n' + T + 'cp 193\n' + T + 'ret nc\n' + T + 'cp h',
        T + 'ld a,d\n' + T + 'cp 192\n' + T + 'ret nc\n' + T + 'cp h'),
    'C slope truncated (no half-up)': (
        T + 'ld a,b\n' + T + 'cp e\n' + T + 'ret c\n' + T + 'inc hl\n' + T + 'ret',
        T + 'ld a,b\n' + T + 'cp e\n' + T + 'ret c\n' + T + 'nop\n' + T + 'ret'),
    'D first left edge without the half-slope rule': (
        T + 'bit 0,a\n' + T + 'jr nz,5F', T + 'bit 0,a\n' + T + 'jr 5F'),
    'E pattern row from the row, not y': (
        T + 'ld a,(r_y)\n' + T + 'and 3\n' + T + 'add a,a\n' + T + 'add a,a\n' + T + 'add a,a\n' + T + 'add a,low rtile',
        T + 'ld a,(r_row)\n' + T + 'and 3\n' + T + 'add a,a\n' + T + 'add a,a\n' + T + 'add a,a\n' + T + 'add a,low rtile'),
    'F fill pattern row = (rows left - 1) & 3': (
        T + 'call l2row\n' + T + 'ld a,b\n' + T + 'and 3', T + 'call l2row\n' + T + 'ld a,b\n' + T + 'dec a\n' + T + 'and 3'),
    'P row fill: pixels 0-1 take the values of 2-3': (
        T + 'ld l,a\n' + T + 'ex de,hl                        ; DE = pixels 2, 3',
        T + 'ld l,a\n' + T + 'ld b,h\n' + T + 'ld c,l\n' + T + 'ex de,hl                        ; DE = pixels 2, 3'),
    'G lowest vertex = the first of ties': (
        T + 'cp (hl)\n' + T + 'jr c,4F', T + 'cp (hl)\n' + T + 'jr c,4F\n' + T + 'jr z,4F'),
    'H line step sign flipped': (
        T + 'ld a,255\n' + T + 'jr nc,3F\n' + T + 'ld a,1', T + 'ld a,1\n' + T + 'jr nc,3F\n' + T + 'ld a,255'),
    'I mountains not scrolled by yaw': (
        T + 'and 7\n' + T + 'add a,a\n' + T + 'ld (c_a),a', T + 'and 0\n' + T + 'add a,a\n' + T + 'ld (c_a),a'),
    'J bolt not lifted above the band': (
        'ld hl,c_lrows\n' + T + 'add a,(hl)\n' + T + 'ld e,a', 'ld hl,c_lrows\n' + T + 'xor a\n' + T + 'ld e,a'),
    'K min / max path skipped': (
        '.L443:  ld a,(r_fl)                     ; chains done; still flagged -> the min / max x of all points\n' + T + 'or a',
        '.L443:  xor a\n' + T + 'or a'),
    'L PUSH fill: odd end pixel not written': (
        T + "ex af,af'\n" + T + 'ld (hl),a\n3:', T + "ex af,af'\n" + T + 'nop\n3:'),
    'M PUSH fill: odd first pixel not written': (
        T + 'ld (hl),d                       ; first pixel odd', T + 'nop                             ; first pixel odd'),
    'N left edge end y not refreshed': (
        T + 'ld e,(hl)\n' + T + 'ld iyl,e\n', T + 'ld e,(hl)\n'),
    'O PUSH fill: BC values swapped': (
        T + 'ld b,a\n' + T + "ex af,af'\n" + T + 'ld c,a\n' + T + 'ld a,l',
        T + 'ld c,a\n' + T + "ex af,af'\n" + T + 'ld b,a\n' + T + 'ld a,l'),
    'Q PUSH fill: no margin below the last PUSH': (
        T + 'add a,3\n' + T + 'and 0xFE\n' + T + 'ld e,a                          ; E = m',
        T + 'add a,1\n' + T + 'and 0xFE\n' + T + 'ld e,a                          ; E = m'),
}


def main():
    every = sys.argv[1] if len(sys.argv) > 1 else '20'
    n = sys.argv[2] if len(sys.argv) > 2 else '800'
    only = set(sys.argv[3]) if len(sys.argv) > 3 else None
    src = open(W + 'cmr.asm').read()
    bad = 0
    for i, (name, (a, b)) in enumerate(MUT.items()):
        if only and name[0] not in only:
            continue
        if src.count(a) != 1:
            print('%s: pattern found %d times' % (name, src.count(a)))
            bad += 1
            continue
        nm = 'cmr_rmut%d' % i
        open(W + nm + '.asm', 'w').write(src.replace(a, b).replace('SAVEBIN "cmr.bin"', 'SAVEBIN "%s.bin"' % nm))
        assemble(nm)
        out = []
        killed = False
        for tag, args in (('gate', ['m1_raster_gate.py', 'm0_states.bin', every, '--bin', nm, '--show', '0']),
                          ('gate light', ['m1_raster_gate.py', 'm0_states.bin', str(int(every) * 4), '--light', '--bin', nm, '--show', '0']),
                          ('sweeps', ['m1_raster_unit.py', '--n', n, '--bin', nm]),
                          ('sweeps irq', ['m1_raster_unit.py', '--n', '150', '--irq', '--bin', nm])):
            r = subprocess.run([sys.executable] + args, cwd=W, capture_output=True, text=True)
            d = [' '.join(l.split()) for l in r.stdout.splitlines() if 'DIFFER' in l or 'wrong' in l or 'outside' in l]
            out.append('%s: %s' % (tag, ', '.join(d) or ('equal' if not r.returncode else 'crash')))
            if d or r.returncode:
                killed = True
                break
        print('%-46s %s  %s' % (name, 'FAILS (good)' if killed else 'PASSES (BAD)', '; '.join(out)))
        bad += not killed
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
