# 云端生产求解与 T550 备份台账

更新：2026-10-20，最新查询时间见 `cloud_backup_20261020/progress_summary.json`。本表为当次核验快照，传输实时状态以 T550 操作目录中的 `transfer_status.json` 为准。

目标根目录：`/home/zz2/National_model_server/cloud_backup/`，每个 release 保持原相对路径。备份不等于科学采纳，不受 QC 的 PASS/FAIL/HARD_FAIL 标签影响。

| 项目 | release | 备份范围规模 | 本次核验状态 |
|---|---|---:|---|
| Base2030 | `20260914_base_v9_t48_m750_tol1e4_v3` | 87 文件；5,314,976,517 bytes | 历史 COMPLETE；当前 manifest 的 path/bytes/SHA 与历史逐项一致 |
| Base2040 | `20260919_base2040_v9_t44_m750_tol1e4_v1` | 87 文件；5,320,516,058 bytes | 历史 COMPLETE；当前 manifest 与历史逐项一致 |
| Base2050 | `20260930_base2050_v9_t48_m750_tol1e4_v1` | 88 文件；5,322,218,103 bytes | 历史 COMPLETE；当前 manifest 与历史逐项一致 |
| Base2060 | `20261012_base2060_v9a12_t48_m750_tol1e4_v1` | 91 文件；5,314,567,406 bytes | 新传输已启动，T1 的 87 文件/524,751,443 bytes 已 SHA VERIFIED；T2 传输中、T3 尚待完成 |
| Case3 2030 | `20261014_case3_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1` | 93 文件；5,514,167,791 bytes | T1 的 89 文件/587,465,747 bytes 已 SHA VERIFIED；T2/T3 尚待完成 |
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
- 完成标准：六个传输层全部 SHA VERIFIED、源身份复核不变、两套最终 `backup_manifest.json` 为 COMPLETE。当前尚未满足全部条件。
- 工具：`scripts/backup_completed_cloud.py`；显式配置：`supplementary_materials/reviews/cloud_backup_20261020/backup_config.json`。原 2026-10-12 工具与证据不改写。

Case3 2030 的 Claude 定价证书全套七文件、扩展 relative_v1 JSON、证书身份检查共九文件（6,223,488 bytes），已另外按原始字节同步到该 release 旁的 `assessments_20261020/`，全部 SHA VERIFIED。它们不改写冻结 `output_8760`，其独立 manifest 与验证见本次证据目录。

## 后续固定流程

每次确认云端生产求解结束，立即核对并补齐 T550 备份，无需作者再次提醒。保持现有“作者询问时检查”的方式，不增加定时监听；传输一旦启动可在 T550 自主完成。遇到中断先检查现有进程、锁和状态再续传，不盲目重复启动。

详情和操作命令见 `SERVER_RUNBOOK.md` 的“2026-10-20 完成求解后 T550 必做备份流程”；授权规则见 `AGENTS.md` 同日条目。
