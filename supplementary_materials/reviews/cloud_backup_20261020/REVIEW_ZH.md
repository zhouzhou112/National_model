# 2026-10-20 已解生产结果补备份

作者要求整理此前 T550 备份，补齐全部已完成求解，并将每次云端求解结束后的备份固定为收尾工作。工作起点 Git `559f633`。

## 已核验

云端顶层 production release 的 `output_8760/solve_report.json` 共五套，均 OPTIMAL、preservation COMPLETE：Base2030/2040/2050/2060、Case3 2030。T550 已有前三套 COMPLETE manifest，path/bytes/SHA 与本地历史原验证逐项一致；本次不重复传输。没有活跃旧备份进程，连接正常。

复用 2026-10-12 的 T1/T2/T3 串行 rsync 与 SHA 工作流，新增通用入口 `scripts/backup_completed_cloud.py`：

- 显式 JSON 参数选择源、目标、operation 和 release，不再固定三个历史年份。
- 原路径或操作已存在时拒绝创建新 plan；全局和操作 flock 防并发。run 只续传既有 plan，部分文件保留。
- 在源端核对无活跃作业、已有 batch 终态标记、保全 COMPLETE；不以 OPTIMAL 或 QC 标签过滤已保全结果。
- 明确纳入全部 `output_8760` 与所列启动/身份/日志元数据，补充 case3/continuation batch 和 batch_exit；不读取凭据。
- 空间不足保留至少 30% 余量时停止；不静默延期 T3 后仍称完整。
- 逐文件 bytes/SHA 核对，传后复核源 manifest、大小、mtime 与原计划一致，再产生 COMPLETE manifest。没有重新运行模型或改科学参数。

七项针对性单测通过：路径穿越/重复 release、空间阈值、既有目标拒绝、SUBOPTIMAL/HARD_FAIL 完整保全结果可备份、活跃作业拒绝、未完成保全/缺终态拒绝、恶意 manifest 路径拒绝。T550 实际 plan/启动成功。

## 启动与当前状态

操作目录 `/home/zz2/National_model_server/cloud_backup/_operations/20261020_base2060_case3_2030/`，PID2833275，UTC16:06:17启动。两套184文件、10,828,735,197 bytes；预计完成后余量34.4127%。

UTC16:08快照：Base2060 T1已VERIFIED，Case3 T1传输中，进程存活；尚无最终backup_manifest，不宣称全部完成。T550独立运行，本机掉线不终止传输。完整传输日志保留在操作目录，任务未建立任何监听或定时服务。

另将Case3定价证书七文件、扩展relative_v1 JSON与证书身份检查，共九文件/6,223,488 bytes，按原字节同步到Case3备份旁`assessments_20261020/`，远端SHA已VERIFIED。原始接受标签、原云端输出与冻结包未改。

## 证据与下一步

`launch_evidence.json` 包含新计划、启动记录和旧三套manifest；`sidecar_manifest.json`、`sidecar_verification.json`记录旁置证书；`latest_status.json`记录当次传输快照。tar包和原始操作stdout/stderr只在本地保留，不混入Git。

授权固化于AGENTS，台账为根目录`CLOUD_BACKUP_REGISTER_ZH.md`；交接/服务器记录同步。下一次状态检查先读本操作status/manifest，若完成则核对六层和184项记录并追加完成证据；若ERROR则保留部分文件、诊断后在原操作续传，绝不盲目重复启动。其余三项RUNNING在确认终态后按相同规则执行。

后续同轮核验：两套T1均VERIFIED，共176文件/1,112,217,190 bytes；Base2060 T2传输中。当前仍RUNNING，不能称完整。只读查询入口为本目录collect_status.py，最新派生摘要progress_summary.json。


## 2026-10-20 本轮验收期间完成

最终状态COMPLETE，六层VERIFIED，184文件/10,828,735,197bytes，源身份不变。最终manifest已取回并逐项匹配原plan，无需重启传输。证据backup_completion_verification.json及completed_acceptance_20261020同名完整记录。两套现行扩展relative_v1均PASS，本机小文件验收包已完成。
