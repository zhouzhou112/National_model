"""Optional linear demand-flexibility blocks for decomposed provincial load.

The baseline load remains immutable. Heating, cooling and EV charging are
reintroduced as transparent hourly expressions whose energy is conserved in
each Beijing-time day. V2G is an incremental daily-cyclic virtual-storage
envelope and therefore never substitutes for the exogenous driving-energy
service embedded in the EV baseline.
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


def _zero(shape: tuple[int, int]) -> np.ndarray:
    return np.zeros(shape, dtype=float)


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
    variables: dict[str, Any] = {}
    shift_terms: list[Any] = []
    actual_components: dict[str, Any] = {
        "base_residual": components["base_residual"]
    }

    for component in ("heating", "cooling"):
        component_settings = settings[component]
        component_baseline = components[component]
        if bool(component_settings["enabled"]):
            up_ub, down_ub = _thermal_shift_bounds(
                component_baseline,
                day_slices,
                float(component_settings["maximum_reduction_fraction"]),
                float(component_settings["maximum_increase_fraction_of_daily_peak"]),
            )
            up = model.addMVar(shape, lb=0.0, ub=up_ub, name=f"{component}_shift_up_gw")
            down = model.addMVar(
                shape, lb=0.0, ub=down_ub, name=f"{component}_shift_down_gw"
            )
            for day_number, day in enumerate(day_slices):
                model.addConstr(
                    up[:, day].sum(axis=1) == down[:, day].sum(axis=1),
                    name=f"{component}_daily_energy_conservation_d{day_number}",
                )
            actual_components[component] = component_baseline + up - down
            variables[f"{component}_shift_up"] = up
            variables[f"{component}_shift_down"] = down
            shift_terms.extend((up.sum(), down.sum()))
        else:
            actual_components[component] = component_baseline

    ev_settings = settings["ev_v1g"]
    ev_baseline = components["ev"]
    if bool(ev_settings["enabled"]):
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
        for day_number, day in enumerate(day_slices):
            model.addConstr(
                ev_up[:, day].sum(axis=1) == ev_down[:, day].sum(axis=1),
                name=f"ev_v1g_daily_energy_conservation_d{day_number}",
            )
        actual_components["ev"] = ev_baseline + ev_up - ev_down
        variables.update(ev_v1g_shift_up=ev_up, ev_v1g_shift_down=ev_down)
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
        participation = float(v2g_settings["participation_fraction"])
        energy_ratio = float(v2g_settings["usable_energy_to_daily_ev_energy_ratio"])
        duration = float(v2g_settings["power_duration_hours"])
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
        ev_v2g_charge=v2g_charge,
        ev_v2g_discharge=v2g_discharge,
        ev_v2g_soc=v2g_soc,
    )

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
    return FlexibleLoadBlock(
        effective_load_gw=effective_load,
        baseline_load_gw=baseline,
        actual_components_gw=actual_components,
        variables=variables,
        costs={
            "flexible_load_shift_throughput": shift_cost,
            "ev_v2g_degradation": degradation_cost,
        },
        day_slices=day_slices,
    )
