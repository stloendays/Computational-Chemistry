"""Build Stage-2 (interface thermodynamics) inputs for the Dynamic SMSI project.

Contract (frozen 2026-09-10):
  substrate  Rh(111) p(3x3), 4 layers, bottom 2 fixed, a0(PBE,400eV) = 3.8232 A (Stage-1 Rh bulk)
  overlayer  2x2 CeO2(111)/Ce2O3 commensurate with 3x3 Rh(111)  (oxide strain ~ +4 %)
  vacuum     >= 15 A, c = 30 A, dipole correction along z
  electrons  PBE+U (Ce 4f, Ueff = 5 eV), ENCUT 400, Gamma 4x4x1, ISMEAR=1/0.1, ISPIN=2, LREAL=.FALSE.
  ions       IBRION=2, EDIFFG = -0.02 eV/A
All coordinates below are initial guesses for relaxation, not results.
"""
import os, math, itertools
import numpy as np

A0_RH = 3.8232328896          # Stage-1 Rh bulk CONTCAR (PBE, 400 eV)
A_S   = A0_RH / math.sqrt(2)  # Rh(111) surface lattice constant
D_RH  = A0_RH / math.sqrt(3)  # (111) interlayer spacing
N     = 3                     # p(3x3)
C     = 30.0
NLAY  = 4
NFIX  = 2
Z0    = 2.0                   # z of the bottom Rh layer
A_CELL = N * A_S

a1 = np.array([A_CELL, 0.0, 0.0])
a2 = np.array([A_CELL / 2, A_CELL * math.sqrt(3) / 2, 0.0])
a3 = np.array([0.0, 0.0, C])
CELL = np.array([a1, a2, a3])


def surf(u, v, z):
    """(u, v) in units of the 1x1 Rh surface cell (60-degree basis); z absolute."""
    return (u / N) * a1 + (v / N) * a2 + np.array([0.0, 0.0, z])


def rh_slab():
    atoms = []
    for L in range(NLAY):
        shift = L / 3.0                       # ABC stacking
        z = Z0 + L * D_RH
        for i in range(N):
            for j in range(N):
                atoms.append(("Rh", surf(i + shift, j + shift, z), L < NFIX))
    return atoms


ZTOP = Z0 + (NLAY - 1) * D_RH
TOPSHIFT = ((NLAY - 1) / 3.0) % 1.0          # top layer (L=3) shift = 0
FCC = TOPSHIFT + 1 / 3.0                     # hollow above layer L=1 (shift 1/3)
HCP = TOPSHIFT + 2 / 3.0                     # hollow above layer L=2 (shift 2/3), directly below top

# ---------------- CeO2(111) O-Ce-O trilayer, 2x2 on 3x3 ----------------------
DZ_OCE = 0.794                                # a0(CeO2, PBE 5.503) / (4 sqrt3)


def trilayer(s, z_ce, remove=()):
    """2x2 trilayer with the Ce sublattice shifted by s (Rh surface-cell units).
    Oxide 1x1 = 1.5 Rh cells. Ce at (0,0); O_top at +(1/3,1/3); O_bot at +(2/3,2/3) of the oxide cell."""
    at = []
    k = 0
    for i, j in itertools.product(range(2), range(2)):
        u0, v0 = 1.5 * i + s, 1.5 * j + s
        at.append(("Ce", surf(u0, v0, z_ce), False, f"Ce{k}"))
        at.append(("O", surf(u0 + 0.5, v0 + 0.5, z_ce + DZ_OCE), False, f"Ot{k}"))
        at.append(("O", surf(u0 + 1.0, v0 + 1.0, z_ce - DZ_OCE), False, f"Ob{k}"))
        k += 1
    return [a for a in at if a[3] not in remove]


# ---------------- Ce2O3 cluster, one formula unit -----------------------------
def cluster(kind):
    ex = np.array([1.0, 0.0, 0.0])
    ey = np.array([0.0, 1.0, 0.0])
    ez = np.array([0.0, 0.0, 1.0])
    if kind == "A":  # O-down chain: O-Ce-O-Ce-O, outer O bond to Rh, apex O bridges the Ce pair
        c1 = surf(1 + FCC, 1 + FCC, ZTOP + 2.5)
        c2 = c1 + 3.9 * ex
        mid = 0.5 * (c1 + c2)
        return [("Ce", c1, False), ("Ce", c2, False),
                ("O", mid + 1.4 * ez, False),
                ("O", c1 + (-1.6 * ex + 1.8 * ey - 0.6 * ez), False),
                ("O", c2 + (1.6 * ex - 1.8 * ey - 0.6 * ez), False)]
    if kind == "B":  # Ce-down: Ce pair in contact with Rh, two flank O + one apex O
        c1 = surf(1 + FCC, 1 + FCC, ZTOP + 2.8)
        c2 = c1 + 3.9 * ex
        mid = 0.5 * (c1 + c2)
        return [("Ce", c1, False), ("Ce", c2, False),
                ("O", mid + 1.8 * ey + 0.3 * ez, False),
                ("O", mid - 1.8 * ey + 0.3 * ez, False),
                ("O", mid + 1.7 * ez, False)]
    raise ValueError(kind)


# ---------------- writers -----------------------------------------------------
ORDER = ["Rh", "Ce", "O"]


def write_poscar(path, title, atoms, cell, seldyn=True):
    syms = [s for s in ORDER if any(a[0] == s for a in atoms)]
    lines = [title, "1.0"]
    for v in cell:
        lines.append("  %.10f  %.10f  %.10f" % tuple(v))
    lines.append("  ".join(syms))
    lines.append("  ".join(str(sum(1 for a in atoms if a[0] == s)) for s in syms))
    if seldyn:
        lines.append("Selective dynamics")
    lines.append("Cartesian")
    for s in syms:
        for a in atoms:
            if a[0] == s:
                flag = ("F F F" if a[2] else "T T T") if seldyn else ""
                lines.append("  %.8f  %.8f  %.8f  %s" % (a[1][0], a[1][1], a[1][2], flag))
    with open(path, "w", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    return syms


def min_dist(atoms, cell):
    P = np.array([a[1] for a in atoms])
    inv = np.linalg.inv(cell)
    best = (1e9, None)
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            f = (P[j] - P[i]) @ inv
            f -= np.round(f)
            r = np.linalg.norm(f @ cell)
            if r < best[0]:
                best = (r, (atoms[i][0], atoms[j][0]))
    return best


def ldau_block(syms):
    L = " ".join("3" if s == "Ce" else "-1" for s in syms)
    U = " ".join("5.0" if s == "Ce" else "0.0" for s in syms)
    J = " ".join("0.0" for _ in syms)
    return f"LDAU = .TRUE.\nLDAUTYPE = 2\nLDAUL = {L}\nLDAUU = {U}\nLDAUJ = {J}\nLMAXMIX = 6\n"


def incar_slab(system, syms, counts, ispin):
    s = (f"SYSTEM = {system}\nISTART = 0\nICHARG = 2\nPREC = Accurate\nENCUT = 400\n"
         f"EDIFF = 1E-5\nNELM = 250\nNELMIN = 4\nISPIN = {ispin}\n")
    if ispin == 2:
        mm = " ".join(f"{c}*{1.0 if s == 'Ce' else 0.0:.1f}" for s, c in zip(syms, counts))
        s += f"MAGMOM = {mm}\nISYM = 0\n"
    # Mixing: VASP default Kerker scheme. The linear-mixing recipe (BMIX = 1e-4) inherited from the insulating
    # CeO2(111) slab causes charge sloshing on the metallic Rh substrate (SCF hit NELM without converging, 2026-09-10).
    s += ("ISMEAR = 1\nSIGMA = 0.10\nALGO = Normal\nAMIN = 0.01\nMAXMIX = 40\n"
          "LREAL = .FALSE.\nLASPH = .TRUE.\nADDGRID = .TRUE.\n"
          "LORBIT = 11\nIBRION = 2\nPOTIM = 0.20\nNSW = 200\nISIF = 2\nEDIFFG = -0.02\n"
          "IDIPOL = 3\nLDIPOL = .TRUE.\nKPAR = 4\nNCORE = 3\nLWAVE = .TRUE.\nLCHARG = .TRUE.\n")
    if "Ce" in syms:
        s += ldau_block(syms)
    return s


INCAR_O2 = """SYSTEM = O2 triplet, 15 A box
ISTART = 0
ICHARG = 2
PREC = Accurate
ENCUT = 400
EDIFF = 1E-7
NELM = 200
ISPIN = 2
MAGMOM = 2*1.0
ISYM = 0
ISMEAR = 0
SIGMA = 0.05
ALGO = Normal
LREAL = .FALSE.
LASPH = .TRUE.
ADDGRID = .TRUE.
IBRION = 2
POTIM = 0.20
NSW = 60
ISIF = 2
EDIFFG = -0.02
LWAVE = .FALSE.
LCHARG = .FALSE.
"""

INCAR_CEO2_BULK = """SYSTEM = CeO2 bulk Ce4O8 | same contract as Stage-1 Ce2O3 bulk
ISTART = 0
ICHARG = 2
ENCUT = 400
PREC = Accurate
EDIFF = 1E-7
EDIFFG = -0.02
ISPIN = 2
MAGMOM = 4*0.0 8*0.0
ISYM = 0
IBRION = 2
NSW = 120
ISIF = 3
POTIM = 0.25
ISMEAR = 0
SIGMA = 0.05
ALGO = Normal
NELM = 220
LREAL = .FALSE.
ADDGRID = .TRUE.
LASPH = .TRUE.
LDAU = .TRUE.
LDAUTYPE = 2
LDAUL = 3 -1
LDAUU = 5.0 0.0
LDAUJ = 0.0 0.0
LMAXMIX = 6
LWAVE = .FALSE.
LCHARG = .FALSE.
"""

JOB = """#!/usr/bin/env bash
#PBS -N {name}
#PBS -P CFP03-CF-126
#PBS -l select=1:ncpus=36:mpiprocs=36:ompthreads=1:mem={mem}
#PBS -l walltime={hours:02d}:00:00
#PBS -j oe

set -euo pipefail
cd "$PBS_O_WORKDIR"
for f in INCAR POSCAR KPOINTS POTCAR; do
  test -s "$f" || {{ echo "Missing or empty $f" >&2; exit 2; }}
done
module purge
module load intel/2021b
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
VASP_BIN=/nfs/home/svu/junbotong/software/vasp/NUS_HPC_VASP/vasp_632_vtst_solpp_beef_std
test -x "$VASP_BIN" || {{ echo "VASP executable not found: $VASP_BIN" >&2; exit 2; }}
NP=$(wc -l < "$PBS_NODEFILE")
echo "job_id=$PBS_JOBID host=$(hostname) ranks=$NP workdir=$PBS_O_WORKDIR start=$(date --iso-8601=seconds)"
rm -f STOPCAR
mpirun -np "$NP" "$VASP_BIN" > vasp.out &
VASP_PID=$!
(
  sleep {secs}
  if kill -0 "$VASP_PID" 2>/dev/null; then
    printf 'LSTOP = .TRUE.\\n' > STOPCAR
    echo "watchdog_requested_stop=$(date --iso-8601=seconds)"
  fi
) &
WATCHDOG_PID=$!
set +e
wait "$VASP_PID"
RC=$?
set -e
kill "$WATCHDOG_PID" 2>/dev/null || true
wait "$WATCHDOG_PID" 2>/dev/null || true
rm -f STOPCAR
echo "end=$(date --iso-8601=seconds) rc=$RC"
exit "$RC"
"""


def write(path, text):
    with open(path, "w", newline="\n") as f:
        f.write(text)


def kpoints(path, mesh, comment):
    write(path, f"{comment}\n0\nGamma\n{mesh[0]} {mesh[1]} {mesh[2]}\n0 0 0\n")


ROOT = "inputs"
os.makedirs(ROOT, exist_ok=True)
report = []


def emit(name, title, atoms, hours, ispin=2, cell=CELL, kmesh=(4, 4, 1), incar=None, seldyn=True, mem="120gb"):
    d = os.path.join(ROOT, name)
    os.makedirs(d, exist_ok=True)
    syms = write_poscar(os.path.join(d, "POSCAR"), title, atoms, cell, seldyn)
    counts = [sum(1 for a in atoms if a[0] == s) for s in syms]
    write(os.path.join(d, "INCAR"), incar if incar else incar_slab(title, syms, counts, ispin))
    kpoints(os.path.join(d, "KPOINTS"), kmesh, title)
    write(os.path.join(d, "POTCAR.spec"), "\n".join(syms) + "\n")
    write(os.path.join(d, "job.pbs"), JOB.format(name="s2_" + name, mem=mem, hours=hours, secs=hours * 3600 - 1800))
    report.append((name, dict(zip(syms, counts)), min_dist(atoms, cell)))


slab = rh_slab()
strip = lambda lst: [(a[0], a[1], a[2]) for a in lst]

emit("00_Rh111_clean", "Rh(111) p(3x3) 4L clean | Stage-2 substrate", slab, 4, ispin=1)

emit("10a_Ce2O3_cluster_Odown", "Ce2O3 unit on Rh(111) 3x3, initial A: O toward Rh",
     slab + strip(cluster("A")), 12)
emit("10b_Ce2O3_cluster_Cedown", "Ce2O3 unit on Rh(111) 3x3, initial B: Ce toward Rh",
     slab + strip(cluster("B")), 12)

Z_CE = ZTOP + 2.1 + DZ_OCE
emit("20a_Ce4O8_layer_regFCC", "2x2 CeO2(111) O-Ce-O trilayer on Rh(111) 3x3, Ce0 over fcc",
     slab + strip(trilayer(FCC, Z_CE)), 12)
emit("20b_Ce4O8_layer_regTOP", "2x2 CeO2(111) O-Ce-O trilayer on Rh(111) 3x3, Ce0 over top",
     slab + strip(trilayer(0.0, Z_CE)), 12)

VAC = {"30a_Ce4O6_layer_2Obot": ("Ob0", "Ob3"),
       "30b_Ce4O6_layer_2Otop": ("Ot0", "Ot3"),
       "30c_Ce4O6_layer_1top1bot": ("Ot0", "Ob3")}
for tag, rem in VAC.items():
    emit(tag, f"2x2 Ce2O3-type layer Ce4O6 on Rh(111) 3x3, removed {rem[0]} {rem[1]}, Ce0 over fcc",
         slab + strip(trilayer(FCC, Z_CE, remove=rem)), 12)

FREE = {"50a_Ce4O8_film_free": (), "50b_Ce4O6_film_2Obot": ("Ob0", "Ob3"),
        "50c_Ce4O6_film_2Otop": ("Ot0", "Ot3"), "50d_Ce4O6_film_1top1bot": ("Ot0", "Ob3")}
for tag, rem in FREE.items():
    emit(tag, f"free-standing 2x2 film in the 3x3 Rh(111) cell (strained reference), removed {rem}",
         strip(trilayer(FCC, Z_CE, remove=rem)), 4, mem="64gb")

box = np.eye(3) * 15.0
o2 = [("O", np.array([7.5, 7.5, 7.5 - 0.615]), False), ("O", np.array([7.5, 7.5, 7.5 + 0.615]), False)]
emit("40_O2_gas", "O2 triplet 15 A box", o2, 1, cell=box, kmesh=(1, 1, 1), incar=INCAR_O2, seldyn=False, mem="32gb")

a = 5.503
ce = [(0, 0, 0), (0, .5, .5), (.5, 0, .5), (.5, .5, 0)]
ox = [(x + .25, y + .25, z + .25) for x, y, z in ce] + [(x + .75, y + .75, z + .75) for x, y, z in ce]
bulk = [("Ce", np.array(p) * a, False) for p in ce] + [("O", np.array(p) * a, False) for p in ox]
emit("41_CeO2_bulk", "CeO2 fluorite conventional cell | Stage-2 reference", bulk, 2,
     cell=np.eye(3) * a, kmesh=(9, 9, 9), incar=INCAR_CEO2_BULK, seldyn=False, mem="32gb")

print(f"a_s={A_S:.4f}  cell={A_CELL:.4f}  d={D_RH:.4f}  ztop={ZTOP:.3f}  fcc={FCC:.3f} hcp={HCP:.3f}")
ox1 = A_CELL / 2
print(f"oxide 1x1 = {ox1:.4f} A ; CeO2(111) PBE = {5.503 / math.sqrt(2):.4f} -> strain "
      f"{100 * (ox1 / (5.503 / math.sqrt(2)) - 1):+.2f} % ; Ce2O3 a=3.9008 -> {100 * (ox1 / 3.9008 - 1):+.2f} %")
for n, c, (r, pair) in report:
    print(f"{n:30s} {str(c):30s} min dist {r:.3f} A {pair}")
