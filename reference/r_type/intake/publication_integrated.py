"""Early integrated copier diagnostic, not an engine or deliverable.

Shared converter/tail, complete live grid preparation and native IRQ wrappers.
Measures pace/freshness before investing in the final engine. No R-equivalence,
text tagging, palette/recolour or hardware claim. Generated files stay in work.
"""
import json
import os
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]/'nexclash'
sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from asm2profile import assemble,sjasm
from nexclash import rzx,z80tonex as Z
from plain import Plain

OUT=Path('/workspace/work/r_type_integrated')
OUT.mkdir(exist_ok=True)


def fixture():
    path=OUT/'play.z80'
    if not path.exists():
        rzx.cut(str(HERE.parent/'Rtype.rzx'),2000,2,str(OUT/'play.rzx'))
        rzx.extract(str(OUT/'play.rzx'),str(path))
    return path


def build():
    src=fixture()
    blocks,syms=assemble(str(HERE/'publication_integrated.asm'),sjasm.find())
    assert syms['attrs']+525<0x3800
    class Diagnostic(Plain):
        name='R-Type EARLY diagnostic, NOT verified'
        slot1=(24,0x3E00)
        hook_page_data=blocks['code']
        extra_banks={12:blocks['code'],20:bytes(16384),21:bytes(16384),22:bytes(16384)}
        def apply(self,snap):
            super().apply(snap)
            backup=self.stub_extra[12:]
            setup=bytearray(self.stub_extra[:11]+Z.nextreg(0x51,24)+b'\xCD'+Z.w16(syms['hook_setup'])+b'\xC9')
            setup[1:3]=Z.w16(self.setup_call+len(setup))
            self.stub_extra=bytes(setup)+backup
            for addr,old,label in [(0x8842,'dd218080','hook_entry'),(0xBE26,'dde5fde5e5','irq_in'),(0xBE52,'f108e1','irq_out')]:
                assert bytes(snap.read(addr+i)for i in range(len(bytes.fromhex(old))))==bytes.fromhex(old),hex(addr)
                bank=2
                data=bytearray(snap.banks[bank])
                data[addr-0x8000:addr-0x8000+3]=b'\xc3'+Z.w16(syms[label])
                snap.banks[bank]=bytes(data)
    dst=OUT/'diagnostic.nex'
    Z.convert(str(src),str(dst),tail_req=0x5B00,force50=True,quiet=True,patch=Diagnostic())
    (OUT/'symbols.json').write_text(json.dumps(syms,indent=2)+'\n')
    print(dst,flush=True)
    return src,dst,syms


if __name__=='__main__':
    build()
