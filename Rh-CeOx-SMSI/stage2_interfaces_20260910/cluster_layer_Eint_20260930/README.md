# Dynamic SMSI — Stage 5: Ce2O3 / Ce2O4 cluster vs layer interaction energy with Rh(111)

Task (supervisor, 2026-09-30; GitHub `Rh-CeOx-SMSI/stage2_interfaces_20260910/TASK_20260930_CLUSTER_LAYER_EINT.md`):

1. Build Ce2O4 cluster/Rh(111) and Ce2O3 cluster/Rh(111).
2. DFT with reasonable magnetic moments, IBRION = 2, no extra single point.
3. E_int = E(CexOy/Rh(111)) − E(CexOy) − E(Rh(111)).
4. Compare with the 2026-09-28 Step-3 layer E_int/2 at Ce:O = 2:3 and 2:4: does the cluster or the layer interact
   more strongly with Rh(111)? Plot the result.

## Calculation contract

| Item | Value |
|---|---|
| Code / PAW | VASP 6.3.2, PAW PBE.54: Rh 04Feb2005, Ce 23Dec2003, O 08Apr2002 |
| Functional | PBE + U, Dudarev, Ueff(Ce 4f) = 5.0 eV, LMAXMIX 6 |
| ENCUT / PREC | 450 eV / Accurate, LASPH, ADDGRID, LREAL .FALSE. |
| Spin | ISPIN = 2, **no MAGMOM line** (VASP default 1 μB per atom); moments checked after convergence |
| Substrate | Rh(111) p(4×4), 4 layers, bottom 2 fixed, a0 = 3.8232 Å; bottom Rh plane at z = 0 |
| Cell | a = 10.814 Å, γ = 60°, c = 25.924 Å (15 Å above the highest atom of the tallest start) |
| k-mesh | Γ 3×3×1 (slabs; same density as Γ 4×4×1 on the 3×3 layer cell), Γ only (15 Å gas boxes) |
| Smearing | slabs ISMEAR 1 / SIGMA 0.10; gas ISMEAR 0 / SIGMA 0.05; E0 (σ → 0) reported |
| Ionic | IBRION 2, POTIM 0.20, EDIFFG −0.02 eV/Å; the final E0 of the relaxation is the energy (no extra single point) |
| Electronic | EDIFF 1e-5; Ce systems: stage A spin SP from scratch (ALGO All, NELM 500) → stage B relaxation from its WAVECAR |
| Dipole | IDIPOL 3, LDIPOL off |
| PBS | CFP04-CF-046, 36 cores, 72 h, watchdog 250200 s |

4×4 rather than 3×3: in 3×3 a Ce2Oy cluster is ~2.3 Å from its own periodic image (stage 3); in 4×4 the smallest
cluster–image gap of the starts is 5.2–7.9 Å.

## Systems (`inputs/`, built by `build_stage5.py`)

| Dir | Atoms | Role | Start |
|---|---|---|---|
| R4_Rh111_4x4 | Rh64 | Rh(111) reference | ideal slab |
| C3a_Ce2O3_Rh_from12b | Rh64 Ce2 O3 | Ce2O3 cluster | stage-3 S1_12b relaxed (lowest stage-3 Ce2O3 cluster) |
| C3b_Ce2O3_Rh_from12a | Rh64 Ce2 O3 | Ce2O3 cluster, 2nd start | stage-3 S1_12a relaxed |
| C4a_Ce2O4_Rh_from10c | Rh64 Ce2 O4 | Ce2O4 cluster | round-1 10c, same registry, rebuilt around the Ce pair |
| C4b_Ce2O4_Rh_from12b_plusO | Rh64 Ce2 O4 | Ce2O4 cluster, 2nd start | S1_12b + one O in the fcc hollow next to a Ce |
| G3_Ce2O3_gas | Ce2 O3 | isolated reference | stage-3 S1_22 relaxed |
| G4_Ce2O4_gas | Ce2 O4 | isolated reference | round-1 43 relaxed |

The lower-energy start of each composition is the reported cluster; both are kept.

## Energies

- E_int(cluster) = E(Ce2Oy/Rh) − E(Ce2Oy, gas) − E(Rh(111) 4×4), per Ce2Oy unit.
- Layer (stage 4, 2026-09-28 Step 3): E_int(Ce4O6/Rh) = −3.267 eV and E_int(Ce4O8/Rh) = −6.008 eV per 3×3 cell,
  i.e. −1.634 and −3.004 eV per Ce2O3 / Ce2O4 unit (E_int/2).
- More negative E_int = stronger interaction with Rh(111).
- `analyse_stage5.py` → `results/stage5_Eint.md`, `results/stage5_Eint.json`, `results/Fig_cluster_vs_layer_Eint.png`.

## Status

2026-09-30 16:20 SGT: submitted PBS 1415466–1415472 (log `SUBMISSION_stage5.md`). Monitor: Task Scheduler
`vanda-stage5-monitor-5h`, 监控总台 id `vanda-stage5` (`MONITOR_HANDOFF.md`).
