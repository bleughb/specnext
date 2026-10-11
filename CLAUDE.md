# Agent instructions - nexclash (Spectrum Next colour-clash remover)

`.z80` -> `.nex` with game figures as Next hardware sprites; game logic proven identical by
differential tests against Dean's recordings. This repo is the ONLY master copy: code, profiles,
docs and Dean's reference files. The claude.ai Project only points here. Never retype a file
from the Project or a chat: clone, edit, commit.

## Start
1. `git clone https://github.com/bleughb/specnext && cd specnext` (or `git pull`).
2. `pip install skoolkit --break-system-packages`. sjasmplus only for .asm edits (docs/BRIEFING.md 0).
3. Read STATUS.md, then games/<game>.md for the game in hand. docs/BRIEFING.md (platform +
   toolkit, settled) and docs/LEARNINGS.md (lessons) before changing shared code or starting a new
   game; docs/PLAYBOOK.md for a new game. Read code only in modules you will change.
4. Before AND after touching shared code (nexclash.py, z80tonex, build, verify, nextboot, ...):
   `setsid nohup python selftest.py > selftest.log 2>&1 < /dev/null &` and poll (inputs come from
   reference/; `--fast` skips Rainbow's ~50 min). Anything not PASSED/skipped = stop and fix.

## Dean's standing rules
- Style: terse. Results, decisions and files first. Explain only new findings or what needs his
  decision. No recap.
- Verify the original bytes at every patch site.
- Test every change differentially against Dean's RZX: all registers (AF' included unless a
  documented convergence check applies) and all memory outside the never-read draw buffers,
  sprite pixels against the original plot, and no jumps into the middle of a patched instruction.
- Cover paths the RZX does not reach with unit tests: guard edges (converted vs passthrough must
  match the guard), table-full cases, and a negative control. The negative control must use the
  broken patch's own tables (restore only run-time state from captured states).
- Keep changes additive and limited to the new engine. Commit every new file (.py, .asm, .json).
- Ask Dean before decisions that change what he sees (which figures become sprites, colours,
  anything left on the ULA).
- Do not change a finished game's output (Wally, Rainbow, ...) unless that is the task. If you
  touch shared code, selftest must reproduce every MD5 in docs/VERIFICATION.md.
- Never run `pkill -f <name>` when your own command line contains <name>.
- 128K start-up tail must end below 0xC000.

## End of every task
1. Update games/<game>.md (facts, decisions, status, checklist), STATUS.md (one row per game),
   docs/VERIFICATION.md (results + MD5s), docs/LEARNINGS.md (GENERAL lessons only; per-game
   facts go in games/). History lives in git: no history sections.
2. Commit on a branch, push, open a PR for Dean (commit message = what changed + verification).
   New reference files Dean attached go in reference/ (list them in reference/README.md).
3. Reply: results, the .nex files (sent as files), a short hardware checklist.

## Layout
| Path | What |
|---|---|
| nexclash.py, selftest.py, run_cspect.bat | CLI, acceptance test, CSpect launcher |
| nexclash/ | toolkit modules + engines (chuckie, dizzy5, dizzy6, rainbow, wally, ...) |
| asm/ | hook sources (sjasmplus --zxnext); regenerate the profile hex after any edit |
| docs/profiles/ | per-game profiles (hook hex read by the engines), signatures.json |
| games/ | one file per game/engine: facts, decisions, status, open items, checklist |
| docs/ | BRIEFING, LEARNINGS, VERIFICATION, PLAYBOOK, RECORDING_CHECKLIST, NEXT_REGISTERS |
| docs/reference/ | Next dev guide r3 (text), Next manual (OCR) |
| docs/dean/ | Dean's own copies (prompts, Project instructions) - not agent instructions |
| reference/ | Dean's .z80/.rzx reference inputs (selftest reads them) |
| tools/ | one-off prototypes kept for reference |
