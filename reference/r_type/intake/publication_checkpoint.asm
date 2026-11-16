; Bounded IRQ timing-checkpoint experiment.
        DEFINE RT_IRQ_CHECKPOINT
; Live per-pixel source-cell lookup, native bitmap fallback, exact cell credit.
        DEFINE RT_LIVEPAINT
        DEFINE RT_FULL_LUT
        DEFINE RT_CELL
        DEFINE RT_CREDIT
        DEFINE RT_PACE
        DEFINE RT_BULKULA
        DEFINE RT_POSTCLEAR
        DEFINE RT_MMU0_TEMP
        DEFINE RT_DYNAMIC
        DEFINE RT_INTEGRATED
        INCLUDE "publication_shadow.asm"
        SAVEBIN "rtlive_code.bin",entry,$-entry
        ORG 0x1000
        INCLUDE "live_lookup.asm"
        SAVEBIN "rtlive_lookup.bin",0x1000,$-0x1000
