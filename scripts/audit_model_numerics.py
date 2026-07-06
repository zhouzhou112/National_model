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
from cispo_model.diagnostics import model_statistics
from cispo_model.monolithic import build_full_year_monolithic


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
        "variable_families": {
            family: int(count)
            for family, count in pd.Series([_family(name) for name in variable_names])
            .value_counts()
            .sort_index()
            .items()
        },
    }
    return report, family_frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/optimization_2030.json")
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--output-dir", default="outputs/model_numerical_audit")
    parser.add_argument("--skip-full-max-cf", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.hours <= 8760:
        raise SystemExit("--hours must be in [1, 8760]")

    config = load_model_config(args.config)
    data = load_model_data(config)
    artifacts = build_full_year_monolithic(
        config,
        data,
        compute_max_cf=not args.skip_full_max_cf,
        optimization_hours=args.hours,
    )
    report, family_frame = audit_model(artifacts.model)
    report.update(
        config=str(config.path),
        audit_hours=args.hours,
        optimized=False,
        reservoir_flow_variable_scale_m3s=float(
            config.raw["hydro"]["reservoir_flow_variable_scale_m3s"]
        ),
        reservoir_volume_variable_scale_m3=float(
            config.raw["hydro"]["reservoir_volume_variable_scale_m3"]
        ),
    )
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
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
