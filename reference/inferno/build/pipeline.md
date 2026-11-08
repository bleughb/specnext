# Inferno sprite pipeline — 2026-11-08

Order: (1) live-table driver at 8EF9; (2) window exact dispatch and duplicate indices; (3) complete
pattern/frame state; (4) protected uploads. Sprites and new layers stay disabled until the whole
pipeline passes. Rule: nothing reads CAP_LOG before the window work.

## 1. Live-table driver (nexclash `claude/inferno-pipeline-driver`)

Assembled driver, page 81 (`driver`, `drvpage`), entered from the 8EF9 gate through a page-68 stub at
1D80 (DI, 28 MHz). For each of the 256 C100 indices: snapshot (78); exact byte search of published
entries (equal stream = duplicate: the entry's payload pointers are copied, valid written last); else
bounds, canvas clear, colour (75, pinned bytes), whole-image B (76), store (79). Worker pages 75, 76,
78, 79 carry the 20-byte `drvworker` stub at 1D00 and the word 1D00 at 1FF0 (a worker's RET returns to
the driver through the page swap). Slots restored; the gate restores registers, R and caller speed.

The duplicate test is the exact stream, so "duplicate" means exactly what the validator accepts; the
host census keyed on tile tuples, where different row splits of the same tiles compare equal.

Checks (`--loading-driver-checks`, crafted table; `--loading-driver-level REF --level N`, real table
at the first 8EF9): against an independent Python oracle for every index (stream bytes, B canvas,
duplicate sharing, rejected and empty indices, counters); all writes and mappings guarded; registers,
R, RAM and speed against the original single instruction over 4 speeds x 4 R values. Negative
controls detected: duplicate search by size only, canvas not cleared, B fill skipped, dx/dy not sign
extended; a store full at the last page leaves the index unpublished and the run continues.

| Level | Frame at 8EF9 | Distinct stored | Duplicate indices | Rejected | No tiles | Driver, ms | Instructions |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 681 | 101 | 2 | 143 | 10 | 4880 | 12424949 |
| 2 | 438 | 109 | 0 | 135 | 12 | 3650 | 9258031 |
| 3 | 475 | 88 | 2 | 153 | 13 | 3217 | 8167675 |
| 4 | 430 | 122 | 1 | 115 | 18 | 4580 | 11630712 |
| 5 | 466 | 84 | 1 | 158 | 13 | 3434 | 8714294 |
| 6 | 452 | 118 | 5 | 120 | 13 | 6896 | 17623182 |

Costs are executed assembly in the simulator (28 MHz model with the read allowance), total pause
including scan, duplicate search and clears; no hardware. The stored counts equal the host census
(`loading_owned.md`, 101/109/88/122/84/118). Evidence: `pipeline/driver<L>.json`. Not installed in any
NEX: the pause is only worth a hardware run once the runtime side (items 2-4) exists.

## 2. Window dispatch (nexclash `claude/inferno-pipeline-dispatch`)

`wk_dispatch` (page 69, 1800-19FF) runs after the scene compile in the 8F95 coroutine and is the first
reader of CAP_LOG. For each record: entry 0800 + 16*image in page 79 (valid, FLASH phase 0, generation
0), then a byte-exact comparison of live C100 pointer, header, runs, tile IDs, bitmaps and attributes
against the stored stream in the owned page, and the stored length. Duplicate indices need no lookup:
the driver gave them the shared entry. Any miss leaves `DX_READY` 0; unfinished work is dropped as in
3c (the 8F95 drop path also clears `DX_READY`: 8F95 now 156-162 T, was 156-160). Polls every record, row
and tile, HL carried on the work stack, slot 1 remapped on resume. No display reads the flag yet.
Only phase 0 is prepared; a FLASH-phase store is part of item 3.

Unit checks (`--dispatch-checks`, crafted store and log): exact hits with duplicate, a yield every Nth
poll, scene not ready, log overflow, no entry, live bitmap/attribute/geometry changed, generation,
stored length. Controls detected: bitmap compare removed, slot-1 remap on resume removed, length not
compared. Gate (`--jobs 6`, with the driver's real store per level): 0 failures over 1,855 states,
every dispatched frame agrees with the oracle; 10745 records matched, no sampled miss;
9907 -48..45 T. Slice margin over 64 CTC phases >= 108 T (`probe_cw_margin64.py`, now with the
store, 768 runs). L6 loading-prep quick PASS. **Cost**, in the simulator (no hardware): done in the
window 1,579 of 1,855 (85.1 %, was 87.7 %); dropped 276 (187 no slice, 89 unfinished), longest run 14
updates on the first 2,000 frames (6 before). Runs of that length would hold a stale frame for up to
about 0.35 s once a display exists; the user should judge that at item 3/4.

NEX `Inferno_copier_window_m3d_diagnostic.nex`, MD5 cd4243eba314e357ffb8e199a6b0d42d, boot checks PASS
incl. hook bytes after boot. The driver is not installed in it and page 79 is zero, so every dispatch
misses on its first record: it only shows the new page-69 code leaves pace and sound alone.
Hardware (user, 2026-11-08): m3d runs ok. No detailed comparison reported; the driver, the store and a
dispatch that matches are still unproved on hardware.

## Remaining
3. Pattern allocation and frame attribute state from the owned canvases, built in the window after
   dispatch, current and pending protected; a FLASH-phase store. Needs the drop rate above reviewed.
4. Uploads under the existing protection and DMA/CPU fallbacks. Then install the driver and hardware.

## Early integrated diagnostic (user-agreed plan, spec in bleughb/nexclash#171, PLAYBOOK 3d and stage 2)
A milestone, not the Stage 2 exit; fits with items 3-4. It changes what the user sees: confirm with them before building it.
- A real NEX through the real converter, stub, hooks and memory layout, showing one sprite from live game data, every step connected.
- One sprite shown, but selection and validation run for every actor and uploads are exercised at the worst observed load (samples so far: 58 visible chunks, 56 distinct patterns; samples do not cover full recordings, say so).
- Report pace and freshness separately: publication rate, longest miss run, maximum displayed-state age, under demanding motion. Measure the diagnostic's own drops: 12 % was scenery only, 14.9 % adds dispatch.
- Each experiment records constraint, evidence, success criterion, change, result. The two-experiment reassessment rule applies. Do not use assumed spare time as a budget.
- Once #171 merges, use `runchecks.measured` and `caseselect` in new Inferno verifiers.

## Driver NEX (first step of the integrated diagnostic)
`Inferno_driver_diagnostic.nex` (`--copier-window-build --cw-driver`), MD5 2d38a1bdacafc5c3724c6cd6ba013cce: m3d plus the 8EF9 gate, the driver and its worker and table pages, so the store is real and dispatch can match. Boot checks PASS incl. hook bytes after boot. Header asks for the expanded machine (banks 48-55 and 64-67). No display change. The model predicts a 4.9 s pause for level 1; pace, sound and pause length on hardware are not yet measured.

## Integrated diagnostic: experiment 1, pattern upload load (model, no hardware)
- Constraint: uploads must fit the window; a CPU 256-byte pair costs 0.298 ms in the earlier model, so 56 per update would be 16.7 ms against a minimum wait of 4.4 ms.
- Evidence: the worst load (58 chunks, 56 patterns) counted patterns in use, not patterns that change.
- Success criterion: after the first update, uploads per update small enough to fit, and current + pending + new never above the 64 hardware slots.
- Change: none to the game; `pipeline/probe_pattern_census.py`, first 5,000 frames per level, 64 slots, least recently used eviction, current and pending protected.
- Result (`pipeline/pattern_census.json`):

| Level | Updates | Max patterns in use | Uploads median | p99 | Max | First update | Updates over 64 protected |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1053 | 56 | 0 | 4 | 47 | 47 | 8 |
| 2 | 1134 | 39 | 0 | 3 | 8 | 8 | 0 |
| 3 | 1130 | 31 | 0 | 1 | 13 | 13 | 0 |
| 4 | 1115 | 48 | 0 | 6 | 39 | 39 | 0 |
| 5 | 719 | 26 | 0 | 1 | 9 | 9 | 0 |
| 6 | 1061 | 40 | 0 | 6 | 12 | 7 | 0 |

Uploads are rare once the patterns are in place: the maximum is the first update, so the initial set belongs in the 8EF9 pause. Level 1 needs more than 64 protected patterns in 8 of 1,053 updates: those frames cannot be published and count as misses unless pattern use is reduced. Samples cover 5,000 frames per level, not full recordings. This is a census model: it does not measure publication, freshness or hardware cost.

Next: pattern selection for every actor in the window, the protected store, initial upload at 8EF9, then one sprite, then the freshness figures.
