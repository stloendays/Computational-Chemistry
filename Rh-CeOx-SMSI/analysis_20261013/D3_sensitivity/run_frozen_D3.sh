#!/bin/bash
# D3(BJ)/PBE dispersion energy of converged Stage-4/5 structures at frozen geometry (= VASP IVDW = 12 without ATM)
set -u
module load Simple-DFTD3/1.2.1-gfbf-2023a >/dev/null 2>&1
B=/app1/ebapps/arches/flat-avx2/software/Simple-DFTD3/1.2.1-gfbf-2023a/bin/s-dftd3
W=/scratch/junbotong/Dynamic_SMSI_D3_sensitivity_20261013
S5=/scratch/junbotong/Dynamic_SMSI_stage5_cluster_layer_20260930/inputs
S4=/scratch/junbotong/Dynamic_SMSI_stage4_Ce4Ox_layers_20260928/inputs
mkdir -p $W/frozen && cd $W/frozen
declare -A P=(
 [R4]=$S5/R4_Rh111_4x4 [C3a]=$S5/C3a_Ce2O3_Rh_from12b [C3b]=$S5/C3b_Ce2O3_Rh_from12a
 [C4a]=$S5/C4a_Ce2O4_Rh_from10c [C4b]=$S5/C4b_Ce2O4_Rh_from12b_plusO [G3]=$S5/G3_Ce2O3_gas
 [G4]=$S5/G4_Ce2O4_gas [GO2]=$S5/GO2_O2_gas
 [L0]=$S4/L0_Rh111_3x3 [L6]=$S4/L6_Ce4O6_Rh [L7s]=$S4/L7s_Ce4O7_Rh_vacSurf [L7i]=$S4/L7i_Ce4O7_Rh_vacInt
 [L8]=$S4/L8_Ce4O8_Rh [F6]=$S4/F6_Ce4O6_free [F7s]=$S4/F7s_Ce4O7_free_vacSurf [F7i]=$S4/F7i_Ce4O7_free_vacInt
 [F8]=$S4/F8_Ce4O8_free [G_O2]=$S4/G_O2 )
for k in "${!P[@]}"; do
  mkdir -p $k; cp ${P[$k]}/CONTCAR $k/POSCAR
  sha=$(sha256sum ${P[$k]}/CONTCAR | cut -c1-16)
  ( cd $k && $B run --bj pbe -i vasp --json d3.json POSCAR > d3.out 2>&1 )
  e=$(python3 -c "import json;print(json.load(open('$k/d3.json'))['energy']*27.211386245988)" 2>/dev/null)
  echo "$k ${P[$k]} $sha $e"
done | sort > $W/frozen/E_D3_eV.txt
cat $W/frozen/E_D3_eV.txt
