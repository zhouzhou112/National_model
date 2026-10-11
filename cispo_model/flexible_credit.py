"""Author-authorized four-hour accreditation of optional service pools.

This is an engineering capacity credit, not an ELCC or event dispatch model.
All bounds use the immutable full-year peak window and enrolled resources.
"""
from __future__ import annotations
import numpy as np

AUTHORIZATION = "author_2026_10_11_derated_credit_v1"
SERVICES = ("heating", "cooling", "ev_v1g", "ev_v2g")


def enabled(config):
    return (config.raw["security"]["capacity_margin_load_basis"] == "firm_flexibility_derated_v1"
            and config.raw["flexible_load"].get("portfolio_contract") == "optional_service_pools_v1"
            and config.raw["flexible_load"]["firm_capacity_credit"].get("optional_portfolio_authorization") == AUTHORIZATION)


def peak_limits(settings, data):
    service = data.flexible_load_v4
    firm = settings["firm_capacity_credit"]
    duration = int(firm["required_event_duration_hours"])
    peak = data.load_gw.argmax(axis=1)
    hours = (peak[:, None] + np.arange(duration)[None, :] - (duration - 1)//2) % data.load_gw.shape[1]
    rows = np.arange(len(peak))[:, None]
    minimum = lambda values: values[rows, hours].min(axis=1)
    return dict(
        thermal=np.column_stack([minimum(service.thermal_envelopes_gw[c+"_down"]) for c in SERVICES[:2]]),
        availability=np.column_stack([minimum(service.thermal_availability[c]) for c in SERVICES[:2]]),
        ev_baseline=float(settings["ev_v1g"]["shiftable_energy_fraction"])*minimum(data.load_components_gw["ev"]),
        discharge=minimum(service.ev_availability["available_discharge_power_gw"]),
        energy=minimum(service.ev_availability["fleet_energy_capacity_gwh"])/duration,
    )


def attach_optional_credit(model, config, data, variables):
    settings = config.raw["flexible_load"]
    limits = peak_limits(settings, data)
    capacity = variables["flexible_service_capacity"]
    alpha = variables["ev_enrolled_service_fraction"]
    beta = variables["ev_bidirectional_service_fraction"]
    rho = float(settings["ev_v2g"]["participation_fraction"])/float(settings["ev_v1g"]["shiftable_energy_fraction"])
    credit = model.addMVar(capacity.shape, lb=0, name="firm_flexible_capacity_credit_gw")
    derating = settings["firm_capacity_credit"]["derating_fraction"]
    for j, name in enumerate(SERVICES):
        factor = float(derating[name])
        availability = limits["availability"][:, j] if j < 2 else 1.0
        model.addConstr(credit[:, j] <= factor*availability*capacity[:, j], name=f"v5_{name}_firm_credit_contract_bound")
        if j < 2:
            model.addConstr(credit[:, j] <= factor*limits["thermal"][:, j], name=f"v5_{name}_firm_credit_peak_bound")
        elif j == 2:
            model.addConstr(credit[:, j] <= factor*limits["ev_baseline"]*alpha, name="v5_ev_v1g_firm_credit_enrolled_peak")
        else:
            model.addConstr(credit[:, j] <= factor*limits["discharge"]/rho*beta, name="v5_ev_v2g_firm_credit_enrolled_power")
            model.addConstr(credit[:, j] <= factor*limits["energy"]*beta, name="v5_ev_v2g_firm_credit_enrolled_energy")
    variables["firm_flexible_capacity_credit"] = credit
    # Finite conservative static bound retained for legacy export/QC interfaces.
    upper = np.column_stack((limits["thermal"], limits["ev_baseline"],
                             np.minimum(limits["discharge"], limits["energy"]*rho)))
    upper *= np.array([derating[s] for s in SERVICES])
    variables["firm_flexible_capacity_credit_upper"] = upper


def audit_optional_credit(settings, data, capacity, alpha, beta, credit):
    limits = peak_limits(settings, data)
    rho = float(settings["ev_v2g"]["participation_fraction"])/float(settings["ev_v1g"]["shiftable_energy_fraction"])
    upper = np.asarray(capacity).copy()
    upper[:, :2] = np.minimum(upper[:, :2]*limits["availability"], limits["thermal"])
    upper[:, 2] = np.minimum(upper[:, 2], limits["ev_baseline"]*np.asarray(alpha))
    upper[:, 3] = np.minimum.reduce([upper[:, 3], limits["discharge"]/rho*np.asarray(beta), limits["energy"]*np.asarray(beta)])
    upper *= np.array([settings["firm_capacity_credit"]["derating_fraction"][s] for s in SERVICES])
    positive = lambda v: float(np.maximum(v, 0).max(initial=0))
    zero = np.asarray(capacity) <= 0
    zero[:, 2] |= np.asarray(alpha) <= 0
    zero[:, 3] |= np.asarray(beta) <= 0
    return {"firm_credit_bound_violation_gw": max(positive(credit-upper), positive(-np.asarray(credit))),
            "firm_credit_zero_when_unenrolled": positive(np.asarray(credit)[zero])}
