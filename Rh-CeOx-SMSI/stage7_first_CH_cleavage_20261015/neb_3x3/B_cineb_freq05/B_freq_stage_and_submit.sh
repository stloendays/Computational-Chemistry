#!/usr/bin/env bash
# frequency check of CI-NEB B climbing image 05 (user 2026-11-20 "提交频率验证"); as A_cineb_freq05: C + 4H displaced
set -euo pipefail
N=/scratch/junbotong/Dynamic_SMSI_stage7_first_CH_cleavage_20261015/neb_3x3; S=$(dirname $N)
C=$N/B_cineb; D=$N/B_cineb_freq05
test ! -e $D || { echo "$D exists"; exit 1; }
grep -q "NEB converged" $C/s7ci_B_B5bB14.o1595539 || { echo "CI-NEB B not converged"; exit 1; }
mkdir $D; cd $D
cp -p $C/KPOINTS $C/POTCAR .
cp $C/05/WAVECAR WAVECAR
[ "$(stat -c %s WAVECAR)" = "$(stat -c %s $C/05/WAVECAR)" ] || { echo "WAVECAR size"; exit 1; }
# INCAR: CI-NEB INCAR without the NEB/relaxation tags, finite differences as A_cineb_freq05
grep -v -E '^(SYSTEM|IMAGES|SPRING|LCLIMB|ICHAIN|IOPT|EDIFFG|IBRION|POTIM|NSW|EDIFF|LWAVE|LCHARG) ' $C/INCAR > INCAR.tmp
{ echo "SYSTEM = Stage-7 B CI-NEB image 05 frequency (C + 4H displaced)"; cat INCAR.tmp
  printf 'EDIFF = 1E-7\nIBRION = 5\nNFREE = 2\nPOTIM = 0.015\nNSW = 1\nLWAVE = .FALSE.\nLCHARG = .FALSE.\n'; } > INCAR
rm INCAR.tmp
# POSCAR: image 05 CONTCAR, every atom fixed except C and H
python3 - $C/05/CONTCAR POSCAR <<'PY'
import sys
L = open(sys.argv[1]).read().splitlines()
syms, cnts = L[5].split(), [int(x) for x in L[6].split()]
i = 7
sel = L[i].strip().lower().startswith('s')
if sel: i += 1
out = L[:7] + ['Selective dynamics', L[i]]
k = 0
for s, n in zip(syms, cnts):
    for _ in range(n):
        xyz = L[i + 1 + k].split()[:3]
        f = 'T T T' if s in ('C', 'H') else 'F F F'
        out.append('  %s %s %s   %s' % (xyz[0], xyz[1], xyz[2], f)); k += 1
open(sys.argv[2], 'w').write('\n'.join(out) + '\n')
PY
sed -e 's/^#PBS -N .*/#PBS -N s7f_B05_freq/' $N/A_cineb_freq05/job.pbs > job.pbs
echo "== INCAR"; cat INCAR
echo "== free atoms: $(grep -c ' T T T$' POSCAR), fixed: $(grep -c ' F F F$' POSCAR)"
python3 - <<'PY'
a=open('POSCAR').read().splitlines(); b=open('/scratch/junbotong/Dynamic_SMSI_stage7_first_CH_cleavage_20261015/neb_3x3/B_cineb/05/CONTCAR').read().splitlines()
import itertools
n=sum(int(x) for x in a[6].split()); bad=0
for i in range(n):
    pa=[float(x) for x in a[9+i].split()[:3]]; pb=[float(x) for x in b[9+i].split()[:3]]
    bad+=max(abs(x-y) for x,y in zip(pa,pb))>1e-9
print('coords identical to CONTCAR:', bad==0, 'atoms', n)
PY
diff $N/A_cineb_freq05/job.pbs job.pbs || true
if qstat -f -F json 2>/dev/null | grep -q "PBS_O_WORKDIR\":\"$D\""; then echo "a job already uses this dir"; exit 1; fi
ok=0; for t in 1 2; do bash "$HOME/hpc_login.sh" > /dev/null 2>&1; hpc project | grep -q CFP04-CF-046 && { ok=1; break; }; done
[ $ok = 1 ] || { echo "allocation not visible"; exit 1; }
j=$(qsub job.pbs); echo "submitted $j"
echo "$(date +%Y-%m-%dT%H:%M:%S) [claude] neb_3x3/B_cineb_freq05 $j (s7f_B05_freq): frequency check of CI-NEB B climbing image 05 (user 11-20 \"提交频率验证\"), as A_cineb_freq05: POSCAR = B_cineb/05/CONTCAR, C + 4H displaced (T), Rh/Ce/O fixed; IBRION 5, NFREE 2, POTIM 0.015, NSW 1, EDIFF 1E-7; physics as the CI-NEB (PBE+U Ce 5 eV, ENCUT 450, ISPIN 2, ISMEAR 1/0.10, k 4x4x1, NBANDS 276); ISTART 1 from 05/WAVECAR; 1 node 36 cores, 72 h, LABORT watchdog 250200 s. Image 05 geometry: C-H51 3.50 A (H on O46 0.97 A), CH3 on Ce40 2.67 A moving to O44 (C-O 3.00 A; 1.53 A in image 06)." >> $S/SUBMISSION_stage7.txt
