; Early integrated diagnostic only. R proof, text hooks and full verify still open.
        DEFINE RT_FULL_LUT
        DEFINE RT_POSTCLEAR
        DEFINE RT_MMU0_TEMP
        DEFINE RT_DYNAMIC
        DEFINE RT_INTEGRATED
        INCLUDE "publication_shadow.asm"
        SAVEBIN "rtintegrated_code.bin",entry,$-entry
