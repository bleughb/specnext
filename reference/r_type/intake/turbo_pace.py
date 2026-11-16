"""Relaxed-equivalence trial (owner decision 2026-11-15): main loop at 28MHz.

Same fresh peak29405/no-input fixture and 100-update probe as live_budget.py.
Compares the original, the cached-producer route and the same route with
RT_TURBO (main loop returns from the copier hook at 28MHz; the native ISR and
its beeper effects stay at 3.5MHz). Original slowdown is intentionally not kept,
so a faster-than-original result is expected and accepted. State is reported,
not required to match: R and IRQ arrival points legitimately differ.
Generated programs/logs stay in work.
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]/'nexclash'
sys.path[:0] = [str(ROOT)]
from nexclash import jnext as J, pace
import live_budget as L
from publication_integrated import build

WORK = Path('/workspace/work/r_type_turbo')
CARD = '/workspace/scratch/cspect-next-2gb.img'


def run(analyze=False):
    os.environ.setdefault('NEXCLASH_JNEXT_HOME', '/workspace/work/r_type_jnext_home')
    WORK.mkdir(exist_ok=True)
    programs = L.fixtures()
    programs.pop('static')
    src = programs['original'][0]
    _, nex, syms = build(src, WORK/'turbo', 'publication_turbo.asm')
    programs['turbo'] = (nex, syms)
    profile = dict(name='fresh peak29405/no input', start=[], dirs=[], fire=[], jump=[],
        restart=[], play_from=0,
        state=list(range(0x7A80, 0x7B00))+list(range(0x8501, 0x8501+28*9)))
    jobs = [(str(p), pace.script(str(p), profile, 0x8649, 100, 1, tag == 'original', 4000,
                profile['state']), str(WORK/tag), 4000, CARD, os.environ['NEXCLASH_JNEXT_HOME'])
            for tag, (p, _) in programs.items()]
    if not analyze:
        codes = J.run_all(jobs)
        assert codes == [0]*len(jobs), codes
    rows = {}
    for tag in programs:
        updates, cnt = pace.load(str(WORK/tag))
        assert len(updates) == 101, (tag, len(updates))
        rows[tag] = dict(updates=updates, cnt=cnt,
            total_s=(updates[-1]['C']-updates[0]['C'])/28e6,
            frames=updates[-1]['F']-updates[0]['F'])
    orig = rows['original']
    result = dict(scope=__doc__, program_md5={k: J.md5(str(p)) for k, (p, _) in programs.items()})
    for tag, r in rows.items():
        frames = [b['F']-a['F'] for a, b in zip(r['updates'], r['updates'][1:])]
        diffs = sum(any(a['S%d' % i] != b['S%d' % i] for i in range(len(profile['state'])))
                    for a, b in zip(orig['updates'], r['updates']))
        result[tag] = dict(total_s=r['total_s'],
            penalty_percent=100*(r['total_s']/orig['total_s']-1),
            updates_per_s=100/r['total_s'],
            frames_per_update=dict((n, frames.count(n)) for n in sorted(set(frames))),
            updates_with_state_difference=diffs,
            rates=pace.rates(r['cnt'], r['updates'][0]['F']))
    out = WORK/'turbo-pace.json'
    out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'scope'}, indent=2))


if __name__ == '__main__':
    run('--analyze' in sys.argv)
