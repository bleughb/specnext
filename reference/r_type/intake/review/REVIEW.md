# R-Type capacity review

Independent measurements from the one reviewer authorized by the owner. Observations and interim
recommendations, not approval of an assembled engine or its timing.

## Classification corrected

The original maximum scene contained THANK-YOU text, which stays on ULA under the approved design.
The tile plotters draw text too: ownership1..DB is not a figure classifier. Owner88 is text only
for this particular graphic; it is a normal enemy slot elsewhere.

Measured per-plot identity: HL=CAFF, D=21, E=24, graphics signature in packing.py. Text is frame32
through8E85, normal plot8CFD from917A; C4BA=D99C in that scene. Track this graphic role per owner
for the current pass; a different plot clears the tag. Other flying figures remain sprites.

## Full corrected census

90,102 frames,18,576 refreshes, no desync;400 text draws,36,119 text-cell visits excluded.
Exact visible nibble patterns, not attributes under transparent quadrants.

| Layout | Max sprites | Max patterns in one state | Max protected old+new patterns |
|---|---:|---:|---:|
| Screen grid |105|103|183|
| Owner origin |111|104|176|
| Owner best parity |108|101|174|

Every one-state layout fits128 sprites/patterns. Concurrent old+new storage is an implementation
constraint, not a hardware/user requirement. Owner alignment and monochrome sharing do not solve it.

## Recommended next experiment

Prepare complete4bpp images in ordinary Next RAM. Publish into the single pattern bank while the
beam is outside the160-line play area, together with clean ULA and attributes. This avoids old+new
storage without changing approved visuals.

Gate: measure the COMPLETE worst publication span: setup, MMU changes, upload, ULA copy, attributes,
DMA stalls, IRQ/audio and fallback. Fit the measured contiguous off-play interval (151 raster lines
in311-line128K timing), no late publication/sprite loss; preserve update pace and freshness. Test
ordinary DMA/no-blitter and CPU fallback separately. Peak DMA rate or uncontended T is not proof.

Main-session follow-up hypothesis: run the original accelerated clean copier into a spare ULA
page before the publication window, then copy the prepared ULA with the patterns inside it. This
could shorten the critical span, but needs proof for shadowed non-display variables and ISR effects.
It is neither implemented nor validated.

Consult midres_hooks.asm SLOTST/SLOTENT (128 logical4bit slots, visibility tracking) and
renegade_hooks.asm half-pattern upload through303B. A visible sibling half need not be rewritten.

## Boundaries

35 sampled copier-removal states with corrected text classification passed registers includingR,
non-ULA RAM and predicted ULA (text retained). Full source/ROM/tail access scan completed. Full ISR-specific proof
has since completed:90,102 frames/86,553 IRQs. The owner supplied a compressed private SD image;
JNext1.2.0 now boots. Follow-up publication/IRQ/shadow prototypes are documented in ../README.md. User reports the supplied plain build works in JNext
and real hardware (2026-11-10); no sprite build tested.

Follow-up review: ordinary-DMA fallback satisfies the no-blitter requirement; CPU-only need not
be offered. The observed CPU deadline failure rejects that route. A shadow-slot2 protocol must
copy5B00..5FFF state back (ISR reads314/writes157 addresses there), retain shadow through all
preparation IRQs, and exclude IRQs during publication. Clone/clear atomicity, its native-IRQ
phase, final EI delay, R sampled inside IRQ and restored MMU6 remain explicit runtime obligations.
Measured shadow prototype passes; dynamic generation and whole-hook pace remain gates.
