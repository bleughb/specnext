# Experimental Rainbow Islands sky DMA v0.1

Source: [nexclash PR #95](https://github.com/bleughb/nexclash/pull/95).
These are complete game builds, based on the pinned sky rework. Existing releases are unchanged.
Hardware has not been tested. The source PR and validation report distinguish partial recording
coverage from a complete recording; neither certifies a complete game or real hardware.

GitHub currently marks specnext public. New binaries are provided as downloadable deliverables,
not committed here. All original snapshots, recordings and pinned NEX files remain unchanged.

| Delivered file | MD5 | SHA-256 |
|---|---|---|
| rainbow_sky_dma_v01_blitter.nex | 505e27a12077926a9bc55ca645c30644 | fc26cac6f63eefe7792dcfa1500a5db96c6e4dbe22c7a25ee5d72151211c69d7 |
| rainbow_sky_dma_v01_no_blitter.nex | 04d68dedb46de2c937b90ef7ade9e49c | 7b7e1e29d3f4a68425b0804ac9a0562eabe454de366f97e8f4185c6a5ce6fae1 |
| rainbow_sky_dma_v01_cpu_only.nex | 6beabfecf7c882e8535e3290cc015df8 | 9f802db73410bdaeb2e75248021537ce86af008139246c8b8231c797253ac0d2 |
| rainbow_sky_dma_v01_blitter_diag.nex | d6b90405d29face3f58938d69b1ec598 | d04ad176e7b8a9c0fd5637833cc3e17163943811295272626b81c4814f6f4eb9 |

The blitter build prefers general virtual 2D DMA on core 3.03.00+ and uses ordinary DMA on older
supported cores. No-blitter uses ordinary DMA/CPU; CPU-only retains an LDIR tilemap copy. All keep
the same sky rule, default class colours, loading screen, cache, AY queue and three-interrupt pace.
Real game-build commands and hardware checks: [game notes](https://github.com/bleughb/nexclash/blob/codex/rainbow-dma-game/games/rainbow_dma.md).
Exact software results: [benchmark report](https://github.com/bleughb/nexclash/blob/codex/rainbow-dma-game/docs/benchmarks/rainbow_dma_v01.json).
Source and mutable command storage use page 28 upper RAM. Source $4000-$44FF and bank-7 virtual
destination $61E8-$6817 stay mapped through completion. Legacy Spectrum IM2 runs with $C0=0;
unexpected hardware IM2 uses CPU fallback without changing $CC-$CE.

## Hardware handoff
Copy the separate experimental NEX files to an SD card and launch with NextZXOS .nexload.
Compare the same scene with blitter, no-blitter and CPU-only files. Record board, exact core,
file hash and policy. Check loading/menus, sky in all island groups, figures, thrown rainbows,
scrolling, tearing, death/continue, island/boss transitions, ending, steady music, IRQ delivery,
raster budget/overrun recovery, quiet and busy gameplay pace. The diagnostic file shows the
existing border signals. No timing, sound, interrupt or visual hardware success is claimed.
