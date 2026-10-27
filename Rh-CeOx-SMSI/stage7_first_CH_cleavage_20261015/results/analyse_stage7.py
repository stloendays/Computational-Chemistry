# -*- coding: utf-8 -*-
"""Stage-7 first C-H cleavage energetics from the final single points (E0 = energy(sigma->0), ISMEAR 0).

E_ads(CH4*) = E(CH4*) - E(clean parent) - E(CH4, g)
dE          = E(CH3* + H*/OH*) - E(lowest CH4* of the same model)
E_rel       = E(state) - E(clean parent) - E(CH4, g)   (every state on one scale per model)
Systems without a final energy yet are kept with value null (placeholders in the deck).
Inputs: E_final_sp.txt (from OUTCAR_stageC_SP on Vanda); CH4(g) from G_CH4 OUTCAR_stageB_relax (ISMEAR 0).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
E_CH4 = -24.03718833

MODELS = {
    "A": {"name": "Rh(111)", "clean": "A0_ref", "IS": ["A1_CH4_top"], "FS": ["A2_CH3top_Hfcc"]},
    "B": {"name": "Ce4O6 layer/Rh(111)", "clean": "B0_ref", "IS": ["B1_CH4_Ce", "B2_CH4_Os"],
          "FS": ["B3_CH3Ce_HOs", "B4_CH3Os_HOs"]},
    "C": {"name": "Ce2O3 cluster/Rh(111)", "clean": "C0_ref", "IS": ["C1_CH4_perimRh", "C2_CH4_Ce"],
          "FS": ["C3_CH3perimRh_HOt", "C4_CH3perimRh_Hfcc", "C5_CH3Ce_HOt", "C6_CH3farRh_Hfcc"]},
    "D": {"name": "Ce2O3 cluster/CeO2(111)", "clean": None, "IS": [], "FS": []},
}


def main():
    E = {}
    for line in open(os.path.join(HERE, "E_final_sp.txt"), encoding="utf-8"):
        p = line.split()
        if len(p) >= 2:
            E[p[0]] = float(p[1])
    out = {"E_CH4_gas": E_CH4, "E0": E, "models": {}}
    for k, m in MODELS.items():
        ec = E.get(m["clean"]) if m["clean"] else None
        rel = {n: (round(E[n] - ec - E_CH4, 3) if (ec is not None and n in E) else None) for n in m["IS"] + m["FS"]}
        is_done = [n for n in m["IS"] if rel[n] is not None]
        best_is = min(is_done, key=lambda n: rel[n]) if is_done else None
        dE = {n: (round(rel[n] - rel[best_is], 3) if (best_is and rel[n] is not None) else None) for n in m["FS"]}
        out["models"][k] = {**m, "E_rel": rel, "best_IS": best_is,
                            "E_ads": rel[best_is] if best_is else None, "dE": dE,
                            "IS_complete": len(is_done) == len(m["IS"]) and bool(m["IS"])}
    json.dump(out, open(os.path.join(HERE, "stage7_energies.json"), "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    for k, v in out["models"].items():
        print(k, v["name"], "best IS", v["best_IS"], "E_ads", v["E_ads"], "E_rel", v["E_rel"], "dE", v["dE"])


if __name__ == "__main__":
    main()
