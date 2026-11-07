# Copier window: original pacing and the translated copier head — 2026-11-07

Branch `claude/inferno-copier-window` in both repositories, from nexclash `codex/inferno` 4bfa72c.
All figures are simulated original-game T-states (uncontended, 3.5 MHz) from the six full
original level recordings (449,659 frames incl. the level-4 shop), not hardware measurements.
Stage 2 remains incomplete. Milestone 2 (§6) installs the window at 8F92 only in a diagnostic NEX
(no hook work, no sprites); its pace and sound are proved in the simulator, not yet on hardware.

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

## 5. Open after milestone 1 (superseded by §6)

Milestone 1 left OUT replay, pad, IRQ handling and contention open; §6 records what milestone 2
closed and what remains.

## 6. Milestone 2: OUT replay and pad (nexclash `claude/inferno-copier-window-m2`)

Design (evaluated against the handover, changed where measurements required it):
- **Lockstep, not head-then-replay.** The first OUT is due 244 T after 9790 entry; the translated
  head takes ~4.7-11 ms. Each value change is OUT from the head's change branch at its original T
  (`cw_wait`, CTC deadline); OUT values (A700) and times (tiles >= 16) do not depend on the head's
  own writes. A change the head reaches late is OUT at once. Cell 415 is deferred until after the
  row end and epilogue: from its OUT the original has only 169 T to 9907.
- **Clock: CTC channel 3**, timer, prescaler 256 (32 T a tick in every video timing, since CTC and
  CPU both run from clk28), no interrupt, polled. Time base = first edge after entry, timed by the
  sync loop (6 T/iteration). The 8-bit count is extended at row ends and while waiting. Without a
  counting CTC (tested once at first use) the window falls back to the original copier. A raster
  clock (216-228 T a line, mode dependent) cannot time 187 T OUT spacing.
- **X: accumulate.** A bounded shift needs X <= head T - last OUT T = 169 T; the capture hooks
  measure X = 3,198-7,642 T (median 3.8-5.6 k by level, `capture_x.json`). With X the window still
  enters 9907 on time; the burst's first ~X are late. The milestone-2 build installs only 8F92
  (X = 0); the window reads `CW_X` so the X behaviour is modelled.
- **IRQs.** Every original head contains >= 1 frame IRQ (the no-op ISR: 94 T, 10 M1 incl. the IM2
  acknowledge); R is read by level code (L6 BA22/BB89/BB8E) and the filler, so a DI window would
  change R. The window runs EI; page 80 byte 0 is the offset of the IM2 JR at FFFF, so an IRQ enters
  `cw_irq`, which adds 94 T to the deadlines and 10 to R and delays its EI past the /INT pulse.
  998E = 0 throughout (checked). The exit EIs before the speed switch, so an IRQ pending since the
  pad is taken by the game ISR just before 9907, as the original takes it inside its head.
- **Never-read rule.** Window CALLs and IRQ pushes leave bytes only in the 4 below the copier's
  final SP, which 9907's PUSH DE / PUSH HL overwrite first; the verifier runs those two pushes and
  requires all RAM equal (with an IRQ before the copier's own SP, as in the original, the bytes lie
  below the caller's SP).

CHECKS_PLACEHOLDER

Full recordings (`probe_cw_timeline.py`, `cw_timeline.json`; 385,739 frames, 88,187 updates):
101,077 frame IRQs fall in 8F92..9907, at least one in every update (the compensation is always
exercised); 76 (0.09 %) fall in the entry DI span (cap_done + sync, <= 139 T) and are lost (R off
by 10, 9907 94 T early); 26,813 updates (30 %) have a level change at cell 0/1, which is OUT up to
108 T late; 27 updates have slack below 32 T; 9907 begins D5 E5 and SP lies in A1F0..A6FE in all;
998E is never set in a head. Free (waiting) time per update, window model: min 14.6-16.7 ms,
p1 15.3-17.5 ms, median 20.9-23.0 ms by level - the budget for milestone 3.

Contention: on a 48K contention model (SkoolKit CMIOSimulator) the original head is 265-509 T
(0.3-0.5 %) longer than the uncontended model the pad uses, so on a contended machine 9907 comes
~0.1 ms early (never a slip) and the burst ~0.4 % fast. The RZX frames hold ~56-60 k uncontended T
(not 69,888): most contention is outside the head (the tail's screen write-out).

Open: no JNext on the milestone-2 machine (no pace run); hardware sound/speed comparison by the
user; capture hooks do not yet measure X or restore R; the entry DI span loses 0.09 % of IRQs;
hook work in the window (milestone 3).
