"""Pure numerical guards for service-constrained flexible load.

This module deliberately has no Gurobi dependency.  Full-year preflight can
therefore evaluate structural lower bounds and solver-profile compatibility
before allocating the LP or importing the optimizer runtime.
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from .config import ModelConfig
    from .data import ModelData


INVERSE_DECAY_LOG10_RISK_THRESHOLD = 3.0
MINIMUM_RETAINED_STATE_TRANSITION_COEFFICIENT = 0.1


def _retained_transition_incoming_gaps(
    retained_hours: np.ndarray,
    horizon_hours: int,
) -> np.ndarray:
    """Return cyclic predecessor-to-current gaps for retained state nodes.

    ``np.diff([t_0, ..., t_n, t_0 + T])`` describes the outgoing gaps from
    each retained node. State equations are indexed by the current node, so
    their predecessor gaps are the same vector rotated right by one element.
    """
    retained = np.asarray(retained_hours, dtype=int)
    if retained.ndim != 1 or not len(retained):
        raise ValueError("Retained transition gaps require at least one hour")
    if horizon_hours <= 0:
        raise ValueError("Retained transition horizon must be positive")
    if (
        np.any(retained < 0)
        or np.any(retained >= horizon_hours)
        or np.any(np.diff(retained) <= 0)
    ):
        raise ValueError(
            "Retained transition hours must be strictly increasing and "
            "inside the horizon"
        )
    cyclic_hours = np.concatenate(
        (retained, [int(retained[0]) + int(horizon_hours)])
    )
    outgoing_gaps = np.diff(cyclic_hours).astype(int)
    return np.roll(outgoing_gaps, 1)


def _maximum_cyclic_true_run(mask: np.ndarray) -> int:
    """Return the longest cyclic run in a one-dimensional Boolean mask."""
    values = np.asarray(mask, dtype=bool)
    if values.ndim != 1 or not len(values):
        raise ValueError("Cyclic-run audit requires a non-empty vector")
    if values.all():
        return int(len(values))
    if not values.any():
        return 0
    best = 0
    current = 0
    for value in np.concatenate((values, values)):
        current = current + 1 if value else 0
        best = max(best, current)
    return min(int(best), int(len(values)))


def _compressed_thermal_state_mask(
    control_support: np.ndarray,
    retention_per_hour: np.ndarray,
    *,
    minimum_transition_coefficient: float = (
        MINIMUM_RETAINED_STATE_TRANSITION_COEFFICIENT
    ),
) -> np.ndarray:
    """Retain control hours plus exact decay anchors for a cyclic state.

    When both thermal controls are fixed to zero, the original recursion is
    ``state[t] = retention * state[t-1]``. Intermediate states have no
    independent decision and their time-invariant upper bounds are redundant
    because retention is in ``(0, 1]``. They can therefore be eliminated
    exactly. Sparse decay anchors cap every retained transition gap so the
    coefficient multiplying the predecessor state does not become tiny.
    """
    support = np.asarray(control_support, dtype=bool)
    retention = np.asarray(retention_per_hour, dtype=float)
    if support.ndim != 2 or support.shape[1] <= 0:
        raise ValueError(
            "Compressed thermal state requires a non-empty 2-D support mask"
        )
    if retention.shape != (support.shape[0],):
        raise ValueError(
            "Compressed thermal state retention shape mismatch"
        )
    if (
        not np.isfinite(retention).all()
        or np.any((retention <= 0.0) | (retention > 1.0))
    ):
        raise ValueError("Compressed thermal state retention must be in (0, 1]")
    if not 0.0 < minimum_transition_coefficient <= 1.0:
        raise ValueError(
            "minimum_transition_coefficient must be in (0, 1]"
        )

    retained = support.copy()
    hours = int(support.shape[1])
    for province_position in range(support.shape[0]):
        active_hours = np.flatnonzero(support[province_position])
        if not len(active_hours):
            continue
        rho = float(retention[province_position])
        if rho == 1.0:
            maximum_gap = hours
        else:
            maximum_gap = max(
                1,
                int(
                    math.floor(
                        math.log(minimum_transition_coefficient)
                        / math.log(rho)
                    )
                ),
            )
        cyclic_hours = np.concatenate(
            (active_hours, [int(active_hours[0]) + hours])
        )
        for start, stop in zip(cyclic_hours[:-1], cyclic_hours[1:]):
            anchor = int(start) + maximum_gap
            while anchor < int(stop):
                retained[province_position, anchor % hours] = True
                anchor += maximum_gap
    return retained


def _compressed_thermal_state_audit(
    control_support: np.ndarray,
    retained_state_mask: np.ndarray,
    retention_per_hour: np.ndarray,
) -> dict[str, Any]:
    """Summarize exact state elimination and retained transition scaling."""
    support = np.asarray(control_support, dtype=bool)
    retained = np.asarray(retained_state_mask, dtype=bool)
    retention = np.asarray(retention_per_hour, dtype=float)
    if support.shape != retained.shape or support.ndim != 2:
        raise ValueError("Compressed thermal state audit shape mismatch")
    if retention.shape != (support.shape[0],):
        raise ValueError("Compressed thermal state audit retention mismatch")
    if np.any(support & ~retained):
        raise ValueError("Every controllable hour must retain a state")

    gaps: list[int] = []
    coefficients: list[float] = []
    for province_position in range(retained.shape[0]):
        retained_hours = np.flatnonzero(retained[province_position])
        if not len(retained_hours):
            continue
        cyclic_hours = np.concatenate(
            (retained_hours, [int(retained_hours[0]) + retained.shape[1]])
        )
        province_gaps = np.diff(cyclic_hours).astype(int)
        gaps.extend(province_gaps.tolist())
        coefficients.extend(
            (
                float(retention[province_position])
                ** province_gaps.astype(float)
            ).tolist()
        )
    return {
        "representation": "active_control_hours_plus_decay_anchors_v1",
        "possible_state_variables": int(retained.size),
        "control_support_state_variables": int(support.sum()),
        "decay_anchor_state_variables": int((retained & ~support).sum()),
        "retained_state_variables": int(retained.sum()),
        "redundant_inactive_state_variables_omitted": int(
            retained.size - retained.sum()
        ),
        "retained_transition_rows": int(retained.sum()),
        "redundant_inactive_transition_rows_omitted": int(
            retained.size - retained.sum()
        ),
        "maximum_retained_transition_gap_hours": (
            max(gaps) if gaps else 0
        ),
        "minimum_retained_transition_coefficient": (
            min(coefficients) if coefficients else None
        ),
        "mathematical_equivalence": (
            "exact_elimination_of_zero_control_states_with_time_invariant_"
            "bounds"
        ),
    }


def _thermal_state_chain_numerical_risks(
    *,
    thermal_envelopes: dict[str, np.ndarray],
    thermal_parameters: dict[str, dict[str, np.ndarray]],
    province_codes: np.ndarray | None = None,
    enforce_aggregate_zero: bool,
    compress_zero_control_states: bool = False,
) -> dict[str, dict[str, Any]]:
    """Audit inverse-decay risk for each retained thermal state chain."""
    first = np.asarray(thermal_envelopes["heating_up"], dtype=float)
    if first.ndim != 2:
        raise ValueError("Thermal state-chain audit requires 2-D envelopes")
    p_count = first.shape[0]
    codes = (
        np.arange(p_count, dtype=int)
        if province_codes is None
        else np.asarray(province_codes, dtype=int)
    )
    if codes.shape != (p_count,):
        raise ValueError("Thermal state-chain province-code shape mismatch")
    risks: dict[str, dict[str, Any]] = {}
    for component in ("heating", "cooling"):
        up = np.asarray(
            thermal_envelopes[f"{component}_up"],
            dtype=float,
        )
        down = np.asarray(
            thermal_envelopes[f"{component}_down"],
            dtype=float,
        )
        if up.shape != first.shape or down.shape != first.shape:
            raise ValueError(
                f"{component} state-chain envelope shape mismatch"
            )
        support = (up > 0.0) | (down > 0.0)
        retention = np.asarray(
            thermal_parameters[component]["retention_per_hour"],
            dtype=float,
        )
        if retention.shape != (p_count,) or np.any(
            (retention <= 0.0) | (retention > 1.0)
        ):
            raise ValueError(f"{component} retention must be in (0, 1]")
        active_rows = []
        for province_position in np.flatnonzero(support.any(axis=1)):
            maximum_zero_run = _maximum_cyclic_true_run(
                ~support[province_position]
            )
            inverse_decay_log10 = (
                -maximum_zero_run
                * math.log10(float(retention[province_position]))
            )
            active_rows.append(
                {
                    "province_position": int(province_position),
                    "province_code": int(codes[province_position]),
                    "maximum_cyclic_zero_control_run_hours": int(
                        maximum_zero_run
                    ),
                    "retention_per_hour": float(
                        retention[province_position]
                    ),
                    "inverse_decay_amplification_log10": float(
                        inverse_decay_log10
                    ),
                }
            )
        worst = (
            max(
                active_rows,
                key=lambda row: row[
                    "inverse_decay_amplification_log10"
                ],
            )
            if active_rows
            else None
        )
        aggregation_risk = bool(
            worst is not None
            and worst["inverse_decay_amplification_log10"]
            > INVERSE_DECAY_LOG10_RISK_THRESHOLD
        )
        compressed_state_audit = None
        if compress_zero_control_states:
            retained = _compressed_thermal_state_mask(
                support,
                retention,
            )
            compressed_state_audit = _compressed_thermal_state_audit(
                support,
                retained,
                retention,
            )
        minimum_retained = (
            compressed_state_audit[
                "minimum_retained_transition_coefficient"
            ]
            if compressed_state_audit is not None
            else None
        )
        compression_well_scaled = bool(
            compressed_state_audit is not None
            and (
                minimum_retained is None
                or float(minimum_retained)
                >= MINIMUM_RETAINED_STATE_TRANSITION_COEFFICIENT - 1e-12
            )
        )
        risks[component] = {
            "active_provinces": len(active_rows),
            "inactive_provinces_with_state_chain_omitted": int(
                p_count - len(active_rows)
            ),
            "worst_active_province": worst,
            "automatic_presolve_aggregation_risk": aggregation_risk,
            "zero_control_state_compression_enabled": bool(
                compress_zero_control_states
            ),
            "zero_control_state_compression": compressed_state_audit,
            "zero_control_state_compression_well_scaled": (
                compression_well_scaled
            ),
            "automatic_presolve_aggregation_risk_mitigated": bool(
                aggregation_risk and compression_well_scaled
            ),
            "aggregate_zero_required_for_solve": bool(
                enforce_aggregate_zero
                and aggregation_risk
                and not compression_well_scaled
            ),
        }
    return risks


def assess_flexible_load_solver_compatibility(
    structural_audit: dict[str, Any],
    numerics: dict[str, Any],
) -> dict[str, Any]:
    """Block risky V5 solves without the stable long-horizon solver contract.

    Long deterministic state-decay chains are scientifically valid, but
    automatic row aggregation can eliminate them in the inverse direction and
    create very large coefficients. V5 removes zero-control states exactly;
    an uncompressed formulation must instead use ``Aggregate=0``. A
    conservative crossover-basis construction remains one accepted diagnostic
    route.  A second route may deliberately request an optimal primal-dual
    interior solution without a basis; it is accepted only with Method=2,
    Crossover=0, SolutionTarget=1 and a tighter barrier convergence target.
    """
    component_risks = {
        component: structural_audit.get(
            f"{component}_state_chain_numerical_risk",
            {},
        )
        for component in ("heating", "cooling")
    }
    aggregate = int(numerics.get("aggregate", 1))
    crossover = int(numerics.get("crossover", -1))
    crossover_basis = int(numerics.get("crossover_basis", -1))
    solution_target = int(numerics.get("solution_target", -1))
    method = int(numerics.get("method", -1))
    barrier_tolerance = float(
        numerics.get("barrier_convergence_tolerance", 1e-8)
    )
    v5_formulation = (
        structural_audit.get("formulation")
        == "integrated_service_constrained_v5"
    )
    aggregate_zero_required = v5_formulation and any(
        bool(risk.get("aggregate_zero_required_for_solve", False))
        for risk in component_risks.values()
    )
    long_chain_numerical_care_required = v5_formulation and any(
        bool(risk.get("automatic_presolve_aggregation_risk", False))
        for risk in component_risks.values()
    )
    stable_crossover_required = bool(long_chain_numerical_care_required)
    # Gurobi's documented crossover push-order choices 1, 2 and 4 all
    # produce a basic solution.  Crossover=3 is intentionally excluded: it
    # has already failed the matched 744 h numerical gate for this model.
    accepted_basic_crossover_orders = (1, 2, 4)
    stable_basic_route = bool(
        crossover in accepted_basic_crossover_orders
        and crossover_basis == 1
    )
    strict_nonbasic_primal_dual_route = bool(
        method == 2
        and crossover == 0
        and solution_target == 1
        and barrier_tolerance <= 1e-9
    )
    stable_long_horizon_settings = (
        (not aggregate_zero_required or aggregate == 0)
        and (
            not stable_crossover_required
            or stable_basic_route
            or strict_nonbasic_primal_dual_route
        )
    )
    passed = (
        not long_chain_numerical_care_required
        or stable_long_horizon_settings
    )
    if not long_chain_numerical_care_required:
        reason = (
            "No selected-horizon V5 inverse-decay chain requires special "
            "solver protection."
        )
    elif passed:
        if aggregate_zero_required:
            reason = (
                "Selected-horizon V5 inverse-decay risk is protected by "
                "Aggregate=0, Crossover in {1,2,4} and CrossoverBasis=1."
            )
        else:
            reason = (
                "Zero-control thermal states were eliminated exactly; the "
                "selected solver follows either the stable-basis route or "
                "the strict optimal primal-dual nonbasic route."
            )
    else:
        if aggregate_zero_required:
            reason = (
                "Refusing optimize(): selected-horizon V5 state chains can "
                "create inverse-decay coefficient amplification; use "
                "Aggregate=0, Crossover in {1,2,4} and CrossoverBasis=1."
            )
        else:
            reason = (
                "Refusing optimize(): structurally compressed V5 long-chain "
                "states require either Crossover in {1,2,4} with "
                "CrossoverBasis=1 or "
                "Method=2/Crossover=0/SolutionTarget=1 with BarConvTol<=1e-9 "
                "until matched long-horizon gates establish evidence."
            )
    return {
        "schema_version": "cispo_solver_numerical_compatibility_v1",
        "status": "PASS" if passed else "BLOCKED",
        "formulation": structural_audit.get("formulation"),
        "aggregate_parameter": aggregate,
        "aggregate_parameter_source": (
            "explicit_profile"
            if "aggregate" in numerics
            else "gurobi_default_1"
        ),
        "aggregate_zero_required": aggregate_zero_required,
        "stable_crossover_required": stable_crossover_required,
        "crossover_parameter": crossover,
        "crossover_basis_parameter": crossover_basis,
        "solution_target_parameter": solution_target,
        "barrier_convergence_tolerance": barrier_tolerance,
        "stable_basic_route": stable_basic_route,
        "accepted_basic_crossover_orders": list(
            accepted_basic_crossover_orders
        ),
        "strict_nonbasic_primal_dual_route": (
            strict_nonbasic_primal_dual_route
        ),
        "required_long_horizon_settings": {
            "aggregate": 0 if aggregate_zero_required else "automatic_allowed",
            "accepted_solver_routes": [
                {
                    "method": 2,
                    "crossover": list(accepted_basic_crossover_orders),
                    "crossover_basis": 1,
                    "solution_form": "basic",
                },
                {
                    "method": 2,
                    "crossover": 0,
                    "solution_target": 1,
                    "maximum_barrier_convergence_tolerance": 1e-9,
                    "solution_form": "primal_dual_nonbasic",
                },
            ],
        },
        "inverse_decay_amplification_log10_threshold": (
            INVERSE_DECAY_LOG10_RISK_THRESHOLD
        ),
        "component_risks": component_risks,
        "reason": reason,
    }


def prebuild_flexible_load_solver_compatibility(
    config: ModelConfig,
    data: ModelData,
    *,
    hours: int,
    hour_start: int = 0,
) -> dict[str, Any]:
    """Assess the V5 numerical contract before allocating the full LP."""
    settings = config.raw["flexible_load"]
    formulation = str(settings.get("formulation"))
    structural_audit: dict[str, Any] = {}
    if (
        bool(config.raw["features"]["flexible_load"])
        and formulation == "integrated_service_constrained_v5"
    ):
        structural_audit.update(
            {
                "formulation": formulation,
                "optimization_hours": int(hours),
                "optimization_start_hour": int(hour_start),
            }
        )
        service = data.flexible_load_v4
        if service is None or service.contract_version != "v5":
            raise ValueError(
                "V5 solver compatibility requires validated V5 inputs"
            )
        hour_stop = int(hour_start) + int(hours)
        available_hours = next(
            iter(service.thermal_envelopes_gw.values())
        ).shape[1]
        if int(hour_start) < 0 or hour_stop > available_hours:
            raise ValueError(
                "Flexible-load numerical-audit window is outside the model year"
            )
        risks = _thermal_state_chain_numerical_risks(
            thermal_envelopes={
                key: value[:, int(hour_start):hour_stop]
                for key, value in service.thermal_envelopes_gw.items()
            },
            thermal_parameters=service.thermal_parameters,
            province_codes=data.provinces.province_code.to_numpy(
                dtype=int
            ),
            enforce_aggregate_zero=True,
            compress_zero_control_states=True,
        )
        for component, risk in risks.items():
            structural_audit[
                f"{component}_state_chain_numerical_risk"
            ] = risk
    return assess_flexible_load_solver_compatibility(
        structural_audit,
        config.raw["numerics"],
    )


def _service_effective_load_lower_bound(
    *,
    components: dict[str, np.ndarray],
    thermal_down_upper: dict[str, np.ndarray],
    fixed_ev_baseline: np.ndarray,
    ev_discharge_upper: np.ndarray,
) -> np.ndarray:
    """Return a bound-only lower envelope for the effective grid load."""
    return (
        components["base_residual"]
        + components["heating"]
        - thermal_down_upper["heating"]
        + components["cooling"]
        - thermal_down_upper["cooling"]
        + fixed_ev_baseline
        - ev_discharge_upper
    )
