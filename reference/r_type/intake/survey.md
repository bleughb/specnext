# Survey: Rtype (128K)
Read this first (PLAYBOOK stage 0). Raw numbers: survey.json. Commands to dig further: PLAYBOOK 2-3.

## Snapshot (inspect)
```
Machine   : 128K
7FFD      : 0x10: ROM 1 (48K BASIC), bank 0 at C000, screen normal (5)
PC        : 48676 (0xBE24) - RAM
RAMTOP    : 8388 (0x20C4)
Interrupts: IM 2, DI, I = 0x84
IM 2      : vector at 0x84FF -> 33667 (0x8383) -> 48675 (0xBE23) (table of 257 equal bytes)
              handler: PUSH AF / PUSH BC / PUSH DE / PUSH IX / PUSH IY / PUSH HL
Stack     : SP 65526 (0xFFF6); top words 0090 FDEC 8197 8631
Border    : 0
WARNING   : none
```
## Engine
Unknown: no detector in nexclash/engines.py and no TID / Dizzy 1 signature -> stage 1 (a new engine).

## Recordings
- Rtype.rzx: no autosave snapshots

## Plain conversion
- Rtype.nex: default tail (no recording to check it against) (128K: tail not proven by a recording - prove it with `scan --range`, PLAYBOOK 1); simulated boot: not run: nextboot.check models 48K start-up only (128K engines bring their own boot check, e.g. midres.boot_check). The user tests it on the Next with the stage-1 question.

## Recording and coverage
- 2501 frames analysed.
- GATE: CHECK - 9 CALL site(s) to these routines, in code that ran, were never reached (table below). For a FIGURE plotter that is a path the recording missed: ask the user for a recording that reaches it (docs/RECORDING_CHECKLIST.md) before stage 1. For a text / score printer it usually is a message that did not come up: say so in games/<game>.md.

## Screen writers by routine (innermost CALL running at the write)
| Routine | pixel / attr bytes | calls | callers seen | T per call median / max | called from | coverage |
|---|---|---|---|---|---|---|
| 34882 (0x8842) | 345650 / 242400 (242400 block copy) | 404 | 4 | 162642 / 340798 | 35405 (0x8A4D), 35559 (0x8AE7), 35193 (0x8979) | 4/5 CALL sites reached |
| 30614 (0x7796) | 0 / 164480 (164480 block copy) | 1 | 1 | 33620968 / 33620968 | top | 1/1 CALL sites reached; 1 JP site(s) (not tracked) |
| 48791 (0xBE97) | 31290 / 0 | 13090 | 1 | 598 / 30658 | 48761 (0xBE79), 48791 (0xBE97), 48734 (0xBE5E) | 1/1 CALL sites reached |
| 65007 (0xFDEF) | 18432 / 640 (19068 block copy) | 29 | 3 | 5305 / 251532 | 34499 (0x86C3), 49042 (0xBF92), 65259 (0xFEEB) | 3/9 CALL sites reached; NOT reached (code ran nearby): 37406 (0x921E), 37415 (0x9227), 37424 (0x9230); 1 JP site(s) (not tracked) |
| 49369 (0xC0D9) | 7168 / 0 | 896 | 2 | 204 / 1154 | 49279 (0xC07F), 49281 (0xC081) | 2/2 CALL sites reached |
| 49284 (0xC084) | 6600 / 0 | 170 | 15 | 580 / 51120 | 30614 (0x7796), 50251 (0xC44B), 37428 (0x9234), 64938 (0xFDAA), 39468 (0x9A2C), 64933 (0xFDA5) | 15/19 CALL sites reached; NOT reached (code ran nearby): 35957 (0x8C75) |
| 35193 (0x8979) | 6400 / 0 | 326 | 1 | 181151 / 340932 | top, 40442 (0x9DFA) | 1/1 CALL sites reached |
| 36093 (0x8CFD) | 4704 / 0 | 1944 | 6 | 4556 / 132856 | 39422 (0x99FE), 65259 (0xFEEB), 38263 (0x9577), 38129 (0x94F1), 39468 (0x9A2C), 37129 (0x9109), 50190 (0xC40E) | 6/10 CALL sites reached; NOT reached (code ran nearby): 42304 (0xA540) |
| 65008 (0xFDF0) | 0 / 2504 (2494 block copy) | 16 | 10 | 681 / 138849 | 34499 (0x86C3), 30411 (0x76CB), 34473 (0x86A9), 35405 (0x8A4D), 30614 (0x7796), 50251 (0xC44B) | 10/13 CALL sites reached |
| 30411 (0x76CB) | 0 / 1408 (1408 block copy) | 2 | 2 | 16334 / 16334 | 65027 (0xFE03), 30614 (0x7796) | 2/2 CALL sites reached |
| 36197 (0x8D65) | 256 / 0 | 2 | 1 | 71029 / 72320 | 65259 (0xFEEB) | 0/2 CALL sites reached; NOT reached (code ran nearby): 37251 (0x9183), 39441 (0x9A11) |
| 30336 (0x7680) | 0 / 48 | 1 | 1 | 1091 / 1091 | 34593 (0x8721) | 1/3 CALL sites reached; NOT reached (code ran nearby): 30355 (0x7693), 37071 (0x90CF) |
| 48965 (0xBF45) | 3 / 0 | 12942 | 2 | 85 / 1035 | 48791 (0xBE97), 48761 (0xBE79) | 2/2 CALL sites reached |
| 48761 (0xBE79) | 3 / 0 | 335 | 4 | 13132 / 43828 | 35405 (0x8A4D), 35559 (0x8AE7), 30614 (0x7796) | 4/4 CALL sites reached |
Block copies (LDIR / LDI / PUSH) into the screen = probably a back buffer: `scan --range BUF --writers` on its source (PLAYBOOK 2). A routine in ROM (< 0x4000) is the ROM printing text.

## Preview (preview.png: screen at frames 312,624,936,1248,1560,1872,2184,2496, what each plot routine draws per caller)
```
Source    : ../specnext/reference/r_type/Rtype.rzx, 2502 frames; shots at 312, 624, 936, 1248, 1560, 1872, 2184, 2496
Sheet     : /workspace/work/r_type_initial_fixed/preview.png (1040 x 392)
Group 0   : plot 65007 (0xFDEF) from 34518 (0x86D6): 27 calls, 18432 bytes drawn, x 0-255, y 0-191 (colour (255, 0, 0))
Group 1   : plot 48791 (0xBE97) from 48784 (0xBE90): 13110 calls, 31348 bytes drawn, x 0-255, y 8-153 (colour (0, 255, 0))
Group 2   : plot 34882 (0x8842) from 35432 (0x8A68): 30 calls, 7120 bytes drawn, x 24-247, y 64-103 (colour (0, 128, 255))
Group 3   : plot 34882 (0x8842) from 35479 (0x8A97): 26 calls, 13264 bytes drawn, x 8-239, y 64-103 (colour (255, 0, 255))
Group 4   : plot 34882 (0x8842) from 35585 (0x8B01): 22 calls, 17504 bytes drawn, x 8-247, y 8-151 (colour (255, 160, 0))
Group 5   : plot 65007 (0xFDEF) from 35588 (0x8B04): 22 calls, 0 bytes drawn, x -, y - (colour (0, 255, 255))
Group 6   : plot 49369 (0xC0D9) from 49345 (0xC0C1): 448 calls, 3584 bytes drawn, x 0-255, y 176-183 (colour (255, 255, 0))
Group 7   : plot 49369 (0xC0D9) from 49360 (0xC0D0): 448 calls, 3584 bytes drawn, x 0-255, y 184-191 (colour (160, 80, 255))
Group 8   : plot 30614 (0x7796) from 34365 (0x863D): 1 calls, 0 bytes drawn, x -, y - (colour (255, 128, 128))
Group 9   : plot 49284 (0xC084) from 30640 (0x77B0): 1 calls, 160 bytes drawn, x 80-239, y 24-31 (colour (128, 255, 128))
Group 10  : plot 49284 (0xC084) from 30646 (0x77B6): 1 calls, 168 bytes drawn, x 80-247, y 32-39 (colour (128, 128, 255))
Group 11  : plot 49284 (0xC084) from 30652 (0x77BC): 1 calls, 144 bytes drawn, x 80-223, y 56-63 (colour (200, 200, 0))
```

## Screen writers (scan --writers)
```
Source    : ../specnext/reference/r_type/Rtype.rzx, 2501 frames
Counting  : from the start
Lowest SP : 49654 (0xC1F6) (any SP value: games that use SP as a data pointer show it here)
Range 0x4000-0x5AFF: 0 of 6912 bytes untouched
  touched     0x4000-0x5AFF (6912 bytes, rw), first: write at PC 65008
  write-first 0x4000-0x5AFF (6912 bytes)
  writers   82 instructions: 34903 (0x8857) x242400, 30693 (0x77E5) x164480, 35182 (0x896E) x26090, 35179 (0x896B) x25450, 35176 (0x8968) x24170, 35173 (0x8965) x22890, 35170 (0x8962) x21610, 65013 (0xFDF5) x21562, 35167 (0x895F) x20330, 35164 (0x895C) x19050
  writers+  72 more instructions in 15 routine span(s): 30345-30347 (0x7689) x48, 30450-30450 (0x76F2) x1408, 34956-34984 (0x888C) x88768, 35005-35019 (0x88BD) x27640, 35110-35161 (0x8926) x69652, 35286-35314 (0x89D6) x6400, 36143-36171 (0x8D2F) x4704, 36246-36281 (0x8D96) x256, 48854-48856 (0xBED6) x298, 48897-48899 (0xBF01) x16344, 48933-48933 (0xBF25) x5234, 48960-48962 (0xBF40) x9420, 49333-49333 (0xC0B5) x6600, 49372-49374 (0xC0DC) x7168, 65008-65008 (0xFDF0) x14
  readers   28 instructions: 35182 (0x896E) x26090, 35179 (0x896B) x25450, 35176 (0x8968) x24170, 35173 (0x8965) x22890, 35170 (0x8962) x21610, 65013 (0xFDF5) x21562, 35167 (0x895F) x20330, 35164 (0x895C) x19050, 35161 (0x8959) x10106, 35158 (0x8956) x7498
  readers+  18 more instructions in 3 routine span(s): 30450-30450 (0x76F2) x1408, 35110-35155 (0x8926) x52048, 48959-48959 (0xBF3F) x768
```
## Memory (scan: free memory for hook state, stack low-water)
```
Source    : ../specnext/reference/r_type/Rtype.rzx, 2501 frames
Counting  : from the start
Lowest SP : 49654 (0xC1F6) (any SP value: games that use SP as a data pointer show it here)
Range 0x4000-0xBFFF: 10968 of 32768 bytes untouched
  untouched   0xA655-0xAB70 (1308 bytes)
  untouched   0xB06D-0xB32D (705 bytes)
  untouched   0xB6DB-0xB94D (627 bytes)
  untouched   0xA231-0xA48F (607 bytes)
  untouched   0x961F-0x9829 (523 bytes)
  untouched   0xA04D-0xA215 (457 bytes)
  touched     0x4000-0x5AFF (6912 bytes, rw), first: write at PC 65008
  touched     0x5BD4-0x5C4B (120 bytes, rw), first: read at PC 63773
  touched     0x5CBA-0x5D02 (73 bytes, rw), first: read at PC 63773
  touched     0x5D04-0x5D05 (2 bytes, r), first: read at PC 36245
  touched     0x5D09-0x5D0A (2 bytes, r), first: read at PC 36245
  touched     0x5D0F-0x5D10 (2 bytes, r), first: read at PC 36250
  touched     0x5D14-0x5D15 (2 bytes, r), first: read at PC 36275
  touched     0x5D1C-0x5D1C (1 bytes, r), first: read at PC 36260
  touched     0x5D1F-0x5D1F (1 bytes, r), first: read at PC 36245
  touched     0x5D21-0x5D21 (1 bytes, r), first: read at PC 36280
  touched     0x5D24-0x5D24 (1 bytes, r), first: read at PC 36280
  touched     0x5D29-0x5D2B (3 bytes, r), first: read at PC 36270
  ... 364 more touched spans
  write-first 0x4000-0x5AFF (6912 bytes)
  write-first 0x5E00-0x5FFF (512 bytes)
  write-first 0x6021-0x6035 (21 bytes)
  write-first 0x6041-0x605E (30 bytes)
  write-first 0x6061-0x607E (30 bytes)
```
## Interrupt handler (isr: what hooks must keep intact)
```
Source    : ../specnext/reference/r_type/Rtype.rzx, 2501 frames, 2052 interrupts accepted, 0 never returned before the next
Mode      : IM 2, I = 0x84 (vector 0x84FF) x2052
Entered at: 33667 (0x8383) x2051
Executed  : 471 distinct instructions in the handler(s)
Uses IX   : saved / overwritten before any read of the interrupted value
Uses IY   : saved / overwritten before any read of the interrupted value
Uses R    : LD A,R at 48859; LD A,R at 48950
Uses AF'  : EX AF,AF' at 48683; EX AF,AF' at 48723; EX AF,AF' at 48869 (+2 more)
Stack     : up to 26 bytes below the interrupted SP; switches stack: LD SP,63610 at 64179, LD SP,63610 at 64195, LD SP,63610 at 64227
Ports     : OUT (254),A at 64162; OUT (254),A at 64338 (7FFD writes page memory at C000 / ROM)
Writes    : 1862 distinct RAM addresses (incl. its stacks)
Slots     : 0 (0x0000) r, 2 (0x4000) rw, 3 (0x6000) rw, 4 (0x8000) rwx, 5 (0xA000) rwx, 7 (0xE000) rwx; never touched: 1, 6
A hook running with interrupts ON must keep: SP must point at a stack with >= 28 free bytes; the alternate set is used by the handler (it saves/restores it? check the listing)
```
