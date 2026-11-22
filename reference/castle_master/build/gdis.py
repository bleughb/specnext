"""dis.py A B [A B ...]: disassemble the game's snapshot (hex addresses)."""
import sys
from types import SimpleNamespace
from skoolkit.snapshot import get_snapshot
from skoolkit.disassembler import Disassembler
ram = get_snapshot('C:/1NEXT/castle_master_work/castle_master.z80')
cfg = SimpleNamespace(asm_hex=True, asm_lower=False, defb_size=8, defm_size=66, defw_size=1, imaker=lambda a, o, b: SimpleNamespace(address=a, operation=o), opcodes='', wrap=False, text_chars='', zfill=False, handle_rst=False, rst_handlers=None, rst=None)
try:
    d = Disassembler(ram, cfg)
except Exception as e:
    from skoolkit.sna2skool import Options
    raise
v = sys.argv[1:]
for i in range(0, len(v), 2):
    for ins in d.disassemble(int(v[i], 16), int(v[i + 1], 16), "h"):
        print('%04X %s' % (ins.address, ins.operation))
    print()
