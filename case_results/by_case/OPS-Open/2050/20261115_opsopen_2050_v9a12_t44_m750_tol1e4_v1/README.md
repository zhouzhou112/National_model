<!-- unified-core-20261123 -->
最新统一核心入口：[OPS-Open 2050](D:/codeenv/pycharmproject/National_RL/National_model/case_results/core_library_20261123/by_case/OPS-Open/2050/20261115_opsopen_2050_v9a12_t44_m750_tol1e4_v1/index.html)。本卡以下内容作为历史记录保留。

# OPS-Open 2050 — 第一批启动记录

> 最新状态：验收PASS、备份COMPLETE；107件、142,735,375bytes已回本机，双端SHA全部通过。

[验收包说明](D:/codeenv/pycharmproject/National_RL/National_model/case_results/by_case/OPS-Open/2050/20261115_opsopen_2050_v9a12_t44_m750_tol1e4_v1/acceptance_resource_batch1_20261115/README_ZH.md) · [验收JSON](D:/codeenv/pycharmproject/National_RL/National_model/case_results/by_case/OPS-Open/2050/20261115_opsopen_2050_v9a12_t44_m750_tol1e4_v1/acceptance_resource_batch1_20261115/acceptance_record.json) · [第一批报告](D:/codeenv/pycharmproject/National_RL/National_model/supplementary_materials/reviews/ops_flex_resource_sensitivity_20261114/acceptance_batch1_20261115/BATCH1_REPORT_ZH.md)

下方保留历次运行记录。

Job 5584373，截至 2026-11-15T00:52:34.902580Z 为RUNNING，尚未验收/备份。44线程、64CPU/750G/UNLIMITED/no-requeue；启动可用内存 719.039097 GiB。

云端：/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20261115_opsopen_2050_v9a12_t44_m750_tol1e4_v1

门禁与证据：D:\codeenv\pycharmproject\National_RL\National_model\supplementary_materials\reviews\ops_flex_resource_sensitivity_20261114


第一批全部终态后备份、验收并交批次报告，作者确认前不得提交第二批。

## 2026-11-15 19:40UTC 三案完成、LATE启动核验与5%门槛备份

云端1运行/3新终态。LATE-Open5587177于10:31:51UTC在m4cm2206启动，已运行9:08:17、第33轮；AllocTRES64CPU/750G/billing64、UNLIMITED/no-requeue，启动可用718.968025GiB≥700，Gurobi13.0.2 smoke PASS、实际44线程、全年服务结构PASS、stderr空。当前打印PInf1.37e10/DInf105/Compl5.64e8，仍在早期；近10轮9.8067分钟/轮，Slurm峰643.934GiB。排序3871.64秒、FactorNZ2.233e10/FactorOps7.483e14，与测试相同规模，尚无终态。

OPS-Open5584373 COMPLETED/0:0，150轮、15:55:05、目标5678988.615607million CNY、进程树峰525.316GiB；OPS-Conservative5584377同为COMPLETED/0:0，161轮、17:12:19、目标5731237.048268、峰522.365GiB；D1/C5 5584390同为COMPLETED/0:0，149轮、14:53:19、目标5707128.582746、峰522.378GiB。三案preservation COMPLETE、内置relative_v1 PASS、冻结容量输出检查PASS。严格绝对口径原HARD_FAIL保留：双向流/成本重构（保守另有水库项），未替换或删除原QC。此为终态与内置QC核验，正式验收包/完整批次报告尚待备份后整理。

备份清单335件16565040777bytes，含全部output_8760、原MPS、BarX/BarPi与明确启动元数据。T550原30%规则会在备份后29.7531%处拦截；已向作者回报完整清单与余量。作者明确“改掉至少30%改为至少5%，然后直接备份”，本次改为通用新规则，不是单案例外。AGENTS第10-20节第3条改5%并追加本日决定；backup_completed_cloud默认及下限改5%，保留显式旧配置不改写。9项针对性备份测试PASS（含整批备份后的余量检查、活跃作业拒绝、路径/旧目标保护）。代码提交acb27944，未改模型或任何冻结作业。

核无同名备份与旧传输后已启动T550单次自主拉取PID3841220，operation=20261115_resource_batch1_completed，计划备份后余29.7531%（约1.20TB）满足新5%。源root为National_model_cloud，目标/home/zz2/National_model_server/cloud_backup。状态RUNNING，不能称备份完成；不重复启动，不建立监听。此前LATE五轮测试备份已COMPLETE，未重复传输。

证据status_20261115T194003Z/{summary,terminal_qc,backup_inventory,backup_config,backup_launch,backup_tool_provenance}.json及snapshots/20261115T194003Z/snapshot.json。下一步核旧PID3841220与各层VERIFIED/backup_manifest，源身份一致后登记COMPLETE；在T550做验收与初步分析，只取小文件；完成第一批报告后等作者明确授权其他第二批作业。LATE继续原作业，不重启/调参。
