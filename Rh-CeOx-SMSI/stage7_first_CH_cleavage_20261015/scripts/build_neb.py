"""Stage 7 ordinary NEB inputs (supervisor 2026-10-15: LCLIMB = .FALSE. first, CI-NEB only after review).

One path per model, lowest CH4* -> lowest dissociated state of the same model (results/analyse_stage7.py):
  A_neb  A1_CH4_top      -> A2_CH3top_Hfcc      CH3*(Rh top) + H*(fcc)
  B_neb  B2_CH4_Os       -> B4_CH3Os_HOs        CH3O* + OH* (lattice O)
  C_neb  C1_CH4_perimRh  -> C3_CH3perimRh_HOt   CH3*(perimeter Rh) + OH*(cluster O)
  D_neb  given on the command line once the D endpoints are final.

Endpoints are the relaxed CONTCARs in results/raw/<name>/. The four H of the FS are reordered onto the IS H by
minimum total displacement (in-plane minimum image), so the split H is the one that moves; all other atoms keep
their index (same parent, same constraints). Six images by IDPP interpolation (ASE).
INCAR = the model's own stageB_relax INCAR (ENCUT 450, U 5, ISPIN 2, ISMEAR 1/0.10, same k mesh) plus
  IMAGES 6, SPRING -5, LCLIMB .FALSE., IBRION 3, POTIM 0, IOPT 7 (VTST FIRE), EDIFFG -0.05, NSW 500,
  ISTART 0, ICHARG 2, LCHARG .FALSE., KPAR 2, NCORE 6 (2 nodes, 12 ranks per image).
00/ and 07/ receive the endpoint OUTCARs on Vanda (stage7_next.py neb), so the profile includes both ends;
the images start from scratch (ISTART 0, ICHARG 2). Endpoint WAVECARs copied into the images broke the SCF of
every image away from the ends on 2026-10-26 (see stage7_next.py), so they are not used.

    python build_neb.py A B C                    -> next_steps/neb/<M>_neb/
    python build_neb.py --pair D D4_CH4_Ce D6_CH3Ce_HOc --raw <dir with D CONTCARs>
"""
import argparse
import itertools
import os
import re

import numpy as np
from ase.io import read, write
from ase.mep import NEB

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "results", "raw")
OUT = os.path.join(HERE, "next_steps", "neb")
PAIRS = {"A": ("A1_CH4_top", "A2_CH3top_Hfcc"),
         "B": ("B2_CH4_Os", "B4_CH3Os_HOs"),
         "C": ("C1_CH4_perimRh", "C3_CH3perimRh_HOt")}
N_IMAGES = 6
NEB_TAGS = {"IBRION": "3", "POTIM": "0", "EDIFFG": "-0.05", "NSW": "500", "ISTART": "0", "ICHARG": "2",
            "LCHARG": ".FALSE.", "KPAR": "2", "NCORE": "6"}
NEB_ADD = ["IMAGES = %d" % N_IMAGES, "SPRING = -5", "LCLIMB = .FALSE.", "ICHAIN = 0", "IOPT = 7"]


def dmin_image(cell, p, q):
    f = np.linalg.solve(np.array(cell).T, q - p)
    f[:2] -= np.round(f[:2])
    return np.linalg.norm(np.array(cell).T @ f)


def match_h(ini, fin):
    """Reorder the FS H atoms onto the IS H (minimum summed displacement)."""
    sy = ini.get_chemical_symbols()
    assert sy == fin.get_chemical_symbols(), "species order differs"
    h = [i for i, s in enumerate(sy) if s == "H"]
    best = min(itertools.permutations(h), key=lambda perm: sum(
        dmin_image(ini.cell, ini.positions[i], fin.positions[j]) for i, j in zip(h, perm)))
    order = list(range(len(fin)))
    for i, j in zip(h, best):
        order[i] = j
    out = fin[order]
    out.set_constraint(fin.constraints)
    return out


def unwrap_to(ref, a):
    """Shift each atom of a by in-plane lattice vectors to the image nearest ref (no jumps across the cell)."""
    cell = np.array(a.cell)
    f = np.linalg.solve(cell.T, (a.positions - ref.positions).T).T
    f[:, :2] = np.round(f[:, :2])
    f[:, 2] = 0
    a.positions = a.positions - f @ cell
    return a


def incar(src, title):
    t = open(src).read().replace("\r\n", "\n")
    t = re.sub(r"^SYSTEM = .*$", "SYSTEM = %s" % title, t, count=1, flags=re.M)
    for k, v in NEB_TAGS.items():
        t, n = re.subn(r"^%s = .*$" % k, "%s = %s" % (k, v), t, flags=re.M)
        if n == 0:
            t += "%s = %s\n" % (k, v)
    return t.rstrip("\n") + "\n" + "\n".join(NEB_ADD) + "\n"


JOB = """#!/usr/bin/env bash
#PBS -N s7neb_{tag}
#PBS -P CFP04-CF-046
#PBS -l select=2:ncpus=36:mpiprocs=36:ompthreads=1:mem=250gb
#PBS -l walltime=72:00:00
#PBS -j oe

set -euo pipefail
cd "$PBS_O_WORKDIR"
for f in INCAR KPOINTS POTCAR 00/POSCAR 00/OUTCAR {last}/POSCAR {last}/OUTCAR; do
  test -s "$f" || {{ echo "Missing or empty $f" >&2; exit 2; }}
done
module purge
module load intel/2021b
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
VASP_BIN=/nfs/home/svu/junbotong/software/vasp/NUS_HPC_VASP/vasp_632_vtst_solpp_beef_std
test -x "$VASP_BIN" || {{ echo "VASP executable not found: $VASP_BIN" >&2; exit 2; }}
NP=$(wc -l < "$PBS_NODEFILE")
echo "job_id=$PBS_JOBID host=$(hostname) ranks=$NP workdir=$PBS_O_WORKDIR start=$(date --iso-8601=seconds)"
START=$(date +%s)
rm -f STOPCAR
mpirun -np "$NP" "$VASP_BIN" > vasp_neb.out &
VP=$!
# watchdog at 250200 s (69.5 h): LSTOP keeps every image's CONTCAR for a restart
( while kill -0 "$VP" 2>/dev/null; do
    if [ $(( $(date +%s) - START )) -ge 250200 ]; then printf 'LSTOP = .TRUE.\\n' > STOPCAR; echo watchdog_stop; break; fi
    sleep 60; done ) &
WD=$!
set +e; wait "$VP"; RC=$?; set -e
kill "$WD" 2>/dev/null || true; wait "$WD" 2>/dev/null || true
rm -f STOPCAR
python3 neb_profile.py . > neb_profile.txt || true
echo "end=$(date --iso-8601=seconds) rc=$RC"
grep -q "reached required accuracy" 01/OUTCAR && echo "NEB converged" || echo "NEB NOT converged"
"""


def build(model, ini_name, fin_name, raw, out):
    ini = read(os.path.join(raw, ini_name, "CONTCAR"), format="vasp")
    fin = read(os.path.join(raw, fin_name, "CONTCAR"), format="vasp")
    assert len(ini) == len(fin) and np.allclose(ini.cell, fin.cell), "IS/FS cells or atom counts differ"
    fi = set(ini.constraints[0].index) if ini.constraints else set()
    ff = set(fin.constraints[0].index) if fin.constraints else set()
    assert fi == ff, "fixed atoms differ"
    fin = unwrap_to(ini, match_h(ini, fin))
    images = [ini] + [ini.copy() for _ in range(N_IMAGES)] + [fin]
    for im in images[1:-1]:
        im.set_constraint(ini.constraints)
    NEB(images).interpolate("idpp")
    d = os.path.join(out, "%s_neb" % model)
    os.makedirs(d, exist_ok=True)
    title = "Stage-7 ordinary NEB %s: %s -> %s" % (model, ini_name, fin_name)
    for k, im in enumerate(images):
        sub = os.path.join(d, "%02d" % k)
        os.makedirs(sub, exist_ok=True)
        write(os.path.join(sub, "POSCAR"), im, format="vasp", direct=True, sort=False)
    src = os.path.join(HERE, "inputs", ini_name)
    open(os.path.join(d, "INCAR"), "w", newline="\n").write(incar(os.path.join(src, "INCAR_stageB_relax"), title))
    k = os.path.join(src, "KPOINTS_relax") if os.path.exists(os.path.join(src, "KPOINTS_relax")) else \
        os.path.join(src, "KPOINTS")
    open(os.path.join(d, "KPOINTS"), "w", newline="\n").write(open(k).read().replace("\r\n", "\n"))
    open(os.path.join(d, "ENDPOINTS"), "w", newline="\n").write("%s %s\n" % (ini_name, fin_name))
    open(os.path.join(d, "job_neb.pbs"), "w", newline="\n").write(
        JOB.format(tag=model + "_" + ini_name.split("_")[0] + fin_name.split("_")[0], last="%02d" % (N_IMAGES + 1)))
    for root, _, fs in os.walk(d):                                # Vanda reads LF only
        for f in fs:
            p = os.path.join(root, f)
            raw_b = open(p, "rb").read()
            open(p, "wb").write(raw_b.replace(b"\r\n", b"\n"))
    disp = [dmin_image(ini.cell, ini.positions[i], fin.positions[i]) for i in range(len(ini))]
    top = sorted(range(len(ini)), key=lambda i: -disp[i])[:3]
    dmin = min(im.get_all_distances(mic=True)[np.triu_indices(len(im), 1)].min() for im in images[1:-1])
    line = "%s %s -> %s: %d atoms, %d fixed; largest moves %s; shortest pair in images %.2f A" % (
        model, ini_name, fin_name, len(ini), len(fi),
        ", ".join("%s%d %.2f A" % (ini[i].symbol, i, disp[i]) for i in top), dmin)
    print(line)
    return line


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("models", nargs="*", default=["A", "B", "C"])
    ap.add_argument("--pair", nargs=3, metavar=("MODEL", "IS", "FS"))
    ap.add_argument("--raw", default=RAW)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    jobs = [tuple(a.pair)] if a.pair else [(m,) + PAIRS[m] for m in a.models]
    rep = [build(m, i, f, a.raw, a.out) for m, i, f in jobs]
    with open(os.path.join(a.out, "BUILD_REPORT.txt"), "a", newline="\n") as fh:
        fh.write("\n".join(rep) + "\n")


if __name__ == "__main__":
    main()
