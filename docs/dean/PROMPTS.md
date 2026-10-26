# Dean's prompts - FOR DEAN, not agent instructions

Start sessions with both repos selected: bleughb/nexclash (public toolkit) and bleughb/specnext
(private reference files). Attach new game files in the first message; one game per chat.

## New game (maintainer session)
> New game: <GAME>. Snapshot and RZX attached. Repos: bleughb/nexclash + bleughb/specnext -
> follow nexclash/CLAUDE.md.

## Continue a game (a NEW chat for each stage; nexclash PLAYBOOK "Sessions")
> Continue <GAME> in nexclash. Repos: bleughb/nexclash + bleughb/specnext - follow
> nexclash/CLAUDE.md, start from the "Next session" block in games/<game>.md.

Design question (end of stage 1): reply "defaults", or the numbers to change. Painting the colour
sheet comes with the first sprite build (stage 3), together with the hardware test.
Model: Opus on medium for stages 1-3; recolour and close-out sessions can run on low effort.

## A contribution arrived (upload link)
> Repo: bleughb/nexclash. Review the attached nexclash_contribution_<GAME>.zip
> (tools/merge_contribution.py), check it against CLAUDE.md's rules, run selftest if shared code
> changed, open a PR.

## Hardware problem / result
> Repos: nexclash + specnext. <GAME>_sprites.nex on the Next: <symptom or checklist results>.
> RZX attached if faulty (autosave off). Fix or record it.

## Release
> Repo: bleughb/nexclash. Make release <VERSION>: `selftest.py --stamp` must pass, bump VERSION,
> merge; I publish the release with tag v<VERSION> in the GitHub UI (the release workflow builds
> and attaches the zip).

## Hygiene
- Merge agent PRs on GitHub, then `git pull` both repos.
- Recordings: Fuse, autosave OFF ("Record from snapshot"), keyboard controls.

## Technique-card pilot (2026-10-26; nexclash PR #75, specnext PR #52 merged first)
Same model and effort for every pilot run (Opus, medium). After each session note its token use
from the app's usage view in the game's Pilot log (the agent cannot see its own tokens).

Cauldron, new workflow (stages 0 + 1, one session):
> Add Cauldron to nexclash - technique-card pilot. Clone bleughb/nexclash and bleughb/specnext
> side by side and follow nexclash/CLAUDE.md. Inputs: specnext/reference/cauldron/
> (Cauldron_1985_Palace_Software_a.z80, cauldron.rzx). Do stage 0 (survey) and stage 1 (design)
> with the patch-plan workflow (PLAYBOOK 2, docs/techniques/STANDARD.md): docs/techniques/index.json
> first, at most 3 cards, then only the functions a card names; never another game's whole engine
> module without a reason in the Stage log. Per figure routine: observations with basis
> (observed / inferred / unknown) and scope, eligible cards (every requires true, every rejects
> false), unknowns -> the card's probe, rejected cards with reasons; if no card fits, say so.
> End with the stage-1 design question. Keep a "## Pilot log" in games/cauldron.md: tool calls
> (roughly), files read more than once (name x count), cards opened, card choices later corrected,
> wall time to the design question, user rounds.
