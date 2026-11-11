"""Capture the known 105-sprite peak at its copier entry, without another census.

Replays only to the already identified frame29405, once when the work fixture is
missing. Generated game banks/registers stay in work. No new coverage claim.
"""
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'nexclash'))
from nexclash.rzx import trace


def capture():
    out=Path('/workspace/work/r_type_peak_state.json')
    if out.exists():return out
    def at(pc,sim):
        if sim.tracer.frame_index==29405 and not out.exists():
            out.write_text(json.dumps(dict(frame=29405,banks=[list(b)for b in sim.memory.banks],
                                          registers=list(sim.registers),port7ffd=sim.memory.o7ffd)))
    frames,desync=trace(str(HERE.parent/'Rtype.rzx'),[0x8842],at,stop=29406)
    assert desync is None and out.exists(),(frames,desync)
    return out


if __name__=='__main__':print(capture())
