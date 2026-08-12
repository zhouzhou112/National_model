"""Compare an engineering-only relaxed Barrier result with a strict root.

The candidate remains scientifically unaccepted regardless of this audit.  The
audit only answers whether national-scale capacity, generation and cost totals
are close enough to justify further solver-parameter experiments.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_series(path: Path, key: str, value: str) -> dict[str, float]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = csv.DictReader(handle)
        return {str(row[key]): float(row[value]) for row in rows}


def _relative_difference(candidate: float, reference: float) -> float:
    scale = max(abs(reference), 1e-12)
    return abs(candidate - reference) / scale


def _normalized_l1(
    candidate: dict[str, float], reference: dict[str, float]
) -> tuple[float, list[dict[str, float | str]]]:
    labels = sorted(set(candidate).union(reference))
    scale = max(sum(abs(reference.get(label, 0.0)) for label in labels), 1e-12)
    rows = []
    for label in labels:
        candidate_value = candidate.get(label, 0.0)
        reference_value = reference.get(label, 0.0)
        rows.append(
            {
                "label": label,
                "candidate": candidate_value,
                "reference": reference_value,
                "absolute_difference": abs(candidate_value - reference_value),
                "difference_as_reference_total_fraction": (
                    abs(candidate_value - reference_value) / scale
                ),
            }
        )
    rows.sort(
        key=lambda row: float(row["difference_as_reference_total_fraction"]),
        reverse=True,
    )
    return (
        sum(float(row["absolute_difference"]) for row in rows) / scale,
        rows,
    )


def audit(
    candidate_root: Path,
    reference_root: Path,
    *,
    objective_limit: float,
    capacity_l1_limit: float,
    generation_l1_limit: float,
    period_generation_limit: float,
) -> dict[str, Any]:
    analysis_root = candidate_root / "engineering_macro_analysis"
    candidate_contract = _read_json(
        analysis_root / "engineering_analysis_contract.json"
    )
    candidate_summary = _read_json(analysis_root / "annual_summary.json")
    reference_summary = _read_json(reference_root / "annual_summary.json")
    candidate_solve = _read_json(candidate_root / "solve_report.json")
    reference_solve = _read_json(reference_root / "solve_report.json")
    candidate_qc = _read_json(analysis_root / "solution_qc.json")

    identity_keys = (
        "planning_year",
        "scenario_id",
        "optimization_hours",
        "optimization_start_hour",
    )
    identity = {
        key: {
            "candidate": candidate_summary.get(key),
            "reference": reference_summary.get(key),
            "matches": candidate_summary.get(key) == reference_summary.get(key),
        }
        for key in identity_keys
    }
    identity_match = all(bool(item["matches"]) for item in identity.values())

    objective_difference = _relative_difference(
        float(candidate_summary["objective_million_cny_per_year"]),
        float(reference_summary["objective_million_cny_per_year"]),
    )
    period_generation_difference = _relative_difference(
        float(candidate_summary["period_generation_gwh"]),
        float(reference_summary["period_generation_gwh"]),
    )
    period_load_difference = _relative_difference(
        float(candidate_summary["period_load_gwh"]),
        float(reference_summary["period_load_gwh"]),
    )

    candidate_capacity = _read_series(
        analysis_root / "annual_capacity_by_technology.csv",
        "technology",
        "capacity",
    )
    reference_capacity = _read_series(
        reference_root / "annual_capacity_by_technology.csv",
        "technology",
        "capacity",
    )
    capacity_l1, capacity_rows = _normalized_l1(
        candidate_capacity, reference_capacity
    )
    candidate_generation = _read_series(
        analysis_root / "annual_generation_by_technology.csv",
        "technology",
        "generation_gwh",
    )
    reference_generation = _read_series(
        reference_root / "annual_generation_by_technology.csv",
        "technology",
        "generation_gwh",
    )
    generation_l1, generation_rows = _normalized_l1(
        candidate_generation, reference_generation
    )

    hard_checks = candidate_qc.get("hard_checks", {})
    failed_hard_checks = sorted(
        str(name) for name, passed in hard_checks.items() if not bool(passed)
    )
    numeric_values = [
        objective_difference,
        period_generation_difference,
        period_load_difference,
        capacity_l1,
        generation_l1,
    ]
    finite = all(math.isfinite(value) for value in numeric_values)
    macro_pass = bool(
        identity_match
        and finite
        and candidate_contract.get("scientifically_accepted") is False
        and candidate_solve.get("run_completion_status")
        == "ENGINEERING_BARRIER_CHECKPOINT_COMPLETE"
        and objective_difference <= objective_limit
        and period_generation_difference <= period_generation_limit
        and capacity_l1 <= capacity_l1_limit
        and generation_l1 <= generation_l1_limit
    )
    return {
        "schema_version": "cispo_relaxed_barrier_macro_comparison_v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": "MACRO_PASS" if macro_pass else "MACRO_FAIL",
        "scientifically_accepted": False,
        "candidate_root": str(candidate_root.resolve()),
        "reference_root": str(reference_root.resolve()),
        "identity": identity,
        "identity_match": identity_match,
        "thresholds": {
            "objective_relative_difference": objective_limit,
            "capacity_normalized_l1": capacity_l1_limit,
            "generation_normalized_l1": generation_l1_limit,
            "period_generation_relative_difference": period_generation_limit,
        },
        "metrics": {
            "objective_relative_difference": objective_difference,
            "period_load_relative_difference": period_load_difference,
            "period_generation_relative_difference": period_generation_difference,
            "capacity_normalized_l1": capacity_l1,
            "generation_normalized_l1": generation_l1,
            "candidate_solver_runtime_seconds": candidate_solve.get(
                "runtime_seconds"
            ),
            "reference_solver_runtime_seconds": reference_solve.get(
                "runtime_seconds"
            ),
            "candidate_barrier_iterations": candidate_solve.get(
                "iteration_counts", {}
            ).get("barrier"),
            "reference_barrier_iterations": reference_solve.get(
                "iteration_counts", {}
            ).get("barrier"),
        },
        "candidate_raw_qc_status": candidate_qc.get("status"),
        "candidate_failed_hard_checks": failed_hard_checks,
        "largest_capacity_differences": capacity_rows[:10],
        "largest_generation_differences": generation_rows[:10],
        "interpretation": (
            "A MACRO_PASS only qualifies the parameter set for longer local "
            "engineering tests. It does not relax the scientific result contract."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-root", required=True)
    parser.add_argument("--reference-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--objective-limit", type=float, default=0.01)
    parser.add_argument("--capacity-l1-limit", type=float, default=0.02)
    parser.add_argument("--generation-l1-limit", type=float, default=0.02)
    parser.add_argument("--period-generation-limit", type=float, default=0.005)
    args = parser.parse_args()
    report = audit(
        Path(args.candidate_root),
        Path(args.reference_root),
        objective_limit=args.objective_limit,
        capacity_l1_limit=args.capacity_l1_limit,
        generation_l1_limit=args.generation_l1_limit,
        period_generation_limit=args.period_generation_limit,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
