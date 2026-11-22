"""Run ddma_probe.nex in JNext headless; print the NR 0x7F results. Usage: python ddma_jnext.py"""
import os, sys, re
sys.path.insert(0, r'C:/1NEXT/nexclash')
os.environ['NEXCLASH_JNEXT'] = r'C:/1NEXT/jnext-1.3.0-windows-x64/jnext.exe'
from nexclash import jnext
W = 'C:/1NEXT/castle_master_work/'
script = 'on nextreg 127 do\n  log "RES V=${VALUE} F=${FRAME}"\nend\n'
p = jnext.launch(W + 'ddma_probe.nex', script, W + 'ddma_jnext', 300, jnext.card(r'C:/1NEXT/cspect-next-2gb.img'))
print('exit', p.wait(timeout=600))
log = open(W + 'ddma_jnext/run.log', errors='replace').read()
print(re.findall(r'RES V=\d+', log), len(log))
print([l for l in log.splitlines() if 'rror' in l or 'DMA' in l][:8])
