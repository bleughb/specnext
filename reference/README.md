# Reference inputs (Dean's snapshots and recordings)

`python selftest.py` (default folder: this one) rebuilds every game from these and checks the
.nex MD5s in docs/VERIFICATION.md. Files are recognised by MD5 (any name); the engine games
without a pinned MD5 by the name below (selftest prints their MD5: pin it in selftest.py).

| File | MD5 | Game | Here |
|---|---|---|---|
| Chuckie_Egg.z80 | cddc0cfea8259d0c497b50fae0acd27e | Chuckie Egg (Chuckie_Egg_1983_A__F_Software_a.z80) | yes |
| Chuckie_Egg.rzx | 7697943d44c33dbef1c073332e36dfc0 | Chuckie Egg, Dean 2026-10-11 (levels 1-2) | yes |
| wally.z80 | (pin) | Everyone's a Wally (World of Spectrum) | upload |
| wally.rzx | (pin) | Dean's wallyrzx.rzx | upload, rename |
| rainbow.z80 | (pin) | Rainbow Islands 128K | upload |
| rainbow.rzx, rainbownew.rzx | (pin) | Dean's two Rainbow recordings | upload |
| any name | 7578947fcc8dbc4ba822e2c565499d54 | Treasure Island Dizzy in-game (dizzy2_game.z80) | upload |
| any name | 9443f0cc4c32415849b0419750f1bff3 | Treasure Island Dizzy title (dizzy2.z80) | upload |
| any name | 0659328fd54fd446e39d1740bafd02e7 / 99d9c4c086d06a46ba7a781e5321dc3e | Dizzy 1 .z80 / .rzx | upload |
| any name | 876f474b3441c08ed8ff25bd43d616a3 / 8005fece5a6d6f8792417b592d6b8df1 | Fantasy World "(a)" .z80 / .rzx | upload |
| any name | 53078ac60141cd808b609600b85f4094 / b4620286854e67b13fb5590476fa17af | Magicland .z80 / .rzx | upload |
| any name | 703c934aa64c1c1d37d5041dd28cf9c7 | Dizzy V (Dizzy_V.z80, loader stage) | upload |
| Dizzy6.z80, try1.rzx | dd6cd7a3af47a520a260376c6ad4b459 / - | Dizzy 6 (not in selftest yet) | upload |
| dizzy7128k.z80 | - | Crystal Kingdom Dizzy (plain only) | optional |

Upload from Windows (in the repo clone): copy the files here, then
`git add reference && git commit -m "Reference files" && git push`
(or GitHub web: Add file -> Upload files, into reference/).
