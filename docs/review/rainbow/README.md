# Rainbow Islands - review images (private: they show game graphics)

From the collectables sessions (2026-10-11 / 12):
- rainbow_B_mask_sheet.png - layer B (dark-blue partial tiles): proposed inside masks, awaiting review
- rainbow_objects_no_borders.png - object / tile catalogue of both recordings as the current build
  (e50733b2) draws them: border on rainbow pieces only
- rainbow_objects_borders.png + rainbow_objects_borders.json - the same catalogue as bffd9357 drew
  it (black border on every object); the .json lists every code seen with its settings

The live settings are the `objects` section of nexclash docs/profiles/rainbow_islands.json
(collectables: opaque "15-255": {"border": false}). Regenerate the catalogue any time (in
nexclash, with the reference files):
`python -m nexclash.rainbow_objects rainbow.z80 rainbow.rzx rainbownew.rzx -o rainbow_objects.png`
