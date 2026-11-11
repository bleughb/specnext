# Book-ingest comparison — 2026-11-11

User supplied a5682-byte secondary dossier for Bob Pape's *It's Behind You* (2013).
Input SHA256: f98fb6c90b149858ad35436d94ffc58ec532a4b4c663030248534cd28279311b.
Neither the PDF nor its mirror was downloaded. Page references below come from
the ingest; original page context/mirror identity is not independently verified.
The owner explicitly said not to download the book again; use the supplied ingest.

Its research-only Next session/checklist is document content, not active project
instructions. Missing-input/recording claims do not apply here. Existing design,
completed intake and current live-budget handoff remain authoritative.

## Insights against the existing binary

| Ingest claim | Current evidence and implication |
|---|---|
|pp52–54: direct background scrolling with buffered sprites|Matches the copier's use of prior displayed background and separate foreground source. Supports replacing the whole duplicate picture pipeline, using an independent background source. Moving the existing composite screen is insufficient.|
|pp52–54: two640-byte maps for background tiles and sprite occupancy;32x20 cells|Follow-up binary review identifies7E00 owner/collision and8100 dirty state, both IRQ-read. Independent background source is the level stream atC4BC, not either640-byte map; see background-consumer-review.md. The ingest's labels alone were insufficient.|
|pp53–54: empty regions skipped; maps/attributes advance at character boundaries|Consistent with conditional scrolling and8CD8 attribute/owner shifts. Hardware pixel scrolling must preserve logical cell progression, clipping and occupancy.|
|pp103–104: level-specific sprite-table indirection|Current8E85 loads the table pointer fromC4BA and selects a four-byte dimensions/source record. Supports plot/level identity rather than repeated cell inference, but does not establish immutability or eliminate generation/Force-mode invalidation and fallback.|
|p90: sound by Rob Hylands; no in-game music owing to RAM|Compatible with zero gameplay AY writes and the observed FE/beeper workload. Sound effects and native IRQ timing still require preservation; no sound-equivalence proof follows.|

The strongest lead is a logical background representation independent of temporary
sprite occupancy. Identify that map, its graphics/palette and edge updates before
choosing a hardware background. This is a targeted continuation of consumer review,
not a reason to repeat intake/capacity/caller/ISR scans.

The nominal6912-byte back-screen description does not make the whole region
disposable: retained binary evidence puts live variables in unused display holes,
e.g.71D0/74FA. Keep actual address/read/write evidence authoritative.

## Exact code anchor

The supplied SCROLL6 excerpt expands to:

```
bytes.fromhex('cb162d') * 30 + bytes.fromhex('cb162469a7c9')
```

These96 bytes match8914..8973 exactly in both original Rtype.z80
(MD5 5a2179b4006d7888a1f7f821a4316bf5) and the recovered peak
(MD5 9cfed755be2d7ae90a3876ea617f87bf). This anchors that excerpt, not every label,
external symbol or release. Initial carry, selected span/entry and preceding
control flow still matter. SAD/NOSCROLL/FRAME are annotation leads, not established
address mappings from this abbreviated ingest.

DO/LOOP are assembly-time directives, not runtime self-modification. The ingest
adds no new SMC evidence for8EB1/8EDA/8F0B-C; use the scoped live write-watch for
those observations. Level-specific tables do not make a frozen relocated helper
safe or prove level-long source lifetime.

No timing/build result changes. The fresh scroll section costs0.984ms/update,
against9.386ms required savings: optimizing SCROLL6 alone cannot close the gap.
Review the whole pipeline's consumers and native-time credit, including new
background work and changed waits, as required by live-budget-review.md.

Book URL supplied for provenance only:
https://spectrumcomputing.co.uk/zxdb/sinclair/entries/2001502/ItsBehindYou-TheMakingOfAComputerGame.pdf
