"""Capture the longest original ISR in a bounded RZX replay for timing probes.

The memory image is generated in work, never committed. This is NOT a whole-game
maximum: it scans only the first4000 frames of the supplied original recording.
"""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'nexclash'))
from nexclash.rzx import trace


def capture(path):
    state, start, best = None, 0, 0

    def at(pc, sim):
        nonlocal state, start, best
        if pc == 0xBE23:
            start = sim.registers[25]
            state = dict(registers=list(sim.registers),
                         banks=[list(b) for b in sim.memory.banks],
                         frame=sim.tracer.frame_index)
        elif state:
            elapsed = sim.registers[25] - start
            if elapsed > best:
                best = elapsed
                Path(path).write_text(json.dumps(dict(**state, T=elapsed)))
            state = None

    frames, desync = trace(str(HERE.parent / 'Rtype.rzx'), [0xBE23, 0xBE5C], at, stop=4000)
    assert frames == 4000 and desync is None, (frames, desync)
    return json.loads(Path(path).read_text())


def load():
    path = Path('/workspace/work/r_type_irq_max_state.json')
    return json.loads(path.read_text()) if path.exists() else capture(path)


if __name__ == '__main__':
    result = capture('/workspace/work/r_type_irq_max_state.json')
    print('frame', result['frame'], 'native T', result['T'])
