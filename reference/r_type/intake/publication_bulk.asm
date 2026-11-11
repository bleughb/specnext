; Whole-page ULA publication trial; unchanged HUD bytes required.
        DEFINE RT_BULKULA
; Feasibility alternative: hardware 1bpp text tiles, same visible figures and ULA.
        DEFINE RT_PACE
        DEFINE RT_TILEMAP
        DEFINE RT_POSTCLEAR
        DEFINE RT_MMU0_TEMP
        DEFINE RT_DYNAMIC
        DEFINE RT_INTEGRATED
        INCLUDE "publication_shadow.asm"
        SAVEBIN "rttilemap_code.bin",entry,$-entry
