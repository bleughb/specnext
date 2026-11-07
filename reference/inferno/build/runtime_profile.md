# Runtime cost attribution and row-bounded exact validation — 2026-11-07

Stage 2 remains incomplete. Sprites remain disabled. Runtime live-table enumeration,
content/duplicate-index selection, the connected loading driver/UI, protected uploads and
complete-frame publication remain open. The 8EF9 pause and memory ownership layout are unchanged.

## Attribution

Every complete replay update now retains its frame number, actor count, component milliseconds
and simultaneous total in `update_timings`. Capture costs are separated by original hook site.
The post-copy hook is split into scenery map/bookkeeping, source compilation and wrapper/prepare
instructions. The source worker is split into geometry parsing/comparison, tile addressing and
attribute work, bitmap equality, and setup/finish. Dispatch and cold colour/B fill remain separate.
Instruction deltas include the existing read allowance. Source totals and every update's component
sum must reconcile exactly (within floating-point tolerance for updates) with the existing totals;
the record count must equal the number of completed post-copy hooks.

These are executed assembled CPU costs under the simulator, not wall-clock Next measurements.
Host table scans/content selection are still unmeasured. Capture and post-copy wrappers are
included; source/dispatch external wrappers, uploads, queue and physical waits are excluded.
A subtotal below 10 ms would remain UNPROVED, not PASS for the complete pipeline.

The baseline profiles for levels 1, 4 and 6 identify simultaneous peaks at original replay frames
1181, 820 and 589. Level 1 spends 4.566 ms in tile-address/attribute work, 3.280 ms in bitmap
comparisons and 1.375 ms in geometry parsing at its 16.317 ms worst update. Level 6 spends
3.183 ms in scenery map/bookkeeping and 3.394 ms compiling sources at its 13.875 ms worst update.
Do not add independently maximized components: the JSON retains every simultaneous update.

## Exact-row bounds change

The exact validator still compares every header, width, dx/dy, tile ID, bitmap and attribute byte,
plus total length, FLASH and paint generation. Header/width reads retain individual bounds checks.
After a nonzero matching width (1..128), the worker bounds the complete remaining row once:

- Serialized remainder has `2 + 10*width` bytes. Its last byte must be below mapped address 4000.
- Live remainder has `2 + width` bytes. Its last address must not carry past FFFF or lie below 4000.

Only those proved spans use unchecked individual byte comparisons. The next width/terminator
checks its bounds again. No cached pointer/hash acceptance, cross-draw deduplication, yield or
source-lifetime assumption is introduced. Capture and original RAM/stack behavior are unchanged.
The new worker is 720 bytes, four bytes smaller than the 724-byte baseline.

The small three-tile exact-hit unit improves 0.165786 to 0.155179 ms. Exact 8 KiB validation
improves 24.696929 to 19.694857 ms, still above the entire runtime budget. Capacity capture stays
23.113321 ms. New fixtures cover widths 1, 2, 16 and 128 with a terminator at FFFF and a stored
stream ending exactly at its page boundary, plus three wrapping relocations for each width.
All existing same-address mutations and deliberately removed byte/bitmap comparisons remain checked.

Repeated identical source streams are counted per update, including their executed validation
cost. This is diagnostic potential, not an optimization or permission to skip checks. The worst
level-6 update has 14 draws of nine exact streams; five repeated validations cost 1.317 ms after
the change. A future reuse mechanism must prove stable original sources or reliable invalidation
across the relevant draw interval. This checkpoint continues validating every draw.

## Six own-original quick results

All six 2,000-frame correctness replays pass: 12,000 frames and 13,194 owned dispatches/exact
validations, with no sampled cold misses. All 1,850 complete updates retain timing rows.

| Level | Previous max, ms | New max, ms | New peak frame | Repeated validation at that peak, ms |
|---|---:|---:|---:|---:|
| 1 | 16.317 | 14.907 | 1186 | 0.904 |
| 2 | 14.031 | 13.380 | 1378 | 2.369 |
| 3 | 10.995 | 10.548 | 1224 | 0.487 |
| 4 | 15.391 | 14.470 | 830 | 0.795 |
| 5 | 10.167 | 9.791 | 555 | 0.516 |
| 6 | 13.875 | 13.245 | 589 | 1.317 |

Five measured subtotals still FAIL 10 ms. Level 5 reaches 9.791 ms but is UNPROVED:
its remaining 0.209 ms excludes runtime selection, external source wrappers, uploads, queue
and physical waits. No complete runtime timing gate passes.
Loading construction/store costs are unchanged: capture and colour/B/store assembly did not change.

The paired L1/L4/L6 profiles retain the same update frames and actor counts; no sampled update
regresses. Initialization, pause, owned-cache, source mutation/negative controls, DMA/DDMA/no-blitter/CPU
fallbacks, current/pending protection and sampled level-4 shop checks pass. Bundled assembly and
doccheck pass. A separate 2,000-frame L6 cold-content replay also passes, including timing
attribution for construction misses (`runtime_profile_cold6.json`). The initial 600-frame cold
probe was insufficient to cover all capture sites, so it was extended; no coverage gate was relaxed.
Full recordings and physical hardware were not run.

Evidence: `runtime_profile_quick/`, `runtime_profile_summary.json`, `runtime_profile_before1.json`,
`runtime_profile_before4.json`, `runtime_profile_before6.json` and `runtime_profile_*checks.json`;
`runtime_profile_initialization.json` retains the original initialization scope limitations.

## Continue

Connect runtime live-table enumeration and exact content selection to the private loading workers
and pause gate. Resolve duplicate indices explicitly and retain the previous complete frame for
unseen/mutated content, capacity refusal or incomplete work. Keep current and pending ownership
protected. Address scenery's approximately 3.2 ms per-update map bookkeeping as well as exact
validation; neither is made free by moving host orchestration to assembly. Measure the complete
connected hooks before enabling any replacement display layer. Continuous original loading/ROM
lifetime, physical IRQ timing, FLASH and other modal paths remain unproved.

Reproduce from nexclash with the bundled assembler:

```bash
python tools/asm2profile.py --check inferno
python -m nexclash.inferno --actor-job-checks --json work/row_job_checks.json
python -m nexclash.inferno --loading-prep-all ../specnext/reference/inferno --quick 2000 --out work/row_quick --json work/row_summary.json
python -m nexclash.inferno --initialization-tests ../specnext/reference/inferno --json work/row_initialization.json
python -m nexclash.inferno --loading-pause-checks
python -m nexclash.inferno --owned-cache-checks
python -m nexclash.inferno --actor-blit-checks
python -m nexclash.inferno --modal-checks ../specnext/reference/inferno/build/modal4_entry.json
python tools/doccheck.py
```
