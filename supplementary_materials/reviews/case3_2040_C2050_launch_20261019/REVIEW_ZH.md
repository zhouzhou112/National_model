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
