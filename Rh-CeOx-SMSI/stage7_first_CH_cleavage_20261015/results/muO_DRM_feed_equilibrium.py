"""850 C, CH4:CO2 = 1:1 flowing feed (the experimental DRM atmosphere): oxygen chemical potential of that gas.

The feed is fixed (continuous flow; gas-cell in situ TEM report p. 4: CH4 0.5, CO2 0.5, He 1; CO2 atmosphere: CO2 0.7,
He 1.3). Delta mu_O is taken from the ideal-gas equilibrium of this feed at 850 C and 1 bar total (CH4, CO2, CO, H2, H2O, He; extents of CH4 + CO2 -> 2 CO + 2 H2 and CO2 + H2 -> CO + H2O), then
    Delta mu_O = Delta mu_O^0(T) + Delta_r G(CO + 1/2 O2 -> CO2) + kT ln(p_CO2/p_CO)
with the same convention and JANAF rows as analysis_20261013/muO_CO2_equilibrium.py (Reuter & Scheffler 2001).
The H2O/H2 couple gives the same value at equilibrium (printed as a check).
JANAF (p0 = 0.1 MPa, https://janaf.nist.gov/tables/, 2026-10-20): C-067 CH4, H-064 H2O(g); O2, CO, CO2 as before.
Output: muO_DRM_feed_equilibrium.json next to this script.
"""
import json
import os

import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
KB = 8.617333262e-5
R = 8.314462618e-3
KJMOL_PER_EV = 96.48533212
T = 1123.15
P = 1.0
FEED = {"CH4": 0.5, "CO2": 0.5, "He": 1.0}     # flow ratio of the report, normalised below

DFG = {  # Delta_f G (kJ/mol) at 1100 / 1200 K
    "CO": (-209.075, -217.819), "CO2": (-396.001, -396.098), "CH4": (30.472, 41.524),
    "H2O": (-187.033, -181.425), "H2": (0.0, 0.0),
}
O2 = {1100: (246.922, 26.212), 1200: (250.010, 29.761)}      # S, H-H(298)
O2_H0_MINUS_HTR = -8.683


def g(sp):
    lo, hi = DFG[sp]
    return lo + (hi - lo) * (T - 1100.0) / 100.0


def dmu0():
    f = (T - 1100.0) / 100.0
    s = O2[1100][0] + (O2[1200][0] - O2[1100][0]) * f
    h = O2[1100][1] + (O2[1200][1] - O2[1100][1]) * f - O2_H0_MINUS_HTR
    return 0.5 * (h - T * s / 1000.0) / KJMOL_PER_EV


def main():
    K1 = np.exp(-(2 * g("CO") + 2 * g("H2") - g("CH4") - g("CO2")) / (R * T))      # dry reforming
    K2 = np.exp(-(g("CO") + g("H2O") - g("CO2") - g("H2")) / (R * T))             # reverse water-gas shift

    f = {k: v / sum(FEED.values()) for k, v in FEED.items()}

    def comp(x):
        a, b = x
        n = {"CH4": f["CH4"] - a, "CO2": f["CO2"] - a - b, "CO": 2 * a + b, "H2": 2 * a - b, "H2O": b, "He": f["He"]}
        tot = sum(n.values())
        return n, {k: v / tot * P for k, v in n.items()}

    def res(x):
        _, p = comp(x)
        return [np.log(p["CO"] ** 2 * p["H2"] ** 2 / (p["CH4"] * p["CO2"])) - np.log(K1),
                np.log(p["CO"] * p["H2O"] / (p["CO2"] * p["H2"])) - np.log(K2)]

    e = 1e-12
    sol = least_squares(res, [0.9 * f["CH4"], 0.01 * f["CO2"]], bounds=([e, e], [f["CH4"] - e, f["CO2"] - e]),
                        xtol=1e-15, ftol=1e-15, gtol=1e-15)
    a, b = sol.x
    if sol.cost > 1e-20 or b >= f["CO2"] - a:
        raise RuntimeError("equilibrium not converged: cost %g" % sol.cost)
    n, p = comp((a, b))
    d0 = dmu0()
    drg_co = (g("CO2") - g("CO")) / KJMOL_PER_EV
    drg_h2 = g("H2O") / KJMOL_PER_EV
    mu_c = d0 + drg_co + KB * T * np.log(p["CO2"] / p["CO"])
    mu_h = d0 + drg_h2 + KB * T * np.log(p["H2O"] / p["H2"])
    out = {"T_K": T, "P_bar": P, "feed": "CH4:CO2 = 1:1", "feed_flow": FEED, "conversion_CH4": a / f["CH4"], "p_bar": p,
           "log10_pCO2_pCO": float(np.log10(p["CO2"] / p["CO"])), "dmuO": float(mu_c), "dmuO_check_H2O_H2": float(mu_h)}
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "DynSMSI_stage6_DRM_CH4_paths_20261013",
                                    "analysis_20261013"))
    import muO_CO2_equilibrium as mc
    r = mc.equilibrium(P, y=0.7 / 2.0)
    out["CO2_atmosphere"] = {"feed_flow": {"CO2": 0.7, "He": 1.3}, "P_bar": P, "dmuO": r["dmuO"],
                             "log10_pCO2_pCO": r["log10_pCO2_pCO"]}
    json.dump(out, open(os.path.join(HERE, "muO_DRM_feed_equilibrium.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
