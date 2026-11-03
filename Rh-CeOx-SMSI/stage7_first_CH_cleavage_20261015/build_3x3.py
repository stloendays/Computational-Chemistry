"""Stage 7 rebuild after the supervisor's guidance of 2026-10-29 (Notion 14, PLAN_20261029_advisor_3x3.md).

A = Rh(111) p(3x3)                       parent: Stage-4 L0_Rh111_3x3 CONTCAR (450 eV, ISPIN 2)
C = Ce2O3 cluster C3a/Rh(111) p(3x3)     cluster of the relaxed C0_ref (p(4x4)) moved onto L0 at the same registry
D = Ce2O3 cluster/CeO2(111) p(2x2) 3 TL  support cut from the relaxed D0 p(4x4) slab (proposed / preliminary);
                                         the three cluster starts are the D1-D3 clusters at the same registry
B (p(3x3)) is unchanged and not rebuilt.

Sites follow the 10-15 sets (Stage-6 site logic) plus the two cluster-top-O sets of 10-29 (C7, C8).
No separate final single point (supervisor, 10-29): stage A spin pre-convergence, then the relaxation; the
reported energy is E0 (sigma -> 0) of the converged relaxation. INCAR/KPOINTS/job are the B0_ref set
(Gamma 4x4x1) without stage C. One c per model: tallest start + 15 A, bottom atom plane at z = 0.
"""
import os
import re
import sys

import numpy as np
from ase.constraints import FixAtoms
from ase.geometry import find_mic
from ase.io import read, write

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "DynSMSI_stage6_DRM_CH4_paths_20261013"))
import build_stage6 as b6  # noqa: E402

OUT = os.path.join(HERE, "inputs_3x3")
L0 = os.path.join(ROOT, "DynSMSI_stage4_Ce4Ox_layers_20260928", "results", "contcars", "L0_Rh111_3x3_CONTCAR")
RAW = os.path.join(HERE, "results", "raw")
TEMPLATE = os.path.join(HERE, "inputs", "B0_ref")
VAC = 15.0
LABEL = {"A": "Rh(111) p(3x3)", "C": "Ce2O3 cluster C3a/Rh(111) p(3x3)",
         "D": "Ce2O3 cluster/CeO2(111) p(2x2) 3TL"}


def clean_read(path):
    a = read(path, format="vasp")
    a.arrays.pop("momenta", None)
    return a


def top_rh_near(a, xy):
    top, _ = b6.rh_layers(a)
    return top[np.argmin([b6.lateral(a, a.positions[i], np.r_[xy, 0]) for i in top])]


def is_fcc_offset(a, i):
    """True if top Rh i + (e1+e2)/3 is an fcc hollow (no 2nd-layer Rh below); fixes the stacking sense."""
    _, sec = b6.rh_layers(a)
    n = int(round(np.linalg.norm(a.cell[0]) / 2.70))
    q = a.positions[i] + (a.cell[0] + a.cell[1]) / n / 3
    return min(b6.lateral(a, q, a.positions[k]) for k in sec) > 0.8


# ---------------------------------------------------------------- parents
def parent_A():
    return b6.load(L0)


def parent_C():
    """Move the relaxed C0_ref cluster (5 atoms) onto L0 with the same registry to a top-layer Rh."""
    src = clean_read(os.path.join(RAW, "C0_ref", "CONTCAR"))
    src.positions[:, 2] -= src.positions[src.numbers == 45, 2].min()
    ox = list(b6.oxide(src))
    d, _ = find_mic(src.positions[ox] - src.positions[ox[0]], src.cell, pbc=True)
    cl = src.positions[ox[0]] + d
    r_src = top_rh_near(src, cl[:, :2].mean(0))
    base = b6.load(L0)
    r_dst = top_rh_near(base, base.cell[:2, :2].sum(0) / 2)
    assert is_fcc_offset(src, r_src) == is_fcc_offset(base, r_dst), "stacking differs between the two slabs"
    shift = base.positions[r_dst] - src.positions[r_src]
    ztop_src = src.positions[b6.rh_layers(src)[0], 2].mean()
    ztop_dst = base.positions[b6.rh_layers(base)[0], 2].mean()
    shift[2] = ztop_dst - ztop_src
    fixed = list(base.constraints[0].index)
    base.set_constraint()
    syms = src.get_chemical_symbols()
    from ase import Atoms
    for s in ("Ce", "O"):
        idx = [k for k, i in enumerate(ox) if syms[i] == s]
        base += Atoms(s + str(len(idx)), positions=cl[idx] + shift, cell=base.cell, pbc=True)
    base.set_constraint(FixAtoms(indices=fixed))
    # translate the whole slab so the cluster centroid sits at the cell centre (pure relabelling of the origin)
    ox = b6.oxide(base)
    d, _ = find_mic(base.positions[ox] - base.positions[ox[0]], base.cell, pbc=True)
    cen = (base.positions[ox[0]] + d).mean(0)
    mid = (base.cell[0] + base.cell[1]) / 2
    base.positions[:, :2] += (mid - cen)[:2]
    base.wrap()
    return base


def support_2x2():
    """CeO2(111) p(2x2) 3 TL from the relaxed p(4x4) D0 slab: fold the 144 atoms into the half cell (the p(2x2)
    lattice is a sublattice of p(4x4)), group the four equivalent copies of each atom and average them."""
    s = clean_read(os.path.join(RAW, "D0_CeO2_111", "CONTCAR"))
    fixed = set(s.constraints[0].index) if s.constraints else set()
    half = np.array([s.cell[0] / 2, s.cell[1] / 2, s.cell[2]])
    f = s.get_scaled_positions(wrap=True)
    groups = []
    for i in range(len(s)):
        g2 = (f[i, :2] * 2) % 1.0
        for g in groups:
            d = g2 - g["f"]
            d -= np.round(d)
            if s[i].symbol == g["sym"] and np.linalg.norm(d @ half[:2, :2]) < 0.6 and abs(s.positions[i, 2] - g["z"]) < 0.6:
                g["m"].append(i)
                break
        else:
            groups.append({"f": g2, "z": s.positions[i, 2], "sym": s[i].symbol, "m": [i]})
    assert all(len(g["m"]) == 4 for g in groups) and len(groups) == len(s) // 4, [len(g["m"]) for g in groups]
    from ase import Atoms
    pos, sym, fx = [], [], []
    for k, g in enumerate(groups):
        ref = g["f"]
        dd = []
        for i in g["m"]:
            d = (f[i, :2] * 2) % 1.0 - ref
            d -= np.round(d)
            dd.append(d)
        fxy = ref + np.mean(dd, axis=0)
        pos.append(np.r_[fxy @ half[:2, :2], np.mean(s.positions[g["m"], 2])])
        sym.append(g["sym"])
        if any(i in fixed for i in g["m"]):
            fx.append(k)
    order = [k for k in range(len(sym)) if sym[k] == "Ce"] + [k for k in range(len(sym)) if sym[k] == "O"]
    b = Atoms([sym[k] for k in order], positions=[pos[k] for k in order], cell=half, pbc=True)
    b.set_constraint(FixAtoms(indices=[n for n, k in enumerate(order) if k in fx]))
    b.positions[:, 2] -= b.positions[:, 2].min()
    b.wrap()
    return b


def parent_D(cluster_src):
    """Clean p(2x2) support + the Ce2O3 cluster of a p(4x4) D parent (last 2 Ce and last 3 O), same registry."""
    sup = support_2x2()
    s = clean_read(cluster_src)
    d0 = clean_read(os.path.join(RAW, "D0_CeO2_111", "CONTCAR"))
    zshift = -d0.positions[:, 2].min()                               # the p(4x4) parents share D0's z frame
    sym = np.array(s.get_chemical_symbols())
    ce = np.where(sym == "Ce")[0][-2:]
    o = np.where(sym == "O")[0][-3:]
    idx = list(ce) + list(o)
    d, _ = find_mic(s.positions[idx] - s.positions[idx[0]], s.cell, pbc=True)
    cl = s.positions[idx[0]] + d
    cl[:, 2] += zshift
    fixed = list(sup.constraints[0].index)
    sup.set_constraint()
    from ase import Atoms
    a = sup.copy()
    a += Atoms("Ce2", positions=cl[:2], cell=a.cell, pbc=True)
    a += Atoms("O3", positions=cl[2:], cell=a.cell, pbc=True)
    order = [i for i in range(len(a)) if a[i].symbol == "Ce"] + [i for i in range(len(a)) if a[i].symbol == "O"]
    fx = set(fixed)
    a = a[order]
    a.set_constraint(FixAtoms(indices=[k for k, i in enumerate(order) if i in fx]))
    a.wrap()
    return a


# ---------------------------------------------------------------- end-state sets
def sets_A(base):
    s = b6.model_A(base)
    return {"A0_ref": base, **{k: b6.add(base, v) for k, v in s.items() if not k.startswith("A3")}}


def sets_C(base):
    # Stage-6 model_B site logic without the CH2 sets (their second and third free fcc hollows do not fit in 3x3)
    a = base
    top, _ = b6.rh_layers(a)
    fcc, _ = b6.fcc_hollows(a)
    ox = b6.oxide(a)
    sym = np.array(base.get_chemical_symbols())
    o = np.where(sym == "O")[0]
    ce = np.where(sym == "Ce")[0]
    o_t = max(o, key=lambda i: base.positions[i, 2])
    cen = a.positions[ox].mean(axis=0)
    per = [i for i in top if 2.6 < min(b6.lateral(a, a.positions[i], a.positions[k]) for k in ox) < 3.6]
    rp = a.positions[min(per, key=lambda i: b6.lateral(a, a.positions[i], a.positions[ce[0]]))]
    free_fcc = [f for f in fcc if b6.free_of_oxide(a, f, 2.4)]
    hp = b6.nearest(free_fcc, rp, a)
    far = a.positions[max(top, key=lambda i: b6.lateral(a, a.positions[i], cen))]
    hfar = b6.nearest([f for f in free_fcc if b6.lateral(a, f, far) > 1.0], far, a)
    ce_top = a.positions[max(ce, key=lambda i: a.positions[i, 2])]
    away = ce_top[:2] - a.positions[o_t, :2]
    away = np.array([*(0.6 * away / np.linalg.norm(away)), 0.8])
    ot = a.positions[o_t]
    s = {"C1_CH4_perimRh": b6.add(a, [b6.ch4(rp + [0, 0, 3.2])]),
         "C2_CH4_Ce": b6.add(a, [b6.ch4(ce_top + [0, 0, 3.4])]),
         "C3_CH3perimRh_HOt": b6.add(a, [b6.ch3(rp + [0, 0, 2.06]), (None, [ot + [0, 0, 0.98]])]),
         "C4_CH3perimRh_Hfcc": b6.add(a, [b6.ch3(rp + [0, 0, 2.06]), (None, [hp + [0, 0, 0.95]])]),
         "C5_CH3Ce_HOt": b6.add(a, [b6.ch3(ce_top + 2.55 * away), (None, [ot + [0, 0, 0.98]])]),
         }
    # C6 (CH3 on a Rh far from the cluster) is not built: in p(3x3) the farthest top Rh is a perimeter Rh and the
    # set came out identical to C4.
    ob = min(i for i in o if i != o_t)
    out = base.positions[ob, :2] - base.positions[np.r_[ce, o], :2].mean(0)
    out /= np.linalg.norm(out)
    h_ob = base.positions[ob] + 0.98 * np.array([out[0], out[1], 1.0]) / np.sqrt(2)
    s["C7_CH4_Ot"] = b6.add(base, [b6.ch4(base.positions[o_t] + [0, 0, 2.9])])
    s["C8_CH3Ot_HOb"] = b6.add(base, [b6.ch3(base.positions[o_t] + [0, 0, 1.43]), (None, [h_ob])])
    return {"C0_ref": base, **dict(sorted(s.items()))}


def sets_D():
    return {"D0_CeO2_111_p2x2": support_2x2(),
            "D1_Ce2O3_hO_2Odown": parent_D(os.path.join(RAW, "D1_Ce2O3_hO_2Odown", "CONTCAR")),
            # D2 is not carried over: its (unconverged) p(4x4) cluster has spread, and in p(2x2) it comes within
            # 2.16 A of its own image, i.e. it would no longer be an isolated cluster.
            "D3_Ce2O3_gasgeom": parent_D(os.path.join(HERE, "parents", "CONTCAR_D3_p4x4_relaxed"))}


# ---------------------------------------------------------------- writers
def job_text(name):
    t = open(os.path.join(TEMPLATE, "job.pbs")).read()
    t = t.replace("#PBS -N s7_B0_ref", "#PBS -N " + ("s73_" + name)[:15])
    t = t.replace(" INCAR_stageC_SP", "")
    t = t.replace("cp POSCAR POSCAR_start; cp CONTCAR POSCAR\nrun_stage stageC_SP LABORT scf\n", "")
    assert "stageC" not in t and "s73_" in t
    return t


def ldau_lines(txt, syms):
    """The B0 template carries LDAU for its own species (Rh Ce O). Rewrite the per-species lists for syms:
    U = 5 eV on Ce 4f only; with no Ce the LDAU block is dropped, as in the 4x4 Rh inputs."""
    keep = [l for l in txt.split("\n") if not re.match(r"\s*(LDAU|LMAXMIX)", l)]
    if "Ce" in syms:
        keep += ["LDAU = .TRUE.", "LDAUTYPE = 2",
                 "LDAUL = " + " ".join("3" if s == "Ce" else "-1" for s in syms),
                 "LDAUU = " + " ".join("5.0" if s == "Ce" else "0.0" for s in syms),
                 "LDAUJ = " + " ".join("0.0" for s in syms), "LMAXMIX = 6"]
    return "\n".join(l for l in keep if l.strip()) + "\n"


def write_set(name, title, a):
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    write(os.path.join(d, "POSCAR"), a, format="vasp", direct=True, sort=False)
    body = open(os.path.join(d, "POSCAR")).read().split("\n", 1)[1]
    open(os.path.join(d, "POSCAR"), "w", newline="\n").write(title + "\n" + body)
    syms = []
    for s in a.get_chemical_symbols():
        if s not in syms:
            syms.append(s)
    for t in ("stageA_spinSP", "stageB_relax"):
        txt = open(os.path.join(TEMPLATE, "INCAR_" + t)).read().split("\n", 1)[1]
        open(os.path.join(d, "INCAR_" + t), "w", newline="\n").write("SYSTEM = %s | %s\n" % (title, t) +
                                                                      ldau_lines(txt, syms))
    open(os.path.join(d, "KPOINTS"), "w", newline="\n").write("%s\n0\nGamma\n4 4 1\n0 0 0\n" % title)
    open(os.path.join(d, "POTCAR.spec"), "w", newline="\n").write("\n".join(syms) + "\n")
    open(os.path.join(d, "job.pbs"), "w", newline="\n").write(job_text(name))


def min_image_dist(a, idx, cut=2.7):
    """Nearest distance between the group idx and its lateral periodic images. The group is unwrapped along its
    bond graph (cut-off 2.7 A), so a cluster wider than half the cell stays in one piece."""
    if not idx:
        return float("nan")
    g = {idx[0]: a.positions[idx[0]].copy()}
    todo = [idx[0]]
    while todo:
        i = todo.pop()
        for j in idx:
            if j in g:
                continue
            d, dl = find_mic(a.positions[j] - a.positions[i], a.cell, pbc=True)
            if dl < cut:
                g[j] = g[i] + d
                todo.append(j)
    for j in idx:                                     # fragments not bonded to the rest: nearest image
        if j not in g:
            d, _ = find_mic(a.positions[j] - a.positions[idx[0]], a.cell, pbc=True)
            g[j] = a.positions[idx[0]] + d
    g = np.array([g[j] for j in idx])
    best = 1e9
    for p in (-1, 0, 1):
        for q in (-1, 0, 1):
            if (p, q) != (0, 0):
                sh = p * a.cell[0] + q * a.cell[1]
                best = min(best, np.min(np.linalg.norm(g[:, None, :] + sh - g[None, :, :], axis=2)))
    return best


def main():
    groups = {"A": sets_A(parent_A()), "C": sets_C(parent_C()), "D": sets_D()}
    report = []
    for m, sets in groups.items():
        c = round(max(s.positions[:, 2].max() for s in sets.values()) + VAC, 3)
        for k, s in sets.items():
            s.cell[2] = [0.0, 0.0, c]
            s.set_cell(s.cell, scale_atoms=False)
            write_set(k, "%s | %s" % (LABEL[m], k), s)
            r, pair = b6.check(s) if any(x in s.get_chemical_symbols() for x in ("C",)) else (float("nan"), None)
            grp = [i for i in range(len(s)) if s[i].symbol in ("Ce", "O")] if m == "C" else                 [i for i in range(len(s)) if s[i].symbol in ("C", "H")] if m == "A" else                 [i for i in range(len(s)) if i >= len(s) - 5 or False]
            if m == "D":
                sym = s.get_chemical_symbols()
                ce = [i for i in range(len(s)) if sym[i] == "Ce"]
                o = [i for i in range(len(s)) if sym[i] == "O"]
                grp = (ce[-2:] + o[-3:]) if len(s) > 36 else []
            img = min_image_dist(s, grp)
            line = "%-22s %-16s natoms=%3d fixed=%2d c=%.3f vac=%.2f min_nonbond=%.2f %s img(ads)=%.2f" % (
                k, s.get_chemical_formula(), len(s), len(s.constraints[0].index), c, c - s.positions[:, 2].max(),
                r, pair, img)
            report.append(line)
            print(line)
    open(os.path.join(OUT, "BUILD_REPORT.txt"), "w", newline="\n").write("\n".join(report) + "\n")


if __name__ == "__main__":
    main()
