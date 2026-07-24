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

## 5. Carbon terminology

The historical field `annual_gross_emissions_mtco2` is retained for compatibility, but the model quantity includes residual fossil emissions and BECCS net emissions before DAC. New outputs use the precise name `emissions_before_dac_mtco2`, alongside fossil-unabated emissions, CO2 captured for storage, DAC removal and final net emissions. The CISPO-equivalent BECCS baseline additionally exports `beccs_gross_biogenic_co2_mtco2`, `beccs_captured_biogenic_co2_mtco2`, `beccs_stored_co2_mtco2`, `beccs_uncaptured_biogenic_co2_mtco2`, `beccs_lifecycle_emissions_mtco2` and `beccs_net_removal_mtco2`. Baseline lifecycle emissions are explicitly zero; hard QC closes capture, storage, net carbon and total captured-CO2 reconstruction.

For the current continuous LP, `hourly_marginal_prices.csv.gz` exports provincial power-balance, reserve and inertia `Pi`, while `annual_constraint_shadow_prices.csv` exports carbon, biomass, capacity-margin and CCS scarcity values. `dual_export_status.json` records whether duals were available. A future nonconvex QCP/MIQCP must not interpret these LP duals as if they remain valid; Gurobi may not provide comparable shadow prices for a nonconvex solution.

## 6. Cross-year acceptance

Only `OPTIMAL + solution_qc=PASS + SCIENTIFIC_PRODUCTION` creates a planning state. State metadata contains SHA256 for the cohort table, transition summary, source QC and final solve report. Resume logic also validates the complete result manifest. A 744h/4344h test can never create a transferable state.

Existing 2025 VRE is currently held as an exogenous floor because plant-level commission/retirement ages are unavailable; existing hydropower is assumed operational through 2060. These are explicit long-term assumptions in `config/optimization_2030.json`, not inferred state-transfer behavior. Model-built cohorts retire by technology lifetime.

## 7. Multi-year architecture

The default is myopic sequential planning, not a joint perfect-foresight solve. This requires four solves in total but keeps peak memory close to one 8760-hour model and permits validation between years. A joint four-year model would generally be much harder, not lighter: chronological blocks, RUC/storage/hydrology/network variables and inter-year capacity couplings would coexist in memory. A perfect-foresight variant should therefore be treated as a separate research formulation and first tested on reduced spatial/temporal instances.
