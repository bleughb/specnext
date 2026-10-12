# Reference games (private)

One folder per game: the original snapshot and Dean's recordings (the references the toolkit is
verified against), and the built games: `<game>.nex` (plain) and `<game>_sprites.nex` (the
modified game), exactly as `python selftest.py` (in nexclash) rebuilds them. Game notes:
nexclash/games/<folder name>.md (one per game, same name as the folder). Never copy anything from here into the public repo.

selftest.py finds files anywhere under reference/ by MD5 (names do not matter); it also
expects ../specnext next to the nexclash clone (or NEXCLASH_REFERENCE=path/to/reference).

## Chuckie Egg - `chuckie_egg/` (games/chuckie_egg.md; hardware: untested)

| File | MD5 | What |
|---|---|---|
| Chuckie_Egg.rzx | 7697943d44c33dbef1c073332e36dfc0 | recording (RZX) |
| Chuckie_Egg.z80 | cddc0cfea8259d0c497b50fae0acd27e | snapshot |
| chuckie_egg.nex | ec0df71e70fae35836eaed521f300777 | plain conversion |
| chuckie_egg_sprites.nex | bfad6be1e7c8a2c797a6242d7f339e35 | modified game (sprites) |

## Midnight Resistance (128K) - `midnight_resistance/` (games/midnight_resistance.md; hardware: untested)

| File | MD5 | What |
|---|---|---|
| Midnight_Resistance_1990_Ocean_128K.rzx | b75ecd5f60c3ec67fe463a0aa606f6a1 | recording (RZX; 8 autosave snapshots, stripped by `auto`; title, level 1 to the tank, game over) |
| Midnight_Resistance_1990_Ocean_128K.z80 | 67bf05d356d51b2b402d88c5f0cdfb21 | snapshot (title screen) |
| midnight_resistance.nex | 17239acaaf67b0f8011478053e17829d | plain conversion |
| midnight_resistance_sprites.nex | e8f0ece9e41c314d76471c96f4595854 | modified game (player green, soldiers white, jeep / tank in their cell colours) |
| midnight_resistance_preview.png | 703915c6bbc0afb66c086edd1a73db4d | design preview shown to Dean (original / fixed colours / cell colours) |

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

## Rainbow Islands (128K) - `rainbow_islands/` (games/rainbow_islands.md; hardware: e50733b2 / diag 8f25bc61 untested; bffd9357 had random corruption + slowdowns)

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

## Adding files
Upload into the game's folder (GitHub: open the folder, Add file -> Upload files). New game:
make a folder named like its nexclash/games/ file.

## Review material
Images an agent made for review (they show game graphics) go in docs/review/<game>/.
