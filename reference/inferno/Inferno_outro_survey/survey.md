# Survey: Inferno_outro (48K)
Read this first (PLAYBOOK stage 0). Raw numbers: survey.json. Commands to dig further: PLAYBOOK 2-3.

## Snapshot (inspect)
```
Machine   : 48K
PC        : 64495 (0xFBEF) - RAM
BASIC     : program 23755-23849, 3 line(s); USR targets: none
                10 PAPER USR VAL "23853": POKE VAL "23624",USR VAL "24460": CLEAR VAL "24199": RANDOMIZE USR VAL "5e4": RAND
                20 RANDOMIZE USR VAL "24200"
                30 RANDOMIZE USR VAL "24200"
RAMTOP    : 24199 (0x5E87)
Interrupts: IM 1, DI, I = 0xA8
IM 1      : ROM 0x0038 (hooks that page slot 0 must DI)
Stack     : SP 34509 (0x86CD); top words 4020 0020 ABE3 718F
Border    : 0
WARNING   : none
```
## Engine
Unknown: no detector in nexclash/engines.py and no TID / Dizzy 1 signature -> stage 1 (a new engine).

## Recordings
- Inferno_outro.rzx: no autosave snapshots

## Plain conversion
- Inferno_outro.nex: tail at 0x5B00 (printer buffer never used by the game); simulated boot: OK (registers, RAM, ROM view, paging). The user tests it on the Next with the stage-1 question.

## Recording and coverage
- 2001 frames analysed.
- GATE: OK - every CALL site to the top plot routines in code that ran was reached

## Screen writers by routine (innermost CALL running at the write)
| Routine | pixel / attr bytes | calls | callers seen | T per call median / max | called from | coverage |
|---|---|---|---|---|---|---|
| 48745 (0xBE69) | 155543 / 0 | 1842 | 1 | 18208 / 18507 | ISR | 1/1 CALL sites reached |
| 48351 (0xBCDF) | 53784 / 0 | 748 | 2 | 138196 / 214879 | 48252 (0xBC7C), 48200 (0xBC48), 48172 (0xBC2C) | 2/2 CALL sites reached |
| 48228 (0xBC64) | 6144 / 769 (6911 block copy) | 1 | 1 | 145208 / 145208 | 44096 (0xAC40) | 1/1 CALL sites reached |
Block copies (LDIR / LDI / PUSH) into the screen = probably a back buffer: `scan --range BUF --writers` on its source (PLAYBOOK 2). A routine in ROM (< 0x4000) is the ROM printing text.

## Preview (preview.png: screen at frames 250,500,750,1000,1250,1500,1750,2000, what each plot routine draws per caller)
```
Source    : ../specnext/reference/inferno/Inferno_outro.rzx, 2002 frames; shots at 250, 500, 750, 1000, 1250, 1500, 1750, 2000
Sheet     : ../specnext/reference/inferno/Inferno_outro_survey/preview.png (1040 x 392)
Group 0   : plot 48228 (0xBC64) from 47017 (0xB7A9): 1 calls, 6144 bytes drawn, x 0-255, y 0-191 (colour (255, 0, 0))
Group 1   : plot 48351 (0xBCDF) from 48264 (0xBC88): 744 calls, 53496 bytes drawn, x 0-255, y 8-183 (colour (0, 255, 0))
Group 2   : plot 48745 (0xBE69) from 48647 (0xBE07): 1843 calls, 155628 bytes drawn, x 0-255, y 2-189 (colour (0, 128, 255))
Group 3   : plot 48351 (0xBCDF) from 48224 (0xBC60): 5 calls, 360 bytes drawn, x 104-183, y 128-183 (colour (255, 0, 255))
```

## Screen writers (scan --writers)
```
Source    : ../specnext/reference/inferno/Inferno_outro.rzx, 2001 frames
Counting  : from the start
Lowest SP : 34481 (0x86B1) (any SP value: games that use SP as a data pointer show it here)
Range 0x4000-0x5AFF: 0 of 6912 bytes untouched
  touched     0x4000-0x5AFF (6912 bytes, rw), first: write at PC 48237
  write-first 0x4000-0x5AFF (6912 bytes)
  writers   9 instructions: 48824 (0xBEB8) x77793, 48775 (0xBE87) x77750, 48419 (0xBD23) x17928, 48426 (0xBD2A) x17928, 48432 (0xBD30) x17928, 48238 (0xBC6E) x6144, 48244 (0xBC74) x767, 48237 (0xBC6D) x1, 48243 (0xBC73) x1
  readers   9 instructions: 48812 (0xBEAC) x82890, 48819 (0xBEB3) x82890, 48823 (0xBEB7) x77793, 48774 (0xBE86) x77750, 48417 (0xBD21) x17928, 48424 (0xBD28) x17928, 48430 (0xBD2E) x17928, 48238 (0xBC6E) x6144, 48244 (0xBC74) x767
```
## Memory (scan: free memory for hook state, stack low-water)
```
Source    : ../specnext/reference/inferno/Inferno_outro.rzx, 2001 frames
Counting  : from the start
Lowest SP : 34481 (0x86B1) (any SP value: games that use SP as a data pointer show it here)
Range 0x4000-0xBFFF: 20621 of 32768 bytes untouched
  untouched   0x86D5-0xABDF (9483 bytes)
  untouched   0x5C7A-0x7108 (5263 bytes)
  untouched   0x7336-0x82DC (4007 bytes)
  untouched   0x8302-0x86B0 (943 bytes)
  untouched   0x71A7-0x7334 (398 bytes)
  untouched   0x5B00-0x5BFF (256 bytes)
  touched     0x4000-0x5AFF (6912 bytes, rw), first: write at PC 48237
  touched     0x5C00-0x5C00 (1 bytes, r), first: read at PC 710
  touched     0x5C04-0x5C05 (2 bytes, rw), first: read at PC 710
  touched     0x5C78-0x5C79 (2 bytes, rw), first: read at PC 58
  touched     0x7109-0x7109 (1 bytes, w), first: write at PC 29081
  touched     0x718F-0x71A6 (24 bytes, rx), first: exec at PC 29071
  touched     0x7335-0x7335 (1 bytes, r), first: read at PC 29071
  touched     0x82DD-0x82E8 (12 bytes, r), first: read at PC 48252
  touched     0x82FE-0x8301 (4 bytes, r), first: read at PC 47153
  touched     0x86B1-0x86D4 (36 bytes, rwx), first: write at PC 53430
  touched     0xABE0-0xBFFF (5152 bytes, rwx), first: write at PC 57263
  write-first 0x4000-0x5AFF (6912 bytes)
  write-first 0x86B1-0x86CC (28 bytes)
Range 0xC000-0xFFFF: 0 of 16384 bytes untouched
  touched     0xC000-0xFFFF (16384 bytes, rwx), first: read at PC 64477
  write-first 0xD906-0xFB66 (8801 bytes)
  write-first 0xFBB7-0xFBC7 (17 bytes)
  write-first 0xFE0F-0xFE2A (28 bytes)
```
## Interrupt handler (isr: what hooks must keep intact)
```
Source    : ../specnext/reference/inferno/Inferno_outro.rzx, 2001 frames, 1844 interrupts accepted, 0 never returned before the next
Mode      : IM 2, I = 0xFE (vector 0xFEFF) x1843; IM 1, I = 0xFE x1
Entered at: 65021 (0xFDFD) x1842, 56 (0x0038) x1
Executed  : 445 distinct instructions in the handler(s)
Uses IX   : saved / overwritten before any read of the interrupted value
Stack     : up to 20 bytes below the interrupted SP
Ports     : OUT (C),A at 53683; OUTD at 53687 (7FFD writes page memory at C000 / ROM)
Writes    : 1440 distinct RAM addresses (incl. its stacks)
Slots     : 0 (0x0000) rx, 2 (0x4000) rw, 4 (0x8000) rw, 5 (0xA000) rwx, 6 (0xC000) rwx, 7 (0xE000) rx; never touched: 1, 3 -> a hook may keep a RAM page mapped in slot 3 with interrupts on (LEARNINGS 1.3)
A hook running with interrupts ON must keep: SP must point at a stack with >= 22 free bytes
```
