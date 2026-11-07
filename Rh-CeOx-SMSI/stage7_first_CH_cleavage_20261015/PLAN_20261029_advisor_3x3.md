# Stage 7 — revised plan after the supervisor's guidance of 2026-10-29

Source: Notion「14｜下一步路线与当前优先级」, entry 2026-10-29. It replaces the model sizes of `PLAN_after_D_parent_20261025.md`. The 10-15 order is unchanged: end states → ordinary NEB → path check → CI-NEB for sound paths only. The scope is still the first C–H cleavage.

## 1. Model sizes

| Model | Before | Now |
|---|---|---|
| A Rh(111) | p(4×4), 64 Rh | **p(3×3), 36 Rh**, 4 layers, bottom 2 fixed |
| B Ce₄O₆ layer/Rh(111) | p(3×3) | p(3×3), unchanged |
| C Ce₂O₃ cluster/Rh(111) | p(4×4) | **p(3×3)**, C3a cluster re-relaxed on 36 Rh |
| D Ce₂O₃ cluster/CeO₂(111) | p(4×4), 3 TL, 149 atoms | **p(2×2), 3 TL, 36 + 5 = 41 atoms** (proposed / preliminary) |

- k-mesh: Γ-centred 4×4×1 for every 3×3 Rh cell, as in B. D p(2×2) also uses 4×4×1, because its lateral size is close.
- The 4×4 energies of A and C are not compared with the new 3×3 values. They stay in `results/` as history.

## 2. In-plane sizes and mismatch (for the deck)

All values come from the cells used.

- **Rh(111)**:
  - 1×1 = 2.7034 Å (a₀ = 3.8232 Å, PBE);
  - p(3×3) = 8.110 Å.
- **CeO₂(111)**: 1×1 = 3.858 Å (a = 5.456 Å, from the D support slab).

| Quantity | Value |
|---|---|
| B: Ce₄O₆ layer Ce–Ce (2×2 oxide on 3×3 Rh, commensurate) | 4.055 Å |
| B mismatch vs PBE+U Ce₂O₃ (a = 3.901 Å) | **+4.0 %** (layer under tension) |
| B mismatch vs PBE+U CeO₂(111) (a/√2 = 3.891 Å) | +4.2 % |
| D: CeO₂(111) p(2×2) lateral size vs Rh(111) p(3×3) | 7.716 vs 8.110 Å, **−4.9 %** (area −9.5 %) |
| D: CeO₂(111) p(3×3) lateral size vs Rh(111) p(3×3) | 11.574 vs 8.110 Å, +42.7 % |

D has no Rh. The −4.9 % compares two supercell sizes and is not an Rh–CeO₂ interface mismatch. The deck says so.

## 3. D supercell check

The cluster geometry is D1 relaxed on p(4×4), with a lateral extent of 4.41 Å. The image distance is the nearest distance between an atom of the cluster and an atom of its periodic image.

| Cell | Atoms | Cluster–image distance |
|---|---|---|
| CeO₂(111) p(2×2) | 41 | 3.67 Å |
| CeO₂(111) p(3×3) | 86 | 7.42 Å |
| CeO₂(111) p(4×4), current | 149 | (current runs) |
| Reference: C cluster on Rh(111) p(3×3) | — | 5.25 Å |

Work on p(2×2) + 3 TL as the proposed model. It is frozen only after the check above, and the deck labels it "proposed / preliminary".

## 4. Final single points

- No separate final single point by default. The reported energy is E₀ (σ → 0) of the converged relaxation (ISMEAR 1, SIGMA 0.10, EDIFFG −0.02).
- The new jobs therefore run only stage A (spin pre-convergence) and then the relaxation.
- B is reported on the same footing, using the E₀ of its relaxations, so that A/B/C/D share one definition.
- A single point is added only where DOS, Δρ or Bader analysis is actually needed.

## 5. Calculations

| Step | Systems | Note |
|---|---|---|
| A3×3 | A0_ref, A1_CH4_top, A2_CH3top_Hfcc | same sites as before |
| C3×3 | C0_ref, C1_CH4_perimRh, C2_CH4_Ce, C7_CH4_Ot; C3_CH3perimRh_HOt, C4_CH3perimRh_Hfcc, C5_CH3Ce_HOt, C6_CH3farRh_Hfcc, C8_CH3Ot_HOb | includes the two O_t sites |
| D2×2 parent | D0 CeO₂(111) p(2×2) 3 TL; Ce₂O₃ cluster starts D1–D3 (same three registries) | lowest one becomes the D parent |
| D2×2 end states | CH₄* (over Ce, over edge O), CH₃*+H*_O variants | after the parent |
| B | ordinary NEB 1502824 continues | already p(3×3) |
| NEB | A, C (and D) on the new cells: ordinary NEB → path check → CI-NEB | same settings as before |
| Deck | mismatch table, D marked preliminary, energies = relaxation E₀ | |

## 6. Running 4×4 jobs made obsolete by the new sizes

| Job | System |
|---|---|
| 1497611 | C NEB (p(4×4)) |
| 1506831 | C7_CH4_Ot (p(4×4)) |
| 1506832 | C8_CH3Ot_HOb (p(4×4)) |
| 1506867 | D2 relaxation r4 (CeO₂ p(4×4)) |
| 1506857 | D3 final single point (CeO₂ p(4×4)) |

B NEB 1502824 is p(3×3) and keeps running.

## 7. Status 2026-10-29 17:10 (user: "停掉并建 3×3", "提交并停 D5–D8")

- **Cancelled.** All the p(4×4) jobs listed in section 6, plus the p(4×4) D4–D8 end states:
  - 1507327 had already failed with Exit 127;
  - 1507330–334 were cancelled.
- **Built.** `inputs_3x3/` with `build_3x3.py`. There are 14 systems, and each runs stage A followed by the relaxation.
- **Changes from the 4×4 set:**
  - C6 (CH₃ on a far Rh) is dropped. In p(3×3) the farthest top Rh is a perimeter Rh, so C6 was identical to C4.
  - D2 is dropped. Its spread p(4×4) cluster comes within 2.16 Å of its own image in p(2×2).
- **Submitted.** Jobs 1507563–576, recorded in `SUBMISSION_stage7.txt`.
- **Monitor.** `monitor_stage7.py` now carries a `SYSTEMS3` set for the two-stage chains. It writes `results/stage7_3x3_table.md`.
- **Next.**
  - D parent: the lower of D1 and D3 on p(2×2).
  - D end states.
  - Ordinary NEBs for A and C on the new cells.
  - Deck: add the mismatch table.

## 8. Status 2026-11-03

- **Input fix (11-02).** `build_3x3.py` now writes LDAU per species:
  - U = 5 eV on Ce 4f only;
  - no LDAU block for Rh/C/H (as in the 4×4 A inputs).

  The first build had copied B0's `LDAUL = -1 3 -1` to every set. All systems except C0_ref were resubmitted as jobs 1510390–402, with the same POSCARs. The old runs are kept in `inputs_3x3_bad_ldau_20261102/` on Vanda.
- **Monitor.** It now stops on VASP input errors ("I REFUSE TO CONTINUE") and checks LDAUL against the POSCAR species.
- **Accepted (relaxation E₀):**

| System | E₀ (eV) | Result |
|---|---|---|
| A0_ref | −247.32369 | — |
| A1_CH4_top | −271.37836 | E_ads −0.02 eV |
| A2_CH3top_Hfcc | −271.11411 | ΔE +0.26 eV |
| C0_ref | −285.80999 | 2 Ce³⁺ |
| D0 CeO₂(111) p(2×2) | −287.60259 | 0 Ce³⁺ |
| D3_Ce2O3_gasgeom | −325.37274 | 2 Ce³⁺ |

- **Running:** C1–C5 and D1. D1 is already about 1.1 eV below D3 and is likely the D parent.
- **Queued:** C7 and C8.
- **B.** NEB 1502824 ended with Exit 143 after 64.9 h (56 steps, not converged). Per the user (11-02), B is left as is for now.

## 9. D end states, 2026-11-04 (user: "建并提交")

- **D parent: D1.** E₀ = −326.73516 eV, 2 Ce³⁺, 1.36 eV below D3.
- **Builder:** `build_D_3x3_endpoints.py`. The cell is c = 29.984 Å (tallest start + 15 Å), and D1 is re-relaxed at the same c (`D1r_ref_vac15`) as the reference for E_ads.
- **Site changes from the p(4×4) set.** In p(2×2) all four top-plane support O are bonded to the cluster, so there is no exposed edge O.

| Set | Start | Job |
|---|---|---|
| D1r_ref_vac15 | D1 relaxed, c = 29.984 Å | 1518228 |
| D4_CH4_Ce | CH₄ over the upper cluster Ce | 1518229 |
| D5_CH4_Oc | CH₄ over the top cluster O (replaces "over edge O") | 1518230 |
| D6_CH3Ce_HOc | CH₃ on cluster Ce + H on the bridging cluster O | 1518231 |
| D7_CH3Oc_HOc | CH₃O* on the top cluster O + H on the bridging cluster O | 1518232 |
| D8_CH3Ce_HOs | CH₃ on cluster Ce + H on support O (most open) | 1518233 |

## 10. Results and next steps, 2026-11-05

### Accepted end states (relaxation E₀)

| Model | Lowest CH₄* | E_ads (eV) | Lowest FS | ΔE (eV) |
|---|---|---|---|---|
| A | A1, Rh top | −0.02 | A2 CH₃*(top) + H*(fcc) | +0.26 |
| B | B2, over O | −0.04 | B4 CH₃O* + H*_O | +0.37 |
| C | C1, cluster perimeter | −0.14 | C3 CH₃*(perimeter Rh) + H*_O | −0.12 |
| D | D4, over Ce | pending D1r | D7 CH₃O* + H*_O | −1.50 |

- **C, other states:**
  - C2 (CH₄* over Ce): E_ads −0.09 eV.
  - C7 (CH₄* over the top O): E_ads −0.05 eV.
  - C4 (CH₃*(perimeter Rh) + H*(Rh)): ΔE +0.57 eV.
  - C8 (CH₃O* + H*_O): ΔE +0.22 eV.
- **C1 geometry:** the CH₄ sits beside the cluster, 3.45 Å from Ce and 4.55 Å from the nearest Rh. The deck labels it "at the cluster perimeter".
- **D, other states:**
  - D5 (CH₄* over the cluster O) is +0.002 eV above D4.
  - D6 = CH₃• + H*_O, at +0.86 eV. The CH₃ left Ce: C–Ce 3.12 Å, planar (H–C–H angles sum to 359°), 0.44 μB on C. It is labelled CH₃•, not CH₃*(Ce).
- **D7 electronic state:** the C–O bond is 1.42 Å, and Ce³⁺ goes from 2 to 4.
- **Literature match:** the same product (CH₃ on lattice O + OH) is reported by Zuo et al., JACS 138, 13810 (2016), with a reaction energy of −1.23 eV.

### Next steps (in order)

1. **Remaining end states.**
   - C5 (r1, 1522434) and D8 (r1, 1523417) are relaxing.
   - D1r (r1, 1519010) is creeping on a flat surface (210 steps, E₀ −326.7601). It is accepted by the monitor at Fmax ≤ 0.02.
   - D E_ads = E(D4) − E(D1r) − E(CH₄). It goes into the deck (slides 12 and 15) when D1r is accepted.
   - **Check that CH₃ stays on Ce in C5 and D8.** D6 shows that CH₃ can leave Ce. If it leaves, relabel the state as CH₃•.
2. **Ordinary NEB on the new cells.** These are the paths on deck slide 16:
   - A1 → A2;
   - C1 → C3;
   - D5 → D7. D5 is used because its O becomes the methoxy O, and it is only 0.002 eV above D4.
   - B2 → B4. It is on hold by the user (11-02); the previous run 1502824 ended unconverged after 56 steps, with images 03/05 at about +4 eV and wrong moments.

   Protocol: 6 IDPP images, H matched by minimum displacement (`build_neb.py`). Paths with Ce use the two-step job (stage A on the images, then the NEB from the image WAVECARs, `neb_two_step_20261027.sh`).

   **Check the moments of every image after stage A.**
   - For C, every image should have 2 Ce³⁺.
   - For D, the count should go from 2 to 4 along the path, never above 4.
   - Rerun any image that falls into a high-spin solution before the NEB starts. This is the B failure mode.
3. **Path review, then CI-NEB** only for the paths that pass.
4. **D cell check (proposal for the supervisor; not submitted).** In p(2×2) the cluster bonds all four top support O, so no bare support O exists next to the cluster.
   - Run CeO₂(111) p(3×3) 3TL (86 + 5 atoms) for the parent, CH₄* and CH₃O* + H*_O.
   - Purpose: confirm ΔE = −1.50 eV in a larger cell, and add the cluster–support edge O site of the 10-15 plan.
5. **Outside the current scope (no action):**
   - CH₃ → CH₂ (the 10-15 plan and Notion 14: not in this round);
   - comparisons with the p(4×4) values.

### Deck (组会_20261112, 18 slides)

- C and D filled.
- New slide 14: Zuo 2016, as literature for the methoxy result.
- Placeholders left:
  - C5 and D8 boxes;
  - the D E_ads (slides 12 and 15);
  - the NEB barrier column.
- Rebuild with `cfpy build_deck_20261112.py` after updating `E` (set `C5`, `D8`, `D1r`), then re-run `render_3x3_ms.py` (render-venv) after downloading the new CONTCARs to `results/raw_3x3/`.

## 11. NEB rebuild, 2026-11-05 (user: "B 一起重建")

### Why the old B path failed, and what changed

The supervisor's plan (10-15, §3.1) requires a physically possible H transfer, and repairing the endpoints before the NEB.

- **The old B NEB 1502824 (B2 → B4) broke that rule.**
  - In B2, the C–H bond that breaks points away from the acceptor O45 (157°).
  - The H matching (minimum summed displacement) then moved H49 by 4.3 Å.
  - After 56 steps, images 03 and 05 still held a free CH₃ (0.34 μB on C) and a free H (−0.30 μB on H), at +4.0 and +4.5 eV.
- **The same matching gave A1 → A2 an up-pointing H as the breaking one,** so the down-pointing H had to flip through the CH₃ umbrella. The p(4×4) A NEB of 10-26 (1493946) used that matching.
- **`build_neb.match_h` (fixed).** The H that leaves C in the FS now goes to the IS H nearest its FS position. The other three H follow by minimum displacement.
- **The C path needed a new final state.** C1 → C3 is not one elementary step: in C3 the H sits on the top O40, 5.65 Å from the CH₃ Rh33. The adjacent product is H on the interface O38, which is 3.54 Å from Rh33. This is the new FS, C9.

### Endpoints (`build_neb_endpoints_20261105.py`)

All four are relaxed in two stages, with the same INCAR, KPOINTS and cell as each model's other states.

| Set | Role | Start | Job |
|---|---|---|---|
| B5_CH4_toB4 | IS for B4 | CH₄ above the O40–O45 pair; the breaking C–H points at O45 | 1523632 |
| C9_CH3perimRh_HOp | adjacent FS | CH₃ on Rh33 (C3 geometry), H on the interface O38 | 1523633 |
| C10_CH4_toC9 | IS for C9 | C where it sits in the relaxed C1 (4.5 Å above Rh33); the C–H points at O38 | 1523634 |
| D9_CH4_toD7 | IS for D7 | CH₄ above the O40–O38 pair; the C–H points at O38 | 1523635 |

### NEB A

- `neb_3x3/A_neb`, job 1523636, 2 nodes, from scratch (no Ce).
- 6 IDPP images. The down-pointing H37 stretches from 1.10 to 2.53 Å and the CH₃ umbrella stays up.

### When B5, C9, C10 and D9 are accepted

The monitor raises an ATTENTION. Then do the following.

1. **Get the relaxed CONTCARs.** Put each pair into one raw folder; B4 comes from `results/raw/B4_CH3Os_HOs`.
2. **Build the path:**

   ```
   cfpy build_neb.py --pair <M> <IS> <FS> --raw <dir> --out next_steps/neb_3x3 --inputs inputs_3x3
   ```

   The pairs are:
   - B5_CH4_toB4 → B4_CH3Os_HOs;
   - C10_CH4_toC9 → C9_CH3perimRh_HOp;
   - D9_CH4_toD7 → D7_CH3Oc_HOc.

   Check:
   - the build prints the breaking H as the largest mover;
   - every image keeps the other three C–H bonds at about 1.1 Å.
3. **Prepare the run folder on Vanda (`neb_3x3/<M>_neb`):**
   - POTCAR from the IS folder;
   - 00/OUTCAR and 07/OUTCAR = the endpoints' `OUTCAR_stageB_relax`;
   - `neb_profile.py`;
   - `MAGMOM` with 1 on every Ce and 0 elsewhere, in the POSCAR species order, added to the INCAR.
4. **Run stage A first.** Ce paths use the two-step scheme of `neb_two_step_20261027.sh`, with the paths changed to `neb_3x3` and `inputs_3x3`.
   - Run stage A alone first.
   - **Check every image's Ce³⁺ count before the NEB:**
     - B: 4 on every image;
     - C: 2 on every image;
     - D: 2 → 4 along the path, never above 4.
   - **No moment above 0.2 μB on C or H.**
   - Rerun any image that fails, then submit the NEB from the image WAVECARs.
5. **Review, then CI-NEB.** Review each finished ordinary NEB (10-15 §3.1 item 5): continuity, atom motion, spins, highest image. Run CI-NEB only on paths that pass.
6. **Barrier reference.** E_a is quoted from the lowest CH₄* of the model; the IS of the path is within a few meV of it (physisorbed).
   - The diffusion steps C9 → C3 (H on O38 → top O40) and the D/B H placement are separate steps. They are not part of the first-cleavage barrier.

## 12. 2026-11-06 actions

- **B5 was on the wrong spin state.** Stage A from scratch hit NELM, the r1 resume converged to 2 Ce³⁺ (↑00↑), and stage B ran on it at about 1.0 eV above B2. Job 1524516 was deleted. Stage A r2 (1525336) starts from the B4 WAVECAR (4 Ce³⁺; same cell, NBANDS 276) and the original POSCAR.
  The monitor now flags a ch4/ref state whose Ce³⁺ count differs from its parent (B 4, C 2, D 2), both while relaxing and at acceptance (`ce3_mismatch`).
- **D9 found a lower D cluster.** At step 90 (Fmax 0.06) D9 is 0.32 eV below D4 with CH₄ intact, 3.07 Å above the surface. The cluster changed: Ce13–O39 went from 2.27 to 2.02 Å, and O39 moved 0.43 Å.
  - D10_ref_D9cluster (1525338) is the D9 CONTCAR without CH₄, relaxed with the D1r inputs.
  - If D10 is below D1r, D10 is the D parent. The D E_ads and ΔE are then quoted against D10 and D9.
- **D1r** stopped at 400 steps on a flat surface (ZBRENT, E0 −326.7613 eV). It was resumed as r2 (1525337).
- **NEB C** (neb_3x3/C_neb):
  - Path C10 → C9, 6 IDPP images. H45 breaks toward O38 (7° in C10); the other C–H bonds stay at 1.09–1.13 Å.
  - `job_stageA.pbs` (1525352) runs stage A only. `job_neb.pbs` is submitted after the per-image Ce³⁺ check; the monitor raises it when stage A ends.
- **NEB A runs at about 1.1 h per ionic step** (6 images × 12 ranks), so one 72 h job gives about 55 steps. Expect a resume from the image CONTCARs.

### Supervisor, 2026-11-06: intermediate spin states are not checked

The supervisor's instruction (via the user): magnetic-state errors in the middle of a calculation need no attention. Only the final result has to be consistent.

This replaces the following, which I had added myself:
- the stage-A-only gate of section 11, step 4;
- the mid-run Ce³⁺ and magnetic-jump alerts.

What changed:
- NEB C runs `job_neb.pbs` as one job (1525494): stage A on the images, then the NEB.
- The monitor checks the Ce³⁺ count only at acceptance (`ce3_mismatch`).
- When a NEB ends, the monitor reports every image's final Ce³⁺ count and the largest C/H moment.

### 2026-11-06 evening

- **D parent switched to D10.** Accepted energies (eV):

  | State | E₀ |
  |---|---|
  | D10 | −327.05190 |
  | D1r | −326.76395 |
  | D9 | −351.14990 |

  D10 is 0.288 eV below D1r, so the monitor's D 'ref' is now D10 and D1r is a 'sup'.
  - D9 is the lowest CH₄*: E_ads −0.06 eV.
  - D7: ΔE −1.18 eV vs D9 (was −1.50 vs D4).
  - D4 and D5 sit on the higher D1-type cluster: +0.32 eV vs D9.
- **D8:** ZBRENT at step 95 of r1; resumed as r2 (1526948).
- **NEB D** (1526950, neb_3x3/D_neb):
  - Path D9 → D7, 6 IDPP images, `MAGMOM = 14*1 32*0`, stage A + NEB in one job.
  - H45 breaks toward O38 (24° in D9) and the CH₃ goes to O40 (C–O40 3.68 → 1.42 Å).

### 2026-11-07

- **B5 is about to finish on the wrong state.** At step 82 (Fmax 0.051) it is still on 2 Ce³⁺ (↑00↑), at 0.86 eV above B2, so its final state will not match the parent. This is after stage A r2–r4, which started from the B4 WAVECAR.
  - B5b_CH4_toB4_fromB2 (1528686) is B2's relaxed slab (4 Ce³⁺) with the B5 CH₄ (C/H positions from the B5 CONTCAR), with stage A from the B2 WAVECAR.
  - B5 keeps running and is judged at the end.
  - NEB_NEXT B is now B5b → B4.
- **D8:** ZBRENT again at r2 step 46 (E0 −349.4445 eV); resumed as r3 (1528687).
- **NEBs at 10:45:**

  | Path | Steps | Images, E − E(00) (eV) | Total moment |
  |---|---|---|---|
  | A | 41 | +0.01 +0.03 +0.07 +0.18 +0.57 +0.39 | — |
  | C | 36 | −0.01 +0.01 +0.40 +1.14 +1.18 +0.75 | ±2.0 on every image |
  | D | 11 | +0.14 +0.62 +3.61 +1.48 +0.25 −0.87 | 2 2 2 2 4 4 |
