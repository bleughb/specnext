"""Disassemble the game (m0_states.bin's first state): python dis.py ADDR [END] (hex)"""
import sys
sys.path.insert(0, r'C:/1NEXT/castle_master_work')
sys.path.insert(0, r'C:/1NEXT/nexclash')
from m0_lib import states
from nexclash.kb import _disassembler

m = list(next(iter(states('m0_states.bin')))[2])
d = _disassembler(m)
a = int(sys.argv[1], 16)
end = int(sys.argv[2], 16) if len(sys.argv) > 2 else a + 0x30
while a < end:
    i = d.disassemble(a, a + 1, 'h')[0]
    print('%04X  %-12s %s' % (i.address, ' '.join('%02X' % b for b in i.bytes), i.operation))
    a = i.address + len(i.bytes)
