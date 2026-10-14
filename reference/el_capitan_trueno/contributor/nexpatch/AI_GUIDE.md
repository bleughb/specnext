# nexpatch - guide for an AI that makes a Spectrum Next mod of a snapshot game

Goal: the user gets a modified game as a `.nex` built from **their own** `.z80`, and nobody
distributes game data. You build the mod as usual (any toolchain), then `nexpatch.py make` turns the
finished `.nex` into one HTML page. The page holds only the difference to the snapshot, encrypted
with a key taken from the snapshot itself; the user opens it in a browser, picks the `.z80`, presses
**Make NEX**.

## 1. Build the mod so that the game's memory changes as little as possible
The patch copies everything the `.nex` shares with the snapshot (its file bytes and its unpacked
memory banks) and carries the rest as "own bytes". Own bytes are what you distribute (encrypted,
but still yours to justify), so keep them for your own work only.
- **Game memory = the snapshot.** In a 48K `.nex` the banks 5, 2, 0 hold 0x4000-0xFFFF exactly in
  snapshot order; keep them identical except for the patch sites. Do not relocate, repack or
  "tidy" game code or data.
- **Patch sites are small**: a jump to a hook (3 bytes) in place of an instruction, or single data
  bytes. List every site with its original bytes, and make the builder refuse a snapshot whose
  bytes differ.
- **Your code and data live outside the game's memory**: the alt ROM (hooks), free Next RAM
  banks (state, sprite patterns, Layer 2, tables). A start-up tail, if the converter needs one,
  only in memory proven unused (scan a recording: written before read, or never touched).
- **Things derived from the game** (sprites made from its frames, scenery copies, redrawn cells)
  are computed from the snapshot by your build; in the patch they become own bytes and are
  encrypted like the rest. Store a human's redrawing as such, never ship the game's own graphics
  in a readable form next to the page.
- **Snapshot already showing a screen** (title, menu): if you change what is drawn there, patch the
  snapshot's screen memory too - it is shown before any of your code runs.
- Count what you changed: the `make` report gives the bytes copied from the snapshot, fills and
  own bytes. A mod whose game banks are not almost all "copied" changed the game's memory more than
  it needed to - find out why before you publish.

## 2. Make the page
```
python nexpatch/nexpatch.py make "Game (1990)(Publisher).z80" Game_mod.nex -o "out/Game.html" \
    --title "Game" --subtitle "no clash patcher for the ZX Spectrum Next" \
    --about "What the mod does, one paragraph (HTML allowed)." --notice "No game resources ..." \
    --credits "Who made it, the original's copyright"
```
- The `.z80` must be the exact file the users have (the page checks its **CRC32**; ask the human
  which file - known collections have few variants of a game). The CRC32 only recognises the file;
  the encryption key is SHA-256 of the whole file and is never stored.
- `make` checks the round trip itself (Python apply == the `.nex`). Then check the page's own
  JavaScript too: `node test_page.js PAGE.html GAME.z80 GAME.nex` (see `nexpatch/CLAUDE.md`), it
  must say `identical: true` and refuse a changed file.
- The `.nex` name is the `.z80` name without the parts in brackets:
  `Capitan Trueno, El (1990)(Dinamic)(ES).z80` -> `Capitan Trueno, El.nex`.

## 3. Patch format (for tools that read it)
`NXP1`, CRC32 of the `.z80` (u32 LE), its size (u32), the `.nex` size (u32), SHA-256 of the `.nex`
(32 bytes), then ops until the end: `varint((length - 1) * 4 + type)`;
type 0 = own bytes (length bytes follow, XOR ChaCha20 keystream: RFC 8439 block function, key =
SHA-256 of the `.z80`, nonce 0, counter from 0, one continuous stream over all own bytes),
type 1 = copy (varint offset into the source follows), type 2 = fill (one byte follows).
Source = the `.z80` file's bytes, then its memory banks in bank order (48K: 0, 2, 5; 128K: 0-7).
The page and `apply` both check the result against the stored SHA-256.
