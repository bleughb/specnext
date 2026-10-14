# El Capitan Trueno: pack the shapes (shapes.json) into 4-bit 16x16 sprite patterns, page by page.
# Pixel index: 0 transparent, 1 black (mask without ink, or black ink), 2-8 Spectrum colours 1-7,
# 9-15 bright colours 1-7. Colour = the attribute the game paints in the cell under the pixel (the
# header attribute where no cell is painted). One palette for all sprites (palette offset 0).
# A shape = cols x rows patterns, row-major, never across an 8K page (64 patterns).
# Outputs:
#   patterns.bin - PAGES x 8192 bytes of patterns
#   shapedir.bin - 220 x 8 bytes, per frame: page index (0xFF = no shape), first pattern in the page
#                  (bits 0-5) + facing of the stored graphic (bit 7), cols, rows, dx, dy (signed, box
#                  offset from the descriptor's x*4-128 / y-68), pads (low nibble cols*16 - width,
#                  high nibble rows*16 - height: the shift when mirrored in x / y), mdx (box x offset
#                  when mirrored in x: the game flips inside the graphic's whole byte width)
#   blink.bin    - 220 bytes, 1 = the hit flash blinks (normal / hit shape on alternate renders): every
#                  figure; the hit shape is the normal drawing with bright red ink (yellow for red
#                  figures) and the black body kept (host's choice 2026-10-13 for the Captain, then for
#                  all: the game's white silhouette flashes the outline as a ragged white ring)
#   fdir.bin     - 220 x 2 bytes, per frame: page, first pattern of its hit-flash shape (descriptor
#                  bit 1: the whole silhouette in the header attribute's colour; same cols x rows)
#   palette.bin  - 256 sprite palette bytes (RRRGGGBB), block 0 = the colours above. No palette
#                  offsets are used: in MAME 0.289 index 0 under an offset is opaque (white boxes)
# Redrawn shapes (the host's sheet trueno/gfx/heroes_clean.png + .json, 2026-10-13): white = ink in the
# figure's header colour, black = body, pink = transparent; each cell is the shape's box grown by 1
# pixel on every side ("flipped": the sheet shows it mirrored). Their hit shape is the drawing inverted:
# white -> black, black -> the figure's colour (the host's choice). Needs the ULA free of figures (the
# pre-copy restore hook), because the redrawn body no longer covers the game's mask.
# Colour sheets (trueno/gfx/coins.png, from clean_sheet.py --raw): every non-pink pixel takes the
# nearest sprite palette colour (black = body); the hit shape is the same drawing. trueno/gfx/goblins.png
# (clean_sheet.py --colour): the same, but the hit shape has every non-black pixel in the hit colour.
# Usage: python patterns.py [frames.json]   (optional list of frame numbers to include)
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NFRAMES = 220
PER_PAGE = 64
BLINK = []                                  # no own blinking: the game toggles its hit bit itself
                                            # (blinking on top of it cancelled out when in phase)
HIT_INK, HIT_INK_RED = 0x42, 0x46           # hit colour: bright red; bright yellow for red figures
# Next default ULA colours (RRRGGGBB), ink 0-7 normal then bright (as nexclash/wally.py SPECCY)
SPECCY = [0x00, 0x02, 0xA0, 0xA2, 0x14, 0x16, 0xB4, 0xB6, 0x00, 0x03, 0xE0, 0xE7, 0x1C, 0x1F, 0xFC, 0xFF]


def colour_index(attr):
    ink, bright = attr & 7, attr >> 6 & 1
    return 1 if ink == 0 else 1 + ink + 7 * bright


def palette():
    return bytes([0x00, 0x00] + SPECCY[1:8] + SPECCY[9:16]).ljust(256, b'\0')


def shape_patterns(s, flash=False, ink=None):
    """flash: the whole mask in the header colour; ink: every ink pixel in this attribute's colour."""
    cols, rows = -(-s['w'] // 16), -(-s['h'] // 16)
    pats = []
    for r in range(rows):
        for c in range(cols):
            p = bytearray(128)
            for y in range(16):
                for x in range(16):
                    bx, by = c * 16 + x, r * 16 + y
                    v = 0
                    if 'idx' in s:
                        v = s['idx'][by][bx] if bx < s['w'] and by < s['h'] else 0
                    elif bx < s['w'] and by < s['h']:
                        if flash:
                            v = colour_index(s['attr']) if s['mask'][by][bx] == '1' else 0
                        elif s['ink'][by][bx] == '1':
                            a = s['cells'][(by + s['cy']) // 8][(bx + s['cx']) // 8]
                            v = colour_index(ink if ink is not None else s['attr'] if a < 0 else a)
                        elif s['mask'][by][bx] == '1':
                            v = 1
                    p[y * 8 + x // 2] |= v << 4 if x % 2 == 0 else v
            pats.append(bytes(p))
    return cols, rows, pats


def redrawn():
    """{frame: (normal shape, hit shape)} from the host's sheet, in shapes.json's format."""
    sheet = os.path.join(HERE, '..', 'gfx', 'heroes_clean.png')
    if not os.path.exists(sheet):
        return {}
    sys.path.insert(0, os.path.join(HERE, '..', '..', '_docs', 'lib'))
    from PIL import Image
    im = Image.open(sheet).convert('RGB')
    lay = json.load(open(os.path.splitext(sheet)[0] + '.json'))
    shapes = {}
    for sh in json.load(open(os.path.join(HERE, 'shapes.json'))):
        shapes.setdefault(sh['frame'], sh)
    out = {}
    for e in lay['frames']:
        f, s = e['frame'], shapes[e['frame']]
        grid = [[{(255, 255, 255): 2, (0, 0, 0): 1}.get(im.getpixel((e['x'] + x, e['y'] + y)), 0)
                 for x in range(e['w'])] for y in range(e['h'])]
        if e['flipped']:
            grid = [row[::-1] for row in grid]
        base = dict(s, w=e['w'], h=e['h'], dx=s['dx'] - 1, dy=s['dy'] - 1, mdx=s['mdx'] - 1,
                    cells=[[-1] * 8 for _ in range(8)], cx=0, cy=0)
        rows = lambda keep: [''.join('1' if v in keep else '0' for v in row) for row in grid]
        out[f] = (dict(base, ink=rows((2,)), mask=rows((1, 2))),      # white ink on the black body
                  dict(base, ink=rows((1,)), mask=rows((1, 2))))      # inverted: the body in the ink colour
    out.update(colour_sheet(os.path.join(HERE, '..', 'gfx', 'coins.png'), shapes))
    for name in ('goblins', 'creatures', 'rest', 'explosions'):     # host's sheets for hand editing
                                                                    # (2026-10-13; explosions = frames 0-3)
        out.update(colour_sheet(os.path.join(HERE, '..', 'gfx', name + '.png'), shapes, hit=True))
    return out


def colour_sheet(sheet, shapes, hit=False):
    """{frame: (shape, hit shape)} from a colour sheet: pink transparent, else the nearest colour.
    The hit shape is the same drawing, or with hit=True every non-black pixel in the hit colour."""
    if not os.path.exists(sheet):
        return {}
    from PIL import Image
    im = Image.open(sheet).convert('RGB')
    lay = json.load(open(os.path.splitext(sheet)[0] + '.json'))
    pal = [((c >> 5) * 255 // 7, (c >> 2 & 7) * 255 // 7, (c & 3) * 255 // 3) for c in palette()[1:16]]
    near = lambda rgb: 1 + min(range(15), key=lambda i: sum((a - b) ** 2 for a, b in zip(rgb, pal[i])))
    out = {}
    for e in lay['frames']:
        f, s = e['frame'], shapes[e['frame']]
        grid = [[0 if im.getpixel((e['x'] + x, e['y'] + y)) == tuple(lay['pink']) else
                 near(im.getpixel((e['x'] + x, e['y'] + y))) for x in range(e['w'])] for y in range(e['h'])]
        if e.get('flipped'):
            grid = [row[::-1] for row in grid]
        sh = dict(s, w=e['w'], h=e['h'], dx=s['dx'] - 1, dy=s['dy'] - 1, mdx=s['mdx'] - 1, idx=grid)
        red = colour_index(HIT_INK_RED if s['attr'] & 7 == 2 else HIT_INK)
        out[f] = (sh, dict(sh, idx=[[red if v > 1 else v for v in row] for row in grid]) if hit else sh)
    return out


def main():
    shapes = json.load(open(os.path.join(HERE, 'shapes.json')))
    redo = redrawn()
    only = set(json.load(open(sys.argv[1]))) if len(sys.argv) > 1 else None
    pages, cur = [], []
    shapedir = bytearray(b'\xFF' + bytes(7)) * NFRAMES
    seen = set()
    fdir = bytearray([0xFF, 0]) * NFRAMES
    kept = []
    for s in shapes:
        f = s['frame']
        if f in seen or (only is not None and f not in only):
            continue                        # frame 32: the second drawing is the mirror of the first
        seen.add(f)
        if f in redo:
            s = redo[f][0]
        kept.append(s)
        cols, rows, pats = shape_patterns(s)
        if len(pats) > PER_PAGE:
            raise SystemExit('frame %d: %d patterns do not fit a page' % (f, len(pats)))
        if len(cur) + len(pats) > PER_PAGE:
            pages.append(cur)
            cur = []
        shapedir[8 * f:8 * f + 8] = bytes([len(pages), len(cur) | s['facing'] << 7, cols, rows, s['dx'] & 255,
                                           s['dy'] & 255, cols * 16 - s['w'] | (rows * 16 - s['h']) << 4,
                                           s['mdx'] & 255])
        cur += pats
    for s in kept:                          # hit-flash silhouettes after all the normal shapes
        if s['frame'] in redo:
            cols, rows, pats = shape_patterns(redo[s['frame']][1])
        else:                               # the normal drawing in red ink (yellow for red figures)
            cols, rows, pats = shape_patterns(s, ink=HIT_INK_RED if s['attr'] & 7 == 2 else HIT_INK)
        if len(cur) + len(pats) > PER_PAGE:
            pages.append(cur)
            cur = []
        fdir[2 * s['frame']:2 * s['frame'] + 2] = bytes([len(pages), len(cur)])
        cur += pats
    if cur:
        pages.append(cur)
    blob = b''.join(b''.join(p).ljust(8192, b'\0') for p in pages)
    open(os.path.join(HERE, 'patterns.bin'), 'wb').write(blob)
    open(os.path.join(HERE, 'shapedir.bin'), 'wb').write(bytes(shapedir))
    open(os.path.join(HERE, 'palette.bin'), 'wb').write(palette())
    open(os.path.join(HERE, 'fdir.bin'), 'wb').write(bytes(fdir))
    open(os.path.join(HERE, 'blink.bin'), 'wb').write(bytes(1 if f in BLINK else 0 for f in range(NFRAMES)))
    print('redrawn:', sorted(redo))
    print('%d shapes, %d patterns, %d pages (%d KB)' % (len(seen), sum(map(len, pages)), len(pages), len(blob) // 1024))


if __name__ == '__main__':
    main()
