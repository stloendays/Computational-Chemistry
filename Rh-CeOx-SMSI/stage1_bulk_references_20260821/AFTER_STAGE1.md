# After Stage 1

Do **not** build the Rh/Ce2O3 interface from the unrelaxed starting cells in this zip.

First accept Stage-1 results:

1. Rh bulk must have a stable optimized cell and a completed ionic relaxation.
2. Compare the two Ce2O3 runs at the same calculation settings.
3. Inspect whether Ce local moments remain physically meaningful rather than collapsing to a pathological electronic state.
4. Use the accepted optimized Rh lattice constant to construct the Rh(111) substrate.
5. Use the accepted Ce2O3 cell as the crystalline reference for later Ce2O3(0001), layer/Rh, and cluster/Rh models.

The next personal-project package should keep one fixed Rh slab contract and use multiple starting registries for Ce2O3 layer/cluster, because a single local minimum is not sufficient for the teacher's stability comparison.
