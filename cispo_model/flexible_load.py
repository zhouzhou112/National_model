"""Optional linear demand-flexibility blocks for decomposed provincial load.

The baseline load remains immutable. ``daily_energy_shift_v1`` preserves the
accepted daily energy-conserving formulation. ``state_envelope_v2`` adds a
daily-reset equivalent thermal inventory for heating/cooling and a causal EV
charging backlog. The latter treats the Power_curve_V2 EV profile as the
uncontrolled charging-service baseline, not as observed plug availability.

``comfort_envelope_v3`` replaces uniform thermal fractions with hourly
Power_curve_V2 BAIT/setpoint envelopes, strengthens the EV backlog with an
hourly service deadline, and supports an explicitly optional causal V2G
sensitivity. Base and previously accepted formulations are unchanged.

``service_constrained_v4`` is deliberately a separate contract.  It uses a
year-continuous signed thermal service state, endogenous contracted flexible
power, and one fleet-level EV state of charge (SOC) with exogenous connection,
mobility-withdrawal and departure-service inputs.  It must never be silently
substituted for V3 or for the production Base.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gurobipy as gp
import numpy as np

from .config import ModelConfig
from .data import ModelData


@dataclass
class FlexibleLoadBlock:
    effective_load_gw: Any
    baseline_load_gw: np.ndarray
    actual_components_gw: dict[str, Any]
    variables: dict[str, Any]
    costs: dict[str, Any]
    day_slices: tuple[slice, ...]


def make_day_slices(hours: int, window_hours: int = 24) -> tuple[slice, ...]:
    if hours <= 0 or window_hours <= 0:
        raise ValueError("hours and window_hours must be positive")
    return tuple(
        slice(start, min(start + window_hours, hours))
        for start in range(0, hours, window_hours)
    )


def _thermal_shift_bounds(
    baseline: np.ndarray,
    day_slices: tuple[slice, ...],
    maximum_reduction_fraction: float,
    maximum_increase_fraction_of_daily_peak: float,
) -> tuple[np.ndarray, np.ndarray]:
    down = maximum_reduction_fraction * baseline
    up = np.zeros_like(baseline)
    for day in day_slices:
        peak = baseline[:, day].max(axis=1)
        up[:, day] = (
            maximum_increase_fraction_of_daily_peak * peak[:, None]
        )
    return up, down


def _thermal_state_bounds(
    baseline: np.ndarray,
    day_slices: tuple[slice, ...],
    maximum_reduction_fraction: float,
    maximum_increase_fraction_of_daily_peak: float,
    duration_hours: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return charge, discharge and inventory bounds for the state proxy."""
    up, down = _thermal_shift_bounds(
        baseline,
        day_slices,
        maximum_reduction_fraction,
        maximum_increase_fraction_of_daily_peak,
    )
    energy = np.zeros_like(baseline)
    for day in day_slices:
        power_envelope = np.maximum(
            up[:, day].max(axis=1),
            down[:, day].max(axis=1),
        )
        energy[:, day] = (duration_hours * power_envelope)[:, None]
    return up, down, energy


def _thermal_envelope_state_bounds(
    up: np.ndarray,
    down: np.ndarray,
    day_slices: tuple[slice, ...],
    duration_hours: float,
) -> np.ndarray:
    """Return an equivalent thermal-energy bound for exogenous power envelopes."""
    if up.shape != down.shape:
        raise ValueError("Thermal increase and reduction envelopes must align")
    energy = np.zeros_like(up)
    for day in day_slices:
        power_envelope = np.maximum(
            up[:, day].max(axis=1),
            down[:, day].max(axis=1),
        )
        energy[:, day] = (duration_hours * power_envelope)[:, None]
    return energy


def _ev_v1g_shift_bounds(
    baseline: np.ndarray,
    day_slices: tuple[slice, ...],
    shiftable_energy_fraction: float,
    maximum_power_to_daily_average_ratio: float,
) -> tuple[np.ndarray, np.ndarray]:
    down = shiftable_energy_fraction * baseline
    up = np.zeros_like(baseline)
    for day in day_slices:
        day_values = baseline[:, day]
        maximum_power = (
            maximum_power_to_daily_average_ratio
            * day_values.mean(axis=1)
        )
        up[:, day] = np.maximum(maximum_power[:, None] - day_values, 0.0)
    return up, down


def _ev_backlog_bounds(
    baseline: np.ndarray,
    day_slices: tuple[slice, ...],
    shiftable_energy_fraction: float,
    maximum_power_to_daily_average_ratio: float,
    maximum_queue_duration_hours: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return V1G relocation bounds plus a causal charging-backlog envelope."""
    up = np.zeros_like(baseline)
    down = shiftable_energy_fraction * baseline
    queue = np.zeros_like(baseline)
    for day in day_slices:
        day_values = baseline[:, day]
        # The uncontrolled Power_curve_V2 profile must always remain feasible.
        maximum_power = np.maximum(
            maximum_power_to_daily_average_ratio * day_values.mean(axis=1),
            day_values.max(axis=1),
        )
        up[:, day] = np.maximum(maximum_power[:, None] - day_values, 0.0)
        shiftable_average = (
            shiftable_energy_fraction * day_values.mean(axis=1)
        )
        queue[:, day] = (
            maximum_queue_duration_hours * shiftable_average
        )[:, None]
    return up, down, queue


def _ev_deadline_backlog_bounds(
    baseline: np.ndarray,
    day_slices: tuple[slice, ...],
    shiftable_energy_fraction: float,
    maximum_power_to_daily_average_ratio: float,
    maximum_queue_duration_hours: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return V1G bounds with a cumulative latest-service deadline.

    At hour ``t`` the backlog cannot exceed shiftable baseline energy from the
    latest ``L`` hours. Combined with the queue transition, this is the
    aggregate cumulative constraint ``served(t) >= baseline(t-L)``.
    """
    up, down, _ = _ev_backlog_bounds(
        baseline,
        day_slices,
        shiftable_energy_fraction,
        maximum_power_to_daily_average_ratio,
        maximum_queue_duration_hours,
    )
    deadline = int(round(maximum_queue_duration_hours))
    if not np.isclose(deadline, maximum_queue_duration_hours) or deadline <= 0:
        raise ValueError("V1G maximum queue duration must be a positive integer")
    queue = np.zeros_like(baseline)
    movable_baseline = shiftable_energy_fraction * baseline
    for day in day_slices:
        start, stop = int(day.start), int(day.stop)
        for hour in range(start, stop):
            rolling_start = max(start, hour - deadline + 1)
            queue[:, hour] = movable_baseline[:, rolling_start : hour + 1].sum(
                axis=1
            )
    return up, down, queue


def _zero(shape: tuple[int, int]) -> np.ndarray:
    return np.zeros(shape, dtype=float)


def _attach_daily_reset_state(
    model: gp.Model,
    *,
    state: Any,
    charge: Any,
    discharge: Any,
    day_slices: tuple[slice, ...],
    retention: float,
    charge_efficiency: float,
    discharge_efficiency: float,
    name: str,
) -> None:
    """Attach a causal within-day state that starts and ends at zero."""
    for day_number, day in enumerate(day_slices):
        start, stop = int(day.start), int(day.stop)
        model.addConstr(
            state[:, start]
            == charge_efficiency * charge[:, start]
            - discharge[:, start] / discharge_efficiency,
            name=f"{name}_daily_initial_transition_d{day_number}",
        )
        if stop - start > 1:
            model.addConstr(
                state[:, start + 1:stop]
                == retention * state[:, start:stop - 1]
                + charge_efficiency * charge[:, start + 1:stop]
                - discharge[:, start + 1:stop] / discharge_efficiency,
                name=f"{name}_hourly_transition_d{day_number}",
            )
        model.addConstr(
            state[:, stop - 1] == 0.0,
            name=f"{name}_daily_terminal_reset_d{day_number}",
        )


def _attach_ev_backlog(
    model: gp.Model,
    *,
    queue: Any,
    shift_up: Any,
    shift_down: Any,
    day_slices: tuple[slice, ...],
) -> None:
    """Attach a causal queue: deferred baseline charging must precede recovery."""
    for day_number, day in enumerate(day_slices):
        start, stop = int(day.start), int(day.stop)
        model.addConstr(
            queue[:, start] == shift_down[:, start] - shift_up[:, start],
            name=f"ev_v1g_backlog_initial_transition_d{day_number}",
        )
        if stop - start > 1:
            model.addConstr(
                queue[:, start + 1:stop]
                == queue[:, start:stop - 1]
                + shift_down[:, start + 1:stop]
                - shift_up[:, start + 1:stop],
                name=f"ev_v1g_backlog_hourly_transition_d{day_number}",
            )
        model.addConstr(
            queue[:, stop - 1] == 0.0,
            name=f"ev_v1g_backlog_daily_terminal_reset_d{day_number}",
        )


V4_CAPACITY_SERVICES = ("heating", "cooling", "ev_v1g", "ev_v2g")


def _periodic_transition(
    model: gp.Model,
    *,
    state: Any,
    charge: Any,
    discharge: Any,
    withdrawal: np.ndarray,
    retention: float | np.ndarray,
    charge_efficiency: float | np.ndarray,
    discharge_efficiency: float | np.ndarray,
    name: str,
) -> None:
    """Attach a selected-horizon periodic state transition.

    On a scientific 8,760-hour horizon this is the annual cyclic boundary.
    Truncated gates intentionally use the same equation over their selected
    test horizon; those gates prove formulation integrity only and are not a
    proxy for annual chronology.
    """
    if state.shape[1] <= 0:
        raise ValueError("Periodic state requires at least one hour")
    model.addConstr(
        state[:, 0]
        == retention * state[:, -1]
        + charge_efficiency * charge[:, 0]
        - discharge[:, 0] / discharge_efficiency
        - withdrawal[:, 0],
        name=f"{name}_periodic_first_transition",
    )
    if state.shape[1] > 1:
        model.addConstr(
            state[:, 1:]
            == retention * state[:, :-1]
            + charge_efficiency * charge[:, 1:]
            - discharge[:, 1:] / discharge_efficiency
            - withdrawal[:, 1:],
            name=f"{name}_hourly_transition",
        )


def _capacity_upper_from_profile(
    available_power: np.ndarray,
    availability_fraction: np.ndarray,
    *,
    label: str,
) -> np.ndarray:
    """Return the smallest contracted-power upper bound covering a profile."""
    if available_power.shape != availability_fraction.shape:
        raise ValueError(f"{label} availability shape mismatch")
    active_without_availability = (
        (available_power > 1e-12) & (availability_fraction <= 1e-12)
    )
    if active_without_availability.any():
        raise ValueError(
            f"{label} has positive available power where availability is zero"
        )
    ratio = np.divide(
        available_power,
        availability_fraction,
        out=np.zeros_like(available_power),
        where=availability_fraction > 1e-12,
    )
    return ratio.max(axis=1)


def _attach_service_constrained_v4(
    model: gp.Model,
    config: ModelConfig,
    data: ModelData,
    *,
    baseline: np.ndarray,
    components: dict[str, np.ndarray],
    day_slices: tuple[slice, ...],
    hours: int,
) -> FlexibleLoadBlock:
    """Attach the V4 thermal-service and fleet-mobility formulation.

    V4 intentionally has no daily energy-conservation or daily-reset
    constraint.  Thermal and EV states are periodic over the selected
    chronological horizon, with the full-year case being the only scientific
    annual interpretation.  The loader validates every V4 input before this
    builder is reached.
    """
    v4 = data.flexible_load_v4
    if v4 is None:
        raise ValueError("service_constrained_v4 requires validated V4 input data")
    settings = config.raw["flexible_load"]
    shape = baseline.shape
    p_count = shape[0]
    if shape[1] != hours:
        raise ValueError("V4 load shape does not match requested horizon")

    thermal_envelopes = {
        key: value[:, :hours]
        for key, value in v4.thermal_envelopes_gw.items()
    }
    thermal_availability = {
        key: value[:, :hours]
        for key, value in v4.thermal_availability.items()
    }
    ev_availability = {
        key: value[:, :hours]
        for key, value in v4.ev_availability.items()
    }
    ev_mobility = {
        key: value[:, :hours]
        for key, value in v4.ev_mobility.items()
    }
    variables: dict[str, Any] = {}
    actual_components: dict[str, Any] = {
        "base_residual": components["base_residual"],
    }

    capacity_ub = np.zeros((p_count, len(V4_CAPACITY_SERVICES)), dtype=float)
    for column, component in enumerate(("heating", "cooling")):
        power_envelope = np.maximum(
            thermal_envelopes[f"{component}_up"],
            thermal_envelopes[f"{component}_down"],
        )
        capacity_ub[:, column] = _capacity_upper_from_profile(
            power_envelope,
            thermal_availability[component],
            label=f"{component} V4",
        )
    capacity_ub[:, 2] = _capacity_upper_from_profile(
        ev_availability["available_charge_power_gw"],
        ev_availability["connected_vehicle_fraction"],
        label="EV charge V4",
    )
    if bool(settings["ev_v2g"]["enabled"]):
        capacity_ub[:, 3] = _capacity_upper_from_profile(
            ev_availability["available_discharge_power_gw"],
            ev_availability["connected_vehicle_fraction"],
            label="EV V2G V4",
        )
    capacity = model.addMVar(
        (p_count, len(V4_CAPACITY_SERVICES)),
        lb=0.0,
        ub=capacity_ub,
        name="flexible_service_capacity_gw",
    )
    variables["flexible_service_capacity"] = capacity

    thermal_activation_terms: dict[str, Any] = {}
    thermal_debt_terms: dict[str, Any] = {}
    for column, component in enumerate(("heating", "cooling")):
        params = v4.thermal_parameters[component]
        up_ub = thermal_envelopes[f"{component}_up"]
        down_ub = thermal_envelopes[f"{component}_down"]
        availability = thermal_availability[component]
        k_service = capacity[:, column].reshape((p_count, 1))
        positive_duration = params["positive_state_duration_hours"]
        negative_duration = params["negative_state_duration_hours"]
        state_ub = np.broadcast_to(
            positive_duration[:, None] * capacity_ub[:, column, None], shape
        ).copy()
        debt_ub = np.broadcast_to(
            negative_duration[:, None] * capacity_ub[:, column, None], shape
        ).copy()
        up = model.addMVar(shape, lb=0.0, ub=up_ub, name=f"{component}_shift_up_gw")
        down = model.addMVar(
            shape, lb=0.0, ub=down_ub, name=f"{component}_shift_down_gw"
        )
        state = model.addMVar(
            shape,
            lb=-debt_ub,
            ub=state_ub,
            name=f"{component}_state_gwh",
        )
        debt = model.addMVar(
            shape, lb=0.0, ub=debt_ub, name=f"{component}_comfort_debt_gwh"
        )
        model.addConstr(
            up <= availability * k_service,
            name=f"{component}_contracted_increase_power",
        )
        model.addConstr(
            down <= availability * k_service,
            name=f"{component}_contracted_reduction_power",
        )
        model.addConstr(
            state <= positive_duration[:, None] * k_service,
            name=f"{component}_positive_service_bound",
        )
        model.addConstr(
            state >= -negative_duration[:, None] * k_service,
            name=f"{component}_negative_service_bound",
        )
        model.addConstr(
            debt >= -state,
            name=f"{component}_comfort_debt_definition",
        )
        _periodic_transition(
            model,
            state=state,
            charge=up,
            discharge=down,
            withdrawal=np.zeros(shape, dtype=float),
            retention=params["retention_per_hour"][:, None],
            charge_efficiency=params["charge_efficiency"][:, None],
            discharge_efficiency=params["discharge_efficiency"][:, None],
            name=f"{component}_state",
        )
        actual_components[component] = components[component] + up - down
        variables.update(
            {
                f"{component}_shift_up": up,
                f"{component}_shift_down": down,
                f"{component}_state": state,
                f"{component}_comfort_debt": debt,
            }
        )
        thermal_activation_terms[component] = up.sum() + down.sum()
        thermal_debt_terms[component] = debt.sum()

    ev_settings = settings["ev_v2g"]
    connected = ev_availability["connected_vehicle_fraction"]
    charge_ub = ev_availability["available_charge_power_gw"]
    discharge_ub = ev_availability["available_discharge_power_gw"]
    fleet_energy_ub = ev_availability["fleet_energy_capacity_gwh"]
    driving_withdrawal = ev_mobility["driving_energy_withdrawal_gwh"]
    minimum_departure = ev_mobility["minimum_departure_energy_gwh"]
    charge = model.addMVar(shape, lb=0.0, ub=charge_ub, name="ev_mobility_charge_gw")
    v2g_enabled = bool(ev_settings["enabled"])
    discharge: Any = (
        model.addMVar(
            shape, lb=0.0, ub=discharge_ub, name="ev_mobility_discharge_gw"
        )
        if v2g_enabled
        else _zero(shape)
    )
    soc = model.addMVar(shape, lb=0.0, ub=fleet_energy_ub, name="ev_mobility_soc_gwh")
    deviation_ub = charge_ub + components["ev"]
    charge_deviation = model.addMVar(
        shape,
        lb=0.0,
        ub=deviation_ub,
        name="ev_mobility_charge_deviation_gw",
    )
    k_charge = capacity[:, 2].reshape((p_count, 1))
    k_v2g = capacity[:, 3].reshape((p_count, 1))
    model.addConstr(
        charge <= connected * k_charge,
        name="ev_mobility_contracted_charge_power",
    )
    if v2g_enabled:
        model.addConstr(
            discharge <= connected * k_v2g,
            name="ev_mobility_contracted_discharge_power",
        )
    model.addConstr(soc >= minimum_departure, name="ev_mobility_departure_soc")
    model.addConstr(
        charge_deviation >= charge - components["ev"],
        name="ev_mobility_charge_deviation_positive",
    )
    model.addConstr(
        charge_deviation >= components["ev"] - charge,
        name="ev_mobility_charge_deviation_negative",
    )
    _periodic_transition(
        model,
        state=soc,
        charge=charge,
        discharge=discharge,
        withdrawal=driving_withdrawal,
        retention=1.0 - float(ev_settings["self_discharge_fraction_per_hour"]),
        charge_efficiency=float(ev_settings["charge_efficiency"]),
        discharge_efficiency=float(ev_settings["discharge_efficiency"]),
        name="ev_mobility_soc",
    )
    actual_components["ev"] = charge
    variables.update(
        ev_mobility_charge=charge,
        ev_mobility_discharge=discharge,
        ev_mobility_soc=soc,
        ev_mobility_charge_deviation=charge_deviation,
        # Compatibility aliases make the existing V2G output series usable,
        # while V4 still has one physical fleet SOC rather than a deviation
        # battery layered on top of V1G.
        ev_v2g_discharge=discharge,
        ev_v2g_soc=soc,
        ev_grid_charge_power_ub=charge_ub,
    )

    effective_load = (
        actual_components["base_residual"]
        + actual_components["heating"]
        + actual_components["cooling"]
        + actual_components["ev"]
        - discharge
    )
    model.addConstr(effective_load >= 0.0, name="effective_load_nonnegative")
    variables.update(
        effective_load=effective_load,
        actual_heating_load=actual_components["heating"],
        actual_cooling_load=actual_components["cooling"],
        actual_ev_load=actual_components["ev"],
        ev_v2g_charge=_zero(shape),
    )

    service_costs = v4.service_costs
    enablement_cost = gp.quicksum(
        service_costs[service]["enablement_cost_yuan_per_kw_year"]
        * capacity[:, column]
        for column, service in enumerate(V4_CAPACITY_SERVICES)
    )
    thermal_activation_cost = gp.quicksum(
        1e-3
        * service_costs[component]["activation_cost_yuan_per_mwh"]
        * thermal_activation_terms[component]
        for component in ("heating", "cooling")
    )
    thermal_comfort_cost = gp.quicksum(
        1e-6
        * service_costs[component]["comfort_debt_cost_yuan_per_gwh_hour"]
        * thermal_debt_terms[component]
        for component in ("heating", "cooling")
    )
    ev_relocation_cost = (
        1e-3
        * service_costs["ev_v1g"]["activation_cost_yuan_per_mwh"]
        * charge_deviation.sum()
    )
    ev_v2g_cost = (
        1e-3
        * service_costs["ev_v2g"]["activation_cost_yuan_per_mwh"]
        * discharge.sum()
    )
    return FlexibleLoadBlock(
        effective_load_gw=effective_load,
        baseline_load_gw=baseline,
        actual_components_gw=actual_components,
        variables=variables,
        costs={
            "flexible_load_v4_enablement": enablement_cost,
            "flexible_load_v4_thermal_activation": thermal_activation_cost,
            "flexible_load_v4_comfort_debt": thermal_comfort_cost,
            "flexible_load_v4_ev_v1g_relocation": ev_relocation_cost,
            "flexible_load_v4_ev_v2g_discharge": ev_v2g_cost,
        },
        day_slices=day_slices,
    )


def attach_flexible_load(
    model: gp.Model,
    config: ModelConfig,
    data: ModelData,
    *,
    hours: int,
) -> FlexibleLoadBlock:
    """Attach optional demand flexibility and return the effective hourly load."""
    baseline = data.load_gw[:, :hours]
    components = {
        name: values[:, :hours]
        for name, values in data.load_components_gw.items()
    }
    day_slices = make_day_slices(
        hours, int(config.raw["flexible_load"]["energy_conservation_window_hours"])
    )
    shape = baseline.shape
    if not bool(config.raw["features"]["flexible_load"]):
        return FlexibleLoadBlock(
            effective_load_gw=baseline,
            baseline_load_gw=baseline,
            actual_components_gw=dict(components),
            variables={},
            costs={},
            day_slices=day_slices,
        )

    settings = config.raw["flexible_load"]
    formulation = str(settings.get("formulation", "daily_energy_shift_v1"))
    if formulation == "service_constrained_v4":
        return _attach_service_constrained_v4(
            model,
            config,
            data,
            baseline=baseline,
            components=components,
            day_slices=day_slices,
            hours=hours,
        )
    variables: dict[str, Any] = {}
    shift_terms: list[Any] = []
    v3_activation_terms: dict[str, Any] = {}
    actual_components: dict[str, Any] = {
        "base_residual": components["base_residual"]
    }

    for component in ("heating", "cooling"):
        component_settings = settings[component]
        component_baseline = components[component]
        if bool(component_settings["enabled"]):
            if formulation == "comfort_envelope_v3":
                up_ub = data.flexible_load_envelopes_gw[f"{component}_up"][
                    :, :hours
                ]
                down_ub = data.flexible_load_envelopes_gw[f"{component}_down"][
                    :, :hours
                ]
                state_ub = _thermal_envelope_state_bounds(
                    up_ub,
                    down_ub,
                    day_slices,
                    float(
                        component_settings[
                            "equivalent_storage_duration_hours"
                        ]
                    ),
                )
            elif formulation == "state_envelope_v2":
                up_ub, down_ub, state_ub = _thermal_state_bounds(
                    component_baseline,
                    day_slices,
                    float(component_settings["maximum_reduction_fraction"]),
                    float(
                        component_settings[
                            "maximum_increase_fraction_of_daily_peak"
                        ]
                    ),
                    float(component_settings["duration_hours"]),
                )
            else:
                up_ub, down_ub = _thermal_shift_bounds(
                    component_baseline,
                    day_slices,
                    float(component_settings["maximum_reduction_fraction"]),
                    float(
                        component_settings[
                            "maximum_increase_fraction_of_daily_peak"
                        ]
                    ),
                )
            up = model.addMVar(shape, lb=0.0, ub=up_ub, name=f"{component}_shift_up_gw")
            down = model.addMVar(
                shape, lb=0.0, ub=down_ub, name=f"{component}_shift_down_gw"
            )
            if formulation in {"state_envelope_v2", "comfort_envelope_v3"}:
                state = model.addMVar(
                    shape,
                    lb=0.0,
                    ub=state_ub,
                    name=f"{component}_state_gwh",
                )
                _attach_daily_reset_state(
                    model,
                    state=state,
                    charge=up,
                    discharge=down,
                    day_slices=day_slices,
                    retention=float(component_settings["retention_per_hour"]),
                    charge_efficiency=float(
                        component_settings["charge_efficiency"]
                    ),
                    discharge_efficiency=float(
                        component_settings["discharge_efficiency"]
                    ),
                    name=f"{component}_state",
                )
                variables[f"{component}_state"] = state
            else:
                for day_number, day in enumerate(day_slices):
                    model.addConstr(
                        up[:, day].sum(axis=1) == down[:, day].sum(axis=1),
                        name=f"{component}_daily_energy_conservation_d{day_number}",
                    )
            actual_components[component] = component_baseline + up - down
            variables[f"{component}_shift_up"] = up
            variables[f"{component}_shift_down"] = down
            if formulation == "comfort_envelope_v3":
                v3_activation_terms[f"{component}_increase"] = up.sum()
                v3_activation_terms[f"{component}_reduction"] = down.sum()
            else:
                shift_terms.extend((up.sum(), down.sum()))
        else:
            actual_components[component] = component_baseline

    ev_settings = settings["ev_v1g"]
    ev_baseline = components["ev"]
    ev_grid_charge_ub = ev_baseline
    if bool(ev_settings["enabled"]):
        if formulation == "comfort_envelope_v3":
            ev_up_ub, ev_down_ub, ev_queue_ub = (
                _ev_deadline_backlog_bounds(
                    ev_baseline,
                    day_slices,
                    float(ev_settings["shiftable_energy_fraction"]),
                    float(
                        ev_settings["maximum_power_to_daily_average_ratio"]
                    ),
                    float(ev_settings["maximum_queue_duration_hours"]),
                )
            )
        elif formulation == "state_envelope_v2":
            ev_up_ub, ev_down_ub, ev_queue_ub = _ev_backlog_bounds(
                ev_baseline,
                day_slices,
                float(ev_settings["shiftable_energy_fraction"]),
                float(ev_settings["maximum_power_to_daily_average_ratio"]),
                float(ev_settings["maximum_queue_duration_hours"]),
            )
        else:
            ev_up_ub, ev_down_ub = _ev_v1g_shift_bounds(
                ev_baseline,
                day_slices,
                float(ev_settings["shiftable_energy_fraction"]),
                float(ev_settings["maximum_power_to_daily_average_ratio"]),
            )
        ev_up = model.addMVar(shape, lb=0.0, ub=ev_up_ub, name="ev_v1g_shift_up_gw")
        ev_down = model.addMVar(
            shape, lb=0.0, ub=ev_down_ub, name="ev_v1g_shift_down_gw"
        )
        ev_grid_charge_ub = ev_baseline + ev_up_ub
        if formulation in {"state_envelope_v2", "comfort_envelope_v3"}:
            ev_queue = model.addMVar(
                shape,
                lb=0.0,
                ub=ev_queue_ub,
                name="ev_v1g_backlog_gwh",
            )
            _attach_ev_backlog(
                model,
                queue=ev_queue,
                shift_up=ev_up,
                shift_down=ev_down,
                day_slices=day_slices,
            )
            variables["ev_v1g_backlog"] = ev_queue
        else:
            for day_number, day in enumerate(day_slices):
                model.addConstr(
                    ev_up[:, day].sum(axis=1) == ev_down[:, day].sum(axis=1),
                    name=f"ev_v1g_daily_energy_conservation_d{day_number}",
                )
        actual_components["ev"] = ev_baseline + ev_up - ev_down
        variables.update(ev_v1g_shift_up=ev_up, ev_v1g_shift_down=ev_down)
        if formulation == "comfort_envelope_v3":
            # Daily service conservation makes ev_down and ev_up equal. Charge
            # one relocated MWh once rather than counting both directions.
            v3_activation_terms["ev_v1g_relocated"] = ev_down.sum()
        else:
            shift_terms.extend((ev_up.sum(), ev_down.sum()))
    else:
        actual_components["ev"] = ev_baseline

    v2g_settings = settings["ev_v2g"]
    v2g_charge: Any = _zero(shape)
    v2g_discharge: Any = _zero(shape)
    v2g_soc: Any = _zero(shape)
    v2g_throughput = gp.LinExpr()
    if bool(v2g_settings["enabled"]):
        power_ub = _zero(shape)
        energy_ub = _zero(shape)
        duration = float(v2g_settings["power_duration_hours"])
        if formulation == "comfort_envelope_v3":
            power_fraction = float(
                v2g_settings["power_fraction_of_daily_baseline_peak"]
            )
            for day in day_slices:
                available_power = (
                    power_fraction * ev_baseline[:, day].max(axis=1)
                )
                power_ub[:, day] = available_power[:, None]
                energy_ub[:, day] = (duration * available_power)[:, None]
        else:
            participation = float(v2g_settings["participation_fraction"])
            energy_ratio = float(
                v2g_settings["usable_energy_to_daily_ev_energy_ratio"]
            )
            for day in day_slices:
                daily_ev_energy = ev_baseline[:, day].sum(axis=1)
                usable_energy = participation * energy_ratio * daily_ev_energy
                energy_ub[:, day] = usable_energy[:, None]
                power_ub[:, day] = (usable_energy / duration)[:, None]
        v2g_charge = model.addMVar(
            shape, lb=0.0, ub=power_ub, name="ev_v2g_charge_gw"
        )
        v2g_discharge = model.addMVar(
            shape, lb=0.0, ub=power_ub, name="ev_v2g_discharge_gw"
        )
        v2g_soc = model.addMVar(
            shape, lb=0.0, ub=energy_ub, name="ev_v2g_soc_gwh"
        )
        eta_charge = float(v2g_settings["charge_efficiency"])
        eta_discharge = float(v2g_settings["discharge_efficiency"])
        retention = 1.0 - float(v2g_settings["self_discharge_fraction_per_hour"])
        if formulation == "comfort_envelope_v3":
            _attach_daily_reset_state(
                model,
                state=v2g_soc,
                charge=v2g_charge,
                discharge=v2g_discharge,
                day_slices=day_slices,
                retention=retention,
                charge_efficiency=eta_charge,
                discharge_efficiency=eta_discharge,
                name="ev_v2g_state",
            )
            model.addConstr(
                actual_components["ev"] + v2g_charge <= ev_grid_charge_ub,
                name="ev_combined_grid_charging_power_limit",
            )
        else:
            for day_number, day in enumerate(day_slices):
                start, stop = int(day.start), int(day.stop)
                model.addConstr(
                    v2g_soc[:, start]
                    == retention * v2g_soc[:, stop - 1]
                    + eta_charge * v2g_charge[:, start]
                    - v2g_discharge[:, start] / eta_discharge,
                    name=f"ev_v2g_daily_cyclic_first_d{day_number}",
                )
                if stop - start > 1:
                    model.addConstr(
                        v2g_soc[:, start + 1:stop]
                        == retention * v2g_soc[:, start:stop - 1]
                        + eta_charge * v2g_charge[:, start + 1:stop]
                        - v2g_discharge[:, start + 1:stop] / eta_discharge,
                        name=f"ev_v2g_hourly_transition_d{day_number}",
                    )
        variables.update(
            ev_v2g_charge=v2g_charge,
            ev_v2g_discharge=v2g_discharge,
            ev_v2g_soc=v2g_soc,
        )
        v2g_throughput = v2g_charge.sum() + v2g_discharge.sum()
        if formulation == "comfort_envelope_v3":
            # One discharged MWh represents one use of the battery cycle. Grid
            # energy for charging is already paid through the system objective.
            v3_activation_terms["ev_v2g_discharged"] = v2g_discharge.sum()

    effective_load = (
        actual_components["base_residual"]
        + actual_components["heating"]
        + actual_components["cooling"]
        + actual_components["ev"]
        + v2g_charge
        - v2g_discharge
    )
    model.addConstr(effective_load >= 0.0, name="effective_load_nonnegative")
    variables.update(
        effective_load=effective_load,
        actual_heating_load=actual_components["heating"],
        actual_cooling_load=actual_components["cooling"],
        actual_ev_load=actual_components["ev"],
        ev_grid_charge_power_ub=ev_grid_charge_ub,
        ev_v2g_charge=v2g_charge,
        ev_v2g_discharge=v2g_discharge,
        ev_v2g_soc=v2g_soc,
    )

    if formulation == "comfort_envelope_v3":
        activation_costs = settings["activation_costs_yuan_per_mwh"]
        cost_components = {
            f"flexible_load_{name}_compensation": (
                float(activation_costs[name])
                * 1e-3
                * v3_activation_terms.get(name, gp.LinExpr())
            )
            for name in (
                "heating_reduction",
                "heating_increase",
                "cooling_reduction",
                "cooling_increase",
                "ev_v1g_relocated",
                "ev_v2g_discharged",
            )
        }
    else:
        shift_cost = (
            float(settings["shift_throughput_cost_yuan_per_mwh"])
            * 1e-3
            * gp.quicksum(shift_terms)
            if shift_terms
            else gp.LinExpr()
        )
        degradation_cost = (
            float(settings["degradation_cost_yuan_per_mwh"])
            * 1e-3
            * v2g_throughput
        )
        cost_components = {
            "flexible_load_shift_throughput": shift_cost,
            "ev_v2g_degradation": degradation_cost,
        }
    return FlexibleLoadBlock(
        effective_load_gw=effective_load,
        baseline_load_gw=baseline,
        actual_components_gw=actual_components,
        variables=variables,
        costs=cost_components,
        day_slices=day_slices,
    )
