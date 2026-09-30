# 2026-09-30 task — Ce2O3/Ce2O4 cluster vs layer interaction energy

## Supervisor task

1. Build the two supported-cluster models on Rh(111):
   - Ce2O3 cluster/Rh(111)
   - Ce2O4 cluster/Rh(111)

2. Run DFT geometry optimizations under the Stage-2 contract.
   - Keep `ISPIN = 2`.
   - Default: do **not** write a `MAGMOM` line. With `ISPIN = 2`, VASP then uses its default 1 muB/atom initial seed.
   - Write `MAGMOM` only when there is a specific physical/literature basis (for example a known Ce3+ localization pattern or AFM arrangement), and record the source/rationale next to the setting.
   - Existing finished calculations that already contain `MAGMOM` remain unchanged.
   - Check the converged total/local moments and electronic solution for physical reasonableness; SCF convergence alone is not sufficient evidence that the magnetic state is appropriate.
   - Use `IBRION = 2` for ionic relaxation.
   - No additional final static/single-point calculation is required after a properly converged relaxation; use the final converged `E0` consistently, following the current Stage-2 protocol.

3. Calculate the cluster/Rh(111) interaction energy at fixed stoichiometry:

   ```text
   E_int = E[Ce_xO_y/Rh(111)] - E[Ce_xO_y] - E[Rh(111)]
   ```

   For the cluster cases, `E[Ce_xO_y]` is the corresponding isolated Ce2O3 or Ce2O4 cluster reference computed with a compatible method.

4. Directly compare the new cluster interaction energies with the **2026-09-28 Step-3 layer result normalized as `E_int/2`**:
   - Ce:O = 2:3:
     `E_int(Ce2O3 cluster/Rh)` vs `E_int(Ce4O6 layer/Rh) / 2`
   - Ce:O = 2:4:
     `E_int(Ce2O4 cluster/Rh)` vs `E_int(Ce4O8 layer/Rh) / 2`

   The division by 2 is required because the layer cells contain two Ce2O3 or Ce2O4 stoichiometric units, whereas each cluster contains one. The comparison is therefore made on the same Ce2O_y formula-unit basis.

5. Determine which morphology interacts more strongly with Rh(111) at each stoichiometry.
   - Under the definition above, a **more negative `E_int` means stronger interaction/binding**.
   - Do not compare the raw Ce4O6/Ce4O8 layer `E_int` directly with the single-unit cluster `E_int`; use the normalized `E_int/2`.

6. Plot the result.
   - x-axis: Ce2O3 and Ce2O4 stoichiometries.
   - y-axis: `E_int` per Ce2O_y unit (eV).
   - Show cluster and layer side by side for each stoichiometry.
   - State explicitly in the caption that more negative `E_int` corresponds to stronger Rh interaction.

## Scientific role in the project

The mainline SMSI morphology comparison remains **Ce2O3 cluster (amorphous-like) vs Ce2O3 crystalline layer**. The Ce2O4 comparison is a composition-matched control: it tests whether the cluster-vs-layer interaction-energy trend persists at the more oxygen-rich Ce:O = 2:4 stoichiometry; it does not reopen CeO2/Ce2O3 as the primary SMSI-composition question.

## Required output / acceptance checks

Record, for every compared calculation:

- exact structure/case identifier;
- final `E0`;
- convergence status and maximum free-atom force;
- total moment and Ce local moments;
- the exact Rh and free-cluster/free-film reference energies used;
- computed `E_int`;
- normalized layer value `E_int/2`;
- cluster-minus-layer difference on the same Ce2O_y basis;
- final comparison figure.

Do not mix legacy `ISPIN = 1` energies into this comparison. Keep the reference methodology internally consistent before interpreting the cluster/layer difference.
