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
| Register results consumed | Alternate BC/DE/HL differ after a skip with no effect on game RAM. | `probe_skip.py` |
| Outputs only for the display | ULA 4000-5AFF. Pages 98, 99, A2-A7, A9-AB, AD are the copier's own working state; A1 also differs on L6. | taint, skip |
| Inputs of the copier | Tile map 9B00-9FFF, graphics DC00+, attributes FC00+. | `probe_deps.py` |
| Sound | Beeper OUT sites: 97C5 (copier replays A700), 993C (filler), A459 (game code; not yet analysed). The filler writes A700 and uses R. | census, `copier_window.md` §2 |
| Cadence | 9907 waits for the frame IRQ after the head, so an update lasts whole frames: 13,869 updates in 61,721 L1 frames, about 4.4 frames each (including non-gameplay frames). | `copier_window.md` §1 |
| R | Gameplay randomness on some levels: `LD A,R` in level code (BB8B on L6). Its exact value only matters for matching a recording. | skip with and without R |
| Game reads of the screen | 81AA/81B0, 8290/82A3, 9039/9066, 90BE, none of bytes the copier wrote. They need the game's own HUD and transition writes to stay. | deps + taint |

Consequences: exact R, the capture hooks' timing compensation and the copier's RAM effects were requirements of the old
architecture. R becomes an ordinary random source; a replay comparison must feed recorded values.

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
