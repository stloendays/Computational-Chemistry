"""Stage 7 (2026-10-15 supervisor plan): first CH4 C-H cleavage on four models.

A = Rh(111) p(4x4)              (Stage-6 A sets, unchanged)
B = Ce4O6 layer L6/Rh(111) p(3x3) (Stage-6 C sets, relabelled)
C = Ce2O3 cluster C3a/Rh(111) p(4x4) (Stage-6 B sets, relabelled)
D = Ce2O3 cluster on CeO2(111) p(4x4), new: clean support D0 + three cluster registries D1-D3.
Only first-cleavage sets are kept (no CH2 sets, only the CH4 gas reference).
"""
import os
import shutil
import sys

import numpy as np
from ase import Atoms
from ase.constraints import FixAtoms
from ase.io import read

HERE = os.path.dirname(os.path.abspath(__file__))
S6 = os.path.join(os.path.dirname(HERE), "stage6_DRM_CH4_paths_20261013")
sys.path.insert(0, S6)
import build_stage6 as b6  # noqa: E402

SLAB = os.path.join(HERE, "parents", "CONTCAR_CeO2_111_p4x4_3TL")
S5 = os.path.join(os.path.dirname(HERE), "stage2_interfaces_20260910", "results", "cluster_layer_Eint_20260930")
GAS = os.path.join(S5, "G3_Ce2O3_gas", "CONTCAR")
OUT = os.path.join(HERE, "inputs")

COPY = {  # new name: Stage-6 name
    "A0_ref": "A0_ref", "A1_CH4_top": "A1_CH4_top", "A2_CH3top_Hfcc": "A2_CH3top_Hfcc",
    "B0_ref": "C0_ref", "B1_CH4_Ce": "C1_CH4_Ce", "B2_CH4_Os": "C2_CH4_Os",
    "B3_CH3Ce_HOs": "C3_CH3Ce_HOs", "B4_CH3Os_HOs": "C4_CH3Os_HOs",
    "C0_ref": "B0_ref", "C1_CH4_perimRh": "B1_CH4_perimRh", "C2_CH4_Ce": "B2_CH4_Ce",
    "C3_CH3perimRh_HOt": "B3_CH3perimRh_HOt", "C4_CH3perimRh_Hfcc": "B4_CH3perimRh_Hfcc",
    "C5_CH3Ce_HOt": "B5_CH3Ce_HOt", "C6_CH3farRh_Hfcc": "B6_CH3farRh_Hfcc",
    "G_CH4": "G_CH4",
}
LABEL = {"A": "Rh(111) p(4x4)", "B": "Ce4O6 layer (Stage-4 L6)/Rh(111) p(3x3)",
         "C": "Ce2O3 cluster C3a/Rh(111) p(4x4)", "D": "Ce2O3 cluster/CeO2(111) p(4x4)"}


def relabel(new, old):
    src, dst = os.path.join(S6, "inputs", old), os.path.join(OUT, new)
    shutil.copytree(src, dst)
    for f in os.listdir(dst):
        p = os.path.join(dst, f)
        s = open(p, newline="").read()
        if f == "job.pbs":
            s = s.replace("#PBS -N s6_" + old[:12], "#PBS -N s7_" + new[:12])
        elif not new.startswith("G"):
            s = s.replace("| " + old, "| " + new)
        open(p, "w", newline="\n").write(s)


def support():
    a = read(SLAB, format="vasp")
    a.positions[:, 2] -= a.positions[:, 2].min()            # bottom O plane -> z = 0
    a.wrap()
    return a


def hollows(a):
    """Three-fold hollows of the top O plane: over a top-trilayer Ce ('hCe') and over the next O ('hO')."""
    z = a.positions[:, 2]
    top_o = [i for i in range(len(a)) if a[i].symbol == "O" and z[i] > z.max() - 0.3]
    ce1 = [i for i in range(len(a)) if a[i].symbol == "Ce" and z[i] > z.max() - 1.2]
    o2 = [i for i in range(len(a)) if a[i].symbol == "O" and z.max() - 2.0 < z[i] < z.max() - 1.2]
    ztop = z[top_o].mean()
    return ztop, a.positions[ce1[0], :2], a.positions[o2[0], :2]


def sites(origin, cell):
    return [origin + i * cell[0, :2] / 4 + j * cell[1, :2] / 4 for i in range(-5, 6) for j in range(-5, 6)]


def cluster_flat(c1, c2, h, oside, hb, n_down):
    """Ce2O3 with both Ce over hO hollows c1, c2. n_down O sit in the hCe hollows closest to the Ce-Ce midpoint
    (fluorite-like next O plane, height hb); the rest sit on top as apex O (C3a-like when n_down = 2)."""
    m = (c1 + c2) / 2
    ce = [np.r_[c1, h], np.r_[c2, h]]
    low = sorted(oside, key=lambda q: np.linalg.norm(q - m))[:n_down]
    o = [np.r_[q, hb] for q in low]
    u = (c2 - c1) / np.linalg.norm(c2 - c1)
    v = np.array([-u[1], u[0]])
    if n_down == 2:
        o.append(np.r_[m, h + 2.0])
    else:
        w = -v if np.dot(low[0] - m, v) > 0 else v                     # top O on the side away from the low O
        o += [np.r_[c1 + 0.9 * w, h + 1.9], np.r_[c2 + 0.9 * w, h + 1.9]]
    return ce, o


def cluster_gas(centre, h):
    """Relaxed gas-phase Ce2O3, Ce-Ce axis in plane, centroid at height h."""
    g = read(GAS, format="vasp")
    x = g.positions - g.positions.mean(0)
    ce = x[[i for i in range(len(g)) if g[i].symbol == "Ce"]]
    ax = ce[1] - ce[0]
    g2 = Atoms(g.get_chemical_symbols(), positions=x)
    g2.rotate(ax, [1, 0, 0])
    p = g2.positions + np.r_[centre, h]
    return [p[i] for i in range(len(g2)) if g2[i].symbol == "Ce"], [p[i] for i in range(len(g2)) if g2[i].symbol == "O"]


def place(a, ce, o):
    fixed = list(a.constraints[0].index)
    b = a.copy()
    b.set_constraint()
    syms = b.get_chemical_symbols()
    pos = list(b.positions)
    # keep species blocks Ce, O: insert new Ce after the last Ce
    nce = syms.count("Ce")
    first_o = syms.index("O")
    assert syms[:nce] == ["Ce"] * nce and first_o == nce
    new_syms = ["Ce"] * (nce + len(ce)) + ["O"] * (len(syms) - nce + len(o))
    new_pos = pos[:nce] + list(ce) + pos[nce:] + list(o)
    fixed = [i if i < nce else i + len(ce) for i in fixed]
    c = Atoms(new_syms, positions=new_pos, cell=b.cell, pbc=True)
    c.set_constraint(FixAtoms(indices=fixed))
    return c


def mind(a, idx):
    d = a.get_all_distances(mic=True)
    best = 9.9
    for i in idx:
        for j in range(len(a)):
            if j != i:
                best = min(best, d[i, j])
    return best


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    for new, old in COPY.items():
        relabel(new, old)
    s = support()
    ztop, hce, ho = hollows(s)
    a1 = s.cell[0, :2]
    h = ztop + 1.0
    sets = {"D0_CeO2_111": s,
            "D1_Ce2O3_hO_2Odown": place(s, *cluster_flat(ho, ho + a1 / 4, h, sites(hce, s.cell), h + 0.3, 2)),
            "D2_Ce2O3_hO_1Odown": place(s, *cluster_flat(ho, ho + a1 / 4, h, sites(hce, s.cell), h + 0.3, 1)),
            "D3_Ce2O3_gasgeom": place(s, *cluster_gas((hce + ho) / 2 + a1 / 8, ztop + 3.0))}
    zmax = max(x.positions[:, 2].max() for x in sets.values())
    c = round(zmax + b6.VAC, 3)
    report = []
    for k, x in sets.items():
        x.cell[2] = [0.0, 0.0, c]
        x.set_cell(x.cell, scale_atoms=False)
        b6.write_set(OUT, k, "%s | %s" % (LABEL["D"], k), x, "slab", (2, 2, 1), False)
        p = os.path.join(OUT, k, "job.pbs")
        t = open(p).read().replace("#PBS -N s6_" + k[:12], "#PBS -N s7_" + k[:12])
        open(p, "w", newline="\n").write(t)
        new = list(range(48, 50)) + list(range(len(x) - 3, len(x))) if k != "D0_CeO2_111" else []
        line = "%-22s %-10s c=%.3f zmax=%.3f vac=%.2f fixed=%d min(cluster)=%.2f" % (
            k, x.get_chemical_formula(), c, x.positions[:, 2].max(), c - x.positions[:, 2].max(),
            len(x.constraints[0].index), mind(x, new) if new else float("nan"))
        report.append(line)
        print(line)
    import hashlib
    lines = []
    for dp, _, fs in sorted(os.walk(OUT)):
        for f in sorted(fs):
            pth = os.path.join(dp, f)
            raw = open(pth, "rb").read()
            if b"\r\n" in raw:
                open(pth, "wb").write(raw.replace(b"\r\n", b"\n"))
            lines.append("%s  %s" % (hashlib.sha256(open(pth, "rb").read()).hexdigest(),
                                     os.path.relpath(pth, OUT).replace("\\", "/")))
    open(os.path.join(OUT, "MANIFEST.sha256"), "w", newline="\n").write("\n".join(lines) + "\n")
    open(os.path.join(OUT, "BUILD_REPORT.txt"), "w", newline="\n").write(
        "A/B/C copied from Stage-6 inputs (B<->C relabelled); D support = parents/CONTCAR_CeO2_111_p4x4_3TL\n"
        + "\n".join(report) + "\n")


if __name__ == "__main__":
    main()
