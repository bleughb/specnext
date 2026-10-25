# Dean's prompts - FOR DEAN, not agent instructions

Start sessions with both repos selected: bleughb/nexclash (public toolkit) and bleughb/specnext
(private reference files). Attach new game files in the first message; one game per chat.

## New game (maintainer session)
> New game: <GAME>. Snapshot and RZX attached. Repos: bleughb/nexclash + bleughb/specnext -
> follow nexclash/CLAUDE.md.

## Continue a game (a NEW chat for each phase; nexclash PLAYBOOK "Sessions")
> Continue <GAME> in nexclash. Repos: bleughb/nexclash + bleughb/specnext - follow
> nexclash/CLAUDE.md, start from the "Next session" block in games/<game>.md.

Design question (end of phase A): reply "defaults", or the numbers to change.

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
