# Live budget and self-modifying-code review — 2026-11-11

Current evaluation after restoring the owner's private SD upload. Supersedes the
implementation directions in the earlier source-only review, not its scoped results.
No renderer variant, timing-constant adjustment, intake/capacity/caller/ISR census
or engine promotion. All measurements below concern existing diagnostic routes.

Documentary follow-up: book-ingest-review.md compares the supplied summary without
downloading the book. SCROLL6 matches8914..8973 exactly; background/sprite map
separation guides consumer review, without establishing both maps' addresses.

## Where we are stuck

The static preexpanded control demonstrates that bulk4bpp publication can fit.
The live route still pays for both the legacy picture pipeline and the hardware
picture, then adds identity/ownership work between them. Local lookup improvements
do not remove that duplicate work. The native1bpp tile route avoids much of the
preparation but does not satisfy per-pixel painting. No complete live painted
route has passed pace, RGB, freshness and the remaining equivalence gates.

We also over-constrained the problem by treating every original pixel write as
mandatory. Collision/ownership RAM, R, sound and other observable effects are
requirements. A particular pixel copier, shadow image or clear pass is an
implementation choice until its consumers show otherwise. Inferno's lesson applies:
identify those consumers and price the complete replacement before more tuning.

The copier also reads its previous displayed background while scrolling, so simply
dropping selected pixel writes while retaining the copier is unsafe. A complete
replacement needs an independent background representation. Meanwhile8842 mutates
owner/dirty state and8CD8 shifts native attribute/owner maps; those effects need a
separate accounting. Owner/ink/level equality alone is not a freshness certificate
after clear/shift/reuse. The cached route's stale-ownership/RGB checks remain open.

## Fresh sample and controls

JNext1.2.0 restored from the official Ubuntu24.04 package, SHA256
86ab6e91619322914fd5ef2b2e5a55a5fe22c5e541146f229440a723f29498e5.
SkoolKit10.1/Pillow13.0.0; bundled sjasmplus1.24.0. Card remains mode444 at
/workspace/scratch/cspect-next-2gb.img; every launch uses --sdcard-readonly.
Isolated home /workspace/work/r_type_jnext_home. No card/JNS metadata is in Git.

The old peak/profile scratch files were absent. This new explicit recipe cuts the
original RZX at29405, extracts the snapshot, supplies no input, probes8649 and
measures100 update intervals. Snapshot MD5 **9cfed755be2d7ae90a3876ea617f87bf**;
this is not the old aab78a9d fixture. Do not combine their budgets.

| Existing route | MD5 |100-update elapsed|Penalty|
|---|---|---:|---:|
| Original peak snapshot |9cfed755be2d7ae90a3876ea617f87bf|10.516004s|reference|
| Static preexpanded control |ca5023185c9681beb89bf36b957bc586|10.651987s|+1.2931%|
| Cached producer IDs |91f7066eaf48f4df38db755cb444ca91|11.664885s|+10.9251% FAIL|

The fresh2% ceiling is107.263244ms/update. Cached IDs need9.385604ms/update savings.
Static has0.743371ms margin but remains a cost control, not live painting.

Read-only phase markers leave **all101 update clocks and all380 monitored bytes
identical** to uninstrumented runs, separately for original and cached IDs.
Nested phase sums conserve elapsed time; duplicate/orphan-end negative is caught.
Copier-section accounting excludes nested IRQ spans. Execute addresses can be
reported again after an intervening IRQ; active flags prevent duplicate boundaries.
The targeted write-watch runs independently reproduce the same clocks/monitor bytes.

All routes make99 copier/controller calls in100 intervals, including the native
game-over path. This is not a claim of a missing rendered gameplay update. All
other native work and marker-edge instructions stay in the ledger's residual;
that residual is not free time. Inclusive parent spans overlap their children;
only exclusive columns may be summed. Full detail: `live-budget.json`.

## Where the time goes

Exclusive elapsed means per update, with nested IRQ marker spans separated:

| Group |Static control|Cached IDs|
|---|---:|---:|
| Figure work, successful-cell wrapper and producer resolver |15.158ms|19.340ms|
| Complete pattern preparation, renderer checks/bridge and texture staging |23.636ms|30.963ms|
| Shadow clone + clear/restore + original copier + post-copy paper |14.176ms|14.176ms|
| Publication, including payload |3.110ms|3.055ms|
| Publication raster wait + credit/debt/wait/return |11.128ms|8.147ms|
| IRQ marker spans |8.008ms|8.635ms|
| Remaining game/controller/edge work |31.303ms|32.334ms|
| Total |106.520ms|116.649ms|

Cached-ID identity checks/bridge alone total9.961ms (producer3.925, renderer4.034,
bridge2.002). Even deleting these at zero replacement cost would only narrowly
cover9.386ms; real dispatch, lifetime/ownership validation and fallback cannot cost
zero. This is why more per-cell lookup tuning is a poor default direction.

The legacy display pipeline breaks down into clone0.898, clear/restore2.901,
copier7.556 and paper2.821ms. This is a larger structural target. Some of that work
has non-display effects, so14.176ms is a **gross hypothesis**, not removable time.
It also contributes to the current native-time credit: deleting it without
replacing that accounting may change cadence rather than free a usable budget.

## Could Layer2, tilemaps or scrolling help?

The fresh, actual copier pixel-scroll section costs **0.984ms/update** in cached
IDs, versus6.870ms in the original. The old source-only0.609ms estimate divided a
different RZX trajectory by8; it was not a live measurement and is superseded here.
Scrolling alone does not approach9.386ms.

A hardware background representation could remove more of the clone/copy/clear/
paper pipeline and possibly some publication. That is the worthwhile architectural
question. A1bpp background tilemap with hardware foreground sprites is a candidate,
not a selected implementation. The old foreground4bpp capacity failure does not
establish background capacity. The rejected Layer2 foreground route does not
rule out a different background use, but a new Layer2 clear/copy/edge-update cost
must be included. Copper/DMA/DDMA do not remove ownership, lifetime or identity work;
ordinary DMA already publishes in about3.055ms. No new backend prototype yet.

Native1bpp tilemap mechanics and bank7 asset relocation already have scoped evidence.
The missing background source/update and state/credit interfaces are the hard part;
more platform-feature experiments alone will not establish this replacement.

For a precise candidate, if all14.176ms pipeline work could go, retained state/R/
SMC accounting, new background work and changed IRQ/raster/debt waits together
would need to cost **at most4.790ms/update** to cover the fresh deficit. Removing
less makes that bound tighter. This is a counterfactual budget equation, not an
allowance or evidence those stages can all be removed. Price actual retained
effects and any changed waits once, without reusing native credit twice.

## Self-modifying code: active and relevant

The targeted watch covers the known native controls,11 hook-site prefixes and all
12031 packed-art bytes in two physical spans (A604..BC5D on page5; C4E0..DD84 on
page0). No broad access/ISR scan. Native controls have the same ordered
(update,address,value,writer-PC) sequence in original and cached-ID runs:

| Native target | Function | Writes in each run | Values observed |
|---|---|---:|---|
|8EB1|Operand of `LD A,n`; effective attribute/Force override|793|00,43,44,45,46|
|8EDA|`RET`/`NOP` enables collision-report side effects|332|C9,00|
|8F0B/8F0C|Neighbour-collision path or forced-success path|1 each|1C/1A restored in this sample|

Source inspection also shows90B5 installs37/C9 (`SCF; RET`) at8F0B/8F0C;
90F7 restores1C/1A. 9A1E/9A26 bracket certain plot calls by writing00/C9 at8EDA.
Attribute writers include9593,9F07,9F30,A026,C07B andF67D in this sample. These
are live rendering/logic parameters, not evidence of artwork bits being rewritten.

**Zero writes** hit the watched hook-site bytes or packed-art bytes in either run.
This supports the current hooks within this sample; it does not prove all levels,
unobserved writers or level-long immutability. Loader/unpacker source changes still
require generation/invalidation and unknown-art fallback.

Current hooks leave8EA5/8EC2 and those control bytes live, explaining why these
native mode changes remain visible. Copying a frozen helper elsewhere would not:
original writers would modify the old address. Any combined writer must use the
native helper, consume the live mode explicitly, or redirect/mirror every relevant
write and test both modes. Timing/M1/R accounting must follow the executed mode.
The unpacker and our private return-R/clock/credit operands also self-modify;
their lifetime/reentrancy rules remain separate. No evidence here attributes the
10.925% slowdown to a hook being overwritten by SMC.

## Equivalence boundaries and next gate

Of380 monitored game bytes,378 match at all101 boundaries. Differences are7A8A
(three-IRQ wait counter) and7A9D (IRQ star-animation counter, incrementBE83 and
readBEA6/BEB1). Do not report whole-RAM equality. Shared steady-play counters show
50Hz IRQs in all routes and maximum sampled gaps about20.265ms. Complete-window
FE totals are11105 in each, with different rates (original1056.01/s, live952.00/s).
Neither equal totals nor these counters prove sound/event/RGB equivalence.

Next is consumer and accounting review of the duplicate display pipeline: separate
visible writes from owner/map/collision mutations, identify native pixel readers,
keep both SMC modes and original R/cadence, and price the proposed background source,
edge updates, fallback and publication. Only then select one bounded implementation
against the9.386ms deficit. No further per-cell tuning by default. A complete live
painted <=2% run, stale-source/ownership, ABI/R/IRQ/RGB/pause/menu/DI checks still
precede engine/profile/registry/record, sheets/recolour and final full verification.

Reproduce from nexclash: `../venv101/bin/python ../specnext/reference/r_type/intake/live_budget.py`.
It reconstructs missing source fixtures and uninstrumented controls; generated game
bytes, logs and JNext home stay in work. `--analyze` reuses existing logs. No uploaded
document instructions were executed; the archive supplied only the private card image.
