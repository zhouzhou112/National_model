# OPS-Conservative 2040

Job 5613303 已release，截至2026-11-17T12:49:40.263885Z为PENDING；尚无全年结果或验收。

44线程/64CPU/750G，全部门禁和preflight通过，启动内存待节点分配核验。原件在云端独立release `20261117_opsconservative_2040_v9a12_t44_m750_tol1e4_v1`；详细门禁和放行报告见 `supplementary_materials/reviews/ops_flex_resource_sensitivity_20261114/batch3_conservative_20261117/LAUNCH_REPORT_ZH.md`。结束后备份及分析在T550，结果小文件再按既定清单归入本目录。

2026-11-18 12:27 UTC 更新：已于01:45 UTC启动，当前RUNNING；启动可用内存718.139 GiB，64CPU/750G分配、smoke与全年资源结构核验PASS。当前第108轮，尚无终态或验收。

2026-11-18 18:34UTC更新：COMPLETED/OPTIMAL，160轮，总耗时16:32:15；原结果保全COMPLETE、内置relative_v1与冻结容量检查PASS。18:36UTC由T550 PID3339359启动合并全量备份，当前RUNNING，正式验收/年度对偶恢复与小文件回传待全量SHA校验完成。

2026-11-18 23:59UTC收尾核验：全量备份已于19:03:46UTC完成；三层逐文件bytes/SHA全部VERIFIED，当前云端manifest仍一致。正式T550验收、年度核算行对偶恢复及结果小文件回传仍待执行。

2026-11-19验收更新：当前relative_v1 PASS，原严格标签不改；恢复1134条年度核算行对偶、T550只读分析完成，验收包和结果小文件已回传且SHA全匹配。正式记录见本目录acceptance_resource_batch3_20261119/acceptance_record.json，作者采纳仍待审阅。
