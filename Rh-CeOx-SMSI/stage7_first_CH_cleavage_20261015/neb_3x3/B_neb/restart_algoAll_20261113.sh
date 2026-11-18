#!/usr/bin/env bash
# 2026-11-13 user "重投一下": stop NEB B 1550784 (SCF stuck at NELM 300, no ionic step in 13 h) and resubmit with
# ALGO = All (INCAR already edited; old INCAR kept as INCAR_before_r1_algoNormal). Waits for PBS to come back.
S=/scratch/junbotong/Dynamic_SMSI_stage7_first_CH_cleavage_20261015
D=$S/neb_3x3/B_neb; LOCK=$S/monitor/lock; OLD=1550784
log(){ echo "$(date +%F_%T) $*"; }
cd "$D" || exit 1
grep -q '^ALGO = All$' INCAR || { log "INCAR not ALGO = All, abort"; exit 1; }
for k in $(seq 1 8640); do qstat -u junbotong >/dev/null 2>&1 && break; sleep 30; done
qstat -u junbotong >/dev/null 2>&1 || { log "PBS still down after 72 h, giving up"; exit 1; }
log "PBS back"
for k in $(seq 1 120); do mkdir "$LOCK" 2>/dev/null && break; sleep 15; done
[ -d "$LOCK" ] || { log "no lock"; exit 1; }
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
qstat -u junbotong
if qstat $OLD 2>/dev/null | grep -q " [RQH] "; then qdel $OLD; log "qdel $OLD"; fi
for k in $(seq 1 60); do qstat $OLD 2>/dev/null | grep -q " [RQHE] " || break; sleep 10; done
if qstat -u junbotong 2>/dev/null | grep -q s7neb_B; then log "a B job is still live, not resubmitting"; qstat -u junbotong; exit 1; fi
sleep 20
for i in 01 02 03 04 05 06; do (cd $i && for f in POSCAR CONTCAR OUTCAR OSZICAR; do [ -e $f ] && cp -p $f ${f}_before_r1_algoNormal; done); done
[ -e vasp_neb.out ] && cp -p vasp_neb.out vasp_neb.out_before_r1_algoNormal
touch STAGEA_DONE
J=$(qsub job_neb.pbs) || { log "qsub failed: $J"; exit 1; }
log "qsub $J"
echo "$(date +%Y-%m-%dT%H:%M:%S) [claude] neb_3x3/B_neb $J (s7neb_B_B5bB14): user 2026-11-13 \"重投一下\" - qdel $OLD (13 h, no ionic step: images 01-04 hit NELM 300 unconverged, 05/06 still in SCF); same images (POSCAR unchanged, outputs kept as *_before_r1_algoNormal), same physics, only ALGO Normal -> All (INCAR_before_r1_algoNormal kept); ISTART 0 / ICHARG 2, MAGMOM 36*0 4*1 11*0, no stage A." >> $S/SUBMISSION_stage7.txt
qstat -u junbotong
