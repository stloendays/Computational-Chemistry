#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Stage 5 (2026-09-30 supervisor task): Ce2O3 / Ce2O4 cluster on Rh(111) vs the composition-matched layer.

Task: GitHub stloendays/Computational-Chemistry, Rh-CeOx-SMSI/stage2_interfaces_20260910/
TASK_20260930_CLUSTER_LAYER_EINT.md. Build Ce2O3/Rh(111) and Ce2O4/Rh(111), relax, compute
E_int = E[CexOy/Rh] - E[CexOy, isolated] - E[Rh(111)], compare with the 2026-09-28 layer E_int/2.

Contract (stage-4 layer contract, with the 2026-09-30 rules):
  VASP 6.3.2, PAW PBE.54 (Rh 04Feb2005, Ce 23Dec2003, O 08Apr2002); PBE+U, Dudarev Ueff(Ce 4f) = 5 eV;
  ENCUT 450 eV; ISPIN = 2 everywhere and NO MAGMOM line (VASP default seed, 1 muB per atom);
  ionic relaxation IBRION = 2, EDIFFG -0.02 eV/A; the final converged E0 of the relaxation is the energy
  (no extra single point); LREAL .FALSE.; LDIPOL off.
  Rh(111) p(4x4), 4 layers, bottom 2 fixed, a0 = 3.8232 A, bottom Rh plane at z = 0; one c for every slab,
  15 A of vacuum above the highest atom of the tallest starting structure; Gamma 3x3x1
  (= the k-point density of the layers' Gamma 4x4x1 on 3x3). 4x4 rather than 3x3: in 3x3 a Ce2Oy cluster is
  2.3 A from its own periodic image (stage 3).
  Slabs ISMEAR 1 / SIGMA 0.10; isolated clusters ISMEAR 0 / SIGMA 0.05 in a 15 A box, Gamma only.
  Ce systems: stage A = spin-polarised single point from scratch (ALGO All, NELM 500),
  stage B = relaxation from A's WAVECAR/CHGCAR (ALGO Normal).
All coordinates are starting guesses for relaxation, not results.
Run with D:/Research/CatalystForge/.venv/Scripts/python.exe from this folder: writes inputs/ + MANIFEST.sha256.
"""
import hashlib
import importlib.util
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "b3", os.path.join(HERE, "..", "DynSMSI_stage3_units_CH4_20260924", "build_stage3.py"))
b3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b3)                       # geometry helpers of stage 3 (same a0, same 4x4 lattice)

R1 = b3.R1                                          # round-1 relaxed CONTCARs (stage 2)
START = os.path.join(HERE, "start")                 # stage-3 relaxed CONTCARs copied from Vanda
PROJECT = "CFP04-CF-046"
VAC = 15.0


def rezero_4x4(path):
    """Stage-3 relaxed 4x4 structure as is (bottom Rh plane already at z = 0), flags kept."""
    atoms, cell = b3.rezero(path)
    return atoms, cell


def transplant_nearest(path):
    """Round-1 3x3 cluster -> 4x4 slab, same registry. Each non-Rh atom takes the periodic image nearest to
    the Ce-pair midpoint (in 3x3 the cluster was bonded to its own image, so a single-reference unwrap can
    pick the wrong image)."""
    cell, sym, pos = b3.read_poscar(path)
    isrh = sym == "Rh"
    zr = pos[isrh, 2]
    ztop_old = pos[isrh][zr > zr.max() - 0.6][:, 2].mean()
    idx = np.where(~isrh)[0]
    ce = pos[[k for k in idx if sym[k] == "Ce"]]
    mid = ce.mean(axis=0)
    un = []
    for k in idx:
        best = None
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                q = pos[k] + i * cell[0] + j * cell[1]
                d = np.linalg.norm((q - mid)[:2])
                if best is None or d < best[0]:
                    best = (d, q)
        un.append(best[1])
    un = np.array(un)
    M = np.array([b3.E1[:2], b3.E2[:2]]).T
    ab = np.linalg.solve(M, un.mean(axis=0)[:2])
    lp = np.round(ab)[0] * b3.E1 + np.round(ab)[1] * b3.E2
    rel = un - lp
    rel[:, 2] = un[:, 2] - ztop_old
    return [(sym[k], b3.surf(*b3.CENTRE, b3.ZTOP) + rel[n], False) for n, k in enumerate(idx)]


def add_o_fcc(atoms, h=1.30):
    """Ce2O3/Rh + one O in the top-layer fcc hollow nearest to the point 2.0 A outward from one Ce."""
    rh = np.array([a[1] for a in atoms if a[0] == "Rh"])
    ztop = rh[:, 2].max()
    ces = [a[1] for a in atoms if a[0] == "Ce"]
    cen = np.mean([a[1] for a in atoms if a[0] in ("Ce", "O")], axis=0)
    ce = max(ces, key=lambda p: p[0])               # the Ce on the +x side
    out = (ce - cen)[:2]
    out /= np.linalg.norm(out)
    target = ce[:2] + 2.0 * out
    M = np.array([b3.E1[:2], b3.E2[:2]]).T
    ab = np.linalg.solve(M, target)
    best = None
    for i in range(int(ab[0]) - 2, int(ab[0]) + 3):
        for j in range(int(ab[1]) - 2, int(ab[1]) + 3):
            p = b3.surf(i + b3.FCC, j + b3.FCC, ztop + h)
            d = np.linalg.norm(p[:2] - target)
            if best is None or d < best[0]:
                best = (d, p)
    return atoms + [("O", best[1], False)]


def incar(system, syms, stage, kind):
    t = [f"SYSTEM = {system} | {stage}", "PREC = Accurate", "ENCUT = 450", "ISPIN = 2",
         "ISYM = 0", "LREAL = .FALSE.", "LASPH = .TRUE.", "ADDGRID = .TRUE.", "LORBIT = 11", "NELMIN = 4",
         "AMIN = 0.01", "MAXMIX = 40", "AMIX_MAG = 0.4", "BMIX_MAG = 1.0"]
    if kind == "slab":
        t += ["ISMEAR = 1", "SIGMA = 0.10", "IDIPOL = 3", "LDIPOL = .FALSE.", "KPAR = 4", "NCORE = 3"]
    else:
        t += ["ISMEAR = 0", "SIGMA = 0.05", "NCORE = 3"]
    relax = ["IBRION = 2", "POTIM = 0.20", "NSW = 400" if kind == "slab" else "NSW = 150", "ISIF = 2",
             "EDIFFG = -0.02"]
    if stage == "stageA_spinSP":
        t += ["ISTART = 0", "ICHARG = 2", "ALGO = All", "NELM = 500", "EDIFF = 1E-5",
              "IBRION = -1", "NSW = 0", "LWAVE = .TRUE.", "LCHARG = .TRUE."]
    elif stage == "stageB_relax":
        t += ["ISTART = 1", "ICHARG = 1", "ALGO = Normal", "NELM = 300", "EDIFF = 1E-5"] + relax
        t += ["LWAVE = .TRUE.", "LCHARG = .TRUE."]
    elif stage == "relax":                          # clean Rh slab, one stage
        t += ["ISTART = 0", "ICHARG = 2", "ALGO = Normal", "NELM = 200", "EDIFF = 1E-5"] + relax
        t += ["LWAVE = .TRUE.", "LCHARG = .TRUE."]
    s = "\n".join(t) + "\n"
    return s + (b3.ldau(syms) if "Ce" in syms else "")


def main():
    root = os.path.join(HERE, "inputs")
    os.makedirs(root, exist_ok=True)
    slab = b3.rh_slab()

    c3a, _ = rezero_4x4(os.path.join(START, "CONTCAR_S1_12b_Ce2O3_Rh_from10b"))
    c3b, _ = rezero_4x4(os.path.join(START, "CONTCAR_S1_12a_Ce2O3_Rh_from10a"))
    c4a = slab + transplant_nearest(os.path.join(R1, "CONTCAR_10c_Ce2O4_cluster_Odown"))
    c4b = add_o_fcc(c3a)
    zmax = max(max(a[1][2] for a in s) for s in (c3a, c3b, c4a, c4b))
    C = round(zmax + VAC, 3)
    cell = np.array([b3.CELL[0], b3.CELL[1], [0.0, 0.0, C]])

    g3, box3 = b3.gas_from_contcar(os.path.join(START, "CONTCAR_S1_22_Ce2O3_gas"))
    g4, box4 = b3.gas_from_contcar(os.path.join(R1, "CONTCAR_43_Ce2O4_gas"))

    systems = [
        ("R4_Rh111_4x4", "Rh(111) p(4x4) 4L clean, bottom 2 fixed", slab, cell, "slab", "rh", (3, 3, 1)),
        ("C3a_Ce2O3_Rh_from12b", "Ce2O3 cluster on Rh(111) 4x4, start = stage-3 S1_12b relaxed", c3a, cell,
         "slab", "ce", (3, 3, 1)),
        ("C3b_Ce2O3_Rh_from12a", "Ce2O3 cluster on Rh(111) 4x4, start = stage-3 S1_12a relaxed", c3b, cell,
         "slab", "ce", (3, 3, 1)),
        ("C4a_Ce2O4_Rh_from10c", "Ce2O4 cluster on Rh(111) 4x4, start = round-1 10c, same registry", c4a, cell,
         "slab", "ce", (3, 3, 1)),
        ("C4b_Ce2O4_Rh_from12b_plusO", "Ce2O4 cluster on Rh(111) 4x4, start = S1_12b + O in fcc hollow", c4b,
         cell, "slab", "ce", (3, 3, 1)),
        ("G3_Ce2O3_gas", "Ce2O3 cluster in a 15 A box, start = stage-3 S1_22 relaxed", g3, box3, "gas", "ce",
         (1, 1, 1)),
        ("G4_Ce2O4_gas", "Ce2O4 cluster in a 15 A box, start = round-1 43 relaxed", g4, box4, "gas", "ce",
         (1, 1, 1)),
    ]
    stages_of = {"ce": [("stageA_spinSP", "LABORT", "scf"), ("stageB_relax", "LSTOP", "relax")],
                 "rh": [("relax", "LSTOP", "relax")]}
    print("c = %.3f A (highest starting atom %.3f A + %.1f A)" % (C, zmax, VAC))
    for name, title, atoms, cl, kind, fam, mesh in systems:
        d = os.path.join(root, name)
        os.makedirs(d, exist_ok=True)
        syms = b3.write_poscar(os.path.join(d, "POSCAR"), title, atoms, cl, seldyn=(kind == "slab"))
        stages = stages_of[fam]
        for tag, _, _ in stages:
            b3.write(os.path.join(d, "INCAR_" + tag), incar(title, syms, tag, kind))
        b3.write(os.path.join(d, "KPOINTS"), b3.kpoints(mesh, title))
        b3.write(os.path.join(d, "POTCAR.spec"), "\n".join(syms) + "\n")
        job = b3.JOB.format(name="s5_" + name[:12], np=36, mem="200gb" if kind == "slab" else "64gb",
                            stages="\n".join("run_stage %s %s %s" % s for s in stages),
                            files=" ".join("INCAR_" + t for t, _, _ in stages))
        b3.write(os.path.join(d, "job.pbs"), job.replace("CFP03-CF-126", PROJECT))
        ads = [a for a in atoms if a[0] != "Rh"]
        r, pair = b3.min_dist(atoms, cl, (True, True, kind == "gas"))
        gap = b3.image_gap(ads, cl) if kind == "slab" and ads else float("nan")
        P = np.array([a[1] for a in atoms])
        print("%-28s %-22s min %.3f A %-14s image gap %5.2f A  zmin %.3f  zmax %.3f" % (
            name, str({s: sum(1 for a in atoms if a[0] == s) for s in syms}), r, str(pair), gap,
            P[:, 2].min(), P[:, 2].max()))

    lines = []
    for dp, _, fs in sorted(os.walk(root)):
        for f in sorted(fs):
            if f == "MANIFEST.sha256":
                continue
            p = os.path.join(dp, f)
            lines.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(),
                                     os.path.relpath(p, root).replace("\\", "/")))
    b3.write(os.path.join(root, "MANIFEST.sha256"), "\n".join(lines) + "\n")
    print("wrote %d files" % len(lines))


if __name__ == "__main__":
    main()
