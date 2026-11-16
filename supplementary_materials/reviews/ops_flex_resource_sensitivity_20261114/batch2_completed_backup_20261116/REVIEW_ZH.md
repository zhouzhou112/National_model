## 2026-11-16 20:52UTC 第二批三个OPS已结束并合并启动T550全备份

云端只剩LATE-Open2050/5587177运行（20:49UTC快照34:17:38）。OPS-Open2030/5591162、2040/5590946、2060/5590961均COMPLETED/0:0、OPTIMAL、preservation COMPLETE、内置relative_v1与冻结容量检查PASS。2030为131轮13:50:57、目标4181810.139274million CNY、进程树峰520.621GiB；2040为164轮18:09:23、目标5035960.232689、峰523.672GiB；2060为171轮17:27:58、目标5718684.655943、峰513.246GiB。原严格HARD_FAIL双向流/成本重构标签保留，正式T550验收仍待备份后执行。

用户恢复T550并明确把剩余已结束案例一起备份。先核hostname、空间、对应目标目录均不存在、无本批旧operation/活跃传输；2030此前仅有本地待办，未启动过单独传输。合并operation=20261116_resource_batch2_ops_completed，PID2385473已脱离本机（PPID1/SID同PID），由T550直连云端单次自主拉取。目标/home/zz2/National_model_server/cloud_backup/<release>/，保持相对路径、不删除源或旧备份。

规模：2030 109件5520216730bytes，2040 112件5526143353bytes，2060 112件5520870430bytes；合计333件16567230513bytes。含全部output_8760（原MPS、BarX/BarPi、状态/QC/日志）及明确启动/窗口门禁元数据，不含输入环境镜像或凭据。5%余量门槛满足，完成后预计仍余29.22%。已核传输RUNNING：2030/2040的T1已VERIFIED，2060的T1传输中；T2/T3未全完，不报告备份COMPLETE。本机断线不影响该单次进程。

证据batch2_completed_backup_20261116/{terminal_summary,terminal_qc_summary,source_inventory,target_precheck,backup_config,launch_receipt,initial_transfer_status,tool_provenance}.json，源状态snapshots/20261116T204903Z/snapshot.json。备用包装器backup_batch2_completed.py复用既有校验/互斥锁/续传引擎，只限定本次三案并扩充明确元数据清单；引擎/科学模型未修改。此前ops_open_2030_completed_20261116待办由本合并operation接续，不能再启动旧单案配置。

下一步先核PID2385473和transfer_status/backup_manifest，全部层VERIFIED且源身份不变后登记COMPLETE，再在T550按第一批方法验收、恢复各自原MPS+BarPi年度行对偶、分析并取小文件。LATE仍运行不纳入此次备份，不改其作业/冻结包；第三批未提交，无后台监听。
