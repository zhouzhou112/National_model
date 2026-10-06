# 局部验证记录（自动由 result.json 汇总）

原始约束、变量界和对偶误差采用 1e-5 的既有严格质量门槛；城市层和小时业务检查同时通过才标记完整通过。
所有实验在同一台本地 i9-14900HX、Gurobi 13.0.2、8 线程下串行执行。局部窗口不代表全年运行。

| 测试目录 | 全年 CF 送出设计 | 终态 | 求解秒 | 原行最大误差 | 城市 QC | 小时 QC | 完整通过 |
|---|---|---|---:|---:|---|---|---|
| capped_nf2_24h_s0_cross0 | False | INCOMPLETE_ARTIFACT | — | — | — | — | False |
| capped_nf2_24h_s0_cross0_fullcf_final | True | SUBOPTIMAL | 35.172 | 5.557e-05 | HARD_FAIL | HARD_FAIL | False |
| cleaned_nf2_168h_s0_cross0 | False | OPTIMAL | 507.667 | 1.191e-06 | NOT_EVALUATED | NOT_EVALUATED | False |
| cleaned_nf2_168h_s0_cross0_fullcf | True | OPTIMAL | 501.531 | 5.153e-07 | HARD_FAIL | HARD_FAIL | False |
| cleaned_nf2_168h_s0_cross2_fullcf_final | True | TIME_LIMIT | 600.084 | — | NOT_EVALUATED | NOT_EVALUATED | False |
| cleaned_nf2_168h_s0_cross2_fullcf_final900 | True | OPTIMAL | 766.854 | 8.809e-07 | PASS | PASS | True |
| cleaned_nf2_24h_s0_cross0 | False | INCOMPLETE_ARTIFACT | — | — | — | — | False |
| cleaned_nf2_24h_s0_cross0_fullcf | True | OPTIMAL | 36.768 | 1.768e-08 | HARD_FAIL | PASS | False |
| cleaned_nf2_24h_s0_cross0_v2 | False | OPTIMAL | 42.516 | 2.394e-08 | NOT_EVALUATED | NOT_EVALUATED | False |
| cleaned_nf2_24h_s0_cross2_fullcf_final | True | OPTIMAL | 41.536 | 1.774e-11 | PASS | PASS | True |
| physical_nf1_24h_s0_cross0_fullcf | True | NUMERIC | 13.998 | — | NOT_EVALUATED | NOT_EVALUATED | False |
| physical_nf2_24h_s0_cross0 | False | NUMERIC | 41.104 | — | NOT_EVALUATED | NOT_EVALUATED | False |
| physical_nf2_24h_s0_cross0_fullcf | True | NUMERIC | 39.775 | — | NOT_EVALUATED | NOT_EVALUATED | False |
| rows_nf1_24h_s0_cross0_fullcf | True | NUMERIC | 14.800 | — | NOT_EVALUATED | NOT_EVALUATED | False |

早期目录 `capped_nf2_24h_s0_cross0` 的日志显示 Barrier OPTIMAL，但 MPS 压缩写出异常使 result.json 未完成，保留为不完整证据。
`cleaned_nf2_24h_s0_cross0` 在配置校验处退出，后续版本修正了显式科学基准 ID 的兼容校验；未进行求解。
早期 compute_max_cf=False 的结构测试不纳入生产送出设计的性能比较。
带 `_final` 的测试采用最终完整精确零小时识别；此前 fullcf 测试只对独立站小时识别精确零。
早期 Crossover=0 的解若只有小时 QC PASS、城市 QC HARD_FAIL，必须视为未完整验收。
矩阵跨度改善并不等于条件数已被证明健康；保留小的有意义既有容量与目标项。未构建或求解新的 8760h LP。
