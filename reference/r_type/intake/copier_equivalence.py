"""Whole assembled copier hook versus original, IRQ-free functional proof.

Uses the shared NextModel DMA/Z80N handlers and real MMU page effects. Not a timing
model. Compares every caller register including R and all eight game banks, with
explicit patch-site, visual ULA and dead-stack differences reported separately.
"""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]/'nexclash'
sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from asm2profile import assemble,sjasm
from nexclash import simpool
from nexclash.dizzy6 import _rw_simulator
from irq_equivalence import Memory,Model
from publication_dynamic import full_lut,oracle,source
from register_bridge import until
from irq_capture import load


def run_case(state,blocks,s,real_stack=False,tile=False):
    regs=state['registers'][:];regs[24]=0x8842;regs[26]=1
    if not real_stack:regs[12]=0xFFF0
    machines=[];inputmem=None
    for patched in (False,True):
        mem=Memory(state,blocks['code'],False)
        mem.mmu=[255,24,10,11,4,5,0,1]
        mem.pages[46]=bytearray(full_lut()[:8192]);mem.pages[47]=bytearray(full_lut()[8192:])
        if tile:
            mem.pages[48]=bytearray(state['banks'][7][:8192]);mem.pages[49]=bytearray(state['banks'][7][8192:])
        for p in (40,41,42,43,44):mem.pages[p]=bytearray(8192)
        if not real_stack:mem[0xFFF0]=0;mem[0xFFF1]=0x1F
        ret=mem[regs[12]]|mem[(regs[12]+1)&65535]<<8
        if not patched:inputmem=bytes(mem[a]for a in range(65536))
        if patched:
            for i,v in enumerate(b'\xc3'+s['hook_entry'].to_bytes(2,'little')):mem[0x8842+i]=v
            mem[s['hlib_dma_cap']]=1
        sim=simpool.machine(_rw_simulator(),mem,regs,slot='whole-p'if patched else'whole-o')
        model=Model(sim,speed=0,t_line=228,lines=311,line=0)
        until(sim,ret,limit=1000000)
        machines.append((sim,model))
    (o,om),(p,pm)=machines
    rd=[(i,o.registers[i],p.registers[i])for i in list(range(25))+[26,27,28]if o.registers[i]!=p.registers[i]]
    assert not rd,(state['frame'],rd)
    expected,attrs=oracle(inputmem)
    if tile:
        image=p.memory.pages[14]
        for y in range(160):
            for x in range(256):
                i=(y//8)*32+x//8;owner=inputmem[0x7E00+i]
                a=inputmem[0x7800+i];colour=((a&7)+(8 if a&64 else 0)) or 8
                want=colour if 0<owner<0xDC and inputmem[source(x//8,y)]&(128>>(x&7)) else 0
                off=((y//8+4)*40+x//8+4)*2
                attr=image[off+1];glyph=image[off]+((attr&1)<<8)
                bit=image[0xC00+glyph*8+(y&7)]&(128>>(x&7))
                got=(attr>>1)if bit else 0
                assert got==want,('tile pixel',x,y,want,got)
    else:
        assert bytes(pm.pattern[:len(expected)])==expected,'pattern bytes'
    clean=bytearray(o.memory[a]for a in range(0x4000,0x5B00))
    for cy in range(20):
        for cx in range(32):
            i=cy*32+cx
            if 0<inputmem[0x7E00+i]<0xDC:
                for r in range(8):clean[source(cx,cy*8+r)-0x6000]=0
                clean[0x1800+i]&=0xC7
    assert bytes(p.memory[a]for a in range(0x4000,0x5B00))==clean,'full clean ULA differs'
    ds=[];stack=[]
    for page in range(16):
        for off,(a,b)in enumerate(zip(o.memory.pages[page],p.memory.pages[page+34 if tile and page in (14,15) else page])):
            if a==b:continue
            bank,offset=page//2,(page%2)*8192+off
            if page==4 and off in range(0x842,0x845):continue
            if bank==5 and offset<0x1B00:continue
            if bank==0 and regs[12]-0xC000-64<=offset<regs[12]-0xC000:stack.append(offset);continue
            ds.append((bank,offset,a,b))
    assert not ds,(state['frame'],ds[:12])
    for y in range(20):
        for x in range(32):
            i=y*32+x
            if 0<inputmem[0x7E00+i]<0xDC:
                assert all(p.memory[0x4000+source(x,8*y+r)-0x6000]==0 for r in range(8))
                assert p.memory[0x5800+i]&0x38==0,'foreground ULA paper'
    assert p.memory.mmu==[255,24,10,11,4,5,0,1],p.memory.mmu
    convergence=[]
    if real_stack:
        for sim,model in machines:
            sim.memory.pending_stack={a+0xC000 for a in stack}
            sim.memory.bad_stack_reads=[]
            until(sim,0x868C,limit=1000000)
            assert not sim.memory.bad_stack_reads,sim.memory.bad_stack_reads
            if sim.memory.pending_stack:
                assert sim.accept_interrupt(sim.registers,sim.memory,0), 'scheduled IRQ not accepted'
                until(sim,0x868C,limit=300000)
            assert not sim.memory.bad_stack_reads,sim.memory.bad_stack_reads
            assert not sim.memory.pending_stack,sim.memory.pending_stack
            convergence.append(dict(overwritten=len(stack),read_before_write=0,PC=hex(sim.registers[24])))
    return dict(convergence=convergence,frame=state['frame'],register_diffs=rd,ram_diffs=ds,dead_stack_offsets=stack,sprites=len(expected)//128)

def run():
    blocks,s=assemble(str(HERE/'publication_integrated.asm'),sjasm.find())
    results=[run_case(state,blocks,s)for state in (load(),json.loads(Path('/workspace/work/r_type_peak_state.json').read_text()))]
    results.append(run_case(json.loads(Path('/workspace/work/r_type_peak_state.json').read_text()),blocks,s,True))
    tile_blocks,tile_syms=assemble(str(HERE/'publication_tilemap.asm'),sjasm.find())
    tile_results=[run_case(state,tile_blocks,tile_syms,tile=True)for state in (load(),json.loads(Path('/workspace/work/r_type_peak_state.json').read_text()))]
    Path('/workspace/work/r_type_tilemap_peak/copier-equivalence.json').write_text(json.dumps(dict(scope=__doc__,results=tile_results),indent=2)+'\n')
    print('tilemap whole hook PASS',tile_results)
    Path('/workspace/work/r_type_integrated/copier-equivalence.json').write_text(json.dumps(dict(scope=__doc__,results=results),indent=2)+'\n')
    print('whole hook no-IRQ PASS',results)

if __name__=='__main__':run()
