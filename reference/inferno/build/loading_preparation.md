# Loading-time live preparation experiment — 2026-11-07

The user approves a brief blank/loading screen before gameplay to front-load image construction.
This checkpoint implements an engine-local experiment using assembled components, not an installed
loading hook or a playable sprite NEX. Original game RAM/register behaviour and approved B visuals
remain required. Sprite display remains disabled.

`--loading-prep-check` freezes the original RAM view at the first 8F7C scenery event. It scans all
256 live C100 indices, rejects malformed/unsupported candidates, deduplicates exact ordered
geometry/IDs/bitmap/attribute contents, and runs the assembled snapshot, colour and whole-image B
workers. Completed source streams and canvases are packed into a host representation of expanded
cache pages 136–215 (655360 bytes); high staging 216–223 remains reserved for physical DDMA.
Every later actual draw compares retained prepared pixels against original-source B reconstruction
and runs the existing assembled exact source validator. Missing content uses the normal cold path.
No pointers/hashes substitute for exact live contents. This is not a recording-derived catalogue.

For the level-6 original 2000-frame replay, preparation completes 118 candidate images, 1534 tile
conversions and 188288 B pixels. Stored streams/canvases total 110875 bytes. All 2272 later actor
draws reuse prepared content, with 1057472 retained cached pixels compared and no mismatches.
The 119 malformed/unsupported indices are not claims about absent future assets; remaining indices
are duplicates or empty images. All existing original-state/frame/IRQ/negative checks still pass.

Preparation costs **6320.133 ms** of modeled assembled CPU work. It excludes host table scanning,
canvas zeroing, cache-store copies, dispatch/allocation, external wrappers and physical waits.
Thus 6.32 seconds is a subtotal, not a measured loading time or a promise of completion within a
few seconds. The cache representation/dispatcher remain host code; actual high-RAM persistence,
allocation metadata, loading UI, runtime bootstrap and cache integration are not installed.

Level 1 independently passes its original 2000-frame replay: 103 prepared live candidates,
86299 bytes and 4797.921 ms preparation CPU subtotal. All 2216 draws reuse prepared content;
5902976 retained pixels compare exactly. Warm capture/scenery/validation still costs 31.235 ms.
Its frozen first-draw point is frame 682. No unexpected-content cold construction was needed
in either sampled replay, which does not establish a full-game catalogue or all-level readiness.

Loading removes sampled cold actor construction: L6 capture/scenery subtotal becomes 8.715 ms.
Exact source validation remains: source work alone peaks at 12.447 ms/update, and capture/scenery
plus validation at **20.957 ms**, before lookup/allocation/uploads/queue/wrappers. The **10 ms TOTAL
runtime gate FAILS**. The gate now includes the validation-inclusive total when determining FAIL;
a lower cold subtotal cannot conceal an expensive warm path. DMA can copy prepared images, but
does not replace exact comparisons or B connectivity. Physical stalls remain unknown.

The first 8F7C event is frame 453 in this replay, after some original gameplay state has already
advanced. It is a convenient frozen-data experiment, not proof of a safe pre-game hook. A separate
point census finds 118 candidate contents at 86C5/frame 368, but that sampled PC is not an approved
hook either. The original loader tests stop at 718C before Nb executes; post-Nb initialization,
continuous loading, safe pause/resume, IFF/R/caller speed and ORIGINAL pacing must be proved.
A real loading message must preserve original screen/RAM state and resume the original flow.

Next: implement much cheaper exact validation, prove the level-initialization preparation boundary,
then installed cache/stream dispatch and high-RAM ownership. Prepare initial complete pattern/frame
state before revealing gameplay; retain bounded handling for later unseen or mutated content.
Current/pending pattern ownership, hardware limits and safe complete-frame switching still apply.

```bash
python -m nexclash.inferno --loading-prep-check ../specnext/reference/inferno/Inferno6.rzx --quick 2000 --json work/loading_prep6.json
python -m nexclash.inferno --loading-prep-check ../specnext/reference/inferno/Inferno1.rzx --quick 2000 --json work/loading_prep1.json
python tools/asm2profile.py --check inferno
python tools/doccheck.py
```

Canonical JSON distinguishes host selection/packing from executed assembled components. Existing
actor_jobs.md and actor_high_dma.md retain source/transfer contracts. No hardware proof or NEX.
