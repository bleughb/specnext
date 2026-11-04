# Inferno stage-1 design proposal (2026-11-05)

All design decisions approved 2026-11-05: option B (solid enclosed black interiors), no added
outlines, all figures/effects/projectiles/pickups, original colours and depth, clean gameplay
scenery with original ULA retained, original modal/intro/ending screens, and continuous automatic
level loads preserving score, health and equipment. No sprite engine or continuous loader is implemented.

- `design_comparison.png`: original / A see-through coloured ink / B enclosed black interiors
  for each of six levels. Both proposals use original tile colours and no added outline.
- `levelN_original.png`, `levelN_ink.png`, `levelN_solid.png`: individual 256x192 images.
- `model_checks.json`: 25 complete original game ticks, zero tile-index and visible-pixel
  mismatches. These are sampled reconstruction checks, not hook or full-recording verification.
- `sceneN.json.gz`: gzip-compressed, bounded pre-instruction register/memory captures for level N.
  Memory key `16384` is the mapped address space 4000-FFFF. Registers follow SkoolKit simutils:
  IXh/l=8/9, IYh/l=10/11, SP=12, PC=24, IFF=26, IM=27. Order is execution order.
- `actor_cost4.txt`: original player-list timing, first 2,001 level-4 frames; not total actor cost.
- `graphics_scan4.txt`: sampled graphics/code region access; no free scratch region proved.
- `tape.txt`: standard TZX headers and lengths. Total raw block data: 190,814 bytes, 24 packed pages.
- `manifest.json`: checksums and sizes of the evidence/images (excluding this README).

Capture command, from nexclash (substitute N=1..6; zero-based capture frame numbers):

```bash
python tools/probes/rzx_census.py ../specnext/reference/inferno/InfernoN.rzx \
  --pc 0x9599,0x969F,0x8F7C,0x8F92,0x8F95 --stop 10030 \
  --sample-frames 10000,10001,10002,10003,10004,10005,10006,10007,10008,10009,10010,10011,10012,10013,10014,10015,10016,10017,10018,10019,10020 \
  --sample-limit 64 --memory 0x4000:0xC000 --json
```

Reconstruction: start a complete tick at 8F7C (all scenery, before actors); collect 9599/969F
actor images until 8F92 (pre-copy map), then compare the next 8F95 post-copy ULA. Drop incomplete
boundary ticks. Decode each actor as documented in nexclash/games/inferno.md: C100 pointer,
header tile-page bits, width/dx/dy/tile runs, 0 terminator, live IX and IYl. Apply clipped tiles
in execution order over the 9B00 scenery map; compare low bytes and high&3 with 8F92.
Render tile DC00+8*index with attribute FC00+index into screen (8*x,48+8*y), and compare
all 36,864 viewport RGB pixels with 8F95. HUD is excluded from the model comparison.
Black attributes hide stale bitmap bytes, so a raw bitmap equality assertion is inappropriate.

Preview A overlays each object's nonblack tile pixels on the clean scenery, in original draw
order. B additionally flood-fills enclosed black regions of each whole object's image;
exterior remains transparent. These are explicit proposed changes to rectangular tile knockouts.
The selected complete tick in each level has the greatest image-call count in this short window.
Original HUD pixels are copied from post-copy ULA; no painted colours or speculative outlines.
The disposable preview calculation was dropped; the capture tool, derivation and evidence remain.

The plain hardware baseline is [`../Inferno.nex`](../Inferno.nex), MD5
`0a3bde4734c5b3f15ad0f2a55cc81e19` (level 1 only; no subsequent tape loads).
For original intro, shop and ending appearance see [`../recording_overview.png`](../recording_overview.png).
The proposed continuous game preserves those screens and disables both new layers there;
exact transition sites, loader state continuity, interrupt safety, resource maxima, timing and
hardware appearance remain build/proof gates. No proposed image is a hardware screenshot.
