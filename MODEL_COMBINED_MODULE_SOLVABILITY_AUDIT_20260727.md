# 全模块联合敏感性与求解性审计（2026-07-27）

## 结论范围

本审计新增并验证独立情景
`wave_energy_medium_v1_flexible_load_comfort_v3_v2g_5pct`。它在一个连续 LP 中同时启用：

- 基于既有海洋 `grid_uid` 的 medium 波浪能扩张；
- `comfort_envelope_v3` 的供暖、制冷等效热状态；
- 带滚动 12 h 服务期限的 EV V1G；
- 每省每日基线 EV 峰值 5% 上限、日内因果零边界的 V2G。

该情景是 `EVIDENCE_ANCHORED_PARAMETERS_REQUIRE_SENSITIVITY` 的联合敏感性，**不是 Base**，也不是可用于论文科学解释的全年结果。Base 的灵活负荷、V2G 和波浪能仍均关闭；目标函数、约束、空间尺度和 `8760 h` 科学时间边界均未改变。

## 本轮可复现实验

所有输出均为新建、被 Git 忽略的本地根；既有 744h 输出、固定服务器 checkout 和 ParaCloud 队列均未写入或改变。

| 门禁 | 输出根 | 终态与 manifest | 主要结构/资源证据 |
| --- | --- | --- | --- |
| 全年 preflight | `outputs/preflight_2030_wave_comfort_v3_v2g_5pct_v0727` | 仅静态通过；本机 15.64 GiB 未达 96 GiB build gate | 44,445,512 variables；69,551,896 constraints；538,014,168 nonzeros；37.63 GiB 静态估计 |
| 24h build-only | `outputs/2030_24h_v0727_wave_comfort_v3_v2g_5pct_build` | build 成功 | 354,920 variables；268,398 constraints；1,844,355 nonzeros；19.281 s；0.455 GiB 峰值 RSS |
| 1h solve | `outputs/2030_1h_v0727_wave_comfort_v3_v2g_5pct` | `OPTIMAL + solution_qc=PASS + validate_result_manifest=True` | 238,839 variables；82,735 constraints；468,502 nonzeros；9.661 s；0.414 GiB |
| 24h solve | `outputs/2030_24h_v0727_wave_comfort_v3_v2g_5pct` | `OPTIMAL + solution_qc=PASS + validate_result_manifest=True` | raw 354,920/268,398/1,844,355；presolved 132,254/266,492/1,299,953；`AA' NZ=2.221e6`；`Factor NZ=6.179e6`；101 Barrier；56,990 simplex/crossover；39.176 s；0.733 GiB |
| 168h solve | `outputs/2030_168h_v0727_wave_comfort_v3_v2g_5pct` | `OPTIMAL + solution_qc=PASS + validate_result_manifest=True` | raw 1,081,688/1,429,226/10,293,428；presolved 751,365/865,314/7,363,654；`AA' NZ=2.162e7`；`Factor NZ=1.056e8`；`Factor Ops=8.603e10`；180 Barrier；239,930 simplex/crossover；602.265 s；3.296 GiB |

`solution_qc.json` 的所有 hard checks 均为真；168h 最大功率平衡残差为 `1.14e-10 GW`，最大约束/边界/对偶违例为 `4.17e-8/6.82e-12/1.75e-10`。本轮完整本地回归为 `67/67` 通过。

### 与本地 Base 24h 的同机结构对照

相同本地数据、同一连续 LP 代码和 P0 manifest 契约下，Base 24h 根
`outputs/2030_24h_v0727_manifest_runtime_contract` 为 raw
342,343/262,201/1,771,702，presolved 129,124/258,630/1,252,290，
`AA' NZ=2.196e6`，`Factor NZ=6.145e6`，`Factor Ops=6.376e8`。

联合情景相对该 Base 24h 增加 12,577 variables（3.67%）、6,197 constraints
（2.36%）和 72,653 nonzeros（4.10%）；`Factor NZ` 增加约 0.55%，
`AA' NZ` 增加约 1.14%。运行时钟不作为结论，因为短窗口的 solver 调度波动大且两个情景的科学问题不同。

固定服务器 Base 168h 是不同硬件/线程配置下的参考，不能与本地联合 168h 作速度或内存因果比较；它只表明联合 168h 的 factor 结构已经处于同一数量级。若要检验模块引入的 168h 因果影响，须在同一主机、同一线程数和同一 solver profile 下补做匹配 Base 对照，且不能与其他 solve 并发。

## 截断窗口中模块是否实际调度

168h 输出确认接口和物理约束均被装配：

- EV V1G 上/下移各 `190.173 GWh`，全省累计 backlog 峰值和为 `56.594 GWh`；
- 供暖、制冷状态和搬移为零；V2G 充/放电均为零；
- `wave_capacity.csv` 的 `capacity_gw` 与 `new_capacity_gw` 总和均为零，波浪发电与弃波也均为零。

这不能解释为“冷热、V2G 或波浪能无价值”。`TEST_ONLY_TRUNCATED_HORIZON` 同时含全年化容量/政策成本和仅 168h 的运行项，`run_summary.json` 已明确其目标“not a planning result”；尤其不能用它排序技术经济性或作年度/路径成本结论。

## 已定位的求解阻碍

1. **全年 Barrier 因子化而非模型构建。** 联合全年静态矩阵仅比 Base 多约 3.53 million variables（8.64%）、1.95 million constraints（2.88%）、17.09 million nonzeros（3.28%）和 1.63 GiB 静态估计。静态内存并不包含 Barrier factor/workspace；现有云端 8760h 的 OOM/超时证据不能被该 preflight 覆盖。
2. **时间展开状态约束与 crossover。** 联合 168h 已有 `1.056e8` Factor NZ、`8.603e10` Factor Ops、180 次 Barrier 和 239,930 次 simplex/crossover。继续只压缩 raw variables 不是充分指标；必须优先观察 presolved 矩阵、`AA' NZ`、`Factor NZ/Ops` 和 crossover 工作量。
3. **模块经济参数尚未校准。** 热工 retention/duration、车辆连接与可用电池、出发 SOC、响应补偿以及波浪 2060 profile/cost 均仍是敏感性假设。这是科学解释门槛，不是通过调低约束获得加速的理由。
4. **短窗口的目标解释限制。** 1h/24h/168h 可验证接口、数值稳定性和稀疏结构，不能判断全年装机、波浪采用或 V2G 价值；不应用于替代 8760h 或代表日方案。

## 不改变 Base 边界的下一步

1. 保留本联合情景和上述门禁根；不启动固定服务器 8760h、任何新的付费云端作业，或第二个并发 solve。
2. 以 `scripts/compare_solver_runs.py` 的现有口径，先补齐同机同 profile 的 168h Base/联合结构对照（仅在无运行任务且确认资源后）；记录 raw/presolved rows、columns、nonzeros、`AA' NZ`、`Factor NZ/Ops`、build/presolve/ordering/Barrier/crossover、iteration、objective、QC 和峰值 RSS。
3. 在不改变科学边界的前提下，优先分析稀疏矩阵构建重复、time-expanded 约束组装、presolve、线程数和 crossover；候选必须先经匹配 24h/168h `OPTIMAL + QC + manifest` 门禁。
4. 年度模型缓存、basis warm start 或 2030→2040 状态复用仅能减少重建/初始点成本，不能假定复用 Barrier factorization；应作为独立小规模原型验证，且保持年份 cohort/state hash 的严格身份校验。
