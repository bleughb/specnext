"""Empty, edge/ink, exact-capacity and overflow tile preparation cases.

Corrupts the actual capacity compare in the runtime binary for the negative, so
its own tables/glyph writes must trigger the reserved-range monitor.
"""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]/'nexclash';sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from asm2profile import assemble,sjasm
from nexclash import simpool
from nexclash.dizzy6 import _rw_simulator
from irq_equivalence import Memory,Model
from publication_dynamic import source
from irq_capture import load

class Guarded(Memory):
    def __setitem__(self,a,v):
        if getattr(self,'watch',False)and self.mmu[a>>13]==40 and (a&8191)>=7168:self.overruns.append(a)
        super().__setitem__(a,v)

def run():
    blocks,s=assemble(str(HERE/'publication_tilemap.asm'),sjasm.find());state=load();results=[]
    for kind,n,negative in [('empty',0,False),('edges-inks',20,False),('capacity',511,False),('overflow',512,False),('broken-capacity',512,True)]:
        code=bytearray(blocks['code'])
        if negative:
            # Locate CP2 / JP NC,tile_overflow inside the generated runtime, not an oracle.
            old=b'\xfe\x02\xd2'+s['tile_overflow'].to_bytes(2,'little')
            off=code.index(old);code[off+1]=3
        mem=Guarded(state,code);mem.overruns=[];mem.watch=False
        mem.mmu=[255,24,10,11,4,5,40,1];mem.pages[40]=bytearray(8192)
        for y in range(160):
            for x in range(32):mem[source(x,y)]=0
        for i in range(640):mem[0x7E00+i]=0;mem[0x7800+i]=0
        cells=list(range(n))if kind!='edges-inks'else[0,31,608,639]+list(range(100,116))
        for k,i in enumerate(cells):
            x,y=i%32,i//32;mem[0x7E00+i]=1
            col=k%16;mem[0x7800+i]=(col&7)|(64 if col&8 else 0)
            for row in range(8):mem[source(x,y*8+row)]=((0x81>>((x+row)%4))|1)&255
        regs=state['registers'][:];regs[24]=s['dynamic_patterns'];regs[26]=0;regs[12]=0x3C00
        mem[0x3C00]=0;mem[0x3C01]=0x1F;mem[s['hlib_dma_cap']]=1
        sim=simpool.machine(_rw_simulator(),mem,regs,slot='geometry');model=Model(sim,speed=3,t_line=228,lines=311)
        overflow=False
        for _ in range(500000):
            pc=sim.registers[24]
            if pc==s['dynamic_patterns.row']:mem.watch=True
            if pc==s['tile_overflow']:overflow=True;break
            if pc==0x1F00:break
            sim.opcodes[mem[pc]]()
        else:raise RuntimeError('geometry did not finish')
        if kind=='overflow':assert overflow and not mem.overruns
        elif negative:assert not overflow and mem.overruns,'broken bound escaped write-range check'
        else:
            assert not overflow and not mem.overruns,(kind,overflow,mem.overruns)
            count=mem[s['tile_count']]|mem[s['tile_count']+1]<<8
            assert count==n+1,(kind,count)
            image=mem.pages[40]
            for k,i in enumerate(sorted(cells)):
                off=((i//32+4)*40+i%32+4)*2;at=image[off+1];tile=image[off]+((at&1)<<8)
                assert tile==k+1,(kind,i,tile)
                raw=mem[0x7800+i];ink=((raw&7)+(8 if raw&64 else 0))or 8;assert at>>1==ink
                for row in range(8):assert image[0xC00+tile*8+row]==mem[source(i%32,(i//32)*8+row)]
        results.append(dict(kind=kind,overflow=overflow,out_of_range_writes=len(mem.overruns)))
    Path('/workspace/work/r_type_tilemap_peak/geometry-check.json').write_text(json.dumps(results,indent=2)+'\n');print(results)
if __name__=='__main__':run()
