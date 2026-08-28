"""Opt-in, reversible binary diagonal scaling of continuous LP arrays.

This experimental module is NOT imported by the production model or runner.
For x = D z, use A' = R A D, b' = R b, c' = D c, bounds' = bounds / D.
The original objective constant and sense are unchanged. Original duals are
pi = R pi', reduced costs rc = rc' / D. All factors are positive powers of two.
Range improvement is NOT evidence of improved conditioning or accepted quality.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse


@dataclass(frozen=True)
class Scaling:
    row_exponents: np.ndarray
    column_exponents: np.ndarray

    @property
    def rows(self):
        return np.exp2(self.row_exponents.astype(float))

    @property
    def columns(self):
        return np.exp2(self.column_exponents.astype(float))

    def primal_to_original(self, z):
        return np.asarray(z) * self.columns

    def dual_to_original(self, pi):
        return np.asarray(pi) * self.rows

    def reduced_cost_to_original(self, rc):
        return np.asarray(rc) / self.columns


def nonzero_range(values):
    values = np.abs(np.asarray(values))
    values = values[np.isfinite(values) & (values != 0)]
    if not values.size:
        return {"count": 0, "minimum": None, "maximum": None, "ratio": None}
    low, high = float(values.min()), float(values.max())
    return {"count": int(values.size), "minimum": low, "maximum": high, "ratio": high / low}


def _extrema(log_values, index, size):
    lo, hi = np.full(size, np.inf), np.full(size, -np.inf)
    np.minimum.at(lo, index, log_values)
    np.maximum.at(hi, index, log_values)
    return lo, hi


def propose_scaling(matrix, objective, *, iterations=8, exponent_limit=20):
    """Geometrically center row/column nonzeros; include c in column ranges.

    Deterministic, bounded experimental recipe; does not change any LP values
    except via reversible coordinate transformations. Empty rows/columns keep
    neutral factors. No coefficient dropping, bound tightening or objective
    reweighting is performed. The objective has no independent scale factor.
    """
    matrix = sparse.csr_matrix(matrix, dtype=float)
    if iterations < 1 or not 0 <= exponent_limit <= 100:
        raise ValueError("Invalid iteration count or exponent limit")
    if not np.all(np.isfinite(matrix.data)) or np.any(matrix.data == 0):
        raise ValueError("Require finite explicit nonzero matrix entries")
    c = np.asarray(objective, dtype=float)
    if c.shape != (matrix.shape[1],) or not np.all(np.isfinite(c)):
        raise ValueError("Invalid objective")
    row_index = np.repeat(np.arange(matrix.shape[0]), np.diff(matrix.indptr))
    col_index = matrix.indices
    logs = np.log2(np.abs(matrix.data))
    re = np.zeros(matrix.shape[0], dtype=np.int32)
    ce = np.zeros(matrix.shape[1], dtype=np.int32)
    objective_nonzero = np.flatnonzero(c)
    for _ in range(iterations):
        lo, hi = _extrema(logs + re[row_index] + ce[col_index], col_index, len(ce))
        cost_logs = np.log2(np.abs(c[objective_nonzero])) + ce[objective_nonzero]
        lo[objective_nonzero] = np.minimum(lo[objective_nonzero], cost_logs)
        hi[objective_nonzero] = np.maximum(hi[objective_nonzero], cost_logs)
        active = np.isfinite(lo)
        delta = np.rint(-(lo[active] + hi[active]) / 2).astype(np.int32)
        ce[active] = np.clip(ce[active] + delta, -exponent_limit, exponent_limit)
        lo, hi = _extrema(logs + re[row_index] + ce[col_index], row_index, len(re))
        active = np.isfinite(lo)
        delta = np.rint(-(lo[active] + hi[active]) / 2).astype(np.int32)
        re[active] = np.clip(re[active] + delta, -exponent_limit, exponent_limit)
    return Scaling(re, ce)


def transform(matrix, rhs, objective, lower, upper, scaling):
    a = sparse.csr_matrix(matrix, dtype=float).copy()
    row_index = np.repeat(np.arange(a.shape[0]), np.diff(a.indptr))
    exponents = scaling.row_exponents[row_index] + scaling.column_exponents[a.indices]
    a.data = np.ldexp(a.data, exponents)
    b = np.ldexp(np.asarray(rhs, dtype=float), scaling.row_exponents)
    c = np.ldexp(np.asarray(objective, dtype=float), scaling.column_exponents)
    lb = np.ldexp(np.asarray(lower, dtype=float), -scaling.column_exponents)
    ub = np.ldexp(np.asarray(upper, dtype=float), -scaling.column_exponents)
    for old, new in ((matrix.data, a.data), (rhs, b), (objective, c), (lower, lb), (upper, ub)):
        old, new = np.asarray(old), np.asarray(new)
        if np.any(np.isfinite(old) & ~np.isfinite(new)) or np.any((old != 0) & (new == 0)):
            raise ValueError("Scaling would overflow or underflow: candidate rejected")
    return a, b, c, lb, ub


def verify_roundtrip(original, transformed, scaling):
    a, b, c, lb, ub = original
    sa, sb, sc, slb, sub = transformed
    inverse = Scaling(-scaling.row_exponents, -scaling.column_exponents)
    back = transform(sa, sb, sc, slb, sub, inverse)
    return {
        "sparsity_identical": bool(np.array_equal(a.indptr, sa.indptr) and np.array_equal(a.indices, sa.indices)),
        **{name: bool(np.array_equal(left, right)) for name, left, right in zip(
            ("matrix_bit_exact", "rhs_bit_exact", "objective_bit_exact", "lower_bit_exact", "upper_bit_exact"),
            (a.data, b, c, lb, ub), (back[0].data, *back[1:]))},
    }


def pulled_back_tolerances(scaling, *, primal_tolerance=1e-6, dual_tolerance=1e-6,
                           minimum_solver_tolerance=1e-9):
    """Budget amplification in rows/bounds and dual-sign/reduced-cost errors.

    This is NOT a sufficiency proof for Barrier termination, stationarity,
    complementarity or scientific QC. Always audit the restored solution.
    Reject transformations requiring unsupported solver tolerances.
    """
    if min(primal_tolerance, dual_tolerance, minimum_solver_tolerance) <= 0:
        raise ValueError("Tolerances must be positive")
    primal_amplification = max(1., float(np.max(scaling.columns, initial=1)),
                               float(np.max(1 / scaling.rows, initial=1)))
    dual_amplification = max(1., float(np.max(scaling.rows, initial=1)),
                             float(np.max(1 / scaling.columns, initial=1)))
    primal = primal_tolerance / primal_amplification
    dual = dual_tolerance / dual_amplification
    if min(primal, dual) < minimum_solver_tolerance:
        raise ValueError("Scaling exceeds original-unit tolerance budget; reduce exponent range")
    return {"FeasibilityTol": primal, "OptimalityTol": dual,
            "primal_amplification_bound": primal_amplification,
            "dual_amplification_bound": dual_amplification}


def matrix_summary(a, b, c, lower, upper):
    a = sparse.csr_matrix(a)
    row_index = np.repeat(np.arange(a.shape[0]), np.diff(a.indptr))
    if a.nnz:
        lo, hi = _extrema(np.log2(np.abs(a.data)), row_index, a.shape[0])
        spans = np.exp2(hi[np.isfinite(lo)] - lo[np.isfinite(lo)])
    else:
        spans = np.array([])
    return {"rows": a.shape[0], "columns": a.shape[1], "nonzeros": a.nnz,
            "matrix": nonzero_range(a.data), "rhs": nonzero_range(b),
            "objective": nonzero_range(c), "finite_bounds": nonzero_range(np.r_[lower, upper]),
            "row_ratio_quantiles": dict(zip(("p50", "p90", "p99", "max"),
                 map(float, np.quantile(spans, [.5, .9, .99, 1])))) if spans.size else {}}


def original_quality(a, b, c, lower, upper, senses, x, pi, rc, objective_constant=0.0):
    """Check mapped vectors in original units; do not conflate this with domain QC."""
    x, pi, rc = map(np.asarray, (x, pi, rc))
    if not all(np.all(np.isfinite(v)) for v in (x, pi, rc)):
        raise ValueError("Nonfinite solution cannot be accepted")
    activity = a @ x
    residual = activity - b
    senses = np.asarray(senses)
    violation = np.where(senses == "<", np.maximum(residual, 0),
                         np.where(senses == ">", np.maximum(-residual, 0), np.abs(residual)))
    bound_violation = np.maximum(0, np.maximum(lower - x, x - upper))
    row_dual_sign = np.where(senses == "<", np.maximum(pi, 0),
                            np.where(senses == ">", np.maximum(-pi, 0), 0))
    lower_finite, upper_finite = np.isfinite(lower), np.isfinite(upper)
    rc_sign = np.maximum(np.where(~lower_finite, np.maximum(rc, 0), 0),
                         np.where(~upper_finite, np.maximum(-rc, 0), 0))
    lower_comp = np.maximum(rc[lower_finite], 0) * (x[lower_finite] - lower[lower_finite])
    upper_comp = np.maximum(-rc[upper_finite], 0) * (upper[upper_finite] - x[upper_finite])
    stationarity = c - a.T @ pi - rc
    primal = float(c @ x + objective_constant)
    dual = float(b @ pi + np.minimum(rc[upper_finite], 0) @ upper[upper_finite]
                 + np.maximum(rc[lower_finite], 0) @ lower[lower_finite] + objective_constant)
    maximum = lambda v: float(np.max(np.abs(v), initial=0))
    return {"maximum_constraint_violation": maximum(violation),
            "maximum_bound_violation": maximum(bound_violation),
            "maximum_stationarity_residual": maximum(stationarity),
            "maximum_dual_sign_violation": max(maximum(row_dual_sign), maximum(rc_sign)),
            "maximum_complementarity": max(maximum(pi * residual), maximum(lower_comp), maximum(upper_comp)),
            "primal_objective": primal, "dual_objective_candidate_not_certified_bound": dual,
            "relative_objective_gap": abs(primal - dual) / max(1., abs(primal), abs(dual)),
            "domain_qc": "NOT_RUN_ARRAY_LEVEL_DIAGNOSTIC_ONLY"}
