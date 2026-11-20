# 服务器端监控与自动续算（2026-11-20 起）

这套做法让续算不再依赖本地电脑。起因：本地 Windows 计划任务（每 5 h 一次，ssh 到 Vanda 跑 `monitor_stage7.py`）在笔记本休眠时漏跑。11-18 20:28 之后连漏 7 次，期间 B 的普通 NEB 已经收敛，却没人接着处理。

## 做法

`server_monitor.pbs` 是一个可以自己续投的小作业：

1. 用 auto_free 队列，1 核、4 GB、walltime 2 h，作业名 `s7mon`，不计机时。
2. 运行时先 ssh 到 `stdct-login-01`，失败就换 `stdct-login-02`，在登录节点上跑 `monitor/monitor_stage7.py`。这个脚本和本地任务调用的是同一个，所以续算、重投、记录的规则完全相同。两个登录节点都连不上时才在计算节点上直接跑，这时查不了配额。
3. 跑完把结果记一行到 `server_monitor.log`，完整报告存为 `last_run.txt`。
4. 用 `qsub -a <当前时间+INTERVAL_H>` 把下一次排上；PBS 在那个时间之前不会启动它，排队时显示状态 W。
5. 以下三种情况不再续投：
   - 存在 `STOP` 文件；
   - 监控报告全部完成（`DONE=1`）；
   - 队列里已经有另一个 `s7mon` 在等（用 `qselect -N s7mon` 判断，防止链条分叉）。

本地计划任务照常保留，用来拉回状态、在出现"需要处理"时启动 Claude 接手。两边共用监控脚本里的同一把 mkdir 锁（`monitor/lock`），不会同时动同一个作业。

## 操作

| 目的 | 命令（在 stage 目录下） |
|---|---|
| 启动或重启链条 | `qsub monitor/server/server_monitor.pbs` |
| 停止 | `touch monitor/server/STOP`（下一次运行时退出），或 `qdel` 正在等待的 s7mon |
| 改间隔 | `echo 3 > monitor/server/INTERVAL_H`（单位小时，默认 5） |
| 看运行记录 | `tail monitor/server/server_monitor.log` |
| 看最近一次报告 | `monitor/status_latest.md` 或 `monitor/server/last_run.txt` |

## 踩过的坑（都用探针作业实测过，见 `probe_20261120/`）

| 发现 | 证据 | 处理 |
|---|---|---|
| 本账号不能用 crontab | `crontab -l` 报 "You (junbotong) are not allowed to use this program" | 改用 PBS 自续投 |
| 计算节点上没有 `hpc` 命令，查不了额度和配额 | 探针 1595612：`hpc: command not found` | 监控通过 ssh 回登录节点跑 |
| 计算节点可以 qsub，也能免密 ssh 回登录节点 | 探针 1595591 的子作业 1595610 跑完（`child.out`）；1595612 里 `ssh stdct-login-01` 后 `hpc project` 正常 | 续投和续算都在服务器内部完成 |
| 计算节点上有 python3 | 3.9.18，`/bin/python3` | 不需要加载 module |
| `hpc_login.sh` 刷新后第一次 `hpc project` 偶尔读不到额度，再刷一次就正常 | 11-20 B CI-NEB 提交前遇到一次 | 提交脚本先检查额度；续投失败时隔 2 min 重试，共 3 次 |
| 本地 Windows 上写出的 .pbs 可能带 CRLF | — | 上传后执行 `sed -i 's/\r$//'`，再用 `bash -n` 检查语法 |

## 同时加入的续算功能：端点 WAVECAR 播种

NEB 的中间像有时会落到和两个端点不同的电子态。例如 C 的所有像都变成 0 个 Ce³⁺，而端点是 2 个。之后如果各像继续读自己的 WAVECAR，就会一直停在错误的势能面上。

处理办法：在 NEB 目录里放一个 `RESEED_ENDPOINT_WAVECAR` 文件。`monitor_stage7.py` 的 `neb_resume` 在下次续算时会：

- 先照常把各像的 CONTCAR 拷成 POSCAR；
- 01–03 拷入 IS 端点的 WAVECAR，04–06 拷入 FS 端点的 WAVECAR，用 `cmp` 核对前 1 MB；
- NBANDS 改成端点 OUTCAR 里的值（两个端点必须相同），设 ISTART 1 / ICHARG 0；
- 旧 WAVECAR 改名为 `WAVECAR_before_rN` 保留，INCAR 备份为 `*.before_reseed_rN`，标记文件改名为 `.done_rN`；
- 只用这一次，之后的续算照常读各像自己的 WAVECAR。

上线前，这段逻辑在 Vanda 上用假目录做过沙盒测试，覆盖了 WAVECAR 来源、NBANDS 写入、备份、日志，以及第二次续算不再播种。B 在 11-14 用同样的思路（读端点 WAVECAR + CHGCAR）手动续算，4 个 Ce³⁺ 一直保持到收敛。
