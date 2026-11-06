# Inferno immutable live-source jobs — 2026-11-07

Stage 2 remains incomplete. No sprite NEX is ready. The new page-78 worker and page-75
pinned-source consumer are assembled standalone components, exercised against original live
replay events. They are not installed hooks, a runtime cache, a scheduler or hardware proof.
The host still chooses cache entries; runtime lookup/allocation costs are excluded.

## Owned source contract

Page 122 holds one bounded 8 KiB immutable source stream. It contains the original image
header, each ordered width/dx/dy run, and each tile ID followed by its eight live bitmap bytes
and live attribute, ending with the original zero-width terminator. No pointer or hash stands
in for source bytes. C1FF's second pointer byte wraps to C100, as in the original game.
Draw coordinates/IX/ordinal remain per-draw state in the existing capture log; they are not
persistent image keys. Run offsets, order and tile bytes remain in the pinned stream.

The page-78 entry is 0000; caller fields begin at 1E80: OP, IMAGE, FLASH and a two-byte PAINT
generation. ACTIVE/DONE/ERROR/MATCH follow at 1E85..1E88, two-byte SIZE at 1E89, retained phase
and generation at 1E8B..1E8D. OP=0 captures only into an unowned slot; OP=1 releases ownership;
OP=2 compares current live content against the pinned stream. A completed capture sets private
DONE only after the valid terminator. It never sets frame readiness. Invalid RAM pointers,
record wrap, width >128, unterminated rows and stream overflow cannot publish partial data.
A busy capture request preserves the existing pinned slot. Consumers must cease using it before
release; no allocator or simultaneous canvas ownership is implied.

Validation compares every serialized byte, exact length, FLASH phase and paint generation.
Different image indices/pointers may reuse a snapshot only when their complete contents match.
Same-address mutations miss. Validation and rejection cannot write pinned bytes. A caller must
handle a mismatch as a cache miss, retain the old complete display, and construct a new owned job.
Generation is a lifetime token, not a content hash: a future recolour owner must invalidate jobs
before generation wrap/reuse and maintain a stable paint table while a job owns it. No such
recolour integration is installed.

The worker runs synchronously under DI/28 MHz, restores slot 1 to 68 and its entry SP, and
may destroy main registers. Original source mappings remain visible. It is deliberately not
resumed across changing original RAM. A future installed wrapper must establish safe entry,
preserve original main/alternate registers, caller speed/R, IFF and mappings, apply ORIGINAL
pace contracts, and charge its complete cost. A long standalone DI call is not a safe hook.

Page 75 adds P_SOURCE at 1EDB: 0 reads original live graphics; 1 reads nine owned raw bytes at
1EC0..1EC8. Both sources use the same checked colour/FLASH lookup and canvas bounds. The harness
marshals copied tiles from page 122 into those parameters; an assembled stream dispatcher remains
open. Pinned-mode execution rejects any original graphics read. B filling then owns only its
private canvas and masks across service calls; source mutation cannot change an in-flight image.

## Correctness and cost

Units cover exact ordered geometry/bitmap/attribute capture, subsequent original-source mutation,
pinned/bad-operation refusal, 29 live content mutations, FLASH/paint changes, relocated identical
contents, wrapped C100 lookup, release/recapture, malformed/unterminated/wrapped records, invalid
phase/inactive validation, exact 8192-byte capacity and unpublished overflow. Removing the actual
assembled byte comparison is an informative negative control using the broken worker's own
pinned bytes. All 512 attribute/phase cases also compare pinned and original-source tile decoding.

Synthetic source capture reaches 53.291 ms at 8 KiB; full exact validation reaches 68.799 ms.
The small three-tile test's exact comparison is 0.356 ms. These are added CPU costs at 28 MHz
with the existing one-read-cycle allowance, not hardware timing. They exclude external wrappers.
Even the source component alone can exceed the **10 ms TOTAL per original update** budget.
Do not install the synchronous walker as a game hook. Exact checks need a substantially cheaper
representation/loop and/or proved deduplication within a stable lifetime; preparation needs a safe
live-data hook and an available budget. Recorded-frame lead proves neither.

Six original 2,000-frame correctness replays PASS: 128 assembled live captures, 13,066 assembled
exact validations, 1,319 pinned-source tile conversions and 128 complete B fills / 108,288 actor
pixels, retaining 16,903 capture comparisons and 1,850 post-copy hooks / 68,198,400 scenery pixels.
The host cache selects candidate entries; these are component executions, not installed runtime
cache hits. Original RAM/register/IRQ and targeted level-4 shop checks remain passing.

| Level | Captures / validations | Cold capture/scenery/snapshot/colour/B, ms | Snapshot/validation worst update alone, ms |
|---|---:|---:|---:|
| 1 | 13 / 2203 | 899.447 | 24.650 |
| 2 | 25 / 1843 | 83.383 | 12.696 |
| 3 | 21 / 2523 | 134.508 | 9.452 |
| 4 | 34 / 3721 | 397.165 | 17.243 |
| 5 | 10 / 529 | 77.024 | 7.950 |
| 6 | 25 / 2247 | 84.289 | 12.028 |

All six total timing gates FAIL. The cold totals exclude cache lookup/allocation, uploads, queue
and external wrappers. Snapshot/validation maxima are independent updates, so do not add them to
the cold-column maximum again. Largest sampled source is 1121 bytes; one sampled source call
costs up to 9.492 ms. Existing capture/scenery can take 8.715 ms and queue about 0.55 ms, leaving
about 0.735 ms before any actor work; the measured validator cannot fit that conservative sum.
Pinned colour decoding is slightly cheaper than original-source decoding, hence the older cold
subtotal changes slightly even before adding snapshot costs. This does not fix cold B latency.

Bundled assembly (17 blocks / 100 exported symbols), shared tools, Chuckie Egg canary and
sampled level-4 shop units PASS. Software checks are separate from absent hardware proof.

## Blitter and ordinary DMA evaluation

The new span probes execute the existing assembled page-77 adapter and strict shared DMA model.
They copy **prepared buffers**, not original live geometry. Policies 0/1/2, capability/ownership/
hardware-IM2 fallback, source/destination bounds, current AND pending pattern protection and the
wrong-stride/pending-overwrite controls remain covered. There are 27 new single-span proxy cases:
1, 8, 9, 16, 31, 32, 63, 64 and 256 bytes, each under all three policies.

Before the new fast path, DDMA CPU setup was 0.104 ms for one 8-byte prepared span versus
0.082 ms for the CPU path, excluding physical transfer stalls. Snapshot bitmaps are eight bytes;
attributes are separate one-byte reads, with data-dependent source addresses. Many small DMA
programs would regress setup and would still need ordered CPU parsing/comparison. The adapter
now routes single spans below 64 bytes directly to CPU, before DMA capability/setup work.
An 8-byte span takes 0.071 ms under every policy in this standalone adapter; 16 bytes take
0.078 ms. This is a prepared-copy primitive measurement, not the cost of capturing a live tile.

For a single 64-byte span, CPU is 0.134 ms and DDMA setup 0.107 ms; 256 bytes are 0.298 / 0.107 ms.
Transfer stalls are UNKNOWN, so those differences are available headroom, not elapsed-time wins.
Larger rectangles still prefer gated DDMA, and protected 256-byte sprite pairs retain ordinary
DMA / CPU fallback and no-blitter policy 1. Snapshot capture itself uses CPU; no adapter source
range was widened to authorize reading arbitrary original RAM.

DDMA 2D copying can help prepared canvas/cache staging. Constant fill could help canvas/mask
initialization, but needs a separately gated shared implementation, model, ownership and timing
checks; it cannot compute bitmap colour expansion, exact byte equality or whole-image exterior
connectivity. Transparent-byte skip preserves destination bytes and is not overwrite composition
or B classification. The documented WR3 mask/match bytes are ignored; DMA search cannot replace
this exact-content validator. No original IRQ masks are altered and no active DMA owner is assumed.

Primary facts and licence boundary: nexclash docs/DDMA.md and DDMA_IMPLEMENTATION.md;
specnext docs/reference/zxnDDMA_guide.txt and docs/dma_backend_validation.md. No guide code copied.

## Reproduce

From nexclash, bundled assembler only:

```bash
python tools/asm2profile.py --check inferno
python -m nexclash.inferno --actor-job-checks --json work/actor_job_checks.json
python -m nexclash.inferno --actor-pack-checks --json work/actor_job_pack_checks.json
python -m nexclash.inferno --actor-fill-checks --json work/actor_job_fill_checks.json
python -m nexclash.inferno --actor-blit-checks --json work/actor_job_blit_checks.json
python -m nexclash.inferno --actor-pack-check ../specnext/reference/inferno/Inferno6.rzx --quick 2000
python -m nexclash.inferno --actor-pack-all ../specnext/reference/inferno --quick 2000 --out work/actor_job_quick --json work/actor_job_summary.json
python -m nexclash.inferno --modal-checks ../specnext/reference/inferno/build/modal4_entry.json --json work/actor_job_modal_checks.json
python selftest.py --tools
python selftest.py --canary
python tools/doccheck.py
```

Runtime cache/allocator, safe early hook/scheduling, assembled stream dispatch, pattern layout,
protected integrated uploads and complete-frame switching remain open. Sprite display stays disabled.
FLASH synchronization, other modal paths, continuous BASIC/Na/Nb/game/ending, startup/ROM-reader
lifetime, recolouring/sheets and complete software/hardware timing remain obligations.
