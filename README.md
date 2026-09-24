# Computational-Chemistry

Junbo Tong (NUS). Small, reproducible input sets and result summaries for VASP work.
Large binaries (POTCAR, WAVECAR, CHGCAR, OUTCAR) are never committed; the licensed PAW set is assembled on the cluster from `POTCAR.spec`.

- `Rh-CeOx-SMSI/` — personal project: atmosphere-dependent dynamic SMSI of Rh/CeO2 (CeOx overlayers on Rh(111)).
  - `stage1_bulk_references_20260821/` — Rh, Ce2O3 bulk references.
  - `stage2_interfaces_20260910/` — CeOx/Rh(111) interface thermodynamics, round 1 (contract, inputs, submission log).


## Project-wide slab geometry rule

For every slab / surface model in this repository, use the following mandatory z-coordinate convention:

- **No vacuum is allowed below the slab.** Translate the structure so that the bottommost substrate atomic plane is at **z = 0 Å** (fractional z = 0, within numerical tolerance).
- Put the **entire vacuum region above the slab**, along +z. Do not vertically center the slab in the cell.
- Keep at least **15 Å of continuous vacuum above the highest atom** unless a specific convergence test requires more.
- When regenerating or exporting a POSCAR/CONTCAR-derived input, re-zero the slab in z before submission and preserve the selective-dynamics flags.
- Legacy structures that contain a bottom z-offset may remain as archived results, but any new or regenerated production input must follow this convention.

This is a project modeling convention for consistency and unambiguous vacuum-thickness reporting.
