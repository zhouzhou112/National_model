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

- Handoff version: `v0.5.0`
- Snapshot date: `2026-07-18`
- Local repository: `D:\codeenv\pycharmproject\National_RL\National_model`
- Git branch: `codex/cispo-2030-full-lp`
- Current local implementation commit: `2a0ee99` (`feat: add sequential planning and stabilize full-year LP`).
- Latest server-deployed implementation last verified live remains `a8cd150` (`fix: switch hydropower to p30 proxy`) from 2026-07-07; it is now behind local.
- On 2026-07-18 TCP/22 connected but SSH closed during key exchange. Therefore server HEAD, old PID `863603` and the P30-cleanup 744h result are currently unverified; do not infer that the process is still running or that the gate passed.
- Current local 24h gate on `2a0ee99` is `OPTIMAL` in 58.79 s with `solution_qc=PASS`; current full-year preflight is PASS but the local 64 GiB RAM build gate is not met.
- Initial handoff-document commit: `1ac58dd`
- Server repository: `/data/zz2/National_model/repo`
- Server Git remote: `/home/zz2/git/National_model.git`
- At handoff version `v0.2.0`, local code was committed and pushed as `8e49a87`, and the server checkout under `/data/zz2/National_model/repo` was fast-forwarded to that commit before data/readiness validation. Always confirm the live HEAD with `git rev-parse --short HEAD` rather than treating a documentation commit as immutable current state.

### Fixed model boundary and architecture

- 2025 is an input boundary condition, not an optimization year.
- 2030 is the first planning year and represents capacity changes during 2025-2030; accepted capacity cohorts then pass sequentially to 2040, 2050 and 2060.
- The scientific production model is one continuous national LP with 8760 chronological hours.
- No Benders decomposition, representative periods, sampled hours or temporal weights are used.
- Test horizons are `one_month=744h` and `six_months=4344h`; their annual costs and policy constraints are not rescaled, so their solutions are engineering tests rather than planning results.
- Per-year entry is `scripts/run_cispo_2030_full_year.py`; the isolated multi-year entry is `scripts/run_cispo_planning_sequence.py`.

### Implemented model scope

- 31 provincial load regions; Inner Mongolia is not split.
- 36,686 VRE technology-site rows with 2023 hourly capacity-factor linkage.
- Continuous capacity-based thermal RUC, ramping, reserve and inertia.
- Battery and PHS state of charge; station-level hydropower, reservoir balance and committed core-cascade hydropower coupling for the Stage2 recommended mainstem groups.
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
- GPU test environment: `/home/zz2/.local/envs/cispo-gurobi-gpu` with `gurobipy 13.0.2+cu129`; it is isolated from the production CPU environment and should be used only for PDHG tests with `Method=6`, `PDHGGPU=1`.
- Gurobi 12.0.1 remains installed as rollback software.
- License file: `/home/zz2/gurobi.lic`, mode `0600`, issued license ID `2840423`, valid through `2027-07-02`.
- The activation key and license-file contents must not be committed or copied into documentation.

### Server data paths

```bash
export CISPO_CF_ROOT=/data/zz2/National_model/data/hourly_cf
export CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries_20260707_p30_cleanup
export CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260707_p30_cleanup
export CISPO_RAW_GRFR_ROOT=/data/zz2/National_model/data/grfr_raw_2019
export GRB_LICENSE_FILE=/home/zz2/gurobi.lic
PYTHON=/home/zz2/.local/envs/cispo-2030/bin/python
```

### Latest verification evidence

- Local implementation commit `2a0ee99`; AST 38 files PASS; unit tests 23/23 PASS; data-package smoke 124/124 PASS.
- Final local 24h gate: 349,962 variables, 260,973 constraints, 1,827,245 nonzeros; Gurobi `OPTIMAL` in 58.79 s; peak RSS 0.698 GiB; `solution_qc=PASS`; maximum power-balance residual `3.90e-11 GW`.
- Local full-year preflight: PASS, zero hard failures; 44,090,772 variables, 67,603,314 constraints, 853,505,952 estimated nonzeros and 46.62 GiB estimated model memory. The workstation does not meet the 64 GiB full-year construction gate.
- Nonempty 2040 state-transfer diagnostic: `OPTIMAL/QC PASS`; inherited 2.5 GW battery and 1.0 GW PHS cohorts entered the intended province-technology lower bounds exactly.
- PHS source/QC: GHT 2026 province-level 8h storage; national operating floor 65.94 GW; 2030 project upper 249.191 GW; 2040+ upper 514.755 GW.
- Outputs: compact capacity/generation/storage/monthly/hourly summaries, SVG quicklooks and SHA256 result manifest are implemented and validated. Detailed audit: `MODEL_SYSTEM_AUDIT_20260718.md`.
- Server refresh attempt on 2026-07-18 failed during SSH key exchange. All server/PID evidence below is retained historical evidence from 2026-07-07 unless explicitly refreshed later.

- Local implementation commit: `8e49a87` (`fix: harden CCS and station-level hydropower model`) pushed to `origin/codex/cispo-2030-full-lp`.
- Raw GRFR transfer to `/data/zz2/National_model/data/grfr_raw_2019` completed and was verified by server-side file size and SHA256:
  - `output_pfaf_03_2019.nc`: `84ff2c882fb17a4b8693bb0773718c2472038021b64618b05f99f8070a506e0f`.
  - `output_pfaf_04_2019.nc`: `e56d5da855ddbdafabdafcb5582981b3f0003054156cf8d912d24a9efd232756`.
- Server readiness with `--require-raw-grfr --verify-raw-grfr-sha256`: `PASS`, zero hard failures; hydropower station rows `2030`, reservoir rows `620`, run-of-river rows `1410`, potential paper-rule mismatches `0`.
- Server regression tests: `15 passed in 20.75s` with pytest.
- One-month server preflight: 4,300,620 variables, 6,004,434 constraints, 74,591,808 nonzeros; estimated memory 4.19 GiB; memory gate passed with about 110.24 GiB available.
- Full-year server preflight: 48,164,172 variables, 68,689,554 constraints, 862,195,872 nonzeros; estimated memory 47.98 GiB; memory gate passed with about 110.22 GiB available.
- Local verification before server sync: AST parse passed for 14 changed Python files; `unittest discover -s tests -q` passed 15 tests; data-package smoke test passed 113/113 checks; 24h station-hydro solve reached Gurobi `OPTIMAL` and `solution_qc.json` reported `PASS`.
- Verification scripts: `scripts/check_gurobi_full_license.py` and `scripts/check_server_readiness.py`; the latter now enforces raw GRFR presence and optional SHA256 verification.
- Local cascade implementation verification on 2026-07-06:
  - Stage2 source path `D:\codeenv\pycharmproject\National_RL\Gis_process\hydro_power\process_hydro\hydro_model_2019_stage2_classification_cascade_20260630` is readable.
  - Generated cascade topology contains 142 COMID nodes, 124 directed edges and 146 mapped reservoir stations across 5 recommended core groups.
  - All 146 Stage2 station IDs map into current `data/hydro/hydro_stations.csv`; all are `reservoir_storage`; capacity alignment residual is 0.0 GW; the directed topology is acyclic.
  - GRFR cross-correlation lag estimation produced non-negative 3h-multiple lags with range 0-168 h; 4 edges have low lag correlation and 18 edges select the 168 h search bound, so these are WARN-level topology/lag QA items.
  - `scripts/build_cispo_data_package.py` with ArcGIS Pro Python regenerated the local data package with 90 QC checks and zero failures.
  - `python scripts/smoke_test_data_package.py` passed 118/118 checks.
  - `C:\Users\ZZ\.conda\envs\RL\python.exe -m unittest discover -s tests -q` passed 16/16 tests.
  - `scripts/run_cispo_2030_full_year.py --horizon one_month --preflight-only` passed and estimated 4,761,900 variables, 6,465,714 constraints and 78,282,048 nonzeros.
  - A custom 24h monolithic build with `compute_max_cf=False` succeeded with 422,596 variables, 342,510 constraints and 2,037,793 nonzeros; reservoir variables now include `reservoir_turbine_flow`, `reservoir_spill_flow` and `reservoir_volume`; core cascade rows = 146 and edges = 124.
- Cascade server deployment and verification on 2026-07-06:
  - Server checkout HEAD `7a2ca27` contains implementation commit `b3e6298`.
  - Versioned data roots are `/data/zz2/National_model/data/model_ready_20260706_hydro_cascade` and `/data/zz2/National_model/data/hydro_timeseries_20260706_hydro_cascade`.
  - Server readiness with raw-GRFR SHA256 verification passed; it reported 2,030 hydropower stations, 620 reservoirs, 1,410 run-of-river stations, 142 cascade nodes, 124 edges, 4 low-correlation edges, 18 max-lag-bound edges and maximum lag 168 h.
  - Server regression tests passed 16/16 in 20.12 s.
  - Server `one_month` preflight passed with estimated 4,761,900 variables, 6,465,714 constraints, 78,282,048 nonzeros and 4.48 GiB model memory.
  - The actual 744h model build completed with 4,808,836 variables, 6,536,681 constraints and 46,092,407 nonzeros.
  - The optimization output directory is `/data/zz2/National_model/outputs/2030_one_month_hydro_cascade`; PID `244035` remained active at 2026-07-06 22:37 Asia/Shanghai after about 5 h 59 min.
  - Gurobi reported large matrix-coefficient and RHS ranges, barrier restarted near iteration 111, dual crossover pushes completed, and primal cleanup was still active at about 1,919,682 remaining pushes with `PInf=3.1246436e+02`. No `solve_report.json` or `solution_qc.json` existed at that checkpoint, so the 744h gate is not yet passed.
- Numerical-stability implementation and validation on 2026-07-07:
  - Commit `281f9c7` scales reservoir flow variables to `10^3 m3/s` and reservoir volume variables to `10^6 m3`, preserving physical `m3/s` and `m3` at all inputs, exports and QC checks.
  - `coefficient_zero_tolerance=1e-6`, `hydrology_flow_zero_tolerance_m3s=1e-4`, `BarConvTol=1e-8`, `Crossover=1` and `Threads=-1` are explicit configuration values.
  - Local numerical audit at 24h improved matrix coefficients from approximately `1e-10–3600` to `1e-6–24`, RHS from approximately `2e-13–4.48e10` to `4.32e-7–1.17e5`, and removed all coefficients/RHS below `1e-8` in the audited model.
  - Local 24h full solve: 422,596 variables, 342,508 constraints and 2,037,549 nonzeros; Gurobi `59.66 s`; `OPTIMAL`; `solution_qc=PASS`; peak RSS `0.865 GiB`.
  - Server checkout was fast-forwarded to `281f9c7`; 18/18 tests passed in `19.46 s`.
  - Server 168h full solve under `/data/zz2/National_model/outputs/2030_diagnostic_168h_numerics_scaled`: 1,299,844 variables, 1,581,351 constraints and 10,733,898 nonzeros; build `90.54 s`; Gurobi `675.56 s`; `OPTIMAL`; `solution_qc=PASS`; peak RSS `4.061 GiB`.
  - Server CPU is 48 physical cores / 96 logical processors. `Threads=-1` exposed all 96 logical processors; barrier factorization used 48 physical threads. Two RTX 4090 GPUs are present, but current `gurobipy 13.0.2` is the standard non-`+cu` build and therefore did not use GPU acceleration.
  - Detailed module and numerical audit: `MODEL_SYSTEM_AUDIT_20260707.md`.
- P30-cleanup and GPU validation on 2026-07-07:
  - Commit `a8cd150` removes the obsolete early block-boundary variables from `master.py`, switches conventional hydropower environmental flow to the configured `monthly_environmental_flow_2019_p30` dataset and keeps run-of-river hydropower as station-CF-weighted provincial hourly output variables.
  - Local checks: AST parse for changed Python files PASS; `C:\Users\ZZ\.conda\envs\RL\python.exe -m unittest discover -s tests -q` passed 19/19; `scripts/smoke_test_data_package.py` passed 118/118.
  - New server data roots: `/data/zz2/National_model/data/model_ready_20260707_p30_cleanup` and `/data/zz2/National_model/data/hydro_timeseries_20260707_p30_cleanup`; P30 proxy NetCDF SHA256 `c28f628642baaaac18d4461ac9474b3d622fcd80fbcd651884e6095d58203767`.
  - Server readiness with the P30 roots passed, including raw-GRFR SHA256 verification; server regression tests passed 19/19 in `18.06 s`.
  - Server 24h CPU P30 gate under `/data/zz2/National_model/outputs/2030_diagnostic_24h_p30_cleanup_cpu`: 375,910 variables, 278,737 constraints, 1,879,966 nonzeros; Gurobi `45.06 s`; `OPTIMAL`; `solution_qc=PASS`; peak RSS `0.879 GiB`.
  - GPU-enabled Gurobi was installed only in `/home/zz2/.local/envs/cispo-gurobi-gpu` from verified wheel `gurobipy-13.0.2+cu129-cp311-cp311-manylinux_2_24_x86_64.whl` (SHA256 `10f0a10fed0c0f959d11bc4f60d36d4ef04a13c48ecf649cd557e8b952de0680`; server SHA256 matched after upload).
  - GPU probe confirmed `linux64gpu[cuda12]`, `GPU model: NVIDIA GeForce RTX 4090` and `Start PDHG on GPU`.
  - The same 24h model with GPU-PDHG was interrupted after about 600 s because it was still iterating and had no `solve_report.json`; CPU barrier is therefore the accepted default for this model at this stage.
  - The P30-cleanup 744h CPU gate under `/data/zz2/National_model/outputs/2030_one_month_p30_cleanup_cpu` completed model build in `339.56 s` with peak RSS `5.336 GiB`; model statistics are 4,762,150 variables, 6,472,914 constraints and 45,718,011 nonzeros. Gurobi optimization is still running under PID `863603`; no `solve_report.json` or `solution_qc.json` exists yet.

### Known limitations and unresolved inputs

- CSP site potential and hourly profiles are missing; CSP is disabled.
- PHS open-loop/closed-loop hydraulic pairing is unavailable. PHS is represented as province-level 8h storage with a GHT 2026 operating floor and year-available project upper.
- Thermal online fuel term `f_on` is not implemented; fuel is charged on gross generation only.
- Hydropower type labels are assigned from the available GHT/proxy rules because source data do not provide reliable type labels for every plant; low-confidence labels are retained for now and should be validated later against external station evidence.
- Core hydropower cascade coupling and the scaled 168h solve have passed server regression, optimization and QC gates. The old 744h run was interrupted with no solution; a replacement scaled 744h run remains unvalidated. Current implementation covers conventional reservoir cascade operation, not open-loop or closed-loop PHS water-pair coupling.
- Core cascade environmental flow now uses a 2019 single-year monthly P30 proxy. This follows the requested P30 direction but is still not the formal 1980-2019 climatological P30; manual review of the 4 low-correlation / 18 max-bound lag edges also remains unresolved input work.
- Capacity credits, inertia threshold and spur/trunk proxy costs still require parameter-source review, but no sensitivity-analysis workflow is requested for the current milestone.
- The intraprovincial load-center network uses a 50% design-utilization assumption.
- Two western AC500 proxy edges exceed the 1000 km range of the cited source cost.
- Intraprovincial load-center transmission losses remain zero.
- Direct server access to PyPI fails TLS certificate-chain validation. The user chose to defer this issue. Do not disable TLS verification; use verified offline wheels when a new package is required.
- Temporary uploaded installers and wheel directories remain on the server; do not delete them without explicit user confirmation.

### Exact next action

Do not start the 8760h production solve. First restore live SSH access and verify, rather than assume, the old P30-cleanup 744h process/output and server HEAD:

```bash
cd /data/zz2/National_model/repo
export CISPO_CF_ROOT=/data/zz2/National_model/data/hourly_cf
export CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries_20260707_p30_cleanup
export CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260707_p30_cleanup
export CISPO_RAW_GRFR_ROOT=/data/zz2/National_model/data/grfr_raw_2019
export GRB_LICENSE_FILE=/home/zz2/gurobi.lic
PYTHON=/home/zz2/.local/envs/cispo-2030/bin/python

OUT=/data/zz2/National_model/outputs/2030_one_month_p30_cleanup_cpu
ps -p 863603 -o pid,etime,%cpu,%mem,rss,stat,cmd
tail -n 80 "$OUT/gurobi.log"
ls -lh "$OUT/solve_report.json" "$OUT/solution_qc.json" 2>/dev/null
```

Exact next action after SSH recovers: inspect the old 744h artifacts, deploy commit `2a0ee99` plus a new minimal-contract model-ready bundle, run readiness and 23 regression tests, then run a replacement 744h CPU barrier gate. Acceptance requires `OPTIMAL`, `solution_qc=PASS`, acceptable balance/water residuals and recorded build/solve/export time plus peak memory. The one-hour runtime remains a target, not a verified promise. GPU-PDHG is not the default route. Only after the replacement 744h gate passes may 8760h `build-only` run; only after that gate may the 2030 production solve and subsequent state-chained years begin.

## Version history

### v0.5.0 - 2026-07-18 - sequential planning, exact sparse reformulation and complete outputs

- Git implementation baseline: `2a0ee99` (`feat: add sequential planning and stabilize full-year LP`).
- Scope: implemented checksummed 2030/2040/2050/2060 capacity-cohort transfer; added GHT 2026 province-level PHS floor/project upper; removed redundant ramp, storage reserve, reservoir generation, hydro inertia and operating-cost-account variables/equalities using exact linear reformulations; completed compact outputs/SVG/manifest; reduced model input tables to an explicit 28-table contract.
- Main changed files: `cispo_model/config.py`, `data.py`, `master.py`, `monolithic.py`, `planning_state.py`, `preflight.py`, `result_summary.py`; `config/model_data_config.json`, `optimization_2030.json`, `model_input_files.json`; run/build/readiness/smoke scripts and sequence/tests.
- Local validation: AST 38 PASS; unit tests 23/23 PASS; data-package smoke 124/124 PASS; 2030 and 2040 full-year preflight PASS; four-year sequence dry-run PASS; final 24h solve `OPTIMAL/QC PASS` in 58.79 s with 0.698 GiB peak RSS; nonempty 2040 state diagnostic `OPTIMAL/QC PASS`.
- Scale: full-year preflight estimates 44,090,772 variables, 67,603,314 constraints, 853,505,952 nonzeros and 46.62 GiB model memory. Local build is correctly blocked by the 64 GiB runtime gate.
- Server status: not deployed. SSH connected to TCP/22 but closed during key exchange on 2026-07-18, so server HEAD and old 744h status could not be verified.
- Unresolved: replacement 744h and 8760 build-only gates; formal multi-year P30; 4 low-correlation and 18 max-bound lag edges; plant-level thermal retrofit/retirement identity; CSP, thermal `f_on`, PHS hydraulic pairing and proxy network assumptions.
- Next action: restore SSH, verify old artifacts, deploy commit/data, pass readiness/tests/744h, then 8760 build-only before any production sequence.

### v0.4.1 - 2026-07-07 - P30 hydropower cleanup and GPU-PDHG isolation test

- Git implementation baseline and live server HEAD: `a8cd150` (`fix: switch hydropower to p30 proxy`).
- Scope: removed obsolete early block-boundary variables from `master.py`; switched conventional hydropower environmental flow from the single-year P10 proxy to the configured single-year P30 proxy; retained run-of-river as station-CF-weighted provincial hourly output variables; kept PHS as province-level storage; installed GPU-enabled Gurobi only in an isolated venv and tested PDHG.
- Main changed files: `.gitignore`, `config/model_data_config.json`, `config/optimization_2030.json`, `cispo_model/config.py`, `cispo_model/hydro.py`, `cispo_model/master.py`, `scripts/build_cispo_data_package.py`, `scripts/check_server_readiness.py`, `scripts/prepare_server_bundle.py`, `tests/test_hydro_station_model.py`.
- Data roots: `/data/zz2/National_model/data/model_ready_20260707_p30_cleanup` and `/data/zz2/National_model/data/hydro_timeseries_20260707_p30_cleanup`; P30 NetCDF SHA256 `c28f628642baaaac18d4461ac9474b3d622fcd80fbcd651884e6095d58203767`.
- Validation: local AST PASS, local 19/19 unit tests PASS, data smoke test 118/118 PASS; server readiness PASS with raw-GRFR SHA256 verification; server 19/19 tests PASS; server 24h CPU P30 solve `OPTIMAL`, `solution_qc=PASS`, Gurobi `45.06 s`, peak RSS `0.879 GiB`.
- GPU result: isolated `gurobipy 13.0.2+cu129` environment successfully used `Start PDHG on GPU`, but the 24h P30 model was still iterating after about 600 s and was interrupted with no `solve_report.json`; standard CPU barrier remains the accepted solver route.
- Current run: P30-cleanup 744h CPU gate is running at `/data/zz2/National_model/outputs/2030_one_month_p30_cleanup_cpu`, PID `863603`; build completed in `339.56 s` with peak RSS `5.336 GiB`, and Gurobi optimization is in progress.
- Unresolved: 744h gate final status not yet known; formal 1980-2019 climatological P30 remains future data work; low-correlation/max-bound cascade lag edges still need manual data review.
- Next action: monitor PID `863603`, then audit solve/QC outputs before any 8760h build or production solve.

### v0.4.0 - 2026-07-07 - LP numerical scaling repair and 168h server gate

- Git baseline and live server HEAD: `281f9c7` (`fix: stabilize hydropower LP numerics`).
- Scope: preserved and interrupted the failed old 744h run; audited every model block; applied mathematically equivalent reservoir flow/volume scaling; added numerical-audit and arbitrary diagnostic-hour tooling; exposed all server CPUs; expanded solver-quality reporting.
- Main changed files: `config/optimization_2030.json`, `cispo_model/config.py`, `cispo_model/diagnostics.py`, `cispo_model/hydro.py`, `cispo_model/monolithic.py`, `cispo_model/solution_export.py`, `scripts/audit_model_numerics.py`, `scripts/run_cispo_2030_full_year.py`, `tests/test_hydro_station_model.py`.
- Validation: local 18/18 tests PASS; local 24h `OPTIMAL` and QC PASS in `59.66 s`; server 18/18 tests PASS; server 168h `OPTIMAL` and QC PASS in `675.56 s` with `4.061 GiB` peak RSS.
- CPU/GPU: `Threads=-1` exposes 96 logical processors; barrier uses 48 physical threads. Two RTX 4090 GPUs are compatible candidates for Gurobi GPU PDHG, but current installed build is CPU-only; any GPU test must use a separate `+cu` environment and `Method=6`, `PDHGGPU=1`.
- Unresolved: replacement scaled 744h run not yet started; no 8760h run is authorized before it passes. Full details are in `MODEL_SYSTEM_AUDIT_20260707.md`.
- Next action: run and audit `/data/zz2/National_model/outputs/2030_one_month_hydro_cascade_numerics_scaled`.

### v0.3.1 - 2026-07-06 - cascade server deployment and 744h numerical gate in progress

- Git implementation baseline: `b3e6298`; server checkout HEAD verified as `7a2ca27`.
- Scope: transferred and verified versioned cascade model-ready/hydrology data, passed server readiness and 16 regression tests, passed the 744h preflight and completed the full 744h model build.
- Server data roots:
  - `/data/zz2/National_model/data/model_ready_20260706_hydro_cascade`
  - `/data/zz2/National_model/data/hydro_timeseries_20260706_hydro_cascade`
- Verification: readiness PASS with raw-GRFR SHA256 verification; cascade counts 142 nodes and 124 edges; 16/16 tests PASS; one-month preflight PASS; actual model build 4,808,836 variables, 6,536,681 constraints and 46,092,407 nonzeros.
- Numerical status: Gurobi emitted coefficient/RHS scale warnings, barrier restarted once and the solve entered a long crossover cleanup. At the recorded checkpoint the process was still active after about 5 h 59 min, with no final solve/QC report. This is not a passed optimization gate.
- Changed files in this handoff-only milestone: `CODEX_HANDOFF.md`, `MODEL_SERVER_STATUS.md`, `SERVER_RUNBOOK.md`.
- Next action: preserve and audit the current run when it exits; if crossover does not finish acceptably, compare a separate `Crossover=0` diagnostic configuration without modifying model physics.

### v0.3.0 - 2026-07-06 - core mainstem hydropower cascade implementation

- Git baseline: `b3e6298` (`fix: add core hydropower cascade coupling`), based on prior server-validated commit `8e49a87` (`fix: harden CCS and station-level hydropower model`).
- Scope: read and validated the Stage2 core-mainstem hydropower classification/cascade scaffold; generated model-ready cascade nodes/edges; estimated MERIT downstream travel lags by 2019 GRFR cross-correlation; replaced independent core-reservoir operation with local-inflow plus upstream turbine/spill delayed arrival; retained independent operation for non-core reservoirs.
- Main changed files in the implementation commit:
  - `config/optimization_2030.json`
  - `config/model_data_config.json`
  - `scripts/build_cispo_data_package.py`
  - `scripts/check_server_readiness.py`
  - `scripts/smoke_test_data_package.py`
  - `cispo_model/data.py`
  - `cispo_model/hydro.py`
  - `cispo_model/monolithic.py`
  - `cispo_model/preflight.py`
  - `cispo_model/solution_export.py`
  - `tests/test_hydro_station_model.py`
  - `cispo_full_lp_model_spec.md`
- Local generated data files:
  - `data/hydro/cascade_topology_nodes.csv`
  - `data/hydro/cascade_topology_edges.csv`
- Verification: Stage2-to-model mapping passed with 146/146 reservoir stations; cascade topology is acyclic; local data package QC has zero failures; smoke test passed 118/118 checks; local unit tests passed 16/16; one-month preflight passed; custom 24h monolithic build succeeded.
- Modeling note: the local implementation follows the user's requested core-mainstem cascade mode for conventional reservoir hydropower. It does not yet implement open-loop/closed-loop PHS hydraulic coupling because required pairing/source data are not present in the current data package.
- Unresolved items: 4 low-correlation lag edges and 18 max-bound lag edges require manual hydrological/topological review; formal multi-year environmental flow remains unavailable.
- Next action: synchronize the branch and transfer a new versioned data package to the server, then rerun server readiness plus 744h `one_month` optimization.

### v0.2.0 - 2026-07-06 - station-level hydropower, CCS retrofit accounting and raw GRFR server readiness

- Git baseline: `8e49a87` (`fix: harden CCS and station-level hydropower model`).
- Scope: implemented assigned-label hydropower rules, paper-consistent potential hydropower classification, independent station-level reservoir balance using GRFR inflow, CCS retrofit/capture-cost accounting, production solution export/QC, and raw GRFR server readiness gates.
- Main changed files:
  - `config/optimization_2030.json`
  - `config/model_data_config.json`
  - `scripts/build_cispo_data_package.py`
  - `scripts/check_server_readiness.py`
  - `scripts/prepare_server_bundle.py`
  - `scripts/run_cispo_2030_full_year.py`
  - `cispo_model/hydro.py`
  - `cispo_model/monolithic.py`
  - `cispo_model/load_center.py`
  - `cispo_model/master.py`
  - `cispo_model/solution_export.py`
  - `cispo_model/runtime_monitor.py`
  - `tests/test_hydro_station_model.py`
  - `tests/test_ccs_model_structure.py`
- Data packages transferred to the server:
  - `/data/zz2/National_model/data/model_ready_20260706_station_hydro`
  - `/data/zz2/National_model/data/hydro_timeseries_20260706_station_hydro`
  - `/data/zz2/National_model/data/grfr_raw_2019`
- Verification: raw GRFR SHA256 matched source files; server readiness passed with raw-GRFR SHA verification; 15/15 tests passed on the server; one-month and full-year preflights passed memory gates with the scale estimates recorded in the current snapshot.
- Modeling note: according to the EES hydropower supplement, installed labels are retained from assigned labels, potential dam sites with design capacity greater than 750 MW are modeled as reservoir hydropower, remaining potential sites as run-of-river hydropower, and no hydraulic cascade propagation delay is added because the cited equations use independent station-level natural inflow rather than upstream/downstream travel-time coupling.
- Unresolved items: listed in the current snapshot above.
- Next action: run and audit the server-side 744h `one_month` optimization using the versioned station-hydropower data paths.

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
