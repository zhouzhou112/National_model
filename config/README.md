# 配置、参数与情景接口

## 1. 运行时权威层级

1. `optimization_2030.json` 定义模型边界、财务、安全、网络、水电和 Base 开关；
2. `scenarios/*.json` 仅保存对 Base 的最小覆盖；其原文件与 SHA256 写入输出 manifest；
3. `data/` 中 `model_input_files.json` 所列的运行时表提供容量边界、成本、资源、负荷和网络数据。

`technology_parameters.json`、`capacity_bounds_v0719.json` 与
`model_data_config.json` 仅服务数据构建或证据追踪，不能替代运行时表。

## 2. 仅有的两个可运行情景

`base` 是当前唯一供给侧 Base。它默认启用陆上风、海上风、集中式/分布式光伏和波浪能；
灵活负荷关闭。波浪能使用既有 marine `grid_uid`，因此运行 Base 必须先提供外部小时
波浪 CF：

```powershell
$env:CISPO_WAVE_ROOT = 'D:\codeenv\pycharmproject\National_RL\wave_energy'
```

Base 运行示例：

```bash
python scripts/run_cispo_2030_full_year.py \
  --planning-year 2030 \
  --horizon full_year \
  --output-dir outputs/base_wave_2030
```

当前唯一可运行的柔性情景 `flexible_load_comfort_v3_v2g_5pct` 继承含波浪的 Base，并仅额外开启
`comfort_envelope_v3`：冷热等效状态、12 h 因果 EV V1G 待充队列、日内因果 V2G，后者
功率上限为各省每日基线 EV 峰值的 5%。

```bash
python scripts/run_cispo_2030_full_year.py \
  --scenario-config config/scenarios/flexible_load_comfort_v3_v2g_5pct.json \
  --planning-year 2030 \
  --horizon full_year \
  --output-dir outputs/base_wave_flexible_v3_v2g_5pct_2030
```

历史 V1、state-V2、第一代 V2G、波浪单模块和旧组合情景均已从可运行 catalog 删除；
既有输出和 Git 历史保留，但不得作为当前情景入口或与新 Base 直接比较。

## 3. 柔性与可靠性边界

灵活性使用不可变负荷分量：

```text
demand_gw = base_residual_gw + heating_gw + cooling_gw + ev_gw
```

Base 不创建柔性变量。V3+V2G 情景以 `Power_curve_V2` 的 BAIT/balance-point 公式和
`+/-1 C` 舒适区间形成冷热功率包络；热状态每日归零。EV `ev_hour_weight` 仅表示无序
充电基线，不代表接桩可用率；V1G 采用因果待充队列，V2G 需先充后放、每日零边界，并与
V1G 共用充电功率上限。

柔性会改变小时有效负荷，因而进入功率平衡、备用、惯量和年度负荷中心闭合；规划容量
裕度仍采用 Base 峰值，柔性不获得备用或容量信用。参数仍需建筑热工、车辆连接率、
电池可用量、出发 SOC 和响应成本校准，不能将该情景解释为经验校准 Base。

## 4. 结果与运行规则

每个情景必须使用独立输出根。每年仅在 `OPTIMAL + solution_qc=PASS` 后写入可传递的
`planning_state/`；`scenario_manifest.json`、`model_config_snapshot.json`、输入/输出
manifest 共同锁定身份。24h、168h、744h 是工程门禁；仅完整 8760h 且 manifest 闭合的
结果可用于科学解释。

`flexible_load_comfort_v4_v1g` 与
`flexible_load_comfort_v4_v2g_sensitivity` 已登记为 `planned_not_runnable`。它们采用全年连续
热服务状态、带舒适债界的内生 `Kflex`，以及同一 EV 车群的接入/驾驶/出发 SOC 合同；在
`data/flexibility/` 的五张校准输入通过闭合与 provenance 检查前，加载器会拒绝构建。完整字段、
方程和校准门禁见 `config/FLEXIBLE_LOAD_V4_CALIBRATION_CONTRACT.md`。
