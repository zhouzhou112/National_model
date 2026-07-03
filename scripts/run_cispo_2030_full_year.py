"""Build or solve the 2030 CISPO monolithic model at a controlled horizon."""
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
from cispo_model.preflight import estimate_full_model_scale, run_preflight


def main() -> None:
    parser = argparse.ArgumentParser(
        description="2030 capacity expansion plus chronological operation in one LP"
    )
    parser.add_argument("--config", default="config/optimization_2030.json")
    parser.add_argument(
        "--horizon",
        choices=("one_month", "six_months", "full_year"),
        default="full_year",
        help="744h and 4344h runs are code tests only; full_year is the scientific run.",
    )
    parser.add_argument("--output-dir")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--write-mps", action="store_true")
    parser.add_argument(
        "--skip-full-max-cf",
        action="store_true",
        help="Developer-only structural build; never use for a production solve.",
    )
    args = parser.parse_args()
    if args.skip_full_max_cf and not args.build_only:
        raise SystemExit("--skip-full-max-cf requires --build-only")
    if args.preflight_only and (args.build_only or args.write_mps):
        raise SystemExit("--preflight-only cannot be combined with build/write options")

    config = load_model_config(args.config)
    horizon = config.horizon(args.horizon)
    optimization_hours = int(horizon["hours"])
    test_only = bool(horizon["test_only"])
    output_dir = Path(args.output_dir or f"outputs/2030_{args.horizon}")
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    available_gb = psutil.virtual_memory().available / 1024**3
    required_gb = float(horizon["minimum_available_memory_gb"])
    data = load_model_data(config)
    preflight = run_preflight(config, data, output_dir / "preflight_report.json")
    if preflight["status"] != "PASS":
        raise SystemExit("Preflight HARD_FAIL; model was not built")
    selected_scale = estimate_full_model_scale(config, data, optimization_hours)
    scope_report = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "horizon": args.horizon,
        "optimization_hours": optimization_hours,
        "configured_full_year_hours": config.hours,
        "definition": horizon["definition"],
        "result_use": "TEST_ONLY_TRUNCATED_HORIZON" if test_only else "SCIENTIFIC_PRODUCTION",
        "annual_cost_and_policy_scaling": (
            "not rescaled; truncated horizons exist only for code and solver testing"
            if test_only
            else "full annual accounting"
        ),
        "time_boundary": "cyclic_over_selected_horizon",
        "available_memory_gb": round(available_gb, 2),
        "minimum_available_memory_gb": required_gb,
        "memory_gate_pass": available_gb >= required_gb,
        "scale_estimate": selected_scale.__dict__,
        "gurobi_required_for_build": True,
    }
    (output_dir / "run_scope.json").write_text(
        json.dumps(scope_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if args.preflight_only:
        print(json.dumps(scope_report, ensure_ascii=False, indent=2))
        return
    if available_gb < required_gb:
        raise SystemExit(
            f"HARD_FAIL: available memory {available_gb:.1f} GiB < "
            f"{required_gb:.1f} GiB required for {args.horizon}"
        )

    # Lazy imports let data/horizon preflight run before Gurobi is installed.
    from cispo_model.diagnostics import model_statistics, solve_and_report
    from cispo_model.master import export_master_solution
    from cispo_model.monolithic import build_full_year_monolithic

    started = datetime.now().astimezone()
    artifacts = build_full_year_monolithic(
        config,
        data,
        compute_max_cf=not args.skip_full_max_cf,
        optimization_hours=optimization_hours,
    )
    statistics = model_statistics(artifacts.model)
    build_report = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "build_started_at": started.isoformat(),
        "architecture": "full_year_monolithic_lp",
        "boundary_year": config.boundary_year,
        "planning_year": config.planning_year,
        "horizon": args.horizon,
        "optimization_hours": optimization_hours,
        "result_use": scope_report["result_use"],
        "available_memory_gb_before_build": round(available_gb, 2),
        "full_max_cf_used": not args.skip_full_max_cf,
        "statistics": statistics,
    }
    (output_dir / "build_report.json").write_text(
        json.dumps(build_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if args.write_mps:
        artifacts.model.write(
            str(output_dir / f"cispo_2030_{optimization_hours}h.mps")
        )
    if args.build_only:
        print(json.dumps(build_report, ensure_ascii=False, indent=2))
        return
    report = solve_and_report(
        artifacts.model,
        config,
        output_dir,
        compute_iis=bool(config.raw["construction"]["compute_iis_on_infeasible"]),
    )
    report.update(
        horizon=args.horizon,
        optimization_hours=optimization_hours,
        result_use=scope_report["result_use"],
    )
    (output_dir / "solve_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if artifacts.model.SolCount:
        export_master_solution(artifacts, data, output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
