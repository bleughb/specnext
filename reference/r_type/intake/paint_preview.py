"""Static peak paint stress: independent RGB oracle and post-publication negative.

Not live colour identity or figure-sheet proof. All tested cells use preexpanded
one-frame textures; moving-gameplay art is intentionally outside this probe.
"""
import json,os,sys,zipfile
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]/'nexclash';sys.path[:0]=[str(ROOT)]
from nexclash import jnext as J,recolour,z80tonex as Z
from publication_integrated import build
from publication_dynamic import source
from paint_stress import texture

def dac(v):
    # JNext expands a 3-bit DAC value by bit replication (nearest 8-bit level).
    return tuple(((q<<5)|(q<<2)|(q>>1))for q in ((v>>6)&7,(v>>3)&7,v&7))

def run():
    os.environ.setdefault('NEXCLASH_JNEXT','/workspace/work/jnext-bin/root/usr/bin/jnext')
    out=Path('/workspace/work/r_type_paint_preview');out.mkdir(exist_ok=True)
    src,nex,s=build('/workspace/work/r_type_integrated/peak.z80',out,'publication_paint.asm')
    snap=Z.Z80Snapshot(str(src));code=bytearray(nex.read_bytes());off=recolour.nex_offsets(code)[12]+s['hook_return']-0x2000
    code[off:off+2]=bytes.fromhex('f376');frozen=out/'frozen.nex';frozen.write_bytes(code)
    marked=None
    for i in range(640):
        if 0<snap.read(0x7E00+i)<0xDC:
            t,f=texture(snap,i)
            for j,v in enumerate(t):
                if v:
                    x=7-j%8 if f&1 else j%8;y=7-j//8 if f&2 else j//8
                    marked=(i%32*8+x,i//32*8+y,v);break
        if marked:break
    jobs=[]
    for negative in (False,True):
        folder=out/('broken'if negative else'good');sc=J.Script(500)
        if negative:
            x,y,v=marked;sc.var('n');sc.rule('on execute %d once do\n  set n = nextreg[0x56]\n  set nextreg[0x56] = nextreg[0x12] * 2 + %d\n  set mem[%d] = %d\n  set nextreg[0x56] = n\nend\n'%(s['hook_return'],y//32,0xC000+(y%32)*256+x,4 if v!=4 else 5))
        sc.at(8,'  screenshot "frame.png"\n  save_snapshot "frame.jns"\n');sc.exit_at(9)
        jobs.append((str(frozen),sc.text(),str(folder),30,'/workspace/scratch/cspect-next-2gb.img','/workspace/work/r_type_jnext_home'))
    assert J.run_all(jobs)==[0,0]
    results=[]
    for negative in (False,True):
        folder=out/('broken'if negative else'good');frame=J.Frame(str(folder/'frame.jns'))
        with zipfile.ZipFile(frame.path)as z:
            nr=bytes.fromhex(json.loads(z.read('state/nextreg.json'))['regs']);tile=z.read('mem/bank7-bram.bin')
        up=bytes.fromhex(frame.pal['ula_rgb333']);up=[up[i]|up[i+1]<<8 for i in range(0,512,2)]
        lp=bytes.fromhex(frame.pal['layer2_rgb333']);lp=[lp[i]|lp[i+1]<<8 for i in range(0,512,2)]
        for i,v in enumerate(lp):
            master=0xE3 if i==0 else i-1 if i<228 else i
            assert v==(master<<1|int(bool(master&3))),('palette',i,v,master)
        assert nr[0x69]&128 and nr[0x12]==35,(nr[0x69],nr[0x12])
        picture=Image.open(folder/'frame.png').convert('RGB');bad=[];painted=0;glyphbad=0
        for y in range(192):
            for x in range(256):
                ua=((y&192)<<5)+((y&7)<<8)+((y&56)<<2)+x//8
                a=frame.ula[0x1800+y//8*32+x//8];b=8 if a&64 else 0
                col=up[(a&7)+b if frame.ula[ua]&(128>>(x&7))else ((a>>3)&7)+b+16]
                rgb=(0,0,0)if col>>1==0xE3 else dac(col)
                if y<160:
                    i=y//8*32+x//8;owner=snap.read(0x7E00+i)
                    if 0<owner<0xDC:
                        t,f=texture(snap,i);rx=7-(x&7)if f&1 else x&7;ry=7-(y&7)if f&2 else y&7
                        v=t[ry*8+rx]
                        if v:rgb=dac(lp[v]);painted+=1
                        at=((y//8+4)*40+x//8+4)*2;glyphbad+=bool(tile[at]or tile[at+1])
                actual=picture.getpixel((64+x*2,64+y*2))
                if actual!=rgb:bad.append((x,y,rgb,actual))
        if negative:assert len(bad)==1,('negative',len(bad),bad[:5])
        else:assert not bad and not glyphbad,(len(bad),glyphbad,bad[:8])
        results.append(dict(negative=negative,pixel_mismatches=len(bad),painted_pixels=painted,glyph_mismatches=glyphbad))
    (out/'paint-preview.json').write_text(json.dumps(results,indent=2)+'\n');print(results)
if __name__=='__main__':run()
