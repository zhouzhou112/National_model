# 2026-09-13 Crossover设定更正与无交叉转换复测

用户指出原定Crossover=0是正确的。此前Stage A默认和当前Thermal profile都是
`Method=2 / Crossover=0 / SolutionTarget=1`；Thermal参数来自本轮稍早的只读回读，未被修改。
本地修复候选v1到v9使用Crossover=2/Basis1清理内点解并通过完整QC，这是真实算法变化。
把这套本地设置带入待启动全国诊断、再把它称为沿用既定方案，是本次需要纠正的配置混用。

## 本轮更正

- `scripts/probe_full_year_numerics.py`现在从既定云资源配置读取Crossover=0，显式设SolutionTarget=1。
  继续使用Gurobi44线程、Slurm64CPU/700G、SoftMemLimit=null；不自动执行Crossover或Stage B。
- 保留NF2、Scale2、Presolve2，诊断入口的1e-6仅为尚未通过验收的测试值，不是已选定生产容差。
  `CrossoverBasis=1`留在历史v9配置中，但在Crossover=0下不启动基转换。
- 源v9物理/数值配置保留作历史实验基准；运行时覆盖值明确进入plan/effective_config和实际参数回读。
  科学配置身份不变。水库数据、目标、单位和QC阈值均未修改。
- 上轮cross2包保留，撤回其“按原定Stage A可进入下一阶段”的资格结论。
  新cross0包只用于复现诊断，未获得科学验收，不建议据现有结果开始长周期全国求解。

## 同模型本地无Crossover复测

采用v9夏季24h/start3960、全年水库界、全年CF送出设计，本地8线程/8GB，冷启动。
两份新MPS与上轮cross2三组逐字节相同，SHA256：
`c8b0c338f86b550e59d42f48e6a5271f1c8b64fb0e6de3b1d78eef393c8e75c3`。
决策仍为发电、容量、储能、水库库存/释放和输电等连续变量，目标仍为原年化系统成本；
完整31省结构及选取24小时的供需/安全/水力约束保持不变；短窗不代表全国8760最优解。

| Crossover | BarConvTol | Barrier轮数 | 求解秒数 | 原模型最大行残差 | 完整QC |
|---|---|---:|---:|---:|---|
| 0 | 1e-6 | 83 | 23.143 | 1.164401e-3 | HARD_FAIL |
| 0 | 1e-4 | 74 | 21.176 | 1.313795e-3 | HARD_FAIL |
| 2（上一轮对照） | 1e-6 | 83 | 26.347 | 1.973532e-11 | PASS |
| 2（上一轮对照） | 1e-4 | 74 | 31.189 | 1.291056e-11 | PASS |

无Crossover两组均为Gurobi OPTIMAL、strict_acceptance=false。最差行均为
`reservoir_independent_hourly_transition[345,0]`；另有跨省同时双向流和城市网络QC未过。
1e-6目标2134775.5787906684，1e-4目标2134847.9484086363，cross2严格解2134775.3913311483。
目标值接近不能替代原单位物理可行性检查；当前不能宣称无Crossover方案数值问题已解决。
此次没有完成修复版Crossover0/1e-8的同窗口完整QC对照，不以旧cross2通过替代它。
局部结果不能证明全国必须开启Crossover，也不能证明关掉即可稳定求解。

官方语义：Crossover=0关闭交叉转换；放宽BarConvTol减少Barrier精度。
因此上一轮“放宽容差增加Crossover工作”的解释只适用于Crossover已启用的对照。
来源：[Gurobi参数文档](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html#parametercrossover)。

## 实现验证与失败记录

- 启动入口5项测试PASS（0.500s），默认dry-run和Gurobi实际参数回读均确认为44线程/0/1/无软限。
- 本地诊断脚本复制到本目录，修复无基解读取Kappa时未捕获AttributeError的问题。
  该属性不可用不是NUMERIC；两次成功复测均从头求解，没有继承基或向量。
- 第一次默认D:/anaconda/python.exe缺gurobipy，随后使用已验证的RL环境；失败日志保留。
  第二次Barrier已结束但Kappa读取失败、未产出QC，保留为不完整证据。
- 单元测试最初模块路径不适用；改用discover后Windows子进程编码异常，显式PYTHONUTF8=1重跑，
  最终5项无异常通过。历史失败不算科学结果，也未覆盖日志。
- 新包197文件全部与tar条目、当前源码哈希一致；旧cross2包哈希也重新核对，保持原样。
- 本轮没有连接服务器、提交新任务或调整Thermal。服务器状态仅引用稍早的只读快照。

Git基线`0a03cc452e95d158f36923ceb5210267979b6234`，未提交。
精确改动见`crossover_contract.patch`；命令见`commands.json`，输出见`probes/`、
`comparison.json`、`parameter_readback.json`、`default_dry_run/`及`delivery_manifest.json`。

新的本地诊断归档：`cloud_gate_20260913_v9_t44_cross0_tol1e6.tar.gz`，SHA256
`ddcc5f6e25e06d0fef01e12eef50d5b118489654c60aa10e34a1792d2c5d07b7`。它只纠正运行约定，不表示资格通过；旧cross2包不得再被当作当前Stage A启动包。

下一步先在本地定位上述水库平衡行的无Crossover残差及小双向流，补充对应原单位诊断；
固定Crossover0验证修改是否实际改善，不能默默打开Crossover2或放宽验收阈值。
在这些已知失败项闭合前，不启动新的多日8760生产任务，不把时间更短或OPTIMAL当作通过。
