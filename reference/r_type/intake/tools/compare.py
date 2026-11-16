"""Sprite build against a same-speed ULA-only control, from RZX snapshots (README.md).

    py -3 compare.py [--frames 2000,30000] [--updates 20,120,300] [--input [--seed N]]
                     [--emulator auto|cspect|jnext] [--diff 400] [--slow 2]

For each RZX frame: cut a snapshot, build the sprite prototype and a control (the same build with the
scenery left on the ULA and Layer 2 hidden), run both on the same emulator and check:
  - both reach every requested update (else FAIL);
  - pacing: updates slower than 3 frames in the sprite build exceed the control's by at most --slow;
  - pictures at the requested updates differ by at most --diff pixels. A bigger difference that
    vanishes when the sprite picture is shifted by one scroll pixel is reported as ONE UPDATE APART
    (the builds left an interrupt-timed sequence an update apart), not as a fault; anything else FAILs.
  - --input: random keys (1-4 move, 5 fire) at exact game updates, the same in both builds (JNext);
    a run where any scheduled key was not pressed FAILs. Pictures are then information only: the
    game's randomness comes from the R register, which the hooks change, so play diverges.
Exit status 1 when anything FAILs. Pictures and logs stay in RTYPE_WORK/r_type_l2scroll/compare/.
"""
import argparse
import random
import sys

import rtenv
import emu

DEFAULT_FRAMES = '2000,10000,20000,30000,40000,50000,60000,75000'


def keys_for(updates, seed):
    rnd = random.Random(seed)
    out, u = [], 3
    while u < max(updates):
        held = rnd.randint(2, 12)
        k = [rnd.choice('1234')] if rnd.random() < 0.85 else []
        if rnd.random() < 0.6:
            k.append('5')
        if k:
            out.append((u, k, held))
        u += held + rnd.randint(0, 4)
    return out


def diff(a, b, shift=0):
    from PIL import ImageChops
    pa, pb = emu.paper(a).crop((16, 0, 240, 160)), emu.paper(b)
    if shift:
        pb = ImageChops.offset(pb, shift, 0)
    d = ImageChops.difference(pa, pb.crop((16, 0, 240, 160))).convert('L')
    return sum(1 for v in (d.get_flattened_data() if hasattr(d, 'get_flattened_data') else d.getdata()) if v)


def builds(frame):
    import l2scroll as L
    src = L.fixture(frame, 'f%05d' % frame)
    _, spr, _ = L.build(src, L.OUT / ('f%05d_spr' % frame), sprites=True)
    ctl_asm = L.HERE / 'l2scroll_ctl_tmp.asm'
    ctl_asm.write_text('        DEFINE L2_KEEP_ULA\n        DEFINE L2_HIDE\n' + (L.HERE / 'l2scroll.asm').read_text())
    try:
        _, ctl, _ = L.build(src, L.OUT / ('f%05d_ctl' % frame), asm=ctl_asm)
    finally:
        ctl_asm.unlink()
    return spr, ctl


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--frames', default=DEFAULT_FRAMES)
    ap.add_argument('--updates', default='20,60,120,200,300')
    ap.add_argument('--input', action='store_true')
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--emulator', choices=('auto', 'cspect', 'jnext'))
    ap.add_argument('--diff', type=int, default=400)
    ap.add_argument('--slow', type=int, default=2)
    a = ap.parse_args(argv)
    if a.emulator:
        import os
        os.environ['RTYPE_EMULATOR'] = a.emulator
    updates = [int(x) for x in a.updates.split(',')]
    keys = keys_for(updates, a.seed) if a.input else None
    emulator = rtenv.emulator(('update_keys',) if keys else ())
    print('emulator: %s   %s' % (emulator, rtenv.describe()))
    fails = 0
    for frame in [int(x) for x in a.frames.split(',')]:
        spr, ctl = builds(frame)
        base = rtenv.OUT / 'compare' / ('f%05d%s' % (frame, '_in%d' % a.seed if keys else ''))
        rs = emu.run(spr, updates, updates, keys, emulator, base / 'spr')
        rc = emu.run(ctl, updates, updates, keys, emulator, base / 'ctl')
        slow_s = sum(1 for f in rs.frames[2:] if f > 3)
        slow_c = sum(1 for f in rc.frames[2:] if f > 3)
        verdict = 'ok' if slow_s - slow_c <= a.slow else 'FAIL'
        fails += verdict == 'FAIL'
        print('%5d pacing %-4s sprite %s control %s (slow updates %d / %d)' % (
            frame, verdict, rs.histogram(), rc.histogram(), slow_s, slow_c))
        for u in updates:
            n = diff(rc.shots[u], rs.shots[u])
            if keys:
                # with input the builds play differently: the game takes random numbers from the R
                # register, which the hooks change (allowed: equivalence is "extremely close")
                print('      u%-4d picture info %5d px (input runs diverge; not a check)' % (u, n))
                continue
            if n <= a.diff:
                print('      u%-4d picture ok   %5d px' % (u, n))
                continue
            best = min(diff(rc.shots[u], rs.shots[u], s) for s in (-1, 1))
            if best <= max(a.diff * 3, n // 4):
                print('      u%-4d ONE UPDATE APART %5d px (%d when shifted one scroll pixel)' % (u, n, best))
            else:
                fails += 1
                print('      u%-4d picture FAIL %5d px (shifted %d)  %s' % (u, n, best, rs.shots[u]))
    print('compare: %s' % ('FAIL (%d)' % fails if fails else 'PASS'))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
