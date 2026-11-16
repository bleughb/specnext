"""Screenshots of any .nex at given game updates, with frames per update (README.md).

    py -3 shots.py NEX 20,60,120 [--out DIR] [--emulator auto|cspect|jnext]

The picture of update N is taken once its drawing is complete. Prints the frames each update took.
"""
import argparse
import sys

import emu


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('nex')
    ap.add_argument('updates')
    ap.add_argument('--out')
    ap.add_argument('--emulator', choices=('auto', 'cspect', 'jnext'))
    a = ap.parse_args(argv)
    if a.emulator:
        import os
        os.environ['RTYPE_EMULATOR'] = a.emulator
    ups = [int(x) for x in a.updates.split(',')]
    r = emu.run(a.nex, ups, ups, out=a.out)
    print('emulator: %s  frames per update: %s' % (r.emulator, r.histogram()))
    for u in ups:
        print('  u%-5d %s' % (u, r.shots[u]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
