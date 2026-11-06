# Case3 2050：供作者与 Claude 判断的验收材料

本包是验收证据交接包，**不是 PASS 验收证书**。原始文件保持字节不变；当前结论 `PENDING_AUTHOR_REVIEW`，原始 `relative_v1` 为 `HARD_FAIL`。

## 已确认事实

- 作业 `5294579`；release `20261027_case3_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2`。
- 2026-11-06 08:40:14 UTC（英国时间）Slurm `COMPLETED/0:0`，551轮 `OPTIMAL`，总耗时9天19:09:08。
- 目标5,698,960.772741691 million CNY；Barrier PInf=0.055149240974，DInf=2.2365026266e-6，Compl=5.3747759770e-5。
- 原始 relative_v1 唯一失败类别为 solver：PInf 超过0.01门槛（约5.515倍）。原始 primal-dual 相对目标差0.0008251803，小于该检查0.01门槛。
- 已执行的物理相对检查均通过，包括功率平衡、GW/GWh、10-27 Mt类别、额外双向损耗等；水库水量逐站检查按作者规定 `DEFERRED_BY_AUTHOR_20261012`，不能称全部物理项已完成。
- Mt分母为 `annual_fossil_unabated_emissions_mtco2`=965.3492916891475 Mt；门槛0.0009653492916891475 Mt。CO2来源平衡残差0.0000756804371808274 Mt，在该门槛内。其余项以原始QC为准。
- 保全 `COMPLETE`，errors为空；完整备份于10:24:24 UTC完成，93文件、5,510,971,992 bytes；T1/T2/T3全部VERIFIED、逐文件bytes/SHA256核对、源身份未变，无deferred_files。

## 尚缺证据与决策边界

1. 最大约束违反0.022921146999578923，原约束索引53400865；原导出未查名称（`SKIPPED_MODEL_SIZE`）。尚未重构其行名、变量族、物理单位、年度或逐时量级及适用相对阈值。**不能仅凭索引与别案相同就认定为河北年度外送行。**
2. 尚未用此解自身 BarPi 计算筛选证书 B/obj。Barrier primal-dual gap 不能代替被筛选列的证书。
3. AGENTS.md 的2026-10-29 PInf条件披露规则明确针对C2050；本包不自动推广到Case3 2050。供作者判断是否在补齐行定位和证书后采用同类条件，或要求其他处理。
4. 年度电量汇总行如经定位证实适用，按现行规则 max(0.001 GWh,1e-6×该行年度电量)；当前本行单位与量级仍未知，不预判通过。
5. 未改写原QC、未正式采纳Case3 2050为上游、未启动Case3 2060；所有结果完整保留。

## 阅读顺序

- 本文件和 `acceptance_review_pending.json`：状态、已知异常与待决项。
- `source/output_8760/solution_qc.json`：严格及relative_v1原始验收；重点查看 `acceptance_profiles.relative_v1.checks`。
- `source/output_8760/solve_report.json`：终态、数值质量和索引；配合 `gurobi.log` 与 `solver_telemetry.jsonl`。
- `source/output_8760/preservation_report.json`、`source/backup_manifest.json`：保全与完整备份证据。
- `source/output_8760/model_config_snapshot.json`、`solver_parameters_before_optimize.json`、`run_identity.json`：科学设置、实际参数和身份。
- `collection_manifest.json`：本机32个源文件逐项bytes/SHA与T550备份manifest核验，全部通过。原始文件合计1,211,740 bytes（约1.21 MB）。

`terminal_summary_at_completion.json`保留首次终态快照，其备份RUNNING字段为历史状态；最新备份完成状态以本文件和 `source/backup_manifest.json` 为准。

大型MPS、BarX/BarPi、逐时调度仍在T550，不回传本机。后续行重构及证书应在T550只读执行：
`/home/zz2/National_model_server/cloud_backup/20261027_case3_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v2`

复现取回：运行上级目录 `collect_review_package.py`。脚本只读T550白名单文件并核SHA，不会启动备份或求解。源代码基准：c5f052d370f6cb047449ea665ce1dc4068beaf0d。
