"""Build or solve the 2030 CISPO monolithic 8760-hour LP on the server."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import psutil

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cispo_model.config import ROOT, load_model_config
from cispo_model.data import load_model_data
from cispo_model.diagnostics import model_statistics, solve_and_report
from cispo_model.master import export_master_solution
from cispo_model.monolithic import build_full_year_monolithic
from cispo_model.preflight import run_preflight


def main() -> None:
    parser = argparse.ArgumentParser(
        description="2030 capacity expansion plus all 8760 chronological hours in one LP"
    )
    parser.add_argument("--config", default="config/optimization_2030.json")
    parser.add_argument("--output-dir", default="outputs/2030_full_year")
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--write-mps", action="store_true")
    parser.add_argument(
        "--structural-smoke-hours",
        type=int,
        help="Build only the first N hours to test dimensions/API; cannot solve.",
    )
    parser.add_argument(
        "--skip-full-max-cf",
        action="store_true",
        help="Developer-only structural build; never use for a production solve.",
    )
    args = parser.parse_args()
    if args.structural_smoke_hours is not None and not args.build_only:
        raise SystemExit("--structural-smoke-hours requires --build-only")
    config = load_model_config(args.config)
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    available_gb = psutil.virtual_memory().available / 1024**3
    required_gb = float(
        config.raw["construction"]["minimum_available_memory_gb_before_build"]
    )
    if args.structural_smoke_hours is None and available_gb < required_gb:
        raise SystemExit(
            f"HARD_FAIL: available memory {available_gb:.1f} GiB < required {required_gb:.1f} GiB"
        )

    data = load_model_data(config)
    preflight = run_preflight(config, data, output_dir / "preflight_report.json")
    if preflight["status"] != "PASS":
        raise SystemExit("Preflight HARD_FAIL; model was not built")
    started = datetime.now().astimezone()
    artifacts = build_full_year_monolithic(
        config,
        data,
        compute_max_cf=(not args.skip_full_max_cf and args.structural_smoke_hours is None),
        structural_smoke_hours=args.structural_smoke_hours,
    )
    statistics = model_statistics(artifacts.model)
    build_report = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "build_started_at": started.isoformat(),
        "architecture": "full_year_monolithic_lp",
        "boundary_year": config.boundary_year,
        "planning_year": config.planning_year,
        "hours": config.hours,
        "structural_smoke_hours": args.structural_smoke_hours,
        "available_memory_gb_before_build": round(available_gb, 2),
        "full_max_cf_used": not args.skip_full_max_cf and args.structural_smoke_hours is None,
        "statistics": statistics,
    }
    (output_dir / "build_report.json").write_text(
        json.dumps(build_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if args.write_mps:
        artifacts.model.write(str(output_dir / "cispo_2030_8760.mps"))
    if args.build_only:
        print(json.dumps(build_report, ensure_ascii=False, indent=2))
        return
    report = solve_and_report(
        artifacts.model,
        config,
        output_dir,
        compute_iis=bool(config.raw["construction"]["compute_iis_on_infeasible"]),
    )
    if artifacts.model.SolCount:
        export_master_solution(artifacts, data, output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
