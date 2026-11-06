# Case3 2050 · v2

类型：COMPLETED_PRODUCTION；求解：OPTIMAL；验收：HARD_FAIL_PENDING_REVIEW；备份：COMPLETE。

完整运行身份：`20261027_case3_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2`。

远端目录：`/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20261027_case3_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2`。

## 本机入口

- [supplementary_materials\reviews\base_frozen_batch2_20261027\cloud_status_20261028T184833Z.json](<D:/codeenv/pycharmproject/National_RL/National_model/supplementary_materials/reviews/base_frozen_batch2_20261027/cloud_status_20261028T184833Z.json>)

[统一目录](<D:/codeenv/pycharmproject/National_RL/National_model/case_results/README.md>)。正式解、候选筛选解和失败记录的身份保持原样；不要把调试短窗当成全年结果。


## 2026-11-06 Case3 2050终态与T550备份启动

2026-11-06：云端1项RUNNING。Case3 2050/5294579于08:40:14 UTC COMPLETED/0:0，551轮OPTIMAL，总9天19:09:08，目标5698960.772742 million CNY，进程树峰值620.95GiB。终态PInf0.05514924/DInf2.2365e-6/Compl5.3748e-5。全部结果保全COMPLETE/errors=[]；原relative_v1 HARD_FAIL仅solver失败，已执行物理检查通过、水库按作者暂缓。尚未正式采纳：最大违反行index53400865（0.022921147，原单位待重构）与自身BarPi证书待核；不将C2050特例自动推广、不提交Case3 2060。T550恢复后确认无重复备份/传输，93文件5,510,971,992bytes单次自主备份已启动（PID3271938），当前RUNNING/T1传输，预计余量35.0642%；尚未校验完成。C2060/5318408第457轮，PInf2.02223/DInf1.07433e-5/Compl0.00318225，仍RUNNING，stderr空。

Git基准`5c7d308d47e274a0c0ba5998aa0b1d6fcca6087a`；命令、输入身份、输出与下一步见`supplementary_materials/reviews/case3_2050_completed_20261106/REVIEW_ZH.md`。只读查询与既定备份，未修改求解设置。


## 验收材料已取回

2026-11-06 Case3 2050备份已于10:24:24 UTC全部完成：93文件/5,510,971,992bytes，T1/T2/T3逐文件bytes/SHA均通过，源身份未变；32个验收源小文件1,211,740bytes已回本机并核验。Claude判断包 `supplementary_materials/reviews/case3_2050_completed_20261106/claude_review_package/README_CLAUDE_ZH.md`；原relative_v1 HARD_FAIL保留，行定位与自身BarPi证书仍待完成，未正式采纳。
