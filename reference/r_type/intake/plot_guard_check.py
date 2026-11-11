"""Assembled packed-plot guard: source mutations, ABI and exact CPU budget.

Tests the identity component proposed for a combined faster original/hardware
writer. No renderer, native-R restoration, interrupts, pace or hardware proof.
Input geometry/dispatch is a host model, not an implemented runtime dispatcher.
"""
import gzip
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3] / 'nexclash'
sys.path[:0] = [str(ROOT), str(ROOT/'tools')]
from asm2profile import assemble, sjasm
from skoolkit.simulator import Simulator
from identity_budget import packed


def execute(code, data, live, seed=0, zero=False, negative=False):
    memory = bytearray(65536)
    memory[0x2000:0x2000+len(code)] = code
    memory[0x4000:0x4000+len(data)] = data
    memory[0xA000:0xA000+len(live)] = live
    memory[0x9F00:0x9F02] = b'\x00\x1F'
    sim = Simulator(memory)
    r = sim.registers
    r[2:8] = [0 if zero else len(data)>>8, 0 if zero else len(data)&255,
              0x40, 0, 0xA0, 0]
    r[12], r[15], r[24] = 0x9F00, seed, 0x2000
    initial = r[:]
    if negative:
        # Mutate the actual runtime CP (HL), making changed artwork compare equal.
        offset = code.index(bytes([0x1A,0xBE]))+1
        memory[0x2000+offset] = 0xBF  # CP A
    before = bytes(memory)
    steps = 0
    while r[24] != 0x1F00:
        sim.opcodes[memory[r[24]]]()
        steps += 1
        assert steps < 200000
    assert r[2:8] == initial[2:8] and r[12] == 0x9F02
    assert bytes(memory[0x4000:0x4000+len(data)]) == data
    assert bytes(memory[0xA000:0xA000+len(live)]) == live
    # Apart from dead stack bytes, the kernel writes no RAM.
    assert memory[:0x9EFA] == before[:0x9EFA] and memory[0x9F00:] == before[0x9F00:]
    return bool(r[1]&1), r[25]


def run():
    blocks, symbols = assemble(str(HERE/'plot_guard.asm'), sjasm.find())
    assert symbols['plot_guard'] == 0x2000
    code = blocks['code']
    corpus = json.loads(gzip.decompress((HERE/'continuation/assets.json.gz').read_bytes()))
    unique = {packed(p,corpus['cells']) for p in corpus['plots'].values()}
    hits = misses = 0
    for data in sorted(unique):
        accepted, cycles = execute(code,data,data)
        assert accepted and cycles == 59*len(data)+100, (len(data),cycles)
        hits += 1
        # First/last plus marker/attribute and pixel interiors, including >255B.
        for index in sorted({0,len(data)//2,len(data)-1}):
            changed = bytearray(data)
            changed[index] ^= 1
            accepted, cycles = execute(code,data,bytes(changed))
            assert not accepted, (len(data),index)
            assert cycles <= 59*len(data)+100
            misses += 1
    # Zero-length dispatch cannot accidentally authorize an unknown plot.
    assert not execute(code,b'x',b'x',zero=True)[0]
    # Counter rollover/high bit is not an ABI claim: R is deliberately clobbered.
    for seed in (0,127,128,255):
        assert execute(code,bytes(300),bytes(300),seed=seed)[0]
    broken = execute(code,b'\x01\x02',b'\x01\x03',negative=True)[0]
    assert broken, 'actual-runtime negative did not demonstrate false acceptance'
    budget = json.loads((HERE/'continuation/identity-budget.json').read_text())
    totals, est = budget['peak_totals'], budget['estimates']
    # Replace the estimated 49T/byte guard by measured 59T/byte+100T hit,
    # plus its caller CALL. The earlier 600T/plot setup and 80T/ID remain estimates.
    extra = (10*totals['known_packed_bytes'] + 117*totals['known_plots'])/28000/100
    combined = est['combined_writer_estimated_net_ms_per_update']-extra
    required = est['required_saving_ms_per_update']
    result = dict(scope=__doc__, assembler='bundled sjasmplus1.24.0',
        matching_packed_images=hits, changed_source_cases_rejected=misses,
        zero_length_rejected=True, actual_runtime_false_acceptance_control_caught=True,
        hit_cpu_T='59*packed_length+100, caller CALL excluded',
        corpus_max_packed_length=max(map(len,unique)),
        combined_estimated_net_ms_per_update=combined,
        required_saving_ms_per_update=required,
        illustrative_residual_ms_per_update=combined-required,
        decision='comparison component passes; whole-route budget unresolved, no implementation gate passed',
        pending=['complete whole-route cost and consumer ledger before further implementation',
                 'runtime dispatch and lifetime/ownership invalidation',
                 'exact combined-writer credit including all wrapper/accounting costs',
                 'ABI/R/IRQ/painted RGB and pause/menu/DI',
                 'JNext live painted100-update peak <=2%, private SD image required'])
    (HERE/'continuation/plot-guard-check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    run()
