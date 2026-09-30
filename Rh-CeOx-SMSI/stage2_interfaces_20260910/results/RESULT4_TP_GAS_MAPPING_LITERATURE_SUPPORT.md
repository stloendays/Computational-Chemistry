# Result 4 — literature support for mapping ΔμO to temperature and gas pressure

## Scope

This note supports the thermodynamic mapping used in the slide:

> **Result 4: ΔμO* = −1.77 eV in terms of T and gas pressure**

The important distinction is:

- **ΔμO* = −1.77 eV is a result from this project, not a literature value.**
- Literature supports the **ab initio thermodynamics formalism**, the use of **O2 and CO2/CO as oxygen reservoirs**, and the **gas-phase thermochemical data** used to convert a calculated oxygen chemical-potential boundary into (T,p) space.
- The pressure thresholds shown on the slide (e.g. (p(O_2)) and (p(CO_2)/p(CO)) at 800–850 °C) are therefore **derived values of this work** and should not be presented as numbers taken from a paper.

## Thermodynamic basis

### 1. O2 reservoir

For an ideal-gas oxygen reservoir,

[
mu_O(T,p_{O_2})=rac{1}{2}mu_{O_2}(T,p_{O_2})
]

and

[
mu_{O_2}(T,p)=mu_{O_2}^{circ}(T)+k_BTlnleft(rac{p}{p^{circ}}ight).
]

Using the DFT O2 energy as the zero-temperature reference, the oxygen chemical-potential correction can be written schematically as

[
Deltamu_O(T,p_{O_2})
=
rac{1}{2}
left[
Deltamu_{O_2}^{circ}(T)
+
k_BTlnleft(rac{p_{O_2}}{p^{circ}}ight)
ight].
]

This is the standard **ab initio atomistic thermodynamics** route for converting a DFT phase boundary in (Deltamu_O) into a temperature/pressure phase boundary.

For the current slide, the phase boundary is imposed by

[
Deltamu_O(T,p_{O_2})=Deltamu_O^*=-1.77 {m eV}.
]

The lower-(mu_O) side is the more reducing side, hence the slide labels Ce4O6/Rh as stable below the corresponding (p(O_2)) boundary.

### 2. CO2/CO reservoir

For the redox equilibrium

[
CO + O ightleftharpoons CO_2,
]

the effective oxygen chemical potential is

[
mu_O=mu_{CO_2}-mu_{CO}.
]

For ideal gases,

[
mu_O(T,p_{CO_2},p_{CO})
=
left[mu_{CO_2}^{circ}(T)-mu_{CO}^{circ}(T)ight]
+
k_BTlnleft(rac{p_{CO_2}}{p_{CO}}ight).
]

Therefore the same calculated boundary (Deltamu_O^*) can be mapped onto a critical (p(CO_2)/p(CO)) ratio. A smaller CO2/CO ratio corresponds to a more reducing oxygen chemical potential and therefore favors the reduced Ce4O6/Rh side of the diagram.

## Direct literature support

### A. General first-principles thermodynamics: DFT → (T,p) phase diagrams

**Reuter, K.; Scheffler, M.**  
“First-Principles Atomistic Thermodynamics for Oxidation Catalysis: Surface Phase Diagrams and Catalytically Interesting Regions.”  
*Physical Review Letters* **90**, 046103 (2003).  
DOI: https://doi.org/10.1103/PhysRevLett.90.046103

Why it supports this figure:
- establishes the standard first-principles atomistic-thermodynamics framework;
- explicitly constructs surface phase diagrams from DFT energetics as a function of temperature and gas pressure;
- supports the conversion of a calculated oxygen chemical potential into an experimentally interpretable (T,p_{O_2}) boundary.

### B. Ceria-specific precedent using both O2 and CO/CO2 reservoirs

**Botu, V.; Ramprasad, R.; Mhadeshwar, A. B.**  
“Ceria in an oxygen environment: Surface phase equilibria and its descriptors.”  
*Surface Science* **619**, 49–58 (2014).  
DOI: https://doi.org/10.1016/j.susc.2013.09.019

Why it is especially relevant:
- develops a first-principles thermodynamic phase diagram specifically for **ceria (111)**;
- treats ceria in a **pure O2 reservoir** and in **CO/CO2 redox environments**;
- demonstrates that the oxygen chemical potential set by the gas environment controls ceria reduction / oxygen-vacancy stability.

This is the closest literature precedent for the logic of the two panels in Result 4.

### C. Explicit use of effective oxygen chemical potential under COx reaction conditions

**Müller, A.; Comas-Vives, A.; Copéret, C.**  
“Ga and Zn increase the oxygen affinity of Cu-based catalysts for the COx hydrogenation according to ab initio atomistic thermodynamics.”  
*Chemical Science* **13**, 13442–13458 (2022).  
DOI: https://doi.org/10.1039/D2SC03107H

Why it supports the right-hand panel:
- explicitly analyzes oxygen chemical potential under CO/CO2-containing reaction environments;
- relates gas composition to (mu_O) and to an equivalent oxygen partial pressure;
- provides a modern catalysis example of using gas composition rather than only (p(O_2)) to describe the redox thermodynamic environment.

### D. Gas-phase thermochemical data used for the conversion

**Chase, M. W., Jr.**  
*NIST-JANAF Thermochemical Tables, Fourth Edition.*  
*Journal of Physical and Chemical Reference Data*, Monograph 9 (1998).

NIST Chemistry WebBook, SRD 69:
- O2: https://webbook.nist.gov/cgi/cbook.cgi?ID=C7782447&Mask=1
- CO: https://webbook.nist.gov/cgi/cbook.cgi?ID=C630080&Mask=1
- CO2: https://webbook.nist.gov/cgi/cbook.cgi?ID=C124389&Mask=1

Why it supports the numerical mapping:
- supplies (H^circ(T)), (S^circ(T)), and heat-capacity / Shomate representations for O2, CO, and CO2;
- these functions provide the finite-temperature standard chemical potentials entering the equations above.

### E. Ceria-interface restructuring controlled by oxygen chemical potential

**Chen, H.; Li, R.; Lv, Z.; et al.**  
“Local Oxygen Chemical Potential Determines Cobalt-Ceria Interfacial Catalysis in CO2 Hydrogenation.”  
*Angewandte Chemie International Edition* **65**, e23112 (2026).  
DOI: https://doi.org/10.1002/anie.202523112

Why it is useful context:
- experimentally and thermodynamically connects gas environment → local oxygen chemical potential → restructuring of a metal–ceria interface;
- supports the broader interpretation that ceria-containing metal/oxide interfaces can dynamically respond to the redox environment.

This paper is conceptual support, not the source of the numerical Rh/CeOx boundary.

## Claim-to-reference map for the slide

| Slide claim / operation | Support |
|---|---|
| Convert a DFT (Deltamu_O) boundary into (T,p) space | Reuter & Scheffler, PRL 2003 |
| Use (p(O_2)) as an oxygen reservoir for ceria reduction | Reuter & Scheffler 2003; Botu et al. 2014 |
| Use CO2/CO ratio as an effective oxygen reservoir | Botu et al. 2014; Müller et al. 2022 |
| Obtain (H^circ(T), S^circ(T)) for O2 / CO / CO2 | NIST-JANAF / NIST Chemistry WebBook |
| Interpret atmosphere-dependent restructuring of a ceria interface through (mu_O) | Chen et al. 2026 |
| (Deltamu_O^*=-1.77) eV and the exact 800/850 °C pressure thresholds | **This work — must be traceable to the calculation artifact that produced the crossover** |

## Provenance warning that must be resolved before manuscript use

At the time this note was added, the repository file
`results/RESULTS_round1.md` still reports an older round-1 Ce4O8(20a) / Ce4O6(30a) layer crossover of

[
Deltamu_O=-0.95 {m eV},
]

whereas the current slide states

[
Deltamu_O^*=-1.77 {m eV}.
]

Therefore **do not replace the canonical repository boundary with −1.77 eV solely from the slide image**. The newer value should first be tied to its exact energy set, formula, script/output, and commit. Once that provenance is identified, regenerate the 800 °C and 850 °C (p(O_2)) and (p(CO_2)/p(CO)) thresholds from the same thermodynamic convention and store the calculation artifact next to this note.

## Recommended slide citation line

A compact citation line for the slide can be:

> **Thermodynamic mapping:** Reuter & Scheffler, *Phys. Rev. Lett.* 2003, 90, 046103; Botu *et al.*, *Surf. Sci.* 2014, 619, 49–58; gas thermochemistry from NIST-JANAF (Chase, 1998).

For the CO2/CO panel, add:

> Müller *et al.*, *Chem. Sci.* 2022, 13, 13442–13458.

