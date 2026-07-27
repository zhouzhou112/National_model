# 负荷分解与唯一柔性情景的输入来源

## 1. 当前逐时负荷合同

`data/load/hourly_load_2025_2060.csv.gz` 是唯一逐时负荷输入，覆盖 31 省、
2025/2030/2040/2050/2060 和每年 8,760 h。每一行必须满足：

```text
demand_gw = base_residual_gw + heating_gw + cooling_gw + ev_gw
```

加载器逐时硬校验该闭合。它来自 `Power_curve_V2`：冷热由 BAIT/HDD/CDD 与未来
`thermal_multiplier` 构建，EV 由未来车队、每车日用电和 `ev_hour_weight` 构建；
`ev_hour_weight` 只是无序充电基线形状，不能解释为车辆接入率。

## 2. Base 与唯一柔性覆盖

Base 直接使用 `demand_gw`，不创建柔性变量。唯一柔性入口是
`config/scenarios/flexible_load_comfort_v3_v2g_5pct.json`；它继承含波浪能的 Base，
并以 `comfort_envelope_v3` 替换需求侧运行。

- 冷热包络来自 `Power_curve_V2` 原始公式的 `+/-1 C` 舒适区间；供暖/制冷等效状态分别
  使用 4/5 h 时长、0.94/0.92 小时保留率，每个北京时间自然日终端状态归零；
- EV V1G 对无序充电基线施加因果待充队列和 12 h 聚合服务期限；
- V2G 是 EV 服务上的增量日内虚拟储能，必须先充后放、日末回零，功率上限为各省每日
  基线 EV 峰值的 5%，并与 V1G 共用电网充电功率上限；
- 有效负荷进入逐时平衡、备用、惯量和年度城市负荷中心闭合；容量裕度仍按未柔性化的
  Base 峰值计算，柔性不获得容量或备用信用。

V3+V2G 的热状态、车辆连接率、可用电池容量、驾驶耗能、出发 SOC 和响应成本尚未由
观测数据校准。因此它是唯一保留的需求柔性敏感性，不得称为经验校准 Base。

## 3. 版本与可复现性

历史 V1、state-V2 和第一代 V2G 配置已从可运行 catalog 删除；既有结果及 Git 历史仍
保留以追溯旧实验，但未来更新必须只修改 V3+V2G 配置和相应 QC。每次运行均须在
`scenario_manifest.json`、`model_config_snapshot.json`、`input_manifest.csv` 中记录解析后
参数和原始 JSON SHA256；跨年份 `--resume` 还会验证 scenario 与 planning-state 身份。
