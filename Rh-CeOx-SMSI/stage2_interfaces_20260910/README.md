# Dynamic SMSI — Stage 2: CeOx/Rh(111) interface thermodynamics (round 1)

Created 2026-09-10 after the 9-10 group meeting (supervisor accepted the plan and the two reproduction cases).
Purpose: supervisor's Q1/Q2 — on the same Rh substrate, compare Ce2O3-type layer vs Ce2O3 cluster vs CeO2-type layer,
and obtain the interaction / formation energies as a function of the oxygen chemical potential.

## Frozen calculation contract

| Item | Value | Source |
|---|---|---|
| Code / PAW | VASP 6.3.2, PAW PBE.54 (Rh 04Feb2005, Ce 23Dec2003, O 08Apr2002) | as reproduction line |
| Functional | PBE + U, Dudarev Ueff(Ce 4f) = 5.0 eV | project contract |
| ENCUT / PREC | 400 eV / Accurate | Stage-1 bulk references |
| Substrate | Rh(111) p(3x3), 4 layers, bottom 2 fixed, a0 = 3.8232 A (PBE, Stage-1 Rh bulk) | Stage-1 |
| Overlayer | 2x2 CeO2(111)-type O-Ce-O trilayer commensurate with 3x3 Rh(111); oxide 1x1 = 4.055 A | this stage |
| Oxide strain | +4.2 % vs PBE CeO2 (5.503 A), +4.0 % vs PBE Ce2O3 (a = 3.9008 A) — declared boundary | this stage |
| Cell | a = b = 8.1103 A, gamma = 60 deg, c = 30 A (vacuum >= 15 A), IDIPOL=3 LDIPOL | this stage |
| k-mesh | Gamma-centred 4x4x1 (slabs), 9x9x9 (CeO2 bulk), Gamma (O2) | this stage |
| Smearing | ISMEAR=1, SIGMA=0.10 (metal substrate); E0 (sigma->0) is the reported energy | this stage |
| Spin | ISPIN=2, Ce seeded 1.0 muB, ISYM=0 | this stage |
| Relaxation | IBRION=2, EDIFFG = -0.02 eV/A, LREAL=.FALSE. throughout (no separate static needed) | this stage |
| Mixing | AMIX 0.2 / BMIX 1e-4 / AMIX_MAG 0.8 / AMIN 0.01 | proven on Rh3/CeO2 |

## Systems (inputs/)

| Dir | Atoms | Question | Note |
|---|---|---|---|
| 00_Rh111_clean | Rh36 | reference | ISPIN=1 |
| 10a_Ce2O3_cluster_Odown | Rh36 Ce2 O3 | Q2 cluster | one Ce2O3 unit, O toward Rh (Rh-O contact) |
| 10b_Ce2O3_cluster_Cedown | Rh36 Ce2 O3 | Q2 cluster | one Ce2O3 unit, Ce toward Rh (Rh-Ce contact) |
| 10c_Ce2O4_cluster_Odown | Rh36 Ce2 O4 | Q1xQ2 CeO2-type cluster | two CeO2 units, O toward Rh (added after review) |
| 20a_Ce4O8_layer_regFCC | Rh36 Ce4 O8 | Q1 CeO2 control | Ce0 over fcc hollow |
| 20b_Ce4O8_layer_regTOP | Rh36 Ce4 O8 | Q1 CeO2 control | Ce0 over top site |
| 30a_Ce4O6_layer_2Obot | Rh36 Ce4 O6 | Q1/Q3 Ce2O3 layer | two interface O removed |
| 30b_Ce4O6_layer_2Otop | Rh36 Ce4 O6 | Q1/Q3 Ce2O3 layer | two surface O removed |
| 30c_Ce4O6_layer_1top1bot | Rh36 Ce4 O6 | Q1/Q3 Ce2O3 layer | one surface + one interface O removed |
| 30d_Ce4O6_layer_Atype | Rh36 Ce4 O6 | Q1/Q3 Ce2O3 layer | A-type Ce2O3(0001) bilayer from the relaxed free film 50c, O-down (added after 50c relaxed) |
| 50a–50d films | Ce4O8 / Ce4O6 | reference | free-standing films in the same (strained) cell, for E_int and strain energy |
| 40_O2_gas | O2 | mu_O reference | triplet, 15 A box; PBE overbinding correction and dmu_O(T,p) applied in analysis |
| 42_Ce2O3_gas / 43_Ce2O4_gas | Ce2O3 / Ce2O4 | isolated-cluster references | 15 A box, for E_int of 10a-10c |
| 41_CeO2_bulk | Ce4O8 | mu reference | same INCAR contract as Stage-1 Ce2O3 bulk (ISIF=3, EDIFF 1e-7) |

Existing references reused (Vanda ~/Rh_CeO2_personal/Dynamic_SMSI_stage1_personal_20260821):
Rh bulk E0 = -29.104763 eV / 4 Rh; Ce2O3 A-type AFM E0 = -41.818216 eV / Ce2O3 (FM -41.816754, degenerate within 1.5 meV).

## Energy definitions (to be evaluated after relaxation)

1. Interaction energy at fixed stoichiometry
   E_int = E(CeOx/Rh) - E(Rh slab) - E(free film, same cell)  — separately for Ce4O8 and each Ce4O6 variant.
2. Strain energy of the film: E(film, strained cell) - E(film, own lattice)  (own-lattice film is a round-2 job).
3. Formation energy vs oxygen chemical potential (compares different stoichiometries):
   dG(mu_O) = E(CenOm/Rh) - E(Rh) - n*E(Ce2O3 bulk)/2 - (m - 1.5 n) * mu_O,
   mu_O = 1/2 E(O2) + d(mu_O); d(mu_O) swept from O-rich (0) to O-poor; CeO2 bulk gives the upper stability bound
   (mu_O where Ce2O3 + 1/2 O2 -> 2 CeO2 is thermoneutral).
4. Cluster vs layer (Q2) is compared per Ce2O3 unit at equal mu_O; strain energy from item 2 is reported next to it.

## Boundaries

- Cluster images are 4.2 A apart in the 3x3 cell (period 8.11 A). The low-mismatch alternative is 5x5 Rh with (2sqrt3 x 2sqrt3)R30 oxide (0.4 % vs PBE CeO2; 4x4 would be 6 %); round 2 if the cluster/layer gap is comparable to the film strain energy.
- 0 K electronic energies only; no ZPE / entropy yet. The mu_O sweep is the only link to the 850 C gas atmospheres.
- Initial geometries are guesses; three-vacancy patterns and two registries are the minimum, not an exhaustive search.
