# Rebuilding El Capitan Trueno (contributor's prototype)

Checked 2026-10-14: every build below reproduces byte for byte (MD5s in ../../README.md).

The archive also held `trueno/tk/nexclash-0.1.4/` (= nexclash tag v0.1.4 + toolkit_changes.diff,
plus a copy of the .z80 and an `auto` run) and `trueno/lib/` (SkoolKit 10.1). Both are left out:
recreate them instead.

    mkdir -p trueno && cp -r build gfx NOTES.md ../trueno1.rzx "../Capitan Trueno, El (1990)(Dinamic)(ES).z80" trueno/
    mkdir -p trueno/tk && git -C ../../../../nexclash worktree add --detach "$PWD/trueno/tk/nexclash-0.1.4" main
    pip install skoolkit==10.1 pillow --break-system-packages
    cd trueno/build && python build_all.py            # ~5 min here; -> ../Trueno_sprites.nex, boot sim OK
    python make_nex.py --en | --immortal | --en --immortal

Both the v0.1.4 tag (+ the diff) and nexclash main (contrib-el-capitan-trueno) give the same
Trueno_sprites.nex. The builder takes only `tools/sjasmplus` and `asm/trueno_hooks.asm` from
the toolkit tree plus nexclash's Python modules.

Plain build: `python nexclash.py convert "<z80>" --tail 0xA6C9` -> ca49e0f4 (boot sim OK with the
79-byte tail at 0xA6C9).
