# Survey: Inferno5 (48K)
Read this first (PLAYBOOK stage 0). Raw numbers: survey.json. Commands to dig further: PLAYBOOK 2-3.

## Snapshot (inspect)
```
Machine   : 48K
PC        : 56 (0x0038) - ROM IM 1 handler
Resume    : IM 1 stack return to RAM at 0xEC22; BASIC execution not established
BASIC     : program 23755-23849, 3 line(s); USR targets: none
                10 PAPER USR VAL "23853": POKE VAL "23624",USR VAL "24460": CLEAR VAL "24199": RANDOMIZE USR VAL "5e4": RAND
                20 RANDOMIZE USR VAL "24200"
                30 RANDOMIZE USR VAL "24200"
RAMTOP    : 24199 (0x5E87)
Interrupts: IM 1, DI, I = 0xA8
IM 1      : ROM 0x0038 (hooks that page slot 0 must DI)
Stack     : SP 34511 (0x86CF); top words EC22 ABE3 718F 73C6
Border    : 0
WARNING   : none
```
## Engine
Unknown: no detector in nexclash/engines.py and no TID / Dizzy 1 signature -> stage 1 (a new engine).

## Recordings
- Inferno5.rzx: no autosave snapshots

## Plain conversion
- Inferno5.nex: WARNING: no proven-safe tail location; converter default used; simulated boot: OK (registers, RAM, ROM view, paging). The user tests it on the Next with the stage-1 question.

## Recording and coverage
- 2001 frames analysed.
- GATE: OK - every CALL site to the top plot routines in code that ran was reached

## Screen writers by routine (innermost CALL running at the write)
| Routine | pixel / attr bytes | calls | callers seen | T per call median / max | called from | coverage |
|---|---|---|---|---|---|---|
| 38800 (0x9790) | 68720 / 35136 (35136 block copy) | 61 | 1 | 212139 / 214693 | top | 1/1 CALL sites reached |
| 33414 (0x8286) | 82944 / 10368 (93312 block copy) | 324 | 1 | 6917 / 7799 | 33379 (0x8263) | 1/1 CALL sites reached |
| 31815 (0x7C47) | 43232 / 1352 | 15 | 1 | 57050 / 18022706 | top | 1/1 CALL sites reached; 1 JP site(s) (not tracked) |
| 32496 (0x7EF0) | 19576 / 0 | 2447 | 3 | 528 / 1639 | 32429 (0x7EAD), 32404 (0x7E94) | 3/3 CALL sites reached |
| 33106 (0x8152) | 7174 / 2370 | 790 | 1 | 23703 / 25533 | 32669 (0x7F9D) | 1/1 CALL sites reached |
| 31991 (0x7CF7) | 5984 / 0 | 691 | 2 | 347 / 927689 | top, 31815 (0x7C47) | 2/2 CALL sites reached |
Block copies (LDIR / LDI / PUSH) into the screen = probably a back buffer: `scan --range BUF --writers` on its source (PLAYBOOK 2). A routine in ROM (< 0x4000) is the ROM printing text.

## Preview (preview.png: screen at frames 250,500,750,1000,1250,1500,1750,2000, what each plot routine draws per caller)
```
Source    : ../specnext/reference/inferno/Inferno5.rzx, 2002 frames; shots at 250, 500, 750, 1000, 1250, 1500, 1750, 2000
Sheet     : ../specnext/reference/inferno/Inferno5_survey/preview.png (1040 x 392)
Group 0   : plot 32496 (0x7EF0) from 32434 (0x7EB2): 162 calls, 1296 bytes drawn, x 0-215, y 0-191 (colour (255, 0, 0))
Group 1   : plot 32496 (0x7EF0) from 32444 (0x7EBC): 2124 calls, 16992 bytes drawn, x 8-247, y 0-191 (colour (0, 255, 0))
Group 2   : plot 32496 (0x7EF0) from 32456 (0x7EC8): 162 calls, 1296 bytes drawn, x 40-255, y 0-191 (colour (0, 128, 255))
Group 3   : plot 33414 (0x8286) from 33392 (0x8270): 324 calls, 82944 bytes drawn, x 0-255, y 40-183 (colour (255, 0, 255))
Group 4   : plot 33106 (0x8152) from 32944 (0x80B0): 791 calls, 7182 bytes drawn, x 8-247, y 9-179 (colour (255, 160, 0))
Group 5   : plot 38800 (0x9790) from 36757 (0x8F95): 61 calls, 68720 bytes drawn, x 0-255, y 48-191 (colour (0, 255, 255))
Group 6   : plot 31991 (0x7CF7) from 31510 (0x7B16): 15 calls, 352 bytes drawn, x 8-183, y 168-183 (colour (255, 255, 0))
Group 7   : plot 31815 (0x7C47) from 31513 (0x7B19): 677 calls, 43296 bytes drawn, x 56-247, y 52-167 (colour (160, 80, 255))
Group 8   : plot 31991 (0x7CF7) from 31821 (0x7C4D): 677 calls, 5632 bytes drawn, x 8-183, y 168-183 (colour (255, 128, 128))
```

## Screen writers (scan --writers)
```
Source    : ../specnext/reference/inferno/Inferno5.rzx, 2001 frames
Counting  : from the start
Lowest SP : 34461 (0x869D) (any SP value: games that use SP as a data pointer show it here)
Range 0x4000-0x5AFF: 0 of 6912 bytes untouched
  touched     0x4000-0x5AFF (6912 bytes, rw), first: write at PC 32499
  write-first 0x4000-0x5AFF (6912 bytes)
  writers   82 instructions: 33424 (0x8290) x82944, 32499 (0x7EF3) x19584, 31887 (0x7C8F) x10816, 31900 (0x7C9C) x10816, 31918 (0x7CAE) x10800, 31925 (0x7CB5) x10800, 33443 (0x82A3) x10368, 38937 (0x9819) x8590, 38939 (0x981B) x8590, 38942 (0x981E) x8590
  writers+  72 more instructions in 22 routine span(s): 30596-30596 (0x7784) x416, 30645-30645 (0x77B5) x52, 31136-31136 (0x79A0) x64, 31744-31758 (0x7C00) x126, 31823-31826 (0x7C4F) x1352, 32078-32078 (0x7D4E) x5984, 32334-32334 (0x7E4E) x2080, 32355-32355 (0x7E63) x260, 32375-32388 (0x7E77) x408, 32528-32528 (0x7F10) x3941, 33132-33132 (0x816C) x791, 33147-33149 (0x817B) x1582, 33198-33204 (0x81AE) x7182, 33305-33305 (0x8219) x759, 33332-33332 (0x8234) x1861, 33403-33403 (0x827B) x4608, 36925-36932 (0x903D) x172, 36953-36959 (0x9059) x12, 38944-38954 (0x9820) x42950, 38964-39026 (0x9834) x35136 ...
  readers   11 instructions: 33424 (0x8290) x82944, 31878 (0x7C86) x10816, 31885 (0x7C8D) x10816, 31891 (0x7C93) x10816, 31898 (0x7C9A) x10816, 33443 (0x82A3) x10368, 33194 (0x81AA) x3591, 33200 (0x81B0) x3591, 37054 (0x90BE) x120, 36921 (0x9039) x67
  readers+  1 more instructions in 1 routine span(s): 36966-36966 (0x9066) x8
```
## Memory (scan: free memory for hook state, stack low-water)
```
Source    : ../specnext/reference/inferno/Inferno5.rzx, 2001 frames
Counting  : from the start
Lowest SP : 34461 (0x869D) (any SP value: games that use SP as a data pointer show it here)
Range 0x4000-0xBFFF: 8513 of 32768 bytes untouched
  untouched   0x86D9-0x8EF7 (2079 bytes)
  untouched   0x6ECB-0x7108 (574 bytes)
  untouched   0x5CB3-0x5E8A (472 bytes)
  untouched   0x758E-0x7730 (419 bytes)
  untouched   0x71AB-0x7334 (394 bytes)
  untouched   0x830C-0x844E (323 bytes)
  touched     0x4000-0x5B4A (6987 bytes, rw), first: write at PC 32499
  touched     0x5B79-0x5B80 (8 bytes, rw), first: write at PC 33085
  touched     0x5BF8-0x5C00 (9 bytes, rw), first: write at PC 37363
  touched     0x5C04-0x5C09 (6 bytes, rw), first: read at PC 710
  touched     0x5C26-0x5C2E (9 bytes, rw), first: write at PC 29612
  touched     0x5C3B-0x5C3B (1 bytes, rw), first: read at PC 767
  touched     0x5C41-0x5C41 (1 bytes, r), first: read at PC 764
  touched     0x5C6A-0x5C6A (1 bytes, r), first: read at PC 858
  touched     0x5C78-0x5C79 (2 bytes, rw), first: read at PC 58
  touched     0x5C81-0x5C81 (1 bytes, rw), first: write at PC 37499
  touched     0x5CB0-0x5CB2 (3 bytes, rw), first: write at PC 37502
  touched     0x5E8B-0x5E8B (1 bytes, r), first: read at PC 32842
  ... 212 more touched spans
  write-first 0x4000-0x5AFF (6912 bytes)
  write-first 0x5B15-0x5B4A (54 bytes)
  write-first 0x7D9D-0x7DBC (32 bytes)
  write-first 0x869D-0x86CE (50 bytes)
  write-first 0x9A80-0x9F7F (1280 bytes)
```
## Interrupt handler (isr: what hooks must keep intact)
```
Source    : ../specnext/reference/inferno/Inferno5.rzx, 2001 frames, 1916 interrupts accepted, 61 never returned before the next
Mode      : IM 1, I = 0xA8 x1733; IM 2, I = 0xA8 (vector 0xA8FF) x183
Entered at: 56 (0x0038) x1732, 65535 (0xFFFF) x183
Executed  : 1361 distinct instructions in the handler(s)
Uses IX   : saved / overwritten before any read of the interrupted value
Reads IY  : the INTERRUPTED code's value: LD C,(IY+7) at 764; LD D,(IY+1) at 767; SET 5,(IY+1) at 779 (+1 more)
Uses R    : LD A,R at 46910; LD A,R at 46915; LD A,R at 47050
Uses alternate set (EXX): EXX at 36942; EXX at 36951; EXX at 38661 (+7 more)
Stack     : up to 118 bytes below the interrupted SP; switches stack: LD SP,HL at 38934, LD SP,42100 at 38955, LD SP,65522 at 39031
Ports     : OUT (254),A at 28206; OUT (254),A at 36698; OUT (254),A at 38853 (7FFD writes page memory at C000 / ROM)
Writes    : 5720 distinct RAM addresses (incl. its stacks)
Slots     : 0 (0x0000) rx, 2 (0x4000) rw, 3 (0x6000) rwx, 4 (0x8000) rwx, 5 (0xA000) rwx, 6 (0xC000) rw, 7 (0xE000) rwx; never touched: 1
A hook running with interrupts ON must keep: SP must point at a stack with >= 120 free bytes; IY unchanged; the alternate set is used by the handler (it saves/restores it? check the listing)
```
