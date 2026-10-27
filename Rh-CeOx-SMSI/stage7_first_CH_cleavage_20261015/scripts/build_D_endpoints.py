"""Stage 7, model D endpoints (2026-10-25): CH4* (IS) and CH3* + OH* (FS) on the lowest Ce2O3/CeO2(111) parent.

Supervisor plan 2026-10-15, model D: "cluster-support edge and accessible Ce/O; optimize CH3* + OH* (and plausible
alternatives)". Two CH4 starts and three dissociated starts, the same site logic as models B and C:

  D4_CH4_Ce        CH4 over the upper cluster Ce                         (as C2_CH4_Ce)
  D5_CH4_edge      CH4 over the exposed support O next to the cluster    (as B2_CH4_Os)
  D6_CH3Ce_HOc     CH3 on cluster Ce + H on the top cluster O            (as C5_CH3Ce_HOt)
  D7_CH3Os_HOc     CH3 on the edge support O (methoxy) + H on cluster O  (as B4_CH3Os_HOs)
  D8_CH3Ce_HOs     CH3 on cluster Ce + H on the edge support O

Parent: CONTCAR of the D1-D3 start with the lowest final single point (choose_parent). Cluster atoms keep the
indices given by build_stage7.place(): Ce 48-49, O = last three atoms of the parent.
Settings follow the D parents (user, 2026-10-17): stage A and B at the Gamma point (KPAR 1, NCORE 6),
final single point 2x2x1 (ISTART 0, ICHARG 1); otherwise the project INCAR (ENCUT 450, U 5, ISPIN 2,
ISMEAR 1/0.10 relax, 0/0.05 final). Fixed atoms are taken from the parent.

    python build_D_endpoints.py <parent CONTCAR> <out dir> [--tag preview]
"""
import argparse
import os
import re
import sys

import numpy as np
from ase.io import read

HERE = os.path.dirname(os.path.abspath(__file__))
# build_stage7 points at the pre-rename Stage-6 folder; the folder is now DynSMSI_stage6_DRM_CH4_paths_20261013
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "DynSMSI_stage6_DRM_CH4_paths_20261013"))
import build_stage7 as b7  # noqa: E402

b6 = b7.b6
# the Stage-2 PBS template b6.job() reads is gone; the D3 job (same VASP binary and watchdog) is the header source,
# and gamma_split() rewrites the stage lines
D_JOB = os.path.join(HERE, "inputs", "D3_Ce2O3_gasgeom", "job.pbs")
b6.job = lambda name, stages, kind: open(D_JOB).read()
CE_CLUSTER = (48, 49)
TITLE = "Ce2O3 cluster/CeO2(111) p(4x4)"


def choose_parent(energies):
    """{name: E(final single point)} -> lowest name."""
    return min(energies, key=energies.get)


def sites(a):
    n = len(a)
    o_cl = list(range(n - 3, n))
    cl = list(CE_CLUSTER) + o_cl
    z = a.positions[:, 2]
    ce_top = max(CE_CLUSTER, key=lambda i: z[i])
    o_top = max(o_cl, key=lambda i: z[i])
    cen = a.positions[cl].mean(axis=0)
    sup_o = [i for i in range(n) if a[i].symbol == "O" and i not in o_cl]
    zs = max(z[i] for i in sup_o)
    top_o = [i for i in sup_o if z[i] > zs - 0.5]
    # edge O: exposed top-plane support O (>= 2.6 A laterally from every cluster atom), nearest to the cluster
    free = [i for i in top_o if min(b6.lateral(a, a.positions[i], a.positions[k]) for k in cl) >= 2.6]
    edge = min(free, key=lambda i: b6.lateral(a, a.positions[i], cen))
    return ce_top, o_top, edge, cen


def tilt_away(a, frm, ref):
    v = a.positions[frm, :2] - ref[:2]
    v = v / np.linalg.norm(v)
    return np.array([0.6 * v[0], 0.6 * v[1], 0.8])


def endpoint_sets(a):
    ce, ot, edge, cen = sites(a)
    p = a.positions
    up = tilt_away(a, ce, p[ot])                               # Ce-CH3 tilted away from the top cluster O
    return {
        "D4_CH4_Ce": [b6.ch4(p[ce] + [0, 0, 3.4])],
        "D5_CH4_edge": [b6.ch4(p[edge] + [0, 0, 2.9])],
        "D6_CH3Ce_HOc": [b6.ch3(p[ce] + 2.55 * up), (None, [p[ot] + [0, 0, 0.98]])],
        "D7_CH3Os_HOc": [b6.ch3(p[edge] + [0, 0, 1.43]), (None, [p[ot] + [0, 0, 0.98]])],
        "D8_CH3Ce_HOs": [b6.ch3(p[ce] + 2.55 * up), (None, [p[edge] + [0, 0, 0.98]])],
    }, (ce, ot, edge)


def gamma_split(d, name, tag):
    """Gamma-point stages A/B, 2x2x1 final single point, as gamma_switch_20261017.py did for D1-D3."""
    def sub(t, k, v):
        t, n = re.subn(r"^%s = .*$" % k, "%s = %s" % (k, v), t, flags=re.M)
        assert n == 1, k
        return t
    for st in ("stageA_spinSP", "stageB_relax"):
        f = os.path.join(d, "INCAR_" + st)
        t = sub(sub(open(f).read(), "KPAR", "1"), "NCORE", "6")
        open(f, "w", newline="\n").write(t)
    f = os.path.join(d, "INCAR_stageC_SP")
    t = sub(sub(open(f).read(), "ISTART", "0"), "ICHARG", "1")
    open(f, "w", newline="\n").write(t)
    k = open(os.path.join(d, "KPOINTS")).read()
    open(os.path.join(d, "KPOINTS_final"), "w", newline="\n").write(k)
    open(os.path.join(d, "KPOINTS_relax"), "w", newline="\n").write(
        "%s | Gamma only (relaxation)\n0\nGamma\n1 1 1\n0 0 0\n" % k.splitlines()[0])
    job = open(os.path.join(d, "job.pbs")).read()
    head = job.split("\nrun_stage ", 1)[0]
    head = re.sub(r"^for f in .*; do$", "for f in INCAR_stageA_spinSP INCAR_stageB_relax INCAR_stageC_SP POSCAR "
                  "KPOINTS_relax KPOINTS_final POTCAR; do", head, count=1, flags=re.M)
    head = re.sub(r"^#PBS -N \S+", "#PBS -N s7%s_%s" % (tag[:1], name[:12]), head, count=1, flags=re.M)
    body = ["cp KPOINTS_relax KPOINTS", "run_stage stageA_spinSP LABORT scf", "run_stage stageB_relax LSTOP relax",
            "cp POSCAR POSCAR_start; cp CONTCAR POSCAR; cp KPOINTS_final KPOINTS", "run_stage stageC_SP LABORT scf"]
    open(os.path.join(d, "job.pbs"), "w", newline="\n").write(
        head + "\n" + "\n".join(body) + '\necho "end=$(date --iso-8601=seconds) rc=0"\n')
    for f in os.listdir(d):                                   # Vanda reads LF only
        raw = open(os.path.join(d, f), "rb").read()
        open(os.path.join(d, f), "wb").write(raw.replace(b"\r\n", b"\n"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("parent")
    ap.add_argument("out")
    ap.add_argument("--tag", default="final", help="'preview' while the parent is still relaxing")
    args = ap.parse_args()
    par = read(args.parent, format="vasp")
    assert par.get_chemical_formula() == "Ce50O99", par.get_chemical_formula()
    sets, (ce, ot, edge) = endpoint_sets(par)
    os.makedirs(args.out, exist_ok=True)
    rep = ["parent %s (%s); cluster Ce %d, top cluster O %d, edge support O %d" %
           (os.path.abspath(args.parent), args.tag, ce, ot, edge)]
    for name, frags in sets.items():
        a = b6.add(par, frags)
        a, ok, mh, mc = b7.tidy(a)
        b6.write_set(args.out, name, "%s | %s" % (TITLE, name), a, "slab", (2, 2, 1), False)
        gamma_split(os.path.join(args.out, name), name, args.tag)
        dmin, pair = b6.check(a)
        rep.append("%-14s %-12s tidy ok=%s minH-X=%.2f minC-X=%.2f shortest non-bond %.2f %s fixed=%d" % (
            name, a.get_chemical_formula(), ok, mh, mc, dmin, pair, len(a.constraints[0].index)))
    open(os.path.join(args.out, "BUILD_REPORT.txt"), "w", newline="\n").write("\n".join(rep) + "\n")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
