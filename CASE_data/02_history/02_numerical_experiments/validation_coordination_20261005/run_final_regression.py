"""Run the required suite with source identities and preserve raw output bytes."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def source_hashes():
    paths = []
    for folder in ("cispo_model", "scripts", "tests", "config"):
        paths.extend(p for p in (ROOT / folder).rglob("*")
                     if p.is_file() and p.suffix in {".py", ".json", ".csv", ".sh", ".sbatch"})
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)}


def main():
    before = source_hashes()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log = HERE / f"unittest_verified_{stamp}.log"
    telemetry = HERE / f"unittest_verified_{stamp}_memory.jsonl"
    start = time.perf_counter()
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]
    environment = {key: os.environ.get(key) for key in (
        "PYTHONPATH", "CISPO_WAVE_ROOT", "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS", "MKL_NUM_THREADS", "PYTHONIOENCODING")}
    (HERE / f"unittest_verified_{stamp}_started.json").write_text(
        json.dumps({"utc_started": stamp, "command": command, "cwd": str(ROOT),
                    "python_version": sys.version, "environment": environment,
                    "source_sha256": before}, indent=2) + "\n", encoding="utf-8")
    memory_guard_triggered = False
    peak_tree_rss = 0
    min_available = psutil.virtual_memory().available
    with log.open("xb") as output, telemetry.open("x", encoding="utf-8") as samples:
        child = subprocess.Popen(command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
        while child.poll() is None:
            memory = psutil.virtual_memory()
            processes = []
            try:
                parent = psutil.Process(child.pid)
                for process in [parent, *parent.children(recursive=True)]:
                    try:
                        processes.append({"pid": process.pid, "rss": process.memory_info().rss})
                    except psutil.NoSuchProcess:
                        pass
            except psutil.NoSuchProcess:
                pass
            tree_rss = sum(p["rss"] for p in processes)
            peak_tree_rss = max(peak_tree_rss, tree_rss)
            min_available = min(min_available, memory.available)
            samples.write(json.dumps({"utc": datetime.now(timezone.utc).isoformat(),
                                      "available_bytes": memory.available,
                                      "tree_rss_bytes": tree_rss, "processes": processes}) + "\n")
            samples.flush()
            if memory.available < 3 * 1024 ** 3:
                memory_guard_triggered = True
                for item in reversed(processes):
                    try:
                        psutil.Process(item["pid"]).terminate()
                    except psutil.NoSuchProcess:
                        pass
                break
            time.sleep(2)
        return_code = child.wait()
    after = source_hashes()
    record = {"utc_started": stamp, "command": command, "return_code": return_code,
              "python_version": sys.version, "environment": environment,
              "memory_guard_triggered": memory_guard_triggered,
              "memory_guard_available_floor_gib": 3,
              "sampled_peak_tree_rss_bytes": peak_tree_rss,
              "sampled_min_available_bytes": min_available,
              "memory_telemetry": telemetry.name,
              "elapsed_seconds": time.perf_counter() - start, "source_unchanged_during_test": before == after,
              "source_sha256": before, "source_sha256_after": after,
              "log": log.name, "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest()}
    (HERE / f"unittest_verified_{stamp}.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(log.read_text(encoding="utf-8", errors="replace")[-2500:])
    print(json.dumps({k: v for k, v in record.items() if not k.startswith("source_sha256")}))
    raise SystemExit(return_code or (0 if before == after and not memory_guard_triggered else 2))


if __name__ == "__main__":
    main()
