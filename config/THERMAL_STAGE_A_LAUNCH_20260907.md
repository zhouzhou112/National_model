# 2030 Base＋冷热正式运行授权

作者在2026-09-07明确要求启动44线程Base＋冷热案例，随后明确正式案例取消任何时间限制。
本条仅替代此前对这一案例的“禁止启动”和4h云端测试时限；不授权EV、联合情景、下一规划年或自动Stage B。

- 情景：`case1_thermal_v5`，2030年31省8760h，原始Base负荷及既有V5物理/技术经济参数不变。
- 求解：`barrier_stagea_portfolio_v1_threads44`，`BarConvTol=1e-4`、Threads44、Method2、Crossover0、SolutionTarget1。
- 资源：既定`amd_a8_768`、1节点1任务、64 CPU/700G，实际计费必须为billing64。
- Slurm `--time=0`（UNLIMITED）；Gurobi `time_limit_seconds=null`、SoftMemLimit=null；不设定时STOP。
- 入口增加`--authorize-thermal-stage-a-1e4`，严格匹配2030/冷热/44线程/1e-4；默认无此授权仍拦截。
- 冷热库存长链使用已有等价压缩。保留仍需Aggregate=0的未压缩风险拦截；仅允许已知压缩形式按作者选定容差执行。
- QC阈值、原始单位物理审查、有限性检查、checkpoint与候选状态门槛不变。允许执行不代表全年数值已合格。
- 原始MPS与参数必须先完整归档；完整向量、QC失败、未收敛和异常按既有保全机制保留。
- 独立不可变release/输出目录；不得覆盖、停止或改变正在运行的Base job4479238。

启动前证据：4项授权范围/预算测试＋既有30项不求解回归PASS；真实31省8760h冷热建模前检查在显式授权路线下PASS。
以上不等于新的全年求解或大规模内存验收。代码及配置由提交SHA和release SHA清单固定，最终作业号和运行状态写入交接文档。
