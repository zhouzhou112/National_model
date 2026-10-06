# Base V9 job4614693终态核验：OPTIMAL后严格验收未通过

取证：2026-09-19 18:56–18:59北京时间（11:56–11:59英国夏令时）。Git基准`0a03cc452e95d158f36923ceb5210267979b6234`及既有dirty；只读服务器，无模型/输入/参数/作业变更。

## 1. 明确结论

Slurm为FAILED 2:0，但Gurobi并未NUMERIC崩溃。实际终态是OPTIMAL/status2、348轮、SolCount1，之后严格原始解质量与物理QC未通过，入口完整保存工程解后主动退出2。

- 作业开始：2026-09-14 10:20:55北京时间。
- 作业结束：2026-09-19 16:42:17北京时间，即英国夏令时09:42:17。
- Slurm墙钟：5天06:21:22；solver Runtime451391.622s，约5.2244天。两者口径不同。
- 日志：`Barrier solved model in 348 iterations and 451381.62 seconds`，`Optimal objective 4.19277884e+06`。
- solve_report：`STAGE_A_COMPLETED_REVIEW_REQUIRED`、`ENGINEERING_BARRIER_CHECKPOINT_COMPLETE`、`scientifically_accepted=false`。
- 原始矩阵50,907,233行/41,458,383列/484,299,937非零；运行参数仍Method2/NF2/48线程/BarConvTol1e-4/Cross0/SolutionTarget1，无时间或内存软限。
- Slurm峰值RSS678.106GiB；/usr/bin/time峰值678.406GiB，750GiB分配，Swaps0，stderr为空。无OOM或超时证据。
- 账号当前squeue为空。

## 2. 为什么显示FAILED

实际部署runner SHA为`a869aac11f745f78e6608bbb093bd6e7bdfbc975e8a91204e5323485e1e00d46`，与已审代码一致。`scripts/run_cispo_2030_full_year.py`约2230–2263行：对于未通过严格原始解质量的nonbasic结果，保存工程checkpoint、导出诊断和候选状态；即使保全COMPLETE，仍以SystemExit(2)阻止科学接受。

本次原始解质量门禁首先卡在`constraint_violation`：最大原始约束违反1.8554081001553868e-4，阈值1e-5。其余该门禁检查（OPTIMAL、原始约束residual、界违反、回调PInf、相对目标差）通过。不能将Slurm FAILED解释成Gurobi NUMERIC，亦不能因Gurobi OPTIMAL忽略独立QC。

## 3. 具体未通过项

`solution_qc.json`小时/运行硬检查59项，55通过、4失败：

| 检查 | 实测 | 当前阈值/解释 |
|---|---:|---|
| 省级小时功率平衡 | 最大0.000185540810GW，即185.54kW | 1e-5GW，即10kW，约18.55倍 |
| 水库小时水量平衡 | 最大1.601773808m³ | 1m³，约1.60倍 |
| 跨省双向流 | 420480 edge-hours；最大相向重叠13.9947MW；合计375.67093GWh | 全年严格方向检查失败；重叠量不等于损失电量 |
| 目标成本分项闭合 | 差7.38324597e-5 million CNY，即73.83元 | 1e-5 million CNY，即10元 |

双向流诊断给出的额外输电损失为9.74765261GWh，不是375.67GWh。禁止把反向重叠电量当作等量发电损失。DC最大反向流为0，跨省线路容量上限检查通过；本次方向问题不等于线路超载。

城市年度网络另有QC CSV，不包含在上述59项计数中：619条边存在高于0.0001GWh阈值的双向流，最大0.40753754GWh，合计1.82190194GWh；城市电量平衡等残差很小。这同样未满足现有严格方向条件。

对偶发布门禁还未通过：最大DualVio5.73371117e-4、最大ComplVio0.0951520361，阈值均1e-5。它们与Barrier日志的DInf/平均互补性不是同一统计，不可混用；现有对偶只供工程诊断，不能直接发布为影子价格。

这些失败同时包含小绝对误差和结构性方向检查；本轮仅如实列明，不擅自改阈值、不宣布它们全部无害。

## 4. 解确实已保全，可用于后续诊断

preservation_report为COMPLETE，errors为空；raw_checkpoint、capacity_and_cost、operation_carbon_dual_qc、summary、candidate_state、output_catalog均COMPLETE。原MPS存在，4,048,048,342bytes；本轮只验证其存在/大小，未重算4GB文件哈希。

本次直接在云端分块核验两份向量，仅读取约739MB，不构建/求解LP：

| 文件 | 条目数 | 大小 | 核验 |
|---|---:|---:|---|
| barrier_checkpoint/primal_barx.npy | 41,458,383 | 331,667,192bytes | SHA256、shape、float64、全有限值通过 |
| barrier_checkpoint/dual_barpi.npy | 50,907,233 | 407,257,992bytes | SHA256、shape、float64、全有限值通过 |

checkpoint标记ENGINEERING_BARRIER_CHECKPOINT_ONLY，`deferred_crossover_eligible=true`，scope为EXPLICIT_ENGINEERING_ACKNOWLEDGEMENT_REQUIRED。说明有后续原LP工程清理的材料，不代表已经验证当前profile下的恢复启动器或保证Crossover成功；保留的是向量，不是Barrier内部因子/预处理状态。

输出包含80文件合计约5.315GB，本轮未全量下载。候选规划状态位于`planning_state_candidate/`，`scientifically_accepted=false`，不得直接用于后续年份或论文结果。完整文件清单见inventory.json。

## 5. 与之前失败应区别评价

旧Base4479238、Thermal4533060均NUMERIC12且SolCount0；本次OPTIMAL2且SolCount1，有完整原对偶向量。这次已恢复全年求解完成能力，并将一次实际完成的solver Runtime从最初4139552的约20.53天降为约5.22天；不是同LP/同容差/同线程配对，不宣称单项修复带来3.93倍加速。

终点精确回调P=4192778.836192754、D=4192472.473057501，相对目标差7.306923337e-5，即0.0073069%。这是原对偶迭代目标诊断差，不是MIPGap或QC替代。当前目标不同于旧科学基准，不能直接解释成本收益。

完整日志iter0–348共349条连续，未观察到相邻Compl超过10倍的跳变；终态明确OPTIMAL。末段目标差和残差持续改善，不能称为重复旧版的后期NUMERIC崩溃。与此同时，严格质量仍未过，不能称最终科研任务已完成。

## 6. 复现、改动、下一步

- `python supplementary_materials/reviews/base_v9_terminal_20260919/collect_evidence.py`：SSH只读终态报告、日志、调度和目录大小，写evidence/、source.json、inventory.json。
- `python supplementary_materials/reviews/base_v9_terminal_20260919/verify_checkpoint.py`：SSH只读分块校验两向量与实际源码SHA，写checkpoint_verification.json；不调用Gurobi。
- 原始证据根：`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260914_base_v9_t48_m750_tol1e4_v3/output_8760`。
- 本轮新增本报告目录并更新CODEX_HANDOFF.md、MODEL_SERVER_STATUS.md、SERVER_RUNBOOK.md；Git未提交，无源码/数据/配置/服务器修改，无随机实验。
- 下一步优先复用已保存解定位省时/库时残差、双向流及成本闭合，再判断是否适合针对同一原LP做工程清理；本轮不自动重跑8760、不启动Stage B、不接受候选规划状态。
