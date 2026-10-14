# El Capitan Trueno: the whole build from the two inputs (the title .z80 and trueno1.rzx) and the
# contributor's sheets (gfx/*.png) to Trueno_sprites.nex, step by step:
#   gfxcat.py     every graphic of every frame in the RZX -> gfx_catalog.json
#   shapes.py     ink + mask per shape via the game's own plotter (state after 5000 RZX frames)
#   patterns.py   4-bit sprite patterns from the shapes and the sheets -> patterns.bin, shapedir, ...
#   bush_walls.py Layer 2 table: bushes (gfx/bush_tiles.png) + fix cells (gfx/fix_tiles.png)
#   sjasmplus     asm/trueno_hooks.asm -> build/asm/tr_rom.bin, tr_page.bin, tr_setup.bin + .sym
#   make_nex.py   the patched snapshot + hooks + tables -> ../Trueno_sprites.nex (boot sim checked)
# Usage: python build_all.py [--sjasm PATH]   (default: the toolkit's pinned sjasmplus, sjasm.py)
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TK = os.path.join(HERE, '..', 'tk', 'nexclash-0.1.4')


def run(*cmd, cwd=HERE):
    print('>', ' '.join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def main():
    a = sys.argv[1:]
    if '--sjasm' in a:
        sjasm = a[a.index('--sjasm') + 1]
    else:
        sjasm = subprocess.run([sys.executable, os.path.join(TK, 'tools', 'sjasmplus', 'sjasm.py')],
                               capture_output=True, text=True, check=True).stdout.strip()
    py = sys.executable
    run(py, 'gfxcat.py', os.path.join('..', 'trueno1.rzx'), 'gfx_catalog.json')
    run(py, 'shapes.py')
    run(py, 'patterns.py')
    run(py, 'bush_walls.py')
    os.makedirs(os.path.join(HERE, 'asm'), exist_ok=True)
    run(sjasm, '--nologo', '--lst=trueno_hooks.lst', '--sym=trueno_hooks.sym',
        '../../tk/nexclash-0.1.4/asm/trueno_hooks.asm', cwd=os.path.join(HERE, 'asm'))
    run(py, 'make_nex.py')


if __name__ == '__main__':
    main()
