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
