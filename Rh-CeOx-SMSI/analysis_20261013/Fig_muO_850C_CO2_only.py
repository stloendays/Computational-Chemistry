"""850 C + CO2 only: where the oxygen chemical potential line sits on the Stage-5 reduction diagram.

No CO2/CO = 1 reference point. Delta mu_O comes from the ideal-gas equilibrium CO2 <=> CO + 1/2 O2 of a pure CO2 feed
(muO_CO2_equilibrium.py, NIST-JANAF, same reference zero 1/2 E_O2 as Stage 5). The line is drawn at 1 bar; the light
band spans the same feed at 1e-4 - 1 bar total pressure.
Output: Fig_muO_850C_CO2_only.svg / .png next to this script.
"""
import os

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from muO_CO2_equilibrium import STAGE5, equilibrium

HERE = os.path.dirname(os.path.abspath(__file__))
BLUE, ORANGE, GREEN, INK = "#2a78d6", "#eb6834", "#139a6a", "#1f1f1f"


def main():
    mu1 = equilibrium(1.0)["dmuO"]
    mu_lo = equilibrium(1e-4)["dmuO"]
    plt.rcParams.update({"font.size": 16, "svg.fonttype": "none", "axes.spines.top": False,
                         "axes.spines.right": False, "font.family": "Arial"})
    fig, ax = plt.subplots(figsize=(9.5, 6.2))
    mu = np.linspace(-3.0, -1.2, 200)
    ax.axvspan(mu_lo, mu1, color=GREEN, alpha=0.12, lw=0)
    ax.axvline(mu1, color=GREEN, lw=3)
    ax.axhline(0, color=INK, lw=0.8)
    for key, col, name in (("cluster", BLUE, "Ce$_2$O$_4$ → Ce$_2$O$_3$ cluster/Rh(111)"),
                           ("layer", ORANGE, "Ce$_4$O$_8$ → Ce$_4$O$_6$ layer/Rh(111)")):
        r = STAGE5[key]
        ax.plot(mu, r["A"] + 0.5 * mu, color=col, lw=2.8, label=name)
        ax.plot(r["star"], 0, "o", color=col, ms=9)
        ax.annotate(("%.2f" % r["star"]).replace("-", "−"), (r["star"], 0),
                    xytext=(-12, -26) if key == "cluster" else (-12, 12), textcoords="offset points", fontsize=14, color=col)
        y = r["A"] + 0.5 * mu1
        ax.plot(mu1, y, "s", color=col, ms=9, mec="white")
        ax.annotate(("%+.2f eV" % y).replace("-", "−"), (mu1, y), xytext=(10, -4) if y > 0 else (10, -28),
                    textcoords="offset points", fontsize=14, color=col)
    ax.text(mu1 + 0.03, 0.56, ("850 °C + CO$_2$\n1 bar: %.2f eV" % mu1).replace("-", "−"), color=GREEN, fontsize=15, va="top")
    ax.text((mu_lo + mu1) / 2, -0.62, "10$^{-4}$–1 bar", color=GREEN, fontsize=13, ha="center")
    ax.text(-2.98, 0.5, "ΔG > 0: oxidised form stable", fontsize=13, color=INK)
    ax.text(-1.22, -0.55, "ΔG < 0: reduced form (Ce$^{3+}$) stable", fontsize=13, color=INK, ha="right")
    ax.set_xlim(-3.0, -1.2)
    ax.set_ylim(-0.7, 0.62)
    ax.set_xlabel(r"$\Delta\mu_\mathrm{O}$ (eV per O, relative to ½E$_{\mathrm{O_2}}$)")
    ax.set_ylabel("ΔG$_\\mathrm{red}$ per Ce (eV)")
    ax.legend(fontsize=13, frameon=False, loc="upper left", bbox_to_anchor=(0.0, 0.92))
    fig.tight_layout()
    for ext in ("svg", "png"):
        fig.savefig(os.path.join(HERE, "Fig_muO_850C_CO2_only." + ext), dpi=220)
    print("1 bar %.3f, 1e-4 bar %.3f" % (mu1, mu_lo))
    for key in ("cluster", "layer"):
        print(key, round(STAGE5[key]["A"] + 0.5 * mu1, 3))


if __name__ == "__main__":
    main()
