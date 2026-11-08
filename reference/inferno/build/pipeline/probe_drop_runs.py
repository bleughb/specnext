"""Experiment 4: where do dropped updates come from? Per consecutive update of a level (first 2,000 frames):
slices, work T, how far the coroutine got (scene / dispatch / selection / done), new patterns.
Run from nexclash: python ../specnext/reference/inferno/build/pipeline/probe_drop_runs.py LEVEL CACHE_PREFIX > out.json
"""
import json
import pickle
import sys
sys.path.insert(0, '.')
import nexclash.inferno as I

level, cache = sys.argv[1], sys.argv[2]
states = pickle.loads(open('%s.%s' % (cache, level), 'rb').read())[0x8F7C]
store = I._cw_store('../specnext/reference/inferno', level, cache)
patch = I.CopierWindowPatch(work=True)
page = None
rows = []
for i, (ram, regs, port) in enumerate(states):
    n = I._cw_n(level, i)
    use = store if page is None else {**store, 82: page}
    res = I.run_cw_window(patch, ram, regs, phase=(n * 13) % I.CW_TICK, count0=(n * 37) & 255, store=use)
    got, matched, p68, live, scene = res['dx']
    page = res['sel']
    stage = 'done' if res['work_done'] else 'none' if not res['slices'] else 'select' if got else 'dispatch' if matched or scene else 'scene'
    rows.append(dict(i=i, stage=stage, slices=res['slices'], work=round(res['work_T']), wait=round(res['wait_T']),
                     draws=p68[0x3F4], chunks=page[I.SEL_N], new=page[I.SEL_NEW], ready=int(res['work_done'] and page[I.SEL_READY])))
print(json.dumps(rows))
