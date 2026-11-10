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
- `review/`: independent measurements and classification. THANK-YOU text is ordinary
  enemy slot88 in this scene; classify its graphic identity, never exclude slot88 globally.
- `r_type_tools.log`: shared analysis checks; survey regression/golden pass, pre-existing Inferno
  IFF audit failure. Canary and doccheck pass in their separate logs.

Run experiments from nexclash using ../venv101/bin/python (SkoolKit10.1, Pillow13). Original and
derived game data stay here, never in nexclash. Owner reports the plain build working in JNext and
real hardware (2026-11-10). No sprite build or sprite hardware result yet.

## JNext publication probes (2026-11-10)

The uploaded compressed SD image boots JNext1.2.0; it is private/read-only at
`/workspace/scratch/cspect-next-2gb.img` and MUST NOT enter either repository.
Original plain gameplay baseline:100 updates at15.83updates/s, penalty-0.04%.

- `isr-footprint.json`: full90,102-frame shared ISR API result,86,553 accepted,0 unreturned.
  Pixel source is untouched;588 source attrs and157 slot2 non-display addresses are ISR-written.
- `irq_capture.py`: reproducibly captures the longest original ISR in first4000 frames into
  `/workspace/work/r_type_irq_max_state.json` (generated game memory, deliberately not committed).
- `publication.asm/py`: transfer-only synthetic worst105-pattern/ULA/attribute publication;
  CPU14.771ms, ordinaryDMA5.556ms. All expected bytes/row deadlines pass, IRQ excluded.
- `publication_irq.asm/py`: original native audio IRQ added, CPU35.150ms misses rows2..9;
  ordinaryDMA still finishes before the IRQ. CPU-only is rejected, no-blitter uses ordinaryDMA.
- `publication_shadow.asm/py`: actual copier/clear/restore ahead of publication; original long
  IRQ runs while slot2shadow mapped. Copy1280 non-display bytes at NR150, publish atNR160.
  DMA attribute batching gives5.100ms no-blitter/5.084ms default on the older emulated core.
  Next native IRQ follows about0.63ms later. Pixel/attr/pattern/tail/HUD/source-hole checks pass.
  The clone/clear phase is DI, starts NR170 and enables IRQ before247; runtime must prove this
  phase cannot mask an IRQ at every actual entry. MMU6 restoration and R remain engine work.
  A forced sentinel at5B64 verifies propagation through the shadow tail; removing only the
  actual tail-copy CALL catches the lost byte. No full machine/whole-hook equivalence claim.
- `publication*-timing.json`: raw marker/cycle/deadline records for those experiments.

Run `../venv101/bin/python ../specnext/reference/r_type/intake/publication_shadow.py` from
nexclash. The script expects the local JNext executable and private card path above; creates only
scratch NEX/JNS/logs under `/workspace/work`. All assemblies use the project's pinned sjasmplus.
Core3.03 DDMA is gated but not exercised by this older JNext core; mode2 here uses ordinaryDMA.
Dynamic pattern generation, complete register/R/stack equivalence and integrated pace remain
unproven. These prototypes are not the R-Type sprite build.
