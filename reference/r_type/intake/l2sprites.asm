; R-Type prototype step 2: l2scroll.asm plus figures as hardware sprites.
        DEFINE L2_SPRITES
        INCLUDE "l2scroll.asm"
        SAVEBIN "l2sprites_code.bin",hook_setup,$-hook_setup
