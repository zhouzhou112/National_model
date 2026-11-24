# 8760h 对偶初筛五轮 Factor 配对：最终报告

**判定：通过本次 factor-screen 门槛。** 初筛S第2–5轮平均674.580974秒，完整F为1110.308785秒，S/F=60.7562%≤75%；Dense cols从37,678降至17,413（下降53.7847%），达到预期16–18k，未触发“Dense cols无明显下降则封存”的否决条款。

这只证明本组真实8760h LP前五轮中每轮计算代价下降。两者Gurobi均status7、BarIterCount5、Iteration limit reached；没有收敛、科学QC、影子价格或规划状态结论。按任务书第5节，**没有自动启动全年case3科学情景；正式采用、遗漏列重新定价与加回重解仍待另行授权**。

## 实验范围与终态

- 情景：case3_thermal_ev_v5，V9显式派生配置；planning_year2030、boundary2025、8760h/start0，逐小时周期边界，31省与原V9空间结构/单位沿用。决策变量、目标函数、约束和数据不变，S只限制未保留站点的vre_new上界为0。
- 保留既有连续LP的风光/水电/火电/储能/输电容量、小时运行和柔性服务签约决策；目标仍最小化年度系统总成本（million 2025 CNY/year），既有负荷平衡、备用/惯量、碳排放、储能SOC及水库水量等约束不变。功率/容量GW、电量GWh、时间步长1h；风光0.25°网格，水电坝址及原省/城市电网结构沿用。输入为冻结V9技术经济/资源/负荷/CF/水文/波浪与V5冷热/EV数据；本报告的输出指标是Factor规模、Runtime秒、Work和RSS，不是规划装机或发电量。
- 原始两LP均54,217,462行、43,761,608列、501,902,601非零；F保留全部36,686站原有边界，S按grid_uid × technology一对一对齐后保留14,167个当前可扩展站，20,272个正headroom列置零，累计限制headroom39,341.39949215136 GW；已有容量下界不变。
- 两节点均AMD EPYC9554、128物理/逻辑核、amd_a8_768，实际AllocTRES cpu64/mem750G/node1/billing64；Gurobi13.0.2、48线程、Seed0。
- 两成员实际参数全部一致：Method2、NF2、Scale2、Presolve2、Aggregate1、Crossover0、SolutionTarget1、BarConvTol1e-4、BarIterLimit5、BarHomogeneous−1；TimeLimit/SoftMemLimit/MemLimit/WorkLimit均无限，Slurm无限时且no-requeue。
- 两成员均COMPLETED/0:0，stderr为0B，原release_files.sha256终态重验通过；没有改动、停止或重提4844528，没有额外云作业。本轮终态阶段没有本机模型求解或测试。

|成员|job id / 节点|开始（英国）|结束（英国）|Slurm wall|
|---|---|---|---|---|
|F完整|4981130 / m4cg1707|10月5日18:12:35|10月6日02:56:31|8:43:56|
|S初筛|4981131 / m4cg1801|10月5日18:12:35|10月6日00:21:32|6:08:57|

终态原始证据：[status_20261006T154830Z/](status_20261006T154830Z/)，共55份取回文件逐bytes匹配远端SHA。精确scheduler记录及无科学产物清单见[terminal_readonly_audit.json](terminal_readonly_audit.json)。

## 配对指标与逐轮代价

|指标|F完整|S初筛|变化/口径|
|---|---:|---:|---|
|Presolved rows|39,598,998|39,581,725|-0.04%|
|Presolved cols|35,912,426|35,714,859|-0.55%|
|Presolved nnz|413,036,312|317,658,492|-23.09%|
|Dense cols|37,678|17,413|-53.78%|
|AA' NZ|7.561e8|6.608e8|-12.60%|
|Factor NZ|3.531e10|2.539e10|-28.09%|
|Factor Ops|2.055e15|1.070e15|-47.93%|
|Presolve / s|17762.13|10574.27|-40.47%|
|Ordering / s|4749.69|4711.41|-0.81%|
|第1轮 / s|658.135570|392.039198|-40.43%|
|第2–5轮均值 / s|1110.308785|674.580974|-39.24%|
|第2–5轮平均Work|2538.105121|1640.193927|-35.38%|
|iter5累计Work|122327.981116|72740.243860|含此前预处理，不等于五轮增量|
|solver_end总Work|123337.327662|73279.062364|含收尾，不作为每轮代价|
|Slurm MaxRSS / GiB|695.121|660.091|调度采样|
|GNU time峰值RSS / GiB|705.371|680.804|-3.48%|
|Slurm elapsed|08:43:56|06:08:57|五轮测试总wall；不外推全年|

计时使用callback Runtime精确值：第i轮=Runtime_i−Runtime_(i−1)，第2–5轮均值=(Runtime5−Runtime1)/4，排除Presolve、Ordering及iter0前开销。Work同样差分。Gurobi文本秒级时间独立复算均值F1110.25s/S674.75s，与精确口径在整数日志分辨率内一致，不改变判定。Factor统计按日志显示精度记录，不能增加虚假有效位。

|轮次|F秒|S秒|F Work增量|S Work增量|
|---|---:|---:|---:|---:|
|1|658.135570|392.039198|2154.913019|1411.905790|
|2|781.829807|640.822125|3351.746258|1368.703455|
|3|1268.500569|640.844539|2609.314081|1369.815503|
|4|1194.168635|670.518070|2095.122033|1619.640691|
|5|1196.736129|746.139163|2096.238115|2202.616057|

源码/输入/参数与原LP非边界部分一致，加上Dense下降53.78%、Factor Ops下降47.93%、Factor NZ下降28.09%，支持“被固定候选减少进入因子分解的稠密容量列，从而降低每轮代价”的机制。没有把短窗结果替代8760，也没有把本次39.24%的前五轮每轮降幅外推为完整求解倍率：后续轮数、重新定价与加回重解代价均未测量。

RSS分别报告Slurm采样与GNU time峰值；二者取样方式不同。monitor进程树峰值F705.154GiB/S679.566GiB另保留在solve_report。callback MEMUSED/MAXMEMUSED是另一个内部记账指标，不当作RSS，也不据其与物理内存的差异推断OOM；实际Slurm均正常终态，GNU time Swaps均0。

## 逐轮目标与残差（仅记录）

以下严格转录Gurobi文本日志显示值。callback BARRIER_PRIMINF/BARRIER_DUALINF与文本列数值不同，因此原始callback CSV另存，**不混用两种残差口径，也不猜测差异原因或评估五轮收敛**。例如F iter0文本PInf/DInf为1.23e11/82.9，而callback约3.14095e11/3.56829e7。

|成员|轮次|P|D|PInf（log）|DInf（log）|Compl（log）|
|---|---:|---:|---:|---:|---:|---:|
|F|0|4.44832020e+12|-1.87427991e+13|1.230e+11|8.290e+01|5.360e+09|
|F|1|4.34074987e+12|-1.87970644e+13|1.200e+11|4.210e+03|5.180e+09|
|F|2|4.15497688e+12|-1.88140059e+13|1.150e+11|4.330e+03|4.970e+09|
|F|3|3.92590120e+12|-1.88306523e+13|1.090e+11|4.230e+03|4.740e+09|
|F|4|3.80724328e+12|-1.88474391e+13|1.060e+11|4.120e+03|4.590e+09|
|F|5|3.66998002e+12|-1.88538342e+13|1.020e+11|4.110e+03|4.460e+09|
|S|0|4.23510216e+12|-1.87630955e+13|1.230e+11|8.290e+01|5.360e+09|
|S|1|4.13261884e+12|-1.88619529e+13|1.200e+11|4.180e+03|5.170e+09|
|S|2|3.89534916e+12|-1.88886513e+13|1.130e+11|4.400e+03|4.950e+09|
|S|3|3.64563135e+12|-1.88959365e+13|1.060e+11|4.500e+03|4.710e+09|
|S|4|3.49598976e+12|-1.89155350e+13|1.020e+11|4.320e+03|4.530e+09|
|S|5|3.30467148e+12|-1.90183742e+13|9.620e+10|3.930e+03|4.240e+09|

文本原值CSV：[barrier_log_iterations.csv](barrier_log_iterations.csv)；精确代价：[barrier_iteration_costs.csv](barrier_iteration_costs.csv)；callback全部原值：[status_20261006T154830Z/barrier_iterations.csv](status_20261006T154830Z/barrier_iterations.csv)。没有读取X/BarX或发布BarPi，终态产物清单确认不存在planning_state、solution_qc、solution_snapshot或barrier_checkpoint。

## 身份与门禁证据

|门禁|结果|证据|
|---|---|---|
|V9源码|云源196个py/json/csv/sh/sbatch文件冻结；仅5个接口/配置/测试文件增改；F/S实际源码SHA全同，终态release散列复验PASS|cloud_source_repo_sha256.json、cloud_payload/、payload_sha256.json、各source_identity.json及terminal_readonly_audit.json|
|数值任务隔离|云包未混入A/B/C；BarHomogeneous−1，无年度分段或新headroom开关启用|原source_identity与参数回读|
|输入|80条input_manifest记录仅规范化member路径后全同；相同data_overlay/CF/hydro/wave roots|各input_manifest.csv、run_environment.json|
|源筛选CSV|SHA fe5d87a2adc6f5d6b8ad21606c571979312c1f632780fcdc9ea7500b7f0f2368；36,686条唯一身份，rc_ratio和当前headroom逐行重算PASS|S/candidate_selection.csv、build_report.json、final_assessment.json|
|真实1h门禁|ROWS/COLUMNS/RHS/目标SHA相同，仅20,272个vre_new上界置零|one_hour_pair_identity.json、gate_F/、gate_S/|
|两行真实Gurobi入口|3项PASS；不写QC/状态；两计算节点重跑也PASS|fixture日志、各startup_regression.log|
|真实8760 MPS|ROWS/COLUMNS/RHS/目标与非vre_new bounds段SHA相同；仅BOUNDS_VRE_NEW不同|各mps_section_sha256.json；下表|
|全套回归|412 tests /112.906s /OK /skip1（Windows无/proc）/exit0/source_unchanged=true|../validation_coordination_20261005/unittest_verified_20261005T185140Z.log及.json|

完整回归日志SHA：bf65c47c52747ef14fb6385b1c1518e822d5f7af1c0771c2b4b98a7077fa2d79。本机18:23蓝屏前中断轮次未计为通过，用户恢复授权后的串行重测证据独立保留。该事件不影响两个Slurm作业。

|MPS段|两成员共同SHA256|
|---|---|
|ROWS|32801212fcc23dd8897017360b9efd576e409fd0d3369fcb839b83910cb7edb4|
|COLUMNS（含目标）|e5266fd7a996062e2fd34de75c4f78bd9950e5da16d2913201480fd5f3f1c4a4|
|RHS|6ef4b21b7eb61823f8d639af20dd002b9b67618a1040c35507bbad2376c0c1e7|
|BOUNDS_OTHER|9c5ea9801c62cf3608065c4bde1845e17047d5e5b76b43113c6f30e9ef629126|

原MPS本体留在云端各成员output_8760/model_archive/，未下载数GB归档：F4,143,651,443 bytes，SHA9f426316dff40fa03398c24f6d675249edd02176380ee66c5110a1a1fde24460；S4,143,496,357 bytes，SHAe2861cfc3612eef82450b626c1fce0a4963ca1573fe800a4b2a18d38afdf258f。原归档manifest哈希与文件字节数已保存；本轮不重复读取8GB归档重算文件SHA，8760段SHA来自计算节点optimize前的流式读取。两份parameters.prm均185 bytes/SHA b57fdfe28a198b08ee3f01f87cc9a8a70998a5e589fbbedb510a71dd51ba4842，原PRM亦已取回。

## 资源费用与任务书差异

Slurm资源账：F8.732222节点小时、558.862222分配核时；S6.149167节点小时、393.546667分配核时；合计14.881389节点小时、952.408889分配核时。核时只取主作业CPUTimeRAW，不能再把batch/extern同一分配重复相加。账单单价未核验，货币费用记未知；作者事前18节点小时是估计，并非本次实际账单。

1. 任务书14,170来自源headroom>1e-6口径；当前V9已有1e-5GW cutoff，三个DPV候选原余量5.852501e-6、3.721000e-6、6.052454e-6GW被原规则归零，故实际14,167。没有为凑数改变V9。source_vs_current_headroom_difference.csv还含机器精度/更小微量行，不把57行全称作这3站。
2. held时AllocTRES为空：采用held核ReqTRES→release→batch核AllocTRES和内存通过才构建/求解。任务书文字顺序在未分配资源前无法直接核AllocTRES。
3. 本机归档实为original.mps，云为original.mps.gz；段解析兼容两者。frozen_local是1h门禁执行副本，其runner已加入接口，不称为未改动before；起始SHA另存，云正式测试基线直接复制V9源。
4. 旧runner嵌套primary_checkpoint_requested仍按SolutionTarget1记true；factor专用路径提前返回，实际无checkpoint/QC/状态，顶层TEST_ONLY_FACTOR_SCREEN/NONE正确。云包保持不可变，未为修饰字段热改正在运行的代码。
5. 文本日志与callback残差不同口径分别保存；sstat在作业结束后报告找不到活动step，这是终态查询差异，不是作业失败。终态内存取sacct与GNU time。

## 复现与最终处置

在本目录执行`python summarize.py status_20261006T154830Z`生成机械提取表，再执行`python finalize_report.py`重算终态身份/时间/资源与本报告；只读取已有小文件，不构建或求解模型。final_assessment.json为最终人工规则判定，factor_summary.json的PENDING字段仅表示机械提取器不擅自定义“明显下降”的新阈值，不覆盖本报告结论。部署命令和sbatch留在deploy.py/factor.sbatch/cloud_payload中，**不得再次运行submit/release**。

**逐项一句话判定：时间门槛通过（60.7562%≤75%）；稠密列机制通过（37,678→17,413）；配对身份通过（只变vre_new上界）；科学接受不适用（五轮上限、无QC）；自动正式投产未执行（后续采用另行授权）。** 本任务没有否决参数，因此不向FULL_YEAR_SOLVER_DECISION_20260817.md追加虚假的否决项；其他数值任务的否决独立维护。

本轮实验没有未完成的Factor证据项；未完成的是实验之外的完整收敛、重定价/加回策略与科学验收。早期状态与故障过程保留于[REVIEW_PRE_TERMINAL_ZH.md](REVIEW_PRE_TERMINAL_ZH.md)和各日期快照。
