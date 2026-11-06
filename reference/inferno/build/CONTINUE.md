# Continue Inferno stage 2 from GitHub

Latest loading experiment: [loading_preparation.md](loading_preparation.md). User approves loading-time
preparation. L6 prepares 118 live images in 6.32 s modeled CPU subtotal / 110875 bytes; all 2272
sampled draws reuse prepared content. Warm capture/scenery/validation still FAILS at 20.957 ms.
Host scan/dispatch/packing only; safe loading hook/UI/runtime cache are not installed.

The former local-only checkpoint is published on `codex/inferno` in both repositories:

- https://github.com/bleughb/nexclash/tree/codex/inferno — implementation, commit `5a137ee`
- https://github.com/bleughb/specnext/tree/codex/inferno/reference/inferno — original inputs and evidence;
  actor-packing checkpoint `556fc95`, followed by this handoff commit.

Access to the originating ChatGPT conversation or its private workspace is not required.
Use existing checkouts when available: inspect status, fetch, and integrate the published branch
without discarding local changes. If the new environment has no checkouts, obtain these published
branches there. Do not replace an existing checkout or recreate the original workspace unnecessarily.

## Restore scratch evidence if needed

`continuation_work.tar.gz` preserves the original untracked `nexclash/work/` evidence and scratch
files. The canonical results remain the individually committed JSON/Markdown files in this folder.
Extract the archive only when the destination `nexclash/work/` does not exist; otherwise extract to
a separate temporary directory and compare before copying. From an existing nexclash checkout:

```bash
# Only if work/ is absent:
tar -xzf ../specnext/reference/inferno/build/continuation_work.tar.gz
```

Scratch logs include historical runs and failed intermediate attempts; they do not supersede
`actor_packing.md`, the evidence record, or the final structured check results.

## Resume instructions

Latest transfer work: [actor_high_dma.md](actor_high_dma.md): physical DDMA into high staging
pages 216–223; CPU/ordinary DMA fallback retained. These pages are no longer general cache.
Standalone synthetic checks, not installed transfers or hardware timing.

Latest source implementation/evidence: [actor_jobs.md](actor_jobs.md), on these same branches.
The immutable source worker is page 78 / pinned stream page 122; page 75 accepts copied raw tiles.
Read actor-job unit/replay evidence before the historical B checkpoint below. All six quick
correctness replays PASS: 128 captures / 13,066 exact validations. Snapshot-inclusive cold totals
FAIL: L1 899.447 ms / L6 84.289 ms, target 10 ms TOTAL; lookup/allocation/uploads/queue/wrappers
excluded. Per-update source work alone reaches 24.650 ms. Do not install the synchronous walker
as a long DI hook. Next: reduce exact-validation cost, prove source-lifetime deduplication if used,
then assembled stream dispatch, runtime cache/allocator and safe early hook/scheduling. No sprite
NEX. Preserve current/pending ownership, caller-speed/R and ORIGINAL-pace obligations. DMA/DDMA
span probes retain gated larger copies/uploads and route single spans <64 bytes directly to CPU.
This preserves original geometry/bitmap/attribute bytes; host cache selection is not runtime code.

Historical B implementation/evidence: [actor_b_compiler.md](actor_b_compiler.md).
Published implementation checkpoint: nexclash `4fd320c` (quota-serviced B fill and gated prepared transfers).
It includes remote `6aa2992` / main `3efa10f` and matches the verified local tree at `042c460`
(implementation `92b7fa0`, integration `6043a98`). Publication used the connected GitHub API because
command-line Git authentication became unavailable. The branch was advanced with a checked
expected head, preserving concurrent work. Existing local checkouts may have equivalent trees
under those local commit IDs: preserve work, then fetch/integrate rather than reset or re-clone.
The older commit IDs above identify the originating colour-only checkpoint. Whole-image B filling
is now an assembled, resumable private worker; prepared rectangle and protected 256-byte pair
uploads reuse the new shared blitter functions from nexclash PR #93. No new NEX is installed.
Read the latest evidence before the historical colour-only status below. Next: pinned exact live
job snapshots, runtime content cache and safe prewarming/scheduling, then actor pattern layout,
allocator and complete-frame integration. Current/pending pair protection is tested in the transfer
component; integrated ownership remains open. Default prefer-blitter policy must retain no-blitter
and CPU fallback; DMA setup time excludes unknown physical transfer stalls.

All six latest quick correctness runs and targeted shop units pass. Cold total work including
fill still FAILS the 10 ms target: L1 882.15 ms / L6 77.56 ms, excluding runtime cache/uploads/queue.
Sampled four-unit fill calls cost <=0.204 ms, excluding an external wrapper. A live-table host census
finds every sampled first-use key >=85 recorded frames early; that is not a proved runtime schedule,
asset catalogue or safe hook. Never read changing original sources across yields under a stale key.

Read `nexclash/CLAUDE.md`, starting from the Next session block in `games/inferno.md`.
Read this folder's `README.md`, `actor_packing.md`, `frame_pipeline.md` and `timing_architecture.md`.
Preserve original RAM/register behavior and approved B appearance. Full expanded Next memory is
authorized. Stage 2 is incomplete; no sprite NEX is ready.

Historical colour-only checkpoint: the actor tile decoder is assembled and checked; whole-image
enclosed-black fill, runtime exact-content caching, uploads and complete-frame readiness were open. Cache/culling census
results are host models, not installed optimizations. Cold capture/scenery/packing costs 11.88 ms
in level 6 and 46.48 ms in level 1, before fill, cache lookup or uploads. The target is 10 ms TOTAL
added work per game update. Solve first-use construction through safe early preparation from live
original data and/or further engine changes. Never use replay assets as a complete catalogue,
pointer-only cache validity, or partially constructed display frames.

Iterate with `Inferno6.rzx --quick 2000`; test each other level against its own original replay at
integration milestones, plus targeted level-4 shop checks. Actual FLASH synchronization, other modal
paths, continuous original BASIC/Nb/game/ending, recolouring and whole-frame timing remain open.
Use the bundled assembler. Continue implementation and testing autonomously, updating evidence,
records and continuation notes. Explain costs in milliseconds against the total budget.
