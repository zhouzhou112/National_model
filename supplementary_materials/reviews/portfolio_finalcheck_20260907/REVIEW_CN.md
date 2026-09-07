# Base＋三个 V5 灵活性情景：正式运行前最终自检

日期：2026-09-07。实现提交：`ba57c79c3cedd3f70b2516cc76ffb29532bf7a5d`，父提交 `45e716f`。

本轮结论：参数与代码级保全/恢复自检通过；**不能据此把三个情景的全年宽松求解标记为已验证可靠**。没有启动优化、presolve、松弛、Stage B 或云作业，没有部署或修改正在运行的 Base。范围冻结为 Base、Base＋冷热、Base＋EV、Base＋冷热＋EV；文献响应候选未启用。

## 1. 参数、输入与 Base 一致性

只读 SSH 获取 job4479238 对应冻结 release 的配置、输入清单和源码 SHA。2026-09-07 17:40 前后观测为 `RUNNING 4-00:16:14 m4cg1605`，只是观测时刻状态。受保护的供给、供需平衡、水电、碳核算、时间块及年度容量行缩放核心源码一致；解析 Base 科学配置零差异。三个情景仅有场景身份与灵活性开关/模块配置差异。

本轮未改三情景配置、物理约束、目标函数、输入数据或筛选规则。2 省×24h 服务块的矩阵、RHS、上下界、目标 SHA 与此前保存的版本完全一致。这不是重新构建全国8760h完整电力系统矩阵的证据。

真实输入核验覆盖31省2030年8760h：负荷组件重建误差最大 `1.1368683772161603e-13 GW`，EV参考服务能量逐小时误差最大 `8.881784197001252e-16 GWh`。V5五个生成文件的完整SHA和大小与manifest一致；文件覆盖2025/2030/2040/2050/2060年，31省、每年8760h。本轮没有重新建立2040—2060各年的实际求解实例。

| 项目 | 冻结设定 | 审查解释 |
|---|---|---|
| 冷热响应 | 沿用既有小时上/下调包络；非负周期服务库存；供暖/制冷小时留存率0.94/0.92，库存时长4/5h，充放效率1 | 上调＋下调共享签约功率，不新添舒适欠账；这是聚合服务代理，不能解释为实测室温RC模型 |
| 冷热费用 | 年签约40元/kW；激活300元/MWh | 2025不变价；两个方向的激活按原合同计费 |
| EV智能充电 | 15%为可参与基准池上限，实际签约比例内生 | 未签约群体维持Base负荷；签约功率与服务份额绑定 |
| V2G | 嵌套份额不超过 `(10%/15%)×已签约V1G份额`；独立充电/服务库存；充放效率各0.94 | 不借用另一池的库存；全国签约功率上限2030/40/50/60分别10/20/30/40GW |
| EV费用 | V1G年签约60元/kW、移位300元/MWh；V2G年签约60＋设施40元/kW、激活150＋退化400元/MWh放电 | V1G移位口径和V2G能量损耗均沿用；不把电价/补贴转移支付重复计入社会成本 |
| 可靠性边界 | 规划容量充裕度沿用Base峰荷口径；不赋予灵活性额外firm容量或备用供给信用 | 避免未经验证就凭需求响应削减可靠供给 |

尚存的解释边界：EV连接比例是归一化可用系数，出发最低库存是聚合代理，并非实测插枪/旅程/SOC；冷热包络亦非逐建筑观测。应在论文方法中如实写明。这些局限没有在本轮被“放宽”或改成更乐观参数。

## 2. Base宽松参数是否可以直接沿用

**当前配置实际上不相同。** 从运行Base配置与三个情景实际加载配置对比，仅有下列两个数值配置差异：

| 参数 | 运行Base | 当前三个情景 |
|---|---:|---:|
| `BarConvTol` | 0.01 | 1e-9 |
| `Threads` | 32 | 44 |

其余共同采用Method2、Crossover0、SolutionTarget1、FeasibilityTol/OptimalityTol各1e-6、NumericFocus1、ScaleFlag2、Aggregate1、Presolve2，无求解器TimeLimit和SoftMemLimit。线程差异属于资源选择，不改变数学模型。

直接代入Base数值参数、使用真实8760h输入做建模前检查：EV情景PASS；冷热、冷热＋EV情景BLOCKED，原因是原有长库存链数值保护要求严格nonbasic或已认可的basic路线。**EV的PASS也只代表通过这个结构检查，并非8760h结果已合格。** 当前1e-9配置三个都通过结构检查，但全年收敛时间和原始单位QC仍未验证。

因此不建议在本轮静默把三个情景统一改回0.01。较宽松的终止条件可能节省时间，但不能解释为“所有约束可违反1%”，也不能从求解器OPTIMAL状态推导出原始水量、冷热服务或EV能量约束均满足。既有宽松中等时段结果存在原始单位残差失败的证据；严格历史8760h水量通过也不等于当前宽松三情景通过。

本轮保持profile、QC阈值和启动保护不变。若以后选择Base宽松参数，应明确它是候选求解路线，保全所有结果，最终按相同原始单位QC与原始/对偶目标差评价四组结果。计算时间有限不能作为忽略QC的理由；也不应为了“统一参数”让Base或灵活性情景取得不同科学接受标准。

## 3. 修复的保全与恢复路径

1. 求解前原始MPS与参数归档必须COMPLETE；归档失败立即拦截优化。
2. `solve_and_report`发生异常时，单年入口先尝试保存可读的全部数值属性，再独立尝试容量成本、运行数组、QC、汇总、候选状态和目录。异常与失败标记同时保留。
3. 损坏的QC/dual sidecar不再中断后续导出；保留损坏原文件副本于`failed_sidecars/`，并记录错误。QC失败不筛掉原始向量或约束违反表。
4. 新增显式`--allow-recovery-barrier-checkpoint`：RECOVERY/PENDING_QC checkpoint或异常raw snapshot可进入**同年、同情景、同时间窗、同一LP**的PStart/DStart准备路径。核对科学输入、模型身份、版本、维度、Fingerprint、变量/约束顺序、行缩放、向量SHA和有限性。改变年份/情景/模型或损坏文件仍拒绝。
5. 默认接受门槛不变：不合格状态不能自动传给下一规划年，不会因保存完整而变成论文结果，也不会自动启动Crossover/Stage B。
6. 停止请求经STOP_REQUESTED协调；solver_start/end在信号处理器有效期间记录，避免在导出阶段发送SIGTERM。Bash wait被信号打断时继续等待子进程保存完成。终态依据实际归档和向量校验，不再依赖遗漏RECOVERY状态的枚举。

| 结束情况 | 保留内容 | 可恢复程度 |
|---|---|---|
| 收敛且QC合格 | 原始MPS、参数、完整checkpoint、正常结果与QC | 精确重建；通过既有门槛后规划续年 |
| 未收敛/受控停止/QC失败，但有限原始与对偶向量可读 | 原始模型＋全向量＋可生成的完整语义结果，失败QC/残差不删除 | 显式同LP Crossover恢复准备；源结果始终未接受 |
| 求解或报告抛出异常 | 原始模型＋当时可读全部属性＋独立导出/错误报告 | 完整有限P/D时可准备同LP恢复；否则保留模型重建能力 |
| 无可读解，或向量非有限 | 原始模型、参数、可读证据、缺失/非有限标记 | 不能声称有可用warm start；可以从原模型重新开始 |
| 强杀/OOM杀进程/节点断电/磁盘故障 | 只能依靠此前成功落盘的文件 | 无法保证最后迭代向量、完整导出或内部状态存在 |

特别说明：**Gurobi Barrier不支持内部迭代热续接。** MPS和PStart/DStart不是Barrier因子分解或内部预处理映射的序列化。恢复Crossover有可能很贵、未必比重新Barrier更快；本轮只验证准备/导入接口，没有启动恢复求解或证明大规模恢复耗时。[Gurobi官方说明](https://doc.gurobi.com/projects/optimizer/en/current/features/warmstart.html)、[LPWarmStart参数](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html#parameterlpwarmstart)。

`COMPLETED_PRESERVED_REVIEW_REQUIRED`只表示完整模型与有限原始/对偶向量已核验保存；全部语义导出是否完成仍须看`preservation_report.json`和`result_manifest.json`，不能单凭wrapper退出0判断论文合格。

## 4. 测试与复现

30项不求解回归全部通过；全程封锁Gurobi optimize/optimizeAsync/presolve/feasRelax入口，主动排除已有真实求解测试。包含：故意违反约束的向量精确存取、MPS重读Fingerprint、非有限/无解证据、异常保全、损坏QC后续导出、未接受checkpoint显式恢复、Fingerprint/时间窗/文件损坏拒绝、默认跨年门槛、原三情景零签约退回Base，以及Bash中断wait的模拟。Windows仅模拟中断返回并做真实Bash语法检查，没有在Slurm上做信号/OOM演练。

```powershell
# 参数/原输入自检，输出目录应为新目录；不构建或求解全国电力系统LP。
python scripts/audit_final_portfolio_no_solve.py --base-snapshot output/portfolio_finalcheck_20260907/base_identity/model_config_snapshot.json --output-dir output/portfolio_finalcheck_repeat
$env:PYTHONPATH='.;tests'
python -m unittest test_final_preservation_no_solve.FinalPreservationNoSolveTests test_portfolio_no_solve.NoSolvePortfolioTests -v
# 完整30项的已审查无优化测试选择器：
python output/portfolio_finalcheck_20260907/run_no_solve_regression.py
```

本目录`evidence/`保存小证据；完整本地审查路径为`output/portfolio_finalcheck_20260907/`。Base只读比较未重新扫描所有大型风光数据块，远端输入清单是启动时记录；新V5数据文件则做了当前完整SHA核验。

## 5. 正式启动前剩余事项

- 模型范围、签约参数与物理约束可以冻结，不需要为本轮自检继续扩模块或大改模型。
- 当前含冷热情景的“Base宽松配置资格”尚未闭合；本轮没有绕过保护或改为放宽QC。必须先明确正式采用的配置与相同接受标准，不能把本报告解释为宽松8760h成功保证。
- 本次修复仅在本地提交，尚未部署。未来部署必须新建冻结release并核验SHA、Gurobi版本、输出目录、磁盘余量和资源配置，不能覆盖正在运行的Base。
- 当前portfolio wrapper仍是2030入口和云端≤4h测试预算；它不是十天正式作业提交脚本。后续正式资源/调度安排需要作者明确授权，且必须在walltime强杀前预留真实导出时间。不能承诺4h分段Barrier热续接。
- 待作者决定启动时再执行相应提交动作。本轮没有要求或启动任何新优化；也没有为结束任务而宣布全年模型已数值合格。
