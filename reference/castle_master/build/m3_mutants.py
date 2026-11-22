"""Castle Master M3a: broken builds that m3_sim.py must reject.
Usage: python m3_mutants.py [every N-th state] [letters] [state list, e.g. 2745,2746,2747,2748,4227] [phase]
"""
import os, subprocess, sys
from m2_lib import W, assemble

T = '        '
MUT = {
    'A interrupt tick without the frame rule': (
        T + 'ld de,HLIB_PACE_NL/2\n' + T + 'or a\n' + T + 'sbc hl,de\n' + T + 'add hl,de\n' + T + 'jr nc,2F\n',
        T + 'jr 2F\n'),
    'B final view from the in-between inputs': (
        T + 'ld hl,fin_g\n' + T + 'ld de,in_cam\n' + T + 'ld bc,15\n' + T + 'ldir\n' + T + 'ld hl,fin_r\n',
        T + 'ld hl,fin_r\n'),
    'C copy from the bank on screen, not the last view': (
        'l2copy:\n' + T + 'ld a,(l2last)\n', 'l2copy:\n' + T + 'ld a,(l2shown)\n'),
    'D sound at 28 MHz': (
        T + 'call ptick                      ; the window counted up to here\n' + T + 'xor a\n' + T + 'ld (m_spd),a\n'
        + T + 'nextreg 0x07,0\n',
        T + 'call ptick\n'),
    'E r_leave keeps 28 MHz': (
        T + 'HLIB_IFF_EI\n' + T + 'ld a,(VP+10)\n' + T + 'or a\n' + T + 'jr nz,1F\n' + T + 'ld (m_spd),a\n'
        + T + 'nextreg 0x07,0\n',
        T + 'HLIB_IFF_EI\n'),
    'F the next bank may be the last view': (
        T + 'ld hl,l2last\n' + T + 'cp (hl)\n' + T + 'call z,.nx\n', ''),
    'G no wait for the target': (
        T + 'ld (t_fin),hl\n' + T + 'call waittgt\n', T + 'ld (t_fin),hl\n'),
    'H sound time counted in the window': (
        T + 'call prest                      ; the window goes on from now: the sound\'s time is not in it\n', ''),
    'I in-between fraction not applied to the turn': (
        T + 'ld a,(tw_dy)\n' + T + 'ld e,a\n' + T + 'ld a,(prev+6)\n' + T + 'call .fine\n' + T + 'ld (in_yaw),a\n',
        T + 'ld a,(tw_dy)\n' + T + 'ld e,a\n' + T + 'ld a,(prev+6)\n' + T + 'call .fine\n' + T + 'ld (in_yaw),a\n' + T + 'ld (fin_g+6),a\n'),
    'J interrupt waits counted in the window (run with every = 440)': (
        T + 'ld a,1\n' + T + 'ld (m_wait),a                   ; the interrupt wrapper leaves the clock alone during the wait\n', ''),
    'K handler time not added to the target (run: 1 K 2745,2746,2747,2748,4227)': (
        T + 'ld a,(m_ni)\n' + T + 'or a\n' + T + 'jr z,.none\n', T + 'jr .none\n'),
    'L the plain-state wrapper restores the speed from the window flag (run: 1 L 770 557516 = m3_rgap.py cm3_mut11 770)': (
        T + "ld a,(m_spd)                    ; the interrupted code's speed (not the window's: an\n"
        + T + 'nextreg 0x07,a                  ; interrupt in r_enter comes before the window opens)\n',
        T + 'ld a,(VP+10)\n' + T + 'or a\n' + T + 'jr nz,1F\n' + T + 'nextreg 0x07,0\n1:\n'),
    'M the window opens with interrupts on (run: 1 M 2416 556016)': (
        'popen:  HLIB_IFF_DI\n' + T + 'push af\n', 'popen:  push af\n'),
    'N an interrupt takes no reading during a main-line one, no re-read (run: 1 N 2892 555200)': (
        '.r:     xor a\n' + T + 'ld (m_sk),a\n' + T + 'ld de,(VP)\n' + T + 'ld bc,(VP+18)\n'
        + T + 'call hlib_since_c               ; HL = lines since the last reading; +22 / +24 = this reading\n'
        + T + 'HLIB_IFF_DI\n' + T + 'push af\n' + T + 'ld a,(m_sk)\n' + T + 'or a\n' + T + 'jr nz,.again\n',
        '.r:     ld a,1\n' + T + 'ld (m_wait),a\n' + T + 'ld de,(VP)\n' + T + 'ld bc,(VP+18)\n'
        + T + 'call hlib_since_c\n' + T + 'HLIB_IFF_DI\n' + T + 'push af\n' + T + 'xor a\n'),
    # M3b: the overlay sprites
    'O the marker left in ov_s': (
        T + 'ld a,(27405+G)                  ; the raster', T + 'jr 1F\n' + T + 'ld a,(27405+G)                  ; the raster'),
    'P the cursor rectangle one row short at the top': (
        T + 'inc a                           ; top row, may be negative (>= -126)\n', T + 'inc a\n' + T + 'inc a\n'),
    'Q no overlay update after the cursor': (
        T + 'call ov_cur\n' + T + 'call r_leave', T + 'call r_leave'),
    'R sprites with old opaque pixels not rebuilt': (
        '.lx:    ld a,(de)\n' + T + 'or (hl)\n', '.lx:    ld a,(hl)\n' + T + 'or a\n'),
    'S sprites left on over a non-view screen (run: 1 S 15,406,1387)': (
        T + 'nextreg 0x15,0                  ; the overlay sprites with it\n' + T + 'jp 0x9F19\nh_flip:',
        T + 'jp 0x9F19\nh_flip:'),
    'T ink and paper swapped in the sprite palette': (
        T + 'nextreg 0x40,1\n' + T + 'ld a,d\n' + T + 'nextreg 0x41,a\n' + T + 'ld a,e\n',
        T + 'nextreg 0x40,1\n' + T + 'ld a,e\n' + T + 'nextreg 0x41,a\n' + T + 'ld a,d\n'),
    'U the screen against the wrong raster byte': (
        T + 'xor (iy+0)                      ; screen ^ the raster\'s\n', T + 'xor (iy+1)\n'),
    'V the cursor bottom row as 9 bits (y >= 250 taken as below the view)': (
        T + 'jp m,.out                       ; bit 7: all above the view\n', T + 'jp c,.out\n'),
    'W the dissolve under Layer 2 (checked by m3b_diss.py)': (
        'h_diss: nextreg 0x69,0\n', 'h_diss: nop\n'),
    'X the MMU registers read with interrupts on (checked by m3b_race.py)': (
        'ov_in:  HLIB_IFF_DI\n', 'ov_in:  push af\n        pop af\n'),
    # hardware runs 2-3: the fixed overlays, the portcullis
    'Y the thrown rock taken for the pointer (m3b_seq.py to frame 1400)': (
        T + 'ld a,h\n' + T + 'cp 0x7F\n' + T + 'jr nz,1F\n' + T + 'ld a,l\n' + T + 'cp 0x20\n' + T + 'jr nz,1F\n', ''),
    'Z the portcullis bars not refreshed (m3b_seq.py to frame 800)': (
        T + 'call ov_pstep\n', ''),
    'a the death drop under Layer 2 (m3b_diss.py portc)': (
        T + 'ld a,(m_pc)\n' + T + 'cp 1\n' + T + 'jr z,1F\n' + T + 'nextreg 0x69,0\n',
        T + 'ld a,(m_pc)\n' + T + 'cp 1\n' + T + 'jr 1F\n' + T + 'nextreg 0x69,0\n'),
    "b the pointer's outline drawn (its clear bits ignored)": (
        T + 'pop hl\n' + T + 'jr c,.c\n', T + 'pop hl\n'),
    'c the cross always white': (
        T + 'ld a,3\n' + T + 'ret c\n' + T + 'inc a\n' + T + 'ret\n', T + 'ld a,3\n' + T + 'ret\n'),
    "d the sight's colour from the bank on screen, not the new one": (
        'ov_sightc:\n' + T + 'ld a,(in_l2page)\n', 'ov_sightc:\n' + T + 'ld a,(l2shown)\n'),
    'e the area colours not read again at the portcullis (m3b_seq.py to frame 800)': (
        'ov_pstep:\n' + T + 'call ov_in\n' + T + 'ld a,(27353+G)\n' + T + 'ld (in_attr),a\n',
        'ov_pstep:\n' + T + 'call ov_in\n'),
    'f Layer 2 left off at the portcullis (m3b_seq.py to frame 800)': (
        T + 'call r_leave\n' + T + 'nextreg 0x69,0x80\n' + T + 'nextreg 0x15,1\n',
        T + 'call r_leave\n' + T + 'nextreg 0x15,1\n'),
    # the deferred flip (CMSRC=cm7 and later)
    'g no flush of the waiting flip before the raster': (
        T + 'call render_geom\n' + T + 'call flipfl                     ; the view before this one on screen before its bank can be chosen again\n',
        T + 'call render_geom\n'),
    'h an in-between view flipped at any line': (
        T + 'call flip_in\n' + T + 'jr nc,flip_go\n' + T + 'neg\n', T + 'call flip_in\n' + T + 'jr flip_go\n' + T + 'neg\n'),
    'i the waiting flip done at the first look, whatever the line': (
        T + 'call flip_in\n' + T + 'call nc,flip_go\n', T + 'call flip_in\n' + T + 'call flip_go\n'),
    'j no next bank chosen at a deferred flip': (
        T + 'call flip_do\n' + T + 'jp nexth\n', T + 'call flip_do\n' + T + 'ret\n'),
    # the speed pass (CMSRC=cm7): renderer maths, the PUSH run, the DMA copy
    'k div32 without its rounding': (T + 'ex de,hl\n' + T + 'jr c,5F\n' + T + 'inc hl\n', T + 'ex de,hl\n' + T + 'jr c,5F\n'),
    'l span: the third pixel below the PUSH run never written': (T + 'sbc a,a                         ; bit 0 = 3 pixels below m\n', T + 'xor a\n'),
    'm DMA chunks across the frame interrupt (no line gate)': (T + 'add a,18\n' + T + 'cp 22\n' + T + 'jr c,.cpu\n', T + 'add a,18\n' + T + 'cp 22\n'),
    'n proj1: a failed step still counts': (T + 'sbc hl,de\n' + T + 'dec a\n' + '1:      inc a\n' + T + 'ENDR\n', T + 'sbc hl,de\n' + '1:      inc a\n' + T + 'ENDR\n'),
}
CURSOR = 'OPQRSTUVbcd'                 # run with --cursor 20
SEQ = {'Y': '1400', 'Z': '800', 'e': '800', 'f': '800'}        # m3b_seq.py --stop N


def main():
    every = sys.argv[1] if len(sys.argv) > 1 else '100'
    only = set(sys.argv[2]) if len(sys.argv) > 2 else None
    SRC = os.environ.get('CMSRC', '')            # e.g. cm7: the mutants of cm7_cmr.asm / cm7_glue.asm
    src = {'cmr': open(W + (SRC + '_cmr.asm' if SRC else 'cmr.asm')).read(), 'glue': open(W + (SRC or 'cm3') + '_glue.asm').read()}
    if SRC:
        src['glue'] = src['glue'].replace('SAVEBIN "%s_' % SRC, 'SAVEBIN "cm3_')
        src['cmr'] = src['cmr'].replace('INCLUDE "%s_glue.asm"' % SRC, 'INCLUDE "cm3_glue.asm"').replace('SAVEBIN "%s_cmr.bin"' % SRC, 'SAVEBIN "cmr.bin"')
    bad = 0
    for i, (name, (a, b)) in enumerate(MUT.items()):
        if only and name[0] not in only:
            continue
        gl, cm = src['glue'], src['cmr']
        if gl.count(a) == 1:
            gl = gl.replace(a, b)
        elif gl.count(a) == 0 and cm.count(a) == 1:
            cm = cm.replace(a, b)
        else:
            print('%s: pattern found %d + %d times' % (name, gl.count(a), cm.count(a)))
            bad += 1
            continue
        nm = 'cm3_mut%d' % i
        open(W + nm + '_glue.asm', 'w').write(gl.replace('SAVEBIN "cm3_', 'SAVEBIN "%s_' % nm)
                                             .replace('ASSERT shared_end + 20 <=', 'ASSERT shared_end <='))
        open(W + nm + '_cmr.asm', 'w').write(cm.replace('INCLUDE "cm3_glue.asm"', 'INCLUDE "%s_glue.asm"' % nm)
                                             .replace('SAVEBIN "cmr.bin"', 'SAVEBIN "%s_cmr.bin"' % nm))
        open(W + nm + '.asm', 'w').write('        DEFINE M2\n        DEFINE M3\n        INCLUDE "%s_cmr.asm"\n' % nm)
        assemble(nm)
        args = [sys.executable, 'm3_sim.py', 'm0_states.bin', every, '--prefix', nm, '--show', '1', '--irq', '--pace', '--tween'] + (['--only', sys.argv[3]] if len(sys.argv) > 3 else []) + (['--phase', sys.argv[4]] if len(sys.argv) > 4 else []) + (['--cursor', '20'] if name[0] in CURSOR else [])
        if name[0] == 'W':
            args = [sys.executable, 'm3b_diss.py', '250', nm]
        if name[0] == 'a':
            args = [sys.executable, 'm3b_diss.py', '250', nm, 'portc']
        if name[0] in SEQ:
            args = [sys.executable, '-I', 'm3b_seq.py', '--stop', SEQ[name[0]], '--prefix', nm]
        if name[0] == 'X':
            args = [sys.executable, 'm3b_race.py', nm]
        r = subprocess.run(args, cwd=W, capture_output=True, text=True)
        lines = [' '.join(l.split())[:150] for l in r.stdout.splitlines() if 'FAILED' in l or 'did not end' in l or 'PACE' in l or l.startswith('  state')]
        killed = bool(r.returncode)
        print('%-52s %s  %s' % (name, 'FAILS (good)' if killed else 'PASSES (BAD)', '; '.join(lines[:3]) or r.stderr[-200:]), flush=True)
        bad += not killed
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
