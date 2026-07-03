# CISPO 2030/8760 server runbook

Production architecture is one continuous LP containing 2030 capacity decisions and all 8760 chronological hours. The 2025 data are boundary conditions only. No Benders decomposition, representative periods, or temporal weights are used.

## Server layout

- Repository: `/data/zz2/National_model/repo`
- Model-ready tables: `/data/zz2/National_model/data/model_ready`
- Capacity factors: `/data/zz2/National_model/data/hourly_cf`
- Hydrology: `/data/zz2/National_model/data/hydro_timeseries`
- Python environment: `/home/zz2/.local/envs/cispo-2030`
- Environment definition: `/data/zz2/National_model/repo/env/cispo-server.yml`
- Outputs: `/data/zz2/National_model/outputs`
- Logs and manifests: `/data/zz2/National_model/logs`, `/data/zz2/National_model/manifests`

The `/data` filesystem is NTFS/fuseblk and does not enforce normal Unix ownership or mode bits. Do not store SSH keys or `gurobi.lic` there.

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
export CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries
export CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready
PYTHON=/home/zz2/.local/envs/cispo-2030/bin/python
$PYTHON scripts/check_server_readiness.py
$PYTHON scripts/preflight_cispo_2030.py --output /data/zz2/National_model/outputs/preflight_2030.json
```

Install `gurobipy` only after the license mechanism is confirmed. Store a license file under the protected home directory, not `/data`.

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
