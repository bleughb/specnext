"""Castle Master M2: broken builds that m2_sim.py must reject (each breaks one thing the integration depends on).
Usage: python m2_mutants.py [every N-th state] [letters]
"""
import subprocess, sys
from m2_lib import W, assemble

T = '        '
# name: (file, old, new, m2_sim mode)
MUT = {
    'A interrupt stub leaves the work RAM in slot 2': (
        'glue', T + 'nextreg 0x52,10\n' + T + 'nextreg 0x53,11\n' + T + 'nextreg 0x54,4\n' + T + 'nextreg 0x55,5\n' + T + 'call GAME_ISR',
        T + 'nextreg 0x53,11\n' + T + 'nextreg 0x54,4\n' + T + 'nextreg 0x55,5\n' + T + 'call GAME_ISR', '--irq'),
    'B slot 4 page not recorded before the NEXTREG': (
        'cmr', T + 'ld (cur54),a                    ; first: an interrupt stub puts (cur54) back in the window\n', '', '--storm'),
    'C r_leave leaves Layer 2 in slot 4': (
        'glue', T + 'nextreg 0x53,11\n' + T + 'nextreg 0x54,4\n' + T + 'nextreg 0x55,5\n' + T + 'nextreg 0x50,0xFF',
        T + 'nextreg 0x53,11\n' + T + 'nextreg 0x55,5\n' + T + 'nextreg 0x50,0xFF', ''),
    'D no copy of the shown picture': (
        'glue', T + 'call z,l2copy\n', T + 'nop\n', ''),
    'E yaw not staged': (
        'glue', T + 'ld a,(27319+G)\n' + T + 'ld (in_yaw),a\n', '', ''),
    "F HL' not restored by r_leave": (
        'glue', T + 'exx\n' + T + 'pop hl\n' + T + 'pop de\n', T + 'exx\n' + T + 'pop hl\n' + T + 'ld hl,0\n' + T + 'pop de\n', ''),
    'G interrupt stub keeps the renderer stack': (
        'glue', T + 'ld (isr_sp),sp\n' + T + 'ld sp,(g_sp)\n', T + 'ld (isr_sp),sp\n', '--irq'),
    'H copy source page not recorded (slot 5)': (
        'glue', '1:      ld a,c\n' + T + 'ld (cur55),a\n' + T + 'nextreg 0x55,a', '1:      ld a,c\n' + T + 'nextreg 0x55,a', '--storm'),
    'I flip without the palette': (
        'glue', 'm2_show:\n' + T + 'call setpal\n', 'm2_show:\n', ''),
}


def main():
    every = sys.argv[1] if len(sys.argv) > 1 else '100'
    only = set(sys.argv[2]) if len(sys.argv) > 2 else None
    src = {'cmr': open(W + 'cmr.asm').read(), 'glue': open(W + 'cm2_glue.asm').read()}
    bad = 0
    for i, (name, (f, a, b, mode)) in enumerate(MUT.items()):
        if only and name[0] not in only:
            continue
        if src[f].count(a) != 1:
            print('%s: pattern found %d times' % (name, src[f].count(a)))
            bad += 1
            continue
        nm = 'cm2_mut%d' % i
        s = dict(src)
        s[f] = s[f].replace(a, b)
        open(W + nm + '_glue.asm', 'w').write(s['glue'].replace('SAVEBIN "cm2_', 'SAVEBIN "%s_' % nm))
        open(W + nm + '_cmr.asm', 'w').write(s['cmr'].replace('INCLUDE "cm2_glue.asm"', 'INCLUDE "%s_glue.asm"' % nm)
                                             .replace('SAVEBIN "cmr.bin"', 'SAVEBIN "%s_cmr.bin"' % nm))
        open(W + nm + '.asm', 'w').write('        DEFINE M2\n        INCLUDE "%s_cmr.asm"\n' % nm)
        assemble(nm)
        args = [sys.executable, 'm2_sim.py', 'm0_states.bin', every, '--prefix', nm, '--show', '1'] + ([mode] if mode else [])
        r = subprocess.run(args, cwd=W, capture_output=True, text=True)
        lines = [' '.join(l.split())[:150] for l in r.stdout.splitlines() if 'FAILED' in l or 'did not end' in l or l.startswith('  state')]
        killed = bool(r.returncode)
        print('%-48s %s  %s' % (name, 'FAILS (good)' if killed else 'PASSES (BAD)', '; '.join(lines[:3]) or r.stderr[-200:]))
        bad += not killed
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
