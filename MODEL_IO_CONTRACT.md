# CISPO model input/output contract

## 1. Design goal

One 8760-hour solve is expensive. A completed case must therefore preserve all optimized decisions and the principal derived quantities needed for paper figures, policy comparisons, constraint validation and cross-year state transfer. Outputs are additive: existing stable filenames remain available, while catalogs and new analysis tables make the case understandable without reading model source code.

## 2. Input contract

`config/model_input_files.json` is the machine-readable source of truth. Inputs fall into four groups:

1. Model-ready CSV/CSV.GZ tables under `CISPO_DATA_ROOT`.
2. Hourly VRE Zarr stores under `CISPO_CF_ROOT`, indexed by `vre/hourly_cf_index.csv`.
3. Hydrology NetCDF files under `CISPO_HYDRO_ROOT`, indexed by `hydro/timeseries_index.csv`.
4. A prior accepted `planning_state/` bundle for 2040, 2050 or 2060.

At case start, `input_manifest.csv` records every resolved table and hydrology file with size and SHA256. If `--scenario-config` is used, the override file is also checksummed. Zarr stores record an exact resolved path and metadata fingerprint; the large chunk payload is not copied into the case directory. `model_config_snapshot.json` embeds the resolved year-specific configuration rather than only referencing a mutable config path.

The hourly load input preserves `demand_gw`, `base_residual_gw`, `heating_gw`, `cooling_gw` and `ev_gw`. The loader hard-fails on missing/negative values or component closure above `1e-9 GW`; optional flexibility is applied only after this immutable baseline is loaded. The current future-load source is the local `Power_curve_V2` projection: heating/cooling use the non-leap 2024 BAIT/HDD/CDD shapes multiplied by `thermal_multiplier`, while EV load is `future_nev_stock × ev_kwh_per_vehicle_day × ev_hour_weight`. `ev_hour_weight` is an uncontrolled charging-profile weight and must not be relabelled as plug availability.

All model power variables use GW, hourly energy sums use GWh, storage energy uses GWh, carbon uses MtCO2, biomass uses PJ, reservoir flows use m3/s and physical active storage uses m3. The objective uses million CNY per year. Truncated horizons retain annual capacity and policy terms but contain only truncated operating terms.

## 3. Output groups

| Group | Stable outputs | Main use |
|---|---|---|
| Provenance | `run_scope.json`, `run_environment.json`, `model_config_snapshot.json`, `input_manifest.csv` | Reproduce the exact case and distinguish scientific vs test horizons |
| Capacity | `vre_capacity.csv`, `thermal_nuclear_capacity.csv`, `hydro_capacity.csv`, `storage_capacity.csv`, `transmission_capacity.csv`, `annual_capacity_by_province_technology.csv` | Capacity maps, province comparisons, build/floor/boundary decomposition |
| Chronological operation | `thermal_dispatch.npz`, `vre_dispatch.npz`, `storage_dispatch.npz`, `hydro_dispatch.npz`, `reservoir_dispatch.npz`, `transmission_flows.npz` | Dispatch, ramps, starts, reserve, SOC, hydrology and corridor-flow analysis |
| Demand flexibility | `scenario_manifest.json`, `flexible_load_dispatch.npz`, `annual_flexible_load_by_province.csv` | Baseline/optimized load components, shifts, V2G, peaks, losses and scenario assumptions |
| Readable hourly tables | `time_index.csv`, `hourly_national_balance.csv.gz`, `hourly_province_balance.csv.gz`, `hourly_province_security.csv.gz` | Plotting, balance checks, adequacy and flexibility metrics |
| Annual/monthly analysis | `annual_generation_by_province_technology.csv`, `annual_resource_accounting_by_province.csv`, `annual_adequacy_by_province.csv`, `annual_constraint_shadow_prices.csv`, `monthly_energy_by_technology.csv`, `cost_components.csv` | Paper tables, regional mechanisms, adequacy, shadow prices, carbon/resource and cost decomposition |
| Fixed result review | `result_dashboard_summary.json`, `result_analysis_metrics.csv`, `visualizations/core_result_dashboard.svg` | One stable post-run review step covering acceptance, capacity, generation, scope-aware costs, flexibility, carbon and security margins |
| Spatial network | `load_center_*.csv`, `province_annual_load_center_accounts.csv`, `co2_source_sink_flows.csv` | 337-city annual load-center allocation, intraprovincial transmission proxy and CCS routing; the 278-node Natural Earth package is retained only for replication/sensitivity |
| Acceptance | `solve_report.json`, `solution_qc.json`, `output_catalog.csv`, `output_data_dictionary.csv`, `result_manifest.json` | Numerical status, physical validity, schema discovery and integrity |
| Cross-year | `planning_state/state_metadata.json`, `capacity_cohorts.csv.gz`, `state_transition_summary.csv` | Exact cohort inheritance and lifetime retirement |

## 4. Array interpretation

NPZ files are saved with numeric arrays and fixed-width Unicode identifiers, so they load with `allow_pickle=False`. Dimension labels are included in `output_data_dictionary.csv`.

- `thermal_dispatch.npz`: `[province, technology, hour]` gross/net generation, online/start/shutdown capacity and ramp magnitude; reserve arrays are `[province, hour]`.
- `vre_dispatch.npz`: `[province, technology, hour]` availability and actual generation. Curtailment is `available_gw - generation_gw`.
- `storage_dispatch.npz`: `[province, technology, hour]` charge, discharge, SOC and up/down reserve.
- `hydro_dispatch.npz`: `[province, hour]` ROR availability/generation, reservoir generation and up reserve.
- `reservoir_dispatch.npz`: `[reservoir_station, hour]` generation, flow, spill, storage and inflow, linked through `reservoir_station_index.csv`.
- `transmission_flows.npz`: `[corridor, hour]` forward/reverse flow, linked to `transmission_capacity.csv`. DC reverse rows are explicitly reconstructed as zero for output compatibility.
- `flexible_load_dispatch.npz`: `[province, hour]` immutable baseline components, optimized components, up/down shifts, equivalent heating/cooling state, EV V1G backlog and V2G charge/discharge/SOC. It is written for Base too; Base arrays equal the inputs and all flexibility/state arrays are zero. In `state_envelope_v2`, thermal states and EV backlog start from zero and reset to zero within each Beijing-time day; in legacy V1 those three arrays are zero and the accepted daily energy-equality formulation is unchanged.

The optimization does not contain site-hour VRE dispatch variables. It dispatches VRE at province-technology-hour resolution while retaining site-level capacity and exact site CF coefficients. Therefore no artificial site-level curtailment allocation is exported. Site potential generation can be recomputed from the saved capacity decision and immutable CF input without rerunning optimization.

## 5. Scope-aware cost intensity

The fixed dashboard uses immutable baseline electricity demand as its
denominator so Base and flexibility cases remain directly comparable. Because
`1 million CNY / GWh = 1 CNY/kWh`, no additional factor is applied.

- For `SCIENTIFIC_PRODUCTION`, total system cost intensity is the sum of
  annualized planning cost and full-year operating cost divided by full-year
  baseline demand.
- For `TEST_ONLY_TRUNCATED_HORIZON`, the dashboard reports annualized planning
  cost intensity against full-year baseline demand and selected-horizon
  operating cost intensity against selected-horizon baseline demand as two
  separate quantities. They must not be added, labelled as LCOE, or interpreted
  as a scientific annual result.
- `annual_operation` is a composite roll-up and is excluded when the detailed
  `SELECTED_HORIZON_OPERATION_COST` rows are summed. Dashboard generation
  fails closed if detailed scope rows do not reconstruct the reported
  objective within numerical tolerance.

The dependency-free SVG is part of the checksummed scientific output. The
standalone `scripts/build_result_dashboard.py` can render PNG/PDF copies in an
external analysis directory on a workstation with Matplotlib; it must not
modify an already accepted historical result root.

For service-constrained V4/V5 EV fleets,
`maximum_ev_v1g_daily_energy_residual_gwh` is JSON `null` and
`ev_v1g_daily_energy_residual_applicability` is
`NOT_APPLICABLE_SERVICE_CONSTRAINED_EV_SOC_ACCOUNTING`. Their governing hard
evidence is the physical fleet-SOC transition, departure requirement, SOC
upper bound, charge/discharge power bounds and periodic boundary. The legacy
daily charging-energy residual remains numeric only for formulations where
grid charging must reproduce the uncontrolled daily reference.

## 6. Carbon terminology

The historical field `annual_gross_emissions_mtco2` is retained for compatibility, but the model quantity includes residual fossil emissions and BECCS net emissions before DAC. New outputs use the precise name `emissions_before_dac_mtco2`, alongside fossil-unabated emissions, CO2 captured for storage, DAC removal and final net emissions. The CISPO-equivalent BECCS baseline additionally exports `beccs_gross_biogenic_co2_mtco2`, `beccs_captured_biogenic_co2_mtco2`, `beccs_stored_co2_mtco2`, `beccs_uncaptured_biogenic_co2_mtco2`, `beccs_lifecycle_emissions_mtco2` and `beccs_net_removal_mtco2`. Baseline lifecycle emissions are explicitly zero; hard QC closes capture, storage, net carbon and total captured-CO2 reconstruction.

For the current continuous LP, `hourly_marginal_prices.csv.gz` exports provincial power-balance, reserve and inertia `Pi`, while `annual_constraint_shadow_prices.csv` exports carbon, biomass, capacity-margin and CCS scarcity values. `dual_export_status.json` records whether duals were available. A future nonconvex QCP/MIQCP must not interpret these LP duals as if they remain valid; Gurobi may not provide comparable shadow prices for a nonconvex solution.

## 7. Cross-year acceptance

Only `OPTIMAL + solution_qc=PASS + SCIENTIFIC_PRODUCTION` creates a planning state. State metadata contains SHA256 for the cohort table, transition summary, source QC and final solve report. Resume logic also validates the complete result manifest. A 744h/4344h test can never create a transferable state.

Existing 2025 VRE is currently held as an exogenous floor because plant-level commission/retirement ages are unavailable; existing hydropower is assumed operational through 2060. These are explicit long-term assumptions in `config/optimization_2030.json`, not inferred state-transfer behavior. Model-built cohorts retire by technology lifetime.

## 8. Multi-year architecture

The default is myopic sequential planning, not a joint perfect-foresight solve. This requires four solves in total but keeps peak memory close to one 8760-hour model and permits validation between years. A joint four-year model would generally be much harder, not lighter: chronological blocks, RUC/storage/hydrology/network variables and inter-year capacity couplings would coexist in memory. A perfect-foresight variant should therefore be treated as a separate research formulation and first tested on reduced spatial/temporal instances.

## 2026-10-05 opt-in 年度分段求和与容量清理

`formulation.annual_dense_row_split.enabled` 默认缺省/false；关闭时不新增变量、约束或审计字段。开启时，`annual_block_<family>_<unit>[b] = sum(y_t, t in block b)`，原有年度行使用这些块的和。默认 `block_hours=730`，末块保留实际小时数，DAC 固定小时负荷乘每块实际时长；全年预算和小时物理约束不变。辅助变量目标系数为零。发电/输送/捕集/生物质用非负界，净排放与未额外证明非负的有效需求用自由界。

变量后缀保留真实单位：电量 `_gwh`，排放/捕集 `_mtco2`，生物质 `_pj`，不能把这些年度流量统一命名为 GWh。实际 `master.py` 中的 carbon/biomass/co2_source 行已经引用年度变量；真正跨小时稠密项位于 `monolithic.py` 的排放、捕集、生物质 accounting 行，因此分段在源求和处实施，不对稀疏终端预算再加无效分层。

消去块定义变量/行可严格恢复原年度行。一个原模型对偶解可提升至新模型：对 `block - sum(y)=0` 定义行，使用与原年度行相应系数一致的乘子；原年度行的物理 RHS 敏感性及对偶解释保留。实际数值对偶解可能因退化、冗余非负界或求解容差而重新分配，不承诺每个 Pi 数值逐字节相同。辅助行 Pi 仅为 formulation 诊断量，不作为新的土地价格、碳价格或独立经济约束导出。

`numerics.hydro_capacity_headroom_zero_gw`、`retrofit_upper_zero_gw`、`inherited_floor_overrun_clip_gw` 均默认 0。前两项明确移除不超过阈值的容量区间，是可量化近似而非严格 LP 等价；仅非零配置进入科学指纹。续接截断只作用于本次构建的有效 floor，不修改已归档 cohort 文件；审计记录资产、截断量和阈值。后续再次导入仍从原始 cohort 重建 floor，重复同一显式检查，不累积截断；任何超过阈值的越界仍失败。水电、VRE、wave、nuclear、storage 的有限 GW 上界均使用同一检查；没有有限上界的资产及非 GW 存量不应用此 GW 截断。
