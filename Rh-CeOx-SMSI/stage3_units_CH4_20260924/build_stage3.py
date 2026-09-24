#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Stage 3, step 1: interaction energies of one CeO2 unit and one Ce2O3 cluster with Rh(111).

Task source: the supervisor's `discussion progress` document (Xiaoyan Li revision): build Rh(111),
Rh(111) + 1 CeO2 and Rh(111) + 1 Ce2O3; on the same Rh substrate compute the interaction energy of
one CeO2 unit and of one Ce2O3 cluster with the substrate. Step 2 (CH4 -> CH3 -> CH2 on Rh(111),
Rh(111) + Ce2O3 and Ce2O3(0001)) is built from the relaxed step-1 cluster afterwards.

Contract (2026-09-24; binding rules in GitHub stloendays/Computational-Chemistry, 053be74):
  ENCUT 450 eV; ISPIN = 2 for every calculation, no ISPIN = 1 pre-stage; PBE+U, Ueff(Ce 4f) = 5 eV;
  slab bottom plane at z = 0, the whole vacuum above, >= 15 A above the highest atom (c = 30 A);
  Rh(111) p(4x4), 4 layers, bottom 2 fixed, a0 = 3.8232 A (Stage-1, 400 eV; job S1_00 re-checks it at 450 eV);
  Gamma 3x3x1 (the k-point density of 4x4x1 on the round-1 3x3 cell); ISMEAR 1 / SIGMA 0.10, report E0;
  FIRE (IBRION 3, IOPT 7), EDIFFG -0.02 eV/A, LREAL = .FALSE., LDIPOL off during relaxation.
  Ce systems run two spin-polarised stages in one job: A = single point from scratch with ALGO = All
  (a Davidson spin start from scratch sloshed in round 1), B = relaxation from A's WAVECAR/CHGCAR.
All coordinates are starting guesses for relaxation, not results.
Run with any Python 3 + numpy from this folder: writes inputs/ and inputs/MANIFEST.sha256.
"""
import hashlib
import math
import os

import numpy as np

R1 = (r"D:\Research\Computational-Chemistry\Rh-CeOx-SMSI\stage2_interfaces_20260910"
      r"\results\CONTCAR_relaxed")

A0_RH = 3.8232328896
A_S = A0_RH / math.sqrt(2)                    # Rh(111) 1x1 surface lattice constant
D_RH = A0_RH / math.sqrt(3)                   # (111) interlayer spacing
N, NLAY, NFIX, C = 4, 4, 2, 30.0
E1 = np.array([A_S, 0.0, 0.0])
E2 = np.array([A_S / 2, A_S * math.sqrt(3) / 2, 0.0])
CELL = np.array([N * E1, N * E2, [0.0, 0.0, C]])
ZTOP = (NLAY - 1) * D_RH                      # bottom layer at z = 0
FCC, HCP = 1 / 3.0, 2 / 3.0                   # hollows above the top layer (top layer shift = 0)
CENTRE = (2.0, 2.0)                           # lattice point at fractional (1/2, 1/2) of the 4x4 cell
ORDER = ["Rh", "Ce", "O", "C", "H"]


def surf(u, v, z):
    """(u, v) in units of the 1x1 Rh surface cell (60-degree basis); z absolute."""
    return u * E1 + v * E2 + np.array([0.0, 0.0, z])


def rh_slab():
    atoms = []
    for L in range(NLAY):
        s = L / 3.0                           # ABC stacking
        for i in range(N):
            for j in range(N):
                atoms.append(("Rh", surf(i + s, j + s, L * D_RH), L < NFIX))
    return atoms


def read_poscar(path):
    L = open(path).read().split("\n")
    s = float(L[1].split()[0])
    cell = np.array([[float(x) for x in L[2 + i].split()[:3]] for i in range(3)]) * s
    names, counts = L[5].split(), [int(x) for x in L[6].split()]
    i = 8 if L[7].strip()[:1] in ("S", "s") else 7
    direct = L[i].strip()[:1] in ("D", "d")
    i += 1
    p = np.array([[float(x) for x in L[i + k].split()[:3]] for k in range(sum(counts))])
    sym = []
    for nm, c in zip(names, counts):
        sym += [nm] * c
    return cell, np.array(sym), (p @ cell if direct else p)


def transplant(path):
    """Take the non-Rh atoms of a round-1 relaxed 3x3 structure and put them on the 4x4 slab with
    the same registry: positions relative to the nearest ideal top-layer Rh lattice point and to the
    mean height of the relaxed top layer."""
    cell, sym, pos = read_poscar(path)
    isrh = sym == "Rh"
    zr = pos[isrh, 2]
    top = pos[isrh][zr > zr.max() - 0.6]
    ztop_old = top[:, 2].mean()
    inv = np.linalg.inv(cell)
    idx = np.where(~isrh)[0]
    ref = pos[idx[0]]
    un = []
    for k in idx:                                  # unwrap the cluster in-plane
        f = (pos[k] - ref) @ inv
        f[:2] -= np.round(f[:2])
        un.append(ref + f @ cell)
    un = np.array(un)
    M = np.array([E1[:2], E2[:2]]).T
    # registry check: relaxed top-layer Rh must sit on the ideal lattice (shift 0)
    ab_top = np.linalg.solve(M, top[:, :2].T).T
    reg_err = float(np.abs((ab_top - np.round(ab_top)) @ np.array([E1[:2], E2[:2]])).max())
    ab = np.linalg.solve(M, un.mean(axis=0)[:2])
    lp = np.round(ab)[0] * E1 + np.round(ab)[1] * E2
    rel = un - lp
    rel[:, 2] = un[:, 2] - ztop_old
    atoms = [(sym[k], surf(*CENTRE, ZTOP) + rel[n], False) for n, k in enumerate(idx)]
    return atoms, reg_err


def ceo2_flat():
    """O in two neighbouring fcc hollows (2.70 A apart, 1.33 A above the top layer), Ce above them."""
    o1 = surf(CENTRE[0] + FCC, CENTRE[1] + FCC, ZTOP + 1.33)
    o2 = surf(CENTRE[0] + 1 + FCC, CENTRE[1] + FCC, ZTOP + 1.33)
    ce = 0.5 * (o1 + o2) + np.array([0.0, 0.0, 1.45])
    return [("Ce", ce, False), ("O", o1, False), ("O", o2, False)]


def ceo2_cedown():
    """Ce over an fcc hollow in contact with Rh (~2.9 A), both O bent upward (O-Ce-O ~136 deg)."""
    ce = surf(CENTRE[0] + FCC, CENTRE[1] + FCC, ZTOP + 2.40)
    return [("Ce", ce, False), ("O", ce + np.array([1.75, 0.0, 0.70]), False),
            ("O", ce + np.array([-1.75, 0.0, 0.70]), False)]


def gas_box(atoms, L=15.0):
    P = np.array([a[1] for a in atoms])
    shift = np.array([L / 2] * 3) - 0.5 * (P.max(axis=0) + P.min(axis=0)) + np.array([0.13, 0.07, 0.0])
    return [(a[0], a[1] + shift, False) for a in atoms], np.eye(3) * L


def gas_from_contcar(path):
    cell, sym, pos = read_poscar(path)
    inv = np.linalg.inv(cell)
    ref = pos[0]
    un = []
    for p in pos:
        f = (p - ref) @ inv
        f -= np.round(f)
        un.append(ref + f @ cell)
    return gas_box([(s, q, False) for s, q in zip(sym, un)])


# ------------------------------------------------------------------ writers
def write(path, text):
    with open(path, "w", newline="\n") as f:
        f.write(text)


def write_poscar(path, title, atoms, cell, seldyn=True):
    syms = [s for s in ORDER if any(a[0] == s for a in atoms)]
    L = [title, "1.0"] + ["  %.10f  %.10f  %.10f" % tuple(v) for v in cell]
    L += ["  ".join(syms), "  ".join(str(sum(1 for a in atoms if a[0] == s)) for s in syms)]
    if seldyn:
        L.append("Selective dynamics")
    L.append("Cartesian")
    for s in syms:
        for a in atoms:
            if a[0] == s:
                flag = ("  F F F" if a[2] else "  T T T") if seldyn else ""
                L.append("  %.8f  %.8f  %.8f%s" % (a[1][0], a[1][1], a[1][2], flag))
    write(path, "\n".join(L) + "\n")
    return syms


def ldau(syms):
    return ("LDAU = .TRUE.\nLDAUTYPE = 2\n"
            "LDAUL = " + " ".join("3" if s == "Ce" else "-1" for s in syms) + "\n"
            "LDAUU = " + " ".join("5.0" if s == "Ce" else "0.0" for s in syms) + "\n"
            "LDAUJ = " + " ".join("0.0" for _ in syms) + "\nLMAXMIX = 6\n")


def incar(system, syms, counts, stage, kind):
    mag = " ".join("%d*%.1f" % (c, 1.0 if s == "Ce" else 0.0) for s, c in zip(syms, counts))
    t = [f"SYSTEM = {system} | {stage}", "PREC = Accurate", "ENCUT = 450", "ISPIN = 2",
         f"MAGMOM = {mag}", "ISYM = 0", "LREAL = .FALSE.", "LASPH = .TRUE.", "ADDGRID = .TRUE.",
         "LORBIT = 11", "NELMIN = 4", "AMIN = 0.01", "MAXMIX = 40", "AMIX_MAG = 0.4", "BMIX_MAG = 1.0"]
    if kind == "slab":
        t += ["ISMEAR = 1", "SIGMA = 0.10", "IDIPOL = 3", "LDIPOL = .FALSE.", "KPAR = 4", "NCORE = 3"]
    elif kind == "gas":
        t += ["ISMEAR = 0", "SIGMA = 0.05", "NCORE = 3"]
    else:                                         # bulk metal
        t += ["ISMEAR = 1", "SIGMA = 0.10", "KPAR = 4", "NCORE = 2"]
    if stage == "stageA_spinSP":                  # spin-polarised single point from scratch
        # NELM 500: the D2 spin stage with ALGO = All on these slabs needed 331 steps once, 800+ once
        t += ["ISTART = 0", "ICHARG = 2", "ALGO = All", "NELM = 500", "EDIFF = 1E-5",
              "IBRION = -1", "NSW = 0", "LWAVE = .TRUE.", "LCHARG = .TRUE."]
    elif stage == "stageB_relax":                 # relaxation from the stage-A wavefunctions
        t += ["ISTART = 1", "ICHARG = 1", "ALGO = Normal", "NELM = 300", "EDIFF = 1E-5"]
        t += (["IBRION = 3", "IOPT = 7", "POTIM = 0", "MAXMOVE = 0.2", "NSW = 400", "ISIF = 2",
               "EDIFFG = -0.02"] if kind == "slab" else
              ["IBRION = 2", "POTIM = 0.20", "NSW = 150", "ISIF = 2", "EDIFFG = -0.02"])
        t += ["LWAVE = .TRUE.", "LCHARG = .TRUE."]
    elif stage == "relax":                        # clean metal slab, single stage
        t += ["ISTART = 0", "ICHARG = 2", "ALGO = Normal", "NELM = 200", "EDIFF = 1E-5",
              "IBRION = 3", "IOPT = 7", "POTIM = 0", "MAXMOVE = 0.2", "NSW = 400", "ISIF = 2",
              "EDIFFG = -0.02", "LWAVE = .TRUE.", "LCHARG = .TRUE."]
    elif stage == "bulk_isif3":                   # Rh lattice constant at 450 eV
        t += ["ISTART = 0", "ICHARG = 2", "ALGO = Normal", "NELM = 200", "EDIFF = 1E-7",
              "IBRION = 2", "POTIM = 0.20", "NSW = 60", "ISIF = 3", "EDIFFG = -0.001",
              "LWAVE = .FALSE.", "LCHARG = .FALSE."]
    s = "\n".join(t) + "\n"
    return s + (ldau(syms) if "Ce" in syms else "")


JOB = """#!/usr/bin/env bash
#PBS -N {name}
#PBS -P CFP03-CF-126
#PBS -l select=1:ncpus={np}:mpiprocs={np}:ompthreads=1:mem={mem}
#PBS -l walltime=72:00:00
#PBS -j oe

set -euo pipefail
cd "$PBS_O_WORKDIR"
for f in {files} POSCAR KPOINTS POTCAR; do
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
# watchdog at 250200 s (69.5 h): LSTOP for relaxations, LABORT for single points
run_stage () {{
  local tag=$1 stop=$2 check=$3
  cp "INCAR_$tag" INCAR
  rm -f STOPCAR
  echo "stage=$tag start=$(date --iso-8601=seconds)"
  mpirun -np "$NP" "$VASP_BIN" > "vasp_$tag.out" &
  local VP=$!
  ( while kill -0 "$VP" 2>/dev/null; do
      if [ $(( $(date +%s) - START )) -ge 250200 ]; then printf '%s = .TRUE.\\n' "$stop" > STOPCAR; echo "watchdog_stop stage=$tag"; break; fi
      sleep 60; done ) &
  local WD=$!
  set +e; wait "$VP"; local RC=$?; set -e
  kill "$WD" 2>/dev/null || true; wait "$WD" 2>/dev/null || true
  rm -f STOPCAR
  cp OSZICAR "OSZICAR_$tag"; cp OUTCAR "OUTCAR_$tag"
  echo "stage=$tag end=$(date --iso-8601=seconds) rc=$RC"
  [ "$RC" -eq 0 ] || exit "$RC"
  case "$check" in
    scf)   grep -q "aborting loop because EDIFF is reached" OUTCAR || {{ echo "stage=$tag SCF NOT converged"; exit 3; }} ;;
    relax) grep -q "reached required accuracy" OUTCAR || {{ echo "stage=$tag RELAX NOT converged"; exit 4; }} ;;
  esac
}}
{stages}
echo "end=$(date --iso-8601=seconds) rc=0"
"""

STAGES = {  # tag, STOPCAR key, check
    "ce": [("stageA_spinSP", "LABORT", "scf"), ("stageB_relax", "LSTOP", "relax")],
    "rh": [("relax", "LSTOP", "relax")],
    "bulk": [("bulk_isif3", "LSTOP", "relax")],
}


def kpoints(mesh, comment):
    return f"{comment}\n0\nGamma\n{mesh[0]} {mesh[1]} {mesh[2]}\n0 0 0\n"


def min_dist(atoms, cell, pbc=(True, True, False)):
    P = np.array([a[1] for a in atoms])
    inv = np.linalg.inv(cell)
    best = (1e9, None)
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            f = (P[j] - P[i]) @ inv
            for k in range(3):
                if pbc[k]:
                    f[k] -= round(f[k])
            r = float(np.linalg.norm(f @ cell))
            if r < best[0]:
                best = (r, (atoms[i][0], atoms[j][0]))
    return best


def image_gap(ads, cell):
    """Shortest distance between an adsorbate atom and a periodic image of the adsorbate."""
    P = np.array([a[1] for a in ads])
    best = 1e9
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            if i == 0 and j == 0:
                continue
            Q = P + i * cell[0] + j * cell[1]
            best = min(best, float(np.min(np.linalg.norm(P[:, None, :] - Q[None, :, :], axis=2))))
    return best


def main():
    root = "inputs"
    os.makedirs(root, exist_ok=True)
    rep = []

    def emit(name, title, atoms, family, kind, cell=CELL, mesh=(3, 3, 1), np_=36, mem="200gb", seldyn=True):
        d = os.path.join(root, name)
        os.makedirs(d, exist_ok=True)
        syms = write_poscar(os.path.join(d, "POSCAR"), title, atoms, cell, seldyn)
        counts = [sum(1 for a in atoms if a[0] == s) for s in syms]
        stages = STAGES[family]
        for tag, _, _ in stages:
            write(os.path.join(d, "INCAR_" + tag), incar(title, syms, counts, tag, kind))
        write(os.path.join(d, "KPOINTS"), kpoints(mesh, title))
        write(os.path.join(d, "POTCAR.spec"), "\n".join(syms) + "\n")
        calls = "\n".join('run_stage %s %s %s' % s for s in stages)
        write(os.path.join(d, "job.pbs"), JOB.format(
            name="s3_" + name[:12], np=np_, mem=mem, stages=calls,
            files=" ".join("INCAR_" + t for t, _, _ in stages)))
        P = np.array([a[1] for a in atoms])
        vac = C - (P[:, 2].max() - P[:, 2].min()) if kind == "slab" else None
        rep.append((name, dict(zip(syms, counts)), min_dist(atoms, cell), P[:, 2].min(), vac))

    slab = rh_slab()
    emit("S1_00_Rh_bulk_450", "fcc Rh primitive cell, a0 check at ENCUT 450",
         [("Rh", np.zeros(3), False)], "bulk", "bulk",
         cell=np.array([[0, .5, .5], [.5, 0, .5], [.5, .5, 0]]) * A0_RH, mesh=(21, 21, 21),
         np_=8, mem="32gb", seldyn=False)
    emit("S1_01_Rh111_4x4", "Rh(111) p(4x4) 4L clean, bottom 2 fixed", slab, "rh", "slab")

    ce_a, err_a = transplant(os.path.join(R1, "CONTCAR_10a_Ce2O3_cluster_Odown"))
    ce_b, err_b = transplant(os.path.join(R1, "CONTCAR_10b_Ce2O3_cluster_Cedown"))
    emit("S1_12a_Ce2O3_Rh_from10a", "one Ce2O3 cluster on Rh(111) 4x4, start = round-1 10a geometry",
         slab + ce_a, "ce", "slab")
    emit("S1_12b_Ce2O3_Rh_from10b", "one Ce2O3 cluster on Rh(111) 4x4, start = round-1 10b geometry",
         slab + ce_b, "ce", "slab")
    emit("S1_11a_CeO2_Rh_flat", "one CeO2 unit on Rh(111) 4x4, start: both O in fcc hollows",
         slab + ceo2_flat(), "ce", "slab")
    emit("S1_11b_CeO2_Rh_Cedown", "one CeO2 unit on Rh(111) 4x4, start: Ce on Rh, O bent up",
         slab + ceo2_cedown(), "ce", "slab")

    g21, box = gas_box([("Ce", np.zeros(3), False), ("O", np.array([1.70, 0.0, -0.62]), False),
                        ("O", np.array([-1.70, 0.0, -0.62]), False)])
    emit("S1_21_CeO2_gas", "CeO2 unit in a 15 A box, bent start", g21, "ce", "gas",
         cell=box, mesh=(1, 1, 1), mem="64gb", seldyn=False)
    g22, box = gas_from_contcar(os.path.join(R1, "CONTCAR_42_Ce2O3_gas"))
    emit("S1_22_Ce2O3_gas", "Ce2O3 unit in a 15 A box, start = round-1 relaxed 42", g22, "ce", "gas",
         cell=box, mesh=(1, 1, 1), mem="64gb", seldyn=False)

    print("a_s = %.4f A, 4x4 cell a = %.4f A, d(111) = %.4f A, top layer z = %.3f A"
          % (A_S, N * A_S, D_RH, ZTOP))
    print("registry check (relaxed round-1 top layer vs ideal lattice): 10a %.3f A, 10b %.3f A"
          % (err_a, err_b))
    for name, ads in (("12a", ce_a), ("12b", ce_b), ("11a", ceo2_flat()), ("11b", ceo2_cedown())):
        print("  %s cluster-to-image gap %.2f A" % (name, image_gap(ads, CELL)))
    for n, c, (r, pair), zmin, vac in rep:
        print("%-26s %-28s min %.3f A %-12s zmin %.3f%s" % (
            n, str(c), r, str(pair), zmin, "" if vac is None else "  vacuum %.2f A" % vac))

    lines = []
    for dp, _, fs in sorted(os.walk(root)):
        for f in sorted(fs):
            if f == "MANIFEST.sha256":
                continue
            p = os.path.join(dp, f)
            lines.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(),
                                     os.path.relpath(p, root).replace("\\", "/")))
    write(os.path.join(root, "MANIFEST.sha256"), "\n".join(lines) + "\n")
    print("wrote %d files, manifest inputs/MANIFEST.sha256" % len(lines))


if __name__ == "__main__":
    main()
