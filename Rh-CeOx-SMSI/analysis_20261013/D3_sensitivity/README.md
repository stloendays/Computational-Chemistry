# D3 敏感性测试（2026-10-13）

主线合同不变：Stage 4–6 全部 **不加 D3**（用户 2026-10-13）。本测试只回答一个问题：PBE-D3(BJ) 会不会改变已经给出的结论。

## 两级

| 级别 | 做法 | 状态 |
|---|---|---|
| 1 冻结几何 | 在 Stage 4/5 已收敛的 PBE+U 结构上加 D3 能量（s-dftd3 1.2.1，`--bj pbe`，无三体项 = VASP `IVDW = 12`）。D3 只依赖几何，因此这就是该几何下 PBE+U+D3 的精确能量 | 完成 |
| 2 D3 重弛豫 | L6 / L7i / L8 以 Stage-4 收敛结构 + WAVECAR 起步，INCAR 只加 `IVDW = 12`，FIRE 弛豫后接 Stage-4 同设置的最终单点（ISMEAR 0 / SIGMA 0.05）+ D3 | 作业 1455137 / 1455138 / 1455139 在跑 |

Vanda：`/scratch/junbotong/Dynamic_SMSI_D3_sensitivity_20261013/`（`run_frozen_D3.sh`、`frozen/`、`setup_relax_D3.sh`、`relax_D3/`）。
本地：`run_frozen_D3.sh`、`E_D3_eV.txt`（含各结构来源路径与 CONTCAR SHA-256 前 16 位）、`analyse_D3_frozen.py` → `D3_frozen.md` / `D3_frozen.json`。
第 2 级完成后监控把 `E_D3_relaxed.txt` 取回，同一脚本自动加上第 2 级表。

## 第 1 级结果

| E_int（eV / Ce₂Oᵧ 单元） | PBE+U | PBE+U+D3 |
|---|---|---|
| Ce₂O₃ 团簇 C3a | −4.452 | −5.678 |
| Ce₄O₆ 层 /2 | −1.634 | −2.762 |
| 团簇 − 层（Ce₂O₃） | −2.818 | −2.916 |
| Ce₂O₄ 团簇 C4a | −5.145 | −6.570 |
| Ce₄O₈ 层 /2 | −3.004 | −4.263 |
| 团簇 − 层（Ce₂O₄） | −2.141 | −2.307 |

→ D3 使每个 E_int 负移 1.1–1.4 eV，但团簇与层的差只变 0.1–0.17 eV：**“团簇与 Rh 作用更强”不受 D3 影响。**

| 还原边界（per Ce） | Δμ_O* PBE+U | Δμ_O* +D3 | ΔG，850 °C、1 bar CO₂（Δμ_O = −1.92）PBE+U | +D3 |
|---|---|---|---|---|
| 团簇 Ce₂O₄ → Ce₂O₃ | −2.45 | −2.67 | +0.27 | +0.38 |
| 层 Ce₄O₈ → Ce₄O₆ | −1.77 | −1.99 | −0.07 | +0.04 |
| 层 Ce₄O₈ → Ce₄O₇（界面 O_v） | −1.84 | −2.03 | −0.02 | +0.03 |

→ D3 使两条还原边界都负移约 0.2 eV（还原后的结构 D3 吸引更弱）。团簇在 CO₂ 下保持 Ce₂O₄ 不变；
**层的还原边界从 −1.77 移到 −1.99 eV，跨过 1 bar 纯 CO₂ 的 −1.92 eV**：冻结几何下，1 bar 时层停在 Ce₄O₈ 一侧（+0.04 eV/Ce），
总压 ≤ 10⁻² bar（Δμ_O ≤ −2.07 eV）时仍还原为 Ce₄O₆。差值只有几十 meV/Ce，第 2 级重弛豫决定最终数值。

`analyse_D3_frozen.py` 按本地目录 `ComputeChem\D3_sensitivity_20261013\` 运行（读取相邻的 Stage-4/5 结果 JSON）；仓库里放的是脚本与输出副本。
