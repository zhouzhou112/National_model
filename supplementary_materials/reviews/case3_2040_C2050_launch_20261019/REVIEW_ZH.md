# case3 2040 / C2050 放行记录（2026-10-19）

作者本轮已采纳 case3 2030 筛选解的 `planning_state_candidate` 作为 2040 上游，并明确授权各自门禁全部通过后提交并 release。所有原始与失败运行完整保留。云端 release 日期按服务器北京时间记为 20261020。

## 2026-10-19：证书与 nocredit

Claude 已完成证书，本轮只核对原件与下载身份：MPS、BarPi、归档 manifest 与 checkpoint manifest SHA 全部一致；未重复计算。B = 347.7820678689325 million CNY，B/obj = 8.304198762899926e-5，近优性 ACCEPT，比较用途 INTERVAL_WITH_B，3 个负价列，无需重解。成本节省区间 [44.46, 64.32] 亿元/年。

Job5153901 已 release，m4cg1604 RUNNING；AllocTRES cpu64/mem750G/billing64，UNLIMITED，no-requeue，启动可用内存 722.5721397399902 GiB，compute-node smoke PASS。证据 nocredit_status_2340.json。

## 2026-10-19：case3 2040 本机门禁

R1_case3_2040_02 由作者采纳的 case3 2030 状态生成，原状态不变。R1 小 cohort 清理：发电/储能 0.110375271902 GW、网络 0.100047035246 GW；bound-close 共 1.2916579760304837e-7 GW。储能删除按实际值披露，电池 0.0015153965075182787、抽蓄 0.0028088653416721999 GW。未改变 R1 算法。

筛选/不筛选 1h 仅 BOUNDS_VRE_NEW 段不同；GW 容量列微小余量 0 列；数值清理逐列审计在 final_gates.json 中。2040 参数核准 PASS。

24h 为 TEST_ONLY：107 轮 OPTIMAL、48.007 秒，M=1.0428117347416332e-7 GWh；容量信用越界 0，relative_v1 块存在，保全 COMPLETE/errors=[]，原模型、BarX/BarPi、candidate_selection 均保全。严格 HARD_FAIL 参考标签保留，不用于外推规划结论。

17 项回归通过：原生产筛选与身份、R1/6c、正式启动导出分支，以及新增续接 profile 与 C2050 跨情景入口约束。两个 profile 数值逐键与原 Aggregate=0 profile 相同，只改 ID 与清单来源。

## 入口实现与保全说明

C2050 新增显式 --late-entry-base-state，仅允许 case3 2050 / Base2040 边界、已正式验收的 Base2040、完成 R1 的派生状态。核对验收文件 SHA、原 solve/QC/run_identity SHA；普通接续仍要求情景一致，PlanningState 原完整性校验保持。

保留构建前失败：R1_case3_2040_01 缺 CISPO_WAVE_ROOT；case3_2040_screen_1h_01 为本机 CRLF 与冻结 LF 的字节 SHA 差异，已证实 LF 字节相同后使用独立 LF 副本；unscreen_1h_01 缺诊断工程标识。未放宽完整性验证或覆盖任何失败目录。实际通过门禁见 case3_2040_final_gates.json。

C2050 的 R1 与筛选版 1h 已通过，后续门禁、冻结与提交回执在完成后追加。未建立后台监听，不触碰 Job5124127、既有冻结源码或 cloud_backup。


## 2026-10-19 23:43：case3 2040 云端 preflight 阻塞

case3 2040 本机门禁全部 PASS；冻结 release `20261020_case3_2040_v9a12_screen0p2_agg0_t48_m750_tol1e4_v1`，源码 `681627fbee627ab1703d72367e4c0e7cf1286848`。随后云端 preflight 报 `Required provenance inputs are missing: thermal/retirement_schedule.csv`。原打包清单沿用 2030，未列入续接所需证据输入，这是本轮打包遗漏，不是数值不收敛。

按任务书第 6 节停止该作业放行：没有 sbatch，Job ID 为空，冻结包及失败输出完整保全，未补写任何冻结文件。修复后必须建立新 release 并通过云端 preflight，不能直接启动当前包。C2050 尚未冻结，不受该作业阻塞；为其新包补全了与本机门禁 manifest 一致的 thermal/existing_capacity_2025.csv、thermal/retirement_schedule.csv、hydro/grfr_monthly_p30_single_year_proxy_2019.nc，并逐 SHA 校验其全部必需 data 输入。


## 2026-10-19 23:45：C2050 门禁完成

Base2040 → R1_C2050_01 → v9_a12 → Base2050 清单 margin0.2 → Aggregate0；框架 C，scenario 仍为 case3_thermal_ev_v5。两版 1h 仅 BOUNDS_VRE_NEW 段不同，容量列微小余量 0，2050 参数核准全部 PASS。24h：OPTIMAL，96 轮、43.75 秒，M=1.969660003986462e-7 GWh，容量信用越界 0，relative_v1 PASS，保全 COMPLETE，错误为空。完整门禁为 C2050_final_gates.json。短窗仅作工程验证。


## 2026-10-19 23:45：C2050 已提交并 release

云端 preflight PASS，提交后先核验 held 的资源请求与冻结文件 SHA，再按本轮授权 release Job5201262。释放时 PENDING，尚无节点分配；AllocTRES 与启动内存须以计算节点回执为准。资源请求 cpu64/mem750G/billing64、UNLIMITED、no-requeue。

|作业|release|源码 commit|源码 manifest SHA256|release manifest SHA256|
|---|---|---|---|---|
|case3 2040（未提交）|20261020_case3_2040_v9a12_screen0p2_agg0_t48_m750_tol1e4_v1|681627fbee627ab1703d72367e4c0e7cf1286848|c8ea0394405ed8492ab58ca300da9de0e179b600aa6f293f31fce3f5b3b27b37|b9f65e7f0bc9e8b5d26033f3afe6e29640cb9e33dfd1194fd61579dbb8e38d07|
|C2050 / 5201262|20261020_lateentry_2050_v9a12_screen0p2_agg0_t48_m750_tol1e4_v1|f6372ff43e043cd91e43f8f998020b508226e7b0|5fd0370caf9dd89e78fb8ac216b59aca6df6dcea1fe0c30b5b95856d71333fca|c3b534aa6555aca3c2012956b7bff38bce203e775f3f4c3334def19a44431a84|

两包均在 `/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/` 下。病例身份均为 case3_thermal_ev_v5；C 包 launch_config.json 明确 `framework=C_Late-entry`。本地完整原始门禁输出、两次 R1 源与派生状态、失败包、MPS/解/checkpoint/日志保留；Git 只收小证据。PARAMETERS_ZH.md 给出实际逐项参数核准表。


## 最终启动核验：2026-10-20T06:46:02.396615+08:00

|作业|Job ID|节点|状态|启动可用内存 GiB|
|---|---|---|---|---|
|_nocredit 2030|5153901|m4cg1604|RUNNING|722.572140|
|case3 2040|未提交|—|云端preflight阻塞|—|
|C2050|5201262|m4cg1606|RUNNING|723.370480|

两个运行作业 AllocTRES 均为 cpu64/mem750G/billing64，UNLIMITED/no-requeue，计算节点smoke及7项启动回归均PASS，stderr为空。final_job_status.json的smoke/runtime小文件已按远端SHA核验。之后仅按作者请求只读查询，无后台监听。

2040的停止来自任务书第6节明确要求，属于输入打包问题；本机数值门禁并未失败。建议后续以包含58项已核对输入的新release修复并重新preflight，不能修改当前冻结失败包。

## 2026-10-20：case3 2040 v2 打包修复与放行

依据作者本轮明确授权，只修复输入打包；生产代码、profile、batch、筛选清单、R1 状态不改。保留此前 v1 失败记录，不覆盖旧结论。

|输入|v1 情况|补齐 SHA256|
|---|---|---|
|hydro/grfr_monthly_p30_single_year_proxy_2019.nc|实体缺失且清单遗漏|c28f628642baaaac18d4461ac9474b3d622fcd80fbcd651884e6095d58203767|
|thermal/existing_capacity_2025.csv|实体存在且 SHA 正确，清单遗漏|60088ff3b1375cba6de943acc09bac4c8dd363e32bbe6ff692321a93906ae374|
|thermal/retirement_schedule.csv|实体缺失且清单遗漏|2f463d6e3e0b754e70ead27e158c218c2bef06b06f555720a973fc4d4bd64def|

补齐来源均为已核验 C2050 release `20261020_lateentry_2050_v9a12_screen0p2_agg0_t48_m750_tol1e4_v1/data_overlay/` 下的同名文件；复制至 v2 自有 additional_data，并写入其 data_overlay 与 58 项 SHA 清单。逐项核对 v1：3 项清单遗漏、2 项实体缺失、其余无 SHA 差异。58 项均与本地文件核验相符，云端实际使用的 74 项必需逻辑输入与本机 24h 门禁 manifest 逐 SHA 一致。

水文月流量在 manifest 中的逻辑标识为 monthly_environmental_flow_2019_p30。云端通过既有环境路径读取的同名水文数据与补齐副本、本地门禁文件 SHA 完全一致。首轮附加检查误将物理文件路径作为逻辑标识，读取已生成 manifest 后核验消除；没有重新运行 preflight、替换数据或放宽 SHA 要求。

源码严格沿用 `681627fbee627ab1703d72367e4c0e7cf1286848`。395 个源码文件与该提交 git archive 字节逐项相同（不是将受换行属性影响的 git show blob 代替归档字节）。源码、状态、batch、旧门禁共 409 项与 v1 字节一致。本机 1h/24h/参数核准继续引用原 PASS 证据，未重算。v1 的 424 个原有文件 SHA、大小、mtime 在新包建立前后均一致。

**新 release**：`20261020_case3_2040_v9a12_screen0p2_agg0_t48_m750_tol1e4_v2`；根 `/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/`。

- source manifest SHA256：`c8ea0394405ed8492ab58ca300da9de0e179b600aa6f293f31fce3f5b3b27b37`。
- release manifest SHA256：`b1a07cb8bb062943dfc543e788eef830667a157e093a2016d1c3605508829283`。
- data manifest SHA256：`18dd2be1d90f669dd0547567c28c73ad2d0d6ebade1f3560ae720deced5110aa`。

云端 preflight 一次执行 PASS，完整 manifest 核验 PASS；随后 sbatch --test-only、held 资源核验、冻结文件校验均通过，已按授权 release **Job5201318**。请求 cpu64/mem750G/billing64、UNLIMITED/no-requeue；节点与启动内存见本节后续追加的启动回执。

证据目录 deployment_case3_2040_v2/：input_comparison.json、local_manifest_check.json、source_identity_check.json、frozen_release.json、cloud_preflight.json、cloud_manifest_check.json、released.json。所有操作命令和原始输出本地保留。没有修改或控制 Job5124127/5153901/5201262，没有后台监听。

### v2 启动核验（2026-10-20T07:01:20.005150+08:00）

Job **5201318**：**RUNNING / m4cm1803**。AllocTRES=`cpu=64,mem=750G,node=1,billing=64`，TimeLimit=UNLIMITED，Requeue=0；启动可用内存 **725.0457878112793 GiB ≥ 700 GiB**，Gurobi13.0.2 smoke PASS，7项正式启动回归PASS，stderr为空。启动小证据已按远端SHA核验，见 deployment_case3_2040_v2/startup_status.json。

作业启动后再核验v1的424个文件SHA与mtime全部不变；v1及其失败输出继续保留。源码未修改，无本机重复构建或求解。后续仅按作者要求查询，不建立后台监听。

## 2026-10-20：C2050 OOM 原因只读核验

Job5201262 在英国 04:08:53（北京 11:08:53）结束，总时长 4:23:41，Slurm 为 OUT_OF_MEMORY，slurmstepd 明确记录 1 次 oom_kill；进程收到 signal 9，batch_exit=137。不是输入遗漏、时限结束或已确认的数值不收敛。实际分配 cpu64/mem750G/billing64，48 求解线程、Aggregate=0，TimeLimit/SoftMemLimit/MemLimit 均无限制，启动可用内存 723.370480 GiB。

Presolve 完成于 10759.10 秒；日志停在 ordering 2005 秒，尚无 Barrier 迭代、Factor NZ 或有限解导出。Slurm MaxRSS=754822880 KiB（719.855194 GiB），/usr/bin/time 进程峰 RSS=758469272 KiB（723.332664 GiB）。二者不是同一采集口径，也不是节点总占用；低于申请 750G 不能否定明确的 OOM 事件。当前没有终止时的 cgroup memory peak 或内核日志，不能断言具体由瞬时峰值、cgroup 额外记账还是节点全局内存压力触发，也没有证据归因其他用户抢占。

|模型|预处理后行|预处理后列|预处理后非零元|Factor NZ|
|---|---:|---:|---:|---:|
|Base2050|37,121,156|33,702,564|401,075,371|3.519e10|
|case3 2030|43,068,079|38,292,964|327,279,521|2.657e10|
|C2050|43,055,074|38,303,957|396,546,740|未输出|

C2050 相对 case3 2030 行列规模近似，但非零元增加 21.16%；相对 Base2050 行数增加 15.99%、列数增加 13.65%。排序/分解内存依赖矩阵结构和填充，不能按非零元或时间窗口线性预测。数据支持“在排序阶段耗尽可用资源”；更具体的填充规模与 Aggregate=0 的独立贡献未被测定，不能单独归因关闭聚合。2030 成功及 744h 内存近似不变均不构成 C2050 全年峰值上界。启动 ≥700 GiB 是启动门禁，不是峰值容量保证；原资源估计没有覆盖此次全年排序需求。

原 MPS 4,145,869,333 字节，归档 manifest 标记 COMPLETE，SHA256=92deb32f13289e2f77ed6d0f4a93133f8e6ee701be7d039a81738dbce2bc2e38；本轮只核对 manifest 与文件存在/大小，没有重新散列 4.15GB 原件。没有 solve_report、solution_qc 或 preservation_report，不将“已有文件全部保留”误写为“完整解已导出”；硬杀前尚无解可保全。

证据在 C2050_oom_20261020/；9 份原始小文件逐字节 SHA 验证，evidence.json 含 sacct、文件目录和历史模型日志摘要/SHA。失败 release 与全部现存输出未修改；没有重启、改参数或新作业。建议下一步先核实可用大内存队列及资源上限，优先维持已核准数值设置；若资源不足，再把降低 Threads 作为需作者核准的独立工程方案，不能保证降线程即可解决。

解释依据：[Gurobi Barrier 日志说明](https://docs.gurobi.com/projects/optimizer/en/current/concepts/logging/barrier.html)、[Gurobi 线程与内存说明](https://support.gurobi.com/hc/en-us/articles/42058344459409-Managing-Threads-and-Memory-Usage-in-Gurobi)、[Slurm sacct 口径](https://slurm.schedmd.com/sacct.html)。Git 基准 908bdfb；本轮仅报告、交接与小证据，生产源码不改。

### 2026-10-20：筛选生效与 Base2050/2060 规模比较补充

作者追问“既然筛选，为何比未筛选 Base 更耗内存”。冻结源码 apply_vre_screen 与云端 build_report 核对：margin=0.2、enabled=true，36,686 个站点中原可扩建35,383，固定6,195个 vre_new 上界为零（17.5084%），保留29,188个可扩建站点。源清单SHA a55a93738a37c0cf51ef84b73f1e34177cfd7f26a040df146e0c83462190d528。筛选没有漏启。实现只改新建容量上界，不直接删除站点及其既有容量、逐时运行变量；固定变量带来的进一步消元交由Presolve完成，不能按“筛掉站点比例”同比缩减整个LP。

原始模型 Base2050/2060 为50,907,233行、41,458,383列；C2050 为54,217,741行、43,761,732列。C2050包含柔性模块，且Aggregate=0，Base生产设置Aggregate=1。这同时涉及模型结构、年度输入和求解预处理差异，不是相同LP只加筛选的受控对照。

|预处理后模型|行数|列数|非零元|
|---|---:|---:|---:|
|Base2050|37,121,156|33,702,564|401,075,371|
|Base2060|36,153,597|33,095,602|387,670,134|
|C2050（已筛选）|43,055,074|38,303,957|396,546,740|

C2050比Base2050行多15.99%、列多13.65%，虽然非零元少1.13%；比Base2060行多19.09%、列多15.74%、非零元多2.29%。因此不能说C2050整体规模小于两者。特别更正解释侧重点：前节“相对case32030非零元增加21.16%”不是对“相对Base2050为何OOM”的充分解释；后者需要同时看行列维度、排序连接结构、填充和并存工作空间。Base2050/2060成功日志FactorNZ分别3.519e10/3.376e10；C2050排序未完成，无可比较FactorNZ，不能断言其因子一定更大，也不能把全部内存增量归因Aggregate=0。

新证据C2050_oom_20261020/screening_comparison.json保存冻结筛选函数、报告SHA/计数及既有Base2060日志证据SHA。无新求解、无运行干预；数据不支持直接撤销Aggregate=0或认定筛选失效。

## 2026-10-20：64计费核资源上限、线程建议与R1实际部署复核

只读 scontrol show partition/node、sinfo、sacctmgr normal 及已结束作业的实际分配。m4cg1606 的 RealMemory=768000 MiB，即750 GiB；CfgTRES mem=750G。Job5201262已实际获得cpu64/mem750G/billing64，因此当前节点在64计费核条件下可确认的最大申请量就是750G，没有再增加到800G的空间。队列名称中的768不能理解成可申请768 GiB；可见分区节点最大也为768000 MiB，没有发现1TiB节点，其他站点/产品与平台额外资费未核实。MaxMemPerCPU=6144属于每CPU申请口径，不能据此否认已实际分配的节点级--mem=750G；不能把改用--mem-per-cpu当成同一请求。保持Slurm申请64CPU，仅将Gurobi Threads改为32或24，不会因求解线程减少而自动减少该作业的billing=64；未来新作业仍应回读AllocTRES。

48线程的失败记录是被OOM截断的记录，723.333GiB只是已达到的进程峰值，无完整排序峰值或上界。作为低置信的资源预算启发式，以历史Base2050/2060的Slurm峰685.98/657.34GiB乘C2050与对应模型的预处理行数比或列数比，得到760.8–795.6GiB；这不是同LP回归，也不是排序峰值测量。可暂按约800GiB量级、800–850GiB资源预算考虑，850并非预测上界或置信区间，不能据此承诺够用。现节点无法满足该预算。

建议优先验证32线程，24线程为更保守备选，44或40线程减幅较小。不能按48→32就把全部RSS乘2/3：共享模型和部分分解内存不随线程线性减少。下面仅演示敏感性，未拟合真实线程内存函数：假设M48=800GiB，其中与线程无关比例f=60%–80%，M(T)=800×[f+(1−f)T/48]，则40线程为747–773GiB，32线程为693–747GiB，24线程为640–720GiB。假设本身未经实测，因此32/24都不能登记为内存安全。建议独立、带资源保护的同LP32线程排序与早期Barrier验证，以全过程RSS约680–690GiB作为留余量的工程目标；不足再评估24，不在本轮执行。纯理想并行部分48→32/24对应1.5/2倍耗时，仅算术参照，不能作为总耗时预测；实际排序、内存带宽和NUMA可能改变结果。依据Gurobi官方线程/内存说明，不能套用MIP每线程完整模型副本解释本连续LP。

**R1已在云端实际生效，不只是本机配置通过。** 本机R1派生状态与云端upstream_state的state_metadata、capacity_cohorts、bound_closure_audit三项SHA全部一致；源状态明确planning_year=2040、source_scenario_id=base、next_planning_year=2050，规则AUTHOR_R1_20261014、applied=true、PASS。新建小cohort按站点/省×技术合计<1MW处理，保留存续retrofit_out保护组；发电/储能删除0.305373549492GW，网络删除0.270692245308GW，保留组28行负尾差置零增加5.932754287841e-15GW。bound-close另收口0.000307977870GW（0.307978MW）。原Base2040档案未改。

云端全年model_config_snapshot实际值：A1/A2=1e-5GW，other_capacity_headroom_zero_gw_gwh=1e-5，capacity_cancellation_rhs_zero=1e-12，A3=0。全年build_report记录82处水电余量清理，总5.507630244196e-5GW（55.0763kW）；改造余量清理总2.220446049250e-16GW；other容量清理列表为空，RHS清理无命中记录，不代表开关漏启。1h/24h门禁均PASS，24h OPTIMAL、冷热M=1.969660003986462e-7GWh。Base2050使用旧R0，C2050已使用与Base2060同类R1；不能将Base2050长耗时全部因果归于旧交接，也不能将R1当全年收敛保证。当前C2050在排序时OOM，尚未出现Barrier数值迭代，未发现“漏做R1导致数值不稳”的证据。

证据C2050_resources_R1_20261020/evidence.json、additional_partitions.json及summary.json；完整只读原件本地保留，Git收摘要与SHA。第一次合并两个partition参数的只读命令被scontrol拒绝，后续分开查询成功；未提交任何测试/生产作业。推荐仅供作者核准，不改变Aggregate0、48线程冻结配置或既有release。Git基准b08d0b3。

## 2026-10-20：作者授权40线程重跑；启动许可过期阻塞

本节取代此前“32线程建议、未授权重跑”的当前状态，不改写历史诊断。作者明确要求以40线程启动C2050；本轮已完成新release冻结、提交并release。Job **5206992** 于北京时间19:47:31（英国12:47:31）在 **m4cm1607** 启动，4秒后 **FAILED / ExitCode 1:0**。报错为 `gurobipy.GurobiError: License 2847107 has expired`，发生在计算节点 `gp.Env.start()`；尚未构建全年模型、未进入排序或Barrier，也无有限解。这不是40线程内存试验失败，不能据此评价40线程峰值可行性。

|项目|核验结果|
|---|---|
|源码|f75a330fa5977562c14979dcdcbba861d2dbe1e7；396个repo文件逐SHA一致|
|新release|20261020_lateentry_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v1|
|资源|实际 AllocTRES cpu=64, mem=750G, billing=64；UNLIMITED、no-requeue|
|求解设置|Threads=40、Aggregate=0、Presolve=2、NumericFocus=2、Crossover=0、BarConvTol=1e-4；TimeLimit/SoftMemLimit保持原设置|
|输入与续接|Base2040→R1及v9_a12不变；margin0.2清单SHA不变；58项数据SHA通过|
|云端preflight|一次PASS；79项必需记录=74项非配置输入+5项配置，78项SHA不变，仅40线程profile改变|
|本机门禁|1h/24h参数PASS；两个窗口的MPS全部分段SHA与原48线程profile门禁模型一致；24h OPTIMAL，M=2.198072843739851e-7 GW/GWh，保全COMPLETE/errors=[]|
|回归|production_screen 6/6、numeric_repaired_formal_launch 7/7 PASS|
|启动可用内存|≥700GiB检查已通过后才进入许可测试；未保存精确GiB值，不能用分配量代替实测值|
|计算节点完整smoke|FAIL：许可过期；startup_regression及全年runner尚未执行|

源码改动仅注册并校验C2050专用40线程profile；原runner与物理构建模块保持原版本。新batch同步设置OMP/OPENBLAS/MKL为40，Slurm仍申请64CPU。原48线程OOM包5201262及其输出只读保留；新40线程失败包也完整保留，未原地修补、重复提交、自动降线程或建立后台监听。没有操作5124127、5153901、5201318或T550 cloud_backup。

本机初次24h门禁调用旧Gurobi12被版本检查拦截（求解前），原输出C2050_t40_24h_01保留；切换现有output/portfolio_runtime_gurobi13后新目录C2050_t40_24h_02通过。云端数据preflight不申请Gurobi环境，因此不能发现计算节点许可证过期；这次许可错误由启动smoke正确阻断，不绕过门禁。

证据在deployment_C2050_t40/：gates.json、local_evidence_sha256.json、frozen_release.json、cloud_preflight.json、held_submission.json、release_receipt.json、startup_status.json、terminal_evidence.json及terminal_files/。终态4份小文件远端SHA与本地逐字节核验；全部大模型/本机门禁完整输出留在原目录。release manifest SHA256为 `1ce60bf0c9e771df428bf4b968e18efc68973ce8261f26d1627d29b16c861bd6`，源码manifest SHA256为 `8f9f2ccdef0e3b77b77e3a64ed7ee21ea1c5ac5281e607bd002afa8c741f301b`。

下一步需要作者恢复已配置云端Gurobi许可后通知；不读取、复制或上传凭据。之后先核验许可，再以新运行身份继续40线程方案，保留此次失败现场。40线程能否跨过排序峰值，以及后续是否约400GiB，都仍待实测；不更改物理参数，不把短窗通过外推为全年内存保证。

## 2026-10-20：作者提供新WLS；40线程C2050恢复运行

作者明确提供`D:/gurobi1/gurobi.lic`并要求使用，授权本次指定许可的安全迁移与验证；不扩展为读取其他凭据的授权。新许可在本机Gurobi13.0.2、云端登录节点、实际计算节点均通过2501变量LP（OPTIMAL/objective=1），证明不落入小规模受限许可。许可内容未打印、未入Git、未放进release或证据包；仅记录路径及SHA256。云端独立目录权限700、文件600，逐字节SHA一致：`f5e565f53eda9ed785c92b262e0efc9366ae2773e733de1521ef79c500150e5c`。原许可文件、全局环境和其他运行作业不修改。

新release：`20261020_lateentry_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2`，源码提交`d385fa781c3f1f4922e40d91e1a1fad046c9a260`。新batch从launch_config读取专用许可路径并在启动前验证SHA，完整smoke使用2501变量；运行前精确可用内存单独保存startup_memory.json。新包的396项repo文件SHA与40线程v1完全相同；物理模型、R1、margin0.2、Aggregate0、Threads40及其他求解参数未改。复用已通过1h/24h门禁，不重复求解；新batch的bash语法和内嵌Python编译检查通过。

云端preflight一次PASS；58项数据SHA、79项必需输入身份通过。新作业 **5207165** 已按既有40线程启动授权提交并release，北京时间 **20:24:47**（英国13:24:47）在 **m4cm1607** 启动，核验为 **RUNNING**。实际AllocTRES `cpu64/mem750G/billing64`、UNLIMITED、no-requeue；启动可用内存 **722.968513 GiB**，超过700GiB门槛。计算节点Gurobi13.0.2新WLS测试PASS，7项启动回归PASS，output_8760已创建、stderr为空，全年流程已开始；尚无排序峰值或收敛结论。

启动回归保留一条`numpy.ndarray size changed` RuntimeWarning，7项测试均通过；不隐去警告，不将其写成求解失败。原始启动日志本地/云端保留，Git仅收录必要摘要与SHA。许可元数据及两侧测试见deployment_C2050_t40/license_*.json；新freeze/preflight/提交/启动证据见deployment_C2050_t40_wls_v2/，startup_verified.json列出精确资源和日志SHA。

release manifest SHA256：`0925676b1538b7cbc11d72e4e6aab7e83fb5b343d8349af2e631510f72906acf`；源码manifest SHA256：`971fc67b9ff234514aa5515118130b395dbf5aaf95bce1419e32ca9e171d78ce`。5201262的OOM包与5206992的许可失败包完整保留，新作业使用独立输出。没有建立后台监听或自动提交，没有操作其他作业/T550 cloud_backup。下一步按作者要求只读核验40线程排序峰值与Barrier进展；不承诺峰后固定400GiB，不自动换线程或追加作业。

## 2026-10-20 21:01北京：其他运行作业的许可影响核验

作者询问旧许可过期是否影响既有求解。UTC13:01:56只读查询三个已知作业并检查stdout、Gurobi日志、stderr和Slurm stderr，均RUNNING；没有重新创建Gurobi环境、换许可、控制进程或改冻结包。证据cloud_joint_progress_20261016/license_impact_20261020T130159Z.json记录状态、日志SHA与最近三轮。

|作业|Job ID / 节点|最新迭代与日志时间（北京）|许可错误|
|---|---|---|---|
|nocredit2030|5153901 / m4cg1604|51轮，20:54:14；此前核验43轮|未发现；两份stderr均空|
|case3 2040|5201318 / m4cm1803|30轮，20:57:07；此前核验23轮|未发现；两份stderr均空|
|C2050 40线程v2|5207165 / m4cm1607|已运行37分09秒，尚无Barrier行|未发现；两份stderr均空|

结论：此前两项在旧许可新建环境失败之后仍继续推进，当前未观察到许可过期导致中断。明确受影响的是5206992在gp.Env.start时退出；其替代作业5207165已使用作者新WLS通过节点许可测试。此结论依据实际状态和迭代，不推断WLS内部续期机制，也不改动既有运行任务。已完成Base2060/case32030的终态仍引用既有归档，本轮未重新操作5124127。
