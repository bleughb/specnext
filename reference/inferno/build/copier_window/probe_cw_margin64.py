"""CW_WKM over all 64 half-T CTC phases: per slice, wall T from its end to the next OUT (or 9907),
plus window/frame errors, on a few states per level (those with the most slices in a 1/25 sample)."""
import sys, pickle, json
sys.path.insert(0, '.')
import nexclash.inferno as I
CACHE = 'C:/Users/micro/AppData/Local/Temp/claude/6237a019316583e8/40a53b24-c723-4977-82ff-466707bedd45/scratchpad/cwst.'
patch = I.CopierWindowPatch(work=True)
holder = []
orig_init = I.CopierWorkMemory.__init__
def init(self, *a, **k):
    orig_init(self, *a, **k)
    holder.append(self)
I.CopierWorkMemory.__init__ = init
out = {'runs': 0, 'errors': [], 'margin_min': None, 'slices': 0}
gaps = []
for lv in '123456':
    d = pickle.loads(open(CACHE + lv, 'rb').read())[0x8F7C]
    store = I._cw_store('../specnext/reference/inferno', lv, CACHE[:-1])   # so the dispatch stage runs
    pick = []
    for k in range(0, len(d), 25):
        ram, regs, port = d[k]
        holder.clear()
        res = I.run_cw_window(patch, ram, regs, phase=0, count0=(k * 37) & 255, store=store)
        pick.append((res['slices'], k))
    for _, k in sorted(pick)[-2:]:
        ram, regs, port = d[k]
        for j in range(64):
            holder.clear()
            res = I.run_cw_window(patch, ram, regs, phase=j / 2, count0=(k * 37 + j) & 255, frame=(j % 16 == 0), store=store)
            out['runs'] += 1
            errs = res['errors'] + (res['frame']['errors'] if res['frame'] else [])
            if errs:
                out['errors'].append([lv, k, j / 2, errs[:2]])
            mem = holder[0]
            outs = [t for t, v in mem.outs]
            end9907 = res['d9907'] + res['o9907']
            for s, l in res['work_spans']:
                e = s + l
                out['slices'] += 1
                gaps.append(min([t for t in outs if t > e] + [end9907]) - e)
gaps.sort()
out['margin_min'] = [round(g) for g in gaps[:5]]
print(json.dumps(out))
