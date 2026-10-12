"""Finite, serial T550 F1--F5/F6 diagnostic queue (not a recurring monitor).

Run under the existing numerical_validation_solver.lock, after immutable install.
Admission reserves 15 GiB plus a conservative per-window working-set budget.
If unavailable, wait up to 24 hours and record RESOURCE_BLOCKED, never delete runs.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import psutil


def save(path, value):
    path.write_text(json.dumps(value, indent=2)+"\n")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--threads", type=int, default=16)
    a = p.parse_args(); root = a.root.resolve()
    windows = json.loads((root / "windows.json").read_text())
    cool, heat = windows["cooling"]["start"], windows["heating"]["start"]
    runs = [("F1",744,cool,"case3_thermal_ev_v5",1,2), ("F2",744,heat,"case3_thermal_ev_v5",1,2),
            ("F3",744,cool,"base",1,2), ("F4",168,cool,"case3_thermal_ev_v5",1,2),
            ("F5",2016,cool,"case3_thermal_ev_v5",1,2)]
    failed = []
    records = []
    for name, hours, start, case, agg, pre in runs:
        # Append only registered conditional single-factor rescues after F5.
        required = (105 if hours > 744 else 43 if hours > 168 else 27) * 2**30
        deadline = time.monotonic()+24*3600
        while True:
            others = []
            for proc in psutil.process_iter(["pid", "cmdline"]):
                try:
                    cmd = proc.info["cmdline"] or []
                    if proc.pid != os.getpid() and any(Path(x).name in
                        ("run_cispo_2030_full_year.py", "run_probe.py", "run_flex_full_diagnostic.py", "gurobi_cl") for x in cmd):
                        others.append(proc.pid)
                except psutil.Error:
                    pass
            gate = dict(name=name, available=psutil.virtual_memory().available, required=required,
                        other_solvers=others, utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
            save(root / "queue_gate.json", gate)
            if gate["available"] >= required and not others:
                break
            if time.monotonic() >= deadline:
                save(root / "queue_terminal.json", dict(state="RESOURCE_BLOCKED", records=records, gate=gate)); return
            time.sleep(30)
        cmd = [sys.executable, str(root / "repo/scripts/run_flex_full_diagnostic.py"),
               "--hours", str(hours), "--start", str(start), "--threads", str(a.threads),
               "--case", case, "--aggregate", str(agg), "--presolve", str(pre), "--output", str(root / name)]
        save(root / (name+"_launch.json"), dict(command=cmd, gate=gate, parallel=False))
        with (root / (name+"_console.log")).open("w") as log, (root / (name+"_memory.jsonl")).open("w") as memory:
            t0 = time.monotonic(); peak = 0
            child = subprocess.Popen(cmd, cwd=root / "repo", stdout=log, stderr=subprocess.STDOUT)
            save(root / "queue_active.json", dict(name=name, pid=child.pid))
            while child.poll() is None:
                try:
                    proc = psutil.Process(child.pid)
                    rss = proc.memory_info().rss + sum(c.memory_info().rss for c in proc.children(recursive=True) if c.is_running())
                    peak = max(peak, rss)
                    memory.write(json.dumps(dict(elapsed=time.monotonic()-t0, rss=rss, available=psutil.virtual_memory().available))+"\n"); memory.flush()
                except psutil.Error:
                    pass
                time.sleep(2)
        record = dict(name=name, returncode=child.returncode, peak_rss_bytes=peak, wall_seconds=time.monotonic()-t0)
        records.append(record); save(root / "queue_status.json", records)
        diagpath = root / name / "service_diagnostics.json"
        if name in ("F1","F2") and diagpath.exists() and json.loads(diagpath.read_text())["maximum_service_residual_gw_gwh"] > 1e-3:
            failed.append((name,start)); runs.insert(next(i for i,r in enumerate(runs) if r[0]=="F5"), ("F6_"+name+"_agg0",744,start,case,0,2))
        if name.startswith("F6_") and agg==0 and diagpath.exists() and json.loads(diagpath.read_text())["maximum_service_residual_gw_gwh"] > 1e-3:
            runs.insert(next(i for i,r in enumerate(runs) if r[0]=="F5"), (name.replace("agg0","pre0"),744,start,case,1,0))
    save(root / "queue_terminal.json", dict(state="COMPLETE", records=records))


if __name__ == "__main__":
    main()
