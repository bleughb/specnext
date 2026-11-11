# R-Type intake evidence

Source: nexclash branch add-r-type; visual design approved 2026-11-10: all figures/effects as
sprites, see-through, no outlines; original colours, depth and pace; ULA scenery, HUD and text.

Current evaluation: [live budget / SMC review](continuation/live-budget-review.md).
Private card and official JNext1.2.0 restored; fresh explicit fixture/profile fails10.925%.
The existing-route ledger and targeted SMC watch are measured; no renderer was added.
Read the whole-pipeline consumer/native-credit directions there before more coding.

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
At that checkpoint dynamic preparation and integrated pace were unproven; the continuation
below measures them in bounded cases. Complete IRQ/R/stack equivalence remains open.
These prototypes are not the R-Type sprite build.

## Dynamic preparation and early integration (continued 2026-11-10)

These extend the existing publication protocol; they are not the R-Type engine.
`publication_shadow.asm` retains its synthetic default. Conditional dynamic code
moves clearing after the atomic clone, allowing IRQs during live preparation.

- `publication_dynamic.asm` / `_body.asm` scan all 640 source cells into a fixed
  screen grid; generate packed 4bpp patterns, native inks (black maps to palette8),
  visible attributes and hidden unused slots. Capacity105 is checked before committing
  a candidate; overflow halts explicitly. Two ordinary-DMA zero fills avoid CPU writes
  to empty quadrants. There is no cross-frame pattern cache or host-prepared image.
- `publication_dynamic.py`: independent per-bit oracle; actual23-sprite/native-long-IRQ
  state3620 and observed105-sprite peak29405 both match every active pattern/attribute,
  cleared figure ULA bytes, HUD, restored source pixels, post-IRQ source holes and tail.
  Default preference and no-blitter publication both pass row deadlines. Preparation
  47.687ms / 71.758ms includes native IRQs; publication5.100ms / default5.084ms.
  Broken runtime LUT catches813/5392 bytes; omitted clear catches328/1887 ULA bytes;
  omitted tail and broad source restoration each catch their forced lost sentinel.
  Source-hole expected state includes IRQs during the wait, not just preparation.
- `refresh_capture.py` reconstructs only the already-known peak copier state if absent.
  This is targeted replay to29406, not another caller/capacity/access census.
- `publication_integrated.asm` / `_body.asm` and `.py`: early diagnostic through the
  shared converter/tail. Hooks the actual8842 copier, preserves its actual output
  registers, restores MMU6/speed and returns on the caller's stack. Clone begins only
  below NR210 or from249 onward; fixed170 entry waiting gave9.80% pace loss, whereas
  guarded entry gives0.82% over100 updates (worst20-update window1.72%). Original/build
  both15.83 updates/s,49.83 IRQ/s, longest IRQ gap40.5ms. No gameplay state lockstep claim.
- `integrated_check.py`:100 copier returns in each mode, exact12 returned register
  fields, SP/MMU6/IFF,34048 RAM bytes from tail transition to return, no accepted IRQ
  in clone or publication critical intervals. Max hook64.42ms; max publication interval
  101.31ms. Forced IY corruption is caught100 times. C000..DFFF and pre-tail IRQ effects
  against the original are excluded explicitly. Minimum observed private SP3CE4
  (the broken-control run reached3CDE); this is not instruction-by-instruction IRQ proof.
- `register_bridge.py`:24 isolated original-vs-assembled bridge cases across both
  captured states, six R seeds including bit7, and wrong-return-R controls. All caller
  registers including R/SP/IFF/IM match without IRQs. Native IRQ R reads at BEDB/BF36
  still need supplied-R consumer proof; return repair is not that proof.

Compact results: `publication_dynamic-timing.json`, `publication_peak-timing.json`,
`integrated-check.json`, `register-bridge.json`, `integrated-pace.json/.txt`,
`integrated-summary.json`. Raw NEX/JNS/machine dumps and50MB exact-boundary logs stay
in work. JNS saves are deferred to a frame boundary: exact ABI/RAM comparisons use
execute-time registers and dump_mem, not JNS CPU state. The private SD image stays
outside both repos and every emulator invocation uses the read-only flag.

Reproduce from nexclash (with the local venv/JNext/card paths in the handoff):

```
../venv101/bin/python ../specnext/reference/r_type/intake/refresh_capture.py
../venv101/bin/python ../specnext/reference/r_type/intake/publication_dynamic.py
../venv101/bin/python ../specnext/reference/r_type/intake/publication_dynamic.py --state /workspace/work/r_type_peak_state.json --out /workspace/work/r_type_publication_peak
../venv101/bin/python ../specnext/reference/r_type/intake/register_bridge.py
../venv101/bin/python ../specnext/reference/r_type/intake/integrated_check.py
```

`publication_integrated.py` builds `/workspace/work/r_type_integrated/diagnostic.nex`
and its frame2000 original fixture for the shared pace command. Use probe8649 and
100 updates, as in `integrated-pace.txt`. It is NOT a user/hardware build: text-owner
flags currently have no plot hooks, entry-IFF0 is explicitly unsupported, source paper
handling is not integrated, full banked RAM/IRQ equivalence and colour/recolour are open.
Core3.03 DDMA is still untested; this JNext core exercises ordinary DMA in both modes.

## Native text tiles and per-pixel provenance (continuation)

Current accepted native-colour candidate: `publication_tilemap.asm`, hardware1bpp text tiles
with source bank7 assets relocated through the original8F21 read gate. `continuation/` holds
compact results; this is still feasibility, with no engine/profile/record/sheets or release stamp.
The full-sprite peak route11.36% slow, full-byte LUT5.40%, and worse cache trial stay rejected.
Native tiles1.32% slow over100 updates (worst20 window2.27%),378 state bytes equal every update,
50Hz native IRQs both and equal FE writes. Includes640 saved foreground attrs for native pause.

Reproduce using ../venv101/bin/python from nexclash, with these intake scripts:

- `irq_equivalence.py`: native IRQ supplied-R consumers,218 reads/14 states, wrong-R controls.
- `copier_equivalence.py`: full caller registers/R, eight logical game banks, exact clean ULA,
  rendered glyphs;18 dead stack bytes overwritten before read through caller/first native IRQ.
- `interrupt_boundaries.py`:113543 quiet native IRQ injections/841 PCs; negative MMU0 restore.
- `text_check.py`:80 live graphic identity and ABI/R cases, including reused owner88.
- `tilemap_bank_check.py`:80 relocation bank/edge/R cases. Bank7 assets clone into bank24;
  physical bank7 becomes BRAM text map/defs. Separate full paging-port census was necessary
  to establish this relocation; it did not repeat intake/capacity or ISR scans.
- `tilemap_geometry.py`: empty/edge/inks,511-glyph capacity/512 overflow, mutated actual bound.
- `tilemap_preview.py`: actual JNext frame versus independent49152-pixel RGB oracle;
  post-preparation glyph bit corruption produces one pixel/one glyph mismatch.
- `pause_check.py`: checks actual converter output uses CALL,12 ABI/R/picture cases including
  repeated pause and deliberate future-source changes. `pause_jnext.py`: actual CapsShift+1/2,
 261 repeated pause calls/one resume, correct native continuation/layer visibility/IFF.
- `integrated_check.py --asm publication_tilemap.asm --source /workspace/work/r_type_integrated/peak.z80
  --out /workspace/work/r_type_tilemap_final`:100returns each mode,42240 checked RAM bytes and
  caller registers exact;100 wrong-IY controls caught. Longest publication interval includes
  the native game-over pause, rather than a skipped game update.

`cell_plot.asm` / `publication_cell.asm` are a separate small successful-writer trial.
Original8EA2 helper plus all four row-copy bodies run at28MHz, with original outputs/R,
source RAM and clock restored. Per-plot clock latching, native DI fallback, and descriptors
(source attr pointer, flip, effective ink including Force override, owner, level) support the
pending per-pixel colour route. Only successful writes enter this gate; rejected collision
checks never create metadata. Private page50 is never game data.

`cell_check.py`:160 crossed real-helper/synthetic-continuation cases, exact caller registers/R,
logical game RAM and descriptors. Credit matches the COMPLETE original minus COMPLETE hook
CPU cost, including bookkeeping, and retains fractional scanline units.9 division edges pass.
`plot_equivalence.py --cell`:64 full real plot calls including both IFF states. The pre-latch
refinement pace result1.53% is retained; remeasure later changes before any acceptance claim.
`cell_interrupts.py` tested759 quiet IRQ boundaries across all four flips before the latest
clock-latch/DI refinements; those need their updated run. No full-recording claim.

The retained `publication_fastplots.asm` broad acceleration trial is rejected:7.83% overall,
13.37% worst20. `plot_equivalence.py` passes64 ABI/R/live-bank cases, which does not establish
pace. Independent review diagnosed wrapper work incorrectly multiplied as original time and
per-call raster quantisation; current exact cell credit avoids both. See continuation review.

Current decision: see [completion review](continuation/completion-review.md) for the
bounded cached-ID failure, alternatives and completion gates. Layer2 is parked;
next evaluate identity once per plot/level before implementing another prototype.
`publication_inlined.asm` and its inline helper/cost files are UNTESTED WIP, with zero
placeholder costs. They are retained for provenance and must not be selected for delivery.
All generated NEX/JNS/raw captures stay in work; private card access remains read-only.

## Source-only identity/budget follow-up

[Source identity review](continuation/source-identity-review.md) establishes the proposed
invocation-local validation/fallback contract and rejects unchecked level-installed IDs.
`identity_budget.py` reconstructs all1288 packed plots, checks source mutations against
the retained ISR write set, and counts only100 original peak updates after frame29404.
Plot-only identity cannot recover the required9.22ms/update on this CPU estimate;
combined acceleration of remaining native plot work has a plausible bounded budget.
No intake/caller/capacity/ISR census was repeated and no renderer variant was added.

`plot_guard.asm` / `plot_guard_check.py`: one comparison component for that combined
direction, assembled by the bundled pinned tool.352 images accepted,1056 changed-source
cases rejected, actual broken-CP negative caught; exact hit59*length+100 CPU T before
caller CALL. AF/R, dispatch/invalidation, IRQ and live hardware painting remain open.
Compact counters: `continuation/identity-budget.json`, `continuation/plot-guard-check.json`.
These commands need the documented Python environment and the checked-in originals,
not the private SD image or JNext. Decoder bytes/cut RZX/real states stay privately in
/workspace/work/r_type_review. The review gives reproduction commands and stop criteria.

Inferno correction: the combined CPU estimate is not a whole-route budget or an
implementation gate. `total_budget.py` / `continuation/total-budget.json` price the
entire original100-update CPU sample. The current copier already runs at28MHz:
its pixel-scroll section is nominally0.609ms/update of current CPU, not4.871ms new
savings. Hardware backgrounds remain conditional on a complete cost/consumer ledger;
the review lists missing live phase costs. No more guard/backend tuning before that gate.

`live_budget.py` now supplies matching live costs (new recipe, not old scratch-file
reproduction), uninstrumented clock/state controls and targeted native-SMC/hook/art
write-watch controls. `continuation/live-budget.json` records every exclusive phase,
counter differences, SMC values and source/input hashes. Source-only0.609ms scrolling
was nominal; the actual new sample measures0.984ms. Existing-route costs are now known;
new-route retained effects, background generation and native-time credit remain open.
