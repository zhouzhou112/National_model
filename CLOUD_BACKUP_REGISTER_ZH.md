# 云端生产求解与 T550 备份台账

更新：2026-10-20，新增两套已完整校验，见 `completed_acceptance_20261020/backup_completion_verification.json`。本表为当次核验快照，传输实时状态以 T550 操作目录中的 `transfer_status.json` 为准。

目标根目录：`/home/zz2/National_model_server/cloud_backup/`，每个 release 保持原相对路径。备份不等于科学采纳，不受 QC 的 PASS/FAIL/HARD_FAIL 标签影响。

| 项目 | release | 备份范围规模 | 本次核验状态 |
|---|---|---:|---|
| Base2030 | `20260914_base_v9_t48_m750_tol1e4_v3` | 87 文件；5,314,976,517 bytes | 历史 COMPLETE；当前 manifest 的 path/bytes/SHA 与历史逐项一致 |
| Base2040 | `20260919_base2040_v9_t44_m750_tol1e4_v1` | 87 文件；5,320,516,058 bytes | 历史 COMPLETE；当前 manifest 与历史逐项一致 |
| Base2050 | `20260930_base2050_v9_t48_m750_tol1e4_v1` | 88 文件；5,322,218,103 bytes | 历史 COMPLETE；当前 manifest 与历史逐项一致 |
| Base2060 | `20261012_base2060_v9a12_t48_m750_tol1e4_v1` | 91 文件；5,314,567,406 bytes | COMPLETE，三层全部SHA VERIFIED；本地验收PASS |
| Case3 2030 | `20261014_case3_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1` | 93 文件；5,514,167,791 bytes | COMPLETE，三层全部SHA VERIFIED；本地验收PASS |
| nocredit 2030 | Job5153901 | 结束后盘点 | RUNNING；确认结束后执行同一备份流程 |
| Case3 2040 | Job5201318 | 结束后盘点 | RUNNING；确认结束后执行同一备份流程 |
| C2050 40 线程新许可重跑 | Job5207165 | 结束后盘点 | RUNNING；确认结束后执行同一备份流程 |

当前已完成的 `*/output_8760/solve_report.json` 共五套，上表全部纳入；三套旧备份不重复启动。旧备份本轮只对照 manifest，未重复读取目标全部 15.96 GB 计算 SHA；逐文件 SHA 完成证据来自 2026-10-12 的原验证。

C2050 的 OOM 和旧许可失败 release 保留在云端，未作为“已解结果”计入上述五套，也未宣称已有完整解或 T550 完整备份。后续如整理异常终态，使用单独的部分备份范围和清单，不能混入完整结果完成计数。

## 本次操作

- 操作目录：`/home/zz2/National_model_server/cloud_backup/_operations/20261020_base2060_case3_2030/`。
- T550 单次进程 PID：`2833275`；UTC 2026-10-20 16:06:17 启动，独立会话运行，不依赖 Windows 持续在线。
- 新增两套总计 184 文件、10,828,735,197 bytes（10.83 GB），T1→T2→T3 全部包含；没有删除或覆盖旧备份。
- 启动前估算完成后磁盘剩余 34.4127%，大于既定 30% 门槛。
- 完成标准：六个传输层全部 SHA VERIFIED、源身份复核不变、两套最终 `backup_manifest.json` 为 COMPLETE。已满足全部条件；六层VERIFIED，两个最终manifest均COMPLETE。
- 工具：`scripts/backup_completed_cloud.py`；显式配置：`supplementary_materials/reviews/cloud_backup_20261020/backup_config.json`。原 2026-10-12 工具与证据不改写。

Case3 2030 的 Claude 定价证书全套七文件、扩展 relative_v1 JSON、证书身份检查共九文件（6,223,488 bytes），已另外按原始字节同步到该 release 旁的 `assessments_20261020/`，全部 SHA VERIFIED。它们不改写冻结 `output_8760`，其独立 manifest 与验证见本次证据目录。

## 后续固定流程

每次确认云端生产求解结束，立即核对并补齐 T550 备份，无需作者再次提醒。保持现有“作者询问时检查”的方式，不增加定时监听；传输一旦启动可在 T550 自主完成。遇到中断先检查现有进程、锁和状态再续传，不盲目重复启动。

详情和操作命令见 `SERVER_RUNBOOK.md` 的“2026-10-20 完成求解后 T550 必做备份流程”；授权规则见 `AGENTS.md` 同日条目。

## 2026-10-20 最终核验与本地验收包

本轮两套新增备份在 2026-10-20T16:26:47.750542+00:00 完成；已将最终manifest取回并与原plan逐项核对，共184文件/10.83GB，未延期任何T3。Base2060和Case32030均通过现行扩展relative_v1，正式JSON在T550旁置并原字节同步，本地ZIP见 `supplementary_materials/reviews/completed_acceptance_20261020/packages/`。大文件没有额外回传本机。云端与T550原输出不变；科学质量参考标签和作者采纳分开。


## 2026-10-24 nocredit2030完成与两项目进度

**2026-10-24英国10:45／北京17:45：当前2项RUNNING，nocredit2030刚完成。** Job5153901于北京17:43:45 COMPLETED/0:0，总4天11:13:23，Barrier404轮OPTIMAL，目标4189002.976254521 million CNY；保全COMPLETE/errors=[]，81个output_8760文件共5,502,966,799bytes。冻结报告relative_v1_author_20261012=PASS，严格HARD_FAIL仍保留；这不是最新扩展口径的独立正式验收。其T550备份未启动：127.0.0.1:22转发拒绝连接、192.168.9.27:22超时，旧manifest/空间/活跃传输尚不可核验。已准备新配置，恢复连接后先防重复核验再自主拉取。Case3 2040/5201318到302轮，PInf7.68/DInf6.76e-5/Compl0.0837；C2050 t40/5207165到221轮，PInf734/DInf5.16e-8/Compl11.2；两项仍求解中。

Git基准8ed5beb6ebd2ddc2e5f038f36ce27e1ee2ebdcf3。09:43UTC第一快照三项RUNNING；09:45UTC再次squeue/sacct确认nocredit正常退出，不把两时点混作同时观测。其求解382362秒、终轮打印PInf8.46e-5/DInf1.98e-7/Compl3.14e-6；最终保全与result_manifest、batch_exit已生成。Case3近292–302轮三项残差降20.91%/20.84%/21.04%，约20.08分钟/轮；C2050近211–221轮降34.46%/45.11%/41.67%，约25.05分钟/轮。当前RSS分别396.02/416.91GiB，Slurm峰712.44/621.18GiB未变，stderr均空，无新警告/OOM。不能据此给可靠ETA。

证据：supplementary_materials/reviews/cloud_joint_progress_20261016/status_20261024T094319Z{,_summary}.json、nocredit_completion_20261024.json；备份配置与阻塞记录cloud_backup_20261024/。现有五套已完成备份的历史结论保留，本轮不能实时复核T550。下一步恢复既有转发后核对manifest/活跃进程/锁/磁盘余量，使用scripts/backup_completed_cloud.py对新release plan/run，全量bytes/SHA和源身份校验完成才称备份完成。无后台监听、不改变活跃作业/冻结包/科学参数；其他SI会话改动保留。仅记录和JSON更新，JSON解析及暂存diff检查，无需重复模型测试。


## 2026-10-25 两项目继续收敛与T550连接阻塞

**2026-10-25英国13:23 GMT／北京21:23：云端2项RUNNING。** Case3 2040/5201318到388轮（5天14:23:02），PInf0.568/DInf4.77e-6/Compl0.006；较昨日302推进86轮，近378–388轮三项下降27.18%/28.49%/28.14%，19.73分钟/轮。C2050 t40/5207165到279轮（5天00:58:50），PInf104/DInf2.71e-6/Compl0.965；较昨日221推进58轮，互补性首次低于1。近269–279轮原始/互补下降26.76%/31.56%，对偶反增122.13%，31.21分钟/轮；268和273轮对偶反弹，273峰3.71e-6后连续回落至2.71e-6，仍高于反弹前267轮2.71e-8，不能称三项持续单调改善。两项stderr空、无显式警告/错误/终态，RSS396.04/416.91GiB、Slurm峰712.44/621.18GiB未增；不承诺ETA。nocredit5153901再次sacct确认COMPLETED/0:0；T550 127.0.0.1:22转发仍Connection refused，无法核验manifest/空间/旧进程，备份本轮未启动。

Git基准45dc64751cc555768f277c47a6b0daadbba209ae；仅只读squeue/scontrol/sstat/sacct和日志、保存小证据与更新交接。证据supplementary_materials/reviews/cloud_joint_progress_20261016/status_20261025T132337Z{,_summary}.json、t550_backup_check_20261025.json。未改科学代码、冻结包、运行作业、其他SI会话或建立监听。验证为JSON解析、暂存范围/凭据模式/diff检查；无模型改动不重跑求解。下一步用户询问时检查收敛/终态；恢复T550既有转发后先核对旧备份、活跃传输与30%磁盘余量，再按cloud_backup_20261024/backup_config.json执行单次自主拉取和全量SHA校验，未完成前不标COMPLETE。


## 2026-10-25 T550恢复并启动nocredit2030完整备份

**2026-10-25英国13:25 GMT／北京21:25，T550连接恢复，取代本日上一条备份阻塞状态。** 作者开启转发后已核验hostname=t550；既有五套备份manifest均COMPLETE，两旧操作COMPLETE且未发现活跃备份进程。nocredit2030新计划93文件/5,510,708,567bytes（全部output_8760及启动身份元数据，T1/T2/T3全部包含），预计余量36.2871%满足30%门槛。单次自主传输PID700378于13:25:24UTC启动，13:25:38核验进程存在、状态RUNNING/T1 TRANSFERRING（89文件/584,009,478bytes），尚无完整目标SHA验证和最终manifest，不称备份完成。

Git基准6ee7f8a4241ed9a572aa2e0d6b9b8aa540ef18f9。复用已测试scripts/backup_completed_cloud.py，工具原字节SHA cd261143d85b91664b26d8b8582468f7171a64155f5d443ca535b579a2f47658，新配置和操作目录20261025_nocredit2030；工具部署backup_tools/completed_20261025。T550直连云端盘点正常，plan终态/保全/空间/目标不重复门禁通过，独立会话运行，具有全局与操作锁。证据supplementary_materials/reviews/cloud_backup_20261025/{backup_config,plan_execution,transfer_launch,startup_status}.json。目标/home/zz2/National_model_server/cloud_backup/20261014_case3nocredit_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1。旧备份只核manifest状态，不重复传输/全量哈希，不改源结果；未启动定时监听。新JSON解析、暂存diff/凭据检查通过；无源码变更，复用既有7项单测证据。下一步读取操作transfer_status，全部三层VERIFIED、目标逐文件bytes/SHA匹配和源身份不变后生成backup_manifest才可报告COMPLETE。异常时先核旧进程/锁再原操作续传。


## 2026-10-25深夜 两项目进度与nocredit备份完成

**2026-10-25英国23:40 GMT／10月26日北京07:40：云端2项RUNNING，nocredit备份已COMPLETE。** Case3 2040/5201318到417轮（6天00:40:06），PInf0.226/DInf3.09e-6/Compl0.00234，较上次388推进29轮；近407–417原始/互补降30.89%/31.58%，对偶升1.64%，22.85分钟/轮。C2050 t40/5207165到298轮（5天11:15:54），PInf50.9/DInf1.07e-4/Compl0.426，较279推进19轮；近288–298原始/互补降29.79%/31.62%，对偶增至原值8.70倍（增加769.92%），30.86分钟/轮。298轮对偶从8.40e-6跃至1.07e-4（12.74倍），尚无后续回落证据；其他两项仍降，无显式警告或错误，不能将互补改善等同于全指标稳定收敛。

Git基准b9ab0698a34f84fc12697486f296e138769ee2b8。只读squeue/scontrol/sstat/sacct及日志，stderr均0，Slurm峰712.44/621.18GiB未变；当前RSS约396.04/420.62GiB。仍无OPTIMAL，不给ETA、不改参数/作业。证据supplementary_materials/reviews/cloud_joint_progress_20261016/status_20261025T234041Z{,_summary}.json。

nocredit备份在2026-10-25T13:34:16.290807Z（北京21:34）完成，T1/T2/T3全部VERIFIED，93文件/5,510,708,567bytes，无延期文件，source_unchanged=true。最终backup_manifest文件清单与原plan逐项相等，源result_manifest SHA一致；本次取回完成证据cloud_backup_20261025/check_20261025T2340Z.json。目标/home/zz2/National_model_server/cloud_backup/20261014_case3nocredit_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1，磁盘仍约36.29%可用。完整逐文件bytes/SHA核验由单次备份进程完成，本次复核最终报告及清单，不重复传输。备份完成不代表最新扩展科学验收完成；原QC/作者待定标签不改。台账、交接、服务器记录同步追加；JSON解析/暂存diff与凭据检查，无源码变更不重跑求解。下一步询问时重点观察C2050对偶反弹是否恢复及两项终态，任何新终态按既定流程完整备份，无后台监听。


## 2026-10-26 nocredit后处理旁置完成

nocredit完整备份仍为2026-10-25已验证的93文件/5,510,708,567bytes，原output_8760未改变。当前result_manifest SHA c5566edafeae0cae5e4bd6b259a34a51f10ba4ec9e43745954ad8acb7a5c05a9与backup_manifest绑定值一致。新增旁置postprocess_20261026/pricing/screen_pricing_certificate.json（SHA4dfc8dce13c73cc72461be146c69990c0d81f26b4e73387a0dac6b022f9da2fa）及扩展评估/输入/evidence；证书未传回本机。B/obj=8.1423511193e-5、扩展PASS，严格标签不改。回执与报告见case3_2050_preparation_20261026及case3_2030_launch_20261014/nocredit_results_20261026。5201318/5207165仍RUNNING，其未来备份不标完成。


## 2026-10-26 Base2060筛选旁置

原完整备份未改，旁置screen_margin0p2_20261026已生成全量表/identity，P4同口径审核PASS。生产三列清单36686项，SHA 831514fdb19da9ffa0a4ccca40def435a3972f37db00284524916c1d8b6c9fc3；详情base_2060_screen_20261026/。14:05GMT另外两项仍RUNNING，终态备份尚未触发，无监听。

补充：Base2060三列生产清单向T550 ready/的额外旁置同步遇SSH255，随后只读核对在127.0.0.1:22 banner阶段超时，目标状态未确认。核心T550全量清单/identity与本地生产清单已经核验，不受影响；下一次连接恢复先核ready/已有文件与SHA，再按缺项续补。详见ready_t550_sync_status.json，不把这次额外同步标为完成。


## 2026-10-26 16:29 GMT T550恢复核验与遗漏同步补齐

Git起点1921b62efed0a71d3da18ee3b24cece86574fe36。T550 hostname已确认；先只读检查发现Base2060 screen_margin0p2_20261026/ready不存在，随后仅新建旁置目录并用exclusive-create写入缺失三文件，读回bytes/SHA与本地逐项一致。生产CSV 1,315,109bytes，SHA 831514fdb19da9ffa0a4ccca40def435a3972f37db00284524916c1d8b6c9fc3；另外两文件身份见base_2060_screen_20261026/ready_t550_recovery_20261026.json。此前ready_t550_sync_status.json连接失败证据原样保留；本条取代其中待恢复状态，不修改原输出。T550原全量CSV及nocredit完整证书SHA亦复核一致，未取回完整证书、未重新定价或求解。

16:29:05 UTC只读collect_live.py：5201318仍RUNNING，第467轮PInf0.0197/DInf2.43e-7/Compl1.74e-4；5207165仍RUNNING，第332轮PInf14.1/DInf1.00e-4/Compl0.120。两者AllocTRES=cpu64/mem750G/node1/billing64，UNLIMITED、Restarts0，stderr均0bytes，尚无solve_report。证据case3_2050_preparation_20261026/live_20261026T162906Z.json。未干预运行作业、未启动终态备份或监听。

原任务1–3及本次恢复补项已完成；4–5仍等待上游终态。下一步按NEXT_ACTIONS_ZH.md：2040终态后完整备份、T550证书及扩展评估，B/obj≤1e-2才采纳，再R1/1h/24h/2050参数/冻结/preflight，门禁全通过直接提交release；C2050终态只收尾，C2060/C′等待作者。验证为SSH身份、远端读回SHA、JSON解析、Git明确清单与diff检查；无源码变更，不重复模型测试。仅更新两份报告、恢复/作业JSON及四份交接台账；其他作者稿件和32行SI交接保留未暂存。

## 2026-10-26 19:43 GMT B2030提交与许可启动失败收尾

- **2026-10-26 19:43 GMT：B2030 Job5276670已提交/release但启动许可失败，停止重提。** 最终源码9f0a042、v2冻结/preflight和481回归/两道身份/参数门禁PASS；m4cg1603实配64CPU/750G/billing64、UNLIMITED。19:39:55–19:39:59 gp.Env.start报旧License2847107过期，尚未构建模型/无output_8760，无全年RSS/轮数指标。部署误沿用旧默认许可；记录已有10-20独立WLS路径，未读凭据，未自动重试。23文件/92,477,291bytes启动失败记录已T550逐项SHA备份COMPLETE，余36.2379%；不是完整解备份。下一步引用已登记WLS路径验证许可并新建v3；保留v1/v2、不重启旧Job、不碰保护作业。详见B review第9节。

- 执行源码：`9f0a042`（修复只读preflight与保全参数互斥），此前实现e2bb4fd、ba7a23f。最终测试481/159.093s/OK；Cross0路径不变，保存X成本项最大相对差1.64e-13、两方向交叉可行≤1e-8、开放柔性24h容量误差2.84e-14、relative_v1 BASIC_CROSSOVER PASS、2030参数与仅投资界改变核验PASS。
- 命令：`deploy_pilot.py prepare`、`preflight`、`submit-release`；405源码与58输入SHA校验，v2 release manifest SHA153d78c95caff43b72ea2a164e7068ca81565c8c4be12d54e4c2420640b7e1b0。held ReqTRES及实际AllocTRES均通过；作业5276670 FAILED/1:0，runtime4秒，no-requeue。≥700GiB检查分支通过但精确内存值未落盘；不将sacct batch MaxRSS=0解释为模型峰值。
- 失败原因：旧默认许可2847107已过期；本轮执行未引用2026-10-20登记的独立WLS，是部署疏漏。已有路径 `/publicfs01/fs1-a8/home/a8s001819/.config/gurobi/licenses/author_wls_20261020_f5e565f5/gurobi.lic`，本轮未读取内容/未再次验证。停止新增提交，不要求作者重新提供凭据，也不把旧许可失败推广为所有许可失效。
- T550：`/home/zz2/National_model_server/cloud_backup/20261026_basefrozen_2030_v9_agg0_t48_m750_tol1e4_v2`，backup_scope=STARTUP_FAILURE_NO_MODEL_OR_SOLUTION；23文件/92,477,291bytes，全部目标bytes/SHA与源前后身份一致。独立operation、全局/本地flock、rsync partial、空间门禁≥30%，完成后余36.2378568%。无output_8760，无有效解/扩展验收，不称完整环境镜像。
- 精确证据/提交清单：`supplementary_materials/reviews/base_frozen_B_20261026/deployment_v2/`、`startup_failure_backup.json`、`COMMIT_PATHS_launch_receipt.txt`；v1 preflight失败及v2许可失败均保留。其他作者未审稿件、32行SI交接仍不暂存。
- 下一动作：按任务失败停止规则回报；新v3应显式绑定现有WLS路径并先过许可门禁，启动资源元数据先于许可检查落盘。不得修改v1/v2/重启5276670。后续年份仍待作者线程决定，5201318/5207165与case3 2050未干预，无后台监听。
