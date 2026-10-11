# Dean's prompts - FOR DEAN, not agent instructions

The repo is the master copy; agents read CLAUDE.md themselves. Attach the game's .z80/.rzx in
the first message (or say they are already in reference/). One game per chat.

## New game (the setup prompt)
> Repo: github.com/bleughb/specnext (follow CLAUDE.md). Task: remove attribute clash from
> <GAME> (<file>.z80, attached with my RZX). Sprites: <which figures>. Everything else stays on
> the ULA unless analysis shows it clashes (then ask me).

## Report says FAILED / unknown engine / virtual read needed
> Repo: github.com/bleughb/specnext. `nexclash auto` on <GAME> says <...>; report folder, .z80
> and my RZX attached. Diagnose and extend nexclash so `auto` handles it.

## Hardware problem
> Repo: github.com/bleughb/specnext. <GAME>_sprites.nex on the Next: <symptom>. RZX attached
> (autosave off). Find the cause, fix, re-verify.

## Hardware result
> Repo: github.com/bleughb/specnext. <GAME>_sprites.nex on the Next: <runs / fault>.
> Checklist: <1 ok, 2 ok, ...>. Record it (games file + STATUS).

## Toolkit work
> Repo: github.com/bleughb/specnext. Do STATUS.md open work item <N>.

## Hygiene
- Merge the agent's pull request on GitHub, then `git pull` locally.
- Recordings: Fuse, autosave OFF ("Record from snapshot"), keyboard controls
  (docs/RECORDING_CHECKLIST.md). Name them like the game: <game>.z80 / <game>.rzx.
