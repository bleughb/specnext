"""Play a build in CSpect for inspection (owner's test recipe, 2026-11-17).

    py -3 sweep.py NEX OUTDIR [--steps N] [--every K]

Starts a game from the title, makes the ship invulnerable (POKE 37362,201: 91F2 = RET), moves it
down into the lower two-thirds of the screen and then sweeps it up and down (keys 3 up, 4 down)
while firing (5) the whole time, which reliably hits level 1's power-up carrier. A screenshot
every K steps goes to OUTDIR/pNNNN.png. CSpect (Builder, MCP) only.
"""
import argparse
import sys
from pathlib import Path

import emu
import smoke


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('nex')
    ap.add_argument('out')
    ap.add_argument('--steps', type=int, default=400)
    ap.add_argument('--every', type=int, default=1)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob('p*.png'):
        f.unlink()
    cs = emu.CSpect()
    cs.text('clear_breakpoint', all=True)
    cs.text('load_nex', path=str(Path(a.nex).resolve()))
    cs.run_to(smoke.TITLE, timeout_ms=60000)
    cs.run_to(smoke.KEYS, timeout_ms=60000)
    cs.run_to(emu.IRQ)
    cs.text('run')
    cs.text('press_keys', keys='5', hold_frames=6)
    cs.run_to(emu.PROBE, timeout_ms=60000)          # in play
    cs.text('write_memory', address='$91F2', data='C9')
    cs.text('run')
    for _ in range(6):
        cs.text('press_keys', keys='4+5', hold_frames=3, gap_frames=0)
    pat = ['4+5'] * 7 + ['3+5'] * 7
    for i in range(a.steps):
        cs.text('press_keys', keys=pat[i % len(pat)], hold_frames=3, gap_frames=0)
        if i % a.every == 0:
            cs.screenshot(out / ('p%04d.png' % i))
    print('sweep: %d steps, screenshots in %s' % (a.steps, out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
