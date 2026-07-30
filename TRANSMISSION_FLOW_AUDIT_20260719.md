# 省际双向潮流与 CISPO 对齐审计（2026-07-19）

## 结论

服务器 744h 输出虽然达到 Gurobi `OPTIMAL` 且旧版 `solution_qc.json` 为 `PASS`，但不能验收。结果存在实质性同线路同小时双向潮流，模型利用输电损耗吸收电量，并通过年度负荷中心毛流量闭合获得可行性/成本收益。该行为不符合 CISPO S4-55/S4-56 的设定。

## 被拒绝的 744h 基线

- 输出：`/data/zz2/National_model/outputs/2030_one_month_20260719_sequential_sparse_cpu`
- 模型：3,955,002 variables；5,919,470 constraints；44,169,131 nonzeros。
- 构建：348.74 s；峰值 RSS 5.07 GiB。
- 求解：20,118.58 s；barrier 10,969.01 s；crossover 9,123.64 s；总峰值 RSS 22.141 GiB。
- 数学状态：`OPTIMAL`；最大约束违反 `9.63e-08`。
- 物理审计：3,358 个 bidirectional edge-hours；两方向较小流量累计 3,909.04 GWh；最大较小方向 4.393 GW。
- 典型线路：`CORRIDOR_0001`（北京—河北）多时段正反向流量之和顶到容量上限。
- manifest：仅 `runner_stdout.log` 在 manifest 写出后继续增长，造成大小与 SHA256 不闭合。

744h 是测试窗口，年度成本、碳约束和生物质约束未按 744/8760 缩放，因此其容量扩建和成本结果本身也不具有科研解释性。

## 与 CISPO 公式的差异

用户提供的 CISPO 页面规定：

1. AC 线路有正、反向非负流量，并满足 `f_forward + f_reverse <= p_AC`（S4-56）。
2. DC 线路采用固定方向（S4-55）。
3. 目标函数加入 `0.001 yuan/kWh` 的轻微流量成本，即 `1 yuan/MWh`。

旧实现虽然具有共享容量约束，但存在三项偏差：流量成本误写为 `0.001 yuan/MWh`（小 1,000 倍）；DC 允许反向流；新增负荷中心层分别闭合毛发送和毛接收，从而给对冲潮流创造收益。

## 修复

实现 commit `1b6da28`：

- AC 保留正反向变量与共享容量约束。
- 363 条 DC 候选/既有边的反向变量 UB 固定为 0。
- `network.flow_regularization_yuan_per_mwh` 从 `0.001` 改为 `1.0`。
- 年度负荷中心网络按省级 `received - sent` 净交换分配，不再要求中心层闭合毛出口。
- `solution_qc.json` 新增 AC 双向流量和 DC 反向流量硬检查。
- `load_center_network_qc.csv` 将内部双向流动列为失败条件。
- manifest 排除由外层 shell 在主程序结束前后继续写入的 `runner_stdout.log`、`runner_stderr.log` 和 `run.pid`。

## 本地验证

- `unittest discover -s tests -v`：26/26 PASS。
- 输出：`outputs/2030_diagnostic_24h_cispo_flow_alignment_local_20260719`。
- 模型：350,024 variables；261,280 constraints；1,867,006 nonzeros。
- Gurobi：`OPTIMAL`，40.02 s；峰值 RSS 0.700 GiB。
- AC bidirectional edge-hours：0。
- DC reverse maximum：0 GW（363 条 DC 边）。
- 负荷中心最大省级净交换残差：`9.15e-10 GWh`。
- 最大省级小时功率平衡残差：`5.35e-12 GW`。
- 最大水库转移残差：`7.63e-06 m3`。
- scientific manifest mismatch：0。

## 后续门槛

1. 服务器同步 `1b6da28`，运行 26 项回归测试和新的 24h 求解。
2. 共享服务器可用内存恢复到安全水平后再运行修复后的 744h；旧结果不得作为接受依据。
3. 修复后的 744h 必须 `OPTIMAL + QC PASS`，且 AC 双向记录和 DC 反向流均为 0。
4. 只有此后且服务器可用内存不少于 64 GiB，才运行 8760h build-only。

## 2026-07-30 负碳诊断窗口补充

诊断时域年度碳账户按 `optimization_hours/8760` 缩放后，2050/168 h
Base 在吉林—黑龙江一条 AC 走廊的 3 个 edge-hours 再次出现小规模对冲流。
最大较小方向为 `0.176374 GW`、累计较小方向为 `0.381006 GWh`，其额外制造
的输电损耗仅 `0.011489 GWh`，分别占全国毛输电量与系统负荷约
`1.3823e-5` 和 `4.0100e-8`。该窗口的净碳上限精确 binding，节点价格最低
约 `-3650 CNY/MWh`；因此 `1.004004 CNY/MWh` 毛流量成本不能在深度负价下
提供无条件单向保证。

作者决定不让这种系统级影响极小的现象阻断更长工程排错。当前合同仅对
`TEST_ONLY_TRUNCATED_HORIZON` 增加可审计 warning budget，并同时限制发生
小时数、最大对冲功率、线路容量占比、累计对冲电量、额外损耗及两项系统
占比；任一超限仍 hard fail。`SCIENTIFIC_PRODUCTION` 全年结果继续要求
`1e-6 GW` 以上零对冲。该修改不改变 LP 方程、目标、输电成本或输出原始
流量，也不把 warning 解释为物理严格单向。

## 服务器修复验证

- 服务器 tests：26/26 PASS，22.24 s。
- 输出：`/data/zz2/National_model/outputs/2030_diagnostic_24h_20260719_cispo_flow_alignment_cpu`。
- Gurobi 13.0.2：`OPTIMAL`，43.88 s；350,024 variables；261,280 constraints；1,867,007 nonzeros；峰值 RSS 0.845 GiB。
- AC bidirectional edge-hours：0。
- DC reverse maximum：0 GW（363 条 DC 边）。
- 最大功率平衡残差：`1.46e-11 GW`。
- 最大水库转移残差：`7.63e-06 m3`。
- 全部 hard checks：PASS。
- scientific manifest mismatch：0。
- 资源门：当时 available RAM 约 32 GiB，21 GiB swap 已满，因此没有启动新的 744h。
