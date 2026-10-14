# El Capitan Trueno + nexclash (notes of 2026-10-13)

The host tests the author's toolkit (nexclash, bleughb) with a new game: El Capitan Trueno (1990, Dinamic).
His prompt (the author's "New game" prompt): "New game: GAME Snapshot and RZX attached. Repos: bleughb/nexclash +
bleughb/specnext - follow nexclash/CLAUDE.md". The author said it is his first public GitHub, be nice.

## Links
- https://github.com/bleughb/nexclash (the toolkit, GPL-3.0; CLAUDE.md = instructions, docs/PLAYBOOK.md = phases A-C)
- https://github.com/bleughb/specnext (meant to be PRIVATE, but GitHub shows it public on 2026-10-13: 15 snapshots, 12 RZX,
  28 .nex of commercial games, the Next manual as text; the host wrote to the author about it; no keys/passwords seen in file names or docs)

## What is here
- `Capitan Trueno, El (1990)(Dinamic)(ES).z80` - the host's snapshot. v1 header (48K): PC 0xEEEE, SP 0xFFF6, IFF1 0, IM 2, I 0xED.
  Interrupts off and PC in the middle of nowhere: it was probably taken at a strange moment (the toolkit wants the title screen).
- `trueno1.rzx` - the host's recording: 53542 frames (~18 minutes). Strong; probably enough for verifying, no new one needed.
- `tk/nexclash-0.1.4/` - the release v0.1.4 zip, unpacked (checked: no network code in `patch`, no eval/os.system; the only
  network use is sjasm.py cloning sjasmplus, not needed here and on Windows not reachable). Output of my runs: `tk/nexclash-0.1.4/Trueno_nexclash/`.
  `tk/nexclash-0.1.4/Trueno.z80` is a copy of the snapshot for the tool.
- `lib/` - SkoolKit 10.1 (pip --target); run with `PYTHONPATH=trueno/lib` from `tk/nexclash-0.1.4/`.

## Results so far
- `python nexclash.py patch Trueno.z80` -> engine "unknown" (no known signature); plain `Trueno.nex` built (tail at 0xFF96,
  stack_low_water 0xFBF7), sprite build impossible without adding the game ("new" = hours of engine work, Opus, fresh session).
- With `--rzx ../../trueno1.rzx` the run printed nothing within the time limit (18 min of recording; likely just slow).
- **The plain Trueno.nex crashes at once** (the host's test; where he ran it and what he saw: not yet asked/answered).

## Next step (agreed 2026-10-13)
Take a snapshot from `trueno1.rzx` (title screen or in-game; `nexclash.py rzx ...` has info/merge/strip) and build a plain
`.nex` from THAT; he tests it. If it runs, the game can be added with the author's "new" flow (Opus, new session, ask the host
the three picture questions: which figures become sprites, their colours, what stays on the ULA).

## 2026-10-13, morning: snapshot from the RZX
- `rzxplay.py --no-screen --fps 0 --stop N trueno1.rzx snaps/fN.z80` (SkoolKit) + `sna2img.py` for a look. Frames 1-200: blank
  screen; frame 300: the game has just started (score 0); 500+ in game. No title screen in the recording.
- `snaps/` - the snapshots and PNGs (temporary; delete when the test is over).
- Frame 300: PC 0x899F, SP 0xEECC, DI, IM 2, I 0xED. IM2 table 0xED00-0xEE00 all 0xEE, ISR at 0xEEEE = JP 0xA1CB.
- `nexclash.py patch Trueno300.z80` -> `Trueno300.nex` (copy in `trueno/`), same warning "no proven-safe tail location":
  its 7 s auto recording gives stack low water 0xEE9E (only 46 bytes of dead stack, 54 needed), printer buffer used,
  ROM never used. The default tail is SP-96 = 0xEE6C-0xEECB: zeros + old stack bytes; it does not touch the IM2 table,
  the ISR or the data at 0xEE01-0xEE55. Probably safe, not proven. Waiting for the host's test.

## 2026-10-13: CAUSE FOUND AND FIXED - the start-up tail above 0xC000
- The stub runs with its own bank 10 at 0xC000-0xFFFF, copies the 79-byte tail there (0xFF97 for the host's .z80,
  0xEE6D for frame 300) and jumps to it; the tail's OUT 0x7FFD maps bank 0 back at 0xC000 and the tail vanishes
  from under the PC. z80tonex.choose_tail_addr refuses tails above 0xC000 only for 128K (`snap.is128`), not for 48K.
  Other 48K games get 0x5B00 (empty printer buffer); Trueno uses the printer buffer, so the tail went below SP.
- The .nex memory (banks 5, 2, 0) equals the .z80 byte for byte: the data conversion is fine.
- The toolkit's own boot simulation catches it: `nextboot.check` on the old Trueno.nex -> "boot did not reach PC 61166
  (at 15086)"; the plain build in `patch` does not run this check.
- Safe place: `nexclash.py scan --rzx trueno1.rzx --range 0x5B00-0xBFFF` over the whole recording (53543 frames, ~18 min):
  0xA6C9-0xAAA2 is write-first (986 bytes; old init code later used as a buffer). Output: `snaps/scan_full.txt`.
- Rebuilt from the host's .z80: `zt.convert('Trueno.z80', 'trueno/Trueno.nex', 0xA6C9, True)` -> tail 0xA6C9-0xA717,
  boot simulation clean. In MAME (Browser -> TRUENO.NEX): the game menu, key 1 starts the game. Host to play-test.
- For the author (gently): the 128K rule in choose_tail_addr applies to 48K too; plain builds could run nextboot.check.

## 2026-10-13: depth demo (`demo/`)
- Host's decisions: sprites for the hero, enemies and coins; colours as in the game for now; bushes stay in front,
  pixel-exact (the hero shows between the leaves - nicer than the game, which cuts whole byte columns).
- Idea (host): Layer 2 palette priority bit (bit 7 of the 2nd byte; manual p.102-103, 110) puts Layer 2 pixels above
  sprites. `LAYER PALETTE n,i,v` takes only 9 bits, so the palette goes through a bank: `LAYER PALETTE 0 BANK b,0`.
- `demo/make_assets.py` -> trueno.scr (frame 2340, hero erased with frame 2100), bush.sl2 (bush ink pixels, attr 0x44,
  colour 0x1C), bush.pal (default + priority on 0x1C), hero.spr (4 patterns, white only, no mask yet).
- `demo/depth.bas.txt` -> depth.bas (cursor keys 5/8 via IN, SPACE quits). `txt2bas -t` flags every @label (also in
  parser.bas.txt) - a checker gap, not an error. Host tests it himself.
- Host's test (2026-10-13): the hero hides behind the bushes. Fixes done: solid bushes (closing r=2 + filled holes,
  black with priority inside the silhouette); hero body solid black (outline + closing r=1 + filled holes), no see-through.
- Later (host's idea): colour the bushes - instead of black inside, a shade between green and black or similar
  shades, for realism.
- Demo v2 (host: "everything works"): the three heroes from the game's frame table (Captain 98+95, Crispin 15
  yellow, Goliath 75), 32x48 boxes = 6 sprites each, keys 1/2/3, mirroring by direction; status bar frame line
  whole in Layer 2 (x 6-249, under the items). Start in MAME: `python trueno/demo/run_demo.py` (puts files into
  /tdemo, starts depth.bas at normal speed). BASIC is slow (6 SPRITE per step) - fine for a demo.
- Demo v3 (host: "all fine, you caught the idea"): enemies and items from the frame table - panther 5-8 runs
  across the screen (also behind the bushes), goblin 9-12, swordsman 53/55, items 24-29 on the ground. Unified
  sprites (anchor + pattern-relative parts, parts interleaved so animation = anchor pattern), enemies move and
  animate by SPRITE CONTINUE (flags 128 = mirror by direction) with SPRITE MOVE INT in the loop. Colour = the
  frame's first byte (attribute). Mirror: hero anchor moved +16 when mirrored (assumed parts reflect about the
  anchor); the host saw no jumps. 56 of 64 patterns used.
- NEXT (fresh session, Opus): the real game - hook the figure plotter (0x82DF / 0x844D), show figures as sprites
  (frame table -> patterns, colour from the header byte), foreground from the game's own column bit map (0x872C, IX)
  -> Layer 2 priority pixels per screen, status bar line in Layer 2; then the author's PLAYBOOK steps (verify, etc).

## TODO (host, 2026-10-13): improve the author's instructions
Two deliverables at the end of the work:
1. The GENERAL part (CLAUDE.md, docs/PLAYBOOK.md, BRIEFING/LEARNINGS, tools) - fix what is wrong or
   incomplete, add better methods found here. Found so far:
   - choose_tail_addr: the "tail below 0xC000" rule applies to 48K too; plain builds should run
     nextboot.check (the Trueno crash).
   - simrun/analysis commands run per-instruction Python hooks: ~100x slower than needed for
     frame-level questions. SkoolKit's C simulator + a patched RZXTracer.next_frame (memory checked
     at the end of each frame) replays 53543 frames in 4-8 s. Worth a shared fast mode/command.
   - Sprite body: do not guess it by morphology; call the game's own plotter in the simulator on a
     0x00 buffer (ink) and a 0xFF buffer (cleared = mask) - exact silhouette with no code reading.
   - Back-buffer games: plotter untouched + clean attributes at the copy + solid sprites with the
     game's mask = game memory identical to the original (verification gets simple).
   - Depth: Layer 2 palette priority bit over sprites (host's idea), from the game's own
     foreground map; an alternative to per-sprite masking (Commando).
   - Capturing shapes through the game's plotter: take the graphic and its trailing data (mask, column
     bits) from ONE consistent state; a game that mirrors in place flips them together (Trueno: a
     catalogue graphic written over a mirrored state got a mirrored mask).
   - Menus and windows (host, 2026-10-13): ALWAYS check whether the game opens menus, pause or
     message windows over the play area. They are drawn in the ULA, so Layer 2 foreground and the
     sprites cover them. Needs a workaround per game: find the window routine (read PC/stack while it
     is up), wrap it in a stub that hides Layer 2 (NextReg 0x69) and sprites (0x15) and shows them
     again on return (Trueno: 0xA375 JP 0xA501 -> e_mnu). Also: what was removed from the ULA
     (figures, bushes) is missing while the layers are off - host wants it back for that time.
   WRITTEN 2026-10-13 evening into tk/nexclash-0.1.4: CLAUDE.md (tail rule), docs/PLAYBOOK.md (step 0,
   3b, step 4 table, rounds), docs/LEARNINGS.md (1.3 ROM3, 2.1, 2.3, 2.6), docs/BRIEFING.md C2 17-19;
   recipe: games/el_capitan_trueno.md 5b-5g. Backups of the old files: session scratchpad only.
   Agreed with the host 2026-10-13 (evening) for the general instructions:
   - Menus / windows: ASK the human whether the game has a pause, menus or message windows over the
     play area; if he does not know, offer to search the code for them.
   - Every path to the plotter, not only the hooked entry (Trueno: the dragon bar via 0x82E4).
   - Screens without the normal build (special modes, the end screen, transitions): clear or hide
     Layer 2 and the sprites on each such path.
   - A snapshot taken at the title shows the screen already drawn: a patch to drawing code does not
     show the first time - patch the snapshot's screen memory too.
   - Scenery clash: OFFER the fix-cells method (Layer 2 without priority, a sheet for the human),
     explaining that an AI is not the best helper at pixel art: the AI copies the cells as they are
     and builds the drawing in; the human draws. Same reason for redrawing figures.
   - Memory budget of per-screen tables (8K page per screen; unexpanded Next ~95 pages).
   - MAME debugging: switch layers off one by one (NextReg 0x15/0x68/0x69 from Lua, emu.step() while
     paused), sprites from memory.shares[":sprites:attr_ram"]: the human sees the guilty layer at once.
   - Work rhythm: OFFER to fix the whole list first and check in one emulator pass; for a long game it
     is wiser to fix many things per pass (the places are far from the start).
   - Cheats: OFFER to find one at the start (immortality etc.) and to switch it off at the end, then
     check the game over.
   - Cover check (build/check_cover.py): at every copy, buffer-before vs scenery-after = the figures'
     pixels; each must lie under an opaque sprite pixel of the hooks' model. Found two real bugs.
   - Graphics catalogue: hash the gfx at each frame end; in-place mirroring leaves transient
     half-mirrored states (1-6 frames each) - group by mirror and keep the real ones.
2. The GAME file games/el_capitan_trueno.md must end with a recipe written for an AI: steps,
   addresses, commands and checks, so a new session repeats the build without the research.

## Host's idea (2026-10-13), if the hit look cannot be fixed otherwise
Clean the Captain's graphics: the figure is two-colour; keep the white, draw a 1-pixel black outline
around it, fill the fully enclosed inner areas (the host will advise on the fill).

## Hit flash: the path so far (2026-10-13) - keep as the fallback (host)
- Game: descriptor bit 1 = hit; the plotter fills the whole mask in the ULA, the original shows a
  white silhouette (ragged ring = the black outline turned white).
- Tried: (1) palette offset silhouette -> MAME made index 0 opaque under an offset (whole 16x16
  boxes); (2) own silhouette shapes (fdir) -> faithful but ugly; (3) now: every figure blinks on
  alternate renders between the normal drawing and the same drawing with bright red ink (yellow for
  red figures), black body kept (patterns.py BLINK/HIT_INK, asm resd + V_BLK).
- Host's look (3): better, still some white flashes, rarer. Cause not found yet (candidates:
  pattern memory overflow -> a figure without sprite for a render; a hit drawn by another routine).
- Next try first: clean the graphics (host's idea above), then come back here if needed.
- Host (2026-10-13): with the cleaned graphics, the hit look = the cleaned drawing inverted (black <->
  white), the same for the other figures. Constraint: the hit sprite's opaque area must still cover
  the game's whole mask (the plotter fills it in the ULA): mask pixels outside the new outline stay
  black.

## Current build (2026-10-13, evening)
- Host's idea: figures are not drawn into the ULA at all - data patch 0x87BE (LD IX,0xEF60 -> 0x3B00, all
  0xFF in the ROM) puts every cell "behind the foreground": the plotter saves/restores as usual but
  draws nothing and paints no attribute. Replaces the 0x889C attr patch and the pre-copy restore.
  check_nodraw.py: RAM differs only in the generated row code, unread restore-list bytes, dead stack.
- Heroes: the host's redrawn sheet gfx/heroes_clean.png (hit = inverted). Others: hit = red ink.
  No own blinking (the game toggles its hit bit; ours cancelled it out when in phase).
- TEMPORARY: CHEAT_IMMORTAL in build/make_nex.py (0x7A1F LD (HL),A -> NOP). REMOVE before delivery.
- Rope (host, 2026-10-13): the rope on some screens is part of the SCENERY (buffer column 15 holds
  the rope pixels; the screen builder gives that column a yellow attribute 0x46 in a white 0x47 wall),
  so the wall pixels sharing its cells turn yellow - the original looks the same. Fix later: such
  cells in Layer 2 in two colours (like the bushes), or redrawn tiles.
- Crispin flashes white sometimes when hit (host). His frames 4, 13-16, 73, 74 are all yellow (0x46),
  the inverted hit shape is yellow, so the white comes from elsewhere - maybe another frame set used
  for his hit (host's guess: the Captain's). The RZX has 7 hits on frame 4 (flags 0x07/0x87):
  list the figures of those renders (debug_render.py) next session.
- Shake (Goliath landing) handled: hook 0x887D sets NextReg 0x7F bit 6, the commit moves Layer 2
  (NextReg 0x17 = 184) and the sprites 8 lines down for that copy. Host: "seems fine".
- Bushes: solid rows from the leftmost to the rightmost leaf per run (temporary; the host will
  rework the bushes). Frame line y 14 drawn whole in Layer 2 again. Coins 25-31 redrawn by the host
  (gfx/coins.png, colour sheet).

## Done 2026-10-13 afternoon (Nika 13.10-g)
- Goblins 9-12: colour sheet gfx/goblins.png (clean_sheet.py --colour, auto 1-pixel outline; host: "keep
  it so for now"), read by patterns.py colour_sheet(hit=True): hit = every non-black pixel red.
- Foreground in Layer 2, two rules (host): bushes (attr & 0x47 = 0x44) = silhouette runs as before; every
  other foreground cell (pillars, masonry, grass, bell) drawn WHOLE (8x8, as the original hides figures).
  Host checked pillars: OK.
- ROOT BUG FOUND: altrom strategy copies the system ROM3 (NextZXOS) into the alt ROM and only lo..hi from
  page 24 over it; NextZXOS has DATA at 0x3B00-0x3CFF (not 0xFF as Sinclair's ROM), so the "all 0xFF" map
  patch let the plotter draw figures into the ULA (clash; bell rope stuck in Layer 2). Fix: make_nex.py
  altrom = (ROM_ORG, 0x3D00). Verified in MAME: 512 bytes 0xFF. nexclash's nextboot.py self-check uses
  rom48() for ROM3, so it cannot see this -> TODO for the author (check against the real ROM3, or copy
  any ROM area a patch relies on). Host: bell rope OK after the fix.
- Screen change: e_scr clears V_N (old figures recorded before the builder) and turns sprites off
  (NextReg 0x15 = 0); the commit turns them on (0x15 = 1). Reason: the copy takes most of a frame, old
  sprites flashed over the new screen. NOT YET CHECKED by the host.
- Wall rope (stained-glass hall, column 15, attr 0x46 in a 0x45 wall): ropec in l2map pass (2a): a
  non-foreground cell whose pixels under the link mask (frame 162: 0x3C rows, ink 10 08 18 18 x2) or
  knot mask (frame 161) match -> Layer 2 WITHOUT priority (palette 32-47, make_nex l2_palette): rope in
  its colours (knots stay yellow, host), wall pixels in the left (x 0-3) / right (x 4-7) neighbour's
  colours; OLDROPE 0x1980 for the clear. Host checked in MAME: OK.

- Host's sheets (2026-10-13): gfx/creatures.png (clean_sheet.py --colour, my auto outline: dogs 5-8,
  spider 17-23, creature 49-52, rats 57-65, dragon 66-68 ("rat boss" before; host), skeleton 106-122, sitting skeleton 209) and
  gfx/rest.png (--raw, as the game draws: 24, 32-43, 45-48, 69-72, 92, 99-104, 156, 157, 192) - the
  host edits them by hand; patterns.py reads goblins/creatures/rest with hit = red. clean_sheet.py:
  --colour takes each pixel's cell colour, cell size = the largest shape + 2. The +1 pixel border made
  1378 patterns (22 pages): Layer 2 moved to banks 27-29 (pages 54-59; asm L2BANK/L2PAGE, make_nex).

## Done 2026-10-13 evening: bushes
- The screen is a list of scenery objects (table 0x6914, groups nest; leaf = frame 0x80-0xD0 plotted by
  0x62BE, the figure plotter 0x82E4). Bushes = frames 0x84-0x8B (8x8, attr 0x44; 16 tiles with mirrors),
  drawn LAST, their black paper hides the wall. The build depends only on the screen number (0x6857
  zeroes 0xE60D). Screen change = 0x65C3 (screen in 0xE60B); ~0.5 s at 3.5 MHz (so no double build).
- build/bush_walls.py: simulates the screen change with/without bush frames (bush screens in part 1:
  0-3), writes bushwall.bin (pages 60-64, banks 30-32): per bush cell 64 Layer 2 bytes = the host's sheet
  gfx/bush_tiles.png (non-pink = bush, priority) over the wall (pink = wall, no priority). Hooks pass (2w)
  copies them; (2b) silhouette rule only for screens without a table. Host drew the bushes; checked in
  MAME: "у нас получилось".
- build/bush_round.py N: propagates the host's edits (sheet vs build/bush_base.png) to every cell of the
  same game tile (+ mirrors); backups snaps/bush_tiles.hostN.bak.png (rounds 1-6 done). Only new tiles
  (cells drawn unlike their game tile) would be lost by a later round on the same tile - warn him.
- Pillar grey dot: lone pixel of frame 0x91 (0xD609, attr 07) removed, DATA_SITES 0xD615 A2->A0 (host OK
  to keep it black, no Layer 2 tricks).

## CLEANUP (2026-10-14, host: keep only what the build needs)
- Removed: snaps/ (110 MB of debug snapshots, logs, sheet backups), demo/ (the depth demo), Trueno.nex /
  Trueno300.nex (plain builds), tk/.../Trueno300.z80 + Trueno300_nexclash/, __pycache__. References to
  snaps/... below and in games/el_capitan_trueno.md are history. snaps/f5000.z80 removed too: shapes.py takes the same state from trueno1.rzx (after 5000 frames; shapes.json identical).
  Kept: the .z80, trueno1.rzx, build/, gfx/, lib/, tk/ (incl. Trueno_nexclash/ report for
  contribute), Trueno_sprites.nex. Rebuild after the cleanup: identical to the nexpatch page.
- Trueno_sprites.nex is 328K now (packed fix/bush table, Layer 2 filled at start-up): host ran it in MAME.

## ENGLISH VERSION (2026-10-14, host)
- build/texts_en.py + make_nex.py --en -> Trueno_sprites_en.nex (default build unchanged, md5 a9befbb2).
  Menu KEYBOARD/KEMPSTON/SINCLAIR/REDEFINE, keys UP DOWN LEFT RIGHT FIRE CAPTAIN CRISPIN GOLIATH PAUSE
  ABORT, CONTINUE, ACCESS CODE, credits CODE / GRAPHICS / (c) DINAMIC AND GAMESOFT 1989 (host: CODE).
  The title in the snapshot is redrawn by the game's own print routines in the simulator.
  run_nex.py --watch --en. NOT checked by the host yet. nexpatch page: language choice, both patches
  inside (host: "genius"), English output name "... EN.nex" - to do.

## REMIND THE HOST: 2026-10-15 - a small readme for Facebook
- Two files to post: a short readme + the nexpatch page (nexpatch/out/Capitan Trueno.html), so that more
  people test it and give their opinion.

## REMIND THE HOST (2026-10-14): upload to the author
- Path (CONTRIBUTING.md): nexclash.py contribute Trueno --report <report> -> zip (toolkit files only, no
  game data) -> Dropbox request link (no account) or a PR to bleughb/nexclash; the maintainers put the
  game into the private repo. Before it: recipe step 6 (move build/ into nexclash/trueno.py + profile +
  docs/records/el_capitan_trueno.json, differential check of the hooks); the host's sheets are derived
  from game graphics (store them as a difference: see the NEX patcher in PROJECTS.md). Running
  contribute = the author's code: only with the host's consent.

## NEXT SESSION (from 2026-10-13, ~17:50) - start here
State: build/make_nex.py -> Trueno_sprites.nex; run `python trueno/build/run_nex.py --watch`; hooks
assembled from trueno/build/asm: `../../../_books/sjasmplus/sjasmplus.exe --nologo --lst=trueno_hooks.lst
--sym=trueno_hooks.sym ../../tk/nexclash-0.1.4/asm/trueno_hooks.asm`, then make_nex.py; patterns from
the host's sheets: python patterns.py first. Bushes: bush_walls.py after editing gfx/bush_tiles.png.
TEMPORARY immortality cheat (remove before delivery). Do not rebuild while the host is still drawing.
Open list (host picks):
1. Host has not yet looked closely at his new sheets in the game (creatures.png, rest.png).
   2026-10-13 18:09: host fixed the rat graphics in creatures.png - next build: patterns.py, then make_nex.py.
   Built and running 2026-10-13 ~18:15.
7. Host list 2026-10-13 (he will show each place in the game).
   CHECKED by the host in MAME (2026-10-13): bell (17), well arch + cypresses, skeletons, dragon bar
   and Layer 2, access code screen ULA only; old list: wall rope + screen changes fixed, spider done,
   leaves outside bushes done; explosions OK, fix cells cleared on screen change OK. STILL TO CHECK:
   title menu (first and after a game), the last cypress tweak (later stage); Crispin's white flash OK; CHEAT_IMMORTAL = False since 2026-10-13 (host): no-cheat run OK, game over OK (the original has no game over screen: straight back to the title menu, host); author instructions + AI recipe.
   - bell: clash
   - barrels on the left -> FIX CELLS (build/fix_cells.py, sheet gfx/fix_tiles.png, merged by bush_walls.py into
     bushwall.bin; Layer 2 without priority; table cells marked in OLDROPE so they clear on a screen
     change). Screens 45-47, frames 0xCB/0xCC; the wall is the game's own (built without the frames).
     Host rules: per group of barrels (pyramid, lonely one): right of the group 1 px gap, rounded
     tops wrapped; left only the top-left shoulder of each row's leftmost barrel (top to widest
     line, 1 px); between the barrels and below the shoulders unchanged (stay close to the original).
     0xCC is the wall's cut edge beside the barrels (hidden for the wall build, not a barrel).
     Draft accepted 2026-10-13; host is redrawing gfx/fix_tiles.png - do not regenerate it.
     Not yet in a build: run bush_walls.py + make_nex.py after his sheet (hooks already mark
     table cells in OLDROPE). Check in MAME only together with the rest of the list.
   - acrobat skeleton
   - dragon (host first called it the big rat) bug: wrong tiles show its life on the right -> screen 34 (clear mode): energy bar = frame 0x69 x (0xE858),
     then 0x7D from x 0x26, drawn by 0x8A0C via 0x82E4 (past the figure hook) into the ULA buffer;
     colours (red lost / green left, host video frame) were in 0xF13C, the copy took 0xEF98 -> white.
     Fix e_att (0x889B): screen 34 copies attributes from 0xF13C. Built, NOT checked at
     the boss in the next run. Paused state confirmed: 0xF13C row 1 = 42 42 42 44 ... (3 red cells =
     the 6 red bars, host). Blue blob = Layer 2 (host: gone with Layer 2 off): s_cm kept the rebuild
     request in clear mode, so the old screen's Layer 2 stayed; now screen 34 clears Layer 2 (ZMAP).
   - well exit: small clash (maybe not critical) -> fix cells: arch 0x32-0x34 (screen 18, copied, host drew);
     cypresses 0xAA-0xAD over the red roof (ink 2), 9 screens 18-24/58/59, 4 distinct cells on the
     sheet, the rest by look (host drew). In the build, not checked in MAME yet.
   - MEMORY: bushwall.bin uses one 8K page per screen (now pages 60-83); an unexpanded Next has
     pages up to ~95 -> pack several screens per page if more places come.
   - "C??VE DE ACCESSO" (LLAVE?): letters overlapped -> screen 60 = end of part 1, the access code screen: 0x65CD
     JP Z 0x5DCD (CALL 0x5E0E, text 0x6000, key 0xA378, then 0x983A, JP 0x61C1 title). No screen is
     built, so the old Layer 2 and sprites stayed. Fix e_end at 0x5DCD: sprites + Layer 2 off; the
     next game's e_scr / first commit turn them on. Host: ULA only there. Built, not checked yet.
   - explosions after hits: colour is right (red as the original), but the outline is untidy (in the
     original graphic, host) -> explosions = frames 0-3 (14x16, 20x18, 24x24, 24x24, attr 0x42), shown
     together with the coin frames 25/26; were on no sheet. gfx/explosions.png (clean_sheet.py --raw
     Explosions=0-3), read by patterns.py like rest.png; host redrew them. Built, not checked yet.
   - title menu: remove the colour on/off item ("5 COLOR ON"): even in the original it only took the
     colour off the sprites, never made the game black and white (host 2026-10-13) -> data patch 0x5FF1 05->04: the menu
     (items 0x5ED1: 1 TECLADO, 2 KEMPSTON, 3 SINCLAIR, 4 REDEFINIR, 5 COLOR ON, handlers 0x5F98, key
     codes 0x1B-0x1F; letters 0x00=A, 0x26=space) draws and polls B items. The snapshot has the menu
     already on screen: make_nex wipes item 5 pixels too (y 112-119, x 88-175). Host checks: first
     menu AND the menu after leaving a game.
   - REMINDER (host): when CHEAT_IMMORTAL is removed, check the game over.
   - in-game pause/menu window (CONTINUAR, ULA) is covered by Layer 2 bushes and sprites
     (snaps/mame/pause1.png). Options: (a) hide Layer 2 + sprites while the window is open
     (NextReg 0x69 / 0x15, hook menu entry/exit); (b) save+clear Layer 2 under the window rect,
     hide overlapping sprites, restore on exit. Proposed (a) first; host decides.
     Host: (a) first. Menu: 0xA36C key poll -> 0xA375 JP 0xA501 (menu is a subroutine, fire = RET NC
     at 0xA540, window drawn by 0xA5DA). Hook: 0xA375 -> e_mnu (sprites/L2 off, CALL 0xA501, on, RET).
     Host note: keep a default ULA picture (figures, bushes as the original) so that switching the
     Next layers off at pause loses little from the screen - later task.
     (He means: whatever we removed from the ULA must come back. Permanently = clash returns around
     the figures, so only for the pause time; to think over after the simple version.)
     DONE (a) 2026-10-13: e_mnu at 0xA375, host checked in MAME: "nothing much lost, not critical".
2. Spider: host says it needs work (ask what).
3. Crispin's white flash when hit; no-colour mode ("5 COLOR ON" off): sprites stay coloured.
4. Leaves outside bush cells (outline into pink cells): needs extra table cells + clearing at screen change.
5. Host checks still open: wall rope, screen changes (no foreign sprites).
6. Verification for the author, hardware checklist, move into nexclash/trueno.py, recipe for an AI,
   instruction improvements (TODO above + the ROM3 finding).
