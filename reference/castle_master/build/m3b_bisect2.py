"""ov_cap variants: python m3b_bisect2.py STATE"""
import subprocess, sys
from m2_lib import W, assemble
VAR = {'ov_cap = ret': ('ov_cap: ld a,(VP+10)\n', 'ov_cap: ret\n        ld a,(VP+10)\n'),
       'no ptick/prest': ('        call nz,ptick\n        call ov_in\n        ld hl,0x5CBC+G\n        ld de,ov_s\n', '        call ov_in\n        ld hl,0x5CBC+G\n        ld de,ov_s\n'),
       'no ldir': ('        ld bc,2688\n        ldir\n        ld a,(27405+G)', '        ld a,(27405+G)'),
       'no marker': ('        ld a,(27405+G)                  ; the raster', '        jr 1F\n        ld a,(27405+G)                  ; the raster')}
src = {'cmr': open(W + 'cmr.asm').read(), 'glue': open(W + 'cm3_glue.asm').read()}
for i, (name, (a, b)) in enumerate(VAR.items()):
    if len(sys.argv) > 2 and str(i) not in sys.argv[2]: continue
    assert src['glue'].count(a) == 1, name
    nm = 'cm3_bis%d' % i
    open(W + nm + '_glue.asm', 'w').write(src['glue'].replace(a, b).replace('SAVEBIN "cm3_', 'SAVEBIN "%s_' % nm))
    open(W + nm + '_cmr.asm', 'w').write(src['cmr'].replace('INCLUDE "cm3_glue.asm"', 'INCLUDE "%s_glue.asm"' % nm)
                                         .replace('SAVEBIN "cmr.bin"', 'SAVEBIN "%s_cmr.bin"' % nm))
    open(W + nm + '.asm', 'w').write('        DEFINE M2\n        DEFINE M3\n        INCLUDE "%s_cmr.asm"\n' % nm)
    assemble(nm)
    r = subprocess.run([sys.executable, 'm3_sim.py', 'm0_states.bin', '1', '--prefix', nm, '--irq', '--tween', '--only', sys.argv[1]], cwd=W, capture_output=True, text=True)
    print(name, [l.strip()[:120] for l in r.stdout.splitlines() if 'state' in l or 'OK' in l or 'FAIL' in l], r.stderr[-300:])
