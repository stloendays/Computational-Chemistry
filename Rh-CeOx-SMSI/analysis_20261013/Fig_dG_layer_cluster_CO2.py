"""Layer (Stage 4) and cluster (Stage 5) CeOx/Rh(111) on one free-energy scale per Ce, referenced to the Ce4O8 layer,
with the 850 C + CO2 oxygen chemical potential (1 bar, CO2 <=> CO + 1/2 O2 equilibrium, muO_CO2_equilibrium.json).
dG per Ce = A + B * dmu_O; A, B from Stage-5 results/cluster_layer_unified.json and Stage-4 energetics_stage4.json.
Outputs Fig_dG_layer_cluster_CO2.{png,svg} and dG_layer_cluster_CO2.csv next to this script.
"""
import json
import os

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
CC = os.path.dirname(os.path.dirname(HERE))
U = json.load(open(os.path.join(CC, "DynSMSI_stage5_cluster_layer_Eint_20260930", "results", "cluster_layer_unified.json"),
                   encoding="utf-8"))
S4 = json.load(open(os.path.join(CC, "DynSMSI_stage4_Ce4Ox_layers_20260928", "results", "energetics_stage4.json"),
                    encoding="utf-8"))["dG"]
MU = json.load(open(os.path.join(HERE, "muO_CO2_equilibrium.json")))["pure_CO2"][-1]["dmuO"]    # 1 bar

LINES = [  # label, A, B, colour, style
    (r"Layer Ce$_4$O$_8$", U["layer Ce4O8"]["A"], U["layer Ce4O8"]["B"], "#1f1f1f", "-"),
    (r"Layer Ce$_4$O$_7$ (interface V$_\mathrm{O}$)", U["layer Ce4O7(int)"]["A"], U["layer Ce4O7(int)"]["B"], "#2a9d8f", "-"),
    (r"Layer Ce$_4$O$_7$ (surface V$_\mathrm{O}$)", S4["Ce$_4$O$_7$ (surface O$_v$)"]["A_per_Ce"],
     S4["Ce$_4$O$_7$ (surface O$_v$)"]["B_per_Ce"], "#8ab17d", ":"),
    (r"Layer Ce$_4$O$_6$", U["layer Ce4O6"]["A"], U["layer Ce4O6"]["B"], "#264b96", "-"),
    (r"Cluster Ce$_2$O$_4$", U["cluster Ce2O4"]["A"], U["cluster Ce2O4"]["B"], "#d4a017", "--"),
    (r"Cluster Ce$_2$O$_3$", U["cluster Ce2O3"]["A"], U["cluster Ce2O3"]["B"], "#b5334a", "--"),
]


def main():
    plt.rcParams.update({"font.family": "Arial", "font.size": 16, "axes.linewidth": 1.2,
                         "xtick.direction": "in", "ytick.direction": "in", "svg.fonttype": "none"})
    fig, ax = plt.subplots(figsize=(8.6, 6.4))
    mu = np.linspace(-3.2, -1.0, 200)
    for lab, a, b, col, ls in LINES:
        ax.plot(mu, a + b * mu, color=col, ls=ls, lw=2.6, label=lab)
    ax.axvline(MU, color="#555555", ls="--", lw=1.4)
    ax.text(MU + 0.03, 1.52, "850 °C, CO$_2$", fontsize=15, va="top")
    ax.set_xlim(-3.2, -1.0)
    ax.set_ylim(-0.8, 1.6)
    ax.set_xticks(np.arange(-3.0, -0.99, 0.5))
    ax.set_xlabel(r"$\Delta\mu_\mathrm{O}$ (eV)")
    ax.set_ylabel(r"$\Delta G$ per Ce (eV)")
    ax.legend(frameon=False, fontsize=13, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.13),
              columnspacing=1.2, handlelength=2.4)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(HERE, "Fig_dG_layer_cluster_CO2." + ext), dpi=220, bbox_inches="tight")
    with open(os.path.join(HERE, "dG_layer_cluster_CO2.csv"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("state,A_eV_per_Ce,B_per_Ce,dG_at_850C_CO2_1bar_eV_per_Ce\n")
        for lab, a, b, *_ in LINES:
            name = lab.replace("$", "").replace("_", "").replace("\\mathrm{O}", "O").replace("{", "").replace("}", "")
            fh.write("%s,%.4f,%.3f,%.3f\n" % (name, a, b, a + b * MU))
    print("dmuO(850 C, 1 bar CO2) = %.3f" % MU)
    print(open(os.path.join(HERE, "dG_layer_cluster_CO2.csv"), encoding="utf-8").read())


if __name__ == "__main__":
    main()
