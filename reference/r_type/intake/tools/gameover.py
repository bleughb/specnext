"""Game over -> high-score name entry in the full build (JNext only: needs keys at frame times).

    py -3 gameover.py [--updates-limit 6000]

Builds a TEST copy of the full build whose high-score table is all 000000 (so any score enters it),
plays with fire pulsed until all lives are lost, then at name entry (934C) checks, each a FAIL:
  - name entry is reached;
  - Layer 2 (NR 69h bit 7) and sprites (NR 15h bit 0) are off over the high-score table;
  - the CPU runs at 3.5MHz there (NR 07h = 0: the screen times itself with CPU loops);
  - the entry keys change the name (up/down letter, fire confirms; the original takes no typed letters).
Screenshots go to RTYPE_WORK/r_type_l2scroll/gameover/. Exit status 1 on any FAIL.
"""
import argparse
import re
import sys

import rtenv

ENTRY, NAME = 0x934C, 0x71D2      # name entry; the letter being entered


def build():
    import l2scroll as L
    keep = list(L.RAMFIX)
    L.RAMFIX = keep + [(0x7CE2 + 17 * i, None, '303030303030') for i in range(9)]   # TEST ONLY
    try:
        _, nex, _ = L.build(L.HERE.parent / 'Rtype.z80', L.OUT / 'gameover_test', full=True)
    finally:
        L.RAMFIX = keep
    return nex


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--frames-limit', type=int, default=20000)
    a = ap.parse_args(argv)
    rtenv.emulator(('update_keys',))
    from nexclash import jnext as J
    nex = build()
    out = rtenv.OUT / 'gameover'
    out.mkdir(parents=True, exist_ok=True)
    s = J.Script(J.start_frame(str(nex)))
    for v in ('e', 'k'):
        s.var(v)
    s.rule('on execute %d when e == 0 do\n  set e = FRAME\n  release "5"\n'
           '  log "ENTRY F=${FRAME} L2=${nextreg[105]} SPR=${nextreg[21]} SPEED=${nextreg[7]} N=${mem[%d]}"\nend\n'
           % (ENTRY, NAME))
    s.rule('on frame when e == 0 and FRAME > %d do\n  set k = k + 1\n  if k == 6 then\n    press "5"\n  end\n'
           '  if k == 9 then\n    release "5"\n    set k = 0\n  end\nend\n' % (J.start_frame(str(nex)) + 300))
    for off, act in ((40, 'press "1"'), (46, 'release "1"'), (70, 'press "1"'), (76, 'release "1"')):
        s.rule('on frame when e != 0 and FRAME == e + %d do\n  %s\nend\n' % (off, act))
    s.rule('on frame when e != 0 and FRAME == e + 10 do\n  screenshot "%s/entry.png"\nend\n' % out.as_posix())
    s.rule('on frame when e != 0 and FRAME == e + 100 do\n  log "AFTER N=${mem[%d]}"\n  screenshot "%s/keys.png"\nend\n'
           % (NAME, out.as_posix()))
    s.rule('on frame when e != 0 and FRAME == e + 104 do\n  exit 0\nend\n')
    s.exit_at(a.frames_limit)
    J.run_all([(str(nex), s.text(), str(out), a.frames_limit + 100, rtenv.CARD, rtenv.JNEXT_HOME)], timeout=3600)
    log = open(out / 'run.log').read()
    m = re.search(r'ENTRY F=\d+ L2=(\d+) SPR=(\d+) SPEED=(\d+) N=(\d+)', log)
    if not m:
        print('gameover: FAIL: name entry never reached in %d frames' % a.frames_limit)
        return 1
    l2, spr, speed, n0 = map(int, m.groups())
    n1 = int(re.search(r'AFTER N=(\d+)', log).group(1)) if 'AFTER N=' in log else None
    checks = [('Layer 2 off', not l2 & 0x80), ('sprites off', not spr & 1), ('3.5MHz', speed & 3 == 0),
              ('keys change the name', n1 is not None and n1 != n0)]
    for name, ok in checks:
        print('  %-22s %s' % (name, 'ok' if ok else 'FAIL'))
    ok = all(c for _, c in checks)
    print('gameover: %s' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
