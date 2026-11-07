# Inferno high SRAM DDMA staging — 2026-11-07

The standalone page-77 adapter now supports expanded staging pages 216–223 in addition to
112–115 / 118–121. Source pages remain 112–115 or 136–223. These eight high pages are reserved
for exclusively owned inactive staging, reducing proposed general cache space to 136–215.
No allocator, game hook or sprite display is installed. Callers must never supply a current,
pending or pinned allocation as writable staging. Hardware pattern current/pending guards remain.

On gated core 3.03+ with exclusive DMA ownership and no hardware-IM2 hazard, high-source to
high-staging rectangles use physical SRAM addresses: 040000 + page*2000 + offset. This includes
the SRAM aperture offset; treating page*2000 alone as physical is wrong. Page 223's final byte is
1FFFFF, within the authorized 2 MiB machine. Firmware, BRAM screen aliases, pages >=224, equal
source/destination pages, out-of-page extents and intermediate cache destinations are rejected.
The packet sets both extended address bytes and the full physical/2D flags, then loads/enables.
Physical transfer bypasses destination MMU mapping; the source mapping used during shared backend
initialization is still restored. It is not an asynchronous preparation or interrupt-safety proof.

Default prefer-blitter policy 2 retains this new route; policy 1 uses ordinary row DMA through
stable mappings, and policy 0 uses CPU. Old/unknown cores, unowned DMA and hardware IM2 fall back.
Small single spans still use CPU before setup; narrow row DMA still uses CPU. No interrupt masks
are changed. Low-memory destinations retain their existing virtual-DDMA route. No shared library
code or DMA device model was changed; this is a private independently written packet using the
existing strict model's physical-memory interface.

36 high-address exact-end capability/policy/fallback cases, three strided gap cases, same-page
refusal, five high-aperture rejects, and a deliberately broken extended-address command pass.
The physical oracle permits reads only from the supplied owned high source and writes only to
the supplied high staging page. Existing 27 span probes, 12 current/pending pattern protections,
bounds and wrong-stride/pending-overwrite controls also pass.

A prepared 256-byte x 16-row (4096-byte) copy takes about 3.74 ms via CPU, 0.514 ms ordinary-DMA
CPU setup, or 0.165 ms physical-DDMA CPU setup, including adapter checks and address conversion.
Physical stalls are UNKNOWN. These are standalone component instruction timings, not elapsed
hardware measurements. Against the 10 ms TOTAL added-work budget, the CPU route alone consumes
about 37%; DDMA's 0.165 ms excludes transfer time and the rest of the pipeline. No total timing
pass: the last snapshot-inclusive cold totals remain L1 899.447 / L6 84.289 ms. DMA cannot replace
exact live validation, colour expansion or B connectivity. Physical copies move owned prepared
bytes; they do not make mutable live sources immutable across yields.

Reproduce from nexclash with the bundled assembler:

```bash
python tools/asm2profile.py --check inferno
python -m nexclash.inferno --actor-blit-checks --json work/actor_high_dma_checks.json
python -m nexclash.inferno --actor-pack-check ../specnext/reference/inferno/Inferno6.rzx --quick 2000 --json work/actor_high_dma6.json
python tools/doccheck.py
```

The level-6 original replay is a regression check of the existing pinned B/frame components;
it does not invoke the new high-SRAM adapter. High transfers are assembled synthetic checks.
Runtime integration, ownership/IRQ proof, physical board timings, FLASH/modal/frontend/ROM
lifetime/recolour and complete-frame switching remain open. Sprite display remains disabled.
Protocol facts: docs/reference/zxnDDMA_guide.txt (physical addresses/mode flags); nexclash
asm/lib/hlib_dma.asm and docs/DDMA_IMPLEMENTATION.md. No guide example code copied.
