#!/usr/bin/env bash
# 2026-11-14 [claude-cli] NEB B r2: 1553237 (ALGO All, ISTART 0) stalled - no OSZICAR update since 17:21, first ionic
# step never finished (01/03/04 at NELM 300, 05/06 CGA diverging); PBS server unresponsive. When PBS returns: if the job
# is still R and its OSZICARs are fresh (<60 min) leave it; otherwise qdel and resubmit the same images with each image
# reading an endpoint WAVECAR+CHGCAR (01-03 <- B5b, 04-06 <- B14; the endpoints themselves converged with ISTART 1/ICHARG 1),
# ALGO Normal (11-07 lesson: ALGO All + WAVECAR diverges), NBANDS 276 = endpoint value. Physics otherwise unchanged.
S=/scratch/junbotong/Dynamic_SMSI_stage7_first_CH_cleavage_20261015
D=$S/neb_3x3/B_neb; LOCK=$S/monitor/lock; OLD=1553237
E1=$S/inputs_3x3/B5b_CH4_toB4_fromB2; E2=$S/inputs_3x3/B14_CH3O43_HO45_fromB5b
log(){ echo "$(date +%F_%T) $*"; }
cd "$D" || exit 1
for k in $(seq 1 4320); do timeout 90 qstat -u junbotong >/dev/null 2>&1 && break; sleep 60; done
timeout 90 qstat -u junbotong >/dev/null 2>&1 || { log "PBS still down after 72 h, giving up"; exit 1; }
log "PBS back"
for k in $(seq 1 120); do mkdir "$LOCK" 2>/dev/null && break; sleep 15; done
[ -d "$LOCK" ] || { log "no lock"; exit 1; }
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
qstat -u junbotong
ST=$(qstat -f $OLD 2>/dev/null | awk '/job_state/{print $3}')
NEWEST=$(stat -c %Y 0[1-6]/OSZICAR | sort -n | tail -1); AGE=$(( $(date +%s) - NEWEST ))
log "job $OLD state=${ST:-gone} newest OSZICAR age ${AGE}s"
if [ "$ST" = R ] && [ $AGE -lt 3600 ]; then log "job alive and writing - leave it"; exit 0; fi
if [ -n "$ST" ] && [ "$ST" != F ]; then qdel $OLD; log "qdel $OLD"; fi
for k in $(seq 1 60); do s=$(qstat -f $OLD 2>/dev/null | awk '/job_state/{print $3}'); [ -z "$s" -o "$s" = F ] && break; sleep 10; done
if qstat -u junbotong 2>/dev/null | grep -q "s7neb_B"; then log "a B NEB job is still live, not resubmitting"; qstat -u junbotong; exit 1; fi
sleep 20
for i in 01 02 03 04 05 06; do (cd $i && for f in POSCAR CONTCAR OUTCAR OSZICAR WAVECAR CHGCAR vasprun.xml XDATCAR; do [ -e $f ] && mv $f ${f}_before_r2_algoAll; done; cp -p POSCAR_before_r2_algoAll POSCAR); done
[ -e vasp_neb.out ] && mv vasp_neb.out vasp_neb.out_before_r2_algoAll
for i in 01 02 03; do cp $E1/WAVECAR $E1/CHGCAR $i/ || { log "copy failed $i"; exit 1; }; done
for i in 04 05 06; do cp $E2/WAVECAR $E2/CHGCAR $i/ || { log "copy failed $i"; exit 1; }; done
cp -p INCAR INCAR_before_r2_algoAll
sed -i -e 's/^ALGO = All$/ALGO = Normal/' -e 's/^ISTART = 0$/ISTART = 1/' -e 's/^ICHARG = 2$/ICHARG = 1/' INCAR
grep -q '^NBANDS' INCAR || sed -i 's/^NELM = 300$/NELM = 300\nNBANDS = 276/' INCAR
grep -q '^ALGO = Normal$' INCAR && grep -q '^ISTART = 1$' INCAR && grep -q '^ICHARG = 1$' INCAR && grep -q '^NBANDS = 276$' INCAR || { log "INCAR edit failed"; exit 1; }
cp -p INCAR INCAR_neb_r2
touch STAGEA_DONE
J=$(qsub job_neb.pbs) || { log "qsub failed: $J"; exit 1; }
log "qsub $J"
python3 - "$J" <<'PY'
import json,sys,shutil
p='/scratch/junbotong/Dynamic_SMSI_stage7_first_CH_cleavage_20261015/monitor/state.json'
shutil.copy(p,p+'.bak_20261114_nebB_r2')
s=json.load(open(p)); b=s['neb']['B']
b['jid']=sys.argv[1].split('.')[0]; b['phase']='run'; b['auto_n']=2
b['run_r1']='1553237 ALGO All ISTART 0, stalled in first ionic step (PBS outage 11-14)'
json.dump(s,open(p,'w'),indent=1)
PY
echo "$(date +%Y-%m-%dT%H:%M:%S) [claude-cli] neb_3x3/B_neb r2 $J (s7neb_B_B5bB14): 1553237 (ALGO All, ISTART 0) stalled - OSZICAR frozen since 11-14 17:21 in the first ionic step (01/03/04 NELM 300 unconverged, 05/06 CGA diverging), PBS was down; qdel/ended -> same IDPP images (POSCAR unchanged; outputs kept as *_before_r2_algoAll), images 01-03 read B5b WAVECAR+CHGCAR, 04-06 read B14 WAVECAR+CHGCAR, ISTART 1 / ICHARG 1, ALGO Normal, NBANDS 276 (endpoint value); ENCUT/U/ISPIN/MAGMOM/k/smearing/EDIFFG unchanged, no stage A (INCAR_before_r2_algoAll kept)." >> $S/SUBMISSION_stage7.txt
qstat -u junbotong
