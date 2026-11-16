"""Functional relocation proof for the original 8F21 bank reader.

Normal banks execute the original OUT/read. Physical bank7 is poisoned to model
published tile RAM; logical bank7 reads must come from its immutable bank24 copy.
"""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]/'nexclash';sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from asm2profile import assemble,sjasm
from nexclash import simpool
from nexclash.dizzy6 import _rw_simulator
from irq_equivalence import Memory,Model
from irq_capture import load
from register_bridge import until


def run():
    state=load();blocks,s=assemble(str(HERE/'publication_tilemap.asm'),sjasm.find());rows=[]
    for bank in (1,3,4,6,7):
        for addr in (0xC000,0xDD01,0xE000,0xFFFF):
            for r0 in (0,127,128,255):
                sims=[]
                for patched in (False,True):
                    mem=Memory(state,blocks['code'])
                    mem.pages[48]=bytearray(state['banks'][7][:8192]);mem.pages[49]=bytearray(state['banks'][7][8192:])
                    if patched:mem.pages[14]=bytearray([0xCC])*8192;mem.pages[15]=bytearray([0x55])*8192
                    regs=state['registers'][:];regs[24]=0x8F21;regs[15]=r0;regs[0]=16+bank;regs[1]=0xD5
                    regs[2:4]=[0x7F,0xFD];regs[6:8]=[addr>>8,addr&255];regs[12]=0x3C00
                    if patched:
                        for i,v in enumerate(b'\xc3'+s['bank_read'].to_bytes(2,'little')):mem[0x8F21+i]=v
                    sim=simpool.machine(_rw_simulator(),mem,regs,slot='bank-p'if patched else'bank-o');model=Model(sim,speed=0)
                    until(sim,0x8F24);sims.append(sim)
                cmp=list(range(25))+[26,27,28]
                bad=[i for i in cmp if sims[0].registers[i]!=sims[1].registers[i]]
                assert not bad,(bank,hex(addr),r0,bad)
                assert sims[1].memory.mmu[0]==255
                rows.append(dict(bank=bank,address=hex(addr),R=r0))
    Path('/workspace/work/r_type_tilemap_peak/bank-check.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(len(rows),'bank read relocation cases PASS incl flags and R')
if __name__=='__main__':run()
