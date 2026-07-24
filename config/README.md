# 配置、参数与情景接口

## 1. 运行时权威层级

模型参数不是全部堆在一个 JSON 中，而是按职责分为三层：

1. `optimization_2030.json`：模型边界、求解器、财务、安全、网络、水电和可选模块的基准控制参数；
2. `scenarios/*.json`：只保存相对基准的最小覆盖项，通过 `--scenario-config` 合并，原始文件和 SHA256 会写入 case；
3. `data/` 下 `model_input_files.json` 列出的运行时表：省年容量边界、技术成本、燃料成本、排放、负荷、资源和网络参数。

`technology_parameters.json`、`capacity_bounds_v0719.json` 和 `model_data_config.json` 主要服务于数据包构建或证据追踪，不能替代运行时表。生产 case 应先运行 `scripts/audit_model_parameters.py`，确认当前数据根目录下的实际数值。

## 2. 情景调用

Base（不启用柔性负荷）：

```bash
python scripts/run_cispo_2030_full_year.py \
  --planning-year 2030 \
  --horizon full_year \
  --output-dir outputs/base_2030
```

冷热 + EV V1G：

```bash
python scripts/run_cispo_2030_full_year.py \
  --scenario-config config/scenarios/flexible_load_v1.json \
  --planning-year 2030 \
  --horizon full_year \
  --output-dir outputs/flexible_load_v1_2030
```

状态型冷热 + 因果 EV V1G（V2G 关闭）：

```bash
python scripts/run_cispo_2030_full_year.py \
  --scenario-config config/scenarios/flexible_load_state_v2.json \
  --planning-year 2030 \
  --horizon full_year \
  --output-dir outputs/flexible_load_state_v2_2030
```

冷热 + EV V1G + V2G：

```bash
python scripts/run_cispo_2030_full_year.py \
  --scenario-config config/scenarios/flexible_load_v2g_v1.json \
  --planning-year 2030 \
  --horizon full_year \
  --output-dir outputs/flexible_load_v2g_v1_2030
```

四个规划年可向 `run_cispo_planning_sequence.py` 传入同一个 `--scenario-config`。每个规划年的 `model_config_snapshot.json`、`input_manifest.csv` 和 `scenario_manifest.json` 会记录解析后的参数及原始覆盖文件。

## 3. 柔性负荷 V1 的数学边界

输入满足：

`demand_gw = base_residual_gw + heating_gw + cooling_gw + ev_gw`。

Base 不创建任何柔性变量。启用后，冷热负荷使用逐时 `shift_up/shift_down`，每个北京时间自然日严格满足上调电量等于下调电量；下调由原始分量的比例限制，上调由当日分量峰值限制。EV V1G 同样逐日守恒，下调不超过可搬运比例，上调后充电功率不超过“当日平均功率 × 倍率”。

V2G 是叠加在 EV 驾驶能量服务上的增量虚拟储能：按日循环 SOC，显式计入充放电效率和退化吞吐成本。它不获得备用、惯量或规划容量信用。当前规划容量裕度仍使用 Base 峰值，小时备用与惯量约束使用优化后的有效负荷，这是保守的可靠性处理。

当前 V1 是宏观情景模块，不是交通行为模型。`15%` 冷热上下调、`50%` EV 可搬运比例、V2G 参与率等均标记为 `ILLUSTRATIVE_ASSUMPTIONS_REQUIRE_SENSITIVITY`；在作为论文主结论前，必须用建筑热惯性、接入率、车辆电池容量、驾驶耗能和出发 SOC 数据校准。

## 3.1 状态型 `flexible_load_state_v2`

该情景不改变四分量输入。`heating_gw` 和 `cooling_gw` 来自
`Power_curve_V2` 的 BAIT/HDD/CDD 重建；未来年份沿用 2024 非闰年逐时形状并按
`thermal_multiplier` 缩放。每个省和北京时间自然日增加等效热库存：

`state[t] = retention * state[t-1] + eta_charge * shift_up[t] - shift_down[t] / eta_discharge`。

日首库存固定为零，日末回到零；因此不能从未来小时或下一日借用热量。库存损耗会使
优化后的冷热用电高于原基线，QC 检查状态转移、日末归零和损耗方向，不再错误要求
冷热逐日净电量严格相等。该表示仍是省级等效代理，不是建筑温度或 COP 的 RC 模型。

EV 输入由 `Power_curve_V2` 的
`future_nev_stock × ev_kwh_per_vehicle_day × ev_hour_weight` 构成。
其中 `ev_hour_weight` 是无序充电基线形状，不是车辆接桩可用率。V2 将可搬运基线视为
逐时进入的待充服务，增加非负 `ev_v1g_backlog_gwh`；只有先延期形成队列后，后续小时
才可补充充电，并在每日末清零。`maximum_queue_duration_hours` 是聚合队列能量包络，
不是逐车严格充电截止期。

`flexible_load_state_v2` 继续继承 V1 的 `15%` 冷热功率比例、`50%` EV 可搬运比例和
`2 ×` 日均充电功率包络；新增 `4/5 h` 热库存时长、`0.94/0.92` 小时保留率和
`12 h` EV 队列包络。以上均为显式敏感性假设。该情景强制关闭 V2G；在缺少逐时接入率、
可用电池能量和出发服务约束时，配置校验拒绝把状态 V2 与 V2G 同时开启。

## 4. 敏感性分析规则

- 每个敏感性 case 新建一个最小 `scenarios/*.json`，不要复制整份主配置；
- 一次只改变已声明的参数组，`scenario_id` 必须唯一；
- Base 与扩展情景使用同一数据根、天气年和规划状态链；
- 先跑 24h，再跑 168h/744h 工程门禁，最终解释只使用 8760h；
- 比较时同时报告系统成本、容量、发电、弃电、输电、储能、碳、负荷搬运量、峰值变化和约束影子价格；
- 参数来源和未决风险以 `outputs/parameter_audit_*/` 为准。

已实现和待实现情景的机器可读状态见 `scenarios/scenario_catalog.json`。

## 5. 诊断敏感性 suite runner

`scripts/run_cispo_sensitivity_suite.py` 只编排 `scenario_catalog.json` 中 `implemented` 的情景，并为每个情景建立独立的四年状态链。它拒绝 `planned_not_runnable`、拒绝重复 `scenario_id`、校验 catalog 与 scenario 文件身份及 SHA256，并且只接受显式的 `--diagnostic-hours`；全量 8760h 仍必须按昂贵 case 的单独审批与门禁流程运行。

先检查 catalog，不创建输出：

```bash
python scripts/run_cispo_sensitivity_suite.py --list-scenarios
```

生成 Base 与 V1 的 1h 编排 dry-run：

```bash
python scripts/run_cispo_sensitivity_suite.py \
  --scenario base \
  --scenario flexible_load_v1 \
  --diagnostic-hours 1 \
  --output-root outputs/sensitivity_suite_1h_v1 \
  --dry-run
```

实际诊断运行去掉 `--dry-run`。只有完整接受且 catalog、base config、情景列表、情景 SHA256 和诊断时长完全相同的独立情景链才能对同一 suite root 使用 `--resume`；失败或混合目录必须换新的版本化 `--output-root`。每次成功进入 resume 前，旧 suite report 会追加保存到 `sensitivity_suite_history/`，逐情景 wrapper 日志也使用时间标签，不覆盖先前运行证据。suite 输出包括 `sensitivity_suite_report.json`、`sensitivity_suite_index.csv`、逐情景 wrapper 日志和每个情景自身的完整 `sequence_report.json`/科学输出。该 runner 不共享跨情景 `planning_state`，也不授权固定服务器 744h/8760h 或付费云端 8760h。
