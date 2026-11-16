"""Freeze a completed frame, compare JNext PNG to an independent RGB compositor.

The actual hardware palette and BRAM map/definitions are checked against original
ZX source bits. Exact 256x192 paper pixels include the unchanged HUD/scenery.
A post-preparation glyph-bit mutation is a meaningful negative control.
"""
import json,os,sys,zipfile
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]/'nexclash';sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from nexclash import jnext as J,recolour
from publication_integrated import build
from publication_dynamic import source


def run():
    os.environ.setdefault('NEXCLASH_JNEXT','/workspace/work/jnext-bin/root/usr/bin/jnext')
    out=Path('/workspace/work/r_type_tilemap_preview');out.mkdir(exist_ok=True)
    src,nex,s=build('/workspace/work/r_type_integrated/peak.z80',out,'publication_tilemap.asm')
    code=bytearray(nex.read_bytes());off=recolour.nex_offsets(code)[12]+s['hook_return']-0x2000
    code[off:off+2]=bytes.fromhex('f376');frozen=out/'frozen.nex';frozen.write_bytes(code)
    jobs=[]
    for negative in (False,True):
        folder=out/('broken'if negative else'good')
        script=J.Script(500)
        if negative:
            script.rule('on execute %d once do\n  set n = nextreg[0x56]\n  set nextreg[0x56] = 14\n  set mem[0xCC08] = mem[0xCC08] ^ 128\n  set nextreg[0x56] = n\nend\n'%s['hook_return'])
            script.var('n')
        script.at(8,'  screenshot "frame.png"\n  save_snapshot "frame.jns"\n');script.exit_at(9)
        jobs.append((str(frozen),script.text(),str(folder),30,'/workspace/scratch/cspect-next-2gb.img','/workspace/work/r_type_jnext_home'))
    assert J.run_all(jobs)==[0,0]
    state=json.loads(Path('/workspace/work/r_type_peak_state.json').read_text())
    original=bytes(16384)+bytes(state['banks'][5])+bytes(state['banks'][2])+bytes(state['banks'][0])
    results=[]
    for negative in (False,True):
        folder=out/('broken'if negative else'good');frame=J.Frame(str(folder/'frame.jns'))
        with zipfile.ZipFile(frame.path)as z:tile=z.read('mem/bank7-bram.bin');nr=bytes.fromhex(json.loads(z.read('state/nextreg.json'))['regs'])
        pal=bytes.fromhex(frame.pal['tilemap_rgb333']);pal=[pal[i]|pal[i+1]<<8 for i in range(0,512,2)]
        up=bytes.fromhex(frame.pal['ula_rgb333']);up=[up[i]|up[i+1]<<8 for i in range(0,512,2)]
        assert all(pal[2*i]==(0xE3<<1|1)and pal[2*i+1]==up[i]for i in range(16)), 'native ink palette'
        assert nr[0x6B]==0x8B and nr[0x6E]==0x80 and nr[0x6F]==0x8C
        picture=Image.open(folder/'frame.png').convert('RGB');bad=[];glyph_bad=0
        for y in range(192):
            for x in range(256):
                ua=source(x//8,y)-0x6000 if y<160 else ((y&192)<<5)+((y&7)<<8)+((y&56)<<2)+x//8
                attr=frame.ula[0x1800+(y//8)*32+x//8]
                bright=8 if attr&64 else 0
                ink=(attr&7)+bright;paper=((attr>>3)&7)+bright
                base_colour=up[ink if frame.ula[ua]&(128>>(x&7))else paper+16]
                rgb=(0,0,0)if base_colour>>1==0xE3 else J.rgb333(base_colour)
                if y<160:
                    i=(y//8)*32+x//8;col=original[0x7800+i];ci=((col&7)+(8 if col&64 else 0))or 8
                    fg=0<original[0x7E00+i]<0xDC and original[source(x//8,y)]&(128>>(x&7))
                    want=ci if fg else 0
                    a=((y//8+4)*40+x//8+4)*2;at=tile[a+1];g=tile[a]+((at&1)<<8)
                    got=(at>>1)if tile[0xC00+g*8+(y&7)]&(128>>(x&7))else 0
                    glyph_bad+=got!=want
                    if fg:rgb=J.rgb333(up[ci])
                actual=picture.getpixel((64+x*2,64+y*2))
                if actual!=rgb:bad.append((x,y,rgb,actual))
        if negative:assert bad and glyph_bad,'glyph corruption escaped RGB oracle'
        else:assert not bad and not glyph_bad,(len(bad),glyph_bad,bad[:12])
        results.append(dict(negative=negative,pixel_mismatches=len(bad),glyph_mismatches=glyph_bad))
    (out/'preview-check.json').write_text(json.dumps(results,indent=2)+'\n');print(results)
if __name__=='__main__':run()
