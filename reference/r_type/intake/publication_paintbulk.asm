; Whole-page ULA publication trial; unchanged HUD bytes required.
        DEFINE RT_BULKULA
; STATIC texture cost/RGB stress, NOT live painting or engine output.
        DEFINE RT_PAINT
; Cell provenance/row acceleration experiment, not the default.
        DEFINE RT_CREDIT
        DEFINE RT_CELL
; Feasibility alternative: hardware 1bpp text tiles, same visible figures and ULA.
        DEFINE RT_PACE
        DEFINE RT_TILEMAP
        DEFINE RT_POSTCLEAR
        DEFINE RT_MMU0_TEMP
        DEFINE RT_DYNAMIC
        DEFINE RT_INTEGRATED
        INCLUDE "publication_shadow.asm"
        SAVEBIN "rttilemap_code.bin",entry,$-entry

        ORG 0xC000
        INCLUDE "paint_stress.asm"
        SAVEBIN "rtpaint_paint.bin",0xC000,$-0xC000
