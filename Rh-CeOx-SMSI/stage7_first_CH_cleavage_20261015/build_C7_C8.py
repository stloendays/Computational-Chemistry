"""Model C supplement (2026-10-29): the cluster top O (O_t) as CH4 site, missing from the 10-15 set.

  C7_CH4_Ot        CH4 over the cluster top O                              (as B2_CH4_Os)
  C8_CH3Ot_HOb     CH3 on O_t (methoxy) + H on a Rh-bridging cluster O     (as B4_CH3Os_HOs)

Base: relaxed C0_ref CONTCAR (same cell, same fixed atoms). INCARs, KPOINTS, POTCAR.spec and job.pbs are the
C1 set relabelled, so the settings match C0-C6 exactly.
"""
import os
import sys

import numpy as np
from ase.io import read, write

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "DynSMSI_stage6_DRM_CH4_paths_20261013"))
import build_stage6 as b6  # noqa: E402

TEMPLATE = os.path.join(HERE, "inputs", "C1_CH4_perimRh")
LABEL = "Ce2O3 cluster C3a/Rh(111) p(4x4)"

base = read(os.path.join(HERE, "results", "raw", "C0_ref", "CONTCAR"))
base.arrays.pop("momenta", None)  # CONTCAR predictor block not carried over
sym = np.array(base.get_chemical_symbols())
o = np.where(sym == "O")[0]
ce = np.where(sym == "Ce")[0]
o_t = max(o, key=lambda i: base.positions[i, 2])
o_b = [i for i in o if i != o_t]
centre = base.positions[np.concatenate([ce, o]), :2].mean(axis=0)
# H on the bridging O farther from Ce-free Rh rows: pick the one with the lower index for reproducibility,
# pointing outward from the cluster centre and 45 deg up
ob = min(o_b)
out = base.positions[ob, :2] - centre
out /= np.linalg.norm(out)
h_ob = base.positions[ob] + 0.98 * np.array([out[0] / np.sqrt(2), out[1] / np.sqrt(2), 1 / np.sqrt(2)])

sets = {
    "C7_CH4_Ot": [b6.ch4(base.positions[o_t] + [0, 0, 2.9])],
    "C8_CH3Ot_HOb": [b6.ch3(base.positions[o_t] + [0, 0, 1.43]), (None, [h_ob])],
}

for name, frags in sets.items():
    a = b6.add(base, frags)
    d = os.path.join(HERE, "inputs", name)
    os.makedirs(d, exist_ok=True)
    title = "%s | %s" % (LABEL, name)
    write(os.path.join(d, "POSCAR"), a, format="vasp", direct=True, sort=False)
    with open(os.path.join(d, "POSCAR")) as fh:
        body = fh.read().split("\n", 1)[1]
    with open(os.path.join(d, "POSCAR"), "w", newline="\n") as fh:
        fh.write(title + "\n" + body)
    for f in ("INCAR_stageA_spinSP", "INCAR_stageB_relax", "INCAR_stageC_SP", "KPOINTS", "POTCAR.spec", "job.pbs"):
        txt = open(os.path.join(TEMPLATE, f)).read()
        txt = txt.replace("C1_CH4_perimRh", name).replace("s7_C1_CH4_perim", ("s7_" + name)[:15])
        with open(os.path.join(d, f), "w", newline="\n") as fh:
            fh.write(txt)
    zmax = a.positions[:, 2].max()
    d_min = min(a.get_distances(i, [j for j in range(len(a)) if j != i], mic=True).min()
                for i in range(len(base), len(a)))
    print("%-14s %-14s c=%.3f zmax=%.2f vac=%.2f  O_t=%d O_b=%d  min d(ads)=%.2f fixed=%d" % (
        name, a.get_chemical_formula(), a.cell[2, 2], zmax, a.cell[2, 2] - zmax, o_t, ob, d_min,
        len(a.constraints[0].index)))
