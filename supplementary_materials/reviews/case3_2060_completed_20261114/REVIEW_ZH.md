# Case3 2060终态与自主备份（2026-11-14）

**求解完成、原始结果完整保全；正式验收待办。** 云端0运行/0排队，5411471为COMPLETED/0:0，求解器OPTIMAL。11月14日10:43:56 UTC（北京18:43:56）作业结束，总7天20:42:27，518轮。日志中的Barrier耗时675686秒；Slurm作业总时长还含构建、导出等，不能混用。

- 目标P=5713559.887378571 million CNY，D=5708901.4104205845，P−D=4658.476957986131 million CNY，相对差0.0008153370。未作情景成本结论，尚待自身定价证书。
- 终态telemetry PInf=0.0465391742、DInf=5.020353e-6、Compl=5.419497e-5。原relative_v1 HARD_FAIL仅solver项，六组已执行物理检查通过、水库DEFERRED；原记录保留。
- 原最大约束违反0.032784048759，index53400865，行名未知、独立重构未执行。不能因索引与其他案例相同推定其行族。正式验收还需本解原MPS+BarX行定位、自身BarPi筛选证书及当前评估器重评。
- 原模型、BarX/BarPi、容量/运营/状态/QC等全部保全COMPLETE，errors=[]。进程树采样峰653.886GiB、Slurm MaxRSS650.685GiB，口径不同，均不把Gurobi累计分配量当常驻内存。

## 备份进展

完整清单106文件、5,506,884,504bytes；源result_manifest SHA `2769049a1e38dd81ad3b0baef4fa1eee0696811bee4d095979ae88057438514d`。源盘点与T550独立计划逐项一致，T1/T2/T3全部纳入，不复制许可证或私钥。

T550最初转发拒绝，作者开启后恢复。无同名目标/operation、无活跃传输、全局锁可用。原目标盘211GiB/5.63%可用，触发30%门禁；作者随后明确“直接保存别管门槛”，本次仅对此operation将有效预留比例改为0（仍要求剩余容量足以容纳完整待传文件），不推广至其他任务。历史阻塞记录保留。核心备份引擎未改；独立wrapper严格匹配operation、release、目标路径与作者原话，6项授权范围检查通过。

15:37:24 UTC已启动PID1081649，PPID1/SID1081649，独立session、stdin DEVNULL；本机断线或关机不影响T550直连云端。15:37:47核验RUNNING/T1 TRANSFERRING，stderr空、实际约10MB/s。**当前未生成完整校验manifest，不称备份完成。**

目标：`/home/zz2/National_model_server/cloud_backup/20261106_case3_2060_v9a12_screen0p2_agg0_t44_m750_tol1e4_v1`。
操作：`/home/zz2/National_model_server/cloud_backup/_operations/20261114_case3_2060_completed`。
工具：`/home/zz2/National_model_server/backup_tools/case3_2060_20261114`。

互斥锁、可续传rsync、逐文件bytes/SHA校验、最终源身份复核均保留，无删除、重解或定时监听。`backup_blocked.json`是被作者明确覆盖的历史门禁事件；最新状态见`backup_progress.json`，之后以远端transfer_status与最终backup_manifest为准。

## 复现与下一步

`backup_case3_2060.py plan|run --config backup_config.json --engine backup_completed_cloud.py`；已有plan/run不得盲目重复。工具原字节SHA与作者例外见`backup_tool_provenance.json`，启动证据见`backup_launch_receipt.json`，独立盘点与计划见`source_inventory.json`、`backup_plan_receipt.json`。本机仅取终态/清单小证据，未取逐时数组或原模型。

下一次连接先核旧PID、transfer_status及backup_manifest；三层全部VERIFIED且源身份不变后才登记COMPLETE。随后在完整T550备份上完成独立行定位、自身BarPi证书和扩展验收；不能以OPTIMAL或备份完成代替正式验收。

收尾快照15:39:27 UTC：T1的102文件577328415bytes已逐文件VERIFIED，T2传输中，进程仍独立运行、stderr空；详见`backup_closeout_status.json`。此时全备份未完成。
