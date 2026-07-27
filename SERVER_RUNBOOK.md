# CISPO 2030/8760 server runbook

## 2026-07-27 原始 LP 稀疏审计：仅本地闭合，不得据此扩大求解

本地提交 `6114157` 增加可选的 `--constraint-family-audit`。该开关仅在
`model.update()` 后读取原始稀疏矩阵，默认 `50,000,000` 个非零元是硬安全上限；
超过即停止审计，禁止为完整 744h/8760h 提高上限。它不改动任何变量、约束、
目标、场景、数据或 Gurobi 数值参数。`constraint_family_audit.json` 与结果目录
一起被 catalog 和 SHA256 manifest 记录，包含原始约束/变量族、最稠密 25 行/列，
以及求解日志的全局 presolve、ordering、`AA' NZ`、`Factor NZ`、`Factor Ops`、
Barrier/crossover 指标。不得把 Gurobi 的全局 presolve 删除量虚假归因给某个族。

本地 1h/24h 新根
`outputs/2030_{1h,24h}_v0727_constraint_family_audit_base_v3` 均满足
`OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，
波浪能开启、灵活负荷关闭，完整回归 `75/75`。24h 根为 raw
`231,074/345,992/1,729,035`、presolved `129,335/260,116/1,269,506`
（rows/columns/nonzeros），`AA' NZ=2.200e6`、`Factor NZ=6.284e6`、
`Factor Ops=7.399e8`、89 Barrier、57,741 crossover/simplex、29.107 s 和
0.712 GiB RSS。最稠密原始行是 `annual_emissions_accounting`（6,697）、
`capacity_margin_p65/p15`（6,491/5,736）和 `co2_source_balance_p*`（各 3,246）；
水电逐站平衡不是当前首要密集行来源。

这只是候选筛选，不是删约束许可。下一步仅为年度排放会计分解建立代数等价证明，
并在新的隔离 Base 24h 根上同机、同 profile 做一次 A/B。只有目标、全部 QC、
manifest、raw/presolved 尺度、factor、阶段时间、迭代和 RSS 都通过后，才可决定是否
运行 168h。未部署固定服务器、未查询或修改 ParaCloud；不得据此启动服务器 168h、
744h、8760h 或新的付费云任务。

## 2026-07-27 孤立梯级节点等价清理：仅本地已验收，禁止直接扩大求解

本地提交 `9787ba7` 不删除拓扑源数据或水电站：142 个节点、124 条边保持不变。只有 8 个已经核验为零度、单站的节点从逐小时核心梯级装配转入向量化独立水库平衡。它们没有上游到达流，其局部 GRFR 入流就是独立平衡的入流，因此物理方程、库容、弃水和可行域均不变；有效核心梯级站点行从 146 变为 138。任何多站孤立节点均会使建模硬失败，不能静默转换。

设置 `CISPO_WAVE_ROOT` 的本地完整回归通过 `71/71`；新的 Base 1h/24h 根
`outputs/2030_{1h,24h}_v0727_cascade_isolated_nodes_independent_base` 均满足
`OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`，波浪能开启、灵活负荷关闭。24h 目标相对清理前只差 `9.78e-09 million CNY`，raw/presolved 规模不变；但 `Factor NZ/Factor Ops` 从 `6.111e6/6.039e8` 变为 `6.284e6/7.399e8`，且 34.636 s 不优于 33.766 s。因此将其视为局部 Python 约束构建清理，不得宣传为 Barrier、内存或 8760h 优化。

本轮没有服务器或云端操作。后续如获单独授权，必须先实时复核固定服务器 checkout、CISPO/Gurobi 进程、`free -h` 和数据根，部署精确的已推送提交，再以全新隔离根运行一个单一的匹配 168h Base 门禁。不得并发、覆盖历史输出、启动固定服务器 8760h 或提交新的付费云任务。

## 2026-07-27 连续 RUC 等价瘦身：仅本地已验收，服务器操作需另行授权

本地实施提交 `3f2255a` 移除了连续 RUC 中四组严格冗余的逐小时上界行：
`online<=capacity`、`startup<=capacity`、`shutdown<=capacity`、`gross<=pmax*online`。
它们分别由保留的 S4-24、S4-25、S4-29 和变量非负下界蕴含；建模前硬校验
`min_up_h>=1`、`min_down_h>=1`、`pmin_fraction<=pmax_fraction` 及参数完整性。不得在
未保留这些行或未通过硬校验的分支上套用此说明。

本地完整回归 `69/69`，以及新建 Base 1h/24h 根
`outputs/2030_{1h,24h}_v0727_ruc_dominated_bounds_removed_base` 均为
`OPTIMAL + solution_qc=PASS + scenario_id=base + validate_result_manifest=True`；Base 波浪能开启、
灵活负荷关闭。24h 原始行数/非零元减少 `32,736/65,472`，变量和目标值不变；但 presolved
矩阵、`AA' NZ`、`Factor NZ`、`Factor Ops`、Barrier/crossover 迭代都完全相同。因此把它记录为
原始构建负担的等价缩减，不能以此声称 8760h Factorization 已加速或可行。

本轮没有服务器部署或远程写操作。只有用户另行授权后，才可按顺序：实时读取服务器
checkout/进程/内存/数据根 → 部署精确的已推送提交 → 用新的、隔离的含波浪 Base 输出根运行一个
匹配 168h A/B。不得并发求解、覆盖任何历史输出、启动固定服务器 8760h，或提交新的付费云端任务。

## 2026-07-27 新 Base：波浪能已整合；服务器尚未部署

当前仅允许两个可运行身份：

1. `base`：风电（含海风）、光伏、严格映射至既有 marine `grid_uid` 的波浪能；`flexible_load=false`。
2. `flexible_load_comfort_v3_v2g_5pct`：继承上述 Base，并启用 `comfort_envelope_v3` 冷热状态、EV V1G 和因果日内 5% V2G；它仍是参数待校准的敏感性。

提交 `c992550` 删除其余实验性 scenario JSON；不删除历史输出、数据或 Git 证据。两个当前身份都必须先设置 `CISPO_WAVE_ROOT`。本地 1h/24h 均已通过 `OPTIMAL + solution_qc=PASS + validate_result_manifest=True`，完整回归为 `66/66`；但这不构成服务器部署、更不构成 8760h 授权。新 Base 的全年静态预估为 36.47 GiB，柔性覆盖层为 37.63 GiB，不能用来判断 Barrier factorization。

旧服务器 wave-off Base 根一律保留且只作历史证据，不能作为重定义后 Base 的新门禁结果。若用户另行授权服务器测试，先实时复核空闲 checkout/进程/内存，部署精确推送提交，并且仅运行一个全新的、明确命名的 168h 根；固定服务器 8760h 和新付费云端任务仍禁止。

## 2026-07-27 全模块联合敏感性：本地门禁完成，服务器运行尚未授权

本地新增的 `wave_energy_medium_v1_flexible_load_comfort_v3_v2g_5pct` 同时启用波浪能、
`comfort_envelope_v3` 冷热、V1G 和 5% 日内因果 V2G。它是参数待校准的独立敏感性，
不是 Base；不得通过覆盖 Base JSON、环境变量或默认开关把它伪装为 Base。

本地 1h/24h/168h 已各自形成新根并通过
`OPTIMAL + solution_qc=PASS + validate_result_manifest=True`；168h 的 factor 结构为
`AA' NZ=2.162e7`、`Factor NZ=1.056e8`、`Factor Ops=8.603e10`。其全年静态 preflight
估计 37.63 GiB，但这不是 Barrier factor/workspace 的内存保证，更不是 8760h 授权。
详细输出、短窗口解释限制与结构优化次序见
`MODEL_COMBINED_MODULE_SOLVABILITY_AUDIT_20260727.md`。

禁止仅因该本地结果启动固定服务器 8760h、新付费云端任务或并发第二个求解。若用户另行
授权服务器比较，先实时核验空闲 checkout/进程/内存，并且只运行一个新的、明确命名的
168h 根；同机、同线程、同 solver profile 的 Base 对照是记录模块求解性增量的前置条件。

## 2026-07-27 Base 168h generic-wrapper manifest 门禁已通过

固定服务器在空闲且 clean 的 `c879c99` 上复核后，fast-forward 到已推送的
`67482ab`（其中 P0 实施为 `7499062`），并完成服务器 discovery 回归 `67` 项
通过、`2` 项可选 xarray 测试跳过。相对于原固定服务器模型实现，新增的唯一
模型邻接代码为 runtime-log manifest 排除；不得将它表述为 LP 或科学边界变化。

已完成且必须保留的新门禁根：

```text
/data/zz2/National_model/outputs/2030_168h_v0727_manifest_runtime_contract_base
```

命令使用 `barrier_16_auto_order_v1`、`Threads=16`、`SoftMemLimit=48`、
`Crossover=1`，将 wrapper 输出重定向到通用 `stdout.log`/`stderr.log`，并由
`/usr/bin/time -v` 记录端到端资源。终态为 `OPTIMAL + solution_qc=PASS +
scenario_id=base + validate_result_manifest=True`，Base 灵活负荷和波浪能均关闭；
所有 hard checks 通过。原始/预处理矩阵为
`1,393,915/1,011,079/9,797,949` 和 `729,559/817,723/7,001,232`
（rows/columns/nonzeros）；`AA' NZ=2.131e7`、`Factor NZ=1.036e8`、
`Factor Ops=8.436e10`。Gurobi 运行 614.894 s（161 Barrier、226,659
simplex/crossover），端到端 12:24.94，峰值进程树 RSS 3.453 GiB，未发生 swap。

`result_manifest.json` 明确排除 `run.pid`、`stdout.log`、`stderr.log`；最终
`validate_result_manifest()` 为真且无失败项，证明最终报告打印发生在 manifest
finalize 后时，wrapper 日志不会再污染科学哈希契约。这个 168h 根仅为
`TEST_ONLY_TRUNCATED_HORIZON`。不得写入、重建或原地修复旧
`2030_744h_v0726_spill_explicit_barrier16_auto_order`；不得启动固定服务器
8760h 或新的付费云端 8760h。

接下来 P2 若需要处理旧 744h，只能先设计名称明确、目录外且只读的
post-run audit manifest；只有研究协议明确要求原目录 result manifest 闭合时，
才可申请全新根的修正版 744h。P3 候选必须先在匹配 24h/168h 记录 raw/presolved
rows、columns、nonzeros、`AA' NZ`、`Factor NZ`、`Factor Ops`、phase time、
Barrier/crossover、objective/QC 与 RSS；不得以改变 Base 科学边界换取加速。

## 2026-07-27 manifest 契约 P0 在本地闭合

提交 `7499062` 修复通用 shell 重定向文件名缺口：`stdout.log` 和
`stderr.log` 均为 runtime-managed artifacts，已从科学输出目录及
`result_manifest.json` 排除；不改变任何科学模型设定。回归先 finalize
manifest，再向两类通用 wrapper 日志追加，并验证所有科学文件哈希仍可
验证。完整本地回归通过 `67/67`。

新的 Base 诊断根为：

```text
outputs/2030_1h_v0727_manifest_runtime_contract
outputs/2030_24h_v0727_manifest_runtime_contract
```

两者均为 `OPTIMAL + solution_qc=PASS + scenario_id=base`，manifest 闭合且
灵活负荷/波浪能关闭；24h 门禁有 342,343 个变量、262,201 条约束、1,771,702
个非零元、41.296 s 求解时间和 0.725 GiB 峰值 RSS。它们仅为 test-only
门禁。不得向旧 744h 目录写入。提交推送后，先重新核验固定服务器 checkout、
CISPO/Gurobi 进程和可用内存，再决定是否部署并启动一个新的 168h Base 根。
固定服务器 8760h 与所有新的付费云端 8760h 工作仍禁止。

## 2026-07-26 solvability-optimization campaign

The user has explicitly authorized sequential 744h or longer fixed-server stress
tests for the latest model, provided the host does not exceed safe memory. This
authorization supersedes earlier fixed-server 744h prohibitions in older entries,
but it does not authorize a fixed-server 8760h solve or another paid cloud run.

Required sequence:

1. preserve `supplementary_materials/**` user changes and commit only reviewed
   non-supplementary code/config/test/handoff files;
2. verify the fixed server has no CISPO/Gurobi process, then fast-forward the
   checkout to the exact pushed commit;
3. export the four versioned runtime roots and pass the complete server regression;
4. retain explicit spill: its matched 168h factor structure and telemetry memory
   are lower, and its 24h flexibility runtime is materially faster;
5. compare dual simplex, Barrier-16 and CPU-PDHG sequentially at 168h;
6. run only one 744h profile at a time, requiring at least 56 GiB available RAM
   before launch and using `SoftMemLimit=48`;
7. compare `build_report.json`, `solver_telemetry.jsonl`, `gurobi.log`,
   `solve_report.json`, `solution_qc.json`, process-tree peak RSS and `/usr/bin/time`;
8. stop further profiles after any memory hard failure or when available RAM falls
   below the gate. Never run multiple profiles concurrently.

The independent-reservoir spill projection in `6d84209` is mathematically exact,
but raw-column reduction alone is not an acceptance criterion. The matched 168h
projection is 1.84% faster, yet explicit spill has lower presolved rows/nonzeros,
lower `AA' NZ`, `Factor NZ`, `Factor Ops` and telemetry solver memory. Explicit
spill is also 24.0% faster in the paired flexibility case. Commit `9e82cc5`
therefore remains the default because 8760h is factor-memory bound. Preserve both
output roots and the audit at:

```text
/data/zz2/National_model/outputs/solver_comparisons/spill_168h_ab_v0726.json
/data/zz2/National_model/outputs/solver_comparisons/spill_168h_ab_v0726.csv
```

Solver profiles are numerics-only JSON files and are separately hashed in
provenance:

```text
config/solver_profiles/barrier_32_reference_v1.json
config/solver_profiles/barrier_16_sparse_amd_v1.json
config/solver_profiles/barrier_16_auto_order_v1.json
config/solver_profiles/dual_simplex_16_v1.json
config/solver_profiles/barrier_32_limited_presolve_fast_basis_v1.json
config/solver_profiles/barrier_32_force_dual_v1.json
config/solver_profiles/pdhg_cpu_32_v1.json
```

Run CPU PDHG only with Gurobi 13.0+ (the fixed server qualifies); local Gurobi
12 must not be used for that profile. Use `scripts/compare_solver_runs.py` to
write one JSON and CSV row per isolated output root.

Dual simplex is not a 744h candidate. The 168h run was stopped gracefully after
905.073 solver seconds and 421,470 pivots without a feasible basis, compared with
654.026 s for a complete Barrier-32 solution. Preserve its diagnostic root:

```text
/data/zz2/National_model/outputs/2030_168h_v0726_spill_explicit_dual_simplex16
```

Barrier-16+AMD completes 168h in 644.636 s with lower RSS, but AMD increases
factor nonzeros and operations. Do not promote it directly to 744h. First run
`barrier_16_auto_order_v1.json`, which changes only the thread limit relative to
the Barrier-32 reference.

The automatic-order control completes in 637.344 s and is the current Barrier
leader while preserving the reference factor structure. The first PDHG launch
root named `2030_168h_v0726_spill_explicit_pdhg_cpu32` is a pre-build config
failure, not a solve. Use a new output root only after the `pdhg_gpu` solver-key
whitelist regression passes on the server.

The corrected CPU-PDHG root is:

```text
/data/zz2/National_model/outputs/2030_168h_v0726_spill_explicit_pdhg_cpu32_v2
```

It was gracefully terminated after 3,074.134 solver seconds with no feasible
solution. The last telemetry record is near iteration 496,035; peak solver and
process-tree memory are only 1.990 GB and 2.503 GiB, but the terminal primal
residual is still about 49.5 and the dual residual is rising. Retain it as a
low-memory diagnostic, not as the first 744h profile.

The active one-at-a-time 744h gate is:

```bash
OUT=/data/zz2/National_model/outputs/2030_744h_v0726_spill_explicit_barrier16_auto_order
PID=663050
ps -p "$PID" -o pid,etime,%cpu,%mem,rss,vsz,stat,cmd
tail -n 100 "$OUT/stdout.log"
tail -n 20 "$OUT/solver_telemetry.jsonl" 2>/dev/null
ls -lh "$OUT"/{build_report,solve_report,solution_qc,result_manifest}.json 2>/dev/null
```

It uses clean server HEAD `c879c99`, the `city_337` data root,
`barrier_16_auto_order_v1`, `Threads=16`, `Crossover=1` and
`SoftMemLimit=48`. Available RAM was about 69 GiB at launch. Do not start a
second fixed-server solve. PID exit is not acceptance: require `OPTIMAL`,
`solution_qc=PASS`, a closed result manifest and inspection of process-tree
peak RSS, presolve/factor structure and crossover behavior.

The verified active-run structure checkpoint is:

```text
build: 341.673 s; 3,686,023 columns; 5,920,701 rows; 42,360,391 nonzeros
build peak process-tree RSS: 4.977 GiB
presolve: 223.80 s; 3,017,979 columns; 3,088,821 rows; 30,884,732 nonzeros
ordering: 115.48 s
AA' NZ: 6.449e7
Factor NZ: 8.062e8 (about 9.0 GB)
Factor Ops: 6.197e12
early telemetry peak solver memory: 25.087 GB
```

This passes the build/factor memory gate but is not solve acceptance. Continue
monitoring the Barrier residual trajectory and subsequent crossover; do not
infer success from factorization alone.

Barrier subsequently completed normally in 244 iterations and 8,917.48 solver
seconds with interior objective `2,196,881.94 million CNY`. The active run is
now in crossover:

```text
initial dual pushes remaining: 1,044,784
dual pushes remaining at solver time 9,860 s: 464,775
latest telemetry checkpoint: 358,606 simplex iterations at 9,996.25 s
current / peak solver memory: 13.948 / 25.087 GB
```

Do not treat the Barrier objective as the accepted LP result. Continue until
crossover and any primal cleanup finish, then require `OPTIMAL`,
`solution_qc=PASS`, a closed result manifest, `scenario_id=base` and final
process-tree memory/time evidence.

The run subsequently completed:

```text
status: OPTIMAL
objective: 2,196,881.920967378 million CNY
solver runtime: 13,541.717 s
Barrier / simplex iterations: 244 / 1,451,182
wall time: 3:52:03
peak process-tree RSS: 23.121 GiB
swaps: 0
solution_qc: PASS
scenario: base
```

Scientific checks pass, but strict manifest validation returns only
`size:stdout.log`. The manifest records 63,631 bytes and the completed file has
66,236 bytes. The launch wrapper used `stdout.log`, while
`RUNTIME_MANAGED_FILES` recognizes `runner_stdout.log`, `run.stdout` and the
sequence variants. Because the entrypoint prints the final solve report after
manifest finalization, hashing the generic redirected log creates a stale
manifest.

Preserve this output unchanged. Treat it as valid mathematical/QC and
performance evidence, but not as a closed reproducibility gate. Before any
replacement run, align the wrapper filename with the runtime-managed contract
or make a reviewed additive contract fix with regression coverage. Do not
silently regenerate the existing manifest or overwrite the terminal output.

## 2026-07-27 next-phase closure and scale-up gate

Live closeout state:

```text
fixed-server implementation HEAD: c879c99 (clean)
fixed-server CISPO/Gurobi process: none
fixed-server available RAM: about 69 GiB
ParaCloud active jobs: none
8760h accepted scientific result: none
```

Follow this order:

1. Make a minimal local manifest-contract fix. Generic wrapper files
   `stdout.log` and `stderr.log` must be runtime-managed/excluded, or the
   alternative design must prove they cannot change after manifest
   finalization. Add a regression that appends to a wrapper log after finalize
   and still validates every scientific file.
2. Preserve
   `/data/zz2/National_model/outputs/2030_744h_v0726_spill_explicit_barrier16_auto_order`
   byte-for-byte. Never regenerate its `result_manifest.json` in place.
3. Pass the complete local regression and new Base 1h/24h roots with
   `OPTIMAL`, `solution_qc=PASS`, `scenario_id=base` and a closed result
   manifest. Then, only on an idle clean fixed server, deploy the exact commit
   and run one new 168h Base root.
4. Do not rerun 744h solely because the wrapper log changed. Default to an
   explicitly named, directory-external, read-only post-run audit for the old
   result. Request a corrected 744h rerun only if the research acceptance
   protocol requires the original in-directory manifest to close.
5. For solvability work, compare candidate formulations/settings on matched
   24h and 168h cases before any 744h. Record raw/presolved rows, columns and
   nonzeros, `AA' NZ`, `Factor NZ`, `Factor Ops`, Barrier/crossover iterations,
   objective/QC equivalence and process-tree peak RSS. Do not change Base
   physics, temporal resolution, objective or constraints to obtain speed.
6. A new ParaCloud 2030/8760h solve requires separate explicit authorization,
   immutable code/data/scenario hashes, fresh 24h/168h gates, a reviewed
   high-memory node/thread/time-limit plan, estimated billed core-hours and
   termination rules. Never launch fixed-server 8760h.

Scientific work may proceed independently only behind scenario/accounting
boundaries: Base keeps flexibility and wave disabled; flexibility V3 requires
building/EV calibration and low/base/high tests; total 2025-2060 transformation
cost requires a discounted pathway ledger or an explicitly approved
multi-period objective; MGA cost-relaxation and point/province/national
complementarity follow an accepted Base scientific solution.

For Slurm deployments, request a termination warning such as
`--signal=B:TERM@300` and set the Slurm wall limit at least five minutes longer
than Gurobi `TimeLimit`. This lets the signal handler call `Model.terminate()` and
write a normal interrupted report. `solver_telemetry.jsonl` is flushed during
optimization and remains useful even if a later hard kill prevents final export.

Cloud job `4004585` is terminal `TIMEOUT`. It reached Barrier iteration 35 with
476.76 GiB sampled MaxRSS but remained far from convergence, and it produced no
acceptance reports. Preserve its output unchanged.

## 2026-07-25 Barrier-32 live factorization evidence

At `2026-07-25 20:30 CST`, job `4004585` has passed ordering and reached Barrier
iteration 23:

```text
Ordering time: 3180.53 s
AA' NZ: 7.425e8
Factor NZ: 3.848e10
estimated factor memory: 340.0 GB
Factor Ops: 2.448e15
Threads: 32
MaxRSS: 499,919,116 KiB = 476.76 GiB
```

The residuals are decreasing, but no accepted solution exists. Slurm ends the job
at `2026-07-26 02:34:26 CST`, about 6:04 after this checkpoint. Because the
Gurobi 86,400-second limit begins after model construction, the Slurm wall limit
will arrive first. Do not interpret a later scheduler kill as mathematical
infeasibility, and do not extend the paid allocation or start another job without
explicit authorization.

## 2026-07-25 active Barrier-32 full-year diagnostic

User-authorized ParaCloud job `4004585` is the only active full-year retry. It uses
the immutable `22fb493` Base/`city_337` release and the additive script:

```text
/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493/cloud_cispo_8760_2030_base_barrier32.sbatch
SHA256 fc604a1a25d37c9cff8a336c83969809cb5b52ea0ab815183d1ea3a7a96bfbf2
```

Relative to failed job `4003172`, change only:

```text
Gurobi Threads: 128 -> 32
Slurm CPUs/Task: 128 -> 32
job/log/output identity: new and isolated
```

Retain `Method=2`, `Presolve=2`, `Crossover=1`, `SoftMemLimit=640`, 700G,
24h and every scientific setting. The output root is:

```text
/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493/outputs/full_year_2030_base_22fb493_barrier32_700g_v0725
```

Initial evidence at `2026-07-25 02:35 CST`: job `4004585` is `RUNNING` on
`m4cg1702`; 50/50 tests pass; the generated config records `threads=32`.
Because 700G forced an allocation of 96 CPU/billing units, do not estimate this
run at only 32 billed core-hours per wall-clock hour. Monitor with:

```bash
squeue -j 4004585 -o '%i|%j|%T|%M|%D|%C|%m|%R'
sstat -j 4004585.batch --format=JobID,AveCPU,MaxRSS,MaxVMSize
tail -n 80 cloud_cispo_8760_base_b32-4004585.out
tail -n 80 outputs/full_year_2030_base_22fb493_barrier32_700g_v0725/gurobi.log
```

The failed 128-thread job consumed `CPUTimeRAW=2,642,304` allocated CPU-seconds,
or 733.973 core-hours; actual `TotalCPU` was only 7:03:11. Slurm exposes this
usage but not the ParaCloud paid-credit or remaining currency balance.

Do not start 2040 or another retry. Accept only after terminal Slurm state plus
`solve_report.json`, `solution_qc.json` and `result_manifest.json`; reaching
`Barrier statistics`/iteration 0 is diagnostic progress but not scientific
acceptance.

## 2026-07-25 cloud full-year OOM boundary

Job `4003172` is terminal `OUT_OF_MEMORY`; do not resubmit its batch script unchanged.
The build-only gate is still valid, but the real solve proved that build memory is not a
barrier-factorization memory estimate.

Terminal facts:

```text
state: OUT_OF_MEMORY
exit: 0:125
elapsed: 05:44:03
request: 128 CPU / 700G
recorded MaxRSS: 526.99 GiB
presolve time: 17,932.25 s
presolved model: 37,982,903 rows / 35,423,761 columns / 400,861,556 nonzeros
terminal stage: ordering before barrier iteration 0
```

The absence of `solve_report.json`, `solution_qc.json` and `result_manifest.json` is
decisive. Preserve the failed root:

```text
/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493/outputs/full_year_2030_base_22fb493_128cpu_700g
```

`Crossover=0` is not a remedy because crossover was never reached. Raising only
`SoftMemLimit` is also unsupported: Slurm killed the step before the configured 640G
soft limit was reported. The 750G-class node rebooted shortly after the event, while
accounting captured only 526.99 GiB; require administrator evidence before interpreting
that value as the true peak.

Before another paid full-year attempt, first choose and validate a lower-memory solver
route on bounded gates or secure a genuinely larger-memory node. Any new 8760h submission
requires a new output identity, explicit user authorization and monitoring through
presolve, ordering, factorization, barrier and QC. Do not start 2040 from this failed
2030 root.

## 2026-07-25 existing-grid correction and combined wave/flexibility cases

This section supersedes the nearest-offshore-wind routing language in the older
wave section below. `scripts/build_wave_energy_inputs.py` must produce contract
`wave_existing_grid_v2`: only coordinate-matched rows already present in
`optimization_points.csv` with `is_land=0` are eligible. Require 1,285 unique
`grid_uid` rows, exact route equality with `city_337/vre_routes.csv`, maximum
coordinate difference no larger than `0.02` degrees, and the recorded source/table
SHA256 values. Never map source rows outside the optimization grid to a distant
in-model anchor.

Two reproducible combined cases are available:

```text
config/scenarios/wave_energy_medium_v1_flexible_load_v1.json
config/scenarios/wave_energy_medium_v1_flexible_load_comfort_v3.json
```

Each combined file enables wave and flexible load in one LP. Comparative Base,
single-module and combined cases remain separate sensitivity-suite runs with
separate output roots. Deployment still requires an explicitly authorized,
versioned release and fresh tests/preflight/24h build and solve-QC gates.

## 2026-07-25 `wave_energy_medium_v1` local-only deployment boundary

The optional wave module is not present in any accepted fixed-server or cloud release.
Base must keep `features.wave_energy=false`. Enabling the scenario requires three
separately verified artifacts:

```text
config/scenarios/wave_energy_medium_v1.json
data/wave/wave_sites.csv
data/wave/wave_input_manifest.json
```

and the external hourly source:

```bash
export CISPO_WAVE_ROOT=/versioned/path/to/wave_energy
test -f "$CISPO_WAVE_ROOT/wave_grid.nc"
```

Rebuild the small site contract locally before transfer:

```bash
$PYTHON scripts/build_wave_energy_inputs.py \
  --wave-netcdf /source/path/wave_grid.nc \
  --output-directory data/wave
```

Require the source and site-table SHA256 values in `wave_input_manifest.json`.
Do not interpret the nearest offshore-wind routing anchor as a maritime boundary or
engineering cable route. Do not claim scenario-specific potential: the current source
potential is identical across all ten CF scenarios. The configured 2060 profile/cost is
an explicit 2050 hold.

After separate deployment authorization, use a new release and output root. First run
tests, wave preflight and a 24h build-only gate. A later 24h optimization must additionally
pass wave availability, power balance, reserve, load-center closure, cost, cohort and
manifest checks. Do not share offshore-wind spur/trunk in this scenario. A successful
local build is not permission for server/cloud 24h, 168h, 744h or 8760h execution.

## 2026-07-24 `comfort_envelope_v3` local-only deployment boundary

The V3 implementation is an independent sensitivity and is not present in the fixed-server
checkout or active cloud release. It requires both code and the ignored generated input:

```text
data/load/flexible_load_envelope_v3.csv.gz
data/load/flexible_load_envelope_v3.manifest.json
```

Rebuild locally from the recorded `Power_curve_V2` products with:

```bash
$PYTHON scripts/build_flexible_load_envelope_v3.py
```

The accepted local table has 1,357,800 rows and SHA256
`b5ebda4344a8f978606c242065159f27a75994a5d976f2cbe06038d66a429a03`.
The input manifest must record both the scenario table and its sidecar. Never stage only the
scenario JSON: a missing or mismatched envelope must hard-fail.

Main and optional V2G scenario files are:

```text
config/scenarios/flexible_load_comfort_v3.json
config/scenarios/flexible_load_comfort_v3_v2g_5pct.json
```

The 5% value means 5% of each province-day baseline EV peak power, not 5% vehicle
participation and not a policy mandate. Main V3 keeps V2G disabled. The V2G sensitivity uses
`daily_zero_causal`, so it cannot borrow energy from the end of a day.

After explicit deployment authorization, create a new versioned code/data/output identity and
first require:

```bash
$PYTHON -m unittest discover -s tests -q
$PYTHON scripts/run_cispo_planning_sequence.py \
  --scenario-config config/scenarios/flexible_load_comfort_v3.json \
  --diagnostic-hours 24 \
  --output-root /data/zz2/National_model/outputs/planning_sequence_24h_<version>_flexible_load_comfort_v3
```

Acceptance additionally requires four valid input/result manifests, four
`OPTIMAL + solution_qc=PASS` years, `flexible_load_formulation=comfort_envelope_v3`,
closed thermal state and V1G backlog transitions, zero daily terminal state/backlog, zero
simultaneous up/down, correct cost components and four `RESUMED_ACCEPTED` records. Validate the
no-V2G main scenario before separately testing the 5% V2G case. A successful 24h local gate is
not permission for server 168h/744h/8760h or cloud execution.

## 2026-07-24 `flexible_load_state_v2` deployment boundary

Implementation `271c6dc` is local-only. It adds
`config/scenarios/flexible_load_state_v2.json` and does not change the accepted Base,
`flexible_load_v1` or `flexible_load_v2g_v1` configurations. Never update an active
server/cloud checkout or reuse an accepted output root for this code.

The new module uses `Power_curve_V2` load components already present in
`hourly_load_2025_2060.csv.gz`. Heating/cooling have causal daily-reset equivalent
inventories; EV V1G has a causal daily-reset charging backlog. Do not relabel
`ev_hour_weight` as vehicle availability. Configuration validation intentionally rejects
V2G in this formulation until hourly availability, usable battery energy and departure
service are provided.

After explicit deployment authorization, first verify an idle clean server and use a new
checkout/data/output identity. Minimum gates are:

```bash
$PYTHON -m unittest discover -s tests -p 'test_*.py' -v
$PYTHON scripts/run_cispo_planning_sequence.py \
  --scenario-config config/scenarios/flexible_load_state_v2.json \
  --diagnostic-hours 24 \
  --output-root /data/zz2/National_model/outputs/planning_sequence_24h_<version>_flexible_load_state_v2
```

Require four `OPTIMAL + solution_qc=PASS` years, four valid result manifests,
`scenario_id=flexible_load_state_v2`, `flexible_load_formulation=state_envelope_v2`,
closed thermal/EV transitions, zero daily terminal state/backlog, no simultaneous
up/down, valid capacity-cohort hashes and four `RESUMED_ACCEPTED` records. Only then may
an explicitly authorized new 168h root start. The current full-year estimate is
43,356,367 variables/68,724,249 constraints/524,283,387 nonzeros; do not infer
fixed-server 744h/8760h or paid-cloud 8760h authorization from this estimate.

## 2026-07-24 local CF-fallback hardening deployment boundary

The local post-release change forbids cross-technology wind-to-PV CF fallback and adds hard preflight checks. It does not alter the currently staged cloud release and must not be copied into an active checkout or output root. Current production inputs already resolve all 45 wind primary-store gaps through same-grid `mixed_wind`; the patch therefore changes no current wind CF mapping or model scale. When deploying later, require a new versioned code/output identity, 54/54 local-equivalent tests, preflight checks `vre_cf_cross_technology_fallback=PASS` and `vre_cf_pv_fallback_uses_land_grid=PASS`, followed by new 24h and 168h gates.

## 2026-07-24 cloud execution state: accepted small gates and one authorized 2030 Base full-year job

The staged city_337 release now has accepted cloud gates `outputs/cloud_gate_24h_base_2030_22fb493` (`4003035`) and `outputs/cloud_gate_168h_base_2030_22fb493` (`4003045`). Both use the released code/data roots, `Threads=32`, pass 50/50 tests, reach `OPTIMAL`, pass QC and close their result manifests. Do not rerun into either root.

`4003088` completed the non-solving 8760h construction gate in 40m20s with exit `0:0`; its build report records 40,912,327 variables, 68,189,325 constraints, 515,040,080 nonzeros and 53.633 GiB peak process-tree RSS. The dependent real 2030 job `4003172` started normally on `m4cg1702`, using 128 CPU/700G/24h and root `outputs/full_year_2030_base_22fb493_128cpu_700g`. Its runtime configuration changes only `numerics.threads=128` and `numerics.soft_mem_limit_gb=640`; do not change any scientific model setting.

At 2026-07-24 21:17 CST, the solve job had completed the full model build in about 40m32s, entered Gurobi `Optimize`, and used 96.402 GiB batch MaxRSS. The log had not yet reached a presolve-complete line or barrier iteration. Continue monitoring Slurm accounting, Gurobi log and memory; `solve_report.json`, `solution_qc.json` and `result_manifest.json` were not yet present. Do not launch a successor planning year until the 2030 root is accepted.

## 2026-07-24 ParaCloud city_337 staged preflight (current cloud state)

The additive release is `/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493`; do not overwrite it. It contains code archive `National_model_22fb493.tar.gz`, the checksummed runtime roots `data/model_ready_20260723_v0722_city337`, `data/hourly_cf` and `data/hydro_timeseries_20260719_sequential_sparse`, and the source-to-cloud SHA256 manifest. The 2030 Base 8760h `--preflight-only` job `4001137` passed on a compute node with 175.17 GiB available memory; its scale is 40,912,327 variables, 67,604,064 constraints and 520,922,832 nonzeros. This proves neither model construction nor optimization.

Do not submit the staged `cloud_cispo_8760_preflight.sbatch` as a Gurobi build substitute. On 2026-07-24 the user-authorized `.bashrc` repair replaced malformed whitespace in its three proxy exports; its backup is `.bashrc.codex_backup_20260724_proxy_export`. Job `4002980` confirmed the proxy is inherited on `m4ci1905` and returns HTTP 302 through `172.16.110.3`; job `4002981` then completed the authenticated Gurobi WLS LP (`GUROBI_SMOKE_PASS`). Its short curl health probe timed out despite the successful solver authentication, so accept Gurobi's `Env.start()` plus `OPTIMAL` as the WLS gate. Retain explicit lower- and upper-case proxy exports in production batch scripts as defensive reproducibility.

Only after that smoke succeeds, use a new versioned 24h cloud root, then a new 168h root, both with `Threads <= --cpus-per-task`, full manifests and QC. A full-year `--build-only` is still a distinct later gate; it requires at least 96 GiB available memory and must not be treated as evidence that barrier factorization or a production solve fits. The raw GRFR source is deliberately not in this runtime release; add it only when running the separate raw-hydrology provenance readiness check.

## Accepted V0722 city_337 V2G gate

The Base, V1 and independent V2G 24h/168h gates are accepted for `city_337`. The accepted V2G 168h root `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v2g_v1` has four `OPTIMAL + solution_qc=PASS` years, four valid 59-entry manifests and four `RESUMED_ACCEPTED` records. The server is idle at checkout `cf39e0a` with data root `/data/zz2/National_model/data/model_ready_20260723_v0722_city337`. Revalidate without changing checkout:

```bash
OUT=/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v2g_v1
pgrep -af '[r]un_cispo_2030_full_year.py|[r]un_cispo_planning_sequence.py' || true
cat "$OUT/sequence_report.json"
```

The accepted chain has closed network/BECCS/security checks, V2G transition closure, zero simultaneous charge/discharge, explicit charging-loss accounting and an immediate four-year `--resume`. Keep `run.stdout`, `run.stderr` and `run.pid` as wrapper evidence. Do not launch fixed-server 744h/8760h.

## V0722 city_337 deployment and small-gate contract

Implementation `8e76753` changes the production spatial input contract from `natural_earth_278` to `city_337` and includes the reviewed 5% capacity-margin/3.5 s inertia baseline. Because `data/` is intentionally outside Git, deploy code and data as two independently verified artifacts. Never copy over the active V0721 data root.

Required new data files are `load_center_network/city_337/{load_centers,vre_routes,hydro_routes,intra_edges,initial_spur_capacity_2025,substation_initial_capacity_2025}.csv`; retain the package README, manifest, initialization audit and route comparison as sidecars. Verify the transferred archive SHA256 before extraction, copy the current data root to a new additive root, and extract only the `city_337` subdirectory there.

Before changing checkout, require `git status --short` empty and no `run_cispo`/Gurobi process. Then run, with the new data root and existing CF/hydrology roots:

```bash
$PYTHON -m unittest discover -s tests -p 'test_*.py' -v
$PYTHON scripts/preflight_cispo_2030.py --output /data/zz2/National_model/outputs/preflight_v0722_city337.json
$PYTHON scripts/run_cispo_planning_sequence.py \
  --diagnostic-hours 24 \
  --output-root /data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337
```

Accept only if all four years are `OPTIMAL + solution_qc=PASS`, scenario ID is `base`, flexibility is disabled, every result manifest closes, load-center outputs contain 337 unique nodes, center/province/capacity residuals pass, security manifests record 5% and 3.5 s, and `--resume` returns four `RESUMED_ACCEPTED` years. Only then launch the corresponding new 168h Base root. Current live memory (about 35 GiB available with swap occupied) is sufficient only for these small gates; do not launch 744h/8760h on the fixed server.

## V0722 reviewed reliability update — not deployed

The local working tree at Git HEAD `e28f315` changes the feasible set: Base provincial capacity margin is `5%`, and minimum system inertia is recorded as `3.5 s reference × 1.0 tolerance = 3.5 s effective`. Model construction and QC share one resolver; legacy scenario overrides may still provide `minimum_system_inertia_seconds`.

Local regression validation is 49/49 PASS. The local 1h engineering gate `outputs/2030_1h_v0722_security_5pct_inertia_3p5s` is `OPTIMAL + solution_qc=PASS` and its result manifest validates. The fixed server remains at accepted checkout `6ed943a`, so every existing server output predates this reliability update. Never reuse an accepted output directory with the new configuration. After an explicit commit/push/deployment decision, first verify an idle clean server checkout, then use a new versioned 24h root and require:

- `model_config_snapshot.json` contains capacity margin `0.05` and the two inertia fields;
- `scenario_manifest.json.security_parameters.minimum_system_inertia_seconds_effective = 3.5`;
- `solution_qc.json.minimum_system_inertia_seconds = 3.5`;
- capacity-margin and inertia hard checks both pass;
- the result manifest closes with no size/SHA256 mismatch.

Do not start fixed-server 744h/8760h or paid cloud 8760h from this local-only state.

## V0722 BECCS carbon-accounting gate

Local commit `c62b769` explicitly closes the CISPO-equivalent BECCS carbon mass balance while retaining the published negative factors, 90% capture assumption and all capture/transport/storage costs. It is not deployed on the fixed server. Before deployment, verify an idle clean checkout and use a new versioned 1h/24h output root; do not reuse any accepted Base/V1 directory.

Acceptance requires the four `solution_qc.json` fields `maximum_beccs_capture_balance_residual_mtco2`, `maximum_beccs_storage_balance_residual_mtco2`, `maximum_beccs_net_carbon_balance_residual_mtco2` and `maximum_captured_co2_reconstruction_residual_mtco2` to pass, plus all six explicit BECCS columns in `annual_resource_accounting_by_province.csv` and a closed result manifest. Baseline lifecycle emissions are zero. A nonzero lifecycle factor is a separate sourced scenario and must not be inserted into Base silently.

## V0722 diagnostic sensitivity suite interface

Local commit `c91828a` adds `scripts/run_cispo_sensitivity_suite.py` as a diagnostic-only wrapper around the existing four-year planning sequence. It does not authorize 8760h and is not deployed on the fixed server; live checkout `6ed943a` remains the accepted Base/V1 model gate. The wrapper gives every scenario an independent state chain, records catalog/config SHA256 values, rejects planned-not-runnable entries and refuses a non-empty root unless `--resume` passes exact suite identity checks.

List or dry-run the implemented scenarios before any solve:

```bash
$PYTHON scripts/run_cispo_sensitivity_suite.py --list-scenarios
$PYTHON scripts/run_cispo_sensitivity_suite.py \
  --diagnostic-hours 24 \
  --output-root /data/zz2/National_model/outputs/sensitivity_suite_24h_<version> \
  --dry-run
```

An actual small gate uses the same command without `--dry-run`; an audit of an accepted root adds `--resume`. Resume must match the mode, diagnostic hours, scenario order, catalog/base-config hashes and each scenario-config hash. The prior suite report is preserved under `sensitivity_suite_history/`, and new timestamped stdout/stderr logs are created rather than overwriting operational evidence. Base must report flexibility disabled, V1 must report V2G disabled, and V2G must remain a separate scenario/root. Do not deploy or start even this small gate until the server is idle and its exact checkout is verified; do not use this wrapper for fixed-server 744h/8760h or paid cloud 8760h.

## V0722 deployed scenario interface

Commit `6ed943a` adds optional, checksummed scenario overrides without changing Base by default and is deployed on the fixed server. The pre-deployment Base 168h gate ran from checkout `b6ca42d`, containing model implementation `0c1eaf2`. Do not mix code versions inside an existing output root.

After deployment, a flexibility gate is selected explicitly:

```bash
$PYTHON scripts/run_cispo_2030_full_year.py \
  --scenario-config config/scenarios/flexible_load_v1.json \
  --diagnostic-hours 24 \
  --output-dir /data/zz2/National_model/outputs/flexible_load_v1_24h_gate
```

Require `scenario_manifest.json`, `flexible_load_dispatch.npz`, `annual_flexible_load_by_province.csv`, `solution_qc=PASS` and a closed result manifest. Full-year Base/V1/V2G estimates are 40.91M/42.54M/43.36M variables respectively; retain the 96 GiB pre-build gate because the static estimate does not bound barrier factor memory.

The fixed-server four-year 168h V1 gate is accepted at `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_flexible_load_v1`. It completed in 1:06:54 with peak RSS 4,040,256 KiB and zero swap; every year is `OPTIMAL + solution_qc=PASS`, every 59-file result manifest validates, maximum daily heating/cooling/EV V1G residual is `8.17e-13 GWh`, and simultaneous up/down counts are zero. Revalidate the immutable chain only with:

```bash
$PYTHON scripts/run_cispo_planning_sequence.py \
  --scenario-config config/scenarios/flexible_load_v1.json \
  --diagnostic-hours 168 \
  --output-root /data/zz2/National_model/outputs/planning_sequence_168h_v0722_flexible_load_v1 \
  --resume
```

Acceptance of `--resume` requires four `RESUMED_ACCEPTED` records, the same `flexible_load_v1` scenario ID/SHA256, closed result manifests and matching `capacity_cohorts_v2` state hashes. Never rerun without `--resume` into these accepted directories. The fixed server remains restricted to small gates; do not launch 744h/8760h there. V2G is an independent optional scenario and must use a new output root.

## V0721 production I/O and acceptance contract

Implementation `0c1eaf2` remains the production I/O/state-acceptance baseline contained by the current fixed-server checkout `6ed943a`. Read `README.md` and `MODEL_IO_CONTRACT.md` before scheduling an expensive case. A case is accepted only when all of the following hold:

- `solve_report.json`: `status=OPTIMAL` and `result_use=SCIENTIFIC_PRODUCTION`;
- `solution_qc.json`: `status=PASS` and every hard check is true;
- `result_manifest.json` validates every scientific output by byte size and SHA256;
- `output_catalog.csv`, `output_data_dictionary.csv`, `model_config_snapshot.json`, `run_environment.json` and `input_manifest.csv` are present;
- the next planning year loads `planning_state/state_metadata.json` and verifies the source solve, source QC, cohort table and transition summary hashes.

Wrapper-owned files such as `run.stdout`, `run.time`, PID and scheduler logs must not be included in the scientific manifest because wrappers can append after model finalization. Preserve them next to the case as operational evidence.

The fixed server is limited to small regression gates for this phase. Use a new versioned output directory for 24h/168h, and do not launch 744h/8760h there. Production 8760h is reserved for the cloud compute node after Gurobi license, data hashes, current regression/smoke checks and 24h/168h solves have passed.

## V0719 capacity-bound/DC-sparse deployment gate

V0719 adds three required data tables and changes the in-memory reverse-flow index. It must be deployed only after the local working tree is committed and the currently active `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` task has completed or been explicitly preserved. Never rebuild the active `model_ready_20260719_sequential_sparse` directory in place.

After the implementation commit is pushed and the server checkout is fast-forwarded, create an additive data version and generate only the three new bound tables:

```bash
OLD_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260719_sequential_sparse
NEW_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260719_v0719_capacity_bounds
test -d "$OLD_DATA_ROOT"
test ! -e "$NEW_DATA_ROOT"
cp -a "$OLD_DATA_ROOT" "$NEW_DATA_ROOT"

cd /data/zz2/National_model/repo
PYTHON=/home/zz2/.local/envs/cispo-2030/bin/python
$PYTHON scripts/build_v0719_capacity_bounds.py --data-root "$NEW_DATA_ROOT"
export CISPO_DATA_ROOT="$NEW_DATA_ROOT"
$PYTHON scripts/smoke_test_data_package.py
$PYTHON -m unittest discover -s tests -q
$PYTHON scripts/check_server_readiness.py --require-raw-grfr --verify-raw-grfr-sha256
```

Acceptance requires 32/32 unit tests, 139/139 data smoke checks and readiness PASS. Confirm the generated national totals before solving:

- nuclear upper 2030/2040/2050/2060 = `110/205/300/300 GW`;
- battery floor 2030 = `65.85 GW`, later exogenous floors = 0;
- `bio+bioccs` shared capacity upper is never below inherited pair capacity; the current expected safeguard is Shanghai in four planning years.

Then run new output directories in order: 24h, 168h and corrected 744h. Each must report zero nuclear floor/upper violation, zero biomass/BECCS shared-capacity violation, zero storage-floor violation, zero AC simultaneous bidirectionality and zero DC reverse flow. Do not launch 8760 before corrected 744h acceptance and the 96 GiB available-memory gate.

## 2026-07-19 deployment note

Implementation commit `1b6da28` supersedes the previously deployed formulation. PID `3778049` completed mathematically `OPTIMAL`, but post-audit rejected it because the former QC did not fail 3,358 material AC bidirectional edge-hours. Do not reuse that result as a solver/model gate.

The corrected server gate `/data/zz2/National_model/outputs/2030_diagnostic_24h_20260719_cispo_flow_alignment_cpu` is `OPTIMAL/QC PASS`: zero AC bidirectional edge-hours, zero DC reverse flow on 363 DC edges and a closed scientific manifest. Server tests passed 26/26. A corrected 744h run is still required.

The updated data root must include `storage/phs_capacity_bounds_by_province_year.csv`. Use `config/model_input_files.json` as the minimal table contract. The code transfer archive must be created from tracked files after the implementation commit; do not package untracked workspace directories.

Production architecture is one continuous LP containing 2030 capacity decisions and all 8760 chronological hours. The 2025 data are boundary conditions only. No Benders decomposition, representative periods, or temporal weights are used.

## Server layout

- Repository: `/data/zz2/National_model/repo`
- Model-ready tables: `/data/zz2/National_model/data/model_ready`
- Capacity factors: `/data/zz2/National_model/data/hourly_cf`
- Hydrology: `/data/zz2/National_model/data/hydro_timeseries`
- Raw 2019 GRFR source: `/data/zz2/National_model/data/grfr_raw_2019`
- Python environment: `/home/zz2/.local/envs/cispo-2030`
- Gurobi Optimizer: `/home/zz2/opt/gurobi1302/linux64`
- Gurobi license: `/home/zz2/gurobi.lic` (mode `600`)
- Environment definition: `/data/zz2/National_model/repo/env/cispo-server.yml`
- Outputs: `/data/zz2/National_model/outputs`
- Logs and manifests: `/data/zz2/National_model/logs`, `/data/zz2/National_model/manifests`

The `/data` filesystem is NTFS/fuseblk and does not enforce normal Unix ownership or mode bits. Do not store SSH keys or `gurobi.lic` there.

Current versioned model and hydropower data:

```bash
export CISPO_CF_ROOT=/data/zz2/National_model/data/hourly_cf
export CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260719_v0719_capacity_bounds
export CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse
export CISPO_RAW_GRFR_ROOT=/data/zz2/National_model/data/grfr_raw_2019
```

The versioned data roots remain current. Fixed-server HEAD `b40900a` passes 34 regression tests, 139 smoke checks and the V0720 24h I/O-contract gate. Do not schedule another 744h run on this host.

## Long-term Git synchronization

- Bare remote: `/home/zz2/git/National_model.git`
- Local `origin`: `ssh://zz2@210.77.85.166/home/zz2/git/National_model.git`
- Active branch: `codex/cispo-2030-full-lp`

Normal local-to-server workflow:

```bash
# Local workstation
git pull --ff-only
git push origin codex/cispo-2030-full-lp

# Server working copy
cd /data/zz2/National_model/repo
git pull --ff-only
```

If code is edited on the server, commit and push it before pulling locally. Model data, capacity-factor Zarr stores, hydrology, outputs, licenses and environments remain outside Git.

## Environment and data gates

```bash
export CISPO_CF_ROOT=/data/zz2/National_model/data/hourly_cf
export CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse
export CISPO_RAW_GRFR_ROOT=/data/zz2/National_model/data/grfr_raw_2019
export CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260719_v0719_capacity_bounds
PYTHON=/home/zz2/.local/envs/cispo-2030/bin/python
$PYTHON scripts/check_server_readiness.py --require-raw-grfr --verify-raw-grfr-sha256
$PYTHON scripts/preflight_cispo_2030.py --output /data/zz2/National_model/outputs/preflight_2030.json
```

For the pending cascade version, the model-ready data root must include:

- `hydro/cascade_topology_nodes.csv`
- `hydro/cascade_topology_edges.csv`

The readiness gate now reports cascade node/edge counts, low-correlation lag edges, max-bound lag edges and maximum travel lag. A valid cascade server bundle should report 142 nodes, 124 edges, 4 low-correlation lag warnings, 18 max-bound lag warnings and no missing required cascade columns.

The server uses Gurobi Optimizer and `gurobipy` 13.0.2. Store the license file under the protected home directory, not `/data`. Do not commit the license file or activation key.

```bash
export GUROBI_HOME=/home/zz2/opt/gurobi1302/linux64
export PATH="$GUROBI_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$GUROBI_HOME/lib:${LD_LIBRARY_PATH:-}"
chmod 600 /home/zz2/gurobi.lic
$PYTHON scripts/check_gurobi_full_license.py
```

The license gate deliberately solves an LP with 2,501 variables. A size-limited fallback license must fail this check; package import or a two-variable solve is not sufficient evidence for production readiness.

Install test-only dependencies with `$PYTHON -m pip install -r requirements-test.txt`, then run `$PYTHON -m pytest -q`. The production dependency file intentionally excludes `pytest`.

As verified on 2026-07-06, direct server access to PyPI fails certificate-chain validation. Do not bypass TLS with `--trusted-host` or disabled verification. Download Linux/Python 3.11 wheels on a trusted workstation, record SHA256 hashes, upload them, and install with `--no-index --find-links=<wheel-directory>` until the institutional CA chain is repaired.

## Selectable optimization horizons

| Horizon | Hours | Intended use | Minimum available RAM |
|---|---:|---|---:|
| `one_month` | 744 | Local code/solver test only | 8 GiB |
| `six_months` | 4344 | Large integration test only | 32 GiB |
| `full_year` | 8760 | Production scientific run/build gate | 96 GiB |

The truncated horizons use the leading hours and a cyclic boundary over the selected interval. Annual investment costs, carbon limits and biomass limits are not rescaled. Their solutions therefore must not be interpreted as planning results.

Preflight without requiring Gurobi:

```bash
$PYTHON scripts/run_cispo_2030_full_year.py --horizon one_month --preflight-only
```

## Current 744h cascade gate

The active corrected gate is:

```bash
OUT=/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict
PID=$(cat "$OUT/run.pid")
ps -p "$PID" -o pid,etime,%mem,%cpu,rss,vsz,stat,cmd
pgrep -P "$PID" -a
tail -n 100 "$OUT/gurobi.log"
ls -lh "$OUT/build_report.json" "$OUT/solve_report.json" "$OUT/solution_qc.json" 2>/dev/null
```

It was launched from implementation `5a9f4ab` after the strict 168h gate reached `OPTIMAL/QC PASS`. At launch `/usr/bin/time` PID was `3344086`, Python child PID was `3344087`, and about 116 GiB RAM was available. Do not infer completion from PID exit alone; require both reports and inspect QC.

The old output below is a preserved failed numerical baseline and must not be reused:

```bash
OUT=/data/zz2/National_model/outputs/2030_one_month_hydro_cascade
PID=$(cat "$OUT/run.pid")
ps -p "$PID" -o pid,etime,%mem,%cpu,rss,vsz,stat,cmd
tail -n 100 "$OUT/gurobi.log"
ls -lh "$OUT/solve_report.json" "$OUT/solution_qc.json" 2>/dev/null
```

PID `244035` was normally interrupted on 2026-07-07 after `37,576.53 s`; it produced no solution. Do not delete this directory.

The following completed output is a preserved rejected baseline:

```bash
OUT=/data/zz2/National_model/outputs/2030_one_month_20260719_sequential_sparse_cpu
PID=$(cat "$OUT/run.pid")
ps -p "$PID" -o pid,etime,%mem,%cpu,rss,vsz,stat,cmd
tail -n 100 "$OUT/gurobi.log"
ls -lh "$OUT/solve_report.json" "$OUT/solution_qc.json" 2>/dev/null
```

Its former `solution_qc=PASS` is insufficient. Acceptance now additionally requires zero AC bidirectional edge-hours above `1e-6 GW`, zero DC reverse flow, closed load-center net exchange and a closed result manifest. CISPO's `0.001 yuan/kWh` flow penalty is configured as `1 yuan/MWh`; DC corridors have reverse UB zero, while AC corridors retain the S4-56 shared-capacity constraint.

Before launching the corrected 744h gate, require at least 64 GiB available RAM and verify that swap/shared jobs no longer leave the host under pressure. The rejected 744h reached 22.141 GiB peak process-tree RSS despite a lower preflight estimate.

Do not set `Crossover=0` for acceptance: the option was retested on the current corrected model and returned `SUBOPTIMAL`, maximum constraint violation 0.01355 and failed reservoir/directionality QC. `Threads=-1` exposes all 96 logical processors; Gurobi barrier uses the 48 physical cores. GPU-enabled Gurobi is installed only in `/home/zz2/.local/envs/cispo-gurobi-gpu`; it confirmed `Start PDHG on GPU`, but the same 24h P30 model was still iterating after about 600 s and was interrupted. CPU barrier remains the default route.

A diagnostic candidate using `FeasibilityTol=OptimalityTol=1e-6`, `BarConvTol=1e-7` and `Crossover=1` passed the current 24h QC in 37.38 s, about 7% faster than the strict local baseline. Do not promote it from 24h evidence: Gurobi warns that looser barrier termination can prolong crossover. Compare it at corrected 168h/744h and retain only if objective, capacity decisions and every hard QC remain acceptable.

`NodefileStart` does not solve this model's memory problem because this is an LP without branch-and-bound nodes. For normal production solves, benchmark default `DualReductions`/`InfUnbdInfo` behavior; use `DualReductions=0`, `InfUnbdInfo=1` and homogeneous-barrier diagnostics only after an infeasible-or-unbounded status. See `MODEL_SOLVABILITY_AUDIT_20260719.md` for the parameter matrix.

## Full model

The revised current-code projection is about 44.09 million variables, 68.19 million constraints and 515-524 million nonzeros. The old 744h factorization already used about 10 GB for factor nonzeros; linear extrapolation is about 118 GB for this component alone. Require at least 96 GiB available RAM for build-only, and do not optimize immediately after a successful build.

Build without optimizing:

```bash
$PYTHON scripts/run_cispo_2030_full_year.py --horizon full_year --build-only --output-dir /data/zz2/National_model/outputs/2030_full_year_build
```

Solve:

```bash
$PYTHON scripts/run_cispo_2030_full_year.py --horizon full_year --output-dir /data/zz2/National_model/outputs/2030_full_year
```

The runtime gate refuses to build when available memory is below the checked-in 96 GiB threshold. This is a build scheduling gate, not proof that barrier factorization fits. For infeasibility, the solve path writes `iis.ilp`; production constraints are not silently relaxed.

Successful solves additionally write `solution_qc.json`, compressed hourly province balances, technology dispatch arrays, station-indexed reservoir dispatch, transmission flows, annual carbon/CCS accounts and objective cost decomposition. A solution is not accepted as production output unless `solution_qc.json` reports `PASS`.

## Sequential 2030-2060 production path

After the revised 744h gate and 8760 build-only gate pass, run a single year as:

```bash
$PYTHON scripts/run_cispo_2030_full_year.py \
  --planning-year 2030 \
  --horizon full_year \
  --output-dir /data/zz2/National_model/outputs/planning_sequence/2030
```

Only `OPTIMAL + solution_qc PASS` full-year runs write `planning_state/`. The isolated sequential driver releases each year's process memory before the next year:

```bash
$PYTHON scripts/run_cispo_planning_sequence.py \
  --output-root /data/zz2/National_model/outputs/planning_sequence
```

Resume only already accepted years:

```bash
$PYTHON scripts/run_cispo_planning_sequence.py \
  --output-root /data/zz2/National_model/outputs/planning_sequence \
  --resume
```

The driver stops at the first non-optimal/QC-failed year. Do not manually copy an unchecked state directory or bypass its SHA256/year-boundary validation.
