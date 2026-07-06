# CISPO 2030/8760 server runbook

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

Current cascade-hydropower data version from 2026-07-06:

```bash
export CISPO_CF_ROOT=/data/zz2/National_model/data/hourly_cf
export CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260706_hydro_cascade
export CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries_20260706_hydro_cascade
export CISPO_RAW_GRFR_ROOT=/data/zz2/National_model/data/grfr_raw_2019
```

Commit `b3e6298` contains the deployed core-mainstem hydropower cascade update. Server checkout HEAD `7a2ca27`, the versioned data roots above, readiness checks and 16 regression tests were verified on 2026-07-06. The complete 744h optimization/QC gate is still pending and must not be represented as passed until `solve_report.json` and `solution_qc.json` are audited.

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
export CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries_20260706_hydro_cascade
export CISPO_RAW_GRFR_ROOT=/data/zz2/National_model/data/grfr_raw_2019
export CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260706_hydro_cascade
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
| `full_year` | 8760 | Production scientific run | 64 GiB |

The truncated horizons use the leading hours and a cyclic boundary over the selected interval. Annual investment costs, carbon limits and biomass limits are not rescaled. Their solutions therefore must not be interpreted as planning results.

Preflight without requiring Gurobi:

```bash
$PYTHON scripts/run_cispo_2030_full_year.py --horizon one_month --preflight-only
```

## Current 744h cascade gate

The current server integration run uses:

```bash
OUT=/data/zz2/National_model/outputs/2030_one_month_hydro_cascade
PID=$(cat "$OUT/run.pid")
ps -p "$PID" -o pid,etime,%mem,%cpu,rss,vsz,stat,cmd
tail -n 100 "$OUT/gurobi.log"
ls -lh "$OUT/solve_report.json" "$OUT/solution_qc.json" 2>/dev/null
```

At the 2026-07-06 22:37 checkpoint, PID `244035` was still active after about 5 h 59 min. The actual model contained 4,808,836 variables, 6,536,681 constraints and 46,092,407 nonzeros. Gurobi warned about large coefficient and RHS ranges, restarted barrier once, then entered a long crossover cleanup. The run is not accepted until it exits and writes a satisfactory `solve_report.json` plus `solution_qc.json`.

If this run ends with `TIME_LIMIT`, `SUBOPTIMAL`, a numerical failure or unacceptable crossover duration, preserve the output directory. For the next diagnostic, copy `config/optimization_2030.json` to a separately named test configuration and change only `numerics.crossover` from `1` to `0`, then invoke it with `--config`. Do not overwrite the baseline configuration or alter model equations/constraints before comparing the diagnostic result:

```bash
$PYTHON scripts/run_cispo_2030_full_year.py \
  --config config/optimization_2030_crossover0.json \
  --horizon one_month \
  --output-dir /data/zz2/National_model/outputs/2030_one_month_hydro_cascade_crossover0
```

## Full model

Build without optimizing:

```bash
$PYTHON scripts/run_cispo_2030_full_year.py --horizon full_year --build-only --output-dir /data/zz2/National_model/outputs/2030_full_year_build
```

Solve:

```bash
$PYTHON scripts/run_cispo_2030_full_year.py --horizon full_year --output-dir /data/zz2/National_model/outputs/2030_full_year
```

The runtime gate refuses to build when available memory is below the configured threshold. For infeasibility, the solve path writes `iis.ilp`; production constraints are not silently relaxed.

Successful solves additionally write `solution_qc.json`, compressed hourly province balances, technology dispatch arrays, station-indexed reservoir dispatch, transmission flows, annual carbon/CCS accounts and objective cost decomposition. A solution is not accepted as production output unless `solution_qc.json` reports `PASS`.
