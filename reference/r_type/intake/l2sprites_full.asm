; R-Type prototype, whole game from the start snapshot: no mid-level start-up, so
; the title screens (which also call the copier) keep Layer 2 and sprites off.
        DEFINE L2_SPRITES
        IFNDEF L2_NOGLIDE
        DEFINE L2_GLIDE          ; figures glide between updates (glide.asm)
        ENDIF
        DEFINE L2_NOLAZY
        DEFINE L2_NOTAPE
        INCLUDE "l2scroll.asm"
        SAVEBIN "l2sprites_code.bin",hook_setup,$-hook_setup
        IFDEF L2_GLIDE
        INCLUDE "glide.asm"
        SAVEBIN "l2sprites_glide.bin",glide_start,glide_end-glide_start
        ENDIF
