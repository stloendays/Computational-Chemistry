# Dynamic SMSI personal project — Stage 1

This package is the first **personal-project** calculation set, not another paper-reproduction set.

## Why these jobs come first
The formal Dynamic SMSI task is to compare Ce2O3 layer / Ce2O3 cluster / CeO2 species on the same Rh substrate, then connect structural stability to CH4 activation. Before building those interfaces, two personal-project references should be fixed under the same VASP/PBE settings:

1. Rh bulk -> optimized lattice constant for the Rh(111) substrate.
2. Ce2O3 bulk -> optimized A-type Ce2O3 reference for the overlayer / cluster model.

The CeO2 bulk reference is **not repeated here**, because it has already been completed in the existing workflow.

## Frozen calculation contract for this stage
- VASP on Vanda
- PAW / PBE.54 potentials
- PBE-GGA
- ENCUT = 400 eV
- PREC = Accurate
- EDIFF = 1E-7 eV
- EDIFFG = -0.02 eV/A
- LREAL = .FALSE.
- Ce 4f: Dudarev DFT+U, Ueff = 5.0 eV
- Ce2O3 is spin-polarized.

The 400 eV cutoff and Ueff=5 eV are kept consistent with the current Rh-CeO2 project calculation contract. Do not mix these Stage-1 references later with a different cutoff, PAW family, or Ce U value when comparing energies.

## Jobs included
- `Rh_bulk/` — fcc Rh conventional cell, full cell + ion relaxation.
- `Ce2O3_bulk_FM/` — A-type hexagonal Ce2O3, ferromagnetic initialization.
- `Ce2O3_bulk_AFM_simple/` — same structural cell, simple collinear AFM initialization (+1/-1 on the two Ce atoms).

The two Ce2O3 magnetic initializations are a **screening step**. The lower relaxed total energy is the better reference within these two simple collinear states. This is not a claim that the 5-atom cell exhaustively resolves the experimental low-temperature magnetic order.

## Initial structures
- Rh: fcc conventional cell, starting a = 3.803 A.
- Ce2O3: A-type P-3m1 cell, starting a = 3.8917 A, c = 6.0585 A. Fractional coordinates use a room-temperature neutron-diffraction structural model.

All cells are allowed to relax with `ISIF = 3`, so the starting lattice parameters are initial guesses, not frozen results.

## Run order on Vanda
For each directory:

```bash
cd Rh_bulk                 # or Ce2O3_bulk_FM / Ce2O3_bulk_AFM_simple
bash ../scripts/make_potcar.sh
bash ../scripts/validate_before_submit.sh
qsub job.pbs
```

Check the job:

```bash
qstat -u junbotong
```

After it finishes:

```bash
bash ../scripts/check_result.sh
```

## Important: POTCAR is intentionally not inside this package
VASP PAW files are licensed and should be assembled on Vanda. `make_potcar.sh` looks for the PBE.54 library in several likely locations. If your local Vanda path differs, set it explicitly:

```bash
export VASP_POTCAR_ROOT=/your/actual/potpaw_PBE.54
bash ../scripts/make_potcar.sh
```

Required POTCAR ordering:
- Rh_bulk: `Rh`
- Ce2O3: `Ce O`

Never use `Ce_3` or a different Ce potential silently; if the PBE.54 library exposes multiple Ce variants, stop and verify the intended `Ce` PAW before submitting.

## What to send back after the calculations
For `Rh_bulk`, send:
- `CONTCAR`
- `OUTCAR`
- `OSZICAR`

For both Ce2O3 runs, send the same three files. I will then:
1. compare FM vs simple-AFM energies and magnetic moments;
2. select the Ce2O3 reference;
3. extract the optimized Rh lattice constant;
4. build the first real personal-task models: `Rh(111)`, `Ce2O3 cluster/Rh(111)`, `Ce2O3 layer/Rh(111)`, and the CeO2 control under one consistent slab contract.
