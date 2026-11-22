"""Castle Master E4 examples: real screens from the RZX, one per overlay kind, overlay area outlined.

Screen = RAM 0x4000-0x5AFF at a frame's end. For a writer into the view buffer the screen is taken at the end
of the first frame in which a buffer copy (0xA38D / 0xB6C3) finished after the write (that is when it shows).
Writes e4_examples.png (contact sheet). Usage: python -I e4_shots.py
"""
import sys
sys.path.insert(0, r'C:/1NEXT/nexclash')
from nexclash import simrun
from PIL import Image, ImageDraw, ImageFont

BUF0, BUF1 = 0x5CBC, 0x6754
COPIERS = set(range(0xA38D, 0xA3F4)) | {0xB6C3}
# label, writer PCs, 'scr' / 'buf' / 'attr', which distinct frame to show
EX = [
    ('Cursor / crosshair (0xCEAF/0xCF39) - screen', {0xCEAF, 0xCF39}, 'scr', 300),
    ('Printer into the view area (0xCB00-0xCB63) - screen', {0xCB00, 0xCB3B, 0xCB63}, 'scr', 1),
    ('Second copier (0xB6C3) - screen', {0xB6C3}, 'scr', 100),
    ('Masked sprite (0xD0F9-0xD146) - screen', {0xD0F9, 0xD0FB, 0xD0FD, 0xD138, 0xD13D, 0xD146}, 'scr', 40),
    ('Centre marker, XOR (0xCF54-0xCF68) - buffer', {0xCF54, 0xCF5B, 0xCF60, 0xCF68}, 'buf', 80),
    ('Printer text (0xCA97-0xCC16) - buffer', {0xCA97, 0xCAA4, 0xCAF5, 0xCB00, 0xCB3B, 0xCB63, 0xCBBA, 0xCBEB,
                                               0xCC14, 0xCC16}, 'buf', 60),
    ('Full-view effect (0xCA42) - buffer', {0xCA42}, 'buf', 6),
    ('Box (0xBC9F-0xBD34) - buffer', {0xBC9F, 0xBCA3, 0xBCCA, 0xBCCE, 0xBD2A, 0xBD30, 0xBD34}, 'buf', 3),
    ('Area colours, white paper (0xB368) - attributes', {0xB368}, 'white', 1),
    ('ISR colour cycle (0xC069) - attributes', {0xC069}, 'attr', 120),
]
PAL = [(0, 0, 0), (0, 0, 205), (205, 0, 0), (205, 0, 205), (0, 205, 0), (0, 205, 205), (205, 205, 0), (205, 205, 205),
       (0, 0, 0), (0, 0, 255), (255, 0, 0), (255, 0, 255), (0, 255, 0), (0, 255, 255), (255, 255, 0), (255, 255, 255)]


def render(scr):
    im = Image.new('RGB', (256, 192))
    px = im.load()
    for y in range(192):
        base = 0x4000 + ((y & 0xC0) << 5) + ((y & 7) << 8) + ((y & 0x38) << 2)
        for cx in range(32):
            b = scr[base + cx - 0x4000]
            at = scr[0x1800 + (y >> 3) * 32 + cx]
            br = 8 if at & 64 else 0
            ink, paper = PAL[(at & 7) + br], PAL[((at >> 3) & 7) + br]
            for bit in range(8):
                px[cx * 8 + bit, y] = ink if b & (128 >> bit) else paper
    return im


def scr_yx(a):
    o = a - 0x4000
    return ((o >> 11) << 6) | ((o >> 5) & 7) << 3 | (o >> 8) & 7, o & 31


def main():
    st = {'f': 0, 'sim': None, 'isr': False}
    seen = [set() for _ in EX]
    hits = [dict() for _ in EX]          # frame -> set of addresses
    shots = [None] * len(EX)
    wait = {}                            # example index -> (frame chosen, copier bytes since)
    copied = [0]

    def screen():
        m = st['sim'].memory
        return bytes(m[a] for a in range(0x4000, 0x5B00))

    class H:
        def on_sim(self, s):
            st['sim'] = s

        def on_interrupt(self, s, p):
            st['isr'] = True

        def before(self, pc):
            if pc == 0xC161:
                st['isr'] = False

        def on_frame(self, n):
            f = st['f']
            if st['sim'] is not None and f:
                m = st['sim'].memory
                for i, (lab, pcs, kind, nth) in enumerate(EX):
                    if shots[i] is not None:
                        continue
                    if kind == 'white':
                        at = m[0x5884]
                        if (at >> 3) & 7 == 7 and f in hits[i]:
                            seen[i].add(f)
                            if len(seen[i]) >= nth:
                                shots[i] = (f, screen(), [(32, 4, 143, 27)])
                        continue
                    if f in hits[i] and i not in wait:
                        seen[i].add(f)
                        if len(seen[i]) == nth:
                            if kind == 'buf':
                                wait[i] = (f, copied[0])
                            else:
                                shots[i] = (f, screen(), hits[i][f])
                    if i in wait and copied[0] - wait[i][1] >= 2688:
                        f0 = wait.pop(i)[0]
                        shots[i] = (f, screen(), hits[i][f0])
            st['f'] = n
            if all(s is not None for s in shots):
                raise SystemExit

        def on_write(self, ad, v, pc, mem):
            if pc in COPIERS and 0x4000 <= ad < 0x5800:
                copied[0] += 1
            for i, (lab, pcs, kind, nth) in enumerate(EX):
                if pc in pcs and shots[i] is None:
                    ok = (kind == 'buf' and BUF0 <= ad < BUF1) or (kind == 'scr' and 0x4000 <= ad < 0x5800 and 32 <= scr_yx(ad)[0] <= 143 and 4 <= scr_yx(ad)[1] <= 27) or \
                         (kind in ('attr', 'white') and 0x5880 <= ad < 0x5A40)
                    if ok:
                        hits[i].setdefault(st['f'], set()).add(ad)

    simrun.play_rzx(r'C:/dev/castlemaster/castle.rzx', H(), stop=167134)
    S, pad, top = 2, 12, 22
    tiles = []
    for i, (lab, pcs, kind, nth) in enumerate(EX):
        if shots[i] is None:
            print('no example for', lab)
            continue
        f, scr, adds = shots[i]
        im = render(scr).resize((512, 384), Image.NEAREST)
        d = ImageDraw.Draw(im)
        if kind == 'buf':
            rows = [(a - BUF0) // 24 for a in adds]
            cols = [(a - BUF0) % 24 for a in adds]
            box = (32 + min(rows), 4 + min(cols), 32 + max(rows), 4 + max(cols))
        elif kind == 'scr':
            yx = [scr_yx(a) for a in adds if a < 0x5800]
            box = (min(y for y, _ in yx), min(x for _, x in yx), max(y for y, _ in yx), max(x for _, x in yx))
        else:
            box = (32, 4, 143, 27)
        y0, x0, y1, x1 = box
        d.rectangle((x0 * 16 - 2, y0 * 2 - 2, x1 * 16 + 17, y1 * 2 + 3), outline=(255, 40, 40), width=3)
        tile = Image.new('RGB', (512, 384 + top), (24, 24, 24))
        tile.paste(im, (0, top))
        ImageDraw.Draw(tile).text((4, 4), '%s   [frame %d]' % (lab, f), fill=(240, 240, 240))
        tiles.append(tile)
        print('%-55s frame %d' % (lab, f))
    cols = 2
    rows = (len(tiles) + 1) // cols
    sheet = Image.new('RGB', (cols * 512 + (cols + 1) * pad, rows * (384 + top) + (rows + 1) * pad), (12, 12, 12))
    for k, t in enumerate(tiles):
        sheet.paste(t, (pad + (k % cols) * (512 + pad), pad + (k // cols) * (384 + top + pad)))
    sheet.save(r'C:/1NEXT/castle_master_work/e4_examples.png')
    return 0


if __name__ == '__main__':
    sys.exit(main())
