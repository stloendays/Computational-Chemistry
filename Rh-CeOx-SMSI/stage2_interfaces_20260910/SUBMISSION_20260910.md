# Stage-2 round-1 submission, 2026-09-10 16:50–16:55 (+08)

Remote root: `vanda:~/Rh_CeO2_personal/Dynamic_SMSI_stage2_interfaces_20260910/inputs/`
Allocation `CFP03-CF-126`, queue `auto` -> `batch_cpu`, 36 ranks each. Allocation session was valid without a new amgr login.

| Dir | PBS ID | walltime | state at submit |
|---|---|---|---|
| 40_O2_gas | 1359679 | 1 h | R |
| 00_Rh111_clean | 1359681 | 4 h | R |
| 41_CeO2_bulk | 1359682 | 2 h | R |
| 50a_Ce4O8_film_free | 1359683 | 4 h | R |
| 50b_Ce4O6_film_2Obot | 1359684 | 4 h | R |
| 50c_Ce4O6_film_2Otop | 1359685 | 4 h | R |
| 50d_Ce4O6_film_1top1bot | 1359686 | 4 h | Q |
| 20a_Ce4O8_layer_regFCC | 1359687 | 12 h | Q |
| 20b_Ce4O8_layer_regTOP | 1359688 | 12 h | Q |
| 30a_Ce4O6_layer_2Obot | 1359689 | 12 h | Q |
| 30b_Ce4O6_layer_2Otop | 1359690 | 12 h | Q |
| 30c_Ce4O6_layer_1top1bot | 1359691 | 12 h | Q |
| 10a_Ce2O3_cluster_Odown | 1359692 | 12 h | Q |
| 10b_Ce2O3_cluster_Cedown | 1359693 | 12 h | Q |

Each job writes `LSTOP` 30 min before walltime (watchdog); a stopped job restarts from WAVECAR/CONTCAR (ISTART=1, copy CONTCAR to POSCAR).
Acceptance per job: `reached required accuracy` in OUTCAR, max force < 0.02 eV/A, bottom two Rh layers unmoved, Ce moments ~1 muB where Ce3+ is expected.

## Added 2026-09-10 evening

| Dir | PBS ID | walltime | why |
|---|---|---|---|
| 30d_Ce4O6_layer_Atype | 1359836 | 12 h | the free Ce4O6 film (50c) relaxed into an A-type Ce2O3(0001) O-Ce-O-Ce-O bilayer, 3.3 eV below the flat vacancy trilayer (50d); this candidate starts from that geometry on Rh (O-down, low Ce over fcc) so the Ce2O3-layer comparison is not biased by the CeO2-derived starting structure. |

Accepted so far: 40_O2 (E0 = -9.8820), 00_Rh111_clean (free-atom max F 0.004 eV/A; spacings 2.207/2.160/2.176 A),
41_CeO2_bulk (a = 5.4612 A under this ISIF=3/400 eV contract; Pulay-stress shrink vs EOS 5.503 A, same bias as the Ce2O3 reference),
50a_Ce4O8_film (all Ce4+, E0 = -89.2457), 50c_Ce4O6_film (A-type bilayer, 4 Ce3+ ~0.99 muB, E0 = -78.8719), 50d_Ce4O6_film (flat, 4 Ce3+, E0 = -75.6039).

## Added 2026-09-10 night (after external review)

| Dir | PBS ID | walltime | why |
|---|---|---|---|
| 10c_Ce2O4_cluster_Odown | 1359841 | 12 h | completes the 2x2 matrix (composition x morphology): CeO2-type cluster |
| 42_Ce2O3_gas | 1359842 | 4 h | isolated-cluster reference for E_int of 10a/10b (15 A box, 2 Ce3+) |
| 43_Ce2O4_gas | 1359843 | 4 h | isolated-cluster reference for E_int of 10c (15 A box, Ce4+) |

Deferred to round 2 (after round-1 relaxations): 500 eV single points on representatives; frozen-fragment / deformation split;
film at its own lattice (strain energy); 5x5 Rh / (2sqrt3 x 2sqrt3)R30 oxide cell (0.4 % mismatch) if layer-vs-cluster gap is small;
O2 overbinding correction and dmu_O(T,p) mapping in the dG(mu_O) analysis; no-dipole single point as a control.

## 2026-09-10 night: resubmission of all interface and gas-cluster jobs

Root cause: INCAR mixing block (AMIX 0.2 / BMIX 1e-4 / AMIX_MAG 0.8 / BMIX_MAG 1e-4) was carried over from the insulating
CeO2(111) slab. On the metallic Rh(111) substrate it switches off Kerker damping and the SCF charge-sloshes:
20a reached NELM=250 without convergence (dE ~ 1e-2 eV oscillating), 30a oscillated by 0.1-0.4 eV, 10a by ~1 eV.
Forces from such densities are meaningless, so the six running and five queued jobs were deleted (partial output kept in
`<dir>/failed_linear_mixing_20260910/`) and resubmitted with VASP default Kerker mixing, AMIN = 0.01, MAXMIX = 40, NELM = 200.
00_Rh111_clean, 40_O2, 41_CeO2_bulk and the 50a-d films (all converged) are unaffected; the SCF was fine there because the
films/bulk are insulating and the clean Rh slab used ISPIN=1 with the same mixing but converged in 10-40 steps.
