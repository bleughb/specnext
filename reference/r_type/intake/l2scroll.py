"""R-Type prototype: scenery on hardware-scrolled Layer 2, original game unchanged.

Owner goal 2026-11-15: hardware scrolling and sprites, play hard to tell from the
original. This first step moves only the scenery; figures, stars and HUD stay on
the ULA and the main loop runs at 28MHz (ISR at 3.5MHz). Not an engine or a
deliverable; no full-recording verification. Generated files stay in work.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]/'nexclash'
sys.path[:0] = [str(ROOT), str(ROOT/'tools')]
from asm2profile import assemble, sjasm
from nexclash import rzx, z80tonex as Z
from plain import Plain

OUT = Path('/workspace/work/r_type_l2scroll')
# address, original bytes, label, opcode (C3 JP / CD CALL)
SITES = [(0x8842, 'dd218080', 'l2_scroll', 0xC3), (0x89C3, '21005e', 'l2_stage', 0xC3),
         (0x8734, 'cdebfe', 'l2_init', 0xCD), (0x863D, 'cdd873', 'l2_off', 0xCD),
         (0x8BE8, '210058', 'l2_off_continue', 0xC3), (0xFE03, 'cdc273', 'l2_off_title', 0xC3),
         (0xBE26, 'dde5fde5e5', 'irq_in', 0xC3), (0xBE52, 'f108e1', 'irq_out', 0xC3)]


def fixture(frame=2000, name='play'):
    OUT.mkdir(exist_ok=True)
    path = OUT/(name+'.z80')
    if not path.exists():
        rzx.cut(str(HERE.parent/'Rtype.rzx'), frame, 2, str(OUT/(name+'.rzx')))
        rzx.extract(str(OUT/(name+'.rzx')), str(path))
    return path


SPRITE_SITES = [(0x8CFD, 'c5d5d9', 'plot_n', 0xC3), (0x8D65, 'c5d506', 'plot_h', 0xC3),
                (0x8DD3, 'c5d5d9', 'plot_v', 0xC3), (0x8E29, 'c5d506', 'plot_hv', 0xC3),
                (0x8886, '7cc620', 'spr_gate', 0xC3), (0x8EA2, '3a9c7a', 'cell_hook', 0xC3), (0x8EC2, '780f0f', 'cand_hook', 0xC3)]


def build(src=None, folder=OUT, asm=None, sprites=False, full=False):
    src = Path(src) if src else fixture()
    folder = Path(folder)
    folder.mkdir(exist_ok=True)
    blocks, syms = assemble(str(asm or HERE/('l2sprites_full.asm' if full else 'l2sprites.asm' if sprites else 'l2scroll.asm')), sjasm.find())
    sprites = sprites or full
    sites = SITES+(SPRITE_SITES if sprites else [])
    code = blocks['code']

    class Prototype(Plain):
        name = 'R-Type Layer 2 scroll PROTOTYPE, not verified'
        slot1 = (24, 0x3E00)
        hook_page_data = code
        extra_banks = {12: code}

        def apply(self, snap):
            super().apply(snap)
            backup = self.stub_extra[12:]
            setup = bytearray(self.stub_extra[:11]+Z.nextreg(0x51, 24)+b'\xCD'+Z.w16(syms['hook_setup'])+b'\xC9')
            setup[1:3] = Z.w16(self.setup_call+len(setup))
            self.stub_extra = bytes(setup)+backup
            for addr, old, label, opcode in sites:
                # 8000..BFFF is bank 2; the C000+ game code sits in bank 0.
                bank, base = (2, 0x8000) if addr < 0xC000 else (0, 0xC000)
                old = bytes.fromhex(old)
                data = bytearray(snap.banks[bank])
                assert bytes(data[addr-base:addr-base+len(old)]) == old, hex(addr)
                data[addr-base:addr-base+3] = bytes([opcode])+Z.w16(syms[label])
                snap.banks[bank] = bytes(data)

    dst = folder/('l2sprites.nex' if sprites else 'l2scroll.nex')
    Z.convert(str(src), str(dst), tail_req=0x5B00, force50=True, quiet=True, patch=Prototype())
    (folder/'symbols.json').write_text(json.dumps(syms, indent=2)+'\n')
    print(dst, flush=True)
    return src, dst, syms


if __name__ == '__main__':
    if '--full' in sys.argv:
        build(HERE.parent/'Rtype.z80', OUT/'full', full=True)
    else:
        build(sprites='--sprites' in sys.argv, folder=OUT/'sprites' if '--sprites' in sys.argv else OUT)
