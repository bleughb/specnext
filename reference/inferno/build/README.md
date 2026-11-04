# Inferno stage-2 loader foundation (2026-11-05)

Stage 2 is INCOMPLETE. No sprite engine or sprite NEX exists. The diagnostic NEX is not a
hardware candidate: full tail lifetime, continuous gameplay and timing remain unproved.
The approved visual design in ../design/ is unchanged.

From nexclash on codex/inferno (SkoolKit 10.1, bundled pinned sjasmplus):

```bash
pip install -r requirements.txt --break-system-packages
python tools/asm2profile.py --check inferno
python -m nexclash.inferno --loader-tests ../specnext/reference/inferno/Inferno.tzx --json work/loader_checks.json
python -m nexclash.inferno --continuation-tests ../specnext/reference/inferno --json work/continuation_checks.json
python -m nexclash.inferno --bootstrap ../specnext/reference/inferno/Inferno.tzx --out work/inferno --json work/bootstrap_checks.json
python nexclash.py scan work/inferno/Inferno_bootstrap.z80 --frames 2000 --range 0x5D30-0x5E6F
```

- loader_checks.json: original-ROM byte decoder versus assembled bank loader. All 32 raw blocks
  in load/verify modes, capacities, flag/parity/verify failure, EOF, address wrap and ROM semantics.
  Two deliberately broken assembled builds detected. Every instruction audited for slot-0/IFF;
  no tape payload writes. Physical pulse acquisition is replaced by canonical completed bytes
  in BOTH machines. This is not a physical-tape comparison or timing measurement.
- continuation_checks.json: seven crafted calls to original 7131 from the supplied level-1
  snapshot, each ending at 718C before CALL 44000. Na is loaded/executed; Nb is loaded but NOT
  executed. No target-level snapshot restore. Four ROM transfers per case, identical registers,
  live RAM and original I/O. R inputs at the original beeper's 7C37 are synchronized and counted;
  13 differing dead-stack bytes are guarded against later reads. No time interrupts are modeled.
  This does NOT prove actual level completion, score/health/equipment retention across gameplay,
  Nb initialization, modal screens, all-level startup, ending or rewind/restart behavior.
- Inferno_bootstrap.z80: original TZX/BASIC run to its first USR 24200, before compressed main runs.
  This is not a synthesized or independently restored level-start state.
- Inferno_loader_diagnostic.nex: that bootstrap plus bank loader, full original alt-ROM images,
  all 32 raw tape blocks unchanged in pages 32-55, cursor state page 68. No display hooks/layers.
- bootstrap_checks.json: NEX boot preserves registers/RAM/ROM with NEXLOAD printer-buffer damage
  and both normal and deliberately foreign system ROM3. Tail 5D30-5D65.
- bootstrap_scan.txt: original initial 2,000-frame scan leaves 5D30-5E59 untouched. This limited
  scan does not establish later tail lifetime. Do not distribute the diagnostic as a release.
- manifest.json: artifact lengths and MD5s, not a verification stamp.

Next: pulse-level loader contract and real continuous startup/Na+Nb/game/ending continuation;
then complete original-memory-preserving sprite/Layer 2 hooks, modal transitions, instruction
interrupt safety, resource bounds, measured timing, colour maps/sheets and quick RZX verification.
Read nexclash/games/inferno.md for the exact current design, evidence and next-session prompt.
