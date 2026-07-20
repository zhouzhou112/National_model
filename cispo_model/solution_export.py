"""Production solution export and numerical/physical quality control."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from gurobipy import GurobiError

from .config import ModelConfig
from .data import STORAGE_TECHS, THERMAL_TECHS, VRE_TECHS, ModelData
from .master import MasterArtifacts


def _value(expression: Any) -> np.ndarray:
    if hasattr(expression, "X"):
        return np.asarray(expression.X, dtype=float)
    if hasattr(expression, "getValue"):
        return np.asarray(expression.getValue(), dtype=float)
    return np.asarray(expression, dtype=float)


def _write_json(payload: dict[str, Any], path: Path) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def export_operational_solution(
    artifacts: MasterArtifacts,
    data: ModelData,
    config: ModelConfig,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Export chronological arrays, compact tables, and hard solution QC."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    variables = artifacts.variables
    hours = int(artifacts.index["optimization_hours"])
    provinces = np.asarray(artifacts.index["province_codes"], dtype=int)
    p_count = len(provinces)
    hour_index = np.arange(hours, dtype=int)
    load = np.asarray(artifacts.index["selected_load_gw"], dtype=float)

    vre_generation = _value(variables["vre_generation"])
    vre_available = _value(variables["vre_available"])
    thermal_gross = _value(variables["thermal_gross_generation"])
    thermal_net = _value(variables["actual_thermal_generation"])
    online = _value(variables["online"])
    startup = _value(variables["startup"])
    shutdown = _value(variables["shutdown"])
    ramp_magnitude = _value(variables["ramp_magnitude"])
    ror_generation = _value(variables["ror_generation"])
    ror_available = _value(variables["ror_available"])
    reservoir_generation = _value(variables["reservoir_generation"])
    reservoir_by_province = _value(variables["reservoir_generation_by_province"])
    reservoir_soc = _value(variables["reservoir_soc"])
    reservoir_spill = _value(variables["reservoir_spill"])
    reservoir_flow_scale_m3s = float(
        artifacts.index.get("reservoir_flow_scale_m3s", 1.0)
    )
    reservoir_volume_scale_m3 = float(
        artifacts.index.get("reservoir_volume_scale_m3", 1.0)
    )
    reservoir_turbine_flow = (
        _value(variables["reservoir_turbine_flow"])
        * reservoir_flow_scale_m3s
    )
    reservoir_spill_flow = (
        _value(variables["reservoir_spill_flow"])
        * reservoir_flow_scale_m3s
    )
    reservoir_volume = (
        _value(variables["reservoir_volume"])
        * reservoir_volume_scale_m3
    )
    reservoir_inflow = np.asarray(artifacts.index["reservoir_inflow_gwh"], dtype=float)
    reservoir_energy_upper = np.asarray(
        artifacts.index["reservoir_energy_upper_gwh"], dtype=float
    )
    reservoir_local_inflow = np.asarray(
        artifacts.index["reservoir_local_inflow_m3s"], dtype=float
    )
    reservoir_active_storage = np.asarray(
        artifacts.index["reservoir_active_storage_m3"], dtype=float
    )
    storage_charge = _value(variables["storage_charge"])
    storage_discharge = _value(variables["storage_discharge"])
    storage_soc = _value(variables["storage_soc"])
    storage_capacity = _value(variables["storage_capacity"])
    vre_capacity = _value(variables["vre_capacity"])
    hydro_capacity = _value(variables["hydro_capacity"])
    thermal_capacity = _value(variables["thermal_capacity"])
    storage_reserve_up_technology = _value(
        variables["storage_reserve_up_technology"]
    )
    storage_reserve_down_technology = _value(
        variables["storage_reserve_down_technology"]
    )
    flow_forward = _value(variables["flow_forward"])
    reverse_edge_rows = np.asarray(
        artifacts.index["interprovincial_reverse_edge_rows"], dtype=int
    )
    flow_reverse = np.zeros_like(flow_forward)
    flow_reverse[reverse_edge_rows, :] = _value(variables["flow_reverse_ac"])
    network_injection = _value(variables["network_injection"])
    dac_load = _value(variables["dac_load"])

    generation_total = (
        vre_generation.sum(axis=1)
        + thermal_net.sum(axis=1)
        + ror_generation
        + reservoir_by_province
        + storage_discharge.sum(axis=1)
        - storage_charge.sum(axis=1)
        + network_injection
    )
    balance_residual = generation_total - load - dac_load[:, None]

    thermal_up = _value(variables["thermal_reserve_up"])
    thermal_down = _value(variables["thermal_reserve_down"])
    vre_up = _value(variables["vre_reserve_up"])
    hydro_up = _value(variables["hydro_reserve_up"])
    storage_up = _value(variables["storage_reserve_up"])
    storage_down = _value(variables["storage_reserve_down"])
    security = config.raw["security"]
    vre_dispatch = vre_generation.sum(axis=1)
    up_requirement = (
        float(security["up_reserve_load_fraction"]) * load
        + float(security["up_reserve_vre_fraction"]) * vre_dispatch
    )
    down_requirement = (
        float(security["down_reserve_load_fraction"]) * load
        + float(security["down_reserve_vre_fraction"]) * vre_dispatch
    )
    up_margin = thermal_up + vre_up + hydro_up + storage_up - up_requirement
    down_margin = (
        thermal_down + ror_generation + reservoir_by_province + storage_down
        - down_requirement
    )

    dates = (
        data.load[["hour_index", "datetime_bj"]]
        .drop_duplicates("hour_index")
        .sort_values("hour_index")
        .iloc[:hours]
        .copy()
    )
    if len(dates) != hours:
        raise ValueError(f"Time index rows={len(dates)}; expected {hours}")
    dates["datetime_bj"] = pd.to_datetime(dates.datetime_bj)
    dates["month"] = dates.datetime_bj.dt.month
    dates["day_of_year"] = dates.datetime_bj.dt.dayofyear
    dates["hour_of_day"] = dates.datetime_bj.dt.hour
    dates.to_csv(
        output_dir / "time_index.csv", index=False, encoding="utf-8-sig"
    )

    ruc_table = data.ruc.set_index("technology").reindex(THERMAL_TECHS)
    inertia_s = ruc_table.inertia_s.to_numpy(dtype=float)
    thermal_inertia = (online * inertia_s[None, :, None]).sum(axis=1)
    hydro_inertia = _value(variables["hydro_inertia"]).reshape(p_count)
    storage_inertia_s = np.asarray(
        [
            float(config.raw["security"]["non_synchronous_inertia_seconds"][tech])
            for tech in STORAGE_TECHS
        ],
        dtype=float,
    )
    storage_inertia = storage_capacity @ storage_inertia_s
    inertia_provided = (
        thermal_inertia + hydro_inertia[:, None] + storage_inertia[:, None]
    )
    inertia_required = (
        float(config.raw["security"]["minimum_system_inertia_seconds"]) * load
    )
    capacity_credit = config.raw["security"]["capacity_credit"]
    credited_capacity = np.zeros(p_count, dtype=float)
    for p, province_code in enumerate(provinces):
        for technology, k in artifacts.index["thermal_index"].items():
            credited_capacity[p] += (
                float(capacity_credit[technology]) * thermal_capacity[p, k]
            )
        for technology, v in zip(VRE_TECHS, range(len(VRE_TECHS))):
            rows = (
                data.vre_sites.province_code.eq(province_code)
                & data.vre_sites.technology.eq(technology)
            ).to_numpy()
            credited_capacity[p] += (
                float(capacity_credit[technology]) * vre_capacity[rows].sum()
            )
        province_hydro = data.hydro_stations.province_code.eq(province_code)
        for technology, operation_type in (
            ("ror", "run_of_river"),
            ("reservoir", "reservoir_storage"),
        ):
            rows = (
                province_hydro
                & data.hydro_stations.operation_type_model.eq(operation_type)
            ).to_numpy()
            credited_capacity[p] += (
                float(capacity_credit[technology]) * hydro_capacity[rows].sum()
            )
        for technology, s in artifacts.index["storage_index"].items():
            credited_capacity[p] += (
                float(capacity_credit[technology]) * storage_capacity[p, s]
            )
    capacity_margin_required = (
        1.0 + float(config.raw["security"]["capacity_margin_fraction"])
    ) * data.load_gw.max(axis=1)
    capacity_margin = credited_capacity - capacity_margin_required

    pmin = ruc_table.pmin_fraction.to_numpy(dtype=float)
    pmax = ruc_table.pmax_fraction.to_numpy(dtype=float)
    ruc_transition_residual = (
        online - np.roll(online, 1, axis=2) - startup + shutdown
    )
    storage_overlap = np.minimum(storage_charge, storage_discharge)
    startup_shutdown_overlap = np.minimum(startup, shutdown)

    storage_table = data.storage.set_index("technology").reindex(STORAGE_TECHS)
    eta_c = storage_table.charge_efficiency.to_numpy(dtype=float)
    eta_d = storage_table.discharge_efficiency.to_numpy(dtype=float)
    self_discharge = 1.0 - (
        1.0 - storage_table.self_discharge_fraction_per_day.to_numpy(dtype=float)
    ) ** (1.0 / 24.0)
    storage_cycle_residual = np.empty_like(storage_soc)
    storage_cycle_residual[:, :, 0] = (
        storage_soc[:, :, 0]
        - (1.0 - self_discharge[None, :]) * storage_soc[:, :, -1]
        - eta_c[None, :] * storage_charge[:, :, 0]
        + storage_discharge[:, :, 0] / eta_d[None, :]
    )
    storage_cycle_residual[:, :, 1:] = (
        storage_soc[:, :, 1:]
        - (1.0 - self_discharge[None, :, None]) * storage_soc[:, :, :-1]
        - eta_c[None, :, None] * storage_charge[:, :, 1:]
        + storage_discharge[:, :, 1:] / eta_d[None, :, None]
    )

    upstream_release = np.zeros_like(reservoir_volume)
    for source_rows, target_rows, target_weights, lag in zip(
        artifacts.index.get("cascade_edge_source_local_rows", []),
        artifacts.index.get("cascade_edge_target_local_rows", []),
        artifacts.index.get("cascade_edge_target_weights", []),
        artifacts.index.get("cascade_edge_lag_h", []),
    ):
        source_rows = np.asarray(source_rows, dtype=int)
        target_rows = np.asarray(target_rows, dtype=int)
        target_weights = np.asarray(target_weights, dtype=float)
        release = (
            reservoir_turbine_flow[source_rows, :].sum(axis=0)
            + reservoir_spill_flow[source_rows, :].sum(axis=0)
        )
        shifted = np.roll(release, int(lag) % hours)
        for target_row, weight in zip(target_rows, target_weights):
            upstream_release[int(target_row), :] += float(weight) * shifted
    reservoir_cycle_residual = np.empty_like(reservoir_volume)
    reservoir_cycle_residual[:, 0] = (
        reservoir_volume[:, 0]
        - reservoir_volume[:, -1]
        - (
            reservoir_local_inflow[:, 0]
            + upstream_release[:, 0]
            - reservoir_turbine_flow[:, 0]
            - reservoir_spill_flow[:, 0]
        )
        * 3600.0
    )
    reservoir_cycle_residual[:, 1:] = (
        reservoir_volume[:, 1:]
        - reservoir_volume[:, :-1]
        - (
            reservoir_local_inflow[:, 1:]
            + upstream_release[:, 1:]
            - reservoir_turbine_flow[:, 1:]
            - reservoir_spill_flow[:, 1:]
        )
        * 3600.0
    )

    line_capacity = _value(variables["line_capacity"])
    line_violation = flow_forward + flow_reverse - line_capacity[:, None]
    thermal_floor = np.asarray(
        artifacts.index["thermal_capacity_floor_gw"], dtype=float
    )
    nuclear_k = int(artifacts.index["thermal_index"]["nuclear"])
    bio_k = int(artifacts.index["thermal_index"]["bio"])
    bioccs_k = int(artifacts.index["thermal_index"]["bioccs"])
    nuclear_upper = np.asarray(
        artifacts.index["nuclear_capacity_upper_gw"], dtype=float
    )
    biomass_pair_upper = np.asarray(
        artifacts.index["biomass_pair_capacity_upper_gw"], dtype=float
    )
    storage_floor = np.asarray(
        artifacts.index["storage_capacity_floor_gw"], dtype=float
    )
    vre_violation = vre_generation - vre_available
    annual_emissions = float(_value(variables["annual_emissions"]).sum())
    dac_removed = float(_value(variables["dac_capture"]).sum())
    net_emissions = annual_emissions - dac_removed
    carbon_limit = float(data.carbon.emissions_limit_mtco2_per_year)
    annual_biomass = _value(variables["annual_biomass"]).sum(axis=0)
    biomass_limit = (
        data.biomass.set_index("province_code")
        .thermcal_gj_per_year.reindex(provinces).to_numpy(dtype=float)
        / 1.0e6
    )
    captured = _value(variables["annual_captured"]).sum(axis=0)
    dac_by_province = _value(variables["dac_capture"]).sum(axis=1)
    co2_ship = _value(variables["co2_ship"])
    co2_source_residual = co2_ship.sum(axis=1) - captured - dac_by_province
    injection_field = str(config.raw["ccs_injection_field"])
    sinks = data.vre_points.loc[data.vre_points[injection_field].gt(0)]
    co2_sink_violation = co2_ship.sum(axis=0) - sinks[injection_field].to_numpy(float)

    thermal_energy = thermal_gross.sum(axis=2)
    emission_table = data.emissions.set_index("technology")
    coal_factor = float(
        emission_table.loc["coal", "emission_factor_mtco2_per_gwh"]
    )
    gas_factor = float(
        emission_table.loc["gas", "emission_factor_mtco2_per_gwh"]
    )
    capture_fraction = float(emission_table.loc["coal", "ccs_capture_fraction"])
    bioccs_factor = float(
        emission_table.loc["bioccs", "emission_factor_mtco2_per_gwh"]
    )
    fossil_unabated = np.zeros(p_count, dtype=float)
    emissions_before_dac_by_province = np.zeros(p_count, dtype=float)
    for technology, k in artifacts.index["thermal_index"].items():
        generation = thermal_energy[:, k]
        if technology.startswith("coal") or technology.startswith("cchp"):
            base_factor = coal_factor
        elif technology.startswith("gas") or technology.startswith("gchp"):
            base_factor = gas_factor
        else:
            base_factor = 0.0
        fossil_unabated += base_factor * generation
        if technology.endswith("ccs") and technology != "bioccs":
            emissions_before_dac_by_province += (
                base_factor * (1.0 - capture_fraction) * generation
            )
        elif technology == "bioccs":
            emissions_before_dac_by_province += bioccs_factor * generation
        else:
            emissions_before_dac_by_province += base_factor * generation
    dac_by_province = _value(variables["dac_capture"]).sum(axis=1)
    biomass_by_province = _value(variables["annual_biomass"]).sum(axis=0)

    cost_values = {
        name: float(expression.getValue())
        for name, expression in artifacts.cost_components.items()
    }
    objective_cost_values = {
        name: value
        for name, value in cost_values.items()
        if not name.startswith("operating_")
    }
    objective_value = float(artifacts.model.ObjVal)
    objective_component_residual = sum(objective_cost_values.values()) - objective_value
    tolerance = 1e-5
    # The internal water-balance equation is scaled to million m3. A 1 m3
    # physical tolerance is 1e-6 in that equation and remains negligible
    # relative to the largest active storage while aligning with LP tolerances.
    reservoir_volume_tolerance_m3 = 1.0
    flow_direction_tolerance_gw = 1e-6
    bidirectional_mask = (
        (flow_forward > flow_direction_tolerance_gw)
        & (flow_reverse > flow_direction_tolerance_gw)
    )
    bidirectional_minimum_flow = np.minimum(flow_forward, flow_reverse)
    dc_edge_mask = (
        data.lines.preset_technology.astype(str).str.upper().eq("DC").to_numpy()
    )
    maximum_dc_reverse_flow = float(
        flow_reverse[dc_edge_mask, :].max() if dc_edge_mask.any() else 0.0
    )
    qc = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "optimization_hours": hours,
        "maximum_power_balance_residual_gw": float(np.abs(balance_residual).max()),
        "minimum_up_reserve_margin_gw": float(up_margin.min()),
        "minimum_down_reserve_margin_gw": float(down_margin.min()),
        "minimum_inertia_margin_gw_s": float(
            (inertia_provided - inertia_required).min()
        ),
        "minimum_capacity_margin_gw": float(capacity_margin.min()),
        "maximum_ruc_transition_residual_gw": float(
            np.abs(ruc_transition_residual).max()
        ),
        "maximum_thermal_online_capacity_violation_gw": float(
            np.maximum(online - thermal_capacity[:, :, None], 0.0).max()
        ),
        "maximum_thermal_minimum_generation_violation_gw": float(
            np.maximum(pmin[None, :, None] * online - thermal_gross, 0.0).max()
        ),
        "maximum_thermal_maximum_generation_violation_gw": float(
            np.maximum(thermal_gross - pmax[None, :, None] * online, 0.0).max()
        ),
        "storage_simultaneous_charge_discharge_asset_hours": int(
            ((storage_charge > flow_direction_tolerance_gw)
             & (storage_discharge > flow_direction_tolerance_gw)).sum()
        ),
        "maximum_storage_charge_discharge_overlap_gw": float(storage_overlap.max()),
        "total_storage_charge_discharge_overlap_gwh": float(storage_overlap.sum()),
        "thermal_simultaneous_startup_shutdown_asset_hours": int(
            ((startup > flow_direction_tolerance_gw)
             & (shutdown > flow_direction_tolerance_gw)).sum()
        ),
        "maximum_thermal_startup_shutdown_overlap_gw": float(
            startup_shutdown_overlap.max()
        ),
        "maximum_vre_availability_violation_gw": float(np.maximum(vre_violation, 0.0).max()),
        "maximum_line_capacity_violation_gw": float(np.maximum(line_violation, 0.0).max()),
        "maximum_nuclear_capacity_floor_violation_gw": float(
            np.maximum(thermal_floor[:, nuclear_k] - thermal_capacity[:, nuclear_k], 0.0).max()
        ),
        "maximum_nuclear_capacity_upper_violation_gw": float(
            np.maximum(thermal_capacity[:, nuclear_k] - nuclear_upper, 0.0).max()
        ),
        "maximum_biomass_beccs_capacity_upper_violation_gw": float(
            np.maximum(
                thermal_capacity[:, bio_k] + thermal_capacity[:, bioccs_k]
                - biomass_pair_upper,
                0.0,
            ).max()
        ),
        "maximum_storage_capacity_floor_violation_gw": float(
            np.maximum(storage_floor - storage_capacity, 0.0).max()
        ),
        "maximum_storage_transition_residual_gwh": float(np.abs(storage_cycle_residual).max()),
        "maximum_storage_soc_upper_violation_gwh": float(
            np.maximum(
                storage_soc
                - storage_capacity[:, :, None]
                * storage_table.duration_h.to_numpy(float)[None, :, None],
                0.0,
            ).max()
        ),
        "maximum_reservoir_transition_residual_m3": float(np.abs(reservoir_cycle_residual).max()),
        "maximum_reservoir_energy_upper_violation_gwh": float(
            np.maximum(reservoir_soc - reservoir_energy_upper[:, None], 0.0).max()
        ),
        "maximum_reservoir_active_storage_upper_violation_m3": float(
            np.maximum(reservoir_volume - reservoir_active_storage[:, None], 0.0).max()
        ),
        "core_cascade_station_rows": int(
            len(np.asarray(artifacts.index.get("cascade_station_local_rows", [])))
        ),
        "core_cascade_edges": int(
            len(artifacts.index.get("cascade_edge_ids", []))
        ),
        "annual_gross_emissions_mtco2": annual_emissions,
        "annual_emissions_before_dac_mtco2": annual_emissions,
        "annual_dac_removed_mtco2": dac_removed,
        "annual_net_emissions_mtco2": net_emissions,
        "carbon_limit_mtco2": carbon_limit,
        "carbon_limit_margin_mtco2": carbon_limit - net_emissions,
        "maximum_biomass_limit_violation_pj": float(
            np.maximum(annual_biomass - biomass_limit, 0.0).max()
        ),
        "maximum_co2_source_balance_residual_mt": float(np.abs(co2_source_residual).max()),
        "maximum_co2_sink_capacity_violation_mt": float(np.maximum(co2_sink_violation, 0.0).max()),
        "objective_value_million_cny": objective_value,
        "objective_component_residual_million_cny": objective_component_residual,
        "total_vre_curtailment_gwh": float((vre_available - vre_generation).sum()),
        "bidirectional_interprovincial_edge_hours": int(
            bidirectional_mask.sum()
        ),
        "bidirectional_flow_tolerance_gw": flow_direction_tolerance_gw,
        "maximum_bidirectional_minimum_flow_gw": float(
            bidirectional_minimum_flow[bidirectional_mask].max()
            if bidirectional_mask.any()
            else 0.0
        ),
        "total_bidirectional_minimum_flow_gwh": float(
            bidirectional_minimum_flow[bidirectional_mask].sum()
        ),
        "dc_fixed_direction_edge_count": int(dc_edge_mask.sum()),
        "maximum_dc_reverse_flow_gw": maximum_dc_reverse_flow,
    }
    hard_checks = {
        "power_balance": qc["maximum_power_balance_residual_gw"] <= tolerance,
        "up_reserve": qc["minimum_up_reserve_margin_gw"] >= -tolerance,
        "down_reserve": qc["minimum_down_reserve_margin_gw"] >= -tolerance,
        "inertia": qc["minimum_inertia_margin_gw_s"] >= -tolerance,
        "capacity_margin": qc["minimum_capacity_margin_gw"] >= -tolerance,
        "ruc_transition": qc["maximum_ruc_transition_residual_gw"] <= tolerance,
        "thermal_online_capacity": qc[
            "maximum_thermal_online_capacity_violation_gw"
        ] <= tolerance,
        "thermal_minimum_generation": qc[
            "maximum_thermal_minimum_generation_violation_gw"
        ] <= tolerance,
        "thermal_maximum_generation": qc[
            "maximum_thermal_maximum_generation_violation_gw"
        ] <= tolerance,
        "vre_availability": qc["maximum_vre_availability_violation_gw"] <= tolerance,
        "line_capacity": qc["maximum_line_capacity_violation_gw"] <= tolerance,
        "nuclear_capacity_floor": qc[
            "maximum_nuclear_capacity_floor_violation_gw"
        ] <= tolerance,
        "nuclear_capacity_upper": qc[
            "maximum_nuclear_capacity_upper_violation_gw"
        ] <= tolerance,
        "biomass_beccs_capacity_upper": qc[
            "maximum_biomass_beccs_capacity_upper_violation_gw"
        ] <= tolerance,
        "storage_capacity_floor": qc[
            "maximum_storage_capacity_floor_violation_gw"
        ] <= tolerance,
        "unidirectional_interprovincial_flow": qc[
            "bidirectional_interprovincial_edge_hours"
        ] == 0,
        "dc_fixed_direction": qc["maximum_dc_reverse_flow_gw"]
        <= flow_direction_tolerance_gw,
        "storage_transition": qc["maximum_storage_transition_residual_gwh"] <= tolerance,
        "storage_soc": qc["maximum_storage_soc_upper_violation_gwh"] <= tolerance,
        "reservoir_transition": qc["maximum_reservoir_transition_residual_m3"] <= reservoir_volume_tolerance_m3,
        "reservoir_energy": qc["maximum_reservoir_energy_upper_violation_gwh"] <= tolerance,
        "reservoir_active_storage": qc["maximum_reservoir_active_storage_upper_violation_m3"] <= reservoir_volume_tolerance_m3,
        "carbon": qc["carbon_limit_margin_mtco2"] >= -tolerance,
        "biomass": qc["maximum_biomass_limit_violation_pj"] <= tolerance,
        "co2_source": qc["maximum_co2_source_balance_residual_mt"] <= tolerance,
        "co2_sink": qc["maximum_co2_sink_capacity_violation_mt"] <= tolerance,
        "objective_components": abs(objective_component_residual) <= tolerance,
    }
    qc["hard_checks"] = hard_checks
    qc["status"] = "PASS" if all(hard_checks.values()) else "HARD_FAIL"
    _write_json(qc, output_dir / "solution_qc.json")

    province_hour = pd.DataFrame(
        {
            "province_code": np.repeat(provinces, hours),
            "hour_index": np.tile(hour_index, p_count),
            "datetime_bj": np.tile(
                dates.datetime_bj.dt.strftime("%Y-%m-%d %H:%M:%S").to_numpy(),
                p_count,
            ),
            "load_gw": load.ravel(),
            "vre_generation_gw": vre_generation.sum(axis=1).ravel(),
            "thermal_net_generation_gw": thermal_net.sum(axis=1).ravel(),
            "ror_generation_gw": ror_generation.ravel(),
            "reservoir_generation_gw": reservoir_by_province.ravel(),
            "storage_charge_gw": storage_charge.sum(axis=1).ravel(),
            "storage_discharge_gw": storage_discharge.sum(axis=1).ravel(),
            "network_injection_gw": network_injection.ravel(),
            "dac_load_gw": np.repeat(dac_load, hours),
            "balance_residual_gw": balance_residual.ravel(),
            "up_reserve_margin_gw": up_margin.ravel(),
            "down_reserve_margin_gw": down_margin.ravel(),
        }
    )
    province_hour.to_csv(
        output_dir / "hourly_province_balance.csv.gz",
        index=False,
        compression="gzip",
        encoding="utf-8-sig",
    )

    security_hour = pd.DataFrame(
        {
            "province_code": np.repeat(provinces, hours),
            "hour_index": np.tile(hour_index, p_count),
            "datetime_bj": np.tile(
                dates.datetime_bj.dt.strftime("%Y-%m-%d %H:%M:%S").to_numpy(),
                p_count,
            ),
            "up_reserve_requirement_gw": up_requirement.ravel(),
            "up_reserve_thermal_gw": thermal_up.ravel(),
            "up_reserve_vre_gw": vre_up.ravel(),
            "up_reserve_hydro_gw": hydro_up.ravel(),
            "up_reserve_storage_gw": storage_up.ravel(),
            "up_reserve_margin_gw": up_margin.ravel(),
            "down_reserve_requirement_gw": down_requirement.ravel(),
            "down_reserve_thermal_gw": thermal_down.ravel(),
            "down_reserve_hydro_gw": (ror_generation + reservoir_by_province).ravel(),
            "down_reserve_storage_gw": storage_down.ravel(),
            "down_reserve_margin_gw": down_margin.ravel(),
            "inertia_required_gw_s": inertia_required.ravel(),
            "inertia_thermal_gw_s": thermal_inertia.ravel(),
            "inertia_hydro_gw_s": np.repeat(hydro_inertia, hours),
            "inertia_storage_gw_s": np.repeat(storage_inertia, hours),
            "inertia_provided_gw_s": inertia_provided.ravel(),
            "inertia_margin_gw_s": (inertia_provided - inertia_required).ravel(),
        }
    )
    security_hour.to_csv(
        output_dir / "hourly_province_security.csv.gz",
        index=False,
        compression="gzip",
        encoding="utf-8-sig",
    )

    dual_status: dict[str, Any] = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "available": False,
        "model_class": "continuous_linear_program",
        "note": (
            "Gurobi Pi is the derivative of the objective with respect to the "
            "constraint RHS. Equality power-balance Pi is reported as an energy "
            "price; inequality scarcity values use the documented tightening sign."
        ),
    }
    try:
        handles = artifacts.index["constraint_handles"]
        power_balance_pi = np.vstack(
            [np.asarray(handle.Pi, dtype=float) for handle in handles["strict_power_balance"]]
        )
        up_reserve_pi = np.asarray(handles["up_reserve"].Pi, dtype=float)
        down_reserve_pi = np.asarray(handles["down_reserve"].Pi, dtype=float)
        inertia_pi = np.vstack(
            [np.asarray(handle.Pi, dtype=float) for handle in handles["inertia"]]
        )
        if any(
            value.shape != (p_count, hours)
            for value in (
                power_balance_pi, up_reserve_pi, down_reserve_pi, inertia_pi
            )
        ):
            raise ValueError("Unexpected hourly dual-array shape")
        pd.DataFrame(
            {
                "province_code": np.repeat(provinces, hours),
                "hour_index": np.tile(hour_index, p_count),
                "datetime_bj": np.tile(
                    dates.datetime_bj.dt.strftime("%Y-%m-%d %H:%M:%S").to_numpy(),
                    p_count,
                ),
                "power_balance_pi_million_cny_per_gwh": power_balance_pi.ravel(),
                "marginal_energy_price_cny_per_mwh": (
                    power_balance_pi * 1000.0
                ).ravel(),
                "up_reserve_pi_million_cny_per_gwh": up_reserve_pi.ravel(),
                "up_reserve_scarcity_cny_per_mwh": (
                    up_reserve_pi * 1000.0
                ).ravel(),
                "down_reserve_pi_million_cny_per_gwh": down_reserve_pi.ravel(),
                "down_reserve_scarcity_cny_per_mwh": (
                    down_reserve_pi * 1000.0
                ).ravel(),
                "inertia_pi_million_cny_per_gw_s": inertia_pi.ravel(),
                "inertia_scarcity_million_cny_per_gw_s": inertia_pi.ravel(),
            }
        ).to_csv(
            output_dir / "hourly_marginal_prices.csv.gz",
            index=False,
            compression="gzip",
            encoding="utf-8-sig",
        )

        annual_dual_rows: list[dict[str, Any]] = []

        def add_dual(
            constraint: str,
            index_type: str,
            index_value: Any,
            pi: float,
            sense: str,
            interpreted_unit: str,
        ) -> None:
            annual_dual_rows.append(
                {
                    "constraint": constraint,
                    "index_type": index_type,
                    "index_value": index_value,
                    "sense": sense,
                    "gurobi_pi": float(pi),
                    "tightening_scarcity_value": (
                        -float(pi) if sense == "<=" else float(pi)
                    ),
                    "interpreted_unit": interpreted_unit,
                }
            )

        add_dual(
            "annual_net_carbon_limit",
            "national",
            "China",
            float(handles["annual_net_carbon_limit"].Pi),
            "<=",
            "CNY_per_tCO2",
        )
        for province_code, pi in zip(
            provinces,
            np.asarray(handles["annual_biomass_fuel_limit"].Pi, dtype=float),
        ):
            add_dual(
                "annual_biomass_fuel_limit",
                "province_code",
                int(province_code),
                float(pi),
                "<=",
                "CNY_per_GJ",
            )
        for province_code, handle in zip(provinces, handles["capacity_margin"]):
            add_dual(
                "capacity_margin",
                "province_code",
                int(province_code),
                float(handle.Pi),
                ">=",
                "CNY_per_kW_credited_capacity",
            )
        for province_code, pi in zip(
            provinces,
            np.asarray(handles["biomass_beccs_capacity_upper"].Pi, dtype=float),
        ):
            add_dual(
                "biomass_beccs_capacity_upper",
                "province_code",
                int(province_code),
                float(pi),
                "<=",
                "CNY_per_kW",
            )
        for province_code, handle in zip(
            provinces, handles["co2_source_balance"]
        ):
            add_dual(
                "co2_source_balance",
                "province_code",
                int(province_code),
                float(handle.Pi),
                "=",
                "CNY_per_tCO2",
            )
        sink_pi = np.asarray(
            handles["co2_sink_injection_capacity"].Pi, dtype=float
        )
        for sink_uid, pi in zip(sinks.grid_uid.astype(str), sink_pi):
            add_dual(
                "co2_sink_injection_capacity",
                "sink_grid_uid",
                sink_uid,
                float(pi),
                "<=",
                "CNY_per_tCO2",
            )
        pd.DataFrame(annual_dual_rows).to_csv(
            output_dir / "annual_constraint_shadow_prices.csv",
            index=False,
            encoding="utf-8-sig",
        )
        dual_status.update(
            available=True,
            hourly_rows=int(p_count * hours),
            annual_rows=int(len(annual_dual_rows)),
        )
    except (AttributeError, KeyError, TypeError, ValueError, GurobiError) as exc:
        dual_status["reason"] = f"{type(exc).__name__}: {exc}"
    _write_json(dual_status, output_dir / "dual_export_status.json")

    pd.DataFrame(
        {
            "province_code": provinces,
            "peak_load_gw": data.load_gw.max(axis=1),
            "capacity_margin_fraction": float(
                config.raw["security"]["capacity_margin_fraction"]
            ),
            "credited_capacity_required_gw": capacity_margin_required,
            "credited_capacity_available_gw": credited_capacity,
            "capacity_margin_gw": capacity_margin,
        }
    ).to_csv(
        output_dir / "annual_adequacy_by_province.csv",
        index=False,
        encoding="utf-8-sig",
    )

    generation_rows: list[dict[str, Any]] = []
    for p, province_code in enumerate(provinces):
        for technology, v in zip(VRE_TECHS, range(len(VRE_TECHS))):
            generation_rows.append(
                {
                    "province_code": int(province_code),
                    "technology": technology,
                    "generation_gwh": float(vre_generation[p, v, :].sum()),
                }
            )
        for technology, k in artifacts.index["thermal_index"].items():
            generation_rows.append(
                {
                    "province_code": int(province_code),
                    "technology": technology,
                    "generation_gwh": float(thermal_net[p, k, :].sum()),
                }
            )
        generation_rows.extend(
            [
                {
                    "province_code": int(province_code),
                    "technology": "ror",
                    "generation_gwh": float(ror_generation[p, :].sum()),
                },
                {
                    "province_code": int(province_code),
                    "technology": "reservoir",
                    "generation_gwh": float(reservoir_by_province[p, :].sum()),
                },
            ]
        )
    pd.DataFrame(generation_rows).to_csv(
        output_dir / "annual_generation_by_province_technology.csv",
        index=False,
        encoding="utf-8-sig",
    )

    pd.DataFrame(
        {
            "province_code": provinces,
            "fossil_unabated_emissions_mtco2": fossil_unabated,
            "emissions_before_dac_mtco2": emissions_before_dac_by_province,
            "co2_captured_for_storage_mtco2": captured,
            "dac_removed_mtco2": dac_by_province,
            "net_emissions_after_dac_mtco2": (
                emissions_before_dac_by_province - dac_by_province
            ),
            "biomass_fuel_pj": biomass_by_province,
            "dac_electricity_gwh": dac_load * hours,
        }
    ).to_csv(
        output_dir / "annual_resource_accounting_by_province.csv",
        index=False,
        encoding="utf-8-sig",
    )

    np.savez_compressed(
        output_dir / "thermal_dispatch.npz",
        gross_generation_gw=thermal_gross,
        net_generation_gw=thermal_net,
        online_capacity_gw=online,
        startup_capacity_gw=startup,
        shutdown_capacity_gw=shutdown,
        ramp_magnitude_gw=ramp_magnitude,
        reserve_up_gw=thermal_up,
        reserve_down_gw=thermal_down,
        province_codes=provinces,
        technologies=np.asarray(THERMAL_TECHS),
        hour_index=hour_index,
    )
    np.savez_compressed(
        output_dir / "vre_dispatch.npz",
        generation_gw=vre_generation,
        available_gw=vre_available,
        reserve_up_gw=vre_up,
        province_codes=provinces,
        technologies=np.asarray(VRE_TECHS),
        hour_index=hour_index,
    )
    np.savez_compressed(
        output_dir / "storage_dispatch.npz",
        charge_gw=storage_charge,
        discharge_gw=storage_discharge,
        soc_gwh=storage_soc,
        reserve_up_gw=storage_reserve_up_technology,
        reserve_down_gw=storage_reserve_down_technology,
        province_codes=provinces,
        technologies=np.asarray(STORAGE_TECHS),
        hour_index=hour_index,
    )
    reservoir_station_rows = np.asarray(
        artifacts.variables["reservoir_station_rows"], dtype=int
    )
    reservoir_index = data.hydro_stations.iloc[reservoir_station_rows].copy()
    reservoir_index.insert(0, "reservoir_local_index", np.arange(len(reservoir_index)))
    cascade_local_rows = set(
        np.asarray(artifacts.index.get("cascade_station_local_rows", []), dtype=int).tolist()
    )
    reservoir_index["is_core_cascade_station"] = reservoir_index.reservoir_local_index.isin(
        cascade_local_rows
    )
    reservoir_index.to_csv(
        output_dir / "reservoir_station_index.csv", index=False, encoding="utf-8-sig"
    )
    np.savez_compressed(
        output_dir / "reservoir_dispatch.npz",
        generation_gw=reservoir_generation,
        soc_gwh=reservoir_soc,
        spill_gwh=reservoir_spill,
        turbine_flow_m3s=reservoir_turbine_flow,
        spill_flow_m3s=reservoir_spill_flow,
        active_storage_m3=reservoir_volume,
        local_inflow_m3s=reservoir_local_inflow,
        upstream_release_m3s=upstream_release,
        inflow_gwh=reservoir_inflow,
        energy_upper_gwh=reservoir_energy_upper,
        active_storage_upper_m3=reservoir_active_storage,
        core_cascade_local_rows=np.asarray(
            artifacts.index.get("cascade_station_local_rows", []), dtype=int
        ),
        core_cascade_edge_ids=np.asarray(
            artifacts.index.get("cascade_edge_ids", []), dtype=str
        ),
        core_cascade_edge_lag_h=np.asarray(
            artifacts.index.get("cascade_edge_lag_h", []), dtype=int
        ),
        hydrochn_row_id=reservoir_index.hydrochn_row_id.astype(str).to_numpy(dtype=str),
        hour_index=hour_index,
    )
    np.savez_compressed(
        output_dir / "hydro_dispatch.npz",
        ror_generation_gw=ror_generation,
        ror_available_gw=ror_available,
        reservoir_generation_gw=reservoir_by_province,
        reserve_up_gw=hydro_up,
        province_codes=provinces,
        hour_index=hour_index,
    )
    np.savez_compressed(
        output_dir / "transmission_flows.npz",
        forward_gw=flow_forward,
        reverse_gw=flow_reverse,
        line_ids=data.lines.line_id.astype(str).to_numpy(dtype=str),
        hour_index=hour_index,
    )

    carbon = {
        "annual_gross_emissions_mtco2": annual_emissions,
        "annual_emissions_before_dac_mtco2": annual_emissions,
        "annual_fossil_unabated_emissions_mtco2": float(fossil_unabated.sum()),
        "annual_dac_removed_mtco2": dac_removed,
        "annual_net_emissions_mtco2": net_emissions,
        "carbon_limit_mtco2": carbon_limit,
        "annual_captured_mtco2": float(captured.sum()),
        "annual_co2_shipped_mtco2": float(co2_ship.sum()),
    }
    _write_json(carbon, output_dir / "annual_carbon_ccs.json")
    if qc["status"] != "PASS":
        raise RuntimeError(f"Production solution QC failed: {hard_checks}")
    return qc
