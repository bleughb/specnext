"""build cm3 variants with one M3b call removed and run one state: python m3b_bisect.py STATE"""
import subprocess, sys
from m2_lib import W, assemble
T = '        '
VAR = {'no ov_capw': (T + 'call ov_capw                    ; ov_s: the buffer as the raster left it\n', ''),
       'no ov_scan': (T + 'call ov_scan                    ; what the copy put over the raster (its time is the final view\'s)\n', ''),
       'no ov_flip': ('3:      call ov_flip                    ; the overlay sprites with the new view\n' + T + 'call flip\n', '3:      call flip\n'),
       'no cursor': (T + 'call ov_cur\n', '')}
src = {'cmr': open(W + 'cmr.asm').read(), 'glue': open(W + 'cm3_glue.asm').read()}
for i, (name, (a, b)) in enumerate(VAR.items()):
    assert src['glue'].count(a) == 1, name
    nm = 'cm3_bis%d' % i
    open(W + nm + '_glue.asm', 'w').write(src['glue'].replace(a, b).replace('SAVEBIN "cm3_', 'SAVEBIN "%s_' % nm))
    open(W + nm + '_cmr.asm', 'w').write(src['cmr'].replace('INCLUDE "cm3_glue.asm"', 'INCLUDE "%s_glue.asm"' % nm)
                                         .replace('SAVEBIN "cmr.bin"', 'SAVEBIN "%s_cmr.bin"' % nm))
    open(W + nm + '.asm', 'w').write('        DEFINE M2\n        DEFINE M3\n        INCLUDE "%s_cmr.asm"\n' % nm)
    assemble(nm)
    r = subprocess.run([sys.executable, 'm3_sim.py', 'm0_states.bin', '1', '--prefix', nm, '--irq', '--tween', '--only', sys.argv[1]], cwd=W, capture_output=True, text=True)
    print(name, [l.strip()[:120] for l in r.stdout.splitlines() if 'state' in l or 'OK' in l or 'FAIL' in l])
