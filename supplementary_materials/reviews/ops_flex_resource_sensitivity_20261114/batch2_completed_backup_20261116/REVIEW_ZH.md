## 2026-11-16 20:52UTC 第二批三个OPS已结束并合并启动T550全备份

云端只剩LATE-Open2050/5587177运行（20:49UTC快照34:17:38）。OPS-Open2030/5591162、2040/5590946、2060/5590961均COMPLETED/0:0、OPTIMAL、preservation COMPLETE、内置relative_v1与冻结容量检查PASS。2030为131轮13:50:57、目标4181810.139274million CNY、进程树峰520.621GiB；2040为164轮18:09:23、目标5035960.232689、峰523.672GiB；2060为171轮17:27:58、目标5718684.655943、峰513.246GiB。原严格HARD_FAIL双向流/成本重构标签保留，正式T550验收仍待备份后执行。

用户恢复T550并明确把剩余已结束案例一起备份。先核hostname、空间、对应目标目录均不存在、无本批旧operation/活跃传输；2030此前仅有本地待办，未启动过单独传输。合并operation=20261116_resource_batch2_ops_completed，PID2385473已脱离本机（PPID1/SID同PID），由T550直连云端单次自主拉取。目标/home/zz2/National_model_server/cloud_backup/<release>/，保持相对路径、不删除源或旧备份。

规模：2030 109件5520216730bytes，2040 112件5526143353bytes，2060 112件5520870430bytes；合计333件16567230513bytes。含全部output_8760（原MPS、BarX/BarPi、状态/QC/日志）及明确启动/窗口门禁元数据，不含输入环境镜像或凭据。5%余量门槛满足，完成后预计仍余29.22%。已核传输RUNNING：2030/2040的T1已VERIFIED，2060的T1传输中；T2/T3未全完，不报告备份COMPLETE。本机断线不影响该单次进程。

证据batch2_completed_backup_20261116/{terminal_summary,terminal_qc_summary,source_inventory,target_precheck,backup_config,launch_receipt,initial_transfer_status,tool_provenance}.json，源状态snapshots/20261116T204903Z/snapshot.json。备用包装器backup_batch2_completed.py复用既有校验/互斥锁/续传引擎，只限定本次三案并扩充明确元数据清单；引擎/科学模型未修改。此前ops_open_2030_completed_20261116待办由本合并operation接续，不能再启动旧单案配置。

下一步先核PID2385473和transfer_status/backup_manifest，全部层VERIFIED且源身份不变后登记COMPLETE，再在T550按第一批方法验收、恢复各自原MPS+BarPi年度行对偶、分析并取小文件。LATE仍运行不纳入此次备份，不改其作业/冻结包；第三批未提交，无后台监听。

## 2026-11-16 OPS-Open2030/2040/2060 T550验收与本地交付完成

证据/工具提交af640553。合并备份于21:19:45UTC COMPLETE：333文件16567230513bytes，T1/T2/T3全部VERIFIED、源身份未变，原PID2385473退出。验收前T550逐文件重新核全部原件bytes/SHA；当前relative_v1重评三个年份全部PASS，冻结容量身份/全年资源结构/保全亦PASS。原严格HARD_FAIL双向流/成本重构及水库暂缓披露保留，不自动决定作者采用状态。无候选筛选，无筛选证书要求。

逐案从原MPS ROWS+本解BarPi恢复1134年度核算行，完整原始行数/名称/sense顺序哈希匹配，旁置acceptance_resource_batch2_20261116/annual_rows，原SavedDual导出缺项和原输出不改。T550完成合同/上限/调用/等效小时、全国及五省8760调度、31省完整负荷侧价格、分省技术发电/风光弃电、连续启停容量/等效次数/成本、储能与同年REF/中央OPS成本比较；数值闭合/重构核对通过。不是用离散机组次数解释连续RUC变量，不以无负价作为正确性标准。

相对同年REF，2030/2040/2060成本点差109.69/521.16/704.13亿元/年；工程区间[106.62,124.16]/[482.65,535.63]/[656.83,723.16]。相对中央OPS再省79.23/265.12/221.44亿元。四年概览复用第一批已验收2050及其登记SHA，未重算旧案；不能把不同资源量跨框架比值当投资替代份额。

三个本地包：2030 105件138555336bytes，2040 107件140663242bytes，2060 107件140978073bytes；有效载荷319件420196651bytes，单件最大30158372bytes，双端SHA全部匹配，验收JSON同步。Case3 2040清单72项适用原文件（无筛选candidate_selection.csv不适用）加冻结/结构/验收/分析；大MPS、BarX/BarPi、热电/水库/柔性大NPZ留T550。回传2040时转发中断，重连后一次连接补2040/2060，2030未重复传输，未重跑备份或科学计算。

主报告acceptance_batch2_20261116/OPS_OPEN_2030_2040_2060_REPORT_ZH.md，四年概览CSV、当前三案表和逐案包均已交付；统一索引case_results/OPS_OPEN_SECOND_BATCH_20261116.md。报告/表/回执与LATE快照已同步T550 analysis_tools_resource_batch2_20261116/final_report，closeout_verification PASS，云端源manifest收尾仍一致。case_catalog与备份台账改COMPLETE/PASS。

LATE5587177截至21:55UTC仍RUNNING，第197轮，打印PInf294/DInf1.57e-7/Compl7.87；近10轮PInf/Compl降44.2%/47.5%，DInf小量反弹40.2%，10.99分钟/轮，Slurm峰643.93GiB、stderr空、无终态。第二批整体尚未结束，当前仅OPS三案阶段交付；第三批仍待作者明确确认，无新提交/重解/监听、不改冻结包或SI。

下一步按询问只读核LATE终态，结束后按5%余量备份、恢复年度行对偶、当前验收和自身双向定价证书；若需要放开重解先报作者。不得据OPS三案已PASS而自动启动第三批。
