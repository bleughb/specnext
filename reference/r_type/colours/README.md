# R-Type colour sheets

Sprite sheets come in pairs, in the game's own colours (what the sprite build shows today), with the
same figures in the same arrangement:

- `r_type_<SHEET>_IDENTIFY.png`: every figure at 2x with its ID above it. For finding a figure;
  never read back.
- `r_type_<SHEET>_PAINTING_SPRITES.png`: the same figures at 1:1 and in the same places (positions
  are the identification sheet's halved), with no text. This is the sheet you paint.

Each game sprite is listed once (2026-11-20):

- `COMMON`: figures drawn the same in more than one level (the ship, Force, shots, explosions,
  power-ups, the logo and so on), once each. Painting one colours it in every level.
- `LEVEL1` .. `LEVEL9`: only that level's own figures. A shared graphic inside one of them is
  shown faded (paint it on COMMON).
- "The same" means the same artwork in the same colours. A figure a level draws in other colours
  stays on that level's sheet, so it can be painted differently there.
- A figure that adds nothing not already shown (a repeat, or a frame built only from shown
  graphics) is left out. The registry still lists it, with `sheet: null`.

Your arrangement is in `r_type_sheets.json`: `add` moves figures from a level sheet onto COMMON
(the Force pods), and `order` places a run of figures after the `after` figure (the ship's shots,
balls, Force pods and collectables follow L1-041). Edit it and run `py -3 r_type_colour.py sheets`.

Scenery has its own sheet per level, `r_type_<LEVEL>_PAINTING_SCENERY.png` (see Scenery below).

Related figures sit together: frames of one object (they share artwork, or their artwork is stored
back to back at a similar size and in the same colours) and look-alike figures are grouped, in
order of their lowest ID.

## Painting

- Keep the size: one PNG pixel is one Spectrum pixel.
- Use the 15 swatches in the top row (the Spectrum colours; swatch 9 is opaque black).
- Grey inside a figure's box is transparent. A grey pixel can be painted (outlines), and a
  coloured pixel can be painted grey to make it see-through.
- **Bright pixels are paintable, faded ones are not.** The first time a graphic appears it is
  drawn bright; later copies of it (other frames, other figures using the same graphic) are drawn
  faded. Painting the bright copy colours every figure that uses that graphic. Paint on a faded
  copy is ignored, and the import names the figure so you can repaint the bright copy.
- Flash frames (a hit enemy drawn in one forced colour) keep the forced colour.
- COMMON also holds the "R-TYPE" logo letters, as drawn on the title and continue screens.

## Import

Until R-Type has an evidence record, from `specnext/reference/r_type/intake`:

```
py -3 r_type_colour.py recolour BUILD.nex r_type_LEVEL3_PAINTING_SPRITES_painted.png
```

The layout `r_type_LEVEL3_PAINTING_SPRITES_layout.json` must be next to the painted PNG. The output
is the usual recolour bundle: `BUILD_painted.nex`, its `_colours.json`, both sheets of that level
redrawn with the new colours (`BUILD_painted_r_type_<LEVEL>_PAINTING_SPRITES.png` and
`_IDENTIFY.png`), and a report. The shared recolour also prints a note that no reference sheet was
found: R-Type has none (the identification sheet replaces it), so ignore that note. Paint the next level on the redrawn sheet or the original: paintings
merge, and a pixel painted two ways is refused. Copy the `_colours.json` to
`nexclash/docs/profiles/r_type_colours.json` to make the painting the default for new builds.

Regenerate the sheets (after a new recording, or to show the default map's colours):
`py -3 r_type_colour.py sheets`.

## Figure IDs and identification sheets

Every figure has a stable ID, `L<level>-<number>` (L0 = TEXT), and belongs to a family,
`L<level>-F<number>`: the figures of a level that share graphics, such as one enemy's frames.

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

## Scenery

`r_type_<LEVEL>_PAINTING_SCENERY.png`: the whole level as it scrolls, in bands of 80 columns (640
pixels) one under the other, in the colours the build draws: black that connects to open sky is
grey (see-through).

- The build knows a scenery cell (8x8) only by its content, so every place a cell is used shows the
  same paint. Each distinct cell is bright the first time it appears and faded after.
- Paint with the swatches; paint grey to make a pixel see-through, or paint a see-through pixel to
  make it solid.
- Import exactly like a sprite sheet: `py -3 r_type_colour.py recolour BUILD.nex
  r_type_LEVEL1_PAINTING_SCENERY_painted.png`. The bundle redraws the scenery sheet with the new
  colours. Scenery keys sit in the same colours file as the sprite keys.
- Builds from 2026-11-20 carry the scenery paint banks (64-71). An older build is refused.
