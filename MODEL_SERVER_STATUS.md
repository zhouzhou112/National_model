# CISPO 2030 full-year server status

## Boundary and architecture

- 2025 is an input boundary only; it is not an optimization year.
- 2030 is the first planning year and represents changes over 2025-2030.
- Production is one continuous LP containing all 8760 chronological hours.
- No Benders decomposition, representative days, sampled hours, or temporal weights are used.

## Implemented

- 31 provinces and 36,686 VRE technology-site rows at 0.25-degree resolution.
- Exact 2023 hourly CF linkage with sparse coefficient construction.
- Continuous capacity-based RUC and cyclic annual commitment/ramp state.
- Battery/PHS SOC and reserve; station-level hydropower and reservoir balance.
- 411 interprovincial corridors, strict hourly power balance, reserve and inertia.
- DAC, annual carbon and biomass accounts, CCS capture and point-level injection.
- Spur/trunk/substation augmentation, memory gate, numerical diagnostics and IIS.

## Verification snapshot

- Data preflight: 23 PASS, 1 INFO, 0 WARN, 0 HARD_FAIL.
- Estimated full scale: 32,678,590 variables, 53,204,758 constraints, 738,317,504 nonzeros.
- Conservative model-memory estimate: 38.23 GiB; configured `SoftMemLimit`: 80 GiB.
- 24h structural smoke: 358,491 variables, 296,321 constraints, 1,734,974 nonzeros.
- Server: 96 logical CPUs, 125 GiB RAM, 4.3 TiB free under `/data`.
- Server Gurobi package/license: not yet configured.

## Explicit unresolved inputs

- CSP site potential and hourly profiles; CSP remains disabled.
- Observed province-level 2025 PHS floor; current floor is explicitly zero.
- Hydropower station-to-substation mapping; hydro is excluded from trunk augmentation.
- Thermal online fuel term `f_on`; fuel is charged on gross generation only.
- Capacity credits, inertia threshold and spur/trunk proxy costs require sensitivity tests.

The only production entry is `scripts/run_cispo_2030_full_year.py`.
