"""Bounded integrated ABI, publication and freshness diagnostic in JNext.

No original-vs-hook full-RAM or supplied-R equivalence claim. Compares the actual
copier's returned registers to the actual hook return, and slot2/source RAM at
tail versus return. Exact log observations; JNS saves are frame-boundary captures.
"""
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]/'nexclash'
sys.path[:0]=[str(ROOT),str(HERE)]
from nexclash import jnext as J,recolour
from publication_integrated import build,OUT


def run():
    import os
    os.environ.setdefault("NEXCLASH_JNEXT", "/workspace/work/jnext-bin/root/usr/bin/jnext")
    src,nex,syms=build()
    regs=('AF','BC','DE','HL','IX','IY','AF2','BC2','DE2','HL2','I','IM')
    jobs=[]
    for name,mode in [('dma',1),('default',2),('bad-restore',1)]:
        folder=OUT/('check-'+name);folder.mkdir(exist_ok=True)
        code=bytearray(nex.read_bytes());off=recolour.nex_offsets(code)[12]
        code[off+syms['integrated_policy']+1-0x2000]=mode
        if name=='bad-restore':
            a=off+syms['restore_control']-0x2000
            code[a:a+4]=bytes.fromhex('fd210000')
        program=folder/'diagnostic.nex';program.write_bytes(code)
        s=J.Script(500);s.var('u');s.var('n');s.var('low',0x3D00)
        s.rule('on execute 0x8649 do\n  set u = u + 1\n  if u == 101 then\n    exit 0\n  end\nend\n')
        labels=[('ENTRY','hook_entry'),('PREP','prepare'),('READY','shadow_ready'),('COPY','copier_done'),
                ('TAIL','tail_begin'),('BEGIN','pstart'),('END','pend'),('RETURN','hook_return'),('IRQ','irq_in')]
        for tag,label in labels:
            extra=' '.join(k+'=${'+k+'}'for k in regs) if tag in ('COPY','RETURN') else ''
            body='  log "%s U=${u} C=${CYCLE} SP=${SP} IFF=${IFF1} M6=${mmu[6]} LOW=${low} %s"\n'%(tag,extra)
            if tag in ('TAIL','RETURN'):
                body+='  log "RAM U=${u} C=${CYCLE}"\n'
                for a,n in [(0x5B00,1280),(0x6000,4096),(0x7000,4096),(0x8000,4096),(0x9000,4096),(0xA000,4096),(0xB000,4096),(0xE000,4096),(0xF000,4096)]:
                    body+='  dump_mem %d %d\n'%(a,n)
            s.rule('on execute %d do\n%send\n'%(syms[label],body))
        s.rule('on execute 0x2000..0x37FF do\n  if SP < low then\n    set low = SP\n  end\nend\n')
        s.exit_at(1000)
        jobs.append((str(program),s.text(),str(folder),1100,'/workspace/scratch/cspect-next-2gb.img','/workspace/work/r_type_jnext_home'))
    codes=J.run_all(jobs);assert codes==[0]*3,codes
    results=[]
    import re
    dump=re.compile(r'\] ([0-9A-Fa-f]{4}): ((?:[0-9A-Fa-f]{2} ?)+)\s*\[client')
    for name,_ in [('dma',1),('default',2),('bad-restore',1)]:
        log=OUT/('check-'+name)/'run.log'
        events=J.unwrap([dict(tag=tag,**r)for tag,r in J.records(str(log))])
        events=[r for r in events if r['tag']!='RAM']
        copies=[r for r in events if r['tag']=='COPY'];returns=[r for r in events if r['tag']=='RETURN']
        assert len(copies)==len(returns) and len(returns)>=90,(name,len(copies),len(returns))
        bad=[(i,k,c[k],r[k])for i,(c,r)in enumerate(zip(copies,returns))for k in regs if c[k]!=r[k]]
        entries=[r for r in events if r['tag']=='ENTRY']
        assert all(r['IFF']==1 and r['M6']==e['M6'] and r['SP']==e['SP'] for e,r in zip(entries,returns)), 'return mapping/stack/IFF'
        if name=='bad-restore':assert any(x[1]=='IY'for x in bad),'negative escaped'
        else:assert not bad,bad[:10]
        critical=[];pending=None;tail=None
        for e in events:
            if e['tag']=='PREP':pending=e
            elif e['tag']=='READY':
                critical.append((pending['C'],e['C']));pending=None
            elif e['tag']=='TAIL':tail=e
            elif e['tag']=='RETURN':critical.append((tail['C'],e['C']))
        assert not any(a<e['C']<b for e in events if e['tag']=='IRQ' for a,b in critical),'IRQ in critical section'
        # RAM dump pairs are exact execute-time observations, not deferred snapshots.
        memories=[];mem=None
        for line in log.read_text().splitlines():
            if '] RAM 'in line:
                mem={};memories.append(mem)
            m=dump.search(line)
            if m and mem is not None:
                a=int(m[1],16)
                mem.update((a+i,b)for i,b in enumerate(bytes.fromhex(m[2])))
        assert len(memories)==2*len(returns),(name,len(memories),len(returns))
        diffs=[]
        for i in range(0,len(memories),2):
            a,b=memories[i:i+2]
            diffs.extend((i//2,k,a[k],b.get(k))for k in a if a[k]!=b.get(k))
        assert not diffs,(name,diffs[:10])
        ages=[(r['C']-e['C'])/28000 for e,r in zip(entries,returns)]
        intervals=[(b['C']-a['C'])/28000 for a,b in zip(returns,returns[1:])]
        result=dict(variant=name,returns=len(returns),register_mismatches=len(bad),checked_registers=regs,
                    tail_to_return_ram_bytes=len(memories[0]),ram_mismatches=len(diffs),
                    max_hook_ms=max(ages),max_publication_interval_ms=max(intervals),
                    min_private_sp=min(r['LOW']for r in returns),critical_irq_count=0,
                    limits=['return R bridge tested separately without IRQ; in-IRQ R consumers unproven','C000..DFFF not compared here','IRQ effects before tail not checked against original','no text hooks or recolour; not an engine'])
        results.append(result);print(result,flush=True)
    (OUT/'integration-check.json').write_text(json.dumps(results,indent=2)+'\n')


if __name__=='__main__':run()
