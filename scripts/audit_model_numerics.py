"""Build a controlled CISPO horizon and audit LP numerical scaling by block.

This script never optimizes the model. It records coefficient, RHS, bound and
objective ranges and identifies the constraint families with the worst row
scaling. The output is intended to be compared before and after mathematically
equivalent variable scaling changes.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cispo_model.config import ROOT, load_model_config
from cispo_model.data import load_model_data
from cispo_model.diagnostics import configure_gurobi, model_statistics
from cispo_model.monolithic import build_full_year_monolithic
from cispo_model.preflight import estimate_full_model_scale


INDEX_SUFFIX = re.compile(r"\[.*$")
DYNAMIC_SUFFIX = re.compile(r"_(?:p|h|row|b|k)\d+(?=_|$)")
TRAILING_INDEX = re.compile(r"_\d+$")


def _family(name: str) -> str:
    base = INDEX_SUFFIX.sub("", name)
    return TRAILING_INDEX.sub("_#", DYNAMIC_SUFFIX.sub("_#", base))


def _quantiles(values: np.ndarray) -> dict[str, float]:
    if not len(values):
        return {}
    probabilities = (0.0, 0.01, 0.10, 0.50, 0.90, 0.99, 1.0)
    result = np.quantile(values, probabilities)
    return {
        f"p{int(probability * 100):02d}": float(value)
        for probability, value in zip(probabilities, result)
    }


def _family_counts(names: list[str]) -> dict[str, int]:
    return {
        family: int(count)
        for family, count in pd.Series([_family(name) for name in names])
        .value_counts()
        .sort_index()
        .items()
    }


def _largest_matrix_coefficients(
    model,
    *,
    count: int = 30,
    matrix=None,
    constraint_names: list[str] | None = None,
    variable_names: list[str] | None = None,
) -> list[dict[str, object]]:
    """Identify the largest coefficients without materializing COO row arrays."""
    model.update()
    if matrix is None:
        matrix = model.getA().tocsr()
    if matrix.nnz == 0:
        return []
    absolute = np.abs(matrix.data)
    sample_count = min(int(count), int(matrix.nnz))
    candidate = np.argpartition(absolute, -sample_count)[-sample_count:]
    order = candidate[np.argsort(absolute[candidate])[::-1]]
    if constraint_names is None:
        constraint_names = [
            constraint.ConstrName for constraint in model.getConstrs()
        ]
    if variable_names is None:
        variable_names = [
            variable.VarName for variable in model.getVars()
        ]
    result: list[dict[str, object]] = []
    for position in order:
        row = int(np.searchsorted(matrix.indptr, position, side="right") - 1)
        column = int(matrix.indices[position])
        constraint_name = constraint_names[row]
        result.append(
            {
                "constraint": constraint_name,
                "constraint_family": _family(constraint_name),
                "variable": variable_names[column],
                "coefficient": float(matrix.data[position]),
                "coefficient_abs": float(absolute[position]),
            }
        )
    return result


def _largest_objective_coefficients(
    model,
    *,
    count: int = 30,
) -> list[dict[str, object]]:
    model.update()
    variables = model.getVars()
    if not variables:
        return []
    objective = np.asarray(model.getAttr("Obj", variables), dtype=float)
    nonzero = np.flatnonzero(objective)
    if not len(nonzero):
        return []
    sample_count = min(int(count), int(len(nonzero)))
    absolute = np.abs(objective[nonzero])
    candidate = np.argpartition(absolute, -sample_count)[-sample_count:]
    order = candidate[np.argsort(absolute[candidate])[::-1]]
    return [
        {
            "variable": variables[int(nonzero[position])].VarName,
            "objective_coefficient": float(objective[int(nonzero[position])]),
            "objective_coefficient_abs": float(absolute[position]),
        }
        for position in order
    ]


def _top_rows(
    names: list[str],
    row_min: np.ndarray,
    row_max: np.ndarray,
    rhs: np.ndarray,
    count: int = 30,
) -> list[dict[str, object]]:
    ratio = np.divide(
        row_max,
        row_min,
        out=np.ones_like(row_max),
        where=row_min > 0.0,
    )
    order = np.argsort(ratio)[-count:][::-1]
    return [
        {
            "constraint": names[int(row)],
            "family": _family(names[int(row)]),
            "coefficient_min_abs": float(row_min[row]),
            "coefficient_max_abs": float(row_max[row]),
            "row_coefficient_ratio": float(ratio[row]),
            "rhs": float(rhs[row]),
        }
        for row in order
        if row_max[row] > 0.0
    ]


def audit_model(model) -> tuple[dict[str, object], pd.DataFrame]:
    model.update()
    matrix = model.getA().tocsr()
    abs_coefficients = np.abs(matrix.data)
    constraints = model.getConstrs()
    variables = model.getVars()
    constraint_names = [constraint.ConstrName for constraint in constraints]
    rhs = np.asarray(model.getAttr("RHS", constraints), dtype=float)
    senses = model.getAttr("Sense", constraints)
    variable_names = [variable.VarName for variable in variables]
    lower = np.asarray(model.getAttr("LB", variables), dtype=float)
    upper = np.asarray(model.getAttr("UB", variables), dtype=float)
    objective = np.asarray(model.getAttr("Obj", variables), dtype=float)

    row_min = np.zeros(matrix.shape[0], dtype=float)
    row_max = np.zeros(matrix.shape[0], dtype=float)
    family_stats: dict[str, dict[str, object]] = defaultdict(
        lambda: {
            "rows": 0,
            "nonzeros": 0,
            "coefficient_min_abs": float("inf"),
            "coefficient_max_abs": 0.0,
            "maximum_row_coefficient_ratio": 1.0,
            "rhs_min_abs_nonzero": float("inf"),
            "rhs_max_abs": 0.0,
            "tiny_coefficients_below_1e_8": 0,
            "large_coefficients_above_1e_3": 0,
        }
    )
    for row, name in enumerate(constraint_names):
        start, stop = matrix.indptr[row], matrix.indptr[row + 1]
        values = np.abs(matrix.data[start:stop])
        values = values[values > 0.0]
        family = _family(name)
        stats = family_stats[family]
        stats["rows"] = int(stats["rows"]) + 1
        stats["nonzeros"] = int(stats["nonzeros"]) + len(values)
        absolute_rhs = abs(rhs[row])
        stats["rhs_max_abs"] = max(float(stats["rhs_max_abs"]), absolute_rhs)
        if absolute_rhs > 0.0:
            stats["rhs_min_abs_nonzero"] = min(
                float(stats["rhs_min_abs_nonzero"]), absolute_rhs
            )
        if not len(values):
            continue
        row_min[row] = float(values.min())
        row_max[row] = float(values.max())
        ratio = row_max[row] / row_min[row]
        stats["coefficient_min_abs"] = min(
            float(stats["coefficient_min_abs"]), row_min[row]
        )
        stats["coefficient_max_abs"] = max(
            float(stats["coefficient_max_abs"]), row_max[row]
        )
        stats["maximum_row_coefficient_ratio"] = max(
            float(stats["maximum_row_coefficient_ratio"]), ratio
        )
        stats["tiny_coefficients_below_1e_8"] = int(
            stats["tiny_coefficients_below_1e_8"]
        ) + int((values < 1e-8).sum())
        stats["large_coefficients_above_1e_3"] = int(
            stats["large_coefficients_above_1e_3"]
        ) + int((values > 1e3).sum())

    family_rows = []
    for family, stats in family_stats.items():
        cleaned = dict(stats)
        for key in ("coefficient_min_abs", "rhs_min_abs_nonzero"):
            if not np.isfinite(float(cleaned[key])):
                cleaned[key] = 0.0
        family_rows.append({"constraint_family": family, **cleaned})
    family_frame = pd.DataFrame(family_rows).sort_values(
        ["maximum_row_coefficient_ratio", "rhs_max_abs"], ascending=False
    )

    finite_lower = lower[np.isfinite(lower) & (np.abs(lower) < 1e100)]
    finite_upper = upper[np.isfinite(upper) & (np.abs(upper) < 1e100)]
    nonzero_objective = np.abs(objective[objective != 0.0])
    positive_rhs = np.abs(rhs[rhs != 0.0])
    row_ratio = np.divide(
        row_max,
        row_min,
        out=np.ones_like(row_max),
        where=row_min > 0.0,
    )
    report: dict[str, object] = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "model_statistics": model_statistics(model),
        "raw_largest_matrix_coefficients": _largest_matrix_coefficients(
            model,
            matrix=matrix,
            constraint_names=constraint_names,
            variable_names=variable_names,
        ),
        "raw_largest_objective_coefficients": (
            _largest_objective_coefficients(model)
        ),
        "matrix_coefficient_abs_quantiles": _quantiles(abs_coefficients),
        "positive_rhs_abs_quantiles": _quantiles(positive_rhs),
        "finite_lower_bound_abs_quantiles": _quantiles(np.abs(finite_lower)),
        "finite_upper_bound_abs_quantiles": _quantiles(np.abs(finite_upper)),
        "nonzero_objective_abs_quantiles": _quantiles(nonzero_objective),
        "row_coefficient_ratio_quantiles": _quantiles(row_ratio[row_max > 0.0]),
        "counts": {
            "matrix_coefficients_below_1e_8": int((abs_coefficients < 1e-8).sum()),
            "matrix_coefficients_above_1e_3": int((abs_coefficients > 1e3).sum()),
            "positive_rhs_below_1e_8": int((positive_rhs < 1e-8).sum()),
            "positive_rhs_above_1e8": int((positive_rhs > 1e8).sum()),
        },
        "worst_scaled_rows": _top_rows(
            constraint_names, row_min, row_max, rhs
        ),
        "largest_rhs_constraints": [
            {
                "constraint": constraint_names[int(row)],
                "family": _family(constraint_names[int(row)]),
                "sense": senses[int(row)],
                "rhs": float(rhs[row]),
            }
            for row in np.argsort(np.abs(rhs))[-30:][::-1]
        ],
        "smallest_positive_rhs_constraints": [
            {
                "constraint": constraint_names[int(row)],
                "family": _family(constraint_names[int(row)]),
                "sense": senses[int(row)],
                "rhs": float(rhs[row]),
            }
            for row in np.argsort(np.where(np.abs(rhs) > 0.0, np.abs(rhs), np.inf))[:30]
        ],
        "variable_families": _family_counts(variable_names),
    }
    return report, family_frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/optimization_2030.json")
    parser.add_argument("--scenario-config")
    parser.add_argument("--solver-config")
    parser.add_argument("--formulation-config")
    parser.add_argument("--planning-year", type=int)
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument(
        "--diagnostic-start-hour",
        type=int,
        default=0,
        help="Zero-based first model hour of the contiguous audit window.",
    )
    parser.add_argument("--output-dir", default="outputs/model_numerical_audit")
    parser.add_argument("--skip-full-max-cf", action="store_true")
    parser.add_argument(
        "--max-estimated-nonzeros",
        type=int,
        default=50_000_000,
        help=(
            "Refuse explicit matrix materialization above this prebuild "
            "estimate unless --allow-oversized-matrix-audit is supplied."
        ),
    )
    parser.add_argument(
        "--allow-oversized-matrix-audit",
        action="store_true",
        help=(
            "Explicitly allow a numerical audit whose estimated matrix "
            "exceeds the safety limit; intended only for a sized compute node."
        ),
    )
    parser.add_argument(
        "--presolve",
        action="store_true",
        help="Run Gurobi presolve only and record its reduced dimensions.",
    )
    parser.add_argument(
        "--presolve-aggregate",
        type=int,
        choices=(0, 1, 2),
        help="Diagnostic-only Aggregate override applied before presolve.",
    )
    parser.add_argument(
        "--presolve-agg-fill",
        type=int,
        help="Diagnostic-only non-negative AggFill override before presolve.",
    )
    parser.add_argument(
        "--presolve-pre-sparsify",
        type=int,
        choices=(-1, 0, 1, 2),
        help="Diagnostic-only PreSparsify override applied before presolve.",
    )
    args = parser.parse_args()
    if not 1 <= args.hours <= 8760:
        raise SystemExit("--hours must be in [1, 8760]")
    if args.diagnostic_start_hour < 0:
        raise SystemExit("--diagnostic-start-hour must be nonnegative")
    if args.diagnostic_start_hour + args.hours > 8760:
        raise SystemExit(
            "--diagnostic-start-hour + --hours must not exceed 8760"
        )
    if args.presolve_agg_fill is not None and args.presolve_agg_fill < 0:
        raise SystemExit("--presolve-agg-fill must be non-negative")
    if args.max_estimated_nonzeros < 1:
        raise SystemExit("--max-estimated-nonzeros must be positive")
    if (
        not args.presolve
        and (
            args.presolve_aggregate is not None
            or args.presolve_agg_fill is not None
            or args.presolve_pre_sparsify is not None
        )
    ):
        raise SystemExit("Presolve parameter overrides require --presolve")

    base_config = load_model_config(
        args.config,
        args.scenario_config,
        args.solver_config,
        args.formulation_config,
    )
    config = (
        base_config.for_planning_year(args.planning_year)
        if args.planning_year is not None
        else base_config
    )
    data = load_model_data(config)
    scale_estimate = estimate_full_model_scale(
        config,
        data,
        args.hours,
    )
    if (
        scale_estimate.nonzeros > args.max_estimated_nonzeros
        and not args.allow_oversized_matrix_audit
    ):
        raise SystemExit(
            "Refusing oversized explicit matrix audit: estimated "
            f"{scale_estimate.nonzeros:,} nonzeros exceeds "
            f"{args.max_estimated_nonzeros:,}; use preflight for full-year "
            "scale evidence or explicitly allow a sized-node audit."
        )
    artifacts = build_full_year_monolithic(
        config,
        data,
        compute_max_cf=not args.skip_full_max_cf,
        optimization_hours=args.hours,
        optimization_start_hour=args.diagnostic_start_hour,
    )
    report, family_frame = audit_model(artifacts.model)
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.presolve:
        configure_gurobi(
            artifacts.model,
            config,
            output_dir / "gurobi_presolve.log",
        )
        presolve_overrides: dict[str, int] = {}
        if args.presolve_aggregate is not None:
            artifacts.model.Params.Aggregate = int(
                args.presolve_aggregate
            )
            presolve_overrides["Aggregate"] = int(
                args.presolve_aggregate
            )
        if args.presolve_agg_fill is not None:
            artifacts.model.Params.AggFill = int(args.presolve_agg_fill)
            presolve_overrides["AggFill"] = int(args.presolve_agg_fill)
        if args.presolve_pre_sparsify is not None:
            artifacts.model.Params.PreSparsify = int(
                args.presolve_pre_sparsify
            )
            presolve_overrides["PreSparsify"] = int(
                args.presolve_pre_sparsify
            )
        presolved_model = artifacts.model.presolve()
        presolved_statistics = model_statistics(presolved_model)
        report["presolved_model_statistics"] = presolved_statistics
        report["presolved_variable_families"] = _family_counts(
            [
                variable.VarName
                for variable in presolved_model.getVars()
            ]
        )
        report["presolved_constraint_families"] = _family_counts(
            [
                constraint.ConstrName
                for constraint in presolved_model.getConstrs()
            ]
        )
        report["presolved_largest_matrix_coefficients"] = (
            _largest_matrix_coefficients(presolved_model)
        )
        report["presolved_largest_objective_coefficients"] = (
            _largest_objective_coefficients(presolved_model)
        )
        raw_statistics = report["model_statistics"]
        raw_max_coefficient = float(
            raw_statistics["coefficient_max_abs"]
        )
        presolved_max_coefficient = float(
            presolved_statistics["coefficient_max_abs"]
        )
        amplification_ratio = (
            presolved_max_coefficient / raw_max_coefficient
            if raw_max_coefficient > 0.0
            else None
        )
        report["presolve_coefficient_amplification"] = {
            "raw_max_matrix_coefficient_abs": raw_max_coefficient,
            "presolved_max_matrix_coefficient_abs": (
                presolved_max_coefficient
            ),
            "max_matrix_coefficient_amplification_ratio": (
                amplification_ratio
            ),
            "presolve_increased_max_matrix_coefficient": bool(
                presolved_max_coefficient
                > raw_max_coefficient * (1.0 + 1e-12)
            ),
            "largest_presolved_entry": (
                report["presolved_largest_matrix_coefficients"][0]
                if report["presolved_largest_matrix_coefficients"]
                else None
            ),
        }
        report["presolve_parameter_overrides"] = presolve_overrides
        report["presolve_only"] = True
    report.update(
        config=str(config.path),
        scenario_config=(
            str(config.scenario_path) if config.scenario_path else None
        ),
        solver_config=(
            str(config.solver_path) if config.solver_path else None
        ),
        planning_year=int(config.planning_year),
        audit_hours=args.hours,
        audit_start_hour=args.diagnostic_start_hour,
        audit_stop_hour_exclusive=(
            args.diagnostic_start_hour + args.hours
        ),
        scale_estimate=scale_estimate.__dict__,
        max_estimated_nonzeros=int(args.max_estimated_nonzeros),
        oversized_matrix_audit_explicitly_allowed=bool(
            args.allow_oversized_matrix_audit
        ),
        optimized=False,
        reservoir_flow_variable_scale_m3s=float(
            config.raw["hydro"]["reservoir_flow_variable_scale_m3s"]
        ),
        reservoir_volume_variable_scale_m3=float(
            config.raw["hydro"]["reservoir_volume_variable_scale_m3"]
        ),
    )
    (output_dir / "numerical_audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    family_frame.to_csv(
        output_dir / "constraint_family_scaling.csv",
        index=False,
        encoding="utf-8-sig",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
