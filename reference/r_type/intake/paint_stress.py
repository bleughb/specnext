"""STATIC whole-frame colour-copy cost trial; not the engine's live paint path.

Textures encode one frozen peak picture, across all flip combinations. Subsequent
natural play exercises occupied-cell copying and stale-cell clearing costs only;
the old texture picture is deliberately unsuitable as live game art.
"""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]/'nexclash';sys.path[:0]=[str(ROOT)]
from publication_dynamic import source

def texture(snap,i):
    cx=i%32;cy=i//32;flip=i&3;out=bytearray(64)
    for ry in range(8):
        for rx in range(8):
            x=7-rx if flip&1 else rx;y=7-ry if flip&2 else ry
            bit=snap.read(source(cx,cy*8+y))&(128>>x)
            colour=3+(i*5+ry*9+rx*3)%224
            out[ry*8+rx]=colour if bit and (ry*8+rx)%13 else 0
    return bytes(out),flip

def textures(snap):
    atlas=bytearray(49152);descs=bytearray(8192)
    for i in range(640):
        t,flip=texture(snap,i);atlas[i*64:i*64+64]=t
        # An absent texel value makes LDIX/LDDX unconditional, including zero.
        skip=next(v for v in range(256)if v not in t)
        page=96+(i*64//8192);off=(i*64)%8192
        descs[i*6:i*6+6]=off.to_bytes(2,'little')+bytes([page,flip,skip,0])
    return {25:bytes(8192)+bytes(descs),**{48+i:bytes(atlas[i*16384:(i+1)*16384])for i in range(3)}}

def run():
    from publication_integrated import build
    build('/workspace/work/r_type_integrated/peak.z80',Path('/workspace/work/r_type_paint_stress'),'publication_paint.asm')
if __name__=='__main__':run()
