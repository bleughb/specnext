; R-Type prototype step 2: l2scroll.asm plus figures as hardware sprites.
        DEFINE L2_SPRITES
        IFNDEF L2_NOGLIDE
        DEFINE L2_GLIDE          ; figures glide between updates (glide.asm)
        ENDIF
        INCLUDE "l2scroll.asm"
        SAVEBIN "l2sprites_code.bin",hook_setup,$-hook_setup
        IFDEF L2_GLIDE
        INCLUDE "glide.asm"
        SAVEBIN "l2sprites_glide.bin",glide_start,glide_end-glide_start
        ENDIF
