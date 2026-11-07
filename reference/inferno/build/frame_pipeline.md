# Inferno frame preparation, display setup and queued switching — 2026-11-05

Stage 2 remains incomplete. These are assembled components and differential/device-model
checks, not a playable sprite NEX. The approved B sprite compiler/cache/pattern uploader,
continuous frontend, all modal entries, FLASH clock synchronization and hardware timing remain open.

## Progress

- `FramePatch` adds a real patch specification at 8F95 (original `LD A,(AC49)` bytes verified),
  after the unchanged original ULA copier. The wrapper at 3BE0 saves all main and alternate
  registers in page 68, enters the page-69 worker, restores every mapping/register/stack value,
  and executes the displaced load. No original game RAM write is permitted by its memory model.
  Preparation leaves display readiness zero until the missing sprite stage has completed.
- Page 69 contains the tilemap compiler, setup, queue and preparation routines. Page 14 remains
  the double-buffered map/pattern store. A pending Copper acknowledgement prevents reusing a
  display-owned back buffer. The preparation hook checks the current map base when selecting
  its destination. Incomplete captures cannot prepare a frame.
- Six original 2,000-frame replays exercise 1,850 post-copy hooks / 68,198,400 scenery pixels,
  plus 16,903 original capture events. Per-instruction interrupt-enabled mapping/register checks,
  exact original RAM comparisons, inactive-buffer/pending/phase units and broken-DI/skipped-render
  controls pass. Original source bytes remain unchanged from scenery capture / actor draw until
  post-copy in 1,850 scenery and 13,159 actor cases. This is sampled lifetime evidence, not a
  full-recording proof or permission to use pointer-only persistent caches.
- The scene-map capture loop now uses unrolled LDI instead of LDIR. This reduces its added
  cost from 1.018 ms to 0.846 ms while preserving its exact original-state contract.

## Palette and clipping

The assembled one-time setup reads the active ULA palette through NextRegs $41/$44, preserving
nine-bit colours, palette bank selection and palette index. Ink entries 0..15 and paper entries
128..143 are read separately. They need not contain equal RGB values. The 128 tilemap palette
pairs reproduce both. Enhanced ULA mode, an already-visible tilemap, or a source colour matching
global transparency are explicitly rejected before modifying display palettes.

FLASH now inverts a tile's bitmap when required. Swapping attribute colour indices alone is
wrong if the original ink and paper palette entries differ. The prior textmap prototype's
pair-swapping description is superseded. The worker still takes an explicit FLASH phase;
synchronizing that phase with the actual ULA clock is not implemented.

Setup establishes the bank-7 text/512 mode, palette 0, original viewport clip, scroll offsets,
SLU priority, ULA output and zero raster offset. Both replacement layers remain disabled.
Tests project the assembled register settings through the documented tilemap geometry and
compare 294,912 RGB pixels, plus every outside-viewport coordinate, across both active ULA
palette banks, FLASH phases and map halves. Broken palette-source and clip controls fail.
This models the hardware description; it is not a hardware video capture.

## Copper commit queue

The compiler's pending attribute area is a page-74 template: WAIT at line 224, sprite index
and five attributes per record, then map base, layer visibility, acknowledgement, and HALT.
The uploader never edits a running list. It requires completed setup and a fully ready image;
that ready flag is deliberately never produced by the current scene-only preparation hook.
An outstanding commit must acknowledge its serial through NextReg $7F before another list is
armed. Serial wrap is covered. Startup must initialize previous sprite count to 128 unless
all hardware sprites have already been cleared.

Only max(previous-visible-count, new-visible-count) sprite records are uploaded. When the count
shrinks, the uploader clears visibility in trailing old records even if supplied bytes are stale.
A fixed WAIT is followed by a HALT, so the completed program cannot repeat and revive old data.
The CPU does not wait for the beam. In the bounded Copper model, a late start on line 224 finishes
on line 225, outside the viewport, even at the shortest modeled frame/line length. Copper timing,
sprite scanline latency and physical IRQ delivery still require hardware confirmation.

The queue tests use **synthetic attribute records**, not compiled approved B sprites. Pattern
uploads and protection of currently displayed sprite pattern slots remain the sprite compiler's
responsibility. Do not turn the queue's ready flag on merely because scenery is complete.

## Shop return

The original level-4 replay reaches the gameplay return at frame 51,805, before the captured shop
image at 52,229. The new 9019 hook checks original `LD SP,86D5` bytes, stops Copper first, disables
tilemap/sprites/Layer 2 without changing their other control bits, invalidates the capture phase,
and reproduces the original stack change. The original following IM1 transition and all drawing
continue. A real replay state and 256 control-bit combinations preserve all original registers/RAM.
Missing Copper cancellation and each missing layer disable are informative negative controls.

This proves this sampled gameplay-return path only. Pause/messages and alternate intro/ending/load
entries must be classified separately. The hook is not yet packaged in a release NEX.

## Speed in milliseconds

These are added CPU costs per game update, modeled at 28 MHz with one extra cycle per modeled
read. They are not physical-Next speed measurements. The target remains **10 ms total**.

| Work | Added time |
|---|---:|
| Worst capture + actual post-copy scenery hook across six quick replays | 8.715 ms |
| Queue, 58 sprites (largest observed count) | about 0.55 ms |
| Queue, shrinking 58 sprites to none | about 0.64 ms |
| Queue, all 128 sprite records | about 1.17 ms |
| Shop-return hide hook | 0.035 ms |
| Palette/clip setup, once only | 2.030 ms |

The observed-size queue leaves roughly **0.64–0.74 ms** for sprite construction/pattern uploads
and any remaining integration work. That is still tight. The full-render timing gate is **not
passed**. Full-capacity FLASH-heavy synthetic scenery alone exceeds 10 ms; broader resource
coverage and cache/scheduling decisions are still necessary. The earlier large Layer 2 redraw
cost is gone, but this does not establish original game speed on hardware.

## Recipes and evidence

Run in nexclash:

```bash
python -m nexclash.inferno --display-checks --json work/display_checks.json
python -m nexclash.inferno --queue-checks --json work/queue_checks.json
python -m nexclash.inferno --modal-checks work/modal4_entry.json --json work/modal_checks.json
python -m nexclash.inferno --frame-check ../specnext/reference/inferno/Inferno6.rzx --quick 2000 --json work/frame_hook6.json
# Integration milestone:
python -m nexclash.inferno --frame-all ../specnext/reference/inferno --quick 2000 --out work/frame_quick --json work/frame_summary.json
```

`modal4_entry.json` comes from the existing census tool on the level-4 original replay,
PC 9019, stop 51820, sample frames 51802..51815, memory 4000:C000. It contains one entry at
51805, with no desync. `display_textmap_units.json` retains the updated standalone compiler
checks; `frame1..6.json` and `frame_summary.json` are the current integration evidence.

References: [palette reads/writes](https://wiki.specnext.dev/NextReg:$44),
[8-bit palette read](https://wiki.specnext.dev/NextReg:$41),
[palette control](https://wiki.specnext.dev/NextReg:$43),
[Copper](https://wiki.specnext.dev/Copper),
[Copper control](https://wiki.specnext.dev/NextReg:$62), and
[acknowledgement register](https://wiki.specnext.dev/NextReg:$7F).
