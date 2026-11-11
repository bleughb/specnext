"""Publication deadline probe using the game's observed long native audio IRQ.

Synthetic graphics; no game integration. Capture is an original RZX state before
BE23 in frame3620 (maximum observed ISR cost in the first4000 frames). No timing
or pixel-equivalence claim about the eventual whole hook.
"""
import json, os, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]/'nexclash'
sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from asm2profile import assemble,sjasm
from nexclash import jnext as J,z80tonex as Z
out=Path('/workspace/work/r_type_publication_irq');out.mkdir(exist_ok=True)
from irq_capture import load
state=load()
blocks,syms=assemble(str(HERE/'publication_irq.asm'),sjasm.find())
snap=Z.Z80Snapshot(str(HERE.parent/'Rtype.z80'))
os.environ['NEXCLASH_JNEXT']='/workspace/work/jnext-bin/root/usr/bin/jnext'
jobs=[]
for mode in (0,1,2):
 folder=out/('mode%d'%mode);folder.mkdir(exist_ok=True)
 banks={i:bytearray(b) for i,b in enumerate(state['banks'])}
 # Preserve the selected original high bank for the native IRQ.
 assert bytes(banks[2][0x3e26:0x3e2b])==bytes.fromhex('dde5fde5e5')
 assert bytes(banks[2][0x3e52:0x3e55])==bytes.fromhex('f108e1')
 for offset,sym in [(0x3e26,'irq_in'),(0x3e52,'irq_out')]:
  banks[2][offset:offset+3]=b'\xc3'+Z.w16(syms[sym])
 code=bytearray(blocks['code']);code[syms['initial_mode']+1-0x2000]=mode
 banks.update({10:bytes.fromhex('ed915118c30020'),12:code,
  20:bytes((i*71+i//256)&255 for i in range(16384)),
  21:bytes((i*19)&255 for i in range(8192))+bytes(8192)})
 nex=folder/'publication.nex';Z.write_nex(str(nex),snap,banks)
 s=J.Script(500)
 for tag,name in [('BEGIN','pstart'),('ROW','rend'),('END','pend'),('IRQIN','irq_in'),('IRQOUT','irq_out')]:
  s.rule('on execute %d do\n  log "%s M=${mem[14336]} R=${mem[14337]} C=${CYCLE}"\nend\n'%(syms[name],tag))
 s.at(5,'  save_snapshot "publication.jns"\n')
 s.exit_at(7)
 jobs.append((str(nex),s.text(),str(folder),40,'/workspace/scratch/cspect-next-2gb.img','/workspace/work/r_type_jnext_home'))
codes=J.run_all(jobs);print('codes',codes);assert codes==[0,0,0]
result=[]
for mode in (0,1,2):
 rows=J.unwrap([dict(tag=tag,**r) for tag,r in J.records(str(out/('mode%d'%mode)/'run.log'),['BEGIN','ROW','END','IRQIN','IRQOUT'])])
 unique={(r['tag'],r['R']):r for r in rows};rows=list(unique.values())
 start=next(r['C'] for r in rows if r['tag']=='BEGIN')
 for r in rows:
  elapsed=r['C']-start
  deadline=(151+16*r['R'])*228*8 if r['tag']=='ROW' else None
  result.append(dict(**r,elapsed=elapsed,ms=elapsed/28000,deadline=deadline,ready=elapsed<deadline if deadline else None))
 frame=J.Frame(str(out/('mode%d'%mode)/'publication.jns'))
 expected=bytes((i*71+i//256)&255 for i in range(16384))
 assert frame.patterns[:105*128]==expected[:105*128],mode
 print('mode',mode,'end ms',[r['ms'] for r in result if r['M']==mode and r['tag']=='END'],
  'late rows',[r['R'] for r in result if r['M']==mode and r['ready'] is False])
(out/'timing.json').write_text(json.dumps(dict(original_irq_frame=state['frame'],original_irq_T=state['T'],results=result),indent=2)+'\n')
