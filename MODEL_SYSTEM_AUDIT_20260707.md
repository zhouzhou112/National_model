# CISPO 全模型系统审计与数值稳定性报告（2026-07-07）

## 1. 审计边界

本次审计覆盖 `cispo_model/master.py`、`cispo_model/monolithic.py`、`cispo_model/hydro.py`、`cispo_model/load_center.py`、`cispo_model/diagnostics.py`、`cispo_model/solution_export.py`、`config/optimization_2030.json` 及生产入口 `scripts/run_cispo_2030_full_year.py`。审计内容包括变量维度、约束方向、物理单位、时间/空间索引、目标函数计费、数值尺度、求解器线程、结果 QC 和服务器运行证据。

本次没有改变模型的研究边界：2030 单年容量扩张、31省、连续 LP/RUC、严格逐小时省级功率平衡、完整时序、站点级水库调度和 Stage2 核心梯级传播均保持不变。

## 2. 模块审计结论

| 模块 | 决策变量与单位 | 时间/空间尺度 | 主要约束 | 审计状态 |
|---|---|---|---|---|
| 风光 | 站点容量 `GW`；省-技术逐小时可用/发电 `GW` | 36,686技术站点；31省；小时 | `available = Σ CF × capacity`；`generation <= available` | 公式和单位一致；`CF < 1e-6` 置零以避免无意义微系数 |
| 火电/RUC | 容量、在线、启停、毛发电、爬坡均为 `GW` | 31省 × 11技术 × 小时 | 连续容量型最小出力、最大出力、启停、爬坡、最小开停时间 | 未发现方向或单位错误；仍缺论文中的 `f_on` 在线燃料项 |
| 储能 | 充放电/备用 `GW`，SOC `GWh` | 31省 × battery/PHS × 小时 | 效率、自放电、功率、时长、循环 SOC、备用可行性 | 单位一致；现有 PHS 是电储能表示，尚无开环/闭环水力配对 |
| 径流式水电 | 站点容量 `GW`；省级逐小时可用/发电 `GW` | 1,410站点 CF 汇总到31省 | `ror_available[p,t] = Σ CF[i,t] × capacity[i]`；允许弃水 | 没有站点级逐小时调度变量；符合小时因子模式。若论文结果需要站点级弃水轨迹，需另行增加输出分配规则 |
| 水库式水电 | 发电 `GW`；内部流量单位 `10^3 m3/s`；内部库容单位 `10^6 m3` | 620站 × 小时 | 发电-流量、水量平衡、库容上限、功率上限、循环边界 | 已实施严格等价变量缩放；物理输入/输出仍为 `m3/s` 和 `m3` |
| 核心梯级 | 上游过机流量+弃水，按时滞进入下游 | 146站、142节点、124边 | 2019 GRFR 互相关时滞，0–168h，循环测试边界 | 公式已实现；4条低相关边和18条168h上限边仍需人工复核 |
| 省际输电 | 双向流和容量 `GW` | 411走廊 × 小时 | 收端损耗、共享双向容量 | 约束正确；连续 LP 仍可能产生容差量级的双向同时流，QC 已记录但未硬失败 |
| 功率平衡/安全 | 发电、负荷、备用 `GW`；惯量 `GW·s` | 31省 × 小时 | 严格功率平衡、上下备用、容量裕度、惯量 | 索引和单位一致；容量信用和惯量阈值仍是显式软假设 |
| 碳/CCS/DAC | 排放、捕集、运输、注入 `MtCO2` | 年度、省-封存点 | 碳上限、源汇守恒、注入容量、生物质上限 | 单位闭合；约100,471个省-汇流量变量是固定规模块 |
| 278负荷中心 | 年电量/流量 `GWh`，容量 `GW` | 278中心、517省内边 | 年度能量闭合、设计利用率容量约束 | 与省级小时平衡年度求和闭合；省内损耗仍固定为0 |
| 目标函数 | `million CNY/year` | 年度 | 投资、固定运维、运行、输电、CCS、DAC | 未发现重复计费；截断时段不缩放年度成本，只能用于工程测试 |

## 3. 数值根因与修复

旧744小时模型的主要数值问题来自水库物理量直接进入 LP：

- 库容使用 `m3`，最大 RHS 为 `44,779,949,240`；
- 水量平衡包含 `3600` 系数；
- 最小容量因子约 `1e-10`；
- 最终矩阵范围约 `1e-10–3600`，RHS 范围约 `2e-13–4.48e10`。

提交 `281f9c7` 采用严格等价变量替换：

```text
q_model = q_m3s / 1000
v_model = v_m3 / 1e6
Δv_model = (q_in_model - q_out_model) × 3.6
P_GW = q_model × 1000 × ηρgH / 1e9
```

同时：

- `coefficient_zero_tolerance` 从 `1e-10` 调整为 `1e-6`；
- `hydrology_flow_zero_tolerance_m3s=1e-4`；
- `BarConvTol=1e-8`；
- 保留 `Crossover=1`，因为无 crossover 的 barrier 内点解未通过水量平衡 QC；
- `Threads=-1`，Gurobi 13 使用全部可用逻辑 CPU，Gurobi 12 自动解析为 `os.cpu_count()`；
- 新增 `scripts/audit_model_numerics.py` 和 `--diagnostic-hours`。

阈值影响的保守上界：风光全部潜力同时落在阈值下时，可用功率上界损失不超过 `0.0575 GW`；径流式水电不超过 `0.000130 GW`；`1e-4 m3/s` 流量阈值在最大水头站对应约 `1.54 kW/站`。这些阈值只消除数值噪声，不改变可解释的系统出力。

## 4. 动态验证证据

### 旧744小时基准

- 输出：`/data/zz2/National_model/outputs/2030_one_month_hydro_cascade`
- 模型：4,808,836变量、6,536,681约束、46,092,407非零系数。
- 运行 `37,576.53 s` 后仍在重启的 crossover 中，无可行解；正常中断后状态 `INTERRUPTED`，`solution_count=0`。
- 峰值进程树 RSS：`22.161 GiB`。

### 本地24小时

- 输出：`outputs/2030_diagnostic_24h_numerics_scaled_crossover1`
- 模型：422,596变量、342,508约束、2,037,549非零系数。
- 系数范围：`1e-6–24`；RHS：`4.32e-7–1.17e5`。
- Gurobi：`59.66 s`，状态 `OPTIMAL`；总监控时间 `82.11 s`；峰值 RSS `0.865 GiB`。
- `solution_qc.json=PASS`；最大功率平衡残差 `1.45e-10 GW`；最大水量平衡残差 `7.63e-6 m3`。

### 服务器168小时

- 输出：`/data/zz2/National_model/outputs/2030_diagnostic_168h_numerics_scaled`
- 模型：1,299,844变量、1,581,351约束、10,733,898非零系数。
- 系数范围：`1e-6–168`；RHS：`4.32e-7–1.17e5`。
- 构建约 `90.54 s`；Gurobi `675.56 s`；总监控时间 `771.71 s`；峰值 RSS `4.061 GiB`。
- 状态 `OPTIMAL`，`solution_qc.json=PASS`；最大功率平衡残差 `7.89e-12 GW`；最大水量平衡残差 `9.65e-6 m3`。
- 服务器识别48物理核、96逻辑线程；`Threads=-1`，日志声明最多使用96线程，barrier 数值分解实际使用48物理线程。Python建模、排序和部分 crossover 阶段不能持续占满全部核心。

## 5. GPU 结论

服务器有两张 RTX 4090，驱动 `570.133.07`，计算能力 `8.9`。硬件落在 Gurobi 13.0.2 GPU PDHG 支持的计算能力范围内，但当前环境安装的是标准 `gurobipy 13.0.2`，不是带 `+cu...` 后缀的 GPU 构建，因此当前任务没有使用 GPU。

Gurobi 13 的 GPU 加速仅针对 PDHG：需要独立 GPU 构建、`Method=6`、`PDHGGPU=1`。它不是 barrier 的 GPU 版本，且最终 crossover 仍可能抵消前段加速。官方建议优先在 H100 或更新硬件评估，并明确要求按模型实测。因此建议建立独立环境进行168小时和744小时 A/B 测试，不替换当前已验证 CPU 环境。依据：[GPU-enabled Gurobi 安装与运行](https://support.gurobi.com/hc/en-us/articles/43498824105873-Installing-and-Running-GPU-enabled-Gurobi)、[Gurobi 13.0 GPU 支持平台](https://docs.gurobi.com/projects/optimizer/en/current/reference/releasenotes/platforms.html)、[Threads/PDHGGPU 参数](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html)。

## 6. 尚未关闭的问题

1. 新744小时门槛尚未启动；目标是一小时内完成，但必须以实际 `solve_report.json` 和 `solution_qc.json` 为准。
2. 全年8760小时模型仍不能启动，直到744小时通过。
3. `master.py` 中保留了一组早期分块架构的边界变量；在当前单块 monolithic 模型中部分变量与小时状态未直接链接，属于可删除的冗余增强层。删除前需做等价性对照，不应与本次数值修复混合。
4. 径流式水电是站点 CF 加权、省级发电变量；如需每站实际发电/弃水输出，需要明确分配规则或增加站点变量。
5. P30环境流、PHS水力配对、4条低相关时滞边和18条上限时滞边仍是数据问题。
6. GPU PDHG 需要单独下载 GPU-enabled Gurobi 构建并在隔离环境验证。

## 7. v0.4.1 追加审计结论（2026-07-07）

本追加段落覆盖本报告早期“尚未关闭的问题”中已经处理的部分：

1. `master.py` 中早期分块架构遗留的边界变量已经在 commit `a8cd150` 删除，包括 `storage_boundary`、`online_boundary`、`gross_boundary`、`reservoir_boundary`、`startup_history`、`shutdown_history`、`startup_prefix` 和 `shutdown_prefix` 及其冗余增强约束。生产入口仍是 monolithic LP；旧 `subproblem.py` 和 Benders 脚本继续作为弃用原型，不作为生产路径。
2. 径流式水电保持“站点 CF 加权、省级出力变量”实现：站点容量仍为站点级决策变量，小时可用出力按站点 CF 与容量加权汇总到省级 `ror_generation_gw`，不引入径流式站点级调度变量。
3. 常规水电环境流量已从 2019 单年 monthly P10 proxy 切换为 2019 单年 monthly P30 proxy。该处理响应当前建模选择，但仍不是正式的 1980-2019 多年气候态 P30。
4. PHS 暂保留为省级储能变量，不复现论文中的 open-loop/closed-loop 水力配对。
5. GPU-enabled Gurobi 已安装在隔离环境 `/home/zz2/.local/envs/cispo-gurobi-gpu`，版本为 `gurobipy 13.0.2+cu129`。探针日志确认 `linux64gpu[cuda12]`、`GPU model: NVIDIA GeForce RTX 4090` 和 `Start PDHG on GPU`。
6. 对同一 24h P30 诊断模型，CPU barrier 在 `45.06 s` 达到 `OPTIMAL` 且 `solution_qc=PASS`；GPU-PDHG 运行约 `600 s` 后仍未完成，已中止且没有 `solve_report.json`。因此当前模型默认求解路径仍应使用 CPU barrier，而不是 GPU-PDHG。
7. P30-cleanup 744h CPU 门禁已启动：`/data/zz2/National_model/outputs/2030_one_month_p30_cleanup_cpu`，PID `863603`。模型构建已完成，耗时 `339.56 s`，峰值 RSS `5.336 GiB`，规模为 4,762,150 variables、6,472,914 constraints、45,718,011 nonzeros。Gurobi 优化仍在进行；该门禁未完成前，不得启动 8760h production solve。

## 8. 精确下一步

1. 监控 `/data/zz2/National_model/outputs/2030_one_month_p30_cleanup_cpu` 的744小时 CPU 门槛，当前 PID 为 `863603`。
2. 要求 `OPTIMAL`、`solution_qc=PASS`、可接受的水量/功率残差，并记录构建/求解/导出时间、峰值内存和线程利用率。
3. 若744小时超过一小时，先保存完整日志和报告；不要修改物理约束。GPU-PDHG 在24小时 P30 模型上已经明显慢于 CPU barrier，暂不作为默认加速路线。
4. 744小时门槛通过后，先做8760小时 `build-only` 和内存审计，再决定是否启动 production solve。
