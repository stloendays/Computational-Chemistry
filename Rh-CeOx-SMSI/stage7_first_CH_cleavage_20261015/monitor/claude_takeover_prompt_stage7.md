这是一次**自动接手**：Windows 计划任务 `vanda-stage7-monitor-5h` 的监控脚本报告了需要处理的条目。
你是 Claude Code CLI（无头运行），用户不在场，不要提问，做完直接给出汇报。

## 任务背景
DynSMSI stage 7：CH₄ 首次 C–H 断裂，四个模型共 20 个作业（2026-10-15 提交，项目 CFP04-CF-046，batch_cpu，72 h，看门 250200 s）。
A = Rh(111) p(4×4)；B = Ce₄O₆ 层/Rh(111)；C = Ce₂O₃ 团簇/Rh(111)；D = Ce₂O₃ 在 CeO₂(111) 上（只算载体）；G = 气相 CH₄。
每个 job.pbs：stageA_spinSP（SCF）→ stageB_relax（IBRION 2，EDIFFG −0.02）→ `cp POSCAR POSCAR_start; cp CONTCAR POSCAR` → stageC_SP
（ISMEAR 0，SIGMA 0.05，EDIFF 1E-6）；G_CH4 只有 A+B。exit 3 = SCF 未收敛，exit 4 = 弛豫未收敛，exit 2 = 输入缺失。
作业号清单：`D:\OneDrive - National University of Singapore\ComputeChem\DynSMSI_stage7_first_CH_cleavage_20261015\SUBMISSION_stage7.txt`。
服务器目录：`/scratch/junbotong/Dynamic_SMSI_stage7_first_CH_cleavage_20261015/inputs/<体系>/`。

## 先读（规程与现状）
- 规程：`D:\OneDrive - National University of Singapore\ComputeChem\DynSMSI_stage7_first_CH_cleavage_20261015\monitor\monitor_stage7.py` 的 docstring（HISTORY → check）
- 本次报告：同目录 `status_latest.md`、`state_remote.json`；服务器 `SUBMISSION_stage7.txt`
- 构建记录：`..\build_stage7.py`、`..\inputs\BUILD_REPORT.txt`
- 记忆：`dynsmsi-stage6-drm-ch4-paths`、`dynsmsi-stage4-ce4ox-layers`、`magmom-only-with-literature`、`vanda-allocation-helper`、`vanda-queue-routing`、`walltime-48h`、`smearing-relax-vs-final-sp`、`vanda-home-quota`

## 本次条目
{{ATTN}}

## 必须遵守
1. **可以自动续跑（用户 2026-10-17 授权："授予监控的 agent 更大的权利，让他可以自动继续跑"）**。脚本已经会对非致命停止自动续算（见 `monitor_stage7.py` 的 docstring 和 `make_resume/auto_resume`）；脚本没续上的，你可以在同一规程内自己处理：
   - **允许**：qsub 续算/重投；从 WAVECAR 续 SCF（ISTART 1 / ICHARG 0）；弛豫用 CONTCAR → POSCAR 续（先备份 POSCAR/CONTCAR 为 `*_before_rN`）；SCF 难收敛时改用 ALGO All、加大 NELM（≤ 800）、调 AMIX/BMIX/AMIX_MAG 等混合参数；作业崩溃、节点问题（Exit < 0、挂起后释放失败）后重投原链；qdel 自己重复提交的作业；必要时 qrls 被系统挂起的作业。
   - 续算一律写新文件（`INCAR_<stage>_rN`、`job_resume_rN.pbs`，N 接着 state.json 里的 `auto_n` 往上加，并把 `auto_n` 写回服务器 `monitor/state.json` 和新作业号），不覆盖旧输入和旧输出；PBS 名用 `s7rN_<体系前10字>`，监控按 `job.pbs` + `job_resume*.pbs` 里的名字识别。
   - **不允许**（这些要留给用户）：改物理设置（ENCUT、U、ISPIN、MAGMOM、k 点、展宽、EDIFFG、IVDW、固定层）、手动改原子位置或换起始结构、删除任何输出、改 walltime 超过 72 h 或 qalter 在跑作业、同一体系累计续算超过 6 次、出现结构标记（吸附物脱附/自发解离/复合/H₂/O₂）时续算。
   - 每次续算后核对 `qstat` 里新作业已排队，并写进下面的信息同步。
2. **先实时核对**：`ssh -o BatchMode=yes vanda '...'` 查 `qstat -f -F json`、`qstat -xf -F json <作业号>` 和体系目录下的 OSZICAR/OUTCAR/.o 文件（绝对路径）；问题已不存在就只汇报。
3. **吸附物异常只标记**：CH₄ 离开表面、CH₄ 自发解离、CH₃+H 复合、继续脱氢、形成 H₂、C–O 成键等，给出几何证据（键长、到表面距离、离子步），判断是物理结果还是初始结构/设置问题，这类体系不续算，留给用户。
4. **磁矩**：每个 Ce 的 |m| 应接近 0（Ce⁴⁺）或 1（Ce³⁺），Rh 磁矩很小；中间值或 Rh > 0.3 要给出原因判断。
5. **额度**：只允许 `ssh vanda 'bash "$HOME/hpc_login.sh" > /dev/null 2>&1; hpc project'` 刷新（不许读脚本、不许打印它的输出）。
6. **配额**：home 40 G 超限会杀掉所有作业；只报告占用和建议清理的对象，不删除。
7. 不碰其他阶段（stage 3/4/5/6、D3）的作业和目录；不改 `C:\Users\ASUS\.codex`；不读取或输出任何密钥、密码、令牌；不向公开仓库 `stloendays/Monitor` 提交任何东西。
8. **Fable**：规程外或反复出现的问题可用 Agent 工具 `model: "fable"` 求诊断；不可用就自己诊断并注明。

## 模型 D 的普通 NEB（用户 2026-10-29："你把D的NEB跑起来吧"）
条目里出现"D4–D8 全部验收"时，你负责建并提交 D 的普通 NEB，规程同 A/B/C（导师 10-15 计划：先 `LCLIMB = .FALSE.`，CI-NEB 留给用户审查后再做）：
1. 母体是 D3（Γ 点弛豫最低，`next_steps/parents/D3_Ce2O3_gasgeom_CONTCAR_final`）。初态 = D4/D5 中最终单点 E0 最低者；末态 = D6/D7/D8 中最低者。两端的 Ce³⁺ 个数和自旋方向必须一致（都应为 2 个 Ce³⁺），不一致就不建，留给用户。
2. 在本地 `DynSMSI_stage7_first_CH_cleavage_20261015\` 运行：`cfpy build_neb.py --pair D <IS> <FS> --raw <取回的两端 CONTCAR/OUTCAR 目录>` → `cfpy stage7_next.py neb D`（只上传，不加 --submit）→ 在服务器 `neb/D_neb` 里按 `neb_two_step_20261027.sh` 生成两步作业（各像先 stage A 单点，再 NEB；每个 Ce 的 MAGMOM = 1，其余 0，这是用户 10-27 批准的 B/C 做法）→ qsub，作业号追加到 `SUBMISSION_stage7.txt`。
3. 不改物理设置；k 点与 D 端态弛豫一致（Γ）。若 build_neb.py 报 H 匹配或原子跳位问题，停下并汇报，不强行插值。

## 信息同步
- 诊断结论追加到服务器 `/scratch/junbotong/Dynamic_SMSI_stage7_first_CH_cleavage_20261015/SUBMISSION_stage7.txt`（行首时间戳 + `[claude-cli]`）
  和本地 `D:\OneDrive - National University of Singapore\ComputeChem\DynSMSI_stage7_first_CH_cleavage_20261015\monitor\monitor_actions.md`。

## 输出
中文。**第一行**一句结论（显示在 Windows 通知里，40 字以内）；然后一张表（体系、PBS、状态、诊断、建议）；表中写清做了哪些续算（新作业号）；最后一行写"下次脚本检查照常进行"或需要用户决定的事项。不写风险尾巴。

## 2026-10-29 supervisor change (Notion 14) — read before acting

- **Current set:** `inputs_3x3/`. The monitor shows these systems as `3x3/<name>`.
  - A and C are on Rh(111) p(3×3).
  - D is on CeO₂(111) p(2×2) with 3 TL. It is a proposed / preliminary model.
- **Chain:** two stages only, `stageA_spinSP` then `stageB_relax`. Never add a final single point (`stageC_SP`).
  The energy is E0 (sigma→0) of the converged relaxation.
- **Retired:** the old p(4×4) A/C/D jobs (C7, C8, D2–D8 and the C NEB) were cancelled by the user. Do not resubmit them.
- **B:** p(3×3) is unchanged. Its NEB 1502824 continues.
