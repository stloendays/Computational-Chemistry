#!/usr/bin/env bash
# stage the B CI-NEB from the converged ordinary NEB 1580815 and submit; user 2026-11-20 "投 B 的 CI-NEB"
set -euo pipefail
N=/scratch/junbotong/Dynamic_SMSI_stage7_first_CH_cleavage_20261015/neb_3x3; S=$(dirname $N)
O=$N/B_neb; D=$N/B_cineb
test ! -e $D || { echo "$D already exists"; exit 1; }
grep -q "NEB converged" $O/s7neb_B_B5bB14.o1580815 || { echo "ordinary NEB B not converged"; exit 1; }
if qstat -f -F json 2>/dev/null | grep -q "PBS_O_WORKDIR\":\"$O\""; then echo "a job still uses B_neb"; exit 1; fi
mkdir -p $D; cd $D
for k in 00 01 02 03 04 05 06 07; do mkdir $k; done
cp -p $O/KPOINTS $O/POTCAR $O/neb_profile.py .
cp -p $O/INCAR INCAR_source_ordinary
sed -e 's/^SYSTEM = .*/SYSTEM = Stage-7 CI-NEB B: B5b_CH4_toB4_fromB2 -> B14_CH3O43_HO45_fromB5b/' \
    -e 's/^ISTART = .*/ISTART = 1/' -e 's/^ICHARG = .*/ICHARG = 0/' -e 's/^LCLIMB = .*/LCLIMB = .TRUE./' \
    INCAR_source_ordinary > INCAR
sed -e 's/^#PBS -N .*/#PBS -N s7ci_B_B5bB14/' $N/A_cineb/job_neb.pbs > job_neb.pbs
for k in 00 07; do cp -p $O/$k/POSCAR $O/$k/OUTCAR $k/; done
for k in 01 02 03 04 05 06; do
  cp -p $O/$k/CONTCAR $k/POSCAR
  cp $O/$k/WAVECAR $k/WAVECAR
  [ "$(stat -c %s $k/WAVECAR)" = "$(stat -c %s $O/$k/WAVECAR)" ] || { echo "WAVECAR $k size"; exit 1; }
done
echo "== INCAR diff vs ordinary"; diff INCAR_source_ordinary INCAR || true
echo "== job diff vs A_ci"; diff $N/A_cineb/job_neb.pbs job_neb.pbs || true
echo "== final magnetisation of ordinary images (tot)"
for k in 01 02 03 04 05 06; do printf '%s %s\n' $k "$(grep 'number of electron' $O/$k/OUTCAR | tail -1 | awk '{print $NF}')"; done
d07=$(dist.pl 00/POSCAR 07/POSCAR | cut -c1-5); echo "dist.pl 00-07 $d07"
sp=""; for k in 0 1 2 3 4 5 6; do sp="$sp $(dist.pl 0$k/POSCAR 0$((k+1))/POSCAR | cut -c1-5)"; done; echo "spacing$sp"
bash "$HOME/hpc_login.sh" > /dev/null 2>&1; hpc project | grep -q CFP04-CF-046 || { echo "allocation not visible"; exit 1; }
j=$(qsub job_neb.pbs); echo "submitted $j"
echo "$(date +%Y-%m-%dT%H:%M:%S) [claude] neb_3x3/B_cineb $j: CI-NEB B5b -> B14 (user 11-20 \"投 B 的 CI-NEB\"); from the converged ordinary NEB 1580815 (53 steps, Fmax 0.042, highest image 05 +1.356 eV, plateau 03-05 +1.31..+1.36); 01-06 POSCAR = ordinary CONTCAR, own WAVECARs, ISTART 1 / ICHARG 0, LCLIMB .TRUE., rest as the ordinary INCAR (ALGO Normal, NBANDS 276, MAGMOM Ce 1); dist.pl 00-07 $d07 A, spacing$sp" >> $S/SUBMISSION_stage7.txt
