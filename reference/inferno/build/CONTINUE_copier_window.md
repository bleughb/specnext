# Continue Inferno stage 2: copier window (handover, 2026-11-07)

Branches: `claude/inferno-copier-window` in **bleughb/nexclash** (code) and **bleughb/specnext**
(evidence). Both start from `codex/inferno` (nexclash 4bfa72c, specnext 488a9bd) and contain all
of it. This is now the ONLY Inferno line: `codex/inferno` (GPT-6 Astra, PR bleughb/nexclash#96)
is superseded and not continued (user, 2026-11-07). Its open items are carried in this branch.

## Read first (in this order, nothing else end to end)
1. `nexclash/CLAUDE.md` (rules, token discipline) and the "Next session" block of `games/inferno.md`.
2. `specnext/reference/inferno/build/copier_window.md`: measurements, decision, milestone 1 evidence.
3. `games/inferno.md` "Copier window" and "Approved design" sections.
4. Code: `nexclash/inferno.py` `cw_out_t`, `CopierWindowPatch`, `CopierWindowMemory`, `run_cw_head`,
   `copier_window_checks`; `asm/inferno_hooks.asm` from `cap_done_tail` and the block after
   "Copier window, milestone 1" (`cw_go`, `cw_exit`, `cw_head`).

## Setup
Clone both repos side by side (`nexclash/`, `specnext/`) and check out the branch in each. specnext
is large; a sparse checkout of `reference/inferno` is enough. `pip install -r requirements.txt`.
Assemble only with `python tools/asm2profile.py inferno` (bundled sjasmplus); new exported symbols
need `--add-sym NAME`. Smoke test:
`python -m nexclash.inferno --copier-window-checks ../specnext/reference/inferno --quick 2000`
(about 70 s; expect 1,854 states, no failures, controls detected).

## Why this branch exists (one paragraph)
Inferno is paced by its own limiter 9907, which the copier calls after row 6. After 9907 the game
plays beeper sound until the next interrupt resumes the copier. Slack after 9907 is often below
1 ms, so any hook time added before 9907 slips frames (+10 ms slips 56–81 % of updates) and
shortens sound. The copier head (9790..97FB, 25–31 ms) also *plays the beeper*: one
`OUT (254),A` per cell from the A700 buffer. Plan: run a translated head fast, replay its OUTs at
their original T, pad to the original 9907 time, and do hook work in the freed ~19 ms.

## Done (milestone 1)
The translated head (page 80, 293 bytes) is exact against the original on 1,854 states of six
levels: all registers incl. R, all RAM, and every OUT change (value plus original uncontended T,
`cw_out_t`). Three negative controls are detected. Cost ≤ 7.6 ms. It is **not installed**: on its
own it would make the game run faster than the original.

## Next: milestone 2 — sound replay and pad, no hook work yet (recommended order)
Goal: an installable 8F92 path that is pace- and sound-equivalent to the original by
construction. It is the hardware test vehicle before any work moves into the window.

1. **Clock.** Pick the wall clock for replay and pad. The repo's guidance for hook timing is the
   copper or a `$1E/$1F` raster poll (TECHNIQUES §1, near "Line interrupt"). A raster line is 224 T;
   CTC (TECHNIQUES §2, near "Sample sound by CTC timer interrupt") gives finer counts. Recommended:
   **poll, no interrupts**. Busy-wait on the clock, OUT each logged change at its time, then wait
   for the 9907 target. Do NOT enable line or CTC interrupts under the game in pulse mode: they
   raise the same /INT and run the game's ISR (TECHNIQUES "Line interrupt", and the CTC gotcha
   "CTC interrupts arrived although $C5 was 0"). Gate CTC use by core version with a raster
   fallback, as DDMA is gated.
2. **Time base.** Replay offsets are relative to the *original* 9790 entry. The hook enters later
   than the original by X = the time the earlier hooks this update added (8F7C/959B/96A1 capture,
   cap_done). Either accumulate X (each hook adds its own measured elapsed time), or accept a
   bounded shift: play the burst X late, keep its internal timing, and still pad to the original
   9907 time. That is only possible while X ≤ (head T − last OUT T). Decide from measurements and
   record which.
3. **Model first, in the simulator.** Extend `CopierWindowMemory` with a clock model (28 MHz T
   with read waits, the existing `elapsed` accounting) and a port-FE write log. Check per state:
   OUT values equal the original stream's changes; each OUT time − original OUT time is a
   constant offset (within the clock's resolution); the 9907 entry time equals the original's.
   Then six-level quicks plus the full recordings (88,187 updates) using the timeline model.
4. **Interrupts.** The window runs DI, so a frame IRQ during it is lost in pulse mode. That is
   harmless only while 998E = 0 (the ISR is then a no-op). Prove 998E = 0 for the whole window,
   which is true by construction: it is set only at 9914. Add the injection test (LEARNINGS:
   deliver an IRQ at ~20 points across the hook's own length) and the per-update rule that bytes
   differing because of IRQ pushes lie below the copier's final SP and are never read
   (copier_window.md §4).
5. **Install path.** Only when 1–4 pass: a patch/profile option that installs the window at 8F92
   in a diagnostic NEX (like `Inferno_capture_diagnostic.nex`), boot checks, then JNext
   `python -m nexclash.pace` against the original for pace and sound (docs/CHECKS.md). Hardware:
   ask the user (Dean) to compare beeper sound and speed against the plain `Inferno.nex`.

## Then milestone 3 — hook work in the window
- Move the post-copy work (scenery compile, exact validation, dispatch, uploads, queue) from 8F95
  into the window, between OUT deadlines. Options: (a) cooperative work units short enough to keep
  OUT jitter within a measured bound (OUT spacing is ≥ 187 T ≈ 53 µs at 3.5 MHz); (b) hardware IM2
  mode during the window with CTC-timed OUTs (BRIEFING C2 #34, TECHNIQUES "Held interrupts").
  Note that hardware IM2 forces the DDMA path to its CPU fallback (DDMA_IMPLEMENTATION.md). Choose
  by measurement.
- Deadline rule: unfinished work publishes nothing; the previous complete frame stays.
- Measure whole updates against the new gate: zero frame slips and the original 9907 time, sound
  unchanged. This replaces the 10 ms total target.
- Optional speed-up: the head is unoptimised (~42 instructions/cell); a faster head enlarges the window.

## Pitfalls already paid for
- The IM2 vector lands on FFFF (`JR` to FFF4, 12 T). Exclude FFFF with the ISR when timing
  foreground code.
- The tile ≥ 16 path is 12 M1, not 10. The R constant `CW_M1K` (0x3A) is end-to-end
  8F92→9907 and must be recalibrated after any change to cap_done or cw_head (zero it, run, read
  the constant offset, set it, rerun everything).
- Tile graphics are mutable mid-level (F400–FA36; L3 ED00–F0AF). A 2,000-frame quick did not show
  it; full recordings did. Keep exact byte validation.
- `--loading-prep-check` takes the `.rzx`, not the `.z80`.
- doccheck on a Windows checkout counts CRLF bytes. Every file it flags is within budget with LF.
  Write `games/inferno.md` with LF and keep it ≤ 25,000 bytes (it is 24.5 k).
- Never install the head without the pad: it removes ~20 ms per update and the game speeds up.

## Constraints (unchanged)
Preserve original RAM/registers/R, actor draw order, approved B appearance, caller speed and
ORIGINAL pacing. Protect current and pending resources. Cold misses, overflow and incomplete work
keep the previous complete frame. Keep gated DMA/DDMA, no-blitter and CPU fallbacks. Never treat
sampled content as a complete catalogue. Sprites stay disabled until the complete pipeline passes.
Commit to the `claude/inferno-copier-window` branches. Push or open a PR only when the user asks.
Report costs in ms, separating simulator models, executed assembly and hardware evidence.
