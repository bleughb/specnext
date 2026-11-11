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
from publication_dynamic import full_lut

OUT=Path('/workspace/work/r_type_integrated')
OUT.mkdir(exist_ok=True)


def fixture():
    path=OUT/'play.z80'
    if not path.exists():
        rzx.cut(str(HERE.parent/'Rtype.rzx'),2000,2,str(OUT/'play.rzx'))
        rzx.extract(str(OUT/'play.rzx'),str(path))
    return path


def patch_bytes(addr,label,syms):
    # The pause sites replace CALLs; their helpers RET to the following byte.
    opcode=0xCD if addr in (0x8B80,0x8B8F) else 0xC3
    return bytes([opcode])+Z.w16(syms[label])


def build(src=None, folder=OUT, asm="publication_integrated.asm"):
    src=Path(src) if src else fixture()
    folder=Path(folder);folder.mkdir(exist_ok=True)
    blocks,syms=assemble(str(HERE/asm),sjasm.find())
    assert syms['attrs']+syms.get('MAXFIG',105)*5<0x3800
    class Diagnostic(Plain):
        name='R-Type EARLY diagnostic, NOT verified'
        slot1=(24,0x3E00)
        hook_page_data=blocks['code']
        extra_banks={24:bytes(16384),25:bytes(16384),26:bytes(16384),23:full_lut(),12:blocks['code'],20:bytes(16384),21:bytes(16384),22:bytes(16384)}
        def apply(self,snap):
            super().apply(snap)
            if 'tile_setup' in syms:
                self.extra_banks=dict(self.extra_banks)
                self.extra_banks[24]=bytes(snap.banks[7])
                if 'paint' in blocks:
                    self.extra_banks[28]=blocks['paint']+bytes(16384-len(blocks['paint']))
                    for bank in range(32,38):self.extra_banks[bank]=bytes(16384)
                    from paint_stress import textures
                    self.extra_banks.update(textures(snap))
            if 'spritepaint_setup' in syms:
                self.extra_banks=dict(self.extra_banks)
                from spritepaint_stress import textures
                self.extra_banks.update(textures(snap))
            if 'lookup' in blocks:
                self.extra_banks=dict(self.extra_banks)
                from live_assets import catalogue,compile,compile_direct
                meta,images=catalogue()
                compiler=compile_direct if 'direct_lookup_code' in syms or 'resolve_code' in syms else compile
                private,summary=compiler(meta,images)
                self.extra_banks.update(private)
                resolver=blocks.get('resolve',b'')
                assert len(resolver)<4096 and len(blocks['lookup'])<4096
                self.extra_banks[28]=resolver+bytes(4096-len(resolver))+blocks['lookup']+bytes(16384-4096-len(blocks['lookup']))
                (folder/'live-assets.json').write_text(json.dumps(summary,indent=2)+'\n')
            backup=self.stub_extra[12:]
            setup=bytearray(self.stub_extra[:11]+Z.nextreg(0x51,24)+b'\xCD'+Z.w16(syms['hook_setup'])+b'\xC9')
            setup[1:3]=Z.w16(self.setup_call+len(setup))
            self.stub_extra=bytes(setup)+backup
            sites=[(0x8842,'dd218080','hook_entry'),(0xBE26,'dde5fde5e5','irq_in'),(0xBE52,'f108e1','irq_out'),
                (0x8CFD,'c5d5d9','text_8cfd'),(0x8D65,'c5d5065d','text_8d65'),
                (0x8DD3,'c5d5d9','text_8dd3'),(0x8E29,'c5d5065d','text_8e29')]
            if 'tile_setup' in syms:sites.extend([(0x8F21,'ed795e','bank_read'),(0x8B80,'cdc5c2','pause_enter'),(0x8B8F,'cdc5c2','pause_leave')])
            if 'cell_entry' in syms and 'cell_inline_n' not in syms:sites.append((0x8EA2,'3a9c7a','cell_entry'))
            if 'cell_inline_n' in syms:
                for addr,label in ((0x8D27,'cell_inline_n'),(0x8D8E,'cell_inline_h'),(0x8DFA,'cell_inline_v'),(0x8E54,'cell_inline_hv')):
                    original=bytes(snap.read(addr+i)for i in range(7))
                    expected={'cell_inline_n':'cda28eca5b8d57','cell_inline_h':'cda28e2836574e','cell_inline_v':'cda28e2820c607','cell_inline_hv':'cda28e2822c607'}[label]
                    assert original==bytes.fromhex(expected),(hex(addr),original.hex(),expected)
                    data=bytearray(snap.banks[2]);data[addr-0x8000:addr-0x8000+7]=Z.nextreg(7,3)+b'\xc3'+Z.w16(syms[label]);snap.banks[2]=bytes(data)
            for addr,old,label in sites:
                assert bytes(snap.read(addr+i)for i in range(len(bytes.fromhex(old))))==bytes.fromhex(old),hex(addr)
                bank=2
                data=bytearray(snap.banks[bank])
                data[addr-0x8000:addr-0x8000+3]=patch_bytes(addr,label,syms)
                snap.banks[bank]=bytes(data)
    dst=folder/'diagnostic.nex'
    Z.convert(str(src),str(dst),tail_req=0x5B00,force50=True,quiet=True,patch=Diagnostic())
    (folder/'symbols.json').write_text(json.dumps(syms,indent=2)+'\n')
    print(dst,flush=True)
    return src,dst,syms


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path);ap.add_argument('--out',type=Path,default=OUT)
    a=ap.parse_args();build(a.source,a.out)
