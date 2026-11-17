"""Which figures the original draws behind scenery (README.md).

    py -3 behind.py [--frames N] [--out FILE]
    py -3 behind.py --flags [--min UPDATES]     rewrite ../behind_flags.asm from the last scan

Replays the full recording (Rtype.rzx) in the Python emulator. The original gives each 8x8 cell one
owner; when a figure's plot reaches a cell the scenery owns (owner map 7E00 = FF, tested at 8ED6), the
scenery wins and that cell of the figure is not drawn. Per family (registry r_type_figures.json) this
counts the updates in which that happened and the cells hidden. A family hidden in many updates comes
out from behind scenery; one or two updates is a brush against a wall. The result goes to
RTYPE_WORK/behind.json and the list is printed. Slow: the whole recording takes a long time.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import rtenv

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT.parent/'nexclash')]
from nexclash import simrun    # noqa: E402

PLOTS = (0x8CFD, 0x8D65, 0x8DD3, 0x8E29)
TEST = 0x8ED7                   # after LD A,(DE): A = owner of the cell being tried


def scan(frames=None):
    mem = []
    state = dict(src=None, frame=0)
    hidden = defaultdict(lambda: dict(updates=set(), cells=0, first=None))

    class Hooks:
        def on_sim(self, sim):
            mem[:] = [sim.memory]
            self.R = sim.registers

        def on_frame(self, n):
            state['frame'] = n

        def before(self, pc):
            R = self.R
            if pc in PLOTS:
                state['src'] = (R[6] << 8) | R[7]
            elif pc == TEST and R[0] == 0xFF and state['src'] is not None:
                m = mem[0]
                if m[0x8EBF] != 0x60:
                    return          # the plotter is drawing scenery itself
                key = (m[0x719C], state['src'], m[0x8EB1])
                h = hidden[key]
                h['updates'].add(state['frame'] // 3)
                h['cells'] += 1
                if h['first'] is None:
                    h['first'] = state['frame']

    simrun.play_rzx(str(ROOT/'reference/r_type/Rtype.rzx'), Hooks(), frames)
    return hidden


def families():
    reg = json.load(open(ROOT/'reference/r_type/colours/r_type_figures.json'))
    out = {}
    for fid, f in reg['families'].items():
        for g in f['graphics']:
            out.setdefault((str(f['level']), g.upper()), []).append((fid, f.get('layer')))
    return out


FLAGS = HERE.parent/'behind_flags.asm'


def write_flags(rows, minimum=50):
    """behind_flags.asm: every graphic of each family the original hides behind scenery in at least
    `minimum` updates. The sprite build keeps those figures in the ULA, under Layer 2."""
    reg = json.load(open(ROOT/'reference/r_type/colours/r_type_figures.json'))
    fam = families()
    best = defaultdict(int)
    for r in rows:
        for (lv, g), lst in fam.items():
            if g == r['graphic'] and lv == 'LEVEL' + chr(r['level_byte']):
                for fid, _ in lst:
                    best[fid] = max(best[fid], r['updates'])
    keep = sorted((f for f, n in best.items() if n >= minimum),
                  key=lambda f: (reg['families'][f]['level'], -best[f]))
    lines = ['; R-Type sprite build: figures drawn BEHIND the scenery, as in the original.',
             '; Every other figure is a hardware sprite in front of the scenery (l2scroll.asm LORDER).',
             '; A flagged figure is not made a sprite: the game draws it in the ULA, under Layer 2, so the',
             '; scenery hides it exactly as the original does (8x8 cells).',
             ';',
             ';     FLAG level, graphic        level = the level byte at 719C ("1" = 0x31 ... "8" = 0x38)',
             ';',
             '; Edit by hand: delete or comment out a line to bring that figure in front, or add a line',
             '; (graphics are in colours/r_type_figures.json, families -> graphics). Generated first by',
             '; tools/behind.py --flags --min %d from a scan of the original (updates hidden).' % minimum,
             '']
    for f in keep:
        fa = reg['families'][f]
        lv = ord(fa['level'][-1])
        lines.append('; %s  hidden %d updates  figures %s' % (f, best[f], ', '.join(fa['figures'])))
        for g in fa['graphics']:
            lines.append('        FLAG 0x%02X, 0x%s' % (lv, g.upper()))
    FLAGS.write_text(chr(10).join(lines)+chr(10))
    return keep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--frames', type=int)
    ap.add_argument('--out')
    ap.add_argument('--flags', action='store_true')
    ap.add_argument('--min', type=int, default=50)
    a = ap.parse_args(argv)
    if a.flags:
        keep = write_flags(json.load(open(a.out or rtenv.OUT/'behind.json')), a.min)
        print('%d families flagged -> %s' % (len(keep), FLAGS))
        return 0
    hidden = scan(a.frames)
    fam = families()
    rows = []
    for (level, src, ink), h in hidden.items():
        g = '%04X' % src
        ids = [fid for (lv, gg), lst in fam.items() if gg == g for fid, _ in lst
               if lv == 'LEVEL' + chr(level)]
        rows.append(dict(level_byte=level, graphic=g, ink=ink, families=ids,
                         updates=len(h['updates']), cells=h['cells'], first_frame=h['first']))
    rows.sort(key=lambda r: (-r['updates'], r['level_byte']))
    out = Path(a.out) if a.out else rtenv.OUT/'behind.json'
    out.write_text(json.dumps(rows, indent=1)+'\n')
    for r in rows:
        print('level byte %3d  graphic %s ink %d  updates %4d  cells %5d  first frame %6d  %s'
              % (r['level_byte'], r['graphic'], r['ink'], r['updates'], r['cells'], r['first_frame'],
                 ','.join(r['families']) or '?'))
    print('written', out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
