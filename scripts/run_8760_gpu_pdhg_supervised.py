"""One-shot full-year GPU0 trial; preserve the existing GPU1 trial.

Run with the GPU Python after sourcing server_env_20260825.sh. --prepare-only
creates task-private config/profile and provenance, but never builds a model.
The new process alone is shed at 94% host use, before the old job's 95% guard.
No solver time/memory limit, retry, reduced horizon or Stage B is introduced.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone

import psutil

EXPECTED_HEAD = "6065bfba34b76098e86307081323e8545a4d25ac"
TAG = "2030_base_8760h_gpu0_pdhg_unlimited_20260828_v2"
OLD_TAG = "2030_base_2160h_case4_gpu_pdhg_unlimited_20260828_v2"
GPU_UUID = "GPU-3b93923b-8b8f-efd4-2da7-e3763741e02b"
PROFILE_ID = "large_lp_8760_gpu0_pdhg_unlimited_v1"


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(args, cwd=None):
    return subprocess.check_output(args, cwd=cwd, text=True, timeout=30).strip()


def derive_config(base):
    result = copy.deepcopy(base)
    # Admission floor only, not an allocation cap or a mathematical parameter.
    result["construction"]["horizons"]["full_year"]["minimum_available_memory_gb"] = 1
    restored = copy.deepcopy(result)
    restored["construction"]["horizons"]["full_year"]["minimum_available_memory_gb"] = (
        base["construction"]["horizons"]["full_year"]["minimum_available_memory_gb"])
    assert restored == base
    assert result["construction"]["horizons"]["full_year"]["hours"] == 8760
    return result


def derive_profile(base):
    result = copy.deepcopy(base)
    result["profile_id"] = PROFILE_ID
    result["description"] = "Full 8760h GPU0 potential trial; numerics identical to unlimited 2160h Case4."
    assert result["numerics"] == base["numerics"]
    for key, value in {"method": 6, "threads": 32, "crossover": 0, "pdhg_gpu": 1,
                       "time_limit_seconds": None, "soft_mem_limit_gb": None}.items():
        assert result["numerics"][key] == value, (key, result["numerics"][key])
    return result


def prepare(root, bundle):
    repo = root / "repo"
    assert command(["git", "rev-parse", "HEAD"], repo) == EXPECTED_HEAD
    assert not command(["git", "status", "--porcelain"], repo), "Production checkout drift"
    source = repo / "config/optimization_2030.json"
    old_profile = root / "campaign_tools/case4_unlimited_20260828_v3/config/solver_profiles/large_lp_2160_case4_gpu_pdhg_unlimited_v2.json"
    base = json.loads(source.read_text())
    profile = json.loads(old_profile.read_text())
    derived = bundle / "derived"
    derived.mkdir()  # Refuse to overwrite a previous preparation.
    write_json(derived / "optimization_2030.json", derive_config(base))
    write_json(derived / "solver_profile.json", derive_profile(profile))
    metadata = {"prepared_at": now(), "repo_head": EXPECTED_HEAD,
                "source_config": str(source), "source_config_sha256": sha(source),
                "source_profile": str(old_profile), "source_profile_sha256": sha(old_profile),
                "only_base_config_change": {"path": "construction.horizons.full_year.minimum_available_memory_gb",
                    "before": base["construction"]["horizons"]["full_year"]["minimum_available_memory_gb"], "after": 1},
                "host_priority_shed_percent": 94, "existing_job_guard_percent": 95,
                "new_child_oom_score_adj": 500,
                "no_time_or_soft_memory_limit": True, "no_retry_or_stage_b": True,
                "files_sha256": {str(p.relative_to(bundle)): sha(p) for p in
                    [*derived.glob("*.json"), *bundle.glob("*.py")]}}
    write_json(bundle / "preparation.json", metadata)
    return metadata


def validate(root, bundle):
    repo = root / "repo"
    assert command(["git", "rev-parse", "HEAD"], repo) == EXPECTED_HEAD
    assert not command(["git", "status", "--porcelain"], repo), "Production checkout drift"
    metadata = json.loads((bundle / "preparation.json").read_text())
    for name, digest in metadata["files_sha256"].items():
        assert sha(bundle / name) == digest, f"Bundle integrity: {name}"
    assert sha(Path(metadata["source_config"])) == metadata["source_config_sha256"]
    assert sha(Path(metadata["source_profile"])) == metadata["source_profile_sha256"]
    old_control = root / "run_control" / OLD_TAG
    old_group = int((old_control / "run.pid").read_text())
    old_members, others = [], []
    for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time"]):
        try:
            args = proc.info["cmdline"] or []
            if any(Path(arg).name in {"run_cispo_2030_full_year.py", "recover_historical_stage_a.py",
                    "run_cispo_planning_sequence.py"} for arg in args):
                if OLD_TAG in " ".join(args) and os.getpgid(proc.pid) == old_group:
                    old_members.append({"pid": proc.pid, "pgid": old_group,
                                        "create_time": proc.create_time(), "name": proc.name()})
                else:
                    others.append(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied, ProcessLookupError):
            continue
    assert old_members and not others, ("Unexpected active CISPO jobs", old_members, others)
    gpu_rows = list(csv.reader(io.StringIO(command(["nvidia-smi", "--query-gpu=index,uuid,memory.free,utilization.gpu", "--format=csv,noheader,nounits"])), skipinitialspace=True))
    gpu = next(row for row in gpu_rows if row[1] == GPU_UUID)
    assert gpu[0] == "0" and float(gpu[2]) >= 20000 and float(gpu[3]) <= 10, gpu
    clients = []
    rows = csv.reader(io.StringIO(command(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,used_gpu_memory", "--format=csv,noheader,nounits"])), skipinitialspace=True)
    for row in rows:
        if row[0] == GPU_UUID:
            proc = psutil.Process(int(row[1]))
            assert proc.name() in {"ptyxis", "nautilus"}, ("Unexpected GPU0 client", proc.pid, proc.name())
            clients.append({"pid": proc.pid, "name": proc.name(), "create_time": proc.create_time(), "vram_mib": row[2]})
    vm = psutil.virtual_memory()
    assert vm.available > 10 * 2**30, "Insufficient memory even for admission"
    return {"validated_at": now(), "existing_job_members": old_members,
            "gpu0_desktop_clients_not_touched": clients, "gpus": gpu_rows,
            "host_memory_total_bytes": vm.total, "host_memory_available_bytes": vm.available,
            "swap_used_bytes": psutil.swap_memory().used}


def signal_owned(process, created, sig):
    if process.poll() is not None:
        return False
    target = psutil.Process(process.pid)
    assert target.create_time() == created and os.getpgid(process.pid) == process.pid
    os.killpg(process.pid, sig)
    return True


def supervise(root, bundle):
    validated = validate(root, bundle)
    control = root / "run_control" / TAG
    output = root / "outputs" / TAG
    assert not output.exists(), "Existing output: refuse restart"
    control.mkdir()  # Atomic claim: never retry a claimed tag automatically.
    write_json(control / "launch_validation.json", validated)
    write_json(control / "preparation.json", json.loads((bundle / "preparation.json").read_text()))
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = GPU_UUID
    env["PYTHONUNBUFFERED"] = "1"
    for variable, directory in [("CUDA_MPS_PIPE_DIRECTORY", "mps_pipe"), ("CUDA_MPS_LOG_DIRECTORY", "mps_log")]:
        path = control / directory
        path.mkdir(mode=0o700)
        env[variable] = str(path)
    args = [sys.executable, str(bundle / "run_8760_gpu_pdhg_instrumented.py"),
            "--repo-root", str(root / "repo"), "--control-root", str(control),
            "--config", str(bundle / "derived/optimization_2030.json"),
            "--solver-config", str(bundle / "derived/solver_profile.json"),
            "--scenario-config", "config/scenarios/base.json", "--planning-year", "2030",
            "--horizon", "full_year", "--output-dir", str(output)]
    write_json(control / "command.json", {"argv": args, "cwd": str(root / "repo"),
               "CUDA_VISIBLE_DEVICES": GPU_UUID, "telemetry_interval_seconds": 2,
               "priority_guard_interval_seconds": 0.25})
    process = monitor = None
    reason = None
    rc = 125
    with (control / "events.log").open("x", buffering=1) as events, \
         (control / "resource_monitor.tsv").open("x", buffering=1) as tsv, \
         (control / "stdout.log").open("x") as stdout, \
         (control / "stderr.log").open("x") as stderr, \
         (control / "telemetry.stderr.log").open("x") as monitor_stderr:
        def event(message):
            events.write(f"{now()} {message}\n")
        tsv.write("timestamp\tmem_total_bytes\tmem_available_bytes\thost_used_percent\tswap_used_bytes\n")
        try:
            process = subprocess.Popen(args, cwd=root / "repo", env=env,
                                       stdout=stdout, stderr=stderr, start_new_session=True)
            created = psutil.Process(process.pid).create_time()
            (control / "run.pid").write_text(str(process.pid) + "\n")
            write_json(control / "process_identity.json", {"pid": process.pid, "pgid": process.pid, "create_time": created, "argv": args})
            event(f"STARTED pid={process.pid} GPU0 full8760 no_solver_time_limit")
            monitor = subprocess.Popen([sys.executable, str(bundle / "monitor_case_resources.py"),
                "--process-group", str(process.pid), "--output-dir", str(control), "--gpu-device", "0",
                "--interval", "2", "--stop-file", str(control / "telemetry.stop")],
                stdout=subprocess.DEVNULL, stderr=monitor_stderr)
            (control / "telemetry.pid").write_text(str(monitor.pid) + "\n")
            last_sample = 0
            log_offset = 0
            log_tail = ""
            monitor_reported = False
            gpu_started = False
            with (control / "stdout.log").open() as live:
                while process.poll() is None:
                    vm = psutil.virtual_memory()
                    used = 100 * (vm.total - vm.available) / vm.total
                    if used >= 94:
                        reason = "NEW_JOB_PRIORITY_HOST_MEMORY_SHED_94_PERCENT"
                        event(f"{reason} used_percent={used:.6f}; SIGKILL new group only to protect existing95guard")
                        write_json(control / "guard_trigger.json", {"at": now(), "reason": reason, "used_percent": used})
                        signal_owned(process, created, signal.SIGKILL)
                        break
                    if time.monotonic() - last_sample >= 2:
                        last_sample = time.monotonic()
                        tsv.write(f"{now()}\t{vm.total}\t{vm.available}\t{used:.6f}\t{psutil.swap_memory().used}\n")
                        if monitor.poll() is not None and not monitor_reported:
                            event(f"TELEMETRY_EXITED rc={monitor.returncode}; memory guard remains active")
                            monitor_reported = True
                        live.seek(log_offset)
                        chunk = log_tail + live.read()
                        log_offset = live.tell()
                        log_tail = chunk[-200:]
                        if "Start PDHG on GPU" in chunk and not gpu_started:
                            gpu_started = True
                            event("GPU_EXECUTION_CONFIRMED Start PDHG on GPU")
                        if "Start PDHG on CPU" in chunk:
                            reason = "INVALID_GPU_TRIAL_CPU_FALLBACK"
                            event(reason)
                            signal_owned(process, created, signal.SIGTERM)
                            try:
                                process.wait(timeout=15)
                            except subprocess.TimeoutExpired:
                                signal_owned(process, created, signal.SIGKILL)
                            break
                    time.sleep(0.25)
            rc = process.wait(timeout=30)
            event(f"ENDED rc={rc} reason={reason} gpu_started={gpu_started}")
            write_json(control / "terminal.json", {"ended_at": now(), "return_code": rc,
                "reason": reason, "gpu_execution_confirmed": gpu_started,
                "scientific_acceptance": "NOT_INFERRED_FROM_PROCESS_EXIT"})
        except BaseException as exc:
            event(f"SUPERVISOR_ERROR {type(exc).__name__}: {exc}")
            if process is not None and process.poll() is None:
                signal_owned(process, created, signal.SIGKILL)
                process.wait(timeout=30)
            raise
        finally:
            (control / "telemetry.stop").touch()
            if monitor is not None:
                try:
                    monitor.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    event("TELEMETRY_PENDING_AFTER_STOP")
            (control / "return_code.txt").write_text(str(rc) + "\n")
    return rc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server-root", type=Path, required=True)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    bundle = Path(__file__).resolve().parent
    if args.prepare_only:
        print(json.dumps(prepare(args.server_root, bundle), indent=2))
    else:
        raise SystemExit(supervise(args.server_root, bundle))


if __name__ == "__main__":
    main()
