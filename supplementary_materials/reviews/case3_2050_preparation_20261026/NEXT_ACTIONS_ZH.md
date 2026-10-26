# case3 2050 后续执行入口

授权来自 AGENTS.md「预先授权 case3 2050（2026-10-26）」与本次用户指令。本文不表示任何尚未完成的门禁通过；不创建后台监听或定时任务。5201318、5207165 在运行时只读。下一次执行先查询终态，尚在运行则保留准备状态。

两份备份配置已预置为 `backup_case3_2040_config.json` 和 `backup_C2050_config.json`，精确绑定当前两个 v2 release。它们尚未执行；终态后先核对源身份及旧操作，再在 T550 用 `backup_completed_cloud.py plan|run --config <对应配置>`，不得在当前 RUNNING 状态启动备份。

`package_identity.json` 的 `source_commit` 是准备时的 Git 基准 `0cbad43`，不是最终求解源码身份；该包仅含数据、profile和批处理，各成员由单独SHA绑定。本轮功能提交为 `3c11ed7`。最终冻结必须重新从当时已审查的完整commit导出源码，并重新生成release清单，不能把旧准备基准写成生产源码commit。

## case3 2040 / 5201318 终态后

1. 核对 Slurm 终态、`solve_report.json`、`preservation_report.json`、`result_manifest.json`，保留所有失败/部分导出。先查 T550 既有 manifest、操作锁和活跃传输；使用 `scripts/backup_completed_cloud.py` 的新显式配置执行单次可续传备份。全部 `output_8760` 和启动身份元数据均包含，预计空闲比例至少 30%，完成后逐文件 bytes/SHA、源身份和三层状态复核。
2. 在 T550 完整备份上运行 `scripts/price_screened_candidates.py --run-dir <2040_output_8760> --output <新的旁置证书目录>`，不得将原 MPS/BarPi 或完整证书传回本机。在备份旁运行 `scripts/assess_relative_v1.py`，包含 `archived_inputs` 的逐省及水库细节；保留严格口径、暂缓项和全部解。
3. 只有证书 `B_over_objective <= 1e-2` 才按预授权记录采纳；采纳文件参照前轮 `case3_2030_author_acceptance.json`，必须绑定这次 2040 的 result manifest、状态与证书实际 SHA。否则停止后继放行并报告，不能把自动 QC 标签当作删除或终止导出的依据。
4. 生成新的 R1 派生状态，不更改冻结 2040 输出。命令模板：

```text
python scripts/prepare_continuation_state.py --source <2040_output_8760> --acceptance <2040_author_adoption.json> --planning-year 2050 --source-scenario case3_thermal_ev_v5 --author-decision-label <采纳文件中的ACCEPTED_标签> --config config/optimization_numeric_dac_by_year_v9_a12.json --output <新R1目录>
```

5. 复用 `case3_2040_C2050_launch_20261019/run_continuation_gate.py`，使用新 profile `config/solver_profiles/barrier_stagea_screened_agg0_case3_2050_v1_threads40.json` 和 **`--same-scenario-continuation`**。筛选/不筛选 1h 构建分别在新目录执行，再执行 24h；均串行，不能使用 Base 2040 状态或 `--late-entry-base-state`。工程测试线程可沿用本地 8 线程预算，不得以工程线程数冒充正式生产 40 线程。

```text
python supplementary_materials/reviews/case3_2040_C2050_launch_20261019/run_continuation_gate.py --year 2050 --same-scenario-continuation --state <R1/planning_state_candidate> --solver-profile config/solver_profiles/barrier_stagea_screened_agg0_case3_2050_v1_threads40.json --hours 1 --output <screen_1h>
python supplementary_materials/reviews/case3_2040_C2050_launch_20261019/run_continuation_gate.py --year 2050 --same-scenario-continuation --state <R1/planning_state_candidate> --solver-profile config/solver_profiles/barrier_stagea_screened_agg0_case3_2050_v1_threads40.json --hours 1 --unscreened --output <unscreen_1h>
python supplementary_materials/reviews/case3_2040_C2050_launch_20261019/run_continuation_gate.py --year 2050 --same-scenario-continuation --state <R1/planning_state_candidate> --solver-profile config/solver_profiles/barrier_stagea_screened_agg0_case3_2050_v1_threads40.json --hours 24 --output <gate_24h>
```

6. 用现有 `mps_section_sha256` 和 `finalize_gates.py` 的检查口径，针对新输出生成独立汇总。筛选前后只允许 `BOUNDS_VRE_NEW` 不同；微小正容量区间数为 0；R1/v9_a12 调整逐列属于白名单。24h 必须 OPTIMAL，柔性服务最大残差 M ≤ 1e-3 GW/GWh，信用约束无越界，relative_v1 块存在，保全 COMPLETE（含候选筛选表、原模型、BarX/BarPi）。不能直接复用旧 `C2050_final_gates.json`，也不能只改旧报告标题。
7. 对实际构建出的 2050 参数核准：供暖/制冷/V1G/V2G 参与率 0.50/0.40/0.40/0.20，V2G 上限 120 GW；冷热签约 30 CNY/kW/年、释放 30 CNY/MWh；V1G 签约 30、搬移 20；V2G 可用性 30 + 设施 20、车主 100 + 退化 80；制冷/供暖/V1G/V2G 折减 0.50/0.45/0.40/0.40。来源：`../claude_workspace/tasks/PROMPT_release_nocredit_case3_2040_C2050_20261019.md` 第 4 节；现有 `parameters()` 已实现这些实际矩阵/数据核准。
8. 所有门禁通过后，审查提交源码，从该 commit 创建 **新的最终 release** `YYYYMMDD_case3_2050_v9a12_screen0p2_agg0_t40_m750_tol1e4_v1`（日期用实际冻结日）。预置目录只是数据/批处理准备，不能原地冒充冻结 release；复制或重新建立数据层时重新核对 SHA 与最终路径，避免 symlink 指向可变临时层。完整源码、输入、R1、参数和候选清单身份写入冻结清单。
9. 最终云端 preflight 通过后，按已授权范围提交并 release，无需再请求放行。先 held 核对 ReqTRES，再 release；实配必须 `cpu=64,mem=750G,billing=64`、UNLIMITED、no-requeue，Gurobi 与 OMP/OPENBLAS/MKL 都是 40。启动内存至少 700 GiB；许可通过既有安全路径由程序正常使用，不读取/复制凭据内容。记录启动、源码和输入 SHA、AllocTRES、启动内存、Job ID，保留全部失败尝试。

任一门禁失败或出现授权未覆盖的异常，停止该作业的放行并报告。短窗通过只代表工程门禁，不能保证全年收敛或不发生 OOM。case3 2060 未包含在此次提交授权内。

## C2050 / 5207165 终态后

按相同完整保全、T550 备份、T550 定价和扩展评估流程收尾，报告结果。C2060 与 C′ 均等待作者决定，不自动续接或启动。
