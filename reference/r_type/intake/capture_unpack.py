"""Capture original unpacker inputs for a source-only build (new asset provenance).

Does not repeat intake/capacity/ISR scans. Cache states privately in work; output
register recipes can reconstruct graphics from the owner's original snapshot.
"""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]/'nexclash';sys.path[:0]=[str(ROOT)]
from nexclash.rzx import trace
out=Path('/workspace/work/r_type_unpack_recipes.json')
if out.exists():print('cached',len(json.loads(out.read_text())))
else:
 states=[];seen=set()
 def at(pc,sim):
  r=sim.registers;ix=r[8]*256+r[9]
  key=(ix,sim.memory[0x719C],bytes(sim.memory[(ix+i)&65535]for i in range(3)))
  if key not in seen:
   seen.add(key);states.append(dict(frame=sim.tracer.frame_index,IX=ix,level=sim.memory[0x719C],registers=list(r),banks=[list(b)for b in sim.memory.banks]))
   print('unpacker',hex(ix),'level',sim.memory[0x719C],'frame',sim.tracer.frame_index,flush=True)
 f,d=trace(str(HERE.parent/'Rtype.rzx'),[0x8F31],at)
 assert d is None,(f,d)
 out.write_text(json.dumps(states,separators=(',',':'))+'\n');print('PASS',f,'frames',len(states),'distinct unpacker inputs')
