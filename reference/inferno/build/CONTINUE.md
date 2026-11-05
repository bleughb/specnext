# Continue Inferno stage 2 from GitHub

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

Read `nexclash/CLAUDE.md`, starting from the Next session block in `games/inferno.md`.
Read this folder's `README.md`, `actor_packing.md`, `frame_pipeline.md` and `timing_architecture.md`.
Preserve original RAM/register behavior and approved B appearance. Full expanded Next memory is
authorized. Stage 2 is incomplete; no sprite NEX is ready.

The actor tile colour decoder is assembled and checked; whole-image enclosed-black fill, runtime
exact-content caching, uploads and complete-frame readiness remain open. Cache/culling census
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
