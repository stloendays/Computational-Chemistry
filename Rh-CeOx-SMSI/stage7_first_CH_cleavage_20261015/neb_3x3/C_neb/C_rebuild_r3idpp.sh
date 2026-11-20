#!/usr/bin/env bash
# user 2026-11-20 "好滴，做吧": stop 1595966, archive the 0-Ce3+ band, rebuild NEB C from the IDPP band
# (build_neb.py, identical to the 11-06 run1 band) and seed as B r2: 01-03 C10, 04-06 C9 WAVECAR+CHGCAR, ISTART 1 / ICHARG 1.
set -uo pipefail
S=/scratch/junbotong/Dynamic_SMSI_stage7_first_CH_cleavage_20261015; N=$S/neb_3x3; IN=$S/inputs_3x3
IS=C10_CH4_toC9; FS=C9_CH3perimRh_HOp; NEW=$N/C_neb_idpp_upload; OLD=$N/C_neb; ARC=$N/C_neb_run2_0Ce3
die () { echo "ABORT: $*"; rmdir $S/monitor/lock 2>/dev/null; exit 1; }
test -d $NEW || die "upload missing"; test ! -e $ARC || die "$ARC exists"
# hold the monitor lock so no monitor run touches C while it has no job
for i in $(seq 1 30); do mkdir $S/monitor/lock 2>/dev/null && break; sleep 20; done
test -d $S/monitor/lock || die "lock"
qdel 1595966 2>&1
for i in $(seq 1 60); do st=$(qstat -x -f 1595966 2>/dev/null | awk '/job_state/{print $3}'); [ "$st" = F ] && break; sleep 10; done
[ "$st" = F ] || die "1595966 not finished ($st)"
if qstat -f -F json 2>/dev/null | grep -q "PBS_O_WORKDIR\":\"$OLD\""; then die "another job in C_neb"; fi
mv $OLD $ARC
mv $NEW $OLD; cd $OLD
cp -p $IN/$IS/POTCAR .
cp -p "$(ls -t $IN/$IS/OUTCAR_stageB_relax* | head -1)" 00/OUTCAR
cp -p "$(ls -t $IN/$FS/OUTCAR_stageB_relax* | head -1)" 07/OUTCAR
cp -p $ARC/neb_profile.py .
sed -e 's/^#PBS -N .*/#PBS -N s7neb_C_C10C9/' $N/B_neb/job_neb.pbs > job_neb.pbs
nb1=$(grep -m1 'NBANDS=' $IN/$IS/OUTCAR | awk '{print $NF}'); nb2=$(grep -m1 'NBANDS=' $IN/$FS/OUTCAR | awk '{print $NF}')
[ "$nb1" = "$nb2" ] || die "endpoint NBANDS differ $nb1 $nb2"
sed -i -e 's/^ISTART = .*/ISTART = 1/' -e 's/^ICHARG = .*/ICHARG = 1/' INCAR
sp=($(sed -n 6p 00/POSCAR)); nn=($(sed -n 7p 00/POSCAR)); mg=''
for i in "${!sp[@]}"; do v=0; [ "${sp[$i]}" = Ce ] && v=1; mg="$mg ${nn[$i]}*$v"; done
sed -i '/^MAGMOM/d;/^NBANDS/d' INCAR; printf 'NBANDS = %s\nMAGMOM =%s\n' "$nb1" "$mg" >> INCAR
for k in 01 02 03 04 05 06; do src=$IS; [ $k \> 03 ] && src=$FS
  cp $IN/$src/WAVECAR $IN/$src/CHGCAR $k/ || die "copy $k"
  cmp -n 1048576 $k/WAVECAR $IN/$src/WAVECAR && cmp $k/CHGCAR $IN/$src/CHGCAR || die "verify $k"
  echo "$k <- $src"; done
touch STAGEA_DONE
echo "== INCAR diff vs archived INCAR_neb"; diff $ARC/INCAR_neb.istart0_before_20261118 INCAR
d07=$(dist.pl 00/POSCAR 07/POSCAR | cut -c1-5); sp2=""; for k in 0 1 2 3 4 5 6; do sp2="$sp2 $(dist.pl 0$k/POSCAR 0$((k+1))/POSCAR | cut -c1-5)"; done
echo "dist.pl 00-07 $d07; spacing$sp2"
bash "$HOME/hpc_login.sh" > /dev/null 2>&1; hp=$(hpc project 2>&1); grep -q CFP04-CF-046 <<< "$hp" || die "allocation not visible"
j=$(qsub job_neb.pbs) || die "qsub"; echo "submitted $j"
echo "$(date +%Y-%m-%dT%H:%M:%S) [claude] neb_3x3/C_neb $j (s7neb_C_C10C9): rebuilt NEB C (user 11-20 \"好滴，做吧\"). 1595966 (endpoint WAVECAR, ICHARG 0, on the run-2 geometry) qdel'd after 10 h without an ionic step (01/04 NELM 300, 05/06 diverging at ~560 s per SCF step, moments falling from 2 toward 0-1); whole run-2 band archived as neb_3x3/C_neb_run2_0Ce3. New band = build_neb.py IDPP C10 -> C9 (identical to the 11-06 run1 band, max dev 0.0000 A); seeded as B r2: 01-03 C10, 04-06 C9 WAVECAR+CHGCAR, ISTART 1 / ICHARG 1, NBANDS $nb1, MAGMOM Ce 1; physics unchanged, no stage A; dist.pl 00-07 $d07 A, spacing$sp2" >> $S/SUBMISSION_stage7.txt
rmdir $S/monitor/lock
qstat -u junbotong | tail -4
