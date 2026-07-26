"""Parse comparable build, presolve, algorithm, memory, and QC evidence."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


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
    solved = re.search(
        r"Solved in ([0-9,]+) iterations and ([0-9.]+) seconds",
        text,
    )
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
        )
    if solved:
        result.update(
            simplex_iterations=int(solved.group(1).replace(",", "")),
            total_solver_log_seconds=float(solved.group(2)),
        )
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
    scope = _read_json(root / "run_scope.json")
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
    return {
        "output_root": str(root),
        "planning_year": solve.get("planning_year", scope.get("planning_year")),
        "optimization_hours": solve.get(
            "optimization_hours", scope.get("optimization_hours")
        ),
        "scenario_id": solve.get("scenario_id", scope.get("scenario_id")),
        "status": solve.get("status"),
        "solution_qc_status": qc.get("status"),
        "solver_profile_id": solve.get("solver_profile_id"),
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
        **log_fields,
    }
