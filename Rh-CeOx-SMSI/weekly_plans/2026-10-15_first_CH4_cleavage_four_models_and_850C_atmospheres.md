# 2026-10-15 | Supervisor-updated plan: first CH₄ C–H cleavage on FOUR structures + dual 850 °C SMSI markers

**Decision source:** User relayed the supervisor's latest instruction on 2026-10-15, together with an experimental-summary slide. This plan **supersedes** the older three-model / CH₄→CH₃→CH₂ / full-DRM suggestions for the **current round**. These are **to-do calculations**, NOT newly completed VASP results. Suggested week: 2026-10-15 to 2026-10-18 (SGT).

## 1. Experiment constraints to use in the slides and plot

| Experimental treatment | Observation reported by collaborator | Modeling relevance |
|---|---|---|
| 400 °C + H₂ | No SMSI or very few CeOₓ clusters on Rh | Supporting contrast; do **not** extrapolate to 850 °C H₂ |
| **850 °C + CO₂** | **Crystalline bilayer SMSI layer** | **Plot marker #1** |
| **850 °C + CH₄:CO₂ = 1:1 reaction feed** | **Crystalline bilayer SMSI layer** | **Plot marker #2** |
| 850 °C + CH₄ | No SMSI or very few CeOₓ clusters on Rh | Supporting contrast; not one of the two requested plot markers |
| Composition evidence | EELS identifies the SMSI overlayer as Ce₂O₃-like | Use Ce₂O₃-based layer/cluster models as working hypotheses |

These temperatures and both 850 °C plot markers follow the supervisor's new summary and supersede the earlier 800 °C suggestion. Preserve the distinction between experimental assignment and literal resolved layer atomic stacking.

## 2. FOUR systems (all included in the first-CH₄-cleavage work package)

| ID | Calculation model | Starting point | Active sites / end-state ideas | Status |
|---|---|---|---|---|
| **A** | **clean Rh(111)** | Stage-5 R4, Rh(111) p(4×4) | Accessible Rh top/hollow; CH₄* → CH₃*(Rh) + H*(Rh) | Parent structure available; NEW cleavage run pending |
| **B** | **crystalline Ce₂O₃ layer/Rh(111)** | Stage-4 L6 Ce₄O₆/Rh(111), Rh p(3×3) | Accessible layer Ce/O; CH₃* + OH*(lattice O) or other stable split state | Parent structure available; NEW cleavage run pending |
| **C** | **Ce₂O₃ cluster/Rh(111)** | Stage-5 lowest C3a, Rh p(4×4) | Rh–O–Ce perimeter / exposed Rh; try CH₃*(Rh) + H*(Rh) and CH₃*(Rh) + OH*(cluster O) | Parent structure available; NEW cleavage run pending |
| **D** | **Ce₂O₃ / CeOₓ cluster on a CeO₂ support** | Use the established CeO₂(111) slab benchmark where suitable; place finite Ce₂O₃ cluster on CeO₂ | Cluster–support edge and accessible Ce/O; optimize CH₃* + OH* (and plausible alternatives) | **NEW supported-cluster model to build and optimize** |

**Structure-definition caution:** the request unambiguously adds *cluster on CeO₂*, but the exact CeOₓ stoichiometry, surface orientation and cluster registry on CeO₂ should be confirmed during modeling. Ce₂O₃ on CeO₂(111) is the consistent **first candidate**, not a supervisor-confirmed unique geometry. Do not silently replace this with **Rh cluster/CeO₂** or assume it has an exposed Rh metal site. The existing L6 layer has **one Ce plane (O–Ce–O)**; it is a computational proxy for the experimentally imaged *bilayer-like* SMSI, **not an atomistically proven 2-ML Ce₂O₃ reconstruction**. Existing 30a/30d remain archived structural controls. No new Ce₈O₁₂ full-path NEB is authorized.

## 3. This round calculates **ONLY THE FIRST C–H CLEAVAGE**

**One reaction per model:** CH₄* → CH₃* + H* for available metal sites, or CH₄* → CH₃* + OH* when a lattice/cluster O abstracts H (all structures kept atom balanced).

1. Reuse / revalidate four clean parents (A–C: verify existing CONTCAR and settings; D: newly optimize Ce₂O₃ cluster/CeO₂ and a clean CeO₂ control).
2. Generate several physically accessible CH₄ adsorption starts; relax CH₄* (IS) and dissociated CH₃* + H*/OH* (FS), without forcing a reaction at inaccessible buried Rh sites. Screen alternatives with **matched model-specific energy references**.
3. Report first-step reaction energy `ΔE = E(FS) − E(IS)` and CH₄ adsorption energy `E_ads = E(CH₄*) − E(clean parent) − E(CH₄,g)`.
4. After stable, composition-matched endpoints exist, run **one best-first-path CI-NEB per model** (up to 4 initial paths; extra only if end-state ranking demands); report `E_a = E(TS) − E(IS)`; verify the saddle by its unstable mode and ideally one imaginary frequency.
5. Compare the **first-cleavage** barriers and accessible sites across A–D. The fourth model answers whether oxide-supported CeOₓ clusters have a different CH₄-activation mechanism than clusters on Rh. Do **not** compare bare raw TOTEN across different supercells/compositions.

**Excluded from this week's authorized scope:** CH₃→CH₂, complete CH₄→C, CO₂ dissociation, CHₓ oxidation, MvK closed cycle, a new large bilayer NEB campaign, microkinetics. The older Stage-6 files exploring these steps stay archived as *future candidates*, not active tasks.

### Calculation quality rules

- Reuse project-wide **PBE+U(Ce 4f, Ueff=5 eV), ISPIN=2, ENCUT=450 eV**; metal slab relax ISMEAR=1 SIGMA=0.10 eV, final comparison ISMEAR=0 SIGMA=0.05 eV, consistent k sampling / spin treatment.
- Clean parent, IS and FS within each model must use same cell, constraints, electronic settings and suitable bottom-fixed layers. Maintain project slab `z_bottom=0 Å`, `vacuum_above ≥15 Å` for new inputs, and verify the oxygen/substrate termination.
- Assess Ce³⁺ site magnetic moments and obvious geometry artifacts; record charge / spin and atom conservation. If no stable CH₄* minimum exists, explicitly record the limit and consider a gas-phase-to-dissociated reaction path rather than inventing an adsorption state.
- C3a vs L6 have different p(4×4)/p(3×3) Rh cells; compare *reaction energies / activation barriers* with appropriately defined local endpoints and discuss coverage, not raw whole-cell totals.
- Keep code, POSCAR/CONTCAR, input parameters, final-state images, NEB profiles, forces and convergence log traceable. Never commit licensed POTCAR, WAVECAR/CHGCAR or bulk binary files.

## 4. Figure update (same figure; TWO 850 °C conditions)

Deliverable: update the existing **Ce₂O₃ layer-vs-cluster stability plot** (ΔG per Ce vs Δμ_O) to put **both experimental atmospheres in a single panel**:
- **850 °C + CO₂** (CO₂-treated SMSI bilayer; if using the previously computed *1 bar ideal-gas dissociation-equilibrium estimate*, the illustrative value is Δμ_O ≈ −1.92 eV/O; label the assumption in the caption).
- **850 °C + CH₄:CO₂ = 1:1** (DRM feed; bilayer). `CH₄:CO₂=1:1` is a *feed ratio*, **not** `CO₂:CO=1:1`. Choose and disclose a *working* CO₂/CO ratio, or show a clearly labeled illustrative marker/range until outlet composition is known. As one transparent **example only**, assuming `pCO₂/pCO = 1` on the existing 850 °C oxygen-buffer convention gives Δμ_O ≈ −3.176 eV/O. **Do not portray this assumed ratio as measured experimental gas composition.**
- Both markers must be named in the legend/caption; retain existing same-reference layer/cluster curves and identify the Ce₂O₃ layer lowest-energy region without changing results to force agreement.
- Use the existing plot/artifacts in `analysis_20261013/` and `stage2_interfaces_20260910/results/cluster_layer_Eint_20260930/` as the starting materials; save updated plot (PNG/SVG), source script and model assumptions in the same research project.

Scientific distinction: the two 850 °C marker comparison is primarily **Ce₂O₃ layer vs CeOₓ cluster on Rh**; the new **Ce₂O₃ cluster on CeO₂** has a different support and should **not** be overplotted using Rh-normalized energies without a new common Ce/oxygen reservoir and consistent support-area accounting.

## 5. This-week task checklist (SGT; suggested, not claimed complete)

### Thu 15 Oct — freeze the first-step scope and figure input
- [ ] Register A–D parents and provenance; confirm D = Ce₂O₃ cluster/CeO₂ with CeO₂(111) as first support candidate.
- [ ] Audit existing A/B/C CONTCAR, adsorption seeds and `Stage 6` scripts; remove second-dehydrogenation jobs from the **active queue plan**, leave archived files untouched.
- [ ] Start the two-marker figure draft at **850 °C** with clearly labeled assumptions.

### Fri 16 Oct — finish geometry generation / screening inputs
- [ ] Build/relax D support+cluster and clean-support reference; begin geometric screening of the cluster site.
- [ ] Prepare / submit initial CH₄* and CH₃*+H*/OH* candidate optimizations for A–D, keeping one folder + manifest per parent.

### Sat 17 Oct — screen endpoints, start first-step kinetics
- [ ] Review relaxed IS/FS energies, Fmax, moment and atom balance; reject physically implausible forced states.
- [ ] Start the lowest viable CH₄ first-cleavage CI-NEB on A/B/C and D when its reference is ready; resource-constrained runs may carry into next week.

### Sun 18 Oct — report and handoff
- [ ] Submit one overlay plot with BOTH 850 °C experimental annotations, source data and caption.
- [ ] Report A–D structure gallery, status table, ΔE and available E_a, convergence and missing work. A pending NEB must be called **running/queued**, not **finished**.
- [ ] Note potential next-stage CH₃→CH₂/CO₂/O-vacancy branches under a **deferred** heading only; do not launch without next supervisor instruction.

## 6. Acceptance criteria

- [ ] **Four** chemically identified parent structures with provenance; D actually built, not merely relabeled.
- [ ] First-cleavage IS/FS attempted on **all four** structures; converged if feasible, with missing/unstable sites clearly recorded.
- [ ] Four first-step CI-NEB pathways attempted once viable endpoints exist; completed barriers only for truly converged paths.
- [ ] **One** properly captioned Ce₂O₃ layer/cluster stability figure containing the **two 850 °C gas conditions**.
- [ ] A concise comparison of what is an experimental observation, a DFT result, and a hypothesis.

## Sources and earlier work

- 2026-10-15 user-supplied experimental-summary slide; partner gas-cell in-situ microscopy presentation **2026.01.22 Rh–CeO₂ SMSI**.
- [Previous Stage-6 pathway README](../stage6_DRM_CH4_paths_20261013/README.md) — now superseded for this round by first cleavage + four structures.
- [2026-10-13 DFT/supervisor audit](../analysis_20261013/2026-10-13_supervisor_review_and_calculation_plan.md).
- [Stage-5 Ce₂O₃ cluster/Rh data](../stage2_interfaces_20260910/results/cluster_layer_Eint_20260930/README.md).
