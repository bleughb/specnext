# The English texts (host, 2026-10-14). The game prints with its own letter codes: 0x00-0x19 = A-Z,
# 0x1A-0x23 = 0-9, 0x25 = the copyright sign, 0x26 = space, 0xFF = end. A printed item = x, y (pixels),
# then the codes. Lists of items are read one after another from their head (LD HL at 0x5DDE, 0x5FEC,
# 0x5FFA; no other reference into them), so a list is rebuilt whole; single strings are rewritten in
# place (never longer). Every old byte is checked against the snapshot.
# The snapshot shows the title already drawn (credits + menu): redraw() wipes the old words and prints
# the new ones with the game's own routines (0x5FE9 credits, 0x5FFD menu) in the simulator.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))

CODES = {**{chr(65 + i): i for i in range(26)}, **{str(i): 0x1A + i for i in range(10)}, '(c)': 0x25, ' ': 0x26}


def enc(x, y, text):
    out = [x, y]
    i = 0
    while i < len(text):
        if text.startswith('(c)', i):
            out.append(0x25)
            i += 3
        else:
            out.append(CODES[text[i]])
            i += 1
    return bytes(out + [0xFF])


TITLE = (0x10, 0x18, 'C A P I T A N   T R U E N O')
CODE = (0x68, 0x50, '270653')                       # the access code for part 2 (unchanged)
LISTS = [   # (head, old items, new items)
    (0x5DF3, [(0x48, 0x30, 'CLAVE DE ACCESO'), CODE],
             [(0x58, 0x30, 'ACCESS CODE'), CODE]),                  # centred: 4 letters shorter, x + 16
    (0x5E58, [(0x28, 0xA0, 'PROGRAMA  JAVIER BRAVO'), (0x28, 0xA8, 'GRAFICOS  RAUL ORTEGA'),
              (0x78, 0xB0, 'RUBEN RUBIO'), (0x1C, 0xB8, '(c) DINAMIC Y GAMESOFT 1989'), TITLE],
             [(0x48, 0xA0, 'CODE  JAVIER BRAVO'), (0x28, 0xA8, 'GRAPHICS  RAUL ORTEGA'),   # names stay in
              (0x78, 0xB0, 'RUBEN RUBIO'), (0x14, 0xB8, '(c) DINAMIC AND GAMESOFT 1989'), TITLE]),  # line
    (0x5ED1, [(0x58, 0x30, '1 TECLADO'), (0x58, 0x40, '2 KEMPSTON'), (0x58, 0x50, '3 SINCLAIR'),
              (0x58, 0x60, '4 REDEFINIR')],                         # item 5 (COLOR ON) stays, unused
             [(0x58, 0x30, '1 KEYBOARD'), (0x58, 0x40, '2 KEMPSTON'), (0x58, 0x50, '3 SINCLAIR'),
              (0x58, 0x60, '4 REDEFINE')]),
]
WORDS = [   # in place, at the label pointers of the table 0x5F13 (4 bytes each: label, key variable)
    ('ARRIBA', 'UP'), ('ABAJO', 'DOWN'), ('IZQUIERDA', 'LEFT'), ('DERECHA', 'RIGHT'), ('GOLPE', 'FIRE'),
    ('CAPITAN', 'CAPTAIN'), ('CRISPIN', 'CRISPIN'), ('GOLIATH', 'GOLIATH'), ('PAUSA', 'PAUSE'),
    ('ABORT', 'ABORT')]
SINGLE = [(0xE904, (0x90, 0x20, 'CONTINUAR'), (0x90, 0x20, 'CONTINUE'))]   # the pause window


def sites(mem):
    """[(address, old bytes, new bytes)] for the English texts; mem = 64K of the snapshot."""
    out = []
    for head, old, new in LISTS:
        ob, nb = b''.join(enc(*i) for i in old), b''.join(enc(*i) for i in new)
        if len(nb) > len(ob):
            raise ValueError('list 0x%04X: the English list is longer' % head)
        out.append((head, ob, nb))
    for k, (old, new) in enumerate(WORDS):
        p = mem[0x5F13 + 4 * k] | mem[0x5F14 + 4 * k] << 8
        x, y = mem[p], mem[p + 1]
        ob, nb = enc(x, y, old), enc(x, y, new)
        assert len(nb) <= len(ob)
        out.append((p, ob, nb))
    for a, old, new in SINGLE:
        ob, nb = enc(*old), enc(*new)
        assert len(nb) <= len(ob)
        out.append((a, ob, nb))
    return out


def screen_addr(x, y):
    return 0x4000 | (y & 0xC0) << 5 | (y & 7) << 8 | (y & 0x38) << 2 | x >> 3


def redraw(mem):
    """mem: 64K after the text sites (ROM 0x0000-0x3FFF not needed). Wipes the old credits and menu
    words on the title screen and prints the new lists with the game's routines. Returns the new
    0x4000-0x5AFF."""
    from skoolkit.simulator import Simulator
    from skoolkit.simutils import PC, SP, IYh, IYl
    m = bytearray(mem)
    rom = os.path.join(HERE, '..', 'lib', 'skoolkit', 'resources', '48.rom')
    m[0:0x4000] = open(rom, 'rb').read()
    for head, old, new in LISTS[1:]:
        for x, y, text in old:
            w = len(enc(0, 0, text)) - 3
            for yy in range(y, y + 8):
                for xx in range(x, x + 8 * w):
                    m[screen_addr(xx, yy)] &= ~(0x80 >> (xx & 7)) & 0xFF
    for start in (0x5FE9, 0x5FFD):                  # credits (5 items), menu (4 items)
        sim = Simulator(m)
        r = sim.registers
        r[SP] = 0xEEE0 - 2
        m[r[SP]:r[SP] + 2] = bytes(2)               # return to 0x0000 = done
        r[PC] = start
        r[IYh], r[IYl] = 0x60, 0xF8                 # as in the game: 0x5FF2 tests (IY+0x13) bit 0 = a 5th item
        while r[PC]:
            sim.run()
    return bytes(m[0x4000:0x5B00])
