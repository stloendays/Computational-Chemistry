"""Layer (Stage 4) and cluster (Stage 5) CeOx/Rh(111) on one free-energy scale per Ce (reference: Ce4O8 layer),
with the two 850 C experimental atmospheres of the 2026-10-15 plan on one panel:
  850 C, CO2 (flow CO2 0.7, He 1.3) and 850 C, CH4:CO2 = 1:1 (flow CH4 0.5, CO2 0.5, He 1), feeds of the gas-cell
  in situ TEM report p. 4; Delta mu_O from the 1 bar gas-phase equilibrium of each feed (muO_DRM_feed_equilibrium.json).
Same A, B per state as analysis_20261013/Fig_dG_layer_cluster_CO2.py. Outputs Fig_dG_850C_two_markers.{png,svg,csv}.
"""
import json
import os

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
CC = os.path.dirname(os.path.dirname(HERE))
AN = os.path.join(CC, "DynSMSI_stage6_DRM_CH4_paths_20261013", "analysis_20261013")
U = json.load(open(os.path.join(CC, "DynSMSI_stage5_cluster_layer_Eint_20260930", "results", "cluster_layer_unified.json"),
                   encoding="utf-8"))
S4 = json.load(open(os.path.join(CC, "DynSMSI_stage4_Ce4Ox_layers_20260928", "results", "energetics_stage4.json"),
                    encoding="utf-8"))["dG"]
MJ = json.load(open(os.path.join(HERE, "muO_DRM_feed_equilibrium.json")))
MU_CO2 = MJ["CO2_atmosphere"]["dmuO"]               # CO2 0.7 / He 1.3, 1 bar
MU_DRM = MJ["dmuO"]                                 # CH4 0.5 / CO2 0.5 / He 1, 1 bar

LINES = [
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
    mu = np.linspace(-4.0, -1.0, 200)
    for lab, a, b, col, ls in LINES:
        ax.plot(mu, a + b * mu, color=col, ls=ls, lw=2.6, label=lab)
    lo = min(min(a + b * mu.min(), a + b * mu.max()) for _, a, b, *_ in LINES)
    hi = max(max(a + b * mu.min(), a + b * mu.max()) for _, a, b, *_ in LINES)
    ylo, yhi = np.floor(lo * 5) / 5 - 0.1, np.ceil(hi * 5) / 5 + 0.4
    for x, t in ((MU_CO2, "850 °C, CO$_2$"), (MU_DRM, "850 °C, CH$_4$:CO$_2$ = 1:1")):
        ax.axvline(x, color="#555555", ls="--", lw=1.4)
        ax.text(x + 0.03, yhi - 0.06, t, fontsize=15, va="top")
    ax.set_xlim(-4.0, -1.0)
    ax.set_ylim(ylo, yhi)
    ax.set_xticks(np.arange(-4.0, -0.99, 0.5))
    ax.set_xlabel(r"$\Delta\mu_\mathrm{O}$ (eV)")
    ax.set_ylabel(r"$\Delta G$ per Ce (eV)")
    ax.legend(frameon=False, fontsize=13, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.13),
              columnspacing=1.2, handlelength=2.4)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(HERE, "Fig_dG_850C_two_markers." + ext), dpi=220, bbox_inches="tight")
    with open(os.path.join(HERE, "Fig_dG_850C_two_markers.csv"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("state,A_eV_per_Ce,B_per_Ce,dG_850C_CO2_feed,dG_850C_DRM_feed_1bar\n")
        for lab, a, b, *_ in LINES:
            name = lab.replace("$", "").replace("_", "").replace(r"\mathrm{O}", "O").replace("{", "").replace("}", "")
            fh.write("%s,%.4f,%.3f,%.3f,%.3f\n" % (name, a, b, a + b * MU_CO2, a + b * MU_DRM))
    print("dmuO CO2 %.3f  DRM %.3f  ylim %.1f %.1f" % (MU_CO2, MU_DRM, ylo, yhi))
    print(open(os.path.join(HERE, "Fig_dG_850C_two_markers.csv"), encoding="utf-8").read())


if __name__ == "__main__":
    main()
