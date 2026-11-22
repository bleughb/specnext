# Castle Master .nxc, version 1.1 (m3d_08): run from castle_master_work. Output: nxc_out_1.1/
set -e
export NXC_ZX0_DIR='C:\1NEXT\castle_master_work\zx0bin'
N=/c/1NEXT/nxc/tools/nxc.py
F="Castle Master (1990)(Incentive)"
T="nxc_out/$F/Castlemaster1.tap"
O="nxc_out_1.1/$F"
mkdir -p "$O"; rm -f cm_a.nxc cm_b.nxc cm_c.nxc cm_d.nxc
python $N make castle_master_m3d_08.nex "$T" --start castle_master.z80 -o cm_a.nxc --title "Castle Master" --publisher "Incentive, 1990" --patch-by "Bleugh" --patch-version 1.1 --rom 2 --file "$F.tap" --fix-label "Colour and smooth views" --toggle "Original colours=castle_master_m3d_08_original.nex" \
 --proof "replay=every view of 524 sampled screen updates of one recording equal per pixel to a model of the original's renderer; the game's own RAM and registers equal at each; all 18 dissolve views" --proof replay_when=2026-11-22 \
 --proof "emulator=CSpect 4.5.9: loading screen, menu, walk to the castle (version 1.0's build, which differs only in holding the loading screen)" --proof emulator_when=2026-11-22 \
 --proof "hardware=ZX Spectrum Next (owner's): loaded from this patch through the loader's build screen and played; Original colours seen in version 1.0" --proof hardware_when=2026-11-22 \
 --proof "coverage=one recording (5,233 updates); neither cheat played" --proof coverage_when=2026-11-22 \
 --proof pace=ORIGINAL --proof "pace_measured=screen updates of the recording: +5%" --proof "pace_where=NexClash simulator" --proof pace_when=2026-11-22 | tail -2
python $N import-pok cm_a.nxc cm_cheats.pok "$T" -o cm_b.nxc | tail -1
python $N help cm_b.nxc "$T" -o cm_c.nxc --line "fix=Colour views, more of them a second, at the original's pace." --line "toggle_1=The original's two colours, still with the smooth views." --line "trainer_1=Strength no longer drains with time." --line "trainer_2=From The Tipshop; not played." | tail -1
python $N set cm_c.nxc "$T" notes "Not a sprite build: the 3D view is redrawn by a Next renderer on Layer 2, each surface in its own colour with the original's dither kept, and extra in-between views make movement smoother while the game keeps its own pace. The sight, pointer and messages are sprites over the view. The original loading screen shows from ENTER while the loader builds the game. Original colours on the menu gives the game's own two colours with the smooth views. Keys as the original." -o cm_d.nxc | tail -1
python $N set cm_d.nxc "$T" changes "1.1: the loading screen shows from ENTER while the game is built, with Patching and a dot for each bank, and is no longer held 4 seconds" -o cm_c.nxc | tail -1
python $N set cm_c.nxc "$T" build_screen 513 -o "$O/$F.nxc" | tail -1
python /c/1NEXT/nxc/tools/make_nfo.py "$O/$F.nxc" | tail -1
python $N "$O/$F.nxc" "$T" -o cm_check_default.nex --bare | tail -1
cmp cm_check_default.nex castle_master_m3d_08.nex && echo "default = m3d_08"
