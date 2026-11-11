# Completion review — 2026-11-11

This is a feasibility checkpoint, not an engine or release. No new renderer experiments
are authorized by this plan itself. Design remains approved. One owner-approved reviewer
has already reviewed the earlier bottleneck; this reassessment is by the primary agent.

## Bounded result

`publication_resolved.asm` resolves guarded source identities at the successful cell writer,
then caches texture IDs for the renderer. `resolved_cell_check.py` passes 320 combinations
of resolver outcome, flip, Force override and R, including exact whole-invocation CPU credit.
The additional signed-budget tests include the shared debt cap and retained negative fractions.

Peak snapshot frame29405, same state profile/probe8649,100 updates,2% existing threshold:
10.531109s original /11.663207s build = **10.7500% slower**, worst20 window18.8695%.
State matches every sampled update; IRQ rate50Hz both. FE writes per second1085.78/977.2;
these are rates, not total-write counts. Sound/event equivalence is not established.
To reach2% on this sample, remove at least0.921476s per100 updates (9.215ms/update)
from this build without altering native behavior. This is the minimum savings target
for a proposed replacement; it is not an assumed available budget.
Result: FAIL pace. This improves the guarded live lookup15.26% but does not close feasibility.
See `resolved-pace.json` and `resolved-pace.txt`; generated diagnostic stays outside Git.

## Re-evaluated directions

| Direction | Evidence | Decision / next necessary proof |
|---|---|---|
| Native1bpp tilemap |1.32% peak pace; independent RGB/IRQ/pause checks |Retain proven native baseline; alone cannot satisfy per-pixel painting.|
| Preexpanded4bpp sprites |Static cost trial1.52%; live guarded lookup15.26%, producer-resolved10.75% |Keep as leading colour backend, stop current per-cell lookup tuning. Static trial is not a live colour proof.|
| Resolve once per plot or level |All9789 raw variants reconstruct from original unpacker;8711 filtered keys unambiguous in recording |Preferred next feasibility direction: install level-specific dispatch or resolve a plot once, reuse sequential cell IDs. Must prove source lifetime/invalidation and preserve unknown-art fallback; uniqueness in a recording is not immutability.|
| Replace redundant original drawing |Current path still writes original rows then reconstructs hardware output |Second direction: use retained read/write evidence to identify original outputs that can be replaced by a faster combined writer. Collision/owner RAM and R remain observable. Requires precise consumer proof, not wholesale omission of original drawing.|
| Sparse painted overlay on native tiles |May reduce work for lightly painted sheets; all-painted L2 still11.81% |Conditional optimization only; cannot make completion depend on users painting few pixels.|
| Layer2 full foreground |Independent static RGB passes; measured21.46→17.17→11.81% |Park current implementation. Larger copies/clearing remain costly; no evidence a backend switch solves identity overhead.|
| Standard4bpp tilemap |Peak274 patterns,263 after flips versus176 usable definitions |Capacity failure for current layout. Copper bands would need new capacity/atomic-publication proof; park.|
| Hardware scrolling |Does not replace collision/owner production or sprite identity |No measured bottleneck it solves here; retain ULA scenery.|
| Copper |Can schedule display state, not source-identity computation |No current measured benefit; do not add complexity without a specific publication bottleneck.|
| DMA / DDMA blitter |Ordinary DMA already batches publication; DDMA3.03 unavailable in current emulator |Keep DMA. DDMA needs compatible validation and fallback; cannot remove pointer lookup or validate source identity.|
| Inline cell-entry optimization |Unfinished source with zero placeholder timing constants |Quarantine; never select for builds or claim verified. It addresses entry overhead but lacks evidence it can recover10.75%.|

## Completion sequence and stop rule

1. Preserve this checkpoint and correct the stale handoff. Do not restart intake scans.
2. Before implementing a new route, derive its cost and invalidation contract from existing
   captures/source-only decoder. Prefer once-per-plot/level identity over repeated8-byte guards.
   Only run a new prototype when that estimate can plausibly recover the measured deficit.
3. Require a complete live painted peak test at <=2%, matching game state, then ABI/R/IRQ,
   rendered pixels, stale ownership, source mutation and pause/menu/DI checks. Passing a
   static picture or adjusting pacing constants does not satisfy this gate.
4. Promote one route into the additive engine/module/profile, whole-figure sheets and
   recolour readback. Validate palette/capacity, quick recording checks, then one final full
   verification and the hardware checklist. No release stamp before these steps.
5. If once-per-plot/level identity cannot meet the budget, review combined-writer replacement
   with explicit consumer evidence. Do not open more render-backend prototypes by default.

## Checkpoint boundaries

All retained sources are per-game reference experiments. Inline files are untested WIP;
`publication_inlined.asm` must not be delivered. Native-path results apply to their recorded
configurations, not automatically to later conditional variants. Live sprite pause, signed
credit IRQ interaction, complete painted RGB and whole-recording verification remain open.
Private SD image and JNS metadata stay outside Git; all emulator card access is read-only.
