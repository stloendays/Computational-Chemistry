# Stage 7 — plan after the D1–D3 parents (2026-10-25)

Follows the supervisor plan of 2026-10-15 (`weekly_plans/2026-10-15_first_CH4_cleavage_four_models_and_850C_atmospheres.md`):
first C–H cleavage only, ordinary NEB (`LCLIMB = .FALSE.`) first, CI-NEB only on paths that pass the review.

## Where things stand

| Model | Lowest IS | Lowest FS | ΔE (eV) | Next |
|---|---|---|---|---|
| A Rh(111) | A1 CH₄* top | A2 CH₃*(top) + H*(fcc) | +0.26 | ordinary NEB staged (`neb/A_neb`) |
| B Ce₄O₆ layer/Rh | B2 CH₄* over O | B4 CH₃O* + OH* | +0.37 | ordinary NEB staged (`neb/B_neb`) |
| C Ce₂O₃ cluster/Rh | C1 CH₄* perimeter | C3 CH₃*(perimeter Rh) + OH* | −0.23 | ordinary NEB staged (`neb/C_neb`) |
| D Ce₂O₃ cluster/CeO₂ | — | — | — | parent: D1 final, D2/D3 relaxing; D3 lowest so far |

D parents (Γ-point relaxation energy, 10-25 21:00): D1 −1187.27 (final SP −1187.25472), D2 −1186.94, D3 −1188.27.

## Steps

1. **D parent** — wait for D2 and D3 (relax at Γ → 2×2×1 single point; the monitor resumes walltime stops).
   `python stage7_next.py d-parent` lists the three final energies and picks the lowest.
2. **D endpoints** — on the lowest parent, five sets, same site logic as B and C:

   | Set | Start |
   |---|---|
   | D4_CH4_Ce | CH₄ over the upper cluster Ce |
   | D5_CH4_edge | CH₄ over the exposed support O at the cluster edge |
   | D6_CH3Ce_HOc | CH₃ on cluster Ce + H on the top cluster O |
   | D7_CH3Os_HOc | CH₃ on the edge support O (methoxy) + H on cluster O |
   | D8_CH3Ce_HOs | CH₃ on cluster Ce + H on the edge support O |

   Settings as D1–D3: stage A/B at Γ (KPAR 1, NCORE 6), final single point 2×2×1. Ce O C H POTCAR.
   `python stage7_next.py d-endpoints --submit` builds, uploads and queues them (5 jobs).
3. **Ordinary NEB A, B, C** — inputs already on Vanda (`neb/<M>_neb`): 6 IDPP images, `IMAGES 6, SPRING −5,
   LCLIMB .FALSE., IBRION 3, POTIM 0, IOPT 7, EDIFFG −0.05`, model's own INCAR and k mesh, 2 nodes (12 ranks/image),
   72 h with LSTOP watchdog. Endpoint OUTCARs in 00/ and 07/.
   `python stage7_next.py neb A B C --submit` queues them (Vanda limit: 6 running jobs per user).
4. **Path review gate** (supervisor 3.1) — `python3 neb_profile.py <dir>` per path: continuous profile, no atom jumps,
   Ce³⁺ count unchanged (B 4, C 2), image forces. Highest image = ordinary-NEB screening estimate only.
   Watch B: the transferred H travels 4.3 Å to a second lattice O.
5. **D NEB** — once D4–D8 are final: lowest IS → lowest FS,
   `python build_neb.py --pair D <IS> <FS> --raw <dir>` then `stage7_next.py neb D --submit`.
6. **CI-NEB** — only for paths that pass step 4: CONTCAR → POSCAR of each image, `LCLIMB = .TRUE.`, tighter EDIFFG;
   then a frequency check on the climbing image (one imaginary mode along C–H).
7. **Report** — E_a tagged as ordinary-NEB estimate / CI-NEB / TS validated; update deck slides 15–18 and the table.

## Scripts (this folder)

| Script | Job |
|---|---|
| `build_D_endpoints.py` | D4–D8 inputs from a parent CONTCAR (preview built on the 10-25 D3 geometry: `next_steps/D_endpoints_preview`) |
| `build_neb.py` | ordinary-NEB inputs: H matching, IDPP images, INCAR/KPOINTS/PBS |
| `neb_profile.py` | energy profile, forces and magnetisation per image (plain python3 on Vanda) |
| `stage7_next.py` | driver: D parent check, D endpoints, NEB upload and submit |
