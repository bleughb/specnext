"""(27353) and the view's screen attributes around the recording's BEGIN (frames 520-720): when they change.
Usage: python -I attr_trace.py"""
import sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
sys.path.insert(0, r'C:/1NEXT/castle_master_work')
from nexclash import simrun

st = {'f': 0, 'sim': None, 'last': None}


class H:
    def on_sim(self, s):
        st['sim'] = s

    def on_frame(self, n):
        st['f'] = n
        if 500 <= n <= 760:
            m = st['sim'].memory
            k = (m[27353], m[0x5800 + 4 * 32 + 4], m[0x5800 + 10 * 32 + 10])
            if k != st['last']:
                print('frame %d: (27353) %02X  view attr row 4 %02X  row 10 %02X' % ((n,) + k))
                st['last'] = k

    def before(self, pc):
        if 500 <= st['f'] <= 760 and pc in (0x9EA3, 0x9F19, 0xCFC2, 0xB368):
            m = st['sim'].memory
            print('  frame %d pc %04X (27353) %02X' % (st['f'], pc, m[27353]))


simrun.play_rzx(r'C:/dev/castlemaster/castle.rzx', H(), stop=761)
