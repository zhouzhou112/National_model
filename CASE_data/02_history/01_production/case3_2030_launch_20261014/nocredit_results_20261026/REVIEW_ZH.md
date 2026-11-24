# nocredit 2030 收尾复核（2026-10-26）

## 结论

Job 5153901 原始报告为 OPTIMAL，保全 COMPLETE。完整 T550 备份为 COMPLETE：93 文件、5,510,708,567 bytes；本轮复核 backup/result manifest 身份一致，未重复传输完整备份。扩展口径 `relative_v1_author_20261014_extended` 为 **PASS**；原严格 HARD_FAIL 与水库暂缓项继续保留，自动验收不替代作者采纳，也不影响完整保全。

本机取回 `output_8760/` 下全部不超过 32 MiB 的文件，共 73 个、105,175,467 bytes。72 项逐项匹配原 result manifest 的 bytes/SHA；manifest 自身与 T550 完整备份所绑定 SHA 一致。包括 annual_flexible_load_by_province、装机表、cost_components、annual_summary、状态与原模型/checkpoint身份文件。8 个超过阈值的大文件留在 T550，逐项路径和大小见 `collect_receipt.json`，没有删除或省略完整备份。

## 三方目标与原对偶差

成本单位为 **million CNY/年（2025 不变价）**，表中原对偶差来自各原始 `solve_report.json` 的最终 durable Barrier 记录。三方均为 2030 年、8760 小时、31 省系统规划；目标为模型年化投资及运行成本。容量/功率 GW、电量 GWh；本次仅后处理，不改变变量、约束、目标、时空尺度或输入。

|情景|原始目标 P|原始对偶 D|P−D|相对原对偶差|筛选上界 B|
|---|---:|---:|---:|---:|---:|
|Base|4192778.836193|4192472.473058|306.363135|7.3069233e-05|0.000000|
|nocredit|4189002.976255|4188728.502285|274.473970|6.5522505e-05|341.083331|
|case3|4188026.777763|4186695.141629|1331.636135|0.00031796266|347.782068|

三方 solve_report 均在 T550 对原 result manifest 重新核验，路径/SHA见 `../../case3_2050_preparation_20261026/compare_receipt.json`；精确数值见 `objective_comparison.csv`。case3 的 B 复用已确认的 2026-10-19 Claude 证书（与现存归档目标一致），未重新求解。

节省区间严格使用 `[D_Base − P_X, P_Base − D_X + B_X]`。1 亿元 = 100 million CNY。

- nocredit 相对 Base：点差 37.758599 亿元/年；按作者公式的节省区间 [34.694968, 43.914172] 亿元/年。
- case3 相对 Base：点差 47.520584 亿元/年；按作者公式的节省区间 [44.456953, 64.314766] 亿元/年。

nocredit 与 case3 的目标点差为 9.761985 亿元/年。该点差同时受各解原对偶差与筛选上界影响，不把它直接写成精确的容量信用因果贡献。工程对偶按 `BARRIER_DUAL_ENGINEERING_GRADE`、BarConvTol=1e-4 披露。

## T550 定价证书

用 `scripts/price_screened_candidates.py` 在完整备份上运行，直接读取原 MPS 和原顺序 BarPi，校验 archive/checkpoint/semantic manifest。B = 341.083330725 million CNY，B/obj = 8.1423511193e-05，近优性 `ACCEPT`，比较用途 `INTERVAL_WITH_B`。公式为被筛掉站点原新增上界乘以负配对约化成本的正部之和，未更改筛选规则或重新求解。

完整证书与定价 CSV **仅保留在 T550**：`/home/zz2/National_model_server/cloud_backup/20261014_case3nocredit_2030_v9_screen0p2_agg0_t48_m750_tol1e4_v1/postprocess_20261026/pricing/screen_pricing_certificate.json`；证书 SHA256 `4dfc8dce13c73cc72461be146c69990c0d81f26b4e73387a0dac6b022f9da2fa`。本机只有数值/路径/SHA回执 `case3_2050_preparation_20261026/price_receipt.json`，未取回完整证书、MPS 或 BarPi。

## 扩展评估与复现

`scripts/assess_relative_v1.py` 在 T550 运行，按原逐时省平衡和水库数组计算 `archived_inputs`，源文件评估前后 SHA 一致。独立结果在 `assessment/solution_qc_relative_v1.json`，输入与核验链在同目录；原 `output_8760/solution_qc.json` 未改写。扩展项按既定 max(严格容差,1e-3 GW/GWh)，双向流按额外损耗/全年负荷≤1e-4；水库记录最差残差及库容并按作者决定暂缓，严格标签继续保留。

本轮入口为 `python supplementary_materials/reviews/case3_2050_preparation_20261026/remote_work.py collect|price|assess|compare`，每个动作单独执行；已有结果拒绝覆盖。具体远端命令、工具 SHA、源 SHA、接收字节核验见各 receipt。无随机采样，无新优化，不涉及随机种子。

## 差异与限制

旧作者决定中case3区间上界简记为64.32亿元；本轮按原归档高精度P/D/B重算为64.314766亿元（保留两位为64.31）。原记录保留，本报告明确采用表内原始高精度值，不修改公式或科学结果。

“全部小文件”以 ≤32 MiB 明确定义；完整结果仍由 T550 93文件备份覆盖。本机原始取回数据约105MB不全部发布到Git，Git保留报告、精确对照表、SHA清单与独立评估。当前报告不启动 nocredit 后继年份，不干预5201318、5207165。
