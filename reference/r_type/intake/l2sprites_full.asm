; R-Type prototype, whole game from the start snapshot: no mid-level start-up, so
; the title screens (which also call the copier) keep Layer 2 and sprites off.
        DEFINE L2_SPRITES
        DEFINE L2_NOLAZY
        DEFINE L2_NOTAPE
        INCLUDE "l2scroll.asm"
        SAVEBIN "l2sprites_code.bin",hook_setup,$-hook_setup
