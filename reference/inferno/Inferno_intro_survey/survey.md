# Survey: Inferno_intro (48K)
Read this first (PLAYBOOK stage 0). Raw numbers: survey.json. Commands to dig further: PLAYBOOK 2-3.

## Snapshot (inspect)
```
Machine   : 48K
PC        : 65535 (0xFFFF) - RAM
BASIC     : program 23755-23849, 3 line(s); USR targets: none
                10 PAPER USR VAL "23853": POKE VAL "23624",USR VAL "24460": CLEAR VAL "24199": RANDOMIZE USR VAL "5e4": RAND
                20 RANDOMIZE USR VAL "24200"
                30 RANDOMIZE USR VAL "24200"
RAMTOP    : 24199 (0x5E87)
Interrupts: IM 2, DI, I = 0x3B
IM 2      : vector at 0x3BFF -> 0 (0x0000) (table of 257 equal bytes)
Stack     : SP 36073 (0x8CE9); top words 89E9 D380 D996 8EF8
Border    : 0
WARNING   : IM 2 handler in ROM (0x0000)
```
## Engine
Unknown: no detector in nexclash/engines.py and no TID / Dizzy 1 signature -> stage 1 (a new engine).

## Recordings
- Inferno_intro.rzx: no autosave snapshots

## Plain conversion
- Inferno_intro.nex: tail at 0x8C89 (converter default, checked safe); simulated boot: OK (registers, RAM, ROM view, paging). The user tests it on the Next with the stage-1 question.

## Recording and coverage
- 2001 frames analysed.
- GATE: OK - every CALL site to the top plot routines in code that ran was reached

## Screen writers by routine (innermost CALL running at the write)
| Routine | pixel / attr bytes | calls | callers seen | T per call median / max | called from | coverage |
|---|---|---|---|---|---|---|
| top (outside any CALL) | 193920 / 0 (190785 block copy) | 0 | 0 | - | - | - |
| ISR (interrupt handler) | 15426 / 0 | 0 | 0 | - | - | - |
| 54053 (0xD325) | 10112 / 0 | 79 | 1 | 12766 / 12766 | top | 1/1 CALL sites reached |
| 32496 (0x7EF0) | 6144 / 0 | 768 | 3 | 528 / 1410 | 32429 (0x7EAD), 32404 (0x7E94) | 3/3 CALL sites reached |
| 52500 (0xCD14) | 5280 / 676 | 1 | 1 | - | top | 1/1 CALL sites reached |
| 57261 (0xDFAD) | 3468 / 0 | 323 | 2 | 2498 / 3449 | ISR, top | 2/2 CALL sites reached |
Block copies (LDIR / LDI / PUSH) into the screen = probably a back buffer: `scan --range BUF --writers` on its source (PLAYBOOK 2). A routine in ROM (< 0x4000) is the ROM printing text.

## Preview (preview.png: screen at frames 250,500,750,1000,1250,1500,1750,2000, what each plot routine draws per caller)
```
Source    : ../specnext/reference/inferno/Inferno_intro.rzx, 2002 frames; shots at 250, 500, 750, 1000, 1250, 1500, 1750, 2000
Sheet     : ../specnext/reference/inferno/Inferno_intro_survey/preview.png (1040 x 392)
Group 0   : plot 32496 (0x7EF0) from 32434 (0x7EB2): 24 calls, 192 bytes drawn, x 0-7, y 0-191 (colour (255, 0, 0))
Group 1   : plot 32496 (0x7EF0) from 32444 (0x7EBC): 720 calls, 5760 bytes drawn, x 8-247, y 0-191 (colour (0, 255, 0))
Group 2   : plot 32496 (0x7EF0) from 32456 (0x7EC8): 24 calls, 192 bytes drawn, x 248-255, y 0-191 (colour (0, 128, 255))
Group 3   : plot 52500 (0xCD14) from 28099 (0x6DC3): 1 calls, 5310 bytes drawn, x 8-247, y 8-183 (colour (255, 0, 255))
Group 4   : plot 57261 (0xDFAD) from 56849 (0xDE11): 179 calls, 1896 bytes drawn, x 16-239, y 171-181 (colour (255, 160, 0))
Group 5   : plot 54053 (0xD325) from 53947 (0xD2BB): 79 calls, 10112 bytes drawn, x 176-239, y 16-31 (colour (0, 255, 255))
Group 6   : plot 57261 (0xDFAD) from 56903 (0xDE47): 144 calls, 1572 bytes drawn, x 16-239, y 171-181 (colour (255, 255, 0))
```

## Screen writers (scan --writers)
```
Source    : ../specnext/reference/inferno/Inferno_intro.rzx, 2001 frames
Counting  : from the start
Lowest SP : 24134 (0x5E46) (any SP value: games that use SP as a data pointer show it here)
Range 0x4000-0x5AFF: 0 of 6912 bytes untouched
  touched     0x4000-0x5AFF (6912 bytes, rw), first: write at PC 32499
  write-first 0x4000-0x5AFF (6912 bytes)
  writers   54 instructions: 53999 (0xD2EF) x10270, 54001 (0xD2F1) x10270, 54003 (0xD2F3) x10270, 54005 (0xD2F5) x10270, 54007 (0xD2F7) x10270, 54009 (0xD2F9) x10270, 54011 (0xD2FB) x10270, 54013 (0xD2FD) x10270, 54015 (0xD2FF) x10270, 54017 (0xD301) x10270
  writers+  44 more instructions in 19 routine span(s): 32499-32499 (0x7EF3) x6144, 32528-32528 (0x7F10) x790, 33132-33132 (0x816C) x22, 33147-33149 (0x817B) x44, 33198-33204 (0x81AE) x200, 33305-33305 (0x8219) x171, 33332-33332 (0x8234) x419, 52517-52517 (0xCD25) x660, 52545-52549 (0xCD41) x16, 52566-52566 (0xCD56) x5280, 53960-53988 (0xD2C8) x5925, 54019-54033 (0xD303) x82160, 54088-54088 (0xD348) x10112, 56563-56563 (0xDCF3) x8622, 56743-56743 (0xDDA7) x7232, 56764-56764 (0xDDBC) x2707, 57249-57249 (0xDFA1) x13, 57259-57259 (0xDFAB) x17, 57340-57344 (0xDFFC) x3468
  readers   9 instructions: 56559 (0xDCEF) x8622, 56742 (0xDDA6) x7232, 56763 (0xDDBB) x2707, 57339 (0xDFFB) x1734, 57343 (0xDFFF) x1734, 33194 (0x81AA) x100, 33200 (0x81B0) x100, 57258 (0xDFAA) x17, 57248 (0xDFA0) x13
```
## Memory (scan: free memory for hook state, stack low-water)
```
Source    : ../specnext/reference/inferno/Inferno_intro.rzx, 2001 frames
Counting  : from the start
Lowest SP : 24134 (0x5E46) (any SP value: games that use SP as a data pointer show it here)
Range 0x4000-0xBFFF: 726 of 32768 bytes untouched
  untouched   0x5D45-0x5E45 (257 bytes)
  untouched   0x5C7A-0x5D19 (160 bytes)
  untouched   0x5B7C-0x5BFF (132 bytes)
  untouched   0x5B2C-0x5B78 (77 bytes)
  untouched   0x5C0B-0x5C3A (48 bytes)
  untouched   0x5B00-0x5B14 (21 bytes)
  touched     0x4000-0x5AFF (6912 bytes, rw), first: write at PC 32499
  touched     0x5B15-0x5B2B (23 bytes, rw), first: write at PC 32814
  touched     0x5B79-0x5B7B (3 bytes, rw), first: write at PC 33085
  touched     0x5C00-0x5C00 (1 bytes, r), first: read at PC 710
  touched     0x5C04-0x5C0A (7 bytes, rw), first: read at PC 710
  touched     0x5C3B-0x5C3B (1 bytes, rw), first: read at PC 10088
  touched     0x5C41-0x5C41 (1 bytes, rw), first: write at PC 28059
  touched     0x5C44-0x5C47 (4 bytes, rw), first: read at PC 7037
  touched     0x5C4B-0x5C6A (32 bytes, rw), first: read at PC 5739
  touched     0x5C74-0x5C79 (6 bytes, rw), first: read at PC 7190
  touched     0x5D1A-0x5D29 (16 bytes, r), first: read at PC 27
  touched     0x5D2F-0x5D44 (22 bytes, rw), first: read at PC 5729
  ... 2 more touched spans
  write-first 0x4000-0x5AFF (6912 bytes)
  write-first 0x5B15-0x5B2B (23 bytes)
  write-first 0x5D30-0x5D44 (21 bytes)
  write-first 0x5E46-0x5E6D (40 bytes)
  write-first 0x8CD1-0x8CE8 (24 bytes)
```
## Interrupt handler (isr: what hooks must keep intact)
```
Source    : ../specnext/reference/inferno/Inferno_intro.rzx, 2001 frames, 1868 interrupts accepted, 1 never returned before the next
Mode      : IM 2, I = 0xFE (vector 0xFEFF) x1041; IM 2, I = 0x3B (vector 0x3BFF) x608; IM 1, I = 0x3B x219
Entered at: 65021 (0xFDFD) x1040, 65535 (0xFFFF) x608, 56 (0x0038) x219
Executed  : 1698 distinct instructions in the handler(s)
Uses IX   : saved / overwritten before any read of the interrupted value
Reads IY  : the INTERRUPTED code's value: LD C,(IY+7) at 764; LD D,(IY+1) at 767; SET 5,(IY+1) at 779 (+1 more)
Uses I    : LD A,I at 54036
Uses alternate set (EXX): EXX at 13154; EXX at 13156; EXX at 13161 (+17 more)
Uses AF'  : EX AF,AF' at 35939; EX AF,AF' at 35942; EX AF,AF' at 54156 (+1 more)
Stack     : up to 26 bytes below the interrupted SP; switches stack: LD SP,(36081) at 54146
Ports     : OUT (254),A at 35721; OUT (254),A at 35756; OUT (254),A at 35777; OUT (C),A at 42073 (7FFD writes page memory at C000 / ROM)
Writes    : 45523 distinct RAM addresses (incl. its stacks)
Slots     : 0 (0x0000) rx, 1 (0x2000) rx, 2 (0x4000) rwx, 3 (0x6000) rw, 4 (0x8000) rwx, 5 (0xA000) rwx, 6 (0xC000) rwx, 7 (0xE000) rwx; never touched: none
A hook running with interrupts ON must keep: SP must point at a stack with >= 28 free bytes; IY unchanged; I unchanged; the alternate set is used by the handler (it saves/restores it? check the listing)
```
