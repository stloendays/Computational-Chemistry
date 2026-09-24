# Dynamic SMSI — Stage 3: CeO2 unit / Ce2O3 cluster on Rh(111), then CH4 activation

Created 2026-09-24. Task source: the supervisor's `discussion progress` document (Xiaoyan Li revision) and the
binding rules in GitHub `stloendays/Computational-Chemistry` (33efa62, 52ee3fe, 7d36d18, 5d0747a, 053be74):
amorphous SMSI = Ce2O3 cluster/Rh, crystalline SMSI = Ce2O3 layer/Rh, CeO2 only as control/reference,
ISPIN = 2 everywhere, slab bottom plane at z = 0 with the whole vacuum above, ENCUT = 450 eV.

1. **Step 1 (this directory, `inputs/`):** interaction energy of one CeO2 unit and of one Ce2O3 cluster with Rh(111).
2. **Step 2 (built after step 1):** CH4 -> CH3 -> CH2 on Rh(111), Rh(111) + Ce2O3 cluster and Ce2O3(0001).

## Calculation contract

| Item | Value |
|---|---|
| Code / PAW | VASP 6.3.2 (`vasp_632_vtst_solpp_beef_std`), PAW PBE.54: Rh 04Feb2005, Ce 23Dec2003, O 08Apr2002 (C 08Apr2002, H 15Jun2001 for step 2) |
| Functional | PBE + U, Dudarev, Ueff(Ce 4f) = 5.0 eV, LMAXMIX = 6 |
| ENCUT / PREC | **450 eV** / Accurate, LASPH, ADDGRID |
| Spin | **ISPIN = 2 in every stage**, MAGMOM Ce 1.0, others 0; ISYM = 0 |
| Substrate | Rh(111) p(4x4), 4 layers, bottom 2 fixed, a0 = 3.8232 A (Stage-1; `S1_00` re-checks at 450 eV); a = 10.814 A |
| Cell / vacuum | c = 30 A, bottom Rh plane at z = 0, vacuum above the highest atom 19.0–23.4 A (>= 15 A) |
| k-mesh | Gamma 3x3x1 (slabs), Gamma only (15 A gas boxes), 21x21x21 (bulk) |
| Smearing | ISMEAR = 1, SIGMA = 0.10 (slabs, bulk); ISMEAR = 0, SIGMA = 0.05 (gas); E0(sigma -> 0) is reported |
| Electronic | EDIFF 1e-5; Kerker mixing, AMIN 0.01, MAXMIX 40, AMIX_MAG 0.4, BMIX_MAG 1.0; LREAL = .FALSE. |
| Ce systems | stage A: spin-polarised single point from scratch, ALGO = All, NELM 500; stage B: relaxation from A's WAVECAR/CHGCAR, ALGO = Normal |
| Ionic | FIRE (IBRION 3, IOPT 7, MAXMOVE 0.2), EDIFFG -0.02 eV/A, NSW 400; gas CG (IBRION 2) |
| Dipole | IDIPOL 3, LDIPOL off during relaxation; dipole-corrected final single points after acceptance |
| PBS | `#PBS -P CFP03-CF-126`, 36 cores (bulk 8), 72 h walltime, watchdog at 250200 s (LSTOP relax / LABORT SP) |

## Step-1 systems (`inputs/`)

| Dir | Atoms | Role | Start |
|---|---|---|---|
| S1_00_Rh_bulk_450 | Rh1 | a0 at 450 eV | fcc primitive, ISIF 3 |
| S1_01_Rh111_4x4 | Rh64 | substrate reference | ideal slab |
| S1_12a_Ce2O3_Rh_from10a | Rh64 Ce2 O3 | Ce2O3 cluster (amorphous model) | round-1 lowest 10a geometry, same registry |
| S1_12b_Ce2O3_Rh_from10b | Rh64 Ce2 O3 | Ce2O3 cluster, second start | round-1 10b geometry, same registry |
| S1_11a_CeO2_Rh_flat | Rh64 Ce1 O2 | CeO2 unit (control) | both O in neighbouring fcc hollows, Ce above |
| S1_11b_CeO2_Rh_Cedown | Rh64 Ce1 O2 | CeO2 unit, second start | Ce on an fcc hollow in contact with Rh, O bent up |
| S1_21_CeO2_gas | Ce1 O2 | gas-phase reference | bent O-Ce-O, 15 A box |
| S1_22_Ce2O3_gas | Ce2 O3 | gas-phase reference | round-1 relaxed 42 |
| S1_02_Rh111_3x3 | Rh36 | substrate reference of the layer | ideal slab, Gamma 4x4x1 |
| S1_31_Ce4O6_layer_Rh3x3 | Rh36 Ce4 O6 | Ce2O3 layer (crystalline model), mainline comparison | round-1 30a relaxed, z re-zeroed, flags kept |
| S1_23_Ce2O3_bulk_AFM | Ce2 O3 | per-unit reference (bulk A-type, AFM) | stage-1 relaxed lattice, ISIF 3, k 7x7x5 |

The last three were added on 2026-09-24 ("全部都按新设置"): the mainline cluster-vs-layer comparison needs the
layer under the same contract. Cluster vs layer per Ce2O3 unit: E_int/n with the gas unit, and
E_f/n = [E(X/Rh) − E(Rh) − n·E(Ce2O3, bulk)]/n.

## Energy definition

E_int(X) = E(X/Rh(111)) − E(Rh(111)) − E(X, gas), X = CeO2 unit or Ce2O3 unit; also reported per Ce.
All terms: same ENCUT, PAW, U, spin treatment and LREAL; the lowest of the two starts is the reported value,
both are kept. Acceptance per system: final SCF reached EDIFF, free-atom Fmax <= 0.02 eV/A (atoms flagged T T T only),
bottom two Rh layers unmoved, Ce magnetic moments reported (Ce3+ ~1 muB).

## Step 2 plan (built from the accepted step-1 structures)

CH4(g), CH4*, CH3* + H*, CH2* + 2H* on (i) Rh(111) 4x4, (ii) the accepted Ce2O3 cluster/Rh(111) 4x4 at Rh, Ce and
Rh–Ce interface sites, (iii) a Ce2O3(0001) slab; references CH4 and H2 in 15 A boxes; same contract. Reaction energies
of CH4* -> CH3* + H* and CH3* -> CH2* + H* first; barriers only if the supervisor asks for them.

## Status

2026-09-24 22:02 / 22:34: step-1 inputs built (`build_stage3.py`, `inputs/MANIFEST.sha256`) and submitted,
PBS 1393602–1393609 and 1393717–1393719 on CFP03-CF-126; working directory
`/scratch/junbotong/Dynamic_SMSI_stage3_units_CH4_20260924` (log `SUBMISSION_stage3.md`).
Accepted so far: Rh a0(450 eV) = 3.8238 A; CeO2 gas E0 = −19.08022 eV (Ce4+); Ce2O3 gas E0 = −34.23422 eV (2 Ce3+).
Monitoring: `MONITOR_HANDOFF.md` — Task Scheduler `vanda-stage3-monitor-5h` every 5 h, Claude Code CLI takeover.
