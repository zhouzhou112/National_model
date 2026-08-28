"""Build one isolated 24h Base LP from read-only inputs; forbid solving/presolve.

This is a structural regression, never a surrogate for 2160h/8760h performance.
Source/data paths are explicit; no deployment or server connection is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--wave-root", type=Path, required=True)
    parser.add_argument("--start-hour", type=int, default=2880)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    os.environ["CISPO_DATA_ROOT"] = str(args.data_root.resolve())
    os.environ["CISPO_WAVE_ROOT"] = str(args.wave_root.resolve())
    import gurobipy as gp
    from cispo_model.config import load_model_config
    from cispo_model.data import load_model_data
    from cispo_model.monolithic import build_full_year_monolithic
    from cispo_model.diagnostics import model_statistics
    config = load_model_config(scenario_path="config/scenarios/base.json")
    started = time.monotonic()
    gp.setParam("Threads", 2)
    with patch.object(gp.Model, "optimize", side_effect=AssertionError("optimize forbidden")), \
         patch.object(gp.Model, "presolve", side_effect=AssertionError("presolve forbidden")):
        data = load_model_data(config)
        artifacts = build_full_year_monolithic(config, data, optimization_hours=24,
                                               optimization_start_hour=args.start_hour)
        model = artifacts.model
        model.update()
        stats = model_statistics(model)
        model.write(str(out / "original.mps"))
        report = {"scope": "24H_BUILD_ONLY_REGRESSION_NOT_LARGE_SCALE_BENCHMARK",
                  "optimization_hours": 24, "optimization_start_hour": args.start_hour,
                  "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                  "data_root": str(args.data_root.resolve()), "wave_root": str(args.wave_root.resolve()),
                  "resolved_configuration": config.raw, "statistics": stats,
                  "reservoir_flow_bound_audit": artifacts.index.get("reservoir_flow_bound_audit"),
                  "monolithic_sha256": hashlib.sha256((ROOT / "cispo_model/monolithic.py").read_bytes()).hexdigest(),
                  "fingerprint": model.Fingerprint, "build_seconds": time.monotonic() - started,
                  "optimize_calls": 0, "presolve_calls": 0, "scientifically_accepted": False}
        digest = hashlib.sha256()
        with (out / "original.mps").open("rb") as handle:
            for block in iter(lambda: handle.read(8 * 1024**2), b""):
                digest.update(block)
        report["mps_sha256"] = digest.hexdigest()
        (out / "build_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
        model.dispose()
    print(json.dumps({"output": str(out), "build_seconds": report["build_seconds"], "statistics": stats}))


if __name__ == "__main__":
    main()
