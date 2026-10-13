# 2026-10-13 | Rh–CeO₂ dynamic SMSI: supervisor directive, scientific audit and next DFT plan

**Status:** source-reviewed / plotting completed / reaction-path DFT **not yet computed** (pathway plan and Phase-1 preview inputs: [../stage6_DRM_CH4_paths_20261013/](../stage6_DRM_CH4_paths_20261013/README.md)).
**Supervisor's scientific intent:** explain the atmosphere-dependent, reversible Ce₂O₃-like overlayer on Rh and test whether a crystalline bilayer improves methane dry reforming (DRM) by lowering elementary-step barriers. Do not promote hypotheses to demonstrated conclusions.

## 1. New directive (2026-10-13)

1. Review and critically test the interpretation of Gangarajula *et al.*, *Applied Catalysis B* **343** (2024) 123503 (https://doi.org/10.1016/j.apcatb.2023.123503).
2. Separate **CH₄:CO₂=1:1 inlet feed** (experiment) from the **CO₂:CO=1:1 redox-buffer assumption** (used as one illustrative chemical-potential reference). Determine where to plot the oxygen chemical potential for **850 °C in CO₂-only gas**.
3. Plot existing cluster/layer **interaction energies**, with matching Ce₂O₃ or Ce₂O₄ formula-unit normalization and known reference structures.
4. Choose justified methane activation/dehydrogenation pathways on **Rh(111)**, **Ce₂O₃-cluster/Rh(111)**, and **Ce₂O₃-layer/Rh(111)**; compare energetics and barriers (later stage). Discuss the scope with Dr. Xiaoyan Li once pathways are selected.

## 2. Evidence and critique: separate observation from interpretation

| Topic | Source-grounded evidence | Scientific limitation / next test |
|---|---|---|
| Literature performance, Fig. 1c–d (not Fig. 2) | After separate 850 °C pretreatments, CO₂-treated Rh/CeO₂ starts at ~90% CH₄ and ~94% CO₂ conversion; H₂- and CH₄-treated catalysts improve during DRM. | Similar later conversion **does not imply an identical atomic surface**. Different conversions also persist; use microscopy/spectroscopy and kinetic rates to compare. |
| Literature Rh/CeO₂ overlayer | Same paper reports Ce-containing encapsulation on **both H₂-850 and CO₂-850**, supported by HRTEM/EELS; CO₂ catalyst's high activity is attributed to mixed Rhδ⁺/Rh⁰ and a permeable layer. | Do **not** generalize the 400 °C H₂ no/weak-SMSI observation to 850 °C H₂. Do not label all encapsulation as inactive. |
| Collaborator operando TEM, 2026-01-22 slide 4–7 | Under high-T CO₂ or CH₄:CO₂=1:1, crystalline bilayer-like SMSI is observed; it becomes less ordered upon cooling and vanishes after switch to CH₄, then reforms in CO₂. Approx. 0.29 nm lattice fringes and Ce-EELS reduction signatures support Ce₂O₃-like material. | A finite cluster is only a **proxy** for amorphous/discontinuous oxide; Ce³⁺ EELS + one fringe do not by themselves establish every atom is stoichiometric Ce₂O₃. Electron-beam and pressure effects require controls. |
| Structure–activity inference | Experimental correlation makes Ce₂O₃ bilayer/Rh a compelling mechanistic **hypothesis**. | It does not establish that layer has lower CH₄ activation barrier; compute barriers on matched active sites, including edge/defect/exposed-Rh controls. |
| CO₂ effect | CO₂ can participate in oxygen-vacancy replenishment and change the restructuring kinetics and electronic state. | A higher oxygen chemical potential generally stabilizes more oxygen-rich stoichiometries; it does **not automatically favor reduced Ce₂O₃ over CeO₂**. The structural explanation remains open. |

Potential methodology reference (verify the precise model and paths before citing in a manuscript): https://doi.org/10.1038/s41467-024-48122-6. Treat as methodological inspiration, not direct evidence for Rh/Ce₂O₃.

## 3. Checkable completed DFT results: Stage 5 (finished 2026-10-08)

Canonical machine-readable artifact:
[stage5_Eint.json](../stage2_interfaces_20260910/results/cluster_layer_Eint_20260930/stage5_Eint.json).
[Stage 5 README](../stage2_interfaces_20260910/results/cluster_layer_Eint_20260930/README.md).
Earlier round-1 numbers are archived separately and are **not** substituted for these new results.

Interaction-energy definition:
`E_int = E(Ce₂Oᵧ/Rh) − E(Ce₂Oᵧ isolated) − E(Rh)` (eV per Ce₂Oᵧ unit).
The layer Ce₄O₆ or Ce₄O₈ has two formula units: **divide its per-cell E_int by 2**.

| Composition | Lowest cluster and E_int (eV/unit) | Other cluster and E_int | Layer E_int per cell | Layer / 2 per unit | Best cluster − layer /2 |
|---|---|---|---|---|---|
| Ce₂O₃ | C3a: **−4.452** | C3b: −3.961 | Ce₄O₆: −3.267 | **−1.634** | **−2.818** |
| Ce₂O₄ | C4a: **−5.145** | C4b: −5.071 | Ce₄O₈: −6.008 | **−3.004** | **−2.141** |

**Observation:** both finite clusters exhibit more negative *fragment-based* Rh interaction energies than their normalized layer controls.
**Not justified:** “clusters are the only equilibrium morphology” or “clusters have greater DRM activity.” Cluster used Rh(111) 4×4; layer used 3×3; coverage, lateral interactions and separate free-cluster/free-film references differ. **The layer's Stage-4 raw total energies and free-film reference dataset should also be archived in this repository** for a fully independent reproduction of layer E_int.

Stage-5 relaxation records (all converged; forces < 0.02 eV/Å): Rh64 reference E0 −439.68688 eV; C3a −478.37273; C3b −477.88210; C4a −485.76487; C4b −485.69049; free Ce₂O₃ −34.234306; free Ce₂O₄ −40.932640; O₂ −9.8782722. ISPIN=2, PBE+U(Ce 4f, Ueff=5 eV), ENCUT=450 eV; reported final relaxation E0, not an extra final-static series. Spin-localization assignment (Ce³⁺ ~1 μB) is indicative, not a fully definitive oxidation-state measurement.

## 4. 850 °C oxygen chemical potential: answer to supervisor question

The **CH₄:CO₂=1:1 feed** is supported by the Applied Catalysis B method section. That is **not** the same quantity as `p_CO2/p_CO`. CO is a DRM **product**, and its partial pressure depends on conversion, flow, local kinetics and sampling position.

When a local equilibrated CO₂/CO oxygen buffer can be used:

```text
CO + O(reservoir) ⇌ CO2
μ_O = μ_CO2 − μ_CO
μ_O(T,p) = μ_CO2°(T) − μ_CO°(T) + k_B T ln(p_CO2/p_CO)
```

Using the exact reference and thermochemical correction stored in Stage-5 `reduction`, at 850 °C (1123.15 K):

```text
Δμ_O (eV/O) = −3.176 + 0.222857 log10(p_CO2/p_CO)
CO2/CO=1       -> Δμ_O=−3.176 eV/O (chosen *reference*, not measured DRM gas)
cluster reduced/oxidised crossover: −2.453 eV/O, log10(CO2/CO)=3.24
layer reduced/oxidised crossover:   −1.771 eV/O, log10(CO2/CO)=6.30
```

**For “850 °C + pure CO₂ feed,” no finite unique Δμ_O vertical line can be determined from feed identity and temperature alone under this CO₂/CO mapping**, because actual `p_CO` is not specified. Formally setting `p_CO=0` makes the logarithm diverge and the reservoir model inapplicable. Plot **a conditional gas-ratio trajectory**, not an invented pure-CO₂ point. To produce a quantitative marker, obtain the in-situ / outlet `p_CO` and `p_CO2` (with caveat that outlet ≠ immediate surface), or declare an explicit CO₂ ⇌ CO + ½O₂ gas-equilibrium model with total pressure / reactor boundary conditions.

An alternative O₂ reservoir is `μ_O=½ μ_O2(T,p_O2)`, but pure CO₂ feed does not fix `p_O2` either. If a carbon reservoir is adopted, that is yet another independently justified assumption.

### Tentative Method B: CO₂-only feed represented by gas dissociation equilibrium (idea for Claude to evaluate; not yet approved or computed)

**Preliminary modeling idea (2026-10-13; subject to Claude's review):** To address the supervisor's question about the **850 °C + CO₂** marker without measured CO partial pressure, *consider* an ideal-gas **CO₂ dissociation equilibrium** as one possible first-pass reservoir model, rather than an adopted physical assumption:

```text
CO2(g) ⇌ CO(g) + 1/2 O2(g)
Kp(T) = [(pCO/p°) (pO2/p°)^(1/2)] / (pCO2/p°)
Kp(T) = exp[-ΔrG°(T)/(R T)]
μO(eq) = μCO2 − μCO = 1/2 μO2
```

**Practical 850 °C implementation:** set `T=1123.15 K`; specify **measured total gas pressure** `P` (and initial CO₂/He composition if the microscope gas cell uses a carrier). For a simple 1 mol *pure CO₂* starting state, define equilibrium dissociation extent `ξ`: `nCO2=1−ξ`, `nCO=ξ`, `nO2=ξ/2`, `ntot=1+ξ/2`; use `p_i=P n_i/ntot`, solve the dimensionless `Kp` equation, and calculate `μO` with gas thermochemistry from the same reference convention as the existing Stage-5 `ΔμO` plot. For inert dilution, include `nHe` in `ntot`. Document the source of `ΔrG°(1123.15 K)` (e.g. NIST-JANAF), standard pressure and reference zero.

**If Claude finds the model defensible:** plot a conditional vertical line titled **“850 °C + CO₂: ideal-gas dissociation-equilibrium estimate (assumed P and feed)”**; if P/He fraction are not yet confirmed, plot a parametric/sensitivity range rather than an unqualified fixed number. Keep the old **CO₂/CO = 1:1, ΔμO = −3.176 eV** point as a separate *illustrative reference*, not an experimental identification. Compare both results to the Stage-5 fixed-morphology boundaries (cluster −2.453 eV, layer −1.771 eV).

**Interpretation:** this calculation estimates a **gas-equilibrium limit**; it does not assert that the actual flowing, heated, illuminated catalytic gas cell reaches full CO₂ dissociation equilibrium, nor that the model captures the local oxygen reservoir exactly. Use the experimental conditions and, when available, measured outlet or local gas composition to cross-check. **Status: tentative hypothesis for further deliberation by Claude; NOT an approved final model, a calculated pure-CO₂ μO value, or a completed DFT run.**

**Claude evaluation (2026-10-13, computed):** the ideal-gas CO₂ ⇌ CO + ½O₂ equilibrium was evaluated with NIST-JANAF data in the Stage-5 reference convention ([muO_CO2_equilibrium.py](muO_CO2_equilibrium.py), [json](muO_CO2_equilibrium.json), [Fig_muO_850C_CO2_equilibrium.svg](Fig_muO_850C_CO2_equilibrium.svg)). K_p(1123 K) = 2.5×10⁻⁹. Pure CO₂ at 1 bar gives Δμ_O = −1.92 eV/O (log₁₀ pCO₂/pCO = 5.63); over P = 10⁻⁴–1 bar and 10–100 % CO₂ in He the range is −2.29 to −1.92 eV/O. Every case lies between the cluster (−2.45) and layer (−1.77) reduction boundaries, i.e. in the region where the Ce₄O₆ (Ce₂O₃) layer is favoured over Ce₄O₈, consistent with the supervisor's high-T CO₂ → Ce₂O₃ layer result. Crossing the layer boundary at 1 bar would need ≥ 24 ppm O₂ in the feed; CO impurity only lowers Δμ_O. Recommended plot: the band plus the 1-bar point, labelled as a gas-equilibrium estimate; the CO₂/CO = 1 point (−3.18 eV) stays as an illustrative reference. JANAF reproduces the Stage-5 CO₂/CO = 1 value to 0.003 eV (−3.173 vs −3.176).

**Claude review request (brainstorm rather than execute blindly):** Evaluate whether CO₂ ⇌ CO + ½O₂ ideal-gas equilibrium is physically defensible for the supervisor's real 850 °C pretreatment conditions (flowing CO₂, possible He carrier, pressure). Check the experimental pressure and flow against original records; re-derive Kp, unit conventions, DFT oxygen reference and sensitivity to pressure. Compare this approach with measured CO₂/CO and an alternative O₂-reservoir mapping; recommend the most practical, well-labeled estimate or range for the supervisor's requested plot. Treat the equilibrium calculation as an *initial suggestion*, not an established result; preserve the supervisor's scientific direction.\n\nThresholds are **within a fixed morphology** (Ce₂O₃ vs Ce₂O₄ cluster, Ce₄O₆ vs Ce₄O₈ layer), **not a cluster-vs-layer stability crossing**. Stage-5 boundaries −2.453 and −1.771 eV must not be confused with old round-1 layer 20a-vs-30a −0.951 eV (different geometries, references and calculation stages). The ~850 °C grand-potential mapping neglects several condensed-phase thermal terms (vibrations/configurational entropy) and is therefore a first approximation.

Legacy ready-made figures, already on GitHub: [Fig_cluster_vs_layer_Eint.png](../stage2_interfaces_20260910/results/cluster_layer_Eint_20260930/Fig_cluster_vs_layer_Eint.png) and [Fig_dG_cluster_vs_layer.png](../stage2_interfaces_20260910/results/cluster_layer_Eint_20260930/Fig_dG_cluster_vs_layer.png).

## 5. Reaction-path workflow: priority and acceptance criteria

**Model set**: (A) clean Rh(111); (B) C3a Ce₂O₃ cluster / Rh(111); (C) 30a-like crystalline Ce₄O₆ layer / Rh(111), updated under the matched 450 eV and spin-polarized protocol; optionally test the physically exposed **edge / vacancy / Rh-accessible** interface. If the full film entirely buries Rh, it cannot by itself represent a permeable/partially exposed Rh site.

**First phase (thermochemistry)**: for each structure, relax CH₄ weak adsorption at plausible Rh top, Rh–O–Ce perimeter, and Ce/O sites as applicable. Enumerate coadsorbed CH₃*+H* and CH₂*+2H* minima, with sensible alternative C/H adsorption registries, fixed slab constraints, same stoichiometry and compatible reference energies. Compute adsorption energies and step reaction energies with consistent sign and reference convention.

**Second phase (kinetics)**: validated CI-NEB / dimer on the lowest viable paths:
1. `CH4* → CH3* + H*`
2. `CH3* + H* → CH2* + 2H*`
3. Optional if surface oxygen is accessible: `CH2* + O* → CH2O*`, and `CO2* + V_O → CO* + O_lattice` for catalyst regeneration/coking resistance.

For each reported barrier provide endpoints, 5–7 NEB image convergence as appropriate, energies relative to initial adsorbed complex, saddle verification (one imaginary frequency if feasible), competing geometries / spin states, clean vs supported benchmark, and evidence traceability. At 850 °C, DFT electronic barriers alone do **not** equal kinetic performance; consider entropy, coverage and surface-site accessibility before making macroscopic conversion claims.

**Calculation contract**: preserve project README's slab z=0 and ≥15 Å upper vacuum; ISPIN=2, Ce DFT+U=5 eV, ENCUT=450 eV for *new* runs; same numerical settings and physically comparable surfaces. Do not splice older 400 eV / different slabs into a new reaction-energy diagram.

## 6. Next discussion with supervisor

1. Confirm whether the original **CO₂:CO=1:1** annotation was intended as *an assumed redox-buffer baseline*, not experimental 1:1 feed. Request measured CO₂, CO (and optionally O₂) partial pressures at 850 °C under CO₂-only flow, or approval for a labeled equilibrium-model scenario.
2. Ask whether the decisive test should focus on **first C–H cleavage / CH₃ dehydrogenation**, before a complete DRM network; request agreement on the three active-site models and an accessible Rh/Ce₂O₃ perimeter model.
3. Compare cluster/film on a common Rh lateral cell or run size/coverage convergence, then compute a **matched-composition grand potential** using consistent bulk/atom reservoirs and actual Ce inventory. E_int/2 alone is insufficient.
4. Confirm experimentally how the Ce³⁺-rich layer identity, bilayer thickness, and permeability were determined; H₂ temperature must be specified.
5. Archive Stage-4 layer reference energies and figures with the numerical scripts (important reproducibility gap).

**Proposed short interpretation:** The experiment establishes atmosphere-reversible, Ce³⁺-rich crystalline SMSI on Rh in CO₂-containing environments. Current DFT favors discrete clusters in *interaction strength* but has not proved either morphology's overall operating stability or catalytic barrier advantage. Gas conditions should be mapped via measured CO₂/CO (or declared equilibrium assumptions), and reaction-path comparisons should test rather than presume the crystalline bilayer's superiority.

## Provenance

- User-provided supervisor notes dated 2026-10-13 and operando TEM/EELS presentation *2026.01.22 Rh–CeO₂ SMSI*.
- Paper: Gangarajula *et al.* Applied Catalysis B 343 (2024) 123503; Fig. 1c–d, Fig. 5–6, methods.
- Stage-5 `stage5_Eint.json` and `stage5_Eint.md`, labeled finished 2026-10-08.
- Old `results/RESULTS_round1.md` is historical only; avoid mixing round 1 / Stage 4 / Stage 5 reference cells.
