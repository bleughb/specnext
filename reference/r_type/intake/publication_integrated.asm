; Early integrated diagnostic only. R proof, text hooks and full verify still open.
        DEFINE RT_DYNAMIC
        DEFINE RT_INTEGRATED
        INCLUDE "publication_shadow.asm"
        SAVEBIN "rtintegrated_code.bin",entry,$-entry
