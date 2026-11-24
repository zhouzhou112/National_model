# 2040完成后的44/48线程速度复核

核验日期：2026-09-30（英国时间），采证UTC见manifest.json。Git基准0a03cc452e95d158f36923ceb5210267979b6234+既有dirty，未提交。本轮只读服务器，不改变模型、配置、原结果或作业。

## 建议与比较边界

若当前必须二选一，速度优先暂倾向48 Gurobi线程；证据有限，尚未通过同LP受控试验证明最优。当前V9/NumericFocus2运行中44没有稳定的单轮速度优势。旧44约17分钟/轮来自NumericFocus1及旧模型，不能沿用为当前V9的线程选择依据。

两例均全国31省、8760小时连续容量投资与运行LP，目标为年度系统成本最小化；决策包括容量、发电、储能、水库和输电，既有约束不变；功率GW、电量GWh、碳MtCO2、目标million CNY/year。2030/2040的负荷、碳边界、容量继承及DAC可用性不同，不能作为相同LP的A/B试验。

两份实际solve_report导出的solver_parameters逐键比较，唯一差异为Threads48→44，均Method2/NF2/ScaleFlag2/BarConvTol1e-4/Crossover0，无TimeLimit/SoftMemLimit。Presolve日志均2。CPU均AMD EPYC9554，节点分别m4cm1708/m4cg1701；2030运行时逐线程绑定未核实，不假设NUMA条件相同。两例Slurm均64CPU/750G/billing64，44不直接少付4核费用；这里比较的是求解器线程。

|指标|2030 Base V9，48线程|2040 Base V9，44线程|
|---|---:|---:|
|Job ID|4614693|4682935|
|Gurobi / 科学QC|OPTIMAL / HARD_FAIL|OPTIMAL / HARD_FAIL|
|Barrier轮数|348|605|
|求解器Runtime|451391.62秒，5.2244天|843709.49秒，9.7640天|
|Slurm墙钟|5天6小时21分22秒|9天19小时19分8秒|
|Presolve|4.7568小时|8.8171小时|
|Ordering|1.2253小时|1.1694小时|
|iter0→终轮均值|20.5687分钟/轮|22.2451分钟/轮|
|Slurm MaxRSS|678.1063 GiB|625.5861 GiB|
|原始行数 / 列数|50,907,233 / 41,458,383|50,907,233 / 41,458,383|
|原始非零元|484,299,937|485,386,301|
|Presolved非零元|392,787,298|396,875,851|
|Factor NZ|3.305e10|3.333e10|
|Factor Ops|1.854e15|1.872e15|

内存统一采用Slurm采样口径。2040 GNU time最大RSS628.9092 GiB、进程树采样峰值628.847 GiB，与Slurm存在采样差异；内存差不能单独归因于线程数。Factor Ops只高约0.97%，不代表累计算法工作量或两个年份同样易收敛。

## 同迭代区间速度

计算式为原gurobi.log累计秒数的端点差：`(T_b-T_a)/(b-a)/60`，排除Presolve/Ordering。日志整秒打印，CSV额外精度用于复算。“同迭代区间”不代表同内部工作或同收敛阶段。

|迭代区间|48线程，分钟/轮|44线程，分钟/轮|44耗时相对48|
|---|---:|---:|---:|
|10→39|19.3270|20.4362|+5.74%|
|50→97|18.1468|19.2589|+6.13%|
|50→200|19.8280|20.0424|+1.08%|
|200→300|22.3860|22.2792|-0.48%|
|300→348|21.1094|26.8795|+27.33%|
|10→348，较长共同区间|20.6596|21.7142|+5.10%|

10→348中位数为20.3333对20.8167分钟/轮，差2.38%；尾部昂贵轮次放大均值差。300→348的44每轮callback Work为5429.62，48为3414.92，增加59.00%，墙钟增加27.33%。10→348的平均Work仅高0.71%，但不同年份内部操作构成不同，不将Work/秒当硬件或线程因果基准。

2040历史采样中44线程忙碌、调度等待极少、swap/iowait/cgroup节流为0，慢轮伴随Work增加；没有DRAM带宽实测。详见`../base_2040_continuation_20260919/PERFORMANCE_CHECK_20260925.md`。

## 总耗时差的描述性拆分

日志终轮累计时刻差为843701−451382=392319秒（4.5407天）。日志迭代行、Barrier摘要和solve_report Runtime有数秒的记录阶段差，本拆分统一使用迭代行。

|时间项|2040相对2030增加|占日志总差|
|---|---:|---:|
|iter0之前准备时间差|14298秒，3.9717小时|3.64%|
|共同iter0→348时间差|21557秒，5.9881小时|5.49%|
|2040额外iter348→605|356464秒，99.0178小时|90.86%|

这是时间账而非因果分解。主要差异表现为多257轮；不能说少4线程让总耗时近乎翻倍，也不能承诺48线程可让2040五天完成。线程可能改变浮点路径与迭代数，本数据无法隔离这种影响。

旧Base4496031的10→39为17.2264分钟/轮，Thermal4533060为17.1948；此前“新48比旧44慢12.19%”算术仍成立，但NumericFocus、模型/缩放和节点不同。旧Base44仅40轮后按历史授权停止，Thermal44最终NUMERIC无解，不能据早期速度判断完成当前模型更快，也不能反推线程导致失败。

## 决策、局限与下一步

- 速度优先暂选48。44可保留作内存压力下的候选，但同LP内存收益尚未验证；两例均未OOM。
- 如需定论，应固定同一个全年归档MPS、Gurobi版本、其他参数、节点及CPU/NUMA/内存绑定，串行比较44/48，记录同预设区间的Runtime/Work/残差/峰值内存，必要时交错重复。短程只验证吞吐，不证明全程收敛更快。本轮未启动该试验。
- 2040 Slurm COMPLETED、2030 FAILED2对应不同入口接受策略；两者Gurobi均OPTIMAL而科学QC均HARD_FAIL，不能据退出码称44质量更好。
- 精确下一步为用户选择配置及是否需要同LP配对。本轮不改当前44配置，不启动2050/Stage B/额外基准，保留所有结果与未接受标记。

官方文档说明Barrier可并行化排序和因子分解，但线程收益依赖模型、内存和NUMA条件，增加线程不保证整体提速。这只提供解释框架：[Barrier并行](https://support.gurobi.com/hc/en-us/articles/360013419951-Does-using-more-threads-make-Gurobi-faster)，[线程与内存](https://support.gurobi.com/hc/en-us/articles/42058344459409-Managing-Threads-and-Memory-Usage-in-Gurobi)。

## 复现与验证

离线复算：`python supplementary_materials/reviews/thread_comparison_20260930/analyze_threads.py`。Python标准库，无Gurobi依赖，不调用optimize。

首次采证另加`--collect --remote-base <cloud release parent>`，默认SSH别名paracloud-bscc-a8，只读取日志和squeue/sacct。来源完整路径、UTC、Git和SHA见manifest.json。2030/2040日志与telemetry本次从服务器读取，旧44日志复用已采证文件；未下载或重验大MPS/解向量。

输出：evidence/、manifest.json、comparison.json、windows.csv、iterations.csv、analysis.stdout.txt及本报告。全部证据SHA、连续迭代、累计时间单调、终态轮数和实际参数差异检查PASS；2030/2040各349/606条日志，与callback数量一致。不新增随机实验/种子。采证器初次因服务器Python3.6不支持capture_output失败，改兼容PIPE后成功，无云端写入。
