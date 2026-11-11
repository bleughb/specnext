; Source lookup cached at successful inline plot blocks.
        DEFINE RT_INLINE
; Live per-pixel source-cell lookup, native bitmap fallback, exact cell credit.
        DEFINE RT_RESOLVED
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
        INCLUDE "resolved_render.asm"
        SAVEBIN "rtlive_lookup.bin",0x1000,$-0x1000

        ORG 0xC000
        INCLUDE "cell_resolve_code.asm"
        SAVEBIN "rtres_resolve.bin",0xC000,$-0xC000
