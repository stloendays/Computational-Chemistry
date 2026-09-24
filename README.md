# Computational-Chemistry

Junbo Tong (NUS). Small, reproducible input sets and result summaries for VASP work.
Large binaries (POTCAR, WAVECAR, CHGCAR, OUTCAR) are never committed; the licensed PAW set is assembled on the cluster from `POTCAR.spec`.

- `Rh-CeOx-SMSI/` — personal project: atmosphere-dependent dynamic SMSI of Rh/CeO2 (CeOx overlayers on Rh(111)).
  - `stage1_bulk_references_20260821/` — Rh, Ce2O3 bulk references.
  - `stage2_interfaces_20260910/` — CeOx/Rh(111) interface thermodynamics, round 1 (contract, inputs, submission log).
  - `stage3_units_CH4_20260924/` — one CeO2 unit / one Ce2O3 cluster on Rh(111) 4x4 (step 1, interaction energies), then CH4 -> CH3 -> CH2 (step 2); ENCUT 450, ISPIN 2, z = 0.


## Rh-CeOx-SMSI binding scientific rules

For the Rh-CeOx-SMSI project, the supervisor's `discussion progress` document is the source of truth. Unless the supervisor explicitly revises the interpretation below:

- **The SMSI overlayer composition is treated as Ce2O3-like reduced ceria in the mainline workflow.** It is not treated as an unresolved CeO2-vs-Ce2O3 composition question.
- **Amorphous SMSI -> Ce2O3 cluster/Rh.** A finite Ce2O3 cluster on Rh represents the amorphous overlayer.
- **Crystalline SMSI -> Ce2O3 layer/Rh.** A Ce2O3 layer/bilayer on Rh represents the crystalline overlayer.
- **CeO2 remains the support/reference/control.** Existing CeO2-type calculations may be retained as controls or historical data, but must not redefine the main research question unless the supervisor explicitly reopens that comparison.
- **Main scientific comparison:** Ce2O3 cluster/Rh vs Ce2O3 crystalline layer/Rh, followed by the reaction and electronic-structure analyses required by the discussion.
- **All calculations use spin polarization:** new jobs, restarts, refinements, references, adsorption calculations and reaction calculations use `ISPIN = 2`. Legacy `ISPIN = 1` results must not be mixed directly into a new energy comparison without rerunning or validating them under the spin-polarized contract.
- Ce-containing systems retain **DFT+U with Ueff(Ce 4f) = 5 eV** unless the supervisor explicitly changes it.
- Do not independently expand the main workflow beyond the discussion-defined questions. Extra phase diagrams, vacancy families, registry searches or other auxiliary calculations are secondary unless required to answer a discussion-defined question or explicitly requested.


## Project-wide slab geometry rule

For every slab / surface model in this repository, use the following mandatory z-coordinate convention:

- **No vacuum is allowed below the slab.** Translate the structure so that the bottommost substrate atomic plane is at **z = 0 Å** (fractional z = 0, within numerical tolerance).
- Put the **entire vacuum region above the slab**, along +z. Do not vertically center the slab in the cell.
- Keep at least **15 Å of continuous vacuum above the highest atom** unless a specific convergence test requires more.
- When regenerating or exporting a POSCAR/CONTCAR-derived input, re-zero the slab in z before submission and preserve the selective-dynamics flags.
- Legacy structures that contain a bottom z-offset may remain as archived results, but any new or regenerated production input must follow this convention.

This is a project modeling convention for consistency and unambiguous vacuum-thickness reporting.

## Project-wide plane-wave cutoff rule

- **ENCUT = 450 eV for every new VASP calculation** (new jobs, references, restarts and any system entering a new energy comparison), set by the user on 2026-09-24.
- Legacy 400 eV (stage 2 rounds 1-2) and 500 eV (round-2 unified single points) results stay as archived records and are not mixed into new comparisons.
