# Stage 5 monitor handoff (cluster vs layer E_int, supervisor task 2026-09-30)

## Task (supervisor, 2026-09-30)
1. Build Ce2O4 cluster/Rh(111) and Ce2O3 cluster/Rh(111).
2. DFT: magnetic moments must be reasonable; IBRION = 2; no extra single point.
3. E_int = E(CexOy/Rh(111)) − E(CexOy) − E(Rh(111)).
4. Compare with the 2026-09-28 Step-3 layer E_int/2: at Ce:O = 2:3 and 2:4, does the cluster or the layer interact
   more strongly with Rh(111)? Plot it.

## Contract
ENCUT 450; ISPIN 2; **no MAGMOM**; PBE+U (Dudarev) Ueff(Ce) 5 eV; IBRION 2, EDIFFG −0.02 eV/Å; final E0 of the
relaxation; LREAL .FALSE.; LDIPOL off. Rh(111) p(4×4) 4 layers, bottom 2 fixed, a0 3.8232 Å, bottom plane z = 0,
c = 25.924 Å (15 Å above the tallest start); Γ 3×3×1; slabs ISMEAR 1/0.10, gas ISMEAR 0/0.05 in 15 Å boxes.
Ce systems: stage A spin SP from scratch (ALGO All) → stage B relaxation from its WAVECAR. PBS `CFP04-CF-046`,
72 h, watchdog 250200 s. Inputs: `build_stage5.py` → `inputs/` (+ MANIFEST.sha256).

Layer values (stage 4, 2026-09-28 Step 3): E_int(Ce4O6/Rh) = −3.267 eV, E_int(Ce4O8/Rh) = −6.008 eV per 3×3 cell
→ −1.634 and −3.004 eV per Ce2O3 / Ce2O4 unit.

## Current jobs (Vanda `/scratch/junbotong/Dynamic_SMSI_stage5_cluster_layer_20260930/inputs/`)

| System | Role | PBS |
|---|---|---|
| R4_Rh111_4x4 | Rh(111) reference | 1415466 |
| C3a_Ce2O3_Rh_from12b | Ce2O3 cluster, start stage-3 S1_12b relaxed | 1415467 |
| C3b_Ce2O3_Rh_from12a | Ce2O3 cluster, start stage-3 S1_12a relaxed | 1415468 |
| C4a_Ce2O4_Rh_from10c | Ce2O4 cluster, start round-1 10c (same registry) | 1415469 |
| C4b_Ce2O4_Rh_from12b_plusO | Ce2O4 cluster, start S1_12b + O in fcc hollow | 1415470 |
| G3_Ce2O3_gas | isolated Ce2O3 | 1415471 |
| G4_Ce2O4_gas | isolated Ce2O4 | 1415472 |

## Monitor
- Task Scheduler `vanda-stage5-monitor-5h` (every 5 h) → `monitor\monitor_stage5.ps1` → server
  `monitor/monitor_stage5.py` (deterministic actions, HISTORY → checks in its docstring) → ATTENTION → headless
  Claude Code CLI (`monitor\claude_takeover_stage5.ps1`, prompt `claude_takeover_prompt_stage5.md`).
- Acceptance: stage B `reached required accuracy`, free-atom Fmax ≤ 0.02 eV/Å, fixed atoms unmoved, every |m(Ce)|
  ≈ 0 or ≈ 1 (no 0.3–0.8), Ce3+ count 2 for Ce2O3 cluster and gas, 0 for Ce2O4 gas, Ce2O4/Rh reported as found,
  max |m(Rh)| ≤ 0.3. No final single point.
- Hub: `D:\Research\Monitor\hub\monitor_hub_projects.json` id `vanda-stage5`, status `monitor\hub_status.json`.
- `monitor/PAUSE` on the server = report only.
- DONE → `results/stage5_table.md` (server), local `analyse_stage5.py` → `results/stage5_Eint.md`,
  `results/stage5_Eint.json`, `results/Fig_cluster_vs_layer_Eint.png`; the task disables itself.

## History
- 2026-09-30 16:14: first set 1415403–409 started; the first monitor round (16:19) used PBS names that did not match
  `job.pbs`, treated the running jobs as ended, archived their files and resubmitted duplicates 1415452–458. All 14 jobs
  deleted at 16:20, the disturbed directories moved to `aborted_20260930_1614/` on Vanda, clean inputs re-uploaded,
  resubmitted as 1415466–472. The monitor now checks cfg PBS name == `#PBS -N` before touching a system.
