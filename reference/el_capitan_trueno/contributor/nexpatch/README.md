# nexpatch - a Spectrum Next .nex from the user's own snapshot

A modified game is never distributed: the user gets one HTML page per game, picks their own `.z80`
in it and presses **Make NEX**; the browser saves the `.nex`. The page holds only the difference to
the snapshot.

- `python nexpatch.py make GAME.z80 GAME.nex -o PAGE.html --title T [--subtitle S] [--about A]
  [--notice N] [--credits C]` - the patch and the page (about / notice / credits: HTML allowed).
  It checks the round trip itself (the patch applied in Python == the `.nex`) and reports how many
  bytes were copied from the snapshot, filled, and carried as own bytes.
- Versions and options: `--choice Language --variant LABEL SUFFIX NEX ...` puts several versions on
  one page (a radio choice, the first preselected); `--option LABEL SUFFIX BASE.nex WITH.nex` adds a
  check box, off by default (the bytes where WITH differs from BASE; only the new bytes are stored,
  applied after the version's SHA-256 check, so it must fit every version). The saved name gets the
  suffixes: `Capitan Trueno, El (Eng) (Immortal).nex`.
- `python nexpatch.py apply GAME.z80 PAGE.html [--variant N] [--option K ...] [-o OUT.nex]` - what the
  page does, in Python.
- `node test_page.js PAGE.html GAME.z80 V1.nex [V2.nex ...] [--option K VERSION WITH.nex]` - runs the
  page's own JavaScript: every version and the option must print `identical: true`, and a changed file
  must be refused. Run it for every new page.
- `template.html` - the page: title, file choice and button, How to use it, Details, then the notice
  and the credits. Fields `{{TITLE}}`, `{{SUBTITLE}}`, `{{ABOUT}}`, `{{NOTICE}}`, `{{CREDITS}}`,
  `{{Z80NAME}}`, `{{CRC}}`, `{{DATA}}` (versions + options, JSON).
- `AI_GUIDE.md` - for an AI that makes a mod: keep the game's memory as in the snapshot, put the
  mod's code and data in the alt ROM and free Next banks, then make the page; the patch format.
- `out/` - pages made so far, with the command that made each (`out/README.txt`).

How it works: the snapshot is recognised by the CRC32 of the file (collections hold few variants of
a game). The patch copies from the snapshot (the file's bytes and its unpacked memory banks: in a
48K `.nex` the banks 5, 2, 0 are the game's memory in snapshot order), fills runs of one byte, and
carries the rest as own bytes, encrypted with ChaCha20 under SHA-256 of the whole `.z80` - a key
that is never stored, so without the original file the patch is noise. Python standard library
only; the page needs nothing external and works offline in any browser.

El Capitan Trueno (`out/Capitan Trueno.html`): the 328,192-byte `.nex` = 63,661 bytes copied from
the snapshot, 106,994 filled, 157,537 own bytes (hooks, sprite patterns, Layer 2 tables); patch
162,748 bytes.
