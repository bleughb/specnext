# Copier window: original pacing and the translated copier head — 2026-11-07

Branch `claude/inferno-copier-window` in both repositories, from nexclash `codex/inferno` 4bfa72c.
All figures are simulated original-game T-states (uncontended, 3.5 MHz) from the six full
original level recordings (449,659 frames incl. the level-4 shop), not hardware measurements.
Stage 2 remains incomplete; the translated head is not installed and no sprite NEX exists.

## 1. How the original is paced

- The copier `CALL 9790` (from 8F92) calls the limiter **9907 from inside itself** after row 6
  (`CALL Z,9907` at 97FB). 9907 saves registers and SP into 9999, sets flag **998E = 4** and runs
  the beeper filler 9917–9987 (`LD A,R`, `XOR 24 / OUT (254),A`, write sink at A700) until
  `JR $` at 9989.
- The IM2 vector lands on FFFF (`JR` to FFF4, 12 T) → `JP 998B`. While 998E = 0 the handler is a
  no-op (`PUSH AF / EI / LD A,0 / OR A / POP AF / RET`). With 998E = 4 it clears the flag,
  restores SP and returns into the copier at 97FE, which finishes rows 5..1 and its DI write-out.
- Census over every level: 998E is written only at 8F32 (=0, init), 9914 (=4) and 9995 (=0), the
  last two exactly once per update. No HALT executes in gameplay.

| Level | Updates | Copier head T (median / max) | 8F7C→9907 T (median) | Slack 9907→IRQ T (p1 / p10 / median) | Slips at +1 / +5 / +10 ms |
|---|---:|---|---:|---|---|
| 1 | 13,869 | 93,187 / 102,453 | 115,924 | 1,385 / 9,332 / 27,787 | 3% / 23% / 66% |
| 2 | 11,921 | 96,823 / 106,822 | 116,476 | 2,210 / 13,233 / 26,995 | 2% / 17% / 79% |
| 3 | 13,749 | 94,575 / 101,544 | 115,243 | 2,377 / 11,352 / 28,169 | 2% / 21% / 70% |
| 4 | 18,635 | 96,520 / 104,776 | 124,576 | 1,307 / 10,519 / 25,714 | 2% / 24% / 81% |
| 5 | 13,831 | 94,500 / 105,382 | 112,490 | 1,716 / 9,888 / 29,275 | 2% / 22% / 64% |
| 6 | 16,182 | 101,544 / 108,034 | 125,442 | 277 / 2,919 / 19,507 | 12% / 48% / 56% |

"Slips at +x ms": share of updates whose slack is below x ms, i.e. that would wait one more
frame (+25 % for that update) if x ms of hook work were added to the foreground. Sources:
`copier_window/pacing<L>.json` (`probe_inferno.py`).

Consequences:
1. The "10 ms TOTAL added work" target is not a pacing gate: meeting it exactly would still slip
   56–81 % of updates and shorten every sound effect (the filler plays only in the slack).
2. Removing all bitmap/attribute validation from the worst profiled updates (runtime_profile)
   would leave about 8.5–10.2 ms, still slipping about half the updates.
3. Tile graphics are mutable during play: level code (B3xx–BCxx, 92BB, 9738) writes F400–FA36
   (L3 also ED00–F0AF) in every level except L2. Exact byte validation stays.

## 2. The copier is also the sound player

Each update the head 9790..97FB processes 13 rows × 32 cells. Every cell does
`LD D,A7 / LD A,(DE) / OUT (254),A`: it replays the A700 buffer written by the filler. About
half the updates change the beeper level (up to 415 changes; `probe_copier_out.py`). Border
bits are 0 except for rare flashes. A copier simply run at 28 MHz would garble the sound.

Exact timing model (`copier_model.py`, checked on 88,187 updates: 88,161 exact; the other 26
differ only by the 2-byte IRQ acknowledge push below SP, see §4):

- head T = 79,477 + 101·G, where G = cells whose tile ID ≥ 16 (12 M1 extra each);
- OUT of cell k (row r = k/32) at T = 121 + 54(r+1) + 66r + 187k + 19·[k>255] + 69 + 101·g(k),
  where g(k) = tiles ≥ 16 before k (`cw_out_t` in nexclash/inferno.py).
- Head range over all updates: 88,163–107,959 T (25.2–30.8 ms).

## 3. Decision: the copier window

Replace the head by a translated head running at 28 MHz with the same RAM result and no OUT.
It logs each OUT value change. Then:
1. replay the logged OUT changes at their original T (CTC timer interrupt, core-gated; raster
   line fallback);
2. pad to the original 9907 wall time (head T, less hook time already spent earlier in the
   update);
3. do the deferred hook work in the freed time. If it is not finished by the deadline, publish
   nothing and keep the previous complete frame.

Everything from 9907 on — filler sound, resuming IRQ, the rest of the copier — then happens at
the original time, so pace and sound match by construction. The budget becomes about 19 ms per
update (original head minus the translated head's cost), against today's worst connected
subtotal of 14.9 ms.

## 4. Milestone 1 (this checkpoint): translated copier head

- nexclash `asm/inferno_hooks.asm`: page-80 `cw_head` (293 bytes) and alt-ROM `cw_go`/`cw_exit`
  at 3CB0 (19 bytes). `CopierWindowPatch` turns `cap_done_tail` into `JP cw_go`. The head replays
  9790..97FB instruction for instruction except the OUT. It logs `[value, E, D, C]` per change,
  restores IY/AF', pushes the 97FE return, sets R = entry R + original M1 (bit 7 kept, constant
  0x3A calibrated once, then checked on every state) and enters 9907 with IFF1/2 set.
- `python -m nexclash.inferno --copier-window-checks ../specnext/reference/inferno --quick 2000`
  (`copier_window/cw_head_checks.json`): 1,854 states (every 8F92 in the first 2,000 frames of
  each level) PASS: all registers incl. R, all game RAM, 119,363 logged OUT changes equal to
  the original's values and uncontended T, head T model. Negative controls detected on 38 of 38
  states each: change detection removed, tile-count `INC C` removed, R constant off by one.
- Cost (cap_done + translated head, equivalent 3.5 MHz T with 28 MHz read waits): max 7.2–7.6
  ms per level, against 26.9–29.7 ms for the original 8F92→9907. Not yet optimised.
- Unchanged: existing capture blob bytes; `--loading-pause-checks`, `--owned-cache-checks`,
  `--actor-job-checks`, `asm2profile --check` and the L6 `--loading-prep-check` quick PASS.

IRQ garbage: in the original, an IRQ during the head pushes 2–4 bytes below SP (the A1FA–A6FD
work stack, or FFF0 if it arrives before `LD SP,A6FE`). A scan of A000–A6FF finds only pops of
pushed data as readers. Bytes below the final SP are never popped. With the head DI these
bytes differ; the installed verifier must enforce "never read" per update.

## 5. Not proved / open

- No OUT replay, no pad, no window scheduling: the head alone would speed the game up, so it
  must not be installed by itself.
- ULA contention (OUT to FE, 48K timing) is not modelled. Pad and replay accuracy need JNext
  `nexclash.pace` and hardware. A raster-line pad (224 T) would misplace about 1 % of updates
  (L6 p1 slack 277 T); prefer CTC.
- Interrupt-injection test over the head, and the integrated verifier with IRQs delivered.
- The capture hooks' own R and cost (8F7C/959B/96A1) still precede the window; their time must be
  repaid by the pad.
