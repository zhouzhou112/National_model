# 2026-09-13 能否9–10天完成与Thermal参数对照

## 判断

目前不能有依据地承诺修复版会在9–10天内稳定完成并交付可用全年结果。
这不是已证明它一定失败，而是尚未完成修复版真正8760 LP构建/预处理/Barrier收敛与峰值内存验证。
已有数据纠错、毛刺清理、数值范围压缩和局部可解性证据，仍不足以给出高置信度的全年用时。
不能把目标设为10天、调宽BarConvTol或保持进程存活解释成收敛保证。

当前待测入口还带900s optimize/2h Slurm时限、CLI上限1800s，仅供早期诊断；
原样使用它无法执行多日正式求解。未来正式启动必须明确调整这个预算，不能把诊断脚本当作已完成的生产启动方案。
本轮只回答和核实，不改变模型、参数、预算、服务器或正在运行的任务。

## 实际参数

Thermal来源为运行中job4533060的Slurm查询、有效model_config_snapshot及gurobi.log参数行，
当前来源为上一轮已实际回读的参数、有效配置及本轮脚本检查。当前Git HEAD仍为0a03cc452e95d158f36923ceb5210267979b6234。

| 项目 | 当前修复版待测入口 | Thermal实际运行 |
|---|---|---|
| Method | 2 | 2 |
| BarConvTol | 1e-4 | 1e-4 |
| Crossover / SolutionTarget | 0 / 1 | 0 / 1 |
| Gurobi Threads | 44 | 44 |
| Slurm CPU / 内存 | 64 / 700G | 64 / 700G |
| NumericFocus | **2** | **1** |
| Presolve / ScaleFlag / Aggregate | 2 / 2 / 1 | 2 / 2 / 1 |
| FeasibilityTol / OptimalityTol | 1e-6 / 1e-6 | 1e-6 / 1e-6 |
| MarkowitzTol | 0.01 | 0.01 |
| DualReductions / InfUnbdInfo | 1 / 0 | 1 / 0 |
| SoftMemLimit | 无 | 无 |
| Gurobi TimeLimit | **900s（诊断）** | 无 |
| Slurm总墙钟 | **2h（诊断）** | UNLIMITED |
| CrossoverBasis | 1，当前未启用Crossover | 未显式指定 |

NumericFocus=2比1更强调检测与处理数值问题，会使用更多检查和可能更昂贵的数值技术；
它是谨慎性差异，不是加速或成功保证。当前建议保持2，不仅为了复制Thermal而改回1。
CrossoverBasis不在Crossover关闭时启动转换；保留该字段不等于恢复Crossover。
依据：[Gurobi参数文档](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html#parameternumericfocus)。

## 模型处理差异必须同时看到

两者不是同一个科学LP，不能把耗时变化全部归因于NumericFocus。
当前v9 Base含三站库容纠错、循环库存界收紧、流量/CF/梯级比例和微容量清理，2030 DAC关闭；
Thermal使用旧水库数据且启用热负荷响应和DAC。当前已取消年度容量链接8192行缩放，Thermal仍启用。
当前CF清理阈值0.01，Thermal为1e-6；城市流量正则1 CNY/MWh，Thermal为0.001。
这些明确的数据/模型差异已在前几轮获授权并留档，本轮没有新增修改。
不要把新Base与旧Thermal直接混作同基准的最终情景比较。

## Thermal不是已经证明能9–10天结束的参照

2026-09-13 20:54:34北京时间只读查询：job4533060为RUNNING，已6天00:44:22，64CPU/700G/billing64。
20:55:28读取的gurobi.log最后完整行为iter483，solver518073s，P=1.59165741e9，D=-5.38091980e9，
PrimalInf=21.5，DualInf=1.41e-4，Compl=89.6。按项目诊断式
`abs(P-D)/max(1,abs(P),abs(D))`，当前约129.58%，全部484条迭代行中的最小值约97.57%。
该式不是Gurobi MIPGap，也不等于BarConvTol内部全部判据；但足以说明原对偶目标尚未接近。
当前不能据“已运行6天”或“迭代已经483轮”推断再3–4天必然收敛，也不据本次查询宣布终态失败。
该日志Presolve为17794.52s（约4.94h），进一步说明900s只够早期观察，尚不覆盖本例完整预处理。
服务器仅只读，未停止、重启或修改Thermal。

## 对宽松与效率的具体意见

固定用户选定1e-4/Cross0/44线程，不再为追求微小误差把Barrier容差收紧。
已有局部无Cross结果：水量残差按当前水头折算绝对值合计0.311MWh、目标相对Cross2差0.0033988%；
从全国能量尺度看，追求抹掉每个这种误差不值得无条件增加多日计算。它们仍须透明记录，当前严格QC结论不篡改。
更关键的是大库存/小通量造成的条件问题、未核实的高凤山工程库容，以及全年预处理/因子和原对偶收敛是否改善。
放宽停止标准不能修复这些问题；保存向量也不能保证NUMERIC后必有可恢复的有效解。

下一步应以固定配置在完整8760规模上评估最初12–24h的预处理/排序/迭代、目标差、残差和实际峰值内存，
在同一科学模型上判断是否持续改善及是否出现严重反复。需要覆盖前处理的测试预算，不能继续用900s窗口推算多日完成时间。
首日检查用于排除明显恶化路径，不是数学上的截止时间保证；本轮未启动或设置监控任务。
9–10天应作为希望达到的运行目标；当前还不能作为已经获得证据支持的交付承诺。

## 证据与限制

有效参数对照JSON/CSV、服务器读回、日志摘要、当前参数和局部残差引用均在本目录。
首次远端查询使用了Python3.6不支持的capture_output参数，失败后改为兼容写法；失败日志保留。
首次snapshot解析未取resolved_configuration，后续v2已修正；原记录保留。
没有重新运行模型测试或求解，因为本轮模型/参数代码未变。只更新本报告与四份交接文档，Git未提交。
