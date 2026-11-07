# Continue Inferno stage 2: copier window (handover, updated 2026-11-07 after milestone 2)

Code: **bleughb/nexclash** branch `claude/inferno-copier-window-m2` (from main 7a23697, which holds
milestone 1). Evidence: **bleughb/specnext** branch `claude/inferno-copier-window`. `codex/inferno`
(PR bleughb/nexclash#96) is superseded and not continued (user, 2026-11-07).

## Read first (in this order, nothing else end to end)
1. `nexclash/CLAUDE.md` and the "Next session" block of `games/inferno.md`.
2. `specnext/reference/inferno/build/copier_window.md`: §1-4 (pacing, milestone 1), §6 (milestone 2).
3. Code: `nexclash/inferno.py` from "Copier window" (`run_cw_window`, `copier_window_checks`,
   `CopierWindowSnapshotPatch`); `asm/inferno_hooks.asm` from "Copier window" (`cw_wait`, `cw_irq`,
   `cw_head`, `cw_done`).

## Setup
Clone both repos side by side; specnext as a sparse checkout of `reference/inferno`.
`pip install -r requirements.txt`. Assemble only with `python tools/asm2profile.py inferno`.
Checks (about 15 min): `python -m nexclash.inferno --copier-window-checks ../specnext/reference/inferno
--quick 2000 --cw-x ../specnext/reference/inferno/build/copier_window/capture_x.json --json OUT.json`.
Subset while iterating: cache `_cw_states` once (pickle) and run every Nth state.

## Done: milestone 2 (window installed at 8F92, no hook work in it)
Each change of the copier's OUT value is OUT at its original T and 9907 is entered at the original
time, polled on CTC channel 3; frame IRQs inside the window enter `cw_irq` (page 80 byte 0 is the
IM2 JR offset) and add the original no-op ISR's 94 T / 10 M1. Diagnostic NEX
`build/Inferno_copier_window_diagnostic.nex` (window only, X = 0) passes the boot checks. Numbers: §6.

## Decisions made in milestone 2 (do not reopen without new measurements)
- "Run the head, then replay" cannot work: the first OUT is due 244 T after 9790, the head takes
  ~5 ms. Replay is lockstep in the head's change branch; OUT values (A700) and times (tile map) do
  not depend on the head's own writes.
- X (earlier hooks): **accumulate**. A bounded shift needs X <= 169 T; capture hooks measure
  3,198-7,642 T. With X the first ~X of the burst is late (OUT at once), the rest and 9907 exact.
- Clock: CTC ch 3, prescaler 256 (32 T in every video timing), polled; time base = first edge
  after entry, timed by the sync loop. Raster ($1E/$1F, 216-228 T a line by mode) cannot time
  187 T OUT spacing; the fallback without a counting CTC is the original copier (CW_CLK = 2).
- Cell 415's OUT is deferred until after the row end and epilogue (the original's 169 T from it to
  9907 are too short for them); one deferred cell is all the 187 T spacing allows.

## Next: milestone 3 - X measured on hardware, then hook work in the window
1. Capture hooks (8F7C/959B/96A1): read the CTC at entry/exit, accumulate X (T) in page 80
   (`CW_X`), and restore R (they do not today: R is read by L6 game code BA22/BB89/BB8E). cap_done
   currently copies nothing; its DI span (plus the sync) loses 0.09 % of frame IRQs.
2. Move post-copy work (8F95: scenery compile, validation, dispatch, uploads, queue) into the
   window: `cw_wait` is the place (work units while the deadline is ahead). Free time per update,
   full recordings: min 14.6 ms, p1 15.3-17.5 ms.
3. Shrink X itself (the 8F7C map copy is ~3.2 k T of it): a late burst prefix is audible only as
   ~X of compressed edges, but smaller X means fewer.
4. JNext `nexclash.pace` (not available on the machine that did milestone 2) and the user's hardware
   test of the diagnostic NEX (checklist in games/inferno.md) before relying on the window.

## Pitfalls already paid for
- The IM2 JR at FFFF reads its offset from 0000: whatever is mapped in slot 0 decides where an IRQ
  goes. Page 80 byte 0 = offset to cw_irq; page 68 (capture) must stay DI.
- At 28 MHz an ISR that EIs at once re-enters on the same /INT pulse (32 T): cw_irq delays its EI.
- CW_M1K (R) counts M1 from 8F92 to the R read and after `LD R,A`; any change there needs a
  recalibration (zero it, read the constant offset, set, rerun). KRB/KPAD likewise centre the OUT
  and 9907 offsets (`work/probes`-style subset run: mean of `dts` and `d9907`).
- Calls and IRQ pushes in the window leave bytes below the copier's SP; 9907's PUSH DE / PUSH HL
  overwrite exactly those 4 first. The verifier checks it by running the two pushes.
- Tile graphics are mutable mid-level (F400-FA36; L3 ED00-F0AF): keep exact byte validation.
- doccheck on a Windows checkout counts CRLF bytes; `games/inferno.md` must be <= 25,000 with LF.
- Never install the head without the pad.

## Constraints (unchanged)
Original RAM/registers/R, actor draw order, approved B appearance, caller speed and ORIGINAL pacing
and sound. Sprites stay disabled until the complete pipeline passes. Push or open a PR only when
the user asks. Report costs in ms, separating simulator models, executed assembly and hardware.
