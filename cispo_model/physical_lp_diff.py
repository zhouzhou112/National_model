"""Fail-closed, machine-readable whitelist for physical-LP release diffs."""
from __future__ import annotations

from collections import Counter
from typing import Sequence

import numpy as np
from scipy import sparse


def _matches(name: str, prefixes: Sequence[str]) -> bool:
    return any(name.startswith(prefix) for prefix in prefixes)


def _matrix_rule(
    row_name: str,
    variable_name: str,
    rules: Sequence[dict],
) -> str | None:
    for rule in rules:
        if _matches(row_name, rule["row_prefixes"]) and _matches(
            variable_name, rule["variable_prefixes"]
        ):
            return str(rule["rule_id"])
    return None


def compare_physical_lp_arrays(
    *,
    reference_matrix: sparse.csr_matrix,
    candidate_matrix: sparse.csr_matrix,
    reference_rhs: np.ndarray,
    candidate_rhs: np.ndarray,
    reference_lower: np.ndarray,
    candidate_lower: np.ndarray,
    reference_upper: np.ndarray,
    candidate_upper: np.ndarray,
    reference_objective: np.ndarray,
    candidate_objective: np.ndarray,
    reference_senses: Sequence[str],
    candidate_senses: Sequence[str],
    row_names: Sequence[str],
    variable_names: Sequence[str],
    whitelist: dict,
    maximum_examples: int = 25,
) -> dict:
    """Compare two same-index physical LPs and reject every unlisted change."""
    if reference_matrix.shape != candidate_matrix.shape:
        raise ValueError("Physical LP matrix shapes differ")
    expected_shape = (len(row_names), len(variable_names))
    if reference_matrix.shape != expected_shape:
        raise ValueError("Physical LP names do not match matrix shape")

    failures: list[dict] = []
    counts: Counter[str] = Counter()
    examples: list[dict] = []

    delta = (candidate_matrix - reference_matrix).tocoo()
    delta.sum_duplicates()
    for row, column, value in zip(delta.row, delta.col, delta.data):
        if value == 0.0:
            continue
        row_name = row_names[int(row)]
        variable_name = variable_names[int(column)]
        rule_id = _matrix_rule(
            row_name,
            variable_name,
            whitelist.get("matrix_change_rules", []),
        )
        entry = {
            "kind": "matrix_coefficient",
            "row": row_name,
            "variable": variable_name,
            "reference": float(reference_matrix[row, column]),
            "candidate": float(candidate_matrix[row, column]),
        }
        if rule_id is None:
            failures.append(entry)
        else:
            counts[rule_id] += 1
            entry["rule_id"] = rule_id
        if len(examples) < maximum_examples:
            examples.append(entry)

    exact_arrays = {
        "rhs": np.array_equal(reference_rhs, candidate_rhs),
        "lower_bounds": np.array_equal(reference_lower, candidate_lower),
        "objective": np.array_equal(reference_objective, candidate_objective),
        "constraint_senses": list(reference_senses) == list(candidate_senses),
    }
    for kind, passed in exact_arrays.items():
        if not passed:
            failures.append({"kind": kind, "reason": "exact_identity_required"})

    allowed_bound_prefixes = tuple(
        whitelist.get("exact_zero_upper_bound_variable_prefixes", [])
    )
    changed_upper = np.flatnonzero(reference_upper != candidate_upper)
    for column in changed_upper:
        name = variable_names[int(column)]
        permitted = bool(
            _matches(name, allowed_bound_prefixes)
            and reference_lower[column] == 0.0
            and reference_upper[column] > 0.0
            and candidate_upper[column] == 0.0
        )
        entry = {
            "kind": "upper_bound",
            "variable": name,
            "reference": float(reference_upper[column]),
            "candidate": float(candidate_upper[column]),
        }
        if permitted:
            counts["exact_zero_reservoir_release_upper_bound"] += 1
            entry["rule_id"] = "exact_zero_reservoir_release_upper_bound"
        else:
            failures.append(entry)
        if len(examples) < maximum_examples:
            examples.append(entry)

    return {
        "schema_version": "cispo_physical_lp_release_diff_v1",
        "status": "PASS" if not failures else "FAIL",
        "scope": "ORIGINAL_PHYSICAL_LP_NO_ROW_SCALING",
        "checks": {
            "matrix_changes_whitelisted": not any(
                failure["kind"] == "matrix_coefficient" for failure in failures
            ),
            "rhs_identical": exact_arrays["rhs"],
            "lower_bounds_identical": exact_arrays["lower_bounds"],
            "objective_identical": exact_arrays["objective"],
            "constraint_senses_identical": exact_arrays["constraint_senses"],
            "upper_bound_changes_are_exact_zero_certificate_candidates": not any(
                failure["kind"] == "upper_bound" for failure in failures
            ),
            "row_scaling_absent_from_physical_diff": not any(
                failure["kind"] == "matrix_coefficient" for failure in failures
            ),
        },
        "approved_change_counts": dict(sorted(counts.items())),
        "changed_matrix_coefficients": int(np.count_nonzero(delta.data)),
        "changed_upper_bounds": int(len(changed_upper)),
        "failure_count": len(failures),
        "failures": failures[:maximum_examples],
        "change_examples": examples,
    }
