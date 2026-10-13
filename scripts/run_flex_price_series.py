"""Serial P0--P5 campaign; preserve failures and continue, never overwrite runs.

Usage: python scripts/run_flex_price_series.py --prices PATH --output NEW_DIRECTORY
Uses the current interpreter/environment; requires Gurobi 13 and production inputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import psutil


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prices", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--series", choices=["original", "5b"], default="original")
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    matrix = [("P0",2030,2,1,1,1e-8), ("P1",2030,2,1,2,1e-4),
              ("P2",2030,2,1,2,1e-8), ("P3",2030,2,0,2,1e-4),
              ("P4",2030,0,1,2,1e-4), ("P5",2060,2,1,2,1e-4)]
    if a.series == "5b":
        matrix = [("P6",2040,2,1,2,1e-4), ("P7",2050,2,1,2,1e-4),
                  ("P5a",2060,2,0,2,1e-4), ("P5b",2060,2,1,2,1e-4),
                  ("P5c",2060,0,1,2,1e-4), ("P8",2030,2,1,2,1e-4)]
    for name, year, presolve, aggregate, nf, tol in matrix:
        cmd = [sys.executable, str(root / "scripts/price_taker_enrollment.py"),
               "--prices", str(a.prices.resolve()), "--year", str(year), "--price-year", "2030",
               "--presolve", str(presolve), "--aggregate", str(aggregate), "--numeric-focus", str(nf),
               "--scale-flag", "2", "--bar-tol", str(tol), "--threads", "8",
               "--preserve-diagnostic", "--time-limit", "2400", "--output", str(a.output / name)]
        if name in ("P5b", "P8"):
            cmd += ["--agg-fill", "0"]
        meta = dict(command=cmd, started_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    series=a.series, source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
                    diagnostic_sha256={str(f.relative_to(root)): hashlib.sha256(f.read_bytes()).hexdigest()
                        for f in (Path(__file__).resolve(), root/"scripts/price_taker_enrollment.py", root/"scripts/flex_numerics_diagnostics.py")},
                    price_sha256=hashlib.sha256(a.prices.read_bytes()).hexdigest())
        (a.output / f"{name}_launch.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        peak = 0
        with (a.output / f"{name}_console.log").open("w", encoding="utf-8") as log, (a.output / f"{name}_memory.jsonl").open("w") as memory:
            t0 = time.monotonic()
            child = subprocess.Popen(cmd, cwd=root, stdout=log, stderr=subprocess.STDOUT)
            while child.poll() is None:
                try:
                    proc = psutil.Process(child.pid)
                    rss = proc.memory_info().rss + sum(c.memory_info().rss for c in proc.children(recursive=True) if c.is_running())
                    peak = max(peak, rss)
                    memory.write(json.dumps(dict(elapsed=time.monotonic()-t0, rss=rss, available=psutil.virtual_memory().available))+"\n")
                    memory.flush()
                except psutil.Error:
                    pass
                time.sleep(2)
        meta.update(returncode=child.returncode, peak_rss_bytes=peak, wall_seconds=time.monotonic()-t0)
        (a.output / f"{name}_terminal.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(name, child.returncode, peak, flush=True)


if __name__ == "__main__":
    main()
