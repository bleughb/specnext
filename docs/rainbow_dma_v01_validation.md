# Experimental Rainbow Islands sky DMA v0.1

Source: [nexclash PR #95](https://github.com/bleughb/nexclash/pull/95).
These are complete game builds, based on the pinned sky rework. Existing releases are unchanged.
Hardware has not been tested. The source PR and validation report distinguish partial recording
coverage from a complete recording; neither certifies a complete game or real hardware.

GitHub currently marks specnext public. At the owner's request, the [complete NEX bundle and separate NXC patch](../reference/rainbow_z80n/experimental_dma_v01/README.md) are now hosted in this repository. All original snapshots, recordings and pinned NEX files remain unchanged.

| Delivered file | MD5 | SHA-256 |
|---|---|---|
| rainbow_sky_dma_v01_blitter.nex | b7c96a5ec9d6bbf764ba4c24dd986158 | 9e041148906e23c5443dd4abfd7c8e71c5654c88ed7a7f896997ad97c6b0af23 |
| rainbow_sky_dma_v01_no_blitter.nex | ed439dadd141fb385b2de71e81fbcf66 | ae534b561e3942cef52e939f0632ef109998db8f2a70ad6d7d7c44484c7130bb |
| rainbow_sky_dma_v01_cpu_only.nex | a92c2c1ee8583c982d40be1914be3791 | d59f014d0c52b70f4e5a05813d8c24e5ded1bad307406e1730892bf0e3a18e6b |
| rainbow_sky_dma_v01_blitter_diag.nex | 658a2647c74956a5d8652d4555b9050b | a849bcf85c031fc0dfb5fd8dd532267d56f7ec9624aa8cc6464b3ece2f0acdc0 |

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

## Software results

Software results: complete rainbow.rzx, 7,178 observed replay frames, 2,212 commits; rainbownew.rzx sampled at 2,000 requested frames (2,008 observed), 489 commits; no-blitter, CPU-only, old-core and hardware-IM2 routes sampled at 200 requested frames each on an active island-1 boss segment. Twelve LeeBee gameplay cuts sampled (five boss cuts at 200 and seven round-start cuts at 1,200 requested frames), plus a 200-frame ending sample with no commit hook reached. All reported comparisons pass. The full recording still has 60 modeled frames over 20 ms, max 25.666 ms before wait states; recovery comparisons pass. The latter ending sample is not DMA gameplay proof. The legacy game unit suite uses six captured dispatch states from a 1,200-frame capture, plus its object/AY/raster cases and negative controls. Hardware is untested.
