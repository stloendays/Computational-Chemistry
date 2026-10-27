#!/usr/bin/env bash
# 2026-10-27 (user: option 1): Ce-containing NEB in two steps inside one job.
#   stage A per image: the endpoint's own INCAR_stageA_spinSP (ALGO All, NELM 500, MAXMIX 40, ISTART 0/ICHARG 2)
#     + IMAGES 6, KPAR 2 / NCORE 6 (the NEB layout, so the WAVECARs are read back unchanged) + MAGMOM Ce 1
#     one resume round (ISTART 1, ICHARG 0) if an image hits NELM, as for the endpoints
#   NEB: the existing INCAR with ISTART 1, ICHARG 0 (each image reads its own stage-A WAVECAR)
# STAGEA_DONE marks a finished stage A, so a monitor resume continues the NEB only.
set -euo pipefail
S=/scratch/junbotong/Dynamic_SMSI_stage7_first_CH_cleavage_20261015
for m in B C; do
  d=$S/neb/${m}_neb
  cd "$d"
  read ini fin < ENDPOINTS
  mg=$(grep '^MAGMOM' INCAR)
  # stage A INCAR from the IS endpoint
  sed -e "s/^SYSTEM = .*/SYSTEM = Stage-7 NEB $m images | stageA_spinSP/" \
      -e 's/^KPAR = .*/KPAR = 2/' -e 's/^NCORE = .*/NCORE = 6/' -e 's/^LCHARG = .*/LCHARG = .FALSE./' \
      ../../inputs/$ini/INCAR_stageA_spinSP > INCAR_stageA_images
  printf 'IMAGES = 6\n%s\n' "$mg" >> INCAR_stageA_images
  sed -e 's/^ISTART = .*/ISTART = 1/' -e 's/^ICHARG = .*/ICHARG = 0/' INCAR_stageA_images > INCAR_stageA_images_r1
  sed -e 's/^ISTART = .*/ISTART = 1/' -e 's/^ICHARG = .*/ICHARG = 0/' INCAR > INCAR_neb
  head=$(sed -n '1,/^START=/p' job_neb.pbs.hold | sed 's/for f in INCAR KPOINTS/for f in INCAR_stageA_images INCAR_neb KPOINTS/')
  cat > job_neb.pbs <<EOF
$head
IMGS="\$(seq -f %02g 1 6)"
run_vasp () {
  local tag=\$1 stop=\$2 out=\$3
  cp "INCAR_\$tag" INCAR
  rm -f STOPCAR
  echo "stage=\$tag start=\$(date --iso-8601=seconds)"
  mpirun -np "\$NP" "\$VASP_BIN" > "\$out" &
  local VP=\$!
  ( while kill -0 "\$VP" 2>/dev/null; do
      if [ \$(( \$(date +%s) - START )) -ge 250200 ]; then printf '%s = .TRUE.\\n' "\$stop" > STOPCAR; echo watchdog_stop; break; fi
      sleep 60; done ) &
  local WD=\$!
  set +e; wait "\$VP"; local RC=\$?; set -e
  kill "\$WD" 2>/dev/null || true; wait "\$WD" 2>/dev/null || true
  rm -f STOPCAR
  for k in \$IMGS; do cp \$k/OSZICAR \$k/OSZICAR_\$tag; cp \$k/OUTCAR \$k/OUTCAR_\$tag; done
  echo "stage=\$tag end=\$(date --iso-8601=seconds) rc=\$RC"
  [ "\$RC" -eq 0 ] || exit "\$RC"
}
imgs_ok () { for k in \$IMGS; do grep -q "aborting loop because EDIFF is reached" \$k/OUTCAR || return 1; done; }
if [ ! -e STAGEA_DONE ]; then
  if [ -e STAGEA_STARTED ] && [ -s 01/WAVECAR ]; then first=stageA_images_r1; else first=stageA_images; fi
  touch STAGEA_STARTED
  run_vasp \$first LABORT vasp_neb_stageA.out
  imgs_ok || run_vasp stageA_images_r1 LABORT vasp_neb_stageA_r1.out
  imgs_ok || { echo "stage=stageA_images SCF NOT converged"; exit 3; }
  for k in \$IMGS; do printf '%s ' "\$k:\$(grep 'number of electron' \$k/OUTCAR | tail -1 | awk '{print \$NF}')"; done; echo
  touch STAGEA_DONE
fi
run_vasp neb LSTOP vasp_neb.out
python3 neb_profile.py . > neb_profile.txt || true
echo "end=\$(date --iso-8601=seconds) rc=0"
grep -q "reached required accuracy" 01/OUTCAR && echo "NEB converged" || echo "NEB NOT converged"
EOF
  rm job_neb.pbs.hold
  echo "== $m"; diff <(sort ../../inputs/$ini/INCAR_stageA_spinSP) <(sort INCAR_stageA_images) || true
  grep -E '^(ISTART|ICHARG|ALGO|NELM|MAGMOM)' INCAR_neb | tr '\n' ';'; echo
  bash -n job_neb.pbs && echo "job_neb.pbs syntax ok"
done
