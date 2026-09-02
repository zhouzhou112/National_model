"""Certify exact-zero reservoir release bounds against an archived LP.

The proof deliberately uses no epsilon.  Summing a reservoir's cyclic water
balance equalities cancels storage.  With an exactly zero summed right-hand
side, nonnegative variables and nonnegative remaining coefficients, every
positively weighted remaining release variable is exactly zero.
"""
from __future__ import annotations

import re
from typing import Sequence

import numpy as np
from scipy import sparse


def certify(
    a: sparse.csr_matrix,
    rhs: np.ndarray,
    lower: np.ndarray,
    old_upper: np.ndarray,
    new_upper: np.ndarray,
    senses: np.ndarray,
    row_names: Sequence[str],
    variable_names: Sequence[str],
) -> dict:
    """Return a machine-readable sufficient proof for positive-to-zero bounds."""
    changed = np.flatnonzero(old_upper != new_upper)
    allowed = (
        "reservoir_turbine_flow_1000m3s[",
        "reservoir_spill_flow_1000m3s[",
    )
    if any(
        not variable_names[j].startswith(allowed)
        or lower[j] != 0.0
        or new_upper[j] != 0.0
        or old_upper[j] <= 0.0
        for j in changed
    ):
        raise ValueError(
            "Changes are not exclusively positive-to-zero nonnegative "
            "reservoir release bounds"
        )

    storage_ids: dict[int, int] = {}
    for j, name in enumerate(variable_names):
        match = re.fullmatch(
            r"reservoir_active_storage_million_m3\[(\d+),\d+\]", name
        )
        if match:
            storage_ids[j] = int(match.group(1))

    groups: dict[int, list[int]] = {}
    for i, name in enumerate(row_names):
        if not name.startswith(
            ("reservoir_independent_", "reservoir_cascade_s4_8_9_12_")
        ):
            continue
        columns = a.indices[a.indptr[i] : a.indptr[i + 1]]
        identities = {storage_ids[j] for j in columns if j in storage_ids}
        if len(identities) == 1:
            groups.setdefault(identities.pop(), []).append(i)

    candidates: dict[int, tuple[list[int], np.ndarray, np.ndarray]] = {}
    for identity, rows in groups.items():
        if not np.all(rhs[rows] == 0.0) or not np.all(senses[rows] == "="):
            continue
        summed = np.asarray(a[rows].sum(axis=0)).ravel()
        nonzero = np.flatnonzero(summed)
        candidates[identity] = (rows, nonzero, summed[nonzero])

    proven = set(np.flatnonzero((lower == 0.0) & (old_upper == 0.0)))
    certificates: list[dict] = []
    while candidates:
        progress = False
        for identity, (rows, columns, values) in list(candidates.items()):
            remaining = [
                (int(j), float(value))
                for j, value in zip(columns, values)
                if j not in proven
            ]
            if any(value < 0.0 or lower[j] < 0.0 for j, value in remaining):
                continue
            newly_proven = [j for j, value in remaining if value > 0.0]
            proven.update(newly_proven)
            certificates.append(
                {
                    "reservoir_local_row": int(identity),
                    "summed_equality_rows": len(rows),
                    "rhs_exact_zero": True,
                    "proven_variable_count": len(newly_proven),
                    "proven_variables": [variable_names[j] for j in newly_proven],
                }
            )
            del candidates[identity]
            progress = True
        if not progress:
            break

    uncovered = [variable_names[j] for j in changed if j not in proven]
    return {
        "schema_version": "cispo_exact_zero_bound_certificate_v1",
        "status": "PASS" if not uncovered else "FAIL",
        "changed_upper_bounds": len(changed),
        "uncovered_variables": uncovered,
        "certificates": certificates,
        "proof": (
            "Exact-zero equality row sums + nonnegative variables + "
            "previously proven zeros; no threshold"
        ),
    }
