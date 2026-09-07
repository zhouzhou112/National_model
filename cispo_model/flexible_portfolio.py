"""Opt-in V5 contracting of disjoint, proportional EV service pools.

Power is GW, inventory GWh and each step one hour. Fractions refer to the
existing V5 eligible service pool, not observed vehicles or measured SOC.
No binary variables, products of decisions, or inverse capacity coefficients.
"""
from __future__ import annotations

from typing import Any, Callable

import gurobipy as gp
import numpy as np

from .flexible_response import enrollment_limit, infrastructure_limit, response_settings

PORTFOLIO_CONTRACT = "optional_service_pools_v1"


def is_optional_portfolio(settings: dict) -> bool:
    return settings.get("portfolio_contract") == PORTFOLIO_CONTRACT


def attach_ev_pools(
    model: gp.Model, *, settings: dict, baseline_ev: np.ndarray,
    availability: dict, mobility: dict, full_availability: dict,
    capacity: Any, periodic_transition: Callable,
) -> dict[str, Any]:
    """Separate V1G-only and V2G participants; zero enrollment is Base."""
    shape = baseline_ev.shape
    p_count = shape[0]
    zero = np.zeros(shape)
    zero_p = np.zeros(p_count)
    fraction = float(settings["ev_v1g"]["shiftable_energy_fraction"])
    eligible = fraction * baseline_ev
    enabled = bool(settings["ev_v1g"]["enabled"])
    v2g_enabled = bool(settings["ev_v2g"]["enabled"])
    rho = (float(settings["ev_v2g"]["participation_fraction"]) / fraction
           if v2g_enabled else 0.0)
    power = availability["available_charge_power_gw"]
    discharge_power = availability["available_discharge_power_gw"]
    energy = availability["fleet_energy_capacity_gwh"]
    withdrawal = mobility["driving_energy_withdrawal_gwh"]
    departure = mobility["minimum_departure_energy_gwh"]
    # Full-year constants keep enrollment identities invariant in window tests.
    p_max = full_availability["available_charge_power_gw"].max(axis=1)
    d_max = full_availability["available_discharge_power_gw"].max(axis=1)
    alpha: Any = zero_p
    beta: Any = zero_p
    c1: Any = zero
    c2: Any = zero
    s1: Any = zero
    s2: Any = zero
    d: Any = zero
    relocated: Any = zero
    if enabled:
        alpha = model.addMVar(p_count, lb=0, ub=(p_max > 0).astype(float) * enrollment_limit(settings, "ev_v1g"),
                             name="ev_enrolled_service_fraction")
        model.addConstr(capacity[:, 2] == p_max * alpha,
                        name="ev_enrollment_charge_contract")
        if v2g_enabled:
            beta = model.addMVar(p_count, lb=0, ub=rho * (d_max > 0) * infrastructure_limit(settings),
                                name="ev_bidirectional_service_fraction")
            model.addConstr(beta <= rho * enrollment_limit(settings, "ev_v2g") * alpha,
                            name="ev_pool_participation_nesting")
            model.addConstr(capacity[:, 3] == (d_max / rho) * beta,
                            name="ev_enrollment_v2g_contract")
        one_way = alpha.reshape((p_count, 1)) - beta.reshape((p_count, 1))
        two_way = beta.reshape((p_count, 1))
        c1 = model.addMVar(shape, lb=0, ub=power, name="ev_v1g_pool_charge_gw")
        s1 = model.addMVar(shape, lb=0, ub=energy, name="ev_v1g_pool_inventory_gwh")
        model.addConstr(c1 <= power * one_way, name="ev_v1g_pool_charge_bound")
        model.addConstr(s1 <= energy * one_way, name="ev_v1g_pool_inventory_bound")
        if np.any(departure > 0):
            mask = departure > 0
            model.addConstr(s1[mask] >= (departure * one_way)[mask], name="ev_v1g_pool_departure")
        ev = settings["ev_v2g"]
        transition_args = dict(
            retention=1 - float(ev["self_discharge_fraction_per_hour"]),
            charge_efficiency=float(ev["charge_efficiency"]),
            discharge_efficiency=float(ev["discharge_efficiency"]),
        )
        periodic_transition(model, state=s1, charge=c1, discharge=zero,
                            withdrawal=withdrawal * one_way,
                            name="ev_v1g_pool", **transition_args)
        if v2g_enabled:
            c2 = model.addMVar(shape, lb=0, ub=power * rho, name="ev_v2g_pool_charge_gw")
            s2 = model.addMVar(shape, lb=0, ub=energy * rho, name="ev_v2g_pool_inventory_gwh")
            d = model.addMVar(shape, lb=0, ub=discharge_power, name="ev_mobility_discharge_gw")
            # A bidirectional participant cannot consume both interface ratings.
            # Aggregated counterflows across distinct participants remain LP-feasible.
            model.addConstr(c2 + d <= power * two_way, name="ev_v2g_pool_shared_connection")
            model.addConstr(d <= (discharge_power / rho) * two_way,
                            name="ev_v2g_pool_discharge_bound")
            model.addConstr(s2 <= energy * two_way, name="ev_v2g_pool_inventory_bound")
            if np.any(departure > 0):
                mask = departure > 0
                model.addConstr(s2[mask] >= (departure * two_way)[mask], name="ev_v2g_pool_departure")
            periodic_transition(model, state=s2, charge=c2, discharge=d,
                                withdrawal=withdrawal * two_way,
                                name="ev_v2g_pool", **transition_args)
        enrolled_baseline = eligible * alpha.reshape((p_count, 1))
        relocated = model.addMVar(shape, lb=0, ub=eligible,
                                 name="ev_mobility_v1g_relocated_gw")
        model.addConstr(relocated >= enrolled_baseline - c1 - c2,
                        name="ev_mobility_v1g_relocated_lower")
    else:
        enrolled_baseline = zero
    return dict(
        charge=c1 + c2, discharge=d, soc=s1 + s2, relocated=relocated,
        fixed_baseline=baseline_ev - enrolled_baseline,
        # A numeric worst-case lower bound, independent of decisions.
        fixed_baseline_lower=baseline_ev - eligible if enabled else baseline_ev,
        charge_upper=power if enabled else zero,
        discharge_upper=discharge_power if v2g_enabled else zero,
        extra_variables=dict(
            ev_enrolled_service_fraction=alpha,
            ev_bidirectional_service_fraction=beta,
            ev_v1g_pool_charge=c1, ev_v2g_pool_charge=c2,
            ev_v1g_pool_inventory=s1, ev_v2g_pool_inventory=s2,
        ),
    )


def audit_ev_pools(*, settings: dict, baseline_ev: np.ndarray, availability: dict,
                   full_availability: dict, mobility: dict, values: dict,
                   capacity: np.ndarray) -> dict[str, float]:
    """Independent postsolve checks of both pools, in original physical units."""
    alpha = np.asarray(values["ev_enrolled_service_fraction"]).reshape((-1, 1))
    beta = np.asarray(values["ev_bidirectional_service_fraction"]).reshape((-1, 1))
    rho = (float(settings["ev_v2g"]["participation_fraction"])
           / float(settings["ev_v1g"]["shiftable_energy_fraction"])
           if settings["ev_v2g"]["enabled"] else 0.0)
    ev = settings["ev_v2g"]
    ec, ed = float(ev["charge_efficiency"]), float(ev["discharge_efficiency"])
    retention = 1 - float(ev["self_discharge_fraction_per_hour"])
    power = availability["available_charge_power_gw"]
    energy = availability["fleet_energy_capacity_gwh"]
    withdrawal = mobility["driving_energy_withdrawal_gwh"]
    departure = mobility["minimum_departure_energy_gwh"]
    c1, c2 = values["ev_v1g_pool_charge"], values["ev_v2g_pool_charge"]
    s1, s2 = values["ev_v1g_pool_inventory"], values["ev_v2g_pool_inventory"]
    discharge = values["ev_mobility_discharge"]
    positive = lambda x: float(np.maximum(np.asarray(x), 0).max(initial=0))
    absolute = lambda x: float(np.abs(np.asarray(x)).max(initial=0))
    metrics = {
        "enrollment_fraction_violation": max(positive(-alpha), positive(alpha - 1),
                                               positive(-beta), positive(beta - rho * alpha)),
        "contract_charge_residual_gw": absolute(capacity[:, 2] - alpha[:, 0] *
            full_availability["available_charge_power_gw"].max(axis=1)),
        "contract_v2g_residual_gw": absolute(capacity[:, 3] - (beta[:, 0] / rho *
            full_availability["available_discharge_power_gw"].max(axis=1) if rho else 0)),
        "discharge_pool_power_violation_gw": positive(discharge - (
            availability["available_discharge_power_gw"] * beta / rho if rho else 0)),
    }
    for name, share, charge, state, out in (
        ("v1g", alpha - beta, c1, s1, np.zeros_like(discharge)),
        ("v2g", beta, c2, s2, discharge),
    ):
        metrics[f"{name}_transition_residual_gwh"] = absolute(
            state - retention * np.roll(state, 1, axis=1) - ec * charge + out / ed
            + withdrawal * share)
        metrics[f"{name}_inventory_violation_gwh"] = max(
            positive(-state), positive(state - energy * share), positive(departure * share - state))
        metrics[f"{name}_connection_violation_gw"] = max(
            positive(-charge), positive(charge + out - power * share))
    eligible = float(settings["ev_v1g"]["shiftable_energy_fraction"]) * baseline_ev
    metrics["baseline_reconstruction_residual_gw"] = absolute(
        values["actual_ev_load"] - (baseline_ev - alpha * eligible + c1 + c2))
    metrics["relocation_lower_bound_violation_gw"] = positive(
        alpha * eligible - c1 - c2 - values["ev_mobility_v1g_relocated"])
    if not settings["ev_v1g"]["enabled"]:
        metrics["disabled_enrollment_violation"] = absolute(alpha)
    if response_settings(settings):
        metrics["response_v1g_enrollment_violation"] = positive(alpha - enrollment_limit(settings, "ev_v1g"))
        metrics["response_v2g_willingness_violation"] = positive(beta - rho * enrollment_limit(settings, "ev_v2g") * alpha)
        metrics["response_v2g_infrastructure_violation"] = positive(beta - rho * infrastructure_limit(settings))
    return metrics


def estimate_portfolio_size(settings: dict, data, hours: int) -> tuple[int, int]:
    """Leading-window raw flexible-block counts, excluding the system LP."""
    from .flexible_load_numerics import _compressed_thermal_state_mask
    service = data.flexible_load_v4
    p = len(data.provinces)
    cells = p*hours
    variables, rows = 4*p, p+1  # service contracts, nesting and national cap
    lower = data.load_gw[:, :hours].copy()
    for component in ('heating', 'cooling'):
        if not settings[component]['enabled']:
            continue
        up = service.thermal_envelopes_gw[f'{component}_up'][:, :hours]
        down = service.thermal_envelopes_gw[f'{component}_down'][:, :hours]
        support = (up > 0) | (down > 0)
        retained = _compressed_thermal_state_mask(support,
            service.thermal_parameters[component]['retention_per_hour'])
        controls = int((up > 0).sum() + (down > 0).sum())
        variables += controls + int(retained.sum())
        rows += controls + 2*int(retained.sum()) + int(support.sum())
        lower -= down
    if settings['ev_v1g']['enabled']:
        variables += p + 3*cells
        rows += p + 4*cells
        lower -= float(settings['ev_v1g']['shiftable_energy_fraction'])*data.load_components_gw['ev'][:, :hours]
        departure_rows = int((service.ev_mobility['minimum_departure_energy_gwh'][:, :hours] > 0).sum())
        rows += departure_rows
        if settings['ev_v2g']['enabled']:
            variables += p + 3*cells
            rows += 2*p + 4*cells + departure_rows
            lower -= service.ev_availability['available_discharge_power_gw'][:, :hours]
    rows += int((lower < 1e-6).sum())
    return variables, rows
