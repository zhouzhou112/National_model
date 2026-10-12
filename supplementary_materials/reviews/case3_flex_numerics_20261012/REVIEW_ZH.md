# case3 柔性数值夜间实验（2026-10-12，进行中）

## 当前结论

**尚不能按任务书第 4 节给出三种终态结论。** P0 已复现历史异常；P1–P5 串行运行。T550 初次资源检查成功，随后 SSH/端口转发中断，实验包传输未获完成回执，F 系列未启动。这是连接阻塞，不是数值失败，不建议修改生产配置。

## 输入、模型与实验设计

执行依据为作者任务书 `TASK_case3_flex_numerics_overnight_20261012.md` 第 2–4 节。共识权威为仓库根 `RESEARCH_DESIGN_CONSENSUS_20261012.md`。本轮仅改诊断脚本和追加文档；`cispo_model/`、生产配置、solver profile 未修改。

P 系列使用 31 省、8760 个连续 1 h、2030 中央输入及 Base 2030 外生电价；P5 为 2060 输入配 2030 电价。决策变量为服务签约 K、EV alpha/beta 和各小时充放/冷热库存；目标为服务成本加外生电价购电成本，约束沿用真实服务块。该价格接受者不估计容量信用价值。GW/GWh、目标 million CNY；Seed=0、8 线程。P0–P5 每项求解 TimeLimit=2400 s（沿用现有诊断默认），若命中限时则如实标记未决，不作为通过。

F 系列计划 V9 + case3、2025 共同边界、无筛选、无继承、2030 全模型截断窗口。只改诊断运行的 Threads，F6 按任务条件单项改 Aggregate/Presolve。T550 串行 16 线程，所有对照记录并行=false；内存保留 15 GiB，资源不足先等待，求解中不足则请求有序返回并保全已取得向量，不杀其他用户任务。F5 独占本实验求解队列，最后执行。年度流量约束按 hours/8760 缩放、年化投资/固定成本不缩放、选择窗口循环边界；不作年度规划结论。

数据选择窗口：以全国逐时可签约削减包络的月能量求和，制冷为 8 月/start5088，供暖为 12 月/start8016。完整 12 月值见 `server_bundle_v1/windows.json`；没有用任意默认月份覆盖数据。

## 已有证据

- P0：94 轮，156.651 s 日志时间（API Runtime 约157.021 s），OPTIMAL；M=7.220764389091675 GWh，制冷最差省份35、hour1542；供暖最大0.16330272068037796 GWh，省份62、hour3177。复现了7.22 GWh异常。该结果只证明指标有效，尚不能在 H1/H2/H3 中择一。
- 本机 1h smoke v1 被服务器默认15 GiB资源保护有序中断；原档保留。v2 发现诊断报告少 `result_use`，原始解和各语义表保全、candidate state导出报错；修复只在诊断脚本中。v3 57轮 OPTIMAL，M=9.186815983641553e-10 GW/GWh；严格QC HARD_FAIL，但 preservation COMPLETE/errors=[]，包括 candidate state、原模型和可用BarX/BarPi/X/Pi，证明QC不阻止导出。1h 不计入F矩阵结论。
- 诊断实现提交 `aef0cb7`。只读核验 Base2060 Job5124127 RUNNING/m4cm2108；未发控制命令、未提交任何云端作业。
- T550首次：96逻辑核、可用54858166272 bytes，主要负载为其他用户预测训练，未发现CISPO求解器；未触碰 `cloud_backup`。新实验目标为 `/home/zz2/National_model_server/probe_outputs/case3_flex_numerics_20261012_aef0cb7`，此时尚未部署/创建。原包传输路径 `packages/case3_flex_numerics_20261012_aef0cb7.tar.gz` 可能是部分文件，保留而不覆盖。

## 运行、文件与核验

本机入口 `scripts/run_flex_price_series.py --prices ../claude_workspace/evidence/base2030_prices/hourly_marginal_prices.csv.gz --output supplementary_materials/reviews/case3_flex_numerics_20261012/P_series`，使用既有 RL 环境/Gurobi13，配置环境参见历史验证入口。启动PID44524；日志/逐2秒RSS在 `P_series/`。每项输出 `model_archive/`、`solution_snapshot/`、参数回读、原单位残差、逐省逐小时剖面和决策量。

T550包由 `scripts/prepare_flex_diagnostic_bundle.py` 生成，281文件/89345689压缩bytes；包内 `bundle_manifest.json` 含全部逐文件SHA。诊断队列 `scripts/run_flex_server_series.py` 采用新输出目录和现有solver锁；本轮连接恢复后才部署并验证。数据和模型大文件只留本机/实验服务器，不入Git。

汇总入口 `scripts/summarize_flex_numerics.py --p-root <P_series> --f-root <collected_F> --output <new-summary-dir>`。`runs.csv`、残差族表、>1%决策差、源SHA和逐小时PNG/PDF/SVG将按新目录增量生成。P0初图在 `summary_initial/`。图仅作机制定位：31省逐小时绝对残差（淡线）及每小时最大值（实线）、1 MWh门槛，symlog的线性区间1e-10 GWh；没有滤波、平滑或删除异常。

## 差异与下一步

1. T550资源紧张：按历史744h Base约22.4GiB峰值并加服务块余量，744h启动门槛43GiB、168h27GiB、2016h105GiB；求解中15GiB保护。门槛是诊断运行保护，不改数学LP或solver profile；若资源阻塞必须报未决，不能套用规则3冒充数值证据。
2. 参数、窗口和完整解按实际运行记录，不自行改生产设置。F1/F2/F5、F4→F1→F5增长及失败窗F6都齐备后才按任务书预登记规则判定；建议设置还需全部失败窗通过且744h轮数/耗时增加≤30%。
3. 连接恢复后先核对部分包，再使用新包文件名传输、SHA验证并在新目录启动。两次传输原件都保留，不覆盖冻结目录；不碰Job5124127或备份目录。
