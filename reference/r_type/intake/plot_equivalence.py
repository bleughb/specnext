"""Whole unchanged plotter calls: real entry states, all outputs/R and game RAM.

Instruction timing is diagnostic; natural JNext pace is the acceptance gate.
Tests both IFF states and all R rollover/high-bit seeds. Dead caller stack writes
are reported separately, rather than exempting an entire memory region.
"""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]/'nexclash'
sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from asm2profile import assemble,sjasm
from nexclash import simpool
from nexclash.dizzy6 import _rw_simulator
from irq_equivalence import Memory,Model
from register_bridge import until
from publication_integrated import patch_bytes

def run():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--cell',action='store_true');args=ap.parse_args()
    blocks,s=assemble(str(HERE/('publication_cell.asm' if args.cell else 'publication_fastplots.asm')),sjasm.find())
    cases=[]
    for state in json.loads(Path('/workspace/work/r_type_plot_states.json').read_text()):
        for r in (0,127,128,255):
            for iff in (0,1):
                machines=[]
                for patched in (False,True):
                    mem=Memory(state,blocks['code']);mem.pages[50]=bytearray(8192);regs=state['registers'][:]
                    regs[15]=r;regs[26]=iff;sp=regs[12];ret=mem[sp]|mem[sp+1]<<8
                    if patched:
                        pc=regs[24]
                        for i,v in enumerate(patch_bytes(pc,'text_%04x'%pc,s)):mem[pc+i]=v
                        if args.cell:
                            for i,v in enumerate(patch_bytes(0x8EA2,'cell_entry',s)):mem[0x8EA2+i]=v
                    sim=simpool.machine(_rw_simulator(),mem,regs,slot='plot-p'if patched else'plot-o')
                    model=Model(sim,speed=0,t_line=228,lines=311,line=100)
                    until(sim,ret,1000000);machines.append((sim,model))
                (o,om),(p,pm)=machines
                bad=[i for i in list(range(25))+[26,27,28]if o.registers[i]!=p.registers[i]]
                assert not bad,(hex(state['pc']),r,iff,[(i,o.registers[i],p.registers[i])for i in bad])
                md=[]
                for page in range(16):
                    for j,(a,b)in enumerate(zip(o.memory.pages[page],p.memory.pages[page])):
                        if a!=b:md.append((page,j,a,b))
                # Hook patch bytes and overwritten, popped stack words are the only differences.
                live=[];dead=[]
                for page,j,a,b in md:
                    virtual=next((i*8192+j for i,v in enumerate(o.memory.mmu)if v==page),None)
                    if virtual is not None and state['pc']<=virtual<state['pc']+3:continue
                    if args.cell and virtual is not None and 0x8EA2<=virtual<0x8EA5:continue
                    if virtual is not None and sp-64<=virtual<sp+2:dead.append(virtual);continue
                    live.append((page,j,a,b))
                assert not live,(hex(state['pc']),r,iff,live[:20])
                cases.append(dict(pc=hex(state['pc']),frame=state['frame'],R=r,IFF=iff,
                    original_T=om.now()-22800,hook_T=pm.now()-22800,
                    credit=int.from_bytes(p.memory[s['cell_credit' if args.cell else 'fast_credit']:s['cell_credit' if args.cell else 'fast_credit']+(3 if args.cell else 2)],'little'),
                    dead_stack_bytes=len(dead)))
    out=Path('/workspace/work/r_type_cell_plot_equivalence.json' if args.cell else '/workspace/work/r_type_plot_equivalence.json');out.write_text(json.dumps(cases,indent=2)+'\n')
    print(len(cases),'whole plotter cases PASS; all registers/R/live game bytes')
    for c in cases[::8]:print(c)
if __name__=='__main__':run()
