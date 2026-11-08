# Continue Inferno stage 2: copier window (handover, updated 2026-11-08 after milestone 3b)

Code: **bleughb/nexclash** main (milestone 3b merged from `claude/inferno-copier-window-m3b`).
Evidence: **bleughb/specnext** main (`build/copier_window.md` §7-8, `copier_window/cw_m3*_*.json`).

## Read first (in this order, nothing else end to end)
1. `nexclash/CLAUDE.md` and the "Next session" block of `games/inferno.md`.
2. `specnext/reference/inferno/build/copier_window.md`: §1-4 (pacing, milestone 1), §6 (milestone 2),
   §7 (milestone 3a: timed capture hooks, lost-IRQ compensation, cw_cal, DMA map copy), §8 (3b).
3. Code: `nexclash/inferno.py` from "Copier window" (`run_cw_window`, `copier_window_update_checks`,
   `copier_window_update_controls`, `run_cw_frame`, `CopierWorkMemory`); `asm/inferno_hooks.asm`: capture kernel
   (`cap_in`/`cap_out`/`cap_chk`/`cap_lost`), "Copier window" (`cw_tin`/`cw_tout`/`cw_cal`, `cw_wait`,
   `cw_work`/`cw_wkback`) and the 3b coroutine (`wk_enter` .. `wk_end`, page 69 0C00).

## Setup
Clone both repos side by side; specnext as a sparse checkout of `reference/inferno`.
`pip install -r requirements.txt`. Assemble only with `python tools/asm2profile.py inferno`.
Diagnostic NEX: `--copier-window-build ../specnext/reference/inferno --cw-work --out DIR` (3b; `--cw-hooks`: m3).

## Check workflow (MANDATORY for every agent session; the owner paid for 20+ sessions to get here)
Base command (CMD): `python -m nexclash.inferno --copier-window-checks ../specnext/reference/inferno
--quick 2000 --cw-x ../specnext/reference/inferno/build/copier_window/capture_x.json --cw-cache C/st --jobs 6`
(`C/st` = a scratch prefix outside both repos: one ~40 MB pickle per level, written on first use,
never committed). Each state's CTC phase and its IRQ/control sample depend only on (level, index),
so a subset checks exactly the cases the full run checks.
1. Failures first: `CMD --cw-only 3:182,6:27 --json F.json` (seconds). Rerun the states the last run
   failed after every fix; a fix is not tried on the full set until they pass.
2. Systematic errors: `CMD --cw-sample 10 --json S.json` (~2 min, all six levels, IRQ injection on
   the sampled every-50th states). Read the error budget there: d9907 and OUT offsets must stay
   inside +-56 T with margin; if X error + window spread cannot fit, no constant shift will.
3. Gate, ONCE per change set, before commit: `CMD --json GATE.json` (all states, ~4-5 min with
   `--jobs 6`; ~20 min serial). Exit 0 and empty `failures` (window-only and `update`) or no merge.
4. Calibrated constants (K*, KR*, KLR, KLOST, KRB, KPAD, KH8, KTPAIR, M1K): calibrate over all 64
   half-T CTC phases (scratch probe, not 5 phases), then steps 1-3.
Never run the full set to find out whether a fix works; never commit with a gate older than the code.
Record in the hand-over which step last passed and on which commit.

## Done
- Milestone 2 (window at 8F92, OUT replay, pad): §6.
- Milestone 3a (§7, bleughb/nexclash#136): capture hooks measure X on the CTC and restore R; lost
  IRQs under DI are compensated from NextReg $C8 (hooks and the window's entry span); cw_cal measures
  the speed switches once; 8F7C map copy by zxnDMA. Update model 8F7C -> 9907 with IRQ injection and
  controls. Last gate (step 3, full, `--jobs 6`): 0 failures on the commit merged with #136.
- Milestone 3b (§8): the 8F95 work as a page-69 coroutine in cw_wait slices, finished at 8F95 (R
  restored there). Model 8F7C -> 9907 -> 8F98: page 14/69/68 = run_frame. Last gate (step 3, full,
  `--jobs 6`): 0 failures, on the sources merged with the 3b PR (MD5s in the record, milestone3b).

## Decisions (do not reopen without new measurements)
- Milestone 2's list stands (lockstep OUT replay, accumulate X, CTC ch 3 / prescaler 256, cell 415
  after the epilogue, tolerance 56 T).
- X per hook = 32 x ticks between an entry edge (synced) and an exit edge (run to), + 3.5 T x the
  check that saw the entry edge (cw_edge: 12 unrolled checks; a looped sync's 6 T gaps summed over
  ~20 hooks put 9907 outside +-56 T), + K (calibrated over 64 CTC phases), + CW_KT.
- A game ISR taken on a site's JP needs no correction (it precedes the entry edge; its M1 are in the R
  read). Do not add a stack-evidence check: it double-counted.
- $C8: cleared right after NEXTREG 7,3 (<= 24 T after DI), read last with IN A,($3B) ($C8 preselected
  by cw_tout). Hardware assumption: a clear during an active pulse does not take (Rainbow evidence).
- Speed-switch costs are measured on the machine (cw_cal), never assumed.

## Next
1. User hardware result of `Inferno_copier_window_m3b_diagnostic.nex` (checklist in games/inferno.md).
2. Busy-beeper updates (10 % of states): every cell gap < 12 ticks, so no slice; the whole work
   (4.5-7 ms) stays at 8F95 and eats that update's slack (§1: slips/shorter filler). Options: units
   small enough for ~45 T per gap (poll + fast cell ~22 T; a source cell is up to ~120 T), or carry
   unfinished work to the next window (a frame late; fine while no display shows it). Measure first.
3. Shrink the actor hooks (252 T each; 8F7C 1,082 T); then the earlier items (live-table scan, runtime
   exact dispatch, complete frame state, protected uploads). Keep sprites disabled.
3b constants: CW_FINE 12, CW_WKM 9 (margin >= 108 T over 64 phases), WK_KR -24 (R at 8F95; checked
on every state). Recheck with `probe_cw_margin64.py` after any change to the work loops or yield path.

## Hardware findings
- 2026-11-08: the first m3 NEX crashed (green bars): hooks sat under the stub's register block
  (alt ROM `rom_end`..+19). Fixed (§7.1, bleughb/nexclash#142; gate 0 failures, controls 40/40); the fixed m3
  and the window-only NEX run on the user's Next with speed and beeper sound matching plain Inferno.nex (2026-11-08). Any new alt-ROM block must start >= rom_end + 20; the build's
  "hook bytes after boot" check must stay empty.

## Hardware (user)
`Inferno_copier_window_diagnostic.nex` (m2, window only) and `Inferno_copier_window_m3_diagnostic.nex`
(hooks + window + cw_cal + DMA) against plain `Inferno.nex`: checklist in games/inferno.md.

## Pitfalls already paid for
- 3b: a hand copy of render_textmap put `.pair` before ADD HL,HL (doubled HL on the source path);
  only the page-14 comparison with run_frame caught it. Keep result equality for every copied routine.
- The work may touch only SP/BC/DE/HL/IX/IYl and A/F: the window keeps AF' and the alternate set live
  across cw_wait, and IY points at CW_PREV (saved by cw_work).
- The IM2 JR at FFFF reads its offset from 0000: whatever is mapped in slot 0 decides where an IRQ
  goes. Page 80 byte 0 = offset to cw_irq; pages 68/69 must stay DI.
- At 28 MHz an ISR that EIs at once re-enters on the same /INT pulse (32 T): hooks EI before
  NEXTREG 7,0 so the IRQ is sampled after the switch; cw_irq delays its EI.
- Between a hook's last $C8 read and the IRQ sample after EI + NEXTREG 7,0 there must be < 32 T; the
  model charges the switch 24 T, leaving a ~6 T gap per hook exit (reported, not compensated).
- CW_M1K/KR/KLR (R) and K/KRB/KPAD (T) are calibrated constants: recalibrate after any path change
  (zero, read the offset over all CTC phases, set, rerun).
- Calls and IRQ pushes in the window leave bytes below the copier's SP; 9907's PUSH DE / PUSH HL
  overwrite exactly those 4 first. Game-code IRQs before 8F92 land on other instructions in the two
  runs: their pushes are garbage below the caller's SP (the model allows exactly those addresses).
- Tile graphics are mutable mid-level (F400-FA36; L3 ED00-F0AF): keep exact byte validation.
- doccheck on a Windows checkout counts CRLF bytes; `games/inferno.md` must be <= 25,000 with LF.
- Bash heredocs with quotes/backslashes fail in this environment's tool: write edit scripts to files.

## Constraints (unchanged)
Original RAM/registers/R, actor draw order, approved B appearance, caller speed and ORIGINAL pacing
and sound. Sprites stay disabled until the complete pipeline passes. Report costs in ms, separating
simulator models, executed assembly and hardware.
