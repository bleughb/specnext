"""R-Type synthetic publication timing; excludes game preparation and interrupts.

Builds with the repository's pinned assembler; compares CPU, ordinary DMA and
capability-gated blitter preference. 105 patterns, 160 ULA lines, 640 attrs.
"""
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3] / 'nexclash'
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from asm2profile import assemble, sjasm
from nexclash import jnext as J, z80tonex as Z

out = Path('/workspace/work/r_type_publication');out.mkdir(exist_ok=True)
blocks, syms = assemble(str(HERE / 'publication.asm'), sjasm.find())
snap = Z.Z80Snapshot(str(HERE.parent / 'Rtype.z80'))
banks = {2: blocks['code'], 5: bytes(16384), 10: bytes([0xC3,0,0x80]),
         20: bytes((i * 71 + i // 256) & 255 for i in range(16384)),
         21: bytes((i * 19) & 255 for i in range(8192)) + bytes(8192)}
os.environ['NEXCLASH_JNEXT']='/workspace/work/jnext-bin/root/usr/bin/jnext'
jobs=[]
for mode in (0,1,2):
    folder=out/('mode%d'%mode);folder.mkdir(exist_ok=True)
    code=bytearray(blocks['code']);code[syms['initial_mode']+1-0x8000]=mode
    banks[2]=code
    nex=folder/'publication.nex';Z.write_nex(str(nex),snap,banks)
    s=J.Script(500)
    for tag,name in [('BEGIN','pstart'),('ROW','rend'),('END','pend')]:
        s.rule('on execute %d do\n  log "%s M=${mem[45312]} R=${mem[45313]} C=${CYCLE}"\nend\n'%(syms[name],tag))
    s.at(5,'  screenshot "publication.png"\n  save_snapshot "publication.jns"\n')
    s.exit_at(7)
    jobs.append((str(nex),s.text(),str(folder),40,'/workspace/scratch/cspect-next-2gb.img',
                 '/workspace/work/r_type_jnext_home'))
codes=J.run_all(jobs);print('exit codes',codes);assert codes==[0,0,0]
rows=[]
for mode in (0,1,2):
    rows+=J.unwrap([dict(tag=tag,**r) for tag,r in J.records(str(out/('mode%d'%mode)/'run.log'),['BEGIN','ROW','END'])])
# JNext reports an execute trigger repeatedly during a synchronous DMA stall.
# Retain the latest observation, conservatively, for each mode/row marker.
unique={}
for r in rows:unique[r['M'],r['tag'],r['R']]=r
rows=list(unique.values())
begin={};result=[]
for r in rows:
    if r['tag']=='BEGIN': begin[r['M']]=r['C']
    else:
        elapsed=r['C']-begin[r['M']]
        deadline=(151+16*r['R'])*228*8 if r['tag']=='ROW' else None
        result.append(dict(**r,elapsed=elapsed,ms=elapsed/28000,deadline=deadline,
                           ready=elapsed<deadline if deadline else None))
(out/'timing.json').write_text(json.dumps(result,indent=2)+'\n')
for mode in (0,1,2):
    a=[r for r in result if r['M']==mode]
    print('mode',mode,'ms',[r['ms'] for r in a if r['tag']=='END'],
          'late rows',sorted({r['R'] for r in a if r['ready'] is False}))
expected=bytes((i*71+i//256)&255 for i in range(16384))
offsets={((y&0xC0)<<5)+((y&7)<<8)+((y&0x38)<<2)+x for y in range(160) for x in range(32)}
offsets.update(range(0x1800,0x1800+640))
for mode in (0,1,2):
    frame=J.Frame(str(out/('mode%d'%mode)/'publication.jns'))
    assert frame.patterns[:105*128]==expected[:105*128], ('sprite upload mismatch',mode)
    assert all(frame.ula[i]==(i*19)&255 for i in offsets), ('ULA copy mismatch',mode)
    assert all(r['ready'] is not False for r in result if r['M']==mode), ('row deadline missed',mode)
print('all3 routes: pattern/ULA bytes match and row deadlines pass; interrupts excluded')
