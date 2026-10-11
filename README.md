# specnext / nexclash - Spectrum Next colour-clash remover

Status of every game: STATUS.md. Agents start at CLAUDE.md.

## Quick start

Turns a ZX Spectrum `.z80` snapshot into two Spectrum Next files:
`GAME.nex` (plain conversion) and `GAME_sprites.nex` (player as hardware sprites,
no colour clash), plus a short report.

## Install (once)
1. Python 3.10+ and SkoolKit: `pip install skoolkit`
   (the tool also finds `C:\skoolkit-10.1` if SkoolKit is not pip-installed).
2. `git clone https://github.com/bleughb/specnext C:\dev\specnext` (GitHub Desktop works too).
   Update with `git pull` before each session; agents push their changes as pull requests -
   merge them on GitHub, then pull.

## Check the toolkit
`python selftest.py` rebuilds every game in `reference/` and checks each .nex byte for byte
(`--fast` skips Rainbow Islands, ~50 min). New reference files: reference/README.md.

## Every game
```
python nexclash.py auto GAME.z80
```
Output goes to `GAME_nexclash\`: `GAME.nex`, `GAME_sprites.nex`, `GAME_auto.rzx`,
`GAME_report.txt`, `GAME_profile.json`. Takes about 1-2 minutes (the recording
itself ~5 s; analysis and verification ~30 s each).

Snapshot tips: 48K, taken at the title screen, controls set to keyboard.

Patch memory: `--strategy altrom` (default where proven: the player code sits in the Next's
alternate ROM), `printer` or `slot1` rebuild the older layouts exactly.

## When the report says something is missing
| Report says | Do this |
|---|---|
| `weak recording` / `start=none detected` | add `--start "SPACE"` (or the real start keys, e.g. `--start "4 5, wait 20, 0 5"`) |
| `inputs=none responded` | add `--keys Z,X,SPACE` (Kempston: `--keys K:LEFT,K:RIGHT,K:FIRE`) or `--input kempston` |
| `dead stack ... 54 needed` | record an RZX in Fuse (docs/RECORDING_CHECKLIST.md) and rerun with `--rzx MY.rzx` |
| `unknown engine` / `needs a virtual read` / `FAILED` | start a chat with the `GAME_nexclash` folder + your RZX (docs/dean/PROMPTS.md) |

Your own recordings are always welcome: `--rzx A.rzx --rzx B.rzx` analyses and
verifies each one. A recording you supply is remembered as evidence for that game
(`nexclash/evidence.json`), so it only has to be proved once.

## Quick iterations
```
python nexclash.py record GAME.z80 --start "SPACE" --keys Z,X,SPACE -o try.rzx
python nexclash.py record GAME.z80 --script moves.txt -o scripted.rzx
python nexclash.py record GAME.z80 --room-threshold 0.4 -o busy.rzx   (busy screens)
python nexclash.py rzx info try.rzx
python nexclash.py rzx merge a.rzx b.rzx -o both.rzx
python nexclash.py rzx strip fuse_autosave.rzx -o clean.rzx      (Fuse recording made with autosave on)
python nexclash.py auto GAME.z80 --no-record --rzx both.rzx
python nexclash.py auto GAME.z80 --quick 2000          (analyse/verify first 2000 frames only)
python nexclash.py identify GAME.z80                     (engine + derived addresses)
python nexclash.py convert GAME.z80 --rzx MY.rzx         (plain .nex only)
```
Script format (`--script`, one step per line; `--start` uses the same steps, comma-separated):
```
wait 50            # no input for 50 frames
SPACE 5            # hold SPACE 5 frames
Z+SPACE 20         # hold two keys
K:RIGHT+K:FIRE 30  # Kempston (KR KL KU KD KF also accepted)
```
Recordings made by nexclash are normal RZX files: they replay in SkoolKit's
rzxplay and in Fuse (frame boundaries are defined by instruction counts).

## What it can do today
| Engine | Games | Sprite build |
|---|---|---|
| TID engine (masked sprite + undo buffer) | Fantasy World Dizzy, Magicland Dizzy, and any relocated copy | generic, automatic, verified per run |
| Treasure Island Dizzy (TID + bubble virtual read) | Treasure Island Dizzy | dedicated builder |
| Dizzy 1 XOR engine | Dizzy: The Ultimate Cartoon Adventure | dedicated builder |
| Dizzy V engine (ISR-driven masked sprite + undo buffer) | Spellbound Dizzy, also from a BASIC-loader snapshot | generic, automatic, verified per run |
| Rainbow Islands (128K) | Rainbow Islands | dedicated engine `rainbow`, verified per run |
| Everyone's a Wally (48K game, 128K snapshot) | Everyone's a Wally | dedicated engine `wally`, verified per run |
| Chuckie Egg | Chuckie Egg | dedicated engine `chuckie`, verified per run |
| anything else | - | plain `.nex` only, plus a report to guide the next step |

## Testing on the Next
Copy `GAME_sprites.nex` to the SD card and run it. Check: it starts; the player is
visible and animates; the player hides in inventory/dialogue boxes and room
changes; the title music is unchanged. If something is wrong, record an RZX in
Fuse (autosave OFF) showing it and send it with the report.
`run_cspect.bat` converts and launches CSpect (edit the CSPECT path at the top).

## Everyone's a Wally (128K snapshot)
    python nexclash.py auto wally.z80 --rzx my_play.rzx
Outputs wally.nex (plain) and wally_sprites.nex (gang members and masked objects as sprites).

## Chuckie Egg
    python nexclash.py auto Chuckie_Egg.z80 --rzx Chuckie_Egg.rzx --no-record
Outputs Chuckie_Egg.nex (plain) and Chuckie_Egg_sprites.nex (player, hens, duck as sprites).

## Rainbow Islands (128K)
    python nexclash.py auto rainbow.z80 --rzx my_play.rzx --no-record [--ink white] [--outline black|blue|transparent|#RRGGBB] [--class-colours map.json]
Outputs rainbow.nex (plain) and rainbow_sprites.nex. Plain 128K conversion of other games:
`python nexclash.py convert game.z80 --tail ADDR` (ADDR below 0xC000, proven unused). Autosave snapshots in the RZX are stripped automatically.
