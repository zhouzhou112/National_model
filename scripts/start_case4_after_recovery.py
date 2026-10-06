#!/usr/bin/env python3
"""One-shot, idempotent Case 4 gate for a Codex scheduled follow-up.

No polling daemon and no solver changes. --check-only never starts a job.
Use the already-installed GPU Python. All directories are explicit arguments.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import psutil

from monitor_case_resources import atomic_json, gpu_rows, nvidia_query, GPU_FIELDS, timestamp


MODEL_PROGRAMS = {"run_cispo_2030_full_year.py", "run_cispo_planning_sequence.py",
                  "recover_historical_stage_a.py", "run_historical_stage_a_recovery.sh"}
UNLIMITED_PROFILE = "large_lp_2160_case4_gpu_pdhg_unlimited_v2.json"


def recovery_gate(root):
    rc_file = root / "control" / "return_code.txt"
    if not rc_file.is_file():
        return "WAITING_RECOVERY"
    if rc_file.read_text().strip() != "0":
        return "BLOCKED_RECOVERY_FAILED"
    try:
        output = root / "recovered_8760"
        progress = json.loads((output / "recovery_progress.json").read_text())
        preservation = json.loads((output / "preservation_report.json").read_text())
        if (progress["status"] != "COMPLETE" or preservation["status"] != "COMPLETE"
                or progress["optimize_calls"] != 0 or progress["presolve_calls"] != 0
                or not (output / "result_manifest.json").is_file()):
            return "BLOCKED_RECOVERY_INCOMPLETE"
    except (OSError, ValueError, KeyError):
        return "BLOCKED_RECOVERY_INCOMPLETE"
    # Scientific QC PASS is deliberately NOT a launch condition. Complete
    # offline preservation and the recovery runner's successful validation are.
    return "READY"


def gpu_gate(gpus, client_text, device):
    selected = next((gpu for gpu in gpus if str(gpu["index"]) == device or gpu["uuid"] == device), None)
    if selected is None:
        return "BLOCKED_GPU_MISSING"
    if any(line.split(",", 1)[0].strip() == selected["uuid"] for line in client_text.splitlines()):
        return "WAITING_GPU_CLIENTS"
    free, util = selected["memory_free_mib"], selected["gpu_util_percent"]
    if free is None or util is None:
        return "BLOCKED_GPU_TELEMETRY"
    if free < 22000 or util > 5:
        return "WAITING_GPU_RESOURCES"
    return "READY"


def model_processes():
    result = []
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            names = {Path(arg).name for arg in proc.info["cmdline"] or []}
            if names & MODEL_PROGRAMS:
                result.append({"pid": proc.pid, "programs": sorted(names & MODEL_PROGRAMS)})
        except psutil.Error:
            continue
    return result


def verify_tools(root):
    manifest = json.loads((root / "deployment_manifest.json").read_text())
    for name in ("run_fixed_server_2160_campaign_case.sh", "monitor_case_resources.py",
                 "start_case4_after_recovery.py"):
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != manifest["sha256"][name]:
            raise ValueError(f"Deployment checksum mismatch: {name}")
    if UNLIMITED_PROFILE in manifest["sha256"]:
        if hashlib.sha256((root / UNLIMITED_PROFILE).read_bytes()).hexdigest() != manifest["sha256"][UNLIMITED_PROFILE]:
            raise ValueError("Unlimited profile checksum mismatch")
    return manifest


def readiness(args):
    recovery_status = recovery_gate(args.recovery_root)
    result = {"checked_at": timestamp(), "status": recovery_status,
              "recovery_status": recovery_status}
    if getattr(args, "independent_after_failed_recovery", False) and recovery_status == "BLOCKED_RECOVERY_FAILED":
        # Explicit new author authorization only; do not relabel or modify the
        # failed recovery, and retain all process/resource/version checks below.
        result.update(status="READY", independent_after_failed_recovery=True)
    if result["status"] != "READY":
        return result
    result["model_processes"] = model_processes()
    if result["model_processes"]:
        result["status"] = "WAITING_MODEL_PROCESS"
        return result
    repo = args.server_root / "repo"
    head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"], text=True).strip()
    result["repo_head"] = head
    if head != args.expected_repo_head or dirty:
        result["status"] = "BLOCKED_REPO_DRIFT"
        return result
    result["deployment"] = verify_tools(Path(__file__).resolve().parent)
    if getattr(args, "unlimited_pdhg", False):
        if UNLIMITED_PROFILE not in result["deployment"]["sha256"]:
            raise ValueError("Unlimited run requires a pinned unlimited profile")
        result["unlimited_pdhg"] = True
    result["memory_available_gib"] = psutil.virtual_memory().available / 2**30
    if result["memory_available_gib"] < 96:
        result["status"] = "WAITING_HOST_MEMORY"
        return result
    result["gpus"] = gpu_rows(nvidia_query("--query-gpu=" + GPU_FIELDS))
    result["status"] = gpu_gate(result["gpus"], nvidia_query(
        "--query-compute-apps=gpu_uuid,pid,used_gpu_memory"), args.gpu_device)
    return result


def claim_launch(path, value):
    # An interrupted/failed launch also keeps this claim: no blind re-launch.
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server-root", type=Path, required=True)
    parser.add_argument("--recovery-root", type=Path, required=True)
    parser.add_argument("--expected-repo-head", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--gpu-device", default="1")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--independent-after-failed-recovery", action="store_true",
                        help="Requires explicit author authorization to run Case 4 independently after failed recovery")
    parser.add_argument("--unlimited-pdhg", action="store_true",
                        help="Requires author authorization; remove only Case 4 solver time limit")
    args = parser.parse_args()
    if not args.tag or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for char in args.tag):
        parser.error("tag must contain only letters, digits, underscore or hyphen")
    if args.check_only:
        print(json.dumps(readiness(args), ensure_ascii=False, indent=2))
        return
    import fcntl  # Server Linux only; pure gate functions remain testable locally.
    state = args.server_root / "run_control" / (args.tag + "_queue")
    state.mkdir(parents=True, exist_ok=True)
    with (state / "launch.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        claim = state / "launch_claim.json"
        if claim.exists():
            print(json.dumps({"status": "ALREADY_CLAIMED", "claim": json.loads(claim.read_text())}))
            return
        result = readiness(args)
        atomic_json(state / "status.json", result)
        if result["status"] != "READY":
            print(json.dumps(result, ensure_ascii=False))
            return
        output = args.server_root / "outputs" / args.tag
        control = args.server_root / "run_control" / args.tag
        if output.exists() or control.exists():
            raise FileExistsError("Refuse pre-existing Case 4 output/control; do not retry under a new tag")
        env = os.environ.copy()
        env.update(CISPO_SERVER_ROOT=str(args.server_root),
                   CISPO_SERVER_ENV=str(args.server_root / "server_env_20260825.sh"),
                   CISPO_PYTHON=str(args.server_root / "envs/cispo-2030-gurobi-gpu13.0.2-cu129-v1/bin/python"),
                   CASE_ID="case4_gpu_pdhg_screen", HOURS="2160", START_HOUR="2880",
                   SCENARIO="config/scenarios/base.json", TAG=args.tag,
                   OUTPUT_ROOT=str(output), CONTROL_ROOT=str(control),
                   MINIMUM_AVAILABLE_GIB="96", GPU_DEVICE=args.gpu_device,
                   GPU_RUNTIME_ROOT=str(state / "gpu_runtime"), PYTHONUNBUFFERED="1")
        env.pop("CASE4_SOLVER_PROFILE", None)
        if args.unlimited_pdhg:
            env["CASE4_SOLVER_PROFILE"] = str(Path(__file__).resolve().parent / UNLIMITED_PROFILE)
        command = ["bash", str(Path(__file__).resolve().parent / "run_fixed_server_2160_campaign_case.sh")]
        claim_launch(claim, {"claimed_at": timestamp(), "command": command, "gate": result})
        with (state / "launcher.stdout.log").open("x") as stdout, (state / "launcher.stderr.log").open("x") as stderr:
            child = subprocess.Popen(command, cwd=args.server_root / "repo", env=env,
                                     stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                     start_new_session=True, close_fds=True)
        result.update(status="LAUNCH_DISPATCHED", launcher_pid=child.pid,
                      output_root=str(output), control_root=str(control))
        atomic_json(state / "status.json", result)
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
