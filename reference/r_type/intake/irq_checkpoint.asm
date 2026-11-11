; A nearly frame-long native IRQ can hide a whole wrap between renderer polls.
; Checkpoint the active timing window immediately before it, then advance only
; that window's anchors past held time. Never re-enter an interrupted timer helper.
rt_debt_tick:
        push af
        ld a,1
        ld (rt_timer_lock),a
        pop af
        call hlib_debt_tick
        ld a,0
        ld (rt_timer_lock),a
        ret
rt_nest_open:
        ld a,1
        ld (rt_timer_lock),a
        call hlib_nest_open
        ld a,1
        ld (rt_timer_kind),a
        ld a,0
        ld (rt_timer_lock),a
        ret
rt_nest_close:
        push af
        ld a,1
        ld (rt_timer_lock),a
        pop af
        call hlib_nest_close
        ld a,0
        ld (rt_timer_kind),a
        ld (rt_timer_lock),a
        ret
rt_irq_hold:
        ld a,0
        ld (irq_timer_kind),a
        ld a,(rt_timer_lock)
        or a
        jr nz,.plain
        ld a,(rt_timer_kind)
        cp 1
        jr z,.debt
        cp 2
        jr z,.window
.plain: jp hlib_pace_hold
.debt:  ld (irq_timer_kind),a
        call hlib_debt_tick
        jr .hold
.window:
        ld (irq_timer_kind),a
        call hlib_pace_tick
.hold:  ld hl,(HLIB_V_PACE+24)
        ld (irq_held_before),hl
        ld hl,(HLIB_V_PACE+22)
        ld (HLIB_V_PACE+16),hl
        ret
rt_irq_anchor:
        ld a,(irq_timer_kind)
        or a
        ret z
        ; Reuse the line sampled by pace_resume, without another hardware read.
        ld hl,(HLIB_V_PACE+14)
        ld de,(irq_held_before)
        or a
        sbc hl,de
        ld de,(HLIB_V_PACE+16)
        add hl,de
        ld de,NL
        or a
        sbc hl,de
        jr nc,.line
        add hl,de
.line:  ld de,(HLIB_V_PACE+14)
        ld a,(irq_timer_kind)
        cp 1
        jr nz,.window
        ld (HLIB_V_PACE+8),hl
        ld (HLIB_V_PACE+20),de
        ret
.window:
        ld (HLIB_V_PACE),hl
        ld (HLIB_V_PACE+18),de
        ret
rt_timer_kind: db 0
rt_timer_lock: db 0
irq_timer_kind: db 0
irq_held_before: dw 0
