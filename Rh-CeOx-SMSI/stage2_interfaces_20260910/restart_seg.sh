#!/usr/bin/env bash
# restart_seg.sh <system_dir> : continue a watchdog-stopped relaxation from CONTCAR/WAVECAR as a new PBS segment
set -eu
d=$1; cd "$d"
[ -s CONTCAR ] || { echo "no CONTCAR in $d" >&2; exit 2; }
n=$(ls -d seg[0-9]* 2>/dev/null | wc -l || true); seg=seg$(printf "%02d" $((n+1)))_$(date +%Y%m%d_%H%M)
mkdir -p "$seg"; cp -f OUTCAR OSZICAR vasp.out CONTCAR XDATCAR "$seg"/ 2>/dev/null || true; mv -f s2_*.o* "$seg"/ 2>/dev/null || true
[ -f OSZICAR_stage1 ] && mv -f OUTCAR_stage1 OSZICAR_stage1 vasp_stage1.out "$seg"/ 2>/dev/null || true
cp -f CONTCAR POSCAR
sed -i -e "s/^#PBS -l walltime=.*/#PBS -l walltime=48:00:00/" -e "s/^  sleep [0-9]*$/  sleep 163800/" job.pbs
sed -i -e "s/^ISTART = .*/ISTART = 1/" -e "s/^ICHARG = .*/ICHARG = 1/" INCAR
python3 - <<PY
s=open("job.pbs").read()
if "cp INCAR_stage1_nospin INCAR" in s:
    a=s.index("cp INCAR_stage1_nospin INCAR"); b=s.index("mpirun -np \"\$NP\" \"\$VASP_BIN\" > vasp.out &"); s=s[:a]+s[b:]
open("job.pbs","w").write(s)
PY
if id=$(qsub job.pbs 2>/dev/null); then echo "$d $seg restart $id" | tee -a ../SUBMISSION_restarts.txt; else echo "$d" >> ../PENDING_RESUBMIT.txt; echo "$d prepared; qsub refused (queue disabled) -> PENDING_RESUBMIT.txt"; fi
