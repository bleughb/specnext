"""Original R-Type end scene: identify final-cell owners and plot callers."""
import collections,json,pathlib,sys
from PIL import Image
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[4]/'nexclash'))
from nexclash.rzx import trace
calls=collections.Counter();copyowners=collections.Counter();shots=0

def callback(pc,sim):
 global shots
 m=sim.memory;r=sim.registers;f=sim.tracer.frame_index
 if pc!=0x8842:
  sp=r[12];ret=m[sp]|m[(sp+1)&65535]<<8
  calls[(hex(pc),hex(m[0x7A9C]),hex(ret-3),r[2],r[3],r[4],r[5],hex(r[6]*256+r[7]),hex(m.o7ffd))]+=1
  return
 if shots:return
 shots+=1
 groups={}
 for y in range(20):
  for x in range(32):
   owner=m[0x7E00+32*y+x]
   if not 0<owner<0xDC:continue
   copyowners[owner]+=1
   im=groups.setdefault(owner,Image.new('RGB',(256,160)))
   for line in range(8):
    sy=y*8+line;a=0x6000+((sy&0xC0)<<5)+((sy&7)<<8)+((sy&0x38)<<2)+x
    b=m[a]
    for bit in range(8):
     if b&(128>>bit):im.putpixel((x*8+bit,sy),(255,255,255))
 for owner,im in groups.items():im.save(HERE/('credits-owner-%02x.png'%owner))

frames,desync=trace(str(HERE/'credits.rzx'),[0x8842,0x8CFD,0x8D65,0x8DD3,0x8E29],callback)
r=dict(frames=frames,desync=desync,owners=dict(copyowners),calls=[dict(key=k,count=v)for k,v in calls.most_common()])
(HERE/'credits-classification.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
