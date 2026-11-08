"""Experiment 5: what does the 8EF9 state know about the first update's draws?
Per level: first logged update's records against RAM at 8EF9 (same IX actor struct, same image); distinct
patterns of that update; how many would be covered by loading the lowest ids, and uploads needed if nothing is preloaded.
Run from nexclash: python ../specnext/reference/inferno/build/pipeline/probe_first_frame.py LEVEL CACHE_PREFIX
"""
import json
import pickle
import sys
from pathlib import Path
sys.path.insert(0, '.')
import nexclash.inferno as I

level, cache = sys.argv[1], sys.argv[2]
ref = Path('../specnext/reference/inferno')
states = pickle.loads(open('%s.%s' % (cache, level), 'rb').read())[0x8F7C]
store = I._cw_store(str(ref), level, cache)
index = I.index_tables({83: store[83]})
ram89, regs, frame = I.driver_boundary_state(ref / ('Inferno%s.rzx' % level))
patch = I.CopierWindowPatch(work=True)
for k, (ram, r, port) in enumerate(states[:40]):
    res = I.run_cw_window(patch, ram, r, phase=0, count0=0, store=store)
    p68 = res['dx'][2]
    if p68[0x3F4] and not p68[0x3F5]:
        break
log = I.capture_log(p68)
same_struct = sum(ram89[(x['ix'] + 4) & 65535] == x['image'] for x in log)
same_pos = sum(ram89[(x['ix'] + 2) & 65535] == x['y'] for x in log)
ids = set()
for x in log:
    if x['image'] in index:
        ids.update(c[3] for c in index[x['image']][2])
print(json.dumps(dict(level=level, first_logged_state=k, draws=len(log), image_at_8ef9=same_struct, y_at_8ef9=same_pos,
                      ids_first_update_all_chunks=len(ids), covered_by_lowest_64_ids=sum(i < 64 for i in ids))))
