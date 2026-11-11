"""Static4bpp texture cost comparison;111-pattern publication, one15-colour palette.

Global16x16 grid here measures costs only. Actual painted owner packing/palette
assignment and live source identity are NOT implemented by this stress probe.
"""
from pathlib import Path
from paint_stress import HERE,source

def texture(snap,i):
    cx=i%32;cy=i//32;out=bytearray(32)
    for y in range(8):
        bits=snap.read(source(cx,cy*8+y))
        for x in range(8):
            v=1+(i*5+y*3+x)%15 if bits&(128>>x) and (y*8+x)%13 else 0
            out[y*4+x//2]|=v<<(0 if x&1 else 4)
    return bytes(out)

def textures(snap):
    atlas=bytearray(32768);descs=bytearray(8192)
    for i in range(640):
        t=texture(snap,i);atlas[i*32:i*32+32]=t
        descs[i*4:i*4+4]=((i*32)%8192).to_bytes(2,'little')+bytes([96+i//256,int(any(t))])
    return {25:bytes(8192)+bytes(descs),48:bytes(atlas[:16384]),49:bytes(atlas[16384:])}

if __name__=='__main__':
    from publication_integrated import build
    build('/workspace/work/r_type_integrated/peak.z80',Path('/workspace/work/r_type_spritepaint'),'publication_spritepaint.asm')
