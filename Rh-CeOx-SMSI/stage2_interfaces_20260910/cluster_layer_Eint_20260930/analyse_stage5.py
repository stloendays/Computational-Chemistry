#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Stage 5 analysis: cluster/Rh(111) E_int vs the 2026-09-28 layer E_int/2, per Ce2O_y unit.

1. Pulls OSZICAR/OUTCAR/CONTCAR/POSCAR of every stage-5 job from Vanda into results/raw/ (--no-fetch to skip).
2. Per job: final E0 of the relaxation, 'reached required accuracy', max force on free atoms,
   total moment, Ce local moments (LORBIT 11, last block).
3. E_int = E[Ce2Oy/Rh] - E[Ce2Oy, isolated] - E[Rh(111) 4x4]; the lowest of the two starts is the reported cluster.
4. Layer: 2026-09-28 Step-3 E_int (stage-4 energetics_stage4.json) divided by 2 (two Ce2Oy units per cell).
5. Writes results/stage5_Eint.json, results/stage5_Eint.md and results/Fig_cluster_vs_layer_Eint.png.
Run with D:/Research/CatalystForge/.venv/Scripts/python.exe from this folder.
"""
import json
import os
import re
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "results", "raw")
REMOTE = "/scratch/junbotong/Dynamic_SMSI_stage5_cluster_layer_20260930/inputs"
STAGE4 = os.path.join(HERE, "..", "DynSMSI_stage4_Ce4Ox_layers_20260928", "results", "energetics_stage4.json")
JOBS = {"R4_Rh111_4x4": "relax", "C3a_Ce2O3_Rh_from12b": "stageB_relax", "C3b_Ce2O3_Rh_from12a": "stageB_relax",
        "C4a_Ce2O4_Rh_from10c": "stageB_relax", "C4b_Ce2O4_Rh_from12b_plusO": "stageB_relax",
        "G3_Ce2O3_gas": "stageB_relax", "G4_Ce2O4_gas": "stageB_relax"}
CLUSTERS = {"Ce2O3": ["C3a_Ce2O3_Rh_from12b", "C3b_Ce2O3_Rh_from12a"],
            "Ce2O4": ["C4a_Ce2O4_Rh_from10c", "C4b_Ce2O4_Rh_from12b_plusO"]}
GAS = {"Ce2O3": "G3_Ce2O3_gas", "Ce2O4": "G4_Ce2O4_gas"}
LAYER_KEY = {"Ce2O3": "Ce4O6", "Ce2O4": "Ce4O8"}


def fetch():
    os.makedirs(RAW, exist_ok=True)
    names = " ".join(JOBS)
    cmd = (f"cd {REMOTE} && tar -cf - $(for d in {names}; do for f in OSZICAR_* OUTCAR_* CONTCAR POSCAR "
           f"*.o1*; do ls $d/$f 2>/dev/null; done; done)")
    tar = subprocess.run(["ssh", "-o", "BatchMode=yes", "vanda", cmd], capture_output=True)
    subprocess.run(["tar", "-C", RAW.replace("\\", "/"), "-xf", "-"], input=tar.stdout, check=True)


def free_flags(poscar):
    L = open(poscar).read().split("\n")
    n = sum(int(x) for x in L[6].split())
    if not L[7].strip()[:1] in ("S", "s"):
        return np.ones(n, bool)
    return np.array([L[9 + k].split()[3] == "T" for k in range(n)])


def parse(job, tag):
    d = os.path.join(RAW, job)
    osz, out = os.path.join(d, f"OSZICAR_{tag}"), os.path.join(d, f"OUTCAR_{tag}")
    if not (os.path.exists(osz) and os.path.exists(out)):
        return {"status": "missing"}
    lines = [l for l in open(osz) if " F= " in l]
    if not lines:
        return {"status": "no ionic step"}
    m = re.search(r"(\d+) F=\s*(\S+) E0=\s*(\S+).*?mag=\s*(\S+)", lines[-1])
    txt = open(out, errors="ignore").read()
    res = {"ionic_steps": int(m[1]), "E0": float(m[3]), "mag_total": float(m[4]),
           "converged": "reached required accuracy" in txt}
    blk = txt.rsplit("TOTAL-FORCE (eV/Angst)", 1)
    if len(blk) == 2:
        rows = blk[1].split("-----\n", 1)[1].split(" -----")[0].strip().splitlines()
        F = np.array([[float(x) for x in r.split()[3:6]] for r in rows])
        free = free_flags(os.path.join(d, "POSCAR"))
        res["Fmax_free"] = float(np.linalg.norm(F[free], axis=1).max())
    mb = re.findall(r" magnetization \(x\)\n.*?\n-+\n(.*?)\n-+", txt, re.S)
    if mb:
        L = open(os.path.join(d, "POSCAR")).read().split("\n")
        sym = [s for s, c in zip(L[5].split(), map(int, L[6].split())) for _ in range(c)]
        mom = [float(r.split()[-1]) for r in mb[-1].splitlines()]
        res["Ce_moments"] = [round(x, 3) for s, x in zip(sym, mom) if s == "Ce"]
        res["n_Ce3+"] = sum(1 for s, x in zip(sym, mom) if s == "Ce" and abs(x) > 0.5)
        res["max_Rh_moment"] = round(max((abs(x) for s, x in zip(sym, mom) if s == "Rh"), default=0.0), 3)
    res["status"] = "converged" if res["converged"] else "running/unconverged"
    return res


def main():
    if "--no-fetch" not in sys.argv:
        fetch()
    jobs = {j: parse(j, t) for j, t in JOBS.items()}
    lay = json.load(open(STAGE4, encoding="utf-8"))["E_int"]
    out = {"jobs": jobs, "comparison": {}}
    rh = jobs["R4_Rh111_4x4"]
    for comp, starts in CLUSTERS.items():
        g = jobs[GAS[comp]]
        row = {"layer_E_int_cell": lay[LAYER_KEY[comp]]["E_int"], "layer_E_int_per_unit": lay[LAYER_KEY[comp]]["E_int"] / 2}
        ok = [s for s in starts if jobs[s].get("converged")]
        if ok and g.get("converged") and rh.get("converged"):
            for s in ok:
                row[f"E_int_{s}"] = jobs[s]["E0"] - g["E0"] - rh["E0"]
            best = min(ok, key=lambda s: jobs[s]["E0"])
            row["cluster"] = best
            row["cluster_E_int"] = row[f"E_int_{best}"]
            row["cluster_minus_layer"] = row["cluster_E_int"] - row["layer_E_int_per_unit"]
            row["stronger"] = "cluster" if row["cluster_minus_layer"] < 0 else "layer"
        out["comparison"][comp] = row
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, "results", "stage5_Eint.json"), "w", encoding="utf-8"), indent=1)

    md = ["# Stage 5: cluster vs layer interaction energy with Rh(111)", "",
          "| Job | status | steps | E0 (eV) | Fmax free (eV/A) | total mag | Ce moments | max |m(Rh)| |",
          "|---|---|---|---|---|---|---|---|"]
    for j, r in jobs.items():
        md.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            j, r.get("status"), r.get("ionic_steps", ""), "%.5f" % r["E0"] if "E0" in r else "",
            "%.3f" % r["Fmax_free"] if "Fmax_free" in r else "", r.get("mag_total", ""),
            r.get("Ce_moments", ""), r.get("max_Rh_moment", "")))
    md += ["", "| Ce:O | cluster E_int (eV/unit) | layer E_int (eV/cell) | layer E_int/2 (eV/unit) | cluster - layer | stronger |",
           "|---|---|---|---|---|---|"]
    for comp, r in out["comparison"].items():
        md.append("| %s | %s | %.3f | %.3f | %s | %s |" % (
            "2:3" if comp == "Ce2O3" else "2:4",
            "%.3f (%s)" % (r["cluster_E_int"], r["cluster"]) if "cluster_E_int" in r else "pending",
            r["layer_E_int_cell"], r["layer_E_int_per_unit"],
            "%.3f" % r["cluster_minus_layer"] if "cluster_minus_layer" in r else "pending", r.get("stronger", "")))
    open(os.path.join(HERE, "results", "stage5_Eint.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))
    if all("cluster_E_int" in r for r in out["comparison"].values()):
        plot(out["comparison"])


def plot(cmp_):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "Arial", "font.size": 16})
    comps = ["Ce2O3", "Ce2O4"]
    labels = [r"Ce$_2$O$_3$ (Ce:O = 2:3)", r"Ce$_2$O$_4$ (Ce:O = 2:4)"]
    cl = [cmp_[c]["cluster_E_int"] for c in comps]
    ly = [cmp_[c]["layer_E_int_per_unit"] for c in comps]
    x, w = np.arange(2), 0.34
    fig, ax = plt.subplots(figsize=(7.5, 5.2), dpi=200)
    b1 = ax.bar(x - w / 2, cl, w, color="#C0392B", label="cluster/Rh(111)")
    b2 = ax.bar(x + w / 2, ly, w, color="#2C5AA0", label="layer/Rh(111), E$_{int}$/2")
    for bars in (b1, b2):
        for r in bars:
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() - 0.08, "%.2f" % r.get_height(),
                    ha="center", va="top", fontsize=15)
    ax.axhline(0, color="k", lw=1)
    ax.set_xticks(x, labels)
    ax.set_ylabel(r"E$_{int}$ per Ce$_2$O$_y$ unit (eV)")
    ax.set_ylim(min(cl + ly) * 1.25, 0.3)
    ax.legend(frameon=False, loc="lower left")
    ax.set_title("More negative E$_{int}$ = stronger interaction with Rh(111)", fontsize=15)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "results", "Fig_cluster_vs_layer_Eint.png"))


if __name__ == "__main__":
    main()
