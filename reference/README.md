# Reference inputs (Dean's snapshots and recordings)

`python selftest.py` (run in the public nexclash repo; finds ../specnext/reference) rebuilds every game from these and checks the
.nex MD5s in docs/VERIFICATION.md. Files are recognised by MD5 (any name); the engine games
without a pinned MD5 by the name below (selftest prints their MD5: pin it in selftest.py).

| File | MD5 | Game | Here |
|---|---|---|---|
| Chuckie_Egg.z80 | cddc0cfea8259d0c497b50fae0acd27e | Chuckie Egg (Chuckie_Egg_1983_A__F_Software_a.z80) | yes |
| Chuckie_Egg.rzx | 7697943d44c33dbef1c073332e36dfc0 | Chuckie Egg, Dean 2026-10-11 (levels 1-2) | yes |
| wally.z80 | a9eeb555a327e5794b0ba19bc80dccf0 | Everyone's a Wally (World of Spectrum) | yes |
| wallyrzx.rzx | 72c7d1f6c99407bc21d892d423e89964 | Dean's Wally recording | yes |
| rainbow.z80 | (pin) | Rainbow Islands 128K | upload |
| rainbow.rzx, rainbownew.rzx | (pin) | Dean's two Rainbow recordings | upload |

Rainbow Islands: once these three are here, `python selftest.py` (in nexclash) must reproduce
rainbow.nex 7ac543fb51c7a3c4137778eeb3cdc175 and rainbow_sprites.nex bffd9357d772e2df975ec5f40dc9e4cb
(objects on the tilemap, 2026-10-11) - the first time that build is rebuilt outside its session.
| any name | 7578947fcc8dbc4ba822e2c565499d54 | Treasure Island Dizzy in-game (dizzy2_game.z80) | upload |
| dizzy2.z80 | 9443f0cc4c32415849b0419750f1bff3 | Treasure Island Dizzy title | yes |
| any name | 0659328fd54fd446e39d1740bafd02e7 / 99d9c4c086d06a46ba7a781e5321dc3e | Dizzy 1 .z80 / .rzx | yes |
| any name | 876f474b3441c08ed8ff25bd43d616a3 / 8005fece5a6d6f8792417b592d6b8df1 | Fantasy World "(a)" .z80 / .rzx | yes |
| any name | 53078ac60141cd808b609600b85f4094 / b4620286854e67b13fb5590476fa17af | Magicland .z80 / .rzx | yes |
| any name | 703c934aa64c1c1d37d5041dd28cf9c7 | Dizzy V (Dizzy_V.z80, loader stage) | yes |
| Dizzy6.z80 + try1.rzx | dd6cd7a3af47a520a260376c6ad4b459 / 60f0d2157d7da48e3e1b038455ebd9e8 | Dizzy 6 (not in selftest yet) | try1-3.rzx + Dizzy6.nex yes, Dizzy6.z80 upload |
| dizzy7128k.z80, dizzy7_auto.rzx | 0cb1cb260b2f17305ef41c30af0e1f8f | Crystal Kingdom Dizzy (plain only) | yes |

Upload from Windows (in the repo clone): copy the files here, then
`git add reference && git commit -m "Reference files" && git push`
(or GitHub web: Add file -> Upload files, into reference/).

Also here: Dizzy_V_auto.rzx, dizzy2rzx / dizzy2newrzx (Treasure Island), Everyone's A Wally.tzx.
Still missing: dizzy2_game.z80 (Treasure Island in game), rainbow.z80 + rainbow.rzx + rainbownew.rzx, Dizzy6.z80.

## Review material (private: shows game graphics)
Put images an agent made for Dean's review in docs/review/<game>/ here, not in the public repo.
Rainbow Islands, from the collectables session (2026-10-11), if you still have them:
rainbow_B_mask_sheet.png (layer B: dark-blue partial tiles - awaiting your review),
rainbow_objects.png + rainbow_objects.json (object/tile catalogue of both recordings).
