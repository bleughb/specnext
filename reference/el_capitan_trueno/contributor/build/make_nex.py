# Prototype builder: El Capitan Trueno with figures as sprites and the foreground in Layer 2.
# Inputs: the host's snapshot, the assembled hooks (build/asm: tr_rom.bin, tr_page.bin, tr_setup.bin,
# trueno_hooks.sym) and the tables from patterns.py (shapedir, fdir, blink, patterns, palette).
# Output: trueno/Trueno_sprites.nex, then the toolkit's boot simulation (nextboot).
# Usage: python make_nex.py [--en] [--immortal]   (run from anywhere; --en: English texts; --immortal: the
#        energy never drops; output Trueno_sprites[_en][_immortal].nex)
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TK = os.path.join(HERE, '..', 'tk', 'nexclash-0.1.4')
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, TK)
from nexclash import z80tonex as zt
from nexclash.build import rom48
from nexclash import nextboot

SNAP = os.path.join(HERE, '..', 'Capitan Trueno, El (1990)(Dinamic)(ES).z80')
EN = '--en' in sys.argv                 # English texts (texts_en.py, host 2026-10-14); default: the original
OUT = os.path.join(HERE, '..', 'Trueno_sprites%s%s.nex' % ('_en' if EN else '', '_immortal' if '--immortal' in sys.argv else ''))
ASM = os.path.join(HERE, 'asm')
ROM_ORG, PAGE_ORG = 0x386E, 0x0100
ALT_PAGE, PAGE_S, PAT0, L2BANK = 24, 26, 28, 27
BWPAGE = 60                 # bush cells (bush_walls.py -> bushwall.bin), pages 60 on (asm BWPAGE)
SDIR, FDIR, BLINK = 0x1200, 0x1A00, 0x1C00
TAIL = 0xA6C9               # write-first in the whole RZX (old init code reused as the restore list)
SPECCY = [0x00, 0x02, 0xA0, 0xA2, 0x14, 0x16, 0xB4, 0xB6, 0x00, 0x03, 0xE0, 0xE7, 0x1C, 0x1F, 0xFC, 0xFF]
JP_SITES = {0x82DF: ('DDCB0346', 'e_fig'), 0x88A2: ('2108E6', 'e_cm'), 0x8865: ('3A08E6', 'e_tk'),
            0x887D: ('3F1F32', 'e_shk'),
            0x6410: ('2160EF', 'e_scr'), 0xA207: ('210058', 'e_cls'),
            0xA375: ('C301A5', 'e_mnu'), 0x889B: ('213CF1', 'e_att'),
            0x5DCD: ('CD0E5E', 'e_end')}
DATA_SITES = {0x87BE: ('60EF', '003B'),     # the plotter's foreground map -> all-0xFF ROM bytes (no drawing)
              0xD615: ('A2', 'A0'),     # (host) pillar edge frame 0x91 (0xD609, 1x2 cells, attr 7): its lone
                                        # pixel at x 6 showed grey beside the cyan pillar -> removed
              0x5FF1: ('05', '04')}     # (host) title menu: 4 items, no "5 COLOR ON" (LD B,5 at 0x5FF0 is the
                                        # item count for drawing and for the keys; the original's colour off
                                        # only took the colour off the figures)
# e_att (0x889B): the copy's attributes from the scenery copy 0xEF98 (the painter ignores the map for
# figures without flag bit 2, 0x841E NOPs); screen 34 from 0xF13C (the dragon's energy bar)
ALLFF = (0x3B00, 0x3D00)                    # must be 0xFF in the 48K ROM and untouched by the hooks
# TEMPORARY test cheat (host, 2026-10-13; remove before delivery): the damage routine 0x7A00 stores the
# reduced energy with LD (HL),A at 0x7A1F -> NOP: energy (0xE60F) never drops, the hit flag still works
CHEAT_IMMORTAL = '--immortal' in sys.argv     # off by default since 2026-10-13; an option for players
if CHEAT_IMMORTAL:
    DATA_SITES[0x7A1F] = ('77', '00')


def syms():
    out = {}
    for line in open(os.path.join(ASM, 'trueno_hooks.sym')):
        name, _, val = line.partition(': EQU ')
        if val:
            out[name.strip()] = int(val, 16)
    return out


def rd(name):
    return open(os.path.join(HERE, name), 'rb').read()


def l2_palette():
    """Layer 2 indices 16-31: the 16 colours with the priority bit (foreground over the sprites);
    32-47: the same without it (wall ropes, under the sprites). 9-bit pairs."""
    out = bytearray()
    for prio in (0x80, 0x00):
        for c in SPECCY:
            out += bytes([c, prio | (1 if c & 3 else 0)])
    return bytes(out)


class TruenoPatch:
    name = 'El Capitan Trueno figures -> hardware sprites, foreground -> Layer 2 (altrom + RAM page 26)'

    def __init__(self):
        S = syms()
        self.rom_code = open(os.path.join(ASM, 'tr_rom.bin'), 'rb').read()
        page_code = open(os.path.join(ASM, 'tr_page.bin'), 'rb').read()
        self.setup = open(os.path.join(ASM, 'tr_setup.bin'), 'rb').read()
        self.stub_extra = self.setup + rd('palette.bin') + l2_palette()
        self.setup_call = 0xD000
        self.hook_page_data = b''
        self.uses_printer_buffer = True
        self.tail_addr = TAIL
        self.max_tail = 80
        self.regblock = ROM_ORG + len(self.rom_code)
        if self.regblock + 20 > 0x3D00:
            raise ValueError('ROM stubs too long')
        self.slot1 = (ALT_PAGE, self.regblock)
        # the stub copies the system ROM3 (NextZXOS: data at 0x3B00-0x3CFF, not 0xFF as in the 48K ROM)
        # into the alt ROM, then lo..hi from the page: hi = 0x3D00 brings the all-0xFF map along
        self.altrom = (ROM_ORG, ALLFF[1])
        rom = rom48()
        if any(b != 0xFF for b in rom[ALLFF[0]:ALLFF[1]]) or self.regblock + 20 > ALLFF[0]:
            raise ValueError('the all-0xFF map 0x%04X-0x%04X is not free' % ALLFF)
        if any(b != 0xFF for b in rom[ROM_ORG:self.regblock + 20]):
            raise ValueError('alt ROM hook range is not free ($FF) in the 48K ROM')
        page = bytearray(rom[0x2000:0x4000])
        page[ROM_ORG - 0x2000:ROM_ORG - 0x2000 + len(self.rom_code)] = self.rom_code
        self.page = bytes(page)
        hp = bytearray(8192)
        if PAGE_ORG + len(page_code) > 0x1000:
            raise ValueError('page code overlaps the tables')
        hp[PAGE_ORG:PAGE_ORG + len(page_code)] = page_code
        sd = rd('shapedir.bin')
        hp[SDIR:SDIR + len(sd)] = sd
        fd = rd('fdir.bin')
        hp[FDIR:FDIR + len(fd)] = fd
        bl = rd('blink.bin')
        hp[BLINK:BLINK + len(bl)] = bl
        pats = rd('patterns.bin')
        npages = len(pats) // 8192
        banks = {12: self.page + bytes(8192), 13: bytes(hp) + bytes(8192)}
        for i in range(0, npages, 2):
            banks[PAT0 // 2 + i // 2] = pats[i * 8192:(i + 2) * 8192].ljust(16384, b'\0')
        if PAT0 // 2 + (npages + 1) // 2 > L2BANK:
            raise ValueError('pattern pages run into the Layer 2 banks')
        # Layer 2 (banks L2BANK on) is not stored: the setup fills it with 0xE3 (2026-10-14)
        bw = rd('bushwall.bin')
        if L2BANK + 3 > BWPAGE // 2:
            raise ValueError('Layer 2 banks run into the bush pages')
        for i in range(0, len(bw), 16384):
            banks[BWPAGE // 2 + i // 16384] = bw[i:i + 16384].ljust(16384, b'\0')
        self.extra_banks = banks
        self.sites = [(a, bytes.fromhex(old), b'\xC3' + S[sym].to_bytes(2, 'little'))
                      for a, (old, sym) in JP_SITES.items()]
        self.sites += [(a, bytes.fromhex(old), bytes.fromhex(new)) for a, (old, new) in DATA_SITES.items()]

    def _bank_of(self, a):
        return (5, 2, 0)[(a >> 14) - 1]

    def apply(self, snap):
        for a, old, new in self.sites:
            k = self._bank_of(a)
            b = bytearray(snap.banks[k])
            cur = bytes(b[a & 0x3FFF:(a & 0x3FFF) + len(old)])
            if cur != old:
                raise ValueError('unexpected code at 0x%04X (%s, expected %s)' % (a, cur.hex(), old.hex()))
            b[a & 0x3FFF:(a & 0x3FFF) + len(new)] = new
            snap.banks[k] = bytes(b)
        b = bytearray(snap.banks[5])        # the snapshot shows the title menu already drawn: wipe "5 COLOR
        for y in range(112, 120):           # ON" (x 88-175, y 112-119; menu item 5 at 0x5F05, 0x5FF1 patch)
            a = (y & 0xC0) << 5 | (y & 7) << 8 | (y & 0x38) << 2
            b[a + 11:a + 22] = bytes(11)
        snap.banks[5] = bytes(b)
        if EN:
            import texts_en
            mem = bytearray(16384) + snap.banks[5] + snap.banks[2] + snap.banks[0]
            for a, old, new in texts_en.sites(mem):
                if bytes(mem[a:a + len(old)]) != old:
                    raise ValueError('unexpected text at 0x%04X' % a)
                mem[a:a + len(new)] = new
            mem[0x4000:0x5B00] = texts_en.redraw(mem)
            snap.banks[5], snap.banks[2], snap.banks[0] = (bytes(mem[0x4000:0x8000]), bytes(mem[0x8000:0xC000]),
                                                           bytes(mem[0xC000:]))


def main():
    patch = TruenoPatch()
    zt.convert(SNAP, OUT, TAIL, patch=patch)
    bad = nextboot.check(OUT, SNAP, TruenoPatch(), tail=(TAIL, TAIL + 80))
    print('Boot     :', 'OK' if not bad else bad)


if __name__ == '__main__':
    main()
