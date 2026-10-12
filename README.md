# National CISPO-style power-system planning model

This repository implements a continuous linear capacity-expansion and chronological-dispatch model for China's 31 provincial regions. The production horizon is one continuous 8760-hour year. The model is intended for reproducible research: every accepted case records its exact inputs, configuration, solver environment, outputs, hard QC and SHA256 manifest.

2026-10-06 GitHub同步说明：`main`与当前审查后的工程工作分支已同步；云端运行包保持冻结，不随Git更新。8760h初筛通过五轮每轮成本门槛，A/B/C当前数值候选未晋级，均不代表科学QC接受。详见[版本差异与提交范围](supplementary_materials/reviews/git_sync_20261006/REVIEW_ZH.md)、[同步结果](supplementary_materials/reviews/git_sync_20261006/SYNC_RESULT_ZH.md)和[后续同步约定](GIT_SYNC_POLICY_ZH.md)。原始数据/大规模运行输出及未审核稿件未随本次Git发布。

2026-10-02 当前顺序：正在运行的 Base 保持不动；下一轮优先 Base＋冷热＋V1G/V2G，从 2030 独立求解至 2060。见 [当前情景执行计划](SCENARIO_EXECUTION_PLAN_20261002.md) 和 [文档/代码版本使用边界](DOCUMENT_STATUS_20261002.md)。对偶筛选尚属隔离验证，不能把初筛候选集当永久资源删减。

## Scientific boundary

- `2025` is a fixed boundary state, not an optimization year.
- Planning years are solved sequentially as `2030 -> 2040 -> 2050 -> 2060`.
- Each planning year is a separate 8760-hour LP. Accepted model-built cohorts pass to the next year and retire by technology lifetime.
- `24h`, `744h` and `4344h` horizons are engineering gates only. Annual flow accounts (net-carbon limit, DAC throughput, biomass fuel and CO2 sink injection) use `optimization_hours/8760` scaling, while annualized capacity and fixed costs remain unscaled. Leading-hour diagnostics are not representative years, so their capacities, objective and energy totals are not planning results.
- The production formulation is `full_year_monolithic_lp`; representative periods and decomposition are not used.

The full mathematical specification is in [cispo_full_lp_model_spec.md](cispo_full_lp_model_spec.md). Current validated implementation and server evidence are in [CODEX_HANDOFF.md](CODEX_HANDOFF.md).

The current demand-flexibility research design compares Base with thermal-only, EV-only and combined optional V5 portfolios. See [the contracting and qualification contract](config/FLEXIBLE_PORTFOLIOS_V5_CONTRACT.md). Legacy V5 remains reproducible; full-system nonbasic annual qualification is still pending.

The production spatial layer is `city_337`: 337 city-level load centers and a 642-edge within-province network. The retained 278-node Natural Earth layer is a replication/sensitivity input only. For a browser-reviewable code-and-data index, see [GITHUB_WEB_REVIEW_GUIDE.md](GITHUB_WEB_REVIEW_GUIDE.md).

## Repository layout

| Path | Purpose |
|---|---|
| `cispo_model/` | Configuration, strict data loading, model construction, diagnostics, exports and sequential state transfer |
| `config/` | Research assumptions, input contract and solver configuration |
| `scripts/` | Data-package builders, readiness checks and run entrypoints |
| `tests/` | Unit and structural regression tests |
| `data/` | Generated model-ready inputs; ignored by Git because of size |
| `outputs/` | Per-case results; ignored by Git |
| `env/`, `requirements-*.txt` | Reproducible Python/Gurobi environment definitions |
| `supplementary_materials/` | Paper evidence and supplementary documents; not required to run the model |

No production model input is silently inferred from `supplementary_materials/`.

## Environment

The validated server environment uses Python 3.11 and Gurobi 13.0.2.

```bash
conda env create -f env/cispo-server.yml
conda activate cispo-2030
```

Large time-series stores remain outside the code checkout. Set these paths before running:

```bash
export CISPO_DATA_ROOT=/path/to/model_ready_data
export CISPO_CF_ROOT=/path/to/hourly_cf
export CISPO_HYDRO_ROOT=/path/to/hydro_timeseries
export CISPO_RAW_GRFR_ROOT=/path/to/raw_grfr_2019
export GRB_LICENSE_FILE=/path/to/gurobi.lic
```

The exact required table list and roles are defined by `config/model_input_files.json`. Run the read-only readiness gate before a solve:

Parameter authority, scenario overrides and sensitivity rules are documented in [config/README.md](config/README.md). Implemented versus planned case modules are separated in [SCENARIO_MODULE_ARCHITECTURE.md](SCENARIO_MODULE_ARCHITECTURE.md).

```bash
python scripts/check_server_readiness.py --require-raw-grfr --verify-raw-grfr-sha256
python -m unittest discover -s tests -q
```

## Running one case

Preflight without building the Gurobi model:

```bash
python scripts/run_cispo_2030_full_year.py \
  --planning-year 2030 \
  --horizon full_year \
  --preflight-only \
  --output-dir outputs/2030_full_year_preflight
```

Small local regression solve:

```bash
python scripts/run_cispo_2030_full_year.py \
  --planning-year 2030 \
  --diagnostic-hours 24 \
  --output-dir outputs/2030_24h_regression
```

The only demand-flexibility overlay is the recorded V3+V2G partial override; both
Base and this overlay require `CISPO_WAVE_ROOT` to point to `wave_grid.nc`:

```bash
python scripts/run_cispo_2030_full_year.py \
  --scenario-config config/scenarios/flexible_load_comfort_v3_v2g_5pct.json \
  --planning-year 2030 \
  --diagnostic-hours 24 \
  --output-dir outputs/base_wave_flexible_v3_v2g_5pct_24h_gate
```

Production solve:

```bash
python scripts/run_cispo_2030_full_year.py \
  --planning-year 2030 \
  --horizon full_year \
  --output-dir outputs/2030_full_year
```

An output is scientifically accepted only when `solve_report.json` is `OPTIMAL`, `solution_qc.json` is `PASS`, `run_scope.json` says `SCIENTIFIC_PRODUCTION`, and every entry in `result_manifest.json` matches its SHA256.

## Sequential planning years

```bash
python scripts/run_cispo_planning_sequence.py \
  --output-root outputs/planning_sequence_2030_2060
```

Sequential planning deliberately reduces peak memory: only one 8760-hour LP is resident at a time. A four-year perfect-foresight joint model would add inter-year coupling and roughly multiply the chronological variable/constraint volume; it is therefore not the default architecture. The trade-off is that sequential planning is myopic rather than perfect foresight.

Each accepted full-year case exports a checksummed `planning_state/` bundle. The next year refuses a stale year, altered cohort file, non-PASS source QC or non-production source solve.

## Result interface

Every solved case is self-describing:

- `input_manifest.csv`: resolved paths, sizes and SHA256 for tabular/hydrology inputs; Zarr metadata fingerprints for CF stores.
- `model_config_snapshot.json`: exact year-specific configuration.
- `run_environment.json`: command, Git revision, worktree state, packages and data roots.
- `output_catalog.csv`: one row per scientific output file.
- `output_data_dictionary.csv`: one row per CSV column, JSON key or NPZ array, including shape/dimensions/unit inference.
- `result_manifest.json`: final SHA256 integrity manifest.

The stable schema and interpretation rules are documented in [MODEL_IO_CONTRACT.md](MODEL_IO_CONTRACT.md).

## Cost interpretation

For a full 8760-hour planning-year case, the objective is `million_CNY_per_year`: annualized capacity cost (`CapEx * CRF`) plus fixed O&M for installed assets, and 8760-hour variable O&M, fuel, startup/shutdown, ramping, storage, flow and optional flexibility costs. It is a target-year annual-system objective, suitable for a static capacity-expansion comparison. The sequential `2030 -> 2040 -> 2050 -> 2060` workflow transfers physical capacity cohorts but does **not** minimize a discounted 2025-2060 pathway NPV. A pathway-total study must use either a multi-stage discounted investment formulation with incremental `CapEx * ΔK`, or a separately declared ex-post accounting ledger; do not combine lump-sum CapEx and CRF for the same investment.

## Development rule

Do not change units, time resolution, spatial resolution, objective terms, capacity bounds or scientific assumptions without updating the configuration/specification, regression tests and `CODEX_HANDOFF.md`. Long solves must pass a small diagnostic gate first.


## 2026-10-12 当前共识入口与历史口径更正

权威依据：`RESEARCH_DESIGN_CONSENSUS_20261012.md` 全文与 `AGENTS.md` 2026-10-12 两节；冲突以共识为准。下列引用逐字摘录共识，不重新计算数值。历史条目保留，仅供追溯，不构成新的执行授权。


当前研究与执行以 `RESEARCH_DESIGN_CONSENSUS_20261012.md` 和 `AGENTS.md` 2026-10-12 两节为准。旧条目中的 V4 主情景、case1/case2 后补、Late-entry 待定、Stage B/basic solution 强制要求、严格 QC 否决导出等均不再定义当前任务。

> ## 3. 求解、验收与数据保全
>
> - 求解：Stage A，即 Barrier、Crossover=0、BarConvTol=1e-4、NumericFocus=2、48 线程，不执行 Stage B。case3 是否沿用 Base 的 Presolve=2/Aggregate=1，取决于夜间数值实验（第 6 节）。
> - relative_v1：功率平衡、成本闭合、双向流（额外损耗 ≤ 全年负荷的 1e-4）、水库（暂缓）四项已实现。**扩展（2026-10-12 决定，case3 启动前实现）：** 其余所有以 GW/GWh 计的物理残差检查，包括冷热和 EV 库存、V2G、信用上界、波浪、储能，判据改为 max(严格容差, 1e-3 GW 或 GWh)。理由是 Base 中柔性检查恒为 0，从未被内点解检验过；严格的 1e-5 GWh 低于内点解的正常残差量级（2030 功率平衡最大残差 0.19 MW）。
> - **验收只是参考标签：** 任何口径的结论都不导致数据被删除、覆盖或放弃；解是否采用，由作者与决策层人工决定（AGENTS.md 2026-10-12 第 6 条）。
> ## 6. 执行顺序与当前状态
>
> 1. **已完成：** Base 2030/2040/2050 正式验收（`supplementary_materials/reviews/base_acceptance_relative_v1_20261012/`）；三年结果已备份到 T550（262 文件，15.96 GB，SHA 全部核验）。
> 2. **运行中：** Base 2060，Job 5124127，release `20261012_base2060_v9a12_t48_m750_tol1e4_v1`，源码 680a5c4，不筛选。
> 3. **今晚：** case3 柔性块解质量的夜间实验（`claude_workspace/tasks/TASK_case3_flex_numerics_overnight_20261012.md`），结论决定 case3 的生产求解参数。
> 4. **下一步（Claude 写任务书，Codex 实现）：**
>    - 筛选生产化：profile、margin 参数、`--state-in` 支持；
>    - 定价证书脚本；
>    - relative_v1 扩展；
>    - R1 交接规则产品化，把 2060 的一次性脚本整理为可复用工具；
>    - 与冻结 Base 2030 release 的身份门禁、24h 门禁；
>    - held 提交。
> 5. **随后：** case3 2030 与 `_nocredit` 2030 并行提交。C 2050 在 `--state-in` 筛选就绪后提交，可与 case3 2030 并行。case3 2040 在 case3 2030 完成后提交。框架 B 任务书在 case3 2030 提交后撰写。
> 6. **云端占用：** 最多同时 4 个 64 CPU/750G 节点（Base 2060、case3 2030、`_nocredit` 2030、C 2050）。每个作业均先 held 提交，作者放行后才运行。
