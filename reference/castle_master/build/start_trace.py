"""Which view routines run around the recording's start (BEGIN ~frame 540) and the portcullis: geometry 0x8D4F, raster
0x9EA3, shows 0x9F19 / 0xA38D, dissolve 0xB66E, portcullis 0xCFC2, the start path 0xA0A0 / 0xA0A4; with callers.
Usage: python -I start_trace.py [from] [to]"""
import sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
sys.path.insert(0, r'C:/1NEXT/castle_master_work')
from nexclash import simrun
from m2_lib import SP

F0 = int(sys.argv[1]) if len(sys.argv) > 1 else 400
F1 = int(sys.argv[2]) if len(sys.argv) > 2 else 760
W = {0x8D4F: 'geometry', 0x9EA3: 'raster', 0x9F19: 'show', 0xA38D: 'flip-show', 0xB66E: 'dissolve',
     0xCFC2: 'portcullis', 0xA097: 'start D1D5', 0xA0A0: 'start raster?', 0xA0A7: 'start after', 0xB63D: 'B63D'}
st = {'f': 0, 'sim': None, 'last': None}


class H:
    def on_sim(self, s):
        st['sim'] = s

    def on_frame(self, n):
        st['f'] = n

    def before(self, pc):
        if F0 <= st['f'] <= F1 and pc in W:
            s = st['sim']
            m, sp = s.memory, s.registers[SP]
            ret = m[sp] | m[sp + 1] << 8
            k = (W[pc], ret, m[0x7349])
            if k != st['last']:
                print('frame %d %-12s ret %04X 7349=%d A=%02X F=%02X' % (st['f'], W[pc], ret, m[0x7349], s.registers[0], s.registers[1]))
                st['last'] = k


simrun.play_rzx(r'C:/dev/castlemaster/castle.rzx', H(), stop=F1 + 1)
