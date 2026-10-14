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
| smash_tv_sprites_outline_cell_paper.nex | 6227481f8f2514faa0d9648b6bc972e8 | modified game (every figure as sprites in its cell inks, outline in the cell paper; prompt front end) |

## Midnight Resistance (128K) - `midnight_resistance/` (games/midnight_resistance.md; hardware: e8f0ece9 runs, Dean 2026-10-13; 670f9403 tests OK, Dean 2026-10-14)

| File | MD5 | What |
|---|---|---|
| Midnight_Resistance_1990_Ocean_128K.rzx | b75ecd5f60c3ec67fe463a0aa606f6a1 | recording (RZX; 8 autosave snapshots, stripped by `auto`; title, level 1 to the tank, game over) |
| Midnight_Resistance_1990_Ocean_128K.z80 | 67bf05d356d51b2b402d88c5f0cdfb21 | snapshot (title screen) |
| midnight_resistance.nex | 17239acaaf67b0f8011478053e17829d | plain conversion |
| Midnight_Resistance_1990_Ocean_128K_V2RZX.rzx | 3e0fa52ae2fbf9fbae62cebb70b83190 | second recording (Dean 2026-10-13; autosaves stripped by `auto`; more of level 1, the shop) |
| midnight_resistance_sprites.nex | 670f94034af175ed56df97f8cdb1ef29 | modified game (every figure a sprite, also flipped and in the shop, in Dean's painted colours; sprites hidden on every loop exit) |
| midnight_resistance_PAINTING_SPRITES.png | - | sheet to paint: every graphic once, drawn in the current colours (`python -m nexclash.midres sheet RZX RZX --z80 Z80`) |
| midnight_resistance_PAINTING_SPRITES_layout.json | - | its layout: reads the painted sheet back (`python -m nexclash.midres colours`) |
| mr_colours_painted.png | - | Dean's first painting (2026-10-14; old single-sheet layout) -> docs/profiles/midnight_resistance_colours.json in nexclash |
| midnight_resistance_REFERENCE_ALL_SPRITES.png | - | every figure whole, as the build colours it (not read back) |

## Commando (128K) - `commando/` (games/commando.md; hardware: 5ab928e9 runs; 5c1081b7 flicker/logo/dots; 541e34e2 crashed (code at 0x3D00, probably the DivMMC automap); d601385e runs)

| File | MD5 | What |
|---|---|---|
| Commando_1985_Elite_Systems_t_128K.RZX | b3350a66a14db07add43c878eb872169 | recording (RZX; 8 autosave snapshots, stripped by `auto`) |
| Commando_1985_Elite_Systems_t_128K.z80 | c9af5668191462d77c5859900268c24b | snapshot (BASIC loader, trainer version) |
| commando.nex | a206f950c12f58a8e7f26b366f5a2480 | plain conversion (starts in the front end) |
| commando_sprites.nex | d601385ee4aeb7f3d7c0771bdc27df6b | modified game (solid sprites with yellow body, solid objects by the walk-box depth rule, scenery restore, pattern cache) |

## Everyone's a Wally - `everyones_a_wally/` (games/everyones_a_wally.md; hardware: boots and runs)

| File | MD5 | What |
|---|---|---|
| Everyone's A Wally.tzx | 538ad0852363e32bc75cfbc7debbf702 | tape image |
| wally.nex | 2e615b3e7ae995e6d6a6ed9e3f586d4d | plain conversion |
| wally.z80 | a9eeb555a327e5794b0ba19bc80dccf0 | snapshot |
| wally_sprites.nex | f7605489c3af55b8e8c6a580c1c26150 | modified game (sprites) |
| wallyrzx.rzx | 72c7d1f6c99407bc21d892d423e89964 | recording (RZX) |

## Rainbow Islands (128K) - `rainbow_islands/` (games/rainbow_islands.md; EXCLUDED from automatic selftest checks; hardware: e50733b2 / diag 8f25bc61 untested; bffd9357 had random corruption + slowdowns)

| File | MD5 | What |
|---|---|---|
| rainbow.nex | 7ac543fb51c7a3c4137778eeb3cdc175 | plain conversion |
| rainbow.rzx | 55046d1893bba0a4faf314ecd3a9638b | recording (RZX) |
| rainbow.z80 | 4c98b980b1726af545fccc99665ef29b | snapshot |
| rainbow_sprites.nex | e50733b2b7e2db32f004c1436a2e0461 | modified game (sprites; collectables without border) |
| rainbow_sprites_diag.nex | 8f25bc6146b9d7f7ae1f12a1d227447e | diagnostic build (border colours = raster wait / tile built / frame overran) |
| rainbownew.rzx | 47bb2b163a947724c343a2bc1b039458 | recording (RZX) |

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
| dizzy1_sprites.nex | 05d2bce99f4d7654d4e1c9c9c04dc391 | modified game (sprites) |
| dizzy1rzx | 99d9c4c086d06a46ba7a781e5321dc3e | recording (RZX) |

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
| dizzy7.nex | 99975f65172dc86ecefbac07db2c0c00 | plain conversion (= `nexclash.py convert dizzy7128k.z80`, checked 2026-10-12) |

## El Capitan Trueno - `el_capitan_trueno/` (games/el_capitan_trueno.md; contributed by Leonid (Leonis Silver), 2026-10-14; prototype outside the toolkit, no record yet; hardware: untested, MAME 0.289 played to the end of part 1 by the contributor)

Private: the contributor asked that none of it be published. Their cover letter: `CONTRIBUTOR_README.md`. Their project (builder, sheets, nexpatch): `contributor/` (how to rebuild: `contributor/REBUILD.md`).

| File | MD5 | What |
|---|---|---|
| CONTRIBUTOR_README.md | - | the contributor's cover letter (contents, build steps, questions to the maintainers) |
| Capitan Trueno, El (1990)(Dinamic)(ES).z80 | 15e128b05c471678d2f0fae2fbb8cedc | snapshot (title screen; CRC32 320337B0) |
| trueno1.rzx | d07fcc914f385aabfe42c4a5cbaf1bba | recording (RZX; the contributor's play, Spectaculator 0.61, 53,542 frames) |
| Trueno.nex | ca49e0f4c92da6fe96d71062c2ed15a3 | plain conversion (`nexclash.py convert ... --tail 0xA6C9`, v0.1.4 and main identical; boot sim OK). The contributor's listed 4b415b4c is the DEFAULT-tail build (tail below SP above 0xC000), which fails the boot sim - not kept |
| Trueno_sprites.nex | a9befbb250a040734555ce80aea208b8 | modified game (every figure a sprite, foreground in Layer 2, fix cells drawn by the contributor); rebuilt byte-identical 2026-10-14 with their tk 0.1.4 and with nexclash main |
| Trueno_sprites_en.nex | da3f1b0a1ba8226573c638bc06cb34d5 | option `--en` (English texts); rebuilt identical |
| Trueno_sprites_immortal.nex | deaf4577f982991774d7aa17f60d1aab | option `--immortal` (energy never drops); rebuilt identical |
| Trueno_sprites_en_immortal.nex | 867bda87225d060964772b36c0ed2aeb | both options; rebuilt identical |
| contributor/ | - | build/ (builder + checks + generated tables), gfx/ (the contributor's sheets: game graphics), NOTES.md (working log), nexpatch/ (proposal; out/ holds the Trueno page = game-derived), toolkit_changes.diff (as sent) |

The archive's `nex/` folder held the same four sprite builds under player names (`Capitan Trueno, El.nex`, `(Eng)`, `(Immortal)`, `(Eng) (Immortal)`); not duplicated here.

## Adding files
Upload into the game's folder (GitHub: open the folder, Add file -> Upload files). New game:
make a folder named like its nexclash/games/ file.

## Review material
Images an agent made for review (they show game graphics) go in docs/review/<game>/.
