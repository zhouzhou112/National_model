# Base V9 是否落实原对话的修复：部署与表述审计

2026-09-15 23:21–23:22北京时间；Git基准`0a03cc452e95d158f36923ceb5210267979b6234`及既有dirty工作区。本轮只读服务器，不修改模型/参数/输入/运行作业。

## 结论

已阅读任务“诊断最新 base 数值错误”（01a09910-847c-7232-bb5c-6e5d6971e2c8）全部12个已返回轮次的用户请求与最终答复。原思路为允许有预算的小幅资源损失，修复真实水库输入、清理无帮助的微量数值、减少无效库存范围，最终达到稳定高效求解。

修复实现和部署已落实；但“数值问题彻底解决、9–10天可靠完成”的结果目标尚未达成。上一答将38.9倍突出为显著改善，容易放大工程效果；应准确称为“原始矩阵最大/最小非零系数比缩小38.9倍”，不能替代条件数、运行时间、内存或最终QC。

## 1. 部署证据

- 当前job4614693对应release：`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260914_base_v9_t48_m750_tol1e4_v3`。
- 云端203文件逐项SHA256与启动冻结manifest一致，0不一致；本地对应198个源码/配置/修正输入文件与同一manifest一致，0不一致。覆盖范围不是整个dirty仓库。
- 实际batch明确`--config config/optimization_numeric_dac_by_year_v9.json`、`--solver-config config/solver_profiles/barrier_stagea_numeric_repaired_v1_threads48.json`；`CISPO_DATA_ROOT`指向本release的`data_overlay`，`PYTHONPATH`优先本release源码。
- 运行时`model_config_snapshot.json`、构建报告、`solver_parameters_before_optimize.json`及输入manifest相互一致。
- 实际使用的修正电站表SHA：`f8135eaffa2de77461912cba5216106f66e0b6207c8b6c381fd725339a378e94`，既与运行输入manifest一致，也与本次读取data_overlay实体文件的SHA一致。
- 与原对话v8冻结源码比较，核心`hydro.py`、`monolithic.py`、`master.py`、`numerical_cleanup.py`、`data.py`、`load_center.py`逐字节一致。后续`config.py`差异为年度DAC开关，`diagnostics.py`差异为不限时参数清除/回读校验；runner修复前后两处年度行合同。v8/v9科学配置仅scenario/scientific_case/features顶层不同，保留原修复。

## 2. 原思路→实现→实际生效证据

| 原对话要求 | 实现及运行证据 | 判断 |
|---|---|---|
| 修正三站有效库容 | 实际修正表：锦屏二级4.96、白竹洲3.84、克孜尔339.9 GL；表SHA及路径验证 | 已部署并由输入manifest引用 |
| 去掉无意义循环库存偏移 | `monolithic.py:801`启用`reduce_cyclic_inventory_range=true`，调用`cyclic_inventory_upper_m3`并赋给库存UB | 已接入建模路径 |
| 清理微小本地来水 | `hydro.py:589`阈值0.01 m³/s，清理后重建入流能量，不补水 | 已启用 |
| 清理CF | `monolithic.py:244`及ROR/波浪对应路径阈值0.01 | 已启用；不是全矩阵统一清零阈值 |
| 清理微容量 | `master.py:864/879`，floor/headroom阈值1e-5 GW即10kW | 已启用；保留站点/变量身份 |
| 梯级比例毛刺 | `hydro.py:605`，`cascade_transfer_cleanup_fraction=1e-4` | 已启用；原审计21个edge-hours不冒充本次重新全量计数 |
| 孤立水库弃水上界收紧，并修正过小正UB | `monolithic.py:844`调用`independent_spill_upper_scaled`，开关true，正上界floor1 m³/s | 已启用；这是UB的下限处理，不是强制弃水下限 |
| 城市流量正则提高至1元/MWh | 运行快照`load_center_network.flow_regularization_yuan_per_mwh=1.0` | 已启用；与省际network的1.004004区分 |
| 2030关DAC，后续年份恢复 | 运行features.dac=false，年度表2030false/2040–2060true | 已启用；后续年份本轮未运行 |
| 撤回8192年度行缩放 | 实际构建registry物理行exponent0，runner检查实际矩阵与registry一致 | 已生效 |
| 撤回碳平衡行单位试验 | 当前`carbon_accounting.py`与v8最终冻结源码相同，未残留v7试验 | 已撤回 |
| 最终用户指定求解参数 | 实测NF2/48线程/BarConvTol1e-4/Crossover0/SolutionTarget1，TimeLimit/SoftMemLimit/MemLimit/WorkLimit均无限 | 与原对话最后约定一致 |

最初v8配置文件仍包含8线程、Cross2、1e-8、900s等本地测试默认值；正式batch显式叠加solver profile后，运行快照与实际参数已变成最终约定。不能只读科学配置文件的未覆盖默认值就判定云端误部署。

## 3. 为什么只有38.9倍，以及为什么不是大幅提速

原始矩阵范围：旧版`1.000486e-6～6250`，当前`3.7e-5～5945.8478`。

- 最小非零系数提高约36.98倍，最大系数只下降约4.87%。
- 最大/最小之比由6.247e9变为1.607e8，缩小38.9倍，对数跨度约从9.80个数量级变为8.21个，减少1.59个数量级。
- 该统计只看两个极值，不说明系数分布、病态位置、接近线性相关的约束、因子分解条件数或可行性/最优性。因此不是性能倍数，更不是完成保证。
- 官方的粗略经验是系数比尽量小于1e9、理想小于1e6；当前虽低于前者，仍高于后者约161倍。这是经验线索，不是验收阈值，不应为跨过阈值盲目改单位：[Gurobi数值问题诊断](https://docs.gurobi.com/projects/optimizer/en/current/concepts/numericguide/modelissues.html)。

### 原对话数字不能混用

原对话“168小时最大系数6250→168”来自关闭DAC后的短窗对照。全年仍保留`E_annual <= sum(CF_t) * K`类年度容量链接，最大等效利用小时约5946，因而没有降到168。这是时间窗口不同，不是DAC关闭漏部署。原报告已指出全年最大年度资源系数仍约5945.847912，本次实际矩阵统计与该量级一致。

“年度/小时链接跨度70倍”“弃水正上界跨度91倍”“目标跨度1000倍”分别是不同子块/统计口径，而且主要相对中间v3；38.9倍是旧失败全国LP对当前全国LP。它们不能相乘或相加，也不能拿短窗范围替代全年。

库容和库存修复主要改变变量边界，并不要求改变矩阵A的最大/最小系数；目标正则改变c，亦不属于A。实质输入修复存在，不必都体现在同一个系数比中。

### 实际工程收益应如何表述

上一轮云端对照已证实，相对旧Base：原始变量数不变，raw nnz-1.73%、presolved nnz-2.85%，Factor NZ-2.07%，Factor Ops+0.27%；峰值RSS从480.48增至678.11GiB。当前仍有约37557个dense columns和26个free variables，长期耦合结构没有大规模重写。

合理评价是：已完成有明确输入/物理含义的清理和纠错，但结构计算量基本未降；数值稳定性收益要等全年收敛与原单位QC，尚未证明。没有证据支持“部署了一次巨大性能优化”。

## 4. 验证边界仍须如实说明

- 原对话的全国24/168h严格QC PASS使用过Crossover2；后来按用户要求恢复Cross0后，局部测试虽然OPTIMAL，但水量与双向流等严格QC仍未通过。原对话已作纠正。这些通过记录不能全部转移给当前Cross0生产配置。
- 620库×8760水力检查与全国电力系统8760LP不是同一个问题。原输入/局部可解性证据不能替代全年验收。
- 73站估算库容模式、10座年利用小时极低的ROR、高凤山等疑点并未全部证实或修正；三站纠错不代表所有输入风险消除。
- 23:22只读实查当前Base仍RUNNING，iter98，PInf470、DInf4.12e-8、Compl61.4；该更新只表示又推进一轮，不改变上述结论。

## 5. 复现与下一步

运行`python supplementary_materials/reviews/deployed_repair_audit_20260915/audit_deployment.py`，只读核验当前云端203个文件及本地198个文件，并保存`audit.json`、`evidence/`运行记录。原对话用户请求与最终答复筛选归档为`thread_reference.json`。源码差异为只读`git diff --no-index`，退出码1表示存在预期差异，不是执行故障。

本轮未重新运行求解测试，没有修改模型/数据/solver参数；只新增本目录及更新三份交接文档。随机种子不适用。后续优先追踪实际长程稳定性与最终QC；若继续诊断，应针对具体坏尺度行/列与约束族，不再将全局极值比作为主要优化成果。本轮不启动新的诊断作业或自动监控。
