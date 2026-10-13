"""One author-authorized F5 rerun with a 2 GiB optimize callback reserve.

Linux only. Wait for the existing F8 campaign to finish, the shared solver
lock, no recognized solver and >=67 GiB available (old sampled F5 peak
64.951 GiB + 2 GiB rounded up; this is not a peak-memory guarantee).
Use a new immutable source overlay and new output root. Never resume or
overwrite the interrupted F5. Admission expires at --admission-deadline-utc;
an admitted solve is not killed at that time. All results are preserved.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil
from run_flex_extension_series import save, verify


def utc():
    return datetime.now(timezone.utc).isoformat()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "data-source", "server-root", "output", "predecessor"):
        p.add_argument("--" + name, required=True, type=Path)
    p.add_argument("--admission-deadline-utc", required=True)
    a = p.parse_args()
    deadline = datetime.fromisoformat(a.admission_deadline_utc.replace("Z", "+00:00"))
    if deadline.tzinfo is None:
        p.error("Admission deadline must include UTC offset")
    source, data, base, out, prior = (x.resolve() for x in
        (a.source, a.data_source, a.server_root, a.output, a.predecessor))
    for root in (source, data, out, prior):
        if not root.is_relative_to(base / "probe_outputs") or "cloud_backup" in root.parts:
            raise ValueError("Only independent diagnostic probe roots are allowed")
    if out in (source, data, prior) or (out / "F5_retry2g").exists():
        raise ValueError("A new output directory is required")
    manifest = verify(source)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "retry_started.json").open("x") as f:
        json.dump(dict(pid=os.getpid(), utc=utc()), f)
    env = os.environ.copy()
    env.update(CISPO_DATA_ROOT=str(data / "data"), CISPO_CF_ROOT=str(base / "data/hourly_cf"),
               CISPO_HYDRO_ROOT=str(base / "data/hydro_timeseries_20260719_sequential_sparse"),
               CISPO_RAW_GRFR_ROOT=str(base / "data/grfr_raw_2019"),
               CISPO_WAVE_ROOT=str(base / "data/wave_energy_20260727"),
               OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
    with (base / "run_control/numerical_validation_solver.lock").open("a") as lock:
        while True:
            acquired = False
            finished = (prior / "F8_terminal.json").exists() and (prior / "extension_terminal.json").exists()
            if finished:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                except BlockingIOError:
                    pass
            others = []
            for proc in psutil.process_iter(["pid", "cmdline"]):
                try:
                    if proc.pid != os.getpid() and any(Path(x).name in
                        ("run_cispo_2030_full_year.py", "run_probe.py", "run_flex_full_diagnostic.py", "gurobi_cl")
                        for x in (proc.info["cmdline"] or [])):
                        others.append(proc.pid)
                except psutil.Error:
                    pass
            gate = dict(utc=utc(), predecessor_complete=finished, lock_acquired=acquired,
                        available_bytes=psutil.virtual_memory().available, required_bytes=67*2**30,
                        admission_basis="prior sampled F5 peak 64.951183 GiB + 2 GiB rounded up; not an upper bound",
                        reserve_gib=2, other_solver_pids=others, deadline_utc=deadline.isoformat())
            save(out / "retry_gate.json", gate)
            if datetime.now(timezone.utc) >= deadline:
                save(out / "retry_terminal.json", dict(state="ADMISSION_TIMEOUT", gate=gate))
                return
            if acquired and not others and gate["available_bytes"] >= gate["required_bytes"]:
                break
            if acquired:
                fcntl.flock(lock, fcntl.LOCK_UN)
            time.sleep(30)
        verify(source)
        cmd = [sys.executable, str(source / "repo/scripts/run_flex_full_diagnostic.py"),
               "--hours", "2016", "--start", "5088", "--threads", "16",
               "--case", "case3_thermal_ev_v5", "--aggregate", "1", "--presolve", "2",
               "--reserve-gib", "2", "--author-authorized-low-reserve", "--output", str(out / "F5_retry2g")]
        save(out / "F5_retry2g_launch.json", dict(command=cmd, gate=gate, source_root=str(source),
             source_commit=manifest["diagnostic_commit"], verified_files=len(manifest["files"]),
             authorization="Author requested replacing F5 15 GiB protection with 2 GiB on 2026-10-13",
             original_run=str(prior / "F5"), restart_from_scratch=True,
             monitoring="RSS throughout; reserve callback during optimize only", parallel=False))
        with (out / "F5_retry2g_console.log").open("x") as log, (out / "F5_retry2g_memory.jsonl").open("x") as memory:
            peak = 0
            t0 = time.monotonic()
            child = subprocess.Popen(cmd, cwd=source / "repo", env=env, stdout=log, stderr=subprocess.STDOUT)
            save(out / "retry_active.json", dict(name="F5_retry2g", pid=child.pid, controller_pid=os.getpid()))
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
        record = dict(name="F5_retry2g", returncode=child.returncode, peak_rss_bytes=peak,
                      wall_seconds=time.monotonic()-t0, ended_utc=utc())
        save(out / "F5_retry2g_terminal.json", record)
        result_path = out / "F5_retry2g/result.json"
        result = json.loads(result_path.read_text()) if result_path.exists() else {}
        state = "RESOURCE_STOP" if result.get("resource_stop") else "COMPLETE" if child.returncode == 0 else "PROCESS_ERROR"
        save(out / "retry_terminal.json", dict(state=state, records=[record]))


if __name__ == "__main__":
    main()
