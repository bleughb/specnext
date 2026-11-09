"""Does Inferno use FLASH? Per level: actor images with a FLASH tile at the 8EF9 table, draws using one in sampled gameplay
updates, and scenery cells with FLASH in those updates. From nexclash: python probe_flash.py LEVEL CACHE_PREFIX"""
import json
import pickle
import sys
from pathlib import Path
sys.path.insert(0, '.')
import nexclash.inferno as I

level, cache = sys.argv[1], sys.argv[2]
ref = Path('../specnext/reference/inferno')
ram, regs, frame = I.driver_boundary_state(ref / ('Inferno%s.rzx' % level))
images = flash_images = 0
flashing = set()
for image, e in enumerate(I.driver_expected(ram)):
    if e in (None, 'reject'):
        continue
    images += 1
    if any(ram[0xFC00 + t] & 0x80 for x, y, t in I.actor_descriptor(ram, image)['tiles']):
        flash_images += 1
        flashing.add(image)
states = pickle.loads(open('%s.%s' % (cache, level), 'rb').read())[0x8F7C]
store = I._cw_store(str(ref), level, cache)
patch = I.CopierWindowPatch(work=True)
draws = flash_draws = updates = scenery = scenery_updates = 0
for k in range(0, len(states), 8):
    m, r, port = states[k]
    res = I.run_cw_window(patch, m, r, phase=0, count0=0, store=store)
    p68 = res['dx'][2]
    if p68[0x3F5]:
        continue
    updates += 1
    for rec in I.capture_log(p68):
        draws += 1
        flash_draws += any(m[0xFC00 + t] & 0x80 for x, y, t in rec['tiles'])
    cells = sum(1 for y in range(18) for x in range(32) if m[0xFC00 + (m[0x9B00 + 64 * y + 2 * x] | (m[0x9B01 + 64 * y + 2 * x] & 3) << 8)] & 0x80)
    scenery += cells
    scenery_updates += cells > 0
print(json.dumps(dict(level=level, images=images, images_with_flash=flash_images, sampled_updates=updates, draws=draws, draws_with_flash=flash_draws,
                      scenery_flash_cells=scenery, updates_with_scenery_flash=scenery_updates)))
