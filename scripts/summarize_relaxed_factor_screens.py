"""Audit and shortlist paired five-iteration Barrier factor screens.

This tool compares structural factorization cost against the current
NF1/Scale2 Base-744 engineering baseline.  It never selects a production
profile and never upgrades a short screen to a checkpoint or science result.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


CASE_TAGS = ("nf0_scale2", "nf1_scaleauto", "nf0_scaleauto")
IDENTITY_FIELDS = (
    "lp_gurobi_fingerprint",
    "lp_identity_variables",
    "lp_identity_constraints",
    "lp_identity_nonzeros",
    "original_rows",
    "original_columns",
    "original_nonzeros",
    "resolved_scientific_configuration_sha256",
    "scenario_configuration_sha256",
)
FACTOR_FIELDS = (
    "presolved_rows",
    "presolved_columns",
    "presolved_nonzeros",
    "dense_columns",
    "aa_transpose_nonzeros",
    "factor_nonzeros",
    "factor_operations",
)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_int(path: Path) -> int | None:
    if not path.is_file():
        return None
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except ValueError:
        return None


def _ratio(value: Any, baseline: Any) -> float | None:
    if value is None or baseline in (None, 0):
        return None
    return float(value) / float(baseline)


def _case(
    tag: str,
    baseline: dict[str, Any],
    control_root: Path,
    material_reduction_fraction: float,
) -> dict[str, Any]:
    control = control_root / tag
    audit_path = control / "solver_audit.json"
    audit = _read_json(audit_path)
    return_code = _read_int(control / "return_code.txt")
    stderr_path = control / "stderr.log"
    stderr_bytes = stderr_path.stat().st_size if stderr_path.is_file() else None
    barrier = (audit.get("telemetry_phase_summaries") or {}).get("barrier") or {}

    identity_matches = {
        field: (
            audit.get(field) is not None
            and baseline.get(field) is not None
            and audit.get(field) == baseline.get(field)
        )
        for field in IDENTITY_FIELDS
    }
    missing_factor_fields = [field for field in FACTOR_FIELDS if audit.get(field) is None]
    failures: list[str] = []
    if not audit:
        failures.append("solver_audit_missing")
    if return_code not in (0, 2):
        failures.append("unexpected_runner_return_code")
    if stderr_bytes != 0:
        failures.append("stderr_nonempty_or_missing")
    if int(audit.get("barrier_iterations") or -1) != 5:
        failures.append("barrier_iteration_count_not_five")
    if int(audit.get("numerical_trouble_count") or 0) != 0:
        failures.append("numerical_trouble_encountered")
    if missing_factor_fields:
        failures.append("factor_metrics_missing")
    if not all(identity_matches.values()):
        failures.append("lp_or_scientific_identity_mismatch")

    factor_ops_ratio = _ratio(
        audit.get("factor_operations"), baseline.get("factor_operations")
    )
    factor_nz_ratio = _ratio(
        audit.get("factor_nonzeros"), baseline.get("factor_nonzeros")
    )
    structural_improvement = bool(
        factor_ops_ratio is not None
        and factor_nz_ratio is not None
        and (
            factor_ops_ratio <= 1.0 - material_reduction_fraction
            or factor_nz_ratio <= 1.0 - material_reduction_fraction
        )
    )
    valid = not failures
    return {
        "tag": tag,
        "audit_path": str(audit_path.resolve()),
        "return_code": return_code,
        "stderr_bytes": stderr_bytes,
        "valid_paired_screen": valid,
        "screen_failures": failures,
        "identity_matches": identity_matches,
        "missing_factor_fields": missing_factor_fields,
        "factor_operations": audit.get("factor_operations"),
        "factor_operations_ratio_to_baseline": factor_ops_ratio,
        "factor_nonzeros": audit.get("factor_nonzeros"),
        "factor_nonzeros_ratio_to_baseline": factor_nz_ratio,
        "dense_columns": audit.get("dense_columns"),
        "aa_transpose_nonzeros": audit.get("aa_transpose_nonzeros"),
        "presolved_nonzeros": audit.get("presolved_nonzeros"),
        "barrier_iterations": audit.get("barrier_iterations"),
        "observed_seconds_per_iteration": barrier.get(
            "observed_seconds_per_iteration"
        ),
        "last_primal_infeasibility": barrier.get("last_primal_infeasibility"),
        "last_dual_infeasibility": barrier.get("last_dual_infeasibility"),
        "last_complementarity": barrier.get("last_complementarity"),
        "last_raw_primal_dual_objective_gap": barrier.get(
            "last_raw_primal_dual_objective_gap"
        ),
        "material_structural_improvement": structural_improvement,
        "shortlist_eligible": valid and structural_improvement,
        "scientifically_accepted": False,
    }


def summarize(
    baseline_audit_path: Path,
    control_root: Path,
    material_reduction_fraction: float = 0.05,
) -> dict[str, Any]:
    baseline = _read_json(baseline_audit_path)
    if not baseline:
        raise ValueError(f"Missing baseline audit: {baseline_audit_path}")
    missing_baseline = [
        field
        for field in (*IDENTITY_FIELDS, *FACTOR_FIELDS)
        if baseline.get(field) is None
    ]
    if missing_baseline:
        raise ValueError(
            "Baseline audit lacks required fields: " + ", ".join(missing_baseline)
        )
    cases = [
        _case(tag, baseline, control_root, material_reduction_fraction)
        for tag in CASE_TAGS
    ]
    valid = [case for case in cases if case["valid_paired_screen"]]
    shortlist = sorted(
        (case for case in valid if case["shortlist_eligible"]),
        key=lambda case: (
            case["factor_operations_ratio_to_baseline"],
            case["factor_nonzeros_ratio_to_baseline"],
            case["observed_seconds_per_iteration"] or float("inf"),
        ),
    )
    all_valid = len(valid) == len(CASE_TAGS)
    status = (
        "SCREEN_AUDIT_INCOMPLETE"
        if not all_valid
        else "SHORTLIST_READY"
        if shortlist
        else "NO_MATERIAL_FACTOR_IMPROVEMENT"
    )
    return {
        "schema_version": "cispo_relaxed_factor_screen_summary_v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "scientifically_accepted": False,
        "automatic_winner_selected": False,
        "baseline_audit_path": str(baseline_audit_path.resolve()),
        "baseline_profile_id": baseline.get("solver_profile_id"),
        "material_reduction_fraction": material_reduction_fraction,
        "all_paired_screens_valid": all_valid,
        "shortlist_tags": [case["tag"] for case in shortlist],
        "ranking_basis": (
            "Factor Ops ratio, then Factor NZ ratio, then observed seconds per "
            "iteration. Shortlisting requires >= configured structural reduction; "
            "a full 744 solve and exact macro A/B remain mandatory."
        ),
        "cases": cases,
    }


CSV_FIELDS = (
    "tag",
    "valid_paired_screen",
    "factor_operations_ratio_to_baseline",
    "factor_nonzeros_ratio_to_baseline",
    "factor_operations",
    "factor_nonzeros",
    "dense_columns",
    "presolved_nonzeros",
    "observed_seconds_per_iteration",
    "last_primal_infeasibility",
    "last_dual_infeasibility",
    "last_complementarity",
    "last_raw_primal_dual_objective_gap",
    "material_structural_improvement",
    "shortlist_eligible",
    "screen_failures",
    "scientifically_accepted",
)


def write_csv(path: Path, cases: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for case in cases:
            row = {field: case.get(field) for field in CSV_FIELDS}
            row["screen_failures"] = ";".join(case["screen_failures"])
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-audit", required=True)
    parser.add_argument("--control-root", required=True)
    parser.add_argument("--material-reduction-fraction", type=float, default=0.05)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-csv", required=True)
    args = parser.parse_args()
    if not 0.0 < args.material_reduction_fraction < 1.0:
        raise SystemExit("--material-reduction-fraction must be in (0, 1)")
    report = summarize(
        Path(args.baseline_audit),
        Path(args.control_root),
        args.material_reduction_fraction,
    )
    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    write_csv(Path(args.output_csv), report["cases"])
    print(json.dumps({"status": report["status"], "shortlist_tags": report["shortlist_tags"]}))
    if report["status"] == "SCREEN_AUDIT_INCOMPLETE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
