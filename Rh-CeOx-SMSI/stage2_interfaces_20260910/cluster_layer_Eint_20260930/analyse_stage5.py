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
        "C4a_Ce2O4_Rh_from10c": "stageB_relax_restart", "C4b_Ce2O4_Rh_from12b_plusO": "stageB_relax",
        "G3_Ce2O3_gas": "stageB_relax", "G4_Ce2O4_gas": "stageB_relax", "GO2_O2_gas": "stageB_relax"}
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
    plot(out["comparison"])
    dg = reduction(jobs, out)
    if dg:
        out["reduction"] = dg
        json.dump(out, open(os.path.join(HERE, "results", "stage5_Eint.json"), "w", encoding="utf-8"), indent=1)


def reduction(jobs, out):
    """Ce2O4 -> Ce2O3 cluster on Rh(111) vs Ce4O8 -> Ce4O6 layer (stage 4), per Ce, against Delta mu_O.

    dG(dmu_O) = E(reduced/Rh) - E(oxidised/Rh) + n (1/2 E_O2 + dmu_O); cluster n = 1 per 2 Ce, layer n = 2 per 4 Ce.
    Each line uses the O2 reference of its own batch (stage 5: GO2_O2_gas; stage 4: G_O2).
    """
    o2 = jobs.get("GO2_O2_gas", {})
    c = out["comparison"]
    if not (o2.get("converged") and "cluster" in c["Ce2O3"] and "cluster" in c["Ce2O4"]):
        return None
    st4 = json.load(open(STAGE4, encoding="utf-8"))
    A_cl = (jobs[c["Ce2O3"]["cluster"]]["E0"] - jobs[c["Ce2O4"]["cluster"]]["E0"] + 0.5 * o2["E0"]) / 2
    lay = st4["dG"]["Ce$_4$O$_6$"]
    A_ly = lay["A_per_Ce"]
    res = {"E_O2_stage5": o2["E0"], "E_O2_stage4": st4["energies"]["G_O2"]["E"],
           "cluster": {"A_per_Ce": A_cl, "B_per_Ce": 0.5, "dmuO_star": -A_cl / 0.5,
                       "reduced": c["Ce2O3"]["cluster"], "oxidised": c["Ce2O4"]["cluster"]},
           "layer": {"A_per_Ce": A_ly, "B_per_Ce": 0.5, "dmuO_star": -A_ly / 0.5}}
    sys.path.insert(0, os.path.join(os.path.dirname(STAGE4)))
    from analyse_muO_TP import dmu0, drG_CO2, KB
    for k in ("cluster", "layer"):
        mu = res[k]["dmuO_star"]
        res[k]["T_table"] = [dict(T_C=t, log10_pO2_star=round(float(2 * (mu - dmu0(t + 273.15)) / (KB * (t + 273.15)) / np.log(10)), 2),
                                  log10_pCO2_pCO_star=round(float((mu - dmu0(t + 273.15) - drG_CO2(t + 273.15)) / (KB * (t + 273.15)) / np.log(10)), 2))
                             for t in (800, 850)]
    print(json.dumps(res, indent=1))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "Arial", "font.size": 16, "axes.linewidth": 1.3,
                         "xtick.direction": "in", "ytick.direction": "in"})
    mu = np.linspace(-3.4, 0.0, 200)
    fig, ax = plt.subplots(figsize=(7.5, 5.2), dpi=200)
    for k, col, lab in (("cluster", "#C0392B", r"cluster: Ce$_2$O$_4$ → Ce$_2$O$_3$"),
                        ("layer", "#2C5AA0", r"layer: Ce$_4$O$_8$ → Ce$_4$O$_6$")):
        r = res[k]
        ax.plot(mu, r["A_per_Ce"] + 0.5 * mu, color=col, lw=2.5, label=lab)
        ax.plot(r["dmuO_star"], 0, "o", color=col, ms=9)
        ax.annotate(("%.2f" % r["dmuO_star"]).replace("-", "−"), (r["dmuO_star"], 0), xytext=(0, -26 if k == "cluster" else 12),
                    textcoords="offset points", ha="center", color=col, fontsize=15)
    mu_ref = float(dmu0(1123.15) + drG_CO2(1123.15))
    res["dmuO_850C_CO2_CO_1to1"] = round(mu_ref, 3)
    ax.axvline(mu_ref, color="#555555", ls="--", lw=1.5)
    ax.text(mu_ref + 0.05, 0.05, "850 °C\nCO$_2$/CO = 1", fontsize=13, va="bottom")
    ax.axhline(0, color="k", lw=1)
    ax.set_xlim(-3.4, 0.0)
    ax.set_xlabel(r"Δμ$_O$ (eV)")
    ax.set_ylabel("ΔG per Ce (eV)")
    ax.legend(frameon=False, loc="lower right", fontsize=14)
    ax.set_title("ΔG < 0: reduced Ce$^{3+}$ phase is stable", fontsize=15)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "results", "Fig_dG_cluster_vs_layer.png"))
    return res


def plot(cmp_):
    """Cluster and layer bars side by side; a cluster value not yet available is left as an empty dashed bar."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    plt.rcParams.update({"font.family": "Arial", "font.size": 16})
    comps = ["Ce2O3", "Ce2O4"]
    labels = [r"Ce$_2$O$_3$ (Ce:O = 2:3)", r"Ce$_2$O$_4$ (Ce:O = 2:4)"]
    cl = [cmp_[c].get("cluster_E_int") for c in comps]
    ly = [cmp_[c]["layer_E_int_per_unit"] for c in comps]
    known = [v for v in cl + ly if v is not None]
    ymin = min(known) * 1.45
    x, w = np.arange(2), 0.34
    fig, ax = plt.subplots(figsize=(7.5, 5.2), dpi=200)
    for xi, v in zip(x - w / 2, cl):
        if v is None:
            ax.text(xi, -0.1, "pending", ha="center", va="top", rotation=90, fontsize=15, color="#C0392B")
        else:
            ax.bar(xi, v, w, color="#C0392B")
            ax.text(xi, v - 0.08, ("%.2f" % v).replace("-", "−"), ha="center", va="top", fontsize=15)
    for xi, v in zip(x + w / 2, ly):
        ax.bar(xi, v, w, color="#2C5AA0")
        ax.text(xi, v - 0.08, ("%.2f" % v).replace("-", "−"), ha="center", va="top", fontsize=15)
    ax.axhline(0, color="k", lw=1)
    ax.set_xticks(x, labels)
    ax.set_ylabel(r"E$_{int}$ per Ce$_2$O$_y$ unit (eV)")
    ax.set_ylim(ymin, 0.3)
    ax.set_xlim(-0.6, 1.6)
    ax.legend(handles=[Patch(color="#C0392B", label="cluster/Rh(111)"),
                       Patch(color="#2C5AA0", label="layer/Rh(111), E$_{int}$/2")], frameon=False, loc="lower center", ncol=2, fontsize=14)
    ax.set_title("More negative E$_{int}$ = stronger interaction with Rh(111)", fontsize=15)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "results", "Fig_cluster_vs_layer_Eint.png"))


if __name__ == "__main__":
    main()
