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

- Latest cloud gate (2026-07-21): Slurm job `3975741` on `m4cl2501.para.bscc` explicitly set the HTTP proxy, reached `token.gurobi.com` through `172.16.110.3:8888` (HTTP 302), and solved a Gurobi 13.0.2 WLS smoke LP to `OPTIMAL` with `GUROBI_SMOKE_PASS`. The account `.bashrc` still contains non-standard whitespace after `export`; every job must set proxy variables explicitly until repaired. The cloud endpoint is ready for staged 24h/168h CISPO gates, not yet for paid 8760h production.

- Handoff version: `v0.9.2`
- Snapshot date: `2026-07-22`
- Local repository: `D:\codeenv\pycharmproject\National_RL\National_model`
- Git branch: `codex/cispo-2030-full-lp`
- Before this continuity update, the local and pushed branch was clean outside the preserved user-owned `supplementary_materials/**` changes at documentation commit `d00d1fb` (`docs: distinguish model and handoff commits`) atop model implementation `6ed943a` (`feat: add modular demand flexibility scenarios`). The fixed-server checkout was independently verified clean at `6ed943a` while the 168h flexibility chain completed; no checkout change occurred during the run or its acceptance audit. The immediately preceding fixed-server Base gate ran from checkout `b6ca42d`, whose model implementation baseline is `0c1eaf2`. `6ed943a` preserves Base by default, reads the existing four-component load contract, adds checksummed partial scenario overrides, daily-conserving heating/cooling/EV V1G flexibility, optional daily-cyclic V2G, complete flexibility outputs/QC and scenario-safe sequential resume checks.
- A separate ParaCloud/BSCC-A8 endpoint was authenticated on 2026-07-20 through both configured IPv4 routes using the existing local public key. The remote host was `ln301.para.bscc`, account `a8s001819`; port 22 is primary and 2222 is fallback. Read-only audit confirms this is a Slurm login node. The official BSCC-A8 manual was reconciled into `supplementary_materials/云服务器使用规范_BSCC-A8.md`; current live partition names override the older screenshot values. The official Gurobi 13.0.2 Linux package is staged privately on the cloud, and engineer-provided `gurobipy310` was exercised in compute-node jobs `3975724` and `3975741`. With explicit proxy variables, both jobs reached the WLS endpoint through `172.16.110.3:8888` and solved a tiny LP to `OPTIMAL` under Gurobi 13.0.2; `3975741` additionally confirmed the route with HTTP 302 and `GUROBI_SMOKE_PASS`. The account `.bashrc` still contains non-standard whitespace after `export`, so proxy variables must be set explicitly in each job until that file is repaired. The cloud endpoint is technically ready for a staged CISPO gate, but not yet approved for paid 8760h production until code/data staging, explicit thread limits and 24h/168h gates pass.
- SSH access was restored on 2026-07-19 by using the configured `national-model-server` alias, which binds the approved workstation source address. The obsolete PID `863603` was not active and no CISPO solve process remained.
- Server readiness, raw-GRFR SHA256 verification and 24/24 regression tests passed on the new versioned data roots. The server 24h gate is `OPTIMAL` in 60.53 s with `solution_qc=PASS`.
- After commit `1b6da28`, server regression tests passed 26/26 and the corrected 24h transmission gate reached `OPTIMAL` in 43.88 s with all directionality/QC/manifest checks passing.
- PID `3778049` completed mathematically `OPTIMAL`, but its result is rejected as a physical model gate because the prior QC omitted 3,358 material AC bidirectional edge-hours.
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
- Nuclear upper bounds, a shared `bio+bioccs` capacity upper, the CISPO Table S17 2030 battery floor and AC-only reverse-flow active indexing are committed and deployed. V0720 changes only provenance, exports, diagnostics and state acceptance; it does not change the feasible set.
- DAC, annual carbon and biomass accounting, CCS capture and point-level injection.
- Spur line, trunk line and substation augmentation.
- The production load-center scenario is the 278-node Natural Earth paper replication.
- Annual load-center energy allocation, provincial export closure and 517-edge intraprovincial AC500 proxy expansion layer are implemented.
- Wind, solar and hydropower use spatial spur/trunk routing. Thermal, nuclear and biomass generation are allocated within each province by load-center demand shares.
- Optional `flexible_load_v1` and `flexible_load_v2g_v1` modules are implemented behind explicit scenario files. Base creates no flexibility variables. The current values are illustrative sensitivity assumptions, not calibrated transport/building parameters and not CISPO source values.

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
export CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse
export CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260722_v0721_fuel_state
export CISPO_RAW_GRFR_ROOT=/data/zz2/National_model/data/grfr_raw_2019
export GRB_LICENSE_FILE=/home/zz2/gurobi.lic
PYTHON=/home/zz2/.local/envs/cispo-2030/bin/python
```

### Latest verification evidence

- Local `6ed943a` validation: 42/42 regression tests pass; Base 1h, `flexible_load_v1` 24h and `flexible_load_v2g_v1` 24h all reach `OPTIMAL + solution_qc=PASS`; all three result manifests validate with zero mismatches. The V1 24h run has daily heating/cooling/EV closure errors below `2e-13 GWh`, no simultaneous up/down and reduces the test-period national peak from 1229.55 to 1215.78 GW. The V2G run has maximum SOC-transition residual `5.55e-17 GWh`, zero simultaneous charge/discharge and records 0.0231 GWh of charging-loss energy. These are truncated engineering gates, not planning results.
- The active load table contains 1,357,800 rows for 31 provinces, five model years and 8,760 h per province-year. `demand_gw = base_residual_gw + heating_gw + cooling_gw + ev_gw` closes to `8.53e-14 GW` on the loaded arrays and all components are nonnegative. The refreshed parameter audit expands 11,681 runtime rows with 22 PASS, 0 WARN and 0 HARD_FAIL; seven scientific risks remain open.
- Full-year static estimates are Base 40.91M variables/67.60M constraints/36.00 GiB, flexibility V1 42.54M/67.91M/36.44 GiB and V2G 43.36M/68.18M/36.70 GiB. These are construction estimates and do not reduce the 96 GiB availability gate or bound barrier factor memory.
- V0721 implementation `0c1eaf2` is pushed and deployed to the fixed server. Local and server regression tests pass 37/37. The local real 1h 2030→2040→2050→2060 diagnostic chain and a subsequent `--resume` audit both report `PASS`; all four years are `OPTIMAL + solution_qc=PASS + accepted state`.
- New server data root `/data/zz2/National_model/data/model_ready_20260722_v0721_fuel_state` was copied additively from the V0719 root and receives only the rebuilt fuel tables. SHA256 matches the local files: `province_fuel_prices.csv` = `b6867259317b419bc8b35aedf6b614fd930cf0eed9620fdddeca6fc6434c50a1`; `province_fuel_generation_cost_by_year.csv` = `e1133fbfc798a15524e3ee920a0c6e3e771206874427abcef7db399227df94cd`.
- Local and server parameter audits each expand 11,658 active runtime parameter rows and report 22 PASS, 0 WARN, 0 HARD_FAIL, with seven scientific risks retained separately. Province-level biomass/BECCS fuel costs now cover every model province and are no longer zeroed in the objective.
- Fixed-server 24h four-year diagnostic sequence `/data/zz2/National_model/outputs/planning_sequence_24h_v0721_fuel_state` and a subsequent `--resume` chain-identity audit both report `PASS`. All four years are `OPTIMAL + solution_qc=PASS`; solver runtimes are 49.42/46.49/45.98/45.74 s, wall time is 6:03 and peak RSS is 0.879 GiB. States are explicitly `TEST_ONLY_TRUNCATED_HORIZON`.
- Fixed-server Base 168h four-year diagnostic sequence `/data/zz2/National_model/outputs/planning_sequence_168h_v0721_fuel_state` completed `PASS` for 2030/2040/2050/2060 and passed an immediate `--resume` identity audit. All four years are `OPTIMAL + solution_qc=PASS`; solver runtimes are 708.80/708.69/1107.69/1137.22 s, wall time is 1:08:40, peak RSS is 4,116,892 KiB and swap is zero. Each result manifest validates with zero mismatches. It ran from checkout `b6ca42d` containing implementation `0c1eaf2` and is retained as the uncontaminated pre-flexibility Base gate.
- After deployment to `6ed943a`, the fixed server passes 42/42 regression tests with all three external data roots explicit. Four-year 24h `flexible_load_v1` sequence `/data/zz2/National_model/outputs/planning_sequence_24h_v0722_flexible_load_v1` and its immediate resume audit both report `PASS`: all years are `OPTIMAL + solution_qc=PASS`, wall time is 6:32, peak RSS is 946,804 KiB and swap is zero. Daily heating/cooling/EV residuals are at most `6.44e-13 GWh`, simultaneous up/down counts are zero, all manifests validate, and every input manifest records scenario SHA256 `7b8f1c920bad35e2e41111f7913cfb456b6e369b85db5b03ae86d43801840532`.
- Fixed-server four-year 168h `flexible_load_v1` sequence `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_flexible_load_v1` completed `PASS` from clean checkout `6ed943a`; PID `1708266` has exited and no CISPO process remains. All four years are `OPTIMAL + solution_qc=PASS`, every hard QC check passes, and each 59-file result manifest validates with zero size/SHA256 mismatches. Solver runtimes are 705.49/672.16/994.41/1181.26 s; wall time is 1:06:54, peak RSS is 4,040,256 KiB and swap is zero. Heating/cooling/EV V1G daily-energy residuals are at most `8.17e-13 GWh`, all simultaneous up/down counts are zero, and every input manifest records scenario SHA256 `7b8f1c920bad35e2e41111f7913cfb456b6e369b85db5b03ae86d43801840532`. A fresh `--resume` identity audit reports four `RESUMED_ACCEPTED` years and sequence `PASS`; diagnostic states remain `TEST_ONLY_TRUNCATED_HORIZON`.
- The pre-fix V0720 2030 168h comparison gate completed `OPTIMAL + solution_qc=PASS` under `/data/zz2/National_model/outputs/2030_168h_v0720_io_contract_server`: solver runtime 799.07 s, wall time 16:06, peak process-tree RSS 3.762 GiB. It omits biomass fuel cost and is retained only as a comparison baseline.
- V0720 implementation `b40900a` is pushed and deployed to the clean fixed-server checkout. Local and server unit tests pass 34/34; the V0719 server data package passes 139/139 smoke checks.
- Server 24h I/O-contract gate `/data/zz2/National_model/outputs/2030_24h_v0720_io_contract_server` reached `OPTIMAL + solution_qc=PASS`: 341,312 variables, 261,280 constraints, 1,768,957 nonzeros, objective `2,024,722.739184 million CNY`, Gurobi runtime 43.65 s and peak process-tree RSS 0.838 GiB. All 27 hard checks pass; result-manifest validation has zero mismatches; all NPZ files load with `allow_pickle=False`; dual export contains 744 hourly and 3,366 annual rows.
- The output contract now includes immutable configuration/environment/input manifests, a 50-file output catalog, a 493-row data dictionary, province-technology capacity and generation tables, security/adequacy/resource diagnostics, hourly marginal prices, annual shadow prices and verified capacity-cohort state transfer. Detailed definitions are in `MODEL_IO_CONTRACT.md`.
- The pre-V0719 744h run at old commit `5a9f4ab` is an accepted engineering gate only. Its solver/QC passed, but the old result manifest is not closed: `run.stdout` and `run.time` were modified by the wrapper after hashing. See `MODEL_744_SERVER_RUN_AUDIT_20260720.md`.
- V0719 local capacity-bound/DC-sparse correction: 32/32 unit tests PASS; 139/139 data-package smoke checks PASS; strict 24h output `outputs/2030_24h_v0719_capacity_bounds_dc_sparse_rerun` reached `OPTIMAL + solution_qc=PASS` with 341,312 variables, 261,280 constraints, 1,768,956 nonzeros, 39.79 s solver time and 0.702 GiB peak RSS.
- New bound QC is zero for nuclear floor/upper, shared biomass+BECCS upper and battery/PHS floor. DC reverse maximum and AC bidirectional edge-hours are zero; maximum power-balance residual is `7.43e-12 GW`.
- Full-year V0719 estimator: 40,911,296 variables, 67,603,283 constraints, 520,920,489 nonzeros and about 36.0 GiB static model memory. Exact DC variable removal is `363×8760=3,179,880`; no runtime or factor-memory speedup is inferred from this structural reduction.
- Server V0719 deployment root is `/data/zz2/National_model/data/model_ready_20260719_v0719_capacity_bounds`. It was copied additively from the completed sparse root, then supplemented with the three generated V0719 bound tables, `sets/model_years.csv` and 28 canonical smoke/QC/source files that were absent from the old sparse root. The old root and completed 744h output were not overwritten.
- Server V0719 gates on 2026-07-19: checkout HEAD `bc83663`; readiness PASS; 32/32 unit tests PASS; 139/139 smoke checks PASS; 24h solve `/data/zz2/National_model/outputs/2030_24h_v0719_capacity_bounds_server` reached `OPTIMAL + solution_qc=PASS` with 341,312 variables, 261,280 constraints, 1,768,957 nonzeros, objective `2,024,722.7392 million CNY`, Gurobi runtime 48.96 s, peak RSS 0.841 GiB and zero nuclear/biomass/storage/DC/AC hard-check violations.
- Requested 8760 direct trial was not launched because the live memory gate failed: `scripts/run_cispo_2030_full_year.py --horizon full_year --preflight-only --output-dir /data/zz2/National_model/outputs/2030_8760_v0719_preflight_memory_check` reported available memory `73.15 GiB` versus required `96.0 GiB`. It produced a V0719 full-year estimate of 40,911,296 variables, 67,603,283 constraints, 520,920,489 nonzeros and 36.0 GiB static model memory; no full-year model was built or solved.
- Server 744h strict gate `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` completed on 2026-07-19 19:44 Asia/Shanghai under deployed HEAD `5a9f4ab`. It reached `OPTIMAL + solution_qc=PASS`: 3,955,064 variables, 5,919,746 constraints, 43,707,940 nonzeros, objective `2,196,413.3453 million CNY`, solver runtime 16,245.79 s, wall time 4:37:02 and peak process-tree RSS 21.979 GiB. Hard QC passed with zero bidirectional interprovincial edge-hours, zero DC reverse flow, maximum power-balance residual `3.64e-10 GW`, and maximum constraint/bound/dual violations `9.73e-8`/`6.59e-8`/`8.81e-8`.

- Commit `5a9f4ab` is pushed and deployed. Local tests passed 29/29; the strict local 24h solve reached `OPTIMAL` in 32.00 s with peak RSS 0.694 GiB and every QC hard check passed.
- The corrected server 168h gate under `/data/zz2/National_model/outputs/2030_168h_sparse_gate_strict` contains 1,071,032 variables, 1,392,960 constraints and 10,100,058 nonzeros. It reached strict `OPTIMAL` in 666.45 s with peak RSS 3.910 GiB, maximum constraint violation `4.17e-8`, zero AC bidirectional edge-hours, zero DC reverse flow and `solution_qc=PASS`.
- The equivalent annual-network rewrite reduced 168h nonzeros by 380,581 (`3.63%`) without changing decision-variable count. Directly eliminating the VRE/ROR availability auxiliaries was tested and rejected because it duplicated CF coefficients in availability and reserve rows.
- The full-year runtime memory gate is now 96 GiB. The scale estimator covers all current variable blocks exactly (44,091,176 projected variables), estimates about 520.9 million nonzeros and 36.71 GiB static model memory, and explicitly does not treat this as a barrier-factorization guarantee.
- Corrected 744h CPU barrier gate under `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` has passed for deployed HEAD `5a9f4ab`. This preserves the sparse transmission/load-center formulation gate, but it does not include the uncommitted V0719 capacity-bound/DC active-index corrections.
- Solvability audit commit `ab9dfe8` records the revised 8760h projection: 44,091,176 variables, 68,188,384 constraints and about 515-524 million nonzeros. The existing 853.5 million preflight nonzero count is a conservative structural upper estimate, while its 46.62 GiB memory number is not a barrier peak-memory estimate.
- Current 24h and 168h build-only numerical audits were written under `outputs/audit_24h_20260719_system_solvability` and `outputs/audit_168h_20260719_system_solvability`. They contain 350,024/261,280/1,867,008 and 1,071,032/1,392,991/10,480,639 variables/constraints/nonzeros respectively.
- Rejected 744h solver evidence identifies the scaling bottleneck: presolved 3,274,450 rows and 3,353,208 columns; `Factor NZ=8.289e8` (about 10 GB); barrier 10,969.01 s and crossover 9,123.64 s. Linear factor-memory extrapolation alone is about 118 GB at 8760h, so a direct solve on the 125 GiB host is high risk even if build-only succeeds.
- A current-model 24h `Crossover=0` re-audit returned `SUBOPTIMAL`, maximum constraint violation 0.01355 and failed reservoir/directionality QC. A candidate `FeasibilityTol=OptimalityTol=1e-6`, `BarConvTol=1e-7`, `Crossover=1` run reached `OPTIMAL/QC PASS` in 37.38 s versus the approximately 40.02 s local strict baseline; this candidate is not approved for production until a corrected 168h/744h comparison passes.
- Live server HEAD remained `f22b9cf`; available RAM was about 30 GiB and all 21 GiB swap was occupied. No large server process was launched.

- Local implementation commit `2a0ee99` plus planning-state export test commit `ecfc7ed`; AST 38 files PASS; unit tests 24/24 PASS; data-package smoke 124/124 PASS.
- Final local 24h gate: 349,962 variables, 260,973 constraints, 1,827,245 nonzeros; Gurobi `OPTIMAL` in 58.79 s; peak RSS 0.698 GiB; `solution_qc=PASS`; maximum power-balance residual `3.90e-11 GW`.
- Local full-year preflight: PASS, zero hard failures; 44,090,772 variables, 67,603,314 constraints, 853,505,952 estimated nonzeros and 46.62 GiB estimated model memory. The workstation does not meet the 64 GiB full-year construction gate.
- Nonempty 2040 state-transfer diagnostic: `OPTIMAL/QC PASS`; inherited 2.5 GW battery and 1.0 GW PHS cohorts entered the intended province-technology lower bounds exactly.
- PHS source/QC: GHT 2026 province-level 8h storage; national operating floor 65.94 GW; 2030 project upper 249.191 GW; 2040+ upper 514.755 GW.
- Outputs: compact capacity/generation/storage/monthly/hourly summaries, SVG quicklooks and SHA256 result manifest are implemented and validated. Detailed audit: `MODEL_SYSTEM_AUDIT_20260718.md`.
- Minimal server bundle prepared from HEAD `dafeb24` with `--skip-cf` and locally rehashed: `national_model_code.tar.gz` 283,416 bytes SHA256 `1311f3ccfd53b26248e37c13370016a6b5e6165f717d1bde0e79c21d3cd73a4d`; `model_ready_data.tar.gz` 49,131,551 bytes SHA256 `502a60e58da959bfa6e5c3ba2ea83a8d39c3aade212231e5c6ecc42db6a9eb17`; `hydro_timeseries.tar.gz` 24,777,505 bytes SHA256 `573d1285eb4787a3058bff8c25b382a5df6630441de2c5e5b8d58095fbfd70f5`. The data archive contains the PHS bounds and no untracked `supplementary_materials/` files.
- On 2026-07-19 those two data archives were uploaded, verified with the same SHA256 values and extracted additively to the current server roots. Readiness passed with 28/28 required tables, 2,030 hydro stations, 124 cascade edges, full-license confirmation and both raw-GRFR hashes valid; server `unittest` passed 24/24 in 19.62 s.
- Server 24h output `/data/zz2/National_model/outputs/2030_diagnostic_24h_20260719_sequential_sparse_cpu`: 349,962 variables, 260,973 constraints and 1,827,246 nonzeros; Gurobi `OPTIMAL` in 60.53 s; maximum constraint violation `1.32e-08`; peak process-tree RSS 0.851 GiB; `solution_qc=PASS`.
- Replacement 744h preflight: 3,954,660 estimated variables, 5,912,178 constraints, 73,853,760 nonzeros and 4.08 GiB estimated memory. PID `3778049` was alive after 55 s with empty `stderr` under `/data/zz2/National_model/outputs/2030_one_month_20260719_sequential_sparse_cpu`.
- At launch, another user's four training jobs occupied about 67 GiB RAM; server available RAM was about 49 GiB and swap was full. This is adequate for the 744h estimate but below the configured 64 GiB full-year gate, so 8760h was not started.

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
- Core hydropower cascade coupling, the scaled 168h solve and the corrected 744h sparse transmission gate have passed server regression, optimization and QC gates. PID `3778049` reached mathematical optimality but is preserved as a rejected transmission-formulation baseline. Current implementation covers conventional reservoir cascade operation, not open-loop or closed-loop PHS water-pair coupling.
- Core cascade environmental flow now uses a 2019 single-year monthly P30 proxy. This follows the requested P30 direction but is still not the formal 1980-2019 climatological P30; manual review of the 4 low-correlation / 18 max-bound lag edges also remains unresolved input work.
- Capacity credits, inertia threshold and spur/trunk proxy costs still require parameter-source review, but no sensitivity-analysis workflow is requested for the current milestone.
- The intraprovincial load-center network uses a 50% design-utilization assumption.
- Two western AC500 proxy edges exceed the 1000 km range of the cited source cost.
- Intraprovincial load-center transmission losses remain zero.
- Demand-flexibility calibration remains open: building thermal inertia/comfort data and province-hour EV connection availability, driving energy, accessible battery capacity and departure SOC are not yet available. The current daily envelopes must be sensitivity-tested before paper interpretation.
- Direct server access to PyPI fails TLS certificate-chain validation. The user chose to defer this issue. Do not disable TLS verification; use verified offline wheels when a new package is required.
- Temporary uploaded installers and wheel directories remain on the server; do not delete them without explicit user confirmation.

### Exact next action

The fixed-server Base 168h and `flexible_load_v1` 24h/168h four-year gates are accepted. Do not run 744h or 8760h on the fixed server, and do not launch a paid cloud 8760h case without explicit cost authorization. The next model-development milestone is to formalize and test the sensitivity-case registry/runner around the existing checksummed scenario override contract, while keeping Base flexibility disabled and preserving strict sequential state identity. Building thermal/comfort envelopes and province-hour EV availability, driving-energy, accessible-battery and departure-SOC inputs still require calibration before any flexibility case can be interpreted scientifically. `flexible_load_v2g_v1` remains an independent optional scenario; its current local 24h gate is engineering evidence only.

```bash
cd /data/zz2/National_model/repo
export CISPO_CF_ROOT=/data/zz2/National_model/data/hourly_cf
export CISPO_HYDRO_ROOT=/data/zz2/National_model/data/hydro_timeseries_20260719_sequential_sparse
export CISPO_DATA_ROOT=/data/zz2/National_model/data/model_ready_20260722_v0721_fuel_state
export CISPO_RAW_GRFR_ROOT=/data/zz2/National_model/data/grfr_raw_2019
export GRB_LICENSE_FILE=/home/zz2/gurobi.lic
PYTHON=/home/zz2/.local/envs/cispo-2030/bin/python

OUT=/data/zz2/National_model/outputs/planning_sequence_168h_v0722_flexible_load_v1
$PYTHON scripts/run_cispo_planning_sequence.py \
  --scenario-config config/scenarios/flexible_load_v1.json \
  --diagnostic-hours 168 \
  --output-root "$OUT" \
  --resume
```

The command above must finish with four `RESUMED_ACCEPTED` records and must never rerun into the accepted year directories. Preserve all current output roots. Any later cloud staging must use exact code/data/scenario hashes, explicit Slurm thread limits and new 24h/168h gates before a separately authorized 8760h job. The 96 GiB pre-build gate remains necessary but is not proof that barrier factorization will fit.

## Version history

### v0.9.2 - 2026-07-22 - fixed-server 168h flexibility chain accepted

- Git/server identity: before this documentation update, local and pushed HEAD was `d00d1fb`; fixed-server checkout was clean at model commit `6ed943a`. No server checkout change occurred during the run or audit, and PID `1708266` is no longer active.
- Output: `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_flexible_load_v1`; original sequence `PASS`, four years `ACCEPTED`, wall time 1:06:54, peak RSS 4,040,256 KiB, swap zero and wrapper exit status 0.
- Solve/QC evidence: 2030/2040/2050/2060 are all `OPTIMAL + solution_qc=PASS`; runtimes 705.49/672.16/994.41/1181.26 s; all hard checks pass. Maximum heating/cooling/EV V1G daily-energy residual over all years is `8.17e-13 GWh`, with zero simultaneous up/down province-hours.
- Integrity/state evidence: each year has a closed 59-file result manifest; scenario IDs agree across solve/scope/scenario manifests; all input manifests record SHA256 `7b8f1c920bad35e2e41111f7913cfb456b6e369b85db5b03ae86d43801840532`; `capacity_cohorts_v2` state inputs follow 2030 -> 2040 -> 2050 -> 2060 and remain `TEST_ONLY_TRUNCATED_HORIZON`.
- Resume evidence: a fresh `--resume` audit at 2026-07-22 16:05 CST returned sequence `PASS` with four `RESUMED_ACCEPTED` records and no re-solve.
- Changed files: `CODEX_HANDOFF.md`, `MODEL_SERVER_STATUS.md`, `SERVER_RUNBOOK.md`; user-owned `supplementary_materials/**` changes were not modified or staged.
- Unresolved/next action: formalize the sensitivity-case registry/runner and calibrate building/EV flexibility envelopes before scientific interpretation. Keep Base disabled, keep V2G separate, and do not start fixed-server 744h/8760h or paid cloud 8760h without the required gates and explicit authorization.

### v0.9.1 - 2026-07-22 - fixed-server flexibility deployment and gates

- Deployment: fixed-server checkout fast-forwarded cleanly from `b6ca42d` to `6ed943a`; no model process was active during deployment, and existing data/results were not modified. The previous handoff shorthand is corrected: `b6ca42d` was the actual checkout for the Base 168h gate, while `0c1eaf2` was its model implementation baseline.
- Base acceptance: the four-year 168h Base chain completed in 1:08:40 with peak RSS 4,116,892 KiB and zero swap. Every year is `OPTIMAL + solution_qc=PASS + accepted state`; all four result manifests and the immediate resume audit pass.
- Flexibility acceptance: server regression tests pass 42/42. The four-year 24h `flexible_load_v1` chain completed in 6:32 with peak RSS 946,804 KiB and zero swap; all years and the immediate resume audit pass, scenario hashes are identical, daily load-shift conservation closes below `6.44e-13 GWh`, and simultaneous up/down counts are zero.
- Active task: four-year 168h `flexible_load_v1` chain is running under PID `1708266` in `/data/zz2/National_model/outputs/planning_sequence_168h_v0722_flexible_load_v1`.
- Exact next action: monitor the active 168h flexibility chain, validate its four solve/QC/result manifests and resume identity, then calibrate the illustrative flexibility envelopes before any cloud 8760h flexibility case. Do not launch fixed-server 744h/8760h.

### v0.9.0 - 2026-07-22 - modular load flexibility and scenario contract

- Git implementation: commit `6ed943a` (`feat: add modular demand flexibility scenarios`) is pushed to `origin/codex/cispo-2030-full-lp` but not yet deployed, so the fixed-server 168h Base sequence remains an uncontaminated `0c1eaf2` gate.
- Scope: retained the four existing load components in `ModelData`; hard-failed component nonclosure; added recursive, checksummed v1 scenario overrides; implemented daily-conserving heating/cooling and EV V1G shifting plus optional daily-cyclic V2G; routed effective load into hourly balance/reserve/inertia and annual load-center closure while retaining Base peak for capacity margin; added throughput/degradation costs, outputs, QC, scenario-safe resume and sequence aggregation.
- Changed files: `cispo_model/{config,data,flexible_load,io_contract,load_center,monolithic,preflight,result_summary,solution_export}.py`, `config/{optimization_2030,model_input_files}.json`, `config/scenarios/*`, run entrypoints, tests, the model/I/O specifications and new parameter/scenario documentation.
- Verification: 42/42 tests PASS; parameter audit 11,681 rows / 22 PASS / 0 WARN / 0 HARD_FAIL; Base 1h, V1 24h and V2G 24h all `OPTIMAL + solution_qc=PASS`; all three manifests validate. V1/V2G detailed closure and scale evidence is in the current snapshot.
- Unresolved: the current flexibility values are illustrative and need physical calibration; complementarity point/province/national and integrated-realistic entries are explicitly catalogued as planned-not-runnable; no 168h flexibility chain or cloud deployment has been performed.
- Exact next action: finish and audit the active server Base 168h chain; then push/deploy `6ed943a`, run fixed-server 24h/168h flexibility gates, and only after those pass stage the same commit/data hashes on the cloud. Do not launch a paid flexibility 8760h case before calibration and gates.

### v0.8.1 - 2026-07-22 - fixed-server four-year 24h chain passed

- Git/model/data baseline: implementation `0c1eaf2`, documentation/encoding HEAD `b6ca42d`, V0721 additive data root.
- Output: `/data/zz2/National_model/outputs/planning_sequence_24h_v0721_fuel_state`; initial sequence `PASS`, immediate `--resume` sequence `PASS`, four `RESUMED_ACCEPTED` records.
- Per-year result: 2030/2040/2050/2060 all `OPTIMAL + solution_qc=PASS`; solver runtimes 49.424/46.489/45.976/45.735 s; objective values 2,024,956.703 / 2,073,142.226 / 2,232,353.866 / 2,470,806.369 million CNY. These are truncated-horizon engineering values and have no scientific cost interpretation.
- Resource evidence: sequence wall time 6:03.31, maximum RSS 921,792 KiB, exit status 0 and no swap by the sequence process tree.
- Next gate: launched the 168h four-year diagnostic chain as PID `1348292` under `/data/zz2/National_model/outputs/planning_sequence_168h_v0721_fuel_state`. Audit all four years and resume identity after completion; do not start cloud 8760h meanwhile.

### v0.8.0 - 2026-07-22 - fuel accounting and safe sequential diagnostic chain

- Git implementation: `0c1eaf2` (`fix: harden sequential planning and fuel accounting`), pushed to `origin/codex/cispo-2030-full-lp` and fast-forwarded on the fixed server.
- Scope: connected existing province-level biomass prices to `bio/bioccs` fuel costs and the objective; added strict fuel-table coverage/range checks; upgraded state to `capacity_cohorts_v2`; validated source QC/solve/summary/result-manifest hashes and source year/use; isolated test-only diagnostic states from 8760h production; prevented nonempty-directory overwrite, nonzero-return acceptance and stale/mixed resume chains; bounded thermal retrofits by future surviving source capacity; cached Gurobi solution arrays during cohort export; added a parameter audit and deployment/paper case roadmaps.
- Changed files: `cispo_model/{config,data,io_contract,master,monolithic,planning_state}.py`, `config/optimization_2030.json`, `scripts/{build_cispo_data_package,rebuild_fuel_price_tables,audit_model_parameters,run_cispo_2030_full_year,run_cispo_planning_sequence}.py`, three regression tests, `FINAL_DEPLOYMENT_WORKFLOW_20260721.md` and `PAPER_CASE_ROADMAP_20260721.md`.
- Data: new additive fixed-server root `/data/zz2/National_model/data/model_ready_20260722_v0721_fuel_state`; rebuilt fuel-table SHA256 values are recorded in the current snapshot. The previous V0719 root was not overwritten.
- Local verification: 37/37 tests PASS; parameter audit 11,658 rows / 22 PASS / 0 WARN / 0 HARD_FAIL; real four-year 1h diagnostic sequence PASS; all years `OPTIMAL + solution_qc=PASS`; immediate `--resume` revalidation PASS. Caching `vre_new.X` reduced a 1h result/state export from an interrupted >5 min path to about 40 s total wall time.
- Server verification: HEAD `0c1eaf2`; parameter audit matches local counts; 37/37 tests PASS; V0721 24h four-year diagnostic sequence launched as PID `1314704`.
- Unresolved: BECCS gross/captured/stored/lifecycle/net carbon separation; 40/60-year nuclear lifetime, 5/15% capacity margin and 3.0/3.5 s inertia scenarios; CapEx and fuel-price low/base/high trajectories; decision-dependent versus fixed cost decomposition before complementarity epsilon constraints; formal multi-weather-year hydrology/robustness.
- Exact next action: audit the server 24h chain; if four years and resume identity pass, launch a new 168h four-year chain. Only after both pass should the cloud receive the new code/data package and run a single 2030 8760h production case.

### v0.7.4 - 2026-07-21 - second proxy/WLS smoke passed; thread limit flagged

- Git state: current model commit remains `b40900a`; no model code, input data or production output was changed.
- Scope: submitted only Slurm job `3975741` to `amd_a8_384`, 1 node, 1 CPU, 2 GB and 5 minutes; no CISPO command and no exclusive-node request.
- Proxy/license evidence: node `m4cl2501.para.bscc` used the engineer-provided proxy `172.16.110.3:8888`; the connectivity check returned HTTP 302, WLS authentication succeeded, and the two-variable LP returned `OPTIMAL` with `GUROBI_SMOKE_PASS`. `sacct` reports `COMPLETED`, exit code `0`.
- Resource caveat: despite the one-CPU request, the smoke log reported Gurobi could use up to 32 threads. Production scripts must set Gurobi `Threads` no higher than `--cpus-per-task` and verify the effective thread count before paid runs.
- Unresolved/next action: stage only the validated input package, verify SHA256 and output permissions, run cloud 24h/168h gates with explicit resources, then perform the full-year preflight/build-only gate. Do not submit 8760 optimization yet.

### v0.7.3 - 2026-07-21 - compute-node proxy/WLS smoke passed

- Git state: current model commit remains `b40900a`; no model code, input data or production output was changed.
- Scope: submitted only Slurm job `3975724` to partition `amd_m8_768-a`, 1 node, 2 CPUs, 8 GiB, 5 minutes; no CISPO command and no exclusive-node request.
- Compute evidence: node `m4cl0208.para.bscc`, Python 3.10.20, `gurobipy`/Gurobi 13.0.2. Partition inventory reports 192 CPUs and 768,000 MB per node; this resource class is adequate for the current 8760 build/factor-memory estimate, subject to an explicit per-job memory request.
- Proxy evidence: correctly encoded lower- and upper-case proxy variables made `token.gurobi.com` return HTTP 405 through remote IP `172.16.110.3`; WLS authentication then solved the tiny LP with `GUROBI_STATUS=2` and objective `1.0`. A PyPI request transferred data but did not finish within 30 seconds, so proxy throughput remains unbenchmarked for multi-GB data transfer.
- Configuration defect: the account `.bashrc` lines contain non-breaking spaces after `export`, producing `No such file or directory` on login and job startup. No configuration was modified automatically; correct proxy exports are now required inside every Slurm script.
- Unresolved/next action: transfer the tracked code and versioned model-ready/CF/hydrology data to a new cloud directory, verify SHA256 and shared-file permissions, run cloud 24h and 168h CISPO gates, then perform the full-year preflight/build-only gate. Do not submit 8760 optimization yet.

### v0.7.2 - 2026-07-21 - WLS recognized; compute-node DNS/egress gate failed

- Git state: current HEAD remains `b40900a`; no model or input-data files were changed by this milestone.
- Scope: after the engineer's WLS reinstallation, submitted only job `3975474` to `amd_a8_384` with 1 node, 1 CPU, 2 GB memory and a 5-minute limit; no `--exclusive` request and no CISPO production command.
- Compute/license evidence: node `m4cl1306.para.bscc` loaded `gurobipy310`/Gurobi 13.0.2 and recognized WLS parameters from the new private license path. `Env.start()` then failed with `Could not resolve host: token.gurobi.com`; `sacct` reports `FAILED`, exit code `1`.
- Unresolved/next action: the WLS credentials are being parsed, but the compute node cannot resolve/reach the WLS endpoint. Ask the cluster engineer to fix compute-node DNS/egress or provide the required proxy/allowlist, and protect the WLS file with mode `600`. Do not resubmit paid jobs or launch CISPO until one smoke test returns `GUROBI_SMOKE_PASS`/`OPTIMAL`.

### v0.7.1 - 2026-07-21 - Compute-node Gurobi call reached license gate

- Git state: current HEAD remains `b40900a`; no model or input-data files were changed by this milestone.
- Scope: submitted only job `3974169` to `amd_a8_384` with 1 node, 1 CPU, 2 GB memory and a 5-minute limit; no `--exclusive` request and no CISPO production command.
- Compute evidence: node `m4cm2307.para.bscc` loaded `/publicfs01/fs1-a8/home/a8s001819/.conda/envs/gurobipy310`, imported `gurobipy` 13.0.2 and saw `GRB_LICENSE_FILE`.
- License evidence: the two-variable LP failed at `Env.start()` with `HostID mismatch`; `sacct` reports `FAILED`, exit code `1`. The Python/Gurobi installation path is therefore reachable, but the current license is not valid for the allocated compute node.
- Unresolved/next action: do not launch CISPO or repeatedly resubmit paid smoke jobs. Obtain a compute-node-compatible academic named-user reactivation or Academic WLS/site license, then rerun one equivalent smoke test requiring `GUROBI_SMOKE_PASS`/`OPTIMAL` before any data staging or 8760h preflight.

### v0.7.0 - 2026-07-20 - open-source I/O contract, diagnostics and verified server gate

- Git implementation: `b40900a` (`feat: formalize model I/O and diagnostics`), pushed to `origin/codex/cispo-2030-full-lp` and fast-forwarded on the clean fixed-server checkout.
- Scope: added an open-source project `README.md`; formal input/output contract and data dictionary; immutable configuration, environment and input provenance; scope-aware summaries; complete dispatch, reserve, adequacy, resource, marginal-price and shadow-price exports; pickle-free NPZ identifiers; stronger model/state acceptance checks; and sequence-wide aggregation. Constraint handles and diagnostics were added without changing the LP feasible set.
- Main changed files: `README.md`, `MODEL_IO_CONTRACT.md`, `MODEL_744_SERVER_RUN_AUDIT_20260720.md`, `cispo_model/io_contract.py`, `solution_export.py`, `result_summary.py`, `planning_state.py`, `master.py`, `monolithic.py`, run/sequence scripts, input contract and tests.
- Local evidence: 34/34 unit tests PASS; 139/139 data-package checks PASS; local 24h output `outputs/2030_24h_v0720_io_contract_rerun3` is `OPTIMAL/QC PASS`, all 27 hard checks pass, manifest validation is clean, dual export is available and complementarity diagnostics are zero.
- Server evidence: 34/34 unit tests and 139/139 smoke checks PASS. `/data/zz2/National_model/outputs/2030_24h_v0720_io_contract_server` is `OPTIMAL/QC PASS` with 43.65 s solver time and 0.838 GiB peak RSS; manifest `(True, [])`; output catalog 50 rows; data dictionary 493 rows; hourly prices 744 rows; annual shadow prices 3,366 rows; all NPZ files are safe under `allow_pickle=False`.
- 744h audit: the old `5a9f4ab` engineering gate remains solver-valid, but its wrapper-owned `run.stdout` and `run.time` invalidate two old manifest entries. V0720 excludes runtime-managed wrapper files from the scientific manifest and validates the manifest before accepting sequence output.
- Architecture decision: retain sequential 2030/2040/2050/2060 full-year optimization as the production default. It requires four solves and is myopic, but keeps only one 8760h LP resident at a time; a joint four-year perfect-foresight model would multiply time-dependent matrix blocks and peak memory and is reserved for reduced-scale research experiments.
- Unresolved/next action: do not repeat 744h on the fixed server. Complete cloud compute-node/license/data staging, run 24h/168h gates there, then use the 8760h output contract for a single production case. Existing VRE retirement, formal climatological hydrology, cascade lag warnings, PHS hydraulic pairing and long-term sensitivity assumptions remain explicit research items.

### v0.6.4 - 2026-07-20 - Gurobi Linux package staged; license transfer held

- Git state: local branch `codex/cispo-2030-full-lp`, HEAD `3c9edfa76c3077de421b56b2b287585cb7b6188d`; no model code, solver environment or remote job state was changed.
- Scope: downloaded the official Gurobi 13.0.2 Linux x86-64 package, verified the official MD5 and uploaded only the installation archive to the user-private cloud staging directory. No license file was transferred.
- Artifact evidence: `/publicfs01/fs1-a8/home/a8s001819/staging/gurobi1302/gurobi13.0.2_linux64.tar.gz`, 64,798,273 bytes, MD5 `f12dcad337ae1d8f9b8c2b3f51b92bb5`, SHA256 `cffd4ee3c1990294e80446626bd1772045e420d7c34c379839b6acca16f0a23b`; local and remote hashes match.
- License decision: the user-provided email identifies an academic named-user license. Because Gurobi named-user licenses are machine-scoped and Slurm may dispatch jobs across multiple compute nodes, copying a license generated on another server was not assumed valid and was deliberately not performed. The cloud document records `grbgetkey`/WLS decision rules without storing key codes or license contents.
- Unresolved/next action: after explicit approval, use a small scheduler allocation to determine the compute-node target and Gurobi installation path, then choose a compliant named-user reactivation or Academic WLS/site license. Do not install or start 8760h before this check.

### v0.6.3 - 2026-07-20 - BSCC-A8 manual reconciliation and cloud usage document

- Git state: local branch `codex/cispo-2030-full-lp`, HEAD `3c9edfa76c3077de421b56b2b287585cb7b6188d`; no model code, data, solver environment or remote job state was changed.
- Scope: interpreted the user-provided official BSCC-A8 manual screenshot and created `supplementary_materials/云服务器使用规范_BSCC-A8.md` with the documented Modules/Slurm/compiler workflow, current SSH aliases, login-node boundary, storage layout, cost gate and CISPO-specific 8760h stop rules.
- Reconciliation evidence: the manual is dated 2024-08-26 and refers to the older `amd_a8_768` queue; live Slurm audit on `ln301.para.bscc` reports `amd_m8_768-a` as the default partition and `amd_a8_384` as the second active partition. The document marks live values as authoritative instead of copying stale queue names.
- Safety evidence: no remote file was written, no module or package was installed, no Slurm allocation was requested and no job was submitted. The verified module initializer `/public1/soft/modules/module.sh` is documented, while current compute-node Gurobi availability remains explicitly unverified.
- Unresolved/next action: only after user approval, run a small scheduler allocation to inventory compute-node Python/Gurobi/license and perform a smoke test; do not launch 8760h production directly from the login node.

### v0.6.2 - 2026-07-20 - ParaCloud Slurm login-node audit

- Git state: local branch `codex/cispo-2030-full-lp`, HEAD `3c9edfa76c3077de421b56b2b287585cb7b6188d`; no model code, data, solver environment or remote job state was changed.
- Scope: performed a read-only audit after public-key login to identify the safe cloud execution path. No `sbatch`, `srun`, package installation, environment activation persisted, file transfer or model execution was performed.
- Verified cluster: Rocky Linux 8.10 login host `ln301.para.bscc`; Slurm 23.11.9, cluster `bscc-m8`, `select/cons_tres` with `CR_CORE_MEMORY`; account `bscc-a8`, QoS `normal`, association output showing a 10-job submission limit.
- Verified partitions: default `amd_m8_768-a` has 194 nodes, 192 CPUs/node and 768000 MB/node with 4000 MB/CPU default; `amd_a8_384` has 103 nodes, 128 CPUs/node and 384000+ MB/node with 3000 MB/CPU default. Both partitions are `UP` and allow all accounts/QoS at the partition level.
- Environment evidence: login host has 64 logical CPUs and about 376 GiB RAM; `/publicfs01` has about 3.1 PB free. System Python is legacy; shared Miniforge `/public1/soft/miniforge/24.11` exposes `base`, `py-moose` and `toga2`, but none of the checked environments imports `gurobipy` or `torch`. This does not prove compute-node software absence.
- Safety conclusion/next action: treat `ln301` as login-only. Before any paid 8760h work, create an explicit Slurm script, request a small approved allocation to inventory compute-node Python/Gurobi/license and run a smoke check, then require the full-year preflight, memory gate and cost confirmation. Do not install packages or run the long solve from the login node.

### v0.6.1 - 2026-07-20 - ParaCloud public-key authentication verified

- Git state: local branch `codex/cispo-2030-full-lp`, HEAD `3c9edfa76c3077de421b56b2b287585cb7b6188d`; no model code, data or solver environment was changed.
- Scope: corrected the ParaCloud SSH aliases to use the normal public-key-first OpenSSH authentication order, then verified both port 22 and port 2222 end to end with a read-only remote command.
- Verification evidence: `paracloud-bscc-a8` and `paracloud-bscc-a8-backup` authenticated with the existing local public key and returned `CODEX_CLOUD_SSH_OK`, remote host `ln301.para.bscc`, account `a8s001819` and home `/publicfs01/fs1-a8/home/a8s001819`; both commands exited with status 0.
- Security evidence: no password was entered, stored or logged; no private-key content was read or copied. The earlier password prompt was caused by the temporary alias preference and has been removed.
- Unresolved/next action: inventory scheduler, quotas, CPU/RAM/storage, Python/Gurobi, data paths and job accounting on the cloud login node. Do not launch a paid 8760h solve until the cost gate and full-year preflight requirements in the selection policy pass.

### v0.6.0 - 2026-07-20 - ParaCloud route selection and cost-gated SSH configuration

- Git state: local branch `codex/cispo-2030-full-lp`, HEAD `3c9edfa76c3077de421b56b2b287585cb7b6188d`; no model code, data or solver environment was changed.
- Scope: classified the two server targets and configured local SSH aliases for the separate ParaCloud BSCC-A8 endpoint. Existing `national-model-server` configuration was preserved unchanged.
- Changed files/state: repository handoff updated; user SSH config `C:\Users\ZZ\.ssh\config` gained `paracloud-bscc-a8` on port 22 and `paracloud-bscc-a8-backup` on port 2222; memory note `20260720-paracloud-server-routing.md` records non-secret routing and cost-gate metadata.
- Verification evidence: DNS resolved both IPv4 backends; TCP checks passed on ports 22, 2222 and 8443 via Ethernet source `124.16.2.171`. SSH banner/auth checks succeeded on ports 22 and 2222 (`ParaCloud`, `password,publickey`); 8443 and IPv6 port 22 reset before the banner. `ssh -G` confirmed both aliases resolve to the intended compound user and ports.
- Selection rule: use `national-model-server` for local work and the 744h engineering gate; use ParaCloud only for explicitly authorized, scheduler-backed 8760h production after full-year preflight, memory/resource/license validation and cost confirmation. No cloud authentication or paid job was started.
- Unresolved/next action: authenticate through `paracloud-bscc-a8`; inventory scheduler, quotas, CPU/RAM/storage, Python/Gurobi and data paths; only then prepare a checksum-verified production transfer and launch decision.

### v0.5.9 - 2026-07-20 - ParaCloud candidate SSH pre-authentication check

- Git state: local branch `codex/cispo-2030-full-lp`, HEAD `3c9edfa76c3077de421b56b2b287585cb7b6188d`; no model code, data, solver environment or server process was changed.
- Scope: performed a read-only connectivity check for the separate ParaCloud/BSCC-A8 candidate endpoint intended for possible future 8760h computation. The existing validated `national-model-server` target and its SSH configuration were not modified.
- Changed file: `CODEX_HANDOFF.md` only, to preserve this verified server milestone without credentials.
- Verification evidence: the hostname resolved to two IPv4 backends; `Test-NetConnection` passed on TCP port `8443` for both via the workstation Ethernet source address. OpenSSH parsed the compound login user correctly, but `ssh -vv`, `ssh-keyscan` and raw banner checks received no SSH banner and both backends reset or timed out before key exchange.
- Security evidence: no password, private-key content, activation key or license content was read, logged or written. Password validity was not tested because the connection never reached authentication.
- Unresolved/next action: verify in ParaCloud that the BSCC-A8 direct-connection mapping is active and that the workstation source IP is permitted, then rerun the SSH banner/authentication check. After successful login, inventory scheduler, CPU/RAM/storage, quotas, environment and Gurobi license before transferring data or launching any 744h/8760h job.

### v0.5.8 - 2026-07-19 - V0719 deployed, 24h gate passed, 8760 memory gate blocked

- Git/server state: local commits `451b1c0`, `c8db9be` and `bc83663` were pushed to `origin/codex/cispo-2030-full-lp`; server checkout `/data/zz2/National_model/repo` was fast-forwarded to `bc83663`.
- Scope: deployed V0719 code and data contract to a new additive data root, fixed server smoke-test path resolution for CF and hydrology files, and ran server validation. No old data root or old 744h output was overwritten.
- Data root: `/data/zz2/National_model/data/model_ready_20260719_v0719_capacity_bounds`; generated `thermal/nuclear_capacity_upper_by_year.csv`, `biomass/capacity_upper_by_province_year.csv` and `storage/battery_capacity_floor_by_province_year.csv`; added missing smoke/QC support files from canonical `model_ready`.
- Validation evidence: server smoke `139/139 PASS`, server unit tests `32/32 PASS`, readiness `PASS` with full Gurobi license and raw-GRFR SHA256 verification.
- Solve evidence: server 24h V0719 output `/data/zz2/National_model/outputs/2030_24h_v0719_capacity_bounds_server` reached `OPTIMAL/QC PASS`; model size 341,312 variables / 261,280 constraints / 1,768,957 nonzeros; Gurobi runtime 48.96 s; peak RSS 0.841 GiB; zero nuclear, biomass+BECCS, storage and transmission-direction hard-check violations.
- 8760 evidence: direct full-year solve was not launched. Full-year preflight `/data/zz2/National_model/outputs/2030_8760_v0719_preflight_memory_check` reported `memory_gate_pass=false`, available memory `73.15 GiB` versus required `96.0 GiB`; estimated full-year scale 40,911,296 variables / 67,603,283 constraints / 520,920,489 nonzeros.
- Unresolved/next action: wait for memory pressure to clear or use a high-memory node. On this host, run V0719 168h and 744h gates before any full-year production solve. If overriding for an exploratory full-year build, require at least 96 GiB available RAM and start with build-only/preflight evidence, not optimize.

### v0.5.7 - 2026-07-19 - corrected 744h sparse gate completed

- Git/server state: server checkout HEAD `5a9f4ab`; local V0719 capacity-bound/DC active-index corrections remain an uncommitted working tree on local HEAD `f84143a` and were not used by this server run.
- Scope: verified completion of `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict`; no model code, data root or server process was changed.
- Verification evidence: `solve_report.json` reports `OPTIMAL`, `solution_count=1`, objective `2,196,413.3453 million CNY`, runtime `16,245.79 s`, barrier iterations `214`, simplex/crossover iterations `1,468,988`, peak process-tree RSS `21.979 GiB`, and model size 3,955,064 variables / 5,919,746 constraints / 43,707,940 nonzeros. `/usr/bin/time` reports wall time 4:37:02, maximum RSS 23,469,440 kB and exit status 0.
- QC evidence: `solution_qc.json` reports `PASS`, maximum power-balance residual `3.64e-10 GW`, zero line-capacity violation, zero bidirectional interprovincial edge-hours, zero DC reverse flow across 363 DC corridors, zero biomass/carbon/CO2 sink violations and all hard checks true.
- Unresolved/next action: preserve this as the completed pre-V0719 sparse gate. Do not start 8760 production on this older scientific boundary. Commit/push V0719, build a new versioned data root with the three new capacity-bound tables, then rerun readiness, tests, smoke, 24h, 168h and corrected 744h before any 8760 build-only or solve.

### v0.5.6 - 2026-07-19 - V0719 capacity bounds and DC active-index correction

- Git state: branch `codex/cispo-2030-full-lp`, local HEAD `f84143a`, implementation base `5a9f4ab`; V0719 changes are intentionally left uncommitted pending user review. Server HEAD remains `5a9f4ab`.
- Scope: implemented the four issues identified in `supplementary_materials/MODEL_V0719_REVIEW_REPORT.md`: nuclear capacity upper, shared biomass+BECCS capacity upper, 2030 battery exogenous floor and removal of DC reverse fixed-zero variables.
- Main changed files: `config/capacity_bounds_v0719.json`, `scripts/build_v0719_capacity_bounds.py`, data/config loaders, `cispo_model/master.py`, `monolithic.py`, `load_center.py`, `solution_export.py`, `result_summary.py`, `preflight.py`, model-input contract/config, data-package builder/smoke tests, unit tests, model specification and V0719 report.
- Generated inputs: `thermal/nuclear_capacity_upper_by_year.csv` (124 rows), `biomass/capacity_upper_by_province_year.csv` (124 rows), `storage/battery_capacity_floor_by_province_year.csv` (124 rows). These are generated under the configured data root and remain outside Git with the rest of `data/`.
- Scientific boundaries: nuclear national upper `110/205/300/300 GW`; shared `bio+bioccs` upper uses `thermcal×0.35/(3600×6132)` with an inherited-floor safeguard that triggers only in Shanghai; 2030 battery floor totals 65.85 GW after Mengdong/Mengxi merge and is zero as an exogenous boundary from 2040 onward.
- Exact sparsification: reverse variables now exist only for 48 AC corridors; all 411 corridors retain forward variables. Dense 411-row reverse output is reconstructed with DC rows zero, preserving file/API compatibility. Full-year variable reduction is 3,179,880.
- Commands/evidence: `C:\Users\ZZ\.conda\envs\RL\python.exe scripts\build_v0719_capacity_bounds.py`; `... -m unittest discover -s tests -q` passed 32/32 in 17.62 s; `... scripts\smoke_test_data_package.py` passed 139/139; strict 24h solve at `outputs/2030_24h_v0719_capacity_bounds_dc_sparse_rerun` reached `OPTIMAL/QC PASS` with 341,312 variables, 261,280 constraints, 1,768,956 nonzeros, solver 39.79 s and peak RSS 0.702 GiB.
- Validation details: all new capacity-bound violations are zero; DC reverse flow and AC simultaneous bidirectionality are zero; maximum power-balance residual `7.43e-12 GW`. The first too-short timeout output `outputs/2030_24h_v0719_capacity_bounds_dc_sparse` is retained as an interrupted trace.
- Server evidence: at 2026-07-19 16:42 Asia/Shanghai, `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict` remained active under PID `3344086`, elapsed 01:35:08 at barrier iteration 107, with no solve/QC reports. It uses the old versioned data root and was not modified.
- Unresolved/next action: commit/push only after review; after the old 744h is preserved, create a new versioned data root, generate the three bound tables and pass server readiness, 32 tests, 139 smoke checks, 24h, 168h and corrected 744h. Do not run 8760 yet. Long-term nuclear, updated biomass, separated battery GW/GWh, formal multi-year hydrology and CSP remain scenario/data work, not hidden hard constraints.

### v0.5.5 - 2026-07-19 - annual-network sparse cleanup and corrected 168h gate

- Git implementation: `5a9f4ab` (`Reduce annual network matrix duplication`).
- Scope/changed files: `cispo_model/load_center.py` reuses province sent/received accounts in net-import closure, removes the implied province reservoir-generation closure and adds unique route checks; `cispo_model/preflight.py` corrects variable-block accounting and recalibrates nonzeros; `config/optimization_2030.json` raises the full-year RAM gate to 96 GiB and removes unused LP-inapplicable settings; `tests/test_model_foundation.py` adds scale/sparsity/gate regressions.
- Verification: local 29/29 tests; local strict 24h `OPTIMAL/QC PASS`; server readiness/raw-GRFR/full-license PASS; server 29/29 tests; server strict 168h `OPTIMAL/QC PASS` in 666.45 s with 3.910 GiB peak RSS.
- Scale evidence: 168h nonzeros decreased from 10,480,639 to 10,100,058 while variables remained 1,071,032. Direct availability-variable removal was rejected after a 24h build increased nonzeros from about 1.87m to 2.23m.
- Server command/output: `scripts/run_cispo_2030_full_year.py --diagnostic-hours 168 --output-dir /data/zz2/National_model/outputs/2030_168h_sparse_gate_strict`.
- Unresolved/next action: PID `3344086`/child `3344087` is running the strict corrected 744h gate under `/data/zz2/National_model/outputs/2030_744h_sparse_gate_strict`. Only after `OPTIMAL/QC PASS` and a fresh >=96 GiB memory check may 8760h build-only start; build success still does not authorize solve.

### v0.5.4 - 2026-07-19 - full-year solvability and cross-year completeness audit

- Git audit commit: `ab9dfe8` (`docs: audit full-year solvability and state transfer`); implementation remains `1b6da28`, documentation baseline before this entry was `f22b9cf`.
- Scope: decomposed current 24h/168h model size by VRE, thermal RUC, storage, hydropower, transmission, balance/security, annual load-center and carbon blocks; recalibrated 8760 nonzeros/static build memory; audited 744h factorization/crossover; reviewed Gurobi parameters and every cross-year capacity cohort class.
- Changed files: `MODEL_SOLVABILITY_AUDIT_20260719.md`, followed by continuity updates in `CODEX_HANDOFF.md`, `MODEL_SERVER_STATUS.md` and `SERVER_RUNBOOK.md`.
- Commands/evidence: current 24h/168h `scripts/audit_model_numerics.py --skip-full-max-cf`; live `ssh national-model-server` HEAD/resource check; rejected 744h `solve_report.json` and `gurobi.log`; two current-model 24h parameter diagnostics.
- Findings: revised 8760 scale is about 44.09m variables, 68.19m constraints and 515-524m nonzeros; calibrated build peak is about 58 GiB, but linearly extrapolated barrier factor memory alone is about 118 GB. Direct 8760 solve on 125 GiB is high risk.
- Parameter result: `Crossover=0` failed current hard QC; a default feasibility/optimality tolerance plus `BarConvTol=1e-7` candidate saved about 7% at 24h and remains diagnostic-only.
- Cross-year result: all current capacity decision classes are transferred through checksummed active cohorts, including VRE, thermal/nuclear, hydro, battery/PHS, inter-/intra-provincial transmission, DAC, spur and trunk. Remaining physical limitations are myopic foresight, missing existing-VRE age retirement, plant-level thermal retrofit remaining life, additive nuclear pipeline interpretation and province-level fixed-duration PHS.
- Unresolved/next action: implement exact availability/load-center sparse reformulations, correct scale reporting, pass local gates, then rerun corrected 744h when shared memory pressure clears. Require at least 96 GiB available RAM for 8760 build-only; do not optimize until its true memory evidence is reviewed.

### v0.5.3 - 2026-07-19 - corrected server 24h transmission gate

- Git implementation: `1b6da28`; synchronized server documentation HEAD includes `c4cfddd` or later.
- Server tests: 26/26 PASS in 22.24 s under `/home/zz2/.local/envs/cispo-2030`.
- Output: `/data/zz2/National_model/outputs/2030_diagnostic_24h_20260719_cispo_flow_alignment_cpu`.
- Solver: 350,024 variables, 261,280 constraints and 1,867,007 nonzeros; Gurobi 13.0.2 `OPTIMAL` in 43.88 s; peak process-tree RSS 0.845 GiB.
- QC: power-balance residual `1.46e-11 GW`; reservoir-transition residual `7.63e-06 m3`; zero AC bidirectional edge-hours; zero DC reverse flow on 363 DC edges; all hard checks PASS.
- Output integrity: every scientific manifest file matched size and SHA256; runtime-owned stdout/stderr/PID files are explicitly excluded.
- Resource stop: only about 32 GiB RAM was available and all 21 GiB swap was occupied by shared workloads. No corrected 744h or 8760h process was started.
- Next action: wait for shared memory pressure to clear, require at least 64 GiB available RAM, then launch a new versioned corrected 744h CPU barrier gate.

### v0.5.2 - 2026-07-19 - CISPO transmission alignment after 744h result audit

- Git implementation: `1b6da28` (`fix: align interprovincial flows with CISPO`).
- Rejected baseline: `/data/zz2/National_model/outputs/2030_one_month_20260719_sequential_sparse_cpu` reached `OPTIMAL` in 20,118.58 s with 22.141 GiB peak RSS, but contained 3,358 material bidirectional edge-hours, 3,909.04 GWh summed opposing minimum flow and a 4.393 GW maximum opposing minimum flow.
- Root causes: the model configured `0.001 yuan/MWh` instead of CISPO's `0.001 yuan/kWh = 1 yuan/MWh`; DC reverse flow was not fixed to zero; the added annual load-center layer closed gross sent/received energy and rewarded artificial loops.
- Fix: AC keeps `f_forward + f_reverse <= capacity`; DC reverse UB is zero; flow cost is 1 yuan/MWh; the annual load-center layer closes province net exchange; AC bidirectionality and DC reverse flow are hard QC failures; shell-managed files are excluded from the scientific SHA256 manifest.
- Local verification: tests 26/26 PASS; corrected 24h model 350,024 variables, 261,280 constraints and 1,867,006 nonzeros; `OPTIMAL` in 40.02 s; peak RSS 0.700 GiB; power-balance residual `5.35e-12 GW`; zero AC bidirectionality; zero DC reverse flow across 363 DC edges; manifest mismatches zero.
- Detailed evidence: `TRANSMISSION_FLOW_AUDIT_20260719.md`.
- Next action: deploy `1b6da28`, run server tests and corrected 24h gate, then defer the corrected 744h until shared-server available RAM is safe.

### v0.5.1 - 2026-07-19 - server synchronization and replacement 744h launch

- Git baseline: branch `codex/cispo-2030-full-lp`, server checkout HEAD `827b37f`, containing implementation commit `2a0ee99`.
- Scope: restored live SSH through the configured bound-source alias; fast-forwarded the clean server checkout; uploaded and SHA256-verified versioned model/hydrology bundles; ran readiness, regression and 24h solve gates; launched the replacement 744h CPU barrier gate.
- Changed files: `CODEX_HANDOFF.md`, `MODEL_SERVER_STATUS.md`, `SERVER_RUNBOOK.md`; model source files were not changed in this milestone.
- Verification: readiness PASS with zero hard failures; raw GRFR 2/2 hashes PASS; tests 24/24 PASS; 24h `OPTIMAL/QC PASS` in 60.53 s with 0.851 GiB peak RSS.
- Server output: `/data/zz2/National_model/outputs/2030_one_month_20260719_sequential_sparse_cpu`, PID `3778049`; initial process check passed and `stderr` was empty.
- Unresolved: the 744h result is still pending; formal climatological P30 and 4 low-correlation/18 max-bound cascade-lag edges remain input limitations. Shared server load leaves only about 49 GiB available, below the 8760h gate.
- Next action: inspect the 744h reports after process exit; if and only if `OPTIMAL/QC PASS` and RAM is at least 64 GiB, run the 8760h build-only gate.

### v0.5.0 - 2026-07-18 - sequential planning, exact sparse reformulation and complete outputs

- Git implementation baseline: `2a0ee99` (`feat: add sequential planning and stabilize full-year LP`).
- Scope: implemented checksummed 2030/2040/2050/2060 capacity-cohort transfer; added GHT 2026 province-level PHS floor/project upper; removed redundant ramp, storage reserve, reservoir generation, hydro inertia and operating-cost-account variables/equalities using exact linear reformulations; completed compact outputs/SVG/manifest; reduced model input tables to an explicit 28-table contract.
- Main changed files: `cispo_model/config.py`, `data.py`, `master.py`, `monolithic.py`, `planning_state.py`, `preflight.py`, `result_summary.py`; `config/model_data_config.json`, `optimization_2030.json`, `model_input_files.json`; run/build/readiness/smoke scripts and sequence/tests.
- Local validation: AST 38 PASS; unit tests 24/24 PASS including real solution-to-cohort mapping; data-package smoke 124/124 PASS; 2030 and 2040 full-year preflight PASS; four-year sequence dry-run PASS; final 24h solve `OPTIMAL/QC PASS` in 58.79 s with 0.698 GiB peak RSS; nonempty 2040 state diagnostic `OPTIMAL/QC PASS`.
- Scale: full-year preflight estimates 44,090,772 variables, 67,603,314 constraints, 853,505,952 nonzeros and 46.62 GiB model memory. Local build is correctly blocked by the 64 GiB runtime gate.
- Server status: not deployed. SSH connected to TCP/22 but closed during key exchange on 2026-07-18, so server HEAD and old 744h status could not be verified.
- Transfer status: minimal code/data/hydrology archives and SHA256 manifest were prepared locally; Git push and server upload are blocked by the same SSH key-exchange closure.
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
