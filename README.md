# specnext (PRIVATE) - nexclash maintainers' reference files

The toolkit lives in the PUBLIC repo **bleughb/nexclash** (GPL-3.0-or-later). This private repo
holds only what may not be published:
- reference/<game>/ - per game: the original snapshot and recordings the selftest verifies against,
  plus the built games (<game>.nex, <game>_sprites.nex); index + MD5s in reference/README.md,
- docs/reference/ - Next dev guide r3 (text) and the Next manual (OCR),
- docs/dean/ - Dean's prompts and Project instructions.

Self-test (maintainers): clone both side by side, then in nexclash/:
    python selftest.py              (finds ../specnext/reference; --fast skips Rainbow)
or set NEXCLASH_REFERENCE to this repo's reference/ folder.
