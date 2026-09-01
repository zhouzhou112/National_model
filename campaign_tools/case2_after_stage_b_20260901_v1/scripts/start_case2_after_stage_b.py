"""Idempotently start the approved 2160 h Case 2 after Stage B passes.

This is an external campaign gate.  It does not modify the production checkout
or either model output.  A persistent watch mode is provided so Case 2 can
start promptly even though human-facing status checks occur every four hours.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import time
from datetime import datetime


EXPECTED_HEAD = "6065bfba34b76098e86307081323e8545a4d25ac"
STAGE_B_TAG = "2030_base_2160h_case1_v3_stage_b_20260901_v1"
CASE2_TAG = "2030_base_2160h_case2_v3_barrier32_screen_20260901_v1"


def now() -> str:
    return datetime.now().astimezone().isoformat()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def memory_state() -> tuple[float, float]:
    values: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, raw = line.split(":", 1)
        if key in {"MemTotal", "MemAvailable"}:
            values[key] = int(raw.split()[0])
    total = values["MemTotal"] * 1024
    available = values["MemAvailable"] * 1024
    used_percent = 100.0 * (total - available) / total
    return available / 1024**3, used_percent


def memory_psi_avg10() -> float:
    for line in Path("/proc/pressure/memory").read_text().splitlines():
        if line.startswith("some "):
            for field in line.split():
                if field.startswith("avg10="):
                    return float(field.split("=", 1)[1])
    raise RuntimeError("memory PSI avg10 is unavailable")


def git_state(repo: Path) -> tuple[str, str]:
    head = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    status = subprocess.check_output(
        ["git", "-C", str(repo), "status", "--short"], text=True
    )
    return head, status


def solver_processes() -> list[str]:
    completed = subprocess.run(
        [
            "pgrep",
            "-af",
            "run_cispo_2030_full_year.py|run_cispo_planning_sequence.py|"
            "recover_historical_stage_a.py|run_historical_stage_a_recovery.sh",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode not in {0, 1}:
        raise RuntimeError(f"pgrep failed with rc={completed.returncode}")
    return [line for line in completed.stdout.splitlines() if line.strip()]


def inspect_once(server_root: Path, queue_root: Path) -> tuple[str, dict]:
    repo = server_root / "repo"
    stage_control = server_root / "run_control" / STAGE_B_TAG
    stage_output = server_root / "outputs" / STAGE_B_TAG
    case_control = server_root / "run_control" / CASE2_TAG
    case_output = server_root / "outputs" / CASE2_TAG
    payload: dict = {
        "checked_at": now(),
        "stage_b_tag": STAGE_B_TAG,
        "case2_tag": CASE2_TAG,
    }

    if case_control.exists() or case_output.exists() or (queue_root / "claim.json").exists():
        payload.update(
            status="ALREADY_CLAIMED",
            case_control_exists=case_control.exists(),
            case_output_exists=case_output.exists(),
        )
        return "ALREADY_CLAIMED", payload

    rc_path = stage_control / "return_code.txt"
    if not rc_path.exists():
        payload.update(status="WAITING_STAGE_B")
        return "WAITING_STAGE_B", payload
    stage_rc = int(rc_path.read_text().strip())
    payload["stage_b_return_code"] = stage_rc
    if stage_rc != 0:
        payload.update(status="BLOCKED_STAGE_B_FAILED")
        return "BLOCKED_STAGE_B_FAILED", payload

    qc_path = stage_output / "solution_qc.json"
    manifest_path = stage_output / "result_manifest.json"
    solve_report_path = stage_output / "solve_report.json"
    if not qc_path.is_file() or not manifest_path.is_file() or not solve_report_path.is_file():
        payload.update(
            status="BLOCKED_STAGE_B_INCOMPLETE",
            solution_qc_exists=qc_path.is_file(),
            result_manifest_exists=manifest_path.is_file(),
            solve_report_exists=solve_report_path.is_file(),
        )
        return "BLOCKED_STAGE_B_INCOMPLETE", payload
    qc = json.loads(qc_path.read_text())
    payload["stage_b_qc_status"] = qc.get("status")
    if qc.get("status") != "PASS":
        payload.update(status="BLOCKED_STAGE_B_QC")
        return "BLOCKED_STAGE_B_QC", payload

    head, dirty = git_state(repo)
    payload.update(repo_head=head, repo_dirty=bool(dirty))
    if head != EXPECTED_HEAD or dirty:
        payload.update(status="BLOCKED_REPO_DRIFT")
        return "BLOCKED_REPO_DRIFT", payload

    processes = solver_processes()
    payload["preexisting_solver_processes"] = processes
    if processes:
        payload.update(status="WAITING_OTHER_SOLVER")
        return "WAITING_OTHER_SOLVER", payload

    available_gib, used_percent = memory_state()
    psi_avg10 = memory_psi_avg10()
    payload.update(
        host_memory_available_gib=available_gib,
        host_memory_used_percent=used_percent,
        memory_psi_some_avg10=psi_avg10,
    )
    if used_percent >= 90.0 or available_gib < 96.0 or psi_avg10 > 0.5:
        payload.update(status="WAITING_RESOURCES")
        return "WAITING_RESOURCES", payload

    payload.update(status="READY")
    return "READY", payload


def claim_and_start(server_root: Path, queue_root: Path, payload: dict) -> dict:
    queue_root.mkdir(parents=True, exist_ok=True)
    claim_path = queue_root / "claim.json"
    try:
        descriptor = os.open(
            claim_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
    except FileExistsError:
        payload.update(status="ALREADY_CLAIMED", checked_at=now())
        return payload
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(
            {"claimed_at": now(), "case2_tag": CASE2_TAG},
            handle,
            ensure_ascii=False,
            indent=2,
        )
        handle.write("\n")

    stdout_handle = (queue_root / "launcher.stdout.log").open("ab")
    stderr_handle = (queue_root / "launcher.stderr.log").open("ab")
    environment = os.environ.copy()
    environment.update(
        {
            "CISPO_SERVER_ROOT": str(server_root),
            "CASE_ID": "case2_v3_barrier32_screen",
            "HOURS": "2160",
            "START_HOUR": "2880",
            "MINIMUM_AVAILABLE_GIB": "96",
            "TAG": CASE2_TAG,
        }
    )
    try:
        process = subprocess.Popen(
            ["bash", "scripts/run_fixed_server_2160_campaign_case.sh"],
            cwd=server_root / "repo",
            env=environment,
            stdout=stdout_handle,
            stderr=stderr_handle,
            start_new_session=True,
        )
    except Exception as error:
        payload.update(status="LAUNCH_FAILED", error=repr(error), checked_at=now())
        write_json(queue_root / "status.json", payload)
        raise
    finally:
        stdout_handle.close()
        stderr_handle.close()
    (queue_root / "launcher.pid").write_text(f"{process.pid}\n", encoding="utf-8")
    payload.update(
        status="STARTED",
        started_at=now(),
        launcher_pid=process.pid,
        command=["bash", "scripts/run_fixed_server_2160_campaign_case.sh"],
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--server-root", type=Path, default=Path("/home/zz2/National_model_server")
    )
    parser.add_argument("--watch-interval", type=float, default=0.0)
    args = parser.parse_args()
    if args.watch_interval < 0.0:
        raise SystemExit("--watch-interval cannot be negative")
    queue_root = (
        args.server_root
        / "campaign_tools"
        / "case2_after_stage_b_20260901_v1"
        / "run_control"
    )
    while True:
        status, payload = inspect_once(args.server_root, queue_root)
        write_json(queue_root / "status.json", payload)
        if status == "READY":
            payload = claim_and_start(args.server_root, queue_root, payload)
            write_json(queue_root / "status.json", payload)
            print(json.dumps(payload, ensure_ascii=False))
            return
        if status in {
            "ALREADY_CLAIMED",
            "BLOCKED_STAGE_B_FAILED",
            "BLOCKED_STAGE_B_INCOMPLETE",
            "BLOCKED_STAGE_B_QC",
            "BLOCKED_REPO_DRIFT",
        }:
            print(json.dumps(payload, ensure_ascii=False))
            raise SystemExit(0 if status == "ALREADY_CLAIMED" else 2)
        if args.watch_interval == 0.0:
            print(json.dumps(payload, ensure_ascii=False))
            return
        time.sleep(args.watch_interval)


if __name__ == "__main__":
    main()
