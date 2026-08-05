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
from cispo_model.flexible_load_numerics import (
    assess_flexible_load_solver_compatibility,
    prebuild_flexible_load_solver_compatibility,
)
from cispo_model.io_contract import validate_result_manifest, write_run_provenance
from cispo_model.preflight import estimate_full_model_scale, run_preflight
from cispo_model.result_dashboard import build_result_dashboard
from cispo_model.run_contract import (
    RUN_IDENTITY_FILENAME,
    claim_output_directory,
    configuration_identity,
    solver_result_is_accepted,
)
from cispo_model.runtime_monitor import PeakMemoryMonitor


CLOUD_FULL_YEAR_PROFILE_IDS = {
    "barrier_checkpoint_full_year_cloud_v1",
    "deferred_crossover2_full_year_cloud_v1",
}
CLOUD_FULL_YEAR_MIN_AVAILABLE_MEMORY_GIB = 640.0


def diagnostic_memory_requirement_gb(config, hours: int) -> float:
    """Map an arbitrary diagnostic length to the next validated memory tier."""
    for name in ("one_month", "six_months", "full_year"):
        horizon = config.horizon(name)
        if int(hours) <= int(horizon["hours"]):
            return float(horizon["minimum_available_memory_gb"])
    raise ValueError(f"Diagnostic horizon {hours} exceeds the configured full year")


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
        "--solver-config",
        help=(
            "Optional v1 numerics-only solver profile. It cannot change the "
            "scientific scenario and is recorded with a SHA256 snapshot."
        ),
    )
    parser.add_argument(
        "--formulation-config",
        help=(
            "Optional v1 algebraically equivalent formulation profile. It may "
            "change matrix structure only and is recorded with a SHA256 snapshot."
        ),
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
            "Build/solve an exact contiguous-hour diagnostic in [1, 8759]. "
            "Annual flow policy/resource limits use hours/8760 scaling, while "
            "annualized planning costs remain unscaled; never interpret it scientifically."
        ),
    )
    parser.add_argument(
        "--diagnostic-start-hour",
        type=int,
        default=0,
        help=(
            "Zero-based model-year start hour for --diagnostic-hours. "
            "The selected window must remain within [0, 8760); default 0."
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
        "--export-warm-start-basis",
        action="store_true",
        help=(
            "Export a post-crossover Gurobi .bas file plus a strict named-LP "
            "identity manifest. Restricted to diagnostic horizons."
        ),
    )
    parser.add_argument(
        "--export-scientific-solver-artifacts",
        action="store_true",
        help=(
            "After an accepted full-year Base solve, export selective .sol, "
            ".bas, .prm and lightweight fingerprint artifacts. Never valid "
            "for truncated horizons, non-Base cases or MGA outputs."
        ),
    )
    parser.add_argument(
        "--export-barrier-checkpoint",
        action="store_true",
        help=(
            "Export ordered BarX/BarPi arrays after an accepted Crossover=0 "
            "solve. This is automatic for horizons longer than 744h."
        ),
    )
    parser.add_argument(
        "--engineering-barrier-checkpoint-only",
        action="store_true",
        help=(
            "Treat a Crossover=0 solve as Stage A only: persist finite ordered "
            "BarX/BarPi immediately after BarStatus=OPTIMAL, never publish it "
            "as a scientific result or planning-state anchor."
        ),
    )
    parser.add_argument(
        "--allow-nonbasic-planning-state",
        action="store_true",
        help=(
            "Explicitly allow an accepted Crossover=0 Barrier capacity solution "
            "with a closed BarX/BarPi checkpoint to form the next-year cohort "
            "state. Planning sequences set this flag deliberately."
        ),
    )
    parser.add_argument(
        "--primal-dual-checkpoint-in",
        help=(
            "Accepted Barrier-first output root used to seed a separate exact-LP "
            "deferred crossover run. Never overwrites the source result."
        ),
    )
    parser.add_argument(
        "--allow-primal-dual-crossover",
        action="store_true",
        help="Explicitly acknowledge exact-LP deferred crossover from BarX/BarPi.",
    )
    parser.add_argument(
        "--allow-engineering-barrier-checkpoint",
        action="store_true",
        help=(
            "Explicitly allow Stage B to consume a non-scientific "
            "ENGINEERING_BARRIER_CHECKPOINT_ONLY source."
        ),
    )
    parser.add_argument(
        "--allow-deferred-crossover-planning-state",
        action="store_true",
        help=(
            "After Stage B alone reaches full scientific acceptance, allow its "
            "basic solution to export the next-year planning state."
        ),
    )
    parser.add_argument(
        "--allow-inline-crossover",
        action="store_true",
        help=(
            "Explicitly permit Barrier and crossover in one solve for horizons "
            "longer than 744h. The default long-horizon contract is Barrier-first."
        ),
    )
    parser.add_argument(
        "--basis-in",
        help=(
            "Accepted diagnostic output directory containing warm_start_basis.bas "
            "and warm_start_basis_manifest.json."
        ),
    )
    parser.add_argument(
        "--allow-basis-reuse",
        action="store_true",
        help="Explicitly acknowledge test-only LP basis reuse for this run.",
    )
    parser.add_argument(
        "--allow-cross-year-basis",
        action="store_true",
        help="Permit a checked diagnostic basis from another planning year.",
    )
    parser.add_argument(
        "--allow-diagnostic-state-in",
        action="store_true",
        help="Allow a test-only predecessor state; valid only for a test horizon.",
    )
    parser.add_argument(
        "--mga-spec",
        help=(
            "Explicit MGA secondary-objective JSON. It is valid only with an "
            "accepted scientific full-year Base baseline."
        ),
    )
    parser.add_argument(
        "--mga-baseline",
        help=(
            "Accepted least-cost Base result root used to set the MGA cost cap."
        ),
    )
    parser.add_argument("--output-dir")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--write-mps", action="store_true")
    parser.add_argument(
        "--constraint-family-audit",
        action="store_true",
        help=(
            "Write a raw LP row/column sparsity census by model family. "
            "It does not modify the model and reports presolve only globally."
        ),
    )
    parser.add_argument(
        "--constraint-family-audit-max-nonzeros",
        type=int,
        default=50_000_000,
        help=(
            "Safety limit for the audit's explicit sparse-matrix access; "
            "default 50,000,000."
        ),
    )
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
    if args.diagnostic_start_hour < 0:
        raise SystemExit("--diagnostic-start-hour must be nonnegative")
    if args.diagnostic_hours is None and args.diagnostic_start_hour != 0:
        raise SystemExit(
            "--diagnostic-start-hour requires --diagnostic-hours"
        )
    if (
        args.diagnostic_hours is not None
        and args.diagnostic_start_hour + args.diagnostic_hours > 8760
    ):
        raise SystemExit(
            "--diagnostic-start-hour + --diagnostic-hours must not exceed 8760"
        )
    if args.export_diagnostic_state and args.diagnostic_hours is None:
        raise SystemExit("--export-diagnostic-state requires --diagnostic-hours")
    if args.export_warm_start_basis and args.diagnostic_hours is None:
        raise SystemExit("--export-warm-start-basis requires --diagnostic-hours")
    if args.basis_in and not args.allow_basis_reuse:
        raise SystemExit("--basis-in requires explicit --allow-basis-reuse")
    if args.allow_basis_reuse and not args.basis_in:
        raise SystemExit("--allow-basis-reuse requires --basis-in")
    if args.allow_cross_year_basis and not args.basis_in:
        raise SystemExit("--allow-cross-year-basis requires --basis-in")
    if args.primal_dual_checkpoint_in and not args.allow_primal_dual_crossover:
        raise SystemExit(
            "--primal-dual-checkpoint-in requires --allow-primal-dual-crossover"
        )
    if args.allow_primal_dual_crossover and not args.primal_dual_checkpoint_in:
        raise SystemExit(
            "--allow-primal-dual-crossover requires --primal-dual-checkpoint-in"
        )
    if (
        args.allow_engineering_barrier_checkpoint
        and not args.primal_dual_checkpoint_in
    ):
        raise SystemExit(
            "--allow-engineering-barrier-checkpoint requires "
            "--primal-dual-checkpoint-in"
        )
    if (
        args.allow_deferred_crossover_planning_state
        and not args.primal_dual_checkpoint_in
    ):
        raise SystemExit(
            "--allow-deferred-crossover-planning-state requires "
            "--primal-dual-checkpoint-in"
        )
    if bool(args.mga_spec) != bool(args.mga_baseline):
        raise SystemExit("--mga-spec and --mga-baseline must be supplied together")
    if args.constraint_family_audit_max_nonzeros < 1:
        raise SystemExit("--constraint-family-audit-max-nonzeros must be positive")

    base_config = load_model_config(
        args.config,
        args.scenario_config,
        args.solver_config,
        args.formulation_config,
    )
    config = (
        base_config.for_planning_year(args.planning_year)
        if args.planning_year is not None
        else base_config
    )
    requested_test_only = bool(
        args.diagnostic_hours is not None
        or config.horizon(args.horizon)["test_only"]
    )
    numerics = config.raw["numerics"]
    nonbasic_primal_dual_requested = bool(
        int(numerics.get("method", -1)) == 2
        and int(numerics.get("crossover", -1)) == 0
        and int(numerics.get("solution_target", -1)) == 1
    )
    requested_optimization_hours = int(
        args.diagnostic_hours
        if args.diagnostic_hours is not None
        else config.horizon(args.horizon)["hours"]
    )
    if nonbasic_primal_dual_requested and (
        args.basis_in
        or args.export_warm_start_basis
        or args.export_scientific_solver_artifacts
        or args.mga_spec
    ):
        raise SystemExit(
            "The optimal primal-dual nonbasic contract cannot be combined "
            "with basis import/export, scientific .bas artifacts, or MGA"
        )
    if args.export_barrier_checkpoint and not nonbasic_primal_dual_requested:
        raise SystemExit(
            "--export-barrier-checkpoint requires Method=2, Crossover=0, "
            "SolutionTarget=1"
        )
    if (
        args.engineering_barrier_checkpoint_only
        and not nonbasic_primal_dual_requested
    ):
        raise SystemExit(
            "--engineering-barrier-checkpoint-only requires Method=2, "
            "Crossover=0, SolutionTarget=1"
        )
    if (
        args.engineering_barrier_checkpoint_only
        and args.allow_nonbasic_planning_state
    ):
        raise SystemExit(
            "Stage A engineering checkpoints can never export planning_state"
        )
    if args.allow_nonbasic_planning_state and not nonbasic_primal_dual_requested:
        raise SystemExit(
            "--allow-nonbasic-planning-state requires Method=2, Crossover=0, "
            "SolutionTarget=1"
        )
    if args.allow_nonbasic_planning_state and requested_test_only and not (
        args.export_diagnostic_state
    ):
        raise SystemExit(
            "A diagnostic nonbasic planning state also requires "
            "--export-diagnostic-state"
        )
    if args.allow_nonbasic_planning_state and not (
        args.export_barrier_checkpoint or requested_optimization_hours > 744
    ):
        raise SystemExit(
            "A nonbasic planning state requires an accepted Barrier checkpoint; "
            "pass --export-barrier-checkpoint for horizons up to 744h"
        )
    if args.primal_dual_checkpoint_in:
        if args.basis_in or args.mga_spec or nonbasic_primal_dual_requested:
            raise SystemExit(
                "Deferred primal/dual crossover cannot be combined with a basis, "
                "MGA, or another Crossover=0 solve"
            )
        if (
            int(numerics.get("method", -1)) != 2
            or int(numerics.get("crossover", 0)) <= 0
            or int(numerics.get("lp_warm_start", -1)) != 2
        ):
            raise SystemExit(
                "Deferred crossover requires Method=2, Crossover>0 and LPWarmStart=2"
            )
    profile_id = config.raw.get("solver_profile", {}).get("id")
    if (
        profile_id == "barrier_checkpoint_full_year_cloud_v1"
        and not args.engineering_barrier_checkpoint_only
    ):
        raise SystemExit(
            "barrier_checkpoint_full_year_cloud_v1 requires "
            "--engineering-barrier-checkpoint-only"
        )
    if (
        profile_id == "deferred_crossover2_full_year_cloud_v1"
        and not args.primal_dual_checkpoint_in
    ):
        raise SystemExit(
            "deferred_crossover2_full_year_cloud_v1 requires "
            "--primal-dual-checkpoint-in"
        )
    if profile_id in CLOUD_FULL_YEAR_PROFILE_IDS and requested_test_only:
        raise SystemExit(
            f"{profile_id} is restricted to the scientific full-year horizon"
        )
    if (
        requested_optimization_hours > 744
        and not args.preflight_only
        and not args.build_only
        and int(numerics.get("crossover", 0)) > 0
        and not args.primal_dual_checkpoint_in
        and not args.allow_inline_crossover
    ):
        raise SystemExit(
            "HARD_FAIL: horizons longer than 744h use Barrier-first acceptance. "
            "Select the nonbasic primal/dual profile, seed a deferred crossover, "
            "or explicitly pass --allow-inline-crossover."
        )
    if args.export_scientific_solver_artifacts and requested_test_only:
        raise SystemExit(
            "--export-scientific-solver-artifacts requires the full-year horizon"
        )
    if (
        args.export_scientific_solver_artifacts
        and base_config.raw["scenario"].get("analysis_role") != "BASELINE"
    ):
        raise SystemExit(
            "--export-scientific-solver-artifacts is restricted to Base"
        )
    if args.export_scientific_solver_artifacts and args.mga_spec:
        raise SystemExit(
            "--export-scientific-solver-artifacts cannot be used for MGA"
        )
    if args.allow_diagnostic_state_in and not requested_test_only:
        raise SystemExit(
            "--allow-diagnostic-state-in cannot be used for a scientific full-year run"
        )
    if args.mga_spec and requested_test_only:
        raise SystemExit("MGA requires the configured scientific full-year horizon")
    if args.mga_spec and (
        args.export_diagnostic_state
        or args.export_warm_start_basis
        or args.basis_in
        or args.allow_diagnostic_state_in
    ):
        raise SystemExit("MGA cannot be combined with diagnostic state or basis reuse")
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
        optimization_start_hour = 0
        test_only = bool(horizon["test_only"])
        definition = str(horizon["definition"])
        required_gb = float(horizon["minimum_available_memory_gb"])
    else:
        horizon_name = f"diagnostic_{args.diagnostic_hours}h"
        optimization_hours = int(args.diagnostic_hours)
        optimization_start_hour = int(args.diagnostic_start_hour)
        test_only = True
        definition = (
            f"{optimization_hours} chronological hours starting at zero-based "
            f"model hour {optimization_start_hour}; cyclic over the selected "
            "diagnostic horizon"
        )
        required_gb = diagnostic_memory_requirement_gb(
            config, optimization_hours
        )
    if profile_id in CLOUD_FULL_YEAR_PROFILE_IDS:
        required_gb = max(
            required_gb,
            CLOUD_FULL_YEAR_MIN_AVAILABLE_MEMORY_GIB,
        )
    output_dir = Path(
        args.output_dir or f"outputs/{config.planning_year}_{horizon_name}"
    )
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    try:
        claim_output_directory(output_dir)
    except RuntimeError as error:
        raise SystemExit(f"HARD_FAIL: {error}") from error

    available_gb = psutil.virtual_memory().available / 1024**3
    write_run_provenance(
        output_dir,
        config,
        data_root=DATA_ROOT,
        planning_state=planning_state,
    )
    (output_dir / RUN_IDENTITY_FILENAME).write_text(
        json.dumps(
            configuration_identity(config, data_root=DATA_ROOT),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    data = load_model_data(config, planning_state=planning_state)
    time_rows = (
        data.load[["hour_index", "datetime_bj"]]
        .drop_duplicates("hour_index")
        .sort_values("hour_index")
    )
    optimization_stop_hour = optimization_start_hour + optimization_hours
    selected_time_rows = time_rows.iloc[
        optimization_start_hour:optimization_stop_hour
    ]
    if len(selected_time_rows) != optimization_hours:
        raise SystemExit("Selected diagnostic time window is incomplete")
    selected_time_start_bj = str(selected_time_rows.datetime_bj.iloc[0])
    selected_time_end_bj = str(selected_time_rows.datetime_bj.iloc[-1])
    prebuild_solver_numerical_compatibility = (
        prebuild_flexible_load_solver_compatibility(
            config,
            data,
            hours=optimization_hours,
            hour_start=optimization_start_hour,
        )
    )
    preflight = run_preflight(config, data, output_dir / "preflight_report.json")
    if preflight["status"] != "PASS":
        raise SystemExit("Preflight HARD_FAIL; model was not built")
    selected_scale = estimate_full_model_scale(config, data, optimization_hours)
    scope_report = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "horizon": horizon_name,
        "optimization_hours": optimization_hours,
        "optimization_start_hour": optimization_start_hour,
        "optimization_stop_hour_exclusive": optimization_stop_hour,
        "selected_time_start_bj": selected_time_start_bj,
        "selected_time_end_bj": selected_time_end_bj,
        "configured_full_year_hours": config.hours,
        "definition": definition,
        "result_use": "TEST_ONLY_TRUNCATED_HORIZON" if test_only else "SCIENTIFIC_PRODUCTION",
        "scientific_acceptance_mode": (
            "ENGINEERING_BARRIER_CHECKPOINT_ONLY"
            if args.engineering_barrier_checkpoint_only
            else "STANDARD_STRICT_ACCEPTANCE"
        ),
        "annual_cost_and_policy_scaling": (
            "annualized planning costs unscaled; annual flow policy and resource "
            "accounts scaled by optimization_hours/configured_full_year_hours"
            if test_only
            else "full annual accounting"
        ),
        "annualized_planning_cost_scaling_factor": 1.0,
        "annual_flow_policy_resource_scaling_factor": (
            float(optimization_hours) / float(config.hours)
        ),
        "time_boundary": "cyclic_over_selected_horizon",
        "boundary_year": config.boundary_year,
        "planning_year": config.planning_year,
        "scenario_id": config.raw["scenario"]["id"],
        "scenario_family": config.raw["scenario"]["family"],
        "analysis_role": config.raw["scenario"]["analysis_role"],
        "publication_status": config.raw["scenario"]["publication_status"],
        "baseline_contract_case_id": config.raw["scientific_case"]["case_id"],
        "formulation_profile_id": config.raw.get("formulation_profile", {}).get(
            "id"
        ),
        "annual_emissions_accounting": config.raw["formulation"][
            "annual_emissions_accounting"
        ],
        "state_in": str(planning_state.root) if planning_state.root else None,
        "state_format": planning_state.metadata.get("format"),
        "available_memory_gb": round(available_gb, 2),
        "minimum_available_memory_gb": required_gb,
        "memory_gate_pass": available_gb >= required_gb,
        "scale_estimate": selected_scale.__dict__,
        "gurobi_required_for_build": True,
        "solution_contract_requested": {
            "mode": (
                "OPTIMAL_PRIMAL_DUAL_NONBASIC"
                if nonbasic_primal_dual_requested
                else "OPTIMAL_BASIC_OR_DEFAULT"
            ),
            "basis_required": not nonbasic_primal_dual_requested,
            "dual_attribute": (
                "BarPi" if nonbasic_primal_dual_requested else "Pi"
            ),
        },
        "basis_reuse_request": {
            "basis_in": str(args.basis_in) if args.basis_in else None,
            "allow_basis_reuse": bool(args.allow_basis_reuse),
            "allow_cross_year_basis": bool(args.allow_cross_year_basis),
            "export_warm_start_basis": bool(args.export_warm_start_basis),
        },
        "barrier_first_workflow": {
            "nonbasic_primal_dual_requested": nonbasic_primal_dual_requested,
            "primary_checkpoint_requested": bool(
                nonbasic_primal_dual_requested
                and not args.engineering_barrier_checkpoint_only
                and (
                    args.export_barrier_checkpoint
                    or optimization_hours > 744
                )
            ),
            "engineering_checkpoint_requested": bool(
                nonbasic_primal_dual_requested
                and args.engineering_barrier_checkpoint_only
            ),
            "deferred_crossover_source": (
                str(args.primal_dual_checkpoint_in)
                if args.primal_dual_checkpoint_in
                else None
            ),
            "engineering_checkpoint_only": bool(
                args.engineering_barrier_checkpoint_only
            ),
            "engineering_checkpoint_source_explicitly_allowed": bool(
                args.allow_engineering_barrier_checkpoint
            ),
            "inline_crossover_explicitly_allowed": bool(
                args.allow_inline_crossover
            ),
            "nonbasic_planning_state_explicitly_allowed": bool(
                args.allow_nonbasic_planning_state
            ),
            "deferred_crossover_planning_state_explicitly_allowed": bool(
                args.allow_deferred_crossover_planning_state
            ),
            "planning_state_policy": (
                "STAGE_A_ENGINEERING_CHECKPOINT_NEVER_EXPORTS_STATE"
                if args.engineering_barrier_checkpoint_only
                else (
                    "ACCEPTED_STAGE_B_BASIC_CAPACITY_STATE"
                    if args.allow_deferred_crossover_planning_state
                    else (
                        "ACCEPTED_OPTIMAL_NONBASIC_BARRIER_CAPACITY_STATE"
                        if args.allow_nonbasic_planning_state
                        else (
                            "POSTHOC_CROSSOVER_ANALYSIS_DERIVATIVE_NO_STATE"
                            if args.primal_dual_checkpoint_in
                            else "DEFAULT_BASIC_OR_NO_STATE"
                        )
                    )
                )
            ),
        },
        "analysis_mode": "BASE_MINIMUM_COST",
        "mga": None,
        "scientific_solver_artifacts_requested": bool(
            args.export_scientific_solver_artifacts
        ),
        "solver_numerical_compatibility_prebuild": (
            prebuild_solver_numerical_compatibility
        ),
    }
    (output_dir / "run_scope.json").write_text(
        json.dumps(scope_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    mga_request = None
    if args.mga_spec:
        from cispo_model.mga import prepare_mga_request

        mga_request = prepare_mga_request(
            args.mga_spec,
            args.mga_baseline,
            config,
            output_dir / "input_manifest.csv",
        )
        scope_report["analysis_mode"] = mga_request["analysis_mode"]
        scope_report["mga"] = {
            key: value
            for key, value in mga_request.items()
            if key not in {"baseline"}
        }
        scope_report["mga"]["baseline_result_manifest_sha256"] = mga_request[
            "baseline"
        ]["baseline_result_manifest_sha256"]
        (output_dir / "mga_request.json").write_text(
            json.dumps(mga_request, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (output_dir / "run_scope.json").write_text(
            json.dumps(scope_report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.preflight_only:
        print(json.dumps(scope_report, ensure_ascii=False, indent=2))
        if prebuild_solver_numerical_compatibility["status"] != "PASS":
            raise SystemExit(
                "Preflight numerical compatibility HARD_FAIL: "
                + str(prebuild_solver_numerical_compatibility["reason"])
            )
        return
    if (
        not args.build_only
        and prebuild_solver_numerical_compatibility["status"] != "PASS"
    ):
        raise RuntimeError(
            str(prebuild_solver_numerical_compatibility["reason"])
        )
    if available_gb < required_gb:
        raise SystemExit(
            f"HARD_FAIL: available memory {available_gb:.1f} GiB < "
            f"{required_gb:.1f} GiB required for {horizon_name}"
        )

    # Lazy imports let data/horizon preflight run before Gurobi is installed.
    from cispo_model.diagnostics import model_statistics, solve_and_report
    from cispo_model.model_structure_audit import audit_model_structure
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
        optimization_start_hour=optimization_start_hour,
    )
    # Every run records a constant-memory Gurobi identity. Exact ordered names
    # and the raw CSR pattern are materialized only for explicit guarded basis
    # import/export, never merely because a long-horizon solve was requested.
    from cispo_model.basis_reuse import (
        lightweight_lp_identity,
        lp_topology_identity,
    )

    lp_model = lightweight_lp_identity(artifacts.model)
    lp_topology = (
        lp_topology_identity(artifacts.model)
        if args.basis_in or args.export_warm_start_basis
        else None
    )
    (output_dir / RUN_IDENTITY_FILENAME).write_text(
        json.dumps(
            configuration_identity(
                config,
                data_root=DATA_ROOT,
                lp_model=lp_model,
                lp_topology=lp_topology,
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    mga_run = None
    if mga_request is not None:
        from cispo_model.mga import apply_mga_secondary_objective

        mga_run = apply_mga_secondary_objective(artifacts, data, mga_request)
        (output_dir / "mga_run.json").write_text(
            json.dumps(mga_run, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    warm_start = None
    if args.basis_in:
        from cispo_model.basis_reuse import prepare_basis_reuse

        warm_start = prepare_basis_reuse(
            args.basis_in,
            artifacts.model,
            config,
            optimization_hours=optimization_hours,
            optimization_start_hour=optimization_start_hour,
            result_use=scope_report["result_use"],
            allow_cross_year=bool(args.allow_cross_year_basis),
        )
        (output_dir / "warm_start_input.json").write_text(
            json.dumps(warm_start, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    primal_dual_start = None
    if args.primal_dual_checkpoint_in:
        from cispo_model.primal_dual_checkpoint import (
            prepare_primal_dual_crossover,
        )

        primal_dual_start = prepare_primal_dual_crossover(
            args.primal_dual_checkpoint_in,
            output_dir,
            artifacts.model,
            config,
            optimization_hours=optimization_hours,
            optimization_start_hour=optimization_start_hour,
            result_use=scope_report["result_use"],
            allow_engineering_checkpoint=bool(
                args.allow_engineering_barrier_checkpoint
            ),
        )
        (output_dir / "primal_dual_start_input.json").write_text(
            json.dumps(primal_dual_start, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    structure_audit_path = output_dir / "constraint_family_audit.json"
    structure_audit = None
    if args.constraint_family_audit:
        structure_audit = audit_model_structure(
            artifacts.model,
            max_matrix_nonzeros=args.constraint_family_audit_max_nonzeros,
        )
        structure_audit_path.write_text(
            json.dumps(structure_audit, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    statistics = model_statistics(artifacts.model)
    flexible_load_structural_audit = artifacts.index.get(
        "flexible_load_structural_audit", {}
    )
    flexible_formulation = str(
        config.raw["flexible_load"].get("formulation")
    )
    compatibility_structural_audit = (
        flexible_load_structural_audit
        if bool(config.raw["features"]["flexible_load"])
        and flexible_formulation == "integrated_service_constrained_v5"
        else {}
    )
    solver_numerical_compatibility = (
        assess_flexible_load_solver_compatibility(
            compatibility_structural_audit,
            config.raw["numerics"],
        )
    )
    build_report = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "build_started_at": started.isoformat(),
        "architecture": "full_year_monolithic_lp",
        "boundary_year": config.boundary_year,
        "planning_year": config.planning_year,
        "scenario_id": config.raw["scenario"]["id"],
        "formulation_profile_id": config.raw.get("formulation_profile", {}).get(
            "id"
        ),
        "annual_emissions_accounting": config.raw["formulation"][
            "annual_emissions_accounting"
        ],
        "horizon": horizon_name,
        "optimization_hours": optimization_hours,
        "optimization_start_hour": optimization_start_hour,
        "optimization_stop_hour_exclusive": optimization_stop_hour,
        "selected_time_start_bj": selected_time_start_bj,
        "selected_time_end_bj": selected_time_end_bj,
        "result_use": scope_report["result_use"],
        "available_memory_gb_before_build": round(available_gb, 2),
        "full_max_cf_used": not args.skip_full_max_cf,
        "constraint_family_audit": {
            "enabled": bool(args.constraint_family_audit),
            "path": str(structure_audit_path) if structure_audit else None,
            "matrix_nonzero_safety_limit": (
                int(args.constraint_family_audit_max_nonzeros)
                if args.constraint_family_audit
                else None
            ),
        },
        "flexible_load_structural_audit": (
            flexible_load_structural_audit
        ),
        "solver_numerical_compatibility": (
            solver_numerical_compatibility
        ),
        "solver_numerical_compatibility_prebuild": (
            prebuild_solver_numerical_compatibility
        ),
        "solver_numerical_compatibility_gate_consistent": (
            solver_numerical_compatibility
            == prebuild_solver_numerical_compatibility
        ),
        "memory_after_build": memory_monitor.snapshot(),
        "statistics": statistics,
        "warm_start": warm_start,
        "primal_dual_start": primal_dual_start,
        "mga": mga_run,
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
    if not build_report["solver_numerical_compatibility_gate_consistent"]:
        build_report["memory_at_exit"] = memory_monitor.stop()
        (output_dir / "build_report.json").write_text(
            json.dumps(build_report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        raise RuntimeError(
            "Flexible-load numerical compatibility changed between "
            "prebuild and postbuild audits"
        )
    if solver_numerical_compatibility["status"] != "PASS":
        build_report["memory_at_exit"] = memory_monitor.stop()
        (output_dir / "build_report.json").write_text(
            json.dumps(build_report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        raise RuntimeError(
            str(solver_numerical_compatibility["reason"])
        )
    report = solve_and_report(
        artifacts.model,
        config,
        output_dir,
        compute_iis=bool(config.raw["construction"]["compute_iis_on_infeasible"]),
        warm_start=warm_start,
        primal_dual_start=primal_dual_start,
    )
    report.update(
        boundary_year=config.boundary_year,
        planning_year=config.planning_year,
        scenario_id=config.raw["scenario"]["id"],
        scenario_family=config.raw["scenario"]["family"],
        analysis_role=config.raw["scenario"]["analysis_role"],
        publication_status=config.raw["scenario"]["publication_status"],
        baseline_contract_case_id=config.raw["scientific_case"]["case_id"],
        horizon=horizon_name,
        optimization_hours=optimization_hours,
        optimization_start_hour=optimization_start_hour,
        result_use=scope_report["result_use"],
    )
    (output_dir / "solve_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    engineering_checkpoint_completed = False
    barrier_status_code = report.get("solution_contract", {}).get(
        "barrier_status_code"
    )
    barrier_iterations = int(
        report.get("iteration_counts", {}).get("barrier", 0)
    )
    if args.engineering_barrier_checkpoint_only and (
        barrier_status_code == 2 or barrier_iterations > 0
    ):
        try:
            from cispo_model.primal_dual_checkpoint import (
                CHECKPOINT_DIRECTORY,
                CHECKPOINT_MANIFEST,
                export_barrier_primal_dual_checkpoint,
            )

            complete_barrier = barrier_status_code == 2
            engineering_checkpoint = export_barrier_primal_dual_checkpoint(
                artifacts.model,
                config,
                output_dir,
                solve_report=report,
                optimization_hours=optimization_hours,
                optimization_start_hour=optimization_start_hour,
                result_use=scope_report["result_use"],
                solution_qc=None,
                accepted_primary=False,
                engineering_only=complete_barrier,
                allow_incomplete_barrier=not complete_barrier,
            )
            engineering_checkpoint_completed = complete_barrier
            report["barrier_checkpoint"] = {
                "status": engineering_checkpoint["checkpoint_status"],
                "scientifically_accepted": False,
                "deferred_crossover_eligible": complete_barrier,
                "engineering_shadow_prices_available": True,
                "path": str(
                    output_dir / CHECKPOINT_DIRECTORY / CHECKPOINT_MANIFEST
                ),
            }
            report["run_completion_status"] = (
                "ENGINEERING_BARRIER_CHECKPOINT_COMPLETE"
                if complete_barrier
                else "INCOMPLETE_BARRIER_RECOVERY_SAVED"
            )
            # Persist this milestone before any optional downstream export.
            (output_dir / "solve_report.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except Exception as error:
            checkpoint_error = {
                "status": "ENGINEERING_CHECKPOINT_EXPORT_FAILED",
                "error_type": type(error).__name__,
                "error": str(error),
            }
            (output_dir / "barrier_checkpoint_error.json").write_text(
                json.dumps(checkpoint_error, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report["barrier_checkpoint"] = checkpoint_error
    if (
        int(report.get("solver_parameters", {}).get("method", -1)) == 2
        and int(report.get("solver_parameters", {}).get("crossover", 0)) > 0
        and report.get("solution_contract", {}).get("barrier_status_code") == 2
        and report.get("status") != "OPTIMAL"
    ):
        try:
            from cispo_model.primal_dual_checkpoint import (
                CHECKPOINT_DIRECTORY,
                CHECKPOINT_MANIFEST,
                export_barrier_primal_dual_checkpoint,
            )

            recovery = export_barrier_primal_dual_checkpoint(
                artifacts.model,
                config,
                output_dir,
                solve_report=report,
                optimization_hours=optimization_hours,
                optimization_start_hour=optimization_start_hour,
                result_use=scope_report["result_use"],
                solution_qc=None,
                accepted_primary=False,
            )
            report["barrier_checkpoint"] = {
                "status": recovery["checkpoint_status"],
                "scientifically_accepted": False,
                "path": str(
                    output_dir / CHECKPOINT_DIRECTORY / CHECKPOINT_MANIFEST
                ),
            }
        except Exception as error:
            checkpoint_error = {
                "status": "RECOVERY_CHECKPOINT_EXPORT_FAILED",
                "error_type": type(error).__name__,
                "error": str(error),
            }
            (output_dir / "barrier_checkpoint_error.json").write_text(
                json.dumps(checkpoint_error, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report["barrier_checkpoint"] = checkpoint_error
    export_state = False
    state_export_requested = False
    qc = None
    solver_solution_accepted = bool(
        report["status"] == "OPTIMAL"
        and report.get("solution_contract", {}).get(
            "acceptance_status"
        ) == "PASS"
    )
    if (
        artifacts.model.SolCount
        and solver_solution_accepted
        and not args.engineering_barrier_checkpoint_only
    ):
        export_master_solution(artifacts, data, output_dir)
        qc = export_operational_solution(artifacts, data, config, output_dir)
        export_result_summary(artifacts, data, config, output_dir)
        state_export_requested = bool(
            (not test_only or args.export_diagnostic_state)
            and report["status"] == "OPTIMAL"
            and report.get("solution_contract", {}).get(
                "acceptance_status"
            ) == "PASS"
            and qc["status"] == "PASS"
            and mga_request is None
        )
        export_state = bool(
            state_export_requested
            and not nonbasic_primal_dual_requested
            and (
                not args.primal_dual_checkpoint_in
                or args.allow_deferred_crossover_planning_state
            )
        )
        if nonbasic_primal_dual_requested and not (
            args.allow_nonbasic_planning_state
        ):
            report["planning_state_export_status"] = (
                "NOT_REQUESTED_NONBASIC_STATE_REQUIRES_EXPLICIT_SEQUENCE_POLICY"
            )
        elif nonbasic_primal_dual_requested and state_export_requested:
            report["planning_state_export_status"] = (
                "PENDING_ACCEPTED_BARRIER_CHECKPOINT"
            )
        if (
            args.primal_dual_checkpoint_in
            and state_export_requested
            and not args.allow_deferred_crossover_planning_state
        ):
            report["planning_state_export_status"] = (
                "NOT_EXPORTED_POSTHOC_CROSSOVER_ANALYSIS_DERIVATIVE"
            )
        elif (
            args.primal_dual_checkpoint_in
            and state_export_requested
            and args.allow_deferred_crossover_planning_state
        ):
            report["planning_state_export_status"] = (
                "ACCEPTED_STAGE_B_BASIC_CAPACITY_STATE"
            )
        if mga_request is not None:
            report["solver_secondary_objective_value_gw"] = report[
                "objective_value_million_cny"
            ]
            report["objective_value_million_cny"] = qc["objective_value_million_cny"]
            report["mga"] = qc["mga"]
            (output_dir / "mga_run.json").write_text(
                json.dumps(qc["mga"], ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        report["solution_qc_status"] = qc["status"]
        report["solution_qc_path"] = str(output_dir / "solution_qc.json")
        report["solution_export_status"] = "COMPLETE"
    elif artifacts.model.SolCount and args.engineering_barrier_checkpoint_only:
        report["solution_export_status"] = (
            "SKIPPED_ENGINEERING_BARRIER_CHECKPOINT_ONLY"
        )
    elif artifacts.model.SolCount:
        report["solution_export_status"] = (
            "SKIPPED_UNACCEPTED_SOLVER_RESULT"
        )
    primary_checkpoint_requested = bool(
        nonbasic_primal_dual_requested
        and not args.engineering_barrier_checkpoint_only
        and (args.export_barrier_checkpoint or optimization_hours > 744)
    )
    if primary_checkpoint_requested and qc is not None and qc.get("status") == "PASS":
        try:
            from cispo_model.primal_dual_checkpoint import (
                CHECKPOINT_DIRECTORY,
                CHECKPOINT_MANIFEST,
                export_barrier_primal_dual_checkpoint,
            )

            checkpoint = export_barrier_primal_dual_checkpoint(
                artifacts.model,
                config,
                output_dir,
                solve_report=report,
                optimization_hours=optimization_hours,
                optimization_start_hour=optimization_start_hour,
                result_use=scope_report["result_use"],
                solution_qc=qc,
                accepted_primary=True,
            )
            report["barrier_checkpoint"] = {
                "status": checkpoint["checkpoint_status"],
                "scientifically_accepted": True,
                "deferred_crossover_eligible": True,
                "path": str(
                    output_dir / CHECKPOINT_DIRECTORY / CHECKPOINT_MANIFEST
                ),
            }
        except Exception as error:
            checkpoint_error = {
                "status": "PRIMARY_CHECKPOINT_EXPORT_FAILED",
                "error_type": type(error).__name__,
                "error": str(error),
                "scientific_solution_remains_eligible_for_normal_acceptance": True,
            }
            (output_dir / "barrier_checkpoint_error.json").write_text(
                json.dumps(checkpoint_error, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report["barrier_checkpoint"] = checkpoint_error
    if (
        state_export_requested
        and nonbasic_primal_dual_requested
        and args.allow_nonbasic_planning_state
    ):
        checkpoint_status = report.get("barrier_checkpoint", {}).get("status")
        export_state = bool(
            checkpoint_status == "ACCEPTED_PRIMARY_BARRIER_SOLUTION"
        )
        report["planning_state_export_status"] = (
            "ACCEPTED_NONBASIC_BARRIER_CAPACITY_STATE"
            if export_state
            else "BLOCKED_MISSING_ACCEPTED_BARRIER_CHECKPOINT"
        )
    if export_state:
        report["planning_state_path"] = str(output_dir / "planning_state")
    report["runtime_memory"] = memory_monitor.stop()
    if (
        args.export_warm_start_basis
        and qc is not None
        and report["status"] == "OPTIMAL"
        and qc["status"] == "PASS"
    ):
        from cispo_model.basis_reuse import export_warm_start_basis

        report["warm_start_basis"] = export_warm_start_basis(
            artifacts.model,
            config,
            output_dir,
            solve_report=report,
            solution_qc=qc,
            optimization_hours=optimization_hours,
            optimization_start_hour=optimization_start_hour,
            result_use=scope_report["result_use"],
        )
    if (
        args.export_scientific_solver_artifacts
        and qc is not None
        and report["status"] == "OPTIMAL"
        and qc["status"] == "PASS"
    ):
        from cispo_model.solver_artifacts import (
            export_scientific_base_solver_artifacts,
        )

        report["scientific_solver_artifacts"] = (
            export_scientific_base_solver_artifacts(
                artifacts.model,
                config,
                output_dir,
                solve_report=report,
                solution_qc=qc,
                result_use=scope_report["result_use"],
            )
        )
    if qc is not None:
        report["result_manifest_path"] = str(output_dir / "result_manifest.json")
    (output_dir / "solve_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if structure_audit is not None:
        from cispo_model.solver_audit import parse_gurobi_log

        structure_audit["solver_log_global"] = parse_gurobi_log(
            (output_dir / "gurobi.log").read_text(
                encoding="utf-8", errors="replace"
            )
        )
        structure_audit["solve_summary"] = {
            "status": report.get("status"),
            "runtime_seconds": report.get("runtime_seconds"),
            "objective_value_million_cny": report.get("objective_value_million_cny"),
            "peak_process_tree_rss_gib": report.get("runtime_memory", {}).get(
                "peak_process_tree_rss_gib"
            ),
        }
        structure_audit_path.write_text(
            json.dumps(structure_audit, ensure_ascii=False, indent=2) + "\n",
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
    manifest_valid = False
    if qc is not None:
        build_result_dashboard(output_dir)
        write_output_catalog(output_dir)
        finalize_result_manifest(output_dir, config)
        manifest_valid, _ = validate_result_manifest(output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.engineering_barrier_checkpoint_only:
        if engineering_checkpoint_completed:
            return
        raise SystemExit(2)
    if not solver_result_is_accepted(
        report,
        qc,
        result_manifest_valid=manifest_valid,
    ):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
