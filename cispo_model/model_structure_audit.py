"""Raw LP sparsity census by stable CISPO constraint and variable families.

This module inspects the constructed linear matrix only.  It never calls
``optimize()``, changes a Gurobi parameter, or attributes presolve reductions
to individual source families: Gurobi exposes the latter only as global log
statistics for this formulation.
"""
from __future__ import annotations

from collections import defaultdict
import heapq
from typing import Any

import gurobipy as gp


_FAMILY_RULES: tuple[tuple[str, str], ...] = (
    ("load_center_", "load_center_annual_network"),
    ("province_annual_", "load_center_annual_network"),
    ("intra_load_center_", "load_center_annual_network"),
    ("reservoir_cascade_", "hydro_reservoir_cascade"),
    ("reservoir_independent_", "hydro_reservoir_independent"),
    ("reservoir_", "hydro_reservoir_station"),
    ("ror_", "hydro_run_of_river"),
    ("hydro_", "hydro_capacity_and_connection"),
    ("ruc_", "thermal_ruc"),
    ("ramp_", "thermal_ruc"),
    ("online_", "thermal_ruc"),
    ("startup_", "thermal_ruc"),
    ("shutdown_", "thermal_ruc"),
    ("gross_", "thermal_ruc"),
    ("thermal_", "thermal_capacity_and_ccs"),
    ("nuclear_", "thermal_capacity_and_ccs"),
    ("chp_", "thermal_ruc"),
    ("biomass_", "thermal_biomass"),
    ("storage_", "storage"),
    ("vre_", "vre"),
    ("wave_", "wave"),
    ("flow_", "interprovincial_transmission"),
    ("ac_line_", "interprovincial_transmission"),
    ("dc_line_", "interprovincial_transmission"),
    ("line_", "interprovincial_transmission"),
    ("strict_power_balance", "hourly_power_balance"),
    ("up_reserve", "security_reserve_and_inertia"),
    ("down_reserve", "security_reserve_and_inertia"),
    ("inertia_", "security_reserve_and_inertia"),
    ("capacity_margin", "security_reserve_and_inertia"),
    ("annual_", "annual_carbon_and_resources"),
    ("co2_", "co2_transport_and_storage"),
    ("dac_", "dac_annual_accounting"),
    ("spur_", "spatial_connection"),
    ("trunk_", "spatial_connection"),
    ("effective_load", "demand_and_flexibility"),
    ("heating_", "demand_and_flexibility"),
    ("cooling_", "demand_and_flexibility"),
    ("ev_", "demand_and_flexibility"),
)


def family_for_name(name: str) -> str:
    """Classify a Gurobi row/column using stable model-name prefixes."""
    for prefix, family in _FAMILY_RULES:
        if name.startswith(prefix):
            return family
    return "other_unclassified"


def _summarize_families(
    names: list[str],
    nonzeros: list[int],
    *,
    count_key: str,
    nonzero_key: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    counts: dict[str, int] = defaultdict(int)
    totals: dict[str, int] = defaultdict(int)
    maxima: dict[str, int] = defaultdict(int)
    examples: dict[str, list[str]] = defaultdict(list)
    unclassified: list[str] = []
    for name, count in zip(names, nonzeros):
        family = family_for_name(name)
        counts[family] += 1
        totals[family] += int(count)
        maxima[family] = max(maxima[family], int(count))
        if len(examples[family]) < 3:
            examples[family].append(name)
        if family == "other_unclassified" and len(unclassified) < 20:
            unclassified.append(name)
    rows = [
        {
            "family": family,
            count_key: counts[family],
            nonzero_key: totals[family],
            f"maximum_{nonzero_key}_per_{count_key.rstrip('s')}": maxima[family],
            f"mean_{nonzero_key}_per_{count_key.rstrip('s')}": (
                totals[family] / counts[family] if counts[family] else 0.0
            ),
            "examples": examples[family],
        }
        for family in counts
    ]
    rows.sort(key=lambda row: (-int(row[nonzero_key]), str(row["family"])))
    return rows, unclassified


def _largest_matrix_entries(
    names: list[str],
    nonzeros: list[int],
    *,
    name_key: str,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Return the exact densest raw rows or columns without sorting all names."""
    largest = heapq.nlargest(
        limit,
        enumerate(nonzeros),
        key=lambda item: (int(item[1]), names[item[0]]),
    )
    return [
        {
            "family": family_for_name(names[position]),
            name_key: names[position],
            "matrix_nonzeros": int(count),
        }
        for position, count in largest
    ]


def audit_model_structure(
    model: gp.Model,
    *,
    max_matrix_nonzeros: int = 50_000_000,
) -> dict[str, Any]:
    """Return raw-matrix family counts without changing the LP formulation.

    ``Model.getA()`` materializes a SciPy sparse matrix, so the caller must
    explicitly opt in and this function refuses matrices above the configured
    safety limit.  The audit reports raw rows/columns only; Gurobi does not
    publish a presolved row-to-source-family mapping.
    """
    model.update()
    if max_matrix_nonzeros < 1:
        raise ValueError("max_matrix_nonzeros must be positive")
    if int(model.NumNZs) > int(max_matrix_nonzeros):
        raise ValueError(
            "Constraint-family audit matrix exceeds the explicit safety limit: "
            f"{int(model.NumNZs)} > {int(max_matrix_nonzeros)} nonzeros"
        )
    matrix = model.getA().tocsr()
    if matrix.shape != (int(model.NumConstrs), int(model.NumVars)):
        raise RuntimeError(
            "Gurobi matrix shape does not match model dimensions: "
            f"{matrix.shape} versus {(int(model.NumConstrs), int(model.NumVars))}"
        )
    if int(matrix.nnz) != int(model.NumNZs):
        raise RuntimeError(
            "Gurobi matrix nonzero count does not match model NumNZs: "
            f"{int(matrix.nnz)} versus {int(model.NumNZs)}"
        )
    constraints = model.getConstrs()
    variables = model.getVars()
    constraint_names = list(model.getAttr("ConstrName", constraints))
    variable_names = list(model.getAttr("VarName", variables))
    row_nonzeros = [int(value) for value in matrix.getnnz(axis=1)]
    column_nonzeros = [int(value) for value in matrix.getnnz(axis=0)]
    constraint_families, unclassified_constraints = _summarize_families(
        constraint_names,
        row_nonzeros,
        count_key="constraints",
        nonzero_key="matrix_nonzeros",
    )
    variable_families, unclassified_variables = _summarize_families(
        variable_names,
        column_nonzeros,
        count_key="variables",
        nonzero_key="matrix_nonzeros",
    )
    return {
        "schema_version": "constraint_family_audit_v2",
        "scope": "raw_model_before_presolve",
        "raw_model": {
            "constraints": int(model.NumConstrs),
            "variables": int(model.NumVars),
            "matrix_nonzeros": int(matrix.nnz),
            "matrix_access_safety_limit_nonzeros": int(max_matrix_nonzeros),
        },
        "constraint_families": constraint_families,
        "variable_families": variable_families,
        "largest_constraints": _largest_matrix_entries(
            constraint_names,
            row_nonzeros,
            name_key="constraint_name",
        ),
        "largest_variables": _largest_matrix_entries(
            variable_names,
            column_nonzeros,
            name_key="variable_name",
        ),
        "unclassified_constraint_name_examples": unclassified_constraints,
        "unclassified_variable_name_examples": unclassified_variables,
        "presolve_family_attribution": (
            "UNAVAILABLE: Gurobi logs global presolved dimensions but does not "
            "expose a stable source-family mapping after presolve."
        ),
    }
