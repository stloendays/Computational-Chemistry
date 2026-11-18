# Stage-7 NEB 进展（2026-11-18）

接 [`NEB_status_20261109.md`](NEB_status_20261109.md)。能量取弛豫 E₀（σ → 0），3×3 晶胞，设置同前（PBE+U，Ce 4f 5 eV，
ENCUT 450，ISPIN 2，ISMEAR 1 / SIGMA 0.10，k 4×4×1，6 像，FIRE，EDIFFG −0.05）。

## 1. 四个模型的路径与结果

| 模型 | IS → FS | ΔE (eV) | 能垒 (eV) | 状态 |
|---|---|---|---|---|
| A Rh(111) | A1 CH₄* → A2 CH₃*(top) + H*(fcc) | +0.264 | **0.714**（CI-NEB，爬坡像 05） | 完成，频率已算 |
| B Ce₄O₆ 层 / Rh(111) | B5b CH₄ → B14 CH₃O*(O43) + OH*(O45) | +0.315 | ≈1.36（普通 NEB，未收敛） | r3 在跑，各像 Fmax ≤ 0.078 |
| C Ce₂O₃ 团簇 / Rh(111) | C10 CH₄ → C9 CH₃*(周界 Rh) + OH*(团簇 O) | +0.557 | 未得（各像 Fmax 0.3–2.3） | r2 在跑 |
| D Ce₂O₃ 团簇 / CeO₂(111) | D9 CH₄ → D11 CH₃• + OH*(O38) | +0.945 | — | 普通 NEB 已停（用户 11-12） |

### A：CI-NEB 与爬坡像频率
- CI-NEB 1539729：53 步，各像 Fmax ≤ 0.049 eV/Å；爬坡像 05 C–H 1.552 Å、C–Rh 2.201 Å、H–Rh 1.648 Å（同一 Rh 顶位氧化加成）。
- 频率 1551032（`neb_3x3/A_cineb_freq05`，只放开 C + 4 H，IBRION 5）：925.4i cm⁻¹ 为断裂 C–H 伸缩；42.1i、85.5i cm⁻¹ 为 CH₃ 转动的软模。原始频率表 `frequencies.txt`。

### B：末态重建为 B14
- B12（CH₃O* 在 O40）离 B5b 9.14 Å，含 CH₃ 迁移，不是基元步；B13（CH₃ 原位 + OH*）弛豫中 CH₃ 与 H 复合回 CH₄，终态不成立，已停。
- B 层 4 个 Ce 全为 Ce³⁺，CH₃ 只能以甲氧基存在 → B14：CH₃ 接 B5b 正下方的 O43，H 接 O45；dist.pl B5b → B14 6.30 Å。E₀ −353.39911 eV，Ce³⁺ 4。
- NEB 1550784（ALGO Normal，ISTART 0）13 h 没走出离子步；改 ALGO All 仍卡；r2 起各像读端点 WAVECAR + CHGCAR（01–03 读 B5b，04–06 读 B14，NBANDS 276）后正常推进。
- 当前 r3（1580815）：最高像 05 +1.356 eV，各像磁矩 ≈ 4 μB，与端点 Ce³⁺ 4 一致。

### C：慢在电子步
- 11-14 PBS 故障后 1551449 被系统重排，从旧 POSCAR 重起，约 22 h 进度被覆盖；当时各像 CONTCAR 存为 `*/CONTCAR_lost_run_20261114`。
- r2（1580814）21.8 h 只走 2 个离子步：`job_neb.pbs` 每次 `cp INCAR_neb INCAR`，而 `INCAR_neb` 为 ISTART 0 / ICHARG 2，续算不读已有 WAVECAR，5/6 像首步电子步满 NELM 300。
  11-18 起 `INCAR_neb` 改为 ISTART 1 / ICHARG 0（下次续算生效），监控 `neb_resume` 同步改为"各像 WAVECAR 齐全就读"。
- 中间像总磁矩 −0.1–0.3 μB，端点为 2 μB（2 个 Ce³⁺）；按导师 11-06 意见中途不干预，收敛后逐像核对 Ce³⁺。

### D：CH₃ 在 D 上不吸附
- D11 末态 CH₃ 离开团簇（C–Ce13 4.05 Å），呈游离 CH₃•；D13 把 CH₃ 放到 Ce13 上（2.55 Å）弛豫后回到同一构型（E₀ 与 D11 差 1 meV）。
- D12 甲氧基 CH₃O*(O40) + OH*(O38) 比 D9 低 1.18 eV，是产物能差，不是直接断键的能垒。
- 即没有 Rh 时 Ce₂O₃/CeO₂ 不能稳定 CH₃*；活化需要 Rh 上的 CeOx（SMSI），D 作对照。

## 2. 文件

- 新端点输入：`inputs_3x3/B13_*`、`B14_*`、`D11_*`、`D12_*`、`D13_*`（INCAR、KPOINTS、POSCAR、CONTCAR、job.pbs）。
- NEB：`neb_3x3/A_cineb`、`A_cineb_freq05`、`B_neb`、`C_neb`；`neb_profile_now.txt` 为 11-18 读数。
- 作业记录：`SUBMISSION_stage7.txt`；监控：`monitor/monitor_stage7.py`。
