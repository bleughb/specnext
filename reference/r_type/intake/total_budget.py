"""Whole-update ORIGINAL CPU ledger for the same bounded100-update peak cut.

This prices original work, not another renderer. It cannot close the patched
whole-hook budget without matching live phase measurements. No intake, caller,
capacity or ISR/access census; no memory read/write tracking or game-art output.
"""
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]/'nexclash'
sys.path[:0] = [str(ROOT)]
from nexclash import rzx
from identity_budget import WORK, FLIPS, instruction_cost


def cost(m, r):
    pc = r[24]
    if m[pc] == 0xED:
        op = m[pc+1]
        if op in (0xB0,0xB8,0xB1,0xB9,0xB2,0xBA,0xB3,0xBB):
            if op in (0xB2,0xBA,0xB3,0xBB):
                repeat = r[2] != 1
            else:
                repeat = r[2]*256+r[3] != 1
                if op in (0xB1,0xB9):
                    repeat = repeat and r[0] != m[r[6]*256+r[7]]
            return 21 if repeat else 16
    return instruction_cost(m,r)


def repeat_check():
    from skoolkit.simulator import Simulator
    n = 0
    for op in (0xB0,0xB8,0xB1,0xB9,0xB2,0xBA,0xB3,0xBB):
        for bc in (1,2,0x100,0x200):
            for equal in (False,True):
                m = bytearray(65536)
                m[0x8000:0x8002] = bytes([0xED,op])
                sim = Simulator(m)
                r = sim.registers
                r[0],r[2],r[3],r[4],r[6],r[24] = int(not equal),bc>>8,bc&255,0xA0,0x90,0x8000
                expected = cost(m,r)
                sim.opcodes[0xED]()
                assert r[25] == expected, (op,bc,equal,expected,r[25])
                n += 1
    return n


def run():
    cut = WORK/'peak.rzx'
    assert cut.exists(), 'Run identity_budget.py first to create the bounded cut'
    rows = []
    row = None
    irq = plot = background = False
    entries = 0

    class Done(Exception):
        pass

    def at(pc, sim):
        nonlocal row, irq, plot, background, entries
        r, m = sim.registers, sim.memory
        if pc == 0x8649:
            if row is not None:
                assert not irq and not plot and not background
                rows.append(row)
                if len(rows) == 100:
                    raise Done
            row = collections.Counter()
        if row is None:
            return
        if pc == 0x8383:
            assert not irq
            irq = True
            entries += 1
            row['IRQ'] += 19  # IM2 acceptance, not an instruction callback.
        if pc in FLIPS and not irq:
            assert not plot
            plot = True
        if pc == 0x8979 and not irq:
            background = True
        if pc == 0x8656 and not irq:
            background = False
        if irq:
            group = 'IRQ'
        elif plot:
            group = 'figure_plot'
        elif 0x8842 <= pc < 0x8881:
            group = 'copier_row_setup_and_attr_shift'
        elif 0x8881 <= pc < 0x88E6:
            group = 'copier_pixel_copy_clear_owner'
        elif 0x88E6 <= pc < 0x8979:
            group = 'copier_pixel_scroll'
        elif 0x8CD8 <= pc < 0x8CFD:
            group = 'native_attr_owner_map_shift'
        elif background:
            group = 'background_controller_other'
        elif 0x868C <= pc < 0x8696:
            group = 'wait_for_3_IRQs'
        else:
            group = 'remaining_game_work'
        row[group] += cost(m,r)
        if irq and pc == 0xBE5D:
            irq = False
        if plot and pc in (0x8D56,0x8DC4,0x8E1A,0x8E76) and r[1]&64:
            plot = False

    checks = repeat_check()
    try:
        frames, desync = rzx.trace(str(cut), range(65536), at)
    except Done:
        desync = None
    assert desync is None and len(rows) == 100, (len(rows),desync)
    totals = sum(rows,collections.Counter())
    identity = json.loads((HERE/'continuation/identity-budget.json').read_text())
    assert totals['figure_plot'] == identity['peak_totals']['original_plot_T']
    all_t = sum(totals.values())
    phases = {k:dict(total_T=v,mean_native_cpu_ms=v/3500/100,
        cpu_percent=100*v/all_t,
        max_update_native_cpu_ms=max(r[k] for r in rows)/3500)
        for k,v in sorted(totals.items())}
    result = dict(scope=__doc__, updates=100, IRQ_entries=entries,
        repeated_instruction_timing_cases=checks, phases=phases,
        total_mean_native_cpu_ms=all_t/3500/100,
        limitations=['RZX trajectory/IRQ schedule differs from natural JNext',
            'uncontended original3.5MHz CPU; not patched elapsed time or spare time',
            'current copier already accelerated; its native cost is not extra available savings',
            'phase maxima occur in different updates and must not be added',
            'remaining game work is unclassified, not presumed removable'],
        feasibility='Whole patched-route ledger remains incomplete; no further renderer/guard optimization gate passed')
    (HERE/'continuation/total-budget.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    run()
