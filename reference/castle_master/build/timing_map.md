# Castle Master on the Next: timing map and speed experiments (2026-11-21)

All figures come from the simulator running the build over 524 recorded screen updates (every 10th of the
5,233 in the recording), with in-between views on. "T" is a CPU T-state at 28 MHz; one 50 Hz frame is 559,104 T.
An "update" is one of the game's own screen updates; the build fills the time the original spent drawing with
in-between views, then shows the final view at the original's time.

## 1. Where one update goes (hardware-confirmed build, m3b)

One update averages 17.0 frames and shows 6.67 views (5.67 in-between + the final one).

| Share | What | Can it shrink? |
|------:|------|----------------|
| 27.4 % | Geometry: object list, transform, clipping, projection, sorting (about 40 routines, none above 2 %) | Only in small pieces |
| 17.6 % | The game's own code inside the update (its logic, its own redraw, its sound at 3.5 MHz) | No: it is the original, kept for exactness and pace |
| 13.0 % | Polygon row set-up (`span`): about 340 rows a view, 530 T each before any pixel is written | A little (done: 495 T) |
| 12.3 % | Polygon pixel fill (PUSH fill, 5.5 T a pixel, about 80 pixels a row) | No: already the fastest dithered fill |
|  7.9 % | Face walking, slopes, colour set-up, view clear | Little |
|  7.1 % | Waiting: for the raster to leave the view before each flip (4.2 %), clock reads, idle before the final view | Yes (done: flip wait removed for in-between views) |
|  6.6 % | Multiply and divide (32-bit divide alone 4.2 %) | Yes (done: divide now 2.3 %) |
|  4.7 % | Overlay sprites (sight, pointer, messages). Inflated here: the test plants random overlays | Little |
|  3.4 % | Copying the last view into the new bank (indoor views that are not cleared) | Yes (done: 1.2 % by DMA) |

Per view the renderer costs about 1.2 million T (2.1 frames) on average: 390,000 T geometry, 470,000 T raster,
the rest shared overheads. There is no single hot spot; the largest single routine is 13 %.

## 2. What was changed, and what each change gave

Views per update over the same 524 updates (more views in the same time = smoother motion; the game's own
pace is unchanged):

| Build | Contents | Views per update | Gain |
|-------|----------|-----------------:|-----:|
| `castle_master_m3b.nex` | hardware-confirmed build | 6.67 | - |
| `castle_master_m3d_01.nex` | + pointer colour fix only (no speed change) | 6.67 | - |
| `castle_master_m3d_02.nex` | + faster 32-bit divide, faster projection divide, leaner row set-up, view copy by classic zxnDMA | 6.99 | +4.7 % |
| `castle_master_m3d_03.nex` | + the flip no longer idles: the next view's geometry starts at once and the flip happens from inside it when the raster has left the view | 7.46 | +11.8 % |

Details of the five changes:

1. **32-bit divide** (clipping): was a 32-step loop using IX. Now 8 bits at a time with the divisor negated
   (ADD sets the carry, no compare), top bytes that are zero skipped. 1,967 T to about 970 T a call.
2. **Projection divide**: same negated-divisor step. 698 T to 637 T a call (many calls leave early anyway).
3. **Row set-up**: the PUSH fill now starts from the row's end whatever its parity, so the "odd end by hand"
   case is gone. 530 T to 495 T a row.
4. **View copy by classic zxnDMA** in chunks of 8 rows; a chunk that could cover the frame interrupt goes by
   LDIR instead (the CPU cannot see the interrupt while the DMA holds the bus). 458,000 T to about 114,000 T.
5. **Deferred flip**: the old code idled on average about 21 video lines before every flip. Now only the final
   view waits (so the pace is untouched); in-between views flip from a check inside the geometry loop.

Pace against the original is slightly better than before (median +0.69 frame an update against +0.76; worst
+1.95 against +2.55).

## 3. The zxnDDMA blitter: measured in CSpect 4.5.9

`blitbench_02.nex` times each technique on a 192 x 64 block (Layer 2 row pitch 256) at 28 MHz and prints, per
test, the video lines taken (64 us each) and a checksum of the destination. It can be run on the real Next to
compare; the CSpect values are:

| Test | Technique | Lines | us a byte |
|-----:|-----------|------:|----------:|
| 00 | LDIR, row by row | 146 | 0.76 |
| 01 | classic DMA, 3-cycle (copies the 64 unused bytes of each row too) | 54 | 0.21 |
| 02 | classic DMA, 2-cycle | 45 | 0.18 |
| 03 | blitter 2D copy, physical addresses, 3-cycle | 41 | 0.21 |
| 04 | blitter 2D copy, 2-cycle | 34 | 0.18 |
| 05 | CPU PUSH fill (the build's fill) | 38 | 0.20 |
| 06 | blitter 2D constant fill, 3-cycle | 21 | 0.11 |
| 07 | blitter 2D constant fill, 2-cycle | 14 | 0.07 |
| 08 | dither rows by blitter copy from a pattern row (4 jobs) | 36 | 0.19 |
| 09 | whole view shifted sideways by blitter (184 x 64) | 33 | 0.18 |
| 11 | one DMA job per row (64 jobs) | 60 | about 26 us set-up a job |
| 12 | 64 short fills re-arming one program (5 bytes each) | 11 | about 11 us a span |

What that means for this game:

- **Constant fill is 2.7 times faster than the CPU**, but every surface here is dithered (two colours in a
  4-pixel pattern), and a constant fill cannot write a pattern. Filling from a pattern row is a copy, and a
  blitter copy is no faster than the PUSH fill.
- **Per-row jobs do not pay**: starting a job costs about as much as the CPU needs to fill 55-130 pixels,
  and the average row is 80 pixels.
- **View copy**: the blitter's 2D mode skips the unused bytes between rows, so it would beat the classic DMA
  copy by about a third. That is worth about 0.5 % of an update on top of what m3d_02 already has. Not built:
  it needs core 3.03+, and JNext 1.3.0 does not emulate the blitter at all (CSpect does).
- **Shifted in-between views for turns** (copy the last view sideways instead of drawing): 3.7 ms a view
  against about 40 ms, so turning could reach 50 views a second outdoors. But a turn is not a pure shift in
  perspective: over a 10-degree turn step the centre moves 17 pixels but the edges 29, and edge heights change by
  16 %, so edges would be up to about 12 pixels out sideways and 9 vertically, snapping into place at the final view. Not built; it
  changes what you see, so it is your call.

So for this renderer the blitter is not the lever. The gains came from the CPU side and from not idling.

## 4. What is left, in order of value

| Idea | Expected | Cost / risk |
|------|---------:|-------------|
| Blitter 2D view copy on core 3.03+ (classic DMA kept as fallback) | +0.5 % | small; cannot be checked in JNext |
| Outcode routine with pointer loads instead of IX | +0.5 % | small |
| Overlay scan with POP compares | +0.5 % | small |
| Use the idle time before the final view (about 3 %) for one more in-between view when one nearly fits | up to +3 % | scheduling change; pace must be re-proved |
| Shifted turns by blitter | large while turning outdoors | visible geometric error; needs your decision |

Beyond these the remaining time is the game's own code, the dithered fill and many small geometry routines;
a further large step would need a different renderer design, not tuning.

## 5. Checks behind these numbers

- Every view of the 524 sampled updates is compared per pixel with the model of the original; cursor, HDMI
  interrupt line, no-interrupt and old-core (no DMA) samples pass; the sequence test over the whole recording
  passes (5,357 views).
- New simulator checks added for the deferred flip: no flip while the raster is inside the view, never draw
  into the bank on screen, every in-between view drawn is also shown. Eight deliberately broken variants (four for the flip, four for the new divide, projection, row fill and DMA gate) are each rejected.
- The all-updates run for m3d_03 passes: 5,233 of 5,233 updates equal per pixel; pace median +0.68 frame,
  -0.11 to +2.41 (the same worst case as m3b).
- Not yet run on hardware: m3d_01, m3d_02, m3d_03, `blitbench_02.nex`. `castle_master_m3b.nex` is untouched.
