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
