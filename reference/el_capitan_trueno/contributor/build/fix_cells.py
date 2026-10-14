# Fix cells (host, 2026-10-13): scenery cells redrawn in Layer 2 WITHOUT priority (under the sprites),
# where the original cut the scenery along cell edges to avoid clash (e.g. the wall stops a cell short
# of the outermost barrels). One method for every such place: a place = screens + the scenery frames
# that hide the wall; the screen is built in the simulator with and without those frames, so the wall
# behind is the game's own. Draft per cell: the frame's ink stays, its paper inside its solid silhouette
# (each plot built alone, per line from its leftmost to its rightmost pixel) stays, its paper outside
# shows the wall only to the RIGHT of the frames, GAP pixels away (host, 2026-10-13: stay close to the
# original; left of and between the barrels nothing changes). Only cells the draft changes are fix cells. The host redraws them on gfx/fix_tiles.png.
# Sheet: per screen, [fix cells as Layer 2 shows them, the rest of the box pink] [the screen now
# (reference)]; only the fix cells are read back, a pink pixel = see-through (the ULA shows).
# bush_walls.py merges the fix cells into the per-screen Layer 2 table (bushwall.bin).
# Usage: python fix_cells.py --sheet   (gfx/fix_tiles.png + .json: adds new screens, keeps the drawn ones)
#        python fix_cells.py --png out.png [--screens 15,17]   (preview: now | draft)
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bush_walls as bw

SHEET = os.path.join(HERE, '..', 'gfx', 'fix_tiles.png')
# (screens, frames hidden for the wall build, shapes = the objects, rule)
#   'edges':  the wall comes to the group's right side and to each row's leftmost top-left shoulder
#   'around': the wall everywhere outside the shapes (an object plotted over the wall with OR: the wall
#             pixels in its cells took its colour)
#   'copy':   the cells given (a set of (row, column)) or changed by the frames, copied as they are, for
#             the host to redraw; the sheet holds each distinct cell once, the build gives the drawing
#             to every cell of the place that looks the same (fixes())
PLACES = [((45, 46, 47), {0xCB, 0xCC}, {0xCB}, 'edges'),        # barrels 0xCB; 0xCC = the wall's cut
                                                                # edge beside them (not a barrel)
          ((17,), {(5, 19), (6, 19), (5, 23), (6, 23)}, None, 'copy'),     # the bell's rim, outer cells
                                                                # (host redraws them; screen 15: none)
          ((39, 40, 41, 50, 51, 52), {0x52, 0x53}, 'skeleton', 'copy'),  # hanging skeleton (arms, body)
          ((18,), {0x32, 0x33, 0x34}, None, 'copy'),     # the well's arch (dark yellow, attribute 0x06)
          ((18, 19, 20, 21, 22, 23, 24, 58, 59), {0xAA, 0xAB, 0xAC, 0xAD}, 'roof', 'copy'),  # cypresses
                                                        # at the roof's level (the red roof behind)
          ((15, 17), {0x2E}, None, 'copy')]         # the bells' top ring (host)


def pick_skeleton(comp, ram, s, norm):
    """Host (2026-10-13): of the top 2 rows (arms) the leftmost and the rightmost column, of the 3 rows
    below (body, legs) every cell."""
    r0 = min(r for r, c in comp)
    top = [c for r, c in comp if r < r0 + 2]
    body = [c for r, c in comp if r >= r0 + 2]
    return ({(r, c) for r in (r0, r0 + 1) for c in (min(top), max(top))} |
            {(r, c) for r in range(r0 + 2, r0 + 5) for c in range(min(body), max(body) + 1)})


def pick_roof(comp, ram, s, norm):
    """Host (2026-10-13): the cypress cells at the roof's level: the screen without the trees shows the
    red roof there (ink red)."""
    m = bw.build(ram, s, {0xAA, 0xAB, 0xAC, 0xAD})
    return {(r, c) for r, c in comp if m[0xF13C + r * 30 + c] & 7 == 2}


PICK = {'skeleton': pick_skeleton, 'roof': pick_roof}


def components(cells):
    out, cells = [], set(cells)
    while cells:
        comp, todo = set(), [min(cells)]
        while todo:
            p = todo.pop()
            if p in cells and p not in comp:
                comp.add(p)
                todo += [(p[0] + a, p[1] + b) for a in (-1, 0, 1) for b in (-1, 0, 1)]
        cells -= comp
        out.append(comp)
    return out
GAP, GAP_R = 1, 1                           # black pixels kept left / right of the frames (host)


def colours(mem, r, c):
    a = mem[0xF13C + r * 30 + c]
    return (a & 7) + (a >> 3 & 8), (a >> 3 & 7) + (a >> 3 & 8)


def pixel(mem, x, y):
    return mem[0xF2E0 + y * 30 + x // 8] & (0x80 >> x % 8)


def build_only(ram, screen, frames, keep, shapes=None):
    """The screen without the frames but the keep-th plot of the shapes (a subset of the frames; 0x62BE
    calls in order); -1 = none of them. Returns (memory, number of shape plots)."""
    from skoolkit.simulator import Simulator
    from skoolkit.simutils import PC, SP
    mem = bytearray(ram)
    mem[0xE60B] = screen
    sim = Simulator(mem)
    r = sim.registers
    r[SP] = 0xEEE0 - 2
    mem[r[SP]:r[SP] + 2] = bytes(2)
    r[PC] = 0x65C3
    n = 0
    while r[PC]:
        if r[PC] == 0x62BE and r[0] in frames:
            k = -1
            if r[0] in (shapes or frames):
                n += 1
                k = n - 1
            if k != keep or k < 0:
                sp = r[SP]
                r[PC] = mem[sp] | mem[sp + 1] << 8
                r[SP] = sp + 2
                continue
        sim.run()
    return mem, n


def solid(mem, wall, ored=False):
    """One frame: (its solid silhouette: per line, its leftmost to its rightmost ink pixel, ink in the
    cells it changed = those it redrew whole, or with ored: only the pixels it added; those cells)."""
    mine = {(r, c) for r in range(14) for c in range(30) if bw.cell(mem, r, c) != bw.cell(wall, r, c)}
    out = set()
    for y in range(112):
        xs = [x for x in range(240) if (y // 8, x // 8) in mine and pixel(mem, x, y)
              and not (ored and pixel(wall, x, y))]
        if xs:
            out.update((x, y) for x in range(min(xs), max(xs) + 1))
    return out, mine


def groups(frames):
    """Frames (silhouette, cells) joined into groups (a pyramid, a lonely barrel): silhouettes closer
    than 5 pixels belong together."""
    near = lambda p, q: any((x + dx, y + dy) in q for x, y in p for dx in (-4, 0, 4) for dy in (-4, 0, 4))
    out = []
    for f in frames:
        joined = [g for g in out if any(near(f[0], h[0]) for h in g)]
        for g in joined:
            out.remove(g)
        out.append(sum(joined, []) + [f])
    return out


def edges(sil):
    """One group's wall edges per line: right = right of every frame (and above the tops: the wall wraps
    the rounded tops); left = only the top-left shoulder of each row's leftmost frame, from above its top
    down to its widest line (host, 2026-10-13: nothing between the frames, the rest as the original)."""
    inside = set().union(*sil)
    right, left = {}, {}
    for y in range(112):
        xs = [x for x, yy in inside if yy == y]
        if xs:
            right[y] = max(xs)
    for y in range(min(right) - 1, -1, -1):
        right[y] = right[y + 1]
    rows = {}
    for p in sil:
        rows.setdefault(max(y for x, y in p) // 4, []).append(p)
    for row in rows.values():
        row.sort(key=lambda p: min(x for x, y in p))
        f = row[0]
        top, bot = min(y for x, y in f), max(y for x, y in f)
        for y in range(top, (top + bot) // 2 + 1):
            xs = [x for x, yy in f if yy == y]
            if xs:
                left[y] = min(xs)
        others = inside - f
        y = top - 1
        while y >= 0 and y not in left and not any(yy == y for x, yy in others):
            left[y] = left[top]
            y -= 1
    return right, left


def draft(ram, s, frames, shapes, rule='edges'):
    """(shapes: for 'copy', the name of a cell picker per object, PICK)"""
    """{cell: 64 colours (0-15)} for the cells where the frames hide wall pixels outside their outlines."""
    norm = bw.build(ram, s)
    if rule == 'copy':
        out = {}
        if not isinstance(next(iter(frames)), tuple):
            m = bw.build(ram, s, frames)
            frames = {(r, c) for r in range(14) for c in range(30) if bw.cell(norm, r, c) != bw.cell(m, r, c)}
            if shapes:
                objs = []                   # (look, row, column, cells): one per object
                for comp in components(frames):
                    cells = PICK[shapes](comp, ram, s, norm)
                    if not cells:
                        continue
                    r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
                    look = tuple(sorted((r - r0, c - c0, bw.cell(norm, r, c)) for r, c in cells))
                    objs.append((look, r0, c0, cells))
                frames = set().union(*(o[3] for o in objs))
        for r, c in sorted(frames):
            ink, paper = colours(norm, r, c)
            out[(r, c)] = [ink if pixel(norm, c * 8 + i % 8, r * 8 + i // 8) else paper for i in range(64)]
        return norm, out, locals().get('objs')
    wall, n = build_only(ram, s, frames, -1, shapes)
    fr = [solid(build_only(ram, s, frames, k, shapes)[0], wall, rule == 'around') for k in range(n)]
    cells = {(r, c) for r in range(14) for c in range(30) if bw.cell(norm, r, c) != bw.cell(wall, r, c)}
    if rule == 'around':
        inside = set().union(*(p for p, m in fr))
        out = {}
        for r, c in sorted(cells):
            ink, paper = colours(norm, r, c)
            wink, wpaper = colours(wall, r, c)
            px = []
            for i in range(64):
                x, y = c * 8 + i % 8, r * 8 + i // 8
                if (x, y) in inside:
                    px.append(ink if pixel(norm, x, y) else paper)
                else:
                    px.append(wink if pixel(wall, x, y) else wpaper)
            if px != [ink if pixel(norm, c * 8 + i % 8, r * 8 + i // 8) else paper for i in range(64)]:
                out[(r, c)] = px
        return norm, out, None
    gs = groups(fr)
    owner = {}                              # each changed cell: the group with the nearest frame cell
    for rc in sorted(cells):
        dist = lambda g: min(abs(rc[0] - r) + abs(rc[1] - c) for p, m in g for r, c in m)
        owner.setdefault(min(range(len(gs)), key=lambda i: dist(gs[i])), []).append(rc)
    inside = set().union(*(p for p, m in fr))
    grow = lambda g: {(x + dx, y + dy) for x, y in inside for dx in range(-g, g + 1) for dy in range(-g, g + 1)}
    near_l, near_r = grow(GAP), grow(GAP_R)
    out = {}
    for i, g in enumerate(gs):
        right, left = edges([p for p, m in g])
        for r, c in owner.get(i, []):
            ink, paper = colours(norm, r, c)
            wink, wpaper = colours(wall, r, c)
            px = []
            for i in range(64):
                x, y = c * 8 + i % 8, r * 8 + i // 8
                if pixel(norm, x, y):
                    px.append(ink)
                elif ((x, y) not in near_r and y in right and x > right[y] or
                      (x, y) not in near_l and y in left and x < left[y]):
                    px.append(wink if pixel(wall, x, y) else wpaper)
                else:
                    px.append(paper)
            if px != [ink if pixel(norm, c * 8 + i % 8, r * 8 + i // 8) else paper for i in range(64)]:
                out[(r, c)] = px
    return norm, out, None


def drafts(ram):
    """[(screen, normal build, {cell: 64 colours}, objects or None)] for every place."""
    out = []
    for p, (screens, frames, shapes, rule) in enumerate(PLACES):
        for s in screens:
            out.append((s, *draft(ram, s, frames, shapes, rule), p))
    return out


def fixes(ram):
    """{screen: {cell: 64 colours or None}} for the build: the cells on the host's sheet; an object of a
    place with objects (skeletons) that is not on the sheet gets the drawing of the object that looks the
    same (every cell: same pixels and attribute), cell by cell."""
    drawn = read_sheet()
    items = drafts(ram)
    look = {}
    for s, norm, cells, objs, p in items:
        for k, r0, c0, oc in objs or ():
            if all(rc in drawn.get(s, {}) for rc in oc):
                look.setdefault(k, {(r - r0, c - c0): drawn[s][(r, c)] for r, c in oc})
    out = {}
    for s, norm, cells, objs, p in items:
        for rc in cells:
            if rc in drawn.get(s, {}):
                out.setdefault(s, {})[rc] = drawn[s][rc]
        for k, r0, c0, oc in objs or ():
            if k in look and not all(rc in drawn.get(s, {}) for rc in oc):
                for (dr, dc), px in look[k].items():
                    out.setdefault(s, {})[(r0 + dr, c0 + dc)] = px
    for s, norm, cells, objs, p in items:   # a cell drawn as the original shows is no fix: left out
        for (r, c) in list(out.get(s, {})):
            ink, paper = colours(norm, r, c)
            if out[s][(r, c)] == [ink if pixel(norm, c * 8 + i % 8, r * 8 + i // 8) else paper for i in range(64)]:
                del out[s][(r, c)]
    return {s: cells for s, cells in out.items() if cells}


def read_sheet():
    """{screen: {cell: 64 colours (0-15) or None = see-through}} from the host's sheet, if there is one."""
    import json
    if not os.path.exists(SHEET):
        return {}
    from PIL import Image
    im = Image.open(SHEET).convert('RGB')
    lay = json.load(open(os.path.splitext(SHEET)[0] + '.json'))
    pink = tuple(lay['pink'])
    near = lambda rgb: min(range(16), key=lambda i: sum((a - b) ** 2 for a, b in zip(rgb, bw.PAL[i])))
    out = {}
    for e in lay['screens']:
        cells = out.setdefault(e['screen'], {})
        for r, c in e['cells']:
            x0, y0 = e['x'] + (c - e['col']) * 8, e['y'] + (r - e['row']) * 8
            cells[(r, c)] = [None if p == pink else near(p)
                             for p in (im.getpixel((x0 + i % 8, y0 + i // 8)) for i in range(64))]
    return out


def put(im, x0, y0, px):
    for i, v in enumerate(px):
        im.putpixel((x0 + i % 8, y0 + i // 8), bw.PINK if v is None else bw.PAL[v])


def sheet(items, out):
    """New screens are added below; the strips already on the sheet (the host's drawing) stay as they are."""
    import json
    from PIL import Image, ImageDraw
    old, lay0 = None, []
    if os.path.exists(out):
        old = Image.open(out).convert('RGB')
        lay0 = json.load(open(os.path.splitext(out)[0] + '.json'))['screens']
    first = lambda s: min(p for p, pl in enumerate(PLACES) if s in pl[0])   # entries before 'place'
    done = {(e.get('place', first(e['screen'])), e['screen']) for e in lay0}
    seen = {k for it in items if (it[4], it[0]) in done for k, r0, c0, oc in it[3] or ()}
    items = [it for it in items if (it[4], it[0]) not in done]
    new = []                                # objects: each look once, whole (the first screen showing it)
    for s, norm, cells, objs, p in items:
        keep = dict(cells)
        if objs:
            keep = {}
            for k, r0, c0, oc in objs:
                if k not in seen:
                    seen.add(k)
                    keep.update((rc, cells[rc]) for rc in oc)
        if keep:
            new.append((s, norm, keep, p))
    items = new
    if old is not None:
        if not items:
            print(out, 'has every screen: unchanged')
            return
    boxes = []
    for s, norm, cells, p in items:
        r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
        r0, c0 = max(r0 - 1, 0), max(c0 - 1, 0)     # one cell of context around
        r1 = min(max(r for r, c in cells) + 2, 14)
        c1 = min(max(c for r, c in cells) + 2, 30)
        boxes.append((r0, c0, r1 - r0, c1 - c0))
    lx, gap = 56, 8
    y = old.height if old else 0
    w = max([lx + 2 * b[3] * 8 + gap for b in boxes] + [old.width if old else 0])
    h = y + sum(b[2] * 8 + 14 for b in boxes)
    im = Image.new('RGB', (w, h), (200, 200, 200))
    if old:
        im.paste(old, (0, 0))
    d = ImageDraw.Draw(im)
    lay = list(lay0)
    for (s, norm, cells, p), (r0, c0, nr, nc) in zip(items, boxes):
        d.rectangle((lx, y, lx + nc * 8 - 1, y + nr * 8 - 1), fill=bw.PINK)
        for (r, c), px in cells.items():
            put(im, lx + (c - c0) * 8, y + (r - r0) * 8, px)
        bw.window(norm, im, lx + nc * 8 + gap, y, None, (r0, c0, nr, nc))
        d.text((0, y), 'Screen %d' % s, fill=(0, 0, 0))
        d.text((lx, y + nr * 8), 'fix cells', fill=(0, 0, 0))
        d.text((lx + nc * 8 + gap, y + nr * 8), 'now (reference)', fill=(0, 0, 0))
        lay.append(dict(screen=s, place=p, x=lx, y=y, row=r0, col=c0, rows=nr, cols=nc,
                        cells=[[r, c] for r, c in sorted(cells)]))
        y += nr * 8 + 14
    im.save(out)
    json.dump(dict(pink=bw.PINK, screens=lay), open(os.path.splitext(out)[0] + '.json', 'w'), indent=0)
    print(out, im.size)


def preview(items, out):
    from PIL import Image
    if '--screens' in sys.argv:
        only = set(map(int, sys.argv[sys.argv.index('--screens') + 1].split(',')))
        items = [it for it in items if it[0] in only]
    im = Image.new('RGB', (488, 120 * len(items)), (200, 200, 200))
    for i, (s, norm, cells, objs, p) in enumerate(items):
        bw.window(norm, im, 0, i * 120)
        bw.window(norm, im, 248, i * 120)
        for (r, c), px in cells.items():
            put(im, 248 + c * 8, i * 120 + r * 8, px)
    im.save(out)


def main():
    items = drafts(bw.game_ram())
    for s, norm, cells, objs, p in items:
        print('screen %d: %d fix cells' % (s, len(cells)))
    if '--sheet' in sys.argv:
        sheet(items, SHEET)
    if '--png' in sys.argv:
        preview(items, sys.argv[sys.argv.index('--png') + 1])


if __name__ == '__main__':
    main()
