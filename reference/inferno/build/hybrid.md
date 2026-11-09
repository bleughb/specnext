# Inferno hybrid renderer: dependency map and plan — 2026-11-09

Question: can original gameplay run with the copier replaced? Evidence is from replays in the simulator
(`hybrid/`, first 2,500 frames per level), not hardware.

## Result
Skipping `CALL 9790` entirely (copier, 9907 limiter, filler) and running consecutive updates from the recording's
inputs gives RAM identical to the original at every 8F92, on levels 1, 2, 3, 4 and 6, outside display memory and the
copier's own pages, **provided the values read by `LD A,R` are supplied**. Without them levels 3, 4 and 6 diverge
(for L6 the first control-flow difference follows an `LD A,R`); level 1 has no such read in these frames.
Level 5's run left gameplay at update 61 of 92 and is not evidence past that point.

## Dependency map
| Question | Answer | Evidence |
|---|---|---|
| Copier/filler writes consumed by gameplay | None. Only the copier's stack unwinding at 9993-99A2 reads them. | `probe_taint.py`, L1/3/4/6 |
| Gameplay logic inside the copier (correction) | **Yes, on a path these replays did not exercise.** 9804: `CALL Z,9881` when AC47 = 0 changes AD33, AC57, AD34, 9A80, A902 and a countdown ending `JP Z,8FF7`. A replacement must keep this call. | disassembly |
| Register results consumed | Alternate BC/DE/HL differ after a skip with no effect on game RAM. | `probe_skip.py` |
| Outputs only for the display | ULA 4000-5AFF. Pages 98, 99, A2-A7, A9-AB, AD are the copier's own working state; A1 also differs on L6. | taint, skip |
| Inputs of the copier | Tile map 9B00-9FFF, graphics DC00+, attributes FC00+. | `probe_deps.py` |
| Sound | Beeper OUT sites: 97C5 (copier replays A700), 993C (filler), A459 (game code; not yet analysed). The filler writes A700 and uses R. | census, `copier_window.md` §2 |
| Cadence | 9907 waits for the frame IRQ after the head, so an update lasts whole frames: 13,869 updates in 61,721 L1 frames, about 4.4 frames each (including non-gameplay frames). | `copier_window.md` §1 |
| R | Gameplay randomness on some levels: `LD A,R` in level code (BB8B on L6). Its exact value only matters for matching a recording. | skip with and without R |
| Game reads of the screen | 81AA/81B0, 8290/82A3, 9039/9066, 90BE, none of bytes the copier wrote. They need the game's own HUD and transition writes to stay. | deps + taint |

Consequences: exact R, the capture hooks' timing compensation and the copier's RAM effects were requirements of the old
architecture. R becomes an ordinary random source; a replay comparison must feed recorded values.

## Update time (`hybrid/probe_budget.py`, original game, T-states, medians; 2,500 frames, L1-6)
An update is exactly 4 frames, 279.5k T, sometimes 5. Head 92-102k, 9907 to the resuming IRQ 45-81k, tail 41-67k (it also replays OUTs at 97C5), game and producers 65-79k.
Idle after the filler ends (`JR $` at 9989) is not used yet: `copier_window.md` §1 gives a median near 27k T but p1 near 1.4k T.

## First visible diagnostic (nexclash `claude/inferno-sprites-visible`, draft)
Sound and pacing path unchanged. Live CAP_LOG data -> dispatch -> selection -> upload -> sprite attributes over the original ULA scenery. Simulator: gate 0 failures over 1,855 states, 1,489 published frames with exact patterns and attributes; dropped 366 (19.7 %), longest run 35, slice margin 66 T. Hardware not run.

## Prototype plan (level 1 first)
Hypothesis: with the copier replaced, one update publishes a complete display within the original cadence.
Success criteria, measured from timestamps: every update published at L1's busiest scenes, longest miss run under 3 updates,
original update cadence within 2 %, sound recognisable beside plain `Inferno.nex`, gameplay RAM equal to a replay with supplied R.

1. At 8F92 call a new routine in place of 9790. It keeps the limiter's cadence with its own frame wait and plays sound.
2. Sound first: keep the existing OUT replay and filler path, without the screen writes; analyse A459. Hardware check by ear.
3. Scenery: tilemap from the clean map at 8F7C (9B00), or Layer 2 where tile colours need it; atomic publish.
4. Actors: reuse dispatch, selection and uploads, now with far more time. Expand the store to 128 patterns: 4-bit patterns use both halves of the 16 KB and the addressing already handles it; masks and protection must grow to match.
5. Sprite attributes from the frame list, published at vblank; the first NEX shows the player, then every actor.
6. Measure publication rate and display age from timestamps; two failed experiments against one constraint trigger reassessment.

Not known yet: cost of the replaced path on hardware; what A459 does; whether the HUD stays on the ULA with the layer priority chosen; level-transition and restart behaviour with the replacement.

Hardware (user, 2026-11-09), sprite NEX MD5 5c01017210b9cc4575147106f1e33964: game runs and plays; ghosting of the ship when moving and in attract mode, like bad vsync; accepted as work in progress.

Hardware (user, 2026-11-09), scenery NEX MD5 fcf9c25ba6dc1f7e2355125c12450134: looks right. No detailed measurements. Modal screens, lag and tearing not reported on.

Hardware (user, 2026-11-09), exit-hook NEX MD5 2b50e783ea116e2841ea3b5b358f9ec7: menu after the ship is destroyed is fixed. Restart from the menu, pause and the level-4 shop not reported.

Hardware (user, 2026-11-09), write-out NEX MD5 4a839a3b0e084e7e612f6ba2b09e1b04: lag better, speed and sound unchanged by the user's report. Not measured.

Hardware (user, 2026-11-09), exit-fix NEX MD5 4b28d334035439373d49cd5ef36d17b6, Copper publish included: works, game plays well, ship death and menu OK. Freshness not measured.

Hardware (user, 2026-11-09), per-level NEXes with tape descriptors kept (L6 MD5 3eec75dbe6626b21ba451cf8c127c15e): level 6 works; pressing S after dying loads level 1; other levels appear to behave the same. Not all levels fully tested; shop and level-to-level progression not reported.

Hardware (user, 2026-11-09): level 4 also works and loads level 1 after S. 128-pattern store: full gate 0 failures over 1,855 states, slice margin 109 T, 0 evictions in the gate; NEXes not yet run on hardware. Shop: leaves gameplay at frame 51,805 through 9019-901C (frame_pipeline.md); not run on hardware.

FLASH census (probe_flash.py, simulator; images at 8EF9, every 8th update of the first 2,000 frames): L1 4 of 103 images have a FLASH tile, 1 of 295 sampled draws; L2-6 none; scenery none in any level. Phase 1 not needed for now; recheck the four L1 images if they look wrong.

Hardware (user, 2026-11-09), 128-pattern store NEXes: several levels work and load level 1 after S. FLASH phase 1 (four L1 images): full gate 0 failures, margin 109 T, not run on hardware. Menu text lists START, PILOT, SAVE, LOAD, RAPORT, REDEFINICE, INFORMACE, ZBRAN, POMOC, KONEC (first letter is enough); SAVE and LOAD untested.

Full-game NEX (tape start) stalls at the loading screen on JNext and on the Next, silently. Loader-only NEX reaches the menu; full build with the USR redirect disabled also stalls, so the redirect is not the cause. Post-boot state differs only in alt ROM 3960-3CF8; the simulator plays the intro music with that ROM, so the cause is not found. Per-level NEXes are unaffected.

Hardware (user, 2026-11-09), full-game NEX MD5 227c2422bcac56dca7840d38b425fc49: reached play with sprites; reported working. Cause of the earlier stall: the intro uses IM 2 with I = 3B, reading its vector from ROM 3BFF-3C00, which hook bytes had overwritten. Found with JNext headless (1.2.0).

JNext 1.2.0 headless, end-of-level-1 snapshot under the sprite build: debrief and medals screen correct, command prompt, attract demo with correct tilemap and sprites. A scripted S press did not start the next level (the attract loop continued), so level-to-level progression remains untested.

JNext 1.2.0 headless, end-of-level-1 snapshot under the sprite build: a short S then ENTER at the prompt loads the next section; the story screen follows, Enter advances it, and the next level plays with HUD, equipment list, tilemap and sprites. Keys must be short presses in the script (JNext holds auto-repeat). Equipment carry-over compared by eye only.

JNext 1.2.0 headless, end-of-level snapshots with S, Enter and Enter presses: L2, L3 and L5 reach the next level in play with HUD and sprites; L6 reaches the ending text; the outro snapshot plays its text. L4 showed the attract demo at the sampled frame, so its transition is not confirmed. Shop not run.
