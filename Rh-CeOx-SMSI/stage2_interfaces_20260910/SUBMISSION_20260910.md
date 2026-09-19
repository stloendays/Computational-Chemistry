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

## 2026-09-10 late: default Kerker mixing also oscillates -> A/B SCF test

With VASP default mixing (AMIN 0.01, MAXMIX 40) 20a still oscillated by 0.2-0.5 eV at SCF step 47 and 30a jumped by 1 eV at step 46.
All 11 interface/gas jobs deleted again (partial output in `failed_kerker_default_20260910/`). Two variants submitted, others held back:
- 20a  variant A: ALGO = All, AMIX 0.2 / BMIX 1.0 / AMIX_MAG 0.8 / BMIX_MAG 1.0, SIGMA 0.10
- 30a  variant B: ALGO = Fast, same damped Kerker mixing, SIGMA 0.20
Decision rule: the variant whose dE falls monotonically below 1e-3 eV within ~80 SCF steps is applied to the remaining nine systems.

## 2026-09-10 night: A/B failed -> SCF diagnostics on 20a (static, NELM 90, ALGO Normal, default mixing)

Variant A (ALGO=All) was still descending by 1-12 eV per step at SCF 120; variant B (Fast, SIGMA 0.2) oscillated 0.02-0.4 eV. Killed.
Hypothesis: the self-consistent dipole correction (LDIPOL) on an asymmetric metal/oxide slab with a large interface dipole destabilises the SCF
(the converged cases were either symmetric or insulating). Four 1.5 h statics in `tests/`:
T1 dipole off | T2 dipole off + ISPIN 1 | T3 dipole on + ISPIN 1 | T4 dipole off + Gaussian 0.05.
Decision: whichever converges fixes the protocol; if T1 converges, production runs will converge without LDIPOL first, then restart with LDIPOL from WAVECAR/CHGCAR (VASP-recommended).

## 2026-09-11: diagnostics decided the protocol -> full resubmission

| test (20a static, ALGO Normal, default mixing) | result |
|---|---|
| T1 dipole off, ISPIN 2 | dE ~1e-3 and falling at step 90 (converging) |
| T2 dipole off, ISPIN 1 | converged at step 63 |
| T3 dipole on, ISPIN 1 | oscillating 1e-2 at step 90 |
| T4 dipole off, Gaussian 0.05 | as T1 |

Root cause: self-consistent dipole correction (LDIPOL) on the asymmetric metal/oxide slab. Contract change: LDIPOL = .FALSE. during relaxation;
the dipole energy is evaluated afterwards in a single point restarted from the converged WAVECAR. Mixing: VASP default Kerker (AMIN 0.01, MAXMIX 40), ALGO Normal, SIGMA 0.10.
All 11 interface / gas jobs resubmitted with this contract (IDs in SUBMISSION_20260911.txt on Vanda).

## 2026-09-11 morning: spin-polarised SCF from scratch still too slow -> two-stage jobs

With LDIPOL off the nine slab jobs still sat at dE 1e-2..1e-1 after 100-130 SCF steps (ISPIN=2 from a superposition density),
while the non-spin diagnostic converged in 63 steps. Jobs deleted (partial output in `failed_spin_scratch_20260911/`) and resubmitted as two-stage jobs:
stage 1 `INCAR_stage1_nospin`: ISPIN=1, NSW=0, EDIFF 1e-4, NELM 150 -> WAVECAR/CHGCAR (OUTCAR_stage1, OSZICAR_stage1 kept);
stage 2 `INCAR_stage2_spin_relax`: ISPIN=2 with Ce seeds, ISTART=1, ICHARG=1, AMIX_MAG 0.4, BMIX_MAG 1.0, full relaxation.
The job aborts with rc=3 if stage 1 does not reach EDIFF. Gas clusters 42/43 unchanged (still queued).

## 2026-09-11 midday: per-system fixes

- 10b, 10c: two-stage protocol works (ionic steps with converged SCF). 43_Ce2O4_gas converged (E0 = -40.993138 eV, 111 ionic steps).
- 20a: spin stage 2 hit NELM; 10a: first spin SCF hit NELM and later ionic steps were meaningless. Both deleted.
- Ce4O8 systems (20a, 20b) contain only Ce4+ (free film confirmed 0 muB): relaxed with ISPIN = 1. 20a resubmitted single-stage; 20b's stage 2 replaced by the non-spin relaxation restarted from its stage-1 density.
- Ce3+ systems: 10a resubmitted with stage 2 ALGO = All, NELM 300; 30a-30d (queued) given the same stage-2 INCAR before they start. 10b/10c left running on Davidson.

## 2026-09-11 afternoon: relaxation tolerance relaxed to EDIFF 1e-4 (ALGO=All where not yet in stage 2)

Observed: ALGO=All spin stage (30a/30b) converges monotonically but needs ~220 SCF steps per ionic step; 20b (Davidson, non-spin) spent 180 steps on the last decade to 1e-5.
Decision: relax at EDIFF = 1e-4 (adequate for EDIFFG = -0.02); final energies come from the planned tight single points (EDIFF 1e-6, with/without LDIPOL) on the relaxed geometries.
Applied to 10a, 20a, 30c, 30d (before their stage 2) and 20b (restarted on ALGO=All from its WAVECAR). 10b, 10c (Davidson, converging in 20-50 steps per ionic step) and 30a, 30b (All, running) left untouched.

## 2026-09-11 23:50: scheduler closed to submissions; maintenance window ahead

All routing queues (auto, auto_free, autox) are disabled; running jobs continue. Vanda datacenter maintenance announced: **14 Sep 08:00 to 15 Sep 09:00 (+08)**, cluster unavailable.
Restarts that cannot be submitted are listed in `PENDING_RESUBMIT.txt` on Vanda (`restart_seg.sh` appends there when qsub is refused); `submit_pending.sh` submits them once `auto` is enabled again.
42_Ce2O3_gas: exhausted NSW=150 (E0 -34.050 eV, still moving, max F 1.35 eV/A); prepared for restart, pending. 30d resubmitted earlier with ALGO=All stage 1 (PBS 1361431), running.

## 2026-09-12 16:20: all slab jobs had left the queue overnight -> segment 2

Findings on inspection (queues had been closed to submission overnight; reopened by 16:00):
- 7 jobs (10a, 10b, 10c, 30a, 30b, 30c, 30d) were killed by PBS at the 12 h walltime. The watchdog wrote STOPCAR 30 min before the limit, but VASP only stops after the current ionic step, and one ionic step (100-200 SCF steps) exceeds 30 min. CONTCAR/WAVECAR intact.
- 20a, 20b (non-spin Ce4O8) exited with VASP's "ZBRENT bracketing / sick job" abort after 89 and 58 ionic steps (max free force 0.08 and 0.33 eV/A): CG line-search failure near the minimum.
- 42_Ce2O3_gas exhausted NSW=150 still moving (max F 1.35 eV/A); resubmitted first (PBS 1362598).
Restart (segment 2, from CONTCAR + WAVECAR, ISTART=1/ICHARG=1) for all nine slab jobs: watchdog margin raised to 2.5 h (sleep 34200 in a 12 h job); 20a/20b switched to IBRION=1 (RMM-DIIS, POTIM 0.3). Segment-1 outputs archived in each `seg01_*` directory.
Maintenance: Vanda unavailable 14 Sep 08:00 - 15 Sep 09:00; segment 2 must finish or be checkpointed before then.
Progress at end of segment 1 (ionic steps / max free force, eV/A): 10a 63/0.14, 10b 12/2.78, 10c 20/0.67, 20a 89/0.08, 20b 58/0.33, 30a 10/0.83, 30b 10/1.26, 30c 28/0.18, 30d 58/0.08.
Correction 16:40: the first segment-2 restart pass silently did nothing (helper exited on an empty `seg*` glob under `pipefail`); one 10a job submitted by hand from the initial POSCAR (1362600) was cancelled. Helper fixed and the nine restarts issued again.
