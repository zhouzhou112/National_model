# National CISPO-style power-system planning model

This repository implements a continuous linear capacity-expansion and chronological-dispatch model for China's 31 provincial regions. The production horizon is one continuous 8760-hour year. The model is intended for reproducible research: every accepted case records its exact inputs, configuration, solver environment, outputs, hard QC and SHA256 manifest.

## Scientific boundary

- `2025` is a fixed boundary state, not an optimization year.
- Planning years are solved sequentially as `2030 -> 2040 -> 2050 -> 2060`.
- Each planning year is a separate 8760-hour LP. Accepted model-built cohorts pass to the next year and retire by technology lifetime.
- `744h` and `4344h` horizons are engineering gates only. Their annual capacity/policy terms are not rescaled, so their objective and energy totals are not planning results.
- The production formulation is `full_year_monolithic_lp`; representative periods and decomposition are not used.

The full mathematical specification is in [cispo_full_lp_model_spec.md](cispo_full_lp_model_spec.md). Current validated implementation and server evidence are in [CODEX_HANDOFF.md](CODEX_HANDOFF.md).

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

## Development rule

Do not change units, time resolution, spatial resolution, objective terms, capacity bounds or scientific assumptions without updating the configuration/specification, regression tests and `CODEX_HANDOFF.md`. Long solves must pass a small diagnostic gate first.
