"""R-Type colour sheets and recolour for the Layer 2 + sprite prototype (owner request 2026-11-16).

Colours stay the game's own until the user paints a sheet; painting and import follow the normal
process (nexclash docs/COLOURS.md: coloursheet sheets, read-back, three-way merge, recolour bundle).
Until R-Type has an evidence record, run the import with this module instead of `nexclash.py
recolour` (same code path: nexclash.recolour.run with this engine):

    python r_type_colour.py sheets [-o DIR]                          the sheets, one pair per level
    python r_type_colour.py recolour BUILD.nex PAINTED.png [-o OUT_painted.nex] [--onto MAP | --replace]
    python r_type_colour.py figures PATCH.json                       names / layers into r_type_figures.json

Keys: one per graphics byte, 'LL:AAAA' = level byte (7 19C, '0'..'9') : address of the byte in the
unpacked graphic stream; check = the byte's value; bit 0 = leftmost pixel. Defaults: ink = the
cell's ink (black ink on coloured paper = opaque black), coloured paper drawn, black paper clear
(paintable: paint_clear). Grey = transparent (clear=True). Flash colours (8EB1 ink override) are not
painted: a forced-ink draw keeps the forced colour.

Runtime (l2sprites_body.asm col_lookup): colour data only in banks 32..47 (pages 64..95), which the
game never maps. Page 64: a directory per level (count, first) then the sorted cell addresses;
pages 65..: 40-byte records per painted cell (8 lines x 4 bytes of nibbles, left pixel high, 0 =
default; then 8 transparent masks, bit 7 = leftmost). Patterns are converted once per graphic, so
the lookup costs only at conversion. The graphic stream is unpacked per level into the same
addresses: the level is part of every key.

The sheets are built from the whole-recording figure corpus (continuation/assets.json.gz: objects
joined by the game's own 9-byte object / owner, capture_assets.py); a later recording that reaches
more figures gives a second sheet read into the same colours file.
"""
import collections
import gzip
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REF = HERE.parent
ROOT = HERE.parents[3] / 'nexclash'
sys.path[:0] = [str(ROOT)]

RECORD = 'r_type'
COLOURS = str(ROOT / 'docs' / 'profiles' / (RECORD + '_colours.json'))
COLOUR_BANKS = list(range(32, 48))
DIR_PAGE, REC_PAGE0, LAST_PAGE = 64, 65, 95
REC = 40
PER_PAGE = 8192 // REC
DIR_ENTRIES = (8192 - 64) // 2
PALETTE = [0x00, 0x02, 0xA0, 0xA2, 0x14, 0x16, 0xB4, 0xB6,
           0x00, 0x03, 0xE0, 0xE7, 0x1C, 0x1F, 0xFC, 0xFF]       # l2scroll.asm col_tab
LEVEL_NAMES = {0x30: 'TEXT'}
ART_BANKS = (3, 4, 6, 7)        # the same in every snapshot of the recording: packed level data
NOTE = ('R-Type colour map (docs/COLOURS.md): key = level:graphics byte (hex; check = its value), 8 '
        'nibbles (0 = the cell default), optional 4th = transparent mask')
RECOLOUR = {'game': RECORD, 'output': 'sprites', 'colours': COLOURS, 'clear': True, 'note': NOTE}


def level_name(lv):
    return LEVEL_NAMES.get(lv, 'LEVEL%d' % (lv - 0x30))


def corpus():
    return json.loads(gzip.decompress((HERE / 'continuation' / 'assets.json.gz').read_bytes()))


def defaults(attr):
    """(ink index or 0, paper index or 0) for a cell attribute, as the sprite converter draws it."""
    bright = 8 if attr & 0x40 else 0
    paper = (attr >> 3) & 7
    pap = paper + bright if paper else 0
    ink = attr & 7
    if ink:
        return ink + bright, pap
    return (8 if pap else 0), pap


def cell_part_pixels(cell, cx, cy):
    """Coloursheet pixels of one 8x8 cell placed at cell (cx, cy) of its plot."""
    ink, pap = defaults(cell['attribute'])
    px = []
    for line, byte in enumerate(cell['bits']):
        key = '%02X:%04X' % (cell['level'], (cell['address'] + 1 + line) & 0xFFFF)
        for bit in range(8):
            if byte & (0x80 >> bit):
                code, d = (1, ink) if ink else (0, 0)
            else:
                code, d = (2, pap) if pap else (0, 0)
            px.append((cx * 8 + bit, cy * 8 + line, key, bit, code, d))
    return px


def plain_cell(cell):
    """True when the corpus cell was drawn without an ink override (its ink is the attribute's)."""
    a = cell['attribute']
    return cell['ink'] == (((a & 7) + (8 if a & 64 else 0)) or 8)


def composites(data):
    """{level: [composite]} for coloursheet.write: one composite per distinct figure (game object)."""
    cells, plots = data['cells'], data['plots']
    parts_cache = {}

    def part(pk):
        if pk not in parts_cache:
            p = plots[pk]
            px, ent, ok = [], {}, True
            for cx, cy, ck in p['cells']:
                c = cells[ck]
                ok &= plain_cell(c)
                px += cell_part_pixels(c, cx, cy)
                for line, byte in enumerate(c['bits']):
                    ent['%02X:%04X' % (c['level'], (c['address'] + 1 + line) & 0xFFFF)] = [byte, 'g']
            parts_cache[pk] = (dict(id=pk, size=len(p['cells']), w=p['w'], h=p['h'], pixels=px,
                                    entries=ent), ok)
        return parts_cache[pk]
    out = collections.defaultdict(list)
    for fig in data['figures']:
        built, ok = [], True
        for q in fig['parts']:
            base, pok = part(q['plot'])
            ok &= pok
            built.append(dict(base, x=q['x'], y=q['y'], dx=q['dx'], dy=q['dy'], mir=q['flip'] & 1,
                              dmir=q['flip'] & 1, vmir=(q['flip'] >> 1) & 1, group=fig['level']))
        if ok and any(px[4] for b in built for px in b['pixels']):
            # what makes the figure itself: its plots (graphic, size, place, flip) in drawing order
            shape = [dict(graphic='%04X' % plots[q['plot']]['address'], w=plots[q['plot']]['w'],
                          h=plots[q['plot']]['h'], dx=q['dx'], dy=q['dy'], flip=q['flip']) for q in fig['parts']]
            sig = hashlib.sha1(json.dumps([fig['level'], shape]).encode()).hexdigest()[:12]
            out[fig['level']].append(dict(count=fig['count'], group=fig['level'], parts=built,
                                          sig=sig, shape=shape))
    return out


def byte_index(data):
    """{key: (level, cell attribute address, line, check byte)} for every graphics byte drawn."""
    idx = {}
    for c in data['cells'].values():
        for line, byte in enumerate(c['bits']):
            idx['%02X:%04X' % (c['level'], (c['address'] + 1 + line) & 0xFFFF)] = (
                c['level'], c['address'], line, byte)
    return idx


def art_md5(banks):
    """MD5 of the banks the levels are unpacked from ({bank: bytes})."""
    return hashlib.md5(b''.join(bytes(banks[b]) for b in ART_BANKS)).hexdigest()


class Peek:
    """The identity's view of a game: its unchanging banks (128K; recolour.nex_peek is 48K only)."""
    def __init__(self, banks):
        self.art = art_md5(banks)

    def __call__(self, a):
        raise NotImplementedError('R-Type identity uses whole banks')


def colour_identity(peek):
    """What a key means for this build (docs/COLOURS.md Identity): level byte + graphics byte, bit
    = pixel; inputs = the banks the levels are unpacked from (3, 4, 6, 7: identical in every
    snapshot of the recording); geometry = the figure corpus the sheets were drawn from."""
    geo = hashlib.md5((HERE / 'continuation' / 'assets.json.gz').read_bytes()).hexdigest()
    return {'schema': 1, 'game': RECORD, 'engine': 'r_type_l2sprites',
            'keys': 'r_type-1: LL:AAAA level byte : unpacked graphics byte, bit = pixel',
            'inputs': peek.art, 'geometry': geo}


def sheets(out_dir=None, colours=None, say=print):
    """Per level: r_type_<LEVEL>_PAINTING_SPRITES.png (fewest whole figures showing every graphics
    byte) and _REFERENCE_ALL_SPRITES.png (every figure), each with its _layout.json."""
    from nexclash import coloursheet as cs, z80tonex as Z
    out_dir = Path(out_dir or REF / 'colours')
    out_dir.mkdir(exist_ok=True)
    data = corpus()
    ident = colour_identity(Peek(Z.Z80Snapshot(str(REF / 'Rtype.z80')).banks))
    cmap = colours if colours is not None else cs.load(os.environ.get('NEXCLASH_COLOURS') or COLOURS)
    rgb = cs.palette_rgb(PALETTE)
    made = []
    for lv, comps in sorted(composites(data).items()):
        pre = str(out_dir / ('r_type_%s' % level_name(lv)))
        # the sheet must be wider than the widest figure (level 3's battleship sections)
        wide = max(max(x for x, _ in cs.owners(c, clear=True)) + 1 for c in comps)
        width = max(cs.WIDTH, wide + 4)
        n1 = cs.write(cs.choose(comps, {}), pre + '_PAINTING_SPRITES.png', pre + '_PAINTING_SPRITES_layout.json',
                      rgb, colours=cmap, width=width, paint_clear=True, identity=ident)
        n2 = cs.write(comps, pre + '_REFERENCE_ALL_SPRITES.png', pre + '_REFERENCE_ALL_SPRITES_layout.json',
                      rgb, colours=cmap, width=width, paint_clear=True, identity=ident)
        say('%-8s painting %3d figures, reference %3d' % (level_name(lv), n1, n2))
        made.append(pre)
    import r_type_figures as F
    F.update(out_dir, composites(data), cmap, rgb, say)
    return made


def tables(cmap, data=None):
    """Colour map -> ({bank: 16384 bytes} for COLOUR_BANKS, info). Unknown keys and wrong check
    bytes are ignored and counted; more painted cells than the directory holds is an error."""
    data = data or corpus()
    idx = byte_index(data)
    recs = {}
    info = collections.Counter()
    for key, e in cmap.items():
        if key not in idx:
            info['map entries for no drawn graphics byte'] += 1
            continue
        lv, cell, line, check = idx[key]
        if e[0] != check:
            info['map entries with a wrong check byte'] += 1
            continue
        r = recs.setdefault((lv, cell), bytearray(REC))
        nib = list(e[2]) + [0] * (8 - len(e[2]))
        if any(n > 15 for n in nib):
            raise ValueError('%s: colour index above 15 (4-bit sprites)' % key)
        for j in range(4):
            r[line * 4 + j] = (nib[2 * j] << 4) | nib[2 * j + 1]
        r[32 + line] = (e[3] if len(e) > 3 else 0) & 0xFF
    recs = {k: v for k, v in recs.items() if any(v)}
    if len(recs) > DIR_ENTRIES or len(recs) > PER_PAGE * (LAST_PAGE - REC_PAGE0 + 1):
        raise ValueError('%d painted cells; the colour pages hold %d' % (len(recs), DIR_ENTRIES))
    pages = {p: bytearray(8192) for p in range(DIR_PAGE, LAST_PAGE + 1)}
    order = sorted(recs)
    n = 0
    for lv in range(0x30, 0x40):
        mine = [k for k in order if k[0] == lv]
        d = (lv - 0x30) * 4
        pages[DIR_PAGE][d:d + 4] = bytes([len(mine) & 255, len(mine) >> 8, n & 255, n >> 8])
        for k in mine:
            pages[DIR_PAGE][64 + 2 * n:66 + 2 * n] = bytes([k[1] & 255, k[1] >> 8])
            page, off = REC_PAGE0 + n // PER_PAGE, (n % PER_PAGE) * REC
            pages[page][off:off + REC] = recs[k]
            n += 1
    info['painted cells'] = n
    banks = {b: bytes(pages[2 * b]) + bytes(pages[2 * b + 1]) for b in COLOUR_BANKS}
    return banks, dict(info)


def load_colours():
    from nexclash import coloursheet as cs, recolour as rc
    return cs.load(rc.build_colours_path(COLOURS))


def nex_peek(nex):
    from nexclash import recolour as rc
    return Peek(rc.banks(nex))


def recolour(nex, cmap):
    """A built prototype .nex + colour map -> (new .nex bytes, info). Refuses a .nex that is not
    this prototype's build of R-Type (hook sites, hook code bank, packed art, colour banks)."""
    from nexclash import recolour as rc
    import l2scroll as L
    off = rc.nex_offsets(nex)
    need = set(COLOUR_BANKS) | {0, 2, 5, 12}
    if not need <= set(off):
        raise ValueError('not an R-Type Layer 2 sprite build: banks %s missing' % sorted(need - set(off)))
    bank = lambda b: bytes(nex[off[b]:off[b] + 16384])
    ram = bank(5) + bank(2) + bank(0)
    peek = lambda a: ram[a - 0x4000] if a >= 0x4000 else 0
    data = corpus()
    if nex_peek(nex).art != _expected_art():
        raise ValueError('packed art differs from Rtype.z80 (another release?)')
    if not any(bank(12)[:len(c)] == c for c in (L.assembled(True), L.assembled(False))):
        raise ValueError("hook code differs from this prototype's (rebuild with l2scroll.py)")
    for addr, old, label, op in L.SITES + L.SPRITE_SITES:
        if peek(addr) != op:
            raise ValueError('hook site 0x%04X does not hold a hook jump' % addr)
    new, info = tables(cmap, data)
    out, changed = rc.splice(nex, new)
    info['banks changed'] = changed
    return out, info


def _expected_art():
    from nexclash import z80tonex as Z
    return art_md5(Z.Z80Snapshot(str(REF / 'Rtype.z80')).banks)


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('sheets')
    s.add_argument('-o', '--out')
    fp = sub.add_parser('figures', help='apply names / layers: {figures|families: {id: {name, layer}}}')
    fp.add_argument('patch')
    fp.add_argument('-o', '--out')
    r = sub.add_parser('recolour')
    r.add_argument('nex')
    r.add_argument('painted')
    r.add_argument('-o', '--output')
    r.add_argument('--layout')
    r.add_argument('--onto')
    r.add_argument('--replace', action='store_true')
    a = ap.parse_args(argv)
    if a.cmd == 'sheets':
        sheets(a.out)
    elif a.cmd == 'figures':
        import r_type_figures as F
        F.apply(a.out or REF / 'colours', json.loads(Path(a.patch).read_text()))
    else:
        from nexclash import recolour as rc
        rc.engines = lambda: {RECORD: sys.modules[__name__]}     # until R-Type has a record
        rc.run(a.nex, a.painted, layout=a.layout, output=a.output, onto=a.onto, replace=a.replace)


if __name__ == '__main__':
    sys.path[:0] = [str(HERE)]
    main(sys.argv[1:])
