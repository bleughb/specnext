"""Inject a native quiet IRQ after every interruptible instruction in a complete hook.

Actual ISR prologue/epilogue and wrapper run, with the game's five optional tasks
masked in the test fixture. Long/native task behavior is proved separately by
irq_equivalence.py and the retained full ISR footprint. Roll back test IRQ writes
and time before continuing, so every boundary belongs to the same genuine path.
"""
import collections,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]/'nexclash';sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from asm2profile import assemble,sjasm
from nexclash import simpool
from nexclash.dizzy6 import _rw_simulator
from irq_equivalence import Memory,Model

class Logged(Memory):
    def __setitem__(self,a,v):
        page=self.mmu[a>>13]
        if page!=255 and getattr(self,'logging',False):self.log.append((page,a&8191,self.pages[page][a&8191]))
        super().__setitem__(a,v)

def interrupt(sim,model,s,negative=False,previous=0):
    mem=sim.memory;before=sim.registers[:];mapping=mem.mmu[:]
    clock=(model.real,model.t_last,model.sel,model.nr.copy(),len(model.events),model.c.copy())
    mem.log=[];mem.logging=True
    for i in range(5):mem[0xBE62+5*i]=0
    accepted=sim.accept_interrupt(sim.registers,mem,previous)
    low=sim.registers[12]
    if accepted:
        for _ in range(10000):
            pc=sim.registers[24]
            if pc==before[24] and sim.registers[12]==before[12]:break
            if negative and pc==s['irq_out']:mem[s['irq_mmu0']]=0
            sim.opcodes[mem[pc]]();low=min(low,sim.registers[12])
        else:raise RuntimeError('quiet native IRQ did not return')
    cmp=list(range(15))+list(range(16,25))+[26,27,28]
    bad=[i for i in cmp if before[i]!=sim.registers[i]]
    errors=[]
    if bad:errors.append(('registers',bad))
    if mem.mmu!=mapping:errors.append(('MMU',mapping,mem.mmu[:]))
    if model.sel!=clock[2]:errors.append(('selector',clock[2],model.sel))
    if model.nr[7]&3!=clock[3][7]&3:errors.append(('speed',clock[3][7],model.nr[7]))
    if 0x2000<=before[12]<0x4000 and low<0x3840:errors.append(('stack overlaps hook state',hex(low)))
    mem.logging=False
    for page,off,old in reversed(mem.log):mem.pages[page][off]=old
    mem.mmu[:]=mapping;sim.registers[:]=before
    model.real,model.t_last,model.sel,model.nr=clock[:4];del model.events[clock[4]:];model.c=clock[5]
    return accepted,low,errors

def run():
    state=json.loads(Path('/workspace/work/r_type_peak_state.json').read_text())
    blocks,s=assemble(str(HERE/'publication_tilemap.asm'),sjasm.find())
    mem=Logged(state,blocks['code']);mem.logging=False
    for p in (40,41,42,43,44):mem.pages[p]=bytearray(8192)
    mem.pages[48]=bytearray(state['banks'][7][:8192]);mem.pages[49]=bytearray(state['banks'][7][8192:])
    regs=state['registers'][:];regs[24]=0x8842;regs[26]=1;regs[12]=0xFFF0
    mem[0xFFF0]=0;mem[0xFFF1]=0x1F;mem[s['hlib_dma_cap']]=1
    for a,label in [(0x8842,'hook_entry'),(0xBE26,'irq_in'),(0xBE52,'irq_out')]:
        for i,v in enumerate(b'\xc3'+s[label].to_bytes(2,'little')):mem[a+i]=v
    sim=simpool.machine(_rw_simulator(),mem,regs,slot='irq-boundaries');model=Model(sim,speed=0,t_line=228,lines=311)
    checked=0;sites=collections.Counter();minimum=0x3D00;negative_done=False;previous=0
    for n in range(1000000):
        pc=sim.registers[24]
        if pc==0x1F00:break
        if sim.registers[26]:
            accepted,low,errors=interrupt(sim,model,s,previous=previous)
            assert not errors,(hex(pc),errors)
            if accepted:
                checked+=1;sites[hex(pc)]+=1
                if 0x2000<=sim.registers[12]<0x4000:minimum=min(minimum,low)
                if not negative_done:
                    a,l,e=interrupt(sim,model,s,True,previous)
                    assert a and any(x[0]=='MMU'for x in e),'wrong IRQ mapping escaped'
                    negative_done=True
        previous=pc;sim.opcodes[mem[pc]]()
        if n and n%10000==0:print('instructions',n,'IRQ checks',checked,flush=True)
    else:raise RuntimeError('hook did not return')
    assert checked>1000 and negative_done
    result=dict(scope=__doc__,instruction_instances=n,irq_injections=checked,distinct_boundaries=len(sites),minimum_private_sp=hex(minimum),negative_caught=negative_done,site_counts=dict(sites))
    Path('/workspace/work/r_type_tilemap_peak/interrupt-boundaries.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items()if k!='site_counts'},flush=True)
if __name__=='__main__':run()
