# Put Trueno_sprites.nex into the SD image, start it in MAME (NextBASIC: .nexload), start the game
# with key 1 and take screen snapshots (not with --watch). Usage: python run_nex.py [--watch] [--en] [--immortal]
#   --watch: stop at the title menu, at normal speed (the host starts and plays it; no key pressed)
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, '_emulators', 'tools'))
import mame
import screen

HDF = os.path.join(ROOT, '_emulators', 'HDFMonkey.exe')
IMG = os.path.join(ROOT, '_emulators', 'sdcard.img')
SHOTS = os.path.join(ROOT, '_emulators', 'screens')
NEX = os.path.join(HERE, '..', 'Trueno_sprites%s%s.nex' % ('_en' if '--en' in sys.argv else '',
                                                         '_immortal' if '--immortal' in sys.argv else ''))
DIR = '/tdemo'
NAME = 'trs.nex'
OUT = os.path.join(HERE, '..', 'snaps', 'mame')


def hdf(*args, check=True):
    r = subprocess.run([HDF, *args], capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError('HDFMonkey ' + ' '.join(args) + ': ' + (r.stdout + r.stderr).strip())


def shot(name):
    mame.run('manager.machine.screens[":screen"]:snapshot("%s")' % name)
    time.sleep(1)
    os.makedirs(OUT, exist_ok=True)
    shutil.move(os.path.join(SHOTS, name), os.path.join(OUT, name))


def main():
    watch = '--watch' in sys.argv
    subprocess.run(['taskkill', '/IM', 'mame.exe', '/F'], capture_output=True)
    time.sleep(2)
    hdf('mkdir', IMG, DIR, check=False)
    hdf('rm', IMG, DIR + '/' + NAME, check=False)
    hdf('put', IMG, NEX, DIR + '/' + NAME)
    # no output capture: MAME inherits the handles and would keep a pipe open
    subprocess.run(['cmd', '/c', os.path.join(ROOT, '_emulators', 'tools', 'runEmulator.cmd')],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    end = time.time() + 60
    while not any('Browser' in r for r in screen.read_text()):
        if time.time() > end:
            raise RuntimeError('NextZXOS main menu did not appear')
        time.sleep(0.5)
    screen.wait_stable(quiet=0.5)
    mame.type_text('n')
    screen.wait_stable(quiet=0.5)
    mame.type_checked('CD "' + DIR + '"')
    mame.type_text('\n')
    screen.wait_stable(quiet=0.5)
    mame.type_text('\n')                       # the key after "0 OK" is eaten
    screen.wait_stable(quiet=0.5)
    mame.type_checked('.nexload ' + NAME)
    mame.type_text('\n')
    mame.run('speed(true)')                    # the game at normal speed
    time.sleep(4)
    if watch:                                  # the host starts the game himself, from the title menu
        print('started')
        return
    shot('trs_menu.png')
    mame.type_text('1')
    for i, t in enumerate((3, 3, 4, 5)):
        time.sleep(t)
        shot('trs_game%d.png' % i)
    print('snapshots in', OUT)


if __name__ == '__main__':
    main()
