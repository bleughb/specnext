"""Independent R-Type capacity review. Original states only; no assembled-hook proof.
Run: /workspace/work/venv101/bin/python packing.py [--stop N]
"""
import argparse
import collections
import json
import pathlib
import sys

HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[4]/'nexclash'))
from nexclash.rzx import trace

ap=argparse.ArgumentParser();ap.add_argument('--stop',type=int)
ap.add_argument('--include-text',action='store_true',help='reproduce rejected unclassified baseline')
a=ap.parse_args()
layouts=('global','owner_min','owner_best')
prev={n:set() for n in layouts}
prev_mono={n:set() for n in layouts}
stats={n:dict(max_sprites=0,max_patterns=0,max_union=0,max_mono_patterns=0,max_mono_union=0,over_sprites=0,over_patterns=0,over_union=0,over_mono_union=0) for n in layouts}
count=0
text_owners=set()
text_draws=0
text_cells=0
TEXT_SIGNATURE=bytes.fromhex('05007e18181818181805004141417f41414105001f3161417f414105006171795d4f')


def addr(x,y):
 return 0x6000+((y&0xC0)<<5)+((y&7)<<8)+((y&0x38)<<2)+x


def packed(cells,ox,oy):
 blocks={}
 for x,y,pix,col in cells:
  bx,dx=divmod(x-ox,2);by,dy=divmod(y-oy,2)
  block=blocks.setdefault((bx,by),bytearray(256))
  for ly,b in enumerate(pix):
   for bit in range(8):
    if b&(128>>bit):block[(dy*8+ly)*16+dx*8+bit]=col
 return [bytes(b) for b in blocks.values() if any(b)]


def callback(pc,sim):
 global count,text_draws,text_cells
 m=sim.memory; frame=sim.tracer.frame_index
 if pc!=0x8842:
  r=sim.registers;owner=m[0x7A9C]
  is_text=(r[6]*256+r[7]==0xCAFF and r[4]==21 and r[5]==24 and
           bytes(m[0xCAFF+i]for i in range(len(TEXT_SIGNATURE)))==TEXT_SIGNATURE)
  if is_text:text_owners.add(owner);text_draws+=1
  else:text_owners.discard(owner)
  return
 groups=collections.defaultdict(list)
 allcells=[]
 for y in range(20):
  for x in range(32):
   owner=m[0x7E00+32*y+x]
   if not 0<owner<0xDC:continue
   if not a.include_text and owner in text_owners:text_cells+=1;continue
   pix=bytes(m[addr(x,8*y+ly)] for ly in range(8))
   if not any(pix):continue
   at=m[0x7800+32*y+x]; col=(at&7)+(8 if at&64 else 0)
   if col==0:col=8 # palette 0 is transparency; 8 is the same black RGB
   c=(x,y,pix,col);groups[owner].append(c);allcells.append(c)
 blocksets={'global':packed(allcells,0,0),'owner_min':[],'owner_best':[]}
 for owner,cells in groups.items():
  ox=min(c[0] for c in cells);oy=min(c[1] for c in cells)
  blocksets['owner_min']+=packed(cells,ox,oy)
  alternatives=[packed(cells,ox-dx,oy-dy) for dx in (0,1) for dy in (0,1)]
  best=min(alternatives,key=lambda bs:(len(bs),len(set(bs))))
  blocksets['owner_best']+=best
 for name,blocks in blocksets.items():
  keys=set(blocks)
  mono=set()
  for b in keys:
   cols=set(b)-{0}
   mono.add(bytes(1 if p else 0 for p in b) if len(cols)==1 else b)
  v=stats[name]
  values=dict(sprites=len(blocks),patterns=len(keys),union=len(keys|prev[name]),mono_patterns=len(mono),mono_union=len(mono|prev_mono[name]))
  for k,n in values.items():
   if n>v['max_'+k]:v['max_'+k]=n;v[k+'_frame']=frame
  for k in ('sprites','patterns','union','mono_union'):
   v['over_'+k]+=values[k]>128
  prev[name]=keys;prev_mono[name]=mono
 count+=1
 if count%4000==0:print('refreshes',count,'frame',frame,flush=True)

frames,desync=trace(str(HERE.parents[1]/'Rtype.rzx'),[0x8842,0x8CFD,0x8D65,0x8DD3,0x8E29],callback,stop=a.stop)
r=dict(frames=frames,desync=desync,refreshes=count,text_draws=text_draws,text_cells=text_cells,layouts=stats,scope='Original refresh states, exact nibble patterns; credits text tagged by live graphic identity and retained on ULA; optional monochrome palette normalization')
(HERE/('packing.json'if a.include_text else 'packing-text-classified.json')).write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
