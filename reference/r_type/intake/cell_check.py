"""Actual successful cell helper: all four flips, effective ink and provenance.

No natural-pace claim; reports complete invocation CPU costs separately. Source
states come from the eight captured real plotter entries, without another scan.
"""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]/'nexclash';sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from asm2profile import assemble,sjasm
from nexclash import simpool
from nexclash.dizzy6 import _rw_simulator
from irq_equivalence import Memory,Model
from register_bridge import until
END={0x8D2A:0x8D4C,0x8D91:0x8DBA,0x8DFD:0x8E10,0x8E57:0x8E6C}
FLIP={0x8D2A:0,0x8D91:1,0x8DFD:2,0x8E57:3}

def run():
    blocks,s=assemble(str(HERE/'publication_cell.asm'),sjasm.find());results=[]
    for state in json.loads(Path('/workspace/work/r_type_plot_states.json').read_text()):
        m=Memory(state,blocks['code']);base=simpool.machine(_rw_simulator(),m,state['registers'],slot='cell-find')
        sp=base.registers[12];ret=m[sp]|m[sp+1]<<8
        while base.registers[24] not in (ret,0x8EA2):base.opcodes[m[base.registers[24]]]()
        if base.registers[24]==ret:continue
        regs=base.registers[:];sp=regs[12];caller=m[sp]|m[sp+1]<<8
        source=regs[6]*256+regs[7];owner=regs[4]*256+regs[5];index=owner-0x7E00
        # Also cross each real helper input with all four legal CALL continuations.
        for caller in END:
            for override in (0,7):
                for r in (0,127,128,255):
                    for speed in (0,):
                        machines=[]
                        for patched in (False,True):
                            mem=Memory(state,blocks['code']);mem.pages={p:b[:]for p,b in m.pages.items()};mem.pages[50]=bytearray(8192)
                            mem[0x8EB1]=override;mem[sp]=caller&255;mem[sp+1]=caller>>8
                            rr=regs[:];rr[15]=r;rr[26]=1
                            if FLIP[caller]&1:rr[2]=0x5D
                            if patched:
                                for i,v in enumerate(b'\xc3'+s['cell_entry'].to_bytes(2,'little')):mem[0x8EA2+i]=v
                            sim=simpool.machine(_rw_simulator(),mem,rr,slot='cell-p'if patched else'cell-o');model=Model(sim,speed=speed,t_line=228,lines=311)
                            until(sim,END[caller],100000);machines.append((sim,model))
                        (o,om),(p,pm)=machines
                        bad=[i for i in list(range(25))+[26,27,28]if o.registers[i]!=p.registers[i]]
                        assert not bad,(hex(caller),override,r,speed,[(i,o.registers[i],p.registers[i])for i in bad])
                        live=[];dead=[]
                        for page in range(16):
                            for j,(a,b)in enumerate(zip(o.memory.pages[page],p.memory.pages[page])):
                                if a==b:continue
                                v=next((i*8192+j for i,x in enumerate(m.mmu)if x==page),None)
                                if v is not None and 0x8EA2<=v<0x8EA5:continue
                                if v is not None and sp-64<=v<sp+2:dead.append(v);continue
                                live.append((page,j,a,b))
                        assert not live,(hex(caller),live[:10])
                        want=source.to_bytes(2,'little')+bytes([FLIP[caller],o.memory[owner-0x600],o.memory[owner],o.memory[0x719C]])
                        assert bytes(p.memory.pages[50][index*6:index*6+6])==want,('metadata',hex(caller),want)
                        assert p.memory.mmu==m.mmu
                        credit=int.from_bytes(p.memory[ s['cell_credit']:s['cell_credit']+3 ],'little')
                        assert credit==int((om.now()-pm.now())*8),(hex(caller),credit,om.now()-pm.now())
                        results.append(dict(caller=hex(caller),flip=FLIP[caller],override=override,R=r,speed=speed,
                            original_T=om.now(),hook_T=pm.now(),saved_T=om.now()-pm.now(),dead_stack_bytes=len(dead)))
    print('covered flips', sorted(set(x['flip']for x in results)), flush=True)
    assert len(set(x['flip']for x in results))==4
    # Exact conversion retains the fractional scanline credit across updates.
    for value in (0,1,113,114,115,65535,65536,1000000,114*65536-1):
        mm=Memory(state,blocks['code']);rr=regs[:];rr[24]=s['cell_budget'];rr[12]=0x3C00
        mm[0x3C00]=0;mm[0x3C01]=0x1F
        for i,v in enumerate(value.to_bytes(3,'little')):mm[s['cell_credit']+i]=v
        sim=simpool.machine(_rw_simulator(),mm,rr,slot='cell-budget');model=Model(sim,speed=3)
        until(sim,0x1F00)
        q=mm[s['cell_lines']]|mm[s['cell_lines']+1]<<8
        rem=int.from_bytes(mm[s['cell_credit']:s['cell_credit']+3],'little')
        assert (q,rem)==divmod(value,114),(value,q,rem)
    Path('/workspace/work/r_type_cell_check.json').write_text(json.dumps(results,indent=2)+'\n')
    print(len(results),'cell cases PASS: registers/R/live RAM, exact source/flip/ink/owner/level metadata')
    for c in results[::8]:print(c)
if __name__=='__main__':run()
