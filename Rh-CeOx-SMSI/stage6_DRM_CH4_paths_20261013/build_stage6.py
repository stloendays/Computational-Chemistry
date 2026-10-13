#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Stage 6 (2026-10-13 supervisor task), Phase 1: CH4 -> CH3* + H* -> CH2* + 2H* intermediates on
(A) Rh(111) p(4x4), (B) Ce2O3 cluster (Stage-5 C3a)/Rh(111) p(4x4), (C) Ce2O3 crystalline layer Ce4O6/Rh(111) p(3x3).

Builds starting geometries + INCAR/KPOINTS/POTCAR.spec/job.pbs only. Nothing is submitted: the pathway list is
first confirmed with Dr. Xiaoyan Li (2026-10-13 note). All coordinates are starting guesses, not results.

Contract (= Stage 5, plus the final single point required by the project rules):
  VASP 6.3.2, PAW PBE.54 (Rh 04Feb2005, Ce 23Dec2003, O 08Apr2002, C 08Apr2002, H 15Jun2001); PBE+U Dudarev
  Ueff(Ce 4f) = 5 eV, LMAXMIX 6; ENCUT 450; ISPIN 2, no MAGMOM line; LREAL .FALSE.; IDIPOL 3, LDIPOL off.
  Slabs: stage A spin SP from scratch (ALGO All) -> stage B relaxation IBRION 2, EDIFFG -0.02, ISMEAR 1 /
  SIGMA 0.10 -> stage C single point on the relaxed structure, ISMEAR 0 / SIGMA 0.05 (reported energy).
  Gas molecules: 15 A box, Gamma, ISMEAR 0 / SIGMA 0.05 throughout.
  One c per model (clean reference included): highest atom of the model's tallest start + 15 A; bottom Rh plane
  at z = 0; parent selective-dynamics flags kept (bottom two Rh layers fixed), adsorbates free.
  Optional --d3 adds IVDW = 12 (D3-BJ) to every system of the set; default off (current project contract).

Usage:  python build_stage6.py [--layer PATH_TO_RELAXED_LAYER_CONTCAR] [--d3]
  The mainline layer parent is the Stage-3 S1_31_Ce4O6_layer_Rh3x3 CONTCAR (450 eV, ISPIN 2) on Vanda; when it is
  not given, the round-1 30a CONTCAR in this repository is used and the inputs are marked PREVIEW.
"""
import argparse
import hashlib
import os

import numpy as np
from ase import Atoms
from ase.constraints import FixAtoms
from ase.io import read, write

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
S5 = os.path.join(ROOT, "stage2_interfaces_20260910", "results", "cluster_layer_Eint_20260930")
PARENT = {"A": os.path.join(S5, "R4_Rh111_4x4", "CONTCAR"),
          "B": os.path.join(S5, "C3a_Ce2O3_Rh_from12b", "CONTCAR"),
          "C": os.path.join(ROOT, "stage2_interfaces_20260910", "results", "CONTCAR_relaxed",
                            "CONTCAR_30a_Ce4O6_layer_2Obot")}
JOB_TEMPLATE = os.path.join(ROOT, "stage2_interfaces_20260910", "cluster_layer_Eint_20260930", "inputs",
                            "C3a_Ce2O3_Rh_from12b", "job.pbs")
KMESH = {"A": (3, 3, 1), "B": (3, 3, 1), "C": (4, 4, 1)}
VAC = 15.0
D_CH = 1.10


# ---------------------------------------------------------------- geometry helpers
def load(path):
    a = read(path, format="vasp")
    a.positions[:, 2] -= a.positions[a.numbers == 45, 2].min()       # bottom Rh plane -> z = 0
    a.wrap()
    return a


def rh_layers(a):
    rh = np.where(a.numbers == 45)[0]
    z = a.positions[rh, 2]
    top = rh[z > z.max() - 0.6]
    sec = rh[(z < z.max() - 0.6) & (z > z.max() - 3.0)]
    return top, sec


def lateral(a, p, q):
    """Minimum-image lateral distance between two points."""
    d = np.array(q[:2]) - np.array(p[:2])
    best = 1e9
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            v = d + i * a.cell[0, :2] + j * a.cell[1, :2]
            best = min(best, np.linalg.norm(v))
    return best


def fcc_hollows(a):
    """fcc hollows of the top Rh layer: centroids of top-layer triangles with no 2nd-layer atom below."""
    top, sec = rh_layers(a)
    ztop = a.positions[top, 2].mean()
    out = []
    # candidate points = top atom + (e1+e2)/3 or 2(e1+e2)/3, e = surface 1x1 vectors; hcp ones sit over a 2nd-layer atom
    n = int(round(np.linalg.norm(a.cell[0]) / 2.70))
    e1, e2 = a.cell[0] / n, a.cell[1] / n
    for i in top:
        for f in (1 / 3, 2 / 3):
            q = a.positions[i] + f * (e1 + e2)
            if min(lateral(a, q, a.positions[k]) for k in sec) > 0.8:
                q = q.copy()
                q[2] = ztop
                if all(lateral(a, q, o) > 0.5 for o in out):
                    out.append(q)
    return np.array(out), ztop


def oxide(a):
    return np.where((a.numbers == 58) | (a.numbers == 8))[0]


def free_of_oxide(a, q, rmin):
    ox = oxide(a)
    return all(lateral(a, q, a.positions[k]) > rmin for k in ox)


def ch4(c, down=True):
    """CH4 with one C-H pointing to the surface."""
    h = [c + [0, 0, -D_CH if down else D_CH]]
    for k in range(3):
        t = 2 * np.pi * k / 3
        h.append(c + [D_CH * 0.9428 * np.cos(t), D_CH * 0.9428 * np.sin(t), (D_CH / 3) * (1 if down else -1)])
    return c, h


def ch3(c):
    """Umbrella CH3, H atoms pointing away from the surface."""
    return c, [c + [1.03 * np.cos(t), 1.03 * np.sin(t), 0.37] for t in (0, 2 * np.pi / 3, 4 * np.pi / 3)]


def ch2(c, phi=0.0):
    return c, [c + [0.93 * np.cos(phi + s), 0.93 * np.sin(phi + s), 0.62] for s in (0, np.pi)]


def add(a, frags):
    """Append C first, then all H (POSCAR species order Rh Ce O C H); adsorbates unconstrained."""
    fixed = list(a.constraints[0].index) if a.constraints else []
    b = a.copy()
    b.set_constraint()
    cs = [f[0] for f in frags if f[0] is not None]
    hs = [h for f in frags for h in f[1]]
    if cs:
        b += Atoms("C%d" % len(cs), positions=cs, cell=b.cell, pbc=True)
    if hs:
        b += Atoms("H%d" % len(hs), positions=hs, cell=b.cell, pbc=True)
    b.set_constraint(FixAtoms(indices=fixed))
    return b


def nearest(points, ref, a, exclude=()):
    best = None
    for p in points:
        if any(lateral(a, p, e) < 0.5 for e in exclude):
            continue
        d = lateral(a, p, ref)
        if best is None or d < best[0]:
            best = (d, p)
    return best[1]


# ---------------------------------------------------------------- site sets per model
def model_A(a):
    top, _ = rh_layers(a)
    fcc, ztop = fcc_hollows(a)
    rh0 = a.positions[top[np.argmin(np.linalg.norm(a.positions[top, :2] - a.cell[:2, :2].sum(0) / 2, axis=1))]]
    h1 = nearest(fcc, rh0 + [2.7, 0, 0], a)
    f1 = nearest(fcc, rh0, a)
    f2 = nearest(fcc, f1 + [2.7, 0, 0], a, exclude=[f1])
    f3 = nearest(fcc, f1 + [-1.35, 2.34, 0], a, exclude=[f1, f2])
    return {
        "A1_CH4_top": [ch4(rh0 + [0, 0, 3.2])],
        "A2_CH3top_Hfcc": [ch3(rh0 + [0, 0, 2.06]), (None, [h1 + [0, 0, 0.95]])],
        "A3_CH2fcc_2Hfcc": [ch2(f1 + [0, 0, 1.55]), (None, [f2 + [0, 0, 0.95], f3 + [0, 0, 0.95]])],
    }


def model_B(a):
    """Cluster: perimeter Rh (Rh-O-Ce interface), cluster top O (O_t), Ce."""
    top, _ = rh_layers(a)
    fcc, ztop = fcc_hollows(a)
    ox = oxide(a)
    ce = [i for i in ox if a.numbers[i] == 58]
    o = [i for i in ox if a.numbers[i] == 8]
    o_top = max(o, key=lambda i: a.positions[i, 2])
    cen = a.positions[ox].mean(axis=0)
    # perimeter Rh: top-layer Rh 2.6-3.6 A laterally from the nearest cluster atom, chosen on the side of a Ce
    per = [i for i in top if 2.6 < min(lateral(a, a.positions[i], a.positions[k]) for k in ox) < 3.6]
    rp = a.positions[min(per, key=lambda i: lateral(a, a.positions[i], a.positions[ce[0]]))]
    free_fcc = [f for f in fcc if free_of_oxide(a, f, 2.4)]
    hp = nearest(free_fcc, rp, a)
    far = a.positions[max(top, key=lambda i: lateral(a, a.positions[i], cen))]
    hfar = nearest(free_fcc, far, a)
    f1 = nearest(free_fcc, rp, a)
    f2 = nearest(free_fcc, f1, a, exclude=[f1])
    f3 = nearest(free_fcc, f1, a, exclude=[f1, f2])
    ce_top = a.positions[max(ce, key=lambda i: a.positions[i, 2])]
    out = ce_top[:2] - a.positions[o_top, :2]                        # Ce-CH3 tilted away from O_t
    away = np.array([*(0.6 * out / np.linalg.norm(out)), 0.8])
    return {
        "B1_CH4_perimRh": [ch4(rp + [0, 0, 3.2])],
        "B2_CH4_Ce": [ch4(ce_top + [0, 0, 3.4])],
        "B3_CH3perimRh_HOt": [ch3(rp + [0, 0, 2.06]), (None, [a.positions[o_top] + [0, 0, 0.98]])],
        "B4_CH3perimRh_Hfcc": [ch3(rp + [0, 0, 2.06]), (None, [hp + [0, 0, 0.95]])],
        "B5_CH3Ce_HOt": [ch3(ce_top + 2.55 * away), (None, [a.positions[o_top] + [0, 0, 0.98]])],
        "B6_CH3farRh_Hfcc": [ch3(far + [0, 0, 2.06]), (None, [hfar + [0, 0, 0.95]])],
        "B7_CH2perimfcc_HOt_Hfcc": [ch2(f1 + [0, 0, 1.55]),
                                    (None, [a.positions[o_top] + [0, 0, 0.98], f2 + [0, 0, 0.95]])],
        "B8_CH2perimfcc_2Hfcc": [ch2(f1 + [0, 0, 1.55]), (None, [f2 + [0, 0, 0.95], f3 + [0, 0, 0.95]])],
    }


def model_C(a):
    """Layer fully covers Rh: surface O (O_s, upper O plane) and Ce sites of the Ce2O3 layer."""
    ox = oxide(a)
    ce = [i for i in ox if a.numbers[i] == 58]
    o = sorted([i for i in ox if a.numbers[i] == 8], key=lambda i: -a.positions[i, 2])
    os_ = [i for i in o if a.positions[i, 2] > a.positions[ce, 2].mean()]      # O above the Ce plane
    ce1 = a.positions[max(ce, key=lambda i: a.positions[i, 2])]
    o1 = a.positions[min(os_, key=lambda i: lateral(a, a.positions[i], ce1))]
    o2 = a.positions[min([i for i in os_ if lateral(a, a.positions[i], o1) > 0.5],
                         key=lambda i: lateral(a, a.positions[i], ce1))]
    o3 = a.positions[max([i for i in os_ if lateral(a, a.positions[i], o1) > 0.5 and lateral(a, a.positions[i], o2) > 0.5],
                         key=lambda i: lateral(a, a.positions[i], o1))]
    return {
        "C1_CH4_Ce": [ch4(ce1 + [0, 0, 3.4])],
        "C2_CH4_Os": [ch4(o1 + [0, 0, 2.9])],
        "C3_CH3Ce_HOs": [ch3(ce1 + [0, 0, 2.55]), (None, [o1 + [0, 0, 0.98]])],
        "C4_CH3Os_HOs": [ch3(o1 + [0, 0, 1.43]), (None, [o2 + [0, 0, 0.98]])],
        "C5_CH2Ce_2HOs": [ch2(ce1 + [0, 0, 2.30]), (None, [o1 + [0, 0, 0.98], o2 + [0, 0, 0.98]])],
        "C6_CH2Os_2HOs": [ch2(o1 + [0, 0, 1.42]), (None, [o2 + [0, 0, 0.98], o3 + [0, 0, 0.98]])],
    }


# ---------------------------------------------------------------- input writers
def species(a):
    out = []
    for s in a.get_chemical_symbols():
        if not out or out[-1] != s:
            out.append(s)
    return out


def ldau(syms):
    return ("LDAU = .TRUE.\nLDAUTYPE = 2\n"
            "LDAUL = " + " ".join("3" if s == "Ce" else "-1" for s in syms) + "\n"
            "LDAUU = " + " ".join("5.0" if s == "Ce" else "0.0" for s in syms) + "\n"
            "LDAUJ = " + " ".join("0.0" for _ in syms) + "\nLMAXMIX = 6\n")


def incar(system, syms, stage, kind, d3):
    t = [f"SYSTEM = {system} | {stage}", "PREC = Accurate", "ENCUT = 450", "ISPIN = 2", "ISYM = 0",
         "LREAL = .FALSE.", "LASPH = .TRUE.", "ADDGRID = .TRUE.", "LORBIT = 11", "NELMIN = 4", "AMIN = 0.01",
         "MAXMIX = 40", "AMIX_MAG = 0.4", "BMIX_MAG = 1.0"]
    if kind == "slab":
        smear = ["ISMEAR = 0", "SIGMA = 0.05"] if stage == "stageC_SP" else ["ISMEAR = 1", "SIGMA = 0.10"]
        t += smear + ["IDIPOL = 3", "LDIPOL = .FALSE.", "KPAR = 4", "NCORE = 3"]
    else:
        t += ["ISMEAR = 0", "SIGMA = 0.05", "NCORE = 3"]
    if d3:
        t += ["IVDW = 12"]
    if stage == "stageA_spinSP":
        t += ["ISTART = 0", "ICHARG = 2", "ALGO = All", "NELM = 500", "EDIFF = 1E-5", "IBRION = -1", "NSW = 0"]
    elif stage == "stageB_relax":
        t += ["ISTART = 1", "ICHARG = 1", "ALGO = Normal", "NELM = 300", "EDIFF = 1E-5", "IBRION = 2",
              "POTIM = 0.20", "NSW = 400" if kind == "slab" else "NSW = 150", "ISIF = 2", "EDIFFG = -0.02"]
    elif stage == "stageC_SP":
        t += ["ISTART = 1", "ICHARG = 1", "ALGO = Normal", "NELM = 300", "EDIFF = 1E-6", "IBRION = -1", "NSW = 0"]
    t += ["LWAVE = .TRUE.", "LCHARG = .TRUE."]
    return "\n".join(t) + "\n" + (ldau(syms) if "Ce" in syms else "")


def job(name, stages, kind):
    """Stage-5 PBS script with this set's stages; CONTCAR -> POSCAR before the final single point."""
    s = open(JOB_TEMPLATE).read()
    head, _, _ = s.partition("run_stage stageA_spinSP LABORT scf")
    head = head.replace("#PBS -N s5_C3a_Ce2O3_Rh", "#PBS -N s6_" + name[:12])
    head = head.replace("for f in INCAR_stageA_spinSP INCAR_stageB_relax POSCAR",
                        "for f in " + " ".join("INCAR_" + t for t in stages) + " POSCAR")
    if kind == "gas":
        head = head.replace("mem=200gb", "mem=64gb")
    body = []
    for t in stages:
        if t == "stageC_SP":
            body.append("cp POSCAR POSCAR_start; cp CONTCAR POSCAR")
        body.append("run_stage %s %s %s" % (t, "LSTOP" if t == "stageB_relax" else "LABORT",
                                            "relax" if t == "stageB_relax" else "scf"))
    return head + "\n".join(body) + '\necho "end=$(date --iso-8601=seconds) rc=0"\n'


def gas(sym, pos):
    m = Atoms(sym, positions=pos, cell=[15.0, 15.1, 15.2], pbc=True)
    m.center()
    return m


def check(a):
    """Shortest contact of the adsorbates that is not an intended bond (C-H < 1.2, O-H < 1.05 A are bonds)."""
    d = a.get_all_distances(mic=True)
    ads = [i for i in range(len(a)) if a[i].symbol in ("C", "H")]
    best = (9.9, None)
    for i in ads:
        for j in range(len(a)):
            pair = {a[i].symbol, a[j].symbol}
            bond = (pair == {"C", "H"} and d[i, j] < 1.2) or (pair == {"O", "H"} and d[i, j] < 1.05)
            if j != i and not bond and d[i, j] < best[0]:
                best = (d[i, j], (a[i].symbol, a[j].symbol))
    return best


def write_set(root, name, title, a, kind, mesh, d3):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    write(os.path.join(d, "POSCAR"), a, format="vasp", direct=True, sort=False)
    with open(os.path.join(d, "POSCAR")) as fh:
        body = fh.read().split("\n", 1)[1]
    with open(os.path.join(d, "POSCAR"), "w") as fh:
        fh.write(title + "\n" + body)
    syms = species(a)
    stages = (["stageA_spinSP", "stageB_relax", "stageC_SP"] if kind == "slab"
              else ["stageA_spinSP", "stageB_relax"])
    for t in stages:
        with open(os.path.join(d, "INCAR_" + t), "w") as fh:
            fh.write(incar(title, syms, t, kind, d3))
    with open(os.path.join(d, "KPOINTS"), "w") as fh:
        fh.write("%s\n0\nGamma\n%d %d %d\n0 0 0\n" % (title, *mesh))
    with open(os.path.join(d, "POTCAR.spec"), "w") as fh:
        fh.write("\n".join(syms) + "\n")
    with open(os.path.join(d, "job.pbs"), "w") as fh:
        fh.write(job(name, stages, kind))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layer", help="relaxed 450 eV / ISPIN 2 Ce4O6/Rh(111) 3x3 CONTCAR (Stage-3 S1_31)")
    ap.add_argument("--d3", action="store_true", help="add IVDW = 12 to every system")
    ap.add_argument("--out", default=os.path.join(HERE, "inputs"))
    args = ap.parse_args()
    preview = args.layer is None
    PARENT["C"] = args.layer or PARENT["C"]
    builders = {"A": model_A, "B": model_B, "C": model_C}
    labels = {"A": "Rh(111) p(4x4)", "B": "Ce2O3 cluster C3a/Rh(111) p(4x4)",
              "C": "Ce4O6 layer/Rh(111) p(3x3)" + (" [PREVIEW: round-1 30a parent]" if preview else "")}
    os.makedirs(args.out, exist_ok=True)
    report = []
    for m in "ABC":
        base = load(PARENT[m])
        sets = {k: add(base, v) for k, v in builders[m](base).items()}
        sets = {m + "0_ref": base, **sets}
        zmax = max(s.positions[:, 2].max() for s in sets.values())
        c = round(zmax + VAC, 3)
        for k, s in sets.items():
            s.cell[2] = [0.0, 0.0, c]
            s.set_cell(s.cell, scale_atoms=False)
            title = "%s | %s" % (labels[m], k)
            write_set(args.out, k, title, s, "slab", KMESH[m], args.d3)
            r, pair = check(s) if k != m + "0_ref" else (float("nan"), None)
            line = "%-26s %-18s c=%.3f  zmax=%.3f  vac=%.2f  min(ads)=%.2f %s" % (
                k, s.get_chemical_formula(), c, s.positions[:, 2].max(), c - s.positions[:, 2].max(), r, pair)
            report.append(line)
            print(line)
    gases = {"G_CH4": gas("CH4", [[0, 0, 0], [0.635, 0.635, 0.635], [-0.635, -0.635, 0.635],
                                   [-0.635, 0.635, -0.635], [0.635, -0.635, -0.635]]),
             "G_H2": gas("H2", [[0, 0, 0], [0, 0, 0.75]]),
             "G_CO": gas("CO", [[0, 0, 0], [0, 0, 1.14]]),
             "G_CO2": gas("CO2", [[0, 0, 0], [0, 0, -1.17], [0, 0, 1.17]]),
             "G_H2O": gas("OH2", [[0, 0, 0], [0.76, 0, 0.59], [-0.76, 0, 0.59]])}
    for k, g in gases.items():
        write_set(args.out, k, k + " in a 15 A box", g, "gas", (1, 1, 1), args.d3)
        report.append("%-26s %s" % (k, g.get_chemical_formula()))
    lines = []
    for dp, _, fs in sorted(os.walk(args.out)):
        for f in sorted(fs):
            if f in ("MANIFEST.sha256", "BUILD_REPORT.txt"):
                continue
            p = os.path.join(dp, f)
            lines.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(),
                                     os.path.relpath(p, args.out).replace("\\", "/")))
    with open(os.path.join(args.out, "MANIFEST.sha256"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(os.path.join(args.out, "BUILD_REPORT.txt"), "w") as fh:
        fh.write(("PREVIEW (layer parent = round-1 30a; rebuild with --layer S1_31 CONTCAR before submission)\n"
                  if preview else "layer parent: %s\n" % args.layer) + ("IVDW = 12\n" if args.d3 else "no IVDW\n"))
        fh.write("\n".join(report) + "\n")
    print("wrote %d files to %s" % (len(lines), args.out))


if __name__ == "__main__":
    main()
