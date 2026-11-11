# Source identity and combined-writer budget — 2026-11-11

Follow-up to [completion-review.md](completion-review.md). No new intake,
capacity, caller or ISR census. No renderer variant or engine promotion.
Sources restored at nexclash6b85acb/specnext6eeaa01; nexclash refreshed from
main f92662e (three unrelated additive engines; no R-Type changes).
SkoolKit10.1/Pillow13.0.0 restored at /workspace/work/venv101. Private SD/JNext
installation and old scratch captures were not transferred. No emulator run.

## Source lifetime and invalidation contract

**Observed, retained corpus + source-only reconstruction:** the original unpacker
reconstructs all1288 retained plots as complete packed streams, including original
attributes and0x36 transparent markers. They reduce to939 unique
(level,address,width,height) keys with no conflicting packed bytes in the recording,
and352 distinct packed images. All12031 packed source addresses are disjoint from
the retained full ISR write set. Host exact-match selection rejects65030 single-bit
mutations (one per byte per keyed stream). This is recorded uniqueness, not a proof
of level-long immutability. See `identity-budget.json`.

**Source-reviewed:** native8F31 low-IX calls set the requested filename digit;
high-IX calls DI at8F40, page bank1, and enter its C000 decoder. Its C040 output
path calls8F29 to store into the normal bank0 view and increments the destination.
C0DD resets persistent bitstream/RLE state only for level'1'; subsequent calls use
saved C03E/C0AE/C0B0/C0FF/C109 state. Repeated level labels alone cannot select a
fresh independent decoder image. The existing decoder correctly retains banks
between calls. Return8F4E restores7FFD=10 before EI/RET. No loader hook is implemented.

**Decision:** reject an unchecked level-installed ID table. No retained evidence
proves every foreground writer leaves source bytes immutable until the next load.
Do not launch another global writer scan to justify that assumption. A preinstalled
level table may identify a candidate; it must not authorize its pixels by itself.

The bounded alternative is an invocation-local certificate:

1. Dispatch on the actual physical source mapping, level, source pointer and
   dimensions. Unknown key/mapping, DI entry or invalid bounds selects native
   fallback. Candidate packed length comes from reconstructed geometry, never
   by walking an unvalidated mutated stream. Bounds must include the entire stream.
2. Compare the complete candidate stream at plot entry, including attributes and
   skip markers. A mismatch selects native fallback for this invocation and clears
   any candidate ID. Never accept a hash alone or reuse last invocation's hit.
3. Certificate lifetime ends at this plot's return. Eligible calls must have
   disjoint source, stack and output locations; the bounded native calls do. The
   dispatcher must enforce that precondition. The four plot bodies and
   their8EA2/8EC2 helpers write output pixels/attributes/owners/collision bookkeeping,
   not the validated packed stream. The retained ISR set also excludes this stream.
   An extended writer/callback/IRQ path needs its own proof or must invalidate it.
4. Associate IDs only with actual successful native writes. Unknown/mutated art
   writes an explicit invalid ID and renders from the native output buffer. Native
   collision acceptance, Force attribute override, flips and original RAM effects
   remain authoritative. A post-plot source change cannot retroactively recolour
   a cell already drawn from the old source.
5. Loader entry, incompatible mapping, untracked native/DI writer, owner reuse,
   clear, menu/pause and generation rollover must invalidate the appropriate
   metadata before it can be consumed. Matching owner/ink/level is insufficient to
   certify freshness. Renderer must check generation as well as current ownership;
   invalid metadata falls back to the actual native bitmap. This integration is
   **not implemented or proven** by the guard component.

`plot_guard.asm` implements only the byte comparison in step2. It preserves
BC/DE/HL and returns carry for exact match; AF/R change. Dispatch, clock/NextReg,
native-R repair, generation and hardware output remain the wrapper's obligations.
Its harness places the test stack in writable RAM, not the simulator's ROM view.

## Bounded cost result

`identity_budget.py` reuses the retained corpus and native decoder. A private RZX
cut starts at original frame29404; the measurement covers100 complete8649 updates
after that cut (2511 plots,12802 nonblank cells,9512 successful writes). Every plot
matches a known packed candidate. This is the recorded trajectory, **not** the
natural JNext sample underlying `resolved-pace.json`; different trajectories and
raster/IRQ phase may change the result. No natural-pace bound is claimed.

| Quantity | CPU estimate per update |
|---|---:|
| Minimum observed cached-ID deficit to reach2% |9.214756ms|
| Remove complete current resolver-associated cost, free replacement |5.445620ms|
| Plot-only identity, estimated49T/byte +600T/plot +80T/successful ID |2.565877ms net saving|
| Additional native plot work outside already accelerated cell spans |11.467513ms potential saving at28MHz|
| Combined direction after measured packed guard cost |13.506037ms potential net saving|
| Remaining allowance for additional integration/accounting |4.291281ms (~120156fast T/update)|

The first ceiling uses the retained complete-cell difference657-(-946)=1603
fast T, including larger metadata and signed accounting, rather than an isolated
resolver timer. It is deliberately optimistic; plot-only identity does not justify
implementation as the next standalone route. Real guard timing is59T/byte+100T
per hit, excluding CALL17T. The combined row includes both, retains the estimated
600T/plot setup and80T/successful selection, and assumes3.5->28MHz for remaining
original plot work. These are proposed costs, **not runtime credit constants**.

Native instruction totals:7823864T, of which3236859T is already inside accelerated
cell spans;4587005T remains outside. The counting uses live branch conditions and
SkoolKit timings, excluding native IRQ instructions.16 isolated executions (four
real entry states x four R seeds) independently match CPU totals and native M1/R
increments. This validates the counter model, not an assembled accounting wrapper.

## Combined writer: consumer constraints and next bounded gate

Retained buffer read/write evidence is not permission to discard the original
outputs:8EC2 reads owner/collision state and8EA2 writes owner/attribute state;8842
consumes native source pixels. The retained6000..77FF scan also includes live
holes: e.g.94FB/9A2C read74FA input state;8B70 reads keyboard tables in that range.
Those readers are not evidence that all figure pixels have gameplay consumers,
but they prohibit treating the entire range as disposable. Keep all native pixel,
attribute, owner and collision RAM effects in the proposed combined writer.

The measured opportunity is the **remaining original plot work**, not another
hardware backend. A future bounded integration can run original plot traversal,
clipping and collision paths at28MHz, fuse successful native/HW metadata writes,
and resolve candidate identity once per plot. Exact time credit must come from
original executed paths minus **all** added CPU, including its own accounting,
classification, guard, descriptor, wrapper and exit work. Do not revive the old
K104/raster-window credit or count accelerated wrapper CPU as original work.
Preserve R and the existing native IRQ supplied-R protocol; IRQ CPU is not a credit.

Pass/fail for that experiment: measured complete added costs fit the remaining
allowance on the bounded sample, all native RAM/register/R outputs and fallback
negatives match, then a complete LIVE painted JNext100-update peak at<=2%, state
equality each update and50Hz IRQs. Report FE event/sound differences separately.
If exact accounting consumes the allowance, stop this experiment; no further
renderer variants by default. No claim that the CPU estimate guarantees2%.

## Assembled guard result and reproduction

`plot_guard_check.py`, pinned sjasmplus1.24.0:352 matching packed images accepted,
1056 changed first/middle/last bytes rejected, zero length rejected,300-byte loop
tested with R seeds0/127/128/255, BC/DE/HL/SP and non-stack RAM exact. Actual CP(HL)
mutated to CP A falsely accepts changed data and is caught by the oracle. Every
hit matches59*length+100 CPU T. Maximum retained packed length1500 bytes.
This is a component result; no caller AF/R, IRQ or live painting claim.

From nexclash, after restoring the documented Python versions:

```
../venv101/bin/python ../specnext/reference/r_type/intake/identity_budget.py
../venv101/bin/python ../specnext/reference/r_type/intake/plot_guard_check.py
```

The first command reconstructs decoder scratch if absent and makes only the known
bounded peak cut; generated packed bytes, snapshots, RZX and plot states stay in
/workspace/work/r_type_review. `refresh_capture.py` also recovered the known peak
copier fixture in work; no new coverage claim. Compact results contain counters,
not game pixels. No SD image, JNS metadata or emulator-generated artifacts committed.

Still open: runtime dispatch/invalidation and combined-writer implementation;
complete live painted pace, ABI/R/IRQ/RGB, stale source/ownership and pause/menu/DI;
engine/profile/registry/record, sheets/recolour, quick runs and final full verification.
