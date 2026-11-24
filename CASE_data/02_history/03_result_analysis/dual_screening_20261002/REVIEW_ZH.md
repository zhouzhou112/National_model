# Base 对偶筛选、下一轮情景及交接整理

日期：2026-10-02（英国）。Git 基准 `0a03cc452e95d158f36923ceb5210267979b6234`，本轮开始前已有大量未提交改动。本轮不修改核心物理模型，不干预在跑 Base，不提交新的云端全年作业。

## 判断

**值得继续做大窗口验证，但当前尚不能认定能大幅提速，也不能直接用于正式全年结果。** Base 对偶适合作为初始候选集的启发信息；保持完整 LP 最优性的关键是本情景的重新定价、负价列加回、迭代重求解和质量验证。0.1/0.2 不是数学安全阈值，也不是永久删站的依据。

本轮已经独立实现并跑通 24h 联合模型的“初筛→定价→加回→重算”闭环，完整物理 QC 通过，最终目标与未筛选模型相对差 `6.54e-15`。不过，筛选需要两轮，共 `43.839s` 求解，完整模型只需 `23.595s`。这不是负面的全年结论：24h 的 Dense cols 都为127，尚未出现全年数万稠密容量列的结构；但它明确否定了“列数减少就已经证明提速”的推论。

固定服务器开始可以通过本机转发登录，上传独立测试包时转发失联；2016h 尚未启动。已请求恢复连接，本地已完成168h五轮因子对照，Factor Ops增加2.29%、前五轮调用时间减少6.13%，未达到既有因子/每轮晋级参考；2016h证据缺口不得用短窗结果代替。

## 输入与方案还原

- 已完整阅读用户粘贴的 Claude 对话、`../claude_workspace/reports/rc_screen_2030_REVIEW_ZH.md`、定价脚本和原始站点 CSV/汇总文件。定向检索 `.claude/projects` 未找到本次对话的新增正文；没有据此访问无关对话。
- 来源为2030 Base的原始MPS和保存的BarPi。BarPi有 **50,907,233** 个约束分量；**41,458,383** 是变量/BarX长度，不能混写。此向量用于原始约束行序，不可直接套到新增柔性约束后的矩阵。
- 源CSV的SHA256为 `fe5d87a2adc6f5d6b8ad21606c571979312c1f632780fcdc9ea7500b7f0f2368`。本輪重算见 `source_screen_audit.json` 和 `source_screen_margins.csv`。
- 范围是36,686个 `grid_uid × technology` 风光候选列对，不是36,686块互斥土地；包括 onwind/offwind/upv/dpv。波浪、水电等本轮没有筛选。

对于本模型，`capacity = floor + new`。需要定价的是一对共同增加的列：

```
r_build[z] = RC(vre_capacity_gw[z]) + RC(vre_new_gw[z])
           = c_cap[z] + c_new[z] - (A_cap[:,z] + A_new[:,z])^T pi
ratio[z]   = r_build[z] / (c_cap[z] + c_new[z])
```

容量记账等式的对偶在这个和中消去。只读取被固定的 `vre_new` 的 RC 可能受这条记账等式的任意对偶分配影响；本轮使用列对之和，并抽样用原始列系数独立重算。严格保留 `capacity_floor`，初筛只把遗漏站点的 **new UB置0**，不删除既有电站、不改原始潜力、不改任一物理约束。

`m=0.2` 表示保留在 Base 这一组对偶价格下、净边际缺口不超过自身年化技术容量成本20%的列。分母不是每站全部独立接网成本；当前技术容量成本按技术统一，接网、送出和城市年度网络通过相应变量及约束的对偶间接影响定价。这个量也不应直接当作市场电价乘发电收入。

潜力上限在Base优化和价格形成中已经起作用，在情景LP里继续保留；最终遗漏列数值误差的系统影响还必须按可新增容量加权，例如 `Σ headroom[z] * max(-r_build[z],0)`。仅说每列误差“小于一个epsilon”，不能自动保证全系统目标误差很小。

## 对 Claude 结论的必要更正

| 原说法/隐含判断 | 本轮核验 |
|---|---|
| 0.2保留14170，未误删>1MW站点 | 数量成立，但遗漏站点的原Base新建量合计0.969925MW，9站>1kW；不能说没有任何影响 |
| 1821站只是1e-8GW噪声 | 这1821站在1kW–1MW之间，合计22.3571MW，最小1.0003kW、最大977.408kW；原描述单位/范围错误 |
| Base已建站定价合理，因此BarPi可靠/可发布 | 可作初筛一致性证据；Base原始QC/对偶质量未过，不能据此发布土地价格或给完整最优性证书 |
| 一次重新定价就能保证等价 | 需要迭代，可能多轮；restricted infeasible也不能证明完整LP不可行。最终要有本次情景的可行性、对偶质量和全候选定价 |
| 六类容量列约40.8k，可当Dense cols计数 | 是原矩阵列族统计；Gurobi实际Dense cols为另一种内部分类，不能直接相减作为实测因子规模 |
| 年度行拆分后AggFill=10保证不被合回 | 是待验证假设；必须看真实presolve与factor结果。本轮不同时改年度行，以免混淆筛选效果 |
| 用Base2040只解目标年是既定路线 | 旧路线图写的是Base2050→2060的条件互补设计；用户本轮已明确选联合独立四年路径 |

“已建到上限”的负定价只有在适当的对偶/界约束解释下才对应放宽潜力的局部边际价值；不能直接当每平方公里土地价格。两个重复容量上界、单位换算和对偶退化也需要处理。

## 独立测试与结果

共同科学设置：V9当前数据和修正水库，31省/337城市/0.25°站点；连续小时，GW/GWh/MtCO2/百万2025CNY；原成本、碳、水力、输电、RUC、备用、惯量、安全约束全部保留。短窗遵循现行代码：年度流量边界按 `hours/8760` 缩放，年化容量成本不缩放。测试不输出可接受的跨年planning state。

本地环境：Windows、RL Python3.10、现有独立Gurobi13.0.2模块；8线程、8GB SoftMemLimit、Seed0。24h采用Method2/NumericFocus2/BarConvTol1e-8/Crossover2，600s求解上限。168h因子试验采用Cross0/1e-4/BarIterLimit5，900s上限。数据和模型身份见每个目录的`input_manifest.csv`、`effective_config.json`和`run_environment.json`。

| 24h/start3960测试 | 初始可扩展候选数 | 求解秒数 | 加回数 | 最终结果 |
|---|---:|---:|---:|---|
| Base完整 | 34439 | 22.767 | 0 | OPTIMAL，物理QC PASS |
| 联合完整 | 34439 | 23.595 | 0 | OPTIMAL，物理QC PASS |
| 联合0.2初筛 | 14167 | 22.060 | 100 | 目标已匹配，但遗漏列最小rc为−1021.354，定价未通过 |
| 联合加回后 | 14267 | 21.779 | 0 | 遗漏列最小rc为+3.02247，物理QC与数值定价通过 |

14167不同于源统计14170，是按当前模型实际可扩展上界计数；V9还对极小headroom作现行10kW清理，不能用源表有空间计数替代实际变量界。

验证细节：

- 完整与初筛原始MPS的ROWS/COLUMNS/RHS/目标等段逐段SHA相同；仅20,272个`vre_new_gw`的界改变，全部置0。原始容量floor和所有其他变量界不变。
- 最终目标差 `1.3969838619e-8 million CNY`，相对 `6.54391018e-15`；列系数重算RC与求解器RC之和最大误差 `1.14e-13`。
- 初筛与完整目标已相同但仍有100个负价列，这体现了退化/对偶选择下，某个restricted最优对偶不一定能证明完整问题最优；不等于这100站都会实际建设。加回使最终对偶验证闭合。
- 五项独立SciPy/HiGHS测试覆盖：情景变化使被筛站重新有价值、加回恢复最优、记账对偶消去、RC与界对偶一致、潜力加权误差。
- 24h全部VRE新增和四类柔性签约均为0，不能从此测试推断长期投资/柔性收益。原始+筛选最终解均是同一短窗工程问题的数值结果。
- 首次Windows压缩MPS写出失败发生在求解之前；保留`local_base24_full`失败目录，改用普通MPS与POSIX路径后在v2目录完成。没有覆盖失败证据。

168h/start2880、联合情景、同机8线程、5轮Barrier的补充对照已经完成：

| 指标 | 完整候选 | 0.2初筛 | 变化 |
|---|---:|---:|---:|
| Presolved nnz | 8,392,491 | 6,417,511 | −23.53% |
| Dense cols | 233 | 233 | 无变化 |
| Factor NZ | 1.296e8 | 1.298e8 | +0.15% |
| Factor Ops | 9.651e10 | 9.872e10 | +2.29% |
| 优化调用总时间（含预处理） | 43.112s | 40.470s | −6.13% |
| 第2–5轮平均时间 | 3.384s | 3.159s | −6.64% |
| Work | 108.842 | 95.697 | −12.08% |

两者均为ITERATION_LIMIT/status7、无可用解；不能比较最终目标或宣称QC通过。单次配对、路径不同且时窗短，耗时变化不当作稳定加速倍率；按既有“Factor Ops下降至少5%或每轮下降至少10%”的晋级参考，也未达到。重要的结构证据是：矩阵非零减少没有转化为因子规模改善；仍需2016h后风光列真正被识别为稠密列的对照。

最新机器可读对照：`paired_results.csv`、`paired_identity_audit.json`。这组168h有限迭代不替代已授权但未完成的2016h资格。

## 2016h试验与正式接入的边界

固定服务器最初确认：t550、96逻辑CPU、123GiB内存、约99GiB可用，有其他用户进程；现有checkout为ba8e09f，与当前V9不一致。因此准备新的隔离代码/输入包，而没有更新旧repo。包261文件、82,711,005bytes；SHA身份清单`experiment_manifest.json`。传输中途SSH转发失联，未解包、未启动求解。仅终止本机属于本试验的卡住SCP客户端；云端2050没有任何控制操作。

恢复后依次完成：校验当前版本实验包；使用同一节点/CPU绑定/输入/2030年/start2880/2016h，先完整再0.2初筛，12线程、72GB SoftMemLimit、至多5400s求解和7200s总墙钟，5轮Barrier。只允许一个成员在跑；可用内存不足90GiB不启动，运行时不足12GiB只停止该新建试验进程组。记录presolve、Dense cols、Factor NZ/Ops、每轮Runtime与Work、RSS、主机压力。该方案不触碰云端在跑Base。

恢复用的修订包已另外冻结为`experiment_v2.tar.gz`（266文件、82,718,241bytes），旧部分上传包不使用、不覆盖；可用`install_remote.py <NEW_REMOTE_ROOT> --archive experiment_v2.tar.gz`核验解包，再由`run_remote.sh <NEW_REMOTE_ROOT> <CASE_NAME> --mode factor --scenario case3_thermal_ev_v5 --hours 2016 --start 2880 --threads 12 --memory-gb 72 --time-limit 5400`运行一个成员。筛选成员另外指定`--screen-csv <NEW_REMOTE_ROOT>/source_screen.csv`。所有解包目标与结果目录须全新；转发未恢复前不自动重试提交。

尚需闭合的工程项：正式配置/输入身份、范围受限的初筛入口、所有年份稳定站点ID对齐、全列定价循环、restricted不可行时恢复候选、每轮遗漏改善界及总成本记录、完整物理/对偶QC、跨年状态接受。这一轮只在隔离试验脚本中实现筛选，未把未经长窗验证的入口接入生产runner。

最终身份核验：257份核心源码、科学配置和输入与本轮起始冻结清单逐SHA一致；实际执行的探针源码已按各run中记录的SHA恢复并核验，见`executed_probe_source.py`。当前runner仅比实际测试版本多一项CLI参数范围检查。Python编译、shell语法和`git diff --check`通过。机器判定与交付SHA见`decision.json`、`delivery_manifest.json`。

## 下一轮情景、文档与清理

用户已确认联合情景完整独立2030→2040→2050→2060。下一轮每年继承本情景自己的cohort，不混入Base后续年的状态；单EV、单冷热酌情补为消融。细节在根目录`SCENARIO_EXECUTION_PLAN_20261002.md`。

旧V5 overlay parent不匹配V9。本轮仅生成`scenario_v9_diagnostic.json`和`scenario_parent_migration.json`，所有物理overrides保持一致，原配置保留。旧数值profile不能当V9全年已验证配置。

`CODEX_HANDOFF.md`已将当前快照与历史快照分开，旧条目不删除；README、旧情景架构、旧路线图、配置说明增加当前入口。`DOCUMENT_STATUS_20261002.md`列出权威入口、历史证据和不可混用的代码版本；保留失败日志、原MPS、向量和源快照。

物理删除候选仅6文件，见`deletion_candidates.csv`；按用户提供AGENTS三.8的明确规则，已列出并请求确认，未获确认前保留。

## 当前Base的重要新观察

只读观察2050/4844528仍RUNNING、Restarts0、64CPU/750G/UNLIMITED；从日志116到117轮，PInf `3.72e3→4.40e11`（约1.18e8倍），Compl `416→5.15e11`（约1.24e9倍）。读到135轮仍为PInf9.05e10/DInf5830/Compl9.21e10。该数值跳升已写入最新交接；只说明迭代明显恶化，没有足够证据判定唯一原因或最终失败。本轮严格遵守不暂停Base。

## 复现

```powershell
python supplementary_materials/reviews/dual_screening_20261002/audit_source_screen.py
python supplementary_materials/reviews/dual_screening_20261002/test_pricing_mechanism.py
$env:PYTHONPATH=Join-Path (Get-Location) 'output/portfolio_runtime_gurobi13'
$env:CISPO_WAVE_ROOT=Join-Path (Split-Path (Get-Location)) 'wave_energy'
$env:OPENBLAS_NUM_THREADS='1'
& C:/Users/ZZ/.conda/envs/RL/python.exe supplementary_materials/reviews/dual_screening_20261002/run_screen_probe.py --mode solve --scenario case3_thermal_ev_v5 --hours 24 --start 3960 --threads 8 --memory-gb 8 --time-limit 600 --screen-csv ../claude_workspace/evidence/rc_screen_2030/vre_site_reduced_costs.csv --output <NEW_DIRECTORY>
python supplementary_materials/reviews/dual_screening_20261002/summarize_experiment.py
```

对照完整模型时省略`--screen-csv`；168h因子对照使用`--mode factor --hours 168 --start 2880`。任何输出目录已存在即拒绝重用。以上Python可执行路径仅记录本机复现环境，脚本自身没有把该路径硬编码为运行依赖。

理论依据：Gurobi将Pi定义为当前连续解的约束对偶，BarPi为最好Barrier迭代的对偶；取得属性本身不证明通过本项目的科学质量门槛。[官方属性定义](https://docs.gurobi.com/projects/optimizer/en/current/reference/attributes/constraintlinear.html)。约束不变、遗漏列定价并反复加入负价列属于restricted master/column generation的标准思路。[Gurobi官方讨论](https://support.gurobi.com/hc/en-us/community/posts/360054740311-Column-Generation-Explanation?sort_by=votes)。本轮采用现有完整矩阵固定变量的原型，不声称已实现省去完整建模内存的真正按需列生成。
