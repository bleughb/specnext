; STATIC 4bpp sprite preparation/cost comparison; not live painting.
        DEFINE RT_MAX111
        DEFINE RT_PREPAINT
        DEFINE RT_FULL_LUT
        DEFINE RT_CELL
        DEFINE RT_CREDIT
        DEFINE RT_PACE
        DEFINE RT_POSTCLEAR
        DEFINE RT_MMU0_TEMP
        DEFINE RT_DYNAMIC
        DEFINE RT_INTEGRATED
        INCLUDE "publication_shadow.asm"
        SAVEBIN "rtprepaint_code.bin",entry,$-entry
