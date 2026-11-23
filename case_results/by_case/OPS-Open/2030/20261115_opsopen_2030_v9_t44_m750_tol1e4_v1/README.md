<!-- unified-core-20261123 -->
最新统一核心入口：[OPS-Open 2030](D:/codeenv/pycharmproject/National_RL/National_model/case_results/core_library_20261123/by_case/OPS-Open/2030/20261115_opsopen_2030_v9_t44_m750_tol1e4_v1/index.html)。本卡以下内容作为历史记录保留。

# OPS-Open2030第二批启动记录

> 最新：验收PASS、备份COMPLETE；105件138,555,336bytes回本机，双端SHA通过。

[验收说明](D:/codeenv/pycharmproject/National_RL/National_model/case_results/by_case/OPS-Open/2030/20261115_opsopen_2030_v9_t44_m750_tol1e4_v1/acceptance_resource_batch2_20261116/README_ZH.md) · [验收JSON](D:/codeenv/pycharmproject/National_RL/National_model/case_results/by_case/OPS-Open/2030/20261115_opsopen_2030_v9_t44_m750_tol1e4_v1/acceptance_resource_batch2_20261116/acceptance_record.json) · [阶段报告](D:/codeenv/pycharmproject/National_RL/National_model/supplementary_materials/reviews/ops_flex_resource_sensitivity_20261114/acceptance_batch2_20261116/OPS_OPEN_2030_2040_2060_REPORT_ZH.md)

下方保留历次运行记录。

## 2026-11-15 23:20UTC OPS-Open2030已按作者例外放行，第二批齐备

作者明确批准2030的24h工程门禁及全部对照使用原B额度10.95890410958904Mt；全年4000Mt/冻结容量/求解容差保持不变。新目录runtime_batch2_2030_author_window_20261115七项门禁全部PASS：Open1h、原B/复制根中性/Open/Conservative/zero24h、真实生产profile1h。数据根中性目标差0，单调性最大反向1.5609e-15<1e-7。原537项模型回归源码LF SHA未变，额外3项例外作用域测试本机/T550均PASS。证据/冻结源提交02c4dd84，例外工具125fdfdd；旧失败MPS/IIS/日志完整保留。

新release20261115_opsopen_2030_v9_t44_m750_tol1e4_v1，沿用B2030 v3原冻结源，无新增闭合或筛选；90项原数据与作者输入SHA匹配，负荷逐行一致。sbatch从最新成功启动OPS-Open2060/5590961派生，preflight PASS，经held核对后release Job5591162。全年命令horizon=full_year、V9、44线程、64CPU/750G/UNLIMITED/no-requeue，不传短窗预算；原模型/BarX/BarPi/状态保全开启。

23:20UTC快照：LATE5587177、OPS-Open2040/5590946、2060/5590961三项RUNNING；2030/5591162 PENDING等待Resources，实际启动内存/smoke尚待分配节点，不宣称已通过。四项已全部提交，未超过4个并发/排队名额。2030启动脚本继续强制可用内存≥700GiB。

精确证据：batch2/2030/author_window_v2/、batch2/2030/FINAL_YEAR_RELEASE_GATES.json、batch2/deployment/ops_open_2030/。注意batch2/2030/YEAR_GATES_STOP.json与原窗口预算仍是历史失败记录，当前有效门禁/预算位于author_window_v2，不得用旧STOP再次拦截已获作者例外通过的新作业，也不得删除旧失败。

下一步询问时核原2030job实际分配/启动内存及四案运行，禁止重复提交；任何终态按5%余量规则完整备份T550、relative_v1与小文件交付。LATE-Open结束后按第一批在原MPS+自身BarPi上恢复年度核算行对偶并核完整行序SHA。第三批仍须作者明确确认，无后台监听，原有三项运行和冻结包未修改。

## 2026-11-16 13:26UTC 第二批四案运行快照与2030启动核验

一次性只读核验：云端4项RUNNING，无排队/新终态，不触发新备份、不操作作业。LATE-Open2050/5587177运行1天2:54:27到151轮，打印PInf=2.00e4、DInf=9.35e-8、Compl=626；近10轮分别下降58.25%/73.96%/67.40%，10.34分钟/轮，仍远未收敛。

OPS-Open2030/5591162运行12:46:34到121轮，打印PInf1.78e-4/DInf8.41e-8/Compl2.94e-5；2040/5590946运行14:38:03到137轮，1.26e-3/2.00e-8/9.33e-5；2060/5590961同运行14:38:03到147轮，6.58e-4/1.24e-8/7.99e-5。三项OPS近10轮原始残差/互补性下降，但对偶残差有反弹，不能称三项同步下降。没有solve_report/batch_exit，不能因互补性低于1e-4就宣称收敛/完成。

首次补核2030启动：00:39:44UTC在m4cm1901启动，实际cpu64/mem750G/node1/billing64、UNLIMITED，启动可用内存718.466244GiB≥700、Gurobi13.0.2 smoke PASS，全年资源结构审计PASS。2030已从此前PENDING进入RUNNING，case_catalog同步。四案stderr均空、近期日志未见warning；Slurm峰值RSS分别约643.93/517.19/523.64/511.58GiB（LATE/2030/2040/2060），与进程树指标分开。记录只用日志打印残差，不混入callback另一尺度。

证据snapshots/20261116T132611Z/snapshot.json及convergence_summary.json；源提交9407463f。没有模型/环境变更，不重复回归。精确下一步：保持询问时有限只读查询，发现终态按5%余量规则核旧备份/传输后完整备份，再T550验收/年度对偶恢复/小文件回传；第三批仍待作者明确确认，无后台监听。

## 2026-11-16 15:09UTC OPS-Open2030完成；备份待用户恢复T550

云端3运行/1新终态。OPS-Open2030/5591162于14:30:41UTC COMPLETED/0:0，总13:50:57、131轮OPTIMAL，目标4181810.139273937 million CNY，进程树峰520.621GiB（Slurm峰另记）。preservation COMPLETE、内置relative_v1 PASS、冻结容量输出PASS；原严格HARD_FAIL仅双向流/成本重构，原记录保留，正式T550验收尚未完成。开放全国V2G1000GW上限的实际松弛999.4437855GW通过。

终态盘点109文件5520216730bytes，完整含原MPS、BarX/BarPi、状态/日志和明确启动元数据，source_result_manifest SHA a9304f86c46e2248d4ce623a550dbb0e347007f9395c84fdfe3d2e5721f6e67a。本机到T550转发连接被拒绝，尚未能核已有目标manifest/活跃传输；用户明确“稍后恢复”。仅准备source_inventory、backup_config和backup_pending，没有启动传输，不把待备份写成COMPLETE。

其余三项RUNNING：LATE-Open2050到160轮，打印PInf3260/DInf8.94e-8/Compl135，近10轮降84.4%/28.5%/81.0%，11.17分钟/轮；OPS-Open2040到151轮，4.84e-4/1.04e-8/3.66e-5；2060到162轮，3.14e-4/1.17e-8/3.76e-5。两OPS原始残差与互补性继续下降；2060近10轮DInf略反弹4.46%，不说全部单调。三项stderr为空、无终态，不因互补性小于1e-4宣称完成。所有残差为Gurobi日志打印口径。

证据snapshots/20261116T150932Z/及ops_open_2030_completed_20261116/{terminal_summary,source_inventory,backup_config,backup_pending}.json；代码基准d12bcb7d，本轮无模型/环境变更。恢复后先核T550旧目标和传输，再按5%余量、互斥锁、全层SHA/源身份规则备份；完成后在T550验收与年度对偶恢复，只取小文件。其余原作业不操作，第三批未授权，无后台监听。

## 2026-11-16 20:52UTC 第二批三个OPS已结束并合并启动T550全备份

云端只剩LATE-Open2050/5587177运行（20:49UTC快照34:17:38）。OPS-Open2030/5591162、2040/5590946、2060/5590961均COMPLETED/0:0、OPTIMAL、preservation COMPLETE、内置relative_v1与冻结容量检查PASS。2030为131轮13:50:57、目标4181810.139274million CNY、进程树峰520.621GiB；2040为164轮18:09:23、目标5035960.232689、峰523.672GiB；2060为171轮17:27:58、目标5718684.655943、峰513.246GiB。原严格HARD_FAIL双向流/成本重构标签保留，正式T550验收仍待备份后执行。

用户恢复T550并明确把剩余已结束案例一起备份。先核hostname、空间、对应目标目录均不存在、无本批旧operation/活跃传输；2030此前仅有本地待办，未启动过单独传输。合并operation=20261116_resource_batch2_ops_completed，PID2385473已脱离本机（PPID1/SID同PID），由T550直连云端单次自主拉取。目标/home/zz2/National_model_server/cloud_backup/<release>/，保持相对路径、不删除源或旧备份。

规模：2030 109件5520216730bytes，2040 112件5526143353bytes，2060 112件5520870430bytes；合计333件16567230513bytes。含全部output_8760（原MPS、BarX/BarPi、状态/QC/日志）及明确启动/窗口门禁元数据，不含输入环境镜像或凭据。5%余量门槛满足，完成后预计仍余29.22%。已核传输RUNNING：2030/2040的T1已VERIFIED，2060的T1传输中；T2/T3未全完，不报告备份COMPLETE。本机断线不影响该单次进程。

证据batch2_completed_backup_20261116/{terminal_summary,terminal_qc_summary,source_inventory,target_precheck,backup_config,launch_receipt,initial_transfer_status,tool_provenance}.json，源状态snapshots/20261116T204903Z/snapshot.json。备用包装器backup_batch2_completed.py复用既有校验/互斥锁/续传引擎，只限定本次三案并扩充明确元数据清单；引擎/科学模型未修改。此前ops_open_2030_completed_20261116待办由本合并operation接续，不能再启动旧单案配置。

下一步先核PID2385473和transfer_status/backup_manifest，全部层VERIFIED且源身份不变后登记COMPLETE，再在T550按第一批方法验收、恢复各自原MPS+BarPi年度行对偶、分析并取小文件。LATE仍运行不纳入此次备份，不改其作业/冻结包；第三批未提交，无后台监听。
