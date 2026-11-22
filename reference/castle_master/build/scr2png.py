import sys
from PIL import Image
d=open('C:/dev/castlemaster/Castlemaster1.tap','rb').read()
pal=[(0,0,0),(0,0,215),(215,0,0),(215,0,215),(0,215,0),(0,215,215),(215,215,0),(215,215,215)]
palb=[(0,0,0),(0,0,255),(255,0,0),(255,0,255),(0,255,0),(0,255,255),(255,255,0),(255,255,255)]
for name,off in (('a',513),('b',43529)):
    s=d[off:off+6912]
    open('cm_scr_%s.scr'%name,'wb').write(s)
    im=Image.new('RGB',(256,192))
    for y in range(192):
        for x in range(256):
            a=0x1800+(y//8)*32+x//8; at=s[a]
            b=s[((y&0xC0)<<5)|((y&7)<<8)|((y&0x38)<<2)|(x>>3)]>>(7-(x&7))&1
            p=palb if at&64 else pal
            im.putpixel((x,y),p[at&7] if b else p[(at>>3)&7])
    im.save('cm_scr_%s.png'%name)
