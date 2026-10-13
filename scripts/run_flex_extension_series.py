"""Finite section-5b F7/F8 queue after F5, using a separate frozen source copy.

Linux only. --source points to a verified overlay containing repo/ and
extension_manifest.json; --data-source is the original campaign input root.
Output is the existing isolated F5 campaign; only extension_* and F7/F8 are
created. Wait at most 24 hours for admission, never interrupt other jobs.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def verify(source):
    manifest = json.loads((source / "extension_manifest.json").read_text())
    for item in manifest["files"]:
        file = (source / item["path"]).resolve()
        if not file.is_relative_to(source) or hashlib.sha256(file.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Frozen extension source mismatch: " + item["path"])
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--data-source", required=True, type=Path)
    p.add_argument("--server-root", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--admission-gib", type=float, default=60)
    a = p.parse_args()
    source, data, base, out = (x.resolve() for x in (a.source, a.data_source, a.server_root, a.output))
    if not out.is_relative_to(base / "probe_outputs") or "cloud_backup" in out.parts or a.admission_gib < 60:
        raise ValueError("Independent probe root and >=60 GiB admission required")
    if not (out / "F5_launch.json").exists() or any((out / n).exists() for n in ("F7", "F8")):
        raise ValueError("Requires the existing F5 campaign and unused F7/F8 names")
    with (out / "extension_started.json").open("x") as f:
        json.dump(dict(pid=os.getpid(), utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())), f)
    manifest = verify(source)
    env = os.environ.copy()
    env.update(CISPO_DATA_ROOT=str(data / "data"), CISPO_CF_ROOT=str(base / "data/hourly_cf"),
               CISPO_HYDRO_ROOT=str(base / "data/hydro_timeseries_20260719_sequential_sparse"),
               CISPO_RAW_GRFR_ROOT=str(base / "data/grfr_raw_2019"),
               CISPO_WAVE_ROOT=str(base / "data/wave_energy_20260727"),
               OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
    deadline = time.monotonic() + 24*3600
    records = []
    lock_path = base / "run_control/numerical_validation_solver.lock"
    for name, switches in (("F7", ["--aggregate", "0"]), ("F8", ["--aggregate", "1", "--agg-fill", "0"])):
        with lock_path.open("a") as lock:
            while True:
                acquired = False
                if (out / "F5_terminal.json").exists():
                    try:
                        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        acquired = True
                    except BlockingIOError:
                        pass
                others = []
                for proc in psutil.process_iter(["pid", "cmdline"]):
                    try:
                        cmd = proc.info["cmdline"] or []
                        if proc.pid != os.getpid() and any(Path(x).name in
                            ("run_cispo_2030_full_year.py", "run_probe.py", "run_flex_full_diagnostic.py", "gurobi_cl") for x in cmd):
                            others.append(proc.pid)
                    except psutil.Error:
                        pass
                gate = dict(name=name, f5_terminal=(out / "F5_terminal.json").exists(),
                            lock_acquired=acquired, available_bytes=psutil.virtual_memory().available,
                            required_bytes=a.admission_gib*2**30, reserve_gib=15,
                            other_solver_pids=others, utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
                save(out / "extension_gate.json", gate)
                if acquired and not others and gate["available_bytes"] >= gate["required_bytes"]:
                    break
                if acquired:
                    fcntl.flock(lock, fcntl.LOCK_UN)
                if time.monotonic() >= deadline:
                    save(out / "extension_terminal.json", dict(state="ADMISSION_TIMEOUT", records=records, gate=gate))
                    return
                time.sleep(30)
            verify(source)
            cmd = [sys.executable, str(source / "repo/scripts/run_flex_full_diagnostic.py"),
                   "--hours", "744", "--start", "5088", "--threads", "16", "--case", "case3_thermal_ev_v5",
                   "--presolve", "2", "--reserve-gib", "15", "--output", str(out / name)] + switches
            save(out / (name+"_launch.json"), dict(command=cmd, gate=gate, parallel=False,
                 source_commit=manifest["diagnostic_commit"], source_root=str(source),
                 verified_files=len(manifest["files"]), monitoring="RSS throughout; reserve callback only during optimize"))
            with (out / (name+"_console.log")).open("x") as log, (out / (name+"_memory.jsonl")).open("x") as memory:
                peak = 0
                t0 = time.monotonic()
                child = subprocess.Popen(cmd, cwd=source / "repo", env=env, stdout=log, stderr=subprocess.STDOUT)
                save(out / "extension_active.json", dict(name=name, pid=child.pid, controller_pid=os.getpid()))
                while child.poll() is None:
                    try:
                        proc = psutil.Process(child.pid)
                        rss = proc.memory_info().rss + sum(c.memory_info().rss for c in proc.children(recursive=True) if c.is_running())
                        peak = max(peak, rss)
                        memory.write(json.dumps(dict(elapsed=time.monotonic()-t0, rss=rss,
                                                    available=psutil.virtual_memory().available)) + "\n")
                        memory.flush()
                    except psutil.Error:
                        pass
                    time.sleep(2)
            record = dict(name=name, returncode=child.returncode, peak_rss_bytes=peak,
                          wall_seconds=time.monotonic()-t0, ended_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
            records.append(record)
            save(out / (name+"_terminal.json"), record)
            save(out / "extension_status.json", records)
            # A resource stop must not be followed by another admission attempt.
            result_path = out / name / "result.json"
            if result_path.exists() and json.loads(result_path.read_text()).get("resource_stop"):
                save(out / "extension_terminal.json", dict(state="RESOURCE_STOP", records=records))
                return
    save(out / "extension_terminal.json", dict(state="COMPLETE", records=records))


if __name__ == "__main__":
    main()
