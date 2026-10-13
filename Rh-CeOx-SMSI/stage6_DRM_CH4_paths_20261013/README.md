# Stage 6 — DRM 中 CH₄ 转化反应路径：Rh(111) / Ce₂O₃ cluster/Rh(111) / Ce₂O₃ layer/Rh(111)

创建：2026-10-13。状态：**路径方案 + Phase-1 提交版输入已准备（layer = Stage-4 L6）；尚未提交任何计算**。按老师要求，先确定路径并与 Dr. Xiaoyan Li 更新，确认后再上 Vanda 提交。

## 1. 任务来源（导师 2026-10-13 笔记，作为验收标准）

- 先前文献（Gangarajula *et al.*, Appl. Catal. B 343 (2024) 123503）：反应条件下形成 CeOx 部分覆盖 Rh(111)，Rh⁺/Rh⁰ mixture，从而高性能。
- 合作者原位实验：850 °C + CO₂ 与 850 °C + CH₄:CO₂ = 1:1 均形成**双层 Ce₂O₃ SMSI layers**；400 °C + H₂、850 °C + CH₄ 下无或很少 SMSI（CeOx clusters on Rh(111)）。
- 我们的观点：反应条件下催化剂变成双层 Ce₂O₃ layers，是这个 SMSI 导致了高性能；需要从理论上支持实验观测。
- Junbo 已计算得到高温 + CO₂ 环境下应形成 Ce₂O₃ layer（done；本次补充的气相平衡估算见第 2 节）。
- **本次任务**：基于 Ce₂O₃ layer + Rh(111) 和 Ce₂O₃ cluster + Rh(111)，计算 DRM 中 CH₄ conversion reaction pathways；预期 Ce₂O₃ layer + Rh(111) 展现更好的催化性能；参考 Nat. Commun. 文献（s41467-024-48122-6）并进一步查找文献；**最终确定需要计算的反应路径，然后与 Dr. Xiaoyan Li 更新**。

## 2. 850 °C + CO₂ 的 Δμ_O：方法 B（CO₂ ⇌ CO + ½O₂ 气相平衡）评估结果

脚本、数据、图：[`../analysis_20261013/muO_CO2_equilibrium.py`](../analysis_20261013/muO_CO2_equilibrium.py)、
[`muO_CO2_equilibrium.json`](../analysis_20261013/muO_CO2_equilibrium.json)、
[`Fig_muO_850C_CO2_equilibrium.svg`](../analysis_20261013/Fig_muO_850C_CO2_equilibrium.svg)。

- 参考零点与 Stage 5 完全一致：Δμ_O = μ_O − ½E_O₂(DFT)；Δμ_O°(1123.15 K) = −1.256 eV（NIST-JANAF O₂，Reuter–Scheffler 约定）。
  JANAF 复算 CO₂/CO = 1 参考点为 −3.173 eV（Stage 5 记录 −3.176 eV，差 0.003 eV，来自插值）。
- K_p(CO₂ ⇌ CO + ½O₂, 1123 K) = 2.5 × 10⁻⁹（Δ_rG° = +1.917 eV）。

| 850 °C 进气 | 总压 | log₁₀(p_CO₂/p_CO) | Δμ_O (eV/O) |
|---|---|---|---|
| 纯 CO₂ | 1 bar | 5.63 | **−1.92** |
| 纯 CO₂ | 10⁻² bar | 4.97 | −2.07 |
| 纯 CO₂ | 10⁻⁴ bar | 4.30 | −2.22 |
| 10 % CO₂/He | 1 bar | 5.30 | −1.99 |
| 10 % CO₂/He | 10⁻⁴ bar | 3.97 | −2.29 |

结论：P = 10⁻⁴–1 bar、10–100 % CO₂ 的全部情形都落在 **−2.29 ~ −1.92 eV**，即位于 cluster 还原边界（−2.45 eV）与 layer 还原边界（−1.77 eV）之间——**此区间内 Ce₄O₆ layer（Ce₂O₃）相对 Ce₄O₈ 稳定**，与老师“高温 + CO₂ 形成 Ce₂O₃ layer”的结论一致。
该判断只有在 1 bar 下含 ≥ 24 ppm O₂ 杂质（p_O₂ ≥ 2.4 × 10⁻⁵ bar）时才会越过 layer 边界；CO 杂质只会使 Δμ_O 更负（更还原）。
标注：这是理想气相平衡估算（Rh 表面可催化 CO₂/CO/O 交换），实际气室压力/He 比例确定后在图中取对应点即可；CO₂/CO = 1 的 −3.18 eV 保留为示意参考点。

## 3. 参考文献模板：Wang *et al.*, Nat. Commun. 15, 3765 (2024)

"Facilitating the dry reforming of methane with interfacial synergistic catalysis in an Ir@CeO₂₋ₓ catalyst"，https://doi.org/10.1038/s41467-024-48122-6 。
DFT：VASP 5.4.4，PBE + DFT-D3，PAW，CI-NEB；模型 Ir₇/CeO₂₋ₓ(110)，活性中心为 Ir^δ+–O_v–Ce³⁺ 界面。论文给出的路径与能垒（原文数值）：

| 步骤 | 能垒 (eV) |
|---|---|
| CH₄ 吸附于界面 Ir^δ+ | E_ads = −0.03 |
| TS1 CH₄* → CH₃* + H* | 1.12 |
| TS2 CH₃* → CH₂* + H*（RDS） | 1.43 |
| TS3 CH₂* + O* → CH₂O* | 1.03 |
| TS4 CH₂* → CH* + H*（竞争的积碳路径） | 1.56 |
| TS5 CH₂O* → CHO* + H* | 0.63 |
| TS6 CHO* → CO* + H* | 0.73 |
| CO₂ 在 O_v 解离吸附 | E_ads = −1.85，E_a = 0.7 |
| 对照 Ir₇/Al₂O₃ 的 RDS | 2.88 |

可借鉴之处：(i) CH₄ → CH₃ → CH₂ 两步脱氢 + CH₂ 分叉（氧化 vs 继续脱氢）这一最小 DRM 网络；(ii) CO₂ 在 O_v/Ce³⁺ 处解离补氧，构成 Mars–van Krevelen 循环；(iii) 用“RDS 能垒 + CH₂* 分叉选择性”来对比不同界面。

### 3.1 其他文献（2026-10-13 检索；DOI 经 Crossref 核对，[全文]/[摘要] 表示阅读程度）

未找到 CeOx/Rh(111)（含 Ce₂O₃ 覆盖层）上 CH₄/DRM 的 DFT 研究，也未找到含 Rh–CeOx 界面的 DRM DFT——本课题的 Ce₂O₃ layer vs cluster on Rh(111) 路径对比是空白。可直接借鉴的模板：

| 文献 | 模型 / 结论（原文数值） | 用途 |
|---|---|---|
| Lustemberg *et al.*, ACS Catal. 6, 8184 (2016), 10.1021/acscatal.6b02360 [全文] | PBE+U(4.5)，Ni/CeO₂(111) 与 Ni/Ce₂O₃(0001)；CH₄→CH₃+H 0.7–0.8 eV（Ni(111) 引用 0.9–1.1）；C 吸附能作积碳描述符 | 金属/Ce₂O₃ 的 DFT+U 建模；C* 描述符 |
| Liu *et al.*, Angew. Chem. 56, 13041 (2017), 10.1002/anie.201707538 [全文] | CH₄→CH₃+H：Co(0001) 1.07，Cu(111) 1.64，Co/Ce₂O₃(0001) 0.05 eV | “金属 + 还原态 Ce₂O₃”作为 DRM 活性相 |
| Liu *et al.*, Angew. Chem. 55, 7455 (2016), 10.1002/anie.201602489 [摘要] | 有效 CH₄ 活化能垒 Ni(111) 0.9 → Ni/CeO₂₋ₓ(111) 0.15 eV | 干净金属 vs 金属/还原 CeOx 的论证方式 |
| Zuo *et al.*, JACS 138, 13810 (2016), 10.1021/jacs.6b08668 [全文] | 反载型 CeO₂/Cu₂O/Cu(111)：CH₄ 在 Cu₂O/Cu 1.60 eV，界面 Ce⁴⁺/O 0.51 eV | 氧化物岛/金属界面 O 参与 C–H 断裂（对应模型 B） |
| Lustemberg *et al.*, ACS Catal. 11, 10604 (2021), 10.1021/acscatal.1c02154 [全文] | 系统比较 Ni 团簇尺寸与界面位；Brønsted 标度关系偏离 | 位点比较与标度关系论证 |
| Wang, Song, Zhang, Appl. Surf. Sci. 258, 3714 (2012), 10.1016/j.apsusc.2011.12.012 [全文] | Rh(111)（PW91）：CH₄→CH₃ 79.4，CH₃→CH₂ 52.7，CH₂→CH 6.3，CH→C 108.1 kJ/mol | 模型 A 脱氢基准 |
| Díaz López, Comas-Vives, Catal. Sci. Technol. 13, 7162 (2023), 10.1039/d3cy01546g [摘要] | Rh(111) DRM 38 步 DFT+kMC；CO₂ 直接解离，CH*+O* 生成第二个 CO | 模型 A 的完整网络 |
| Kim *et al.*, Nat. Commun. 11, 5649 (2020), 10.1038/s41467-020-19398-1 [全文] | Rh(111) CO₂→CO*+O*：Ea 0.58 eV，ΔE −0.82 eV（RPBE-D3） | R8 在 Rh 上的基准 |
| Kettner *et al.*, J. Phys. Chem. C 120, 26782 (2016), 10.1021/acs.jpcc.6b07431 [摘要] | 实验：CeOx/Rh(111) 反载型模型催化剂真实存在 | B、C 结构模型的实验依据 |

据此在第 4 节补充：各模型 C* 吸附能（积碳描述符，3 个便宜计算）；模型 A 的 CH₂→CH→C 与 CH*+O* 支路按 Rh(111) 文献做基准。项目合同仍为 Ueff = 5 eV、ENCUT 450 eV（文献中 4.5 eV/415 eV 不改变本项目设定）。

## 4. 建议计算的反应路径（待与 Dr. Xiaoyan Li 确认）

**Phase 1 — CH₄ 活化（必做，优先）**

| 编号 | 基元步 | 计算 |
|---|---|---|
| R1 | CH₄(g) → CH₄* | 吸附能 |
| R2 | CH₄* → CH₃* + H* | 反应能 + CI-NEB 能垒 |
| R3 | CH₃* + H* → CH₂* + 2H* | 反应能 + CI-NEB 能垒 |
| D1 | C*（各模型最优位） | 吸附能，积碳描述符（Lustemberg 2016） |

**Phase 2 — DRM 中 CHₓ 的去向与补氧（按参考文献模板）**

| 编号 | 基元步 | 意义 |
|---|---|---|
| R4a | CH₂* → CH* + H* | 继续脱氢 / 积碳路径 |
| R4b | CH₂* + O*（Ce₂O₃ 晶格 O 或 CO₂ 解离 O）→ CH₂O* | C–O 偶联，抑制积碳 |
| R5 | CH₂O* → CHO* + H* | |
| R6 | CHO* → CO* + H* | |
| R7 | CO* → CO(g)；2H* → H₂(g) | 脱附 |
| R8 | CO₂(g) + O_v/界面位 → CO* + O* | 补氧，闭合循环 |

Phase 1 先做完三种模型的 R1–R3，给出“CH₄ 活化能垒 + 能量剖面”对比；Phase 2 在每个模型最优的 Phase-1 位点上继续。

## 5. 模型与活性位

| 模型 | 来源 | 位点 |
|---|---|---|
| A Rh(111) p(4×4) | Stage-5 R4 CONTCAR | Rh top / fcc（基准） |
| B Ce₂O₃ cluster/Rh(111) p(4×4) | Stage-5 C3a（最稳定 cluster）CONTCAR | 周边 Rh（Rh–O–Ce 界面）、cluster 顶 O（O_t）、Ce、远离 cluster 的 Rh |
| C Ce₂O₃ layer (Ce₄O₆)/Rh(111) p(3×3) | Stage-4 L6_Ce4O6_Rh 弛豫 CONTCAR（450 eV, ISPIN 2；即 Stage-5 层 E_int −3.267 eV 所用结构，`parents/`） | 表面 O（O_s）、Ce、Ce–O 对 |

Phase-1 初始构型（`inputs/`，每个模型各取若干起点，取最低者）：

| 体系 | 构型 |
|---|---|
| A1 / A2 / A3 | CH₄ 在 top；CH₃ top + H fcc；CH₂ fcc + 2H fcc |
| B1 / B2 | CH₄ 在周边 Rh；CH₄ 在 Ce |
| B3 / B4 / B5 / B6 | CH₃ 周边 Rh + H 在 O_t；CH₃ 周边 Rh + H fcc；CH₃ 在 Ce + H 在 O_t；CH₃ 远端 Rh + H fcc |
| B7 / B8 | CH₂ 周边 fcc + H 在 O_t + H fcc；CH₂ 周边 fcc + 2H fcc |
| C1 / C2 | CH₄ 在 Ce；CH₄ 在 O_s |
| C3 / C4 | CH₃ 在 Ce + H 在 O_s；CH₃ 在 O_s（甲氧基）+ H 在 O_s |
| C5 / C6 | CH₂ 在 Ce + 2H 在 O_s；CH₂ 在 O_s + 2H 在 O_s |
| A0 / B0 / C0 | 各模型在同一 c 下的干净参考 |
| G_CH₄, G_H₂, G_CO, G_CO₂, G_H₂O | 15 Å 盒子气相参考 |

能量定义：ΔE(R2) = E(CH₃*+H*) − E(CH₄*)；E_ads(CH₄) = E(CH₄*) − E(slab) − E(CH₄,g)；
相对 CH₄(g) 的能量剖面统一以 E(slab) + E(CH₄,g) 为零点。

## 6. 计算合同（与 Stage 5 相同 + 项目规则）

VASP 6.3.2，PAW PBE.54（另加 C 08Apr2002、H 15Jun2001）；PBE+U，Ueff(Ce 4f) = 5 eV；ENCUT 450 eV；ISPIN = 2，不写 MAGMOM；
LREAL .FALSE.；IDIPOL 3、弛豫时 LDIPOL off；bottom Rh 平面 z = 0，最高原子上方 ≥ 15 Å 真空，同一模型（含干净参考）用同一 c；
底两层 Rh 固定。每个 slab 作业三段：A 自旋单点（ALGO All）→ B 弛豫（IBRION 2，EDIFFG −0.02，ISMEAR 1/SIGMA 0.10）→
C 终态单点（ISMEAR 0/SIGMA 0.05，用于能量比较）。k 点：4×4 用 Γ 3×3×1，3×3 用 Γ 4×4×1。PBS 72 h，项目 CFP04-CF-046。
CI-NEB（VTST 已编译进 `vasp_632_vtst_solpp_beef_std`）：5–7 个 image，IMAGES/SPRING −5，EDIFFG −0.05 后对 TS 做 −0.02 精修与频率验证（单一虚频）。

## 7. 工作量估计

| 阶段 | 结构弛豫 | CI-NEB |
|---|---|---|
| Phase 1 | 3 参考 + 17 吸附态 + 5 气相 = 25 | 每模型 R2、R3 各 1 条（cluster 周边/顶位各 1）≈ 7–8 条 |
| Phase 2 | ≈ 30 中间态 | 5 步 × 3 模型 ≈ 15 条 |

## 8. 与 Dr. Xiaoyan Li 更新时需确认的事项

1. 路径范围：先做 Phase 1（R1–R3）给出初步对比，再按第 4 节做 Phase 2 的 CH₂ 分叉 + CO₂ 补氧，是否同意？
2. Ce₂O₃ layer 模型：沿用 Stage 5 比较所用的 Ce₄O₆/Rh(111) p(3×3)（层上只有一个 Ce 平面）；实验描述为“双层 Ce₂O₃”，是否需要另建两个 Ce 平面的 Ce₈O₁₂/Rh(111) 双层模型？
3. 范德华修正：CH₄ 物理吸附与参考文献均用 DFT-D3；当前项目合同无 IVDW。是否在 Stage 6 全体系统一加 D3（`build_stage6.py --d3`）？
4. Layer 上 R4b 使用 Ce₂O₃ 晶格 O（产生 O_v，再由 CO₂ 在 R8 补回），按参考文献的 MvK 循环处理，是否同意？
5. Layer 边界位：Ce₄O₆/Rh(111) p(3×3) 把 Rh 完全盖住，CH₄ 只能在 Ce/O_s 上活化；文献中“金属/Ce₂O₃”低能垒（Co/Ce₂O₃ 0.05 eV、Ni/CeO₂₋ₓ 0.15 eV）都出现在金属–氧化物界面。
   是否加一个 layer 条带模型（Ce₂O₃ 条带 + 一排裸露 Rh，即 layer 的 Rh–Ce₂O₃ 边界）作为模型 C′，与 cluster 周边位（B）对等比较？

## 9. 文件与复现

- `build_stage6.py`：生成 Phase-1 全部输入（POSCAR、INCAR_stageA/B/C、KPOINTS、POTCAR.spec、job.pbs、MANIFEST.sha256、BUILD_REPORT.txt）。
  `python build_stage6.py [--d3]`；三个父结构：A = Stage-5 R4、B = Stage-5 C3a、C = `parents/CONTCAR_L6_Ce4O6_Rh_stage4`（2026-10-13 从 Vanda
  `/scratch/junbotong/Dynamic_SMSI_stage4_Ce4Ox_layers_20260928/inputs/L6_Ce4O6_Rh/CONTCAR` 取回）。
- `inputs/`：**提交版**（2026-10-13 用 L6 重建，替换此前的 round-1 30a 预览版）；所有文件 LF 行尾，`MANIFEST.sha256` 与之对应。
- 所有坐标都是初始猜测，不是结果。

## 10. 2026-10-13 本地复核（ComputeChem 会话）

- **方法 B 数值复核：**JANAF 1100/1200 K 插值 Δ_fG°(CO₂) −395.73、Δ_fG°(CO) −211.09 kJ/mol → Δ_rG° = 184.6 kJ/mol = 1.914 eV，
  K_p = 2.6 × 10⁻⁹；1 bar 纯 CO₂：p_CO = 2.4 × 10⁻⁶ bar、log₁₀(p_CO₂/p_CO) = 5.62、Δμ_O = −1.92 eV，与第 2 节一致。
  O₂ 杂质是唯一能把点推过 layer 边界（−1.77 eV）的因素：1 bar 下 10 ppm O₂ 给 −1.81 eV，24 ppm 到边界；向合作者确认 CO₂ 纯度与气室压力即可定点。
- **Layer 父结构改为 Stage-4 L6**（老师笔记中 “done” 的 layer 结论来自 L6 → Stage-5 E_int −3.267 eV），不再用 Stage-3 S1_31 或 round-1 30a。
- **L6 的结构是一个 Ce 平面：**界面 2 O（z 8.58 Å）– 4 Ce（9.56–9.69 Å）– 表面 4 O（10.02–10.36 Å），即 O–Ce–O 三原子层；
  完整 Ce₂O₃(0001) 双层（两个 Ce 平面，Ce₈O₁₂/Rh p(3×3)）尚未计算 → 第 8 节第 2 条需老师定。
- **INCAR 修正：**MAXMIX 40 只留在 stage A 单点；Stage-5 C4a 在弛豫中跨离子步保留混合历史导致 BRMIX 发散（2026-10-06），B/C 段不再写。
- **Windows 行尾：**生成脚本统一写 LF（CRLF 的 job.pbs 会被 bash 拒绝），MANIFEST 按 LF 内容计算。
- Vanda 上仍有一个 Stage-3 遗留的挂起作业 1403405（sp_S1_11a，状态 H），与 Stage 6 无关。
