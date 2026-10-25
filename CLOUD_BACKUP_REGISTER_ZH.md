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
