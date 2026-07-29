# 配置、参数与情景接口

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

`scenario_catalog.json` 是当前情景入口清单。`implemented` 表示代码和输入合同已闭合、
可以运行工程门禁，并不表示已成为论文 Base 或已经完成全国全年校准。当前实现包括：

- `flexible_load_comfort_v3_v2g_5pct`：保留的历史 V3 工程对照；
- `flexible_load_comfort_v4_v1g`：数据支持的连续冷热状态与 EV V1G 中心情景；
- `flexible_load_comfort_v4_v2g_sensitivity`：同一 V4 车群的 V2G 敏感性；
- `hydro_aggregate_flex_v1`：省级未识别常规水电参与调节的敏感性；
- 三个 `phs_power_energy_separated_*_v1`：抽蓄功率/能量容量分离的成本敏感性。

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
