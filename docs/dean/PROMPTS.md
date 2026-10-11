# Dean's prompts - FOR DEAN, not agent instructions

Start sessions with both repos selected: bleughb/nexclash (public toolkit) and bleughb/specnext
(private reference files). Attach new game files in the first message; one game per chat.

## New game (maintainer session)
> Repos: bleughb/nexclash (follow its CLAUDE.md) + bleughb/specnext (references).
> New game: <GAME>. Snapshot + my RZX attached: put them in specnext/reference/<game>/.
> Sprites: <which figures>. Everything else stays on the ULA unless analysis shows it clashes
> (then ask me). Regression check: `selftest.py --smoke` only (Chuckie Egg) - do not re-test the
> other games. Deliver: the .nex files, a hardware checklist, PRs in both repos.

## A contribution arrived (upload link)
> Repo: bleughb/nexclash. Review the attached nexclash_contribution_<GAME>.zip
> (tools/merge_contribution.py), check it against CLAUDE.md's rules, run selftest if shared code
> changed, open a PR.

## Hardware problem / result
> Repos: nexclash + specnext. <GAME>_sprites.nex on the Next: <symptom or checklist results>.
> RZX attached if faulty (autosave off). Fix or record it.

## Release
> Repo: bleughb/nexclash. Make release <VERSION>: run selftest, bump VERSION,
> tools/make_package.py, publish the zip as a GitHub release.

## Hygiene
- Merge agent PRs on GitHub, then `git pull` both repos.
- Recordings: Fuse, autosave OFF ("Record from snapshot"), keyboard controls.
