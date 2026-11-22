"""print the snapshot's code: python dis_range.py START END"""
import sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import simrun
from skoolkit.snapshot import make_snapshot
ram = make_snapshot(r'C:/1NEXT/castle_master_work/castle_master.z80', None)[0]
a, end = int(sys.argv[1], 16), int(sys.argv[2], 16)
while a < end:
    t, n = simrun.disasm(ram, a)
    print('%04X  %-12s %s' % (a, ' '.join('%02X' % ram[a + i] for i in range(n)), t))
    a += n
