"""D3 sensitivity, level 1: PBE-D3(BJ) dispersion added at frozen PBE+U geometries (Stage 4 layers, Stage 5 clusters).

E_D3 from s-dftd3 1.2.1 on Vanda (run_frozen_D3.sh -> E_D3_eV.txt; --bj pbe, no ATM term = VASP IVDW = 12).
D3 is a pure function of the geometry, so E(PBE+U+D3) at the PBE+U geometry = E(PBE+U) + E_D3 exactly; relaxation under
D3 is level 2 (VASP re-relaxation). PBE+U energies: Stage-5 stage5_Eint.json (relaxation E0) and Stage-4
energetics_stage4.json (final SP), as used in the original analyses.
Level 2 (VASP re-relaxation with IVDW = 12, then the Stage-4 final-SP settings + IVDW = 12, jobs in relax_D3/ on Vanda):
when E_D3_relaxed.txt exists ("<name> <E0 of final_sp_D3, eV>" for L6, L7i, L8), the layer reduction lines are also
evaluated with these energies; O2 keeps the frozen-geometry D3 term (-0.007 eV; its relaxation under D3 is negligible).
Writes D3_frozen.json and D3_frozen.md.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KB = 8.617333262e-5
MU_CO2_850C = {"1 bar": -1.917, "1e-2 bar": -2.066, "1e-4 bar": -2.215}   # analysis_20261013/muO_CO2_equilibrium.json

d3 = {}
for line in open(os.path.join(HERE, "E_D3_eV.txt")):
    k, path, sha, e = line.split()
    d3[k] = float(e)
s5 = json.load(open(os.path.join(ROOT, "DynSMSI_stage5_cluster_layer_Eint_20260930", "results", "stage5_Eint.json"),
                    encoding="utf-8"))["jobs"]
s4 = json.load(open(os.path.join(ROOT, "DynSMSI_stage4_Ce4Ox_layers_20260928", "results", "energetics_stage4.json"),
                    encoding="utf-8"))["energies"]
E = {"R4": s5["R4_Rh111_4x4"]["E0"], "C3a": s5["C3a_Ce2O3_Rh_from12b"]["E0"], "C3b": s5["C3b_Ce2O3_Rh_from12a"]["E0"],
     "C4a": s5["C4a_Ce2O4_Rh_from10c"]["E0"], "C4b": s5["C4b_Ce2O4_Rh_from12b_plusO"]["E0"],
     "G3": s5["G3_Ce2O3_gas"]["E0"], "G4": s5["G4_Ce2O4_gas"]["E0"], "GO2": s5["GO2_O2_gas"]["E0"],
     "L0": s4["L0_Rh111_3x3"]["E"], "L6": s4["L6_Ce4O6_Rh"]["E"], "L7s": s4["L7s_Ce4O7_Rh_vacSurf"]["E"],
     "L7i": s4["L7i_Ce4O7_Rh_vacInt"]["E"], "L8": s4["L8_Ce4O8_Rh"]["E"], "F6": s4["F6_Ce4O6_free"]["E"],
     "F7s": s4["F7s_Ce4O7_free_vacSurf"]["E"], "F7i": s4["F7i_Ce4O7_free_vacInt"]["E"], "F8": s4["F8_Ce4O8_free"]["E"],
     "G_O2": s4["G_O2"]["E"]}


def tot(k, with_d3):
    return E[k] + (d3[k] if with_d3 else 0.0)


def eint(ads, free, slab, n_units, w):
    return (tot(ads, w) - tot(free, w) - tot(slab, w)) / n_units


def red_line(red, ox, o2, n_o, n_ce, w):
    """dG_red per Ce = A + B * dmu_O for ox -> red + n_o O(reservoir), O referenced to 1/2 E_O2."""
    a = (tot(red, w) + n_o * 0.5 * tot(o2, w) - tot(ox, w)) / n_ce
    return a, n_o / n_ce


out = {"E_D3": d3, "E_int_per_unit": {}, "reduction": {}}
rows = []
for w in (False, True):
    tag = "PBE+U+D3" if w else "PBE+U"
    ei = {"C3a cluster Ce2O3": eint("C3a", "G3", "R4", 1, w), "C3b cluster Ce2O3": eint("C3b", "G3", "R4", 1, w),
          "C4a cluster Ce2O4": eint("C4a", "G4", "R4", 1, w), "C4b cluster Ce2O4": eint("C4b", "G4", "R4", 1, w),
          "L6 layer Ce4O6 /2": eint("L6", "F6", "L0", 2, w), "L8 layer Ce4O8 /2": eint("L8", "F8", "L0", 2, w)}
    out["E_int_per_unit"][tag] = ei
    lines = {"cluster Ce2O4->Ce2O3": red_line("C3a", "C4a", "GO2", 1, 2, w),
             "layer Ce4O8->Ce4O6": red_line("L6", "L8", "G_O2", 2, 4, w),
             "layer Ce4O8->Ce4O7 (interface Ov)": red_line("L7i", "L8", "G_O2", 1, 4, w),
             "layer Ce4O8->Ce4O7 (surface Ov)": red_line("L7s", "L8", "G_O2", 1, 4, w)}
    red = {}
    for k, (a, b) in lines.items():
        red[k] = {"A_per_Ce": a, "B_per_Ce": b, "dmuO_star": -a / b,
                  "dG_850C_CO2": {p: a + b * mu for p, mu in MU_CO2_850C.items()}}
    a6, _ = lines["layer Ce4O8->Ce4O6"]
    a7, _ = lines["layer Ce4O8->Ce4O7 (interface Ov)"]
    red["Ce4O6 = Ce4O7(interface Ov)"] = {"dmuO_star": -(a6 - a7) / 0.25}
    out["reduction"][tag] = red

for k in ("PBE+U", "PBE+U+D3"):
    ei = out["E_int_per_unit"][k]
    out.setdefault("cluster_minus_layer", {})[k] = {"Ce2O3": ei["C3a cluster Ce2O3"] - ei["L6 layer Ce4O6 /2"],
                                                    "Ce2O4": ei["C4a cluster Ce2O4"] - ei["L8 layer Ce4O8 /2"]}
rel = os.path.join(HERE, "E_D3_relaxed.txt")
if os.path.exists(rel):
    er = {l.split()[0]: float(l.split()[1]) for l in open(rel) if l.strip()}
    o2 = E["G_O2"] + d3["G_O2"]
    red = {}
    for k, (r, n_o) in {"layer Ce4O8->Ce4O6": ("L6", 2), "layer Ce4O8->Ce4O7 (interface Ov)": ("L7i", 1)}.items():
        a = (er[r] + n_o * 0.5 * o2 - er["L8"]) / 4
        b = n_o / 4
        red[k] = {"A_per_Ce": a, "B_per_Ce": b, "dmuO_star": -a / b,
                  "dG_850C_CO2": {p: a + b * mu for p, mu in MU_CO2_850C.items()}}
    red["Ce4O6 = Ce4O7(interface Ov)"] = {"dmuO_star": -(red["layer Ce4O8->Ce4O6"]["A_per_Ce"]
                                                     - red["layer Ce4O8->Ce4O7 (interface Ov)"]["A_per_Ce"]) / 0.25}
    out["reduction"]["PBE+U+D3 relaxed"] = red
    out["E_D3_relaxed"] = er
json.dump(out, open(os.path.join(HERE, "D3_frozen.json"), "w"), indent=1)

md = ["# D3 sensitivity, level 1 (frozen PBE+U geometries)", "",
      "| E_int (eV per Ce₂Oᵧ unit) | PBE+U | PBE+U+D3 | D3 shift |", "|---|---|---|---|"]
for k in out["E_int_per_unit"]["PBE+U"]:
    a, b = out["E_int_per_unit"]["PBE+U"][k], out["E_int_per_unit"]["PBE+U+D3"][k]
    md.append("| %s | %.3f | %.3f | %+.3f |" % (k, a, b, b - a))
for c in ("Ce2O3", "Ce2O4"):
    a, b = out["cluster_minus_layer"]["PBE+U"][c], out["cluster_minus_layer"]["PBE+U+D3"][c]
    md.append("| cluster − layer, %s | %.3f | %.3f | %+.3f |" % (c, a, b, b - a))
md += ["", "| Reduction (per Ce) | Δμ_O* PBE+U | Δμ_O* +D3 | ΔG at 850 °C, 1 bar CO₂: PBE+U | +D3 |", "|---|---|---|---|---|"]
for k in out["reduction"]["PBE+U"]:
    a, b = out["reduction"]["PBE+U"][k], out["reduction"]["PBE+U+D3"][k]
    g = ("%+.3f | %+.3f" % (a["dG_850C_CO2"]["1 bar"], b["dG_850C_CO2"]["1 bar"])) if "dG_850C_CO2" in a else "– | –"
    md.append("| %s | %.3f | %.3f | %s |" % (k, a["dmuO_star"], b["dmuO_star"], g))
if "PBE+U+D3 relaxed" in out["reduction"]:
    md += ["", "| Level 2, D3 re-relaxed (per Ce) | Δμ_O* | ΔG 1 bar | ΔG 10⁻² bar | ΔG 10⁻⁴ bar |", "|---|---|---|---|---|"]
    for k, v in out["reduction"]["PBE+U+D3 relaxed"].items():
        g = v.get("dG_850C_CO2")
        md.append("| %s | %.3f | %s |" % (k, v["dmuO_star"], " | ".join("%+.3f" % g[p] for p in MU_CO2_850C) if g else "– | – | –"))
open(os.path.join(HERE, "D3_frozen.md"), "w", encoding="utf-8", newline="\n").write("\n".join(md) + "\n")
print("\n".join(md))
