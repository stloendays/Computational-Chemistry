# Stage 7 — first C–H cleavage of CH₄ on four models (supervisor plan 2026-10-15)

CH₄* → CH₃* + H*/OH* only. Kinetics: ordinary NEB (`LCLIMB = .FALSE.`) first, path review, CI-NEB only on
paths that pass the review. Plan: `../weekly_plans/2026-10-15_first_CH4_cleavage_four_models_and_850C_atmospheres.md`;
next steps: `PLAN_after_D_parent_20261025.md`. Status as of 2026-10-27.

**Model B (Ce₄O₆ layer / Rh(111)), status 2026-11-07: [`B_layer_status_20261107.md`](B_layer_status_20261107.md)**
— endpoints, the failed first NEB and why, the new IS B5 / B5b, next steps.

## Current line: Rh(111) p(3×3) and CeO₂(111) p(2×2) (supervisor, 2026-10-29)

The 2026-10-29 guidance changes the cells and the energy definition (plan: `PLAN_20261029_advisor_3x3.md`).

- **Cells:**
  - A and C move to Rh(111) p(3×3), as B;
  - D moves to CeO₂(111) p(2×2) with 3 trilayers. D is proposed / preliminary.
- **Energy:** E₀ (σ → 0) of the converged relaxation, with no separate final single point. Each system runs stage A (spin pre-convergence), then the relaxation.
- **Inputs:** `inputs_3x3/`, built by `build_3x3.py`. LDAU is set per species: U = 5 eV on Ce 4f, and no LDAU block without Ce.
- **Monitor:** `monitor/monitor_stage7.py`. A Windows task runs it every 5 h through `monitor_stage7.ps1`. It writes `results/stage7_3x3_table.md` on Vanda.
- The 4×4 values below are kept as history and are not compared with the 3×3 values.

Accepted so far (relaxation E₀):

| System | E₀ (eV) | Result |
|---|---|---|
| A0 Rh(111) p(3×3) | −247.32369 | — |
| A1 CH₄* top | −271.37836 | E_ads −0.02 eV |
| A2 CH₃*(top) + H*(fcc) | −271.11411 | ΔE +0.26 eV |
| C0 Ce₂O₃/Rh(111) p(3×3) | −285.80999 | 2 Ce³⁺ |
| D0 CeO₂(111) p(2×2) 3TL | −287.60259 | 0 Ce³⁺ |
| D3 Ce₂O₃/CeO₂(111) p(2×2), gas-phase geometry | −325.37274 | 2 Ce³⁺ |

- C1–C5 and D1 are relaxing; C7 and C8 are queued (jobs in `SUBMISSION_stage7.txt`).
- The lower of D1 and D3 becomes the D parent.
- The B ordinary NEB 1502824 (B2 → B4) stopped after 56 steps without converging, and B is on hold.

| Model | Cell | Ce³⁺ |
|---|---|---|
| A | Rh(111) 4×4 | — |
| B | Ce₄O₆ layer L6 / Rh(111) 3×3 | 4 |
| C | Ce₂O₃ cluster C3a / Rh(111) 4×4 | 2 |
| D | Ce₂O₃ cluster / CeO₂(111) p(4×4) 3TL (Ce₅₀O₉₉) | — |

## Settings (every system)

PBE+U, Ueff(Ce 4f) = 5 eV, ENCUT 450 eV, ISPIN 2, z = 0 bottom with ≥ 15 Å vacuum above.
Three stages per endpoint:

| Stage | Purpose | Key tags |
|---|---|---|
| A | spin single point | ALGO All, NELM 500, MAXMIX 40, IBRION −1 |
| B | relaxation | IBRION 2, EDIFFG −0.02, ISMEAR 1 / SIGMA 0.10 |
| C | final single point (energies below) | ISMEAR 0 / SIGMA 0.05, EDIFF 1E-6 |

D: relaxation at Γ (KPAR 1 / NCORE 6), final single point at 2×2×1 (ISTART 0 / ICHARG 1).
Walltime 72 h, STOPCAR watchdog at 250200 s, project CFP04-CF-046.

## Endpoint results (stage-C E0, `results/E_final_sp.txt`)

E_ads = E(CH₄*) − E(parent) − E(CH₄,g); ΔE = E(FS) − E(lowest IS) of the same model.

| Model | Lowest IS | E_ads (eV) | Final state | ΔE (eV) |
|---|---|---|---|---|
| A | A1 CH₄* top | −0.01 | A2 CH₃*(top) + H*(fcc) | +0.26 |
| B | B2 CH₄* over O | −0.04 | B4 CH₃O* + OH* | **+0.37** |
| | | | B3 CH₃*(Ce) + OH* | +1.31 |
| C | C1 CH₄* perimeter | −0.11 | C3 CH₃*(perimeter Rh) + OH*(cluster O) | **−0.24** |
| | | | C6 CH₃*(far Rh) + H*(fcc) | +0.41 |
| | | | C4 CH₃*(perimeter Rh) + H*(fcc) | +0.47 |
| | | | C5 CH₃*(Ce) + OH* | +0.79 |

Relaxed structures: `results/final_structures/<name>_CONTCAR`. Analysis: `results/analyse_stage7.py` →
`results/stage7_energies.json`. ΔG figure with the two 850 °C atmospheres (CO₂ and CH₄:CO₂ = 1:1 feed):
`results/Fig_dG_850C_two_markers.*`, μO from `results/muO_DRM_feed_equilibrium.*`.

### D parents (Ce₂O₃ cluster on CeO₂(111))

| Start | State 2026-10-27 | E (Γ, eV) |
|---|---|---|
| D1 hO, 2 O down | converged; final SP (2×2×1) −1187.25472 | −1187.27 |
| D2 hO, 1 O down | relaxing (3rd segment) | ≈ −1187.0 |
| D3 gas-phase geometry | relaxing (3rd segment) | ≈ −1188.50 (lowest) |

The lowest final parent carries D4–D8 (`scripts/build_D_endpoints.py`, `scripts/stage7_next.py d-endpoints`).

## Ordinary NEB (`neb/`)

One path per model, lowest IS → lowest FS: A1 → A2, B2 → B4, C1 → C3.
Six IDPP images (ASE), FS H atoms matched onto IS H by minimum displacement (`scripts/build_neb.py`).
INCAR = the model's stage-B INCAR plus IMAGES 6, SPRING −5, LCLIMB .FALSE., IBRION 3, POTIM 0, IOPT 7 (VTST FIRE),
EDIFFG −0.05, NSW 500, KPAR 2 / NCORE 6, 2 nodes × 36 ranks. Endpoint OUTCARs (stage B, same smearing) sit in 00/ and
07/. `neb_profile.py` reads the last energy of every ionic step per image.

**Ce-containing paths (B, C) run in two steps inside one job** (`scripts/neb_two_step_20261027.sh`):

1. stage A on all six images: the endpoint's own `INCAR_stageA_spinSP` + IMAGES 6, the NEB parallel layout and
   `MAGMOM` = 1 on every Ce, 0 elsewhere (`INCAR_stageA_images`); one resume round from the image WAVECARs if NELM is
   hit (`INCAR_stageA_images_r1`); `STAGEA_DONE` marks completion;
2. the NEB from each image's own WAVECAR (`INCAR_neb`, ISTART 1 / ICHARG 0).

This follows the VTST/VASP practice of converging an image's electronic state in a single point and then
letting the NEB read that image's WAVECAR from its own directory.

| Path | Job | State 2026-10-27 |
|---|---|---|
| A | 1493946 | 47 steps, Fmax 0.14 eV/Å; highest image 05 +0.75 eV, ΔE +0.26 (ordinary-NEB estimate, not converged) |
| B | 1497610 | stage A on the six images |
| C | 1497611 | stage A on the six images |

`neb/A_neb/neb_profile_snapshot_20261027.txt` holds the A profile at the time of this commit.

### Attempts that failed (outputs kept on Vanda in `neb/<M>_neb/failed_*`)

| Date | Start | Outcome |
|---|---|---|
| 10-26 | images 01–03 / 04–06 read the IS / FS endpoint WAVECAR | images away from the ends diverged (A04 −1508 eV, B05 −1220 eV, C04 −3.8e7 eV) |
| 10-26 | from scratch, default MAGMOM (1 μB per atom) | B, C images fell into high-spin states (B06 −326.5 vs ≈ −353 eV, mag 31–42; C mag 58) |
| 10-27 | from scratch, MAGMOM Ce 1, ALGO Normal / NELM 300 | B, C SCF not converged (moments 2.7–3.8 and 0.6–1.6) |

A runs from scratch (no Ce) and is unaffected.

## Files

- `inputs/<system>/` — endpoint inputs (POSCAR, INCAR_stage*, KPOINTS, job.pbs, POTCAR.spec); `build_stage7.py`,
  `gamma_switch_20261017.py` (D relax at Γ).
- `neb/<M>_neb/` — NEB inputs as running on Vanda (`job_neb.pbs.orig_20261027` = the single-step script replaced
  by the two-step one).
- `scripts/` — `build_neb.py`, `neb_profile.py`, `build_D_endpoints.py`, `stage7_next.py`, `neb_two_step_20261027.sh`.
- `results/` — energies, analysis and figure scripts, relaxed structures.
- `SUBMISSION_stage7.txt` — every qsub with its reason.
