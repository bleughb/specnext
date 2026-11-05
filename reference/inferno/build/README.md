# Inferno stage-2 build evidence (2026-11-05)

Stage 2 is INCOMPLETE. No sprite engine or sprite NEX exists. The diagnostic NEX is not a
hardware candidate: full tail lifetime, continuous gameplay and timing remain unproved.
The approved visual design in ../design/ is unchanged.

Latest checkpoint: [frame_pipeline.md](frame_pipeline.md) documents the checked post-copy
hook, palette/clip setup, Copper queue and level-4 shop-return cancellation. Six 2,000-frame
replays pass, including original RAM/register preservation. Capture + frame preparation costs
up to **8.715 ms per game update**, plus about **0.55 ms** for the observed 58-sprite queue.
Sprite construction/uploads are still missing; no complete-render timing PASS or sprite NEX.
This supersedes the earlier “no frame hook/setup” status and FLASH pair-swapping description.

## Current architecture experiment

See [timing_architecture.md](timing_architecture.md) for the evaluated Z80/Z80N, DMA,
tilemap and expanded-memory choices. The new assembled 1-bit textmap worker reduces level-6
worst scenery overhead from **130.069 ms to 6.547 ms per game update**. Capture plus scenery
costs **8.708 ms**, leaving **1.292 ms** of the 10 ms total target for sprites/wrappers/commit.
These are modeled assembly timings, not physical-Next measurements; the TOTAL gate is unproved.

All six original quick replays pass: 12,000 frames, 1,855 scenery images / 68,382,720 pixels,
16,903 capture comparisons. Units cover both buffers, all attribute/FLASH pairs, source overflow,
live mutation and negative controls. Shop census exposes the need for a separate modal hook.
The worker is experimental and enables no display registers; **no sprite NEX is ready**.

```bash
python -m nexclash.inferno --textmap-units ../specnext/reference/inferno --json work/textmap_units.json
python -m nexclash.inferno --textmap-check ../specnext/reference/inferno/Inferno6.rzx --quick 2000 --json work/textmap6_quick.json
# At an integration milestone:
python -m nexclash.inferno --textmap-all ../specnext/reference/inferno --quick 2000 --out work/textmap_quick --json work/textmap_summary.json
python tools/probes/rzx_census.py ../specnext/reference/inferno/Inferno4.rzx --pc 0x8F7C,0x8F92,0x9790 --stop 52500 --sample-frames 52229 --memory 0x4000:0xC000 --json > work/textmap_shop_census.json
python tools/probes/rzx_census.py ../specnext/reference/inferno/Inferno4.rzx --pc 0xFFFF,0xFFF4,0x998B,0x0038 --stop 52231 --sample-frames 52229 --memory 0x4000:0xC000 --json > work/textmap_shop_state.json
```

From nexclash on codex/inferno (SkoolKit 10.1, bundled pinned sjasmplus):

```bash
pip install -r requirements.txt --break-system-packages
python tools/asm2profile.py --check inferno
python -m nexclash.inferno --loader-tests ../specnext/reference/inferno/Inferno.tzx --json work/loader_checks.json
python -m nexclash.inferno --continuation-tests ../specnext/reference/inferno --json work/continuation_checks.json
python -m nexclash.inferno --bootstrap ../specnext/reference/inferno/Inferno.tzx --out work/inferno --json work/bootstrap_checks.json
python nexclash.py scan work/inferno/Inferno_bootstrap.z80 --frames 2000 --range 0x5D30-0x5E6F
```

- loader_checks.json: original-ROM byte decoder versus assembled bank loader. All 32 raw blocks
  in load/verify modes, capacities, flag/parity/verify failure, EOF, address wrap and ROM semantics.
  Two deliberately broken assembled builds detected. Every instruction audited for slot-0/IFF;
  no tape payload writes. Physical pulse acquisition is replaced by canonical completed bytes
  in BOTH machines. This is not a physical-tape comparison or timing measurement.
- continuation_checks.json: seven crafted calls to original 7131 from the supplied level-1
  snapshot, each ending at 718C before CALL 44000. Na is loaded/executed; Nb is loaded but NOT
  executed. No target-level snapshot restore. Four ROM transfers per case, identical registers,
  live RAM and original I/O. R inputs at the original beeper's 7C37 are synchronized and counted;
  13 differing dead-stack bytes are guarded against later reads. No time interrupts are modeled.
  This does NOT prove actual level completion, score/health/equipment retention across gameplay,
  Nb initialization, modal screens, all-level startup, ending or rewind/restart behavior.
- Inferno_bootstrap.z80: original TZX/BASIC run to its first USR 24200, before compressed main runs.
  This is not a synthesized or independently restored level-start state.
- Inferno_loader_diagnostic.nex: that bootstrap plus bank loader, full original alt-ROM images,
  all 32 raw tape blocks unchanged in pages 32-55, cursor state page 68. No display hooks/layers.
- bootstrap_checks.json: NEX boot preserves registers/RAM/ROM with NEXLOAD printer-buffer damage
  and both normal and deliberately foreign system ROM3. Tail 5D30-5D65.
- bootstrap_scan.txt: original initial 2,000-frame scan leaves 5D30-5E59 untouched. This limited
  scan does not establish later tail lifetime. Do not distribute the diagnostic as a release.
- manifest.json: artifact lengths and MD5s, not a verification stamp.

Next: pulse-level loader contract and real continuous startup/Na+Nb/game/ending continuation;
then complete original-memory-preserving sprite/Layer 2 hooks, modal transitions, instruction
interrupt safety, resource bounds, measured timing, colour maps/sheets and quick RZX verification.
Read nexclash/games/inferno.md for the exact current design, evidence and next-session prompt.

## Capture kernel checkpoint (2026-11-05)

The current decoder corrects canonical C to 7E using unmodified-ROM/TZX pulse tests. The loader
NEX above is regenerated; use manifest.json for its current checksum. The capture NEX is a
separate level-1 snapshot diagnostic, not a continuous release. Neither enables replacement layers.

```bash
python -m nexclash.inferno --pulse-tests ../specnext/reference/inferno/Inferno.tzx --json work/pulse_checks.json
python -m nexclash.inferno --pulse-continuation ../specnext/reference/inferno --json work/pulse_continuation.json
python -m nexclash.inferno --capture-all ../specnext/reference/inferno --out work --quick 2000 --json work/capture_summary.json
python -m nexclash.inferno --render-model-units --json work/render_model_units.json
python -m nexclash.inferno --capture-build ../specnext/reference/inferno --out work/inferno --json work/capture_boot.json
```

- pulse_checks.json: 32 loads, 32 verifies and 3 error cases against actual TZX pulse timings,
  no fast load or pulse-loop accelerators. Strict CMP/live RAM comparison, including C and AF'.
  Reference polarity 0; short-tape timeouts/other polarities remain unproved. pulse_continuation.json
  extends every Na/Nb prefix to that oracle, matching each 731C return and final 718C handoff.
- capture_summary.json and capture1..6.json: 12,000 frames in one process, 16,903 assembled-hook
  comparisons, 13,194 whole actor draws, 1,854 tile-map checks and 1,850 complete ULA comparisons.
  Capture sites are 8F7C, 959B, 96A1, 8F92. The actor hooks replace just DD 6E 04, retaining the
  preceding LD H,C1. This preserves legitimate interrupt resumes between those instructions.
- Every capture compares all CMP registers and all game RAM with the original displaced
  instruction(s), including exact original CALL return bytes. Compiled site bytes must remain
  intact. Private stack, clean map and raw run-list log use page 68 only; loader data is retained.
  Every hook instruction checks interrupt-enabled state/mapping/clock invariants. No incomplete
  image or overflow becomes ready. Positions are capture-parameter tests, not full-plot edge proof.
- IRQ tests follow vector trampoline FFFF/FFF4 into 998B through RET. Each level has four source
  contexts and four forced stack-unwind cases using the captured tables. An earlier prototype
  stopped before the trampoline/handler; those results are superseded. No hardware IRQ timing
  or instruction-interleaving guarantee is claimed.
- Broken compiled controls remove DI, jump inside a replaced instruction, or overwrite a live
  game byte. Each is detected using its own private data. Original-image controls drop a writer
  and omit modulo-256 x: the latter fails 841 times across the six quick runs.
- render_model_units.json tests approved B's closed/open interiors, whole-image fill across a
  tile seam, content-key changes, original palette and wrap/clip. This is a software resource/mask
  model, not a runtime sprite rasterizer or recolour implementation.
- Sample maxima: 21 image calls, 58 visible chunks, 56 distinct patterns, 64 old+new pattern union.
  Dirty histograms count tile IDs, not source-byte invalidation. DC00-FFFF has 9-109 byte states
  per sampled recording; no permanent pointer-only graphics cache is justified. These are not
  full-recording maxima and do not include future painting changes.
- Capture-only cost model: max 8,342.625 equivalent 3.5MHz T/tick, <=758.375 per image, including
  one extra 28MHz cycle per modeled memory read and conservative clock transitions. Rendering,
  uploads, raster atomicity and real hardware waits/speed remain unmeasured.
- capture_pool_check.json and capture_unpooled_check.json are identical 810-frame A/B checks.
  intro_rom_scan.txt and game_rom_scan.txt: original intro and level-4 first 2,001 frames never
  touch the decoder/register block or capture ROM areas. Other/full reader coverage remains open.
- Inferno_capture_diagnostic.nex / capture_boot.json: boot checks pass with NEXLOAD printer damage
  and both original and foreign ROM3. It starts the existing level-1 snapshot with capture hooks;
  it is NOT the approved original-BASIC continuous frontend. No sprite/Layer 2 renderer is enabled.

## Assembled scenery baseline

Validation optimization follow-up (2026-11-05): current `scene_renderer_checks.json` and
`scenery6_quick.json` use aligned validation flags, private-stack flag clearing under DI and
unrolled source comparisons. Six bounded scenes and eight flag-page boundary IDs pass, including
the stale-source and retained-validation negative controls. Level-6 quick 2,000 retains all
347 images / 12,791,808 pixels / 2,966 capture events / 347 map / 346 ULA comparisons.
Its unchanged maximum falls from 37,782.875 to **32,738.5** equivalent T; bounded unchanged
maximum is **32,219**. Level-6 cold/dirty maximum is still **455,240.75**. These numbers supersede
the scene timings below. The TOTAL gate still fails, including capture and future sprite/commit
costs. No frame integration, other-level replay milestone or shop-path change occurred.

`tile_renderer_units.json`, `tile_cache_units.json`, `tile_batch_units.json` and
`scene_renderer_checks.json` exercise actual assembled Z80/Z80N writes through modeled shadow
write-only Layer 2 paging. The complete scenery worker uses the clean map retained by the capture
kernel and live game graphics. This is an offline execution harness, not an installed frame hook.

- All 384 attribute/FLASH combinations, uniform bitmap extremes, edge positions/sections, invalid
  inputs and front protection pass. The direct 64-slot cache checks complete source content, ID
  and relevant FLASH phase, including collisions, source mutation and a stale-key negative control.
- Complete 576-cell batches pass; malformed jobs late in the list and invalid cache slots reject
  before any pixel write. Broken shadow/visibility controls are detected.
- Six bounded stage-1 scenes pass cold/unchanged/same-ID mutation comparisons (663,552 viewport
  pixels). Independent front/back content keys, whole-scene attribute/FLASH changes and a single
  colliding map ID are checked. Broken source comparison and retained validation flags are detected
  using surviving private scratch and the good worker's real source/cache pages.
- `scenery1.png` through `scenery6.png` show the clean 256x144 scenery produced by the assembled
  worker, using a Spectrum colour lookup. They omit actors and HUD; they are not sprite previews.
- `scenery6_quick.json`: representative 2,000-frame RZX iteration, 347 scenery images / 12,791,808
  viewport pixels, 2,966 capture events, 347 map and 346 ULA comparisons; all invariants/IRQ and
  negative controls pass. Host alternates inactive target banks; no runtime commit is tested.
  Other levels retain bounded scene checks; all-six quick replays resume at integration milestones.
- Timing model includes one extra cycle per modeled read at 28MHz, divided by eight. Primitive
  maxima in these cases: tile 708.25, cache miss 1,238.375 / hit 484.5; prepared batch 307.12 per
  tile (preparation excluded). Cold scene maximum 459,051.75. Distinct-source validation reduces
  level-6 unchanged maximum from 58,200.625 to 37,782.875. **The total 35,000/tick gate fails**,
  before capture, sprites or commit. No hardware-speed or complete-renderer timing claim.

Run from nexclash; use level 6 during iteration, other levels at milestones (user preference):

```bash
python -m nexclash.inferno --tile-renderer-units --json work/tile_renderer_units.json
python -m nexclash.inferno --tile-cache-units --json work/tile_cache_units.json
python -m nexclash.inferno --tile-batch-units --json work/tile_batch_units.json
python -m nexclash.inferno --scene-renderer-checks ../specnext/reference/inferno --out work/scenery --json work/scene_renderer_checks.json
python -m nexclash.inferno --scenery-check ../specnext/reference/inferno/Inferno6.rzx --quick 2000 --json work/scenery6_quick.json
# Integration milestone, not the per-edit loop:
python -m nexclash.inferno --scenery-all ../specnext/reference/inferno --out work/scenery_quick --quick 2000 --json work/scenery_summary.json
```

Next: budgeted validation/dirty scheduling, frame hook and atomic commit, sprite compilation/upload,
modal transitions, colour workflow and original-BASIC startup through all levels/ending. The engine
remains unregistered and its record excluded/unstamped. Existing NEX diagnostics are unchanged;
none contains the new scenery code or is a sprite release.
