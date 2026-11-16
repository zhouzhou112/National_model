# OPS-Open 2040 第二批启动记录

Job 5590946 已提交并release；门禁及preflight PASS。当前等待节点资源，实际分配和启动内存尚待验证，不标为已运行。44线程，64CPU/750G/UNLIMITED/no-requeue，启动可用内存至少700GiB。

原冻结来源/上游/闭合复用已验收B2040，作者输入文件原样使用；全年碳上限不变。无候选筛选。终态后完整T550备份（5%余量）、relative_v1验收、年度行对偶恢复和小文件回传。第三批未授权，不自动提交。

证据：D:\codeenv\pycharmproject\National_RL\National_model\supplementary_materials\reviews\ops_flex_resource_sensitivity_20261114\batch2\deployment\ops_open_2040

## 2026-11-15 22:53UTC 第二批2040/2060启动检查通过

Job5590946（OPS-Open2040/m4cm1702）和5590961（OPS-Open2060/m4cm1803）均于22:48:15UTC开始运行；实配cpu64/mem750G/node1/billing64、UNLIMITED/no-requeue。启动可用内存分别720.655060与719.145313GiB，均≥700，Gurobi13.0.2计算节点smoke PASS，stderr空，配置44线程；全年模型仍在构建，实际求解参数/全年服务上界读回待构建完成。云端3运行（含LATE5587177），无新增第四项；2030仍在门禁STOP等待作者窗口预算决定，不能因另两案已运行而绕过该门禁。

证据batch2/startup_verification_2040_2060.json及snapshots/20261115T225352Z/snapshot.json。放行与2030停止证据eb85777c，模型源码相对537项覆盖回归无变化。case_catalog已改RUNNING。下一步：作者明确2030短窗例外前不重跑或提交2030；后续询问时只读核实际模型构建/迭代，终态按5%余量规则备份、T550恢复年度对偶和验收；第三批未提交，无监听。

## 2026-11-16 20:52UTC 第二批三个OPS已结束并合并启动T550全备份

云端只剩LATE-Open2050/5587177运行（20:49UTC快照34:17:38）。OPS-Open2030/5591162、2040/5590946、2060/5590961均COMPLETED/0:0、OPTIMAL、preservation COMPLETE、内置relative_v1与冻结容量检查PASS。2030为131轮13:50:57、目标4181810.139274million CNY、进程树峰520.621GiB；2040为164轮18:09:23、目标5035960.232689、峰523.672GiB；2060为171轮17:27:58、目标5718684.655943、峰513.246GiB。原严格HARD_FAIL双向流/成本重构标签保留，正式T550验收仍待备份后执行。

用户恢复T550并明确把剩余已结束案例一起备份。先核hostname、空间、对应目标目录均不存在、无本批旧operation/活跃传输；2030此前仅有本地待办，未启动过单独传输。合并operation=20261116_resource_batch2_ops_completed，PID2385473已脱离本机（PPID1/SID同PID），由T550直连云端单次自主拉取。目标/home/zz2/National_model_server/cloud_backup/<release>/，保持相对路径、不删除源或旧备份。

规模：2030 109件5520216730bytes，2040 112件5526143353bytes，2060 112件5520870430bytes；合计333件16567230513bytes。含全部output_8760（原MPS、BarX/BarPi、状态/QC/日志）及明确启动/窗口门禁元数据，不含输入环境镜像或凭据。5%余量门槛满足，完成后预计仍余29.22%。已核传输RUNNING：2030/2040的T1已VERIFIED，2060的T1传输中；T2/T3未全完，不报告备份COMPLETE。本机断线不影响该单次进程。

证据batch2_completed_backup_20261116/{terminal_summary,terminal_qc_summary,source_inventory,target_precheck,backup_config,launch_receipt,initial_transfer_status,tool_provenance}.json，源状态snapshots/20261116T204903Z/snapshot.json。备用包装器backup_batch2_completed.py复用既有校验/互斥锁/续传引擎，只限定本次三案并扩充明确元数据清单；引擎/科学模型未修改。此前ops_open_2030_completed_20261116待办由本合并operation接续，不能再启动旧单案配置。

下一步先核PID2385473和transfer_status/backup_manifest，全部层VERIFIED且源身份不变后登记COMPLETE，再在T550按第一批方法验收、恢复各自原MPS+BarPi年度行对偶、分析并取小文件。LATE仍运行不纳入此次备份，不改其作业/冻结包；第三批未提交，无后台监听。
