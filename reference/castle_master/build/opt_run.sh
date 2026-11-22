#!/bin/sh
# opt_run.sh TAG [EVERY] [TOP] [PREFIX]: assemble ${4:-cm6}, sampled sim with profile, report
cd /c/1NEXT/castle_master_work
python -c "from m2_lib import assemble; assemble('${4:-cm6}')" || exit 1
python m3_sim.py m0_states.bin ${2:-50} --prefix ${4:-cm6} --show 1 --irq --pace --tween --prof p${4:-cm6}$1.json > p${4:-cm6}$1.log 2>&1
echo "exit $? FAILED lines: $(grep -c FAILED p${4:-cm6}$1.log)"
grep -i "FAILED" p${4:-cm6}$1.log | head -5 | cut -c1-200
python m3_calls.py p${4:-cm6}$1.json ${4:-cm6} ${3:-14}
