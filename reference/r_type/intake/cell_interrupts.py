"""Native quiet IRQ injected at every cell-hook instruction, all four flips.

Uses real helper input and crosses its legal original continuations; long ISR/R
consumer behavior is covered separately. No pace or recording coverage claim.
"""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from cell_check import END,FLIP
from interrupt_boundaries import Logged,interrupt
from irq_equivalence import Memory,Model
from asm2profile import assemble,sjasm
from nexclash import simpool
from nexclash.dizzy6 import _rw_simulator

def run():
    blocks,s=assemble(str(HERE/'publication_cell.asm'),sjasm.find())
    for state in json.loads(Path('/workspace/work/r_type_plot_states.json').read_text()):
        m=Memory(state,blocks['code']);base=simpool.machine(_rw_simulator(),m,state['registers'],slot='cell-find')
        sp=base.registers[12];ret=m[sp]|m[sp+1]<<8
        while base.registers[24] not in (ret,0x8EA2):base.opcodes[m[base.registers[24]]]()
        if base.registers[24]==0x8EA2:break
    results=[]
    for caller,end in END.items():
        mem=Logged(state,blocks['code']);mem.pages={p:b[:]for p,b in m.pages.items()};mem.pages[50]=bytearray(8192);mem.logging=False
        regs=base.registers[:];regs[26]=1;sp=regs[12];mem[sp]=caller&255;mem[sp+1]=caller>>8
        if FLIP[caller]&1:regs[2]=0x5D
        for pc,label in ((0x8EA2,'cell_entry'),(0xBE26,'irq_in'),(0xBE52,'irq_out')):
            for i,v in enumerate(b'\xc3'+s[label].to_bytes(2,'little')):mem[pc+i]=v
        sim=simpool.machine(_rw_simulator(),mem,regs,slot='cell-boundary');model=Model(sim,speed=0)
        checked=0;sites=set();previous=0;low=0x3D00
        for n in range(10000):
            pc=sim.registers[24]
            if pc==end:break
            a,l,e=interrupt(sim,model,s,previous=previous)
            assert not e,(hex(caller),hex(pc),e)
            if a:
                checked+=1;sites.add(pc)
                if 0x2000<=sim.registers[12]<0x4000:low=min(low,l)
            previous=pc;sim.opcodes[mem[pc]]()
        else:raise RuntimeError('cell hook did not return')
        results.append(dict(flip=FLIP[caller],instructions=n,irq_injections=checked,distinct_boundaries=len(sites),min_private_sp=hex(low)))
    Path('/workspace/work/r_type_cell_interrupts.json').write_text(json.dumps(results,indent=2)+'\n');print(results)
if __name__=='__main__':run()
