"""Original versus assembled native-IRQ wrapper with supplied LD A,R values.

Checks all game banks, caller registers and mapped pages. The slot2 shadow and
slot0 lookup are genuinely mapped during entry; the wrapper must supply ROM to
native code and restore the interrupted mappings. Temporary source pixels are
excluded only until explicitly restored before RAM comparison. No timing claim.
"""
import collections,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]/'nexclash'
sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from asm2profile import assemble,sjasm
from nexclash import simpool,hooklib,rzx
from nexclash.dizzy6 import _rw_simulator
from skoolkit import ROM128
from irq_capture import load

class Memory:
    def __init__(self,state,code,shadow=False):
        self.pages={2*i+j:bytearray(b[8192*j:8192*(j+1)]) for i,b in enumerate(state['banks']) for j in (0,1)}
        self.pages[24]=bytearray(8192);self.pages[24][:len(code)]=code
        self.pages[42]=self.pages[10][:]
        self.pages[40]=bytearray(8192)
        self.pages[46]=bytearray([0xA5])*8192
        self.rom=Path(ROM128[1]).read_bytes()
        self.mmu=[46 if shadow else 255,24,42 if shadow else 10,11,4,5,40 if shadow else 0,1]
    def __len__(self):return 65536
    def __getitem__(self,a):
        if isinstance(a,slice):return [self[i]for i in range(*a.indices(65536))]
        if a in getattr(self,'pending_stack',()):self.bad_stack_reads.append(a)
        p=self.mmu[a>>13];return self.rom[a] if p==255 else self.pages[p][a&8191]
    def __setitem__(self,a,v):
        if hasattr(self,'pending_stack'):self.pending_stack.discard(a)
        p=self.mmu[a>>13]
        if p!=255:self.pages[p][a&8191]=v

class Model(hooklib.NextModel):
    def nextreg(self,n,v):
        super().nextreg(n,v)
        if 0x50<=n<=0x57:self.sim.memory.mmu[n-0x50]=v
    def write_port(self,regs,port,value,*args):
        if port&0x8002==0:
            self.sim.memory.mmu[6]=(value&7)*2
            self.sim.memory.mmu[7]=(value&7)*2+1
        return super().write_port(regs,port,value,*args)
    def read_port(self,regs,port):
        if port==0x243B:return self.sel
        if port==0x253B and 0x50<=self.sel<=0x57:return self.sim.memory.mmu[self.sel-0x50]
        if port&1==0:return 0xFF
        return super().read_port(regs,port)

def fixtures():
    path=Path('/workspace/work/r_type_irq_cases.json')
    if path.exists():return json.loads(path.read_text())
    states=[];pending=None;counts=collections.Counter();seen=set()
    def at(pc,sim):
        nonlocal pending
        if pc==0xBE23:
            pending=dict(frame=sim.tracer.frame_index,banks=[list(b)for b in sim.memory.banks],registers=list(sim.registers))
        elif pending and counts[pc]<16:
            counts[pc]+=1
            if pending['frame'] not in seen:
                states.append(pending);seen.add(pending['frame'])
    f,d=rzx.trace(str(HERE.parent/'Rtype.rzx'),[0xBE23,0xBEDB,0xBF36],at,stop=4000)
    assert d is None and states,(f,d)
    states.append(load());path.write_text(json.dumps(states));return states

def execute(state,code,s,patched=False,values=None,negative=False,slot2=None):
    mem=Memory(state,code,shadow=patched)
    if patched and slot2 is not None:
        mem.mmu[2]=slot2
        for page in range(64,76):mem.pages[page]=bytearray([0xA5])*8192
    regs=state['registers'][:];regs[24]=0xBE23;regs[26]=0
    # Relocated IRQ stack so original and wrapper dead stack cannot hide live RAM differences.
    regs[12]=0x3C00;mem[0x3C00]=0;mem[0x3C01]=0x1F
    if patched:
        for a,label in [(0xBE26,'irq_in'),(0xBE52,'irq_out')]:
            for i,v in enumerate(b'\xc3'+s[label].to_bytes(2,'little')):mem[a+i]=v
    original_pixels={a:mem[a] for a in range(0x6000,0x7800)if (a<0x7000 or a&255<128)}
    if patched:
        for a in original_pixels:mem[a]=0
    sim=simpool.machine(_rw_simulator(),mem,regs,slot='irq-p' if patched else 'irq-o')
    model=Model(sim,speed=3 if patched else 0,t_line=228,lines=311,line=247)
    observed=[];n=0
    while sim.registers[24]!=0x1F00:
        pc=sim.registers[24]
        if pc in (0xBEDB,0xBF36):
            if values is not None:
                assert n<len(values) and values[n][0]==pc,(n,pc,values)
                value=values[n][1] ^ ((1 if pc==0xBEDB else 2) if negative else 0)
                sim.registers[15]=(value&128)|((value-2)&127)
            sim.opcodes[mem[pc]]()
            observed.append((pc,sim.registers[0]));n+=1
        else:sim.opcodes[mem[pc]]()
        if sim.registers[25]-regs[25]>500000:raise RuntimeError('IRQ did not return')
    if patched:
        for a,v in original_pixels.items():mem[a]=v
    return sim,observed

def run():
    blocks,s=assemble(str(HERE/'publication_integrated.asm'),sjasm.find())
    summary=[];coverage=collections.Counter();caught=0
    for state in fixtures():
        original,values=execute(state,blocks['code'],s)
        if not values:continue
        for negative in (False,True):
            patched,obs=execute(state,blocks['code'],s,True,values,negative)
            om,pm=original.memory,patched.memory
            cmp=list(range(15))+list(range(16,25))+[26,27,28]
            rd=[i for i in cmp if original.registers[i]!=patched.registers[i]]
            md=[]
            for page in range(16):
                ppage=42 if page==10 else page
                for off,(a,b) in enumerate(zip(om.pages[page],pm.pages[ppage])):
                    addr=(page//2,off+(page%2)*8192)
                    if page==5 and off in set(range(0x1E26,0x1E29))|set(range(0x1E52,0x1E55)):continue
                    if a!=b:md.append(addr)
            assert pm.mmu==[46,24,42,11,4,5,40,1],pm.mmu
            assert patched.tracer.sel==0,patched.tracer.sel
            if negative:
                assert md,'changed supplied-R value escaped';caught+=1
            else:
                assert not rd and not md,(state['frame'],rd,md[:12])
                coverage.update(hex(pc)for pc,v in values)
            summary.append(dict(frame=state['frame'],negative=negative,reads=values,register_diffs=rd,ram_diffs=md[:16],ram_diff_count=len(md)))
    assert set(coverage)=={'0xbedb','0xbf36'},coverage
    result=dict(scope=__doc__,cases=summary,coverage=dict(coverage),negative_caught=caught)
    Path('/workspace/work/r_type_integrated/irq-equivalence.json').write_text(json.dumps(result,indent=2)+'\n')
    print('supplied-R IRQ PASS',dict(coverage),'negative cases',caught)

if __name__=='__main__':run()
