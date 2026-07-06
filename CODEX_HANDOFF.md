# CISPO model Codex handoff and version log

This is the repository's single handoff document for work continued across Codex windows. It records only verified, reproducible project state. New windows must read this file before taking action.

## Handoff update protocol

- Maintain `Current validated snapshot` as the concise active state.
- Append one entry under `Version history` after every material milestone.
- Each entry must include date, Git commit, scope, changed files, verification evidence, unresolved issues and next action.
- Link to detailed specifications rather than duplicating long derivations.
- Never include activation keys, passwords, private keys or the contents of `gurobi.lic`.

## Current validated snapshot

### Version identity

- Handoff version: `v0.1.0`
- Snapshot date: `2026-07-06`
- Local repository: `D:\codeenv\pycharmproject\National_RL\National_model`
- Git branch: `codex/cispo-2030-full-lp`
- Latest validated implementation commit: `805a1fa`
- Initial handoff-document commit: `1ac58dd`
- Server repository: `/data/zz2/National_model/repo`
- Server Git remote: `/home/zz2/git/National_model.git`
- At handoff version `v0.1.0`, local and server worktrees were clean and both contained `1ac58dd`. Always confirm the live HEAD with `git rev-parse --short HEAD` rather than treating a documentation commit as immutable current state.

### Fixed model boundary and architecture

- 2025 is an input boundary condition, not an optimization year.
- 2030 is the first planning year and represents capacity changes during 2025-2030.
- The scientific production model is one continuous national LP with 8760 chronological hours.
- No Benders decomposition, representative periods, sampled hours or temporal weights are used.
- Test horizons are `one_month=744h` and `six_months=4344h`; their annual costs and policy constraints are not rescaled, so their solutions are engineering tests rather than planning results.
- The only production entry point is `scripts/run_cispo_2030_full_year.py`.

### Implemented model scope

- 31 provincial load regions; Inner Mongolia is not split.
- 36,686 VRE technology-site rows with 2023 hourly capacity-factor linkage.
- Continuous capacity-based thermal RUC, ramping, reserve and inertia.
- Battery and PHS state of charge; station-level hydropower and reservoir balance.
- 411 interprovincial transmission corridors and strict hourly provincial power balance.
- DAC, annual carbon and biomass accounting, CCS capture and point-level injection.
- Spur line, trunk line and substation augmentation.
- The production load-center scenario is the 278-node Natural Earth paper replication.
- Annual load-center energy allocation, provincial export closure and 517-edge intraprovincial AC500 proxy expansion layer are implemented.
- Wind, solar and hydropower use spatial spur/trunk routing. Thermal, nuclear and biomass generation are allocated within each province by load-center demand shares.

Detailed definitions are in `cispo_full_lp_model_spec.md` and `LOAD_CENTER_NETWORK_278_年度输电层说明.md`.

### Server runtime

- Host login: `zz2@210.77.85.166`; SSH identity path on the workstation is `%USERPROFILE%\.ssh\server_ed25519`. Never read or copy the private-key contents.
- Server hardware observed: 96 logical CPUs and about 125 GiB RAM.
- Python environment: `/home/zz2/.local/envs/cispo-2030`, Python 3.11.15.
- Gurobi Optimizer: 13.0.2 at `/home/zz2/opt/gurobi1302/linux64`.
- `gurobipy`: 13.0.2 in the `cispo-2030` environment.
- Gurobi 12.0.1 remains installed as rollback software.
- License file: `/home/zz2/gurobi.lic`, mode `0600`, issued license ID `2840423`, valid through `2027-07-02`.
- The activation key and license-file contents must not be committed or copied into documentation.

### Server data paths

```bash
export CISPO_CF_ROOT=/data/zz2/National_model/data/hourly_cf
export CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries
export CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready
export GRB_LICENSE_FILE=/home/zz2/gurobi.lic
PYTHON=/home/zz2/.local/envs/cispo-2030/bin/python
```

### Latest verification evidence

- Full-license gate: Gurobi 13.0.2 solved a deterministic LP with 2,501 variables and one constraint to objective `1.0`; status `PASS`.
- Server readiness: `PASS`, zero hard failures.
- Regression tests: `10 passed in 4.72s` with pytest 9.1.1.
- Full-year preflight: memory gate passed with 112.23 GiB available.
- Estimated 8760h scale: 32,685,283 variables, 53,210,634 constraints and 738,364,512 nonzeros.
- Estimated model memory: 38.23 GiB.
- Verification script: `scripts/check_gurobi_full_license.py`; it is also called by `scripts/check_server_readiness.py`.

### Known limitations and unresolved inputs

- CSP site potential and hourly profiles are missing; CSP is disabled.
- The observed provincial 2025 PHS capacity floor is unavailable; the current floor is explicitly zero.
- Thermal online fuel term `f_on` is not implemented; fuel is charged on gross generation only.
- Capacity credits, inertia threshold and spur/trunk proxy costs require sensitivity analysis.
- The intraprovincial load-center network uses a 50% design-utilization assumption.
- Two western AC500 proxy edges exceed the 1000 km range of the cited source cost.
- Intraprovincial load-center transmission losses remain zero.
- Direct server access to PyPI fails TLS certificate-chain validation. The user chose to defer this issue. Do not disable TLS verification; use verified offline wheels when a new package is required.
- Temporary uploaded installers and wheel directories remain on the server; do not delete them without explicit user confirmation.

### Exact next action

Run the complete 744h `one_month` optimization on the server before any 8760h production solve:

```bash
cd /data/zz2/National_model/repo
export CISPO_CF_ROOT=/data/zz2/National_model/data/hourly_cf
export CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries
export CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready
export GRB_LICENSE_FILE=/home/zz2/gurobi.lic
PYTHON=/home/zz2/.local/envs/cispo-2030/bin/python

$PYTHON scripts/run_cispo_2030_full_year.py \
  --horizon one_month \
  --output-dir /data/zz2/National_model/outputs/2030_one_month
```

Record build time, solve time, peak memory, solver status, objective decomposition, numerical warnings, balance residuals, SOC/reservoir checks, transmission flows, curtailment, capacity additions and CCS injection. If infeasible, inspect the generated IIS; do not silently relax production constraints. After the 744h gate passes, run 8760h `build-only`, review actual memory/build behavior, freeze the baseline commit and only then start the production solve.

## Version history

### v0.1.0 - 2026-07-06 - Gurobi 13.0.2 server readiness

- Git baseline: `805a1fa` (`chore: configure Gurobi 13.0.2 server runtime`).
- Scope: completed server Gurobi installation, license retrieval, full-license verification, dependency documentation and synchronized server checkout.
- Main changed files:
  - `requirements-server.txt`
  - `requirements-test.txt`
  - `env/cispo-server.yml`
  - `scripts/check_gurobi_full_license.py`
  - `scripts/check_server_readiness.py`
  - `SERVER_RUNBOOK.md`
  - `MODEL_SERVER_STATUS.md`
- Verification: full-license 2,501-variable gate passed; server readiness passed; 10/10 tests passed; 8760h preflight memory gate passed.
- Environment note: pytest 9.1.1 was installed from locally verified offline wheels because server PyPI TLS validation remains unresolved.
- Unresolved items: listed in the current snapshot above.
- Next action: run and audit the server-side 744h `one_month` optimization.
