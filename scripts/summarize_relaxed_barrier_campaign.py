"""Summarize fixed-server relaxed Barrier campaign evidence.

This reader never upgrades an engineering checkpoint to a scientific result.
It joins solver, GNU time, telemetry, resource and exact-A/B evidence into one
machine-readable JSON document and a flat CSV table.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _read_int(path: Path) -> int | None:
    if not path.is_file():
        return None
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except ValueError:
        return None


def _json_safe(value: Any) -> Any:
    """Replace non-finite floats so failure evidence remains valid JSON."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _duration_seconds(value: str) -> float:
    fields = [float(item) for item in value.strip().split(":")]
    if len(fields) == 2:
        minutes, seconds = fields
        return minutes * 60.0 + seconds
    if len(fields) == 3:
        hours, minutes, seconds = fields
        return hours * 3600.0 + minutes * 60.0 + seconds
    raise ValueError(f"Unsupported GNU time duration: {value!r}")


def _gnu_time(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    result: dict[str, Any] = {"path": str(path.resolve())}
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if line.startswith("Elapsed (wall clock) time"):
            value = line.rsplit(": ", 1)[-1]
            result["elapsed_text"] = value
            result["elapsed_seconds"] = _duration_seconds(value)
        elif line.startswith("Maximum resident set size (kbytes):"):
            result["maximum_rss_kib"] = int(line.rsplit(":", 1)[-1].strip())
        elif line.startswith("User time (seconds):"):
            result["user_seconds"] = float(line.rsplit(":", 1)[-1].strip())
        elif line.startswith("System time (seconds):"):
            result["system_seconds"] = float(line.rsplit(":", 1)[-1].strip())
        elif line.startswith("Percent of CPU this job got:"):
            result["cpu_percent"] = float(
                line.rsplit(":", 1)[-1].strip().rstrip("%")
            )
        elif line.startswith("Swaps:"):
            result["swaps"] = int(line.rsplit(":", 1)[-1].strip())
        elif line.startswith("Exit status:"):
            result["exit_status"] = int(line.rsplit(":", 1)[-1].strip())
    return result


def _telemetry(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    events = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    barrier = [
        item
        for item in events
        if item.get("event") == "solver_progress"
        and item.get("phase") == "barrier"
    ]
    start = next(
        (item for item in events if item.get("event") == "solver_start"), None
    )
    end = next(
        (item for item in reversed(events) if item.get("event") == "solver_end"),
        None,
    )
    result: dict[str, Any] = {
        "path": str(path.resolve()),
        "event_count": len(events),
        "solver_start": start,
        "solver_end": end,
        "barrier_event_count": len(barrier),
    }
    if barrier:
        first = barrier[0]
        last = barrier[-1]
        first_iteration = float(first["iteration"])
        last_iteration = float(last["iteration"])
        iteration_span = last_iteration - first_iteration
        runtime_span = float(last["runtime_seconds"]) - float(
            first["runtime_seconds"]
        )
        result.update(
            first_barrier_event=first,
            last_barrier_event=last,
            observed_barrier_seconds_per_iteration=(
                runtime_span / iteration_span if iteration_span > 0 else None
            ),
        )
    return result


def _resource_monitor(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if not rows:
        return {"path": str(path.resolve()), "sample_count": 0}

    def maximum(name: str) -> float | None:
        values = [float(row[name]) for row in rows if row.get(name) not in (None, "")]
        return max(values) if values else None

    def minimum(name: str) -> float | None:
        values = [float(row[name]) for row in rows if row.get(name) not in (None, "")]
        return min(values) if values else None

    return {
        "path": str(path.resolve()),
        "sample_count": len(rows),
        "first_timestamp": rows[0].get("timestamp"),
        "last_timestamp": rows[-1].get("timestamp"),
        "maximum_python_rss_kib": maximum("python_rss_kib"),
        "minimum_mem_available_kib": minimum("mem_available_kib"),
        "maximum_swap_used_kib": maximum("swap_used_kib"),
        "maximum_psi_some_avg10": maximum("psi_some_avg10"),
        "maximum_psi_full_avg10": maximum("psi_full_avg10"),
    }


def _find_control_case(
    tag: str,
    control_root: Path,
    fallback_control_roots: Iterable[Path],
) -> tuple[Path | None, Path | None]:
    primary = control_root / tag
    fallbacks = [root / tag for root in fallback_control_roots]
    time_source = next(
        (root for root in [primary, *fallbacks] if (root / "time.txt").is_file()),
        None,
    )
    evidence_source = next(
        (
            root
            for root in [primary, *fallbacks]
            if root.is_dir() or root.is_symlink()
        ),
        None,
    )
    return evidence_source, time_source


def _case_summary(
    tag: str,
    output_root: Path,
    control_root: Path,
    fallback_control_roots: list[Path],
) -> dict[str, Any]:
    output = output_root / tag
    resolved_output = output.resolve()
    control, time_control = _find_control_case(
        tag, control_root, fallback_control_roots
    )
    solve = _read_json(resolved_output / "solve_report.json")
    identity = _read_json(resolved_output / "run_identity.json")
    contract = _read_json(
        resolved_output
        / "engineering_macro_analysis"
        / "engineering_analysis_contract.json"
    )
    macro = _read_json(control_root / tag / "macro_comparison.json")
    checkpoint_path = (
        resolved_output
        / "barrier_checkpoint"
        / "barrier_checkpoint_manifest.json"
    )
    checkpoint = _read_json(checkpoint_path)
    time_report = _gnu_time(time_control / "time.txt") if time_control else None
    telemetry = _telemetry(resolved_output / "solver_telemetry.jsonl")
    resource = None
    if control is not None:
        resource = _resource_monitor(control / "resource_monitor.tsv")
    rc = None
    rc_source = None
    for candidate in (
        [control / "return_code.txt", control / "wrapper_exit_code.txt"]
        if control is not None
        else []
    ):
        rc = _read_int(candidate)
        if rc is not None:
            rc_source = str(candidate.resolve())
            break
    if rc is None and time_report is not None:
        rc = time_report.get("exit_status")
        rc_source = time_report.get("path")

    solver_parameters = solve.get("solver_parameters", {}) if solve else {}
    quality = solve.get("solution_quality", {}) if solve else {}
    iterations = solve.get("iteration_counts", {}) if solve else {}
    runtime_memory = solve.get("runtime_memory", {}) if solve else {}
    metrics = macro.get("metrics", {}) if macro else {}
    exact_identity = macro.get("exact_ab_identity", {}) if macro else {}
    return {
        "tag": tag,
        "output_path": str(output.absolute()),
        "resolved_output_path": str(resolved_output),
        "output_is_symlink": output.is_symlink(),
        "control_path": str(control.resolve()) if control else None,
        "time_control_path": str(time_control.resolve()) if time_control else None,
        "return_code": rc,
        "return_code_source": rc_source,
        "planning_year": solve.get("planning_year") if solve else None,
        "scenario_id": solve.get("scenario_id") if solve else None,
        "optimization_hours": solve.get("optimization_hours") if solve else None,
        "optimization_start_hour": (
            solve.get("optimization_start_hour") if solve else None
        ),
        "result_use": solve.get("result_use") if solve else None,
        "scientifically_accepted": False,
        "solver_status": solve.get("status") if solve else None,
        "run_completion_status": (
            solve.get("run_completion_status") if solve else None
        ),
        "solver_profile_id": solve.get("solver_profile_id") if solve else None,
        "solver_parameters": solver_parameters,
        "solver_runtime_seconds": solve.get("runtime_seconds") if solve else None,
        "barrier_iterations": iterations.get("barrier"),
        "solution_quality": quality,
        "strict_solver_acceptance_status": (
            contract.get("strict_solver_acceptance_status") if contract else None
        ),
        "raw_physical_qc_status": (
            contract.get("raw_physical_qc_status") if contract else None
        ),
        "barrier_checkpoint_manifest_present": checkpoint is not None,
        "barrier_checkpoint_manifest": checkpoint,
        "root_scientific_artifacts": {
            "solution_qc": (resolved_output / "solution_qc.json").is_file(),
            "result_manifest": (resolved_output / "result_manifest.json").is_file(),
            "planning_state": (resolved_output / "planning_state.json").is_file(),
            "basis_manifest": (resolved_output / "basis_manifest.json").is_file(),
        },
        "runtime_memory": runtime_memory,
        "gnu_time": time_report,
        "telemetry": telemetry,
        "resource_monitor": resource,
        "macro_status": macro.get("status") if macro else None,
        "exact_ab_identity_status": exact_identity.get("status"),
        "exact_ab_identity_matches": exact_identity.get("matches"),
        "macro_metrics": metrics,
        "candidate_failed_hard_checks": (
            macro.get("candidate_failed_hard_checks", []) if macro else []
        ),
        "lp_identity": identity.get("lp_model") if identity else None,
    }


CSV_FIELDS = [
    "tag",
    "planning_year",
    "scenario_id",
    "optimization_hours",
    "optimization_start_hour",
    "solver_profile_id",
    "numeric_focus",
    "barrier_convergence_tolerance",
    "feasibility_tolerance",
    "optimality_tolerance",
    "crossover",
    "return_code",
    "solver_status",
    "run_completion_status",
    "solver_runtime_seconds",
    "wall_elapsed_seconds",
    "barrier_iterations",
    "observed_barrier_seconds_per_iteration",
    "gnu_maximum_rss_kib",
    "process_tree_peak_rss_gib",
    "maximum_constraint_violation",
    "maximum_bound_violation",
    "maximum_dual_violation",
    "maximum_complementarity_violation",
    "strict_solver_acceptance_status",
    "raw_physical_qc_status",
    "barrier_checkpoint_manifest_present",
    "root_solution_qc_present",
    "root_result_manifest_present",
    "root_planning_state_present",
    "root_basis_manifest_present",
    "macro_status",
    "exact_ab_identity_status",
    "objective_relative_difference",
    "capacity_normalized_l1",
    "generation_normalized_l1",
    "period_generation_relative_difference",
    "candidate_failed_hard_checks",
    "scientifically_accepted",
]


def _flat_case(case: dict[str, Any]) -> dict[str, Any]:
    parameters = case["solver_parameters"]
    quality = case["solution_quality"]
    time_report = case.get("gnu_time") or {}
    telemetry = case.get("telemetry") or {}
    runtime_memory = case.get("runtime_memory") or {}
    metrics = case.get("macro_metrics") or {}
    root_artifacts = case["root_scientific_artifacts"]
    return {
        "tag": case["tag"],
        "planning_year": case["planning_year"],
        "scenario_id": case["scenario_id"],
        "optimization_hours": case["optimization_hours"],
        "optimization_start_hour": case["optimization_start_hour"],
        "solver_profile_id": case["solver_profile_id"],
        "numeric_focus": parameters.get("numeric_focus"),
        "barrier_convergence_tolerance": parameters.get(
            "barrier_convergence_tolerance"
        ),
        "feasibility_tolerance": parameters.get("feasibility_tolerance"),
        "optimality_tolerance": parameters.get("optimality_tolerance"),
        "crossover": parameters.get("crossover"),
        "return_code": case["return_code"],
        "solver_status": case["solver_status"],
        "run_completion_status": case["run_completion_status"],
        "solver_runtime_seconds": case["solver_runtime_seconds"],
        "wall_elapsed_seconds": time_report.get("elapsed_seconds"),
        "barrier_iterations": case["barrier_iterations"],
        "observed_barrier_seconds_per_iteration": telemetry.get(
            "observed_barrier_seconds_per_iteration"
        ),
        "gnu_maximum_rss_kib": time_report.get("maximum_rss_kib"),
        "process_tree_peak_rss_gib": runtime_memory.get("peak_process_tree_rss_gib"),
        "maximum_constraint_violation": quality.get(
            "maximum_constraint_violation"
        ),
        "maximum_bound_violation": quality.get("maximum_bound_violation"),
        "maximum_dual_violation": quality.get("maximum_dual_violation"),
        "maximum_complementarity_violation": quality.get(
            "maximum_complementarity_violation"
        ),
        "strict_solver_acceptance_status": case[
            "strict_solver_acceptance_status"
        ],
        "raw_physical_qc_status": case["raw_physical_qc_status"],
        "barrier_checkpoint_manifest_present": case[
            "barrier_checkpoint_manifest_present"
        ],
        "root_solution_qc_present": root_artifacts["solution_qc"],
        "root_result_manifest_present": root_artifacts["result_manifest"],
        "root_planning_state_present": root_artifacts["planning_state"],
        "root_basis_manifest_present": root_artifacts["basis_manifest"],
        "macro_status": case["macro_status"],
        "exact_ab_identity_status": case["exact_ab_identity_status"],
        "objective_relative_difference": metrics.get(
            "objective_relative_difference"
        ),
        "capacity_normalized_l1": metrics.get("capacity_normalized_l1"),
        "generation_normalized_l1": metrics.get("generation_normalized_l1"),
        "period_generation_relative_difference": metrics.get(
            "period_generation_relative_difference"
        ),
        "candidate_failed_hard_checks": ";".join(
            case["candidate_failed_hard_checks"]
        ),
        "scientifically_accepted": False,
    }


def summarize(
    output_base: Path,
    control_root: Path,
    fallback_control_roots: list[Path],
) -> dict[str, Any]:
    tags = sorted(
        item.name
        for item in output_base.iterdir()
        if item.is_dir() or item.is_symlink()
    )
    cases = [
        _case_summary(
            tag,
            output_base,
            control_root,
            fallback_control_roots,
        )
        for tag in tags
        if (output_base / tag / "solve_report.json").is_file()
    ]
    winner = _read_json(control_root / "winner.json")
    macro_pass = [case["tag"] for case in cases if case["macro_status"] == "MACRO_PASS"]
    return {
        "schema_version": "cispo_relaxed_barrier_campaign_summary_v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "scientifically_accepted": False,
        "output_base": str(output_base.resolve()),
        "control_root": str(control_root.resolve()),
        "fallback_control_roots": [
            str(path.resolve()) for path in fallback_control_roots
        ],
        "case_count": len(cases),
        "macro_pass_tags": macro_pass,
        "winner": winner,
        "cases": cases,
        "interpretation": (
            "Engineering timing, resource, quality and exact-A/B evidence only; "
            "no row is a scientifically accepted planning result."
        ),
    }


def write_csv(path: Path, cases: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(_flat_case(case) for case in cases)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-base", required=True)
    parser.add_argument("--control-root", required=True)
    parser.add_argument("--fallback-control-root", action="append", default=[])
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-csv", required=True)
    args = parser.parse_args()
    report = summarize(
        Path(args.output_base),
        Path(args.control_root),
        [Path(item) for item in args.fallback_control_root],
    )
    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(
            _json_safe(report),
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    write_csv(Path(args.output_csv), report["cases"])
    print(json.dumps({"case_count": report["case_count"], "macro_pass_tags": report["macro_pass_tags"]}))


if __name__ == "__main__":
    main()
