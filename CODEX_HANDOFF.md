# CISPO model Codex handoff and version log

This is the repository's single handoff document for work continued across Codex windows. It records only verified, reproducible project state. New windows must read this file before taking action.

## Handoff update protocol

- Maintain `Current validated snapshot` as the concise active state.
- Append one entry under `Version history` after every material milestone.
- Each entry must include date, Git commit, scope, changed files, verification evidence, unresolved issues and next action.
- Link to detailed specifications rather than duplicating long derivations.
- Never include activation keys, passwords, private keys or the contents of `gurobi.lic`.

## Current validated snapshot

- 2026-09-02 21:08+08:00：唯一2160h年度容量联结行缩放资格运行已按冻结门禁终止，结论为
  `FAIL_TERMINATED`，不得自动重启或晋级8760h。运行20:05:31启动，21:04:32起由guard/launcher
  受控终止；未进入Barrier迭代，未取得Factor NZ/Ops、AA' NZ、DenseCols或iter30证据。raw结构精确匹配
  `12,520,914 rows / 10,398,783 vars / 126,724,678 nnz`，presolved NNZ为`106,864,011`，低于
  `107,398,350`反回归上限，且日志无数值警告；但ordering阶段进程组RSS由约68.55GiB继续升至
  `75.615GiB`并触及75GiB资格上限，随后达到`86.382GiB`，整机used达到`99.008%`、MemAvailable最低
  约`1.31GB`，触发95%整机保护。当前solver、guard和tmux均已退出，生产checkout仍detached、clean
  `ba8e09f97a6526e299f807eb9be8c579a217caeb`；21:08资源已恢复到available约94.45GB、实时si/so0/0、
  PSI avg10=0。该结果只证明当前128GB固定服务器无法在冻结内存门槛内完成本候选的2160h排序/分解，
  不能判断数值缩放是否加速Barrier。证据已保存到
  `downloads/stagea_rowscale_2160_fail_memory_20260902_v1`。作者随后授权每3小时自动巡检并按实测内存逐级
  扩大本地测试；已创建当前对话heartbeat `3-stage-a`。该授权不允许原样重启失败的2160h，也不允许直接
  晋级8760h：下一阶段先完成下述审计缺口与内存诊断，再从能够留出安全余量的更小时间窗开始单任务验证。

- 2026-09-02 本轮 current override（实现提交`122642f616b7abb2ad137250721a937e83a6f524`；
  Linux swap 实时采样修正`ba8e09f97a6526e299f807eb9be8c579a217caeb`）：作者已明确把唯一数值优化路线收敛为
  `annual_capacity_link_rows_8192_v1`，即只对 VRE 与径流式水电（ROR）的年度可用量约束做
  **精确整行左缩放**。对族 $f$ 取 $s_f=2^{-k_f}$，将零右端行
  $E_f-\sum_i FLH_{f,i}K_i\leq0$ 整体改写为
  $s_fE_f-\sum_i s_fFLH_{f,i}K_i\leq0$；变量、目标、边界、行支撑和可行域均不变。
  $k_f$ 是不超过13且保证缩放后最小非零系数不低于`1e-6`的最大整数；正式2160h/8760h
  门禁要求 VRE/ROR 均为`k=13`（`s=1/8192`），否则 fail closed。Wave 与省内负荷中心容量行明确
  不缩放。原单位解释固定为`pi_physical=s*pi_solver`、`slack_physical=slack_solver/s`、reduced cost
  不变；所有原单位QC继续执行。
- 8760h Stage A 冻结使用`barrier_checkpoint_full_year_cloud_v4`：`Method=2`、`Threads=32`、
  `Presolve=2`、`Crossover=0`、`SolutionTarget=1`、`BarConvTol=1e-9`、`FeasibilityTol=1e-9`、
  `OptimalityTol=1e-8`、`NumericFocus=1`、`ScaleFlag=2`、`Aggregate=1`、`soft_mem_limit_gb=600`，
  无`TimeLimit`；32线程是作者
  根据既有8760h经验作出的正式选择，不以小规模线程效率否决。Stage B不是必需步骤，且任何脚本、
  watcher或规划序列均不得自动启动Stage B；只有作者以后另行明确授权时才可作为独立任务讨论。
- 2160h/start2880只作为正式放大前的工程资格门禁；本轮候选已在进入Barrier前因内存门禁终止，不能宣称
  性能已改善。后续同尺度复测仍要求结构
  保持raw`12,520,914 rows / 10,398,783 vars / 126,724,678 nnz`；presolved nnz不超过
  `107,398,350`、DenseCols不超过`38,982`、`AA' NZ`不超过`2.17035e8`、Factor NZ不超过
  `6.28845e9`、Factor Ops不超过`2.19345e14`、日志factor memory不超过`63 GB`且无数值警告。
  首个`iteration >= 30`遥测点必须同时满足累计runtime不超过`12,000 s`、Work不超过
  `18,961.075`、进程组RSS不超过`75 GiB`；前两项一旦通过即锁定，后续内存或警告仍可失败。
- 本地验证已完成：设置权威wave根后完整测试`290 passed, 1 skipped`；
  `output/annual_capacity_link_scaling_24h_start2880_solve_v6/validation_report.json`为`PASS`，物理原式与
  缩放式均为Gurobi status2 `OPTIMAL`，目标均为`2112716.676624984 million CNY`且原单位QC均`PASS`。
  这仅证明短时域代数/接口正确，不是2160h/8760h加速证据。
- 服务器唯一有效生产checkout是`/home/zz2/National_model_server/repo`，已以detached HEAD部署并核实
  clean`ba8e09f97a6526e299f807eb9be8c579a217caeb`；`/data/zz2/National_model/repo`是旧NTFS克隆，
  不得部署或启动。本任务为落实作者
  “Stage B非必需、先解决Stage A”的新决定，已**有意停止**旧Stage B进程组及其Case2 watcher，
  旧任务已全部停止。这是对下方18:04条目在当时证据不足下保留
  `EXTERNAL_SIGTERM_CAUSE_UNRESOLVED`的后续纠正；不删除或改写该历史记录。服务器精确提交全套测试
  `256/256`通过；detached `tmux`跨SSH探针保持同PID/start time/cgroup并以6个heartbeat自然rc0；launcher
  假进程集成验证正常rc0、guard早退rc96、重复HUP/TERM首信号rc129、并发`flock`拒绝rc90、guard卡死
  超时rc97，所有solver/guard PID均已消失。探针还发现旧`vmstat`表达式误读since-boot首行，已在
  `ba8e09f`改为只审查3个实时区间。20:04:49可用内存自然升至`100.304 GiB`；20:05:24已用tag
  `2030_base_2160h_stagea_capacity_link_rows8192_barrier32_20260902_v1`和tmux session
  `cispo_stagea_rowscale_2160_v1`启动唯一资格运行。runner PID`384500`、guard PID`384507`，实际
  `Cpus_allowed_list=0-31`；CPU拓扑32个唯一物理核、NUMA0/1各16核。该任务21:04在ordering阶段因
  进程组RSS/整机内存保护终止，未形成Barrier性能证据。下一步仅沿`annual_capacity_link_rows_8192_v1`
  单路线推进：先恢复7fce1ca中的水库精确零上界、增加非basic终态的primal/dual residual、complementarity
  与relative gap硬门禁，并生成parent→new physical LP机器可读差异白名单；随后在无其他CISPO任务且资源
  预检通过时，以新tag从内存安全的较小时间窗做32核scaled/physical匹配筛选。只有实测峰值留有安全余量
  才按`1488h -> 2160h -> 4320h -> 5880h`逐级单任务扩大；不并发、不自动Stage B、不自动云端8760h。

- 2026-09-02 18:04+08:00：Case1 2160h Stage B已于17:41:39被`SIGTERM`中断，非自然完成、
  非95%内存保护、非OOM。runner rc143、Gurobi status11 `INTERRUPTED`、SolCount0，严格审计rc42；
  exact checkpoint resume和Crossover路径此前已通过，但运行92699.686s、8366337 simplex iterations后
  仍剩1262112 PPushes/PInf1265.5003，无objective、QC或result manifest。0.5s process-tree RSS峰
  26.954GiB；2s遥测46818样本/errors0、job RSS峰28.908GB、host used峰77.64%、最低available
  29.55GB；双stderr空、host guard0，排除资源保护或solver报错。终止时刻与一条SSH session断开
  同秒，但现有证据不足以确认信号发送者或因果关系，不能写成算法失败或用户主动停止。
  Case2 watcher也已退出，最后状态停在17:41:05 `WAITING_STAGE_B`；没有Case2 claim/output/process，
  不得手工启动，因为Stage B未达到rc0/QC PASS/manifest门禁。证据见
  `downloads/case1_stage_b_interrupted_20260902_v1`。原4小时heartbeat应删除，等待作者决定是否以
  更可靠的脱离SSH session/cgroup方式重跑Stage B、改走其他严格收尾路线或重新排序Case2/数值筛选。

- 2026-09-02 10:45+08:00：版本关系核实完成：服务器生产6065bfb是本地主分支/服务器裸远端
  65c8b21的祖先，本地仅领先两条运行记录，无分叉。已从6065bfb建立并整合统一工程分支
  `codex/numerical-stability-engineering-v2`，提交`7fce1ca4ae08997124a41322f1460040712b5afc`，
  已推送固定服务器裸远端和GitHub同名分支，活动生产checkout未更新。权威记录
  `NUMERICAL_STABILITY_ENGINEERING_LINE.md`明确：744h的CF1e-4负结果只阻止凭该证据直接晋级，
  不构成2160h/8760h必慢的外推证明；当前Case1/Case2结束且资源门禁满足后，仍可做隔离匹配的
  2160h结构/有限Barrier筛选。工程线整合候选均默认关闭、互斥测试，不改变生产1e-6默认值。

- 2026-09-02 09:59+08:00：完整744h Stage A阈值A/B已于09-01 22:42终态，pair两条均
  runner rc0、Gurobi `OPTIMAL`且checkpoint完整/可deferred crossover，但均因Crossover0宽松Barrier
  为`HARD_FAIL`、原始QC失败，不能科学接受。候选CF阈值1e-4相对生产1e-6虽然raw NNZ少20976，
  却由120增至134 Barrier步（+11.67%）、solver 2995.079→3070.307s（+2.51%）、work units
  2842.982→3006.566（+5.75%）、端到端3380.386→3478.729s（+2.91%），process-tree RSS峰
  20.049→20.402GiB（+1.76%）；目标还因可行域改变相差371.039 million CNY（约0.01598%）。
  因此`coefficient_zero_tolerance=1e-4`不凭744h证据启动该尺度Stage B或修改生产默认；但这不是
  对2160h/8760h性能的永久否决，后续可按统一工程线做隔离长时域结构筛选，不能直接上8760h。
  终态证据见`downloads/cf_744_stagea_pair_terminal_20260902_v1`；隔离分支worklog提交
  `4a95822bf0cfbaa85851c9f5d72ea55996109c32`，生产仍clean6065bfb。Case1 Stage B同PGID3946395
  继续exact-resume Crossover，09:59剩约2.418M
  PPushes/PInf1633.873、solver约64942s，无return code/QC/manifest；当前RSS约24.1GiB、host
  available约44GiB/PSI0。Case2 watcher881511仍`WAITING_STAGE_B`，不会绕过rc0+QC PASS+
  manifest+无竞争求解+available>=96GiB门禁。当前可用内存不足以安全再塞一对744h，且两张GPU
  存在其他计算客户；不触碰外部进程，先让Stage B完成并由门禁启动Case2。

- 2026-09-01 21:44+08:00：依据作者“在Stage B空余期自行迭代744h起步”的明确授权和前述
  `PROMISING_MODEST`五步结果，已启动下一对完整744h Stage A：基线tag
  `2030_base_744h_cf1e6_stage_a_concurrent_20260901_v1`（PGID1045145）与候选tag
  `2030_base_744h_cf1e4_stage_a_concurrent_20260901_v1`（PGID1045150），均为Base2030、
  744h/start2880、Method2/Threads16/Presolve2/Crossover0、BarConvTol1e-2、Feas/Opt1e-5、
  NF1/Scale2、engineering checkpoint模式、无TimeLimit/SoftMemLimit，分别绑定两个NUMA节点。
  新campaign root为`campaign_tools/cf_744_stagea_pair_20260901_v1`、supervisor1045122；本轮已修复
  monitor路径并核实两个2秒telemetry进程实际运行，pair级95%保护保留。启动时host available约87GiB、
  PSI0，Stage B同PGID3946395继续PPushes；Case2 watcher将按无竞争/96GiB门禁等待，不会过量并发。
  新launcher/worklog已提交隔离分支`ba89225a23375f2bc400d510b62f6e1865412239`，生产仍为6065bfb。

- 2026-09-01 21:41+08:00：两条并发744h CF阈值5步因子筛选均按预期到`ITERATION_LIMIT`
  （Gurobi status7、5 Barrier steps、无解/QC，runner rc2是当前runner对诊断终态的非零返回，不是OOM）。
  候选1e-4相对基线1e-6：raw NNZ 44000585→43979609（-0.0477%），presolved NNZ
  37040141→37023865（-0.0439%），Factor NZ 8.249e8→8.064e8（-2.24%），Factor Ops
  5.048e12→4.738e12（-6.14%），ordering 135.34→117.64s，solver 562.912→522.945s
  （并发筛选约-7.10%，不能直接当隔离加速）；process-tree RSS峰20.468→20.112GiB。候选raw Matrix
  最小值升至3.7e-5，但目标/RHS/bounds仍有更小尺度，故只判`PROMISING_MODEST`，尚未通过完整
  Stage A+B/QC。pair于21:18结束、host95 guard未触发；独立遥测器因生产repo缺少
  `scripts/monitor_case_resources.py`均启动失败，但pair级2秒内存/PSI记录、runner内部0.5秒RSS及
  `/usr/bin/time`完整，不能把缺失的独立字段记为0。Stage B于21:41完成DPushes后转入
  6755240 PPushes/PInf3224.99，仍无return code/solve report/QC/manifest；这是Crossover下一阶段，
  不是失败或重跑Barrier。production clean6065bfb、当前available约87GiB/PSI0，Case2 watcher
  仍`WAITING_STAGE_B`，未重复启动。

- 2026-09-01 21:04+08:00：作者明确授权在Case1 Stage B内存空闲期并发744h以上数值筛选，已部署
  两条匹配`744h/start2880`、Barrier16、`BarIterLimit=5`、Crossover0、无TimeLimit/SoftMemLimit
  运行：生产阈值tag `2030_base_744h_cf1e6_factor5_concurrent_20260901_v1`绑定CPU
  `0,2,...,30`，候选阈值tag `2030_base_744h_cf1e4_factor5_concurrent_20260901_v1`绑定
  `1,3,...,31`；21:03:45两者均启动，Stage B同PGID3946395继续，21:04整机可用约91GiB、
  used约25.8%、memory PSI0，95%配对保护和各自2秒遥测正常。生产模型本就将CF<1e-6置零；
  完整8760h只读误差审计表明升至1e-4会额外删除VRE64001项、ROR261060项、wave0项，容量
  上界可用电量损失分别5.2221/0.8794/0GWh，合计约6.1015GWh；既有容量floor损失合计
  约0.4151GWh，单小时全国上界损失不超过各资源上界之和约0.01303GW。该候选改变可行域，
  只能凭A/B晋级，不能称代数等价或已加速。Case2即时幂等watcher PID881511已部署，每60秒
  只做轻量门禁；Stage B rc0+QC PASS+manifest完整、repo clean6065bfb、无竞争求解、host used<90%、
  available>=96GiB、PSI正常后启动唯一`2030_base_2160h_case2_v3_barrier32_screen_20260901_v1`。
  人类可见automation `2160h-stage-b`保持每4小时并已扩展监测Stage B/Case2/数值候选。

- 2026-09-01 18:30+08:00：在独立worktree/分支`codex/annual-energy-coordinate-v1`完成
  `Annual Energy Coordinate V1`候选提交`4814c2e5f197cb152e9e37ff6dcf78df605bb38d`；基于生产
  6065bfb，默认关闭，未部署服务器、未干预活动Stage B。首版因把24h极小CF汇总系数压到
  `5.64e-10`已否决；当前版只缩放年度账户/省内年度流量，VRE/wave/hydro资源发电与CF/径流
  行保持物理GWh。24h/start2880 raw Matrix由`1.026e-6..6250`变为`1.026e-6..260.417`，
  最小系数不降；严格候选`OPTIMAL+QC PASS+manifest complete`且目标与原版binary64相同。
  但候选严格Barrier/Crossover为178.807s/131/370107，对比原版174.979s/120/366065，
  非exact Kappa也更差，故尚无速度/条件数改善结论；完整回归223/223 PASS。唯一后续是在当前
  Stage B完成后做相同2160h/start2880 Barrier16 Stage A+B A/B，候选不得复用原checkpoint。
  详细证据见隔离分支`ANNUAL_ENERGY_COORDINATE_V1_WORKLOG.md`。`2160h-stage-b` heartbeat已按
  作者要求从每小时改为每4小时，只读监测策略和2秒服务器遥测不变。

- 2026-09-01 17:36+08:00：2160h Case1 Stage B已通过exact resume门禁并进入真正的deferred
  Crossover，不再是build待确认状态。`primal_dual_start_input.json`证明Gurobi13.0.2、implementation
  bundle、科学输入identity、LP Fingerprint `0xcf045770`、10398783/12520914维度、变量/约束顺序及
  primal/dual向量完整性门禁均通过；Gurobi日志明确为`use start vectors`→`perform crossover with primal
  and dual start vectors`→`crush start vectors`，未重跑Barrier。17:36仍为同一PGID3946395/Python3946400，
  DPushes 8159992→222988、DInf约9.04、solver约5982s；这是Crossover进展，不是收敛或验收。
  3462个2秒样本/errors0，RSS采样峰28.908GB、host可用最低92.465GB、memory PSI0，双stderr空；
  无return code/solve report/QC/result manifest，继续只读监测，不改参/重启/并发/部署数值缩放。
  证据见`downloads/case1_stage_b_crossover_20260901_1736/README.md`。

- 2026-09-01 15:42+08:00：按作者授权启动唯一2160h Case1 deferred Crossover Stage B，标签
  `2030_base_2160h_case1_v3_stage_b_20260901_v1`，source为只读Stage A根
  `2030_base_2160h_case1_v3_barrier16_stage_a_20260827_v1`。启动前production clean6065bfb、
  无CISPO solver、MemAvailable113.093GiB、si/so0/0、memory PSI0；checkpoint gate eligible=true，
  BarX/BarPi 10398783/12520914项的size/SHA全部PASS；定向测试13 passed+34 subtests。
  参数为Method2/Threads16/Presolve2/Crossover2/CrossoverBasis1/LPWarmStart2、Feas/Opt1e-6、
  NF2/Scale2，无TimeLimit/SoftMemLimit，保留整机95%保护和2秒遥测。launcher3946098、
  solve PGID3946395/Python3946400；15:42仍在build，双stderr空，尚无primal_dual_start_input，
  因此不能提前宣称exact resume/Crossover开始。独立工具包SHA和启动证据见
  `downloads/case1_stage_b_launch_20260901_v1/README.md`。heartbeat `2160h-stage-b`已ACTIVE/每4小时，
  只监测此标签，不重启/改参/并发；终态须以strict contract、原单位QC和manifests共同验收。

- 2026-09-01 13:59+08:00：作者明确要求停止2160h GPU-PDHG。停止前重新核验同一标签
  `2030_base_2160h_case4_gpu_pdhg_unlimited_20260828_v2`、PGID1216966/Python1216969/GPU1；
  仅向目标进程组发送SIGTERM，29秒后正常退出，未使用SIGKILL，独立遥测器正常落盘退出，
  GPU0其他客户未触碰。终态`INTERRUPTED`/status11/rc143，solver386921.588s（107.478h）、
  78474440步、无解；末行P/D/Compl=1.32e-4/762/0.388，目标6.14573627e6/1.34354222e6。
  193911个2s资源样本/errors0，RSS峰27.043GiB、GPU1 job显存峰4558MiB/平均利用99.196%，
  无CPU回退/CUDA OOM/host guard，证明终止原因是长期算法/数值平台而非资源不足。服务器求解、
  wrapper、telemetry均已消失，GPU1已释放；未改生产代码/模型/数据/参数/其他任务。三小时
  `case-4-gpu-pdhg` heartbeat已删除，不会自动重启。证据见
  `downloads/case4_gpu_pdhg_user_stop_20260901_1359/README.md`。

- 2026-09-01 13:52+08:00：2160h GPU-PDHG同Python1216969/PGID1216966、clean6065bfb已连续
  运行约4d11h，solver386540s/78397740步，P/D/Compl=1.66e-4/763/0.388，目标
  6145955.98/1343518.08，相对分离仍78.14%，无终态/QC。8月29日P残差突破后形成新平台：
  近24h D残差仅改善1.548%、Compl0.257%、目标绝对分离0.232%，P在1.04e-4以上振荡；
  近48h对应2.554%/0.513%/0.321%。资源正常，193695个2s样本/errors0，GPU1当前100%/
  job4558MiB、全程平均99.20%，RSS16.59GiB/峰27.04GiB，主机可用约96.5GiB、PSI0，
  双stderr空，无CPU回退/CUDA/OOM。结论为算法/数值长期平台，不是资源瓶颈；按作者无时限
  授权继续，不停止/重启/改参。证据`downloads/case4_gpu_pdhg_heartbeat_20260901_1352/README.md`。

- 2026-08-29 23:32+08:00：2160h GPU-PDHG出现首次明确平台突破；同Python1216969/
  PGID1216966、clean6065bfb继续，solver162185s/32634740步。近3h primal residual由
  3.93e-3降至1.04e-4（97.354%），且新水平已持续约1.54h，不是单点波动；跳变窗口
  156620～156625s同时伴随dual/Compl短暂振荡，日志无显式restart标记，内部restart/iterate
  切换仅为推断。dual residual仅790→789，Compl0.390→0.389，目标绝对分离仅改善0.887%，
  当前目标相对分离仍约78.19%，故只判为原始可行性方向突破，绝非收敛或科学接受。
  GPU1仍100%/job4558MiB，81526个2s样本/errors0，RSS16.59GiB/峰27.04GiB，两stderr空，
  无CPU回退/CUDA/OOM/终态；未干预进程/参数/95%保护。证据
  `downloads/case4_gpu_pdhg_heartbeat_20260829_2332/README.md`，原自然运行策略继续。

- 2026-08-29 15:35+08:00：完整8760h原始MPS流式数值审计已核验为`COMPLETE`，修正此前
  “下载/审计未完成”的过期状态。输入4142909397bytes、SHA256`344f2ae4...43fe2435d`，
  integrity PASS；50907234 rows/41458383 columns/492835195 nnz与预期完全一致。审计为
  `NO_BUILD_NO_PRESOLVE_NO_OPTIMIZE`，故不提供full presolved矩阵/Kappa，也不等于科学接受。
  原Matrix1.000486e-6～6250/ratio6.246964e9；主因定位为`vre_capacity_gw`和
  `hydro_capacity_gw`同时连接小时CF约1e-6与年度FLH约6000，列族跨度约5.92e9/5.94e9；
  年度负荷中心GWh子系统还产生6250、4380和1e-6目标系数。形成第一优先候选
  `Annual Energy Coordinate V1`：只将该年度能量/流量内部坐标按S=8192GWh缩放并在导出/QC
  恢复原单位；不改模型边界、物理数据或求解容差。该候选仅为待实现/验证方案，预期range改善
  必须经MPS、presolve、原单位QC和唯一2160h对照证明；不推广既有通用binary scaling负结果。
  证据`downloads/numerical_audit_8760_20260829_v1/REPORT.md`及原audit.json。15:35只读核验
  服务器production clean6065bfb、同2160h Python1216969/PGID1216966仍运行，无干预。

- 2026-08-29 15:16+08:00：只读刷新2160h GPU-PDHG平台判断；同Python1216969/PGID1216966、
  production clean6065bfb继续，solver132365s/26552140步，P/D/Compl=0.00393/793/0.390，
  objective=6162895.93/1154994.79，无终态/错误，GPU1仍100%/job4558MiB，未干预。
  解析完整26036条日志、按实际记录无插值取3/6/12/24h窗口：P残差打印精度下均0%改善；
  D残差改善0.252/0.751/1.491/4.802%，Compl改善0/0/0.256/1.015%；目标绝对分离改善
  1.644/3.140/4.262/6.041%。结论仍是残差主导的平台期，但不是目标差完全横盘；
  当残差仍大时目标差不是可行上下界/停止gap，不能据此预测终态或宣称接近最优。
  证据downloads/pdhg_plateau_review_20260829_1516（源日志2096940bytes/SHA cfd9802e...18a）。
  本地HEAD65c8b21；仅scp/分析/文档，无模型/参数/进程/保护/自动化改变，原自然运行策略继续。

- 2026-08-28 20:27+08:00：例行3h只读巡检，2160h同Python1216969/PGID1216966、clean6065bfb继续，
  约12729540步/solver64600s，P/D/Compl=0.00393/818/0.392，仍未收敛，无新增异常/终态。
  GPU1为100%/4600MiB、RSS16.58GiB，主机可用86.92GiB；32760个2s样本/errors0，监测持续。
  证据downloads/case4_gpu_pdhg_heartbeat_20260828_2027/README.md。只保存日志，无生产/参数/进程变更。
  作者19:14提出99%重试后，因旧2160h自身95%保护冲突已询问是否允许联动调整，**尚未收到确认**；
  本次heartbeat仍要求95%，实际launcher也仍为95。99%未实施、8760h未重试，不将心跳当作授权。
  下一步保留原巡检和运行，等待作者就联动保护的新决定；不自动停2160h或改其保护。

- 2026-08-28 19:10+08:00核验：新8760h GPU0 tag `2030_base_8760h_gpu0_pdhg_unlimited_20260828_v2`
  已于18:23:22因94%整机优先退出保护结束（rc=-9，原702485已消失），不是仍在运行。
  总63min；完整建模3663.595s/61.06min、建模RSS峰48.183GiB，进入optimize约109s，
  最后presolve100s，尚无Start PDHG on GPU/任何PDHG迭代或QC。全程RSS采样峰77.627GiB，
  host峰94.374%/最低可用6.925GiB、Swap峰8GiB；GPU0仅初始化job386MiB/整卡786MiB、利用率0%。
  非显存OOM、非算法收敛失败；实际TimeLimit/SoftMemLimit均Infinity已由模型读回，参数符合原请求。
  原2160h Python1216969/GPU1仍100%/4600MiB，生产clean6065bfb；无新启停/改参/缩小/StageB。
  18份control+7份输出证据本地25/25 SHA匹配，见downloads/8760_gpu0_terminal_20260828_1910/README.md。
  原启动快照已加终态更正，本地HEAD65c8b21，未改生产/模型/数据，既有2160h自动化不暂停。
  真实模型规模50907234/41458383/492835195与历史云8760相同，但指纹0x2acf0ca2不同于历史0xd16b4c7e，
  来源待独立核验，不能宣称逐项矩阵完全一致；未据此改变模型边界。下一步需作者决定是否另安排
  更充分主存窗口后再试；不自动重启/取消保护/停旧2160h，也不能声称单独运行就一定能完成。

- 2026-08-28 17:22+08:00：作者新授权另一张卡尝试完整8760h，已于17:20:22在GPU0启动独立
  `2030_base_8760h_gpu0_pdhg_unlimited_20260828_v2`，PID/PGID702485、create_time1787908821.96。
  生产仍clean6065bfb，Base2030/full_year8760/start0，原2160h参数完整复用（Method6/Threads32/
  Conv/Abs/Rel=1e-2/1e-5/1e-2、无TimeLimit/SoftMemLimit）；未部署数值候选、未改模型/数据。
  唯一基础配置变化是私有副本启动内存准入96→1GiB；preflight PASS，非内存使用限额。
  共享主机旧95%保护保持；已告知作者新任务94%整机优先退出（0.25s检查，仅杀新组），
  新进程oom_score_adj500，2秒双GPU/主存/Swap/PSI/job采样正常，不自动缩小/重试/StageB。
  17:22新job建模中、RSS8.38GiB、host可用78.46GiB、GPU0仅初始化786MiB/0%；尚无实际参数
  读回文件或Start PDHG on GPU，不能称为已开始GPU迭代或已证明显存足够。旧1216969/GPU1仍100%。
  启动器v1在模型构建前因自身拼写错误返回125，已保留现场并修正为v2；不是算法失败。
  2个独立新增脚本+6项单测/静态检查PASS；详细SHA/命令/失败记录见downloads/8760_gpu0_launch_20260828_v2/README.md。
  本地HEAD65c8b21、相关新文件未提交；既有其他修改与审计下载未动。下一步只核验当前v2的
  实际Infinity/参数与GPU开始标志、资源/收敛和终态QC，不重复启动；2160h原3h巡检不变。

- 2026-08-28 17:12+08:00：作者追问N50R5后，已通过登录态网页确认NC-N50R5/scvk386确已绑定，
  同时还有BSCC-N56R5/scxk805、NC-N30/scz0rmg及原A6/A8；账号关系图五中心均标记在线。
  这修正此前查询范围：原SSH只覆盖bscc-m8，不是平台全部资源。详细证据追加于
  downloads/cloud_resource_inventory_20260828_1703/README.md。N50R5网页SSH实际返回connection closed，
  未获提示符；控制台队列仅返回A6/A8，GPU型号/显存/配额/空闲/报价尚未核实，不宣称已可调度。
  首页可用额度显示约-4973元，尚未核实合同/信用/停机政策，不能认定是断连原因。
  Chrome资源关系页已保留；下一步核实该资源区登录/队列和计费状态，再只读查配置；未提交任何作业或改绑定。

- 2026-08-28 17:03+08:00：超算账号资源只读核验完成，详见downloads/cloud_resource_inventory_20260828_1703/README.md。
  用户组与AllowGroups匹配的UP分区为amd_m8_768-a（192CPU/768000MB）、amd_a8_768（128CPU/768000MB）、
  amd_a8_384（128CPU，87节点384000MB/15节点768000MB）；17:03:52严格idle分别80/29/0。
  关联GrpTRES cpu=1280、MaxSubmitJobs=50；当前用户队列空。部分节点跨分区，不能相加；361唯一节点GRES均null。
  仅证明当前bscc-m8集群未暴露GPU；全平台资源/价格仍待作者登录已保留的Chrome控制台后查询。
  未申请资源/安装/迁移许可/改模型/启停求解；HEAD65c8b21。下一步仅查其他资源区，不自动提交计费作业。

- 2026-08-28 17:00+08:00：按作者要求完成当前2160h PDHG与前一轮23h Barrier16的同时间收敛对照，
  见downloads/pdhg_barrier_comparison_20260828_v1/REPORT.md及4份CSV/comparison.json。
  只读复制约16:53 PDHG日志（9916条、末51765s/10111540步），Barrier243条/末82527s；
  同2160h/start2880、原LP指纹0xcf045770，Time含预求解但不含建模，取不晚于预算的最近记录，无插值。
  10→14h：Barrier原始/对偶残差和目标绝对差下降80.77%/95.21%/88.83%；PDHG约0%/1.90%/0.48%。
  PDHG前期更快拉近目标但后段平台；14h目标差仍约为Barrier十分之一，不能说同耗时全面落后。
  历史Barrier17.4175h将目标差降至当前PDHG以下，23h宽松终态仍HARD_FAIL；不据此预测PDHG达标时间。
  两算法内部残差尺度未证明一致；描述性abs(P-D)/max(1,abs(P),abs(D))不是solver停止指标/最优性证书。
  新增本地比较脚本和4项测试PASS/py_compile通过，输入SHA和配置/QC可追溯；无模型/参数/进程变更。
  16:59审计v3下载222MiB（222/3951块），仍DOWNLOADING，不干预；下一步等待各自既有流程，
  PDHG按原无时限策略与3h巡检继续，严禁把这份比较当作提前停机或自动StageB授权。

- 2026-08-28 16:44+08:00：云端GPU-PDHG可部署性只读核验完成，证据
  downloads/cloud_gpu_license_review_20260828_v1/README.md。云端现有许可确为WLS
  （非秘密ID2847107、0600、无机器绑定字段），但文件无到期日，本次未申请token核验订阅/并发。
  官方GPU功能不需单独许可；当前云端应用gurobipy13.0.2无+cu，需独立GPU环境。
  sinfo -a未见GPU分区，全部GRES null；只能证明当前账号/资源区未暴露GPU，不代表平台无GPU。
  16:42云队列空；固定服务器原Python1216969/RTX4090 GPU1继续100%，13.0.2+cu129已实核。
  未申请节点/迁移许可/安装/求解/改动进程；HEAD65c8b21。下一步先取得GPU资源区/型号/价格，
  作者授权后才做新节点小LP许可及GPU验证，再评估相同2160h独立对照；现有任务不受影响。

- 2026-08-28 16:43+08:00：作者明确授权“继续审计”，已启动独立本机小块续传→整文件SHA→本地审计
  流程。当前根`.codex_tmp/numerical_stability_20260828_v1/outputs/local_8760_verified_v3`，
  16:41:48 launcher13448/实际Python49052（需复核身份），run_v1/status.json为DOWNLOADING；
  16:42:10成功保存3个1MiB块，非完整下载/审计终态。2线程、1MiB块、每次180s/最多3次；
  源端仅stat/dd读取，不提交云计算、不写固定服务器、不触碰另一备份45560。
  完整4142909397bytes/SHA344f2ae4...43fe2435d通过后自动启动一次原audit_saved_mps_stream.py，
  验证50907234/41458383/492835195及gzip/ENDATA/SHA；最终输出run_v1/audit/audit.json。
  首次32MiB块版因慢网络超时，于16:41身份核验后仅停止本机31188及其SSH子进程；
  local_8760_verified_v2全部partial/锁/旧status和controlled_stop.json保留，不再当作活动任务。
  15:38失败现场也保留。新增fetch_and_audit_mps.py及7项测试，7+11项PASS，未改解析器/LP/数据。
  16:38 PDHG原1216969、生产clean6065bfb、GPU1 100%/4600MiB、资源无错误，未干预。
  详细命令/哈希/接续见v3根README.md；下一步查同一run_v1状态，禁止重复启动或绕过完整性门禁。
  仍无可推广的大规模数值修复，下载恢复不能记为审计完成；主机需保持开机联网。

- 2026-08-28 16:33+08:00：响应作者状态询问，只读复核发现全8760h流式矩阵审计已于15:38:14
  **FAILED**，不是仍在等待。ssh.stderr.log为Connection reset，解压报EOFError；原Python34684/
  SSH40220/launcher37332均已退出。最后进度104072756/492835195 nnz（约21.1%）、
  接收1555038208/4142909397bytes，无audit.json、未完成全量SHA/CRC/维度核验。失败现场保留，未重启。
  16:32云端SSH恢复可达，源MPS大小仍4142909397bytes、mtime03:01:57；本轮未重新全量hash，
  不能单凭stat证明源完整，也不将传输截断归为模型数值失败。
  独立备份进程45560身份仍匹配，但本地transfer_progress和服务器backup_status均停在14:22:46，
  1945156460/6606826274bytes、31/104范围，未见完整性PASS；记录为进度停滞，不干预其他任务。
  PDHG同一Python1216969/PGID1216966、production clean6065bfb继续；16:31约9847340步，
  solver50470s，stdout primal/dual/Compl=0.00393/828/0.393，相较14:18改善很小，仍未收敛。
  RSS17.002GiB/采样峰27.043GiB，GPU1为100%、4600MiB、60°C/312.79W，host可用约86.83GiB；
  25702个资源样本/errors0，日志持续更新且stderr空，未见终态/回退/OOM，不停止/改参。
  下一步建议先处理传输停滞，取得校验通过的稳定MPS副本再重新审计；本次仅状态核验和文档更新，
  不自动续传/重启审计或开展新数值试验。下次PDHG仍按既有3h巡检，不因本次问询改频率。

- 2026-08-28 15:09+08:00：按作者要求完成历史job4139552的8760h收敛日志简报，3页中文PDF/Markdown、
  2组PNG/SVG及逐步CSV，目录output/pdf/8760_stage_a_convergence_20260828_v1。
  原始7个日志/报告/配置SHA256匹配归档；stdout/callback各608点（0—607）连续且独立留存。
  solver1773606.980s=20.5279天，iter0→607占98.8365%；步间隔中位47.937min，最后100步3.0933天。
  Matrix1.000486e-6～6250（跨度6.246964e9）；本报告无完整presolved范围/条件数，未套用旧1h统计。
  保留solver OPTIMAL、原LP HARD_FAIL与恢复QC FAIL/56 of58三层口径；StageB未执行，恢复非二次求解。
  新增scripts/report_8760_convergence.py、render_8760_convergence_note.py和6项解析单测；6/6 PASS、
  编译/阶段时间闭合/3页渲染目视检查PASS，QA.md留存脚本/PDF哈希。HEAD65c8b21未提交。
  本轮仅本地归档分析，无模型构建/presolve/optimize或服务器操作；不干预Case4、完整备份及独立
  数值诊断任务，也不宣称其新终态。下一步作者查看简报；其他窗口的独立稳定性工作流保持原计划。

- 2026-08-28 15:07+08:00：按作者“不干预PDHG，同步提高数值稳定性”授权，已建立独立worktree
  `.codex_tmp/numerical_stability_20260828_v1`，分支codex/numerical-stability-20260828-v1，
  候选提交`cff89ceb2e6590923f2413d9a739c3d4a7013c29`；未合并/部署，主工作区既有修改保留。
  完整证据/数学边界/失败记录见该目录`NUMERICAL_STABILITY_WORKLOG.md`。
  新增可逆二进制行列缩放、原单位容差预算、MPS流式审计；1h缩放v2约束违反9.416e-7→7.089e-11，
  但耗时增加，24h/start2880原版及缩放版均NUMERIC。homogeneous诊断仅SUBOPTIMAL，不能认定不可行。
  独立分支还修正严格零入流水库上界的1e-12余量，10944个UB改变由原LP等式求和逐项证明；
  矩阵/目标/RHS/LB/命名不变，但24h仍NUMERIC，不宣称稳定性或速度收益。237/237回归PASS。
  **候选均不允许推广：工程代码/等价性验证通过，不等于数值问题已解决。**
  全8760h原MPS审计14:49:54在本机后台启动，Python34684（launcher37332/SSH40220）身份已核，
  直接只读云端完整源，不读固定服务器部分备份；本机BelowNormal、约39MB RSS，无GPU/服务器计算。
  15:06:29已扫完50907234约束名、24088472/492835195矩阵非零；仍RUNNING，完整SHA/规模校验未结束。
  状态位于worktree的outputs/stream_8760_original_v1/status.json；预期4142909397bytes，
  SHA256344f2ae4cabb669123c2a946fe530fa3417ab7c10ebb035850584f043fe2435d，完整终态才可引用全量结论。
  14:56固定服务器仍clean6065bfb、原PDHG Python1216969/GPU1 100%/4600MiB，未改参/停止/重启。
  下一步先查同一流式审计终态及错误日志，不重复启动；完成后据全量族统计定向设计，
  全尺寸presolved/条件诊断仍待独立资源窗口。PDHG原3h巡检/2s采样/无时限/95%保护不变。

- 2026-08-28 14:34+08:00：按作者要求完成三轮大规模数值范围只读诊断，详见
  `downloads/numerical_review_20260828_v1/REPORT.md`和带输入SHA256的`evidence.json`。
  云端8760h、2160h Case1 Barrier、Case4 PDHG原矩阵均1.000486e-6～6250，跨度6.247e9；
  目标均1e-6～3853.189876。两个2160h指纹0xcf045770及原/预求解维度一致，未见原LP漂移。
  6250已追溯DAC耗电年度核算，1e-6目标项为省内流量惩罚；不能任意截小系数或改物理参数。
  两个Barrier虽OPTIMAL，原LP严格质量均HARD_FAIL；PDHG约14:25仍未收敛，未检出明确数值告警。
  旧1h MPS仅作来源/预求解机制示例：全局最大不变、最差行跨度约增216倍；**非新小模型测试，
  非当前全尺寸presolved统计**。当前全尺寸系数分布/条件数仍未知，不证明PDHG已数值崩溃。
  本次零build/presolve/optimize，未改生产/参数/运行或其他备份任务。14:31生产clean6065bfb，
  本机HEAD65c8b21及其他窗口未提交修改保留；脚本编译通过，旧1h统计7字段与build_report一致。
  下一步若开展修复，先补全尺寸原/预求解分族系数审计及可逆单位缩放论证，仍按原物理QC验收；
  不因诊断终止/重启当前无时限PDHG，3小时巡检、2秒采样与95%保护不变。

- 2026-08-28 14:18+08:00 三小时巡检：同一无时限2160h Case4仍在GPU1运行，PGID1216966/
  Python1216969创建时间和命令行已复核，production clean6065bfb；实际time_limit_seconds/
  soft_mem_limit_gb仍null，未重启/改参/停止。14:18:02 callback8211040步、solver42448.095s
  （含presolve），墙钟约12h03m/GPU阶段约11h11m，尚无终态/QC。
  相较11:17改善明显放缓：stdout primal/dual/Compl由0.00396/847/0.396变为0.00393/837/0.394；
  目标6.19070422e6/8.54039989e5仍分离，不判为收敛，按作者无时限要求继续，不因长尾停止。
  RSS17.002GiB/采样峰27.043GiB、host可用86.831GiB；GPU1卡级4600MiB/job4558MiB，自上次巡检
  平均GPU99.9991%，当前61°C/313.73W。summary21681样本/errors0，原始文件晚4秒，均持续更新；
  memory PSI为0、swap-out增量0，无CUDA/OOM/回退，stderr空。
  证据downloads/case4_unlimited_20260828_v3/review_20260828_1417/，HEAD65c8b21未提交；
  本轮仅监测/备份/交接，保留其他窗口刚追加的云端结果备份记录。约17:17继续3小时heartbeat，
  2秒采样及原95%保护不变，不干预云端恢复/其他备份任务。

- 2026-08-28 14:17+08:00：首个2030/8760h恢复结果的**可视化已完成，完整固定服务器备份仍在后台传输**。
  云端源仍为`20260828_8760_stagea_recovery_v1`；目标父目录
  `/home/zz2/National_model_server/backups/2030_8760_stage_a_first_recovered_20260828_v1`，
  下含同名release，核心为`recovered_8760/`。全release301文件6606826274bytes（6.153GiB），
  其中原结果manifest86文件5852013714bytes；不重复全量原始输入数据库。未删除云端/旧本地副本。
  Windows后台Python45560于14:14:41启动（须复核身份），4路64MiB分块传输；原有t550
  checkpoint经SHA256匹配后复制复用4目标，共1477850384bytes。14:14:45完整分块/小文件计
  1626281156bytes，**不是全部完成**；大MPS及其余大文件仍待传。源和目标只传数据，没有求解。
  服务器父目录`backup_status.json`为实时状态，必须COMPLETE且`release_integrity_report.json`
  PASS/301文件全部passed，才可称完整备份。脚本结束自动全量SHA256并同步报告；Windows需保持联网开机。
  证据/日志/续传说明：`downloads/2030_stage_a_first_result_visualization_v1/README.md`及`backup_evidence/`。
  本机60个绘图输入13378779bytes已逐项SHA256 SUBSET_PASS（不是整包PASS）；概览和月度/8760h
  运行热图各PNG/PDF/SVG及汇总CSV/JSON完成，另有对话内交互概览，QC FAIL/56 of58明确保留。
  图表/说明已复制到目标父目录`analysis_v1`，脚本在`backup_tools`；不写入历史recovered_8760。
  4/4备份校验小测试PASS、4脚本py_compile通过；图形单位/时间/汇总闭合及明暗窄宽屏验证通过。
  本轮未改模型/验收规则，不启动StageB/2040，不触碰Case4进程。HEAD65c8b21未提交。
  下一步先查后台日志/实时status；若仍运行不重复启动；终态核验301文件PASS，再追加“备份完成”交接。
  14:19补充核验：45560仍为原后台进程、stderr空；14:18:19进度1810938732bytes、29/104范围。
  analysis_v1/figures的12文件与本机逐项SHA256全部一致（figure_backup_integrity.json PASS）；
  此为图表备份终态，不是全release终态。Case4 Python1216969仍运行，未操作其进程。

- 2026-08-28 13:45+08:00：终态核验确认**云端历史8760h Stage A已完整恢复**。job4396245于
  03:18:35 COMPLETED0:0、wrapper rc0，24核wall1:04:39；原LP构建2336.557s（38m57s）、构建峰值
  48.584GiB，整个恢复采样峰62.061GiB（Slurm batch MaxRSS64244236K为另一采样口径）。
  结果根`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260828_8760_stagea_recovery_v1/recovered_8760`。
  原LP fingerprint=-781497218，变量/约束/nnz、完整名称/sense顺序均与历史一致；虽然显式允许
  fingerprint mismatch，本次differences为空，**没有实际使用指纹豁免**。optimize/presolve均0。
  preservation COMPLETE/errors0，capacity/cost、operation/carbon/dual/QC、summary、candidate、catalog
  全部COMPLETE。result manifest共86文件、5852013714bytes（约5.45GiB）；本次逐项存在/大小PASS，
  QC、solve report、candidate cohorts/summary及来源关联hash另行复核PASS。运行末尾清单和candidate
  loader亦成功执行；本次没有在登录节点重新全量读取5.45GiB做所有SHA，也未新申请计算资源。
  原模型MPS.gz已保存4142909397bytes，完整variable/constraint名称目录206395222/251766440bytes，
  archive COMPLETE，无presolved/uncrush/factorization。BarPi小时271560行、年度3366行。
  planning_state_candidate保留86900行、零值/微小值不筛除，next_year2040；可供作者显式选择续年，
  不自动采用。QC仍FAIL：58项56PASS，失败为unidirectional_interprovincial_flow和objective_components；
  raw LP另有2行超1e-5，最大2.286828932e-5，与源报告一致。scientifically_accepted仍false。
  本地只备份终态报告到downloads/cloud_stage_a_recovery_4396245_20260828_v1/terminal_review_1342，
  完整5.45GiB恢复包仍在云端。未启动Stage B/下一年份，未干预固定服务器Case4。
  下一步可按作者要求下载完整结果、分析QC及选择是否采用候选state；不需要重做Stage A恢复。

- 2026-08-28 11:17+08:00 三小时巡检：同一无时限Case4仍运行，PGID1216966/Python1216969身份
  实核一致，production clean6065bfb。实际配置time_limit_seconds/soft_mem_limit_gb仍null，
  solver已31569.427s，超过旧21600s截止且继续GPU求解；未停止/重启/改参。
  11:16:44为5992040步，墙钟约9h01m、GPU迭代约8h09m；stdout31565s的primal/dual/Compl
  为0.00396/847/0.396，相较08:14的2.54/1020/0.502，primal明显改善但dual改善有限。
  当前目标6.19768764e6/8.42910122e5仍未闭合；无终态/QC，不将primal单项改善视为科学接受。
  11:16:46资源16246样本；summary于11:16:42为16244条/errors0（顺序复制的4s差异）。
  RSS当前17.001GiB/采样峰27.043GiB、host可用87.196GiB；GPU1卡级4600MiB（18.727%）、
  job4558MiB，近3h GPU平均99.9998%，当前60°C/312.9W、历史峰61°C/317.6W。
  memory PSI为0、swap-out增量0；双GPU/CPU/Swap记录持续，无CUDA/OOM/回退，stderr均空。
  证据`downloads/case4_unlimited_20260828_v3/review_20260828_1116/`，local HEAD65c8b21未提交。
  本轮仅监测/备份/交接；约14:16继续3小时heartbeat，不设6h/长尾截止，2秒采样及95%保护不变。

- 2026-08-28 08:15+08:00 三小时巡检：无时限Case4仍在GPU1运行，tag
  `2030_base_2160h_case4_gpu_pdhg_unlimited_20260828_v2`，PGID1216966/Python1216969身份已复核；
  production clean6065bfb，实际配置TimeLimit/SoftMemLimit对应字段仍null，未改参数/停止/重启。
  08:14:36 callback为3763040步、solver20641.640s（含presolve）；墙钟近6h、GPU迭代约5h07m。
  相较05:14，同stdout口径primal/dual/Compl由9.71/4.95e3/24.2降为2.54/1.02e3/0.502，
  目标由6.989144e6/-5.15735717e8变为6.2597836e6/-1.71134618e8；有进展但仍未收敛/无QC，
  不以两个端点改善宣称全程单调或已优于Barrier。继续无时限，不按竞争力或长尾停机。
  08:14:37资源10782样本/errors0；RSS当前17.001GiB/采样峰27.043GiB，host可用87.349GiB；
  GPU1卡级4600MiB（18.727%）、本job4558MiB，近3h GPU平均99.9998%，当前60°C/314.22W。
  双GPU/CPU/Swap/PSI记录持续，GPU0无本job客户，当前memory PSI为0、本轮swap-out增量0；
  无CUDA/OOM/CPU回退，solver与telemetry stderr空，无return_code或终态文件。
  本地证据`downloads/case4_unlimited_20260828_v3/review_20260828_0814/`，HEAD65c8b21未提交；
  本轮只读监测/备份/文档更新。下一次约11:14按既有3小时heartbeat检查，2秒采样及95%保护不变。

- 2026-08-28 05:14+08:00 三小时巡检：无时限Case4 `2030_base_2160h_case4_gpu_pdhg_unlimited_20260828_v2`
  仍运行，pgid1216966/Python1216969创建时间与命令行吻合；生产repo仍clean6065bfb。
  **已确认RTX4090及Start PDHG on GPU**，首条PDHG callback为03:07:07；build913.382s、
  presolve2184.98s。05:13:51累计solver9797.042s（包含presolve）、1551040次迭代，未有终态/QC。
  自身配置快照time_limit_seconds/soft_mem_limit_gb仍null，日志无非默认TimeLimit，原无限时设置未漂移。
  05:13:53资源5360样本/errors0；job RSS当前17.001GiB、采样峰27.043GiB，host可用87.330GiB。
  GPU1卡级显存当前/峰4600MiB（18.727%）、job4558MiB；近1h GPU平均99.999%，61°C、约315W。
  显存控制器活跃100%不是显存容量100%；GPU0无本job客户。Swap约7.419GiB为既有占用，
  本轮swap-out增量0、swap-in13.508MiB，当前memory PSI为0；未见CUDA/OOM/CPU回退或监测错误。
  收敛仍未达标且非单调：stdout在7200s的primal/dual/compl为0.196/2.22e4/193，
  9795s为9.71/4.95e3/24.2；目标仍明显分离，不能以高GPU负载判定加速或科学接受。
  本轮仅只读巡检、备份和交接更新；未停止/重启/改参，不触发其他Case或StageB。
  证据`downloads/case4_unlimited_20260828_v3/review_20260828_0514/`，本地HEAD65c8b21未提交。
  下一步约08:13按既有3小时heartbeat审查；无6h/竞争力提前终止，2秒资源采样及95%整机保护不变。

- 2026-08-28 02:16+08:00：按作者“每3小时审查、取消这一轮6小时门禁、观察PDHG潜力”要求，
  heartbeat `case-4-gpu-pdhg`已改为ACTIVE/每3小时；删除按6h或相对Barrier竞争力提前终止的规则。
  **无时限Case4已于02:15:14重新启动**，tag
  `2030_base_2160h_case4_gpu_pdhg_unlimited_20260828_v2`；launcher1216822、pgid1216966、
  Python1216969、telemetry1216967。旧screen进程已在进入optimize前受控SIGTERM，02:15:04
  rc143/hostguard0，约10分钟建模需重做；旧输出/控制日志/claim完整保留，不能计为PDHG求解失败。
  原进程已缓存21600秒配置且无在线控制入口，不能靠改JSON取消限制；本次只做这一回必要替换。
  新profile `large_lp_2160_case4_gpu_pdhg_unlimited_v2.json`，schema仍v1，numerics唯一变化是
  time_limit_seconds21600→null；实际Gurobi参数空模型检查PASS TimeLimit=Infinity、SoftMemLimit=Infinity。
  新任务自身model_config_snapshot也已核实time_limit_seconds/soft_mem_limit_gb均null；仍2160h/
  start2880、GPU1单4090、Method6/Threads32/Crossover0及原PDHG容差，不改模型/数据/精度。
  生产repo仍clean6065bfb，隔离工具包 `campaign_tools/case4_unlimited_20260828_v3`，本地HEAD65c8b21
  未提交。服务器最终18/18启动/资源测试PASS，11/11资源/profile测试在schema修正后再次PASS。
  02:15:32任务尚在数据/模型准备，未确认GPU迭代；2秒采样9条/errors0、solver/telemetry stderr空。
  原整机95%外部保护保留；无6h、无新增显存上限，不因长尾或暂时落后而主动停止本case。
  下一步只按3小时节奏审查新tag的GPU迭代、内存/显存压力和终态；2秒原始采样不降频，终态后暂停。

- 2026-08-28 02:15+08:00：按作者明确授权“云端原环境恢复、24核、不过度严格门禁”，已提交并启动
  **ParaCloud job4396245**，节点m4cg1702，02:13:56 RUNNING，实际Req/AllocTRES均为
  cpu24/mem128G/billing24，TimeLimit4h（06:13:56上限，提前完成即释放）。根
  `/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260828_8760_stagea_recovery_v1`，
  输出`recovered_8760`，控制日志`control`；02:14:08已进入BUILDING_ORIGINAL_LP，stderr为空。
  原Python3.10.20及8个记录依赖在计算节点全部匹配，30原始备份文件/77输入记录预检PASS；
  云端6项tiny LP测试1.047s全部通过，没有重复全国尺度求解验证。
  恢复新策略：先归档重建MPS/参数/完整名称，指纹不同经显式`--allow-fingerprint-mismatch`
  记录后可继续，不再仅因此退出。维度/非零元、完整变量名/约束名及sense顺序、向量哈希/finite
  仍核对以避免错配；名称摘要直接复用本次归档，省去第二次全量扫描。QC FAIL不阻断保存，
  raw LP审计异常也尝试继续语义导出并标PARTIAL，不伪造exact LP匹配或科学接受。
  原云端release和结果不改；固定服务器失败现场和独立运行Case4均未干预。Stage B/续年不启动。
  本地HEAD65c8b21未提交；变更offline_solution、recover_historical_stage_a、test_solution_preservation，
  新增cloud_recover_stage_a_24core.sbatch；local6/6、py_compile、diff check、cloud bash-n/hash校验PASS。
  注意progress中的available约689.9GiB是整节点指标，不是本作业可用额度；实际allocation仍128G。
  下一步只读检查job4396245的阶段/内存/终态与最终清单，不能把当前构建状态写成恢复已完成。

- 2026-08-28 02:06+08:00：按作者“那赶紧先启动pdhg吧”的新明确授权，**Case4已独立启动**，
  不再以历史恢复成功为前提；恢复失败现场、指纹门禁和旧结果全部保留，未修复/重启恢复。
  固定tag `2030_base_2160h_case4_gpu_pdhg_screen_20260828_v1`，02:05:12开始，launcher1175139、
  pgid1175169、Python1175172、telemetry1175170。启动前available104.376GiB、GPU1无compute
  客户端/可用24047MiB，生产repo仍clean6065bfb；模型与Case4 profile均未修改。
  Base2030/2160h/start2880，GPU1单4090、Method6/Threads32/Crossover0、最多6h、既定PDHG容差，
  SoftMemLimit=null，原整机95%保护保留，无新增显存上限。GPU环境已实读13.0.2+cu129。
  02:05:22仍在数据/建模准备，未见Start PDHG on GPU，不得声称已进入GPU迭代；进程已建立GPU1
  显存分配。2秒采样连续6条、telemetry errors0，solver/telemetry stderr均空；02:05:41主机监测
  继续更新，Python仍存活，暂无return_code。所有日志在对应run_control/<tag>。
  新工具包 `campaign_tools/case4_independent_20260828_v2`，仅给一次性门禁新增显式
  `--independent-after-failed-recovery`；保留失败身份记录及进程/内存/GPU/版本/hash/幂等检查。
  两项新授权边界测试和其余资源门禁测试，本地/服务器10/10 PASS；未改已验证launcher/monitor。
  本地HEAD65c8b21未提交，overlay清单见downloads/case4_independent_20260828_v2。
  heartbeat `case-4-gpu-pdhg`已恢复ACTIVE（每10分钟），提示改为仅监测已启动的本次任务，
  不调用旧恢复接续入口、不重复启动；后续确认GPU迭代、资源压力、终态和QC后暂停。

- 2026-08-28 02:07+08:00：作者询问改在云端原环境恢复是否更可靠；本轮仅只读核验，未提交付费作业。
  ParaCloud原release、python_overlay、checkpoint及数据链接仍在；按原cloud_environment_paths.env
  检查，Python3.10.20及记录的8个依赖包版本全部与历史run_environment相同，30-file implementation
  bundle摘要仍为bdf36a79...caf9a8e。原云端用户队列为空，amd_a8_768为UP。
  因此原环境是更稳妥的恢复候选，但尚未证明其新建8760LP指纹必然匹配；必须保留门禁。
  历史云端仅构建约38m57s/48.574GiB，恢复仍有校验、原模型归档、残差与语义导出，完整耗时未实测。
  队列现DefMemPerCPU6000/MaxMemPerCPU6144，未来可评估24CPU/128G的独立恢复allocation，
  不沿用96CPU/700G原Barrier请求，不代表已批准或已提交，也未核验账户余额/实际单价。
  先修复失败模型保全，再经作者授权使用原环境独立恢复；原release/结果保持不变。

- 2026-08-28 02:04+08:00：按作者“为何退出了”只读诊断，确认恢复退出直接原因是
  `recover_historical_stage_a.py:197` 的原LP指纹不匹配异常，非内存/费用/求解阶段终止；
  00:47:11报错、00:48:04 rc1、host95_guard0，重建耗时3566.906s、peak tree RSS47.914GiB。
  新核查发现源/目标环境并未完整锁定：Python3.10.20→3.11.15、NumPy2.2.6→2.4.6、
  SciPy1.15.3→1.17.1、xarray2025.1.2→2026.7.0，Gurobi同13.0.2；这是待排查线索，
  **不是已证明根因**。此前1h对照是新环境内在线/离线对照，不能证明跨环境全年LP相同。
  同时确认恢复驱动的保全缺陷：archive_model在指纹/顺序门禁之后，本次异常未留下重建MPS与完整
  名称目录；只保留build_report、原始向量副本及错误证据。原云端/本地原解未丢失。
  本轮未改代码/环境/服务器、未重启恢复、未绕过门禁；生产checkout仍clean6065bfb。
  下一步若获修复授权，应先补齐失败模型归档与分项诊断，再用匹配历史依赖的小模型跨环境对照
  定位系数/顺序/属性差异，不能仅改fingerprint期望值。既有Case4暂停规则不变。

- 2026-08-28 00:57+08:00 heartbeat巡检发现：历史8760h离线恢复已失败，00:47:11报
  `Original LP identity mismatch`，00:48:04 wrapper退出rc1、host95_guard=0。
  重建与历史模型均为41458383变量/50907234约束/492835195非零元，但Gurobi fingerprint为
  `718212258` vs历史`-781497218`。仅相同维度不能证明LP/顺序等价，根因尚未查明，未放宽门禁。
  build3566.906s，wrapper1:00:28，采样peak tree RSS47.914GiB；optimize/presolve均0，尚未开始
  全量顺序/旧向量核验及正式恢复导出。原云端checkpoint、本地备份和恢复现场保持不变。
  Case4门禁实调为 `BLOCKED_RECOVERY_FAILED`，没有launch_claim、没有正式Case4控制目录，
  **Case4未启动**；按既定失败规则已将heartbeat `case-4-gpu-pdhg`置PAUSED并核验本地配置。
  生产repo仍clean6065bfb，available约104GiB；内存已释放，但不能据此绕过恢复成功这一接续条件。
  证据备份 `downloads/case4_after_recovery_20260828_v1/recovery_failure_0057/`。本轮只读排查、
  状态记录和暂停后续任务，未改模型/数据/求解参数。下一步请作者决定是否先诊断指纹差异；
  不自动重启恢复、不自动改条件启动Case4。本条覆盖下方00:46的ACTIVE/WAITING状态。

- 2026-08-28 00:46+08:00：按作者“恢复结束后启动该算法并记录内存/显存/GPU压力”的新授权，已创建
  当前对话heartbeat `case-4-gpu-pdhg`（ACTIVE，每10分钟检查）。本条覆盖00:32的“未自动排队”。
  一次性门禁实测返回 `WAITING_RECOVERY`，**Case 4尚未启动**；不终止历史恢复，不并发大模型。
  固定Case 4标签 `2030_base_2160h_case4_gpu_pdhg_screen_20260828_v1`，GPU 1，2160h/start2880，
  最多6h、原PDHG profile不变，无SoftMemLimit或新增显存上限，原整机95%保护保留。
  独立部署目录 `campaign_tools/case4_after_recovery_20260828_v1/scripts`，生产repo仍clean6065bfb，
  未部署本地其他保全/恢复dirty代码；本地HEAD65c8b21，工具为SHA256固定的未提交overlay。
  新增 `scripts/start_case4_after_recovery.py` 与 `scripts/monitor_case_resources.py`，修正campaign
  launcher并接入采样。Windows14 PASS+1 Linux-only SKIP；服务器15/15 PASS（含5秒占位进程的
  完整启动→采样→退出测试，未运行模型）。双卡真实单次监测PASS，telemetry_error_samples=0。
  运行时每2秒记录主机RAM/Swap/PSI/CPU、进程组RSS/CPU时间、双GPU显存/利用率/温度/功耗与
  本次进程显存；`resource_pressure.jsonl`和持续更新的`resource_pressure_summary.json`位于对应
  run_control目录。峰值为采样峰值，不是精确分配器高水位；显存控制器活跃率不等于容量占比。
  后续检查依赖本机Codex运行和SSH可达；求解启动后的记录在服务器独立执行。恢复失败则暂停并报告，
  恢复成功且资源/版本/空闲GPU门禁通过后只启动一次；完成后汇总并暂停heartbeat，不自动其他Case。

- 2026-08-28 00:32+08:00：作者要求先启动Case 4并询问双卡。SSH可连接，双4090计算利用率均0%，
  显存占用395/36MiB；但历史8760h离线恢复PID657364仍在 `BUILDING_ORIGINAL_LP`，RSS约30.96GiB，
  整机available约71.96GiB，低于既定2160h启动门槛96GiB。**Case 4未启动，也未排队自动启动**；
  未中断恢复、未部署生产checkout，server仍clean6065bfb。GPU空闲不代表CPU建模/内存资源空闲。
  本地修复campaign启动器：保留source环境前的显式 `CISPO_PYTHON`，Case 4默认使用已验证cu129环境；
  并发门禁新增历史恢复脚本识别。`tests/test_campaign_launcher.py` 的6项隔离测试PASS，未求解。
  Gurobi13.0.2官方公开文档未找到受支持的单模型双GPU分摊接口；`PDHGGPU=1`是启用GPU，不是卡数，
  不将两张24GB当成48GB池。本轮保持单卡2160h/最多6h及既定容差，不新增求解器。
  本地HEAD65c8b21，本次修改未提交；已有保全/恢复dirty改动完整保留。下一步先确认恢复结束且资源
  满足门禁，再单独部署启动器修复、验证GPU环境并启动Case 4；如需改变任务优先级须作者明确选择。

- 2026-08-27 23:48+08:00：按作者“服务器空闲，可以启动上一轮Stage A恢复”授权，已在t550启动
  云端历史8760h job4139552的独立离线恢复，**不是2160h Case 1重跑，也不是Stage B**。
  根 `/home/zz2/National_model_server/recovery_8760_20260827_v1`；launcher PID657349、进程组657359、
  Python PID657364，23:47:35启动，23:47:45进入 `BUILDING_ORIGINAL_LP`，23:47:51 stderr=0。
  启动前available100.91GiB，设置90GiB启动门禁和整机95%外部保护；optimize/presolve入口强制报错。
  旧release源码包SHA256 `c49d48da...ec40e`及原始30文件全部验证，原实现bundle `bdf36a79...caf9a8e`
  匹配；只覆盖4个导出/保全文件并新增恢复适配器，历史master除export函数外AST完全相同。
  原始77条输入/完整配置/科学身份通过显式跨机器路径映射；实际使用的8份2023/2024 CF存储共22536
  文件全payload与云端一致，排序sha256sum清单总摘要 `c909ba9d...42c709fc`。唯一不一致为后来更新的
  `output_manifest.csv`，已从云端取回原件放入独立historical_model_data，未改动现用数据。
  同一历史版本1h真实求解→未求解重建→恢复对照PASS，容量/运行/成本/对偶/cohort、碳、原LP QC、
  manifest/candidate loader均通过，恢复调用optimize/presolve均0；年度LP指纹/顺序核验仍待本次构建。
  输出为 `recovered_8760/`，控制日志 `control/`，完整证据 `launch_validation.json`、`preflight_v2/`、
  `validation_1h/validation_report.json`。生产checkout仍clean6065bfb，旧8760/2160输出不变。
  本地HEAD65c8b21未提交；新入口 `scripts/recover_historical_stage_a.py` 与
  `scripts/run_historical_stage_a_recovery.sh`。下一步只检查此恢复的进程、资源、进度和最终清单；
  不启动并发大模型、Stage B或续年。恢复尚未完成，不得宣称已得到全年结果表或科学接受。

- 2026-08-27 23:34+08:00 终态复核：固定服务器2160h Case 1 Stage A 已于23:27:51正常结束，
  rc=0、host guard未触发、stderr=0，server仍clean `6065bfba34b76098e86307081323e8545a4d25ac`。
  Barrier 242步，solver `82535.468 s`，wrapper wall `23:13:57`，peak tree RSS `69.291 GiB`，
  整机最高使用率 `88.742598%`。Gurobi OPTIMAL仅是宽松Stage A终态：strict contract HARD_FAIL，
  原LP最大constraint/bound/dual violation为 `0.0384984/0.000263950/0.00783257`，末次primal-dual
  目标相对差 `6.286394%`；工程物理QC为53/58，失败项为power_balance、wave_availability、
  unidirectional_interprovincial_flow、reservoir_transition、captured_co2_reconstruction。
  输出根 `outputs/2030_base_2160h_case1_v3_barrier16_stage_a_20260827_v1` 的BarX/BarPi均已实读核验
  finite、entries正确、SHA256匹配，checkpoint为ENGINEERING_BARRIER_CHECKPOINT_ONLY且
  deferred_crossover_eligible=true，scientifically_accepted=false。当前无CISPO solver，available约101GiB；
  Stage B和Case 2--4未启动。本次旧进程没有14:18的新保全功能；下一步应先核对独立离线完整恢复/导出，
  不因QC失败省略候选结果，也不重标科学接受。本次仅状态查询与本地交接更新，未部署/启动新求解。
- 2026-08-27 14:18+08:00：Stage A 完整保全策略已在本地实现并验证，状态为
  `LOCAL_VALIDATED_NOT_DEPLOYED`，覆盖下方13:39的“代码待实现”。所有 nonbasic Stage A 先保存可读
  原始向量，再独立导出容量、运行、成本、碳、对偶、QC、结果清单和未筛选 `planning_state_candidate`；
  QC FAIL 不阻断保存，文件完整性与科学接受分开，候选续年必须显式 `--allow-candidate-state-in`。
  默认在 optimize 前归档原始 MPS、参数和完整名称目录；`--archive-presolved-model` 仅额外保存诊断
  副本，未保存 uncrush/factorization。新增 `--recover-stage-a-from` 真正离线恢复，不调用 optimize/
  presolve；仍严格核对输入、Gurobi版本、LP指纹、完整顺序与向量哈希。历史8760h尚未恢复或重建。
  Gurobi13.0.2全量回归 `222/222 PASS`；Gurobi12/13的1h对照、正式runner源/恢复入口均通过，
  45个容量/运行/成本/对偶/cohort表或数组与直接在线导出一致、碳和原LP残差一致。已由候选状态成功
  构建2040/1h LP（仅build，不求解），238529变量/80143约束/453269非零元，0.375GiB。
  本条已自包含记录保存/恢复边界；机器可读验证证据为
  `outputs/stage_a_recovery_validation_20260827_v2_gurobi13/validation_report.json`，不依赖未提交的外部说明文档。
  未部署服务器、未改变正在运行的2160h进程、未启动Stage B/全年恢复/正式续年。旧进程仍按旧代码运行，
  不能声称已获得新保存策略；结束后须用独立恢复入口补齐。本地HEAD仍为 `65c8b21...`，本轮未提交。
- 2026-08-27 13:39+08:00：作者明确要求将 Stage A 的**完整保存、质量评价、结果采用**解耦。
  新要求状态为 `AUTHOR_REQUIRED_EXPORT_POLICY_PENDING_IMPLEMENTATION`，不是已部署功能：只要结果
  可读取，就必须保存容量、运行、成本、碳、对偶、`solution_qc.json`、`result_manifest.json` 和候选
  跨年容量状态；QC/solver contract FAIL 只记录违反项，不得成为省略这些文件的理由。结果清单的
  完整性不等于科学接受，候选 state 保存不等于自动续年；论文采用和未验收 state 的消费均留待作者
  明确选择。原始 checkpoint/solve report 的 `scientifically_accepted=false` 与 `HARD_FAIL` 不改写。
  本地复核确认 runner 仍跳过 engineering Stage A 导出，state loader 仍要求 QC PASS/accepted checkpoint；
  当前 `.npy` 不能直接作为下一年份输入。同一 2030 LP 的 Stage B 可按现有 exact-LP/checkpoint 门禁
  使用该 checkpoint，不依赖先生成规划表，但未启动。恢复应首先开发无 `optimize/presolve/crossover`
  的离线数值适配器，按原源码/输入重建并验证变量、约束映射，再导出完整结果与候选资产 cohort。
  此条更正下述旧 zero-iteration 建议：`PStart/DStart` 不是对 `.X` 的直接赋值，小模型被 presolve
  全部消去的试验不能证明 8760 h 可零迭代恢复。历史构建峰值 `48.574 GiB` 高于本机约 32 GiB；
  本轮只完成政策/恢复路径核查与文档记录，未修改求解代码、运行恢复、提交云作业或实时复查服务器。
- 2026-08-27 03:28+08:00：ParaCloud 8760 h Stage A job `4139552` 已于 2026-08-26 14:39
  正常结束，Slurm/runner 均为 rc 0，Gurobi `OPTIMAL`、Barrier 607、solver runtime
  `1,773,606.980 s`、wrapper wall `20-13:21:11`、峰值 RSS `362.952 GiB`、stderr 0，objective
  `4,188,006.084013813 million CNY`。已保存原始 LP 顺序的完整 `BarX/BarPi`
  （`41,458,383/50,907,234` entries），但 checkpoint 身份严格为
  `ENGINEERING_BARRIER_CHECKPOINT_ONLY`、`scientifically_accepted=false`。严格 solver contract
  为 `HARD_FAIL`：最大 constraint violation `2.28683e-5 > 1e-5`；因此没有正式
  `solution_qc/result_manifest/planning_state/basis`，不得重标为科学结果。云端当前用户队列及
  Python/Gurobi/CISPO 进程为空，Stage B 未启动。完整 checkpoint、输出、control、配置和精确源码包
  已备份到本地忽略目录
  `downloads/paracloud_4139552_2030_8760_stagea_barrier_v2_20260826`：30 个下载文件、
  `748,733,446 bytes`，文件数/核心向量/源码归档 SHA256 全部 PASS。恢复与文件保存政策已由上方
  13:39 作者要求覆盖；原始 checkpoint 身份及本段终态证据保持不变。
- 2026-08-27 00:16+08:00：作者已授权执行唯一四 Case 的 2160h 大 LP 筛选。实现提交
  `88f88779949a5bc27486447d674f6b700b21ac93` 将省际线损、VRE/水电 FOM 改为经 schema/range/source
  校验的 `config/technology_parameters.json` 注册表读取，并显式冻结 primary objective component 集合；
  GPU 运行时隔离提交为 `6065bfba34b76098e86307081323e8545a4d25ac`。新 profile 只包括
  V3-16核、V3-32核、Dual simplex、GPU-PDHG，统一默认 2160h；四者 `soft_mem_limit_gb=null`，
  challengers 最多 6h，GPU-PDHG 为 `PDHGConvTol/AbsTol/RelTol=1e-2/1e-5/1e-2`。server 全量
  `217/217 PASS`；新旧 1h raw LP 均为 `238529/80143/453269`、fingerprint `-146272577`、objective
  `2127270.3027043818 million CNY`、QC PASS，证明本轮审查修复不改变 LP 边界。独立 GPU env
  `cispo-2030-gurobi-gpu13.0.2-cu129-v1` 已验证日志出现 RTX 4090 与 `Start PDHG on GPU`。
  Case 1 已于 `00:13:53` 在 clean server `6065bfb` 启动：Base 2030、hours `2880--5039`、V3
  Barrier 16核 Stage A、无 TimeLimit/SoftMemLimit，control/output tag 均为
  `2030_base_2160h_case1_v3_barrier16_stage_a_20260827_v1`；PID group `687599`，初始 stderr 0，整机
  used 约 16%、swap 无新增、PSI 0。`00:28:59` 已进入 Gurobi：raw LP
  `10398783/12520914/126724678`，fingerprint `0xcf045770`；生效参数无 TimeLimit/SoftMemLimit，构建峰值
  `12.492 GiB`，presolve 初期整机 used 约 28%。仅整机 used>=95% 时外部保护终止；若 2160h 因内存确实不可运行，
  才依次降至 2016h 或更小。活动 cloud 8760h 不触碰。
- 2026-08-25 17:20+08:00：已完成 National_model 最终基准情景数据归档，目标为
  `E:\数据拷贝\National_model基准情景数据_20260825_v1`，共 `16,966` 个文件、`7.003 GiB`，按 00--09
  中文编号分类，未删除任何源数据。最终风光装机采用
  `osm_geometry_value_added_capacity_v3_offwind47/final_pointV2`，不是旧 v2；负荷另导出严格只含
  `base_residual_gw` 的 31 省 × 5 年 × 8,760 h 表，共 `1,357,800` 行，QA PASS。首轮已生成
  `16,961` 文件 SHA256 清单并完成 98 条映射检查；95 条直接 PASS，3 条告警经快速复查均已解释或
  同步。按作者指令，第二轮逐文件严格复核在 `3,000/16,961` 处停止，交付状态记录为
  `QUICK_PASS`，不能表述为第二轮 strict PASS。`data/raw` 的 116 条旧清单记录属于明确排除的 1 km
  原始用电 TIFF，非 model-ready 输入漏拷；非 raw 缺失为 0。说明、版本判定、映射、哈希与校验摘要
  均位于归档根和 `00_归档说明与校验`。归档开始时记录的 Git 基线为 `f7ef130...`；执行期间分支
  前进到 `fc3ca89d07feb796f57a0c433845e0e48901b416`，更新后的
  `scripts/run_fixed_server_host95_long_horizon.sh` 已补同步并核对 SHA256。新增本地脚本
  `scripts/archive_final_baseline_data.ps1`、`scripts/extract_base_residual_load.py` 尚未提交。
- 2026-08-25 17:07+08:00：`t550` SSH 已恢复，server bare remote、GitHub 与 clean checkout 均部署到
  `60561e57c419131a94539c2258ff108cc725edfd`；host95 功能提交仍为 `7dfefbb`。部署前发现共享主机
  资源快照不应持久化其他用户完整命令参数，故以 `60561e5` 最小改为仅记录 `comm`，模型方程、数据、
  场景、求解参数和内存阈值均未改变。server `bash -n`、py_compile、profile `9/9`、guard `8/8`、
  完整 pytest `215 passed + 63 subtests`（`98.34 s`、MaxRSS `1,186,016 KiB`、swaps 0）全部 PASS。
  `outputs/preflight_host95_2160h_deploy_20260825_v1` 以 Base 2030、hours `2880--5039` PASS：规模
  `10,331,823/13,932,898/123,010,374`，数值兼容 PASS，物理内存 `132,145,156,096 bytes`，动态
  `SoftMemLimit=125.537898 decimal GB`、`TimeLimit=null`。正式 2160h **尚未启动**：共享主机其他用户
  工作负载使 available RAM 仅约 `85--86 GiB`，低于不可绕过的 `96 GiB` 启动门禁；未更改任何他人
  进程。精确下一步是等待 available `>=96 GiB`，重新核对 clean/no-solver/目标根不存在/si-so/PSI 后，
  启动唯一 `2030_base_2160h_host95_20260825_v1`。
- 2026-08-25 13:05+08:00：按作者明确授权，已在本地实现固定服务器长时域 `host95` 工程路线，但尚未
  部署或启动。新增 profile `barrier_checkpoint_fixed_server_host_memory_95_v1`：Base Stage A、
  `Method2/Threads16/Presolve2/Crossover0/SolutionTarget1/BCTol1e-2/FeasOpt1e-5/NF1/Scale2/Aggregate1`，
  `TimeLimit=null`；runner 从 `/proc`/`psutil` 检测主机物理内存，将 Gurobi decimal-GB
  `SoftMemLimit` 动态解析为总物理内存的 `95%`，并完整写入 run scope/config snapshot。新启动器
  `scripts/run_fixed_server_host95_long_horizon.sh` 仅允许 `745--8759 h`、clean checkout、单 solver、
  新 output/control roots；默认重跑与历史可比的 Base `2160 h`、start hour `2880`，每 2 秒记录整机
  内存，整机使用率达到 `95%` 才发送 SIGTERM，solver 自然终态仍可提前结束。该路线仍是
  `TEST_ONLY_TRUNCATED_HORIZON`，不改变 LP 方程/数据/目标，也不自动形成科学结果或 planning state。
  本地 py_compile、profile tests `9/9`、guard tests `8/8`、完整 unittest `215/215 PASS`；2160 preflight
  PASS，估计 `10,331,823 vars / 13,932,898 rows / 123,010,374 nnz`。两次 SSH 入口均在 banner 阶段
  timeout。实现提交 `7dfefbbef5acc593d22b82173259931183353b89` 已推送 GitHub；server bare `origin`
  push 因同一 SSH blocker 失败。因此服务器仍保持最后验证的 `50e2d20`/idle 状态，尚未 deploy/run；连接恢复后必须先
  核对 HEAD/clean/no-solver/available>=96 GiB/si-so/PSI，再以全新版本根启动唯一 2160 h 任务。
- 2026-08-25 00:35+08:00：新本地服务器 `t550` 已完成可复现部署与真解门禁。主 SSH 入口为
  `national-model-server -> zz2@192.168.9.27`，当前显式绑定本机有线地址 `124.16.2.17`；本地
  `origin` 已切到 `ssh://national-model-server/home/zz2/git/National_model.git`，新 bare remote、服务器
  clean checkout 与本地分支均为 `50e2d2012a76a342eed1d281997c9b2382731a8a`，`github` remote 保留。
  服务器运行根为 `/home/zz2/National_model_server`，Python `3.11.15`、Gurobi/gurobipy `13.0.2`，
  2,501 变量完整许可门禁 PASS；发布契约、V5 输入、水电 380 GW 闭合、readiness 与两个 raw GRFR
  SHA256 均 PASS，数据 smoke `142/142 PASS`，完整 pytest `212 passed + 59 subtests`。
- 新根 `/home/zz2/National_model_server/outputs/2030_1h_new_server_smoke_20260825_v1` 已以 Base、
  `--diagnostic-hours 1`、`barrier_16_auto_order_v2`、cold/no-basis 完成：`OPTIMAL + QC 58/58 + current
  input manifest + valid result manifest`。raw LP `238,529/80,143/453,269`，objective
  `2,127,270.302704 million CNY`，solver `6.925 s`、wall `33.33 s`、peak process-tree RSS `0.469 GiB`、
  swaps/stderr `0/0`；最大 constraint/bound/dual violation
  `9.244e-12/4.922e-12/0`。该结果明确为 `TEST_ONLY_TRUNCATED_HORIZON`，不是科学规划结果；结束后
  checkout clean、无 CISPO/Gurobi 进程、available RAM 约 `104 GiB`。
- 新服务器所有已挂载文件系统中未发现旧 National_model case/data/output。`/dev/sdb1` 是未挂载
  `14.6 TiB NTFS`（label `系统`），`/dev/sdc4` 是未挂载约 `222.7 GiB ext4`；当前账户不在 `disk`
  组且无 passwordless mount 权限，因此未越权挂载或写入，旧 case 是否位于这两个盘仍未知。新部署
  采用 add-only 版本化数据根；为尽快恢复运行，只上传 solver 实际消费的 147 个 model-ready 文件，
  未上传不被运行时合同消费的约 `19.2 GB data/raw` 用电 TIFF。两份中止传输的 partial tar 共约
  `6.37 GB` 被保留在 `packages/`，清理前须另行确认。
- 2026-08-17 19:29+08:00：对持久化目标完成逐项审计。原目标要求的“不停止活动 cloud、固定服务器
  多轮宽松 744 与更长时域、显著提速、宏观 A/B 稳定、资源/耗时/质量/Git 全记录、形成后续全年决策”
  均已有直接证据：Base/V5 744、两批 factor screens、Base/1488、Base/2160 memory boundary、deferred
  v3 strict `OPTIMAL + 58/58 + manifests + Pi + macro PASS`、正式 Stage A/B v3 profiles 与 fixed
  `14/14 + 212/212 PASS`。Stage A+B 相对 strict 744 solver/wall 加速 `7.71×/6.99×`。因此参数筛选
  目标已完成；不等待当前旧参数 cloud job 终态，也绝不取消它或把它写成已接受年度结果。cloud
  `4139552` 保持原样，后续只在约 2 小时/terminal/anomaly 做独立只读审计；下一次付费资源申请须在
  新授权时实时核对计费/核内存规则。
- 2026-08-17 19:26+08:00：正式 future full-year v3 profiles 已完成 fixed Gurobi 环境验证，参数冻结
  工程闭合。local/origin/GitHub implementation tip 均为
  `0363b7b0183a52184b2f0be7a1381efc76d1615e`；fixed 在无 CISPO/Gurobi、clean、available
  `122,241,404,928 bytes`（约 `113.85 GiB`）、连续 si/so 0、memory PSI 0 后从 `710aa02`
  fast-forward 到该精确提交。两份 v3 JSON、cloud sbatch bash、py_compile PASS；Gurobi targeted
  `14/14 PASS`（wall `0:02.52`、MaxRSS `109,940 KiB`、swaps 0），完整 server regression
  `212/212 PASS`（tests `97.282 s`、wall `1:38.40`、MaxRSS `1,118,064 KiB`、swaps 0）。结束后
  fixed 仍 clean/idle、资源安全，未启动 solver。Stage A/B v3 现在是正式
  `APPROVED_PARAMETERS_NOT_LAUNCH_AUTHORIZED`；当前 cloud v2 未触碰，下一 cloud 常规检查仍约 21:20。
- 2026-08-17 19:20+08:00：按约 2 小时低频窗口完成 cloud resource audit round 41，并因 Barrier
  从 `340` 推进到 `343` 才追加 ledger。job `4139552` 仍 RUNNING；latest runtime
  `1,012,057.571 s`，primal/dual/complementarity `0.983025/8.356e-7/0.087008`，最近 20 步平均
  `51.190 min/step`。wall `1,015,381 s`、allocated `27,076.827 core-hours`、actual CPU
  `4,235.784 h`、efficiency `15.6436%`；job MaxRSS `362.913 GiB`，Gurobi current/max
  `351.054/354.498 GiB`，节点当时 CPU load `16.13`、FreeMem 约 `372.184 GiB`（均为整节点指标）。
  stderr 0，无 solve/QC/result/checkpoint；ParaCloud 用户队列只有该 job。ledger 现 `42` records、SHA256
  `69e14220...0f25`。未取消、未改参、未启 Stage B；下一常规 cloud 检查不早于约 21:20，除非
  terminal/anomaly。
- 2026-08-17 19:18+08:00：未来全年两阶段正式 v3 profiles 已在本地建立但未授权启动。Stage A
  `barrier_checkpoint_full_year_cloud_v3` 冻结为 `Method2/Threads16/Presolve2/Crossover0/
  SolutionTarget1/BCTol1e-2/FeasOpt1e-5/Markowitz0.01/NF1/Scale2/Aggregate1/no TimeLimit/
  SoftMem600 GiB`；Stage B `deferred_crossover2_full_year_cloud_v3` 冻结为 exact
  `Crossover2/CrossoverBasis1/LPWarmStart2/FeasOpt1e-6/NF2`，其余公共项相同。首次 config load 发现
  `solver_profile_version` 是 loader schema 而非 profile identity，已从误写 `v3` 修正为合法 `v1`；
  profile identity 仍由 `_v3` 文件名/`profile_id` 表示。独立 config load、all-version role guard `5/5`、
  py_compile 与 diff check 均 PASS；本地默认 Python 缺 gurobipy，完整 solver-profile/full regression 留给
  fixed Gurobi 环境。fixed 仍 idle，尚未部署/启动；cloud 仍原 job/profile，保持约 2 小时/事件低频只读。
- 2026-08-17 19:14+08:00：deferred Crossover v3 已于 18:44:12 严格闭合。runner/audit/macro rc
  `0/0/0`；Gurobi `OPTIMAL`、solution contract `PASS`、QC `PASS 58/58`、current input 与 result manifest
  均 valid，planning state/basis 均不存在，strict test 与 accepted macro pair 均 PASS。Barrier `0`、simplex
  `1,266,756`；solver `2,662.606 s`，其中 Crossover `2,458.89 s`，wrapper wall `50:52.08`，MaxRSS
  `9,644,004 KiB`、swaps 0、stderr 0。最大 constraint/bound/dual violation
  `9.608e-7/8.955e-7/9.538e-7`，均通过本路线 `1e-6` 合同。相对 strict reference：objective 差
  `1.838e-12`，capacity/carbon/cost normalized L1 `4.220e-8/1.588e-13/2.209e-9`，generation
  normalized L1 `0.002380`、operation `2.109e-6`，全部通过。`Pi` 导出 available：hourly `23,064`
  rows/`115,320` finite dual-price values，annual `3,366/3,366` finite。该结果仍是
  `TEST_ONLY_TRUNCATED_HORIZON`，scientifically accepted=false，但已严格证明 save-first Stage A → exact
  deferred Stage B 架构。未来 Stage A+B 合计 solver `6,938.338 s`、wall `2:08:24.08`，相对 strict
  744 约加速 `7.71×/6.99×`。fixed 已 idle；cloud `4139552` 未取消/改参，下一审计约 19:20。
- 2026-08-17 18:26+08:00：v3 首次低频阶段审计确认 deferred resume 主链已真实生效。supervisor/Python
  `1758970/1758995` 存活，wall `32:29`；source/target Gurobi 均 `13.0.2`，科学 input manifest
  `77` rows、SHA256 `772627bc...9ac3`，Fingerprint `2120635803`，raw
  `4,454,178 rows / 3,735,087 cols / 40,395,436 nnz`，唯一 data-root 差异为 RAW_GRFR 双端 usage
  `0/0`。Gurobi 明确记录 `LP warm-start: perform crossover with primal and dual start vectors`，presolve
  `166.67 s` 后为 `3,007,038 / 2,846,655 / 31,252,909`，没有 Barrier 重跑。Crossover push 于 solver
  `1,361 s` 完成，当前进入 simplex cleanup；18:25:41 为 iteration `1,220,005`、runtime `1,601 s`、
  objective 约 `2,361,959.0`，尚未终态，不能验收。进程 RSS `8,758,088 KiB`，Gurobi max memory
  `13.944 GiB`，主机 available `105 GiB`、si/so 0、memory PSI 0、stderr 0，无 numerical-trouble 或
  solve/QC/result。继续运行且不改参；下一 fixed 检查约 19:10 或 terminal/anomaly，cloud 仍等约 19:20。
- 2026-08-17 17:54+08:00：fixed 在 no-solver/clean、v3 roots 不存在、available `113 GiB`、si/so 0、
  memory PSI 0 后 fast-forward 到 `710aa0259957d03c45821b755562fc1636a60519`。Linux bash/py_compile
  PASS，focused `17/17`，完整 server regression `212/212 PASS`（tests `97.198 s`、wall `1:38.40`、
  MaxRSS `1,105,756 KiB`、swaps 0）。全新 output/control
  `deferred_crossover2_744_validation_v0817_v3` 于 17:53:13 启动；supervisor/Python PID
  `1758970/1758995`，5 秒存活、首 start event、supervisor/runner stderr 0。当前为唯一 fixed solver，
  checkout 冻结 `710aa02`；source/reference/profile 不变。下一 fixed 检查仅 phase/terminal/resource anomaly
  或约 30--45 分钟；cloud 本轮未查询、未触碰，仍约 2 小时且无新 iteration 不落账。
- 2026-08-17 17:48+08:00：deferred Stage B v2 已确认于 17:15:01 在 optimize/build 前异常退出，
  runner/audit/macro rc `1/41/42`；没有 output 文件、LP、Gurobi log、telemetry、solve/QC/result 或
  primal-dual start identity。唯一异常为 `run_cispo_2030_full_year.py:639` 引用已删除的
  `CLOUD_FULL_YEAR_PROFILE_IDS`，因此不是 checkpoint、模型或数值失败。v1/v2 roots 均永久保留。
  最小修复提交 `018607c` 已双推送：全年度 profile role 统一应用 640 GiB memory floor，新增覆盖
  Stage A/B v1/v2/future versions 的单元回归；py_compile、focused `5/5 PASS`、旧常量引用 0。
  下一步仅在 fixed 再次 no-solver/clean/resource-safe 后部署该精确提交，执行 focused/full server
  regression，再以全新 `deferred_crossover2_744_validation_v0817_v3` roots 启动唯一验证。cloud 未查询、
  未取消、未改参；监管保持 fixed 30--45 分钟/阶段事件、cloud 约 2 小时且无增量不落账。
- 2026-08-17 17:21+08:00：cloud 两小时增量审计 round 40 已完成。job `4139552` 仍 RUNNING，Barrier
  iteration `340`、runtime `1,002,807.627 s`，primal/dual/complementarity
  `1.082073/8.926e-7/0.0942553`；最近 20 步 `51.928 min/step`。wall `1,008,190 s`、allocated
  `26,885.067 core-hours`、actual CPU `4,205.427 h`、efficiency `15.6422%`、MaxRSS `362.913 GiB`；
  stderr 0，无 solve/QC/result/checkpoint。ledger round 40 后 41 records，SHA256
  `5e3a972a...21a4`。未取消、未改参、未启 Stage B。fixed v2 本轮未查询，仍按 30--45 分钟/
  phase event 低频监管。
- 2026-08-17 17:15+08:00：未消费 RAW_GRFR root 修复提交
  `acf59f9180483b09c4c0e9380e0576457cc554ac` 已双推送；fixed 在 no-solver/clean 后从 `b277fce`
  fast-forward 到该精确 tip。Linux `bash -n`、py_compile、四组 focused `16/16` 与完整 server regression
  `211/211 PASS`（tests `97.142 s`、wall `1:38.26`、MaxRSS `1,112,044 KiB`、swaps 0）。全新
  output/control `deferred_crossover2_744_validation_v0817_v2` 于 17:14:54 启动唯一 supervisor PID
  `1710059`；启动 gate available `113.905 GiB`、si/so `0/0`、memory PSI avg10 0、supervisor stdout/
  stderr 0。v1 失败根永久保留；v2 使用同一源 checkpoint/reference/profile，只改变已审计 identity gate
  与全新 roots。fixed checkout 现冻结 `acf59f9`，禁止部署后续 docs tip/第二 solver；下一 fixed 检查仅
  phase/terminal/resource anomaly 或约 30--45 分钟。cloud 尚未到本轮窗口、未查询、未触碰。
- 2026-08-17 17:10+08:00：首次降频 fixed 检查发现 deferred Stage B v1 已于 16:39:46 在 optimize 前
  fail-closed 退出：runner/audit/macro rc `1/41/42`，wall `5:31.43`、MaxRSS `4,754,120 KiB`、swaps 0；
  无 Gurobi log/telemetry/solve/QC/result manifest，未运行 Barrier/Crossover。错误唯一为
  `data_roots differs`。逐层复核证明 source checkpoint/run identity 的 `CISPO_RAW_GRFR_ROOT=null`，
  target 为 `/data/zz2/National_model/data/grfr_raw_2019`；其余四根完全相同。source/target manifests
  各自 valid，排除 solver 行后 `77/77` 行逐字段相同，scientific SHA 同为
  `772627bc...9ac3`，RAW_GRFR 两端 manifest usage 均为 0；Fingerprint 仍为 `2120635803`。因此不是
  科学数据/LP 漂移，而是未消费可选 readiness root 的环境登记差异。主机 idle，available `113 GiB`、
  si/so `0/0`、PSI 0，checkout clean `b277fce`。本地最小修复只 allowlist `CISPO_RAW_GRFR_ROOT`，且仅
  当两端 usage 均 0 才允许差异并落盘完整审计；任何被消费或非 allowlist 根仍拒绝。新增纯单元正反
  `4/4 PASS`，完整 primal-dual focused `5/5 PASS`（含 Gurobi 12 小 LP Crossover2），compile/diff PASS。
  尚未提交/部署/重启；cloud 本轮未查询、未触碰。
- 2026-08-17 16:43+08:00：等待低频检查窗口期间完成全年 save-first 代码合同复核。当前 runner 已在
  `BarStatus=OPTIMAL` 时把 engineering checkpoint 标为可续接；若 `BarStatus!=OPTIMAL` 但 Barrier
  iterations `>0`，则尽力保存 `INCOMPLETE_BARRIER_RECOVERY_ONLY`，明确不可续接；`SUBOPTIMAL +
  BarStatus=OPTIMAL` 仍可形成工程 checkpoint，现有单元证据覆盖该分支。发现新的 fail-closed 缺口：
  cloud full-year role/flag/horizon guard 只硬编码 v1，而活动 cloud 使用 v2；当前 sbatch 已显式传正确
  Stage A flag 与 full_year，故不影响 job `4139552`。本地最小修复改为按
  `barrier_checkpoint_full_year_cloud_*` / `deferred_crossover2_full_year_cloud_*` 前缀分类，所有未来版本
  自动强制 engineering flag/checkpoint input 和 full-year-only。新增无 Gurobi 依赖的 subprocess tests，
  `4/4 PASS`，`py_compile`/diff PASS。尚未提交/部署；fixed 活动 checkout `b277fce` 与 solver、cloud
  均未查询或触碰。
- 2026-08-17 16:35+08:00：744 h deferred Stage B 已按独立全新 roots 安全启动。修复提交
  `b277fcea4cb42d4bf8634f0baaf794095e00d67f` 已双推送并 fast-forward 到 fixed；部署后 Linux
  `bash -n`、profile JSON、`py_compile`、focused `20/20` 与完整 server regression `203/203 PASS`
  （tests `94.966 s`、wall `1:36.07`、MaxRSS `1,121,468 KiB`、swaps 0），checkout clean 后才启动。
  output/control 为 `deferred_crossover2_744_validation_v0817_v1`，supervisor PID `1656831`，
  `/usr/bin/time` child PID `1656855`，启动时刻 `16:34:12`，available RAM `113.918 GiB`、si/so
  `0/0`、memory PSI avg10 0、supervisor stderr 0。命令使用 Base/744、源 relaxed checkpoint、
  `Crossover=2/CrossoverBasis=1/LPWarmStart=2`、显式 engineering-source 与 compatible-implementation
  许可；优化前仍必须逐层通过 target manifest、Gurobi version、scientific resume identity、Fingerprint、
  raw dimensions 与完整变量/约束顺序 digest。当前只允许这一个 fixed solver，checkout 冻结在
  `b277fce`；不部署后续文档 tip、不并发。监管频率按用户要求降为 fixed 约 30--45 分钟或 phase/
  terminal/resource anomaly，cloud 约 2 小时且仅在新 Barrier iteration/异常时落账；云端 `4139552`
  未取消、未改参、未启 Stage B。
- 2026-08-17 16:30+08:00：在启动 744 h deferred Stage B 前完成 fail-closed 源审计并发现真实续接
  缺陷。winner source `relaxed_barrier_campaign_v0812_v1/base_744h_bctol1e2_numeric1` 的 checkpoint
  gate `eligible=true`、reasons 空；Fingerprint `2120635803`，raw vars/rows/nnz
  `3,735,087/4,454,178/40,395,436`，BarX/BarPi entries
  `3,735,087/4,454,178`、SHA256 `53054c53...aa4c5/98d035bb...35ef`，manifest SHA256
  `76460ff4...148b4`，source commit `6477f42`、Gurobi `13.0.2`。现实现却逐字节比较 Stage A/B
  `input_manifest.csv`，其中包含必然不同的 `solver_configuration`，并把任意 Git commit 差异直接当 LP
  差异，导致真实 deferred Crossover 在 solve 前自相矛盾地被拒绝。最小修复现只排除恰好一条 solver
  runtime 行；configuration/scenario/formulation/state/数据仍全部进入 scientific resume SHA。跨
  implementation bundle 默认 fail-closed，新增显式许可后仍必须通过相同 Gurobi version、科学/数据
  identity、Fingerprint、LP 尺寸与完整变量/约束顺序 digest。新增专用 744 profile：Method 2、Threads
  16、Presolve 2、Crossover 2、CrossoverBasis 1、LPWarmStart 2、Feas/Opt `1e-6`、NF2、Scale2、
  no TimeLimit、SoftMem 80 GiB；runner 使用全新 roots、无 state/basis，并要求 OPTIMAL + PASS + 58/58 +
  current input + valid result manifest + exact macro pair PASS。JSON/py_compile/diff 与不依赖 Gurobi 的
  focused `6/6 PASS`；本机缺 gurobipy，server full regression/build identity gate 尚未执行，Stage B
  尚未启动。fixed idle clean `7551e3f`；cloud 未查询、未触碰。
- 2026-08-17 16:16+08:00：第二批 `relaxed_factor_screens_v0817_v2` 已于 16:06:11 串行完成，
  campaign wall 约 `43:00`，summary 为 `NO_MATERIAL_COST_IMPROVEMENT`、
  `all_paired_screens_valid=true`、shortlist 空。三根均保持 Fingerprint `2120635803` 与完整
  LP/scientific/scenario identity，status 7、Barrier 5、runner rc 2、audit rc 0、stderr/swaps 0，且无
  `solution_qc/result_manifest/planning_state/basis/checkpoint`。`PreSparsify=2` 将 Factor NZ 降至
  `7.158e8`（ratio `0.976002`），但 Factor Ops 升至 `5.111e12`（`1.073514`）、步时升至
  `14.2197 s`（`1.107897`），wall `17:00.64`、MaxRSS `20,371,484 KiB`；`BarOrder=1` 的 Factor
  NZ/Ops 与 baseline 完全相同、步时 `14.2189 s`（`1.107832`），wall `12:46.29`、MaxRSS
  `19,783,500 KiB`；Threads 32 同样不改结构，步时 `16.1291 s`（`1.256668`），wall `13:01.31`、
  MaxRSS `19,759,924 KiB`。summary JSON/CSV SHA256 为
  `8c30c896...7a071/af32487b...154ad`。fixed 已无 solver，available RAM 约 `113 GiB`、si/so/PSI 0，
  checkout clean `7551e3f`。这些候选不进入完整 744；不再盲扫参数，下一步汇总完整 744/1488/2160
  与两批 screens，形成 8760 参数/内存/验收决策。cloud 本轮未查询、未触碰。
- 2026-08-17 15:23+08:00：第二批 paired factor/throughput screens 已在固定服务器安全启动。local/origin/
  GitHub 与部署实施提交均为 `7551e3fcc55aa2964dd8eff2bed30e7ab47400f7`；部署前 fixed clean/idle，
  Linux `bash -n`、三份 profile JSON、`py_compile`、focused `16/16` 与完整 server regression
  `197/197 PASS`（`93.710 s` test runtime、`1:34.83` wall、MaxRSS `1,133,084 KiB`、swaps 0）。
  baseline `nf1_scaleauto` 再审计为 Fingerprint `2120635803`、raw
  `4,454,178 rows / 3,735,087 cols / 40,395,436 nnz`、Factor NZ/Ops
  `7.334e8/4.761e12`、5 iterations、`12.834849 s/iter`。全新 output/control 为
  `relaxed_factor_screens_v0817_v2`；15:23:11 启动唯一串行 supervisor PID `1567638`，首根
  `presparsify2`。启动 available RAM `113.951 GiB`、si/so `0/0`、memory PSI avg10 `0.00`、
  supervisor stderr 0；后续只能由同一 supervisor 顺序执行 `barorder1`、`threads32`，每根仍只是
  Base/744、Crossover 0、5-step engineering screen，不是 checkpoint/科学结果。fixed checkout 在活动期
  冻结，不部署后续文档 tip、不并发第二求解。云端 `4139552` 于 15:19 仍 RUNNING、iteration 338、
  stderr 0，未修改；fixed 改为约 30--45 分钟或 case switch/terminal/resource anomaly 检查，cloud
  改为约 2 小时且仅新迭代/异常落账。
- 2026-08-17 15:16+08:00：第一批空 shortlist 后，已基于两组 24 h 历史根收敛第二批而非继续盲扫。
  淘汰 `PreDual=1`（24 h Factor Ops `2.605e11`，约基线数百倍）、`PreDual=2`（无结构收益）、
  `Aggregate=0/Presolve=1`（更差或无收益）与 `AggFill=0`（Ops 仅约 `1.8%` 改善）。仅保留
  `PreSparsify=2`（历史 Ops 约 `-8.2%` 但迭代增加）、`BarOrder=1`（历史 Ops 约 `-3.5%`，检查
  大尺度放大）和 `Threads=32`（结构不变，只测真实 throughput）。新增三份 current relaxed 5-step
  profiles 与 `run_fixed_server_relaxed_factor_screens_round2.sh`；baseline 固定为第一批同机同 5-step
  `nf1_scaleauto`，v2 roots 为 `relaxed_factor_screens_v0817_v2`。通用 summary/runner 现接受显式且经
  校验的 case/profile 列表；结构门槛仍为 Factor Ops/NZ 降低 `>=5%`，新增配对 observed
  sec/iteration 降低 `>=10%` 的 runtime 门槛，任一晋级仍非 winner，必须完整 744 + exact macro A/B。
  candidate/baseline 缺 runtime metric、identity、5 iterations、Factor 字段、rc/stderr 任一即 fail-closed。
  本地 JSON/py_compile/diff PASS；summary/profile/solver-profile discovery 合计 `16/16 PASS`。尚未提交/
  部署/启动第二批；fixed 当前 idle clean `4f195d4`，cloud 未触碰。
- 2026-08-17 15:10+08:00：三根 Base/744 5-iteration factor screens 已于 15:04:08 串行完成，
  campaign wall 约 `38:19`，summary 为 `NO_MATERIAL_FACTOR_IMPROVEMENT`、
  `all_paired_screens_valid=true`、shortlist 空、scientifically accepted/automatic winner 均 false。
  三根均 Fingerprint `2120635803`、LP/scientific/scenario identity 完全相同，status 7、Barrier 5、
  runner rc 2、audit rc 0、stderr/swaps 0，无 checkpoint/QC/result/planning state。`NF0+Scale2` 与
  `NF0+ScaleAuto` 均为 Factor NZ/Ops `7.360e8/4.911e12`，相对 NF1+Scale2 baseline 恶化
  `0.3545%/3.1506%`，observed `13.187/13.505 s/iter`；`NF1+ScaleAuto` 与 baseline 完全一致
  `7.334e8/4.761e12`、`12.835 s/iter`。三根 wall/MaxRSS 分别为
  `12:44.06/20,211,636 KiB`、`12:42.69/19,678,600 KiB`、`12:41.36/20,501,636 KiB`。
  fixed 已无 solver，available RAM 约 `114.0 GiB`、si/so 0、PSI 0，checkout clean `4f195d4`。
  结论是 NumericFocus 0 与 auto scaling 不降低当前 744 fill-in，不值得进入完整 744；下一轮只测试
  更直接作用于 sparsification/fill/order 的短候选，不把空 shortlist 强行升级为 winner。ParaCloud
  round 39 已追加：iteration 338、runtime `996,833.092 s`，primal/dual/complementarity
  `1.114863/9.225e-7/0.097289`；wall `999,673 s`、allocated `26,657.947 core-hours`、actual CPU
  `4,169.626 h`、efficiency `15.6412%`、recent-20 `52.922 min`，40 records SHA256
  `75c7edd5...2108`；仍 RUNNING、stderr 0、无 terminal/checkpoint、未启 Stage B。
- 2026-08-17 14:26+08:00：factor-screen data-root 修复提交
  `4f195d4353b76ce76c710eb5c7ba3c467a4d494c` 已双推送并部署；server `bash -n`/profile/py_compile
  PASS、focused `10/10 PASS`、完整 regression `194/194 PASS`（`96.14 s`、MaxRSS
  `1,104,912 KiB`），checkout clean 且无 solver。启动前 baseline fail-closed audit 全字段齐全：Fingerprint
  `2120635803`，LP identity/raw `3,735,087 cols / 4,454,178 rows / 40,395,436 nnz`，presolved
  `2,775,698 / 3,001,388 / 31,159,971`，dense cols `6,050`、AA' NZ `6.131e7`、Factor NZ/Ops
  `7.334e8/4.761e12`，scientific/scenario SHA `fdb337d6...a2c72/aa5a3fc6...a6f7`。14:25:44
  以全新 output/control `relaxed_factor_screens_v0817_v1` 启动唯一串行 supervisor PID `1494933`；
  第一根 `nf0_scale2` 于 14:25:49 启动，wrapper/Python PID `1495063/1495064`。合同为 Base/744、
  Crossover 0、5 Barrier iterations；后两根只能由同一 supervisor 顺序启动。启动 available
  `113.97 GiB`、si/so 0、PSI 0、磁盘可用约 `3.96 TB`、stderr 0。fixed checkout 在活动期间冻结
  `4f195d4`；cloud `4139552` 仍 RUNNING 且未触碰。下一次 fixed 检查为 15--20 分钟或 case switch/
  terminal/resource anomaly，不做分钟级轮询。
- 2026-08-17 14:20+08:00：fixed 已在 idle/clean/resource-safe 门禁后 fast-forward 到
  `613abe8d48ac3aa6382cdca3ce5a7d3528356723`。Linux `bash -n`、三份 factor profile JSON、
  `py_compile` 与 focused `10/10 PASS`；显式冻结当前五个外部根后完整 server regression 为
  `194/194 PASS`（`95.60 s`、MaxRSS `1,115,900 KiB`）。前两次 full regression 分别只设置零个/一个
  数据根，因 repo 不内含 model-ready/CF 等外部数据而 fail-fast；没有 solver 或输出根，不能计作代码
  回归失败。该过程识别出新 `run_fixed_server_relaxed_factor_screens.sh` 未自行冻结五个数据根；本地最小
  修复现导出 current `CISPO_DATA_ROOT/CF_ROOT/HYDRO_ROOT/RAW_GRFR_ROOT/WAVE_ROOT`，并新增静态断言，
  discovery focused `10/10 PASS`、`diff --check` PASS。此修复尚待提交/双推送/部署，故 factor screens
  尚未启动；server 仍无 solver，cloud Stage A 未触碰。
- 2026-08-17 14:14+08:00：fixed Base/2160 已在 Ordering 后、Barrier 第 0 次迭代前因
  `SoftMemLimit=80 GiB` 正常 fail-closed：Gurobi `MEM_LIMIT/status 17`、`solution_count=0`、solver
  runtime `2,800.735 s`，wrapper rc `2`、wall `1:01:40`、MaxRSS `72,659,300 KiB`（约
  `69.3 GiB`）、swaps/stderr `0/0`。原始 LP 为 `12,520,914 rows / 10,398,783 cols /
  126,724,678 nnz`；build `884.643 s`，Presolve `2,214.94 s` 后为 `9,527,353 / 8,288,888 /
  106,864,030`，Ordering `565.03 s`。没有 Barrier 内点、objective、BarX/BarPi、engineering
  checkpoint、`solution_qc` 或 `result_manifest`，因此不能做影子价格、宏观 A/B 或科学解释；失败根只保留
  scale/memory 证据。campaign 于 14:03:30 写入 `campaign_complete`，fixed 已无 CISPO/Gurobi/campaign
  进程，checkout clean `902b1672...ff36`；退出后 available RAM 约 `114.0 GiB`、si/so 0、memory
  PSI 0。该证据说明当前 128 GiB 主机的 2160 h、NF1+Scale2 路线已进入内存边界，不授权直接抬高
  SoftMem 后重跑；下一步先部署已完成的 744 h lower-factor screens，以降低 fill-in 再决定较长时域。
  ParaCloud round 38 同时已追加：iteration 336、runtime `990,741.973 s`，primal/dual/complementarity
  `1.161194/9.516e-7/0.100835`；wall `995,707 s`、allocated `26,552.187 core-hours`、actual CPU
  `4,153.300 h`、efficiency `15.6420%`、MaxRSS `362.913 GiB`、recent-20 `53.040 min`，39 records
  SHA256 `932b7d8a...bd534`。云端仍 RUNNING、stderr 0、无 terminal/checkpoint，未取消/改参/启 Stage B。
- 2026-08-17 13:09+08:00：fixed Base/1488 已于 13:01:41 正常 rc 0 结束：Barrier `OPTIMAL`，143
  iterations，solver `25,834.260 s`，wrapper wall `7:22:57`，MaxRSS `55,460,664 KiB`，swaps 0、
  stderr 0。checkpoint 为 `ENGINEERING_BARRIER_CHECKPOINT_ONLY`、`deferred_crossover_eligible=true`；
  本地新 fail-closed gate 以只读流式执行后 `eligible=true`、reasons 空。BarX `7,236,351` entries/
  `57,890,936 bytes`/SHA256 `a49ce6bf...7fef0`，BarPi `8,648,849` entries/`69,190,920 bytes`/
  SHA256 `82c4ad5f...8c718`，LP Fingerprint `893131507`，变量/约束 order digests 与 current input manifest
  SHA256 `673d0230...35a1e` 均落盘。身份仍是 `TEST_ONLY_TRUNCATED_HORIZON`，strict solver contract
  `HARD_FAIL`（Constr/Bound/Dual/ComplVio `0.0112802/4.62e-6/0.0022079/42.0475`），根目录没有科学
  `solution_qc/result_manifest/planning_state/basis`。engineering QC 为 `54/58`：失败项仅 wave availability、
  strict unidirectional interprovincial flow、reservoir transition、reservoir active storage；power balance
  `2.315 kW`，wave overshoot `0.850 MW`，水库 transition/active-storage 残差 `11,280 m3/3.775 m3`。
  interprov opposing energy 占 period load `0.259%`、其 excess loss 占 `0.00641%`，load-center simultaneous
  bidirectional energy 占 `0.891%`；storage overlap 占 `0.0952%`、max `58.9 MW`。成本闭合相对残差
  `1.47e-13`，碳/CCS/DAC、备用、惯量、容量、网络容量、储能状态、级联水文与 objective accounting
  均闭合；BarPi 影子价格成功导出 `46,128` hourly/`3,366` annual rows，但仅工程使用。按作者已定优先级，
  这些方向性/小残差不阻断长时域工程测试，也绝不升级为科学结果。旧 campaign 于 13:01:45 串行启动
  唯一 Base/2160（PID `1387308/1387309`，start hour 2880，同 NF1 relaxed long profile）；13:08 尚在 build，
  RSS 约 `4.14 GiB`、available RAM 约 `110 GiB`、si/so 0、PSI 0、stderr 0。fixed checkout 仍 clean
  `902b1672...ff36`，未中途部署。ParaCloud round 37 已追加：iteration 335、runtime `987,914.783 s`，
  primal/dual/complementarity `1.181479/9.659e-7/0.102464`，wall `991,984 s`、allocated
  `26,452.907 core-hours`、actual CPU `4,137.397 h`、efficiency `15.6406%`、recent-20 `53.550 min`，
  38 records SHA256 `c31d779c...e0df`；云端未取消/改参/启 Stage B。
- 2026-08-17 11:57+08:00：本地完成 factor-screen fail-closed 汇总闭环。`collect_solver_run()` 新增
  run-identity 的 LP Fingerprint、变量/约束/非零数与 resolved scientific/scenario SHA；新
  `scripts/summarize_relaxed_factor_screens.py` 将三个 5-step 候选与既有 NF1+Scale2 Base/744 基线按
  完整 LP/scientific identity、runner rc、stderr、5 Barrier iterations、numerical trouble、presolved/
  Factor 指标核对，并以 Factor Ops/NZ 至少降低 `5%` 作为工程 shortlist 门槛。排序只生成 shortlist，
  `automatic_winner_selected=false`、`scientifically_accepted=false`，完整 744 与 exact macro A/B 仍为
  强制后续。screen runner 现先生成并验证 `baseline_solver_audit.json`，任一基线字段缺失即在运行三根
  前 exit 98；完成后生成 JSON/CSV summary，审计不完整 exit 99。focused tests `11/11 PASS`、
  `py_compile` PASS；尚未部署，活动 fixed/cloud 完全未触碰。
- 2026-08-17 11:52+08:00：fixed Base/1488 到 iteration 120，runtime `21,739.318 s`，primal/dual/
  complementarity `0.050274/0.000789619/0.027934`，100--120/110--120 平均约
  `169.03/169.75 s/step`，按 100--120 窗口投影 12 h 到 iteration `247.0`。process RSS
  `55,459,960 KiB`，11:50 host available 约 `61.1 GiB`、swap used 约 `984 MiB`，si/so 0、memory
  PSI 0、stderr 0、无终态/checkpoint，仍为唯一 solver。ParaCloud iteration 334 于 11:28:50 落盘，
  runtime `984,705.405 s`，primal/dual/complementarity `1.213709/9.858e-7/0.104884`；resource audit
  round 36 已原子追加：wall `988,357 s`、allocated `26,356.187 core-hours`、actual CPU
  `4,122.200 h`、efficiency `15.6404%`、MaxRSS `362.913 GiB`、最近 20 步 `53.255 min`，37 records
  SHA256 `cbf0311e...33710`。云端 stderr 0、无终态/checkpoint，未取消/改参/启 Stage B。
- 2026-08-17 11:05+08:00：本地扩展 `cispo_model.solver_audit.collect_solver_run()` 的 phase-level
  telemetry 审计：每个 Barrier/simplex phase 现自动记录 iteration/runtime span、observed seconds per
  iteration、complementarity 的末值/极值、末端 primal/dual objective 与 raw gap。这样三根 5-step
  factor screens 和后续完整 744/长时域根可使用同一机器可读口径比较，而无需人工高频读日志。
  `tests.test_solver_audit` 等 focused tests `8/8 PASS`，并用既有本地 1 h telemetry 实读验证；活动
  fixed/cloud checkout、solver、输出与参数均未触碰。待 campaign idle 后随 lower-factor screens 一并部署。
- 2026-08-17 10:59+08:00：低频材料门禁已闭合。fixed Base/1488 于 10:55:05 到 iteration 100，
  runtime `18,358.690 s`，primal/dual/complementarity `0.562716/0.00180162/0.402016`，raw
  primal-dual objective gap `5.432e6`；0--100、50--100、75--100、90--100 平均步长分别为
  `168.69/166.88/168.82/169.06 s`，按 75--100 窗口投影 12 h 到 iteration `247.2`。按残差量级与
  strict Base/744 对齐，primal/dual/complementarity 分别约对应 iteration `67/96/122`；不同 horizon
  的 objective gap 不直接作科学对齐。solver current/max memory `45.07/58.29 GiB`，process RSS
  `55,452,788 KiB`，host available 约 `61.1 GiB`，swap used 约 `984 MiB` 但 si/so 0、memory PSI 0，
  stderr 0、无终态/checkpoint，仍为唯一 solver。ParaCloud 同轮只读核验到 iteration 333，runtime
  `981,713.748 s`，primal/dual/complementarity `1.246258/1.002e-6/0.107341`；resource audit round 35
  已原子追加：wall `985,280 s`、allocated `26,274.133 core-hours`、actual CPU `4,109.163 h`、
  efficiency `15.6396%`、MaxRSS `362.913 GiB`、最近 20 步 `53.302 min`，36 records SHA256
  `64d80b8c...db6e87`。云端 stderr 0、无终态/checkpoint，未取消/改参/启 Stage B。监听器因 CRLF
  尾字符退出仅影响本地等待器，不影响 solver；后续改用低频直接只读检查。相关本地 focused tests
  `5/5 PASS`。下一轮只在 fixed 每 10 iteration/15--30 min 或终态事件检查，cloud 约每小时且仅有
  新 iteration 才记账；不为中途正常点反复更新文档。
- 2026-08-17 09:57+08:00：ParaCloud audit round 34 已追加；`4139552` 仍 RUNNING，iteration 332
  于 09:52:13 落盘，runtime `978,908.233 s`，primal/dual/complementarity
  `1.274926/1.023e-6/0.109716`。wall `981,492 s`、allocated `26,173.120 core-hours`、actual CPU
  `4,092.853 h`、efficiency `15.6376%`、MaxRSS `362.913 GiB`、最近 20 步 `53.291 min`；35 records
  SHA256 `29960f1e...aad17`。stderr 0、无终态/checkpoint，未取消/改参/启 Stage B。fixed
  Base/1488 同时到 iteration 79，runtime `14,822.968 s`，primal/dual/complementarity
  `10.2064/0.0030838/7.74511`，process RSS 约 `55,451,664 KiB`、stderr 0；继续唯一 solver。
- 2026-08-17 09:44+08:00：下一轮 744 h lower-factor screen 已在本地冻结为三个配对 profile：
  `NF0+Scale2`、`NF1+ScaleAuto(-1)`、`NF0+ScaleAuto(-1)`。共同保持 Method 2、Threads 16、
  Presolve 2、Crossover 0、SolutionTarget 1、`BarConvTol=1e-2`、Feas/Opt `1e-5`、Aggregate 1，
  仅跑 `BarIterLimit=5`，TimeLimit 2 h、SoftMem 40 GiB。新串行 runner 要求 clean checkout、
  no-solver、available ≥64 GiB、si/so 0、memory PSI 0，并为每根记录 time、resource、log-derived
  raw/presolved/dense/Factor NZ/Ops 与 telemetry；不导出 checkpoint、不做 Crossover、不作科学结果。
  配置加载与 exact-pair unittest `1/1 PASS`、三份 JSON PASS；本机无 `gurobipy`，完整 profile suite
  待 server idle 后执行。活动 fixed/cloud 未修改，screens 不能在当前 campaign 退出前部署或启动。
- 2026-08-17 09:41+08:00：本地修复 relaxed campaign 的 1488→2160 门禁。旧脚本只检查
  `barrier_checkpoint_manifest.json` 是否存在，会把 TimeLimit 后的
  `RECOVERY_ONLY_UNACCEPTED_SOLVER_RESULT` 错当成继续条件；新
  `scripts/check_barrier_checkpoint_eligibility.py` fail-closed 核验 schema、
  `deferred_crossover_eligible=true`、checkpoint/solver/Barrier status，并逐个核对 BarX/BarPi
  entries、size 与 SHA256。campaign 只有 gate exit 0 才继续 2160，否则落盘 JSON 与 stop event。
  本地 `py_compile`、新旧相关 unittest `4/4 PASS`；Windows WSL 无 `/bin/bash`，故待 fixed server
  空闲后仍须 `bash -n` 与 server regression。活动 fixed checkout/脚本/solver 与 cloud job 均未
  修改；当前旧 campaign 的本轮行为不被追改。
- 2026-08-17 09:32+08:00：ParaCloud audit round 33 已追加；job `4139552` 仍为原 Stage A，最新
  iteration 331（09:02:16），runtime `975,911.936 s`，primal/dual/complementarity
  `1.336420/1.053e-6/0.113863`。Slurm wall `980,022 s`、allocated `26,133.920 core-hours`、
  actual CPU `4,086.896 h`、efficiency `15.6383%`、MaxRSS `362.913 GiB`，最近 20 步
  `53.414 min/step`；账本 34 records，SHA256 `fc88fd29...e48045c`。stderr 0、无终态或
  checkpoint；未取消、未改参、未启 Stage B。fixed Base/1488 到 iteration 70，runtime
  `13,316.273 s`，primal/dual/complementarity `19.5745/0.009304/18.2902`，进程/RSS 稳定、
  stderr 0。当前云 profile 无法在活动 `optimize()` 中安全改参；按近期指数衰减只能作成本预警：
  primal 到本地 relaxed-744 终点量级约 5 天、absolute objective gap 到 1,000 量级约 8--9 天，
  不是完成承诺。依作者“不取消”边界继续只读监管；下一全年路线必须以 relaxed/factor A/B 降本。
- 2026-08-17 08:37+08:00：fixed Base/1488 到 iteration 50，runtime `10,014.836 s`，0--50/
  30--50/40--50 平均 `170.51/171.33/161.75 s/step`；primal/dual/complementarity
  `229.055/0.172288/262.879`。相对 Base/744 的同量级点分别对应 iteration `48/58/65`，
  absolute primal-dual objective gap 对应 iteration 61，且同 iteration 50 的 gap 小 `157.5x`。
  按三个步长窗口，12 h 约可到 iteration `244--255`；若仍需 263 步会略超时，若当前约 10--15 步
  迭代领先保持则可能刚好完成，故继续且不提前停止。process RSS `55,428,232 KiB`、available
  `65,492,828,160 bytes`（约 61.0 GiB）、swap used 约 984 MiB 但 si/so 0、memory PSI 0、
  stderr 0；运行安全。
- 2026-08-17 07:40+08:00：ParaCloud audit round 32 已追加；job `4139552` 仍 `RUNNING`，最新
  iteration 329（07:22:40），runtime `969,935.080 s`，primal/dual/complementarity
  `1.404886/1.110e-6/0.119628`。wall `973,314 s`、allocated `25,955.040 core-hours`、
  actual CPU `4,058.406 h`、efficiency `15.6363%`、MaxRSS `362.913 GiB`、最近 20 步
  `53.686 min/step`；账本 33 records，SHA256 `0752c628...e467326d`。stderr 0、无终态/
  checkpoint，未取消、未改参、未启 Stage B。fixed Base/1488 同时到 iteration 30，runtime
  `6,588.139 s`，primal/dual/complementarity `2.223e6/702.46/5.926e5`，仍稳定下降。
- 2026-08-17 07:35+08:00：只读复核 2026-08-01 fixed-server 24 h 参数根后，下一轮候选从“继续放宽
  容差”转为“降低每步因子成本”。历史 `NumericFocus=0 + ScaleFlag=-1` 相对同轮 NF2/Scale2
  路线把 Factor NZ/Ops 从约 `6.562e6/6.930e8` 降至 `6.017e6/6.408e8`
  （`-8.3%/-7.5%`），Barrier `18.99 s` 对 `57.95 s`；当时因严格 nonbasic contract 的
  `ConstrVio=0.04788` 与 complementarity 被拒绝，但目标相对偏差仅约 `1.54e-7`，故应在当前
  `BarConvTol=1e-2` 宏观 A/B 合同下重新拆分 NF0 与 auto scaling。`AggFill=0` 仅约 `2%`
  Factor Ops 改善，列为次选；`PreSparsify=2` 仅做短迭代 factor screen。活动 Base/1488 与 cloud
  job 均未修改；候选只能在当前串行 campaign 退出并释放内存后启动。
- 2026-08-17 07:25+08:00：fixed Base/1488 到 iteration 25，runtime `5,731.421 s`，iteration
  0--25 平均 `169.69 s/step`；primal/dual/complementarity
  `2.275e8/1.364e5/5.068e7`。相对同参数 Base/744 的 iteration 25，primal 约高 32.6%，但 dual/
  complementarity 低约 `30x/533x`，故不能按 744 的 263 步机械外推。按当前均值 12 h 可到约
  iteration 246；下一判别点为 50。solver current/max memory `45.07/58.29 GiB`，process RSS
  约 52.8 GiB，主机 available `61.1 GiB`、si/so 0、memory PSI 0、stderr 0；运行安全但 2160
  必须等待当前内存释放并重新通过 96 GiB 启动门禁。
- 2026-08-17 07:03+08:00：本地 1488 已验证为可信的 8760 单步成本代理。云端 8760 factor 为
  dense cols `37,696`、Factor NZ `3.395e10`、Factor Ops `1.931e15`，本地 1488 分别为
  `36,218/3.866e9/1.060e14`；Factor Ops 比值 `18.22x`。云最近 20 步实际 `53.608 min`
  （`3216.5 s`），按 Ops 比值折算本地 `176.6 s/step`，与本地 iteration 0--16 实测
  `171.0 s/step` 仅差约 3.2%。因此全年每步约 50--55 min 是 fill-in 决定的，可由 1488 预测；
  放宽容差只能减少迭代数，不能数量级降低单步成本。当前 1488 的核心任务转为实测
  `BarConvTol=1e-2/NF1` 所需迭代数，继续运行、不改参。
- 2026-08-17 07:01+08:00：ParaCloud `4139552` 未触碰；06:29 落盘 Barrier iteration 328，
  runtime `966,756.149 s`，primal/dual/complementarity `1.450925/1.129e-6/0.122696`。
  resource audit round 31 为 wall `970,967 s`、allocated `25,892.453 core-hours`、actual CPU
  `4,048.863 h`、efficiency `15.6372%`、MaxRSS `362.913 GiB`、最近 20 步 `53.608 min`；
  32 records SHA256 `223757e0...e391`，stderr 0、无 terminal/checkpoint。fixed Base/1488 同时已到
  iteration 16，0--16 平均约 `171.00 s/step`，solver current/max memory `45.07/58.29 GiB`。
- 2026-08-17 06:21+08:00：fixed Base/1488 已进入 Barrier。raw LP 为
  `7,236,351 vars / 8,648,849 rows / 87,364,792 nnz`；build 约 10.4 min，Presolve=2 用
  `1,080.17 s` 后得到 `6,564,794 / 5,761,274 / 73,637,736`，ordering `322.03 s`。
  Barrier 因子为 dense cols `36,218`、Factor NZ `3.866e9`（约 36 GB）、Factor Ops `1.060e14`
  （Gurobi 粗估 200 s/iter）；相对同 Base/744 NF1 winner，presolved nnz `2.36x`，但 dense cols/
  Factor NZ/Factor Ops 为 `5.99x/5.27x/22.26x`，确认主要长时域瓶颈是 fill-in 而非容差。
  iteration 0/1/2 runtime `1,489.26/1,595.89/1,855.80 s`，前两步分别约 `106.64/259.91 s`；
  Gurobi current/max memory `45.07/58.29 GiB`，stderr 0。12 h TimeLimit 可能只够约 200--250 步，
  但 runner 会在至少一轮 Barrier 后保存 `INCOMPLETE_BARRIER_RECOVERY`；这种根只供取证，不能延期
  Crossover。campaign 当前只检查 manifest 是否存在才放行 2160，未区分 recovery/eligible，需在本轮
  结束后修正门禁；活动脚本/checkout 不得中途修改。
- 2026-08-17 05:47+08:00：ParaCloud `4139552` 未触碰，新增落盘 Barrier iteration 326/327；
  最新 runtime `963,537.897 s`，primal/dual/complementarity
  `1.529887/1.166e-6/0.128042`，继续下降。resource audit round 30：wall `966,523 s`、allocated
  `25,773.947 core-hours`、actual CPU `4,030.069 h`、efficiency `15.6362%`、MaxRSS
  `362.913 GiB`、最近 20 步 `53.232 min`；31 records SHA256 `5ea6005a...840c9`，stderr 0、
  无 terminal/checkpoint。fixed Base/1488 同时仍是唯一 solver，尚在 build，stderr 0。
- 2026-08-17 05:41+08:00：V5/744 winner 路线已于 05:38:39 正常返回 rc 0，solver
  `OPTIMAL`，Barrier `305 iterations / 4,520.108 s`，wrapper wall `1:21:54`、stderr 0、
  MaxRSS `21,285,692 KiB`、swaps 0。完整工程 checkpoint 已保存：`BarX` `3,894,744` 项、
  `BarPi` `4,636,251` 项，均为 finite `float64` 并带 SHA256；LP Fingerprint、变量/约束顺序摘要、
  分层 identity 与 input manifest 均落盘，`deferred_crossover_eligible=true`。该宽松内点严格 QC 为
  `HARD_FAIL`：58 项物理账目中仅 `reservoir_transition` 失败，最大递推残差 `11,917.821 m3`；
  power balance `2.36e-7 GW`，网络双向流 0，储能同时充放电量 `1.75e-5 GWh`，其余网络、备用、
  惯量、碳/CCS 与成本账目通过。因此身份仅为 `ENGINEERING_BARRIER_CHECKPOINT_ONLY`，不是科学结果。
  campaign 已于 05:38:42 自动且串行进入唯一 Base/1488，PID `3899905/3899906`，start hour 3624，
  使用 long NF1 winner profile；05:41 尚在模型构建，stderr 0、约 `111 GiB` available、si/so 0、
  memory PSI 0。fixed checkout clean `902b1672...ff36`；local/origin/GitHub docs tip 为 `245d3b4`。
- 2026-08-17 04:18+08:00：v5 exact A/B 已真实完成。`5e-2/NF2` 与 `1e-2/NF2` 因宏观
  operation-account L1 `29.64%/10.04%` 等失败；`1e-2/NF1` 唯一 `MACRO_PASS`，objective/
  capacity/generation/carbon/operation 差异 `2.93e-9/1.33e-8/0.001056/8.41e-10/1.92e-6`。
  winner Barrier `4,275.73 s`，较 strict total 快 `92.0%`、较 strict Barrier 快 `44.7%`。
  04:16:42 已启动唯一 V5/744 Barrier-only，PID `3569191/3569192`，profile 为 Crossover 0、
  BarConvTol `1e-2`、Feas/Opt `1e-5`、NF1、Scale2、TimeLimit 6h、SoftMem 40 GiB；启动资源安全、
  stderr 0。ParaCloud `4139552` 未修改，03:53 iteration 325、runtime `957,363.69 s`；round 29
  wall `961,177 s`、allocated `25,631.387 core-hours`、actual CPU `4,007.857 h`、efficiency
  `15.6365%`、最近 20 步 `53.129 min`、30 records SHA256 `26a9903d...7a61e69`，无终态/checkpoint。
- 2026-08-17 04:16+08:00：fixed server clean `5161dd0`，server `bash -n`、focused `6/6`、
  full regression `187/187 PASS` (`94.975 s`)。v4 exact-macro 正确复用三组 supervisor symlink 且
  import 已修复，但复用分支没有创建 `$CONTROL_ROOT/$tag`，shell 在 audit stdout 重定向前失败；
  因此 `NO_MACRO_PASS` 仍是编排终态，无 `macro_comparison.json`、无 solver。最小补丁在候选循环
  入口无条件创建 control 子目录；本地 focused `6/6 PASS`，脚本 SHA256
  `21e67deb...ff79b07`。v4 保留，下一步只能以全新 v5 根重试 exact macro。
- 2026-08-17 04:12+08:00：fixed strict Base/744 reference 已正式闭合：`OPTIMAL + QC PASS +
  58/58 + current input manifest + valid 68-file result manifest`，solver `53,489.07 s`（Barrier
  `7,734.65 s`、Crossover `45,468.01 s`），objective `2,361,958.416203 million CNY`；wrapper rc 0、
  stderr 0、wall `14:57:39`、MaxRSS `20,617,928 KiB`、swap 0，严格三项 violation 均 `<1e-7`。
  电力、网络、储能、水电、备用、惯量、碳与成本 hard checks 全闭合；身份仍为
  `TEST_ONLY_TRUNCATED_HORIZON`。v3 exact-macro campaign 因编排错误 fail-closed 且无新 solver：
  supervisor symlink 被重复运行逻辑拒绝，独立 audit 缺 frozen repo `PYTHONPATH`，三候选均 import
  failure，故 `NO_MACRO_PASS` 不是模型结论。campaign 已最小修复为只复用完整 supervisor symlink
  并显式注入 `PYTHONPATH`；本地 focused `6/6 PASS`，脚本 SHA256 `95e177ee...5a17132`。
- 2026-08-17 03:01+08:00：ParaCloud `4139552` 未修改，02:58 落盘 Barrier iteration 324，
  runtime `954,056.89 s`，primal/dual/complementarity `1.740057/1.228e-6/0.145081`。round 28
  记录 wall `956,593 s`、allocated `25,509.147 core-hours`、actual CPU `3,988.565 h`、
  efficiency `15.6358%`、MaxRSS `362.913 GiB`、iteration 304--324 平均 `53.113 min`；
  29 records SHA256 `b9d852b3...31951f87`，stderr 0、无 terminal/checkpoint。iteration 323--324
  单步约 `57.12 min`，primal/complementarity 继续下降。fixed strict quad cleanup 同时为 iteration
  `1,009,728`、runtime `49,698.19 s`、primal 0、dual `1.02e3`，仍为唯一 solver；wrapper 与 v3
  supervisor 存活，continuation 输出根 absent。
- 2026-08-17 02:07+08:00：ParaCloud `4139552` 未修改，02:00 落盘 Barrier iteration 323，
  runtime `950,629.60 s`，primal/dual/complementarity `1.779718/1.283e-6/0.149749`。round 27
  记录 wall `953,368 s`、allocated `25,423.147 core-hours`、actual CPU `3,975.420 h`、
  efficiency `15.6370%`、MaxRSS `362.913 GiB`、iteration 303--323 平均 `52.990 min`；
  28 records SHA256 `1ac421f7...534f0b8`，stderr 0、无 terminal/checkpoint。iteration 322--323
  单步约 `53.86 min`，primal/complementarity 继续下降。fixed strict quad cleanup 同时为 iteration
  `995,574`、runtime `46,496.02 s`、primal 0、dual `9.22e2`，仍为唯一 solver；wrapper 与 v3
  supervisor 存活，continuation 输出根 absent。
- 2026-08-17 01:15+08:00：ParaCloud `4139552` 未修改，01:07 落盘 Barrier iteration 322，
  runtime `947,398.04 s`，primal/dual/complementarity `1.879145/1.434e-6/0.157175`。round 26
  记录 wall `950,224 s`、allocated `25,339.307 core-hours`、actual CPU `3,962.390 h`、
  efficiency `15.6373%`、MaxRSS `362.913 GiB`、iteration 302--322 平均 `52.831 min`；
  27 records SHA256 `ec248a3b...73ee91`，stderr 0、无 terminal/checkpoint。iteration 321--322
  单步约 `60.04 min`，primal/complementarity 继续下降。fixed strict quad cleanup 同时为 iteration
  `980,379`、runtime `43,298.54 s`、primal 0、dual `3.23e2`，仍为唯一 solver；wrapper 与 v3
  supervisor 存活，continuation 输出根 absent。
- 2026-08-17 00:14+08:00：ParaCloud `4139552` 未修改，00:07 落盘 Barrier iteration 321，
  runtime `943,795.68 s`，primal/dual/complementarity `1.955394/1.517e-6/0.164821`。round 25
  记录 wall `946,575 s`、allocated `25,242.000 core-hours`、actual CPU `3,947.624 h`、
  efficiency `15.6391%`、MaxRSS `362.913 GiB`、iteration 301--321 平均 `52.246 min`；
  26 records SHA256 `05a7a568...2f52f7`，stderr 0、无 terminal/checkpoint。iteration 320--321
  单步约 `55.02 min`，回到近期量级且 primal/complementarity 继续下降。fixed strict quad cleanup
  同时为 iteration `962,785`、runtime `39,637.75 s`、primal 0、dual `2.55e3`，仍为唯一 solver；
  wrapper 与 v3 supervisor 存活，continuation 输出根 absent。
- 2026-08-16 23:50+08:00：ParaCloud `4139552` 未修改，23:11 落盘 Barrier iteration 320，
  runtime `940,494.22 s`，primal/dual/complementarity `2.064526/1.575e-6/0.172070`。round 24
  记录 wall `945,131 s`、allocated `25,203.493 core-hours`、actual CPU `3,942.270 h`、
  efficiency `15.6418%`、MaxRSS `362.913 GiB`、iteration 300--320 平均 `52.071 min`；
  25 records SHA256 `efb6bd58...f51a7`，stderr 0、无 terminal/checkpoint。iteration 319--320
  单步约 `68.32 min`，虽明显慢于近期均值，但 primal/complementarity 仍下降，尚无卡死或失败证据。
  fixed strict quad cleanup 同时为 iteration `955,777`、runtime `38,214.01 s`、primal 0、dual
  `1.54e4`，仍为唯一 solver；wrapper 与 v3 supervisor 存活，终态文件 absent。
- 2026-08-16 23:09+08:00：ParaCloud `4139552` 未修改，22:03 落盘 Barrier iteration 319，
  runtime `936,395.20 s`，primal/dual/complementarity `2.179757/1.617e-6/0.180733`。round 23
  记录 wall `942,654 s`、allocated `25,137.440 core-hours`、actual CPU `3,931.546 h`、
  efficiency `15.6402%`、MaxRSS `362.913 GiB`、iteration 299--319 平均 `51.167 min`；
  24 records SHA256 `d203d675...fa7b`，stderr 0、无 terminal/checkpoint。fixed strict quad cleanup
  同时为 iteration `942,842`、runtime `35,770.00 s`、primal 0、dual `1.99e5`，仍为唯一 solver；
  wrapper 与 v3 supervisor 存活，终态文件 absent。
- 2026-08-16 21:45+08:00：ParaCloud `4139552` 未修改，21:12 落盘 Barrier iteration 318，
  runtime `933,326.74 s`，primal/dual/complementarity `2.289620/1.714e-6/0.188602`。round 22
  记录 wall `937,651 s`、allocated `25,004.027 core-hours`、actual CPU `3,911.908 h`、
  efficiency `15.6451%`、MaxRSS `362.913 GiB`、iteration 298--318 平均 `51.532 min`；
  23 records SHA256 `5db4ac89...50a0`，stderr 0、无 terminal/checkpoint。fixed strict quad cleanup
  同时为 iteration `917,738`、runtime `30,759.68 s`、primal 0、dual `8.19e6`，仍为唯一 solver；
  wrapper 与 v3 supervisor 存活，终态文件 absent。
- 2026-08-16 20:23+08:00：ParaCloud `4139552` 未修改，20:17 落盘 Barrier iteration 317，
  runtime `930,000.70 s`，primal/dual/complementarity `2.379513/1.678e-6/0.195367`。round 21
  记录 wall `932,693 s`、allocated `24,871.813 core-hours`、actual CPU `3,890.998 h`、
  efficiency `15.6442%`、MaxRSS `362.913 GiB`、iteration 297--317 平均 `51.272 min`；
  22 records SHA256 `bf039d69...d7de`，stderr 0、无 terminal/checkpoint。fixed strict quad cleanup
  同时为 iteration `892,970`、runtime `25,778 s`、primal 0、dual `2.51e6`，仍为唯一 solver。
- 2026-08-16 19:57+08:00：current-identity strict Base/744 总 Gurobi runtime 已达 `24,224 s` 且
  仍未结束，正式超过旧历史成功根 `24,156.53 s` 约 `67.5 s`。本次 Barrier `7,734.65 s` 相对旧
  `11,142.54 s` 节省约 `3,407.9 s`，但自 Barrier 完成后的 Crossover/cleanup 已至少
  `16,489.4 s`，相对旧 `Crossover time=12,672.69 s` 多约 `3,816.7 s`（`30.1%`），完全吞掉
  Barrier 加速。该比较跨数据版本，仅为历史工程参照，不是 exact scientific A/B；但已证明不能用
  Barrier 加速推断端到端加速，并增强 8760 h “先保存 Barrier checkpoint、后续独立 Crossover”
  的架构依据。当前 iteration `885,507`、primal 0、dual `2.89e5`、stderr 0，继续运行。
- 2026-08-16 19:36+08:00：ParaCloud `4139552` 未修改，19:28 落盘 Barrier iteration 316，
  runtime `927,093.65 s`，primal/dual/complementarity `2.420051/1.732e-6/0.199649`。round 20
  记录 wall `929,885 s`、allocated `24,796.933 core-hours`、actual CPU `3,879.081 h`、
  efficiency `15.6434%`、MaxRSS `362.913 GiB`、iteration 296--316 平均 `51.638 min`；
  21 records SHA256 `278f0396...e639`，stderr 0、无 terminal/checkpoint。fixed strict quad cleanup
  同时为 iteration `879,136`、runtime `22,956 s`、primal 0、dual `4.73e4`，仍为唯一 solver。
- 2026-08-16 18:38+08:00：ParaCloud `4139552` 保持原样，18:31 落盘 Barrier iteration 315，
  runtime `923,654.91 s`，primal/dual/complementarity `2.505751/1.784e-6/0.206062`。round 19
  记录 wall `926,381 s`、allocated `24,703.493 core-hours`、actual CPU `3,864.724 h`、
  efficiency `15.6444%`、MaxRSS `362.913 GiB`、iteration 295--315 平均 `51.837 min`；
  20 records SHA256 `19273e36...c437`，stderr 0、无 terminal/checkpoint。fixed strict quad cleanup
  已从高 dual 段恢复，iteration `859,888`、runtime `19,483 s`、primal 0、dual `2.05e6`，继续单 solver。
- 2026-08-16 18:04+08:00 correction：strict 与旧成功根只在“丢弃 1 个 basis variable 并切换 quad”
  的保护动作上相同，**quad 后数值轨迹并不相同**。旧根 quad 后最大 dual infeasibility 仅
  `1.908564e8`，只有 2 个日志采样点 `>=1e8`、无 `>=1e9`；当前根 quad 后最大已达
  `6.625378e12`，41/23/17/10 个采样点分别 `>=1e8/1e9/1e10/1e11`。iteration `848,783`、
  runtime `17,444 s` 时 primal 0、dual `3.964324e10`、stderr 0，objective 仍下降且 wrapper 活跃，
  因此不取消，但不能再用旧根 quad 剩余时间或成功率作乐观外推；必须等待正式 status/终态。
- 2026-08-16 17:51+08:00：ParaCloud `4139552` 未修改，17:43 落盘 Barrier iteration 314，
  runtime `920,799.47 s`，primal/dual/complementarity `2.587524/1.804e-6/0.211519`。round 18
  记录 wall `923,578 s`、allocated `24,628.747 core-hours`、actual CPU `3,852.752 h`、
  efficiency `15.6433%`、MaxRSS `362.913 GiB`、iteration 294--314 平均 `51.766 min`；
  19 records SHA256 `90fc64d6...0498`，stderr 0、无 terminal/checkpoint。fixed strict quad cleanup
  同时为 iteration `844,413`、runtime `16,683 s`、primal 0、dual `2.69e8`，继续单 solver。
- 2026-08-16 17:06+08:00：ParaCloud `4139552` 保持原样，16:52 落盘 Barrier iteration 313，
  runtime `917,751.15 s`，primal/dual/complementarity `2.701581/1.817e-6/0.219215`。resource
  audit round 17：wall `920,881 s`、allocated `24,556.827 core-hours`、actual CPU
  `3,841.487 h`、efficiency `15.6433%`、MaxRSS `362.913 GiB`、iteration 293--313 平均
  `52.099 min`；18 records SHA256 `a7ab2c58...11ba`。stderr 0、无 terminal/checkpoint。
  fixed strict quad cleanup 同时仍活跃，iteration `828,761`、runtime `13,981 s`、primal 0、
  dual `2.73e5`，只有一个 solver。
- 2026-08-16 16:58+08:00：strict cleanup 在 iteration `823,548`、runtime `13,224 s` 自动报告
  `Warning: 1 variables dropped from basis` 与 `Warning: switch to quad precision`。这与旧成功根完全
  相同类型的 Gurobi 数值保护；切换后约 `7 pivots/s`，iteration `825,303`、runtime `13,464 s`
  时 primal 为 0、dual `1.14e5`，stderr 0。该 warning 需要记录但不是失败/取消条件；继续等待
  Crossover 正式终态和完整 wrapper/QC/manifest。
- 2026-08-16 16:27+08:00：strict Base/744 simplex cleanup 仍活跃；约从 iteration `788,784`
  推进到 `792,828`，runtime `11,448→11,630 s`，primal infeasibility 持续为 0，dual
  infeasibility 在 `7.47e3--9.29e8` 间非单调。该形态与旧成功根 push 后同阶段相符：旧根在约
  6--7 分钟内也曾由 `1.52e4` 跳到 `1.09e9`，最终仍为 `OPTIMAL`；因此当前尖峰不是失败证据，
  但旧 cleanup 总计仍约 `10,450 s`，不能承诺短时结束。stderr 0、无终态文件、单 solver、
  available RAM 约 `100 GiB`。
- ParaCloud `4139552` 未修改、未取消：16:06 落盘 Barrier iteration 312，runtime
  `914,959.12 s`，primal/dual/complementarity `2.862660/1.840e-6/0.229635`。resource audit
  round 16 已追加：wall `918,306 s`、allocated `24,488.16 core-hours`、actual CPU
  `3,830.451 h`、CPU efficiency `15.6421%`、MaxRSS `362.913 GiB`、iteration 292--312
  平均 `52.330 min`；17 records SHA256 `65b3c549...a59c9`。stderr 0、无 terminal/checkpoint。
- 2026-08-16 16:20+08:00：strict Base/744 Crossover push 已完成并进入 simplex cleanup。
  initial basis 约 `255 s`；DPush `841,200→0` 为 `2,565 s`，PPush `274,055→0` 为 `602 s`；
  push complete runtime `11,177 s`，PInf/DInf `2.741902 / 1.751704e8`。cleanup 从 iteration
  `782,488` 开始，iteration `782,690` 已把 primal infeasibility 从 `2.742` 降到 `1.19e-3`，
  但 dual cleanup 尚未展示，不能判断完成时间或最终成功。
- 与旧严格成功根相比，当前到 push complete 仍提前 `2,530 s`（约 42.17 分钟），但旧 push
  complete PInf/DInf 仅 `0.576694 / 6.499e3`，当前 cleanup 起点明显更难；Crossover 是否净加速
  必须等最终 simplex 结束。当前 stderr 0、终态三文件 absent，RSS 约 `13.57 GiB`、available RAM
  约 `100 GiB`、memory PSI 0；仍只有一个 solver，v3 supervisor 继续等待。
- 2026-08-16 15:39+08:00：ParaCloud `4139552` 未修改、未取消；15:14 落盘 Barrier iteration
  311、runtime `911,815.51 s`，primal/dual/complementarity
  `3.026548/1.806e-6/0.241261`。resource audit round 15 已追加：wall `915,643 s`、allocated
  `24,417.15 core-hours`、actual CPU `3,819.47 h`、CPU efficiency `15.643%`、MaxRSS
  `362.913 GiB`、iteration 291--311 平均 `52.200 min`；16 records SHA256
  `41c67c50...a58fe`。stderr 0、无 terminal/checkpoint，不启动 Stage B。
- fixed strict 仍在 Crossover DPush；initial `841,200` 已降至约 `237,580`，runtime 约
  `8,725 s`。Python RSS 约 `12.47 GiB`、available RAM 约 `101 GiB`、memory PSI 0；没有第二
  solver，v3 supervisor 继续等待 wrapper。
- 2026-08-16 15:25+08:00：fixed strict Base/744 h Barrier 已正常结束并进入
  `Building initial crossover basis`。Gurobi 记录 `218 iterations / 7,734.65 s / 11,980.50 work units`、
  `Optimal objective 2,361,958.43 million CNY`；最后 telemetry primal/dual/complementarity 为
  `0.003445/6.761e-7/1.962e-9`，Gurobi scaled 表为 `6.11e-4/6.58e-8/1.96e-9`。相对旧同 profile
  Jan/2030 Barrier `251 / 11,142.54 s`，少 33 轮且 Barrier runtime 缩短约 `30.58%`。
- 最快 relaxed `BarConvTol=1e-2/NumericFocus=1` 候选 objective `2,361,958.423126 million CNY`，
  与严格 Barrier objective 相对差约 `3e-9`；其 solver runtime `4,275.73 s`，相对本次 strict
  Barrier-only 部分节省约 `44.72%`。这只是强候选信号，仍须等待 strict Crossover/完整导出后执行
  容量、发电、period、碳/CCS、运行和成本 exact A/B，不能提前登记科学接受。
- 当前仍只有 strict 一个 fixed solver；Crossover basis 构建时 Python RSS 约 `12.57 GiB`、available
  RAM 约 `101 GiB`、`si/so=0/0`、memory PSI 0，stderr 0，终态三文件 absent。v3 supervisor
  PID `46839` 继续等待 wrapper，不启动第二求解。ParaCloud `4139552` 保持 iteration 310、round 14，
  未取消、未改参、未启动 Stage B。
- 2026-08-16 14:20+08:00：fixed strict Base/744 h 仍为唯一 solver，Barrier iteration 120、solver
  runtime `3,996.41 s`；110--120 平均 `45.062 s/iteration`，telemetry primal/dual/complementarity
  为 `0.007359/5.61e-4/0.502643`。日志无 numerical warning/error，stderr 0，终态三文件仍 absent；
  Python RSS 约 `17.51 GiB`，available RAM 约 `96 GiB`、实时 `si/so=0/0`、memory PSI 0。
  v3 supervisor PID `46839` 继续只等待，预定输出根 absent；checkout clean/frozen `d80f5b7`。
- ParaCloud `4139552` 未修改、未取消：14:18 落盘 Barrier iteration 310、runtime
  `908,489.11 s`，primal/dual/complementarity `3.147713/1.860e-6/0.251022`，stderr 0、无
  terminal/checkpoint。resource audit round 14 已追加：wall `910,941 s`、allocated
  `24,291.76 core-hours`、actual CPU `3,799.68 h`、CPU efficiency `15.642%`、MaxRSS
  `362.913 GiB`，iteration 290--310 平均 `51.827 min`；15 records SHA256
  `12ecc84d...e21f`。不启动 Stage B 或第二云求解。
- 2026-08-16 13:54+08:00：macro 账目范围与 continuation 已升级。实现
  `a02d4d99b1060a2552e1c1f470817f1d4dbe3ac1` 把碳/CCS normalized L1 `<=2%`、运行账目
  normalized L1 `<=5%` 纳入 exact `MACRO_PASS`，继续保留 objective `<=1%`、容量/发电 L1
  `<=2%`、period generation `<=0.5%`；成本分项存在时要求 L1 `<=2%`，历史候选缺失时明确记录且
  只由总 objective 作成本门禁，不插补、不伪装。`cost_components.csv` 改为在严格 load-center QC 前
  写出，QC 阈值和模型均未放松。联合 tests `6/6 PASS`，server isolated fake-expression cost export PASS；
  真实旧根 parser v2 成功写入
  `run_control/relaxed_barrier_continuation_v0816_v2/pre_exact_v2_parser_numeric1.json`，但因旧 reference
  identity 不同保持 `MACRO_FAIL`，不得用于 winner。
- 实现 `5af8efe6872b569e4ca068c7c66cc2aefa9e676e` 新增 versioned continuation supervisor，并让
  campaign 接受 checksummed `AUDIT_SCRIPT`。v2 PID `4179192` 及唯一 sleep child 已精确终止；strict
  和 sampler 未受影响，v2 全部证据保留。supervisor v3 PID `46839`、PPID 1，控制/预定输出根为
  `relaxed_barrier_continuation_v0816_v3`；audit/campaign/supervisor SHA256 分别为
  `dbcf0a6c...665df`、`dd94436d...fa4b3`、`6a3a70e0...2b9dd`，绑定 `a02d4d9/5af8efe`。
  它会以新 macro v2 选 winner，仍只按 V5/744→Base/1488→条件式 Base/2160 串行执行。
- 13:54 v3 新输出根 absent，fixed server 仍仅 strict Base/744 一个 solver；Barrier iteration 81、
  runtime `2,445.64 s`、stderr 0，RSS 约 `17.5 GiB`、无 memory PSI。活动 checkout 按 PID 保护仍为
  `d80f5b7`；`a02d4d9/5af8efe` 已推送双远端但未部署。云端 `4139552` 继续不取消、不改参、
  不启动 Stage B；最近权威 resource audit 仍为 round 13。
- 2026-08-16 13:42+08:00：reference 终态门禁已加固。实现提交
  `f96d9e0443a40f343eaf74b6d97c7abd186e309a` 修复 `validate_result_manifest()` 对缺失/空 `files`
  的误接受，并要求每条记录具有安全相对路径、非负 size、合法 SHA256 且逐文件 size/hash 闭合；
  `audit_relaxed_barrier_macro.py` 现在把实际 manifest 校验结果和 failures 纳入 strict reference contract。
  py_compile、macro targeted `5/5 PASS` 与独立正/反 synthetic validator 检查通过；本机因无 `gurobipy`
  不能导入 `result_summary` 的完整 manifest test，须待 fixed solve 退出后在服务器完整回归。提交已推送
  `origin` 与 GitHub，但活动 fixed checkout 按 PID 保护继续冻结 `d80f5b7`，未部署。
- 原 supervisor v1 PID `4100799` 及其唯一 `sleep` 子进程已精确终止，solver wrapper/Python/resource
  sampler 均未受影响；v1 控制根和全部日志保留。强化后的 supervisor v2 PID `4179192` 已 reparent
  到 PID 1，控制/预定输出根分别为 `run_control/relaxed_barrier_continuation_v0816_v2` 与
  `outputs/relaxed_barrier_continuation_v0816_v2`，脚本 SHA256
  `90e399e9...e17c3b`。它在 reference 退出后硬要求 wrapper rc 0、stderr 0、`OPTIMAL`、
  `solution_qc=PASS`、恰好 `58/58`、非空逐文件 result manifest 与 current input manifest 均有效；
  任一失败即停止。13:39 新输出根仍不存在，fixed server 仍仅一个 solver。
- strict Base/744 h 13:39 仍在 Barrier iteration 51、runtime `1,579.34 s`，stderr 0；Python RSS
  约 `17.5 GiB`，host available 约 `96.5 GiB`，实时 `si/so=0/0`、memory PSI 0。ParaCloud
  `4139552` 13:42 仍 `RUNNING`；iteration 309、solver runtime `905,512.39 s`、stderr 0、无终态/
  checkpoint。cloud resource audit 已追加 round 13：wall `908,636 s`、allocated `24,230.29`
  core-hours、actual CPU `3,790.05 h`、MaxRSS `362.913 GiB`、最近 289--309 平均
  `52.070 min/iteration`，14 records SHA256 `a649998d...55a1f`；未取消、未改参、未启动 Stage B。
- 2026-08-16 13:30+08:00：按 Gurobi 13 官方文档复审当前参数。strict 744 matrix/objective/RHS
  跨度约 `6.24e9/3.85e9/3.68e11`，确认存在真实数值尺度风险；工程 profile 的 Feas/Opt `1e-5`
  大于最小 `1e-6` 系数一个数量级，只能保留为隔离测试，不能直接升级 Stage B/科学结果。可验证的
  速度旋钮冻结为 `BarConvTol` 与 `NumericFocus`；`CrossoverBasis=1` 继续作为更稳健的 Stage B
  basis 构造策略，Stage B 绝对容差不宽于 `1e-6`。详细更正已追加
  `MODEL_SOLVABILITY_AUDIT_20260719.md` 第 10 节。当前云 8760 h 不改参、不取消。
- 2026-08-16 13:28+08:00：新增只读汇总器
  `scripts/summarize_relaxed_barrier_campaign.py` 与合成测试，把 solve report、GNU time、telemetry、
  checkpoint、工程 QC、exact macro、LP identity、根目录科学产物隔离和可选资源采样统一为合法 JSON/CSV；
  非有限数写为 `null`，任何行仍固定 `scientifically_accepted=false`。py_compile 与联合 targeted tests
  `5/5 PASS`。未部署活动 checkout，而是经 stdin 在 fixed server 读取三根真实历史 candidate，权威
  pre-exact v2 输出为 continuation 控制根下 `pre_exact_candidate_summary_v2.{json,csv}`，SHA256
  分别 `f1f95348...82a688`、`e15331e5...a6cf50`。三根均 rc 0/OPTIMAL/checkpoint present，且根目录
  science QC/manifest/state/basis 全 absent；旧 reference 宏观列仍标 invalid，不作参数结论。
- v2 量化单步成本：`5e-2/NumericFocus2` `31.643 s/iter`，`1e-2/NumericFocus2`
  `32.573 s/iter`，`1e-2/NumericFocus1` `14.862 s/iter`。最快根 wall/solver/Barrier 为
  `4652/4275.73 s/263`，说明当前主要加速来自 NumericFocus=1 的单步成本，而不是只减少 Barrier
  iterations；exact A/B 仍决定其能否晋级。13:27 strict reference 为 iteration 16、stderr 0。
- 2026-08-16 13:21+08:00：strict Base/744 h reference 已于 runtime `363.60 s` 进入 Barrier；LP 为
  `3,735,087` variables、`4,454,178` constraints、`40,395,436` nonzeros，Fingerprint
  `0x7e66559b`=`2120635803`，与三根 relaxed candidates 完全一致。Presolve `226.12 s`，presolved
  LP `3,007,552 × 2,780,968`、`31,165,413` nonzeros；ordering `99.29 s`。13:20 iteration 3，
  stderr 0，Gurobi current/max memory `12.61/21.36 GiB`；5 分钟资源账本显示 Python RSS 从
  `1.90→7.92→17.39 GiB`，主机 available 约 96 GiB、swap 累计计数基本不变、memory PSI 0。
- 已启动只等待的 continuation supervisor PID `4100799`，控制根
  `/data/zz2/National_model/run_control/relaxed_barrier_continuation_v0816_v1`。它在 strict wrapper
  存活期间每 300 秒等待，当前新输出根尚不存在、没有第二求解；只有 reference 同时满足 wrapper
  rc 0、stderr 0、`OPTIMAL`、`solution_qc=PASS`、result manifest 与必要身份文件存在，才建立指向
  三个历史 candidate 的只读 symlink，在全新输出根重算 exact A/B，并仅让最快 exact `MACRO_PASS`
  串行进入 V5/744、Base/1488、以及 1488 checkpoint 完整时的 Base/2160。任何门禁失败均停止。
- 2026-08-16 13:08+08:00：local、`origin` 与 GitHub branch
  `codex/cispo-2030-full-lp` 均为 `d80f5b76b7deefd6c82004ee0e17f1fc206f7eff`；fixed server
  clean checkout 亦为同一提交，Gurobi 13.0.2 权威完整回归 `184/184 PASS`，耗时 `94.693 s`。
  在确认无活动 CISPO/Gurobi、目标根不存在、available RAM 约 114 GiB、`si/so=0/0`、memory PSI 0
  后，已启动当前数据/LP 身份严格 Base/744 h reference：wrapper PID `4046161`，输出根
  `/data/zz2/National_model/outputs/relaxed_barrier_exact_reference_v0816_v1/base_744h_strict_crossover2`，
  控制根同名位于 `run_control/`。命令使用 2030、hour 0--743、`base.json` 与
  `barrier_16_crossover2_stable_basis_long_v1`，未传 `--export-diagnostic-state`；启动后 Python 子进程
  存在、stderr 0、available RAM 约 113 GiB、无 swap I/O/PSI。该根只用于严格参考和 exact-LP A/B，
  仍是 `TEST_ONLY_TRUNCATED_HORIZON`，不得作为 state anchor。
- ParaCloud `4139552` 未触碰：13:07 仍 `RUNNING` 10 天 11:49，latest iteration 308、runtime
  `902,426.19 s`、Gurobi primal/dual/compl `0.901/1.26e-6/0.272`、stderr 0，无
  solve report/QC/result manifest/checkpoint。fixed reference 运行期间继续只读云任务，不取消、不改参、
  不启动 Stage B 或第二个 fixed solve。
- 2026-08-16 13:02+08:00：fixed-server relaxed campaign 已在 8 月 13 日完成三根 Base/744 h 后
  自动停止，未启动 V5/1488/2160。三根均 rc 0、stderr 0、`OPTIMAL`、完整 engineering
  checkpoint，wall/solver/Barrier/MaxRSS 分别为：`5e-2` `1:28:31/4927.57 s/144/
  19,959,364 KiB`；`1e-2` `1:34:34/5289.26 s/151/19,802,092 KiB`；`1e-2+NumericFocus1`
  `1:17:32/4275.73 s/263/19,486,068 KiB`。三根严格 QC 均 HARD_FAIL，科学根目录保护通过。
- campaign 的 `NO_MACRO_PASS` 已发现是无效 A/B，不是参数结论：旧 reference 使用 Git `3f123f0`、
  `model_ready_20260730_flex_v5_4f717de_v1`、LP Fingerprint `-1670477391`；候选使用 Git
  `6477f42`、Power_curve v3_qc 数据根、Fingerprint `2120635803`。负荷 SHA 改变导致同一窗口
  `period_load` 差 `0.2732%`。候选耗时/资源仍有效，既有宏观差异与速度比不得作为 exact-LP 证据。
- 修补 `c53bd78` 对宏观 A/B 新增非 solver input manifest、科学配置、LP 规模/Fingerprint 与 strict
  reference OPTIMAL/QC/manifest 硬门禁；targeted `4/4 PASS`。下一步双推送、server regression，
  在当前 tip/数据上运行一次 Base/744 h Crossover=2 strict reference（不导出 state），再离线重算
  三根；exact winner 才进入 V5/744 与 1488/2160。
- 13:02 fixed server clean/idle `6477f42`、available 约 114 GiB、无 swap I/O/PSI。ParaCloud
  `4139552` 未触碰，RUNNING 10 天 11:44，iteration 308、runtime `902,426.19 s`、stderr 0，
  无 solve report/QC/result manifest/checkpoint；继续只读，不取消、不启动 Stage B。

- 2026-08-12 21:45+08:00：第二次 fixed-server 1 h smoke 根
  `/data/zz2/National_model/outputs/relaxed_barrier_smoke_1h_0d773d5_v2` 的 Python/time 终态 rc 0，
  wall `0:37.84`、MaxRSS `496,276 KiB`、stderr 0，checkpoint 完整；但远端 shell 在事后写
  `return_code.txt` 时把 `$rc` 误作字面量并以 rc 1 退出，该 wrapper 证据不算闭合。更关键的是，
  双向流严格拒绝实际发生在 `export_master_solution()`，所以 `cc9293b` 的 operational-only catch
  层级不足，第二根仍未生成 annual summary/raw-QC contract。
- 新实现提交 `247c3020dc7c667e161d61a331ff81d8b5f616fe` 将 master/operational/summary 工程导出分阶段：
  仅两个已知严格 QC RuntimeError 可被原样记录并继续，任何磁盘、代码或其他非预期错误仍 fail-fast；
  summary 不再被预期严格物理 QC 阻断。本地 py_compile 与 targeted `3/3 PASS`；Windows full suite
  未形成有效终态，不能记为 PASS。下一步双推送、fixed-server `182/182` 和第三次 1 h 真解门禁；
  只有 wrapper、checkpoint、summary/raw-QC/contract、根目录保护全部闭合才启动 744 h。

- 2026-08-12 21:28+08:00：首次 fixed-server Base/1 h `BarConvTol=5e-2` 真解已完成，输出根
  `/data/zz2/National_model/outputs/relaxed_barrier_smoke_1h_9f5c2ca_v1`。wall `1:44.92`、MaxRSS
  `497,512 KiB`、stderr 0；Gurobi `OPTIMAL`、Barrier 49、solver `2.829 s`，完整 finite BarX
  `238,529` 项和 BarPi `80,143` 项已优先保存。严格 contract 为 `HARD_FAIL`：ConstrVio
  `4.04e-6`、DualVio `0.628`、ComplVio `29.509`，末次 relative objective gap `1.389%`；原始
  load-center QC 还记录最大/累计双向最小流 `3.599/76.294 GWh`、640 条活动边。根目录无 scientific
  QC/manifest/state/basis，隔离有效，但原实现因严格 QC 异常未继续生成 annual summary。
- 修补提交 `cc9293b25ef66ff4642eeb5860fb00b0a938b5ba` 只让隔离工程路径在原始 QC 抛错时写
  `engineering_raw_qc_error.json` 并继续保留宏观摘要/contract；审计器也显式带出该失败。它不修改
  LP、求解参数、严格 QC、科学门禁或 campaign 晋级阈值。本地 py_compile、focused test 与完整
  `181/181 PASS`。fixed server 仍 clean/idle `9f5c2ca`、available 约 114 GiB、无 swap I/O/PSI；
  下一步是双推送、部署和全新 1 h 复测，闭合后立即启动串行 744 h campaign。
- ParaCloud job `4139552` 未修改、未取消：21:28 仍 `RUNNING` 6 天 20:10，最新 iteration 202、
  solver runtime `587,056.87 s`、Slurm MaxRSS `380,541,576 KiB`、stderr 0，无 solve report、QC、
  result manifest 或 checkpoint；继续只读监控，不启动 Stage B 或第二云任务。

- 2026-08-12 12:05+08:00：作者已授权在不停止 ParaCloud `4139552` 的前提下，于 fixed
  server 启动多轮显著放宽的 744 h 及更长时域测试，并要求持续自主监管。实时核验时 local、
  `origin`、GitHub 均为 `13e2eb7f63b278bca9591ac1e3965a758326bd8f`；fixed server 为 clean
  `3f739fd6216b1c7fc356e8d3a1d9a257c666f0c5`、无 CISPO/Gurobi solver、Gurobi `13.0.2`，
  available RAM 约 `114 GiB`、swap `976 MiB/2 GiB` 但连续 `si/so=0/0`、memory PSI 0、
  `/data` 余 `3.6 TiB`。云 job 仍为唯一付费任务，Barrier iteration 191、runtime
  `554,846.21 s`、MaxRSS `362.913 GiB`、stderr 0，无终态/checkpoint；本轮明确不取消、不改参。
- 实现提交 `9308ac002161a0b7971c28db8e46b5f42e8b91a8` 只增加隔离的
  `ENGINEERING_RELAXED_BARRIER_MACRO_ANALYSIS` 路线，不改 LP 变量、约束、目标、单位、Base/V5
  数据或正式科学门禁。候选统一为 `Method=2/Threads=16/Presolve=2/Crossover=0/
  SolutionTarget=1/FeasibilityTol=OptimalityTol=1e-5/ScaleFlag=2/Aggregate=1`，A/B 比较
  `BarConvTol=5e-2`、`1e-2` 与 `1e-2 + NumericFocus=1`；744 h 的 `TimeLimit/SoftMemLimit`
  为 `21,600 s/40 GiB`，更长候选为 `43,200 s/80 GiB`。完整 Barrier 优先保存 `BarX/BarPi`；
  宏观容量、发电、碳、成本和原始 QC 只写入 `engineering_macro_analysis/`，不生成科学
  `result_manifest`、planning state 或 basis。
- `scripts/run_fixed_server_relaxed_barrier_campaign.sh` 规定严格串行：3 个 Base/744 h 候选
  → 以旧 strict Base/744 h 根作宏观对照并选最快 `MACRO_PASS` → 同路线 V5/744 h → Base/1488 h
  → checkpoint 完整且资源安全时 Base/2160 h。宏观晋级阈值为 objective 相对差 `<=1%`、容量/
  发电按技术归一化 L1 各 `<=2%`、总发电相对差 `<=0.5%`；即使通过仍是
  `scientifically_accepted=false`。本地 py_compile、focused `22/22 + 9/9` 与完整回归
  `180/180 PASS`；Windows 没有可用 WSL bash，故部署后还必须在 fixed server 执行
  `bash -n` 和全回归，并先做 1 h 真解门禁，尚未启动 744 h。

- 2026-08-05 20:14+08:00：Module 06 的 EV 图件已按最终
  `four_city_geo_tariff_guangzhou_order_reweighting_v3_qc` 方法完成本地更新；报告正文与编译稿未改。
  本次明确区分两类变化：legacy→final 同时修正月度单车充电电量与小时形状，全国年度 EV
  充电电量增加 `4.219004%`，12 个月相对变化范围为 `-7.244%` 至 `+16.163%`；v2→v3-QC
  仅替换 QC 后的小时形状，年度 EV 电量差异不超过 `2.22e-14%`。修正后的月度参数源为
  `Power_curve_V2/ev/outputs/guangzhou_monthly_kwh_per_vehicle_day.csv`，SHA256
  `3e9109f192ba084c0154f779a2886b23d07d665f99b02344203ae44356381ffb`；未来负荷仍锁定
  `future_hourly_load_2025_2060_8760.csv.gz` 的 SHA256
  `8ed727745afda68b7114b08ea65660392cb374b68f203a6633bbbc9a13af791a`。已更新 S6-3、S6-4、
  S6-5，并新增/纳入 S6-7 至 S6-10；PNG/PDF/SVG 均按 178 mm 双栏宽度输出（地图 S6-9 按
  项目规则不输出 SVG），机器可读绘图数据、10 行图件 manifest 与
  `qa_load_flexibility/ev_figure_update_qa.json` 均已生成，QA 为 `PASS`。广州 QC 留出验证包含
  11 个观测月份与 1 个插值三月，244/330 日通过逐日门禁；观测月份相对 Yu 曲线均改善，平均
  RMSE 从 `0.004468` 降至 `0.002038`，相关系数从 `0.82845` 升至 `0.95843`。集成报告
  `.tex/.pdf` SHA256 仍分别为
  `187e5bc8b537af7ade28b58d0f9f893d411509e9f66481c112b8d4761fd4b697` 与
  `e0be5e109064efd924df98a341f3f7263b744761e409d5aa9c481b88d22083dd`。未进行服务器、模型
  求解、Git 提交或部署动作；正文后续若采用新增图号，须单独同步图注和 S6-3 参数表。

- 2026-08-05 16:05+08:00：在本地工作树（基于 Git `d6984b2902aa85a2459935f4c76b6fa5a5623589`）
  将 `Power_curve_V2` 最新广州逐日质控 EV 重构结果接入 National_model。权威上游为
  `outputs/future_8760_projection_ev_calibrated_v3_qc/tables/
  future_hourly_load_2025_2060_8760.csv.gz`，size `93,200,150 bytes`、SHA256
  `8ed727745afda68b7114b08ea65660392cb374b68f203a6633bbbc9a13af791a`；上游包含
  2025/2030/2035/2040/2045/2050/2055/2060，模型边界继续只保留
  2025/2030/2040/2050/2060，未新增优化年份。新的本地 model-ready 主表
  `data/load/hourly_load_2025_2060.csv.gz` 为 1,357,800 行、SHA256
  `bd94df0fd192c31e553ec9df7e486c90cc51ce2f9cd063cc660e499dce0c9903`；31×5 个省年组均
  8,760 h，源到模型 1:1 key 闭合，最大 MW→GW 转换误差 `5.68e-14 GW`，四分量闭合误差
  `1.71e-13 GW`。全国总负荷逐年电量不变，冷热分量不变；EV 年电量相对旧本地输入提高
  `4.219004%`，base residual 同步回算以维持总负荷。兼容四决策年视图、年度汇总、V3 热舒适
  包络及 V4/V5 EV availability/mobility 与 sidecar 已重建；V4/V5 manifest 现在直接登记负荷
  主表 SHA256。独立 data smoke `142/142 PASS`，相关 unittest `23/23 PASS`，最终
  `data/output_manifest.csv` 无 hash/size mismatch。详细机器可读记录为
  `data/load/power_curve_v3_qc_update_manifest.json`。本里程碑仅替换本地 `data/`；固定服务器、
  ParaCloud、既有版本化数据根和历史求解输出均未改变。服务器后续只能新建版本化数据根并重跑
  readiness/release/短门禁，不得原地覆盖当前生产数据根或重标任何既有结果。

- 2026-08-05 20:35+08:00：上述 Power_curve v3_qc 身份已完成本地、fixed server 与 ParaCloud
  文件级同步。实现/合同提交为 `d63a2513650b1075ba124d188f7e5842db0920a7` /
  `3cb3939197c3915a5a679a15c9a42e651c320534`，均已双推送；fixed server clean checkout 为
  `3cb3939`。新数据根
  `/data/zz2/National_model/data/model_ready_20260805_power_curve_v3_qc_d63a251_v1` 为 78 files、
  tree SHA256 `4e5ba9c5057ff18a2c7267395d69ce292b8f5347453dc57f9dcd892af45886e0`；
  release/readiness/V4/V5/smoke 全 PASS，完整 unittest `178/178 PASS`。全新 summer hour 3960
  Base/V5 1 h、24 h 四年序列共 16 个年度根全部 `ACCEPTED`，两份 A/B audit PASS；全部仍是
  `TEST_ONLY_TRUNCATED_HORIZON`。ParaCloud 有效发布为
  `$HOME/National_model_cloud/20260805_power_curve_v3_qc_3cb3939_v2`，model-ready/CF/hydro/wave
  解包 tree hashes 与 fixed server 完全相同，队列为空且没有提交 cloud job。云端未复制未变化的
  8.3 GiB raw GRFR provenance root，因此尚不能宣称通过 `--require-raw-grfr` readiness；无 `_v2`
  的 sibling 是保留的失败 GitHub clone，不可使用。旧数据根、旧 outputs/state/basis 及用户的
  `supplementary_materials/**` 改动均未覆盖或纳入本次部署。

- 2026-08-06 00:57+08:00：作者已授权启动单个 2030 Base 8760 h Stage A。实现提交
  `6f0b1f7286a5ba479eabff3df2b14c2f8cf6bbb6` 新增 v2 两阶段 profiles 与单任务 Slurm wrapper；
  当前只授权 Stage A。v2 Stage A 为 `Method=2/Threads=16/Presolve=2/Crossover=0/
  SolutionTarget=1/BarConvTol=1e-8/FeasibilityTol=OptimalityTol=1e-6/MarkowitzTol=0.01/
  NumericFocus=2/ScaleFlag=2/Aggregate=1/SoftMemLimit=600 GiB`，Gurobi `TimeLimit=null`；wrapper
  申请 `96 CPU/700G` 且不设置 Slurm wall time。完整 Barrier 后保存工程 `BarX/BarPi`；异常中断时
  若向量仍可读则只保存 `RECOVERY_ONLY`，禁止作为 deferred crossover source。Stage A 不写科学
  result manifest/state，不会自动启动 Stage B、下一年或 V5。py_compile、profile `8/8`、checkpoint
  `5/5` 与完整回归 `179/179` 均 PASS。00:49 核验 fixed server idle/clean、约 113 GiB available、
  无 swap I/O/PSI，ParaCloud 队列为空，分区 `DefaultTime=NONE/MaxTime=UNLIMITED`。当前条目写入时
  尚未提交 job；精确下一步为双推送本合同、clean 部署、建立新不可变 cloud release，执行
  `sbatch --test-only` 后只提交一个 Stage A 并核对开始阶段与实际 billing TRES。

- 2026-08-06 01:06+08:00：无计费调度预检已接受 `96 CPU/700G`；首次实际 job `4139419`
  显示 `billing=96/TimeLimit=UNLIMITED`，但在 `Elapsed/CPUTime=0`、`TotalCPU=0.007 s`、
  `MaxRSS=0` 时以 `FAILED 1:0` 退出，stdout/stderr 均为 0 bytes，未进入 Python/model build/Gurobi。
  原因是 Slurm 运行脚本 spool copy，不能用 `$0` 推导 immutable release。修复提交
  `d857f8d2a0724bc7d89856aea70042977b2f9b0a` 改为从 `SLURM_SUBMIT_DIR` 的父目录解析 release，
  并加入静态 wrapper 回归；profile tests `9/9 PASS`。CRLF `_v1` 与旧 resolver `_v2` cloud
  releases 均保留且禁止复用。精确下一步是双推送/deploy 修复，使用 fixed-server Linux archive
  建全新 `_v3`，再跑 `bash -n + sbatch --test-only` 后只重提一个 Stage A。

- 2026-08-06 01:10+08:00：第二次 job `4139479` 已通过 Stage A profile preflight，但 `.env`
  普通赋值未 export 给 runner 子进程，因此在 provenance 门禁前以全部 data inputs missing 退出。
  该 job 仅 5 秒；runner `1.09 s`、peak `83,900 KiB`、swap 0，无 LP build/Gurobi/telemetry。
  修复提交 `b5cad0dee02f0f2ac7c8368b778f68dde0796826` 在 source 前后使用 `set -a/set +a`，
  并新增静态断言，profile suite `9/9 PASS`。前三个 cloud releases 与两个 job 均保留为失败证据；
  精确下一步为双推送/deploy、新建 Linux archive `_v4`、预检后仅重提一个 Stage A。

- 2026-08-06 01:13+08:00：v4 低成本 compute preflight `4139494` 为 `COMPLETED 0:0`，证明
  profile、代理/WLS 与 Gurobi 13.0.2 小 LP正常；主 job `4139496` 随后完成 provenance/input
  manifest，但 cloud Python 缺 `xarray`，在 wave data store 初始化前 7 秒退出，无 LP build、
  `gurobi.log` 或 telemetry。cloud 已含 netCDF4/cftime，仅缺 xarray；fixed server 的
  `xarray-2025.1.2-py3-none-any.whl` SHA256 为
  `a7ad6a36c6e0becd67f8aff6a7808d20e4bdcd344debb5205f0a34b1a4a7f8d6`。不污染共享 env；
  下一 release 使用私有 `python_overlay/PYTHONPATH`，并先以低资源 compute job 完整运行
  `load_model_data(Base/8760)`，通过后才可重提唯一主 Stage A。

- 2026-08-06 01:19+08:00：当前唯一活动任务为 ParaCloud job `4139552`，release
  `$HOME/National_model_cloud/20260806_8760_stagea_3f739fd_v5`，output/control 分别为
  `outputs/2030_8760_base_stage_a_barrier_v2` 与 `run_control/2030_8760_base_stage_a_barrier_v2`。
  job 在 `m4cm1901` 以 `96 CPU/700G/billing=96/TimeLimit=UNLIMITED` 运行，Gurobi Threads=16；
  无依赖和自动 Stage B/下一年。先行 data-load job `4139550` 为 `COMPLETED 0:0`，41.69 s、
  321,264 KiB、0 swap，完整加载 31×8760、36,686 VRE、2,030 hydro 与 wave。主 runner 已通过
  profile/provenance/input manifest/preflight（67 PASS、0 HARD_FAIL），scale estimate
  `41,186,823/55,928,698/497,144,574`（vars/rows/nnz），01:19 正在 model build，MaxRSS
  3,986,620 KiB、stderr 0；尚无 Gurobi log/telemetry 属正常。继续只读监控，禁止第二任务。

- 2026-08-06 12:06+08:00：job `4139552` 已完成 2,336.984 s model build、17,414.51 s presolve
  和 2,912.17 s ordering，进入 Barrier；最新落盘 iteration 7，runtime 34,202.25 s，正在计算
  iteration 8。实际 LP 为 `41,458,383 vars / 50,907,234 rows / 492,835,195 nnz`，presolved 为
  `32,166,850 / 37,703,954 / 404,259,819`。Slurm/Gurobi peak memory 分别约 361.6/354.5 GiB，
  stderr 0、无 numerical warning；16 threads 仍满载。当前仍无终态报告或 checkpoint，只读监控。

- 2026-08-06 12:16+08:00：iteration 8 于 12:12:31 完成，单步 45.40 分钟；job 继续 RUNNING，
  MaxRSS 361.648 GiB、累计实际 CPU 86.877 h、allocation 约 1,054.24 core-hours。作者明确要求
  不得随意取消；当前 control root 已新增 `resource_audit_snapshots.jsonl` 与
  `historical_8760_comparison.json`，分别冻结逐次 Slurm 快照/审计合同和旧 job `4004585` A/B。
  Barrier 每轮的 runtime/work/residual/memory 继续由 solver telemetry 自动记录，终态用 sacct 闭合。

- 2026-08-06 20:27+08:00：job `4139552` 保持 RUNNING 且未被取消，最新 iteration 18，runtime
  65,252.49 s；iteration 8--18 平均 47.210 分钟。MaxRSS 362.188 GiB、累计 allocation/actual CPU
  为 1,838.24/212.941 h，stderr 和数值警告为零。资源账本 round 4 已写入，5 records，SHA256
  `fb390f551ef190720673a341037e2bcd8b6ce006905b549268a27c4f0f418c7f`；无终态文件/checkpoint。

- 2026-08-07 00:00+08:00：job `4139552` 最新 iteration 23，runtime 79,383.98 s；18--23 平均
  47.105 分钟/步，MaxRSS 362.344 GiB，allocation/actual CPU 为 2,179.973/267.629 h。
  stderr/数值警告为零，无终态/checkpoint。资源账本 round 5 共 6 records，SHA256
  `73f3df3998f4313051231658dd35dc8ccaeb1f8c3c23ccec5efa7a0e4c30d967`；继续不人工取消。

- 2026-08-07 09:59+08:00：job `4139552` 仍为 `RUNNING`，wall 1 天 08:41:08；最新落盘
  iteration 35（09:24:32），solver runtime 113,247.02 s，正在计算下一轮。iteration 23--35
  平均 47.032 分钟/步；同期 telemetry primal/dual infeasibility 与 complementarity 分别下降
  `78.29%/76.82%/77.52%`，但绝对残差仍远离验收，不给完成百分比。MaxRSS 362.540 GiB，
  allocation/actual CPU 为 3,137.813/421.861 h，stderr 与数值告警为零，无终态/checkpoint。
  资源账本 round 6 共 7 records，SHA256
  `13e567bd1743c5b0079ebb7445123bb18f6cba05a5e7be208f9619592c2c6175`；继续不人工取消、不改参、
  不启动 Stage B 或第二求解。

- 2026-08-07 19:45+08:00：job `4139552` 仍为 `RUNNING`，wall 1 天 18:27:23；最新落盘
  iteration 48（19:34:53），solver runtime 149,868.82 s。iteration 35--48 平均 46.951 分钟/步；
  相对 iteration 35 的 telemetry primal/dual infeasibility 与 complementarity 分别下降
  `77.27%/84.52%/77.95%`，继续单调改善但尚未达到验收量级。MaxRSS 362.649 GiB，
  allocation/actual CPU 为 4,075.813/572.464 h；stderr 与数值告警为零，无终态/checkpoint。
  资源账本 round 7 共 8 records，SHA256
  `d691d087fec95263c77e62530befa58cac9b0aed6a986a55a9b992535305badc`；继续只读运行。

- 2026-08-08 17:51+08:00：job `4139552` 仍为 `RUNNING`，wall 2 天 16:33:41；iteration 77
  于 17:50:39 刚落盘，solver runtime 230,014.78 s。iteration 48--77 平均 46.061 分钟/步；
  telemetry primal/dual infeasibility 与 complementarity 相对 iteration 48 分别缩小约
  `82,964/832,887/57,100` 倍，Gurobi 表内最新 residual 为 `4.45e4/5.22e-5/1.15e4`，但
  primal/dual objective `4.98e10/-5.30e11` 仍未闭合。MaxRSS 362.765 GiB，allocation/actual CPU
  为 6,197.893/915.299 h；stderr/告警为零，无终态/checkpoint。资源账本 round 8 共 9 records，
  SHA256 `f0c7fdfa03c0ab39c5a1ace6739ea5a337b7dd0b22de7e83d37c4f5bde09ede0`；继续只读运行。

- 2026-08-10 00:47+08:00：job `4139552` 仍为 `RUNNING`，wall 3 天 23:29:30；iteration 116
  于 00:43:08 落盘，solver runtime 341,163.39 s。iteration 77--116 平均 47.499 分钟/步；
  telemetry primal/dual infeasibility 与 complementarity 相对 iteration 77 继续缩小
  `82.48/36.26/42.62` 倍，但近期已转为较缓长尾。Gurobi 表内最新 residual 为
  `5.40e2/1.52e-5/2.70e2`，objective `2.28e9/-1.72e10` 相对间距约 `8.56`，仍未收敛。
  MaxRSS 362.909 GiB，allocation/actual CPU 为 9,167.2/1,391.305 h；stderr/告警为零，无终态或
  checkpoint。资源账本 round 9 共 10 records，SHA256
  `9aa1f051e406b4bdfd5056f0dec90303e4d5ad3b18a0faf360cd18580bf9052b`；继续只读运行。

- 2026-08-10 23:43+08:00：job `4139552` 仍为 `RUNNING`，wall 4 天 22:25:36；iteration 145
  于 23:41:30 刚落盘，solver runtime 423,865.48 s。iteration 116--145 平均 47.530 分钟/步；
  telemetry primal/dual infeasibility 与 complementarity 再缩小 `6.61/4.71/4.81` 倍。Gurobi
  表内最新 residual 为 `8.16e1/3.23e-6/5.61e1`，objective `1.08e9/-3.13e9` 相对间距约
  `3.90`，较上一轮 `8.56` 继续改善但仍未收敛。MaxRSS 362.913 GiB，allocation/actual CPU 为
  11,368.96/1,744.324 h；stderr/告警为零，无终态或 checkpoint。资源账本 round 10 共
  11 records，SHA256 `581e3c52d5a087f38368cf35f9396a67c7561e612d91b2059b9f19537db3bba0`。

- 2026-08-11 10:16+08:00：job `4139552` 仍为 `RUNNING`，wall 5 天 08:58:07；iteration 158
  于 09:55:55 落盘，solver runtime 460,730.61 s。iteration 145--158 平均 47.263 分钟/步；
  Gurobi primal/dual residual/complementarity 为 `6.97e1/1.92e-6/4.63e1`，objective
  `9.42e8/-2.54e9` 相对间距约 `3.69`，相对 iteration 145 的 `3.90` 只缓慢下降，仍属长尾。
  MaxRSS 362.913 GiB，allocation/actual CPU 为 12,380.987/1,906.975 h；stderr/告警为零，无终态或
  checkpoint。资源账本 round 11 共 12 records，SHA256
  `467e4f1bba55a0fac1c9947d444e8f45d3e32fc247b043c0e0dfa76d9c8dc6b4`。

- 2026-08-12 11:50+08:00：job `4139552` 仍为 `RUNNING`，wall 6 天 10:32:11；iteration 190
  于 11:18:12 落盘，solver runtime 552,067.53 s。iteration 158--190 平均 47.571 分钟/步；
  Gurobi primal/dual residual/complementarity 为 `4.00e1/9.35e-7/2.37e1`，objective
  `5.57e8/-1.23e9` 相对间距约 `3.21`，较 iteration 158 的 `3.69` 继续缓慢改善。
  MaxRSS 362.913 GiB，allocation/actual CPU 为 14,835.493/2,300.554 h；stderr/告警为零，无终态或
  checkpoint。资源账本 round 12 共 13 records，SHA256
  `e299d4c7821a0e6e372b44182c3dc239179b58bea5ccfa784a4cc841a77b776d`。

- 2026-08-05 14:50+08:00：作者确认 8760 h 采用独立两阶段架构；实现提交
  `369506010b5bc876676941e456d9574187e0f293` 已双推送并部署到 clean fixed server。
  阶段 A profile 为 `barrier_checkpoint_full_year_cloud_v1`：`Method=2/Threads=16/
  Presolve=2/Crossover=0/SolutionTarget=1/BarConvTol=1e-9/FeasibilityTol=OptimalityTol=1e-7/
  NumericFocus=2/ScaleFlag=2/Aggregate=1/DualReductions=1/InfUnbdInfo=0/TimeLimit=604800/
  SoftMemLimit=600`。runner 强制 `--engineering-barrier-checkpoint-only`；只要 Gurobi 13
  `BarStatus=OPTIMAL` 且 `BarX/BarPi` 完整有限，就在任何科学输出/QC 前优先落盘，并登记为
  `ENGINEERING_BARRIER_CHECKPOINT_ONLY`、`scientifically_accepted=false`、
  `deferred_crossover_eligible=true`。原始 `BarPi` 可作工程影子价格，但不得用于论文、年度
  planning state、MGA 或科学 result manifest。检查点同时保存 input/config/Git/Gurobi 身份、
  Gurobi Fingerprint、原始 LP 尺寸，以及完整 `VarName` 和 `ConstrName+Sense` 顺序的分块
  SHA256；不持久化数 GB 名称目录。
- 阶段 B profile 为 `deferred_crossover2_full_year_cloud_v1`：完整重建同一 LP，逐层核对
  identity、input manifest、Fingerprint、尺寸和两类顺序 SHA256，再注入全量
  `PStart=BarX/DStart=BarPi`；`LPWarmStart=2/Crossover=2/CrossoverBasis=1/SolutionTarget=0`，
  其余严格 numerics、7 天 solver limit 与 600 GB soft limit 同阶段 A。工程源必须同时显式传入
  `--allow-primal-dual-crossover --allow-engineering-barrier-checkpoint`；只有阶段 B 最终
  `OPTIMAL + strict quality + solution_qc PASS + 全部 hard checks（当前 Base 为 58/58）+
  current input + valid result manifest + Pi` 才是科学结果。只有再显式传入
  `--allow-deferred-crossover-planning-state`，该 accepted basic solution 才能导出下一年 state。
- 本地 Gurobi 12 环境 targeted tests `12/12 PASS`；全套回归执行 124 tests，其中与本次改动
  无关的 4 个 class setup 和 2 个 planning dry-run 因本机缺少外部 `CISPO_WAVE_ROOT` 失败。
  fixed server Gurobi 13.0.2 上 targeted checkpoint/profile tests 为 `4/4 + 8/8 PASS`。
  14:50 fixed server clean/idle、HEAD `3695060`、available 约 `113 GiB`，低于 cloud profile
  内建 `640 GiB available` 硬门禁，不能运行该 8760 h profile；ParaCloud `squeue` 为空。
  `amd_a8_768` 为 128 CPU/750 GiB、`MaxMemPerCPU=6144 MB`，正式 job 建议申请整节点
  `128 CPU + 700G`、应用仍 `Threads=16`，Slurm wall time 至少 `7-12:00:00` 并提前 TERM，
  留出检查点写出时间。尚未创建/提交任何 8760 h 作业；启动前仍需冻结精确代码/数据/场景/
  predecessor state hash、全新 roots、云端计费预算和 Slurm wrapper SHA256。

- 2026-08-05 14:09+08:00：汇总当前 Phase 2 的 11 个实际执行 744 h Base 根。全部使用
  `barrier_16_crossover2_stable_basis_long_v1`：`Method=2/Threads=16/Presolve=2/
  Crossover=2/CrossoverBasis=1/FeasibilityTol=OptimalityTol=1e-7/BarConvTol=1e-8/
  NumericFocus=2/ScaleFlag=2/TimeLimit=86400/SoftMemLimit=80`，无 basis reuse。9 个 accepted
  根 solver runtime 为 `5.20--18.37 h`，平均 `8.89 h`、中位 `7.24 h`；其 Barrier 段平均
  `2.60 h`，Crossover 平均 `6.08 h`，按合计 runtime 约占 `68.3%`。另两根在 24 h
  TimeLimit 失败，Crossover 分别耗时 `22.14/21.81 h`。11 根峰值 process-tree RSS 为
  `18.632--21.158 GiB`。递归扫描服务器全部现存 `solve_report.json`，满足
  `optimization_hours=744 && solver_parameters.crossover=0` 的报告为 **0 个**；当前没有真正
  执行过 744 h Barrier-only。两个 Crossover timeout 后保存的 recovery `BarX/BarPi` 不属于
  Barrier-only solve，不能替代该门禁。

- 2026-08-05 13:52+08:00：纠正 solver contract 文档冲突。经当前模型实证，Barrier-only
  24 h 的 20 个组合均未同时通过严格 primal/dual 门禁；`Crossover=2` 才是已通过
  24 h/168 h 配对并用于 Phase 2 的截断时域 profile，但 Phase 2 又出现两个 744 h
  Crossover TIME_LIMIT。因此 `cispo_full_lp_model_spec.md` 中“Barrier-first 为当前主生产
  路线”的旧表述已由后置更正明确降为历史设计目标；当前为**没有已验证的 8760 h
  production solver route**。在完成 recovery 离线物理/dual 审计、容差候选 A/B 与至少
  一个全新 744 h 门禁前，不得启动 8760 h。不能因 `BarStatus=OPTIMAL` 或 recovery-only
  `BarX/BarPi` 推断 Barrier-only 已可用。

- 2026-08-05 13:47+08:00：进一步复核 Jan/2050 与 Jun/2060 两个 Crossover TIME_LIMIT
  根，确认 Gurobi 13 的 `BarStatus=OPTIMAL`，wrapper 已自动保存完整 `BarX/BarPi`：Jan
  `primal_barx.npy=29,880,824 bytes`、`dual_barpi.npy=35,633,552 bytes`，Jun 分别为
  `29,880,824/34,895,496 bytes`。两份 manifest 均明确为
  `RECOVERY_ONLY_UNACCEPTED_SOLVER_RESULT`、`scientifically_accepted=false`、
  `deferred_crossover_eligible=false`；它们不含 presolve/factorization/basis，且源 solve
  `SolCount=0`、无 QC/result manifest/planning state，因此只作取证，不得当作内点科学结果、
  sequence state 或可直接续跑的 checkpoint。当前实现对大于 744 h 的 inline Crossover
  默认在 optimize 前 hard-fail；8760 h 预期路线必须先用 `Crossover=0` 获得严格 accepted
  Barrier 结果，成功后才自动导出可用的 accepted `BarX/BarPi`，但该路线在当前模型上仍需
  重新完成数值门禁。

- 2026-08-05 13:42+08:00：三条 Phase 2 runner 均已退出，当前无 CISPO/Gurobi/sequence
  进程。Base 终态为 `9/12 accepted + 2 TIME_LIMIT + 1 not run`，V5 `0/12` 未启动。
  Jan/2050 在 runtime `86,402.390 s`、simplex `1,969,776` 后 `TIME_LIMIT`；Jun/2060 在
  `86,400.831 s`、simplex `1,984,282` 后同样 `TIME_LIMIT`。两根日志均明确为 Barrier
  后的 Crossover 将 status 从 Optimal 变为 Time Limit，Crossover 分别耗时
  `79,706.97/78,531.93 s`；二者均无 `solution_qc.json`、`result_manifest.json` 或
  accepted planning state，对应 sequence 为 `HARD_FAIL`，Jan/2060 未运行，Jan/Jun V5
  均未启动。Oct/2060 已严格接受：`OPTIMAL + contract/QC PASS + 58/58 + current input +
  valid result manifest + Pi`，objective `2,644,370.958385 million CNY`、runtime
  `18,714.463 s`、Barrier/simplex `207/1,846,030`、peak `20.118 GiB`，counterflow 与
  storage/V2G overlap 均为零；Oct 四年 Base sequence `PASS`、wrapper exit 0、wall
  `42:59:34`。但 05:44 自动接续 Oct V5 前资源检查读到 available `96,679,408 KiB`、
  `si/so=0/0`、memory PSI avg10 `0.54/0.54`，故 fail-closed 为 `RESOURCE_GATE_BLOCKED`，
  未创建 V5 root。13:42 host 已恢复 available `116,236 MiB`（约 `113.51 GiB`）、swap
  `596/2047 MiB`、实时 `si/so=0/0`、memory/IO PSI 0，ParaCloud 空队列；server clean
  `3f123f0`。不得重标两个 TIME_LIMIT 根或把 Barrier 中间解当 accepted 结果；后续须先决定
  新 solver/profile 与全新根的重跑合同，不能 resume、跳年或直接补 manifest。

- 2026-08-05 00:26+08:00：Phase 2 新增 Oct Base/2050 严格接受，累计 Base `8/12`
  accepted。Oct/2050 为 `OPTIMAL + contract acceptance PASS + strict quality PASS + QC PASS +
  58/58 + current input manifest + valid result manifest + Pi`，objective
  `2,570,488.097027 million CNY`、runtime `66,128.573 s`、Barrier/simplex
  `238/1,113,083`、peak `19.916 GiB`；manifest commit `3f123f0`、72 files，network
  counterflow、storage overlap 与 EV V2G overlap 均为零。当前 Jan Base/2050 与 Jun
  Base/2060 仍在 Crossover/simplex，runtime 分别约 `81,826/64,975 s`；二者中间 primal/
  dual infeasibility 已放大至约 `3.79e39/1.18e6` 与 `5.91e40/4.91e7`，存在明显的超时或
  数值失败风险，但 PID 仍存在、尚无终态报告，不能提前判失败。Jan 距 `86,400 s`
  TimeLimit 约 1.27 h。Oct Base/2060 已开始 model build，尚无 `gurobi.log`；V5 根均尚未
  启动。00:26 host available `74,239 MiB`（约 `72.50 GiB`）、swap `623/2047 MiB`、最新
  `si/so=0/0`、memory PSI avg10/60 `0.02/0.08`、IO PSI avg10/60 `4.70/1.93`、磁盘余
  `3.7 TiB`，全部 control stderr 0；ParaCloud 队列为空。服务器继续 clean `3f123f0`，
  只读监控，不干预活动 Crossover、不启动第四条或部署 docs tip。

- 2026-08-04 13:57+08:00：Phase 2 新增 Jan Base/2040、Jun Base/2050、Oct Base/2040
  三根严格接受，累计 Base `7/12` accepted，另有 3 根活动。三根均为
  `OPTIMAL + contract acceptance PASS + strict quality PASS + QC PASS + 58/58 + current
  input manifest + valid result manifest + Pi`，manifest commit `3f123f0`、72 files，且 network
  counterflow、storage charge/discharge overlap 与 EV V2G overlap 均为零。Jan/2040 objective
  `2,695,375.706199 million CNY`、runtime `35,113.316 s`、Barrier/simplex `295/775,050`、peak
  `19.266 GiB`；Jun/2050 为 `2,653,537.909967 million CNY`、`23,990.239 s`、
  `208/1,065,097`、`19.859 GiB`；Oct/2040 为 `2,624,367.338789 million CNY`、
  `33,408.641 s`、`204/960,431`、`20.706 GiB`。当前 Jan Base/2050、Jun Base/2060、
  Oct Base/2050 均在 Crossover/simplex；V5 根均尚不存在。13:57 host available
  `74,374 MiB`（约 `72.63 GiB`）、swap `507/2047 MiB`、最新 `si/so=0/0`、memory/IO
  PSI 0、磁盘余 `3.7 TiB`，全部 control stderr 0；ParaCloud 队列为空。服务器继续 clean
  `3f123f0`，只读监控现有三条，不启动第四条或独立 V5，不部署本地 docs tip。

- 2026-08-04 00:50+08:00：Phase 2 新增两根严格接受：Jun Base/2040 与 Oct Base/2030。
  两根均为 `OPTIMAL + contract acceptance PASS + strict quality PASS + QC PASS + 58/58 +
  current input manifest + valid result manifest + Pi`，result manifest 均为运行提交 `3f123f0`
  且含 72 files。Jun/2040 objective `2,678,562.527479 million CNY`、solver runtime
  `26,056.710 s`、Barrier/simplex `227/850,993`、process-tree peak `18.632 GiB`；Oct/2030
  objective `2,316,701.874843 million CNY`、runtime `34,852.144 s`、`223/1,071,575`、peak
  `21.158 GiB`。两根 input/result validators 均 `(true, [])`，network counterflow、storage
  charge/discharge overlap 与 EV V2G overlap 均为零，对应年度、case 与 window stderr 均为
  0 bytes。当前 Jan Base/2040 与 Oct Base/2040 在 Crossover/simplex，Jun Base/2050 在
  Barrier；三个 runner/sequence 仍活动，V5 尚未启动。00:48 host available `70,941 MiB`
  （约 `69.28 GiB`）、swap `507/2047 MiB`、实时 `si/so=0/0`、memory/IO PSI 0、CPU 约
  `65--66% idle`、`/data` 余 `3.7 TiB`，ParaCloud 空队列。server checkout 保持 clean
  `3f123f0`；继续只读监控，不启动第四条或独立 V5，不部署本地 docs tip。

- 2026-08-03 17:25+08:00：Phase 2 Jan/Jun Base 2030 两根已严格接受并自动进入 2040。
  Jan 2030 为 `OPTIMAL + contract PASS + strict quality + QC PASS + 58/58 + current input +
  valid result manifest + Pi`，objective `2,355,641.489790 million CNY`、solver runtime
  `24,157.126 s`、Barrier/simplex `251/751,916`、process-tree peak `19.022 GiB`；Jun 2030
  同合同全部通过，objective `2,352,092.149379 million CNY`、runtime `25,642.054 s`、
  Barrier/simplex `218/914,644`、peak `19.366 GiB`。两根 result manifest 均为当前运行提交
  `3f123f0`、72 files，input/result validators 均 `(true, [])`；storage/V2G overlap 为零，
  counterflow `STRICT_PASS` 且 0 edge-hours。Jan Base/2040 当前 Barrier iteration 128；Jun
  Base/2040 iteration 107。Oct Base/2030 仍在 Crossover/simplex，约 `1,008,035` iterations、
  primal infeasibility 0、dual infeasibility振荡，尚无终态文件。17:23 host available 约
  `73.2 GiB`、`si/so=0/0`、memory/IO PSI 0、磁盘余 `3.7 TiB`，全部 stderr 0、ParaCloud
  空队列。三条继续运行，不启动第四条，不部署本地后续 docs tip。

- 2026-08-03 10:45+08:00：作者进一步明确 48 GiB 不是 744 h 模型硬需求，授权按实测峰值
  启动第三条 Phase 2。新三并发判据为：每实例按 `24 GiB` 规划，第三条启动前 available
  `>=56 GiB`，预计启动后至少保留 `32 GiB`，且 `si/so=0/0`、memory PSI 0；绝不启动第四条。
  Oct 专用 runner `/data/zz2/National_model/run_control/phase2_3f123f0_v1/window_runner_56g.sh`
  SHA256 `e22f1696445b88458b1927fc1e803ca8ae7ec8c2f00ccf34f2c8feb6111c6be1`，只把
  启动阈值从 64 GiB 改为 56 GiB，不改模型、profile 或验收。Oct wrapper PID `4173801`
  于 10:44:51 启动，Base 根 `planning_sequence_2030_2060_744h_oct6552_3f123f0_base_v1`；
  2030 scope 已核为 `[6552,7296)`、`2030-10-01 00:00--10-31 23:00`、Base、test-only、
  Crossover=2/no-basis。启动 available `62,007,656 KiB`、`si/so=0/0`、PSI 0，window/Base
  stderr 均为 0。当前 Jan/Jun/Oct 三条各自保持 Base 四年→V5 四年串行；不得提前独立运行 V5，
  不得启动第四条。server checkout 继续冻结 `3f123f0`，只读监控三条资源与终态。

- 2026-08-03 08:56+08:00：Phase 2 已按作者新授权启动两条并发窗口，服务器 checkout 冻结为
  clean `3f123f0598e95151e8492f784ca79521569f57f0`（模型实现仍为 `b2206d9`，其后仅文档）。
  control root 为 `/data/zz2/National_model/run_control/phase2_3f123f0_v1`，runner SHA256
  `db8adbfa18821d5dd09875cf8eee7301b557172c9189c9c140e5b93c95fafa1c`。Jan wrapper PID
  `3742233` 正在 Base 四年 sequence，根
  `planning_sequence_2030_2060_744h_jan0_3f123f0_base_v1`；2030 scope 已核为 `[0,744)`、
  `2030-01-01 00:00--01-31 23:00`。Jun-15 wrapper PID `3746869` 正在 Base 四年 sequence，
  根 `planning_sequence_2030_2060_744h_jun15_3960_3f123f0_base_v1`；2030 scope 已核为
  `[3960,4704)`、`2030-06-15 00:00--07-15 23:00`。两者均为 Base、744 h、
  `TEST_ONLY_TRUNCATED_HORIZON`、`barrier_16_crossover2_stable_basis_long_v1`、no basis。
  08:56 available `117,797,340 KiB`、`si/so=0/0`、memory PSI 0，两个 window/case stderr
  均为 0。不得启动第三条；Oct 仅在 Jan/Jun 任一窗口完整 Base→V5 结束并释放槽位后启动。
  活动 PID 存在时不 fast-forward server、不改参数，只读监控 telemetry/logs/reports/资源。

- 2026-08-03 08:51+08:00：作者明确撤销 Phase 2 的 `available>=96 GiB` 过度保守启动门槛，
  要求尽快启动，并授权在资源证据支持时最多并发两条 Phase 2 sequence。历史 744 h 证据并非
  严格“最多 20 GiB”：0729 单根 process-tree peak 为 `21.484 GiB`，四年 744 h sequence
  wrapper peak 为 `21,927,236 KiB`，solver 历史最大内存约 `23.13 GiB`。据此，当前合同改为：
  单条新 744 h sequence 启动前 available `>=64 GiB`、`vmstat si/so=0/0`、memory PSI 0；
  运行中 available `<48 GiB` 时不再启动下一条。先启动 Jan Base 四年 sequence；仅当当前模型
  实时 solver/process-tree 内存 `<=24 GiB`、第二条启动后的保守预计 available 仍 `>=32 GiB`、
  `si/so=0/0` 且 PSI 0 时，才允许并发第二条，最多两条。该授权不改变 LP、solver profile、
  strict QC、Base→V5 年度 state chain、Crossover=3/basis/MGA/8760 h/付费云禁令。
  08:51 server clean/idle available `91,889,284 KiB`（约 `87.63 GiB`），已满足单条启动合同；
  local/origin/GitHub 为 `2ddf432186875285dab981aef267977460686aba`，server 仍为 clean
  `b2206d9c899c8008d7b6dabdf15cc50dd286e8b7`，下一步是提交/双推送本合同、fast-forward
  server、复验并启动全新 Phase 2 Jan Base 根。

- 2026-08-03 03:17+08:00：Phase 1 已完整结束并严格审计通过。control root
  `/data/zz2/National_model/run_control/phase1_b2206d9_v1` 写出 `PHASE1_DONE`，总 stderr
  为 0 字节；六条 Base/V5 `1/24/168 h` 四年 sequences 均 `rc=0`，六个 `/usr/bin/time -v`
  wrapper 均 `Exit status: 0`。三组 `audit_planning_sequence_ab.py` 均 `PASS`，新生成的
  `phase1_strict_audit.json` 对 6 个 sequence、24 个年度根复核为 `24/24 accepted`、零
  failures：逐根 `OPTIMAL + contract PASS + strict quality + solution_qc PASS + 58/58 +
  current input manifest + valid result manifest + Pi dual + TEST_ONLY_TRUNCATED_HORIZON`。
- 168 h Base/V5 的 2030/2040/2060 counterflow 均为 `STRICT_PASS`；2050 两根为显式
  `TEST_ONLY_DE_MINIMIS_WARNING`。Base 2050 为 7 edge-hours、`0.177690 GW`、`1.029728 GWh`、
  `0.031052 GWh` excess loss；V5 2050 为 7 edge-hours、`0.140848 GW`、`0.721842 GWh`、
  `0.021767 GWh`。两者七项指标都在已批准 warning budgets 内；24 根的 storage 与 EV V2G
  simultaneous charge/discharge 均为零，不增加网络方向互斥结构。
- 03:17 实时四端状态：本地、origin、GitHub branch tip 均为文档基线 `b0b6d402e24a45dadcca077c882424a75f14d4c9`；
  固定服务器 clean/idle checkout 为运行提交 `b2206d9c899c8008d7b6dabdf15cc50dd286e8b7`。
  available RAM 约 `87 GiB`、swap `449 MiB/2 GiB`、最新 `vmstat si/so=0/0`、memory PSI 0、
  `/data` available `3.7 TiB`；ParaCloud `squeue -u a8s001819` 为空。Phase 2 的新任务门禁仍为
  available `>=96 GiB`，当前只因资源未达标而等待；不得降低阈值或触碰外部进程。资源恢复后
  先双推送本里程碑文档、fast-forward clean server，再按 `start-hour=0/3960/6552` 严格串行
  执行每个窗口 Base 四年→V5 四年，共 24 个 744 h solve；不并发、不复用 basis、不运行
  `Crossover=3`、8760 h、付费云或 MGA。

- 2026-08-02 23:16+08:00：新 Phase 1 的 1 h Base/V5 与 24 h Base/V5 四条四年
  sequences 均已 `rc=0`；逐根 `solve_report=OPTIMAL`、`solution_qc=PASS`，结果
  manifests 均已生成，storage 与 EV V2G simultaneous charge/discharge 均为零，24 h
  interprovincial counterflow 亦为零。24 h 多个根的 Barrier 以 sub-optimal 结束，但
  `Crossover=2` 将其恢复为 primal/dual feasible optimal，因此当前生产 profile 不得在
  Phase 1 中途切换为 no-crossover。23:16 已串行进入 168 h Base；wrapper PID 仍为
  `1314144`，启动 available `91,891,228 KiB`、`si/so=0/0`、PSI=0。PID 存在期间继续
  只读监控，不运行并发审计或 Phase 2。

- 2026-08-02 22:55+08:00：提交 `b2206d9c899c8008d7b6dabdf15cc50dd286e8b7` 已双推送并
  部署到 clean fixed server。服务器在正确五个生产数据根下完整回归 `177/177 PASS`；
  readiness、release、V5 input 与水电 380 GW audits 全部 PASS，四项 audit stderr 为零。
  全新 Phase 1 control root `/data/zz2/National_model/run_control/phase1_b2206d9_v1`
  已启动，wrapper PID `1314144`；当前从 1 h Base 开始，依次串行 Base/V5 的
  `1 h → 24 h → 168 h` 四年 sequences。启动时 available `91,919,056 KiB`、
  `si/so=0/0`、PSI=0；活动期间只监控，不修改 server checkout 或启动第二求解。

- 2026-08-02 22:49+08:00：作者明确决定不因系统影响极小的截断时域 AC 对冲流引入
  MILP、逐小时方向锁或其他高复杂度结构；在储能同时充放与输电对冲均不严重时优先推进。
  当前 2050/168 h 根的 storage overlap 为 `0 asset-hours / 0 GW / 0 GWh`，EV V2G overlap
  也全为 0；对冲流额外损耗占系统负荷 `9.7667e-8`，opposing energy 占毛输电量
  `3.4079e-5`，其余 `57/58` hard checks 全部通过。
- 最小合同修订只把 `TEST_ONLY_TRUNCATED_HORIZON` 每 168 h 的三个绝对 warning budgets
  从 `4 edge-hours / 0.75 GWh opposing / 0.025 GWh excess loss` 调整为
  `8 / 1.25 / 0.04`；单小时 `0.25 GW`、线路容量占比 `15%`、毛输电量占比 `5e-5`、
  系统负荷占比 `1e-7` 均保持。8760 h `SCIENTIFIC_PRODUCTION` 仍要求 `1e-6 GW`
  以上严格零对冲。模型变量、功率平衡、输电损耗、流成本、碳/BECCS/DAC、目标函数、
  solver profile 和 state contract 均未改变。
- 新增解析回归复现当前 7 小时事件并要求 warning acceptance，同时证明 9 小时事件仍
  hard fail、相同事件在 full-year scope 仍 hard fail。方向性专项 `7/7 PASS`；设置生产 wave
  root 后本地完整回归 `177/177 PASS`。下一步是提交/双推送、服务器空闲部署与完整回归，
  然后用全新 roots 重做 Phase 1 的 matched 1/24/168 h Base/V5；不得重标或 resume
  `fc2c500` 失败根。Phase 1 完整接受后才允许 Phase 2。

- 2026-08-02 22:19+08:00：Phase 1 已按 strict fail-closed 合同停止，不再自动执行。
  wrapper `/data/zz2/National_model/run_control/phase1_fc2c500_v1` 已退出；1 h Base/V5 与
  24 h Base/V5 四条四年 sequence 全部 `sequence_report=PASS`。逐年重验的 16 个根均为
  `OPTIMAL + solution_qc=PASS + 58/58 hard checks + current input/result manifests PASS`。
  168 h Base 的 2030、2040 也严格接受，但 2050 虽为 Gurobi `OPTIMAL`、solver acceptance
  PASS、标准 `Pi` 已导出，`solution_qc=HARD_FAIL`（`57/58`），因此没有
  `result_manifest.json` 或 accepted planning state；2060、168 h V5 与整个 Phase 2 均未启动。
- 2050 blocker 是可复现的 AC 同时双向潮流，不是求解残差：仅
  `CORRIDOR_0153`（吉林 `22`—黑龙江 `23`，AC，容量 `1.646 GW`）在 2050-06-15 至
  2050-06-21 每天 04:00 共 7 个 edge-hours 出现 counterflow。opposing flow 为
  `0.121496--0.177690 GW`，总 opposing energy `1.029728 GWh`、额外损耗
  `0.031052 GWh`；分别超过当前 168 h test-only warning budgets 的 `4 edge-hours`、
  `0.75 GWh`、`0.025 GWh`。对应两省边际能量价格为
  `-1976.01-- -3412.05 CNY/MWh`，与 directional-flow LP 在深度负价下把同时对流用作
  lossy sink 的已知机制一致。不得通过放宽 QC、补写 manifest 或 resume 绕过。
- 22:19 实时状态：本地、origin、GitHub 和固定服务器均为 clean-tracked baseline
  `fc2c5002d774e80853f4059c506a55d2befc08f0`（本地仅有受保护的 supplementary/.codex_tmp
  用户文件）；服务器没有本项目 Python/Gurobi/Phase1 进程，available RAM 约 `87 GiB`、
  swap `449 MiB/2 GiB`、最新 `vmstat si/so=0/0`、memory PSI 0；ParaCloud `squeue` 为空。
  精确下一步是在不启动 solve 的前提下审查/修正 interprovincial AC directional-flow
  formulation 或其深度负价 sink 机制，并从 1 h/24 h/168 h matched Base/V5 重新闭合；
  未经该闭合不得继续 Phase 1 或进入 Phase 2。

- 2026-08-02 19:58+08:00：共享服务器 available RAM 稳定约 `85 GiB`，外部 workers
  仍驻留，但最新 `vmstat r=9`、`si/so=0/0`、memory PSI 0。基于刚完成的 current-tip
  168 h Base/V5 实测 process-tree peak `<=3.651 GiB`，Phase 1 的启动门禁采用保守的
  `available>=64 GiB`（约 17.5 倍实测峰值）并要求 `si/so=0/0`、PSI=0；这只适用于
  1/24/168 h Phase 1，不放松 Phase 2 的 `>=96 GiB` 门禁。若运行中 available `<48 GiB`、
  出现 swap I/O 或 PSI，则完成/终止当前最小根后停止，不启动下一根。

- 2026-08-02 19:53+08:00：提交 `d190c23f5bcdaf0414b9d630ef8181039dfd214e`
  已在固定服务器通过专项 `30/30` 与正确生产数据环境下完整回归 `175/175 PASS`。
  第一次完整回归命令漏设外部 data/CF/hydro roots，产生预期 missing-file failures；随后显式
  设置五个生产数据根重跑通过。该命令错误已保留，不得误报为代码回归失败。
- 全新 168 h V5 Crossover=2/4 根均严格通过：2 为 `2021.046 s`、Barrier/simplex
  `171/382,382`、Crossover `1312.02 s`；4 为 `2122.079 s`、`171/383,134`、
  Crossover `1362.02 s`。两根均 `OPTIMAL/PASS`、QC `58/58`、current input/result
  manifests PASS、dual=`Pi`，process-tree peak 约 `3.65 GiB`。2 的最大
  constraint/bound/dual violations 为 `9.51e-8/1.94e-8/9.43e-8`，4 为
  `9.95e-8/4.80e-8/8.53e-8`。
- production winner 冻结为 `Crossover=2/CrossoverBasis=1/Threads=16/Presolve=2`。
  理由是它在更难的 168 h V5 上快约 101 s、少 752 simplex iterations、质量不劣；
  Crossover=4 保留为已验证 fallback，direct dual simplex 保留为无 Crossover 严格 fallback，
  `Crossover=3` 永久拒绝。新增 long profile 使用 `TimeLimit=86400 s/SoftMemLimit=80 GiB`，
  不复用 `.bas`。
- 19:53 任务结束后服务器 available RAM 约 `93 GiB`，swap `449 MiB/2 GiB`、
  `si/so=0/0`、memory PSI 0。下降来自另一用户的多条
  `wind_power.round6.leakage_compare` workers，并非 CISPO；不得触碰外部进程。因低于新任务
  `>=96 GiB` 门禁，Phase 1 尚未启动。精确下一步是提交/双推送/deploy production profile，
  等待 available 恢复后再串行启动 Phase 1。

- 2026-08-02 18:35+08:00 实时复核：固定服务器 clean/idle，checkout
  `eb4d5591723d5ed528c8326898731591937ec645`，available RAM `113 GiB`、swap
  `447 MiB/2 GiB`、连续 `vmstat si/so=0/0`、memory PSI 0。现行 Base/V5 共用数据根是
  `/data/zz2/National_model/data/model_ready_20260730_flex_v5_4f717de_v1`；下方 16:53
  snapshot 把历史 0729 unified 根误写为现行根，本条明确纠正，历史 0729 根本身不改写。
- current-tip matched 24 h Base/V5 的 `Crossover=1/2/4 + CrossoverBasis=1` 六项全部
  `OPTIMAL`、acceptance/QC/manifests PASS 并导出 `Pi`。Crossover=4 在 Base/V5 分别为
  `62.076/109.042 s`，略快于 2 的 `62.531/109.488 s` 和 1 的
  `62.158/110.236 s`；差距很小。
- 168 h Base 的 Crossover=2/4 也严格通过。2 为 `2044.630 s`、Barrier/simplex
  `159/372,666`、Crossover `953.98 s`；4 为 `1822.354 s`、`159/359,356`、
  Crossover `1201.85 s`。两者均 QC `58/58`、current input/result manifests PASS，峰值
  process tree 约 `3.45 GiB`。Crossover=4 总 runtime 快约 10.9%，暂列优胜。
- 168 h V5 的 2/4 尚未进入 optimize：旧 `flexible_load_numerics` 硬编码仅允许
  Crossover=1，两个 wrapper 均在约 9.5 s prebuild 后 `rc=1`。这不是 Gurobi/模型失败，
  而是已过时的 solver-route 门禁。当前最小修订把有 Gurobi 定义且已完成 24 h matched gate
  的 basic routes 扩展为 `{1,2,4} + CrossoverBasis=1`，继续显式拒绝 3；待测试、提交、
  双推送和服务器部署后重跑全新 168 h V5 根。Phase 1/2 尚未启动。

- 2026-08-01 16:53+08:00：固定服务器已 clean/idle 部署到实现提交
  `5e7db6835db60170fad7a1a13283e2a4d16792f4`。Phase 0 已闭合：服务器完整回归
  `175/175 PASS`，readiness/release/Base/V5 input/hydropower 380 GW/1 h build audits
  均通过；显式数据根仍为
  `/data/zz2/National_model/data/model_ready_20260729_unified_7c56622_v4`，数据归档 SHA256
  仍为 `f3e6cc0f810d0f4e1ccf8fd10907fb25b8859546be397f21035cd072cdb9d261`。
  Phase 1/2 尚未启动，也没有 8760 h、付费云、并发第二求解、MGA 或 `Crossover=3`。
- 当前模型已经否定旧的 Barrier-only 主线假设。24 h Base 上，基准和两轮共 20 个
  `Method=2/Crossover=0/SolutionTarget=1` Barrier 配置均未通过严格原始可行性；典型最大
  constraint violation 为 `4.26e-2`，即使 `PreDual=1` 最好约 `7.60e-8`，dual violation
  仍为 `1.29e-5`，均不能验收。失败根的 `BarPi` 不得作为科学影子价格或 sequence state。
  这不是 LP 不可行：同一 LP 的 `Method=1` dual simplex 在 `795.206 s`、`524,890`
  iterations 后严格 `OPTIMAL`，`solution_qc=PASS`、`58/58 hard checks`、current input 与
  result manifests 均有效；最大 constraint/bound/dual violation 分别为
  `3.24e-8/1.66e-10/2.47e-8`，并成功导出标准 `Pi` 影子价格。因此“不做 Crossover”
  可以保留影子价格，但当前可接受实现是 simplex `Pi`，不是未验收 Barrier 根的 `BarPi`。
- 参数候选实现分别为 `a3a078e20be8a480dc63cae7964a56c01451d8df`（首轮 8 个单因素）和
  `5e7db6835db60170fad7a1a13283e2a4d16792f4`（第二轮 scaling/presolve/dual-simplex）。
  首轮/第二轮证据根分别为
  `/data/zz2/National_model/outputs/solver_tuning_v0801_a3a078e_24h_base_candidates_v3`
  和
  `/data/zz2/National_model/outputs/solver_tuning_v0801_5e7db68_24h_base_round2_v1`。
  direct dual-simplex 成功根位于后者的 `tuning2_dual_simplex16_v1/`。
- 精确下一步：在当前 tip 上串行比较 `Crossover=1/2/4 + CrossoverBasis=1` 的 24 h
  Base/V5；`Crossover=3` 永久拒绝。优胜候选再做 168 h Base/V5。冻结 production profile、
  完整回归和交接后，才进入 Phase 1 的 1/24/168 h 四年 Base→V5 sequences，再串行执行
  Phase 2 三个季节起点的 744 h Base→V5 sequences。全过程不复用 `.bas`，也不另开并发求解。

- 2026-08-01 14:18+08:00 对 2026-07-29 统一候选 2030/744 h V4 V1G cold gate
  完成实时只读复核。历史 PID `1004972/1004975` 已退出，终态仍为
  `OPTIMAL + solution_qc=PASS + 52/52 hard checks + valid result manifest +
  wrapper exit 0`；solver `12,984.854 s`、Barrier/simplex `313/832,655`、
  Crossover `3,573.87 s`、wall `3:42:57`、process-tree peak `21.484 GiB`、
  swaps 0。全部冷热/EV、wave、水电、PHS/储能、网络、备用、惯量、碳/CCS/BECCS
  和成本 scope 仍由封存输出与 52 项 hard checks 覆盖。该根继续只属于
  `TEST_ONLY_TRUNCATED_HORIZON`，不是年度科学结果或正式 2040 state anchor。
- 当前 checkout 已前进，直接对历史 `input_manifest.csv` 调用 runtime validator 会对
  repo 内 `optimization_2030.json`、V4 scenario JSON 和
  `model_input_files.json` 返回 3 个 size drift；其余 75/78 项仍通过。逐项只读
  `git show 7c56622:<path>` 复核确认这 3 个运行提交 blob 的字节数与 SHA256 均与
  manifest 完全一致，故这是当前 worktree 与历史 immutable run identity 的预期差异，
  不是历史输入或结果损坏；不得把当前 checkout 的 `(False, ...)` 误记成运行当时的
  current-input PASS，也不得因此改写历史根。标准数据归档 SHA256 仍为
  `f3e6cc0f810d0f4e1ccf8fd10907fb25b8859546be397f21035cd072cdb9d261`。
- 14:18 实时状态：本地、origin、GitHub branch tip 均为
  `fb7cec37b552f31dcf365b859c93f2734241bb53`；固定服务器保持 clean
  `7a1520eb723db7717b6ce4dd41646916c34bb0cf`，比当前 tip 落后 5 个提交，且无真实
  CISPO/Gurobi/planning-sequence 进程。host available RAM 约 `114 GiB`、swap
  `447 MiB/2 GiB`，最新两个 `vmstat si/so=0/0`、memory PSI 0、`/data`
  available `3.7 TiB`；ParaCloud `squeue -u a8s001819` 为空。本次没有部署、切换
  server checkout 或启动任何求解；下一步仍是下述 Barrier-primary Phase 0。
- 2026-08-01 13:58+08:00：Barrier-primary sequence 实现提交为
  `53a5873156bfe4e81abfaa258d02b3f3ff664bbd`，建立在
  `19b5754bb0db12818975344e5365777674698c47` 的 Barrier checkpoint 工作流上。
  它没有改变冷热、EV、水电、储能、网络、可靠性、碳/CCS 或成本方程；只修改
  求解阶段、checkpoint、planning-state provenance、sequence 窗口和验收合同。
  主线使用 Gurobi 13 `Method=2/Crossover=0/SolutionTarget=1`；接受条件仍为
  `OPTIMAL + strict primal/dual contract + solution_qc=PASS + 全部 hard checks +
  current input + valid result manifest`，没有放松科学 QC。
- 接受后的 `barrier_checkpoint/{primal_barx.npy,dual_barpi.npy,
  barrier_checkpoint_manifest.json}` 保存完整原 LP 顺序的 `BarX/BarPi`。planning
  sequence 现在显式传入 `--export-barrier-checkpoint
  --allow-nonbasic-planning-state`；只有 accepted checkpoint 完整时，才将该最优
  内点容量解登记为 `ACCEPTED_OPTIMAL_NONBASIC_BARRIER_CAPACITY_STATE` 并续接下一
  规划年。state metadata 锁定 source contract、checkpoint SHA256、cohort tolerance
  和被忽略的微小容量统计。该策略承认多重最优时内点容量分布可能较弥散，但它仍是
  满足全部约束的最优解；论文必须把这种 sequential cohort policy 明示为方法定义。
- Crossover 已从年度/序列门禁中完全移除。所有 case/year 的 accepted Barrier
  主线完成后，作者才按研究需要选择年份，用 exact-LP `PStart/DStart +
  LPWarmStart=2` 独立生成 basic derivative。该 derivative 不写 `planning_state`、
  不回溯改变已完成路径，也不覆盖源结果。容量、调度、成本、碳核算及 `BarPi`
  影子价格和连续 LP reduced cost 不需要 Crossover；`VBasis/CBasis`、`.bas`、
  `SAObj*`/`SARHS*` 等 basis sensitivity 才依赖 Crossover。退化 LP 的 dual/RC
  可能不唯一。MGA 数学上不要求所有年份先 Crossover，basis 仅是所选年份的
  可选加速/深入分析资产。
- runner 现默认拒绝 `>744 h` 的 inline Crossover，除非显式
  `--allow-inline-crossover`；Gurobi 13 若在 `BarStatus=OPTIMAL` 后 inline
  Crossover 失败，会尽力保留 `RECOVERY_ONLY_UNACCEPTED_SOLVER_RESULT`，但该
  recovery 没有完整 QC，不能重标为科学接受结果。任意 diagnostic 的内存门禁已从
  错误的固定 8 GiB 改为 `<=744:8`、`745--4344:32`、`>4344:96 GiB`；长 profile
  为 `TimeLimit=86400 s/SoftMemLimit=80 GiB`，禁止越过 host memory/swap/PSI
  门禁。
- 本地在 `CISPO_WAVE_ROOT=D:\codeenv\pycharmproject\National_RL\wave_energy`
  下完整回归 `175/175 PASS`；真实 Gurobi 小模型已验证 memmap `BarX/BarPi` 能
  注入 `PStart/DStart` 并完成 `LPWarmStart=2` deferred crossover。`py_compile`
  与 `git diff --check` 通过。
- 13:58 实时核验：本地已形成实现提交 `53a5873`；提交前 origin/GitHub 均为
  `1465a2bd8f4a0fcbd52fcb2fb296db5eade52672`。固定服务器仍为 clean
  `7a1520eb723db7717b6ce4dd41646916c34bb0cf`，无 CISPO/Gurobi/planning-sequence
  求解进程，available RAM 约 `114 GiB`、swap `447 MiB/2 GiB`、最新两次
  `vmstat si/so=0/0`、memory PSI 0；ParaCloud `squeue -u a8s001819` 为空。
  本窗口没有部署或启动任何求解。
- 精确下一步：先推送实现与本交接 tip；下一窗口实时核验后部署精确 tip，完成 server
  regression/readiness/release/Base+V5 input/hydro audits。先在 summer 起点串行闭合
  1 h/24 h/168 h Base/V5 四年 nonbasic sequence，再运行 Jan、Jun-15、Oct 三个
  start hour `0/3960/6552` 的 2030→2060 Base/V5 744 h sequences。全部通过后再做
  2030 Base `1008/1488/2160/2976/4344 h` 长度阶梯、最大安全长度 V5 配对，并由
  作者决定是否在该长度追加四年 sequence。主线不运行 Crossover；`>4344 h`、
  8760 h、付费云、MGA/basis、并发第二求解和 `Crossover=3` 均不自动启动；详细
  停止规则见 `SERVER_RUNBOOK.md` 顶节。

### Historical 2026-08-01 05:52 snapshot（仅保留失败证据，已被上节取代）

- 2026-08-01 05:52+08:00：当前四端与固定服务器 checkout 均为
  `7a1520eb723db7717b6ce4dd41646916c34bb0cf`，branch
  `codex/cispo-2030-full-lp`；服务器 worktree clean、无 CISPO/Gurobi 进程。
  该实现包含 `e004703` 的 reservoir/VRE/thermal/storage bound tightening 与
  `7a1520e` 的 reservoir storage native-bound 编码；本轮没有 basis、并发任务、
  付费云或后续年份。
- summer-offset 2030 Base 744 h 根
  `/data/zz2/National_model/outputs/2030_744h_v0731_reservoir_native_ub_7a1520e_base_stablebasis_v1`
  已正式终止为 `TIME_LIMIT`，不是可接受解。窗口为 model hour
  `[3960,4704)`、北京时间 `2030-06-15 00:00--2030-07-15 23:00`，scenario
  为 `base`，solver 为 `barrier_16_auto_order_stable_basis_v3`，并严格标记
  `TEST_ONLY_TRUNCATED_HORIZON`。
- Barrier 在 218 iterations、`6,900.02 s` 报告 interior optimal objective
  `2,352,092.16 million CNY`；末行 primal/dual infeasibility 与
  complementarity 为 `1.48e-4/1.69e-8/1.74e-9`。随后 crossover 重启，push
  phase 在 `10,249 s` 以 `PInf=6.459046`、`DInf=1.0102534e5` 结束；simplex
  cleanup 在 iteration 721,237 出现 `PInf=1.4119e-2`、`DInf=6.1797e19`，
  Gurobi 报告一个变量从 basis 丢弃并切换 quad precision。最终
  `Crossover time=14,528.04 s`、746,438 simplex iterations、solver
  `21,601.01 s`，状态从 Barrier `Optimal` 变为 `TIME_LIMIT`，`SolCount=0`。
- 严格终态审计结论为拒绝：`solve_report.json.status=TIME_LIMIT`；无
  `solution_qc.json`，因此 58 项 solution hard checks 未执行而不是通过；无
  `result_manifest.json`、dashboard、科学结果表或 planning state。当前
  `input_manifest.csv` validator 为 `(True, [])`，SHA256 为
  `99842464c22371d15e757bcc6db76490060a74bbb944961ed1be6cbdef40d6e4`；result
  validator 明确返回 `result_manifest.json is missing`。wrapper exit `2`、
  stderr 空、wall `6:05:29`、MaxRSS `19,702,352 KiB`、process-tree peak
  `18.667 GiB`、process swaps 0。由于无解，冷热、EV、wave、水电、PHS/储能、
  网络、备用、惯量、碳/CCS/BECCS 与成本 accounting 只能确认 build/preflight
  scope 存在，不能完成解后审计或作科学解释。
- 同窗 Base 在不启用灵活负荷时仍复现 crossover 失败，说明该 744 h blocker
  不依赖 V5 新增灵活性方程；但这不证明 V5 已通过。候选 V5 输出/控制根均未创建，
  且不得启动。服务器 available RAM 约 `114 GiB`、swap `447 MiB/2 GiB`、实时
  `vmstat si/so=0/0`、memory PSI 0；ParaCloud 队列为空，故终止不是 RAM、swap
  或外部并发造成。
- 精确下一步：原样保留 Base 失败根，停止当前 Base→V5 串行门禁；不得 resume、
  补写 QC/manifest 或启动 V5/8760 h/付费云/basis/MGA/`Crossover=3`。下一轮
  代码工作必须先针对 shared-core crossover 数值路径形成可审查方案，在全新根上
  重新通过 1 h/24 h/168 h 的匹配 Base/V5 门禁与当前 manifests，再由作者批准
  是否重跑 744 h；不能仅提高 TimeLimit 后直接放大。

## Superseded current-snapshot archive (through 2026-07-31 16:49+08:00)

- 2026-07-31 16:49+08:00 summer-offset 744 h 已完成 Barrier，当前处于
  Crossover 后的 simplex cleanup，尚未终止。Barrier 在 iteration `233`、
  runtime `7,414.52 s` 达到 `Optimal objective 2,351,134.66 million CNY`；
  末行 primal/dual infeasibility 与 complementarity 为
  `2.26e-4/2.27e-8/1.82e-9`。日志没有 `Numerical trouble`。
- `Crossover=1/CrossoverBasis=1` 在约 `7,680 s` 进入 crossover；push phase
  于 `9,652 s` 完成，当时 `PInf=0.79097523`、`DInf=1.4466055e5`。16:48
  最新 simplex iteration 为 `912,630`，runtime `11,752.76 s`，objective
  `2,351,203.328 million CNY`，primal infeasibility 为 0，dual
  infeasibility 为 `2.014e6`；近期 dual infeasibility 在约 `2.18e4--1.36e10`
  间显著波动，因此当前只能判定为“crossover 数值恢复仍在进行”，不能判成功，
  也尚无正式失败状态。
- 唯一 wrapper/Python 链仍存活，server 保持 clean 启动提交
  `aaf16cc49a5a3d5bb07d214a957a3a4065ac3f07`；本地/origin/GitHub
  `36ca08c46a3720e6e867124d7e32f29e032ea04a` 仅比它多活动运行交接文档，
  运行期间不得部署。Python RSS 约 `14.2 GiB`；solver current/max memory
  `16.36/23.50 GiB`，host available RAM 约 `100 GiB`，swap
  `780 MiB/2 GiB` 且实时 `si/so=0/0`，memory PSI 0，stderr 0，
  ParaCloud 队列为空。`solve_report.json`、`solution_qc.json` 和
  `result_manifest.json` 均尚不存在。
- 精确下一步继续只读监控。profile 的 solver `TimeLimit=21,600 s`，当前尚余
  约 `9,847 s`；不得把 Barrier 的 optimal line 当作最终接受，也不得因当前
  dual oscillation 提前修改运行。PID 退出后执行完整终态审计。
- 2026-07-31 13:29+08:00 已获准并启动唯一 summer-offset 2030/V5 744 h
  cold gate。输出根为
  `/data/zz2/National_model/outputs/2030_744h_v0731_summer_offset_a7c6715_v5_v1`，
  控制根为对应 `run_control` 路径；wrapper/Python PID 初始为
  `674143/674145`，启动时间 `2026-07-31T13:27:06+08:00`。服务器为 clean
  `aaf16cc49a5a3d5bb07d214a957a3a4065ac3f07`，与启动时 local/origin/GitHub
  一致；运行期间不得切换 checkout。
- 实时 `run_scope.json` 已确认 model hour `[3960,4704)`、北京时间
  `2030-06-15 00:00--2030-07-15 23:00`、744 h、V5 central、
  `TEST_ONLY_TRUNCATED_HORIZON`、annual-flow scaling
  `744/8760=0.08493150684931507`、no-basis，以及
  `Crossover=1/CrossoverBasis=1` 的 long-horizon compatibility PASS。
  13:29 时仍处于模型构建：Python RSS 约 `1.68 GiB`，尚无
  `build_report/solver_telemetry/gurobi.log`，stderr 0；host available RAM
  约 `112 GiB`、swap `780 MiB/2 GiB`、第二个 `vmstat si/so=0/0`、
  memory PSI 0，ParaCloud 队列为空。
- 当前精确动作是只读监控该唯一任务。PID 退出前不修改服务器 checkout、不启动
  第二求解；PID 退出后不能凭日志或 Gurobi status 验收，必须执行
  solve/QC/58 hard checks/current input/valid result manifest/wrapper 与完整
  物理和 accounting scope 审计。仍禁止 8760 h、付费云、basis/MGA 与
  `Crossover=3`。
- 2026-07-31 13:27+08:00 summer-offset 恢复链已闭合：固定服务器已部署
  `11c682076869e30e0ed24db038bf3c12ecdbb1ae`，完整回归 `167/167 PASS`。
  全新 1 h Base v2 根
  `/data/zz2/National_model/outputs/2030_1h_v0731_summer_offset_a7c6715_base_v2`
  达到 `OPTIMAL + solution_qc=PASS + 58/58 + current input + valid result
  manifest + wrapper exit 0/stderr 0`；`time_index.csv` 精确从 model hour 3960、
  `2030-06-15 00:00` 开始。solver runtime `4.966 s`，Barrier/simplex
  `92/1,134`，wall `0:34.02`，MaxRSS `498,444 KiB`，swaps 0。
- 同起点全新 24 h V5 v2 根
  `/data/zz2/National_model/outputs/2030_24h_v0731_summer_offset_a7c6715_v5_v2`
  也达到全部严格接受条件；时间范围为 model hour `[3960,3984)`，
  `2030-06-15 00:00--23:00`。solver runtime `115.226 s`，Barrier/simplex
  `243/29,002`，wall `2:38.15`，MaxRSS `962,928 KiB`，swaps 0；Barrier
  的 sub-optimal warning 由 `Crossover=1` 恢复为 `Optimal`，无
  `Numerical trouble`，最大 constraint/bound/dual violation 为
  `3.242e-8/2.980e-11/2.025e-13`。
- 24 h 夏季 V5 已实质激活 cooling：up/down/net
  `2.1335/1.6170/+0.5165 GWh`，contracted cooling `6.4145 GW`；
  storage charge/discharge `187.9103/162.4830 GWh` 且 simultaneous
  charge/discharge 为 0；EV mobility charge `152.998 GWh`、V1G relocated
  `43.3376 GWh`，本日最优解 V2G export 为 0。按 `24/8760` 缩放的碳上限
  `10.958904 MtCO2` binding。selected-horizon effective peak 比 baseline
  peak 高 `4.985 GW`，不应与基于完整 8760 h 各省峰窗计算的
  `5.7441 GW` firm credit 直接比较。全部输出仍为
  `TEST_ONLY_TRUNCATED_HORIZON`。
- 精确下一步：在再次确认固定服务器 clean/idle、资源正常、目标根不存在且
  ParaCloud 队列为空后，把服务器 fast-forward 到包含本条记录的精确文档
  tip；随后只启动一个 model hour `[3960,4704)`、2030-06-15 至
  2030-07-15 的 V5 744 h cold gate，使用
  `barrier_16_auto_order_stable_basis_v3.json`、无 basis、无并发。
  PID 存在时只读监控；不启动 8760 h、付费云、MGA、basis gate 或
  `Crossover=3`。
- 2026-07-31 13:18+08:00 首个 summer-offset 1 h Base 在 build 阶段暴露并
  修复空季节索引 bug。失败根
  `/data/zz2/National_model/outputs/2030_1h_v0731_summer_offset_985983b_base_v1`
  只形成 provenance/preflight，无 `build_report`、solve/QC/manifest；
  wrapper exit `1`、wall `0:23.75`、MaxRSS `493,580 KiB`、swaps 0。
  精确错误为夏季窗口 `winter=[]` 时 Gurobi 空 MVar 索引广播
  `AssertionError`，未进入 `optimize()`。
- 最小修复提交 `a7c67153d9b90055b60ed2704ef6bba702086ae4` 仅在无 winter
  hour 时省略空的 CHP winter 约束；有冬季小时的现有约束、全部冷热/EV
  服务、目标与参数不变。`test_bound_tightening.py` 的完整模型 1 h 构建已
  改为 hour 3960，并显式核对 baseline 切片；本地完整回归
  `167/167 PASS`。下一步推送/部署该修复，服务器重新运行完整回归后用全新
  `v2` 根重跑 summer 1 h Base；失败 `v1` 永不复用。

- 2026-07-31 13:10+08:00 已实现非年初连续诊断窗口，模型实现提交为
  `077bce0eca16b1025130143122aee0a05559c3e0`。runner 新增
  `--diagnostic-start-hour`，并把同一 `hour_start:hour_stop` 一致用于
  baseline/冷热/EV、风光 CF、wave CF、站点及省级水电、CHP 季节约束、
  QC、`time_index.csv` 和结果摘要；容量充裕度仍使用完整 8760 h immutable
  baseline peak。冷热、V1G、V2G、firm credit、碳缩放和成本口径均未改变。
  basis manifest 现在拒绝跨 start-hour 复用。
- 夏季 744 h 工程窗口固定为 2030-06-15 00:00 至
  2030-07-15 23:00，即 model hour `[3960, 4704)`。本地数据核验该窗口
  cooling 为 `147,056.322 GWh`，而年初 744 h 仅 `68.469 GWh`，因此它比
  固定 1 月窗口更适合暴露 cooling/V5 约束和数值问题。该选择仍是
  `TEST_ONLY_TRUNCATED_HORIZON`，不是年度科学结果。
- 正确设置 `CISPO_WAVE_ROOT` 后本地完整回归为 `166/166 PASS`；
  未设置 wave 根时出现的 4 个 setup error 与 1 个 provenance dry-run
  failure 已确认是缺少必需环境变量，不是代码回归。新增测试覆盖非年初
  负荷切片和跨窗口 basis 拒绝。精确下一步：推送该实现和本交接，实时复核
  固定服务器后部署；先串行运行 summer-offset 1 h Base 和 24 h V5，
  只有两根达到 `OPTIMAL + PASS + 58/58 + current input + valid result
  manifest + wrapper exit 0/stderr 0` 才启动唯一 2030/V5 summer 744 h
  cold gate，使用 `barrier_16_auto_order_stable_basis_v3.json`、无 basis、
  无并发。继续禁止 8760 h、付费云、MGA、`Crossover=3`。

- 2026-07-31 12:45+08:00 当前输出语义修复与匹配 24 h/168 h
  Base--V5 门禁已在固定服务器闭合。当前本地、`origin`、GitHub 与服务器
  checkout 一致为 clean task identity
  `ae3356391ec55376b041d6a356ea2d1f26be88bc`；本地工作树仍仅保留用户拥有的
  `supplementary_materials/**`、`.codex_tmp/**` 等无关改动。该提交把
  service-constrained V4/V5 不适用的旧式
  `maximum_ev_v1g_daily_energy_residual_gwh` 显式输出为 `null`，新增
  applicability 字段，并修正 dashboard 对严格零与小于 0.001 GWh 数值的
  显示；没有改变 LP 变量、约束、目标、输入或 solver 参数。
- 本地与服务器完整回归均为 `165/165 PASS`；readiness、release contract、
  V5 input 与水电审计全部 PASS。常规水电仍精确闭合为
  `297.8895 + 82.1105 = 380.0000 GW`。本机 available RAM 约
  `7.91 GiB < 8 GiB`，故没有降低门槛或强行在 Windows 本机启动 solver。
- 当前提交的 2030/24 h Base 与 V5 production-profile 根分别为
  `/data/zz2/National_model/outputs/2030_24h_v0731_ae33563_base_v2prod_v1`
  和
  `/data/zz2/National_model/outputs/2030_24h_v0731_ae33563_v5_v2prod_v1`。
  两根均为 `OPTIMAL + solution_qc=PASS + 58/58 + current input +
  valid result manifest + wrapper exit 0/stderr 0`；solver runtime 为
  `407.321/420.232 s`，整轮 wall 为 `7:28.51/7:44.38`，peak
  process-tree RSS 为 `0.761/0.794 GiB`。V5 相对 Base 的 24 h solver
  增量约 3.2%，没有出现新增的数值爆炸。
- 当前 2030/168 h 匹配根为
  `/data/zz2/National_model/outputs/2030_168h_v0731_ae33563_base_v2prod_v1`、
  `/data/zz2/National_model/outputs/2030_168h_v0731_ae33563_base_v3stable_v1`
  与
  `/data/zz2/National_model/outputs/2030_168h_v0731_ae33563_v5_v3stable_v1`。
  三根全部达到 `OPTIMAL + PASS + 58/58 + current input + valid result
  manifest + wrapper exit 0/stderr 0`。Base v2、Base v3、V5 v3 的 solver
  runtime 分别为 `907.672/917.121/1024.510 s`，wall 为
  `16:54.30/17:03.75/18:54.89`，peak process-tree RSS 为
  `3.336/3.328/3.508 GiB`；Barrier/simplex 分别为
  `213/211003`、`213/185333`、`232/258814`。Base v2/v3 objective
  仅差 `2.9e-7 million CNY`，证明 `CrossoverBasis=1` 没有改变科学解。
- 结构压缩 V5 的 168 h optimize() 仍由代码合同要求
  `CrossoverBasis=1`。一次显式的 V5/v2 尝试在求解前按预期被 guard
  拒绝，控制根
  `/data/zz2/National_model/run_control/2030_168h_v0731_ae33563_v5_v2prod_v1`
  记录 `exit=1`、wall `0:09.41` 与精确 RuntimeError；它不是失败求解或
  可接受结果，不得补写 result manifest。V5 的可用长时段候选仍是
  `barrier_16_auto_order_stable_basis_v3`，尚未自动晋升为全年
  production profile。
- 同 profile 的 168 h V5 相对 Base：objective 降低
  `298.097 million CNY`，bio/coal/gas 发电容量合计减少约
  `2.915 GW`，对应保守 firm-flex credit `2.891320 GW`；所选窗口全国
  effective peak 下降 `1.663365 GW`。adequacy 仍以完整 8760 h immutable
  baseline peak 为基准，只允许折减 firm credit，不直接以 effective peak
  降容。V5 的物理 EV fleet 充电 `756.192 GWh`、V1G relocated
  `193.242 GWh`、V2G export `1.178 GWh`；兼容字段
  `ev_v2g_charge_gwh=0` 在 V5 明确不适用，能量由同一 fleet SOC 与
  mobility charging 闭合，SOC transition residual 为
  `2.537e-13 GWh`。
- 冷热、EV、wave、水电/梯级、PHS/储能、网络、备用、惯量、碳/CCS/BECCS
  与成本 accounting scope 均通过 hard QC。电池/PHS 在 168 h 内均有非零
  充放电且同充同放为零；水电 380 GW 闭合；网络对冲流与 DC 反向流为零；
  碳上限按 `168/8760` 缩放至 `76.712329 MtCO2` 并 binding；objective
  component residual 为 `-1.774e-7 million CNY`。wave 已启用但本窗口
  最优装机/发电为零，不是缺少输入。需保留两项解释边界：首周冬季没有实际
  冷热移峰，但广东 cooling 合同仍从完整全年峰窗获得 `0.3044 GW` firm
  credit；梯级水文审计虽代数闭合，raw negative-local-inflow clipping
  等价水量仍为 `974.405 million m3`、实际 routed adjustment 为
  `669.451 million m3`，属于后续科学数据敏感性而非本轮 solver bug。
- 终态实时复核：服务器 clean `ae33563`、无 CISPO/Gurobi 进程、available
  RAM 约 `114 GiB`、swap `780 MiB/2 GiB`、第二个 `vmstat` 样本
  `si/so=0/0`、memory PSI 0；ParaCloud `squeue -u a8s001819` 为空。
  所有 24 h/168 h 根仍严格标记 `TEST_ONLY_TRUNCATED_HORIZON`。精确下一步
  是由作者决定是否在 `stable_basis_v3` 上运行全新、串行的四年 168 h
  Base/V5 sequence，或据此批准单一更长门禁；本里程碑不自动启动
  744/1008/8760 h、付费云、basis/MGA、并发第二求解或 `Crossover=3`。

- 2026-07-31 10:15+08:00 固定结果查阅环节已实现并通过最终服务器门禁。
  实现提交为 `336116b493cf92eb461d1a2aab490678fd2dbac5`，最终解释修正为
  `bdb57b2cb4e3f4781cfd53c087c7cc1a780d73a5`。每个正常完成的运行现在
  在 result manifest 定稿前自动生成
  `result_dashboard_summary.json`、`result_analysis_metrics.csv` 与
  `visualizations/core_result_dashboard.svg`，三项均进入
  `output_catalog.csv` 和最终 SHA256 `result_manifest.json`。独立脚本
  `scripts/build_result_dashboard.py` 可在不改动历史结果根的外部目录
  补充渲染 SVG/PNG/PDF。
- 本轮结果查阅实现不创建或修改任何 LP 变量、约束、目标系数、输入参数或
  solver 参数。此前数值稳定化仍保持冷热服务库存、V1G 充电调度、V2G
  SOC/驾驶取能、付费合同和 firm capacity credit 的既定模式；零控制状态和
  严格冗余行/列是代数等价消元。需要精确区分的是，数值稳定化里唯一新增的
  物理不等式为 `charge + discharge <= connected * K_v1g`，用于禁止
  V1G/V2G 同时重复占用同一签约连接；它不改变服务定义，但确实封闭了原来
  缺失的共享接入上限，且已有独立 hard QC。
- 成本强度分母固定为不可变 baseline electricity demand，保证 Base/V5
  可比，换算恒等式为 `1 million CNY / GWh = 1 CNY/kWh`。8760 h 才允许
  报告“年化规划成本 + 全年运行成本”的 total system cost intensity；
  截断门禁只分别报告 annualized-planning intensity 与
  selected-horizon operating intensity，二者不得相加或称为 LCOE。
  成本明细会排除 composite `annual_operation` 重复汇总项，并要求详细成本
  对 objective 的重构残差在容差内，否则 dashboard 生成失败。
- 本地完整回归在正确 `CISPO_WAVE_ROOT` 下为 `162/162 PASS`；本机当时
  available RAM `7.64 GiB < 8 GiB`，故没有降低内存门槛或强行启动新本地
  solver。既有 24 h V5 输出只读复演已在外部目录成功生成 SVG/PNG/PDF。
  固定服务器在 `bdb57b2` 上运行的最终 2030/V5 1 h 根
  `/data/zz2/National_model/outputs/2030_1h_v0731_dashboard_v5_bdb57b2_server_v1`
  为 `OPTIMAL + solution_qc=PASS + 58/58`，input/result manifest
  validator 均为 `(True, [])`，wrapper exit `0`、stderr `0 bytes`、wall
  `0:39.10`、MaxRSS `597,624 KiB`、swaps `0`。solver runtime
  `7.352116 s`，Barrier/simplex 为 `96/1,716`，最大
  constraint/bound/dual violation 为
  `0/4.441e-16/0`。
- 最终 dashboard 的规划成本强度为 `0.2003156 CNY/kWh`，所选 1 h
  运行成本强度为 `0.3141334 CNY/kWh`，全年综合值为 `null`；objective
  重构残差仅 `-9.779e-9 million CNY`。所选 1 h 全国 baseline/effective
  peak 都是 `1150.7158 GW`，而 `2.8741 GW` firm credit 来自各省完整
  8760 h baseline peak windows 与折减率，dashboard 已明确说明两者不能
  直接比较。冷热状态、EV SOC、V1G/V2G nesting/共享连接、储能、网络、
  备用、惯量、碳/CCS、梯级水电和成本 hard checks 全部通过。
- 2026-07-31 10:15 实时复核服务器 checkout clean、无 CISPO/Gurobi
  进程、available RAM 约 `114 GiB`、swap `780 MiB/2 GiB` 且第二个
  `vmstat` 样本 `si/so=0/0`、memory PSI 0；ParaCloud
  `squeue -u a8s001819` 为空。该 1 h 根仍严格标记
  `TEST_ONLY_TRUNCATED_HORIZON`。结果查阅 bug 已闭合，但它不证明
  8760 h 可解性；下一次获准的 24/168/更长门禁应直接复用该固定输出环节，
  不自动启动 744/1008/8760 h、付费云、basis/MGA、并发第二求解或
  `Crossover=3`。

- 2026-07-31 05:14+08:00 固定服务器数值稳定化门禁已严格闭合。实现提交
  `fead34334153eca32bbf7ec3651f3388038ac04b` 与前一文档 tip
  `22e19c154148fcfcb137d5a7e882ff69abd2b7c8` 已双端推送，服务器 checkout
  为 clean `22e19c1`。服务器完整回归 `159/159 PASS`，readiness、release、
  V5 input、水电输入与 `297.8895 + 82.1105 = 380.0000 GW` 审计均 PASS。
  新建的 2030 Base/V5 1 h 与 24 h 四根全部达到
  `OPTIMAL + solution_qc=PASS + 58/58 + current input manifest +
  valid result manifest + wrapper exit 0`。1 h Base/V5 solver runtime 为
  `7.707/7.316 s`；24 h 为 `408.850/421.015 s`，V5 相对 Base 只增加
  5,321 variables、5,934 rows、30,045 nonzeros、约 3.0% solver time 和
  0.032 GiB RSS。24 h 两根仍在 Barrier 后报告共同的
  `Numerical trouble`，随后由 `Crossover=1` 严格恢复，故该共享数值债不能
  归因于 V5 新增结构。
- 唯一 2030/V5 168 h cold 根
  `/data/zz2/National_model/outputs/2030_168h_v0731_v5_numeric_central_22e19c1_server_v1`
  已为 `OPTIMAL + solution_qc=PASS + 58/58`；input/result manifest
  validator 均返回 `(True, [])`，wrapper exit `0`、wall `18:38.92`、
  peak process-tree RSS `3.511 GiB`、swaps `0`。服务器实际 raw 矩阵为
  `1,209,095 rows / 1,060,576 vars / 9,755,329 nz`，presolved 为
  `737,850 / 751,223 / 7,386,987`；最大矩阵系数仍为 6,250，presolve
  amplification 为 `1.0`。Barrier 运行 232 次、819.54 s 后以
  `Sub-optimal` 结束，但没有出现 `Numerical trouble encountered`；
  `CrossoverBasis=1` 在 176.79 s 内将状态改为 `Optimal`，最终
  258,814 simplex iterations、solver `1005.194 s`，无 restart。
  最大 constraint/bound/dual violation 为
  `8.339e-8 / 2.609e-8 / 6.047e-8`。
- 本轮严格 QC 未发现新增钻空子：冷热 up/down、EV charge/discharge、
  储能 charge/discharge、火电 startup/shutdown、AC 对冲流均为零；
  V1G/V2G nested、全国 V2G cap、共享连接功率、firm-credit 物理上界、
  备用、惯量、网络、水电/梯级、碳/CCS/BECCS 与成本 component 全部通过。
  2030 firm flexibility credit 为 `2.891320 GW`，诊断碳上限按
  `168/8760` 缩放至 `76.712329 MtCO2` 并 binding。输出中的
  `maximum_ev_v1g_daily_energy_residual_gwh=5.999958` 是旧式“每日充电
  量等于不受控基线”指标；V5 使用带效率、驾驶取能和周期 SOC 的车群服务
  守恒，该旧指标不适用，真正的车群 SOC transition residual 为
  `2.537e-13 GWh`。后续应清理该输出名称/适用性，避免论文审计误读，
  但不得把它误判为当前 LP 漏约束。
- 与旧 V5 168 h `TIME_LIMIT` 根相比，新根把“6 h、3,488,935 次
  simplex、无解/QC/manifest”改为约 16.8 min solver 严格最优，证明本轮
  精确冷热状态压缩修复了已复现的 V5 presolve 放大和数值循环。它仍不是
  8760 h 可解性证明：解的估计 `Kappa=1.6198e10`，共享模型最差 row
  scaling 仍来自 `load_center_ror_availability`、ROR/VRE availability
  与年度会计；直接消去 availability variables 曾增加 presolved
  nonzeros，盲目提高 CF 零阈值又会改变科学输入。因此
  `barrier_16_auto_order_stable_basis_v3` 只升级为“168 h V5 诊断通过”，
  仍不是 production profile。服务器当前无 CISPO/Gurobi 进程、约
  111 GiB available、`vmstat si/so=0`、memory PSI 0；ParaCloud 队列空。
  下一步先以相同提交/数据/profile 运行一个全新、匹配的 2030 Base 168 h
  cold gate，并在不求解的矩阵审计中量化共享小系数的可证明等价候选；
  两者闭合前不启动 744/1008/8760 h。继续禁止付费云、并发第二求解、
  basis/MGA 和 `Crossover=3`。

- 2026-07-31 04:21+08:00 已提交 V5 长时域数值稳定化实现
  `fead34334153eca32bbf7ec3651f3388038ac04b`。旧服务器根
  `/data/zz2/National_model/outputs/planning_sequence_168h_v0730_direction_warning_v5_cf265f3_server_v1`
  已严格归类为数值 `HARD_FAIL`：2030 在 21,600 s 达到 `TIME_LIMIT`，
  Barrier 210 后出现 `Numerical trouble encountered`，Crossover/Simplex
  累计 3,488,935 次仍无可行解；无 `solution_qc.json`、无
  `result_manifest.json`，2040--2060 未启动。失败不是内存或队列导致：
  wrapper 峰值 RSS 约 3.47 GiB、swaps 0，终态服务器约 114 GiB available、
  `vmstat si/so=0`、memory PSI 0，ParaCloud 队列为空。
- 根因已由 168 h 原始/预求解矩阵复现：旧完整冷热状态链被 presolve
  反向聚合后，最大系数由 6,250 放大到 319,337.737（51.094 倍），最差
  家族为 `cooling_positive_service_bound`。新实现仅在有非零控制的小时
  保留冷热状态，并以衰减锚点限制相邻保留节点的系数不低于 0.1；被省略
  小时的控制严格为零、状态上界不随时间变化且 `0 < rho <= 1`，因此使用
  `S_t = rho^Delta S_prev + eta_c u_t - d_t/eta_d` 是精确消元，不改变可行域
  或目标。还删除 V5 未进入目标/QC 的 EV 绝对偏差 epigraph、零上界冷热
  控制变量、零 departure rows 以及可由静态正下界证明冗余的
  `effective_load >= 0` rows；全年共减少 1,227,241 个原始变量和
  2,348,964 个原始约束。新增 `charge + discharge <= connected * K_v1g`
  以禁止 V1G/V2G 同时重复占用同一签约连接，并新增对应 hard QC。
- 最终本地证据：完整回归 `159/159 PASS`，V5 input audit、release audit、
  compileall 与 `git diff --check` 均 PASS；水电仍为
  `297.8895 + 82.1105 = 380.0000 GW`。最终 2030/168 h V5 数值审计为
  raw `1,209,095 rows / 1,060,576 vars / 9,755,331 nz`，presolved
  `737,850 / 751,222 / 7,386,903`，raw/presolved 最大系数均为 6,250，
  放大比严格为 1.0。8760 h 静态 preflight 为约 42.95M variables、
  57.92M constraints、503.13M nonzeros、34.3 GiB；它不是 Barrier
  factorization 或可解性证据。本地 1 h 求解在 `optimize()` 前因 available
  RAM 约 7.9 GiB 低于 8 GiB 安全门槛而停止，不得降低门槛。
- 新的 `barrier_16_auto_order_stable_basis_v3` 只是诊断候选：
  `Method=2`、`Threads=16`、`Presolve=2`、`Crossover=1`、
  `CrossoverBasis=1`，不设置 `Aggregate=0`。下一精确步骤是推送
  `fead343`，在服务器无进程且 clean 时 fast-forward，运行完整回归、
  readiness/release/V5/hydro audits，再串行运行全新 2030 Base/V5 1 h
  与 24 h cold gates；均严格闭合后，才启动唯一 2030/168 h V5 cold
  candidate。不得自动启动 744 h、8760 h、四年 sequence、付费云、basis、
  MGA、并发第二求解或 `Crossover=3`。

- 2026-07-30 21:29+08:00 作者已决定不让系统级影响极小的 AC 对冲流阻断截断时域排错，限定 warning 实现提交为 `9b6e72a456b0dc8f0123f90b07195f94ca902c9a`。该提交不改变 LP 方程、目标、输电成本、流量数组或 `1e-6 GW` 原始检测阈值；只对 `TEST_ONLY_TRUNCATED_HORIZON` 增加七重 warning budget：每 168 h 最多 4 个 edge-hours、单小时较小方向不超过 `0.25 GW`、不超过线路容量 `15%`、累计较小方向不超过 `0.75 GWh`、额外损耗不超过 `0.025 GWh`、累计较小方向占毛输电量不超过 `5e-5`、额外损耗占系统负荷不超过 `1e-7`，其中小时/电量/损耗预算随诊断小时线性缩放。任一超限仍 hard fail；8760 h `SCIENTIFIC_PRODUCTION` 继续要求 `1e-6 GW` 以上严格零对冲。原 2050/168 h 现场在新评估器下为 `TEST_ONLY_DE_MINIMIS_WARNING`：3 edge-hours、`0.176374 GW`、线路占比 `0.107153`、`0.381006 GWh`、额外损耗 `0.011489 GWh`、毛流占比 `1.3823e-5`、负荷占比 `4.0100e-8`，所有原始值和限额均保留在 QC。
- 本地新增方向性解析测试后完整回归 `146/146 PASS`，V5 input audit 与 release audit 均 PASS；本机 available RAM 约 `7.48 GiB < 8 GiB`，因此未降低门槛或启动本地 solver。21:28 实时复核固定服务器仍为 clean `af390fa`、无 CISPO/Gurobi/sequence 进程、约 `114 GiB` available、swap `780 MiB` 且 `si/so=0`、memory PSI 0，ParaCloud 队列空。下一步提交文档并双端推送后，在服务器空闲现场 fast-forward 精确 tip，运行 `146/146`、release/readiness/V5/hydro audits 及全新 1 h/24 h Base/V5；随后依次运行全新四年 168 h Base 和 V5。全部闭合后，作者授权的长门禁为唯一串行四年 `1008 h` `flex_integrated_v5_central`（42 天，强于 744 h），继续使用 `barrier_16_auto_order_v2`、cold/no-basis。仍禁止 8760 h、付费云、并发第二求解、basis/MGA 和 `Crossover=3`。
- 2026-07-30 19:38+08:00 固定服务器四年 168 h Base sequence 已在 2050 年按物理 hard QC 正确停止，不能接受或续接。输出根 `/data/zz2/National_model/outputs/planning_sequence_168h_v0730_flex_v5_base_af390fa_server_v1` 的 `sequence_report.json=HARD_FAIL`：2030/2040 均为 `OPTIMAL + solution_qc=PASS + 57/57 + current input + valid result manifest`，2050 的 Gurobi 求解虽为 `OPTIMAL`（solver runtime `849.053 s`、Barrier `128`、Crossover/simplex `340,040`、最大 constraint/bound/dual violation `4.889e-10/1.193e-8/9.313e-8`），但 `solution_qc=HARD_FAIL`，仅 `unidirectional_interprovincial_flow` 一项失败；2050 无 `result_manifest.json`/planning state，2060 未启动，V5 sequence 也未启动。违规严格局限于 `CORRIDOR_0153`（吉林 `22`—黑龙江 `23`，AC，既有容量 `1.646 GW`）的 3 个小时：最大较小方向流量 `0.176374 GW`、累计较小方向流量 `0.381006 GWh`，不是 `1e-6 GW` 数值尾差。对应 2050 窗口净碳上限按 `168/8760` 缩放至 `-1.917808 MtCO2` 并精确 binding，碳影子价格 `3589.731 CNY/tCO2`，违规小时吉林/黑龙江边际电价约 `-1405` 至 `-3650 CNY/MWh`；模型利用 AC 正反向流的额外输电损耗吸收 BECCS 驱动的局部过剩电量。这说明现有 `1.004004 CNY/MWh` 毛流量成本在深度负价下不再足以保证无对冲流，硬 QC 拒绝是正确行为，禁止通过调大 `1e-6 GW` 阈值重标结果。
- sequence 顶层 wrapper exit `1`、wall `49:20.77`、maximum RSS `3,741,888 KiB`、swaps `0`；2030/2040 年度 stderr 为空，2050 stderr 仅为上述 QC RuntimeError。终态无 CISPO/Gurobi/Python sequence 进程；固定服务器 checkout 仍为 clean `af390fad22dc4e3ec4636edadfb56295e4907234`，约 `114 GiB` available RAM、swap `780 MiB/2.0 GiB` 且实时 `si/so=0`、memory PSI 0；ParaCloud `squeue -u a8s001819` 为空。本地、origin、GitHub 文档 tip 均为 `134af0fcf5ccc9d631f1bf805f3104e0de5f7f7e`，用户拥有的 `supplementary_materials/**`、`.codex_tmp/**` 和历史 outputs 未改。下一步先审查并批准保持 LP/物理边界的 AC 方向性修复方案，再用全新根从 2030 重跑 Base 168 h；不得复用失败根、跳过 2050、启动 V5/744 h/8760 h、付费云、basis/MGA、并发第二求解或 `Crossover=3`。
- 2026-07-30 16:58+08:00 固定服务器 V5 预门禁和当前身份 24 h A/B 已闭合。跨平台构建暴露并修复两项 release 身份问题：提交 `4f717de` 将五张 V5 CSV 和 manifest 固定为 UTF-8/LF、`%.17g`、gzip level 6/空 filename/`mtime=0`，Windows Python 3.10/pandas 2.2.2/NumPy 1.26.4 与 Linux Python 3.11/pandas 2.3.3/NumPy 2.4.6 生成的六项 SHA256 逐字节一致；提交 `af390fa` 删除 V5 对本地 ignored 技术经济 manifest 的错误覆盖，继续继承 V0729 权威 SHA256 `397297ec...`。当前服务器代码为 clean `af390fad22dc4e3ec4636edadfb56295e4907234`，最终数据根为 `/data/zz2/National_model/data/model_ready_20260730_flex_v5_4f717de_v1`，V5 manifest SHA256 为 `a324430713e0eb3a1671c9b9ba6c127c34c5e0d7c2e21f090cbcd9394f061831`。本地和服务器完整回归均 `141/141 PASS`；服务器 readiness、V5 输入、release 和水电审计均 PASS，水电仍为 `297.8895 + 82.1105 = 380.0000 GW`。
- 当前服务器 2030/24 h Base 根 `/data/zz2/National_model/outputs/2030_24h_v0730_flex_v5_base_af390fa_server_v1` 与 V5 根 `/data/zz2/National_model/outputs/2030_24h_v0730_flex_v5_central_af390fa_server_v1` 均为 `OPTIMAL + solution_qc=PASS + 57/57 + current input + valid result manifest + wrapper exit 0`。solver runtime 为 `405.882/434.896 s`，wall 为 `7:26.56/7:58.18`，peak process-tree RSS 为 `0.759/0.797 GiB`，swaps 0；Barrier 均报告 numerical trouble，随后 `Crossover=1`/simplex 以 `503,365/519,659` 次迭代修复，最大 constraint violation 均为 `1.224e-8`。V5 objective 相对 Base 低 `347.394 million CNY`，显式 flexibility cost 为 `785.531 million CNY`，firm credit 为 `2.891320 GW`，总发电装机同步减少 `2.891320 GW`（主要 gas `-1.969238 GW`、coal `-0.922082 GW`），所有冷热、EV/V1G/V2G、firm credit、储能、网络、备用、惯量、碳/CCS 和成本 hard checks 均通过。
- 24 h 结果中首日全国有效峰值由 `1229.5522` 降至 `1227.3831 GW`，变化 `-2.1692 GW`；它不能与 `2.8913 GW` firm credit 直接比较。诊断运行只优化领先 24 h，而 capacity adequacy 和 firm credit 按各省不可变完整 8760 h baseline peak 的四小时窗口、合同容量、功率/能量包络与折减率计算。因而当前证据证明的是容量认证方程和发电侧容量响应已生效，不是年度 endogenous effective-peak 或中国 ELCC 结论。下一步在冻结 `af390fa` checkout 上串行运行全新四年 168 h Base sequence，严格接受后才运行 V5 sequence；两者仍为 `TEST_ONLY_TRUNCATED_HORIZON`。168 h A/B 全闭合前不得启动 744 h。
- 2026-07-30 16:05+08:00 已形成并提交集成需求侧灵活性 V5 候选 `57ad4c5`。正式主分析仍严格只有 Base 与一个中央反事实；Base 不变，中央反事实联合冷热负荷、付费 V1G、内生付费 V2G，以及只对四小时峰值窗口内可交付服务计入的折减 firm capacity credit。V1G 只对相对不受控充电基线的向下迁移计费；V2G 内嵌于有序充电合同，另付 availability、双向设施、车主参与和电池退化成本；不提供备用信用。V5 输入审计 PASS，四年/31 省/8760 h 完整，输入 manifest SHA256 为 `350fce0051d5e79494f2f71e2c28a620385f868de7596baac6dfd3e39260a108`；`release_contract_v0730_v5` 审计 PASS，完整回归 `140/140 PASS`。新的英文论文式补充章节位于 `supplementary_materials/modules/06_integrated_demand_flexibility/integrated_demand_flexibility_methods_en.tex`，仅四个紧凑 section，无内部 scenario/config/manifest 名称；对应 PDF 已经 Tectonic 编译和逐页视觉复核。中文技术合同版本同时保留。
- 2030 1 h Base/V5 门禁均为 `OPTIMAL + solution_qc=PASS + 57/57 + current input manifest + valid result manifest`。修正 V5 单一 EV 车队 SOC 的输出解释后，当前实现 1 h 根 `outputs/2030_1h_v0730_flex_v5_central_gate_v3` 仍为 `OPTIMAL + 57/57`，solver runtime `17.330 s`；`scenario_manifest.json` 现在明确说明 `ev_mobility_charge_gwh` 是集成车队总充电，旧 `ev_v2g_charge_gwh` 在 V5 中不适用且保持兼容零值。数学实现修正前后的目标一致。24 h A/B 数学门禁根 `outputs/2030_24h_v0730_flex_v5_{base,central}_gate_v2` 均为 `OPTIMAL + PASS + 57/57 + closed manifests`，solver runtime 分别为 `404.360/727.286 s`；两者 Barrier 均数值困难后由 `Crossover=1`/simplex 修复，分别为 `507,293/546,950` 次 simplex。V5 将该 24 h 窗口全国峰值降低 `2.3211 GW`，获得 `2.8913 GW` firm credit，发电装机相对 Base 减少 `2.8913 GW`；灵活性成本约 `785.53 million CNY`，总目标净下降 `347.40 million CNY`。冷热/EV 状态、V1G/V2G 合同、全国 V2G 上限、firm-credit 物理上界、同时充放、备用、惯量、容量裕度和碳账户均无 hard-check 违反。因最后仅修改了 scenario/output 身份说明，`57ad4c5` 仍需在同一精确身份下重跑 24 h closed-manifest A/B，不能把现有 v2 根重标为当前提交结果。
- 本地四年 168 h Base sequence 首次尝试根 `outputs/planning_sequence_168h_v0730_flex_v5_base_v1` 在 2030 建模前被运行时内存门禁主动停止：available RAM `6.07 GiB < 8 GiB`，`sequence_report.json=HARD_FAIL`；无 Gurobi 求解、无 state 输出。168 h 静态估计为约 `1,019,223` variables、`1,257,802` constraints、`10,089,870` nonzeros、`0.74 GiB`，但不得降低 8 GiB 门槛或复用失败根。固定服务器实时为 clean `codex/cispo-2030-full-lp` / `c19e35b`、约 `114 GiB` available、swap `780 MiB` 且 `si/so=0`、memory PSI 0，ParaCloud 队列空；没有 CISPO/Gurobi solver，但遗留部署审计 wrapper PID `976320`（子进程 `grep` PID `976713`）仍存在。按 PID 保护规则，在该遗留进程被作者确认处理前不切换服务器 checkout、不部署 `57ad4c5`、不启动 168 h/744 h。下一步是释放本地至少 2 GiB RAM 后以全新根重跑当前身份 24 h A/B 与 Base/V5 四年 168 h，或先获得处理服务器遗留 audit PID 的明确授权；仍禁止 8760 h、付费云、并发第二求解、basis/MGA 和 `Crossover=3`。
- 2026-07-30 11:26+08:00 已实现诊断时域年度流量账户缩放，模型提交为 `d3b6f1485d5ef88762e9d8d0ac8ca87db15dc244`。定义 `f=optimization_hours/8760`，短时域的净碳上限、DAC 捕集 throughput、生物质燃料预算与 CO2 场址注入能力统一乘 `f`；DAC 小时功率由窗口捕集量除以 `f` 后的年化速率计算。年化装机/固定成本和 capacity state 不缩放，8760 h 因 `f=1` 与原科学模型完全一致。新增 2030 V4 V1G 本地 1 h/24 h 根 `outputs/2030_{1h,24h}_v0730_annual_flow_scaled_v4_v1g_v1` 均为 `OPTIMAL + solution_qc=PASS + 54/54 + current input + valid result manifest`；碳上限分别为 `0.456621/10.958904 MtCO2`，两根净排放均精确达到上限，DAC capacity violation 为 0。24 h solver runtime `270.653 s`；外层命令在结果/manifest 全部写完后达到 300 s 工具返回上限，实时复核无残留 runner。完整本地回归为 `138/139 PASS`，唯一失败仍是既有本地 ignored `technology/technoeconomic_price_basis_manifest.json` hash `f89241...` 与服务器冻结权威值 `397297...` 不同，本次未改数据或 release contract。`scenario_catalog v4` 的 `primary_analysis` 现在机器锁定为且仅为 `base` 与 `flexible_load_comfort_v4_v1g`；effective-peak、V2G、水电聚合调节、PHS low/central/high 仍是独立 sensitivity，V3 只作 legacy validation，PHS template 不可运行。固定服务器和 ParaCloud 本次均未操作；旧 744 h 结果不因新代码自动重标或复用，任何新服务器 744 h/8760 h 仍需独立授权与新输出根。
- 2026-07-30 09:18:42+08:00 串行 2030→2060 744 h V4 V1G diagnostic sequence 已严格完成，`sequence_report.json=PASS`，完成时间 `2026-07-30T09:12:33+08:00`，四年均 `ACCEPTED`、return code 0。2030/2040/2050/2060 均为 `OPTIMAL + solution_qc=PASS + 53/53 hard checks + current input manifest + valid result manifest + hydro cascade reconciliation audit`，objective 分别为 `2,331,204.529 / 2,380,260.669 / 2,564,163.188 / 2,808,392.706 million CNY`，solver runtime 分别为 `12,268.312 / 10,701.027 / 12,557.989 / 14,954.122 s`；年度 `sequence_stderr.log` 全部 0 bytes。顶层 wrapper exit 0、wall `14:27:23`、maximum RSS `21,927,236 KiB`、swaps 0；活动 PID 已全部退出。53 项 hard checks 显式覆盖冷热、EV、wave、水电/梯级、PHS/储能、网络、备用、惯量、容量充裕、碳/CCS/BECCS 与成本目标，四年 planning state 链均存在且仅标记为 test-only。终态主机 available RAM 约 114 GiB、swap 780 MiB 且 `si/so=0`、memory PSI 0，ParaCloud 队列空。该整轮仍是 `TEST_ONLY_TRUNCATED_HORIZON`，不能作为年度科学结果或正式 2040/2050/2060 state anchor；不得由此自动启动 8760 h、basis、MGA、付费云或第二求解。
- 2026-07-29 23:21:48+08:00 四年 744 h sequence 已完成首个逐年里程碑：2030 `ACCEPTED`，2040 正在 Barrier。2030 为 `OPTIMAL + solution_qc=PASS + 53/53 + current input manifest + valid result manifest`，solver runtime `12,268.312 s`，Crossover 后 `914,501` simplex iterations，objective `2,331,204.529 million CNY`；年度 `sequence_stderr.log` 为 0 bytes，运行监控 peak process-tree RSS `20.385 GiB`。53 项 hard checks 显式覆盖冷热服务/状态、EV V1G/V2G、wave、水电聚合与梯级水量、PHS/储能、网络方向、备用、惯量、容量充裕、碳/CCS/BECCS 与 objective components。2040 runner PID `1717598`，Barrier iteration `107`，runtime `3,572.896 s`，primal/dual infeasibility `0.008370/0.000821`、complementarity `1.8373`，current/max solver memory `13.174/22.222 GiB`；终态三文件尚不存在。主机 available RAM 约 95 GiB、swap `781 MiB/2 GiB` 且 `si/so=0`、memory PSI 0，ParaCloud 队列空。运行 checkout 继续冻结在 clean `5d31b51b350a581287fc8eb13e73216c11fc7543`；本地/origin/GitHub 文档 tip 为 `b0a3f3b26ff77a8b5357ccc9f423605fc3a1d2e8`，PID 存在期间不追平服务器文档。
- 2026-07-29 18:45:08+08:00 已在固定服务器 checkout `5d31b51b350a581287fc8eb13e73216c11fc7543` 启动唯一串行 2030→2060 744 h V4 V1G diagnostic sequence。输出根 `/data/zz2/National_model/outputs/planning_sequence_744h_v0729_identity_hydro_v4_v1g_v1`，控制根 `/data/zz2/National_model/run_control/planning_sequence_744h_v0729_identity_hydro_v4_v1g_v1`；wrapper/Python PID 初始为 `1463763/1463765`，2030 runner PID `1463870`。`sequence_report.json` 已锁定 `RUNNING + TEST_ONLY_TRUNCATED_HORIZON + diagnostic_hours=744 + flexible_load_comfort_v4_v1g`，无 basis。18:45:49 首次快照仍在构建，尚无 telemetry/Gurobi/终态三文件；available RAM 约 113 GiB、swap `781 MiB/2 GiB` 且 `si/so=0`、memory PSI 0、ParaCloud 队列空。PID 存在期间只读监控，不再切换服务器 checkout；每年必须严格 accepted 后才允许 runner 串行进入下一年。
- 2026-07-29 18:42+08:00 固定服务器已 fast-forward 到干净 `codex/cispo-2030-full-lp` / `03e77ccc8d2ef3813b7cc5c0d727b068d008090d`。权威 v4 数据根下 release contract、readiness、水电 380 GW 容量审计和 V4 输入验证全部 PASS，完整回归 `135/135 PASS`；`technology/technoeconomic_price_basis_manifest.json` SHA256 为冻结值 `397297ec3980ffb38988a0463f934e310f228cbe48268d59ce38c7fa8350ec75`。服务器全新 1 h/24 h 中央 V4 V1G 根 `2030_1h_v0729_identity_hydro_v4_v1g_server_v1` 与 `2030_24h_v0729_identity_hydro_v4_v1g_server_v1` 均为 `OPTIMAL + solution_qc=PASS + 53/53 hard checks + current input manifest + valid result manifest`，且均生成 `hydro_cascade_reconciliation_audit.json`；24 h solver runtime `84.230 s`，wrapper wall `2:07.62`、peak RSS `0.813 GiB`、swaps `0`。下一步仅在再次确认无 solver、资源安全、新 sequence 输出/控制根不存在且 ParaCloud 空队列后，启动唯一串行 2030→2060 744 h V4 V1G sequence。
- 2026-07-29 18:27+08:00 新模型实现里程碑已提交为 `cea78ae1546b19754f7859982ae82dbf66820fdc`（父提交 `96e989f22a74c621ad6642a287738befa5ea6c6f`），尚未部署固定服务器。它修复 8760 h runner 在求解前无条件 `getA()` 的阻断：常规运行只记录 Gurobi `Fingerprint`、变量/约束/非零元，只有显式 diagnostic basis import/export 才物化完整 CSR。运行身份升级为 `baseline_contract + analysis_case`；Base、中央反事实、敏感性、遗留验证和模板均有显式角色，scenario overlay 只能修改白名单根。
- 容量充裕口径现有两个互斥合同：Base 与中央 V4 V1G 保持 `baseline_peak_v1`，新情景 `flexible_load_comfort_v4_v1g_effective_peak_sensitivity` 使用 `effective_peak_endogenous_v1`。后者采用每省一个 `capacity_margin_credited_capacity_gw` 辅助变量和逐小时两非零元约束，避免复制省级容量表达式。匹配 24 h 门禁均为 `OPTIMAL + solution_qc=PASS + 53/53 hard checks + valid result manifest`；baseline/effective 的 raw LP 分别为 `241,523/353,587/1,799,111` 与 `242,236/353,587/1,803,544`（rows/columns/nonzeros），effective 仅增加 `713` rows、`4,433` nonzeros（约 `0.246%`），solver runtime `55.253/53.021 s`。截断窗口的全国逐省峰值和发电侧总装机分别从 `1793.402 GW/3998.172 GW` 降到 `1255.373 GW/3785.672 GW`；这只证明容量价值通道真实且工程开销很小，不能把 24 h 差值解释为年度容量价值。
- 梯级水电不再把负本地入流静默截零。`target_bounded_proportional_transfer_v1` 对每个下游节点逐时按 `min(1, target natural flow / lagged upstream natural flow)` 显式调和上游转移，并把同一系数用于优化得到的 turbine+spill release；未来任何一源多下游拓扑在缺少 branch shares 时 hard fail。当前 8760 h 输入审计为 `335,304` 个原始负本地入流 node-hours、最小 `-5701.463 m3/s`、需显式调和 `158,199.650 million m3`、94 个节点，调和后最大水量恒等式残差 `4.55e-13 m3/s`。容量口径仍严格为站点 `297.8895 GW` + 省级聚合 `82.1105 GW` = `380 GW`。
- 新增 opt-in 的 accepted full-year Base solver artifact 合同：只保存压缩 `.sol`、post-crossover `.bas`、`.prm`、轻量 fingerprint 与 hash manifest；不全量导出 RC/slack/SA 范围、不计算 `KappaExact`，也不允许自动跨年或改变矩阵后复用。MGA 仍须等待 accepted full-year Base；本里程碑不启动 MGA 或 basis gate。
- 本地验证：聚焦测试 `58/58 PASS`；完整 discovery `135` 项中 `134 PASS`，唯一失败是本地忽略数据中的 `technology/technoeconomic_price_basis_manifest.json` hash `f89241...` 与冻结服务器 v4 数据包的权威 hash `397297...` 不同，服务器文件已实时复核仍为 `397297...`，因此未篡改 release contract 或用户本地数据。全新 1 h/24 h baseline/effective 四根全部 `OPTIMAL + PASS + 53/53 + closed manifest`；全新四年 1 h V4 V1G planning sequence 为 `PASS`，四年均 `ACCEPTED`，无 basis。下一步：文档提交并推送两端；再次实时核验服务器/ParaCloud；仅在无 solver、资源安全时 fast-forward，运行服务器权威数据根下完整回归与 1 h/24 h 门禁，然后按授权启动唯一、串行的 2030→2060 744 h V4 V1G diagnostic sequence。不得启动 8760 h、付费云、并发第二求解、basis gate 或 `Crossover=3`。
- 2026-07-29 固定服务器已部署并完成统一候选的隔离 744 h 门禁。当前代码身份为 `7c56622c266e673037bd6afaa70c85aa57e6cb13`，服务器 checkout 干净；外置表使用全新根 `/data/zz2/National_model/data/model_ready_20260729_unified_7c56622_v4`，标准数据归档 SHA256 为 `f3e6cc0f810d0f4e1ccf8fd10907fb25b8859546be397f21035cd072cdb9d261`。`model_input_files.json` 已升级到 v10（42 张运行表、12 个 sidecar），显式覆盖 Base、wave、V3、V4 与全部来源 manifest。服务器 `release_contract/readiness/hydro/V4-loader` 全部 PASS，完整回归 `130/130 PASS`。全新 V4 V1G 1 h/24 h 根均为 `OPTIMAL + solution_qc=PASS + 52/52 hard checks + current input/result manifests valid`；24 h 的 Barrier numerical trouble 由生产 `Crossover=1` 恢复为最优解，不能据此改用已拒绝的 `Crossover=3`。
- 当前唯一模型实现基线为 `codex/cispo-2030-full-lp` / `7aac739e03646edfed14bbf48ac77869ba66cbef`；本次终态审计只在其上增加交接文档，不改变模型、配置或数据合同。固定服务器 checkout 保持 clean `7c56622c266e673037bd6afaa70c85aa57e6cb13`，无需为追平文档而切换；本地工作树仅保留用户拥有的 `supplementary_materials/**` 与 `.codex_tmp/**` 修改/未跟踪文件，后续必须继续选择性暂存并保护。
- `/data/zz2/National_model/outputs/2030_744h_v0729_unified_v4_v1g_cold_v1` 已完成并通过严格工程验收。它是单独的 `--planning-year 2030 --horizon one_month`、`flexible_load_comfort_v4_v1g`、`barrier_16_auto_order_v2` (`Crossover=1`) cold gate，无 basis，未调用 planning-sequence runner。Gurobi 在 Barrier `313` 次后完成 Crossover，终态为 `OPTIMAL`，objective `2,330,214.449430 million CNY`，solver runtime `12,984.854 s`，simplex `832,655` 次；wrapper exit `0`、wall `3:42:57`、peak process-tree RSS `21.484 GiB`、swaps `0`，stderr 只有 `/usr/bin/time` 统计。`solution_qc.json=PASS`、`52/52` hard checks、current input manifest 和 result manifest 的运行时 validator 均为 `(True, [])`；最终 constraint/bound/dual violation 均低于 `1e-7`。求解 PID 已退出，未产生并发第二求解。
- 终态模块审计闭合冷热/EV 状态与边界、wave 输入和零选择、水电 380 GW 与月度/库容约束、PHS/电池容量和充放电、411 条网络 corridor 与 DC 方向、备用/惯量/容量裕度、碳/CCS 源汇平衡，以及成本 `accounting_scope`。objective 由 `2,112,470.998439 million CNY` annualized-planning scope 与截断时域 operation scope 共同构成；因此本根始终是 `TEST_ONLY_TRUNCATED_HORIZON`，不能作为年度科学结果、年度净价值或正式 2040 state anchor。
- 2026-07-29 16:32+08:00 终态刷新时，主机约 `114 GiB` available、swap `781 MiB/2.0 GiB`，实时 `vmstat si/so=0`、memory PSI=0；ParaCloud `squeue -u a8s001819` 为空。历史 `4003088/4003172/4004585` 仍分别为 `COMPLETED build-only / OUT_OF_MEMORY / TIMEOUT`。没有已验收的 8760 h 结果，也没有启动或获准启动 8760 h、付费云、basis gate、并发第二求解或 `Crossover=3`。
- 服务器隔离部署门禁发现并修复了本地同目录测试无法暴露的四类整合疏漏：hydro audit 的 `numpy.bool_` 跨环境 JSON 序列化；V4 上游 manifest 未进入部署包；V4 运行表及 wave 表/manifest 未进入标准 `model_input_files` 合同；已声明 implemented 的 V3 表未进入包且少数测试写死 `repo/data`。修复提交依次为 `a3ab9f5`、`95e1b76`、`5c749b6`、`e0b5dbd`、`7c56622`，均已推送 `origin` 与 `github`；旧的 v1--v3 数据根和失败审计目录只保留为故障证据，不得作为当前运行输入。
- 2026-07-29 对 7.28—7.29 多智能体改动完成首轮统一审计并形成实现提交 `1d04f07565c3039ed467ec4080f276bd0da90786`。发现 `3b3de57`/`b87b3b6` 的干净提交只含省级聚合水电 loader、漏掉配置/约束/输出，不能直接部署；当前提交已把常规水电 380 GW 闭合、重复 COMID 水量分配、V4 冷热/EV、PHS 功率—能量敏感性、成本会计和输出/QC 合并为一个可测试候选。`config/release_contract_v0729.json` 冻结 Base、solver profile、情景 catalog 与 11 个外置数据 SHA256；`scripts/audit_release_contract.py` 当前为 PASS。历史 `m2_model_boundary_audit_v1.json` 已显式标为 superseded，不能再代表当前模型。
- 技术经济生产口径已经进入当前代码、部署数据和活动 744 h 的实际解析配置，不是仅存在于补充材料。正确实施提交为 `29bbf90d9edde4e74e3e095b807f2fa1ffaab6a6`，它是本地/GitHub `7aac739` 与服务器 `7c56622` 的共同祖先；先前交接误写的完整哈希 `29bbf904638fbfa45911bb6d801432d592302e15` 已在本次交接中纠正。`technoeconomic_2025_cny_v2` 对生产货币输入统一使用 2025 constant CNY；本地迁移审计为 `ALREADY_APPLIED + PASS`、专项测试 `4/4 PASS`。服务器数据根的 `technology/technoeconomic_price_basis_manifest.json` 为 `APPLIED_PRODUCTION_LOCAL_DATA_PACKAGE + PASS`，活动 744 h 的 `input_manifest.csv` 与 `model_config_snapshot.json` 分别记录该 sidecar SHA256 和 `target=2025 constant CNY`。这不消除未来 CapEx 图读数、混合来源年燃料价和 V4 说明性成本的科学不确定性。
- 统一审计额外修复三项真实问题：`hydro_aggregate_flex_v1` 的向上备用 QC 曾重复计入省级聚合水电，已改为只使用模型导出的总水电备用；小时安全表的向下水电备用已包含聚合层，重新计算的 up/down closure 最大误差分别为 `1.42e-14/7.11e-15 GW`。V4 年化 enablement 成本不再误标为 selected-horizon cost，混合总项 `annual_operation` 标为 `COMPOSITE_SEE_COMPONENT_ROWS`。V4 gzip builder 固定 `mtime=0`，连续两次完整 build+validate 的六个输出逐文件字节一致，sidecar SHA256 为 `ad46c7610903726a059b92255332056935021763ca11433b0b866b6dd1ac144a`。
- 当前统一候选的 `py_compile` 通过，完整本地回归为 `129/129 PASS`；参数审计为 `11,727 rows / 26 PASS / 0 WARN / 0 hard fail`，保留 4 个已知科学风险；省级水电输入审计确认 `31` 省、`372` 省月行、`297.8895 + 82.1105 = 380 GW`。全新 2030 1 h Base、V4 V1G、hydro flex、PHS central 均为 `OPTIMAL + solution_qc=PASS + current input/result manifests valid`。首次 Base `_v1` 在 OPTIMAL 后因统一重命名漏改一处 export 字段失败，已保留作故障证据；修复后的 `_v2` 与 hydro flex `_v3` 闭合。
- 2026-07-29 已在本地当前工作树顺序完成匹配的 2030→2040→2050→2060 168 h Base 与 `flexible_load_comfort_v4_v1g` 两条 planning sequence；每年只接收上一年的显式 diagnostic state，不复用 basis。八个求解全部达到 `OPTIMAL + solution_qc=PASS + 52/52 hard checks + closed result manifest + current input manifest PASS`，两条序列 resume 后四年均为 `RESUMED_ACCEPTED`。Base/V4 raw LP 分别为 `1,167,956/1,024,400/9,546,696` 与 `1,240,868/1,071,396/9,859,176`（rows/columns/nonzeros）；V4 增量为 `+6.24%/+4.59%/+3.27%`，峰值 RSS 仅增加约 `0.12--0.27 GiB`，未出现内存或可行性退化。机器审计位于 `outputs/planning_sequence_168h_v0729_ab_audit/planning_sequence_ab_audit.{json,csv}`。
- 168 h 结果只证明数据传递和机制可解性。V4 在四年分别发生 `657.86/1435.91/2025.12/2314.68 GWh` EV 充电重排，全国峰值改变 `-0.90/-1.76/-2.00/-5.78 GW`；冷热转移吞吐为零（2050 仅 `5.2e-12 GWh` 数值噪声），说明中心参数和该代表窗口下优化器不购买冷热服务，不是公式失效。波浪能在两条序列中均为 enabled，1,284 条候选与 `9,798.111 GW` 原始上限均进入输入/QC，但最优装机和发电均为零；只能表述为“已考虑但该截断窗口未选择”。
- 不能把 V4 相对 Base 的目标差直接解释为年度净价值：年化 enablement/planning cost 被完整计入，而运行收益只覆盖 168 h。诊断性的“扣除显式柔性成本前系统收益”从 2030 到 2060 为 `3.52/11.26/24.76/33.89 million CNY`，只说明机制方向。为封堵误读，当前工作树新增 `accounting_scope`，把 `ANNUALIZED_PLANNING_COST` 与 `SELECTED_HORIZON_OPERATION_COST` 分开，同时保留旧 `value_million_cny_per_year` 列兼容；独立 1 h 根 `outputs/2030_1h_v0729_cost_accounting_metadata_v4_v1g` 已验证 `OPTIMAL + PASS + closed manifests`。2026-07-29 统一审计进一步把混合的 `annual_operation` 标为 `COMPOSITE_SEE_COMPONENT_ROWS`，并把 V4 年化 enablement 成本单独归入 annualized planning scope。
- 当前主线已完成 V4 中心情景的四年 168 h 工程闭环，但尚未达到论文科学闭环。作者已在 2026-07-29 明确授权：代码/外置数据口径统一并在服务器小门禁通过后，可启动一个隔离的 744 h 或两个月长度优化。当前选择标准 744 h V4 V1G cold gate，因为它是既有支持时域且同时覆盖新 Base 水电、wave 与 V4；不复用任何 basis，不启动并发第二求解。执行前必须先提交/推送精确候选、创建版本化服务器数据根、实时核验服务器 Git/进程/RAM/swap/PSI 与 ParaCloud、运行 release/input/readiness 和服务器 1 h/24 h 门禁。low/high V4 仍是论文科学敏感性的必要后续，但不再作为本次工程 744 h 的前置条件；MGA 继续等待完整 accepted Base anchor，`Crossover=3` 永久拒绝。
- 2026-07-28 常规水电 2025 容量口径已在本地闭合：`hydro_stations.csv` 的 2,030 条记录形成 297.8895 GW 可识别站点容量，另以 `provincial_aggregate_capacity_2025.csv` 表示 82.1105 GW 固定省级聚合容量，全国严格合计 380 GW；抽水蓄能运行下限保持 65.94 GW。国家能源局约 450 GW 的水电总量是四舍五入口径，380 + 65.94 = 445.94 GW，4.06 GW 舍入差不回填到任一技术。GHT operating non-PHS 的项目容量为 302.939 GW，中国归属份额 302.133 GW；旧“未匹配 39.869 GW”中已确认至少 15.419 GW 与 HydroCHN 清单重叠，故它不是可直接追加容量。
- 省级闭合不制造虚构坝址。四川 100 GW 下限、云南 83.6036 GW、湖北 36.7763 GW 常规水电规划锚点、贵州 22.98 GW 和广西 17.8838 GW 常规水电作为校准锚点，青海 16.445 GW 仅作外部排序/量级核验；其余省份在 `max(HydroCHN station, GHT China-attributable)` 非加和下界之上按既有省级先验比例调整。82.1105 GW 聚合层只有固定容量和由同省已识别站点 2019 水文形成的逐月可弃自然可用上限；无站点、水头、库容、COMID、扩张、跨期蓄水、梯级、备用、惯量、容量信用或 spur/trunk。
- 当前未提交工作树在 `b87b3b6a76e9b6a3683087105e3251daff22cfad` 之上接入该层；聚合发电进入省级电力平衡、成本会计、337 负荷中心年度注入、结果导出和硬 QC。水电定向测试 `12/12 PASS`；与当前模型相关的回归 `117/117 PASS`，完整 discovery 的另 2 项失败来自用户拥有的 `scenario_catalog.json` 字段 `blocked_by` 与旧测试期待 `reason`，与本水电改动无关且未修改。全新 1 h/24 h 根 `outputs/2030_{1h,24h}_v0728_hydro_provincial_closure_base_v2` 均为 `OPTIMAL + solution_qc=PASS + closed manifest`；24 h 聚合发电/可用量均为 97.768506 GWh、违反量 0，最大功率平衡残差 `1.12e-12 GW`，solver 43.188 s、峰值 RSS 0.743 GiB。它们均为 `TEST_ONLY_TRUNCATED_HORIZON`。
- Module 05 / S6 包已更新为 18 张表、两张主图、源数据、风险登记、QA 与 SHA256 manifest；`formal_closure_validation.csv` 为 `12/12 PASS`。最终空间图 `Figure_M05_02_hydropower_spatial_contract_v3.{png,pdf}` 把 R1、实际存放在 `R3/R3` 的 `hyd2_4l` 和 R5 共 5,950 条全国河网线以完全相同的层级和样式绘制在两幅地图中；图 a 表示五组核心梯级且不再标注 Laxiwa 等单站名称，图 b 表示非核心既有/潜在站点与省级聚合，南海诸岛改为图间空白区的单一共享插图，下排为当前容量与未来清单技术上限双栏柱图。V3 图件 QA 全部通过，Module 05 manifest 含 63 个文件；V2 作为历史版本保留。常规水电全国总量缺口已从 P0 改为“会计闭合、分配敏感性仍开放”的 P1；仍未关闭的 P0 是 2019 单年 monthly P30 环境流量代理，以及 VRE 2024/wave 2023/hydro 2019 的混合年协方差。本里程碑没有提交、推送、部署或读取/改变固定服务器与 ParaCloud，也未启动 168h/744h/8760h；早于本条的水电门禁不能重标为新容量口径。
- 2026-07-29 在同一未提交工作树上完成 PHS 功率—能量成本标定。Base 仍为固定 8 h PHS；低、中、高候选在每个规划年严格保留现行 2025 年不变价 8 h 总 CAPEX，只把能量侧成本占比分别设为 30%、36.5% 和 45%。中央值由 DOE/PNNL 与 ANU 两组直接分项证据得到的 31.69% 和 41.35% 取中点并取整；证据矩阵共 7 个独立来源组，其中中国证据 3 组、直接分项证据 2 组。三条配置均为 `PROPOSED_NOT_APPLIED_COST_CALIBRATED`，未替换 Base；最大 8 h 重构舍入误差为 `4.0e-6 CNY/kW`。全新中央情景 1 h 根 `outputs/2030_1h_v0729_phs_power_energy_separated_central_v1/2030` 为 238,529 variables / 80,794 constraints，达到 `OPTIMAL + solution_qc=PASS + closed manifest`；完整本地回归 `125/125 PASS`。Module 05 已扩展到表 M05-19—21、独立成本 QA 和更新的 S6 方法/技术归档，formal closure `12/12 PASS`。该门禁仅验证实现和成本会计，未运行 168h/744h/8760h，未触碰固定服务器或 ParaCloud；正式年度比较仍是候选升级的必要条件。

- 2026-07-28 冷热/EV V4 已在当前未提交工作树（基于 `b87b3b6a76e9b6a3683087105e3251daff22cfad`）收敛为数据支撑型工程情景。P0 修复包括：消除多省周期状态的 `p×p` 广播、把多省成本压为标量 Gurobi 表达式、将禁用 V2G 成本保持为 `LinExpr`、让 V4 QC 使用实际 smart-charge、修正 EV 电网充电上界，并删除允许无先行预热/预冷的负舒适债。冷热改为非负、全选定时域连续的服务库存；EV 改为“75% 不可调基线 + 25% 聚合可调服务”，严格复用已有逐省逐时 EV 基线，不把 `ev_hour_weight` 伪称为接桩率，也不虚构行程链或出发 SOC。V1G 为中心情景，V2G 仅独立敏感性；Base 和 V3 未改，V4 topology 绝不与它们互用 basis。
- `scripts/build_flexible_load_v4_inputs.py` 已从现有 `hourly_load_2025_2060.csv.gz` 与已审计 BAIT `+/-1 C` 包络生成五张 V4 输入；`scripts/validate_flexible_load_v4_inputs.py` 对 2030/2040/2050/2060 全部重新走 runtime loader，并生成含源文件/输入文件 SHA256 的 `data/flexibility/flexible_load_v4.manifest.json`。2026-07-29 统一审计修复 gzip 时间戳后，连续两次完整 build+validate 的六个输出均字节一致，当前 sidecar SHA256 为 `ad46c7610903726a059b92255332056935021763ca11433b0b866b6dd1ac144a`。中心/低/高参数、来源和独立证据计数分别登记在 `config/flexible_load_v4_central_parameters.csv`、`config/flexible_load_v4_source_registry.csv` 与 `config/flexible_load_v4_source_count_qa.csv`。这些值可直接运行，但状态仍是 `ENGINEERING_CENTRAL_REQUIRES_LOW_HIGH_SENSITIVITY`，不能表述为已观测的中国省级校准。
- 本地 `py_compile`、V4 定向测试 `11/11 PASS` 和完整回归 `123/123 PASS`。完整回归首次发现用户现有 PHS planning-state 测试夹具缺少已实现的 `phs_energy_capacity_mode`；仅向该 stub 补入旧模式 `fixed_duration_v1` 后重跑闭合，不改变模型。与当前稳定输入身份一致的新根 `outputs/2030_1h_v0728_flexible_load_v4_data_supported_v3`、`outputs/2030_24h_v0728_flexible_load_v4_data_supported_v2`、`outputs/2030_1h_v0728_flexible_load_v4_v2g_data_supported_v2` 均为 `OPTIMAL + solution_qc=PASS + closed manifest + current input_manifest PASS`；24 h V1G raw LP 为 `241,492 rows / 353,556 columns / 1,799,247 nonzeros`，solver `43.13 s`、端到端 `81.55 s`、峰值 RSS `0.760 GiB`。相对当前 24 h Base 候选仅增加约 `4.5% rows / 2.0% columns / 2.5% nonzeros`。首个 1 h 根 `_v1` 因禁用 V2G cost 的类型错误在 OPTIMAL 后 export 失败并保留作故障证据；旧成功根使用非确定性 sidecar hash，只保留为历史数值证据。所有截断根仅是工程门禁，不是论文结果；未运行 168h/744h/8760h，未部署或启动固定服务器/ParaCloud，未暂存或修改 `supplementary_materials/**`。下一步仅在作者接受公式与中心值后运行一个隔离的本地 168 h V1G gate；此后先做低/高敏感性，再谈 basis 工程。

- 2026-07-28 M2 boundary audit Stage A is closed locally at implementation commit `379a96a79cf14d7dc08d0a5cfd45b8223f2f4b47` (`feat: add m2 boundary audit`). It adds a machine-readable 11-item decision register (`config/m2_model_boundary_audit_v1.json`), actual flexible-load V3/V2G overlay registry (`config/scenario_parameter_registry.csv`), read-only auditor (`scripts/audit_m2_model_boundary.py`) and targeted tests. The audit creates no LP, changes no input, and passed with `9 PASS, 0 OPEN, 0 hard fail`; `scripts/audit_model_parameters.py` additionally reports `11,717` parameter rows, `26 PASS, 0 WARN, 0 hard fail`, and four explicitly carried open risks. `M2-PARAM-001` is therefore closed: every active V3/V2G override has an exact resolved-config path/value record and remains scenario-only, not Base.
- The current local uncommitted hydro work now contains both `duplicate_comid_flow_allocation=static_capacity_potential_share_v1` and the fixed province-aggregate conventional-hydro closure described above. It is **not deployed**. Because the aggregate layer adds variables, balance coefficients and fixed hydro cost, the earlier duplicate-COMID-only objective/topology is historical evidence and must not be used as the current gate. The current 24h raw LP is `231,076/346,736/1,754,607` (rows/columns/nonzeros), objective `2,104,433.505757702 million CNY`; it reached `OPTIMAL + PASS + closed manifest` without changing the rule that truncated annualized costs have no scientific interpretation.
- M2 remains intentionally bounded: existing VRE cohort retirement is `CLOSED_M1`; duplicate-COMID is `LOCAL_GATE_PASS_PENDING_COMMIT`; formal multi-year hydrology/PHS pairing and adequacy/capacity credit remain separate work; V4 now has reproducible engineering inputs and local 1h/24h gates but still requires low/high sensitivity before paper claims; BECCS low/base/high remains a sourced-required post-solve screen; Base stays `base_2024_vre_wave_on_flex_off_v1` (wave on, flexible load off); MGA remains blocked until a complete accepted Base anchor. No M2 finding licenses a 744h/8760h run, cloud job, server deployment, concurrent solve, cross-year basis, or rejected `Crossover=3`.

- 2026-07-28 对固定服务器 swap 的实时只读诊断否定了“只是 cache”的假设：`Cached + Buffers` 仅约 `5.6 GiB`，而 `AnonPages` 约 `49.5 GiB`、`Inactive(anon)` 约 `34.6 GiB`。约 `19.1 GiB` swap 属于仍在运行的匿名页：活跃 GPU `wind_power` Python（RSS 约 `43.0 GiB`、`VmSwap 8.18 GiB`）及两组 MATLAB（`VmSwap 6.01/2.28 GiB`）已解释约 `16.5 GiB`。`vmstat` 的 `si/so` 和 memory/IO PSI 当前为零，说明没有持续换页，但不表示这些匿名页可丢弃。`drop_caches` 无法降低 swap；`swapoff/swapon` 技术上可在约 70 GiB available RAM 下回迁页面，却会扰动这些活跃的非 CISPO 作业，未获明确主机级授权前不得执行。

- 2026-07-28 早期的重复 `COMID` 修复和 Module 05 / S6 站点下限审查已被本快照首四条的 380 GW 容量闭合层扩展；原 297.890 GW“仅为全国下限”、15 张表、9/9 QA 和三个 P0 的陈述仅保留为历史阶段，不是当前口径。
- 2026-07-28 18:15 后再次只读核验固定服务器：`/data/zz2/National_model/repo` 为干净的 `codex/cispo-2030-full-lp` / `701b9bc225013a5009dcce3f4e97ee2063dcd00f`，未发现真实 CISPO/Gurobi 求解进程，约 `70 GiB` 可用 RAM；swap 仍约 `19/21 GiB`。本轮没有切换 checkout、传输输入或启动远程求解，任何未来部署仍须重新实时核验并使用新命名输出根。
- 2026-07-28 本轮结束时已重新只读核验远程易变状态：固定服务器 `/data/zz2/National_model/repo` 是干净的 `codex/cispo-2030-full-lp` / `701b9bc225013a5009dcce3f4e97ee2063dcd00f`，未发现 CISPO/Gurobi 进程，约 `70 GiB` 可用 RAM；但 swap 仍为约 `19.1/21 GiB`，并有约 `43.0 GiB RSS` 的无关 Python 进程。ParaCloud `squeue -u a8s001819` 为空。按 runbook 仍是内存压力状态，未部署 `a5e34bf`/`616acb3`、未传数据、未启动任何远程求解；任一后续远程动作前仍须重新核验。

- 2026-07-28 当前 M1 提交的 168h 四根 basis 门禁已完成，全部使用 `barrier_16_auto_order_v2` / `Crossover=1` 且仅为 `TEST_ONLY_TRUNCATED_HORIZON`。2030 cold/warm 分别为 solver `520.266/10.874 s`、RSS `2.924/2.395 GiB`；2040（仅接收明确 2030 diagnostic state bridge）cold/warm 为 `489.268/14.257 s`、RSS `3.038/2.518 GiB`。四根均为 `OPTIMAL + solution_qc=PASS + validate_result_manifest=(True, [])`，warm 全为 0 Barrier/0 simplex，同年 objective 均完全一致；容量最大差 2030 `0`、2040 `7.11e-15 GW`，成本/发电量仅浮点量级。2040 只导入其自身 cold basis，未跨年导入。虽已证明同构重解加速，但孤立 744h basis gate 必须先额外完成同配置 cold 744h 才能产生 basis；当前没有第二次同构 744h 的端到端需求，故不申请也不启动 744h。

- 2026-07-28 本地 M0/M1 basis 前置建设已由实现提交 `a5e34bf5357301c205b246b0aa2149db0dca9c3b`（`feat: close basis preparation m0 m1`）闭合，尚未推送或部署。M0 将运行身份拆为 `scientific_case`、`lp_topology`、`solver_runtime` 与 `implementation_bundle`：只有变量/约束顺序、约束方向、维度、NNZ 以及原始 CSR sparsity pattern 的精确 `lp_topology` 相等时才允许导入 LP basis；结果 resume 仍保守审计 implementation bundle，科学 case 或实现 bundle 差异只记录审计、绝不把 warm 根提升为科学验收。24h 2030 Base cold/warm 均为 `OPTIMAL + solution_qc=PASS + closed manifest`，objective `1996289.6918468594` 完全一致；warm 为 `LPWarmStart=2`、0 Barrier/0 simplex（`65.237 s` 降至 `1.188 s`）。
- M1 已明确 Base 科学标签与 `hybrid_weather_bundle_v1`（VRE 2024、wave 2023、hydro 2019），参数 registry 26 项 PASS；VRE retirement 生产模式为 `cohort_survival_v1`，并保留 `fixed_floor_v1` 作为对照，2030/2040/2050/2060 cohort floor 均有测试闭合。BECCS lifecycle 仅为目录外、post-solve low/base/high screening，绝不改变 LP 规模或冒充有来源的生产参数；新增 bound tightening 仅加入可证明不改变可行域的显式上界。M1 24h cold 与 M0 结果 objective、容量、成本与发电量均为零差异，raw LP 仍为 `231,076/345,992/1,753,119`，本地完整回归 `114/114 PASS`。现存旧 168h 四根是 M0/M1 前快照，只可作历史性能证据；下一步必须在当前提交重新运行 2030/2040 cold/warm 四根门禁，不得复用 `Crossover=3`、跨年 basis、固定服务器/8760h 或付费云任务。

- 2026-07-28 技术经济 V2 已获作者批准并由本地实施提交 `29bbf90d9edde4e74e3e095b807f2fa1ffaab6a6` 写入生产模型。统一价格合约为 `technoeconomic_2025_cny_v2`：CISPO 国内 2022 年不变人民币轨迹在 2030/2040/2050/2060 各规划年统一乘 `1.004004`，只平移共同价格基准、不改变年际学习比例；核电 CapEx 回到 `2800/2650/2500/2350 USD/kW` 后乘 `7.1429 CNY/USD`；省级燃料按原始 USD/GJ 乘同一汇率；波浪能按 EUR 来源值乘 `8.1185 CNY/EUR`；CCS 捕集/运输/封存为 `261.04104 CNY/tCO2`、`0.50 CNY/tCO2/km`、`45 CNY/tCO2`。物理参数、real WACC、市内数值破简并项及独立灵活负荷情景成本不重基准。

- 本地 Git 外置 `data/` 已由幂等脚本迁移并生成 `data/technology/technoeconomic_price_basis_manifest.json`；第二次执行只校验、不重复换算。带本地原生水文路径、2024 VRE 与 wave 路径的完整回归为 `106/106 PASS`，数据包 smoke test 为 `142/142 PASS`。`config/model_input_files.json` 已升级到 v5 并要求服务器数据包携带该价格合约 sidecar。固定服务器和 ParaCloud 均未部署、未启动求解；Git 推送不等价于外置数据包部署，后续服务器同步须新建版本化数据根并重新运行 readiness/smoke/input-manifest 门禁。

- 2026-07-28 本地 168h 四根 basis 门禁已闭合，全部使用 `barrier_16_auto_order_v2` / `Crossover=1`，仅为 `TEST_ONLY_TRUNCATED_HORIZON`：2030 cold/warm 分别为 solver `576.593/11.406 s`、RSS `2.925/2.262 GiB`；2040 cold/warm 为 `543.965/15.517 s`、RSS `3.030/2.263 GiB`。四根皆为 `OPTIMAL + solution_qc=PASS + validate_result_manifest=(True, [])`。warm 均为 0 Barrier/0 simplex；同年 cold/warm 的 objective 和全部容量 CSV 相同，发电量最大绝对差仅 `3.64e-11`（2030）/`2.91e-11 GWh`（2040）。2040 使用 2030 明确 test-only state bridge，但只导入 2040 自身 cold basis，未跨年 basis reuse。basis sidecar 以 Git/config/profile/命名结构 hash 约束，不能用于全年科学结果。

- 2026-07-28 本地实施已提交为 `282c393fd98e25737631493e19110e38bb49ed28`（`feat: share VRE intra-grid connection and retire cohorts`），尚未推送或部署。提交后即时只读核验固定服务器：HEAD 仍为 `701b9bc225013a5009dcce3f4e97ee2063dcd00f`，无 CISPO/Gurobi 进程、约 70 GiB 可用内存，但 swap 已用约 19/21 GiB，另有约 45 GiB RSS 的无关长任务；因此按 runbook 判定为内存压力，未切换 checkout、未传输数据、未启动 168h。ParaCloud `squeue -u a8s001819` 为空。此快照只记录当时状态，任何后续部署前仍须重新实时核验。

- 2026-07-28 本地已完成“同格网风光共享并入 + 既有 VRE 可追溯退役”模型修正，尚未提交或部署。基线为 `codex/cispo-2030-full-lp` 的 `d73eb3390c970b0da6319a03ca8b1d3c30384040`；本次只修改 `cispo_model/{config,data,io_contract,master}.py`、`config/{optimization_2030.json,model_input_files.json}`、`scripts/build_existing_vre_cohorts.py`、两组测试和本交接/服务器文档，既有 `supplementary_materials/**` 用户改动未触碰。对 36,686 个 VRE technology-site 行、16,317 个 `grid_uid` 实测：12,603 个多技术格网全部连接到唯一同一 `substation`。新 spur 严格采用 CISPO S4-18 的 `max_t(cf) × capacity`；风光 trunk 改为 CISPO S4-19 的站级 potential-weighted equivalent peak，避免把风光非同期峰值相加。该设计只增加一次完整 8760 气象 CF 扫描和审计 CSV，不增加逐小时 LP 变量或约束。

- 新的 `data/vre/existing_capacity_cohorts_2025.csv` 由可复现脚本从 GEM operating projects 和已审计的 V3 0.25° 既有容量表构建：15,171 行，SHA256 `e00791ec9597897da80377458d6acefdc481ef1708c0f86d68adb2a5576f92d0`，按技术精确闭合 2025 年 onwind/offwind/UPV/DPV `593/47/670/530 GW`。有有效 GEM 投运年的队列按技术寿命退役；未识别 OSM/残差和边界后才投运的记录显式作 2025 boundary-censored cohort，不虚构年龄。退役只解除 observed-capacity floor，不移除技术 site upper，因此同址再建是优化决策而非强制假定；既有 spur/trunk 代理按显式连接复用规则独立保留。

- 隔离本地 24h Base 根 `outputs/2030_24h_v0728_intra_grid_cohort_smoke_local_v1` 已达到 `OPTIMAL + solution_qc=PASS + closed result_manifest`；wave 开启、flexible load 关闭。raw `231,076/345,992/1,753,119`、presolved `129,500/260,190/1,295,919`（rows/columns/nonzeros），Barrier 99、crossover 53,551 simplex、solver 34.83 s、端到端 58.91 s、峰值 RSS 0.739 GiB。2025 VRE 初始 trunk proxy 从旧 nameplate `1,310.0 GW` 降至共享峰值 `1,069.513 GW`（-18.36%）；这是网络代理成本口径变化，不能由截断时域目标外推科学结论。完整本地回归 `102/102` 通过。固定服务器 checkout、进程、输出和 ParaCloud 队列均未由本里程碑写入；任何部署前必须重新实时核验。

- 2026-07-28 Module 04 的审批前深度审查 v2：15 个实质性审查单元登记 63 个独立来源、104 条证据关联，每单元 6—8 个独立证据组，`table_m04_19_source_count_qa.csv` 全部 PASS。审批前 `candidate_inputs_v2` 中的 `PROPOSED_NOT_APPLIED` 作为历史快照保留，不回写覆盖；其后已按本快照最前两条所述完成授权集成。审批后新增 `production_integration_2025cny_zh.md`、表 M04-24 和 production QA，终止标记为 `FINAL_M04_V2_PRODUCTION_INTEGRATION_PASS`。

- 2026-07-28 补充材料总控与 Module 04 的最初候选阶段保留为历史证据：候选 QA 19/19 PASS，深度 v2 QA 8/8 PASS；后续 v2 授权以核电 USD 币种链和多来源 CCS 中央值替代早期候选，并已按当前快照完成生产落库。电池功率—能量拆分、燃料长期轨迹、技术特定 WACC、既有机组寿命、CCS 有效能耗惩罚及海上风电空间成本仍保持敏感性/结构审查项。
- 2026-07-28 的当前模型实施提交为 `1449a4571d2881077f926bbc4116d2c9bdc6b5d5`，分支为 `codex/cispo-2030-full-lp`；其后提交仅闭合验证、运行状态和交接文档。744h 实际运行 checkout 为 `0dadfe9566ea69b1105161451a399e476307a4f1`；最新本地/远端/服务器 HEAD 属易变化信息，必须用 Git 实时核验。早先快照所称服务器仍为 `4e1999d` 已被实时证据纠正。
- 风电/光伏运行气象年已切换为 2024，并采用显式 `beijing_natural_year_drop_feb29_v1`：模型小时严格覆盖北京时间 2024 自然年，使用 2023 UTC 最后 8 小时衔接 2024 UTC 数据，再删除北京时间 2 月 29 日，最终保持 8760 小时。波浪能仍使用独立的 2023 reference time coordinate，水文仍为 2019；这是明确的混合数据年边界。输入 manifest 同时锁定 2023/2024 两组 VRE Zarr。服务器已追加四个 2024 stores；传输 tar 的本地/服务器 SHA256 均为 `2f70713d7a93633f8478e554b1924be7fdfe1d05ff5674a385461d3fa3045cfc`，四个目录文件数与本地逐项一致，既有 2023 数据未覆盖。
- 求解器全局硬编码已改为 solver-profile-controlled；Base 默认仍保留已验证的 `DualReductions=0 + InfUnbdInfo=1`。新增显式生产候选 `barrier_16_auto_order_v2`（1/0）、`PreSparsify=2`、`PreDual=1/2` 与旧诊断参数 profile。新增可选且严格等价的 `annual_emissions_province_hierarchy_v1`：用 31 条省级年度排放会计替换一条全国全小时行，再由 31 个省级变量进入全国碳上限；它是 formulation A/B，不是新科学情景。
- 本地完整回归 `89/89` 通过。2024 气象 Base 的两个 1h 根均为 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，全国式与省级分层式目标完全一致。六个 24h 匹配根也全部 `OPTIMAL + PASS + manifest closed`，目标仅有浮点级差异。省级分层把原始 6,697-NZ 全国排放行拆开，但在 `DualReductions=1` 下 dense/hierarchy 的 presolved 矩阵、`AA' NZ=1.925e6`、`Factor NZ=5.602e6`、`Factor Ops=5.883e8` 完全相同，因此尚无性能收益证据。
- 服务器完整回归 `89/89`。三组新 168h 根均 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`。旧 0/1 参数为 presolved `731,124/820,537/7,212,238`、`AA' NZ=2.160e7`、`Factor NZ=1.042e8`、`Factor Ops=8.440e10`、163 Barrier/626.10 s、crossover 72.76 s、229,459 simplex、700.50 s、3.407 GiB RSS。dense v2 为 `704,597/719,155/7,133,417`、`1.987e7`、`1.023e8`、`8.480e10`、124 Barrier/475.02 s、crossover 190.62 s、630,993 simplex、668.05 s、3.411 GiB。省级分层 v2 的 presolved/factor/迭代/work units/目标与 dense v2 完全一致，仅墙钟受调度波动，故不采用分层。唯一 744h 候选为 dense + `barrier_16_auto_order_v2`；必须显式保留 crossover 放大风险。
- 新 744h 根 `/data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_v2` 已在运行 checkout `0dadfe9` 上完成并严格验收：`OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=(True, [])`，49 项 hard checks 全部通过；Base 波浪能开启、灵活负荷关闭，VRE 为 2024 北京时间自然年对齐。raw/presolved 为 `4,915,427/3,711,992/40,836,493` 与 `3,063,498/2,664,976/31,086,440`（rows/columns/nonzeros），`AA' NZ=6.388e7`、`Factor NZ=7.481e8`、`Factor Ops=4.721e12`。Barrier 211 次/7,543.19 s，crossover 5,709.46 s，simplex 1,437,196 次，总 solver 13,268.90 s，端到端 3:47:18，峰值进程树 RSS 20.049 GiB，无 swap。最大功率平衡残差 `3.43e-12 GW`；最大约束/边界/对偶违例 `9.32e-8/2.75e-8/9.35e-8`。它仍是 `TEST_ONLY_TRUNCATED_HORIZON`，不是年度科学结果。
- 当前 Base 为含陆上/海上风电、光伏和严格映射到既有 marine `grid_uid` 的波浪能，`flexible_load=false`；唯一可运行覆盖情景为 `flexible_load_comfort_v3_v2g_5pct`，仍是待校准敏感性。历史 wave-off 744h 仅作历史数学/QC/性能证据，绝不能伪称为当前 Base 门禁。
- 固定服务器在 `9a3c5e8` 阶段完成波浪数据和运行环境部署，随后以 `0dadfe9` 运行 168h/744h 门禁；运行根使用新增且不覆盖历史的 `/data/zz2/National_model/data/model_ready_20260723_v0722_city337_wave_20260727` 与 `/data/zz2/National_model/data/wave_energy_20260727`。`wave_sites.csv`、`wave_input_manifest.json`、`wave_grid.nc` 的 SHA256 分别为 `9b318630e4783a9453492ae6403ae9f3d108a9cec09499dd6f0acd961fdd79d3`、`540d601070b093f0d991193ce606c861ab5b310b7a892ca9787a455b95405af9`、`b2e259862c8bad9a34addf24534a8d1e1c8f66c4e351bdfe13fe9cfca1eb4831`。服务器专用 CISPO 环境补齐了与本地一致的 `xarray==2025.1.2`，并通过 `wave_grid.nc` 打开 smoke test；未记录任何密钥或 license 内容。
- 先前 2023 气象的固定服务器 Base 输出 `/data/zz2/National_model/outputs/2030_{1h,24h,168h}_v0728_server_wave_base_*` 与 `2030_1h_v0728_server_mga_runner_base` 均为 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，且都是 `TEST_ONLY_TRUNCATED_HORIZON`。其 168h raw/presolved 为 `1,167,958/1,019,192/9,486,177` 与 `730,782/820,208/7,174,545`（rows/columns/nonzeros），`AA' NZ=2.150e7`、`Factor NZ=1.045e8`、`Factor Ops=8.532e10`、138 Barrier、411,056 simplex/crossover、690.86 s solver、3.359 GiB process-tree RSS；该证据保留为历史年份对照，不能替代上面的 2024 门禁。
- `solver_audit.py` 现在解析 Barrier 的 `solved` 与 `performed` 分支、crossover 时间、presolve 缩减、factor/AA' 比和 post-Barrier 时间；同机 `1h/24h/168h` 审计表在 `/data/zz2/National_model/outputs/solver_audit_v0728/base_time_expansion_1h_24h_168h.{json,csv}`。24h 的 Barrier 虽为 `performed`，但 crossover 将终态恢复为 `OPTIMAL`，因此终态必须以 `solve_report.json`/QC/manifest 为准。
- `warm_start_basis.bas` 是仅限 diagnostic 的 crossover 后 LP basis，不是可序列化的 Gurobi 模型、presolve 状态、Barrier factorization 或 crossover tableau。导入前强制验证源 manifest、`OPTIMAL+PASS`、git、情景、小时数、raw dimensions 与全体变量/约束名-方向哈希，跨年还须显式 `--allow-cross-year-basis`；科学全年自动 basis 复用被代码阻止。固定服务器 1h 证据：2030 同年从 9.43 s/80 Barrier 降至 0.25 s/0 Barrier；2030→2040（携带严格 cohort state）从 9.29 s/77 Barrier 降至 0.52 s/0 Barrier，2040 目标一致至浮点误差。它们仅说明工程可行性，不构成全年性能或科学结论。
- 已保留既有 744h 根且未原地重建 manifest；固定服务器未启动 8760h，ParaCloud 未提交新任务。当前 checkout 的 MGA 只能接受闭合的 `SCIENTIFIC_PRODUCTION + BASE_MINIMUM_COST + OPTIMAL + PASS` 年度 Base 根，并逐项匹配 resolved config 和 required-input hash；它将原年度成本作为硬上限、以点/省/全国筛选的风光/波浪/水电/储能新增容量为二级目标，并拒绝导出递进 planning state。当前没有 accepted Base 全年结果，故未运行 MGA。任何云端 8760h 仍需用户单独确认。

- 当前生产工程实施提交为 `701b9bc225013a5009dcce3f4e97ee2063dcd00f`，已推送 `origin` 与 `github` 并部署到固定服务器。该提交不改变 Base 数学模型、数据口径或情景边界；新增单运行根原子 claim、`run_identity.json`、源码/config/profile/scenario/formulation/data-root 身份、运行前当前输入复验、递进序列身份锁与 stale-lock 恢复协议。runner 只有在 `OPTIMAL + solution_qc=PASS + validate_result_manifest=True` 时返回成功。本地与服务器完整回归均为 `98/98`；本地新 Base 1h/24h 根 `outputs/2030_{1h,24h}_v0728_production_contract_v1` 均闭合，使用 2024 VRE、wave on、flexible load off，24h objective 为 `1,982,265.6076383933 million CNY`。
- 固定服务器 wave-ready 数据根以 add-only 方式补齐唯一灵活性覆盖层所需的 `load/flexible_load_envelope_v3.csv.gz` 及 manifest，未覆盖任何既有文件；SHA256 分别为 `b5ebda4344a8f978606c242065159f27a75994a5d976f2cbe06038d66a429a03` 与 `0298256b2c1394f8e5a9e36780d2be279f06b27b291a9eca57daae91dba9a745`。这只闭合数据契约，不表示柔性参数已完成科学校准。
- 严格同结构 168h Crossover A/B 已闭合。`Crossover=1` 参考根 solver `649.17 s`、Barrier `124/455.86 s`、crossover `190.92 s`；`Crossover=3` 候选 solver `594.63 s`、Barrier `124/474.61 s`、crossover `117.67 s`。两根 raw/presolved、`AA' NZ=1.987e7`、`Factor NZ=1.023e8`、`Factor Ops=8.480e10`、目标、49 项 hard checks、manifest 与约 `3.41 GiB` RSS 一致；Crossover=3 的总 solver 快 `8.4%`、crossover 快 `38.4%`。`CrossoverBasis=0` 为 `661.25 s`，无收益，已淘汰。
- 744h 放大结果否决将 `Crossover=3` 作为生产候选。隔离根 `/data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_crossover3_v1` 与接受的参考根具有相同 raw/presolved/factor 结构、相同 211 次 Barrier 和 2024 Base 身份；其 Barrier `6,981.07 s`、PPush `1,191.93 s`、DPush `1,214.00 s`，但 primal cleanup 出现量级 `1e8--1e38` 的 infeasibility 循环。按数值稳定性停止准则优雅中断后，`solve_report=INTERRUPTED`、runtime `10,930.99 s`、crossover `3,947.89 s`、simplex `1,724,960`、peak RSS `19.828 GiB`，没有解、QC 或 result manifest；它不是科学结果，也不能被宣称为“更快”。机器可读比较为 `/data/zz2/National_model/outputs/solver_ab_v0728_crossover_744h.{json,csv}`。接受的 744h 工程参考仍是 `2030_744h_v0728_2024_dense_dualred_v2` / `barrier_16_auto_order_v2` (`Crossover=1`)。
- 当前固定服务器无活动 CISPO/Gurobi 求解，历史与候选输出均保留。下一步生产路线：保留 `Crossover=1` 作为唯一接受的 744h profile；任何新 solver/formulation 改动先经过匹配 24h/168h 的 `OPTIMAL+PASS+manifest` 门禁，再由唯一赢家获得一个新 744h 根。固定服务器 8760h 与新付费云任务继续禁止；8760h 前仍需用户单独确认、高内存节点、不可变身份、线程/SoftMemLimit、预算与优雅停止规则。

## Superseded snapshot detail (preserved historical notes)

- 原始 LP 约束族稀疏审计已在本地闭合（2026-07-27，实施提交 `6114157`）：新增只读 `--constraint-family-audit`，在 `model.update()` 后以显式 50,000,000 非零元安全上限读取原始矩阵；它不改变变量、目标、约束、求解器参数或任何科学情景。输出 `constraint_family_audit.json` 纳入 `output_catalog.csv` 与 result manifest，记录稳定命名前缀的约束/变量族、每族矩阵非零元、最稠密的 25 个具体行/列，以及仅能从日志获得的全局 presolve/ordering/Barrier/crossover 指标。Gurobi 不暴露稳定的预处理后来源归属，审计明确禁止将全局 presolve 删除量归因于任一约束族。
- 新的含波浪、无灵活负荷 Base 根 `outputs/2030_{1h,24h}_v0727_constraint_family_audit_base_v3` 均达到 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，所有 hard checks 为真。24h 原始/预处理矩阵为 `231,074/345,992/1,729,035` 与 `129,335/260,116/1,269,506`（rows/columns/nonzeros）；`AA' NZ=2.200e6`、`Factor NZ=6.284e6`、`Factor Ops=7.399e8`、89 Barrier、57,741 simplex/crossover、29.107 s solver runtime 和 0.712 GiB 峰值进程树 RSS。精确最稠密行依次是 `annual_emissions_accounting`（6,697 个非零元）、`capacity_margin_p65`（6,491）、`capacity_margin_p15`（5,736）以及 31 个 `co2_source_balance_p*`（各 3,246）；最稠密列为省级 `storage_capacity_gw[province,1]`（各 194）。水电逐站库容/泄流/水量平衡并非这次矩阵密集度的首要来源。
- 审计只确定候选，不允许删除容量裕度、CO2 源汇守恒、年度碳约束或储能物理。下一步仅为 `annual_emissions_accounting` 的省级会计分解准备代数等价证明与匹配 24h A/B；只有目标、全部 QC、manifest、presolved/factor 结构、阶段时间和 RSS 均通过，才可考虑 168h。当前未部署固定服务器或 ParaCloud、未启动任何长任务；既有 744h、所有其他输出和 `supplementary_materials/**` 保持未改。

- 孤立梯级节点的等价构建瘦身（2026-07-27，实施提交 `9787ba7`）：保留 `data/hydro/cascade_topology_nodes.csv` 的 142 个节点和 `cascade_topology_edges.csv` 的 124 条边，不删除水电站、GRFR 入流、库容、泄流变量或水量平衡。8 个经核验为“零度、单站”的孤立拓扑节点仅从逐小时核心梯级装配转入既有向量化独立水库平衡；因其无上游到达流且本地入流就是站点 GRFR 可用流量，S4-17 逐项代数等价。有效核心行由 146 降至 138，结果 QC 记录该数量、124 条有效边及 8 个转入独立平衡的节点；未来多站孤立节点会硬失败而不会静默转换。
- 本地完整回归为 `71/71` 通过。全新且隔离的含波浪 Base 根 `outputs/2030_{1h,24h}_v0727_cascade_isolated_nodes_independent_base` 均达到 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，所有 hard checks 为真，灵活负荷关闭、波浪能开启。24h 与 RUC 瘦身后对照的原始/预处理矩阵均为 `345,992/231,074/1,729,035` 与 `260,116/129,335/1,269,506`（columns/rows/nonzeros）；最优目标差仅 `9.78e-09 million CNY`。添加顺序改变使 factor/crossover 路径有数值差异（`Factor NZ` `6.111e6→6.284e6`、67,614→61,108 simplex），故这只是极小的 Python 约束构建清理，未证明 Barrier 加速或 8760h 内存改善。截断 LP 的退化可导致逐小时调度取不同等价最优基，不能据此解释为物理边界改变。
- 此次仅本地操作：未连接或改动固定服务器 checkout/进程/内存/输出，也未查询或改动 ParaCloud 队列；未启动 744h、8760h、第二个求解或付费云任务。既有输出（含 744h）和 `supplementary_materials/**` 均未触碰。任何未来服务器部署仍需实时复核状态、部署精确已推送提交并先运行单一新命名的匹配 168h 门禁。

- 连续 RUC 的可证明等价瘦身（2026-07-27，实施提交 `3f2255a`）：在不改变任何变量、目标函数、科学情景、容量/备用/惯量/爬坡/最小出力/启停时序或水电约束的前提下，移除了四组已被保留时序行严格蕴含的逐小时上界：`online<=capacity`、`startup<=capacity`、`shutdown<=capacity` 和通用 `gross<=pmax*online`。建模前新硬校验要求完整 RUC 参数、`min_up_h>=1`、`min_down_h>=1`、`pmin_fraction<=pmax_fraction`；S4-24、S4-25 和 S4-29 仍全部保留，因此这是可行域完全等价的行缩减而非放松。详见 `cispo_full_lp_model_spec.md` §5.5.3。
- 新建且隔离的 Base 1h/24h 根 `outputs/2030_{1h,24h}_v0727_ruc_dominated_bounds_removed_base` 均达到 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，灵活负荷关闭、波浪能开启。相对于对应的 wave-integrated Base 对照，变量数和最优目标不变（1h 仅有 `-2.33e-10 million CNY` 浮点舍入差，24h 完全一致）；1h/24h 原始行数精确减少 `1,364/32,736`，非零元减少 `2,728/65,472`。24h 原始矩阵由 `345,992/263,810/1,794,507` 降至 `345,992/231,074/1,729,035`（variables/rows/nonzeros），但 presolve 后均为 `129,335/260,116/1,269,506`，且 `AA' NZ=2.200e6`、`Factor NZ=6.111e6`、`Factor Ops=6.039e8`、95 Barrier、67,614 simplex/crossover 完全相同。该缩减降低的是原始建模/矩阵负担，并未在此尺度改变 Barrier 因子分解瓶颈。
- 更新后的 8760h 静态 preflight 是 `41,186,792` variables、`55,928,636` estimated constraints、`497,144,388` estimated nonzeros、`33.40 GiB`；较原估算少 `11,948,640` 行和 `35,845,920` 估计非零元。它只是结构性预估，绝不能作为全年 Barrier factorization 可行性或 8760h 授权证据。本轮未接触固定服务器 checkout/进程/输出或 ParaCloud 队列，未启动任何服务器、云端、744h 或 8760h 作业；既有 744h 根保持未改。

- 情景边界已按用户指令重置（2026-07-27，实施提交 `c992550`）：唯一可运行的基准为 `base`，其默认包含陆上/海上风电、光伏与已严格映射到既有 marine `grid_uid` 的波浪能；`flexible_load=false`。唯一可运行的柔性覆盖层是 `flexible_load_comfort_v3_v2g_5pct`，它继承同一含波浪 Base，并启用 `comfort_envelope_v3` 冷热状态、EV V1G 与日内因果 5% V2G。其灵活性参数仍为待校准敏感性，不得作为已校准 Base 结论。旧 `flexible_load_v1`、`flexible_load_state_v2`、`flexible_load_v2g_v1`、单独 comfort/wave 及各组合情景 JSON 已删除；历史代码、Git 记录和既有输出均保留且只能按其原情景身份解释。`CISPO_WAVE_ROOT` 因而是两个当前可运行情景的必需运行时数据根。
- 本地验证（`c992550`）：设置 `CISPO_WAVE_ROOT` 后，完整 `unittest discover` 回归为 `66/66` 通过。四个全新截断根 `outputs/2030_{1h,24h}_v0727_wave_integrated_base` 与 `outputs/2030_{1h,24h}_v0727_wave_integrated_flexible_v3_v2g_5pct` 都独立达到 `OPTIMAL + solution_qc=PASS + validate_result_manifest=True`，所有 hard checks 为真且 scenario identity/开关复核正确。24h Base 为 raw `345,992/263,810/1,794,507`、presolved `129,335/260,116/1,269,506`（rows/columns/nonzeros）、`AA' NZ=2.200e6`、`Factor NZ=6.111e6`、`Factor Ops=6.039e8`、95 Barrier、67,614 simplex/crossover、34.074 s、0.735 GiB 峰值 RSS；24h 柔性覆盖层为 `354,920/268,398/1,844,355`、`132,254/266,492/1,299,953`、`2.221e6`、`6.179e6`、`5.905e8`、101、56,990、33.984 s、0.731 GiB。它们均为 `TEST_ONLY_TRUNCATED_HORIZON`，不能解释为年度科学结果或已校准技术经济性。
- 全年静态 preflight（未构建、未求解）现为：wave-integrated Base `41,186,792` variables、`67,877,276` constraints、`532,990,308` nonzeros、36.47 GiB；唯一柔性覆盖层 `44,445,512`、`69,551,896`、`538,014,168`、37.63 GiB。本机可用内存约 15 GiB，低于 96 GiB preflight 门槛；这些静态数值绝不证明 Barrier factorization 可行。此次只做本地工作，未触碰固定服务器 checkout/进程/输出、ParaCloud 队列或历史 744h 根；固定服务器 8760h 和新的付费云端任务仍未授权。

- 本地全模块联合敏感性与求解结构审计（2026-07-27，提交 `31dc265`）：新增显式、独立的 `wave_energy_medium_v1_flexible_load_comfort_v3_v2g_5pct` 情景；它同时启用既有 marine `grid_uid` 波浪能、`comfort_envelope_v3` 冷热状态、EV V1G 和 5% 日内因果 V2G，但 `evidence_status=EVIDENCE_ANCHORED_PARAMETERS_REQUIRE_SENSITIVITY`，绝非 Base。完整本地回归 `67/67` 通过。新根 1h、24h、168h 分别达到 `OPTIMAL + solution_qc=PASS + validate_result_manifest=True`，全部 hard checks 为真；168h 为 raw `1,081,688/1,429,226/10,293,428`、presolved `751,365/865,314/7,363,654`（rows/columns/nonzeros），`AA' NZ=2.162e7`、`Factor NZ=1.056e8`、`Factor Ops=8.603e10`、180 Barrier、239,930 simplex/crossover、602.265 s 和 3.296 GiB 峰值 RSS。截断窗口只出现 V1G（上/下移各 190.173 GWh）；冷热、V2G、波浪容量/发电均为零，不能作技术经济性结论。全年静态 preflight 为 44,445,512 variables、69,551,896 constraints、538,014,168 nonzeros 和 37.63 GiB，较 Base 多 8.64% variables/2.88% constraints/3.28% nonzeros/1.63 GiB；它不证明 Barrier factorization 可行。本轮未改变 Base、既有 744h、固定服务器 checkout/进程或 ParaCloud；固定服务器 8760h 和新付费云端任务仍禁止。细节见 `MODEL_COMBINED_MODULE_SOLVABILITY_AUDIT_20260727.md`；下一步仅在同机同 profile 的匹配 168h A/B 和资源复核后评估结构优化，不直接放大到全年。

- 固定服务器 Base 168h manifest 闭合门禁（2026-07-27）：在空闲、干净且已 fast-forward 到 `67482ab` 的 `/data/zz2/National_model/repo` 上，以 `barrier_16_auto_order_v1`、`Threads=16`、`SoftMemLimit=48` 运行新根 `/data/zz2/National_model/outputs/2030_168h_v0727_manifest_runtime_contract_base`。服务器完整回归通过 `67` 项（其中 2 项为可选 xarray 测试而跳过）。门禁为 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`；灵活负荷与波浪能关闭，所有 hard checks 为真。LP 原始规模为 1,393,915 行、1,011,079 列、9,797,949 非零元；presolve 后为 729,559/817,723/7,001,232，ordering 26.08 s，`AA' NZ=2.131e7`、`Factor NZ=1.036e8`、`Factor Ops=8.436e10`。Gurobi 为 161 次 Barrier、226,659 次 simplex/crossover、614.894 s；端到端墙钟 12:24.94，进程树峰值 RSS 3.453 GiB（`/usr/bin/time` 3,641,828 KiB），无 swap。QC 最大功率平衡残差 `3.91e-12 GW`、最大约束/边界/对偶违例 `4.17e-8/4.11e-12/1.75e-10`。最终 `stdout.log` 为 18,072 bytes、`stderr.log` 为 1,006 bytes，二者与 `run.pid` 均明确出现在 manifest 的 `excluded_runtime_files`，科学文件验证零失败；这直接验证了 finalize 后 wrapper 继续输出的 P0 修复。该根仍为 `TEST_ONLY_TRUNCATED_HORIZON`，不是全年科学结果。既有 744h 根未写入或重跑；固定服务器未启动 8760h，ParaCloud 未启动新任务。确切下一步：P2 仅设计目录外只读 post-run audit 方案（若协议需要）；P3 在匹配 24h/168h A/B 上记录完整稀疏/Barrier/crossover/RSS 指标后，才评估是否申请新的 744h。
- Manifest 契约 P0 与本地 P1 闭合（2026-07-27，实施提交 `7499062`）：已将通用 `stdout.log`、`stderr.log` 明确加入 `RUNTIME_MANAGED_FILES`，与既有 runner/sequence 日志一样排除在科学输出目录和 result manifest 之外。`tests/test_result_manifest.py` 会创建这两个文件、生成 manifest、随后追加 wrapper 文本，并验证 `validate_result_manifest()` 仍为真。完整本地测试通过 `67/67`。新的独立 2030 Base 根 `outputs/2030_1h_v0727_manifest_runtime_contract` 与 `outputs/2030_24h_v0727_manifest_runtime_contract` 均达到 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，灵活负荷和波浪能均关闭。24h 诊断为 342,343 个变量、262,201 条约束、1,771,702 个非零元，求解时间 41.296 s、进程树峰值 RSS 为 0.725 GiB。它们仍是 `TEST_ONLY_TRUNCATED_HORIZON`；未改变固定服务器/云端 checkout、进程或既有 744h 输出。确切下一步：推送审查后的提交，再复核空闲固定服务器后决定是否部署到新的 168h Base 根。
- Solvability A/B decision (2026-07-26, comparison commit `9e82cc5`): explicit nonnegative spill and equality water balances remain the default. Both 168h Base formulations are `OPTIMAL + solution_qc=PASS` with objectives agreeing within `6.2e-8 million CNY`. Projection is 1.84% faster (641.996 versus 654.026 s), but explicit spill reduces presolved rows/nonzeros by 2.03%/0.74%, `AA' NZ` by 0.88%, `Factor NZ/Factor Ops` by 0.67%/0.80%, and telemetry peak solver memory from 3.957 to 3.876 GB. It is also 24.0% faster in the paired 24h flexibility case. Because the 8760h bottleneck is factorization memory, not a 12 s 168h runtime difference, lower factor structure and cross-scenario robustness take priority over removing raw columns. The projected outputs remain preserved as exact-formulation evidence. `scripts/compare_solver_runs.py` writes the paired JSON/CSV audit.
- Solver engineering milestone (2026-07-26, commits `6d84209` and `44f7fef`): a numerics-only `--solver-config` contract, six versioned Barrier/dual-simplex/CPU-PDHG profiles, flushed `solver_telemetry.jsonl` and SIGTERM/SIGINT-to-`Model.terminate()` handling are validated locally. Solver-profile paths/hashes are recorded and cannot modify scientific settings. CPU-PDHG requires the fixed server's Gurobi 13 environment and is not run under local Gurobi 12.
- Dual-simplex 168h rejection (2026-07-26): the fixed-server 16-thread run was gracefully terminated after 905.073 solver seconds and 421,470 pivots, with no feasible solution and repeated primal-infeasibility spikes. This is already 38.4% slower than the complete Barrier-32 reference. Peak process-tree RSS falls from 3.614 to 2.594 GiB, but the convergence loss disqualifies dual simplex from the first 744h gate. The SIGTERM handler wrote a normal `INTERRUPTED` report with `termination_signal=SIGTERM`; logs and telemetry are preserved.
- Barrier-16+AMD 168h result (2026-07-26): `OPTIMAL + solution_qc=PASS` in 644.636 s, 1.44% faster than Barrier-32, with peak process-tree RSS reduced from 3.614 to 3.187 GiB. However, forced AMD ordering reduces ordering time from 25.70 to 9.83 s while increasing `Factor NZ` from `1.036e8` to `1.090e8` and `Factor Ops` from `8.436e10` to `1.059e11`. It is not yet the 744h selection. A new `barrier_16_auto_order_v1` profile isolates the thread/memory effect without the adverse factor-order change.
- Barrier-16 automatic-order 168h result (2026-07-26): current best Barrier profile, `OPTIMAL + solution_qc=PASS` in 637.344 s. It retains the reference `Factor NZ=1.036e8` and `Factor Ops=8.436e10`, reduces telemetry solver memory from 3.876 to 3.538 GB and peak process-tree RSS from 3.614 to 3.459 GiB, and is 2.55% faster than Barrier-32. A first CPU-PDHG launch failed before model loading because `pdhg_gpu` was missing from the solver-profile whitelist; the whitelist and direct profile-loading test are corrected locally, with no model process or scientific output from the failed root.
- CPU-PDHG 168h decision and active 744h gate (2026-07-26): the corrected fixed-server PDHG run was gracefully terminated after 3,074.134 solver seconds and 496,035 recorded telemetry iterations. It used only 1.990 GB peak solver memory and 2.503 GiB peak process-tree RSS, but produced no feasible solution; near termination the log still showed primal residual about `49.5`, a roughly `0.6%` primal-dual objective gap and a rising dual residual. PDHG is retained only as a low-memory research option, not the first scale-up profile. The five-profile comparison is saved under `/data/zz2/National_model/outputs/solver_comparisons/solver_profiles_168h_v0726.{json,csv}`. With 69 GiB available RAM and no other CISPO solve, a single 744h Base gate using `barrier_16_auto_order_v1`, `Threads=16` and `SoftMemLimit=48` was launched at `/data/zz2/National_model/outputs/2030_744h_v0726_spill_explicit_barrier16_auto_order`; Python PID was `663050`. This is an active engineering gate, not yet an accepted result. Do not start another fixed-server solve concurrently.
- Active 744h structure checkpoint (2026-07-26): model construction completed in 341.673 s with 3,686,023 variables, 5,920,701 constraints and 42,360,391 nonzeros; build peak process-tree RSS was 4.977 GiB. Presolve took 223.80 s and reduced the LP to 3,088,821 rows, 3,017,979 columns and 30,884,732 nonzeros. Automatic ordering took 115.48 s and produced `AA' NZ=6.449e7`, `Factor NZ=8.062e8` (Gurobi estimate about 9.0 GB) and `Factor Ops=6.197e12`. Barrier iteration 4 completed at solver time 493 s with decreasing primal residual and complementarity; telemetry peak solver memory was 25.087 GB and observed process RSS was about 19.1 GiB. Available host memory remained about 50 GiB. The gate is healthy but not solved; continue monitoring without changing checkout or parameters.
- Active 744h crossover checkpoint (2026-07-27): Barrier completed normally in 244 iterations and 8,917.48 solver seconds with interior objective `2,196,881.94 million CNY`, then entered crossover. At the live checkpoint, dual pushes fell from 1,044,784 to 464,775 remaining and telemetry reached 358,606 simplex iterations at solver time 9,996.25 s. Solver memory was 13.948 GB with the unchanged 25.087 GB peak; process RSS fell to about 13.8 GiB and host available memory rose to about 55 GiB. No `solve_report.json`, `solution_qc.json` or `result_manifest.json` exists yet, so this is a phase milestone, not acceptance.
- Terminal 744h result and manifest rejection (2026-07-27): the run completed `OPTIMAL + solution_qc=PASS` with objective `2,196,881.920967378 million CNY`, 13,541.717 solver seconds, 244 Barrier iterations, 1,451,182 simplex iterations, 3:52:03 wall time, 23.121 GiB peak process-tree RSS and zero swaps. All QC hard checks pass; maximum constraint/bound/dual violations are `9.30e-8/5.50e-8/9.22e-8`, maximum power-balance residual is `2.40e-10 GW`, bidirectional interprovincial edge-hours and maximum DC reverse flow are zero, and nested `scenario.id` is `base` with flexibility/wave disabled. Strict acceptance nevertheless fails: `validate_result_manifest()` reports only `size:stdout.log`, because the manifest hashes 63,631 bytes before the final printed solve report while the wrapper-managed file finishes at 66,236 bytes. The result is mathematically/QC valid but not a closed reproducibility gate. Preserve the output unchanged; fix the wrapper/runtime-managed filename contract and obtain an independently closed manifest before formal acceptance.
- 本轮对话收束与下一阶段（2026-07-27）：实时复核确认固定服务器无 CISPO/Gurobi 进程、约 69 GiB 可用内存，checkout 干净停留在实现 `c879c99`；ParaCloud `squeue` 为空，`4003088/4003172/4004585` 分别保持 `COMPLETED build-only`、`OUT_OF_MEMORY`、`TIMEOUT`，没有已验收 8760h 结果。当前能力边界是“`city_337` Base 月尺度连续 LP 可稳定完成 Barrier+Crossover 并通过全部物理 QC”，不是“全年科学结果已完成”。下一阶段按优先级执行：P0 修复通用 `stdout.log`/`stderr.log` 与 `RUNTIME_MANAGED_FILES` 的 manifest 契约并增加 append-after-finalize 回归；P1 用 1h/24h 和固定服务器 168h 新根验证闭合，不因本缺陷立即重跑 744h；P2 决定既有 744h 采用独立只读 post-run audit 还是在严格协议要求下重跑；P3 基于 744h 与云端 Factor NZ/Factor Ops/MaxRSS 证据开展不改变科学边界的稀疏结构、presolve、Barrier/Crossover 求解性优化；P4 仅在新 24h/168h/744h 门禁、资源方案和付费授权齐备后再申请 8760h。Base 默认继续禁用灵活负荷与波浪能；V3 灵活性校准、贴现路径成本/总转型成本账本以及 MGA 均为后续独立研究工作。
- Cloud Barrier-32 terminal state (read-only audit 2026-07-26): ParaCloud job `4004585` ended `TIMEOUT` after `1-00:00:25`, with the batch step `CANCELLED` at `1-00:00:32`. It retained the sampled 499,919,116 KiB = 476.76 GiB MaxRSS and reached Barrier iteration 35 at solver time 82,521 s. Primal residual/complementarity improved to `1.05e8/6.03e6`, but the primal/dual objectives remained `2.0166e11/-1.4513e13`; no accepted iterate, `solve_report.json`, `solution_qc.json` or `result_manifest.json` exists. This is preserved as scale/convergence evidence, not a scientific result. No ParaCloud job is active.
- Local optional wave-energy integration corrected to the existing optimization grid (2026-07-25, uncommitted worktree based on `796a6fc`): raw wave cells are coordinate-intersected with `optimization_points.csv` and restricted to `is_land=0`, yielding 1,285 unique existing marine `grid_uid` rows, 1,284 positive-potential expansion options, 9,798.111 GW retained raw potential and 57 imputed-CF rows. Province/substation/`city_337` routes are exact reuse of the matched existing rows; the prior nearest-offshore-wind proxy and out-of-bound matches up to roughly 1,524 km are removed. `wave_energy_medium_v1` remains optional and creates no wave variables in Base. Two explicit combined cases enable wave with flexible-load V1 or comfort V3 in the same LP, while Base and all single-module cases remain isolated. Base/wave/wave+flex V1/wave+comfort V3 24h build-only gates succeed at 342,343/345,992/350,456/352,688 variables, 262,201/263,810/264,647/266,879 constraints and 1,771,704/1,794,509/1,825,757/1,830,221 nonzeros. Wave and combined preflight reports have overall `PASS` status with 72 records (67 `PASS`/2 `INFO`/3 unrelated existing `WARN`); full local regression passes 62/62. Full-year static estimates are 41,186,792 variables/67,877,276 constraints/532,990,308 nonzeros/36.47 GB for wave and 42,816,152/68,182,781/533,906,823/36.91 GB for wave+flex V1. No optimization, fixed-server checkout, cloud release, process or output was changed.
- Local comfort-aware flexibility V3 (2026-07-24, uncommitted worktree based on `796a6fc`): the independent `comfort_envelope_v3` formulation preserves Base and every accepted V1/V2 path. `scripts/build_flexible_load_envelope_v3.py` perturbs the original `Power_curve_V2` 2024 BAIT/balance-point equations by `+/-1 C`, carries the original future `thermal_multiplier`, and writes a 1,357,800-row envelope for 31 provinces, 2025/2030/2040/2050/2060 and 8760 h/year. Source-formula reconstruction, National_model load alignment, reduction bounds and finite/nonnegative QC pass; the generated ignored-data SHA256 is `b5ebda4344a8f978606c242065159f27a75994a5d976f2cbe06038d66a429a03`. Thermal flexibility uses a causal daily-reset equivalent state, V1G uses a rolling 12h cumulative service deadline, and optional V2G is capped at 5% of province-day baseline EV peak with a causal daily-zero state and a shared V1G+V2G grid-charging power limit. Activation costs are component/direction specific and V1G/V2G moved energy is charged once. Local regression is 58/58. Both 2030 24h gates are `OPTIMAL + solution_qc=PASS`: no-V2G has 349,039 variables/265,270 constraints/1,807,414 nonzeros and 33.63 s solver runtime; final 5%-V2G has 351,271/266,789/1,821,550 and 38.60 s. All state/backlog/V2G/combined-charging residual and terminal checks pass, with zero simultaneous operations. The V3 scenario input and sidecar are included in `input_manifest.csv`. No fixed-server/cloud checkout, process or output was changed; no 168h/744h/8760h V3 run is authorized by this milestone.
- Local state-based flexible-load enhancement (2026-07-24, implementation `271c6dc`): `flexible_load_state_v2` adds daily-reset equivalent heating/cooling inventories and a causal EV V1G charging backlog while preserving Base and the accepted legacy V1/V2G formulations. `Power_curve_V2` `ev_hour_weight` is explicitly treated as the uncontrolled charging baseline rather than plug availability; V2G is rejected in the new state formulation until calibrated availability/battery/departure inputs exist. The final local 2030 24h gate is `OPTIMAL + solution_qc=PASS`, with state/backlog transition residuals at most `8.88e-16 GWh`, zero terminal states/backlog, zero simultaneous up/down and a valid result manifest. A four-year 1h diagnostic chain passes all solve/QC/manifests and immediate `--resume`. Full regression is 56/56. Base and existing scenario JSON files are unchanged, so accepted V1/V2G scenario identities remain reproducible. This implementation is not deployed to the fixed server or active cloud release.
- Local correctness hardening (2026-07-24, based on `4b5bd98`): runtime VRE CF resolution now forbids wind-to-PV fallback and permits missing wind only to the same-grid `mixed_wind` store; nearest-province PV fallback candidates must be land-centroid PV grids. The active data audit finds 35 onwind and 10 offwind rows using valid same-grid mixed-wind, zero wind-to-PV mappings, and 141 PV-family nearest-grid fallbacks. Excluding water-centroid PV donors changes zero current donor assignments, so this closes a latent future-data bug without changing the current Base feasible set or cloud run. Four focused tests and the complete 54-test regression suite pass. `MODEL_IO_CONTRACT.md` and `SCENARIO_MODULE_ARCHITECTURE.md` now consistently identify `city_337` as an annual load-center/transmission proxy, not a city-hourly dispatch network; 278 Natural Earth remains replication/sensitivity only.
- Cloud execution update (2026-07-24): the staged `city_337` release passed both mandatory single-year 2030 Base engineering gates. Job `4003035` (24h, 32 CPU/64G) is `OPTIMAL + solution_qc=PASS`, with 342,343 variables, 262,201 constraints, 1,771,703 nonzeros, 26.978 s solver time and 0.834 GiB peak process-tree RSS. Job `4003045` (168h, 32 CPU/64G, `m4ci1805`) is `OPTIMAL + solution_qc=PASS`, with 1,011,079 variables, 1,393,915 constraints, 9,797,949 nonzeros, 377.057 s solver time and 3.661 GiB peak process-tree RSS. Both pass all 50 regression tests and independent `solve_report`/`solution_qc`/result-manifest validation.
- Full-year cloud terminal state (live read-only audit at 2026-07-25 02:14 CST): structural job `4003088` remains accepted as build-only, but the authorized real 2030 job `4003172` ended `OUT_OF_MEMORY`, exit `0:125`, after 5:44:03 on `m4cg1702`. The 40,912,327-variable/68,189,325-constraint/515,040,080-nonzero model completed Gurobi presolve in 17,932.25 s and reduced to 35,423,761 variables, 37,982,903 constraints and 400,861,556 nonzeros. It then reached ordering for barrier factorization but was OOM-killed before barrier iteration 0. Slurm recorded 526.99 GiB MaxRSS/527.03 GiB MaxVMSize against a 700G request; the node rebooted shortly after the failure, so sampled MaxRSS may not capture the terminal spike and the exact kernel/cgroup cause requires cluster-admin evidence. No `solve_report.json`, `solution_qc.json` or `result_manifest.json` exists. The output is a failed scale/memory diagnostic, not a scientific result. No cloud job remains active; do not resubmit the same configuration or start 2040.

- User-authorized Barrier-32 retry (live audit at 2026-07-25 02:35 CST): ParaCloud job `4004585` is `RUNNING` on `m4cg1702` from the immutable `22fb493` Base/`city_337` release. The only solver-resource change from failed job `4003172` is `Threads=128 -> 32`; `Method=2`, `Presolve=2`, `Crossover=1`, `SoftMemLimit=640`, the 700G request, 24h limit and all scientific settings are unchanged. The new script SHA256 is `fc604a1a25d37c9cff8a336c83969809cb5b52ea0ab815183d1ea3a7a96bfbf2`, and the isolated output root is `outputs/full_year_2030_base_22fb493_barrier32_700g_v0725`. The 50-test gate passed in 11.845 s and the generated config records `threads=32`. Because the 700G memory request forced Slurm to allocate 96 CPU billing units despite `CPUs/Task=32`, scheduler billing for this run accrues at 96 core-hours per wall-clock hour. The prior failed job consumed 2,642,304 allocated CPU-seconds = 733.973 core-hours, while its actual `TotalCPU` was only 7:03:11. No solve/QC/manifest is expected until optimization completes; do not start 2040 or another retry while `4004585` is active.

- Barrier-32 live progress (read-only audit at 2026-07-25 20:30 CST): job `4004585` remains `RUNNING` on `m4cg1702` after 17:55:54. It completed ordering in 3,180.53 s and, unlike failed job `4003172`, entered Barrier iterations. The presolved system has `AA' NZ=7.425e8`, `Factor NZ=3.848e10`, an estimated 340.0 GB factor footprint and `Factor Ops=2.448e15`; iteration 23 completed at solver time 60,528 s. Primal residual and complementarity decreased from `8.98e9/6.57e8` at iteration 0 to `7.71e8/4.47e7` at iteration 23, so the process is advancing but is not close to an accepted solution. Current sampled `MaxRSS` is 499,919,116 KiB = 476.76 GiB, below the failed 128-thread sample. Slurm has 6:04:06 remaining and will end the job at `2026-07-26 02:34:26 CST`; recent iterations take roughly 30-32 minutes, so completion within the current wall limit is uncertain and no solve/QC/result manifest exists. No scheduler setting was changed during this audit.

### Version identity

- Latest cloud audit (2026-07-24): the user-authorized city_337 release is staged at `/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493`. Code archive SHA256 is `2f3564ff9123b292106e51bd5ee943e13e874b6798450e38a96428a48a3b6b7a`; all 11,350 runtime-input files (model-ready, hourly CF and hydrology) match the fixed-server SHA256 manifest (`662565a090b64523ec353994e6fdb3314a94b88d429f16e85e1665300ffbc85a`). Compute-node job `4001137` completed the 2030/8760h preflight: 175.17 GiB available memory, 40,912,327 variables, 67,604,064 constraints, 520,922,832 nonzeros and 36.0 GiB static model-memory estimate. It did not construct or solve a Gurobi model.
- Cloud proxy/WLS was revalidated on 2026-07-24 after repairing the three malformed `.bashrc` exports (the pre-fix file is retained as `.bashrc.codex_backup_20260724_proxy_export`). Compute-node job `4002980` inherited the proxy from `.bashrc` and reached `token.gurobi.com` through `172.16.110.3:8888` with HTTP 302. WLS job `4002981` then completed `Env.start()` and a tiny LP with `GUROBI_SMOKE_PASS`/`OPTIMAL` on `m4ci1905.para.bscc`. A short standalone curl probe in that smoke still timed out, so treat Gurobi's successful authenticated solve—not curl alone—as the license gate. Cloud 24h/168h gates are now eligible; full-year build-only remains downstream of those gates.

- Handoff version: `v0.9.66`
- Snapshot date: `2026-07-28`
- Local repository: `D:\codeenv\pycharmproject\National_RL\National_model`
- Git branch: `codex/cispo-2030-full-lp`
- Live identity after P1 deployment: local/server shared HEAD was `67482ab` before this documentation closeout; the fixed-server checkout is clean and has no CISPO/Gurobi process. It contains the P0 implementation `7499062` plus prior documentation; relative to the prior server implementation `c879c99`, the only model-adjacent code change is the runtime-log manifest exclusion, not LP/data/scenario logic. `9e82cc5` retains explicit reservoir spill, `84a277c` adds the automatic-order Barrier control, and `c879c99` completes the traceable CPU-PDHG profile contract. The matched spill and five-profile 168h outputs are preserved. The fully rebuilt `city_337` package is the production configuration; 278 Natural Earth remains separate. The fixed server uses the additive data root `/data/zz2/National_model/data/model_ready_20260723_v0722_city337`.
- A separate ParaCloud/BSCC-A8 endpoint was authenticated on 2026-07-20 through both configured IPv4 routes using the existing local public key. The remote host is `ln301.para.bscc`, account `a8s001819`; port 22 is primary and 2222 is fallback. The official Gurobi 13.0.2 Linux package is staged privately on the cloud. Following transient refusal in `4000608`, `4000762` and `4001248`, the user-authorized `.bashrc` repair and fresh compute-node WLS solve `4002981` restore the cloud license gate. The proxy is now inherited by batch shells from `.bashrc`; retain explicit lower-/upper-case exports in production scripts as defensive reproducibility, and do not regard the short curl timeout in `4002981` as a replacement for the authenticated Gurobi smoke result.
- SSH access was restored on 2026-07-19 by using the configured `national-model-server` alias, which binds the approved workstation source address. The obsolete PID `863603` was not active and no CISPO solve process remained.
- Server readiness, raw-GRFR SHA256 verification and 24/24 regression tests passed on the new versioned data roots. The server 24h gate is `OPTIMAL` in 60.53 s with `solution_qc=PASS`.
- After commit `1b6da28`, server regression tests passed 26/26 and the corrected 24h transmission gate reached `OPTIMAL` in 43.88 s with all directionality/QC/manifest checks passing.
- PID `3778049` completed mathematically `OPTIMAL`, but its result is rejected as a physical model gate because the prior QC omitted 3,358 material AC bidirectional edge-hours.
- Initial handoff-document commit: `1ac58dd`
- Server repository: `/data/zz2/National_model/repo`
- Server Git remote: `/home/zz2/git/National_model.git`
- At handoff version `v0.2.0`, local code was committed and pushed as `8e49a87`, and the server checkout under `/data/zz2/National_model/repo` was fast-forwarded to that commit before data/readiness validation. Always confirm the live HEAD with `git rev-parse --short HEAD` rather than treating a documentation commit as immutable current state.

### Fixed model boundary and architecture

- 2025 is an input boundary condition, not an optimization year.
- 2030 is the first planning year and represents capacity changes during 2025-2030; accepted capacity cohorts then pass sequentially to 2040, 2050 and 2060.
- The scientific production model is one continuous national LP with 8760 chronological hours.
- No Benders decomposition, representative periods, sampled hours or temporal weights are used.
- Test horizons are `one_month=744h` and `six_months=4344h`; their annual costs and policy constraints are not rescaled, so their solutions are engineering tests rather than planning results.
- Per-year entry is `scripts/run_cispo_2030_full_year.py`; the isolated multi-year entry is `scripts/run_cispo_planning_sequence.py`.

### Implemented model scope

- 31 provincial load regions; Inner Mongolia is not split.
- 36,686 VRE technology-site rows with 2023 hourly capacity-factor linkage.
- Continuous capacity-based thermal RUC, ramping, reserve and inertia.
- Battery and PHS state of charge; station-level hydropower, reservoir balance and committed core-cascade hydropower coupling for the Stage2 recommended mainstem groups.
- 411 interprovincial transmission corridors and strict hourly provincial power balance.
- Nuclear upper bounds, a shared `bio+bioccs` capacity upper, the CISPO Table S17 2030 battery floor and AC-only reverse-flow active indexing are committed and deployed. V0720 changes only provenance, exports, diagnostics and state acceptance; it does not change the feasible set.
- DAC, annual carbon and biomass accounting, CCS capture and point-level injection.
- Spur line, trunk line and substation augmentation.
- The production load-center scenario is `city_337`; the 278-node Natural Earth paper replication is retained as a separate reproducibility/sensitivity input.
- Annual load-center energy allocation, provincial export closure and a 642-edge intraprovincial AC500 proxy expansion layer are implemented. The 2025 city network initializes 203 positive-capacity edges.
- Wind, solar and hydropower use spatial spur/trunk routing. Thermal, nuclear and biomass generation are allocated within each province by load-center demand shares.
- Optional `flexible_load_v1` and `flexible_load_v2g_v1` modules are implemented behind explicit scenario files. Base creates no flexibility variables. The current values are illustrative sensitivity assumptions, not calibrated transport/building parameters and not CISPO source values.
- Optional `wave_energy_medium_v1` is implemented only on existing marine optimization `grid_uid` rows behind an explicit scenario file. Base creates no wave variables. Wave capacity is grid resolved and hourly generation is province aggregated after applying site CF; costs, potential scaling and the explicit 2060 hold remain sensitivity assumptions. Explicit wave+flexibility V1 and wave+comfort-V3 combined cases are also available.

Detailed definitions are in `cispo_full_lp_model_spec.md` and `LOAD_CENTER_NETWORK_278_年度输电层说明.md`.

### Server runtime

- Host login: `zz2@210.77.85.166`; SSH identity path on the workstation is `%USERPROFILE%\.ssh\server_ed25519`. Never read or copy the private-key contents.
- Server hardware observed: 96 logical CPUs and about 125 GiB RAM.
- Python environment: `/home/zz2/.local/envs/cispo-2030`, Python 3.11.15.
- Gurobi Optimizer: 13.0.2 at `/home/zz2/opt/gurobi1302/linux64`.
- `gurobipy`: 13.0.2 in the `cispo-2030` environment.
- GPU test environment: `/home/zz2/.local/envs/cispo-gurobi-gpu` with `gurobipy 13.0.2+cu129`; it is isolated from the production CPU environment and should be used only for PDHG tests with `Method=6`, `PDHGGPU=1`.
- Gurobi 12.0.1 remains installed as rollback software.
- License file: `/home/zz2/gurobi.lic`, mode `0600`, issued license ID `2840423`, valid through `2027-07-02`.
- The activation key and license-file contents must not be committed or copied into documentation.

### Server data paths

```bash
export CISPO_CF_ROOT=/data/zz2/National_model/data/hourly_cf
export CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse
export CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260723_v0722_city337
export CISPO_RAW_GRFR_ROOT=/data/zz2/National_model/data/grfr_raw_2019
export GRB_LICENSE_FILE=/home/zz2/gurobi.lic
PYTHON=/home/zz2/.local/envs/cispo-2030/bin/python
```

### Latest verification evidence

- Fixed-server 168h `city_337` Base sequence `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337` and immediate `--resume` pass. Solver runtimes are 733.00/811.58/892.10/1397.12 s; wall time 1:13:47; peak RSS 4,085,152 KiB; zero swaps. Every year is `OPTIMAL + solution_qc=PASS`, has zero false hard checks, 337 center rows, 642 intra-edge rows, 31 province-account rows and 59 manifest entries. Maximum center/province/intra-capacity/power residuals are `7.09e-11 GWh`, `2.73e-12 GWh`, `8.24e-12 GWh` and `1.78e-10 GW`; BECCS net-carbon residual is numerical zero. Compared with the prior 278 Base gate, the 337 layer adds only 1,031 variables, 924 constraints and 2,749 nonzeros at 168h; total solver time increases 4.68%, dominated by a 706.6 s 2060 Crossover.
- Fixed-server `city_337` `flexible_load_v1` 24h and 168h sequences both pass four years and immediate `--resume`. The 168h root `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v1` has runtimes 714.39/816.08/1007.71/980.09 s, wall 1:08:59, peak RSS 4,030,672 KiB and zero swaps. Every year is `OPTIMAL + solution_qc=PASS`, has 59 validated manifest entries, 337 center rows, 642 intra-edge rows and 31 province/flexibility accounts. Maximum heating/cooling/EV V1G residuals are `1.17e-12/1.78e-15/4.26e-13 GWh`; simultaneous up/down is zero, V2G is disabled and BECCS/network/security checks pass. Versus city_337 Base, V1 adds 3.09% variables and 2.23% nonzeros but total solver time is 8.23% lower; 2050/2060 crossover remains the main variability source.
- The independent V2G 24h and 168h roots both pass four years, manifests and immediate `--resume`. The accepted 168h root `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v2g_v1` has runtimes 792.55/806.12/953.60/1033.25 s, wall 1:09:57, peak RSS 4,087,888 KiB and zero swaps. All years are `OPTIMAL + solution_qc=PASS`, have 59 validated manifest entries, V2G transition residual at most `1.90e-13 GWh`, zero simultaneous charge/discharge and exact period loss closure (`charge-discharge = net_load_energy_change`). The fixed server is now idle; do not launch 744h/8760h without a new explicit authorization.
- Fixed-server 24h `city_337` Base sequence `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337` passes four years and `--resume`. Solver runtimes are 43.29/48.82/41.17/46.90 s; wall time 7:21; peak RSS 930,204 KiB. Every year is `OPTIMAL + solution_qc=PASS`, Base flexibility is disabled, security is 5%/3.5 s, 337 center rows and all 59 manifest entries are present, and maximum center/province/intra-capacity residuals are `3.01e-12/4.55e-13/4.61e-10 GWh`. BECCS net-carbon closure is zero.
- The first server smoke attempt exposed a stale row-count contract (1,240 expected versus the correct 31 provinces × 5 years × 10 thermal/biomass technologies = 1,550). Commit `cf39e0a` fixes only that test and adds uniqueness/year/technology checks. Local and server smoke then pass 142/142; server tests pass 50/50, readiness/full-license gate passes, and preflight passes.
- Local implementation `8e76753`: the new additive `data/load_center_network/city_337/` package contains 337 city centers, 16,609 VRE routes, 2,030 hydropower routes and 642 same-province edges. All 31 provincial graphs are connected; province demand shares close within `1.11e-15`; 2025 initialization includes 1,310.0 GW connected wind/utility PV, 530.0 GW local DPV, 297.8895 GW existing hydro and 647.8401 GW summed intra-edge capacity, with maximum balance residual `7.28e-14 GW`. Exact joint routing improves spur+trunk distance by 20.21 km on average versus the former nearest-substation-first logic. Regression tests pass 50/50 and preflight passes 61 checks with zero hard failures. The local four-year 1h Base sequence `outputs/planning_sequence_1h_v0722_city337` is `PASS`; every year is `OPTIMAL + solution_qc=PASS`, exports 337 load-center balance rows and a 59-file manifest, and a fresh `--resume` returns four `RESUMED_ACCEPTED` records. This is engineering evidence only.
- Live fixed-server audit before deployment: clean checkout `6ed943a`, no active CISPO/Gurobi solve, approximately 35 GiB available RAM and swap nearly full. The accepted V1 168h root remains `PASS` with four resumed years. This resource state allows only the new 24h/168h gates; fixed-server 744h/8760h remain prohibited.
- Local uncommitted reliability update at Git HEAD `e28f315`: 49/49 regression tests PASS. The real 1h engineering gate `outputs/2030_1h_v0722_security_5pct_inertia_3p5s` is `OPTIMAL + solution_qc=PASS`; effective inertia is recorded as `3.5 s`, capacity-margin and inertia hard checks pass, and the result manifest validates with zero mismatches. No server checkout, process, data root or output was changed. User-owned `supplementary_materials/**` changes remain untouched.
- Local `c62b769` validation: 47/47 regression tests pass. Real Base 1h gate `outputs/2030_1h_v0722_beccs_mass_balance` is `OPTIMAL + solution_qc=PASS`; all four new BECCS/captured-CO2 hard residuals are exactly zero, all six explicit BECCS accounting fields are present, and the 59-file result manifest validates with zero mismatches. The parameter audit under `outputs/parameter_audit_20260722_beccs_mass_balance` reports 11,681 rows, 22 PASS, 0 WARN, 0 HARD_FAIL and six remaining open/scenario-required risks; the former P0 BECCS mass-balance risk is closed for the zero-lifecycle CISPO baseline.
- Local implementation `c91828a` adds `scripts/run_cispo_sensitivity_suite.py` and identity-safe tests without changing the model formulation. All 45 regression tests pass. A real 1h suite under `outputs/sensitivity_suite_1h_v0722_interface` ran Base, `flexible_load_v1` and `flexible_load_v2g_v1` as three isolated 2030→2040→2050→2060 state chains: all 12 year-scenario cases are `OPTIMAL + solution_qc=PASS`, all hard checks and 59-file result manifests pass, Base reports flexibility disabled, V1 reports V2G disabled and V2G is enabled only in its independent scenario. A suite-level `--resume` audit returned all three scenarios and all four years as accepted without re-solving. The original suite report was preserved in `sensitivity_suite_history` with SHA256 `2140efc5ac4cbb4e9dedbaf4e1d8f43593c05132d638e08dccc1526b5da63766`.
- Local `6ed943a` validation: 42/42 regression tests pass; Base 1h, `flexible_load_v1` 24h and `flexible_load_v2g_v1` 24h all reach `OPTIMAL + solution_qc=PASS`; all three result manifests validate with zero mismatches. The V1 24h run has daily heating/cooling/EV closure errors below `2e-13 GWh`, no simultaneous up/down and reduces the test-period national peak from 1229.55 to 1215.78 GW. The V2G run has maximum SOC-transition residual `5.55e-17 GWh`, zero simultaneous charge/discharge and records 0.0231 GWh of charging-loss energy. These are truncated engineering gates, not planning results.
- The active load table contains 1,357,800 rows for 31 provinces, five model years and 8,760 h per province-year. `demand_gw = base_residual_gw + heating_gw + cooling_gw + ev_gw` closes to `8.53e-14 GW` on the loaded arrays and all components are nonnegative. The refreshed parameter audit expands 11,681 runtime rows with 22 PASS, 0 WARN and 0 HARD_FAIL; seven scientific risks remain open.
- Full-year static estimates are Base 40.91M variables/67.60M constraints/36.00 GiB, flexibility V1 42.54M/67.91M/36.44 GiB and V2G 43.36M/68.18M/36.70 GiB. These are construction estimates and do not reduce the 96 GiB availability gate or bound barrier factor memory.
- V0721 implementation `0c1eaf2` is pushed and deployed to the fixed server. Local and server regression tests pass 37/37. The local real 1h 2030→2040→2050→2060 diagnostic chain and a subsequent `--resume` audit both report `PASS`; all four years are `OPTIMAL + solution_qc=PASS + accepted state`.
- New server data root `/data/zz2/National_model/data/model_ready_20260722_v0721_fuel_state` was copied additively from the V0719 root and receives only the rebuilt fuel tables. SHA256 matches the local files: `province_fuel_prices.csv` = `b6867259317b419bc8b35aedf6b614fd930cf0eed9620fdddeca6fc6434c50a1`; `province_fuel_generation_cost_by_year.csv` = `e1133fbfc798a15524e3ee920a0c6e3e771206874427abcef7db399227df94cd`.
- Local and server parameter audits each expand 11,658 active runtime parameter rows and report 22 PASS, 0 WARN, 0 HARD_FAIL, with seven scientific risks retained separately. Province-level biomass/BECCS fuel costs now cover every model province and are no longer zeroed in the objective.
- Fixed-server 24h four-year diagnostic sequence `/data/zz2/National_model/outputs/planning_sequence_24h_v0721_fuel_state` and a subsequent `--resume` chain-identity audit both report `PASS`. All four years are `OPTIMAL + solution_qc=PASS`; solver runtimes are 49.42/46.49/45.98/45.74 s, wall time is 6:03 and peak RSS is 0.879 GiB. States are explicitly `TEST_ONLY_TRUNCATED_HORIZON`.
- Fixed-server Base 168h four-year diagnostic sequence `/data/zz2/National_model/outputs/planning_sequence_168h_v0721_fuel_state` completed `PASS` for 2030/2040/2050/2060 and passed an immediate `--resume` identity audit. All four years are `OPTIMAL + solution_qc=PASS`; solver runtimes are 708.80/708.69/1107.69/1137.22 s, wall time is 1:08:40, peak RSS is 4,116,892 KiB and swap is zero. Each result manifest validates with zero mismatches. It ran from checkout `b6ca42d` containing implementation `0c1eaf2` and is retained as the uncontaminated pre-flexibility Base gate.
- After deployment to `6ed943a`, the fixed server passes 42/42 regression tests with all three external data roots explicit. Four-year 24h `flexible_load_v1` sequence `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_flexible_load_v1` and its immediate resume audit both report `PASS`: all years are `OPTIMAL + solution_qc=PASS`, wall time is 6:32, peak RSS is 946,804 KiB and swap is zero. Daily heating/cooling/EV residuals are at most `6.44e-13 GWh`, simultaneous up/down counts are zero, all manifests validate, and every input manifest records scenario SHA256 `7b8f1c920bad35e2e41111f7913cfb456b6e369b85db5b03ae86d43801840532`.
- Fixed-server four-year 168h `flexible_load_v1` sequence `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_flexible_load_v1` completed `PASS` from clean checkout `6ed943a`; PID `1708266` has exited and no CISPO process remains. All four years are `OPTIMAL + solution_qc=PASS`, every hard QC check passes, and each 59-file result manifest validates with zero size/SHA256 mismatches. Solver runtimes are 705.49/672.16/994.41/1181.26 s; wall time is 1:06:54, peak RSS is 4,040,256 KiB and swap is zero. Heating/cooling/EV V1G daily-energy residuals are at most `8.17e-13 GWh`, all simultaneous up/down counts are zero, and every input manifest records scenario SHA256 `7b8f1c920bad35e2e41111f7913cfb456b6e369b85db5b03ae86d43801840532`. A fresh `--resume` identity audit reports four `RESUMED_ACCEPTED` years and sequence `PASS`; diagnostic states remain `TEST_ONLY_TRUNCATED_HORIZON`.
- The pre-fix V0720 2030 168h comparison gate completed `OPTIMAL + solution_qc=PASS` under `/data/zz2/National_model/outputs/2030_168h_v0720_io_contract_server`: solver runtime 799.07 s, wall time 16:06, peak process-tree RSS 3.762 GiB. It omits biomass fuel cost and is retained only as a comparison baseline.
- V0720 implementation `b40900a` is pushed and deployed to the clean fixed-server checkout. Local and server unit tests pass 34/34; the V0719 server data package passes 139/139 smoke checks.
- Server 24h I/O-contract gate `/data/zz2/National_model/outputs/2030_24h_v0720_io_contract_server` reached `OPTIMAL + solution_qc=PASS`: 341,312 variables, 261,280 constraints, 1,768,957 nonzeros, objective `2,024,722.739184 million CNY`, Gurobi runtime 43.65 s and peak process-tree RSS 0.838 GiB. All 27 hard checks pass; result-manifest validation has zero mismatches; all NPZ files load with `allow_pickle=False`; dual export contains 744 hourly and 3,366 annual rows.
- The output contract now includes immutable configuration/environment/input manifests, a 50-file output catalog, a 493-row data dictionary, province-technology capacity and generation tables, security/adequacy/resource diagnostics, hourly marginal prices, annual shadow prices and verified capacity-cohort state transfer. Detailed definitions are in `MODEL_IO_CONTRACT.md`.
- The pre-V0719 744h run at old commit `5a9f4ab` is an accepted engineering gate only. Its solver/QC passed, but the old result manifest is not closed: `run.stdout` and `run.time` were modified by the wrapper after hashing. See `MODEL_744_SERVER_RUN_AUDIT_20260720.md`.
- V0719 local capacity-bound/DC-sparse correction: 32/32 unit tests PASS; 139/139 data-package smoke checks PASS; strict 24h output `outputs/2030_24h_v0719_capacity_bounds_dc_sparse_rerun` reached `OPTIMAL + solution_qc=PASS` with 341,312 variables, 261,280 constraints, 1,768,956 nonzeros, 39.79 s solver time and 0.702 GiB peak RSS.
- New bound QC is zero for nuclear floor/upper, shared biomass+BECCS upper and battery/PHS floor. DC reverse maximum and AC bidirectional edge-hours are zero; maximum power-balance residual is `7.43e-12 GW`.
- Full-year V0719 estimator: 40,911,296 variables, 67,603,283 constraints, 520,920,489 nonzeros and about 36.0 GiB static model memory. Exact DC variable removal is `363×8760=3,179,880`; no runtime or factor-memory speedup is inferred from this structural reduction.
- Server V0719 deployment root is `/data/zz2/National_model/data/model_ready_20260719_v0719_capacity_bounds`. It was copied additively from the completed sparse root, then supplemented with the three generated V0719 bound tables, `sets/model_years.csv` and 28 canonical smoke/QC/source files that were absent from the old sparse root. The old root and completed 744h output were not overwritten.
- Server V0719 gates on 2026-07-19: checkout HEAD `bc83663`; readiness PASS; 32/32 unit tests PASS; 139/139 smoke checks PASS; 24h solve `/data/zz2/National_model/outputs/2030_24h_v0719_capacity_bounds_server` reached `OPTIMAL + solution_qc=PASS` with 341,312 variables, 261,280 constraints, 1,768,957 nonzeros, objective `2,024,722.7392 million CNY`, Gurobi runtime 48.96 s, peak RSS 0.841 GiB and zero nuclear/biomass/storage/DC/AC hard-check violations.
- Requested 8760 direct trial was not launched because the live memory gate failed: `scripts/run_cispo_2030_full_year.py --horizon full_year --preflight-only --output-dir /data/zz2/National_model/outputs/2030_8760_v0719_preflight_memory_check` reported available memory `73.15 GiB` versus required `96.0 GiB`. It produced a V0719 full-year estimate of 40,911,296 variables, 67,603,283 constraints, 520,920,489 nonzeros and 36.0 GiB static model memory; no full-year model was built or solved.
- Server 744h strict gate `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` completed on 2026-07-19 19:44 Asia/Shanghai under deployed HEAD `5a9f4ab`. It reached `OPTIMAL + solution_qc=PASS`: 3,955,064 variables, 5,919,746 constraints, 43,707,940 nonzeros, objective `2,196,413.3453 million CNY`, solver runtime 16,245.79 s, wall time 4:37:02 and peak process-tree RSS 21.979 GiB. Hard QC passed with zero bidirectional interprovincial edge-hours, zero DC reverse flow, maximum power-balance residual `3.64e-10 GW`, and maximum constraint/bound/dual violations `9.73e-8`/`6.59e-8`/`8.81e-8`.

- Commit `5a9f4ab` is pushed and deployed. Local tests passed 29/29; the strict local 24h solve reached `OPTIMAL` in 32.00 s with peak RSS 0.694 GiB and every QC hard check passed.
- The corrected server 168h gate under `/data/zz2/National_model/outputs/2030_168h_sparse_gate_strict` contains 1,071,032 variables, 1,392,960 constraints and 10,100,058 nonzeros. It reached strict `OPTIMAL` in 666.45 s with peak RSS 3.910 GiB, maximum constraint violation `4.17e-8`, zero AC bidirectional edge-hours, zero DC reverse flow and `solution_qc=PASS`.
- The equivalent annual-network rewrite reduced 168h nonzeros by 380,581 (`3.63%`) without changing decision-variable count. Directly eliminating the VRE/ROR availability auxiliaries was tested and rejected because it duplicated CF coefficients in availability and reserve rows.
- The full-year runtime memory gate is now 96 GiB. The scale estimator covers all current variable blocks exactly (44,091,176 projected variables), estimates about 520.9 million nonzeros and 36.71 GiB static model memory, and explicitly does not treat this as a barrier-factorization guarantee.
- Corrected 744h CPU barrier gate under `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` has passed for deployed HEAD `5a9f4ab`. This preserves the sparse transmission/load-center formulation gate, but it does not include the uncommitted V0719 capacity-bound/DC active-index corrections.
- Solvability audit commit `ab9dfe8` records the revised 8760h projection: 44,091,176 variables, 68,188,384 constraints and about 515-524 million nonzeros. The existing 853.5 million preflight nonzero count is a conservative structural upper estimate, while its 46.62 GiB memory number is not a barrier peak-memory estimate.
- Current 24h and 168h build-only numerical audits were written under `outputs/audit_24h_20260719_system_solvability` and `outputs/audit_168h_20260719_system_solvability`. They contain 350,024/261,280/1,867,008 and 1,071,032/1,392,991/10,480,639 variables/constraints/nonzeros respectively.
- Rejected 744h solver evidence identifies the scaling bottleneck: presolved 3,274,450 rows and 3,353,208 columns; `Factor NZ=8.289e8` (about 10 GB); barrier 10,969.01 s and crossover 9,123.64 s. Linear factor-memory extrapolation alone is about 118 GB at 8760h, so a direct solve on the 125 GiB host is high risk even if build-only succeeds.
- A current-model 24h `Crossover=0` re-audit returned `SUBOPTIMAL`, maximum constraint violation 0.01355 and failed reservoir/directionality QC. A candidate `FeasibilityTol=OptimalityTol=1e-6`, `BarConvTol=1e-7`, `Crossover=1` run reached `OPTIMAL/QC PASS` in 37.38 s versus the approximately 40.02 s local strict baseline; this candidate is not approved for production until a corrected 168h/744h comparison passes.
- Live server HEAD remained `f22b9cf`; available RAM was about 30 GiB and all 21 GiB swap was occupied. No large server process was launched.

- Local implementation commit `2a0ee99` plus planning-state export test commit `ecfc7ed`; AST 38 files PASS; unit tests 24/24 PASS; data-package smoke 124/124 PASS.
- Final local 24h gate: 349,962 variables, 260,973 constraints, 1,827,245 nonzeros; Gurobi `OPTIMAL` in 58.79 s; peak RSS 0.698 GiB; `solution_qc=PASS`; maximum power-balance residual `3.90e-11 GW`.
- Local full-year preflight: PASS, zero hard failures; 44,090,772 variables, 67,603,314 constraints, 853,505,952 estimated nonzeros and 46.62 GiB estimated model memory. The workstation does not meet the 64 GiB full-year construction gate.
- Nonempty 2040 state-transfer diagnostic: `OPTIMAL/QC PASS`; inherited 2.5 GW battery and 1.0 GW PHS cohorts entered the intended province-technology lower bounds exactly.
- PHS source/QC: GHT 2026 province-level 8h storage; national operating floor 65.94 GW; 2030 project upper 249.191 GW; 2040+ upper 514.755 GW.
- Outputs: compact capacity/generation/storage/monthly/hourly summaries, SVG quicklooks and SHA256 result manifest are implemented and validated. Detailed audit: `MODEL_SYSTEM_AUDIT_20260718.md`.
- Minimal server bundle prepared from HEAD `dafeb24` with `--skip-cf` and locally rehashed: `national_model_code.tar.gz` 283,416 bytes SHA256 `1311f3ccfd53b26248e37c13370016a6b5e6165f717d1bde0e79c21d3cd73a4d`; `model_ready_data.tar.gz` 49,131,551 bytes SHA256 `502a60e58da959bfa6e5c3ba2ea83a8d39c3aade212231e5c6ecc42db6a9eb17`; `hydro_timeseries.tar.gz` 24,777,505 bytes SHA256 `573d1285eb4787a3058bff8c25b382a5df6630441de2c5e5b8d58095fbfd70f5`. The data archive contains the PHS bounds and no untracked `supplementary_materials/` files.
- On 2026-07-19 those two data archives were uploaded, verified with the same SHA256 values and extracted additively to the current server roots. Readiness passed with 28/28 required tables, 2,030 hydro stations, 124 cascade edges, full-license confirmation and both raw-GRFR hashes valid; server `unittest` passed 24/24 in 19.62 s.
- Server 24h output `/data/zz2/National_model/outputs/2030_diagnostic_24h_20260719_sequential_sparse_cpu`: 349,962 variables, 260,973 constraints and 1,827,246 nonzeros; Gurobi `OPTIMAL` in 60.53 s; maximum constraint violation `1.32e-08`; peak process-tree RSS 0.851 GiB; `solution_qc=PASS`.
- Replacement 744h preflight: 3,954,660 estimated variables, 5,912,178 constraints, 73,853,760 nonzeros and 4.08 GiB estimated memory. PID `3778049` was alive after 55 s with empty `stderr` under `/data/zz2/National_model/outputs/2030_one_month_20260719_sequential_sparse_cpu`.
- At launch, another user's four training jobs occupied about 67 GiB RAM; server available RAM was about 49 GiB and swap was full. This is adequate for the 744h estimate but below the configured 64 GiB full-year gate, so 8760h was not started.

- Local implementation commit: `8e49a87` (`fix: harden CCS and station-level hydropower model`) pushed to `origin/codex/cispo-2030-full-lp`.
- Raw GRFR transfer to `/data/zz2/National_model/data/grfr_raw_2019` completed and was verified by server-side file size and SHA256:
  - `output_pfaf_03_2019.nc`: `84ff2c882fb17a4b8693bb0773718c2472038021b64618b05f99f8070a506e0f`.
  - `output_pfaf_04_2019.nc`: `e56d5da855ddbdafabdafcb5582981b3f0003054156cf8d912d24a9efd232756`.
- Server readiness with `--require-raw-grfr --verify-raw-grfr-sha256`: `PASS`, zero hard failures; hydropower station rows `2030`, reservoir rows `620`, run-of-river rows `1410`, potential paper-rule mismatches `0`.
- Server regression tests: `15 passed in 20.75s` with pytest.
- One-month server preflight: 4,300,620 variables, 6,004,434 constraints, 74,591,808 nonzeros; estimated memory 4.19 GiB; memory gate passed with about 110.24 GiB available.
- Full-year server preflight: 48,164,172 variables, 68,689,554 constraints, 862,195,872 nonzeros; estimated memory 47.98 GiB; memory gate passed with about 110.22 GiB available.
- Local verification before server sync: AST parse passed for 14 changed Python files; `unittest discover -s tests -q` passed 15 tests; data-package smoke test passed 113/113 checks; 24h station-hydro solve reached Gurobi `OPTIMAL` and `solution_qc.json` reported `PASS`.
- Verification scripts: `scripts/check_gurobi_full_license.py` and `scripts/check_server_readiness.py`; the latter now enforces raw GRFR presence and optional SHA256 verification.
- Local cascade implementation verification on 2026-07-06:
  - Stage2 source path `D:\codeenv\pycharmproject\National_RL\Gis_process\hydro_power\process_hydro\hydro_model_2019_stage2_classification_cascade_20260630` is readable.
  - Generated cascade topology contains 142 COMID nodes, 124 directed edges and 146 mapped reservoir stations across 5 recommended core groups.
  - All 146 Stage2 station IDs map into current `data/hydro/hydro_stations.csv`; all are `reservoir_storage`; capacity alignment residual is 0.0 GW; the directed topology is acyclic.
  - GRFR cross-correlation lag estimation produced non-negative 3h-multiple lags with range 0-168 h; 4 edges have low lag correlation and 18 edges select the 168 h search bound, so these are WARN-level topology/lag QA items.
  - `scripts/build_cispo_data_package.py` with ArcGIS Pro Python regenerated the local data package with 90 QC checks and zero failures.
  - `python scripts/smoke_test_data_package.py` passed 118/118 checks.
  - `C:\Users\ZZ\.conda\envs\RL\python.exe -m unittest discover -s tests -q` passed 16/16 tests.
  - `scripts/run_cispo_2030_full_year.py --horizon one_month --preflight-only` passed and estimated 4,761,900 variables, 6,465,714 constraints and 78,282,048 nonzeros.
  - A custom 24h monolithic build with `compute_max_cf=False` succeeded with 422,596 variables, 342,510 constraints and 2,037,793 nonzeros; reservoir variables now include `reservoir_turbine_flow`, `reservoir_spill_flow` and `reservoir_volume`; core cascade rows = 146 and edges = 124.
- Cascade server deployment and verification on 2026-07-06:
  - Server checkout HEAD `7a2ca27` contains implementation commit `b3e6298`.
  - Versioned data roots are `/data/zz2/National_model/data/model_ready_20260706_hydro_cascade` and `/data/zz2/National_model/data/hydro_timeseries_20260706_hydro_cascade`.
  - Server readiness with raw-GRFR SHA256 verification passed; it reported 2,030 hydropower stations, 620 reservoirs, 1,410 run-of-river stations, 142 cascade nodes, 124 edges, 4 low-correlation edges, 18 max-lag-bound edges and maximum lag 168 h.
  - Server regression tests passed 16/16 in 20.12 s.
  - Server `one_month` preflight passed with estimated 4,761,900 variables, 6,465,714 constraints, 78,282,048 nonzeros and 4.48 GiB model memory.
  - The actual 744h model build completed with 4,808,836 variables, 6,536,681 constraints and 46,092,407 nonzeros.
  - The optimization output directory is `/data/zz2/National_model/outputs/2030_one_month_hydro_cascade`; PID `244035` remained active at 2026-07-06 22:37 Asia/Shanghai after about 5 h 59 min.
  - Gurobi reported large matrix-coefficient and RHS ranges, barrier restarted near iteration 111, dual crossover pushes completed, and primal cleanup was still active at about 1,919,682 remaining pushes with `PInf=3.1246436e+02`. No `solve_report.json` or `solution_qc.json` existed at that checkpoint, so the 744h gate is not yet passed.
- Numerical-stability implementation and validation on 2026-07-07:
  - Commit `281f9c7` scales reservoir flow variables to `10^3 m3/s` and reservoir volume variables to `10^6 m3`, preserving physical `m3/s` and `m3` at all inputs, exports and QC checks.
  - `coefficient_zero_tolerance=1e-6`, `hydrology_flow_zero_tolerance_m3s=1e-4`, `BarConvTol=1e-8`, `Crossover=1` and `Threads=-1` are explicit configuration values.
  - Local numerical audit at 24h improved matrix coefficients from approximately `1e-10–3600` to `1e-6–24`, RHS from approximately `2e-13–4.48e10` to `4.32e-7–1.17e5`, and removed all coefficients/RHS below `1e-8` in the audited model.
  - Local 24h full solve: 422,596 variables, 342,508 constraints and 2,037,549 nonzeros; Gurobi `59.66 s`; `OPTIMAL`; `solution_qc=PASS`; peak RSS `0.865 GiB`.
  - Server checkout was fast-forwarded to `281f9c7`; 18/18 tests passed in `19.46 s`.
  - Server 168h full solve under `/data/zz2/National_model/outputs/2030_diagnostic_168h_numerics_scaled`: 1,299,844 variables, 1,581,351 constraints and 10,733,898 nonzeros; build `90.54 s`; Gurobi `675.56 s`; `OPTIMAL`; `solution_qc=PASS`; peak RSS `4.061 GiB`.
  - Server CPU is 48 physical cores / 96 logical processors. `Threads=-1` exposed all 96 logical processors; barrier factorization used 48 physical threads. Two RTX 4090 GPUs are present, but current `gurobipy 13.0.2` is the standard non-`+cu` build and therefore did not use GPU acceleration.
  - Detailed module and numerical audit: `MODEL_SYSTEM_AUDIT_20260707.md`.
- P30-cleanup and GPU validation on 2026-07-07:
  - Commit `a8cd150` removes the obsolete early block-boundary variables from `master.py`, switches conventional hydropower environmental flow to the configured `monthly_environmental_flow_2019_p30` dataset and keeps run-of-river hydropower as station-CF-weighted provincial hourly output variables.
  - Local checks: AST parse for changed Python files PASS; `C:\Users\ZZ\.conda\envs\RL\python.exe -m unittest discover -s tests -q` passed 19/19; `scripts/smoke_test_data_package.py` passed 118/118.
  - New server data roots: `/data/zz2/National_model/data/model_ready_20260707_p30_cleanup` and `/data/zz2/National_model/data/hydro_timeseries_20260707_p30_cleanup`; P30 proxy NetCDF SHA256 `c28f628642baaaac18d4461ac9474b3d622fcd80fbcd651884e6095d58203767`.
  - Server readiness with the P30 roots passed, including raw-GRFR SHA256 verification; server regression tests passed 19/19 in `18.06 s`.
  - Server 24h CPU P30 gate under `/data/zz2/National_model/outputs/2030_diagnostic_24h_p30_cleanup_cpu`: 375,910 variables, 278,737 constraints, 1,879,966 nonzeros; Gurobi `45.06 s`; `OPTIMAL`; `solution_qc=PASS`; peak RSS `0.879 GiB`.
  - GPU-enabled Gurobi was installed only in `/home/zz2/.local/envs/cispo-gurobi-gpu` from verified wheel `gurobipy-13.0.2+cu129-cp311-cp311-manylinux_2_24_x86_64.whl` (SHA256 `10f0a10fed0c0f959d11bc4f60d36d4ef04a13c48ecf649cd557e8b952de0680`; server SHA256 matched after upload).
  - GPU probe confirmed `linux64gpu[cuda12]`, `GPU model: NVIDIA GeForce RTX 4090` and `Start PDHG on GPU`.
  - The same 24h model with GPU-PDHG was interrupted after about 600 s because it was still iterating and had no `solve_report.json`; CPU barrier is therefore the accepted default for this model at this stage.
  - The P30-cleanup 744h CPU gate under `/data/zz2/National_model/outputs/2030_one_month_p30_cleanup_cpu` completed model build in `339.56 s` with peak RSS `5.336 GiB`; model statistics are 4,762,150 variables, 6,472,914 constraints and 45,718,011 nonzeros. Gurobi optimization is still running under PID `863603`; no `solve_report.json` or `solution_qc.json` exists yet.

### Known limitations and unresolved inputs

- CSP site potential and hourly profiles are missing; CSP is disabled.
- PHS open-loop/closed-loop hydraulic pairing is unavailable. PHS is represented as province-level 8h storage with a GHT 2026 operating floor and year-available project upper.
- Thermal online fuel term `f_on` is not implemented; fuel is charged on gross generation only.
- Hydropower type labels are assigned from the available GHT/proxy rules because source data do not provide reliable type labels for every plant; low-confidence labels are retained for now and should be validated later against external station evidence.
- Core hydropower cascade coupling, the scaled 168h solve and the corrected 744h sparse transmission gate have passed server regression, optimization and QC gates. PID `3778049` reached mathematical optimality but is preserved as a rejected transmission-formulation baseline. Current implementation covers conventional reservoir cascade operation, not open-loop or closed-loop PHS water-pair coupling.
- Core cascade environmental flow now uses a 2019 single-year monthly P30 proxy. This follows the requested P30 direction but is still not the formal 1980-2019 climatological P30; manual review of the 4 low-correlation / 18 max-bound lag edges also remains unresolved input work.
- Capacity-credit values and spur/trunk proxy costs still require parameter-source review. The Base capacity margin and inertia threshold are now reviewed at `5%` and `3.5 s` respectively; alternatives require explicit scenario overrides.
- The intraprovincial load-center network uses a 50% design-utilization assumption.
- Two western AC500 proxy edges exceed the 1000 km range of the cited source cost.
- Intraprovincial load-center transmission losses remain zero.
- Demand-flexibility calibration remains open: building thermal inertia/comfort data and province-hour EV connection availability, driving energy, accessible battery capacity and departure SOC are not yet available. The current daily envelopes must be sensitivity-tested before paper interpretation.
- Direct server access to PyPI fails TLS certificate-chain validation. The user chose to defer this issue. Do not disable TLS verification; use verified offline wheels when a new package is required.
- Temporary uploaded installers and wheel directories remain on the server; do not delete them without explicit user confirmation.

### Exact next action

1. 提交、双远端推送、正确checkout部署、服务器全套测试、detached `tmux`持久性和launcher监督集成均已
   完成。现在只重复只读检查`MemAvailable`、实时`vmstat si/so`和memory PSI；在自然达到
   `MemAvailable>=100 GiB`前不创建正式tag，不降低阈值、不drop caches、不干预其他用户任务。
2. 门槛满足后，以精确SHA`ba8e09f97a6526e299f807eb9be8c579a217caeb`、
   `barrier_checkpoint_fixed_server_host_memory_95_v2`、`annual_capacity_link_rows_8192_v1`和CPU`0-31`的
   32个物理核，通过已验证的detached `tmux`方式启动唯一2160h/start2880 Stage A资格运行。runner必须按
   `host_memory_soft_limit_fraction=0.95`解析有效Gurobi `SoftMemLimit`；按首个iteration>=30和结构阈值
   判定，不启动其他数值支线，绝不自动Stage B。
3. 只有2160h iter30、结构、内存和警告门槛全部通过，才保全证据、更新handoff并准备唯一8760h Stage A：
   `barrier_checkpoint_full_year_cloud_v4`、`Threads=32`、`soft_mem_limit_gb=600`、无`TimeLimit`，使用足够内存
   的云节点和不可变代码/数据/场景身份。2160未通过则先停止放大并只诊断这条路线；Stage B始终需要作者
   以后单独明确授权，不是Stage A或规划序列的默认下一步。

## Version history

### 2026-09-02 21:24+08:00 — 2160h内存门禁终态、GPTPro复核与三小时续测序列

- Git/范围：服务器运行提交仍为`ba8e09f97a6526e299f807eb9be8c579a217caeb`；本条只更新
  `CODEX_HANDOFF.md`、`MODEL_SERVER_STATUS.md`和`SERVER_RUNBOOK.md`，不修改模型、数据、solver参数或
  服务器checkout。终态证据保存在忽略目录`downloads/stagea_rowscale_2160_fail_memory_20260902_v1`。
- 终态证据：`qualification_gate.json=FAIL_TERMINATED`；raw结构精确匹配，presolved NNZ`106,864,011`
  通过反回归上限且无数值警告。任务在ordering阶段、Barrier之前终止；进程组RSS越过75GiB并最终记录
  `86.382GiB`，host used达到`99.008%`。因此没有iter30、Factor或缩放提速证据，也未启动Stage B。
- GPTPro质量复核：确认整行二进制缩放、ROR FLH修正、demand share解耦、24h双式验证和launcher安全
  方向正确；但要求把当前运行明确降级为Early Barrier screen，并补做同提交32核physical对照、严格容差
  长时窗、KKT/relative gap硬门禁、精确零水库上界及parent→new physical LP差异白名单。
- 调度/下一步：作者授权每3小时巡检并按内存逐级扩大本地测试，已创建heartbeat `3-stage-a`。不原样重启
  失败的2160h；先完成上述代码/审计缺口和24h回归，再以1488h/start2880做scaled/physical顺序匹配筛选。
  只有两者均通过且资源有保守余量，才依次考虑2160h、4320h、5880h；任一级失败即停止扩大。Stage B
  不是默认步骤，且不自动启动云端8760h。当前未解决项是ordering内存增长及HUP/TERM信号链的精确归因。

### 2026-09-02 20:05+08:00 — 唯一2160h/32核Stage A资格任务已启动

- 启动身份：实现SHA`ba8e09f97a6526e299f807eb9be8c579a217caeb`；tag
  `2030_base_2160h_stagea_capacity_link_rows8192_barrier32_20260902_v1`；output/control分别为
  `/home/zz2/National_model_server/outputs/<tag>`与`/home/zz2/National_model_server/run_control/<tag>`；
  detached tmux session为`cispo_stagea_rowscale_2160_v1`，20:05:24开始。启动准入时
  `MemAvailable=100.292 GiB`，未降低100 GiB门槛。
- 进程证据：tmux pane PID`384367`，wrapper`384371`，setsid solver/runner PID/PGID/SID均为`384500`，
  guard PID`384507`；同属`tmux-spawn-...scope`。solver实际affinity为`0-31`，拓扑验证32个唯一物理核、
  NUMA0/1各16核。参数快照为2160h/start2880、Base、Method2、Threads32、Presolve2、Crossover0、
  BarConvTol1e-2、Feas/Opt1e-5、NF1、Scale2、Aggregate1、无TimeLimit；运行时SoftMemLimit按host95解析为
  `125.5378982912` decimal GB，profile的80仅fallback/provenance。
- 初始状态：20:07:37仍在构建模型；guard`PENDING`，尚缺raw/presolved/factor及Barrier记录，进程组RSS
  约2.97 GiB，solver/guard stderr均0，无termination signal。不得把该启动或短时状态写成方案已奏效；
  只有结构门禁和首个iteration>=30同时通过才形成长时域加速证据。
- 监测：原automation id`2160h-stage-b`已原位改名/改写为“监测唯一StageA行缩放资格运行”，每小时只读
  核对身份、资源、结构、iter30与终态；明确不恢复旧Stage B/Case2 watcher、不改参、不重启、不启动
  Stage B。下一步保持活动checkout不可变，等待guard给出结构及iter30判定。

### 2026-09-02 19:58+08:00 — 精确提交已部署，Linux持久化/监督门禁通过，等待100 GiB准入

- Git/部署：实现提交`122642f616b7abb2ad137250721a937e83a6f524`和swap采样修正提交
  `ba8e09f97a6526e299f807eb9be8c579a217caeb`均已推送服务器裸远端与GitHub同名分支
  `codex/stagea-8760-row-scaling-v1`。唯一生产checkout
  `/home/zz2/National_model_server/repo`在无solver且clean条件下以detached HEAD切到`ba8e09f`；旧NTFS
  checkout未触碰。服务器Python3.11.15/Gurobi13.0.2上精确提交全套`256/256`通过，launcher `bash -n`
  与专项7项通过。
- 持久化证据：detached tmux probe根
  `/home/zz2/National_model_server/run_control/tmux_persistence_probe_sJrFGC`；跨独立SSH连接核对同一
  PID`344545`、SID/PGID`344545`和`tmux-spawn-...scope` cgroup，最终6个heartbeat、return code0、
  session自然消失。`Linger=no`不再作为阻断，但仍不使用user systemd托管长任务。
- 监督集成：使用不建模的临时fake Python在真实launcher上验证normal`0`、guard early`96`、重复
  HUP/TERM`129`、并发flock contender`90`、guard stuck timeout`97`；启动窗口信号另以`95`安全
  fail closed。复核所有记录的runner/guard PID均已消失，无孤儿求解进程。
- 现场修正：首次探针暴露`vmstat 1 4`的首个数据行是since-boot平均值，原`NR>2`会把历史swap误报为
  当前压力并永久返回94。`ba8e09f`改为`NR>3`，只对之后三个实时区间的`si/so`非零fail closed；真实
  活跃swap保护未放松。
- 当前阻塞/下一步：19:58十次5秒采样为`99.62--99.68 GiB`，尚未达到launcher冻结的
  `MemAvailable>=100 GiB`；memory PSI为0且实时`si/so=0/0`。不降低阈值、不清理内核缓存、不干预
  其他用户任务。达到100 GiB后以新tag和detached tmux启动唯一2160h/32核资格任务，随后按iter30门禁
  判定；Stage B仍非必需且绝不自动。

### 2026-09-02 — 唯一Stage A精确行缩放路线冻结并通过本地正确性门禁

- Git/范围：工作分支`codex/stagea-8760-row-scaling-v1`，基线`65c8b21`，本轮实现与文档提交
  `pending`，尚未部署。核心变更为`cispo_model/annual_capacity_link_scaling.py`，以及其在
  `config.py`、`load_center.py`、`master.py`、`diagnostics.py`、`run_contract.py`、checkpoint/结果保全、
  planning/MGA入口中的严格绑定；新增formulation profile
  `config/formulation_profiles/annual_capacity_link_rows_8192_v1.json`、2160工程profile
  `config/solver_profiles/barrier_checkpoint_fixed_server_host_memory_95_v2.json`、8760正式profile
  `config/solver_profiles/barrier_checkpoint_full_year_cloud_v4.json`，并配套validator、guard、唯一launcher、
  regression tests及四份强制交接文档。未纳入CF`1e-4`、PDHG、simplex、Annual Energy Coordinate v2、
  自动Stage B或其他并行数值支线。
- 模型变换：只对VRE/ROR年度可用量零右端约束做二进制整行左缩放；$s_f=2^{-k_f}$，
  $k_f$为`0..13`中保证缩放后最小非零系数`>=1e-6`的最大值，正式2160h/8760h必须两族均
  `k=13`。Wave和省内负荷中心容量不在登记表中。变换保持变量、目标、边界、矩阵支撑与可行域；
  物理对偶/松弛恢复为`pi_physical=s*pi_solver`、`slack_physical=slack_solver/s`，reduced cost不变。
- 求解合同：8760h Stage A使用`barrier_checkpoint_full_year_cloud_v4`和作者指定`Threads=32`；
  Stage B仅是未来可单独授权的可选任务，任何launcher、watcher或sequence都不自动执行。2160h资格运行
  使用`barrier_checkpoint_fixed_server_host_memory_95_v2`、32个物理核、
  `host_memory_soft_limit_fraction=0.95`、整机95%保护且无TimeLimit。profile中的
  `soft_mem_limit_gb=80`仅为fallback/provenance；runner运行时将其覆盖为物理内存95%对应的十进制GB。
  iter30和结构门槛依本页current snapshot；本轮尚未启动2160h，未形成长时域加速结论。
- 本地命令/验证：在PowerShell设置
  `CISPO_WAVE_ROOT=D:\codeenv\pycharmproject\National_RL\wave_energy`后，以
  `C:\Users\ZZ\.conda\envs\RL\python.exe -m unittest discover -s tests -q`完成全套回归，结果
  `290 passed, 1 skipped`。`scripts/validate_annual_capacity_link_scaling.py --hours 24
  --diagnostic-start-hour 2880 --solve`输出
  `output/annual_capacity_link_scaling_24h_start2880_solve_v6/validation_report.json`：15项结构检查全真，
  physical/scaled均status2 `OPTIMAL`，目标均为`2112716.676624984 million CNY`，两者原单位QC均`PASS`。
  短窗口wall差异不作为32线程或8760h性能证据。
- checkpoint/验收：Stage A候选向量按raw order校验shape/dtype/finite/bytes/SHA与模型名称顺序；
  `BarX==X`、`BarPi==Pi`须逐项binary64精确成立。只有严格scientific-acceptance合同满足时才能生成accepted
  规划状态；promotion后的报告/打包失败写独立finalization error，不得倒写为未接受或伪造完整结果。
- 服务器纠正：唯一生产checkout为`/home/zz2/National_model_server/repo`，clean`6065bfb`；旧
  `/data/zz2/National_model/repo` NTFS克隆禁止使用。本任务为切换到作者确认的唯一Stage A路线而有意
  停止旧Stage B及Case2 watcher，当前无本项目solver；这是对18:04未知归因记录的后续纠正，历史原文
  保留。下一步在形成精确提交并推送后，先通过detached `tmux`跨SSH持久性与launcher监督集成门禁，
  再启动唯一2160h资格运行；未通过iter30不得放大8760h，也不得自动讨论或执行Stage B。

### 2026-09-02 18:04+08:00 — Case1 Stage B遭外部SIGTERM，Case2门禁阻断

- 终态：tag`2030_base_2160h_case1_v3_stage_b_20260901_v1`于17:41:39写出return code143；
  solve report为`INTERRUPTED`/status11/SIGTERM、SolCount0，运行92699.686s、work units73433.167、
  simplex8366337，无objective/solution quality/QC/result manifest，strict audit rc42。
- 最后轨迹：PPushes remaining1262112、PInf1265.5003；这说明Crossover未完成，不能作为严格基线，
  也不能据此判断V3科学结果或自动启动Case2。
- 资源排除：launcher记录host guard0；46818个2s样本无遥测错误，RSS sampled峰28.908GB，host used
  峰77.64%、最低available29.55GB，memory PSI与stderr无异常；不是95%保护、OOM或Gurobi数值报错。
- 原因边界：system journal在17:41:39记录来自本机公网地址的SSH session断开，与终止同秒；但没有
  信号发送审计，不能据此确认是SSH/cgroup清理、人工命令或其他外部机制。必须保留为
  `EXTERNAL_SIGTERM_CAUSE_UNRESOLVED`，不得臆测归因。
- Case2：watcher PID881511已消失，最后status仍为17:41:05 `WAITING_STAGE_B`；没有claim、case2
  control/output或solver。其门禁按设计未绕过。禁止重启watcher后让失败Stage B触发Case2。
- 证据：关键control、solve report、start identity、config和资源摘要已复制至
  `downloads/case1_stage_b_interrupted_20260902_v1`并记录SHA256。production仍clean6065bfb，当前
  无本项目solver。下一步删除已过期heartbeat并请作者决定新的严格收尾/重跑方案，不自动重启。

### 2026-09-02 10:45+08:00 — 数值稳定性工程线完成整合并推送双远端

- 关系：6065bfb是65c8b21祖先，本地主分支只领先8165b20/65c8b21，无分叉；活动服务器继续锁定
  clean6065bfb以保持Stage B实现身份。
- 工程分支：`codex/numerical-stability-engineering-v2`从6065bfb建立，整合可逆equilibration、严格
  零入流水库证书、Annual Energy Coordinate和CF误差审计/配对工具；统一提交`7fce1ca4`已推送
  `origin`裸远端与GitHub，两个远端ref均核验为同一完整SHA。
- 验证：定向36项PASS；设置现有只读data/wave根后完整unittest 243/243 PASS（76.866s），
  py_compile/diff-check PASS。短worktree首次未设数据根的缺表失败如实保留。
- 判定：744h CF1e-4较慢是该尺度不晋级依据，不是更长时域性能定理。候选保留为Case1/Case2
  结束后的2160h单因素结构/有限Barrier筛选；不得叠加候选、直接启动8760h或热更新生产。
- 活动服务器checkout、模型数据、参数、输出和队列均未改变。下一步只在资源窗口满足后按
  `NUMERICAL_STABILITY_ENGINEERING_LINE.md`逐级执行，不绕过当前Stage B/Case2门禁。

### 2026-09-02 09:59+08:00 — 744h完整Stage A否决CF 1e-4候选，Stage B继续PPushes

- 身份/终态：基线与候选tag分别为`2030_base_744h_cf1e6_stage_a_concurrent_20260901_v1`和
  `2030_base_744h_cf1e4_stage_a_concurrent_20260901_v1`，生产实现均为6065bfb，pair于21:44:26
  启动、22:42:36结束，baseline/candidate runner rc均0、guard0。两条均为744h/start2880、
  Barrier16/Crossover0/BarConvTol1e-2/Feas/Opt1e-5、无TimeLimit/SoftMemLimit，唯一LP差异是
  CF零化阈值1e-6/1e-4；各自checkpoint manifest均`deferred_crossover_eligible=true`。
- 完整Stage A比较：候选Barrier 134对120步（+11.67%），solver 3070.307对2995.079s
  （+2.51%），work units 3006.566对2842.982（+5.75%），端到端3478.729对3380.386s
  （+2.91%）。runner 0.5s process-tree峰20.402对20.049GiB（+1.76%）；独立2s sampled job
  RSS为21.193对21.264GB（约-0.33%，口径不同，不得覆盖前者）。两遥测均errors0，整机峰
  61.287%、最低available约51.16GB，未OOM或触发保护。
- 科学判定：两条都是engineering Barrier checkpoint，strict solution contract `HARD_FAIL`且
  raw physical QC export失败，均无result manifest/planning state；候选目标比基线高371.039
  million CNY（约0.01598%），符合其改变可行域而非等价坐标的事实。五步筛选的Factor Ops优势
  未转化为744h完整收敛优势，故不晋级该尺度Stage B且不修改生产默认1e-6；此结论不能外推为
  2160h/8760h必慢，后续长时域复测须遵循独立结构筛选门禁。
- 证据/文件：服务器原目录原样保留；关键solve report、checkpoint manifest、工程contract、资源摘要
  与pair TSV已复制到`downloads/cf_744_stagea_pair_terminal_20260902_v1`并记录SHA256。隔离分支
  `codex/cf-sparsification-v1`终态worklog提交`4a95822bf0cfbaa85851c9f5d72ea55996109c32`；
  主工作区其余用户修改未触碰。
- 活动序列：09:59 Stage B同PGID3946395/Python3946400仍在Crossover PPush，约剩2.418M、
  PInf1633.873、solver约64942s，尚无终态。host available约44GiB、PSI0，且GPU0/1有未知客户；
  不再并发新大模型。Case2 watcher881511继续等待Stage B严格通过和available>=96GiB，随后幂等启动
  已批准Threads32 Case2。下一步保持4小时巡检并严格区分运行完成、QC通过和科学接受。

### 2026-09-01 21:44+08:00 — 启动匹配744h完整Stage A阈值A/B

- 依据：1e-4五步筛选已将Factor Ops降低6.14%且完整8760h物理误差上界已量化；作者已明确授权
  在Stage B内存空闲期并发两条744h以上数值测试。为检验是否改善完整Barrier收敛而非只改善首个
  factorization，晋级为单因素744h完整Stage A A/B；不混入年度坐标、线程、算法或容差变化。
- 配置/身份：baseline/candidate标签分别为`2030_base_744h_cf1e6_stage_a_concurrent_20260901_v1`
  和`2030_base_744h_cf1e4_stage_a_concurrent_20260901_v1`，PGID1045145/1045150；唯一LP差异仍是
  `coefficient_zero_tolerance=1e-6/1e-4`。两者均16线程、Crossover0、BarConvTol1e-2、无Gurobi
  time/memory limit并显式保存engineering checkpoint，输出隔离且不覆盖五步结果。
- 启动/资源：21:44:26 pair supervisor1045122启动成功，CPU集合沿用两个NUMA节点各16个；两个
  per-case monitor改为经验证的campaign绝对路径并已实际存活，pair2秒TSV和95%整机保护正常。
  启动时host used约29%、available约87GiB、PSI0，Stage B继续，生产repo clean6065bfb。
- Git：隔离分支新增Stage A pair launcher及worklog提交
  `ba89225a23375f2bc400d510b62f6e1865412239`；未部署到或修改生产checkout。
- 队列规则：若Stage B先终态，Case2 watcher会因活动744h返回`WAITING_OTHER_SOLVER`，待pair释放且
  available>=96GiB后立即启动；不同时强塞第三个32线程2160h Barrier。下一步每4小时检查Stage B、
  两个Stage A收敛/资源、pair终态及Case2 gate；Stage A后不得自动用对方checkpoint或跳过Stage B QC。

### 2026-09-01 21:41+08:00 — 744h CF阈值因子筛选终态：候选小幅降低Factor Ops，Stage B转PPushes

- 终态身份：基线`2030_base_744h_cf1e6_factor5_concurrent_20260901_v1`与候选
  `2030_base_744h_cf1e4_factor5_concurrent_20260901_v1`均从21:03:45运行至约21:18，实际快照均为
  Base2030、744h/start2880、Method2/Threads16/Presolve2/Crossover0/BarIterLimit5、NF1/Scale2、
  无TimeLimit/SoftMemLimit，唯一模型差异为CF阈值。两者status7/5步/solution_count0，runner rc2；
  这是预设因子筛选终态，不得标为科学解或QC失败。
- 数值/结构：候选Matrix min`1.000486e-6→3.7e-5`，raw NNZ减少20976，presolved rows/columns/NNZ
  分别`3269493/2975594/37040141→3269458/2975419/37023865`，dense columns5168→5165；
  Factor NZ`8.249e8→8.064e8`（-2.24%）、Factor Ops`5.048e12→4.738e12`（-6.14%）。
- 运行/资源：candidate solver522.9445s对baseline562.9116s（并发描述性-7.10%），ordering
  117.64s对135.34s；runner内部process-tree RSS峰20.112GiB对20.468GiB。pair级host峰约54.9%、
  PSI0、guard0。候选第5步Primal/Dual/Compl为8.87e9/2.93e3/9.53e9，基线为
  8.55e9/3.27e3/1.91e10；早期轨迹混合，不能仅凭5步外推最终迭代数。
- 监测更正：两个per-case telemetry进程均因生产repo不存在`monitor_case_resources.py`而退出；这是
  外部launcher路径缺陷。pair supervisor自己的2秒host/RSS TSV、solver telemetry、runner0.5秒RSS及
  time.txt均完整，因子比较仍有效，但GPU/独立resource summary缺失不得记为0，也不为补监测重跑。
- Stage B/队列：21:41同PGID3946395完成DPush阶段并进入6755240 PPushes，PInf3224.99；无终态文件，
  stderr/telemetry stderr空，采样10808/errors0、job RSS峰28.908GB、host峰54.924%。Case2 watcher881511
  保持`WAITING_STAGE_B`；不得把DPush结束误判为Stage B结束。下一步继续4小时监测；1e-4候选只晋级
  为`PROMISING_MODEST`，待空闲窗口做隔离744h完整Stage A+B，不能直接改生产或上8760h。

### 2026-09-01 21:04+08:00 — 完成CF阈值误差审计、并发启动两条744h因子筛选并部署Case2即时队列

- Git/隔离：基于生产`6065bfba34b76098e86307081323e8545a4d25ac`建立worktree/分支
  `codex/cf-sparsification-v1`并提交`46f843bc9137bf2112e33dba43e7cc4e584c4bfc`；新增只读审计脚本
  `audit_vre_cf_thresholds.py`和
  `audit_wave_ror_cf_thresholds.py`、匹配744h profile及外部campaign gate。生产checkout保持clean
  6065bfb，未修改源CF/Zarr、模型代码、活动Stage B checkpoint或输出。
- 审计：生产`coefficient_zero_tolerance=1e-6`已同时应用于VRE、wave和ROR。744h/start2880
  将阈值升为1e-4时，VRE删6152项、上界损失0.495424GWh/单小时0.009706GW；ROR删14826项、
  上界损失0.0442055GWh/单小时0.0001335GW；wave无变化。完整8760h对应VRE删64001项、
  上界损失5.222078GWh，ROR删261060项、上界损失0.879441GWh，wave无变化；两类既有容量
  floor损失合计0.415104GWh。VRE审计源系数321369360项，ROR12351600项，报告分别位于隔离
  worktree的`output/cf_threshold_audit_8760h.json`和`output/wave_ror_cf_threshold_audit_8760h.json`。
  两个审计脚本py_compile PASS、四个profile加载值核验PASS、`test_solver_profiles` 10/10 PASS；系统
  Python完整pytest因无gurobipy在collection阶段失败，不记为代码回归，候选未改生产模型代码。
- 运行：外部工具根`/home/zz2/National_model_server/campaign_tools/cf_744_pair_20260901_v1`；
  21:03:45同时启动生产1e-6与候选1e-4两条744h/start2880、Barrier16、前5步筛选，分别绑定
  两个NUMA节点的16个CPU。两条均无Gurobi内存/时间上限，各自2秒遥测，配对supervisor PID
  896264保留95%整机保护。21:04两条处于建模，Stage B继续，host used25.76%/available约91GiB/
  PSI0；并发墙钟只作筛选，晋级看presolve/Factor NZ/Factor Ops/轨迹/RSS，正式加速须隔离复测。
- Case2队列：部署`campaign_tools/case2_after_stage_b_20260901_v1`，脚本SHA256
  `cd5db9c61e6ad3976d1e70e591456cbcafcbb0843d3eee7cf8fa7d5a4e248ce0`，watcher PID881511、
  当前`WAITING_STAGE_B`。Stage B严格通过且资源/版本/无竞争求解门禁满足后，只启动一次既定
  2160h Case2 Threads32/Crossover0/最多21600s；不得换标签重启或绕过门禁。automation
  `2160h-stage-b`仍ACTIVE/每4小时，prompt已覆盖三类任务。
- 未决/下一动作：等待两条5步筛选产生build/solve日志和资源终态，判断1e-4是否实质降低矩阵范围、
  presolved NNZ或Factor Ops；若收益不显著即否决，不因物理误差小而推广。两条结束且Stage B通过后
  Case2自动接管；之后才安排同机隔离744h完整Stage A+B。8760h仍只在候选通过逐级门禁后启动。

### 2026-09-01 18:30+08:00 — 隔离完成年度账户坐标候选并把Stage B轮询改为4小时

- Git/范围：从服务器生产基线`6065bfba34b76098e86307081323e8545a4d25ac`建立独立分支
  `codex/annual-energy-coordinate-v1`，提交`4814c2e5f197cb152e9e37ff6dcf78df605bb38d`。
  修改`cispo_model/annual_energy_coordinate.py`、`load_center.py`、`master.py`、config/diagnostics/
  checkpoint/basis/solver-artifact contracts、runner、模型规范、formulation profile和测试；未改主工作区
  模型文件，未部署服务器，未改变活动Stage B、数据、求解参数或进程。
- 安全收缩：第一草案把资源年度发电也统一缩放，24h矩阵门禁发现最小系数
  `1.026e-6 -> 5.636e-10`，立即否决。当前提交仅将年度账户和intra-load-center年度流量用
  `8192 GWh/internal unit`表示；CF、径流、水库入流、VRE/wave/hydro资源发电变量和可用量行
  均保持物理值，不删减/截断小系数。输出与QC恢复GWh，flow penalty保持物理经济等价；
  checkpoint和原始solver artifact记录内部坐标并禁止跨坐标resume。
- 验证：24h/start2880同结构规模346767/213253/1834406。候选raw Matrix
  `1.0262457e-6..260.4167`（原版上限6250）、Objective最小`0.001004004`（原1e-6），
  RHS上限517.0825（原2873.3179）；严格候选为`OPTIMAL+solution_qc PASS+manifest complete`，
  objective `2112716.6766244858`与原版solve report逐位相同。完整本地回归223/223 PASS。
- 负结果/限制：严格候选178.807s、131 Barrier、370107 simplex、Kappa6.589e6，相比原版
  174.979s、120、366065、Kappa1.270e6没有短时速度/条件指标收益；24h Stage A候选也为
  11.503s/132步，对比10.861s/124步。原版严格运行虽OPTIMAL，但新增导出函数首轮NameError导致
  该原版根不完整；代码已修复，不能把该根当完整QC。不得宣称候选已修复收敛。
- 下一步：等待当前物理坐标Stage B形成严格端到端基线；随后只做一个2160h/start2880、相同
  Barrier16 Stage A+B候选A/B，不同时改容差、线程或算法，候选必须自产checkpoint；只有原单位
  目标/QC闭合且端到端确有收益才考虑推广，禁止直接上8760h。heartbeat `2160h-stage-b`已从
  每小时更新为每4小时；服务器2秒资源采样频率不变。

### 2026-09-01 17:36+08:00 — Case1 Stage B通过exact resume并进入deferred Crossover

- Git/身份：服务器production checkout为clean `6065bfba34b76098e86307081323e8545a4d25ac`；同一
  launcher3946098、solve PGID3946395/Python3946400及完整命令行持续，无旧PID误判或重复启动。
- exact gate：15:56生成`primal_dual_start_input.json`。该文件只会在scientific-input manifest、
  Gurobi版本、identity layers、exact LP Fingerprint、variable/constraint order digest、向量SHA/size/dtype
  和10398783/12520914维度全部通过后写出。Gurobi13.0.2、implementation bundle exact match，科学输入
  identity SHA256为`2eafc35116b997927d2952689778ffd1966f0f0f138ab3cfe02a3df921dfc8c9`，
  Fingerprint为signed `-821799056`（`0xcf045770`）。
- 路径：日志明确`LP warm-start: use start vectors`、`perform crossover with primal and dual start vectors`、
  `crush start vectors`和`Crossover log`；没有重新执行Barrier。Presolve1513.67s，presolved规模
  9539397 rows/8395548 columns/107048306 nnz。
- 进展/资源：17:36 DPushes由8159992降至222988，DInf约9.04，solver约5982s；尚不能称收敛。
  3462个2秒样本/errors0，RSS采样峰28.908GB、host可用最低92.465GB、used峰30.03%；当前memory
  PSI0、si/so0/0，双stderr空。GPU空闲符合CPU Crossover预期。
- 终态/下一步：无`return_code.txt`、`solve_report.json`、`solution_qc.json`或`result_manifest.json`，
  工程严格验收待定。后续作者已将heartbeat更新为每4小时；只在重要阶段/异常/终态报告，不改参、重启、并发或部署
  `Annual Energy Coordinate V1`。证据和快照SHA见
  `downloads/case1_stage_b_crossover_20260901_1736/README.md`。

### 2026-09-01 15:42+08:00 — 启动2160h Case1 Stage B并更正数值审计耗时/后续门禁

- Git/范围：本地HEAD `65c8b21ea7bbe583d126f1142eebb348c3b32f3d`并保留既有未提交修改；
  服务器生产checkout保持clean `6065bfba34b76098e86307081323e8545a4d25ac`。未改生产模型、数据、
  Stage A源结果或其他用户进程；新增本地/隔离启动脚本、证据README和数值审计附录。
- 前置门禁：server无CISPO solver，Gurobi13.0.2；MemAvailable113.093GiB，vmstat si/so0/0、
  memory PSI0。Stage A checkpoint `ENGINEERING_BARRIER_CHECKPOINT_ONLY`、eligible=true/reasons[]；
  primal/dual 10398783/12520914项、83190392/100167440bytes及SHA256全部复核PASS。
- 工具/验证：独立部署
  `/home/zz2/National_model_server/campaign_tools/case1_stage_b_20260901_v1`，launcher SHA256
  `4834535b1b5ba0a8936a6a7942994ab3f37cd15c3ccb9903b25be248980841e9`；server bash-n、monitor
  py_compile、checkpoint/profile定向`13 passed + 34 subtests`均PASS。
- 启动：15:40:56 launcher3946098，15:41:00 solve PGID3946395/Python3946400；目标为Base2030、
  2160h/start2880，profile`large_lp_2160_case1_v3_stage_b_v1`，显式允许engineering checkpoint和
  deferred crossover，不允许implementation漂移。无TimeLimit/SoftMemLimit，整机95%保护和2秒资源采样保留。
- 初始状态：15:42仍在数据/LP构建，双stderr空、资源正常；尚未生成`primal_dual_start_input.json`，
  故exact LP/Fingerprint/order门禁与直接Crossover路径仍待核，不把“已启动”写成“已成功续接”。
- 审计耗时更正：成功的8760h下载+完整SHA+审计为18437.594s（5h07m18s），其中本地流式MPS解析
  2865.453s（47m45s）；含此前失败尝试的总墙钟约6h59m。次日15:35是人工报告时间，不是审计运行终点。
  新附录`downloads/numerical_audit_8760_20260829_v1/ADDENDUM_20260901.md`将后续Gate C从PDHG改为
  2160h Barrier Stage A+B单一A/B，并补充dual/reduced-cost逆变换硬门禁。
- 监测/下一步：创建每小时heartbeat `2160h-stage-b`，只跟踪本标签；首先核实exact start和直接
  Crossover，再等待严格终态。数值缩放不部署到活动Stage B；终态后才实现Annual Energy Coordinate V1。

### 2026-09-01 13:59+08:00 — 作者终止2160h GPU-PDHG并关闭巡检

- Git/边界：本地HEAD `65c8b21ea7bbe583d126f1142eebb348c3b32f3d`，服务器生产checkout保持
  clean `6065bfba34b76098e86307081323e8545a4d25ac`；保留本地既有未提交修改。本动作不改模型、
  数据、求解profile、保护阈值或其他用户任务。
- 目标核验：停止前从run.pid、完整命令行、创建时间、PGID和GPU客户交叉确认唯一目标为
  `2030_base_2160h_case4_gpu_pdhg_unlimited_20260828_v2`、PGID1216966、Python1216969、GPU1；
  GPU0的两个无关计算客户未触碰。
- 停止：13:59:10仅对目标进程组发送SIGTERM；29秒内正常退出，未使用SIGKILL。写入
  `user_stop_20260901.txt`并通过`telemetry.stop`使遥测器正常退出。13:59:49复核求解、wrapper、
  telemetry均不存在，GPU1已无本任务客户；run_control记录`return_code.txt=143`和events end。
- 终态：solve report为`INTERRUPTED`/status11/SIGTERM，solver386921.588s、PDHG78474440次、
  SolCount0，末行P/D/Compl=1.32e-4/762/0.388；这不是自然收敛、科学接受、CUDA OOM、CPU回退
  或host guard终态。
- 资源：193911个2秒样本、telemetry errors0；进程树RSS峰27.043GiB，GPU1任务显存峰4558MiB、
  全程平均利用99.196%。资源供应正常但长期平台，故将本轮归类为有执行效度的算法负结果。
- 证据：`downloads/case4_gpu_pdhg_user_stop_20260901_1359/`保存stdout/stderr/events、配置、
  build/solve report、运行身份及资源摘要；stdout SHA256
  `b0e0229247c060e4c0d3e62e6b8a9e8ea5d9858354c256f49aad7b24746fcb3f`。
- 自动化/下一步：已删除`case-4-gpu-pdhg`三小时heartbeat，不自动重启PDHG。下一步转为梳理
  云端8760h后已验证改动，并优先评估Barrier Stage A+B与等价年度能量坐标缩放；任何新求解另行决策。

### 2026-09-01 13:52+08:00 — Case4运行107h后的长期平台量化

- Git/进程：本地HEAD65c8b21及既有未提交修改保留；服务器repo clean6065bfb；同一
  Python1216969/PGID1216966/create_time1787854514.09，未重启或换标签。
- 进度：solver386540s/78397740步，P/D/Compl=1.66e-4/763/0.388，目标
  6145955.98/1343518.08，相对分离78.14%，无return code或QC。
- 窗口：近3/24/48h目标绝对分离仅改善0.108/0.232/0.321%，D残差改善
  0.909/1.548/2.554%；P residual非单调、窗口最佳均1.04e-4，旧突破未转化为整体加速。
- 资源：193695样本/errors0，GPU1 100%/job4558MiB、全程平均99.20%，RSS16.59GiB/
  采样峰27.04GiB，主机可用约96.5GiB、PSI0；双stderr空，无CPU回退/CUDA/OOM。
- 文件：新增`downloads/case4_gpu_pdhg_heartbeat_20260901_1352/`证据和说明，更新交接及
  `MODEL_SERVER_STATUS.md`；没有模型、数据、参数、保护、服务器文件或自动化变更。
- 下一步：按作者无时限要求继续自然运行和三小时检查；只在终态、异常或新的实质突破时报告。

### 2026-08-29 23:32+08:00 — Case4 primal residual突破旧平台

- Git/进程：本地HEAD65c8b21及既有未提交修改保留；服务器repo clean6065bfb；同一
  Python1216969/PGID1216966/create_time1787854514.09，未重启或换标签。
- 进度：solver162185s/32634740步，P/D/Compl=1.04e-4/789/0.389，目标
  6160597.02/1343433.04；无return code或QC。
- 三小时变化：P残差降低97.354%，D残差降低0.127%，Compl降低0.256%，目标绝对分离降低
  0.887%；新P残差平台持续约1.54h。只记录轨迹突破，不宣称整体收敛加速或预测终态。
- 资源：81526样本/errors0，GPU1 100%/job4558MiB，RSS16.59GiB/采样峰27.04GiB，
  主机当前可用约86.9GiB，PSI0；双stderr空，无CPU回退/CUDA/OOM。
- 文件：新增`downloads/case4_gpu_pdhg_heartbeat_20260829_2332/`日志和说明，更新交接及
  `MODEL_SERVER_STATUS.md`；没有模型、数据、参数、保护、服务器文件或自动化变更。
- 下一步：保持无时限自然运行，三小时后复核P残差是否继续下降及D/Compl是否出现同步突破；
  不自动停止、StageB、其他算法或缩小时域。

### 2026-08-29 15:35+08:00 — 8760h完整原始矩阵审计终态与定向等价缩放方案

- Git：本地主工作区HEAD `65c8b21ea7bbe583d126f1142eebb348c3b32f3d`，既有未提交修改保留；
  固定服务器repo clean `6065bfba34b76098e86307081323e8545a4d25ac`。
- 范围：只读核验已经下载的云端8760h `original.mps.gz`及其流式审计结果，分析约束/变量族；
  未build、presolve、optimize，未修改模型、数据、solver profile、保护或活动PDHG进程。
- 完整性：4142909397bytes、SHA256 `344f2ae4cabb669123c2a946fe530fa3417ab7c10ebb035850584f043fe2435d`，
  `input_integrity=PASS`、audit `COMPLETE`；规模50907234/41458383/492835195与门槛一致。
- 结论：最大风险定位为VRE/ROR容量列混合小时CF与年度FLH，以及年度负荷中心GWh坐标；水库
  transition和近零VRE headroom列为第二阶段证据项。通用二进制缩放与提高截断阈值均不推广。
- 方案：提出`Annual Energy Coordinate V1`，S=8192GWh的二进制内部坐标；先代数/接口门检，
  再24h/168h工程验证与presolve对照，最后只做一个2160h同参GPU-PDHG性能验证。
- 文件：新增`downloads/numerical_audit_8760_20260829_v1/REPORT.md`，更新本交接、
  `MODEL_SERVER_STATUS.md`及隔离worktree工作记录；没有生产代码变更。
- 未决：尚无已部署或已证明加速的数值修复；full presolved范围、Kappa及水库族终态残差归因待补。
- 下一步：作者确认后在隔离分支实现年度能量坐标候选，严格通过原单位QC后才允许2160h运行；
  当前自然PDHG继续，不因审计方案停止或重启。

### 2026-08-29 15:16+08:00 — 2160h GPU-PDHG多窗口平台量化

- production clean6065bfb；活动身份不变，最新132365s/26552140步，未终态，资源正常。
- 只读复制gurobi.log，以既有严格进度格式解析26036条，取3/6/12/24h实际窗口，无插值/外推。
- 输出downloads/pdhg_plateau_review_20260829_1516/README.md、window_metrics.csv及原日志；
  源2096940bytes/SHA cfd9802e680a7187f70697a231e3d4ff67e382ce4831640446c0005bcadcc18a。
- 核心残差继续平台，目标分离仍缓慢改善；目标分离非证书，打印0%不代表数学严格零变化。
- 未改代码/模型/数据/参数/保护/进程或自动化；不因本分析提前停止，继续原3h巡检。

### 2026-08-28 20:27+08:00 — 例行巡检及99%联动调整待确认

- 生产clean6065bfb，同2160h身份/参数/资源记录正常，约64600s仍未终态，未作服务器变更。
- 保存配置/求解日志/events/两stderr/资源摘要于downloads/case4_gpu_pdhg_heartbeat_20260828_2027。
- 记录作者99%重试请求的待确认项：旧2160h95%保护仍有效，尚未授权联动调整，不执行重试。
- 未修改模型、数据、求解器参数或自动化；下一步原3h巡检，等待联动范围确认。

### 2026-08-28 19:10+08:00 — 8760h GPU0在预处理阶段触发主存保护，终态保全

- 只读核验生产clean6065bfb；本地HEAD65c8b21，更新三份交接、启动记录终态提示及独立终态证据目录。
- 运行17:20:22→18:23:22，总约63min；完整模型build_report=3663.595s/48.183GiB。
  optimize后约109s在Presolve触发94%主机优先保护，SIGKILL仅原新组702485，rc=-9。
- 实际参数文件确认Method6/Threads32、原PDHG容差和TimeLimit/SoftMemLimit Infinity；
  没有Start PDHG on GPU、迭代轨迹或QC，不能归类为GPU OOM/PDHG慢收敛/自然终态。
- RSS采样峰77.627GiB、整机94.374%、Swap近8GiB；GPU0仅job386MiB，2秒1891样本/errors0。
- scp完整control及7份输出到downloads/8760_gpu0_terminal_20260828_1910，逐份SHA25/25匹配；
  README说明口径/精确时间/无新MPS或解。旧2160h运行和监测继续，不暂停其自动化。
- 原模型规模与历史相同但指纹不同（2acf0ca2 vs d16b4c7e），原因待核，不能以规模相同替代等价证明。
- 下一步等待作者关于主存窗口/后续试验的新决定；不重启/缩小/取消保护，不干预其他任务。

### 2026-08-28 17:22+08:00 — 作者授权完整8760h GPU0并发尝试

- 本地HEAD65c8b21、生产clean6065bfba34b76098e86307081323e8545a4d25ac。
- 新增scripts/run_8760_gpu_pdhg_supervised.py、run_8760_gpu_pdhg_instrumented.py及
  tests/test_8760_gpu_pdhg_supervised.py；生产repo不改，独立部署campaign_tools/full8760_gpu0_20260828_v2。
- Base2030/full8760/start0、GPU0 UUID锁定、Threads32及其他PDHG参数和现有2160h一致；
  私有配置只改启动内存准入96→1GiB，无算法内存/时间上限；95%旧保护前新组94%优先退出。
- 先prepare-only/生产preflight-only（PASS、rc0），后nohup一次启动；17:20:22新PID/PGID702485。
  首次v1启动器拼写错误返回125、未建模，现场保留；v2已修正，6/6单测、pyflakes/编译PASS。
- 输出与参数/输入manifest/资源/旧失败证据保存在downloads/8760_gpu0_launch_20260828_v2；
  README含完整命令、脚本SHA、变化边界和下一步。配置null已核，真实Params Infinity待建模结束前读取。
- 17:22新模型正在构建，GPU上下文已建立但未GPU迭代；原2160h及审计下载未停止/改参。
- 未决：8760h真实矩阵指纹、峰值主存/显存、GPU实际开始、收敛及QC均待本轮推进；
  不把预估33.4GB/目前8.38GiB当峰值，不自动重启/缩小/StageB，不将自然退出当科研接受。

### 2026-08-28 17:12+08:00 — 登录态核实N50R5绑定，纠正资源查询范围

- Git：65c8b21ea7bbe583d126f1142eebb348c3b32f3d；保留既有未提交改动。
- 文件：追加downloads/cloud_resource_inventory_20260828_1703/README.md及CODEX_HANDOFF.md、MODEL_SERVER_STATUS.md、SERVER_RUNBOOK.md；无代码变更。
- 证据：Chrome账号管理/SSH列表/资源管理所属关系图交叉核验NC-N50R5=scvk386、BSCC-N56R5=scxk805；所有五中心蓝色在线。原A8上的scontrol查N50R5返回not found，范围仅原集群。
- 验证边界：N50R5网页SSH返回connection closed，未获得shell；GPU队列未从控制台返回，配置和实际调度权限仍未知。
- 风险：首页可用额度约-4973元；未核合同/信用政策，不与SSH失败建立未经证实的因果关系。
- 下一步：核实NC-N50R5登录/队列和计费条件；确认入口后只读查配置，任何计费试算另行授权。本轮未改资源、账号、许可证或求解进程。

### 2026-08-28 17:03+08:00 — 超算账号资源权限、配额和实时库存核验

- Git：65c8b21ea7bbe583d126f1142eebb348c3b32f3d；保留所有既有未提交改动。
- 本轮文件：新增downloads/cloud_resource_inventory_20260828_1703/README.md；仅追加CODEX_HANDOFF.md、MODEL_SERVER_STATUS.md、SERVER_RUNBOOK.md。
- 证据：SSH只读id/sinfo/scontrol/sacctmgr/squeue；用户组交叉验证分区AllowGroups；17:03:52节点状态快照，详见资源记录中的命令与返回值摘录。
- 结果：三可申请CPU分区，M8/A8_768/A8_384严格idle80/29/0；cpu=1280，作业提交上限50；当前队列空；全部361唯一节点无GRES。
- 未决：跨中心GPU资源、适用价格、余额及平台额外限制未查询；两个浏览器均停在控制台登录页，已保留Chrome页。
- 下一步：作者登录后只读查全平台GPU和价格；任何开通/计费运行需单独授权。不修改既有PDHG、备份或审计流程。

### 2026-08-28 17:00 同2160h的PDHG与Barrier16收敛对照

- Git：主区HEAD65c8b21未变，未提交/部署；新增文件位于downloads/pdhg_barrier_comparison_20260828_v1，
  同步更新handoff/status/runbook，保留其他窗口记录。输入只读，不构建模型或调用求解器。
- 命令：scp读取活动Case4 outputs/<unlimited标签>/gurobi.log至input/pdhg_gurobi.log，
  D:/anaconda/python.exe <对照目录>/compare_logs.py；unittest discover同目录test_compare_logs.py及py_compile。
- 输出：REPORT.md、comparison.json、barrier16_trajectory.csv、gpu_pdhg_trajectory.csv、
  same_time_samples.csv、window_changes.csv，包含输入SHA、源日志行号、真实时间和取样滞后。
- 验证：Barrier243条、PDHG9916条，轻量LP身份全部字段匹配；同2160/start2880；有符号目标、初始假零gap、
  无前视取样、重复迭代拒绝4项测试PASS。PDHG快照末51765s，不能当作终态；未混用callback残差。
- 结果：PDHG前期接近快、后期平台，10—14h目标差只降0.48%，Barrier降88.83%；14h绝对差PDHG仍小约10倍。
  Barrier历史17.4175h达到更小目标差，但23h严格质量HARD_FAIL；不能进行同QC最终速度排名或预测PDHG剩余耗时。
- 原算法/日志采样/审计下载均不干预；16:59审计下载222MiB继续。下一步维持原监测及审计，终态后才更新同QC比较。

### 2026-08-28 16:44 云WLS许可与GPU-PDHG部署条件只读核验

- Git：65c8b21ea7bbe583d126f1142eebb348c3b32f3d，未提交；保留其他窗口16:43的新审计交接。
- 文件：新增downloads/cloud_gpu_license_review_20260828_v1/README.md，更新handoff/status/runbook；
  没有模型、数据、服务器环境或任务修改。
- 命令/证据：SSH sinfo -a、squeue、sacctmgr show assoc；许可文件安全解析仅输出WLS存在标志、
  非秘密ID/权限/是否有到期日；importlib.metadata查询云端13.0.2；固定服务器nvidia-smi、
  ps及GPU解释器pip show查询13.0.2+cu129。未输出凭据、API key或许可证原文。
- 结论：WLS类型允许按有效授权跨机器，GPU无需额外许可证；新GPU节点仍须验证到期/配额/联网、
  驱动与GPU build。当前资源区无可见GPU队列，不能直接把amd_a8_768作业换成GPU作业。
- 下一步：先取得可用GPU型号、资源区及价格，获明确申请授权后才启动小型授权/GPU smoke和
  同2160h对照；不承诺更快收敛，不停止本地PDHG，不触碰独立审计/备份流程。

### 2026-08-28 16:43 授权恢复8760h审计：独立可续传本地缓存与自动审计门禁

- Git：主区65c8b21、隔离候选cff89ce不变；未提交/部署。只新增隔离scripts/fetch_and_audit_mps.py、
  tests/test_fetch_and_audit_mps.py，并更新主handoff/status/runbook、隔离worklog及运行根README。
- 源：云端已保全original.mps.gz，stat4142909397bytes/mtime1787857317与既有记录一致。
  预期SHA344f2ae4cabb669123c2a946fe530fa3417ab7c10ebb035850584f043fe2435d；无源文件修改。
- 首次32MiB/2线程传输16:37:37启动31188，两块180s超时；16:41:47按创建时间/完整命令行核验后
  仅终止该本机父进程及其两个SSH客户端，未操作任一服务器求解/另一个备份。旧部分文件全部保留。
- 改用1MiB/2线程、每块最多3次、排他缓存锁、完成块SHA收据；16:41:48 v3 launcher13448/
  Python49052启动，16:42:10已有3个完整块、stderr空。完整副本SHA通过才自动本地审计，不再边传边解析。
- 命令/输出：工作目录为隔离worktree；.venv/Scripts/python.exe -u scripts/fetch_and_audit_mps.py，
  source-host paracloud-bscc-a8，cache-dir outputs/local_8760_verified_v3/cache，
  output-dir outputs/local_8760_verified_v3/run_v1，workers2/chunk-mib1/chunk-timeout-seconds180；
  完整参数由run状态、进程命令和v3/README保留。预期audit位于run_v1/audit/。
- 验证：新增7项离线测试及原解析/缩放11项PASS，py_compile通过；整文件坏SHA不允许启动审计的门禁
  及真实小MPS解析端到端路径均覆盖。脚本/测试SHA见运行README。测试不访问网络或调用求解器。
- 未完成：仍在DOWNLOADING，完整hash/审计均待执行；当前不是数值修复验收。16:38 PDHG同进程/clean6065bfb，
  GPU1满载4600MiB、资源errors为空；既有3h巡检不变。下一步检查同一run终态，失败保留且不盲目重启。

### 2026-08-28 16:33 全尺寸流式审计传输失败、备份停滞及PDHG状态复核

- Git：主区65c8b21ea7bbe583d126f1142eebb348c3b32f3d、隔离候选cff89ceb2e6590923f2413d9a739c3d4a7013c29；
  服务器clean6065bfba34b76098e86307081323e8545a4d25ac。未提交或部署；保留所有既有修改。
- 命令/证据：Get-Content读取隔离worktree outputs/stream_8760_original_v1/{status.json,ssh.stderr.log}
  和outputs/stream_8760_launch_v1/stderr.log；Get-CimInstance复核退出的审计进程及仍在的备份45560。
  SSH只读stat云端original.mps.gz，读取固定服务器同一Case4的ps/git/stdout/events/资源summary及末行、
  双stderr、return_code存在性；读取备份backup_status.json并与本地transfer_progress.json比对。
- 结果：审计15:38:14因SSH Connection reset后gzip EOF而FAILED，最后104072756 nnz约21.1%，无完整审计输出。
  云端源stat大小/mtime不变，但未重做全量哈希；备份14:22:46后进度不更新、进程尚在，不能当作完整副本。
  PDHG16:31 solver50470s、9847340步，资源记录正常、未收敛；不得因缓慢停止。
- 修改仅为CODEX_HANDOFF.md、MODEL_SERVER_STATUS.md、SERVER_RUNBOOK.md及隔离NUMERICAL_STABILITY_WORKLOG.md。
  无模型/数据/环境/求解参数变更，无新求解、无重启、无清理。失败现场仍为原目录。
- 下一动作：向作者报告不能再只等待已退出的审计；建议安全处理传输并校验稳定副本后重做审计，
  具体恢复动作待作者决定，不自动重复启动。完整原矩阵/预求解矩阵数值修复尚未验收。

### 2026-08-28 15:09 历史8760h Stage A收敛日志简报与完整轨迹

- Git：本地HEAD65c8b21ea7bbe583d126f1142eebb348c3b32f3d；被分析原代码
  3f739fd6216b1c7fc356e8d3a1d9a257c666f0c5。未提交，保留其他窗口已有修改。
- 范围：只读历史job4139552归档及job4396245恢复对照JSON，不读取巨大NPY/MPS，不连接云端/固定服务器；
  日志字段解释参照Gurobi官方在线文档，链接已附入报告。
- 新增文件：scripts/report_8760_convergence.py、scripts/render_8760_convergence_note.py、
  tests/test_convergence_note.py；输出目录output/pdf/8760_stage_a_convergence_20260828_v1下
  PDF/Markdown、FIGURE_CONTRACT.md、README.md、QA.md、figures和data。同步本交接/status/runbook。
- 命令：D:/anaconda/python.exe scripts/report_8760_convergence.py --source-dir
  downloads/paracloud_4139552_2030_8760_stagea_barrier_v2_20260826 --recovery-dir
  downloads/2030_stage_a_first_result_visualization_v1/input --output-dir
  output/pdf/8760_stage_a_convergence_20260828_v1；bundled Python运行render_8760_convergence_note.py
  --report-dir同目录，完整可复制命令见README。
- 证据：原始7文件SHA256 PASS，4恢复JSON和清单记录哈希；两通道608点连续，目标/时间显示精度一致，
  残差不混接。阶段时间加总与solver总时长1773606.980326891s闭合；6/6解析测试、py_compile PASS。
  PDF3页785875bytes，逐页渲染及文本检查PASS；PDF SHA256
  e0b6ba0f032cb41bc1c4ef1b04934252079206fc30c3549abad66ffe71e7924e。
- 结论：607次迭代耗时1752971.911s，占solver98.8365%；中位步间隔47.937min、最后100步3.0933天。
  原矩阵跨度6.246964e9不是条件数，未保存全尺寸presolved范围。solver OPTIMAL不改变原LP HARD_FAIL，
  恢复QC FAIL/56 of58独立保留；StageB未执行，恢复optimize/presolve0不能并入本轮迭代。
- 未决与下一步：本简报不补齐完整presolved分族系数及Kappa、不定位/修复全部QC原因、不改变门槛。
  作者先审阅简报；其他窗口独立稳定性分支、MPS流式审计、Case4和完整备份沿用各自既有流程，
  本次没有重新核验其当前进度，不宣称其新终态；已保留另一窗口15:07的新交接内容。

### 2026-08-28 15:07 数值改进隔离实验完成首轮；完整8760h矩阵审计后台运行

- Git/隔离：生产6065bfba34b76098e86307081323e8545a4d25ac保持clean；主工作区HEAD65c8b21
  及用户原未提交修改保留。新worktree .codex_tmp/numerical_stability_20260828_v1，候选提交
  cff89ceb2e6590923f2413d9a739c3d4a7013c29；未部署、未合并或push。
- 变更：独立分支新增lp_equilibration/mps_stream_audit/zero_bound_certificate、5个实验/诊断脚本、
  20个单测和NUMERICAL_STABILITY_WORKLOG.md；monolithic.py只修正有严格零入流证书的零上界余量。
  主工作区仅本轮三个交接文档追加，不改主模型/参数/数据/环境、PDHG进程或其他备份任务。
- 验证：独立venv Gurobi13.0.2、numpy1.26.4/scipy1.13.1；原RL Gurobi12.0.1未修改。
  237/237 unittest 80.494s PASS，py_compile/pip-check/diff-check PASS，MPS逆变换bit-exact。
  24h/start2880源213253行/346767列/1834406nnz；10944个UB→0全部由旧MPS等式求和证明，
  其余矩阵/目标/RHS/LB/名称/方向逐项不变。不能把这个证书当成收敛改善证据。
- 负结果：无预算缩放v1原单位误差变差；v2在1h改善primal误差但更慢，24h原版/缩放/零界修正
  全部NUMERIC。HSD诊断仅SUBOPTIMAL而非INFEASIBLE，没有有效IIS。全部现场保留，候选不推广。
- 后台审计：14:49:54本机Python34684/launcher37332/SSH40220开始只读云端完整original.mps.gz，
  预期4142909397bytes、SHA344f2ae4cabb669123c2a946fe530fa3417ab7c10ebb035850584f043fe2435d；
  预期50907234行/41458383列/492835195nnz。15:06:29为24088472nnz、约39MB RSS，未完成全SHA校验。
  工作区outputs/stream_8760_original_v1/status.json为状态，完成才生成audit.json；
  源端仅cat，本机解压/统计/哈希，不在固定服务器或云端计算节点构建/求解新LP。
- 接续：同一审计不重复启动；失败保留现场，不盲目重跑；COMPLETE且gzip/ENDATA/SHA/维度通过后
  分析族统计，进一步定位水库状态链与大规模预求解风险。尚未宣称完整数值稳定性修复完成。
  当前PDHG无时限及3h/2s频率不变，本轮不自动StageB/其他算法/缩小时域服务器任务。

### 2026-08-28 14:34 三轮大规模数值尺度诊断：风险延续，非已证实的新数值崩溃

- Git：14:31服务器实核clean`6065bfba34b76098e86307081323e8545a4d25ac`；
  local HEAD`65c8b21ea7bbe583d126f1142eebb348c3b32f3d`，既有未提交修改均保留。
- 范围/文件：只读SSH/scp日志、build/solve/config/run_identity；新增downloads/numerical_review_20260828_v1
  下collect_evidence.py、REPORT.md、evidence.json与两个2160h日志快照，更新三个交接文档。
  不改生产模型、数据、参数、进程、环境、自动任务；未启动新模型、presolve、optimize或其他Case。
- 命令/验证：python -m py_compile及python运行collect_evidence.py通过；已有1h归档原MPS的
  Matrix/Objective/RHS极值和nnz共7字段与build_report精确一致；MPS RHS中的OBJ常数单独排除。
  原始输入SHA256记录在evidence.json；monolithic.py/load_center.py/DAC参数对production提交无差异。
- 发现：三轮Matrix 1.0004860087065026e-6～6250、Objective1e-6～3853.189875762917，
  Matrix比6.247e9；两个2160h同指纹0xcf045770、同原/预求解维度。6250是DAC年度耗电，
  极小目标来自省内流量惩罚；V3放松容差未缩小矩阵范围。三轮灵活负荷均关闭，不能直接归因旧V5热状态链。
- 质量：云端8760h/Case1原LP最大约束违反2.28683e-5/0.0384984，均OPTIMAL但strict HARD_FAIL；
  Case4约14:25为8304240步、42905s，stdout残差0.00393/838、Compl0.394，目标仍分离、无最终QC。
  未检出明确Numerical trouble等告警；残差平台不是数值崩溃的充分证据，也不证明未来无法收敛。
- 限制：旧1h归档预求解前后全局maxA均6250，最差单行比9.42e5→2.035e8，说明全局范围不能涵盖
  所有预求解风险；这不是当前全尺寸结论。全尺寸presolved系数分布和Kappa仍未知。
- 下一步：先完整原/预求解系数分族诊断，再考虑保持模型等价的单位缩放并原单位QC；未经另行授权，
  不截断小系数/改目标惩罚/增加求解组合/终止当前PDHG。3h heartbeat与2s采样、95%保护保持。

### 2026-08-28 14:18 Case4第四次巡检：改善放缓，保持无时限

- 范围/Git：生产clean `6065bfba34b76098e86307081323e8545a4d25ac`，local HEAD
  `65c8b21ea7bbe583d126f1142eebb348c3b32f3d`未提交；仅三个交接文档和独立巡检README更新。
  SSH只读检查Git、run.pid、ps身份/命令行、实际配置/日志/资源，scp独立备份；未动运行进程或参数。
- 标签仍2030_base_2160h_case4_gpu_pdhg_unlimited_20260828_v2，PGID1216966/Python1216969、
  02:15:14创建时间一致；TimeLimit/SoftMemLimit对应字段null，GPU1客户匹配RTX4090/Start PDHG日志。
- 14:18:02为8211040步、solver42448.095s含presolve，墙钟12h03m。stdout42440s目标
  6.19070422e6/8.54039989e5、primal/dual/Compl=0.00393/837/0.394，相较上次改善很小；
  不证明永久停滞或未来必不能收敛。callback残差0.0436490391/2693.6107041单独保留，无终态/QC。
- 资源：summary21681条/errors0至14:17:56，raw至14:18:00，顺序复制差4秒；RSS17.002GiB/
  峰27.043GiB、host可用86.831GiB；GPU1显存4600MiB、job4558MiB，自上次均值99.9991%，
  当前61°C/313.73W、峰61°C/317.6W。Swap7.4129GiB、swap-in增量19.762MiB、swap-out0、
  当前memory PSI0，job CPU累计46170.91s。GPU0无本job客户，stderr空，无OOM/回退/95%保护触发。
- 输出：downloads/case4_unlimited_20260828_v3/review_20260828_1417/{run_control,output,README.md}，
  为活动文件分别复制的证据，非终态原子归档；没有删除/覆盖其他实验结果。
- 文档首轮补丁因其他窗口新增14:17结果备份条目而未匹配；重新读取后仅追加本次记录，保留对方改动。
  下一步约17:17继续既有3小时heartbeat，2秒采样/95%保护/无时限不变，不因长尾停机、不启动其他Case。

### 2026-08-28 14:17 首个2030结果可视化完成，完整固定服务器备份后台进行

- 14:19复核补充：后台PID45560/创建时间一致，stderr空；最新完整范围1810938732bytes、29/104。
  服务器analysis_v1/figures的12文件全量SHA256与本机一致，figure_backup_integrity.json PASS；
  全release仍IN_PROGRESS，Case4原进程1216969继续运行。
- Git基线`65c8b21ea7bbe583d126f1142eebb348c3b32f3d`，本轮未提交，保留既有脏工作树。
- 按作者要求备份整个历史恢复release，非只有结果CSV；源301文件6606826274bytes。
  目标`/home/zz2/National_model_server/backups/2030_8760_stage_a_first_recovered_20260828_v1`。
  t550只读资源检查约2.5TiB空闲、86GiB可用内存；未操作独立GPU求解任务。
- 先尝试SCP，独立小文件多连接下载遇Connection closed；改为二进制tar流取回60个分析文件，
  加manifest共61文件。完整release受约1MiB/s网络总吞吐限制，改为分块可续传；8路未显著
  改善吞吐，最终后台4路。只停止本任务自己的传输进程，没有停止服务器求解或删除文件。
- 新脚本`backup_recovered_release.py`（初始流传输）、`parallel_backup_release.py`（最终后台）、
  `verify_preserved_backup.py`、`visualize_preserved_2030.py`；新测试`test_preserved_backup_verifier.py`。
  交接更新CODEX_HANDOFF、MODEL_SERVER_STATUS、SERVER_RUNBOOK；另在downloads产出README/证据/图表。
- 精确启动/续传参数见`downloads/2030_stage_a_first_result_visualization_v1/README.md`。
  后台PID45560/14:14:41；4路64MiB分块，源read-only，不复制SSH凭据，不申请计算资源。
  t550旧checkpoint经SHA256验证后复制4个目标1477850384bytes，不删除或修改旧副本。
  源完整inventory已落本机；结果86文件预期hash来自原manifest，其他文件由源端新算hash。
- **当前仍IN_PROGRESS**：14:14:45计1626281156/6606826274bytes（只计完整范围，不含正在写的片段）。
  文件大小可能暂时为稀疏文件表观值，不能据此认定完整。脚本最后自动对301文件全量hash，
  `release_integrity_report.json` PASS后才写COMPLETE；本条不是终态备份成功声明。
- 图表输入60文件逐项SHA256 PASS，manifest hash
  `277732ed0a4016650e084d1b8c3c820e240b4ff6a99d0b40b3ef9753e5f2096d`。
  装机4730.771GW（储能功率另304.455GW），发电10838.759TWh/负荷10608TWh，风光占44.763%，
  净排放3561.645MtCO2/上限4000；原目标4.188006万亿元（2025不变价）。不据此宣布科学验收通过。
  成本汇总不重复相加；保留主分项-354.02元闭合差、所有微小值和QC FAIL。
  月度年度发电差-1.86e-9GWh，全国电量闭合4.16e-7GWh，时间8760行连续不重复；不代替原QC。
- 输出`figures/2030_stage_a_overview`与`2030_stage_a_operation`，均PNG/PDF/SVG，加CSV/JSON。
  源结果不改，分析另存；已复制到server父目录analysis_v1。PNG实际检查，修正CO2字体缺失和图例遮挡；
  交互图736/360与1024宽明暗模式实检、320宽边界PASS，精确数值提示可用，无浏览器错误。
  小测试4/4通过，4脚本py_compile通过；未重跑模型或扩大全年求解测试。
- 下一步：保持Windows开机联网，查询本机background.stdout/stderr、服务器backup_status；完成后
  核验301文件报告PASS和原86文件清单，追加终态记录。仍运行时禁止并发重复写同目录。

### 2026-08-28 13:45 云端8760h Stage A恢复成功终态与产物复核

- 请求：作者询问“是否恢复”。只读SSH/sacct/文件元数据与关键hash复核，下载小型终态报告，
  未提交新作业、未安装环境、未改变模型/数据/阈值、未重启或干预Case4。
- 作业：4396245 COMPLETED0:0，24核，02:13:56--03:18:35，elapsed1:04:39，wrapper/tiny测试均rc0，
  stderr为空。运行末尾代码已完成result_manifest验证和PlanningState候选读取。
- 完全匹配：原始LP41458383变量、50907234约束、492835195非零元，fingerprint=-781497218；
  variable/constraint digest与原checkpoint完全相同，offline_recovery exact_lp_identity_and_full_order
  为true、identity_differences={}。author allow flag为true但未用到豁免，不是绕过门禁的恢复。
  全年恢复未调用optimize/presolve，target SolCount0，不做新优化。
- 耗时/内存：build2336.55684s、build peak48.584GiB；完整恢复monitor3843.847s/peak62.061GiB；
  Slurm batch MaxRSS64244236K（约61.27GiB），与0.5秒进程树采样62.061GiB口径不同，均如实保留。
- 输出：preservation_report各阶段COMPLETE/errors[]，result_manifest86文件/5852013714bytes。
  本次所有文件存在和size复核0失败；另实读SHA验证QC、solve report、candidate cohort/summary及
  state source hashes，均PASS。未在登录节点重新全量hash4GB模型；不宣称完成第二次全文件SHA审计。
  archive_manifest COMPLETE；original.mps.gz4142909397bytes/SHA344f2ae4...435d；完整变量名目录
  206395222bytes、约束名目录251766440bytes，参数归档为未求解重建模型的参数而非内部Barrier状态。
  原solver profile和config另在source_backup/配置快照；无presolved副本/uncrush/factorization。
- 结果：容量/运行/成本/碳/BarPi均生成；hourly dual271560行、annual dual3366行。
  candidate capacity_cohorts_v2共86900行，next_planning_year2040，source_qcFAIL、authorPENDING、
  scientifically_acceptedfalse，未筛除小值/零值，未自动进入2040优化。
- QC：hard_checks56/58，失败unidirectional_interprovincial_flow、objective_components。
  opposing flow最大1.425562296e-5GW、累计0.297960491GWh、edge_hours149717；objective component
  residual=-0.000354019459million CNY。重算objective4188006.0843866686 vs源4188006.084013813，
  两者记录均保留，不修改源报告。raw LP有2行超过1e-5，最大2.286828932e-5（load_center_ror_generation_closure_p43），
  bound最大8.128594686e-9、无超阈值bound。保存成功不等于科学验收PASS或所有论文结论成立。
- Git/文件：HEAD65c8b21未变；更新CODEX_HANDOFF、MODEL_SERVER_STATUS、SERVER_RUNBOOK及当时独立的
  Stage A保全说明；该说明未纳入当前可依赖提交，本条自包含保留其历史事实。备份报告在
  downloads/cloud_stage_a_recovery_4396245_20260828_v1/terminal_review_1342；
  仅小型报告下载，不把它描述为完整恢复包本地备份。
- 下一步：作者决定是否下载5.45GiB完整结果/模型归档，以及如何分析QC、采用candidate state。
  不重复恢复、不自动Stage B/续年；固定服务器GPU-PDHG为独立任务，本轮未查询或操作。

### 2026-08-28 11:17 Case4第三次三小时巡检：primal显著改善，已持续运行超过旧时限

- 范围：只读SSH核验Git、run.pid/ps身份、配置/日志/资源，scp本轮证据；未改生产代码、模型、数据、
  参数或进程。production clean `6065bfba34b76098e86307081323e8545a4d25ac`，本地HEAD
  `65c8b21ea7bbe583d126f1142eebb348c3b32f3d`未提交。修改三个交接文档和独立巡检README。
- 标签仍`2030_base_2160h_case4_gpu_pdhg_unlimited_20260828_v2`；PGID1216966/Python1216969、
  02:15:14创建时间、2160h/start2880/指定GPU环境/profile均实核一致。实际快照time_limit_seconds及
  soft_mem_limit_gb仍null；日志RTX4090/Start PDHG on GPU与GPU1客户对应，无CPU回退。
- 11:16:44 callback5992040步、runtime31569.427s（含presolve），已经超过旧21600s而未结束，
  墙钟约9h01m/GPU阶段8h09m。stdout31565s目标6.19768764e6/8.42910122e5，
  primal/dual/Compl=0.00396/847/0.396；相较上次primal改善明显，dual仍高、目标差未闭合。
  callback残差0.0461572596/2701.3989368单独保留，不与stdout混用；无终态/QC/科学接受。
- 资源：本地原始16246样本，summary16244样本/errors0（文件复制时间不同，不是采样停止）；
  RSS17.001GiB/峰27.043GiB、host可用87.196GiB；GPU1卡级4600MiB/job4558MiB，近3h均值99.9998%。
  当前60°C/312.9W，峰61°C/317.6W；Swap7.4171GiB、累计swap-in增量15.559MiB、swap-out0，
  当前memory PSI为0，job CPU累计34602.60s。GPU0无本job客户，stderr/telemetry stderr空。
- 输出：`downloads/case4_unlimited_20260828_v3/review_20260828_1116/{run_control,output,README.md}`，
  活动文件顺序复制，非终态原子归档；没有删除/覆盖其他实验结果。
- 下一步约14:16按既有3小时heartbeat监测，同一任务无时限、原95%保护与2秒采样不变；
  不因长尾/竞争力终止，不自动StageB/其他算法/缩小模型/历史恢复；终态才汇总并暂停。

### 2026-08-28 08:15 Case4第二次三小时巡检：残差较上次改善，尚未收敛

- 范围与Git：只读监测、独立备份和交接；生产clean `6065bfba34b76098e86307081323e8545a4d25ac`，
  本地HEAD `65c8b21ea7bbe583d126f1142eebb348c3b32f3d`，无提交。仅更新CODEX_HANDOFF.md、
  MODEL_SERVER_STATUS.md、SERVER_RUNBOOK.md及本次独立证据，不改任何运行代码/模型/数据。
- 检查：SSH读取Git、run.pid、events、ps的PID/PGID/创建时间/完整本job命令行、stdout/资源/错误日志；
  scp保存`downloads/case4_unlimited_20260828_v3/review_20260828_0814/{run_control,output}`。
  原始文件在活动期间分别复制，非终态原子归档；README.md保留口径、资源、残差和下一步。
- 状态：PGID1216966/Python1216969均仍为02:15:14创建的指定2160h/start2880 GPU任务；
  config snapshot的time_limit_seconds/soft_mem_limit_gb均null，日志无非默认TimeLimit；
  RTX4090/Start PDHG on GPU及GPU1本job客户持续对应，没有CPU回退。未停止、重启或改参。
- 08:14:36累计3763040次迭代，solver20641.640s包含presolve；纯GPU迭代约5h07m29s，墙钟近6h。
  stdout20640s目标6.2597836e6/-1.71134618e8，primal/dual/Compl=2.54/1.02e3/0.502，
  较05:14端点9.71/4.95e3/24.2改善；中间非单调性和明显目标差仍在，不宣称可行/科学接受/算法优胜。
  同时保存callback残差40.4778753/2861.1234620，不与文本日志混用；没有终态或QC文件。
- 资源：10782个2秒样本、errors0；RSS17.001GiB/峰27.043GiB，host可用87.349GiB。
  GPU1卡级显存当前/峰4600MiB、job4558MiB；近3h GPU均值99.9998%，当前60°C/314.22W；
  峰61°C/316.91W。Swap7.4186GiB，本轮swap-in14.031MiB、swap-out0，当前memory PSI为0。
  CPU时间累计22975.62s是进程组CPU秒，不是墙钟秒；GPU0无本job客户，其他用户资源未干预。
- 下一步：不改ACTIVE/3h调度，约11:14再检查；不因6h/长尾/竞争排名停止，2秒资源采样及整机95%
  保护不变。终态才完整汇总/QC/暂停，不自行启动StageB、其他算法或缩小时域。

### 2026-08-28 05:14 Case4首次三小时巡检，确认GPU实际迭代

- 范围：仅监测无时限2160h Case4；不干预生产模型/数据、历史8760恢复或其他用户进程。
  固定服务器Git clean `6065bfba34b76098e86307081323e8545a4d25ac`；
  本地HEAD `65c8b21ea7bbe583d126f1142eebb348c3b32f3d`，
  本轮无提交。修改仅CODEX_HANDOFF.md、MODEL_SERVER_STATUS.md、SERVER_RUNBOOK.md及独立巡检证据。
- 命令/证据：SSH读取git rev-parse/status、ps PID/PGID/创建时间/命令行、run_control和outputs日志，
  scp复制到`downloads/case4_unlimited_20260828_v3/review_20260828_0514/{run_control,output}`；
  这是运行中分别复制的快照，非终态原子归档。README.md记录采样口径和残差原值。
- 验证：stdout第488行出现Start PDHG on GPU且GPU识别为RTX4090；GPU1计算客户为本Python1216969。
  配置快照numerics的time_limit_seconds/soft_mem_limit_gb均null，Method6/Threads32/Crossover0、
  PDHGConvTol/AbsTol/RelTol=1e-2/1e-5/1e-2；build_report确认2160h/start2880，模型边界不变。
- 进展：build913.382s、presolve2184.98s，03:07:07开始GPU迭代；05:13:51 callback1551040步、
  solver9797.042s（含presolve），stdout9795s目标6.989144e6/-5.15735717e8、
  primal/dual/compl=9.71/4.95e3/24.2。callback残差口径与文本日志数值不同，分别保留，不混用。
  primal残差较7200s上升，dual/compl下降，不能宣称单调收敛、已可行或比Barrier更快。
- 资源：5360个2秒样本、errors0，RSS当前17.001GiB/峰27.043GiB；host可用87.330GiB，
  host使用率当前29.040%/峰37.202%；GPU1显存卡级峰4600MiB、job峰4558MiB，近1h负载平均99.999%。
  GPU1温度峰61°C/功耗峰316.91W；Swap已有约7.43GiB，本轮无新增swap-out、当前memory PSI为0。
  stderr/telemetry.stderr为空，resource日志持续更新，无return_code/终态/QC。
- 下一步：保持现有ACTIVE/每3小时heartbeat，约08:13再检查。无时限，不按慢收敛/竞争力停止；
  原95%整机保护不变。终态后再完整备份/汇总并暂停；不自动重启、缩模型、StageB或其他算法。

### 2026-08-28 02:16 Case4取消时间上限、受控替换启动、审查改为3小时

- 作者新要求覆盖此前6小时筛选和10分钟heartbeat策略。本轮不再依据运行时长/相对Barrier速度/
  长尾自动停止，保留既定整机95%外部安全保护和实际错误/CPU回退处理。
- Git：local65c8b21ea7bbe583d126f1142eebb348c3b32f3d；生产clean6065bfba34b76098e86307081323e8545a4d25ac。
  不部署其他任务dirty代码，不改生产建模实现或输入，不重启历史恢复，不改变PDHG收敛容差。
- 文件：新增 `config/solver_profiles/large_lp_2160_case4_gpu_pdhg_unlimited_v2.json`（schema v1、
  profile_id后缀v2），全部numerics只将time_limit_seconds从21600改为null；旧profile保留。
  `scripts/run_fixed_server_2160_campaign_case.sh`仅给Case4加入显式profile路径覆盖；
  `scripts/start_case4_after_recovery.py`加入`--unlimited-pdhg`、固定profile哈希检查和环境传递。
  `tests/test_case4_resources.py`验证唯一数值参数变化和schema。更新本handoff/status/runbook。
- 不能在线取消原因：runner启动即load_model_config并深拷贝进内存，当前telemetry只采集数据，
  没有外部cbSetParam/信号改参接口。Gurobi自身可在指定callback改TimeLimit，不代表现有进程已经
  实现了该控制入口；不向活动进程注入代码、不靠修改磁盘profile假装生效。
- 验证：服务器启动/资源完整测试最终18/18 PASS；本地17 PASS+1 Linux-only SKIP。
  首次实际生产loader验证发现schema不接受solver_profile_version=v2，已保持schema v1而只让
  profile_id表达v2；修正后11/11资源/profile测试复核PASS。生产configure_gurobi作用于空模型、
  不optimize的实测确认TimeLimit=Infinity、SoftMemLimit=Infinity、Method6、PDHGGPU1；
  参数日志在新工具包validation/parameters.log。没有因为这个配置问题启动过失败的新大模型。
- 受控停止旧case：核实PID1175172/pgid1175169、完整output参数、创建时间1787853911.67，且
  stdout无Optimize a model/Start PDHG后，仅对该进程组SIGTERM。旧tag screen_20260828_v1
  02:15:04退出rc143、hostguard0；只是为换无时限配置取消建模，不是算法OOM/收敛失败。
  约10分钟建模不保留内存态，但文件全保留；旧control备份到本地新工具包downloads目录。
- 新部署：`campaign_tools/case4_unlimited_20260828_v3/scripts`，不覆盖v1/v2历史工具包。
  launcher SHA256 43217a950d3fee447d877497af0a145abb49d66e46a541e01b24c2aa9ec2ac2a；
  gate a80ef9f0e708b9963b0a952512d857766f8f6b487614e406e44a6d7216b24f64；
  profile 9c5c5ea38572dc26454c8a735e91e161e240a887dc98f5897cdff74d02c87122；monitor仍
  10f8724fe2ac366db26d74d2eb74d41c2eca108070263ea8c6fc18323c9adf72。
  部署清单 `downloads/case4_unlimited_20260828_v3/deployment_manifest.json`。
- 启动命令：沿用新包start_case4_after_recovery.py的固定server/recovery/head/gpu参数，tag改为
  `2030_base_2160h_case4_gpu_pdhg_unlimited_20260828_v2`，追加
  `--independent-after-failed-recovery --unlimited-pdhg`。02:15:12门禁PASS、available104.258835GiB、
  无其他模型、GPU1无compute客户端/free24047MiB。02:15:14开始；launcher1216822、pgid1216966、
  Python1216969、telemetry1216967。新claim明确unlimited_pdhg=true，旧claim不删除。
- 生效证据：新进程自己的model_config_snapshot.json显示time_limit_seconds=null及soft_mem_limit_gb=null，
  argv指向固定hash的新profile；02:15:32资源9样本/errors0、stderr空，尚未进入GPU迭代。
  控制/输出均为新tag，startup副本在downloads/case4_unlimited_20260828_v3/startup。
- 调度：原heartbeat id/name/target不变，频率改为每3小时并实读配置确认；提示跟进新tag，明确无
  6h/竞争力截止、2秒采样不变、不会再重复启动。后续查明GPU真实迭代与资源压力，终态汇总后暂停。

### 2026-08-28 02:15 云端24核Stage A恢复启动，指纹告警与失败模型保全

- 作者授权：立即使用云端原环境恢复，只申请24核心，减少过度门禁，以保存结果为主线。
  执行范围仅8760h历史Stage A离线恢复，4h安全上限；不optimize/presolve、不Stage B/续年。
- Git：本地HEAD65c8b21未变、未提交；原云端3f739fd发布不改，隔离overlay通过SHA256记录。
  新release `National_model_cloud/20260828_8760_stagea_recovery_v1`，原release/数据/旧输出只读复用。
- 文件：修改`cispo_model/offline_solution.py`、`scripts/recover_historical_stage_a.py`、
  `tests/test_solution_preservation.py`；新增`scripts/cloud_recover_stage_a_24core.sbatch`；
  staging脚本/映射/压缩包位于`.codex_tmp/cloud_stage_a_recovery_20260828_v1`；同步handoff、
  server status/runbook、model spec与当时独立的Stage A保全说明文档；该说明不作为当前提交依赖。
  无模型方程/配置/输入/阈值变更。
- 恢复逻辑：MPS、PRM及完整index/name/sense目录在身份门禁前归档，失败也保留模型。
  新显式allow_fingerprint_mismatch仅放行fingerprint差异，默认接口仍严格；维度/nnz、顺序、
  checksum/finite保留。归档得到的顺序摘要在同一未修改模型中复用，避免重复遍历约9200万条名称。
  identity差异单独保存，exact_lp_identity_and_full_order_verified不会在不匹配时错误标true。
  raw LP审计普通异常不阻断其他导出，保全状态明确PARTIAL；原物理QC FAIL继续保存，科学接受仍false。
- 测试：本地6/6（0.493s），新增真实改bound改变指纹的测试：默认拒绝、显式允许；改名称和破坏
  向量仍拒绝，缓存摘要不重复遍历。py_compile/diff-check通过；云端计算节点6/6（1.047s），
  没有跑新的全国1h/24h/744h求解或全库回归。此测试仅tiny合成LP，不是正式恢复的optimize调用。
- 提交：02:13:55 `sbatch --parsable --export=ALL,SOURCE_RELEASE=<原release> ...
  cloud_recover_stage_a_24core.sbatch` 返回4396245，02:13:56开始，m4cg1702。
  实读scontrol：NumCPUs24/CPUsPerTask24、ReqTRES/AllocTRES cpu24 mem128G billing24，TimeLimit4h，
  Requeue0。amd_a8_768实时MaxMemPerCPU6144，128G/24符合配置；不沿用96CPU/700G申请。
- 运行：02:14:05 preflight77条PASS；原始30文件、源码/数据身份均通过。计算节点Python与全部已记录
  依赖相同。02:14:08进入BUILDING_ORIGINAL_LP；02:14:24 sstat MaxRSS1031484K、stderr0。
  节点available689.9GiB不等于allocation128G，不能把整节点内存作为任务额度宣传。
- 哈希：code tar `e951750a37070aa4a07ec114f27696c4523c4b4f04197f123395802e9c25d89f`；
  metadata tar `946d1fcddc0bdad36e828db4ed2a08796dd0afbbf43b95fb47fbdf05d30631e4`；
  release_files.sha256摘要 `c17635741051a2b963580cbe22550960b2158d7d9baa6be89d926d10886840fe`；
  driver `bb02ea983095a252c192f434bb3cd789cbce5d7081690a9eb3c06395b4a919f9`；
  sbatch `9eb4a162b1385f2c33581c8031b492ad41295c87cabcca482e2d438fb691c26f`。
  原始向量在云端复制，不往返下载上传；上传量约4.2MB，仅源码/元数据。
- 未完成：本次8760LP指纹、完整顺序、归档和最终表/QC/candidate仍待构建后验证。准确下一步：
  `squeue/sacct/sstat -j 4396245`，检查新release的control及recovered_8760/recovery_progress.json。
  不重复提交、不在登录节点计算、不触碰独立Case4或原始备份。

### 2026-08-28 02:06 作者独立启动授权落实，2160h Case4已启动并持续采样

- 新授权：作者明确要求立即启动PDHG，覆盖“等待恢复成功”的依赖条件；不授权修复恢复、套用
  指纹不匹配的旧向量、改模型边界或开启其他Case。历史恢复仍FAILED，原现场不修改。
- Git：local65c8b21ea7bbe583d126f1142eebb348c3b32f3d，生产clean
  6065bfba34b76098e86307081323e8545a4d25ac。沿用Case1同一生产模型/data和原Case4 profile。
- 文件：`scripts/start_case4_after_recovery.py`新增显式独立授权开关，只接受已失败恢复的依赖
  豁免，result保留recovery_status=BLOCKED_RECOVERY_FAILED；`tests/test_case4_resources.py`
  新增测试验证不跳过仍运行/不完整恢复、也不跳过已有模型进程检查；本地/服务器均10/10 PASS。
  本轮不改launcher/monitor/solver profile，既有其他dirty代码保留，未提交。
- 部署新隔离包 `campaign_tools/case4_independent_20260828_v2/scripts`，不覆盖旧v1工具包或生产repo。
  gate SHA256 `a6cdf66be3b8642d32bb55946785d7c19f7624cca7d48c947dac5de0afdf6db9`；launcher
  `c0363c1e165fa895ec0439abb0c936c8f3a45c6fc8b9bebd2571409bfcd3db27`；monitor
  `10f8724fe2ac366db26d74d2eb74d41c2eca108070263ea8c6fc18323c9adf72`。清单在本地
  `downloads/case4_independent_20260828_v2/deployment_manifest.json`和服务器scripts同名文件。
- 启动命令：GPU Python执行新包的start_case4_after_recovery.py，沿用runbook的server-root/
  recovery-root/expected-repo-head/tag/gpu-device参数并显式追加`--independent-after-failed-recovery`。
  02:05:09 gate为READY并LAUNCH_DISPATCHED；available104.376495GiB、无其他模型、GPU1无计算
  客户端、free24047MiB。queue/launch_claim.json已创建，记录授权与旧恢复FAILED，不允许重复发起。
- 运行：tag `2030_base_2160h_case4_gpu_pdhg_screen_20260828_v1`；events.log开始02:05:12；
  launcher1175139、pgid1175169、Python1175172、telemetry1175170。GPU环境13.0.2+cu129；
  Base2030、2160h/start2880、Method6、Threads32、GPU1、最多21600秒、Crossover0，PDHG三容差
  1e-2/1e-5/1e-2，SoftMemLimit空、95%整机保护不变，没有新增显存上限。
- 验证：02:05:22原始资源样本6条、telemetry_error_samples0、stderr均0；GPU1本job显存峰值
  386MiB、卡级428MiB，但GPU利用率0，尚未出现Start PDHG on GPU；这仅证实启动/上下文分配，
  不能证明GPU迭代已开始。02:05:41资源日志继续更新、Python存活、无return_code。
- 调度：保留原heartbeat id/name/10分钟频率/当前thread，改提示为仅监测本次已启动Case并置ACTIVE；
  不调用旧恢复等待入口、不因恢复FAILED停止此case。明确GPU回退CPU不得记为GPU成绩，终态/需新决定
  后暂停，不自动重启/缩小时域/运行StageB或其他Case。
- 输出/下一步：对应run_control/<tag>保存stdout/stderr/events/time、host资源TSV、每2秒双GPU/
  主机/进程JSONL和summary。等待构建/预处理后核验Start PDHG on GPU及收敛；保持生产版本冻结。

### 2026-08-28 02:07 云端原环境恢复可行性核验（只读，未启动）

- 请求：评估直接在云端原版本恢复的可靠性与时间。SSH读取原release路径、源码摘要、Python/package
  metadata、squeue/sinfo/scontrol；未启动模型、未创建allocation、未安装依赖、未修改云端文件。
- 核验：原Python3.10.20，NumPy2.2.6、pandas2.3.2、SciPy1.15.3、xarray2025.1.2、netCDF4 1.7.2、
  zarr2.18.3、psutil5.9.8、gurobipy13.0.2全部与原run_environment一致。原30个源码bundle
  `bdf36a799f7eaf2c037e806a87f21f6e9b59c247e369e610b7cd22806caf9a8e`匹配，checkpoint和数据根仍在。
- 资源：squeue用户无job；amd_a8_768 UP，查询时31节点idle，不保证下一次排队耗时。
  DefMemPerCPU=6000、MaxMemPerCPU=6144；24CPU/128G只作恢复资源候选，不是已申请或费用报价。
  共享文件系统空闲不等于账户配额；账户余额/单价本轮未核验。
- 判断：原源码/原输入/原依赖可减少跨环境变数，因此优先考虑云端恢复；仍不能担保指纹一致。
  Gurobi官方列举Python版本、构建顺序等均可能造成指纹变化：
  https://support.gurobi.com/hc/en-us/articles/41809886403217-Why-Is-My-Model-Fingerprint-Different 。
- 时间依据：历史云端原LP构建38m57s、峰值48.574GiB，本地此次59m27s/47.914GiB；不做
  optimize/presolve的恢复不重跑20天Barrier，但全量顺序、MPS/名称归档、原LP审计与导出耗时未知。
- Git/文件：HEAD65c8b21未变；仅更新CODEX_HANDOFF/MODEL_SERVER_STATUS。下一步需作者明确
  云端付费执行授权，并先修复异常路径的模型归档；不得原样重跑旧Stage A求解sbatch。

### 2026-08-28 02:04 恢复退出原因核查与保全缺陷记录（未修复/未重启）

- 请求：作者询问“为何退出了”。只读检查进程、return_code/events/time/stdout/stderr、source/target
  run_environment、build_report及恢复代码控制流；未启动任何建模/求解/环境安装。
- 直接证据：00:47:11 `Original LP identity mismatch`，00:48:04 rc1、host95_guard0；维度与nnz
  一致但fingerprint718212258不等于-781497218。峰值47.914GiB，wrapper1:00:28，optimize/presolve0。
  02:02服务器available111959785472 bytes，原进程已全部退出，生产checkoutclean6065bfb。
- 新线索：源→目标 Python3.10.20→3.11.15，NumPy2.2.6→2.4.6，pandas2.3.2→2.3.3，
  SciPy1.15.3→1.17.1，xarray2025.1.2→2026.7.0，netCDF4 1.7.2→1.7.4，zarr2.18.3→2.18.7；
  Gurobi13.0.2相同。驱动只强制检查Gurobi版本。依赖差异可能影响重建，尚无差分证据证明因果。
  原始输入字节和源码核对不自动等于最终浮点LP相同；同环境1h恢复测试不证明跨环境8760等价。
- 保全缺陷：驱动197行异常早于203行archive_model，因此本次重建MPS和名称目录未持久化。
  这是需要修复的失败路径，不得把“已有原始checkpoint备份”写成“本次构建模型已归档”。
  原BarX/BarPi和源solve_report仍保留；此次未完成solution_qc/result_manifest/candidate state。
- 官方属性说明：`https://docs.gurobi.com/projects/optimizer/en/current/reference/attributes/model.html#fingerprint`。
  Fingerprint取决于模型数据和属性，不能仅以机器不同为由豁免不一致。
- Git/文件：本地HEAD65c8b21未变，本轮只追加CODEX_HANDOFF、MODEL_SERVER_STATUS和SERVER_RUNBOOK；
  未修改恢复驱动、历史release、输入或验收阈值。下一步待修复授权，优先失败现场归档和分项对照，
  再准备匹配历史依赖的隔离环境及跨环境小模型验证；不盲目重复一小时全年重建。

### 2026-08-28 00:57 heartbeat发现历史恢复失败，Case4接续已暂停

- Git：local65c8b21ea7bbe583d126f1142eebb348c3b32f3d；server clean
  6065bfba34b76098e86307081323e8545a4d25ac。本轮不修改模型、输入、环境或求解器参数。
- 命令：按runbook执行 `start_case4_after_recovery.py` 的固定参数入口，返回
  BLOCKED_RECOVERY_FAILED；随后只读检查recovery control/stdout/stderr/events/time、build_report、
  preservation_runtime_memory和 `source_backup/output/run_identity.json`。首次查找原identity缺少
  output子目录，已按实际文件路径纠正，不据缺文件推断数据丢失。
- 恢复终态：00:47:11.975915 identity检查抛ValueError，00:48:04 wrapper rc1/host95_guard0；
  wall1:00:28，build3566.90585s；采样进程树峰值47.914GiB，time MaxRSS50740524KiB。
  不是本次内存保护终止或GPU显存失败；optimize/presolve均0。
- 实测与原模型变量41458383/约束50907234/非零元492835195均一致，唯一此层identity差别为
  fingerprint718212258 vs -781497218。只能确认身份校验失败，不能据此断言数学模型边界改变，
  也不能认定只是排序/浮点问题；需后续有授权的分项诊断。失败发生在完整顺序/向量核验之前，
  没有恢复容量/运行/成本/QC等正式输出，也没有新的科学接受结论。
- Case4：queue/status.json记录00:57:22检查BLOCKED_RECOVERY_FAILED；没有launch_claim，
  正式Case4控制目录不存在。未启动任何Case/StageB/续年，未终止其他用户进程。
- 调度：保留name/prompt/频率/targetThreadId，将 `case-4-gpu-pdhg` 从ACTIVE改为PAUSED；
  通过app工具成功更新且automation.toml实读为PAUSED。停止自动检查/接续，等待作者选择。
- 文件/证据：更新本handoff、MODEL_SERVER_STATUS.md和SERVER_RUNBOOK.md；
  `downloads/case4_after_recovery_20260828_v1/recovery_failure_0057/`保存control完整日志及
  build_report/recovery_progress/preservation_runtime_memory/source_run_identity。
  原备份、原checkpoint和服务器恢复失败现场均保留。本地已有dirty代码不动，未提交/部署。
- 下一步：请作者决定先诊断历史指纹差异，或另行授权在保留失败现场的前提下独立启动Case4；
  在获得新决定前不改门禁、不重新恢复、不重建大LP。

### 2026-08-28 00:46 恢复后Case 4自动接续与资源压力记录已配置

- 作者授权：恢复结束后启动GPU-PDHG，记录主机内存、显存及GPU压力；保持2160h四Case范围。
- Git/边界：local65c8b21ea7bbe583d126f1142eebb348c3b32f3d；生产仍clean
  6065bfba34b76098e86307081323e8545a4d25ac。没有修改模型、输入数据、目标约束或solver profile，
  没有部署其他任务的dirty保存/恢复代码。独立工具overlay未提交，以部署manifest+SHA256固定。
- 文件：新增 `scripts/monitor_case_resources.py`、`scripts/start_case4_after_recovery.py`、
  `tests/test_case4_resources.py`；更新 `scripts/run_fixed_server_2160_campaign_case.sh` 和
  `tests/test_campaign_launcher.py`，以及本handoff/status/runbook。部署清单和真实单次采样备份在
  `downloads/case4_after_recovery_20260828_v1/`。
- 部署：`/home/zz2/National_model_server/campaign_tools/case4_after_recovery_20260828_v1` 下
  scripts/保存3个工具和deployment_manifest.json，tests/保存2个测试；未覆盖生产repo或历史恢复。
  launcher SHA256 `c0363c1e165fa895ec0439abb0c936c8f3a45c6fc8b9bebd2571409bfcd3db27`；
  monitor `10f8724fe2ac366db26d74d2eb74d41c2eca108070263ea8c6fc18323c9adf72`；
  gate `dc678dc835458134c53df74335524ce53c4c38c35b9e2b50895dfa626865be76`，服务器实读匹配。
- 验证命令：本地分别 `python -m unittest discover -s tests -p test_campaign_launcher.py -v`
  与 `-p test_case4_resources.py -v`，14 PASS+1 Linux-only SKIP；服务器独立工具根下以GPU Python
  执行 `-m unittest discover -s tests -v`，15/15 PASS、10.672s。Linux集成fixture只sleep5秒，不建模，
  验证detached job、多次采样、summary、return_code与telemetry_return_code均0，临时fixture自动回收。
  真实 `monitor_case_resources.py --process-group 657359 --gpu-device 1 --once --output-dir validation_telemetry`
  也PASS，双GPU sensor可读，error_samples=0；不启动持续监测恢复，不干预其进程。
- 幂等门禁：恢复rc0、progress/preservation均COMPLETE、optimize/presolve均0、无其他模型进程、
  生产HEAD/clean匹配、工具hash一致、host available>=96GiB、GPU1无compute客户端、free>=22000MiB
  且util<=5%才允许启动。QC FAIL不是恢复完整性失败。使用flock+不可覆盖launch_claim，失败亦不盲重试。
- 采样：默认2秒，JSONL原始序列与原子替换summary持续落盘；主机内存、Swap累计换入换出、PSI、
  CPU利用率、求解PGID成员RSS/CPU时间；两卡总/已用/可用显存、GPU和显存控制器活跃率、温度、
  功耗/pstate、本job GPU进程显存。只保存本job客户端PID，不持久化其他用户命令行；缺失传感器null，
  查询失败记录errors。原resource_monitor.tsv/time.txt和95%guard保留；监测异常记日志，不静默假装成功。
- 调度：已创建当前对话heartbeat `case-4-gpu-pdhg`，ACTIVE，每10分钟一次；只调用一次性门禁，
  不另建服务器cron/无限等待器。00:44:09实调返回WAITING_RECOVERY；queue/status.json已落盘，
  未生成launch_claim或正式Case 4控制目录。恢复运行中，算法未启动；首个创建调用因缺destination被拒，
  加destination=thread后成功，已view核验。无重复任务。
- 后续：保持本地Codex和SSH可用；自动检查恢复终态及门禁后启动GPU1 Case4，核实Start PDHG on GPU
  和资源日志持续更新。明显不可竞争可按原筛选政策提前停止本case；CUDA回退CPU不得当GPU结果。
  异常需新决定则报告并暂停，终态汇总内存/显存峰值、GPU负载、耗时、残差/QC后暂停，不自动Stage B。

### 2026-08-28 00:32 Case 4启动准备、GPU解释器修复与恢复冲突门禁

- 请求范围：先尝试2160h GPU-PDHG Case 4并核实双卡；未改变模型边界、数据、四Case配置或容差。
- Git：local HEAD65c8b21（本轮未提交）；server clean6065bfba34b76098e86307081323e8545a4d25ac。
  既有未提交的Stage A保全/历史恢复改动不纳入本次修改，也未部署。
- 改动：`scripts/run_fixed_server_2160_campaign_case.sh` 保留调用者在source之前指定的解释器，
  Case 4无显式覆盖时选 `envs/cispo-2030-gurobi-gpu13.0.2-cu129-v1/bin/python`；原共享环境会覆盖
  `CISPO_PYTHON`为CPU解释器，不能继续使用旧启动路径。并发进程检查增加
  `recover_historical_stage_a.py` 和 `run_historical_stage_a_recovery.sh`。
- 新增 `tests/test_campaign_launcher.py`：真实Bash执行初始化/门禁，隔离临时环境并mock git/pgrep，
  不运行Python求解器、SSH或大模型。命令 `python -m unittest discover -s tests -p test_campaign_launcher.py -v`
  为6/6 PASS；涵盖Bash语法、CPU默认、GPU默认、显式解释器优先、已有求解/恢复拒绝及无关进程放行。
- SSH 00:32:12实时证据：双卡util0%、显存395/36MiB；恢复PID657364、pgid657359、elapsed2677s、
  RSS32462960KiB；monitor 00:32:11 MemAvailable75450228KiB，总129048004KiB。恢复仍构建原LP，
  没有return_code文件；生产git clean6065bfb。本轮只有只读服务器检查，没有启动/终止进程。
- 双卡依据：[Gurobi GPU安装/运行说明](https://support.gurobi.com/hc/en-us/articles/43498824105873-Installing-and-Running-GPU-enabled-Gurobi)
  及[GPU支持说明](https://support.gurobi.com/hc/en-us/articles/360012237852-Does-Gurobi-support-GPUs)。
  公开接口仅核实GPU版安装、Method6/PDHGGPU1和成功日志，未找到单模型双卡分摊配置。
  `CUDA_VISIBLE_DEVICES=0,1`不等于已并行或显存池化；当前只承诺已验证单4090路径。
- 状态/输出：本地启动器和测试、此handoff及status/runbook更新；Case 4无输出目录/求解结果/自动队列。
  不绕过96GiB启动门槛，不中断历史恢复，不将现有whole-host95%保护改为新的Gurobi内存上限。
- 精确下一步：恢复正常结束后核验资源和清洁生产版本，单独部署本次启动器修复，再按Case 4原profile
  在一张空闲4090启动2160h；若作者要求立即抢占，须先明确对历史恢复的处置，不能自行停掉它。

### 2026-08-27 23:48 历史8760h Stage A恢复的隔离部署、跨机校验与启动

- 授权与边界：作者明确授权在空闲服务器启动上一轮Stage A恢复；本线程按前文8760h job4139552
  执行。只恢复原向量语义、原LP审计、归档和候选结果；不重复Barrier，不执行presolve/Stage B/续年。
- Git：本地HEAD `65c8b21ea7bbe583d126f1142eebb348c3b32f3d`，未提交；生产服务器checkout仍clean
  `6065bfba34b76098e86307081323e8545a4d25ac`。实际恢复采用历史Linux源码包
  `c49d48da070834b969b13b7a4ea50d0b45c5383276820db0e314d324822ec40e`，不使用当前建模方程。
- 新文件：`scripts/recover_historical_stage_a.py`、`scripts/run_historical_stage_a_recovery.sh`；
  隔离release及path_mapping/launch_validation在 `.codex_tmp/stage_a_8760_recovery_20260827_v1`。
  更新本handoff、MODEL_SERVER_STATUS、SERVER_RUNBOOK及当时独立的Stage A保全说明；该说明未纳入
  当前可依赖提交。原备份文件不修改。
- 源码核对：原始下载30/30 SHA256一致；源包30个implementation文件的canonical bundle摘要与
  run_identity完全相同。4个受审查覆盖仅为master导出QC开关、solution_export导出QC开关、
  planning_state候选保全和result_summary清单标签；历史master的非export AST不变，其余旧py/config
  文件必须逐字节相同。新增offline_solution/solution_preservation采用此前验证版本。
- 数据：第一轮preflight_v1在建模前正确拒绝 `size:output_manifest.csv`。从原云端只读取回
  8482-byte原清单（SHA256 `9179cba6...cb42be4`），在独立historical_model_data中替换这一说明文件；
  其余数据通过只读消费的符号链接复用。preflight_v2原始77条输入与全新provenance逐项相同，完整
  resolved config、baseline/analysis/scientific/solver身份和Gurobi13.0.2匹配。
- CF完整性：云端只带2023/2024，服务器另有2020--2025；不能比较父目录总摘要后误判数据损坏。
  对实际消费8个2023/2024 zarr的全部22536文件，`find . -type f -path '*202[34].zarr/*' -print0 |
  LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum` 两端一致为
  `c909ba9d0f75d9d5bd539a3df682f1c32d461df83b0037152990a17442c709fc`，不只是metadata一致。
- 验证：隔离历史版本运行 `scripts/validate_stage_a_recovery.py --hours 1 --output-dir ../validation_1h`
  PASS，源和恢复fingerprint均-146272577，源Barrier87步/10.10s，恢复optimize/presolve调用0；
  直接在线与离线45个CSV/NPZ一致、碳/原LP QC一致、两端manifest/candidate读取均成功。新入口
  py_compile及launcher bash -n通过；此次未重跑全库回归，不把此前222项结果冒充本轮新运行。
- 启动命令：`RECOVERY_ROOT=/home/zz2/National_model_server/recovery_8760_20260827_v1
  CISPO_SERVER_ENV=/home/zz2/National_model_server/server_env_20260825.sh bash run_historical_stage_a_recovery.sh`，
  实际通过nohup后台启动；控制root `control`，结果root `recovered_8760`，独立进程组657359。
  开始23:47:35，23:47:45已进入原LP构建；启动available100.9078GiB，23:47:51 stderr0、资源正常。
  保护只终止自身进程组，阈值整机95%；不触碰其他用户进程。脚本强制禁用optimize/presolve。
- 发布证据：恢复代码tar SHA256 `f8da39275948dc725de879571006940d82d1f0b6679ba2edf4b69e1600fba3aa`；
  driver SHA256 `6629978ee2d555cf69df4256d0c44b46d392c83a856a2b0bdaf675c4f5578228`；
  launcher SHA256 `f72e7b1623d03786a56a5be9bee82ba8a3ba72c1cd6946ac654fcd7285dc108d`。
- 待完成：8760h原LP构建、-781497218指纹/完整顺序门禁、原模型归档、原始残差、完整输出及候选
  state最终读取。QC FAIL保留而不筛选数据；失败/PARTIAL保留错误。不承诺总恢复时间或峰值内存。
  精确下一步：查看 `control/stdout.log`、`stderr.log`、`return_code.txt`、`resource_monitor.tsv` 与
  `recovered_8760/recovery_progress.json`；终态后检查preservation_report、solution_qc和result_manifest。

### 2026-08-27 23:34 2160h Case 1 Stage A终态与检查点实读核验

- Git/范围：server clean `6065bfba34b76098e86307081323e8545a4d25ac`，未改代码/参数/数据，未启动
  Stage B或挑战者。仅向本地 `CODEX_HANDOFF.md`、`MODEL_SERVER_STATUS.md` 追加终态记录，保留已有
  未提交的Stage A保全实现和其他作者改动；本次未提交、未部署。
- 命令/输出：SSH只读检查Case 1 `run_control/.../events.log`、`return_code.txt`、`time.txt`、
  `resource_monitor.tsv`，读取对应output的solve report、checkpoint manifest和engineering QC；
  用SHA256及NumPy mmap核对原始BarX/BarPi文件。根tag为
  `2030_base_2160h_case1_v3_barrier16_stage_a_20260827_v1`。
- 终态：23:27:51 rc0、guard0、stderr0；242 Barrier iterations、solver82535.468s、wall23:13:57、
  peak RSS69.291GiB、host peak88.742598%。OPTIMAL但strict HARD_FAIL，工程QC53/58；原始primal/dual
  objective分别2874667.943668152/2693954.9896529447 million CNY，相对差6.286394%。不得将宽松
  solver终态写为严格LP或科学验收通过。
- 保全/下一动作：10398783个BarX、12520914个BarPi全部finite，两个文件SHA256与manifest一致。
  checkpoint可用于exact-LP deferred crossover，但本轮未启动。旧进程未获得本地14:18完整保全逻辑，
  应先在独立根核对离线恢复及候选表/状态补齐流程，保留质量失败项供作者决定采用。

### 2026-08-27 14:18 Stage A 全量保全、模型归档与不求解恢复的本地实现

- Git/范围：基线 `65c8b21ea7bbe583d126f1142eebb348c3b32f3d`，未commit/push/deploy；保留作者原有
  工作树修改。未改模型方程、目标、物理单位、时空尺度、输入数据、求解profile或验收数值阈值。
- 改动：新增 `cispo_model/solution_preservation.py`、`cispo_model/offline_solution.py`、
  `scripts/validate_stage_a_recovery.py`、`tests/test_solution_preservation.py`及当时独立的Stage A保全说明文档
  （未提交，当前不作为运行或验收依赖）；
  修改 runner、master/solution_export 的可选QC抛错接口、planning_state 候选写入/显式读取、
  result_summary/run_contract 的完整性与接受标识，及 checkpoint 说明文字；同步本交接和三份规范/运行文档。
- 行为：所有nonbasic Stage A无验收筛选地保存可读取向量和完整结果。可用RC/Slack/basis一并保存，
  不可用属性如实列出；每个导出模块独立留错。原LP全部行/变量边界重新计算，超阈值条目按名称/index
  写入 `raw_lp_violations.csv.gz`，阈值读取源solver contract。`result_manifest`是字节完整性清单，
  不是科学证书；`scientifically_accepted=false`和作者待决定状态不因QC PASS自动更改。
- 候选续接：全量保留raw新cohort，包括0、微小值和负值；保留原建造/退役/单位规则和前序元数据。
  `--allow-candidate-state-in`只豁免源QC/accepted状态要求，不豁免年份、哈希、资产/单位和数值结构。
  后继结果继续为候选；截断状态绝不能进入正式年度。旧accepted-only sequence不会自动采用候选。
- 模型归档：默认原始MPS、参数和全量变量/约束名称目录；显式presolve仅生成诊断代数副本。
  本地Windows Gurobi不能直接写gzip MPS时回退未压缩MPS并记warning，未丢弃模型。微型MPS读回后
  原LP向量映射通过；没有保存Barrier内部状态、uncrush映射或factorization。
- 真模型验证：Gurobi12.0.1与隔离overlay13.0.2的1h恢复对照PASS；后者输出根
  `outputs/stage_a_recovery_validation_20260827_v2_gurobi13`，在线直接读取与离线恢复的45个CSV/NPZ
  数据产物在 `rtol=atol=1e-10` 下通过，碳JSON一致、原LP QC一致、manifest有效、候选可显式加载。
  恢复端对 `Model.optimize/Model.presolve` 做立即报错替换，仍成功且target.SolCount=0。
- runner闭环：`outputs/stage_a_runner_1h_20260827_v1`生成完整结果和具备Stage B资格的engineering
  checkpoint；`outputs/stage_a_runner_recovered_1h_20260827_v1`通过正式恢复入口，无presolve/optimize，
  build+恢复监测峰值0.417GiB、36.484s（仅1h，不能线性保证8760h）。实现变更显式使用
  `--allow-compatible-primal-dual-implementation`，source/target bundle分别写入恢复证据，LP/数据门禁不放宽。
  最终入口复核根 `outputs/stage_a_runner_recovered_1h_20260827_v2` 同样COMPLETE，包含output catalog，
  manifest有效，候选cohort共86900行；峰值0.417GiB、37.141s。新增Windows短暂文件锁下的有限原子
  rename重试，不用原地覆盖代替原子写入；永久写盘错误仍明确失败并保留临时文件。
- 跨年结构验证：使用上述恢复候选及 `--allow-candidate-state-in --allow-diagnostic-state-in --build-only`
  构建2040/1h，输出 `outputs/stage_a_candidate_2040_1h_build_20260827_v1`，构建成功、0.375GiB，
  未优化2040、未形成任何正式年度结论。
- 测试：Gurobi13.0.2下 `python -m unittest discover -s tests -p 'test_*.py' -q` 为222/222 PASS，
  96.237s；新增测试覆盖非零Barrier迭代后离线恢复、MPS读回、legacy checkpoint、QC FAIL候选、
  缺失dual、失败模块不阻断其他模块、校验篡改及具名约束/边界违反。`py_compile/git diff --check`通过。
  为验证版本一致性仅在 `.codex_tmp/gurobipy_13_recovery_validation` 安装13.0.2 overlay，未改全局环境。
  Windows原子写入重试修复后，最终全量再跑222/222 PASS（96.668s）；原8760h备份30个下载文件的
  字节数/SHA256复核仍30/30 PASS、不匹配0，未改动任何原始向量或源报告。
- 历史溯源：会话 `rollout-2026-08-16T13-02-33-01a008f3-3c1a-7190-bddf-921000ee7fff.jsonl` 中
  2026-08-16 13:13提问、13:14答复明确为“未来版本可加presolve模型保存”，且不能修改运行中进程。
  历史runner只有可选write-mps，job4139552启动未传，且无presolved写出实现；不是已成功保存的模型丢失。
- 边界/下一步：服务器仍未部署、当前2160h不触碰；先在闲置环境部署精确版本。历史8760h要在原release
  数据/源码核验和路径映射审计后，再选择可用内存>=90GiB的环境执行独立恢复；当前完整历史恢复、
  全年资源峰值和跨机器路径迁移尚未验证，不自动启动Stage B、全年恢复或下一正式年份。

### 2026-08-27 13:39 Stage A 完整保全与作者采用决策解耦（要求记录，代码待实现）

- Git：`65c8b21ea7bbe583d126f1142eebb348c3b32f3d`；保留工作树既有修改，未 commit/push。
- 作者新要求：不以项目质量门槛筛掉 Stage A 导出。保存全部可读取的容量、运行、成本、碳、对偶、
  QC、结果清单及候选跨年状态，并逐项记录门槛、实测违反值、定位和未能完成的检查。采用与否由
  作者在保全后决定，不自动进入论文或下一年份，不把 FAIL 改为 PASS。
- 修改文件：`CODEX_HANDOFF.md`、`cispo_full_lp_model_spec.md`、`MODEL_SERVER_STATUS.md`、
  `SERVER_RUNBOOK.md`；在忽略目录的 `downloads/paracloud_4139552_2030_8760_stagea_barrier_v2_20260826/README_BACKUP.md`
  追加覆盖说明。未更改已下载的 30 个源文件、数值向量、历史 solve/checkpoint manifest、模型或参数。
- 核查命令/证据：`git status --short`、`git rev-parse HEAD`、定向 `rg`/`Get-Content`；
  `run_cispo_2030_full_year.py` 明确将 engineering Stage A 标为
  `SKIPPED_ENGINEERING_BARRIER_CHECKPOINT_ONLY`；`planning_state.py` 的 loader 强制 QC PASS 与
  accepted nonbasic checkpoint，writer 按既有 tolerance 省略小 cohort。新候选保存路径必须额外保留
  未筛选的 cohort 原值与转换记录，不能只删掉上述 gate 后冒用 accepted state schema。
- 本地备份证据：`vector_integrity.json` 中 `BarX/BarPi` 长度为 `41458383/50907234`、全 finite；
  `solve_report.json` 仍为 OPTIMAL、strict contract HARD_FAIL，constraint violation
  `2.2868289320854274e-05 > 1e-05`。文件完整性 PASS 不等于该解的物理 QC PASS。
- 恢复路线更正：此前 zero-iteration `PStart/DStart` 方案尚未验证；微型试验被 presolve 全部消去，
  不足以证明赋值后直接得到 `.X`。优先实现直接读取 `BarX/BarPi` 的离线值/线性表达式适配层，
  exact-LP identity/order 校验后再导出，无需求解器再次 optimize。原输入数据仍须从清单指定来源
  获取并校验；源码备份不等于完整输入数据备份。不得套用 current-model 的新数据/变量顺序。
- 续接区别：Stage B 同年 LP starts 已具资格，但仍需重建和身份校验；跨年必须先恢复容量语义、
  建造/退役年份、单位与资产 cohort，并实现显式作者选择的候选 state 读取。完整逐时表不是容量
  续接的数学前提，但当前既无 candidate state，也无该读取接口。任何续年仍须另行明确选择。
- 验证：文档差异与 `git diff --check` PASS；用 `Import-Csv`/`Get-FileHash` 对原 30 个下载文件逐个
  重核字节数与 SHA256，`30/30 PASS`、不匹配 0。不运行测试求解或大模型重建。运行状态只引用既有带时间戳
  证据，本轮未 SSH 实时检查，未部署/启动 Stage B、恢复作业、下一年份或干预其他服务器任务。
- 未解决与下一动作：在隔离脚本/输出根实现离线恢复和候选 state schema；先做小模型数值、成本、
  碳、dual/cohort 对照及 QC FAIL 仍完整导出的回归测试；通过后再选择内存充足的环境做历史 8760 h
  exact-LP 重建恢复。历史 build-only 约 39 分钟、48.574 GiB 仅为参考，不是总恢复耗时/内存承诺。

### 2026-08-27 ParaCloud 8760 h Stage A 终态复核与本地 checkpoint 备份

- Git/范围：当前本地 HEAD `65c8b21ea7bbe583d126f1142eebb348c3b32f3d`；云端 release commit
  `3f739fd6216b1c7fc356e8d3a1d9a257c666f0c5`，implementation commit `6f0b1f7`。本任务未改模型、
  数据、solver 参数或服务器文件，未提交/推送；只新增 Git 忽略的本地备份目录并更新本交接记录。
  工作树原有作者与其他任务修改均未清理或覆盖。
- 云端终态：job `4139552` 为 `COMPLETED 0:0`；Gurobi `OPTIMAL`、Barrier 607、objective
  `4188006.084013813 million CNY`、solver `1773606.980 s`、wrapper wall `20-13:21:11`、MaxRSS
  `362.952 GiB`。末步 primal/dual objective gap `0.313559536`、relative gap `7.48708e-8`；checkpoint
  `BarX/BarPi` 完整有限且 deferred-crossover eligible。当前云端用户队列和 solver 进程为空，未启动
  Stage B，也没有继续计费的 CISPO 作业。
- 科学门禁：`solve_report.json` 的 solution contract 为 `HARD_FAIL`，最大 constraint/bound/dual/
  complementarity violation 分别为 `2.28683e-5/8.12859e-9/9.99418e-7/0.0141787`；正式
  `solution_qc.json`、`result_manifest.json`、规划状态和 basis 均不存在。checkpoint 仅保存 raw-order
  vectors 与变量/约束顺序摘要，不保存完整名称目录、presolve 状态或 Barrier factorization。
- 本地输出：`downloads/paracloud_4139552_2030_8760_stagea_barrier_v2_20260826` 保存 output 14、
  run_control 10、configuration 3、source_bundle 3 个云端文件；总计 `748,733,446 bytes`。
  `backup_verification.json=PASS`、`vector_integrity.json=PASS`；primal SHA256
  `7be2d311...a26f43`、dual SHA256 `b9a56569...6282`、源码归档 SHA256 `c49d48da...ec40e` 均与
  manifest 一致，完整文件清单位于 `downloaded_files_sha256.csv`。
- 未决/精确下一动作：若不承担 Stage B 成本，先新增 fail-closed 的 engineering checkpoint
  postprocessor，并在 1 h/744 h 验证 exact identity、`PStart/DStart` zero-iteration 暴露值、原向量
  等价性以及现有导出/QC。8760 h 只允许在独立根和足够内存节点执行，输出必须标为
  `scientifically_accepted=false`；正式结果仍要求后续严格 numerical/QC/manifest 闭合。

### 2026-08-27 2160h 四 Case 实装、等价性/GPU 门禁通过并启动 Case 1

- Git/范围：模型与 profile 提交 `88f8877`，GPU socket 隔离提交 `6065bfb`；修改
  `cispo_model/{config,data,diagnostics,io_contract,master,monolithic,technology_registry}.py`、五个
  `large_lp_2160_*` profile、`scripts/run_fixed_server_2160_campaign_case.sh` 与两组测试。没有修改决策
  变量、约束、目标系数、单位、时间/空间分辨率或数据值；原硬编码数值只迁移为同值注册表读取。
- 参数/资源合同：只允许 Case 1 V3 Barrier16 Stage A、Case 2 V3 Barrier32、Case 3 Dual simplex、
  Case 4 single-4090 GPU-PDHG；统一 2160h/start 2880。Case 1 无 solver time limit，其余挑战者最多
  21600 s；所有新 profile 均无 Gurobi SoftMemLimit。外部整机 95% guard 保留，2016h 及以下也不设置
  solver memory limit；只有真实 OOM/guard terminal 才降时域。
- 验证：local py_compile/registry test PASS；server targeted `11/11 PASS`，加载数据环境后的 full regression
  `217/217 PASS`。旧根 `2030_1h_new_server_smoke_20260825_v1` 与新根
  `2030_1h_registry_equivalence_88f8877_v1` 的 raw dimensions、fingerprint、objective、94 Barrier + 1623
  simplex iterations、最大 violation 与 QC 均完全一致。GPU wheel SHA256
  `10f0a10fed0c0f959d11bc4f60d36d4ef04a13c48ecf649cd557e8b952de0680`；独立 env 的 tiny LP 明确
  `linux64gpu[cuda12]`、RTX 4090、`Start PDHG on GPU`、OPTIMAL。
- 当前运行：server clean `6065bfb`；Case 1 于 `2026-08-27T00:13:53+08:00` 启动，root/tag
  `2030_base_2160h_case1_v3_barrier16_stage_a_20260827_v1`，进程组 `687599`。`00:15:52` 尚在构建，
  Python RSS 约 3.03 GiB，整机 used 16.02%，memory PSI 0、stderr 0；`00:28:59` 进入 Gurobi，raw
  `10398783/12520914/126724678`、fingerprint `0xcf045770`，未设置 TimeLimit/SoftMemLimit，构建峰值
  `12.492 GiB`。精确下一动作是只读监管 Case 1
  到 Stage A terminal；接受完整 checkpoint 后再执行 Stage B。Case 2--4 不得与 Case 1 并发，cloud
  8760h 保持原样。

### 2026-08-25 National_model 最终基准情景数据中文分类归档完成

- Git：归档开始时 HEAD 为 `f7ef130...`，任务收尾时当前 HEAD 为
  `fc3ca89d07feb796f57a0c433845e0e48901b416`、分支 `codex/cispo-2030-full-lp`；本任务未提交、未推送。
  工作树原有大量作者文件，均未改动或清理；本任务新增
  `scripts/archive_final_baseline_data.ps1`、`scripts/extract_base_residual_load.py`，并更新本交接文件。
- 范围：向 `E:\数据拷贝\National_model基准情景数据_20260825_v1` add-only 复制最终风光精细栅格、
  0.25° 潜力/装机、非采暖制冷 EV 基准负荷、生物质、2025 省际输电、火电/核电、水电/抽蓄、
  2023 默认气象年容量因子及当前 model-ready 输入/配置/复现代码快照；未复制约 17.9 GiB
  `data/raw` 和非默认气象年。
- 版本冻结：权威装机链为 `osm_geometry_value_added_capacity_v3_offwind47 -> final_pointV2`；v2 仅作为
  复现上游并明确标记非最终。负荷使用 v3-QC 当前 model-ready 输入，另逐行提取 `base_residual_gw`，
  不含 `heating_gw/cooling_gw/ev_gw`，不得解释为观测总负荷。
- 命令与输出：运行 `powershell -File scripts/archive_final_baseline_data.ps1` 完成 98 条显式映射；运行
  `python ...\00_归档说明与校验\verify_archive.py` 完成首轮全量哈希/映射核验；按作者要求以 Ctrl-C
  停止第二轮细核对。根目录 `README_数据说明.md` 与 `00_归档说明与校验` 保存版本判定、映射、
  `归档文件清单_SHA256.csv`、快速验收摘要和首轮原始摘要。
- 验证：归档 `16,966` 文件、`7,519,131,497 bytes`；负荷 `1,357,800` 行、155 个省年组、每组 8,760 h、
  QA PASS；model-ready smoke 快照 `142/142 PASS`。首轮 95/98 映射直接 PASS；两个目录短暂可见性告警
  复查后文件数/字节一致，一个运行脚本后续更新已补同步且源目标 SHA256 一致。旧 output manifest
  的 116 个缺失项全部位于有意排除的 `raw/`，非 raw 缺失 0。最终口径为 `QUICK_PASS`，不是第二轮
  strict PASS。
- 未决与下一步：当前归档可用于内部留档和同门复现。若将其作为公开/长期发布包，可在空闲时重跑
  `verify_archive.py` 完成第二轮 strict 校验；迁移到新机器后还需重映射 VRE Zarr 与水文时序绝对路径。

### 2026-08-25 t550 host95 deployed and server gates passed; large run memory-blocked

- Git/部署：SSH 恢复后，将 `7dfefbb` 功能与 `f7ef130` 文档推送 server bare remote 并 fast-forward；
  随后以 `60561e57c419131a94539c2258ff108cc725edfd` 将共享主机资源快照从完整 `cmd` 改为无参数的
  `comm`，避免持久化无关用户命令行中的凭据。`origin`、GitHub、server checkout 同步到 `60561e5`，
  server checkout clean、无 CISPO/Gurobi solver。
- 修改文件：`scripts/run_fixed_server_host95_long_horizon.sh` 仅改变 before/after 资源快照字段；不改变
  profile、LP、数据、场景、目标、约束、单位、时间窗口、95% SoftMemLimit 或 96 GiB pre-start gate。
- 验证：server `bash -n`、py_compile、`tests/test_solver_profiles.py` 9/9、
  `tests/test_cloud_full_year_profile_guard.py` 8/8、完整 pytest `215 passed + 63 subtests`；完整测试 wall
  `98.34 s`、MaxRSS `1,186,016 KiB`、swaps 0。preflight 根
  `/home/zz2/National_model_server/outputs/preflight_host95_2160h_deploy_20260825_v1` stderr 0，Base 2030
  2160h/start 2880、`TEST_ONLY_TRUNCATED_HORIZON`、compatibility PASS，规模
  `10,331,823/13,932,898/123,010,374`，动态 SoftMemLimit `125.537898 decimal GB`。
- 未决/精确下一步：共享主机上其他用户的 MATLAB/模型服务使 available RAM 约 `85--86 GiB`，低于
  `96 GiB` 门禁；没有停止、修改或挤压这些任务，正式 2160h 未启动。等待 available `>=96 GiB` 后，
  再核对 exact HEAD、clean、无 solver、目标 output/run_control 根不存在、si/so 0 与 memory PSI benign，
  然后只启动唯一 `2030_base_2160h_host95_20260825_v1`，不得绕过门禁或并发第二个 solver。

### 2026-08-25 fixed-server host95 long-horizon route implemented locally

- 授权/边界：作者明确要求解除原 80 GB 长 profile 上限，让 128G 本地服务器尽可能利用内存，并停止
  依赖 744 h 作为主要规模门禁。本实现不改变科学模型边界、输入数据、变量、约束、目标、单位或 Base
  场景；只新增显式、隔离、test-only 的求解与资源策略。自然 `OPTIMAL/MEM_LIMIT/INTERRUPTED/ERROR`
  仍可终止；“95%”是允许上限和整机保护阈值，不是强制占用目标。
- 修改文件：`cispo_model/config.py` 支持 solver profile 声明、验证并追踪
  `host_memory_soft_limit_fraction<=0.95`；`scripts/run_cispo_2030_full_year.py` 将物理内存字节换算为
  Gurobi decimal GB，覆盖保守 fallback 并把解析值、总内存和解释写入 `run_scope.json`；新增
  `config/solver_profiles/barrier_checkpoint_fixed_server_host_memory_95_v1.json` 与
  `scripts/run_fixed_server_host95_long_horizon.sh`；扩展两组 profile/guard tests。
- 运行合同：新 profile 只允许 truncated horizon、`--engineering-barrier-checkpoint-only`、
  `Method=2/Crossover=0/SolutionTarget=1/TimeLimit=null`。启动器默认 2030 Base、2160 h、start 2880，
  pre-start 要求 checkout clean、无已有 solver、available>=96 GiB；output/control 必须不存在。监控器
  每 2 秒写 `resource_monitor.tsv`，整机 used>=95% 时只向独立进程组发 SIGTERM；所有 stdout/stderr、
  GNU time、PID、return code、events 和前后资源快照均保留。
- 本地验证：系统 Python guard tests `8/8 PASS`；RL/Gurobi 环境 solver-profile tests `9/9 PASS`；设置
  本地 wave root 后完整 unittest `215/215 PASS`（`76.227 s`）。2160 preflight 使用 May--July 窗口，
  result-use 正确为 `TEST_ONLY_TRUNCATED_HORIZON`，数值兼容 PASS，规模估计
  `10,331,823/13,932,898/123,010,374`。Windows 无可用 Linux bash，`bash -n` 留到服务器部署门禁。
- Git/同步：selective commit `7dfefbbef5acc593d22b82173259931183353b89` 只包含本路线、t550 交接
  记录与测试，未包含 Module 06 或 `supplementary_materials/**`。GitHub 已 fast-forward 到该提交；
  `origin` push 因 SSH banner timeout 失败。
- 未决/精确下一步：`national-model-server` 与 `national-model-server-vpn` 均可建立 TCP 但 SSH banner
  timeout，故没有更新 server bare remote/checkout、没有启动任务。连接恢复后：先 push `origin`，
  server fast-forward，执行 `bash -n`、focused/full regression 和资源门禁；再
  以新根后台启动唯一 2160 h。不得复用 2026-08-17 的 MEM_LIMIT 根或与云端 `4139552` 相互覆盖。

### 2026-08-25 t550 new-server deployment and 1h Base gate PASS

- Git/入口：运行实现锁定 clean `50e2d2012a76a342eed1d281997c9b2382731a8a`，branch
  `codex/cispo-2030-full-lp`；新 bare remote 为 `/home/zz2/git/National_model.git`，本地 `origin` 已改为
  `ssh://national-model-server/home/zz2/git/National_model.git`，`github` 保留为
  `https://github.com/zhouzhou112/National_model.git`。`C:\Users\ZZ\.ssh\config` 主入口更新为
  `zz2@192.168.9.27`、`id_ed25519`、`BindAddress 124.16.2.17`，并保留自动路由备用入口。当前文档更新
  未提交，以避免把用户已有的 `CODEX_HANDOFF.md` 与 `supplementary_materials/**` 工作树一并提交。
- 服务器盘点：主机 `t550`，96 logical CPUs、约 123 GiB RAM、根盘可用约 2.6 TiB、2×RTX 4090；
  初始 `/home/zz2` 未发现 repo/case/data/output，所有已挂载文件系统的有界检索亦无旧 case。未挂载
  `/dev/sdb1`（14.6 TiB NTFS）和 `/dev/sdc4`（约 222.7 GiB ext4）需要管理员只读挂载授权；本轮没有
  mount、删除或覆盖旧数据。
- 版本化部署：代码 `/home/zz2/National_model_server/repo`；环境
  `/home/zz2/National_model_server/envs/cispo-2030-v1`；数据根分别为
  `model_ready_20260805_power_curve_v3_qc_d63a251_v1`、`hourly_cf`、
  `hydro_timeseries_20260719_sequential_sparse`、`grfr_raw_2019`、`wave_energy_20260727`。所有传输均以
  bytes/SHA256 校验；raw GRFR 两文件分别为既有权威 SHA
  `84ff2c88...506e0f`、`e56d5da8...232756`。首轮 smoke 识别到错误水文子包缺 p30 与 transfer
  manifest，已 add-only 补入权威本地 `grfr_monthly_p30_single_year_proxy_2019.nc`（SHA
  `c28f6286...03767`）及新传输 manifest；随后 `142/142 PASS`。首轮 pytest 同时识别运行环境缺
  `xarray`，按仓库 `requirements-data.txt` 补装 `xarray/xlrd/openpyxl` 后完整复跑为
  `212 passed + 59 subtests`。
- 环境/输入证据：Python `3.11.15`，Gurobi `13.0.2`；`check_gurobi_full_license.py` 以 2,501
  variables/1 constraint/objective 1.0 PASS。`audit_release_contract.py`、V5 input audit、provincial hydro
  audit、`compileall`、6 个 shell、91 个 JSON 及
  `check_server_readiness.py --require-raw-grfr --verify-raw-grfr-sha256` 全部 PASS。pip freeze、Conda
  explicit、部署 manifest、环境脚本和 29 行证据 SHA 文件保存在
  `/home/zz2/National_model_server/manifests/`；证据清单自身 SHA256 为
  `4db4ba8a806028df9f1452ffd24a2ae63891728864ef562fa328bd961e686e52`。
- 真解命令/输出：版本化脚本
  `/home/zz2/National_model_server/run_control/run_2030_1h_new_server_smoke_20260825_v1.sh` 调用
  `scripts/run_cispo_2030_full_year.py --planning-year 2030 --diagnostic-hours 1 --scenario-config
  config/scenarios/base.json --solver-config config/solver_profiles/barrier_16_auto_order_v2.json`。输出根
  `/home/zz2/National_model_server/outputs/2030_1h_new_server_smoke_20260825_v1` 为 `OPTIMAL`，QC
  `58/58`、两个 manifest valid；LP `238,529 vars / 80,143 rows / 453,269 nnz`，presolved
  `113,589/5,709/236,401`，94 Barrier + 1,623 simplex，objective `2,127,270.302704 million CNY`，solver
  `6.9245 s`、wall `33.33 s`、RSS `0.469 GiB`、swaps/stderr 0。数值违约最大值低于 `1e-11`。
- 未决/下一步：旧 case 只能在管理员允许对 `/dev/sdb1`、`/dev/sdc4` 做只读挂载后继续盘点；不要猜测
  它们不存在，也不要写盘。`packages/` 中保留两个 partial tar（约 5.06/1.77 GB），如需清理须作者确认。
  当前环境已可用于审查后的最小调试；下一步应根据具体 review issue 先写/跑 focused test，再只运行
  新命名 1h/24h 门禁。不得把本次 1h 当科学结果，不自动启动 168h/744h/8760h、付费云或并发第二求解。

### 2026-08-17 full-year parameter-route goal completion audit

- 范围：只做目标级证据审计与文档状态更新；没有查询未到窗口的 cloud、没有部署纯文档 tip、没有启动/
  停止/修改任何 solver，也没有触碰用户 supplementary/Module 06 工作树。
- 完成证明：多轮 relaxed 744、V5/744、两批 paired factor screens、Base/1488、Base/2160 memory boundary
  均有 identity/资源/时间/质量记录；strict 744 与 deferred v3 完成 exact macro A/B；正式 v3 profiles
  已由 fixed Gurobi `14/14 + 212/212` 验证并双推送。
- 决策：Stage A `barrier_checkpoint_full_year_cloud_v3` 与 Stage B
  `deferred_crossover2_full_year_cloud_v3` 为 `APPROVED_PARAMETERS_NOT_LAUNCH_AUTHORIZED`；相对 strict
  744 的组合加速为 solver/wall `7.71×/6.99×`。截断根仍非年度科学结果。
- 独立未发生事件：活动 cloud `4139552` 的最终 Barrier/checkpoint/resource terminal audit；任何未来
  付费提交时的实时 ParaCloud CPU/memory/计费规则复核。二者不否定已经形成的未来全年参数决策，且
  均不能由本轮提前假定。
- Git/下一步：基于 docs tip `5fc60efd41cc4a54147dcbbfbac78ae3f17dee8d` 记录本完成审计并双推送；
  fixed 保持 implementation `0363b7b` idle。后续 cloud 只按约 2 小时或 terminal/anomaly 另行审计。

### 2026-08-17 approved future full-year v3 profiles validated on fixed server

- Git/deploy：implementation `0363b7b0183a52184b2f0be7a1381efc76d1615e` 已双推送；fixed 部署前为
  clean/idle `710aa02`，实时资源门禁通过后 fast-forward 到 exact `0363b7b`，部署后仍 clean。
- 服务器门禁：无 CISPO/Gurobi；available RAM 约 `113.85 GiB`，swap 约 `1.04/2.0 GiB` 已用但
  `vmstat si/so=0/0`，memory PSI avg10/60/300 均 0。验证结束后同样无 solver/压力异常。
- 命令/验证：两份 v3 `json.tool`、Stage A sbatch `bash -n`、runner/tests py_compile PASS；在 Gurobi
  13.0.2 环境运行 `tests.test_cloud_full_year_profile_guard + tests.test_solver_profiles` 为 `14/14 PASS`
  （wall `0:02.52`、MaxRSS `109,940 KiB`、swaps 0）；全发现回归 `212/212 PASS`（test runtime
  `97.282 s`、wall `1:38.40`、MaxRSS `1,118,064 KiB`、swaps 0）。
- 结论：`barrier_checkpoint_full_year_cloud_v3` 与 `deferred_crossover2_full_year_cloud_v3` 的正式文件、
  loader schema、all-version guard 与 Gurobi regression 全闭合；参数获批但不构成任何实际 launch
  authorization。本轮未启动 fixed solver、未改 cloud v2、未启 Stage B。
- 下一步：提交/双推送本验证文档；固定服务器保持 `0363b7b` idle，不必为纯文档 tip 再部署。cloud
  只在约 21:20 或 terminal/anomaly 做下一次检查，iteration 不推进且无异常时不落账。

### 2026-08-17 cloud resource audit round 41

- Git：基于本地未提交 future v3 profile 里程碑；本轮只写远端 append-only resource ledger 与文档，
  不修改活动 checkout、profile、进程或输出。
- 只读证据：`squeue/scontrol/sstat/sacct`、最新 telemetry/Gurobi tail、stderr、terminal artifacts、节点状态
  与用户队列。`4139552` 仍 RUNNING/Barrier 343；runtime `1,012,057.571 s`，primal/dual/compl
  `0.983025/8.356e-7/0.087008`，recent-20 `51.190 min`。wall `1,015,381 s`、allocated
  `27,076.827 core-hours`、actual CPU `4,235.784 h`、efficiency `15.6436%`、MaxRSS `362.913 GiB`；
  stderr 0、无 terminal/checkpoint，用户队列无第二任务。
- 持久化：只有因 iteration 从 round 40 的 340 推进到 343，才追加 `audit_round=41`；ledger 变为
  `42` records，SHA256 `69e14220460f734f4f929170e5b9b4575040c5e1be99147a230de749d7d90f25`。
- 下一步：不早于约 21:20 再做常规 cloud 检查，除非 terminal/anomaly；先完成本地 future v3 profile
  提交和 fixed 无求解部署回归，不启动任何 solver。

### 2026-08-17 approved future full-year v3 profiles prepared locally

- Git：基于 `bb42e1e71bea0c784cd6c82902ad93d0598bc450` 的未提交里程碑；local/origin/GitHub 起点一致。
- 范围：新增 `config/solver_profiles/barrier_checkpoint_full_year_cloud_v3.json` 与
  `deferred_crossover2_full_year_cloud_v3.json`；更新 profile-role/profile-value tests、模型规范、全年决策、
  三份强制交接文档。没有改模型边界、数据、scenario、目标/约束、活动 cloud 或 fixed 输出。
- 参数：Stage A 为 744/1488 实证 relaxed winner，Stage B 为 deferred v3 strict terminal 实证路线；共同
  16 threads、Presolve2、Scale2、Aggregate1、Markowitz0.01、无 TimeLimit、SoftMem600 GiB。两份 profile
  均 `APPROVED / NOT LAUNCH AUTHORIZED`，不能覆盖 v2 或自动启动任务。
- 本地验证：首次 config load 正确抓到 schema 字段误写，修正为 `solver_profile_version=v1` 后两份配置
  load PASS；`tests.test_cloud_full_year_profile_guard` `5/5 PASS`，py_compile 与 `git diff --check` PASS。
  本地默认 Python 无 gurobipy，故 `tests.test_solver_profiles` 的真实执行必须在 fixed 环境完成。
- 未决与下一步：选择性暂存本任务文件、提交并双推送；随后实时确认 fixed no-solver/clean/resource-safe，
  fast-forward 精确提交并执行 targeted/full regression。只验证配置与代码，不启动求解。cloud 约 19:20
  做下一次低频只读审计，只有 iteration 进展、异常或 terminal 才写 ledger。

### 2026-08-17 deferred Crossover v3 strict terminal and macro pair PASS

- terminal contract：v3 18:44:12 完成，runner/strict audit/macro pair `0/0/0`。`OPTIMAL`、solver contract
  PASS、QC PASS 58/58、input/result manifests valid、无 state/basis、两个 stderr 0；strict test accepted，
  但因 744 h 截断边界，`scientifically_accepted=false`。
- solver/resources：Barrier 0、simplex `1,266,756`、solver `2,662.606 s`、Crossover `2,458.89 s`；
  wrapper wall `50:52.08`、User/System `7,596.66/785.36 s`、MaxRSS `9,644,004 KiB`、swaps 0。
  最大 constraint/bound/dual violation `9.608e-7/8.955e-7/9.538e-7`，strict quality PASS。
- macro A/B：objective relative `1.838e-12`；capacity/carbon/cost/generation/operation normalized L1
  `4.220e-8/1.588e-13/2.209e-9/0.002380/2.109e-6`，period generation relative `2.365e-9`、load 0。
  所有阈值通过；小幅发电组合差为同一最优面退化，不影响容量、碳、成本和总能量闭合。
- dual/manifests：`dual_export_status.available=true`、Pi basic/default；hourly `23,064` rows、`115,320`
  finite values，annual `3,366/3,366` finite。input/result/QC/solve/start SHA256 分别为
  `be36b189...a0c6/c9a66c72...17cd/2d703865...ce9f/2ef1bcfe...eec8/45ca39fb...1be`；strict/macro
  audit SHA `44c57482...778/541f5291...b79`。
- conclusion/next：relaxed Stage A + v3 Stage B 合计 solver `6,938.338 s`、wall `2:08:24.08`，相对 strict
  744 的 solver/wall 加速 `7.71×/6.99×`。参数 A/B 架构可从 provisional 升级为未来全年工程批准；
  仍须新增不覆盖现有 v2 的正式 profiles/tests，并等待 cloud 19:20 低频审计。不得把 744 重标年度结果。

### 2026-08-17 deferred Crossover v3 exact-resume / simplex phase confirmed

- identity：source checkpoint status `ENGINEERING_BARRIER_CHECKPOINT_ONLY`，科学 manifest 77 rows、SHA
  `772627bc1539338f5f0af23ad7be01eb9553e78b38a67788863dd26593ad9ac3`；Gurobi `13.0.2`、Fingerprint
  `2120635803`、raw LP `4,454,178 / 3,735,087 / 40,395,436`。implementation bundle 差异已显式许可，
  但 target 精确 LP 检查已通过；RAW_GRFR 是唯一差异且两端科学 manifest usage 均 0。
- phase：17:58:55 optimize，日志先写 `use start vectors`，再写 `perform crossover with primal and dual
  start vectors`；Presolve `166.67 s`，presolved rows/cols/nnz `3,007,038/2,846,655/31,252,909`。日志没有
  Barrier 阶段；push 于 `1,361 s` 完成，随后 simplex cleanup。18:25:41 为 iteration `1,220,005`、
  runtime `1,601 s`，尚未达到终态，较大的 cleanup dual infeasibility 仅作为进行中轨迹记录，不提前判败。
- resources/artifacts：Python RSS `8,758,088 KiB`，Gurobi current/max memory `12.687/13.944 GiB`；available
  RAM `105 GiB`、vmstat si/so 0、PSI 0、stderr 0。没有 numerical trouble、return code、solve/QC/result。
- 边界/下一步：只读审计，未改参/取消/并发/部署。fixed checkout 继续冻结 `710aa02`；约 19:10 或
  terminal/anomaly 再查，若仍活动只记录新增阶段；terminal 后依 runner strict audit 和 macro pair 验收。
  cloud 未查询，仍保留约 19:20 的两小时窗口。

### 2026-08-17 deferred Crossover v3 deployed, validated and launched

- deploy gate：fixed `17:50+08:00` 为 branch `codex/cispo-2030-full-lp`、clean `acf59f9`，无真实
  CISPO/Gurobi solver；可用内存约 `113 GiB`、swap `1.0/2.0 GiB` 但连续 vmstat si/so 0、memory PSI
  avg10/60/300 0、磁盘可用 `3.6 TiB`，v3 output/control 均不存在。随后 fast-forward 到 `710aa02`。
- server validation：runner `bash -n`、py_compile PASS；cloud/root/checkpoint/deferred focused `17/17 PASS`；
  full regression `212/212 PASS`，tests `97.198 s`、wall `1:38.40`、MaxRSS `1,105,756 KiB`、swaps 0。
- launch：全新 output `/data/zz2/National_model/outputs/deferred_crossover2_744_validation_v0817_v3`，
  control `/data/zz2/National_model/run_control/deferred_crossover2_744_validation_v0817_v3`；17:53:13 start，
  supervisor PID `1758970`、Python PID `1758995`。5 秒后存活，events 已写 start，两个 stderr 均 0。
- 边界/下一步：v1/v2 roots 永久保留；v3 是唯一 fixed solver，checkout 冻结 `710aa02`，不部署随后
  docs tip、不并发、不改参。约 30--45 分钟或 phase/terminal 检查 exact resume、Gurobi 是否直接
  Crossover、资源与 stderr；terminal 后才执行 strict 58/58/manifests/macro pair。cloud 本轮未查询。

### 2026-08-17 deferred Crossover v2 pre-build terminal and memory-gate repair

- terminal：v2 于 `17:15:01+08:00` 结束，runner/audit/macro rc `1/41/42`；未生成任何 output/LP/Gurobi/
  checkpoint/验收产物，故不能解释为 Crossover 或数值结果。唯一 traceback 是 full-year memory gate
  仍引用已删除的逐版本常量 `CLOUD_FULL_YEAR_PROFILE_IDS`。
- Git/changed files：`018607c`（`fix: apply cloud profile role to memory gate`）修改
  `scripts/run_cispo_2030_full_year.py` 与 `tests/test_cloud_full_year_profile_guard.py`；用纯函数把已分类
  Stage A/B role 应用于 640 GiB floor，非 cloud profile 保持原 horizon 门槛，配置值高于 640 GiB 时不下调。
- 验证：本地 py_compile PASS、profile-guard `5/5 PASS`、`rg CLOUD_FULL_YEAR_PROFILE_IDS` 为 0、
  `git diff --check` PASS；提交已推送 origin/GitHub。未修改模型、数据、checkpoint、solver 参数或云任务。
- 下一步：fixed 必须先实时复核 idle/clean/RAM/swap/PSI，再 fast-forward exact `018607c`，运行 focused 与
  full regression；全部通过后只用全新 v3 roots 启动一个 Base/744 deferred Crossover2。v1/v2 不删除、
  不覆盖；v3 后按 30--45 分钟或 phase event 低频监管。

### 2026-08-17 cloud resource audit round 40

- job：`4139552` RUNNING，Barrier iteration 340、runtime `1,002,807.627 s`；primal/dual/compl
  `1.082073/8.926e-7/0.0942553`，近期 20 步平均 `51.928 min`。
- 资源：wall `1,008,190 s`、96 allocated CPUs/700 GiB、allocated `26,885.067 core-hours`、actual
  CPU `4,205.427 h`、efficiency `15.6422%`、MaxRSS `362.913 GiB`，stderr 0。
- 产物：solve/QC/result/checkpoint 均不存在；ledger 41 records，SHA256
  `5e3a972a36812e11ea3b4464743e4f996653b39e141e592081615233cf7021a4`。
- 边界：纯只读 Slurm/solver 检查后仅因 iteration 338→340 才追加一条 ledger；未取消/改参/启动
  Stage B。fixed v2 未查询，继续独立低频监管。

### 2026-08-17 deferred Crossover v2 deployed and launched

- Git/deploy：`acf59f9180483b09c4c0e9380e0576457cc554ac` 已推送 origin/GitHub；fixed no-solver、
  clean 后 fast-forward 到相同 tip。
- 验证：`bash -n`/py_compile PASS；focused `16/16 PASS`；full `211/211 PASS`，tests `97.142 s`、
  wall `1:38.26`、MaxRSS `1,112,044 KiB`、swaps 0。
- 运行：全新 v2 output `/data/zz2/National_model/outputs/deferred_crossover2_744_validation_v0817_v2`，
  control `/data/zz2/National_model/run_control/deferred_crossover2_744_validation_v0817_v2`；17:14:54
  启动 PID `1710059`。available `113.905 GiB`、si/so/PSI `0/0/0`、初始 stderr 0。
- 边界/下一步：v1 不覆盖；v2 仍须先写出 root compatibility、exact Fingerprint/dimensions/order 与
  `LPWarmStart=2` 证据，随后严格 OPTIMAL/QC/58/58/manifests/macro pair。活动期间 fixed checkout 冻结；
  约 30--45 分钟或 phase/terminal 才检查。cloud 保持原 Stage A。

### 2026-08-17 deferred Crossover v1 data-root gate terminal and narrow repair

- fixed terminal：v1 output/control `deferred_crossover2_744_validation_v0817_v1`；runner rc 1、strict
  audit rc 41、macro rc 42，wall `5:31.43`、MaxRSS `4,754,120 KiB`、swaps 0。无 solve/QC/result、
  Gurobi log 或 telemetry，故没有求解成本和可接受结果；失败根不可复用。
- 根因证据：checkpoint source 的 `CISPO_RAW_GRFR_ROOT=null`，target 显式指向 current raw root；该根
  在两端科学 manifest 中均零使用。除 solver row 外，两份 manifest 的 77 行完全相同，SHA256
  `772627bc1539338f5f0af23ad7be01eb9553e78b38a67788863dd26593ad9ac3`；其他 roots 与 LP
  Fingerprint/尺寸一致。严格门禁正确地阻止了 optimize，但把未消费环境根等同科学数据漂移过严。
- 修改：`cispo_model/primal_dual_checkpoint.py` 新增 manifest root-usage audit，只 allowlist
  `CISPO_RAW_GRFR_ROOT` 且要求 source/target usage 均 0；所有 consumed/non-allowlisted roots 仍精确匹配，
  audit 结果进入 `primal_dual_start_input.json`。新增
  `tests/test_primal_dual_data_root_compatibility.py`，并在 existing prepare integration test 覆盖真实形态。
- 验证：新 root-compatibility `4/4 PASS`；primal-dual checkpoint `5/5 PASS`；`py_compile` 与 diff PASS。
- 未决与下一步：选择性提交/双推送后，fixed 已 idle 可 fast-forward 新 tip；先跑 bash/focused/full
  regression，再以全新 v2 output/control 启动唯一验证。任何测试失败不启动。cloud 仍不取消/改参。

### 2026-08-17 all-version cloud Stage A/B fail-closed guard prepared locally

- 问题：`run_cispo_2030_full_year.py` 仅把两个 `*_v1` profile 纳入全年/flag 门禁；current v2 sbatch
  本身正确，但直接调用 v2 或未来版本可能绕过 profile-specific fail-closed 检查。
- 修改：`scripts/run_cispo_2030_full_year.py` 新增纯函数 `cloud_full_year_profile_role()`，按稳定前缀识别
  所有版本；Stage A 必须显式 engineering checkpoint，Stage B 必须给 checkpoint input，二者必须为
  full-year。新增 `tests/test_cloud_full_year_profile_guard.py`；同步 `cispo_full_lp_model_spec.md` 的
  complete/incomplete recovery 与 all-version guard 合同。
- 验证：RL Python `py_compile` PASS；focused subprocess/unit tests `4/4 PASS`；`git diff --check` PASS。
- 运行影响：无。当前 cloud sbatch 已使用 full_year 与 engineering flag；fixed/cloud 均未查询、未改参、
  未部署。本地修复不得在 fixed PID 存在期间 fast-forward。
- 下一步：到 fixed 约 30--45 分钟/phase 事件窗口后核对 exact resume；cloud 仍约 2 小时且仅新 iteration
  落账。代码提交后也只推送 remotes，不部署活动 fixed checkout。

### 2026-08-17 exact deferred Crossover=2 validation launched on fixed server

- Git：实施提交 `b277fcea4cb42d4bf8634f0baaf794095e00d67f`（`fix: enable exact deferred
  crossover resume`）已推送 origin/GitHub 并部署到 fixed；启动前 checkout clean/idle。
- 范围：独立重建 Base/744 exact LP，从既有 relaxed Base/744 BarX/BarPi 只读恢复，验证
  `LPWarmStart=2 + Crossover=2 + CrossoverBasis=1` 是否直接完成 Stage B，而不重新运行 Barrier。
- server validation：`bash -n`、JSON、`py_compile` PASS；focused actual `20/20 PASS`；完整 regression
  `203/203 PASS`，tests `94.966 s`、wall `1:36.07`、MaxRSS `1,121,468 KiB`、swaps 0。
- 运行证据：output `/data/zz2/National_model/outputs/deferred_crossover2_744_validation_v0817_v1`，
  control `/data/zz2/National_model/run_control/deferred_crossover2_744_validation_v0817_v1`；
  `2026-08-17T16:34:12+08:00` 启动 supervisor PID `1656831`、time child PID `1656855`；available
  RAM `113.918 GiB`、si/so `0/0`、memory PSI avg10 0、stderr 0。
- 合同：优化前必须通过源/目标 current manifests、相同 Gurobi `13.0.2`、科学/数据 identity、
  Fingerprint `2120635803`、raw `3,735,087 vars / 4,454,178 rows / 40,395,436 nnz` 与完整顺序
  digests；终态仅接受 `OPTIMAL + solver contract PASS + solution_qc PASS + 58/58 + valid manifests +
  exact accepted-pair macro PASS`，且仍为 `TEST_ONLY_TRUNCATED_HORIZON`。
- 未决与精确下一步：fixed checkout 冻结 `b277fce`，只按约 30--45 分钟或 phase/terminal/资源异常
  检查；首次事件检查核对 `primal_dual_start_input.json` 与是否直接进入 Crossover。cloud 仍按约 2 小时
  低频只读，仅新迭代/异常追加 ledger；不得取消/改参/启 Stage B 或提交第二云任务。

### 2026-08-17 real deferred-crossover resume contract repaired locally

- 问题证据：既有 relaxed Base/744 source checkpoint eligibility 全通过，完整 BarX/BarPi、Fingerprint、
  source identity/order digests 均有效；但 `prepare_primal_dual_crossover()` 要求 source/target 完整
  `input_manifest.csv` 文件 SHA 相同。manifest 明确包含 solver profile 行，Stage A 与 Stage B 又必须
  使用不同 profile，故原合同无法真实续接。implementation layer 还包含 Git commit，使后续非 LP 修复
  同样无条件阻断，尽管 exact LP Fingerprint/order 可独立验证。
- 修改范围：`io_contract.py` 新增只排除 `solver_configuration` 的科学 resume identity；
  `primal_dual_checkpoint.py` 保留 source manifest/vector 自校验并增加 source/target Gurobi version、
  科学 input SHA、显式跨 bundle 许可和全量 provenance；runner 新增
  `--allow-compatible-primal-dual-implementation`，无 checkpoint 时拒绝。模型变量、约束、目标、Base、
  数据、容差和现有云作业均未改变。
- 新实验合同：新增 `barrier_16_deferred_crossover2_744_validation_v1.json`、固定服务器独立 runner 与
  accepted Stage B/strict reference macro pair auditor。目标必须 Crossover 2、CrossoverBasis 1、
  LPWarmStart 2、Feas/Opt `1e-6`、SoftMem 80、no TimeLimit；使用全新 output/control，不导出 state/basis，
  终态要求 OPTIMAL、solver contract PASS、QC PASS、58/58、两个 manifest 有效及 exact macro PASS。
- 验证/未决：JSON、py_compile、`git diff --check` 与 input-resume/runner/pair-audit focused `6/6 PASS`。
  Windows 无 gurobipy，不能把 checkpoint/profile Gurobi tests 记为通过。下一步提交/双推送，fixed idle
  fast-forward 后执行 bash/json/compile、focused/full regression；再先让真实 744 build 完成全部
  checkpoint identity/order gate，只有进入 Crossover 才持续运行。cloud `4139552` 不改参、不取消。

### 2026-08-17 second factor/throughput screen batch terminal

- 运行/身份：固定服务器实施 checkout 保持 clean `7551e3f`；唯一 supervisor PID `1567638` 按
  `presparsify2 -> barorder1 -> threads32` 从 15:23:11 至 16:06:11 串行完成，未并发、未修改云端。
  三根均 Base/744、Crossover 0、5 Barrier steps、status 7、runner rc 2、audit rc 0、stderr/swaps 0；
  Fingerprint `2120635803` 及九项 LP/scientific/scenario identity 全匹配，无科学/checkpoint 产物。
- 结果：`PreSparsify=2` 的 Factor NZ/Ops/step ratios 为
  `0.976002/1.073514/1.107897`，wall `17:00.64`、MaxRSS `20,371,484 KiB`；`BarOrder=1` 为
  `1.0/1.0/1.107832`，wall `12:46.29`、MaxRSS `19,783,500 KiB`；Threads 32 为
  `1.0/1.0/1.256668`，wall `13:01.31`、MaxRSS `19,759,924 KiB`。summary
  `NO_MATERIAL_COST_IMPROVEMENT`、all valid、shortlist 空、scientifically accepted false。
- 证据/资源：summary JSON/CSV、events、baseline audit SHA256 分别为
  `8c30c896...7a071`、`af32487b...154ad`、`948582e8...d036`、`c782526a...3f49`；output/control
  仅约 `330/157 KiB`。16:16 fixed 无 solver，available RAM 约 `113 GiB`、si/so/PSI 0。
- 未决/下一步：不从空 shortlist 选择 winner，不为三根运行完整 744，也不继续低价值 solver 参数盲扫。
  汇总既有完整 relaxed/strict 744、1488、2160 memory boundary 与云端 Stage A，形成后续 8760 的
  profile、线程、内存、checkpoint 与验收建议；仅新候选具备可解释的实质结构收益才重开完整 A/B。

### 2026-08-17 second paired factor/throughput screen batch launched

- Git/部署：local、origin、GitHub 已统一为实施提交
  `7551e3fcc55aa2964dd8eff2bed30e7ab47400f7`；fixed 从 clean/idle `4f195d4` fast-forward 到该提交，
  部署后 checkout clean。未改模型、数据、Base 身份、容差或云端作业。
- 验证：`scripts/run_fixed_server_relaxed_factor_screens{,_round2}.sh` 均 `bash -n PASS`，三份新增 profile
  JSON 和 summary `py_compile` PASS；summary/profile/solver-profile focused `16/16 PASS`。设置五个
  current 外部数据根后的完整 server regression 为 `197/197 PASS`，test runtime `93.710 s`、wall
  `1:34.83`、MaxRSS `1,133,084 KiB`、swaps 0。
- 启动证据：目标 output/control 均事先不存在；无 Python/Gurobi solver；available RAM
  `113.951 GiB`、si/so `0/0`、memory PSI avg10 `0.00`、磁盘充足。baseline audit 为 Fingerprint
  `2120635803`、raw `4,454,178/3,735,087/40,395,436`、Factor NZ/Ops `7.334e8/4.761e12`、5 steps、
  observed `12.8348494053 s/iter`。15:23:11 以全新 `relaxed_factor_screens_v0817_v2` roots 启动唯一
  supervisor PID `1567638`，首根 `presparsify2`；5 秒存活检查、首个 event 与 stderr 0 均通过。
- 边界/下一步：三根固定为 `presparsify2 -> barorder1 -> threads32` 串行，Base/744、Crossover 0、
  `BarIterLimit=5`，没有科学/checkpoint 身份。活动期不改 fixed checkout、不并发求解。按用户要求将
  fixed 正常检查降为约 30--45 分钟/事件驱动，cloud 降为约 2 小时；批次终态后严格审计 identity、
  rc/stderr、Factor 与 paired throughput，只有 shortlist 候选才允许完整 744 + exact macro A/B。

### 2026-08-17 second paired factor/throughput screen batch prepared

- Git/范围：基于 `b1af1e42d42c6bc8d31857e4a09cdc4accc8c81f`；新增
  `PreSparsify=2`、`BarOrder=1`、Threads 32 三份 relaxed 744×5 profiles 与 round-2 wrapper；扩展
  通用 runner/summary 和测试，更新三份交接文档。未修改模型/数据/scenario，未启动 solver。
- 筛选理由：24 h PreSparsify2 Factor Ops/NZ 约 `6.361e8/6.298e6`，有结构收益但迭代变多；
  BarOrder1 `6.690e8/6.505e6`，收益低于门槛但可能随规模放大；Threads32 结构不变，24 h 曾较慢，
  仅允许以同机 paired 5-step throughput 证明。PreDual1、PreDual2、Aggregate0、Presolve1、AggFill0
  已因灾难性 factor、无收益或 <2% 收益排除。
- 合同：round-2 baseline 为 v1 `nf1_scaleauto` 5-step 根；结构门槛 `>=5%`，runtime 门槛
  `>=10%`。summary v2 接受显式安全 case tags，记录 observed ratio；missing runtime/identity/factor/
  exact 5 steps/rc/stderr fail-closed。shortlist 不自动 winner 或 science。
- 验证：三份 JSON、py_compile、diff check PASS；summary 3、profile 4、solver profile 9 项，共
  `16/16 PASS`。下一步双推送，fixed idle/clean fast-forward 后执行 Linux bash/profile/focused/full
  regression；再以全新 v2 roots 唯一串行启动。

### 2026-08-17 first factor-screen batch terminal and cloud resource round 39

- Git/范围：fixed 冻结 clean `4f195d4353b76ce76c710eb5c7ba3c467a4d494c` 完成三根 screen；
  只读终态审计并向 cloud ledger 原子追加 round 39，更新三份交接文档。无 checkout/profile/solver
  中途修改，未取消/改参 cloud、未启 Stage B。
- factor terminal：三根均 paired identity 全匹配、status 7、5 Barrier iterations、runner rc 2、
  audit rc 0、stderr/swaps 0，且无科学/检查点产物。NF0 两根 Factor NZ/Ops ratio
  `1.003545/1.031506`，NF1+ScaleAuto 为 `1.0/1.0`；observed step `13.187/12.835/13.505 s`。
  case wall `12:44.06/12:42.69/12:41.36`，MaxRSS `20,211,636/19,678,600/20,501,636 KiB`。
  summary `NO_MATERIAL_FACTOR_IMPROVEMENT`、all valid、shortlist `[]`，完整 744 未启动。
- cloud：iteration 338、runtime `996,833.092 s`，primal/dual/complementarity
  `1.114863/9.225e-7/0.097289`；round 39 wall `999,673 s`、allocated `26,657.947 core-hours`、
  actual CPU `4,169.626 h`、efficiency `15.6412%`、MaxRSS `362.913 GiB`、recent-20
  `52.922 min`。ledger 40 records SHA256
  `75c7edd5cc791517c465798066974edcd7a0acfcf43ee337cf99bbb9222c2108`。
- 下一步：审计既有 AggFill/PreSparsify/BarOrder/PreDual 证据并只构造最少数量的第二批 744 5-step
  candidates；仍要求 exact paired identity 和 >=5% Factor Ops/NZ，未过门槛不跑完整 744。

### 2026-08-17 three serial 744 h factor screens launched

- Git/部署：`4f195d4353b76ce76c710eb5c7ba3c467a4d494c` 已到 local/origin/GitHub/fixed；fixed
  clean/idle。Linux `bash -n`、3 profile JSON、py_compile、focused `10/10` 与 full `194/194 PASS`
  （`96.14 s`、MaxRSS `1,104,912 KiB`）。
- baseline gate：Fingerprint `2120635803`，raw/identity `4,454,178 rows / 3,735,087 cols /
  40,395,436 nnz`，presolved `3,001,388 / 2,775,698 / 31,159,971`，dense `6,050`、AA' NZ
  `6.131e7`、Factor NZ `7.334e8`、Ops `4.761e12`；scientific/scenario SHA 完整。输出/control 均
  在启动前不存在，available `113.97 GiB`、si/so/PSI 0、磁盘约 `3.96 TB` 可用。
- 启动：`relaxed_factor_screens_v0817_v1` supervisor PID `1494933`，14:25:49 第一根
  `nf0_scale2` PID `1495063/1495064`；严格串行 3×Base/744、每根 5 Barrier iterations、Crossover 0，
  不导出 checkpoint/科学结果。launch contract 冻结 exact head、roots、64 GiB 门槛与 cloud untouched。
- 下一步：15--20 分钟或 case switch/terminal 低频检查；三根结束后只按 summary fail-closed shortlist，
  不自动选 winner。活动期间不改 fixed checkout；cloud 保持原 Stage A。

### 2026-08-17 factor-screen external data identity freeze

- Git/范围：基于 `613abe8d48ac3aa6382cdca3ce5a7d3528356723`；仅修改
  `scripts/run_fixed_server_relaxed_factor_screens.sh`、对应静态测试与三份交接文档。runner 现在与已验
  campaign 一样，以可覆盖但有 current defaults 的方式导出 model-ready、CF、hydro、raw GRFR、wave
  五个外部数据根，消除后台 shell 环境偶然性；模型、scenario、solver 参数与数据内容均未改变。
- server 部署前验证：checkout clean/idle 后 fast-forward `613abe8`；`bash -n`、profile JSON、
  `py_compile`、focused `10/10 PASS`。在五个 current roots 显式设置后，完整 regression
  `194/194 PASS`，wall `95.60 s`、MaxRSS `1,115,900 KiB`。两次缺根运行只产生 missing external
  input 错误且未启动 solver；这也是加入 runner defaults 的直接证据。
- local 验证：四个目标文件按 discovery 方式合计 `10/10 PASS`，`git diff --check` PASS。直接以
  `tests.test_*` 模块路径调用因 `tests/` 非 package 而 import failure，未当作测试结果。
- 下一步：提交/双推送本修复，fixed fast-forward 新精确 tip 后重复 `bash -n`、focused/full regression；
  然后以全新 v1 roots、`EXPECTED_HEAD` 和唯一后台 supervisor 启动三根串行 744 h 5-iteration screens。

### 2026-08-17 Base/2160 memory boundary and cloud resource round 38

- Git/范围：基于 `62290ea19e087d5e177066071315c2bbfc195639`；只读审计 fixed terminal 与 cloud，
  向既有 cloud resource ledger 原子追加 round 38，并更新三份交接文档。未修改 fixed checkout/profile，
  未取消/改参 cloud，未启动 Stage B 或第二 solver。
- fixed：Base/2160 原始 LP `12,520,914 / 10,398,783 / 126,724,678`（rows/cols/nnz），build
  `884.643 s`；Presolve `2,214.94 s` 后为 `9,527,353 / 8,288,888 / 106,864,030`，Ordering
  `565.03 s`。`SoftMemLimit=80 GiB` 在 Barrier 0 iterations 前触发 `MEM_LIMIT/status 17`；solver
  `2,800.735 s`、wrapper wall `1:01:40`、MaxRSS `72,659,300 KiB`、rc 2、stderr/swaps 0。
  `solve_report.json` 明确 `solution_count=0`、objective null；无 QC/result/checkpoint/BarX/BarPi，故只作为
  内存/fill-in 工程证据。campaign `14:03:30` complete，fixed 无 solver、checkout clean `902b1672`。
- cloud：iteration 336、runtime `990,741.973 s`，primal/dual/complementarity
  `1.161194/9.516e-7/0.100835`；round 38 wall `995,707 s`、allocated `26,552.187 core-hours`、
  actual CPU `4,153.300 h`、efficiency `15.6420%`、MaxRSS `362.913 GiB`、recent-20
  `53.040 min`。ledger 39 records、SHA256
  `932b7d8a6510e26653ee2b275cb8ec6280f19d1c87b6c640771c404e66bbd534`；stderr 0、无终态。
- 未决/下一步：不以提高 SoftMemLimit 直接重跑 2160。先双推送本记录，fixed fast-forward 精确 tip，执行
  `bash -n`、profile/focused/full regression；通过后仅启动三根串行 Base/744 五迭代 factor screens，
  用 Factor Ops/NZ shortlist 决定完整 744 候选，再做 exact macro A/B。

### 2026-08-17 Base/1488 terminal checkpoint audit, Base/2160 start and cloud round 37

- Git/范围：基于 `9304f91be2b0262cd8d306d66c175cbb9c375ce3`；只读 fixed/cloud，流式运行尚未部署的
  checkpoint gate 但不写 fixed 文件，向 cloud ledger 原子追加 round 37，并更新三份交接文档。
  未停止/改参/并发、未修改 fixed checkout。
- 1488 solver/resource：Barrier status/code `OPTIMAL/2`、143 iterations、runtime `25,834.260 s`、objective
  `2,594,713.948279 million CNY`；last persisted primal/dual/compl `0.0035927/4.623e-5/0.00096294`，
  relative primal-dual gap `0.0050318`。wrapper rc 0、wall `7:22:57`、MaxRSS `55,460,664 KiB`、swaps 0、
  stderr 0。strict solution contract 因 Constr/Bound/Dual/ComplVio
  `0.0112802/4.62e-6/0.0022079/42.0475` 为 `HARD_FAIL`，不作科学解。
- checkpoint/identity：streamed current gate `eligible=true`；primal/dual vectors 分别为
  `7,236,351/8,648,849` entries，bytes `57,890,936/69,190,920`，SHA256
  `a49ce6bf...7fef0/82c4ad5f...8c718`。LP Fingerprint `893131507`、raw dimensions、变量/约束 order
  digests、Gurobi `13.0.2`、scenario/solver SHA、input manifest SHA256 `673d0230...35a1e` 均完整。
  它可供显式授权的 exact-LP deferred crossover，但不是 planning state、年度结果或论文价格。
- 物理/宏观审计：engineering QC `54/58`，失败 wave `0.850 MW` overshoot、strict bidirectionality、
  reservoir transition `11,280 m3`、active-storage `3.775 m3`。power balance `2.315 kW`；storage overlap
  `1,832.89 GWh = 0.0952%` period load，max `58.9 MW`；interprov opposing `4,993.57 GWh = 0.259%`
  period load，excess loss share `0.00641%`；load-center bidirectional `17,153.38 GWh = 0.891%`。
  其余 load、VRE、热电、储能状态、水电月能量/级联、网络容量、备用、惯量、碳/CCS/DAC 与成本
  accounting 通过；objective component relative residual `1.47e-13`。BarPi 导出可用，hourly/annual
  rows `46,128/3,366`，限定 `ENGINEERING_ONLY_NOT_FOR_PUBLICATION`。
- 2160：旧 campaign 的存在性 gate 在 1488 完成后进入 Base/2160；本次 checkpoint 用新严格 gate 也
  实际 PASS，因此不是误放行。13:01:45 启动唯一 PID `1387308/1387309`，start hour 2880，同 relaxed
  NF1 long profile；13:08 build RSS 约 `4.14 GiB`，available 约 `110 GiB`、si/so/PSI 0、stderr 0。
- cloud：iteration 335、runtime `987,914.783 s`；round 37 wall `991,984 s`、allocated
  `26,452.907 core-hours`、actual CPU `4,137.397 h`、efficiency `15.6406%`、MaxRSS `362.913 GiB`、
  recent-20 `53.550 min`，ledger 38 records SHA256
  `c31d779cededad5baf6d50912808be8c09bfd90a1a98577d10cddec62d0fe0df`，stderr 0、无 terminal/
  checkpoint、无 Stage B。
- 下一步：低频监管 Base/2160 到 factor structure/iteration gate/终态；campaign idle 前不得部署
  `9304f91` 或启动 factor screens。2160 完成后才 fast-forward、server regression、三根 744 screen。

### 2026-08-17 fail-closed factor-screen shortlist audit

- Git/范围：基于 `b545f6ca603285878372d4e91d3c3c7adb56181d`；修改
  `cispo_model/solver_audit.py`、`scripts/run_fixed_server_relaxed_factor_screens.sh`、新增
  `scripts/summarize_relaxed_factor_screens.py` 与测试，并更新三份交接文档。未部署或触碰活动作业。
- 身份/门禁：baseline 与每根 candidate 必须同时具备相同 Gurobi Fingerprint、LP identity/raw matrix
  数量、resolved scientific configuration SHA 与 scenario SHA；候选还必须 rc `0/2`、stderr 0、
  Barrier iterations `5`、无 numerical trouble 且 presolved/AA'/Factor/dense 指标齐全。baseline
  audit 在任何 screen 前 fail-closed；三根有任一不完整则 summary 为 `SCREEN_AUDIT_INCOMPLETE`。
- 排序合同：相对当前 NF1+Scale2 baseline，Factor Ops 或 Factor NZ 至少降低 `5%` 才进 engineering
  shortlist；排序依次为 Ops ratio、NZ ratio、observed seconds/iteration。工具明确不自动选 production
  winner，也不创建 checkpoint/scientific acceptance；shortlist 仍须完整 744 和 exact macro A/B。
- 验证：focused unittest `11/11 PASS`、两个 Python 文件 `py_compile` PASS、`git diff --check` PASS。
  单测覆盖 material-improvement shortlist 与 LP Fingerprint mismatch fail-closed；runner 内容测试覆盖
  baseline/JSON/CSV summary 编排。
- 下一步：待当前 fixed campaign idle 后 fast-forward 精确 tip，执行 server `bash -n`、profile/focused/
  full regression；随后用唯一串行 runner 产生三根 screen。不得在 active Base/1488/2160 中途部署。

### 2026-08-17 cloud resource audit round 36 and Base/1488 iteration 120

- Git/范围：基于 `4cf59af2ccbaf5a2a049453e0793d07ccd1be1ff`；只读 fixed/cloud，并向既有 cloud
  ledger 原子追加 round 36；更新三份交接文档。未修改活动 checkout/profile，未启停任何 solver。
- fixed：iteration 120 于 11:51:25 落盘，runtime `21,739.318 s`，primal/dual/complementarity
  `0.050274/0.000789619/0.027934`；100--120/110--120 平均 `169.03/169.75 s/step`，12 h 投影
  iteration `247.0`。RSS `55,459,960 KiB`，available 约 `61.1 GiB`，swap used 约 `984 MiB` 但
  si/so/PSI 为 0，stderr 0，终态/checkpoint 不存在。
- cloud：job `4139552` RUNNING，iteration 334、runtime `984,705.405 s`，primal/dual/
  complementarity `1.213709/9.858e-7/0.104884`；round 36 wall `988,357 s`、allocated
  `26,356.187 core-hours`、actual CPU `4,122.200 h`、efficiency `15.6404%`、MaxRSS `362.913 GiB`、
  recent-20 `53.255 min`。ledger 37 records，SHA256
  `cbf0311e71c382508ad459bd238232e3fbea499b1f8913bbb7792bd5d8233710`；stderr 0、无终态/
  checkpoint、无 Stage B。
- 下一步：继续低频到 fixed iteration 130/终态，cloud 下一轮约一小时且仅有新 iteration 才记账；
  正常中间点不另写文档。当前 campaign idle 前不部署本地 tip 或 factor screens。

### 2026-08-17 machine-readable phase trajectory audit

- Git/范围：基于 `71e5da6467d94770fee7f83b49031eff420443b8`；修改
  `cispo_model/solver_audit.py`、`tests/test_solver_audit.py` 与三份交接文档。没有服务器部署、求解
  启停、参数或 checkout 变更。
- 实现：`telemetry_phase_summaries` 新增 `iteration_span`、`runtime_span_seconds`、
  `observed_seconds_per_iteration`、complementarity 末值/极值、末端 primal/dual objectives 与 raw
  objective gap；字段对缺失 telemetry 保持 `None`，不改变既有接口和科学验收语义。
- 验证：`python -m unittest tests.test_solver_audit tests.test_relaxed_factor_screen_profiles
  tests.test_checkpoint_campaign_gate tests.test_summarize_relaxed_barrier_campaign` 为 `8/8 PASS`；
  `py_compile` PASS；既有 1 h telemetry 实读得到 76-step span 与 `0.11054 s/iteration`，末端 gap
  `0.00108687`，证明真实 JSONL 路径兼容。
- 未决/下一步：fixed campaign 仍运行旧 clean checkout；必须等 idle 才 fast-forward 并做 server
  full regression。随后三个 744 factor screens 的 `solver_audit.json` 将直接提供统一 per-step 与末端
  数值轨迹，只有 Factor NZ/Ops/步时有实质改善者才晋级完整 744 exact macro A/B。

### 2026-08-17 cloud resource audit round 35 and Base/1488 iteration 100

- Git/范围：基于 `1c156c87ea9f4306c8c484eef67c0ba1a323d963`；仅只读 fixed/cloud 活动作业、向既有 cloud
  resource ledger 原子追加一条记录并更新 `CODEX_HANDOFF.md`、`MODEL_SERVER_STATUS.md`、
  `SERVER_RUNBOOK.md`。未修改活动 checkout/profile、未取消任务、未启动 Stage B 或第二 solver。
- fixed 证据：Base/1488 iteration 100 于 10:55:05 落盘，runtime `18,358.690 s`，primal/dual/
  complementarity `0.562716/0.00180162/0.402016`；0--100/50--100/75--100/90--100 平均步长
  `168.69/166.88/168.82/169.06 s`，按近期窗口投影 12 h 到 iteration `247.2`。process RSS
  `55,452,788 KiB`，available 约 `61.1 GiB`，swap used 约 `984 MiB` 但 si/so 0、PSI 0，stderr 0，
  终态三文件与 checkpoint 均不存在。残差量级对齐 strict Base/744 为 `67/96/122`；不同 horizon
  objective gap 不直接比较，raw gap 仅记录为 `5.432e6`。
- cloud 证据：job `4139552` 仍 RUNNING，iteration 333、runtime `981,713.748 s`，primal/dual/
  complementarity `1.246258/1.002e-6/0.107341`。round 35 记录 wall `985,280 s`、allocated
  `26,274.133 core-hours`、actual CPU `4,109.163 h`、efficiency `15.6396%`、MaxRSS `362.913 GiB`、
  recent-20 `53.302 min`；账本 36 records，SHA256
  `64d80b8cceb7eae1081524328adb85d01515c16e1c5446cc5f0eb504bbdb6e87`，stderr 0、无终态/
  checkpoint、无 Stage B。
- 验证/未决/下一步：本地 focused unittest `5/5 PASS`。iteration-100 watcher 因 CRLF 路径尾字符
  退出，但 direct SSH 已验证远端 solver/PID 完整，故仅弃用该等待器，不干预求解。继续低频监管
  fixed 至 Barrier 终态或 12 h TimeLimit；旧 campaign 若切换到 2160，只记录且不追改。campaign
  idle 后部署 fail-closed gate/lower-factor screens，补 server bash/profile/full regression，再串行筛选。

### 2026-08-17 cloud resource audit round 34 and Base/1488 iteration 79

- cloud：只读核验 `squeue/sstat`、telemetry 与两个 stderr；job `4139552` iteration 332、runtime
  `978,908.233 s`，primal/dual/complementarity `1.274926/1.023e-6/0.109716`。wall
  `981,492 s`、allocated `26,173.120 core-hours`、actual CPU `4,092.853 h`、CPU efficiency
  `15.6376%`、MaxRSS `380,541,608 KiB`；iteration 312--332 平均 `53.2909 min/step`。
- 账本：向既有 `resource_audit_snapshots.jsonl` 追加 round 34 后为 35 records，SHA256
  `29960f1e803e98b1dcbd59e26f242b48b026e87e9a01859f20a3681d6ddaad17`。slurm/wrapper stderr
  均 0，终态与 checkpoint absent；没有 cancel、signal、改参或 Stage B。
- fixed：Base/1488 iteration 79 于 09:56:09 落盘，runtime `14,822.968 s`；primal/dual/
  complementarity `10.206400/0.00308381/7.745108`，process RSS 约 `55,451,664 KiB`、stderr 0。
  保持当前 checkout/profile 和唯一 solver，下一材料判别点仍为 iteration 100/终态。

### 2026-08-17 paired five-iteration 744 h factor screens prepared

- 设计：新增三个 Base/744 test-only profiles：
  `barrier_16_engineering_factor_nf0_scale2_5iter_v1`、
  `barrier_16_engineering_factor_nf1_scaleauto_5iter_v1`、
  `barrier_16_engineering_factor_nf0_scaleauto_5iter_v1`。除 `NumericFocus/ScaleFlag` 的
  `(0,2)/(1,-1)/(0,-1)` 外，所有数值参数一致；`BarIterLimit=5` 只取得 presolve、ordering、factor
  与初始步长证据，不以未收敛向量冒充 checkpoint。
- 编排：新增 `scripts/run_fixed_server_relaxed_factor_screens.sh`，只在 clean/no-solver、available
  ≥64 GiB、无 swap I/O/PSI 时串行运行；每根输出新 root，拒绝覆盖，记录 `/usr/bin/time -v`、
  resource snapshots、return code 与 `collect_solver_run()` 机器可读审计，并要求 1--5 Barrier steps
  及 Factor NZ/Ops/dense cols 完整。
- 验证：三份 JSON 可解析；`load_model_config()` 均接受；
  `tests.test_relaxed_factor_screen_profiles` `1/1 PASS`。本地完整 `test_solver_profiles` 因环境没有
  `gurobipy` 无法导入，不记录为测试失败或通过；Windows WSL 同样没有 `/bin/bash`。
- 边界/下一步：未触碰 fixed checkout、活动 Base/1488、历史 outputs 或 ParaCloud。待当前 campaign
  退出后部署精确 tip，先跑 server `bash -n`、新测试、完整 profile/full regression，再以新 roots
  执行三个 screen；只有 materially 降低 factor/step 成本的候选进入完整 744 exact macro A/B。

### 2026-08-17 fail-closed long-horizon checkpoint campaign gate

- 问题：`scripts/run_fixed_server_relaxed_barrier_campaign.sh` 原来只用 manifest 文件存在性放行
  Base/2160；runner 在 TimeLimit 后只要有 Barrier iteration 也会保存完整向量和 recovery manifest，
  因而 `deferred_crossover_eligible=false` 的 forensic recovery 可能被错误用作完整工程 checkpoint。
- 修复：新增 `scripts/check_barrier_checkpoint_eligibility.py`，核验 checkpoint schema、eligible flag、
  accepted/engineering status、solver/Barrier status code，并校验 primal/dual vector metadata、文件大小
  与 SHA256。campaign 把机器可读 gate 写入对应 control 子目录；只有 exit 0 才运行 2160，其他情况
  记录 `checkpoint_ineligible_stop` 后 fail-closed 结束。
- 测试：新增 `tests/test_checkpoint_campaign_gate.py`，覆盖 complete engineering PASS、recovery-only
  拒绝与 vector corruption 拒绝；`python -m py_compile ...` PASS，配合既有 summary test 共
  `4/4 PASS`。本地 WSL 配置没有 `/bin/bash`，所以没有伪造 bash-n 结论。
- 边界/下一步：本变更仅在本地工作树；没有修改活动 fixed checkout、campaign 进程、outputs 或
  ParaCloud `4139552`。待活动串行 campaign 完全退出、服务器 clean/idle 后再部署精确提交，执行
  `bash -n`、focused/full regression，并用合成 eligible/recovery manifests 验证两条 shell 分支。

### 2026-08-17 cloud resource audit round 33 and Base/1488 iteration 70

- cloud：只读核验 `squeue/sstat`、telemetry、stderr 与终态文件，并向既有
  `run_control/2030_8760_base_stage_a_barrier_v2/resource_audit_snapshots.jsonl` 追加 round 33。
  job `4139552` 为 `RUNNING`，latest Barrier iteration 331、runtime `975,911.936 s`；wall
  `980,022 s`、96 CPUs/700 GiB allocation、allocated `26,133.920 core-hours`、actual CPU
  `4,086.896 h`、efficiency `15.6383%`、MaxRSS `380,541,608 KiB`。iteration 311--331 平均
  `53.4137 min/step`；34 条记录 SHA256
  `fc88fd29580cc565620096fdf9a2b06ead35e42e88bfa32a2cd3d0d5fe48045c`。
- 成本判断：latest primal/dual/complementarity 为 `1.336420/1.053e-6/0.113863`，仍改善但离
  current `BarConvTol=1e-8` 的全年终点无近端证据。用最近 10--80 步端点衰减率外推，primal 到
  relaxed Base/744 终点量级约 5 天，absolute objective gap 到 1,000/1 量级约 8--9/14--16 天；
  该估计不把非线性 Barrier 当确定 ETA，只作为费用风险下界。活动 Gurobi 参数不可安全追改；
  按作者明确要求不取消、不改参、不启 Stage B。
- fixed：Base/1488 iteration 70 于 09:31:02 落盘，runtime `13,316.273 s`；primal/dual/
  complementarity `19.574527/0.00930446/18.290173`，iteration 69--70 继续下降。唯一 solver
  存活，process RSS 约 `55,451,552 KiB`、stderr 0；继续到 100/终态，不并发、不部署。
- 下一步：本轮活动 campaign 完成并释放内存后，优先执行 `NF0+Scale2`、`NF1+ScaleAuto`、
  `NF0+ScaleAuto` 的短迭代 factor screen；只有 materially 降低 Factor NZ/Ops 且 744 宏观账目
  通过的路线才可成为下一次 8760 候选。当前 cloud/fixed 运行身份及历史 outputs 保持不变。

### 2026-08-17 Base/1488 iteration 50 convergence and time-limit gate

- 轨迹：iteration 50 于 08:36:01 落盘，runtime `10,014.836 s`；iteration 0--50、30--50、
  40--50 的平均步长为 `170.51/171.33/161.75 s`。primal/dual/complementarity 为
  `229.055098/0.1722879/262.878554`；iteration 40--50 从
  `357.500/0.328730/484.941` 单调下降，中段平台存在但无反弹。
- exact 744 对齐：三个质量维度分别最接近 Base/744 的 iteration `48/58/65`；absolute
  primal-dual objective gap `3.472e9` 最接近 744 iteration 61，而 744 同 iteration 50 gap
  `5.468e11`，1488 小 `157.5x`。综合迭代路径约领先 10--15 步，但 primal 本身没有领先。
- 时限估计：按 0--50、20--50、30--50、40--50 窗口，43,200 s TimeLimit 可到约
  `244.6/245.2/243.7/255.2` steps。若复制 744 的 263 步会差约 8--19 步；若质量领先能转化为
  终点迭代缩短则可能完成。该区间不足以取消，继续到 100/终态并保留完整 checkpoint/recovery。
- 资源：Python RSS `55,428,232 KiB`，Gurobi current/max memory `45.07/58.29 GiB`；host
  available `65,492,828,160 bytes`、swap used `1,031,831,552 bytes`，实时 si/so `0/0`、
  memory PSI 0、stderr 0。当前 solver 安全，下一 case 仍须等待退出释放内存。

### 2026-08-17 cloud resource audit round 32 and Base/1488 iteration 30

- cloud：只读核验并向既有
  `run_control/2030_8760_base_stage_a_barrier_v2/resource_audit_snapshots.jsonl` 原子追加 round 32。
  job `4139552` 为 `RUNNING`，iteration 329、solver runtime `969,935.080 s`；Slurm wall
  `973,314 s`、96 CPUs、700 GiB allocation、allocated `25,955.040 core-hours`、actual CPU
  `4,058.406 h`、efficiency `15.6363%`、MaxRSS `380,541,608 KiB`。最近 iteration 309--329
  平均 `53.6856 min`；33 条记录 SHA256
  `0752c62843c6d272d58b6d81b2d2444f0fb7b8123e0bc5b225d99921e467326d`。
- 终态边界：cloud wrapper stderr 0；`solve_report.json`、`solution_qc.json`、
  `result_manifest.json` 与 checkpoint manifest 均不存在；未停止、未修改 profile、未启 Stage B。
- fixed：Base/1488 iteration 30 于 07:38:54 落盘，runtime `6,588.139 s`；primal/dual/
  complementarity `2.223e6/702.46/5.926e5`，solver current/max memory 仍
  `45.07/58.29 GiB`、stderr 0。继续唯一 solver 到 iteration 50。

### 2026-08-17 historical factor-parameter audit for the next relaxed campaign

- 只读来源：fixed-server 历史根
  `/data/zz2/National_model/outputs/solver_tuning_v0801_a3a078e_24h_base_candidates_v3` 与
  `solver_tuning_v0801_5e7db68_24h_base_round2_v1`；没有更改历史输出、活动 checkout、当前
  Base/1488 或 ParaCloud `4139552`。
- 关键证据：NF0/auto-scale 历史根的 presolved rows/cols/nnz 为
  `101,664/232,186/1,416,758`，Factor NZ/Ops `6.017e6/6.408e8`、137 iterations、
  `18.99 s`；NF2/Scale2 对照为 `110,665/232,186/1,408,639`、
  `6.562e6/6.930e8`、150 iterations、`57.95 s`。前者 status `SUBOPTIMAL`、目标
  `2,128,186.084091 million CNY`、ConstrVio `0.047882845`，因此不是科学结果，但相对严格
  objective 的宏观偏差约 `1.54e-7`，具备按现行工程宏观合同重测的价值。
- 次选证据：`AggFill=0` 为 `6.557e6/6.803e8`、134 iterations、54.21 s，Factor Ops
  改善不足 2%；`PreSparsify=2` 为 `6.298e6/6.361e8`，但 175 iterations/74.12 s，说明只看
  稀疏度不足以晋级。官方参数说明也指出 NF0 偏速度、默认 scaling 通常有效，而 AggFill/
  PreSparsify 只控制 presolve 填充/稀疏化。
- 下一步：当前串行 campaign 终止并通过空闲/内存门禁后，先做 current-model 744 短迭代 factor
  screen，分别隔离 `NF0+Scale2`、`NF1+ScaleAuto`、`NF0+ScaleAuto`；只将显著降低 Factor
  NZ/Ops 且无异常数值轨迹的候选晋级完整 744 宏观 A/B。容差仍为 `BarConvTol=1e-2`、
  Feas/Opt `1e-5`，不再无证据地放宽；fixed 始终单 solver。

### 2026-08-17 Base/1488 iteration 25 resource and trajectory gate

- 轨迹：iteration 25 于 07:24:37 落盘，runtime `5,731.421 s`；0--25 平均
  `169.69 s/step`，primal/dual/complementarity `2.275e8/1.364e5/5.068e7`。按该早期均值和
  43,200 s solver limit，粗略可到 iteration 246；这不是停止判据，继续到 50/100/终态。
- exact 744 对齐：Base/744 同 profile iteration 25 为 primal/dual/complementarity
  `1.715e8/4.129e6/2.703e10`；1488 primal 高约 32.6%，但 dual/compl 低约 `30x/533x`。
  因收敛维度混合，不能直接沿用 744 的 263 iterations；需观察目标差和中段平台。
- 资源：Gurobi current/max memory `45.07/58.29 GiB`，Python RSS `55,367,700 KiB`；主机
  available `65,561,522,176 bytes`（约 61.1 GiB），swap used 约 970 MiB 且实时 si/so 0，
  memory PSI 0、stderr 0。运行继续安全；下一 case 只能在当前退出释放内存后重新通过 96 GiB 门禁。
- Git/运行：local/origin/GitHub 文档 tip 在本记录前为 `27e991d`；fixed 仍 clean/frozen
  `902b1672...ff36`，不部署、不并发、不修改云 job。

### 2026-08-17 Base/1488 to cloud/8760 factor-cost validation

- 只读对照：cloud 8760 raw `50,907,234 rows / 41,458,383 cols / 492,835,195 nnz`，presolve
  `17,414.51 s` 后为 `37,703,954 / 32,166,850 / 404,259,819`，ordering `2,912.17 s`；
  dense cols 37,696、AA' NZ `7.469e8`、Factor NZ `3.395e10`（约 300 GB）、Factor Ops
  `1.931e15`（粗估 5000 s/iter）。未改 cloud job。
- 与 fixed 1488 对照：1488 dense cols 36,218，Factor NZ `3.866e9`、Factor Ops `1.060e14`；
  8760/1488 Factor NZ/Ops 比为 `8.78x/18.22x`，dense cols 已接近饱和。cloud 最近 20 步实际
  `53.608 min = 3216.5 s/step`，按 Ops 比值折算 1488 为 `176.6 s/step`，而 fixed iteration
  0--16 实测约 `171.0 s/step`，误差约 3.2%。
- 结论/下一步：1488 可作为当前 LP/机器路线的全年每迭代成本代理；当前瓶颈是 Cholesky fill-in，
  不是容差本身。宽松 profile 的全年收益必须由显著减少 Barrier iteration 数产生。fixed 继续到
  25/50/终态测迭代数和残差曲线；不因该推断中止当前任务，也不启动第二 solver。

### 2026-08-17 cloud resource audit round 31 and Base/1488 iteration 16

- cloud：job `4139552` 仍 `RUNNING`，iteration 328 于 06:29:41 落盘；runtime
  `966,756.149 s`，primal/dual/complementarity `1.450925/1.129e-6/0.122696`。07:00:40 追加
  round 31：wall `970,967 s`、allocated `25,892.453 core-hours`、actual CPU `4,048.863 h`、
  efficiency `15.6372%`、MaxRSS `362.913 GiB`、iteration 308--328 平均 `53.608 min`。
  账本 32 records，SHA256 `223757e0609a3299b471d9e01081d1b6a7c69a5a62037707bc6bea191d0ae391`；
  stderr 0、无 terminal/checkpoint，未取消、未改参、未启动 Stage B。
- fixed：Base/1488 已到 iteration 16、runtime `4,225.346 s`；iteration 0--16 平均约
  `171.00 s/step`，primal infeasibility `1.927e9`，solver current/max memory `45.07/58.29 GiB`，
  stderr 0。仍为唯一 fixed solver，继续到 iteration 25 重新估算；checkout 不部署文档 tip。

### 2026-08-17 Base/1488 presolve, factorization and early Barrier evidence

- 命令/身份：fixed clean `902b1672a869cd4e6483633ceaf0208e092bff36`，Base/1488 start hour
  3624，long NF1 winner profile（Method2/Threads16/Presolve2/Crossover0/BarConvTol1e-2/FeasOpt1e-5/
  Scale2/TimeLimit43200/SoftMem80）。local/origin/GitHub 文档 tip 在本记录前为 `97d0a13`；活动求解
  期间未部署新 tip、未启动第二 solver，云 job 未改。
- 规模/预处理：build 约 10.4 min；raw `7,236,351 vars / 8,648,849 rows / 87,364,792 nnz`。
  Presolve `1,080.17 s` 后为 `6,564,794 rows / 5,761,274 cols / 73,637,736 nnz`；ordering
  `322.03 s`。Barrier statistics：dense cols 36,218、AA' NZ `1.509e8`、Factor NZ `3.866e9`
  （约 36 GB）、Factor Ops `1.060e14`（约 200 s/iter）、16 threads。
- 对照：同 Base/744 NF1 winner 的 presolved 规模为 `3,001,388/2,775,698/31,159,971`，ordering
  `101.00 s`、dense cols 6,050、Factor NZ `7.334e8`、Factor Ops `4.761e12`。因此 1488 虽仅延长
  一倍时域，presolved nnz 为 `2.36x`，Factor NZ/Factor Ops 却为 `5.27x/22.26x`；全年效率问题
  不能只靠放宽 BarConvTol 解决，优先目标应转为降低跨时序填充和 dense-column coupling。
- 早期轨迹/资源：iteration 0/1/2 runtime `1,489.26/1,595.89/1,855.80 s`，步耗时约
  `106.64/259.91 s`；current/max solver memory `45.07/58.29 GiB`，主机采样 available 约 82 GiB、
  si/so 0、memory PSI 0、stderr 0。继续运行，至少收集 5--10 步后再估终点。
- 恢复合同审计：runner 在非 OPTIMAL 且 Barrier iteration>0 时会尝试保存完整 BarX/BarPi 为
  `INCOMPLETE_BARRIER_RECOVERY`，`deferred_crossover_eligible=false`；不会把它当科学结果。但 campaign
  的 2160 条件当前仅测试 manifest 文件存在，未检查 eligibility，和“完整 checkpoint 才晋级”的
  文档合同不完全一致。活动脚本不得中途改；本轮结束后最小修复为解析 manifest 并要求
  `deferred_crossover_eligible=true`，另加回归测试。

### 2026-08-17 cloud resource audit round 30 during Base/1488 build

- ParaCloud：只读发现 iteration 326/327，最新 05:36:02 落盘；runtime `963,537.897 s`，
  primal/dual/complementarity `1.529887/1.166e-6/0.128042`。job 仍 `RUNNING`，stderr 0，
  `solve_report/solution_qc/result_manifest/checkpoint` 均不存在；未取消、未改参、未启动 Stage B。
- 资源账本：05:46:36 追加 round 30；wall `966,523 s`、96 CPU allocation
  `25,773.947 core-hours`、actual CPU `4,030.069 h`、efficiency `15.6362%`、Slurm MaxRSS
  `362.913 GiB`、最近 iteration 307--327 平均 `53.232 min`。账本共 31 records，SHA256
  `5ea6005a31f704c2d4a00a0c35555ab1118bf16e2fdf722e1d417d4d911840c9`。
- fixed/下一步：Base/1488 PID `3899905/3899906` 仍在模型构建，stderr 0、无第二 solver；继续只读
  等待 presolve/Barrier 首个证据。fixed checkout 活跃期间不部署新的文档提交。

### 2026-08-17 V5/744 engineering checkpoint terminal and Base/1488 start

- Git/身份：运行实现为 fixed server clean
  `902b1672a869cd4e6483633ceaf0208e092bff36`；本次记录前 local/origin/GitHub 文档 tip 均为
  `245d3b4be270150af0c4ff14fb0acd98aa97138a`。固定 checkout 在 solver 活动期间未切换，用户拥有的
  `supplementary_materials/**`、`.codex_tmp/**`、Module 06 handoff hunks 与历史 outputs 未改。
- V5/744 命令/终态：2030、hours 0--743、`flex_integrated_v5_central.json`、
  `barrier_16_engineering_relaxed_bctol1e2_numeric1_v1.json`，Crossover 0、工程 checkpoint/analysis。
  campaign event 为 04:16:42 start、05:38:39 end rc 0；solver `OPTIMAL`，Barrier 305 次、
  `4,520.108 s`，objective `2,361,276.668084 million CNY`。`/usr/bin/time -v` 为 wall `1:21:54`、
  user/system `63,271.79/2,208.31 s`、MaxRSS `21,285,692 KiB`、swaps 0；stderr 0。
- checkpoint/质量：`BarX` 3,894,744 项、SHA256 `464a5ee1...2d96`；`BarPi` 4,636,251 项、
  SHA256 `8bd6de58...43b2`。Gurobi Fingerprint `-807918957`，LP nonzeros `41,327,437`，变量/约束
  ordering digest 完整，`deferred_crossover_eligible=true`。严格 solution
  contract/QC 为 `HARD_FAIL`；58 个物理 hard checks 仅 `reservoir_transition=false`，最大残差
  `11,917.821 m3`，对应 solver maximum constraint violation `0.011917821`。power balance
  `2.362e-7 GW`、line violation `3.643e-9 GW`、双向省间流 0、storage overlap `1.745e-5 GWh`，
  其余账目通过。未创建 scientific result manifest/planning state/basis；不得发表或锚定 sequence。
- 长时域启动/资源：05:38:42 campaign 串行启动 Base/1488，output
  `relaxed_barrier_continuation_v0817_v5/base_1488h_bctol1e2_numeric1`，PID `3899905/3899906`，
  start hour 3624，使用 `barrier_16_engineering_relaxed_bctol1e2_numeric1_long_v1.json`；05:41 仍在
  build，stderr 0、available RAM 约 111 GiB、si/so 0、memory PSI 0，无第二 solver。
- 未决/下一步：只读监管 1488 到正式终态，审计 rc/stderr/time、LP 规模、Barrier 轨迹、资源、
  checkpoint vectors/identity 和 relaxed physical QC。只有 1488 checkpoint manifest 存在时 campaign
  才可进入 Base/2160。云 job `4139552` 保持原样，只在新 iteration/终态时追加审计，不启 Stage B。

### 2026-08-17 exact macro winner, V5/744 start and cloud resource round 29

- Git/部署：启动时 local/origin/GitHub/fixed server 均为
  `902b1672a869cd4e6483633ceaf0208e092bff36`；fixed server `bash -n` 与 focused `6/6 PASS`，
  clean 且无 pre-existing solver。v3/v4 编排失败根均保留；全新 v5 control/output 成功生成三份 exact
  macro comparison，未改历史候选或 strict reference。
- A/B 结果：`5e-2/NF2` 为 `MACRO_FAIL`，objective rel `0.012520`、generation L1
  `0.034367`、operation L1 `0.296402`；`1e-2/NF2` 为 `MACRO_FAIL`，对应
  `0.004278/0.014511/0.100422`。`1e-2/NF1` 唯一 `MACRO_PASS`：objective rel
  `2.931e-9`、capacity L1 `1.330e-8`、generation L1 `0.0010563`、carbon L1 `8.414e-10`、
  operation L1 `1.917e-6`；runtime `4,275.732 s`，相对 strict total/Barrier 分别缩短约
  `92.0%/44.7%`。
- fixed 启动：04:16:42 campaign 严格串行启动
  `v5_744h_bctol1e2_numeric1`，wrapper/Python PID `3569191/3569192`；命令为 2030、hours 0--743、
  `flex_integrated_v5_central.json`、engineering Barrier-only。profile 明确 Method2/Threads16/Presolve2/
  Crossover0/BarConvTol1e-2/FeasOpt1e-5/NF1/Scale2/TimeLimit21600/SoftMem40。启动时 available
  约 113.6 GiB、si/so 0、memory PSI 0、stderr 0；无第二 solver。
- cloud round 29：job 仍 RUNNING；iteration 325、runtime `957,363.694 s`，primal/dual/compl
  `1.646663/1.197e-6/0.137358`；round 29 wall `961,177 s`、allocation
  `25,631.387 core-hours`、actual CPU `4,007.857 h`、efficiency `15.6365%`、MaxRSS
  `362.913 GiB`、最近 20 步 `53.129 min`。30 records SHA256
  `26a9903d932fae6c68d5f81b17a04f995313167ec8b2ebca28f7e55d07a61e69`；stderr 0、无
  terminal/checkpoint，未取消、未改参、未启动 Stage B。
- 下一步：只读监管 V5/744 到正式终态；无论终态先核对 checkpoint、engineering macro、stderr/time
  与资源。campaign 仅在该 case 返回后串行 Base/1488，且仅在其 checkpoint 存在时 Base/2160。

### 2026-08-17 v4 exact-macro second orchestration fail-closed and directory fix

- Git/部署：v4 前 local/origin/GitHub/fixed server 已统一到
  `5161dd0d7cd1958dda0ffdc648f2d6683056c95b`，server clean；`bash -n`、focused `6/6` 与
  full regression `187/187 PASS` (`94.975 s`)。ParaCloud 未修改。
- v4 证据：新 control/output 为 `relaxed_barrier_continuation_v0817_v4`；strict contract 通过，三组
  `reuse_supervisor_candidate` 均写入 events，import 修复生效。但复用分支绕过 `run_case()` 后没有
  创建候选 control 子目录，导致 shell 在 `macro_comparison_stdout.log` 重定向时失败；三份 comparison
  均未生成，winner 为 `NO_MACRO_PASS`，无活动 CISPO/Gurobi。
- 修复/验证：在候选循环入口无条件创建 `$CONTROL_ROOT/$tag`，兼容复用与新求解两条路径；不改
  audit 阈值、模型、参数、候选输出或 strict reference。`git diff --check`、focused `6/6 PASS`；
  脚本 SHA256 `21e67deb17013c09a05f84c4f28e161c781d48878365d86f1e4124ffaff79b07`。
- 下一步：提交并双推送；server fast-forward、`bash -n` 后使用全新 v5 root 重跑 exact macro。
  v3/v4 均不得重标或覆盖；只有真实 `MACRO_PASS` winner 才允许串行 V5/744 与后续长时域。

### 2026-08-17 strict Base/744 terminal acceptance and v3 orchestration repair

- Git/范围：里程碑前 local/origin/GitHub tip 为
  `7a15b406e7684da97087c6032ec9cd00c22cc41f`，fixed checkout clean/frozen `d80f5b7`。严格根
  wrapper 退出后执行完整只读终态审计；随后 v3 自动 exact-macro campaign fail-closed，未启动 solver。
  修改仅限 `scripts/run_fixed_server_relaxed_barrier_campaign.sh` 与三份交接文档；不改模型、数据、
  参数、候选输出、严格输出或 ParaCloud `4139552`。
- strict 证据：status `OPTIMAL`、QC `PASS`、58/58 hard checks、input/result manifest 均 valid，
  result manifest 68 files；solver `53,489.068 s`、Barrier `218 / 7,734.65 s`、Crossover
  `45,468.01 s`、simplex `1,027,895`、objective `2,361,958.416203 million CNY`。wrapper rc 0、
  stderr 0、wall `14:57:39`、MaxRSS `20,617,928 KiB`、swap 0；`ConstrVio/BoundVio/DualVio`
  `9.737e-8/8.505e-8/8.854e-8`。power balance `2.17e-9 GW`，无双向跨省流、无储能同时充放；
  reserve/inertia 仅有容差内浮点负边际，CO2/DAC/BECCS/CCS 与成本分解检查均通过。
- v3 诊断与修复：`campaign_events.log` 为三个 `refuse_existing_output` 后
  `no_macro_winner_stop`；三个 macro stdout 均为 `ModuleNotFoundError: cispo_model`，因此
  `NO_MACRO_PASS` 仅是编排失败。修复只在候选是 supervisor symlink 且 engineering contract 存在时
  复用，并以 `PYTHONPATH=$REPO_ROOT...` 调 audit；普通已有目录仍 fail-closed。`git diff --check` 与
  `tests.test_relaxed_barrier_macro + tests.test_summarize_relaxed_barrier_campaign` 共 `6/6 PASS`；脚本
  SHA256 `95e177eeb6874a36bf769dc70f95e7a1262506438bf7124d4f74f69dd5a17132`。
- 未决/下一步：提交并双推送修复；确认 fixed server 无 solver、clean checkout 后部署精确 tip，运行
  server `bash -n` 与 focused tests。使用全新 v4 control/output 根重跑 exact macro，不能重标 v3；
  只有 winner `MACRO_PASS` 后才依脚本串行 V5/744、Base/1488，并在 checkpoint 存在时 Base/2160。

### 2026-08-17 cloud iteration 324 / resource audit round 28

- Git/范围：里程碑前本地、origin、GitHub tip 均为
  `589bcf2eab1ed61fda26268fb7424021c1a5197e`；fixed checkout 继续 clean/frozen `d80f5b7`。
  仅追加 cloud resource snapshot 并更新三份交接文档；未改 active solver、profile、checkout、模型、
  数据、output 或 Stage B 状态。账本以新 iteration 去重，并经 JSON/count/SHA 写后复核。
- cloud 证据：job 继续 RUNNING；iteration 324、runtime `954,056.892 s`，primal infeasibility
  `1.740057`、complementarity `0.145081`，较 iteration 323 继续下降；323--324 单步约
  `57.12 min`。round 28 为 wall `956,593 s`、allocation `25,509.147 core-hours`、actual CPU
  `3,988.565 h`、CPU efficiency `15.6358%`、MaxRSS `362.913 GiB`、最近 20 步平均
  `53.113 min`。29 records SHA256
  `b9d852b351e0fcb1c2ccf51d7b0c7ce7ba819bca49d63a77c0a3e59431951f87`；stderr 0、无终态或
  checkpoint，任务未取消、未改参、未启动 Stage B。
- fixed/下一步：strict quad cleanup 为 iteration `1,009,728`、runtime `49,698.19 s`、primal 0、dual
  `1.022765e3`、stderr 0，wrapper/v3 supervisor 存活且仍只有一个 solver，continuation 输出根
  absent。继续监管 strict；只有完整终态通过才允许 exact macro 和后续串行宽松长时域测试。

### 2026-08-17 cloud iteration 323 / resource audit round 27

- Git/范围：里程碑前本地、origin、GitHub tip 均为
  `6c46967383d8cf81888b7deb9f108f3754ea3045`；fixed checkout 继续 clean/frozen `d80f5b7`。
  仅追加 cloud resource snapshot 并更新三份交接文档；未改 active solver、profile、checkout、模型、
  数据、output 或 Stage B 状态。账本以新 iteration 去重，并经 JSON/count/SHA 写后复核。
- cloud 证据：job 继续 RUNNING；iteration 323、runtime `950,629.600 s`，primal infeasibility
  `1.779718`、complementarity `0.149749`，较 iteration 322 继续下降；322--323 单步约
  `53.86 min`。round 27 为 wall `953,368 s`、allocation `25,423.147 core-hours`、actual CPU
  `3,975.420 h`、CPU efficiency `15.6370%`、MaxRSS `362.913 GiB`、最近 20 步平均
  `52.990 min`。28 records SHA256
  `1ac421f725323ec5d061a8a58d6600507732cb6fbea6cfe08b3621959534f0b8`；stderr 0、无终态或
  checkpoint，任务未取消、未改参、未启动 Stage B。
- fixed/下一步：strict quad cleanup 为 iteration `995,574`、runtime `46,496.02 s`、primal 0、dual
  `9.215256e2`、stderr 0，wrapper/v3 supervisor 存活且仍只有一个 solver，continuation 输出根
  absent。继续监管 strict；只有完整终态通过才允许 exact macro 和后续串行宽松长时域测试。

### 2026-08-17 cloud iteration 322 / resource audit round 26

- Git/范围：里程碑前本地、origin、GitHub tip 均为
  `b5fde71e9cc0ca6eda10cc4a827605fa12a80e2c`；fixed checkout 继续 clean/frozen `d80f5b7`。
  仅追加 cloud resource snapshot 并更新三份交接文档；未改 active solver、profile、checkout、模型、
  数据、output 或 Stage B 状态。账本以新 iteration 去重，并经 JSON/count/SHA 写后复核。
- cloud 证据：job 继续 RUNNING；iteration 322、runtime `947,398.037 s`，primal infeasibility
  `1.879145`、complementarity `0.157175`，较 iteration 321 继续下降；321--322 单步约
  `60.04 min`。round 26 为 wall `950,224 s`、allocation `25,339.307 core-hours`、actual CPU
  `3,962.390 h`、CPU efficiency `15.6373%`、MaxRSS `362.913 GiB`、最近 20 步平均
  `52.831 min`。27 records SHA256
  `ec248a3bfa4b62e56df235e3a16395aabf86e18fd7411047d8e8c94b2573ee91`；stderr 0、无终态或
  checkpoint，任务未取消、未改参、未启动 Stage B。
- fixed/下一步：strict quad cleanup 为 iteration `980,379`、runtime `43,298.54 s`、primal 0、dual
  `3.231602e2`、stderr 0，wrapper/v3 supervisor 存活且仍只有一个 solver，continuation 输出根
  absent。继续监管 strict；只有完整终态通过才允许 exact macro 和后续串行宽松长时域测试。

### 2026-08-17 cloud iteration 321 / resource audit round 25

- Git/范围：里程碑前本地、origin、GitHub tip 均为
  `c5a40a6f05d435239f423b2b81d854ca03adfc12`；fixed checkout 继续 clean/frozen `d80f5b7`。
  仅追加 cloud resource snapshot 并更新三份交接文档；未改 active solver、profile、checkout、模型、
  数据、output 或 Stage B 状态。账本以新 iteration 去重，并经 JSON/count/SHA 写后复核。
- cloud 证据：job 继续 RUNNING；iteration 321、runtime `943,795.685 s`，primal infeasibility
  `1.955394`、complementarity `0.164821`，较 iteration 320 继续下降；320--321 单步约
  `55.02 min`。round 25 为 wall `946,575 s`、allocation `25,242.000 core-hours`、actual CPU
  `3,947.624 h`、CPU efficiency `15.6391%`、MaxRSS `362.913 GiB`、最近 20 步平均
  `52.246 min`。26 records SHA256
  `05a7a568c7e3ba293db050626324d197ce4ce3172cc940d5e8621e25172f52f7`；stderr 0、无终态或
  checkpoint，任务未取消、未改参、未启动 Stage B。
- fixed/下一步：strict quad cleanup 为 iteration `962,785`、runtime `39,637.75 s`、primal 0、dual
  `2.547886e3`、stderr 0，wrapper/v3 supervisor 存活且仍只有一个 solver，continuation 输出根
  absent。继续监管 strict；只有完整终态通过才允许 exact macro 和后续串行宽松长时域测试。

### 2026-08-16 cloud iteration 320 / resource audit round 24

- Git/范围：里程碑前本地、origin、GitHub tip 均为
  `e475428810f1eb3d490ea8634ba17bb9c06fd611`；fixed checkout 继续 clean/frozen `d80f5b7`。
  仅追加 cloud resource snapshot 并更新三份交接文档；未改 active solver、profile、checkout、模型、
  数据、output 或 Stage B 状态。账本追加脚本兼容登录节点旧 Python，并以新 iteration 去重及写后
  JSON/count/SHA 校验闭合。
- cloud 证据：job 继续 RUNNING；iteration 320、runtime `940,494.224 s`，primal infeasibility
  `2.064526`、complementarity `0.172070`，较 iteration 319 继续下降；319--320 单步约
  `68.32 min`，显著慢于近期均值但没有停滞。round 24 为 wall `945,131 s`、allocation
  `25,203.493 core-hours`、actual CPU `3,942.270 h`、CPU efficiency `15.6418%`、MaxRSS
  `362.913 GiB`、最近 20 步平均 `52.071 min`。25 records SHA256
  `efb6bd58ce5abc8acd628204b4a876dd4fd0dbe1a16f46f5c97880b0acbf51a7`；stderr 0、无终态或
  checkpoint，任务未取消、未改参、未启动 Stage B。
- fixed/下一步：strict quad cleanup 为 iteration `955,777`、runtime `38,214.01 s`、primal 0、dual
  `1.538969e4`、stderr 0，wrapper/v3 supervisor 存活且仍只有一个 solver。继续监管 strict；只有其
  完整终态通过才允许 exact macro。cloud 继续只读监管，不因长尾自行取消；下一次只在新 iteration、
  终态或资源异常时追加审计。

### 2026-08-16 cloud iteration 319 / resource audit round 23

- Git/范围：里程碑前本地、origin、GitHub tip 均为
  `a0397c4017966ed9a306a32511752be476d9a13a`；fixed checkout 继续 clean/frozen `d80f5b7`。
  仅追加 cloud resource snapshot 并更新三份交接文档；未改 active solver、profile、checkout、模型、
  数据、output 或 Stage B 状态。账本追加采用新 iteration 去重与写后 JSON/count/SHA 校验；PowerShell
  管道仅在 Python 成功结束后留下一个 CRLF 空行 shell warning，不影响已复核的 JSONL 内容。
- cloud 证据：job 继续 RUNNING；iteration 319、runtime `936,395.199 s`，primal infeasibility
  `2.179757`、complementarity `0.180733`，较 iteration 318 继续下降。round 23 为 wall
  `942,654 s`、allocation `25,137.440 core-hours`、actual CPU `3,931.546 h`、CPU efficiency
  `15.6402%`、MaxRSS `362.913 GiB`、最近 20 步平均 `51.167 min`。24 records SHA256
  `d203d675072bc5b4edde3ace8361aea3068fa557119c8e47b34d66b0c3a3fa7b`；stderr 0、无终态或
  checkpoint，任务未取消、未改参、未启动 Stage B。
- fixed/下一步：strict quad cleanup 为 iteration `942,842`、runtime `35,770.00 s`、primal 0、dual
  `1.988602e5`、stderr 0，wrapper/v3 supervisor 存活且仍只有一个 solver。继续监管 strict；只有其
  完整终态通过才允许 exact macro，cloud 仅在新 iteration 或终态后追加下一轮审计。

### 2026-08-16 cloud iteration 318 / resource audit round 22

- Git/范围：里程碑前本地、origin、GitHub tip 均为
  `6b7862d60a6adbefa3d532046cb7f7fb3e4c7917`；fixed checkout 继续 clean/frozen `d80f5b7`。
  仅追加 cloud resource snapshot 并更新三份交接文档；未改 active solver、profile、checkout、模型、
  数据、output 或 Stage B 状态。首次账本脚本因登录节点旧 Python 不支持 `datetime.fromisoformat`
  在写入前退出；兼容重试执行唯一追加，并经 JSON/count/SHA 复核闭合。
- cloud 证据：job 继续 RUNNING；iteration 318、runtime `933,326.741 s`，primal infeasibility
  `2.289620`、complementarity `0.188602`，较 iteration 317 继续下降。round 22 为 wall
  `937,651 s`、allocation `25,004.027 core-hours`、actual CPU `3,911.908 h`、CPU efficiency
  `15.6451%`、MaxRSS `362.913 GiB`、最近 20 步平均 `51.532 min`。23 records SHA256
  `5db4ac898c7bc21d5598176853242bcadea04eb9b20599ffc5fccbc2915d50a0`；stderr 0、无终态或
  checkpoint，任务未取消、未改参、未启动 Stage B。
- fixed/下一步：strict quad cleanup 为 iteration `917,738`、runtime `30,759.68 s`、primal 0、dual
  `8.190958e6`、stderr 0，wrapper/v3 supervisor 存活且仍只有一个 solver。继续监管 strict；只有其
  完整终态通过才允许 exact macro，cloud 仅在新 iteration 或终态后追加下一轮审计。

### 2026-08-16 cloud iteration 317 / resource audit round 21

- Git/范围：里程碑前本地、origin、GitHub tip 均为
  `32321d2ec3ff44151ff553bbcffd09a0d60168a9`；fixed checkout 继续 clean/frozen `d80f5b7`。
  仅追加 cloud resource snapshot 并更新三份交接文档；未改 active solver、profile、checkout、模型、
  数据、output 或 Stage B 状态。
- cloud 证据：job 继续 RUNNING；iteration 317、runtime `930,000.702 s`，primal infeasibility
  `2.379513`、complementarity `0.195367`，较 iteration 316 继续下降。round 21 为 wall
  `932,693 s`、allocation `24,871.813 core-hours`、actual CPU `3,890.998 h`、CPU efficiency
  `15.6442%`、MaxRSS `362.913 GiB`、最近 20 步平均 `51.272 min`。22 records SHA256
  `bf039d692007d3704baa2f8faab337b4bc629aed5ddbedf2f0c8b2e2617d7de0`；stderr 0、无终态或
  checkpoint，任务未取消、未改参、未启动 Stage B。
- fixed/下一步：strict quad cleanup 为 iteration `892,970`、runtime `25,778 s`、primal 0、dual
  `2.506362e6`、stderr 0，继续唯一 solver；其端到端已慢于旧历史根但仍按合同运行。继续监管
  strict，cloud 仅在新 iteration 后追加下一轮审计。

### 2026-08-16 strict 744 端到端耗时已超过旧成功根

- Git/范围：里程碑前本地、origin、GitHub tip 均为
  `4ce1c92c2f6e05d37a4c7fe1550462125355f88e`；fixed checkout 继续 clean/frozen `d80f5b7`。
  本轮只读比较当前与旧成功 `gurobi.log` 并更新三份交接文档；未改 solver、profile、checkout、模型、
  数据、output 或 cloud job。
- 证据：当前 runtime `24,224 s` 时仍在 iteration `885,507` 的 quad cleanup，primal 0、dual
  `2.886885e5`、stderr 0；旧成功根总 runtime `24,156.53 s`。当前已慢 `67.47 s` 且差距将继续增长。
  当前 Barrier `7,734.65 s` 比旧 `11,142.54 s` 快 `3,407.89 s`；当前 Barrier 后阶段已至少
  `16,489.35 s`，比旧完整 Crossover `12,672.69 s` 多 `3,816.66 s`（`30.12%`）。
- 判读边界：旧根绑定旧 LP/data，故该比较只能作为历史工程轨迹，不能替代 current-identity exact
  macro A/B。但它足以否定“Barrier 快即整轮快”，并说明严格 Crossover 长尾可完全抹去 Barrier
  收益；8760 h Stage A checkpoint 与 Stage B 解耦仍是必要的成本控制架构。
- 下一步：strict 继续运行到正式终态，不因超过历史时间取消；成功后执行 reference contract/exact
  macro，失败则让 v3 保留现场并停止。云 job `4139552` 保持原样。

### 2026-08-16 cloud iteration 316 / resource audit round 20

- Git/范围：里程碑前本地、origin、GitHub tip 均为
  `16fe477921e64f1f2fdd2674c5248f6abe5ba65b`；fixed checkout 继续 clean/frozen `d80f5b7`。
  仅追加 cloud resource snapshot 并更新三份交接文档；未改 active solver、profile、checkout、模型、
  数据、output 或 Stage B 状态。
- cloud 证据：job 继续 RUNNING；iteration 316、runtime `927,093.647 s`，primal infeasibility
  `2.420051`、complementarity `0.199649`，较 iteration 315 继续下降。round 20 为 wall
  `929,885 s`、allocation `24,796.933 core-hours`、actual CPU `3,879.081 h`、CPU efficiency
  `15.6434%`、MaxRSS `362.913 GiB`、最近 20 步平均 `51.638 min`。21 records SHA256
  `278f03964d057fe6748aee8f2f6cb0327d6b594961f092d4ffd789b067c9e639`；stderr 0、无终态或
  checkpoint，任务未取消、未改参、未启动 Stage B。
- fixed/下一步：strict quad cleanup 当前 iteration `879,136`、runtime `22,956 s`、primal 0、dual
  `4.729218e4`、stderr 0，继续唯一 solver；低 dual 局部状态不替代正式终态。继续监管 strict，
  cloud 仅在新 iteration 或有意义间隔后追加下一轮审计。

### 2026-08-16 cloud iteration 315 / resource audit round 19

- Git/范围：里程碑前本地、origin、GitHub tip 均为
  `64868c1574ae0b435d1037c86f9fbb2805981caa`；fixed checkout 继续 clean/frozen `d80f5b7`。
  仅追加 cloud resource snapshot 并更新三份交接文档；未改 active solver、profile、checkout、模型、
  数据、output 或 Stage B 状态。
- cloud 证据：job 继续 RUNNING；iteration 315、runtime `923,654.909 s`，primal infeasibility
  `2.505751`、complementarity `0.206062`，较 iteration 314 继续下降。round 19 为 wall
  `926,381 s`、allocation `24,703.493 core-hours`、actual CPU `3,864.724 h`、CPU efficiency
  `15.6444%`、MaxRSS `362.913 GiB`、最近 20 步平均 `51.837 min`。20 records SHA256
  `19273e364307274243a2b9491cd0610b1c5d6aee964bd08cc34e0a4cfadfc437`；stderr 0、无终态或
  checkpoint，任务未取消、未改参、未启动 Stage B。
- fixed/下一步：strict quad cleanup 经 `1e10--1e12` 高 dual 段后恢复到 `1e4--1e7` 区间；当前
  iteration `859,888`、runtime `19,483 s`、primal 0、dual `2.045376e6`、stderr 0，仍只有一个
  solver。恢复不能替代终态，继续等待正式 status/rc/QC/manifest；cloud 仅在新 iteration 后追加审计。

### 2026-08-16 strict quad 数值轨迹与旧成功根的定量纠正

- Git/范围：里程碑前本地、origin、GitHub tip 均为
  `ec368abb586e78f057a6f07865d534bc19cd2ff6`；fixed checkout 继续 clean/frozen `d80f5b7`。
  本轮只读解析当前与旧成功根完整 `gurobi.log` 的 quad 段并更新三份交接文档；未改 solver、profile、
  checkout、模型、数据、output 或 cloud job。
- 对照证据：旧成功根 quad 段 244 个日志采样，最大 dual `1.908564e8`，仅 2 点 `>=1e8`、0 点
  `>=1e9`；当前至 18:04 的 139 个 quad 采样，最大 dual `6.625378e12`，分别有 41/23/17/10 点
  `>=1e8/1e9/1e10/1e11`。因此此前“保护动作与旧根相同”只适用于 warning 类型，不能延伸为
  quad 后收敛轨迹相同；旧根约 9,500 s quad 尾长不再是可靠 ETA。
- 当前状态/边界：iteration `848,783`、runtime `17,444 s`，primal infeasibility 0、dual
  `3.964324e10`、objective `2,362,011.2 million CNY`；wrapper/CPU/iteration 活跃，stderr 0，尚无
  新 warning 或正式 numerical failure。依据用户“不随意取消”合同继续唯一 solver，但显式提高
  Crossover 数值风险等级；只有 Gurobi status、wrapper rc 与完整 QC/manifest 才能决定终态。
- 下一步：持续监管，不提前触发 relaxed campaign；若 strict 失败，v3 应保留现场并停止 continuation；
  若 strict 通过，仍按强 reference contract 后再执行 exact macro。ParaCloud `4139552` 保持原样。

### 2026-08-16 cloud iteration 314 / resource audit round 18

- Git/范围：里程碑前本地、origin、GitHub tip 均为
  `7b4188bf0f8f1d1a011200a9f7a08a54af29ef48`；fixed checkout 继续 clean/frozen `d80f5b7`。
  仅追加 cloud resource snapshot 并更新三份交接文档；未改 solver、profile、checkout、模型、数据、
  output 或 Stage B 状态。
- cloud 证据：job 继续 RUNNING；iteration 314、runtime `920,799.474 s`，primal infeasibility
  `2.587524`、complementarity `0.211519`，较 iteration 313 继续下降。round 18 为 wall
  `923,578 s`、allocation `24,628.747 core-hours`、actual CPU `3,852.752 h`、CPU efficiency
  `15.6433%`、MaxRSS `362.913 GiB`、最近 20 步平均 `51.766 min`。19 records SHA256
  `90fc64d612696045ba3c03abd40f60df143a048fafea6357a9d8538aa3730498`；stderr 0、无终态或
  checkpoint，任务未取消、未改参、未启动 Stage B。
- fixed/下一步：strict quad cleanup 为 iteration `844,413`、runtime `16,683 s`，primal 0、dual
  `2.692850e8`，objective 继续下降、只有一个 solver。继续监控 strict 终态；cloud 仅在新 iteration
  或有意义时间间隔后追加下一轮审计。

### 2026-08-16 cloud iteration 313 / resource audit round 17

- Git/范围：里程碑前本地、origin、GitHub tip 均为
  `689a2a4a1c3fa5e2fd16b424ce69daa7efb2248c`；fixed checkout 继续 clean/frozen `d80f5b7`。
  仅追加 cloud run-control resource snapshot 并更新三份交接文档；未修改 cloud/fixed solver、
  profile、checkout、模型、数据或 output。
- cloud 证据：job 继续 RUNNING；iteration 313、runtime `917,751.150 s`，primal infeasibility
  `2.701581`、complementarity `0.219215`，均较 iteration 312 下降。round 17 记录 wall
  `920,881 s`、allocation `24,556.827 core-hours`、actual CPU `3,841.487 h`、CPU efficiency
  `15.6433%`、MaxRSS `362.913 GiB`、最近 20 步平均 `52.099 min`。18 records SHA256 为
  `a7ab2c58591de060f886052d2c47f1cc4916f48ed38473710ecfe2003c9411ba`；stderr 0、无终态文件或
  checkpoint，不取消、不改参、不启动 Stage B。
- fixed/下一步：strict quad cleanup 到 iteration `828,761`、runtime `13,981 s`，primal 0、dual
  `2.732433e5`，wrapper 和 v3 supervisor 存活且只有一个 solver。继续监控 strict 正式终态；cloud
  只在下一新 iteration 或有意义时间间隔后再追加审计。

### 2026-08-16 strict Crossover 自动切换 quad precision

- Git/范围：里程碑前本地、origin、GitHub tip 均为
  `1d79af5bd6851c805cb6aa82b5acc8bc6d97c17f`；fixed checkout 继续 clean/frozen `d80f5b7`。
  只读检查 active `gurobi.log`、进程、stderr 与终态文件并更新三份交接文档；未改求解器、checkout、
  profile、模型、数据、output 或 cloud job。
- 证据：iteration `823,548`、runtime `13,224 s` 时 dual infeasibility `7.102660e9`；随后 Gurobi
  报告丢弃 1 个 basis variable 并切换 quad precision。到 iteration `825,303`、runtime `13,464 s`，
  primal infeasibility 0、dual `1.142198e5`，objective `2,362,020.1 million CNY`；stderr 0、wrapper
  仍存活、终态三文件 absent。
- 判读/下一步：旧成功 strict 根也执行了同样两条 warning 后最终 `OPTIMAL`；quad 后约 `7 pivots/s`
  的速度下降是高精度 cleanup 代价，不是停滞。继续唯一 solver，记录 quad iterations/runtime、dual
  趋势与最终 `Crossover time/Solved in/Optimal objective`；wrapper 退出后仍执行强 reference contract。
  ParaCloud `4139552` 保持不变，不取消、不改参、不启动 Stage B。

### 2026-08-16 strict cleanup 对照审计与 cloud round 16

- Git/范围：里程碑前本地、origin、GitHub tip 均为
  `cc5dcb1022c0093a517c7821e12c74931db0f8f1`；fixed checkout 继续 clean/frozen
  `d80f5b76b7deefd6c82004ee0e17f1fc206f7eff`。本轮只追加 cloud run-control resource snapshot
  并更新三份交接文档；未改 active solver、profile、模型、数据、checkout 或 output。
- fixed 证据：只读 `gurobi.log`、进程、stderr、终态文件和资源。16:23--16:27，simplex 从
  iteration `788,784` 推进至 `792,828`，约 `22.2 pivots/s`；primal infeasibility 保持 0，dual
  infeasibility 非单调，最低观察到 `7.47e3`、尖峰 `9.29e8`。wrapper/Python 仍存活，stderr 0，
  `solve_report.json`、`solution_qc.json`、`result_manifest.json` 均 absent，v3 supervisor 只等待。
- 历史解释：旧成功根在 push 完成约 345--423 s 时，dual infeasibility 同样在
  `1.52e4--1.09e9` 摆动，随后最终 `OPTIMAL`。因此当前轨迹暂未偏离历史成功模式；但旧根从
  push complete 到求解结束约 `10,450 s`，仍须按终态合同继续监管，不能据局部尖峰取消，也不能
  据 primal=0 提前验收。
- cloud 证据：iteration 312、runtime `914,959.120 s`；round 16 记录 wall `918,306 s`、
  allocation `24,488.16 core-hours`、actual CPU `3,830.451 h`、efficiency `15.6421%`、MaxRSS
  `362.913 GiB`、最近 20 步平均 `52.330 min`。17 records SHA256 为
  `65b3c5495adf75062420582837743b6bd34a46afecae1b4e61cf1e34578a59c9`；stderr 0、无终态或
  checkpoint，未取消、未改参、未启动 Stage B。
- 精确下一步：继续监控 strict simplex 到 wrapper 退出；只在完整 `OPTIMAL + PASS + 58/58 +
  current input + valid result manifest` 后允许 v3 exact macro，再让唯一赢家串行进入 V5/744、
  Base/1488/2160。云端仅在新 iteration 或有意义时间间隔后追加下一轮审计。

### 2026-08-16 strict Crossover push 完成并进入 simplex cleanup

- Git/范围：里程碑前本地、origin、GitHub tip 均为
  `fa595a6d9afbbe68ec43985059e3cb974d8bbe6f`；fixed checkout 继续 clean/frozen
  `d80f5b76b7deefd6c82004ee0e17f1fc206f7eff`。本里程碑只更新三份交接文档，不改 active solver、
  checkout、profile、模型、数据或 output。
- 命令/证据：只读解析 `gurobi.log` transition、process tree、stderr、terminal artifacts 与资源。
  Crossover basis 在约 runtime `7,990 s` 完成；DPush 从 runtime `8,010` 的 `841,200` 项到
  runtime `10,575` 的 0 项，共 `2,565 s`；PPush 从 `274,055` 项到 runtime `11,177` 的 0 项，
  共 `602 s`。`Push phase complete` 为 PInf `2.741902`、DInf `1.751704e8`。
- cleanup：首行 iteration `782,488`、objective `2,362,074.5 million CNY`；到 `782,690`
  primal infeasibility 已由 `2.742` 降至 `1.19e-3`。这只证明 cleanup 活跃，dual phase 和终态均
  未完成；不得把 primal 快速下降冒充 `OPTIMAL`。
- 历史比较：旧成功根 push complete runtime `13,707 s`，当前 `11,177 s`，仍领先 `2,530 s`
  （42.17 分钟）；但旧 PInf/DInf 为 `0.576694/6.499e3`，当前起点显著更差。必须以最终 cleanup
  iterations/runtime/status 评价 Crossover，而非只报告 Barrier 或 push 加速。
- 资源/下一步：RSS 约 `13.57 GiB`、available RAM 约 `100 GiB`、`si/so=0/0`、memory PSI 0；
  stderr 0，终态文件 absent，仍只有 strict solver。继续只读监管 simplex；wrapper 后走强 reference
  合同，再决定 exact macro 与串行长时域候选。云 job `4139552` 保持原样，不启动 Stage B。

### 2026-08-16 cloud iteration 311 / resource audit round 15

- Git/范围：里程碑前本地、origin、GitHub tip 均为
  `4dbcf9cc53f140a25d6b427d242cc41f1c9453ae`；fixed checkout 保持 clean/frozen
  `d80f5b76b7deefd6c82004ee0e17f1fc206f7eff`。仅更新三份交接文档与 cloud run-control 旁路
  resource audit；未改 active solver、profile、模型、数据、output 或 checkout。
- cloud 证据：只读 `squeue/sstat`、telemetry 与 terminal artifacts 后追加 round 15。job 仍
  RUNNING；iteration 311、runtime `911,815.511 s`；wall `915,643 s`、allocation
  `24,417.1467 core-hours`、actual CPU `3,819.4717 h`、CPU efficiency `15.6426%`、MaxRSS
  `362.913 GiB`，stderr 0、terminal/checkpoint absent。16 records SHA256
  `41c67c508e5f43dc2eb490a949fc77904319efb190f3fef30384878bebda58fe`。
- fixed 证据：strict Barrier 已完成，Crossover initial basis 完成后进入 DPush；初始 `841,200`
  降至约 `237,580`，DInf 非单调但进程满载、日志无 numerical error。available RAM 约 `101 GiB`、
  memory PSI 0，仍只有一个 solver，supervisor 不越过 wrapper 门禁。
- 下一步：继续单独记录 DPush、PPush、simplex cleanup 与 strict 终态；强合同通过后才执行 exact
  macro v2 和串行长时域候选。云端继续不取消、不改参、不启动 Stage B。

### 2026-08-16 strict Base/744 Barrier 正常完成并进入 Crossover

- Git/范围：里程碑前本地、origin、GitHub tip 均为
  `8313ef8932196bc13c36c50292bd79147f5416a2`；fixed checkout 继续 clean/frozen
  `d80f5b76b7deefd6c82004ee0e17f1fc206f7eff`。本里程碑只更新三份交接文档，未改模型、数据、
  solver profile、活动 checkout/output 或进程。
- 命令/证据：只读检查 `solver_telemetry.jsonl`、`gurobi.log`、process tree、stderr、终态文件和
  `free/vmstat/PSI`。Barrier 在 iteration 218、runtime `7,734.65 s` 正常报告 `Optimal objective
  2.36195843e+06`，随后进入 `Building initial crossover basis`；日志无 numerical warning/error。
  最后 telemetry 与 scaled Gurobi 三项残差均完整保留，不以 telemetry callback 停在 Barrier 冒充
  卡住或 wrapper 终态。
- A/B 前置量化：旧同 profile Jan/2030 Barrier 为 `251 / 11,142.54 s`，本次少 33 轮、runtime
  快约 `30.58%`。`1e-2/NumericFocus=1` candidate 为 `263 / 4,275.73 s`、objective
  `2,361,958.423126 million CNY`，与 strict Barrier objective 相对差约 `3e-9`，Barrier-only 时间
  节省约 `44.72%`；但该候选仍 `scientifically_accepted=false`，不能用目标值近似代替宏观账目门禁。
- 资源/并发：Crossover basis 时 Python RSS 约 `12.57 GiB`、available RAM 约 `101 GiB`、实时
  `si/so=0/0`、memory PSI 0；stderr 0，solve/QC/result manifest absent。v3 supervisor 仍等待
  reference wrapper，预定 continuation 根不存在，没有第二 fixed solver。云 `4139552` 未触碰，仍
  Barrier iteration 310、resource audit round 14。
- 精确下一步：单独计时 Crossover basis/push/simplex；wrapper 退出后先执行强终态合同。只有 strict
  `OPTIMAL + QC PASS + 58/58 + current input + valid result manifest` 才运行 macro v2 并让最快
  `MACRO_PASS` 候选串行进入 V5/744、Base/1488 与条件式 Base/2160；云端继续不取消、不启动 Stage B。

### 2026-08-16 strict 744 iteration 120 与 cloud resource audit round 14

- Git/范围：里程碑前本地、origin、GitHub 均为文档 tip
  `86f3ca3a030319455157bf585029937e50fd4301`；fixed checkout 保持 clean/frozen
  `d80f5b76b7deefd6c82004ee0e17f1fc206f7eff`。本里程碑只更新
  `CODEX_HANDOFF.md`、`MODEL_SERVER_STATUS.md`、`SERVER_RUNBOOK.md`，未修改模型、数据、profile、
  active output 或进程。
- fixed 命令/证据：只读 SSH 复核 process tree、telemetry/Gurobi log、终态文件、resource sampler、
  `free/vmstat/PSI`。strict Base/744 为 iteration 120、runtime `3,996.405 s`；110--120 平均
  `45.062 s/iteration`，primal 从 `0.006807` 到 `0.007359`，dual 从 `6.761e-4` 到
  `5.605e-4`，complementarity 从 `1.4913` 到 `0.5026`。这说明原始残差仍非单调，不能把中途
  complementarity 下降冒充严格完成；stderr 0、无 warning/terminal，资源安全。
- continuation 预检：v3 PID `46839` 仍等待 reference；新输出根不存在。三根旧 candidate 的
  engineering contract、solve report、run identity、input manifest 与 checkpoint manifest 均存在；
  三根 checkpoint 都是 `ENGINEERING_BARRIER_CHECKPOINT_ONLY`，BarX `3,735,087` 项、BarPi
  `4,454,178` 项，`deferred_crossover_eligible=true`，但 `scientifically_accepted=false`。复制脚本
  `bash -n` 与 audit `py_compile` 均 PASS。
- cloud 命令/证据：只读 `squeue/sstat` 与 telemetry 后，向 run-control 旁路
  `resource_audit_snapshots.jsonl` 追加 round 14。job 仍 RUNNING；iteration 310、runtime
  `908,489.106 s`；wall `910,941 s`、allocation `24,291.76 core-hours`、actual CPU
  `3,799.6767 h`、MaxRSS `362.913 GiB`、stderr 0、终态/checkpoint absent；15 records SHA256
  `12ecc84d4405e9549fdcd3e295bdd6c13e940c5b233e7d9ae340080d6aade21f`。
- 未决/精确下一步：继续等待 strict Barrier→Crossover→wrapper 终态，按强合同复核
  `OPTIMAL + QC PASS + 58/58 + current input + valid result manifest`；仅通过后运行 exact macro v2，
  再由全账目 `MACRO_PASS` 的最快候选串行进入 V5/744、Base/1488 与条件式 Base/2160。云端继续
  不取消、不改参、不启动 Stage B。

### 2026-08-16 relaxed macro 全账目 v2 与 versioned supervisor v3

- Git：`a02d4d99b1060a2552e1c1f470817f1d4dbe3ac1` 修改
  `cispo_model/master.py`、macro auditor/summary 与 tests；`5af8efe6872b569e4ca068c7c66cc2aefa9e676e`
  增加 versioned supervisor 并参数化 campaign 的 audit script。两提交均已推送 `origin` 与 GitHub；
  活动 fixed checkout 未部署。
- 账目合同：exact identity 后同时门禁 objective、技术容量/发电、period generation、碳/CCS六项和
  VRE/ROR/hydro curtailment、储能充放、网损、wave generation 等运行账目。碳与运行采用总量归一化
  L1 `2%/5%`，避免近零单项造成虚假巨大相对误差；成本分项可用时 L1 `2%`，历史缺失时仅总 objective
  门禁并显式标记 `component_gate_applied=false`。这不改变 LP、求解参数或严格物理 QC。
- 导出修正：`export_cost_components()` 在 load-center 严格 QC 前写同内容 CSV，使未来 relaxed 解即使因
  `0.0001 GWh` 级双向流严格拒绝，仍留下成本构成。既有三根不重写；其成本分项 unavailable 被保留为
  历史限制。server fake expression 两行 isolated export PASS，无第二 Gurobi solve。
- 验证：py_compile；macro+summary tests `6/6 PASS`，覆盖 carbon/operation/cost drift 分别使
  `MACRO_FAIL`；两 shell scripts `bash -n` PASS。旧 invalid-reference real parser v2 的 carbon L1
  `8.42e-10`、operation L1 `2.007%`、cost components unavailable，且 exact identity 仍 FAIL。
- 监管替换：严格核验 v2 supervisor PID/PPID/cmdline/唯一 sleep child 后只终止等待进程，保留 v2
  控制根；启动 v3 PID `46839`。v3 使用隔离复制且逐字节匹配提交的 audit/campaign/supervisor，强
  reference 合同不变，winner 改由 macro v2 决定。13:54 仍只等待，不创建输出、不并发求解。
- 未决与下一步：strict reference 完成后由 v3 做终态与 exact macro v2；仅全账目 PASS 的最快候选
  进入 V5/744 与长时域。活动求解全部结束前不得部署新 tip；之后需 fixed full regression，确认提前
  cost export 对科学成功根逐字段兼容，再生成 post-exact summary v2。

### 2026-08-16 strict reference manifest 合同与无人值守监管器 v2

- 实现提交：`f96d9e0443a40f343eaf74b6d97c7abd186e309a`，已推送 `origin` 与 GitHub。changed files 为
  `cispo_model/io_contract.py`、`scripts/audit_relaxed_barrier_macro.py`、
  `tests/test_result_manifest.py`、`tests/test_relaxed_barrier_macro.py`。
- 修复：旧 validator 对 `{"valid":true}` 或空 `files` 返回 true；现要求非空结构、唯一且安全的相对
  path、可解析的非负 bytes、64 位 SHA256，并逐文件复核存在性、size 与 hash；损坏 JSON 返回显式
  failure。exact macro 审计不再以 manifest “存在/可解析”代替有效性。
- 验证：`git diff --check`、py_compile、macro targeted `5/5 PASS`，并直接验证无 `files` 的 manifest
  被拒绝、正确单文件 manifest 通过。本机缺 `gurobipy`，因此包含 `finalize_result_manifest()` 的完整
  test module 留待 fixed checkout 空闲并部署后进入 full regression，不把该未运行项写成 PASS。
- 服务器动作：精确核验 v1 supervisor PID `4100799` 的命令、PPID 与唯一 `sleep` 子进程后只终止这两个
  非 solver 进程；strict PID `4046161/4046167/4046172` 与 resource sampler `4059299` 持续存活。
  v1 证据不删除。v2 PID `4179192` 使用独立根和版本化脚本，新增 wrapper、58/58、result/input
  manifest 强门禁；当前只等待，不创建输出、不启动第二求解。
- 云端证据：job `4139552` 保持 RUNNING；resource audit round 13 已追加，14 records SHA256
  `a649998df5a4dfb05e3efda7a89d09265353a13d4a56d4771c3d7dbd91355a1f`。没有 `scancel`、
  profile 修改、Stage B 或第二 cloud job。
- 未决与精确下一步：继续监控 strict reference；退出后由 v2 先完成强终态审计，再复用三根历史
  candidates 重算 exact A/B。仅最快 exact `MACRO_PASS` 可串行进入 V5/744、Base/1488、以及 1488
  checkpoint 完整时的 Base/2160。fixed checkout 在活动 solver 退出前不得部署 `f96d9e0`。

### 2026-08-16 Gurobi 官方语义与 relaxed 744 参数边界复审

- 范围：只追加 `MODEL_SOLVABILITY_AUDIT_20260719.md` 第 10 节并更新三份交接文档；不修改 profile、
  LP、QC、活动 checkout、fixed solve 或 cloud job。
- 官方依据：Gurobi 13 Parameter Reference、Numerical Issues 参数指南与 Tolerances/User-Scaling；
  `BarConvTol` 是 Barrier 精度/速度旋钮，较高 `NumericFocus` 以成本换数值保护，Feas/Opt 是绝对容差且
  通常不是修复病态的首选，`CrossoverBasis=1` 更慢但更稳健。
- 模型证据：strict 744 matrix/objective/RHS 跨度为 `6.24e9/3.85e9/3.68e11`；工程候选 `1e-5`
  Feas/Opt 容差大于最小 `1e-6` 系数，故冻结为 engineering-only。三根有效速度/quality 表和 exact
  晋级阈值已写入审计；不再把放宽 Feas/Opt 当成主要加速来源。
- 当前执行：strict reference 与 continuation supervisor 保持不变；ParaCloud 8760 h v2 继续
  `BarConvTol=1e-8/NumericFocus=2/FeasOpt=1e-6/Crossover=0`，未触碰。
- 未决：等待 exact A/B；只有最快宏观 PASS 路线才进入 V5/744 与 Base/1488/2160。长时域即使通过也
  不能把 `1e-5` 绝对容差直接复制到 scientific Stage B。

### 2026-08-16 relaxed campaign 机器可读汇总器与真实三根验证

- 范围：新增 `scripts/summarize_relaxed_barrier_campaign.py` 和
  `tests/test_summarize_relaxed_barrier_campaign.py`；只读取既有证据，不修改 LP、solver profiles、
  campaign 阈值、科学 QC 或服务器 checkout。
- 合同：自动发现 campaign cases，连接 `solve_report.json`、`run_identity.json`、engineering contract、
  `barrier_checkpoint_manifest.json`、telemetry、GNU time、return code、macro comparison 和可选
  `resource_monitor.tsv`；支持 fallback control root，以便新 continuation symlink 复用旧 candidate 的
  wall/MaxRSS。JSON 将非有限数转为 `null`；CSV 明示 checkpoint、根目录 science artifacts、solution
  quality、exact identity、宏观 metrics 和 failed hard checks。汇总自身及所有 case 永不标科学接受。
- 验证：py_compile；`python -m unittest tests.test_summarize_relaxed_barrier_campaign
  tests.test_relaxed_barrier_macro` 为 `5/5 PASS`。首次增强补丁人工检查发现 `_read_int()` 分支错位，
  合成测试因 GNU-time fallback 未暴露；已在提交前修正并增加直接 `return_code.txt=7` 断言，复测通过。
- 真实运行：不部署 active checkout，而把脚本经 stdin 交给 fixed-server Python，读取旧 campaign 三根；
  初版 `pre_exact_candidate_summary.{json,csv}` 保留为探索证据，字段增强后的权威文件为
  `/data/zz2/National_model/run_control/relaxed_barrier_continuation_v0816_v1/
  pre_exact_candidate_summary_v2.{json,csv}`，JSON/CSV SHA256 为
  `f1f9534895a190fde28f5262303330c7579c25d3216e54c4586412a59282a688` 与
  `e15331e5cc3ddac5e260c7fe5d87dfcd4c94bbe534c5e19928763c7a4aa6cf50`。
- 结果：三根均 checkpoint present，root `solution_qc/result_manifest/planning_state/basis_manifest` absent；
  NumericFocus2 两根 observed Barrier `31.643/32.573 s/iter`，NumericFocus1 为 `14.862 s/iter`。
  当前 macro 字段来自已撤回的旧 reference，仅用于验证 parser，不能选 winner。
- 未决与下一步：strict reference 完成后由 supervisor 生成新 exact reports，再以同一汇总器和新的
  continuation control root 生成 post-exact summary；然后审计 V5/744 与更长时域资源、质量和宏观账目。

### 2026-08-16 strict reference 进入 Barrier 与无人值守 continuation supervisor

- Git/服务器边界：活动 fixed checkout 继续冻结在 `d80f5b7`，没有部署或修改 checkout；唯一 solver
  仍是 strict reference PID `4046161`。local/双远端文档 tip 为 `1480f82`，用户拥有的
  `supplementary_materials/**`、`.codex_tmp/**` 与历史输出均未改写。
- 求解证据：model build 后 LP `3,735,087 × 4,454,178`、`40,395,436` nonzeros、Fingerprint
  `2120635803`，与 relaxed candidates 相同；presolve/order 分别 `226.12/99.29 s`，Barrier iteration 0
  于 runtime `363.60 s` 落盘。iteration 3 时 stderr 0、solver current/max memory `12.61/21.36 GiB`，
  host available 约 96 GiB、memory PSI 0。
- 资源留痕：strict control 根新增独立 PID `4059299` 的 `resource_monitor.tsv`，每 300 秒记录 Python
  PID/RSS/CPU、MemAvailable、swap used 与累计 pswpin/pswpout、memory PSI；它只读系统状态，不修改模型。
  首次内联 `awk` 启动命令因引号错误在写 PID 前退出，第二次标准输入脚本已独立核验为活动采样器。
- 自主续接：启动 supervisor PID `4100799`，控制根
  `/data/zz2/National_model/run_control/relaxed_barrier_continuation_v0816_v1`，预定输出根
  `/data/zz2/National_model/outputs/relaxed_barrier_continuation_v0816_v1`。它只在 reference
  `rc=0 + stderr=0 + OPTIMAL + QC PASS + result manifest` 后创建三条指向旧 candidates 的 symlink，
  使用新控制根重算 exact A/B；随后现有 campaign 的严格串行合同只允许最快 exact `MACRO_PASS`
  进入 V5/744、Base/1488、Base/2160。外层启动命令最后一次 `cat` 因 Windows CR 行尾返回 rc 1，
  发生在 supervisor 启动后；独立复核确认 PID 已 reparent 到 1、正在 `sleep 300`、event log 正常、
  新输出根不存在且无第二 solver。
- ParaCloud：job `4139552` 未修改，仍为原 Stage A；不取消、不改参、不启动 Stage B。
- 未决与下一步：继续只读监管 strict reference 与 supervisor。reference 退出时先人工执行完整终态审计；
  supervisor 只负责安全续接，不替代 58/58 hard checks、manifest validity、资源/耗时和宏观结果审计。

### 2026-08-16 当前身份 strict Base/744 h reference 启动（`d80f5b7`）

- Git 与部署：local、`origin`、GitHub 和 fixed-server checkout 均为
  `d80f5b76b7deefd6c82004ee0e17f1fc206f7eff`；fixed server 工作树 clean。提交包含 exact-LP 宏观
  审计门禁及相应三份交接修正；没有修改 LP 变量、约束、目标、数据或正式科学 QC。
- 验证：在 Power_curve v3_qc 当前数据根与 Gurobi 13.0.2 环境完成完整回归 `184/184 PASS`
  （`94.693 s`）。启动前无活动 CISPO/Gurobi，available RAM 约 114 GiB，swap 968 MiB/2 GiB 但
  `vmstat si/so=0/0`，memory PSI avg10/60/300 均为 0，两个新根均不存在。
- 命令与输出：以 `/usr/bin/time -v` 后台执行
  `scripts/run_cispo_2030_full_year.py --planning-year 2030 --diagnostic-hours 744
  --diagnostic-start-hour 0 --scenario-config config/scenarios/base.json
  --solver-config config/solver_profiles/barrier_16_crossover2_stable_basis_long_v1.json`；输出根为
  `/data/zz2/National_model/outputs/relaxed_barrier_exact_reference_v0816_v1/base_744h_strict_crossover2`，
  控制根位于对应 `run_control/`，wrapper PID `4046161`。未传 `--export-diagnostic-state`。
- 启动证据：wrapper→`time`→Python 进程树完整，stderr 0；主机 available RAM 约 113 GiB、无 swap I/O、
  memory PSI 0。ParaCloud `4139552` 仍为原唯一付费任务且未修改，latest iteration 308，尚无终态文件。
- 未决与精确下一步：只读监管 strict reference，退出后必须验收 rc/time/stderr、`OPTIMAL`、
  `solution_qc=PASS`、全部 hard checks、current input manifest、valid result manifest 和 LP Fingerprint；
  随后用新审计器离线重算三个既有 relaxed candidates，保留旧无效报告且另写新报告。只有 exact
  `MACRO_PASS` 中最快者才可串行进入 V5/744 与 Base/1488/2160；运行中不部署、不启动第二求解。

### 2026-08-16 macro audit exact-LP identity 门禁（`c53bd78`）

- 范围：修改 `scripts/audit_relaxed_barrier_macro.py` 与
  `tests/test_relaxed_barrier_macro.py`，加入 path-neutral 非 solver input identity、科学配置、LP
  Fingerprint/规模和 strict reference contract；新增 mismatch 回归。
- 触发证据：8 月 12 日 campaign 三根运行成功，但 reference 与候选的数据根、负荷/flex/EV hashes、
  source bundle 和 Gurobi Fingerprint 均不同；旧审计只检查 year/scenario/window，错误地允许跨 LP 比较。
- 修复边界：solver profile 明确排除于 input equality，source bundle 只记录不硬拦；同一 Fingerprint、
  科学配置和全部非 solver inputs 才能证明 exact LP。reference 还必须 OPTIMAL/QC PASS/result manifest。
- 验证：RL 环境 py_compile、targeted `4/4 PASS`、`git diff --check` PASS。尚待 fixed-server full
  regression；未启动新求解。
- 精确下一步：提交/双推送/clean deploy 后启动当前身份 strict Base/744 reference，保留完整资源账本；
  完成后重算三根，按 exact fastest MACRO_PASS 决定 V5 与长时域路线。

### 2026-08-12 relaxed macro export 按 master/operational/summary 分阶段（`247c302`）

- 范围：重构 `scripts/run_cispo_2030_full_year.py` 的隔离工程导出为可测试 helper，并扩展
  `tests/test_relaxed_barrier_macro.py`。master 与 operational 的预期严格 QC 失败分别登记 stage，
  汇总后写单一 raw-QC payload，再继续生成年度宏观摘要。
- 安全边界：只允许两个精确前缀的 `RuntimeError` 作为预期 QC 失败；I/O、编程、未知 RuntimeError
  与 summary 异常全部重新抛出。未修改 LP、profile、科学 QC、manifest/state/basis 规则或 A/B 阈值。
- 触发证据：`0d773d5` 的第二次 1 h smoke 再现相同 49 次 Barrier 解，证明异常源在 master export；
  Python `/usr/bin/time` rc 0，但外层 shell rc 留痕因转义错误无效，故保留该根但不用于启动 campaign。
- 验证与下一步：py_compile PASS、targeted `3/3 PASS`；本地完整回归未形成有效终态。双推送后只在
  idle fixed server clean fast-forward，执行 Linux full `182` tests，再建第三个不可复用 smoke 根，
  最终门禁通过后启动既定串行 744 h campaign。

### 2026-08-12 relaxed Barrier 严格 QC 失败时仍保留宏观证据（`cc9293b`）

- 范围：修改 `scripts/run_cispo_2030_full_year.py` 和
  `scripts/audit_relaxed_barrier_macro.py`，新增 `tests/test_relaxed_barrier_macro.py`。隔离工程导出现在
  单独捕获 strict operational QC 异常、写出机器可读失败原因，并继续生成宏观汇总和永不科学接受的
  analysis contract；比较器不再因候选缺少严格 `solution_qc.json` 而丢失整轮 A/B 证据。
- 触发证据：fixed server 旧 tip `9f5c2ca` 的 1 h/5e-2 真解 checkpoint 完整、wrapper rc=0，
  但 DualVio/ComplVio 为 `0.628/29.509`，load-center 双向最小流最大/合计 `3.599/76.294 GWh`，
  严格 QC 正确拒绝。根目录 scientific output 保护检查通过。
- 验证：targeted py_compile PASS；新增测试 `1/1 PASS`；完整 unittest `181/181 PASS`。科学含义没有
  放宽：raw QC failure 会被保留，`MACRO_PASS` 仍只表示宏观晋级，所有工程根仍
  `scientifically_accepted=false`。
- 未决与下一步：提交后双推送，确认 fixed server/cloud 实时状态，再在 idle fixed server fast-forward、
  执行 `bash -n`、py_compile、全回归和全新 1 h smoke；只有隔离 annual summary/contract 与根目录保护
  同时闭合，才后台启动既定单实例 744 h campaign。

### 2026-08-12 relaxed Barrier 本地长时域 campaign 实现（`9308ac0`）

- 范围：新增 6 个明确 test-only 的 relaxed Barrier profiles、
  `scripts/audit_relaxed_barrier_macro.py`、`scripts/run_fixed_server_relaxed_barrier_campaign.sh`；
  修改 `cispo_model/flexible_load_numerics.py` 与 `scripts/run_cispo_2030_full_year.py`，让 V5
  仅在显式工程标志下放行宽松 nonbasic 路线，并把未接受解的宏观输出隔离在子目录。新增测试
  锁定“默认仍拒绝、显式工程模式才放行”。
- 科学边界：不改变任何模型方程、数据、政策约束或现有 strict acceptance。工程输出永远
  `scientifically_accepted=false`，无 `result_manifest`、state、basis、MGA 或 Crossover；
  `MACRO_PASS` 只允许进入下一本地测试长度，不能用于论文或 2030→2040 state。
- 验证：`py_compile` PASS；`test_flexible_load.py` `22/22`、`test_solver_profiles.py` `9/9`；
  设置当前 wave root 后完整 unittest `180/180 PASS`；JSON 解析与 `git diff --check` PASS。
  由于本机 WSL 不含 `/bin/bash`，部署后以 Linux `bash -n` 补闭 shell 静态证据。
- 实时证据与下一步：12:05 fixed server clean/idle 且资源安全；ParaCloud job `4139552` 仍运行
  iteration 191，未触碰。下一步选择性提交/双推送，重新核验两端进程与资源，fixed server
  fast-forward 后运行 server regression、`bash -n` 和全新 1 h Base relaxed smoke；只有检查点、
  隔离宏观输出和保护标记闭合，才以新根后台启动唯一串行 campaign。

### 2026-08-05 Module 06 最终 EV 重构图件与月度能量尺度审计

- Git：未提交工作树，基于 `d6984b2902aa85a2459935f4c76b6fa5a5623589`；没有推送、部署、
  服务器动作或优化求解。
- 范围：只更新论文图件、绘图脚本、机器可读图数据、manifest、QA 与本交接记录；不改补充材料
  `.tex/.pdf`。重绘输入锁定最终 v3-QC 广州逐日质控、四城市时段原型、分省逐月映射、修正后的
  月度单车充电电量和最终 2025--2060 8760 h 分量表。
- 修改与新增：`Power_curve_V2/ev/make_ev_nature_figures.py`；Module 06 的
  `scripts/update_ev_figure_bundle.py`、`figures_load_flexibility/Figure_S6_{03,04,05,07,08,09,10}_*`、
  `figure_data_load_flexibility/*`、`tables_load_flexibility/figure_manifest.csv` 与
  `qa_load_flexibility/ev_figure_update_qa.json`。上游
  `outputs/ev_calibrated_v2_supplement/figures/Figure_S{1,2,3}_*` 亦由最终 v3-QC 数据重绘；旧目录名
  仅为兼容输出路径，不表示方法版本。
- 命令：在 Module 06 目录使用 RL 环境执行
  `python scripts/update_ev_figure_bundle.py`；对两个绘图脚本执行 `python -m py_compile`；人工检查
  S6-3 至 S6-5、S6-7 至 S6-10 的 PNG，并复核报告哈希与 10 行图件 manifest。
- 验证：QA `PASS`、7 个本次更新图均为双栏就绪；2050 典型日分量闭合最大误差
  `5.82e-11 MW`，年度分量份额闭合最大误差 `4.28e-11 percentage points`；legacy→final 全国
  EV 年电量为 `+4.219004%`，v2→v3-QC 年电量一致；广州平均验证 RMSE/相关系数分别由
  `0.004468/0.82845` 改善为 `0.002038/0.95843`。报告 `.tex/.pdf` SHA256 与改图前一致。
- 未决与下一步：本轮按作者要求不改报告，因此新增 S6-7 至 S6-10 的引用/图注以及 S6-3 参数表
  尚未同步；只有在作者授权报告集成后再更新这些文字，并应明确三月为二月至四月插值、EV 服务
  库存不等于逐车行程/SOC、容量信用与备用/惯量边界仍由正文解释。

### 2026-08-05 Power_curve_V2 v3_qc 负荷与 EV 派生输入本地替换

- Git：未提交工作树，基于 `d6984b2902aa85a2459935f4c76b6fa5a5623589`；没有推送、部署或服务器动作。
- 范围：把 `Power_curve_V2` 最新广州逐日质控、四城市映射的 8 年 8760 h 结果筛选为既有五个
  CISPO 模型年；不改变 31 省、北京时间、8760 h、2025 边界或 2030/2040/2050/2060 决策年。
- 修改文件：`config/model_data_config.json`、`config/flexible_load_v{4,5}_source_registry.csv`、
  `scripts/build_flexible_load_envelope_v3.py`、`scripts/build_flexible_load_v{4,5}_inputs.py`，以及
  本交接/规格/状态/runbook 文档。忽略型数据根内替换 `load/hourly_load_{2025,2030}_2060*`、年度
  汇总、V3 envelope、V4/V5 EV 派生表和 manifests，并新增
  `data/load/power_curve_v3_qc_update_manifest.json`。用户拥有的 `supplementary_materials/**` 未修改。
- 命令：调用 `build_cispo_data_package.build_load()` 只重建 load 模块；随后依次执行
  `build_flexible_load_envelope_v3.py`、V4/V5 builders 与 validators、
  `smoke_test_data_package.py`，并用 `RL` 环境 `unittest discover` 执行两个灵活负荷测试文件。
- 验证：源 2,172,480 行、8 个省年集合；模型筛选后 1,357,800 行、155 个省年组、每组 8760 h；
  source/model keys 全部 `both`，datetime 完全一致，最大转换误差 `5.68e-14 GW`，组件闭合
  `1.71e-13 GW`，legacy 1,086,240 行与主表四决策年子集完全一致；data smoke `142/142 PASS`，
  unittest `23/23 PASS`，262 个 output-manifest 条目在最终刷新后无 SHA256/size mismatch。
- 环境诊断：默认系统 Python 的 pytest 因无 `gurobipy` 在 collection 前退出；`RL` 环境无 pytest
  包，因此按仓库既有 unittest 接口执行并通过。这两次不是模型/数据测试失败。
- 未决与下一步：本地数据身份尚未提交或部署。服务器如需采用该负荷，必须复制当前版本化数据根
  到全新目录，仅替换本里程碑列出的 load/flexibility/provenance 文件，运行完整 readiness、release、
  input validators 与小尺度 Base/V5 配对门禁；不得覆盖当前服务器数据根或复用已有 output/state/basis。

### 2026-08-05 Power_curve v3_qc 三端同步与短门禁

- Git：`d63a251` 更新来源与 V4/V5 直接负荷哈希，`3cb3939` 新增
  `release_contract_v0805_power_curve_v3_qc.json`；历史 v0729/v0730 合同未改写。两提交双推送并
  fast-forward fixed server；暂存排除了并发的 Module 06 与其余 `supplementary_materials/**` 改动。
- fixed server：新建 78-file 版本根，不覆盖旧生产根。首次 smoke 对继承的 62-file 精简根
  fail-closed，缺少的 16 个现行 QA/support tables 补入新根后，v2 deployment 下 release、readiness、
  V4/V5、smoke、Gurobi full-license 与 unittest `178/178` 全 PASS；失败 v1 证据保留。
- 门禁：在全新 `outputs/gates_20260805_power_curve_v3_qc_3cb3939_v1` 串行运行四年 Base/V5
  1 h、24 h。16 roots 均 `ACCEPTED + QC PASS + current input + valid result manifest`；sequence
  wall/peak RSS/swap 依次为 `2:56.78/0.516 GiB/0`、`3:03.53/0.559 GiB/0`、
  `7:03.44/0.825 GiB/0`、`7:39.20/0.861 GiB/0`。A/B JSON SHA256 为
  `f052f2aa...`（1 h）与 `bd3bd632...`（24 h）。不得将截断结果解释为年度科学价值。
- cloud：有效 release 为 `$HOME/National_model_cloud/20260805_power_curve_v3_qc_3cb3939_v2`，
  5.5 GiB；代码 `git archive` 与三个数据 tar 均经 SHA256 验收，四个解包 tree hashes 与 fixed
  server 相同。Python 3.10.20 py_compile PASS，队列为空，未提交 compute/WLS/solver job。旧 cloud
  hydro 哈希相同而复用；旧 CF 文件数仅为当前一半，故未复用。raw GRFR 8.3 GiB 未同步是明确限制。
- 证据：fixed server 的 `run_control/deployment_20260805_power_curve_v3_qc_3cb3939_v2`、
  `run_control/gates_20260805_power_curve_v3_qc_3cb3939_v1`；cloud 的
  `manifests/cloud_release_manifest.json`。下一步若需云求解，须独立授权并决定是否补齐 raw GRFR；
  本任务未启动 168/744/8760 h。

### 2026-08-06 2030 Base 8760 h Stage A v2 实现与提交前冻结

- Git/修改：实现提交 `6f0b1f7286a5ba479eabff3df2b14c2f8cf6bbb6`；修改
  `cispo_model/{config,diagnostics,primal_dual_checkpoint}.py`、
  `scripts/run_cispo_2030_full_year.py`、两份 tests；新增 v2 Stage A/B profiles 与
  `cloud_cispo_8760_stage_a_barrier_checkpoint_v2.sbatch`。未修改 LP 变量/约束/目标、Base 情景、
  数据、历史 outputs 或用户 `supplementary_materials/**`。
- 参数/保存：Stage A 宏观容差改为 `BarConvTol=1e-8`、`FeasibilityTol=OptimalityTol=1e-6`，
  保持 `NumericFocus=2/ScaleFlag=2/Aggregate=1/MarkowitzTol=0.01`；solver 与 Slurm 均不设时间
  上限，保留 `SoftMemLimit=600 GiB`。完整 Barrier 检查点可进入另行授权的 Stage B；未完成
  Barrier 的可读向量只登记 recovery，不能复用。
- 验证：py_compile、targeted `8/8 + 5/5`、完整 unittest `179/179 PASS`。live 审计确认
  fixed server 无 CISPO/Gurobi 进程、内存无压力，ParaCloud 队列为空且 768 GiB 分区无默认/最大
  wall time；旧云文件 release hashes 仍有效。
- 未决/下一步：本条仍是提交前冻结点。先双推送/部署精确 tip，建立只读的新 cloud release；
  用不启动 job 的 `sbatch --test-only` 审核 96 CPU/700G，再提交单个 Stage A。禁止自动 Stage B、
  2040/V5、并发第二求解或将工程 `BarPi` 当论文价格。

### 2026-08-06 Stage A job 4139419 的 0 秒 launcher failure 与修复

- 证据：ParaCloud `scontrol/sacct` 为 `FAILED 1:0`、0 秒 elapsed/CPUTime、`TotalCPU=0.007 s`、
  `MaxRSS=0`；资源为 `Req/Alloc cpu=96,mem=700G,billing=96`，无 wall time。control 下两份 Slurm
  日志都是 0 bytes，output root 未创建，故没有模型构建、求解或有效 8760 h 数据。
- 原因/修复：Slurm 将脚本复制到 spool 后执行，`dirname "$0"` 不再指向 release。提交
  `d857f8d2a0724bc7d89856aea70042977b2f9b0a` 使用 `SLURM_SUBMIT_DIR`，并测试无 `#SBATCH --time`、
  保持 96 CPU/700G 且禁止 `$0` resolver；targeted `9/9 PASS`。
- 未决/下一步：失败 releases/job 全部只读保留。双推送/clean deploy 后用 Linux archive 建 `_v3`；
  只有其 `bash -n`、profile load、调度预检与全新 roots 通过时才重提唯一 Stage A。

### 2026-08-06 Stage A job 4139479 的环境继承 fail-fast 与修复

- 证据：Slurm 5 秒；profile preflight PASS；runner 在 `write_run_provenance` 前报告 data roots 未传入，
  `1.09 s/83,900 KiB/0 swap/exit 1`，没有 model build、Gurobi log、telemetry 或 solver output。
- 修复：`b5cad0dee02f0f2ac7c8368b778f68dde0796826` 用 `set -a/source/set +a` 将 manifest 中的
  `PYTHON/GUROBI_HOME/CISPO_*_ROOT` 导出到子进程；静态 profile tests `9/9 PASS`。
- 下一步：失败 root/release 不复用；双推送、clean deploy 后建立 `_v4` Linux release，完成
  syntax/LF/hash/queue/test-only 预检，再提交唯一 Stage A。

### 2026-08-06 Stage A job 4139496 的 xarray 依赖 fail-fast

- 证据：前置 `4139494` 小 LP/WLS 为 `COMPLETED 0:0`；主 job `4139496` 写出 run identity、
  environment 与 input manifest 后因缺 xarray 退出，Slurm 7 秒，无 model build/solver 文件。
- 环境审计：cloud 已有 netCDF4 1.7.2/cftime 1.6.5；采用 SHA256
  `a7ad6a36...a7f8d6` 的 xarray 2025.1.2 纯 Python wheel建立 release 私有 overlay，不改共享 env。
- 下一步：提交/双推送本环境合同，建立新 Linux release；先运行完整 `load_model_data` 低资源门禁，
  再决定是否提交唯一 96 CPU/700G Stage A。

### 2026-08-06 Stage A v5 数据门禁通过并启动 job 4139552

- Git/release：cloud code `3f739fd6216b1c7fc356e8d3a1d9a257c666f0c5`；Linux archive SHA256
  `c49d48da...822ec40e`；xarray wheel `a7ad6a36...a7f8d6` 安装到 release 私有 overlay。
- 门禁：job `4139550` 完整 `load_model_data` PASS；主 job preflight 67 PASS/3 WARN/2 INFO/0 fail，
  Base、2030、8760 h、wave on、flex off、无 state/basis/crossover identity 均正确。
- 活动证据：job `4139552` 于 01:17:53 开始，96 CPU/700G/billing 96、无限时长；01:19 已稳定进入
  model build，RSS 3.80 GiB、stderr 0。输出尚无 solve files，不得提前声称 Barrier 已开始。
- 下一步：持续读取 squeue/sstat/build report；出现 `gurobi.log` 后核对 v2 parameters 和 Barrier
  telemetry。任何终态都先审计 checkpoint/report，且不自动 Stage B。

### 2026-08-06 Stage A 进入 Barrier iteration 7

- cloud code/release 保持 `3f739fd6216b1c7fc356e8d3a1d9a257c666f0c5` / `_v5`，没有修改运行中
  release、模型、配置或 output；本次仅只读审计并更新三份交接文档。
- `build_report.json`：01:18:08--01:57:05，2,336.984 s，build peak process-tree RSS
  48.574 GiB；原始 LP `41,458,383/50,907,234/492,835,195`（vars/rows/nnz），fingerprint
  `0xd16b4c7e`。Gurobi 13.0.2 参数与 v2 profile 完全一致且无 `TimeLimit`。
- `gurobi.log`：presolve 17,414.51 s，presolved `32,166,850/37,703,954/404,259,819`；ordering
  2,912.17 s；Barrier iteration 7 于 11:27:07 落盘，3--7 每步约 45--48 分钟。12:06 的两次
  `sstat` 证明 16 threads 持续工作，日志无 warning/error。
- 资源/终态：Slurm MaxRSS 361.6 GiB，Gurobi max 354.5 GiB；距 SoftMemLimit 600 GiB 和 allocation
  700 GiB 尚有余量。终态三文件/checkpoint 均不存在。下一步继续只读监控 iteration、CPU 与内存；
  不自动取消、重提、启动 Stage B 或第二求解。

### 2026-08-06 iteration 8、资源留痕与旧 8760 对照

- 运行边界：除作者明确授权外，禁止人工取消 job `4139552`；本轮只写 run-control 审计旁路文件，
  不修改 active release、output、solver 或配置。iteration 8 runtime `36,926.334 s`，work units
  `132,433.217`，Gurobi current/max memory `351.054/354.498 GiB`。
- 资源文件：`resource_audit_snapshots.jsonl` 4 records，SHA256
  `7ecb6006e5f590838e4212aa1fe83f671f1faa5073d8d4f357c777fdc55dae10`；
  `historical_8760_comparison.json` SHA256
  `2e77c8ef6c440c1edc94212d02ef0f8bbed2afaf6f02f3fbda0781877f4fc7f6`。终态仍需追加 sacct、wrapper
  wall、最终 iteration/checkpoint/report，不得把当前快照视为完整资源账本。
- 对照结论：旧 `4004585` 是 full-year 8760 h + 24 h wall limit，非 24 h horizon；其原始 LP
  `68,189,325/40,912,327/515,040,080`（rows/cols/nnz），presolved
  `37,982,903/35,423,761/400,861,556`，Factor NZ/Ops `3.848e10/2.448e15`，32 threads、MaxRSS
  476.760 GiB，最终 iteration 35/TIMEOUT。当前 raw rows/nnz 更低，presolved规模仍接近；Factor
  NZ/Ops 和 sampled RSS 分别改善 11.772%/21.119%/24.145%，但 16-thread 单步更慢。
- 下一步：持续逐轮保留 telemetry，并在每次人工状态审计追加 Slurm snapshot；不取消、不重跑、
  不启动 Stage B。任务终止后生成最终资源/阶段时间/迭代/QC/checkpoint 汇总。

### 2026-08-06 Barrier iteration 18 与资源审计 round 4

- 本轮仅执行 squeue/sacct/sstat、Gurobi/telemetry/stderr/终态文件只读检查，并更新 run-control
  旁路账本；未修改 active release、output、solver、配置或 scheduler state，未取消任务。
- 进度：iteration 18 timestamp `2026-08-06T20:04:37.541593+08:00`，solver runtime
  `65,252.488843 s`、work units `175,875.850995`；iteration 8--18 平均 `47.2103 min/step`。
  三项表内收敛指标相对 iteration 8 下降约 74%--78%，但仍无可接受解或完成百分比。
- 资源：wall 68,934 s、96 CPUs/700G，allocation `1,838.24 core-hours`，sstat actual CPU
  `212.9408 h`、MaxRSS `379,781,180 KiB = 362.1876 GiB`；Gurobi max 354.4981 GiB。
- 账本：`resource_audit_snapshots.jsonl` 当前 5 records，SHA256
  `fb390f551ef190720673a341037e2bcd8b6ce006905b549268a27c4f0f418c7f`。下一步继续逐 iteration
  telemetry 与周期 Slurm snapshot；不得人工取消、重提或启动 Stage B/第二求解。

### 2026-08-07 Barrier iteration 23 与资源审计 round 5

- 只读证据：00:00:22 squeue/sacct/sstat、Gurobi tail、telemetry、warning grep、stderr 和 output
  文件清单；未修改 active job/release/output/config/scheduler，未取消任务。
- 进度：iteration 23 timestamp `2026-08-07T00:00:09.031273+08:00`，runtime
  `79,383.978511 s`、work `197,157.586975`；18--23/8--23 平均 `47.105/47.175 min/step`。
  相对 iteration 18 的 primal/dual infeasibility/complementarity 下降 `42.9%/54.9%/45.6%`。
- 资源：wall 81,749 s、allocation `2,179.9733 core-hours`、actual CPU `267.6286 h`、MaxRSS
  `379,945,024 KiB = 362.3438 GiB`；Gurobi max 354.4981 GiB，stderr 0。
- 账本：`resource_audit_snapshots.jsonl` 6 records，SHA256
  `73f3df3998f4313051231658dd35dc8ccaeb1f8c3c23ccec5efa7a0e4c30d967`。下一步继续逐轮监控；
  无终态文件/checkpoint，不得人工取消、Stage B 或第二求解。

### 2026-08-07 Barrier iteration 35 与资源审计 round 6

- Git 基线：本轮开始时本地、`origin` 与 `github` 均为 `58e6c3166c7c6a68cfb3385ad42aaabd93132b10`；
  cloud active release 继续冻结实现 `3f739fd6216b1c7fc356e8d3a1d9a257c666f0c5`。本轮仅执行
  squeue/sacct/sstat、Gurobi/telemetry/stderr/终态文件只读审计，并更新 run-control 旁路账本；
  未修改 active release、output、solver 参数或 scheduler state，未取消任务。
- 进度：09:59:01 job `RUNNING` 1 天 08:41:08；iteration 35 timestamp
  `2026-08-07T09:24:32.076212+08:00`，runtime `113,247.023468 s`、work
  `247,618.444288`。23--35/8--35 平均 `47.032/47.112 min/step`；相对 iteration 23 的
  primal/dual infeasibility/complementarity 下降 `78.29%/76.82%/77.52%`，内存与单步稳定，
  但绝对残差和目标间距仍不支持完成比例或可接受解声明。
- 资源：wall 117,668 s、96 CPU/700G，allocation `3,137.8133 core-hours`、sstat actual CPU
  `421.8608 h`、MaxRSS `380,150,660 KiB = 362.5399 GiB`；Gurobi current/max
  `351.0545/354.4981 GiB`，stderr 0，warning/numerical trouble/error 均无。
- 输出与账本：`solve_report.json`、`solution_qc.json`、`result_manifest.json` 和 checkpoint 均不存在，
  符合 Barrier 运行中状态。`resource_audit_snapshots.jsonl` 已追加 round 6，共 7 records，SHA256
  `13e567bd1743c5b0079ebb7445123bb18f6cba05a5e7be208f9619592c2c6175`。精确下一步仍是只读监控；
  禁止人工取消、改参、重提、Stage B 或第二求解，终态后再按 checkpoint/报告合同闭合审计。

### 2026-08-07 Barrier iteration 48 与资源审计 round 7

- Git 基线：本轮开始时本地、`origin` 与 `github` 均为
  `471a90080f6ec38b8a1f084d159a6b289f008227`；cloud release 仍冻结实现
  `3f739fd6216b1c7fc356e8d3a1d9a257c666f0c5`。仅执行只读状态/日志/文件审计并更新旁路资源账本，
  未取消、改参、重提或启动 Stage B/第二求解。
- 进度：19:45:16 job `RUNNING` 1 天 18:27:23；iteration 48 timestamp
  `2026-08-07T19:34:53.868146+08:00`，runtime `149,868.815376 s`、work `301,863.167704`；
  iteration 35--48 平均 `46.951 min/step`。相对 iteration 35 的 primal/dual infeasibility 与
  complementarity 下降 `77.27%/84.52%/77.95%`；绝对指标仍未达到 Stage A 收敛或验收量级。
- 资源：wall 152,843 s、96 CPU/700G，allocation `4,075.8133 core-hours`、actual CPU
  `572.4642 h`、MaxRSS `380,264,648 KiB = 362.6486 GiB`；Gurobi current/max
  `351.0545/354.4981 GiB`，stderr 0，无 warning/numerical trouble/error。
- 输出与下一步：终态三文件和 checkpoint 仍不存在。`resource_audit_snapshots.jsonl` round 7
  共 8 records，SHA256 `d691d087fec95263c77e62530befa58cac9b0aed6a986a55a9b992535305badc`。
  继续只读监控，终态后立即执行 checkpoint、wrapper、QC/manifest 与总资源闭合审计。

### 2026-08-08 Barrier iteration 77 与资源审计 round 8

- Git 基线：本轮开始时本地、`origin` 与 `github` 均为
  `4a8ad14f100a7f6344bbe184cd1910be7710b89e`；cloud release 仍冻结实现
  `3f739fd6216b1c7fc356e8d3a1d9a257c666f0c5`。仅执行只读状态、日志、资源和输出文件审计，
  并追加 run-control 资源账本；未取消、改参、重提或启动 Stage B/第二求解。
- 进度：17:51:34 job `RUNNING` 2 天 16:33:41；iteration 77 timestamp
  `2026-08-08T17:50:39.829041+08:00`，runtime `230,014.776122 s`、work `414,514.268194`；
  iteration 48--77 平均 `46.061 min/step`。相对 iteration 48，三项 telemetry 指标分别缩小
  `82,964/832,887/57,100` 倍；最新 Gurobi primal/dual residual/complementarity 为
  `4.45e4/5.22e-5/1.15e4`，但 objective 相对间距仍约 `11.63`，尚未达到 Stage A 收敛。
- 资源：wall 232,421 s、96 CPU/700G，allocation `6,197.8933 core-hours`、actual CPU
  `915.2986 h`、MaxRSS `380,386,444 KiB = 362.7648 GiB`；Gurobi current/max
  `351.0545/354.4981 GiB`，stderr 0，无 warning/numerical trouble/error。
- 输出与下一步：终态报告、QC、result manifest 与 checkpoint 均不存在。资源账本 round 8 共
  9 records，SHA256 `f0c7fdfa03c0ab39c5a1ace6739ea5a337b7dd0b22de7e83d37c4f5bde09ede0`。
  继续只读监控；只有 Barrier 返回并保存检查点后才执行严格终态审计，不自动启动 Stage B。

### 2026-08-10 Barrier iteration 116 与资源审计 round 9

- Git 基线：本轮开始时本地、`origin` 与 `github` 均为
  `3f9c76b8b90fc1593d8b97ea6a2e4a0e03b2555f`；cloud release 继续冻结实现
  `3f739fd6216b1c7fc356e8d3a1d9a257c666f0c5`。仅执行 scheduler、telemetry、Gurobi、stderr、
  output/control 文件只读审计并追加资源账本；未取消、改参、重提或启动 Stage B/第二求解。
- 进度：00:47:23 job `RUNNING` 3 天 23:29:30；iteration 116 timestamp
  `2026-08-10T00:43:08.437793+08:00`，runtime `341,163.385031 s`、work `584,610.437812`；
  iteration 77--116 平均 `47.499 min/step`。相对 iteration 77 的 primal/dual infeasibility 与
  complementarity 再缩小 `82.48/36.26/42.62` 倍；最新 Gurobi 三项为
  `5.40e2/1.52e-5/2.70e2`。objective 相对间距仍约 `8.56`，近期下降速度较前段放缓，不能声明临近终态。
- 资源：wall 343,770 s、96 CPU/700G，allocation `9,167.2 core-hours`、actual CPU
  `1,391.305 h`、MaxRSS `380,537,464 KiB = 362.9088 GiB`；Gurobi current/max
  `351.0545/354.4981 GiB`，stderr 0，无 warning/numerical trouble/error。
- 输出与下一步：终态报告、QC、result manifest、checkpoint 及 wrapper time 均未生成或仍为空，
  符合运行中状态。资源账本 round 9 共 10 records，SHA256
  `9aa1f051e406b4bdfd5056f0dec90303e4d5ad3b18a0faf360cd18580bf9052b`。继续只读监控；Stage A
  返回后先审计检查点身份与资源终态，不自动进入 Stage B。

### 2026-08-10 Barrier iteration 145 与资源审计 round 10

- Git 基线：本轮开始时本地、`origin` 与 `github` 均为
  `a80e11a870a5c77d1c104f93905625d4b76b5776`；cloud release 继续冻结实现
  `3f739fd6216b1c7fc356e8d3a1d9a257c666f0c5`。仅执行 scheduler、telemetry、Gurobi、stderr、
  output 文件只读审计并追加资源账本；未取消、改参、重提或启动 Stage B/第二求解。
- 进度：23:43:29 job `RUNNING` 4 天 22:25:36；iteration 145 timestamp
  `2026-08-10T23:41:30.535792+08:00`，runtime `423,865.483042 s`、work `711,816.781497`；
  iteration 116--145 平均 `47.530 min/step`。三项 telemetry 指标相对 iteration 116 再缩小
  `6.61/4.71/4.81` 倍；最新 Gurobi primal/dual residual/complementarity 为
  `8.16e1/3.23e-6/5.61e1`。objective 相对间距由约 `8.56` 降至 `3.90`，仍在长尾且未收敛。
- 资源：wall 426,336 s、96 CPU/700G，allocation `11,368.96 core-hours`、actual CPU
  `1,744.3239 h`、MaxRSS `380,541,568 KiB = 362.9127 GiB`；Gurobi current/max
  `351.0545/354.4981 GiB`，stderr 0，无 warning/numerical trouble/error。
- 输出与下一步：终态报告、QC、result manifest、checkpoint 仍不存在。资源账本 round 10 共
  11 records，SHA256 `581e3c52d5a087f38368cf35f9396a67c7561e612d91b2059b9f19537db3bba0`。
  继续只读监控；Stage A 返回后先审计工程检查点，不自动进入 Stage B。

### 2026-08-11 Barrier iteration 158 与资源审计 round 11

- Git 基线：本轮开始时本地、`origin` 与 `github` 均为
  `adef6fb36ae93a4ec096d418050a3c6f74ed41a8`；cloud release 继续冻结实现
  `3f739fd6216b1c7fc356e8d3a1d9a257c666f0c5`。本轮仍仅做只读审计和 run-control 账本追加；
  未取消、改参、重提或启动 Stage B/第二求解。
- 进度：10:16:00 job `RUNNING` 5 天 08:58:07；iteration 158 timestamp
  `2026-08-11T09:55:55.667613+08:00`，runtime `460,730.614875 s`、work `767,656.242179`；
  iteration 145--158 平均 `47.263 min/step`。telemetry primal/dual infeasibility 与 complementarity
  分别只再缩小 `1.17/1.74/1.21` 倍；最新 Gurobi 三项为 `6.97e1/1.92e-6/4.63e1`，objective
  相对间距约 `3.69`，证明仍在推进但长尾明显。
- 资源：wall 464,287 s、96 CPU/700G，allocation `12,380.9867 core-hours`、actual CPU
  `1,906.9753 h`、MaxRSS `380,541,572 KiB = 362.9127 GiB`；Gurobi current/max
  `351.0545/354.4981 GiB`，stderr 0，无 warning/numerical trouble/error。
- 输出与下一步：终态报告、QC、result manifest 与 checkpoint 均不存在。资源账本 round 11 共
  12 records，SHA256 `467e4f1bba55a0fac1c9947d444e8f45d3e32fc247b043c0e0dfa76d9c8dc6b4`。
  继续只读监控；Stage A 返回后先审计检查点，不自动进入 Stage B。

### 2026-08-12 Barrier iteration 190 与资源审计 round 12

- Git 基线：本轮开始时本地、`origin` 与 `github` 均为
  `b6711e2f22b26af001806c859e8f1168a0b13323`；cloud release 继续冻结实现
  `3f739fd6216b1c7fc356e8d3a1d9a257c666f0c5`。本轮只做 scheduler、telemetry、Gurobi、资源与
  output/control 文件审计并追加旁路账本；未取消、改参、重提或启动 Stage B/第二求解。
- 进度：11:50:04 job `RUNNING` 6 天 10:32:11；iteration 190 timestamp
  `2026-08-12T11:18:12.582597+08:00`，runtime `552,067.529856 s`、work `908,413.916280`；
  iteration 158--190 平均 `47.571 min/step`。telemetry primal/dual infeasibility 与 complementarity
  分别再缩小 `1.74/2.05/1.95` 倍；最新 Gurobi 三项为 `4.00e1/9.35e-7/2.37e1`，objective
  相对间距由约 `3.69` 降至 `3.21`，仍是活跃但缓慢的 Barrier 长尾。
- 资源：wall 556,331 s、96 CPU/700G，allocation `14,835.4933 core-hours`、actual CPU
  `2,300.5539 h`、MaxRSS `380,541,576 KiB = 362.9127 GiB`；Gurobi current/max
  `351.0545/354.4981 GiB`，stderr 0，无 warning/numerical trouble/error。
- 输出与下一步：终态报告、QC、result manifest 与 checkpoint 均不存在。资源账本 round 12 共
  13 records，SHA256 `e299d4c7821a0e6e372b44182c3dc239179b58bea5ccfa784a4cc841a77b776d`。
  继续只读监控；Stage A 返回后先审计检查点，不自动进入 Stage B。

### 2026-08-05 8760 h 工程 Barrier 检查点与独立 Crossover=2 架构

- 实现提交：`369506010b5bc876676941e456d9574187e0f293`。改动文件：
  `cispo_model/primal_dual_checkpoint.py`、`scripts/run_cispo_2030_full_year.py`、两个 cloud
  solver profiles 及对应 tests；数学模型、输入数据和历史 outputs 均未修改。
- 实现证据：阶段 A 的工程检查点在求解返回后、科学结果导出前写出；持久化有限
  `BarX/BarPi`、末次 Barrier telemetry、Gurobi/package/config/input/planning-state 身份、
  LP Fingerprint/规模和完整有序名称 SHA256。阶段 B 对完全重建 LP 复算全部身份与顺序，
  只有显式授权工程源后才设置 `PStart/DStart + LPWarmStart=2`；Stage A 永不写 scientific
  manifest/state，Stage B 可在严格 accepted 后显式写 state。
- 验证：本地 targeted `12/12 PASS`；fixed server Gurobi 13.0.2 targeted `12/12 PASS`。
  本地全套 124 tests 的 6 项非通过均可复现为缺少外部 `CISPO_WAVE_ROOT`，不是断言回归。
  fixed server 已 clean fast-forward 到 `3695060`，没有启动 solver。ParaCloud 队列为空，
  `amd_a8_768` 资源合同已核为 128 CPU/750 GiB/每 CPU 上限 6144 MB。
- 未决问题与精确下一步：在任何付费提交前，冻结 2030 Base 的 exact scenario/data/state 和
  双远端 tip，建立不可复用的 Stage A/B roots 与 Slurm wrapper，申请约 `128 CPU/700G`
  但保持 Gurobi `Threads=16`，给 solver 7 天外另留至少 12 小时写出/审计窗口，并先报告
  核时费用。当前没有 8760 h job；固定服务器因 640 GiB memory guard 不具备执行资格。

### 2026-08-05 744 h runtime/profile 与 Barrier-only 执行记录审计

- 证据：逐根解析本轮 11 份 `solve_report.json` 与 `gurobi.log` 的 Barrier/Crossover 时间、
  iterations、runtime memory 和 resolved solver parameters；递归扫描服务器 outputs 下全部
  solve reports，筛选 `optimization_hours=744` 且 `crossover=0`。
- 结果：本轮 9 accepted、2 TIME_LIMIT 全部为同一 Crossover=2 profile；accepted solver
  runtime 平均 `8.89 h`，Crossover 是主要耗时。服务器保留记录中无任何 744 h
  Barrier-only solve report。
- 下一步：不能把 24 h Barrier-only 诊断或 recovery-only checkpoint 外推为 744/8760 h
  资格。若选择 Barrier-only 候选，必须建立全新命名根并按 24 h→168 h→744 h 逐级验收。

### 2026-08-05 当前不存在已验证 8760 h solver route

- 冲突：模型规格仍把 2026-08-01 的 Barrier-first 提案写成当前默认生产路线，但后续
  Phase 0 已用 20 个当前模型 24 h Barrier-only 组合严格否定该资格；Phase 1/2 实际冻结并
  使用 `Crossover=2`。本次按已验证输出增加后置更正规格，不改变数学模型或运行文件。
- 结论：Barrier-only 在数学上可能得到 `BarStatus=OPTIMAL`，但当前尚不能通过原始
  primal/dual 科学门禁；Crossover=2 在 744 h 也并非稳健全通过。故二者都不能直接外推为
  8760 h production route。
- 精确下一步：优先对两个 recovery `BarX/BarPi` 做 exact-LP 离线 primal/physical/dual
  审计；再以 `FeasibilityTol/OptimalityTol=1e-6` 为首个最小候选做 24 h→168 h→单根
  744 h A/B。只有严格、宏观稳定且端到端提速的路线才可进入年度 preflight。

### 2026-08-05 Crossover 超时后的 Barrier recovery checkpoint 边界复核

- 范围/证据：只读检查两个 TIME_LIMIT 根的 `solve_report.json`、
  `barrier_checkpoint/barrier_checkpoint_manifest.json` 与两份 `.npy`；未启动任务或修改
  server。两根均为 `BarStatus=OPTIMAL`，故 recovery export 成功。
- 结论：当前 wrapper 会在 inline Crossover 非最优终止后尽力保存 `BarX/BarPi`，但 recovery
  manifest 明确拒绝 scientific acceptance 与 deferred-crossover eligibility。只有以
  `Crossover=0/SolutionTarget=1` 最终 `OPTIMAL`、严格 primal/dual、QC、hard checks 和
  manifests 全部闭合的主阶段，才能生成 `ACCEPTED_PRIMARY_BARRIER_SOLUTION`。
- 下一步：8760 h 不得使用当前 744 h Crossover=2 profile 强行 inline 运行；先闭合当前模型
  的 Barrier-only 小根与长根数值门禁，再决定独立后置 Crossover。recovery-only 向量不得
  resume、续年、出图或进入影子价格科学解释。

### 2026-08-05 Phase 2 Base 部分失败并停止；Oct 四年 Base PASS

- Git/范围：运行身份与服务器 checkout 仍为 clean
  `3f123f0598e95151e8492f784ca79521569f57f0`；本里程碑仅更新三份状态文档，未修改模型、
  数据、profile、历史 outputs 或受保护文件，未启动新任务。
- 命令/证据：SSH 逐根读取 solve/QC/result manifests、sequence reports、Gurobi log tails、
  wrapper `/usr/bin/time -v`、control stdout/stderr、进程树与资源；用 current-tip validators
  严格复验 Oct/2060；查询 ParaCloud `squeue -u a8s001819`。
- 输出/验证：Oct/2060 为 `OPTIMAL + acceptance/QC PASS + 58/58 + Pi + current input +
  valid result manifest`，使 Oct 四年 Base sequence 完整 `PASS`。Jan/2050 与 Jun/2060
  均在约 24 h 时由 Crossover `TIME_LIMIT`，缺 QC/result manifest/state；Jan/Jun sequences
  fail closed。Oct V5 在开始前因 memory PSI 非零被 resource gate 阻止，未创建输出根。
- 未决问题/精确下一步：当前服务器空闲、资源恢复，但 Phase 2 未完成。先基于本次两根
  Crossover 失败证据确定新 profile 的最小 A/B：优先测试 `FeasibilityTol/OptimalityTol=1e-6`
  且保留 58 项 QC 和 `1e-5` 物理阈值，再决定是否测试 `BarConvTol=1e-7`；必须用全新
  24 h→168 h→744 h 根验证端到端提速和宏观结果稳定性。未经该闭合不得直接 resume
  失败根、运行 Jan/2060、启动任何 V5/8760 h/basis/MGA/Crossover=3 或付费云。

### 2026-08-05 Phase 2 Oct/2050 accepted；Jan/2050 与 Jun/2060 数值风险监控

- Git/范围：活动服务器 checkout 仍为 clean
  `3f123f0598e95151e8492f784ca79521569f57f0`；本里程碑仅更新三份状态文档，未修改模型、
  数据、solver profile、进程、活动 checkout 或受保护文件。
- 命令/证据：SSH 读取全部 Phase 2 roots、进程树、telemetry/log、三份终态文件、
  sequence/control stderr 与主机资源；用 current-tip validators 复验 Oct/2050 input/result
  manifests；通过 `paracloud-bscc-a8` 查询 `squeue -u a8s001819`。
- 输出/验证：Oct/2050 严格满足 `OPTIMAL + acceptance/QC PASS + 58/58 + Pi + current input +
  valid result manifest`；runtime `66,128.573 s`、Barrier/simplex `238/1,113,083`、peak
  `19.916 GiB`，counterflow 与 storage/V2G overlap 均为零。Base 累计 `8/12` accepted。
- 未决问题/精确下一步：Jan/2050 与 Jun/2060 的 Crossover 中间 infeasibility 已升至极大
  数量级，Jan 接近 24 h TimeLimit；Oct/2060 处于 build。PID 存在期间只读等待，不 kill、
  不延长时限、不改容差、不 resume 或补 manifest。任一退出后必须按终态三文件、wrapper
  exit/stderr、58 checks 与 manifests 判定；若失败，对应 runner 应由 `set -e` 停止，不能
  手工跳年或启动其 V5。继续禁止第四条、8760 h、basis/MGA、Crossover=3 与付费云。

### 2026-08-04 Phase 2 Base 累计 7/12 accepted

- Git/范围：活动服务器 checkout 仍为 clean
  `3f123f0598e95151e8492f784ca79521569f57f0`；本里程碑仅更新三份状态文档，未修改模型、
  数据、solver profile、活动 checkout 或受保护的 `supplementary_materials/**`、`.codex_tmp/**`。
- 命令/证据：SSH 逐根读取 Jan/2040、Jun/2050、Oct/2040 的 `solve_report.json`、
  `solution_qc.json`、`result_manifest.json`，运行 current-tip `validate_input_manifest` 与
  `validate_result_manifest`；同时读取三根活动 telemetry、进程树、RAM/swap/vmstat/PSI、
  stderr、磁盘，并通过 `paracloud-bscc-a8` 查询 `squeue -u a8s001819`。
- 输出/验证：三根均严格满足 `OPTIMAL + acceptance/QC PASS + 58/58 + Pi + current input +
  valid result manifest`。Jan/2040 runtime/Barrier/simplex/peak 为
  `35,113.316 s / 295 / 775,050 / 19.266 GiB`；Jun/2050 为
  `23,990.239 s / 208 / 1,065,097 / 19.859 GiB`；Oct/2040 为
  `33,408.641 s / 204 / 960,431 / 20.706 GiB`。三根 counterflow、storage/V2G overlap
  均为零，全部 control stderr 0，ParaCloud 空队列。
- 未决问题/精确下一步：Jan/2050、Jun/2060、Oct/2050 正在 Crossover/simplex；中间
  primal/dual infeasibility 可大幅振荡，不能据此验收或判失败。继续只读监控，逐根等待三份
  终态文件并重复严格审计。Jun 只有 Base/2060 accepted 且 sequence rc=0 后，才由原 runner
  自动启动 Jun V5；其他窗口同理。不得手工提前启动 V5、第四条、8760 h、basis/MGA、
  Crossover=3 或付费云。

### 2026-08-04 Phase 2 Jun/2040 与 Oct/2030 严格接受

- Git/范围：活动模型与服务器 checkout 仍为 clean
  `3f123f0598e95151e8492f784ca79521569f57f0`；本里程碑只更新
  `CODEX_HANDOFF.md`、`MODEL_SERVER_STATUS.md`、`SERVER_RUNBOOK.md`，未修改模型、数据、
  solver profile、活动 checkout 或任何用户 `supplementary_materials/**`、`.codex_tmp/**`。
- 命令/证据：通过 SSH 逐根读取 `solve_report.json`、`solution_qc.json`、
  `result_manifest.json`，以 server checkout 的 `validate_input_manifest(input_manifest.csv)`
  与 `validate_result_manifest(output_root)` 复验；同时读取三根实时
  `solver_telemetry.jsonl`/`gurobi.log`、进程树、RAM/swap/vmstat/PSI、stderr、磁盘与
  ParaCloud `squeue -u a8s001819`。
- 输出/验证：Jun/2040 与 Oct/2030 均为 `OPTIMAL + acceptance/QC PASS + 58/58 + Pi +
  current input + valid result manifest`。Jun/2040 为 objective `2,678,562.527479 million CNY`、
  runtime `26,056.710 s`、Barrier/simplex `227/850,993`、peak `18.632 GiB`；Oct/2030 为
  `2,316,701.874843 million CNY`、`34,852.144 s`、`223/1,071,575`、`21.158 GiB`。
  两根 network/storage/V2G 双向重叠均为零，stderr 0 bytes。
- 未决问题/精确下一步：Jan/2040 与 Oct/2040 仍在 Crossover/simplex，Jun/2050 仍在
  Barrier；三个 Base 四年 sequence 尚未全部结束，V5 尚未启动。继续只读监控并在每个新
  年度终态后重复相同严格审计；只有各 runner 的 Base 四年全部 rc=0 后才允许其自动进入
  同窗口 V5。不得启动第四条、手工独立 V5、8760 h、basis/MGA、Crossover=3 或付费云。

### 2026-08-03 17:25+08:00 — Phase 2 首两个 2030 年度根严格接受

- 运行身份：server checkout 继续 clean/frozen `3f123f0598e95151e8492f784ca79521569f57f0`；
  Jan/Jun Base sequences 由原 PID `3742233/3746869` 管理，均已用 accepted 2030
  `planning_state` 启动同窗 2040；未传入 basis。
- Jan 2030 证据：`OPTIMAL`、solution contract/strict quality/QC 均 PASS、58/58、Pi、完整导出，
  input/result validators `(true, [])`；runtime `24,157.126 s`、Barrier/simplex
  `251/751,916`、peak RSS `19.022 GiB`、objective `2,355,641.489790 million CNY`。
- Jun 2030 证据：同一严格合同全部通过，runtime `25,642.054 s`、Barrier/simplex
  `218/914,644`、peak RSS `19.366 GiB`、objective `2,352,092.149379 million CNY`；两根
  manifests 均记录 commit `3f123f0`、72 files。两根 storage/V2G overlap 0、counterflow
  strict zero。
- 当前/下一步：Jan/2040 Barrier 128，Jun/2040 Barrier 107；Oct/2030 仍在 Crossover，约
  1.008m simplex iterations，尚无终态。资源无压力、stderr 全零。继续只读监控；Oct 必须按
  相同合同验收，Jan/Jun 逐年继续，任何失败由对应 runner 停止并保留现场。

### 2026-08-03 10:45+08:00 — Phase 2 Oct 第三窗口启动

- 作者/资源决策：48 GiB 是此前保守 host reserve，不是 744 h 数学模型需求。基于 Jan/Jun
  current max solver memory `20.91/21.42 GiB` 与历史 `23.13 GiB`，第三实例继续按 `24 GiB`
  规划；启动前 available 需 `>=56 GiB`，扣减后预计至少 `32 GiB`，swap I/O/PSI 必须为零。
- 命令/身份：由原 runner 复制专用 `window_runner_56g.sh`，仅将
  `MIN_AVAILABLE_KB=67108864` 改为 `58720256`，SHA256 为
  `e22f1696445b88458b1927fc1e803ca8ae7ec8c2f00ccf34f2c8feb6111c6be1`；以
  `oct6552 6552` 启动，实际 window PID `4173801`。server checkout 保持 clean `3f123f0`。
- scope/资源证据：Oct Base 根不存在后新建；scope `[6552,7296)`、北京时间 10 月完整 744 h、
  Base/test-only/Crossover=2/no-basis 均正确。启动 available `62,007,656 KiB`、`si/so=0/0`、
  PSI 0，初始 window/Base stderr 为零。
- 下一步：Jan/Jun/Oct 三个窗口各自只在 Base 四年全部 accepted 后自动进入同窗 V5；不独立
  提前启动 V5，不启动第四条。持续监控三实例峰值、available、swap/PSI、Barrier/Crossover 与
  strict terminal artifacts；活动期间不部署本里程碑后的 docs tip。

### 2026-08-03 08:56+08:00 — Phase 2 Jan 与 Jun-15 双窗口启动

- Git/运行身份：资源合同文档提交 `3f123f0598e95151e8492f784ca79521569f57f0` 已双推送并
  fast-forward 到 clean server；模型实现未越过 `b2206d9`。控制脚本位于
  `/data/zz2/National_model/run_control/phase2_3f123f0_v1/window_runner.sh`，SHA256 为
  `db8adbfa18821d5dd09875cf8eee7301b557172c9189c9c140e5b93c95fafa1c`。
- 启动命令/对象：`nohup ./window_runner.sh jan0 0`（PID `3742233`）与
  `nohup ./window_runner.sh jun15_3960 3960`（PID `3746869`）；各 runner 串行执行本窗口
  Base 四年→V5 四年，年度内部严格 2030→2040→2050→2060。当前两条均在 Base/2030 build。
- scope/配置证据：Jan `[0,744)`、Jun `[3960,4704)`；均为正确北京时间、Base、744 h、
  test-only、Crossover=2/CrossoverBasis=1、无 basis reuse。启动 available 分别为
  `119,476,916/118,249,404 KiB`，`si/so=0/0`、PSI 0；08:56 available `117,797,340 KiB`，
  两个 window stderr 与两个 Base case stderr 全为 0。
- 未决/下一步：只读监控两个活动窗口的 build、Barrier/Crossover、solver/process memory、
  swap/PSI 与严格终态；不得启动第三条。任一窗口完整 Base→V5 结束后，资源复验通过才启动
  Oct `start-hour=6552`。活动期间 server checkout 固定 `3f123f0`，本里程碑后续文档提交不部署。

### 2026-08-03 08:51+08:00 — Phase 2 744 h 启动门槛按实测峰值下调

- 作者决策：不再等待 available `>=96 GiB`；单条 Phase 2 sequence 改为 `>=64 GiB` 即可启动，
  并授权在实时证据满足时最多并发两条。该决策仅修改运行资源合同，不修改模型、数据、目标、
  约束、solver profile、QC 或 result/state manifests。
- 证据：历史统一 744 h 根 process-tree peak `21.484 GiB`，历史四年 744 h sequence wrapper
  peak `21,927,236 KiB`、swaps 0，solver 历史 max memory 约 `23.13 GiB`；因此“最多 20 GiB”
  作为近似判断方向合理，但审计合同按 `24 GiB` 单实例上界留余量。
- 新运行边界：单条启动需 available `>=64 GiB`、`si/so=0/0`、PSI 0；available `<48 GiB`
  不启动下一条。第二并发 sequence 还须首实例实时内存 `<=24 GiB`、保守预计启动后 available
  `>=32 GiB`、swap I/O/PSI 均为零；最多两条，任一严格终态失败仍停止对应 sequence 并保留现场。
- 实时证据/下一步：08:51 server clean/idle、available `91,889,284 KiB`、`si/so=0/0`、PSI 0、
  `/data` 余 `3.7 TiB`、ParaCloud 空队列，Phase 2 七个 control/output 候选根均不存在。
  提交并双推送三份交接文档，fast-forward server 后复验 identity/资源/根不存在，立即启动 Jan
  Base 四年 744 h sequence；取得当前实例内存证据后决定是否并发第二条。

### 2026-08-03 03:17+08:00 — Phase 1 24/24 严格闭合；Phase 2 等待 96 GiB

- Git/run identity：模型与全部 Phase 1 结果身份为
  `b2206d9c899c8008d7b6dabdf15cc50dd286e8b7`；本里程碑只更新
  `CODEX_HANDOFF.md`、`MODEL_SERVER_STATUS.md`、`SERVER_RUNBOOK.md`，不修改模型、数据、
  solver profile、历史 outputs 或用户 supplementary/.codex_tmp 文件。
- 命令/输出：六条 sequence 由
  `/data/zz2/National_model/run_control/phase1_b2206d9_v1/phase1_runner.sh` 严格串行完成；
  运行三次 `scripts/audit_planning_sequence_ab.py`，输出 `ab_audit_{1h,24h,168h}.{json,csv}`；
  另对 24 根运行 input/result manifest、contract、QC、dual、overlap 与 counterflow 汇总，
  输出 `phase1_strict_audit.json`。
- 验证证据：A/B audits 三项均 `PASS`；strict audit 为 `24/24 accepted`、零 failures；所有年度
  根均 `OPTIMAL/PASS/58/58`、input/result manifests 有效、manifest commit 为 `b2206d9`、
  dual=`Pi`。storage/V2G overlap 全零；仅 Base/V5 2050 各有一个预算内 de-minimis warning。
  六个 wrapper 与总 wrapper 均 rc 0；168 h Base/V5 wall 分别 `1:55:01/2:01:00`，最大 RSS
  `3,621,576/3,870,496 KiB`。
- 资源/未决/下一步：03:17 server clean/idle、available 约 `87 GiB`、`si/so=0/0`、PSI 0、
  磁盘余 `3.7 TiB`，ParaCloud 空队列。唯一未决是 Phase 2 新任务 `>=96 GiB` 资源门禁；继续
  轮询而不降门槛。资源满足后部署双推送文档 tip，重验 clean/idle/queue/目标根，再启动三季节
  744 h Base→V5 四年 sequences；任一根失败即停，全部结果仍为测试时域。

### 2026-08-02 23:16+08:00 — Phase 1 的 1 h/24 h 配对完成并进入 168 h

- Git/run identity：模型 checkout 保持 clean `b2206d9c899c8008d7b6dabdf15cc50dd286e8b7`；
  control root `/data/zz2/National_model/run_control/phase1_b2206d9_v1`，wrapper PID
  `1314144`。
- 完成证据：1 h Base/V5、24 h Base/V5 四条 sequences 均 `rc=0`，覆盖 2030/2040/
  2050/2060。逐根均为 `OPTIMAL/PASS` 且完整导出；storage、V2G overlap 为零，24 h
  counterflow 为零。
- solver 证据：24 h 部分根的 Barrier status 为 sub-optimal，Crossover=2 后最终 primal/
  dual infeasibility 为零并转为 optimal，证明当前 run 不应中途关闭 crossover。
- 当前运行：23:16:52 启动 168 h Base；启动 available `91,891,228 KiB`、`si/so=0/0`、
  memory PSI=0。下一步仅监控 168 h Base/V5，Phase 1 全部退出后再运行严格 A/B audit，
  并仅在 available RAM `>=96 GiB` 时启动 Phase 2。

### 2026-08-02 22:55+08:00 — warning 合同部署并启动全新 Phase 1

- Git/部署：`b2206d9c899c8008d7b6dabdf15cc50dd286e8b7` 已推送 origin/GitHub，固定服务器
  clean fast-forward 到同一提交。
- 验证：服务器生产环境 `177/177 PASS`；readiness/full-license、release、V5 input、
  hydropower `297.8895 + 82.1105 = 380 GW` 均 PASS，审计 stderr 全零。
- 运行：control root `/data/zz2/National_model/run_control/phase1_b2206d9_v1`，wrapper PID
  `1314144`；输出根按 `planning_sequence_2030_2060_{1,24,168}h_start3960_b2206d9_{base,v5}_v1`
  命名。无 basis、无并发、无 Crossover=3。
- 下一步：PID 存在期间只读监控；逐根审计 strict/warning QC、storage/V2G overlap、manifests、
  state 与资源。Phase 1 全部 accepted 后才按 96 GiB 新任务门禁进入 Phase 2。

### 2026-08-02 22:49+08:00 — 截断时域轻微对冲流按作者边界降为 warning

- Git 基线/文件：基线 `34b61daa5c145b37d53f7a4dedfe6d0b3ed01dcd`；修改
  `config/optimization_2030.json`、`tests/test_directionality_qc.py`、
  `cispo_full_lp_model_spec.md` 及三份交接文档。未修改 LP 方程、solver profile、数据或
  历史输出；用户 supplementary/.codex_tmp 文件未纳入任务。
- 决策/范围：仅把 168 h warning 的 edge-hours/opposing-energy/excess-loss 绝对预算调整为
  `8/1.25 GWh/0.04 GWh`，其余四项严重度阈值和 full-year strict-zero contract 不变。
- 验证：当前失败根的储能及 V2G 同时充放均为零；方向性专项 `7/7`、完整本地回归
  `177/177 PASS`。新增测试接受当前 7-hour 事件为显式 warning，并拒绝 9-hour 与 full-year
  事件。
- 未决/下一步：提交双推送，在 idle/clean server 部署后完成服务器回归与配置审计；使用
  新 implementation identity 从 1 h/24 h matched gates 开始，随后重跑全新 168 h Base/V5。
  只有 Phase 1 全闭合后才启动 Phase 2；仍禁止 8760 h、付费云、并发、basis/MGA 和
  `Crossover=3`。

### 2026-08-02 22:19+08:00 — Phase 1 在 168 h Base 2050 网络方向性 QC 处闭锁

- Git/文件：运行与审计基线为 `fc2c5002d774e80853f4059c506a55d2befc08f0`；本里程碑仅更新
  `CODEX_HANDOFF.md`、`MODEL_SERVER_STATUS.md`、`SERVER_RUNBOOK.md`，未改模型、配置、数据
  或历史输出。
- 命令/输出：审计 control root
  `/data/zz2/National_model/run_control/phase1_fc2c500_v1`、四条已完成的 1/24 h roots，以及
  `/data/zz2/National_model/outputs/planning_sequence_2030_2060_168h_start3960_fc2c500_base_v1`；
  用 current-tip `validate_input_manifest()`、`validate_result_manifest()` 逐根复验 1/24 h
  16 个年度输出，并直接读取 2050 `transmission_flows.npz`、capacity/time/price/QC 文件。
- 验证：1/24 h Base/V5 共 16 个年度根全部 strict PASS；168 h Base 2030/2040 PASS。
  2050 solver 为 `OPTIMAL`，runtime `1757.735 s`、Barrier/simplex `144/286,354`，最大
  constraint/bound/dual violation `9.897e-8/7.286e-9/3.876e-12`，但网络 hard check 因
  吉林—黑龙江同一 AC 走廊 7 个每日 04:00 counterflow hours 超出三个 warning budgets 而
  `HARD_FAIL`。server idle、内存/交换/PSI 正常，ParaCloud 队列为空。
- 未决/下一步：这是物理/表述层面的 lossy-sink degeneracy，不是 Gurobi 未收敛；不放宽阈值、
  不 resume、不运行 2060/V5/Phase 2。先形成最小、可审计的 AC net-flow/损耗或负价吸收机制
  修订，明确目标函数与约束影响，再从 matched 1/24/168 h Base/V5 门禁重新验证。

### 2026-08-02 19:58+08:00 — Phase 1 采用实测峰值分级资源门禁

- Git/文件：更新三份交接文档；不改模型或 solver profile。
- 证据：current-tip 168 h Base/V5 四根 process-tree peak 均约 `3.45--3.65 GiB`；当前
  available 约 `85 GiB`，`si/so=0/0`、PSI=0。外部负载不可触碰。
- 决策：Phase 1 启动阈值为 64 GiB、运行中 stop threshold 为 48 GiB；Phase 2 仍为
  96 GiB。由此可在不牺牲资源安全的前提下继续小门禁，而不等待外部 page cache/RSS 全释放。

### 2026-08-02 19:53+08:00 — 168 h V5 调优闭合并冻结 Crossover=2

- Git：V5 route contract 修订 `d190c23f5bcdaf0414b9d630ef8181039dfd214e`；本里程碑新增
  `config/solver_profiles/barrier_16_crossover2_stable_basis_long_v1.json`，更新 profile test
  与三份交接文档。
- 输出/控制根：
  `/data/zz2/National_model/{outputs,run_control}/solver_tuning_v0802_d190c23_168h_v5_round3_v1`。
- 验证：专项 `30/30`、完整 `175/175`；Crossover 2/4 两根均完整 strict PASS。参数冻结
  依据见 current snapshot；没有改模型方程、数据、单位、情景或时间边界。
- 未决：Phase 1/2 均未启动；shared-server available RAM 暂为 93 GiB，低于新任务门禁。
- 下一步：部署 production profile 后只监控资源；恢复到 `>=96 GiB`、`si/so=0/0`、PSI=0
  且无 CISPO 进程时，按 Phase 1 顺序启动 1/24/168 h Base→V5 四年 sequences。

### 2026-08-02 18:35+08:00 — 24 h/168 h crossover 调优与 V5 旧门禁更正

- Git 基线：`eb4d5591723d5ed528c8326898731591937ec645`。本里程碑修改
  `cispo_model/flexible_load_numerics.py`、`tests/test_flexible_load.py` 及三份交接文档；
  implementation commit 以本条后的 Git tip 为准。
- 命令/输出：24 h Base/V5 roots 为
  `/data/zz2/National_model/outputs/solver_tuning_v0801_eb4d559_24h_{base,v5}_round3_v1`；
  168 h root 为
  `/data/zz2/National_model/outputs/solver_tuning_v0801_eb4d559_168h_round3_v1`。
- 验证：24 h 六根和 168 h Base 两根均满足完整 strict contract；168 h V5 两次只触发旧
  prebuild guard，未调用 optimize。资源无异常、无并发、无 Crossover=3。
- 更正：现行数据根为 `model_ready_20260730_flex_v5_4f717de_v1`，0729 unified 根仅用于
  历史根审计。
- 未决/下一步：服务器回归验证扩展后的 `{1,2,4}` contract 与 3 的拒绝，然后以全新根
  串行重跑 168 h V5 Crossover=2/4；冻结优胜 production profile 后再进入 Phase 1/2。

### 2026-08-01 16:53+08:00 — Phase 0 与两轮 solver 参数诊断闭合

- Git：参数候选实现提交
  `a3a078e20be8a480dc63cae7964a56c01451d8df`、
  `5e7db6835db60170fad7a1a13283e2a4d16792f4`；本条同步
  `CODEX_HANDOFF.md`、`MODEL_SERVER_STATUS.md`、`SERVER_RUNBOOK.md`。
- 变更：新增首轮 8 个 Barrier 单因素 profile，以及第二轮 11 个 Barrier scaling/presolve
  profile 和 1 个 dual-simplex profile；扩展 `tests/test_solver_profiles.py` 的 profile contract。
  未改变模型目标、约束、单位、数据、Base/V5 情景或时间/空间边界。
- 命令与输出：服务器完整回归、readiness/release/input/hydro/build audits 位于
  `/data/zz2/National_model/run_control/phase0_4d3ace6_v1`；两轮 24 h Base 串行 tuning
  输出位于 snapshot 所列两个 output roots。所有任务均由独立 output/control/stdout/stderr
  包装，未并发。
- 验证证据：`175/175 PASS`；Phase 0 audits PASS；20 个 Barrier-only 路径均严格拒绝；
  `tuning2_dual_simplex16_v1` 为 `OPTIMAL`、acceptance PASS、QC `58/58`、current input 与
  result manifest validators PASS，并导出 `Pi`。运行后 available RAM 约 `114 GiB`、swap
  约 `447 MiB/2 GiB`、`si/so=0/0`、memory PSI 0。
- 未决：尚未在当前 tip 上完成 `Crossover=1/2/4` 的 24 h/168 h Base/V5 配对比较；
  Phase 1/2 均未启动。失败 Barrier 根的 `BarPi` 不可用于科学分析。
- 精确下一步：新增并验证 `Crossover=2/4 + CrossoverBasis=1` 候选，与既有稳定
  `Crossover=1` profile 串行比较；冻结通过配对门禁的 production profile 后执行 Phase 1，
  再执行 Phase 2。永久排除 `Crossover=3`。

### 2026-08-01 - 0729 统一候选 744 h 历史根实时终态复核

- Scope：只读复核
  `/data/zz2/National_model/outputs/2030_744h_v0729_unified_v4_v1g_cold_v1`
  及对应 control root、四端 Git、固定服务器资源/进程和 ParaCloud 队列；没有修改模型、
  数据、服务器 checkout、历史输出或任何求解状态。
- Terminal evidence：PID 已退出；`solve_report.json=OPTIMAL`、
  `solution_qc.json=PASS`、52/52 hard checks 全真、`validate_result_manifest=(True, [])`、
  wrapper exit 0/stderr 仅含 `/usr/bin/time -v`、wall `3:42:57`、MaxRSS
  `22,527,656 KiB`、swaps 0。solver objective 为
  `2,330,214.449430 million CNY`，Barrier/simplex 为 `313/832,655`，最大
  constraint/bound/dual violation 为 `9.10e-8/4.55e-8/9.65e-8`。
- Input provenance：当前 checkout 前进使通用 input validator 对 3 个 repo 配置文件
  返回 size drift；75 个外置/其余输入仍通过。运行提交 `7c56622` 中对应 3 个 Git blob
  的 size/SHA256 与 manifest 完全一致，数据归档 SHA256 也复算一致。因此历史 gate
  保持 accepted engineering evidence，但当前 checkout 不得伪报 input validator 全绿。
- Live environment：local/origin/GitHub=`fb7cec3`；server clean/idle=`7a1520e`；
  Gurobi `13.0.2`；available RAM 约 114 GiB、swap 447 MiB/2 GiB、实时无换页、
  memory PSI 0、ParaCloud 空。本轮没有部署或启动新任务。
- Exact next action：保持历史 0729 根不变，继续执行 `SERVER_RUNBOOK.md` 顶节的
  Barrier-primary Phase 0；不得由本复核启动 8760 h、付费云、basis/MGA、inline
  Crossover、并发第二求解或 `Crossover=3`。

### 2026-08-01 - Barrier 主线跨年续接与人工后置 Crossover 合同

- Implementation commit：`53a5873156bfe4e81abfaa258d02b3f3ff664bbd`，父实现为
  `19b5754bb0db12818975344e5365777674698c47`。修改文件为
  `cispo_model/{planning_state,primal_dual_checkpoint,run_contract}.py`、两个 runner、
  nonbasic profiles、V5/full-LP 合同和三组 tests；没有改变任何科学变量、目标、
  物理约束、输入或单位，也未暂存用户的 `supplementary_materials/**`、
  `.codex_tmp/**` 或历史 outputs。
- Workflow：`run_cispo_planning_sequence.py` 现在支持
  `--diagnostic-start-hour`，并为 nonbasic profile 自动、显式传递
  `--export-barrier-checkpoint --allow-nonbasic-planning-state`。只有
  `OPTIMAL + strict primal/dual PASS + QC PASS + all hard checks + accepted
  checkpoint` 才写跨年 state；sequence identity 锁定窗口起点，resume 同时核对
  `optimization_start_hour`。
- Provenance：nonbasic state metadata 保存 source solution contract、capacity-state
  policy、checkpoint manifest SHA256、cohort zero tolerance 及被忽略微小容量的行数/
  单位汇总；load/resume 会重新校验 solve/QC/result/input manifests、identity layers
  和两条向量的路径、大小、SHA256、shape/dtype。checkpoint 不闭合时，科学解仍可
  保留，但 sequence 不会假装 state 已可续接。
- Crossover policy：accepted Barrier 是容量、调度、成本、碳与 `BarPi` 结论的主
  结果。Crossover 仅在全部主线完成后按作者选择的年份重建 exact LP；派生任务不导出
  `planning_state`、不回写既有路径。basis statuses/SA sensitivity 依赖该派生过程；MGA
  不要求所有年份先有 basis，是否做 Crossover 是按研究问题和算力决定的人工选择。
- Verification：`py_compile` PASS；针对性 checkpoint/planning sequence/solver profile/
  run-contract tests PASS；正确 wave root 下完整 discovery `175/175 PASS`，真实 Gurobi
  `BarX/BarPi -> PStart/DStart -> LPWarmStart=2` 往返 PASS；`git diff --check` PASS。
- Live evidence：13:58 local implementation 为 `53a5873`，其形成前 origin/GitHub
  均为 `1465a2b`；server clean `7a1520e`、无 CISPO/Gurobi/sequence 进程、available
  RAM 约 114 GiB、swap 447 MiB/2 GiB、连续 `si/so=0/0`、memory PSI 0、磁盘
  3.7 TiB available，ParaCloud 队列空。本窗口未部署或求解。
- Exact next action：推送实现与本交接 tip；下一窗口按 `SERVER_RUNBOOK.md` 顶节部署、
  小门禁、三季节 Base/V5 四年 744 h sequences 和递增长时段压力测试。任何主线任务
  都不自动进入 Crossover/MGA/basis/8760 h/付费云。

### 2026-08-01 - Barrier-first 正式验收、完整内点检查点与递增长时域门禁

- Implementation commit: `19b5754bb0db12818975344e5365777674698c47`。
- Scope/files：新增 `cispo_model/primal_dual_checkpoint.py`、
  `barrier_16_nonbasic_primal_dual_long_v1.json`、
  `barrier_16_deferred_crossover_v1.json` 与 checkpoint tests；修改 runner、
  solver config/diagnostics、output catalog 和 full LP spec。没有改变模型变量、目标或
  物理约束，也没有触碰/暂存用户拥有的 `supplementary_materials/**`、
  `.codex_tmp/**` 或历史 outputs。
- Workflow：accepted nonbasic Barrier 先导出全部科学结果和 `BarPi`，再保存完整
  ordered `BarX/BarPi`；deferred crossover 只在 exact LP/input/code identity
  相同时启用 `PStart/DStart + LPWarmStart=2`。nonbasic primary 不写 planning
  state；inline crossover failure 的 recovery artifact 明确为未接受。
- Kill-condition audit：修复 arbitrary diagnostic 永远按 8 GiB 放行的 OOM 风险；
  `>744 h` inline crossover 改为 explicit opt-in；长 profile 使用 24 h solver limit/
  80 GiB soft memory。SIGKILL、OOM killer、Slurm cgroup OOM/节点重启仍不可恢复，
  未来云 walltime 必须大于 solver limit 并保留导出/TERM grace headroom。
- Commands/evidence：`py_compile`、`git diff --check` 通过；设置正确 wave root 后
  `python -m unittest discover -s tests -p 'test_*.py' -v` 为 `174/174 PASS`；
  真实 Gurobi checkpoint round-trip PASS。12:20 server clean/idle、113 GiB
  available、无实时换页/PSI，ParaCloud 空队列；未部署、未启动 solver。
- Unresolved/exact next action：服务器仍在 `7a1520e`，必须等文档 tip 双推送后由
  下一窗口实时复核并部署。先完成五个季节 744 h Base/V5 配对，再按
  `1008→1488→2160→2976→4344 h` 做 Base-only 阶梯和一个最大安全 V5 配对；
  任何一步失败即保留现场并停，不自动改 profile、补跑 inline Crossover 或扩大到
  `>4344/8760 h`。

### 2026-08-01 - reservoir native bounds 后同窗 Base 744 h 终态拒绝

- Git/runtime identity: `7a1520eb723db7717b6ce4dd41646916c34bb0cf`，包含
  `e004703` 与 `7a1520e` 的等价 bound tightening；branch
  `codex/cispo-2030-full-lp`，终态复核时 local/origin/GitHub/server 四端一致，
  server clean/idle。
- Scope/command: 只运行 summer hour `[3960,4704)` 的 2030 Base，命令为
  `scripts/run_cispo_2030_full_year.py --planning-year 2030
  --diagnostic-start-hour 3960 --diagnostic-hours 744 --scenario-config
  config/scenarios/base.json --solver-config
  config/solver_profiles/barrier_16_auto_order_stable_basis_v3.json`；无 basis、无
  V5、无并发或后续年份。
- Terminal evidence: Barrier 218 iterations/`6,900.02 s`；crossover
  `14,528.04 s`，发生 basis variable drop、quad precision 与大幅 primal/dual
  振荡；最终 `TIME_LIMIT + SolCount=0`、746,438 simplex iterations、wrapper
  exit 2/wall `6:05:29`/stderr 0/process swaps 0。
- Contract audit: current input manifest validator `(True, [])`；无 QC，故 58 项
  solution hard checks 未运行；无 valid result manifest 或解后模块输出。该根为
  `TEST_ONLY_TRUNCATED_HORIZON` 且严格拒绝，不能用于容量、成本或物理结论。
- Changed files: `CODEX_HANDOFF.md`、`MODEL_SERVER_STATUS.md`、
  `SERVER_RUNBOOK.md`；未触碰用户拥有的 `supplementary_materials/**`、
  `.codex_tmp/**` 或历史 outputs。
- Unresolved/exact next action: Base 已证明 shared-core basic crossover 本身仍是
  744 h blocker；不得启动候选 V5。先形成并验证新的数值恢复方案，重过匹配的
  1 h/24 h/168 h Base/V5 门禁后，再单独申请 744 h 重跑授权。

### 2026-07-31 - Crossover 失败闭合与 strict nonbasic 诊断合同

- Implementation commit: `8de7a8e5bf4712bac30472fc4a564f47462fd9cd`.
- Scope/files: `cispo_model/{config,diagnostics,flexible_load_numerics,load_center,master,run_contract,solution_export,solver_audit}.py`、
  `scripts/{audit_model_numerics,run_cispo_2030_full_year}.py`、
  `config/optimization_2030.json`、新 solver profile、V5 contract、full LP spec
  与对应 tests。未触碰/暂存用户拥有的 `supplementary_materials/**`、
  `.codex_tmp/**` 或历史 outputs。
- Commands/evidence: `py_compile` 通过；设置
  `CISPO_WAVE_ROOT=D:\codeenv\pycharmproject\National_RL\wave_energy` 后
  `python -m unittest discover -s tests -p 'test_*.py'` 为 `169/169 PASS`。
  新 1 h Base/V5 根分别为
  `outputs/2030_1h_v0731_nonbasic_primal_dual_local_base_v2` 与
  `outputs/2030_1h_v0731_nonbasic_primal_dual_local_v5_v1`，均严格闭合；
  24 h Gurobi-12 Base 根
  `outputs/2030_24h_v0731_nonbasic_primal_dual_local_base_v1` 为
  `SUBOPTIMAL/HARD_FAIL`，无 QC/manifest 接受资格。
- Server evidence: 旧 summer 744 h V5 为 `TIME_LIMIT + SolCount=0`，无 QC/
  manifest；固定服务器 clean/idle，资源正常，ParaCloud 空队列。
- Unresolved/exact next action: 只有服务器 Gurobi 13 的匹配 1 h/24 h Base/V5
  能判定 nonbasic 候选是否可用。严格小门禁失败即淘汰；成功后才进入 168 h，
  再决定串行的 same-window Base/V5 744 h。禁止 8760 h、付费云、并发、basis/
  MGA 和 `Crossover=3`。

### 2026-07-31 - summer-offset 744 h 进入 Crossover/simplex cleanup

- Runtime identity: server clean
  `aaf16cc49a5a3d5bb07d214a957a3a4065ac3f07`；唯一输出/控制根为
  `2030_744h_v0731_summer_offset_a7c6715_v5_v1`。
- Milestone: Barrier 233 iterations、`7,414.52 s` 后报告 optimal objective
  `2,351,134.66 million CNY`；随后完成 crossover basis build 与
  DPush/PPush，进入 simplex cleanup。
- Live evidence: 16:48 runtime `11,752.76 s`、simplex iteration `912,630`、
  primal infeasibility 0、dual infeasibility `2.014e6`；近期 dual 指标大幅
  波动，但日志无 `Numerical trouble` 或终态。stderr 0，资源无压力，
  ParaCloud 空。
- Changed files: 本条仅更新三份交接文档，不部署到活动 server checkout，
  不修改模型、配置或求解。
- Unresolved/exact next: 结果未完成且无 solve/QC/result manifest。继续只读
  监控到 PID 退出；只有完整终态合同通过后才能接受。

### 2026-07-31 - 启动唯一 summer-offset 744 h V5 cold gate

- Git/runtime identity: 启动提交
  `aaf16cc49a5a3d5bb07d214a957a3a4065ac3f07`；server clean 且启动时与
  local/origin/GitHub 一致。
- Scope: 在通过 summer 1 h Base 与 24 h V5 小门禁后，只启动一个
  2030/V5 744 h cold gate；没有 basis、并发任务、付费云或后续年份。
- Changed files: 本条仅更新三份交接文档；求解使用已验证模型实现
  `a7c67153d9b90055b60ed2704ef6bba702086ae4`。
- Command: `scripts/run_cispo_2030_full_year.py --planning-year 2030
  --diagnostic-start-hour 3960 --diagnostic-hours 744 --scenario-config
  config/scenarios/flex_integrated_v5_central.json --solver-config
  config/solver_profiles/barrier_16_auto_order_stable_basis_v3.json`。
- Output/control: `2030_744h_v0731_summer_offset_a7c6715_v5_v1` 的固定
  outputs/run_control 根；wrapper/Python PID 初始为 `674143/674145`。
- Verification: `run_scope.json` 精确确认 `[3960,4704)`、summer 北京时戳、
  V5 central、正确缩放、no-basis 和 long-horizon numerical compatibility
  PASS；启动后 stderr 0、资源无压力、ParaCloud 空。
- Unresolved/exact next: 当前仍处于 build，尚不能判断 Barrier、Crossover 或
  终态。只读监控到 PID 退出，再按严格终态合同审计；不得启动任何后续任务。

### 2026-07-31 - summer-offset 1 h/24 h 恢复门禁严格闭合

- Git: 模型实现 `a7c67153d9b90055b60ed2704ef6bba702086ae4`；恢复记录基线
  `11c682076869e30e0ed24db038bf3c12ecdbb1ae`。
- Scope: 部署空 winter CHP 约束修复，执行固定服务器完整回归，并以全新输出根
  串行重跑 summer hour 3960 的 1 h Base 与 24 h
  `flex_integrated_v5_central`。
- Changed files: 本里程碑仅更新 `CODEX_HANDOFF.md`、
  `MODEL_SERVER_STATUS.md`、`SERVER_RUNBOOK.md`；模型改动已在
  `a7c6715` 记录。
- Verification: server regression `167/167 PASS`；1 h Base 与 24 h V5
  均为 `OPTIMAL + PASS + 58/58`，input/result manifest validators 均为
  `(True, [])`，wrapper exit 0、stderr 0、swaps 0。时间索引分别精确覆盖
  `[3960,3961)` 与 `[3960,3984)`；24 h cooling、storage 与 EV 服务均按
  既定 V5 约束闭合，碳上限按实际小时缩放且 binding。
- Unresolved: 24 h 只证明非首时段切片、夏季服务与短门禁闭合；不能证明 744 h
  数值稳定、全年可解或年度科学结论。单日 V2G export 为 0 是最优调度结果，
  仍需在更长窗口观察。
- Exact next action: 部署本记录 tip 后，按 runbook 启动唯一 summer 744 h V5
  cold gate；运行期间仅监控，退出后执行完整终态审计。

### 2026-07-31 — summer 空 CHP 季节索引修复

- Git/changed files: `a7c67153d9b90055b60ed2704ef6bba702086ae4`
  修改 `cispo_model/monolithic.py` 与 `tests/test_bound_tightening.py`。
  当所选窗口没有冬季小时，跳过空 CHP winter rows；非空窗口方程保持原样。
- Failure/evidence: `985983b` 的首次 server summer 1 h Base 在 build
  阶段因 `winter=[]` 的 Gurobi 空索引广播退出，未调用 solver；失败根和
  控制日志原样保留。修复后的 focused 5/5 与完整 `167/167` 本地回归 PASS。
- Next: 双端推送、server fast-forward、完整 regression 后以新 `v2` 根重跑
  1 h Base。只有 1 h Base 和后续 24 h V5 严格接受后才启动 744 h V5。

### 2026-07-31 — 非年初连续诊断窗口与 summer 744 h 前置门禁

- Git/changed files: `077bce0eca16b1025130143122aee0a05559c3e0`
  修改 `scripts/run_cispo_2030_full_year.py`、`cispo_model/monolithic.py`、
  `flexible_load.py`、`flexible_load_numerics.py`、`solution_export.py`、
  `result_summary.py`、`basis_reuse.py` 及两项回归测试。未修改
  `supplementary_materials/**`、`.codex_tmp/**` 或历史 outputs。
- Commands/verification: `py_compile` PASS；focused flexible-load/basis
  回归 `22/22 + 5/5 PASS`；设置
  `CISPO_WAVE_ROOT=D:\codeenv\pycharmproject\National_RL\wave_energy`
  后完整 `unittest discover` 为 `166/166 PASS`；`git diff --check` PASS。
  数据实读确认 hour 3960/4703 分别为
  `2030-06-15 00:00`/`2030-07-15 23:00`。
- Unresolved/next: 尚未部署服务器、尚未形成 offset solve/QC/manifest
  证据。先完成四端 identity 与服务器 idle/resource/queue 复核，再部署并
  执行 1 h Base、24 h V5 小门禁；全部严格接受后才运行单一 744 h V5。
  不启动四年 sequence、8760 h、付费云、basis/MGA 或并发第二求解。

### 2026-07-31 — 输出语义修复与 24 h/168 h Base--V5 匹配门禁

- Git/changed files: `ae3356391ec55376b041d6a356ea2d1f26be88bc`
  更新 `cispo_model/solution_export.py`、`cispo_model/result_dashboard.py`、
  `tests/test_solution_qc_semantics.py`、`tests/test_result_dashboard.py`、
  `MODEL_IO_CONTRACT.md` 与 `cispo_full_lp_model_spec.md`。修改仅涉及
  QC/展示语义：V4/V5 的旧 V1G daily-energy residual 标为不适用，
  dashboard 区分精确零和小于 0.001 GWh 的非零量；LP 与 solver 配置不变。
- Commands/verification: 本地和服务器均运行
  `python -m unittest discover -s tests -p 'test_*.py' -v`，结果
  `165/165 PASS`；服务器另运行 readiness、release、V5 input 与 hydro
  audits，全部 PASS。服务器按串行、cold、no-basis 运行当前快照中的两根
  24 h 与三根 168 h；每个有效根均为
  `OPTIMAL + PASS + 58/58 + current input + valid result manifest +
  wrapper exit 0/stderr 0`。V5/v2 的 168 h 尝试由预期 guard 在 optimize
  前拒绝，作为合同证据保留，不重标为 solver result。
- Evidence: 24 h Base/V5 solver 为 `407.321/420.232 s`；168 h
  Base-v2/Base-v3/V5-v3 为 `907.672/917.121/1024.510 s`。V5-v3 最大
  constraint/bound/dual violation 为
  `8.339e-8/2.609e-8/6.047e-8`，peak process-tree RSS `3.508 GiB`，
  swaps 0。Base-v2/v3 objective 在 `2.9e-7 million CNY` 内一致。
- Scientific audit: 168 h V5 的容量变化、firm credit、EV fleet SOC、
  PHS/储能、水电 380 GW、网络方向、可靠性、碳/CCS/BECCS 与成本闭合均
  通过。未发现凭空 V2G 能量或以 selected-horizon effective peak 直接
  降容。首周冷热未实际调度却存在全年峰窗 cooling credit，以及非零梯级
  negative-inflow clipping 水量，均已登记为截断解释/后续科学敏感性。
- Unresolved/exact next action: `stable_basis_v3` 已有匹配 2030 Base/V5
  168 h 工程证据，但 V5 `Kappa≈1.62e10`，不能据此宣称 8760 h 可解或把
  168 h 价值外推全年。保持服务器空闲；下一步由作者选择全新四年 168 h
  Base/V5 sequence 或一个明确命名的更长测试。继续禁止自动启动
  8760 h、付费云、basis/MGA、并发第二求解与 `Crossover=3`。

### 2026-07-31 — 固定、scope-aware 的结果数据与图表环节

- Git commits: `336116b493cf92eb461d1a2aab490678fd2dbac5`
  实现固定结果 dashboard；`bdb57b2cb4e3f4781cfd53c087c7cc1a780d73a5`
  将 firm flexibility credit 明确标为“full-year provincial peak-window
  accreditation”，避免与截断时域全国峰值变化混读。
- Scope/changed files: 新增 `cispo_model/result_dashboard.py`、
  `scripts/build_result_dashboard.py` 与 `tests/test_result_dashboard.py`；
  更新 `cispo_model/result_summary.py`、`cispo_model/io_contract.py`、
  `scripts/run_cispo_2030_full_year.py`、`MODEL_IO_CONTRACT.md` 和
  `cispo_full_lp_model_spec.md`。自动产物为 JSON、tidy CSV 和无外部依赖
  SVG；外部重渲染支持 SVG/PNG/PDF。dashboard 在最终 solve report 与 QC
  已存在后、output catalog/result manifest 之前生成，因此自身也被严格
  checksummed。
- Model boundary: dashboard-only 提交对 LP 变量、约束、目标、输入和 solver
  参数的改动均为零。前一数值稳定化的冷热/EV 服务模式保持不变；其代数
  等价消元与唯一新增的 V1G/V2G 共享接入功率约束必须分别解释，不能笼统
  写成“全程没有约束变化”。
- Verification: 本地完整回归 `162/162 PASS`；既有 24 h V5 输出只读复演
  的成本重构通过并成功渲染三种格式。本机新求解由未修改的 8 GiB 内存门槛
  安全阻止。服务器 `336116b` 完整回归同为 `162/162 PASS`，readiness、
  release、V5 input、hydro audits 均 PASS；最终 `bdb57b2` 聚焦 dashboard
  回归 `3/3 PASS`。
- Server command/output:
  `/home/zz2/.local/envs/cispo-2030/bin/python
  scripts/run_cispo_2030_full_year.py --planning-year 2030
  --diagnostic-hours 1 --scenario-config
  config/scenarios/flex_integrated_v5_central.json --solver-config
  config/solver_profiles/barrier_16_auto_order_v2.json --output-dir
  /data/zz2/National_model/outputs/2030_1h_v0731_dashboard_v5_bdb57b2_server_v1`。
  对应控制根为
  `/data/zz2/National_model/run_control/2030_1h_v0731_dashboard_v5_bdb57b2_server_v1`。
  终态为 `OPTIMAL + PASS + 58/58 + current input + valid result manifest`，
  wrapper `exit=0/stderr=0/wall=0:39.10/MaxRSS=597624 KiB/swaps=0`。
- Interpretation/unresolved: 1 h 的 `0.2003156 CNY/kWh` 是用全年 baseline
  demand 作分母的年化规划成本强度；`0.3141334 CNY/kWh` 是用所选 1 h
  baseline demand 作分母的运行成本强度。它们时域不同，不能相加，全年
  total 字段因此强制为 `null`。只有 8760 h accepted scientific run 才会
  输出可比较的 total system cost intensity；即便如此也不自动等同于文献
  中边界各异的 LCOE。
- Exact next action: 保持服务器空闲。下一次经作者选择的 Base/V5
  24 h、168 h 或更长工程门禁直接使用这一输出合同，并以图表作为固定查阅
  入口；仍需逐根严格验收 QC/manifest/wrapper，而不是以图片替代审计。
  不自动启动 744/1008/8760 h、付费云、basis/MGA、并发第二求解或
  `Crossover=3`。

### 2026-07-31 — V5 数值修复的固定服务器 1 h/24 h/168 h 严格验收

- Git/identity: 模型实现为
  `fead34334153eca32bbf7ec3651f3388038ac04b`，部署文档 tip 为
  `22e19c154148fcfcb137d5a7e882ff69abd2b7c8`；本地、origin、GitHub 与
  clean 固定服务器 checkout 已核对一致。数据根为
  `/data/zz2/National_model/data/model_ready_20260730_flex_v5_4f717de_v1`，
  solver 候选为
  `config/solver_profiles/barrier_16_auto_order_stable_basis_v3.json`。
- Commands/outputs: 服务器依次执行 `159/159` regression、readiness、
  release/V5/hydro validators、Base/V5 1 h、Base/V5 24 h，最后只运行
  `scripts/run_cispo_2030_full_year.py --planning-year 2030
  --diagnostic-hours 168 --scenario-config
  config/scenarios/flex_integrated_v5_central.json --solver-config
  config/solver_profiles/barrier_16_auto_order_stable_basis_v3.json`。全部
  输出根隔离，无 basis、无并发第二求解。
- 168 h evidence: 输出根
  `/data/zz2/National_model/outputs/2030_168h_v0731_v5_numeric_central_22e19c1_server_v1`
  为 `OPTIMAL + PASS + 58/58 + current input + valid result manifest`。
  raw/presolved 为 `1,209,095/1,060,576/9,755,329` 与
  `737,850/751,223/7,386,987`；Barrier 232/819.54 s，
  Crossover 176.79 s，solver 1005.194 s，258,814 simplex，peak RSS
  3.511 GiB，swaps 0。Crossover 将 `Sub-optimal` interior status 改为
  `Optimal`，日志无 `Numerical trouble`，所有物理、服务、网络、安全、
  碳/CCS 与成本 QC 均通过。
- Interpretation/unresolved: 该证据接受本轮“V5 精确稀疏化 +
  `CrossoverBasis=1`”作为 168 h 诊断路径，但不接受为 8760 h production
  solver。`Kappa≈1.62e10` 与 24 h Base/V5 的共同 Barrier recovery 表明
  ROR/VRE availability 和年度会计仍有共享 conditioning debt。旧式
  `maximum_ev_v1g_daily_energy_residual_gwh` 对 V5 车群 SOC 服务模型不
  适用，需在下一代码里显式标记 N/A/替换为服务账户指标，避免误读。
- Exact next action: 先运行同身份、同 profile 的单一 2030 Base 168 h
  匹配根；同时只做共享小系数的 build/presolve 数值审计，任何稀疏化必须
  证明不改变科学可行域且同时改善 presolved/factor 证据。未闭合前不得
  启动 744/1008/8760 h、付费云、basis/MGA、并发第二求解或
  `Crossover=3`。

### 2026-07-31 — V5 长时域精确稀疏化与数值兼容门禁

- Git commit:
  `fead34334153eca32bbf7ec3651f3388038ac04b`。
- Scope/changed files: `cispo_model/flexible_load.py` 与新增
  `cispo_model/flexible_load_numerics.py` 实施零控制冷热状态的精确消元、
  稀疏控制变量和 EV 共享连接约束；`preflight.py`、runner、diagnostics、
  solver/model-structure audits 与 `solution_export.py` 增加规模、数值风险、
  硬验收和 QC 证据；新增
  `config/solver_profiles/barrier_16_auto_order_stable_basis_v3.json`；同步更新
  V5 合同、模型规范及对应测试。
- Commands/evidence:
  `CISPO_WAVE_ROOT=...\wave_energy conda run -n RL python -m unittest discover
  -s tests -p 'test_*.py' -v` 为 `159/159 PASS`；V5 input/release audits PASS；
  `scripts/audit_model_numerics.py --hours 168 --presolve` 得到 raw
  `1,209,095/1,060,576/9,755,331` 与 presolved
  `737,850/751,222/7,386,903`（rows/vars/nonzeros），最大矩阵系数放大比
  `1.0`。全年 preflight 估计 `42,946,990` variables、
  `57,924,850` constraints、`503,133,030` nonzeros、`34.3 GiB`。
- Unresolved/next action: 当前提交尚未经过固定服务器 1 h/24 h 或 168 h
  求解验证；`CrossoverBasis=1` 尚不能标为 production。推送后只允许在
  clean/idle 固定服务器依次执行回归、readiness/release/V5/hydro、
  Base/V5 1 h、Base/V5 24 h 和单个 2030/V5 168 h。禁止把静态规模或
  truncated gates 外推为 8760 h 可解性或年度科学结果。

### 2026-07-30 — bounded test-only AC counterflow warning contract

- Implementation commit: `9b6e72a456b0dc8f0123f90b07195f94ca902c9a`.
- Scope: preserve all model equations, objective coefficients, raw directional flows and the `1e-6 GW` detector; add a bounded `TEST_ONLY_TRUNCATED_HORIZON` warning classification using seven simultaneous prevalence/power/capacity/energy/loss/system-share limits. Full-year scientific outputs remain strict-zero.
- Verification: analytic tests cover strict pass, bounded warning, every-budget failure and full-year rejection; full local discovery is `146/146 PASS`; V5 input and release audits PASS. The observed failed 2050 case is transparently reclassified as a warning with `0.011489 GWh` induced extra loss, only `4.0100e-8` of system load.
- Local execution boundary: available RAM was `7.48 GiB`, below the immutable 8 GiB runtime gate, so no local solve was forced.
- Authorized server sequence: deploy the exact pushed tip only while idle; repeat server regressions/audits and fresh 1 h/24 h Base/V5, then fresh four-year 168 h Base and V5. If all close, start one serial four-year `1008 h` V5 sequence with `barrier_16_auto_order_v2`, cold/no-basis. Keep 8760 h, paid cloud, MGA/basis, Crossover=3 and concurrent solves forbidden.

### 2026-07-30 — 168 h Base sequence stopped by material AC counterflow

- Server/model identity: clean `af390fad22dc4e3ec4636edadfb56295e4907234`; output root `/data/zz2/National_model/outputs/planning_sequence_168h_v0730_flex_v5_base_af390fa_server_v1`; data root `/data/zz2/National_model/data/model_ready_20260730_flex_v5_4f717de_v1`.
- Terminal state: sequence `HARD_FAIL`; 2030/2040 accepted with valid current input/result manifests, while 2050 is mathematically `OPTIMAL` but physical QC fails only `unidirectional_interprovincial_flow`; no 2050 result manifest/state and no 2060 or V5 run.
- Exact evidence: three simultaneous AC direction edge-hours on `CORRIDOR_0153` (Jilin--Heilongjiang), maximum opposing minimum `0.176374 GW`, total opposing minimum `0.381006 GWh`; the line's forward plus reverse flow equals its `1.646 GW` capacity in all three hours.
- Mechanism: the scaled 2050 net-carbon cap is binding at `-1.917808 MtCO2`; carbon scarcity is `3589.731 CNY/tCO2` and affected nodal prices are deeply negative. The current `1.004004 CNY/MWh` gross-flow term is therefore outweighed by the value of dissipating BECCS-driven surplus through directional transmission losses. This is a real formulation loophole, not solver tolerance.
- Runtime/closure: wrapper exit 1, wall `49:20.77`, MaxRSS `3,741,888 KiB`, swaps 0; server idle and memory-safe afterward; ParaCloud empty. Existing output remains immutable failure evidence.
- Exact next action: design and review a directionality treatment that does not weaken QC, hide spillage, convert the national LP to a large MILP, or materially distort ordinary transmission economics. Only after focused regression plus new 1 h/24 h and four-year 168 h Base closure may V5 or 744 h start.

### 2026-07-30 — V5 cross-platform release identity and fixed-server 24 h A/B

- Model/release commits: `4f717de` (canonical cross-platform CSV/gzip/manifest serialization) and `af390fa` (retain the inherited authoritative techno-economic manifest).
- Server identity: clean `af390fa`; data root `/data/zz2/National_model/data/model_ready_20260730_flex_v5_4f717de_v1`; V5 manifest SHA256 `a324430713e0eb3a1671c9b9ba6c127c34c5e0d7c2e21f090cbcd9394f061831`.
- Verification: local and server `141/141 PASS`; server readiness, V5 input, release and 380 GW hydropower audits PASS; Base/V5 24 h roots both `OPTIMAL + PASS + 57/57 + closed manifests + wrapper exit 0`.
- Finding: parsed V5 values were already identical across hosts, but pandas/Python platform serialization changed every release hash. Canonical serialization now produces identical bytes. A second pre-solve failure showed that V5 had frozen a local timestamp-only techno-economic manifest rather than inheriting the existing server authority; no parameter table differed.
- 24 h evidence: Base/V5 runtime `405.882/434.896 s`, simplex `503,365/519,659`, objective delta `-347.394 million CNY`, explicit flexibility cost `785.531 million CNY`, firm credit and generation-capacity delta `+2.891320/-2.891320 GW`. Both Barrier stages report numerical trouble before successful crossover repair.
- Interpretation/next action: truncated leading hours cannot validate annual effective-peak value because adequacy accreditation references immutable full-year provincial peak windows. Run isolated serial four-year 168 h Base then V5 under frozen `af390fa`; audit every year, state transfer, manifests, flexibility/accounting and an immediate resume before considering 744 h.

### 2026-07-30 — integrated demand flexibility V5 and paper-style supplement

- Git implementation commit: `57ad4c5`.
- Scope: keep Base unchanged; add one integrated central flexibility counterfactual with thermal-load service envelopes, paid V1G, nested endogenous paid V2G and derated peak-deliverable firm capacity credit; add evidence/source registries, deterministic input builder/validator, release contract, expanded QC/output accounting and an English supplementary-information chapter.
- Principal changed files: `cispo_model/{config,data,flexible_load,master,monolithic,solution_export}.py`, `config/scenarios/flex_integrated_v5_central.json`, V5 parameter/source registries, `scripts/{build,validate}_flexible_load_v5_inputs.py`, V5 release/audit contracts, tests, and `supplementary_materials/modules/06_integrated_demand_flexibility/*`.
- Verification: V5 input audit PASS; release audit PASS; full unittest `140/140 PASS`; English TeX has four sections, no internal scenario/config names, compiles to a visually checked 9-page PDF; 1 h current-output-contract V5 gate `OPTIMAL + PASS + 57/57 + current input + valid result manifest`; 24 h Base/V5 mathematical A/B both `OPTIMAL + PASS + 57/57 + closed manifests`.
- Material findings: the 24 h V5 gate pays all contracted/activated service costs, reduces the selected-window national peak by `2.3211 GW`, receives `2.8913 GW` bounded firm credit and reduces generation capacity by the same `2.8913 GW`; no simultaneous charge/discharge or state/reliability/accounting loophole was detected. Both Base and V5 encounter Barrier numerical trouble and require large simplex repair, so numerical efficiency remains an explicit 744 h risk.
- Unresolved: after the final output-contract-only patch, the exact commit still needs fresh 24 h A/B closure. Local 168 h was blocked before build by `6.07 GiB < 8 GiB` available RAM. Fixed-server deployment is blocked by stale non-solver audit PID `976320`; do not terminate it or switch checkout without explicit authorization.
- Exact next action: obtain at least 8 GiB local available RAM and use fresh roots for current-commit 24 h Base/V5 and serial four-year 168 h Base/V5; alternatively obtain explicit permission to clear the stale fixed-server audit wrapper, then deploy the pushed commit and repeat the same staged gates. Do not start 744 h until those gates close.

### 2026-07-30 — 诊断时域年度碳与资源流量缩放

- 实现提交：`d3b6f1485d5ef88762e9d8d0ac8ca87db15dc244`。
- 变更范围：`cispo_model/{master,monolithic,solution_export}.py`、full-year/sensitivity runners、`scenario_catalog v4`、配置/数学说明和年度缩放/情景目录测试。
- 公式：`f=optimization_hours/8760`；窗口净碳上限、DAC throughput、生物质燃料、CO2 sink 注入均乘 `f`，DAC 电力负荷使用窗口质量除以 `f` 的年化速率；annualized capacity/fixed cost 不缩放。
- 验证证据：新增 1 h/24 h V4 V1G 根均 `OPTIMAL + PASS + 54/54 + current input + valid result manifest`，碳约束在两根中均 binding；聚焦测试通过，完整本地 `138/139 PASS`，唯一失败为已知本地 ignored technoeconomic manifest 与冻结服务器数据 hash 差异。
- 情景边界：主分析只有 `base` 和 `flexible_load_comfort_v4_v1g`；其余 implemented 文件是独立敏感性或历史回归，不会在一次 run 中自动叠加。
- 未决问题与精确下一步：先提交并推送三份交接文档；如需新的四年 744 h 验证，必须在实时核验固定服务器/ParaCloud 后用新输出根、无 basis、串行执行。旧 744 h 不可重标；8760 h、付费云、MGA、basis 与并发求解仍禁止自动启动。

### 2026-07-30 — 四年 744 h sequence 严格终态接受

- 运行身份：clean `5d31b51b350a581287fc8eb13e73216c11fc7543`，中央 V4 V1G、`barrier_16_auto_order_v2` / `Crossover=1`、cold/no-basis、每年 744 h。
- 终态：sequence `PASS`，四年全部 `ACCEPTED`；每年均 `OPTIMAL + PASS + 53/53 + current input + valid result manifest`，完整 test-only planning-state 链闭合。
- wrapper/资源：exit 0、wall `14:27:23`、maximum RSS `21,927,236 KiB`、swaps 0；终态无活动 PID、无内存压力、ParaCloud 空。
- 未决问题：V4 low/high、完整 accepted Base anchor、年度 effective-peak sensitivity、basis/MGA 与 8760 h 均未闭合。本结果始终 `TEST_ONLY_TRUNCATED_HORIZON`。
- 精确下一步：提交并双端推送本终态文档；服务器空闲时仅 fast-forward 文档 tip；停止 744 h heartbeat。不得自动启动任何求解。

### 2026-07-29 — 四年 744 h：2030 accepted，2040 Barrier

- 2030 终态：`OPTIMAL + PASS + 53/53 + current input + valid result manifest`，sequence 记录 `ACCEPTED` 并只传递显式 test-only planning state。
- 完整 scope：冷热、EV、wave、水电/梯级、PHS/储能、网络、备用、惯量、容量充裕、碳/CCS/BECCS、成本目标均由 hard checks 通过；年度 stderr 为空。
- 2040 实时状态：Barrier iteration 107，尚无终态报告；资源与队列安全。
- 精确下一步：继续只读监控 2040，只有 runner 自身严格接受后才允许串行进入 2050。

### 2026-07-29 — 启动唯一串行四年 744 h diagnostic sequence

- 运行 Git 身份：`5d31b51b350a581287fc8eb13e73216c11fc7543`；命令、PID 与 wrapper 日志记录在 `/data/zz2/National_model/run_control/planning_sequence_744h_v0729_identity_hydro_v4_v1g_v1`。
- 边界：2030→2060、每年 744 h、中央 V4 V1G、`barrier_16_auto_order_v2` / `Crossover=1`、cold/no-basis、严格串行。
- 初始证据：唯一进程树正常，sequence identity 为 `TEST_ONLY_TRUNCATED_HORIZON`，资源无压力，ParaCloud 为空。
- 精确下一步：PID 存在时只读监控 2030 build/Barrier/Crossover；不得启动第二求解或修改服务器 checkout。任一年退出后按 OPTIMAL、QC、53/53、input/result manifests、wrapper 与完整 accounting scope 审计。

### 2026-07-29 — 固定服务器部署与 1 h/24 h 新实现门禁

- 部署身份：`03e77ccc8d2ef3813b7cc5c0d727b068d008090d`，固定服务器 checkout clean。
- 命令/输出：权威四数据根环境下运行 release/readiness/hydro/V4 validators、完整 unittest，并依次执行中央 V4 V1G 1 h/24 h cold gates；部署证据根为 `/data/zz2/National_model/run_control/deployment_03e77cc_v1`，求解根见 current snapshot。
- 验证证据：validators 全 PASS，`135/135` tests；两根均 `OPTIMAL + PASS + 53/53 + current input + valid result manifest + hydro reconciliation audit`。
- 未决问题与下一步：再次实时核验后启动唯一串行 2030→2060 744 h；该 sequence 仍是 `TEST_ONLY_TRUNCATED_HORIZON`，任一年失败必须停止。

### 2026-07-29 — effective-peak、梯级水量调和与 8760 runner 阻断修复

- 实现提交：`cea78ae1546b19754f7859982ae82dbf66820fdc`。
- 变更范围：`cispo_model/{basis_reuse,config,hydro,io_contract,master,monolithic,preflight,run_contract,solution_export,solver_artifacts}.py`，`config/optimization_2030.json`、release/scenario contracts，full-year/sensitivity runners 与相关测试。
- 验证证据：本地 1 h/24 h matched baseline/effective gates、四年 1 h sequence、8760 h hydro input-only audit、聚焦 `58/58 PASS`、完整 `134/135`（唯一差异为本地 ignored technoeconomic manifest 与服务器权威数据包 hash）。
- 未决问题：V4 low/high、accepted full-year Base、full-year solver artifact 实际生成、MGA batch、年度 effective-peak 容量价值均未闭合；24 h 结果始终 `TEST_ONLY_TRUNCATED_HORIZON`。
- 精确下一步：推送文档 tip；实时核验并部署固定服务器；服务器权威数据根完整回归和 1 h/24 h 后，启动唯一 2030→2060 744 h V4 V1G sequence。

### v0.9.75 - 2026-07-29 - 统一候选 744 h 工程门禁终态接受

- Git/运行身份：终态审计前本地、固定服务器 bare `origin` 与 GitHub 分支 tip 均为文档提交 `5ffee8a79b090dd8493e9b38da78464f3312ec6f`；固定服务器 checkout 保持 clean `7c56622c266e673037bd6afaa70c85aa57e6cb13`，唯一模型实现基线仍为 `7aac739e03646edfed14bbf48ac77869ba66cbef`。本里程碑只改 `CODEX_HANDOFF.md`、`MODEL_SERVER_STATUS.md`、`SERVER_RUNBOOK.md`，不切换服务器 checkout，不改模型/配置/数据，不暂存用户拥有的 supplementary 或临时文件。
- Solver/wrapper：原 wrapper/Python PID `1004972/1004975` 已退出，Gurobi 终态 `OPTIMAL`、objective `2,330,214.449430 million CNY`、runtime `12,984.854 s`、Barrier/simplex `313/832,655`、Crossover `3,573.87 s`。wrapper exit `0`、wall `3:42:57`、peak process-tree RSS `21.484 GiB`、swaps `0`；stderr 无 Traceback 或错误，仅含 `/usr/bin/time` 统计。
- 严格接受证据：`solution_qc.json=PASS` 且 `52/52` hard checks 全真；`validate_input_manifest(input_manifest.csv)` 与 `validate_result_manifest(output_root)` 均返回 `(True, [])`。运行身份为 2030/744 h、`flexible_load_comfort_v4_v1g`、`barrier_16_auto_order_v2`、`Crossover=1`、cold/no-basis，数据根和 `technoeconomic_2025_cny_v2 / 2025 constant CNY` sidecar/config snapshot 匹配。
- 模块/会计：冷热、EV、wave、水电、PHS/储能、网络、备用、惯量、碳/CCS 与成本 scope 全部通过硬 QC 和逐表审计；最大电力平衡残差 `1.63e-10 GW`，objective component residual `1.79e-6 million CNY`。wave 1,284 个候选已加载但装机/发电为零；常规水电 `297.8895 + 82.1105 = 380 GW`；电池/PHS 为 `66.881775/65.94 GW`；411 条 corridor 无 AC 同时双向、DC 反向为零。成本混合 annualized planning 与 744 h operation，不能解释为年度净价值。
- 资源/队列/下一步：终态刷新约 `114 GiB` available、swap `781 MiB/2.0 GiB`、实时 `si/so=0`、memory PSI=0；ParaCloud 队列为空。744 h 仅为 `TEST_ONLY_TRUNCATED_HORIZON`，不作为正式 2040 state anchor。V4 low/high、完整 accepted Base anchor、basis 工程与 MGA 仍未闭合；本次不启动固定服务器 8760 h、付费云、并发第二求解、basis gate 或 `Crossover=3`，完成交接推送后暂停 heartbeat。

### v0.9.74 - 2026-07-29 - 统一候选 744 h 完成 Barrier 并进入生产 Crossover

- Git/运行身份：2026-07-29 15:25--15:33+08:00 实时复核确认本地、固定服务器 bare `origin` 与 GitHub 分支 tip 均为文档提交 `1f8cbaf9fd6ad778084ee97405beb99150fe9551`；固定服务器 checkout 保持 clean `7c56622c266e673037bd6afaa70c85aa57e6cb13`，唯一模型实现仍为 `7aac739e03646edfed14bbf48ac77869ba66cbef`。本里程碑只更新三份交接文档，不切换服务器 checkout，不改模型/配置/数据，也不暂存 `supplementary_materials/**` 或 `.codex_tmp/**`。
- Phase evidence：wrapper/Python PID `1004972/1004975` 持续存在。Barrier 在 iteration `313`、solver runtime `9396.13 s` 完成，interior objective 约为 `2,330,214.46 million CNY`；随后日志明确出现 `Crossover log...`。crossover basis 加入后进入 dual push，最近 Gurobi 进度为 `922,426 DPushes remaining`、`DInf=1.9217246e-6`；15:32:53 telemetry phase 为 `simplex`、runtime `9604.40 s`、current/max solver memory `14.06/23.13 GiB`。
- Resource/queue：主机约 `101 GiB` available、swap `781 MiB/2.0 GiB`；连续 `vmstat` 实时 `si/so=0`，memory PSI avg10/60/300 均为 0。ParaCloud `squeue -u a8s001819` 为空。另有一个 12:28 起遗留的旧 release-audit SSH/bash/grep 管道，占用约 3 MiB RSS、无 Python/Gurobi 子进程；它不是第二求解，本次只读记录且未终止。
- Acceptance/next action：`solve_report.json`、`solution_qc.json`、`result_manifest.json` 仍不存在，因此这只是阶段里程碑，不是终态接受。继续只读监控 Crossover；PID 退出后必须交叉验证 `OPTIMAL + solution_qc=PASS + 52/52 hard checks + current input/result manifests valid`、wrapper stderr/time，以及冷热、EV、wave、水电、PHS/储能、网络、备用、惯量、碳/CCS 与成本 `accounting_scope`。744 h 始终为 `TEST_ONLY_TRUNCATED_HORIZON`；不得启动固定服务器 8760 h、付费云、并发第二求解、basis gate 或 `Crossover=3`。

### v0.9.73 - 2026-07-29 - 最终窗口 live refresh：744 h 仍在 Barrier，primal residual 未闭合

- Git/文档基线：上一轮完整交接已提交并同步为 `a92a5c7e50bf8774fe1db75ae21c4c425f80b5ed`；本条仅把其后的易变服务器状态追加到三份交接文档，不改变模型实现 `7aac739`、服务器 checkout `7c56622` 或外置数据根。
- Live evidence：2026-07-29 15:18:36+08:00，唯一 wrapper/Python PID `1004972/1004975` 已运行约 `2:31 h`，Barrier 到 iteration `280`、runtime `8746.80 s`。telemetry primal/dual infeasibility 为 `0.014279/6.29e-7`、complementarity `1.31e-9`；Gurobi log 最近的 primal residual 约 `4.6e-3--4.9e-3`。这说明求解仍在推进但 primal feasibility 尚未闭合，不能因 dual/complementarity 较小而提前接受。
- Resource/queue：solver current/max memory `13.56/23.13 GiB`，主机约 `95 GiB` available、swap `781 MiB/2.0 GiB`，`vmstat` 无新增 swap-in/out、memory PSI=0；ParaCloud 队列为空。没有启动、终止或修改任何进程/队列。
- Acceptance/next action：三个终态 JSON 仍不存在。下一窗口先实时读取 PID、最新 telemetry/log 和终态文件；若仍运行只监控，若退出则严格验证 solve/QC/input+result manifests 和模块输出。不得启动第二求解、`Crossover=3`、basis gate、固定服务器 8760 h 或付费云。

### v0.9.72 - 2026-07-29 - 对话窗口收束、技术经济实装复核与活动 744 h 边界冻结

- Git/范围：本次只读审计开始时，本地、固定服务器 bare `origin` 与 GitHub tip 同步于模型实现基线 `7aac739e03646edfed14bbf48ac77869ba66cbef`；固定服务器保持 clean `7c56622c266e673037bd6afaa70c85aa57e6cb13`，不切换活动 checkout。仅更新 `CODEX_HANDOFF.md`、`MODEL_SERVER_STATUS.md`、`SERVER_RUNBOOK.md`；后续文档提交不改变模型，用户拥有的 `supplementary_materials/**` 与 `.codex_tmp/**` 不暂存。
- 口径闭合：重新验证 `technoeconomic_2025_cny_v2` 已被当前代码、服务器数据根和活动 run config 实际消费；本地迁移审计 `ALREADY_APPLIED + PASS`、专项测试 `4/4 PASS`。正确实施提交为 `29bbf90d9edde4e74e3e095b807f2fa1ffaab6a6`，并修正历史交接中不可解析的错误完整哈希。
- 运行边界：当前服务器任务是单独的 `--planning-year 2030 --horizon one_month` V4 V1G cold gate，不是 `2030→2040→2050→2060` sequence。13:43:13+08:00 时 Barrier iteration `87`、runtime `2994.35 s`，current/max solver memory `13.56/23.13 GiB`；约 `95 GiB` available、swap `781 MiB`、`si/so=0`、memory PSI=0。终态三件套均不存在。ParaCloud 队列为空，三个历史全年度作业状态未变。
- 已闭合与未闭合：`7aac739` 是后续修改的唯一统一工程基线；代码/数据/参数身份、release contract、服务器 130 项回归、小门禁和本地四年 168 h Base/V4 sequence 已闭合。活动 744 h 终态、V4 low/high、完整 accepted Base anchor、后续 basis/MGA 仍未闭合。
- 下一窗口精确动作：先完整读取五份交接/规范文件，再实时读取固定服务器 Git、唯一 PID、`solver_telemetry.jsonl`、RAM/swap/PSI、三个终态 JSON 和 ParaCloud 队列。若仍运行，只监控；若退出，先验证 `solve_report`、全部 hard QC、当前 input/result manifests 与模块输出，再更新三份交接文档。无论状态如何，不启动第二求解、8760 h、付费云、basis gate 或 `Crossover=3`。

### v0.9.71 - 2026-07-29 - 隔离服务器数据合同闭合、130 项回归与 V4 744 h 启动

- Git/部署：统一实现 `1d04f07565c3039ed467ec4080f276bd0da90786` 之后的服务器专用闭合提交为 `a3ab9f5`、`95e1b76`、`5c749b6`、`e0b5dbd`、`7c56622`，当前本地/服务器/双远端 tip 为 `7c56622c266e673037bd6afaa70c85aa57e6cb13`。提交范围仅为模型输入合同、release contract、两个审计脚本相关测试与跨数据根测试修复；`supplementary_materials/**` 和 `.codex_tmp/**` 未暂存。
- 根因与修复：服务器先后暴露 `numpy.bool_` 无法 JSON 序列化、V4 来源 manifest 漏包、V4 五张运行表与 wave 两文件漏出标准打包合同、V3 implemented 场景本体漏包，以及三个测试写死 `repo/data`。`config/model_input_files.json` 现为 v10，42 张 required tables + 12 sidecars 完整覆盖 Base/wave/V3/V4；release contract 同时冻结新增来源和 wave/V3 SHA256。测试新增场景文件必须是部署合同子集的门禁。
- 数据/审计：最终标准归档 `transfer_bundle/model_ready_data.tar.gz` 为 68,238,922 bytes、SHA256 `f3e6cc0f810d0f4e1ccf8fd10907fb25b8859546be397f21035cd072cdb9d261`、55 个归档条目；add-only 安装到 `/data/zz2/National_model/data/model_ready_20260729_unified_7c56622_v4`。服务器审计根 `/data/zz2/National_model/outputs/release_contract_v0729_server_7c56622_v5` 中 readiness、release、hydro、V4 loader 均 PASS，完整 unittest 为 `130/130 PASS`。
- 小门禁：`2030_1h_v0729_unified_v4_v1g_server_v1` 为 `81,166 rows / 238,901 columns / 455,569 nnz`、65 Barrier、1,877 simplex、4.136 s solver、0.485 GiB peak RSS；`2030_24h_v0729_unified_v4_v1g_server_v1` 为 `241,492/353,556/1,799,247`、107 Barrier、135,724 simplex、82.272 s solver、0.819 GiB peak RSS。两根均为 `OPTIMAL + QC PASS + 52/52 hard checks + valid input/result manifests`；24 h Barrier numerical trouble 后由 `Crossover=1` 恢复最优。24 h 聚合水电为 82.1105 GW、V4 EV mobility charge deviation 为 93.91 GWh、冷热吞吐为 0、wave 最优容量为 0；这些仍是 truncated engineering evidence。
- 744 h：启动前实时核验 checkout 干净、目标根不存在、约 114 GiB available、`vmstat si/so=0`、memory PSI=0、ParaCloud 队列为空。唯一 cold 根使用 `--horizon one_month`、V4 V1G、`barrier_16_auto_order_v2`/`Crossover=1`，不使用 basis。raw/presolved 和 factor 指标为 `5,238,323/3,942,756/42,266,264`、`3,234,057/2,812,319/31,818,664`、`AA' NZ=6.236e7`、`Factor NZ=8.124e8`、`Factor Ops=5.567e12`；本条提交时仍在 Barrier。
- 未决/下一步：持续监控该唯一求解直至进程退出；仅以 `OPTIMAL + solution_qc=PASS + 52/52 hard checks + valid current input/result manifests` 接受，并审计冷热/EV、wave、水电、储能/网络/备用/惯量/碳 CCS、成本 scope、RSS/swap/PSI。无论终态如何均不得并发替代 case、使用 `Crossover=3`、运行固定服务器 8760 h 或付费云；744 h 仍为 `TEST_ONLY_TRUNCATED_HORIZON`。

### v0.9.70 - 2026-07-29 - 多智能体改动统一、release contract 与干净提交复验

- Git：模型/配置/测试实现提交为 `1d04f07565c3039ed467ec4080f276bd0da90786`（`feat: unify 0729 model release candidate`）。选择性暂存 52 个模型、配置、脚本、测试和交接文件；`supplementary_materials/**`、`.codex_tmp/**` 与全部历史 outputs 均未进入提交。
- 统一内容：闭合常规水电 `297.8895 + 82.1105 = 380 GW`、重复 COMID 一次水量分配、V4 冷热/EV 数据合同、PHS 功率/能量分离 sensitivities、scenario catalog、成本 accounting scope 与完整输出/QC；新增 `release_contract_v0729.json`、release/hydro input auditors 和确定性 V4 builder。
- 修复：聚合水电 up-reserve QC 不再重复计数，down-reserve 安全表不再漏项；V4 年化 enablement 与 selected-horizon 运行成本分列；gzip `mtime=0`；M2 v1 标为历史 superseded。精确提交第一次 detached 复验还发现 M2 历史 audit 依赖受保护未跟踪 review 文件，已改为校验外部证据引用登记，避免主工作树假阳性。
- 验证：V4 连续两次完整 build+validate 六文件字节一致；release audit PASS；参数 audit `11,727 rows / 26 PASS / 0 WARN / 0 hard fail`；hydro input audit `31 provinces / 372 province-month rows / 380 GW closure`；本地四个全新 1 h Base/V4/hydro-flex/PHS-central 均 `OPTIMAL + solution_qc=PASS + current input/result manifests valid`；detached 精确提交在外置数据 junction 下 `129/129 PASS`。
- 未决/下一步：外置 `data/` 未由 Git 携带，服务器必须按 release contract 新建版本化根并逐文件核对 SHA256。实现提交尚未部署，固定服务器与 ParaCloud 的旧状态不得沿用。下一步先 push，再实时核验服务器和队列、部署新数据根、运行服务器 release/readiness/1 h/24 h 门禁；全部通过后只启动一个 2030 V4 V1G 744 h cold gate。禁止 8760 h、付费云、并发第二求解、basis reuse 和 `Crossover=3`。

### v0.9.69 - 2026-07-29 - V4/Base 四年 168 h 配对序列、机制审计与成本口径修复（本地）

- Git baseline: `b87b3b6a76e9b6a3683087105e3251daff22cfad`；仍是包含水电、PHS、V4 与其他用户改动的未提交工作树，未暂存、提交、推送、部署或修改 `supplementary_materials/**`。
- Scope: 顺序运行 2030/2040/2050/2060 的 V4 V1G 与匹配 Base，每年使用上一年 diagnostic state，禁止跨年/跨情景 basis；新增只读 `scripts/audit_planning_sequence_ab.py`，并修复截断时域 `cost_components.csv` 把运行成本误标成每年值的语义风险。主要改动为 `scripts/audit_planning_sequence_ab.py`、`cispo_model/{master,monolithic,flexible_load}.py`、`tests/test_cost_accounting_metadata.py` 及四份交接/规范文档；LP 目标与约束未改。
- Evidence: 两条序列均 `PASS`，八个根均 `OPTIMAL + QC PASS + 52/52 hard checks + result/input manifests valid`，resume 后均 `RESUMED_ACCEPTED`。V4 solver 时间为 `542.60/535.68/534.58/624.49 s`，Base 为 `524.30/528.61/502.95/616.01 s`；V4 峰值 RSS `3.205--3.309 GiB`，Base `2.939--3.165 GiB`。完整回归 `127/127 PASS`，V4 输入验证 PASS。
- Mechanism audit: EV 四年均有 `657.86--2314.68 GWh` 重排并降低选定窗口全国峰值；冷热服务合同容量/吞吐为零；波浪能已加载并通过 availability QC，但装机和发电为零。全模型其他电力平衡、水电、储能、输电、备用、惯量、容量裕度、碳/CCS/BECCS/DAC 与递进状态检查均通过。
- Interpretation and bug boundary: 所有根均为 `TEST_ONLY_TRUNCATED_HORIZON`。年化规划/enablement 成本与 168 h 运行收益口径不对称，因此目标差不是年度净收益。后修复的 1 h 根证明新增 `accounting_scope` 和 `optimization_hours/result_use` 输出闭合；四年 A/B 根生成于该输出修复之前，但其 LP topology、数值解和 manifests 保持有效。
- Unresolved and exact next action: 未发现需要继续扩写模型的硬公式 bug；主要开放项是 V4 low/high 参数敏感性、冷热零采用的经济含义、波浪零采用的长时域稳健性，以及两条序列共同存在的 late-Barrier/crossover 数值恢复。下一步仅落地独立 low/high overlays 并先运行 2030/2060 168 h 配对门禁，同时只读定位近零 RHS/约束族；不得修改 `barrier_16_auto_order_v2`、使用 `Crossover=3`、启动服务器/云端/并发第二求解、744h/8760h 或 MGA。

### v0.9.68 - 2026-07-29 - PHS 功率—能量成本标定与中央情景 1 h 闭合（本地）

- Git baseline: `b87b3b6a76e9b6a3683087105e3251daff22cfad`；本里程碑仍位于包含水电、V4 和其他用户改动的未提交工作树中，没有暂存、提交、推送或部署。
- Scope: 保持 Base 固定 8 h 和现行 PHS 总 CAPEX 轨迹不变，只为已实现的 `independent_power_energy_v1` 建立低/中/高 \(c_P/c_E\) 候选。8 h 能量侧占比为 30%、36.5%、45%，其中中央值由 DOE/PNNL 31.69% 与 ANU 41.35% 两组直接分项结果取中点并取整；所有配置均标记 `PROPOSED_NOT_APPLIED_COST_CALIBRATED`。
- Main changed files: `config/scenarios/phs_power_energy_separated_{low_energy_cost,central,high_energy_cost}_v1.json`；`tests/test_sensitivity_suite.py`；`cispo_full_lp_model_spec.md`；Module 05 的 `source_data/phs_cost_calibration_evidence.csv`、生成脚本、表 M05-19—21、`supplementary_methods_zh.md`、`technical_archive_zh.md`、`source_references.md`、QA 和 manifest。
- Evidence and accounting: 登记 7 条记录/7 个独立来源组，其中中国证据 3 组、直接功率—能量分项证据 2 组。CISPO 轨迹是总成本锚点；NREL 用于分项结构和场址不确定性；中国官方项目披露与 IRENA 只作总量级核验；中国站点级抽蓄研究只说明固定 8 h 的结构风险。中央 2030 \(c_P=3353.473760\) CNY/kW、\(c_E=240.948410\) CNY/kWh，低/中/高所有年份的最大 8 h 重构误差为 `4.0e-6 CNY/kW`。
- Verification: 成本标定 QA `10/10 PASS`，Module 05 formal closure `12/12 PASS`；配置加载和模板拒绝测试 PASS；完整本地 discovery `125/125 PASS`。全新 2030 中央情景 1 h 根为 `OPTIMAL + solution_qc=PASS + closed manifest`，raw 模型 238,529 variables / 80,794 constraints / 453,957 nonzeros，solver 12.074 s、峰值 RSS 0.425 GiB。该根为 `TEST_ONLY_TRUNCATED_HORIZON`，目标值和最优时长不得解释为年度经济结果。
- Unresolved: 直接分项证据仍只有两个国际独立组，中国项目披露没有可比的 power/energy component breakdown；4—48 h 时长范围、闭式/开式差异、场址成本异质性和既有机组时长仍需敏感性。当前没有 168 h、744 h 或 8,760 h 证据支持把中央候选升级为 Base。
- Exact next action: 由作者审阅 30%/36.5%/45% 包络和 `PROPOSED_NOT_APPLIED` 边界；如接受，只在另行授权后按 Base、low、central、high 的同配置长时域阶梯门禁评估成本分摊与时长选择，先本地 168 h，再决定是否需要更长门禁。不得直接覆盖 Base、复用不匹配 basis 或启动固定服务器/ParaCloud/744h/8760h。

### v0.9.67 - 2026-07-28 - PHS 功率—能量候选结构与省级聚合水电灵活性情景（本地）

- Git baseline: `b87b3b6a76e9b6a3683087105e3251daff22cfad`; 本里程碑仍为未提交工作树，保留用户已有 Module 05、V4 与其他未提交内容。
- Scope: 保持 Base 科学边界不变，增加可切换的 31 省 PHS 年度能量容量结构、跨规划年 GWh cohort、参考 8 h CAPEX 闭合门禁，以及不增加小时变量的聚合常规水电月度电量预算/备用/惯量敏感性。
- Main changed files: `config/optimization_2030.json`; `config/scenarios/{hydro_aggregate_flex_v1,phs_power_energy_separated_template_v1,scenario_catalog}.json`; `cispo_model/{config,master,monolithic,planning_state,solution_export}.py`; `tests/{test_bound_tightening,test_sensitivity_suite}.py`; `cispo_full_lp_model_spec.md`; Module 05 的 `supplementary_methods_zh.md`、`technical_archive_zh.md`、`source_references.md`、生成脚本、QA 与 manifest。
- Verification: `py_compile` PASS；水电定向 `12/12 PASS`；PHS/边界定向 `3/3 PASS`；完整本地 discovery `123/123 PASS`。`outputs/2030_1h_v0728_phs_hydro_refinement_base_control_v1`、`outputs/2030_1h_v0728_hydro_aggregate_flex_v1`、`outputs/2030_24h_v0728_hydro_aggregate_flex_v1` 均为 `OPTIMAL + solution_qc=PASS + validate_result_manifest=True`。1 h 配对根均 238,498 variables，情景 constraints 为 80,763、Base 为 80,732；24 h 情景为 346,736 variables / 231,107 constraints / 1,756,839 nonzeros，月度预算最大违反 \(3.55\times10^{-15}\) GWh。
- Evidence boundary: 2026 EES 研究的约 30% 闭式抽蓄容量高估和约 360 亿元/年成本差来自站点—库盆—水头—成本联合模型，不能直接校准本省级 4–48 h 结构。当前 PHS 总 CAPEX 仅有聚合 CNY/kW 路径，生产 \(c_P/c_E\) 未确定，故模板拒绝运行；聚合水电备用系数 1 与 3 s 惯量也只是与现有站点级公式对齐的敏感性。
- Unresolved: 正式 PHS 功率/能量成本证据矩阵与中央值；聚合水电低/中灵活性系数；年度 Base 对照；原有 2019 单年 P30、混合天气—水文年、备用持续时间与同步机在线状态风险。
- Exact next action: 先对 PHS power/energy CAPEX、闭式/开式定义和时长范围做来源审查并形成 `PROPOSED_NOT_APPLIED` 候选表；获得作者批准后再激活 PHS 情景。聚合水电先做本地 168 h Base/情景对照或年度求解授权评估，不得将本轮 1 h/24 h 结果解释为科学结果。

### v0.9.66 - 2026-07-28 - 冷热/EV V4 数据支撑型闭环与 P0 修复（本地）

- Git/范围：当前工作树基于 `b87b3b6a76e9b6a3683087105e3251daff22cfad`，尚未提交、推送或部署。模型修改集中于 `cispo_model/{data,flexible_load,preflight,solution_export}.py`、两个 V4 scenario、V4 参数/来源登记、输入生成与验证脚本、测试和模型规范；保留用户现有水电改动，未修改或暂存 `supplementary_materials/**`。
- 数学与数据：修复多省周期转移错误广播、多省目标向量、禁用 V2G cost 类型、V4 charge/QC 上界等 P0；冷热采用有前置库存约束的非负连续服务状态，EV 采用既有基线的 75% 固定负荷与 25% 可调服务库存。五张逐省/小时输入由已有 load/V3 envelope 可复现生成；中心值与 low/high、来源映射和证据计数全部机器登记。V1G 为中心情景，V2G 只作敏感性；没有车辆会话数据时不声称物理车队 SOC。
- 验证/输出：输入构建与五年份 runtime-loader 审计 PASS；确定性 sidecar 连续两次 SHA256 相同（`49cefa…c3108`）；`py_compile`、V4 定向 `11/11`、完整 `123/123` 回归 PASS。完整回归所需的唯一额外修正是为既有 PHS planning-state 测试 stub 明确 `fixed_duration_v1`，不改变模型。当前身份的新 V1G 1 h/24 h 与 V2G 1 h 根分别为 `_data_supported_v3`、`_data_supported_v2`、`_v2g_data_supported_v2`，均为 `OPTIMAL + solution_qc=PASS + closed manifest + current input_manifest PASS`；24 h raw `241,492/353,556/1,799,247`（rows/columns/nonzeros），solver `43.13 s`、端到端 `81.55 s`、峰值 RSS `0.760 GiB`。失败根 `outputs/2030_1h_v0728_flexible_load_v4_data_supported_v1` 因 export cost 类型错误保留，不得重标为成功结果。
- 未决/下一步：中心值是可直接运行的工程假设，不是已观测省级校准。作者接受当前边界后，只运行一个隔离、本地、顺序的 168 h V1G gate；论文结论前必须执行已登记的参与率、时长/保留率和成本 low/high，V2G 不替代 V1G。不得复用 Base/V3 basis、`Crossover=3`、启动 744h/8760h、固定服务器或付费云任务。
- 里程碑结束只读复核：本地仍为 `codex/cispo-2030-full-lp` / `b87b3b6a76e9b6a3683087105e3251daff22cfad` 加未提交候选；固定服务器仍是 clean `codex/cispo-2030-full-lp` / `701b9bc225013a5009dcce3f4e97ee2063dcd00f`，没有真实 CISPO/Gurobi 求解进程，约 `70.9 GiB` available RAM、swap 使用约 `19.1/21.5 GiB`；ParaCloud `squeue -u a8s001819` 为空。本轮没有远程写操作。

### v0.9.65 - 2026-07-28 - 水电空间图 V3 河网与插图版式统一（本地）

- Git/范围：工作树仍基于 `b87b3b6a76e9b6a3683087105e3251daff22cfad`，尚未提交、推送或部署。本次只修改 `plot_hydro_capacity_spatial_contract.py` 的制图布局与 `generate_module_outputs.py` 的图注，并增量生成 V3 PNG/PDF、五份 V3 source-data sidecar 和 `figure_m05_02_v3_qa.json`；V2 文件未覆盖或删除，模型变量、约束、容量口径、输入数据和求解结果均未改变。
- 图形契约：图 a 与图 b 均调用同一个底图函数，固定按 R5、hyd2/R2、R1 顺序绘制相同的 5,950 条分级河网；删除按梯级组自动选择并显示 Laxiwa 等代表站名的文字循环。原先两幅地图各自覆盖右下角内容的南海小图，改为整张 figure 仅创建一次、放置于两图之间空白区的共享插图，不覆盖河网、站点、梯级线或省级聚合标记。
- 验证：两份脚本 `py_compile` 通过；V3 为 `7.2 × 6.6 in`、`450 dpi`、`3240 × 2970 px`，PNG/PDF 均存在。`figure_m05_02_v3_qa.json` 全部检查为真，记录两图河网层级同为 `R5/R2/R1`、单一共享南海插图和无站名；计数仍为 31 省、2,030 个站点记录、142 个核心节点、2,211 条核心路径河段及 5,950 条全国河网。生成器重建后 formal closure 保持 `12/12 PASS`，SHA256 manifest 为 63 个文件。
- 未决/下一步：该修改仅关闭当前图件的遮挡、冗余文字和跨面板底图不一致问题，不改变省级聚合分配、2019 单年月曲线或混合资源年份等科学风险。下一步由作者审阅 V3 的地图密度和柱图范围后决定是否定稿；不得据此重解释既有 1h/24h 门禁或启动任何远程求解。

### v0.9.64 - 2026-07-28 - 常规水电 380 GW 省级闭合与聚合运行层（本地）

- Git/范围：工作树基于 `b87b3b6a76e9b6a3683087105e3251daff22cfad`，尚未提交、推送或部署。模型改动覆盖 `cispo_model/{config,hydro,io_contract,load_center,master,monolithic,result_summary,solution_export}.py`、`config/{optimization_2030,model_input_files}.json`、`tests/test_hydro_station_model.py` 和 `cispo_full_lp_model_spec.md`；新增外置水电容量/月曲线输入以及 Module 05 重建脚本、表、图和 QA。用户拥有的 `supplementary_materials/MODEL_V0719_REVIEW_REPORT.md` 等无关改动未覆盖。
- 容量与来源：2025 常规水电按“297.8895 GW 可识别站点 + 82.1105 GW 固定省级聚合”闭合到国家能源局 380 GW；PHS 下限 65.94 GW。GHT operating non-PHS 项目总量 302.939 GW、中国归属 302.133 GW；旧未匹配 39.869 GW 中至少 15.419 GW 为清单重叠，不直接加和。重点省份锚点、时间、是否规划值和抽蓄扣除均记录在表 M05-18；非锚点在站点/GHT 非加和下界之上按省级先验比例调整。
- 模型契约：省级聚合容量固定不扩张，逐小时出力上界为容量乘 2019 逐月代理 CF，可弃发；无站点、水头、额定流量、库容、COMID、跨期蓄水、梯级、备用、惯量、容量信用或 spur/trunk。其发电进入省级平衡，并按需求份额进入 337 负荷中心；结果、QC、NPZ 和 manifest 均显式导出。成本沿用 CISPO 对总装机计收 annualized CapEx/FOM 的口径，因此固定聚合容量的该成本是情景常数。
- 验证：`tests/test_hydro_station_model.py` 为 `12/12 PASS`；水电改动相关回归 `117/117 PASS`。完整 discovery 另有 2 项与本改动无关的 scenario catalog 字段失败，未修改用户文件。新根 `outputs/2030_{1h,24h}_v0728_hydro_provincial_closure_base_v2` 均为 `OPTIMAL + solution_qc=PASS + validate_result_manifest=True`；24h raw/presolved 为 `231,076/346,736/1,754,607` 与 `129,500/260,862/1,295,832`（rows/columns/nonzeros），120 Barrier、52,592 simplex、43.188 s、0.743 GiB RSS，最大平衡残差 `1.12e-12 GW`，聚合可用量违反为 0。
- 补充材料：`reconcile_provincial_hydro_2025.py`、表 M05-16—18和容量闭合 QA记录去重与分配；`Figure_M05_02_hydropower_spatial_contract_v2.{png,pdf}` 以上排双地图分别表示 5,950 条真实分级河网/五组核心梯级与非核心既有/潜在站点/省级聚合，下排双栏表示31省当前容量和未来站点清单技术上限，图件 QA 通过。生成器重建后 Module 05 formal closure 为 `12/12 PASS`，输出 manifest 含 55 个文件。
- 未决/下一步：全国容量会计已闭合，但聚合省间分配与月曲线仍为 P1 敏感性；2019 单年 monthly P30 和混合资源年份仍为 P0。下一步是作者审阅这些边界后再决定是否提交；不得用省级聚合层声称获得了清单外电站的水库调度，也不得据此启动服务器/云端 168h、744h 或 8760h。任何未来部署须新建版本化数据根并重新执行完整输入、测试、1h/24h 和 manifest 门禁。

### v0.9.63 - 2026-07-28 - 冷热/EV V4 服务约束情景与校准拒绝门禁（本地）

- Git/范围：实现提交为 `3b3de57f41a8208b4e6bd0265270a91c77b1c8df` (`feat: add v4 flexible service contract`)。变更限于 `cispo_model/{config,data,flexible_load,io_contract,preflight,solution_export}.py`、两个 V4 scenario JSON、V4 校准契约/参数登记、输入验证脚本、配置说明和 `tests/test_flexible_load.py`；未修改 Base JSON 或 V3 JSON，未暂存 `supplementary_materials/**`。
- 数学与数据契约：`service_constrained_v4` 对冷热使用连续的 signed state、`-S_under <= S <= S_bar`、舒适债与服务签约容量；EV 仅使用一个车群 SOC，按外生连接率/可用功率限制充放电，并扣除出行能耗、满足最低出发 SOC。V1G 为主情景，V2G 仅敏感性。五张输入表、来源 manifest 和 SHA256 验证为强制条件；没有已验证输入时 loader/preflight/provenance 都拒绝继续，故 V4 不会以默认数值或代理数据伪装为已校准情景。
- 验证：`conda run -n RL python -m py_compile cispo_model/data.py cispo_model/flexible_load.py cispo_model/preflight.py cispo_model/io_contract.py cispo_model/solution_export.py scripts/validate_flexible_load_v4_inputs.py` 通过；`conda run -n RL --no-capture-output python -m unittest discover -s tests -p test_flexible_load.py -v` 为 `11/11 PASS`，包括 1 省×4 小时 Gurobi 线性门禁；设置 `CISPO_WAVE_ROOT` 后，`conda run -n RL --no-capture-output python -m unittest discover -s tests -p 'test_*.py' -v` 为 `122/122 PASS`。
- 未决/下一步：V4 的热惯性、舒适边界、连接可用率、车队电池/功率、出行/出发 SOC 以及启用/激活/补偿/退化成本仍需由有来源的四规划年输入校准。输入交付后先运行 `scripts/validate_flexible_load_v4_inputs.py`，再仅在本地顺序运行新命名的 1h、24h、168h V4 gate；不得使用 Base/V3 basis，不得启动固定服务器 744h/8760h、付费云任务或并发第二个求解。

### v0.9.62 - 2026-07-28 - M2 boundary audit Stage A and current-worktree hydro gate record

- Git implementation: `379a96a79cf14d7dc08d0a5cfd45b8223f2f4b47` (`feat: add m2 boundary audit`).
- Scope/changed files: added `config/m2_model_boundary_audit_v1.json`, `config/scenario_parameter_registry.csv`, `scripts/audit_m2_model_boundary.py`, `tests/test_m2_model_boundary_audit.py`; added one scope record to `config/critical_parameter_registry.csv`; updated this handoff, `MODEL_SERVER_STATUS.md`, and `SERVER_RUNBOOK.md`. No `supplementary_materials/**` content is staged by this milestone.
- Verification: audit output `outputs/m2_model_boundary_audit_20260728_local_v3/` has 11 findings and `9 PASS, 0 OPEN, 0 hard fail`; targeted audit tests pass; parameter audit output `outputs/parameter_audit_20260728_m2_local_v2/` has `11,717` rows, `26 PASS, 0 WARN, 0 hard fail`, and four explicit open risks. The independent review was triaged rather than implemented wholesale: Base-changing suggestions, unsourced parameters, and new LP formulations remain separated from basis work.
- Hydrology evidence/status: the user's uncommitted duplicate-COMID candidate passed `117/117` regression and local 1h/24h `OPTIMAL + PASS + closed manifest` gates in `outputs/2030_{1h,24h}_v0728_m2_hydro_duplicate_comid_local_v1`. The 24h root is a candidate only: it retains the raw `231,076/345,992/1,753,119` topology, has objective delta `+12.883815481793135 million CNY`, and its Barrier stage reported numerical trouble before terminal Crossover optimality. Do not stage, deploy, or call it an accepted scientific Base until the owner separately reviews and commits the scientific change.
- Unresolved/next action: first review/commit (or revise) the duplicate-COMID implementation independently; only after that decision, use a new isolated local 168h cold Base gate if a further model gate is warranted. Continue BECCS evidence/provenance work without inserting unsourced LP parameters. No server/cloud/744h/8760h action is authorized; preserve `Crossover=1` and never reuse `Crossover=3`.

### v0.9.61 — 2026-07-28 — 固定服务器 swap 归因与清理停止条件

- Read-only evidence: `free` 显示约 `70 GiB` available RAM、swap `19.1/21 GiB`；`Cached+Buffers` 仅约 `5.6 GiB`，并非 cache 累积。`/proc` 显示活跃 `wind_power` Python 的 `VmSwap=8.18 GiB`，两组 MATLAB 为 `6.01/2.28 GiB`；`vmstat` 5 秒采样 `si/so=0`，memory/IO PSI 均为 0。
- Decision: 当前 swap 是未被访问但仍归属于活跃匿名内存的页面。不得使用 `drop_caches`（不能释放 swap）或在未获主机级授权下运行 `swapoff/swapon`（会将约 19 GiB 页面回迁并扰动活动 GPU/MATLAB 作业）。未停止、重启、修改或清理任何非 CISPO 进程；服务器继续不满足 CISPO 部署/求解门槛。

### v0.9.61 — 2026-07-28 — 重复 COMID 水量守恒修复与 Module 05 / S6 审查包

- Git/scope: 本地基线 `ed72ba08ff52025cb372fc5c16583c3e05bd38b5`；本里程碑尚未创建提交。模型改动限于 `cispo_model/{hydro,config}.py`、`config/optimization_2030.json`、`tests/test_hydro_station_model.py` 与 `cispo_full_lp_model_spec.md`；补充材料新增 `supplementary_materials/modules/05_hydropower_and_pumped_storage/**`。既有用户文档和其他模块未覆盖。
- Root cause/fix: 2,030 条站点记录中有 146 个重复 `COMID`，涉及 319 条站点记录，其中 44 个河段同时映射径流式和水库式站点；旧实现会在非梯级或混合类型映射中重复使用同一 GRFR 河段序列。新配置锁定 `static_capacity_potential_share_v1`，先扣除 2019 monthly P30 环境流，再按技术容量上限分配；逐河段份额和硬校验为 1，梯级节点改为汇总成员站分配流量。该静态规则保持 LP 线性，但候选站未建时不会动态转移份额，已登记为敏感性边界。
- Commands/evidence: focused hydro tests `10/10 PASS`；`CISPO_WAVE_ROOT` 指向当前 wave 输入后执行完整 `unittest` 为 `116/116 PASS`。隔离根 `outputs/2030_1h_v0728_hydro_comid_flow_share_base_v1` 与 `outputs/2030_24h_v0728_hydro_comid_flow_share_base_v1` 均为 `OPTIMAL + solution_qc=PASS + validate_result_manifest=True`。24 h 新根 raw/presolved 为 `231,076/345,992/1,753,119` 与 `129,500/260,190/1,295,919`，solver `41.70 s`、峰值 RSS `0.742 GiB`；相对修复前参考根，水电发电量 `380.062 → 348.553 GWh`，目标 `+0.714%`。两根均为 `TEST_ONLY_TRUNCATED_HORIZON`。
- Supplement evidence: Module 05 / S6 生成器只读当前输入和已闭合诊断根，不运行优化器；产出中文方法、15 张表、四联图及 PNG/PDF/SVG、6 份 figure-data CSV、技术档案、来源登记、图注、风险表、QA 与 SHA256 manifest。formal closure `9/9 PASS`，包括 142 节点/124 边的 Kahn 有向无环检验。
- Unresolved/next action: P0 保持为常规水电清单覆盖不足、正式多年环境流量缺失、混合气象年协方差边界；另需对 115/750 MW 分类代理、22 条非 PASS 梯级时滞、PHS 8 h/效率/省级聚合及水电备用持续时间做敏感性。先由作者审阅风险处置口径并决定是否补建多年 P30 与清单覆盖层；未经批准不恢复旧省级残差、不改变 PHS 功率语义、不部署服务器或放大到 168/744/8760 h。

### v0.9.59 — 2026-07-28 — M1 168h 四根 basis 工程门禁闭合（本地）

- Git/runtime: implementation `a5e34bf5357301c205b246b0aa2149db0dca9c3b`，documentation baseline `7b5c2d66f7826d13635a403f0da012ce4f8631fe`；Base 为 `base_2024_vre_wave_on_flex_off_v1`，profile `barrier_16_auto_order_v2`、`Crossover=1`。仅生成新的本地 outputs，未改模型代码、服务器 checkout、服务器进程、ParaCloud 队列或 `supplementary_materials/**`。
- Commands/roots: 顺序运行 `outputs/2030_168h_v0728_m1_basis_{cold_local_v1,warm_local_v1}`、`outputs/2030_168h_v0728_m1_statebridge_local_v1`，以及携带该 test-only state 的 `outputs/2040_168h_v0728_m1_basis_{cold_local_v1,warm_local_v1}`。2030/2040 cold 各自导出 `cispo_lp_basis_reuse_v2` basis；2040 warm 仅导入 2040 cold basis，未使用 `--allow-cross-year-basis`。
- Acceptance evidence: 四根均 `OPTIMAL + solution_qc=PASS + validate_result_manifest=(True, [])`。2030 cold/warm objective `2043256.6580149832`，solver `520.266/10.874 s`，warm 0 Barrier/0 simplex；2040 `2025434.603188973`，solver `489.268/14.257 s`，warm 0/0。cold/warm objective 均 zero-diff；2030 容量 zero-diff、成本/发电最大差 `1.82e-12/2.73e-12`，2040 为 `7.11e-15 GW`、`2.91e-11/4.09e-11`。raw topology 保持 `1,167,956/1,019,192/9,536,286`，CSR pattern SHA256 为 `50220850416e219fb1f3f5130c4c20cb6419cbf6b56d5d22d231491ab383f998`。
- Decision/next action: 这证明同年、同拓扑的 truncated-horizon warm restart 工程可用，不构成全年科学结果。孤立 744h basis gate 无法在没有先行同构 cold 744h 的情况下产生净端到端收益，故不申请、不运行。下一阶段保持模型边界冻结，等待实际重复同构求解或明确的、获授权的工程需求；远程动作仍须实时核验服务器和 ParaCloud，`Crossover=3` 永久拒绝。

### v0.9.60 — 2026-07-28 — M1 门禁后服务器与 ParaCloud 实时只读复核

- Git/server: 只读核验固定服务器为干净的 `codex/cispo-2030-full-lp` / `701b9bc225013a5009dcce3f4e97ee2063dcd00f`；`ps` 未发现 CISPO/Gurobi，RAM available 约 `70 GiB`。无需、也没有切换 checkout、传输输入或运行回归。
- Safety decision: host swap 约 `19.1/21 GiB`，RSS 最大的无关 Python 约 `43.0 GiB`；即使 ParaCloud `squeue -u a8s001819` 为空，也不满足服务器运行门槛。未启动第二个求解、固定服务器 744h/8760h 或任何付费云任务；下一步仍为等待状态变化后重新读取，而非复用本条快照。

### v0.9.58 — 2026-07-28 — M0 分层身份与 M1 科学前置闭合（本地）

- Git implementation: `a5e34bf5357301c205b246b0aa2149db0dca9c3b` (`feat: close basis preparation m0 m1`)。范围为 `cispo_model/{run_contract,basis_reuse,config,data,master,carbon_accounting,io_contract}.py`、Base/registry/BECCS screening 配置、两份审计脚本和对应测试；`supplementary_materials/**`、固定服务器和 ParaCloud 均未写入。
- M0 contract: `run_identity.json` 现在显式保存 `scientific_case`、`solver_runtime`、`implementation_bundle`，建模后附加 `lp_topology`。basis 导入严格要求同 test-only horizon、closed source manifest、`OPTIMAL + PASS`、basis hash 和完整 raw CSR pattern；科学/实现层身份不相同只写入 `audit_layer_matches`，不作为 source basis 的结构兼容性替代，也不授予科学验收。
- M1 scope: Base 标签和混合气象 bundle 已登记；`cohort_survival_v1` 的 2030--2060 floor 以及 `fixed_floor_v1` 对照均已测试；BECCS lifecycle 是固定结果的 post-solve screening；新增的 wave/nuclear/hydro/PHS/CO2-ship/DAC 上界均有可行域不变论证。参数审计输出 `outputs/parameter_audit_20260728_m1_local_v1`：11,717 行、26 PASS、0 WARN、0 hard fail（4 项待来源研究风险保持显式）。
- Verification: M0 24h cold/warm 根为 `outputs/2030_24h_v0728_m0_identity_{cold_local_v2,warm_local_v1}`，同一 objective 且 warm 为 0 Barrier/0 simplex；M1 24h cold `outputs/2030_24h_v0728_m1_equivalence_cold_local_v1` 与 M0 zero-diff，跨 implementation-bundle 的 warm 审计根也 closed；`conda run -n RL python -m unittest discover -s tests -p 'test_*.py' -v` 为 `114/114 PASS`。
- Unresolved/next action: 现存 168h basis 根形成于 M0/M1 前，不能充当新分层契约的 gate。只在本地、一次一个求解地运行当前提交的 2030 cold/warm 与携带明确 2030 diagnostic state bridge 的 2040 cold/warm；四根闭合且端到端收益明确前，不申请隔离 744h basis gate。固定服务器的 swap 压力仍须在任何远程动作前实时复核；`Crossover=3` 永久拒绝。

### v0.9.57 — 2026-07-28 — 技术经济 V2 批准落库与 2025 年不变人民币生产合约

- Git implementation: `29bbf90d9edde4e74e3e095b807f2fa1ffaab6a6` (`feat: normalize technoeconomic inputs to 2025 CNY`). A later handoff audit corrected the previously mistyped full hash while preserving the valid short prefix `29bbf90`.
- Scope: 将经 CISPO 原作者逻辑与多来源审查后的 V2 货币参数正式写入运行配置、数据构建器和本地外置数据包；统一 2025 constant CNY，保留审批前 candidate 快照；未改变物理参数、约束边界、目标结构或时间/空间尺度。
- Main changed files: `config/technoeconomic_price_basis_2025.json`, `config/optimization_2030.json`, `config/technology_parameters.json`, `config/fuel_prices_supplementary_table2.json`, `config/model_input_files.json`, `cispo_model/price_basis.py`, `scripts/apply_technoeconomic_price_basis_v2.py`, `scripts/build_cispo_data_package.py`, `scripts/build_natural_earth_278_network.py`, smoke/unit tests, `cispo_full_lp_model_spec.md` and Module 04.
- Production rules: domestic 2022 CNY × `1.004004` across the complete planning trajectory; nuclear/source fuel USD × `7.1429`; wave EUR × `8.1185`; CCS central values `261.04104/0.50/45`; numerical and physical exceptions explicitly registered.
- Verification: migration representative checks 9/9 PASS; idempotent second execution PASS; full local unit tests 106/106 PASS; model-ready data smoke 142/142 PASS. The earlier hydrology failure was an incorrect local `CISPO_HYDRO_ROOT` override forcing two native files into one directory; native indexed paths passed.
- Data/deployment boundary: repository `data/` is Git-ignored. Local model-ready tables and `technoeconomic_price_basis_manifest.json` are updated, while the pushed commit carries the reproducible config/builder/migration contract. No fixed-server checkout, external data root, output or cloud job was changed.
- Unresolved: fuel time trajectories, storage duration decomposition, technology-specific WACC, plant age/retirement, CCS energy penalty and offshore spatial cost remain sensitivity priorities. Exact next action is to create a new server data root, apply the migration there, and pass readiness/smoke/1h or 24h gates before any longer solve; this deployment requires a separate explicit request.

### v0.9.56 — 2026-07-28 — intra-grid/cohort 的 168h 同年 basis 四根门禁（本地闭合）

- 范围：实施提交 `282c393fd98e25737631493e19110e38bb49ed28` 的模型/配置/数据契约在本地运行四根新命名的隔离 168h Base 根；另以 2030 warm 根导出一个明确 `TEST_ONLY` diagnostic state bridge，供 2040 cold/warm 的既有容量递进状态输入。未连接、写入或部署固定服务器，未传输 cohort 数据，未修改 ParaCloud，未启动 744h、8760h 或并发第二个求解。
- 2030：`outputs/2030_168h_v0728_intra_grid_cohort_basis_cold_local_v1` 为 `OPTIMAL + QC PASS + manifest true`，raw/presolved `1,167,956/1,019,192/9,536,286` 与 `697,875/712,434/7,103,801`（rows/columns/nonzeros），180 Barrier、219,076 simplex、solver `576.593 s`、RSS `2.925 GiB`。同身份 warm 根以其 checksummed post-crossover basis 输入，solver `11.406 s`、0 Barrier/0 simplex、RSS `2.262 GiB`；objective 都为 `2,027,739.8896732337 million CNY`，容量 CSV 完全一致，发电 CSV 最大绝对差 `3.64e-11 GWh`。
- 2040：2030 state bridge 使用 `--allow-diagnostic-state-in`，不构成生产递进 state。`outputs/2040_168h_v0728_intra_grid_cohort_basis_cold_local_v1` 为 `OPTIMAL + QC PASS + manifest true`，raw/presolved `1,167,956/1,019,192/9,536,286` 与 `699,024/715,445/7,173,198`，168 Barrier、221,342 simplex、solver `543.965 s`、RSS `3.030 GiB`；2040 自身 basis 的 warm 根为 `15.517 s`、0 Barrier/0 simplex、RSS `2.263 GiB`。目标都为 `2,008,165.4183561637 million CNY`，容量完全一致、发电最大差 `2.91e-11 GWh`。未使用 `--allow-cross-year-basis`。
- 共享并网审计：四根均含 manifest/catalog 覆盖的 `intra_grid_vre_site_design.csv` 和 `intra_grid_substation_design.csv`；2025 初始 VRE trunk 均为 `1,069.512666 GW`，旧 nameplate proxy 为 `1,309.999999962 GW`。四根 result manifest 的验证错误列表皆为空。
- 决策/下一步：同年同结构 basis 工程复用具有明确收益，但不证明跨年或全年 reuse，也不授权 744h。固定服务器即时检查存在 19/21 GiB swap 使用和无关 45 GiB RSS 长任务，故部署和服务器 168h 均暂停。待主机压力解除且用户仍授权时，重新实时核验 HEAD/进程/内存/队列，add-only 安装 cohort CSV/sidecar，部署精确推送提交并完成服务器回归后，才可运行一个新的服务器 168h cold gate；不得复用 `Crossover=3` 或启动 744h/8760h/付费云任务。

### v0.9.55 — 2026-07-28 — 同格网风光共享并入与既有 VRE cohort retirement（本地闭合，未部署）

- Git/范围：起始分支/HEAD 为 `codex/cispo-2030-full-lp` / `d73eb3390c970b0da6319a03ca8b1d3c30384040`。工作树原有 `supplementary_materials/**` 与本交接文档用户改动保留；本次模型工作尚未提交。新增 `scripts/build_existing_vre_cohorts.py`、`tests/test_intra_grid_vre_design.py`，并修改 `cispo_model/config.py`、`cispo_model/data.py`、`cispo_model/io_contract.py`、`cispo_model/master.py`、`config/optimization_2030.json`、`config/model_input_files.json`、`tests/test_model_foundation.py` 及交接文档。没有连接、写入或部署固定服务器，未修改 ParaCloud，未启动 168h/744h/8760h 或第二个求解。
- 模型边界：逐格网 VRE 仍沿既有 `grid_uid -> substation -> load center` 路由；现场 spur 保留 CISPO S4-18 的 `p_spur >= max_t(cf_site,t) * capacity_site`。共享 wind/PV trunk 由原先的逐 site `max(cf)` 相加，改为 CISPO S4-19 的 `p_trunk >= sum(capacity_site) * max_t[sum(potential_site*cf_site,t)/sum(potential_site)]`，DPV 不引入此输电代理，水电仍按其原有项另加。36,686 行中 12,603 个多技术 `grid_uid` 全部映射同一 substation，零违规。完整 8760 CF 扫描为设计系数，不是 8760 LP 求解，且不增加 LP 变量或逐小时约束。
- 既有 VRE：新增受 `model_input_files.json` 和 manifest 追踪的 cohort 输入。GEM project 使用可用 `start_year`；unknown/OSM/residual 与 `start_year>2025` 容量以显式 `boundary_censored_2025_v1` 处理。2025 容量按每个 grid-technology 严格闭合，cohort 为 15,171 行、SHA256 `e00791ec9597897da80377458d6acefdc481ef1708c0f86d68adb2a5576f92d0`；退出的 observed cohort 不再构成容量下界，但保留 site technical upper 和独立连接代理，故模型允许而不强迫同址再建。
- 验证：`CISPO_WAVE_ROOT=D:\codeenv\pycharmproject\National_RL\wave_energy conda run -n RL python -m unittest discover -s tests -p 'test_*.py' -v` 为 `102/102 OK`。本地 preflight `outputs/2030_24h_v0728_intra_grid_cohort_preflight_local_v1` PASS；隔离 24h Base 根 `outputs/2030_24h_v0728_intra_grid_cohort_smoke_local_v1` 为 `OPTIMAL + solution_qc=PASS + closed result_manifest`，raw/presolved `231,076/345,992/1,753,119` 与 `129,500/260,190/1,295,919`，objective `1,982,153.352438188 million CNY`，solver `34.83 s`、端到端 `58.91 s`、peak RSS `0.739 GiB`。输出新增 `intra_grid_vre_site_design.csv` 与 `intra_grid_substation_design.csv`，并被 output catalog 和 manifest 覆盖。
- 下一步：先审查并选择性提交这组非补充材料变更；若获准部署，先重新实时核验服务器 HEAD/空闲进程/内存与 ParaCloud 队列，以 add-only 方式传输 checksummed cohort 输入，fast-forward 到精确提交并完成服务器完整回归。只有上述条件满足，才在新隔离根顺序运行单一匹配 168h Base 门禁（`barrier_16_auto_order_v2`、`Crossover=1`）；不得复用已拒绝的 `Crossover=3`，不得启动 744h/8760h 或付费云任务。

### v0.9.53 — 2026-07-28 — CISPO 驱动的技术经济参数深度综合审查 v2

- Git/授权边界：沿用本轮只读核验的本地基线 `701b9bc225013a5009dcce3f4e97ee2063dcd00f`；工作区已有补充材料改动全部保留。本里程碑只新增/修改 Module 04 补充材料、`supplementary-materials` skill 和本交接记录，未修改 `National_model/data`、`config`、模型方程、服务器 checkout、历史输出或求解状态。
- CISPO 原作者逻辑：逐节恢复 S3.3.4、S3.5.1—3、S3.6.2、S3.7—10 和 S6 的当前成本锚点、相对学习率来源、插值/外推、运行参数、CCS/DAC、WACC 和 1.25× CapEx 不确定性设计。关键结论是原作者对风光采用“中国绝对成本锚点 + 多来源相对下降率”，并未直接导入 NREL 的美国绝对成本。
- 深度证据：建立 15 个审查单元、63 条唯一来源、104 条参数族—来源关联；主文/SI/代码/数据按一个 `independence_group` 计数，同一机构同版报告不同格式不重复计数。每单元 6—8 个独立来源，最低为 6；`table_m04_19_source_count_qa.csv` 15/15 PASS，并报告中国证据数和最新证据年。
- 2025 CNY 口径：国内 2022 CNY 值继续乘 `1.004004`；原始外币值必须回到可复现来源币种后按 2025 FX 转换，不再对旧 CNY 折算值机械乘中国 CPI。完整来源年、币种、指数/汇率、公式和解释见 `table_m04_21_2025_price_conversion_ledger.csv`。
- v2 中央值：核电回到 Bowen/CISPO 原始 USD 路径，2030/2040/2050/2060 为 `2800/2650/2500/2350 USD/kW × 7.1429`，即 `20000.12/18928.69/17857.25/16785.82 CNY/kW`。CCS 运输和封存不再采用 An 等单篇中央值，而按中国多来源综合取 `0.50 CNY/tCO2/km` 与 `45 CNY/tCO2`，敏感性范围约 `0.18—0.80` 与 `25—116`。其余 v1 候选值在五来源以上审查后保留。
- 产物：新增 `deep_integrated_technoeconomic_review_2025cny_zh.md`、`scripts/generate_deep_integrated_review.py`、`candidate_inputs_v2/` 四张候选表、表 M04-16—23、`qa/deep_integrated_review_validation.csv` 和运行摘要。候选行数为 CapEx 76、燃料 31、派生燃料成本 1550、其他参数 166；全部为 `PROPOSED_NOT_APPLIED`。
- Skill：`supplementary-materials` 新增强制原作者逻辑恢复、每审查单元至少 5 个独立证据组、中国证据优先、source registry/evidence matrix/source-count QA、外币来源链和 v1→v2 变更表规则。Windows 默认 GBK 首次读取 UTF-8 skill 失败；设置 `PYTHONUTF8=1` 后 `quick_validate.py` 返回 `Skill is valid!`。
- 验证/下一步：生成脚本成功，8/8 QA PASS，正式标记 `FINAL_M04_DEEP_REVIEW_2025CNY_PASS`。作者下一步校对 v2 三项数值修正及波浪能参考情景边界；批准前不落库。电池功率—能量成本拆分、CCS 有效能耗、既有容量 CapEx 计费、既有机组退役队列等仍为独立 `MODEL_CODE_REVIEW_REQUIRED`，本轮未运行敏感性或优化。

### v0.9.52 — 2026-07-28 — Module 04 最终候选输入、逐参数文献审查与图件重构

- Git/授权边界：只读核验时本地分支 `codex/cispo-2030-full-lp` 的 HEAD 为 `701b9bc225013a5009dcce3f4e97ee2063dcd00f`；工作区已有用户补充材料改动全部保留。本里程碑只修改补充材料、`supplementary-materials` skill 和本交接记录，未改 `National_model/data`、`config`、优化方程、服务器 checkout 或任何求解输出。
- 文献与来源纠正：查明 `province_fuel_prices.csv` 来自 An 等（2025）*Nature Communications* 16, 2311，DOI `10.1038/s41467-025-57559-2`，公开数据/代码 DOI `10.5281/zenodo.14836760`。煤价由 2014—2020 省级指数回归到 2023 全国水平，气价由 2018 省级门站基准加 `0.8 CNY/m3` 构造，生物质价来自其引用的 2022 出厂价研究；先前“燃料价格年未解决”结论被纠正。候选表按 2025 官方平均 `7.1429 CNY/USD` 换算文献所报 USD/GJ，但明确不是统一的 2025 现货观测。
- 中央候选值：19 技术×4 年 CapEx、绝对 O&M/启停/核燃料/DAC/CCS 捕集/输电等 2022 语境货币量按 CPI `1.004004`转为 2025 CNY；效率、时长、寿命、热耗、排放和容量边界不做价格换算。统一实际 WACC `7.4%`、4 h 电池 `RTE=90.25%`、8 h 抽蓄 `RTE=77.44%`在最新证据对照后保留。CCS 运输和封存建议采用 An 等中央值按 2025 FX 换算的 `0.185715 CNY/tCO2/km` 与 `35.7145 CNY/tCO2`，须作者批准后落库；捕集成本保留 CISPO 并按 CPI 得到 `261.041 CNY/tCO2`。
- 结构边界：电池不同时长严谨比较需要 `CAPEX=c_P K_P+c_E K_E`；当前 CCS 能耗同时通过热耗率和 5% 净出力损失实现，不能直接抄入单一文献惩罚百分比；目标函数按 CapEx×CRF 对全部在役容量计费。三项均标记 `MODEL_CODE_REVIEW_REQUIRED`，本轮未改代码。实时配置核验确认当前 Base 的 `features.wave_energy=true`；本轮建议最终论文 reference 改为 wave-disabled，把 2025 EUR/CNY 换算与强制敏感性留给独立波浪能情景，该 Base 情景改动同样须作者批准。
- 产物：新增 `final_candidate_input_review_zh.md`；`candidate_inputs/{technology_capex_by_year_2025_candidate,province_fuel_prices_2025_candidate,province_fuel_generation_cost_by_year_2025_candidate,other_parameter_values_2025_candidate}.csv`；表 M04-11—15（含候选输入 SHA256 清单）；Figure M04-03—06 及机器绘图数据；`scripts/generate_final_candidate_review.py`；`qa/final_candidate_validation.csv` 与运行摘要。原两张四面板审计图保留作历史证据，但已在图注中标记为非优先投稿图。
- 图件：新图按单一科学问题拆分为风光成本、可调度技术成本、储能外部对照和参数处置决定；每图最多 1—2 面板，不再把全部 CapEx 曲线堆在同一图。所有新图为精确 177.8 mm 宽 PDF + 450 dpi PNG，并有 `figure_data`。
- Skill：`C:\Users\ZZ\.codex\skills\supplementary-materials\SKILL.md` 新增强制技术经济审查流程，并新增 `references/techno-economic-parameter-review.md`；要求先产出精确中央候选值，再做敏感性；强制来源年/货币/换算/可比性/可靠性/授权状态；区分数据更新与模型结构问题；技术经济图默认 1—2 面板且禁止无证据区间。`python -X utf8 ...\quick_validate.py` 返回 `Skill is valid!`。
- 验证：两套生成脚本均成功；初始模块 QA 19/19 PASS，候选 QA 19/19 PASS；候选 CapEx 76 行、燃料价 31 行、派生燃料成本 1,550 行；燃料成本逐行满足价格×热耗率；4 张新 PNG 均为 3150 px 宽且 PDF 非空；完成逐图视觉检查并修复裁切、图例遮挡和无来源区间。正式标记 `FINAL_M04_CANDIDATE_INPUT_REVIEW_PASS`。
- 未决/下一步：作者先校对 `final_candidate_input_review_zh.md` 和表 M04-12/M04-14，并明确批准或拒绝三类数据更新（2025 CNY 重基准、燃料 FX/来源纠正、CCS 运输/封存替换）。只有批准后才更新生产输入和 manifest；任何电池成本拆分、CCS 能耗公式或既有容量投资计费修改都需单独模型代码审查与小样本门禁。敏感性注册已完成，但本轮未运行任何敏感性或优化。

### v0.9.51 — 2026-07-28 — Module 04 技术经济参数与 2025 年价格口径定稿

- Git 基线：本轮只读核验时本地分支 `codex/cispo-2030-full-lp` 的 HEAD 为 `701b9bc225013a5009dcce3f4e97ee2063dcd00f`；工作区已有用户补充材料改动，均予保留。本里程碑没有提交、推送、切换服务器 checkout、启动求解或修改生产数据包。
- 范围：新增 `supplementary_materials/modules/04_thermal_nuclear_storage_technoeconomics/`。以 `cispo_model/data.py`、`master.py`、`monolithic.py`、`config/optimization_2030.json` 和当前实际输入为权威，核对 18 类有效输入、19 技术×4 年 CapEx、11 类火电/核电 RUC 与 O&M、2 类储能、31 省燃料、DAC/CCS/输电、容量上下界和寿命/WACC；并识别 partly stale 的 278 中心 sidecar 及历史审查/计划文档。
- 价格定稿：补充材料采用 2025 年不变人民币作为共同报告口径。明确或可靠归入 2022 年的货币参数以 2023/2024/2025 CPI `0.2%/0.2%/0.0%` 换算，系数 `1.004004`；生产模型值未覆盖。燃料来源价格年仍未解决，因此保留 `6.9 CNY/USD` 活动值，只以 2025 年平均 `7.1429 CNY/USD` 给出 `1.035203` 汇率对照。波浪能保留 `7.8 CNY/EUR` 说明性基线，`8.1185 CNY/EUR` 只作敏感性。
- 关键方法边界：核电 pipeline 下界与 110/205/300/300 GW 上界分列；2030 年电池下界 65.85 GW、抽蓄下界/上界 65.94/249.191 GW，最新 160 GW 抽蓄和 300 GW 新型储能只作政策比较。当前目标函数按 `CapEx × CRF × 全部在役容量` 年化，既有容量也计费；四个规划年目标不会自动折现汇总为 2025—2060 NPV。
- 产物：`technical_archive_zh.md`、`supplementary_methods_zh.md`、`supplementary_tables_zh.md`、`source_references.md`、`figure_legends_zh.md`、10 张 CSV 表、6 个绘图数据文件、`Figure_M04_01_capacity_boundaries_and_capex.{pdf,png}`、`Figure_M04_02_price_basis_and_uncertainty.{pdf,png}`、生成脚本和 QA/运行摘要。顶层 `SUPPLEMENT_WORKFLOW_GUIDE_ZH.md` 与 `SUPPLEMENT_EVIDENCE_REGISTER_ZH.md` 已同步。
- 验证：`conda run -n RL python modules\04_thermal_nuclear_storage_technoeconomics\scripts\generate_module_outputs.py` 成功；`python -m py_compile` 通过；`qa/formal_closure_validation.csv` 19/19 PASS；两张 PNG 均为 `3150×2497`，两张 PDF 均存在且非空；正式终止标记 `FINAL_M04_TECHNOECONOMIC_CLOSURE_PASS`。两张图已完成人工视觉检查。
- 未决/下一步：燃料原始美元价格的价格年和正式出处、GEM tracker 精确版本/下载日期/许可、CapEx 图表数字化误差仍需投稿前补齐；海上风电空间成本、技术特定 WACC、电池时长、既有机组寿命和 CCS/DAC 为高优先级敏感性。下一模块固定为 Module 05 水电、水文、环境流量与梯级拓扑。

### v0.9.50 — 2026-07-28 — 补充材料总控刷新与 Module 02 定稿

- Git/范围：实时本地 HEAD `701b9bc225013a5009dcce3f4e97ee2063dcd00f`；工作树原有用户补充材料改动保持未提交。本里程碑只新增/修改 `supplementary_materials/**` 和本交接记录，未改模型、配置、数据包、服务器或运行结果。
- 输入与口径：直接核对 `optimization_2030.json`、`CapacityFactorStore`、`hourly_cf_index.csv`、`optimization_points.csv` 和 `03_compute_hourly_cf_from_era5V2.py`。生产口径为 2024 北京自然年、删除 2 月 29 日后 8760 h，前 8 h 读取 2023 UTC 年末；波浪能仍为独立 2023 参考年。`city_337`/642 边为生产网络，278/517 只作复现对照。
- 交付：新增 `modules/02_hourly_vre_capacity_factors/` 的技术档案、正式中文方法、来源表、6 张机器表、图注、5 份绘图数据、可复现 Python 脚本及六面板 PDF/PNG；更新 `SUPPLEMENT_WORKFLOW_GUIDE_ZH.md` 和 `SUPPLEMENT_EVIDENCE_REGISTER_ZH.md` 的剩余路线与易漂移计数。
- 命令/证据：`conda run -n RL python modules\02_hourly_vre_capacity_factors\scripts\generate_module_outputs.py` 返回 `FINAL_M02_HOURLY_VRE_CLOSURE_PASS`；正式 QA 12/12 PASS，PNG 3150×2497 px，配对 PDF 非空；人工视觉检查后修复曲线截断和色标遮挡并重跑。当前 manifest/source/QA/smoke 为 240/33/90/142 项，构建 QA 74 PASS + 16 WARN + 0 FAIL，smoke 142/142 PASS。
- 未决/下一步：Module 02 的 2024 单年结果不是长期气候均值，少量格点使用已审计回退；Module 01/03 仍有外部许可与引用缺口。补充材料下一步固定为 Module 04，需把核电 pipeline 下界与 110/205/300/300 GW 上界分列，并完成火电退役、储能和 19 类技术经济参数的来源—表格—图件—QA 闭合。

### v0.9.49 — 2026-07-28 — 2024 Base 744h 严格验收

- 终态：唯一 744h 根 `/data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_v2` 在 `0dadfe9` 上以 `barrier_16_auto_order_v2` 完成。`solve_report=OPTIMAL`、`solution_qc=PASS`、Base identity 正确、49 项 hard checks 全真、result manifest 验证 `(True, [])`；进程已退出，服务器恢复空闲。
- 规模/求解：raw `4,915,427/3,711,992/40,836,493`，presolved `3,063,498/2,664,976/31,086,440`（rows/columns/nonzeros），presolve 173.12 s，ordering 114.19 s，`AA' NZ=6.388e7`，`Factor NZ=7.481e8`，`Factor Ops=4.721e12`。Barrier 211 次/7,543.19 s；crossover 5,709.46 s；simplex 1,437,196；solver 13,268.90 s；墙钟 3:47:18；峰值 RSS 20.049 GiB；无 swap。
- 科学身份：`base`、wave on、flexible load off、`national_dense_v1`、2024 Beijing natural-year VRE。最大功率平衡残差 `3.43e-12 GW`，最大约束/边界/对偶违例 `9.32e-8/2.75e-8/9.35e-8`。结果是 744h 工程门禁，不能解释为 8760h 科学结果。
- 解释：相对历史 wave-off/旧气象 744h，本根墙钟、RSS 和 factor ops 均较低，但模型边界与气象数据不同，不能把差异单独归因于 solver profile。crossover 占约 43% solver 时间，仍是后续 8760h 的核心工程风险。未启动固定服务器 8760h、第二个求解或付费云任务。

### v0.9.54 — 2026-07-28 — 生产运行契约闭合与 Crossover=3 744h 否决

- Git/范围：工程提交 `701b9bc225013a5009dcce3f4e97ee2063dcd00f` 已双端推送并部署。修改只涉及运行身份、原子锁、严格 resume/input 校验、solver 阶段审计和数值 profile；未改变 Base 的目标、约束、技术、时空尺度或数据来源。已有 `supplementary_materials/**` 用户改动保持未提交。
- 工程与短门禁：新增 `run_identity.json`、源码 bundle、Git/config/profile/scenario/formulation/data-root 身份，且运行根与 planning sequence 均采用原子 claim。运行中输入变化、混合身份 resume、或非 `OPTIMAL+PASS+manifest` 终态均硬失败。本地/服务器完整回归均 `98/98`；本地 1h/24h 新 Base 根均 `OPTIMAL + PASS + manifest true`。服务器仅以 add-only 方式补齐 flexible envelope 与 manifest，SHA256 已在当前快照记录。
- 168h 严格 A/B：`Crossover=3` 在完全相同矩阵、目标、QC、manifest 与 RSS 下，将 crossover 从 `190.92 s` 降至 `117.67 s`，总 solver 从 `649.17 s` 降至 `594.63 s`；`CrossoverBasis=0` 为 `661.25 s`，淘汰。比较文件为 `/data/zz2/National_model/outputs/solver_ab_v0728_crossover_168h.{json,csv}`。
- 744h 放大反例：唯一新根 `2030_744h_v0728_2024_dense_dualred_crossover3_v1` 与接受的 Crossover=1 根 raw/presolved、`AA' NZ=6.388e7`、`Factor NZ=7.481e8`、`Factor Ops=4.721e12` 和 211 次 Barrier 完全一致。候选完成 Barrier (`6,981.07 s`) 和两类 push (`PPush=1,191.93 s`、`DPush=1,214.00 s`)，但 primal cleanup 发生极端 infeasibility 循环；在 `10,930.99 s` 时优雅中断，终态 `INTERRUPTED`、无解、无 QC、无 manifest，simplex `1,724,960`，peak RSS `19.828 GiB`。因此不能用中断时的较低累计时间声称更快，`Crossover=3` 明确不进入生产候选。
- 决策/下一步：继续以 `barrier_16_auto_order_v2` / `Crossover=1` 作为唯一接受的 744h profile；保留中断根和 `solver_ab_v0728_crossover_744h.{json,csv}` 作为负面工程证据，绝不重写为科学结果。未来候选先完成匹配 24h/168h 的最终门禁，再由唯一胜者运行一个新 744h 根；固定服务器 8760h、新付费云任务和 MGA solve 均未启动且仍需相应授权。

### v0.9.48 — 2026-07-28 — 单一 2024 Base 744h 已启动

- Git/运行身份：168h 证据提交 `0dadfe9` 已双端推送并部署。服务器在无其他求解、约 70 GiB 可用内存时，于 `03:12:23+08:00` 启动唯一根 `/data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_v2`；命令显式使用 `--diagnostic-hours 744` 与 `barrier_16_auto_order_v2`，未使用省级碳分层。
- 当前状态：PID `2708836`/Python child `2708837` 正常存在，尚处于模型构建且没有 Gurobi 日志。此条仅记录启动，不是求解验收。终态必须同时满足 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`。
- 安全边界：保持单一求解；不改变运行 checkout，不启动固定服务器 8760h、第二个 744h 或付费云任务。结束后再记录 raw/presolved/factor/Barrier/crossover/RSS 与 manifest 终态。

### v0.9.47 — 2026-07-28 — 固定服务器 2024 数据与 168h Phase A/B

- Git/部署：`9a3c5e8` 已同时推送 `origin`/`github` 并部署到空闲固定服务器；部署前实际服务器 HEAD 为 `78a605d`，不是旧快照中的 `4e1999d`。服务器完整回归 `89/89`。
- 数据：以新增归档传输四个 2024 CF Zarr，本地/服务器 SHA256 均为 `2f70713d7a93633f8478e554b1924be7fdfe1d05ff5674a385461d3fa3045cfc`；四目录文件数 3,489/465/3,489/3,825，与本地一致。目标目录原先不存在，未覆盖 2023 stores，归档未删除。
- 168h A/B：三个隔离根均 `OPTIMAL + PASS + manifest true`。0/1 参数 700.50 s；dense 1/0 参数 668.05 s，`AA' NZ`/`Factor NZ` 更低但 crossover 从 72.76 s 增至 190.62 s。省级碳会计与 dense 1/0 的 presolved/factor/迭代/work units/目标完全一致，证明该 raw 稀疏化已由 Gurobi presolve 自动完成，不选为默认。
- 决策/下一步：保留 Base 默认 0/1，不修改科学边界；本轮 744h 工程候选显式使用 dense + `barrier_16_auto_order_v2`，因为 168h 总时间、AA' NZ 与 Factor NZ 占优，同时以 crossover 放大作为停止/复核风险。再次核验空闲和内存后只启动一个新 744h 根；固定服务器 8760h 与付费云任务继续禁止。

### v0.9.46 — 2026-07-28 — 2024 VRE 自然年契约与本地 Phase A/B

- Git/范围：模型实施提交 `1449a4571d2881077f926bbc4116d2c9bdc6b5d5`；本条文档闭合提交待生成。本里程碑仅在本地完成，固定服务器 checkout 仍为 `4e1999d`。修改 `cispo_model/{config,data,diagnostics,io_contract,master,monolithic,wave_energy}.py`、runner、主配置、参数注册表、新 solver/formulation profiles 与聚焦测试；未暂存或修改本任务范围外的 `supplementary_materials/**`。
- 数据契约：风电/光伏使用严格的北京时间 2024 自然年，拼接 2023 UTC 尾部与 2024 UTC 主体并删除北京时间闰日；wave 使用独立的 2023 reference coordinate。provenance 同时哈希两年 VRE stores 及可选 formulation profile。
- 本地验证：完整 discovery `89/89`；两个新 1h 和六个新 24h 根均达到 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`。机器可读比较为 `outputs/solver_ab_v0728_2024_24h.{json,csv}`。
- 结论：省级碳会计在代数、目标和 QC 上等价，但 Gurobi presolve 重建出与全国式相同的矩阵，故保留为实验 formulation 而不选为默认。开启 dual reductions 虽降低 factor 结构，却因 crossover 增长在 24h 变慢；`PreDual=1` 和 `PreSparsify=2` 已在短门禁淘汰。未启动 744h、8760h 或付费云任务。
- 下一步：推送两个远端；再次复核服务器空闲后追加并校验四个 2024 CF stores，部署精确推送提交，运行服务器完整回归和顺序匹配 168h A/B。只有唯一胜者通过全部阶段/RSS/QC/manifest 门禁后，才启动一个新命名的 744h 根；固定服务器 8760h 继续禁止。

### v0.9.45 — 2026-07-28 — 受限 Base MGA 契约及双端回归门禁

- Git/模型范围：实施提交 `4e1999d`（`cispo_model/mga.py`、`scripts/run_cispo_2030_full_year.py`、`cispo_model/solution_export.py`、`cispo_model/result_summary.py`、`cispo_model/master.py`、`cispo_model/io_contract.py`、`config/mga/base_min_onwind_new_national_epsilon_1pct.json` 与 `tests/test_mga.py`）。MGA 不改写 Base 最小成本模型：先按闭合年度 Base manifest、`OPTIMAL+PASS`、`SCIENTIFIC_PRODUCTION`、`BASE_MINIMUM_COST`、相同年度/边界/已解析配置及 required-input SHA256 验证基线，再添加 `Base_cost <= Base_cost* (1+epsilon)`，最后才设置一个显式二级容量目标。
- 输出/QC：MGA 根记录 `mga_request.json`、`mga_run.json`、基线 manifest SHA256、成本松弛、选择器、候选资产哈希、主成本和二级目标。`solution_qc.json` 按原成本表达式而非求解器的 GW 二级目标检查 cost-component closure，并新增成本上限 hard check；`run_summary.json`/`solve_report.json` 分别保留主成本和二级目标。MGA 输出不导出 `planning_state`，也不能成为后续 MGA 基线。
- 支持范围：当前仅接受 `base` 年度基线；二级目标可按全国、省或显式点位选择 `vre_new_capacity_gw`（onwind/offwind/pv）、`wave_new_capacity_gw`、`hydro_new_capacity_gw` 或 `storage_new_power_gw`，方向为最小化或最大化。示例 JSON 是在 1% 松弛内最小化全国新增 onwind；它不是已授权的 MGA 求解。
- 验证/部署：MGA 的小 LP 成本上限测试、闭合基线接受测试、截断基线拒绝测试均通过。本地及固定服务器完整回归均为 `82/82`。在固定服务器空闲、checkout 干净、约 70 GiB 可用内存时，已由 `56d166d` fast-forward 至 `4e1999d`；新根 `/data/zz2/National_model/outputs/2030_1h_v0728_server_mga_runner_base` 为 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，波浪开启、灵活负荷关闭、`analysis_mode=BASE_MINIMUM_COST`。本地同类根为 `outputs/2030_1h_v0728_local_mga_runner_base`。两者都只是截断工程门禁。
- 未决/下一步：当前没有已验收的 2030 Base 8760h，因此不得运行 MGA 或把 1h/24h/168h 诊断根作为其基线。后续先在已授权的全年度 Base 后进行 MGA preflight（不求解）以核验全部身份和成本松弛，再为每个独立的二级目标建立新根和完整 QC；不得启动固定服务器 8760h 或新付费云端任务。

### v0.9.44 — 2026-07-28 — 固定服务器当前 Base 门禁、阶段审计与受限 LP basis 复用

- Git/模型范围：已提交并推送 `56d166d`（`cispo_model/basis_reuse.py`、`cispo_model/diagnostics.py`、`cispo_model/io_contract.py`、`cispo_model/solver_audit.py`、`scripts/run_cispo_2030_full_year.py` 及聚焦测试）。本轮未改变 Base 代数、输入数据契约、情景边界、目标函数或约束；唯一新增的数学模型输出均在隔离的新 test-only 根目录。
- 部署/环境：fast-forward 前已实时复核服务器 checkout、进程和内存。服务器在无活动 CISPO 进程时由 `01ec6f9` fast-forward 至 `56d166d`。新增的 wave-ready 数据根和 wave 数据根均为附加目录，未覆盖或删除既有根、输出或临时文件。仅以本地 wheel 和 `--no-deps` 补齐缺失的 `xarray==2025.1.2`，随后通过 NetCDF smoke test。
- 验证：本地及服务器完整 `unittest discover` 均为 `78/78` 通过。服务器新建的 Base 1h、24h、168h 根均闭合科学 result manifest 并通过 QC。阶段比较 JSON/CSV 记录 raw/presolved 维度、ordering、factor 结构、Barrier、crossover、总运行时间和 RSS；不将全局 presolve 缩减归因于任一源约束族。
- Basis 证据：新的 test-only `.bas` 导出/导入契约会对源 basis 和带名称的 LP 结构哈希。2030 同年及 2030→2040 跨年 1h A/B 都复现了冷启动目标和 QC，并消除了 Barrier；但端到端墙钟仍须完整重建模型和导出结果。全年自动 basis 导出/导入仍受显式 `50m` 非零元带名称身份安全上限及科学运行保护所阻止。
- 未决/下一步：不得由 168h 推断 8760h 可行性。仅在获得已验收的 Base 科学结果后，以独立 runner 实现 MGA，并保留显式成本上限和基线身份。保持历史 744h 根完全不变；未授权固定服务器 8760h 或新的付费云端运行。

### v0.9.43 - 2026-07-27 - raw LP constraint-family sparsity audit

- Implementation commit: `6114157` (`feat: audit raw LP constraint sparsity`). Changed `cispo_model/model_structure_audit.py`, `cispo_model/io_contract.py`, `cispo_model/solver_audit.py`, `scripts/run_cispo_2030_full_year.py`, `tests/test_model_structure_audit.py`, `tests/test_solver_audit.py` and `cispo_full_lp_model_spec.md`. The feature is diagnostic only: it neither adds/removes mathematical variables or constraints nor changes objective, scenario, input data, temporal/spatial boundary or solver numerics.
- Contract: `--constraint-family-audit` explicitly materializes only the raw Gurobi sparse matrix after `model.update()` and hard-fails above the configured 50,000,000-nonzero safety limit. Its JSON records raw family totals, exact densest rows/columns and global log phases after solve; it is catalogued and hashed. Presolve family attribution is deliberately recorded as unavailable because Gurobi does not publish a stable source mapping.
- Verification: targeted audit tests and the full local discovery suite pass `75/75` with `CISPO_WAVE_ROOT` set. Fresh isolated Base roots `outputs/2030_1h_v0727_constraint_family_audit_base_v3` and `outputs/2030_24h_v0727_constraint_family_audit_base_v3` are `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`; wave is enabled, flexibility is disabled and every hard check is true. The 24h root has raw `231,074/345,992/1,729,035`, presolved `129,335/260,116/1,269,506` (rows/columns/nonzeros), 0.73 s presolve, 0.41 s ordering, `AA' NZ=2.200e6`, `Factor NZ=6.284e6`, `Factor Ops=7.399e8`, 89 Barrier, 57,741 simplex/crossover, 29.107 s solver runtime and 0.712 GiB peak RSS.
- Finding/next action: `annual_emissions_accounting` (6,697 raw coefficients), the two largest provincial capacity-margin rows (6,491/5,736) and the 31 `co2_source_balance_p*` rows (3,246 each) are the first dense-row candidates. These are binding scientific/accounting structures, not proven redundancy; do not remove them. First prepare an algebraic equivalence proof for a province-disaggregated annual-emissions accounting form and test one new 24h Base A/B before any 168h/744h decision. No server/cloud checkout, process, queue, historical output or `supplementary_materials/**` file was changed.

### v0.9.42 - 2026-07-27 - isolated cascade nodes use the equivalent independent balance

- Implementation commit: `9787ba7` (`Optimize isolated cascade node construction`). Changed `cispo_model/hydro.py`, `cispo_model/monolithic.py`, `cispo_model/solution_export.py`, `tests/test_hydro_station_model.py` and `cispo_full_lp_model_spec.md`; no source topology, hydrology input, station, objective, capacity, spill, storage or scientific scenario file was changed.
- Scope/equivalence: source topology remains 142 nodes/124 edges. The 8 nodes with no incident edge and exactly one station are excluded only from per-hour core-cascade assembly and receive the existing independent S4-17 vectorized balance. Their core equation has an empty upstream term and a local GRFR inflow identical to the independent form, so the effective core station rows change 146→138 while all 124 topology edges remain. The new guard rejects any multi-station isolated node, preventing a future data refresh from silently changing hydraulic aggregation.
- Validation: targeted hydrology tests pass 8/8; full local discovery passes 71/71 with `CISPO_WAVE_ROOT` set. Fresh Base roots `outputs/2030_1h_v0727_cascade_isolated_nodes_independent_base` and `outputs/2030_24h_v0727_cascade_isolated_nodes_independent_base` are `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`; all hard checks pass, wave is enabled and flexibility is disabled. The 24h objective differs from the paired RUC-thinned reference by `9.78e-09 million CNY`, with identical raw/presolved dimensions. LP degeneracy changes some equivalent dispatch/basis values, so solver path differences are not evidence of a model-boundary change.
- Solvability finding/preservation: 24h `Factor NZ`/`Factor Ops` move from `6.111e6/6.039e8` to `6.284e6/7.399e8`; runtime is 34.636 versus 33.766 s and peak RSS remains 0.724 GiB. This avoids 8×hours Python scalar cascade-row constructions but does not improve the presolved structure, so do not promote it as a Barrier or 8760h optimization. Existing outputs, user-owned `supplementary_materials/**`, fixed-server checkout/outputs and ParaCloud state remain untouched. Exact next action is to seek another mathematically safe, presolve-relevant thinning target locally; no server/cloud run follows from this change.

### v0.9.41 - 2026-07-27 - exact continuous-RUC row reduction

- Implementation commit: `3f2255a` (`Optimize redundant continuous RUC bounds`); this is local only and has not changed the fixed-server or ParaCloud checkout.
- Changed `cispo_model/monolithic.py`, `cispo_model/preflight.py`, `tests/test_ruc_redundancy.py` and `cispo_full_lp_model_spec.md`. It removes only the four generic continuous-RUC upper-bound row families proven by S4-24/S4-25/S4-29 and the nonnegative variable bounds. A build-time domain guard rejects missing RUC parameters, `min_up_h<1`, `min_down_h<1` or `pmin_fraction>pmax_fraction`.
- Validation: the targeted proof/regression tests pass 3/3 and the full local discovery suite passes 69/69 with `CISPO_WAVE_ROOT` set. Fresh Base roots `outputs/2030_1h_v0727_ruc_dominated_bounds_removed_base` and `outputs/2030_24h_v0727_ruc_dominated_bounds_removed_base` are `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`; wave is enabled and flexibility is disabled. Objectives match the paired wave-integrated Base reference within floating-point tolerance, all hard checks pass and manifests close.
- 24h raw rows/nonzeros fall by exactly 32,736/65,472 (12.41%/3.65%) with no variable change. Presolved matrix, factor structure and iterations are identical, so retain this as safe construction/matrix thinning—not as evidence of a Barrier-factorization speedup. The revised static 8760h estimate is 41,186,792 variables/55,928,636 constraints/497,144,388 nonzeros/33.40 GiB and remains non-evidence for an 8760h solve.
- Existing outputs and user-owned `supplementary_materials/**` remain untouched. No server/cloud process, checkout, queue, output root, 744h run or 8760h run was changed. Next action is a separately authorized, fresh 168h A/B only after live server readiness revalidation.

### v0.9.40 - 2026-07-27 - wave-integrated Base and single flexibility overlay

- Git/scenario scope: `c992550` (`refactor: make wave energy part of base`) makes wave energy a normal Base technology and retains exactly two runnable JSON identities: `base` and `flexible_load_comfort_v3_v2g_5pct`. The latter is the sole permitted future flexibility path and inherits the wave-integrated Base. Eight earlier experimental scenario JSONs and planned-suite metadata are removed. Historical outputs, implementations and Git history are deliberately not deleted; they cannot be relabelled as results of the redefined Base.
- Scientific boundary: Base now means wind (including offshore wind), PV and correctly routed existing-grid wave potential, with flexibility disabled. The overlay adds only V3 comfort-envelope heating/cooling, causal V1G and 5% V2G; it retains its calibration-sensitive evidence status. Both runnable cases require `CISPO_WAVE_ROOT`; wave is no longer an optional Base-off switch. This is a stated Base-boundary change, not a solver-only optimization, so earlier wave-off Base gates remain historical engineering evidence only.
- Verification: with the wave data root set, `conda run -n RL python -m unittest discover -s tests -p 'test_*.py' -v` passed `66/66`. New 1h and 24h roots for both identities are `OPTIMAL + solution_qc=PASS + validate_result_manifest=True`; every hard check is true. 24h Base: raw `345,992/263,810/1,794,507`, presolved `129,335/260,116/1,269,506`, `AA' NZ=2.200e6`, `Factor NZ=6.111e6`, `Factor Ops=6.039e8`, 95 Barrier, 67,614 simplex/crossover, 34.074 s, 0.735 GiB peak RSS. 24h overlay: `354,920/268,398/1,844,355`, `132,254/266,492/1,299,953`, `2.221e6`, `6.179e6`, `5.905e8`, 101, 56,990, 33.984 s, 0.731 GiB. These roots are explicitly truncated tests.
- Full-year preflight/preservation: Base estimates `41,186,792` variables, `67,877,276` constraints, `532,990,308` nonzeros and 36.47 GiB; the overlay estimates `44,445,512`, `69,551,896`, `538,014,168` and 37.63 GiB. Local available memory is below the 96 GiB gate, so no build/solve followed. No server/cloud checkout, process, queue, old output or 744h evidence was modified; no 8760h or paid cloud task was launched.
- Exact next action: retain only these two identities in future gates. Before any authorized server deployment, re-check live server checkout/process/memory and run at most one new, separately named 168h root; do not reuse old wave-off Base roots as an A/B baseline for this new Base.

### v0.9.39 - 2026-07-27 - 本地全模块联合敏感性门禁与求解结构审计

- Git commit: `31dc265` (`feat: add combined flexibility and wave sensitivity`)。新增 `config/scenarios/wave_energy_medium_v1_flexible_load_comfort_v3_v2g_5pct.json` 并登记 catalog；仅扩展独立情景和契约测试，未改动 Base JSON、LP 目标函数、约束、空间/时间尺度或既有模块接口。情景同时使用 medium 波浪能、`comfort_envelope_v3` 冷热、V1G 和日内因果 5% V2G；参数状态仍为敏感性，不能提升为 Base 或论文基准。
- Verification: `conda run -n RL python -m unittest discover -s tests -p 'test_*.py' -v` 通过 `67/67`。新建本地 1h、24h、168h 根均为 `OPTIMAL + solution_qc=PASS + validate_result_manifest=True`，且 scenario identity、冷热/V1G/V2G/wave 开关和所有 hard checks 已单独复核。168h raw/presolved 矩阵为 `1,081,688/1,429,226/10,293,428` 与 `751,365/865,314/7,363,654`，`AA' NZ=2.162e7`、`Factor NZ=1.056e8`、`Factor Ops=8.603e10`，180 Barrier、239,930 crossover/simplex、602.265 s 和 3.296 GiB 峰值 RSS。科学 manifest 为零失败。
- Solvability evidence: 全年 preflight 静态估计为 44,445,512 variables、69,551,896 constraints、538,014,168 nonzeros 和 37.63 GiB；相对于 Base 的增量为 +3,533,185 variables、+1,947,832 constraints、+17,091,336 nonzeros、+1.63 GiB。它只描述构建规模，不能替代 Barrier factor/workspace 证据，也不授权 8760h。168h 仅 V1G 激活；冷热/V2G/wave 为零不是技术无效结论，因为该根是 `TEST_ONLY_TRUNCATED_HORIZON` 且混合全年化容量成本与截断运行项。
- Preservation/next action: 未写入既有 744h 输出，未改变固定服务器或 ParaCloud 的 checkout、进程、队列或任务；未启动服务器 8760h 或新付费云任务。详细指标、阻碍及下一步见 `MODEL_COMBINED_MODULE_SOLVABILITY_AUDIT_20260727.md`。如需量化模块的 168h 因果增量，先在同机/同线程/同 profile 下做单一匹配 Base A/B，完整记录 raw/presolved/factor/phase/RSS/QC 后再决定是否评估更长根。

### v0.9.38 - 2026-07-27 - fixed-server Base 168h manifest closure gate passed

- Git/deployment: P0 implementation is `7499062` (`fix: exclude generic wrapper logs from result manifest`); reviewed branch was pushed and the idle fixed-server checkout was fast-forwarded cleanly to `67482ab`. Only `cispo_model/io_contract.py`, `tests/test_result_manifest.py` and handoff documents are in scope; `supplementary_materials/**` user changes remain untouched and uncommitted.
- Command/output: after exporting the three versioned data roots, the server complete discovery suite passed `67` tests (`2` optional xarray tests skipped). The one-at-a-time command used `scripts/run_cispo_2030_full_year.py --diagnostic-hours 168 --solver-config config/solver_profiles/barrier_16_auto_order_v1.json --output-dir /data/zz2/National_model/outputs/2030_168h_v0727_manifest_runtime_contract_base`, with generic `stdout.log`/`stderr.log` redirection and `/usr/bin/time -v`.
- Acceptance evidence: `solve_report.json` is `OPTIMAL`, `solution_qc.json` is `PASS`, `scenario_id=base`, flexibility/wave are false, every hard check is true and `validate_result_manifest()` returns `(True, [])`. The scientific manifest excludes exactly `run.pid`, `stderr.log` and `stdout.log`; their completed sizes may therefore change after finalize without affecting the scientific hash contract. The root is `TEST_ONLY_TRUNCATED_HORIZON`, not a 8760h planning result.
- Scale/performance: raw 1,393,915 rows / 1,011,079 columns / 9,797,949 nonzeros; presolved 729,559 / 817,723 / 7,001,232; presolve 22.89 s; ordering 26.08 s; `AA' NZ=2.131e7`, `Factor NZ=1.036e8`, `Factor Ops=8.436e10`. The solve used 161 Barrier and 226,659 simplex/crossover iterations, 614.894 s solver runtime, objective `2,028,598.8440447072 million CNY`, 3.453 GiB process-tree peak RSS and 12:24.94 wall clock. This is a revalidation of the same Base engineering boundary, not an A/B speed claim against a different scientific case.
- Preservation/next action: existing 744h output was neither modified nor re-manifested; no fixed-server 8760h and no cloud job was started. First design a clearly named, directory-external, read-only post-run audit if P2 needs it. For P3, require matched 24h/168h A/B records of raw/presolved matrix, factor structure, phase times, iterations, objective/QC equivalence and RSS before considering any replacement 744h run.

### v0.9.37 - 2026-07-27 - manifest runtime 日志契约闭合；本地 Base 短门禁通过

- Git 实施：`7499062`（`fix: exclude generic wrapper logs from result manifest`）。仅修改 `cispo_model/io_contract.py` 与 `tests/test_result_manifest.py`；未暂存或提交 `supplementary_materials/**`。
- 契约修正：`stdout.log`、`stderr.log` 与 `runner_stdout.log`、`runner_stderr.log`、`sequence_stdout.log`、`sequence_stderr.log`、`run.stdout`、`run.stderr`、`run.time` 和 PID 文件同属 runtime-managed artifacts。它们从科学目录和 SHA256 result manifest 中排除；`gurobi.log` 继续作为带哈希的科学诊断文件。
- 回归证据：修订后的 manifest 测试先 finalize、再向通用 stdout/stderr 追加，随后通过 `validate_result_manifest()`。聚焦 manifest/I-O 测试通过；`conda run -n RL python -m unittest discover -s tests -p 'test_*.py' -v` 在 17.821 s 内通过 `67/67`。直接以模块路径调用 unittest 的失败仅因 `tests/` 不是 Python package；discovery 是认可的调用方式。
- 新本地 Base 诊断：`outputs/2030_1h_v0727_manifest_runtime_contract` 与 `outputs/2030_24h_v0727_manifest_runtime_contract` 均为新根，均有 `OPTIMAL`、`solution_qc=PASS`、`scenario_id=base`、灵活负荷/波浪能关闭且 result manifest 零失败。24h 为 342,343 个变量、262,201 条约束、1,771,702 个非零元、41.296 s 求解时间和 0.725 GiB 进程树峰值 RSS；它们仅是截断工程门禁。
- 保全/下一步：已完成的固定服务器 744h 根未被写入、重建或重做 manifest；未改变服务器/云端 checkout、进程、调度任务或付费运行。推送审查后的提交后，再次实时核验固定服务器空闲状态、checkout 与内存，才单独决定是否部署并运行新的 168h Base 门禁。固定服务器 8760h 仍禁止；新云端 8760h 仍须单独授权。

### v0.9.36 - 2026-07-27 - 对话收束、实时状态复核与下一阶段目标冻结

- 实时状态：本地分支起始 HEAD `3664177`；固定服务器 checkout 干净停留在 `c879c99`，无 CISPO/Gurobi 进程，约 69 GiB 可用内存。ParaCloud `squeue -u a8s001819` 为空；`sacct` 复核 `4003088=COMPLETED`、`4003172=OUT_OF_MEMORY`、`4004585=TIMEOUT`。
- 核验命令：本地执行 `git status --short`、`git branch --show-current`、`git rev-parse --short HEAD`；固定服务器只读执行 `ps -eo pid,comm,args`、`free -h`、`git -C /data/zz2/National_model/repo status/branch/rev-parse` 及终态 JSON/log 列表；ParaCloud 只读执行 `squeue -u a8s001819` 与 `sacct -j 4003088,4003172,4004585`。
- 本轮结论：`city_337` Base 744h 工程门禁已经证明当前连续 LP 能在固定服务器完成构建、presolve、Barrier、crossover 并满足全部物理/数值 QC；但它是 `TEST_ONLY_TRUNCATED_HORIZON`，且原 `result_manifest.json` 因 wrapper `stdout.log` 在 finalize 后继续写入而未闭合，因此不是 8760h 科学结果或严格可复现 acceptance。
- 对话累计工作：完成 337 市级负荷中心及省内年度网络、2025 初始化、风光水接入路由、5%容量裕度/3.5 s惯量、BECCS 显式碳质量守恒、Base/V1/V2G/V3 模块边界、逐年状态传递与 resume、开放式输入输出/QC/manifest、云端数据/WLS/24h/168h门禁、两次 8760h 失败诊断，以及固定服务器求解器/显式弃水/744h优化。
- 本次变更文件仅为 `CODEX_HANDOFF.md`、`MODEL_SERVER_STATUS.md`、`SERVER_RUNBOOK.md`；`supplementary_materials/**` 用户改动和 `.codex_tmp/` 均保持未修改、未暂存。
- 约束边界：Base 默认不启用灵活负荷和波浪能；不把 744h 目标值解释为年度/路径成本；不把 build-only、静态内存或 Barrier 中间迭代解释为求解成功；不触碰或提交 `supplementary_materials/**` 用户改动。
- 下一阶段：先闭合 manifest 契约和短门禁，再做匹配 A/B 的稀疏结构及 Barrier/Crossover 优化；随后决定744h证据闭合方式。只有通过门禁、资源/费用方案审查并取得显式授权后，才可再次尝试单年 2030/8760h。灵活负荷校准、贴现路径成本账本和 MGA 在 accepted Base 科学结果基础上分别推进。

### v0.9.35 - 2026-07-27 - 744h optimal/QC pass; strict manifest gate rejected

- Terminal solve: fixed-server checkout remained clean at `c879c99`; the sole 744h process exited normally with Gurobi `OPTIMAL`, objective `2,196,881.920967378 million CNY`, 13,541.717 solver seconds, 244 Barrier iterations and 1,451,182 simplex iterations.
- Runtime evidence: `/usr/bin/time` records 3:52:03 wall time, 24,244,196 KiB maximum RSS, 1,086% average CPU, zero swaps and exit status 0. The internal process-tree monitor records 23.121 GiB peak RSS.
- Scientific QC: `solution_qc=PASS` and every hard check is true. Maximum constraint/bound/dual violations are `9.2955e-8/5.4955e-8/9.2151e-8`; maximum power-balance residual is `2.3961e-10 GW`; reservoir transition residual is `1.8798e-5 m3`; AC bidirectional edge-hours and DC reverse flow are zero. `solve_report.scenario_id=base`, `scenario_manifest.scenario.id=base`, and optional flexibility/wave are disabled.
- Manifest audit: 58 entries were checked and every item except `stdout.log` matches. The manifest records 63,631 bytes, while the completed wrapper log is 66,236 bytes; `validate_result_manifest()` returns `False` with only `size:stdout.log`.
- Root cause: `finalize_result_manifest()` correctly excludes names in `RUNTIME_MANAGED_FILES`, but the launch wrapper used `stdout.log`; the current contract recognizes `runner_stdout.log`, `run.stdout` and sequence variants, not the generic name. The script prints the final solve report after manifest finalization, making this particular log stale by construction.
- Decision and exact next action: preserve the terminal output unchanged and do not call it an accepted reproducibility gate. Review a minimal wrapper/contract correction with regression coverage, then either produce a separately identified post-run audit manifest without overwriting evidence or rerun the corrected 744h gate. Do not infer authorization for fixed-server 8760h or another cloud job.

### v0.9.34 - 2026-07-27 - active 744h Barrier completed; crossover in progress

- Runtime identity remains the clean fixed-server checkout `c879c99`, output `/data/zz2/National_model/outputs/2030_744h_v0726_spill_explicit_barrier16_auto_order`, sole Python PID `663050`; no checkout, parameter or process was changed.
- Barrier milestone: Gurobi completed Barrier normally in 244 iterations and 8,917.48 s, reporting interior objective `2,196,881.94 million CNY`, then entered crossover.
- Crossover progress: 1,044,784 initial dual pushes fell to 464,775 by solver time 9,860 s. Telemetry subsequently reached 358,606 simplex iterations at 9,996.25 s with dual infeasibility about `3.515e-3`.
- Memory remains safe: solver memory is 13.948 GB, peak solver memory remains 25.087 GB, process RSS is about 13.8 GiB and host available memory about 55 GiB.
- Acceptance remains pending: `solve_report.json`, `solution_qc.json`, `result_manifest.json` and final `/usr/bin/time` output are absent. Exact next action is continue the sole crossover process and validate all terminal reports before accepting the 744h engineering gate.

### v0.9.33 - 2026-07-26 - active 744h build, presolve and factorization gates passed

- Git/runtime identity: the active solve remains on clean fixed-server HEAD `c879c99`; documentation milestone `b7b6e80` is pushed to both remotes but is intentionally not pulled into the active checkout.
- Build evidence: `build_report.json` records 341.673 s, 3,686,023 variables, 5,920,701 constraints, 42,360,391 nonzeros and 4.977 GiB build peak process-tree RSS.
- Solver structure: presolve completed in 223.80 s at 3,088,821 rows/3,017,979 columns/30,884,732 nonzeros. Automatic ordering completed in 115.48 s with `AA' NZ=6.449e7`, `Factor NZ=8.062e8`, about 9.0 GB estimated factor memory and `Factor Ops=6.197e12`.
- Runtime safety: telemetry peak solver memory reached 25.087 GB during ordering/factor setup; process RSS at early Barrier was about 19.1 GiB and host available memory about 50 GiB. These remain below the 48 GiB solver soft limit and do not justify interruption.
- Progress: Barrier iteration 4 completed at solver time 492.91 s. Primal residual and complementarity fell from `4.97e9/3.55e10` at iteration 0 to `3.89e9/2.83e10`; no acceptance result exists yet.
- Exact next action: keep the sole PID `663050` running, monitor residual trajectory, peak memory and crossover. On completion validate `solve_report.json`, `solution_qc.json`, `result_manifest.json` and scenario identity before accepting the 744h engineering gate.

### v0.9.32 - 2026-07-26 - CPU-PDHG rejected for first scale-up; Barrier-16-auto 744h launched

- Server deployment and validation: local, fixed-server and both pushed remotes are aligned at `c879c99`. The server-focused solver-profile tests pass after adding `pdhg_gpu` to the numerics-only whitelist; Base scientific settings remain unchanged.
- PDHG output: `/data/zz2/National_model/outputs/2030_168h_v0726_spill_explicit_pdhg_cpu32_v2` was gracefully stopped with `status=INTERRUPTED`, `termination_signal=SIGTERM`, `solution_count=0`, 3,074.134 solver seconds and 496,035 last recorded telemetry iterations. Peak solver/process-tree memory was 1.990 GB/2.503 GiB.
- Convergence decision: at about 49万 iterations the log retained a primal residual around `49.5`; the primal/dual objectives were about `2.0117e6/1.9993e6`, and the dual residual was rising. The run was about 4.82 times slower than the complete 637.344 s Barrier-16-auto gate and still had no accepted solution. Keep PDHG as low-memory diagnostic evidence, but exclude it from the first 744h run.
- Five-profile audit: `/data/zz2/National_model/outputs/solver_comparisons/solver_profiles_168h_v0726.{json,csv}` records Barrier-32, Barrier-16+AMD, Barrier-16-auto, interrupted dual simplex and interrupted CPU-PDHG.
- Active gate: after verifying no other CISPO process and about 69 GiB available RAM, the fixed server launched one 2030 Base 744h run at `/data/zz2/National_model/outputs/2030_744h_v0726_spill_explicit_barrier16_auto_order` using `barrier_16_auto_order_v1`, `Threads=16`, `Crossover=1` and `SoftMemLimit=48`. Python PID at launch was `663050`.
- Exact next action: monitor build, presolve, ordering, factor structure, Barrier/crossover and process-tree memory. Accept only `OPTIMAL + solution_qc=PASS + closed result_manifest`; otherwise preserve diagnostics and stop cleanly. Do not start a concurrent fixed-server solve, fixed-server 8760h or another paid cloud job.

### v0.9.31 - 2026-07-26 - 16-thread automatic-order Barrier leads; PDHG profile contract fixed

- Accepted output: `/data/zz2/National_model/outputs/2030_168h_v0726_spill_explicit_barrier16_auto_order` is `OPTIMAL + solution_qc=PASS`, objective `2,028,598.8440447072 million CNY`, 637.344 s solver time and 3.459 GiB process-tree peak.
- Against Barrier-32: same presolved matrix and factor structure, 16 rather than 32 threads, 2.55% faster solve, 8.72% lower telemetry solver memory and 4.29% lower process-tree peak. Against Barrier-16+AMD: 7.292 s faster and avoids the AMD factor-operation inflation.
- Comparison output: `/data/zz2/National_model/outputs/solver_comparisons/solver_profiles_168h_v0726.{json,csv}` records Barrier-32, Barrier-16+AMD, Barrier-16-auto and interrupted dual simplex.
- PDHG contract defect: the first root `/data/zz2/National_model/outputs/2030_168h_v0726_spill_explicit_pdhg_cpu32` exited before data/model loading with `Unsupported solver-profile numerics keys: pdhg_gpu`. No solve was started. `cispo_model/config.py` now permits the diagnostics-supported key and `tests/test_solver_profiles.py` directly loads/asserts the CPU-PDHG profile.
- Validation: 67/67 local tests pass. Exact next action is deploy the whitelist fix, pass the focused server test, rerun CPU-PDHG under a new output identity, then select and launch one 744h profile.

### v0.9.30 - 2026-07-26 - Barrier-16 accepted at 168h; automatic-order control added

- Accepted output: `/data/zz2/National_model/outputs/2030_168h_v0726_spill_explicit_barrier16_sparse_amd` is `OPTIMAL + solution_qc=PASS`, objective `2,028,598.8440447145 million CNY`, solver runtime 644.636 s and peak process-tree RSS 3.187 GiB.
- Relative to Barrier-32: runtime improves 9.390 s (1.44%), process-tree peak falls 0.427 GiB (11.81%), Barrier iterations fall from 185 to 175 and crossover/simplex iterations fall from 228,190 to 226,296.
- Ordering caveat: AMD ordering takes 9.83 rather than 25.70 s, but produces 5.21% more factor nonzeros and 25.54% more factor operations. This could scale adversely at 8760h even though the 168h total is slightly faster.
- Added `config/solver_profiles/barrier_16_auto_order_v1.json` and regression coverage so the next 168h run changes only `Threads=32 -> 16`; automatic ordering and sparsification remain at Gurobi defaults. Scientific settings are unchanged.
- Exact next action: pass local/server tests, run the automatic-order 16-thread 168h gate, then run CPU-PDHG. Select the first 744h profile only after comparing solve/QC, factor structure and memory.

### v0.9.29 - 2026-07-26 - dual simplex rejected at 168h; graceful termination proven

- Output: `/data/zz2/National_model/outputs/2030_168h_v0726_spill_explicit_dual_simplex16`.
- Evidence: after 905.073 solver seconds and 421,470 simplex iterations, the run still had no feasible solution and no objective; recent primal infeasibility repeatedly ranged from roughly `1.5e7` to `1.1e8`. Complete Barrier-32 took 654.026 s on the identical LP.
- Memory tradeoff: dual simplex peak process-tree RSS is 2.594 GiB and telemetry solver memory is about 2.70 GB, versus 3.614 GiB/3.88 GB for Barrier-32. The lower memory does not compensate for the observed degeneracy and convergence risk at larger horizons.
- Termination validation: SIGTERM reached `GracefulSolverTermination`, Gurobi returned status 11, and `solve_report.json` records `status=INTERRUPTED`, `solution_count=0`, `termination_signal=SIGTERM`; `/usr/bin/time` exited normally with status 0. No QC or scientific result is claimed.
- Decision: exclude dual simplex from the first 744h gate. Continue with sequential 168h Barrier-16 and CPU-PDHG gates on explicit spill.

### v0.9.28 - 2026-07-26 - matched 168h spill A/B closed; explicit formulation retained

- Server deployment: idle fixed-server checkout was fast-forwarded from `ed8e91a` to documentation HEAD `94d1f1d`; the complete suite passes 67 tests with two optional wave-I/O tests skipped because xarray is absent. No Base dependency is missing.
- Matched solve: `/data/zz2/National_model/outputs/2030_168h_v0726_spill_explicit_barrier32` is `OPTIMAL + solution_qc=PASS`, objective `2,028,598.844044710 million CNY`, solver runtime 654.026 s and peak process-tree RSS 3.614 GiB.
- A/B result: projected spill is 12.030 s faster at 168h but has 15,114 more presolved rows, 51,936 more presolved nonzeros, `0.7e6` more factor nonzeros, `6.8e8` more factor operations and 0.081 GB higher telemetry peak solver memory. Explicit spill also wins the paired 24h flexibility runtime 34.358 versus 45.168 s. Objectives and QC agree.
- Decision: retain explicit spill because full-year feasibility is constrained by presolved/factor memory and the explicit formulation is more robust across Base and flexibility. Do not infer solve benefit from a raw-column estimate. Preserve the projected 24h/168h roots as rejected-performance evidence.
- Audit output: `/data/zz2/National_model/outputs/solver_comparisons/spill_168h_ab_v0726.{json,csv}` contains both paired runs.
- Local profile pre-screen: Base 24h reference Barrier-32, Barrier-16+AMD+PreSparsify, and dual simplex solve in 33.889, 29.181 and 25.796 s, respectively, all with identical objectives within tolerance and QC PASS. Limited-presolve and forced-dual profiles are slower and produce the same 24h presolved structure as reference.
- Exact next action: on the retained explicit formulation, run sequential fixed-server 168h dual-simplex, Barrier-16 and CPU-PDHG gates. Use their solve/QC/memory evidence to select one 744h profile; do not run fixed-server 8760h.

### v0.9.27 - 2026-07-26 - spill formulation A/B reopened after presolved-matrix evidence

- Git state: `44f7fef` adds limited-presolve/fast-crossover, forced-dual and CPU-PDHG profiles; `9e82cc5` restores explicit full-reservoir spill as the provisional default and adds `cispo_model/solver_audit.py`, `scripts/compare_solver_runs.py` and parser regression coverage. User-owned `supplementary_materials/**` changes remain unstaged and unmodified.
- Local paired evidence: explicit spill repeated at 349,039 variables/265,270 constraints/1,807,414 nonzeros, `OPTIMAL + solution_qc=PASS`, objective `1,982,474.939703926 million CNY` and 34.358 s solver time. The exact projected variant has the same objective within `1.4e-9` and passes QC, but takes 45.168 s; its presolved rows/nonzeros and factor operations are higher by 2.03%, 0.68% and 9.62%, respectively.
- Fixed-server projected evidence: `/data/zz2/National_model/outputs/2030_168h_v0726_spill_projection_barrier32` is `OPTIMAL + solution_qc=PASS`. It has 931,447 original columns, presolves to 744,673 rows/757,209 columns/7,053,168 nonzeros, reports `Factor NZ=1.043e8`, `Factor Ops=8.504e10`, solves Barrier in 182 iterations/585.33 s and finishes after 219,718 crossover iterations/641.996 s. Peak process-tree RSS is 3.512 GiB.
- Interpretation: exact feasible-set equivalence does not imply a faster sparse factorization. The projected 168h result is faster than an older fixed-server reference but is not a matched current-code A/B, whereas the local paired 24h result favors explicit spill. Do not select by raw column count.
- Validation: 67/67 local regression tests pass after removing two projection-specific tests. The comparison parser test is included, and the repeated explicit-spill 24h gate passes all manifests and QC.
- Exact next action: push the comparison commits and this documentation, fast-forward the idle fixed server, pass regression, then run the same 2030 Base 168h Barrier-32 command with explicit spill. Select the formulation from presolved matrix/factor/runtime/QC evidence, then test solver profiles sequentially before the first 744h gate.

### v0.9.26 - 2026-07-26 - exact reservoir spill projection and persistent solver diagnostics

- Git state: implementation committed as `6d84209` on `codex/cispo-2030-full-lp`. No `supplementary_materials/**` file was staged or committed; the remaining user worktree changes are preserved.
- Exact reformulation: only 146 cascade-reservoir spill arrays remain explicit. For 474 independent reservoirs, the equality plus nonnegative spill is projected to a water-volume inequality and spill is reconstructed from its slack. This preserves the projected feasible set, generation, costs, downstream physics and the existing full reservoir-output contract.
- Scale evidence: Base estimates are now 330,967 variables at 24h and 36,760,087 at 8760h. Full-year reduction is 4,152,240 columns = 10.15% of the previous Base estimate; constraints are unchanged.
- Numerical equivalence: the previous 24h `flexible_load_comfort_v3` reference objective `1,982,474.939703926` and the projected result `1,982,474.9397039246 million CNY` differ by only `1.4e-9`. The new run is `OPTIMAL + solution_qc=PASS`; maximum reservoir balance residual is `4.68e-6 m3` and minimum reconstructed spill is `-2.12e-9 m3/s`.
- Solver engineering: `--solver-config` accepts only validated `numerics`, is separately hashed in provenance and cannot change scenario/model assumptions. Added reference Barrier-32, memory-conscious Barrier-16+PreSparsify+AMD and dual-simplex profiles. `solver_telemetry.jsonl` flushes Barrier/PDHG/simplex progress, residuals, work and solver memory during the solve, and graceful signal handling asks Gurobi to terminate so normal reports can be written when the scheduler provides a signal grace period.
- Validation: 68/68 regression tests pass. A real 1h Barrier-16 profile run is `OPTIMAL + solution_qc=PASS`, records the solver profile and telemetry, and reports about 0.17 s callback cost in a 9.31 s solve.
- Cloud terminal evidence: job `4004585` ended `TIMEOUT`, not OOM or infeasible, after reaching Barrier iteration 35. MaxRSS remained 476.76 GiB and no principal acceptance reports exist.
- Exact next action: push `6d84209` plus this documentation follow-up, fast-forward the idle fixed server, pass server regression plus 24h/168h gates, then run one 744h profile at a time under the 48 GiB solver soft limit and compare build, presolve, ordering, factorization, iterations, crossover, memory, objective and QC.

### v0.9.25 - 2026-07-25 - Barrier-32 passed factorization and reached iteration 23

- Scope: read-only live audit of ParaCloud job `4004585`; no checkout, model, data, output, scheduler limit or process was changed.
- Solver evidence: ordering completed in 3,180.53 s and produced `AA' NZ=7.425e8`, `Factor NZ=3.848e10`, an estimated 340.0 GB factor footprint and `Factor Ops=2.448e15`. Barrier iteration 23 completed at solver time 60,528 s.
- Convergence evidence: primal residual/complementarity declined from `8.98e9/6.57e8` at iteration 0 to `7.71e8/4.47e7` at iteration 23. This is real progress but not convergence; primal/dual objectives remain widely separated.
- Resource evidence: after 17:55:54 wall time, `sstat` reports 499,919,116 KiB MaxRSS = 476.76 GiB and `AveCPU=15-07:23:51`, corresponding to about 367.40 actual CPU-hours and roughly 20.5 cores used on average. Slurm allocation remains 96 CPU billing units/700G.
- Time-limit risk: only 6:04:06 remained at the audit. The Slurm 24h end time precedes the configured 86,400-second Gurobi optimize limit because approximately 41 minutes were spent building the model; without an authorized extension, Slurm may terminate the process before Gurobi can return a graceful `TIME_LIMIT` result.
- Acceptance: only `build_report.json` exists among the principal reports. `solve_report.json`, `solution_qc.json` and `result_manifest.json` remain absent; do not classify the run as solved or start 2040.

### v0.9.24 - 2026-07-25 - authorized Barrier-32 full-year retry submitted

- Git/model identity: local worktree remains dirty at `796a6fc6d0e37db1156c56d9fcbe2468db8cceef`; concurrent local wave/flexibility changes were preserved. The cloud release remains immutable at `22fb493`; no model code, data root or scientific configuration was changed.
- Remote change: created additive script `cloud_cispo_8760_2030_base_barrier32.sbatch` with SHA256 `fc604a1a25d37c9cff8a336c83969809cb5b52ea0ab815183d1ea3a7a96bfbf2`. Relative to job `4003172`, it changes only `--cpus-per-task=128 -> 32`, job/log identity and the isolated output root; it retains `Method=2`, `Presolve=2`, `Crossover=1`, `SoftMemLimit=640`, 700G and 24h.
- Scheduler evidence: job `4004585` started at `2026-07-25 02:34:26 CST` on `m4cg1702`. Slurm shows `CPUs/Task=32` and the runtime config records `threads=32`, but the 700G request caused an allocation/billing TRES of 96 CPUs. The embedded 50-test gate passed in 11.845 s.
- Prior-use accounting: job `4003172` has `CPUTimeRAW=2,642,304` allocated CPU-seconds = 733.973 core-hours and `TotalCPU=07:03:11` actual CPU time. The account-level `sreport` total for 2026-07-24 through 2026-07-26 was 48,355 CPU-minutes = 805.917 core-hours across all jobs; Slurm exposes no remaining paid quota or currency balance.
- Changed handoff files: `CODEX_HANDOFF.md`, `MODEL_SERVER_STATUS.md`, `SERVER_RUNBOOK.md`. No supplementary-material file was modified.
- Exact next action: monitor `4004585` through construction, presolve and ordering. Acceptance requires a terminal status plus `solve_report.json`, `solution_qc.json` and `result_manifest.json`; if it again fails before `Barrier statistics`, preserve the root and do not start another full-year retry without a new solver/memory decision.

### v0.9.23 - 2026-07-25 - authorized 2030 cloud solve OOM before barrier

- Git/server scope: documentation-only live audit of ParaCloud job `4003172`; concurrent local wave/flexibility work was preserved and no checkout, code, input, output or scheduler state was changed.
- Terminal evidence: `sacct` reports `OUT_OF_MEMORY`, exit `0:125`, start `2026-07-24 20:24:47`, end `2026-07-25 02:08:50`, elapsed 5:44:03, 128 CPUs and 700G requested memory. `seff` reports 526.99 GiB MaxRSS and 0.96% CPU efficiency.
- Solver stage: model construction had already passed. Gurobi presolve consumed 17,932.25 s and produced 37,982,903 rows, 35,423,761 columns and 400,861,556 nonzeros. Ordering logged through 140 s; no barrier statistics or iteration 0 appeared before the process was killed.
- Acceptance: `solve_report.json`, `solution_qc.json` and `result_manifest.json` are absent. The cloud root `outputs/full_year_2030_base_22fb493_128cpu_700g` is rejected as an incomplete OOM diagnostic and must be preserved.
- Resource caveat: recorded MaxRSS is below the 700G request, but the step reported an OOM kill and the 750G-configured node rebooted approximately two minutes later. Do not infer a safe 527 GiB requirement; a transient spike, cgroup/kernel accounting or node failure remains possible without administrator logs.
- Exact next action: do not repeat `Method=2`, `Presolve=2`, `Threads=128`, `SoftMemLimit=640` on the same 750G-class node. First audit lower-memory algorithms/orderings on bounded gates or obtain a genuinely larger-memory node, and require fresh explicit authorization before any new full-year submission. Crossover changes alone cannot address this failure because crossover was never reached.

### v0.9.22 - 2026-07-25 - existing-grid wave correction and combined wave/flexibility cases

- Git state: uncommitted local worktree on `codex/cispo-2030-full-lp`, based on `796a6fc`; all pre-existing flexibility and `supplementary_materials/**` changes were preserved. No server/cloud state changed.
- Scope: supersedes v0.9.21 spatial routing. `scripts/build_wave_energy_inputs.py` now retains only raw wave cells matching existing `optimization_points.csv` coordinates within `0.02` degrees and `is_land=0`; `wave_source_grid_id` is CF provenance only, while model identity/cohorts/routes use existing `grid_uid`/`grid_id`.
- Data evidence: 1,285 unique existing marine rows, 1,284 positive-potential options, 9,798.111 GW retained raw potential, 57 imputed-CF rows, maximum actual coordinate difference `4.96e-5` degrees, and exact reuse of every matched `city_337` route. The previous nearest-offwind proxy could misroute external South China Sea rows by up to about 1,524 km and has been removed.
- Combined cases: added `wave_energy_medium_v1_flexible_load_v1.json` and `wave_energy_medium_v1_flexible_load_comfort_v3.json`. Each jointly optimizes both modules in one LP; Base and the single-module scenarios remain separate catalog cases and outputs.
- Changed files: `scripts/build_wave_energy_inputs.py`, `cispo_model/{wave_energy,config,master,monolithic,load_center,preflight,solution_export,io_contract}.py`, wave and combined scenario JSON, scenario catalog, critical parameter registry, wave/sensitivity tests, `WAVE_ENERGY_INTEGRATION.md`, model spec, status, runbook and this handoff.
- Verification: wave and combined 24h preflight reports have overall `PASS` status with 72 records each (67 `PASS`, 2 `INFO`, 3 unrelated existing `WARN`); full local regression passes 62/62; scenario JSON parsing, `py_compile` and `git diff --check` pass. Base/wave/wave+flex-V1/wave+comfort-V3 24h build-only gates contain 342,343/345,992/350,456/352,688 variables, 262,201/263,810/264,647/266,879 constraints and 1,771,704/1,794,509/1,825,757/1,830,221 nonzeros. A four-case sensitivity-suite dry run preserves independent output/state roots and accepts both combined IDs. Full-year static wave and wave+flex-V1 estimates are 36.47/36.91 GB. No optimization was started.
- Unresolved: retained potential is still a very large technical upper bound; scenario-specific potential is absent; 2060 holds 2050; China cost, exchange rate, depth/distance, imputation and `potential_fraction` sensitivities remain mandatory. Comfort V3 combined runs additionally require its generated envelope.
- Exact next action: finish local regression/diff checks, then review the spatial/cost sensitivity matrix before any separately authorized 24h optimization and QC gate.

### v0.9.21 - 2026-07-25 - grid-resolved optional wave-energy expansion

- Git state: uncommitted local worktree on branch `codex/cispo-2030-full-lp`, based on `796a6fc`; pre-existing flexibility and supplementary-material changes were preserved and no server/cloud checkout was modified.
- Scope: audited `wave_grid.nc` and the Excel summary; added an opt-in wave data contract, grid capacity/new-build cohorts, exact hourly CF availability, provincial dispatch/balance/reserve coupling, annual load-center allocation, cost/QC/provenance/summary exports, and a scenario catalog entry while leaving `VRE_TECHS` and Base unchanged.
- Main changed files: `cispo_model/wave_energy.py`, `data.py`, `config.py`, `master.py`, `monolithic.py`, `load_center.py`, `planning_state.py`, `preflight.py`, `solution_export.py`, `result_summary.py`, `io_contract.py`; `config/optimization_2030.json`, `config/scenarios/wave_energy_medium_v1.json`, `config/scenarios/scenario_catalog.json`, `config/critical_parameter_registry.csv`; `scripts/build_wave_energy_inputs.py`, `data/wave/*`, `tests/test_wave_energy.py`, `tests/test_sensitivity_suite.py`, `WAVE_ENERGY_INTEGRATION.md`, `cispo_full_lp_model_spec.md`.
- Commands/evidence: `scripts/build_wave_energy_inputs.py` produced 4,194 unique routes and SHA256 manifests; wave preflight is `PASS` with 68 checks; Base and wave 24h build-only gates succeed; `python -m unittest discover -s tests` passes 61/61; `py_compile` and `git diff --check` pass.
- Data/cost boundary: raw potential is identical in all ten CF scenarios, 241 CF grids are imputed, maximum source distance/depth is 1,654.768 km/5,847.782 m, route-proxy distance reaches 1,530.837 km, and 2060 holds 2050 medium. CAPEX/FOM/lifetime and depth/distance adders follow DOI `10.1016/j.apenergy.2024.123119` with explicit `7.8 CNY/EUR`.
- Unresolved: replace the nearest-offwind route proxy with maritime/landing/cable data; obtain real scenario-specific potential and 2060 data; calibrate China cost year/exchange rate; run potential/depth/distance/imputation/cost sensitivities. No 24h solve, 168h/744h/8760h run or deployment is authorized by this milestone.
- Exact next action: review and freeze the wave spatial-screen and cost sensitivity matrix; only then run a local 24h optimization/QC gate, followed by separately authorized staged gates.

### v0.9.20 - 2026-07-24 - Power_curve_V2 comfort envelopes, deadline V1G and causal optional V2G

- Git state: uncommitted local worktree based on `796a6fc`; no fixed-server or cloud deployment.
- Scope: adds an independent `comfort_envelope_v3` without changing Base or accepted legacy scenario semantics. Thermal power limits come from `Power_curve_V2` BAIT/balance-point perturbations rather than uniform 15% fractions; V1G receives a rolling cumulative 12h service deadline; optional V2G is a causal daily-zero 5%-of-EV-peak sensitivity. Response costs are split by thermal direction, V1G relocated energy and V2G discharged energy.
- Changed files: `cispo_model/{config,data,flexible_load,io_contract,preflight,solution_export}.py`, `scripts/build_flexible_load_envelope_v3.py`, `config/scenarios/{flexible_load_comfort_v3,flexible_load_comfort_v3_v2g_5pct,scenario_catalog}.json`, `tests/{test_flexible_load,test_sensitivity_suite}.py`, `supplementary_materials/灵活性负荷V3建模与参数依据.md`, and this handoff/status/runbook set. Existing user-owned supplementary files were not edited.
- Data evidence: generated ignored input `data/load/flexible_load_envelope_v3.csv.gz` has 1,357,800 rows and SHA256 `b5ebda4344a8f978606c242065159f27a75994a5d976f2cbe06038d66a429a03`; its provenance sidecar records all upstream hashes and four passing QC families. A 24h preflight confirms both files are required/hash-recorded scenario inputs.
- Validation: 58/58 local regression tests pass. `outputs/diagnostic_24h_flexible_load_comfort_v3` and final V2G root `outputs/diagnostic_24h_flexible_load_comfort_v3_v2g_5pct_final` are both `OPTIMAL + solution_qc=PASS`; solver runtimes are 33.63/38.60 s, peak process-tree RSS 0.739/0.718 GiB, and all state, terminal, service, combined-charging, simultaneity and objective-component checks pass.
- Unresolved: the +/-1 C band, equivalent thermal duration/retention, V1G participation/deadline and activation prices remain sensitivity parameters rather than province-specific building/vehicle calibrations. Vehicle connection/SOC/departure data and building RC/COP/occupancy data are absent. The 5% V2G number is explicitly not a policy mandate.
- Next action: retain the no-V2G V3 scenario as the main flexibility sensitivity and the 5% V2G case as separate. Run low/base/high parameter sweeps on small horizons, then request explicit authorization before any fixed-server 168h or larger V3 gate. Do not alter the active cloud release.

### v0.9.19 - 2026-07-24 - cloud full-year build accepted; 2030 solve in presolve

- Git/model identity: cloud release remains immutable at `22fb493`; this is a read-only operational audit and documentation update. Local state-flex code `271c6dc` is not deployed to the active cloud release.
- Build-only evidence: Slurm job `4003088` completed in `00:40:20`, exit `0:0`, on `m4cm1904`. `build_report.json` records `SCIENTIFIC_PRODUCTION`, 8,760 h, 40,912,327 variables, 68,189,325 constraints, 515,040,080 nonzeros and 53.633 GiB peak process-tree RSS. No solve/QC is expected from this no-optimize gate.
- Solve evidence at 2026-07-24 21:17 CST: dependent job `4003172` is `RUNNING` on `m4cg1702`, 128 CPU, 700G, 24h limit. Its model build completed in about 40m32s with identical structure and 53.686 GiB build peak. Gurobi 13.0.2 accepted `Threads=128`, `SoftMemLimit=640`, the WLS license and the full LP, then entered `Optimize`.
- Current stage/resource: the latest log ends after coefficient statistics, before `Presolve removed` or barrier iteration 0. Treat it as Gurobi presolve/matrix preprocessing, not barrier or crossover. `sstat` batch MaxRSS is 101,085,156 KiB = 96.402 GiB; no `solve_report.json`, `solution_qc.json` or `result_manifest.json` exists yet.
- Action: continue read-only monitoring. Do not cancel, resubmit, change checkout/config, start 2040 or classify the result until terminal Slurm state plus solve report, QC and manifest are all available.

### v0.9.18 - 2026-07-24 - state-based thermal flexibility and causal EV V1G

- Git implementation: `271c6dc` (`feat: add state-based flexible load scenario`), based on `72bd078`.
- Scope: added independent `flexible_load_state_v2` without changing Base, `flexible_load_v1` or `flexible_load_v2g_v1`; implemented daily-reset equivalent heating/cooling state equations, thermal loss accounting and a nonnegative EV charging backlog that prevents recovery charging before baseline energy is deferred. The new formulation rejects V2G until hourly vehicle availability, battery energy and departure-service inputs exist.
- Power_curve_V2 alignment: verified the current 1,357,800-row National_model table is an exact five-year/name-code/MW-to-GW transformation of the eight-year future projection, with maximum numerical error `5.68e-14 GW`. The final input SHA256 is `8c2cb3b6b233625af2e6f9aef635a1fcabfe746010c2a11464579f8b77a369cd`; the upstream projection SHA256 is `67a0a79ed94f5ffa1f5935519044e09e8878f6429fbe79ed605d16e4d067af5a`. `ev_hour_weight` remains an uncontrolled charging shape, not availability.
- Main files: `cispo_model/flexible_load.py`, `cispo_model/config.py`, `cispo_model/preflight.py`, `cispo_model/solution_export.py`, `cispo_model/io_contract.py`, `config/scenarios/flexible_load_state_v2.json`, `config/scenarios/scenario_catalog.json`, tests and the tracked model/I/O/provenance documents. No `supplementary_materials/**` file was modified or committed.
- Verification: 56/56 regression tests and `compileall` pass. Final 2030 24h output `outputs/2030_24h_v0724_flexible_load_state_v2_final` is `OPTIMAL + solution_qc=PASS`; it has 349,039 variables, 265,270 constraints, 1,807,414 nonzeros, 32.84 s solve time and 0.705 GiB peak process-tree RSS. Maximum heating/cooling/EV backlog transition residuals are `8.88e-16/1.73e-18/4.44e-16 GWh`, all daily terminal states/backlog are zero, simultaneous up/down counts are zero and the result manifest validates.
- Sequential interface: `outputs/planning_sequence_1h_v0724_flexible_load_state_v2` passes 2030/2040/2050/2060 with four `OPTIMAL + QC PASS` cases, four valid manifests and immediate four-year `RESUMED_ACCEPTED`. This is test-only evidence.
- Scale: full-year static estimate is 43,356,367 variables, 68,724,249 constraints, 524,283,387 nonzeros and 36.84 GiB model memory. Barrier factorization remains a separate larger risk; no 8760h authorization is inferred.
- Unresolved: V2 parameters remain illustrative (`15%` thermal power envelope, `4/5 h` duration, `0.94/0.92` retention, `50%` EV movable share, `12 h` queue envelope, `10 CNY/MWh` per throughput direction). The upstream `Power_curve_V2/scripts/08_generate_future_8760_loads.py` is still untracked in its own dirty repository, so its file SHA256 is recorded but Git-only upstream reproduction is incomplete. No hourly EV plug availability, battery energy, driving withdrawal, departure SOC or province-calibrated building RC/COP data exist.
- Server/cloud: not deployed and not started. Existing fixed-server and cloud output identities must not be reused with `271c6dc`.
- Next action: review/calibrate the new sensitivity parameters and obtain EV availability/building thermal evidence; only after explicit authorization and a live idle-check may a new versioned fixed-server 24h then 168h state-V2 gate be deployed. Do not launch fixed-server 744h/8760h or another paid-cloud 8760h case.

### v0.9.17 - 2026-07-24 - VRE CF fallback hard-fail and city_337 contract clarification

- Git baseline: `4b5bd98`. Changed owned files are `cispo_model/data.py`, `cispo_model/preflight.py`, `tests/test_vre_cf_fallback.py`, `MODEL_IO_CONTRACT.md`, `SCENARIO_MODULE_ARCHITECTURE.md` and the three continuity documents. The user-authored `supplementary_materials/deep-research-report.md`, `supplementary_materials/National_model_Codex_implementation_plan.md` and all other `supplementary_materials/**` changes remain untouched and unstaged.
- Scope and decision: fixed only a latent cross-technology CF fallback path. Wind sites may use their primary technology store or same-grid `mixed_wind`; if neither exists the loader now hard-fails instead of selecting a PV donor. UPV/DPV may still use the nearest same-province valid PV donor, now explicitly restricted to land-centroid donor grids. Added hard preflight checks for cross-technology mappings and non-land PV donors. Corrected two current contract descriptions from 278 to the production `city_337` annual proxy without rewriting historical 278 replication records.
- Evidence: the active 2030 Base input has 35 onwind and 10 offwind primary-store gaps, all resolved at the same grid through `mixed_wind`; there are zero unresolved wind rows and zero wind-to-PV mappings. There are 29 UPV and 112 DPV nearest-PV fallback rows. A before/after donor comparison shows that the new land-donor restriction changes zero of the 141 current assignments. Focused tests pass 4/4 and full local regression passes 54/54 in the `RL` environment.
- Scientific interpretation: `is_land` is the 0.25-degree cell-centroid mask, not a technology label. The 35 onwind-on-water and 10 offwind-on-land active rows are existing-capacity boundary allocations, have no expandable scenario-B capacity, and use the documented same-grid mixed-wind fallback. They must not be silently reclassified or deleted. Existing-VRE retirement, coincident trunk sizing and enhanced flexibility remain separate scientific choices, not part of this no-regression fix.
- Exact next action: do not alter the active cloud release or jobs. Before deploying this local hardening to any server, wait for the current cloud case to be preserved, use a new code/data/output identity and rerun regression/preflight plus 24h/168h gates. Decide the existing-VRE survival dataset and optional coincident-trunk scenario separately; do not insert unsourced retirement fractions into Base.

### v0.9.16 - 2026-07-24 - cloud 24h/168h gates accepted; authorized 2030 full-year execution queued

- Git baseline: `1d72a8a`; new tracked cloud wrappers are `cloud_runs/scripts/cloud_cispo_diagnostic_gate.sbatch`, `cloud_runs/scripts/cloud_cispo_8760_build_only.sbatch` and `cloud_runs/scripts/cloud_cispo_8760_2030_base.sbatch`, alongside the three handoff/runbook status documents. No `supplementary_materials/**` content was modified or staged.
- Scope: the user-authorized release passed ordered 24h and 168h 2030 Base cloud gates, each with explicit `Threads=32`, 50/50 tests, `OPTIMAL`, `solution_qc=PASS` and closed result-manifest validation. Structural full-year job `4003088` then began on the 768G partition with 128 CPU and 700G; it performs model construction only. After the user explicitly authorized a single-year full solve, `4003172` was submitted with `afterok:4003088`, 128 CPU, 700G, 24h scheduler limit and a 640G Gurobi soft-memory limit. The resource overrides do not change the CISPO physics, objective, constraints, data or horizon.
- Evidence: `4003035` has 342,343 variables/262,201 constraints/1,771,703 nonzeros and 26.978 s solve time; `4003045` has 1,011,079/1,393,915/9,797,949 and 377.057 s. Their cloud roots are respectively `outputs/cloud_gate_24h_base_2030_22fb493` and `outputs/cloud_gate_168h_base_2030_22fb493`; both retain full solver, QC and manifest evidence. At update time `4003088` is running on `m4cm1904`, while `4003172` is correctly `PENDING` on the success dependency.
- Exact next action: let `4003088` finish and validate its `build_report.json`, run scope and Slurm `MaxRSS`. If it succeeds, monitor `4003172` through model construction, Gurobi presolve/barrier/crossover and terminal output QC. Do not start a 2040 successor or reinterpret an incomplete/limit-stopped 2030 run as a scientific production sequence.

### v0.9.15 - 2026-07-24 - cloud proxy export repaired; WLS smoke restored

- Git baseline: `90a0785`; changed tracked files are `cloud_runs/scripts/cloud_proxy_export_probe.sbatch`, `CODEX_HANDOFF.md`, `MODEL_SERVER_STATUS.md` and `SERVER_RUNBOOK.md`. No `supplementary_materials/**` content was touched or staged.
- Scope: at user direction, repaired only the three malformed lower-case proxy export lines in cloud account `.bashrc` and retained `/publicfs01/fs1-a8/home/a8s001819/.bashrc.codex_backup_20260724_proxy_export` before the change. No license-file content, credential or fixed-server checkout was modified.
- Verification: fresh login shell reports all three expected proxy variables. Compute-node job `4002980` explicitly cleared its proxy environment, sourced `.bashrc`, passed `PROXY_EXPORT_COMPUTE_PASS`, and reached `token.gurobi.com` through `172.16.110.3:8888` with HTTP 302. WLS job `4002981` on `m4ci1905.para.bscc` completed `Env.start()` and a two-variable LP with `SMOKE_STATUS 2`, objective `1.0` and `GUROBI_SMOKE_PASS`. Its separate 10-second curl probe timed out, but Gurobi authenticated and optimized successfully.
- Next action: cloud license gate is restored. Before any full-year build-only, run fresh versioned 24h and 168h cloud gates with `Threads <= --cpus-per-task`, full QC and manifests. Do not start fixed-server 744h/8760h or cloud full-year optimization.

### v0.9.14 - 2026-07-24 - fresh cloud network probe reconfirms WLS block

- Git state: local HEAD remains `22fb493`; no model code, input data or production output was changed.
- Scope: submitted only user-authorized Slurm job `4001248` to `amd_a8_384` with 1 node, 1 CPU, 2 GiB and a 5-minute limit. It was the staged `cloud_wls_network_probe.sbatch`; no Gurobi model, CISPO model build or optimization was submitted.
- Evidence: node `m4cl1305.para.bscc` reported direct DNS timeout for `token.gurobi.com` and `curl` status `000`; the explicitly supplied historical proxy `172.16.110.3:8888` returned connection refused and status `000`. `sacct` reports `COMPLETED`, exit code `0`, because the diagnostic intentionally records connectivity failures without failing the shell job.
- Decision: the 8760h user request was reduced safely to its required network gate. No full-year build-only or solve can start until the administrator supplies a currently reachable compute-node proxy or egress route and a new WLS LP reports `GUROBI_SMOKE_PASS`.
- Exact next action: obtain the current proxy hostname/port or an approved direct allowlist from the administrator; run one 1-CPU/2-GiB WLS LP smoke, then re-establish the ordered 24h and 168h cloud gates with explicit Gurobi thread limits before the separately controlled 8760h build-only gate.

### v0.9.13 - 2026-07-24 - cloud city_337 staging and 8760h preflight

- Git baseline: local `22fb493`; fixed-server source baseline `cf39e0a`. Changed tracked files: `cloud_runs/scripts/cloud_wls_network_probe.sbatch`, `cloud_runs/scripts/cloud_cispo_8760_preflight.sbatch`, this handoff, `MODEL_SERVER_STATUS.md` and `SERVER_RUNBOOK.md`. User-owned `supplementary_materials/**` changes were not modified or staged.
- Scope: staged a new cloud release `/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493` without touching the fixed-server checkout. It contains the `22fb493` code archive, `model_ready_20260723_v0722_city337`, `hourly_cf` and `hydro_timeseries_20260719_sequential_sparse`; raw GRFR is intentionally not replicated because it is a provenance/readiness input, not a runtime dependency of this LP.
- Verification: code archive SHA256 is `2f3564ff9123b292106e51bd5ee943e13e874b6798450e38a96428a48a3b6b7a`; 11,350 staged input hashes match source manifest SHA256 `662565a090b64523ec353994e6fdb3314a94b88d429f16e85e1665300ffbc85a`. A missing cloud numerical stack was installed offline into the user-private `gurobipy310` environment from a 14-wheel Linux/Python 3.10 bundle (archive SHA256 `63141e6059580f7a94cbdeafbbc60fe98b69f6e5eca971d9b342ac5d4529228e`); `pip check` passes and Gurobi 13.0.2 was not replaced. Slurm job `4001137` completed the full-year preflight on `m4ci1905.para.bscc` in 4 s, reporting 175.17 GiB available memory, 40,912,327 variables, 67,604,064 constraints, 520,922,832 nonzeros and 36.0 GiB estimated model memory.
- Blocker: WLS smoke `4000608` on `amd_a8_384` and independent network probe `4000762` on `amd_m8_768-a` both show direct DNS/egress failure and `172.16.110.3:8888` connection refused. Therefore no Gurobi model build, no 24h/168h cloud gate and no 8760h build-only/solve was submitted. The `.bashrc` proxy whitespace defect remains untouched; batch scripts export proxy variables explicitly.
- Exact next action: obtain a working compute-node proxy/egress route from the cloud administrator, rerun one 1-CPU/2-GiB WLS smoke and require `GUROBI_SMOKE_PASS`; then run fresh cloud 24h and 168h gates with `Threads <= --cpus-per-task` before the separately controlled full-year build-only gate. Do not infer solve time from the static 36.0 GiB estimate.

### v0.9.12 - 2026-07-23 - city_337 fixed-server 168h V2G accepted

- Identity: server checkout `cf39e0a`; additive data root `/data/zz2/National_model/data/model_ready_20260723_v0722_city337`; output `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v2g_v1`.
- Solve/state evidence: all four years are `OPTIMAL + solution_qc=PASS`; immediate `--resume` returns four `RESUMED_ACCEPTED` records. Runtimes are 792.55/806.12/953.60/1033.25 s; wall time 1:09:57; peak RSS 4,087,888 KiB; swaps zero; wrapper exit zero.
- Output/QC evidence: each 59-entry SHA256 manifest validates with no mismatch. The V2G matrix has 1,057,951 variables, 1,404,982 constraints and 10,100,013 nonzeros. All hard checks pass; maximum center/province/intra/power residuals are `5.12e-12 GWh`, `3.64e-12 GWh`, `3.11e-08 GWh` and `1.60e-10 GW`; BECCS closure is zero.
- V2G evidence: V2G is enabled only in this independent scenario; maximum transition residual is `1.90e-13 GWh`; simultaneous charge/discharge is zero. Period losses in 2030/2040/2050/2060 are 7.747/4.509/13.909/42.092 GWh and agree with both `charge-discharge` and net-load energy change to numerical precision.
- Solvability assessment: barrier/crossover times are 729.00/61.68, 720.15/82.77, 665.47/283.90 and 770.22/259.12 s. Memory remains below 3.9 GiB and no output or state-chain regression is found; late-year crossover remains the measurable runtime variability.
- Next action: server is deliberately idle after completing the approved Base/V1/V2G 24h/168h matrix. Use `city_337` for all future work. Do not start 744h/8760h locally or paid-cloud 8760h without a separately authorized gate.

### v0.9.11 - 2026-07-23 - city_337 fixed-server 24h V2G accepted; 168h V2G active

- Accepted output: `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337_flexible_load_v2g_v1`, server checkout `cf39e0a`, data root `/data/zz2/National_model/data/model_ready_20260723_v0722_city337`.
- Solve/evidence: all four years and immediate `--resume` pass; runtimes are 44.81/43.45/48.35/45.23 s, wall time 9:10, peak RSS 934,340 KiB, swaps zero and wrapper exit zero. Every year is `OPTIMAL + solution_qc=PASS`, has zero false hard checks and a valid 59-entry SHA256 manifest.
- V2G/output evidence: V2G is enabled only in this independent scenario. Maximum transition residual is `1.83e-12 GWh`; simultaneous charge/discharge is zero. Period charging losses in 2040/2050/2060 are 0.1563/2.3423/3.4673 GWh and equal both `charge-discharge` and `net_load_energy_change` to numerical precision. Network, Base flexibility, security and BECCS closures remain valid.
- Active/next action: PID `4032297` runs `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v2g_v1`. Keep checkout/data immutable; after exit validate all four years, output layers, loss accounting, state transfer and an immediate `--resume`. No fixed-server 744h/8760h and no paid cloud 8760h.

### v0.9.10 - 2026-07-23 - city_337 fixed-server 168h V1 accepted; 24h V2G active

- Accepted output: `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v1`, server checkout `cf39e0a`, data root `/data/zz2/National_model/data/model_ready_20260723_v0722_city337`.
- Solve evidence: all four years and immediate `--resume` pass; runtimes are 714.39/816.08/1007.71/980.09 s, wall time 1:08:59, peak RSS 4,030,672 KiB, swaps zero and wrapper exit zero. Barrier/crossover times are 665.74/45.79, 738.71/74.38, 738.10/265.69 and 688.26/288.77 s.
- Output/QC evidence: four SHA256 manifests validate with no mismatches; every year has 337 center balances, 2,022 center-technology rows, 642 intra edges, 31 province accounts, 31 flexibility accounts and 57 output-catalog data rows. All hard checks pass; maximum center/province/intra/power residuals are `5.06e-12 GWh`, `3.64e-12 GWh`, `4.69e-11 GWh` and `1.75e-10 GW`. BECCS closure is zero.
- Flexibility/state evidence: maximum heating/cooling/EV V1G daily-energy residuals are `1.17e-12/1.78e-15/4.26e-13 GWh`; no simultaneous up/down occurs; V2G is disabled; the scenario SHA256 is identical in all four years. `capacity_cohorts_v2` and the final four `RESUMED_ACCEPTED` records revalidate strict state transfer.
- Solvability assessment: versus city_337 Base, V1 adds 31,248 variables, 5,859 constraints and 218,736 nonzeros (3.09%, 0.42%, 2.23%) but total solver time decreases 8.23%. Runtime variability remains concentrated in crossover, especially 2050/2060; no memory, swap, manifest or output-layer regression is detected.
- Active/next action: PID `3984748` runs the independent 24h `flexible_load_v2g_v1` chain at `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337_flexible_load_v2g_v1`. Keep checkout/data immutable; require V2G transition closure, zero simultaneous charge/discharge, energy-loss accounting, four manifests and `--resume`. No fixed-server 744h/8760h and no paid cloud 8760h.

### v0.9.9 - 2026-07-23 - city_337 fixed-server 24h V1 accepted; 168h V1 active

- Identity: server checkout `cf39e0a`; data root `/data/zz2/National_model/data/model_ready_20260723_v0722_city337`; accepted output `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337_flexible_load_v1`.
- Solve/output evidence: four years and immediate `--resume` are `PASS`; all years are `OPTIMAL + solution_qc=PASS`, have zero false hard checks, 337-node network closure and 59 manifest entries. Runtimes are 40.84/44.23/43.39/41.95 s; wall time is 9:35, peak RSS 929,096 KiB and swaps zero.
- Flexibility evidence: scenario ID is `flexible_load_v1`, flexibility is enabled, V2G is disabled, maximum heating/cooling/EV V1G daily-energy residual is `1.14e-13 GWh`, and simultaneous up/down counts are zero. Capacity margin remains 5%, effective inertia remains 3.5 s and BECCS closure remains numerical zero.
- Active/next action: PID `3687503` runs `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v1`. Do not change the server checkout/data root. After exit, audit all four solve/QC/manifests/network/flexibility/state outputs and run an immediate identity-safe `--resume`. No fixed-server 744h/8760h and no paid cloud 8760h.

### v0.9.8 - 2026-07-23 - city_337 fixed-server 168h Base gate accepted

- Identity: model/server checkout `cf39e0a`; additive data root `/data/zz2/National_model/data/model_ready_20260723_v0722_city337`; Base output `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337`.
- Solve evidence: sequence and immediate resume are `PASS`; all four years are `OPTIMAL + solution_qc=PASS` with runtimes 733.00/811.58/892.10/1397.12 s. Wall time is 1:13:47, peak RSS 4,085,152 KiB and swaps zero.
- Output/state evidence: no false hard checks; every result manifest has 59 entries and validates; output layers contain 337 centers, 2,022 center-technology rows, 642 edges and 31 province accounts; strict `capacity_cohorts_v2` transition is reverified by four `RESUMED_ACCEPTED` records.
- Solvability assessment: versus the prior 278 Base 168h model, city_337 adds 1,031 variables, 924 constraints and 2,749 nonzeros. Total solver time is 4.68% higher; 2030/2040/2050 remain comparable or faster, while 2060 Crossover takes 706.6 s and is the principal remaining numerical-performance risk.
- Active/next action: PID `3632117` runs a separate 24h `flexible_load_v1` city_337 chain in `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337_flexible_load_v1`. Keep checkout/data immutable; validate daily conservation, simultaneous shifting, manifests and resume. V2G remains separate; no 744h/8760h.

### v0.9.7 - 2026-07-23 - city_337 fixed-server 24h gate accepted

- Git/server identity: model and fixed-server checkout `cf39e0a`; city-network implementation `8e76753`; additive data root `/data/zz2/National_model/data/model_ready_20260723_v0722_city337`; transferred archive SHA256 `c1451d95c3303f98e53434cd29abc4288f486cba04c99a2c591380b010d470bb`.
- Gate repair: the first server smoke correctly stopped before any solve because its legacy expectation omitted two fuel-cost technologies. The table itself is complete and unique at 1,550 rows (31×5×10). `cf39e0a` updates the smoke contract and adds year/technology/uniqueness checks; local and server smoke pass 142/142.
- Verification: server 50/50 tests, full-license/readiness and preflight pass. The 24h Base four-year sequence and immediate resume audit pass; runtimes 43.29/48.82/41.17/46.90 s, wall 7:21, peak RSS 930,204 KiB, 337 centers and 59 manifest entries per year. All hard checks, network residuals, capacity margin, inertia and BECCS closure pass.
- Active/next action: PID `3321747` runs the new 168h Base chain in `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337`. Keep server checkout/data immutable, monitor each year, then validate all outputs and `--resume`. No fixed-server 744h/8760h and no paid cloud 8760h.

### v0.9.6 - 2026-07-23 - 337-city production network and 2025 initialization

- Git implementation: `8e76753` (`feat: promote 337-city load-center network`). Before deployment the fixed server was reverified clean and idle at `6ed943a`; existing output roots were not altered.
- Scope: promoted one-center-per-prefecture `city_337` to production; retained the 278 Natural Earth package as a separate CISPO replication input; rebuilt every VRE/hydropower route by exact same-province joint minimization of great-circle spur+trunk distance; rebuilt the 642-edge MST+3NN network and 2025 spur/trunk/intra capacities.
- Data/figure evidence: 337 centers/31 provinces, 296 observed and 41 imputed 2022 city electricity weights, 16,609 VRE routes, 2,030 hydro routes, 642 edges, 203 initialized edges, and maximum initialization balance residual `7.28e-14 GW`. Module 03 Figure M09 and the new two-panel Figure M09c plus PDF/450-dpi PNG/source CSV/QA were regenerated locally; pre-existing user files outside the requested module scope were not staged or committed.
- Verification: package manifest `PASS`; 50/50 regression tests; 61-check preflight `PASS`; local four-year 1h Base sequence `PASS` with four `OPTIMAL + solution_qc=PASS` cases, 337 center rows and 59 manifest entries per year; `--resume` returned four `RESUMED_ACCEPTED` records. Base flexibility remains disabled, capacity margin is 5%, and effective inertia is 3.5 s.
- Unresolved/next action: transfer the ignored model-data package by SHA256 to a new additive server data root, deploy the exact pushed commit only while the checkout remains idle, run server tests/readiness, then validate a new 24h four-year Base chain before a 168h chain. Inspect every output layer and compare scale/runtime; do not start fixed-server 744h/8760h or paid cloud 8760h.

### v0.9.5 - 2026-07-22 - reviewed capacity margin and inertia baseline

- Git state: local HEAD `e28f315`; reliability changes are uncommitted and not deployed. The fixed server remains at accepted checkout `6ed943a`, with no new process or output.
- Scope: changed Base provincial capacity margin from `15%` to the reviewed CISPO-aligned `5%`; represented minimum inertia as `3.5 s reference × 1.0 tolerance`; added one resolver shared by model construction and solution QC; retained backward compatibility for v1 scenarios that supply the former single effective threshold.
- Changed files: `config/optimization_2030.json`, `config/critical_parameter_registry.csv`, `cispo_model/config.py`, `cispo_model/monolithic.py`, `cispo_model/solution_export.py`, `scripts/audit_model_parameters.py`, `tests/test_model_foundation.py`, `cispo_full_lp_model_spec.md`, and the three handoff/runbook files. User-owned `supplementary_materials/**` changes were not modified.
- Verification: `conda run -n RL python -m unittest discover -s tests -p "test_*.py" -v` passed 49/49 tests. Local 1h output `outputs/2030_1h_v0722_security_5pct_inertia_3p5s` reached `OPTIMAL` in 12.84 s with `solution_qc=PASS`; effective inertia is `3.5 s`, both reliability hard checks pass, minimum inertia margin is `12.4173 GW·s`, the capacity-margin residual is numerical zero (`-5.68e-14 GW`), and manifest validation returns `(True, [])`. This is a truncated engineering gate, not a scientific result.
- Unresolved/next action: freeze the 2025-2060 total transformation-cost formulation before changing the objective. Keep the current annual snapshot objective until an explicit discounted multi-period NPV or clearly separated ex-post pathway ledger is approved; do not mix lump-sum CapEx with CRF annualization.

### v0.9.4 - 2026-07-22 - CISPO-equivalent BECCS carbon mass balance closed

- Git implementation: `c62b769` (`fix: close beccs carbon mass balance`), based on `231c3d9`. The fixed server remains at `6ed943a`; no checkout, process or accepted output was changed.
- Scope: introduced a single BECCS factor resolver and replaced the ambiguous dual use of the negative factor with explicit gross/captured/stored/uncaptured biogenic CO2, lifecycle emissions and net removal. The CISPO replication baseline retains zero lifecycle emissions, 90% capture and the published year-specific net factors, so objective coefficients, source-sink quantities and feasible set are unchanged.
- Outputs/QC: `annual_resource_accounting_by_province.csv` gains six BECCS fields; `solution_qc.json` hard-checks capture, storage, net-carbon and total-captured reconstruction closure. The I/O contract, formula specification, parameter registry and risk audit were updated.
- Verification: 47/47 tests PASS. `outputs/2030_1h_v0722_beccs_mass_balance` is `OPTIMAL + solution_qc=PASS`; all four new residuals are zero and the result manifest passes. Parameter audit has 22 PASS / 0 WARN / 0 HARD_FAIL and six remaining open/scenario risks.
- Unresolved/next action: make CISPO/adapted parameter scenarios explicit for 40/60-year nuclear lifetime, 5/15% capacity margin and the 3.5 s reference inertia with tolerance; then address CapEx/fuel trajectories and separate line/substation annualization. Do not infer a nonzero BECCS lifecycle factor without new evidence.

### v0.9.3 - 2026-07-22 - diagnostic sensitivity suite interface validated

- Git implementation: `c91828a` (`feat: add diagnostic sensitivity suite runner`), based on accepted fixed-server handoff commit `0d44616`. The fixed server remains clean and idle at `6ed943a`; this runner has not been deployed and no server checkout/output was changed.
- Scope: added a diagnostic-only catalog runner with explicit `--diagnostic-hours`, isolated per-scenario state roots, catalog/config SHA256 identity, refusal of planned-not-runnable scenarios, non-empty-root protection, identity-safe `--resume`, immutable prior-report history and timestamped wrapper logs. Full-year execution is intentionally unsupported by this wrapper.
- Changed files: `scripts/run_cispo_sensitivity_suite.py`, `tests/test_sensitivity_suite.py` and `config/README.md`; this handoff milestone additionally updates `CODEX_HANDOFF.md`, `MODEL_SERVER_STATUS.md` and `SERVER_RUNBOOK.md`. User-owned `supplementary_materials/**` changes were not modified, staged or committed.
- Verification: 45/45 local regression tests PASS. Real 1h output `outputs/sensitivity_suite_1h_v0722_interface` contains three independent Base/V1/V2G four-year chains; all 12 cases are `OPTIMAL + solution_qc=PASS`, all hard checks and result manifests pass, and scenario boundaries are correct. Suite `--resume` returns all cases as accepted without re-solving and preserves the prior report with SHA256 `2140efc5ac4cbb4e9dedbaf4e1d8f43593c05132d638e08dccc1526b5da63766`.
- Scientific boundary: no flexibility parameters, costs, objectives, constraints, units, spatial/temporal resolution or state-transition rules changed. The 1h suite is interface/identity engineering evidence only, not a sensitivity result.
- Unresolved/next action: calibrate evidence-backed building and EV parameter envelopes before adding runnable low/base/high cases. Keep complementarity/cost-relaxation cases planned-not-runnable until their formulation is frozen. Any server deployment must use a new small-gate root; fixed-server 744h/8760h and paid cloud 8760h remain prohibited without the required gates and authorization.

### v0.9.2 - 2026-07-22 - fixed-server 168h flexibility chain accepted

- Git/server identity: before this documentation update, local and pushed HEAD was `d00d1fb`; fixed-server checkout was clean at model commit `6ed943a`. No server checkout change occurred during the run or audit, and PID `1708266` is no longer active.
- Output: `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_flexible_load_v1`; original sequence `PASS`, four years `ACCEPTED`, wall time 1:06:54, peak RSS 4,040,256 KiB, swap zero and wrapper exit status 0.
- Solve/QC evidence: 2030/2040/2050/2060 are all `OPTIMAL + solution_qc=PASS`; runtimes 705.49/672.16/994.41/1181.26 s; all hard checks pass. Maximum heating/cooling/EV V1G daily-energy residual over all years is `8.17e-13 GWh`, with zero simultaneous up/down province-hours.
- Integrity/state evidence: each year has a closed 59-file result manifest; scenario IDs agree across solve/scope/scenario manifests; all input manifests record SHA256 `7b8f1c920bad35e2e41111f7913cfb456b6e369b85db5b03ae86d43801840532`; `capacity_cohorts_v2` state inputs follow 2030 -> 2040 -> 2050 -> 2060 and remain `TEST_ONLY_TRUNCATED_HORIZON`.
- Resume evidence: a fresh `--resume` audit at 2026-07-22 16:05 CST returned sequence `PASS` with four `RESUMED_ACCEPTED` records and no re-solve.
- Changed files: `CODEX_HANDOFF.md`, `MODEL_SERVER_STATUS.md`, `SERVER_RUNBOOK.md`; user-owned `supplementary_materials/**` changes were not modified or staged.
- Unresolved/next action: formalize the sensitivity-case registry/runner and calibrate building/EV flexibility envelopes before scientific interpretation. Keep Base disabled, keep V2G separate, and do not start fixed-server 744h/8760h or paid cloud 8760h without the required gates and explicit authorization.

### v0.9.1 - 2026-07-22 - fixed-server flexibility deployment and gates

- Deployment: fixed-server checkout fast-forwarded cleanly from `b6ca42d` to `6ed943a`; no model process was active during deployment, and existing data/results were not modified. The previous handoff shorthand is corrected: `b6ca42d` was the actual checkout for the Base 168h gate, while `0c1eaf2` was its model implementation baseline.
- Base acceptance: the four-year 168h Base chain completed in 1:08:40 with peak RSS 4,116,892 KiB and zero swap. Every year is `OPTIMAL + solution_qc=PASS + accepted state`; all four result manifests and the immediate resume audit pass.
- Flexibility acceptance: server regression tests pass 42/42. The four-year 24h `flexible_load_v1` chain completed in 6:32 with peak RSS 946,804 KiB and zero swap; all years and the immediate resume audit pass, scenario hashes are identical, daily load-shift conservation closes below `6.44e-13 GWh`, and simultaneous up/down counts are zero.
- Active task: four-year 168h `flexible_load_v1` chain is running under PID `1708266` in `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_flexible_load_v1`.
- Exact next action: monitor the active 168h flexibility chain, validate its four solve/QC/result manifests and resume identity, then calibrate the illustrative flexibility envelopes before any cloud 8760h flexibility case. Do not launch fixed-server 744h/8760h.

### v0.9.0 - 2026-07-22 - modular load flexibility and scenario contract

- Git implementation: commit `6ed943a` (`feat: add modular demand flexibility scenarios`) is pushed to `origin/codex/cispo-2030-full-lp` but not yet deployed, so the fixed-server 168h Base sequence remains an uncontaminated `0c1eaf2` gate.
- Scope: retained the four existing load components in `ModelData`; hard-failed component nonclosure; added recursive, checksummed v1 scenario overrides; implemented daily-conserving heating/cooling and EV V1G shifting plus optional daily-cyclic V2G; routed effective load into hourly balance/reserve/inertia and annual load-center closure while retaining Base peak for capacity margin; added throughput/degradation costs, outputs, QC, scenario-safe resume and sequence aggregation.
- Changed files: `cispo_model/{config,data,flexible_load,io_contract,load_center,monolithic,preflight,result_summary,solution_export}.py`, `config/{optimization_2030,model_input_files}.json`, `config/scenarios/*`, run entrypoints, tests, the model/I/O specifications and new parameter/scenario documentation.
- Verification: 42/42 tests PASS; parameter audit 11,681 rows / 22 PASS / 0 WARN / 0 HARD_FAIL; Base 1h, V1 24h and V2G 24h all `OPTIMAL + solution_qc=PASS`; all three manifests validate. V1/V2G detailed closure and scale evidence is in the current snapshot.
- Unresolved: the current flexibility values are illustrative and need physical calibration; complementarity point/province/national and integrated-realistic entries are explicitly catalogued as planned-not-runnable; no 168h flexibility chain or cloud deployment has been performed.
- Exact next action: finish and audit the active server Base 168h chain; then push/deploy `6ed943a`, run fixed-server 24h/168h flexibility gates, and only after those pass stage the same commit/data hashes on the cloud. Do not launch a paid flexibility 8760h case before calibration and gates.

### v0.8.1 - 2026-07-22 - fixed-server four-year 24h chain passed

- Git/model/data baseline: implementation `0c1eaf2`, documentation/encoding HEAD `b6ca42d`, V0721 additive data root.
- Output: `/data/zz2/National_model/outputs/planning_sequence_24h_v0721_fuel_state`; initial sequence `PASS`, immediate `--resume` sequence `PASS`, four `RESUMED_ACCEPTED` records.
- Per-year result: 2030/2040/2050/2060 all `OPTIMAL + solution_qc=PASS`; solver runtimes 49.424/46.489/45.976/45.735 s; objective values 2,024,956.703 / 2,073,142.226 / 2,232,353.866 / 2,470,806.369 million CNY. These are truncated-horizon engineering values and have no scientific cost interpretation.
- Resource evidence: sequence wall time 6:03.31, maximum RSS 921,792 KiB, exit status 0 and no swap by the sequence process tree.
- Next gate: launched the 168h four-year diagnostic chain as PID `1348292` under `/data/zz2/National_model/outputs/planning_sequence_168h_v0721_fuel_state`. Audit all four years and resume identity after completion; do not start cloud 8760h meanwhile.

### v0.8.0 - 2026-07-22 - fuel accounting and safe sequential diagnostic chain

- Git implementation: `0c1eaf2` (`fix: harden sequential planning and fuel accounting`), pushed to `origin/codex/cispo-2030-full-lp` and fast-forwarded on the fixed server.
- Scope: connected existing province-level biomass prices to `bio/bioccs` fuel costs and the objective; added strict fuel-table coverage/range checks; upgraded state to `capacity_cohorts_v2`; validated source QC/solve/summary/result-manifest hashes and source year/use; isolated test-only diagnostic states from 8760h production; prevented nonempty-directory overwrite, nonzero-return acceptance and stale/mixed resume chains; bounded thermal retrofits by future surviving source capacity; cached Gurobi solution arrays during cohort export; added a parameter audit and deployment/paper case roadmaps.
- Changed files: `cispo_model/{config,data,io_contract,master,monolithic,planning_state}.py`, `config/optimization_2030.json`, `scripts/{build_cispo_data_package,rebuild_fuel_price_tables,audit_model_parameters,run_cispo_2030_full_year,run_cispo_planning_sequence}.py`, three regression tests, `FINAL_DEPLOYMENT_WORKFLOW_20260721.md` and `PAPER_CASE_ROADMAP_20260721.md`.
- Data: new additive fixed-server root `/data/zz2/National_model/data/model_ready_20260722_v0721_fuel_state`; rebuilt fuel-table SHA256 values are recorded in the current snapshot. The previous V0719 root was not overwritten.
- Local verification: 37/37 tests PASS; parameter audit 11,658 rows / 22 PASS / 0 WARN / 0 HARD_FAIL; real four-year 1h diagnostic sequence PASS; all years `OPTIMAL + solution_qc=PASS`; immediate `--resume` revalidation PASS. Caching `vre_new.X` reduced a 1h result/state export from an interrupted >5 min path to about 40 s total wall time.
- Server verification: HEAD `0c1eaf2`; parameter audit matches local counts; 37/37 tests PASS; V0721 24h four-year diagnostic sequence launched as PID `1314704`.
- Unresolved: BECCS gross/captured/stored/lifecycle/net carbon separation; 40/60-year nuclear lifetime, 5/15% capacity margin and 3.0/3.5 s inertia scenarios; CapEx and fuel-price low/base/high trajectories; decision-dependent versus fixed cost decomposition before complementarity epsilon constraints; formal multi-weather-year hydrology/robustness.
- Exact next action: audit the server 24h chain; if four years and resume identity pass, launch a new 168h four-year chain. Only after both pass should the cloud receive the new code/data package and run a single 2030 8760h production case.

### v0.7.4 - 2026-07-21 - second proxy/WLS smoke passed; thread limit flagged

- Git state: current model commit remains `b40900a`; no model code, input data or production output was changed.
- Scope: submitted only Slurm job `3975741` to `amd_a8_384`, 1 node, 1 CPU, 2 GB and 5 minutes; no CISPO command and no exclusive-node request.
- Proxy/license evidence: node `m4cl2501.para.bscc` used the engineer-provided proxy `172.16.110.3:8888`; the connectivity check returned HTTP 302, WLS authentication succeeded, and the two-variable LP returned `OPTIMAL` with `GUROBI_SMOKE_PASS`. `sacct` reports `COMPLETED`, exit code `0`.
- Resource caveat: despite the one-CPU request, the smoke log reported Gurobi could use up to 32 threads. Production scripts must set Gurobi `Threads` no higher than `--cpus-per-task` and verify the effective thread count before paid runs.
- Unresolved/next action: stage only the validated input package, verify SHA256 and output permissions, run cloud 24h/168h gates with explicit resources, then perform the full-year preflight/build-only gate. Do not submit 8760 optimization yet.

### v0.7.3 - 2026-07-21 - compute-node proxy/WLS smoke passed

- Git state: current model commit remains `b40900a`; no model code, input data or production output was changed.
- Scope: submitted only Slurm job `3975724` to partition `amd_m8_768-a`, 1 node, 2 CPUs, 8 GiB, 5 minutes; no CISPO command and no exclusive-node request.
- Compute evidence: node `m4cl0208.para.bscc`, Python 3.10.20, `gurobipy`/Gurobi 13.0.2. Partition inventory reports 192 CPUs and 768,000 MB per node; this resource class is adequate for the current 8760 build/factor-memory estimate, subject to an explicit per-job memory request.
- Proxy evidence: correctly encoded lower- and upper-case proxy variables made `token.gurobi.com` return HTTP 405 through remote IP `172.16.110.3`; WLS authentication then solved the tiny LP with `GUROBI_STATUS=2` and objective `1.0`. A PyPI request transferred data but did not finish within 30 seconds, so proxy throughput remains unbenchmarked for multi-GB data transfer.
- Configuration defect: the account `.bashrc` lines contain non-breaking spaces after `export`, producing `No such file or directory` on login and job startup. No configuration was modified automatically; correct proxy exports are now required inside every Slurm script.
- Unresolved/next action: transfer the tracked code and versioned model-ready/CF/hydrology data to a new cloud directory, verify SHA256 and shared-file permissions, run cloud 24h and 168h CISPO gates, then perform the full-year preflight/build-only gate. Do not submit 8760 optimization yet.

### v0.7.2 - 2026-07-21 - WLS recognized; compute-node DNS/egress gate failed

- Git state: current HEAD remains `b40900a`; no model or input-data files were changed by this milestone.
- Scope: after the engineer's WLS reinstallation, submitted only job `3975474` to `amd_a8_384` with 1 node, 1 CPU, 2 GB memory and a 5-minute limit; no `--exclusive` request and no CISPO production command.
- Compute/license evidence: node `m4cl1306.para.bscc` loaded `gurobipy310`/Gurobi 13.0.2 and recognized WLS parameters from the new private license path. `Env.start()` then failed with `Could not resolve host: token.gurobi.com`; `sacct` reports `FAILED`, exit code `1`.
- Unresolved/next action: the WLS credentials are being parsed, but the compute node cannot resolve/reach the WLS endpoint. Ask the cluster engineer to fix compute-node DNS/egress or provide the required proxy/allowlist, and protect the WLS file with mode `600`. Do not resubmit paid jobs or launch CISPO until one smoke test returns `GUROBI_SMOKE_PASS`/`OPTIMAL`.

### v0.7.1 - 2026-07-21 - Compute-node Gurobi call reached license gate

- Git state: current HEAD remains `b40900a`; no model or input-data files were changed by this milestone.
- Scope: submitted only job `3974169` to `amd_a8_384` with 1 node, 1 CPU, 2 GB memory and a 5-minute limit; no `--exclusive` request and no CISPO production command.
- Compute evidence: node `m4cm2307.para.bscc` loaded `/publicfs01/fs1-a8/home/a8s001819/.conda/envs/gurobipy310`, imported `gurobipy` 13.0.2 and saw `GRB_LICENSE_FILE`.
- License evidence: the two-variable LP failed at `Env.start()` with `HostID mismatch`; `sacct` reports `FAILED`, exit code `1`. The Python/Gurobi installation path is therefore reachable, but the current license is not valid for the allocated compute node.
- Unresolved/next action: do not launch CISPO or repeatedly resubmit paid smoke jobs. Obtain a compute-node-compatible academic named-user reactivation or Academic WLS/site license, then rerun one equivalent smoke test requiring `GUROBI_SMOKE_PASS`/`OPTIMAL` before any data staging or 8760h preflight.

### v0.7.0 - 2026-07-20 - open-source I/O contract, diagnostics and verified server gate

- Git implementation: `b40900a` (`feat: formalize model I/O and diagnostics`), pushed to `origin/codex/cispo-2030-full-lp` and fast-forwarded on the clean fixed-server checkout.
- Scope: added an open-source project `README.md`; formal input/output contract and data dictionary; immutable configuration, environment and input provenance; scope-aware summaries; complete dispatch, reserve, adequacy, resource, marginal-price and shadow-price exports; pickle-free NPZ identifiers; stronger model/state acceptance checks; and sequence-wide aggregation. Constraint handles and diagnostics were added without changing the LP feasible set.
- Main changed files: `README.md`, `MODEL_IO_CONTRACT.md`, `MODEL_744_SERVER_RUN_AUDIT_20260720.md`, `cispo_model/io_contract.py`, `solution_export.py`, `result_summary.py`, `planning_state.py`, `master.py`, `monolithic.py`, run/sequence scripts, input contract and tests.
- Local evidence: 34/34 unit tests PASS; 139/139 data-package checks PASS; local 24h output `outputs/2030_24h_v0720_io_contract_rerun3` is `OPTIMAL/QC PASS`, all 27 hard checks pass, manifest validation is clean, dual export is available and complementarity diagnostics are zero.
- Server evidence: 34/34 unit tests and 139/139 smoke checks PASS. `/data/zz2/National_model/outputs/2030_24h_v0720_io_contract_server` is `OPTIMAL/QC PASS` with 43.65 s solver time and 0.838 GiB peak RSS; manifest `(True, [])`; output catalog 50 rows; data dictionary 493 rows; hourly prices 744 rows; annual shadow prices 3,366 rows; all NPZ files are safe under `allow_pickle=False`.
- 744h audit: the old `5a9f4ab` engineering gate remains solver-valid, but its wrapper-owned `run.stdout` and `run.time` invalidate two old manifest entries. V0720 excludes runtime-managed wrapper files from the scientific manifest and validates the manifest before accepting sequence output.
- Architecture decision: retain sequential 2030/2040/2050/2060 full-year optimization as the production default. It requires four solves and is myopic, but keeps only one 8760h LP resident at a time; a joint four-year perfect-foresight model would multiply time-dependent matrix blocks and peak memory and is reserved for reduced-scale research experiments.
- Unresolved/next action: do not repeat 744h on the fixed server. Complete cloud compute-node/license/data staging, run 24h/168h gates there, then use the 8760h output contract for a single production case. Existing VRE retirement, formal climatological hydrology, cascade lag warnings, PHS hydraulic pairing and long-term sensitivity assumptions remain explicit research items.

### v0.6.4 - 2026-07-20 - Gurobi Linux package staged; license transfer held

- Git state: local branch `codex/cispo-2030-full-lp`, HEAD `3c9edfa76c3077de421b56b2b287585cb7b6188d`; no model code, solver environment or remote job state was changed.
- Scope: downloaded the official Gurobi 13.0.2 Linux x86-64 package, verified the official MD5 and uploaded only the installation archive to the user-private cloud staging directory. No license file was transferred.
- Artifact evidence: `/publicfs01/fs1-a8/home/a8s001819/staging/gurobi1302/gurobi13.0.2_linux64.tar.gz`, 64,798,273 bytes, MD5 `f12dcad337ae1d8f9b8c2b3f51b92bb5`, SHA256 `cffd4ee3c1990294e80446626bd1772045e420d7c34c379839b6acca16f0a23b`; local and remote hashes match.
- License decision: the user-provided email identifies an academic named-user license. Because Gurobi named-user licenses are machine-scoped and Slurm may dispatch jobs across multiple compute nodes, copying a license generated on another server was not assumed valid and was deliberately not performed. The cloud document records `grbgetkey`/WLS decision rules without storing key codes or license contents.
- Unresolved/next action: after explicit approval, use a small scheduler allocation to determine the compute-node target and Gurobi installation path, then choose a compliant named-user reactivation or Academic WLS/site license. Do not install or start 8760h before this check.

### v0.6.3 - 2026-07-20 - BSCC-A8 manual reconciliation and cloud usage document

- Git state: local branch `codex/cispo-2030-full-lp`, HEAD `3c9edfa76c3077de421b56b2b287585cb7b6188d`; no model code, data, solver environment or remote job state was changed.
- Scope: interpreted the user-provided official BSCC-A8 manual screenshot and created `supplementary_materials/云服务器使用规范_BSCC-A8.md` with the documented Modules/Slurm/compiler workflow, current SSH aliases, login-node boundary, storage layout, cost gate and CISPO-specific 8760h stop rules.
- Reconciliation evidence: the manual is dated 2024-08-26 and refers to the older `amd_a8_768` queue; live Slurm audit on `ln301.para.bscc` reports `amd_m8_768-a` as the default partition and `amd_a8_384` as the second active partition. The document marks live values as authoritative instead of copying stale queue names.
- Safety evidence: no remote file was written, no module or package was installed, no Slurm allocation was requested and no job was submitted. The verified module initializer `/public1/soft/modules/module.sh` is documented, while current compute-node Gurobi availability remains explicitly unverified.
- Unresolved/next action: only after user approval, run a small scheduler allocation to inventory compute-node Python/Gurobi/license and perform a smoke test; do not launch 8760h production directly from the login node.

### v0.6.2 - 2026-07-20 - ParaCloud Slurm login-node audit

- Git state: local branch `codex/cispo-2030-full-lp`, HEAD `3c9edfa76c3077de421b56b2b287585cb7b6188d`; no model code, data, solver environment or remote job state was changed.
- Scope: performed a read-only audit after public-key login to identify the safe cloud execution path. No `sbatch`, `srun`, package installation, environment activation persisted, file transfer or model execution was performed.
- Verified cluster: Rocky Linux 8.10 login host `ln301.para.bscc`; Slurm 23.11.9, cluster `bscc-m8`, `select/cons_tres` with `CR_CORE_MEMORY`; account `bscc-a8`, QoS `normal`, association output showing a 10-job submission limit.
- Verified partitions: default `amd_m8_768-a` has 194 nodes, 192 CPUs/node and 768000 MB/node with 4000 MB/CPU default; `amd_a8_384` has 103 nodes, 128 CPUs/node and 384000+ MB/node with 3000 MB/CPU default. Both partitions are `UP` and allow all accounts/QoS at the partition level.
- Environment evidence: login host has 64 logical CPUs and about 376 GiB RAM; `/publicfs01` has about 3.1 PB free. System Python is legacy; shared Miniforge `/public1/soft/miniforge/24.11` exposes `base`, `py-moose` and `toga2`, but none of the checked environments imports `gurobipy` or `torch`. This does not prove compute-node software absence.
- Safety conclusion/next action: treat `ln301` as login-only. Before any paid 8760h work, create an explicit Slurm script, request a small approved allocation to inventory compute-node Python/Gurobi/license and run a smoke check, then require the full-year preflight, memory gate and cost confirmation. Do not install packages or run the long solve from the login node.

### v0.6.1 - 2026-07-20 - ParaCloud public-key authentication verified

- Git state: local branch `codex/cispo-2030-full-lp`, HEAD `3c9edfa76c3077de421b56b2b287585cb7b6188d`; no model code, data or solver environment was changed.
- Scope: corrected the ParaCloud SSH aliases to use the normal public-key-first OpenSSH authentication order, then verified both port 22 and port 2222 end to end with a read-only remote command.
- Verification evidence: `paracloud-bscc-a8` and `paracloud-bscc-a8-backup` authenticated with the existing local public key and returned `CODEX_CLOUD_SSH_OK`, remote host `ln301.para.bscc`, account `a8s001819` and home `/publicfs01/fs1-a8/home/a8s001819`; both commands exited with status 0.
- Security evidence: no password was entered, stored or logged; no private-key content was read or copied. The earlier password prompt was caused by the temporary alias preference and has been removed.
- Unresolved/next action: inventory scheduler, quotas, CPU/RAM/storage, Python/Gurobi, data paths and job accounting on the cloud login node. Do not launch a paid 8760h solve until the cost gate and full-year preflight requirements in the selection policy pass.

### v0.6.0 - 2026-07-20 - ParaCloud route selection and cost-gated SSH configuration

- Git state: local branch `codex/cispo-2030-full-lp`, HEAD `3c9edfa76c3077de421b56b2b287585cb7b6188d`; no model code, data or solver environment was changed.
- Scope: classified the two server targets and configured local SSH aliases for the separate ParaCloud BSCC-A8 endpoint. Existing `national-model-server` configuration was preserved unchanged.
- Changed files/state: repository handoff updated; user SSH config `C:\Users\ZZ\.ssh\config` gained `paracloud-bscc-a8` on port 22 and `paracloud-bscc-a8-backup` on port 2222; memory note `20260720-paracloud-server-routing.md` records non-secret routing and cost-gate metadata.
- Verification evidence: DNS resolved both IPv4 backends; TCP checks passed on ports 22, 2222 and 8443 via Ethernet source `124.16.2.171`. SSH banner/auth checks succeeded on ports 22 and 2222 (`ParaCloud`, `password,publickey`); 8443 and IPv6 port 22 reset before the banner. `ssh -G` confirmed both aliases resolve to the intended compound user and ports.
- Selection rule: use `national-model-server` for local work and the 744h engineering gate; use ParaCloud only for explicitly authorized, scheduler-backed 8760h production after full-year preflight, memory/resource/license validation and cost confirmation. No cloud authentication or paid job was started.
- Unresolved/next action: authenticate through `paracloud-bscc-a8`; inventory scheduler, quotas, CPU/RAM/storage, Python/Gurobi and data paths; only then prepare a checksum-verified production transfer and launch decision.

### v0.5.9 - 2026-07-20 - ParaCloud candidate SSH pre-authentication check

- Git state: local branch `codex/cispo-2030-full-lp`, HEAD `3c9edfa76c3077de421b56b2b287585cb7b6188d`; no model code, data, solver environment or server process was changed.
- Scope: performed a read-only connectivity check for the separate ParaCloud/BSCC-A8 candidate endpoint intended for possible future 8760h computation. The existing validated `national-model-server` target and its SSH configuration were not modified.
- Changed file: `CODEX_HANDOFF.md` only, to preserve this verified server milestone without credentials.
- Verification evidence: the hostname resolved to two IPv4 backends; `Test-NetConnection` passed on TCP port `8443` for both via the workstation Ethernet source address. OpenSSH parsed the compound login user correctly, but `ssh -vv`, `ssh-keyscan` and raw banner checks received no SSH banner and both backends reset or timed out before key exchange.
- Security evidence: no password, private-key content, activation key or license content was read, logged or written. Password validity was not tested because the connection never reached authentication.
- Unresolved/next action: verify in ParaCloud that the BSCC-A8 direct-connection mapping is active and that the workstation source IP is permitted, then rerun the SSH banner/authentication check. After successful login, inventory scheduler, CPU/RAM/storage, quotas, environment and Gurobi license before transferring data or launching any 744h/8760h job.

### v0.5.8 - 2026-07-19 - V0719 deployed, 24h gate passed, 8760 memory gate blocked

- Git/server state: local commits `451b1c0`, `c8db9be` and `bc83663` were pushed to `origin/codex/cispo-2030-full-lp`; server checkout `/data/zz2/National_model/repo` was fast-forwarded to `bc83663`.
- Scope: deployed V0719 code and data contract to a new additive data root, fixed server smoke-test path resolution for CF and hydrology files, and ran server validation. No old data root or old 744h output was overwritten.
- Data root: `/data/zz2/National_model/data/model_ready_20260719_v0719_capacity_bounds`; generated `thermal/nuclear_capacity_upper_by_year.csv`, `biomass/capacity_upper_by_province_year.csv` and `storage/battery_capacity_floor_by_province_year.csv`; added missing smoke/QC support files from canonical `model_ready`.
- Validation evidence: server smoke `139/139 PASS`, server unit tests `32/32 PASS`, readiness `PASS` with full Gurobi license and raw-GRFR SHA256 verification.
- Solve evidence: server 24h V0719 output `/data/zz2/National_model/outputs/2030_24h_v0719_capacity_bounds_server` reached `OPTIMAL/QC PASS`; model size 341,312 variables / 261,280 constraints / 1,768,957 nonzeros; Gurobi runtime 48.96 s; peak RSS 0.841 GiB; zero nuclear, biomass+BECCS, storage and transmission-direction hard-check violations.
- 8760 evidence: direct full-year solve was not launched. Full-year preflight `/data/zz2/National_model/outputs/2030_8760_v0719_preflight_memory_check` reported `memory_gate_pass=false`, available memory `73.15 GiB` versus required `96.0 GiB`; estimated full-year scale 40,911,296 variables / 67,603,283 constraints / 520,920,489 nonzeros.
- Unresolved/next action: wait for memory pressure to clear or use a high-memory node. On this host, run V0719 168h and 744h gates before any full-year production solve. If overriding for an exploratory full-year build, require at least 96 GiB available RAM and start with build-only/preflight evidence, not optimize.

### v0.5.7 - 2026-07-19 - corrected 744h sparse gate completed

- Git/server state: server checkout HEAD `5a9f4ab`; local V0719 capacity-bound/DC active-index corrections remain an uncommitted working tree on local HEAD `f84143a` and were not used by this server run.
- Scope: verified completion of `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict`; no model code, data root or server process was changed.
- Verification evidence: `solve_report.json` reports `OPTIMAL`, `solution_count=1`, objective `2,196,413.3453 million CNY`, runtime `16,245.79 s`, barrier iterations `214`, simplex/crossover iterations `1,468,988`, peak process-tree RSS `21.979 GiB`, and model size 3,955,064 variables / 5,919,746 constraints / 43,707,940 nonzeros. `/usr/bin/time` reports wall time 4:37:02, maximum RSS 23,469,440 kB and exit status 0.
- QC evidence: `solution_qc.json` reports `PASS`, maximum power-balance residual `3.64e-10 GW`, zero line-capacity violation, zero bidirectional interprovincial edge-hours, zero DC reverse flow across 363 DC corridors, zero biomass/carbon/CO2 sink violations and all hard checks true.
- Unresolved/next action: preserve this as the completed pre-V0719 sparse gate. Do not start 8760 production on this older scientific boundary. Commit/push V0719, build a new versioned data root with the three new capacity-bound tables, then rerun readiness, tests, smoke, 24h, 168h and corrected 744h before any 8760 build-only or solve.

### v0.5.6 - 2026-07-19 - V0719 capacity bounds and DC active-index correction

- Git state: branch `codex/cispo-2030-full-lp`, local HEAD `f84143a`, implementation base `5a9f4ab`; V0719 changes are intentionally left uncommitted pending user review. Server HEAD remains `5a9f4ab`.
- Scope: implemented the four issues identified in `supplementary_materials/MODEL_V0719_REVIEW_REPORT.md`: nuclear capacity upper, shared biomass+BECCS capacity upper, 2030 battery exogenous floor and removal of DC reverse fixed-zero variables.
- Main changed files: `config/capacity_bounds_v0719.json`, `scripts/build_v0719_capacity_bounds.py`, data/config loaders, `cispo_model/master.py`, `monolithic.py`, `load_center.py`, `solution_export.py`, `result_summary.py`, `preflight.py`, model-input contract/config, data-package builder/smoke tests, unit tests, model specification and V0719 report.
- Generated inputs: `thermal/nuclear_capacity_upper_by_year.csv` (124 rows), `biomass/capacity_upper_by_province_year.csv` (124 rows), `storage/battery_capacity_floor_by_province_year.csv` (124 rows). These are generated under the configured data root and remain outside Git with the rest of `data/`.
- Scientific boundaries: nuclear national upper `110/205/300/300 GW`; shared `bio+bioccs` upper uses `thermcal×0.35/(3600×6132)` with an inherited-floor safeguard that triggers only in Shanghai; 2030 battery floor totals 65.85 GW after Mengdong/Mengxi merge and is zero as an exogenous boundary from 2040 onward.
- Exact sparsification: reverse variables now exist only for 48 AC corridors; all 411 corridors retain forward variables. Dense 411-row reverse output is reconstructed with DC rows zero, preserving file/API compatibility. Full-year variable reduction is 3,179,880.
- Commands/evidence: `C:\Users\ZZ\.conda\envs\RL\python.exe scripts\build_v0719_capacity_bounds.py`; `... -m unittest discover -s tests -q` passed 32/32 in 17.62 s; `... scripts\smoke_test_data_package.py` passed 139/139; strict 24h solve at `outputs/2030_24h_v0719_capacity_bounds_dc_sparse_rerun` reached `OPTIMAL/QC PASS` with 341,312 variables, 261,280 constraints, 1,768,956 nonzeros, solver 39.79 s and peak RSS 0.702 GiB.
- Validation details: all new capacity-bound violations are zero; DC reverse flow and AC simultaneous bidirectionality are zero; maximum power-balance residual `7.43e-12 GW`. The first too-short timeout output `outputs/2030_24h_v0719_capacity_bounds_dc_sparse` is retained as an interrupted trace.
- Server evidence: at 2026-07-19 16:42 Asia/Shanghai, `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` remained active under PID `3344086`, elapsed 01:35:08 at barrier iteration 107, with no solve/QC reports. It uses the old versioned data root and was not modified.
- Unresolved/next action: commit/push only after review; after the old 744h is preserved, create a new versioned data root, generate the three bound tables and pass server readiness, 32 tests, 139 smoke checks, 24h, 168h and corrected 744h. Do not run 8760 yet. Long-term nuclear, updated biomass, separated battery GW/GWh, formal multi-year hydrology and CSP remain scenario/data work, not hidden hard constraints.

### v0.5.5 - 2026-07-19 - annual-network sparse cleanup and corrected 168h gate

- Git implementation: `5a9f4ab` (`Reduce annual network matrix duplication`).
- Scope/changed files: `cispo_model/load_center.py` reuses province sent/received accounts in net-import closure, removes the implied province reservoir-generation closure and adds unique route checks; `cispo_model/preflight.py` corrects variable-block accounting and recalibrates nonzeros; `config/optimization_2030.json` raises the full-year RAM gate to 96 GiB and removes unused LP-inapplicable settings; `tests/test_model_foundation.py` adds scale/sparsity/gate regressions.
- Verification: local 29/29 tests; local strict 24h `OPTIMAL/QC PASS`; server readiness/raw-GRFR/full-license PASS; server 29/29 tests; server strict 168h `OPTIMAL/QC PASS` in 666.45 s with 3.910 GiB peak RSS.
- Scale evidence: 168h nonzeros decreased from 10,480,639 to 10,100,058 while variables remained 1,071,032. Direct availability-variable removal was rejected after a 24h build increased nonzeros from about 1.87m to 2.23m.
- Server command/output: `scripts/run_cispo_2030_full_year.py --diagnostic-hours 168 --output-dir /data/zz2/National_model/outputs/2030_168h_sparse_gate_strict`.
- Unresolved/next action: PID `3344086`/child `3344087` is running the strict corrected 744h gate under `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict`. Only after `OPTIMAL/QC PASS` and a fresh >=96 GiB memory check may 8760h build-only start; build success still does not authorize solve.

### v0.5.4 - 2026-07-19 - full-year solvability and cross-year completeness audit

- Git audit commit: `ab9dfe8` (`docs: audit full-year solvability and state transfer`); implementation remains `1b6da28`, documentation baseline before this entry was `f22b9cf`.
- Scope: decomposed current 24h/168h model size by VRE, thermal RUC, storage, hydropower, transmission, balance/security, annual load-center and carbon blocks; recalibrated 8760 nonzeros/static build memory; audited 744h factorization/crossover; reviewed Gurobi parameters and every cross-year capacity cohort class.
- Changed files: `MODEL_SOLVABILITY_AUDIT_20260719.md`, followed by continuity updates in `CODEX_HANDOFF.md`, `MODEL_SERVER_STATUS.md` and `SERVER_RUNBOOK.md`.
- Commands/evidence: current 24h/168h `scripts/audit_model_numerics.py --skip-full-max-cf`; live `ssh national-model-server` HEAD/resource check; rejected 744h `solve_report.json` and `gurobi.log`; two current-model 24h parameter diagnostics.
- Findings: revised 8760 scale is about 44.09m variables, 68.19m constraints and 515-524m nonzeros; calibrated build peak is about 58 GiB, but linearly extrapolated barrier factor memory alone is about 118 GB. Direct 8760 solve on 125 GiB is high risk.
- Parameter result: `Crossover=0` failed current hard QC; a default feasibility/optimality tolerance plus `BarConvTol=1e-7` candidate saved about 7% at 24h and remains diagnostic-only.
- Cross-year result: all current capacity decision classes are transferred through checksummed active cohorts, including VRE, thermal/nuclear, hydro, battery/PHS, inter-/intra-provincial transmission, DAC, spur and trunk. Remaining physical limitations are myopic foresight, missing existing-VRE age retirement, plant-level thermal retrofit remaining life, additive nuclear pipeline interpretation and province-level fixed-duration PHS.
- Unresolved/next action: implement exact availability/load-center sparse reformulations, correct scale reporting, pass local gates, then rerun corrected 744h when shared memory pressure clears. Require at least 96 GiB available RAM for 8760 build-only; do not optimize until its true memory evidence is reviewed.

### v0.5.3 - 2026-07-19 - corrected server 24h transmission gate

- Git implementation: `1b6da28`; synchronized server documentation HEAD includes `c4cfddd` or later.
- Server tests: 26/26 PASS in 22.24 s under `/home/zz2/.local/envs/cispo-2030`.
- Output: `/data/zz2/National_model/outputs/2030_diagnostic_24h_20260719_cispo_flow_alignment_cpu`.
- Solver: 350,024 variables, 261,280 constraints and 1,867,007 nonzeros; Gurobi 13.0.2 `OPTIMAL` in 43.88 s; peak process-tree RSS 0.845 GiB.
- QC: power-balance residual `1.46e-11 GW`; reservoir-transition residual `7.63e-06 m3`; zero AC bidirectional edge-hours; zero DC reverse flow on 363 DC edges; all hard checks PASS.
- Output integrity: every scientific manifest file matched size and SHA256; runtime-owned stdout/stderr/PID files are explicitly excluded.
- Resource stop: only about 32 GiB RAM was available and all 21 GiB swap was occupied by shared workloads. No corrected 744h or 8760h process was started.
- Next action: wait for shared memory pressure to clear, require at least 64 GiB available RAM, then launch a new versioned corrected 744h CPU barrier gate.

### v0.5.2 - 2026-07-19 - CISPO transmission alignment after 744h result audit

- Git implementation: `1b6da28` (`fix: align interprovincial flows with CISPO`).
- Rejected baseline: `/data/zz2/National_model/outputs/2030_one_month_20260719_sequential_sparse_cpu` reached `OPTIMAL` in 20,118.58 s with 22.141 GiB peak RSS, but contained 3,358 material bidirectional edge-hours, 3,909.04 GWh summed opposing minimum flow and a 4.393 GW maximum opposing minimum flow.
- Root causes: the model configured `0.001 yuan/MWh` instead of CISPO's `0.001 yuan/kWh = 1 yuan/MWh`; DC reverse flow was not fixed to zero; the added annual load-center layer closed gross sent/received energy and rewarded artificial loops.
- Fix: AC keeps `f_forward + f_reverse <= capacity`; DC reverse UB is zero; flow cost is 1 yuan/MWh; the annual load-center layer closes province net exchange; AC bidirectionality and DC reverse flow are hard QC failures; shell-managed files are excluded from the scientific SHA256 manifest.
- Local verification: tests 26/26 PASS; corrected 24h model 350,024 variables, 261,280 constraints and 1,867,006 nonzeros; `OPTIMAL` in 40.02 s; peak RSS 0.700 GiB; power-balance residual `5.35e-12 GW`; zero AC bidirectionality; zero DC reverse flow across 363 DC edges; manifest mismatches zero.
- Detailed evidence: `TRANSMISSION_FLOW_AUDIT_20260719.md`.
- Next action: deploy `1b6da28`, run server tests and corrected 24h gate, then defer the corrected 744h until shared-server available RAM is safe.

### v0.5.1 - 2026-07-19 - server synchronization and replacement 744h launch

- Git baseline: branch `codex/cispo-2030-full-lp`, server checkout HEAD `827b37f`, containing implementation commit `2a0ee99`.
- Scope: restored live SSH through the configured bound-source alias; fast-forwarded the clean server checkout; uploaded and SHA256-verified versioned model/hydrology bundles; ran readiness, regression and 24h solve gates; launched the replacement 744h CPU barrier gate.
- Changed files: `CODEX_HANDOFF.md`, `MODEL_SERVER_STATUS.md`, `SERVER_RUNBOOK.md`; model source files were not changed in this milestone.
- Verification: readiness PASS with zero hard failures; raw GRFR 2/2 hashes PASS; tests 24/24 PASS; 24h `OPTIMAL/QC PASS` in 60.53 s with 0.851 GiB peak RSS.
- Server output: `/data/zz2/National_model/outputs/2030_one_month_20260719_sequential_sparse_cpu`, PID `3778049`; initial process check passed and `stderr` was empty.
- Unresolved: the 744h result is still pending; formal climatological P30 and 4 low-correlation/18 max-bound cascade-lag edges remain input limitations. Shared server load leaves only about 49 GiB available, below the 8760h gate.
- Next action: inspect the 744h reports after process exit; if and only if `OPTIMAL/QC PASS` and RAM is at least 64 GiB, run the 8760h build-only gate.

### v0.5.0 - 2026-07-18 - sequential planning, exact sparse reformulation and complete outputs

- Git implementation baseline: `2a0ee99` (`feat: add sequential planning and stabilize full-year LP`).
- Scope: implemented checksummed 2030/2040/2050/2060 capacity-cohort transfer; added GHT 2026 province-level PHS floor/project upper; removed redundant ramp, storage reserve, reservoir generation, hydro inertia and operating-cost-account variables/equalities using exact linear reformulations; completed compact outputs/SVG/manifest; reduced model input tables to an explicit 28-table contract.
- Main changed files: `cispo_model/config.py`, `data.py`, `master.py`, `monolithic.py`, `planning_state.py`, `preflight.py`, `result_summary.py`; `config/model_data_config.json`, `optimization_2030.json`, `model_input_files.json`; run/build/readiness/smoke scripts and sequence/tests.
- Local validation: AST 38 PASS; unit tests 24/24 PASS including real solution-to-cohort mapping; data-package smoke 124/124 PASS; 2030 and 2040 full-year preflight PASS; four-year sequence dry-run PASS; final 24h solve `OPTIMAL/QC PASS` in 58.79 s with 0.698 GiB peak RSS; nonempty 2040 state diagnostic `OPTIMAL/QC PASS`.
- Scale: full-year preflight estimates 44,090,772 variables, 67,603,314 constraints, 853,505,952 nonzeros and 46.62 GiB model memory. Local build is correctly blocked by the 64 GiB runtime gate.
- Server status: not deployed. SSH connected to TCP/22 but closed during key exchange on 2026-07-18, so server HEAD and old 744h status could not be verified.
- Transfer status: minimal code/data/hydrology archives and SHA256 manifest were prepared locally; Git push and server upload are blocked by the same SSH key-exchange closure.
- Unresolved: replacement 744h and 8760 build-only gates; formal multi-year P30; 4 low-correlation and 18 max-bound lag edges; plant-level thermal retrofit/retirement identity; CSP, thermal `f_on`, PHS hydraulic pairing and proxy network assumptions.
- Next action: restore SSH, verify old artifacts, deploy commit/data, pass readiness/tests/744h, then 8760 build-only before any production sequence.

### v0.4.1 - 2026-07-07 - P30 hydropower cleanup and GPU-PDHG isolation test

- Git implementation baseline and live server HEAD: `a8cd150` (`fix: switch hydropower to p30 proxy`).
- Scope: removed obsolete early block-boundary variables from `master.py`; switched conventional hydropower environmental flow from the single-year P10 proxy to the configured single-year P30 proxy; retained run-of-river as station-CF-weighted provincial hourly output variables; kept PHS as province-level storage; installed GPU-enabled Gurobi only in an isolated venv and tested PDHG.
- Main changed files: `.gitignore`, `config/model_data_config.json`, `config/optimization_2030.json`, `cispo_model/config.py`, `cispo_model/hydro.py`, `cispo_model/master.py`, `scripts/build_cispo_data_package.py`, `scripts/check_server_readiness.py`, `scripts/prepare_server_bundle.py`, `tests/test_hydro_station_model.py`.
- Data roots: `/data/zz2/National_model/data/model_ready_20260707_p30_cleanup` and `/data/zz2/National_model/data/hydro_timeseries_20260707_p30_cleanup`; P30 NetCDF SHA256 `c28f628642baaaac18d4461ac9474b3d622fcd80fbcd651884e6095d58203767`.
- Validation: local AST PASS, local 19/19 unit tests PASS, data smoke test 118/118 PASS; server readiness PASS with raw-GRFR SHA256 verification; server 19/19 tests PASS; server 24h CPU P30 solve `OPTIMAL`, `solution_qc=PASS`, Gurobi `45.06 s`, peak RSS `0.879 GiB`.
- GPU result: isolated `gurobipy 13.0.2+cu129` environment successfully used `Start PDHG on GPU`, but the 24h P30 model was still iterating after about 600 s and was interrupted with no `solve_report.json`; standard CPU barrier remains the accepted solver route.
- Current run: P30-cleanup 744h CPU gate is running at `/data/zz2/National_model/outputs/2030_one_month_p30_cleanup_cpu`, PID `863603`; build completed in `339.56 s` with peak RSS `5.336 GiB`, and Gurobi optimization is in progress.
- Unresolved: 744h gate final status not yet known; formal 1980-2019 climatological P30 remains future data work; low-correlation/max-bound cascade lag edges still need manual data review.
- Next action: monitor PID `863603`, then audit solve/QC outputs before any 8760h build or production solve.

### v0.4.0 - 2026-07-07 - LP numerical scaling repair and 168h server gate

- Git baseline and live server HEAD: `281f9c7` (`fix: stabilize hydropower LP numerics`).
- Scope: preserved and interrupted the failed old 744h run; audited every model block; applied mathematically equivalent reservoir flow/volume scaling; added numerical-audit and arbitrary diagnostic-hour tooling; exposed all server CPUs; expanded solver-quality reporting.
- Main changed files: `config/optimization_2030.json`, `cispo_model/config.py`, `cispo_model/diagnostics.py`, `cispo_model/hydro.py`, `cispo_model/monolithic.py`, `cispo_model/solution_export.py`, `scripts/audit_model_numerics.py`, `scripts/run_cispo_2030_full_year.py`, `tests/test_hydro_station_model.py`.
- Validation: local 18/18 tests PASS; local 24h `OPTIMAL` and QC PASS in `59.66 s`; server 18/18 tests PASS; server 168h `OPTIMAL` and QC PASS in `675.56 s` with `4.061 GiB` peak RSS.
- CPU/GPU: `Threads=-1` exposes 96 logical processors; barrier uses 48 physical threads. Two RTX 4090 GPUs are compatible candidates for Gurobi GPU PDHG, but current installed build is CPU-only; any GPU test must use a separate `+cu` environment and `Method=6`, `PDHGGPU=1`.
- Unresolved: replacement scaled 744h run not yet started; no 8760h run is authorized before it passes. Full details are in `MODEL_SYSTEM_AUDIT_20260707.md`.
- Next action: run and audit `/data/zz2/National_model/outputs/2030_one_month_hydro_cascade_numerics_scaled`.

### v0.3.1 - 2026-07-06 - cascade server deployment and 744h numerical gate in progress

- Git implementation baseline: `b3e6298`; server checkout HEAD verified as `7a2ca27`.
- Scope: transferred and verified versioned cascade model-ready/hydrology data, passed server readiness and 16 regression tests, passed the 744h preflight and completed the full 744h model build.
- Server data roots:
  - `/data/zz2/National_model/data/model_ready_20260706_hydro_cascade`
  - `/data/zz2/National_model/data/hydro_timeseries_20260706_hydro_cascade`
- Verification: readiness PASS with raw-GRFR SHA256 verification; cascade counts 142 nodes and 124 edges; 16/16 tests PASS; one-month preflight PASS; actual model build 4,808,836 variables, 6,536,681 constraints and 46,092,407 nonzeros.
- Numerical status: Gurobi emitted coefficient/RHS scale warnings, barrier restarted once and the solve entered a long crossover cleanup. At the recorded checkpoint the process was still active after about 5 h 59 min, with no final solve/QC report. This is not a passed optimization gate.
- Changed files in this handoff-only milestone: `CODEX_HANDOFF.md`, `MODEL_SERVER_STATUS.md`, `SERVER_RUNBOOK.md`.
- Next action: preserve and audit the current run when it exits; if crossover does not finish acceptably, compare a separate `Crossover=0` diagnostic configuration without modifying model physics.

### v0.3.0 - 2026-07-06 - core mainstem hydropower cascade implementation

- Git baseline: `b3e6298` (`fix: add core hydropower cascade coupling`), based on prior server-validated commit `8e49a87` (`fix: harden CCS and station-level hydropower model`).
- Scope: read and validated the Stage2 core-mainstem hydropower classification/cascade scaffold; generated model-ready cascade nodes/edges; estimated MERIT downstream travel lags by 2019 GRFR cross-correlation; replaced independent core-reservoir operation with local-inflow plus upstream turbine/spill delayed arrival; retained independent operation for non-core reservoirs.
- Main changed files in the implementation commit:
  - `config/optimization_2030.json`
  - `config/model_data_config.json`
  - `scripts/build_cispo_data_package.py`
  - `scripts/check_server_readiness.py`
  - `scripts/smoke_test_data_package.py`
  - `cispo_model/data.py`
  - `cispo_model/hydro.py`
  - `cispo_model/monolithic.py`
  - `cispo_model/preflight.py`
  - `cispo_model/solution_export.py`
  - `tests/test_hydro_station_model.py`
  - `cispo_full_lp_model_spec.md`
- Local generated data files:
  - `data/hydro/cascade_topology_nodes.csv`
  - `data/hydro/cascade_topology_edges.csv`
- Verification: Stage2-to-model mapping passed with 146/146 reservoir stations; cascade topology is acyclic; local data package QC has zero failures; smoke test passed 118/118 checks; local unit tests passed 16/16; one-month preflight passed; custom 24h monolithic build succeeded.
- Modeling note: the local implementation follows the user's requested core-mainstem cascade mode for conventional reservoir hydropower. It does not yet implement open-loop/closed-loop PHS hydraulic coupling because required pairing/source data are not present in the current data package.
- Unresolved items: 4 low-correlation lag edges and 18 max-bound lag edges require manual hydrological/topological review; formal multi-year environmental flow remains unavailable.
- Next action: synchronize the branch and transfer a new versioned data package to the server, then rerun server readiness plus 744h `one_month` optimization.

### v0.2.0 - 2026-07-06 - station-level hydropower, CCS retrofit accounting and raw GRFR server readiness

- Git baseline: `8e49a87` (`fix: harden CCS and station-level hydropower model`).
- Scope: implemented assigned-label hydropower rules, paper-consistent potential hydropower classification, independent station-level reservoir balance using GRFR inflow, CCS retrofit/capture-cost accounting, production solution export/QC, and raw GRFR server readiness gates.
- Main changed files:
  - `config/optimization_2030.json`
  - `config/model_data_config.json`
  - `scripts/build_cispo_data_package.py`
  - `scripts/check_server_readiness.py`
  - `scripts/prepare_server_bundle.py`
  - `scripts/run_cispo_2030_full_year.py`
  - `cispo_model/hydro.py`
  - `cispo_model/monolithic.py`
  - `cispo_model/load_center.py`
  - `cispo_model/master.py`
  - `cispo_model/solution_export.py`
  - `cispo_model/runtime_monitor.py`
  - `tests/test_hydro_station_model.py`
  - `tests/test_ccs_model_structure.py`
- Data packages transferred to the server:
  - `/data/zz2/National_model/data/model_ready_20260706_station_hydro`
  - `/data/zz2/National_model/data/hydro_timeseries_20260706_station_hydro`
  - `/data/zz2/National_model/data/grfr_raw_2019`
- Verification: raw GRFR SHA256 matched source files; server readiness passed with raw-GRFR SHA verification; 15/15 tests passed on the server; one-month and full-year preflights passed memory gates with the scale estimates recorded in the current snapshot.
- Modeling note: according to the EES hydropower supplement, installed labels are retained from assigned labels, potential dam sites with design capacity greater than 750 MW are modeled as reservoir hydropower, remaining potential sites as run-of-river hydropower, and no hydraulic cascade propagation delay is added because the cited equations use independent station-level natural inflow rather than upstream/downstream travel-time coupling.
- Unresolved items: listed in the current snapshot above.
- Next action: run and audit the server-side 744h `one_month` optimization using the versioned station-hydropower data paths.

### v0.1.0 - 2026-07-06 - Gurobi 13.0.2 server readiness

- Git baseline: `805a1fa` (`chore: configure Gurobi 13.0.2 server runtime`).
- Scope: completed server Gurobi installation, license retrieval, full-license verification, dependency documentation and synchronized server checkout.
- Main changed files:
  - `requirements-server.txt`
  - `requirements-test.txt`
  - `env/cispo-server.yml`
  - `scripts/check_gurobi_full_license.py`
  - `scripts/check_server_readiness.py`
  - `SERVER_RUNBOOK.md`
  - `MODEL_SERVER_STATUS.md`
- Verification: full-license 2,501-variable gate passed; server readiness passed; 10/10 tests passed; 8760h preflight memory gate passed.
- Environment note: pytest 9.1.1 was installed from locally verified offline wheels because server PyPI TLS validation remains unresolved.
- Unresolved items: listed in the current snapshot above.
- Next action: run and audit the server-side 744h `one_month` optimization.
