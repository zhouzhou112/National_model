# Case3 2050 终态与备份记录（2026-11-06）

2026-11-06：云端1项RUNNING。Case3 2050/5294579于08:40:14 UTC COMPLETED/0:0，551轮OPTIMAL，总9天19:09:08，目标5698960.772742 million CNY，进程树峰值620.95GiB。终态PInf0.05514924/DInf2.2365e-6/Compl5.3748e-5。全部结果保全COMPLETE/errors=[]；原relative_v1 HARD_FAIL仅solver失败，已执行物理检查通过、水库按作者暂缓。尚未正式采纳：最大违反行index53400865（0.022921147，原单位待重构）与自身BarPi证书待核；不将C2050特例自动推广、不提交Case3 2060。T550恢复后确认无重复备份/传输，93文件5,510,971,992bytes单次自主备份已启动（PID3271938），10:15快照RUNNING/T1传输，预计余量35.0642%；尚未校验完成。C2060/5318408第457轮，PInf2.02223/DInf1.07433e-5/Compl0.00318225，仍RUNNING，stderr空。

## 证据与操作

- 基准Git：`5c7d308d47e274a0c0ba5998aa0b1d6fcca6087a`。本轮不修改模型、运行包或科学设置。
- 云端：`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20261027_case3_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2`。
- 本地终态：`terminal_source.json`（原始只读查询）、`terminal_summary.json`（精简判定）。sacct终态、solve_report、QC、preservation_report及result_manifest共同核对。
- T550目标：`/home/zz2/National_model_server/cloud_backup/20261027_case3_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2`。
- 操作目录：`/home/zz2/National_model_server/cloud_backup/_operations/20261106_case3_2050_completed`。
- 复用 `scripts/backup_completed_cloud.py`，SHA `cd261143d85b91664b26d8b8582468f7171a64155f5d443ca535b579a2f47658`；`plan/run --config backup_config.json`。独立session、全局/本地锁、可续传rsync、全层逐文件bytes/SHA校验、源身份复核；不建监听。
- 首次连接拒绝记录保留，用户恢复后已启动；初始状态见`backup_status.json`，10:18更新见`backup_progress_20261106T101834Z.json`，启动不等于完成。

## 下一步

复核备份T1/T2/T3和最终manifest全部通过，再在T550执行最大约束违反行重构、自身BarPi筛选证书和独立验收。只回传小文件。当前PInf超过现行0.01门槛，不自动改PASS；现有C2050条件采纳特例不直接套用于Case3 2050，先收齐证据再报告。验收后补11-05清单的T550分析。C2060保持只读。

10:18:34 UTC复核：T1/T2均VERIFIED，92文件/1,365,121,511bytes已校验，T3原模型4,145,850,481bytes传输中，最终manifest尚未生成。单次自主进程继续运行，无重复启动。


## 备份完成与本地交付更新

2026-11-06 Case3 2050备份已于10:24:24 UTC全部完成：93文件/5,510,971,992bytes，T1/T2/T3逐文件bytes/SHA均通过，源身份未变；32个验收源小文件1,211,740bytes已回本机并核验。Claude判断包 `supplementary_materials/reviews/case3_2050_completed_20261106/claude_review_package/README_CLAUDE_ZH.md`；原relative_v1 HARD_FAIL保留，行定位与自身BarPi证书仍待完成，未正式采纳。
