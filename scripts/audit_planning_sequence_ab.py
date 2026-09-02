"""Audit matched CISPO planning-sequence Base/scenario output roots.

The report is deliberately result-use aware.  A truncated-horizon comparison
can verify implementation, state transfer and dispatch mechanisms, but it must
not be reported as an annual scientific value result.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cispo_model.io_contract import (  # noqa: E402
    validate_input_manifest,
    validate_result_manifest,
)
from cispo_model.solver_audit import collect_solver_run  # noqa: E402

YEARS = (2030, 2040, 2050, 2060)
FLEX_COST_PREFIX = "operating_flexible_load"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _cost_value_column(frame: pd.DataFrame) -> str:
    preferred = "value_million_cny_model_accounting_period"
    return preferred if preferred in frame.columns else "value_million_cny_per_year"


def _flex_cost_breakdown(output_dir: Path) -> dict[str, float]:
    frame = pd.read_csv(output_dir / "cost_components.csv")
    value_column = _cost_value_column(frame)
    mask = frame.cost_component.astype(str).str.startswith(FLEX_COST_PREFIX)
    selected = frame.loc[mask].copy()
    if "accounting_scope" not in selected.columns:
        selected["accounting_scope"] = np.where(
            selected.cost_component.astype(str).eq(
                "operating_flexible_load_v4_enablement"
            ),
            "ANNUALIZED_PLANNING_COST",
            "SELECTED_HORIZON_OPERATION_COST",
        )
    annualized = selected.accounting_scope.eq("ANNUALIZED_PLANNING_COST")
    return {
        "total": float(selected[value_column].sum()),
        "annualized": float(selected.loc[annualized, value_column].sum()),
        "selected_horizon": float(
            selected.loc[~annualized, value_column].sum()
        ),
    }


def _flex_metrics(output_dir: Path) -> dict[str, float]:
    path = output_dir / "flexible_load_dispatch.npz"
    if not path.is_file():
        return {
            "thermal_shift_throughput_gwh": 0.0,
            "ev_charge_relocation_gwh": 0.0,
            "national_peak_load_change_gw": 0.0,
        }
    with np.load(path) as values:
        thermal_keys = (
            "heating_shift_up_gw",
            "heating_shift_down_gw",
            "cooling_shift_up_gw",
            "cooling_shift_down_gw",
        )
        thermal = sum(float(np.abs(values[key]).sum()) for key in thermal_keys)
        relocation_key = (
            "ev_mobility_v1g_relocated_gw"
            if "ev_mobility_v1g_relocated_gw" in values
            else "ev_mobility_charge_deviation_gw"
        )
        ev_relocation = float(values[relocation_key].sum())
        baseline_peak = float(values["baseline_total_load_gw"].sum(axis=0).max())
        effective_peak = float(values["effective_total_load_gw"].sum(axis=0).max())
    return {
        "thermal_shift_throughput_gwh": thermal,
        "ev_charge_relocation_gwh": ev_relocation,
        "national_peak_load_change_gw": effective_peak - baseline_peak,
    }


def _wave_metrics(output_dir: Path, qc: dict[str, Any]) -> dict[str, Any]:
    capacity_path = output_dir / "wave_capacity.csv"
    if not capacity_path.is_file():
        return {
            "wave_energy_enabled": bool(qc.get("wave_energy_enabled", False)),
            "wave_candidate_rows": 0,
            "wave_capacity_upper_gw": 0.0,
            "wave_capacity_gw": 0.0,
            "wave_generation_gwh": float(qc.get("total_wave_generation_gwh", 0.0)),
        }
    frame = pd.read_csv(capacity_path)
    return {
        "wave_energy_enabled": bool(qc.get("wave_energy_enabled", False)),
        "wave_candidate_rows": int(len(frame)),
        "wave_capacity_upper_gw": float(frame.capacity_upper_gw.sum()),
        "wave_capacity_gw": float(frame.capacity_gw.sum()),
        "wave_generation_gwh": float(qc.get("total_wave_generation_gwh", 0.0)),
    }


def _sequence_metadata(root: Path) -> dict[str, Any]:
    report = _read_json(root / "sequence_report.json")
    return {
        "status": report.get("status"),
        "result_use": report.get("result_use"),
        "diagnostic_hours": int(report.get("diagnostic_hours", 0)),
        "scenario_id": report.get("scenario_id"),
        "years": tuple(int(year) for year in report.get("years", [])),
        "accepted": all(
            run.get("status") in {"ACCEPTED", "RESUMED_ACCEPTED"}
            for run in report.get("runs", [])
        ),
    }


def audit_pair(base_root: Path, scenario_root: Path) -> dict[str, Any]:
    base_sequence = _sequence_metadata(base_root)
    scenario_sequence = _sequence_metadata(scenario_root)
    failures: list[str] = []
    for label, metadata in (
        ("base", base_sequence),
        ("scenario", scenario_sequence),
    ):
        if metadata["status"] != "PASS":
            failures.append(f"{label}:sequence_status={metadata['status']}")
        if not metadata["accepted"]:
            failures.append(f"{label}:not_all_years_accepted")
        if metadata["years"] != YEARS:
            failures.append(f"{label}:years={metadata['years']}")
    for key in ("result_use", "diagnostic_hours", "years"):
        if base_sequence[key] != scenario_sequence[key]:
            failures.append(f"pair_mismatch:{key}")

    rows: list[dict[str, Any]] = []
    for year in YEARS:
        base_dir = base_root / str(year)
        scenario_dir = scenario_root / str(year)
        base_qc = _read_json(base_dir / "solution_qc.json")
        scenario_qc = _read_json(scenario_dir / "solution_qc.json")
        base_run = collect_solver_run(base_dir)
        scenario_run = collect_solver_run(scenario_dir)
        base_result_manifest, base_result_failures = validate_result_manifest(base_dir)
        scenario_result_manifest, scenario_result_failures = validate_result_manifest(
            scenario_dir
        )
        base_input_manifest, base_input_failures = validate_input_manifest(
            base_dir / "input_manifest.csv"
        )
        scenario_input_manifest, scenario_input_failures = validate_input_manifest(
            scenario_dir / "input_manifest.csv"
        )
        flex_cost = _flex_cost_breakdown(scenario_dir)
        objective_delta = (
            float(scenario_qc["objective_value_million_cny"])
            - float(base_qc["objective_value_million_cny"])
        )
        row: dict[str, Any] = {
            "planning_year": year,
            "result_use": scenario_qc.get("result_use", scenario_sequence["result_use"]),
            "base_qc_status": base_qc.get("status"),
            "scenario_qc_status": scenario_qc.get("status"),
            "base_hard_check_failures": sum(
                value is not True
                for value in base_qc.get("hard_checks", {}).values()
            ),
            "scenario_hard_check_failures": sum(
                value is not True
                for value in scenario_qc.get("hard_checks", {}).values()
            ),
            "base_result_manifest_valid": base_result_manifest,
            "scenario_result_manifest_valid": scenario_result_manifest,
            "base_input_manifest_valid": base_input_manifest,
            "scenario_input_manifest_valid": scenario_input_manifest,
            "base_objective_million_cny": float(
                base_qc["objective_value_million_cny"]
            ),
            "scenario_objective_million_cny": float(
                scenario_qc["objective_value_million_cny"]
            ),
            "scenario_minus_base_objective_million_cny": objective_delta,
            "explicit_flex_cost_million_cny": flex_cost["total"],
            "annualized_flex_enablement_cost_million_cny": flex_cost[
                "annualized"
            ],
            "selected_horizon_flex_operation_cost_million_cny": flex_cost[
                "selected_horizon"
            ],
            "gross_system_benefit_before_flex_cost_million_cny": (
                flex_cost["total"] - objective_delta
            ),
            "net_system_benefit_after_flex_cost_million_cny": -objective_delta,
            "base_variables": int(base_run["variables"]),
            "scenario_variables": int(scenario_run["variables"]),
            "variable_increase_fraction": (
                int(scenario_run["variables"]) / int(base_run["variables"]) - 1.0
            ),
            "base_constraints": int(base_run["constraints"]),
            "scenario_constraints": int(scenario_run["constraints"]),
            "constraint_increase_fraction": (
                int(scenario_run["constraints"]) / int(base_run["constraints"])
                - 1.0
            ),
            "base_nonzeros": int(base_run["nonzeros"]),
            "scenario_nonzeros": int(scenario_run["nonzeros"]),
            "nonzero_increase_fraction": (
                int(scenario_run["nonzeros"]) / int(base_run["nonzeros"]) - 1.0
            ),
            "base_solver_runtime_seconds": float(base_run["runtime_seconds"]),
            "scenario_solver_runtime_seconds": float(
                scenario_run["runtime_seconds"]
            ),
            "base_peak_rss_gib": float(base_run["peak_process_tree_rss_gib"]),
            "scenario_peak_rss_gib": float(
                scenario_run["peak_process_tree_rss_gib"]
            ),
            "base_barrier_iterations": int(base_run["barrier_iterations"]),
            "scenario_barrier_iterations": int(
                scenario_run["barrier_iterations"]
            ),
            "base_simplex_iterations": int(base_run["simplex_iterations"]),
            "scenario_simplex_iterations": int(
                scenario_run["simplex_iterations"]
            ),
            **_flex_metrics(scenario_dir),
            **_wave_metrics(scenario_dir, scenario_qc),
        }
        artifact_failures = (
            base_result_failures
            + scenario_result_failures
            + base_input_failures
            + scenario_input_failures
        )
        if artifact_failures:
            failures.extend(f"{year}:{item}" for item in artifact_failures)
        if row["base_qc_status"] != "PASS" or row["scenario_qc_status"] != "PASS":
            failures.append(f"{year}:solution_qc")
        if (
            row["base_hard_check_failures"]
            or row["scenario_hard_check_failures"]
        ):
            failures.append(f"{year}:hard_checks")
        rows.append(row)

    return {
        "schema_version": "planning_sequence_ab_audit_v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": "PASS" if not failures else "FAIL",
        "base_root": str(base_root.resolve()),
        "scenario_root": str(scenario_root.resolve()),
        "base_sequence": base_sequence,
        "scenario_sequence": scenario_sequence,
        "interpretation_limit": (
            "TEST_ONLY_TRUNCATED_HORIZON verifies implementation and mechanism "
            "only; annualized planning/enablement costs and selected-horizon "
            "operating benefits must not be interpreted as annual scientific value."
        ),
        "failures": failures,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-root", required=True)
    parser.add_argument("--scenario-root", required=True)
    parser.add_argument("--json-out", required=True)
    parser.add_argument("--csv-out", required=True)
    args = parser.parse_args()
    report = audit_pair(Path(args.base_root), Path(args.scenario_root))
    json_path = Path(args.json_out)
    csv_path = Path(args.csv_out)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    fields = list(report["rows"][0]) if report["rows"] else []
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report["rows"])
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
