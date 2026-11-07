# Inferno actor colour packing and cache census — 2026-11-05

Stage 2 remains incomplete. No sprite NEX is ready. This adds an assembled colour-expansion
primitive and measures it on original actor source data; it does not install a sprite compiler,
cache, culling hook or pattern uploader. The approved whole-image B silhouette is unchanged.

## Implemented primitive

`pack_actor_tile` is 233 bytes at offset 0 in proposed private worker page 75. It expands one
original 8×8 bitmap/attribute tile into 32 packed four-bit bytes. Pages 96..111 contain a generic
128 KiB table: 128 colour pairs × 256 possible row bytes × four output bytes. These are colour
conversion data, not a replay-derived graphics catalogue. Pages 112..115 provide a 32 KiB packed
canvas, enough for 65,536 pixels. User authorization covers these expanded-memory pages.

Each tile reads the current original bytes at DC00/FC00. FLASH is an explicit phase input;
actual ULA clock synchronization is still open. Palette indices match the existing B model:
zero initially means black, 2..8 normal nonblack colours, 9..15 bright nonblack colours. This
primitive does not distinguish exterior black from enclosed black. That classification must
still run over the complete actor before clipping; filling individual tiles would change B.

The worker runs under DI at 28 MHz. It validates the ten-bit tile ID, phase, four-byte-aligned
canvas position and stride (4..512 packed bytes), and the final row before writing. It maps
lookup RAM into slot 2 and canvas RAM into slot 1, restoring original page 10 and capture page 68
before return. The verifier rejects original game RAM, lookup, capture, code and unowned writes.
No boot code currently loads the table or calls this worker from the post-copy hook.

## Checks

- 512 assembled attribute/FLASH cases, including both black brightnesses and page-crossing rows.
- All 32,768 table entries independently compared with the original Spectrum tile decoder.
- Four source/canvas boundary cases and ten invalid inputs rejected before canvas writes.
- Three deliberately broken workers detected: wrong table bank, omitted FLASH and wrong restore.
- A conservative wrapped-canvas visibility model checked against 4,608 explicit interval cases.
  It includes canvas gaps that B could fill; it does not cull using only source-tile coverage.
- Each replay retains the existing original RAM/register and scenery comparisons. On first use
  of an exact actor-content key, every constituent tile is run through the assembled worker and
  independently checked. This is offline execution at original draw events, not installed timing.
- The sampled level-4 shop-return check remains passing: frame 51,805, 256 bit-preservation cases,
  four missing-hide controls, and original instruction-site refusal.

## Timing interpretation

All times below are extra work per original game update, modeled at 28 MHz with the existing
one-cycle-per-read allowance. The total target is 10 ms. These are not physical hardware timings
or a claim that the original game updates at 50 fps.

A standalone tile conversion costs at most **0.164 ms**. Ten new tiles therefore cost about
**1.64 ms**, already larger than the approximately **0.73 ms** remaining after the existing
worst capture/scenery cost and largest observed sprite queue. Cache hits are modeled with zero
lookup cost here, so neither the cache-hit estimate nor the cold path establishes a timing pass.
Whole-image fill, cache validation, cache placement, pattern upload and queue time are excluded
from the replay totals. Each level begins with an empty content cache; keys compare complete
ordered tile IDs, signed coordinates and live source bytes, not pointers or hashes alone.

Conservative culling estimates reject only a canvas entirely outside the wrapped viewport. The
model checks every rejected actor has no visible B patterns. Its timing column excludes the
cost of a future runtime bounds check. It is a scheduling estimate, not an implemented speedup.

## Six-level results

All six original 2,000-frame replays pass: 12,000 frames, 16,903 capture comparisons,
1,850 post-copy checks and 1,319 assembled tile conversions. Exact-content cache estimates
count 13,066 hits / 128 misses across 13,194 actor draws. The per-level caches reset; the
73,929-byte total is a sum, not a simultaneously resident requirement. The largest individual
estimate is 24,211 bytes, excluding allocator/index overhead and hardware pattern slots.

| Level | Model hits / misses | Estimated cache bytes | Cold capture + scenery + packing, ms | With modeled bounds cull, ms |
|---|---:|---:|---:|---:|
| 1 | 2203 / 13 | 24211 | 46.478 | 46.478 |
| 2 | 1843 / 25 | 10838 | 11.755 | 11.755 |
| 3 | 2523 / 21 | 8715 | 12.841 | 12.841 |
| 4 | 3721 / 34 | 15742 | 27.007 | 27.007 |
| 5 | 529 / 10 | 5163 | 10.680 | 10.680 |
| 6 | 2247 / 25 | 9260 | 11.881 | 11.881 |

The model culls 932 wholly offscreen actor calls, but does not lower any level's worst cold
update. Large visible image construction still must be addressed. All costs exclude the
remaining work listed above; **the 10 ms total timing gate fails**.

## Architecture consequence

Expanded RAM can hold decoded actor images cheaply compared with recomputing them on every
appearance, but it cannot eliminate first-use CPU cost or enlarge the hardware sprite store.
The next implementation must establish safe early construction/prewarming from original live
image data, or reduce the construction path enough to fit. Do not use the sampled recordings as
a complete asset catalogue, accept pointer-only cache hits, or mark a partially built image ready.
Eviction must protect the current and pending display's pattern slots. Implement whole-image B
fill and exact live-content validation before connecting the existing Copper readiness flag.

The larger level-1 and level-4 actors make this an integration constraint, not just a level-6
micro-optimization. Original source mutation, remaining modal paths, continuous loads, palette
recolouring and full hardware timing remain open.

## Reproduce

From nexclash on codex/inferno, with the bundled pinned assembler:

```bash
python tools/asm2profile.py --check inferno
python -m nexclash.inferno --actor-pack-checks --json work/actor_pack_checks.json
python -m nexclash.inferno --actor-pack-check ../specnext/reference/inferno/Inferno6.rzx --quick 2000 --json work/actor_pack6.json
python -m nexclash.inferno --actor-pack-all ../specnext/reference/inferno --quick 2000 --out work/actor_pack_quick --json work/actor_pack_summary.json
python -m nexclash.inferno --modal-checks ../specnext/reference/inferno/build/modal4_entry.json
```

Platform choices build on [timing_architecture.md](timing_architecture.md) and
[frame_pipeline.md](frame_pipeline.md). Primary references: [Next memory map](https://wiki.specnext.dev/Memory_map)
and [extended Z80 instructions](https://wiki.specnext.dev/Extended_Z80_instruction_set).
This uses indexed lookup, ordinary LDI and NextReg paging; DMA cannot perform the monochrome-to-
colour conversion or the B interior classification.
