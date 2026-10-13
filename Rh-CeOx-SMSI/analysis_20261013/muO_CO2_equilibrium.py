"""850 C + CO2: oxygen chemical potential from the ideal-gas equilibrium CO2 <=> CO + 1/2 O2 (Method B evaluation).

Reference convention identical to Stage 5 (analyse_stage5.py `reduction`):
    Delta mu_O(T, p) = mu_O - 1/2 E_O2(DFT) = Delta mu_O^0(T) + 1/2 kT ln(p_O2 / p0)
    Delta mu_O^0(T) = 1/2 {[H(T) - H(0)] - T S(T)}_O2          (Reuter & Scheffler, PRB 65, 035406 (2001))
and, at gas-phase equilibrium, the CO2/CO form gives the same number:
    Delta mu_O = Delta mu_O^0(T) + Delta_r G(CO + 1/2 O2 -> CO2) + kT ln(p_CO2/p_CO)

Thermochemistry: NIST-JANAF tables (p0 = 0.1 MPa), downloaded 2026-10-13 from https://janaf.nist.gov/tables/
O-029 (O2), C-093 (CO), C-095 (CO2); only the rows bracketing 1123.15 K (and the 0 K H-H(Tr) of O2) are needed,
linear interpolation in T.

Feed model: 1 mol gas = y CO2 + x_O2 O2 + x_CO CO + rest He; extent xi of CO2 -> CO + 1/2 O2; total pressure P (bar).
Outputs: muO_CO2_equilibrium.json and Fig_muO_850C_CO2_equilibrium.svg next to this script.
"""
import json
import os

import numpy as np
from scipy.optimize import brentq

HERE = os.path.dirname(os.path.abspath(__file__))
KB = 8.617333262e-5          # eV/K
R = 8.314462618e-3           # kJ/mol/K
KJMOL_PER_EV = 96.48533212
T = 1123.15                  # 850 C

# JANAF rows: T(K): (S J/mol/K, H-H(298.15) kJ/mol, Delta_f G kJ/mol)
JANAF = {
    "O2":  {1100: (246.922, 26.212, 0.0), 1200: (250.010, 29.761, 0.0)},
    "CO":  {1100: (237.726, 25.035, -209.075), 1200: (240.679, 28.430, -217.819)},
    "CO2": {1100: (274.528, 38.884, -396.001), 1200: (279.390, 44.473, -396.098)},
}
O2_H0_MINUS_HTR = -8.683     # kJ/mol, O-029 row T = 0 K

# Stage-5 fixed-morphology reduction lines, per Ce: dG = A + 0.5 * Delta mu_O (stage5_Eint.json -> reduction)
STAGE5 = {"cluster": {"A": 1.2265019499999918, "star": -2.4530038999999837, "label": "Ce$_2$O$_4$→Ce$_2$O$_3$ cluster/Rh"},
          "layer": {"A": 0.8857, "star": -1.7714, "label": "Ce$_4$O$_8$→Ce$_4$O$_6$ layer/Rh"}}
STAGE5_CO2_CO_1TO1 = -3.176


def interp(sp, col, t=T):
    lo, hi = JANAF[sp][1100][col], JANAF[sp][1200][col]
    return lo + (hi - lo) * (t - 1100.0) / 100.0


def dmu0(t=T):
    """Delta mu_O^0(T, p0) in eV/O, zero = 1/2 E_O2 at 0 K."""
    h = interp("O2", 1, t) - O2_H0_MINUS_HTR
    s = interp("O2", 0, t) / 1000.0
    return 0.5 * (h - t * s) / KJMOL_PER_EV


def drG_ox(t=T):
    """Delta_r G(CO + 1/2 O2 -> CO2), eV."""
    return (interp("CO2", 2, t) - interp("CO", 2, t)) / KJMOL_PER_EV


def equilibrium(P, y=1.0, x_o2=0.0, x_co=0.0, t=T):
    """Equilibrium partial pressures (bar) for CO2 <=> CO + 1/2 O2 starting from the given feed."""
    kp = np.exp(drG_ox(t) / (KB * t))          # dissociation K_p = exp(-Delta_r G_diss / kT)

    def f(xi):                                 # residual of ln K_p
        n_co2, n_co, n_o2 = y - xi, x_co + xi, x_o2 + xi / 2
        ntot = 1.0 + xi / 2
        p = lambda n: P * n / ntot
        return np.log(p(n_co)) + 0.5 * np.log(p(n_o2)) - np.log(p(n_co2)) - np.log(kp)

    lo = max(-x_co, -2 * x_o2) + 1e-30
    xi = brentq(f, lo, y * (1 - 1e-12), xtol=1e-30, rtol=1e-14, maxiter=500)
    ntot = 1.0 + xi / 2
    p = {"CO2": P * (y - xi) / ntot, "CO": P * (x_co + xi) / ntot, "O2": P * (x_o2 + xi / 2) / ntot}
    mu_o2 = dmu0(t) + 0.5 * KB * t * np.log(p["O2"])
    mu_co = dmu0(t) + drG_ox(t) + KB * t * np.log(p["CO2"] / p["CO"])
    return dict(P_bar=P, y_CO2=y, x_O2=x_o2, x_CO=x_co, xi=xi, p=p,
                log10_pCO2_pCO=float(np.log10(p["CO2"] / p["CO"])), log10_pO2=float(np.log10(p["O2"])),
                dmuO=float(mu_o2), dmuO_check_CO2CO=float(mu_co))


def main():
    out = {"T_K": T, "dmu0_O": dmu0(), "drG_CO_plus_halfO2_to_CO2_eV": drG_ox(),
           "Kp_CO2_dissociation": float(np.exp(drG_ox() / (KB * T))),
           "dmuO_CO2_CO_1to1_JANAF": dmu0() + drG_ox(), "dmuO_CO2_CO_1to1_stage5": STAGE5_CO2_CO_1TO1}
    pressures = [1e-4, 1e-3, 1e-2, 0.1, 1.0]
    out["pure_CO2"] = [equilibrium(P) for P in pressures]
    out["CO2_10pct_He"] = [equilibrium(P, y=0.1) for P in pressures]
    out["O2_impurity_1bar"] = [equilibrium(1.0, x_o2=x) for x in (1e-6, 5e-6, 1e-5, 2.4e-5, 1e-4)]
    out["CO_impurity_1bar"] = [equilibrium(1.0, x_co=x) for x in (1e-6, 1e-5, 1e-4, 1e-3)]
    # O2 impurity needed (1 bar, pure CO2) to lift Delta mu_O to the layer reduction boundary
    out["pO2_at_layer_boundary_bar"] = float(np.exp(2 * (STAGE5["layer"]["star"] - dmu0()) / (KB * T)))
    out["pO2_at_cluster_boundary_bar"] = float(np.exp(2 * (STAGE5["cluster"]["star"] - dmu0()) / (KB * T)))
    with open(os.path.join(HERE, "muO_CO2_equilibrium.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    for k in ("pure_CO2", "CO2_10pct_He", "O2_impurity_1bar", "CO_impurity_1bar"):
        print(k)
        for r in out[k]:
            print("  P=%-7g y=%-4g xO2=%-7g xCO=%-7g log10(CO2/CO)=%6.2f log10 pO2=%7.2f dmuO=%7.3f (check %7.3f)" % (
                r["P_bar"], r["y_CO2"], r["x_O2"], r["x_CO"], r["log10_pCO2_pCO"], r["log10_pO2"], r["dmuO"], r["dmuO_check_CO2CO"]))
    print({k: v for k, v in out.items() if not isinstance(v, list)})
    plot(out)


def plot(out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 11, "svg.fonttype": "none", "axes.spines.top": False, "axes.spines.right": False})
    BLUE, ORANGE, AQUA, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#555555"
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={"width_ratios": [1.25, 1]})

    # (a) Stage-5 reduction lines with the 850 C CO2 equilibrium band
    mu = np.linspace(-3.4, -1.2, 200)
    for key, col in (("cluster", BLUE), ("layer", ORANGE)):
        r = STAGE5[key]
        a1.plot(mu, r["A"] + 0.5 * mu, color=col, lw=2, label=r["label"])
        a1.plot(r["star"], 0, "o", color=col, ms=8)
        a1.annotate("%.2f" % r["star"], (r["star"], 0), xytext=(4, 8), textcoords="offset points", fontsize=10)
    band = [r["dmuO"] for r in out["pure_CO2"] + out["CO2_10pct_He"]]
    a1.axvspan(min(band), max(band), color=AQUA, alpha=0.18, lw=0,
               label="850 °C CO$_2$ equilibrium, P = 10$^{-4}$–1 bar, 10–100 % CO$_2$")
    one_bar = out["pure_CO2"][-1]["dmuO"]
    a1.axvline(one_bar, color=AQUA, lw=2, label="850 °C, 1 bar pure CO$_2$: %.2f eV" % one_bar)
    a1.axvline(STAGE5_CO2_CO_1TO1, color=GREY, ls="--", lw=1.5, label="CO$_2$/CO = 1 reference: −3.18 eV")
    a1.axhline(0, color="#999999", lw=0.8)
    a1.set_xlabel(r"$\Delta\mu_\mathrm{O}$ (eV/O, ref. ½E$_{\mathrm{O_2}}$)")
    a1.set_ylabel("ΔG$_\\mathrm{red}$ per Ce (eV)")
    a1.set_title("(a) Reduction of the fixed morphology vs Δμ$_\\mathrm{O}$", fontsize=11, loc="left")
    a1.text(-1.25, -0.75, "ΔG < 0: reduced form (Ce$^{3+}$) favoured", fontsize=9, color=GREY, ha="right")
    a1.legend(fontsize=8.5, frameon=False, loc="upper left")

    # (b) sensitivity: total pressure, He dilution, O2 impurity
    lp = np.linspace(-4, 0, 41)
    cases = [("pure CO$_2$", dict(y=1.0), BLUE, "-"), ("10 % CO$_2$ / He", dict(y=0.1), ORANGE, "-"),
             ("pure CO$_2$ + 1 ppm O$_2$", dict(x_o2=1e-6), AQUA, "--"), ("pure CO$_2$ + 10 ppm O$_2$", dict(x_o2=1e-5), GREY, "--")]
    for lab, kw, col, ls in cases:
        a2.plot(lp, [equilibrium(10 ** x, **kw)["dmuO"] for x in lp], color=col, ls=ls, lw=2, label=lab)
    for key in ("cluster", "layer"):
        a2.axhline(STAGE5[key]["star"], color=GREY, lw=1, ls=":")
        a2.text(-3.95, STAGE5[key]["star"] + 0.02, "%s boundary %.2f" % (key, STAGE5[key]["star"]), fontsize=9, color=GREY)
    a2.set_xlabel("log$_{10}$(total pressure / bar)")
    a2.set_ylabel(r"$\Delta\mu_\mathrm{O}$ (eV/O)")
    a2.set_ylim(-2.6, -1.6)
    a2.set_title("(b) Sensitivity at 850 °C", fontsize=11, loc="left")
    a2.legend(fontsize=8.5, frameon=False, loc="center right")
    fig.text(0.01, 0.005, "Ideal-gas CO$_2$ $\\rightleftharpoons$ CO + ½O$_2$ equilibrium, NIST-JANAF; a gas-equilibrium estimate, not a measured "
             "local gas composition. Boundaries are within one morphology (Stage 5), not cluster-vs-layer.", fontsize=8, color=GREY)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(os.path.join(HERE, "Fig_muO_850C_CO2_equilibrium.svg"))
    fig.savefig(os.path.join(HERE, "Fig_muO_850C_CO2_equilibrium.png"), dpi=200)


if __name__ == "__main__":
    main()
