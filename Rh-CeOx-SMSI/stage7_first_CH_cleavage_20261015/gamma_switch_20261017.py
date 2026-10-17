#!/usr/bin/env python3
"""2026-10-17 (user): D1-D3 relax with Gamma-only k-points, final single point with 2x2x1; D0 unchanged.

Per system (run on Vanda in .../inputs, after the old jobs are stopped):
  backups  INCAR_*_k221, KPOINTS_k221, OUTCAR/OSZICAR of the stopped run -> *_k221_partial
  KPOINTS_relax = Gamma 1x1x1, KPOINTS_final = the original 2x2x1
  INCAR_stageA_spinSP / INCAR_stageB_relax -> KPAR 1, NCORE 6 (one k-point); stageB reads the 2x2 CHGCAR (ICHARG 1)
  INCAR_stageC_SP -> ISTART 0, ICHARG 1 (starts from the Gamma-relax density; WAVECAR k-mesh differs)
  D1: CONTCAR (1 ionic step at 2x2) -> POSCAR; D3: POSCAR kept (no ionic step); D2: stage A had not finished -> redo at Gamma
  job_resume_gamma.pbs: [A] -> B (Gamma) -> cp CONTCAR POSCAR; cp KPOINTS_final KPOINTS -> C (2x2x1)
Physics settings otherwise identical (ENCUT 450, U 5, ISPIN 2, smearing, EDIFFG).
"""
import os
import re
import shutil
import subprocess
import sys

SYS = {"D1_Ce2O3_hO_2Odown": "B", "D2_Ce2O3_hO_1Odown": "A", "D3_Ce2O3_gasgeom": "B"}


def sub(txt, key, val):
    new, n = re.subn(r"^%s = .*$" % key, "%s = %s" % (key, val), txt, flags=re.M)
    assert n == 1, key
    return new


def main(stage_dir):
    for name, first in SYS.items():
        d = os.path.join(stage_dir, name)
        os.chdir(d)
        for f in ("INCAR_stageA_spinSP", "INCAR_stageB_relax", "INCAR_stageC_SP", "KPOINTS"):
            if not os.path.exists(f + "_k221"):
                shutil.copy(f, f + "_k221")
        shutil.copy("KPOINTS_k221", "KPOINTS_final")
        title = open("KPOINTS_k221").readline().strip()
        open("KPOINTS_relax", "w").write("%s | Gamma only (relaxation)\n0\nGamma\n1 1 1\n0 0 0\n" % title)
        for f in ("OUTCAR", "OSZICAR", "vasp_stageA_spinSP.out", "vasp_stageB_relax.out"):
            if os.path.exists(f):
                shutil.move(f, f + "_k221_partial")
        a = open("INCAR_stageA_spinSP_k221").read()
        a = sub(sub(a, "KPAR", "1"), "NCORE", "6")
        b = open("INCAR_stageB_relax_k221").read()
        b = sub(sub(b, "KPAR", "1"), "NCORE", "6")
        if first == "B":           # start from the converged 2x2 spin density
            b = sub(sub(b, "ISTART", "0"), "ICHARG", "1")
        c = open("INCAR_stageC_SP_k221").read()
        c = sub(sub(c, "ISTART", "0"), "ICHARG", "1")
        open("INCAR_stageA_spinSP", "w").write(a)
        open("INCAR_stageB_relax", "w").write(b)
        open("INCAR_stageC_SP", "w").write(c)
        if name.startswith("D1"):
            shutil.copy("POSCAR", "POSCAR_before_gamma")
            shutil.copy("CONTCAR", "CONTCAR_k221_step1")
            shutil.copy("CONTCAR", "POSCAR")
        job = open("job.pbs").read()
        head = job.split("\nrun_stage ", 1)[0]
        stages = (["stageA_spinSP"] if first == "A" else []) + ["stageB_relax", "stageC_SP"]
        need = " ".join("INCAR_" + t for t in stages) + " POSCAR KPOINTS_relax KPOINTS_final POTCAR" + \
            (" CHGCAR" if first == "B" else "")
        head = re.sub(r"^for f in .*; do$", "for f in %s; do" % need, head, count=1, flags=re.M)
        head = re.sub(r"^#PBS -N \S+", "#PBS -N s7g_%s" % name[:12], head, count=1, flags=re.M)
        body = ["cp KPOINTS_relax KPOINTS"]
        if first == "A":
            body.append("run_stage stageA_spinSP LABORT scf")
        body += ["run_stage stageB_relax LSTOP relax",
                 "cp POSCAR POSCAR_start; cp CONTCAR POSCAR; cp KPOINTS_final KPOINTS",
                 "run_stage stageC_SP LABORT scf"]
        open("job_resume_gamma.pbs", "w").write(head + "\n" + "\n".join(body) +
                                               '\necho "end=$(date --iso-8601=seconds) rc=0"\n')
        jid = subprocess.run(["qsub", "job_resume_gamma.pbs"], stdout=subprocess.PIPE,
                             universal_newlines=True, check=True).stdout.strip()
        with open(os.path.join(stage_dir, "..", "SUBMISSION_stage7.txt"), "a") as fh:
            fh.write("%s %s gamma_relax_k221_SP_20261017\n" % (name, jid))
        print(name, jid)


if __name__ == "__main__":
    main(sys.argv[1])
