# CISPO 2030/8760 server runbook

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
