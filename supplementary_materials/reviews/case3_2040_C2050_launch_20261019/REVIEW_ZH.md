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
