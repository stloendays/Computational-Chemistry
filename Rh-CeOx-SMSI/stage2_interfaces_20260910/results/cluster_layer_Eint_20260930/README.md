# Stage 5 results: Ce2O3 / Ce2O4 cluster vs layer interaction energy with Rh(111) (task 2026-09-30, finished 2026-10-08)

E_int = E(Ce2Oy/Rh(111) p(4×4)) − E(Ce2Oy, isolated) − E(Rh(111) p(4×4)); layer = 2026-09-28 Step-3 E_int/2
(one Ce4O2y cell = two Ce2Oy units). Final E0 of each IBRION 2 relaxation, no extra single point; ISPIN 2, no MAGMOM.

| Ce:O | Cluster E_int (eV/unit) | Layer E_int/2 (eV/unit) | Cluster − layer (eV) | Stronger with Rh(111) |
|---|---|---|---|---|
| 2:3 (Ce2O3) | −4.452 (C3a) | −1.634 | −2.818 | cluster |
| 2:4 (Ce2O4) | −5.145 (C4a) | −3.004 | −2.141 | cluster |

| System | E0 (eV) | Fmax free (eV/Å) | Total moment (μB) | Ce moments (μB) | Ce³⁺ |
|---|---|---|---|---|---|
| R4 Rh(111) p(4×4) | −439.68688 | 0.002 | 0.00 | — | — |
| C3a Ce2O3/Rh (lowest) | −478.37273 | 0.016 | 2.05 | 0.997, 0.997 | 2 |
| C3b Ce2O3/Rh | −477.88210 | 0.017 | 1.90 | 0.982, 0.997 | 2 |
| C4a Ce2O4/Rh (lowest) | −485.76487 | 0.018 | 2.04 | 0.997, 0.993 | 2 |
| C4b Ce2O4/Rh | −485.69049 | 0.017 | 1.91 | 0.973, 0.995 | 2 |
| G3 Ce2O3 gas | −34.23431 | 0.019 | 2.00 | 0.994, 0.976 | 2 |
| G4 Ce2O4 gas | −40.93264 | 0.017 | 0.00 | 0.000, 0.001 | 0 |
| O2 gas | −9.87827 | 0.005 | 2.00 | — | — |

All relaxations reached the required accuracy (EDIFFG −0.02 eV/Å); max |m(Rh)| ≤ 0.031 μB. On Rh(111) the Ce2O4
cluster also carries two Ce³⁺: Rh donates two electrons to the cluster.

Reduction Ce2O4 → Ce2O3 per Ce: cluster Δμ_O* = −2.45 eV, layer (Ce4O8 → Ce4O6) Δμ_O* = −1.77 eV
(`Fig_dG_cluster_vs_layer.png`, `stage5_Eint.json` → `reduction`).

Files: `stage5_Eint.md/json`, `Fig_cluster_vs_layer_Eint.png`, `Fig_dG_cluster_vs_layer.png`; per system the
relaxed `CONTCAR` and the `INCAR` of the final relaxation (C4a: segment-3 restart INCAR, POTIM 0.10, EDIFF 1e-6).
Script: `../../cluster_layer_Eint_20260930/analyse_stage5.py`.
