# Loading-time live preparation experiment — 2026-11-07

Latest checkpoint: [loading_owned.md](loading_owned.md): checked 8EF9 initialization pause,
assembled owned high-RAM store/dispatch and direct exact validation. Six quicks pass;
warm totals 10.167–16.317 ms still FAIL. Runtime scan/driver/UI and full frame integration remain open.

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

For the unoptimized level-6 original 2000-frame baseline, preparation completes 118 candidate images, 1534 tile
conversions and 188288 B pixels. Stored streams/canvases total 110875 bytes. All 2272 later actor
draws reuse prepared content, with 1057472 retained cached pixels compared and no mismatches.
The 119 malformed/unsupported indices are not claims about absent future assets; remaining indices
are duplicates or empty images. All existing original-state/frame/IRQ/negative checks still pass.

Preparation costs **6320.133 ms** of modeled assembled CPU work. It excludes host table scanning,
canvas zeroing, cache-store copies, dispatch/allocation, external wrappers and physical waits.
Thus 6.32 seconds is a subtotal, not a measured loading time or a promise of completion within a
few seconds. The cache representation/dispatcher remain host code; actual high-RAM persistence,
allocation metadata, loading UI, runtime bootstrap and cache integration are not installed.

The unoptimized level-1 baseline independently passes its original 2000-frame replay: 103 prepared live candidates,
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

## Exact validation optimization

The source worker now bounds each eight-byte bitmap span once. Capture uses eight unrolled LDI
instructions; validation compares eight bytes directly, without generic stream calls per byte.
The remaining stream emitter uses scratch C instead of stack saves and pointer exchanges.
Order, length, phase, paint and all original-source bytes remain exact. No hash/pointer shortcut,
DMA search assumption, or unproved source-lifetime deduplication is introduced.

The small exact-hit unit improves 0.356 to 0.201 ms; full 8 KiB capacity improves 68.799 to
29.843 ms, and capacity capture 53.291 to 23.112 ms. Eight deliberate broken bitmap comparisons
are detected in addition to the generic geometry-comparison control, 29 source mutations,
phase/paint, ownership, wrap, exact capacity and overflow checks. Synthetic maxima still exceed
10 ms and cannot establish an installable synchronous hook.

Current canonical optimized results: loading_fast_job_checks.json, loading_fast_quick/ and
loading_fast_summary.json. The earlier loading_prep1/6.json retain the unoptimized baseline.

```bash
python -m nexclash.inferno --actor-job-checks --json work/loading_fast_job_checks.json
python -m nexclash.inferno --loading-prep-all ../specnext/reference/inferno --quick 2000 --out work/loading_fast_quick --json work/loading_fast_summary.json
```

The existing visible-content/culling census counters are separate from loading-cache misses;
actual unexpected cold content is counted by actor content cache misses (model).

## Optimized six-level result

All six own original 2000-frame correctness replays PASS: 12000 frames, 624 prepared candidate
images across separate level caches, 13194 exact live validations/cache reuses, 11948096 retained
actor pixels, 16903 capture comparisons and 1850 post-copy hooks. No sampled unexpected cold
actor content. Synthetic source/bitmap negative controls, high-DMA controls, sampled shop units,
bundled assembly and doccheck pass. These are host loading/cache experiments with assembled workers;
no runtime loading UI, safe pause boundary, dispatcher/cache allocator or sprite NEX is installed.

| Level | Prepared candidates | Packed source/canvas bytes | Loading CPU subtotal, seconds | Warm capture/scenery/validation max, ms |
|---|---:|---:|---:|---:|
| 1 | 103 | 86299 | 4.741 | 18.194 |
| 2 | 109 | 57129 | 3.161 | 14.877 |
| 3 | 88 | 52370 | 2.752 | 11.517 |
| 4 | 122 | 77545 | 4.134 | 16.466 |
| 5 | 84 | 54795 | 3.029 | 10.566 |
| 6 | 118 | 110875 | 6.263 | 14.674 |

Every runtime timing gate still FAILS 10 ms TOTAL. Loading figures exclude scan, zeroing, copies,
allocation/dispatch, wrappers and hardware waits. Runtime figures exclude lookup/allocation,
uploads, queue and wrappers. They are CPU models, not hardware elapsed times. No all-game catalogue
or full-recording coverage is implied by 2000-frame samples.
