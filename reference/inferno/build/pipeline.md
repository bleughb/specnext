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
