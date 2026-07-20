# 服务器 744h 运行审计（2026-07-20）

## 1. 审计结论

`/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` 是一次有效的旧稀疏架构工程门槛：它在 commit `5a9f4ab` 下得到 `OPTIMAL + solution_qc=PASS`，证明 744h 连续 LP 可以在现有 125 GiB 服务器上完成。但它不是论文结果，也不是当前 V0719 模型结果；它不包含核电上界、共享 `bio+bioccs` 容量上界、2030 电池省级下界和 DC 反向变量消除。

实时复核时服务器代码 HEAD 已为 `3c9edfa`，`zz2` 名下没有 CISPO/Gurobi 求解进程。旧结果目录保持原样，没有重跑、改名或删除。

## 2. 求解范围与数值结果

| 项目 | 证据 |
|---|---:|
| 时间范围 | 2030 年前 744 小时（1 月），测试时段首尾循环 |
| 科学用途 | `TEST_ONLY_TRUNCATED_HORIZON` |
| 年度缩放 | 投资/政策项未按 744h 重标，禁止作为规划结果 |
| 变量 | 3,955,064 |
| 约束 | 5,919,746 |
| 非零系数 | 43,707,940 |
| 预求解后规模 | 3,274,401 行、3,082,861 列、32,316,806 非零 |
| Barrier factor NZ | `8.198e8`，Gurobi 日志估计约 10.0 GB |
| Barrier | 214 次迭代，9,976.91 s |
| 完整求解 | 1,468,988 次 simplex 迭代，16,244.99 s |
| Gurobi runtime | 16,245.79 s |
| 墙钟时间 | 4:37:02 |
| 峰值进程树 RSS | 21.979 GiB |
| 目标值 | 2,196,413.3453 million CNY（测试混合口径） |

96 个逻辑 CPU 可见，Barrier 实际使用 48 线程；`run.time` 报告平均约 29 个 CPU 核的利用率。大规模 crossover 占用了约 6,268 s，因此该实例的运行时间不仅由 Barrier 决定。744h 到 8760h 不能按小时数线性外推，factor fill-in 和 crossover 都会非线性增长。

## 3. 物理与数值 QC

- 最大省级功率平衡残差：`3.64e-10 GW`。
- 最大约束/变量边界/对偶违反：`9.73e-8 / 6.59e-8 / 8.81e-8`。
- AC 同小时双向流动：0 个 edge-hour。
- DC 反向流动：0。
- 储能循环、水库水量/库容、碳、生物质、CO2 源汇和目标分解均通过旧版硬检查。

旧 QC 没有显式复核惯量、容量裕度、RUC 状态转移、热电最小/最大出力，也没有记录储能同充同放和热机同启同停互补性指标。本轮代码已经补齐这些输出与检查；它们不能追溯性地添加到旧 744h 结果，必须由新版本小规模回归或未来 8760h case 产生。

## 4. 旧输出的可用性与缺口

旧 case 共记录 38 个 manifest 文件，包含容量、成本、碳/CCS、278 负荷中心、逐省/全国平衡，以及热电、VRE、储能、水库、输电 `.npz`。主要缺口如下：

1. 缺少 `model_config_snapshot.json`、软件环境、命令行、输入文件逐项 SHA256 和 CF/Zarr 元数据指纹，难以独立确认运行时精确输入。
2. `.npz` 没有统一数据字典；`reservoir_dispatch.npz` 的 `hydrochn_row_id` 和 `transmission_flows.npz` 的 `line_ids` 是 object dtype，需要 `allow_pickle=True`，不适合安全公开读取。
3. 缺少逐省逐技术容量/发电表、逐省资源/碳核算、逐时备用与惯量分解、年度容量裕度表。
4. `annual_summary.json` 和 `annual_*` 字段在 744h 下容易被误读为全年量；实际只是截短时段电量与年度投资/政策项的混合测试口径。
5. 旧 `result_manifest.json` 当前校验失败两项：`run.stdout` 在 manifest 后继续追加，`run.time` 在 manifest 时仍为空。除此之外的科学文件哈希一致。旧 manifest 因而不能作为目录整体不可篡改证明。
6. 文件属主/权限显示为 `root:root` 且 world-writable。旧目录不修改，但未来云端/服务器 case 应由提交用户写入并避免 `0777`，否则结果完整性依赖 SHA256 而非文件权限。

## 5. 本轮修复与新 case 接口

当前代码保留旧稳定文件名，并新增：

- 输入与运行证据：`input_manifest.csv`、`model_config_snapshot.json`、`run_environment.json`。
- 可发现性：`output_catalog.csv`、`output_data_dictionary.csv`。
- 可读时间与分析表：`time_index.csv`、`annual_capacity_by_province_technology.csv`、`annual_generation_by_province_technology.csv`、`annual_resource_accounting_by_province.csv`、`annual_adequacy_by_province.csv`、`hourly_province_security.csv.gz`。
- 完整运行数组：新增 `hydro_dispatch.npz`，并在热电/VRE/储能数组中补齐 ramp 与 reserve。
- 互补性基线：储能同充同放、热机同启同停的次数、最大重叠功率和累计重叠电量。
- 结果完整性：运行包装器的 `run.stdout/run.time` 不再进入科学 manifest；所有 NPZ 标识符改为固定宽度 Unicode，可用 `allow_pickle=False`。
- 跨年完整性：规划状态绑定 source QC、最终 solve report、cohort 和 transition summary 的 SHA256；序贯恢复同时校验完整 result manifest。

## 6. 对 8760 云端运行的直接含义

旧 744h 结果仍是求解复杂度证据，但不能作为当前模型的最终工程门槛。云端 8760 前应按以下顺序：

1. 当前代码在本地完成 24h `OPTIMAL + QC PASS + manifest PASS`。
2. 同一 commit 部署到本地服务器，执行 tests、data smoke 和 24h 回归。
3. 云端只做 preflight/build gate，确认 Gurobi license、内存、磁盘和输出路径权限。
4. 8760 运行使用新的自描述 case 接口；若 solve、QC、catalog 或 manifest 任一失败，不得向下一规划年传递状态。
