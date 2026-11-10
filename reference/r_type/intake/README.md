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
