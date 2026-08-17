"""Audit an accepted deferred-crossover result against an accepted strict LP.

Both roots remain truncated-horizon engineering evidence.  Passing this audit
proves that the saved Barrier checkpoint can be consumed by an independent
Crossover=2 run without changing the exact LP or national macro accounts; it
does not promote 744 h outputs to annual scientific results.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cispo_model.io_contract import (  # noqa: E402
    validate_input_manifest,
    validate_result_manifest,
)
from scripts.audit_relaxed_barrier_macro import (  # noqa: E402
    CARBON_ACCOUNT_FIELDS,
    OPERATION_ACCOUNT_FIELDS,
    _exact_ab_identity,
    _named_numeric_values,
    _normalized_l1,
    _read_json,
    _read_series,
    _relative_difference,
)


def _accepted_contract(root: Path) -> dict[str, Any]:
    solve = _read_json(root / "solve_report.json")
    qc = _read_json(root / "solution_qc.json")
    hard = qc.get("hard_checks")
    hard_pass = bool(
        isinstance(hard, dict)
        and len(hard) == 58
        and all(value is True for value in hard.values())
    )
    result_valid, result_failures = validate_result_manifest(root)
    input_valid, input_failures = validate_input_manifest(
        root / "input_manifest.csv"
    )
    accepted = bool(
        solve.get("status") == "OPTIMAL"
        and solve.get("solution_contract", {}).get("acceptance_status") == "PASS"
        and qc.get("status") == "PASS"
        and hard_pass
        and result_valid
        and input_valid
    )
    return {
        "accepted": accepted,
        "solver_status": solve.get("status"),
        "solver_acceptance_status": solve.get("solution_contract", {}).get(
            "acceptance_status"
        ),
        "solution_qc_status": qc.get("status"),
        "hard_check_count": len(hard) if isinstance(hard, dict) else None,
        "hard_checks_all_true": hard_pass,
        "result_manifest_valid": result_valid,
        "result_manifest_failures": result_failures,
        "input_manifest_valid": input_valid,
        "input_manifest_failures": input_failures,
        "solve_report": solve,
    }


def audit_pair(
    candidate_root: Path,
    reference_root: Path,
    *,
    objective_limit: float = 0.01,
    capacity_l1_limit: float = 0.02,
    generation_l1_limit: float = 0.02,
    period_generation_limit: float = 0.005,
    carbon_l1_limit: float = 0.02,
    operation_l1_limit: float = 0.05,
    cost_component_l1_limit: float = 0.02,
) -> dict[str, Any]:
    candidate_contract = _accepted_contract(candidate_root)
    reference_contract = _accepted_contract(reference_root)
    candidate_summary = _read_json(candidate_root / "annual_summary.json")
    reference_summary = _read_json(reference_root / "annual_summary.json")
    candidate_carbon = _read_json(candidate_root / "annual_carbon_ccs.json")
    reference_carbon = _read_json(reference_root / "annual_carbon_ccs.json")
    start = _read_json(candidate_root / "primal_dual_start_input.json")
    exact_identity = _exact_ab_identity(candidate_root, reference_root)

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
    capacity_l1, capacity_rows = _normalized_l1(
        _read_series(
            candidate_root / "annual_capacity_by_technology.csv",
            "technology",
            "capacity",
        ),
        _read_series(
            reference_root / "annual_capacity_by_technology.csv",
            "technology",
            "capacity",
        ),
    )
    generation_l1, generation_rows = _normalized_l1(
        _read_series(
            candidate_root / "annual_generation_by_technology.csv",
            "technology",
            "generation_gwh",
        ),
        _read_series(
            reference_root / "annual_generation_by_technology.csv",
            "technology",
            "generation_gwh",
        ),
    )
    carbon_l1, carbon_rows = _normalized_l1(
        _named_numeric_values(candidate_carbon, CARBON_ACCOUNT_FIELDS),
        _named_numeric_values(reference_carbon, CARBON_ACCOUNT_FIELDS),
    )
    operation_l1, operation_rows = _normalized_l1(
        _named_numeric_values(candidate_summary, OPERATION_ACCOUNT_FIELDS),
        _named_numeric_values(reference_summary, OPERATION_ACCOUNT_FIELDS),
    )
    candidate_cost_path = candidate_root / "cost_components.csv"
    reference_cost_path = reference_root / "cost_components.csv"
    cost_component_l1 = None
    cost_component_rows: list[dict[str, float | str]] = []
    if candidate_cost_path.is_file() and reference_cost_path.is_file():
        cost_component_l1, cost_component_rows = _normalized_l1(
            _read_series(
                candidate_cost_path,
                "cost_component",
                "value_million_cny_per_year",
            ),
            _read_series(
                reference_cost_path,
                "cost_component",
                "value_million_cny_per_year",
            ),
        )

    metrics = {
        "objective_relative_difference": objective_difference,
        "period_load_relative_difference": period_load_difference,
        "period_generation_relative_difference": period_generation_difference,
        "capacity_normalized_l1": capacity_l1,
        "generation_normalized_l1": generation_l1,
        "carbon_account_normalized_l1": carbon_l1,
        "operation_account_normalized_l1": operation_l1,
        "cost_component_normalized_l1": cost_component_l1,
    }
    finite = all(
        math.isfinite(value)
        for value in metrics.values()
        if value is not None
    )
    start_valid = bool(
        start.get("lp_warm_start") == 2
        and start.get("engineering_checkpoint_explicitly_allowed") is True
        and start.get("source_checkpoint_manifest_sha256")
        and start.get("scientific_input_manifest_identity", {}).get("sha256")
    )
    passed = bool(
        candidate_contract["accepted"]
        and reference_contract["accepted"]
        and exact_identity["matches"]
        and start_valid
        and finite
        and objective_difference <= objective_limit
        and period_generation_difference <= period_generation_limit
        and capacity_l1 <= capacity_l1_limit
        and generation_l1 <= generation_l1_limit
        and carbon_l1 <= carbon_l1_limit
        and operation_l1 <= operation_l1_limit
        and (
            cost_component_l1 is None
            or cost_component_l1 <= cost_component_l1_limit
        )
    )
    return {
        "schema_version": "cispo_accepted_deferred_crossover_pair_audit_v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": "PASS" if passed else "FAIL",
        "strict_test_result_accepted": passed,
        "scientifically_accepted": False,
        "result_use": "TEST_ONLY_TRUNCATED_HORIZON",
        "candidate_root": str(candidate_root.resolve()),
        "reference_root": str(reference_root.resolve()),
        "candidate_contract": {
            key: value
            for key, value in candidate_contract.items()
            if key != "solve_report"
        },
        "reference_contract": {
            key: value
            for key, value in reference_contract.items()
            if key != "solve_report"
        },
        "exact_ab_identity": exact_identity,
        "primal_dual_start_valid": start_valid,
        "primal_dual_start": start,
        "thresholds": {
            "objective_relative_difference": objective_limit,
            "capacity_normalized_l1": capacity_l1_limit,
            "generation_normalized_l1": generation_l1_limit,
            "period_generation_relative_difference": period_generation_limit,
            "carbon_account_normalized_l1": carbon_l1_limit,
            "operation_account_normalized_l1": operation_l1_limit,
            "cost_component_normalized_l1_when_available": (
                cost_component_l1_limit
            ),
        },
        "metrics": metrics,
        "largest_capacity_differences": capacity_rows[:20],
        "largest_generation_differences": generation_rows[:20],
        "carbon_account_differences": carbon_rows,
        "operation_account_differences": operation_rows,
        "cost_component_differences": cost_component_rows,
        "interpretation_limit": (
            "Passing proves the deferred Stage B route on this exact 744 h LP; "
            "it does not make the truncated horizon an annual scientific result."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-root", required=True)
    parser.add_argument("--reference-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = audit_pair(Path(args.candidate_root), Path(args.reference_root))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 2)


if __name__ == "__main__":
    main()
