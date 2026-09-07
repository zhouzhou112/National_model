"""Explicit response-contract refinements; no solver or input-file mutation.

Hourly powers are GW. Participation is an exogenous fraction of the existing
V5 eligible pool, not a measured national vehicle/building participation rate.
"""
from __future__ import annotations

from math import erf, isfinite, sqrt
import numpy as np

RESPONSE_CONTRACT = "proportional_enrollment_response_v1"
SERVICES = ("heating", "cooling", "ev_v1g", "ev_v2g")
COST_FIELDS = (
    "enablement_cost_yuan_per_kw_year", "activation_cost_yuan_per_mwh",
    "infrastructure_cost_yuan_per_kw_year", "degradation_cost_yuan_per_mwh",
)


def response_settings(settings: dict) -> dict:
    return settings.get("response_contract", {})


def validate_response_contract(settings: dict) -> None:
    response = response_settings(settings)
    if not response:
        return
    if (settings.get("formulation") != "integrated_service_constrained_v5"
            or settings.get("portfolio_contract") != "optional_service_pools_v1"):
        raise ValueError("response_contract requires optional V5 service pools")
    if not isinstance(response, dict) or response.get("version") != RESPONSE_CONTRACT:
        raise ValueError("Unknown response_contract version")
    allowed = {"version", "maximum_enrollment_fraction", "v2g_infrastructure_fraction",
               "cost_multipliers"}
    if set(response) - allowed:
        raise ValueError("Unknown response_contract fields")
    fractions = response.get("maximum_enrollment_fraction", {})
    if not isinstance(fractions, dict) or set(fractions) - set(SERVICES):
        raise ValueError("Unknown enrollment service")
    for key, value in {**fractions, "infrastructure": response.get("v2g_infrastructure_fraction", 1)}.items():
        if isinstance(value, bool) or not isfinite(float(value)) or not 0 <= float(value) <= 1:
            raise ValueError(f"Response fraction {key} must be finite in [0, 1]")
    multipliers = response.get("cost_multipliers", {})
    if not isinstance(multipliers, dict) or set(multipliers) - set(SERVICES):
        raise ValueError("Unknown cost multiplier service")
    for service, fields in multipliers.items():
        if not isinstance(fields, dict) or set(fields) - set(COST_FIELDS):
            raise ValueError(f"Unknown cost multiplier field for {service}")
        for value in fields.values():
            if isinstance(value, bool) or not isfinite(float(value)) or float(value) <= 0:
                raise ValueError("Cost multipliers must be finite and positive")


def enrollment_limit(settings: dict, service: str) -> float:
    return float(response_settings(settings).get("maximum_enrollment_fraction", {}).get(service, 1))


def infrastructure_limit(settings: dict) -> float:
    return float(response_settings(settings).get("v2g_infrastructure_fraction", 1))


def thermal_contract_profile(up: np.ndarray, down: np.ndarray,
                             availability: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Annual K0 and dimensionless U/K0, D/K0; zeros remain exact zeros.

K0=max_t(max(U,D)/a). Thus normalized coefficients are at most a<=1.
No inverse-capacity coefficient is inserted into the LP.
"""
    up, down, availability = (np.asarray(x, dtype=float) for x in (up, down, availability))
    if (up.ndim != 2 or not up.shape[1] or up.shape != down.shape or up.shape != availability.shape
            or not all(np.isfinite(x).all() for x in (up, down, availability))
            or min(up.min(), down.min(), availability.min()) < 0 or availability.max() > 1):
        raise ValueError("Invalid full-year thermal response arrays")
    power = np.maximum(up, down)
    if np.any((availability == 0) & (power > 0)):
        raise ValueError("Thermal response requires nonzero availability")
    annual = np.divide(power, availability, out=np.zeros_like(power), where=availability > 0).max(axis=1)
    coefficients = [np.divide(x, annual[:, None], out=np.zeros_like(x), where=annual[:, None] > 0)
                    for x in (up, down)]
    if not np.isfinite(annual).all() or any(not np.isfinite(x).all() for x in coefficients):
        raise ValueError("Nonfinite thermal normalization")
    return annual, *coefficients


def resolved_service_costs(settings: dict, service_costs: dict) -> dict:
    """Apply declared real-cost sensitivity factors without changing source tables."""
    multipliers = response_settings(settings).get("cost_multipliers", {})
    if not multipliers:
        return service_costs
    resolved = {service: {key: np.asarray(value) * float(multipliers.get(service, {}).get(key, 1))
                         for key, value in fields.items()} for service, fields in service_costs.items()}
    if any(not np.isfinite(value).all() for fields in resolved.values() for value in fields.values()):
        raise ValueError("Nonfinite resolved response cost")
    return resolved


def normal_participation_fraction(gamma: float, coefficient_of_variation: float = .5) -> float:
    """Analytic expectation of paper Eq.47, without clipping negative draws.

This is a transparent distributional sensitivity, not calibrated China data.
"""
    if not isfinite(gamma) or gamma < 0 or not isfinite(coefficient_of_variation) or coefficient_of_variation <= 0:
        raise ValueError("Invalid willingness distribution parameters")
    return .5 * (1 + erf((gamma - 1) / (coefficient_of_variation * sqrt(2))))


def audit_thermal_response(settings: dict, *, component: str, full_up: np.ndarray,
                           full_down: np.ndarray, full_availability: np.ndarray,
                           selected_hours: slice, capacity: np.ndarray,
                           up: np.ndarray, down: np.ndarray) -> dict[str, float]:
    if not response_settings(settings):
        return {}
    annual, up_coeff, down_coeff = thermal_contract_profile(full_up, full_down, full_availability)
    positive = lambda x: float(np.maximum(x, 0).max(initial=0))
    enabled = bool(settings[component]["enabled"])
    return {
        f"{component}_proportional_up_violation_gw": positive(up - up_coeff[:, selected_hours] * capacity[:, None]),
        f"{component}_proportional_down_violation_gw": positive(down - down_coeff[:, selected_hours] * capacity[:, None]),
        f"{component}_enrollment_cap_violation_gw": positive(capacity - annual * enrollment_limit(settings, component) * enabled),
    }
