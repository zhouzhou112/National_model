# 2026-09-13 下一阶段测试启动前复查

## 决策

启动前本地检查通过，可以进入**单次、有时限的2030全国8760小时数值诊断**。
这不是正式长跑资格，也不是启动2030–2060连续求解的许可或证据。
本轮实际启动并完成的是本地24小时冷测试，另做了集群只读环境检查、单线程单变量许可烟测和`sbatch --test-only`。
新包只在本地准备，没有上传、正式提交、停止或修改既有作业。

采用配置`config/optimization_numeric_dac_by_year_v9.json`，2030 DAC关闭，2040/2050/2060恢复可选。
模型和输入仍为前轮已验证的修复方案；本轮不增加新的数值截断、变量换算或容差放松。
Git基线`0a03cc452e95d158f36923ceb5210267979b6234`，未提交；既有无关dirty保持。

## 1. 求解参数已实际回读

以下由`configure_gurobi`写入后通过`model.Params`回读；不只检查JSON文字。
Gurobi本地与服务器均为13.0.2，服务器Python3.10.20。

| 参数 | 本地冷测试 | 计划中的全国诊断 |
|---|---:|---:|
| Method | 2（Barrier） | 2 |
| NumericFocus | 2 | 2 |
| ScaleFlag / Presolve | 2 / 2 | 2 / 2 |
| BarConvTol | 1e-8 | 1e-8 |
| Crossover / CrossoverBasis | 2 / 1 | 2 / 1 |
| SolutionTarget | 0 | 0 |
| FeasibilityTol / OptimalityTol | 1e-6 / 1e-6 | 1e-6 / 1e-6 |
| MarkowitzTol | 0.01 | 0.01 |
| Threads | 8 | 32 |
| TimeLimit | 900秒 | 900秒 |
| SoftMemLimit | 8 GB | 550 GB |

保留自动Ordering、自动BarCorrectors/BarHomogeneous、Aggregate=1、Seed=0；
BarIterLimit仍为默认1000，不另设激进迭代中止规则。年度资源链接使用物理行，不带8192行缩放overlay，
也没有套用旧的NF1、BarConvTol=0.01、Crossover0或SolutionTarget1方案。

32线程为本次固定诊断资源设定，并没有证明其优于16线程。不同时启动多套参数竞赛。
900秒为`optimize()`的总优化预算，包含其中预处理、ordering和crossover；Python建模及原MPS写出在其之前。
设置Slurm两小时总墙钟限制覆盖整个任务。TimeLimit可能略有超出才能完成终态计算，
SoftMemLimit也不是严格进程RSS硬上限，故Slurm申请700GiB，给Python数据及导出留余量。
这些参数语义核对了[Gurobi官方参数文档](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html)。

## 2. 本轮实际验证

- v9上一轮清单的28条哈希在开始前核对通过；三站修正水库输入CSV仍为
  `f8135eaffa2de77461912cba5216106f66e0b6207c8b6c381fd725339a378e94`。
- 全年输入检查PASS：31省×8760负荷、2030条水电站记录（其中620座为水库）。
  `validate-inputs-only`没有构建全国LP。
- 新增5项启动入口测试PASS：实际参数写入/回读、原MPS写出读回、退出码、dry-run、
  历史目录不可覆盖、参数赋值不一致检测及原子记录保护（合并于5个测试方法）。
  之前73项模型/年度DAC回归已经通过；模型生产代码本轮未改，未重复跑无新增覆盖收益的全套。
- **v9夏季24h独立冷启动**，起始小时3960，包含本次梯级毛刺所在时刻，使用真实全年水库界和完整年度CF送出设计。
  25.740秒、88次Barrier、OPTIMAL，完整QC PASS；最大原行违反`2.961187e-11`，
  界违反`6.111778e-12`，对偶违反`4.766575e-9`。没有复用基。
- 本轮MPS与v8同窗口原始MPS逐字节相同，SHA256
  `c8b0c338f86b550e59d42f48e6a5271f1c8b64fb0e6de3b1d78eef393c8e75c3`。
  这验证年度DAC日程没有改变2030这一个窗口的物理LP；不能外推后续年完整求解通过。
- 原始Matrix仍`3.7e-5 .. 24`，Objective`0.001 .. 3853.189876`；全年水库最大库存界18482.41654 million m3。
  不把此24h范围当作全国8760h完整矩阵范围。

## 3. 启动入口发现的问题与修复

原包仍指向v8，且全年诊断脚本存在“有日志但缺少复盘文件”的缺口。本轮修复
`scripts/probe_full_year_numerics.py`及新的本地包启动脚本：

1. 默认使用v9，限定2030/8760循环年，不会自动进入后续年份。
2. 原始MPS和实际生效参数在优化前保存；参数回读不符立即失败。只存算法参数白名单，不导出许可内容。
3. 用原子JSON记录构建/优化阶段和终态；普通Python异常也落盘。不覆写已有输出目录。
   硬杀/OOM仍可能只留下RUNNING阶段，必须结合Slurm状态判断，不能把缺少终态当成功。
4. Barrier记录同时保存原/对偶目标、相对目标差、可行性残差与互补量，不再只看某一残差下降估计接近最优。
5. `OPTIMAL+完整QC`才返回0；NUMERIC/不可行/QC失败返回2；限时/内存等未完成返回3。
   即使Gurobi找到部分解，TIME_LIMIT也不记为全年通过。错误终态不会伪装成Slurm成功退出。
6. 不额外调用`Model.presolve()`复制整个年度模型；从实际`optimize()`日志记录预处理和因子信息。
   保留原MPS用于精确复盘，不把单独预处理模型当作可直接恢复的科学解。
7. 本地压缩MPS首次写出测试失败，已改为原生未压缩MPS并完成读回；原失败记录保留为`launch_tests_attempt1.*`。
   测试子进程的UTF-8读取也已修正，最终5项检查全部通过。

## 4. 集群与准备好的包

SSH只读确认：分区`amd_a8_768`为UP，源release的数据、波浪和Gurobi路径存在，
旧Thermal作业4533060仍RUNNING，最后本轮读取耗时5-23:35:52，AllocTRES为64CPU/700G/billing64。
没有对它做停止、改参或目录修改。
服务器许可烟测只构建1变量、Threads=1、TimeLimit=10s，OPTIMAL，最终SSH退出0；不属于年度模型求解。
首次烟测LP本身通过，但PowerShell输入尾部换行使包装器出现NameError，修正输入结束行后重测通过，两次日志保留。

`sbatch --test-only`接受32CPU/700G/2h申请，但给出2027-09-30的远期调度估计，
该预测不可靠，不作排队ETA或计费保证。输出中的4609690是test-only模拟编号，**不是已提交任务**。
实际CPU/内存计费须按真实分配核对，不将32个Gurobi线程直接等同于最终收费核数。
首次只读环境查询遗漏shell变量导出而返回null，补上与真实启动脚本一致的`set -a`后路径检查全部通过；
原始两次查询日志均保留，没有把第一次查询误当运行环境缺失。

新包`cloud_gate_20260913_v9.tar.gz`，197文件，662562 bytes，SHA256
`dad108f8c38611ccee98db938b13ffb39ad35c4e89fa117b32bc6820b41a0f4a`。
包内使用新数据覆盖目录，旧数据只读链接，修正水库CSV单独复制。旧v8包保留；
当前新入口的变更不回写旧冻结证据。Slurm脚本通过`bash -n`，包内各文件逐项核验。

下一项实际全国测试应只提交这一个独立诊断：32线程、700GiB Slurm、550GB SoftMemLimit、900秒优化、2小时总墙钟。
目标是实际测量全国raw范围、presolve、factor规模和早期迭代；若预算全部花在预处理/ordering，结论为未完成，
不能判模型失败，更不能判全年数值健康。没有自动重试、自动延长或生产后继任务。

## 5. 复现与交付

全年输入检查（新目录）：

```powershell
python scripts/probe_full_year_numerics.py --config config/optimization_numeric_dac_by_year_v9.json --output-dir output/v9_prelaunch_input --validate-inputs-only
```

本轮实际本地冷测试参数：

```powershell
python supplementary_materials/reviews/numeric_prelaunch_20260913/run_numeric_probe.py --case cleaned_nf2 --config config/optimization_numeric_dac_by_year_v9.json --hours 24 --start 3960 --time-limit 900 --crossover 2 --spill-reduction --spill-positive-bound-floor 1 --cf-cutoff 0.01 --annual-water-bounds --tag _new_recheck
```

沿用项目Python/Gurobi环境及`CISPO_WAVE_ROOT`。本轮证据包括
`parameter_preflight.json`、`cold_probe_summary.json`、`launch_tests.json`、`full_year_input_check/`、
`server_environment.stdout.log`、`server_preflight.stderr.log`、`cloud_gate_manifest.json`及`delivery_manifest.json`。
本地已准备完成不等于全国作业已启动，也不等于全年验收已通过。
