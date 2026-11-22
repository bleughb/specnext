"""Castle Master option (i) trial: what the colour view on Layer 2 over the ULA would look like, from the RZX.

Colour per pixel: every span the game fills is recorded at 0x969E (38558: H / D = the span's x ends 1-192,
(29662) = its line address -> buffer row, (29501) = the face's colour index 1-16) and painted in the game's
order (its own painter's algorithm). Pixels no span covered (sky / ground from the clear) get the index whose
dither pattern (table 53825, 4 bytes per index) matches the buffer byte on that line; 0 if none.
Layer 2 (192 x 112) replaces the ULA view area (pixel lines 32-143, x 32-223); everything else stays ULA.
PLACEHOLDER palette: the real one is the user's choice (pending).
Writes opt1_trial.png: per example frame, original | option (i). Usage: python opt1_trial.py [--shaded]  (--shaded: keep the game's dither, set pixel = face colour, clear
pixel = the area's paper; writes opt1_shaded.png)
"""
import sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
sys.path.insert(0, r'C:/1NEXT/castle_master_work')
from nexclash import simrun
from PIL import Image, ImageDraw
from e4_shots import render, PAL as ZX
FIX = '--fix' in sys.argv
SHADED = '--shaded' in sys.argv or FIX

BUF = 23740
FRAMES = [(1676, 'Wilderness: white-paper area'), (3406, 'Courtyard: centre marker (XOR, in buffer)'),
          (13523, 'ISR colour cycle'), (13525, 'ISR colour cycle, later step'), (13529, 'ISR colour cycle, later step'), (19652, 'Lobby: cursor (on screen)'),
          (20283, 'Message scroll (in buffer)'), (56672, 'Cavern')]
# PLACEHOLDER: 16 distinct colours for indices 1-16 (0 = nothing / black)
PAL = [(0, 0, 0), (40, 40, 48), (150, 150, 160), (196, 120, 70), (120, 160, 90), (90, 130, 200), (210, 190, 120),
       (170, 90, 90), (110, 110, 120), (225, 225, 230), (200, 160, 60), (80, 170, 170), (150, 110, 190),
       (100, 140, 70), (220, 140, 160), (60, 90, 150), (180, 200, 220)]


def main():
    st = {'sim': None, 'f': 0, 'isr': False, 'area': None}
    col = [bytearray(192) for _ in range(112)]
    painted = [bytearray(192) for _ in range(112)]
    ovl = set()                                  # buffer bytes drawn by an overlay writer since the last render
    spr = set()                                  # screen bytes written outside a copy since the last copy
    shown = {'col': None}                        # colour frame as of the last copy to the screen
    want = {f for f, _ in FRAMES}
    shots = {}

    class H:
        def on_sim(self, s):
            st['sim'] = s

        def on_interrupt(self, s, p):
            st['isr'] = True

        def on_frame(self, n):
            f = st['f']
            if f in want and shown['col'] is not None:
                m = st['sim'].memory
                shots[f] = (bytes(m[a] for a in range(0x4000, 0x5B00)), [bytes(r) for r in shown['col']], shown['buf'], st['area'], set(spr), shown['ovl'])
                if len(shots) == len(want):
                    raise SystemExit
            st['f'] = n

        def on_write(self, ad, v, pc, mem):
            if pc == 0xB368 and 0x5880 <= ad < 0x5A40:   # the area's own view colour
                st['area'] = v
            elif BUF <= ad < BUF + 112 * 24 and (0xCA42 <= pc <= 0xCC16 or 0xCF54 <= pc <= 0xCF68 or 0xBC9F <= pc <= 0xBD34):
                ovl.add(ad - BUF)                # text / marker / box / transition drawn into the buffer
            elif 0x4000 <= ad < 0x5800 and not (0xA38D <= pc < 0xA3F4 or pc == 0xB6C3):
                spr.add(ad)                      # drawn on the screen by something other than a copier

        def before(self, pc):
            if pc == 0xC161:
                st['isr'] = False
            if st['isr']:
                return
            m = st['sim'].memory
            if pc == 0xA3F4:                     # a new render: forget last frame's spans
                for r in painted:
                    r[:] = bytes(192)
                ovl.clear()
            elif pc == 38558:                    # inside the span routine, after its bounds checks
                R = st['sim'].registers
                a, b = R[6], R[4]                # H, D
                x0, x1 = min(a, b) - 1, max(a, b) - 1
                line = m[29662] | m[29663] << 8
                row = (line - BUF) // 24
                c = m[29501]
                if 0 <= row < 112:
                    for x in range(max(0, x0), min(191, x1) + 1):
                        col[row][x] = c
                        painted[row][x] = 1
            elif pc == 0xA38D or pc == 0xB6C3:   # a copy to the screen: fill the unpainted pixels from the dither
                for row in range(112):
                    for cx in range(24):
                        byte = m[BUF + row * 24 + cx]
                        idx = 0
                        for k in range(16):
                            if m[53825 + 4 * k + (row & 3)] == byte:
                                idx = k + 1
                                break
                        for bit in range(8):
                            x = cx * 8 + bit
                            if not painted[row][x]:
                                col[row][x] = idx
                shown['col'] = [bytearray(r) for r in col]
                shown['buf'] = bytes(m[BUF:BUF + 112 * 24])
                shown['ovl'] = set(ovl)
                spr.clear()

    simrun.play_rzx(r'C:/dev/castlemaster/castle.rzx', H(), stop=max(want) + 2)
    pad, top = 10, 20
    tiles = []
    for f, label in FRAMES:
        if f not in shots:
            print('no shot', f)
            continue
        scr, cview, buf, area, sprb, ovb = shots[f]
        orig = render(scr)
        new = orig.copy()
        px = new.load()
        notes = []
        if FIX:
            ats = {scr[0x1800 + r * 32 + c] for r in range(4, 18) for c in range(4, 28)}
            cyc = area is not None and ats != {area}
            notes.append('cycle palette ON' if cyc else 'cycle off')
            nspr = 0
        for y in range(112):
            sb = 0x4000 + (((32 + y) & 0xC0) << 5) + (((32 + y) & 7) << 8) + (((32 + y) & 0x38) << 2) - 0x4000
            for x in range(192):
                if FIX:
                    bit = 128 >> (x & 7)
                    on = buf[y * 24 + (x >> 3)] & bit
                    sv = scr[sb + 4 + (x >> 3)] & bit
                    at = scr[0x1800 + ((32 + y) >> 3) * 32 + 4 + (x >> 3)]
                    br = 8 if at & 64 else 0
                    ink, paper = ZX[(at & 7) + br], ZX[((at >> 3) & 7) + br]
                    if 0x4000 + sb + 4 + (x >> 3) in sprb and bool(sv) != bool(on):     # drawn on the screen after the copy -> hardware sprite pixel
                        px[32 + x, 32 + y] = ink if sv else paper
                        nspr += 1
                    elif on and (y * 24 + (x >> 3) in ovb or not cview[y][x]):   # overlay or unknown writer: the original ink
                        px[32 + x, 32 + y] = ink
                    elif cyc:                    # ISR cycle -> palette: every face index shows the ISR ink
                        px[32 + x, 32 + y] = ink if on else paper
                    else:
                        px[32 + x, 32 + y] = PAL[cview[y][x]] if on else paper
                elif SHADED:                       # the game's own dither: set pixel = face colour, clear = area paper
                    on = buf[y * 24 + (x >> 3)] & (128 >> (x & 7))
                    at = scr[0x1800 + ((32 + y) >> 3) * 32 + 4 + (x >> 3)]
                    paper = ZX[((at >> 3) & 7) + (8 if at & 64 else 0)]
                    px[32 + x, 32 + y] = PAL[cview[y][x]] if on else paper
                else:
                    px[32 + x, 32 + y] = PAL[cview[y][x]]
        if FIX:
            notes.append('sprite px %d' % nspr)
            print(f, label, notes)
        pair = Image.new('RGB', (2 * 512 + pad, 384 + top), (20, 20, 20))
        pair.paste(orig.resize((512, 384), Image.NEAREST), (0, top))
        pair.paste(new.resize((512, 384), Image.NEAREST), (512 + pad, top))
        d = ImageDraw.Draw(pair)
        d.text((4, 4), 'frame %d  %s   |   original' % (f, label), fill=(235, 235, 235))
        d.text((512 + pad + 4, 4), 'option (i)%s: Layer 2 on top - PLACEHOLDER palette %s' % (', shaded + sprite/cycle' if FIX else (', shaded' if SHADED else ''), ' '.join(notes)), fill=(255, 200, 120))
        tiles.append(pair)
    sheet = Image.new('RGB', (2 * 512 + 3 * pad, len(tiles) * (384 + top + pad) + pad), (10, 10, 10))
    for k, t in enumerate(tiles):
        sheet.paste(t, (pad, pad + k * (384 + top + pad)))
    sheet.save(r'C:/1NEXT/castle_master_work/opt1_%s.png' % ('fixed' if FIX else ('shaded' if SHADED else 'trial')))
    print('saved', len(tiles))
    return 0


if __name__ == '__main__':
    sys.exit(main())
