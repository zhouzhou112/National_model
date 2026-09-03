# CISPO 2030/8760 server runbook

## 2026-09-03 14:53 current override：只允许最终v6单路Stage A

- 唯一候选提交为`af96fb6361af4bb09dd90513c48ad76796f30a7d`，profile只能是
  `barrier_stagea_final_full_year_cloud_v6_threads32`；禁止再次启动32/64对照、Stage B或第二个求解。
- 参数锁为`Method2/Threads32/Presolve2/Aggregate1/Crossover0/SolutionTarget1/BarConvTol1e-2/
  FeasibilityTol1e-6/OptimalityTol1e-6/NumericFocus1/ScaleFlag2`且无`TimeLimit`。SoftMemLimit必须由当前Slurm
  cgroup按`min(0.85*limit, limit-64GiB)`计算并写入launch identity。
- 启动前必须确认队列空、目标根不存在、Gurobi13/WLS可用、分区/计费明确，并在新构建中复核raw
  `50,907,234 rows / 41,458,383 cols / 492,835,195 nnz`、Fingerprint`0x94cf2e50`和解压MPS流SHA256
  `8216816027025ffc16eb7fb80ce55d6beb822242f03f1a24433102248603713a`；不匹配即停止，不允许通过改模型绕过。
- 终态只看`terminal_status.json`三类：接受、保全待复核、无可用Stage A。接受要求runner rc0、primal门禁、
  原单位QC、accepted checkpoint及闭合result manifest；dual不达标只禁止影子价格发表。任何EXIT都必须留下
  terminal JSON；计划内停止仍只创建精确`STOP_REQUESTED`，禁止直接`scancel`破坏保全。

## 2026-09-03 01:29 current override：0.01停止容差与科学验收必须解耦

- `4466067/4466068`已在Barrier 0步受控停止，当前无活动线程对照。归档原MPS完整、解压流SHA一致；没有
  Barrier迭代就不存在可续接BarX/BarPi。不得把Slurm `FAILED/2`误判为求解器失败。
- 下一次提交前必须新建并锁定canonical 32/64 profile：`BarConvTol=1e-2`，其余物理模型、输入、
  `Method=2/Presolve=2/Crossover=0/SolutionTarget=1/NumericFocus=1/ScaleFlag=2/Aggregate=1`保持一致；
  不得再用`BarConvTol<=1e-8`作为direct scientific acceptance的代码门槛。
- 科学接受改为两层：第一层允许Barrier按1%宏观容差停止；第二层在原变量/原单位上报告并fail-closed检查
  供需平衡、功率/能量/容量、水库、储能、输电、碳约束，以及primal/dual residual、complementarity和
  实际相对primal-dual gap。阈值必须显式版本化，不能静默继承`10*BarConvTol`而把complementarity上限
  放到0.1，也不能反向要求`1e-9`才算科研结果。
- 重启后继续32/64同模型对照、无自动结束时间；只在同Presolve/Ordering阶段或同Barrier迭代比较wall、
  Work、残差、gap、RSS和factor指标。旧日志给出的15.71天只是`1e-2`代理，不是新运行时限承诺。

## 2026-09-02 23:26：8760h线程对照运行与受控停止（已被上方终态覆盖）

- 正在运行：`4466067`=`Threads32, Slurm89 CPU/520G, SoftMemLimit520 decimal GB, m4cg1602`；
  `4466068`=`Threads64, Slurm120 CPU/700G, SoftMemLimit680 decimal GB, m4cm1804`。两者23:24:12同秒启动，
  `TimeLimit=UNLIMITED`。发布根与完整SHA见`CODEX_HANDOFF.md`最新snapshot；禁止更新运行中release。
- 每4小时检查`squeue/scontrol/sstat/sacct`、两control/output根、stderr、build/archive、Gurobi日志与
  telemetry。只在相同阶段/相同Barrier迭代比较runtime/work/residual/gap；检查raw/presolved维度、
  Fingerprint、Ordering、DenseCols、AA' NZ、Factor NZ/Ops/memory和MaxRSS。SoftMem触发时只评价资源包。
- 用户未授权自动停止或后续实验。不得`scancel`、改参、重启、Stage B或下一年份。计划内停止只执行：
  `touch <release>/run_control/<exact-case-id>/STOP_REQUESTED`。wrapper若仍在build/archive会等待
  `solver_start`，随后SIGTERM Python并等待checkpoint/preservation完成；以`return_code.txt`、
  `terminal_status.txt`、solve/QC/checkpoint/preservation manifests共同判终态。
- “可续接”边界：original MPS/PRM和精确LP身份可重建模型，BarX/BarPi可作精确身份验证后的热启动；
  Gurobi未公开的中途Barrier因子分解/迭代器内部状态无法保存为原位续算文件。节点硬故障/OOM可能只留下
  已落盘模型、日志和遥测，缺失checkpoint不得记为0或COMPLETE。

## 2026-09-02 22:40修复后云端资源与Presolve边界

- 实现提交`cff905476ed2811a26b16e86f772eb5b91f9357d`已闭合精确零水库上界、nonbasic终态
  KKT/relative-gap硬门禁和parent→new physical LP白名单并双推送；在部署该不可变提交、通过Gurobi13
  小门禁前，不提交付费8760h作业。
- 作者提供的计费规则是`billable_cores=max(requested_cores,memory_equivalent_cores)`：例如120G内存即使
  `--cpus-per-task=1`也可能按12核计费。每次提交前必须重新读取分区`DefMemPerCPU/MaxMemPerCPU`，先用
  `sbatch --test-only`或最短可行探针核实`ReqTRES/AllocTRES/billing`；成本表按计费核心数而非Gurobi
  `Threads`计算。
- “构建+presolve便宜档”只能拆成两类：①Python build并保存原始MPS，供后续科学作业读取；②单独
  `Model.presolve()`保存reduced MPS，用于内存、ordering、factor和Barrier吞吐诊断。后者没有Gurobi
  内部uncrush映射，不能直接恢复原变量科学解，也不保证与`optimize()`内部presolve完全相同；不得作为
  32/64核正式Stage A的续算起点。
- 构建通常以Python侧工作为主、增加线程收益有限，但Gurobi presolve是否并行及其峰值内存都不能靠假设。
  已知旧8760 build峰约48.574GiB，独立presolve峰值未测；`Model.presolve()`还可能同时持有original与
  reduced model。低价准备档应先以实测峰值加安全余量选择内存折算档，不能直接假定“presolve低内存”。
- 后续32核/64核正式比较必须读取同一个原始MPS，使用同一代码/数据/参数/内存上限、内部`Presolve=2`，
  分别独占两个节点或严格顺序运行，并比较wall/work、ordering/factor、Barrier残差轨迹及峰值RSS。Stage B
  不自动执行；科学接受仍要求原始模型终解、原单位QC和完整manifest。

## 2026-09-02 21:08终态覆盖：2160h行缩放资格门禁失败

- 唯一tag `2030_base_2160h_stagea_capacity_link_rows8192_barrier32_20260902_v1`已由guard按冻结门槛受控
  终止，状态`FAIL_TERMINATED`。不得重启同标签、放宽75GiB/95%门槛、恢复Stage B或启动其他求解。
- raw结构和presolved NNZ反回归通过、无数值警告；但ordering阶段RSS超过75GiB并继续到86.382GiB，
  host used达到99.008%。任务未进入Barrier，Factor指标和iter30证据缺失，缺失值不得记作0或PASS。
- 当前无本项目solver/guard/tmux，checkout仍clean `ba8e09f`。作者已授权每3小时自动巡检并依据实测内存
  逐级扩大本地测试，但本结果不授权原样重启2160h、直接启动8760h或解释为数值缩放性能结论。

### 终态后的唯一续测序列

- heartbeat `3-stage-a`每3小时执行一次；先核实终态、服务器资源、Git/输出身份及是否存在其他CISPO
  进程。任何时刻只允许一个CISPO求解，外部用户任务不得停止，swap实时活动或memory PSI异常即等待。
- 启动下一求解前先在隔离分支补齐GPTPro复核指出的三项高优先级缺口：水库`release_upper`精确零上界、
  非basic终态`ConstrResidual/DualResidual/ComplVio/relative gap`硬门禁、parent→new physical LP机器可读
  差异白名单；完成单元测试、24h等价性与配置审计后才可部署新不可变提交。
- 第一组性能证据使用同一提交、同一32物理核、同一数据/时间窗/参数的scaled与`physical_v1`匹配对照，
  除年度容量联结行缩放外不得改变其他因素。鉴于2160h ordering已达到86.382GiB进程组RSS，首个候选窗
  从1488h/start2880开始；两条顺序运行，均使用新tag/new roots和原guard，不得并发。
- 只有scaled/physical均通过资源与结构门禁、scaled显示可重复收益且峰值内存留有保守余量，才顺序考虑
  `2160h -> 4320h -> 5880h`。任一级内存/数值失败即停止扩大并诊断；严格生产容差验证必须在可承载的
  最大已通过尺度上闭合，最终仍需一轮严格2160h才可讨论8760h。Stage B不在序列内，云端8760h不会自动启动。

## 2026-09-02 current override：唯一2160h Stage A行缩放资格路线

本节覆盖下方过期的活动任务/队列指令，但不删除其历史事实。当前唯一允许推进的数值路线是
`annual_capacity_link_rows_8192_v1`：仅将VRE/ROR年度可用量零右端约束的**整行**乘以
`s=2^-k`；`k`为`0..13`中保证缩放后最小非零系数`>=1e-6`的最大整数，正式2160h/8760h要求
两族均`k=13`。Wave和省内负荷中心容量行不得缩放。变量、目标、边界、矩阵支撑与可行域不变；
解释对偶和松弛时必须使用`pi_physical=s*pi_solver`与`slack_physical=slack_solver/s`，reduced cost不变。

### 固定服务器身份与启动前门禁

- 唯一生产checkout是`/home/zz2/National_model_server/repo`；
  `/data/zz2/National_model/repo`是旧NTFS克隆，禁止fetch、checkout、部署或启动。当前已核实前者为
  detached、clean`ba8e09f97a6526e299f807eb9be8c579a217caeb`且无本项目solver；实现提交为
  `122642f616b7abb2ad137250721a937e83a6f524`。服务器精确提交测试`256/256`通过。
- 形成并推送精确提交后，只允许clean、仓库顶层且owner为`zz2`的正确checkout以该完整SHA运行。
  `EXPECTED_GIT_SHA`必须是冻结的完整SHA；不得用分支名、短SHA或运行中checkout更新替代。
- 启动前必须再次确认无CISPO solver/recovery/watcher、Gurobi恰为`13.0.2`、`MemAvailable>=100 GiB`、
  `vmstat si/so=0/0`且memory PSI正常。CPU`0-31`必须映射为32个不同物理核，NUMA0/1各16核，launcher
  affinity包含全部CPU；solver启动后`Cpus_allowed_list`必须精确为`0-31`。任一条件不满足即fail closed。
- 先用一个短时detached `tmux` probe记录PID/PGID/SID/cgroup，断开SSH后重连，核实同一进程身份并等待
  自然rc0；`Linger=no`时不得把user systemd当成持久化保证。该probe已在
  `run_control/tmux_persistence_probe_sJrFGC`通过（同PID、6个heartbeat、自然rc0）。真实launcher的
  normal/guard早退/重复信号/flock/guard超时探针也分别得到`0/96/129/90/97`且无孤儿进程。
- 唯一launcher为`scripts/run_fixed_server_stagea_row_scaling_2160.sh`，固定2160h/start2880、Base、
  `barrier_checkpoint_fixed_server_host_memory_95_v2`、`annual_capacity_link_rows_8192_v1`、
  `Method=2/Threads=32/Presolve=2/Crossover=0/BarConvTol=1e-2/FeasibilityTol=OptimalityTol=1e-5/
  NumericFocus=1/ScaleFlag=2/Aggregate=1`、`host_memory_soft_limit_fraction=0.95`、整机95%保护且无
  `TimeLimit`。JSON中的`soft_mem_limit_gb=80`仅为fallback/provenance；runner必须把有效Gurobi
  `SoftMemLimit`覆盖为`physical_memory_bytes*0.95/1e9`十进制GB。只可在完成持久性probe后以detached `tmux`
  调用，例如先设置`EXPECTED_GIT_SHA=<完整提交SHA>`与唯一`TAG`，再从正确checkout执行该脚本。
  output/control根必须位于仓库外、彼此不同且不嵌套、启动前均不存在；全局`flock`不得绕过。
- launcher/guard必须共同存活：guard早退时终止且reap求解进程组；HUP/INT/TERM重复到达仍须转发；solver
  结束后guard最多等待60秒再单独TERM/KILL。保留`events.log`、PID/PGID/SID/lstart/cgroup、CPU topology、
  resource telemetry、stdout/stderr及各return code；不得把缺失值写成0或手工伪造PASS。
- `vmstat 1 4`的首个数据行是since-boot平均值；提交`ba8e09f`明确忽略该行，只要后续三个实时区间任一
  `si/so`非零仍返回94。禁止改回会永久误判历史swap的`NR>2`，也禁止跳过真实swap压力检查。
- 2026-09-02 20:04:49可用内存自然升至`100.304 GiB`；20:05:24已创建正式唯一tag
  `2030_base_2160h_stagea_capacity_link_rows8192_barrier32_20260902_v1`并在detached tmux
  `cispo_stagea_rowscale_2160_v1`中启动。runner/PGID/SID=`384500`、guard=`384507`、实际affinity
  `0-31`，启动时可用内存`100.292 GiB`。运行期间禁止切换checkout或再启动任何CISPO求解。
- 20:07:37 guard仍为`PENDING`，进程组RSS约2.97 GiB、solver与guard stderr均0；21:04该任务在ordering
  阶段因内存门禁终止，未进入Barrier。后续不得复用该tag；每3小时heartbeat `3-stage-a`按上方续测序列
  执行，绝不恢复旧Stage B/Case2 watcher或自动启动Stage B。

### 2160h资格判定与后续边界

- raw结构必须精确为`12,520,914 rows / 10,398,783 vars / 126,724,678 nnz`；presolved nnz
  `<=107,398,350`、DenseCols`<=38,982`、`AA' NZ<=2.17035e8`、Factor NZ`<=6.28845e9`、
  Factor Ops`<=2.19345e14`、日志factor memory`<=63 GB`，且不得出现数值警告。
- guard读取**第一个**`iteration>=30`遥测记录：累计runtime`<=12,000 s`、Work`<=18,961.075`、
  进程组RSS`<=75 GiB`才通过速度/内存门槛。runtime/Work一经通过即锁定；之后发生内存越界、警告、
  身份漂移或其他fail-closed条件仍判失败。Factor指标只是结构反回归，不单独构成加速证据。
- 本地先验仅为`290 passed, 1 skipped`及24h/start2880 physical/scaled双`OPTIMAL`、相同目标
  `2112716.676624984 million CNY`、原单位QC双`PASS`。本候选2160h已在Barrier前因内存终止；不得据24h wall差异
  宣称32线程或8760h已加速。
- 只有2160h上述门禁通过，才可另行准备8760h Stage A；正式profile为
  `barrier_checkpoint_full_year_cloud_v4`，`Threads=32`、`soft_mem_limit_gb=600`且无`TimeLimit`。Stage B
  不是必需步骤，也不属于
  该launcher/guard/sequence：不得自动启动、不得设置等待Stage B的watcher、不得把Stage A完成解释成
  Stage B授权。作者以后若单独要求Stage B，必须新任务、新身份和独立验收。
- 本任务已为落实作者“Stage B非必需、先解决Stage A”的决定而**有意停止**旧Stage B进程组和Case2
  watcher；当前无活动solver。这是对下方18:04“外部SIGTERM原因未解析”在当时证据范围内所作记录的
  后续纠正，不删除或改写原历史条目，也不得恢复旧Stage B/Case2自动链。

## 2026-09-02 18:04 Stage B中断后的安全边界

- `2030_base_2160h_case1_v3_stage_b_20260901_v1`是已中断现场：return code143、solver status11、
  SIGTERM、SolCount0。保留全部output/control，不覆盖、不换标签盲目重跑、不把solve report写成完成。
- host guard0、无OOM/遥测/stderr异常；终止原因未解析。任何重跑前必须改用可证明脱离临时SSH
  session/cgroup生命周期的持久launcher，并记录unit/cgroup和信号来源，否则可能再次丢失长跑。
- Case2 watcher已退出且未claim；Stage B缺QC/manifest，因此Case2严格阻断。不得手工绕过门禁或
  用当前失败root伪造PASS。
- 当前无本项目solver、available约96GiB并不构成自动启动授权。先让作者在“重跑严格Stage B、
  改用另一严格收尾路线、先做独立数值筛选”之间决定；任何选择都需新标签和完整身份/资源门禁。

## 2026-09-02 09:59 当前队列与CF候选终态规则

- `cf_744_stagea_pair_20260901_v1`已终态：baseline/candidate runner rc0、guard0，checkpoint完整；
  保留原目录，不重启或补跑744h候选Stage B。`CF=1e-4`在744h完整Stage A的迭代、时间、work units
  和主RSS均劣于1e-6，故不凭该尺度晋级；但不得把它外推为2160h/8760h必慢。当前Case1/Case2
  完成后可按`codex/numerical-stability-engineering-v2`的单因素门禁做2160h有限Barrier结构筛选。
- 两条Crossover0结果都只是`ENGINEERING_BARRIER_CHECKPOINT_ONLY`，solution contract `HARD_FAIL`
  且raw QC失败。不要把Gurobi `OPTIMAL`写成严格完成，也不要用任一checkpoint生成规划状态。
- 当前唯一CISPO大任务仍是`2030_base_2160h_case1_v3_stage_b_20260901_v1`。09:59同一
  PGID3946395/Python3946400处于PPushes（约2.418M remaining、PInf1633.873）；无终态文件，继续
  只读监测，不改参/重启/终止。
- Case2 watcher PID881511继续幂等等待。不得手工绕过`Stage B rc0 + QC PASS + manifest complete +
  clean6065bfb + no competing solve + used<90% + available>=96GiB + PSI normal`门禁。
- 当前available约44GiB，虽used未达90%，但不足以安全加入新的744h配对；两张GPU有本任务外客户。
  不启动新测试、不抢GPU、不降低Case2的96GiB准入。下次4小时巡检重算可用量并优先完成
  Stage B→Case2既定序列。

## 2026-09-01 21:44 当前活动744h完整Stage A配对

- control root：`/home/zz2/National_model_server/campaign_tools/cf_744_stagea_pair_20260901_v1`；
  supervisor PID1045122。标签/PGID为`2030_base_744h_cf1e6_stage_a_concurrent_20260901_v1`/
  1045145和`2030_base_744h_cf1e4_stage_a_concurrent_20260901_v1`/1045150。
- 两条均应读回744h/start2880、Method2/Threads16/Presolve2/Crossover0、BarConvTol1e-2、
  Feas/Opt1e-5、NF1/Scale2、无TimeLimit/SoftMemLimit并带engineering checkpoint flags。唯一LP差异
  是CF阈值；任何其他快照漂移立即报告，不重启或换标签。
- 每条2秒monitor现引用`campaign_tools/case1_stage_b_20260901_v1/scripts/monitor_case_resources.py`；
  必须检查其telemetry stderr为空和summary持续更新。pair supervisor另有2秒host/RSS TSV及95%保护。
- Stage A终态只评价Barrier runtime/iterations、残差、Factor NZ/Ops、checkpoint完整性和RSS；Crossover0
  engineering结果不做科学接受/规划状态。候选若无稳定收益则否决；若晋级，每条Stage B必须读取各自
  checkpoint并做严格QC，禁止交叉resume。

## 2026-09-01 21:41 744h CF筛选终态处理

- 两个既有744h标签均已终态status7/5 Barrier iterations/runner rc2。该rc2是runner对
  `ITERATION_LIMIT`的返回；保留现场，不重启、不补QC、不把它写成失败求解或科学结果。
- 比较结论固定为候选1e-4的Factor NZ -2.24%、Factor Ops -6.14%、并发solver -7.10%、
  process-tree RSS约-1.74%；raw/presolved NNZ仅约-0.05%。这是`PROMISING_MODEST`筛选信号，后续
  只有隔离744h完整Stage A+B及严格QC通过才可推广。不得与Annual Energy Coordinate同时启用。
- per-case `telemetry.stderr.log`记录monitor脚本路径不存在；不得把相应resource summary缺失值记为0。
  pair级`resource_monitor_pair.tsv`、各自`solver_telemetry.jsonl`、`solve_report.json`和`time.txt`
  可用于本轮证据。未来外部launcher应从campaign tool目录部署monitor副本或引用已验证绝对路径。
- Stage B现在处于PPushes而非DPushes：PPush remaining从6755240开始。仍使用原primal/dual start的
  同一Crossover，不是重跑Barrier；只有runner rc/solve report/QC/manifest齐全才算终态。Case2门禁
  在此之前保持`WAITING_STAGE_B`，不得人工绕过。

## 2026-09-01 21:04 CF阈值配对筛选与Case2队列

- 配对控制根：`/home/zz2/National_model_server/campaign_tools/cf_744_pair_20260901_v1`；supervisor
  PID写在`run_control/supervisor.pid`。两条run_control标签为
  `2030_base_744h_cf1e6_factor5_concurrent_20260901_v1`和
  `2030_base_744h_cf1e4_factor5_concurrent_20260901_v1`。操作前核对PID/PGID/创建时间/命令行；
  不重启、不改标签、不把5步ITERATION_LIMIT当作失败或科学解。
- 两条都是744h/start2880、Method2/Threads16/Presolve2/Crossover0/BarIterLimit5、NF1/Scale2、
  无TimeLimit/SoftMemLimit；唯一差异是`coefficient_zero_tolerance=1e-6`对`1e-4`。并发屏幕只能比较
  presolve维度、Factor NZ/Ops、每步轨迹、警告和RSS；墙钟差异须在隔离复测后才能称加速。
- pair控制器每2秒记录主机内存/PSI及两PGID RSS，达到95%只终止这两条新筛选，不触碰Stage B。
  缺失遥测不得记为0；终态检查各自`return_code.txt`、build/solve report、stdout/stderr、time和
  resource summary。候选物理误差报告保存在本地隔离worktree，不得据误差小跳过性能门禁。
- Case2即时队列根：`campaign_tools/case2_after_stage_b_20260901_v1`，watcher PID在
  `run_control/watcher.pid`、状态在`status.json`。它每60秒只做轻量门禁；Stage B rc0/QC PASS/
  manifest完整、repo clean6065bfb、无竞争求解、host used<90%、available>=96GiB、PSI正常时，
  调现有生产launcher启动一次tag`2030_base_2160h_case2_v3_barrier32_screen_20260901_v1`。
  `ALREADY_CLAIMED`只能读取原现场；BLOCKED/LAUNCH_FAILED不得换标签盲目重试。
- 人类可见heartbeat仍每4小时。Case2启动后核实实际快照为2160h/start2880、Threads32、Crossover0、
  BarConvTol1e-2、Feas/Opt1e-5、TimeLimit21600s、SoftMemLimit空和95%保护；不得自动Stage B或其他算法。

## 2026-09-01 18:30 年度账户坐标候选与轮询规则

- 活动生产Stage B继续使用clean6065bfb物理GWh坐标；不得部署或热切换隔离候选4814c2e。
- 候选只允许在当前Stage B终态后，以新checkout/新标签执行一次同2160h/start2880 Barrier16
  Stage A+B A/B；候选Stage B必须使用候选自产checkpoint，禁止读取当前物理坐标checkpoint。
- 候选必须显式传`config/formulation_profiles/annual_energy_coordinate_8192_v1.json`；默认配置仍是
  物理GWh。保持原solver profiles、线程、容差、无SoftMemLimit及整机95%保护，不能同时改其他参数。
- 轮询automation `2160h-stage-b`现为每4小时；服务器独立2秒资源采样保持不变。只读巡检不得因
  周期变长而改进程、清理现场或降低终态验收要求。

## 2026-09-01 17:36 Stage B接续状态：Crossover运行中

- exact resume已通过：`primal_dual_start_input.json`存在且identity/Fingerprint/order/vector门禁全部PASS；
  日志明确使用完整primal+dual start vectors直接做Crossover，禁止再把本轮描述为“仍待确认续接”。
- 同一PGID3946395/Python3946400当前处于DPushes；17:36剩余约222988、DInf约9.04。不得因DInf短期
  波动停止，也不得换标签、改参、重启、并行试算法或部署年度能量缩放。
- 资源/遥测正常，CPU Crossover时GPU空闲是预期行为。终态仍必须检查runner rc、OPTIMAL、solver
  contract、原单位QC全部hard checks及input/result manifests；当前没有这些终态文件，严格验收未完成。

## 2026-09-01 15:42 当前唯一活动任务：2160h Stage B

- 唯一允许标签：`2030_base_2160h_case1_v3_stage_b_20260901_v1`；source Stage A根只读，不得覆盖。
- production必须保持clean6065bfb。启动器位于
  `/home/zz2/National_model_server/campaign_tools/case1_stage_b_20260901_v1/scripts/`；不要从生产
  launcher补启动，也不要换标签重试。当前launcher3946098、solve PGID3946395/Python3946400，
  操作前必须重新核验创建时间和完整命令行。
- 参数固定Method2/Threads16/Presolve2/Crossover2/CrossoverBasis1/LPWarmStart2、Feas/Opt1e-6、
  NF2/Scale2、无TimeLimit/SoftMemLimit；整机95%保护及2秒采样不可关闭。
- build后首先检查`primal_dual_start_input.json`的科学输入身份、Gurobi版本、Fingerprint、raw维度、
  变量/约束完整顺序和向量hash；日志必须使用start vectors直接进入Crossover/cleanup，不能重跑Barrier。
- 终态只有runner rc0、solver contract PASS、原单位QC全部hard checks、input/result manifests有效时才是
  工程严格通过；2160h仍为TEST_ONLY。heartbeat `2160h-stage-b`后续已改为每4小时监测，终态后删除。

## 2026-09-01 13:59 当前活动状态更正

- `2030_base_2160h_case4_gpu_pdhg_unlimited_20260828_v2`已按作者要求以SIGTERM正常停止，
  `return_code.txt=143`、solve status=`INTERRUPTED`；该标签不得重启或换标签续跑。
- 原PGID1216966、Python1216969和telemetry1216967均已退出，GPU1已释放；GPU0上的其他客户
  不属于本任务，禁止操作。
- `case-4-gpu-pdhg` heartbeat已删除。后续若启动任何Barrier、Stage B或数值缩放对照，必须建立
  新标签并重新执行Git/输入身份、资源、唯一求解器和保护门禁；本次终态不得当作可复用解。

## 2026-08-28 19:10 完整8760h GPU0终态接续（不重启）

tag `2030_base_8760h_gpu0_pdhg_unlimited_20260828_v2`已18:23:22触发94%整机保护结束，
return_code=-9、terminal.reason=NEW_JOB_PRIORITY_HOST_MEMORY_SHED_94_PERCENT。
下方17:22是历史启动记录，不是当前活动状态；不要复用原PID702485操作，也不要新标签绕过占位重启。
当前没有针对此8760h的单独自动化；既有case-4-gpu-pdhg只监测仍在运行的2160h，不能误暂停。

完整control与7份输出已保全，25/25 SHA一致，见downloads/8760_gpu0_terminal_20260828_1910。
build_report表明完整模型已构建，actual_solver_params确认Infinity；日志停在presolve100s，
尚无GPU迭代/解/QC，GPU空闲是阶段现象，真正退出原因是共享主存压力。
后续先取得作者对资源安排的决定；不得自动停止2160h、取消94/95保护、缩小或另启求解。
指纹2acf0ca2与历史d16b4c7e不同，需另核等价性；不能凭相同维度直接宣称原LP逐项相同。

## 2026-08-28 17:22 完整8760h GPU0任务已启动，勿重复执行

作者授权并发尝试，当前tag为`2030_base_8760h_gpu0_pdhg_unlimited_20260828_v2`，
工具为`/home/zz2/National_model_server/campaign_tools/full8760_gpu0_20260828_v2`。
run_control与outputs均在服务器根的同标签目录。PID/PGID702485（操作前重核创建时间/命令），
生产clean6065bfb；不要套用只允许1..8759h且禁止并发的旧2160h launcher。

先查events、stdout/stderr、run.pid、process_identity、resource_pressure_summary/jsonl、
resource_monitor.tsv、telemetry.stderr、return_code/terminal；2秒资源采样在独立进程运行。
本轮full_year8760/start0，不是diagnostic8760。model_config_snapshot中numerics复用2160h无限时PDHG，
私有基础config仅启动准入96→1GiB；实际Params文件在建模后生成，必须见Infinity及GPU开始标志才确认。
GPU0约386MiB新上下文/GPU利用率0可仅是建模，不得据此终止。

旧2160h整机95%保护不改；新任务0.25秒检查94%整机占用后优先kill自身已核实组，
并记录guard_trigger.json，oom_score_adj500也只针对新job。不得操作其他用户桌面GPU0客户端。
明确Start PDHG on CPU时新supervisor只结束新job；不因时长/长尾/排名停止，不自动重试/缩小/StageB。
终态需另核solver状态、raw_solution_preservation、strict QC；.sol.gz原始值不是科研验收。

v1工具/control保留：启动器拼写错误返回125，在模型构建前退出，不能重复运行或作为算法失败。
详细命令/哈希和本地快照见downloads/8760_gpu0_launch_20260828_v2/README.md。
原2160h三小时自动化范围/频率未改变，本轮没有另建自动化；独立本地审计保持原流程。

## 2026-08-28 17:12 N50R5接续核验入口

平台已登录，cloud.paratera.com的账号管理/SSH入口显示NC-N50R5/scvk386；console.paratera.com/self-service/index
账号关系页确认同一绑定并标记在线。在线不代表有空闲卡或作业可调度；N50R5与N56R5不是同一资源区。
此次N50R5网页SSH仅返回connection closed，未执行终端命令；控制台GPU队列未返回。下一步核实登录入口/队列，
并核实首页约-4973元可用额度对应的信用/停机政策，不能直接把断连归因欠费。
获得可用入口后再只读查GPU型号、显存、资源配比和空闲卡；不从原bscc-m8的sinfo推断N50R5状态。
本次没有申请/开通/转区/修改绑定或提交试算。原任务和WLS文件保持不变；证据见资源查询记录的17:12补充段。

## 2026-08-28 17:03 查询账号资源的口径

通过paracloud-bscc-a8，只读运行id -Gn、sinfo -a -N、scontrol -a show partition -o、sacctmgr关联查询及squeue。
必须以用户组匹配AllowGroups且分区UP为准，不把可见别名/VIP或重叠节点重复算作可申请资源。
当前三分区M8_768-a/A8_768/A8_384；用户关联cpu=1280、MaxSubmitJobs=50。整节点内存不等于少核作业可得内存。
详细命令、内存限额和17:03:52快照见downloads/cloud_resource_inventory_20260828_1703/README.md。
全平台其他中心/GPU/价格须作者自行登录cloud.paratera.com后查询；当前Chrome登录页已保留。
此查询不授权开通资源、修改许可证或提交作业；选择GPU试验仍遵循下节费用授权与小LP验证流程。

## 2026-08-28 17:00 收敛比较复现（不操作服务器求解）

本地downloads/pdhg_barrier_comparison_20260828_v1/compare_logs.py读取固定日志快照，输出逐点CSV、
同耗时取样和窗口下降率。运行D:/anaconda/python.exe <脚本路径>，测试用同目录test_compare_logs.py。
快照PDHG末51765s、Barrier末82527s，不能当作未来终态。Time包括预求解、排除建模；不混合callback。
更新比较需新快照目录，不覆盖旧证据。残差内部尺度尚不等价、目标差不是可行上下界证书；
报告不授权停机/改参/StageB，继续原无时限PDHG及独立审计流程。

## 2026-08-28 16:44 云GPU试验前提（未申请）

云端现有WLS类型可支持GPU-PDHG，但当前账号可见队列无GPU。先取得GPU资源区/型号/价格并获作者
明确费用授权；新环境需匹配GPU版gurobipy、驱动及持续WLS联网，原代理不可跨区盲用。
许可证文件未含到期日，本次未创建Env验证订阅/并发，不能把“WLS字段存在”当作新节点已授权。
如后续启动，先小LP确认GPU model及Start PDHG on GPU，再考虑同2160h独立对照；保持现有本地
无时限PDHG不变，不把节点切换当作当前进程无缝迁移。此轮仅只读查询，无远程写入或计费作业。

## 2026-08-28 16:43 当前接续入口：local_8760_verified_v3

作者已授权恢复审计。当前工作在本机隔离worktree，读取
outputs/local_8760_verified_v3/run_v1/status.json及launcher_v1/stdout.log、stderr.log。
16:41:48实际Python49052/launcher13448启动；勿根据旧PID操作，先核验创建时间/命令。
阶段DOWNLOADING→ASSEMBLING_AND_VERIFYING→AUDITING_LOCAL_VERIFIED_FILE→COMPLETE。
完整SHA验证前不启动解析；解析阶段读取run_v1/audit/status.json，最终audit.json只在完整验证后产生。
新工具不涉及Gurobi或服务器计算，只从云端分块读取并在本机处理；本机保持开机联网。

禁止重复启动同cache；active_download.lock须按运行README核验归属。失败保留所有已完成块及日志，
后续授权恢复使用同cache、新run目录，不覆盖旧结果。32MiB旧v2已受控停止，旧status不是当前状态。
另一备份45560/目标目录及PDHG均不干预；继续原无时限/3h检查/2s采样。

## 2026-08-28 16:33 接续更正：审计FAILED，不能继续等待原进程

隔离worktree outputs/stream_8760_original_v1/status.json已于15:38:14写FAILED；SSH Connection reset
造成gzip EOF。Python34684/SSH40220/launcher37332已退出；不得将下方15:07旧状态当作仍运行。
原失败目录保留，无完整audit.json或SHA/CRC通过记录。16:32云端SSH可达，源大小仍4142909397bytes。

独立备份45560仍在，但transfer_progress及服务器backup_status自14:22:46停在31/104范围；
未见release_integrity_report PASS，不得从稀疏/部分副本开始矩阵审计。仅提出先取得稳定校验副本
再重新审计的建议，本轮没有恢复传输或启动新审计。后续须复核旧写进程/子进程并取得对应恢复授权，
不要并发写同一目录或重复启动。PDHG仍为原1216969、clean6065bfb，继续无时限/3h检查/2s采样。

## 2026-08-28 15:09 8760h日志简报的本地复现

历史job4139552的图文结果位于output/pdf/8760_stage_a_convergence_20260828_v1，
从该目录README复制命令：先运行scripts/report_8760_convergence.py（numpy/matplotlib），
再运行scripts/render_8760_convergence_note.py（reportlab）。仅需小型本地归档日志/JSON，
不需SSH、Gurobi、模型构建或presolve/optimize；脚本不启动StageB。
源码/输出哈希与6/6测试、三页渲染证据见QA.md。原LP HARD_FAIL与恢复QC FAIL不改变。
本次没有核验或改动Case4、独立数值诊断和完整结果备份的运行状态，仍遵守其各自既有工作流。

## 2026-08-28 15:07 数值改进接续：隔离分支，不部署

独立worktree `.codex_tmp/numerical_stability_20260828_v1`，候选commit cff89ce；
237项回归及代数证书通过，但24h求解仍NUMERIC，禁止据此合并部署或重启当前PDHG。
完整说明在该目录NUMERICAL_STABILITY_WORKLOG.md。严格零入流修正不是任意截断小正值。

已有一个Windows本地完整8760h MPS流式审计：Python34684、启动器37332、SSH40220，14:49:54启动。
先查该worktree的outputs/stream_8760_original_v1/status.json、outputs/stream_8760_launch_v1/stderr.log，
以及运行目录ssh.stderr.log；复核创建时间/命令行后判断，**不得换标签重复启动**。
输入是paracloud-bscc-a8云端完整恢复original.mps.gz，不是固定服务器正在传输的副本；
源端只读cat，本机解压/统计/哈希，无额外云计算作业或固定服务器求解，主机应保持联网开机。
COMPLETE必须包含完整gzip/ENDATA、SHA256、4142909397bytes、50907234/41458383/492835195规模匹配。
失败保留现场、不自动重启；完成后再分析audit.json。当前PDHG3h巡检/2s采样/无时限/95%保护不变。

## 2026-08-28 14:34 数值诊断接续限制

三轮大规模Matrix极值一致、两个2160h同原LP指纹。诊断见
`downloads/numerical_review_20260828_v1/REPORT.md`；全尺寸presolved系数分布尚未取得，
旧1h归档不是本次新增运行或大规模数值验收。不要因此重启Case4、提高系数截断阈值、
修改DAC/目标惩罚/验收门槛，亦不要并发构建大模型做presolve诊断。
当前无时限GPU-PDHG及3h heartbeat、2s采样、95%保护不变；仅在后续获授权的独立诊断窗口
补全原/预求解行列尺度审计，保留原单位QC。此数值分析未更改生产代码/环境或其他备份任务。

## 2026-08-28 14:18 Case4继续无时限，下次约17:17

同一tag `2030_base_2160h_case4_gpu_pdhg_unlimited_20260828_v2`，PGID1216966/Python1216969身份
已复核；production clean6065bfb，无时限配置不变，8211040步后仍未收敛。近3h改善很小，
不因此杀进程或改变算法；作者已明确允许观察长尾。资源记录正常，GPU1持续满载、显存约4.5GiB，
RSS约17GiB，无CPU回退/OOM；证据review_20260828_1417已保存。约17:17按3小时heartbeat继续，
2秒采样/95%保护不变，不重启/缩模型/其他Case或StageB，不干预独立结果备份。

## 2026-08-28 14:17 首个2030结果完整备份：后台进行，勿重复启动

固定服务器备份父目录：
`/home/zz2/National_model_server/backups/2030_8760_stage_a_first_recovered_20260828_v1`。
源整个cloud release301文件6.153GiB复制到父目录下同名release；核心结果在recovered_8760。
Windows后台Python45560于14:14:41启动，命令`parallel_backup_release.py`，4路64MiB分块。
只允许检查状态，不应在原任务运行时再次写同目录；PID需要结合创建时间/命令行实核。
本机必须保持开机联网。本条不是“完整备份已成功”：大文件仍在传输，表观size可能含稀疏洞。

完成判据：服务器父目录`backup_status.json`为COMPLETE，`release_integrity_report.json`为PASS，
301文件全部passed；未出现终态报告时不得删除云端数据或将本地副本当作唯一恢复来源。
本机日志/进度/完整续传命令见`downloads/2030_stage_a_first_result_visualization_v1/README.md`。
最后自动hash校验；若进程退出或网络中断，先审查stderr、确认旧写进程退出，再从已有完整块续传。
已SHA验证复用t550旧checkpoint4份目标、1.376GiB；旧文件保持不变，不需要重做Stage A。
图表已在父目录analysis_v1；备份工具在backup_tools，不写入历史result manifest目录。
QC FAIL/候选state仍不自动接受；没有StageB/下一年份启动动作，不改Case4任务。

## 2026-08-28 13:45 job4396245恢复成功，不再提交恢复任务

历史8760h恢复已03:18:35完成，Slurm COMPLETED0:0、preservation COMPLETE，耗时1:04:39、峰62.061GiB。
结果root `/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260828_8760_stagea_recovery_v1/recovered_8760`。
原LP指纹和完整顺序一致，实际没有依赖放宽指纹；无optimize/presolve/Stage B。

完整恢复产物86文件约5.45GiB，包括4.14GB压缩MPS、完整名称目录、所有语义结果和86900行候选state。
候选续年要显式allow-candidate-state-in，不自动进入2040；QC FAIL不作丢弃条件，science仍未接受。
本次文件size/存在和关键hash复核通过，完整manifest/candidate验证已在作业结束前执行。
本地terminal_review_1342仅为终态报告，不是5.45GiB完整下载。按作者下一步需求下载或分析，
不要因QC FAIL重跑恢复或默认启动Stage B；固定服务器Case4独立运行不受本条改变。

## 2026-08-28 11:17 Case4无时限生效，下次约14:16检查

同一tag `2030_base_2160h_case4_gpu_pdhg_unlimited_20260828_v2`，PGID1216966/Python1216969
仍运行且身份已复核。实际配置time_limit_seconds/soft_mem_limit_gb均null；solver31569.427s，
超过旧21600s仍GPU迭代，不存在“到6小时应停止”的接续动作。production clean6065bfb。
11:16:44已5992040步，primal明显改善、dual仍高，未完成/QC；GPU1客户匹配，没有CPU回退/OOM。
原始资源记录16246条，summary因先复制而少4秒/2条，errors0；不要误判为监测失步。
证据review_20260828_1116；保持无时限/3小时审查/2秒采样/95%保护，约14:16再检查，不重启。

## 2026-08-28 08:15 Case4仍运行，下次约11:14检查

无时限tag仍为`2030_base_2160h_case4_gpu_pdhg_unlimited_20260828_v2`，PGID1216966/Python1216969
身份实核一致，production clean6065bfb；实际配置TimeLimit/SoftMemLimit对应字段null，无非默认
TimeLimit日志。08:14:36已3763040步，GPU1实际满载，未收敛且无终态/QC。
资源采样10782条/errors0，RSS17.001GiB/采样峰27.043GiB、显存卡级4600MiB；无OOM/回退。

证据位于downloads/case4_unlimited_20260828_v3/review_20260828_0814/，只读备份，无进程操作。
保持每3小时审查、2秒服务器采样与原95%保护；不要因为墙钟或求解时间超过6h而停止。
下次约11:14继续核验同一运行，不调用启动器、不清理旧目录、不干预其他任务。

## 2026-08-28 05:14 Case4监测接续：GPU已确认、继续无时限运行

当前仍为 `2030_base_2160h_case4_gpu_pdhg_unlimited_20260828_v2`，pgid1216966/Python1216969；
创建时间和命令行已复核。不要重新启动门禁或切回旧screen标签。生产clean6065bfb、配置快照
time_limit_seconds/soft_mem_limit_gb均null，求解日志无非默认TimeLimit；无6小时截止。

首次GPU PDHG callback为03:07:07，stdout含RTX4090和Start PDHG on GPU；05:13:51已1551040步，
尚无return_code或QC。RSS当前17.001GiB/采样峰27.043GiB，GPU1卡级峰4600MiB、本job4558MiB；
近1h GPU平均99.999%，无显存溢出/CPU回退。2秒采样5360条且errors0，资源文件持续更新。
残差非单调且目标仍分离，不将GPU满载等同算法优势，也不因此终止本次无时限探索。

本次只读日志/进程、scp备份和交接更新，证据在downloads/case4_unlimited_20260828_v3/
review_20260828_0514/。下一次约08:13按既有3小时heartbeat检查同一标签；若仍运行，继续记录；
终态后才汇总并暂停。不干预云端恢复或其他用户进程，原95%整机保护不变。

## 2026-08-28 02:16 当前为无时限Case4，审查每3小时

新tag `2030_base_2160h_case4_gpu_pdhg_unlimited_20260828_v2`，02:15:14启动；pgid1216966、
Python1216969、telemetry1216967。不要再监测旧screen tag作为当前任务，更不要重复启动。
旧进程在进入求解前因取消6h配置而被受控SIGTERM，02:15:04 rc143；旧输出/日志/claim完整保留。

新工具包为`campaign_tools/case4_unlimited_20260828_v3`，其一次性门禁在既有独立授权参数外追加
`--unlimited-pdhg`，并选用已固定SHA的large_lp_2160_case4_gpu_pdhg_unlimited_v2.json。
schema仍v1，只有数值参数time_limit_seconds改为null；实际configure_gurobi空模型验证Infinity，
新任务自身model_config_snapshot同样null。不能把修改磁盘配置等同于旧进程在线改参。

当前任务无6h截止，不按竞争力/长尾自动停止；仍保留95%整机外部保护、实际错误/CPU回退处置。
Base2030/2160h/start2880、GPU1单卡、Threads32、原PDHG容差不变，不启动其他算法或StageB。
heartbeat case-4-gpu-pdhg ACTIVE，频率已改为每3小时；服务器资源采样仍每2秒，读取新tag下
resource_pressure.jsonl/summary、resource_monitor.tsv、stdout/stderr/telemetry日志与return_code。
02:15:32采样正常但尚未确认GPU迭代，后续必须看到Start PDHG on GPU，不以显存上下文分配代替。
终态汇总后暂停；旧screen、v1/v2工具包及恢复失败现场均不可覆盖。

## 2026-08-28 02:15 云端恢复正在运行：job4396245，不重复提交

作者已明确授权24核云端恢复以及不过度严格的门禁。实际24CPU/128G，4h上限，02:13:56开始。
原环境+隔离补丁根为`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260828_8760_stagea_recovery_v1`。

```bash
squeue -j 4396245
sstat -j 4396245.batch --format=JobID,AveCPU,MaxRSS,AveRSS
sacct -j 4396245 --format=JobID,State,ExitCode,Elapsed,AllocCPUS,ReqMem,MaxRSS
```

在此root查看control/stdout.log、stderr.log、time.txt、terminal_status.txt和recovered_8760/
recovery_progress.json。计算节点6项tiny测试已通过，77输入校验PASS，正式恢复已进入建模。
不要使用旧Stage A求解sbatch；不要因fingerprint不同重跑求解。新`--allow-fingerprint-mismatch`
明确放行这一个诊断项，并如实记录；维度/nnz、变量/约束顺序与向量完整性仍检查。
模型在身份检查前归档，归档摘要复用以避免重复全量扫描；审计异常尽力导出并标PARTIAL。
最终result_manifest表示文件完整性而非科学接受，QC失败不丢数据、不自动续年。

## 2026-08-28 02:06 当前运行Case4：不要重复启动

作者新授权立即独立启动PDHG，已于02:05:12启动2160h Case4，覆盖下方暂停/等待恢复成功规则。
tag `2030_base_2160h_case4_gpu_pdhg_screen_20260828_v1`；pgid1175169、Python1175172、telemetry1175170。
历史恢复仍FAILED，未绕过其指纹校验、未恢复旧向量、未改现场。生产模型仍clean6065bfb。

新工具包`campaign_tools/case4_independent_20260828_v2`的门禁在原参数外增加
`--independent-after-failed-recovery`，只豁免旧恢复失败的依赖，仍检查进程/资源/版本/工具hash。
已存在queue/launch_claim.json，记录显式授权和旧恢复失败；不要删除claim或重跑启动器。

本次仍用GPU1/2160h/start2880及原profile，最多6h，SoftMemLimit空，保留95%主机外部保护。
02:05:22资源监测正常，但尚未出现Start PDHG on GPU；不能把GPU上下文显存分配当成已迭代。
只读跟进对应run_control/<tag>的stdout/stderr/events、resource_pressure.jsonl/summary、
resource_monitor.tsv和telemetry日志。heartbeat case-4-gpu-pdhg已ACTIVE，每10分钟只监测本次运行，
不再执行恢复后接续入口；进程身份须复核后操作，终态汇总后暂停，不自动重启或其他Case。

## 2026-08-28 02:04 指纹不一致诊断注意事项（待修复授权）

源/目标Gurobi同13.0.2，但Python、NumPy、SciPy、xarray等版本不同，当前只作为根因线索。
此前同环境1h在线/离线一致不证明跨环境原LP相同；不能删除fingerprint门禁或修改源期望值。
恢复驱动先在197行抛出identity mismatch，203行才archive_model，因此失败模型没有MPS/名称归档。
若后续获修复授权，须先让失败原模型和分项审计落盘（不允许把旧向量当作匹配成功的数据导出），
再做历史依赖匹配和跨环境小模型差分；不在没有新诊断产物的情况下盲目重复全年重建。
本轮仅说明与记录，未修改代码、环境、门禁、自动接续或重启任务。

## 2026-08-28 00:57 接续已暂停：历史恢复LP指纹不匹配

本节覆盖下方ACTIVE/WAITING状态。heartbeat `case-4-gpu-pdhg`已PAUSED，Case4未启动；
`run_control/2030_base_2160h_case4_gpu_pdhg_screen_20260828_v1_queue/status.json`为
BLOCKED_RECOVERY_FAILED，没有launch_claim或正式Case4控制目录。不要删除门禁记录或换tag重试。

恢复根仍为`recovery_8760_20260827_v1`：00:47:11报identity mismatch，00:48:04退出rc1，
host95_guard0、optimize/presolve0。原identity实际路径为`source_backup/output/run_identity.json`，
与`recovered_8760/build_report.json`比较可见维度/非零元相同但fingerprint为-781497218/718212258。
这不是恢复完整或QC失败可接受的情况，而是尚未通过精确模型身份核验；不直接套用旧BarX/BarPi。

本地证据在`downloads/case4_after_recovery_20260828_v1/recovery_failure_0057/`。保留所有原始结果和
失败现场。待作者明确诊断或独立启动Case4的新决定后再行动；不可自动重启恢复或修改门禁继续求解。

## 2026-08-28 00:46 恢复后Case 4一次性启动和资源监测

已授权并创建当前对话heartbeat `case-4-gpu-pdhg`（ACTIVE，每10分钟）。必须保持本机Codex运行和SSH
可达；服务器没有额外cron/等待daemon，定时任务调用下述幂等门禁。当前实调为WAITING_RECOVERY，
**尚未启动Case4**。工具已隔离部署，覆盖下方00:32“本地修复尚未部署”的状态，但生产repo未改动。

```bash
/home/zz2/National_model_server/envs/cispo-2030-gurobi-gpu13.0.2-cu129-v1/bin/python \
  /home/zz2/National_model_server/campaign_tools/case4_after_recovery_20260828_v1/scripts/start_case4_after_recovery.py \
  --server-root /home/zz2/National_model_server \
  --recovery-root /home/zz2/National_model_server/recovery_8760_20260827_v1 \
  --expected-repo-head 6065bfba34b76098e86307081323e8545a4d25ac \
  --tag 2030_base_2160h_case4_gpu_pdhg_screen_20260828_v1 --gpu-device 1
```

追加`--check-only`只检查不启动。正常模式在`run_control/<tag>_queue/status.json`保存状态，flock和
`launch_claim.json`确保不重复发起。ALREADY_CLAIMED不是成功求解证据，须读取queue/launcher日志及
正式`run_control/<tag>/run.pid`、stdout/stderr/return_code。不得删除claim或换标签绕过失败记录。

恢复rc0、progress和preservation_report COMPLETE且optimize/presolve0后，仍要求无其他大模型、
生产clean6065bfb、工具SHA匹配、available>=96GiB、GPU1无compute客户端且free>=22000MiB/util<=5%。
这些是启动检查，不是运行用量上限；原SoftMemLimit=null及whole-host95%外部保护不变。恢复QC失败
但保全完整允许接续；恢复本身失败/版本漂移则报告并暂停后续任务，不自行终止恢复或抢其他用户资源。

GPU1专用私有CUDA MPS目录在queue/gpu_runtime。Case4固定2160h/start2880、原profile、最多6h；
运行日志必须出现GPU识别及`Start PDHG on GPU`。回退CPU不得计为GPU成绩，不自动双卡或其他Case。

正式控制目录新增：

- `resource_pressure.jsonl`：每2秒完整样本，UTC时间戳；主机RAM/可用量/Swap累计换入换出/PSI/CPU、
  job进程组RSS/CPU时间、双GPU显存总量/使用/余量/容量占比、GPU利用率/显存控制器活跃率、温度/
  功耗/pstate、本job GPU进程显存。后者与卡级总占用分开；缺失值null或errors，不按0伪造。
- `resource_pressure_summary.json`：每样本原子更新，采样峰值/最低available/采样平均GPU利用率/
  telemetry_error_samples。可能漏掉2秒内瞬时峰值；显存控制器活跃率不是容量占比。
- `telemetry.pid`、`telemetry.stderr.log`、`telemetry_return_code.txt`；原host resource_monitor.tsv、
  `/usr/bin/time -v`及stdout/stderr保留。监测异常在events.log记录，后续任务须核验日志持续更新。

验证证据：独立工具根下GPU Python执行`-m unittest discover -s tests -v`为15/15 PASS，包含5秒
占位job的端到端监测，不运行模型；`validation_telemetry/`为读取真实恢复进程组/双GPU的一次样本。
工具完整SHA在scripts/deployment_manifest.json，本地副本及验证样本位于
`downloads/case4_after_recovery_20260828_v1/`。生产repo仍clean6065bfb，本地未提交其他改动未部署。

## 2026-08-28 00:32 Case 4 GPU启动器本地修复（尚未部署）

`run_fixed_server_2160_campaign_case.sh` 现在保留source共享环境之前显式传入的 `CISPO_PYTHON`；
Case 4未显式覆盖时默认选 `envs/cispo-2030-gurobi-gpu13.0.2-cu129-v1/bin/python`，其他Case仍用CPU环境。
旧生产6065bfb会被共享环境强制覆盖回CPU解释器，执行Case 4前必须先单独部署此修复，不能只export。
`GPU_DEVICE=0`或`1`选择一张卡；保留私有CUDA MPS目录隔离。不将`0,1`视为受验证的双GPU模式。

并发门禁已在本地新增历史恢复Python及shell入口识别。6项测试PASS，运行命令：
`python -m unittest discover -s tests -p test_campaign_launcher.py -v`。
00:32实时核查恢复仍在运行、available约71.96GiB、双GPU计算空闲；故本轮未启动Case 4、未建立自动队列。
先让恢复完成并检查return_code/进程消失、MemAvailable达到96GiB，再部署和执行2160h Case 4。
启动门槛不是Gurobi内存上限；原profile的`soft_mem_limit_gb=null`与最多6h筛选不变。
若作者要立即改变优先级，先明确历史恢复处置，不默认杀掉恢复、不干预其他用户进程。

## 2026-08-27 23:48 正在运行的历史8760h离线恢复

已获作者启动授权，任务根 `/home/zz2/National_model_server/recovery_8760_20260827_v1`。
23:47:35启动，pgid657359、Python657364。不要重复运行启动命令或修改此release。
生产checkout仍clean6065bfb，恢复在独立旧源码+导出补丁目录，不表示已部署当前完整新runner。

```bash
R=/home/zz2/National_model_server/recovery_8760_20260827_v1
tail -n 10 "$R/control/stdout.log"
tail -n 10 "$R/control/stderr.log"
tail -n 3 "$R/control/resource_monitor.tsv"
cat "$R/recovered_8760/recovery_progress.json"
test ! -f "$R/control/return_code.txt" || cat "$R/control/return_code.txt"
```

驱动为`scripts/recover_historical_stage_a.py`，使用`--source-backup`、`--path-map`、全新`--output-dir`，
`--preflight-only`仅核验输入。原配置和原30-file implementation bundle必须一致，master非导出AST
不变；完整LP identity和全部索引名称digest均在数值使用前核验。禁止optimize/presolve入口，
90GiB可用内存启动门禁和95%整机外部保护。当前构建峰值、耗时、最终导出仍未知。

已通过`preflight_v2`和历史版本`validation_1h`；input77项、CF实际22536文件全payload一致。
第一轮preflight拒绝更新过的说明清单，其失败证据保留；原清单从云端恢复到隔离数据根，不放宽哈希。
结束后核验QC/保全清单/manifest/candidate读取，QC FAIL不删结果；不自动Stage B或续年。

## 2026-08-27 14:18 本地新保存策略与恢复入口已验证

本节覆盖下方“实现待完成”：代码已本地实现、Gurobi13.0.2的222项回归和1h恢复对照通过，但未部署。
使用边界为：所有nonbasic Stage A自动完整保全raw-order primal/dual、名称/顺序/哈希和逐项QC；候选状态
只能经作者显式`--allow-candidate-state-in`采用，且采用不改变原始QC或scientific acceptance。默认归档
原始MPS，额外presolved诊断副本须显式开启，不默认重复presolve。本节为自包含历史说明，不依赖当时
未提交的独立说明文档。

`--recover-stage-a-from`只重建原LP、校验输入/版本/顺序/哈希、代入原数值导出，不调用optimize/presolve。
大于744h恢复最低可用内存90GiB，仅是执行门禁，不是峰值保证；跨机器路径映射不得隐式放宽。
当前运行中的2160h任务仍为旧代码；不修改活动checkout或干预进程。正式历史8760h恢复须单独选择
原release数据/源码及空闲高内存环境，本轮未启动。

## 2026-08-27 Stage A 历史结果恢复与完整保存要求（实现待完成）

作者要求先完整保全 Stage A，再决定是否用于论文或续年；QC FAIL 只记录，不阻断可读取数据、结果
清单或候选容量状态的保存。本节不是已经可运行的恢复命令，不授权启动新计算任务。

1. 保持 job `4139552` 的本地备份与云端原始输出不变。使用其精确 release 源码、原配置、原始输入
   manifest 与数据文件；不能用当前优化模型替换历史 LP。迁移路径时须建立显式路径映射并逐项核对
   被消费文件哈希，不能仅因为“文件名相同”而跳过 identity 校验。
2. 先开发隔离离线值适配器，重建原 LP/变量与约束映射，并核对 Fingerprint、规模、完整顺序摘要与
   checkpoint 哈希。直接读取 `BarX/BarPi` 计算线性表达式、结果表及原模型残差，不调用 optimize、
   presolve 或 Crossover。旧 zero-iteration start 注入试验不作为已验证恢复方法。
3. 分模块写出全部可读取的容量、运行、成本、碳、对偶及语义/单位映射；一个 QC FAIL 不停止其余导出。
   写 `solution_qc.json`、区分完整性与科学接受的 `result_manifest.json`、包含未筛选原值的候选
   容量 cohort/state metadata。缺失项明确标 partial/error，不伪造 PASS；独立输出根不覆盖源报告。
4. 先以小模型比较在线结果与离线导出的数值、QC、cohort；覆盖 QC FAIL、缺少对偶、向量非有限、
   identity/order 不匹配及部分写出错误。任何映射错误都不得产出貌似正确的语义表，仍可保留原文件
   与诊断。通过后再选择高内存环境；历史 build-only 约 39 分钟/48.574 GiB 不包含全部后处理开销。
5. 下一年份需先生成容量 cohort 并实现作者显式选择的 candidate-state 读取路径；完整逐时表不是
   数学前提，但原始 NPY 不能直接传给现有 planning sequence。保持 QC/未通过项的来源链，不把
   作者选择实验续年写成科学接受。同年 Stage B 则使用已有 checkpoint exact-LP starts，是独立选择。
6. 正式执行前实时检查目标机队列、其他任务、内存、数据与源码身份、license 和输出空间；本轮未做
   新的服务器检查或提交。不得干预其他实验，不默认重启 Stage B、付费恢复作业或跨年序列。

## 2026-08-27 four-case 2160h campaign (Case 1 active)

```text
implementation_commit=88f88779949a5bc27486447d674f6b700b21ac93
gpu_runtime_commit=6065bfba34b76098e86307081323e8545a4d25ac
server_checkout=6065bfba34b76098e86307081323e8545a4d25ac_clean
active_case=case1_v3_barrier16_stage_a
active_tag=2030_base_2160h_case1_v3_barrier16_stage_a_20260827_v1
active_process_group=687599
start=2026-08-27T00:13:53+08:00
```

The only approved cases are `case1_v3_barrier16_stage_a`, `case2_v3_barrier32_screen`,
`case3_dual_simplex_screen`, and `case4_gpu_pdhg_screen`. Run them serially through
`scripts/run_fixed_server_2160_campaign_case.sh`; never add a parameter combination. All new profiles declare
`soft_mem_limit_gb=null`. Case 1 has no solver time limit; the other cases have at most 21600 seconds. The launcher
retains a separate whole-host 95% emergency guard and records resource evidence every two seconds.

Case 4 must use:

```bash
export CISPO_PYTHON=/home/zz2/National_model_server/envs/cispo-2030-gurobi-gpu13.0.2-cu129-v1/bin/python
export CASE_ID=case4_gpu_pdhg_screen
export GPU_DEVICE=0
bash scripts/run_fixed_server_2160_campaign_case.sh
```

The launcher creates private CUDA MPS pipe/log directories so the `zz2` client does not connect to another user's
default MPS socket. GPU acceptance requires both `GPU model: NVIDIA GeForce RTX 4090` and `Start PDHG on GPU` in
the Gurobi log; `GPU not found - running on CPU instead` is a failed GPU case. Do not run another solver, deploy a
new commit, or alter the checkout while Case 1 is active. If and only if 2160h terminates from actual memory failure
or the 95% guard, set `HOURS=2016` with a fresh tag; reduce further only if 2016h also cannot run.

## 2026-08-25 host95 2160h fixed-server gate (deployed; waiting for memory gate)

```text
implementation_commit=7dfefbbef5acc593d22b82173259931183353b89
operational_safety_commit=60561e57c419131a94539c2258ff108cc725edfd
github=60561e57c419131a94539c2258ff108cc725edfd
server_bare_origin=60561e57c419131a94539c2258ff108cc725edfd
server_checkout=60561e57c419131a94539c2258ff108cc725edfd_clean
run_status=NOT_STARTED
blocker=shared_host_available_memory_85_to_86_GiB_below_96_GiB_gate
```

The author superseded the former 80 GB/744 h operational limit for one isolated fixed-server engineering run.
This does not authorize fixed-server 8760 h or a second concurrent solver. The checked-in launcher defaults to
Base/2160 h over model hours 2880--5039 and creates new versioned output/control roots:

```bash
source /home/zz2/National_model_server/server_env_20260825.sh
cd "$CISPO_REPO_ROOT"
bash -n scripts/run_fixed_server_host95_long_horizon.sh
$CISPO_PYTHON -m pytest -q

nohup bash scripts/run_fixed_server_host95_long_horizon.sh \
  >"$CISPO_SERVER_ROOT/run_control/host95_2160_launcher.stdout" \
  2>"$CISPO_SERVER_ROOT/run_control/host95_2160_launcher.stderr" </dev/null &
```

Do not run the launch command until all of these are true: exact deployed commit recorded, checkout clean, no
`run_cispo_2030_full_year.py`/planning-sequence process, target roots absent, available memory at least 96 GiB,
`vmstat si/so=0/0`, memory PSI zero/benign, and the focused/full tests pass. The profile has no solver time limit.
The runner resolves Gurobi `SoftMemLimit` to 95% of detected physical memory; the launcher separately samples
whole-host use every 2 s and sends SIGTERM only when whole-host used reaches 95%. Natural optimal/numerical/error
terminal may occur earlier. Evidence paths under the control root include `git_head.txt`, `git_status.txt`,
`resource_monitor.tsv`, `events.log`, `time.txt`, stdout/stderr, PID, return code, and before/after snapshots.

Deployment verification on `t550` passed `bash -n`, py_compile, focused profile `9/9`, guard `8/8`, and full
pytest `215 passed + 63 subtests` (`98.34 s`, MaxRSS `1,186,016 KiB`, swaps 0). The matching server preflight is
`$CISPO_SERVER_ROOT/outputs/preflight_host95_2160h_deploy_20260825_v1`: numerical compatibility PASS, dimensions
`10,331,823/13,932,898/123,010,374`, resolved Gurobi SoftMemLimit `125.537898 decimal GB`, no time limit. Do not
launch while shared-host available memory remains below `96 GiB`; do not stop or displace unrelated users' jobs.

This run remains `TEST_ONLY_TRUNCATED_HORIZON`. Require a finite eligible engineering checkpoint plus exact input,
LP identity, QC/macro and resource audit before drawing any parameter conclusion. Never reuse the preserved
2026-08-17 Base/2160 MEM_LIMIT root. Resource snapshots intentionally record only process names (`comm`), never
full command arguments, because the server is shared.

## 2026-08-25 t550 current entry, layout and validated short gate

```text
primary_ssh=national-model-server -> zz2@192.168.9.27 (BindAddress 124.16.2.17)
fallback_ssh=national-model-server-vpn -> zz2@192.168.9.27 (system route)
server=t550
server_root=/home/zz2/National_model_server
repo=/home/zz2/National_model_server/repo
python=/home/zz2/National_model_server/envs/cispo-2030-v1/bin/python
environment=/home/zz2/National_model_server/server_env_20260825.sh
bare_remote=/home/zz2/git/National_model.git
validated_commit=50e2d2012a76a342eed1d281997c9b2382731a8a
```

登录后先加载版本化环境，不要手写或猜测数据根：

```bash
source /home/zz2/National_model_server/server_env_20260825.sh
cd "$CISPO_REPO_ROOT"
git rev-parse HEAD
git status --short
```

当前五个运行数据根位于 `$CISPO_SERVER_ROOT/data/`：
`model_ready_20260805_power_curve_v3_qc_d63a251_v1`、`hourly_cf`、
`hydro_timeseries_20260719_sequential_sparse`、`grfr_raw_2019`、`wave_energy_20260727`。部署 manifest、
pip/Conda 清单、readiness/test logs 和 SHA256 证据均位于 `$CISPO_SERVER_ROOT/manifests/`。当前最小复核：

```bash
source /home/zz2/National_model_server/server_env_20260825.sh
cd "$CISPO_REPO_ROOT"
$CISPO_PYTHON scripts/smoke_test_data_package.py
$CISPO_PYTHON -m pytest -q
$CISPO_PYTHON scripts/check_server_readiness.py --require-raw-grfr --verify-raw-grfr-sha256
```

2026-08-25 的接受证据为 data `142/142 PASS`、pytest `212 passed + 59 subtests`、readiness PASS。
唯一真解根 `2030_1h_new_server_smoke_20260825_v1` 使用 Base、1h、
`barrier_16_auto_order_v2`、cold/no-basis，达到 `OPTIMAL + 58/58 + manifests valid`；solver/wall
`6.925/33.33 s`、RSS `0.469 GiB`、swaps 0。它只证明运行链闭合，不是科学结果，也不授权自动放大。

旧 case 盘点边界：所有已挂载文件系统未发现旧 National_model roots；`/dev/sdb1`（14.6 TiB NTFS）与
`/dev/sdc4`（约 222.7 GiB ext4）未挂载，普通 `zz2` 无权只读挂载。必须由管理员授权只读 mount 后再
盘点；禁止自行写盘或宣称旧 case 已丢失。`packages/` 内两个 `*.partial_aborted_20260825` 仅是中止传输
残片，删除前仍须作者确认。

## 2026-08-17 19:29 parameter-route completion boundary

```text
parameter_route_goal=COMPLETE
approved_stage_a=barrier_checkpoint_full_year_cloud_v3
approved_stage_b=deferred_crossover2_full_year_cloud_v3
combined_744_speedup_solver_wall=7.71x/6.99x
fixed=idle_at_0363b7b
cloud_4139552=KEEP_RUNNING_UNCHANGED
cloud_terminal_scientific_status=UNKNOWN
```

“目标完成”只表示未来全年参数架构已有充分工程证据，不表示 cloud 已结束、744/1488 是年度结果，亦不
授权新付费任务。cloud 后续检查仍不早于约 2 小时窗口，除非 terminal/anomaly；无 iteration/异常不写
ledger。任何新 8760 提交必须重新核对当时有效的 ParaCloud 计费、最小 CPU/内存绑定与独立 roots。

## 2026-08-17 19:26 future full-year v3 profile server validation

```text
implementation_commit=0363b7b0183a52184b2f0be7a1381efc76d1615e
fixed_head=0363b7b0183a52184b2f0be7a1381efc76d1615e checkout=clean solver_count=0
pre_post_available_gib~=113.85 si_so=0/0 memory_psi=0
json_bash_pycompile=PASS
focused=14/14_PASS wall=0:02.52 maxrss_kib=109940 swaps=0
full_regression=212/212_PASS tests_s=97.282 wall=1:38.40 maxrss_kib=1118064 swaps=0
profile_status=APPROVED_PARAMETERS_NOT_LAUNCH_AUTHORIZED
```

fixed 现在保持 idle `0363b7b`，不启动 smoke/744/8760、Stage B 或第二 solver；纯文档 tip 不需要再次
部署。未来实际提交仍须独立授权、全新 roots、实时资源/identity 门禁。cloud 原 v2 继续运行，下一常规
检查约 21:20 或 terminal/anomaly；没有 iteration/异常时不追加 ledger。

## 2026-08-17 19:20 cloud resource round 41

```text
job=4139552 state=RUNNING barrier_iteration=343 solver_runtime_s=1012057.571
primal_dual_complementarity=0.983025/8.356e-7/0.087008 recent20_minutes=51.190
wall_s=1015381 allocated_core_hours=27076.827 actual_cpu_hours=4235.784
cpu_efficiency_percent=15.6436 maxrss_gib=362.913 stderr_bytes=0 terminal_artifacts=[]
gurobi_current_max_gib=351.054/354.498 user_queue_jobs=1
ledger_records=42 sha256=69e14220460f734f4f929170e5b9b4575040c5e1be99147a230de749d7d90f25
```

本轮距 round 40 约 2 小时且 iteration 340→343，故追加 ledger；没有无增量重复记录。下一常规 cloud
检查不早于约 21:20，除非 terminal/anomaly。保持原 Stage A，不取消、不改参、不启动 Stage B。

## 2026-08-17 19:18 approved future full-year v3 profile contract

```text
stage_a_profile=barrier_checkpoint_full_year_cloud_v3
stage_a_numerics=Method2,Threads16,Presolve2,Crossover0,SolutionTarget1,BCTol1e-2,FeasOpt1e-5,NF1,Scale2,Aggregate1
stage_b_profile=deferred_crossover2_full_year_cloud_v3
stage_b_numerics=Method2,Threads16,Presolve2,Crossover2,Basis1,LPWarmStart2,FeasOpt1e-6,NF2,Scale2,Aggregate1
common=Markowitz0.01,DualReductions1,InfUnbdInfo0,no_TimeLimit,SoftMem600GiB,Gurobi13+
authorization=APPROVED_PARAMETERS_NOT_LAUNCH_AUTHORIZED
local_validation=config_load_PASS,role_guard_5/5,py_compile_PASS,diff_check_PASS
server_validation=PENDING
```

`solver_profile_version=v1` 是当前 loader schema，不得误改为 profile identity；版本身份由文件名和
`profile_id` 的 `_v3` 表示。部署验证只能在 fixed 无 CISPO/Gurobi、checkout clean、RAM/swap/vmstat/PSI
安全时进行：fast-forward 精确提交，运行 JSON/config load、bash/py_compile、cloud role guard、完整
`tests.test_solver_profiles` 和 full regression。验证完成后仍不得启动 solver。活动 cloud `4139552` 继续
原 v2，不取消、不改参、不启动 Stage B；只约 2 小时或 terminal/anomaly 检查，iteration 未推进且无异常
时不追加 ledger。

## 2026-08-17 19:14 deferred Crossover v3 terminal acceptance

```text
terminal=2026-08-17T18:44:12+08:00 runner_audit_macro_rc=0/0/0
status=OPTIMAL solver_contract=PASS qc=PASS hard_checks=58/58
input_manifest_valid=true result_manifest_valid=true planning_state=false basis=false stderr=0
barrier=0 simplex=1266756 solver_s=2662.606 crossover_s=2458.89 wrapper_wall=50:52.08
max_constr_bound_dual_vio=9.608e-7/8.955e-7/9.538e-7 maxrss_kib=9644004 swaps=0
macro_objective_rel=1.838e-12 capacity_carbon_cost_generation_operation_l1=4.220e-8/1.588e-13/2.209e-9/0.002380/2.109e-6
dual_export=available hourly_rows=23064 hourly_finite=115320 annual_rows_finite=3366/3366
result_use=TEST_ONLY_TRUNCATED_HORIZON scientifically_accepted=false
```

v3 证明 exact deferred route，不是年度结果。未来 8760 Stage B 仍须独立 root、完整 source checkpoint、
相同 Gurobi/scientific identity/Fingerprint/order 和单独授权；最终必须重复本节完整验收。fixed 当前 idle，
不得因成功而自动启动下一 solver。cloud 不取消/改参，约 19:20 才执行下一低频审计。

## 2026-08-17 18:26 deferred Crossover v3 phase audit

```text
identity=Gurobi13.0.2,Fingerprint2120635803,raw_rows_cols_nnz=4454178/3735087/40395436
scientific_manifest=77_rows,sha256=772627bc1539338f5f0af23ad7be01eb9553e78b38a67788863dd26593ad9ac3
data_root_compatibility=PASS,RAW_GRFR_usage_0/0_only
presolve_s=166.67 presolved_rows_cols_nnz=3007038/2846655/31252909
resume=LPWarmStart2_primal_and_dual_vectors direct_crossover=true barrier_rerun=false
push_complete_s=1361 simplex_iteration=1220005 solver_runtime_s=1601 objective~=2361959.0
python_rss_kib=8758088 gurobi_current_max_gib=12.687/13.944
available_gib=105 si_so=0/0 memory_psi=0 stderr=0 terminal=false
```

cleanup 中的 dual infeasibility 不能单独作为失败或验收依据；保持运行，不修改参数。下一 fixed 只在约
19:10 或 terminal/resource anomaly 检查；若 terminal，读取 runner/audit/macro rc、solve/QC、58/58、
input/result manifest、stdout/stderr/time 和 exact macro pair。cloud 约 19:20 才查。

## 2026-08-17 17:54 deferred Crossover v3 active

```text
deployed_head=710aa0259957d03c45821b755562fc1636a60519 checkout=clean_frozen
server_validation=bash_compile_PASS,focused_17/17,full_212/212_97.198s
full_wall=1:38.40 maxrss_kib=1105756 swaps=0
output=/data/zz2/National_model/outputs/deferred_crossover2_744_validation_v0817_v3
control=/data/zz2/National_model/run_control/deferred_crossover2_744_validation_v0817_v3
started_at=2026-08-17T17:53:13+08:00 supervisor_pid=1758970 python_pid=1758995
launch_available_gib~=113 si_so=0/0 psi=0 initial_stderr=0
```

活动期禁止 fast-forward、第二 solver、改参和覆盖 roots。下一 fixed 检查不早于约 30--45 分钟，除非
phase/terminal/resource anomaly；顺序为 process/event → start identity/root compatibility → Fingerprint/
dimensions/order → Gurobi 是否直接 Crossover 且 Barrier 未重跑 → RAM/swap/vmstat/PSI/stderr。若 terminal，
必须依赖 runner strict audit、58/58、两个 manifest 和 macro pair，不能只看 PID/日志/status。cloud 仍按
约 2 小时检查且无新 Barrier iteration/异常时不落账。

## 2026-08-17 17:48 deferred Crossover v2 terminal and v3 relaunch gate

```text
v2_terminal=2026-08-17T17:15:01+08:00 runner_audit_macro_rc=1/41/42
build_started=false solver_started=false output_files=0
error=NameError:CLOUD_FULL_YEAR_PROFILE_IDS
repair_commit=018607c local_compile=PASS focused=5/5 stale_reference_count=0
next_roots=deferred_crossover2_744_validation_v0817_v3
```

不得复用/删除 v1 或 v2 roots。v3 只能按以下顺序启动：实时确认 fixed 无 CISPO/Gurobi、checkout clean、
RAM/swap/vmstat/PSI 安全；fast-forward exact `018607c`；运行 bash/py_compile、profile guard、data-root、
primal-dual、deferred contract 与 full regression；再次确认无 solver；预检全新 v3 roots 后启动唯一
supervisor。任何一步失败都不启动。启动后只按 phase event/terminal 或约 30--45 分钟检查；cloud 约两小时，
没有新 Barrier iteration 或异常时不追加 ledger。

## 2026-08-17 17:21 cloud resource round 40

```text
job=4139552 state=RUNNING barrier_iteration=340 solver_runtime_s=1002807.627
primal_dual_complementarity=1.082073/8.926e-7/0.0942553 recent20_minutes=51.928
wall_s=1008190 allocated_core_hours=26885.067 actual_cpu_hours=4205.427
cpu_efficiency_percent=15.6422 maxrss_gib=362.913 stderr_bytes=0 terminal_artifacts=[]
ledger_records=41 sha256=5e3a972a36812e11ea3b4464743e4f996653b39e141e592081615233cf7021a4
```

下一 cloud 检查约 2 小时或 terminal/anomaly；只有新 iteration 才追加 ledger。fixed v2 本轮未查询，
保持独立的 30--45 分钟/phase-event cadence。

## 2026-08-17 17:15 deferred Crossover v2 active

```text
deployed_head=acf59f9180483b09c4c0e9380e0576457cc554ac checkout=clean_frozen
server_validation=bash_compile_PASS,focused_16/16,full_211/211_97.142s
full_wall=1:38.26 maxrss_kib=1112044 swaps=0
output=/data/zz2/National_model/outputs/deferred_crossover2_744_validation_v0817_v2
control=/data/zz2/National_model/run_control/deferred_crossover2_744_validation_v0817_v2
started_at=2026-08-17T17:14:54+08:00 supervisor_pid=1710059
launch_available_gib=113.905 si_so=0/0 psi=0 initial_stderr=0
```

v2 与 v1 的 source/reference/profile 相同，只使用修复后的窄 root-compatibility gate 和全新 roots。第一次
phase 检查必须验证 `primal_dual_start_input.json.data_root_compatibility` 仅含 RAW_GRFR 0/0 usage 差异，
并继续核对 scientific SHA、Gurobi version、Fingerprint、dimensions/order、LPWarmStart2 与 Gurobi 是否
直接 Crossover。PID 存在时禁止 fast-forward、并发、改参或覆盖 v1/v2。

## 2026-08-17 17:10 deferred Crossover v1 identity terminal

```text
v1_runner_audit_macro_rc=1/41/42 wall=5:31.43 maxrss_kib=4754120 swaps=0
solver_started=false gurobi_log=false solve_qc_result=false
source_raw_grfr_root=null
target_raw_grfr_root=/data/zz2/National_model/data/grfr_raw_2019
scientific_manifest_rows=77/77 equal=true sha256=772627bc1539338f5f0af23ad7be01eb9553e78b38a67788863dd26593ad9ac3
source_target_raw_grfr_manifest_usage=0/0
fixed_idle=true checkout=b277fce available_gib~=113 si_so=0/0 psi=0
local_fix_tests=root_compatibility_4/4,primal_dual_5/5 deployment=NOT_YET
```

v1 output/control 永久保留，不删除、不覆盖。允许重跑的唯一修复范围是：只有
`CISPO_RAW_GRFR_ROOT` 在双方 scientific manifest usage 均 0 时可作为审计后环境差异；任何其他 root
或非零 usage 仍 fail-closed。提交/双推送后，fixed 先 fast-forward exact tip，执行 `bash -n`、新增 focused
与 full regression；全部通过且 no-solver/resource-safe 后，显式设置全新
`OUTPUT_ROOT/CONTROL_ROOT=deferred_crossover2_744_validation_v0817_v2` 再启动。不得复用 v1 根。

## 2026-08-17 16:43 all-version cloud profile fail-closed guard

```text
stage_a_profile_prefix=barrier_checkpoint_full_year_cloud_
stage_a_required_flag=--engineering-barrier-checkpoint-only
stage_b_profile_prefix=deferred_crossover2_full_year_cloud_
stage_b_required_input=--primal-dual-checkpoint-in
both_roles=full_year_only
focused_local=4/4_PASS py_compile=PASS diff_check=PASS deployment=NOT_YET
```

不要再用逐版本 allowlist 增补 v3/v4；稳定前缀本身就是 fail-closed role contract。complete Barrier
checkpoint 可进入 exact Stage B；incomplete Barrier 只保存 recovery evidence，必须保持
`deferred_crossover_eligible=false`。当前 v2 cloud job 启动命令已满足上述合同，不重提、不改参。
fixed solver 存在期间不得部署此本地修复。

## 2026-08-17 16:35 deferred Crossover=2 744 validation active

```text
deployed_head=b277fcea4cb42d4bf8634f0baaf794095e00d67f checkout=clean_frozen
server_validation=bash_json_compile_PASS,focused_20/20,full_203/203_94.966s
regression_wall=1:36.07 maxrss_kib=1121468 swaps=0
output=/data/zz2/National_model/outputs/deferred_crossover2_744_validation_v0817_v1
control=/data/zz2/National_model/run_control/deferred_crossover2_744_validation_v0817_v1
started_at=2026-08-17T16:34:12+08:00 supervisor_pid=1656831 time_child_pid=1656855
launch_available_gib=113.918 vmstat_si_so=0/0 memory_psi_avg10=0 stderr_bytes=0
fixed_monitor=phase_event_or_30_to_45_minutes cloud_monitor=about_2_hours_new_iteration_or_anomaly_only
```

首个 fixed 检查不得早于正常 build/identity 窗口，除非 PID/资源异常。检查顺序为：supervisor/process tree
→ events → `primal_dual_start_input.json` → source/target manifest 与 Gurobi/version/implementation authorization
→ Fingerprint/dimensions/order digests → `gurobi.log` 是否直接 warm-start/Crossover 且未重跑 Barrier →
RAM/swap/vmstat/PSI/stderr。PID 存在时禁止 fast-forward、第二求解或修改输出。terminal 后只能由 runner 的
strict audit 与 macro pair audit 判定；不得仅凭 PID、return code 或 Gurobi log 接受。cloud `4139552`
仍为原 Stage A，不取消、不改参、不启动 Stage B。

## 2026-08-17 16:30 deferred Crossover=2 744 validation contract prepared

```text
source=/data/zz2/National_model/outputs/relaxed_barrier_campaign_v0812_v1/base_744h_bctol1e2_numeric1
source_checkpoint_eligible=true source_manifest_sha256=76460ff4e1ff36cc59c72235d95816aeb1961a34ef90d0e7a9bdd68a0bb148b4
source_fingerprint_vars_rows_nnz=2120635803/3735087/4454178/40395436
source_barx_entries_sha=3735087/53054c53f01c4f0caad533766dadb355e5f0c7625f3f3a6e82a71ce5bdaaa4c5
source_barpi_entries_sha=4454178/98d035bb632994482879831938f28102aae1595d16d116b4cbd492482db335ef
target_profile=barrier_16_deferred_crossover2_744_validation_v1
target_params=Crossover2,CrossoverBasis1,LPWarmStart2,Threads16,FeasOpt1e-6,NF2,Scale2,no_TimeLimit,SoftMem80
target_output=/data/zz2/National_model/outputs/deferred_crossover2_744_validation_v0817_v1
target_control=/data/zz2/National_model/run_control/deferred_crossover2_744_validation_v0817_v1
local_validation=json_compile_diff_PASS,focused_6/6_PASS deployment=NOT_YET started=false
```

真实 resume identity 不得比较包含 solver profile 的完整 manifest 文件 SHA；Stage A/B 必须使用不同
solver profile。现在只排除恰好一行 `solver_configuration`，其余 manifest 行全部参与科学 SHA。
implementation bundle 不同默认拒绝；显式许可只允许继续执行 Gurobi version、case/data layers、exact
Fingerprint/dimensions 与完整 Var/Constr order digests，任一不符仍在 optimize 前失败。部署后先跑完整
server regression；启动命令必须包含三项显式许可并禁止 state/basis。终态只有
`OPTIMAL + solver PASS + solution_qc PASS + 58/58 + current input + valid result manifest + accepted-pair
macro PASS` 才证明 744 Stage A→B 架构可用；结果仍是 `TEST_ONLY_TRUNCATED_HORIZON`。

## 2026-08-17 16:16 second paired factor/throughput batch terminal

```text
campaign=COMPLETE wall~=43:00 summary_status=NO_MATERIAL_COST_IMPROVEMENT
all_paired_screens_valid=true shortlist_tags=[] scientifically_accepted=false
presparsify2_factor_nz_ops_step_ratio=0.976002/1.073514/1.107897 wall=17:00.64 maxrss_kib=20371484
barorder1_factor_nz_ops_step_ratio=1.0/1.0/1.107832 wall=12:46.29 maxrss_kib=19783500
threads32_factor_nz_ops_step_ratio=1.0/1.0/1.256668 wall=13:01.31 maxrss_kib=19759924
all_cases=status7,barrier5,runner_rc2,audit_rc0,stderr0,swaps0,no_science_artifacts
summary_json_sha256=8c30c8960d987cb9c765d085c6e80c02c9c3eb276d89f22c56e19076def7a071
summary_csv_sha256=af32487bcff1cda14ad45ebc697c517a1bee7b3d74d560ccde9e9fd5dc9154ad
fixed_solver_count=0 checkout=7551e3f available_gib~=113 si_so=0/0 psi=0
```

不得为这三个空-shortlist 候选运行完整 744，也不得继续 PreDual/Aggregate/Scale/Order/Threads 的低价值
盲扫。下一阶段仅做证据汇总：用已经完成的完整 relaxed/strict 744、Base/1488、Base/2160 memory boundary
与 cloud Stage A，冻结后续 8760 的线程、内存、Barrier tolerance、checkpoint 和科学验收边界。若未来提出
新候选，必须先给出代数等价或明确参数机制及预期 >=5% 结构/10% throughput 改善，再重复短筛。

## 2026-08-17 15:23 second paired factor/throughput batch active

```text
deployed_head=7551e3fcc55aa2964dd8eff2bed30e7ab47400f7 checkout=clean_frozen
server_validation=bash_json_compile_PASS,focused_16/16,full_197/197_93.710s
full_regression_wall=1:34.83 maxrss_kib=1133084 swaps=0
baseline_fingerprint=2120635803 raw_rows_cols_nnz=4454178/3735087/40395436
baseline_factor_nz_ops=7.334e8/4.761e12 baseline_observed_step_s=12.8348494053
output_base=/data/zz2/National_model/outputs/relaxed_factor_screens_v0817_v2
control_root=/data/zz2/National_model/run_control/relaxed_factor_screens_v0817_v2
supervisor_pid=1567638 started_at=2026-08-17T15:23:11+08:00 active_tag=presparsify2
launch_available_gib=113.951 si_so=0/0 psi_avg10=0.00 stderr_bytes=0
cloud_job=4139552 state=RUNNING iteration=338 verified_at=2026-08-17T15:19:23+08:00
```

活动期禁止修改 fixed checkout、启动并发求解或把 5-step 根当 checkpoint/科学结果。仅同一 supervisor
可按 `presparsify2 -> barorder1 -> threads32` 顺序切换。正常 fixed 检查约 30--45 分钟或由 case
switch/terminal/resource anomaly 触发；cloud 约 2 小时且只有新迭代/异常才追加 ledger。批次终态必须先
完成 summary fail-closed 审计，再决定是否存在完整 744 + exact macro A/B 候选。

## 2026-08-17 15:16 second paired factor/throughput batch contract

```text
round2_tags=presparsify2,barorder1,threads32
round2_baseline=/data/zz2/National_model/outputs/relaxed_factor_screens_v0817_v1/nf1_scaleauto
round2_output=/data/zz2/National_model/outputs/relaxed_factor_screens_v0817_v2
round2_control=/data/zz2/National_model/run_control/relaxed_factor_screens_v0817_v2
structural_reduction_gate=0.05 paired_runtime_reduction_gate=0.10
common_scope=Base/744,NF1,Scale2,Crossover0,BarIterLimit5,scientific_false
local_validation=json_compile_diff_PASS,focused_16/16_PASS
deployment=NOT_YET factor_screens_started=false
```

只允许三根：PreSparsify2 检查稀疏化、BarOrder1 检查 nested-dissection、Threads32 检查真实吞吐。
PreDual/Aggregate/Presolve/AggFill 不再重测。部署后必须验证 baseline 的 paired runtime metric；任一
case 缺 identity/Factor/5 steps/rc/stderr/runtime 时 summary fail-closed。通过短门槛仍须完整 744 宏观
A/B，不能直接成为 8760 profile。

## 2026-08-17 15:10 factor batch 1 terminal / no material improvement

```text
factor_campaign_status=COMPLETE wall~=38:19 all_paired_screens_valid=true
summary_status=NO_MATERIAL_FACTOR_IMPROVEMENT shortlist_tags=[] scientific=false
nf0_scale2_factor_nz_ops_ratio=1.003545/1.031506 step_s=13.187 wall=12:44.06 maxrss_kib=20211636
nf1_scaleauto_factor_nz_ops_ratio=1.0/1.0 step_s=12.835 wall=12:42.69 maxrss_kib=19678600
nf0_scaleauto_factor_nz_ops_ratio=1.003545/1.031506 step_s=13.505 wall=12:41.36 maxrss_kib=20501636
all_cases=status7,barrier5,runner_rc2,audit_rc0,stderr0,swaps0,no_science_artifacts
fixed_solver_count=0 checkout=4f195d4 available_gib~=114 si_so=0/0 psi=0
cloud_job=4139552 RUNNING barrier_iteration=338 runtime_s=996833.092
cloud_round=39 wall_s=999673 allocated_core_hours=26657.947 actual_cpu_hours=4169.626
cloud_efficiency_percent=15.6412 recent20_minutes=52.922 records=40
cloud_ledger_sha256=75c7edd5cc791517c465798066974edcd7a0acfcf43ee337cf99bbb9222c2108
```

不得从空 shortlist 选择 production winner，也不得运行这三根的完整 744。下一候选必须直接针对
presolve sparsification、fill 或 ordering，仍先 5 iterations；保持原 LP/scientific identity、串行、
全新 roots 与 >=5% Factor Ops/NZ 门槛。cloud 继续低频只读。

## 2026-08-17 14:26 serial 744 h factor-screen campaign

```text
fixed_head=4f195d4353b76ce76c710eb5c7ba3c467a4d494c checkout=clean
server_validation=bash/profile/pycompile_PASS,focused_10/10,full_194/194_96.14s
baseline_fingerprint=2120635803 raw_rows_cols_nnz=4454178/3735087/40395436
baseline_presolved_rows_cols_nnz=3001388/2775698/31159971
baseline_dense_aat_factor_nz_ops=6050/6.131e7/7.334e8/4.761e12
output_base=/data/zz2/National_model/outputs/relaxed_factor_screens_v0817_v1
control_root=/data/zz2/National_model/run_control/relaxed_factor_screens_v0817_v1
supervisor_pid=1494933 active_tag=nf0_scale2 wrapper_python_pid=1495063/1495064
started_at=2026-08-17T14:25:49+08:00 serial_cases=3 barrier_iter_limit=5 crossover=0
launch_available_gib=113.97 si_so=0/0 psi=0 stderr=0
```

活动期间不得 fast-forward fixed checkout、并发第二 solver、生成 checkpoint 或把 screen 当科学结果。
监控只在 15--20 分钟、case switch、terminal 或资源异常触发。结束后要求三根 identity/rc/stderr/
5-iteration/factor fields 全闭合；Factor Ops 或 NZ 至少下降 `5%` 才进入完整 744 shortlist。

## 2026-08-17 14:20 factor-screen data-root freeze before launch

```text
fixed_deployed_head=613abe8d48ac3aa6382cdca3ce5a7d3528356723
server_bash_n=PASS profile_json=3/3_PASS py_compile=PASS focused=10/10_PASS
server_full_regression=194/194_PASS wall_s=95.60 maxrss_kib=1115900
factor_runner_data_roots=CISPO_DATA_ROOT,CISPO_CF_ROOT,CISPO_HYDRO_ROOT,CISPO_RAW_GRFR_ROOT,CISPO_WAVE_ROOT
factor_runner_patch_local=PASS_NOT_YET_DEPLOYED factor_screens_started=false fixed_solver_count=0
```

后台 factor runner 禁止依赖登录 shell 的偶然环境；必须冻结与 Base/744 baseline 相同的五个外部根。
前两次缺根 full regression 仅证明外部数据不在 Git checkout 中，未启动 solver。补丁双推送并 redeploy
后，重复 `bash -n`、focused/full regression；通过后启动时必须传 `EXPECTED_HEAD=<exact tip>`，且
`OUTPUT_BASE`/`CONTROL_ROOT` 均须不存在。cloud Stage A 保持不变。

## 2026-08-17 14:14 Base/2160 memory boundary, fixed idle, cloud round 38

```text
fixed_base_2160_status=MEM_LIMIT status_code=17 solution_count=0 barrier_iterations=0
fixed_base_2160_raw_rows_cols_nnz=12520914/10398783/126724678
fixed_base_2160_build_s=884.643 presolve_s=2214.94
fixed_base_2160_presolved_rows_cols_nnz=9527353/8288888/106864030
fixed_base_2160_ordering_s=565.03 soft_mem_limit_gib=80
fixed_base_2160_solver_s=2800.735 wall=1:01:40 maxrss_kib=72659300 rc=2 stderr=0 swaps=0
fixed_base_2160_checkpoint=false qc=false result_manifest=false objective=null
fixed_campaign=COMPLETE fixed_solver_count=0 checkout=902b1672
fixed_idle_available_gib~=114 si_so=0/0 memory_psi=0
cloud_job=4139552 RUNNING barrier_iteration=336 runtime_s=990741.973
cloud_round=38 wall_s=995707 allocated_core_hours=26552.187 actual_cpu_hours=4153.300
cloud_efficiency_percent=15.6420 maxrss_gib=362.913 recent20_minutes=53.040
cloud_resource_audit_records=39 sha256=932b7d8a6510e26653ee2b275cb8ec6280f19d1c87b6c640771c404e66bbd534
```

`MEM_LIMIT` 发生在任何 Barrier iterate 之前，因此没有可保存内点，禁止把此根登记为 checkpoint、
shadow-price 或 macro A/B 结果。不得仅提高 SoftMemLimit 后原样重跑 2160；先利用 744 h 配对 screen
筛选 Factor Ops/NZ 至少下降 `5%` 的候选。fixed 已空闲，下一操作顺序固定为：双推送本里程碑 →
fast-forward 精确 tip → `bash -n`、profile/focused/full regression → 唯一串行 factor-screen runner。
cloud 保持原 Stage A，只读低频监管，不取消、不改参、不启动 Stage B。

## 2026-08-17 13:09 Base/1488 terminal, Base/2160 start, cloud round 37

```text
fixed_base_1488_status=OPTIMAL barrier_status=2 barrier_iterations=143 solver_s=25834.260
fixed_base_1488_wall=7:22:57 maxrss_kib=55460664 rc=0 stderr=0 swaps=0
fixed_base_1488_checkpoint=ENGINEERING_BARRIER_CHECKPOINT_ONLY gate_eligible=true
barx_entries_bytes_sha=7236351/57890936/a49ce6bf164345f78408f8453eba831e6aa74262391b9b9f9d1c928a8d17fef0
barpi_entries_bytes_sha=8648849/69190920/82c4ad5f89c60fc62bd6c08bf71424fdf43288887c99b4078d2c6c197e38c718
lp_fingerprint=893131507 input_manifest_sha=673d0230315cca7dbe1af06a0c9785a696cfd24f18ec52b6359cc3dc9b035a1e
strict_contract=HARD_FAIL engineering_qc=54/58 result_use=TEST_ONLY_TRUNCATED_HORIZON
failed_hard_checks=wave_availability,unidirectional_interprovincial_flow,reservoir_transition,reservoir_active_storage
storage_overlap_share_load=0.000952 interprov_opposing_share_load=0.002594
interprov_excess_loss_share_load=0.00006414 load_center_bidirectional_share_load=0.008909
shadow_price_rows_hourly_annual=46128/3366 publication=ENGINEERING_ONLY_NOT_FOR_PUBLICATION
fixed_base_2160_start=2026-08-17T13:01:45+08:00 pid=1387308/1387309 start_hour=2880 phase=BUILD
fixed_base_2160_start_available_gib~=110 si_so=0/0 psi=0 stderr=0 checkout=902b1672
cloud_job=4139552 RUNNING barrier_iteration=335 runtime_s=987914.783
cloud_round=37 wall_s=991984 allocated_core_hours=26452.907 actual_cpu_hours=4137.397
cloud_efficiency_percent=15.6406 maxrss_gib=362.913 recent20_minutes=53.550
cloud_resource_audit_records=38 sha256=c31d779cededad5baf6d50912808be8c09bfd90a1a98577d10cddec62d0fe0df
```

1488 的 checkpoint 可用于工程 deferred crossover，但 strict QC/HARD_FAIL 决定它不能成为科学结果、
planning anchor 或论文价格。作者已接受不把低占比双向/重叠现象作为长时域工程阻断项；仍须完整记录，
且最终科学 Stage B 必须严格 QC PASS。当前只读监管唯一 Base/2160；不部署、不并发、不改 checkout。

## Factor-screen fail-closed summary contract

runner 默认 baseline：

```text
/data/zz2/National_model/outputs/relaxed_barrier_campaign_v0812_v1/base_744h_bctol1e2_numeric1
```

部署后必须先生成 `CONTROL_ROOT/baseline_solver_audit.json`；缺少 LP Fingerprint、raw/LP matrix counts、
scientific/scenario SHA 或 presolved/Factor fields 时 exit 98，不能先消耗三根 screen。三根完成后执行：

```bash
python scripts/summarize_relaxed_factor_screens.py \
  --baseline-audit CONTROL_ROOT/baseline_solver_audit.json \
  --control-root CONTROL_ROOT \
  --output-json CONTROL_ROOT/factor_screen_summary.json \
  --output-csv CONTROL_ROOT/factor_screen_summary.csv
```

任一 identity/rc/stderr/5-iteration/numerical/factor gate 失败为 `SCREEN_AUDIT_INCOMPLETE` 并 exit 99。
Factor Ops 或 Factor NZ 相对 baseline 至少下降 `5%` 才进 shortlist；shortlist 只决定哪些 profile 值得
跑完整 744，不是 winner、checkpoint 或科学验收。

## 2026-08-17 11:52 cloud round 36 / fixed iteration 120

```text
cloud_job=4139552 RUNNING barrier_iteration=334 runtime_s=984705.405
cloud_primal_dual_complementarity=1.213709/9.858e-7/0.104884
cloud_round=36 wall_s=988357 allocated_core_hours=26356.187 actual_cpu_hours=4122.200
cloud_efficiency_percent=15.6404 maxrss_gib=362.913 recent20_minutes=53.255
cloud_resource_audit_records=37 sha256=cbf0311e71c382508ad459bd238232e3fbea499b1f8913bbb7792bd5d8233710
fixed_base_1488_iteration=120 runtime_s=21739.318
fixed_primal_dual_complementarity=0.050274/0.000789619/0.027934
fixed_step_seconds_100_120_110_120=169.03/169.75 projected_iteration_at_43200s=247.0
fixed_process_rss_kib=55459960 stderr_bytes=0 terminal_files=absent
```

继续原 profile、唯一 fixed solver 与不取消 cloud 合同。下一 fixed 检查为 iteration 130/终态；下一 cloud
检查约一小时，只有新 iteration 才追加 ledger。不启动 Stage B 或 factor screens。

## Factor-screen machine-readable trajectory fields

部署当前本地 tip 后，`solver_audit.json -> telemetry_phase_summaries.barrier` 必须包含：

```text
iteration_span
runtime_span_seconds
observed_seconds_per_iteration
last_primal_infeasibility / last_dual_infeasibility / last_complementarity
last_primal_objective / last_dual_objective / last_raw_primal_dual_objective_gap
```

server regression 必须包含 `tests.test_solver_audit`。这些字段只用于工程性能与数值轨迹比较，不把
5-step screen 升级为 checkpoint 或科学结果，也不替代完整 744 exact macro A/B。

## 2026-08-17 10:59 cloud round 35 / fixed iteration 100

```text
cloud_job=4139552 RUNNING barrier_iteration=333 runtime_s=981713.748
cloud_primal_dual_complementarity=1.246258/1.002e-6/0.107341
cloud_round=35 wall_s=985280 allocated_core_hours=26274.133 actual_cpu_hours=4109.163
cloud_efficiency_percent=15.6396 maxrss_gib=362.913 recent20_minutes=53.302
cloud_resource_audit_records=36 sha256=64d80b8cceb7eae1081524328adb85d01515c16e1c5446cc5f0eb504bbdb6e87
fixed_base_1488_iteration=100 runtime_s=18358.690 raw_objective_gap=5.432e6
fixed_primal_dual_complementarity=0.562716/0.00180162/0.402016
fixed_step_seconds_0_100_50_100_75_100_90_100=168.69/166.88/168.82/169.06
fixed_projected_iteration_at_43200s=247.2
fixed_process_rss_kib=55452788 mem_available_kib=64075116 swap_used_kib=1007648
fixed_vmstat_si_so=0/0 memory_psi_avg10=0/0 stderr_bytes=0 terminal_files=absent
```

fixed 继续唯一 solver，不按 iteration 100 中途结果停止或改参。每 10 iteration 或 15--30 min 只读检查；
仅终态、TimeLimit、资源异常、campaign job switch 才立即做完整审计。cloud 约每小时检查且仅在新 iteration
后追加账本；不取消、不改参、不启 Stage B。CRLF watcher 已弃用，后续使用 direct read-only SSH。

## 2026-08-17 09:57 cloud round 34 / fixed iteration 79

```text
cloud_job=4139552 RUNNING barrier_iteration=332 runtime_s=978908.233
cloud_primal_dual_complementarity=1.274926/1.023e-6/0.109716
cloud_round=34 wall_s=981492 allocated_core_hours=26173.120 actual_cpu_hours=4092.853
cloud_efficiency_percent=15.6376 maxrss_gib=362.913 recent20_minutes=53.291
cloud_resource_audit_records=35 sha256=29960f1e803e98b1dcbd59e26f242b48b026e87e9a01859f20a3681d6ddaad17
fixed_base_1488_iteration=79 runtime_s=14822.968
fixed_primal_dual_complementarity=10.206400/0.00308381/7.745108
fixed_process_rss_kib~=55451664 stderr_bytes=0
```

两端继续只读监管；不修改 profile/checkout、不取消 cloud、不启 Stage B/并发 fixed solve。下一 fixed
材料门禁为 iteration 100 或终态；cloud 只在新 iteration 后追加下一轮资源账本。

## Next lower-factor screen matrix

活动 campaign 结束且服务器空闲后，部署精确提交并先执行 bash/profile/full regression。随后以唯一
串行 runner 比较：

```text
NF0 + ScaleFlag=2
NF1 + ScaleFlag=-1
NF0 + ScaleFlag=-1
common: Base/744, Method=2, Threads=16, Presolve=2, Crossover=0,
        BarConvTol=1e-2, FeasibilityTol=OptimalityTol=1e-5,
        BarIterLimit=5, TimeLimit=7200, SoftMemLimit=40 GiB
```

启动门禁为 clean checkout、无 CISPO/Gurobi、available ≥64 GiB、si/so 0、memory PSI 0。screen 只
比较 raw/presolved、ordering、dense columns、AA' NZ、Factor NZ/Ops、5-step time、RSS/swap/PSI；
不导出 checkpoint，不做 Crossover，不做宏观/科学验收。只有 factor 成本有实质改善者再跑完整 744。

## Future 1488-to-2160 checkpoint gate

新 campaign 不得再用 manifest existence 作为长时域继续条件。必须执行：

```text
python scripts/check_barrier_checkpoint_eligibility.py \
  OUTPUT/barrier_checkpoint/barrier_checkpoint_manifest.json \
  --output CONTROL/checkpoint_campaign_gate.json
```

仅 exit 0 / `eligible=true` 可继续；recovery-only、非 OPTIMAL Barrier、BarX/BarPi size 或 SHA256
不符都停止。该实现当前只在本地，活动 fixed campaign 不追改。部署必须等待 solver/campaign idle，
再执行 server `bash -n scripts/run_fixed_server_relaxed_barrier_campaign.sh`、focused tests 与全回归。

## 2026-08-17 09:32 cloud round 33 / Base-1488 iteration 70

```text
cloud_job=4139552 RUNNING barrier_iteration=331 runtime_s=975911.936
cloud_primal_dual_complementarity=1.336420/1.053e-6/0.113863
cloud_round=33 wall_s=980022 allocated_core_hours=26133.920 actual_cpu_hours=4086.896
cloud_efficiency_percent=15.6383 maxrss_gib=362.913 recent20_minutes=53.414
cloud_resource_audit_records=34 sha256=fc88fd29580cc565620096fdf9a2b06ead35e42e88bfa32a2cd3d0d5fe48045c
fixed_base_1488_iteration=70 runtime_s=13316.273
fixed_primal_dual_complementarity=19.574527/0.00930446/18.290173
fixed_process_rss_kib~=55451552 stderr_bytes=0
```

继续遵守作者“不取消 cloud”边界。不得尝试对活动 `optimize()` 追改 `BarConvTol` 或其他参数；
不得 signal/cancel/requeue，不启 Stage B。最近轨迹的 5 天/8--9 天外推仅作费用风险预警，不是 ETA。
fixed 继续唯一 solver 到 iteration 100/终态，活动 campaign 退出前不得部署 lower-factor profiles。

## 2026-08-17 08:37 Base/1488 iteration 50 gate

```text
fixed_base_1488_iteration=50 runtime_s=10014.836
fixed_primal_dual_complementarity=229.055/0.172288/262.879
same_profile_base744_equivalent_iterations=48/58/65 objective_gap_equivalent=61
fixed_projected_iteration_at_12h=244..255
fixed_process_rss_kib=55428232 host_available_gib~=61.0
swap_used_mib~=984 swap_io=0/0 memory_psi=0 stderr_bytes=0
```

这是时间边界信号，不是停止信号。继续到 iteration 100 或终态；不得中途改 TimeLimit/profile、不得
并发。若触发 TimeLimit，按 recovery contract 审计 BarX/BarPi、identity 与物理账目，不能重标为
complete checkpoint 或科学解。

## 2026-08-17 07:40 cloud round 32 / fixed iteration 30

```text
cloud_job=4139552 RUNNING barrier_iteration=329 runtime_s=969935.080
cloud_primal_dual_complementarity=1.404886/1.110e-6/0.119628
cloud_round=32 wall_s=973314 allocated_core_hours=25955.040 actual_cpu_hours=4058.406
cloud_efficiency_percent=15.6363 maxrss_gib=362.913 recent20_minutes=53.686
cloud_resource_audit_records=33 sha256=0752c62843c6d272d58b6d81b2d2444f0fb7b8123e0bc5b225d99921e467326d
fixed_base_1488_iteration=30 runtime_s=6588.139
fixed_primal_dual_complementarity=2.223e6/702.46/5.926e5
```

两端均继续运行；cloud 不取消、不改参、不启 Stage B，fixed 不并发、不部署，下一 fixed 判别点为 50。

## 2026-08-17 07:35 next relaxed factor-screen order

活动 Base/1488 期间只读监控；不得部署或并发。campaign 完成并重新通过 no-solver、clean checkout、
available RAM、si/so 与 PSI 门禁后，下一轮按以下顺序串行：

1. 744 short-iteration factor screen：`NF0+Scale2`、`NF1+ScaleAuto`、
   `NF0+ScaleAuto`，其余保持 winner 的 `BarConvTol=1e-2`、Feas/Opt `1e-5`、Method 2、
   Threads 16、Presolve 2、Crossover 0；
2. 每根记录 raw/presolved rows/cols/nnz、dense cols、AA' NZ、Factor NZ/Ops、ordering、实际
   step time、RSS/swap/PSI；只有明显降低 factor 成本且轨迹有限的候选晋级；
3. 晋级候选以全新 root 完成 744，并和 strict reference 比较 objective、capacity、generation、
   carbon、operation 与 cost-component 账目；不因 micro residual 单独拒绝，也不产生科学 manifest；
4. `AggFill=0` 与 `PreSparsify=2` 仅为次级 screen：历史前者 Factor Ops 改善不足 2%，后者虽降
   Factor Ops 却增加 iterations/总时间。不得直接把它们放大到长任务。

## 2026-08-17 07:25 Base/1488 iteration 25 gate

```text
fixed_base_1488_iteration=25 runtime_s=5731.421 avg_iter_0_25_s=169.69
fixed_primal_dual_complementarity=2.275e8/1.364e5/5.068e7
same_profile_base744_iter25=1.715e8/4.129e6/2.703e10
fixed_solver_memory_current_max_gib=45.07/58.29 process_rss_gib~=52.8
host_available_gib~=61.1 swap_io=0/0 memory_psi=0 stderr_bytes=0
```

继续到 iteration 50；不得仅按 Base/744 的 263 步判断 1488。当前 available 低于新长任务门槛是
活动因子内存所致，不构成停当前任务条件；1488 退出释放内存后，2160 必须重新通过 available>=96 GiB、
si/so=0、PSI=0 门禁才可启动。

## 2026-08-17 07:03 1488-to-8760 factor cost proxy

```text
cloud_8760_presolved=37703954_rows/32166850_cols/404259819_nnz
cloud_8760_ordering_s=2912.17 dense_cols=37696 factor_nz=3.395e10 factor_ops=1.931e15
fixed_1488_dense_cols=36218 factor_nz=3.866e9 factor_ops=1.060e14
cloud_to_fixed_factor_nz_factor_ops_ratio=8.78/18.22
cloud_recent_step_s=3216.5 factor_scaled_fixed_step_s=176.6 fixed_observed_step_s~=171.0
```

1488 现在是全年单步耗时的实证代理。后续参数候选必须同时报告 presolved matrix、dense cols、
Factor NZ/Ops 和实际 step time；只减少 Barrier iteration 但增加每步成本的候选不得晋级。当前唯一
1488 继续测宽松容差所需总迭代数；云端与 fixed 均不改变。

## 2026-08-17 07:01 cloud round 31 / Base/1488 iteration 16

```text
cloud_job=4139552 RUNNING barrier_iteration=328 runtime_s=966756.149
cloud_primal_dual_complementarity=1.450925/1.129e-6/0.122696
cloud_round=31 wall_s=970967 allocated_core_hours=25892.453 actual_cpu_hours=4048.863
cloud_efficiency_percent=15.6372 maxrss_gib=362.913 recent20_minutes=53.608
cloud_resource_audit_records=32 sha256=223757e0609a3299b471d9e01081d1b6a7c69a5a62037707bc6bea191d0ae391
fixed_base_1488_iteration=16 runtime_s=4225.346 avg_iter_0_16_s~=171.00
fixed_solver_memory_current_max_gib=45.07/58.29 stderr_bytes=0
```

两侧均继续只读监管；fixed 下一统计门点为 iteration 25，云端下一次仅在新 iteration/终态追加。
不得取消、改参、部署 fixed checkout、启动第二 solver 或云 Stage B。

## 2026-08-17 06:21 Base/1488 presolve/factor/early Barrier

```text
base_1488_raw=7236351_vars/8648849_rows/87364792_nnz build_minutes~=10.4
base_1488_presolve_seconds=1080.17 presolved=6564794_rows/5761274_cols/73637736_nnz
base_1488_ordering_seconds=322.03 dense_cols=36218 aa_nz=1.509e8
base_1488_factor_nz=3.866e9 factor_memory_estimate_gb=36 factor_ops=1.060e14
base_1488_iter_0_1_2_runtime_s=1489.26/1595.89/1855.80
base_1488_solver_current_max_memory_gib=45.07/58.29 stderr_bytes=0
base744_to1488_presolved_nnz_factor_nz_factor_ops_ratio=2.36/5.27/22.26
```

继续只读运行 PID `3899905/3899906`；先收集至少 5--10 个 Barrier 步长，不以单步外推终点。
TIME_LIMIT 后若 runner 生成 `INCOMPLETE_BARRIER_RECOVERY`，该 manifest 的
`deferred_crossover_eligible=false`，只可用于取证，不可 deferred crossover。现有 campaign 的 2160
条件只检查 manifest 存在，活动期间不得修改脚本；本轮退出后先核查它是否错误晋级，再把未来门禁
最小修复为解析 manifest 且强制 `deferred_crossover_eligible=true`。云 Stage A 保持不变。

## 2026-08-17 05:47 cloud round 30 / Base/1488 build

```text
cloud_job=4139552 RUNNING barrier_iteration=327 runtime_s=963537.897
cloud_primal_dual_complementarity=1.529887/1.166e-6/0.128042
cloud_round=30 wall_s=966523 allocated_core_hours=25773.947 actual_cpu_hours=4030.069
cloud_efficiency_percent=15.6362 maxrss_gib=362.913 recent20_minutes=53.232
cloud_resource_audit_records=31 sha256=5ea6005a31f704c2d4a00a0c35555ab1118bf16e2fdf722e1d417d4d911840c9
fixed_base_1488=BUILDING pid=3899905/3899906 stderr_bytes=0
```

云端继续按原 Stage A 合同只读，不取消、不改参、不启 Stage B。fixed 继续只读等待首个 Gurobi 日志；
build 期没有 telemetry 属正常状态，不构成停滞。任何一侧均不得启动并发第二求解。

## 2026-08-17 05:41 V5/744 terminal / Base/1488 monitoring

```text
v5_744_campaign_rc=0 solver_status=OPTIMAL barrier_iterations=305 solver_seconds=4520.108
v5_744_wall=1:21:54 stderr_bytes=0 maxrss_kib=21285692 swaps=0
v5_744_lp=3894744_vars/4636251_constrs/41327437_nonzeros
v5_744_checkpoint=COMPLETE deferred_crossover_eligible=true scientifically_accepted=false
v5_744_strict_qc=HARD_FAIL failed_check=reservoir_transition residual_m3=11917.821
v5_744_power_balance_gw=2.362e-7 bidirectional_edge_hours=0 storage_overlap_gwh=1.745e-5
base_1488_start=2026-08-17T05:38:42+08:00 pid=3899905/3899906 start_hour=3624
base_1488_profile=BarConvTol1e-2_FeasOpt1e-5_NF1_Scale2_Crossover0_long
fixed_git=902b1672a869cd4e6483633ceaf0208e092bff36 clean
```

当前只读监管 PID `3899905/3899906`。不得切 fixed checkout、启动第二 solver 或修改输出根；每次采样
记录 Barrier iteration/runtime/primal/dual/complementarity、RSS、available RAM、swap I/O、memory PSI、
stderr bytes。wrapper 退出后不能只看 PID/Gurobi status：必须核对 `time.txt`、campaign rc、
`solve_report.json`、checkpoint manifest、向量长度/finite/hash、LP identity 与 engineering physical QC。
1488 checkpoint manifest 缺失则 campaign 必须 fail-closed，不得进入 2160；存在时只允许脚本按既定顺序
启动一个 Base/2160。V5/744 的 `reservoir_transition` 残差必须保留为质量证据，不得把工程解重标为
scientific PASS。云 job `4139552` 继续不取消、不改参、不启 Stage B。

## 2026-08-17 04:18 exact macro winner / V5/744 / cloud round 29

```text
exact_macro_5e2_nf2=FAIL objective_rel=0.012520 operation_l1=0.296402
exact_macro_1e2_nf2=FAIL objective_rel=0.004278 operation_l1=0.100422
exact_macro_1e2_nf1=PASS objective_rel=2.931e-9 capacity_l1=1.330e-8
exact_macro_1e2_nf1_generation_l1=0.001056 operation_l1=1.917e-6 runtime_s=4275.732
v5_744_start=2026-08-17T04:16:42+08:00 pid=3569191/3569192
v5_744_profile=BarConvTol1e-2_FeasOpt1e-5_NF1_Scale2_Crossover0_TimeLimit21600_SoftMem40
cloud_iteration=325 runtime_s=957363.694 audit_round=29 records=30
cloud_wall_s=961177 allocated_core_hours=25631.387 actual_cpu_hours=4007.857
cloud_resource_audit_sha256=26a9903d932fae6c68d5f81b17a04f995313167ec8b2ebca28f7e55d07a61e69
```

当前只读监管 V5/744；PID 存在时不切 fixed checkout、不启动第二 solver。V5 退出后必须先审计
checkpoint/engineering macro/stderr/time；campaign 才可串行进入 Base/1488。ParaCloud 继续不取消、
不改参、不启动 Stage B。

## 2026-08-17 04:16 v4 fail-closed / reused-candidate control directory

```text
server_git=5161dd0d7cd1958dda0ffdc648f2d6683056c95b clean
server_bash_n=PASS focused=6/6_PASS full_regression=187/187_PASS_94.975s
v4_reuse_symlink=PASS audit_import=PASS
v4_macro_files=0 winner=NO_MACRO_PASS solver_started=false
cause=missing_CONTROL_ROOT_tag_directory_before_shell_redirection
patched_campaign_sha256=21e67deb17013c09a05f84c4f28e161c781d48878365d86f1e4124ffaff79b07
```

v4 只作为第二次编排 fail-closed 证据保留。修复后不得覆盖 v4；使用全新 v5 control/output，候选
control 子目录必须在 audit stdout 重定向前存在。只有三份 `macro_comparison.json` 实际生成且 winner
为 `MACRO_PASS` 才能启动一个串行 solver。

## 2026-08-17 04:12 strict reference terminal / v3 fail-closed / minimal fix

```text
strict_status=OPTIMAL qc=PASS hard_checks=58/58
strict_solver_seconds=53489.068 barrier_seconds=7734.65 crossover_seconds=45468.01
strict_objective_million_cny=2361958.416203
strict_constr_bound_dual_vio=9.74e-8/8.50e-8/8.85e-8
strict_wrapper_rc=0 stderr_bytes=0 wall=14:57:39 maxrss_kib=20617928 swaps=0
v3_campaign=NO_MACRO_PASS orchestration_failure_only solver_started=false
patched_campaign_sha256=95e177eeb6874a36bf769dc70f95e7a1262506438bf7124d4f74f69dd5a17132
focused_tests=6/6_PASS
```

v3 不得重标为候选失败；其三个 `macro_comparison_stdout.log` 均为 import failure，且无新 solver。
部署修复后必须使用全新 v4 control/output root；只复用 supervisor symlink 指向的既有 744 engineering
roots，普通已有目录继续拒绝。v4 先运行 exact macro，只有 `MACRO_PASS` winner 才允许严格串行
V5/744、Base/1488，且仅在 1488 checkpoint 存在时进入 Base/2160。

## 2026-08-17 03:01 cloud round 28 / fixed cleanup

```text
cloud_job=4139552 RUNNING Barrier iteration 324
cloud_solver_runtime_seconds=954056.892
cloud_recent_20_iteration_average_minutes=53.113
cloud_last_iteration_minutes=57.122
cloud_resource_audit_round=28 records=29
cloud_resource_audit_sha256=b9d852b351e0fcb1c2ccf51d7b0c7ce7ba819bca49d63a77c0a3e59431951f87
fixed_quad_iteration=1009728
fixed_quad_runtime_seconds=49698.190
fixed_quad_dual_infeasibility=1.022765e3
```

cloud round 28 已持久化且 Stage A 保持原样。fixed 仍为唯一 quad cleanup，wrapper/v3 supervisor
存活、continuation 输出根 absent；继续到正式终态，不提前放行 exact macro。

## 2026-08-17 02:07 cloud round 27 / fixed cleanup

```text
cloud_job=4139552 RUNNING Barrier iteration 323
cloud_solver_runtime_seconds=950629.600
cloud_recent_20_iteration_average_minutes=52.990
cloud_last_iteration_minutes=53.859
cloud_resource_audit_round=27 records=28
cloud_resource_audit_sha256=1ac421f725323ec5d061a8a58d6600507732cb6fbea6cfe08b3621959534f0b8
fixed_quad_iteration=995574
fixed_quad_runtime_seconds=46496.021
fixed_quad_dual_infeasibility=9.215256e2
```

cloud round 27 已持久化且 Stage A 保持原样。fixed 仍为唯一 quad cleanup，wrapper/v3 supervisor
存活、continuation 输出根 absent；继续到正式终态，不提前放行 exact macro。

## 2026-08-17 01:15 cloud round 26 / fixed cleanup

```text
cloud_job=4139552 RUNNING Barrier iteration 322
cloud_solver_runtime_seconds=947398.037
cloud_recent_20_iteration_average_minutes=52.831
cloud_last_iteration_minutes=60.039
cloud_resource_audit_round=26 records=27
cloud_resource_audit_sha256=ec248a3bfa4b62e56df235e3a16395aabf86e18fd7411047d8e8c94b2573ee91
fixed_quad_iteration=980379
fixed_quad_runtime_seconds=43298.541
fixed_quad_dual_infeasibility=3.231602e2
```

cloud round 26 已持久化且 Stage A 保持原样。fixed 仍为唯一 quad cleanup，wrapper/v3 supervisor
存活、continuation 输出根 absent；继续到正式终态，不提前放行 exact macro。

## 2026-08-17 00:14 cloud round 25 / fixed cleanup

```text
cloud_job=4139552 RUNNING Barrier iteration 321
cloud_solver_runtime_seconds=943795.685
cloud_recent_20_iteration_average_minutes=52.246
cloud_last_iteration_minutes=55.024
cloud_resource_audit_round=25 records=26
cloud_resource_audit_sha256=05a7a568c7e3ba293db050626324d197ce4ce3172cc940d5e8621e25172f52f7
fixed_quad_iteration=962785
fixed_quad_runtime_seconds=39637.753
fixed_quad_dual_infeasibility=2.547886e3
```

cloud round 25 已持久化且 Stage A 保持原样。fixed 仍为唯一 quad cleanup，wrapper/v3 supervisor
存活、continuation 输出根 absent；继续到正式终态，不提前放行 exact macro。

## 2026-08-16 23:50 cloud round 24 / fixed cleanup

```text
cloud_job=4139552 RUNNING Barrier iteration 320
cloud_solver_runtime_seconds=940494.224
cloud_recent_20_iteration_average_minutes=52.071
cloud_last_iteration_minutes=68.317
cloud_resource_audit_round=24 records=25
cloud_resource_audit_sha256=efb6bd58ce5abc8acd628204b4a876dd4fd0dbe1a16f46f5c97880b0acbf51a7
fixed_quad_iteration=955777
fixed_quad_runtime_seconds=38214.013
fixed_quad_dual_infeasibility=1.538969e4
```

cloud round 24 已持久化且 Stage A 保持原样；最新步变慢但残差仍改善，不据此取消。fixed 仍为唯一
quad cleanup，wrapper/v3 supervisor 存活且无终态文件；继续到正式终态，不提前放行 exact macro。

## 2026-08-16 23:09 cloud round 23 / fixed cleanup

```text
cloud_job=4139552 RUNNING Barrier iteration 319
cloud_solver_runtime_seconds=936395.199
cloud_recent_20_iteration_average_minutes=51.167
cloud_resource_audit_round=23 records=24
cloud_resource_audit_sha256=d203d675072bc5b4edde3ace8361aea3068fa557119c8e47b34d66b0c3a3fa7b
fixed_quad_iteration=942842
fixed_quad_runtime_seconds=35770.004
fixed_quad_dual_infeasibility=1.988602e5
```

cloud round 23 已持久化且 Stage A 保持原样。fixed 仍为唯一 quad cleanup，wrapper/v3 supervisor
存活且无终态文件；继续到正式终态，不提前放行 exact macro。

## 2026-08-16 21:45 cloud round 22 / fixed cleanup

```text
cloud_job=4139552 RUNNING Barrier iteration 318
cloud_solver_runtime_seconds=933326.741
cloud_recent_20_iteration_average_minutes=51.532
cloud_resource_audit_round=22 records=23
cloud_resource_audit_sha256=5db4ac898c7bc21d5598176853242bcadea04eb9b20599ffc5fccbc2915d50a0
fixed_quad_iteration=917738
fixed_quad_runtime_seconds=30759.680
fixed_quad_dual_infeasibility=8.190958e6
```

cloud round 22 已持久化且 Stage A 保持原样。fixed 仍为唯一 quad cleanup，wrapper/v3 supervisor
存活且无终态文件；继续到正式终态，不提前放行 exact macro。

## 2026-08-16 20:23 cloud round 21 / fixed cleanup

```text
cloud_job=4139552 RUNNING Barrier iteration 317
cloud_solver_runtime_seconds=930000.702
cloud_recent_20_iteration_average_minutes=51.272
cloud_resource_audit_round=21 records=22
cloud_resource_audit_sha256=bf039d692007d3704baa2f8faab337b4bc629aed5ddbedf2f0c8b2e2617d7de0
fixed_quad_iteration=892970
fixed_quad_runtime_seconds=25778
fixed_quad_dual_infeasibility=2.506362e6
```

cloud round 21 已持久化且 Stage A 保持原样。fixed 仍为唯一 quad cleanup，端到端虽已慢于旧根但
进程/iteration/objective 仍活跃；继续到正式终态，不提前放行 exact macro。

## 2026-08-16 19:57 strict 端到端基准交叉

```text
current_total_runtime_seconds=24224 still_running
old_success_total_runtime_seconds=24156.53
current_minus_old_total_seconds=67.47
current_barrier_seconds=7734.65
old_barrier_seconds=11142.54
current_post_barrier_elapsed_seconds=16489.35
old_crossover_seconds=12672.69
current_post_barrier_vs_old_crossover_percent=+30.12
```

该历史比较跨 LP/data identity，只用于工程耗时，不用于科学 exact A/B。结论是 Barrier 加速不能代表
端到端加速；Crossover 长尾已经抹去约 3,408 s Barrier 节省。继续 strict 到正式终态，不因超过旧
耗时取消；8760 h 继续采用独立 Barrier checkpoint / deferred Crossover 架构思路。

## 2026-08-16 19:36 cloud round 20 / fixed low-dual cleanup

```text
cloud_job=4139552 RUNNING Barrier iteration 316
cloud_solver_runtime_seconds=927093.647
cloud_recent_20_iteration_average_minutes=51.638
cloud_resource_audit_round=20 records=21
cloud_resource_audit_sha256=278f03964d057fe6748aee8f2f6cb0327d6b594961f092d4ffd789b067c9e639
fixed_quad_iteration=879136
fixed_quad_runtime_seconds=22956
fixed_quad_dual_infeasibility=4.729218e4
```

fixed 当前处于低 dual 局部段，但仍高于正式容差且无 solver status；继续唯一 solver，不提前验收。
cloud round 20 已持久化，Stage A 保持原样，不取消、不改参、不启动 Stage B。

## 2026-08-16 18:38 cloud round 19 / fixed dual recovery

```text
cloud_job=4139552 RUNNING Barrier iteration 315
cloud_solver_runtime_seconds=923654.909
cloud_recent_20_iteration_average_minutes=51.837
cloud_resource_audit_round=19 records=20
cloud_resource_audit_sha256=19273e364307274243a2b9491cd0610b1c5d6aee964bd08cc34e0a4cfadfc437
fixed_quad_iteration=859888
fixed_quad_runtime_seconds=19483
fixed_quad_dual_infeasibility=2.045376e6
```

fixed dual 从高风险段回落证明当前 cleanup 尚有恢复能力，但不撤销数值风险升级，也不能替代正式
`OPTIMAL + wrapper/QC/manifest`。继续唯一 solver；cloud round 19 已持久化且 Stage A 保持原样。

## 2026-08-16 18:04 strict quad 风险升级与历史对照纠正

```text
old_quad_max_dual_infeasibility=1.908564e8
old_quad_samples_ge_1e8_1e9=2/0
current_quad_max_dual_infeasibility=6.625378e12
current_quad_samples_ge_1e8_1e9_1e10_1e11=41/23/17/10
current_iteration=848783
current_runtime_seconds=17444
current_primal_infeasibility=0
current_dual_infeasibility=3.964324e10
```

不得再以旧成功根 quad 尾长直接预测当前 ETA；两根只共享 warning/保护动作，不共享后续数值轨迹。
当前仍有 pivot/CPU/objective 进展且无正式 failure，故继续唯一 solver，不人工取消。若出现 wrapper 退出，
立即以 status/rc/stderr/QC/manifest 做终态；失败则 supervisor 必须停住，成功才允许 exact macro。

## 2026-08-16 17:51 cloud round 18

```text
cloud_job=4139552 RUNNING Barrier iteration 314
cloud_solver_runtime_seconds=920799.474
cloud_recent_20_iteration_average_minutes=51.766
cloud_resource_audit_round=18 records=19
cloud_resource_audit_sha256=90fc64d612696045ba3c03abd40f60df143a048fafea6357a9d8538aa3730498
fixed_quad_iteration=844413
fixed_quad_runtime_seconds=16683
```

cloud primal infeasibility/complementarity 继续下降，round 18 已持久化；保持原 Stage A，不取消、不改参、
不启动 Stage B。fixed quad cleanup 仍活跃且单 solver，只有完整 strict 终态通过后才允许 exact macro。

## 2026-08-16 17:06 cloud round 17

```text
cloud_job=4139552 RUNNING Barrier iteration 313
cloud_solver_runtime_seconds=917751.150
cloud_recent_20_iteration_average_minutes=52.099
cloud_resource_audit_round=17 records=18
cloud_resource_audit_sha256=a7ab2c58591de060f886052d2c47f1cc4916f48ed38473710ecfe2003c9411ba
fixed_quad_iteration=828761
fixed_quad_runtime_seconds=13981
```

iteration 313 的 primal infeasibility 与 complementarity 继续下降，任务不是停滞。round 17 已持久化；
不得据本地 strict 中途状态取消、修改或追加 cloud Stage B。fixed 继续唯一 quad cleanup，终态后才执行
reference contract 与 exact macro。

## 2026-08-16 16:58 strict quad-precision cleanup

```text
quad_switch_iteration=823548
quad_switch_runtime_seconds=13224
basis_variables_dropped=1
post_switch_iteration=825303
post_switch_runtime_seconds=13464
post_switch_primal_infeasibility=0
post_switch_dual_infeasibility=1.142198e5
```

`drop basis variable + switch to quad precision` 是 Gurobi 自动数值保护，旧成功根有相同轨迹；不得仅凭
该 warning 取消。quad 后 pivot 变慢是预期成本，仍以 CPU/iteration 是否增长、后续 warning/status、
stderr 与终态文件联合判断。继续唯一 solver；只有 wrapper 退出后才执行完整 reference contract。

## 2026-08-16 16:27 strict cleanup 与 cloud round 16

```text
fixed_simplex_iteration=792828
fixed_solver_runtime_seconds=11630
fixed_primal_infeasibility=0
fixed_dual_infeasibility_nonmonotonic_range=7.47e3..9.29e8
cloud_job=4139552 RUNNING Barrier iteration 312
cloud_resource_audit_round=16 records=17
cloud_resource_audit_sha256=65b3c5495adf75062420582837743b6bd34a46afecae1b4e61cf1e34578a59c9
```

simplex dual infeasibility 的单次尖峰不是取消条件。旧成功根在 push 后约 6--7 分钟同样从 `1.52e4`
摆动到 `1.09e9`，最后仍 OPTIMAL；只有持续无 pivot/CPU 增长、warning/error、进程异常退出或正式
status 才升级。继续记录 cleanup iteration/runtime、objective、primal/dual infeasibility；wrapper 退出后
执行完整 reference contract，不得由 `primal=0` 或局部日志提前验收。cloud round 16 已持久化，任务
不取消、不改参、不启动 Stage B。

## 2026-08-16 16:20 Crossover simplex cleanup 监控

```text
crossover_basis_seconds≈255
dpush_initial=841200
dpush_seconds=2565
ppush_initial=274055
ppush_seconds=602
push_complete_runtime_seconds=11177
push_complete_pinf=2.741902
push_complete_dinf=1.751704e8
simplex_initial_iteration=782488
```

simplex cleanup 必须继续记录 primal→dual 阶段、iteration 增量、objective 跳变、长时间无改善和最终
`Crossover time/Solved in/Optimal objective`。当前 PInf 很快下降不代表 dual cleanup 完成；尤其当前
DInf 明显高于旧成功根，禁止提前终止或用当前 basis 验收。资源安全时继续唯一 solver；终态三文件
出现前 supervisor 只等待。云 job `4139552` 不变。

## 2026-08-16 15:39 live Crossover / cloud 状态

```text
fixed_phase=Crossover DPush
fixed_dpush_initial=841200
fixed_dpush_latest≈237580
fixed_single_solver=true
cloud_job=4139552 RUNNING Barrier iteration 311
cloud_resource_audit_round=15 records=16
cloud_resource_audit_sha256=41c67c508e5f43dc2eb490a949fc77904319efb190f3fef30384878bebda58fe
```

DPush 的 DInf 可非单调，只有剩余 pushes、进程活性、warning/error 与最终 push/simplex 状态联合判断；
不得因 DInf 暂升终止。继续按 `gurobi.log` 而不是 barrier telemetry 判断 Crossover 阶段。round 15 已
写入 cloud run-control 旁路，云任务不取消、不改参、不启动 Stage B。

## 2026-08-16 15:25 strict Barrier→Crossover 监控边界

```text
strict_barrier_status=OPTIMAL
strict_barrier_iterations=218
strict_barrier_runtime_seconds=7734.65
strict_barrier_work_units=11980.50
strict_barrier_objective_million_cny=2361958.43
current_phase=Building initial crossover basis
reference_wrapper=alive
supervisor_pid=46839 waiting_reference
```

telemetry 最后一条仍标 `phase=barrier` 是 callback 语义，不代表当前阶段；权威阶段必须同时读取
`gurobi.log`。进入 Crossover 后分别记录：initial basis 构建时长、primal/dual push 时间与数量、
simplex cleanup iterations/time、最终 status/quality。不得因 Barrier 已 `OPTIMAL` 就终止 wrapper，
不得提前启动 relaxed campaign。strict 终态后仍先走强 reference contract；失败则保留现场并停止
continuation，通过才执行 exact macro v2。

当前 fastest candidate 仅得到 objective 近似与时间优势：`1e-2/NumericFocus=1` 相对 strict Barrier
objective 差约 `3e-9`、Barrier-only runtime 节省约 `44.72%`。它仍是 engineering-only，必须等待
完整宏观账目 A/B；该信号不得放松 Stage B 科学验收。云 job `4139552` 保持原样。

## 2026-08-16 14:20 运行中权威状态

```text
fixed_checkout=d80f5b76b7deefd6c82004ee0e17f1fc206f7eff clean/frozen
fixed_strict_phase=Barrier iteration 120
fixed_strict_runtime_seconds=3996.405
fixed_strict_telemetry_primal_dual_complementarity=0.007359 / 5.61e-4 / 0.502643
fixed_supervisor_pid=46839 waiting_reference
fixed_continuation_output=absent
cloud_job=4139552 RUNNING iteration 310
cloud_runtime_seconds=908489.106
cloud_resource_audit_round=14 records=15
cloud_resource_audit_sha256=12ecc84d4405e9549fdcd3e295bdd6c13e940c5b233e7d9ae340080d6aade21f
```

运行中仍只允许只读监控。strict wrapper 退出前不得修改 checkout、候选 profile 或输出；不得手工
触发 campaign。iteration 110--120 的 primal 非单调而 complementarity 继续下降，不构成失败或
完成判断。reference 只有完整通过强终态合同后，v3 才会创建新输出根、只读链接三根 candidate 并
运行 exact macro v2。ParaCloud round 14 已追加到 run-control 旁路；下一轮只在新 iteration 或有意义
时间间隔后追加，禁止因本地中途结果取消/改参/启动 Stage B。

## 2026-08-16 macro accounting v2 / supervisor v3

当前唯一 continuation 为：

```text
supervisor_pid=46839
control=/data/zz2/National_model/run_control/relaxed_barrier_continuation_v0816_v3
output=/data/zz2/National_model/outputs/relaxed_barrier_continuation_v0816_v3
macro_implementation=a02d4d99b1060a2552e1c1f470817f1d4dbe3ac1
supervisor_implementation=5af8efe6872b569e4ca068c7c66cc2aefa9e676e
audit_sha256=dbcf0a6c119d6727e20ec09176fe561dcd00d7cdd13cdfd15156e4371e9665df
campaign_sha256=dd94436d7e007d580f3b3266edb7d56f98e9572710e0e777abb42b76faefa4b3
supervisor_sha256=6a3a70e04c51d77d436b56d14c3be2b602d54fc16742285cf7aa4a7b6862b9dd
```

reference 强终态合同沿用下节；通过后 winner 必须再满足：

1. exact LP/input/scientific identity；
2. objective relative difference `<=1%`；
3. capacity/generation normalized L1 各 `<=2%`，period generation relative difference `<=0.5%`；
4. `annual_carbon_ccs.json` 中 gross/unabated/net/captured/shipped/DAC 的 normalized L1 `<=2%`；
5. curtailment、storage charge/discharge、interprovincial losses 与 wave generation 的 normalized L1
   `<=5%`；采用总账归一化，不能用近零单项的无界相对误差拒绝宏观等价路线；
6. 双方均有 `cost_components.csv` 时 normalized L1 `<=2%`；既有候选因 strict load-center QC 在旧导出
   顺序中提前抛错而缺表时，必须记录 unavailable，只由总 objective 作成本门禁，不得插补。

`export_cost_components()` 的提前写出只影响未来工程证据的保存顺序，不放松 load-center、reservoir 或
其他 hard checks。v3 仍只复用三根候选，不新增参数轮次；只让全账目 `MACRO_PASS` 的最快者运行
V5/744、Base/1488、以及 1488 checkpoint 完整时的 Base/2160。v1/v2 控制根永久保留；不得恢复其
等待 PID。活动 checkout 仍是 `d80f5b7`，不得在 strict 或 continuation solver 存活时部署新提交。

## 2026-08-16 strict reference 强终态门禁与 supervisor v2

活动 fixed checkout 在 strict solve 退出前继续冻结 `d80f5b7`；本地/双远端实现
`f96d9e0443a40f343eaf74b6d97c7abd186e309a` 不得部署到活动 PID。v1 supervisor 已保留日志并由 v2
取代：

```text
supervisor_pid=4179192
control=/data/zz2/National_model/run_control/relaxed_barrier_continuation_v0816_v2
output=/data/zz2/National_model/outputs/relaxed_barrier_continuation_v0816_v2
script_sha256=90e399e9ede9d4d48969e53095f9e7a41308e26351ecbdb1d344632685e17c3b
```

reference wrapper 退出后必须按顺序检查：

1. `wrapper_exit_code.txt=0`、stderr 为 0 bytes，五个 reference contract 文件齐全；
2. `solve_report.status=OPTIMAL`，`solution_qc.status=PASS`，`hard_checks` 必须为恰好 58 项且全部 true；
3. `result_manifest.json.files` 必须是非空列表；每项 path 安全且唯一、bytes 非负、SHA256 合法，随后
   调用正式 validator 逐文件核对存在性/size/hash；
4. 调用 `validate_input_manifest()` 复核当前每个 input；任一 failure/exception 以非零状态停止；
5. 仅强门禁通过后创建全新 v2 输出根和三个只读 candidate symlink，调用冻结的 serial campaign 重算
   exact A/B。其内层旧 validator 较弱不构成放行，因为 reference 已先经过上述更强门禁；后续部署
   `f96d9e0` 后所有新审计直接使用修复后的通用 validator。

不得终止 strict wrapper/Python/resource sampler，不得提前创建 v2 输出根，不得并发第二 fixed solve。
ParaCloud `4139552` 继续只读；每轮人工检查须向 `resource_audit_snapshots.jsonl` 追加 wall、allocated/
actual CPU-hours、MaxRSS、latest Barrier、近期平均单步、stderr 与 terminal artifacts。round 15 已记录，
16 records SHA256 为 `41c67c508e5f43dc2eb490a949fc77904319efb190f3fef30384878bebda58fe`。

## 2026-08-16 relaxed tolerance 的生产边界

1. `BarConvTol=1e-2/5e-2` 与 `NumericFocus=1` 仅在
   `--engineering-barrier-checkpoint-only --engineering-relaxed-barrier-analysis` 隔离路径使用；
   根目录不得生成 scientific QC/manifest/state/basis。
2. relaxed profile 的 `FeasibilityTol=OptimalityTol=1e-5` 不得复制到 scientific Stage B。当前最小
   matrix/objective coefficient 约 `1e-6`，而 Feas/Opt 是绝对容差；`1e-5` 只用于宏观工程 A/B。
3. exact macro 晋级阈值维持 objective `<=1%`、capacity/generation normalized L1 `<=2%`、period
   generation `<=0.5%`。通过只表示可跑 V5/744 与 Base/1488/2160，不表示科学接受。
4. deferred Stage B 继续 `LPWarmStart=2/Crossover=2/CrossoverBasis=1/NumericFocus=2/ScaleFlag=2`，
   Feas/Opt 不宽于 `1e-6`；必须产生 basic OPTIMAL、全部 QC 与有效 manifest。
5. ParaCloud active Stage A 不根据本地中途结果改参或取消。只有本地 exact+long 证据完整后，才为下一次
   8760 h 形成新的 versioned profile；禁止原地修改已运行 profile。

官方依据为 Gurobi 13
[Parameter Reference](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html)、
[Numerical Parameters](https://docs.gurobi.com/projects/optimizer/en/current/concepts/numericguide/numeric_parameters.html)
和 [Tolerances/User-Scaling](https://docs.gurobi.com/projects/optimizer/en/current/concepts/numericguide/tolerances_scaling.html)。

## 2026-08-16 relaxed campaign summary 生成方法

汇总器只读，不改变任何验收状态：

```bash
python scripts/summarize_relaxed_barrier_campaign.py \
  --output-base /data/zz2/National_model/outputs/relaxed_barrier_continuation_v0816_v1 \
  --control-root /data/zz2/National_model/run_control/relaxed_barrier_continuation_v0816_v1/campaign \
  --fallback-control-root /data/zz2/National_model/run_control/relaxed_barrier_campaign_v0812_v1 \
  --output-json /data/zz2/National_model/run_control/relaxed_barrier_continuation_v0816_v1/post_exact_summary.json \
  --output-csv /data/zz2/National_model/run_control/relaxed_barrier_continuation_v0816_v1/post_exact_summary.csv
```

输出必须至少审计：return code 与来源、solver/wall runtime、Barrier count/observed seconds per iteration、
GNU MaxRSS 与 process-tree peak、Constr/Bound/Dual/ComplVio、checkpoint manifest、root scientific
QC/manifest/state/basis 是否误生、raw physical QC、exact identity、四个宏观阈值和 failed hard checks。
JSON 中非有限数必须为 `null`；所有 relaxed rows 与 campaign 根均为
`scientifically_accepted=false`。若 continuation 新输出根中的 Base candidates 是历史根 symlink，必须用
`--fallback-control-root` 读取原始 GNU time；不得复制或篡改历史输出。

当前 pre-exact v2 已在三根真实结果上验证，JSON/CSV SHA256 为 `f1f95348...82a688`、
`e15331e5...a6cf50`。其中 macro comparison 仍来自旧 reference，只证明汇总器能读历史失败报告，
不得用于 winner。strict reference 完成、supervisor 重算 exact A/B 后必须另写 `post_exact_summary`，
保留 pre-exact 文件，不得原地覆盖。

## 2026-08-16 autonomous exact-A/B continuation supervisor

strict reference 进入 Barrier 后启动只等待 supervisor：

```text
supervisor_pid=4100799
control=/data/zz2/National_model/run_control/relaxed_barrier_continuation_v0816_v1
output=/data/zz2/National_model/outputs/relaxed_barrier_continuation_v0816_v1
reference=/data/zz2/National_model/outputs/relaxed_barrier_exact_reference_v0816_v1/base_744h_strict_crossover2
candidate_source=/data/zz2/National_model/outputs/relaxed_barrier_campaign_v0812_v1
poll_interval=300 s
```

执行状态机固定为：

1. reference wrapper PID 存活时只写 `waiting_reference` event，禁止创建新输出或启动 solver；
2. wrapper 退出后要求 `wrapper_exit_code=0`、stderr 空、`solve_report/solution_qc/result_manifest/
   run_identity/input_manifest` 齐全，并解析确认 `OPTIMAL + PASS`；任一失败以非零状态停止；
3. 通过后在新输出根为三个旧 Base/744 candidates 建只读 symlink，不复制、不覆盖、不重跑旧结果；
4. 以新 `CONTROL_ROOT` 和 exact `REFERENCE_ROOT` 调用冻结在 `d80f5b7` 的 serial campaign；audit
   自身还必须通过 input manifest、科学配置、LP 规模/Fingerprint 与 strict reference contract；
5. 无 exact `MACRO_PASS` 即停止；有 winner 才按最快 solver runtime 选择 profile，顺序为 V5/744、
   Base/1488、1488 checkpoint 完整时 Base/2160。fixed server 始终最多一个 solver。

supervisor 不是科学终态审计的替代品。每根退出后仍须人工核对 rc/time/stderr、checkpoint completeness、
工程 raw QC、宏观容量/发电/负荷/碳/成本账目、资源账本与科学根目录隔离。strict reference 当前 LP
Fingerprint 为 `2120635803`，presolve/order `226.12/99.29 s`，Barrier iteration 0 runtime
`363.60 s`；独立资源 sampler PID `4059299` 每 300 秒写 `resource_monitor.tsv`。

## 2026-08-16 current-identity strict Base/744 h reference 运行合同

当前 strict reference 已在 fixed server clean checkout `d80f5b7` 启动，wrapper PID `4046161`：

```text
OUTPUT=/data/zz2/National_model/outputs/relaxed_barrier_exact_reference_v0816_v1/base_744h_strict_crossover2
CONTROL=/data/zz2/National_model/run_control/relaxed_barrier_exact_reference_v0816_v1/base_744h_strict_crossover2
planning_year=2030; diagnostic_start_hour=0; diagnostic_hours=744
scenario=config/scenarios/base.json
solver=config/solver_profiles/barrier_16_crossover2_stable_basis_long_v1.json
export_diagnostic_state=false
```

启动门禁为 server full regression `184/184 PASS`（Gurobi 13.0.2，`94.693 s`）、clean/current checkout、
无 solver、目标根不存在、available RAM 约 114 GiB、`si/so=0/0`、memory PSI 0；均已满足。运行中：

1. 只读检查 `$CONTROL/pid` 的 wrapper/time/Python 树、`stdout.log`、`stderr.log`、`time.txt`、
   output `solver_telemetry.jsonl` 与 `gurobi.log`，以及 RAM/swap/vmstat/PSI；不得部署、改 profile、
   删除根或启动第二个 fixed solve。
2. PID 退出后不能以日志尾或 Gurobi status 单独验收；必须同时核对 wrapper rc/time、stderr、
   `solve_report.json=OPTIMAL`、`solution_qc.json=PASS`、全部 hard checks、current input manifest、
   valid `result_manifest.json`、LP variables/constraints/nonzeros/Fingerprint 与无 diagnostic state。
3. 对三个 relaxed candidates 使用更新后的 `scripts/audit_relaxed_barrier_macro.py` 另写新报告；旧报告
   必须保留并标记 `INVALID_AB_REFERENCE_IDENTITY`。只有 exact identity 为 PASS 后才计算宏观阈值，
   只有最快 exact `MACRO_PASS` 才晋级 V5/744 与 Base/1488/2160。
4. ParaCloud `4139552` 与本 reference 相互独立；继续只读，不 `scancel`、不改参、不启动 Stage B。
   13:07 snapshot 为 RUNNING 10 天 11:49、iteration 308、stderr 0、无终态/checkpoint。

## 2026-08-16 exact-LP relaxed Barrier A/B 修正

8 月 12 日 campaign 的三个候选本身均成功保存工程解，但 reference 指向旧数据/旧 LP；其
`NO_MACRO_PASS` 必须撤回为 **INVALID_AB_REFERENCE_IDENTITY**，不得用于选择或拒绝 8760 h 参数。
实施 `c53bd78` 后，`scripts/audit_relaxed_barrier_macro.py` 的 macro PASS 必须同时满足：

1. summary 的 planning year、scenario、hours、start hour 相同；
2. baseline contract、resolved scientific config、scenario config、formulation config SHA 相同；
3. 除 `solver_configuration` 外的 input manifest 逐行逻辑路径、SHA、size、required/existence/role 相同；
4. LP variables、constraints、nonzeros 与 Gurobi Fingerprint 全部相同；
5. reference 为 `Status=OPTIMAL`、`solution_qc=PASS` 且存在 result manifest；
6. 以上闭合后才评估 objective `<=1%`、capacity/generation L1 `<=2%`、period generation `<=0.5%`。

source bundle SHA 继续记录但不作为 LP 等价硬门禁，因为纯审计/导出脚本提交可能改变 provenance 而不
改变 LP；LP Fingerprint、科学配置与全输入 manifest 共同作为硬证据。旧 reference 的数据根为
`model_ready_20260730_flex_v5_4f717de_v1`、Fingerprint `-1670477391`；候选为
`model_ready_20260805_power_curve_v3_qc_d63a251_v1`、Fingerprint `2120635803`，明确不等价。

当前正确执行顺序是：部署 `c53bd78` 并完成 server regression → 当前代码/数据上单独运行一次
`barrier_16_crossover2_stable_basis_long_v1` Base/744 h strict reference → 验收 OPTIMAL/QC/manifest
与 exact identity → 重跑三个离线 macro audits → 仅 fastest exact `MACRO_PASS` 晋级 V5/744 和更长
时域。strict reference 不传 `--export-diagnostic-state`，不产生后续 state anchor；它仍是
`TEST_ONLY_TRUNCATED_HORIZON`。

已完成候选资源证据（均 rc 0/stderr 0）：

| 候选 | wall | solver | Barrier | MaxRSS |
|---|---:|---:|---:|---:|
| `5e-2/NumericFocus=2` | 1:28:31 | 4,927.57 s | 144 | 19,959,364 KiB |
| `1e-2/NumericFocus=2` | 1:34:34 | 5,289.26 s | 151 | 19,802,092 KiB |
| `1e-2/NumericFocus=1` | 1:17:32 | 4,275.73 s | 263 | 19,486,068 KiB |

## 2026-08-12 relaxed engineering export 的实际分层

第二次 1 h smoke 证明 load-center network QC 位于 `export_master_solution()`，不是
`export_operational_solution()`。实施提交
`247c3020dc7c667e161d61a331ff81d8b5f616fe` 后，工程导出按以下顺序执行：

1. master export：若且仅若异常是以 `Load-center solution QC failed:` 开头的 `RuntimeError`，记录
   `stage=MASTER_SOLUTION_EXPORT` 后继续；
2. operational export：若且仅若异常是以 `Production solution QC failed:` 开头的 `RuntimeError`，
   记录 `stage=OPERATIONAL_SOLUTION_EXPORT` 后继续；
3. 将所有预期严格 QC 失败写入 `engineering_raw_qc_error.json`，再执行 result summary；
4. 任何 OSError、非预期 RuntimeError、summary error 或其他异常一律向外抛出并使 smoke/campaign
   失败，禁止把代码/磁盘故障伪装成宽松 QC 结果。

第二次 smoke 根 `relaxed_barrier_smoke_1h_0d773d5_v2` 的 Python 本体由 `/usr/bin/time` 记录为
`Exit status: 0`、wall `0:37.84`、MaxRSS `496,276 KiB`、stderr 0；但远端审计 shell 在写 rc 时转义
错误，`return_code.txt` 为字面 `$rc`，所以该根仍不是启动门禁证据。第三次 smoke 必须使用无变量转义
歧义的 wrapper（例如直接让 `/usr/bin/time` 终态成为 SSH 终态，随后用独立命令写已核验状态），并要求
summary/raw-QC/contract 三者齐全后才能启动 744 h。

## 2026-08-12 relaxed Barrier 工程导出容错门禁

首次 Base/1 h、`BarConvTol=5e-2` 真解证明：宽松 Barrier 可以先形成完整有限 BarX/BarPi checkpoint，
但严格 load-center 物理 QC 可能在宏观摘要生成前因双向流而抛错。提交
`cc9293b25ef66ff4642eeb5860fb00b0a938b5ba` 后按以下规则执行：

1. `export_operational_solution()` 的任何异常都必须原样写入隔离目录
   `engineering_macro_analysis/engineering_raw_qc_error.json`；不得压低或删除既有物理阈值，不得把异常
   改写为 PASS。
2. 只要 master solution 可读，runner 仍继续生成 `annual_summary.json`、容量/发电汇总和
   `engineering_relaxed_analysis_contract.json`。contract 必须同时记录
   `STRICT_PHYSICAL_QC_EXPORT_FAILED`、原始异常和 `scientifically_accepted=false`。
3. `scripts/audit_relaxed_barrier_macro.py` 允许候选隔离目录不存在 `solution_qc.json`，但必须读取上述
   error 文件并在 A/B 报告中保留。`MACRO_PASS` 只评估冻结的 objective/容量/发电差异，绝不消除
   raw QC failure，也绝不升级成科学验收。
4. 1 h 复测必须同时满足：wrapper rc=0、stderr=0、完整 checkpoint、隔离 annual summary/contract/
   raw-QC error 可读、根目录无 scientific manifest/state/basis。满足后才可启动 744 h；如果缺失任一项，
   保留失败根并停在 smoke 门禁。

首次失败导出根为
`/data/zz2/National_model/outputs/relaxed_barrier_smoke_1h_9f5c2ca_v1`：wall `1:44.92`、MaxRSS
`497,512 KiB`、Barrier 49、solver `2.829 s`；ConstrVio `4.04e-6`，但 DualVio `0.628`、ComplVio
`29.509`，relative objective gap `1.389%`，最大/累计双向最小流 `3.599/76.294 GWh`。该根只用于验证
隔离与极宽松参数的风险，不得作为 744 h 预期质量或科学结果。

## 2026-08-12 fixed-server relaxed Barrier 自主 campaign 合同

本节响应作者新授权，覆盖此前“本地不得新增 744 h/更长时域”的旧执行限制；它不改变云端
`4139552` 的不取消合同，也不放松任何正式年度科学验收。fixed server 与 ParaCloud 可同时运行，
但 fixed server 内部仍只允许一个 CISPO/Gurobi solve。实施基线为
`9308ac002161a0b7971c28db8e46b5f42e8b91a8`。

1. 精确 profiles：744 h 使用
   `barrier_16_engineering_relaxed_bctol{5e2,1e2}_v1` 与
   `barrier_16_engineering_relaxed_bctol1e2_numeric1_v1`；统一
   `Method=2/Threads=16/Presolve=2/Crossover=0/SolutionTarget=1/
   FeasibilityTol=OptimalityTol=1e-5/ScaleFlag=2/Aggregate=1`，只改变
   `BarConvTol=5e-2/1e-2` 和 matched `NumericFocus=2/1`。744 h 为
   `TimeLimit=21,600 s/SoftMemLimit=40 GiB`；对应 long profiles 为
   `43,200 s/80 GiB`。不得临时原地改 JSON。
2. 每根必须同时传入 `--engineering-barrier-checkpoint-only` 和
   `--engineering-relaxed-barrier-analysis`。只有 `BarStatus=OPTIMAL` 才形成完整工程 checkpoint；
   `engineering_macro_analysis/` 可保存容量、调度、碳、成本与原始 hard checks，但根目录不得生成
   科学 `solution_qc/result_manifest`、planning state、basis 或 MGA。所有结果均
   `scientifically_accepted=false`，即使宏观对照 PASS 也不例外。
3. 执行脚本 `scripts/run_fixed_server_relaxed_barrier_campaign.sh` 的顺序固定为：Base/744 h
   `5e-2 → 1e-2 → 1e-2+NumericFocus1`；以 strict Jan Base/744 h 根比较相同 year/scenario/
   window，只有 objective 差 `<=1%`、技术容量/发电 normalized L1 各 `<=2%`、period generation
   差 `<=0.5%` 的最快候选晋级；随后 V5/744 h、Base/1488 h@3624，若完整 checkpoint 存在再
   Base/2160 h@2880。不得自动超过 2160 h。
4. 每根前确认没有 fixed-server CISPO/Gurobi、checkout clean/current、目标根不存在；744 h
   等待 available `>=64 GiB`，1488/2160 h 等待 `>=96 GiB`；均要求最新 `si/so=0/0`、memory
   PSI avg10=0。资源不足最多等待 12 h 后安全退出。每根用 `/usr/bin/time -v`、独立 stdout/
   stderr/return code 及前后 resource snapshot 留痕；失败根保留，campaign 只按既定分支继续。
5. 部署顺序：选择性提交并双推送 → 再次核验 cloud/fixed 实时状态 → fixed server fast-forward
   到精确 tip → `bash -n`、py_compile、server full regression → 全新 Base/1 h profile smoke。
   1 h 必须验证 complete checkpoint、隔离 analysis contract、无根目录科学 manifest/state/basis，
   才能后台启动 campaign。活动 PID 上不部署、不切 profile、不并发第二固定机求解。
6. 12:05 启动前快照：fixed server clean `3f739fd`、Gurobi 13.0.2、available 约 114 GiB、
   `si/so=0/0`、memory PSI 0；云 job 4139552 iteration 191、stderr 0、无终态/checkpoint。
   这是易变化状态，实际部署和 campaign 启动前都必须重读。

## 2026-08-12 11:50 iteration 190 监控基准

```text
job=4139552 RUNNING 6-10:32:11
Barrier iteration=190; solver runtime=552,067.53 s
iteration 158--190 average=47.571 min/iteration
latest Gurobi prim/dual/compl=4.00e1 / 9.35e-7 / 2.37e1
objective relative gap~=3.21
Slurm MaxRSS=362.913 GiB
allocated core-hours=14,835.493; actual CPU-hours=2,300.554
stderr=0; warnings=0; terminal/checkpoint files=absent
resource audit=round 12 / 13 records / SHA256 e299d4c7...a77b776d
```

目标相对间距从 iteration 158 的约 `3.69` 缓慢降至 `3.21`，长尾仍在推进。继续只读运行；禁止
人工取消、改参、重提、Stage B 或第二求解。

## 2026-08-11 10:16 iteration 158 监控基准

```text
job=4139552 RUNNING 5-08:58:07
Barrier iteration=158; solver runtime=460,730.61 s
iteration 145--158 average=47.263 min/iteration
latest Gurobi prim/dual/compl=6.97e1 / 1.92e-6 / 4.63e1
objective relative gap~=3.69
Slurm MaxRSS=362.913 GiB
allocated core-hours=12,380.987; actual CPU-hours=1,906.975
stderr=0; warnings=0; terminal/checkpoint files=absent
resource audit=round 11 / 12 records / SHA256 467e4f1b...d9c8dc6b4
```

目标相对间距从 iteration 145 的约 `3.90` 缓慢降至 `3.69`，长尾明显但进程仍活跃。继续只读运行；
禁止人工取消、改参、重提、Stage B 或第二求解。

## 2026-08-10 23:43 iteration 145 监控基准

```text
job=4139552 RUNNING 4-22:25:36
Barrier iteration=145; solver runtime=423,865.48 s
iteration 116--145 average=47.530 min/iteration
latest Gurobi prim/dual/compl=8.16e1 / 3.23e-6 / 5.61e1
objective relative gap~=3.90
Slurm MaxRSS=362.913 GiB
allocated core-hours=11,368.96; actual CPU-hours=1,744.324
stderr=0; warnings=0; terminal/checkpoint files=absent
resource audit=round 10 / 11 records / SHA256 581e3c52...db3bba0
```

目标相对间距由 iteration 116 的约 `8.56` 降至 `3.90`，长尾仍在推进但尚未收敛。继续只读运行；
禁止人工取消、改参、重提、Stage B 或第二求解。

## 2026-08-10 00:47 iteration 116 监控基准

```text
job=4139552 RUNNING 3-23:29:30
Barrier iteration=116; solver runtime=341,163.39 s
iteration 77--116 average=47.499 min/iteration
latest Gurobi prim/dual/compl=5.40e2 / 1.52e-5 / 2.70e2
objective relative gap~=8.56
Slurm MaxRSS=362.909 GiB
allocated core-hours=9,167.2; actual CPU-hours=1,391.305
stderr=0; warnings=0; terminal/checkpoint files=absent
resource audit=round 9 / 10 records / SHA256 9aa1f051...bf9052b
```

iteration 77--116 三项 telemetry 指标继续下降，但近期进入较缓长尾，目标仍未闭合。继续只读运行；
禁止人工取消、改参、重提、Stage B 或第二求解。

## 2026-08-08 17:51 iteration 77 监控基准

```text
job=4139552 RUNNING 2-16:33:41
Barrier iteration=77; solver runtime=230,014.78 s
iteration 48--77 average=46.061 min/iteration
latest Gurobi prim/dual/compl=4.45e4 / 5.22e-5 / 1.15e4
Slurm MaxRSS=362.765 GiB
allocated core-hours=6,197.893; actual CPU-hours=915.299
stderr=0; warnings=0; terminal/checkpoint files=absent
resource audit=round 8 / 9 records / SHA256 f0c7fdfa...09ede0
```

iteration 48--77 的三项 telemetry 指标已缩小约 `8.30e4/8.33e5/5.71e4` 倍，是明显收敛推进；
但 primal/dual objective 仍未闭合。继续只读运行，禁止人工取消、改参、重提、Stage B 或第二求解。

## 2026-08-07 19:45 iteration 48 监控基准

```text
job=4139552 RUNNING 1-18:27:23
Barrier iteration=48; solver runtime=149,868.82 s
iteration 35--48 average=46.951 min/iteration
Slurm MaxRSS=362.649 GiB
allocated core-hours=4,075.813; actual CPU-hours=572.464
stderr=0; warnings=0; terminal/checkpoint files=absent
resource audit=round 7 / 8 records / SHA256 d691d087...305badc
```

相对 iteration 35，primal/dual infeasibility 与 complementarity 分别下降
`77.27%/84.52%/77.95%`。继续只读运行；禁止由 iteration 数推断完成比例，禁止人工取消、改参、
重提、Stage B 或第二求解。

## 2026-08-07 09:59 iteration 35 监控基准

```text
job=4139552 RUNNING 1-08:41:08
Barrier iteration=35; solver runtime=113,247.02 s
iteration 23--35 average=47.032 min/iteration
Slurm MaxRSS=362.540 GiB
allocated core-hours=3,137.813; actual CPU-hours=421.861
stderr=0; warnings=0; terminal/checkpoint files=absent
resource audit=round 6 / 7 records / SHA256 13e567bd...2c6175
```

iteration 23--35 的 primal/dual infeasibility 与 complementarity 分别下降
`78.29%/76.82%/77.52%`，单步和内存稳定；但绝对残差仍远离验收。继续只读运行，禁止按
iteration 序号推断完成率，禁止人工取消、改参、重提、Stage B 或第二求解。

## 2026-08-07 00:00 iteration 23 监控基准

```text
job=4139552 RUNNING 22:42:29
Barrier iteration=23; solver runtime=79,383.98 s
iteration 18--23 average=47.105 min/iteration
Slurm MaxRSS=362.344 GiB
allocated core-hours=2,179.973; actual CPU-hours=267.629
stderr=0; warnings=0; terminal/checkpoint files=absent
resource audit=round 5 / 6 records / SHA256 73f3df39...30d967
```

残差继续单调改善、内存和单步时间稳定；继续只读运行。禁止由 iteration 23 推测完成百分比，禁止
人工取消、改参数、重提、Stage B 或第二求解。

## 2026-08-06 20:27 iteration 18 监控基准

```text
job=4139552 RUNNING 19:08:54
Barrier iteration=18; solver runtime=65,252.49 s
iteration 8--18 average=47.210 min/iteration
Slurm MaxRSS=362.188 GiB
allocated core-hours=1,838.24; actual CPU-hours=212.941
Gurobi current/max memory=351.054/354.498 GiB
stderr=0; numerical warnings=0; terminal files=absent
```

iteration 8--18 的 primal/dual residual 与 complementarity 均持续下降约 74%--78%，进程和16线程
仍活跃。不得从 iteration 序号外推完成百分比；继续按“不人工取消”合同运行。最新旁路账本为
`run_control/.../resource_audit_snapshots.jsonl`，5 records，SHA256
`fb390f551ef190720673a341037e2bcd8b6ce006905b549268a27c4f0f418c7f`。

## 2026-08-06 12:16 不取消与资源留痕合同

对 active job `4139552` 执行以下硬规则：除非作者明确授权，不得人工 `scancel`、发送终止信号、
修改 wall limit、重提或启动替代任务。Slurm/solver 自身终态不等于人工取消，仍须立即保存并审计现场。

资源证据采用三层来源：

1. `solver_telemetry.jsonl`：自动逐 Barrier iteration 记录 timestamp、solver runtime、work units、
   primal/dual/complementarity 与 Gurobi current/max memory；
2. `run_control/.../resource_audit_snapshots.jsonl`：每次人工审计追加 squeue/sstat 的 wall、allocated
   core-hours、actual CPU、MaxRSS、stderr 与最新 iteration；
3. terminal `sacct` + wrapper time：闭合 elapsed、CPUTimeRAW、TotalCPU、MaxRSS、exit/state，并生成最终
   Stage A resource audit。不得以运行中 snapshot 冒充终态总量。

历史比较文件 `historical_8760_comparison.json` 明确：job `4004585` 是完整 8760 h、24 h wall-limit
任务，最终 iteration 35/TIMEOUT；不是 24 h horizon。当前模型虽 raw rows 下降 25.344%，但 presolved
rows 仅下降 0.734%、nnz 反增 0.848%，因此仍是同量级超大 LP。当前 Factor NZ/Ops 分别下降
11.772%/21.119%，sampled MaxRSS 由 476.760 降至 361.648 GiB；16 threads 相对旧 32 threads
使单步约慢 50%。两任务科学身份不同，禁止把残差或目标直接作质量 A/B。

## 2026-08-06 12:06 Barrier 活动监控合同

job `4139552` 已完成 38.95 分钟 model build、4.84 小时 presolve 和 48.54 分钟 ordering，当前
为 Barrier iteration 8 的因子/步计算；最新已落盘 iteration 7。有效规模和资源证据：

```text
original LP = 50,907,234 rows / 41,458,383 cols / 492,835,195 nnz
presolved LP = 37,703,954 rows / 32,166,850 cols / 404,259,819 nnz
factor NZ = 3.395e10; estimated factor memory ~= 300 GB
Slurm MaxRSS = 379,125,920 KiB; Gurobi max memory = 354.50 GiB
latest Barrier = iter 7 at 11:27:07, runtime 34,202.25 s
```

近期每步约 45--48 分钟；短时无新 telemetry 是正常 factorization，不构成停滞。判断仍活跃时，
同时比较两次 `sstat ... AveCPU`：本次 58 秒内累计 CPU 增加约 15.5 分钟，与 16 threads 满载一致。
只有下列任一出现时才升级审计，不自动取消或重提：

1. Slurm state 不再为 `RUNNING`；
2. stderr、Gurobi log 出现 error/numerical trouble；
3. 累计 CPU 长时间不增长且无新 telemetry；
4. RSS 持续逼近 600 GiB soft limit；
5. 产生 checkpoint/solve report，此时立即执行终态或阶段审计。

当前 `solve_report.json`、`solution_qc.json`、`result_manifest.json` 与 Barrier checkpoint 均不存在，
符合运行中状态；仍禁止 Stage B、第二个 8760、V5 或下一年。

## 2026-08-06 01:19 当前 Stage A 监控对象

```text
job_id=4139552
state=RUNNING
node=m4cm1901
release=$HOME/National_model_cloud/20260806_8760_stagea_3f739fd_v5
output=$RELEASE/outputs/2030_8760_base_stage_a_barrier_v2
control=$RELEASE/run_control/2030_8760_base_stage_a_barrier_v2
resources=96 CPU / 700G / billing 96 / TimeLimit UNLIMITED
```

该 job 已通过 compute data load `4139550`（31×8760、wave、36,686 VRE、2,030 hydro）及主 runner
preflight（67 PASS、0 HARD_FAIL），当前为 LP model build。01:19 MaxRSS 3.80 GiB、stderr 0 bytes，
尚无 Gurobi log/telemetry。监控命令：

```bash
squeue -j 4139552 -o '%.18i %.12T %.10M %.10l %.6D %R'
sstat -j 4139552.batch --format=JobID,AveCPU,MaxRSS,MaxVMSize,AveRSS -P
tail -n 80 "$CONTROL/slurm-4139552.err"
tail -n 80 "$OUTPUT/gurobi.log"
tail -n 20 "$OUTPUT/solver_telemetry.jsonl"
```

build 期间不存在 `gurobi.log` 是正常状态；只有 model build 完成并调用 `optimize()` 后才出现 solver
日志/telemetry。禁止因短时无日志取消；也禁止启动 Stage B、第二个 8760、下一年或 V5。前三个失败
主 jobs `4139419/4139479/4139496` 均只保留为 launcher/dependency fail-fast 证据。

## 2026-08-06 01:13 cloud xarray 私有 overlay 合同

job `4139496` 在 provenance/input manifest 后、wave data load 前因 `ModuleNotFoundError: xarray`
退出，Slurm 7 秒；没有 LP build 或 Gurobi solve。共享 cloud env 已含 netCDF4/cftime，禁止为本任务
原地修改该环境。新 release 必须复制已校验的纯 Python wheel：

```text
xarray-2025.1.2-py3-none-any.whl
SHA256 a7ad6a36c6e0becd67f8aff6a7808d20e4bdcd344debb5205f0a34b1a4a7f8d6
```

以 `pip --no-index --no-deps --target=$RELEASE/python_overlay` 安装，并在版本化 env manifest 中设置
`PYTHONPATH=$RELEASE/python_overlay`。主任务前必须新增低资源 compute-node 数据加载门禁：导入
`xarray/netCDF4`、解析 Stage A profile、执行完整 Base/8760 `load_model_data`，但不建 LP/不求解。
只有该门禁 rc 0 后才允许再次提交单个 96 CPU/700G Stage A。

## 2026-08-06 01:10 Stage A 环境变量导出修正

job `4139479` 只完成 profile preflight；在 provenance 门禁前报告全部 data inputs missing。
`/usr/bin/time` 为 `1.09 s/83,900 KiB/0 swap/exit 1`，无 LP build、solver telemetry 或 Gurobi log，
不得作为 8760 h 求解样本。原因是 `.env` 中的普通赋值没有自动继承到子 Python。

从 `b5cad0d` 起必须按以下方式加载，且静态测试要锁定三行相邻：

```bash
set -a
source "$ENV_FILE"
set +a
```

失败 `_v3`/job `4139479` 不得复用 output root。只允许从 clean `b5cad0d` 后续文档 tip 的 Linux
archive 新建 `_v4` release，再做 `bash -n`、LF、manifest、queue 与 `sbatch --test-only` 检查。
Stage B/下一年/V5 仍未授权。

## 2026-08-06 01:06 Stage A 首次提交失败与 wrapper 修正

job `4139419` 仅可解释为 0 秒 launcher failure：`FAILED 1:0`、`Elapsed/CPUTime=0`、
`TotalCPU=0.007 s`、`MaxRSS=0`、stdout/stderr 0 bytes；不得计入 8760 h build/solver 样本。
资源合同本身已由调度器确认：`96 CPU/700G/billing=96/TimeLimit=UNLIMITED`。

禁止从 Slurm 脚本 `$0` 推导 release，因为执行对象是 spool copy。提交 `d857f8d` 后 wrapper 必须：

```bash
test -n "${SLURM_SUBMIT_DIR:-}"
RELEASE="$(cd "$SLURM_SUBMIT_DIR/.." && pwd)"
test -d "$RELEASE/repo"
```

且 `sbatch` 必须从精确的 `$RELEASE/repo` 调用。失败的 `_v1`（CRLF archive）与 `_v2`
（旧 `$0` resolver/job 4139419）release 只读保留；不得原地修补或重提。使用 fixed-server Linux
`git archive` 新建 `_v3`，重跑 `bash -n`、profile load 和 `sbatch --test-only` 后才可提交新的唯一
Stage A。仍不授权 Stage B、下一年、V5 或第二并发求解。

## 2026-08-06 00:57 2030 Base 8760 h Stage A v2 提交合同

本条取代 2026-08-05 14:50 节中 Stage A v1 的严格容差、7 天 Gurobi/Slurm 时限和 128 CPU
资源建议；不改变数学模型、Base 情景、数据或 Stage B 的独立授权边界。

```text
profile=barrier_checkpoint_full_year_cloud_v2
Method=2 Threads=16 Presolve=2 Crossover=0 SolutionTarget=1
BarConvTol=1e-8 FeasibilityTol=1e-6 OptimalityTol=1e-6 MarkowitzTol=0.01
NumericFocus=2 ScaleFlag=2 Aggregate=1 DualReductions=1 InfUnbdInfo=0
TimeLimit=UNSET SoftMemLimit=600 GiB
Slurm=amd_a8_768, 1 node, 1 task, 96 CPU, 700G, no --time
```

只允许使用 `cloud_runs/scripts/cloud_cispo_8760_stage_a_barrier_checkpoint_v2.sbatch`。提交前必须：

1. local/origin/GitHub/fixed server/cloud code identity 一致；fixed server idle/clean，cloud `squeue`
   为空，Stage A output/control roots 不存在；
2. cloud file release 绑定当前 Power_curve v3_qc model-ready、CF、hydro、wave tree hashes；raw GRFR
   未复制不影响模型运行，但不得声称通过 `--require-raw-grfr`；
3. 先用 `sbatch --test-only` 验证 `96 CPU/700G` 请求，不产生求解费用；若调度器拒绝，只能重新
   审计资源，不得静默改变内存、线程或模型参数；
4. 仅提交一个 Stage A，不设置依赖任务，不自动 Stage B/2040/V5。运行中监控 `squeue/sstat`、
   `gurobi.log`、telemetry 与控制日志；因没有时间上限，只在明确 solver failure、内存临界、节点/
   license 故障或经人工复核的长期无进展时 `scancel`，不得以正常长 factorization 静默期误判停滞；
5. 完成终态必须核对 wrapper rc/time、`solve_report.json`、checkpoint manifest、两份向量长度/
   finite/SHA256、input/config/Git/Fingerprint/order hashes。只有
   `ENGINEERING_BARRIER_CHECKPOINT_ONLY + deferred_crossover_eligible=true` 才可等待单独 Stage B
   授权；`RECOVERY_ONLY` 只作取证。

Stage A 不生成科学 `result_manifest.json`、QC 结论或 planning state；其 `BarPi` 只是工程影子价格
原始向量。`deferred_crossover2_full_year_cloud_v2` 虽已作为候选实现，但本合同不授权提交。

## 2026-08-05 20:35 Power_curve v3_qc 当前部署合同

fixed server 当前根：

```bash
export CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260805_power_curve_v3_qc_d63a251_v1
export CISPO_CF_ROOT=/data/zz2/National_model/data/hourly_cf
export CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse
export CISPO_RAW_GRFR_ROOT=/data/zz2/National_model/data/grfr_raw_2019
export CISPO_WAVE_ROOT=/data/zz2/National_model/data/wave_energy_20260727
PYTHON=/home/zz2/.local/envs/cispo-2030/bin/python
```

必须使用 `config/release_contract_v0805_power_curve_v3_qc.json`；旧 v0729/v0730 contracts 是历史
身份。已验收证据根：

```text
/data/zz2/National_model/run_control/deployment_20260805_power_curve_v3_qc_3cb3939_v2
/data/zz2/National_model/run_control/gates_20260805_power_curve_v3_qc_3cb3939_v1
/data/zz2/National_model/outputs/gates_20260805_power_curve_v3_qc_3cb3939_v1
```

ParaCloud 有效文件发布为
`$HOME/National_model_cloud/20260805_power_curve_v3_qc_3cb3939_v2`；环境路径与完整哈希见
`manifests/{cloud_environment_paths.env,cloud_release_manifest.json}`。云端未提交 compute job，且未
同步 8.3 GiB raw GRFR；未来若要求 `--require-raw-grfr` 必须先版本化补齐。无 `_v2` 的 sibling
是失败 clone，不得运行。下一步长门禁仍需独立授权；禁止复用 test-only states、旧 outputs/basis，
或把 1 h/24 h 成本差解释为年度结果。

## 2026-08-05 16:05 Power_curve_V2 v3_qc 负荷更新合同（本地已完成，服务器未部署）

本地权威源：

```text
D:/codeenv/pycharmproject/National_RL/Power_curve_V2/outputs/
future_8760_projection_ev_calibrated_v3_qc/tables/
future_hourly_load_2025_2060_8760.csv.gz
SHA256 8ed727745afda68b7114b08ea65660392cb374b68f203a6633bbbc9a13af791a
```

上游含 8 年；National_model 必须继续筛选为 2025/2030/2040/2050/2060。禁止把
2035/2045/2055 静默加入 `model_years.csv` 或序贯求解。负荷必须整体转换，不能只替换 `ev_gw`：
新版 EV 年电量较旧输入高 4.219004%，base residual 已同步回算，全国总负荷年电量保持不变。

本地重建顺序：

```powershell
# 1. 使用 config/model_data_config.json 的新 future_hourly_load，
#    仅调用 scripts/build_cispo_data_package.py::build_load。
python scripts/build_flexible_load_envelope_v3.py
python scripts/build_flexible_load_v4_inputs.py --data-root data
python scripts/validate_flexible_load_v4_inputs.py --data-root data `
  --source-manifest data/load/hourly_load_2025_2060.csv.gz `
  --source-manifest data/load/flexible_load_envelope_v3.manifest.json `
  --source-manifest config/flexible_load_v4_source_registry.csv `
  --source-manifest config/flexible_load_v4_source_count_qa.csv `
  --source-manifest config/flexible_load_v4_central_parameters.csv
python scripts/build_flexible_load_v5_inputs.py --data-root data
python scripts/validate_flexible_load_v5_inputs.py --data-root data
python scripts/smoke_test_data_package.py
```

验收硬门禁：主表 1,357,800 行；155 个省年组各 8760 h；source→model key 全闭合；最大
MW→GW 转换误差不高于 `1e-12 GW`；逐时四分量闭合不高于 `1e-9 GW`；legacy 视图必须等于
四决策年精确子集；V4/V5 manifests 必须直接登记主表 SHA256；data smoke 与相关回归全 PASS；
`data/output_manifest.csv` 不得有 size/SHA256 mismatch。

截至该本地里程碑，服务器尚未部署。执行部署时：先实时确认服务器 idle/clean；从当前版本化数据根
复制到全新、明确命名的根，只替换本次 load/flexibility/provenance 文件；设置新 `CISPO_DATA_ROOT`
后完整运行 readiness、release、V4/V5 validators、data smoke 和新的 1 h/24 h Base--V5 配对门禁。
不得原地覆盖旧根，不得复用旧 output、planning state、basis 或 result manifest。

## 2026-08-05 14:50 8760 h 两阶段执行合同（已实现、未授权提交 job）

### 资源与调度硬门禁

1. 只允许 ParaCloud `amd_a8_768` 计算节点；禁止 login node 和 fixed server。两个 cloud
   profiles 在 runner 内要求 `available >=640 GiB`。当前 fixed server 仅约 `113 GiB`，即使
   `SoftMemLimit=600` 不会立即分配内存，也不得绕过该 guard。
2. `amd_a8_768` 为 128 CPU、`RealMemory=768000 MB`/Slurm `750G`，且
   `MaxMemPerCPU=6144 MB`。推荐 `--nodes=1 --ntasks=1 --cpus-per-task=128 --mem=700G`
   （可配 `--exclusive`），应用内保持 `Threads=16`；其余 CPU 是内存配额/整节点计费，不得
   误报为 Gurobi 128 threads。启动前必须再次核对账户配额、单价与预计 128 core-hours/
   wall-hour 成本。
3. Gurobi `TimeLimit=604800 s`，Slurm wall time 不得也设成恰好 7 天。建议至少
   `--time=7-12:00:00 --signal=B:TERM@1800`，使 runner 在提前 TERM 时调用
   `model.terminate()`，并给 BarX/BarPi、stderr/time 和审计文件留写出窗口。Slurm kill、节点
   故障或磁盘失败仍可能阻止检查点完整写出，不能声称绝对保证。
4. 提交前重新核对 local/origin/GitHub/server commit、server/cloud queue、不可变 data root
   及 release SHA256、Base/scenario/formulation、2030 predecessor state、目标 roots 不存在、
   磁盘与 license。Stage A 与 B 必须串行；任何时刻只允许一个 8760 h solve。

### Stage A：工程 Barrier checkpoint

profile：`config/solver_profiles/barrier_checkpoint_full_year_cloud_v1.json`：

```text
Method=2 Threads=16 Presolve=2 Crossover=0 SolutionTarget=1
BarConvTol=1e-9 FeasibilityTol=1e-7 OptimalityTol=1e-7
NumericFocus=2 ScaleFlag=2 Aggregate=1 DualReductions=1 InfUnbdInfo=0
TimeLimit=604800 SoftMemLimit=600
```

命令骨架（`STAGE_A_ROOT` 必须是新绝对路径；其余 case/state 参数按冻结 release 补齐）：

```bash
$PYTHON scripts/run_cispo_2030_full_year.py \
  --planning-year 2030 \
  --horizon full_year \
  --solver-config config/solver_profiles/barrier_checkpoint_full_year_cloud_v1.json \
  --engineering-barrier-checkpoint-only \
  --output-dir "$STAGE_A_ROOT"
```

Stage A 成功的工程终态不是 scientific acceptance，而是：

- `solve_report.run_completion_status=ENGINEERING_BARRIER_CHECKPOINT_COMPLETE`；
- checkpoint `BarStatus=OPTIMAL`，`BarX/BarPi` 长度正确、全 finite、SHA256 有效；
- checkpoint status 为 `ENGINEERING_BARRIER_CHECKPOINT_ONLY`、
  `scientifically_accepted=false`、`deferred_crossover_eligible=true`；
- input/config/Git/Gurobi/Fingerprint/LP dimensions，以及完整 `VarName` 和
  `ConstrName+Sense` 顺序 SHA256 齐全；末次 Barrier primal/dual objective、残差、
  complementarity 已从 telemetry 记录。

Stage A 在 checkpoint 完整时可返回 wrapper rc 0；该 rc 仅表示工程检查点完成。不得生成或
补写 scientific `result_manifest.json`、planning state、MGA/basis，也不得把 raw `BarPi`
作为论文价格。若 `BarStatus!=OPTIMAL`、向量不有限/不完整、顺序 hash 或写出失败，则 Stage A
rc 非零并保留现场；不得从残缺文件启动 Stage B。

### Stage B：exact-LP deferred Crossover=2

profile：`config/solver_profiles/deferred_crossover2_full_year_cloud_v1.json`。除 Stage A 的严格
numerics/resource limits 外，显式设置 `LPWarmStart=2/Crossover=2/CrossoverBasis=1/
SolutionTarget=0`。`BarConvTol` 保留为身份记录；当完整 PStart/DStart 被 Gurobi 接受时，官方
合同是直接对 crushed presolved starts 做 crossover，不执行 Barrier iterations。

```bash
$PYTHON scripts/run_cispo_2030_full_year.py \
  --planning-year 2030 \
  --horizon full_year \
  --solver-config config/solver_profiles/deferred_crossover2_full_year_cloud_v1.json \
  --primal-dual-checkpoint-in "$STAGE_A_ROOT" \
  --allow-primal-dual-crossover \
  --allow-engineering-barrier-checkpoint \
  --allow-deferred-crossover-planning-state \
  --output-dir "$STAGE_B_ROOT"
```

只有当 Stage B 为 `OPTIMAL`、`ConstrVio/BoundVio/DualVio` 通过 strict contract、
`solution_qc=PASS`、全部 hard checks（当前 Base 预期 58/58）、current input manifest、valid
result manifest、`Pi` 导出及 wrapper/time 均通过，才登记科学结果并允许上述显式 planning
state。任何不满足项均保留 Stage A，不重跑 Barrier、不重标 Stage B、不补 manifest；是否以
同一 Stage A 重新尝试另一项 Stage B 必须另行授权并使用新 root。

### 当前验证与未决项

- implementation commit `369506010b5bc876676941e456d9574187e0f293`；本地 targeted
  `12/12 PASS`，fixed server Gurobi 13.0.2 targeted `12/12 PASS`。
- 本地全套 124 tests 中 6 项因未配置外部 `CISPO_WAVE_ROOT` 失败；云端提交前必须在冻结
  production roots 上重跑完整 regression/readiness/release/input audits，不得忽略该缺口。
- 目前 ParaCloud queue 为空，没有 Stage A/B root、Slurm script 或 job。下一步是确定精确
  Base/scenario/data/state identity、预算与 wrapper SHA256；本节不等于付费提交授权。

## 2026-08-05 14:09 744 h solver 实证基线

1. 当前 744 h 执行证据仅覆盖 Crossover=2：11 根执行、9 accepted、2 TIME_LIMIT；accepted
   solver runtime 平均 `8.89 h`，Barrier/Crossover 平均 `2.60/6.08 h`。
2. 服务器保留报告中不存在 `744 h + Crossover=0` 根。不得把 recovery checkpoint、
   24 h Barrier-only 参数诊断或规格设计目标称为 744 h Barrier-only 门禁。
3. 新 Barrier-only 路线必须使用全新 profile/root，按 24 h→168 h→744 h 逐级闭合，不能
   resume 当前 TIME_LIMIT 根或跳过长时域验证进入 8760 h。

## 2026-08-05 13:52 8760 h solver route 未闭合

1. Barrier-first 是待重新验证的设计目标，不是当前 production route；24 h 当前模型的
   20 个 Barrier-only 组合均未同时通过严格 primal/dual acceptance。
2. `barrier_16_crossover2_stable_basis_long_v1` 只在截断时域冻结；本轮 744 h 的两个
   Crossover TIME_LIMIT 证明它不能未经年度门禁直接用于 8760 h。
3. 当前任何 8760 h solve 均 fail closed。先对 recovery BarX/BarPi 做 exact-LP 离线审计，
   再完成新容差 profile 的 24 h/168 h/744 h A/B；不得以 `BarStatus=OPTIMAL`、恢复向量或
   9 个 accepted 744 h 根替代年度 solver qualification。

## 2026-08-05 13:47 8760 h 与 Crossover 超时后的内点向量边界

1. 对 `Method=2/Crossover>0`，若 Gurobi 13 已有 `BarStatus=OPTIMAL` 而最终因
   TIME_LIMIT/MEM_LIMIT 等非最优终止，runner 会尽力导出 `BarX/BarPi`。导出并非保证：
   属性不可读、磁盘/内存或写出错误时只会生成 checkpoint error。
2. 成功写出的超时 checkpoint 必须标记 `RECOVERY_ONLY_UNACCEPTED_SOLVER_RESULT`；不得
   当作 QC PASS、result manifest、planning state、accepted shadow prices 或可直接恢复的
   factorization。Jan/2050 与 Jun/2060 是已验证实例，均 `deferred_crossover_eligible=false`。
3. 8760 h 默认禁止 inline Crossover；未传 `--allow-inline-crossover` 时会在 optimize 前
   hard-fail。生产路线应为 `Method=2/Crossover=0/SolutionTarget=1`，只有最终 `OPTIMAL +
   strict primal/dual + QC + hard checks + manifests` 才导出
   `ACCEPTED_PRIMARY_BARRIER_SOLUTION`，之后再以 exact-LP 独立后置 Crossover。
4. 当前模型的 Barrier-only 路线尚未重新通过门禁，因此上述设计不构成立即启动 8760 h
   的授权。先完成小根/长根参数与宏观结果 A/B；禁止把 recovery-only 文件改标或续年。

## 2026-08-05 13:42 Phase 2 停止后的 fail-closed 边界

1. 当前无 Phase 2/CISPO/Gurobi/sequence PID。Jan Base/2050 与 Jun Base/2060 均为
   `TIME_LIMIT`，无 QC/result manifest/planning state；不得 resume、重标、补 manifest、
   使用其中间 Barrier/Crossover 解续接或手工跳到 Jan/2060/V5。
2. Oct Base 四年 sequence 完整 PASS；Oct/2060 已严格复验 58/58、Pi 与双 manifests。
   Oct V5 没有启动：Base 完成后 resource gate 因 memory PSI avg10 `0.54/0.54` 返回 90，
   `oct6552_window.stderr=RESOURCE_GATE_BLOCKED`，目标 V5 root 不存在。
3. 本次失败定位为 Crossover 路径而非内存/build：Jan/Jun Crossover 分别持续约
   `22.14/21.81 h` 后触发 24 h TimeLimit。后续不得只延长 TimeLimit；先用全新小根比较
   放宽一级 `FeasibilityTol/OptimalityTol=1e-6` 的候选，保持 physical QC `1e-5`、58 checks、
   manifests 和宏观结果对照；只有 24 h/168 h/单根 744 h 闭合后才能建立新 Phase 2 roots。
4. 13:42 服务器 idle，available `116,236 MiB`、swap `596/2047 MiB`、实时 `si/so=0/0`、
   memory/IO PSI 0，ParaCloud 空；checkout clean `3f123f0`。当前资源恢复不等于自动授权
   重跑、V5、8760 h、basis/MGA、Crossover=3 或付费云。

## 2026-08-05 00:26 Phase 2 Base 8/12 与临近 TimeLimit 监控

1. Oct Base/2050 已严格接受，Base 累计 `8/12`。Oct/2050 的 solve/QC/58 checks/input/result
   manifests/Pi、counterflow 与 storage/V2G overlap 已逐项复验，不得因 runtime 较长降级。
2. 当前只读监控对象为 Jan Base/2050、Jun Base/2060 与正在 build 的 Oct Base/2060。
   Jan/Jun Crossover 中间 infeasibility 已达极大数量级，Jan 接近 `86,400 s` TimeLimit。
   PID 存在时不得 kill、改 TimeLimit/容差/profile 或据中间日志补写任何结果。
3. 任一进程退出后先读取 `solve_report.json`、`solution_qc.json`、`result_manifest.json`、
   sequence/control stderr 与 wrapper exit。缺少任何终态文件、非 `OPTIMAL`、非 58/58 或
   manifest invalid 均 fail closed；对应 runner 应停止，不得手工跳至下一年或 V5。
4. 00:26 available `74,239 MiB`、swap `623/2047 MiB`、最新 `si/so=0/0`、memory PSI
   avg10/60 `0.02/0.08`、IO PSI `4.70/1.93`、磁盘余 `3.7 TiB`；stderr 0、ParaCloud 空。
   server checkout 继续冻结 clean `3f123f0`，不启动第四条、8760 h、basis/MGA、
   Crossover=3、付费云或部署 docs tip。

## 2026-08-04 13:57 Phase 2 Base 7/12 accepted 监控对象

1. 新增 accepted roots 为 Jan Base/2040、Jun Base/2050、Oct Base/2040；三根已逐项验证
   `OPTIMAL + acceptance/QC PASS + 58/58 + current input + valid result manifest + Pi`，且
   counterflow、storage overlap、EV V2G overlap 均为零。Base 累计 `7/12` accepted。
2. 当前只读监控对象为 Jan Base/2050、Jun Base/2060、Oct Base/2050，三者均处于
   Crossover/simplex。中间 primal/dual infeasibility 允许大幅振荡，不得以 telemetry 单点
   判断成功或失败；必须等待 wrapper 退出并读取 solve/QC/result 三份终态文件。
3. 13:57 资源为 available `74,374 MiB`、swap `507/2047 MiB`、最新 `si/so=0/0`、
   memory/IO PSI 0、磁盘余 `3.7 TiB`；control stderr 全部 0，ParaCloud 空队列。资源正常只
   授权现有三条继续，不授权第四条或提前独立 V5。
4. server checkout 继续冻结 clean `3f123f0`。每个窗口仅在 Base/2060 accepted 且 Base
   sequence rc=0 后，由同一 runner 自动启动其 V5 四年链。不得部署 docs tip、改 profile、
   复用 basis、补写 manifest或运行 Crossover=3/8760 h/MGA/付费云。

## 2026-08-04 00:50 Phase 2 当前监控对象与新增 accepted roots

1. 新增 accepted roots 为 Jun Base/2040 与 Oct Base/2030；两根已逐项验证
   `OPTIMAL + acceptance/QC PASS + 58/58 + current input + valid result manifest + Pi`，且
   counterflow、storage overlap、EV V2G overlap 均为零。不得仅凭 sequence 已续年反推接受，
   后续每根仍须重复读取三份终态文件并运行 input/result validators。
2. 当前只读监控对象为 Jan Base/2040 PID `1152769`（Crossover/simplex）、Jun Base/2050
   PID `2949044`（Barrier）与 Oct Base/2040 PID `2270187`（Crossover/simplex）；三个外层
   runner/sequence 仍活动，V5 尚未启动。以实时 PID/telemetry 为准，不沿用本节 PID 作未来状态。
3. 00:48 资源为 available `70,941 MiB`、swap `507/2047 MiB`、实时 `si/so=0/0`、
   memory/IO PSI 0、CPU `65--66% idle`、磁盘余 `3.7 TiB`；全部 case/window stderr 0，
   ParaCloud 空队列。资源安全只授权现有三条继续，不授权第四条或提前独立 V5。
4. server checkout 继续冻结 clean `3f123f0`。不得部署 docs tip、修改 profile、复用 basis、
   补写 manifest、运行 Crossover=3/8760 h/MGA/付费云。Base 四年 rc=0 后，由同一 runner
   自动启动同窗口 V5；任何年度失败则对应 runner fail closed 并保留现场。

## 2026-08-03 17:25 Phase 2 当前年度监控对象

1. Jan Base/2030 与 Jun Base/2030 已分别严格接受，input/result validators 均 `(true, [])`，
   hard checks 58/58、dual Pi、counterflow strict zero；当前活动年份为 Jan/2040 与 Jun/2040。
2. Oct Base/2030 仍在 Crossover/simplex，约 1.008m iterations；PID 存在且无终态文件时只读
   telemetry/log，不把 Barrier interior objective 或中间 primal/dual infeasibility当作终态。
3. 继续检查三棵进程树、available/swap/PSI、stderr 与逐年三份终态报告。任何年度只有同时满足
   `OPTIMAL + contract/QC PASS + 58/58 + current input + valid result manifest + Pi` 才允许 runner
   自动续年。不得启动第四条、改 profile、部署 docs tip、复用 basis 或补写 manifest。

## 2026-08-03 10:45 Phase 2 三并发活动合同

本节按作者最新决策取代下方“最多两个/禁止第三条”条款；其余 solver、state、QC 与禁令不变。

1. 活动窗口为 Jan PID `3742233`、Jun PID `3746869`、Oct PID `4173801`。Oct 根为
   `/data/zz2/National_model/outputs/planning_sequence_2030_2060_744h_oct6552_3f123f0_base_v1`，
   scope `[6552,7296)`。server checkout 继续固定 clean `3f123f0`。
2. 第三实例按 24 GiB 规划；启动条件为 available `>=56 GiB`、预计启动后 `>=32 GiB`、
   `si/so=0/0`、memory PSI 0。Oct 专用 `window_runner_56g.sh` 只修改资源阈值，SHA256
   `e22f1696445b88458b1927fc1e803ca8ae7ec8c2f00ccf34f2c8feb6111c6be1`。
3. 三个 runner 各自严格 Base 四年→V5 四年；V5 不作为额外第四实例提前启动。不得再启动任何
   第四条 solve。持续审计三棵进程树、telemetry/log、available/swap/PSI、stderr 和终态合同；
   任一失败由对应 runner 停止并保留现场。

## 2026-08-03 08:56 Phase 2 双窗口活动监控对象

1. server checkout 固定 clean `3f123f0598e95151e8492f784ca79521569f57f0`；活动 PID 存在时
   不 fast-forward、不改 profile/runner。control root：
   `/data/zz2/National_model/run_control/phase2_3f123f0_v1`。
2. Jan window PID `3742233`，Base root
   `/data/zz2/National_model/outputs/planning_sequence_2030_2060_744h_jan0_3f123f0_base_v1`，
   scope `[0,744)`；Jun-15 PID `3746869`，Base root
   `/data/zz2/National_model/outputs/planning_sequence_2030_2060_744h_jun15_3960_3f123f0_base_v1`，
   scope `[3960,4704)`。各 runner 会在 Base 四年全部 accepted 后自动进入同窗口 V5。
3. 只读检查两个 process trees、当前年度 `solver_telemetry.jsonl`/`gurobi.log`、available/
   swap/vmstat/PSI、window/case stderr 与三份终态报告。任何中间 Barrier objective 都不是终态。
4. 禁止启动第三条。任一窗口 Base 或 V5 的任一年度失败时，该 runner 由 `set -e` 停止并保留
   现场；不得 resume、补 manifest 或换参数。窗口全部结束后按 strict contract 审计，释放槽位
   且资源门禁通过才启动 Oct `start-hour=6552`。

## 2026-08-03 08:51 Phase 2 744 h 资源门槛修订与立即启动合同

本节按作者最新决策取代下方所有 Phase 2 `available>=96 GiB` 与“禁止并发第二求解”的旧条款；
旧条款保留为历史记录，不再控制本轮 Phase 2。模型、solver/QC 和科学边界没有改变。

1. 历史 744 h 的 process-tree peak 为 `21.484--21.92 GiB`，solver max memory 曾约
   `23.13 GiB`；运行规划按每实例 `24 GiB`，不得声称硬上界为 20 GiB。
2. 第一条新 744 h sequence 的启动门禁为：checkout clean 且为双推送 tip、无 CISPO/Gurobi
   PID、available `>=64 GiB`、最新 `vmstat si/so=0/0`、memory PSI 0、磁盘充足、目标根不存在、
   ParaCloud 队列已核验。运行中 available `<48 GiB` 时不得启动下一条 sequence。
3. 立即先启动 `start-hour=0` Jan Base 四年 sequence。第二条并发 sequence 只有在首实例当前
   solver/process-tree 内存 `<=24 GiB`、按 `24 GiB` 估计第二条启动后 available 仍 `>=32 GiB`、
   `si/so=0/0`、PSI 0、CPU/磁盘正常时才可启动；最多两个 CISPO solves，绝不启动第三个。
4. 每个窗口仍保持 Base 四年 accepted 后才启动同窗 V5；并发只能发生在不同窗口的独立 sequence
   之间，不得打乱单一 sequence 内 2030→2040→2050→2060 state chain。任一年度不是
   `OPTIMAL + acceptance/QC PASS + 58/58 + current input + valid result manifest + Pi + wrapper rc 0`
   即停止对应 sequence 并保留现场。
5. profile 仍为 `config/solver_profiles/barrier_16_crossover2_stable_basis_long_v1.json`；不复用
   `.bas`，不运行 Crossover=3、MGA、8760 h 或付费云。全部 744 h 根仍为
   `TEST_ONLY_TRUNCATED_HORIZON`。

## 2026-08-03 03:17 Phase 1 终态与 Phase 2 资源等待

1. Phase 1 control root `/data/zz2/National_model/run_control/phase1_b2206d9_v1` 已完成；
   `phase1.stdout` 末尾为 `PHASE1_DONE`，`phase1.stderr` 为 0 字节，六个 sequence wrapper
   均 `Exit status: 0`。不得再把 PID `1314144` 当作活动任务或 resume 任一 Phase 1 root。
2. `ab_audit_{1h,24h,168h}.json` 均 `PASS`；`phase1_strict_audit.json` 为 24/24 accepted、
   零 failures。逐根仍必须保留 solve/QC/58 checks/input/result manifests/dual/state 证据。
   168 h Base/V5 的 2050 de-minimis warnings 已显式保留 observed/limits，不得报告为 strict zero；
   其余根 strict zero，全部 storage/V2G overlap 为零。
3. Phase 2 不因 Phase 1 完成而忽略资源门禁。每个新 744 h sequence 前重新确认：无 CISPO/
   Gurobi PID、server checkout clean 且为双推送 tip、available `>=96 GiB`、最新
   `vmstat si/so=0/0`、memory PSI 0、磁盘充足、目标 output/control root 不存在、ParaCloud
   `squeue -u a8s001819` 已核验。03:17 available 约 `87 GiB`，故当前只等待。
4. 资源满足后 Phase 2 仍严格串行：`start-hour=0` Jan Base→V5，`3960` Jun-15 Base→V5，
   `6552` Oct Base→V5；每条均为 2030→2060 四年 sequence，共 24 个 solve。沿用已冻结的
   `barrier_16_crossover2_stable_basis_long_v1.json`，不复用 `.bas`，不在活动 run 中切参。
5. 任一年度不是 `OPTIMAL + acceptance/QC PASS + 58/58 + current input + valid result manifest +
   Pi + wrapper rc 0`，立即停止对应 sequence 并保留现场。所有 744 h 根仍是
   `TEST_ONLY_TRUNCATED_HORIZON`；继续禁止 Crossover=3、并发第二求解、8760 h、付费云、
   basis gate 和 MGA。

## 2026-08-02 23:16 活动 Phase 1 更新

- 1 h 与 24 h 的 Base/V5 已全部 `rc=0`；当前唯一活动求解为 168 h Base，仍由 wrapper
  PID `1314144` 串行管理。
- 24 h 实证显示 Barrier 可能以 sub-optimal 结束，而 Crossover=2 可恢复严格 optimal；
  活动 Phase 1 不得切换 profile 或关闭 crossover。
- 继续只读检查当前年度 `solver_telemetry.jsonl`、`gurobi.log`、三份终态报告、overlap/
  counterflow 与资源。不得并发运行 A/B audit、Phase 2、basis、MGA 或第二求解。
- 168 h Base/V5 全部结束后，先验证 wrapper rc、四年 strict/QC/input/result manifests 与
  A/B audit；随后重新检查 available `>=96 GiB`、`si/so=0/0`、PSI=0 才可启动 Phase 2。

## 2026-08-02 22:55 活动 Phase 1 监控对象

- checkout/run identity：`b2206d9c899c8008d7b6dabdf15cc50dd286e8b7`。
- control root：`/data/zz2/National_model/run_control/phase1_b2206d9_v1`；wrapper PID
  `1314144`。
- output roots：
  `planning_sequence_2030_2060_{1,24,168}h_start3960_b2206d9_{base,v5}_v1`。
- PID 存在时只读 `phase1.stdout`、当前年度 logs/reports、RAM/swap/vmstat/PSI；不得更新
  server checkout、启动第二求解或 Phase 2。wrapper 任一非零返回即由 `set -e` 停止，
  不手工跳过。

## 2026-08-02 22:49 截断时域轻微对冲流推进覆盖条款

本节按作者决策覆盖下方 22:19 的“必须先做 network formulation change”要求；下方失败现场
和不得 resume/补 manifest 的规定继续有效。

1. 不引入 binary direction、MILP、逐小时方向锁、自由弃电或更高输电成本。LP 方程、损耗、
   碳/BECCS/DAC、solver 与 state contract 保持不变。
2. `TEST_ONLY_TRUNCATED_HORIZON` 每 168 h warning budgets 更新为：8 edge-hours、
   `0.25 GW` 最大 opposing flow、线路容量 `15%`、`1.25 GWh` opposing energy、
   `0.04 GWh` excess loss、毛输电占比 `5e-5`、系统负荷占比 `1e-7`。小时/绝对电量预算
   继续随诊断时长线性缩放；任一超限 hard fail。
3. 8760 h `SCIENTIFIC_PRODUCTION` 不应用 warning，仍要求 AC `1e-6 GW` 以上零对冲。
   warning 根必须保留 observed/limits，不能报告为 strict directionality。
4. 配置变更形成新 implementation identity，故旧 `fc2c500` 168 h 根不得 resume 或重标。
   部署后先完成 server regression/config/release audits，再以全新 roots 串行重做 matched
   1 h、24 h Base/V5 和四年 168 h Base/V5。只有全部 sequence accepted 才进入 Phase 2。
5. 每年仍单独检查 storage/V2G overlap、对冲流七项指标、solve/QC/input/result manifests、
   state、wrapper exit 与资源。继续禁止 8760 h、付费云、并发第二求解、basis reuse、MGA
   和 `Crossover=3`。

## 2026-08-02 22:19 Phase 1 网络方向性失败后的覆盖条款

本节覆盖下方 Phase 1 自动续接安排，直到新的 network-formulation milestone 完整闭合。

1. `/data/zz2/National_model/run_control/phase1_fc2c500_v1` 已退出；不得把它当作仍在运行的
   wrapper，也不得手工补写 `END`、`result_manifest.json` 或 planning state。
2. 1 h/24 h Base/V5 四条 sequence 已严格完成。168 h Base 只接受 2030、2040；2050
   虽为 solver `OPTIMAL`，但因 `unidirectional_interprovincial_flow=false` 而
   `solution_qc=HARD_FAIL`，2060 未运行。168 h V5 和 Phase 2 未启动。
3. 保留失败根
   `/data/zz2/National_model/outputs/planning_sequence_2030_2060_168h_start3960_fc2c500_base_v1/2050`。
   复核时必须同时读取 `transmission_flows.npz`、`transmission_capacity.csv`、
   `time_index.csv`、`hourly_marginal_prices.csv.gz` 和 `solution_qc.json`。当前证据固定为
   吉林—黑龙江 `CORRIDOR_0153` 在 7 个连续日 04:00 出现 `0.121496--0.177690 GW`
   opposing flow；这不是 `1e-6 GW` 级数值噪声。
4. 禁止通过增加 warning budgets、把 `HARD_FAIL` 改为 warning、后处理净流量、resume 或
   更换 Crossover 参数来绕过。下一步必须先审查 directional variables、shared AC capacity、
   losses、`flow_regularization_yuan_per_mwh` 与深度负价/最小出力之间的机制，形成最小模型
   修订及其目标/约束/价格口径说明。
5. 任一修订都视为 network formulation change：先运行相关 unit/regression tests，再以全新
   roots 串行重做 matched 1 h、24 h、168 h Base/V5。只有六条四年 sequence 全部满足 strict
   acceptance，方可另建新的 Phase 2 wrapper。继续禁止 8760 h、付费云、并发第二求解、
   basis reuse、MGA 和 `Crossover=3`。

## 2026-08-02 19:58 Phase 1 分级资源门禁

上节统一 `available>=96 GiB` 门禁按实测规模细化：Phase 1 的 1/24/168 h current-tip matched
roots 已证明 process-tree peak `<=3.651 GiB`，故 Phase 1 新 sequence 可在 available
`>=64 GiB`、最新 `vmstat si/so=0/0`、memory PSI 0 时启动。运行中若 available `<48 GiB`、
出现非零 swap I/O 或 memory PSI，则不启动下一 sequence/root。Phase 2 的 744 h 仍要求
available `>=96 GiB`，本条不授权降低。外部用户进程不得终止、nice 或修改。

## 2026-08-02 19:53 production solver freeze 与资源等待条款

当前 production profile 冻结为
`config/solver_profiles/barrier_16_crossover2_stable_basis_long_v1.json`：
`Method=2/Threads=16/Presolve=2/Crossover=2/CrossoverBasis=1/TimeLimit=86400/
SoftMemLimit=80`，其余严格 numerics 继承基线。它已完成 24 h Base/V5、168 h Base/V5 matched
门禁；Crossover=4 仅作已验证 fallback，不自动切换；direct dual simplex 仅作无 Crossover
strict fallback；Crossover=3 禁止。不得复用 `.bas`。

任何新 Phase 1/2 solve 前必须同时满足：无 CISPO/Gurobi PID、server checkout clean 且为双推送
tip、available RAM `>=96 GiB`、最新 `vmstat si/so=0/0`、memory PSI 0、磁盘充足、ParaCloud
队列核验完成。2026-08-02 19:53 available 约 93 GiB，原因是外部用户 wind-power workers；
不得触碰它们，资源未恢复前只监控。Phase 1/2 顺序和 strict acceptance contract 不变。

## 2026-08-02 18:35 V5 solver-route guard 更正

现行数据根是
`/data/zz2/National_model/data/model_ready_20260730_flex_v5_4f717de_v1`；0729 unified 根只用于
历史 744 h root 审计。24 h matched Base/V5 已证明 Gurobi 的 Crossover 1、2、4 在当前模型上
都能生成严格 accepted basic solution；168 h Base 又验证了 2/4。故 V5 长链的 basic route
允许集合从硬编码的 `{1}` 扩展为 `{1,2,4}`，并继续要求 `CrossoverBasis=1`。Crossover=3 仍因
既有 744 h 数值失稳证据永久拒绝，不得试跑。

168 h V5 在旧 guard 下产生的两个 `rc=1` 根只包含 prebuild 证据，不得 resume、补写 QC 或
结果 manifest。新 contract 通过回归并部署后，必须用新输出/控制根串行重跑 Crossover=2、4；
只有两根都满足完整 strict contract 才冻结 profile。其余 Phase 1/2 顺序与 2026-08-01 16:53
覆盖条款不变。

## 2026-08-01 16:53 参数重评后的 Phase 1/2 执行覆盖条款

本节取代下方 13:58 节中“Barrier-only 是当前主线、Crossover 不进入门禁”的安排；物理、
accounting、manifest、QC、资源与串行执行门禁均不放松。Phase 0 已在服务器提交
`5e7db6835db60170fad7a1a13283e2a4d16792f4` 上完成并通过。

1. 当前模型的 24 h Base 已对 20 个 Barrier-only 组合完成串行诊断。所有组合都未同时达到
   strict primal/dual acceptance，因此其 `BarPi` 即使存在也不得进入科学输出或 planning
   state。无 Crossover 并不等于没有影子价格：已验收的 dual simplex 根直接导出标准 `Pi`；
   但它在 24 h 上需 `795.206 s`，只作为严格可行 fallback，不直接宣称为最终性能优胜者。
2. 下一轮只比较 `Crossover=1/2/4 + CrossoverBasis=1`，每个候选先 24 h Base，再做 V5；
   优胜候选继续 168 h Base/V5。`Crossover=3` 由于既有数值失稳证据永久拒绝。候选间不复用
   `.bas`、不运行独立 basis gate，也不并发。
3. production profile 只有在 current-tip matched 24 h/168 h Base/V5 均满足
   `OPTIMAL + acceptance PASS + solution_qc PASS + all hard checks + current input manifest +
   valid result manifest + wrapper exit 0` 后才可冻结。任何 `TIME_LIMIT`、`SUBOPTIMAL`、
   missing manifest 或资源异常都 fail closed。
4. profile 冻结后，Phase 1 仍按 `start-hour=3960` 串行运行 1 h、24 h、168 h 四年
   Base sequence，再运行对应 V5 sequence。Phase 1 全闭合后，Phase 2 严格串行运行
   `744 h @ start-hour 0/3960/6552`，每个起点先 Base 四年 sequence，再 V5 四年 sequence。
   每个 744 h 根仍标记 `TEST_ONLY_TRUNCATED_HORIZON`，不得作为年度科学结果或正式
   2040 state anchor。
5. 仍禁止 8760 h、付费云、并发第二求解、MGA 和 `Crossover=3`。每个 solve 前后继续审计
   PID、RAM/swap/vmstat/memory PSI、磁盘、wrapper stderr/time、solve/QC/result manifests
   及 ParaCloud `squeue`；失败即保留现场并停止该 sequence。

## 2026-08-01 14:18 0729 历史 744 h 根的只读复核边界

统一候选根 `2030_744h_v0729_unified_v4_v1g_cold_v1` 已再次确认严格终态为
`OPTIMAL + QC PASS + 52/52 + valid result manifest + wrapper exit 0`。PID 已退出，
当前固定服务器 clean/idle；不得继续监控为活动任务，也不得由该根自动启动任何后续
solve。它仍是 `TEST_ONLY_TRUNCATED_HORIZON`，不进入 2040 state。

历史输入复核必须区分两层：

1. 当前 checkout 上直接运行 `validate_input_manifest()` 会因 3 个 repo 配置文件已随
   后续提交改变而返回 size drift；不得伪报 `(True, [])`。
2. 必须用 `result_manifest.json`、`run_identity.json.git_commit=7c56622` 和
   `git show 7c56622:<path>` 复核 immutable run identity。本次 3 个 Git blob 与
   manifest 的 size/SHA256 完全一致，其余 75 个输入仍在原路径通过，故历史根没有
   损坏。未来 historical-root auditor 应显式实现这种 commit-aware 配置复核，不能要求
   固定服务器永远停留在旧 checkout。

本次没有 fast-forward、部署、resume 或启动新求解。后续动作仍从下节 Phase 0 开始；
禁止 8760 h、付费云、basis/MGA、inline Crossover、并发第二求解和 `Crossover=3`。

## 2026-08-01 13:58 Barrier-primary 跨年主线与人工后置 Crossover

对应实现提交为 `53a5873156bfe4e81abfaa258d02b3f3ff664bbd`。本节取代下方
12:20 节中“nonbasic primary 不写 planning state”“先做单年五季节、暂不做四年
sequence”的执行安排；12:20 节的 kill-condition、内存阶梯和 recovery 风险仍有效。

### 主线验收与跨年状态

1. 每个 case/year 的首要产物是 Gurobi 13
   `Method=2/Crossover=0/SolutionTarget=1` 的最优内点解。只有同时满足
   `OPTIMAL + OPTIMAL_PRIMAL_DUAL_NONBASIC/PASS + solution_qc=PASS + 全部 hard
   checks + current input manifest + accepted BarX/BarPi checkpoint + valid result
   manifest + wrapper exit 0` 才能成为 sequence predecessor。不得凭 Barrier 日志中
   的 objective、`BarStatus` 或 recovery-only checkpoint 续接。
2. `run_cispo_planning_sequence.py` 对 nonbasic profile 自动、显式传入
   `--export-barrier-checkpoint --allow-nonbasic-planning-state`。接受后以该解的容量
   决策形成下一年的 additive cohort state；`state_metadata.json` 必须记录
   `ACCEPTED_OPTIMAL_NONBASIC_BARRIER_CAPACITY_STATE`、source contract、checkpoint
   manifest SHA256、cohort zero tolerance 和微小容量截断统计。state load/resume
   重新验证 source solve/QC/input/result manifests、identity layers 和两条 `.npy`
   向量完整性。
3. 内点容量状态是可行且最优的规划决策，但在线性规划多重最优空间中可能比 extreme
   point 更弥散。此处把它作为明确的 sequential cohort policy，而不是宣称容量分布
   唯一。Base 与 V5 必须各自形成独立的 2030→2060 state chain，不能让 V5 读取
   Base predecessor，也不能跨窗口混用 state。
4. 截断时域 sequence 的 state 只允许 `TEST_ONLY_TRUNCATED_HORIZON` 链内部测试；
   不能进入未来正式 8760 h production chain，也不能被论文解释为年度容量路径。

### Crossover 的人工边界

- Crossover 不是任何年度、case 或 sequence 的必需验收项。容量、逐小时调度、成本、
  碳/CCS、可靠性和 `BarPi` shadow prices 均从 accepted Barrier 解直接导出。
- 只有 `VBasis/CBasis`、`.bas`、`SAObjLow/Up`、`SARHSLow/Up` 等
  basis-dependent sensitivity 需要 basic solution。连续 LP 的 RC 可从 nonbasic
  解读取，但 RC 与 `BarPi` 在退化问题中可能不唯一。MGA 数学上不要求所有年份先
  Crossover；basis 只可能帮助选定年份的 re-optimization，是否值得使用须单独验证。
- 所有主线完成后，作者才能选择少数 source roots，使用
  `barrier_16_deferred_crossover_v1.json --primal-dual-checkpoint-in SOURCE
  --allow-primal-dual-crossover` 在全新 target root 重建 exact LP。必须提供 source
  当年原来使用的 predecessor `--state-in`（若非 2030），使 input manifest 和 LP
  identity 完全一致。派生输出不写 planning state、不改写原 sequence；失败不影响
  accepted source。
- 当前下一轮实验**不自动运行任何 Crossover**。完成后只建立 accepted checkpoint
  inventory，交由作者按论文问题选择年份。

### 下一窗口严格串行执行顺序

#### Phase 0：身份、部署和环境门禁

1. 完整阅读五份合同，实时核验 local/origin/GitHub branch/HEAD、服务器 checkout/
   dirty、唯一 CISPO/Gurobi 进程、Gurobi major version、数据根和 release SHA、RAM/
   swap/vmstat/memory PSI、磁盘、目标根及 ParaCloud `squeue`。PID 存在即只监控。
2. 仅在服务器 clean/idle 时 fast-forward 到包含 `53a5873` 的精确文档 tip；随后运行
   server full regression、readiness、release contract、Base/V5 input manifest、
   hydropower 380 GW closure 和 1 h build audit。任一失败即停止，不启动 solver。
3. 所有任务继续由 `/usr/bin/time -v`、独立 output/control/stdout/stderr/PID 包装，
   一次只允许一个 Python/Gurobi solve；历史根永不覆盖。

#### Phase 1：summer 小规模四年 sequence 门禁

依次运行 `1 h → 24 h → 168 h`，每个长度先完整 Base sequence，再完整 V5 sequence；
起点统一为 `3960`。只有前一根 `sequence_report.json=PASS` 且四个年份分别满足全部
终态合同时，才进入下一根。

```bash
python scripts/run_cispo_planning_sequence.py \
  --start-year 2030 --end-year 2060 \
  --diagnostic-start-hour 3960 \
  --diagnostic-hours HOURS \
  --scenario-config SCENARIO_JSON \
  --solver-config config/solver_profiles/barrier_16_nonbasic_primal_dual_v1.json \
  --output-root SEQUENCE_ROOT
```

`SCENARIO_JSON` 只取 `config/scenarios/base.json` 或
`config/scenarios/flex_integrated_v5_central.json`。建议根名：
`planning_sequence_2030_2060_{1,24,168}h_start3960_53a5873_{base,v5}_v1`。

#### Phase 2：三季节 Base/V5 四年 744 h sequence

Phase 1 全部闭合后，严格串行运行：

1. Jan：`start-hour=0`，Base→V5；
2. Jun-15：`start-hour=3960`，Base→V5；
3. Oct：`start-hour=6552`，Base→V5。

命令沿用上面模板，把 `HOURS=744`；建议根名：
`planning_sequence_2030_2060_744h_{jan0,jun15_3960,oct6552}_53a5873_{base,v5}_v1`。
这是 6 条独立 sequence、24 个逐年 solve，绝不并发。任一年度失败时 sequence 必须
停在该年并保留现场；只有 exact identity 且已有年份全部 accepted 才可 `--resume`。
每个年度审计容量/发电、冷热、V1G/V2G、wave、水电、PHS/储能、网络、备用、惯量、
碳/CCS/BECCS、成本、state transition、checkpoint 和微小 cohort census。三季节
根始终为 `TEST_ONLY_TRUNCATED_HORIZON`。

#### Phase 3：固定服务器最大安全时段阶梯

三季节 744 h 全部通过后，先只做单年 2030 Base cold ladder：

1. `1008 h @ start 3960`；
2. `1488 h @ start 3624`；
3. `2160 h @ start 2880`；
4. `2976 h @ start 2160`；
5. `4344 h @ start 2160`。

使用 `barrier_16_nonbasic_primal_dual_long_v1.json` 和
`scripts/run_cispo_2030_full_year.py`；每一级都导出 checkpoint（`>744 h` 自动），但
不导出 diagnostic state。每级记录 build/Barrier/export walltime、raw/presolved LP、
Barrier iterations、solver/process-tree peak memory、swap/PSI、checkpoint bytes、输出
总大小和完整 QC。只有一级严格接受且资源恢复正常才进下一级。

最大安全 Base 时段确定后，运行同窗口单年 V5。Base/V5 均通过且满足 solver peak
`<=72 GiB`、process-tree peak `<=88 GiB`、新任务前 host available `>=96 GiB`、
持续 `si/so=0/0`、memory PSI 0、磁盘余量充分，才允许作者决定是否在该最大时段
追加一对四年 Base→V5 sequences。不得由自动化自行作此决定。

`>4344 h`、5088 h 和 8760 h 均不在本轮授权内。不得启动付费云、MGA、basis gate、
inline Crossover、`Crossover=3` 或并发第二求解。所有实质里程碑都更新
`CODEX_HANDOFF.md`、`MODEL_SERVER_STATUS.md`、`SERVER_RUNBOOK.md`，选择性提交并
双推送；用户拥有的 supplementary、`.codex_tmp` 和历史 outputs 继续保护。

## 2026-08-01 Barrier-first 验收、检查点与下一轮压力测试合同

对应实现提交为 `19b5754bb0db12818975344e5365777674698c47`；在部署前必须确认
local、origin、GitHub 已包含该提交及随后交接提交，固定服务器不得在活动 PID 上
切换 checkout。

本节取代“所有成功运行都必须先完成 inline Crossover”这一过严工作流，但**不放松**
任何科学或物理门禁。超过 744 h 的默认第一阶段必须使用
`barrier_16_nonbasic_primal_dual_long_v1.json`；744 h 季节窗口使用
`barrier_16_nonbasic_primal_dual_v1.json --export-barrier-checkpoint`。第一阶段只在
`OPTIMAL + OPTIMAL_PRIMAL_DUAL_NONBASIC/PASS + solution_qc=PASS + 全部 hard
checks + current input manifest + valid result manifest + wrapper exit 0` 时接受。
`BarPi` 是此阶段的 dual；不要求 basis、RC 或 SA attributes。所有截断根仍是
`TEST_ONLY_TRUNCATED_HORIZON`。

通过后，输出根中的 `barrier_checkpoint/` 保存 `primal_barx.npy`、
`dual_barpi.npy` 和 `barrier_checkpoint_manifest.json`。manifest 锁定 baseline/
analysis identity、implementation bundle、data roots、input manifest、规划年、窗口、
Gurobi Fingerprint、原 LP 尺寸和文件 SHA256。非基第一阶段不自动导出
`planning_state`，避免退化容量空间中的弥散内点未经审查地成为下一规划年 anchor。
若需要 basis、SA sensitivity 或 MGA warm-start 工程，必须用
全新输出根、完全相同 LP 和
`barrier_16_deferred_crossover_v1.json --primal-dual-checkpoint-in SOURCE
--allow-primal-dual-crossover` 单独执行；该 profile 以 `PStart/DStart +
LPWarmStart=2 + Crossover=1/CrossoverBasis=1` 重建 presolved start。派生 Crossover
失败不得删除、覆盖或降级第一阶段结果。

旧式 `Crossover>0` 在 `>744 h` 默认被 runner 拒绝；诊断时必须显式传入
`--allow-inline-crossover`。若 Gurobi 13 已有 `BarStatus=OPTIMAL` 而 inline
Crossover 后 `TIME_LIMIT/MEM_LIMIT`，runner 会尽力保存
`RECOVERY_ONLY_UNACCEPTED_SOLVER_RESULT` 原始向量。该 recovery 根没有完整 QC，
不得用于科学解释或直接进入正式 deferred crossover。

### 会直接损失结果的条件审计

1. 原 `--diagnostic-hours` 无论多长都按 8 GiB 放行，现已修为向上匹配内存层级：
   `<=744 h: 8 GiB`、`745--4344 h: 32 GiB`、`4345--8760 h: 96 GiB`。
   这是防 OOM 的收紧，禁止回退。
2. Gurobi `TimeLimit` 和 `SoftMemLimit` 通常会让 `optimize()` 返回，因而可以执行
   报告/检查点导出；长 profile 将 solver 时间从 6 h 提至 24 h、soft memory 从
   48 GiB 提至 80 GiB，但仍须保留至少 16 GiB host available、`si/so=0` 和
   memory PSI=0。不得用更大 soft limit 越过 host memory gate。
3. `SIGINT/SIGTERM` 已由 telemetry/graceful termination 捕获；`SIGKILL`、Linux
   OOM killer、Slurm cgroup OOM 和节点重启不可被 Python 捕获。付费云脚本在未来
   重新批准前必须保证 scheduler walltime 大于 Gurobi TimeLimit 加 build/export
   headroom，并配置 TERM grace period；旧 24 h scheduler + 24 h solver 组合不得复用。
4. 检查点不保存 Barrier factorization，不能从某次 Barrier iteration 继续；它只允许
   exact-LP deferred crossover。8760 h 的两条 float64 向量原始规模约 0.9 GB，
   但导入时 Python/Gurobi 对象列表会产生额外瞬时内存，必须计入资源余量。
5. 不放松 `Status=OPTIMAL`、primal/dual quality、58/58（或当前版本实际 hard-check
   总数）、物理/成本 QC、input/result manifest 与 wrapper stderr/time。Barrier 日志中的
   `Optimal objective`、recovery checkpoint 或单独 `BarStatus=OPTIMAL` 均不是验收。

### 下一窗口实验顺序

1. 先实时核验 local/origin/GitHub、服务器 checkout/dirty、唯一进程、Gurobi 13、
   数据根、RAM/swap/vmstat/PSI、磁盘和 ParaCloud；部署精确新提交并完成全回归、
   readiness、release、Base/V5 input 与 hydro audits。不得在活动 PID 上部署。
2. 以 2030 单年、cold/no-basis、严格串行方式运行五个 744 h 窗口的 Base→V5
   配对：`start-hour=0`（Jan）、`2160`（Apr）、`3960`（已知 Jun-15 blocker）、
   `4344`（Jul）、`6552`（Oct）。每个 Base 只有严格接受后才启动同窗 V5；任一失败
   保留现场并停止该窗口，不能自动补跑、改 profile 或转 inline Crossover。

   744 h runner 模板（wrapper 仍须按既有 `/usr/bin/time -v`、独立 control root、
   stdout/stderr/PID 合同封装）：

   ```bash
   python scripts/run_cispo_2030_full_year.py \
     --planning-year 2030 \
     --diagnostic-start-hour START \
     --diagnostic-hours 744 \
     --scenario-config SCENARIO_JSON \
     --solver-config config/solver_profiles/barrier_16_nonbasic_primal_dual_v1.json \
     --export-barrier-checkpoint \
     --output-dir OUTPUT_ROOT
   ```

   `SCENARIO_JSON` 只取 `config/scenarios/base.json` 或
   `config/scenarios/flex_integrated_v5_central.json`；禁止传入 state/basis/MGA。
   建议根名为
   `2030_744h_v0801_barrierfirst_19b5754_{jan,apr,jun15,jul,oct}_{base,v5}_v1`。
3. 五组闭合后才做 Base-only 长度阶梯：`1008 h@3960`、`1488 h@3624`、
   `2160 h@2880`、`2976 h@2160`、`4344 h@2160`，使用 long profile。每一级
   必须完成严格终态审计与资源趋势复核后才进入下一级。最大 Base 接受长度确定后，
   只运行一个同长度 V5 配对；若 V5 资源预测不安全，则退回最近较短已接受长度。

   长度阶梯把上面模板的 hours/start/profile 改为该级参数与
   `barrier_16_nonbasic_primal_dual_long_v1.json`；`>744 h` checkpoint 自动导出，
   不需要 `--export-barrier-checkpoint`。输出名使用
   `2030_{hours}h_v0801_barrierfirst_19b5754_{base,v5}_v1`，每一级开始前再次确认
   output/control 根不存在。
4. `>4344 h` 不自动启动。只有 4344 h 严格接受、solver peak <=72 GiB、process-tree
   peak <=88 GiB、host available >=96 GiB、无 swap-in/out/PSI、剩余磁盘充足，且
   作者再次审查后，才可提出下一候选（先 5088 h，仍不得直接 8760 h）。largest
   accepted horizon 只是该服务器工程上限证据，不是年度科学结果。
5. 本轮不运行四年 planning sequence、固定服务器 8760 h、付费云、MGA、basis
   gate、`Crossover=3` 或并发第二求解。若以后需要 2030→2060 state chain，先用
   accepted checkpoint 的独立 Crossover 闭合容量 anchor，再另行批准。

## 2026-08-01 reservoir-native Base 744 h 失败后的恢复边界

Base 根
`/data/zz2/National_model/outputs/2030_744h_v0731_reservoir_native_ub_7a1520e_base_stablebasis_v1`
已以 `TIME_LIMIT + SolCount=0 + wrapper exit 2` 终止。Barrier 在 218 iterations、
`6,900.02 s` 报告 interior optimal，但 `Crossover=1/CrossoverBasis=1` 的
cleanup 经 basis variable drop、quad precision 与 746,438 simplex iterations 后，
在总 solver `21,601.01 s` 超时。无 `solution_qc.json`、58 项 solution hard
checks、`result_manifest.json` 或解后物理/成本输出。current input manifest 有效。

当前执行边界固定为：

1. 原样保留上述 output/control 根；禁止 resume、删除、补写 QC/manifest、从
   Barrier interior point 手工导出结果或把日志中的 `Optimal objective` 重标为
   可接受解。
2. 候选 V5 根 `2030_744h_v0731_reservoir_native_ub_7a1520e_v5_stablebasis_v1`
   未创建且不得启动。Base 已复现 shared-core crossover blocker，因此先诊断
   basic-solution 数值路径，不把问题归因于 V5，也不把 V5 视为已验证。
3. 后续修改必须以 `7a1520e` 为可追溯起点，明确区分数学等价 bound tightening、
   solver profile 和科学约束变更。不得仅增加 TimeLimit、放松 primal/dual/QC、
   启用 `Crossover=3` 或删除物理约束来绕过失败。
4. 任一新候选先运行完整 regression/readiness/release/input/hydro audits，再在
   全新根串行通过同窗 1 h、24 h、168 h Base/V5；每根仍要求
   `OPTIMAL + solution_qc=PASS + 58/58 + current input + valid result manifest +
   wrapper exit 0/stderr 0`。短门禁只能证明工程可运行，不能代替 744 h 证据。
5. 只有作者审查新方案且上述成对门禁全部闭合后，才可重新申请 Base 744 h；
   Base 接受后才允许 V5 744 h，绝不并发。所有截断根继续标记
   `TEST_ONLY_TRUNCATED_HORIZON`。

仍禁止固定服务器 8760 h、付费云、basis/MGA、并发第二求解和
`Crossover=3`。当前服务器 clean/idle、资源正常、ParaCloud 空队列，不构成
自动启动任何新任务的授权。

## 2026-07-31 20:41+08:00 strict nonbasic 部署与同窗 Base/V5 门禁

旧 summer V5 744 h 已以 `TIME_LIMIT + SolCount=0` 结束；不得 resume、补写
QC/manifest 或重标。实现提交 `8de7a8e` 增加 Gurobi 13+ 专用的
`barrier_16_nonbasic_primal_dual_v1.json`。它不要求 basic solution，但必须
同时满足 `OPTIMAL`、strict primal/dual quality、58/58 hard checks、current
input、valid result manifest、`BarPi` dual available、wrapper exit 0/stderr 0。
它禁止 basis import/export、scientific `.bas` 与 MGA。

执行顺序必须为：

1. 确认 local/origin/GitHub 为同一文档 tip；固定服务器 checkout clean、无
   CISPO/Gurobi/National_model 进程，RAM/swap/vmstat/PSI 正常，ParaCloud
   `squeue -u a8s001819` 为空。任一不满足即停止。
2. fast-forward 固定服务器到精确 tip，设置当前
   `CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260730_flex_v5_4f717de_v1`
   及匹配 CF/hydro/raw-GRFR/wave roots；核验 Gurobi major version 为 13，运行
   完整 regression、readiness、release、V5 input 与 hydro audits。
3. 使用全新根依次运行 summer start hour 3960 的 1 h Base、1 h V5、24 h
   Base、24 h V5；profile 均为
   `config/solver_profiles/barrier_16_nonbasic_primal_dual_v1.json`。建议根名：
   `2030_{1h,24h}_v0731_summer_nonbasic_8de7a8e_{base,v5}_v1`。一次只允许
   一个 wrapper/Python/Gurobi 链。
4. 每根必须检查 solver contract、`solve_report.json`、`solution_qc.json`、
   58/58 hard checks、dual export、current input/valid result manifests、
   dashboard、load-center opposing-flow 最大值/总量、冷热/EV/wave/水电/储能/
   网络/备用/惯量/碳/CCS/成本，以及 wrapper stderr/time。任一失败即淘汰
   nonbasic 候选，不运行后续长门禁。
5. 四个小门禁全部闭合后，先串行运行同窗 168 h Base/V5。二者闭合后才可
   依次运行 `[3960,4704)` 的 Base 744 h 与 V5 744 h；Base 是用户要求的同月
   求解难度/容量对照，绝不与 V5 并发。744 h 均为
   `TEST_ONLY_TRUNCATED_HORIZON`，不导出 basis，不自动续接 2040。

仍禁止固定服务器 8760 h、付费云、并发第二求解、basis/MGA 和
`Crossover=3`。若 nonbasic 被淘汰，保留全部失败根，回到已验证 basic profile
做针对性结构诊断，不得放松 primal/dual 或物理 QC。

## 2026-07-31 16:49+08:00 活动运行 Crossover 监控点（已由上节终态取代）

Barrier 已在 233 iterations、`7,414.52 s` 报告 optimal；当前不是 Barrier，
而是 `Crossover=1/CrossoverBasis=1` 后的 simplex cleanup。16:48 监控点为
iteration `912,630`、runtime `11,752.76 s`、primal infeasibility 0、dual
infeasibility `2.014e6`。dual 指标近期大幅振荡，但尚无 `Numerical trouble`
或终态。

继续执行只读规则：

1. 不把 Barrier 的 `Optimal objective` 当成最终 `OPTIMAL`；
2. 不因中间 dual oscillation 中断或更改参数，除非进程形成正式终态；
3. 每次检查剩余 `21,600 s` time limit、iteration/objective、primal/dual
   infeasibility、solver/host memory、swap、PSI 和 stderr；
4. PID 退出后才读取并联合验收 solve/QC/result manifest 与 wrapper time；
5. server checkout 固定在 `aaf16cc`，本地后续文档提交不得在运行中部署。

## 2026-07-31 13:29+08:00 summer 744 h 活动运行监控点

活动根为 `2030_744h_v0731_summer_offset_a7c6715_v5_v1`，server checkout
固定在 `aaf16cc49a5a3d5bb07d214a957a3a4065ac3f07`。初始 wrapper/Python
PID 为 `674143/674145`，`run_scope.json` 已确认 `[3960,4704)` 与正确北京
时戳。PID 存在时执行以下只读合同：

1. 每次重新核验 local/origin/GitHub HEAD，并确认 server 仍为 clean 启动提交；
2. 核对唯一 wrapper/Python/Gurobi 链、`solver_telemetry.jsonl`、
   `gurobi.log`、RAM/swap/两个 `vmstat` 样本/memory PSI；
3. 核对 `solve_report.json`、`solution_qc.json`、`result_manifest.json`
   是否出现，但不得在 PID 存在时据中间文件宣告接受；
4. 核对 ParaCloud `squeue -u a8s001819` 仍为空；
5. 不切换 checkout，不启动 8760 h、第二求解、付费云、basis/MGA 或
   `Crossover=3`。

PID 退出后按下一节的完整终态合同审计。若 build 阶段退出，保留根并精确诊断；
若进入 solver，则同时判定 Barrier/Crossover、数值稳定性与最终 artifacts。

## 2026-07-31 13:27+08:00 summer 744 h 唯一启动候选

前置小门禁已经严格闭合：summer 1 h Base v2 与 24 h V5 v2 均为
`OPTIMAL + PASS + 58/58 + current input + valid result manifest +
wrapper exit 0/stderr 0`，且时间索引从 model hour 3960 开始。长门禁只能使用：

```text
output:
/data/zz2/National_model/outputs/2030_744h_v0731_summer_offset_a7c6715_v5_v1

control:
/data/zz2/National_model/run_control/2030_744h_v0731_summer_offset_a7c6715_v5_v1

arguments:
--planning-year 2030
--diagnostic-start-hour 3960
--diagnostic-hours 744
--scenario-config config/scenarios/flex_integrated_v5_central.json
--solver-config config/solver_profiles/barrier_16_auto_order_stable_basis_v3.json
```

启动前重新核验 local/origin/GitHub/server HEAD、server clean/idle、
RAM/swap/`vmstat`/memory PSI、两个目标根不存在和 ParaCloud 空队列。
必须设置当前 V5 data/CF/hydro/raw-GRFR/wave roots；不得传入
`--basis-in`。只允许一个 wrapper/Python/Gurobi 链。启动后立即核对
`run_scope.json` 的 `[3960,4704)` 与北京时戳；PID 存在时只读监控，不切换
checkout、不启动任何新任务。PID 退出后必须验收 solve/QC/58 hard checks、
current input/valid result manifests、wrapper stderr/time、dashboard 和全部
物理/accounting scope。该根始终标记 `TEST_ONLY_TRUNCATED_HORIZON`。

## 2026-07-31 13:18+08:00 summer 1 h 空 winter bug 恢复点

失败根 `2030_1h_v0731_summer_offset_985983b_base_v1` 必须原样保留且不得
resume。它在 build 阶段退出，未调用 `optimize()`。恢复身份必须为
`a7c67153d9b90055b60ed2704ef6bba702086ae4` 或包含它的精确文档 tip。
部署后先完整回归，再用新根
`2030_1h_v0731_summer_offset_a7c6715_base_v2` 重跑同一 hour 3960。
若 v2 未严格接受，停止，不运行 24 h/744 h。

## 2026-07-31 13:10+08:00 非年初 summer-offset 门禁执行合同

实现身份为 `077bce0eca16b1025130143122aee0a05559c3e0`。夏季窗口只能
使用显式参数：

```text
--diagnostic-start-hour 3960 --diagnostic-hours 744
```

这对应 2030-06-15 00:00 至 2030-07-15 23:00。不得用
`--horizon one_month` 冒充该窗口，因为后者仍从 hour 0 开始。执行顺序：

1. 实时核验四端 HEAD、server checkout clean、无 CISPO/Gurobi、资源正常、
   新输出/控制根不存在、ParaCloud 队列为空；任一不满足即停止。
2. fast-forward 到同时存在于 origin/GitHub 的精确文档 tip，并设置当前
   V5 data/CF/hydro/wave roots。运行完整 regression、readiness、release、
   V5 input 与 hydro audits。
3. 串行运行 summer hour 3960 的 1 h Base cold gate；严格接受后运行
   同起点 24 h V5 cold gate。每根必须满足
   `OPTIMAL + solution_qc=PASS + 58/58 + current input + valid result
   manifest + wrapper exit 0/stderr 0`，并核对 `time_index.csv` 的
   `model_hour_index`、北京时间、冷热/EV/wave/水电/储能/网络/安全/碳与成本。
4. 两个小门禁全部接受后，启动唯一 2030/V5 744 h cold gate，solver 为
   `barrier_16_auto_order_stable_basis_v3.json`，无 `--basis-in`、无并发。
   监控 Barrier/Crossover、telemetry、RAM/swap/vmstat/PSI；PID 存在时只读。
5. PID 退出后按完整终态合同审计 solve/QC/58 hard checks/manifests/wrapper、
   dashboard 与全部物理 accounting scope。744 h 始终标为
   `TEST_ONLY_TRUNCATED_HORIZON`。不自动继续四年、8760 h、付费云、
   basis/MGA 或 `Crossover=3`。

## 2026-07-31 12:45+08:00 `ae33563` 匹配门禁后的执行边界

当前严格验证身份为
`ae3356391ec55376b041d6a356ea2d1f26be88bc`，数据根为
`/data/zz2/National_model/data/model_ready_20260730_flex_v5_4f717de_v1`。
服务器 `165/165` regression、readiness、release、V5 input、hydro
audits 均 PASS。当前可复用的严格根为：

```text
/data/zz2/National_model/outputs/2030_24h_v0731_ae33563_base_v2prod_v1
/data/zz2/National_model/outputs/2030_24h_v0731_ae33563_v5_v2prod_v1
/data/zz2/National_model/outputs/2030_168h_v0731_ae33563_base_v2prod_v1
/data/zz2/National_model/outputs/2030_168h_v0731_ae33563_base_v3stable_v1
/data/zz2/National_model/outputs/2030_168h_v0731_ae33563_v5_v3stable_v1
```

五根均满足 `OPTIMAL + solution_qc=PASS + 58/58 + current input +
valid result manifest + wrapper exit 0/stderr 0`。V5 的长链结构在
`diagnostic-hours >= 168` 时仍必须使用 `Crossover=1` 且
`CrossoverBasis=1`；不要用 `barrier_16_auto_order_v2` 绕过 guard。
对应的预优化拒绝根
`/data/zz2/National_model/run_control/2030_168h_v0731_ae33563_v5_v2prod_v1`
只保留为合同证据，不得补写 solve/QC/manifest。

后续执行固定规则：

1. 每次先实时核验四端 Git、服务器 clean/idle、RAM/swap/`vmstat`/PSI、
   目标根不存在和 ParaCloud 队列；严格串行，不复用失败根。
2. Base 可以用 `barrier_16_auto_order_v2` 或匹配诊断用
   `barrier_16_auto_order_stable_basis_v3`；长时段 V5 只能用后者，直到
   新证据和代码合同共同完成 production 晋级。两者都保持
   `Crossover=1`，禁止 `Crossover=3`。
3. 每根必须验收 solve/QC、当前 input/result manifests、wrapper
   stderr/time/RSS/swap、dashboard，以及冷热、EV fleet SOC、firm credit、
   wave、水电/梯级、PHS/储能、网络、备用、惯量、碳/CCS/BECCS和成本。
4. 截断时域 adequacy 的 firm credit 来自完整 8760 h immutable baseline
   peak windows；selected-horizon effective peak 只用于诊断。冬季 168 h
   可出现“实际 cooling shift 为零但全年峰窗 cooling credit 非零”，禁止
   把它表述为已验证的年度价值。
5. V5 的 `ev_v2g_charge_gwh` 是旧兼容字段，在单一物理 fleet SOC 下为零；
   能量审计读取 `ev_mobility_charge_gwh`、`ev_mobility_discharge_gwh`、
   SOC transition、departure、功率上限和 periodic boundary，不能把兼容
   字段误判为凭空放电。
6. 水电工程门禁要求 380 GW、aggregate monthly budget 与 cascade
   reconciliation 全部通过；同时单独登记 raw negative-local-inflow clip
   与 routed adjustment。它们非零时，工程 PASS 不等于水文敏感性已闭合。
7. 当前可选下一步是全新四年 168 h Base/V5 sequence，或经作者明确批准的
   一个更长门禁。全部截断根仍是 `TEST_ONLY_TRUNCATED_HORIZON`。本节不
   授权自动启动 744/1008/8760 h、付费云、basis/MGA、并发第二求解或
   `Crossover=3`。

## 2026-07-31 10:15+08:00 每轮固定结果数据与图表合同

实现身份为 `336116b493cf92eb461d1a2aab490678fd2dbac5`，解释修正为
`bdb57b2cb4e3f4781cfd53c087c7cc1a780d73a5`。正常 runner 在最终
`solve_report.json` 和 `solution_qc.json` 形成后、output catalog 与
result manifest 定稿前，自动生成：

```text
result_dashboard_summary.json
result_analysis_metrics.csv
visualizations/core_result_dashboard.svg
```

这三项必须同时出现在 `output_catalog.csv` 和
`result_manifest.json`；缺失、成本重构失败或 hash 失配均不得接受运行。
SVG 是服务器无 Matplotlib/Pillow 环境下的保证产物。需要 PNG/PDF 时必须
在历史结果根之外执行：

```text
python scripts/build_result_dashboard.py \
  --result-dir <accepted_result_root> \
  --output-dir <external_analysis_dir> \
  --formats svg,png,pdf
```

固定查阅顺序：

1. 先看标题行的 solver status、QC status、hard-check count 与
   `result_use`；图片不能替代 input/result manifest 和 wrapper 审计。
2. 查看 installed capacity、selected-horizon generation、灵活性/系统
   margins、碳限额和 curtailment；随后在 tidy CSV/JSON 中读取精确值。
3. 成本统一以不可变 baseline demand 为分母。`1 million CNY/GWh =
   1 CNY/kWh`。截断时域分别报告 annualized-planning intensity 和
   selected-horizon operating intensity，禁止相加，full-year total
   必须为 N/A/null，也不得标为 LCOE。
4. 只有 accepted 8760 h scientific run 才允许把年化规划成本与全年运行
   成本相加并输出 total system cost intensity。仍需披露该指标的系统边界，
   不能自动等同于发电技术 LCOE。
5. firm flexibility credit 来自各省完整 8760 h immutable baseline peak
   windows、服务包络和 derating；截断时域全国
   `baseline -> effective peak` 是另一个指标，二者不得直接比较。

最终服务器验证根为
`/data/zz2/National_model/outputs/2030_1h_v0731_dashboard_v5_bdb57b2_server_v1`，
控制根为
`/data/zz2/National_model/run_control/2030_1h_v0731_dashboard_v5_bdb57b2_server_v1`。
它达到 `OPTIMAL + PASS + 58/58 + current input + valid result manifest`，
wrapper `exit=0/stderr=0/wall=0:39.10/MaxRSS=597624 KiB/swaps=0`。三项
dashboard 产物均被最终 manifest 覆盖；成本 objective 重构残差
`-9.779e-9 million CNY`。本根仅为 `TEST_ONLY_TRUNCATED_HORIZON`。

模型边界必须明确：本 dashboard 提交不增删任何 LP 变量、约束、目标或
solver 参数；冷热与 EV 灵活性模式未变。前一数值稳定化的零控制状态/冗余
行列删除是代数等价变换，而
`charge + discharge <= connected * K_v1g` 是唯一新增的共享接入物理
约束，用于阻止 V1G/V2G 重复占用签约连接，不能误写成纯性能改动。

当前固定服务器空闲、资源安全，ParaCloud 队列为空。下一次经作者选择的
24 h、168 h 或更长门禁直接使用这一合同并逐根验收；不自动启动
744/1008/8760 h、付费云、basis/MGA、并发第二求解或 `Crossover=3`。

## 2026-07-31 05:14+08:00 V5 168 h 门禁闭合后的下一阶段

实现 `fead34334153eca32bbf7ec3651f3388038ac04b` 已在 clean
`22e19c154148fcfcb137d5a7e882ff69abd2b7c8` 服务器完成全部短门禁。
Base/V5 1 h、24 h 及唯一 V5 168 h 均严格闭合；168 h 是
`OPTIMAL + PASS + 58/58 + current input + valid result manifest`，
solver 1005.194 s、Barrier/Crossover `819.54/176.79 s`、RSS
3.511 GiB、swaps 0。`CrossoverBasis=1` 成功把 Barrier 的
`Sub-optimal` 状态恢复为 `Optimal`，但 `Kappa≈1.62e10`，不得直接升格
为全年 production profile。

下一阶段固定顺序：

1. 重新核验本地/origin/GitHub/server HEAD、服务器 clean/idle、
   RAM/swap/`vmstat`/PSI、目标根不存在和 ParaCloud 空队列。
2. 只运行一个全新 2030 Base 168 h cold root，使用相同数据和
   `barrier_16_auto_order_stable_basis_v3.json`，无 basis。要求
   `OPTIMAL + PASS + 58/58 + current input + valid result manifest +
   wrapper exit 0`，并记录 raw/presolved/factor、Barrier/crossover、
   Kappa、violations、RSS 与 swap。
3. 并行求解仍禁止；共享 numerical debt 只允许先做 build/presolve
   数值审计。重点为 `load_center_ror_availability`、ROR/VRE
   availability 和年度会计。不得未经等价证明提高 CF 零阈值、删掉
   availability variables、启用 `BarHomogeneous` 或强制
   `Aggregate=0`。
4. 修正 V5 QC 输出语义：旧式
   `maximum_ev_v1g_daily_energy_residual_gwh` 对带 SOC、效率和驾驶取能
   的车群模型应显式标为不适用，并以 SOC transition/periodic/service
   accounting 作为 hard evidence。不得因此放松任何现有 EV 物理约束。
5. Base 168 h 与上述审计闭合后，形成 744/1008 h 的单一停止条件与资源
   预算，再由作者决定是否启动。任何截断根仍是
   `TEST_ONLY_TRUNCATED_HORIZON`；本节不授权 8760 h、付费云、basis/MGA、
   并发第二求解或 `Crossover=3`。

## 2026-07-31 04:21+08:00 V5 数值稳定化部署与分级门禁

部署身份必须是
`fead34334153eca32bbf7ec3651f3388038ac04b`。该提交把 V5 零控制冷热
状态链精确压缩为“控制小时 + 衰减锚点”，将 168 h presolve 最大系数放大
从 51.094 倍降为 1.0；同时删除冗余变量/约束并增加 V1G/V2G 共享连接
hard QC。`barrier_16_auto_order_stable_basis_v3` 是诊断候选，不是已接受
production profile。

部署前必须重新核验服务器无 CISPO/Gurobi/sequence 进程、checkout clean、
RAM/swap/`vmstat`/memory PSI 正常且 ParaCloud 队列为空。随后：

1. fast-forward 到精确 `fead343`；设置
   `CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260730_flex_v5_4f717de_v1`、
   `CISPO_CF_ROOT=/data/zz2/National_model/data/hourly_cf`、
   `CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse`
   与 `CISPO_WAVE_ROOT=/data/zz2/National_model/data/wave_energy_20260727`。
2. 运行完整 `unittest`、`check_server_readiness.py`、V5 input audit、
   release audit 和水电审计；任一失败即停止。确认常规水电仍为
   `297.8895 + 82.1105 = 380.0000 GW`。
3. 使用全新输出根和
   `config/solver_profiles/barrier_16_auto_order_stable_basis_v3.json`，
   无 `--basis-in`，依次运行 2030 Base 1 h、V5 1 h、Base 24 h、V5
   24 h。每次结束后核对 `OPTIMAL`、`solution_qc=PASS`、58/58 hard
   checks、current input manifest、valid result manifest、wrapper
   stderr/time、raw/presolved/factor、Barrier/Crossover、RSS/swap/PSI。
4. 只有四个短门禁都接受后，才启动一个全新 2030/V5 168 h cold root；
   不启动 Base sequence 或后续年份。重点比较 `Numerical trouble`、
   Barrier residual、Crossover iterations、Kappa、最大 primal/bound/dual
   violation、共享 EV 连接、冷热状态、网络方向性与全部 accounting scope。
5. 168 h 始终是 `TEST_ONLY_TRUNCATED_HORIZON`。本节不授权 744 h、
   8760 h、四年 sequence、付费云、并发第二求解、basis/MGA 或
   `Crossover=3`。不得以 34.3 GiB 全年静态估计替代 Barrier factorization
   内存和可解性证据。

## 2026-07-30 21:29+08:00 有界方向性 warning 的部署与 1008 h V5 授权

实现提交为 `9b6e72a456b0dc8f0123f90b07195f94ca902c9a`。该实现不调大 `1e-6 GW` 检测阈值、不改变 LP 或输电成本；仅允许截断工程根在七项配置预算全部满足时以 `TEST_ONLY_DE_MINIMIS_WARNING` 通过。QC 必须同时保留 `strict_unidirectional_interprovincial_flow=false`、`diagnostic_bidirectional_flow_warning_applied=true`、原始观测值、按时域缩放的限额和 `acceptance_scope=TEST_ONLY_TRUNCATED_HORIZON`。任何全年根都不得应用 warning。

服务器执行顺序：

1. 重新核验本地/origin/GitHub tip、服务器 clean/idle、RAM/swap/vmstat/PSI、目标根不存在和 ParaCloud 空队列；只有三端提交一致且无 solver 时 fast-forward。
2. 在现有 V5 数据根运行完整 `146` 项回归、release/readiness/V5/hydro audits；任何失败即停止。
3. 使用全新根依次运行 2030/1 h、24 h Base/V5，均要求 `OPTIMAL + solution_qc=PASS + 57/57 + current input + valid result manifest`；若出现 warning，必须逐项打印七项 observed/limit，不能只报告 PASS。
4. 从 2030 重新运行四年 168 h Base，不能复用 `af390fa` 失败根的 2030/2040 state；随后以新根运行四年 168 h V5。每年必须闭合 state、碳/CCS/BECCS、冷热、V1G/V2G、firm credit、水电、储能、网络、备用、惯量和成本。
5. 以上全部通过后，作者授权启动唯一串行四年 `1008 h` `flex_integrated_v5_central` sequence。它覆盖连续 42 天，强于 744 h，但仍是 `TEST_ONLY_TRUNCATED_HORIZON`；solver 保持 `barrier_16_auto_order_v2`、cold、no-basis。任一年 timeout、SoftMemLimit、QC、manifest 或 state 失败立即停止，不自动更换 profile 或补跑。

禁止项不变：固定服务器 8760 h、付费云、并发第二求解、basis/MGA 和 `Crossover=3`。

## 2026-07-30 19:38+08:00 168 h Base HARD_FAIL 现场与恢复边界

失败根为 `/data/zz2/National_model/outputs/planning_sequence_168h_v0730_flex_v5_base_af390fa_server_v1`，控制根为 `/data/zz2/National_model/run_control/planning_sequence_168h_v0730_flex_v5_base_af390fa_server_v1`。必须原样保留。2030/2040 已 accepted；2050 Gurobi `OPTIMAL` 但 production QC 因 3 个 material AC bidirectional edge-hours hard fail，故 2050 没有 result manifest/state，2060 未启动。不得调用 `--resume`，不得手工补 manifest，不得跳年。

违规位于 `CORRIDOR_0153`（吉林—黑龙江，AC，容量 `1.646 GW`）的 hour 28/94/95，最大/累计 opposing minimum flow 为 `0.176374 GW`/`0.381006 GWh`。2050 缩放碳上限 binding 且节点电价深度为负，说明线路损耗被用作 BECCS 过剩电量的隐式 sink。现有 `1.004004 CNY/MWh` flow cost 只在常规非负边际条件下足以破除正反向退化；不得把这次失败归为 solver residual，也不得提高 `1e-6 GW` QC tolerance。

恢复顺序固定为：

1. 保持服务器 checkout/output 不动，完成方向性方案审查；方案必须显式说明 LP/MILP 边界、输电损耗、负价、BECCS/碳约束、普通潮流经济性和 8760 h 规模影响。
2. 不允许仅把全体输电流成本提高到高于负节点价格；这种做法会改变所有正常输电、扩建和调度经济性。也不允许新增未审计的自由弃电变量来隐藏同一问题。
3. 方案批准后先做解析单元测试和故意制造负价/过剩电量的最小回归；随后在全新根运行 1 h/24 h Base，并要求原有 57 项 hard checks 全部 PASS、AC counterflow 为 0、input/result manifests 闭合。
4. 再从 2030 开始运行全新四年 168 h Base；不得复用 2030/2040 planning state，因为实现身份已变化。只有 Base 四年完全 accepted 后才允许 V5 168 h。
5. Base/V5 168 h 全闭合前禁止 744 h；继续禁止 8760 h、付费云、basis/MGA、并发第二求解和 `Crossover=3`。

## 2026-07-30 16:58+08:00 V5 当前服务器身份与 168 h 启动边界

当前冻结模型 checkout 为 `af390fad22dc4e3ec4636edadfb56295e4907234`，数据根为 `/data/zz2/National_model/data/model_ready_20260730_flex_v5_4f717de_v1`。V5 manifest SHA256 必须为 `a324430713e0eb3a1671c9b9ba6c127c34c5e0d7c2e21f090cbcd9394f061831`，技术经济 manifest 必须继承 V0729 的 `397297ec...`。任何服务器重建都必须得到与本地完全相同的六项 V5 hashes；不能接受“解析后数值相同但压缩文件 hash 不同”。

服务器 `141/141` regression、readiness、V5 input、release 和 hydro audits 已 PASS。匹配 24 h Base/V5 根：

- `/data/zz2/National_model/outputs/2030_24h_v0730_flex_v5_base_af390fa_server_v1`
- `/data/zz2/National_model/outputs/2030_24h_v0730_flex_v5_central_af390fa_server_v1`

两根均为 `OPTIMAL + solution_qc=PASS + 57/57 + current input + valid result manifest + wrapper exit 0`。两者 Barrier 都报告 numerical trouble，必须保留 `Crossover=1`；不得因 24 h 成功改为 `Crossover=3`。Base/V5 solver runtime 为 `405.882/434.896 s`，simplex 为 `503,365/519,659`，peak RSS 为 `0.759/0.797 GiB`。

下一步只允许以全新输出/控制根串行运行 `scripts/run_cispo_planning_sequence.py --start-year 2030 --end-year 2060 --diagnostic-hours 168 --solver-config config/solver_profiles/barrier_16_auto_order_v2.json`。先 Base，逐年接受且 immediate `--resume` PASS 后，才以 `--scenario-config config/scenarios/flex_integrated_v5_central.json` 运行 V5。每年必须检查 OPTIMAL、57/57、current input/result manifests、state chain、wrapper stderr/time、RSS/swap，以及冷热、V1G/V2G、firm credit、wave、水电、PHS/储能、网络、备用、惯量、碳/CCS 和成本口径。任何失败根不得复用。

容量解释边界：短时域 output 的 `effective_peak_load_gw` 只来自所选领先小时；V5 firm credit 则按完整 8760 h 各省不可变 baseline peak 的四小时窗口、合同容量、功率/能量包络和 derating 计算。因此 24/168/744 h 只能验证工程实现，不能给出年度 effective-peak、ELCC 或科学价值结论。168 h A/B 全闭合后才可启动新的串行 744 h，且仍标记 `TEST_ONLY_TRUNCATED_HORIZON`。

## 2026-07-30 16:05+08:00 集成需求侧灵活性 V5 的分阶段门禁合同

候选实现提交为 `57ad4c5`。Base 不变，正式对比只允许 Base 与一个集成中央反事实；中央反事实同时包含冷热负荷服务、付费 V1G、内生付费 V2G 和折减 firm capacity credit。论文补充材料源文件为 `supplementary_materials/modules/06_integrated_demand_flexibility/integrated_demand_flexibility_methods_en.tex`，技术合同见同目录中文版本和 `config/FLEXIBLE_LOAD_V5_CONTRACT.md`。

部署或扩大求解前必须依次满足：

1. 精确候选下完整 unittest、V5 input audit 和 release audit 均 PASS；
2. 当前身份的全新 1 h/24 h Base/V5 根均满足 `OPTIMAL + solution_qc=PASS + 57/57 + current input manifest + valid result manifest`；
3. 全新、串行四年 168 h Base sequence 逐年 accepted 后，才运行 V5 sequence；任何失败根不得复用；
4. 只在上述全部闭合后，才可部署固定服务器并启动唯一、串行的四年 744 h Base/V5 工程门禁；所有截断时域结果仍标记 `TEST_ONLY_TRUNCATED_HORIZON`。

当前本地 168 h 首次尝试在建模前因 `6.07 GiB < 8 GiB` 可用 RAM 被拒绝。不得降低 `minimum_available_memory_gb`，不得关闭作者应用或清理用户进程，除非得到明确指示。固定服务器虽然无 solver 且资源安全，但遗留 release-audit wrapper PID `976320`/子进程 `976713` 仍存在；PID 存在期间不得 fetch/fast-forward/切换 checkout，也不得启动新任务。若作者授权处理该 PID，必须先确认它不是 solver、记录 `ps`/子进程/输出根证据，再终止并重新核验 clean checkout、进程、RAM/swap/vmstat/PSI、目标根不存在和 ParaCloud 空队列。

24 h 已暴露共同数值风险：Base/V5 都在 Barrier 后报告 numerical trouble，并由 `Crossover=1` 的 `507,293/546,950` 次 simplex 修复为最优解。不得据此切换到已拒绝的 `Crossover=3`；168 h/744 h 必须记录 Barrier、crossover/simplex、终态解质量、RSS、swap 和 wall time。继续禁止 8760 h、付费云、basis/MGA 和并发第二求解。

## 2026-07-30 11:26+08:00 诊断时域年度流量缩放部署合同

候选实现为 `d3b6f1485d5ef88762e9d8d0ac8ca87db15dc244`。短时域统一使用 `f=optimization_hours/8760`：净碳 RHS、DAC 捕集 throughput、生物质燃料和 CO2 sink 注入能力乘 `f`；DAC 小时负荷由窗口捕集量除以 `f` 后的年化速率计算。annualized capacity/fixed cost 不缩放，故短门禁仍是 `TEST_ONLY_TRUNCATED_HORIZON`；8760 h 的 `f=1`。

本地已通过 1 h/24 h 中央 V4 V1G 门禁，均为 `OPTIMAL + PASS + 54/54 + current input + valid result manifest`，且缩放后的 2030 碳约束 binding。部署前不得复用或覆盖 2026-07-29 的旧 744 h 根；必须使用全新输出/控制根，并先完成：

1. 核验本地、origin、GitHub 精确 HEAD；
2. 核验服务器 checkout/dirty state、唯一 CISPO/Gurobi 进程、RAM/swap/vmstat/PSI 和 ParaCloud 队列；
3. fast-forward 后在冻结权威数据根运行 release/readiness、完整回归及全新 1 h/24 h；
4. 明确作者授权后，才可运行新的串行四年 744 h，无 basis、无并发第二求解。

`scenario_catalog v4` 的主分析仅为 `base` 和 `flexible_load_comfort_v4_v1g`。effective-peak、V2G、水电聚合调节与 PHS low/central/high 必须分别以独立输出根调用；V3 仅用于 legacy validation，PHS template 不可运行。不得启动 8760 h、付费云、basis/MGA 或 `Crossover=3`。

## 2026-07-30 09:18+08:00 四年 744 h 终态与停止条件

活动 sequence 已正常结束，`sequence_report.json=PASS`，四年全部 `ACCEPTED`。每年均满足 `OPTIMAL + PASS + 53/53 + current input + valid result manifest`，顶层 wrapper exit 0。当前服务器空闲；本 744 h 工程测试的监控任务应停止。

不得把四年 test-only planning state 用作正式年度 anchor，不得自动调用 8760 h、basis/MGA、付费云或第二求解。后续任何年度科学运行必须基于单独批准的完整 Base/low/high/effective-peak 合同重新执行部署前门禁。

## 2026-07-29 23:21+08:00 当前逐年状态

2030 已由 sequence 严格接受并传递 test-only planning state；2040 正在 Barrier iteration 107。当前无故障、无资源压力，不需要人工动作。继续按下一节只读监控；不得因 2030 accepted 将 744 h 解释为年度科学结果，也不得手工跳过 2040、启动并发任务或修改活动 checkout。

## 2026-07-29 18:45+08:00 四年 744 h sequence 活动监控合同

活动输出根为 `/data/zz2/National_model/outputs/planning_sequence_744h_v0729_identity_hydro_v4_v1g_v1`，控制根为 `/data/zz2/National_model/run_control/planning_sequence_744h_v0729_identity_hydro_v4_v1g_v1`，运行 checkout `5d31b51b350a581287fc8eb13e73216c11fc7543`。初始 wrapper/Python PID 为 `1463763/1463765`，2030 runner 为 `1463870`。

PID 存在时只读检查进程树、`sequence_report.json`、当前年份 `solver_telemetry.jsonl`/`gurobi.log`、RAM/swap/vmstat/PSI、终态三文件和 ParaCloud；不得 fetch/merge/切换 checkout，不得启动第二求解。runner 只有在当前年份 `OPTIMAL + PASS + 53/53 + current input + valid result manifest` 时才会串行接续。任何 HARD_FAIL 或异常退出均保持现场并执行严格终态审计，不得自动补跑。

## 2026-07-29 18:42+08:00 新实现服务器门禁完成，待启动四年 744 h

固定服务器已部署 clean `03e77ccc8d2ef3813b7cc5c0d727b068d008090d`。`/data/zz2/National_model/run_control/deployment_03e77cc_v1` 记录的 release/readiness/hydro/V4 validators 全 PASS，完整 unittest `135/135 PASS`。全新 1 h/24 h 中央 V4 V1G roots 均通过 `OPTIMAL + PASS + 53/53 + current input + valid result manifest + hydro reconciliation audit`。启动 sequence 前必须再次执行下面的只读核验，并确认新根不存在：

- 输出根：`/data/zz2/National_model/outputs/planning_sequence_744h_v0729_identity_hydro_v4_v1g_v1`
- 控制根：`/data/zz2/National_model/run_control/planning_sequence_744h_v0729_identity_hydro_v4_v1g_v1`

sequence 命令继续使用下一节第 5 项的精确参数，保持 serial、cold/no-basis、`barrier_16_auto_order_v2` / `Crossover=1`。任一年未达到全部接受条件，runner 必须停止，不得启动替代求解。

## 2026-07-29 新实现部署与四年 744 h sequence 合同（部署已完成，sequence 待启动）

目标实现提交为 `cea78ae1546b19754f7859982ae82dbf66820fdc`，最终部署应使用随后包含三份交接文档的分支 tip。该实现把常规 run identity 改为轻量 Gurobi fingerprint，修复全年构建后因 >50m nonzeros 调用 `getA()` 而在 optimize 前退出的问题；只有显式 test-only basis 工程可使用完整 CSR topology。Base/中央 V4 继续 `baseline_peak_v1`；`effective_peak_endogenous_v1` 仅在独立 sensitivity 中使用。水电新增 `target_bounded_proportional_transfer_v1` 与两张审计输出，solution QC 由 52 项增至 53 项。

部署前后严格顺序：

1. 实时核验本地、bare `origin`、GitHub branch/HEAD；服务器 checkout/dirty state；所有 CISPO/Gurobi/Python wrapper；RAM、swap、`vmstat`、memory PSI；旧目标根报告；ParaCloud `squeue -u a8s001819`。任何 solver 存在时只监控，不切换 checkout。
2. 仅在服务器空闲时 fast-forward 到已同时推送 origin/GitHub 的精确文档 tip。保持数据根 `/data/zz2/National_model/data/model_ready_20260729_unified_7c56622_v4`、CF 根 `/data/zz2/National_model/data/hourly_cf`、hydro 根 `/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse` 与既有 wave 根。
3. 先运行 release contract、readiness、hydro/V4 validators 和完整 unittest。服务器权威 technoeconomic manifest 必须为 `397297ec3980ffb38988a0463f934e310f228cbe48268d59ce38c7fa8350ec75`；本地 ignored manifest 的不同时间戳 hash 不得覆盖服务器数据。
4. 在全新根顺序运行 1 h 与 24 h `flexible_load_comfort_v4_v1g` + `barrier_16_auto_order_v2`，要求 `OPTIMAL + solution_qc=PASS + 53/53 + current input manifest + valid result manifest`，并核对 `hydro_cascade_reconciliation_audit.json`。
5. 以上全闭合后，使用 `scripts/run_cispo_planning_sequence.py --start-year 2030 --end-year 2060 --diagnostic-hours 744 --scenario-config config/scenarios/flexible_load_comfort_v4_v1g.json --solver-config config/solver_profiles/barrier_16_auto_order_v2.json` 启动唯一串行 sequence。新输出根和控制根必须先确认不存在；wrapper 使用 `/usr/bin/time -v`、独立 stdout/stderr、PID 与 sequence claim。不得传入 basis。
6. 每年只在 `OPTIMAL + PASS + 53/53 + current input + valid result manifest` 后传递显式 `TEST_ONLY_TRUNCATED_HORIZON` planning state。任一年失败即停止，不能跳年或启动替代求解。四年 744 h 仍不是年度科学结果或正式 state anchor。

禁止项不变：固定服务器 8760 h、付费云、并发第二求解、basis gate、MGA、Dual Simplex/PDHG 付费 A/B 与 `Crossover=3`。

## 2026-07-29 统一 release candidate 的固定服务器 744 h 门禁

执行状态（2026-07-29）：门禁 1--4 已在干净服务器提交 `7c56622c266e673037bd6afaa70c85aa57e6cb13` 和最终数据根 `/data/zz2/National_model/data/model_ready_20260729_unified_7c56622_v4` 上完成；服务器完整回归 `130/130 PASS`，1 h/24 h V4 cold 均为 `OPTIMAL + QC PASS + 52/52 hard checks + valid input/result manifests`。唯一 744 h 根 `2030_744h_v0729_unified_v4_v1g_cold_v1` 也已完成严格验收，控制证据保存在 `/data/zz2/National_model/run_control/2030_744h_v0729_unified_v4_v1g_cold_v1`。运行锁已从“活动求解保护”转为“不得由本门禁自动启动任何后续求解”。

terminal checkpoint（2026-07-29 16:32+08:00）：服务器 checkout 仍为 clean `7c56622`，审计前本地/固定服务器 bare `origin`/GitHub 文档基线为 `5ffee8a`，模型实现仍为 `7aac739`；无需切换服务器 checkout。wrapper/Python PID `1004972/1004975` 已退出。Gurobi 为 `OPTIMAL`，objective `2,330,214.449430 million CNY`、runtime `12,984.854 s`、Barrier/simplex `313/832,655`、Crossover `3,573.87 s`；wrapper exit `0`、wall `3:42:57`、peak process-tree RSS `21.484 GiB`、swaps `0`。`solution_qc=PASS`、`52/52` hard checks、current input manifest 与 result manifest validator 均闭合；冷热/EV、wave、水电、PHS/储能、网络、备用、惯量、碳/CCS、成本 scope 已严格审计。主机约 `114 GiB` available、swap `781 MiB/2.0 GiB`，实时 `vmstat si/so=0`、memory PSI=0；ParaCloud 队列为空。旧 release-audit SSH/bash/grep 管道无 Python/Gurobi solver 子进程，本次未终止。

接受边界：该结果只能标记为 `TEST_ONLY_TRUNCATED_HORIZON`。其 objective 混合 annualized planning 与 744 h operation scope，不能作为年度科学结果、年度净价值或正式 2040 state anchor。V4 low/high、完整 accepted Base anchor、basis 工程与 MGA 仍未闭合；不得由本门禁启动固定服务器 8760 h、付费云、并发第二求解、basis gate 或 `Crossover=3`。

任务边界：当前命令是 `scripts/run_cispo_2030_full_year.py --planning-year 2030 --horizon one_month`，仅运行一个 2030 V4 V1G cold gate；它不是、也不会自动转入 `2030→2040→2050→2060` 接续求解。服务器代码包含 `scripts/run_cispo_planning_sequence.py`，但该 runner 当前未调用。744 h 是 `TEST_ONLY_TRUNCATED_HORIZON`，不能成为正式 2040 科学状态 anchor；只有未来独立授权且逐年满足接受合同的 sequence 才能进行状态传递。

生产货币口径同样属于本 release：`technoeconomic_2025_cny_v2` 已在代码、服务器数据 sidecar、活动 input manifest 和 resolved config 中闭合，正确实施提交为 `29bbf90d9edde4e74e3e095b807f2fa1ffaab6a6`。后续不得回到旧 2022-CNY/旧 FX 表或把说明性 V4 成本机械重平减。

本轮隔离部署把 `config/model_input_files.json` 升级为 v10；标准包必须包含 42 张运行表、12 个 server sidecar，归档中另含 `model_input_files.json`，合计 55 个条目。必须特别保留 `load/flexible_load_envelope_v3.{csv.gz,manifest.json}`、五张 V4 表、`flexibility/flexible_load_v4.manifest.json`、`wave/wave_sites.csv` 与 `wave/wave_input_manifest.json`。只传 V4 表而漏来源、只传 manifest 而漏 V3/wave 本体，都会在服务器回归或场景 dry-run 中失败。

当前本地匹配 Base/V4 V1G 的 2030→2040→2050→2060 168 h 序列已全部闭合，机器审计为 `outputs/planning_sequence_168h_v0729_ab_audit/planning_sequence_ab_audit.{json,csv}`。它证明递进 state、冷热/EV 输入、波浪输入、全模型 QC 和当前资源占用稳定；不证明年度价值。任何比较必须同时确认 `result_use=TEST_ONLY_TRUNCATED_HORIZON`，不得把年化 planning/enablement cost 与 168 h operation benefit 的差直接称为年度净收益。

作者已授权代码/外置数据口径统一后启动一个固定服务器 744 h 或两个月门禁。当前选择
标准 `one_month=744 h` 的 `flexible_load_comfort_v4_v1g` cold gate；它是既有支持时域，
同时覆盖新 Base 水电、wave 与 V4，且不需要新建时域接口。统一实现提交为
`1d04f07565c3039ed467ec4080f276bd0da90786`；部署时使用包含本节交接更新的最新分支 tip，
并确认相对该实现只增加文档变更。必须按以下顺序执行：

1. 本地 `scripts/audit_release_contract.py`、完整 unittest、V4 input validator、hydro input
   validator 和四个 1 h 模块根全部通过；精确暂存不得包含 `supplementary_materials/**` 或
   `.codex_tmp/**`。提交并推送后以 commit SHA 作为部署身份。
2. 实时核验固定服务器 checkout/dirty state、CISPO/Gurobi 进程、RAM/swap、`vmstat`、PSI、
   磁盘和目标输出根；同时核验 ParaCloud 队列。存在第二求解或内存持续换页时停止。
3. 从既有 model-ready 数据根复制出全新版本化根，只向新根安装 release contract 的外置
   文件；不得覆盖历史数据根。逐文件 SHA256 必须与 `release_contract_v0729.json` 相同。
4. 在精确 checkout 和新数据根运行 release audit、readiness、input-manifest、完整 tests，
   然后依次运行全新 1 h 与 24 h V4 cold；任一项不是
   `OPTIMAL + solution_qc=PASS + closed result/input manifests` 即停止，不启动 744 h。
5. 只启动一个全新命名的 2030 V4 V1G `--horizon one_month` cold root，显式使用
   `barrier_16_auto_order_v2` / `Crossover=1`，不传 `--basis-in`。持续记录 Barrier/crossover、
   raw/presolved/factor、RSS/swap/PSI、冷热/EV、wave、水电、成本 scope 和所有 hard checks。
6. 744 h 仍为 `TEST_ONLY_TRUNCATED_HORIZON`。不得启动 8760 h、付费云、并发第二求解、
   Base/V3/PHS/hydro-flex basis reuse 或 `Crossover=3`；MGA 仍等待完整 accepted Base anchor。
   V4 low/high 是论文参数敏感性的后续任务，不是本次工程稳定性门禁的前置条件。

下一窗口接续顺序固定为：

1. 完整读取 `AGENTS.md`、`CODEX_HANDOFF.md`、`cispo_full_lp_model_spec.md`、`MODEL_SERVER_STATUS.md`、`SERVER_RUNBOOK.md`。
2. 只读复核本地/双远端 Git，固定服务器 checkout/dirty state、唯一 PID/子进程、`solver_telemetry.jsonl`、`free -h`、`vmstat`、memory PSI、三个终态 JSON 与 ParaCloud `squeue`。
3. 若 PID 仍存在，仅监控，不改 checkout、不启动任何求解。若 PID 已退出，不以退出码或日志结尾单独验收；必须读取并交叉验证 `solve_report.json`、`solution_qc.json`、`result_manifest.json`、当前 `input_manifest.csv`、wrapper stderr/time 和全部模块输出。
4. 只有 `OPTIMAL + QC PASS + 52/52 hard checks + current input/result manifests valid` 才把该 744 h 工程门禁标为接受；随后更新三份交接文档。科学上仍保留 V4 low/high、完整 accepted Base anchor、basis/MGA 等开放项。

截断成本输出必须同时保留旧兼容列和以下解释字段：`value_million_cny_model_accounting_period`、`accounting_scope`、`optimization_hours`、`result_use`。`ANNUALIZED_PLANNING_COST` 是年化规划口径，`SELECTED_HORIZON_OPERATION_COST` 只覆盖当前求解窗口。缺少这些元数据的旧结果可以做数值/机制审计，但不能直接用于年度成本图表。

此前固定服务器 `701b9bc`、约 `70 GiB` available、swap 约 `19/21 GiB` 与空 ParaCloud
队列只是旧快照，不能作为本次启动证据；必须在部署和 744 h 启动前分别重新核验。

## 2026-07-28 常规水电 380 GW 省级聚合层的部署前门禁

当前本地未提交候选增加 `data/hydro/provincial_aggregate_capacity_2025.csv` 和 `data/hydro/provincial_aggregate_monthly_capacity_factor_2019.csv`，并将 `config/model_input_files.json` 升级为 v6。它把 297.8895 GW 站点级常规水电与 82.1105 GW 固定省级聚合容量闭合为 380 GW。省级聚合层是新的 LP topology：其发电变量进入省级平衡和 337 负荷中心年度注入，但不进入站点水文、梯级、备用、惯量、容量充裕性或 spur/trunk。不得导入任何旧 Base、duplicate-COMID-only 或跨年 `.bas`。

本节不授权服务器或云端动作。作者审阅并提交精确实现后，如单独批准部署，必须按下列顺序执行：

1. 本地工作树先分离并保留用户无关改动；提交/推送精确模型与生成脚本。核对两张新 CSV、31 省、372 省月行、全国 `297.8895 + 82.1105 = 380 GW`、PHS `65.94 GW` 以及输入 manifest v6 的 SHA256/role。
2. 远程实时核验 clean checkout、无 CISPO/Gurobi、RAM/swap/PSI 和输出根；把现有 model-ready 数据根复制到全新版本化根，只 add-only 安装两张新水电表及 v6 manifest，禁止覆盖旧根或把 82.1105 GW 写成伪站点。
3. 同时设置与新数据包匹配的 `CISPO_DATA_ROOT`、`CISPO_CF_ROOT`、`CISPO_HYDRO_ROOT` 和 `CISPO_WAVE_ROOT`，运行数据包 readiness、输入 manifest、focused hydro tests 和完整回归。注意本地原生水文索引分散在既有绝对路径时应保持 `CISPO_HYDRO_ROOT` 未设置；不要用错误的统一根覆盖索引路径。
4. 只运行全新、隔离、非并发的 1 h 和 24 h cold Base 根；要求 `OPTIMAL + solution_qc=PASS + closed manifest`，并核对 `hydro_aggregate_capacity.csv`、31×hours 的聚合发电、availability hard check、337 负荷中心聚合注入总量、成本分解、raw/presolved/factor 指标和 RSS。
5. 24 h 仍只是截断门禁。不得据此启动 168h/744h/8760h、复用 basis、覆盖旧输出或提交付费云任务；更长门禁必须由作者基于新的 topology、内存证据和科学敏感性另行授权。

## 2026-07-28 V4 冷热/EV 数据支撑型情景的运行门禁

当前未提交工作树中的 `flexible_load_comfort_v4_v1g` 与 `flexible_load_comfort_v4_v2g_sensitivity` 是新的 LP topology，不是 Base 或 V3 的 resume/basis 变体。禁止在三者之间复制 `.bas`、planning state 或把某一情景的性能外推给另一情景；V1G 是工程中心情景，V2G 仅作独立敏感性。

五张数据表已由已有 `hourly_load_2025_2060.csv.gz` 和 `flexible_load_envelope_v3.csv.gz` 生成。重新构建与验收使用：

```powershell
conda run -n RL python scripts/build_flexible_load_v4_inputs.py

conda run -n RL python scripts/validate_flexible_load_v4_inputs.py `
  --source-manifest data/load/flexible_load_envelope_v3.manifest.json `
  --source-manifest config/flexible_load_v4_source_registry.csv `
  --source-manifest config/flexible_load_v4_central_parameters.csv `
  --source-manifest config/flexible_load_v4_source_count_qa.csv
```

验收必须确认四个规划年均通过 loader energy closure、五张表的 SHA256 与 source manifest 非空；`connected_vehicle_fraction` 只能为聚合服务归一化 1，`minimum_departure_energy_gwh` 必须为 0，不得把二者重标为实测车辆行为。builder 必须使用固定 gzip `mtime=0`；连续两次完整 build+validate 的输出应逐文件字节一致，当前 sidecar SHA256 为 `ad46c7610903726a059b92255332056935021763ca11433b0b866b6dd1ac144a`。当前本地成功根为 `outputs/2030_1h_v0728_flexible_load_v4_data_supported_v3`、`outputs/2030_24h_v0728_flexible_load_v4_data_supported_v2` 和 `outputs/2030_1h_v0728_flexible_load_v4_v2g_data_supported_v2`，均须同时通过 result manifest 与当前 input manifest；失败的 `outputs/2030_1h_v0728_flexible_load_v4_data_supported_v1` 必须保留为 export 类型 bug 证据，不得 resume 或重标。

当前停止条件是作者审阅。若作者接受公式和中心值，下一步只运行一个全新、隔离、非并发的本地 168 h V1G cold root，并记录 raw/presolved/factor、Barrier/crossover、QC、manifest 和 RSS。该门禁只证明工程可解性；论文结论前仍须执行参数登记中的 low/high。不得由此启动 basis 工程、固定服务器 744h/8760h、付费云任务或并发第二个求解；`Crossover=3` 永久拒绝。

## 2026-07-28 M2 boundary audit: local decision closure, no deployment

`379a96a79cf14d7dc08d0a5cfd45b8223f2f4b47` adds a read-only M2 decision register and scenario parameter registry. It validates the locked Base identity, cohort VRE boundary, scenario-only V3/V2G overrides, explicit BECCS evidence status, the duplicate-COMID configuration flag, and MGA-anchor stop condition without building or solving an LP. Its local output is `outputs/m2_model_boundary_audit_20260728_local_v3/` (`9 PASS, 0 OPEN, 0 hard fail`); it does not license a server operation.

The present `static_capacity_potential_share_v1` duplicate-COMID hydrology implementation remains a user-owned uncommitted candidate. Local 1h/24h candidate roots are closed, but the 24h Barrier stage reported numerical trouble before Crossover produced `OPTIMAL`. Until its owner has reviewed and committed it, do not transfer it, fast-forward a server checkout, or infer a 168h/744h/8760h permission. After an explicit accepted commit, the only possible next solver gate is a newly named, isolated **local** 168h cold Base run, one solve at a time, with `barrier_16_auto_order_v2` and `Crossover=1`; record objective, hydro generation, raw/presolved/factor diagnostics, QC, manifest, RSS and the complete solver log. It remains prohibited to use `Crossover=3`, a cross-year basis, a concurrent second solve, fixed-server 744h/8760h, or any paid-cloud task.

## 2026-07-28 swap 清理判定规则

若 swap 占用高，先只读检查 `Cached/Buffers`、`AnonPages`、主要进程 `VmSwap`、`vmstat si/so` 和 PSI；不可把 `free` 的 buff/cache 或低当前 I/O 误判为“swap 可清”。本次约 `19.1 GiB` swap 已归因于活跃 Python/MATLAB 的匿名页，`drop_caches` 不会降低它。

只有确认没有会受影响的非 CISPO 作业，或获得主机级明确授权并确认约 `70 GiB` available RAM 仍充足时，才可在维护窗口使用受监控的 `swapoff/swapon` 回迁页面；完成后必须重新核验 RAM、swap、进程与 PSI。当前不满足前一条件，故不执行清理、不部署、不启动 CISPO。

## 2026-07-28 重复 COMID 水量修复的部署前门禁

本地 `static_capacity_potential_share_v1` 修复改变水电可用流量系数但不增加 LP 行列：同一 `COMID` 的站点按 `capacity_potential_gw` 静态份额共享一次扣除环境流量后的河段径流，梯级节点汇总成员站份额。该实现和 Module 05 / S6 审查包已通过 `116/116` 本地回归、1 h/24 h `OPTIMAL + PASS + closed manifest` 与 9/9 补充材料 formal closure；这些都只是本地截断工程证据。

本节不授权部署。18:15 后只读核验的服务器仍为干净 `701b9bc225013a5009dcce3f4e97ee2063dcd00f`、无真实 CISPO/Gurobi 进程、约 70 GiB available RAM，但 swap 约 19/21 GiB；因此继续停止。若未来单独授权部署，必须：

1. 先提交并推送精确实现，确认本地工作树中不混入补充材料或用户无关改动；服务器再次实时核验 clean checkout、进程、RAM/swap 和目标输出根。
2. fast-forward 到精确提交，并同时设置当前 `CISPO_DATA_ROOT`、`CISPO_CF_ROOT`、`CISPO_HYDRO_ROOT`、`CISPO_WAVE_ROOT`；先运行完整回归和输入 manifest 校验，确认配置项 `duplicate_comid_flow_allocation=static_capacity_potential_share_v1`。
3. 只在一个全新隔离根运行匹配 24 h，再由作者决定是否需要一个 168 h cold Base 门禁；比较水电发电量、目标、raw/presolved 结构、全部 QC、manifest 与峰值 RSS。不得复用任何旧输出根或把旧 744 h 结果重标为新口径。
4. 不得由本门禁启动固定服务器 744/8760 h、第二个并发求解或付费云任务。正式多年 P30、清单覆盖、PHS 水力配对和容量语义属于独立科学决策，不能在部署时静默修改。

## 2026-07-28 M1 168h 四根 basis gate 已闭合后的停止条件

在本地 `a5e34bf` 实现、`barrier_16_auto_order_v2` / `Crossover=1` 下，2030 和 2040 的 cold/warm 四根均已达到 `OPTIMAL + PASS + closed manifest`，同年 objective 完全一致，warm 均为 0 Barrier/0 simplex。2040 仅接收 `2030_168h_v0728_m1_statebridge_local_v1` 的显式 diagnostic state，且只导入其自身 `2040 cold` basis。它们只证明同年、同 raw CSR topology 的截断 LP 可加速，不能转化为年度科学结果或跨年 basis 许可。

当前不运行 744h basis gate。原因是 basis 需要先有同一 744h cold root；在没有第二个同构 744h 求解需求时，新增 cold root 本身不产生可回收的端到端收益。等待真实的重复同构工程需要或新的、经授权的运行目标；届时先实时核验服务器和 ParaCloud，仍禁止 `Crossover=3`、并发第二求解、固定服务器 8760h 和付费云任务。

本里程碑后的实际只读复核为：服务器干净 HEAD `701b9bc225013a5009dcce3f4e97ee2063dcd00f`，无 CISPO/Gurobi、约 `70 GiB` available RAM，但 swap 约 `19.1/21 GiB` 且有约 `43.0 GiB RSS` 的无关 Python；ParaCloud 队列为空。这个组合仍触发暂停条件：不部署、不复制数据、不启动服务器求解。该快照会变化，任何后续动作必须再次执行同样的只读核验。

## 2026-07-28 M0/M1 basis 身份协议与当前本地门禁

`a5e34bf5357301c205b246b0aa2149db0dca9c3b` 将运行身份拆为 `scientific_case`、`solver_runtime`、`implementation_bundle`，并在 LP 构建后写入 `lp_topology`。导入 basis 时必须同时满足：source closed manifest、`OPTIMAL + solution_qc=PASS`、相同 diagnostic hours、同规划年（除非代码明确的跨年例外）、basis SHA256，以及变量/约束顺序和方向、维度、NNZ、raw CSR sparsity pattern 的精确 topology 一致。只有 `lp_topology` 是 basis 兼容硬门；scientific/implementation 差异必须留下审计记录，且 warm root 永远不能替代科学 Base 验收。

当前 Base 为 `base_2024_vre_wave_on_flex_off_v1`：VRE 2024 北京自然年、wave 2023、hydro 2019；既有 VRE 生产 mode 为 `cohort_survival_v1`，`fixed_floor_v1` 仅为可重复的对照。BECCS lifecycle low/base/high 只是目录外 post-solve screening，不加 LP 行列、不能声称重新优化的可行性；bound tightening 仅保留已证明不改变可行域的变量上界。

在任何远程动作前，先在当前本地提交上顺序完成五个根：2030 168h cold、2030 warm、2030 state bridge、2040 168h cold、2040 warm。2040 只接收显式 test-only 2030 planning state，且只导入自身 2040 cold basis；任何跨年 basis、`Crossover=3`、第二个并发求解、744h、8760h 和付费云任务均禁止。现有下节 168h 根在本协议之前生成，只能作历史性能参考。

本节不授权部署：若未来确有远程必要性，仍先重新只读核验服务器 HEAD/工作树、CISPO/Gurobi 进程、RAM/swap、数据根和 ParaCloud 队列；swap 压力、非预期 checkout 或任何活动任务都要求停止。只有随后经过 add-only data 安装、完整回归和一个新命名 168h cold 根，才可另行评估下一阶段。

## 2026-07-28 intra-grid/cohort 168h basis 结果与服务器暂停条件

本地四根 168h Base 门禁已验证同年同结构的 guarded LP basis：2030 cold/warm solver `576.593/11.406 s`，2040 cold/warm `543.965/15.517 s`；均为 `OPTIMAL + solution_qc=PASS + closed manifest`，warm 均为 0 Barrier/0 simplex，cold/warm 容量一致。2040 仅接收明确 diagnostic 的 2030 state bridge，并且只使用 2040 自身 basis；不得以此说明跨年 basis 或生产全年复用。四根均输出并校验 `intra_grid_vre_site_design.csv` / `intra_grid_substation_design.csv`，其中 2025 VRE initial trunk proxy 为 `1,069.512666 GW`，旧 nameplate proxy 为 `1,309.999999962 GW`。

本地门禁不触发服务器部署。2026-07-28 即时只读检查虽未发现 CISPO/Gurobi 进程，且显示约 70 GiB 可用内存，但 swap 已用约 `19/21 GiB`，并有约 45 GiB RSS 的无关任务。因此严禁在该状态下切换 checkout、复制 cohort 输入或启动服务器 168h。ParaCloud 队列当时为空，但这不是后续操作的实时证明。

恢复服务器门禁的必要顺序是：先确认 swap 压力已解除、无求解/无冲突任务，再重新读 HEAD/内存/数据根/ParaCloud；add-only 安装 checksummed cohort CSV/sidecar；fast-forward 到精确推送提交；完整回归；最后在全新目录运行唯一的 168h cold Base 根。任何一步不符即停止。此门禁前后都不得使用 `Crossover=3`、跨年 basis、第二个并发求解、744h、8760h 或付费云任务。

## 2026-07-28 同格网风光共享并入 / 既有 VRE cohort 的部署前门禁

该本地模型变更对齐 CISPO S4-18/S4-19：site spur 使用 `max_t(cf) × capacity`，共享 wind/PV trunk 使用同一 substation 内 potential-weighted equivalent peak；它不增加逐小时 LP 行/列。既有 VRE 改用可追溯 cohort：已知 GEM 投运年按寿命退出，未知/OSM/残差与边界后投运容量只作 2025 boundary-censored cohort；退出不删除技术 site upper，因而同址再建是可选投资而非强制重建。此变更在本地 24h 通过 QC/manifest 和 `102/102` 回归，但尚未部署。

部署前必须按以下顺序执行，且一次只有一个求解：

1. 在本地从精确提交运行 `scripts/build_existing_vre_cohorts.py`，核对 `data/vre/existing_capacity_cohorts_2025.csv` 及 sidecar manifest 的 SHA256；当前已验证 CSV hash 为 `e00791ec9597897da80377458d6acefdc481ef1708c0f86d68adb2a5576f92d0`。服务器数据根只能 add-only 安装这两个文件，不覆盖既有输入。
2. 实时读取服务器 Git HEAD、`ps`/`pgrep`、`free -h`、目标数据根和 ParaCloud 队列；若有任何活动 CISPO/Gurobi job、内存压力、非预期 checkout 或目标输出根已存在，停止，不切换 checkout。
3. 仅在空闲服务器 fast-forward 到精确已推送提交，设置全部三个数据根，并先运行完整回归和 preflight。回归、input manifest 或 cohort SHA256 任一不一致即停止，不手工绕过。
4. 仅在全新隔离目录运行一个匹配 168h Base 门禁，保持 `barrier_16_auto_order_v2` 和 `Crossover=1`。比较 `raw/presolved`、factor 指标、Barrier/crossover、objective、全部 QC、result manifest、进程树 RSS，以及 `intra_grid_vre_site_design.csv` / `intra_grid_substation_design.csv` 的容量闭合。
5. 不得把历史接受的 744h 根当作该科学边界的 anchor；不得使用已拒绝的 `Crossover=3`，不得并发第二个求解、启动固定服务器 8760h 或提交付费云任务。168h 的单次门禁只有在上述所有证据闭合后才可决定是否申请隔离 744h basis 门禁。

## 2026-07-28 Crossover=3 744h 严格 A/B 已结束：拒绝候选、保留 Crossover=1

`/data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_crossover3_v1` 是唯一的、隔离的 solver-only A/B 根；它没有覆盖参考根或历史输出。该根在 `701b9bc`、2024 Base、wave on、flexible load off 和相同 raw/presolved/factor 结构下只把 `Crossover=1` 改为 `Crossover=3`。

Barrier 完成于 `6,981.07 s`（211 次），PPush/DPush 分别为 `1,191.93/1,214.00 s`，但 primal simplex cleanup 发生严重 infeasibility 循环。在 `10,930.99 s`、`1,724,960` simplex iterations 时向隔离候选发送一次 `SIGINT`，Gurobi 正常记录 `INTERRUPTED`；其无 solution、`solution_qc.json` 或 `result_manifest.json`，因此绝不可解释为 Base 解或“更快的 744h”。峰值进程树 RSS 为 `19.828 GiB`、无 swap，故失败原因是 crossover 数值路径而非内存。

生产决定：保持接受的参考根
`/data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_v2` 与
`config/solver_profiles/barrier_16_auto_order_v2.json` (`Crossover=1`)；不要把
`barrier_16_crossover_3_v1.json` 用于任何 744h/8760h/MGA anchor。保留两根和
`/data/zz2/National_model/outputs/solver_ab_v0728_crossover_744h.{json,csv}` 作为正反对照证据。

后续任何 solver/formulation 候选必须先在新 24h、168h 根上获得
`OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，并记录
raw/presolved 规模、`AA' NZ`、Factor、全部阶段时间、迭代、objective、QC 与 RSS；只有唯一赢家才可运行一个新的 744h 根。当前服务器无活动求解；不得启动第二个求解、固定服务器 8760h 或新的付费云任务。

## 2026-07-28 744h 运行锁已释放

`/data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_v2` 已达到 `OPTIMAL + PASS + manifest true`，原 wrapper/Python 进程均已退出。运行锁解除仅允许在重新核验 clean checkout、无进程和安全内存后 fast-forward 文档提交；不构成启动第二个 744h、固定服务器 8760h 或付费云任务的授权。

该根的 crossover 为 5,709.46 s，占 solver 时间约 43%。后续 8760h 方案必须单独处理 crossover 策略和 basis/MGA 需求，不能只按 Barrier 7,543.19 s 外推。

## 2026-07-28 168h 选择与 744h 唯一候选

服务器 2024 CF 与 `9a3c5e8` 已部署，完整回归及三组 168h 均闭合。省级年度排放分层不改变 presolved/factor/迭代，禁止仅因 raw dense row 消失就将其选为生产 formulation。`PreDual=1`、`PreSparsify=2` 已由 24h 淘汰。

新 744h 只允许：

```text
formulation: national_dense_v1
solver: config/solver_profiles/barrier_16_auto_order_v2.json
hours: 744
weather: Beijing natural-year aligned 2024
output: /data/zz2/National_model/outputs/2030_744h_v0728_2024_dense_dualred_v2
```

选择依据是 168h 总时间 668.05 s 对 700.50 s、`AA' NZ` 低约 8%、`Factor NZ` 低约 1.8%、RSS 持平；风险是 Barrier 只到 `performed`，crossover 190.62 s 对 72.76 s、simplex 630,993 对 229,459。744h 必须监控 build/presolve/ordering/Barrier/crossover、进程树 RSS 和 solver telemetry；若达到 `MEM_LIMIT`、无进展或异常 swap 增长，应保留输出并停止，不得启动并发替代 case。

## 2026-07-28 2024 VRE 部署与 Phase A/B 放大顺序

当前本地实现提交 `1449a457` 尚未部署；服务器仍为 `4e1999d`，且 `/data/zz2/National_model/data/hourly_cf` 缺少 2024 stores。新代码需要同时读取各技术的 `cf_hourly_*_2023.zarr` 与 `cf_hourly_*_2024.zarr`，覆盖 `onshore_wind`、`offshore_wind`、`pv` 和 `mixed_wind`。

2024 数据只能在再次确认无求解进程、目标目录不存在、磁盘足够后追加传输；不得覆盖 2023 stores。传输前后记录每个目录的文件数、总字节和归档 SHA256。然后 fast-forward 到已经同时推送 `origin`/`github` 的精确提交，设置四个数据根，运行完整 discovery 回归。

服务器放大采用顺序匹配门禁，绝不并发：

1. 168h dense + `barrier_16_infeasibility_diagnostic_v1`，复现 `DualReductions=0 + InfUnbdInfo=1`；
2. 168h dense + `barrier_16_auto_order_v2`，只改变为 1/0；
3. 仅当第二步 factor/阶段证据有价值时，再运行 168h province hierarchy + 同一 profile；24h 已证明其 presolve 后矩阵与 dense 完全相同；
4. 每根必须满足 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，并记录 raw/presolved rows、columns、nonzeros、`AA' NZ`、`Factor NZ/Ops`、build/presolve/ordering/Barrier/crossover、迭代、objective、RSS；
5. 选择唯一胜者后，以全新名称启动一个 744h 根。启动前再次检查无第二个求解及安全可用内存；不得因 744h 压测改变 Base 目标、约束、时空尺度或技术边界。

固定服务器 8760h 继续禁止；ParaCloud 8760h 仍需用户另行确认。

## 2026-07-28 当前 Base 工程门禁与 basis 复用协议

当前部署 checkout 为 `/data/zz2/National_model/repo` 的 `4e1999d`，仅在实时确认无进程且内存安全后 fast-forward。使用附加的 wave-ready 数据根 `/data/zz2/National_model/data/model_ready_20260723_v0722_city337_wave_20260727`、CF 根 `/data/zz2/National_model/data/hourly_cf`、水文根 `/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse` 和波浪根 `/data/zz2/National_model/data/wave_energy_20260727`；不得替换为历史 wave-off 根。

当前 Base 已完成 1h、24h、168h 工程序列，每项均使用新根并满足 `OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`。168h 根为：

```text
/data/zz2/National_model/outputs/2030_168h_v0728_server_wave_base_barrier16_v1
```

它是 `TEST_ONLY_TRUNCATED_HORIZON`，不是年度科学结果。168h 求解耗时 690.86 s，其中 Barrier 584.20 s、crossover 104.23 s；后续性能比较必须同时保留两个阶段、raw/presolved 维度、`AA' NZ`、`Factor NZ`、`Factor Ops`、目标/QC 和峰值 RSS。机器可读的 1h/24h/168h 及 basis A/B 表位于 `/data/zz2/National_model/outputs/solver_audit_v0728/`。

仅限 test-only 的 LP basis 复用：先从 `OPTIMAL + PASS` 诊断根以 `--export-warm-start-basis` 导出。导入时传入 `--basis-in SOURCE_ROOT --allow-basis-reuse`；跨年还必须显式传入 `--allow-cross-year-basis`，并提供相应已验收的 diagnostic `--state-in` 与 `--allow-diagnostic-state-in`。runner 会验证源 result manifest、源终态、git commit、情景、小时数、basis hash、raw dimensions 和完整有序的带名称 LP 结构。它设置 `LPWarmStart=2` 以保留 presolve。该机制不会序列化或复用 Gurobi 模型、Barrier factorization、presolve state 或 crossover tableau。科学全年运行及 raw 非零元超过 50m 的矩阵均被显式禁止自动 basis 复用。

绝不并发运行两个 CISPO 求解。不得触碰历史输出根，尤其是 `/data/zz2/National_model/outputs/2030_744h_v0726_spill_explicit_barrier16_auto_order`。固定服务器 8760h 仍被禁止。新的云端 8760h 必须获得用户单独确认，并具备不可变代码/数据/情景 hash、新门禁、高内存 Slurm 方案、线程/SoftMemLimit、成本预估与停止规则。MGA 必须作为独立的“成本约束后二级目标”工作流实现和运行；不得覆盖或重标 Base 最小成本输出。

`4e1999d` 已提供 MGA runner 选项：`--mga-spec SPEC.json --mga-baseline BASE_ROOT`。它只接受闭合的 `SCIENTIFIC_PRODUCTION + BASE_MINIMUM_COST + OPTIMAL + PASS` 年度 Base 根，且要求同一计划年/边界年、已解析配置和 required-input SHA256；诊断时域、basis 复用、diagnostic state 和既有 MGA 输出均被拒绝。通过后模型保留原年度成本表达式并添加成本上限，再最小化或最大化一个明确筛选的新增容量目标；结果写入 `mga_request.json`/`mga_run.json`，不导出 `planning_state`。当前没有 accepted 年度 Base，故只允许 MGA preflight/契约测试，不得执行 MGA 求解。

## 2026-07-27 原始 LP 稀疏审计：仅本地闭合，不得据此扩大求解

本地提交 `6114157` 增加可选的 `--constraint-family-audit`。该开关仅在
`model.update()` 后读取原始稀疏矩阵，默认 `50,000,000` 个非零元是硬安全上限；
超过即停止审计，禁止为完整 744h/8760h 提高上限。它不改动任何变量、约束、
目标、场景、数据或 Gurobi 数值参数。`constraint_family_audit.json` 与结果目录
一起被 catalog 和 SHA256 manifest 记录，包含原始约束/变量族、最稠密 25 行/列，
以及求解日志的全局 presolve、ordering、`AA' NZ`、`Factor NZ`、`Factor Ops`、
Barrier/crossover 指标。不得把 Gurobi 的全局 presolve 删除量虚假归因给某个族。

本地 1h/24h 新根
`outputs/2030_{1h,24h}_v0727_constraint_family_audit_base_v3` 均满足
`OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，
波浪能开启、灵活负荷关闭，完整回归 `75/75`。24h 根为 raw
`231,074/345,992/1,729,035`、presolved `129,335/260,116/1,269,506`
（rows/columns/nonzeros），`AA' NZ=2.200e6`、`Factor NZ=6.284e6`、
`Factor Ops=7.399e8`、89 Barrier、57,741 crossover/simplex、29.107 s 和
0.712 GiB RSS。最稠密原始行是 `annual_emissions_accounting`（6,697）、
`capacity_margin_p65/p15`（6,491/5,736）和 `co2_source_balance_p*`（各 3,246）；
水电逐站平衡不是当前首要密集行来源。

这只是候选筛选，不是删约束许可。下一步仅为年度排放会计分解建立代数等价证明，
并在新的隔离 Base 24h 根上同机、同 profile 做一次 A/B。只有目标、全部 QC、
manifest、raw/presolved 尺度、factor、阶段时间、迭代和 RSS 都通过后，才可决定是否
运行 168h。未部署固定服务器、未查询或修改 ParaCloud；不得据此启动服务器 168h、
744h、8760h 或新的付费云任务。

## 2026-07-27 孤立梯级节点等价清理：仅本地已验收，禁止直接扩大求解

本地提交 `9787ba7` 不删除拓扑源数据或水电站：142 个节点、124 条边保持不变。只有 8 个已经核验为零度、单站的节点从逐小时核心梯级装配转入向量化独立水库平衡。它们没有上游到达流，其局部 GRFR 入流就是独立平衡的入流，因此物理方程、库容、弃水和可行域均不变；有效核心梯级站点行从 146 变为 138。任何多站孤立节点均会使建模硬失败，不能静默转换。

设置 `CISPO_WAVE_ROOT` 的本地完整回归通过 `71/71`；新的 Base 1h/24h 根
`outputs/2030_{1h,24h}_v0727_cascade_isolated_nodes_independent_base` 均满足
`OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，波浪能开启、灵活负荷关闭。24h 目标相对清理前只差 `9.78e-09 million CNY`，raw/presolved 规模不变；但 `Factor NZ/Factor Ops` 从 `6.111e6/6.039e8` 变为 `6.284e6/7.399e8`，且 34.636 s 不优于 33.766 s。因此将其视为局部 Python 约束构建清理，不得宣传为 Barrier、内存或 8760h 优化。

本轮没有服务器或云端操作。后续如获单独授权，必须先实时复核固定服务器 checkout、CISPO/Gurobi 进程、`free -h` 和数据根，部署精确的已推送提交，再以全新隔离根运行一个单一的匹配 168h Base 门禁。不得并发、覆盖历史输出、启动固定服务器 8760h 或提交新的付费云任务。

## 2026-07-27 连续 RUC 等价瘦身：仅本地已验收，服务器操作需另行授权

本地实施提交 `3f2255a` 移除了连续 RUC 中四组严格冗余的逐小时上界行：
`online<=capacity`、`startup<=capacity`、`shutdown<=capacity`、`gross<=pmax*online`。
它们分别由保留的 S4-24、S4-25、S4-29 和变量非负下界蕴含；建模前硬校验
`min_up_h>=1`、`min_down_h>=1`、`pmin_fraction<=pmax_fraction` 及参数完整性。不得在
未保留这些行或未通过硬校验的分支上套用此说明。

本地完整回归 `69/69`，以及新建 Base 1h/24h 根
`outputs/2030_{1h,24h}_v0727_ruc_dominated_bounds_removed_base` 均为
`OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`；Base 波浪能开启、
灵活负荷关闭。24h 原始行数/非零元减少 `32,736/65,472`，变量和目标值不变；但 presolved
矩阵、`AA' NZ`、`Factor NZ`、`Factor Ops`、Barrier/crossover 迭代都完全相同。因此把它记录为
原始构建负担的等价缩减，不能以此声称 8760h Factorization 已加速或可行。

本轮没有服务器部署或远程写操作。只有用户另行授权后，才可按顺序：实时读取服务器
checkout/进程/内存/数据根 → 部署精确的已推送提交 → 用新的、隔离的含波浪 Base 输出根运行一个
匹配 168h A/B。不得并发求解、覆盖任何历史输出、启动固定服务器 8760h，或提交新的付费云端任务。

## 2026-07-27 新 Base：波浪能已整合；服务器尚未部署

当前仅允许两个可运行身份：

1. `base`：风电（含海风）、光伏、严格映射至既有 marine `grid_uid` 的波浪能；`flexible_load=false`。
2. `flexible_load_comfort_v3_v2g_5pct`：继承上述 Base，并启用 `comfort_envelope_v3` 冷热状态、EV V1G 和因果日内 5% V2G；它仍是参数待校准的敏感性。

提交 `c992550` 删除其余实验性 scenario JSON；不删除历史输出、数据或 Git 证据。两个当前身份都必须先设置 `CISPO_WAVE_ROOT`。本地 1h/24h 均已通过 `OPTIMAL + solution_qc=PASS + validate_result_manifest=True`，完整回归为 `66/66`；但这不构成服务器部署、更不构成 8760h 授权。新 Base 的全年静态预估为 36.47 GiB，柔性覆盖层为 37.63 GiB，不能用来判断 Barrier factorization。

旧服务器 wave-off Base 根一律保留且只作历史证据，不能作为重定义后 Base 的新门禁结果。若用户另行授权服务器测试，先实时复核空闲 checkout/进程/内存，部署精确推送提交，并且仅运行一个全新的、明确命名的 168h 根；固定服务器 8760h 和新付费云端任务仍禁止。

## 2026-07-27 全模块联合敏感性：本地门禁完成，服务器运行尚未授权

本地新增的 `wave_energy_medium_v1_flexible_load_comfort_v3_v2g_5pct` 同时启用波浪能、
`comfort_envelope_v3` 冷热、V1G 和 5% 日内因果 V2G。它是参数待校准的独立敏感性，
不是 Base；不得通过覆盖 Base JSON、环境变量或默认开关把它伪装为 Base。

本地 1h/24h/168h 已各自形成新根并通过
`OPTIMAL + solution_qc=PASS + validate_result_manifest=True`；168h 的 factor 结构为
`AA' NZ=2.162e7`、`Factor NZ=1.056e8`、`Factor Ops=8.603e10`。其全年静态 preflight
估计 37.63 GiB，但这不是 Barrier factor/workspace 的内存保证，更不是 8760h 授权。
详细输出、短窗口解释限制与结构优化次序见
`MODEL_COMBINED_MODULE_SOLVABILITY_AUDIT_20260727.md`。

禁止仅因该本地结果启动固定服务器 8760h、新付费云端任务或并发第二个求解。若用户另行
授权服务器比较，先实时核验空闲 checkout/进程/内存，并且只运行一个新的、明确命名的
168h 根；同机、同线程、同 solver profile 的 Base 对照是记录模块求解性增量的前置条件。

## 2026-07-27 Base 168h generic-wrapper manifest 门禁已通过

固定服务器在空闲且 clean 的 `c879c99` 上复核后，fast-forward 到已推送的
`67482ab`（其中 P0 实施为 `7499062`），并完成服务器 discovery 回归 `67` 项
通过、`2` 项可选 xarray 测试跳过。相对于原固定服务器模型实现，新增的唯一
模型邻接代码为 runtime-log manifest 排除；不得将它表述为 LP 或科学边界变化。

已完成且必须保留的新门禁根：

```text
/data/zz2/National_model/outputs/2030_168h_v0727_manifest_runtime_contract_base
```

命令使用 `barrier_16_auto_order_v1`、`Threads=16`、`SoftMemLimit=48`、
`Crossover=1`，将 wrapper 输出重定向到通用 `stdout.log`/`stderr.log`，并由
`/usr/bin/time -v` 记录端到端资源。终态为 `OPTIMAL + solution_qc=PASS +
scenario_id=base + validate_result_manifest=True`，Base 灵活负荷和波浪能均关闭；
所有 hard checks 通过。原始/预处理矩阵为
`1,393,915/1,011,079/9,797,949` 和 `729,559/817,723/7,001,232`
（rows/columns/nonzeros）；`AA' NZ=2.131e7`、`Factor NZ=1.036e8`、
`Factor Ops=8.436e10`。Gurobi 运行 614.894 s（161 Barrier、226,659
simplex/crossover），端到端 12:24.94，峰值进程树 RSS 3.453 GiB，未发生 swap。

`result_manifest.json` 明确排除 `run.pid`、`stdout.log`、`stderr.log`；最终
`validate_result_manifest()` 为真且无失败项，证明最终报告打印发生在 manifest
finalize 后时，wrapper 日志不会再污染科学哈希契约。这个 168h 根仅为
`TEST_ONLY_TRUNCATED_HORIZON`。不得写入、重建或原地修复旧
`2030_744h_v0726_spill_explicit_barrier16_auto_order`；不得启动固定服务器
8760h 或新的付费云端 8760h。

接下来 P2 若需要处理旧 744h，只能先设计名称明确、目录外且只读的
post-run audit manifest；只有研究协议明确要求原目录 result manifest 闭合时，
才可申请全新根的修正版 744h。P3 候选必须先在匹配 24h/168h 记录 raw/presolved
rows、columns、nonzeros、`AA' NZ`、`Factor NZ`、`Factor Ops`、phase time、
Barrier/crossover、objective/QC 与 RSS；不得以改变 Base 科学边界换取加速。

## 2026-07-27 manifest 契约 P0 在本地闭合

提交 `7499062` 修复通用 shell 重定向文件名缺口：`stdout.log` 和
`stderr.log` 均为 runtime-managed artifacts，已从科学输出目录及
`result_manifest.json` 排除；不改变任何科学模型设定。回归先 finalize
manifest，再向两类通用 wrapper 日志追加，并验证所有科学文件哈希仍可
验证。完整本地回归通过 `67/67`。

新的 Base 诊断根为：

```text
outputs/2030_1h_v0727_manifest_runtime_contract
outputs/2030_24h_v0727_manifest_runtime_contract
```

两者均为 `OPTIMAL + solution_qc=PASS + scenario_id=base`，manifest 闭合且
灵活负荷/波浪能关闭；24h 门禁有 342,343 个变量、262,201 条约束、1,771,702
个非零元、41.296 s 求解时间和 0.725 GiB 峰值 RSS。它们仅为 test-only
门禁。不得向旧 744h 目录写入。提交推送后，先重新核验固定服务器 checkout、
CISPO/Gurobi 进程和可用内存，再决定是否部署并启动一个新的 168h Base 根。
固定服务器 8760h 与所有新的付费云端 8760h 工作仍禁止。

## 2026-07-26 solvability-optimization campaign

The user has explicitly authorized sequential 744h or longer fixed-server stress
tests for the latest model, provided the host does not exceed safe memory. This
authorization supersedes earlier fixed-server 744h prohibitions in older entries,
but it does not authorize a fixed-server 8760h solve or another paid cloud run.

Required sequence:

1. preserve `supplementary_materials/**` user changes and commit only reviewed
   non-supplementary code/config/test/handoff files;
2. verify the fixed server has no CISPO/Gurobi process, then fast-forward the
   checkout to the exact pushed commit;
3. export the four versioned runtime roots and pass the complete server regression;
4. retain explicit spill: its matched 168h factor structure and telemetry memory
   are lower, and its 24h flexibility runtime is materially faster;
5. compare dual simplex, Barrier-16 and CPU-PDHG sequentially at 168h;
6. run only one 744h profile at a time, requiring at least 56 GiB available RAM
   before launch and using `SoftMemLimit=48`;
7. compare `build_report.json`, `solver_telemetry.jsonl`, `gurobi.log`,
   `solve_report.json`, `solution_qc.json`, process-tree peak RSS and `/usr/bin/time`;
8. stop further profiles after any memory hard failure or when available RAM falls
   below the gate. Never run multiple profiles concurrently.

The independent-reservoir spill projection in `6d84209` is mathematically exact,
but raw-column reduction alone is not an acceptance criterion. The matched 168h
projection is 1.84% faster, yet explicit spill has lower presolved rows/nonzeros,
lower `AA' NZ`, `Factor NZ`, `Factor Ops` and telemetry solver memory. Explicit
spill is also 24.0% faster in the paired flexibility case. Commit `9e82cc5`
therefore remains the default because 8760h is factor-memory bound. Preserve both
output roots and the audit at:

```text
/data/zz2/National_model/outputs/solver_comparisons/spill_168h_ab_v0726.json
/data/zz2/National_model/outputs/solver_comparisons/spill_168h_ab_v0726.csv
```

Solver profiles are numerics-only JSON files and are separately hashed in
provenance:

```text
config/solver_profiles/barrier_32_reference_v1.json
config/solver_profiles/barrier_16_sparse_amd_v1.json
config/solver_profiles/barrier_16_auto_order_v1.json
config/solver_profiles/dual_simplex_16_v1.json
config/solver_profiles/barrier_32_limited_presolve_fast_basis_v1.json
config/solver_profiles/barrier_32_force_dual_v1.json
config/solver_profiles/pdhg_cpu_32_v1.json
```

Run CPU PDHG only with Gurobi 13.0+ (the fixed server qualifies); local Gurobi
12 must not be used for that profile. Use `scripts/compare_solver_runs.py` to
write one JSON and CSV row per isolated output root.

Dual simplex is not a 744h candidate. The 168h run was stopped gracefully after
905.073 solver seconds and 421,470 pivots without a feasible basis, compared with
654.026 s for a complete Barrier-32 solution. Preserve its diagnostic root:

```text
/data/zz2/National_model/outputs/2030_168h_v0726_spill_explicit_dual_simplex16
```

Barrier-16+AMD completes 168h in 644.636 s with lower RSS, but AMD increases
factor nonzeros and operations. Do not promote it directly to 744h. First run
`barrier_16_auto_order_v1.json`, which changes only the thread limit relative to
the Barrier-32 reference.

The automatic-order control completes in 637.344 s and is the current Barrier
leader while preserving the reference factor structure. The first PDHG launch
root named `2030_168h_v0726_spill_explicit_pdhg_cpu32` is a pre-build config
failure, not a solve. Use a new output root only after the `pdhg_gpu` solver-key
whitelist regression passes on the server.

The corrected CPU-PDHG root is:

```text
/data/zz2/National_model/outputs/2030_168h_v0726_spill_explicit_pdhg_cpu32_v2
```

It was gracefully terminated after 3,074.134 solver seconds with no feasible
solution. The last telemetry record is near iteration 496,035; peak solver and
process-tree memory are only 1.990 GB and 2.503 GiB, but the terminal primal
residual is still about 49.5 and the dual residual is rising. Retain it as a
low-memory diagnostic, not as the first 744h profile.

The active one-at-a-time 744h gate is:

```bash
OUT=/data/zz2/National_model/outputs/2030_744h_v0726_spill_explicit_barrier16_auto_order
PID=663050
ps -p "$PID" -o pid,etime,%cpu,%mem,rss,vsz,stat,cmd
tail -n 100 "$OUT/stdout.log"
tail -n 20 "$OUT/solver_telemetry.jsonl" 2>/dev/null
ls -lh "$OUT"/{build_report,solve_report,solution_qc,result_manifest}.json 2>/dev/null
```

It uses clean server HEAD `c879c99`, the `city_337` data root,
`barrier_16_auto_order_v1`, `Threads=16`, `Crossover=1` and
`SoftMemLimit=48`. Available RAM was about 69 GiB at launch. Do not start a
second fixed-server solve. PID exit is not acceptance: require `OPTIMAL`,
`solution_qc=PASS`, a closed result manifest and inspection of process-tree
peak RSS, presolve/factor structure and crossover behavior.

The verified active-run structure checkpoint is:

```text
build: 341.673 s; 3,686,023 columns; 5,920,701 rows; 42,360,391 nonzeros
build peak process-tree RSS: 4.977 GiB
presolve: 223.80 s; 3,017,979 columns; 3,088,821 rows; 30,884,732 nonzeros
ordering: 115.48 s
AA' NZ: 6.449e7
Factor NZ: 8.062e8 (about 9.0 GB)
Factor Ops: 6.197e12
early telemetry peak solver memory: 25.087 GB
```

This passes the build/factor memory gate but is not solve acceptance. Continue
monitoring the Barrier residual trajectory and subsequent crossover; do not
infer success from factorization alone.

Barrier subsequently completed normally in 244 iterations and 8,917.48 solver
seconds with interior objective `2,196,881.94 million CNY`. The active run is
now in crossover:

```text
initial dual pushes remaining: 1,044,784
dual pushes remaining at solver time 9,860 s: 464,775
latest telemetry checkpoint: 358,606 simplex iterations at 9,996.25 s
current / peak solver memory: 13.948 / 25.087 GB
```

Do not treat the Barrier objective as the accepted LP result. Continue until
crossover and any primal cleanup finish, then require `OPTIMAL`,
`solution_qc=PASS`, a closed result manifest, `scenario_id=base` and final
process-tree memory/time evidence.

The run subsequently completed:

```text
status: OPTIMAL
objective: 2,196,881.920967378 million CNY
solver runtime: 13,541.717 s
Barrier / simplex iterations: 244 / 1,451,182
wall time: 3:52:03
peak process-tree RSS: 23.121 GiB
swaps: 0
solution_qc: PASS
scenario: base
```

Scientific checks pass, but strict manifest validation returns only
`size:stdout.log`. The manifest records 63,631 bytes and the completed file has
66,236 bytes. The launch wrapper used `stdout.log`, while
`RUNTIME_MANAGED_FILES` recognizes `runner_stdout.log`, `run.stdout` and the
sequence variants. Because the entrypoint prints the final solve report after
manifest finalization, hashing the generic redirected log creates a stale
manifest.

Preserve this output unchanged. Treat it as valid mathematical/QC and
performance evidence, but not as a closed reproducibility gate. Before any
replacement run, align the wrapper filename with the runtime-managed contract
or make a reviewed additive contract fix with regression coverage. Do not
silently regenerate the existing manifest or overwrite the terminal output.

## 2026-07-27 next-phase closure and scale-up gate

Live closeout state:

```text
fixed-server implementation HEAD: c879c99 (clean)
fixed-server CISPO/Gurobi process: none
fixed-server available RAM: about 69 GiB
ParaCloud active jobs: none
8760h accepted scientific result: none
```

Follow this order:

1. Make a minimal local manifest-contract fix. Generic wrapper files
   `stdout.log` and `stderr.log` must be runtime-managed/excluded, or the
   alternative design must prove they cannot change after manifest
   finalization. Add a regression that appends to a wrapper log after finalize
   and still validates every scientific file.
2. Preserve
   `/data/zz2/National_model/outputs/2030_744h_v0726_spill_explicit_barrier16_auto_order`
   byte-for-byte. Never regenerate its `result_manifest.json` in place.
3. Pass the complete local regression and new Base 1h/24h roots with
   `OPTIMAL`, `solution_qc=PASS`, `scenario_id=base` and a closed result
   manifest. Then, only on an idle clean fixed server, deploy the exact commit
   and run one new 168h Base root.
4. Do not rerun 744h solely because the wrapper log changed. Default to an
   explicitly named, directory-external, read-only post-run audit for the old
   result. Request a corrected 744h rerun only if the research acceptance
   protocol requires the original in-directory manifest to close.
5. For solvability work, compare candidate formulations/settings on matched
   24h and 168h cases before any 744h. Record raw/presolved rows, columns and
   nonzeros, `AA' NZ`, `Factor NZ`, `Factor Ops`, Barrier/crossover iterations,
   objective/QC equivalence and process-tree peak RSS. Do not change Base
   physics, temporal resolution, objective or constraints to obtain speed.
6. A new ParaCloud 2030/8760h solve requires separate explicit authorization,
   immutable code/data/scenario hashes, fresh 24h/168h gates, a reviewed
   high-memory node/thread/time-limit plan, estimated billed core-hours and
   termination rules. Never launch fixed-server 8760h.

Scientific work may proceed independently only behind scenario/accounting
boundaries: Base keeps flexibility and wave disabled; flexibility V3 requires
building/EV calibration and low/base/high tests; total 2025-2060 transformation
cost requires a discounted pathway ledger or an explicitly approved
multi-period objective; MGA cost-relaxation and point/province/national
complementarity follow an accepted Base scientific solution.

For Slurm deployments, request a termination warning such as
`--signal=B:TERM@300` and set the Slurm wall limit at least five minutes longer
than Gurobi `TimeLimit`. This lets the signal handler call `Model.terminate()` and
write a normal interrupted report. `solver_telemetry.jsonl` is flushed during
optimization and remains useful even if a later hard kill prevents final export.

Cloud job `4004585` is terminal `TIMEOUT`. It reached Barrier iteration 35 with
476.76 GiB sampled MaxRSS but remained far from convergence, and it produced no
acceptance reports. Preserve its output unchanged.

## 2026-07-25 Barrier-32 live factorization evidence

At `2026-07-25 20:30 CST`, job `4004585` has passed ordering and reached Barrier
iteration 23:

```text
Ordering time: 3180.53 s
AA' NZ: 7.425e8
Factor NZ: 3.848e10
estimated factor memory: 340.0 GB
Factor Ops: 2.448e15
Threads: 32
MaxRSS: 499,919,116 KiB = 476.76 GiB
```

The residuals are decreasing, but no accepted solution exists. Slurm ends the job
at `2026-07-26 02:34:26 CST`, about 6:04 after this checkpoint. Because the
Gurobi 86,400-second limit begins after model construction, the Slurm wall limit
will arrive first. Do not interpret a later scheduler kill as mathematical
infeasibility, and do not extend the paid allocation or start another job without
explicit authorization.

## 2026-07-25 active Barrier-32 full-year diagnostic

User-authorized ParaCloud job `4004585` is the only active full-year retry. It uses
the immutable `22fb493` Base/`city_337` release and the additive script:

```text
/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493/cloud_cispo_8760_2030_base_barrier32.sbatch
SHA256 fc604a1a25d37c9cff8a336c83969809cb5b52ea0ab815183d1ea3a7a96bfbf2
```

Relative to failed job `4003172`, change only:

```text
Gurobi Threads: 128 -> 32
Slurm CPUs/Task: 128 -> 32
job/log/output identity: new and isolated
```

Retain `Method=2`, `Presolve=2`, `Crossover=1`, `SoftMemLimit=640`, 700G,
24h and every scientific setting. The output root is:

```text
/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493/outputs/full_year_2030_base_22fb493_barrier32_700g_v0725
```

Initial evidence at `2026-07-25 02:35 CST`: job `4004585` is `RUNNING` on
`m4cg1702`; 50/50 tests pass; the generated config records `threads=32`.
Because 700G forced an allocation of 96 CPU/billing units, do not estimate this
run at only 32 billed core-hours per wall-clock hour. Monitor with:

```bash
squeue -j 4004585 -o '%i|%j|%T|%M|%D|%C|%m|%R'
sstat -j 4004585.batch --format=JobID,AveCPU,MaxRSS,MaxVMSize
tail -n 80 cloud_cispo_8760_base_b32-4004585.out
tail -n 80 outputs/full_year_2030_base_22fb493_barrier32_700g_v0725/gurobi.log
```

The failed 128-thread job consumed `CPUTimeRAW=2,642,304` allocated CPU-seconds,
or 733.973 core-hours; actual `TotalCPU` was only 7:03:11. Slurm exposes this
usage but not the ParaCloud paid-credit or remaining currency balance.

Do not start 2040 or another retry. Accept only after terminal Slurm state plus
`solve_report.json`, `solution_qc.json` and `result_manifest.json`; reaching
`Barrier statistics`/iteration 0 is diagnostic progress but not scientific
acceptance.

## 2026-07-25 cloud full-year OOM boundary

Job `4003172` is terminal `OUT_OF_MEMORY`; do not resubmit its batch script unchanged.
The build-only gate is still valid, but the real solve proved that build memory is not a
barrier-factorization memory estimate.

Terminal facts:

```text
state: OUT_OF_MEMORY
exit: 0:125
elapsed: 05:44:03
request: 128 CPU / 700G
recorded MaxRSS: 526.99 GiB
presolve time: 17,932.25 s
presolved model: 37,982,903 rows / 35,423,761 columns / 400,861,556 nonzeros
terminal stage: ordering before barrier iteration 0
```

The absence of `solve_report.json`, `solution_qc.json` and `result_manifest.json` is
decisive. Preserve the failed root:

```text
/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493/outputs/full_year_2030_base_22fb493_128cpu_700g
```

`Crossover=0` is not a remedy because crossover was never reached. Raising only
`SoftMemLimit` is also unsupported: Slurm killed the step before the configured 640G
soft limit was reported. The 750G-class node rebooted shortly after the event, while
accounting captured only 526.99 GiB; require administrator evidence before interpreting
that value as the true peak.

Before another paid full-year attempt, first choose and validate a lower-memory solver
route on bounded gates or secure a genuinely larger-memory node. Any new 8760h submission
requires a new output identity, explicit user authorization and monitoring through
presolve, ordering, factorization, barrier and QC. Do not start 2040 from this failed
2030 root.

## 2026-07-25 existing-grid correction and combined wave/flexibility cases

This section supersedes the nearest-offshore-wind routing language in the older
wave section below. `scripts/build_wave_energy_inputs.py` must produce contract
`wave_existing_grid_v2`: only coordinate-matched rows already present in
`optimization_points.csv` with `is_land=0` are eligible. Require 1,285 unique
`grid_uid` rows, exact route equality with `city_337/vre_routes.csv`, maximum
coordinate difference no larger than `0.02` degrees, and the recorded source/table
SHA256 values. Never map source rows outside the optimization grid to a distant
in-model anchor.

Two reproducible combined cases are available:

```text
config/scenarios/wave_energy_medium_v1_flexible_load_v1.json
config/scenarios/wave_energy_medium_v1_flexible_load_comfort_v3.json
```

Each combined file enables wave and flexible load in one LP. Comparative Base,
single-module and combined cases remain separate sensitivity-suite runs with
separate output roots. Deployment still requires an explicitly authorized,
versioned release and fresh tests/preflight/24h build and solve-QC gates.

## 2026-07-25 `wave_energy_medium_v1` local-only deployment boundary

The optional wave module is not present in any accepted fixed-server or cloud release.
Base must keep `features.wave_energy=false`. Enabling the scenario requires three
separately verified artifacts:

```text
config/scenarios/wave_energy_medium_v1.json
data/wave/wave_sites.csv
data/wave/wave_input_manifest.json
```

and the external hourly source:

```bash
export CISPO_WAVE_ROOT=/versioned/path/to/wave_energy
test -f "$CISPO_WAVE_ROOT/wave_grid.nc"
```

Rebuild the small site contract locally before transfer:

```bash
$PYTHON scripts/build_wave_energy_inputs.py \
  --wave-netcdf /source/path/wave_grid.nc \
  --output-directory data/wave
```

Require the source and site-table SHA256 values in `wave_input_manifest.json`.
Do not interpret the nearest offshore-wind routing anchor as a maritime boundary or
engineering cable route. Do not claim scenario-specific potential: the current source
potential is identical across all ten CF scenarios. The configured 2060 profile/cost is
an explicit 2050 hold.

After separate deployment authorization, use a new release and output root. First run
tests, wave preflight and a 24h build-only gate. A later 24h optimization must additionally
pass wave availability, power balance, reserve, load-center closure, cost, cohort and
manifest checks. Do not share offshore-wind spur/trunk in this scenario. A successful
local build is not permission for server/cloud 24h, 168h, 744h or 8760h execution.

## 2026-07-24 `comfort_envelope_v3` local-only deployment boundary

The V3 implementation is an independent sensitivity and is not present in the fixed-server
checkout or active cloud release. It requires both code and the ignored generated input:

```text
data/load/flexible_load_envelope_v3.csv.gz
data/load/flexible_load_envelope_v3.manifest.json
```

Rebuild locally from the recorded `Power_curve_V2` products with:

```bash
$PYTHON scripts/build_flexible_load_envelope_v3.py
```

The accepted local table has 1,357,800 rows and SHA256
`b5ebda4344a8f978606c242065159f27a75994a5d976f2cbe06038d66a429a03`.
The input manifest must record both the scenario table and its sidecar. Never stage only the
scenario JSON: a missing or mismatched envelope must hard-fail.

Main and optional V2G scenario files are:

```text
config/scenarios/flexible_load_comfort_v3.json
config/scenarios/flexible_load_comfort_v3_v2g_5pct.json
```

The 5% value means 5% of each province-day baseline EV peak power, not 5% vehicle
participation and not a policy mandate. Main V3 keeps V2G disabled. The V2G sensitivity uses
`daily_zero_causal`, so it cannot borrow energy from the end of a day.

After explicit deployment authorization, create a new versioned code/data/output identity and
first require:

```bash
$PYTHON -m unittest discover -s tests -q
$PYTHON scripts/run_cispo_planning_sequence.py \
  --scenario-config config/scenarios/flexible_load_comfort_v3.json \
  --diagnostic-hours 24 \
  --output-root /data/zz2/National_model/outputs/planning_sequence_24h_<version>_flexible_load_comfort_v3
```

Acceptance additionally requires four valid input/result manifests, four
`OPTIMAL + solution_qc=PASS` years, `flexible_load_formulation=comfort_envelope_v3`,
closed thermal state and V1G backlog transitions, zero daily terminal state/backlog, zero
simultaneous up/down, correct cost components and four `RESUMED_ACCEPTED` records. Validate the
no-V2G main scenario before separately testing the 5% V2G case. A successful 24h local gate is
not permission for server 168h/744h/8760h or cloud execution.

## 2026-07-24 `flexible_load_state_v2` deployment boundary

Implementation `271c6dc` is local-only. It adds
`config/scenarios/flexible_load_state_v2.json` and does not change the accepted Base,
`flexible_load_v1` or `flexible_load_v2g_v1` configurations. Never update an active
server/cloud checkout or reuse an accepted output root for this code.

The new module uses `Power_curve_V2` load components already present in
`hourly_load_2025_2060.csv.gz`. Heating/cooling have causal daily-reset equivalent
inventories; EV V1G has a causal daily-reset charging backlog. Do not relabel
`ev_hour_weight` as vehicle availability. Configuration validation intentionally rejects
V2G in this formulation until hourly availability, usable battery energy and departure
service are provided.

After explicit deployment authorization, first verify an idle clean server and use a new
checkout/data/output identity. Minimum gates are:

```bash
$PYTHON -m unittest discover -s tests -p 'test_*.py' -v
$PYTHON scripts/run_cispo_planning_sequence.py \
  --scenario-config config/scenarios/flexible_load_state_v2.json \
  --diagnostic-hours 24 \
  --output-root /data/zz2/National_model/outputs/planning_sequence_24h_<version>_flexible_load_state_v2
```

Require four `OPTIMAL + solution_qc=PASS` years, four valid result manifests,
`scenario_id=flexible_load_state_v2`, `flexible_load_formulation=state_envelope_v2`,
closed thermal/EV transitions, zero daily terminal state/backlog, no simultaneous
up/down, valid capacity-cohort hashes and four `RESUMED_ACCEPTED` records. Only then may
an explicitly authorized new 168h root start. The current full-year estimate is
43,356,367 variables/68,724,249 constraints/524,283,387 nonzeros; do not infer
fixed-server 744h/8760h or paid-cloud 8760h authorization from this estimate.

## 2026-07-24 local CF-fallback hardening deployment boundary

The local post-release change forbids cross-technology wind-to-PV CF fallback and adds hard preflight checks. It does not alter the currently staged cloud release and must not be copied into an active checkout or output root. Current production inputs already resolve all 45 wind primary-store gaps through same-grid `mixed_wind`; the patch therefore changes no current wind CF mapping or model scale. When deploying later, require a new versioned code/output identity, 54/54 local-equivalent tests, preflight checks `vre_cf_cross_technology_fallback=PASS` and `vre_cf_pv_fallback_uses_land_grid=PASS`, followed by new 24h and 168h gates.

## 2026-07-24 cloud execution state: accepted small gates and one authorized 2030 Base full-year job

The staged city_337 release now has accepted cloud gates `outputs/cloud_gate_24h_base_2030_22fb493` (`4003035`) and `outputs/cloud_gate_168h_base_2030_22fb493` (`4003045`). Both use the released code/data roots, `Threads=32`, pass 50/50 tests, reach `OPTIMAL`, pass QC and close their result manifests. Do not rerun into either root.

`4003088` completed the non-solving 8760h construction gate in 40m20s with exit `0:0`; its build report records 40,912,327 variables, 68,189,325 constraints, 515,040,080 nonzeros and 53.633 GiB peak process-tree RSS. The dependent real 2030 job `4003172` started normally on `m4cg1702`, using 128 CPU/700G/24h and root `outputs/full_year_2030_base_22fb493_128cpu_700g`. Its runtime configuration changes only `numerics.threads=128` and `numerics.soft_mem_limit_gb=640`; do not change any scientific model setting.

At 2026-07-24 21:17 CST, the solve job had completed the full model build in about 40m32s, entered Gurobi `Optimize`, and used 96.402 GiB batch MaxRSS. The log had not yet reached a presolve-complete line or barrier iteration. Continue monitoring Slurm accounting, Gurobi log and memory; `solve_report.json`, `solution_qc.json` and `result_manifest.json` were not yet present. Do not launch a successor planning year until the 2030 root is accepted.

## 2026-07-24 ParaCloud city_337 staged preflight (current cloud state)

The additive release is `/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493`; do not overwrite it. It contains code archive `National_model_22fb493.tar.gz`, the checksummed runtime roots `data/model_ready_20260723_v0722_city337`, `data/hourly_cf` and `data/hydro_timeseries_20260719_sequential_sparse`, and the source-to-cloud SHA256 manifest. The 2030 Base 8760h `--preflight-only` job `4001137` passed on a compute node with 175.17 GiB available memory; its scale is 40,912,327 variables, 67,604,064 constraints and 520,922,832 nonzeros. This proves neither model construction nor optimization.

Do not submit the staged `cloud_cispo_8760_preflight.sbatch` as a Gurobi build substitute. On 2026-07-24 the user-authorized `.bashrc` repair replaced malformed whitespace in its three proxy exports; its backup is `.bashrc.codex_backup_20260724_proxy_export`. Job `4002980` confirmed the proxy is inherited on `m4ci1905` and returns HTTP 302 through `172.16.110.3`; job `4002981` then completed the authenticated Gurobi WLS LP (`GUROBI_SMOKE_PASS`). Its short curl health probe timed out despite the successful solver authentication, so accept Gurobi's `Env.start()` plus `OPTIMAL` as the WLS gate. Retain explicit lower- and upper-case proxy exports in production batch scripts as defensive reproducibility.

Only after that smoke succeeds, use a new versioned 24h cloud root, then a new 168h root, both with `Threads <= --cpus-per-task`, full manifests and QC. A full-year `--build-only` is still a distinct later gate; it requires at least 96 GiB available memory and must not be treated as evidence that barrier factorization or a production solve fits. The raw GRFR source is deliberately not in this runtime release; add it only when running the separate raw-hydrology provenance readiness check.

## Accepted V0722 city_337 V2G gate

The Base, V1 and independent V2G 24h/168h gates are accepted for `city_337`. The accepted V2G 168h root `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v2g_v1` has four `OPTIMAL + solution_qc=PASS` years, four valid 59-entry manifests and four `RESUMED_ACCEPTED` records. The server is idle at checkout `cf39e0a` with data root `/data/zz2/National_model/data/model_ready_20260723_v0722_city337`. Revalidate without changing checkout:

```bash
OUT=/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v2g_v1
pgrep -af '[r]un_cispo_2030_full_year.py|[r]un_cispo_planning_sequence.py' || true
cat "$OUT/sequence_report.json"
```

The accepted chain has closed network/BECCS/security checks, V2G transition closure, zero simultaneous charge/discharge, explicit charging-loss accounting and an immediate four-year `--resume`. Keep `run.stdout`, `run.stderr` and `run.pid` as wrapper evidence. Do not launch fixed-server 744h/8760h.

## V0722 city_337 deployment and small-gate contract

Implementation `8e76753` changes the production spatial input contract from `natural_earth_278` to `city_337` and includes the reviewed 5% capacity-margin/3.5 s inertia baseline. Because `data/` is intentionally outside Git, deploy code and data as two independently verified artifacts. Never copy over the active V0721 data root.

Required new data files are `load_center_network/city_337/{load_centers,vre_routes,hydro_routes,intra_edges,initial_spur_capacity_2025,substation_initial_capacity_2025}.csv`; retain the package README, manifest, initialization audit and route comparison as sidecars. Verify the transferred archive SHA256 before extraction, copy the current data root to a new additive root, and extract only the `city_337` subdirectory there.

Before changing checkout, require `git status --short` empty and no `run_cispo`/Gurobi process. Then run, with the new data root and existing CF/hydrology roots:

```bash
$PYTHON -m unittest discover -s tests -p 'test_*.py' -v
$PYTHON scripts/preflight_cispo_2030.py --output /data/zz2/National_model/outputs/preflight_v0722_city337.json
$PYTHON scripts/run_cispo_planning_sequence.py \
  --diagnostic-hours 24 \
  --output-root /data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337
```

Accept only if all four years are `OPTIMAL + solution_qc=PASS`, scenario ID is `base`, flexibility is disabled, every result manifest closes, load-center outputs contain 337 unique nodes, center/province/capacity residuals pass, security manifests record 5% and 3.5 s, and `--resume` returns four `RESUMED_ACCEPTED` years. Only then launch the corresponding new 168h Base root. Current live memory (about 35 GiB available with swap occupied) is sufficient only for these small gates; do not launch 744h/8760h on the fixed server.

## V0722 reviewed reliability update — not deployed

The local working tree at Git HEAD `e28f315` changes the feasible set: Base provincial capacity margin is `5%`, and minimum system inertia is recorded as `3.5 s reference × 1.0 tolerance = 3.5 s effective`. Model construction and QC share one resolver; legacy scenario overrides may still provide `minimum_system_inertia_seconds`.

Local regression validation is 49/49 PASS. The local 1h engineering gate `outputs/2030_1h_v0722_security_5pct_inertia_3p5s` is `OPTIMAL + solution_qc=PASS` and its result manifest validates. The fixed server remains at accepted checkout `6ed943a`, so every existing server output predates this reliability update. Never reuse an accepted output directory with the new configuration. After an explicit commit/push/deployment decision, first verify an idle clean server checkout, then use a new versioned 24h root and require:

- `model_config_snapshot.json` contains capacity margin `0.05` and the two inertia fields;
- `scenario_manifest.json.security_parameters.minimum_system_inertia_seconds_effective = 3.5`;
- `solution_qc.json.minimum_system_inertia_seconds = 3.5`;
- capacity-margin and inertia hard checks both pass;
- the result manifest closes with no size/SHA256 mismatch.

Do not start fixed-server 744h/8760h or paid cloud 8760h from this local-only state.

## V0722 BECCS carbon-accounting gate

Local commit `c62b769` explicitly closes the CISPO-equivalent BECCS carbon mass balance while retaining the published negative factors, 90% capture assumption and all capture/transport/storage costs. It is not deployed on the fixed server. Before deployment, verify an idle clean checkout and use a new versioned 1h/24h output root; do not reuse any accepted Base/V1 directory.

Acceptance requires the four `solution_qc.json` fields `maximum_beccs_capture_balance_residual_mtco2`, `maximum_beccs_storage_balance_residual_mtco2`, `maximum_beccs_net_carbon_balance_residual_mtco2` and `maximum_captured_co2_reconstruction_residual_mtco2` to pass, plus all six explicit BECCS columns in `annual_resource_accounting_by_province.csv` and a closed result manifest. Baseline lifecycle emissions are zero. A nonzero lifecycle factor is a separate sourced scenario and must not be inserted into Base silently.

## V0722 diagnostic sensitivity suite interface

Local commit `c91828a` adds `scripts/run_cispo_sensitivity_suite.py` as a diagnostic-only wrapper around the existing four-year planning sequence. It does not authorize 8760h and is not deployed on the fixed server; live checkout `6ed943a` remains the accepted Base/V1 model gate. The wrapper gives every scenario an independent state chain, records catalog/config SHA256 values, rejects planned-not-runnable entries and refuses a non-empty root unless `--resume` passes exact suite identity checks.

List or dry-run the implemented scenarios before any solve:

```bash
$PYTHON scripts/run_cispo_sensitivity_suite.py --list-scenarios
$PYTHON scripts/run_cispo_sensitivity_suite.py \
  --diagnostic-hours 24 \
  --output-root /data/zz2/National_model/outputs/sensitivity_suite_24h_<version> \
  --dry-run
```

An actual small gate uses the same command without `--dry-run`; an audit of an accepted root adds `--resume`. Resume must match the mode, diagnostic hours, scenario order, catalog/base-config hashes and each scenario-config hash. The prior suite report is preserved under `sensitivity_suite_history/`, and new timestamped stdout/stderr logs are created rather than overwriting operational evidence. Base must report flexibility disabled, V1 must report V2G disabled, and V2G must remain a separate scenario/root. Do not deploy or start even this small gate until the server is idle and its exact checkout is verified; do not use this wrapper for fixed-server 744h/8760h or paid cloud 8760h.

## V0722 deployed scenario interface

Commit `6ed943a` adds optional, checksummed scenario overrides without changing Base by default and is deployed on the fixed server. The pre-deployment Base 168h gate ran from checkout `b6ca42d`, containing model implementation `0c1eaf2`. Do not mix code versions inside an existing output root.

After deployment, a flexibility gate is selected explicitly:

```bash
$PYTHON scripts/run_cispo_2030_full_year.py \
  --scenario-config config/scenarios/flexible_load_v1.json \
  --diagnostic-hours 24 \
  --output-dir /data/zz2/National_model/outputs/flexible_load_v1_24h_gate
```

Require `scenario_manifest.json`, `flexible_load_dispatch.npz`, `annual_flexible_load_by_province.csv`, `solution_qc=PASS` and a closed result manifest. Full-year Base/V1/V2G estimates are 40.91M/42.54M/43.36M variables respectively; retain the 96 GiB pre-build gate because the static estimate does not bound barrier factor memory.

The fixed-server four-year 168h V1 gate is accepted at `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_flexible_load_v1`. It completed in 1:06:54 with peak RSS 4,040,256 KiB and zero swap; every year is `OPTIMAL + solution_qc=PASS`, every 59-file result manifest validates, maximum daily heating/cooling/EV V1G residual is `8.17e-13 GWh`, and simultaneous up/down counts are zero. Revalidate the immutable chain only with:

```bash
$PYTHON scripts/run_cispo_planning_sequence.py \
  --scenario-config config/scenarios/flexible_load_v1.json \
  --diagnostic-hours 168 \
  --output-root /data/zz2/National_model/outputs/planning_sequence_168h_v0722_flexible_load_v1 \
  --resume
```

Acceptance of `--resume` requires four `RESUMED_ACCEPTED` records, the same `flexible_load_v1` scenario ID/SHA256, closed result manifests and matching `capacity_cohorts_v2` state hashes. Never rerun without `--resume` into these accepted directories. The fixed server remains restricted to small gates; do not launch 744h/8760h there. V2G is an independent optional scenario and must use a new output root.

## V0721 production I/O and acceptance contract

Implementation `0c1eaf2` remains the production I/O/state-acceptance baseline contained by the current fixed-server checkout `6ed943a`. Read `README.md` and `MODEL_IO_CONTRACT.md` before scheduling an expensive case. A case is accepted only when all of the following hold:

- `solve_report.json`: `status=OPTIMAL` and `result_use=SCIENTIFIC_PRODUCTION`;
- `solution_qc.json`: `status=PASS` and every hard check is true;
- `result_manifest.json` validates every scientific output by byte size and SHA256;
- `output_catalog.csv`, `output_data_dictionary.csv`, `model_config_snapshot.json`, `run_environment.json` and `input_manifest.csv` are present;
- the next planning year loads `planning_state/state_metadata.json` and verifies the source solve, source QC, cohort table and transition summary hashes.

Wrapper-owned files such as `run.stdout`, `run.time`, PID and scheduler logs must not be included in the scientific manifest because wrappers can append after model finalization. Preserve them next to the case as operational evidence.

The fixed server is limited to small regression gates for this phase. Use a new versioned output directory for 24h/168h, and do not launch 744h/8760h there. Production 8760h is reserved for the cloud compute node after Gurobi license, data hashes, current regression/smoke checks and 24h/168h solves have passed.

## V0719 capacity-bound/DC-sparse deployment gate

V0719 adds three required data tables and changes the in-memory reverse-flow index. It must be deployed only after the local working tree is committed and the currently active `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` task has completed or been explicitly preserved. Never rebuild the active `model_ready_20260719_sequential_sparse` directory in place.

After the implementation commit is pushed and the server checkout is fast-forwarded, create an additive data version and generate only the three new bound tables:

```bash
OLD_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260719_sequential_sparse
NEW_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260719_v0719_capacity_bounds
test -d "$OLD_DATA_ROOT"
test ! -e "$NEW_DATA_ROOT"
cp -a "$OLD_DATA_ROOT" "$NEW_DATA_ROOT"

cd /data/zz2/National_model/repo
PYTHON=/home/zz2/.local/envs/cispo-2030/bin/python
$PYTHON scripts/build_v0719_capacity_bounds.py --data-root "$NEW_DATA_ROOT"
export CISPO_DATA_ROOT="$NEW_DATA_ROOT"
$PYTHON scripts/smoke_test_data_package.py
$PYTHON -m unittest discover -s tests -q
$PYTHON scripts/check_server_readiness.py --require-raw-grfr --verify-raw-grfr-sha256
```

Acceptance requires 32/32 unit tests, 139/139 data smoke checks and readiness PASS. Confirm the generated national totals before solving:

- nuclear upper 2030/2040/2050/2060 = `110/205/300/300 GW`;
- battery floor 2030 = `65.85 GW`, later exogenous floors = 0;
- `bio+bioccs` shared capacity upper is never below inherited pair capacity; the current expected safeguard is Shanghai in four planning years.

Then run new output directories in order: 24h, 168h and corrected 744h. Each must report zero nuclear floor/upper violation, zero biomass/BECCS shared-capacity violation, zero storage-floor violation, zero AC simultaneous bidirectionality and zero DC reverse flow. Do not launch 8760 before corrected 744h acceptance and the 96 GiB available-memory gate.

## 2026-07-19 deployment note

Implementation commit `1b6da28` supersedes the previously deployed formulation. PID `3778049` completed mathematically `OPTIMAL`, but post-audit rejected it because the former QC did not fail 3,358 material AC bidirectional edge-hours. Do not reuse that result as a solver/model gate.

The corrected server gate `/data/zz2/National_model/outputs/2030_diagnostic_24h_20260719_cispo_flow_alignment_cpu` is `OPTIMAL/QC PASS`: zero AC bidirectional edge-hours, zero DC reverse flow on 363 DC edges and a closed scientific manifest. Server tests passed 26/26. A corrected 744h run is still required.

The updated data root must include `storage/phs_capacity_bounds_by_province_year.csv`. Use `config/model_input_files.json` as the minimal table contract. The code transfer archive must be created from tracked files after the implementation commit; do not package untracked workspace directories.

Production architecture is one continuous LP containing 2030 capacity decisions and all 8760 chronological hours. The 2025 data are boundary conditions only. No Benders decomposition, representative periods, or temporal weights are used.

## Server layout

- Repository: `/data/zz2/National_model/repo`
- Model-ready tables: `/data/zz2/National_model/data/model_ready`
- Capacity factors: `/data/zz2/National_model/data/hourly_cf`
- Hydrology: `/data/zz2/National_model/data/hydro_timeseries`
- Raw 2019 GRFR source: `/data/zz2/National_model/data/grfr_raw_2019`
- Python environment: `/home/zz2/.local/envs/cispo-2030`
- Gurobi Optimizer: `/home/zz2/opt/gurobi1302/linux64`
- Gurobi license: `/home/zz2/gurobi.lic` (mode `600`)
- Environment definition: `/data/zz2/National_model/repo/env/cispo-server.yml`
- Outputs: `/data/zz2/National_model/outputs`
- Logs and manifests: `/data/zz2/National_model/logs`, `/data/zz2/National_model/manifests`

The `/data` filesystem is NTFS/fuseblk and does not enforce normal Unix ownership or mode bits. Do not store SSH keys or `gurobi.lic` there.

Current versioned model and hydropower data:

```bash
export CISPO_CF_ROOT=/data/zz2/National_model/data/hourly_cf
export CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260719_v0719_capacity_bounds
export CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse
export CISPO_RAW_GRFR_ROOT=/data/zz2/National_model/data/grfr_raw_2019
```

The versioned data roots remain current. Fixed-server HEAD `b40900a` passes 34 regression tests, 139 smoke checks and the V0720 24h I/O-contract gate. Do not schedule another 744h run on this host.

## Long-term Git synchronization

- Bare remote: `/home/zz2/git/National_model.git`
- Local `origin`: `ssh://national-model-server/home/zz2/git/National_model.git`
- Active branch: `codex/cispo-2030-full-lp`

Normal local-to-server workflow:

```bash
# Local workstation
git pull --ff-only
git push origin codex/cispo-2030-full-lp

# Server working copy
cd /home/zz2/National_model_server/repo
git pull --ff-only
```

If code is edited on the server, commit and push it before pulling locally. Model data, capacity-factor Zarr stores, hydrology, outputs, licenses and environments remain outside Git.

## Environment and data gates

```bash
export CISPO_CF_ROOT=/data/zz2/National_model/data/hourly_cf
export CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse
export CISPO_RAW_GRFR_ROOT=/data/zz2/National_model/data/grfr_raw_2019
export CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260719_v0719_capacity_bounds
PYTHON=/home/zz2/.local/envs/cispo-2030/bin/python
$PYTHON scripts/check_server_readiness.py --require-raw-grfr --verify-raw-grfr-sha256
$PYTHON scripts/preflight_cispo_2030.py --output /data/zz2/National_model/outputs/preflight_2030.json
```

For the pending cascade version, the model-ready data root must include:

- `hydro/cascade_topology_nodes.csv`
- `hydro/cascade_topology_edges.csv`

The readiness gate now reports cascade node/edge counts, low-correlation lag edges, max-bound lag edges and maximum travel lag. A valid cascade server bundle should report 142 nodes, 124 edges, 4 low-correlation lag warnings, 18 max-bound lag warnings and no missing required cascade columns.

The server uses Gurobi Optimizer and `gurobipy` 13.0.2. Store the license file under the protected home directory, not `/data`. Do not commit the license file or activation key.

```bash
export GUROBI_HOME=/home/zz2/opt/gurobi1302/linux64
export PATH="$GUROBI_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$GUROBI_HOME/lib:${LD_LIBRARY_PATH:-}"
chmod 600 /home/zz2/gurobi.lic
$PYTHON scripts/check_gurobi_full_license.py
```

The license gate deliberately solves an LP with 2,501 variables. A size-limited fallback license must fail this check; package import or a two-variable solve is not sufficient evidence for production readiness.

Install test-only dependencies with `$PYTHON -m pip install -r requirements-test.txt`, then run `$PYTHON -m pytest -q`. The production dependency file intentionally excludes `pytest`.

As verified on 2026-07-06, direct server access to PyPI fails certificate-chain validation. Do not bypass TLS with `--trusted-host` or disabled verification. Download Linux/Python 3.11 wheels on a trusted workstation, record SHA256 hashes, upload them, and install with `--no-index --find-links=<wheel-directory>` until the institutional CA chain is repaired.

## Selectable optimization horizons

| Horizon | Hours | Intended use | Minimum available RAM |
|---|---:|---|---:|
| `one_month` | 744 | Local code/solver test only | 8 GiB |
| `six_months` | 4344 | Large integration test only | 32 GiB |
| `full_year` | 8760 | Production scientific run/build gate | 96 GiB |

The truncated horizons use the leading hours and a cyclic boundary over the selected interval. Annual investment costs, carbon limits and biomass limits are not rescaled. Their solutions therefore must not be interpreted as planning results.

Preflight without requiring Gurobi:

```bash
$PYTHON scripts/run_cispo_2030_full_year.py --horizon one_month --preflight-only
```

## Current 744h cascade gate

The active corrected gate is:

```bash
OUT=/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict
PID=$(cat "$OUT/run.pid")
ps -p "$PID" -o pid,etime,%mem,%cpu,rss,vsz,stat,cmd
pgrep -P "$PID" -a
tail -n 100 "$OUT/gurobi.log"
ls -lh "$OUT/build_report.json" "$OUT/solve_report.json" "$OUT/solution_qc.json" 2>/dev/null
```

It was launched from implementation `5a9f4ab` after the strict 168h gate reached `OPTIMAL/QC PASS`. At launch `/usr/bin/time` PID was `3344086`, Python child PID was `3344087`, and about 116 GiB RAM was available. Do not infer completion from PID exit alone; require both reports and inspect QC.

The old output below is a preserved failed numerical baseline and must not be reused:

```bash
OUT=/data/zz2/National_model/outputs/2030_one_month_hydro_cascade
PID=$(cat "$OUT/run.pid")
ps -p "$PID" -o pid,etime,%mem,%cpu,rss,vsz,stat,cmd
tail -n 100 "$OUT/gurobi.log"
ls -lh "$OUT/solve_report.json" "$OUT/solution_qc.json" 2>/dev/null
```

PID `244035` was normally interrupted on 2026-07-07 after `37,576.53 s`; it produced no solution. Do not delete this directory.

The following completed output is a preserved rejected baseline:

```bash
OUT=/data/zz2/National_model/outputs/2030_one_month_20260719_sequential_sparse_cpu
PID=$(cat "$OUT/run.pid")
ps -p "$PID" -o pid,etime,%mem,%cpu,rss,vsz,stat,cmd
tail -n 100 "$OUT/gurobi.log"
ls -lh "$OUT/solve_report.json" "$OUT/solution_qc.json" 2>/dev/null
```

Its former `solution_qc=PASS` is insufficient. Acceptance now additionally requires zero AC bidirectional edge-hours above `1e-6 GW`, zero DC reverse flow, closed load-center net exchange and a closed result manifest. CISPO's `0.001 yuan/kWh` flow penalty is configured as `1 yuan/MWh`; DC corridors have reverse UB zero, while AC corridors retain the S4-56 shared-capacity constraint.

Before launching the corrected 744h gate, require at least 64 GiB available RAM and verify that swap/shared jobs no longer leave the host under pressure. The rejected 744h reached 22.141 GiB peak process-tree RSS despite a lower preflight estimate.

Do not set `Crossover=0` for acceptance: the option was retested on the current corrected model and returned `SUBOPTIMAL`, maximum constraint violation 0.01355 and failed reservoir/directionality QC. `Threads=-1` exposes all 96 logical processors; Gurobi barrier uses the 48 physical cores. GPU-enabled Gurobi is installed only in `/home/zz2/.local/envs/cispo-gurobi-gpu`; it confirmed `Start PDHG on GPU`, but the same 24h P30 model was still iterating after about 600 s and was interrupted. CPU barrier remains the default route.

A diagnostic candidate using `FeasibilityTol=OptimalityTol=1e-6`, `BarConvTol=1e-7` and `Crossover=1` passed the current 24h QC in 37.38 s, about 7% faster than the strict local baseline. Do not promote it from 24h evidence: Gurobi warns that looser barrier termination can prolong crossover. Compare it at corrected 168h/744h and retain only if objective, capacity decisions and every hard QC remain acceptable.

`NodefileStart` does not solve this model's memory problem because this is an LP without branch-and-bound nodes. For normal production solves, benchmark default `DualReductions`/`InfUnbdInfo` behavior; use `DualReductions=0`, `InfUnbdInfo=1` and homogeneous-barrier diagnostics only after an infeasible-or-unbounded status. See `MODEL_SOLVABILITY_AUDIT_20260719.md` for the parameter matrix.

## Full model

The revised current-code projection is about 44.09 million variables, 68.19 million constraints and 515-524 million nonzeros. The old 744h factorization already used about 10 GB for factor nonzeros; linear extrapolation is about 118 GB for this component alone. Require at least 96 GiB available RAM for build-only, and do not optimize immediately after a successful build.

Build without optimizing:

```bash
$PYTHON scripts/run_cispo_2030_full_year.py --horizon full_year --build-only --output-dir /data/zz2/National_model/outputs/2030_full_year_build
```

Solve:

```bash
$PYTHON scripts/run_cispo_2030_full_year.py --horizon full_year --output-dir /data/zz2/National_model/outputs/2030_full_year
```

The runtime gate refuses to build when available memory is below the checked-in 96 GiB threshold. This is a build scheduling gate, not proof that barrier factorization fits. For infeasibility, the solve path writes `iis.ilp`; production constraints are not silently relaxed.

Successful solves additionally write `solution_qc.json`, compressed hourly province balances, technology dispatch arrays, station-indexed reservoir dispatch, transmission flows, annual carbon/CCS accounts and objective cost decomposition. A solution is not accepted as production output unless `solution_qc.json` reports `PASS`.

## Sequential 2030-2060 production path

After the revised 744h gate and 8760 build-only gate pass, run a single year as:

```bash
$PYTHON scripts/run_cispo_2030_full_year.py \
  --planning-year 2030 \
  --horizon full_year \
  --output-dir /data/zz2/National_model/outputs/planning_sequence/2030
```

Only `OPTIMAL + solution_qc PASS` full-year runs write `planning_state/`. The isolated sequential driver releases each year's process memory before the next year:

```bash
$PYTHON scripts/run_cispo_planning_sequence.py \
  --output-root /data/zz2/National_model/outputs/planning_sequence
```

Resume only already accepted years:

```bash
$PYTHON scripts/run_cispo_planning_sequence.py \
  --output-root /data/zz2/National_model/outputs/planning_sequence \
  --resume
```

The driver stops at the first non-optimal/QC-failed year. Do not manually copy an unchecked state directory or bypass its SHA256/year-boundary validation.
