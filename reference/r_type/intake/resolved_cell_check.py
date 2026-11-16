"""Original cell versus resolved-colour producer: ABI/R/RAM and exact CPU credit.

Crosses every resolver outcome with four row variants and Force override. Timing
constants contain CPU costs only, never game graphics. Calibration precedes the
independent assembled run with real signed counter values.
"""
import argparse,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]/'nexclash';sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from asm2profile import assemble,sjasm
from nexclash import simpool
from nexclash.dizzy6 import _rw_simulator
from irq_equivalence import Memory,Model
from register_bridge import until
from cell_check import END,FLIP

def run():
    ap=argparse.ArgumentParser();ap.add_argument('--calibrate',action='store_true');args=ap.parse_args()
    blocks,s=assemble(str(HERE/'publication_resolved.asm'),sjasm.find())
    for state in json.loads(Path('/workspace/work/r_type_plot_states.json').read_text()):
        m=Memory(state,blocks['code']);base=simpool.machine(_rw_simulator(),m,state['registers'],slot='res-find')
        sp=base.registers[12];ret=m[sp]|m[sp+1]<<8
        while base.registers[24]not in(ret,0x8EA2):base.opcodes[m[base.registers[24]]]()
        if base.registers[24]==0x8EA2:break
    regs=base.registers[:];sp=regs[12];src=regs[6]*256+regs[7];owner=regs[4]*256+regs[5];index=owner-0x7E00
    sourcebits=bytes(m[src+1+i]for i in range(8));costs={};results=[]
    for case in range(10):
        for caller,end in END.items():
            for force in (0,7):
                for r in ((0,)if args.calibrate else(0,127,128,255)):
                    machines=[]
                    for patched in(False,True):
                        mem=Memory(state,blocks['code']);mem.pages={p:b[:]for p,b in m.pages.items()};mem.pages[50]=bytearray(8192);mem.pages[56]=bytearray(8192)
                        mem.pages[56][:len(blocks['resolve'])]=blocks['resolve']
                        for page in range(64,119):mem.pages[page]=bytearray(8192)
                        rr=regs[:];rr[15]=r;rr[26]=1
                        if FLIP[caller]&1:rr[2]=0x5D
                        mem[sp]=caller&255;mem[sp+1]=caller>>8;mem[0x8EB1]=force;mem[0x719C]=49;mem[0x7A9C]=0x88
                        if case==2:mem[0x7A9C]=0xDC
                        if case==3:mem[s['text_owners']+mem[0x7A9C]]=1
                        if case==4:mem[0x719C]=0
                        a=force or mem[src];ink=((a&7)+(8 if a&64 else 0))or 8
                        if case!=5:
                            page=64+4+(src-0xA000)//4096;off=((src-0xA000)&4095)*2
                            mem.pages[page][off:off+2]=(1).to_bytes(2,'little')
                        raw=bytearray(sourcebits)
                        if case==8:raw[4]^=1
                        if case in(1,7):data=raw+bytes([128])+b''.join((0x8001 if i==ink and case==1 else 65535).to_bytes(2,'little')for i in range(16))
                        else:data=raw+bytes([ink if case!=6 else 1+(ink%15)])+(65535 if case==9 else 0x8001).to_bytes(2,'little')
                        mem.pages[104][4:4+len(data)]=data
                        if patched:
                            for i,v in enumerate(b'\xc3'+s['cell_entry'].to_bytes(2,'little')):mem[0x8EA2+i]=v
                        sim=simpool.machine(_rw_simulator(),mem,rr,slot='res-cell-p'if patched else'res-cell-o');model=Model(sim,speed=0)
                        until(sim,end,100000);machines.append((sim,model))
                    (o,om),(p,pm)=machines
                    rd=[i for i in list(range(25))+[26,27,28]if o.registers[i]!=p.registers[i]]
                    assert not rd,(case,hex(caller),force,r,[(i,o.registers[i],p.registers[i])for i in rd])
                    assert p.memory[s['cell_case']]==case,(case,p.memory[s['cell_case']])
                    assert p.memory.mmu==m.mmu,p.memory.mmu
                    md=[];dead=[]
                    for page in range(16):
                        for j,(a,b)in enumerate(zip(o.memory.pages[page],p.memory.pages[page])):
                            if a==b:continue
                            v=next((i*8192+j for i,x in enumerate(m.mmu)if x==page),None)
                            if v is not None and 0x8EA2<=v<0x8EA5:continue
                            if v is not None and sp-64<=v<sp+2:dead.append(v);continue
                            md.append((page,j,a,b))
                    assert not md,(case,hex(caller),md[:8])
                    group=0x8001 if case in(0,1)else 65535
                    want=src.to_bytes(2,'little')+group.to_bytes(2,'little')+bytes([FLIP[caller],ink if case not in(2,3)else 0,o.memory[0x7A9C],o.memory[0x719C]])
                    assert bytes(p.memory.pages[50][index*8:index*8+8])==want,(case,'descriptor')
                    saving=int((om.now()-pm.now())*8);key=case*8+FLIP[caller]+4*bool(force)
                    assert key not in costs or costs[key]==saving,(key,costs[key],saving)
                    costs[key]=saving
                    credit=int.from_bytes(p.memory[s['cell_credit']:s['cell_credit']+3],'little',signed=True)
                    if not args.calibrate:assert credit==saving,(key,credit,saving)
                    results.append(dict(case=case,flip=FLIP[caller],Force=bool(force),R=r,original_T=om.now(),hook_T=pm.now(),credit_fast_T=saving,dead_stack_bytes=len(dead)))
    assert len(costs)==80
    # Signed producer costs must retain fractional debt, including exact multiples.
    for value in (0,1,113,114,115,65535,1000000,114*65536-1,-1,-113,-114,-115,-65535,-1000000,-(114*65536-1)):
        mm=Memory(state,blocks['code']);rr=regs[:];rr[24]=s['cell_budget'];rr[12]=0x3C00
        mm[0x3C00]=0;mm[0x3C01]=0x1F
        for i,v in enumerate(value.to_bytes(3,'little',signed=True)):mm[s['cell_credit']+i]=v
        sim=simpool.machine(_rw_simulator(),mm,rr,slot='resolved-budget');Model(sim,speed=3)
        until(sim,0x1F00)
        q=mm[s['cell_lines']]|mm[s['cell_lines']+1]<<8
        debt=mm[s['HLIB_V_PACE']+4]|mm[s['HLIB_V_PACE']+5]<<8
        rem=int.from_bytes(mm[s['cell_credit']:s['cell_credit']+3],'little',signed=True)
        mag,frac=divmod(abs(value),114)
        expected=(mag,0,frac)if value>=0 else(0,min(mag,s['HLIB_PACE_CAP']),-frac)
        assert(q,debt,rem)==expected,(value,q,debt,rem,expected)
    print('15 signed budget edges PASS')
    if args.calibrate:
        lines=['; Generated CPU-only whole-invocation savings; verified by resolved_cell_check.py.']
        for case in range(10):lines.append('        dw '+','.join(str(costs[case*8+i])for i in range(8))+' ; case '+str(case))
        (HERE/'cell_resolved_costs.asm').write_text('\n'.join(lines)+'\n')
    Path('/workspace/work/r_type_resolved_cell_check.json').write_text(json.dumps(results,indent=2)+'\n')
    print(len(results),'resolved cell cases PASS; exact registers/R/game RAM, source/ID metadata; CPU credit', 'calibrated'if args.calibrate else'verified')
    print('credit range',min(costs.values()),max(costs.values()),'fast T; all10 outcomes x8 row/Force variants')
if __name__=='__main__':run()
