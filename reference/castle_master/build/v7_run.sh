#!/bin/sh
cd /c/1NEXT/castle_master_work
P=cm7
python m3_sim.py m0_states.bin 10 --prefix $P --show 1 --irq --pace --tween --prof v7_p.json > v7_sim10.log 2>&1; echo "sim10 $?" > v7_status.txt
python m3_sim.py m0_states.bin 50 --prefix $P --show 1 --irq --pace --tween --cursor 20 > v7_cur50.log 2>&1; echo "cursor50 $?" >> v7_status.txt
python m3_sim.py m0_states.bin 50 --prefix $P --show 1 --irq --pace --tween --intline 256 > v7_hdmi50.log 2>&1; echo "hdmi50 $?" >> v7_status.txt
python m3_sim.py m0_states.bin 50 --prefix $P --show 1 > v7_noirq50.log 2>&1; echo "noirq50 $?" >> v7_status.txt
python m3_sim.py m0_states.bin 50 --prefix $P --show 1 --irq --pace --tween --core 20 > v7_cpu50.log 2>&1; echo "oldcore50 $?" >> v7_status.txt
python -I m3b_seq.py --stop 30000 --prefix $P > v7_seq.log 2>&1; echo "seq $?" >> v7_status.txt
python m3b_diss.py 250 $P > v7_diss.log 2>&1; echo "diss $?" >> v7_status.txt
python m3b_diss.py 250 $P portc > v7_portc.log 2>&1; echo "portc $?" >> v7_status.txt
python m3b_race.py $P > v7_race.log 2>&1; echo "race $?" >> v7_status.txt
echo done >> v7_status.txt
