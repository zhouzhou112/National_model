# CISPO 全模型系统审计与跨年求解完善记录（2026-07-18）

## 1. 审计结论

本轮以 Git implementation commit `2a0ee99` 为模型基线，对输入合同、容量扩建、逐小时运行、数值尺度、跨年状态、结果输出和服务器门槛进行了逐模块检查。当前代码可形成以下严格链条：

```text
2025 input boundary
  -> 2030 full-year solve -> checksummed capacity cohorts
  -> 2040 full-year solve -> checksummed capacity cohorts
  -> 2050 full-year solve -> checksummed capacity cohorts
  -> 2060 full-year solve
```

每个规划年仍是一个完整的 8760 小时连续 LP；跨年路径是逐期、近视型（myopic sequential）扩建，不是四个年份联合的 perfect-foresight LP。744h 和其他截断时段只允许作为工程门槛，不得解释为规划结果。

本轮发现并修正了会影响模型合理性或求解性的实质问题：

1. 建立可校验的跨年容量 cohort 状态，不再让 2040/2050/2060 丢失先前年份投资。
2. PHS 不再采用零装机下界和无上限扩建：接入 GHT 2026 省级项目数据，2030 全国下界/上界分别为 65.94/249.191 GW，2040 年及以后项目池上界为 514.755 GW。
3. 删除冗余变量并采用数学等价的稀疏表达：单一绝对爬坡变量、聚合储能备用、表达式化水库发电和水电惯量、直接目标函数运行成本。
4. 补齐储能上备用的前一时刻 SOC 约束；避免空储能仅凭功率容量虚报上备用。
5. 年化 CapEx 按 CISPO 公式统一作用于当期总装机，而不是部分技术只对当期新增容量计费。
6. 建立最小输入合同，只传输模型实际读取的 28 张表；代码包只包含 Git tracked files，避免把无关结果和用户未跟踪目录发往服务器。
7. 增加完整结果摘要、压缩逐小时结果、可复核 manifest 和不依赖绘图库的 SVG 快速图。

## 2. 模型边界和变量尺度

| 模块 | 空间尺度 | 时间尺度 | 核心决策/状态 | 当前结论 |
|---|---|---|---|---|
| VRE | 0.25° technology-site | 8760h | site capacity；省级 technology-hour dispatch | 保留 site CF 稀疏聚合，避免将同一 CF 系数复制到多个约束 |
| Thermal/nuclear | 31 省 × 11 技术 | 8760h | capacity、continuous online/startup/shutdown、gross output | 是 relaxed RUC，不是整数 UC；公式结构保留 |
| Run-of-river | 站点 CF 加权到省级 | 8760h | station capacity；省级 ROR dispatch | 各站 `CF * capacity` 汇总成省级可用出力，省级变量决定弃水 |
| Reservoir hydro | 620 个水库站 | 8760h | turbine flow、spill、volume、station capacity | 站点级调度；146 个核心梯级站、124 条边传播上游 release |
| Storage | 31 省 × battery/PHS | 8760h | power capacity、charge/discharge、SOC、reserve | PHS 是省级 8h 储能，不复现 PHS 水库配对 |
| Transmission | 411 条省间走廊 | 8760h | capacity、双向 flow | transportation model，不是 AC power flow |
| Load-center network | 278 中心、517 条省内边 | 年度 | capacity、annual energy flow | 避免 center-hour 变量；保持省级逐小时平衡为主约束 |
| Carbon/CCS/DAC | 省级源 + 点级 sink | 年度 | capture、shipping、DAC capacity/removal | 严格年度碳平衡和 sink 上限 |

单位保持：功率/容量 `GW`，电量 `GWh`，水流输入 `m3/s`，水库物理体积 `m3`，内部水流/体积变量分别缩放为 `10^3 m3/s` 和 `10^6 m3`，目标函数为 `million CNY/year`。

## 3. 数学等价稀疏化

### 3.1 爬坡成本

原来的 `ramp_up` 与 `ramp_down` 两组变量改为一组 `ramp_magnitude`：

```math
r_{g,k,t} \ge P_{g,k,t}-P_{g,k,t-1},\qquad
r_{g,k,t} \ge P_{g,k,t-1}-P_{g,k,t}.
```

由于爬坡成本系数严格为正，最优时 `r = |P_t-P_{t-1}|`，因此该改写与原目标函数严格等价，并减少一组 `province × technology × hour` 变量。

### 3.2 储能备用

四组充/放电备用分量投影为 `R_up` 和 `R_down` 两组聚合变量。除功率约束外，必须保留前一时刻 SOC 能量约束：

```math
R^{up}_{t} \le charge_t + P\eta_d-discharge_t,
```

```math
R^{up}_{t} \le P\eta_d,
```

```math
R^{up}_{t} \le charge_t + SOC_{t-1}\eta_d-discharge_t.
```

下备用相应受充电功率余量和剩余能量空间约束。本轮最后一条是在系统自检中发现并补齐的关键约束。

### 3.3 水库发电与运行成本

`reservoir_generation` 改为由 turbine flow 直接构造的线性表达式；`hydro_inertia` 也改为容量线性表达式。删除年度运行成本会计等式，将运行成本线性式直接并入目标函数。它们不改变可行域或目标值，但减少辅助变量、等式和重复密集系数。

## 4. 跨年状态合同

状态目录固定包含：

- `planning_state/state_metadata.json`
- `planning_state/capacity_cohorts.csv.gz`

cohort 主键包含 `asset_class`、稳定 `asset_id`、`technology`、`build_year`、`retire_year`、`capacity_delta`、`unit` 和 `action`。下一年只读取 `planning_year < retire_year` 的 cohort，并核验：

- 上一年年份必须等于当前 `boundary_year`；
- cohort 文件 SHA256 必须与 metadata 一致；
- 单位、资产 ID 和重复键必须合法；
- 继承下界不得超过 VRE/hydro/PHS 的外生潜力上界；
- 只有 `OPTIMAL + full_year + solution_qc PASS` 才允许产生下一期状态。

传递资产包括 VRE、thermal/nuclear 新建与 CCS retrofit、hydro、battery/PHS、interprovincial transmission、intra-load-center transmission、DAC、VRE/hydro spur 和 trunk。模型新增资产按技术寿命退休；现有 VRE 因缺少机组年龄继续作为外生下界，现有水电沿用“运行至 2060”论文假设。

热电 retrofit 与外生退役路径缺少 plant-level 年龄匹配，因此代码采用 fail-fast：若累计 retrofit 调整使未来外生下界为负，停止该规划年而不是静默裁剪。该限制需要未来 plant-level 数据才能严格消除。

## 5. 输入精简和 PHS

`config/model_input_files.json` 是唯一最小表输入合同。模型读取 CSV 时显式指定 `usecols`，不再读取来源说明、早期比较字段和绘图辅助字段。Zarr CF、hydrology NetCDF 与原始 GRFR 仍按独立大文件路径管理。

PHS 使用 `phs_ght2026_8h_clean.csv` 生成 `storage/phs_capacity_bounds_by_province_year.csv`：

| Planning year | National floor (GW) | National upper (GW) |
|---:|---:|---:|
| 2030 | 65.940 | 249.191 |
| 2040 | 65.940 | 514.755 |
| 2050 | 65.940 | 514.755 |
| 2060 | 65.940 | 514.755 |

现有 floor 来自 `is_existing_2025`，项目上界来自 `available_from_year <= planning_year`。PHS 仍按用户确定的省级储能模式建模，不引入 open-loop/closed-loop 水力配对。

## 6. 输出与可视化

每个成功求解目录至少包含：

- 容量：`vre_capacity.csv`、`thermal_nuclear_capacity.csv`、`hydro_capacity.csv`、`storage_capacity.csv`、`transmission_capacity.csv`；
- 运行：`hourly_province_balance.csv.gz`、`thermal_dispatch.npz`、`vre_dispatch.npz`、`storage_dispatch.npz`、`reservoir_dispatch.npz`、`transmission_flows.npz`；
- 摘要：`annual_capacity_by_technology.csv`、`annual_generation_by_technology.csv`、`annual_storage_operation_by_technology.csv`、`hourly_national_balance.csv.gz`、`monthly_energy_by_technology.csv`、`annual_summary.json`；
- 碳和成本：`annual_carbon_ccs.json`、`co2_source_sink_flows.csv`、`cost_components.csv`；
- 质量：`build_report.json`、`solve_report.json`、`solution_qc.json`、`result_manifest.json`；
- 快速图：`visualizations/capacity_by_technology.svg`、`generation_by_technology.svg`、`national_dispatch_first_week.svg`。

`result_manifest.json` 记录 Git commit、文件大小和 SHA256。跨年汇总额外生成 `sequence_annual_summary.csv`、容量/发电 trajectory 表和 `sequence_capacity_trajectory.svg`。

## 7. 本地验证证据

- AST：38 个 Python 文件解析通过。
- Unit tests：24/24 PASS；包含真实 solution arrays 到 checksummed capacity cohorts 的映射测试。
- Data package smoke：124/124 PASS。
- 2030 full-year preflight：PASS，0 hard fail；粗略规模 44,090,772 variables、67,603,314 constraints、853,505,952 nonzeros、46.62 GiB 模型内存估计。
- 24h 最终诊断：349,962 variables、260,973 constraints、1,827,245 nonzeros；CPU barrier + crossover `OPTIMAL`，Gurobi 58.79 s，peak RSS 0.698 GiB，`solution_qc PASS`。
- 24h 最大功率平衡残差 `3.90e-11 GW`，目标分解残差 `9.31e-10 million CNY`。
- 结果输出：36 个 manifest 文件（含 storage summary）和 3 个 SVG 均通过结构/数值检查。
- 2040 非空状态诊断：1h 模型 `OPTIMAL/QC PASS`；北京 battery 继承 2.5 GW，河北 PHS 继承 1.0 GW，并准确进入容量下界。
- 2030/2040 full-year preflight 均 PASS；四年 sequence `--dry-run` 形成连续正确的 state 路径。

## 8. 尚未消除的限制和停止规则

| 事项 | 类型 | 当前处理/停止规则 |
|---|---|---|
| 744h 新版 CPU 门槛 | server verification | 服务器 SSH 在 KEX 阶段关闭，旧 PID/结果当前无法验证；不得声称已通过 |
| 8760 实际 build/solve | server verification | 只有新版 744h `OPTIMAL + QC PASS` 后才启动；本地 17 GiB RAM 不满足 64 GiB gate |
| 4 条低相关时滞边 | data WARN | 保留论文 cross-correlation 结果并显式 WARN，不擅自改时滞 |
| 18 条达到 168h 上限的边 | data WARN | 表明最优相关峰位于搜索边界，需扩展水文窗口/人工复核；当前仍按论文方法使用 |
| P30 | data proxy | 当前是 2019 单年 monthly P30 proxy，不是 1980-2019 climatological P30 |
| CSP | missing source | 固定禁用，直到有 site potential 和 hourly profile |
| Thermal `f_on` | missing source | 燃料成本按 gross generation 计；不伪造 online fuel 参数 |
| VRE weather / hydrology | scenario limitation | 各规划年复用 2023 VRE weather 与 2019 hydrology，不能解释为气候年代变化 |
| PHS hydraulic pairing | model scope | 仅省级 8h storage，不复现 open/closed-loop 水库水量耦合 |
| RUC | formulation scope | 连续 capacity relaxation，不是整数 UC |
| Intra-grid loss | model proxy | 当前为 0；50% design utilization 和两条超 1000 km proxy edge 继续显式 WARN |
| Sequential foresight | planning assumption | 逐期 myopic，不是四期联合最优；论文结论中必须明确 |

GPU-PDHG 的已验证 24h 对比慢于 CPU barrier（超过 600 s 仍未完成），因此标准 CPU barrier 继续作为生产默认；安装 GPU-enabled Gurobi 并不等于该 LP 会获得 GPU 加速收益。

## 9. 服务器下一步

已生成并本地复核的最小传输包：

| Archive | Bytes | SHA256 |
|---|---:|---|
| `national_model_code.tar.gz` | 283,416 | `1311f3ccfd53b26248e37c13370016a6b5e6165f717d1bde0e79c21d3cd73a4d` |
| `model_ready_data.tar.gz` | 49,131,551 | `502a60e58da959bfa6e5c3ba2ea83a8d39c3aade212231e5c6ecc42db6a9eb17` |
| `hydro_timeseries.tar.gz` | 24,777,505 | `573d1285eb4787a3058bff8c25b382a5df6630441de2c5e5b8d58095fbfd70f5` |

该 bundle 从 Git HEAD `dafeb24` 生成。代码包仅含 tracked files；数据包包含 PHS bounds；三个包均不含 `supplementary_materials/`。当前因 SSH key-exchange 关闭尚未上传。

1. 恢复 SSH 后先核验服务器 Git HEAD、旧 744h PID 和 `solve_report.json/solution_qc.json`，不得用旧文档推断当前状态。
2. 部署 commit `2a0ee99` 及由最小输入合同构建的新数据包。
3. 执行 readiness、24 项测试和 744h CPU gate。
4. 744h 通过后执行 8760 `--build-only`，记录真实 build time、model statistics 和 peak RSS。
5. 只有 build-only 和可用内存门槛均通过，才启动 2030 full-year；2030 通过后由 `scripts/run_cispo_planning_sequence.py` 依次推进后续年份。
