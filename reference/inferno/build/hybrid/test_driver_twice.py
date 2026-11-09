"""The 8EF9 driver run twice on the same pages (restart after a game): second run must not hang and must equal the oracle.
From nexclash: python test_driver_twice.py [LEVEL]"""
import sys
from pathlib import Path
sys.path.insert(0, '.')
import nexclash.inferno as I
level = sys.argv[1] if len(sys.argv) > 1 else '1'
ref = Path('../specnext/reference/inferno')
ram, regs, frame = I.driver_boundary_state(ref / ('Inferno%s.rzx' % level))
expected = I.driver_expected(ram)
first = I.run_loading_driver(ram, regs)
pages = first['pages']
keep = I.driver_pages
I.driver_pages = lambda *a, **k: pages
second = I.run_loading_driver(ram, regs, limit=60_000_000)
I.driver_pages = keep
print(I.driver_compare(second, expected))
print(I.driver_index_compare(second, ram, expected))
print('ok: instructions', first['instructions'], second['instructions'], 'setup', pages[69][0x1EB4], 'error', pages[69][0x1EB3])
