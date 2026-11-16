"""Exclusive live phase ledger, existing routes only; no renderer optimization.

Requires JNext1.2.0, the private read-only SD and the documented Python versions.
Uses a fresh, explicit peak29405/no-input recipe, not the missing old scratch
fixture/profile. Reconstructs all assets from checked-in originals and recipes.
Logs/captures/game bytes stay in work; only compact measurements belong in Git.
"""
import collections
import hashlib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]/'nexclash'
sys.path[:0] = [str(ROOT)]
from nexclash import jnext as J, pace, rzx
from publication_integrated import build

WORK = Path('/workspace/work/r_type_budget')
NAMES = {1:'figure_plot',2:'copy_hook',3:'shadow_clone',4:'pattern_preparation',
    5:'foreground_clear_restore',6:'original_copier',7:'postcopy_paper',
    8:'background_controller',9:'publication_raster_wait',10:'publication',
    11:'credit_debt_wait_return',12:'publication_payload',13:'render_lookup_bridge',
    14:'render_ID_checks',15:'successful_cell',16:'producer_resolver',
    17:'texture_stage',18:'IRQ_marker_span',19:'copier_row_setup_attr_shift',
    20:'copier_pixel_copy_clear_owner',21:'copier_pixel_scroll'}


def fixtures():
    WORK.mkdir(exist_ok=True)
    src = Path('/workspace/work/r_type_integrated/peak.z80')
    src.parent.mkdir(exist_ok=True)
    if not src.exists():
        rzx.cut(str(HERE.parent/'Rtype.rzx'),29405,2,str(src.with_suffix('.rzx')))
        rzx.extract(str(src.with_suffix('.rzx')),str(src))
    assert J.md5(str(src)) == '9cfed755be2d7ae90a3876ea617f87bf', 'different peak recipe'
    normalized = Path('/workspace/work/r_type_assets_normalized.json.gz')
    normalized.write_bytes((HERE/'continuation/assets.json.gz').read_bytes())
    decoded = Path('/workspace/work/r_type_review/decoded.bin')
    if not decoded.exists():
        from live_assets import reconstruct
        from nexclash import z80tonex as Z
        decoded.parent.mkdir(exist_ok=True)
        images = reconstruct(Z.Z80Snapshot(str(HERE.parent/'Rtype.z80')),
            dict(unpack_levels=[49,50,51,52,53,54,55,56,49]))
        decoded.write_bytes(b''.join(images))
    data = decoded.read_bytes()
    expected = json.loads((HERE/'continuation/identity-budget.json').read_text())['source']['decoded_sha256']
    assert hashlib.sha256(data).hexdigest() == expected
    Path('/workspace/work/r_type_decoded_assets.json').write_text(json.dumps(
        {str(i):list(data[(i+1)*65536:(i+2)*65536]) for i in range(9)},separators=(',',':')))
    programs = {'original':(src,{})}
    for tag,asm in [('resolved','publication_resolved.asm'),('static','publication_spritebulk.asm')]:
        _,nex,syms = build(src,WORK/tag,asm)
        programs[tag]=(nex,syms)
    return programs


def call_return(program, syms, label):
    from nexclash.recolour import nex_offsets
    data = program.read_bytes()
    off = nex_offsets(data)[12]
    # No runtime bytes changed: find the one actual assembled CALL's continuation.
    code = data[off:off+8192]
    pattern = b'\xCD'+syms[label].to_bytes(2,'little')
    matches = [i+0x2003 for i in range(len(code)-2) if code[i:i+3]==pattern]
    assert len(matches)==1, (label,matches)
    return matches[0]


def script(program, syms, profile):
    base = pace.script(str(program),profile,0x8649,100,1,not syms,2000,profile['state'])
    rules = []
    def rule(addr, text, condition=''):
        c = 'u >= 1 and u <= 100'+(' and '+condition if condition else '')
        # JNext may report an execute address again after an intervening IRQ.
        # Keep measurement intervals one-shot until their opposite boundary.
        for p,e in re.findall(r'PH P=(\d+) E=(\d+)',text):
            c += ' and bp%s == %d'%(p,1-int(e))
        rules.append('on execute %d when %s do\n%send\n'%(addr,c,text))
    def mark(p,e):
        return ('  log "PH P=%d E=%d U=${u} C=${CYCLE}"\n  set bp%d = %d\n'%(p,e,p,e)
                +('  set bcs = 0\n' if p==6 else ''))
    rule(0x8383,mark(18,1)+'  set birq = 1\n')
    rule(0xBE5D,mark(18,0)+'  set birq = 0\n','birq == 1')
    rule(0x8979,mark(8,1))
    rule(0x8656,mark(8,0))
    for pc in (0x8CFD,0x8D65,0x8DD3,0x8E29):
        rule(pc,mark(1,1)+'  set bplot = 1\n','birq == 0')
    for pc in (0x8D56,0x8DC4,0x8E1A,0x8E76):
        rule(pc,mark(1,0)+'  set bplot = 0\n','bplot == 1 and (F & 64) != 0 and birq == 0')
    # Basic-block boundaries inside the unchanged copier. This classifies its
    # actual elapsed instruction spans at each route's clock; no /8 assumption.
    for pc,kind in ((0x8846,19),(0x8869,19),(0x8881,20),(0x88E6,21)):
        rule(pc,'  log "CS K=%d U=${u} C=${CYCLE}"\n  set bcs = %d\n'%(kind,kind),
            'bp6 == 1 and birq == 0 and bcs != %d'%kind)
    if not syms:
        rule(0x8842,mark(6,1)+'  set bcopy = 1\n')
        rule(0x884A,mark(6,0)+'  set bcopy = 0\n','bcopy == 1 and (F & 64) != 0')
    else:
        rule(0x8842,mark(2,1)+'  set bhook = 1\n')
        rule(syms['hook_return'],mark(2,0)+'  set bhook = 0\n','bhook == 1')
        for p,start,end in [(3,'prepare','shadow_ready'),(4,'dynamic_patterns','clear_call'),
            (5,'clear_call','hook_copy_start'),(6,'hook_copy_start','copier_done'),
            (7,'copier_saved','prep_end'),(9,'prep_end','tail_begin'),
            (10,'tail_begin','hook_finish'),(11,'hook_finish','hook_return'),
            (12,'pstart','pend')]:
            # Close phases at an address before opening its successor there.
            rule(syms[end],mark(p,0),'bhook == 1')
            rule(syms[start],mark(p,1),'bhook == 1')
        rule(0x8EA2,mark(15,1)+'  set bcell = 1\n','bplot == 1 and birq == 0')
        for pc in (0x8D4C,0x8DBA,0x8E10,0x8E6C):
            rule(pc,mark(15,0)+'  set bcell = 0\n','bcell == 1 and birq == 0')
        if 'cell_resolve' in syms:
            rule(syms['cell_resolve'],mark(16,1),'bcell == 1 and birq == 0')
            rule(call_return(program,syms,'cell_resolve'),mark(16,0),'bcell == 1 and birq == 0')
            rule(syms['live_lookup'],mark(13,1),'bhook == 1 and birq == 0')
            rule(call_return(program,syms,'live_lookup'),mark(13,0),'bhook == 1 and birq == 0')
            rule(syms['live_lookup_code'],mark(14,1)+'  set blk = 1\n',
                'bhook == 1 and birq == 0 and mmu[0] == 56')
            rule(syms['resolved_render_code.valid'],mark(14,0)+mark(17,1)+'  set blk = 2\n',
                'blk == 1 and birq == 0 and mmu[0] == 56')
            for key in ('live_hit','live_miss'):
                rule(syms[key],mark(14,0)+'  set blk = 0\n',
                    'blk == 1 and birq == 0 and mmu[0] == 56')
                rule(syms[key],mark(17,0)+'  set blk = 0\n',
                    'blk == 2 and birq == 0 and mmu[0] == 56')
    # Same-address event order matters: ends must precede starts. hook_return is
    # outermost, so close bookkeeping before the complete-hook marker there.
    if syms:
        outer = 'on execute %d when u >= 1 and u <= 100 and bhook == 1 and bp2 == 1 do\n%s  set bhook = 0\nend\n'%(
            syms['hook_return'],mark(2,0))
        rules.remove(outer)
        rules.append(outer)
    variables=''.join('var %s = 0\n'%n for n in ('birq','bplot','bcopy','bhook','bcell','blk','bcs'))
    variables+=''.join('var bp%d = 0\n'%p for p in NAMES)
    return variables+base+''.join(rules)


def ledger(log, expected_updates=100, events=None):
    stack=[];last=None;rows=[];row=None;counts=collections.Counter();inclusive=collections.Counter();section=None
    for tag,r in J.records(str(log),('U','PH','CS')) if events is None else events:
        c=r['C']
        if row is not None and last is not None:
            assert c>=last, ('clock order',last,c)
            group=stack[-1][0] if stack else 'unclassified_game_and_edges'
            if group=='original_copier' and section is not None:group=section
            row[group] += c-last
        last=c
        if tag=='U':
            if row is not None:
                assert not stack, ('unclosed phases',stack,r['u'])
                rows.append(row)
            if r['u']==expected_updates+1:break
            row=collections.Counter()
        elif tag=='CS':
            assert stack and stack[-1][0]=='original_copier', (stack,r)
            section=NAMES[r['K']];counts[section]+=1
        elif r['E']:
            name=NAMES[r['P']];stack.append((name,c));counts[name]+=1
            if name=='original_copier':section=None
        else:
            name=NAMES[r['P']]
            assert stack and stack[-1][0]==name, ('phase imbalance',name,stack,r)
            _,start=stack.pop();inclusive[name]+=c-start
            if name=='original_copier':section=None
    assert len(rows)==expected_updates and not stack,(len(rows),stack)
    totals=sum(rows,collections.Counter())
    return dict(updates=expected_updates,total_s=sum(totals.values())/28e6,
        exclusive_mean_ms={k:v/28000/expected_updates for k,v in sorted(totals.items())},
        inclusive_mean_ms={k:v/28000/expected_updates for k,v in sorted(inclusive.items())},
        counts=dict(counts))


def ledger_check():
    events=[('U',dict(u=1,C=0)),('PH',dict(P=8,E=1,C=10)),
        ('PH',dict(P=6,E=1,C=20)),('PH',dict(P=6,E=0,C=60)),
        ('PH',dict(P=8,E=0,C=90)),('U',dict(u=2,C=100))]
    good=ledger(None,1,events)
    assert good['total_s']==100/28e6
    assert good['exclusive_mean_ms']=={'background_controller':40/28000,
        'original_copier':40/28000,'unclassified_game_and_edges':20/28000}
    broken=events[:4]+[('PH',dict(P=6,E=0,C=90))]+events[5:]
    try:ledger(None,1,broken)
    except AssertionError:pass
    else:raise AssertionError('duplicate/orphan end escaped ledger control')
    segments=[('U',dict(u=1,C=0)),('PH',dict(P=6,E=1,C=10)),
        ('CS',dict(K=21,C=20)),('PH',dict(P=18,E=1,C=30)),
        ('PH',dict(P=18,E=0,C=40)),('CS',dict(K=19,C=60)),
        ('PH',dict(P=6,E=0,C=80)),('U',dict(u=2,C=100))]
    got=ledger(None,1,segments)
    assert got['exclusive_mean_ms']=={'IRQ_marker_span':10/28000,
        'copier_pixel_scroll':30/28000,'copier_row_setup_attr_shift':20/28000,
        'original_copier':10/28000,'unclassified_game_and_edges':30/28000}


def smc_review(programs, profile, analyze=False):
    """Targeted write watch, not another full access/ISR/caller census."""
    import gzip
    from identity_budget import packed
    corpus=json.loads(gzip.decompress((HERE/'continuation/assets.json.gz').read_bytes()))
    sources=sorted({p['address']+i for p in corpus['plots'].values()
        for i in range(len(packed(p,corpus['cells'])))})
    spans=[]
    for a in sources:
        page=5 if a<0xC000 else 0
        if spans and spans[-1][1]+1==a and spans[-1][2]==page:
            spans[-1][1]=a
        else:spans.append([a,a,page])
    targets=[(a,a,4,1) for a in (0x8EDA,0x8EB1,0x8F0B,0x8F0C)]
    targets += [(a,a+2,4 if a<0xA000 else 5,2) for a in
        (0x8842,0x8CFD,0x8D65,0x8DD3,0x8E29,0x8EA2,0xBE26,0xBE52,0x8F21,0x8B80,0x8B8F)]
    targets += [(a,b,page,3) for a,b,page in spans]
    jobs=[]
    for tag in ('original','resolved'):
        program=programs[tag][0]
        sc=pace.script(str(program),profile,0x8649,100,1,tag=='original',2000,profile['state'])
        for a,b,page,kind in targets:
            sc+=('on write %d..%d page %d when u >= 1 and u <= 100 do\n'
                '  log "SMC K=%d U=${u} C=${CYCLE} A=${ADDR} V=${VALUE} P=${PC}"\nend\n')%(
                    a,b,page,kind)
        jobs.append((str(program),sc,str(WORK/('smc-'+tag)),2000,
            '/workspace/scratch/cspect-next-2gb.img',os.environ['NEXCLASH_JNEXT_HOME']))
    if not analyze:assert J.run_all(jobs)==[0,0]
    results={};sequences={}
    for tag in ('original','resolved'):
        before,_=pace.load(str(WORK/('phases-'+tag)))
        after,_=pace.load(str(WORK/('smc-'+tag)))
        fields=['C']+['S'+str(i) for i in range(380)]
        assert len(before)==len(after)==101 and all(a[k]==b[k]
            for a,b in zip(before,after) for k in fields), ('write-watch changed trajectory',tag)
        writes=[r for _,r in J.records(str(WORK/('smc-'+tag)/'run.log'),('SMC',))]
        native=[r for r in writes if r['K']==1]
        sequences[tag]=[(r['U'],r['A'],r['V'],r['P']) for r in native]
        results[tag]=dict(native_code_write_counts={hex(a):sum(r['A']==a for r in native)
            for a in sorted({r['A'] for r in native})},
            native_code_values={hex(a):sorted({r['V'] for r in native if r['A']==a})
                for a in sorted({r['A'] for r in native})},
            native_code_writer_PCs=sorted({hex(r['P']) for r in native}),
            writes_to_hook_site_bytes=sum(r['K']==2 for r in writes),
            writes_to_retained_packed_sources=sum(r['K']==3 for r in writes),
            control='all101 clocks and380 monitored bytes unchanged by targeted watch')
    return dict(scope='Only known native code controls, hook-site bytes and retained packed art; fresh100-update sample, not all levels/writers',
        packed_source_addresses=len(sources),packed_source_spans=len(spans),
        native_code_sequence_equal=sequences['original']==sequences['resolved'],results=results)


def run(analyze=False):
    ledger_check()
    os.environ.setdefault('NEXCLASH_JNEXT','/workspace/work/jnext-bin/root/usr/bin/jnext')
    os.environ.setdefault('NEXCLASH_JNEXT_HOME','/workspace/work/r_type_jnext_home')
    programs=fixtures()
    profile=dict(name='fresh peak29405/no input; all380 monitored bytes retained',start=[],
        dirs=[],fire=[],jump=[],restart=[],play_from=0,
        state=list(range(0x7A80,0x7B00))+list(range(0x8501,0x8501+28*9)))
    if not all((WORK/'pace'/tag/'run.log').exists() for tag in ('original','build')):
        assert not analyze, 'Missing uninstrumented controls; run without --analyze'
        controls=[]
        for tag,program_tag in [('original','original'),('build','resolved')]:
            program=programs[program_tag][0]
            controls.append((str(program),pace.script(str(program),profile,0x8649,100,1,
                tag=='original',2000,profile['state']),str(WORK/'pace'/tag),2000,
                '/workspace/scratch/cspect-next-2gb.img',os.environ['NEXCLASH_JNEXT_HOME']))
        assert J.run_all(controls)==[0,0]
    jobs=[]
    for tag,(program,syms) in programs.items():
        jobs.append((str(program),script(program,syms,profile),str(WORK/('phases-'+tag)),
            2000,'/workspace/scratch/cspect-next-2gb.img',os.environ['NEXCLASH_JNEXT_HOME']))
    if not analyze:
        codes=J.run_all(jobs)
        assert codes==[0]*3,codes
    results={tag:ledger(WORK/('phases-'+tag)/'run.log') for tag in programs}
    for tag,result in results.items():
        for required in ('figure_plot','background_controller','original_copier','IRQ_marker_span'):
            assert result['counts'].get(required,0)>0, (tag,required,'not measured')
    # Instrumentation must not change the already measured emulated trajectory.
    controls={}
    for tag,old in [('original','original'),('resolved','build')]:
        before,_=pace.load(str(WORK/'pace'/old));after,_=pace.load(str(WORK/('phases-'+tag)))
        assert len(before)==len(after)==101
        fields=['C']+['S'+str(i) for i in range(len(profile['state']))]
        assert all(a[k]==b[k] for a,b in zip(before,after) for k in fields), tag
        controls[tag]='all101 update clocks and380 monitor bytes identical with/without markers'
    monitors={}
    original,_=pace.load(str(WORK/'phases-original'))
    for tag in ('static','resolved'):
        build_rows,_=pace.load(str(WORK/('phases-'+tag)))
        diffs=collections.Counter()
        for a,b in zip(original,build_rows):
            for i,addr in enumerate(profile['state']):
                if a['S'+str(i)]!=b['S'+str(i)]:diffs[hex(addr)]+=1
        monitors[tag]=dict(monitored=380,difference_update_counts=dict(diffs),
            scope='Do not claim all RAM equality; retain IRQ/star counter differences explicitly')
    orig=results['original']['total_s'];live=results['resolved']['total_s']
    smc=smc_review(programs,profile,analyze)
    windows={}
    for tag in programs:
        updates,cnt=pace.load(str(WORK/('phases-'+tag)))
        sec=(updates[-1]['C']-updates[0]['C'])/28e6
        windows[tag]=dict(steady_play_rates=pace.rates(cnt,updates[0]['F']),
            whole_window_FE_writes=updates[-1]['BP']-updates[0]['BP'],
            whole_window_FE_rate=(updates[-1]['BP']-updates[0]['BP'])/sec)
    e=results['resolved']['exclusive_mean_ms']
    pipeline=sum(e[k] for k in ('original_copier','copier_pixel_copy_clear_owner',
        'copier_pixel_scroll','copier_row_setup_attr_shift','shadow_clone',
        'foreground_clear_restore','postcopy_paper'))
    deficit=(live-1.02*orig)*10
    result=dict(scope=__doc__,snapshot_md5=J.md5(str(programs['original'][0])),
        program_md5={k:J.md5(str(p)) for k,(p,_) in programs.items()},profile=profile,
        instrumentation_controls=controls,results=results,state_monitors=monitors,
        self_modification=smc,
        sound_IRQ_windows=windows,
        replacement_budget=dict(display_pipeline_exclusive_ms=pipeline,
            identity_checks_and_bridge_ms=sum(e[k] for k in
                ('producer_resolver','render_ID_checks','render_lookup_bridge')),
            conditional_new_work_plus_changed_waits_ms=pipeline-deficit,
            status='Gross removable-work hypothesis only. Prove consumers and price retained effects, new background work and changed IRQ/waits before any replacement.'),
        ledger_controls='nested phases conserve elapsed time; duplicate/orphan end negative caught; copier sections exclude nested IRQ spans',
        live_penalty_percent=100*(live/orig-1),required_saving_ms_per_update=(live-1.02*orig)*10,
        limits=['fresh fixture/profile; not exact reproduction of old10.75% trial',
            'all markers fire before instructions; omitted boundary instructions remain in parent/residual',
            'IRQ marker excludes IM2 acceptance and final RET, charged to parent/residual',
            'inclusive phases overlap: use exclusive ledger for sums',
            '99 copier/controller calls in100 probe intervals in every route; native game-over path included',
            'static preexpanded remains a cost control, not live painting',
            'no full RAM/R/IRQ/RGB/sound or full-recording verification claim'])
    (HERE/'continuation/live-budget.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='profile'},indent=2))


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--analyze',action='store_true',help='analyze retained logs without starting JNext')
    run(ap.parse_args().analyze)
