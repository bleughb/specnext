"""Reconstruct captured graphics with the ORIGINAL unpacker and source snapshot.

No captured graphic bytes are inputs to decoding. Recipes contain only original
loader register/header parameters. Output remains private build scratch.
"""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]/'nexclash';sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from nexclash import simpool,z80tonex as Z
from nexclash.dizzy6 import _rw_simulator
from irq_equivalence import Memory,Model
from register_bridge import until

def decode(snapshot,entry,previous=None):
    state=dict(banks=previous or [list(snapshot.banks[i])for i in range(8)])
    mem=Memory(state,b'');mem.mmu=[255,255,10,11,4,5,0,1]
    ix=entry['IX']
    # The preceding low-IX loader call writes the requested filename digit.
    mem[0x600D]=entry['level']
    mem[0x719C]=entry['level']
    regs=[0]*30;regs[8:10]=[entry['IX']>>8,entry['IX']&255];regs[12]=0xF000;regs[24]=0x8F31
    sim=simpool.machine(_rw_simulator(),mem,regs,slot='asset-unpack');model=Model(sim,speed=0)
    until(sim,0x8F4E,10000000)
    # The native continuation still has bank1 mapped. Canonical graphics use
    # the normal gameplay bank0, after the caller restores port7FFD=10.
    mem.mmu[6:]=[0,1]
    return bytes(mem[a]for a in range(65536)),[bytes(mem.pages[2*i])+bytes(mem.pages[2*i+1])for i in range(8)]

def run():
    snapshot=Z.Z80Snapshot(str(HERE.parent/'Rtype.z80'))
    source=Path('/workspace/work/r_type_unpack_recipes.json')
    if not source.exists():source=Path('/workspace/work/r_type_unpack_states.json')
    states=[s for s in json.loads(source.read_text())if s['IX']&0x8000]
    corpus=json.loads(Path('/workspace/work/r_type_assets.json').read_text())
    found=set();outputs={}
    # Include assets already in the original snapshot, then each native unpack.
    initial=bytes(snapshot.read(a)or 0 for a in range(65536))
    images=[('initial',initial)]
    previous=None
    for j,entry in enumerate(states):
        data,previous=decode(snapshot,entry,previous);images.append((str(j),data));outputs[str(j)]=list(data)
        print('decoded',j,'level',entry['level'],'IX',hex(entry['IX']),flush=True)
    for key,c in corpus['cells'].items():
        a=c['address']+1;bits=bytes(c['bits'])
        if any(data[a:a+8]==bits for name,data in images):found.add(key)
    print('cell variants matched at actual source address',len(found),'/',len(corpus['cells']))
    missing=[c for k,c in corpus['cells'].items()if k not in found]
    print('unmatched by level',dict(__import__('collections').Counter(c['level']for c in missing)),flush=True)
    Path('/workspace/work/r_type_decoded_assets.json').write_text(json.dumps(outputs,separators=(',',':')))
if __name__=='__main__':run()
