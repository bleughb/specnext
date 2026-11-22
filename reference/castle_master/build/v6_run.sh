#!/bin/sh
cd /c/1NEXT/castle_master_work
P=cm6
python m3_sim.py m0_states.bin 10 --prefix $P --show 1 --irq --pace --tween --prof v6_p.json > v6_sim10.log 2>&1; echo "sim10 $?" > v6_status.txt
python m3_sim.py m0_states.bin 50 --prefix $P --show 1 --irq --pace --tween --cursor 20 > v6_cur50.log 2>&1; echo "cursor50 $?" >> v6_status.txt
python m3_sim.py m0_states.bin 50 --prefix $P --show 1 --irq --pace --tween --intline 256 > v6_hdmi50.log 2>&1; echo "hdmi50 $?" >> v6_status.txt
python m3_sim.py m0_states.bin 50 --prefix $P --show 1 > v6_noirq50.log 2>&1; echo "noirq50 $?" >> v6_status.txt
python m3_sim.py m0_states.bin 50 --prefix $P --show 1 --irq --pace --tween --core 20 > v6_cpu50.log 2>&1; echo "oldcore50 $?" >> v6_status.txt
python -I m3b_seq.py --stop 30000 --prefix $P > v6_seq.log 2>&1; echo "seq $?" >> v6_status.txt
python m3b_diss.py 250 $P > v6_diss.log 2>&1; echo "diss $?" >> v6_status.txt
python m3b_diss.py 250 $P portc > v6_portc.log 2>&1; echo "portc $?" >> v6_status.txt
python m3b_race.py $P > v6_race.log 2>&1; echo "race $?" >> v6_status.txt
echo done >> v6_status.txt
