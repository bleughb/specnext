# Survey: Inferno4 (48K)
Read this first (PLAYBOOK stage 0). Raw numbers: survey.json. Commands to dig further: PLAYBOOK 2-3.

## Snapshot (inspect)
```
Machine   : 48K
PC        : 56 (0x0038) - ROM IM 1 handler
Resume    : IM 1 stack return to RAM at 0xEA90; BASIC execution not established
BASIC     : program 23755-23849, 3 line(s); USR targets: none
                10 PAPER USR VAL "23853": POKE VAL "23624",USR VAL "24460": CLEAR VAL "24199": RANDOMIZE USR VAL "5e4": RAND
                20 RANDOMIZE USR VAL "24200"
                30 RANDOMIZE USR VAL "24200"
RAMTOP    : 24199 (0x5E87)
Interrupts: IM 1, DI, I = 0xA8
IM 1      : ROM 0x0038 (hooks that page slot 0 must DI)
Stack     : SP 34511 (0x86CF); top words EA90 ABE3 718F 73C6
Border    : 0
WARNING   : none
```
## Engine
Unknown: no detector in nexclash/engines.py and no TID / Dizzy 1 signature -> stage 1 (a new engine).

## Recordings
- Inferno4.rzx: no autosave snapshots

## Plain conversion
- Inferno4.nex: WARNING: no proven-safe tail location; converter default used; simulated boot: OK (registers, RAM, ROM view, paging). The user tests it on the Next with the stage-1 question.

## Recording and coverage
- 2001 frames analysed.
- GATE: OK - every CALL site to the top plot routines in code that ran was reached

## Screen writers by routine (innermost CALL running at the write)
| Routine | pixel / attr bytes | calls | callers seen | T per call median / max | called from | coverage |
|---|---|---|---|---|---|---|
| 38800 (0x9790) | 647808 / 210816 (210816 block copy) | 367 | 1 | 201141 / 268022 | top | 1/1 CALL sites reached |
| 33414 (0x8286) | 82432 / 10304 (92736 block copy) | 322 | 1 | 6917 / 7799 | 33379 (0x8263) | 1/1 CALL sites reached |
| 32496 (0x7EF0) | 7672 / 0 | 959 | 3 | 528 / 1410 | 32429 (0x7EAD), 32404 (0x7E94) | 3/3 CALL sites reached |
| 33379 (0x8263) | 5120 / 64 (576 block copy) | 18 | 1 | 136024 / 136906 | top | 1/1 CALL sites reached |
| 32517 (0x7F05) | 0 / 1678 | 1678 | 5 | 58 / 940 | 32496 (0x7EF0), 32429 (0x7EAD), 33414 (0x8286), 33379 (0x8263), 33106 (0x8152), 31123 (0x7993) | 5/7 CALL sites reached |
| 36908 (0x902C) | 1504 / 0 | 222 | 4 | 682 / 1224 | top | 4/4 CALL sites reached |
Block copies (LDIR / LDI / PUSH) into the screen = probably a back buffer: `scan --range BUF --writers` on its source (PLAYBOOK 2). A routine in ROM (< 0x4000) is the ROM printing text.

## Preview (preview.png: screen at frames 250,500,750,1000,1250,1500,1750,2000, what each plot routine draws per caller)
```
Source    : ../specnext/reference/inferno/Inferno4.rzx, 2002 frames; shots at 250, 500, 750, 1000, 1250, 1500, 1750, 2000
Sheet     : ../specnext/reference/inferno/Inferno4_survey/preview.png (1040 x 392)
Group 0   : plot 32496 (0x7EF0) from 32434 (0x7EB2): 30 calls, 240 bytes drawn, x 0-7, y 0-191 (colour (255, 0, 0))
Group 1   : plot 32517 (0x7F05) from 32514 (0x7F02): 960 calls, 0 bytes drawn, x -, y - (colour (0, 255, 0))
Group 2   : plot 32496 (0x7EF0) from 32444 (0x7EBC): 900 calls, 7200 bytes drawn, x 8-247, y 0-191 (colour (0, 128, 255))
Group 3   : plot 32496 (0x7EF0) from 32456 (0x7EC8): 30 calls, 240 bytes drawn, x 248-255, y 0-191 (colour (255, 0, 255))
Group 4   : plot 33379 (0x8263) from 30565 (0x7765): 18 calls, 4608 bytes drawn, x 0-255, y 184-191 (colour (255, 160, 0))
Group 5   : plot 33414 (0x8286) from 33392 (0x8270): 324 calls, 82944 bytes drawn, x 0-255, y 40-183 (colour (0, 255, 255))
Group 6   : plot 32517 (0x7F05) from 33438 (0x829E): 324 calls, 0 bytes drawn, x -, y - (colour (255, 255, 0))
Group 7   : plot 32517 (0x7F05) from 33443 (0x82A3): 324 calls, 0 bytes drawn, x -, y - (colour (160, 80, 255))
Group 8   : plot 32517 (0x7F05) from 33131 (0x816B): 62 calls, 0 bytes drawn, x -, y - (colour (255, 128, 128))
Group 9   : plot 32517 (0x7F05) from 31134 (0x799E): 8 calls, 0 bytes drawn, x -, y - (colour (128, 255, 128))
Group 10  : plot 38800 (0x9790) from 36757 (0x8F95): 367 calls, 648840 bytes drawn, x 0-255, y 48-191 (colour (128, 128, 255))
Group 11  : plot 36908 (0x902C) from 36794 (0x8FBA): 101 calls, 548 bytes drawn, x 56-159, y 10-13 (colour (200, 200, 0))
```

## Screen writers (scan --writers)
```
Source    : ../specnext/reference/inferno/Inferno4.rzx, 2001 frames
Counting  : from the start
Lowest SP : 34475 (0x86AB) (any SP value: games that use SP as a data pointer show it here)
Range 0x4000-0x5AFF: 0 of 6912 bytes untouched
  touched     0x4000-0x5AFF (6912 bytes, rw), first: write at PC 32499
  write-first 0x4000-0x5AFF (6912 bytes)
  writers   67 instructions: 33424 (0x8290) x82944, 38937 (0x9819) x80976, 38939 (0x981B) x80976, 38942 (0x981E) x80976, 38944 (0x9820) x80976, 38947 (0x9823) x80976, 38949 (0x9825) x80976, 38952 (0x9828) x80976, 38954 (0x982A) x80976, 33443 (0x82A3) x10368
  writers+  57 more instructions in 15 routine span(s): 30596-30596 (0x7784) x416, 30645-30645 (0x77B5) x52, 31136-31136 (0x79A0) x64, 32499-32499 (0x7EF3) x7680, 32528-32528 (0x7F10) x1678, 33132-33132 (0x816C) x62, 33147-33149 (0x817B) x124, 33198-33204 (0x81AE) x638, 33403-33403 (0x827B) x4608, 36925-36932 (0x903D) x480, 36953-36959 (0x9059) x816, 36970-36977 (0x906A) x208, 38964-39026 (0x9834) x210816, 44953-44953 (0xAF99) x32, 45006-45006 (0xAFCE) x36
  readers   7 instructions: 33424 (0x8290) x82944, 33443 (0x82A3) x10368, 36921 (0x9039) x1914, 36966 (0x9066) x768, 37054 (0x90BE) x736, 33194 (0x81AA) x319, 33200 (0x81B0) x319
```
## Memory (scan: free memory for hook state, stack low-water)
```
Source    : ../specnext/reference/inferno/Inferno4.rzx, 2001 frames
Counting  : from the start
Lowest SP : 34475 (0x86AB) (any SP value: games that use SP as a data pointer show it here)
Range 0x4000-0xBFFF: 12226 of 32768 bytes untouched
  untouched   0x623C-0x6AC6 (2187 bytes)
  untouched   0x86D9-0x8EF7 (2079 bytes)
  untouched   0x6E46-0x7108 (707 bytes)
  untouched   0x7C47-0x7E93 (589 bytes)
  untouched   0x82FE-0x8524 (551 bytes)
  untouched   0x79B3-0x7BC2 (528 bytes)
  touched     0x4000-0x5B1F (6944 bytes, rw), first: write at PC 32499
  touched     0x5B79-0x5B79 (1 bytes, rw), first: write at PC 33085
  touched     0x5BF8-0x5C00 (9 bytes, rw), first: write at PC 37363
  touched     0x5C04-0x5C09 (6 bytes, rw), first: read at PC 710
  touched     0x5C26-0x5C2E (9 bytes, rw), first: write at PC 29612
  touched     0x5C3B-0x5C3B (1 bytes, rw), first: read at PC 767
  touched     0x5C41-0x5C41 (1 bytes, r), first: read at PC 764
  touched     0x5C78-0x5C79 (2 bytes, rw), first: read at PC 58
  touched     0x5C81-0x5C81 (1 bytes, w), first: write at PC 37499
  touched     0x5CB0-0x5CB0 (1 bytes, rw), first: write at PC 37502
  touched     0x5EA5-0x5EA5 (1 bytes, r), first: read at PC 32842
  touched     0x5EAC-0x5EAE (3 bytes, r), first: read at PC 32842
  ... 163 more touched spans
  write-first 0x4000-0x5AFF (6912 bytes)
  write-first 0x86AB-0x86CE (36 bytes)
  write-first 0x9A80-0x9F7F (1280 bytes)
  write-first 0xA23E-0xA25C (31 bytes)
  write-first 0xA2A3-0xA2B5 (19 bytes)
```
## Interrupt handler (isr: what hooks must keep intact)
```
Source    : ../specnext/reference/inferno/Inferno4.rzx, 2001 frames, 1619 interrupts accepted, 366 never returned before the next
Mode      : IM 2, I = 0xA8 (vector 0xA8FF) x1204; IM 1, I = 0xA8 x415
Entered at: 65535 (0xFFFF) x1203, 56 (0x0038) x415
Executed  : 965 distinct instructions in the handler(s)
Uses IX   : saved / overwritten before any read of the interrupted value
Reads IY  : the INTERRUPTED code's value: LD C,(IY+7) at 764; LD D,(IY+1) at 767; SET 5,(IY+1) at 779
Uses alternate set (EXX): EXX at 36942; EXX at 36951; EXX at 38661 (+6 more)
Stack     : up to 1022 bytes below the interrupted SP; switches stack: LD SP,HL at 38934, LD SP,41554 at 38955, LD SP,65522 at 39031
Ports     : OUT (254),A at 36698; OUT (254),A at 38853 (7FFD writes page memory at C000 / ROM)
Writes    : 7328 distinct RAM addresses (incl. its stacks)
Slots     : 0 (0x0000) rx, 2 (0x4000) rw, 4 (0x8000) rwx, 5 (0xA000) rw, 6 (0xC000) r, 7 (0xE000) rwx; never touched: 1, 3 -> a hook may keep a RAM page mapped in slot 3 with interrupts on (LEARNINGS 1.3)
A hook running with interrupts ON must keep: SP must point at a stack with >= 1024 free bytes; IY unchanged; the alternate set is used by the handler (it saves/restores it? check the listing)
```
