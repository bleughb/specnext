# Reference games (private)

One folder per game: the original snapshot and Dean's recordings (the references the toolkit is
verified against), and the built games: `<game>.nex` (plain) and `<game>_sprites.nex` (the
modified game), exactly as `python selftest.py` (in nexclash) rebuilds them. Game notes:
nexclash/games/<folder name>.md (one per game, same name as the folder). Never copy anything from here into the public repo.

selftest.py copies each game's inputs from the `path` its record (nexclash docs/records/<game>.json)
names under reference/ and checks their MD5s: keep file names and folders as listed here. It expects
../specnext next to the nexclash clone (or NEXCLASH_REFERENCE=path/to/reference).

## Chuckie Egg - `chuckie_egg/` (games/chuckie_egg.md; hardware: untested)

| File | MD5 | What |
|---|---|---|
| Chuckie_Egg.rzx | 7697943d44c33dbef1c073332e36dfc0 | recording (RZX) |
| Chuckie_Egg.z80 | cddc0cfea8259d0c497b50fae0acd27e | snapshot |
| chuckie_egg.nex | ec0df71e70fae35836eaed521f300777 | plain conversion |
| chuckie_egg_sprites.nex | bfad6be1e7c8a2c797a6242d7f339e35 | modified game (sprites) |

## Smash TV - `smash_tv/` (games/smash_tv.md; hardware: untested)

| File | MD5 | What |
|---|---|---|
| Smash_TV.rzx | ed4ee1a08ce14101cb7b1246dcdaf040 | recording (RZX; Fuse autosave on: 8 autosave snapshots, stripped by `auto`; title, arenas 1-2, game over; N = not invulnerable) |
| Smash_TV.z80 | 3b89344c6d7e6433bf044bef1880a2f1 | snapshot (BASIC loader at the trainer prompt "DO YOU WANT TO BE INVULNERABLE ?") |
| smash_tv.nex | c72ea298486b14036ac1a87ac89c3f0e | plain conversion (the loader as it is) |
| smash_tv_sprites.nex | 03979d5438cf55410ecec8aac76f05ec | modified game = the record's build (every figure 4-bit sprites in its cell inks, see-through outline; pattern cache; prompt front end; supplied by Dean 2026-10-14) |
| smash_tv_sprites_outline_cell_paper.nex | 6227481f8f2514faa0d9648b6bc972e8 | variant, not the record's build (every figure as sprites in its cell inks, outline in the cell paper; prompt front end) |

## Midnight Resistance (128K) - `midnight_resistance/` (games/midnight_resistance.md; hardware: e8f0ece9 runs, Dean 2026-10-13; 670f9403 tests OK, Dean 2026-10-14)

| File | MD5 | What |
|---|---|---|
| Midnight_Resistance_1990_Ocean_128K.rzx | b75ecd5f60c3ec67fe463a0aa606f6a1 | recording (RZX; 8 autosave snapshots, stripped by `auto`; title, level 1 to the tank, game over) |
| Midnight_Resistance_1990_Ocean_128K.z80 | 67bf05d356d51b2b402d88c5f0cdfb21 | snapshot (title screen) |
| midnight_resistance.nex | 17239acaaf67b0f8011478053e17829d | plain conversion |
| Midnight_Resistance_1990_Ocean_128K_V2RZX.rzx | 3e0fa52ae2fbf9fbae62cebb70b83190 | second recording (Dean 2026-10-13; autosaves stripped by `auto`; more of level 1, the shop) |
| midnight_resistance_sprites.nex | 670f94034af175ed56df97f8cdb1ef29 | modified game (every figure a sprite, also flipped and in the shop, in Dean's painted colours; sprites hidden on every loop exit) |
| midnight_resistance_PAINTING_SPRITES.png | - | sheet to paint: every graphic once, drawn in the current colours; grey = paintable, the rest of a box background (`python -m nexclash.midres sheet RZX RZX --z80 Z80`; regenerated 2026-10-14 after the autosave fix, nexclash #36) |
| midnight_resistance_PAINTING_SPRITES_layout.json | - | its layout: reads the painted sheet back (`python -m nexclash.midres colours`) |
| mr_colours_painted.png | - | Dean's first painting (2026-10-14; old single-sheet layout) -> docs/profiles/midnight_resistance_colours.json in nexclash |
| midnight_resistance_REFERENCE_ALL_SPRITES.png | - | every figure whole, as the build colours it (not read back); grey only where paintable (2026-10-14) |

## Commando (128K) - `commando/` (games/commando.md; hardware: 5ab928e9 runs; 5c1081b7 flicker/logo/dots; 541e34e2 crashed (code at 0x3D00, probably the DivMMC automap); d601385e runs)

| File | MD5 | What |
|---|---|---|
| Commando_1985_Elite_Systems_t_128K.RZX | b3350a66a14db07add43c878eb872169 | recording (RZX; 8 autosave snapshots, stripped by `auto`) |
| Commando_1985_Elite_Systems_t_128K.z80 | c9af5668191462d77c5859900268c24b | snapshot (BASIC loader, trainer version) |
| commando.nex | a206f950c12f58a8e7f26b366f5a2480 | plain conversion (starts in the front end) |
| commando_sprites.nex | d601385ee4aeb7f3d7c0771bdc27df6b | modified game (solid sprites with yellow body, solid objects by the walk-box depth rule, scenery restore, pattern cache) |

## Everyone's a Wally - `everyones_a_wally/` (games/everyones_a_wally.md; FROZEN 2026-10-14, superseded by everyones_a_wally_updated; hardware: boots and runs)

| File | MD5 | What |
|---|---|---|
| Everyone's A Wally.tzx | 538ad0852363e32bc75cfbc7debbf702 | tape image |
| wally.nex | 2e615b3e7ae995e6d6a6ed9e3f586d4d | plain conversion |
| wally.z80 | a9eeb555a327e5794b0ba19bc80dccf0 | snapshot |
| wally_sprites.nex | f7605489c3af55b8e8c6a580c1c26150 | modified game (sprites) |
| wallyrzx.rzx | 72c7d1f6c99407bc21d892d423e89964 | recording (RZX) |

## Everyone's a Wally, updated - `everyones_a_wally_updated/` (games/everyones_a_wally_updated.md; hardware: untested)

Inputs: the snapshot and recording of `everyones_a_wally/` (wally.z80, wallyrzx.rzx; the record's
input paths point there), not copied.

| File | MD5 | What |
|---|---|---|
| everyones_a_wally_updated.nex | 2e615b3e7ae995e6d6a6ed9e3f586d4d | plain conversion (= the frozen version's) |
| everyones_a_wally_updated_sprites.nex | 31c3ef131330d26238b01a69b35c647e | modified game: every figure on Layer 2, one colour each, black 4-neighbour outline, default colours (nothing painted yet) |
| everyones_a_wally_updated_PAINTING_SPRITES.png | - | sheet to paint: every graphic once with its outline ring, in the build's colours; grey = paintable (`python -m nexclash.wally2 sheet wallyrzx.rzx --z80 wally.z80`) |
| everyones_a_wally_updated_PAINTING_SPRITES_layout.json | - | its layout: reads the painted sheet back (`python -m nexclash.wally2 colours`, or `nexclash.py recolour`) |
| everyones_a_wally_updated_REFERENCE_ALL_SPRITES.png | - | every figure whole, as the build colours it (not read back) |
| everyones_a_wally_updated_preview.png | - | 8 shots, 2x: the original (left) and the build (clean ULA + the Layer 2 figures the model draws) |

## Rainbow Islands (128K) - `rainbow_islands/` (games/rainbow_islands.md; EXCLUDED from automatic selftest checks; hardware: cf017271 / diag c16751b0 untested (2026-10-19: no rainbow border, collectable insides); c5e1823d "seems better")

DEPRECATED (2026-10-21): superseded by `rainbow_z80n/` (below); these files stay as they are, and the
inputs here are also rainbow_z80n's inputs.

| File | MD5 | What |
|---|---|---|
| rainbow.nex | 7ac543fb51c7a3c4137778eeb3cdc175 | plain conversion |
| rainbow.rzx | 55046d1893bba0a4faf314ecd3a9638b | recording (RZX) |
| rainbow.z80 | 4c98b980b1726af545fccc99665ef29b | snapshot |
| rainbow_sprites.nex | cf017271dfc01bdd0c7cf2f599b03628 | modified game (sprites; no rainbow border, collectable insides black / white, thrown rainbow without outline) |
| rainbow_sprites_diag.nex | c16751b0255ee3d83a4e342bf9a8c411 | diagnostic build (border: blue = deferred commit, red = tile built, yellow = overrun, magenta = overrun flag unreliable) |
| rainbownew.rzx | 47bb2b163a947724c343a2bc1b039458 | recording (RZX) |
| leebee/rainbowislands_LeeBee.rzx | 92bbaa0a24102b3e5169d5c6432e4928 | whole-game playthrough (195,356 frames, all islands): do NOT replay in full - use the bookmarks |
| leebee/leebee_rNN_islandI_roundR.rzx, leebee_ending.rzx | (leebee_bookmarks.json) | BOOKMARKS: one RZX per round, starting where the round variable 0x636F changes (rzx.cut) |
| sheets/rainbow_islands_{PLAYER,ISLAND1-7,COLLECTABLES}_PAINTING_SPRITES.png + _layout.json | - | colour sheets to paint (whole figures, today's colours, collectables per colour; layout = read-back map) |
| sheets/rainbow_islands_*_REFERENCE_ALL_SPRITES.png | - | every figure / colour as the build draws it (not read back) |

## Treasure Island Dizzy - `treasure_island_dizzy/` (games/treasure_island_dizzy.md; hardware: plain runs)

| File | MD5 | What |
|---|---|---|
| dizzy2.z80 | 9443f0cc4c32415849b0419750f1bff3 | snapshot (title screen) |
| dizzy2_game.z80 | 7578947fcc8dbc4ba822e2c565499d54 | snapshot (in game) |
| dizzy2newrzx | 4d708b014db515382005dc2632244408 | recording (RZX) |
| dizzy2rzx | 973fee73fc535e48eb6b64382537c80d | recording (RZX) |
| treasure_island_title.nex | 70890aba7d821fba8a41e63636eb58be | plain conversion, from the title snapshot dizzy2.z80 |
| treasure_island_title_sprites.nex | 85e054fe4bce8e4b3a8e336aac432f58 | modified game (sprites), from the title snapshot dizzy2.z80 |
| treasure_island_dizzy.nex | 4dae1a3a15b2158642a5d5b82de92ef7 | plain conversion, from the in-game snapshot |
| treasure_island_dizzy_sprites.nex | 8b4d0847d68fce3215bd43a0e116e682 | modified game (sprites), from the in-game snapshot |

## Dizzy: The Ultimate Cartoon Adventure - `dizzy_ultimate_cartoon_adventure/` (games/dizzy_ultimate_cartoon_adventure.md; hardware: untested)

| File | MD5 | What |
|---|---|---|
| Dizzy_The_Ultimate_Cartoon_Adventure_1987_Codemasters.z80 | 0659328fd54fd446e39d1740bafd02e7 | snapshot |
| dizzy1.nex | 7892b2e0f1f3f9f19165516db307cbe0 | plain conversion |
| dizzy1_sprites.nex | fb4cb1482b3e337374ca99c3ff58edad | modified game: every figure on Layer 2 (shadow screen), Dizzy = hardware sprites in front, solid (enclosed paper black), Dean's painted colours (docs/profiles/dizzy1_colours.json); HUD and room tiles on the ULA (2026-10-14, nexclash #35: draws exactly as 38e1a491, only never-drawn paper nibbles differ; replaces 38e1a491 / 83ea050d) |
| dizzy1rzx | 99d9c4c086d06a46ba7a781e5321dc3e | recording (RZX) |
| dizzy1_PAINTING_SPRITES.png | 002c2c81d5bfc86a6e23804559e723bd | sheet to paint: every graphic once, in the current (painted, outlined) colours, enclosed paper black; grey (100,100,100) on an opaque pixel = transparent; any colour on a paper pixel inside a figure's box = an outline (paint_clear, 2026-10-14) (`python -m nexclash.dizzy1 sheet dizzy1rzx --z80 SNAPSHOT -o dizzy1`) |
| dizzy1_PAINTING_SPRITES_layout.json | 0f2e2b4aa3b5c58558438a80c3d6db59 | its layout (paint_clear: lists paper pixels too; carries the current colour map: a repaint edits only changed pixels): reads the painted sheet back (`python -m nexclash.dizzy1 colours PAINTED.png --layout ...`); an older layout drops outlines |
| dizzy1_PAINTING_SPRITES_painted.png | 15770ebab5e8a89fbd7a1604354ce6f1 | Dean's outlined painting (2026-10-14, 2,471 outline pixels), read with the paint_clear layout -> dizzy1_sprites_painted.nex 79218527 (nexclash dizzy1-layer2 c915df7) |
| dizzy1_REFERENCE_ALL_SPRITES.png | d62dc2a5d1ed515189ab5abd5d58954e | every figure whole, as the build colours it with the outlined map (not read back) |
| dizzy1_preview.png | 06fc75bb4d22a2c247af37844e0784b2 | phase-A preview: original / planned build at RZX frames 264, 1584, 2640, 3168, 4752, 5544 |
| dizzy1_preview_painted.png | 5d72432af591dda3071fb09845af262e | original / build in the painted colours at RZX frames 400, 900, 4000 |

## Fantasy World Dizzy - `fantasy_world_dizzy/` (games/fantasy_world_dizzy.md; hardware: untested)

| File | MD5 | What |
|---|---|---|
| Dizzy III - Fantasy World Dizzy (1989)(Codemasters)[a].z80 | 876f474b3441c08ed8ff25bd43d616a3 | snapshot |
| dizzy3rzx | 8005fece5a6d6f8792417b592d6b8df1 | recording (RZX) |
| fantasy_world_dizzy.nex | cd620010e2f61af0002e76718945716f | plain conversion |
| fantasy_world_dizzy_sprites.nex | 9182f2f8b4b0dc55b59a69728568b403 | modified game (sprites) |

## Magicland Dizzy - `magicland_dizzy/` (games/magicland_dizzy.md; hardware: untested)

| File | MD5 | What |
|---|---|---|
| Dizzy IV - Magicland Dizzy (1989)(Codemasters).z80 | 53078ac60141cd808b609600b85f4094 | snapshot |
| dizzy4rzx | b4620286854e67b13fb5590476fa17af | recording (RZX) |
| magicland_dizzy.nex | 09eb18496cff334ea17bfc0b0c94585d | plain conversion |
| magicland_dizzy_sprites.nex | bf137d41d3cc08221bf6fdda153c9de2 | modified game (sprites) |

## Spellbound Dizzy (Dizzy V) - `spellbound_dizzy/` (games/spellbound_dizzy.md; hardware: untested)

| File | MD5 | What |
|---|---|---|
| Dizzy_V.z80 | 703c934aa64c1c1d37d5041dd28cf9c7 | snapshot |
| Dizzy_V_auto.rzx | 9768b55b1f115db9b5989ac7f12090ec | recording (RZX) |
| dizzy5.nex | c99189f3274a4803f0b25b0217206bdb | plain conversion |
| dizzy5_sprites.nex | 1f33c467e6aa55585cea79cfbb24bcfe | modified game (sprites) |

## Prince of the Yolkfolk (Dizzy 6) - `prince_of_the_yolkfolk/` (games/prince_of_the_yolkfolk.md; hardware: untested)

| File | MD5 | What |
|---|---|---|
| Dizzy6.nex | e02faca34df9504cc1f2f162e0ef791e | plain conversion |
| Dizzy6_sprites.nex | f491e1f6621559ccc4d36de3535ff5d0 | modified game (sprites, slot1; rebuilt by selftest 2026-10-13 = the record's MD5) |
| Dizzy6.z80 | dd6cd7a3af47a520a260376c6ad4b459 | snapshot |
| try1.rzx | 60f0d2157d7da48e3e1b038455ebd9e8 | recording (RZX) |
| try2.rzx | 2bb26be393be7a1117d820513d868667 | recording (RZX) |
| try3.rzx | 285581685fd15c3e096e85999984b245 | recording (RZX) |

## Crystal Kingdom Dizzy (128K, plain only) - `crystal_kingdom_dizzy/` (games/crystal_kingdom_dizzy.md; hardware: plain runs)

| File | MD5 | What |
|---|---|---|
| Dizzy VII - Crystal Kingdom Dizzy (1992)(Codemasters).z80 | 9297ffd60d7c845166827d78f92d1636 | snapshot (48K version) |
| dizzy7128k.z80 | 0cb1cb260b2f17305ef41c30af0e1f8f | snapshot (128K) |
| dizzy7_auto.rzx | 53fd13edbbf1d77b8436cbc289b0d051 | recording (RZX) |
| crystal_kingdom_dizzy.nex | 99975f65172dc86ecefbac07db2c0c00 | plain conversion (= `nexclash.py convert dizzy7128k.z80`, checked 2026-10-12; named as the record's output, was dizzy7.nex) |

## El Capitan Trueno - removed from main (games/el_capitan_trueno.md)
Dean removed the reference folder from main (2026-10-14 12:28). The contributor's files (snapshot,
recording, the four sprite builds, their project; private: the contributor asked that none of it be
published) remain on branch `contrib-el-capitan-trueno` (commit 309eabf), with this section's full
file list. Restore the folder from there to work on the game.

## Adding files
Upload into the game's folder (GitHub: open the folder, Add file -> Upload files). New game:
make a folder named like its nexclash/games/ file.

## Review material
Images an agent made for review (they show game graphics) go in docs/review/<game>/.

## Target Renegade (128K) - `target_renegade/` (games/target_renegade.md; hardware: untested)

| File | MD5 | What |
|---|---|---|
| Renegade_II_Target_Renegade_1988_Imagine_Software_128K.z80 | 1895877d638a4a5f37a9402bed18f59a | snapshot (128K BASIC loader at its last PAUSE 0, loading screen) |
| Renegade_II_Target_Renegade_1988_Imagine_Software_128K.rzx | 464d4eeaa005e2d16fb1d65737325285 | recording (RZX; Fuse, its own SZX at the game menu, 9 autosaves stripped by `auto`; level 1) |
| target_renegade.nex | a0be8dc03a1be8c6d67dc3e0229abc35 | plain conversion (loader run in the toolkit, loading-screen front end) |
| target_renegade_sprites.nex | e0b246e35d028c34170e1d1c52f00f5f | modified game (every figure a sprite: ink black, body grey) |
| target_renegade_PAINTING_SPRITES.png | - | sheet to paint (+ _layout.json): every graphic once, in the build's colours (`python -m nexclash.renegade sheet RZX`) |
| target_renegade_REFERENCE_ALL_SPRITES.png | - | every figure whole, in the build's colours (not read back) |
| target_renegade_PREVIEW.png | - | four RZX frames: original, ULA layer, ULA + sprites |
| target_renegade_entry.z80 / target_renegade_plain_test.nex | - / 23647948ff22fc10e26b589cf1b83193 | phase A: the loader's state after the entry code; a plain test without front end |

## Jetpac - `jetpac/` (games/jetpac.md; hardware: untested)

| File | MD5 | What |
|---|---|---|
| Jetpac_1983_Ultimate_Play_The_Game_a_16K.z80 | 5875d535442974a0de82737652854f1f | snapshot (BASIC loader state, game code at PC 29026; no recording - Dean, 2026-10-19) |
| jetpac.nex | feff51b7038606d21c03c260055481e4 | plain conversion |
| jetpac_sprites.nex | 1a41d0312677ad9ae8fc9b9af1b77679 | modified game (sprites; every figure, game colours) |
| jetpac_PAINTING_SPRITES.png | 67302e7c259c3b011798d412ab6ad598 | colour sheet to paint (game default colours) |
| jetpac_PAINTING_SPRITES_layout.json | d4b1106e3593dea13d05f6fede084442 | its layout |
| jetpac_REFERENCE_ALL_SPRITES.png | df64f7b62826bd6022256c6f0f36a7f4 | every figure whole, game default colours |
| jetpac_preview.png | 31264b7a6145ea459016ed1d8085e752 | phase A preview frames (free run) |

## Lode Runner - `lode_runner/` (games/lode_runner.md; hardware: untested)

| File | MD5 | What |
|---|---|---|
| LODERUNN.TAP | bf13792fddf8545e6e96d7383c05a10d | tape image (48K, cracked version; Dean 2026-10-19) |
| LODERUNN.rzx | d491e25234e137d244121ba656f310c7 | recording (Fuse RZX; 8 autosave snapshots, stripped by `rzx strip`; key definition, level 1, two lives lost) |
| lode_runner.z80 | 47c265e30f51a9b7eb5c98db6cd994c5 | snapshot = the RZX's first SZX converted (identical RAM and registers; key definition screen) |
| Lode_Runner_-_128k.tzx | 0a3275c42d414200d1bb12a3c653873a | 128K version tape (sent first; not used: the recording is of the 48K TAP) |
| lode_runner.nex | cd0c1659c8569b2fa80da74962af90d2 | plain conversion (tail 0xA400; boot check OK) |
| lode_runner_sprites.nex | 85fe6afd593679bf59c787230ba0eaca | modified game (runner + guards = 4-bit sprites in the game's colours, scenery cells keep their colour, sprites hidden at the fade; hooks in RAM 0xA460; RZX + free run IDENTICAL) |
| lode_runner_PAINTING_SPRITES.png | - | sheet to paint: runner 15 + guard 15 frames, every graphic once (`python -m nexclash.loderunner sheet RZX --z80 Z80`) |
| lode_runner_PAINTING_SPRITES_layout.json | - | its layout: reads the painted sheet back (`python -m nexclash.loderunner colours`) |
| lode_runner_REFERENCE_ALL_SPRITES.png | - | every figure whole, as the build colours it (not read back) |
| lode_runner_REFERENCE_ALL_SPRITES_layout.json | - | its layout |
| lode_runner_preview.png | - | phase A preview: original / planned build at 8 frames |

## Match Day - `match_day/` (games/match_day.md; hardware: round 1 6188bacd - printer buffer / speed / fill fixed in round 2, untested)

| File | MD5 | What |
|---|---|---|
| Match_Day_1985_Ocean.rzx | 79427a4aa442948ff7d8f6f15e178512 | recording (RZX, Dean 2026-10-20: title, menu, walk-on, ~6 match minutes, a goal, a keeper dive) |
| Match_Day_spectrumcomputing.rzx | 04fd855b05d1849c117a91ee1199b9a3 | second recording (50403 frames, 1008 s; spectrumcomputing.co.uk entry 3067, supplied by Dean 2026-10-20; its own start snapshot, same code at every plotter / line writer) |
| Match_Day_1985_Ocean.z80 | d5ea19e487141ce922d0e96c02fd9054 | snapshot (48K, title/menu) |
| match_day.nex | 612761ec2772c5a7dcd27f939588d227 | plain conversion (printer buffer put back after NEXLOAD) |
| match_day_sprites.nex | f0aecd138d1668ff057318c2545f539d | modified game: players, ball, shadow as sprites (round 2; stamped verification of both recordings) |
| match_day_PAINTING_SPRITES.png | - | sheet to paint (+ _layout.json): fewest whole figures with every graphics byte, from both recordings; swatch 1 = strip colour, 2 = socks colour, 3-15 fixed; enclosed gaps shown in the pitch green (paintable) (`python -m nexclash.matchday sheet Z80 RZX RZX`) |
| match_day_REFERENCE_ALL_SPRITES.png | - | every figure drawn (+ _layout.json), not read back |
| match_day_PREVIEW.png | - | original / planned at RZX frames 2200, 3760, 5400, 6100 |
| match_day_PREVIEW_solid.png | - | same, players solid: enclosed gaps in the pitch green (Dean 2026-10-20) |
| match_day_PREVIEW_dive.png | - | keeper dive at frames 3746-3790: top original (torn), bottom planned (halves locked) |

## Cyclone - `cyclone/` (games/cyclone.md; sprite build verified in software; hardware: 25c1b1e0 loads, runs and plays for a few minutes, user 2026-10-21)

| File | MD5 | What |
|---|---|---|
| Cyclone_1985_Vortex_Software_a.z80 | c69e10137827958f8d39483cdf84f159 | snapshot as sent (saved MID TAPE LOAD, PC in ROM LD-BYTES: not used) |
| Cyclone_1985_Vortex_Software_a.rzx | d17bb2f7ca6aa8afbd1ed8caa7061dca | recording as sent (Fuse, 8 autosave snapshots; 4700 frames) |
| cyclone.z80 | 745cb8f59f865db5118e6dc98d09e385 | the RZX's first snapshot (SZX -> .z80; RAM and registers identical) |
| cyclone.rzx | 77010f7b6d806fbe44bf6c5dcfc7bec8 | the recording stripped (`rzx strip`: 8 autosaves dropped); take-off, land, sea, map screen |
| cyclone.nex | 390516396ca4d385c94b7f7bd2315d31 | plain conversion (tail 0x5D24, printer buffer put back: the main loop lives at 0x5B00; boot sim with NEXLOAD OK). Replaces 6071b59c (2026-10-21 morning), which lacked the printer-buffer fix and would not run on hardware |
| cyclone_sprites.nex | 25c1b1e070b07565fe4d1a38f69e3024 | modified game = the record's build (helicopter + aircraft as sprites with a white mask, shadows dithered; default colours) |
| cyclone_scc.rzx | 6fd92e589e12fb0b3152c5cb725fbd1b | whole-game recording (spectrumcomputing.co.uk entry 1206, sent by the user 2026-10-21): 179928 frames, starts at the menu, no autosaves; never replayed in full again - use bookmarks |
| cyclone_scc_aircraft_24500.rzx | c737e6252c1a7a8457263e151b2a4448 | bookmark of cyclone_scc.rzx (rzx.cut, 2000 frames; aircraft) |
| cyclone_scc_aircraft_167000.rzx | 6044da5a8458ad042f9e0cb55bc5e38d | bookmark of cyclone_scc.rzx (rzx.cut, 2000 frames; aircraft) |
| cyclone_PAINTING_SPRITES.png (+ _layout.json) | - | sheet to paint (`python -m nexclash.cyclone sheet cyclone.rzx cyclone_scc_aircraft_24500.rzx cyclone_scc_aircraft_167000.rzx --z80 cyclone.z80`), 84 figures; helicopter + aircraft with mask |
| cyclone_REFERENCE_ALL_SPRITES.png (+ _layout.json) | - | every figure drawing (102), not read back |
| cyclone_scc_crash_17800.rzx | 1e29775cc6df7f289dd2094169a410ba | bookmark of cyclone_scc.rzx (rzx.cut, 700 frames; a crash and the next life) |
| cyclone_scc_gameover_179500.rzx | 5f792e811ed695461f950e87b30bb567 | bookmark of cyclone_scc.rzx (rzx.cut, 428 frames; last crash, game over, back to the menu) |

## The Incredible Shrinking Fireman - `incredible_shrinking_fireman-add-OPUS/` (games/incredible_shrinking_fireman-add-OPUS.md; sprite build verified in software 2026-10-25; dc65565c and 400d0d11 ran on a real Next, round 2 fixed in 53f2665e)

The "-add-OPUS" suffix is this run's naming (Dean, 2026-10-25). The record stages the snapshot as
incredible_shrinking_fireman-add-OPUS.z80.

| File | MD5 | What |
|---|---|---|
| Incredible_Shrinking_Fireman_The_1986_Mastertronic.z80 | fc8e7535fc42afb60c12625b5fdfd064 | snapshot as sent (48K, in game code, IM 2 via ROM 0x39FF) |
| incrediblefireman.rzx | 8154d148d90b0f3cc94229bc143bac68 | Dean's recording (Fuse, 32492 frames, no autosaves): title, many rooms, option / carrying screens |
| incredible_shrinking_fireman-add-OPUS.nex | feb706fcdaa29f13844a7b4982dc21fa | plain conversion (tail 0x5D00, printer buffer put back; boot sim with NEXLOAD OK) |
| incredible_shrinking_fireman-add-OPUS_sprites.nex | 53f2665e76775f3c1b404aba74e93a7b | modified game = the record's build (fireman + room figures as 18 x 26 sprites with a black mask, shown from the plotter entry; diamonds; live inks; interrupts deferred while a plot runs). Replaces 400d0d11 (hardware round 2: room 5 corruption, ISR plot inside a main-code plot) and dc65565c (round 1: flicker, no mask) |
| incredible_shrinking_fireman-add-OPUS_three_windows.png | - | frames 604 (room 2) and 1028 (room 6): original / clash removed / clash removed + mask (simulated) |
| incredible_shrinking_fireman-add-OPUS_PAINTING_SPRITES.png (+ _layout.json) | - | sheet to paint (`python -m nexclash.incredible_shrinking_fireman_add_opus sheet incrediblefireman.rzx --z80 Incredible_Shrinking_Fireman_The_1986_Mastertronic.z80 -o incredible_shrinking_fireman-add-OPUS`), 86 figures |
| incredible_shrinking_fireman-add-OPUS_REFERENCE_ALL_SPRITES.png (+ _layout.json) | - | every figure drawing (103, incl. 21 never drawn in the RZX), not read back |
| incredible_shrinking_fireman-add-OPUS_phaseA_preview.png / _phaseA_callers.png | - | phase A: original / planned frames, the plotter's callers |
| run_cspect_incredible_shrinking_fireman-add-OPUS.bat | - | double-click: runs the sprite build in CSpect (-zxnext -nextrom); drag another .nex onto it to run that |

## Hardware test: Z80N instructions - `hwtests/z80ntest/` (not a game; nexclash tools/hwtests/README.md "z80ntest")

The test .nex and the photos of its runs: every Z80N instruction's result, flags and T-states on a
real Next against nexclash/z80n.py. Results and what they settled: nexclash tools/hwtests/README.md
(board results, CSpect) and the nexclash/z80n.py docstring. Rebuild: `python tools/hwtests/build.py
z80ntest` in nexclash (same MD5 from nexclash #60).

| File | MD5 | What |
|---|---|---|
| z80ntest.nex | 28528e1035cf193227e4d6402f6b6e43 | z80ntest v2 (nexclash 4a2b4a9 / main after #60) |
| board_v1_func.webp | 5cc8f6a69ebecdecfee9353cc0dfc8bb | v1 on the board, core 3.02.00: FUNC page (LDWSF yellow -> LDWS fix; LDPIRX red) |
| board_v1_time.webp | 3fb234c4806ac9a1743e0589e6645b54 | v1 on the board: TIME page, all green (LDWS 13.9) |
| board_v2_func.webp | f26ba903d9dfc6528131f9a433e08138 | v2 on the board, core 3.02.00: all green but LDPIRX (fixed in core 3.02.02) |
| board_v2_time.webp | 03e5aecc8ce7eb6e31f3f1ee099d1634 | v2 on the board: TIME page, all green |
| cspect_3.3.1.0_func.webp | 5bb14fadf402f396d729ffd1916c68f7 | v2 in CSpect 3.3.1.0 (reports core 4.00.00): ADD rr,A, LDIX-family, LDWS, JP (C) flags differ from the board |
| cspect_3.3.1.0_time.webp | fb8264ded709082503e412f5328ae4ad | v2 in CSpect: PUSH nn 19.0 T (board 23) |

## Rainbow Islands, Z80N version - `rainbow_z80n/` (games/rainbow_z80n.md; the version going forward; hardware: untested)

Inputs are the deprecated version's files in `rainbow_islands/` (rainbow.z80, rainbow.rzx, rainbownew.rzx, leebee/),
not copied: the record's paths point there. Built by `selftest.py --game rainbow_z80n --verify --stamp`
(2026-10-22, both RZX IDENTICAL).

| File | MD5 | What |
|---|---|---|
| rainbow_z80n.nex | 7ac543fb51c7a3c4137778eeb3cdc175 | plain conversion (identical to rainbow_islands/rainbow.nex) |
| rainbow_z80n_sprites.nex | bda21ab675fa271b6f51f332aae14206 | modified game: as rainbow_sprites cf017271 + Z80N hooks (SWAPNIB, MIRROR A, ADD HL,A) + raster pair read until it agrees |
| rainbow_z80n_sprites_diag.nex | bb2058c8bb9d593364aa1515a38a130c | the same + diagnostic border (blue = commit deferred, red = tile built, yellow = overrun) |

## Hardware test: technique costs - `hwtests/nextbench/` (not a game; nexclash tools/hwtests/README.md "nextbench")

The benchmark .nex files and the photos of their board runs. Tables and conclusions: nexclash
docs/TECHNIQUES.md 1.0 (v1) and 1.0b (v2).

| File | MD5 | What |
|---|---|---|
| nextbench.nex | c78bde9c5a6a3a88cb91be72edcfbfbd | nextbench v1 (nexclash 0b51cc9) |
| board_v1_p1.webp | 2fd5d98d921a504e6d035373ac0351b0 | board, core 3.02.00: copies, fills, pattern uploads (DMA "!" at 3.5 MHz: wrong copies) |
| board_v1_p2.webp | 1451b57c68f599948d5b39adfa60fe00 | board: attributes, registers, paging, cells, scroll, palette, copper |
| nextbench_v2.nex | e3a065b49b6853f043279628b1344b28 | nextbench v2 (88 rows: sizes, DMA reuse, copper; nexclash 5b86b0f) |
| board_v2_p1.webp | 294813e742b39830f9535415d848bc00 | v2 on the board, core 3.02.00: copies LDIR / LDI / stack / DMA 1-256 |
| board_v2_p2.webp | e587788d3e0b87e871f211f08aa54e3e | DMA 1K-2K, rtg / rrun / burst, LDIRX, fills, OTIR uploads |
| board_v2_p3.webp | b45117bbb42548335cf6e239a72c1fe4 | uploads OUTI / DMA, attributes, hides, registers |
| board_v2_p4.webp | e42607a25880053a5c1827e800b0fb01 | paging, cells, flips, scroll, palette, copper load |
| board_v2_p5.webp | fdd65f7784d72bf46f9e5da417cfccda | LDIR with the copper running; CP WAIT 122 / 120, CP APART 0, CP SHARE 255 |
| nextbench_v3.nex | a188e0d560a28c59656646b05fc0bca5 | nextbench v3 (v2's 88 rows x 5 runs, "~" = varies between runs, variation page; line read fixed; nexclash 625df06); board run 2026-10-22: no value varied between the 5 runs |
| board_v3_p1.webp | a91824a514bf87edf398e609c51c2eeb | v3 on the board, core 3.02.00 (5 runs, means): copies LDIR / LDI / stack / DMA 1-256 |
| board_v3_p2.webp | b875fb660e94ef4d9b5d6dabb50f5ea7 | DMA 1K-2K, rtg / rrun / burst, LDIRX, fills, OTIR uploads |
| board_v3_p3.webp | 7fad1e7e571d1efb28d6c79df154a3ee | uploads OUTI / DMA, attributes, hides, registers |
| board_v3_p4.webp | 05a30e2b70aab960f396c73f189123b6 | paging, cells, flips, scroll, palette, copper load |
| board_v3_p5.webp | c2cdf6f12a11f05d730b05f51f3d48df | LDIR with the copper running; CP WAIT 120 / 120, CP APART 0, CP SHARE 255 (variation page 6: none, not photographed) |
