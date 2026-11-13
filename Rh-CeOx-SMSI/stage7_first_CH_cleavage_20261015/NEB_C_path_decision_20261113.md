# 2026-11-13 | Model C path selection and layer-vs-cluster interpretation

## Decision

**Keep the current Model C first-cleavage path C10 → C9. Do not launch C1 → C3 as a replacement NEB for the same elementary step.**

This is a reaction-definition decision, not a choice made to obtain a more favourable reaction energy.

## Why C10 → C9 is the appropriate first-cleavage path

The 3×3 endpoint construction records that C1 → C3 is not a single local first C–H-cleavage event:

- In C3, CH3 remains on perimeter Rh33, but H is placed on the remote top O40, about 5.65 Å from the CH3/Rh33 site.
- The adjacent interfacial acceptor is O38, about 3.54 Å from Rh33. The immediate product with H on O38 is C9.
- C10 was built with the CH4 C–H bond directed toward O38 (about 7°), and C10 → C9 therefore represents the local event: C–H cleavage, H transfer to adjacent interfacial O38, and CH3 remaining on perimeter Rh33.
- The subsequent H migration from O38 to top O40 (C9 → C3) is a separate structural/reaction step. It is outside the current first-C–H-cleavage scope.

Thus, the current 3×3 values ΔE(C10 → C9) = +0.56 eV and ΔE(C1 → C3) = −0.12 eV refer to different product arrangements. The exothermicity of C1 → C3 includes stabilization associated with the remote H-on-O40 product and must not be used as a substitute for the first-cleavage reaction energy or barrier.

C10 is reported to lie about 0.05 eV above the lowest CH4* state C1. When comparing the C10-referenced barrier with a barrier referenced to the lowest adsorbed state (e.g. Model A), include or explicitly discuss this small pre-orientation penalty; do not silently mix initial-state references.

## Current NEB status and quality gate

The latest status reported on 2026-11-13 for C10 → C9 is: 111 ionic steps with little further energy change; several intermediate images are reported at +1.7 to +2.6 eV relative to the initial image, image 04 at +0.89 eV, and the endpoint/image electronic states are not yet consistent.

These values are **not a validated activation barrier**. Before reporting any barrier:
1. Check the endpoint and final-image electronic states (including the expected two Ce3+ in Model C and absence of spurious C/H radical moments).
2. Check the image-by-image geometry, C–H/O–H transfer, atom mapping, energy continuity and maximum forces.
3. Continue or rebuild the C10 → C9 band only if needed to repair the path; retain the same chemically local endpoint definition.
4. Proceed to CI-NEB only after the ordinary NEB passes the existing path-review gate.

C1 → C3 may be considered later as a separate O38 → O40 H-migration step if that chemistry becomes part of the approved scope. It is not a replacement first-cleavage path.

## How this fits the layer-vs-cluster research question

The intended conclusion is that a Ce2O3-like crystalline overlayer is the experimentally relevant and thermodynamically favoured morphology under CO2-containing high-temperature conditions, and that this structure contributes to the observed catalytic behaviour. The evidence must be kept in distinct categories:

- **Experiment:** the gas-cell observations report a crystalline bilayer-like SMSI overlayer under 850 °C CO2 and 850 °C CH4:CO2 = 1:1, while switching to pure CH4 weakens/removes the crystalline layer; EELS assigns the particle overlayer as Ce2O3-like. This supports an atmosphere-dependent layer state under CO2-containing conditions.
- **Thermodynamic structure comparison:** the existing oxygen-chemical-potential analysis places the Ce2O3-like layer below the discrete Ce2O3 cluster under the illustrative 850 °C pure-CO2 condition (ΔμO ≈ −1.92 eV/O; reported relative ΔG values are −0.07 eV/Ce for Ce4O6 layer and +1.10 eV/Ce for Ce2O3 cluster). This supports layer stability within the current model set and stated gas-equilibrium assumptions.
- **Different metric, different question:** the earlier matched-composition Rh–CeOx interaction-energy comparison gave a more negative interaction energy for the cluster than for the normalized layer. That measures fragment–Rh interaction on its chosen reference, not the same quantity as the atmosphere-dependent formation free energy. Do not conflate the two or claim that every metric favours the layer.
- **Kinetics:** the first-cleavage barriers for A (bare Rh), B (layer) and C (cluster) are still separate tests. The Model C comparison must use the physically local C10 → C9 event, not the more exothermic but non-equivalent C1 → C3 endpoint pair. The current C NEB is not converged/validated, so no kinetic conclusion can yet be drawn from its image energies.

## Important model limitation

Model B currently uses the Stage-4 L6 Ce4O6/Rh(111) structure, which has one Ce atomic plane and fully covers the Rh surface. It is a computational layer proxy, not an atomistically exact representation of the experimentally observed crystalline bilayer. The weak CH4 adsorption and the B endpoint chemistry must therefore be discussed with this model limitation in view. Do not silently claim that L6 is the experimentally resolved two-Ce-plane overlayer.

For the kinetic comparison, state the actual product motif for each model. Model C gives CH3* on perimeter Rh plus OH* on interfacial O38; the current B route involves CH3O* + OH*. These are model-specific pathways and should not be described as identical product states. Compare barriers only after each path is validated, with consistent energy references and explicit mechanism labels.

## Working interpretation and next actions

1. Keep C10 → C9 as the Model C first-cleavage path; do not submit C1 → C3 NEB now.
2. Resolve the C10 → C9 convergence/electronic-state problem before extracting a barrier.
3. Finish and validate the corresponding Model B layer path and Model A reference; report ordinary-NEB estimates separately from CI-NEB-refined barriers.
4. Compare structural stability, reaction energy ΔE and activation energy Ea as three different quantities.
5. If the layer is experimentally/thermodynamically favoured but its current ideal full-coverage L6 model does not show a lower intrinsic CH4-cleavage barrier, do not force the result. Discuss possible accessible edges, defects or a permeable overlayer as hypotheses for later testing, subject to the supervisor-approved scope. No new Ce8O12 full-bilayer NEB is initiated by this note.

**Bottom line:** the current evidence supports the Ce2O3-like layer as the relevant/favoured structure under CO2-containing conditions. Whether it also has a lower intrinsic first C–H-cleavage barrier than the cluster is an open kinetic question. A fair comparison requires the physically local C10 → C9 cluster path and a validated layer path—not a cherry-picked exothermic endpoint pair.
