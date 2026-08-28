"""Verify zero-flow bound tightening directly against an archived LP.

For a sum of equality rows with zero RHS, after substituting already-proven
zero variables, nonnegative coefficients times nonnegative variables summing
to zero prove that every remaining positively weighted variable is zero.
No epsilon/cutoff is used; this is a sufficient, intentionally narrow proof.
"""
import re

import numpy as np


def certify(a, rhs, lower, old_upper, new_upper, senses, row_names, variable_names):
    changed = np.flatnonzero(old_upper != new_upper)
    allowed = ("reservoir_turbine_flow_1000m3s[", "reservoir_spill_flow_1000m3s[")
    if any(not variable_names[j].startswith(allowed) or lower[j] != 0
           or new_upper[j] != 0 or old_upper[j] <= 0 for j in changed):
        raise ValueError("Changes are not exclusively positive-to-zero nonnegative reservoir release bounds")
    storage_ids = {}
    for j, name in enumerate(variable_names):
        match = re.fullmatch(r"reservoir_active_storage_million_m3\[(\d+),\d+\]", name)
        if match:
            storage_ids[j] = int(match[1])
    groups = {}
    for i, name in enumerate(row_names):
        if not name.startswith(("reservoir_independent_", "reservoir_cascade_s4_8_9_12_")):
            continue
        cols = a.indices[a.indptr[i]:a.indptr[i+1]]
        identities = {storage_ids[j] for j in cols if j in storage_ids}
        if len(identities) != 1:
            continue
        groups.setdefault(identities.pop(), []).append(i)
    candidates = {}
    for identity, rows in groups.items():
        if not np.all(rhs[rows] == 0) or not np.all(senses[rows] == "="):
            continue
        summed = np.asarray(a[rows].sum(axis=0)).ravel()
        nonzero = np.flatnonzero(summed)
        candidates[identity] = (rows, nonzero, summed[nonzero])
    proven = set(np.flatnonzero((lower == 0) & (old_upper == 0)))
    certificates = []
    while candidates:
        progress = False
        for identity, (rows, columns, values) in list(candidates.items()):
            remaining = [(int(j), float(v)) for j, v in zip(columns, values) if j not in proven]
            if any(value < 0 or lower[j] < 0 for j, value in remaining):
                continue
            newly_proven = [j for j, value in remaining if value > 0]
            proven.update(newly_proven)
            certificates.append({"reservoir_local_row": int(identity), "summed_equality_rows": len(rows),
                                 "rhs_exact_zero": True, "proven_variable_count": len(newly_proven),
                                 "proven_variables": [variable_names[j] for j in newly_proven]})
            del candidates[identity]
            progress = True
        if not progress:
            break
    uncovered = [variable_names[j] for j in changed if j not in proven]
    return {"status": "PASS" if not uncovered else "FAIL", "changed_upper_bounds": len(changed),
            "uncovered_variables": uncovered, "certificates": certificates,
            "proof": "Exact-zero equality row sums + nonnegative variables + previously proven zeros; no threshold"}
