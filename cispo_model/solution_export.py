"""Production solution export and numerical/physical quality control."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

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
    ror_generation = _value(variables["ror_generation"])
    ror_available = _value(variables["ror_available"])
    reservoir_generation = _value(variables["reservoir_generation"])
    reservoir_by_province = _value(variables["reservoir_generation_by_province"])
    reservoir_soc = _value(variables["reservoir_soc"])
    reservoir_spill = _value(variables["reservoir_spill"])
    reservoir_turbine_flow = _value(variables["reservoir_turbine_flow"])
    reservoir_spill_flow = _value(variables["reservoir_spill_flow"])
    reservoir_volume = _value(variables["reservoir_volume"])
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
    flow_forward = _value(variables["flow_forward"])
    flow_reverse = _value(variables["flow_reverse"])
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
    reservoir_volume_tolerance_m3 = 1e-2
    qc = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "optimization_hours": hours,
        "maximum_power_balance_residual_gw": float(np.abs(balance_residual).max()),
        "minimum_up_reserve_margin_gw": float(up_margin.min()),
        "minimum_down_reserve_margin_gw": float(down_margin.min()),
        "maximum_vre_availability_violation_gw": float(np.maximum(vre_violation, 0.0).max()),
        "maximum_line_capacity_violation_gw": float(np.maximum(line_violation, 0.0).max()),
        "maximum_storage_transition_residual_gwh": float(np.abs(storage_cycle_residual).max()),
        "maximum_storage_soc_upper_violation_gwh": float(
            np.maximum(
                storage_soc
                - _value(variables["storage_capacity"])[:, :, None]
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
            ((flow_forward > 1e-7) & (flow_reverse > 1e-7)).sum()
        ),
    }
    hard_checks = {
        "power_balance": qc["maximum_power_balance_residual_gw"] <= tolerance,
        "up_reserve": qc["minimum_up_reserve_margin_gw"] >= -tolerance,
        "down_reserve": qc["minimum_down_reserve_margin_gw"] >= -tolerance,
        "vre_availability": qc["maximum_vre_availability_violation_gw"] <= tolerance,
        "line_capacity": qc["maximum_line_capacity_violation_gw"] <= tolerance,
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

    np.savez_compressed(
        output_dir / "thermal_dispatch.npz",
        gross_generation_gw=thermal_gross,
        net_generation_gw=thermal_net,
        online_capacity_gw=online,
        startup_capacity_gw=startup,
        shutdown_capacity_gw=shutdown,
        province_codes=provinces,
        technologies=np.asarray(THERMAL_TECHS),
        hour_index=hour_index,
    )
    np.savez_compressed(
        output_dir / "vre_dispatch.npz",
        generation_gw=vre_generation,
        available_gw=vre_available,
        province_codes=provinces,
        technologies=np.asarray(VRE_TECHS),
        hour_index=hour_index,
    )
    np.savez_compressed(
        output_dir / "storage_dispatch.npz",
        charge_gw=storage_charge,
        discharge_gw=storage_discharge,
        soc_gwh=storage_soc,
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
        hydrochn_row_id=reservoir_index.hydrochn_row_id.astype(str).to_numpy(),
        hour_index=hour_index,
    )
    np.savez_compressed(
        output_dir / "transmission_flows.npz",
        forward_gw=flow_forward,
        reverse_gw=flow_reverse,
        line_ids=data.lines.line_id.astype(str).to_numpy(),
        hour_index=hour_index,
    )

    carbon = {
        "annual_gross_emissions_mtco2": annual_emissions,
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
