# Base 2040续接、44/48线程比较与启动核验

核验时刻：2026-09-19 19:22 北京时间。Git基准 `0a03cc452e95d158f36923ceb5210267979b6234` + 既有dirty；本轮不提交Git，不改变生产模型源码。

## 结论与授权

用户明确要求续接2040、恢复44线程并先核实每轮耗时。作业 `4682935` 于2026-09-19 19:19:41提交、19:19:49放行、19:19:50启动，节点 `m4cg1701`，当前RUNNING，处于全年模型构建阶段，尚无Barrier迭代或收敛结论。
这覆盖历史交接中“未获授权不进入下一年”的操作限制；不把2030 QC改为PASS，不启动2050/2060、Stage B或其他情景。

## 线程耗时：观测确实较慢，因果尚未隔离

按各日志相同迭代区间端点累计秒数相减，除以迭代数；排除Presolve/Ordering，用 `compare_threads.py` 复算。

|案例|线程|NumericFocus|第10→39轮均值，分钟/轮|Factor Ops|
|---|---:|---:|---:|---:|
|旧Base 4496031|44|1|17.2264|1.881e15|
|新Base 4614693|48|2|19.3270|1.854e15|
|Thermal 4533060|44|1|17.1948|1.874e15|

新Base相对旧44线程Base慢 **12.19%**。第20→39轮为19.3982对17.1868分钟/轮，方向一致。
相对Thermal的第50→97轮为18.1468对17.1557分钟/轮。Base48后段200→300轮为22.3860分钟/轮，不能拿它直接与旧44线程Base早期作受控比较。
旧44线程Base只运行至40轮后按用户要求停止；其全程平均不能与新Base348轮平均视作相同区间。
三者模型、缩放、数值保护和节点不同，没有同一LP、相同NumericFocus和节点条件下的44/48配对证据。因此确认“本次观测每轮较慢”，不声称“48线程本身必然更慢”。本次按用户选择恢复44，不额外启动线程基准作业。

## 2040范围与运行配置

- 全国31省，完整8760小时，连续LP；容量投资、逐小时运行、碳排放、备用、惯量、水库/储能/输电约束沿用v9；目标仍为年度成本最小化。功率GW、电量GWh、碳MtCO2、目标million CNY/年。
- 2030→2040容量cohort继承及原技术寿命/退役规则；边界2030、规划年2040、间隔10年。按既有DAC分年配置在2040启用DAC；未增加新研究假设。
- 44 Gurobi线程；Slurm仍申请/实际分配64CPU、750GiB、billing64，不能误报为44计费核。
- Method2/NumericFocus2/ScaleFlag2/Presolve2/Aggregate1/BarConvTol1e-4/Crossover0/SolutionTarget1；FeasibilityTol/OptimalityTol仍1e-6。
- Gurobi TimeLimit/SoftMemLimit/MemLimit/WorkLimit均无限，Slurm UNLIMITED；不自动续接其他年份。
- 新profile使用现有engineering候选保全路线，`direct_nonbasic_scientific_acceptance=false`，不授予科学接受资格。求解数值参数相对2030唯一变化为Threads48→44。
- release：`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260919_base2040_v9_t44_m750_tol1e4_v1`；输出：`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260919_base2040_v9_t44_m750_tol1e4_v1/output_8760`。
- 模型源码从已完成2030的release复制：194个原repo文件逐一SHA一致，零差异；数据overlay链接原release。新增profile/启动与验证工具、独立继承状态副本，不改原2030结果。
- 模型配置：`config/optimization_numeric_dac_by_year_v9.json`；求解配置：`config/solver_profiles/barrier_checkpoint_full_year_cloud_2040_numeric_v1_threads44.json`。
- 原2030科学指纹937c3c6f…b0d4f0，2040解析后指纹9875d908…4f994017。年度参数按原配置解析，指纹不同正常。

## 续接时发现并闭合的单站容量越界

原始候选的完整数据preflight通过，但真实1小时构建在 `build_master` 报 `Inherited VRE capacity is outside the active site bounds`，故没有直接花费全年作业资源试错。

只读审计定位到一个网格 `G000021474::dpv`：2030原始导出确认外生存量5.709kW，按已有10kW阈值将该容量floor清为0；导出的new-build为11.217929509MW。2040加回外生5.709kW后，容量达到11.223638509MW，超过不变的11.219285567MW上限 **4.352942kW**。
因此该错误来自微小存量清理和跨年cohort累计的组合，不是本次数值求解器崩溃，也不宜误称为纯浮点舍入。

在 `/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260919_base2040_v9_t44_m750_tol1e4_v1/upstream_2030_bound_closed/planning_state_candidate` 建立显式未接受的状态副本。只将这个网格继承的new-build由0.011217929509069887 GW改为0.011213576566778299 GW；减少4.352942292 kW，使其加上2040外生存量后不超过原上限。调整小于已有10kW容量清理尺度。
86900条记录全保留，逐条比较恰好1条capacity_delta改变；原始2030状态/解/QC未修改，`candidate_unaccepted=true`、`scientifically_accepted=false`及原HARD_FAIL均保留。更新副本cohort/summary SHA并生成明确标注DERIVED_UNACCEPTED的完整性清单，保留原结果manifest和原状态来源SHA。
这是一项公开记录的容量状态近似，不是声称原始2030精确解不变，也不是全面解决跨年微小floor清理问题。源数据、容量上限、模型约束、QC阈值都未改变。未来通用跨年实现仍需统一清理量的cohort表示。

## 验证

1. 原候选与调整后候选分别通过实际全年输入预检查：67 PASS、3 WARN、2 INFO、0 HARD_FAIL。三项既有WARN仍保留。
2. 原始2030候选加载验证了来源QC/solve report/cohorts/summary与结果manifest完整性；无显式candidate允许标志时仍拒绝加载。调整后副本的所有文件与来源SHA也通过。
3. 调整后真实2040一小时模型构建通过：80104行、238529列、452584非零；未调用optimize，不是全年收敛资格。
4. 真实全年runner以两条Gurobi年度行fixture走通候选状态、2040、工程入口与原模型归档路径；不求解、不写accepted planning_state。
5. Gurobi参数回读确认44线程/NF2/1e-4/Cross0与无限制设置。
6. 实际计算节点Gurobi13.0.2许可小LP PASS、7项启动回归PASS、续接合同PASS；可用内存约730.6GiB，实际申请/计费吻合。正式run_scope确认2040/2030/8760及工程候选继承。
7. 新release Bash语法、源文件SHA、sbatch --test-only通过；held提交核对资源后放行。

准备阶段的验证工具修正也保留：默认physical_v1字段使用get读取；第一次状态副本缺少完整性manifest，保留在preparation_history并补齐完整派生清单。另一次SSH建连超时后确认没有输出才重试。这些均发生于作业提交前，不是全年求解失败。

## 复现与后续

本目录 `compare_threads.py` 可安全重算历史比较；`collect_evidence.py` 只读取证。`deploy.py` 的prepare/preflight/validate/submit/release是本次操作记录，有目录/已提交标志保护，不要为了查看状态再次提交；只用 `deploy.py status`。
`prepare_bound_closed_state.py` 记录一站状态调整，`validate_2040.py` 记录真实小构建及入口验证，`evidence_sha256.json` 固定采证文件身份。原始日志与线程比较详见 `evidence/`、`thread_comparison.json`。

精确下一步：只读检查job4682935的build_report、原MPS/PRM归档、gurobi.log的Threads44与矩阵/Ordering/Barrier及资源曲线；不重复提交、不自动改参/停止、不启动2050或Stage B。2040启用DAC且继承容量后LP会改变，当前没有其完整矩阵或峰值内存实测，不给完成时间保证。
