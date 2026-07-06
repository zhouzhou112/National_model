# CISPO 2030 full-year server status

## Boundary and architecture

- 2025 is an input boundary only; it is not an optimization year.
- 2030 is the first planning year and represents changes over 2025-2030.
- Production is one continuous LP containing all 8760 chronological hours.
- No Benders decomposition, representative days, sampled hours, or temporal weights are used.
- Optional 744h and 4344h leading-hour horizons are explicitly test-only; 8760h remains the only scientific horizon.

## Implemented

- 31 provinces and 36,686 VRE technology-site rows at 0.25-degree resolution.
- Exact 2023 hourly CF linkage with sparse coefficient construction.
- Continuous capacity-based RUC and cyclic annual commitment/ramp state.
- Battery/PHS SOC and reserve; station-level hydropower and reservoir balance. Commit `b3e6298` adds Stage2 core-mainstem conventional hydropower cascade coupling and is deployed on the server.
- 411 interprovincial corridors, strict hourly power balance, reserve and inertia.
- DAC, annual carbon and biomass accounts, CCS capture and point-level injection.
- Spur/trunk/substation augmentation, memory gate, numerical diagnostics and IIS.
- Production load centers are the 278-node Natural Earth paper replication.
- Annual center energy allocation, provincial export closure and 517-edge intra-province AC500 expansion layer.
- Hydropower station-to-substation/load-center routing and hydro spur/trunk augmentation.

## Verification snapshot

- Current deployed implementation commit: `b3e6298` (`fix: add core hydropower cascade coupling`); live server checkout HEAD was `7a2ca27` on 2026-07-06.
- Current validated server data paths:
  - `CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260706_hydro_cascade`
  - `CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries_20260706_hydro_cascade`
  - `CISPO_RAW_GRFR_ROOT=/data/zz2/National_model/data/grfr_raw_2019`
- Raw GRFR transfer completed on 2026-07-06 and was verified on the server:
  - `output_pfaf_03_2019.nc`: 3,380,260,808 bytes, SHA256 `84ff2c882fb17a4b8693bb0773718c2472038021b64618b05f99f8070a506e0f`.
  - `output_pfaf_04_2019.nc`: 5,445,519,752 bytes, SHA256 `e56d5da855ddbdafabdafcb5582981b3f0003054156cf8d912d24a9efd232756`.
- Server readiness with `--require-raw-grfr --verify-raw-grfr-sha256`: `PASS`, zero hard failures.
- Hydropower station input: 2,030 rows, 620 reservoir rows, 1,410 run-of-river rows, 0 potential paper-rule mismatches, no missing required columns. Cascade readiness reported 142 nodes, 124 edges, 4 low-correlation edges, 18 max-bound edges and maximum lag 168 h.
- Server regression test: 16/16 tests passed with pytest in 20.12 seconds.
- One-month cascade server preflight: 4,761,900 variables, 6,465,714 constraints, 78,282,048 nonzeros; estimated model memory 4.48 GiB; memory gate passed with about 106.65 GiB available.
- Actual one-month cascade model build: 4,808,836 variables, 6,536,681 constraints and 46,092,407 nonzeros.
- Full-year server preflight: 48,164,172 variables, 68,689,554 constraints, 862,195,872 nonzeros.
- Conservative full-year model-memory estimate: 47.98 GiB; configured `SoftMemLimit`: 80 GiB.
- Local 744h build-only test: 3,032,784 variables, 4,760,844 constraints, 39,084,173 nonzeros; completed in about 134 seconds without optimization.
- Local 24h smoke solve: 365,184 variables, 285,309 constraints and 1,812,785 nonzeros; continuous LP solved to optimality in about 8 seconds after presolve. Maximum center-balance and province-export residuals were `1.16e-13` and `1.14e-13` GWh; no edge flowed in both directions, DPV spur augmentation was exactly zero, and no intra-capacity constraint was violated.
- Six-month/full-year local preflight correctly reported that the 32/64 GiB memory gates were not met; no construction was attempted.
- Server: 96 logical CPUs, 125 GiB RAM, 4.3 TiB free under `/data`.
- Server Gurobi Optimizer and `gurobipy`: 13.0.2 installed under `/home/zz2/opt/gurobi1302/linux64` and `/home/zz2/.local/envs/cispo-2030` respectively; 12.0.1 remains available as rollback software.
- Server license: retrieved successfully with Gurobi 13.0.2 on 2026-07-03, stored at `/home/zz2/gurobi.lic`, and valid through 2027-07-02. The server-issued license ID is 2840423.
- Production-license gate passed on 2026-07-06: Gurobi 13.0.2 solved the deterministic 2,501-variable LP to optimality with objective `1.0`, confirming that the bundled size-limited fallback is not active. This gate is also enforced by `scripts/check_server_readiness.py`.

## Cascade server validation status

- Implementation commit `b3e6298` reads Stage2 core cascade files from `D:\codeenv\pycharmproject\National_RL\Gis_process\hydro_power\process_hydro\hydro_model_2019_stage2_classification_cascade_20260630`.
- Generated cascade inputs contain 142 COMID nodes, 124 directed edges and 146 mapped reservoir stations. All mapped stations exist in `data/hydro/hydro_stations.csv`, all are `reservoir_storage`, capacity alignment residual is 0.0 GW and the topology is acyclic.
- Travel lags are estimated from 2019 GRFR hourly discharge by 3h-multiple cross-correlation, range 0-168 h. QA warnings remain for 4 low-correlation edges and 18 edges selecting the 168 h maximum search bound.
- Local checks passed: data-package rebuild with 90 QC checks and zero failures, smoke test 118/118 PASS, unit tests 16/16 PASS, one-month preflight PASS, and custom 24h monolithic build PASS with 146 cascade reservoir rows and 124 cascade edges.
- Server readiness, regression, preflight and full 744h model-build gates passed using the versioned cascade data roots.
- The 744h solve under `/data/zz2/National_model/outputs/2030_one_month_hydro_cascade` is still running as PID `244035`. At 2026-07-06 22:37 Asia/Shanghai it had run for about 5 h 59 min. Gurobi reported large coefficient/RHS ranges, restarted barrier near iteration 111, completed dual crossover pushes and remained in primal cleanup with about 1.92 million pushes and `PInf` about 312.
- No `solve_report.json` or `solution_qc.json` existed at that checkpoint. Therefore the cascade version is validated through construction but not yet through the complete optimization/QC gate.

## Explicit unresolved inputs

- CSP site potential and hourly profiles; CSP remains disabled.
- Observed province-level 2025 PHS floor; current floor is explicitly zero.
- Open-loop and closed-loop PHS hydraulic pairing data; the local cascade update covers conventional reservoir hydropower only.
- Thermal online fuel term `f_on`; fuel is charged on gross generation only.
- Hydropower type labels include low-confidence assigned labels because source data do not provide reliable type labels for all stations; retain them for now and validate later against external station evidence.
- Formal multi-year environmental flow for hydropower; the current cascade update still uses the 2019 single-year monthly P10 proxy. Four low-correlation and eighteen max-bound cascade-lag edges need manual hydrological/topological review.
- Capacity credits, inertia threshold and spur/trunk proxy costs still need parameter-source review, but no sensitivity-test workflow is requested for the current milestone.
- Intra-center annual capacity uses a 50% design utilization assumption; two western AC500 proxy edges exceed the 1000 km source range.
- Intra-center losses remain zero until their annual energy can be fed back into the provincial hourly balance.

The only production entry is `scripts/run_cispo_2030_full_year.py`.
