"""Castle Master M2 harness: the integrated build's memory as on the Next, in SkoolKit's stock simulator + nexclash.z80n.

Next(ram): the game's RAM in its own 8K pages (10, 11, 4, 5, 0, 1 in MMU slots 2-7), the alt ROM (Sinclair's ROM +
cm2_rom.bin at SHARED) in slots 0-1, the renderer's pages (cm2_page.bin = PG_C0 / PG_C1, work RAM PG_W0 / PG_W1 with
the tables the build copies from the snapshot), the patch sites applied (original bytes checked). NEXTREG 0x50-0x57
swap 8K pages in and out of the 64K list; 0x07 is the speed; ports 0x243B / 0x253B read registers back.
run(stop): steps instructions; a frame interrupt every FRAME 28 MHz-T (an instruction at 3.5 MHz counts 8x), held for
PULSE; one that finds interrupts off for the whole pulse is LOST (counted). Each interrupt entry is checked: at
0xC01F the game's pages must be in slots 2-7, the speed the game's, SP on the game's stack.
"""
import os, subprocess, sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import z80n
from nexclash.z80tonex import rom48
from skoolkit.simulator import Simulator

W = r'C:/1NEXT/castle_master_work/'
SJ = os.path.expanduser(r'~/.cache/nexclash/sjasmplus-1.24.0/sjasmplus')
LIB = r'C:/1NEXT/nexclash/asm/lib'
GAME = [0xFF, 0xFF, 10, 11, 4, 5, 0, 1]
FRAME, PULSE = 69888 * 8, 32 * 8
SP, PC, T, IFF = 12, 24, 25, 26
SITES = [(0x855E, 'cd4f8d', 0xCD, 'h_geom'), (0x8599, 'cda39e', 0xCD, 'h_rast'), (0x859C, 'cd199f', 0xCD, 'h_show'),
         (0xB635, 'cda39e', 0xCD, 'h_rast'), (0xB638, 'cd8da3', 0xCD, 'h_flip'), (0xFDFD, 'c31fc0', 0xC3, 'isr_e')]
SITES3 = (SITES
          + [(0xC68B, 'f33dcb27', 0xCD, 'h_snd_in'), (0xC7F2, 'f1fbc1', 0xCD, 'h_snd_out'),
             (0xCA4E, 'dde5fde5', 0xC3, 'h_prn'), (0xCBFF, 'f1c1d1', 0xC3, 'h_prn_out'),
             (0xCDD2, 'dde5fde5', 0xC3, 'h_cdraw'), (0xCECD, 'dde5e5', 0xC3, 'h_crest'),
             (0xB66E, 'dde5fde5e5', 0xC3, 'h_diss'), (0xCFC2, 'dde5fde5', 0xC3, 'h_portc')]
          + [(a, '3a7773b720fa', 0xCD, 'h_w77') for a in (0x839C, 0x8505, 0x85AD, 0xB1E8, 0xB44F, 0xB506, 0xBD5E,
                                                          0xBEB9, 0xC52A, 0xC54A)]
          + [(a, '3a7773b720fa', 0xCD, 'h_w77p') for a in (0xCFE9, 0xD00F)]       # the portcullis's steps
          + [(a, '3a4a73b728fa', 0xCD, 'h_w4a') for a in (0x9F8C, 0x9F9D)])
VP = 0xFE40                             # cm3: hlib_pace's state + flags (40 bytes zero in the image, K at +28)
TABLES = (('tmpl', 27486, 334), ('sincos', 29337, 146), ('pano', 30660, 288), ('lgfx', 31085, 688))


def assemble(name='cm2'):
    r = subprocess.run([SJ, '--nologo', '--zxnext', '-I' + LIB, '--sym=%s.sym' % name, '%s.asm' % name], cwd=W,
                       capture_output=True, text=True)
    if r.returncode or 'Errors: 0,' not in r.stdout + r.stderr:      # (a failed ASSERT exits 0)
        raise RuntimeError(r.stdout + r.stderr)
    return r.stdout


def syms(name='cm2'):
    d = {}
    for line in open(W + name + '.sym'):
        if ':' in line and 'EQU' in line:
            k, v = line.split(':', 1)
            d[k.strip()] = int(v.split('EQU')[1].strip().replace('0x', ''), 16)
    return d


def sites_for(S):
    return [x for x in SITES3 if x[3] in S] if 'h_prn' in S else SITES


def site_bytes(S):
    return [(a, bytes.fromhex(old), bytes([op, S[sym] & 255, S[sym] >> 8]) + bytes(len(old) // 2 - 3))
            for a, old, op, sym in sites_for(S)]


def work_image(S, ram):
    """PG_W0 + PG_W1 as the build writes them: zero, the game's constant tables, the first Layer 2 roles"""
    w = bytearray(16384)
    for name, src, n in TABLES:
        w[S[name] - 0x4000:S[name] - 0x4000 + n] = bytes(ram[src:src + n])
    w[S['l2shown'] - 0x4000] = S['PG_LA']
    w[S['in_l2page'] - 0x4000] = S['PG_LB']
    w[S['cur54'] - 0x4000], w[S['cur55'] - 0x4000] = 4, 5
    if 'l2last' in S:
        w[S['l2last'] - 0x4000] = S['PG_LA']
        o = S['sincos'] - 0x4000        # entry 72 = entry 0 (in-between angles read one entry on)
        w[o + 144:o + 146] = w[o:o + 2]
        w[S['t_fin'] - 0x4000:S['t_fin'] - 0x4000 + 2] = (400).to_bytes(2, 'little')
    return bytes(w)


def alt_rom(S, prefix='cm2'):
    rom = bytearray(rom48())
    b = open(W + prefix + '_rom.bin', 'rb').read()
    assert all(x == 0xFF for x in rom[max(S['SHARED'], 0x386E):min(S['SHARED'] + len(b) + 20, 0x3D00)])   # below 0x386E: m3b_rom.py
    rom[S['SHARED']:S['SHARED'] + len(b)] = b
    return bytes(rom)


class Next:
    def __init__(self, ram, prefix='cm2', S=None, sites=True, period=FRAME, rng=None, k16=128):
        self.S = S = S or syms(prefix)
        self.rom = alt_rom(S, prefix)
        page = open(W + prefix + '_page.bin', 'rb').read()
        wk = work_image(S, ram)
        self.pages = {S['PG_C0']: list(page[:8192]), S['PG_C1']: list(page[8192:]),
                      S['PG_W0']: list(wk[:8192]), S['PG_W1']: list(wk[8192:])}
        g = bytearray(ram[0x4000:0x10000])
        if sites:
            for a, old, new in site_bytes(S):
                assert bytes(g[a - 0x4000:a - 0x4000 + len(old)]) == old, 'site %04X' % a
                g[a - 0x4000:a - 0x4000 + len(old)] = new
        self.inside = set()
        if sites:
            for a, old, new in site_bytes(S):
                self.inside.update(range(a + 1, a + 3))
        if 'h_prn' in S:                # the start-up code's part
            g[VP - 0x4000:VP - 0x4000 + 40] = bytes(40)
            g[VP + 28 - 0x4000] = k16
        self.mem = list(self.rom) + list(g)
        self.slots = list(GAME)
        self.nr = {7: 0, 0x12: 9, 0x69: 0}
        self.sel = 0
        self.pal = {}                   # Layer 2 palette (NR 0x43 bits 6:4 = 1), index -> RGB332
        self.spal = {}                  # sprite palette (bits 6:4 = 2)
        self.pat = bytearray(16384)     # sprite pattern RAM (port 0x5B, slot by 0x303B)
        self.sattr = [bytearray(5) for _ in range(128)]     # sprite attributes (port 0x57)
        self.pidx = self.aidx = self.abyte = 0
        self.sim = Simulator(self.mem, {})
        self.sim.int_active = 0         # LD A,I / R: P/V reads IFF; the NMOS quirk (P/V 0 when an interrupt is
                                        # accepted at its end) is run()'s, on this model's interrupts, not the stock
                                        # simulator's 48K frame (which cleared it at random here: HLIB_IFF_DI then EI lost)
        z80n.install(self.sim, nextreg=self.nextreg)
        self.sim.set_tracer(self)
        self.R = self.sim.registers
        self.period, self.rng = period, rng
        self.acc = 0
        self.clock = 0                  # 28 MHz T since the start
        self.minsp = 0xFFFF
        self.count_main = False         # count the game's own main-line instructions (path check, m3_sim --pace)
        self.nmain = 0
        self.inisr = False
        self.skip_main = {0xFDFD}       # sites (their bytes differ between the builds) and the vector's JP
        for a, old, op, sym in SITES3:
            self.skip_main.update(range(a, a + len(old) // 2))
        self.pending = None
        if 'setup_spr' in S:            # the start-up code's sprite part (the rest: the image, work_image)
            self.run_setup_spr(prefix)
        self.pending = None
        self.irqs = self.lost = 0
        self.lost_at = []
        self.bad = []
        self.irq_log = []

    def run_setup_spr(self, prefix):
        """run setup_spr as the start-up code does (from 0xD000's copy, interrupts off), game RAM put back"""
        S, m, R = self.S, self.mem, self.R
        b = open(W + prefix + '_setup.bin', 'rb').read()
        keep = (m[0xD000:0xD000 + len(b)], m[0x5BF0:0x5C00])
        m[0xD000:0xD000 + len(b)] = list(b)
        regs = list(R)
        R[PC], R[SP], R[IFF] = S['setup_spr'], 0x5C00, 0
        R[SP] -= 2
        m[R[SP]], m[R[SP] + 1] = 0x00, 0x5B
        period, self.period, self.bad = self.period, 0, []
        self.run(0x5B00, max_ins=200_000)
        bad = self.bad
        self.period, self.bad = period, bad
        m[0xD000:0xD000 + len(b)], m[0x5BF0:0x5C00] = keep
        R[:] = regs
        self.clock = self.acc = 0

    # ---- Next model
    def map(self, slot, page):
        m, lo = self.mem, slot * 8192
        cur = self.slots[slot]
        if cur != 0xFF:
            self.pages[cur] = m[lo:lo + 8192]
        if page == 0xFF:
            if slot > 1:
                raise RuntimeError('ROM in slot %d' % slot)
            m[lo:lo + 8192] = list(self.rom[lo:lo + 8192])
        else:
            if page in self.slots:
                o = self.slots.index(page) * 8192          # the same page in two slots: one copy only
                if self.slots.index(page) != slot:
                    self.pages[page] = m[o:o + 8192]
                    self.bad.append('page %d in two slots' % page) if page not in (10, 11) else None
            m[lo:lo + 8192] = self.pages.get(page) or [0] * 8192
        self.slots[slot] = page

    def nextreg(self, reg, v):
        if 0x50 <= reg <= 0x57:
            self.map(reg - 0x50, v)
        self.nr[reg] = v
        if reg == 0x41:
            sel = self.nr.get(0x43, 0) >> 4 & 7
            if sel == 1:
                self.pal[self.nr.get(0x40, 0) & 255] = v
            elif sel == 2:
                self.spal[self.nr.get(0x40, 0) & 255] = v
            else:
                self.bad.append('palette write to palette %d' % sel)
            if not self.nr.get(0x43, 0) & 0x80:
                self.nr[0x40] = (self.nr.get(0x40, 0) + 1) & 255

    def read_port(self, regs, port):
        if port == 0x253B:
            if self.sel == 7:
                return (self.nr[7] & 3) * 0x11
            if self.sel in (0x1E, 0x1F):        # the video line: the interrupt comes at line 248
                line = (self.acc * 312 // FRAME + 248) % 312
                return line >> 8 if self.sel == 0x1E else line & 255
            if 0x50 <= self.sel <= 0x57:            # MMU: the page mapped now (0xFF = ROM), written or not
                return self.slots[self.sel - 0x50]
            return self.nr.get(self.sel, 0)
        return 0xFF

    def write_port(self, regs, port, value, *x):
        if port == 0x243B:
            self.sel = value
        elif port == 0x253B:
            self.nextreg(self.sel, value)
        elif port == 0x303B:            # pattern slot (bits 5:0, bit 7 = +128 bytes) and attribute index (bits 6:0)
            self.pidx = (value & 0x3F) << 8 | (value & 0x80)
            self.aidx, self.abyte = value & 0x7F, 0
        elif port & 255 == 0x5B:
            self.pat[self.pidx] = value
            self.pidx = (self.pidx + 1) & 0x3FFF
        elif port & 255 == 0x57:
            a = self.sattr[self.aidx]
            a[self.abyte] = value
            self.abyte += 1
            if self.abyte == 5 or self.abyte == 4 and not a[3] & 0x40:
                self.abyte, self.aidx = 0, (self.aidx + 1) & 127

    def sprite_pixels(self):
        """the visible 4-bit sprites' opaque pixels: {(x, y): RGB332} in screen pixels (0-255, 0-191); no scaling,
        mirroring or rotation (the build uses none: a sprite using them is reported in self.bad)"""
        out = {}
        if not self.nr.get(0x15, 0) & 1:
            return out
        tr = self.nr.get(0x4B, 0xE3) & 15
        for k in range(128):                    # sprite 127 on top (NR 0x15 bit 6 = 0); the grid never overlaps
            a = self.sattr[k]
            if not a[3] & 0x80:
                continue
            if not (a[3] & 0x40 and a[4] & 0x80) or a[2] & 0x0E or a[4] & 0x1E:
                self.bad.append('sprite %d: not a plain 4-bit sprite %s' % (k, a.hex()))
                continue
            x = a[0] | (a[2] & 1) << 8
            y = a[1] | (a[4] & 1) << 8
            p = (a[3] & 0x3F) << 8 | (a[4] & 0x40) << 1
            off = a[2] & 0xF0
            for r in range(16):
                for c in range(16):
                    b = self.pat[p + r * 8 + c // 2]
                    v = b >> 4 if c % 2 == 0 else b & 15
                    if v != tr:
                        out[(x - 32 + c, y - 32 + r)] = self.spal.get(off + v)
        return out

    def page(self, p):
        """a page's bytes now (from the 64K list when mapped)"""
        if p in self.slots:
            o = self.slots.index(p) * 8192
            return self.mem[o:o + 8192]
        return self.pages.get(p) or [0] * 8192

    def game_ram(self):
        """the game's 0x4000-0xFFFF now"""
        out = []
        for p in GAME[2:]:
            out += self.page(p)
        return out

    # ---- run
    def run(self, stop, watch=None, max_ins=30_000_000):
        R, m, ops = self.R, self.mem, self.sim.opcodes
        n = 0
        while R[PC] != stop:
            pc = R[PC]
            if watch and pc in watch:
                watch[pc](self)
            if pc in self.inside and self.slots[4:] == GAME[4:]:
                self.bad.append('execution inside a patched site: %04X' % pc)
            if pc == 0xC01F:
                self.irq_log.append((list(self.slots), self.nr[7] & 3, R[SP]))
                self.minsp = min(self.minsp, R[SP])
                if self.slots[2:] != GAME[2:] or R[SP] < 0xFF10:
                    self.bad.append('ISR entry: slots %s speed %d SP %04X' % (self.slots, self.nr[7] & 3, R[SP]))
            op = m[pc]
            if self.count_main:
                if pc == 0xC01F:
                    self.inisr = True
                elif pc == 0xC161:
                    self.inisr = False
                elif pc >= 0x4000 and not self.inisr and pc not in self.skip_main and self.slots[2] == 10:
                    self.nmain += 1
            t0 = R[T]
            ops[op]()
            n += 1
            if n > max_ins:
                self.bad.append('instruction limit at %04X' % R[PC])
                return False
            if not self.period:
                continue
            dt = R[T] - t0
            if not self.nr[7] & 3:
                dt *= 8
            self.acc += dt
            self.clock += dt
            if self.pending is None and self.acc >= self.period:
                self.acc -= self.period if self.rng is None else self.rng.randrange(self.period // 2, self.period * 3 // 2)
                self.pending = PULSE
                dt = 0
            if self.pending is not None:
                self.pending -= dt
                if R[IFF] and op != 0xFB:
                    self.pending = None
                    self.irqs += 1
                    if op == 0xED and m[(pc + 1) & 0xFFFF] in (0x57, 0x5F):
                        R[1] &= 0xFB            # LD A,I / R: P/V reads 0 when the interrupt is accepted at its end
                    R[IFF] = 0
                    sp = (R[SP] - 2) & 0xFFFF
                    if sp < 0x4000:
                        self.bad.append('interrupt with SP %04X' % sp)
                    else:
                        m[sp], m[sp + 1] = R[PC] & 255, R[PC] >> 8
                    R[SP] = sp
                    R[PC] = m[0xFEFF] | m[0xFF00] << 8
                    R[T] += 19
                elif self.pending <= 0:
                    self.pending = None
                    self.lost += 1
                    self.lost_at.append((self.clock, R[PC], list(self.slots)))
        return True
