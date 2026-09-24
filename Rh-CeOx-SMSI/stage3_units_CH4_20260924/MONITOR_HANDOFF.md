# Stage-3 monitoring handoff (written 2026-09-24 22:50 SGT)

Protocol for everyone who touches the stage-3 jobs: the scheduled script, the Claude Code CLI takeover, and interactive
sessions. Contract and energy definitions: `README.md`. Binding rules: GitHub `stloendays/Computational-Chemistry`
README (ISPIN 2 everywhere, ENCUT 450, slab bottom plane at z = 0, supervisor's `discussion progress` defines the workflow).

## Where things are

| What | Path |
|---|---|
| Vanda working dir | `/scratch/junbotong/Dynamic_SMSI_stage3_units_CH4_20260924/` (`~/Rh_CeO2_personal/Dynamic_SMSI_stage3_units_CH4_20260924` links here) |
| server monitor | `.../monitor/monitor_stage3.py`, state `.../monitor/state.json`, report `.../monitor/status_latest.md`, `PAUSE` = report only |
| server action log | `.../SUBMISSION_stage3.txt` (`[monitor]` = script, `[claude-cli]` = takeover) |
| local wrapper | `monitor/monitor_stage3.ps1` (Task Scheduler `vanda-stage3-monitor-5h`, every 5 h) |
| CLI takeover | `monitor/claude_takeover_stage3.ps1` + `monitor/claude_takeover_prompt_stage3.md`; output `monitor/claude_takeover_latest.md` |
| local copies | `monitor/status_latest.md`, `monitor/state_remote.json`, `SUBMISSION_stage3.md`, records in `ComputeChem/Vanda_monitor_records/` |

## Current jobs (22:40)

| System | PBS | State |
|---|---|---|
| S1_00_Rh_bulk_450 | 1393602 | done, accepted: a0(450 eV) = 3.8238 A (slabs use 3.8232) |
| S1_01_Rh111_4x4 | 1393603 | R, relaxation |
| S1_02_Rh111_3x3 | 1393717 | R, relaxation |
| S1_11a_CeO2_Rh_flat | 1393606 | R, stage A (spin SP, ALGO All) |
| S1_11b_CeO2_Rh_Cedown | 1393607 | R, stage A |
| S1_12a_Ce2O3_Rh_from10a | 1393604 | R, stage A |
| S1_12b_Ce2O3_Rh_from10b | 1393605 | R, stage A |
| S1_21_CeO2_gas | 1393608 | done, accepted: E0 -19.08022 eV, Ce4+ (0 muB) |
| S1_22_Ce2O3_gas | 1393609 | done, accepted: E0 -34.23422 eV, 2 Ce3+ FM |
| S1_23_Ce2O3_bulk_AFM | 1393719 | Q |
| S1_31_Ce4O6_layer_Rh3x3 | 1393718 | Q |

## What the script does by itself

- held ("too many failed attempts") -> qdel + resubmit (max 2);
- stage A (spin SP) hit NELM -> resume A from WAVECAR, then B (max 1);
- relaxation stopped (watchdog / NSW / walltime) -> archive `segNN_*`, CONTCAR -> POSCAR (`POSCAR_orig` kept), restart
  from WAVECAR/CHGCAR with `job_restart.pbs` (max 4 segments);
- crash without end line -> archive `crash_*`, resubmit (max 3);
- chain finished -> acceptance (free-atom Fmax <= 0.02 eV/A, fixed atoms unmoved, Ce3+ where expected, no desorption /
  O2); slabs then get `final_sp/` (ISPIN 2, 450 eV, LDIPOL on, IDIPOL 3, EDIFF 1e-6, ALGO All, from the relaxed
  WAVECAR/CHGCAR); gas and bulk are final after acceptance;
- final SP not finished -> NELM 800 retry (max 1);
- everything final -> `results/stage3_step1_table.md`, DONE, then the CLI finalises and syncs, the task disables itself.
- qsub refused for allocation reasons -> `~/hpc_login.sh` silently, retry once.

Anything beyond these, or a counter exceeded, is an ATTENTION item and starts the CLI takeover.

## Round 2 is paused

`Dynamic_SMSI_stage2_interfaces_20260910/round2` is paused on the user's request (2026-09-24 18:28): its `monitor/PAUSE`
stays, task `vanda-round2-monitor-5h` stays disabled, its jobs are not resumed.
