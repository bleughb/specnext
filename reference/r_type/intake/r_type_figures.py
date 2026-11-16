"""R-Type figure IDs, families and identification sheets (owner request 2026-11-16).

Every figure on the colour sheets gets a stable ID, so the user can name it and, later, choose its
place in the display stack (layer). Written by `r_type_colour.py sheets` next to the colour sheets:

  r_type_figures.json            the registry: every figure and family, all levels (read back on the
                                 next run, so IDs, names and layers survive a longer recording)
  r_type_<LEVEL>_IDENTIFY.png    every figure of the level, 2x, in today's colours, its ID beside it;
                                 for looking only (never read back), so text is allowed

IDs. A figure = one game object as drawn (its plots: graphic, size, place, flip; the colour sheets'
composites). Its signature is a hash of those plots and the level. Its ID is L<level>-<n> (L0 = the
TEXT level): n is handed out once, in drawing order of first appearance, and kept forever for that
signature; a new recording adds numbers after the highest one and never renumbers.
A family = the figures of one level that share any graphic (an object's animation frames, a ship
and its turret drawn from the same art): L<level>-F<n>, kept by matching graphics with the previous
run. A family is the unit a user names and layers; a figure may override both.

Registry format (schema 1), designed for an interactive page to read and write:
  game, schema, note, scale (identification sheet magnification), palette (16 RGB),
  layers: the layer choices (ids and labels; "original" = as the game draws, the default),
  levels: {LEVEL: {level byte, identify sheet file, width, height, figures [ids in sheet order]}},
  families: {Fid: {level, name, layer, figures [ids], graphics [hex addresses]}},
  figures: {id: {sig, level, family, name, layer, count (draws in the recording), size [w, h],
                 parts [{graphic, w, h, dx, dy, flip}], box [x, y, w, h] on the identify sheet,
                 keys (colour-map keys it shows), painted (keys with a colour)}}
  outline: false / true ("black", palette 8) / a palette index 1-15: a 1-pixel border around the
  figure's outer edge (pixels directly above, below, left or right, no diagonals; holes and dither
  gaps left alone), drawn outside the graphic: its sprites are pre-rendered one pixel bigger. Figures sharing a graphic share its border, so it is normally set per family.
  name / layer / outline on a figure: null = the family's. Unknown fields are kept on rewrite.
Only `name` and `layer` are user data; everything else is regenerated. A page edits the JSON
(or exports a patch {figures|families: {id: {name, layer}}}) and `r_type_colour.py` reads it back.
"""
import json
from pathlib import Path

SCHEMA = 1
SCALE = 2
WIDTH = 640                      # identification sheet width in sheet pixels (before scaling)
LABEL_H = 9
LAYERS = [{'id': 'original', 'label': 'As the game draws it'},
          {'id': 1, 'label': '1 back'}, {'id': 2, 'label': '2'}, {'id': 3, 'label': '3 middle'},
          {'id': 4, 'label': '4'}, {'id': 5, 'label': '5 front'}]
BG = (40, 40, 48)
TEXT = (255, 255, 160)
FRAME = (110, 110, 120)


def level_tag(lv):
    return 'L%d' % (lv - 0x30)


def _load(path):
    if path.exists():
        return json.loads(path.read_text())
    return {}


def _families(comps):
    """Union of figures sharing any graphic -> [set of figure indexes]."""
    parent = list(range(len(comps)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    owner = {}
    for i, c in enumerate(comps):
        for p in c['shape']:
            g = p['graphic']
            if g in owner:
                parent[find(i)] = find(owner[g])
            else:
                owner[g] = i
    groups = {}
    for i in range(len(comps)):
        groups.setdefault(find(i), []).append(i)
    return sorted(groups.values(), key=lambda g: min(g))


def _render(comp, cmap, rgb):
    """{(x, y): rgb} of a composite as the sprite build draws it (painted colours applied)."""
    from nexclash import coloursheet as cs
    out = {}
    for (x, y), (pi, xi) in cs.owners(comp).items():
        c, r, key, bit, code, dflt = comp['parts'][pi]['pixels'][xi]
        st = cs.state(cmap, key, bit)
        if st == 'T':
            continue
        n = st[1] if st != 'D' else dflt
        if code == 0 and st == 'D':
            continue
        out[(x, y)] = rgb[n]
    return out


def _font():
    from PIL import ImageFont
    try:
        return ImageFont.load_default()
    except Exception:            # noqa: BLE001
        return None


def update(out_dir, comps_by_level, cmap, rgb, say=print):
    """Assign / keep IDs, write the registry and one identification sheet per level."""
    from PIL import Image, ImageDraw
    from nexclash import coloursheet as cs
    out_dir = Path(out_dir)
    reg_path = out_dir / 'r_type_figures.json'
    old = _load(reg_path)
    old_figs = old.get('figures', {})
    old_fams = old.get('families', {})
    by_sig = {f['sig']: fid for fid, f in old_figs.items()}
    reg = dict(old)
    reg.update(schema=SCHEMA, game='r_type', note=__doc__.split('\n\n')[0], scale=SCALE,
               palette=[list(c) for c in rgb], layers=LAYERS)
    figs, fams, levels = {}, {}, {}
    font = _font()
    for lv, comps in sorted(comps_by_level.items()):
        tag = level_tag(lv)
        from r_type_colour import level_name
        lname = level_name(lv)
        # figure IDs: keep known signatures, number new ones after the highest so far
        used = [int(fid.split('-')[1]) for fid in old_figs if fid.startswith(tag + '-')]
        nxt = max(used, default=0) + 1
        ids = []
        for c in comps:
            fid = by_sig.get(c['sig'])
            if fid is None:
                fid = '%s-%03d' % (tag, nxt)
                nxt += 1
            ids.append(fid)
        # families: keep an old family ID when the new family shares graphics with it
        fam_used = [int(k.split('-F')[1]) for k in old_fams if k.startswith(tag + '-F')]
        fnext = max(fam_used, default=0) + 1
        taken = set()
        for group in _families(comps):
            graphics = sorted({p['graphic'] for i in group for p in comps[i]['shape']})
            best, bestn = None, 0
            for k, f in old_fams.items():
                if k.startswith(tag + '-F') and k not in taken:
                    n = len(set(f.get('graphics', [])) & set(graphics))
                    if n > bestn:
                        best, bestn = k, n
            if best is None:
                best = '%s-F%02d' % (tag, fnext)
                fnext += 1
            taken.add(best)
            prev = old_fams.get(best, {})
            fam = dict(prev)
            fam.update(level=lname, name=prev.get('name', ''), layer=prev.get('layer', 'original'),
                       outline=prev.get('outline', False),
                       figures=sorted(ids[i] for i in group), graphics=graphics)
            fams[best] = fam
            for i in group:
                comps[i]['family'] = best
        # identification sheet: figures in ID order, label above each box
        order = sorted(range(len(comps)), key=lambda i: int(ids[i].split('-')[1]))
        place, x, y, rowh = {}, 2, 2, 0
        drawn = {}
        from r_type_colour import outline_colour, ring
        for i in order:
            pix = _render(comps[i], cmap, rgb)
            prev = old_figs.get(ids[i], {})
            ov = prev.get('outline')
            if ov is None:
                ov = fams.get(comps[i]['family'], old_fams.get(comps[i]['family'], {})).get('outline')
            col = outline_colour(ov)
            if col is not None:                 # the border the build draws, 1 pixel outside
                inv = {v: k for k, v in enumerate(rgb)}
                idx = {(x + 1, y + 1): inv.get(c, 8) for (x, y), c in pix.items()}
                xs = [q[0] for q in idx] or [0]
                ys = [q[1] for q in idx] or [0]
                idx = ring(idx, max(xs) + 2, max(ys) + 2, col)
                pix = {(x - 1, y - 1): rgb[n] for (x, y), n in idx.items() if n}
            allpx = cs.owners(comps[i], clear=True)
            xs = [p[0] for p in allpx] or [0]
            ys = [p[1] for p in allpx] or [0]
            w, h = max(xs) + 1, max(ys) + 1
            boxw = max(w, 6 * len(ids[i]) // SCALE + 2)
            if x + boxw + 2 > WIDTH:
                x, y, rowh = 2, y + rowh + 4, 0
            place[i] = (x, y + LABEL_H, w, h)
            drawn[i] = pix
            x += boxw + 6
            rowh = max(rowh, h + LABEL_H)
        height = y + rowh + 4
        img = Image.new('RGB', (WIDTH * SCALE, height * SCALE), BG)
        dr = ImageDraw.Draw(img)
        for i in order:
            bx, by, w, h = place[i]
            dr.rectangle([bx * SCALE - 1, by * SCALE - 1, (bx + w) * SCALE, (by + h) * SCALE], outline=FRAME)
            for (px, py), col in drawn[i].items():
                dr.rectangle([(bx + px) * SCALE, (by + py) * SCALE, (bx + px + 1) * SCALE - 1,
                              (by + py + 1) * SCALE - 1], fill=col)
            dr.text((bx * SCALE, (by - LABEL_H) * SCALE), ids[i], fill=TEXT, font=font)
        sheet = 'r_type_%s_IDENTIFY.png' % lname
        img.save(out_dir / sheet)
        levels[lname] = dict(level=lv, tag=tag, identify=sheet, width=WIDTH * SCALE, height=height * SCALE,
                             figures=[ids[i] for i in order])
        for i in order:
            c = comps[i]
            prev = old_figs.get(ids[i], {})
            keys = {q[2] for p in c['parts'] for q in p['pixels'] if q[4]}
            f = dict(prev)
            f.update(sig=c['sig'], level=lname, family=c['family'], name=prev.get('name'),
                     layer=prev.get('layer'), outline=prev.get('outline'), count=c['count'],
                     size=[place[i][2], place[i][3]], parts=c['shape'],
                     box=[place[i][0] * SCALE, place[i][1] * SCALE, place[i][2] * SCALE, place[i][3] * SCALE],
                     keys=len(keys), painted=sum(1 for k in keys if k in cmap))
            figs[ids[i]] = f
        say('%-8s %3d figures, %3d families -> %s' % (lname, len(comps), len({c['family'] for c in comps}), sheet))
    # figures no longer seen keep their entry (a shorter recording must not lose names)
    for fid, f in old_figs.items():
        if fid not in figs:
            figs[fid] = dict(f, unseen=True)
    for k, f in old_fams.items():
        if k not in fams:
            fams[k] = dict(f, unseen=True)
    reg.update(levels=levels, families=dict(sorted(fams.items())), figures=dict(sorted(figs.items())))
    reg_path.write_text(json.dumps(reg, indent=1) + '\n')
    return reg


def apply(out_dir, patch, say=print):
    """Read back user data: patch = {figures|families: {id: {name, layer}}} (a page export or a
    hand-edited file). Only name and layer change; unknown IDs or layers are refused."""
    out_dir = Path(out_dir)
    reg_path = out_dir / 'r_type_figures.json'
    reg = _load(reg_path)
    ok_layers = {l['id'] for l in LAYERS}
    bad, n = [], 0
    for kind in ('figures', 'families'):
        for fid, change in patch.get(kind, {}).items():
            if fid not in reg.get(kind, {}):
                bad.append('%s %s: not in the registry' % (kind, fid))
                continue
            for field in ('name', 'layer', 'outline'):
                if field not in change:
                    continue
                v = change[field]
                if field == 'layer' and v not in ok_layers and not (kind == 'figures' and v is None):
                    bad.append('%s %s: layer %r (choices %s)' % (kind, fid, v, sorted(map(str, ok_layers))))
                    continue
                if field == 'outline':
                    from r_type_colour import outline_colour
                    try:
                        outline_colour(v)
                    except ValueError as e:
                        bad.append('%s %s: %s' % (kind, fid, e))
                        continue
                if field == 'name' and v is not None and not isinstance(v, str):
                    bad.append('%s %s: name must be text' % (kind, fid))
                    continue
                reg[kind][fid][field] = v
                n += 1
    if bad:
        raise ValueError('nothing applied:\n  ' + '\n  '.join(bad))
    reg_path.write_text(json.dumps(reg, indent=1) + '\n')
    say('%d name / layer change(s) applied to %s' % (n, reg_path.name))
    return reg
