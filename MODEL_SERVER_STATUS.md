# CISPO 2030 full-year server status

## 2026-07-26 spill A/B reopened; projected 168h accepted; cloud job terminal

- ParaCloud job `4004585` is terminal `TIMEOUT` after `1-00:00:25`; its batch step is `CANCELLED` after `1-00:00:32`. It reached Barrier iteration 35 at solver time 82,521 s, with primal residual `1.05e8`, dual residual `2.68`, complementarity `6.03e6`, primal objective `2.0166e11` and dual objective `-1.4513e13`. It was still far from acceptance.
- Sampled MaxRSS remains 499,919,116 KiB = 476.76 GiB. The run did not produce `solve_report.json`, `solution_qc.json` or `result_manifest.json`; it is neither solved nor evidence of infeasibility. Preserve the cloud root unchanged. No cloud job is active.
- Fixed-server HEAD `ed8e91a` completed `/data/zz2/National_model/outputs/2030_168h_v0726_spill_projection_barrier32` as `OPTIMAL + solution_qc=PASS`: 931,447 original columns; 744,673/757,209/7,053,168 presolved rows/columns/nonzeros; `Factor NZ=1.043e8`; `Factor Ops=8.504e10`; Barrier 182 iterations/585.33 s; total solver runtime 641.996 s; peak process-tree RSS 3.512 GiB. The server is now idle.
- The exact projection is not yet accepted as the default. In a local same-code 24h `flexible_load_comfort_v3` comparison, it increased Factor Ops by 9.62% and runtime from 34.358 s to 45.168 s despite removing 11,376 raw columns. Commit `9e82cc5` restores explicit spill provisionally and adds a machine-readable comparison tool; 67/67 local tests and the repeated explicit 24h solve/QC pass.
- Persistent solver telemetry, graceful termination and six traceable numerics-only solver profiles are validated locally. The user has explicitly authorized sequential fixed-server 744h or longer stress tests provided memory remains safe; this supersedes earlier fixed-server 744h prohibitions for the present engineering campaign. First complete a matched explicit-spill 168h A/B, then compare profiles. Do not run concurrent CISPO solves and do not start fixed-server 8760h.

## 2026-07-25 20:30 CST Barrier-32 reached iteration 23

- Job `4004585` remains `RUNNING` on `m4cg1702` after 17:55:54 and has passed the exact stage where the 128-thread run failed.
- Ordering completed in 3,180.53 s. Gurobi reports `AA' NZ=7.425e8`, `Factor NZ=3.848e10`, approximately 340.0 GB factor memory, `Factor Ops=2.448e15` and `Threads=32`.
- Barrier iteration 23 completed at solver time 60,528 s. Primal residual/complementarity improved from `8.98e9/6.57e8` at iteration 0 to `7.71e8/4.47e7`; the run is progressing but is not converged and its primal/dual objectives remain far apart.
- `sstat` reports 499,919,116 KiB MaxRSS = 476.76 GiB and 499,955,580 KiB MaxVMSize. This is below the prior sampled 526.99 GiB peak, but it does not establish a safe lower bound for future runs.
- Slurm has 6:04:06 remaining and ends at `2026-07-26 02:34:26 CST`. Recent iterations require about 30-32 minutes, so completion within the current 24h wall limit is uncertain. The Slurm limit will arrive before Gurobi's configured 86,400-second optimize limit because model construction consumed about 41 minutes.
- `solve_report.json`, `solution_qc.json` and `result_manifest.json` are absent; only `build_report.json` is present. No scheduler parameter was changed during this read-only audit. Do not start 2040 or another job.

## 2026-07-25 02:35 CST authorized Barrier-32 cloud retry running

- ParaCloud job `4004585` started at `2026-07-25 02:34:26 CST` on `m4cg1702`. It uses the unchanged `22fb493` Base/`city_337` release, 700G and 24h, with only Gurobi `Threads` reduced from 128 to 32 relative to failed job `4003172`; `Method=2`, `Presolve=2`, `Crossover=1`, `SoftMemLimit=640` and all scientific settings remain unchanged.
- The additive script is `cloud_cispo_8760_2030_base_barrier32.sbatch`, SHA256 `fc604a1a25d37c9cff8a336c83969809cb5b52ea0ab815183d1ea3a7a96bfbf2`. Output is isolated under `outputs/full_year_2030_base_22fb493_barrier32_700g_v0725`.
- The 50-test gate passed in 11.845 s. Runtime stdout reports `FULL_SOLVE_CPUS 32`, and `optimization_2030_cloud_32threads_640gsoft.json` confirms `threads=32`, `presolve=2`, `method=2`, `crossover=1` and `soft_mem_limit_gb=640`.
- Although the script requests 32 CPUs per task, Slurm allocated 96 CPU/billing units because the 700G request exceeds the partition's per-CPU memory ratio. Cost accounting therefore accrues at 96 allocated core-hours per wall-clock hour, while Gurobi remains capped at 32 threads.
- Failed job `4003172` consumed 2,642,304 allocated CPU-seconds = 733.973 core-hours. Its actual `TotalCPU` was 7:03:11. The scheduler's account report shows 48,355 CPU-minutes = 805.917 core-hours for user `a8s001819` across all jobs in the 2026-07-24 to 2026-07-26 window, but it exposes no paid-credit or remaining-quota balance.
- This is active engineering evidence, not an accepted scientific result. Do not change the release, start 2040 or submit another retry while `4004585` is active.

## 2026-07-25 02:14 CST cloud 2030/8760h solve failed OOM before barrier

- ParaCloud job `4003172` is terminal `OUT_OF_MEMORY` with exit `0:125`; it ran from `2026-07-24 20:24:47` to `2026-07-25 02:08:50` for 5:44:03 on `m4cg1702`, using 128 CPUs and a 700G request.
- The full model build succeeded earlier. Gurobi then spent 17,932.25 s in presolve, reducing 68,189,325 rows/40,912,327 columns/515,040,080 nonzeros to 37,982,903/35,423,761/400,861,556.
- Ordering for barrier factorization ran for at least 140 s, but no barrier statistics or iteration 0 appeared. The Python process was killed by Slurm before an optimization iterate existed.
- Accounting records 526.99 GiB MaxRSS and 527.03 GiB MaxVMSize; CPU efficiency was 0.96%. The node is configured with 750G and rebooted shortly after the OOM event, so the sampled peak does not establish the true instantaneous memory requirement.
- `solve_report.json`, `solution_qc.json` and `result_manifest.json` are absent. Preserve `outputs/full_year_2030_base_22fb493_128cpu_700g` as failed engineering evidence; it is not accepted.
- No ParaCloud CISPO job is now active. Do not rerun the identical barrier configuration, do not start 2040, and do not treat the successful 53.633 GiB build-only result as evidence that barrier factorization fits.

## 2026-07-25 wave module corrected to existing marine grid; combined cases added; not deployed

- This local correction supersedes the spatial mapping and scale figures in the wave note immediately below; no accepted server/cloud release, checkout, data root, process or output changed.
- Raw wave rows are intersected with existing `optimization_points.csv` coordinates within `0.02` degrees and then restricted to `is_land=0`. The resulting contract contains 1,285 unique existing marine `grid_uid` rows (1,284 positive-potential options), 9,798.111 GW retained raw potential and 57 imputed-CF rows. The actual maximum coordinate difference is `4.96e-5` degrees.
- Province, substation and `city_337` load-center identifiers now reuse the exact existing `grid_uid` route. The prior nearest-offshore-wind proxy, including erroneous model-boundary-external matches up to roughly 1,524 km, is removed.
- Explicit combined cases `wave_energy_medium_v1_flexible_load_v1` and `wave_energy_medium_v1_flexible_load_comfort_v3` enable both modules in one LP while Base and single-module cases remain isolated.
- Wave and wave+flex preflight reports have overall `PASS` status with 72 records each (67 `PASS`, 2 `INFO`, 3 pre-existing unrelated `WARN`); the complete local regression passes 62/62. Base/wave/wave+flex-V1/wave+comfort-V3 24h build-only gates are respectively 342,343/345,992/350,456/352,688 variables, 262,201/263,810/264,647/266,879 constraints and 1,771,704/1,794,509/1,825,757/1,830,221 nonzeros. No optimization was started.
- Full-year static estimates are 41,186,792 variables/67,877,276 constraints/532,990,308 nonzeros/36.47 GB for wave, and 42,816,152/68,182,781/533,906,823/36.91 GB for wave+flex V1. These are not solve-memory guarantees.

## 2026-07-25 optional wave-energy module passed local build gates; not deployed

- Local worktree based on `796a6fc` adds `wave_energy_medium_v1` without changing Base `VRE_TECHS`, accepted server/cloud releases, data roots, processes or outputs.
- The source audit finds 4,194 unique grids, 4,187 positive-potential grids, 35,898.123 GW raw potential, ten CF scenarios, 241 imputed-CF grids and no 2060 profile. Capacity potential is identical in every source scenario.
- `data/wave/wave_sites.csv` and `wave_input_manifest.json` are reproducible from `scripts/build_wave_energy_inputs.py`; hourly data stay external and require `CISPO_WAVE_ROOT`.
- Wave preflight passes 68 checks and the complete local regression passes 61/61. Base 24h build-only remains 342,343 variables/262,201 constraints/1,771,704 nonzeros; wave 24h build-only is 351,798/266,712/1,867,703. No optimization was started.
- Full-year static estimate with wave is 41,192,598 variables, 67,880,179 constraints, 558,429,297 nonzeros and 37.23 GB. This is not a solve-memory guarantee.
- Deployment remains blocked pending review of maritime routing, scenario-specific potential, 2060 treatment and China cost sensitivities. Do not stage `wave_grid.nc`, change a live checkout or start any wave solve without a new versioned release and explicit authorization.

## 2026-07-24 local comfort-aware flexibility V3 accepted at 24h; not deployed

- Local worktree based on `796a6fc` adds independent `flexible_load_comfort_v3` and `flexible_load_comfort_v3_v2g_5pct` scenarios. Base, accepted V1/V2 and server/cloud releases are unchanged.
- The generated ignored-data table `data/load/flexible_load_envelope_v3.csv.gz` contains 1,357,800 province-year-hour rows. It reconstructs the `Power_curve_V2` BAIT/balance-point formula with a +/-1 C setpoint envelope, retains the upstream future `thermal_multiplier`, matches the National_model load components, and has SHA256 `b5ebda4344a8f978606c242065159f27a75994a5d976f2cbe06038d66a429a03`.
- Thermal flexibility is a causal daily-reset equivalent state. EV V1G uses a rolling 12h cumulative latest-service constraint. Optional V2G is limited to 5% of province-day baseline EV peak, has a four-hour energy envelope and requires charge before discharge through a daily-zero causal state.
- Costs are explicit objective components: thermal reduction/increase are separate, V1G relocated energy is paid once, and V2G discharged energy is paid once while charging energy/losses remain in normal system operating costs.
- Local regression passes 58/58. The no-V2G 2030 24h gate `outputs/diagnostic_24h_flexible_load_comfort_v3` is `OPTIMAL + solution_qc=PASS` with 349,039 variables, 265,270 constraints, 1,807,414 nonzeros, 33.63 s solver time and 0.739 GiB peak process-tree RSS.
- The final independent 5% V2G gate `outputs/diagnostic_24h_flexible_load_comfort_v3_v2g_5pct_final` is also `OPTIMAL + solution_qc=PASS`, with 351,271 variables, 266,789 constraints, 1,821,550 nonzeros, 38.60 s solver time and 0.718 GiB peak RSS. V1G and V2G share one aggregate grid-charging power ceiling; its violation is zero. All transition/terminal checks pass and simultaneous operations are zero.
- This is local truncated-horizon engineering evidence only. No server/cloud state was changed or refreshed during this milestone. Do not launch fixed-server 168h/744h/8760h or another cloud job without explicit authorization and a new versioned release.

## 2026-07-24 21:17 CST prior cloud checkpoint (superseded by OOM terminal state)

- Job `4003088` completed normally in 40m20s (`COMPLETED`, exit `0:0`). The full Base model has 40,912,327 variables, 68,189,325 constraints and 515,040,080 nonzeros. Build-only peak process-tree RSS is 53.633 GiB.
- The success dependency released job `4003172`, now running on `m4cg1702` with 128 CPU, 700G and a 24h limit. Its full model build completed in about 40m32s with identical statistics and 53.686 GiB build peak.
- Gurobi 13.0.2 accepted the WLS license, `Threads=128` and `SoftMemLimit=640`, and entered `Optimize`. At the audit checkpoint the log had not yet emitted presolve completion or barrier iterations; current stage is presolve/matrix preprocessing.
- Current `sstat` batch MaxRSS is 101,085,156 KiB (96.402 GiB). This remains far below both the 700G allocation and 640G solver soft limit, but presolve/barrier factorization may increase it further.
- `solve_report.json`, `solution_qc.json` and `result_manifest.json` do not yet exist. The task is healthy but not accepted. Continue monitoring without changing the release or starting 2040.

## 2026-07-24 local `flexible_load_state_v2` accepted; not deployed

- Local implementation `271c6dc` adds an independent state-based flexibility scenario. Base and the accepted legacy V1/V2G scenario JSON files are unchanged.
- Heating/cooling use daily-reset equivalent inventories with explicit retention/efficiency and loss accounting. EV V1G uses a causal charging backlog derived from the immutable `Power_curve_V2` uncontrolled charging baseline; `ev_hour_weight` is not treated as plug availability. The new formulation refuses V2G until calibrated availability, battery-energy and departure-service inputs exist.
- Full local regression passes 56/56. Final 2030 24h gate `outputs/2030_24h_v0724_flexible_load_state_v2_final` is `OPTIMAL + solution_qc=PASS`, with 349,039 variables, 265,270 constraints, 1,807,414 nonzeros, 32.84 s solver time, 0.705 GiB peak process-tree RSS, transition residuals at most `8.88e-16 GWh`, zero terminal state/backlog, zero simultaneous up/down and a valid result manifest.
- Four-year 1h diagnostic chain `outputs/planning_sequence_1h_v0724_flexible_load_state_v2` passes all four solve/QC/manifests and immediate `--resume`. It is engineering evidence only.
- Full-year static estimate is 43,356,367 variables, 68,724,249 constraints, 524,283,387 nonzeros and 36.84 GiB model memory. This is not a barrier-memory guarantee and no 8760h job was started.
- No fixed-server or cloud checkout, process, input or output was changed. Retain the existing active cloud release and output roots unchanged. Any deployment of `271c6dc` requires a new versioned identity and fresh authorized 24h/168h gates.

## 2026-07-24 local post-release hardening; not deployed to active cloud run

- Local code based on `4b5bd98` now forbids wind-to-PV CF fallback, hard-fails unresolved wind after same-grid mixed-wind, and requires land-centroid donors for nearest-province PV fallback. Current data have 35 onwind and 10 offwind same-grid mixed-wind rows, zero wind-to-PV mappings, and 141 PV-family nearest-grid fallbacks; the land-donor restriction changes zero current donor assignments.
- Focused tests pass 4/4 and the full local suite passes 54/54. Two live contract documents now describe production `city_337` as a 337-city annual allocation/transmission proxy, not a 337-city hourly nodal dispatch network.
- This hardening is local only. Do not change the staged cloud release, its checkout, inputs or output roots while its authorized jobs are active. Any later deployment requires a new identity and fresh small gates.

## 2026-07-24 ParaCloud 24h/168h accepted; full-year build and authorized single-year solve active

- Cloud 2030 Base 24h job `4003035` (32 CPU, 64G) and 168h job `4003045` (32 CPU, 64G, `m4ci1805`) each pass 50/50 tests, `OPTIMAL`, `solution_qc=PASS` and independent result-manifest validation. Their solver statistics are respectively 342,343 variables/262,201 constraints/1,771,703 nonzeros/26.978 s/0.834 GiB and 1,011,079/1,393,915/9,797,949/377.057 s/3.661 GiB.
- Full-year build-only job `4003088` is running on `m4cm1904` in `amd_a8_768` with 128 CPU and 700G. It constructs but does not optimize the 2030 Base 8760h LP, writing `outputs/full_year_build_only_2030_22fb493_128cpu_700g`.
- The user explicitly authorized one real 2030/8760h Base solve. Job `4003172` is submitted as `afterok:4003088`, requests 128 CPU, 700G and 24h, writes the separate root `outputs/full_year_2030_base_22fb493_128cpu_700g`, and raises only Gurobi `soft_mem_limit_gb` from the fixed-server 80 to 640. Do not start a successor year or a second full-year run while this evidence is pending.

## 2026-07-24 ParaCloud city_337 release staged; 8760h preflight and repaired WLS smoke passed

- New cloud release: `/publicfs01/fs1-a8/home/a8s001819/National_model_cloud/20260724_city337_22fb493`. It carries code archive `22fb493` (SHA256 `2f3564ff9123b292106e51bd5ee943e13e874b6798450e38a96428a48a3b6b7a`) and exactly 11,350 runtime data files whose cloud SHA256 check matches the fixed-server manifest (`662565a090b64523ec353994e6fdb3314a94b88d429f16e85e1665300ffbc85a`). The release is additive and does not modify the fixed server.
- Cloud preflight job `4001137` completed on `m4ci1905.para.bscc`: 175.17 GiB available memory exceeds the full-year 96 GiB gate. For 2030 Base/city_337 it estimates 40,912,327 variables, 67,604,064 constraints, 520,922,832 nonzeros and 36.0 GiB static model memory. This is a data/scale gate only, not a Gurobi build or solve.
- Cloud environment was completed offline with the project numerical stack and `pip check` passes. The user-authorized repair of the three `.bashrc` proxy exports was verified on compute node `m4ci1905` by job `4002980` (`PROXY_EXPORT_COMPUTE_PASS`, HTTP 302 through `172.16.110.3`). WLS job `4002981` then reached `Env.start()` and solved its LP to `OPTIMAL` with `GUROBI_SMOKE_PASS`. Its standalone 10-second curl check timed out, but the authenticated Gurobi solve is the decisive license evidence.
- No cloud 24h/168h, full-year build-only or full-year solve is active. Next cloud action is a new versioned 24h gate, then a 168h gate, with explicit Gurobi thread limits; the full-year build-only gate remains later. Fixed server remains idle and restricted to its accepted 24h/168h roots; do not start fixed-server 744h/8760h.

## 2026-07-23 city_337 fixed-server 168h V2G accepted; server idle

- Four-year 168h V2G root `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v2g_v1` and immediate `--resume` pass. All years are `OPTIMAL + solution_qc=PASS`; runtimes are 792.55/806.12/953.60/1033.25 s, wall time is 1:09:57, peak RSS is 4,087,888 KiB and swaps are zero.
- Every 59-entry SHA256 manifest validates. The V2G model has 1,057,951 variables, 1,404,982 constraints and 10,100,013 nonzeros. All hard checks pass; maximum center/province/intra/power residuals are `5.12e-12/3.64e-12/3.11e-08 GWh` and `1.60e-10 GW`; BECCS closure is zero.
- V2G transition residual is at most `1.90e-13 GWh`, simultaneous charge/discharge is zero, and period charging losses of 7.747/4.509/13.909/42.092 GWh equal both `charge-discharge` and net-load energy change to numerical precision.
- No CISPO/Gurobi process remains. Base, V1 and V2G have all passed 24h/168h city_337 gates. Do not start fixed-server 744h/8760h without separate authorization.

## 2026-07-23 city_337 fixed-server 24h V2G accepted

- Four-year 24h V2G root `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337_flexible_load_v2g_v1` and immediate `--resume` pass. All years are `OPTIMAL + solution_qc=PASS`; runtimes are 44.81/43.45/48.35/45.23 s, wall time is 9:10, peak RSS is 934,340 KiB and swaps are zero.
- Every 59-entry SHA256 manifest validates. V2G is enabled only in this separate scenario; maximum transition residual is `1.83e-12 GWh`, simultaneous charge/discharge is zero, and 2040/2050/2060 charging losses of 0.1563/2.3423/3.4673 GWh close exactly against net-load energy change within floating-point precision.
- Maximum center/province/intra/power residuals are `6.37e-12/5.24e-13/4.61e-10 GWh` and `2.46e-12 GW`; heating/cooling/EV V1G daily conservation, security and BECCS checks also pass.
- The follow-on 168h V2G chain has completed and is accepted in the newer status section above.

## 2026-07-23 city_337 fixed-server 168h V1 accepted

- Four-year 168h V1 root `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337_flexible_load_v1` and immediate `--resume` pass. Every year is `OPTIMAL + solution_qc=PASS`; runtimes are 714.39/816.08/1007.71/980.09 s, wall is 1:08:59, peak RSS is 4,030,672 KiB and swaps are zero.
- All four 59-entry SHA256 manifests validate. Each year exports 337 center balances, 2,022 center-technology rows, 642 intra edges, 31 province accounts, 31 flexibility accounts and 57 output-catalog data rows. Maximum center/province/intra/power residuals are `5.06e-12/3.64e-12/4.69e-11 GWh` and `1.75e-10 GW`; BECCS closure is zero.
- Maximum heating/cooling/EV V1G daily-energy residuals are `1.17e-12/1.78e-15/4.26e-13 GWh`; simultaneous up/down counts are zero and V2G is disabled. Four `RESUMED_ACCEPTED` records revalidate scenario and strict state-chain identity.
- The V1 matrix has 1,042,327 variables, 1,399,774 constraints and 10,016,685 nonzeros: +3.09%, +0.42% and +2.23% versus Base. Total solver time is nevertheless 8.23% lower; 2050/2060 crossover (265.69/288.77 s) is the remaining performance variability.
- The follow-on 24h V2G chain has completed and is accepted in the newer status section above.

## 2026-07-23 city_337 fixed-server 24h V1 accepted

- Four-year 24h V1 root `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337_flexible_load_v1` and immediate `--resume` pass. Every year is `OPTIMAL + solution_qc=PASS`, has 59 manifest entries and closes the 337-center network; runtimes are 40.84/44.23/43.39/41.95 s.
- The wrapper completed in 9:35 with peak RSS 929,096 KiB, zero swaps and exit status zero. Maximum daily heating/cooling/EV V1G residual is `1.14e-13 GWh`, all simultaneous up/down counts are zero, and V2G is explicitly disabled.
- Capacity margin remains 5%, effective inertia remains 3.5 s, all hard checks pass and BECCS net-carbon closure is zero. These are truncated engineering diagnostics, not scientific planning results.
- The follow-on 168h V1 chain has completed and is accepted in the newer status section above.

## 2026-07-23 city_337 fixed-server 168h Base accepted

- Four-year 168h Base root `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337` is accepted: sequence and `--resume` pass, all years are `OPTIMAL + solution_qc=PASS`, runtimes 733.00/811.58/892.10/1397.12 s, wall 1:13:47, peak RSS 4,085,152 KiB and zero swaps.
- Every year has zero false hard checks, 59 valid manifest entries, 337 center balances, 642 intra-edge outputs and 31 province accounts. Maximum network/power residuals are below `1.78e-10` in their reported units; BECCS closure is numerical zero.
- Relative to the prior 278 Base gate, the 168h city model adds 1,031 variables, 924 constraints and 2,749 nonzeros. Total solver time rises 4.68%; the measurable risk is 2060 Crossover (706.6 s), not model construction or memory.
- The follow-on 24h `flexible_load_v1` chain has completed and is accepted in the newer status section above.

## 2026-07-23 city_337 fixed-server 24h accepted; 168h active

- Fixed-server checkout is clean at `cf39e0a`; active data root is `/data/zz2/National_model/data/model_ready_20260723_v0722_city337`. The city archive SHA256 matches local: `c1451d95c3303f98e53434cd29abc4288f486cba04c99a2c591380b010d470bb`.
- Server regression is 50/50, smoke is 142/142, readiness/full-license and preflight pass. The initial 139-check smoke failure was an obsolete 8-technology row expectation; the production table is correctly 31×5×10=1,550 unique rows and the corrected smoke now validates this explicitly.
- Four-year 24h Base root `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_city337` and immediate `--resume` are `PASS`. Runtimes are 43.29/48.82/41.17/46.90 s, wall time 7:21, peak RSS 930,204 KiB, and all four 59-file manifests validate. Base flexibility is disabled; 5% capacity margin, 3.5 s inertia, power/network/BECCS checks all pass.
- The new four-year 168h Base chain is active as PID `3321747` under `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_city337`. Do not change checkout or data root until it exits and is audited. Do not start 744h/8760h.

## 2026-07-23 city_337 local gate and pre-deployment server audit

- Local implementation commit `8e76753` promotes `city_337` to production while retaining `natural_earth_278` as a separate CISPO replication/sensitivity package. The package has 337 centers, 16,609 VRE routes, 2,030 hydropower routes, 642 intra-provincial edges and 203 positive 2025 initial edges.
- Data QA is `PASS`: 31 connected provincial graphs, province demand-share error at most `1.11e-15`, initial network-balance residual at most `7.28e-14 GW`, and exact joint routing is never materially worse than the old nearest-substation-first rule (mean distance reduction 20.21 km).
- Local validation passes 50/50 tests and 61 preflight checks. `outputs/planning_sequence_1h_v0722_city337` passes all four years and `--resume`; each year is `OPTIMAL + solution_qc=PASS`, has 337 load-center rows, a closed 59-file result manifest, Base flexibility disabled, 5% capacity margin and 3.5 s effective inertia.
- Live fixed-server audit before deployment: branch `codex/cispo-2030-full-lp`, clean HEAD `6ed943a`, no active CISPO/Gurobi process, about 35 GiB available memory, 21 GiB swap occupied and 3.8 TiB free on `/data`. The accepted V1 168h root remains `PASS` after its prior four-year resume audit.
- Exact next gate: push/deploy the code plus a SHA256-verified additive `city_337` data root, pass server tests/readiness, then use new 24h and 168h Base output roots. Do not reuse accepted roots and do not launch fixed-server 744h/8760h or paid cloud 8760h.

## 2026-07-22 reviewed reliability parameters (local only)

- Local Git HEAD remains `e28f315`; the working tree now sets Base provincial capacity margin to `5%` and minimum inertia to `3.5 s reference × 1.0 tolerance = 3.5 s effective`.
- Model construction and solution QC use the same effective-threshold resolver. Legacy scenario overrides containing `minimum_system_inertia_seconds` remain accepted and take precedence within that scenario.
- Local regression tests pass 49/49. Local 1h output `outputs/2030_1h_v0722_security_5pct_inertia_3p5s` is `OPTIMAL + solution_qc=PASS`; effective inertia is `3.5 s`, capacity-margin/inertia checks pass and the result manifest validates. No fixed-server checkout change, server process or server output was created.
- Fixed-server checkout and all accepted Base/V1 gates remain at their previously recorded versions and therefore still reflect the old committed security configuration. Do not compare new local results against those outputs without identifying this feasible-set change.
- The next server action, if authorized, is a new versioned 24h gate after committing/pushing/deploying the exact reliability update. Do not reuse accepted output roots and do not start fixed-server 744h/8760h or paid cloud 8760h.

## 2026-07-22 V0722 flexibility deployment and server gates (authoritative)

- Local commit `c62b769` closes the CISPO-equivalent BECCS carbon mass balance without changing the published net factors, objective or feasible set. Local validation is 47/47 tests plus an `OPTIMAL/QC PASS` 1h gate with zero new closure residuals and a valid manifest. This commit is not deployed; the fixed server remains unchanged at `6ed943a`, and no new server job was started.
- Local commit `c91828a` adds a diagnostic sensitivity-suite runner and passes 45/45 tests plus a real 1h Base/V1/V2G suite (12/12 year-scenario cases `OPTIMAL + solution_qc=PASS`, closed manifests, identity-safe `--resume`). This is local interface evidence only: the runner is not deployed, no server job was started, and the fixed-server checkout remains clean and idle at `6ed943a`.
- Commit `6ed943a` implements the optional flexibility/scenario interface and is now the clean fixed-server checkout. It passes 42/42 local and server tests plus local Base 1h, V1 24h and V2G 24h `OPTIMAL/QC PASS` gates.
- The fixed-server Base 168h gate ran from checkout `b6ca42d`, whose model implementation baseline is `0c1eaf2`; this corrects the earlier shorthand that described the checkout itself as `0c1eaf2`. The active data root remains `/data/zz2/National_model/data/model_ready_20260722_v0721_fuel_state`.
- The server four-year 24h sequence and immediate resume audit pass for 2030/2040/2050/2060.
- Four-year 168h Base sequence `/data/zz2/National_model/outputs/planning_sequence_168h_v0721_fuel_state` completed `PASS`: all years are `OPTIMAL + solution_qc=PASS`, every result manifest validates, the resume identity audit passes, wall time is 1:08:40, peak RSS is 4,116,892 KiB and swap is zero.
- Four-year 24h `flexible_load_v1` sequence `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_flexible_load_v1` completed `PASS` and passed resume identity validation. Wall time is 6:32, peak RSS is 946,804 KiB and all daily flexibility residuals are below `6.44e-13 GWh` with no simultaneous up/down.
- Four-year 168h `flexible_load_v1` sequence `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_flexible_load_v1` completed `PASS` from clean checkout `6ed943a`; PID `1708266` has exited and no CISPO process remains. All four years are `OPTIMAL + solution_qc=PASS`, all hard checks pass, and every 59-file result manifest validates. Solver runtimes are 705.49/672.16/994.41/1181.26 s; wall time is 1:06:54, peak RSS is 4,040,256 KiB and swap is zero. Maximum heating/cooling/EV V1G daily-energy residual is `8.17e-13 GWh`, simultaneous up/down counts are zero, and scenario SHA256 is consistently `7b8f1c920bad35e2e41111f7913cfb456b6e369b85db5b03ae86d43801840532`.
- A fresh 168h `--resume` identity audit at 2026-07-22 16:05 CST completed `PASS` with four `RESUMED_ACCEPTED` years. The accepted capacity-cohort chain remains explicitly `TEST_ONLY_TRUNCATED_HORIZON` and cannot enter production.
- Flexibility is disabled in Base. Local full-year static estimates are 40.91M variables for Base, 42.54M for V1 and 43.36M for V2G; the 96 GiB availability gate remains unchanged.
- No fixed-server 744h/8760h and no cloud 8760h task is running. The V1 168h gate is now accepted, but cloud production remains gated on calibrated sensitivity assumptions, exact code/data/scenario deployment, cloud 24h/168h gates, explicit Slurm thread limits and explicit cost authorization.

## 2026-07-20 V0720 I/O-contract deployment (authoritative)

- Fixed-server checkout is clean at `b40900a`; active model data are `/data/zz2/National_model/data/model_ready_20260719_v0719_capacity_bounds` with the existing versioned hydrology and CF stores.
- Server unit tests pass 34/34 and data-package smoke checks pass 139/139.
- New 24h gate `/data/zz2/National_model/outputs/2030_24h_v0720_io_contract_server` is `OPTIMAL + solution_qc=PASS`: 341,312 variables, 261,280 constraints, 1,768,957 nonzeros, objective `2,024,722.739184 million CNY`, solve time 43.65 s and peak RSS 0.838 GiB.
- All 27 hard checks pass. The SHA256 result manifest is closed with zero mismatches; all NPZ files are pickle-free; the output catalog has 50 files, the field dictionary has 493 rows, and LP dual export contains 744 hourly price rows plus 3,366 annual constraint-shadow rows.
- At launch, about 88 GiB RAM was available. Another user's four Python training processes occupied about 29 GiB RSS and were not changed. This was safe for 24h only and remains below the 96 GiB full-year build gate.
- No 744h or 8760h process is running. The next full-year solve belongs on the cloud platform after compute-node Gurobi licensing, data staging and small gates are verified.
- The old `5a9f4ab` 744h result remains an engineering solvability gate, not a V0720 or scientific-horizon result. Its old manifest has two wrapper-after-hash mismatches (`run.stdout`, `run.time`); see `MODEL_744_SERVER_RUN_AUDIT_20260720.md`.

## 2026-07-19 V0719 deployed server status (authoritative)

- Current server checkout is `bc83663`, including V0719 capacity-bound/DC active-index commit `451b1c0` plus server smoke-test path fixes `c8db9be` and `bc83663`.
- Active V0719 data root is `/data/zz2/National_model/data/model_ready_20260719_v0719_capacity_bounds`. It was created additively; the old `model_ready_20260719_sequential_sparse` root and the completed 744h output were not overwritten.
- Generated V0719 tables are present: `thermal/nuclear_capacity_upper_by_year.csv`, `biomass/capacity_upper_by_province_year.csv` and `storage/battery_capacity_floor_by_province_year.csv`. The root also includes `sets/model_years.csv` and canonical smoke/QC support files that were absent from the old sparse root.
- Server smoke checks passed 139/139, server unit tests passed 32/32 and readiness passed with full Gurobi license plus raw-GRFR SHA256 verification.
- Server 24h V0719 solve `/data/zz2/National_model/outputs/2030_24h_v0719_capacity_bounds_server` reached `OPTIMAL + solution_qc=PASS`: 341,312 variables, 261,280 constraints, 1,768,957 nonzeros, objective `2,024,722.7392 million CNY`, Gurobi runtime 48.96 s and peak process-tree RSS 0.841 GiB. Nuclear floor/upper, biomass+BECCS capacity upper, storage floor, AC bidirectionality and DC reverse-flow hard checks are all zero.
- Requested direct 8760 trial was not launched because the live full-year preflight failed the checked memory gate: `/data/zz2/National_model/outputs/2030_8760_v0719_preflight_memory_check` reported available memory `73.15 GiB` against required `96.0 GiB`. The V0719 full-year estimate is 40,911,296 variables, 67,603,283 constraints and 520,920,489 nonzeros.
- The completed pre-V0719 sparse 744h gate `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` remains valid solver evidence for deployed HEAD `5a9f4ab`, but it is not the V0719 scientific boundary.
- Sections below this heading include older handoff snapshots; use this authoritative section for current deployment and launch decisions.

## 2026-07-19 V0719 local capacity-bound correction

- Local working tree based on Git HEAD `f84143a` / implementation base `5a9f4ab` now implements four reviewed corrections: provincial nuclear upper bounds, shared `bio+bioccs` capacity upper bounds, the CISPO Table S17 2030 battery floor, and active-index AC-only reverse-flow variables.
- New reproducible inputs are generated by `scripts/build_v0719_capacity_bounds.py` from `config/capacity_bounds_v0719.json`; `config/model_input_files.json` contract v2 requires all three new tables.
- Local unit tests passed 32/32; data-package smoke checks passed 139/139. The corrected 24h solve under `outputs/2030_24h_v0719_capacity_bounds_dc_sparse_rerun` reached `OPTIMAL + solution_qc=PASS` with 341,312 variables, 261,280 constraints and 1,768,956 nonzeros. Every nuclear/biomass/storage bound residual and every transmission-direction hard check passed.
- Full-year active-index estimate is now 40,911,296 variables, 67,603,283 constraints and 520,920,489 nonzeros; exact variable reduction is `363×8760=3,179,880`. This is a structural estimate, not barrier-memory proof.
- This local V0719 correction is **not yet committed, deployed or used by the server**. The server remains at `5a9f4ab` and its current versioned data root remains unchanged.
- Server check at 2026-07-19 20:14 Asia/Shanghai: corrected old-code 744h gate `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` has completed. `solve_report.json` reports `OPTIMAL`; `solution_qc.json` reports `PASS`. It used the old versioned data root and did not include the uncommitted V0719 capacity-bound/DC active-index corrections.

## 2026-07-19 synchronized server validation

- Current deployed implementation `5a9f4ab`; readiness/raw-GRFR/full-license gates and 29/29 server tests pass.
- Strict corrected 168h output `/data/zz2/National_model/outputs/2030_168h_sparse_gate_strict`: 1,071,032 variables, 1,392,960 constraints, 10,100,058 nonzeros, `OPTIMAL` in 666.45 s, peak RSS 3.910 GiB and `solution_qc=PASS`. AC bidirectional edge-hours and DC reverse flow are both zero.
- Corrected 744h CPU gate under `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` completed with `OPTIMAL + solution_qc=PASS`: 3,955,064 variables, 5,919,746 constraints, 43,707,940 nonzeros, objective `2,196,413.3453 million CNY`, Gurobi runtime 16,245.79 s, wall time 4:37:02 and peak process-tree RSS 21.979 GiB. Directionality QC passed with zero AC bidirectional edge-hours and zero DC reverse flow.
- Full-year available-memory gate is now checked in as 96 GiB; the unused `NodefileStart`-style config was removed because this is a continuous LP, not branch-and-bound.
- Solvability audit `ab9dfe8` revises the current-code 8760 projection to approximately 44,091,176 variables, 68,188,384 constraints and 515-524 million nonzeros. The prior 853.5 million nonzero preflight is conservative for the raw matrix, but the reported 46.62 GiB is not a barrier peak-memory estimate.
- The rejected 744h barrier formed `8.289e8` factor nonzeros (about 10 GB), then spent 10,969.01 s in barrier and 9,123.64 s in crossover. Linear factor-memory extrapolation is already about 118 GB at 8760h before the model and workspaces are counted; a direct solve on this 125 GiB host is therefore high risk.
- Earlier pre-launch resource snapshot: server HEAD was `f22b9cf`, about 30 GiB available RAM and 21 GiB/21 GiB swap occupied. This snapshot is superseded by the active corrected 744h status recorded above; 8760 was not launched.
- Full-year build-only requires at least 96 GiB available RAM after V0719 server gates, not merely after this old-code 744h. A successful build-only does not authorize solve; inspect peak RSS and factor-risk estimates first.

- Current implementation commit: `1b6da28` (`fix: align interprovincial flows with CISPO`).
- The production sequence is now 2030/2040/2050/2060, with checksummed capacity-cohort transfer between successive full-year solves.
- Local final 24h gate: 349,962 variables, 260,973 constraints, 1,827,245 nonzeros; `OPTIMAL` in 58.79 s; `solution_qc=PASS`; peak RSS 0.698 GiB.
- Local full-year preflight: 44,090,772 variables, 67,603,314 constraints, 853,505,952 estimated nonzeros and 46.62 GiB estimated model memory; local available RAM does not meet the 64 GiB build gate.
- PHS now uses the GHT 2026 province-level 8h-storage floor/project-pipeline upper: 2030 national floor 65.94 GW and upper 249.191 GW; 2040+ upper 514.755 GW.
- Server readiness and raw-GRFR SHA256 verification passed on the 2026-07-19 versioned data roots; server regression tests passed 24/24.
- Server 24h gate: 349,962 variables, 260,973 constraints and 1,827,246 nonzeros; `OPTIMAL` in 60.53 s; `solution_qc=PASS`; peak RSS 0.851 GiB.
- PID `3778049` completed `OPTIMAL`, but the result is rejected: 3,358 material simultaneous AC-direction edge-hours were omitted from the former hard QC. The corrected formulation still needs new server gates.
- Do not start 8760 on the old scientific boundary. The sparse cleanup and corrected 744h gate have passed for deployed HEAD `5a9f4ab`, but V0719 capacity-bound/DC active-index corrections still need commit, deployment to a new versioned data root and fresh 24h/168h/744h gates. Require at least 96 GiB available RAM for build-only; a direct solve remains blocked pending true build/factor-memory review.

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

- Current deployed implementation baseline: `827b37f` on 2026-07-19; it contains implementation commit `2a0ee99`. Verify the live HEAD directly because documentation-only synchronization commits follow this baseline.
- Current validated server data paths:
  - `CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260719_sequential_sparse`
  - `CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse`
  - `CISPO_RAW_GRFR_ROOT=/data/zz2/National_model/data/grfr_raw_2019`
- Raw GRFR transfer completed on 2026-07-06 and was verified on the server:
  - `output_pfaf_03_2019.nc`: 3,380,260,808 bytes, SHA256 `84ff2c882fb17a4b8693bb0773718c2472038021b64618b05f99f8070a506e0f`.
  - `output_pfaf_04_2019.nc`: 5,445,519,752 bytes, SHA256 `e56d5da855ddbdafabdafcb5582981b3f0003054156cf8d912d24a9efd232756`.
- Server readiness with `--require-raw-grfr --verify-raw-grfr-sha256`: `PASS`, zero hard failures.
- Hydropower station input: 2,030 rows, 620 reservoir rows, 1,410 run-of-river rows, 0 potential paper-rule mismatches, no missing required columns. Cascade readiness reported 142 nodes, 124 edges, 4 low-correlation edges, 18 max-bound edges and maximum lag 168 h.
- Server regression test on the synchronized checkout/data: 24/24 tests passed with `unittest` in 19.62 seconds.
- Current one-month preflight: 3,954,660 estimated variables, 5,912,178 constraints, 73,853,760 nonzeros and 4.08 GiB estimated model memory.
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
- The old 744h solve under `/data/zz2/National_model/outputs/2030_one_month_hydro_cascade` was normally interrupted after `37,576.53 s`. Final status is `INTERRUPTED`, `solution_count=0`, and peak RSS is `22.161 GiB`; the output is preserved as the failed numerical baseline.
- Commit `281f9c7` scales water flow/volume variables without changing physical equations. Server 168h validation under `/data/zz2/National_model/outputs/2030_diagnostic_168h_numerics_scaled` reached `OPTIMAL` in `675.56 s`, used `4.061 GiB` peak RSS and passed every `solution_qc.json` hard check.
- Commit `a8cd150` switches hydropower environmental flow to the 2019 single-year monthly P30 proxy and removes obsolete master boundary variables. Server 24h P30 CPU validation under `/data/zz2/National_model/outputs/2030_diagnostic_24h_p30_cleanup_cpu` reached `OPTIMAL` in `45.06 s`, used `0.879 GiB` peak RSS and passed `solution_qc.json`.
- GPU-enabled Gurobi is available only in `/home/zz2/.local/envs/cispo-gurobi-gpu` (`gurobipy 13.0.2+cu129`). It confirmed `Start PDHG on GPU`, but the same 24h model with GPU-PDHG was still iterating after about 600 s and was interrupted without `solve_report.json`; CPU barrier remains the default route.
- PID `3778049` completed with 3,955,002 variables, 5,919,470 constraints and 44,169,131 nonzeros; build 348.74 s, solve 20,118.58 s and peak RSS 22.141 GiB. Although the old report says `solution_qc=PASS`, post-audit found 3,358 material bidirectional edge-hours, so the output is explicitly rejected and 8760h remains blocked.
- Commit `1b6da28` aligns with CISPO S4-55/S4-56: AC shared bidirectional capacity, DC fixed direction, `0.001 yuan/kWh = 1 yuan/MWh` flow cost, net-exchange load-center closure and hard directionality QC. Local 26/26 tests and corrected 24h `OPTIMAL/QC PASS` succeeded with zero AC bidirectionality and zero DC reverse flow.
- Corrected server validation also passed: 26/26 tests; 24h Gurobi 13.0.2 `OPTIMAL` in 43.88 s; 0 AC bidirectional edge-hours; 0 DC reverse flow across 363 DC edges; all hard QC and scientific manifest hashes PASS. Output: `/data/zz2/National_model/outputs/2030_diagnostic_24h_20260719_cispo_flow_alignment_cpu`.
- Corrected 744h was initially deferred when available RAM was only about 32 GiB and swap was full; it was launched later after memory pressure cleared and completed `OPTIMAL/QC PASS`. Current authoritative status is recorded at the top of this file.

## Explicit unresolved inputs

- CSP site potential and hourly profiles; CSP remains disabled.
- Open-loop and closed-loop PHS hydraulic pairing data remain unavailable; current PHS is province-level 8h storage with GHT 2026 operating floor and year-available project upper.
- Thermal online fuel term `f_on`; fuel is charged on gross generation only.
- Hydropower type labels include low-confidence assigned labels because source data do not provide reliable type labels for all stations; retain them for now and validate later against external station evidence.
- Formal multi-year environmental flow for hydropower; the current cleanup uses the requested 2019 single-year monthly P30 proxy, not a formal 1980-2019 climatological P30. Four low-correlation and eighteen max-bound cascade-lag edges need manual hydrological/topological review.
- Capacity-credit values and spur/trunk proxy costs still need parameter-source review. Base capacity margin and inertia threshold are reviewed locally at `5%` and `3.5 s` but are not yet deployed on the fixed server.
- Intra-center annual capacity uses a 50% design utilization assumption; two western AC500 proxy edges exceed the 1000 km source range.
- Intra-center losses remain zero until their annual energy can be fed back into the provincial hourly balance.

Per-year production entry: `scripts/run_cispo_2030_full_year.py`.
Sequential production entry: `scripts/run_cispo_planning_sequence.py`.
