# 波浪能既有格点扩建模块

更新时间：2026-07-25

## 1. 实现边界

波浪能是默认关闭的可选技术，不创建第二套空间网格，也不改变
`VRE_TECHS`。启用后，它只在 `data/vre/optimization_points.csv` 已有、
且 `is_land == 0` 的 `grid_uid` 上增加连续容量扩建选项。省份、
`substation_id` 和 `city_337 load_center_id` 均直接复用该 `grid_uid`
在既有路由表中的字段。

因此，“增加波浪能”仍会增加每个可开发格点的容量变量以及逐小时 CF
约束系数，但不会增加空间节点、另建波浪网格或使用远距离最近邻代理。
Base 的 `features.wave_energy=false`，不会生成任何波浪能变量。

## 2. 原始数据与既有格点交集

原始数据位于：

```text
D:\codeenv\pycharmproject\National_RL\wave_energy\wave_grid.nc
```

审计结果：

- 原始数据为 `scenario=10, time=8760, grid=4194`；
- 时间为完整的 2023 年逐小时序列；
- CF 包括 2025 medium，以及 2030/2040/2050 的
  conservative/medium/aggressive；没有 2060；
- 原始总潜力为 `35,898.123 GW`，且十个 CF 情景的潜力完全相同；
- 241 个原始格点的 CF 为插补值。

构建脚本采用最大 `0.02°` 的坐标容差（实际最大差异仅
`4.96e-5°`），与既有格点求交后再限制 `is_land == 0`：

- 保留 1,285 个既有海洋 `grid_uid`，映射一一对应；
- 其中 1,284 个格点潜力大于零；
- 保留原始潜力 `9,798.111 GW`；
- 57 个保留格点的 CF 为插补值；
- 排除 2,909 个不在既有海洋优化格点集合中的原始格点。

排除主要发生在模型空间范围之外的远海。旧版“映射至最近海上风电格点”
会产生最高约 1,524 km 的错误挂接，现已取消。

## 3. 数据构建与字段

```powershell
& 'C:\Users\ZZ\.conda\envs\RL\python.exe' `
  scripts\build_wave_energy_inputs.py
```

输出：

```text
data/wave/wave_sites.csv
data/wave/wave_input_manifest.json
```

关键字段：

- `grid_uid`, `grid_id`：模型既有优化格点标识；
- `wave_source_grid_id`：仅用于从原始 NetCDF 读取对应 CF；
- `province_code`, `substation_id`, `load_center_id`：既有格点路由；
- `capacity_upper_gw_raw`：该交集格点的原始潜力；
- `water_depth_m`, `distance_to_shore_km`, `wave_nc_imputed`：成本和筛选字段。

运行时还需设置：

```powershell
$env:CISPO_WAVE_ROOT = 'D:\codeenv\pycharmproject\National_RL\wave_energy'
```

## 4. 数学形式

对既有海洋格点 \(i\)、省份 \(p\) 和小时 \(t\)：

\[
K_i^{wave}=K_{i,inherited}^{wave}+K_{i,new}^{wave}, \qquad
0\le K_i^{wave}\le f_{potential}K_{i,raw}^{wave},
\]

\[
0\le g_{p,t}^{wave}
\le \sum_{i\in p}CF_{i,t}^{wave}K_i^{wave}.
\]

波浪能出力直接进入已有省级逐小时功率平衡。首版采用保守可靠性设定：

- 不提供向上或向下备用；
- 波浪能出力按 `reserve_requirement_fraction=0.05` 增加备用需求；
- `capacity_credit=0`；
- 不提供同步惯量。

为控制规模，模型不增加“格点 × 小时”的波浪出力变量，也不复制
availability 数组，只增加格点容量变量和省级逐小时出力变量。

## 5. 成本与情景假设

格点 CAPEX 为：

\[
C_i^{capex}=
\left(C_y^{base}+\alpha_yD_i+\beta_yR_i\right)q_{\mathrm{EUR/CNY}}.
\]

参数暂采用 Martinez and Iglesias, *Applied Energy* 364 (2024) 123119
（DOI `10.1016/j.apenergy.2024.123119`）的 CorPower 路径：

| year | base CAPEX (EUR/kW) | FOM/CAPEX | lifetime | depth adder | distance adder |
|---:|---:|---:|---:|---:|---:|
| 2030 | 2,777 | 2.7% | 25 y | 0.66 EUR/kW/m | 2.97 EUR/kW/km |
| 2040 | 2,012 | 2.4% | 30 y | 0.46 EUR/kW/m | 2.52 EUR/kW/km |
| 2050 | 1,731 | 2.4% | 30 y | 0.36 EUR/kW/m | 2.14 EUR/kW/km |

`eur_to_cny=7.8` 和 `potential_fraction=1.0` 均为需要敏感性分析的显式
假设。波浪项目不共享海上风电 `spur/trunk` 容量，避免引入额外共享送出
决策与重复计费。

2030/2040/2050 分别使用对应年份的 medium CF 和成本；2060 明确保持
2050 medium CF 与 2050 成本，待获得 2060 数据后替换。

## 6. 单模块和组合情景

单独启用波浪能：

```text
config/scenarios/wave_energy_medium_v1.json
```

同一个 LP 中同时优化波浪能与灵活负荷：

```text
config/scenarios/wave_energy_medium_v1_flexible_load_v1.json
config/scenarios/wave_energy_medium_v1_flexible_load_comfort_v3.json
```

组合情景是一个解析后的模型案例，两个模块的变量、约束和成本在同一个
目标函数与功率平衡中共同求解。Base、各单模块与组合情景仍是不同案例，
由 `scripts/run_cispo_sensitivity_suite.py` 分别运行和保存结果；这不是
在一个 LP 中混合多套互斥情景概率。

示例：

```powershell
$env:CISPO_WAVE_ROOT = 'D:\codeenv\pycharmproject\National_RL\wave_energy'

& 'C:\Users\ZZ\.conda\envs\RL\python.exe' `
  scripts\run_cispo_2030_full_year.py `
  --scenario-config `
  config/scenarios/wave_energy_medium_v1_flexible_load_v1.json `
  --diagnostic-hours 24 `
  --build-only `
  --skip-full-max-cf `
  --output-dir outputs/wave_flex_24h_build
```

## 7. 规模和本地验证

24 小时 build-only（未求解）：

| case | variables | constraints | nonzeros |
|---|---:|---:|---:|
| Base | 342,343 | 262,201 | 1,771,704 |
| wave medium v1 | 345,992 | 263,810 | 1,794,509 |
| wave + flexible load v1 | 350,456 | 264,647 | 1,825,757 |
| wave + flexible load comfort V3 | 352,688 | 266,879 | 1,830,221 |

静态 8760 小时规模估计：

| case | variables | constraints | nonzeros | estimated memory |
|---|---:|---:|---:|---:|
| Base | 40,912,327 | 67,604,064 | 520,922,832 | 36.00 GB |
| wave medium v1 | 41,186,792 | 67,877,276 | 532,990,308 | 36.47 GB |
| wave + flexible load v1 | 42,816,152 | 68,182,781 | 533,906,823 | 36.91 GB |

与旧版全部 4,187 原始格点直接建模相比，既有海洋格点交集显著减少了
容量变量和 CF 非零系数。波浪/组合预检整体状态均为 `PASS`，每份报告含
72 项记录（67 `PASS`、2 `INFO`、3 个与波浪模块无关的既有 `WARN`）；
完整回归测试通过 62/62。三种案例均通过 24 小时构建门。未启动优化、
744 h、8760 h 或服务器/云端任务。

## 8. 尚需校准

1. 对 `potential_fraction`、最大水深、最大离岸距离和是否排除插补 CF
   做正交敏感性分析；
2. 核验中国本地化安装、运维、汇率和基准成本年；
3. 获取真正分情景的装机潜力；当前源文件只有分情景 CF；
4. 获取 2060 装置性能和成本，替换 2050 保持假设；
5. 先做本地 24 h 求解与硬 QC，再按既有门禁开展 168 h/744 h；
6. 未经单独授权，不启动 8760 h 生产求解或服务器部署。
