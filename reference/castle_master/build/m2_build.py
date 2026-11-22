"""Castle Master M2: build the early integrated NEX (local; the engine module comes with M3's verifier).
The repo's converter (nexclash.z80tonex.convert), its stub and alt ROM fill; hooks = cm2_rom.bin in the alt ROM at
SHARED; renderer pages (bank 16), work RAM (bank 17: the game's constant tables copied from the snapshot); sites
with their original bytes checked. Then the repo's boot check (nexclash.nextboot.check).
Usage: python m2_build.py [snapshot.z80] [-o out.nex]
"""
import argparse, sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import z80tonex as zt, nextboot
from m2_lib import W, assemble, syms, site_bytes, work_image, VP

ALT_BANK = 12                           # 8K page 24: the alt ROM's source image of 0x2000-0x3FFF
ROM_FF = 0x386E                         # Sinclair's ROM is 0xFF from here; below it (to SHARED) the game never
                                        # reads or runs the ROM (m3b_rom.py: reads only at 0x0000-0x00FF)
TAIL_ADDR = 0x5B00                      # printer buffer: zero in the snapshot (survey: safe)


class CastlePatch:
    name = 'Castle Master M2: colour view on Layer 2 (early integrated build)'

    def __init__(self, prefix='cm2'):
        self.prefix = prefix
        self.S = S = syms(prefix)
        self.rom_code = open(W + prefix + '_rom.bin', 'rb').read()
        self.code_pages = open(W + prefix + '_page.bin', 'rb').read()
        if MONO:
            assert self.code_pages[S['col_on']] == 1
            self.code_pages = self.code_pages[:S['col_on']] + bytes(1) + self.code_pages[S['col_on'] + 1:]
        self.stub_extra = open(W + prefix + '_setup.bin', 'rb').read()
        self.setup_call = 0xD000
        self.hook_page_data = b''
        self.uses_printer_buffer = False
        self.tail_addr = TAIL_ADDR
        self.max_tail = 256
        self.regblock = S['SHARED'] + len(self.rom_code)
        assert self.regblock + 20 <= 0x3D00
        self.slot1 = (2 * ALT_BANK, self.regblock)
        self.altrom = (S['SHARED'], self.regblock + 20)
        rom = zt.rom48()
        assert all(b == 0xFF for b in rom[max(S['SHARED'], ROM_FF):self.regblock + 20])
        page = bytearray(rom[0x2000:0x4000])
        page[S['SHARED'] - 0x2000:S['SHARED'] - 0x2000 + len(self.rom_code)] = self.rom_code
        self.page = bytes(page)
        self.sites = site_bytes(S)
        self.extra_banks = {}

    def apply(self, snap):
        if snap.is128:
            raise ValueError('Castle Master: a 48K snapshot expected')
        ram = bytearray(snap.banks[5] + snap.banks[2] + snap.banks[0])
        for a, old, new in self.sites:
            cur = bytes(ram[a - 0x4000:a - 0x4000 + len(old)])
            if cur != old:
                raise ValueError('unexpected code at 0x%04X (%s, expected %s)' % (a, cur.hex(), old.hex()))
        if any(ram[TAIL_ADDR - 0x4000:TAIL_ADDR - 0x4000 + 256]):
            raise ValueError('printer buffer is not empty in this snapshot (tail site)')
        full = bytes(16384) + bytes(ram)
        work = work_image(self.S, full)
        for a, old, new in self.sites:
            ram[a - 0x4000:a - 0x4000 + len(new)] = new
        if 'h_prn' in self.S:           # cm3: the clock's state (IM 2 table bytes the CPU never reads), K
            if set(ram[VP - 0x4000:VP - 0x4000 + 40]) != {0xFD} or ram[0xFEFF - 0x4000] != 0xFD:
                raise ValueError('the IM 2 table is not as expected at 0x%04X' % VP)
            ram[VP - 0x4000:VP - 0x4000 + 40] = bytes(40)
            ram[VP + 28 - 0x4000] = self.S['K16']
        if SCREEN is not None and not getattr(self, 'for_check', False):
            o = self.S['scr_on'] - 0xD000
            assert self.stub_extra[o] == 0
            self.stub_extra = self.stub_extra[:o] + bytes([1]) + self.stub_extra[o + 1:]
            self.hook_page_data = bytes(ram[0:6912])
            ram[0:6912] = SCREEN
        snap.banks[5], snap.banks[2], snap.banks[0] = bytes(ram[0:16384]), bytes(ram[16384:32768]), bytes(ram[32768:])
        S = self.S
        self.extra_banks = {ALT_BANK: self.page + bytes(8192), S['PG_C0'] // 2: self.code_pages, S['PG_W0'] // 2: work}


MONO = False
SCREEN = None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('z80', nargs='?', default=W + 'castle_master.z80')
    ap.add_argument('-o', default=W + 'castle_master_m2.nex')
    ap.add_argument('--asm', action='store_true')
    ap.add_argument('--prefix', default='cm2')
    ap.add_argument('--mono', action='store_true', help='col_on = 0: the original look (the .nxc colour set)')
    ap.add_argument('--screen', help='a 6,912-byte loading screen: the own screen of the image until the start-up code '
                    'puts the game screen back (cm11 on: scr_on; game data, local only)')
    a = ap.parse_args()
    global MONO, SCREEN
    MONO = a.mono
    SCREEN = open(a.screen, 'rb').read() if a.screen else None
    assert SCREEN is None or len(SCREEN) == 6912
    if a.asm:
        assemble(a.prefix)
    if a.prefix != 'cm2' and a.o.endswith('castle_master_m2.nex'):
        a.o = W + 'castle_master_%s.nex' % a.prefix.replace('cm', 'm')
    patch = CastlePatch(a.prefix)
    patch.for_check = True              # the boot check's reference: the game's own screen at the entry
    snap, tail_addr, tail, restore = zt.convert(a.z80, a.o, patch=CastlePatch(a.prefix))
    bad = nextboot.check(a.o, a.z80, patch, tail=(tail_addr, tail_addr + len(tail)))
    print('Boot check:', 'OK' if not bad else bad)
    if a.screen:
        print('Screen    : %s as the screen of the image; the start-up code puts the game screen back (scr_on)' % a.screen)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
