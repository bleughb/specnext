; Dynamic experiment extends the shared staged publication, no engine installed.
        DEFINE RT_FULL_LUT
        DEFINE RT_MMU0_TEMP
        DEFINE RT_DYNAMIC
        INCLUDE "publication_shadow.asm"
        SAVEBIN "rtdynamic_code.bin",entry,$-entry
