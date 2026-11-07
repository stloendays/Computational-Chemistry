"""NEB endpoints with a physically possible H transfer (2026-11-05, user: "B 一起重建").

Supervisor plan 10-15, sec. 3.1: IS and FS must allow a physically possible H transfer; repair endpoints before the
NEB. Built straight from the lowest CH4* to the lowest FS, the B path (1502824) had to move one H by 4.3 A while the
C-H bond in the IS pointed away from the acceptor O (157 deg). Images 03/05 then held a free H or CH3 radical
(+4.0/+4.5 eV, 0.30/0.34 muB on H/C). C1 -> C3 and D5 -> D7 have the same geometry problem.

Repairs (one NEB path per model; the energy table keeps the lowest CH4* and the lowest FS):
  B5_CH4_toB4         IS for B4: CH4 above O40 (methoxy O of B4), the breaking C-H pointing at O45 (H acceptor)
  C9_CH3perimRh_HOp   adjacent FS on C: CH3 on perimeter Rh33 as in C3, H on the interface O38 next to it
                      (C3 puts H on the top O40, 5.65 A from Rh33: not one elementary step)
  C10_CH4_toC9        IS for C9: CH4 above Rh33, the breaking C-H pointing at O38
  D9_CH4_toD7         IS for D7: CH4 above O40, the breaking C-H pointing at O38
The breaking H keeps its atom index in IS and FS, so the NEB moves that H and no other.
Inputs: build_3x3.write_set (stage A + relaxation, U on Ce only), the cell of each model's FS CONTCAR.
"""
import os
import sys

import numpy as np
from ase.io import read

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_3x3 as b3  # noqa: E402

RAW3 = os.path.join(HERE, "results", "raw_3x3")
RAWB = os.path.join(HERE, "results", "raw")
LABEL = {"B": "Ce4O6 layer/Rh(111) p(3x3)", "C": b3.LABEL["C"], "D": b3.LABEL["D"]}
D_CH = 1.10


def load(path):
    a = read(path, format="vasp")
    cons = a.constraints
    a.arrays.pop("momenta", None)
    a.set_constraint(cons)
    return a


def rot_to(u, v):
    """Rotation matrix taking unit vector u onto unit vector v."""
    u, v = u / np.linalg.norm(u), v / np.linalg.norm(v)
    w = np.cross(u, v)
    s, c = np.linalg.norm(w), u @ v
    if s < 1e-8:
        return np.eye(3) if c > 0 else -np.eye(3) + 2 * np.outer([1, 0, 0], [1, 0, 0])
    k = np.array([[0, -w[2], w[1]], [w[2], 0, -w[0]], [-w[1], w[0], 0]]) / s
    return np.eye(3) + s * k + (1 - c) * k @ k


def ch4_pointing(c, u):
    """Tetrahedral CH4 at c with its first C-H along u (the breaking bond); returns 4 H positions, first = H_break."""
    base = [np.array([0, 0, -D_CH])] + [np.array([D_CH * 0.9428 * np.cos(t), D_CH * 0.9428 * np.sin(t), D_CH / 3])
                                         for t in (0, 2 * np.pi / 3, 4 * np.pi / 3)]
    r = rot_to(np.array([0, 0, -1.0]), u)
    return [c + r @ b for b in base]


def mic_vec(a, i, p):
    """Minimum-image vector from atom i to point p."""
    d = p - a.positions[i]
    f = np.linalg.solve(a.cell.T, d)
    f[:2] -= np.round(f[:2])
    return a.cell.T @ f


def is_from_fs(fs, x, acc, h_break, d_cx=3.3):
    """IS for a given FS. The CH4 carbon sits above the midpoint of x (the atom CH3 binds in the FS) and the H
    acceptor, at the height where it is d_cx from both, raised in 0.1 A steps until C is >= 3.1 A from every heavy
    atom and every H is >= 2.2 A from the slab; the breaking C-H points at the acceptor, and the other three H are
    rotated about that bond to the most open setting. C and H keep their FS indices; h_break is the breaking H."""
    a = fs.copy()
    sym = a.get_chemical_symbols()
    c = sym.index("C")
    hs = [i for i, s in enumerate(sym) if s == "H"]
    xa = a.positions[x]
    aa = xa + mic_vec(a, x, a.positions[acc])
    mid = (xa + aa) / 2
    half = np.linalg.norm(aa - xa) / 2
    slab = [j for j in range(len(a)) if j != c and j not in hs]
    heavy = [j for j in slab if sym[j] != "H"]
    cell = np.array(a.cell)

    def dmin(p, idx):
        best = 1e9
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                sh = i * cell[0] + j * cell[1]
                best = min(best, np.min(np.linalg.norm(a.positions[idx] + sh - p, axis=1)))
        return best
    h0 = np.sqrt(max(d_cx ** 2 - half ** 2, 0.0)) + max(xa[2], aa[2]) - mid[2]
    for dh in np.arange(0, 3.01, 0.1):
        pc = mid + np.array([0, 0, h0 + dh])
        u = aa - pc
        u /= np.linalg.norm(u)
        best = None
        for t in np.radians(np.arange(0, 120, 10)):
            hp = ch4_pointing(pc, u)
            r = rot_to(np.array([0, 0, 1.0]), u)
            # rotate the three non-breaking H about u by t
            k = np.array([[0, -u[2], u[1]], [u[2], 0, -u[0]], [-u[1], u[0], 0]])
            rt = np.eye(3) + np.sin(t) * k + (1 - np.cos(t)) * k @ k
            hp = [hp[0]] + [pc + rt @ (q - pc) for q in hp[1:]]
            dh_ = min(dmin(q, slab) for q in hp)
            if best is None or dh_ > best[0]:
                best = (dh_, hp)
        if dmin(pc, heavy) >= 3.1 and best[0] >= 2.2:
            break
    a.positions[c] = pc
    a.positions[h_break] = best[1][0]
    for h, q in zip([h for h in hs if h != h_break], best[1][1:]):
        a.positions[h] = q
    return a


def is_at(fs, pc, acc, h_break):
    """IS with the carbon at pc, the breaking C-H pointing at acc, the other three H rotated to the most open
    setting (same rule as is_from_fs, fixed carbon position)."""
    a = fs.copy()
    sym = a.get_chemical_symbols()
    c = sym.index("C")
    hs = [i for i, s in enumerate(sym) if s == "H"]
    slab = [j for j in range(len(a)) if j != c and j not in hs]
    u = (pc + mic_vec(a, acc, pc) * -1) - pc
    u /= np.linalg.norm(u)
    best = None
    k = np.array([[0, -u[2], u[1]], [u[2], 0, -u[0]], [-u[1], u[0], 0]])
    for t in np.radians(np.arange(0, 120, 10)):
        hp = ch4_pointing(pc, u)
        rt = np.eye(3) + np.sin(t) * k + (1 - np.cos(t)) * k @ k
        hp = [hp[0]] + [pc + rt @ (q - pc) for q in hp[1:]]
        d = min(np.linalg.norm(mic_vec(a, j, q)) for q in hp for j in slab)
        if best is None or d > best[0]:
            best = (d, hp)
    a.positions[c] = pc
    a.positions[h_break] = best[1][0]
    for h, q in zip([h for h in hs if h != h_break], best[1][1:]):
        a.positions[h] = q
    return a


def contacts(a):
    """Shortest C-X and H-X distances to atoms other than the CH_n group (O-H < 1.05 A counted as a bond)."""
    s = a.get_chemical_symbols()
    c = s.index("C")
    d = a.get_all_distances(mic=True)
    grp = [c] + [h for h in range(len(a)) if s[h] == "H" and d[c, h] < 1.3]
    rest = [j for j in range(len(a)) if j not in grp]
    dc = min(d[c, j] for j in rest if not (s[j] == "H"))
    dh = min(d[h, j] for h in grp[1:] for j in rest if not (s[j] == "O" and d[h, j] < 1.05))
    return dc, dh


def main():
    rep = []
    sets = {}
    # B: IS for B4 (B4 relaxed, results/raw = stage-B CONTCARs of the 10-xx B runs)
    b4 = load(os.path.join(RAWB, "B4_CH3Os_HOs", "CONTCAR"))
    s = b4.get_chemical_symbols()
    hb = max([i for i, x in enumerate(s) if x == "H"], key=lambda h: b4.get_distance(s.index("C"), h, mic=True))
    acc_b = min([i for i, x in enumerate(s) if x == "O"], key=lambda o: b4.get_distance(hb, o, mic=True))
    sets["B5_CH4_toB4"] = ("B", is_from_fs(b4, 40, acc_b, hb), "IS for B4: C above O40/O%d midpoint, C-H -> O%d" % (acc_b, acc_b) if False else "IS for B4: C above O40-O%d, C-H -> O%d" % (acc_b, acc_b))
    # C: adjacent FS (H on interface O38) and its IS
    c3 = load(os.path.join(RAW3, "C3_CH3perimRh_HOt", "CONTCAR"))
    s = c3.get_chemical_symbols()
    cc = s.index("C")
    hc = max([i for i, x in enumerate(s) if x == "H"], key=lambda h: c3.get_distance(cc, h, mic=True))
    c9 = c3.copy()
    # H on O38 pointing up and away from its Ce/Rh neighbours (same rule as build_D_3x3_endpoints.up_away)
    v = -sum(mic_vec(c9, 38, c9.positions[j]) for j in range(len(c9))
             if j != 38 and s[j] in ("Ce", "Rh") and c9.get_distance(38, j, mic=True) < 2.8)
    v[2] = 0
    v /= np.linalg.norm(v)
    u = 0.6 * v + np.array([0, 0, 0.8])
    c9.positions[hc] = c9.positions[38] + 0.98 * u / np.linalg.norm(u)
    sets["C9_CH3perimRh_HOp"] = ("C", c9, "adjacent FS: CH3 on Rh33 (C3 geometry), H on interface O38")
    # above the Rh33-O38 pair the cluster Ce36 is in the way; the carbon takes its place in the relaxed C1 instead
    # (4.48 A above Rh33), and the CH4 is turned so that the breaking C-H points at O38
    c1 = load(os.path.join(RAW3, "C1_CH4_perimRh", "CONTCAR"))
    s1 = c1.get_chemical_symbols()
    v_c1 = mic_vec(c1, 33, c1.positions[s1.index("C")])
    sets["C10_CH4_toC9"] = ("C", is_at(c9, c9.positions[33] + v_c1, 38, hc), "IS for C9: C as in C1, C-H -> O38")
    # D: IS for D7
    d7 = load(os.path.join(RAW3, "D7_CH3Oc_HOc", "CONTCAR"))
    s = d7.get_chemical_symbols()
    hd = max([i for i, x in enumerate(s) if x == "H"], key=lambda h: d7.get_distance(s.index("C"), h, mic=True))
    sets["D9_CH4_toD7"] = ("D", is_from_fs(d7, 40, 38, hd), "IS for D7: C above O40-O38, C-H -> O38")

    for name, (m, a, what) in sets.items():
        top = c_cell = a.cell[2, 2]
        b3.write_set(name, "%s | %s" % (LABEL[m], name), a)
        dc, dh = contacts(a)
        s = a.get_chemical_symbols()
        rep.append("%-19s %-14s %s | natoms=%d fixed=%d c=%.3f vac=%.2f | min C-X %.2f, min H-X %.2f" % (
            name, a.get_chemical_formula(), what, len(a), len(a.constraints[0].index), c_cell,
            c_cell - a.positions[:, 2].max(), dc, dh))
    open(os.path.join(b3.OUT, "BUILD_REPORT_neb_endpoints_20261105.txt"), "w", newline="\n").write("\n".join(rep) + "\n")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
