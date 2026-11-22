#!/bin/sh
cd /c/1NEXT/castle_master_work
python m3_sim.py m0_states.bin 50 --prefix cm7 --noasm --show 1 --irq --pace --tween --cursor 20 > v7_cur50b.log 2>&1; echo "cursor50b $?" > v7_full_status.txt
python m3_sim.py m0_states.bin 1 --prefix cm7 --noasm --show 1 --irq --pace --tween > v7_all.log 2>&1; echo "all $?" >> v7_full_status.txt
echo done >> v7_full_status.txt
