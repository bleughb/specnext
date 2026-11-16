"""Whole-game smoke test of the full build (README.md).

    py -3 smoke.py [NEX] [--updates 200] [--emulator auto|cspect|jnext]

Default NEX: the full build made by `l2scroll.py --full` (rebuilt first unless a NEX is given).
Checks, each a FAIL when it does not happen:
  1. the technical specification screen is followed by the title loop (7796, keys polled at 77D6)
     with no reset (PC 0);
  2. fire ('5') at the title starts a game (main loop 8649 reached);
  3. --updates game updates run: none slower than 6 frames and at most a quarter slower than 3
     (the first two updates, still at the title's speed, are not counted).
Exit status 1 on any FAIL. Screenshots of the title and of play go to RTYPE_WORK/r_type_l2scroll/smoke/.
"""
import argparse
import sys
from pathlib import Path

import rtenv
import emu

TITLE = 0x7796
KEYS = 0x77D6       # the title's key-polling loop (after the logo is drawn)


def cspect(nex, updates, out):
    cs = emu.CSpect()
    cs.text('clear_breakpoint', all=True)
    cs.text('load_nex', path=str(Path(nex).resolve()))
    cs.text('set_breakpoint', address='$0000')               # a reset stops here
    cs.run_to(TITLE, timeout_ms=60000)
    cs.run_to(KEYS, timeout_ms=60000)
    cs.run_to(emu.IRQ)
    cs.screenshot(out / 'title.png')
    cs.text('run')
    cs.text('press_keys', keys='5', hold_frames=6)
    cs.run_to(emu.PROBE, timeout_ms=60000)
    frames = []
    for u in range(updates):
        cs.run_to(emu.PROBE)
        frames.append(cs.byte(emu.FRAMES))
    cs.run_to(emu.WAIT)
    cs.run_to(emu.IRQ)
    cs.run_to(emu.IRQ)
    cs.screenshot(out / 'play.png')
    cs.text('clear_breakpoint', all=True)
    cs.text('run')
    return frames


def jnext(nex, updates, out):
    import re
    from nexclash import jnext as J
    s = J.Script(J.start_frame(str(nex)))
    s.var('u')
    s.var('t')
    s.var('k')
    s.rule('on execute %d do\n  log "TITLE F=${FRAME}"\nend\n' % TITLE)
    s.rule('on execute %d when t == 0 do\n  set t = FRAME\n  screenshot "%s/title.png"\nend\n'
           % (KEYS, out.as_posix()))
    # fire, pulsed until the game starts (the title polls keys only between its pages)
    s.rule('on frame when t != 0 and u == 0 do\n  set k = k + 1\n  if k == 10 then\n    press "5"\n  end\n'
           '  if k == 18 then\n    release "5"\n    set k = 0\n  end\nend\n')
    s.rule('on execute 0 when t != 0 do\n  log "RESET F=${FRAME}"\n  exit 0\nend\n')
    s.rule('on execute %d do\n  set u = u + 1\n  log "U u=${u} F=${FRAME}"\nend\n' % emu.PROBE)
    s.var('e')
    s.rule('on execute %d when u == %d and e == 0 do\n  set e = FRAME\n  screenshot "%s/play.png"\nend\n'
           % (emu.PROBE, updates + 1, out.as_posix()))
    s.rule('on frame when e != 0 and FRAME == e + 3 do\n  exit 0\nend\n')     # let the screenshot render
    s.exit_at(20000)
    code = J.run_all([(str(nex), s.text(), str(out), 20100, rtenv.CARD, rtenv.JNEXT_HOME)], timeout=3600)
    log = open(out / 'run.log').read()
    if 'TITLE F=' not in log:
        raise RuntimeError('title loop never reached')
    if 'RESET F=' in log:
        raise RuntimeError('the machine reset after the title')
    F = [int(m) for m in re.findall(r'U u=\d+ F=(\d+)', log)]
    if code != [0] or len(F) < updates + 1:
        raise RuntimeError('game did not run %d updates (%d)' % (updates, len(F) - 1))
    return [b - a for a, b in zip(F, F[1:])]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('nex', nargs='?')
    ap.add_argument('--updates', type=int, default=200)
    ap.add_argument('--emulator', choices=('auto', 'cspect', 'jnext'))
    a = ap.parse_args(argv)
    if a.emulator:
        import os
        os.environ['RTYPE_EMULATOR'] = a.emulator
    nex = a.nex
    if not nex:
        import l2scroll as L
        _, nex, _ = L.build(L.HERE.parent / 'Rtype.z80', L.OUT / 'full', full=True)
    emulator = rtenv.emulator()
    out = rtenv.OUT / 'smoke'
    out.mkdir(parents=True, exist_ok=True)
    print('emulator: %s  nex: %s' % (emulator, nex))
    try:
        frames = (cspect if emulator == 'cspect' else jnext)(nex, a.updates, out)
    except RuntimeError as e:
        print('smoke: FAIL: %s' % e)
        return 1
    play = frames[2:]
    worst = max(play) if play else 0
    slow = sum(1 for f in play if f > 3)
    hist = {f: frames.count(f) for f in sorted(set(frames))}
    # the game waits for 3 interrupts per update; busier moments take 4. More than a quarter of the
    # updates over 3 frames, or any over 6, means the hooks are costing play time.
    ok = worst <= 6 and slow * 4 <= len(play)
    print('title reached, game started, %d updates: frames per update %s' % (len(frames), hist))
    print('smoke: %s' % ('PASS' if ok else 'FAIL (slowest update %d frames, %d of %d over 3)' % (worst, slow, len(play))))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
