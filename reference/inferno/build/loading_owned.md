# Initialization pause and owned high-RAM cache — 2026-11-07

Latest runtime evidence: [runtime_profile.md](runtime_profile.md): per-update component totals
and row-bounded exact validation. Every byte is still compared; connected loading driver and
full runtime timing remain open. Earlier measurements below are historical checkpoints.

Stage 2 remains incomplete. No sprite NEX is built or enabled. The new assembled components
are exercised differentially and through original replay states; the live-table scan, content
selection, duplicate-index resolution and worker orchestration still run on the host. The pause
gate is not yet connected to a runtime loading driver/UI or the full display pipeline.

## Loading boundary

Do **not** hook 86C5. The level-6 census reaches it 10,729 times during frames 360–369; it is
inside decompression and its bytes change before gameplay. The old frame-368 candidate census
was source-availability evidence only. `loading_boundary_points.json` preserves this rejection.

Use the checked original instruction at **8EF9**, `LD (9198),A` (`32 98 91`), immediately after
8EF8's original DI and before the game's stack/vector/IM2 initialization. The six original
replays reach this boundary in DI/IM1, at frames 681, 438, 475, 430, 466 and 452 respectively.
Loading preparation now freezes the live tables there, rather than at the first actor tick.
Failure to observe the boundary before gameplay fails explicitly; there is no first-draw fallback.

The 105-byte alt-ROM gate at 3C40 maps private page 68 before saving SP and all main/alternate
registers/IX/IY on a private stack. No push or CALL touches the original stack. It latches the
caller clock with the shared speed macros, calls a private service, restores that clock and R,
then restores registers/SP/mapping and executes the displaced instruction. R restoration is
independent of worker duration and retains bit 7. I, IM and IFF remain unchanged; interrupts
remain disabled throughout this initialization pause. ORIGINAL gameplay pacing is not changed
by a release here: this is an approved loading pause, and no runtime renderer is enabled.

Each captured level entry passes 24 all-register/R/RAM/stack/IFF/caller-speed cases (all four
clocks and six R edges), two different worker durations and a missing-R negative control.
The service used for these wrapper checks is a clobbering private test routine, not the loading
scanner or cache driver. Source construction/store/dispatch are executed separately below.
This proves the gate's return contract in the sampled domain, not all possible entries or ROM
reader lifetime, physical IRQ timing, UI behavior or a connected multi-second loading driver.

`--initialization-tests` also extends the existing crafted 7131 bank-loader versus original-ROM
comparison through Nb to its A2FF input routine for tape ordinals 0–5. Ordinal 6 is the ending.
Four transfers per prefix retain register/live-RAM/I/O equality, tracked dead-stack reads and
explicit equal R inputs. Level ordinal 4 needs 150 common logical HALT wake-ups. These are
logical common interrupts, not wall-clock IRQ scheduling. Prefixes still start from the level-1
state and stop before interactive initialization/gameplay; continuous BASIC/level/ending flow
and persistent player state are not proved by either this test or the independent RZX segments.

## Owned store and dispatch

Page 79 now owns a 483-byte assembled worker and 256 sixteen-byte metadata records. Physical
pages **136–215** form a 655,360-byte append-only store. DDMA staging **216–223** is untouched.
An insertion copies a completed source stream from page 122 and a completed B canvas from pages
112–115. Source streams are aligned only when needed to fit within one mapped page; canvases
cross pages. Full bounds/capacity checks happen before payload writes. Payload copies and all
metadata finish before the single valid-byte publication. Failure never publishes a partial entry.

Entries are immutable until level reset; insertion cannot overwrite an existing slot. Reset is
refused if either supplied current or pending ownership is nonzero. These are component guards:
the caller must still connect actual frame ownership and cancel/drain it before a level reset.
There is no eviction, hardware pattern allocation or frame readiness publication here.

Assembled dispatch checks validity, FLASH phase and the full paint generation. **It returns a
candidate only.** The source worker then walks current original geometry, IDs, bitmap and attribute
bytes in order and compares them directly against the high-RAM source page at its stored offset.
No source copy back to page 122, hash acceptance, pointer-only key or lifetime deduplication is
used. Canvas bytes retained in high RAM are checked against original-source whole-image B pixels
at every sampled draw. Actual draw ordinal, original actor order/priority and original RAM remain
unchanged. The host still selects the content-equivalent metadata slot, including duplicate indices;
this must become assembled runtime selection with a bounded unseen/mutated-content fallback.

The inline exact-hit walker avoids generic capture dispatch for serialized byte comparisons.
Small exact hit improves from 0.200750 to 0.165786 ms; the exact 8 KiB capacity case improves from
29.843250 to 24.696929 ms and still exceeds 10 ms. Capture remains approximately 23.113 ms at
capacity. All geometry/bitmap/attribute mutations, eight broken bitmap controls, phase/paint,
pinning, wrap, capacity and overflow cases remain checked. Direct high-RAM tests additionally
cover nonzero offsets and live-source mutations. Dispatch alone is 0.021393 ms per candidate.

Owned-store units cover page crossings/full 32 KiB canvas, exact final-byte capacity, overflow
without writes/publication, source alignment, immutable overwrite refusal, both ownership reset
guards, phase/paint rejection, scratch mutation and missing publication. Cache code cannot map
staging pages or write original RAM/source/code. New loading copies use CPU; existing gated
DMA/DDMA/no-blitter/CPU transfer paths are unchanged and their component controls pass.

## Six own-original quick replays

Every 2,000-frame replay passes original state/frame/IRQ/negative checks. All 13,194 sampled draws
reuse completed owned contents and validate current source bytes exactly. There are 622 prepared
candidates across six separate level caches; no sampled unexpected cold content. Initial live data
now yields 101 candidates in L1 (the historical first-draw freeze yielded 103); these are not asset
catalogues or claims about unseen game paths. Whole-frame readiness remains closed.

| Level | Boundary frame | Prepared | Construction CPU, s | Store CPU, s | Warm added subtotal, ms |
|---|---:|---:|---:|---:|---:|
| 1 | 681 | 101 | 4.372 | 0.295 | 16.317 |
| 2 | 438 | 109 | 3.162 | 0.212 | 14.031 |
| 3 | 475 | 88 | 2.752 | 0.192 | 10.995 |
| 4 | 430 | 122 | 4.065 | 0.280 | 15.391 |
| 5 | 466 | 84 | 3.029 | 0.199 | 10.167 |
| 6 | 452 | 118 | 6.263 | 0.421 | 13.875 |

All six runtime gates **FAIL 10 ms TOTAL**. Warm totals include capture, scenery, exact source
validation and assembled candidate dispatch. They exclude runtime scan/content selection,
external wrappers, uploads, queue and physical waits. Construction/store columns exclude host
scan, zeroing, orchestration and hardware waits. They are assembled CPU models, not elapsed Next
measurements or promises about loading duration. The earlier six-level warm range was
10.566–18.194 ms; the new range is 10.167–16.317 ms despite including candidate dispatch.

## Reproduce and continue

From nexclash on `codex/inferno` with the bundled assembler:

```bash
python tools/asm2profile.py --check inferno
python -m nexclash.inferno --loading-pause-checks --json work/loading_pause_checks.json
python -m nexclash.inferno --owned-cache-checks --json work/owned_cache_checks.json
python -m nexclash.inferno --actor-job-checks --json work/owned_job_checks.json
python -m nexclash.inferno --initialization-tests ../specnext/reference/inferno --json work/loading_nb_prefix.json
python -m nexclash.inferno --loading-prep-all ../specnext/reference/inferno --quick 2000 --out work/owned_quick --json work/owned_summary.json
python -m nexclash.inferno --actor-blit-checks --json work/owned_blit_checks.json
python -m nexclash.inferno --modal-checks ../specnext/reference/inferno/build/modal4_entry.json --json work/owned_modal_checks.json
python tools/doccheck.py
```

Next: connect runtime live-table enumeration, duplicate-index/content selection and bounded cold
fallback to the pause gate and private workers; build initial complete patterns/frame before reveal.
Keep current/pending resources protected, retain original state/priority and transfer fallbacks,
reduce the remaining runtime subtotal and measure whole hooks. FLASH/modal/continuous frontend,
original ROM lifetime, recolouring and physical timing remain open. Keep sprites disabled.
