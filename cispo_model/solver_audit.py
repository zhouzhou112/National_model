"""Parse comparable build, presolve, algorithm, memory, and QC evidence."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .io_contract import validate_result_manifest


_NUMBER = r"([0-9]+(?:\.[0-9]+)?(?:e[+-]?[0-9]+)?)"


def _match(
    text: str,
    pattern: str,
    *,
    converter: Any = float,
) -> Any | None:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return converter(match.group(1)) if match else None


def parse_gurobi_log(text: str) -> dict[str, Any]:
    """Extract stable performance fields from a Gurobi LP log."""
    original = re.search(
        r"Optimize a model with ([0-9,]+) rows, ([0-9,]+) columns "
        r"and ([0-9,]+) nonzeros",
        text,
    )
    presolved = re.search(
        r"Presolved: ([0-9,]+) rows, ([0-9,]+) columns, "
        r"([0-9,]+) nonzeros",
        text,
    )
    barrier_solved = re.search(
        r"Barrier solved model in ([0-9,]+) iterations and "
        r"([0-9.]+) seconds",
        text,
    )
    barrier_performed = re.search(
        r"Barrier performed ([0-9,]+) iterations in ([0-9.]+) seconds",
        text,
    )
    solved = re.search(
        r"Solved in ([0-9,]+) iterations and ([0-9.]+) seconds",
        text,
    )
    push_records = [
        {
            "remaining": int(match.group(1).replace(",", "")),
            "phase": "dual" if match.group(2).upper() == "D" else "primal",
            "runtime_seconds": float(match.group(3)),
        }
        for match in re.finditer(
            r"^\s*([0-9,]+)\s+([DP])Pushes remaining with [DP]Inf "
            r"[^\s]+\s+([0-9]+(?:\.[0-9]+)?)s\s*$",
            text,
            flags=re.IGNORECASE | re.MULTILINE,
        )
    ]
    result: dict[str, Any] = {
        "presolve_seconds": _match(
            text, rf"Presolve time:\s*{_NUMBER}s"
        ),
        "ordering_seconds": _match(
            text, rf"Ordering time:\s*{_NUMBER}s"
        ),
        "aa_transpose_nonzeros": _match(
            text, rf"AA' NZ\s*:\s*{_NUMBER}", converter=float
        ),
        "factor_nonzeros": _match(
            text, rf"Factor NZ\s*:\s*{_NUMBER}", converter=float
        ),
        "factor_operations": _match(
            text, rf"Factor Ops\s*:\s*{_NUMBER}", converter=float
        ),
        "factor_memory_gb_log_estimate": _match(
            text,
            rf"Factor NZ[^\n]*roughly\s*{_NUMBER}\s*GB of memory",
            converter=float,
        ),
        "dense_columns": _match(
            text, r"Dense cols\s*:\s*([0-9,]+)", converter=lambda value: int(value.replace(",", ""))
        ),
        "crossover_seconds": _match(
            text, rf"Crossover time:\s*{_NUMBER}\s+seconds"
        ),
    }
    if original:
        result.update(
            original_rows=int(original.group(1).replace(",", "")),
            original_columns=int(original.group(2).replace(",", "")),
            original_nonzeros=int(original.group(3).replace(",", "")),
        )
    if presolved:
        result.update(
            presolved_rows=int(presolved.group(1).replace(",", "")),
            presolved_columns=int(presolved.group(2).replace(",", "")),
            presolved_nonzeros=int(presolved.group(3).replace(",", "")),
        )
    if barrier_solved:
        result.update(
            barrier_iterations=int(barrier_solved.group(1).replace(",", "")),
            barrier_solve_seconds=float(barrier_solved.group(2)),
            barrier_termination="SOLVED",
        )
    elif barrier_performed:
        result.update(
            barrier_iterations=int(barrier_performed.group(1).replace(",", "")),
            barrier_solve_seconds=float(barrier_performed.group(2)),
            barrier_termination="PERFORMED",
        )
    if solved:
        result.update(
            simplex_iterations=int(solved.group(1).replace(",", "")),
            total_solver_log_seconds=float(solved.group(2)),
        )
    if push_records:
        phase_summary: dict[str, dict[str, Any]] = {}
        for phase in ("dual", "primal"):
            records = [row for row in push_records if row["phase"] == phase]
            if records:
                phase_summary[phase] = {
                    "samples": len(records),
                    "first_remaining": records[0]["remaining"],
                    "last_remaining": records[-1]["remaining"],
                    "first_runtime_seconds": records[0]["runtime_seconds"],
                    "last_runtime_seconds": records[-1]["runtime_seconds"],
                }
        ordered_phases = sorted(
            phase_summary,
            key=lambda phase: phase_summary[phase]["first_runtime_seconds"],
        )
        result["crossover_push_order"] = "_then_".join(ordered_phases)
        result["crossover_push_phases"] = phase_summary
        barrier_seconds = result.get("barrier_solve_seconds")
        if barrier_seconds is not None:
            phase_start = float(barrier_seconds)
            for phase in ordered_phases:
                phase_end = float(phase_summary[phase]["last_runtime_seconds"])
                result[f"crossover_{phase}_push_seconds"] = max(
                    0.0, phase_end - phase_start
                )
                phase_start = phase_end
            crossover_seconds = result.get("crossover_seconds")
            if crossover_seconds is not None:
                crossover_end = float(barrier_seconds) + float(crossover_seconds)
                result["crossover_cleanup_seconds"] = max(
                    0.0, crossover_end - phase_start
                )
    original_rows = result.get("original_rows")
    original_columns = result.get("original_columns")
    original_nonzeros = result.get("original_nonzeros")
    presolved_rows = result.get("presolved_rows")
    presolved_columns = result.get("presolved_columns")
    presolved_nonzeros = result.get("presolved_nonzeros")
    if original_rows and presolved_rows is not None:
        result["presolve_row_reduction_fraction"] = 1.0 - presolved_rows / original_rows
    if original_columns and presolved_columns is not None:
        result["presolve_column_reduction_fraction"] = 1.0 - presolved_columns / original_columns
    if original_nonzeros and presolved_nonzeros is not None:
        result["presolve_nonzero_reduction_fraction"] = 1.0 - presolved_nonzeros / original_nonzeros
    aa_transpose_nonzeros = result.get("aa_transpose_nonzeros")
    factor_nonzeros = result.get("factor_nonzeros")
    if aa_transpose_nonzeros and factor_nonzeros is not None:
        result["factor_to_aa_nonzero_ratio"] = factor_nonzeros / aa_transpose_nonzeros
    barrier_seconds = result.get("barrier_solve_seconds")
    total_seconds = result.get("total_solver_log_seconds")
    if barrier_seconds is not None and total_seconds is not None:
        result["post_barrier_solver_seconds"] = total_seconds - barrier_seconds
    return result


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def collect_solver_run(root: str | Path) -> dict[str, Any]:
    """Collect one output root without requiring a successful final solve."""
    root = Path(root).resolve()
    solve = _read_json(root / "solve_report.json")
    qc = _read_json(root / "solution_qc.json")
    build = _read_json(root / "build_report.json")
    structure = _read_json(root / "constraint_family_audit.json")
    scope = _read_json(root / "run_scope.json")
    config_snapshot = _read_json(root / "model_config_snapshot.json")
    environment = _read_json(root / "run_environment.json")
    log_path = root / "gurobi.log"
    log_fields = (
        parse_gurobi_log(log_path.read_text(encoding="utf-8", errors="replace"))
        if log_path.is_file()
        else {}
    )
    build_elapsed = None
    if build.get("build_started_at") and build.get("generated_at"):
        build_elapsed = (
            datetime.fromisoformat(build["generated_at"])
            - datetime.fromisoformat(build["build_started_at"])
        ).total_seconds()
    telemetry_path = root / "solver_telemetry.jsonl"
    telemetry_records: list[dict[str, Any]] = []
    if telemetry_path.is_file():
        telemetry_records = [
            json.loads(line)
            for line in telemetry_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    progress = [
        row for row in telemetry_records if row.get("event") == "solver_progress"
    ]
    last_progress = progress[-1] if progress else {}
    max_solver_memory = max(
        (
            float(row["max_memory_used_gb"])
            for row in progress
            if row.get("max_memory_used_gb") is not None
        ),
        default=None,
    )
    statistics = solve.get("model_statistics") or build.get("statistics") or {}
    solver_parameters = solve.get("solver_parameters") or {}
    warm_start = solve.get("warm_start") or build.get("warm_start") or {}
    manifest_valid, manifest_failures = validate_result_manifest(root)
    hard_checks = qc.get("hard_checks") or {}
    largest_constraint_family = next(
        iter(structure.get("constraint_families", [])), {}
    )
    largest_variable_family = next(
        iter(structure.get("variable_families", [])), {}
    )
    return {
        "output_root": str(root),
        "planning_year": solve.get("planning_year", scope.get("planning_year")),
        "optimization_hours": solve.get(
            "optimization_hours", scope.get("optimization_hours")
        ),
        "scenario_id": solve.get("scenario_id", scope.get("scenario_id")),
        "result_use": solve.get("result_use", scope.get("result_use")),
        "status": solve.get("status"),
        "solution_qc_status": qc.get("status"),
        "hard_check_count": len(hard_checks),
        "hard_check_failure_count": sum(
            not bool(value) for value in hard_checks.values()
        ),
        "result_manifest_valid": manifest_valid,
        "result_manifest_failure_count": len(manifest_failures),
        "solver_profile_id": solve.get("solver_profile_id"),
        "solver_method": solver_parameters.get("method"),
        "solver_crossover": solver_parameters.get("crossover"),
        "solver_crossover_basis": solver_parameters.get("crossover_basis"),
        "solver_lp_warm_start": solver_parameters.get("lp_warm_start"),
        "solver_dual_reductions": solver_parameters.get("dual_reductions"),
        "solver_inf_unbd_info": solver_parameters.get("inf_unbd_info"),
        "warm_start_cross_year": warm_start.get("cross_year"),
        "warm_start_source_planning_year": warm_start.get(
            "source_planning_year"
        ),
        "git_commit": environment.get("git_commit"),
        "configuration_source_sha256": config_snapshot.get("source_sha256"),
        "scenario_source_sha256": config_snapshot.get("scenario_source_sha256"),
        "solver_profile_source_sha256": config_snapshot.get("solver_source_sha256"),
        "objective_value_million_cny": solve.get(
            "objective_value_million_cny"
        ),
        "runtime_seconds": solve.get("runtime_seconds"),
        "build_elapsed_seconds": build_elapsed,
        "peak_process_tree_rss_gib": solve.get("runtime_memory", {}).get(
            "peak_process_tree_rss_gib",
            build.get("memory_at_exit", {}).get("peak_process_tree_rss_gib"),
        ),
        "telemetry_max_solver_memory_gb": max_solver_memory,
        "telemetry_last_phase": last_progress.get("phase"),
        "telemetry_last_iteration": last_progress.get("iteration"),
        "telemetry_last_runtime_seconds": last_progress.get("runtime_seconds"),
        "variables": statistics.get("variables"),
        "constraints": statistics.get("constraints"),
        "nonzeros": statistics.get("nonzeros"),
        "constraint_family_audit_schema": structure.get("schema_version"),
        "largest_raw_constraint_family": largest_constraint_family.get("family"),
        "largest_raw_constraint_family_nonzeros": largest_constraint_family.get(
            "matrix_nonzeros"
        ),
        "largest_raw_variable_family": largest_variable_family.get("family"),
        "largest_raw_variable_family_nonzeros": largest_variable_family.get(
            "matrix_nonzeros"
        ),
        **log_fields,
    }
