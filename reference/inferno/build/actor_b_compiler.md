# Inferno whole-image B construction and prepared transfers — 2026-11-06

Stage 2 remains **incomplete**. No sprite NEX is ready. These are assembled components with
software checks; the runtime actor cache, early-preparation hook/scheduler, actor-to-pattern
layout/allocator and complete-frame integration are not installed. Sprite display stays disabled.

## Whole-image construction

The existing page-75 colour decoder now composes successive tiles into one owned, zeroed canvas
in pages 112–115, retaining original tile overwrite order. A separate page-76 worker classifies
the complete image **before clipping**. It builds one passable bit per black pixel in page 116,
then floods the exterior in page 117. A generic 64 KiB horizontal-connectivity lookup in pages
128–135 spreads each seed across its eight-pixel byte. Forward/backward sweeps converge to the
four-connected boundary component. A final pass changes enclosed black to palette index 1 and
leaves exterior black transparent. No outline or per-tile filling is introduced.

Page 76 also holds 256 zero-pixel flags and a 1,024-byte final-colouring lookup. These and the
connectivity table are generic conversion data, not recording-derived graphics. Code/table data
must be loaded by a future bootstrap. Pages 118–121 are proposed prepared-transfer staging;
pages 136–223 remain available for caches. None of this enlarges hardware sprite pattern RAM.

The service entry is 0400. Caller-owned fields start at 1E90: packed stride, size, private DONE,
ERROR and work state; COMMAND/BUDGET/ACTIVE are at 1EA0/1EA1/1EA3. Start a new zeroed/composed
canvas with COMMAND=0, ACTIVE=DONE=0; resume only that same owned job with COMMAND=1. Budget is
1–16 work units; checks use four. The worker retains its coroutine stack/registers on page 76,
restores slots 1/2/3 to 68/10/11 at every yield/return, and runs only under DI/28 MHz. Main
registers may be destroyed between calls. DONE becomes one only after final colouring finishes;
it is **not** the frame queue's readiness flag. A real wrapper and job cancellation/lifetime
integration are still required. Never reuse this canvas while a job owns it.

Both masks start dirty in the harness and are initialized by assembly. Input dimensions and
quota are checked; rejected geometry cannot write canvas/mask bytes. The source canvas is tight
row-major, stride 4–512 packed bytes, multiple of four, size at most 32 KiB. Unsupported capacity
must fail closed. Original RAM, immutable lookups and hardware patterns cannot be written here.

Checks: 65,536 independently traversed horizontal-connectivity entries; 29 assembled canvases
including open/closed tile seams, randomized colours, full 65,536-pixel capacity and a winding
exterior requiring nine sweep pairs; seven geometry/one-shot guards, three quota guards, three
inactive/invalid resume guards, four quota/register-clobber cases and four broken workers.
The largest measured four-unit call is 0.204 ms across units and replays. External wrapper,
scheduling, real interrupt delivery and physical memory waits remain outside that measurement.
The largest synthetic whole construction still costs 1,985.53 ms across many service calls.
Quotas bound each call; they do not eliminate total construction cost or prove responsiveness.

## New blitter functions factored into the transfer path

The shared DMA/library dependencies come from nexclash PR #93, head 449682f, now incorporated
through remote Inferno commit 6aa2992 (main 3efa10f). The only assembly
library change adds symbolic names to existing packet dimension words, without changing their
bytes. The Inferno adapter in writable page 77 reuses `hlib_dma_init`, `hlib_dma_backend`, the
rectangle/row command packets and `hlib_dma_sprite`; it does not replace the shared device model
with a permissive per-engine DMA imitation. The shared selfchecks are included in `selftest --tools`.
The upstream shared/observational selfchecks are retained after resolving the concurrent main
refresh; their synthetic tests do not require another game's recording or change its output.
The shared immutable-image pattern cache is a selfcheck dependency only; Inferno does not use it
to validate live graphics. Its immutable-key contract cannot replace exact live-content checks.
Page 77 owns its packet state exclusively; do not mix the fixed Rainbow rectangle entry with
the Inferno adapter after changing that private copy's geometry.

OP=0 copies prepared rectangles, width 1–256, height 1–16, within independently bounded 8 KiB
pages. Sources are owned canvas/cache pages 112–115 or 136–223; destinations are private canvas
112–115 or staging 118–121. Equal source/destination pages and mask/lookup/game destinations are
rejected. DDMA uses one 2D transfer; ordinary DMA uses rows of at least 64 bytes. Narrow ordinary
DMA rows use CPU copying because setup alone was slower in these checks. OP=1 uploads one
256-byte hardware pair (two four-bit patterns) using ordinary DMA or the CPU fallback. The
current **and pending** pair bitsets at 1F00/1F08 protect both halves before slot selection or
upload. This is a transfer primitive, not an allocator; future allocation must provide correct
ownership bitsets and preserve draw priority. Upload completion never publishes attributes.

Default policy 2 prefers the blitter, policy 1 provides **no-blitter**, policy 0 is CPU-only.
The future launcher must expose/retain this choice. Capability is revoked unless ownership is
explicitly established. Core <3.00, unknown interfaces, unowned DMA and hardware IM2 fall back
to CPU; 3.00–3.02 never receive DDMA extensions. No original interrupt masks are changed. A real
integration must establish an idle, exclusively owned channel, stable mappings and bounded stall
time before enabling DMA. These components do not establish that original-game lifetime proof.

54 capability/policy/operation/width cases, nine exact page/pattern-end boundaries, 20 rejected bounds, 12 current/pending pair protections
and wrong-stride/pending-overwrite controls pass, using the compiled adapter and strict shared
functional DMA model. The test data are synthetic prepared buffers, not uploaded actor frames.

| Operation | CPU added time | DMA/blitter CPU setup | Transfer time |
|---|---:|---:|---|
| 8 bytes × 16 rows, strided rectangle | 0.338 ms | DDMA 0.148 ms | unknown |
| 64 bytes × 16 rows, strided rectangle | 1.106 ms | row DMA 0.511 ms; DDMA 0.148 ms | unknown |
| 256-byte sprite pair | 0.267 ms | ordinary DMA 0.068 ms | unknown |

The right columns exclude bus stalls and cannot be called elapsed-time savings or a 10 ms pass.
For example, the pair's approximately 0.199 ms CPU saving is its maximum available transfer-time
headroom in this model. Measure the complete job on the named board/core. DMA cannot replace
the bitmap-to-colour lookup or the data-dependent B flood itself. Primary protocol/reference and
backend policies: specnext `docs/reference/zxnDDMA_guide.txt`, `docs/dma_backend_validation.md`,
and nexclash `docs/DDMA_IMPLEMENTATION.md`. No guide example code is copied into the engine.

## Replay correctness and timing are separate gates

Each level uses its own original replay, 2,000 frames: 12,000 frames, 16,903 capture comparisons,
1,850 assembled post-copy hooks, 68,198,400 scenery pixels, 128 complete assembled B fills /
108,288 actor pixels and 1,319 assembled tile conversions pass. Existing IRQ/negative controls
and level-4's targeted shop-return checks still pass (256 bit cases, four missing-hide controls).
Host exact-content reuse remains 13,066 hits / 128 misses. It is **not installed runtime caching**.

All times are modeled **added work per original game update**, target **10 ms total**, at 28 MHz
with the existing one-cycle-per-CPU-read allowance. The cold column includes all service calls
needed to finish misses in that update, not a claim that the future scheduler executes them all.
It excludes runtime validation/allocation, uploads, queue and the external service wrapper.

| Level | Complete B fills | Earliest sampled first-use lead, recorded frames | Cold capture/scenery/colour/fill, ms |
|---|---:|---:|---:|
| 1 | 13 | 86 | 882.151 |
| 2 | 25 | 85 | 70.787 |
| 3 | 21 | 85 | 131.485 |
| 4 | 34 | 86 | 387.688 |
| 5 | 10 | 86 | 74.742 |
| 6 | 25 | 85 | 77.563 |

**All six cold total timing gates FAIL.** The older 46.48/11.88 ms figures excluded filling;
they are not equivalent workloads. No hardware timing or complete-frame software proof exists.
Capture/scenery up to 8.715 ms + observed queue about 0.55 ms + one fill service about 0.204 ms
already leaves only about 0.53 ms for runtime validation/uploads/wrappers in that conservative
component sum. It is not a measured complete update, and broader FLASH/capacity cases still fail.

## Early construction investigation

At the first original instruction of each recorded frame, a **host census** tries every C100
index, including odd indices and the wrapped second pointer byte. It rejects malformed or
oversize candidates, recording complete ordered geometry, IDs and live bitmap/attribute bytes.
All 128 later first-use keys were already present 85–86 or more recorded frames before use.
The maximum candidate set is 124 and serialized source estimate 28,935 bytes, excluding canvases,
allocator and indexing. Some speculative candidates may never be drawn. Neither these candidates
nor recording assets are a complete game catalogue. Invalid candidates never authorize omitting
a future real draw. Earliest sampled PCs 86C1–86CC identify frame-boundary samples, **not proven
preparation hook sites**. Independent level recordings do not prove continuous-load readiness.

This supports early live-data preparation but does not prove a schedule. Recorded-frame lead
cannot be converted into available CPU milliseconds or game-update counts. Level 1's first
visible batch alone still needs substantial work. A safe implementation must snapshot complete
ordered source bytes/geometry into a pinned job, construct from that snapshot, revalidate exact
live content (including relevant FLASH and paint generation) before accepting a hit, and protect
current/pending display allocations through upload/acknowledgement. Reading changing originals
across yields under a pointer-only key is unsafe. Handle unseen/mutated inputs with bounded jobs
and retained complete display state; never mark partial work ready. The cache and preparation
scheduler are the next architectural work, not optimizations claimed by this census.

## Reproduce

From nexclash on codex/inferno, using only the bundled assembler:

```bash
python tools/asm2profile.py --check inferno
python -m nexclash.inferno --actor-pack-checks
python -m nexclash.inferno --actor-fill-checks
python -m nexclash.inferno --actor-blit-checks
python -m nexclash.inferno --actor-pack-check ../specnext/reference/inferno/Inferno6.rzx --quick 2000
python -m nexclash.inferno --actor-pack-all ../specnext/reference/inferno --quick 2000 --out work/actor_b_quick
python -m nexclash.inferno --modal-checks ../specnext/reference/inferno/build/modal4_entry.json
python selftest.py --tools
python selftest.py --canary
python tools/doccheck.py
```

Canonical evidence: `actor_b_fill_checks.json`, `actor_b_pack_checks.json`, `actor_blit_checks.json`,
`actor_b_summary.json`, `actor_b_quick/actor_pack1..6.json`, `actor_b_modal_checks.json`.
FLASH synchronization, remaining modal paths, continuous BASIC/Na/Nb/game/ending, startup/ROM-reader
lifetime, recolouring/sheets and complete timing validation remain open. No NEX is changed.
