"""Actual pause/resume keys through converter output; native continuation/visibility.

Does not patch the pause sites in the test. Saves emulator frames while paused
and after resume; the unit oracle separately checks all ULA pixels and ABI/R.
"""
import json,os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]/'nexclash';sys.path[:0]=[str(ROOT)]
from nexclash import jnext as J
from publication_integrated import build

def run():
    os.environ.setdefault('NEXCLASH_JNEXT','/workspace/work/jnext-bin/root/usr/bin/jnext')
    out=Path('/workspace/work/r_type_pause_jnext');out.mkdir(exist_ok=True)
    _,nex,s=build('/workspace/work/r_type_integrated/peak.z80',out,'publication_tilemap.asm')
    script=J.Script(500);script.var('paused');script.var('resumed');script.var('copies')
    script.rule('on execute %d once do\n  press "caps+1"\nend\n'%s['hook_return'])
    script.rule('on execute 0x8B83 do\n  set paused = paused + 1\n  log "PAUSED TILE=${nextreg[0x6B]} IFF=${IFF1} SP=${SP}"\nend\n')
    script.rule('on execute 0x8B92 do\n  set resumed = resumed + 1\n  log "RESUMED TILE=${nextreg[0x6B]} IFF=${IFF1} SP=${SP}"\nend\n')
    script.rule('on execute %d do\n  set copies = copies + 1\nend\n'%s['hook_return'])
    script.at(30,'  release "caps+1"\n  screenshot "paused.png"\n  save_snapshot "paused.jns"\n')
    script.hold(40,['caps+2'],15)
    script.at(65,'  screenshot "resumed.png"\n  save_snapshot "resumed.jns"\n  log "TOTAL P=${paused} R=${resumed} C=${copies}"\n')
    script.exit_at(66)
    assert J.run_all([(str(nex),script.text(),str(out/'run'),100,'/workspace/scratch/cspect-next-2gb.img','/workspace/work/r_type_jnext_home')])==[0]
    records=J.records(str(out/'run'/'run.log'))
    p=[r for tag,r in records if tag=='PAUSED'];r=[r for tag,r in records if tag=='RESUMED'];t=[r for tag,r in records if tag=='TOTAL']
    assert len(p)>=1 and len(r)==1 and all(v['TILE']==0 for v in p) and r[0]['TILE']==0x8B,(p,r)
    assert p[0]['IFF']==r[0]['IFF']==0
    assert t[0]['P']>=1 and t[0]['R']==1 and t[0]['C']>1,t
    result=dict(pause_calls=len(p),paused=p[:1],resumed=r,totals=t)
    (out/'pause-jnext.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
