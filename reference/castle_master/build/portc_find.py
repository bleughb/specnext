"""Where the opening portcullis (0xD0F9 masked sprite, recording frames 559-673) is called from, and the keys
read just before. Usage: python -I portc_find.py"""
import sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
sys.path.insert(0, r'C:/1NEXT/castle_master_work')
from nexclash import simrun
from m2_lib import SP, PC

st = {'f': 0, 'n': 0, 'sim': None, 'calls': {}}


class H:
    def on_sim(self, s):
        st['sim'] = s

    def on_frame(self, n):
        st['f'] = n

    def before(self, pc):
        if pc == 0xD0F9 and st['n'] < 3:
            s = st['sim']
            m, sp = s.memory, s.registers[SP]
            st['n'] += 1
            print('frame', st['f'], 'D0F9 stack', ['%04X' % (m[sp + 2 * i] | m[sp + 2 * i + 1] << 8) for i in range(8)])
        if 540 <= st['f'] <= 600 and pc in (0x859C, 0xB638, 0xB66E, 0xBCE5, 0xC93E, 0xCA44):
            k = (st['f'], '%04X' % pc)
            if k not in st['calls']:
                st['calls'][k] = 1
                print('frame', st['f'], 'pc %04X' % pc, '0x7349', st['sim'].memory[0x7349])


simrun.play_rzx(r'C:/dev/castlemaster/castle.rzx', H(), stop=700)
