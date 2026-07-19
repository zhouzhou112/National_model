# CISPO 全年模型可解性、数值稳定性与跨年状态审计（2026-07-19）

## 1. 结论

当前模型在 24h、168h 和旧 744h 尺度上已经证明为连续 LP，并且经过水量变量缩放后能够由 CPU barrier + crossover 求到高质量解。但在现有 `125 GiB` 服务器上，直接构建并求解单体 8760h 模型仍具有很高的内存失败风险：

- 当前代码按 8760h 精确外推约有 `44,091,176` 个变量、`68,188,384` 条约束和约 `515-524 million` 个矩阵非零元。
- 只保存原始模型矩阵和变量/约束工作区的经验估计约为 `37 GiB`；用旧 744h 实际构建峰值校准后，完整构建峰值约为 `58 GiB`，因此 build-only 有机会在服务器空闲时完成，但不应再使用仅 `64 GiB` available RAM 的紧边界。
- 旧 744h barrier 的 `Factor NZ=8.289e8`，Gurobi 自报约 `10.0 GB`。即使只按小时数线性放大，8760h 因子本身也约为 `118 GB`；再叠加原模型、presolve、排序、线程工作区和 crossover，服务器总内存很可能超过 `125 GiB`。填充通常并不保证线性，因此这是偏乐观下限，不是上限。
- 旧 744h 的 `20,118.58 s` 求解时间中，barrier 为 `10,969.01 s`，crossover 为 `9,123.64 s`。可解性阻碍是大型稀疏矩阵的因子填充和高度退化的 crossover，不是 Python 建模时间。
- `Crossover=0` 不能作为生产捷径。对当前修正模型重新运行 24h 后返回 `SUBOPTIMAL`，最大约束违反 `0.01355`，水库转移和传输方向 QC 失败。
- 将 `FeasibilityTol/OptimalityTol` 从 `1e-7` 放宽到 Gurobi 默认 `1e-6`，并把 `BarConvTol` 从 `1e-8` 放宽到 `1e-7`，在当前 24h 本地模型上仍为 `OPTIMAL/QC PASS`，求解从基线约 `40.02 s` 降至 `37.38 s`。该收益只有约 7%，不能据此推断 744h/8760h 会显著加速；Gurobi 官方也明确说明，放宽 barrier 收敛可能把时间转移到更长的 crossover。

因此，当前推荐路径是先做数学等价的稀疏化，再在 168h 和修正后的 744h 上做参数矩阵测试。若 barrier 因子内存仍按现有规律增长，则必须在“至少 256 GiB RAM 的机器”与“保持全部 8760 时序但采用精确分解”之间选择；现有 125 GiB 主机不适合作为未经验证的单体全年生产求解器。

## 2. 审计证据

### 2.1 当前代码与服务器

- Git branch：`codex/cispo-2030-full-lp`
- 审计基线：`f22b9cf`，包含模型实现 commit `1b6da28`
- 服务器 checkout：`/data/zz2/National_model/repo`，实时 HEAD `f22b9cf`
- 服务器：48 physical cores / 96 logical CPUs，约 `125 GiB` RAM
- 审计时实时资源：约 `30 GiB` available RAM，`21 GiB` swap 已满；外部四个 Python 作业合计约 `85 GiB RSS`
- 因此本轮没有启动新的服务器 744h 或 8760h 任务。

### 2.2 实测规模

| Horizon | Variables | Constraints | Nonzeros | Build/solve evidence |
|---:|---:|---:|---:|---|
| 24h current | 350,024 | 261,280 | 1,867,007-1,867,008 | 当前本地结构/数值审计；服务器修正模型 `OPTIMAL` in 43.88 s |
| 168h current build | 1,071,032 | 1,392,991 | 10,480,639 | 本轮本地 build-only 数值审计，89.5 s |
| 744h rejected baseline | 3,955,002 | 5,919,470 | 44,169,131 | build 348.74 s；solve 20,118.58 s；peak RSS 22.141 GiB |
| 8760h revised projection | 44,091,176 | 68,188,384 | 515-524 million | 24/168 与 24/744 斜率交叉校准 |

原 `preflight` 的 `853,505,952` nonzeros 是偏保守的通用上界；它高估原始矩阵非零元约 63%，但同时没有表示 barrier 填充，因此 `46.62 GiB estimated model memory` 不能解释为全年求解峰值。

## 3. 8760h 模块规模贡献

### 3.1 变量

| 模块 | 8760h variables | 占比 | 主要变量 |
|---|---:|---:|---|
| Hydropower | 16,842,810 | 38.20% | 620 个水库站的 turbine/spill/volume；省级 ROR dispatch/available；站点容量 |
| Thermal RUC | 14,936,637 | 33.88% | 31 省 × 11 技术 × online/startup/shutdown/gross/ramp |
| Interprovincial transmission | 7,201,542 | 16.33% | 411 条 corridor × forward/reverse hourly flow |
| Storage | 2,715,724 | 6.16% | battery/PHS charge/discharge/SOC/up/down reserve |
| VRE | 2,245,852 | 5.09% | 省-技术-hour dispatch/available + 36,686 site capacity/new |
| Carbon/CCS/DAC | 100,906 | 0.23% | 31 × 3,241 source-sink flow是主要固定块 |
| Spur/trunk | 42,980 | 0.10% | site spur 与 substation trunk augmentation |
| Annual load-center | 4,725 | 0.01% | 278 中心和 517 条省内边的年度变量 |
| **Total** | **44,091,176** | **100%** | |

水电变量多并不是因为 ROR 被按站点逐小时调度。ROR 仍是“各站 CF × 各站容量后汇总为省级可用出力”；逐小时站点变量来自 620 个水库式站点。

### 3.2 约束

| 模块 | 8760h constraints | 占比 | 主要来源 |
|---|---:|---:|---|
| Thermal RUC | 39,733,661 | 58.27% | 连续 RUC、min up/down、ramp、CHP、biomass online |
| Hydropower | 16,814,500 | 24.66% | 水库功率/库容/水量转移及 ROR 可用性 |
| Storage | 4,888,142 | 7.17% | 功率、SOC 转移、上下备用投影 |
| Interprovincial transmission | 3,600,771 | 5.28% | 共享 corridor capacity |
| VRE | 2,033,966 | 2.98% | 104 个实际省-技术 availability 组合和 124 个 dispatch 上界 |
| Balance/security | 1,086,271 | 1.59% | 省级功率平衡、上下备用、惯量、容量裕度 |
| Spur/trunk | 23,952 | 0.04% | 年度接入容量 |
| Carbon/CCS/DAC | 3,615 | 0.01% | 年度碳、biomass 与 source-sink 账户 |
| Annual load-center | 3,506 | 0.01% | 年度中心网络；行数很少但行很长 |
| **Total** | **68,188,384** | **100%** | |

### 3.3 非零元

由当前 24h 和 168h `constraint_family_scaling.csv` 分离固定块与逐小时斜率，并对全年 CHP 冬季小时作修正后：

| 模块 | Projected nonzeros | 占比 |
|---|---:|---:|
| Thermal RUC | 162,836,552 | 31.14% |
| VRE | 152,033,549 | 29.07% |
| Balance/security | 80,832,599 | 15.46% |
| Hydropower | 50,846,358 | 9.72% |
| Annual load-center | 45,252,115 | 8.65% |
| Storage | 15,750,604 | 3.01% |
| Interprovincial transmission | 10,801,902 | 2.07% |
| Carbon/CCS/DAC | 4,546,772 | 0.87% |
| Spur/trunk | 68,598 | 0.01% |
| **Total** | **522,969,049** | **100%** |

年度 load-center 只有 3,506 条约束，却贡献约 45 million nonzeros，因为少数年度账户直接汇总全年 hourly dispatch/flow。这种“少量超长行”比行数占比更值得关注，也可能放大 barrier fill-in。

## 4. 内存与耗时判断

### 4.1 静态构建

按现有 preflight 的每个 nonzero/variable/constraint 经验字节公式，将 revised nonzeros 代入，原始模型工作区约为 `36.9 GiB`。旧 744h 同一公式约为 `3.2 GiB`，而实际构建峰值约为 `5.07 GiB`，校准倍率约 `1.58`；全年 build 峰值因此约为 `58 GiB`。

这说明：

- 服务器完全空闲且 available RAM 至少 `96 GiB` 时，8760h build-only 值得测试。
- 当前仅 `30 GiB` available 且 swap 已满时，build-only 会与其他任务争抢内存，不应启动。
- `64 GiB` 是过紧的全年构建门槛；应在完成数学等价稀疏化后，把全年 build-only 调度门槛提高到 `96 GiB`，并继续记录真实 peak RSS。

### 4.2 Barrier 与 crossover

旧 744h Gurobi 日志：

```text
Presolved: 3,274,450 rows, 3,353,208 columns, 34,097,199 nonzeros
AA' NZ:     7.211e+07
Factor NZ:  8.289e+08 (roughly 10.0 GB)
Factor Ops: 6.215e+12
Barrier:    208 iterations, 10,969.01 s
Crossover:  9,123.64 s
Simplex:    1,538,530 iterations
```

`Factor NZ / AA' NZ ≈ 11.5`，显示显著填充。即使以 `8760/744=11.77` 线性放大，factor memory 也约 `118 GB`；原模型和其他工作区尚未计入。因此在 125 GiB 主机上，单体全年求解是高风险动作，而不是“只要 preflight 约 47 GiB 就能跑”。

耗时也不能简单按 12 倍外推。若因子规模和 crossover 退化只线性增长，已经是约 2.8 天；若 fill-in 或迭代数随全年耦合加重，可能更长。当前 `TimeLimit=86400 s` 会在 24 小时停止，因此即使内存足够也可能先触发 `TIME_LIMIT`。

## 5. 数值稳定性

当前修正 24h 数值审计：

- matrix coefficients：`1.05e-6` 到 `24`
- objective coefficients：`1e-6` 到 `3375.82`
- positive RHS：`3.63e-7` 到 `44,779.95`
- 小于 `1e-8` 的 matrix coefficients：0
- 大于 `1e3` 的 matrix coefficients：0

当前 744h 日志：

- matrix coefficients：约 `1e-6` 到 `628`
- objective coefficients：约 `1e-6` 到 `3e3`
- RHS：约 `4e-7` 到 `9e4`
- 最终最大约束违反：`9.63e-8`

结论是：水量流量/库容缩放已经消除了最危险的 `1e-10` 级矩阵系数和 `1e10` 级 RHS；当前数值质量足以达到 QC。但年度汇总系数会随小时数增长，168h 模型的最大系数已经从 24 增至 168，8760h 仍应在 build-only 后重新运行 `audit_model_numerics.py`，不能只使用 24h 范围判断全年。

## 6. Gurobi 参数审计

### 6.1 当前合理设置

- `Method=2`：对当前大型 LP，barrier 是已验证最快的 CPU 路线；默认 concurrent 会复制算法工作区并显著增加内存。
- `Threads=-1`：Gurobi 13 使用全部 96 logical CPUs；barrier 因子分解实际使用 48 physical threads。
- `Presolve=2`：旧 744h 将 rows 从 5.92m 降到 3.27m，保留。
- `ScaleFlag=2`、`NumericFocus=2`：对当前跨 `1e-6` 到数百的系数范围属于保守而合理的生产设置。
- `Crossover=1`：当前 QC 需要 basic solution 精度；不能直接关闭。
- `SoftMemLimit=80`：适合作为保护性停止，但它不能把 80 GiB 以上的 barrier 变成可解。

### 6.2 需要调整或基准测试的设置

1. `FeasibilityTol=1e-7`、`OptimalityTol=1e-7` 比 Gurobi 默认 `1e-6` 更严格。24h relaxed test 表明恢复默认容差并保持 QC 可节省约 7%，可作为 168h/744h 候选，而不是直接改成生产默认。
2. `BarConvTol=1e-8` 是 Gurobi 默认。24h 的 `1e-7` 候选通过 QC，但官方说明放宽 barrier 可能延长 crossover；必须看 168h/744h 总时间而不是只看 barrier iterations。
3. `Crossover=0` 已在当前模型上重新否决。下一轮可比较 `Crossover=-1/1/2`；旧 744h 主要耗时在 primal cleanup，`Crossover=2` 的 dual cleanup 值得单独测量。
4. `DualReductions=0` 和 `InfUnbdInfo=1` 当前对每次正常求解都强制启用。更合理的工作流是生产首跑使用默认 reductions；只有出现 `INF_OR_UNBD` 时，再用 `DualReductions=0`/`InfUnbdInfo=1` 或 homogeneous barrier 诊断。需先在 168h 上比较 presolve 与结果一致性。
5. `NodefileStart=16` 写在配置里，但 `configure_gurobi()` 没有设置它；更重要的是 Nodefile 只解决 MIP branch-and-bound node 内存，对本模型的 LP barrier factorization 无效。它不应作为全年内存保护依据。
6. 若内存而非时间成为硬限制，官方建议比较 `Method=1` dual simplex。它大概率更慢且基本单线程，但内存通常明显低于 barrier；可作为“125 GiB 能否完成”的保底实验。
7. 可在 168h/744h 比较 `Aggregate=0/1`、`BarOrder=-1/0` 和 `NumericFocus=1/2`。旧 744h 的 ordering 只有 126.59 s，优化 ordering time 本身不是重点；应比较 `Factor NZ` 和总时间。

参数依据见 Gurobi 官方 [Parameter Reference](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html) 与 [Parameter Guidelines](https://docs.gurobi.com/projects/optimizer/en/current/concepts/parameters/guidelines.html)。

## 7. 优先稀疏化方向

以下均可保持当前物理边界、8760 连续时序和最优解集合不变：

1. 消除 `vre_available_gw` 辅助变量及 availability 等式，把 site CF 聚合表达式直接用于 VRE dispatch 上界和 reserve。预计减少约 `1.09m` 变量及约 `0.91m` 等式。
2. 消除 `ror_available_gw` 辅助变量及 availability 等式，用站点 CF × capacity 表达式直接约束省级 ROR generation 和 reserve。预计减少约 `0.27m` 变量和约 `0.25m` 等式。
3. 年度 load-center 中，`province_external_net_import` 应由已存在的 `received - sent` 年度变量定义，避免第三次复制全部 hourly corridor flow 系数。
4. 每个 center 已与其 reservoir station generation 严格相等，因此省级 `load_center_reservoir_generation_closure` 是覆盖完整时的冗余约束，可在先加入显式覆盖断言后删除。
5. 更新 `preflight`：同时报告 exact variables/constraints、empirical nonzeros、static build memory 与 barrier-risk estimate，避免把静态模型内存误当求解峰值。

如果这些等价稀疏化仍不能把 factor memory 压入服务器范围，则需要改变求解架构或硬件。保持所有 8760 小时并不等于必须构建单个 monolithic matrix；精确时间分解可以不使用代表日和权重，但这会改变当前“单体 LP”架构约束，必须单独获得研究设定批准。

## 8. 跨年容量传递

### 8.1 已实现的正确关系

对 2040 及以后年份，容量下界按下式形成：

```text
capacity_floor(planning_year)
  = exogenous_floor(planning_year)
  + sum(active model-built cohorts)

active cohort iff build_year <= planning_year < retire_year
```

2030 的 accepted full-year solution 会将 `new_capacity` 或 augmentation 写入带 SHA256 的 `capacity_cohorts.csv.gz`。2040 只有在读取到 metadata year=2030、SHA256 正确且 asset ID/unit 合法时才会启动。当前传递资产包括：

| Asset class | Resolution | 2030→2040 treatment |
|---|---|---|
| VRE | 36,686 site-technology | 继承 active `vre_new`，叠加原始 site floor |
| Thermal/nuclear | province-technology | 继承 new build 与 CCS retrofit out/in |
| Hydropower | station | 继承 station `hydro_new` |
| Battery/PHS | province-technology | 继承 power capacity；energy 由固定 duration 派生 |
| Interprovincial transmission | corridor | 继承 corridor expansion |
| Intra-load-center transmission | 517 edges | 继承省内 annual capacity expansion |
| DAC | province-technology | 继承 annual capture capacity |
| VRE/hydro spur | site/station | 继承 augmentation |
| Trunk/substation | substation | 继承 augmentation |

因此，用户要求的“2040 以 2030 优化完成的风光、储能、输电等装机为基础继续优化”在代码路径上已经实现，不是仅靠输出表手工复制。

### 8.2 尚不能称为物理上完全

1. 当前是 sequential myopic planning，不是 2030-2060 四期 perfect foresight 联合优化。2030 不知道 2040/2050/2060 的未来成本和约束。
2. 现有 2025 VRE 因缺少 plant age 继续作为外生 floor，不退役；新建 VRE 按 25 年 cohort 退役。
3. 现有 hydropower 按论文假设保持运行至 2060；新扩水电按 40 年寿命。
4. thermal retrofit 缺少 plant-level identity 和 remaining life。当前 retrofit cohort 按 retrofit 年起算完整技术寿命；如果未来外生 thermal floor 退役使负调整超过剩余容量，代码会 fail-fast，而不是静默截断。
5. nuclear exogenous floor 从 2030 的 106.764 GW 增至 2040 的 146.308 GW；模型-built nuclear 与未来 pipeline floor 被解释为相互独立的额外容量。论文中必须明确这一加法解释，否则可能被误读为重复计算同一项目。
6. PHS 只传递省级 power capacity，energy capacity 固定为 8h；没有 open/closed-loop 水库配对状态。
7. SOC、水库年末库容和机组 online 状态不跨规划年传递。由于每个规划年是独立典型气象/水文年的 cyclic 8760 运行，这一处理在当前边界下是合理的；它不是连续模拟真实 2039-2040 年末状态。
8. 当前尚未实际完成 2030 full-year accepted solve，因此 2030→2040→2050→2060 的生产链仍是“实现并通过小规模诊断”，不是 end-to-end 科学结果。

## 9. 下一步门槛

1. 先实施第 7 节的数学等价稀疏化，并更新 scale estimator 与 regression tests。
2. 本地通过 24h numerical audit、`OPTIMAL/QC PASS` 和跨年全资产 cohort 单元测试。
3. 服务器在 available RAM 至少 `64 GiB` 且 swap 压力解除后运行修正 744h；记录 `Factor NZ`、barrier/crossover 分时和 peak RSS。
4. 只在服务器 available RAM 至少 `96 GiB` 时运行 8760 build-only；不得立即 optimize。
5. 若 build-only 峰值或 barrier 线性下限表明总内存超过主机，停止单体求解，改用至少 256 GiB 节点或提交精确分解架构供研究边界审批。
6. 容差候选必须在修正 744h 上同时满足 `OPTIMAL + all hard QC PASS + objective/capacity comparison` 后才可写入生产配置。

