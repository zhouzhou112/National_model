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
- Battery/PHS SOC and reserve; station-level hydropower and reservoir balance.
- 411 interprovincial corridors, strict hourly power balance, reserve and inertia.
- DAC, annual carbon and biomass accounts, CCS capture and point-level injection.
- Spur/trunk/substation augmentation, memory gate, numerical diagnostics and IIS.
- Production load centers are the 278-node Natural Earth paper replication.
- Annual center energy allocation, provincial export closure and 517-edge intra-province AC500 expansion layer.
- Hydropower station-to-substation/load-center routing and hydro spur/trunk augmentation.

## Verification snapshot

- Data preflight: 32 PASS, 1 WARN, 1 INFO, 0 HARD_FAIL.
- Estimated full scale: 32,685,283 variables, 53,210,634 constraints, 738,364,512 nonzeros.
- Conservative model-memory estimate: 38.23 GiB; configured `SoftMemLimit`: 80 GiB.
- Local 744h build-only test: 3,032,784 variables, 4,760,844 constraints, 39,084,173 nonzeros; completed in about 134 seconds without optimization.
- Local 24h smoke solve: 365,184 variables, 285,309 constraints and 1,812,785 nonzeros; continuous LP solved to optimality in about 8 seconds after presolve. Maximum center-balance and province-export residuals were `1.16e-13` and `1.14e-13` GWh; no edge flowed in both directions, DPV spur augmentation was exactly zero, and no intra-capacity constraint was violated.
- Six-month/full-year local preflight correctly reported that the 32/64 GiB memory gates were not met; no construction was attempted.
- Server: 96 logical CPUs, 125 GiB RAM, 4.3 TiB free under `/data`.
- Server working copy and model-ready data were synchronized at commit `c99b6c2`; the uploaded data archive SHA256 is `09831040de1901fa02610fb6272e76e7995edaabcbac12d158ae81b0caf47b25`.
- Server verification: 10/10 tests passed; full-year preflight passed the 64 GiB runtime gate with about 110 GiB available and reported 32 PASS, 1 WARN, 1 INFO and 0 HARD_FAIL.
- Server Gurobi Optimizer and `gurobipy`: 13.0.2 installed under `/home/zz2/opt/gurobi1302/linux64` and `/home/zz2/.local/envs/cispo-2030` respectively; 12.0.1 remains available as rollback software.
- Server license: retrieved successfully with Gurobi 13.0.2 on 2026-07-03, stored at `/home/zz2/gurobi.lic`, and valid through 2027-07-02. The server-issued license ID is 2840423.
- Production-license gate passed on 2026-07-06: Gurobi 13.0.2 solved the deterministic 2,501-variable LP to optimality with objective `1.0`, confirming that the bundled size-limited fallback is not active. This gate is also enforced by `scripts/check_server_readiness.py`.
- Post-upgrade full-year preflight passed with 112.23 GiB available memory; the estimated production scale remains 32,685,283 variables, 53,210,634 constraints and 738,364,512 nonzeros.
- Post-upgrade regression test: 10/10 tests passed on the server with pytest 9.1.1 in 4.69 seconds.

## Explicit unresolved inputs

- CSP site potential and hourly profiles; CSP remains disabled.
- Observed province-level 2025 PHS floor; current floor is explicitly zero.
- Thermal online fuel term `f_on`; fuel is charged on gross generation only.
- Capacity credits, inertia threshold and spur/trunk proxy costs require sensitivity tests.
- Intra-center annual capacity uses a 50% design utilization assumption; two western AC500 proxy edges exceed the 1000 km source range.
- Intra-center losses remain zero until their annual energy can be fed back into the provincial hourly balance.

The only production entry is `scripts/run_cispo_2030_full_year.py`.
