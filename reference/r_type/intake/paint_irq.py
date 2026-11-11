"""Supplied-R native IRQ equivalence outside/inside paint slot2 aliasing.

All retained native IRQ fixtures and every L2 target page; native live/shadow
write destinations are compared, not merely restored page numbers.
"""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from irq_equivalence import execute,fixtures
from asm2profile import assemble,sjasm

def diffs(o,p,slot):
    md=[]
    for page in range(16):
        target=42 if page==10 and slot!=10 else page
        for off,(a,b)in enumerate(zip(o.memory.pages[page],p.memory.pages[target])):
            if page==5 and off in set(range(0x1E26,0x1E29))|set(range(0x1E52,0x1E55)):continue
            if a!=b:md.append((page,off))
    return md

def run():
    blocks,s=assemble(str(HERE/'publication_paint.asm'),sjasm.find());results=[];negative=False
    for state in fixtures():
        o,values=execute(state,blocks['code'],s)
        if not values:continue
        for slot in (10,42,*range(64,76)):
            p,_=execute(state,blocks['code'],s,True,values,slot2=slot)
            rd=[i for i in list(range(15))+list(range(16,25))+[26,27,28]if o.registers[i]!=p.registers[i]]
            md=diffs(o,p,slot);assert not md and not rd,(state['frame'],slot,rd,md[:10])
            assert p.memory.mmu==[46,24,slot,11,4,5,40,1],p.memory.mmu
            assert all(b==0xA5 for page in range(64,76)for b in p.memory.pages[page]),'native IRQ wrote L2'
            if slot==10:assert p.memory.pages[42]==bytearray(state['banks'][5][:8192]),'outside IRQ changed shadow'
            results.append(dict(frame=state['frame'],slot2=slot,reads=len(values)))
            if slot==10 and not negative:
                broken=bytearray(blocks['code']);start=s['irq_in']-0x2000
                k=broken.index(bytes.fromhex('fe4038'),start);broken[k+1]=0
                q,_=execute(state,bytes(broken),s,True,values,slot2=10)
                # Native task may write only attributes in slot3 in this state;
                # keep looking until a real slot2 write distinguishes destinations.
                if diffs(o,q,10):negative=True
    assert negative,'wrong forced-shadow guard escaped'
    result=dict(cases=results,negative_caught=negative)
    Path('/workspace/work/r_type_paint_irq.json').write_text(json.dumps(result,indent=2)+'\n');print(len(results),'native IRQ mappings PASS, forced-shadow negative caught')
if __name__=='__main__':run()
