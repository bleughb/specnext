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

Checks (`python -m nexclash.inferno --copier-window-checks ../specnext/reference/inferno --quick 2000
--cw-x .../copier_window/capture_x.json`, `copier_window/cw_window_checks.json`; simulator, uncontended
T with 28 MHz read waits, CTC phase varied per state): 1,854 states of six levels PASS. Registers
incl. R and all RAM exact (the 4 bytes below SP after 9907's two pushes); 119,363 OUT changes, each
within -24..+56 T of the original except cells 0/1 (entry overhead, <= 114 T late; a level change
in 650 states); 9907 entered -24..+42 T from the original. A sweep of all 32 CTC phases on 49 states
(1,568 runs): worst OUT after cell 1 +48.4 T, |9907| <= 41.1 T. Accumulate-X (each state entered X
late, X from `capture_x.json`): 9907 still on time in all 1,854; the burst's first ~X late (877
states change level there). IRQ injection, 23 points x 38 states + 38 double: PASS; 82 points in
the entry DI span (<= 120 T after 8F92) are lost; an OUT due within one tick of an IRQ may move by
one ISR (53 OUTs, <= 95 T). Negative controls 7/7 x 38 (change detection, tile count, R constant,
IRQ T, IRQ M1, pad +3 ticks, deadlines -3 ticks). CTC units: untested -> tested on first use (that
window up to 293 T late), absent or stopped -> original copier (9907 <= 389 T late, R not kept).
Window busy <= 11.3 ms, waiting >= 15.1 ms per update. Diagnostic NEX (`cw_build.json`): boot checks
PASS with the Sinclair and a foreign ROM3; MD5 4f7fef40b4a50b7f1ba7c82d064e851b.

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

## 7. Milestone 3a: timed capture hooks (nexclash PR bleughb/nexclash#136)

Simulator only: uncontended T with 28 MHz read waits, speed switches charged at 3.5 MHz (plus a
"fast switch" bound charged at 28 MHz). Gate: `copier_window/cw_m3_checks.json` (`--jobs 6`).

- **X measured by the hooks.** 8F7C/959B/96A1 each: `DI; NEXTREG 7,3; NEXTREG $C8,1`, R read at a
  fixed M1 offset, sync to the next CTC edge (`cw_edge`: 12 unrolled checks ~3.5 T apart, page 80),
  body, run to the next edge at exit, constant path to the target. X = 32 x ticks + 3.5 T x entry
  check index + K + CW_KT; 8F7C sets CW_X, actor hooks add. K/KR calibrated over all 64 half-T CTC
  phases (a 5-phase calibration was 7 T off per hook; a 6 T looped sync summed over ~20 hooks put
  9907 outside +-56 T). Per hook error about +-2 T; per update X error -12..+17 T.
- **R restored**: entry R + per-hook M1 constant (bit 7 kept).
- **Lost IRQs.** Hooks run DI (page 68 in slot 0 owns the IM2 offset). $C8 bit 0 is cleared right
  after the speed switch (<= 24 T after DI) and read last before the exit (`cap_chk`, one-register
  `IN A,($3B)`; $C8 preselected by `cw_tout`). Set: wait for /INT to drop, then R + 10, X - 94 (+ the
  wait). The window entry does the same (`cap_done` clears, `cw_synced` reads): milestone 2's 0.09 %
  lost IRQs are compensated. A game ISR taken on a site's JP precedes the entry edge: no correction.
  Hardware assumption: a $C8 clear during an active pulse does not take (Rainbow evidence).
- **Model gap.** A pulse starting between a hook's last $C8 read and the IRQ sample after EI +
  NEXTREG 7,0 (the model charges the switch 24 T: ~6 T of window) is lost uncompensated; with 28 MHz
  switches there is no gap. Estimate ~0.07 % of updates (8.5 hooks/update), model only.
- **cw_cal.** At the first window (with the CTC test): 64 NEXTREG 7,0 / 7,3 pairs timed on the CTC ->
  CW_KT = T per pair - 46 (model 0; fast bound -38). Hooks add KT; the window adds KT/2 to its base
  and takes KT/2 off the pad. Fast-bound updates pass with KT; without it 9907 is ~230 T early.
  One-off cost: the first update after boot ~3.3 k T late.
- **DMA map copy.** 9B00..9F7F -> CAP_MAP by zxnDMA (port 6B, continuous, all cores; model 0.65 T/byte
  from the TECHNIQUES 2K figure): 8F7C hook 3.1 k -> 1.09 k T; actor hooks 252 T. X per update
  1,444-8,905 T (L1 ~4.5 k, was ~5.6 k).
- **Update model 8F7C -> 9907** (`copier_window_update_checks`): the capture hooks + window from each
  8F7C state; IRQs injected around every hook and the window entry. Game-code IRQs (and hook-lost,
  compensated ones) are matched to the original at the same game instruction - the hooks shift the
  game by X, and level code reads R between 8F7C and 8F92 (wall-time matching made L2 diverge).
- **Results.** Window-only 1,854 states: 0 failures, 9907 -41..+35 T, controls 7/7 x 40. Update 1,855
  states: 0 failures, 9907 -52..+42 T, 1,485 injections (550 lost and compensated, 873 anchored, 82
  in the post-check gap), 40 fast-switch runs, controls 7 x 40 (lost-IRQ R 39/40), wait >= 13.7 ms.
  L6 loading-prep quick PASS. m3 diagnostic NEX (hooks + window): boot checks PASS, MD5
  9baec6412f2c3b7974b0db74a7ab9b75 (`copier_window/cw_m3_build.json`). No JNext here; no hardware.
- **Data for 3b.** The head writes only 9878, A3F2-A6FD, A9A2-AB41, FFF2-FFF3 (L1 probe): the textmap
  compile's inputs (page-68 map, DC00+ tiles, FC00+ attributes) are stable inside the window.

### 7.1 First hardware result and fix (2026-11-08, nexclash `claude/inferno-m3-hw-bisect`)
- `Inferno_copier_window_m3_diagnostic.nex` MD5 9baec641... crashed on the user's Next every time
  (many vertical green bars). The m2 window-only diagnostic runs (level 1 reached; "Neznamy povel"
  is the game's own Czech command console: type START / S + Enter).
- Cause: z80tonex's tail keeps its 20-byte register block (BC' DE' HL' AF' IX IY BC DE HL AF) in the
  alt ROM at the slot1 address = `rom_end` 3945, written by the stub at boot. Milestone 3a's `caplo`
  started at 3948: `cap_in`/`cap_out`, called by every capture hook, were overwritten. Simulated boot
  of that NEX: 3945-3958 = `2000 2055 8953 4400 c0a0 3a5c fdbe 0000 c8a0 bbff`. The model never runs
  the stub; the boot check did not compare hook bytes afterwards.
- Fix: `caplo` from 3960 (cap_chk, cap_lost, cap_done), cap_in/cap_out moved into the capture block;
  asm `ASSERT cap_chk >= rom_end + 20`; CapturePatch and both snapshot patches refuse hook bytes in
  the register block (control: the 3a profile is refused); `--copier-window-build` boots the NEX in
  the simulator and requires every hook byte intact (new boot check "hook bytes after boot"). DMA
  program now sends 0xC3 (reset) after 0x83 like hlib_dma. Hook timing unchanged (same instructions).
- Model fixes found by the rerun (an L6 sample failure, 9907 -56 T): cap_lost starts while the pulse
  is still active, so the original is now anchored there too (it was left at wall time); its /INT
  wait loop costs 4 T, not 6 (CW_KSPIN; CAP_KLOST follows it); a "post-check gap" pulse is one no
  $C8 read saw (a read that saw it and did not compensate fails).
- New files: `Inferno_copier_window_m3_diagnostic.nex` (fixed, MD5 68340edf338f8e41c0f80cc432ba2af0)
  and `Inferno_copier_window_current_diagnostic.nex` (current window code, no hooks, MD5
  692a8d92f123bf2c8c4d7a623a3b251a). Gate: `copier_window/cw_m3_checks.json` (rerun).
- Hardware (user, 2026-11-08): both run; speed (enemies, scrolling, stopwatch) and beeper sound match plain Inferno.nex.

## 8. Milestone 3b: the 8F95 work in the window's waits (nexclash `claude/inferno-copier-window-m3b`)

Simulator only (uncontended T, 28 MHz read waits). Gate: `copier_window/cw_m3b_checks.json` (`--jobs 6`).

- **Coroutine.** prepare_frame + render_textmap (same results; copy `wk_prepare`/`wk_textmap`) run in
  page 69 on their own stack (1C40). cw_wait's coarse loop now runs down to `CW_FINE` = 12 ticks
  (was 128; the fine spin is unchanged); with work pending and >= 12 ticks to the deadline it calls
  `cw_work`: DI, saves window SP/IX/IY/BC in page 80, slice end = CTC count `CW_WKM` = 9 ticks before
  the deadline (at most 120 ticks) in IYl, clears $C8, ROM `wk_in` maps page 69. Polls (clear loop,
  every map cell: `LD A,1B / IN A,(3B) / SUB IYl / DEC A / JP M`) yield before the slice end; the yield
  saves SP (the map pointer), BC, DE, IX, PC, restores slots 1/2, reads $C8 last, ROM `wk_out` maps
  page 80 back. A pulse in the slice: wait for /INT to drop, then as cw_irq (IRQT + 94, RIRQ + 10,
  NIRQ + 1, IRQRAW = count at the slice start). The first slice of each window restarts the work.
- **8F95.** In work builds 8F95 is `JP wk_hook` (ROM: DI, 28 MHz, $C8 cleared, page 69): `wk_frame`
  saves the game registers (1C80), reads R, finishes a suspended work or runs it all (polls jumped
  over by a self-modified JR: no CTC reads), restores everything, R = entry R + WK_KR (+10 when $C8
  shows a lost pulse), LD A,(AC49), EI, 3.5 MHz, JP 8F98. The legacy frame_hook is not used.
- **Model** (`run_cw_window(frame=True)` + `run_cw_frame`): 8F7C -> 9907 as in §7, then the original
  runs 9907 -> 8F95 with one limiter IRQ; from that state the work patch's 8F95 runs to 8F98:
  registers incl. R and RAM equal to the original; page 14, page 69 results and page 68 equal
  `run_frame` (FramePatch, all work at 8F95) from the same state and the capture at window entry.
- **Results (gate, 0 failures).** Window-only 1,854 states: 9907 -41..+34 T, cells 0/1 up to 142 T
  late (138 in m3a: the entry reads CW_WKEN). Update 1,855 states: 9907 -51..+45 T, X error
  -14..+20 T; work finished in the window 1,626 (88 %), resumed at 8F95 42, no slice 187 (10 %:
  busy beeper, every gap < 12 ticks); 17,833 slices; 8F95 added 168 T when done in the window, up
  to 24.7 k T (7 ms) when not (all work at 8F95 before: 15.6-23.6 k T). 1,815 IRQ injections incl.
  inside slices, 40 inside the 8F95 hook (lost, compensated). Controls: the 7 of §7 + work ignoring
  the slice end, slice pulse not counted, yield losing SP (37/37 states with >= 2 slices), 8F95 lost
  pulse not counted (40/40). CW_WKM over 64 half-T CTC phases (12 states, 768 runs, 15,261 slices):
  >= 108 T from any slice end to the next OUT/9907, no errors (`cw_m3b_margin64.json`,
  `probe_cw_margin64.py`). L6 loading-prep quick PASS.
- **NEX** `Inferno_copier_window_m3b_diagnostic.nex` (hooks + window + work; page 69 in bank 34's upper
  Hardware (user, 2026-11-08): gameplay ok.
  half): boot checks PASS incl. hook bytes after boot, MD5 2ca871c6d19550055811fb35ec299bd4.
- **Open.** Busy-beeper updates still do the whole work at 8F95 (slip/shorter filler there: §1 table,
  "+5 ms"); finer slices need units < ~45 T or carrying the work to the next window. No hardware run.

## 9. Milestone 3c: unfinished work is dropped, not finished at 8F95 (nexclash `claude/inferno-copier-window-m3c`)

- Finishing at 8F95 (3b) put up to 7 ms after the limiter in the 10 % busy-beeper updates (no slice),
  eating their slack (§1). Carrying the work into the next window is not cheap: the next 8F7C
  overwrites the captured map it reads. 3c drops it: `wk_frame` restores R only; F_SCENE_READY and
  Q_READY stay 0 (a display would keep its last complete frame); the next window restarts the work on
  the new capture. The model checks a dropped frame writes nothing at 8F95 but readiness 0.
- Gate (`cw_m3c_checks.json`, `--jobs 6`): 0 failures; 8F95 156-160 T in every update; 1,626 frames done
  in the window, 229 dropped (12 %: 187 no slice, 42 unfinished); at most 6 consecutive drops (L6,
  first 2,000 frames; 3 on other levels); 9907 -51..+45 T; 11 update controls detected. L6 loading-prep
  quick PASS. NEX `Inferno_copier_window_m3c_diagnostic.nex` MD5 ac3be35a00830b05028fa766d568e307, boot
  checks PASS incl. hook bytes after boot. Open: drop runs on full recordings; hardware run.
