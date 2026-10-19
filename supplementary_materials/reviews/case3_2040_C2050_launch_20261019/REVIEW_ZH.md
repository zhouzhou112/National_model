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
