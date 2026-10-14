# El Capitan Trueno for nexclash - from Leonid and Nika

Hello Dean,

Thank you for nexclash. We tried it on El Capitan Trueno (Dinamic, 1990, 48K, part 1): a game with
rich, colourful graphics, where we wanted to see what it looks like without colour clash (we love
the clash in its own way, so the original stays the original). It works: every figure is a
hardware sprite, bushes and the other foreground stay in front of them on Layer 2, and the scenery
that clashed in the original was redrawn by hand. Leonid played part 1 to the end in MAME, with and
without an immortality cheat.

This archive is for you to look at and experiment with. It is private: it includes the snapshot,
our recording and graphics drawn over the game's own, so please keep it in your private reference
repository and do not publish it.

## What is inside
| Path | What |
|---|---|
| `trueno/` | the game project, ready to build: the `.z80`, `trueno1.rzx`, `build/` (the builder and checks), `gfx/` (Leonid's sheets), `lib/` (SkoolKit 10.1), `NOTES.md` (our working log), `Trueno_sprites.nex` (the result) |
| `trueno/tk/nexclash-0.1.4/` | your toolkit 0.1.4 with our additions (the builder imports it from there) |
| `toolkit_changes.diff` | every change to your files, against 0.1.4 as released (MANIFEST.json) |
| `nexpatch/` | a proposal: a `.nex` built from the user's own `.z80` in a browser page, no game data shipped |
| `nex/` | the four ready builds: `Capitan Trueno, El.nex` (Spanish), `(Eng)` (English texts), `(Immortal)` (energy never drops), `(Eng) (Immortal)` |

## Building
Requirements: Python 3 with SkoolKit (bundled in `trueno/lib`) and Pillow (`pip install pillow`).
```
cd trueno/build
python build_all.py          # whole chain, ~1 minute: catalogue, shapes, patterns, Layer 2 tables,
                             # hooks (your pinned sjasmplus 1.24.0), then ../Trueno_sprites.nex
python make_nex.py           # the last step alone (after a change to the hooks or the tables)
python make_nex.py --en --immortal   # options: English texts (texts_en.py), immortality (one byte)
```
Outputs: `Trueno_sprites[_en][_immortal].nex`. `build_all.py --sjasm PATH` uses another sjasmplus. The full build reproduces
`Trueno_sprites.nex` a9befbb250a040734555ce80aea208b8 byte for byte. `run_nex.py` is our MAME
helper (paths of our machine); you will want CSpect or the Next instead.

How it works, in one paragraph: the game composes every frame in a back buffer and copies it to the
screen. The plotter is left untouched, but its "behind the foreground" map is pointed at bytes that
say every cell is foreground, so it saves the scenery as usual and draws no figure pixel: the
game's memory stays as the original's. The hooks record each figure and show it as sprites; the
attributes come from the game's clean scenery copy; the game's own foreground cells go into Layer 2
with the palette priority bit. Details, addresses and the recipe: `games/el_capitan_trueno.md`.

## Your files we changed (please treat them as suggestions)
Your CLAUDE.md asks to capture what a session learned; this is what we learned. Take what you like.
- `CLAUDE.md`: the start-up tail rule for 48K too, with the reason (Trueno's tail above 0xC000
  vanished when the tail's OUT 0x7FFD mapped bank 0 back).
- `docs/PLAYBOOK.md`: ask about menus / windows and offer a test cheat at step 0; pixel art is the
  human's at 3b; six rows in the decision table (windows over the play area, screens without the
  normal build, code entering the plotter past the hook, a snapshot with the title already drawn,
  scenery clash as Layer 2 "fix cells", memory for per-screen tables); one emulator pass per list
  on a long game.
- `docs/LEARNINGS.md`: the alt ROM is a copy of NextZXOS ROM3, which has data at 0x3B00-0x3CFF;
  back-buffer games; the plotter as the source of exact ink and mask; one consistent state for
  shapes; a fast frame-level mode; layer-by-layer debugging in MAME; a sharper dis.py warning.
- `docs/BRIEFING.md` C2 17-19: the 48K tail check, nextboot's ROM3 model, a shared fast mode.
- `docs/VERIFICATION.md`: a section for Trueno, with what is not done yet.
- New: `asm/trueno_hooks.asm`, `games/el_capitan_trueno.md`.

## English version and immortality
Leonid asked for an English translation: the game's texts (menu, key definition, pause window,
access code screen, credits) are in `build/texts_en.py`, with every old byte checked. The title
in the snapshot is already drawn, so the build wipes the Spanish words and prints the English ones
with the game's own print routines in the simulator. Immortality (the energy store 0x7A1F -> NOP)
was our test cheat; it is now an option for players who just want to look around.

## Not done yet (honestly)
- The builder is a prototype outside the toolkit: no engine module, no profile, no evidence record
  (a record would make selftest try to rebuild it through the toolkit). Moving it into
  `nexclash/trueno.py` is step 6 of the recipe.
- The per-call differential verification of the hooks (registers and memory), unit tests and a
  negative control. Whole-recording checks were done instead (order, cover, screen and buffer
  reads, no-draw): `docs/VERIFICATION.md`.
- Real hardware: not tried yet.

## nexpatch (a proposal)
Your rule is that game data never travels; for a mod with redrawn graphics that is hard. nexpatch
turns a finished `.nex` into one HTML page: the user opens it in any browser, picks their own `.z80`
(recognised by CRC32) and gets the `.nex`. The page holds only the difference to the snapshot; our
own bytes are encrypted with a key taken from the whole `.z80`, so without the original file the
page is noise. `nexpatch/README.md` and `nexpatch/AI_GUIDE.md` (for an AI making such a mod).
`nexpatch/out/Capitan Trueno.html` is the page for this game: a language choice (Spanish /
English) and an immortality check box, off by default; the saved file is named like the builds in
`nex/`.

## Questions for you
1. Would you like Trueno as a toolkit engine (`nexclash/trueno.py`), and is a human's redrawn
   graphics welcome in a contribution, or should such mods go out as nexpatch pages?
2. Which of the doc changes would you rather have differently?

With best wishes,
Leonid (Leonis Silver) and Nika Claude, an AI assistant
