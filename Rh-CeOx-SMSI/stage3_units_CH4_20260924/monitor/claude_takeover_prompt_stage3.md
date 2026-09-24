这是一次**自动接手**：Windows 计划任务 `vanda-stage3-monitor-5h` 的监控脚本报告了需要处理的条目（或第 1 步已完成需要收尾同步）。
你是 Claude Code CLI（无头运行），用户不在场，不要提问，做完直接给出汇报。

## 先读（规程与现状）
- `D:\OneDrive - National University of Singapore\ComputeChem\DynSMSI_stage3_units_CH4_20260924\MONITOR_HANDOFF.md`（规程，按它办事）
- 同目录 `monitor\status_latest.md`（本次脚本报告全文）、`monitor\state_remote.json`（服务器 state.json 的副本）、`SUBMISSION_stage3.md` 末尾几节
- `README.md`（合同）与记忆：`dynsmsi-stage3-units-ch4`、`dynsmsi-stage2-interfaces`（导师约束）、`vasp-encut-450`、
  `slab-model-no-bottom-gap`、`vanda-allocation-helper`、`vanda-queue-routing`

## 本次条目
{{ATTN}}

## 必须遵守
1. **先实时核对再动手**：`ssh -o BatchMode=yes vanda '...'` 查 `qstat -f -F json`、相关目录（在 `/scratch/junbotong/Dynamic_SMSI_stage3_units_CH4_20260924/inputs/<体系>/`，命令里一律用绝对路径或先 `cd`）的 OSZICAR/OUTCAR/.o；问题已不存在就只汇报。
2. **不和别的进程抢同一作业**：qsub/qdel 前确认服务器上 `.../monitor/lock` 不存在（存在就等 5 分钟再查，最多 3 次），队列里没有同名作业；`SUBMISSION_stage3.txt` 最近 30 分钟有非 `[monitor]` 的新行（用户或另一个会话在处理）→ 不操作，只汇报。
3. **合同不许改**：所有新作业、续算、单点都是 ISPIN = 2（任何阶段都不许 ISPIN = 1）、ENCUT = 450、PBE+U 5 eV、slab 底层 z = 0、真空 ≥ 15 Å、`#PBS -P CFP03-CF-126`、walltime 72:00:00、看门 250200 s。换泛函/U/ENCUT、新增构型、改晶胞：只写建议，不执行。
4. **只做可逆、规程内的操作**：续算、重投、调 NELM/ALGO/混合参数重跑单点。导师文档之外的新计算不做。
5. **额度**：qsub 报额度/项目问题时，先 `ssh vanda 'bash "$HOME/hpc_login.sh" > /dev/null 2>&1; hpc project'` 刷新（不许读脚本、不许打印它的输出），确认 CFP03-CF-126、junbotong、余额为正后重试；仍失败才在汇报里请用户处理。
6. **第二轮（`Dynamic_SMSI_stage2_interfaces_20260910/round2`）处于用户要求的暂停状态**：不许动那里的作业，不许删它的 `monitor/PAUSE`，不许启用 `vanda-round2-monitor-5h`。
7. **Fable**：规程外或反复失败的问题用 Agent 工具 `model: "fable"` 求诊断；Fable 不可用就自己诊断，并在汇报里注明。
8. 不改 `.codex` 目录，不读取或输出任何密钥、密码、令牌。

## 信息同步（用户要求"注意同步信息"，每次都做）
- 你做的每个动作：追加到服务器 `SUBMISSION_stage3.txt`（行首时间戳 + `[claude-cli]`）和本地 `SUBMISSION_stage3.md`。
- 作业号变了：更新 `MONITOR_HANDOFF.md` 的"当前作业"表；问题解决后把服务器 `monitor/state.json` 里对应体系的计数（a_resume / seg / crash / hold / sp_resume）改回，并把 `phase` 设成脚本能继续接管的值。
- 记忆 `dynsmsi-stage3-units-ch4.md` 的"状态"一行改成最新（日期、完成了哪些、还在跑哪些）。
- 条目是 **DONE**：核对 `results/stage3_step1_table.md`，把结果表、各体系最终 CONTCAR、INCAR（小文件，绝不含 POTCAR/WAVECAR/CHGCAR/OUTCAR）同步到本地 `DynSMSI_stage3_units_CH4_20260924/results/` 和 GitHub 仓库
  `D:\Research\Computational-Chemistry\Rh-CeOx-SMSI\stage3_units_CH4_20260924\results\`，用
  `git -c user.name=Tony -c user.email=157110190+stloendays@users.noreply.github.com commit` 提交并 push；更新 README 状态行。第 2 步不要自己开始建，写进汇报等用户决定。

## 输出
中文。**第一行**一句结论（显示在 Windows 通知里，40 字以内）；然后一张表（体系、PBS、状态、做了什么、结果）；最后一行写"下次脚本检查照常进行"或需要用户决定的事项。不写风险尾巴。
