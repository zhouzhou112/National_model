#!/usr/bin/env python3
"""Fail-closed online qualification gate for the sole 2160h Stage A route."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import signal
import sys
import time
from typing import Any

import psutil

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cispo_model.solver_audit import parse_gurobi_log


EXPECTED_ORIGINAL = {
    "original_rows": 12_520_914,
    "original_columns": 10_398_783,
    "original_nonzeros": 126_724_678,
}
FACTOR_UPPER_BOUNDS = {
    "presolved_nonzeros": 107_398_350,
    "dense_columns": 38_982,
    "aa_transpose_nonzeros": 2.17035e8,
    "factor_nonzeros": 6.28845e9,
    "factor_operations": 2.19345e14,
    "factor_memory_gb_log_estimate": 63.0,
}
ITERATION_GATE = {
    "iteration": 30.0,
    "runtime_seconds": 12_000.0,
    "work_units": 18_961.075,
    "process_group_rss_gib": 75.0,
}


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _barrier_records(
    path: Path,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Return the latest record and immutable first ``iteration >= 30`` row."""
    if not path.is_file():
        return None, None
    latest = None
    gate = None
    try:
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if (
                    isinstance(row, dict)
                    and row.get("event") == "solver_progress"
                    and row.get("phase") == "barrier"
                ):
                    latest = row
                    iteration = _finite_number(row.get("iteration"))
                    if (
                        gate is None
                        and iteration is not None
                        and iteration >= ITERATION_GATE["iteration"]
                    ):
                        gate = row
    except OSError:
        return None, None
    return latest, gate


def _process_group_rss_bytes(pgid: int) -> tuple[int, int]:
    total = 0
    members = 0
    for process in psutil.process_iter(["pid", "memory_info", "status"]):
        try:
            if process.info["status"] == psutil.STATUS_ZOMBIE:
                continue
            if os.getpgid(process.pid) == pgid:
                members += 1
                total += int(process.info["memory_info"].rss)
        except (ProcessLookupError, PermissionError, psutil.Error):
            continue
    return total, members


def evaluate_qualification(
    log_metrics: dict[str, Any],
    barrier: dict[str, Any] | None,
    *,
    process_group_rss_bytes: int,
    host_memory_used_percent: float,
    iteration_gate_already_passed: bool = False,
    iteration_gate_barrier: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a deterministic gate decision without sending signals."""
    failures: list[str] = []
    pending: list[str] = []
    for key, expected in EXPECTED_ORIGINAL.items():
        actual = log_metrics.get(key)
        if actual is None:
            pending.append(key)
            continue
        number = _finite_number(actual)
        if number is None or not number.is_integer():
            failures.append(f"invalid_{key}={actual!r}")
        elif int(number) != expected:
            failures.append(f"{key}={actual} expected={expected}")
    numerical_trouble_count = _finite_number(
        log_metrics.get("numerical_trouble_count", 0)
    )
    if numerical_trouble_count is None or numerical_trouble_count < 0:
        failures.append("invalid_numerical_trouble_count")
    elif numerical_trouble_count > 0:
        failures.append("numerical_trouble_encountered")
    if bool(log_metrics.get("suboptimal_termination_warning")):
        failures.append("suboptimal_termination_warning")
    for key, upper in FACTOR_UPPER_BOUNDS.items():
        actual = log_metrics.get(key)
        if actual is None:
            pending.append(key)
            continue
        number = _finite_number(actual)
        if number is None or number < 0:
            failures.append(f"invalid_{key}={actual!r}")
        elif number > upper:
            failures.append(f"{key}={actual} upper={upper}")
    rss_bytes = _finite_number(process_group_rss_bytes)
    rss_gib = None if rss_bytes is None else rss_bytes / 1024**3
    if rss_gib is None or rss_gib < 0:
        failures.append("invalid_process_group_rss_bytes")
    elif rss_gib > ITERATION_GATE["process_group_rss_gib"]:
        failures.append(
            f"process_group_rss_gib={rss_gib:.6f} "
            f"upper={ITERATION_GATE['process_group_rss_gib']}"
        )
    host_used = _finite_number(host_memory_used_percent)
    if host_used is None or not 0.0 <= host_used <= 100.0:
        failures.append("invalid_host_memory_used_percent")
    elif host_used >= 95.0:
        failures.append(
            f"host_memory_used_percent={host_used:.6f} upper<95"
        )

    iteration = (
        _finite_number(barrier.get("iteration")) if barrier else None
    )
    runtime = (
        _finite_number(barrier.get("runtime_seconds")) if barrier else None
    )
    work = _finite_number(barrier.get("work_units")) if barrier else None
    if barrier is not None:
        for label, value in (
            ("iteration", iteration),
            ("runtime_seconds", runtime),
            ("work_units", work),
        ):
            if value is None or value < 0:
                failures.append(f"invalid_latest_barrier_{label}")
    current_iteration = iteration if iteration is not None else -1.0
    # Crossing either budget before iteration 30 already makes the gate
    # impossible to pass, so stop without waiting for an additional iteration.
    if (
        not iteration_gate_already_passed
        and current_iteration < ITERATION_GATE["iteration"]
        and runtime is not None
        and runtime > ITERATION_GATE["runtime_seconds"]
    ):
        failures.append(
            f"runtime_seconds={runtime} upper={ITERATION_GATE['runtime_seconds']}"
        )
    if (
        not iteration_gate_already_passed
        and current_iteration < ITERATION_GATE["iteration"]
        and work is not None
        and work > ITERATION_GATE["work_units"]
    ):
        failures.append(
            f"work_units={work} upper={ITERATION_GATE['work_units']}"
    )
    iteration_gate_passed = bool(iteration_gate_already_passed)
    gate_evidence = iteration_gate_barrier
    if gate_evidence is None and current_iteration >= ITERATION_GATE["iteration"]:
        gate_evidence = barrier
    if not iteration_gate_already_passed and gate_evidence is not None:
        gate_iteration = _finite_number(gate_evidence.get("iteration"))
        gate_runtime = _finite_number(gate_evidence.get("runtime_seconds"))
        gate_work = _finite_number(gate_evidence.get("work_units"))
        if gate_iteration is None or gate_iteration < ITERATION_GATE["iteration"]:
            failures.append("invalid_iteration_gate_evidence")
        for key, value, upper in (
            ("runtime_seconds", gate_runtime, ITERATION_GATE["runtime_seconds"]),
            ("work_units", gate_work, ITERATION_GATE["work_units"]),
        ):
            if value is None or value < 0:
                failures.append(f"invalid_{key}_at_iteration_30")
            elif value > upper:
                failures.append(f"{key}={value} upper={upper}")
        if pending:
            failures.append(
                "missing_factor_evidence_at_iteration_30:" + ",".join(pending)
            )
        iteration_gate_passed = not failures

    return {
        "status": (
            "FAIL"
            if failures
            else (
                "PASS_ITERATION_30_CONTINUE"
                if iteration_gate_passed
                else "PENDING"
            )
        ),
        "failures": failures,
        "pending_metrics": sorted(set(pending)),
        "iteration_gate_passed": iteration_gate_passed,
        "latest_barrier": barrier,
        "iteration_gate_evidence": gate_evidence,
        "process_group_rss_gib": rss_gib,
        "host_memory_used_percent": host_used,
        "log_metrics": log_metrics,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--process-group", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--control-dir", type=Path, required=True)
    parser.add_argument("--interval", type=float, default=10.0)
    args = parser.parse_args()
    if args.process_group <= 1 or args.interval <= 0:
        parser.error("process-group > 1 and interval > 0 are required")
    args.control_dir.mkdir(parents=True, exist_ok=True)
    decision_path = args.control_dir / "qualification_gate.json"
    samples_path = args.control_dir / "qualification_samples.jsonl"
    termination_sent = False
    ever_passed = False
    last_decision: dict[str, Any] = {}
    with samples_path.open("x", encoding="utf-8", buffering=1) as samples:
        while True:
            rss_bytes, members = _process_group_rss_bytes(args.process_group)
            if members == 0:
                final = dict(last_decision)
                final.update(
                    generated_at=_timestamp(),
                    solver_process_group_exited=True,
                    termination_signal_sent=termination_sent,
                    status=(
                        "FAIL_TERMINATED"
                        if termination_sent
                        else (
                            "PASS_ITERATION_30_SOLVER_EXITED"
                            if ever_passed
                            else "INCOMPLETE_SOLVER_EXITED_BEFORE_ITERATION_30"
                        )
                    ),
                )
                _atomic_json(decision_path, final)
                raise SystemExit(
                    42 if termination_sent else (0 if ever_passed else 3)
                )
            log_path = args.output_dir / "gurobi.log"
            log_metrics = parse_gurobi_log(
                log_path.read_text(encoding="utf-8", errors="replace")
                if log_path.is_file()
                else ""
            )
            barrier, gate_barrier = _barrier_records(
                args.output_dir / "solver_telemetry.jsonl"
            )
            memory = psutil.virtual_memory()
            decision = evaluate_qualification(
                log_metrics,
                barrier,
                process_group_rss_bytes=rss_bytes,
                host_memory_used_percent=(
                    100.0 * (memory.total - memory.available) / memory.total
                ),
                iteration_gate_already_passed=ever_passed,
                iteration_gate_barrier=gate_barrier,
            )
            decision.update(
                schema_version="cispo_stagea_2160_qualification_gate_v1",
                generated_at=_timestamp(),
                expected_original=EXPECTED_ORIGINAL,
                factor_upper_bounds=FACTOR_UPPER_BOUNDS,
                iteration_gate=ITERATION_GATE,
                process_group=args.process_group,
                process_group_members=members,
                host_memory_available_bytes=int(memory.available),
                termination_signal_sent=termination_sent,
            )
            last_decision = decision
            ever_passed = ever_passed or bool(decision["iteration_gate_passed"])
            samples.write(
                json.dumps(decision, ensure_ascii=False, separators=(",", ":"))
                + "\n"
            )
            _atomic_json(decision_path, decision)
            if decision["status"] == "FAIL" and not termination_sent:
                os.killpg(args.process_group, signal.SIGTERM)
                termination_sent = True
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
