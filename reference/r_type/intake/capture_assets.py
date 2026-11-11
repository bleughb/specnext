"""New figure/source-byte corpus for the colour build, not another intake scan.

Whole plots group only by the game's actual object/owner within one copier update.
Records canonical cells and all per-byte/ink variants; no screen-box joining.
Generated captured graphics stay in specnext or /workspace/work, never nexclash.
"""
import argparse,collections,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]/'nexclash';sys.path[:0]=[str(ROOT)]
from nexclash import rzx
TEXT=bytes.fromhex('05007e18181818181805004141417f41414105001f3161417f414105006171795d4f')
FLIPS={0x8CFD:0,0x8D65:1,0x8DD3:2,0x8E29:3}

def run():
    ap=argparse.ArgumentParser();ap.add_argument('--stop',type=int);ap.add_argument('--out',type=Path,default=Path('/workspace/work/r_type_assets.json'));args=ap.parse_args()
    cells={};plots={};figures={};pending=collections.defaultdict(list);levels=collections.Counter();draws=0;texts=0;lastlog=-1;conflicts=collections.Counter()
    def flush():
        for (level,obj),parts in pending.items():
            x=min(p['x']for p in parts);y=min(p['y']for p in parts)
            # Object identity is authoritative even when pieces do not touch.
            signature=tuple((p['plot'],p['x']-x,p['y']-y,p['flip'])for p in parts)
            key=json.dumps([level,signature],separators=(',',':'))
            if key in figures:figures[key]['count']+=1
            else:figures[key]=dict(level=level,count=1,parts=[dict(p,dx=p['x']-x,dy=p['y']-y)for p in parts])
        pending.clear()
    def at(pc,sim):
        nonlocal draws,texts,lastlog
        m=sim.memory;r=sim.registers;frame=sim.tracer.frame_index
        if frame//4000!=lastlog:
            lastlog=frame//4000;print('frame',frame,'draws',draws,'cells',len(cells),'plots',len(plots),'figures',len(figures),flush=True)
        if pc==0x8842:flush();return
        ptr=r[6]*256+r[7];h=r[4]or 256;w=r[5]or 256
        if ptr==0xCAFF and (h,w)==(21,24)and bytes(m[(ptr+i)&65535]for i in range(34))==TEXT:texts+=1;return
        if w>32 or h>32:raise ValueError(('unexpected whole-plot dimensions',frame,hex(pc),w,h))
        level=m[0x719C];override=m[0x8EB1];owner=m[0x7A9C];iy=r[10]*256+r[11]
        obj=('object',(iy-0x8501)//9)if 0x8501<=iy<0x8501+28*9 and(iy-0x8501)%9==0 else('owner',owner)
        records=[];start=ptr
        for y in range(h):
            for x in range(w):
                addr=ptr;attr=m[ptr];ptr=(ptr+1)&65535
                if attr==0x36:continue
                bits=bytes(m[(ptr+i)&65535]for i in range(8));ptr=(ptr+8)&65535
                a=override or attr;ink=((a&7)+(8 if a&64 else 0))or 8
                ck='%02x:%04x:%x:%s'%(level,addr,ink,bits.hex())
                if ck not in cells:cells[ck]=dict(level=level,address=addr,ink=ink,attribute=attr,bits=list(bits))
                records.append([x,y,ck])
        if not records:return
        sig=json.dumps([level,start,w,h,records],separators=(',',':'));pk=hashlib.sha256(sig.encode()).hexdigest()[:24]
        if pk not in plots:plots[pk]=dict(level=level,address=start,w=w*8,h=h*8,cells=records)
        pending[(level,obj)].append(dict(plot=pk,x=r[3]*8,y=r[2]*8,flip=FLIPS[pc],object=list(obj),owner=owner))
        levels[str(level)]+=1;draws+=1
    frames,desync=rzx.trace(str(HERE.parent/'Rtype.rzx'),[0x8842,*FLIPS],at,stop=args.stop);flush()
    assert desync is None,(frames,desync)
    result=dict(schema=1,scope=__doc__,frames=frames,desync=desync,draws=draws,text_draws=texts,levels=dict(levels),cells=cells,plots=plots,figures=list(figures.values()))
    args.out.write_text(json.dumps(result,separators=(',',':'))+'\n');print('PASS',frames,'frames;',draws,'draws;',len(cells),'cell variants;',len(plots),'plots;',len(figures),'whole object figures')
if __name__=='__main__':run()
