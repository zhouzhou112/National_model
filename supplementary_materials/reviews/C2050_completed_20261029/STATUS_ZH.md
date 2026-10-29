# C2050终态与待办

**2026-10-29 19:09 GMT（北京10月30日03:09）：云端1项RUNNING，C2050已完成。** C2050/5207165于16:28:53GMT（北京10月30日00:28:53）COMPLETED/0:0，总9天04:04:06，496轮OPTIMAL，目标5700892.181056213 million CNY，峰值RSS623.282GiB；保全COMPLETE/errors=[]，原模型已归档。最终PInf0.02918/DInf2.17e-6/Compl3.34e-5，旧10-14 relative_v1 HARD_FAIL（co2_source及solver原始残差>0.01）；10-27独立复评/筛选证书尚未执行，不自动采纳或放行2060。Case3 2050/5294579第129轮，运行2天05:38:15，PInf3.319e8/DInf4.760/Compl1.410e6，近10轮下降67.99%/89.88%/68.21%，22.12分钟/轮，stderr空。T550转发连接拒绝，备份配置已准备，尚未计划或启动传输，已请作者恢复。

## 2026-10-29 C2050终态与备份待恢复

**2026-10-29 19:09 GMT（北京10月30日03:09）：云端1项RUNNING，C2050已完成。** C2050/5207165于16:28:53GMT（北京10月30日00:28:53）COMPLETED/0:0，总9天04:04:06，496轮OPTIMAL，目标5700892.181056213 million CNY，峰值RSS623.282GiB；保全COMPLETE/errors=[]，原模型已归档。最终PInf0.02918/DInf2.17e-6/Compl3.34e-5，旧10-14 relative_v1 HARD_FAIL（co2_source及solver原始残差>0.01）；10-27独立复评/筛选证书尚未执行，不自动采纳或放行2060。Case3 2050/5294579第129轮，运行2天05:38:15，PInf3.319e8/DInf4.760/Compl1.410e6，近10轮下降67.99%/89.88%/68.21%，22.12分钟/轮，stderr空。T550转发连接拒绝，备份配置已准备，尚未计划或启动传输，已请作者恢复。

Git基准bf72d8e；只读squeue/sacct及solve/preservation/QC/result_manifest核验。证据C2050_completed_20261029/terminal_evidence.json、qc_failed_checks.json、backup_config.json；队列证据base_frozen_batch2_20261027/cloud_status_20261029T190921Z.json。结果manifest为46e39579d1d5ef4bcef80d722e4586a0c92b10019920db2a2ae5a051fbbf035c，80条5,509,265,018bytes；这只是结果manifest合计，完整备份还需启动元数据，未冒称最终计划规模。无模型/运行作业变更，不因QC标签放弃保全。

下一步：T550恢复后先查既有manifest/operation/锁/进程及30%余量；复用scripts/backup_completed_cloud.py，操作20261029_C2050_completed，仅一次自主拉取全部output_8760与明确启动元数据，分层SHA及源身份核验完成后再称完整备份。随后复用postprocess.py的assess/price，对C2050独立Mt验收及筛选证书在T550计算，只回传小JSON/汇总，不跑旧collect全清单。原始PInf门槛仍为0.01，不能仅以Mt更新推断PASS。不得自动启动C2060、不得触碰Case3在跑包；无后台监听。
