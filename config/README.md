# 配置、参数与情景接口

2026-10-02 当前覆盖：运行中的 Base 使用 `optimization_numeric_dac_by_year_v9.json`。下一轮优先 `case3_thermal_ev_v5` 独立 2030→2060；旧 V5 overlay 的 parent ID 仍是修复前 Base，不能直接叠加 V9 或绕过身份校验。隔离试验显式派生 parent、保留全部物理 overrides；正式组合尚待资格验证。详见 [当前执行计划](../SCENARIO_EXECUTION_PLAN_20261002.md)。下文早期默认/V4 口径是历史接口说明，不能覆盖本条。

2026-09-05 当前研究情景覆盖：`base`、`case1_thermal_v5`（冷热）、`case2_ev_v5`（EV）、
`case3_thermal_ev_v5`（冷热+EV）。三者保持同一原始需求与 Base 容量充裕度口径，采用可选签约与分离 EV 服务池。
精确约束、接口与尚未通过的无 Crossover 全国数值门禁见 [FLEXIBLE_PORTFOLIOS_V5_CONTRACT.md](FLEXIBLE_PORTFOLIOS_V5_CONTRACT.md)。
下文 V4/V5 两情景说明属于历史合同，不再定义当前论文主比较；旧配置保留用于复核。

## 1. 运行时权威层级

1. `optimization_2030.json` 定义模型边界、财务、安全、网络、水电和 Base 开关；
2. `scenarios/*.json` 仅保存对 Base 的最小覆盖；其原文件与 SHA256 写入输出 manifest；
3. `data/` 中 `model_input_files.json` 所列运行时表提供容量边界、成本、资源、负荷和网络数据。

`technology_parameters.json`、`capacity_bounds_v0719.json` 与
`model_data_config.json` 仅服务数据构建或证据追踪，不能替代运行时表。
`m2_model_boundary_audit_v1.json` 是保留的 2026-07-28 历史快照；当前统一口径由
`release_contract_v0729.json` 与 `scripts/audit_release_contract.py` 审计。

## 2. Base 与可运行情景

`base` 是当前唯一供给侧 Base。它启用陆上风、海上风、集中式/分布式光伏和波浪能，
灵活负荷关闭。波浪能使用既有 marine `grid_uid`，运行前必须提供外部小时波浪 CF：

```powershell
$env:CISPO_WAVE_ROOT = 'D:\codeenv\pycharmproject\National_RL\wave_energy'
```

`scenario_catalog.json` 是代码能力清单，不是论文主情景清单。`implemented` 仅表示代码和
输入合同已闭合、可以运行工程门禁；一次求解只会加载命令行指定的一个 overlay。当前
论文主分析只保留两个身份：

- `base`：非灵活性基准；
- `flexible_load_comfort_v4_v1g`：数据支持的连续冷热状态与 EV V1G 中心反事实。

其余文件按用途隔离：

- `flexible_load_comfort_v4_v1g_effective_peak_sensitivity`：仅检验需求柔性是否获得容量充裕信用；
- `flexible_load_comfort_v4_v2g_sensitivity`：同一 V4 车群的 V2G 敏感性；
- `hydro_aggregate_flex_v1`：省级未识别常规水电参与调节的敏感性；
- 三个 `phs_power_energy_separated_*_v1`：抽蓄功率/能量容量分离的低/中/高成本敏感性；
- `flexible_load_comfort_v3_v2g_5pct`：已由 V4 替代，只保留作历史回归；
- `phs_power_energy_separated_template_v1`：不可运行模板。

因此 `scenario=flexible_load_comfort_v4_v1g` 在四个规划年重复出现，表示同一个中心
overlay 被 2030、2040、2050、2060 串行复用，并不表示同时叠加了多个 scenario。

V4 168 h 工程门禁示例：

```bash
python scripts/run_cispo_2030_full_year.py \
  --scenario-config config/scenarios/flexible_load_comfort_v4_v1g.json \
  --planning-year 2030 \
  --horizon diagnostic_168h \
  --output-dir outputs/flexible_load_v4_v1g_2030_168h
```

`planned_not_runnable` 中的 PHS template 只保存公式与证据接口，不含可直接求解的数值参数。
历史 V1、state-V2、第一代 V2G、波浪单模块和旧组合情景已从 catalog 删除；既有输出和
Git 历史保留，但不得作为当前情景入口或与新 Base 直接比较。

## 3. 柔性、水电与抽蓄边界

灵活性使用不可变负荷分量：

```text
demand_gw = base_residual_gw + heating_gw + cooling_gw + ev_gw
```

Base 不创建柔性变量。V3 仅作为旧工程对照。V4 使用现有省级逐小时冷热/EV 分解：

- 冷热采用全年连续的非负服务库存；`+/-1 C` BAIT 包络限制可调功率，月末回到零；
- EV 将既有 EV 基线拆成固定与柔性服务，柔性份额为 25%，V1G/V2G 共用同一车群；
- V1G/V2G 满足逐小时驾驶能量提取、接入功率和车队能量容量；没有观测支持的出发
  SOC 下限固定为零，不伪造出行链约束；
- V2G 只作为敏感性，不并入 Base。

柔性会改变小时有效负荷，因而进入功率平衡、备用、惯量和负荷中心闭合；规划容量裕度
仍采用 Base 峰值，柔性不获得备用或容量信用。V4 中的
`connected_vehicle_fraction=1` 是对已选柔性车群的归一化，不代表全国车辆 100% 接桩。
完整参数来源、公式与适用边界见 `FLEXIBLE_LOAD_V4_CALIBRATION_CONTRACT.md`。

Base 常规水电按 380 GW 口径闭合：可识别电站保留河网/水库表示，差额省级汇总容量采用
月度可用率、零备用/惯量/容量信用。`hydro_aggregate_flex_v1` 才允许该差额提供调节。
Base 抽蓄仍为固定 8 h；功率/能量分离只在独立 PHS 敏感性中启用。

## 4. 结果与运行规则

每个情景必须使用独立输出根。每年仅在 `OPTIMAL + solution_qc=PASS` 后写入可传递的
`planning_state/`；`scenario_manifest.json`、`model_config_snapshot.json`、输入/输出
manifest 共同锁定身份。24 h、168 h、744 h 是工程门禁；仅完整 8760 h 且 manifest 闭合的
结果可用于科学解释。

V4 的构建、来源计数和运行时输入分别由
`scripts/build_flexible_load_v4_inputs.py`、
`flexible_load_v4_source_count_qa.csv` 与
`data/flexibility/flexible_load_v4.manifest.json` 锁定。截断时域结果只用于工程验证：
V4 年化启用成本与所选小时运行成本必须分列，不能直接解释成全年净收益。


## 2026-10-12 当前共识入口与历史口径更正

权威依据：`RESEARCH_DESIGN_CONSENSUS_20261012.md` 全文与 `AGENTS.md` 2026-10-12 两节；冲突以共识为准。下列引用逐字摘录共识，不重新计算数值。历史条目保留，仅供追溯，不构成新的执行授权。


当前研究与执行以 `RESEARCH_DESIGN_CONSENSUS_20261012.md` 和 `AGENTS.md` 2026-10-12 两节为准。旧条目中的 V4 主情景、case1/case2 后补、Late-entry 待定、Stage B/basic solution 强制要求、严格 QC 否决导出等均不再定义当前任务。

> ## 3. 求解、验收与数据保全
>
> - 求解：Stage A，即 Barrier、Crossover=0、BarConvTol=1e-4、NumericFocus=2、48 线程，不执行 Stage B。case3 是否沿用 Base 的 Presolve=2/Aggregate=1，取决于夜间数值实验（第 6 节）。
> - relative_v1：功率平衡、成本闭合、双向流（额外损耗 ≤ 全年负荷的 1e-4）、水库（暂缓）四项已实现。**扩展（2026-10-12 决定，case3 启动前实现）：** 其余所有以 GW/GWh 计的物理残差检查，包括冷热和 EV 库存、V2G、信用上界、波浪、储能，判据改为 max(严格容差, 1e-3 GW 或 GWh)。理由是 Base 中柔性检查恒为 0，从未被内点解检验过；严格的 1e-5 GWh 低于内点解的正常残差量级（2030 功率平衡最大残差 0.19 MW）。
> - **验收只是参考标签：** 任何口径的结论都不导致数据被删除、覆盖或放弃；解是否采用，由作者与决策层人工决定（AGENTS.md 2026-10-12 第 6 条）。
> ## 6. 执行顺序与当前状态
>
> 1. **已完成：** Base 2030/2040/2050 正式验收（`supplementary_materials/reviews/base_acceptance_relative_v1_20261012/`）；三年结果已备份到 T550（262 文件，15.96 GB，SHA 全部核验）。
> 2. **运行中：** Base 2060，Job 5124127，release `20261012_base2060_v9a12_t48_m750_tol1e4_v1`，源码 680a5c4，不筛选。
> 3. **今晚：** case3 柔性块解质量的夜间实验（`claude_workspace/tasks/TASK_case3_flex_numerics_overnight_20261012.md`），结论决定 case3 的生产求解参数。
> 4. **下一步（Claude 写任务书，Codex 实现）：**
>    - 筛选生产化：profile、margin 参数、`--state-in` 支持；
>    - 定价证书脚本；
>    - relative_v1 扩展；
>    - R1 交接规则产品化，把 2060 的一次性脚本整理为可复用工具；
>    - 与冻结 Base 2030 release 的身份门禁、24h 门禁；
>    - held 提交。
> 5. **随后：** case3 2030 与 `_nocredit` 2030 并行提交。C 2050 在 `--state-in` 筛选就绪后提交，可与 case3 2030 并行。case3 2040 在 case3 2030 完成后提交。框架 B 任务书在 case3 2030 提交后撰写。
> 6. **云端占用：** 最多同时 4 个 64 CPU/750G 节点（Base 2060、case3 2030、`_nocredit` 2030、C 2050）。每个作业均先 held 提交，作者放行后才运行。
