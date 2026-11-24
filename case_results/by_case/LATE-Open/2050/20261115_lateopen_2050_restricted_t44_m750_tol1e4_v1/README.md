<!-- paper-name-20261124 -->
论文正式名称：**LATE-Open 2050**；历史代号：`LATE-Open`。

<!-- unified-core-20261123 -->
最新统一核心入口：[LATE-Open 2050](D:/codeenv/pycharmproject/National_RL/National_model/case_results/core_library_20261123/by_case/LATE-Open/2050/20261115_lateopen_2050_restricted_t44_m750_tol1e4_v1/index.html)。本卡以下内容作为历史记录保留。

## 2026-11-15 08:47UTC 作者单独授权LATE-Open2050正式求解已放行

作者在五轮测试与条件耗时报告后明确“启动LATE-Open，可以考量48核心吧”。按本次直接授权仅提前启动LATE-Open2050受限全年作业，覆盖该案等待第一批结束的时间条件，未授权其他第二/三批案例。考虑44线程实测进程树峰649.791GiB、48线程峰值及加速未验证，执行方推荐并沿用44线程；简单比例外推708.863GiB仅为风险提示，不是可靠内存预测。没有改模型源码/约束/目标/输入/数值参数，复用535项回归、真实1h界审计、24h自身解恒等性、全年结构审计与5轮测试。

新release：20261115_lateopen_2050_restricted_t44_m750_tol1e4_v1；源提交c92ee1bb（授权236b8fa7，模型源码仍与29e3782d同字节），sbatch从最新成功测试5584392派生。原R1上游、4481自由/28846下界/3359上界固定清单SHA不变；生产profile与测试profile的numerics逐键相等，正式入口没有5轮回调，开启原MPS、BarX/BarPi和候选状态保全。独立复制/输入SHA/负荷逐行相等/preflight/bash语法检查均PASS。经held核对后release Job5587177。

08:47UTC：云端3RUNNING+1PENDING。5587177等待Resources，StartTime=Unknown，ReqTRES cpu64/mem750G/node1/billing64，UNLIMITED/Requeue=0；AllocTRES尚空、尚无startup_resources或compute_node_smoke，不能宣称已实际启动或内存已通过。脚本内启动门禁保留可用内存≥700GiB及资源核对；下一次先查原job，不重复提交或自动重跑。估时从实际启动计，条件3.6–4.1天，保守4.8–5.3天，不保证五天内。

测试5584392备份已在08:43:31UTC COMPLETE：42文件4191604666bytes，T1/T3全部VERIFIED、源manifest身份未变；T2按测试设计未产生，不伪称存在最终科学解。证据factor_test_backup_complete.json，原PID2744265不重复启动。

操作入口deploy_late_production.py prepare/preflight/submit-release/status，只能表示这一授权案例；snapshot_batch1.py已扩展读正式LATE。最新证据deployment/late_open_2050/、LATE_PRODUCTION_AUTHORIZATION.json、LATE_PRODUCTION_LAUNCH_GATES.json。没有碰3个运行作业或旧冻结包，没有后台监听。下一步核实际分配和启动内存、全年结构/参数；终态按原规则完整备份、relative_v1及本解自身双向定价B证书，报告与LATE2050目标比较，需放开重解先报作者。其余第二批仍等待原批次完成与作者确认。

## 2026-11-15 19:40UTC 三案完成、LATE启动核验与5%门槛备份

云端1运行/3新终态。LATE-Open5587177于10:31:51UTC在m4cm2206启动，已运行9:08:17、第33轮；AllocTRES64CPU/750G/billing64、UNLIMITED/no-requeue，启动可用718.968025GiB≥700，Gurobi13.0.2 smoke PASS、实际44线程、全年服务结构PASS、stderr空。当前打印PInf1.37e10/DInf105/Compl5.64e8，仍在早期；近10轮9.8067分钟/轮，Slurm峰643.934GiB。排序3871.64秒、FactorNZ2.233e10/FactorOps7.483e14，与测试相同规模，尚无终态。

OPS-Open5584373 COMPLETED/0:0，150轮、15:55:05、目标5678988.615607million CNY、进程树峰525.316GiB；OPS-Conservative5584377同为COMPLETED/0:0，161轮、17:12:19、目标5731237.048268、峰522.365GiB；D1/C5 5584390同为COMPLETED/0:0，149轮、14:53:19、目标5707128.582746、峰522.378GiB。三案preservation COMPLETE、内置relative_v1 PASS、冻结容量输出检查PASS。严格绝对口径原HARD_FAIL保留：双向流/成本重构（保守另有水库项），未替换或删除原QC。此为终态与内置QC核验，正式验收包/完整批次报告尚待备份后整理。

备份清单335件16565040777bytes，含全部output_8760、原MPS、BarX/BarPi与明确启动元数据。T550原30%规则会在备份后29.7531%处拦截；已向作者回报完整清单与余量。作者明确“改掉至少30%改为至少5%，然后直接备份”，本次改为通用新规则，不是单案例外。AGENTS第10-20节第3条改5%并追加本日决定；backup_completed_cloud默认及下限改5%，保留显式旧配置不改写。9项针对性备份测试PASS（含整批备份后的余量检查、活跃作业拒绝、路径/旧目标保护）。代码提交acb27944，未改模型或任何冻结作业。

核无同名备份与旧传输后已启动T550单次自主拉取PID3841220，operation=20261115_resource_batch1_completed，计划备份后余29.7531%（约1.20TB）满足新5%。源root为National_model_cloud，目标/home/zz2/National_model_server/cloud_backup。状态RUNNING，不能称备份完成；不重复启动，不建立监听。此前LATE五轮测试备份已COMPLETE，未重复传输。

证据status_20261115T194003Z/{summary,terminal_qc,backup_inventory,backup_config,backup_launch,backup_tool_provenance}.json及snapshots/20261115T194003Z/snapshot.json。下一步核旧PID3841220与各层VERIFIED/backup_manifest，源身份一致后登记COMPLETE；在T550做验收与初步分析，只取小文件；完成第一批报告后等作者明确授权其他第二批作业。LATE继续原作业，不重启/调参。

2026-11-19：T550条件验收PASS，独立最大行河北年度外送残差0.015772605GWh、比例5.7493e-8，在容差内；自身双向B=6517.873876million CNY，B/P=0.00115236245，接受并披露。年度行对偶恢复1134行，107个小文件138036187bytes已回本机，双端SHA与验收JSON一致。原严格标签和输出不变；作者已授权准备2060，明确暂不提交。完整报告见本地completion_20261119。
