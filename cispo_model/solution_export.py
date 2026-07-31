"""Production solution export and numerical/physical quality control."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from gurobipy import GurobiError

from .carbon_accounting import resolve_beccs_carbon_factors
from .config import ModelConfig, resolve_minimum_system_inertia_seconds
from .data import STORAGE_TECHS, THERMAL_TECHS, VRE_TECHS, ModelData
from .master import MasterArtifacts
from .wave_energy import reconstruct_wave_availability


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


def _ev_v1g_daily_energy_residual_for_qc(
    residual: np.ndarray,
    *,
    service_contract_formulation: bool,
) -> tuple[float | None, str]:
    """Return the legacy V1G residual only where its identity applies.

    Service-constrained V4/V5 uses a physical fleet-SOC transition with driving
    withdrawals, efficiencies and a periodic boundary. Comparing its grid
    charging directly with the uncontrolled reference is therefore not an
    energy-conservation identity and must not be reported as a residual.
    """
    if service_contract_formulation:
        return (
            None,
            "NOT_APPLICABLE_SERVICE_CONSTRAINED_EV_SOC_ACCOUNTING",
        )
    return (
        float(np.abs(np.asarray(residual, dtype=float)).max()),
        "APPLICABLE_LEGACY_DAILY_CHARGING_ENERGY_ACCOUNTING",
    )


def assess_interprovincial_bidirectionality(
    *,
    flow_forward: np.ndarray,
    flow_reverse: np.ndarray,
    line_capacity_gw: np.ndarray,
    line_efficiency: np.ndarray,
    system_load_gwh: float,
    optimization_hours: int,
    configured_hours: int,
    tolerance_gw: float,
    warning_contract: dict[str, Any],
) -> dict[str, Any]:
    """Classify AC counterflow without weakening full-year scientific QC.

    The directional-flow LP can use simultaneous opposite flows as a small
    lossy sink under deep negative prices.  Truncated engineering gates may
    retain such a solution only as an explicit warning when every power,
    energy, loss and prevalence budget below is satisfied.  A full-year run
    always requires strict zero counterflow above ``tolerance_gw``.
    """
    forward = np.asarray(flow_forward, dtype=float)
    reverse = np.asarray(flow_reverse, dtype=float)
    if forward.shape != reverse.shape or forward.ndim != 2:
        raise ValueError("Directional transmission arrays must be matching 2-D arrays")
    capacity = np.asarray(line_capacity_gw, dtype=float)
    efficiency = np.asarray(line_efficiency, dtype=float)
    if capacity.shape != (forward.shape[0],):
        raise ValueError("line_capacity_gw must have one value per corridor")
    if efficiency.shape != (forward.shape[0],):
        raise ValueError("line_efficiency must have one value per corridor")
    if (
        not np.isfinite(forward).all()
        or not np.isfinite(reverse).all()
        or not np.isfinite(capacity).all()
        or not np.isfinite(efficiency).all()
    ):
        raise ValueError("Directionality assessment requires finite inputs")
    if (capacity < 0.0).any() or (efficiency <= 0.0).any() or (efficiency > 1.0).any():
        raise ValueError("Invalid line capacity or efficiency")
    if optimization_hours <= 0 or configured_hours <= 0:
        raise ValueError("Optimization and configured hours must be positive")
    if tolerance_gw < 0.0 or system_load_gwh < 0.0:
        raise ValueError("Directionality tolerance and system load must be nonnegative")

    mask = (forward > tolerance_gw) & (reverse > tolerance_gw)
    opposing = np.where(mask, np.minimum(forward, reverse), 0.0)
    positive_capacity = np.where(capacity > tolerance_gw, capacity, np.inf)
    opposing_fraction = opposing / positive_capacity[:, None]
    excess_loss = 2.0 * (1.0 - efficiency[:, None]) * opposing
    gross_flow_gwh = float((forward + reverse).sum())
    opposing_energy_gwh = float(opposing.sum())
    excess_loss_gwh = float(excess_loss.sum())
    strict_pass = bool(not mask.any())

    reference_hours = int(warning_contract["reference_hours"])
    horizon_scale = float(optimization_hours) / float(reference_hours)
    limits = {
        "maximum_edge_hours": int(
            np.ceil(
                float(warning_contract["maximum_edge_hours_per_reference"])
                * horizon_scale
            )
        ),
        "maximum_opposing_flow_gw": float(
            warning_contract["maximum_opposing_flow_gw"]
        ),
        "maximum_opposing_fraction_of_line_capacity": float(
            warning_contract["maximum_opposing_fraction_of_line_capacity"]
        ),
        "maximum_opposing_energy_gwh": float(
            warning_contract["maximum_opposing_energy_gwh_per_reference"]
        )
        * horizon_scale,
        "maximum_excess_loss_gwh": float(
            warning_contract["maximum_excess_loss_gwh_per_reference"]
        )
        * horizon_scale,
        "maximum_opposing_share_of_gross_flow": float(
            warning_contract["maximum_opposing_share_of_gross_flow"]
        ),
        "maximum_excess_loss_share_of_system_load": float(
            warning_contract["maximum_excess_loss_share_of_system_load"]
        ),
    }
    observed = {
        "edge_hours": int(mask.sum()),
        "maximum_opposing_flow_gw": float(
            opposing[mask].max() if mask.any() else 0.0
        ),
        "maximum_opposing_fraction_of_line_capacity": float(
            opposing_fraction[mask].max() if mask.any() else 0.0
        ),
        "opposing_energy_gwh": opposing_energy_gwh,
        "excess_loss_gwh": excess_loss_gwh,
        "opposing_share_of_gross_flow": (
            opposing_energy_gwh / gross_flow_gwh if gross_flow_gwh > 0.0 else 0.0
        ),
        "excess_loss_share_of_system_load": (
            excess_loss_gwh / float(system_load_gwh)
            if system_load_gwh > 0.0
            else 0.0
        ),
    }
    within_warning_budget = bool(
        observed["edge_hours"] <= limits["maximum_edge_hours"]
        and observed["maximum_opposing_flow_gw"]
        <= limits["maximum_opposing_flow_gw"]
        and observed["maximum_opposing_fraction_of_line_capacity"]
        <= limits["maximum_opposing_fraction_of_line_capacity"]
        and observed["opposing_energy_gwh"]
        <= limits["maximum_opposing_energy_gwh"]
        and observed["excess_loss_gwh"] <= limits["maximum_excess_loss_gwh"]
        and observed["opposing_share_of_gross_flow"]
        <= limits["maximum_opposing_share_of_gross_flow"]
        and observed["excess_loss_share_of_system_load"]
        <= limits["maximum_excess_loss_share_of_system_load"]
    )
    diagnostic_scope = optimization_hours < configured_hours
    warning_applied = bool(
        not strict_pass
        and diagnostic_scope
        and bool(warning_contract["enabled"])
        and within_warning_budget
    )
    accepted = bool(strict_pass or warning_applied)
    if strict_pass:
        classification = "STRICT_PASS"
    elif warning_applied:
        classification = "TEST_ONLY_DE_MINIMIS_WARNING"
    else:
        classification = "HARD_FAIL"
    return {
        "accepted": accepted,
        "strict_pass": strict_pass,
        "warning_applied": warning_applied,
        "within_warning_budget": within_warning_budget,
        "classification": classification,
        "acceptance_scope": (
            "STRICT_FULL_YEAR"
            if optimization_hours == configured_hours
            else "TEST_ONLY_TRUNCATED_HORIZON"
        ),
        "tolerance_gw": float(tolerance_gw),
        "reference_hours": reference_hours,
        "horizon_scale": horizon_scale,
        "limits": limits,
        "observed": observed,
    }


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
    hour_start = int(artifacts.index.get("optimization_start_hour", 0))
    hour_stop = hour_start + hours
    selected_hours = slice(hour_start, hour_stop)
    provinces = np.asarray(artifacts.index["province_codes"], dtype=int)
    p_count = len(provinces)
    hour_index = np.arange(hours, dtype=int)
    load = _value(artifacts.index["selected_load_gw"])
    baseline_load = np.asarray(artifacts.index["baseline_load_gw"], dtype=float)
    baseline_components = {
        name: np.asarray(values, dtype=float)
        for name, values in artifacts.index["baseline_load_components_gw"].items()
    }
    actual_components = {
        name: _value(values)
        for name, values in artifacts.index["actual_load_components_gw"].items()
    }
    flexible_formulation = str(
        config.raw["flexible_load"].get(
            "formulation", "daily_energy_shift_v1"
        )
    )
    zero_load = np.zeros_like(baseline_load)
    heating_up = _value(variables.get("heating_shift_up", zero_load))
    heating_down = _value(variables.get("heating_shift_down", zero_load))
    cooling_up = _value(variables.get("cooling_shift_up", zero_load))
    cooling_down = _value(variables.get("cooling_shift_down", zero_load))
    ev_up = _value(variables.get("ev_v1g_shift_up", zero_load))
    ev_down = _value(variables.get("ev_v1g_shift_down", zero_load))
    heating_state = _value(variables.get("heating_state", zero_load))
    cooling_state = _value(variables.get("cooling_state", zero_load))
    heating_comfort_debt = _value(
        variables.get("heating_comfort_debt", zero_load)
    )
    cooling_comfort_debt = _value(
        variables.get("cooling_comfort_debt", zero_load)
    )
    ev_backlog = _value(variables.get("ev_v1g_backlog", zero_load))
    ev_mobility_charge = _value(
        variables.get("ev_mobility_charge", zero_load)
    )
    ev_mobility_discharge = _value(
        variables.get("ev_mobility_discharge", zero_load)
    )
    ev_mobility_soc = _value(variables.get("ev_mobility_soc", zero_load))
    if "ev_mobility_charge_deviation" in variables:
        ev_mobility_charge_deviation = _value(
            variables["ev_mobility_charge_deviation"]
        )
    elif flexible_formulation == "integrated_service_constrained_v5":
        flexible_ev_baseline = (
            float(
                config.raw["flexible_load"]["ev_v1g"][
                    "shiftable_energy_fraction"
                ]
            )
            * baseline_components["ev"]
        )
        ev_mobility_charge_deviation = np.abs(
            ev_mobility_charge - flexible_ev_baseline
        )
    else:
        ev_mobility_charge_deviation = zero_load.copy()
    ev_mobility_v1g_relocated = _value(
        variables.get("ev_mobility_v1g_relocated", zero_load)
    )
    flexible_service_capacity = _value(
        variables.get("flexible_service_capacity", np.zeros((p_count, 4)))
    )
    firm_flexible_capacity_credit = _value(
        variables.get(
            "firm_flexible_capacity_credit", np.zeros((p_count, 4))
        )
    )
    firm_flexible_capacity_credit_upper = _value(
        variables.get(
            "firm_flexible_capacity_credit_upper", np.zeros((p_count, 4))
        )
    )
    ev_grid_charge_power_ub = _value(
        variables.get("ev_grid_charge_power_ub", baseline_components["ev"])
    )
    v2g_charge = _value(variables.get("ev_v2g_charge", zero_load))
    v2g_discharge = _value(variables.get("ev_v2g_discharge", zero_load))
    v2g_soc = _value(variables.get("ev_v2g_soc", zero_load))

    vre_generation = _value(variables["vre_generation"])
    vre_available = _value(variables["vre_available"])
    wave_generation = _value(
        variables.get("wave_generation", np.zeros((p_count, hours)))
    )
    if data.wave is not None:
        wave_capacity = _value(variables["wave_capacity"])
        wave_available = reconstruct_wave_availability(
            config, data.wave, wave_capacity, provinces, hours
        )
    else:
        wave_capacity = np.asarray([], dtype=float)
        wave_available = np.zeros((p_count, hours), dtype=float)
    thermal_gross = _value(variables["thermal_gross_generation"])
    thermal_net = _value(variables["actual_thermal_generation"])
    online = _value(variables["online"])
    startup = _value(variables["startup"])
    shutdown = _value(variables["shutdown"])
    ramp_magnitude = _value(variables["ramp_magnitude"])
    ror_generation = _value(variables["ror_generation"])
    ror_available = _value(variables["ror_available"])
    hydro_aggregate_generation = _value(
        variables["hydro_aggregate_generation"]
    )
    hydro_aggregate_available = np.asarray(
        artifacts.index["hydro_aggregate_available_gw"], dtype=float
    )
    hydro_aggregate_power_upper = np.asarray(
        artifacts.index["hydro_aggregate_power_upper_gw"], dtype=float
    )
    hydro_aggregate_month_slices = artifacts.index[
        "hydro_aggregate_month_slices"
    ]
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
    dac_capacity = _value(variables["dac_capacity"])

    generation_total = (
        vre_generation.sum(axis=1)
        + wave_generation
        + thermal_net.sum(axis=1)
        + ror_generation
        + reservoir_by_province
        + hydro_aggregate_generation
        + storage_discharge.sum(axis=1)
        - storage_charge.sum(axis=1)
        + network_injection
    )
    balance_residual = generation_total - load - dac_load[:, None]
    component_input_closure = baseline_load - sum(baseline_components.values())
    component_effective_closure = load - (
        sum(actual_components.values()) + v2g_charge - v2g_discharge
    )
    day_slices = artifacts.index["flexible_load_day_slices"]
    daily_energy_residuals = {
        component: np.asarray(
            [
                (
                    actual_components[component][:, day].sum(axis=1)
                    - baseline_components[component][:, day].sum(axis=1)
                )
                for day in day_slices
            ]
        )
        for component in ("heating", "cooling", "ev")
    }
    thermal_state_formulation = flexible_formulation in {
        "state_envelope_v2",
        "comfort_envelope_v3",
    }
    thermal_state_transition_max = {"heating": 0.0, "cooling": 0.0}
    thermal_state_terminal_max = {"heating": 0.0, "cooling": 0.0}
    thermal_daily_energy_change_min = {"heating": 0.0, "cooling": 0.0}
    ev_backlog_transition_max = 0.0
    ev_backlog_terminal_max = 0.0
    if (
        bool(config.raw["features"]["flexible_load"])
        and thermal_state_formulation
    ):
        thermal_arrays = {
            "heating": (heating_state, heating_up, heating_down),
            "cooling": (cooling_state, cooling_up, cooling_down),
        }
        for component, (state, charge, discharge) in thermal_arrays.items():
            component_config = config.raw["flexible_load"][component]
            retention = float(component_config["retention_per_hour"])
            eta_c = float(component_config["charge_efficiency"])
            eta_d = float(component_config["discharge_efficiency"])
            transition_residuals = []
            terminal_residuals = []
            energy_changes = []
            for day in day_slices:
                start, stop = int(day.start), int(day.stop)
                transition_residuals.append(
                    state[:, start]
                    - eta_c * charge[:, start]
                    + discharge[:, start] / eta_d
                )
                if stop - start > 1:
                    transition_residuals.append(
                        state[:, start + 1:stop]
                        - retention * state[:, start:stop - 1]
                        - eta_c * charge[:, start + 1:stop]
                        + discharge[:, start + 1:stop] / eta_d
                    )
                terminal_residuals.append(state[:, stop - 1])
                energy_changes.append(
                    actual_components[component][:, day].sum(axis=1)
                    - baseline_components[component][:, day].sum(axis=1)
                )
            thermal_state_transition_max[component] = max(
                float(np.abs(values).max()) for values in transition_residuals
            )
            thermal_state_terminal_max[component] = max(
                float(np.abs(values).max()) for values in terminal_residuals
            )
            thermal_daily_energy_change_min[component] = min(
                float(values.min()) for values in energy_changes
            )

        backlog_transition_residuals = []
        backlog_terminal_residuals = []
        for day in day_slices:
            start, stop = int(day.start), int(day.stop)
            backlog_transition_residuals.append(
                ev_backlog[:, start] - ev_down[:, start] + ev_up[:, start]
            )
            if stop - start > 1:
                backlog_transition_residuals.append(
                    ev_backlog[:, start + 1:stop]
                    - ev_backlog[:, start:stop - 1]
                    - ev_down[:, start + 1:stop]
                    + ev_up[:, start + 1:stop]
                )
            backlog_terminal_residuals.append(ev_backlog[:, stop - 1])
        ev_backlog_transition_max = max(
            float(np.abs(values).max())
            for values in backlog_transition_residuals
        )
        ev_backlog_terminal_max = max(
            float(np.abs(values).max())
            for values in backlog_terminal_residuals
        )
    v4_formulation = flexible_formulation == "service_constrained_v4"
    v5_formulation = (
        flexible_formulation == "integrated_service_constrained_v5"
    )
    service_contract_formulation = v4_formulation or v5_formulation
    v4_thermal_transition_max = {"heating": 0.0, "cooling": 0.0}
    v4_thermal_periodic_max = {"heating": 0.0, "cooling": 0.0}
    v4_thermal_positive_bound_violation = {"heating": 0.0, "cooling": 0.0}
    v4_thermal_negative_bound_violation = {"heating": 0.0, "cooling": 0.0}
    v4_thermal_debt_violation = {"heating": 0.0, "cooling": 0.0}
    v4_ev_transition_max = 0.0
    v4_ev_departure_violation = 0.0
    v4_ev_soc_upper_violation = 0.0
    v4_ev_charge_power_violation = 0.0
    v4_ev_discharge_power_violation = 0.0
    if service_contract_formulation:
        if data.flexible_load_v4 is None:
            raise ValueError("V4 solution export requires validated V4 input data")
        v4 = data.flexible_load_v4
        capacity_index = {"heating": 0, "cooling": 1, "ev_v1g": 2, "ev_v2g": 3}
        for component, state, charge, discharge, debt in (
            ("heating", heating_state, heating_up, heating_down, heating_comfort_debt),
            ("cooling", cooling_state, cooling_up, cooling_down, cooling_comfort_debt),
        ):
            parameters = v4.thermal_parameters[component]
            retention = parameters["retention_per_hour"][:, None]
            eta_c = parameters["charge_efficiency"][:, None]
            eta_d = parameters["discharge_efficiency"][:, None]
            periodic = (
                state[:, 0]
                - retention[:, 0] * state[:, -1]
                - eta_c[:, 0] * charge[:, 0]
                + discharge[:, 0] / eta_d[:, 0]
            )
            transitions = [periodic]
            if hours > 1:
                transitions.append(
                    state[:, 1:]
                    - retention * state[:, :-1]
                    - eta_c * charge[:, 1:]
                    + discharge[:, 1:] / eta_d
                )
            k = flexible_service_capacity[:, capacity_index[component]][:, None]
            positive = parameters["positive_state_duration_hours"][:, None] * k
            negative = parameters["negative_state_duration_hours"][:, None] * k
            v4_thermal_transition_max[component] = max(
                float(np.abs(values).max()) for values in transitions
            )
            v4_thermal_periodic_max[component] = float(np.abs(periodic).max())
            v4_thermal_positive_bound_violation[component] = float(
                np.maximum(state - positive, 0.0).max()
            )
            v4_thermal_negative_bound_violation[component] = float(
                np.maximum(-negative - state, 0.0).max()
            )
            v4_thermal_debt_violation[component] = float(
                np.maximum(-state - debt, 0.0).max()
            )
        ev_settings = config.raw["flexible_load"]["ev_v2g"]
        eta_c = float(ev_settings["charge_efficiency"])
        eta_d = float(ev_settings["discharge_efficiency"])
        retention = 1.0 - float(ev_settings["self_discharge_fraction_per_hour"])
        withdrawal = v4.ev_mobility["driving_energy_withdrawal_gwh"][
            :, selected_hours
        ]
        periodic = (
            ev_mobility_soc[:, 0]
            - retention * ev_mobility_soc[:, -1]
            - eta_c * ev_mobility_charge[:, 0]
            + ev_mobility_discharge[:, 0] / eta_d
            + withdrawal[:, 0]
        )
        transitions = [periodic]
        if hours > 1:
            transitions.append(
                ev_mobility_soc[:, 1:]
                - retention * ev_mobility_soc[:, :-1]
                - eta_c * ev_mobility_charge[:, 1:]
                + ev_mobility_discharge[:, 1:] / eta_d
                + withdrawal[:, 1:]
            )
        v4_ev_transition_max = max(float(np.abs(values).max()) for values in transitions)
        v4_ev_departure_violation = float(
            np.maximum(
                v4.ev_mobility["minimum_departure_energy_gwh"][
                    :, selected_hours
                ]
                - ev_mobility_soc,
                0.0,
            ).max()
        )
        v4_ev_soc_upper_violation = float(
            np.maximum(
                ev_mobility_soc
                - v4.ev_availability["fleet_energy_capacity_gwh"][
                    :, selected_hours
                ],
                0.0,
            ).max()
        )
        v4_ev_charge_power_violation = float(
            np.maximum(
                ev_mobility_charge
                - v4.ev_availability["available_charge_power_gw"][
                    :, selected_hours
                ],
                0.0,
            ).max()
        )
        v4_ev_discharge_power_violation = float(
            np.maximum(
                ev_mobility_discharge
                - v4.ev_availability["available_discharge_power_gw"][
                    :, selected_hours
                ],
                0.0,
            ).max()
        )
    v2g_transition_max = 0.0
    v2g_terminal_max = 0.0
    if (not service_contract_formulation) and bool(config.raw["features"]["flexible_load"]) and bool(
        config.raw["flexible_load"]["ev_v2g"]["enabled"]
    ):
        v2g_config = config.raw["flexible_load"]["ev_v2g"]
        eta_c = float(v2g_config["charge_efficiency"])
        eta_d = float(v2g_config["discharge_efficiency"])
        retention = 1.0 - float(v2g_config["self_discharge_fraction_per_hour"])
        transition_residuals = []
        terminal_residuals = []
        for day in day_slices:
            start, stop = int(day.start), int(day.stop)
            if flexible_formulation == "comfort_envelope_v3":
                transition_residuals.append(
                    v2g_soc[:, start]
                    - eta_c * v2g_charge[:, start]
                    + v2g_discharge[:, start] / eta_d
                )
                terminal_residuals.append(v2g_soc[:, stop - 1])
            else:
                transition_residuals.append(
                    v2g_soc[:, start]
                    - retention * v2g_soc[:, stop - 1]
                    - eta_c * v2g_charge[:, start]
                    + v2g_discharge[:, start] / eta_d
                )
            if stop - start > 1:
                transition_residuals.append(
                    v2g_soc[:, start + 1:stop]
                    - retention * v2g_soc[:, start:stop - 1]
                    - eta_c * v2g_charge[:, start + 1:stop]
                    + v2g_discharge[:, start + 1:stop] / eta_d
                )
        v2g_transition_max = max(
            float(np.abs(values).max()) for values in transition_residuals
        )
        if terminal_residuals:
            v2g_terminal_max = max(
                float(np.abs(values).max()) for values in terminal_residuals
            )

    thermal_up = _value(variables["thermal_reserve_up"])
    thermal_down = _value(variables["thermal_reserve_down"])
    vre_up = _value(variables["vre_reserve_up"])
    # monolithic.py exports station and provincial-aggregate hydro reserve-up
    # as one total array.  Adding the aggregate component again below would
    # make the QC margin falsely optimistic in aggregate-flex sensitivities.
    hydro_up_total = _value(variables["hydro_reserve_up"])
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
    if data.wave is not None:
        wave_requirement = (
            float(config.raw["wave_energy"]["reserve_requirement_fraction"])
            * wave_generation
        )
        up_requirement += wave_requirement
        down_requirement += wave_requirement
    aggregate_down_credit = float(
        config.raw["hydro"]["provincial_aggregate_down_reserve_credit"]
    )
    hydro_aggregate_down = (
        aggregate_down_credit * hydro_aggregate_generation
    )
    up_margin = thermal_up + vre_up + hydro_up_total + storage_up - up_requirement
    down_margin = (
        thermal_down + ror_generation + reservoir_by_province
        + hydro_aggregate_down + storage_down
        - down_requirement
    )

    dates = (
        data.load[["hour_index", "datetime_bj"]]
        .drop_duplicates("hour_index")
        .sort_values("hour_index")
        .iloc[selected_hours]
        .copy()
    )
    if len(dates) != hours:
        raise ValueError(f"Time index rows={len(dates)}; expected {hours}")
    dates["datetime_bj"] = pd.to_datetime(dates.datetime_bj)
    dates = dates.rename(columns={"hour_index": "model_hour_index"})
    dates.insert(0, "hour_index", hour_index)
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
    minimum_inertia_seconds = resolve_minimum_system_inertia_seconds(
        config.raw["security"]
    )
    inertia_required = minimum_inertia_seconds * load
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
        if data.wave is not None:
            rows = data.wave.sites.province_code.eq(province_code).to_numpy()
            credited_capacity[p] += (
                float(config.raw["wave_energy"]["capacity_credit"])
                * wave_capacity[rows].sum()
            )
    capacity_margin_load_basis = str(
        config.raw["security"]["capacity_margin_load_basis"]
    )
    baseline_peak_load = data.load_gw.max(axis=1)
    effective_peak_load = load.max(axis=1)
    if capacity_margin_load_basis == "baseline_peak_v1":
        selected_peak_load = baseline_peak_load
        adequacy_available_capacity = credited_capacity
    elif capacity_margin_load_basis == "effective_peak_endogenous_v1":
        selected_peak_load = effective_peak_load
        adequacy_available_capacity = credited_capacity
    elif capacity_margin_load_basis == "firm_flexibility_derated_v1":
        selected_peak_load = baseline_peak_load
        adequacy_available_capacity = (
            credited_capacity + firm_flexible_capacity_credit.sum(axis=1)
        )
    else:
        raise ValueError(
            f"Unsupported capacity-margin load basis: {capacity_margin_load_basis}"
        )
    capacity_margin_required = (
        1.0 + float(config.raw["security"]["capacity_margin_fraction"])
    ) * selected_peak_load
    capacity_margin = adequacy_available_capacity - capacity_margin_required

    pmin = ruc_table.pmin_fraction.to_numpy(dtype=float)
    pmax = ruc_table.pmax_fraction.to_numpy(dtype=float)
    ruc_transition_residual = (
        online - np.roll(online, 1, axis=2) - startup + shutdown
    )
    storage_overlap = np.minimum(storage_charge, storage_discharge)
    startup_shutdown_overlap = np.minimum(startup, shutdown)
    heating_overlap = np.minimum(heating_up, heating_down)
    cooling_overlap = np.minimum(cooling_up, cooling_down)
    ev_grid_charge_for_overlap = (
        ev_mobility_charge
        if service_contract_formulation
        else v2g_charge
    )
    ev_v2g_overlap = np.minimum(
        ev_grid_charge_for_overlap,
        v2g_discharge,
    )

    storage_table = data.storage.set_index("technology").reindex(STORAGE_TECHS)
    eta_c = storage_table.charge_efficiency.to_numpy(dtype=float)
    eta_d = storage_table.discharge_efficiency.to_numpy(dtype=float)
    storage_energy_capacity = (
        storage_capacity
        * storage_table.duration_h.to_numpy(dtype=float)[None, :]
    )
    if artifacts.index["phs_energy_capacity_mode"] == (
        "independent_power_energy_v1"
    ):
        storage_energy_capacity[:, artifacts.index["storage_index"]["phs"]] = (
            _value(variables["phs_energy_capacity"])
        )
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
    routed_release_loss_m3s = np.zeros(hours, dtype=float)
    for source_rows, target_rows, target_weights, lag, transfer_fraction in zip(
        artifacts.index.get("cascade_edge_source_local_rows", []),
        artifacts.index.get("cascade_edge_target_local_rows", []),
        artifacts.index.get("cascade_edge_target_weights", []),
        artifacts.index.get("cascade_edge_lag_h", []),
        artifacts.index.get("cascade_edge_transfer_fraction", []),
    ):
        source_rows = np.asarray(source_rows, dtype=int)
        target_rows = np.asarray(target_rows, dtype=int)
        target_weights = np.asarray(target_weights, dtype=float)
        release = (
            reservoir_turbine_flow[source_rows, :].sum(axis=0)
            + reservoir_spill_flow[source_rows, :].sum(axis=0)
        )
        shifted = np.roll(release, int(lag) % hours)
        transfer_fraction = np.asarray(transfer_fraction, dtype=float)
        routed_release_loss_m3s += shifted * (1.0 - transfer_fraction)
        shifted = shifted * transfer_fraction
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
    cascade_reconciliation_audit = dict(
        artifacts.index.get("cascade_reconciliation_audit", {})
    )
    cascade_reconciliation_audit[
        "actual_routed_release_adjustment_volume_million_m3"
    ] = float(routed_release_loss_m3s.sum() * 3600.0 / 1.0e6)

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
    wave_violation = wave_generation - wave_available
    hydro_aggregate_violation = (
        hydro_aggregate_generation - hydro_aggregate_power_upper
    )
    hydro_aggregate_monthly_energy_violation = np.asarray(
        [
            (
                hydro_aggregate_generation[:, month_hours].sum(axis=1)
                - hydro_aggregate_available[:, month_hours].sum(axis=1)
            )
            for month_hours in hydro_aggregate_month_slices
        ],
        dtype=float,
    )
    annual_emissions = float(_value(variables["annual_emissions"]).sum())
    dac_removed = float(_value(variables["dac_capture"]).sum())
    net_emissions = annual_emissions - dac_removed
    annual_flow_scaling_factor = float(
        artifacts.index["annual_flow_scaling_factor"]
    )
    annual_carbon_limit = float(
        artifacts.index["annual_carbon_limit_mtco2_per_year"]
    )
    carbon_limit = float(
        artifacts.index["selected_horizon_carbon_limit_mtco2"]
    )
    annual_biomass = _value(variables["annual_biomass"]).sum(axis=0)
    annual_biomass_limit = np.asarray(
        artifacts.index["annual_biomass_limit_pj_per_year"],
        dtype=float,
    )
    biomass_limit = np.asarray(
        artifacts.index["selected_horizon_biomass_limit_pj"],
        dtype=float,
    )
    captured = _value(variables["annual_captured"]).sum(axis=0)
    dac_by_province = _value(variables["dac_capture"]).sum(axis=1)
    co2_ship = _value(variables["co2_ship"])
    co2_source_residual = co2_ship.sum(axis=1) - captured - dac_by_province
    injection_field = str(config.raw["ccs_injection_field"])
    sinks = data.vre_points.loc[data.vre_points[injection_field].gt(0)]
    selected_horizon_sink_injection_upper = np.asarray(
        artifacts.index[
            "selected_horizon_co2_sink_injection_upper_mtco2"
        ],
        dtype=float,
    )
    co2_sink_violation = (
        co2_ship.sum(axis=0) - selected_horizon_sink_injection_upper
    )
    dac_selected_horizon_capacity_violation = (
        _value(variables["dac_capture"])
        - annual_flow_scaling_factor * dac_capacity
    )

    thermal_energy = thermal_gross.sum(axis=2)
    emission_table = data.emissions.set_index("technology")
    coal_factor = float(
        emission_table.loc["coal", "emission_factor_mtco2_per_gwh"]
    )
    gas_factor = float(
        emission_table.loc["gas", "emission_factor_mtco2_per_gwh"]
    )
    capture_fraction = float(emission_table.loc["coal", "ccs_capture_fraction"])
    beccs_carbon = resolve_beccs_carbon_factors(emission_table)
    fossil_unabated = np.zeros(p_count, dtype=float)
    fossil_captured = np.zeros(p_count, dtype=float)
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
            fossil_captured += base_factor * capture_fraction * generation
        elif technology == "bioccs":
            emissions_before_dac_by_province += beccs_carbon.net_emissions * generation
        else:
            emissions_before_dac_by_province += base_factor * generation
    beccs_generation = thermal_energy[:, bioccs_k]
    beccs_gross_biogenic = beccs_carbon.gross_biogenic * beccs_generation
    beccs_captured_biogenic = beccs_carbon.captured_biogenic * beccs_generation
    beccs_stored = beccs_carbon.stored * beccs_generation
    beccs_uncaptured_biogenic = (
        beccs_carbon.uncaptured_biogenic * beccs_generation
    )
    beccs_lifecycle_emissions = (
        beccs_carbon.lifecycle_emissions * beccs_generation
    )
    beccs_net_removal = beccs_carbon.net_removal * beccs_generation
    beccs_capture_residual = (
        beccs_captured_biogenic
        - beccs_carbon.capture_fraction * beccs_gross_biogenic
    )
    beccs_storage_residual = beccs_stored - beccs_captured_biogenic
    beccs_net_residual = (
        beccs_lifecycle_emissions
        + beccs_uncaptured_biogenic
        - beccs_gross_biogenic
        + beccs_net_removal
    )
    captured_reconstruction_residual = (
        captured - fossil_captured - beccs_stored
    )
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
    mga_metadata = artifacts.index.get("mga")
    if mga_metadata is None:
        objective_value = float(artifacts.model.ObjVal)
        solver_objective_value = objective_value
        mga_result = None
    else:
        objective_value = float(
            artifacts.index["mga_primary_cost_expression"].getValue()
        )
        solver_objective_value = float(artifacts.model.ObjVal)
        cost_cap = float(mga_metadata["cost_cap_million_cny"])
        mga_result = {
            **mga_metadata,
            "primary_cost_value_million_cny": objective_value,
            "cost_cap_slack_million_cny": cost_cap - objective_value,
            "secondary_objective_value_gw": solver_objective_value,
        }
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
    directionality_assessment = assess_interprovincial_bidirectionality(
        flow_forward=flow_forward,
        flow_reverse=flow_reverse,
        line_capacity_gw=line_capacity,
        line_efficiency=np.asarray(
            artifacts.index["line_efficiency"], dtype=float
        ),
        system_load_gwh=float(load.sum()),
        optimization_hours=hours,
        configured_hours=config.hours,
        tolerance_gw=flow_direction_tolerance_gw,
        warning_contract=config.raw["network"][
            "diagnostic_bidirectional_flow_warning"
        ],
    )
    dc_edge_mask = (
        data.lines.preset_technology.astype(str).str.upper().eq("DC").to_numpy()
    )
    maximum_dc_reverse_flow = float(
        flow_reverse[dc_edge_mask, :].max() if dc_edge_mask.any() else 0.0
    )
    v5_nested_v2g_contract_violation = (
        float(
            np.maximum(
                flexible_service_capacity[:, 3]
                - flexible_service_capacity[:, 2],
                0.0,
            ).max()
        )
        if v5_formulation
        else 0.0
    )
    v5_national_v2g_cap_violation = 0.0
    v5_shared_connection_power_violation = 0.0
    if v5_formulation:
        national_v2g_cap = float(
            config.raw["flexible_load"]["ev_v2g"][
                "national_contracted_power_cap_gw_by_planning_year"
            ][str(config.planning_year)]
        )
        v5_national_v2g_cap_violation = max(
            float(flexible_service_capacity[:, 3].sum()) - national_v2g_cap,
            0.0,
        )
        if data.flexible_load_v4 is None:
            raise ValueError("V5 shared-connection QC requires V5 inputs")
        connected = data.flexible_load_v4.ev_availability[
            "connected_vehicle_fraction"
        ][:, selected_hours]
        shared_connection_power = (
            connected * flexible_service_capacity[:, 2, None]
        )
        v5_shared_connection_power_violation = float(
            np.maximum(
                ev_mobility_charge
                + ev_mobility_discharge
                - shared_connection_power,
                0.0,
            ).max()
        )
    v5_firm_credit_bound_violation = (
        float(
            np.maximum(
                firm_flexible_capacity_credit
                - firm_flexible_capacity_credit_upper,
                0.0,
            ).max()
        )
        if v5_formulation
        else 0.0
    )
    (
        ev_v1g_daily_energy_residual,
        ev_v1g_daily_energy_residual_applicability,
    ) = _ev_v1g_daily_energy_residual_for_qc(
        daily_energy_residuals["ev"],
        service_contract_formulation=service_contract_formulation,
    )
    qc = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "flexible_load_structural_audit": artifacts.index.get(
            "flexible_load_structural_audit", {}
        ),
        "optimization_hours": hours,
        "optimization_start_hour": hour_start,
        "optimization_stop_hour_exclusive": hour_stop,
        "maximum_power_balance_residual_gw": float(np.abs(balance_residual).max()),
        "maximum_load_component_input_closure_error_gw": float(
            np.abs(component_input_closure).max()
        ),
        "maximum_effective_load_reconstruction_error_gw": float(
            np.abs(component_effective_closure).max()
        ),
        "minimum_effective_load_gw": float(load.min()),
        "maximum_heating_daily_energy_residual_gwh": float(
            np.abs(daily_energy_residuals["heating"]).max()
        ),
        "maximum_cooling_daily_energy_residual_gwh": float(
            np.abs(daily_energy_residuals["cooling"]).max()
        ),
        "maximum_ev_v1g_daily_energy_residual_gwh": (
            ev_v1g_daily_energy_residual
        ),
        "ev_v1g_daily_energy_residual_applicability": (
            ev_v1g_daily_energy_residual_applicability
        ),
        "flexible_load_formulation": flexible_formulation,
        "maximum_heating_state_transition_residual_gwh": (
            thermal_state_transition_max["heating"]
        ),
        "maximum_cooling_state_transition_residual_gwh": (
            thermal_state_transition_max["cooling"]
        ),
        "maximum_heating_daily_terminal_state_gwh": (
            thermal_state_terminal_max["heating"]
        ),
        "maximum_cooling_daily_terminal_state_gwh": (
            thermal_state_terminal_max["cooling"]
        ),
        "minimum_heating_daily_net_energy_change_gwh": (
            thermal_daily_energy_change_min["heating"]
        ),
        "minimum_cooling_daily_net_energy_change_gwh": (
            thermal_daily_energy_change_min["cooling"]
        ),
        "maximum_ev_v1g_backlog_transition_residual_gwh": (
            ev_backlog_transition_max
        ),
        "maximum_ev_v1g_daily_terminal_backlog_gwh": (
            ev_backlog_terminal_max
        ),
        "maximum_ev_v2g_transition_residual_gwh": v2g_transition_max,
        "maximum_ev_v2g_daily_terminal_state_gwh": v2g_terminal_max,
        "maximum_v4_heating_state_transition_residual_gwh": (
            v4_thermal_transition_max["heating"]
        ),
        "maximum_v4_cooling_state_transition_residual_gwh": (
            v4_thermal_transition_max["cooling"]
        ),
        "maximum_v4_heating_periodic_boundary_residual_gwh": (
            v4_thermal_periodic_max["heating"]
        ),
        "maximum_v4_cooling_periodic_boundary_residual_gwh": (
            v4_thermal_periodic_max["cooling"]
        ),
        "maximum_v4_heating_positive_state_bound_violation_gwh": (
            v4_thermal_positive_bound_violation["heating"]
        ),
        "maximum_v4_cooling_positive_state_bound_violation_gwh": (
            v4_thermal_positive_bound_violation["cooling"]
        ),
        "maximum_v4_heating_negative_state_bound_violation_gwh": (
            v4_thermal_negative_bound_violation["heating"]
        ),
        "maximum_v4_cooling_negative_state_bound_violation_gwh": (
            v4_thermal_negative_bound_violation["cooling"]
        ),
        "maximum_v4_heating_comfort_debt_violation_gwh": (
            v4_thermal_debt_violation["heating"]
        ),
        "maximum_v4_cooling_comfort_debt_violation_gwh": (
            v4_thermal_debt_violation["cooling"]
        ),
        "maximum_v4_ev_soc_transition_residual_gwh": v4_ev_transition_max,
        "maximum_v4_ev_departure_soc_violation_gwh": v4_ev_departure_violation,
        "maximum_v4_ev_soc_upper_violation_gwh": v4_ev_soc_upper_violation,
        "maximum_v4_ev_charge_power_violation_gw": v4_ev_charge_power_violation,
        "maximum_v4_ev_discharge_power_violation_gw": v4_ev_discharge_power_violation,
        "maximum_v5_nested_v2g_contract_violation_gw": (
            v5_nested_v2g_contract_violation
        ),
        "maximum_v5_national_v2g_cap_violation_gw": (
            v5_national_v2g_cap_violation
        ),
        "maximum_v5_shared_connection_power_violation_gw": (
            v5_shared_connection_power_violation
        ),
        "maximum_v5_firm_capacity_credit_bound_violation_gw": (
            v5_firm_credit_bound_violation
        ),
        "total_v5_firm_capacity_credit_gw": float(
            firm_flexible_capacity_credit.sum()
        ),
        "maximum_ev_combined_grid_charging_power_violation_gw": float(
            np.maximum(
                actual_components["ev"]
                + v2g_charge
                - ev_grid_charge_power_ub,
                0.0,
            ).max()
        ),
        "flexible_load_enabled": bool(config.raw["features"]["flexible_load"]),
        "heating_simultaneous_up_down_province_hours": int(
            ((heating_up > flow_direction_tolerance_gw)
             & (heating_down > flow_direction_tolerance_gw)).sum()
        ),
        "maximum_heating_up_down_overlap_gw": float(
            heating_overlap.max()
        ),
        "total_heating_up_down_overlap_gwh": float(
            heating_overlap.sum()
        ),
        "cooling_simultaneous_up_down_province_hours": int(
            ((cooling_up > flow_direction_tolerance_gw)
             & (cooling_down > flow_direction_tolerance_gw)).sum()
        ),
        "maximum_cooling_up_down_overlap_gw": float(
            cooling_overlap.max()
        ),
        "total_cooling_up_down_overlap_gwh": float(
            cooling_overlap.sum()
        ),
        "ev_v1g_simultaneous_up_down_province_hours": int(
            ((ev_up > flow_direction_tolerance_gw)
             & (ev_down > flow_direction_tolerance_gw)).sum()
        ),
        "ev_v2g_simultaneous_charge_discharge_province_hours": int(
            (
                (
                    (
                        ev_grid_charge_for_overlap
                    )
                    > flow_direction_tolerance_gw
                )
                & (v2g_discharge > flow_direction_tolerance_gw)
            ).sum()
        ),
        "maximum_ev_v2g_charge_discharge_overlap_gw": float(
            ev_v2g_overlap.max()
        ),
        "total_ev_v2g_charge_discharge_overlap_gwh": float(
            ev_v2g_overlap.sum()
        ),
        "minimum_up_reserve_margin_gw": float(up_margin.min()),
        "minimum_down_reserve_margin_gw": float(down_margin.min()),
        "minimum_inertia_margin_gw_s": float(
            (inertia_provided - inertia_required).min()
        ),
        "minimum_system_inertia_seconds": minimum_inertia_seconds,
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
        "maximum_wave_availability_violation_gw": float(
            np.maximum(wave_violation, 0.0).max()
        ),
        "maximum_hydro_aggregate_availability_violation_gw": float(
            np.maximum(hydro_aggregate_violation, 0.0).max()
        ),
        "maximum_hydro_aggregate_monthly_energy_budget_violation_gwh": float(
            np.maximum(
                hydro_aggregate_monthly_energy_violation,
                0.0,
            ).max()
            if hydro_aggregate_monthly_energy_violation.size
            else 0.0
        ),
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
                - storage_energy_capacity[:, :, None],
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
        "core_cascade_isolated_single_station_nodes_removed": int(
            len(artifacts.index.get("cascade_isolated_node_ids", []))
        ),
        "cascade_raw_negative_local_inflow_node_hours": int(
            cascade_reconciliation_audit.get("raw_negative_node_hours", 0)
        ),
        "cascade_raw_clip_equivalent_volume_million_m3": float(
            cascade_reconciliation_audit.get(
                "raw_clip_equivalent_volume_million_m3", 0.0
            )
        ),
        "cascade_adjusted_transfer_volume_million_m3": float(
            cascade_reconciliation_audit.get(
                "adjusted_transfer_volume_million_m3", 0.0
            )
        ),
        "cascade_actual_routed_release_adjustment_volume_million_m3": float(
            cascade_reconciliation_audit[
                "actual_routed_release_adjustment_volume_million_m3"
            ]
        ),
        "maximum_cascade_reconciliation_residual_m3s": float(
            cascade_reconciliation_audit.get(
                "maximum_reconciliation_residual_m3s", 0.0
            )
        ),
        "annual_gross_emissions_mtco2": annual_emissions,
        "annual_emissions_before_dac_mtco2": annual_emissions,
        "annual_dac_removed_mtco2": dac_removed,
        "annual_net_emissions_mtco2": net_emissions,
        "annual_flow_scaling_factor": annual_flow_scaling_factor,
        "annual_carbon_limit_mtco2_per_year": annual_carbon_limit,
        "selected_horizon_carbon_limit_mtco2": carbon_limit,
        "carbon_limit_mtco2": carbon_limit,
        "carbon_limit_margin_mtco2": carbon_limit - net_emissions,
        "maximum_dac_selected_horizon_capacity_violation_mtco2": float(
            np.maximum(
                dac_selected_horizon_capacity_violation,
                0.0,
            ).max()
        ),
        "maximum_biomass_limit_violation_pj": float(
            np.maximum(annual_biomass - biomass_limit, 0.0).max()
        ),
        "maximum_co2_source_balance_residual_mt": float(np.abs(co2_source_residual).max()),
        "maximum_co2_sink_capacity_violation_mt": float(np.maximum(co2_sink_violation, 0.0).max()),
        "maximum_beccs_capture_balance_residual_mtco2": float(
            np.abs(beccs_capture_residual).max()
        ),
        "maximum_beccs_storage_balance_residual_mtco2": float(
            np.abs(beccs_storage_residual).max()
        ),
        "maximum_beccs_net_carbon_balance_residual_mtco2": float(
            np.abs(beccs_net_residual).max()
        ),
        "maximum_captured_co2_reconstruction_residual_mtco2": float(
            np.abs(captured_reconstruction_residual).max()
        ),
        "objective_value_million_cny": objective_value,
        "objective_component_residual_million_cny": objective_component_residual,
        "solver_objective_value": solver_objective_value,
        "mga": mga_result,
        "total_vre_curtailment_gwh": float((vre_available - vre_generation).sum()),
        "wave_energy_enabled": data.wave is not None,
        "total_wave_generation_gwh": float(wave_generation.sum()),
        "total_wave_curtailment_gwh": float(
            (wave_available - wave_generation).sum()
        ),
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
        "interprovincial_directionality_assessment": directionality_assessment,
        "strict_unidirectional_interprovincial_flow": directionality_assessment[
            "strict_pass"
        ],
        "diagnostic_bidirectional_flow_warning_applied": directionality_assessment[
            "warning_applied"
        ],
        "dc_fixed_direction_edge_count": int(dc_edge_mask.sum()),
        "maximum_dc_reverse_flow_gw": maximum_dc_reverse_flow,
    }
    hard_checks = {
        "power_balance": qc["maximum_power_balance_residual_gw"] <= tolerance,
        "load_component_input_closure": qc[
            "maximum_load_component_input_closure_error_gw"
        ] <= tolerance,
        "effective_load_reconstruction": qc[
            "maximum_effective_load_reconstruction_error_gw"
        ] <= tolerance,
        "effective_load_nonnegative": qc["minimum_effective_load_gw"] >= -tolerance,
        "heating_service_accounting": (
            (
                qc["maximum_v4_heating_state_transition_residual_gwh"] <= tolerance
                and qc["maximum_v4_heating_periodic_boundary_residual_gwh"] <= tolerance
                and qc["maximum_v4_heating_positive_state_bound_violation_gwh"] <= tolerance
                and qc["maximum_v4_heating_negative_state_bound_violation_gwh"] <= tolerance
                and qc["maximum_v4_heating_comfort_debt_violation_gwh"] <= tolerance
            )
            if service_contract_formulation
            else (
                qc["maximum_heating_state_transition_residual_gwh"] <= tolerance
                and qc["maximum_heating_daily_terminal_state_gwh"] <= tolerance
                and qc["minimum_heating_daily_net_energy_change_gwh"] >= -tolerance
            )
            if thermal_state_formulation
            else qc["maximum_heating_daily_energy_residual_gwh"] <= tolerance
        ),
        "cooling_service_accounting": (
            (
                qc["maximum_v4_cooling_state_transition_residual_gwh"] <= tolerance
                and qc["maximum_v4_cooling_periodic_boundary_residual_gwh"] <= tolerance
                and qc["maximum_v4_cooling_positive_state_bound_violation_gwh"] <= tolerance
                and qc["maximum_v4_cooling_negative_state_bound_violation_gwh"] <= tolerance
                and qc["maximum_v4_cooling_comfort_debt_violation_gwh"] <= tolerance
            )
            if service_contract_formulation
            else (
                qc["maximum_cooling_state_transition_residual_gwh"] <= tolerance
                and qc["maximum_cooling_daily_terminal_state_gwh"] <= tolerance
                and qc["minimum_cooling_daily_net_energy_change_gwh"] >= -tolerance
            )
            if thermal_state_formulation
            else qc["maximum_cooling_daily_energy_residual_gwh"] <= tolerance
        ),
        "heating_state_transition": (
            not thermal_state_formulation
            or qc["maximum_heating_state_transition_residual_gwh"] <= tolerance
        ),
        "cooling_state_transition": (
            not thermal_state_formulation
            or qc["maximum_cooling_state_transition_residual_gwh"] <= tolerance
        ),
        "heating_daily_state_reset": (
            not thermal_state_formulation
            or qc["maximum_heating_daily_terminal_state_gwh"] <= tolerance
        ),
        "cooling_daily_state_reset": (
            not thermal_state_formulation
            or qc["maximum_cooling_daily_terminal_state_gwh"] <= tolerance
        ),
        "heating_state_loss_accounting": (
            not thermal_state_formulation
            or qc["minimum_heating_daily_net_energy_change_gwh"] >= -tolerance
        ),
        "cooling_state_loss_accounting": (
            not thermal_state_formulation
            or qc["minimum_cooling_daily_net_energy_change_gwh"] >= -tolerance
        ),
        "ev_v1g_daily_energy_conservation": qc[
            "maximum_ev_v1g_daily_energy_residual_gwh"
        ] <= tolerance if not service_contract_formulation else True,
        "ev_v1g_backlog_transition": (
            not thermal_state_formulation
            or qc["maximum_ev_v1g_backlog_transition_residual_gwh"] <= tolerance
        ),
        "ev_v1g_daily_backlog_reset": (
            not thermal_state_formulation
            or qc["maximum_ev_v1g_daily_terminal_backlog_gwh"] <= tolerance
        ),
        "ev_v2g_transition": qc["maximum_ev_v2g_transition_residual_gwh"] <= tolerance,
        "ev_v2g_daily_state_reset": (
            flexible_formulation != "comfort_envelope_v3"
            or qc["maximum_ev_v2g_daily_terminal_state_gwh"] <= tolerance
        ),
        "ev_combined_grid_charging_power": (
            flexible_formulation
            not in {
                "comfort_envelope_v3",
                "service_constrained_v4",
                "integrated_service_constrained_v5",
            }
            or qc["maximum_ev_combined_grid_charging_power_violation_gw"]
            <= tolerance
        ),
        "v4_ev_mobility_service": (
            not service_contract_formulation
            or (
                qc["maximum_v4_ev_soc_transition_residual_gwh"] <= tolerance
                and qc["maximum_v4_ev_departure_soc_violation_gwh"] <= tolerance
                and qc["maximum_v4_ev_soc_upper_violation_gwh"] <= tolerance
                and qc["maximum_v4_ev_charge_power_violation_gw"] <= tolerance
                and qc["maximum_v4_ev_discharge_power_violation_gw"] <= tolerance
            )
        ),
        "v5_v2g_contract_nesting": (
            not v5_formulation
            or qc["maximum_v5_nested_v2g_contract_violation_gw"]
            <= tolerance
        ),
        "v5_v2g_national_power_cap": (
            not v5_formulation
            or qc["maximum_v5_national_v2g_cap_violation_gw"]
            <= tolerance
        ),
        "v5_shared_bidirectional_connection_power": (
            not v5_formulation
            or qc["maximum_v5_shared_connection_power_violation_gw"]
            <= tolerance
        ),
        "v5_firm_capacity_credit_physical_bound": (
            not v5_formulation
            or qc["maximum_v5_firm_capacity_credit_bound_violation_gw"]
            <= tolerance
        ),
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
        "wave_availability": (
            qc["maximum_wave_availability_violation_gw"] <= tolerance
        ),
        "hydro_aggregate_availability": (
            qc["maximum_hydro_aggregate_availability_violation_gw"]
            <= tolerance
        ),
        "hydro_aggregate_monthly_energy_budget": (
            qc[
                "maximum_hydro_aggregate_monthly_energy_budget_violation_gwh"
            ]
            <= tolerance
        ),
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
        "unidirectional_interprovincial_flow": directionality_assessment[
            "accepted"
        ],
        "dc_fixed_direction": qc["maximum_dc_reverse_flow_gw"]
        <= flow_direction_tolerance_gw,
        "storage_transition": qc["maximum_storage_transition_residual_gwh"] <= tolerance,
        "storage_soc": qc["maximum_storage_soc_upper_violation_gwh"] <= tolerance,
        "reservoir_transition": qc["maximum_reservoir_transition_residual_m3"] <= reservoir_volume_tolerance_m3,
        "cascade_inflow_reconciliation": qc[
            "maximum_cascade_reconciliation_residual_m3s"
        ] <= tolerance,
        "reservoir_energy": qc["maximum_reservoir_energy_upper_violation_gwh"] <= tolerance,
        "reservoir_active_storage": qc["maximum_reservoir_active_storage_upper_violation_m3"] <= reservoir_volume_tolerance_m3,
        "carbon": qc["carbon_limit_margin_mtco2"] >= -tolerance,
        "dac_selected_horizon_capacity": qc[
            "maximum_dac_selected_horizon_capacity_violation_mtco2"
        ] <= tolerance,
        "biomass": qc["maximum_biomass_limit_violation_pj"] <= tolerance,
        "co2_source": qc["maximum_co2_source_balance_residual_mt"] <= tolerance,
        "co2_sink": qc["maximum_co2_sink_capacity_violation_mt"] <= tolerance,
        "beccs_capture_mass_balance": qc[
            "maximum_beccs_capture_balance_residual_mtco2"
        ] <= tolerance,
        "beccs_storage_mass_balance": qc[
            "maximum_beccs_storage_balance_residual_mtco2"
        ] <= tolerance,
        "beccs_net_carbon_balance": qc[
            "maximum_beccs_net_carbon_balance_residual_mtco2"
        ] <= tolerance,
        "captured_co2_reconstruction": qc[
            "maximum_captured_co2_reconstruction_residual_mtco2"
        ] <= tolerance,
        "objective_components": abs(objective_component_residual) <= tolerance,
    }
    if mga_result is not None:
        hard_checks["mga_primary_cost_cap"] = (
            mga_result["cost_cap_slack_million_cny"] >= -tolerance
        )
    qc["hard_checks"] = hard_checks
    qc["status"] = "PASS" if all(hard_checks.values()) else "HARD_FAIL"
    _write_json(
        cascade_reconciliation_audit,
        output_dir / "hydro_cascade_reconciliation_audit.json",
    )
    pd.DataFrame(
        artifacts.index.get("cascade_reconciliation_node_rows", [])
    ).to_csv(
        output_dir / "hydro_cascade_reconciliation_by_node.csv",
        index=False,
        encoding="utf-8-sig",
    )
    _write_json(qc, output_dir / "solution_qc.json")

    province_hour = pd.DataFrame(
        {
            "province_code": np.repeat(provinces, hours),
            "hour_index": np.tile(hour_index, p_count),
            "datetime_bj": np.tile(
                dates.datetime_bj.dt.strftime("%Y-%m-%d %H:%M:%S").to_numpy(),
                p_count,
            ),
            "baseline_load_gw": baseline_load.ravel(),
            "load_gw": load.ravel(),
            "base_residual_load_gw": actual_components["base_residual"].ravel(),
            "heating_load_gw": actual_components["heating"].ravel(),
            "cooling_load_gw": actual_components["cooling"].ravel(),
            "ev_load_gw": actual_components["ev"].ravel(),
            "ev_v2g_charge_gw": v2g_charge.ravel(),
            "ev_v2g_discharge_gw": v2g_discharge.ravel(),
            "ev_mobility_charge_gw": ev_mobility_charge.ravel(),
            "ev_mobility_discharge_gw": ev_mobility_discharge.ravel(),
            "ev_mobility_soc_gwh": ev_mobility_soc.ravel(),
            "vre_generation_gw": vre_generation.sum(axis=1).ravel(),
            "wave_generation_gw": wave_generation.ravel(),
            "thermal_net_generation_gw": thermal_net.sum(axis=1).ravel(),
            "ror_generation_gw": ror_generation.ravel(),
            "reservoir_generation_gw": reservoir_by_province.ravel(),
            "hydro_aggregate_generation_gw": (
                hydro_aggregate_generation.ravel()
            ),
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
            "up_reserve_hydro_gw": hydro_up_total.ravel(),
            "up_reserve_storage_gw": storage_up.ravel(),
            "up_reserve_margin_gw": up_margin.ravel(),
            "down_reserve_requirement_gw": down_requirement.ravel(),
            "down_reserve_thermal_gw": thermal_down.ravel(),
            "down_reserve_hydro_gw": (
                ror_generation
                + reservoir_by_province
                + hydro_aggregate_down
            ).ravel(),
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

    use_barrier_duals = bool(
        int(artifacts.model.Params.Method) == 2
        and int(artifacts.model.Params.Crossover) == 0
        and int(artifacts.model.Params.SolutionTarget) == 1
    )
    dual_attribute = "BarPi" if use_barrier_duals else "Pi"
    dual_status: dict[str, Any] = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "available": False,
        "model_class": "continuous_linear_program",
        "dual_attribute": dual_attribute,
        "solution_form": (
            "optimal_primal_dual_nonbasic"
            if use_barrier_duals
            else "basic_or_default"
        ),
        "note": (
            f"Gurobi {dual_attribute} is the derivative of the objective with "
            "respect to the constraint RHS for the accepted solution form. "
            "Equality power-balance duals are reported as energy prices; "
            "inequality scarcity values use the documented tightening sign."
        ),
    }
    try:
        handles = artifacts.index["constraint_handles"]

        def dual_value(handle: Any) -> Any:
            return getattr(handle, dual_attribute)

        power_balance_pi = np.vstack(
            [
                np.asarray(dual_value(handle), dtype=float)
                for handle in handles["strict_power_balance"]
            ]
        )
        up_reserve_pi = np.asarray(
            dual_value(handles["up_reserve"]), dtype=float
        )
        down_reserve_pi = np.asarray(
            dual_value(handles["down_reserve"]), dtype=float
        )
        inertia_pi = np.vstack(
            [
                np.asarray(dual_value(handle), dtype=float)
                for handle in handles["inertia"]
            ]
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
            float(dual_value(handles["annual_net_carbon_limit"])),
            "<=",
            "CNY_per_tCO2",
        )
        for province_code, pi in zip(
            provinces,
            np.asarray(
                dual_value(handles["annual_biomass_fuel_limit"]),
                dtype=float,
            ),
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
            pi = np.asarray(dual_value(handle), dtype=float)
            add_dual(
                "capacity_margin",
                "province_code",
                int(province_code),
                float(pi.sum()),
                ">=",
                "CNY_per_kW_credited_capacity",
            )
        for province_code, pi in zip(
            provinces,
            np.asarray(
                dual_value(handles["biomass_beccs_capacity_upper"]),
                dtype=float,
            ),
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
                float(dual_value(handle)),
                "=",
                "CNY_per_tCO2",
            )
        sink_pi = np.asarray(
            dual_value(handles["co2_sink_injection_capacity"]), dtype=float
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
            "capacity_margin_load_basis": capacity_margin_load_basis,
            "baseline_peak_load_gw": baseline_peak_load,
            "effective_peak_load_gw": effective_peak_load,
            "selected_peak_load_gw": selected_peak_load,
            "peak_load_gw": selected_peak_load,
            "capacity_margin_fraction": float(
                config.raw["security"]["capacity_margin_fraction"]
            ),
            "credited_capacity_required_gw": capacity_margin_required,
            "credited_capacity_available_gw": credited_capacity,
            "firm_flexible_capacity_credit_gw": (
                firm_flexible_capacity_credit.sum(axis=1)
            ),
            "adequacy_available_capacity_including_flex_gw": (
                adequacy_available_capacity
            ),
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
        if data.wave is not None:
            generation_rows.append(
                {
                    "province_code": int(province_code),
                    "technology": "wave",
                    "generation_gwh": float(wave_generation[p, :].sum()),
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
                {
                    "province_code": int(province_code),
                    "technology": "hydro_aggregate",
                    "generation_gwh": float(
                        hydro_aggregate_generation[p, :].sum()
                    ),
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
            "beccs_gross_biogenic_co2_mtco2": beccs_gross_biogenic,
            "beccs_captured_biogenic_co2_mtco2": beccs_captured_biogenic,
            "beccs_stored_co2_mtco2": beccs_stored,
            "beccs_uncaptured_biogenic_co2_mtco2": beccs_uncaptured_biogenic,
            "beccs_lifecycle_emissions_mtco2": beccs_lifecycle_emissions,
            "beccs_net_removal_mtco2": beccs_net_removal,
            "dac_removed_mtco2": dac_by_province,
            "net_emissions_after_dac_mtco2": (
                emissions_before_dac_by_province - dac_by_province
            ),
            "biomass_fuel_pj": biomass_by_province,
            "annual_biomass_limit_pj_per_year": annual_biomass_limit,
            "selected_horizon_biomass_limit_pj": biomass_limit,
            "annual_flow_scaling_factor": annual_flow_scaling_factor,
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
    if data.wave is not None:
        np.savez_compressed(
            output_dir / "wave_dispatch.npz",
            generation_gw=wave_generation,
            available_gw=wave_available,
            capacity_gw=wave_capacity,
            province_codes=provinces,
            grid_uids=data.wave.sites.grid_uid.to_numpy(dtype=str),
            grid_ids=data.wave.sites.grid_id.to_numpy(dtype=np.int64),
            wave_source_grid_ids=data.wave.sites.wave_source_grid_id.to_numpy(
                dtype=np.int64
            ),
            hour_index=hour_index,
        )
    np.savez_compressed(
        output_dir / "storage_dispatch.npz",
        charge_gw=storage_charge,
        discharge_gw=storage_discharge,
        soc_gwh=storage_soc,
        reserve_up_gw=storage_reserve_up_technology,
        reserve_down_gw=storage_reserve_down_technology,
        energy_capacity_gwh=storage_energy_capacity,
        province_codes=provinces,
        technologies=np.asarray(STORAGE_TECHS),
        hour_index=hour_index,
    )
    np.savez_compressed(
        output_dir / "flexible_load_dispatch.npz",
        baseline_total_load_gw=baseline_load,
        effective_total_load_gw=load,
        baseline_base_residual_gw=baseline_components["base_residual"],
        baseline_heating_gw=baseline_components["heating"],
        baseline_cooling_gw=baseline_components["cooling"],
        baseline_ev_gw=baseline_components["ev"],
        actual_base_residual_gw=actual_components["base_residual"],
        actual_heating_gw=actual_components["heating"],
        actual_cooling_gw=actual_components["cooling"],
        actual_ev_gw=actual_components["ev"],
        heating_shift_up_gw=heating_up,
        heating_shift_down_gw=heating_down,
        cooling_shift_up_gw=cooling_up,
        cooling_shift_down_gw=cooling_down,
        ev_v1g_shift_up_gw=ev_up,
        ev_v1g_shift_down_gw=ev_down,
        heating_state_gwh=heating_state,
        cooling_state_gwh=cooling_state,
        heating_comfort_debt_gwh=heating_comfort_debt,
        cooling_comfort_debt_gwh=cooling_comfort_debt,
        ev_v1g_backlog_gwh=ev_backlog,
        ev_v2g_charge_gw=v2g_charge,
        ev_v2g_discharge_gw=v2g_discharge,
        ev_v2g_soc_gwh=v2g_soc,
        ev_mobility_charge_gw=ev_mobility_charge,
        ev_mobility_discharge_gw=ev_mobility_discharge,
        ev_mobility_soc_gwh=ev_mobility_soc,
        ev_mobility_charge_deviation_gw=ev_mobility_charge_deviation,
        ev_mobility_v1g_relocated_gw=ev_mobility_v1g_relocated,
        flexible_service_capacity_gw=flexible_service_capacity,
        firm_flexible_capacity_credit_gw=firm_flexible_capacity_credit,
        firm_flexible_capacity_credit_upper_gw=(
            firm_flexible_capacity_credit_upper
        ),
        flexible_service_names=np.asarray(
            ("heating", "cooling", "ev_v1g", "ev_v2g")
        ),
        province_codes=provinces,
        hour_index=hour_index,
    )
    flexible_rows = []
    for p, province_code in enumerate(provinces):
        flexible_rows.append(
            {
                "province_code": int(province_code),
                "optimization_hours": hours,
                "result_use": (
                    "SCIENTIFIC_PRODUCTION"
                    if hours == config.hours
                    else "TEST_ONLY_TRUNCATED_HORIZON"
                ),
                "baseline_load_gwh": float(baseline_load[p].sum()),
                "effective_load_gwh": float(load[p].sum()),
                "baseline_peak_load_gw": float(baseline_load[p].max()),
                "effective_peak_load_gw": float(load[p].max()),
                "heating_shift_up_gwh": float(heating_up[p].sum()),
                "heating_shift_down_gwh": float(heating_down[p].sum()),
                "cooling_shift_up_gwh": float(cooling_up[p].sum()),
                "cooling_shift_down_gwh": float(cooling_down[p].sum()),
                "ev_v1g_shift_up_gwh": float(ev_up[p].sum()),
                "ev_v1g_shift_down_gwh": float(ev_down[p].sum()),
                "heating_state_peak_gwh": float(heating_state[p].max()),
                "cooling_state_peak_gwh": float(cooling_state[p].max()),
                "heating_state_minimum_gwh": float(heating_state[p].min()),
                "cooling_state_minimum_gwh": float(cooling_state[p].min()),
                "heating_comfort_debt_gwh_hours": float(
                    heating_comfort_debt[p].sum()
                ),
                "cooling_comfort_debt_gwh_hours": float(
                    cooling_comfort_debt[p].sum()
                ),
                "heating_net_energy_change_gwh": float(
                    actual_components["heating"][p].sum()
                    - baseline_components["heating"][p].sum()
                ),
                "cooling_net_energy_change_gwh": float(
                    actual_components["cooling"][p].sum()
                    - baseline_components["cooling"][p].sum()
                ),
                "ev_v1g_backlog_peak_gwh": float(ev_backlog[p].max()),
                "ev_v2g_charge_gwh": float(v2g_charge[p].sum()),
                "ev_v2g_discharge_gwh": float(v2g_discharge[p].sum()),
                "ev_mobility_charge_gwh": float(ev_mobility_charge[p].sum()),
                "ev_mobility_discharge_gwh": float(ev_mobility_discharge[p].sum()),
                "ev_mobility_soc_peak_gwh": float(ev_mobility_soc[p].max()),
                "ev_mobility_charge_deviation_gwh": float(
                    ev_mobility_charge_deviation[p].sum()
                ),
                "ev_mobility_v1g_relocated_gwh": float(
                    ev_mobility_v1g_relocated[p].sum()
                ),
                "contracted_heating_flexibility_gw": float(
                    flexible_service_capacity[p, 0]
                ),
                "contracted_cooling_flexibility_gw": float(
                    flexible_service_capacity[p, 1]
                ),
                "contracted_ev_v1g_flexibility_gw": float(
                    flexible_service_capacity[p, 2]
                ),
                "contracted_ev_v2g_flexibility_gw": float(
                    flexible_service_capacity[p, 3]
                ),
                "firm_heating_flexibility_credit_gw": float(
                    firm_flexible_capacity_credit[p, 0]
                ),
                "firm_cooling_flexibility_credit_gw": float(
                    firm_flexible_capacity_credit[p, 1]
                ),
                "firm_ev_v1g_flexibility_credit_gw": float(
                    firm_flexible_capacity_credit[p, 2]
                ),
                "firm_ev_v2g_flexibility_credit_gw": float(
                    firm_flexible_capacity_credit[p, 3]
                ),
                "net_load_energy_change_gwh": float(
                    load[p].sum() - baseline_load[p].sum()
                ),
            }
        )
    pd.DataFrame(flexible_rows).to_csv(
        output_dir / "annual_flexible_load_by_province.csv",
        index=False,
        encoding="utf-8-sig",
    )
    if v5_formulation:
        v2g_definition = (
            "one physical EV-fleet state of charge with endogenous smart-charging "
            "and nested bidirectional-power contracts; V2G receives no reserve "
            "credit, while separately bounded and derated peak-deliverable service "
            "may receive firm capacity credit"
        )
        state_definition = (
            "periodic non-negative heating/cooling service inventories and one "
            "periodic physical EV-fleet state of charge with exogenous driving "
            "withdrawals and minimum departure energy"
        )
        ev_energy_flow_accounting = {
            "ev_mobility_charge_gwh": (
                "total optimized grid charging of the flexible EV-fleet share; "
                "mobility energy and V2G round-trip replenishment are not uniquely "
                "separable within the single physical state of charge"
            ),
            "ev_mobility_discharge_gwh": (
                "total V2G export from the integrated EV fleet"
            ),
            "ev_v2g_charge_gwh": (
                "legacy deviation-storage field; not applicable and zero under "
                "the integrated V5 fleet formulation"
            ),
            "ev_v2g_discharge_gwh": (
                "compatibility alias of ev_mobility_discharge_gwh under V5"
            ),
        }
    else:
        v2g_definition = (
            "incremental daily-cyclic virtual storage around the EV charging "
            "service; no reserve or capacity-margin credit"
        )
        state_definition = (
            "daily-reset equivalent heating/cooling inventories and causal EV "
            "charging backlog; Power_curve_V2 ev_hour_weight is an uncontrolled "
            "charging baseline and is not interpreted as vehicle plug availability"
        )
        ev_energy_flow_accounting = {
            "ev_v2g_charge_gwh": "charge into the separate V2G deviation store",
            "ev_v2g_discharge_gwh": (
                "discharge from the separate V2G deviation store"
            ),
        }
    _write_json(
        {
            "scenario": config.raw["scenario"],
            "optimization_hours": hours,
            "result_use": (
                "SCIENTIFIC_PRODUCTION"
                if hours == config.hours
                else "TEST_ONLY_TRUNCATED_HORIZON"
            ),
            "flexible_load_enabled": bool(config.raw["features"]["flexible_load"]),
            "flexible_load_formulation": flexible_formulation,
            "flexible_load_parameters": config.raw["flexible_load"],
            "wave_energy_enabled": data.wave is not None,
            "wave_energy_parameters": config.raw["wave_energy"],
            "hydro_provincial_aggregate_parameters": {
                key: value
                for key, value in config.raw["hydro"].items()
                if key.startswith("provincial_aggregate_")
            },
            "hydro_provincial_aggregate_data_summary": {
                "province_rows": int(len(data.hydro_aggregate_capacity)),
                "identified_station_capacity_gw": float(
                    data.hydro_aggregate_capacity[
                        "identified_station_capacity_gw"
                    ].sum()
                ),
                "aggregate_capacity_gw": float(
                    data.hydro_aggregate_capacity[
                        "provincial_aggregate_capacity_gw"
                    ].sum()
                ),
                "harmonized_conventional_capacity_gw": float(
                    data.hydro_aggregate_capacity[
                        "harmonized_conventional_capacity_gw"
                    ].sum()
                ),
            },
            "wave_energy_data_summary": (
                {
                    "active_grid_rows": int(len(data.wave.sites)),
                    "raw_capacity_upper_gw": float(
                        data.wave.sites.capacity_upper_gw_raw.sum()
                    ),
                    "active_capacity_upper_gw": float(
                        data.wave.sites.capacity_upper_gw.sum()
                    ),
                }
                if data.wave is not None
                else None
            ),
            "baseline_load_definition": (
                "base_residual + heating + cooling + EV; source table values remain immutable"
            ),
            "v2g_definition": v2g_definition,
            # Retain the established key for downstream readers while the
            # formulation-neutral name becomes the preferred field.
            "state_envelope_v2_definition": state_definition,
            "state_envelope_definition": state_definition,
            "ev_energy_flow_accounting": ev_energy_flow_accounting,
            "reliability_treatment": config.raw["flexible_load"]["reliability_treatment"],
            "security_parameters": {
                "capacity_margin_fraction": float(
                    config.raw["security"]["capacity_margin_fraction"]
                ),
                "capacity_margin_load_basis": capacity_margin_load_basis,
                "inertia_reference_seconds": config.raw["security"].get(
                    "inertia_reference_seconds"
                ),
                "inertia_tolerance_fraction": config.raw["security"].get(
                    "inertia_tolerance_fraction"
                ),
                "minimum_system_inertia_seconds_effective": minimum_inertia_seconds,
            },
        },
        output_dir / "scenario_manifest.json",
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
        aggregate_generation_gw=hydro_aggregate_generation,
        aggregate_available_gw=hydro_aggregate_available,
        reserve_up_gw=hydro_up_total,
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
        "accounting_scope": (
            "FULL_YEAR"
            if hours == config.hours
            else "SELECTED_HORIZON_ANNUAL_FLOW_SCALED"
        ),
        "optimization_hours": hours,
        "configured_hours": int(config.hours),
        "annual_flow_scaling_factor": annual_flow_scaling_factor,
        "annual_gross_emissions_mtco2": annual_emissions,
        "annual_emissions_before_dac_mtco2": annual_emissions,
        "annual_fossil_unabated_emissions_mtco2": float(fossil_unabated.sum()),
        "annual_dac_removed_mtco2": dac_removed,
        "annual_net_emissions_mtco2": net_emissions,
        "annual_carbon_limit_mtco2_per_year": annual_carbon_limit,
        "selected_horizon_carbon_limit_mtco2": carbon_limit,
        "carbon_limit_mtco2": carbon_limit,
        "annual_captured_mtco2": float(captured.sum()),
        "annual_co2_shipped_mtco2": float(co2_ship.sum()),
    }
    _write_json(carbon, output_dir / "annual_carbon_ccs.json")
    if qc["status"] != "PASS":
        raise RuntimeError(f"Production solution QC failed: {hard_checks}")
    return qc
