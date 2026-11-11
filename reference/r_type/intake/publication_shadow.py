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
out=Path('/workspace/work/r_type_publication_shadow');out.mkdir(exist_ok=True)
from irq_capture import load
state=load()
blocks,syms=assemble(str(HERE/'publication_shadow.asm'),sjasm.find())
snap=Z.Z80Snapshot(str(HERE.parent/'Rtype.z80'))
os.environ['NEXCLASH_JNEXT']='/workspace/work/jnext-bin/root/usr/bin/jnext'
jobs=[]
for mode in (1,2,3):
 folder=out/('mode%d'%mode);folder.mkdir(exist_ok=True)
 banks={i:bytearray(b) for i,b in enumerate(state['banks'])}
 # Preserve the selected original high bank for the native IRQ.
 assert bytes(banks[2][0x3e26:0x3e2b])==bytes.fromhex('dde5fde5e5')
 assert bytes(banks[2][0x3e52:0x3e55])==bytes.fromhex('f108e1')
 for offset,sym in [(0x3e26,'irq_in'),(0x3e52,'irq_out')]:
  banks[2][offset:offset+3]=b'\xc3'+Z.w16(syms[sym])
 code=bytearray(blocks['code']);code[syms['initial_mode']+1-0x2000]=min(mode,2)
 if mode==3:code[syms['tail_copy']-0x2000:syms['tail_copy']-0x2000+3]=bytes(3)
 banks.update({10:bytes.fromhex('ed915118c30020'),12:code,
  20:bytes((i*71+i//256)&255 for i in range(16384)),
  21:bytes((i*19)&255 for i in range(8192))+bytes(8192)})
 nex=folder/'publication.nex';Z.write_nex(str(nex),snap,banks)
 s=J.Script(500)
 for tag,name in [('PREP','prepare'),('READY','shadow_ready'),('PREPEND','prep_end'),('TAIL','tail_begin'),('BEGIN','pstart'),('ROW','rend'),('END','pend'),('IRQIN','irq_in'),('IRQOUT','irq_out')]:
  s.rule('on execute %d do\n  log "%s M=${mem[14336]} R=${mem[14337]} C=${CYCLE}"\nend\n'%(syms[name],tag))
 s.rule('on execute %d do\n  save_snapshot "publication.jns"\nend\n'%syms['pend'])
 s.exit_at(7)
 jobs.append((str(nex),s.text(),str(folder),40,'/workspace/scratch/cspect-next-2gb.img','/workspace/work/r_type_jnext_home'))
codes=J.run_all(jobs);print('codes',codes);assert codes==[0,0,0]
result=[]
for mode in (1,2,3):
 rows=J.unwrap([dict(tag=tag,**r) for tag,r in J.records(str(out/('mode%d'%mode)/'run.log'),['PREP','READY','PREPEND','TAIL','BEGIN','ROW','END','IRQIN','IRQOUT'])])
 for r in rows:r['M']=mode
 unique={(r['tag'],r['R']):r for r in rows if r['tag'] not in ('IRQIN','IRQOUT')};rows=list(unique.values())+[r for r in rows if r['tag'] in ('IRQIN','IRQOUT')]
 start=next(r['C'] for r in rows if r['tag']=='BEGIN')
 for r in rows:
  elapsed=r['C']-start
  deadline=(151+16*r['R'])*228*8 if r['tag']=='ROW' else None
  result.append(dict(**r,elapsed=elapsed,ms=elapsed/28000,deadline=deadline,ready=elapsed<deadline if deadline else None))
 frame=J.Frame(str(out/('mode%d'%mode)/'publication.jns'))
 expected=bytes((i*71+i//256)&255 for i in range(16384))
 assert frame.patterns[:105*128]==expected[:105*128],mode
 import zipfile
 z=zipfile.ZipFile(frame.path);ram=z.read('mem/ram.bin');live=z.read('mem/bank5-vram.bin');shadow=ram[0x40000+42*8192:0x40000+43*8192];backup=ram[0x40000+43*8192:0x40000+44*8192]
 offsets={((y&192)<<5)+((y&7)<<8)+((y&56)<<2)+x for y in range(160) for x in range(32)}
 assert all(live[a]==shadow[a] for a in offsets|set(range(0x1800,0x1a80))), 'ULA commit differs'
 tail_bad=sum(x!=y for x,y in zip(live[0x1b00:0x2000],shadow[0x1b00:0x2000]))
 if mode==3:
  assert tail_bad>0, 'negative missing-tail-copy control escaped'
  print('negative missing-tail-copy caught',tail_bad,'bytes')
  continue
 assert tail_bad==0, 'slot2 variables lost'
 assert live[0x1a80:0x1b00]==bytes(state['banks'][5][0x1a80:0x1b00]), 'HUD changed'
 assert all(live[0x2000+a]==backup[a] for a in set(range(0x1800))-offsets), 'source hole was overwritten'
 times={r['tag']:r['C'] for r in rows if r['tag'] not in ('IRQIN','IRQOUT')}
 assert any(times['READY']<r['C']<times['PREPEND'] for r in rows if r['tag']=='IRQIN'), 'IRQ-during-prep path untested'
 assert not any(times['PREP']<r['C']<times['READY'] for r in rows if r['tag']=='IRQIN'), 'IRQ raced initial clone'
 assert not any(times['TAIL']<r['C']<times['END'] for r in rows if r['tag']=='IRQIN'), 'IRQ raced publication'
 assert all(live[0x2000+a]==backup[a] for a in offsets), 'source pixels not restored'
 assert all(r['ready'] is not False for r in result if r['M']==mode), 'row deadline missed'
 print('mode',mode,'end ms',[r['ms'] for r in result if r['M']==mode and r['tag']=='END'],
  'late rows',[r['R'] for r in result if r['M']==mode and r['ready'] is False])
print('patterns, clean ULA, slot2 variables and restored source pixels match')
(out/'timing.json').write_text(json.dumps(dict(original_irq_frame=state['frame'],original_irq_T=state['T'],results=result),indent=2)+'\n')
