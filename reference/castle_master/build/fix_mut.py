W = 'C:/1NEXT/castle_master_work/'
L = open(W + 'm1_mutants.py').read().split('\n')
i = next(k for k, l in enumerate(L) if l.startswith("    'G sort"))
j = next(k for k in range(i, len(L)) if L[k] == '}')
L[i:j] = [
    "    'G sort cache: key takes b low bits from a': ('        ld a,c                          ; sort key b low',",
    "                                                  '        ld a,e                          ; sort key b low'),",
    "    'H sort cache: a swap result read as keep': ('        rra                             ; cached: bit 0 = keep',",
    "                                                 '        scf                             ; cached: bit 0 = keep'),",
]
open(W + 'm1_mutants.py', 'w').write('\n'.join(L))
L = open(W + 'm1_raster_mutants.py').read().split('\n')
i = next(k for k, l in enumerate(L) if l.startswith("    'F fill"))
j = next(k for k, l in enumerate(L) if l.startswith("    'G lowest"))
L[i:j] = [
    "    'F fill pattern row = (rows left - 1) & 3': (",
    "        T + 'call l2row\\n' + T + 'ld a,b\\n' + T + 'and 3', T + 'call l2row\\n' + T + 'ld a,b\\n' + T + 'dec a\\n' + T + 'and 3'),",
    "    'P row fill: pixels 0-1 take the values of 2-3': (",
    "        T + 'ld l,a\\n' + T + 'ex de,hl                        ; DE = pixels 2, 3',",
    "        T + 'ld l,a\\n' + T + 'ld b,h\\n' + T + 'ld c,l\\n' + T + 'ex de,hl                        ; DE = pixels 2, 3'),",
]
open(W + 'm1_raster_mutants.py', 'w').write('\n'.join(L))
import importlib, sys
sys.path.insert(0, W)
s = open(W + 'cmr.asm').read()
for m in ('m1_mutants', 'm1_raster_mutants'):
    M = importlib.import_module(m).MUT
    print(m, len(M), [k[0] for k, (a, b) in M.items() if s.count(a) != 1])
