"""Pause/resume native ULA folding, caller ABI and R against original CALLs.

Starts with an actual complete copier invocation in both machines. Under DI the
pause display must exactly equal the original ULA; resume must restore the clean
ULA plus the unchanged added layer. All caller registers including R are compared.
"""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]/'nexclash';sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from asm2profile import assemble,sjasm
from nexclash import simpool
from nexclash.dizzy6 import _rw_simulator
from irq_equivalence import Memory,Model
from register_bridge import until
from publication_dynamic import source
from publication_integrated import patch_bytes,build


def run():
    state=json.loads(Path('/workspace/work/r_type_peak_state.json').read_text())
    blocks,s=assemble(str(HERE/'publication_tilemap.asm'),sjasm.find());cases=[]
    # Inspect the actual converter output, rather than separately encoding CALLs.
    from nexclash.recolour import banks
    _,dst,_=build(Path('/workspace/work/r_type_integrated/peak.z80'),
        Path('/workspace/work/r_type_pause_build'),asm='publication_tilemap.asm')
    actual=banks(dst.read_bytes())
    for pc,label in ((0x8B80,'pause_enter'),(0x8B8F,'pause_leave')):
        assert actual[2][pc-0x8000:pc-0x8000+3]==bytes([0xCD])+s[label].to_bytes(2,'little')

    inputmem=bytes(16384)+bytes(state['banks'][5])+bytes(state['banks'][2])+bytes(state['banks'][0])
    for r0 in (0,127,128,255):
        machines=[]
        for patched in (False,True):
            mem=Memory(state,blocks['code']);mem.pages[48]=bytearray(state['banks'][7][:8192]);mem.pages[49]=bytearray(state['banks'][7][8192:])
            for p in (40,41,42,43,44,45):mem.pages[p]=bytearray(8192)
            regs=state['registers'][:];regs[24]=0x8842;regs[26]=1;regs[12]=0xFFF0
            mem[0xFFF0]=0;mem[0xFFF1]=0x1F
            if patched:
                for a,label,call in [(0x8842,'hook_entry',False),(0x8B80,'pause_enter',True),(0x8B8F,'pause_leave',True)]:
                    for i,v in enumerate(patch_bytes(a,label,s)):mem[a+i]=v
                mem[s['hlib_dma_cap']]=1
            sim=simpool.machine(_rw_simulator(),mem,regs,slot='pause-p'if patched else'pause-o');model=Model(sim,speed=0,t_line=228,lines=311,line=0)
            until(sim,0x1F00,1000000);machines.append((sim,model))
        # Main logic may already have composed the next frame before the pause poll.
        # The pause view must use the last published glyphs, not this future source.
        for sim,model in machines:
            for y in range(160):
                for x in range(32):
                    a=source(x,y);sim.memory[a]^=0xFF
            for i in range(640):sim.memory[0x7800+i]^=0x47
        for pc,after,visible in ((0x8B80,0x8B83,False),(0x8B80,0x8B83,False),(0x8B8F,0x8B92,True)):
            for sim,model in machines:
                sim.registers[24]=pc;sim.registers[15]=r0;sim.registers[26]=0
                until(sim,after,1000000)
            (o,om),(p,pm)=machines
            cmp=list(range(25))+[26,27,28]
            bad=[i for i in cmp if o.registers[i]!=p.registers[i]]
            assert not bad,(hex(pc),r0,[(i,o.registers[i],p.registers[i])for i in bad])
            want=bytearray(o.memory[a]for a in range(0x4000,0x5B00))
            if visible:
                for cy in range(20):
                    for cx in range(32):
                        i=cy*32+cx
                        if 0<inputmem[0x7e00+i]<0xDC:
                            for row in range(8):want[source(cx,8*cy+row)-0x6000]=0
                            want[0x1800+i]&=0xC7
            assert bytes(p.memory[a]for a in range(0x4000,0x5B00))==want,('pause picture',hex(pc),r0)
            assert bool(pm.nr.get(0x6B,0)&128)==visible,pm.nr
            assert p.memory.mmu==[255,24,10,11,4,5,0,1]
            cases.append(dict(pc=hex(pc),R=r0,layer_visible=visible,register_diffs=bad))
    Path('/workspace/work/r_type_tilemap_peak/pause-check.json').write_text(json.dumps(cases,indent=2)+'\n');print(len(cases),'pause/resume cases PASS: ABI/R, ULA, mapping, visibility')
if __name__=='__main__':run()
