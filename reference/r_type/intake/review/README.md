# Independent R-Type feasibility review

Scope: original-recording layout measurements and review of the synthetic/actual-copier
publication probes. No engine was implemented or verified by this review.

## Findings

The 221-pattern result rejects the original fixed-grid double-generation cache, not the
approved sprite design. It included end-of-game text that the user explicitly leaves on ULA.
The separate hardware limit of 128 displayed sprites was never exceeded by the fixed grid.

`peak-original.png` shows the supposedly worst scene (original frames 87564/87573).
`credits-owner-88.png` isolates the thank-you text. In the 87480..87780 cut it is rendered by
normal enemy-list object 8, owner 88h, IY=8540h, from caller 917Ah. It resolves frame 32 via
8E85h to source CAFFh, dimensions 21x24 cells, with table C4BAh=D99Ch. Other owners are flying
figures on the same screen and remain sprites. Never filter owner 88h globally: it is reused
by ordinary enemies elsewhere. `classify_credits.py` and `credits-classification.json` retain
the observed call metadata.

The corrected full census tags text from its live graphic identity at plot entry, not by
screen or an unconditional owner ID. It reaches 90,102 frames / 18,576 refreshes without
desync, tags 400 text draws and retains 36,119 text cells on ULA.

| Layout | Maximum displayed sprites | Distinct active patterns | Protected old+new patterns |
|---|---:|---:|---:|
| Fixed screen 16x16 grid | 105 | 103 | 183 |
| One grid per owner, aligned to visible minimum | 111 | 104 | 176 |
| Per-owner best of four grid parities | 108 | 101 | 174 |

`packing-text-classified.json` has the exact peak frames and overflow counts.
Monochrome palette normalization does not fix the decisive corrected peaks. Per-owner grids
are not recommended: one owner can group separate bullets, visible-minimum alignment moves
when clipped, and capacity is worse than the fixed grid. A copier-only text classifier based
on actor type 3Fh and the loaded frame-32 asset may avoid plot hooks, but must first agree with
the measured per-plot graphic classifier across the recording. Other semantic text callers
still need classification; this review confirmed the large end-message exception.

## Publication architecture

Requiring old and new complete pattern generations to coexist is an implementation choice.
A single pattern bank can serve the approved visuals if all replacements occur after the
old play-area pixels have been scanned and before the next scan reaches the new pixels.
Prepare patterns and the clean ULA image in ordinary Next RAM, outside that publication window.

The original native ISR makes an IRQ-free publication interval essential. The initial
synthetic ordinary-DMA publication took 5.556 ms and finished only about 0.16 ms before the
next observed IRQ. The observed native IRQ used for the follow-up takes about 20.27 ms:
CPU publication interrupted there missed rows 2..9. A nominal total below the entire 9.84 ms
off-play interval is therefore insufficient if it crosses that IRQ.

The follow-up `publication_shadow.asm/.py` moves the actual copier before publication,
executes a native long IRQ while the shadow is mapped, and uses DMA for sprite attributes.
The parent reports measured publication about 5.10 ms and about 0.63 ms before the next IRQ,
with exact pattern, ULA, tail and restored-source pixel assertions. Reviewing that source
found no fatal flaw in the measured protocol. This is a component result on one captured
IRQ state with synthetic pattern data, not a full integrated engine or pace proof.

## Shadow-state protocol and required checks

- Clone only slot 2 (4000h..5FFFh), leaving slot 3 and its game variables original.
  Make the initial live-to-shadow clone atomic against ISR stores, and demonstrate that
  this bounded DI phase does not cover a native IRQ. The current prototype keeps DI until
  switching to the shadow and enabling interrupts.
- Keep slot 2 shadowed through preparation/wait so IRQ reads/writes consistently see the
  prepared state. Source pixels may be zeroed temporarily because the full ISR footprint
  does not read/write them. Restore actual pixel addresses only.
- The ISR DOES update 157 non-display bytes at 5B64h..5D00h and reads 314 bytes in
  5B64h..5D01h. Publishing only pixels and 640 attributes would silently lose those updates.
  Copy 5B00h..5FFFh back as well, after a safe DI transition before publication.
- The proposed NR150 transition, DMA tail copy, NR160 publication, and EI before the native
  IRQ near NR247 is valid if its entire worst timing is measured. A CPU LDI copy of the
  1280-byte tail alone takes about 0.73 ms and cannot be assumed to fit ten raster lines;
  use the evaluated ordinary-DMA route for this gate.
- After the last publication write, slot 2 must be live bank 5 and the shadow retired before
  IRQs resume. Restore MMU6 and all caller state before returning. If any IRQ is allowed
  during publication, redirecting it only to the shadow is insufficient: already-published
  rows can become stale. That requires a different mirrored/delta protocol.
- Preserve HUD attributes 5A80h..5AFFh. They are not IRQ-written in the supplied full footprint.
  Source pixel storage is nonlinear: 6000h..6FFFh plus the low 128 bytes of each page
  7000h..77FFh. Never restore the whole 6000h..77FFh range: its gaps contain live game state.
- Add informative negative controls omitting the slot-2 tail copy and restoring the whole
  source area. Compare the source gaps against their post-IRQ values, not the pre-IRQ backup.
- A return-time R restoration does not preserve R sampled inside IRQs during preparation.
  Audit those consumers, record the supplied-R proof scope, and perform natural-play checks.

DDMA-to-ordinary-zxnDMA is the required tested fallback/no-blitter route here; a CPU-only
launcher route is not required by DDMA.md's CPU/zxnDMA wording. Establish DMA ownership and
minimum-core/configuration requirements concretely. Reject unsupported configurations rather
than silently dropping figures or claiming a CPU path meets timing when it does not.

## Next exact gate

Integrate actual pattern preparation, text tagging, the original copier, register/R handling
and caller-speed pacing into one real build. On the worst observed states verify both default
and no-blitter routes, no missed IRQ, publication completion and EI (including its delayed
acceptance) before the next native IRQ, exact non-ULA memory including the slot-2 tail/source
gaps, original sprite pixels and preserved ULA text, and original update cadence. No result in
this review establishes that complete gate or hardware behavior.
