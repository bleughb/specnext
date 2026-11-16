# R-Type prototype: setup and tests

The tests for the Layer 2 + hardware sprite prototype (`../l2scroll.*`, `../l2sprites*`). Read
nexclash `games/r_type.md` ("Next session") first.

## Choose a setup

There are two ways to run these tools. Both use the same scripts.

**A. Duplicate the original owner's local Windows setup** (recommended on Windows). Everything below
the "A" heading must exist.

**B. Use the original Linux workspace layout** (`/workspace/work`, `/workspace/scratch`), as the
earlier cloud sessions did. The defaults already point there. Install JNext 1.2.0 to
`/workspace/work/jnext-bin/root/usr/bin/jnext`, or set `NEXCLASH_JNEXT`.

Either way, any path can be overridden with an environment variable (table below), so no setup has
to match exactly.

### A. Local Windows setup

1. Clone both repositories side by side, for example `C:\1NEXT\nexclash` and `C:\1NEXT\specnext`.
   The scripts find each other through that sibling layout.
2. Install Python 3 with `pip install -r nexclash/requirements.txt` (SkoolKit, Pillow). Run
   commands with `py -3`.
3. Install JNext 1.2.0 for Windows, for example `C:\1NEXT\jnext-1.2.0-windows-x64\jnext.exe`.
4. Get a NextZXOS SD card image, for example `C:\1NEXT\cspect-next-2gb.img`. It's the owner's
   private image: never commit it. JNext always opens it read-only.
5. The parked intake scripts in `..` (the earlier route) hardcode `/workspace/...`. To run them
   unchanged, link those paths once from an administrator-free command prompt:

   ```
   mkdir C:\workspace
   mklink /J C:\workspace\work C:\1NEXT\rtype_work
   mklink /J C:\workspace\scratch C:\1NEXT\rtype_scratch
   mklink /H C:\1NEXT\rtype_scratch\cspect-next-2gb.img C:\1NEXT\cspect-next-2gb.img
   ```

   The tools in this folder do not need the links if `RTYPE_WORK` and `NEXCLASH_JNEXT_CARD` are set.
6. Optional: CSpect, see below.

### Environment variables

| Variable | Meaning | Default |
|---|---|---|
| `RTYPE_WORK` | work folder for builds, logs, pictures (never committed) | `C:/workspace/work` on Windows, `/workspace/work` elsewhere |
| `NEXCLASH_JNEXT` | JNext executable | `jnext` on PATH, then `C:/1NEXT/jnext-1.2.0-windows-x64/jnext.exe` |
| `NEXCLASH_JNEXT_CARD` | SD card image for JNext | `.../scratch/cspect-next-2gb.img`, then `C:/1NEXT/cspect-next-2gb.img` |
| `CSPECT_EXE` | CSpect executable | `C:/CSpect/CSpect.exe` if present |
| `CSPECT_MCP_URL` | CSpect control server | `http://127.0.0.1:8765/mcp` |
| `RTYPE_EMULATOR` | `auto`, `cspect` or `jnext` | `auto` |
| `RTYPE_CSPECT_START` | `0` = never start CSpect, only use one already running | start it |

## Emulator order

`auto` uses **CSpect first, then JNext**:

1. **CSpect**, when its control server answers, or when `CSPECT_EXE` exists and opens the server
   when started with `-mcp`. The server takes about 20 seconds to open.
   - **The control server needs CSpect's paid Builder tier.** Most users' CSpect will not open it.
     `auto` then closes that CSpect, remembers the result in `RTYPE_WORK/.cspect_no_mcp` (delete
     that file after upgrading), and uses JNext.
   - The free CSpect is still useful for playing a build by hand.
2. **JNext**, which needs the SD card image. This is the standard route for most users.
3. Neither: the tool stops and names what is missing.

**What only JNext can do.** A test that presses keys at exact game updates (`compare.py --input`,
`gameover.py`) always uses JNext, and says so. CSpect presses keys in real time, which is not
repeatable.

**The two emulators differ in timing.** CSpect runs 28MHz without memory wait states, so busy
updates take 3 frames there where JNext sometimes shows 4. Compare builds only on the same emulator.
The tools never mix them.

To use CSpect from Claude Code as well, add a user-level MCP server named `cspect` (HTTP,
`http://127.0.0.1:8765/mcp`). Then start CSpect with `-mcp` before starting the session.

## Tests

From this folder:

| Command | What it checks | Emulator |
|---|---|---|
| `py -3 smoke.py [NEX] [--updates 200]` | Whole game. It builds the full game unless given a NEX, then checks: the technical specification screen then the title, no reset, fire starts a game, and pacing (none over 6 frames, at most a quarter over 3) | either |
| `py -3 compare.py [--frames ...] [--updates ...]` | The sprite build against a same-speed control from RZX snapshots: equal pacing (within `--slow`) and pictures within `--diff` pixels. A difference explained by the builds being one update apart is reported, not failed | either |
| `py -3 compare.py --input [--seed N]` | The same, with random keys at exact game updates. Every key must be pressed. Pictures are information only: the game's randomness uses the R register, which the hooks change, so play diverges by design | JNext |
| `py -3 gameover.py` | Game over to name entry, using a test copy with a 000000 high-score table. Checks Layer 2 and sprites are off, the speed is 3.5MHz, and the entry keys work | JNext |
| `py -3 shots.py NEX 20,60` | Screenshots at given updates, and frames per update | either |

Each test prints `PASS` or `FAIL` and exits with status 1 on failure. Before pushing changes to the
prototype, run `smoke.py` and `compare.py` (all snapshots), and `gameover.py` when anything around
titles, game over or speed changed.

## Known limits

- Level changes are not tested automatically: the recording snapshots start inside levels. Play
  one through with the full build.
- Screenshots in CSpect are taken two frames after the update ends: CSpect shows a screen write
  made after the beam passed one frame later.
