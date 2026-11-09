# R-Type intake evidence

Source: nexclash branch add-r-type; visual design approved 2026-11-10: all figures/effects as
sprites, see-through, no outlines; original colours, depth and pace; ULA scenery, HUD and text.

- `plain.py` builds ../Rtype.nex from ../Rtype.z80 and checks the plain boot. `plain-boot.json`
  records its MD5, exact-R check and the negative control for printer restoration.
- `full-access.log`: all 90,102 frames, ROM/tail access proof. Tail 5B00..5B4E lies in untouched
  5B00..5B63. ROM1F00..3FFF untouched; code at3D00 remains excluded for DivMMC compatibility.
- `survey.md/json`, `preview.png`: corrected survey of first2,501 frames, not whole-game coverage.
- `r_type_figure_coverage.json`: complete recording, all17 static caller candidates reached.
- `recording-preview.png`: original screen samples through the entire recording.
- `removal.py/json`: game-specific source-pixel/paper replacement experiment,35 captured states;
  exact registers including R, non-ULA RAM and predicted ULA. No assembled/IRQ/timing claim.
- `feasibility.py`, `sprite-budget.json`: first global-grid budget; includes credits text and is
  superseded for sprite classification by the independent review. It is not a hardware lower bound.
- `review/`: independent measurements and classification; in progress. THANK-YOU text is ordinary
  enemy slot88 in this scene; classify its graphic identity, never exclude slot88 globally.
- `r_type_tools.log`: shared analysis checks; survey regression/golden pass, pre-existing Inferno
  IFF audit failure. Canary and doccheck pass in their separate logs.

Run experiments from nexclash using ../venv101/bin/python (SkoolKit10.1, Pillow13). Original and
derived game data stay here, never in nexclash. Hardware has not been tested.
