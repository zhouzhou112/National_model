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
selected-horizon periodic, non-negative thermal service inventory, endogenous
contracted flexible power, and one fleet-level EV state of charge (SOC) with
exogenous availability and mobility-withdrawal inputs.  It must never be
silently substituted for V3 or for the production Base.

``integrated_service_constrained_v5`` retains that physical service model but
integrates paid V1G and V2G, nests the V2G contract inside smart charging, and
exposes only derated peak-deliverable flexibility to planning adequacy.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import gurobipy as gp
import numpy as np

from .config import ModelConfig
from .data import ModelData
from .flexible_load_numerics import (
    _compressed_thermal_state_audit,
    _compressed_thermal_state_mask,
    _retained_transition_incoming_gaps,
    _service_effective_load_lower_bound,
    _thermal_state_chain_numerical_risks,
)


@dataclass
class FlexibleLoadBlock:
    effective_load_gw: Any
    baseline_load_gw: np.ndarray
    actual_components_gw: dict[str, Any]
    variables: dict[str, Any]
    costs: dict[str, Any]
    day_slices: tuple[slice, ...]
    structural_audit: dict[str, Any] = field(default_factory=dict)


@dataclass
class SparseThermalStateView:
    """Reconstruct a full hourly thermal state from retained state nodes."""

    active: Any | None
    retained_mask: np.ndarray
    retention_per_hour: np.ndarray

    @property
    def shape(self) -> tuple[int, int]:
        return tuple(self.retained_mask.shape)

    def getValue(self) -> np.ndarray:
        retained = np.asarray(self.retained_mask, dtype=bool)
        values = np.zeros(retained.shape, dtype=float)
        if self.active is None:
            return values
        values[retained] = np.asarray(self.active.X, dtype=float)
        hours = retained.shape[1]
        for province_position in range(retained.shape[0]):
            retained_hours = np.flatnonzero(retained[province_position])
            if not len(retained_hours):
                continue
            rho = float(self.retention_per_hour[province_position])
            cyclic_hours = np.concatenate(
                (retained_hours, [int(retained_hours[0]) + hours])
            )
            for start, stop in zip(cyclic_hours[:-1], cyclic_hours[1:]):
                predecessor = values[province_position, int(start) % hours]
                for hour in range(int(start) + 1, int(stop)):
                    values[province_position, hour % hours] = (
                        rho ** (hour - int(start))
                    ) * predecessor
        return values


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


def _add_sparse_hourly_control(
    model: gp.Model,
    *,
    upper_bound: np.ndarray,
    name: str,
) -> tuple[Any, Any | None, np.ndarray]:
    """Create variables only where an hourly control has a positive bound.

    The returned ``MLinExpr`` preserves the full province-hour shape for all
    downstream equations and exports. Exact-zero cells are constants rather
    than fixed Gurobi variables, so their tautological contracted-power rows
    can also be omitted before presolve.
    """
    upper = np.asarray(upper_bound, dtype=float)
    if upper.ndim != 2:
        raise ValueError(f"{name} upper bound must be two-dimensional")
    if not np.isfinite(upper).all() or (upper < 0.0).any():
        raise ValueError(f"{name} upper bound must be finite and non-negative")
    active_mask = upper > 0.0
    expression = gp.MLinExpr.zeros(upper.shape)
    active_count = int(active_mask.sum())
    if active_count == 0:
        return expression, None, active_mask
    active = model.addMVar(
        active_count,
        lb=0.0,
        ub=upper[active_mask],
        name=f"{name}_active",
    )
    expression[active_mask] = active
    return expression, active, active_mask


def _add_compressed_thermal_state(
    model: gp.Model,
    *,
    upper_bound: np.ndarray,
    control_support: np.ndarray,
    retention_per_hour: np.ndarray,
    name: str,
) -> tuple[
    SparseThermalStateView,
    Any | None,
    np.ndarray,
    dict[str, Any],
]:
    """Create only controllable thermal states and exact decay anchors."""
    upper = np.asarray(upper_bound, dtype=float)
    support = np.asarray(control_support, dtype=bool)
    retention = np.asarray(retention_per_hour, dtype=float)
    if upper.shape != support.shape:
        raise ValueError(f"{name} upper-bound/support shape mismatch")
    retained = _compressed_thermal_state_mask(support, retention)
    if np.any(retained & (upper <= 0.0)):
        raise ValueError(
            f"{name} retained state has no positive state-capacity bound"
        )
    active_count = int(retained.sum())
    active = (
        model.addMVar(
            active_count,
            lb=0.0,
            ub=upper[retained],
            name=f"{name}_retained",
        )
        if active_count
        else None
    )
    view = SparseThermalStateView(
        active=active,
        retained_mask=retained,
        retention_per_hour=retention,
    )
    return (
        view,
        active,
        retained,
        _compressed_thermal_state_audit(support, retained, retention),
    )


def _attach_compressed_thermal_state_transitions(
    model: gp.Model,
    *,
    active_state: Any,
    retained_state_mask: np.ndarray,
    retention_per_hour: np.ndarray,
    charge: Any,
    discharge: Any,
    charge_efficiency: np.ndarray,
    discharge_efficiency: np.ndarray,
    capacity: Any,
    positive_duration_hours: np.ndarray,
    name: str,
) -> None:
    """Attach exact cyclic transitions between retained thermal states."""
    retained = np.asarray(retained_state_mask, dtype=bool)
    hours = retained.shape[1]
    cursor = 0
    for province_position in range(retained.shape[0]):
        retained_hours = np.flatnonzero(retained[province_position])
        count = int(len(retained_hours))
        if not count:
            continue
        state = active_state[cursor : cursor + count]
        predecessor = gp.MLinExpr.zeros(count)
        predecessor[0] = state[-1]
        if count > 1:
            predecessor[1:] = state[:-1]
        gaps = _retained_transition_incoming_gaps(
            retained_hours,
            hours,
        ).astype(float)
        predecessor_coefficients = (
            float(retention_per_hour[province_position]) ** gaps
        )
        model.addConstr(
            state
            == predecessor_coefficients * predecessor
            + float(charge_efficiency[province_position])
            * charge[province_position, retained_hours]
            - discharge[province_position, retained_hours]
            / float(discharge_efficiency[province_position]),
            name=f"{name}_compressed_transition_p{province_position}",
        )
        model.addConstr(
            state
            <= float(positive_duration_hours[province_position])
            * capacity[province_position],
            name=f"{name}_compressed_positive_bound_p{province_position}",
        )
        cursor += count
    if cursor != int(retained.sum()):
        raise AssertionError(f"{name} retained-state indexing mismatch")


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
    # Province-specific parameters are stored as one-dimensional vectors.
    # Gurobi/NumPy would otherwise broadcast ``(p,)`` against ``(p, 1)`` to
    # ``(p, p)`` for the first-hour slice, silently creating cross-province
    # transition rows.  Normalise every such vector to a province column.
    def province_column(value: float | np.ndarray) -> float | np.ndarray:
        array = np.asarray(value)
        if array.ndim == 1:
            if array.shape[0] != state.shape[0]:
                raise ValueError(
                    f"{name} parameter length {array.shape[0]} does not match "
                    f"province count {state.shape[0]}"
                )
            return array[:, None]
        return value

    retention = province_column(retention)
    charge_efficiency = province_column(charge_efficiency)
    discharge_efficiency = province_column(discharge_efficiency)
    model.addConstr(
        state[:, 0:1]
        == retention * state[:, -1:]
        + charge_efficiency * charge[:, 0:1]
        - discharge[:, 0:1] / discharge_efficiency
        - withdrawal[:, 0:1],
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
    hour_start: int,
) -> FlexibleLoadBlock:
    """Attach the V4/V5 thermal-service and fleet-mobility formulation.

    V4 intentionally has no daily energy-conservation or daily-reset
    constraint.  Thermal and EV states are periodic over the selected
    chronological horizon, with the full-year case being the only scientific
    annual interpretation.  The loader validates every V4 input before this
    builder is reached.
    """
    service_data = data.flexible_load_v4
    if service_data is None:
        raise ValueError(
            "Service-constrained flexibility requires validated input data"
        )
    settings = config.raw["flexible_load"]
    v5_formulation = (
        str(settings.get("formulation")) == "integrated_service_constrained_v5"
    )
    expected_contract = "v5" if v5_formulation else "v4"
    if service_data.contract_version != expected_contract:
        raise ValueError(
            f"{expected_contract.upper()} formulation received "
            f"{service_data.contract_version.upper()} input data"
        )
    shape = baseline.shape
    p_count = shape[0]
    cell_count = int(np.prod(shape))
    if shape[1] != hours:
        raise ValueError("V4 load shape does not match requested horizon")

    hour_stop = int(hour_start) + int(hours)
    selected_hours = slice(int(hour_start), hour_stop)
    thermal_envelopes = {
        key: value[:, selected_hours]
        for key, value in service_data.thermal_envelopes_gw.items()
    }
    thermal_availability = {
        key: value[:, selected_hours]
        for key, value in service_data.thermal_availability.items()
    }
    ev_availability = {
        key: value[:, selected_hours]
        for key, value in service_data.ev_availability.items()
    }
    ev_mobility = {
        key: value[:, selected_hours]
        for key, value in service_data.ev_mobility.items()
    }
    variables: dict[str, Any] = {}
    structural_audit: dict[str, Any] = {
        "schema_version": "cispo_flexible_load_structural_audit_v2",
        "formulation": str(settings.get("formulation")),
        "contract_version": expected_contract,
        "province_count": int(p_count),
        "optimization_hours": int(hours),
        "optimization_start_hour": int(hour_start),
        "optimization_stop_hour_exclusive": int(hour_stop),
    }
    state_chain_numerical_risks = (
        _thermal_state_chain_numerical_risks(
            thermal_envelopes=thermal_envelopes,
            thermal_parameters=service_data.thermal_parameters,
            province_codes=data.provinces.province_code.to_numpy(
                dtype=int
            ),
            enforce_aggregate_zero=v5_formulation,
            compress_zero_control_states=v5_formulation,
        )
    )
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
    if v5_formulation:
        model.addConstr(
            capacity[:, 3] <= capacity[:, 2],
            name="v5_v2g_contract_nested_in_smart_charging",
        )
        national_cap = float(
            settings["ev_v2g"][
                "national_contracted_power_cap_gw_by_planning_year"
            ][str(config.planning_year)]
        )
        model.addConstr(
            capacity[:, 3].sum() <= national_cap,
            name="v5_v2g_national_contracted_power_cap",
        )

        firm_settings = settings["firm_capacity_credit"]
        derating = firm_settings["derating_fraction"]
        peak_hours = np.asarray(data.load_gw.argmax(axis=1), dtype=int)
        rows = np.arange(p_count, dtype=int)
        event_duration = float(
            firm_settings["required_event_duration_hours"]
        )
        event_hours_count = int(round(event_duration))
        event_offsets = np.arange(event_hours_count, dtype=int) - (
            (event_hours_count - 1) // 2
        )
        event_hours = (
            peak_hours[:, None] + event_offsets[None, :]
        ) % int(data.load_gw.shape[1])
        event_rows = rows[:, None]
        full_thermal_down = {
            component: service_data.thermal_envelopes_gw[
                f"{component}_down"
            ][event_rows, event_hours].min(axis=1)
            for component in ("heating", "cooling")
        }
        full_thermal_availability = {
            component: service_data.thermal_availability[component][
                event_rows, event_hours
            ].min(axis=1)
            for component in ("heating", "cooling")
        }
        full_flexible_ev_at_peak = (
            float(settings["ev_v1g"]["shiftable_energy_fraction"])
            * data.load_components_gw["ev"][
                event_rows, event_hours
            ].min(axis=1)
        )
        full_v2g_power_at_peak = service_data.ev_availability[
            "available_discharge_power_gw"
        ][event_rows, event_hours].min(axis=1)
        full_v2g_energy_at_peak = service_data.ev_availability[
            "fleet_energy_capacity_gwh"
        ][event_rows, event_hours].min(axis=1)

        firm_ub = np.zeros_like(capacity_ub)
        for column, component in enumerate(("heating", "cooling")):
            alpha = float(derating[component])
            firm_ub[:, column] = alpha * np.minimum(
                capacity_ub[:, column],
                full_thermal_down[component],
            )
        firm_ub[:, 2] = float(derating["ev_v1g"]) * np.minimum(
            capacity_ub[:, 2], full_flexible_ev_at_peak
        )
        firm_ub[:, 3] = float(derating["ev_v2g"]) * np.minimum.reduce(
            (
                capacity_ub[:, 3],
                full_v2g_power_at_peak,
                full_v2g_energy_at_peak / event_duration,
            )
        )
        firm_credit = model.addMVar(
            (p_count, len(V4_CAPACITY_SERVICES)),
            lb=0.0,
            ub=firm_ub,
            name="firm_flexible_capacity_credit_gw",
        )
        for column, component in enumerate(("heating", "cooling")):
            model.addConstr(
                firm_credit[:, column]
                <= float(derating[component])
                * full_thermal_availability[component]
                * capacity[:, column],
                name=f"v5_{component}_firm_credit_contract_bound",
            )
        model.addConstr(
            firm_credit[:, 2]
            <= float(derating["ev_v1g"]) * capacity[:, 2],
            name="v5_ev_v1g_firm_credit_contract_bound",
        )
        model.addConstr(
            firm_credit[:, 3]
            <= float(derating["ev_v2g"]) * capacity[:, 3],
            name="v5_ev_v2g_firm_credit_contract_bound",
        )
        variables["firm_flexible_capacity_credit"] = firm_credit
        variables["firm_flexible_capacity_credit_upper"] = firm_ub

    thermal_activation_terms: dict[str, Any] = {}
    thermal_fixed_zero_controls_omitted = 0
    thermal_fixed_zero_states_omitted = 0
    thermal_redundant_states_eliminated = 0
    for column, component in enumerate(("heating", "cooling")):
        params = service_data.thermal_parameters[component]
        up_ub = thermal_envelopes[f"{component}_up"]
        down_ub = thermal_envelopes[f"{component}_down"]
        availability = thermal_availability[component]
        k_service = capacity[:, column].reshape((p_count, 1))
        positive_duration = params["positive_state_duration_hours"]
        state_ub = np.broadcast_to(
            positive_duration[:, None] * capacity_ub[:, column, None], shape
        ).copy()
        if v5_formulation:
            up, up_active, up_active_mask = _add_sparse_hourly_control(
                model,
                upper_bound=up_ub,
                name=f"{component}_shift_up_gw",
            )
            down, down_active, down_active_mask = (
                _add_sparse_hourly_control(
                    model,
                    upper_bound=down_ub,
                    name=f"{component}_shift_down_gw",
                )
            )
        else:
            up = model.addMVar(
                shape,
                lb=0.0,
                ub=up_ub,
                name=f"{component}_shift_up_gw",
            )
            down = model.addMVar(
                shape,
                lb=0.0,
                ub=down_ub,
                name=f"{component}_shift_down_gw",
            )
            up_active = None
            down_active = None
            up_active_mask = np.ones(shape, dtype=bool)
            down_active_mask = np.ones(shape, dtype=bool)
        if v5_formulation:
            control_support = up_active_mask | down_active_mask
            (
                state,
                state_active,
                retained_state_mask,
                compressed_state_audit,
            ) = _add_compressed_thermal_state(
                model,
                upper_bound=state_ub,
                control_support=control_support,
                retention_per_hour=params["retention_per_hour"],
                name=f"{component}_state_gwh",
            )
            state_active_provinces = retained_state_mask.any(axis=1)
        else:
            state = model.addMVar(
                shape,
                lb=0.0,
                ub=state_ub,
                name=f"{component}_state_gwh",
            )
            state_active = state
            state_active_provinces = np.ones(p_count, dtype=bool)
            retained_state_mask = np.ones(shape, dtype=bool)
            compressed_state_audit = {
                "representation": "full_hourly_state_v4",
                "possible_state_variables": cell_count,
                "control_support_state_variables": cell_count,
                "decay_anchor_state_variables": 0,
                "retained_state_variables": cell_count,
                "redundant_inactive_state_variables_omitted": 0,
                "retained_transition_rows": cell_count,
                "redundant_inactive_transition_rows_omitted": 0,
                "maximum_retained_transition_gap_hours": 1,
                "minimum_retained_transition_coefficient": float(
                    np.min(params["retention_per_hour"])
                ),
                "mathematical_equivalence": "native_full_hourly_state",
            }
        if v5_formulation:
            if up_active is not None:
                up_provinces = np.nonzero(up_active_mask)[0]
                model.addConstr(
                    up_active
                    <= availability[up_active_mask]
                    * capacity[up_provinces, column],
                    name=f"{component}_contracted_increase_power",
                )
            if down_active is not None:
                down_provinces = np.nonzero(down_active_mask)[0]
                model.addConstr(
                    down_active
                    <= availability[down_active_mask]
                    * capacity[down_provinces, column],
                    name=f"{component}_contracted_reduction_power",
                )
        else:
            model.addConstr(
                up <= availability * k_service,
                name=f"{component}_contracted_increase_power",
            )
            model.addConstr(
                down <= availability * k_service,
                name=f"{component}_contracted_reduction_power",
            )
        if v5_formulation and state_active is not None:
            _attach_compressed_thermal_state_transitions(
                model,
                active_state=state_active,
                retained_state_mask=retained_state_mask,
                retention_per_hour=params["retention_per_hour"],
                charge=up,
                discharge=down,
                charge_efficiency=params["charge_efficiency"],
                discharge_efficiency=params["discharge_efficiency"],
                capacity=capacity[:, column],
                positive_duration_hours=positive_duration,
                name=f"{component}_state",
            )
        elif state_active is not None:
            active_count = int(state_active_provinces.sum())
            active_shape = (active_count, hours)
            active_capacity = capacity[state_active_provinces, column].reshape(
                (active_count, 1)
            )
            model.addConstr(
                state_active
                <= positive_duration[state_active_provinces, None]
                * active_capacity,
                name=f"{component}_positive_service_bound",
            )
            _periodic_transition(
                model,
                state=state_active,
                charge=up[state_active_provinces, :],
                discharge=down[state_active_provinces, :],
                withdrawal=np.zeros(active_shape, dtype=float),
                retention=params["retention_per_hour"][
                    state_active_provinces
                ],
                charge_efficiency=params["charge_efficiency"][
                    state_active_provinces
                ],
                discharge_efficiency=params["discharge_efficiency"][
                    state_active_provinces
                ],
                name=f"{component}_state",
            )
        actual_components[component] = components[component] + up - down
        variables.update(
            {
                f"{component}_shift_up": up,
                f"{component}_shift_down": down,
                f"{component}_state": state,
            }
        )
        thermal_activation_terms[component] = up.sum(axis=1) + down.sum(axis=1)
        structural_audit[f"{component}_sparse_hourly_control"] = {
            "possible_up_variables": cell_count,
            "active_up_variables": int(up_active_mask.sum()),
            "fixed_zero_up_variables_omitted": int(
                np.size(up_active_mask) - up_active_mask.sum()
            ),
            "possible_down_variables": int(np.prod(shape)),
            "active_down_variables": int(down_active_mask.sum()),
            "fixed_zero_down_variables_omitted": int(
                np.size(down_active_mask) - down_active_mask.sum()
            ),
        }
        redundant_state_variables = int(
            cell_count - retained_state_mask.sum()
        )
        fixed_zero_state_variables = int(
            (~state_active_provinces).sum() * hours
        )
        structural_audit[f"{component}_sparse_state"] = {
            **compressed_state_audit,
            "active_state_variables": int(retained_state_mask.sum()),
            "inactive_provinces_omitted": int(
                (~state_active_provinces).sum()
            ),
            "fixed_zero_state_variables_omitted": (
                fixed_zero_state_variables if v5_formulation else 0
            ),
            "redundant_state_variables_eliminated": (
                redundant_state_variables if v5_formulation else 0
            ),
            "redundant_state_bound_rows_omitted": (
                redundant_state_variables if v5_formulation else 0
            ),
            "redundant_state_transition_rows_omitted": (
                redundant_state_variables if v5_formulation else 0
            ),
        }
        structural_audit[f"{component}_state_chain_numerical_risk"] = {
            **state_chain_numerical_risks[component],
        }
        thermal_fixed_zero_controls_omitted += int(
            np.size(up_active_mask)
            - up_active_mask.sum()
            + np.size(down_active_mask)
            - down_active_mask.sum()
        )
        if v5_formulation:
            thermal_fixed_zero_states_omitted += (
                fixed_zero_state_variables
            )
            thermal_redundant_states_eliminated += (
                redundant_state_variables
            )

    ev_settings = settings["ev_v2g"]
    shiftable_fraction = float(settings["ev_v1g"]["shiftable_energy_fraction"])
    flexible_ev_baseline = shiftable_fraction * components["ev"]
    fixed_ev_baseline = components["ev"] - flexible_ev_baseline
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
    charge_deviation: Any | None = None
    if not v5_formulation:
        deviation_ub = charge_ub + components["ev"]
        charge_deviation = model.addMVar(
            shape,
            lb=0.0,
            ub=deviation_ub,
            name="ev_mobility_charge_deviation_gw",
        )
    v1g_relocated: Any = (
        model.addMVar(
            shape,
            lb=0.0,
            ub=flexible_ev_baseline,
            name="ev_mobility_v1g_relocated_gw",
        )
        if v5_formulation
        else _zero(shape)
    )
    k_charge = capacity[:, 2].reshape((p_count, 1))
    k_v2g = capacity[:, 3].reshape((p_count, 1))
    if v5_formulation and v2g_enabled:
        model.addConstr(
            charge + discharge <= connected * k_charge,
            name="v5_ev_shared_bidirectional_connection_power",
        )
        structural_audit["ev_shared_connection_power_contract"] = (
            "charge_plus_discharge_within_nested_smart_charging_contract_v1"
        )
    else:
        model.addConstr(
            charge <= connected * k_charge,
            name="ev_mobility_contracted_charge_power",
        )
        structural_audit["ev_shared_connection_power_contract"] = (
            "charge_only_legacy_contract"
        )
    if v2g_enabled:
        model.addConstr(
            discharge <= connected * k_v2g,
            name="ev_mobility_contracted_discharge_power",
        )
    minimum_departure_positive_mask = minimum_departure > 0.0
    minimum_departure_positive_cells = int(
        minimum_departure_positive_mask.sum()
    )
    if not v5_formulation:
        model.addConstr(soc >= minimum_departure, name="ev_mobility_departure_soc")
        departure_soc_constraint_rows_added = cell_count
    elif minimum_departure_positive_cells:
        model.addConstr(
            soc[minimum_departure_positive_mask]
            >= minimum_departure[minimum_departure_positive_mask],
            name="ev_mobility_departure_soc",
        )
        departure_soc_constraint_rows_added = (
            minimum_departure_positive_cells
        )
    else:
        departure_soc_constraint_rows_added = 0
    if charge_deviation is not None:
        model.addConstr(
            charge_deviation >= charge - flexible_ev_baseline,
            name="ev_mobility_charge_deviation_positive",
        )
        model.addConstr(
            charge_deviation >= flexible_ev_baseline - charge,
            name="ev_mobility_charge_deviation_negative",
        )
    if v5_formulation:
        model.addConstr(
            v1g_relocated >= flexible_ev_baseline - charge,
            name="ev_mobility_v1g_relocated_lower",
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
    actual_components["ev"] = fixed_ev_baseline + charge
    variables.update(
        ev_mobility_charge=charge,
        ev_mobility_discharge=discharge,
        ev_mobility_soc=soc,
        ev_mobility_v1g_relocated=v1g_relocated,
        # Compatibility aliases make the existing V2G output series usable,
        # while V4 still has one physical fleet SOC rather than a deviation
        # battery layered on top of V1G.
        ev_v2g_discharge=discharge,
        ev_v2g_soc=soc,
        ev_grid_charge_power_ub=fixed_ev_baseline + charge_ub,
    )
    if charge_deviation is not None:
        variables["ev_mobility_charge_deviation"] = charge_deviation

    effective_load = (
        actual_components["base_residual"]
        + actual_components["heating"]
        + actual_components["cooling"]
        + actual_components["ev"]
        - discharge
    )
    effective_load_lower_bound = _service_effective_load_lower_bound(
        components=components,
        thermal_down_upper={
            component: thermal_envelopes[f"{component}_down"]
            for component in ("heating", "cooling")
        },
        fixed_ev_baseline=fixed_ev_baseline,
        ev_discharge_upper=(
            discharge_ub if v2g_enabled else np.zeros(shape, dtype=float)
        ),
    )
    effective_load_redundancy_safety_margin_gw = 1e-6
    effective_load_requires_explicit_row = (
        effective_load_lower_bound
        < effective_load_redundancy_safety_margin_gw
    )
    if not v5_formulation:
        model.addConstr(effective_load >= 0.0, name="effective_load_nonnegative")
        effective_load_nonnegative_constraint_rows_added = cell_count
    elif effective_load_requires_explicit_row.any():
        model.addConstr(
            effective_load[effective_load_requires_explicit_row] >= 0.0,
            name="effective_load_nonnegative",
        )
        effective_load_nonnegative_constraint_rows_added = int(
            effective_load_requires_explicit_row.sum()
        )
    else:
        effective_load_nonnegative_constraint_rows_added = 0
    effective_load_naturally_nonnegative = (
        effective_load_nonnegative_constraint_rows_added == 0
    )
    departure_soc_constraint_rows_omitted = (
        cell_count - departure_soc_constraint_rows_added
        if v5_formulation
        else 0
    )
    effective_load_nonnegative_constraint_rows_omitted = (
        cell_count - effective_load_nonnegative_constraint_rows_added
        if v5_formulation
        else 0
    )
    structural_audit.update(
        {
            "ev_charge_deviation_representation": (
                "postsolve_derived_absolute_deviation"
                if v5_formulation
                else "optimization_epigraph_variable"
            ),
            "ev_charge_deviation_variables_omitted": (
                cell_count if v5_formulation else 0
            ),
            "ev_charge_deviation_constraints_omitted": (
                2 * cell_count if v5_formulation else 0
            ),
            "minimum_departure_energy_min_gwh": float(
                np.min(minimum_departure)
            ),
            "minimum_departure_energy_max_gwh": float(
                np.max(minimum_departure)
            ),
            "minimum_departure_positive_cells": (
                minimum_departure_positive_cells
            ),
            "departure_soc_constraint_rows_added": (
                departure_soc_constraint_rows_added
            ),
            "departure_soc_constraint_rows_omitted_as_redundant": (
                departure_soc_constraint_rows_omitted
            ),
            "effective_load_static_lower_bound_min_gw": float(
                np.min(effective_load_lower_bound)
            ),
            "effective_load_redundancy_safety_margin_gw": (
                effective_load_redundancy_safety_margin_gw
            ),
            "effective_load_naturally_nonnegative": (
                effective_load_naturally_nonnegative
            ),
            "effective_load_nonnegative_enforcement": (
                "inherent_static_lower_bound"
                if v5_formulation and effective_load_naturally_nonnegative
                else (
                    "sparse_explicit_constraint_rows"
                    if v5_formulation
                    else "explicit_constraint_rows"
                )
            ),
            "effective_load_nonnegative_constraint_rows_added": (
                effective_load_nonnegative_constraint_rows_added
            ),
            "effective_load_nonnegative_constraint_rows_omitted": (
                effective_load_nonnegative_constraint_rows_omitted
            ),
            "redundant_raw_variables_omitted": (
                cell_count
                + thermal_fixed_zero_controls_omitted
                + thermal_redundant_states_eliminated
                if v5_formulation
                else 0
            ),
            "net_raw_variables_removed": (
                cell_count
                + thermal_fixed_zero_controls_omitted
                + thermal_redundant_states_eliminated
                if v5_formulation
                else 0
            ),
            "thermal_fixed_zero_raw_variables_omitted": (
                thermal_fixed_zero_controls_omitted
                if v5_formulation
                else 0
            ),
            "thermal_fixed_zero_state_variables_omitted": (
                thermal_fixed_zero_states_omitted
                if v5_formulation
                else 0
            ),
            "thermal_redundant_state_variables_eliminated": (
                thermal_redundant_states_eliminated
                if v5_formulation
                else 0
            ),
            "thermal_tautological_contracted_power_rows_omitted": (
                thermal_fixed_zero_controls_omitted
                if v5_formulation
                else 0
            ),
            "redundant_raw_constraint_rows_omitted": (
                (2 * cell_count if v5_formulation else 0)
                + departure_soc_constraint_rows_omitted
                + effective_load_nonnegative_constraint_rows_omitted
                + (
                    thermal_fixed_zero_controls_omitted
                    if v5_formulation
                    else 0
                )
                + (
                    2 * thermal_redundant_states_eliminated
                    if v5_formulation
                    else 0
                )
            ),
            "net_raw_constraint_rows_removed": (
                (
                    (2 * cell_count)
                    + departure_soc_constraint_rows_omitted
                    + effective_load_nonnegative_constraint_rows_omitted
                    + thermal_fixed_zero_controls_omitted
                    + 2 * thermal_redundant_states_eliminated
                )
                if v5_formulation
                else 0
            ),
        }
    )
    variables.update(
        effective_load=effective_load,
        actual_heating_load=actual_components["heating"],
        actual_cooling_load=actual_components["cooling"],
        actual_ev_load=actual_components["ev"],
        ev_v2g_charge=_zero(shape),
    )

    service_costs = service_data.service_costs
    enablement_cost = gp.quicksum(
        (
            service_costs[service]["enablement_cost_yuan_per_kw_year"]
            * capacity[:, column]
        ).sum()
        for column, service in enumerate(V4_CAPACITY_SERVICES)
    )
    thermal_activation_cost = gp.quicksum(
        (
            1e-3
            * service_costs[component]["activation_cost_yuan_per_mwh"]
            * thermal_activation_terms[component]
        ).sum()
        for component in ("heating", "cooling")
    )
    thermal_comfort_cost = gp.LinExpr(0.0)
    if v5_formulation:
        ev_relocation_measure = v1g_relocated
    else:
        if charge_deviation is None:
            raise AssertionError("V4 charge-deviation variable was not created")
        ev_relocation_measure = charge_deviation
    ev_relocation_cost = (
        (
            1e-3
            * service_costs["ev_v1g"]["activation_cost_yuan_per_mwh"]
            * ev_relocation_measure.sum(axis=1)
        ).sum()
    )
    ev_v2g_participation_cost = (
        (
            1e-3
            * service_costs["ev_v2g"]["activation_cost_yuan_per_mwh"]
            * discharge.sum(axis=1)
        ).sum()
        if v2g_enabled
        else gp.LinExpr(0.0)
    )
    ev_v2g_infrastructure_cost = (
        (
            service_costs["ev_v2g"][
                "infrastructure_cost_yuan_per_kw_year"
            ]
            * capacity[:, 3]
        ).sum()
        if v5_formulation
        else gp.LinExpr(0.0)
    )
    ev_v2g_degradation_cost = (
        (
            1e-3
            * service_costs["ev_v2g"]["degradation_cost_yuan_per_mwh"]
            * discharge.sum(axis=1)
        ).sum()
        if v5_formulation
        else gp.LinExpr(0.0)
    )
    if v5_formulation:
        costs = {
            "flexible_load_v5_enablement": enablement_cost,
            "flexible_load_v5_v2g_infrastructure": (
                ev_v2g_infrastructure_cost
            ),
            "flexible_load_v5_thermal_activation": thermal_activation_cost,
            "flexible_load_v5_ev_v1g_relocation": ev_relocation_cost,
            "flexible_load_v5_ev_v2g_participation": (
                ev_v2g_participation_cost
            ),
            "flexible_load_v5_ev_v2g_degradation": (
                ev_v2g_degradation_cost
            ),
        }
    else:
        costs = {
            "flexible_load_v4_enablement": enablement_cost,
            "flexible_load_v4_thermal_activation": thermal_activation_cost,
            "flexible_load_v4_comfort_debt": thermal_comfort_cost,
            "flexible_load_v4_ev_v1g_relocation": ev_relocation_cost,
            "flexible_load_v4_ev_v2g_discharge": (
                ev_v2g_participation_cost
            ),
        }
    return FlexibleLoadBlock(
        effective_load_gw=effective_load,
        baseline_load_gw=baseline,
        actual_components_gw=actual_components,
        variables=variables,
        costs=costs,
        day_slices=day_slices,
        structural_audit=structural_audit,
    )


def attach_flexible_load(
    model: gp.Model,
    config: ModelConfig,
    data: ModelData,
    *,
    hours: int,
    hour_start: int = 0,
) -> FlexibleLoadBlock:
    """Attach optional demand flexibility and return the effective hourly load."""
    hour_start = int(hour_start)
    hour_stop = hour_start + int(hours)
    if hour_start < 0 or hour_stop > data.load_gw.shape[1]:
        raise ValueError("Flexible-load time window is outside the model year")
    selected_hours = slice(hour_start, hour_stop)
    baseline = data.load_gw[:, selected_hours]
    components = {
        name: values[:, selected_hours]
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
    if formulation in {
        "service_constrained_v4",
        "integrated_service_constrained_v5",
    }:
        return _attach_service_constrained_v4(
            model,
            config,
            data,
            baseline=baseline,
            components=components,
            day_slices=day_slices,
            hours=hours,
            hour_start=hour_start,
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
                    :, selected_hours
                ]
                down_ub = data.flexible_load_envelopes_gw[f"{component}_down"][
                    :, selected_hours
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
