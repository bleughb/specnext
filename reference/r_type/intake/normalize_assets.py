"""Normalize the retained producer capture without another recording pass.

Native owner and object identifiers jointly separate adjacent/projectile figures.
Signed8-bit cell positions unwrap off-screen coordinates before composing parts.
"""
import collections,gzip,json
from pathlib import Path

def normalize(raw):
    figures={};usedplots=set()
    for f in raw['figures']:
        groups=collections.defaultdict(list)
        for serial,part in enumerate(f['parts']):
            if not 0<part['owner']<0xDC:continue
            p=dict(part);p['x']=p['x']-2048 if p['x']>=1024 else p['x'];p['y']=p['y']-2048 if p['y']>=1024 else p['y']
            # A low owner flag can be shared by many independent shots. Only an
            # actual nine-byte object authorizes joining separate plot calls.
            identity=tuple(p['object'])if p['object'][0]=='object'else('draw',serial)
            groups[(p['owner'],identity)].append(p)
        for parts in groups.values():
            x=min(p['x']for p in parts);y=min(p['y']for p in parts)
            for p in parts:p['dx']=p['x']-x;p['dy']=p['y']-y
            k=json.dumps([f['level'],[(p['plot'],p['dx'],p['dy'],p['flip'])for p in parts]],separators=(',',':'))
            if k in figures:figures[k]['count']+=f['count']
            else:figures[k]=dict(level=f['level'],count=f['count'],parts=parts)
            usedplots.update(p['plot']for p in parts)
    plots={k:v for k,v in raw['plots'].items()if k in usedplots};usedcells={c for p in plots.values()for x,y,c in p['cells']}
    result={k:v for k,v in raw.items()if k not in ('figures','plots','cells')}
    result.update(cells={k:v for k,v in raw['cells'].items()if k in usedcells},plots=plots,figures=list(figures.values()),
        normalization='join only actual9-byte object+owner; other plots stay whole individually; signed positions; owner1..DB')
    return result

if __name__=='__main__':
    raw=json.loads(Path('/workspace/work/r_type_assets.json').read_text());data=normalize(raw)
    out=Path('/workspace/work/r_type_assets_normalized.json.gz');out.write_bytes(gzip.compress(json.dumps(data,separators=(',',':')).encode(),mtime=0))
    sizes=[]
    for f in data['figures']:
        sizes.append((max(p['dx']+data['plots'][p['plot']]['w']for p in f['parts']),max(p['dy']+data['plots'][p['plot']]['h']for p in f['parts'])))
    print('normalized:',len(data['cells']),'cells;',len(data['plots']),'plots;',len(data['figures']),'whole figures;',out.stat().st_size,'bytes')
    print('max whole figure dimensions',max(w for w,h in sizes),max(h for w,h in sizes),'large count',sum(w>320 or h>192 for w,h in sizes))
