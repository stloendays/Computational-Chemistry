#!/bin/bash
# Level-2 D3 sensitivity: re-relax Stage-4 layers with IVDW = 12 (only change), then the Stage-4 final-SP settings + IVDW = 12.
set -euo pipefail
S4=/scratch/junbotong/Dynamic_SMSI_stage4_Ce4Ox_layers_20260928/inputs
W=/scratch/junbotong/Dynamic_SMSI_D3_sensitivity_20261013/relax_D3
mkdir -p $W
for k in L6_Ce4O6_Rh L7i_Ce4O7_Rh_vacInt L8_Ce4O8_Rh; do
  d=$W/$k; mkdir -p $d; s=$S4/$k
  cp $s/CONTCAR $d/POSCAR; cp $s/KPOINTS $s/POTCAR $s/WAVECAR $s/CHGCAR $d/
  sed -e 's/| stageB_relax/| stageB_relax + D3(BJ) sensitivity/' $s/INCAR_stageB_relax > $d/INCAR_stageB_relax_D3
  printf 'IVDW = 12\n' >> $d/INCAR_stageB_relax_D3
  sed -e 's/| final_sp/| final_sp + D3(BJ) sensitivity/' $s/final_sp/INCAR_final_sp > $d/INCAR_final_sp_D3
  printf 'IVDW = 12\n' >> $d/INCAR_final_sp_D3
  sed -e "s/^#PBS -N .*/#PBS -N d3_${k:0:3}/" \
      -e 's/for f in INCAR_final_sp POSCAR/for f in INCAR_stageB_relax_D3 INCAR_final_sp_D3 POSCAR/' \
      -e 's/^run_stage final_sp LABORT scf$/run_stage stageB_relax_D3 LSTOP relax\ncp POSCAR POSCAR_start; cp CONTCAR POSCAR\nrun_stage final_sp_D3 LABORT scf/' \
      $s/final_sp/job.pbs > $d/job.pbs
  diff <(grep -v -e SYSTEM $s/INCAR_stageB_relax) <(grep -v -e SYSTEM $d/INCAR_stageB_relax_D3) | sed "s/^/$k relax diff: /" || true
  diff <(grep -v -e SYSTEM $s/final_sp/INCAR_final_sp) <(grep -v -e SYSTEM $d/INCAR_final_sp_D3) | sed "s/^/$k sp diff: /" || true
  sha256sum $s/CONTCAR $d/POSCAR | cut -c1-16
done
tail -6 $W/L6_Ce4O6_Rh/job.pbs; grep -E "^#PBS" $W/L6_Ce4O6_Rh/job.pbs
