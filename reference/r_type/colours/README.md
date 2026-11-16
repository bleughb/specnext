# R-Type colour sheets

One pair of sheets per level, drawn in the game's own colours (the colours the sprite build shows
today). Paint the `_PAINTING_SPRITES.png` of a level; the `_REFERENCE_ALL_SPRITES.png` shows every
figure and is not read back.

## Painting

- Keep the size: one PNG pixel is one Spectrum pixel.
- Use the 15 swatches in the top row (the Spectrum colours; swatch 9 is opaque black).
- Grey inside a figure's box is transparent. A grey pixel can be painted (outlines), and a
  coloured pixel can be painted grey to make it see-through.
- A graphic shared by several figures appears once; painting it colours every figure that uses it.
- Flash frames (a hit enemy drawn in one forced colour) keep the forced colour.
- LEVEL1 also holds the title-screen "R-TYPE" letters: the title is drawn by the original screen,
  so painting them has no effect.

## Import

Until R-Type has an evidence record, from `specnext/reference/r_type/intake`:

```
py -3 r_type_colour.py recolour BUILD.nex r_type_LEVEL3_PAINTING_SPRITES_painted.png
```

The layout `r_type_LEVEL3_PAINTING_SPRITES_layout.json` must be next to the painted PNG. The output
is the usual recolour bundle: `BUILD_painted.nex`, its `_colours.json`, the sheets redrawn with the
new colours, and a report. Paint the next level on the redrawn sheet or the original: paintings
merge, and a pixel painted two ways is refused. Copy the `_colours.json` to
`nexclash/docs/profiles/r_type_colours.json` to make the painting the default for new builds.

Regenerate the sheets (after a new recording, or to show the default map's colours):
`py -3 r_type_colour.py sheets`.

## Figure IDs and identification sheets

Every figure has a stable ID, `L<level>-<number>` (L0 = TEXT), and belongs to a family,
`L<level>-F<number>`: the figures of a level that share graphics, such as one enemy's frames.

- `r_type_<LEVEL>_IDENTIFY.png`: every figure of the level at 2x, in today's colours, with its ID
  above it. For looking up a figure; never read back.
- `r_type_figures.json`: the registry of all figures and families: level, family, how often the
  recording drew it, its parts (graphic address, size, place, flip), its box on the identify
  sheet, colour keys, and the user's `name` and `layer` (layer choices in `layers`; "original" =
  as the game draws). A figure's `null` name or layer means "use the family's".

IDs never change for a figure the recording drew before: regenerating the sheets keeps them, a
longer recording adds new numbers after the highest, and figures it no longer sees stay listed
with `"unseen": true`, so names are never lost.

Name or layer figures by editing `r_type_figures.json`, or with a patch file:

```
{"families": {"L3-F07": {"name": "Battleship turret", "layer": 5}},
 "figures":  {"L1-036": {"name": "Charge beam"}}}
```

```
py -3 r_type_colour.py figures PATCH.json
```

Unknown IDs or layers are refused and nothing changes. Layers are recorded only for now: the build
does not use them yet.

## Outlines (borders)

A family or figure can have a 1-pixel border around its outer edge: pixels directly above, below,
left or right of the figure, no diagonals. Holes and the gaps of a dotted pattern are left alone.
The border is drawn outside the graphic, so the figure is shown one pixel bigger on every side;
the build pre-renders those sprites (colour pages 88-95). Set `outline` in the registry:
`true` (black) or a palette index 1-15; `false` = none (the default).

```
{"families": {"L1-F08": {"outline": true}}}
```

`example_outline_ship.json` outlines the player ship (its three frames) on every level. Apply
it, then either rebuild or restyle an existing build without rebuilding:

```
py -3 r_type_colour.py figures ../colours/example_outline_ship.json
py -3 r_type_colour.py restyle BUILD.nex          -> BUILD_styled.nex
```

The identification sheets show the borders. During a hit flash an outlined figure is drawn without
its border, in the flash colour.
