"""Source-only catalogue and4bpp texture compiler for the live colour prototype.

Public catalogue stores addresses, original-unpacker recipes and object geometry,
never graphic bytes. Art tables are reconstructed from the owner's snapshot.
"""
import gzip,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]/'nexclash';sys.path[:0]=[str(ROOT)]
from nexclash import z80tonex as Z
TABLE_PAGES=32
SLOTS=16384
POOL_PAGES=160
PALETTE=[0xE3,2,0xA0,0xA2,0x14,0x16,0xB4,0xB6,0,3,0xE0,0xE7,0x1C,0x1F,0xFC,0xFF]

def rowkey(level,addr,ink,byte):
    return 'L%02X:%04X:I%X:B%02X'%(level,addr,ink,byte)

def hashkey(level,addr,ink):
    return (addr+(addr&255)*12+level*257+ink*273)&(SLOTS-1)

def catalogue():
    raw=json.loads(gzip.decompress(Path('/workspace/work/r_type_assets_normalized.json.gz').read_bytes()))
    snap=Z.Z80Snapshot(str(HERE.parent/'Rtype.z80'))
    initial=bytes(snap.read(a)or 0 for a in range(65536))
    dec=json.loads(Path('/workspace/work/r_type_decoded_assets.json').read_text())
    images=[initial]+[bytes(dec[str(i)])for i in range(len(dec))]
    cells=[];ids={}
    for key,c in sorted(raw['cells'].items()):
        addr=c['address'];bits=bytes(c['bits']);recipe=next(i for i,data in enumerate(images)if data[addr+1:addr+9]==bits)
        ids[key]=len(cells);cells.append([c['level'],addr,c['ink'],recipe])
    plots=[];pids={}
    for key,p in sorted(raw['plots'].items()):
        pids[key]=len(plots);plots.append([p['level'],p['address'],p['w'],p['h'],[[x,y,ids[c]]for x,y,c in p['cells']]])
    figures=[[f['level'],f['count'],[[pids[p['plot']],p['dx'],p['dy'],p['flip']]for p in f['parts']]]for f in raw['figures']]
    meta=dict(schema=1,unpack_levels=[49,50,51,52,53,54,55,56,49],cells=cells,plots=plots,figures=figures,
        source_md5=hashlib.md5((HERE.parent/'Rtype.z80').read_bytes()).hexdigest(),palette=PALETTE,
        scope='Recorded source/ink variants, whole figures grouped by actual native9-byte object+owner; independent whole plots otherwise')
    Path('/workspace/work/r_type_assets_meta.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
    return meta,images

def reconstruct(snapshot,meta):
    from decode_assets import decode
    images=[bytes(snapshot.read(a)or 0 for a in range(65536))];previous=None
    for level in meta['unpack_levels']:
        data,previous=decode(snapshot,dict(IX=0xC4AE,level=level),previous);images.append(data)
    return images

def group(bits,ink,level,addr,cmap):
    pixels=[]
    for y,b in enumerate(bits):
        key=rowkey(level,addr+1+y,ink,b);paint=cmap.get(key)
        if paint:
            assert paint[0]==b and paint[1]==1 and len(paint[2])==8,('invalid pixel map',key)
            assert all(isinstance(v,int)and 0<=v<=15 for v in paint[2]),('4bpp palette value',key)
        for x in range(8):
            colour=(paint[2][x]or ink)if paint else ink
            clear=paint[3]if paint and len(paint)>3 else 0
            pixels.append(colour if b&(128>>x)and not(clear&(128>>x))else 0)
    out=bytearray()
    for flip in range(4):
        for y in range(8):
            row=[]
            for x in range(8):row.append(pixels[(7-y if flip&2 else y)*8+(7-x if flip&1 else x)])
            out.extend((row[x]<<4)|row[x+1]for x in range(0,8,2))
    return bytes(out)

def compile(meta,images,cmap=None):
    cmap=cmap or {};table=bytearray(SLOTS*16);pool=bytearray(POOL_PAGES*8192);groups={};probes=[];validkeys=set()
    for level,addr,ink,recipe in meta['cells']:
        bits=images[recipe][addr+1:addr+9];assert len(bits)==8
        validkeys.update(rowkey(level,addr+1+y,ink,b)for y,b in enumerate(bits))
        tex=group(bits,ink,level,addr,cmap)
        if tex not in groups:
            index=len(groups);assert(index+1)*128<=len(pool),'paint texture pool full'
            groups[tex]=index;pool[index*128:index*128+128]=tex
        index=groups[tex];slot=hashkey(level,addr,ink);n=0
        while table[slot*16]or table[slot*16+1]:slot=(slot+1)&(SLOTS-1);n+=1;assert n<SLOTS,'paint lookup table full'
        entry=addr.to_bytes(2,'little')+bytes([level,ink])+bits+index.to_bytes(2,'little')+bytes([int(any(tex)),0])
        table[slot*16:slot*16+16]=entry;probes.append(n)
    assert not set(cmap)-validkeys,('map contains unknown source-byte keys',sorted(set(cmap)-validkeys)[:4])
    banks={32+i:bytes(table[i*16384:(i+1)*16384])for i in range(16)}
    banks.update({48+i:bytes(pool[i*16384:(i+1)*16384])for i in range(80)})
    summary=dict(cells=len(meta['cells']),groups=len(groups),pool_bytes=len(groups)*128,table_bytes=len(table),max_probe=max(probes),mean_probe=sum(probes)/len(probes))
    return banks,summary

if __name__=='__main__':
    meta,images=catalogue();banks,summary=compile(meta,images)
    Path('/workspace/work/r_type_live_compiler.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)

def compile_direct(meta,images,cmap=None):
    """Exact source-address dispatch; shared raw guard and sparse ink vectors."""
    cmap=cmap or {};ram=bytearray(192*8192);records={};groups={};validkeys=set()
    for level,addr,ink,recipe in meta['cells']:
        bits=images[recipe][addr+1:addr+9];assert 48<=level<=57 and 0xA000<=addr<0xE000
        validkeys.update(rowkey(level,addr+1+y,ink,b)for y,b in enumerate(bits))
        tex=group(bits,ink,level,addr,cmap)
        if tex not in groups:
            index=len(groups);assert(index+1)*128<=137*8192,'paint texture pool full'
            groups[tex]=index;offset=55*8192+index*128;ram[offset:offset+128]=tex
        index=groups[tex]|(0x8000 if any(tex)else 0)
        record=records.setdefault((level,addr),dict(bits=bits,inks={}))
        assert record['bits']==bits,'source changes within one level; requires a different key scheme'
        record['inks'][ink]=index
    cursor=4
    for (level,addr),record in sorted(records.items()):
        inks=record['inks']
        if len(inks)==1:
            ink,index=next(iter(inks.items()));data=record['bits']+bytes([ink])+index.to_bytes(2,'little')
        else:
            data=record['bits']+bytes([128])+b''.join(inks.get(i,65535).to_bytes(2,'little')for i in range(16))
        if cursor%8192+len(data)>8192:cursor=(cursor+8191)&~8191
        assert cursor+len(data)<=15*8192,'source-variant table full'
        offset=40*8192+cursor;ram[offset:offset+len(data)]=data
        offset=(level-48)*32768+(addr-0xA000)*2;ram[offset:offset+2]=(cursor//4).to_bytes(2,'little')
        cursor=(cursor+len(data)+3)&~3
    assert not set(cmap)-validkeys,('unknown source-byte keys',sorted(set(cmap)-validkeys)[:4])
    banks={32+i:bytes(ram[i*16384:(i+1)*16384])for i in range(96)}
    summary=dict(cells=len(meta['cells']),source_records=len(records),groups=len(groups),pool_bytes=len(groups)*128,
        direct_bytes=40*8192,record_bytes=cursor,pool_capacity=137*8192,lookup_kind='direct address + guarded ink variant')
    return banks,summary
