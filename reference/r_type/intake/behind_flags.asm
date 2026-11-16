; R-Type sprite build: figures drawn BEHIND the scenery, as in the original.
; Every other figure is a hardware sprite in front of the scenery (l2scroll.asm LORDER).
; A flagged figure is not made a sprite: the game draws it in the ULA, under Layer 2, so the
; scenery hides it exactly as the original does (8x8 cells).
;
;     FLAG level, graphic        level = the level byte at 719C ("1" = 0x31 ... "8" = 0x38)
;
; Edit by hand: delete or comment out a line to bring that figure in front, or add a line
; (graphics are in colours/r_type_figures.json, families -> graphics). Generated first by
; tools/behind.py --flags --min 50 from a scan of the original (updates hidden).

; L1-F91  hidden 210 updates  figures L1-121, L1-122, L1-123, L1-124
        FLAG 0x31, 0xCBE7
; L1-F82  hidden 162 updates  figures L1-102, L1-108
        FLAG 0x31, 0xD574
; L1-F83  hidden 84 updates  figures L1-103, L1-105, L1-110, L1-114
        FLAG 0x31, 0xD5C5
; L1-F16  hidden 80 updates  figures L1-016   [off: explosion/shot]
;       FLAG 0x31, 0xB32E
; L1-F60  hidden 51 updates  figures L1-070   [off: explosion/shot]
;       FLAG 0x31, 0xB6DB
; L2-F25  hidden 495 updates  figures L2-025, L2-046, L2-051, L2-058
        FLAG 0x32, 0xCBC7
; L2-F26  hidden 457 updates  figures L2-026, L2-047, L2-052, L2-059
        FLAG 0x32, 0xCC80
; L2-F69  hidden 327 updates  figures L2-093, L2-095, L2-107, L2-120
        FLAG 0x32, 0xCB76
; L2-F61  hidden 124 updates  figures L2-076   [off: explosion/shot]
;       FLAG 0x32, 0xB0EB
; L2-F43  hidden 68 updates  figures L2-048   [off: explosion/shot]
;       FLAG 0x32, 0xB6DB
; L2-F65  hidden 63 updates  figures L2-085, L2-101, L2-115, L2-126
        FLAG 0x32, 0xCB25
; L2-F44  hidden 61 updates  figures L2-049   [off: explosion/shot]
;       FLAG 0x32, 0xB7AC
; L2-F29  hidden 60 updates  figures L2-029   [off: explosion/shot]
;       FLAG 0x32, 0xB32E
; L2-F66  hidden 57 updates  figures L2-086, L2-090, L2-102, L2-106
        FLAG 0x32, 0xCAD4
; L2-F67  hidden 50 updates  figures L2-087, L2-091, L2-113, L2-124
        FLAG 0x32, 0xC93F
; L3-F26  hidden 239 updates  figures L3-026, L3-028, L3-124
        FLAG 0x33, 0xC85F
; L3-F30  hidden 116 updates  figures L3-032, L3-159
        FLAG 0x33, 0xC7FB
; L3-F38  hidden 59 updates  figures L3-048, L3-049, L3-050, L3-051
        FLAG 0x33, 0xDBFF
; L3-F54  hidden 55 updates  figures L3-095   [off: explosion/shot]
;       FLAG 0x33, 0xB6DB
; L3-F41  hidden 54 updates  figures L3-054   [off: explosion/shot]
;       FLAG 0x33, 0xB32E
; L4-F31  hidden 63 updates  figures L4-032, L4-071
        FLAG 0x34, 0xD6E7
; L5-F48  hidden 195 updates  figures L5-062, L5-077
        FLAG 0x35, 0xCB23
; L5-F35  hidden 95 updates  figures L5-043, L5-074
        FLAG 0x35, 0xCBBD
; L5-F26  hidden 76 updates  figures L5-034, L5-044, L5-064, L5-065
        FLAG 0x35, 0xCB74
; L5-F55  hidden 74 updates  figures L5-080, L5-091
        FLAG 0x35, 0xC9DF
; L5-F57  hidden 70 updates  figures L5-082, L5-092, L5-106
        FLAG 0x35, 0xC98E
; L5-F12  hidden 59 updates  figures L5-016, L5-021
        FLAG 0x35, 0xAC13
; L5-F47  hidden 58 updates  figures L5-061, L5-076
        FLAG 0x35, 0xCA30
; L5-F58  hidden 58 updates  figures L5-084, L5-093
        FLAG 0x35, 0xC93D
; L5-F15  hidden 57 updates  figures L5-020, L5-025
        FLAG 0x35, 0xAC37
; L5-F40  hidden 53 updates  figures L5-051, L5-078
        FLAG 0x35, 0xCCB0
; L5-F11  hidden 52 updates  figures L5-014, L5-017
        FLAG 0x35, 0xABEF
; L5-F04  hidden 50 updates  figures L5-004, L5-024
        FLAG 0x35, 0xAC5B
; L6-F17  hidden 288 updates  figures L6-025   [off: explosion/shot]
;       FLAG 0x36, 0xB0EB
; L6-F13  hidden 269 updates  figures L6-017, L6-020
        FLAG 0x36, 0xAC13
; L6-F12  hidden 263 updates  figures L6-015, L6-018
        FLAG 0x36, 0xABEF
; L6-F11  hidden 261 updates  figures L6-013, L6-016
        FLAG 0x36, 0xABCB
; L6-F14  hidden 256 updates  figures L6-019, L6-023
        FLAG 0x36, 0xAC37
; L6-F09  hidden 248 updates  figures L6-010, L6-014
        FLAG 0x36, 0xACC7
; L6-F04  hidden 246 updates  figures L6-004, L6-022
        FLAG 0x36, 0xAC5B
; L6-F03  hidden 240 updates  figures L6-003, L6-008
        FLAG 0x36, 0xAC7F
; L6-F07  hidden 239 updates  figures L6-007, L6-011
        FLAG 0x36, 0xACA3
; L6-F19  hidden 169 updates  figures L6-027   [off: explosion/shot]
;       FLAG 0x36, 0xB05B
; L6-F42  hidden 81 updates  figures L6-050   [off: explosion/shot]
;       FLAG 0x36, 0xB7AC
; L6-F41  hidden 80 updates  figures L6-049   [off: explosion/shot]
;       FLAG 0x36, 0xB6DB
; L6-F44  hidden 56 updates  figures L6-052   [off: explosion/shot]
;       FLAG 0x36, 0xB87D
; L7-F10  hidden 199 updates  figures L7-012, L7-016
        FLAG 0x37, 0xABCB
; L7-F12  hidden 199 updates  figures L7-015, L7-021
        FLAG 0x37, 0xABEF
; L7-F06  hidden 195 updates  figures L7-006, L7-010
        FLAG 0x37, 0xACA3
; L7-F08  hidden 194 updates  figures L7-009, L7-013
        FLAG 0x37, 0xACC7
; L7-F04  hidden 191 updates  figures L7-004, L7-028
        FLAG 0x37, 0xAC5B
; L7-F03  hidden 188 updates  figures L7-003, L7-007
        FLAG 0x37, 0xAC7F
; L7-F16  hidden 188 updates  figures L7-020, L7-027
        FLAG 0x37, 0xAC13
; L7-F21  hidden 186 updates  figures L7-026, L7-029
        FLAG 0x37, 0xAC37
; L7-F64  hidden 149 updates  figures L7-080, L7-094
        FLAG 0x37, 0xCB97
; L7-F97  hidden 86 updates  figures L7-132
        FLAG 0x37, 0xCF89
; L7-F96  hidden 81 updates  figures L7-131
        FLAG 0x37, 0xCC9E
; L7-F65  hidden 76 updates  figures L7-081, L7-093
        FLAG 0x37, 0xCBE8
; L7-F63  hidden 75 updates  figures L7-079, L7-095
        FLAG 0x37, 0xCB4E
; L7-F11  hidden 69 updates  figures L7-014   [off: explosion/shot]
;       FLAG 0x37, 0xB9A9
; L7-F95  hidden 65 updates  figures L7-130
        FLAG 0x37, 0xCC55
; L7-F25  hidden 56 updates  figures L7-033   [off: explosion/shot]
;       FLAG 0x37, 0xB32E
; L7-F20  hidden 51 updates  figures L7-025   [off: explosion/shot]
;       FLAG 0x37, 0xB05B
; L8-F47  hidden 190 updates  figures L8-070, L8-072
        FLAG 0x38, 0xC64D
; L8-F31  hidden 80 updates  figures L8-040, L8-051, L8-060, L8-073
        FLAG 0x38, 0xC844
; L8-F45  hidden 78 updates  figures L8-064, L8-068
        FLAG 0x38, 0xC779
; L8-F71  hidden 64 updates  figures L8-113   [off: explosion/shot]
;       FLAG 0x38, 0xB7AC
; L8-F70  hidden 62 updates  figures L8-112   [off: explosion/shot]
;       FLAG 0x38, 0xB6DB
; L8-F42  hidden 60 updates  figures L8-056, L8-058
        FLAG 0x38, 0xBBF2
; L8-F39  hidden 60 updates  figures L8-050, L8-053
        FLAG 0x38, 0xBB86
; L8-F41  hidden 59 updates  figures L8-055, L8-059
        FLAG 0x38, 0xBBBC
