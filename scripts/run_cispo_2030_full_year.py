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
from cispo_model.data import DATA_ROOT, load_model_data
from cispo_model.io_contract import write_run_provenance
from cispo_model.preflight import estimate_full_model_scale, run_preflight
from cispo_model.runtime_monitor import PeakMemoryMonitor


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sequential CISPO planning-year expansion plus chronological operation"
    )
    parser.add_argument("--config", default="config/optimization_2030.json")
    parser.add_argument(
        "--scenario-config",
        help="Optional v1 partial override under config/scenarios; recorded in provenance.",
    )
    parser.add_argument(
        "--planning-year",
        type=int,
        choices=(2030, 2040, 2050, 2060),
        help="Override the base configuration with one sequential planning year.",
    )
    parser.add_argument(
        "--state-in",
        help=(
            "Prior accepted full-year planning_state directory. Required after 2030."
        ),
    )
    parser.add_argument(
        "--horizon",
        choices=("one_month", "six_months", "full_year"),
        default="full_year",
        help="744h and 4344h runs are code tests only; full_year is the scientific run.",
    )
    parser.add_argument(
        "--diagnostic-hours",
        type=int,
        help=(
            "Build/solve an exact leading-hour diagnostic in [1, 8759]. "
            "Annual costs and policy limits are not rescaled; never interpret it scientifically."
        ),
    )
    parser.add_argument(
        "--export-diagnostic-state",
        action="store_true",
        help=(
            "Export an explicitly test-only state for a diagnostic sequence. "
            "That state is rejected by production runs."
        ),
    )
    parser.add_argument(
        "--allow-diagnostic-state-in",
        action="store_true",
        help="Allow a test-only predecessor state; valid only for a test horizon.",
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
    if args.diagnostic_hours is not None and not 1 <= args.diagnostic_hours < 8760:
        raise SystemExit("--diagnostic-hours must be in [1, 8759]")
    if args.export_diagnostic_state and args.diagnostic_hours is None:
        raise SystemExit("--export-diagnostic-state requires --diagnostic-hours")

    base_config = load_model_config(args.config, args.scenario_config)
    config = (
        base_config.for_planning_year(args.planning_year)
        if args.planning_year is not None
        else base_config
    )
    requested_test_only = bool(
        args.diagnostic_hours is not None
        or config.horizon(args.horizon)["test_only"]
    )
    if args.allow_diagnostic_state_in and not requested_test_only:
        raise SystemExit(
            "--allow-diagnostic-state-in cannot be used for a scientific full-year run"
        )
    from cispo_model.planning_state import PlanningState

    if config.boundary_year == 2025:
        if args.state_in:
            raise SystemExit("2030 uses the 2025 data boundary and must not receive --state-in")
        planning_state = PlanningState.empty(config.boundary_year)
    else:
        if not args.state_in:
            raise SystemExit(
                f"{config.planning_year} requires --state-in from accepted "
                f"{config.boundary_year} full-year results"
            )
        planning_state = PlanningState.load(
            args.state_in,
            expected_boundary_year=config.boundary_year,
            allow_test_only=args.allow_diagnostic_state_in,
        )
        if (
            planning_state.metadata.get("state_use")
            == "TEST_ONLY_TRUNCATED_HORIZON"
            and not requested_test_only
        ):
            raise SystemExit("A diagnostic planning state cannot enter a production run")
    if args.diagnostic_hours is None:
        horizon_name = args.horizon
        horizon = config.horizon(args.horizon)
        optimization_hours = int(horizon["hours"])
        test_only = bool(horizon["test_only"])
        definition = str(horizon["definition"])
        required_gb = float(horizon["minimum_available_memory_gb"])
    else:
        horizon_name = f"diagnostic_{args.diagnostic_hours}h"
        optimization_hours = int(args.diagnostic_hours)
        test_only = True
        definition = (
            f"first {optimization_hours} chronological hours; cyclic over the "
            "selected diagnostic horizon"
        )
        required_gb = float(
            config.horizon("one_month")["minimum_available_memory_gb"]
        )
    output_dir = Path(
        args.output_dir or f"outputs/{config.planning_year}_{horizon_name}"
    )
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    available_gb = psutil.virtual_memory().available / 1024**3
    write_run_provenance(
        output_dir,
        config,
        data_root=DATA_ROOT,
        planning_state=planning_state,
    )
    data = load_model_data(config, planning_state=planning_state)
    preflight = run_preflight(config, data, output_dir / "preflight_report.json")
    if preflight["status"] != "PASS":
        raise SystemExit("Preflight HARD_FAIL; model was not built")
    selected_scale = estimate_full_model_scale(config, data, optimization_hours)
    scope_report = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "horizon": horizon_name,
        "optimization_hours": optimization_hours,
        "configured_full_year_hours": config.hours,
        "definition": definition,
        "result_use": "TEST_ONLY_TRUNCATED_HORIZON" if test_only else "SCIENTIFIC_PRODUCTION",
        "annual_cost_and_policy_scaling": (
            "not rescaled; truncated horizons exist only for code and solver testing"
            if test_only
            else "full annual accounting"
        ),
        "time_boundary": "cyclic_over_selected_horizon",
        "boundary_year": config.boundary_year,
        "planning_year": config.planning_year,
        "scenario_id": config.raw["scenario"]["id"],
        "scenario_family": config.raw["scenario"]["family"],
        "state_in": str(planning_state.root) if planning_state.root else None,
        "state_format": planning_state.metadata.get("format"),
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
            f"{required_gb:.1f} GiB required for {horizon_name}"
        )

    # Lazy imports let data/horizon preflight run before Gurobi is installed.
    from cispo_model.diagnostics import model_statistics, solve_and_report
    from cispo_model.master import export_master_solution
    from cispo_model.monolithic import build_full_year_monolithic
    from cispo_model.solution_export import export_operational_solution
    from cispo_model.result_summary import export_result_summary, finalize_result_manifest
    from cispo_model.io_contract import write_output_catalog
    from cispo_model.planning_state import export_solution_planning_state

    started = datetime.now().astimezone()
    memory_monitor = PeakMemoryMonitor().start()
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
        "scenario_id": config.raw["scenario"]["id"],
        "horizon": horizon_name,
        "optimization_hours": optimization_hours,
        "result_use": scope_report["result_use"],
        "available_memory_gb_before_build": round(available_gb, 2),
        "full_max_cf_used": not args.skip_full_max_cf,
        "memory_after_build": memory_monitor.snapshot(),
        "statistics": statistics,
    }
    (output_dir / "build_report.json").write_text(
        json.dumps(build_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if args.write_mps:
        artifacts.model.write(
            str(output_dir / f"cispo_{config.planning_year}_{optimization_hours}h.mps")
        )
    if args.build_only:
        build_report["memory_at_exit"] = memory_monitor.stop()
        (output_dir / "build_report.json").write_text(
            json.dumps(build_report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(build_report, ensure_ascii=False, indent=2))
        return
    report = solve_and_report(
        artifacts.model,
        config,
        output_dir,
        compute_iis=bool(config.raw["construction"]["compute_iis_on_infeasible"]),
    )
    report.update(
        boundary_year=config.boundary_year,
        planning_year=config.planning_year,
        scenario_id=config.raw["scenario"]["id"],
        scenario_family=config.raw["scenario"]["family"],
        horizon=horizon_name,
        optimization_hours=optimization_hours,
        result_use=scope_report["result_use"],
    )
    (output_dir / "solve_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    export_state = False
    if artifacts.model.SolCount:
        export_master_solution(artifacts, data, output_dir)
        qc = export_operational_solution(artifacts, data, config, output_dir)
        export_result_summary(artifacts, data, config, output_dir)
        export_state = bool(
            (not test_only or args.export_diagnostic_state)
            and report["status"] == "OPTIMAL"
            and qc["status"] == "PASS"
        )
        if export_state:
            report["planning_state_path"] = str(output_dir / "planning_state")
        report["solution_qc_status"] = qc["status"]
        report["solution_qc_path"] = str(output_dir / "solution_qc.json")
    report["runtime_memory"] = memory_monitor.stop()
    if artifacts.model.SolCount:
        report["result_manifest_path"] = str(output_dir / "result_manifest.json")
    (output_dir / "solve_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if export_state:
        export_solution_planning_state(
            artifacts,
            data,
            config,
            output_dir,
            state_use=scope_report["result_use"],
        )
    if artifacts.model.SolCount:
        write_output_catalog(output_dir)
        finalize_result_manifest(output_dir, config)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
