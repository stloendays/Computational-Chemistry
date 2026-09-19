# Stage-2 round 1: all 18 systems converged (2026-09-19)

Acceptance: `reached required accuracy`, free-atom max force <= 0.02 eV/A, bottom two Rh layers unmoved, Ce moments as expected.

| System | E0 / eV | Ce3+ | E_int / eV | E_int per Ce | dG per Ce at O-rich / eV |
|---|---|---|---|---|---|
| 20a Ce4O8 layer, fcc | -341.238 | 0 | -4.685 (vs free film) | -1.171 | -0.103 |
| 20b Ce4O8 layer, top | -340.904 | 0 | -4.351 | -1.088 | -0.020 |
| 30a Ce4O6 layer, 2 interface vacancies | -329.455 | 4 (AFM) | -3.276 (vs A-type film) | -0.819 | +0.372 |
| 30c Ce4O6 layer, 1+1 | -328.592 | 4 | -2.413 | -0.603 | +0.588 |
| 30d A-type Ce2O3 bilayer | -328.415 | 4 | -2.236 | -0.559 | +0.632 |
| 30b Ce4O6 layer, 2 surface vacancies | -328.151 | 4 (FM) | -1.972 | -0.493 | +0.698 |
| 10c Ce2O4 cluster | -293.253 | 2 (AFM) | -4.953 (vs gas unit) | -2.476 | +0.407 |
| 10a Ce2O3 cluster, O in Rh hollow + Ce-Rh contact | -286.613 | 2 | -5.023 | -2.512 | +1.256 |
| 10b Ce2O3 cluster, O-down | -285.839 | 2 | -4.250 | -2.125 | +1.643 |

References: Rh slab -247.307; O2 -9.882; CeO2 bulk -24.388 /f.u.; Ce2O3 bulk -41.818 /f.u.; films Ce4O8 -89.246, Ce4O6 A-type -78.872, Ce4O6 flat -75.604; gas Ce2O3 -34.282, Ce2O4 -40.993 eV.
Bulk CeO2/Ce2O3 boundary: dmu_O = -2.017 eV. Layer crossover (20a vs 30a): dmu_O = -0.95 eV.

Structural notes
- 10a: relaxed (FIRE) into a structure 0.77 eV below 10b: one O in a Rh fcc hollow (3 Rh-O 2.09-2.15 A), both Ce in contact with Rh (2.85-2.98 A), 2 Ce3+.
- 30a: Ce4O6 film anchored by two O on Rh (2.01 A), Ce 3.0 A above Rh; 0.86-1.30 eV below the other Ce4O6 variants.
- 10c: Ce2O4 keeps 2 Ce3+; the extra O binds three Rh.
- Free Ce4O6 film reconstructs into the A-type Ce2O3 bilayer (3.3 eV below the flat vacancy trilayer).

Boundaries: 0 K electronic energies; PBE O2; +5 % oxide strain not yet corrected; cluster coverage is half of the layer coverage.
Protocol lessons (process, not results): LDIPOL off during relaxation; two-stage spin start; FIRE (IOPT=7) for soft modes; 48 h walltime.
