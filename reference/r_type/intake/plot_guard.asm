; Bounded combined-writer component, not an integrated renderer.
; HL=live packed source, DE=reconstructed expected packed source, BC=length.
; Caller dispatch must first validate level/address/dimensions/bank and bounds.
; Checks attributes and transparent markers as well as every pixel byte.
; Returns carry=exact match; zero length/any mismatch returns carry clear.
; BC/DE/HL preserved. AF/R change; whole-plot wrapper must account for them.
; Uninterrupted hit: 59*length+100 CPU T, excluding caller CALL.
        DEVICE ZXSPECTRUMNEXT
        ORG 0x2000
plot_guard:
        push bc
        push de
        push hl
        ld a,b
        or c
        jp z,.miss
.loop: ld a,(de)
        cp (hl)
        jr nz,.miss
        inc de
        inc hl
        dec bc
        ld a,b
        or c
        jr nz,.loop
        scf
        jp .restore
.miss: or a
.restore:
        pop hl
        pop de
        pop bc
        ret
        SAVEBIN "rtguard_code.bin",plot_guard,$-plot_guard
