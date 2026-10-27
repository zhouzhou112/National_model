"""Read an archived gate model and audit fixed-capacity row contradictions.

No optimization, relaxation or model mutation. Substitute accounting equalities
with exactly one unfixed total-capacity variable, then evaluate row intervals.
This detects necessary infeasibility conditions, not every possible conflict.
"""
import argparse
import hashlib
import json
from pathlib import Path

import gurobipy as gp
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    archive = args.run/'model_archive/original.mps'
    if not archive.exists():
        archive = archive.with_suffix('.mps.gz')
    model = gp.read(str(archive))
    variables = model.getVars()
    lower, upper = np.array(model.LB), np.array(model.UB)
    matrix, rows = model.getA().tocsr(), model.getConstrs()
    conflicts, derived = [], 0
    def terms(i):
        part = slice(matrix.indptr[i], matrix.indptr[i+1])
        return matrix.indices[part], matrix.data[part]
    for i, row in enumerate(rows):
        if row.Sense != '=' or 'capacity_accounting' not in row.ConstrName:
            continue
        columns, coefficients = terms(i)
        free = np.flatnonzero(lower[columns] != upper[columns])
        if len(free) != 1:
            continue
        k = free[0]
        mask = np.arange(len(columns)) != k
        value = float((row.RHS-np.dot(coefficients[mask], lower[columns[mask]]))/coefficients[k])
        column = columns[k]
        if value < lower[column]-1e-9 or value > upper[column]+1e-9:
            conflicts.append(dict(kind='implied_capacity_bound', row=row.ConstrName,
                variable=variables[column].VarName, value=value,
                lb=float(lower[column]), ub=float(upper[column])))
        lower[column] = upper[column] = value
        derived += 1
    for i, row in enumerate(rows):
        columns, coefficients = terms(i)
        minimum = float(np.dot(coefficients, np.where(coefficients > 0, lower[columns], upper[columns])))
        maximum = float(np.dot(coefficients, np.where(coefficients > 0, upper[columns], lower[columns])))
        violation = max(minimum-row.RHS if row.Sense in ['<', '='] else 0,
                        row.RHS-maximum if row.Sense in ['>', '='] else 0)
        if violation > 1e-9:
            conflicts.append(dict(kind='after_capacity_substitution', row=row.ConstrName,
                sense=row.Sense, rhs=row.RHS, minimum_lhs=minimum,
                maximum_lhs=maximum, violation=violation))
    report = dict(source=str(archive), source_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        tolerance=1e-9, derived_capacity_count=derived, conflicts=conflicts,
        model_unchanged=True, optimized=False, limitation='Necessary conditions only; not a complete IIS')
    args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(derived_capacity_count=derived, conflicts=len(conflicts), output=str(args.output))))
    model.dispose()


if __name__ == '__main__':
    main()
