# Background consumers and native modes — 2026-11-11

Continuation of live-budget-review.md. Targeted source review and source-only
initialization tests; no new renderer, intake/capacity/caller/ISR scan or emulator
pace run. Both repositories and the mode444 private SD are accessible here.
Fetched both remotes; no incoming nexclash main commits at this checkpoint.

## Actual background interface

The supplied book ingest provided a useful separation, but the binary establishes
these addresses. The two640-byte maps are **not** a convenient pair of background
tile IDs and sprite IDs:

| State | Native producer/consumer | Replacement obligation |
|---|---|---|
|7E00..807F,640 bytes|Plot helper8EA5 writes owners;8EC2 reads collision/adjacency;8842 clears most owners;8CD8 shifts them; native IRQ reads them|Keep native ownership, collision and special9C/DC..FF semantics.|
|8100..837F,640 bytes|8842 marks cells after foreground copy and clears marks after pixel erasure; IRQ BF11/BF45 reads dirty/owner state before drawing stars|Keep this state and its ordering even if ULA pixel copying is replaced. It is observable to native IRQs.|
|7800..7A7F,640 attributes|8EA2 writes source attributes,8842 copies30 columns to ULA,8CD8 shifts30 columns, IRQ changes source attributes|Retain native attributes and IRQ updates. Background colour cannot replace their gameplay/display roles.|
|8080..80CF|20 four-byte row descriptors: pixel end address and attribute end address|Not part of either640-byte map. Preserve star/controller access.|
|5E00..5EB3|20 staging records, each8 bitmap bytes plus one attribute|New incoming character column; not a640-cell map.|
|C4BC pointer|End of reversed144-byte background block pool and beginning of level-map stream|Validate mapping/generation; do not treat old addresses as stable identities after unpacking.|
|Level stream up to C4B4|Five map bytes per32-pixel-wide world column; low6 bits block ID, high2 bits horizontal/vertical flip|Independent logical background source, subject to native clipping, skips and live flip table.|

Reusing the retained ISR address sets: owner map609 read addresses, dirty map590;
neither is IRQ-written. Source attributes588 write addresses. These are retained
recording footprints, not new scans or proof that unobserved code has no consumers.
Native foreground-buffer pixel consumers outside the copier still need explicit
closure before removing their production; the known absence of ISR source-pixel
access alone does not establish that closure.

Each background block is4x4 cells, each cell one attribute then8 pixel bytes.
882D computes its address by native8-bit arithmetic before widening: for map byte
v, `C4BC - ((((v+1)*4)&255)*36)`, modulo65536. Do not assume an unwrapped64th block.
Source0x36 attributes skip a cell. Column0 is clipped by the plotters; initial
draw temporarily admits column31. The eight decoded streams contain respectively
107,67,64,74,74,62,74,184 world columns. Pointer spans are source-derived; no new
asset or capacity census was performed.

8979 calls8842 first. Old phase7 triggers8CD8. It then advances7A89/7A82; phase0
advances7A83 modulo4, advances7A84/7A87 every fourth character column, and copies
the prepared column directly to ULA column31. Source attributes lose bit7; bit7
sets background ownerFF. Phases2..6 consume five map bytes and dispatch8741/8778/
87B8/87F2 to build the next column;7A80 is its output pointer,7A85 its input cursor.
NOSCROLL7A8E suppresses that work. Neither replacing scroll nor skipping8842 can
silently remove these state transitions. A global hardware offset is not yet an
oracle for the conditional native pixel-scroll/erase behavior.

## Additional self-modifying modes

Earlier100-update watches covered8EB1/8EDA/8F0B-C only. Targeted source review now
identifies additional modes, exercised by native initialization rather than that
steady-play sample:

- 8A3F writes the horizontal limit at8D19/8D83/8DEF/8E49. Initial background draw
  uses32; foreground restores31.
- C3E5 sets8EBF=40 (direct ULA pixel destination) and8F10=D8 (RET C). C3EE restores
 8EBF=60 (foreground buffer) and8F10=D0 (RET NC). The four figure plotters also
 draw the initial background; hooks cannot assume every invocation is a figure.
- FF48 changes CALL operandFF53..54 to select the block's flip plotter.

Native FEEB initializes eight block columns through these live plotters, records
the next stream pointer in7A85/7A87, converts attribute bit7 into ownerFF, then
restores limits and buffer mode. Any replacement must explicitly handle this
background mode or use an intact native fallback. Earlier successful-cell tests
do not establish coverage of these new mode combinations.

## Independent initialization and flip evidence

`background_contract.py` reconstructs no new assets: it consumes the existing
source-only unpacker images, checks their SHA256, and compares native FEEB with an
independent block-map decoder. For each of eight levels it tests starting at0,
the midpoint and eight columns before the stream end: **24 cases pass**. All5120
pixel bytes,640 source attributes and640 owners match. Dirty map stays clear,
ULA attributes remain initially clear, next-column pointers and restored native
mode bytes match. IRQs are excluded; no scroll/RGB/cadence/replacement claim.
Results: background-contract.json. Reproduce from nexclash:
`../venv101/bin/python ../specnext/reference/r_type/intake/background_contract.py`.
Run live_budget.py first only if the private decoded-image fixture is absent.

The actual5D00 lookup table has `table[1]=0`, not the mathematical reversal80.
This holds in the original snapshot, fresh peak and all ten decoded images.
Using ideal reversal in the independent background model produces pixel
differences in **9 of24 cases**, while using the actual table passes all24.
This is observable behavior to preserve, not a request to correct the game.

There is also a concrete foreground compiler mismatch: a controlled legal cell
with eight01 rows, passed through the unchanged native plotters, produces00 rows
for horizontal/both flips. Current live_assets.group produces80 instead. Normal
and vertical agree. A negative control changing only table[1] to80 makes all four
flips agree, isolating the cause. Eight scoped foreground executions, not a
whole painted RGB test. This establishes a legal foreground counterexample;
the number of affected visible invocations is not established by these tests.

No compiler/runtime fix is claimed here. A delivery route must reproduce the
actual flip table or fall back when its table certificate is invalid. Source
byte guards alone do not validate that table. Its lifetime must be established;
do not silently normalize5D01 or infer immutability from these fixtures. Existing
live painted RGB/freshness gates remain open and now have this explicit case.

## Whole budget and decision

The matching fresh sample still requires9.385604ms/update savings. The measured
pixel-scroll section is0.984154ms; even free scrolling recovers only10.5% of that
deficit. Layer2 or tilemap offsets can address that specific visual operation,
but not identity checks, native state transitions, texture preparation or the
other legacy passes. The identified stream makes a background implementation
possible to evaluate; it supplies no measured performance pass by itself.

The gross14.176076ms legacy group contains0.897787 clone,2.900984 clear/restore,
7.556344 copier,2.820961 paper. Dirty/owner/attribute/IRQ effects must be priced
inside any replacement. Eliminating all of it would leave only4.790471ms for
retained effects, new background work and changed waits/IRQs. That is a
conditional equation, not spare time or a plausible implementation estimate.

**Native-time-credit constraint, source traced:** hook_entry opens the pace
window; nested prepare/publication work goes to debt. The un-nested original
copier contributes elapsed lines at28MHz; hook_finish scales that measured
window by K=104/16 and incoming speed, then adds signed cell_lines before the
debt-aware wait. RT_NEST_CLOSE before original_copy and RT_NEST_OPEN afterwards
are essential boundaries. Replacing the copier and retaining this calculation
would measure the replacement as though it were the displaced original. That
changes the target as well as the work. A valid replacement needs independent
original path cost/M1 accounting (including SMC and branch modes), excludes IRQ
time once, and charges its own complete overhead once. Do not adjust K to make
a pace test pass or spend the original copier's native cycles a second time.

**Decision:** no further renderer implementation is justified by the present
budget. Keep the existing sprite publication backend for comparison. Next price
the retained semantic loop and original-time/R accounting on the matching fresh
trajectory, plus independent background progression and unknown-art fallback.
Only if their complete estimate can recover9.386ms run one bounded combined
experiment. Its gates remain live painted100-update peak<=2%, state/ABI/R/IRQ,
native flip/mode cases, stale-source/ownership, pause/menu/DI and RGB; no sound
equivalence claim follows from50Hz or equal FE totals. No engine/sheets/final
verification before a complete route passes.
