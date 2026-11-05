# Inferno timing architecture evaluation — 2026-11-05

The useful change is to stop expanding Spectrum scenery into Layer 2 pixels. A new,
experimental assembled text-tilemap worker reproduces the same scenery using original
one-bit graphics and ink/paper pairs. It is not installed in a NEX or enabled at runtime.
The approved appearance, original game RAM, producers and copier remain unchanged.

## What the speed figures mean

All figures below are **added work per game update**, not the duration of the whole game
update or the 50 Hz display frame. Divide equivalent 3.5 MHz T-states by 3,500 to get ms.
The model executes the assembled instructions at 28 MHz and conservatively adds one cycle
per modeled read. These are modeled costs, not physical-Next measurements.

| Level-6 2,000-frame replay | Equivalent T | Extra time |
|---|---:|---:|
| Previous Layer 2 worker, worst rebuild | 455,240.750 | 130.069 ms |
| Previous Layer 2 worker, worst unchanged call | 32,738.500 | 9.354 ms |
| New textmap worker, worst call, rebuilding every image | 22,913.250 | 6.547 ms |
| New textmap + capture, worst combined game update | 30,476.375 | 8.708 ms |
| Total added-work target, including future sprites/commit | 35,000 | 10.000 ms |

This is about a **20x reduction in worst scenery cost**, not a 20x increase in game speed.
It removes the old renderer's long redraw stalls. The remaining 1.292 ms must still cover
sprite construction/uploads, wrapper overhead and commit. The full-render timing gate is
therefore **not passed**. A synthetic 256-source image takes 9.584 ms for scenery alone;
resource capacity does not imply a passing worst-case time budget.

## Sources and choices

Primary references checked: [Z80N instructions](https://wiki.specnext.dev/Extended_Z80_instruction_set),
[text tilemap](https://wiki.specnext.dev/Tilemap),
[tilemap control](https://wiki.specnext.dev/NextReg:$6B),
[map base](https://wiki.specnext.dev/NextReg:$6E),
[definition base](https://wiki.specnext.dev/NextReg:$6F),
[clip coordinates](https://wiki.specnext.dev/NextReg:$1B),
[DMA](https://wiki.specnext.dev/DMA), and
[physical memory](https://wiki.specnext.dev/Memory_map).
The local guide r3, nexclash/docs/TECHNIQUES.md hardware benchmark tables and
nexclash/z80n.py's board/core corrections were also consulted. Documentation is not a
hardware test of this engine.

| Candidate | Assessment for Inferno |
|---|---|
| More Z80N substitutions in the old pixel loop | Useful locally; does not remove 64 output pixels per tile or per-cell content validation. MUL and ADD rr,A simplify addresses. LDWS advances a row-address high byte and is useful with column-oriented data; it does not expand bitmap bits into colours. LDIRX/LDPIRX are copy/pattern operations, not bitmap decoders. They are not a general replacement for faster stack copies. |
| DMA for every 8-byte tile row | Too many tiny transfers and address changes. DMA is better for contiguous uploads or large copies; setup and re-arming must be charged. It stalls the CPU in continuous mode and can lose an original interrupt pulse. |
| More Layer 2 cache memory | Removes direct-map collisions and permits pre-expanded assets, but still copies the final pixels. It cannot by itself fix the 36,864-byte viewport redraw cost. |
| Scroll registers/ring buffer | Could avoid pixel movement for real global scroll. The existing level-6 map census finds (0,0) as the best shift; its changes are not a simple whole-map translation. Keep this as a path-specific optimization, not the main design. |
| **1-bit hardware tilemap** | **Implemented as the experimental worker.** The display hardware expands the original eight bitmap bytes. Attributes select ink/paper pairs. No pixel expansion, 64-slot colour cache, or per-buffer thirteen-byte source key is needed. |
| Copper / raster commit | Useful for showing a complete map and sprite set at a safe boundary. It solves tearing, not construction time. Indexed registers must have one owner; setup/commit and missed-deadline behavior still need implementation and hardware checks. |
| Accelerate or remove original drawing | Rejected here: the original copier, collision map, registers, timing-sensitive ISR and game RAM behavior remain the reference. The new renderer is additional work. |

## Implemented data path

- Page 68 retains the exact captured original map. The worker reads its 576 words through SP
  under DI, avoiding another 1,152-byte map copy. It switches back to its private stack for
  first-use source construction and restores SP at exit.
- Each distinct 10-bit source ID is copied once **on every image**. Its live bitmap and
  attribute are read again, so address reuse or animation cannot silently keep stale content.
  A 1,024-entry flag table and 2,048-byte slot/attribute lookup in page 69 serve repeated cells.
- Page 14, unused by the original 48K game, holds two map regions at offsets 0000/0600 and
  two 256-pattern halves at 0C00/1400. Total reservation is 7,168 bytes. Each pattern is eight
  bytes, not a 64-byte pixel tile. The maps retain the hardware's 40-column stride.
- Page 14 is temporarily mapped into CPU slot 2 only while DI/28 MHz holds. The original
  physical screen page remains untouched and is restored at slot 2 before return. Original
  source graphics at DC00-FFFF stay visible. Mapping preservation and physical RAM writes
  are checked instruction by instruction / at return in the harness.
- Attribute bits encode one of 128 original ink/paper pairs. FLASH swaps the pair in the
  lookup instead of rewriting bitmap pixels. Pattern bit 8 selects the inactive definition
  half. The worker never changes the front map, front definitions, palette or display state.
- More than 256 distinct source IDs returns an explicit error and preserves the front image.
  It is not silently truncated. Whether a larger shared-slot allocator or bitmap deduplication
  is needed must be determined from broader recording coverage.

## Display integration still to prove

The planned register setup is text/512/forced-over-ULA mode ($6B=$8B), definitions at bank-7
0C00 ($6F=$8C), and map base $80 or $86. Clip coordinates 16..143 / 80..223 correspond to the
ULA viewport x=0..255 / y=48..191. X scroll 288 and Y scroll 176 place the visible cells in
map rows 0..17, columns 0..31. This compact storage relies on the clip and scroll setup;
without it, the hardware would show unused/overlapping map areas. These settings are a
**documented plan, not an executed video test**.

Text-mode transparency uses the final colour, not the 4-bit tile transparency index.
Palette pairs must reproduce the ULA colours while keeping black opaque and avoiding the
selected global transparency colour. Sprites must remain above the tilemap; the original
HUD and all modal screens must remain ULA. The new backend changes the implementation
proposed in stage 1, not the approved visual design; keep it experimental until these
conditions and raster-safe map/sprite commit are demonstrated.

## Expanded Next RAM

The user authorizes expanded memory. On a 2 MB Next, the documented application RAM is
1,792 KB: pages 0..223; firmware-reserved space is separate. Pages 96..223 are available
only with the expansion. Do not treat them as unexpanded-machine RAM or use page FF as RAM.
The current worker does not need these pages.

Use expanded RAM next for validated whole-actor/pattern caches and immutable conversion
lookup tables. For example, all 128 Spectrum colour pairs x 256 bitmap row values x four
packed sprite bytes require 128 KB, removing per-pixel colour branches. The approved B
interior-fill operation still spans the whole actor; a colour lookup cannot replace it.
The cache key must include live run-list/bitmap/attribute contents, not just an address.
Upload only changed sprite patterns; measure persistent-program DMA versus OUTI including
re-arm and attribute costs. Extra CPU RAM does **not** enlarge hardware sprite pattern RAM
or the tilemap's bank-5/bank-7 display-memory window.

## Evidence and next work

`textmap_units.json`: 12 bounded scenes (six levels, both buffers), all 512 attribute/FLASH
combinations, capacity/front guards, live mutations with surviving scratch, and broken
stale-source/front-write/FLASH controls. `textmap_summary.json` plus `textmap1..6.json`:
2,000 frames from each level's own replay, 1,855 scenery images / 68,382,720 scenery pixels,
16,903 capture events, original RAM/register and reconstruction checks. Maximum observed
source set is 134; this is sampled coverage, not a full-game maximum.

`textmap_shop_census.json` replays level 4 through frame 52,500 without desync. Gameplay
capture/copy sites last execute at 51,802 and do not execute at the recorded shop image
(frame 52,229). This shows why a gameplay-only hook cannot switch off an old overlay for
the shop. It does **not** prove a modal-disable hook: none is installed yet.
`textmap_shop_state.json` independently reaches that frame from the same original recording:
the shop uses ROM IM1 entry 0038, SP 86B1, interrupted return 8193. Gameplay IM2 IRQ tests do
not establish safety in this modal context.

Next: identify and test modal entry hooks, prove the clip/palette/layer setup, then connect
post-copy frame work and a raster-safe complete-image commit. Implement approved B sprite
construction/cache/uploads with expanded RAM where useful, and measure the **whole tick**.
No sprite NEX, full verification stamp, continuous release or hardware speed claim exists.
