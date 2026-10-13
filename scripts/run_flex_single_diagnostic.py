"""Finite F5 controller using an existing immutable diagnostic source bundle.

Run under numerical_validation_solver.lock. Author-authorized direct launch;
retains the original solver callback reserve, records RSS through all phases,
and never overwrites a run. No production or frozen source edits.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-root", required=True, type=Path)
    p.add_argument("--server-root", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    source, base, out = a.source_root.resolve(), a.server_root.resolve(), a.output.resolve()
    if not out.is_relative_to(base / "probe_outputs") or "cloud_backup" in out.parts:
        raise ValueError("Output must be an isolated probe_outputs directory")
    if out == source or (out / "F5").exists():
        raise ValueError("Existing experiment must not be overwritten")
    out.mkdir(parents=True, exist_ok=True)
    with (out / "controller_started.json").open("x", encoding="utf-8") as f:
        json.dump(dict(pid=os.getpid(), utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())), f)
    manifest = json.loads((source / "bundle_manifest.json").read_text())
    for item in manifest["files"]:
        file = (source / item["path"]).resolve()
        if not file.is_relative_to(source):
            raise ValueError("Manifest path outside source")
        if hashlib.sha256(file.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Source bundle SHA mismatch: " + item["path"])
    windows = json.loads((source / "windows.json").read_text())
    start = windows["cooling"]["start"]
    env = os.environ.copy()
    env.update(CISPO_DATA_ROOT=str(source / "data"), CISPO_CF_ROOT=str(base / "data/hourly_cf"),
               CISPO_HYDRO_ROOT=str(base / "data/hydro_timeseries_20260719_sequential_sparse"),
               CISPO_RAW_GRFR_ROOT=str(base / "data/grfr_raw_2019"),
               CISPO_WAVE_ROOT=str(base / "data/wave_energy_20260727"),
               OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1",
               PYTHONDONTWRITEBYTECODE="1")
    cmd = [sys.executable, str(source / "repo/scripts/run_flex_full_diagnostic.py"),
           "--hours", "2016", "--start", str(start), "--threads", "16",
           "--case", "case3_thermal_ev_v5", "--aggregate", "1", "--presolve", "2",
           "--reserve-gib", "15", "--output", str(out / "F5")]
    available = psutil.virtual_memory().available
    if available < 15 * 2**30:
        raise RuntimeError("Available memory already below the retained 15 GiB reserve")
    save(out / "F5_launch.json", dict(command=cmd, available_bytes=available,
         source_root=str(source), source_commit=manifest["git_commit"], verified_files=len(manifest["files"]),
         authorization="Author directly requested F5 start after memory review on 2026-10-13",
         admission_override="105 GiB queue gate bypassed for this single author-authorized run",
         reserve_gib=15, parallel=False, monitoring="RSS sampling throughout; stop callback only inside optimize"))
    peak = 0
    t0 = time.monotonic()
    with (out / "F5_console.log").open("x") as log, (out / "F5_memory.jsonl").open("x") as memory:
        child = subprocess.Popen(cmd, cwd=source / "repo", env=env, stdout=log, stderr=subprocess.STDOUT)
        save(out / "active.json", dict(name="F5", pid=child.pid, controller_pid=os.getpid()))
        while child.poll() is None:
            try:
                process = psutil.Process(child.pid)
                rss = process.memory_info().rss + sum(c.memory_info().rss for c in process.children(recursive=True) if c.is_running())
                peak = max(peak, rss)
                memory.write(json.dumps(dict(elapsed=time.monotonic()-t0, rss=rss,
                                            available=psutil.virtual_memory().available)) + "\n")
                memory.flush()
            except psutil.Error:
                pass
            time.sleep(2)
    terminal = dict(name="F5", returncode=child.returncode, peak_rss_bytes=peak,
                    wall_seconds=time.monotonic()-t0)
    save(out / "F5_terminal.json", terminal)
    save(out / "queue_status.json", [terminal])
    save(out / "queue_terminal.json", dict(state="COMPLETE", records=[terminal]))


if __name__ == "__main__":
    main()
