"""Run 2030/2040/2050/2060 as isolated sequential full-year processes."""
from __future__ import annotations

import argparse
import atexit
import json
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cispo_model.config import load_model_config
from cispo_model.data import DATA_ROOT
from cispo_model.io_contract import validate_result_manifest
from cispo_model.planning_state import PlanningState
from cispo_model.result_summary import _svg_lines
from cispo_model.run_contract import (
    SEQUENCE_ACTIVE_CLAIM_FILENAME,
    SEQUENCE_CLAIM_HISTORY_DIRNAME,
    capture_input_identity,
    claim_sequence_directory,
    output_matches_configuration,
    release_sequence_directory,
    sequence_identity,
    solver_result_is_accepted,
)


def uses_nonbasic_barrier_primary(config) -> bool:
    """Return whether the sequence profile requests the strict Barrier-only route."""
    numerics = config.raw["numerics"]
    return bool(
        int(numerics.get("method", -1)) == 2
        and int(numerics.get("crossover", -1)) == 0
        and int(numerics.get("solution_target", -1)) == 1
    )


def _predecessor_matches_manifest(output_dir: Path, expected_state_in: Path) -> bool:
    try:
        manifest = pd.read_csv(output_dir / "input_manifest.csv")
    except (FileNotFoundError, pd.errors.EmptyDataError, UnicodeDecodeError):
        return False
    expected_root = expected_state_in.resolve()
    required = {
        "state_metadata.json": expected_root / "state_metadata.json",
        "capacity_cohorts.csv.gz": expected_root / "capacity_cohorts.csv.gz",
        "state_transition_summary.csv": expected_root / "state_transition_summary.csv",
        "../result_manifest.json": expected_root.parent / "result_manifest.json",
    }
    for logical_path, current_path in required.items():
        selected = manifest.loc[
            manifest.kind.eq("planning_state")
            & manifest.logical_path.eq(logical_path)
        ]
        if len(selected) != 1 or not current_path.is_file():
            return False
        row = selected.iloc[0]
        if Path(str(row.resolved_path)).resolve() != current_path.resolve():
            return False
        from cispo_model.io_contract import sha256_file

        if str(row.sha256) != sha256_file(current_path):
            return False
    return True


def accepted(
    output_dir: Path,
    *,
    require_state: bool = True,
    expected_result_use: str = "SCIENTIFIC_PRODUCTION",
    expected_state_in: Path | None = None,
    expected_run_id: str | None = None,
    expected_scenario_id: str | None = None,
    expected_planning_year: int | None = None,
    expected_optimization_start_hour: int | None = None,
    expected_config=None,
) -> bool:
    solve_path = output_dir / "solve_report.json"
    qc_path = output_dir / "solution_qc.json"
    state_path = output_dir / "planning_state" / "state_metadata.json"
    if not solve_path.is_file() or not qc_path.is_file():
        return False
    try:
        solve = json.loads(solve_path.read_text(encoding="utf-8"))
        qc = json.loads(qc_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return False
    manifest_ok, _ = validate_result_manifest(output_dir)
    accepted_core = bool(
        solver_result_is_accepted(
            solve,
            qc,
            result_manifest_valid=manifest_ok,
        )
        and solve.get("result_use") == expected_result_use
        and (state_path.is_file() or not require_state)
    )
    if not accepted_core:
        return False
    if expected_planning_year is not None and int(
        solve.get("planning_year", -1)
    ) != int(expected_planning_year):
        return False
    if expected_optimization_start_hour is not None and int(
        solve.get("optimization_start_hour", -1)
    ) != int(expected_optimization_start_hour):
        return False
    if expected_config is not None and not output_matches_configuration(
        output_dir,
        expected_config,
        data_root=DATA_ROOT,
    ):
        return False
    if expected_scenario_id is not None:
        scenario_id = solve.get("scenario_id")
        if scenario_id is None:
            try:
                scope = json.loads(
                    (output_dir / "run_scope.json").read_text(encoding="utf-8")
                )
                scenario_id = scope.get("scenario_id", "base")
            except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
                scenario_id = "base"
        if str(scenario_id) != str(expected_scenario_id):
            return False
    if expected_run_id is not None:
        try:
            attempt = json.loads(
                (output_dir / "sequence_attempt.json").read_text(encoding="utf-8")
            )
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
            return False
        if attempt.get("run_id") != expected_run_id:
            return False
    if expected_state_in is not None and not _predecessor_matches_manifest(
        output_dir, expected_state_in
    ):
        return False
    if require_state:
        try:
            PlanningState.load(
                output_dir / "planning_state",
                expected_boundary_year=int(solve["planning_year"]),
                allow_test_only=expected_result_use != "SCIENTIFIC_PRODUCTION",
            )
        except (FileNotFoundError, KeyError, TypeError, ValueError):
            return False
    return True


def write_sequence_summaries(output_root: Path, years: list[int]) -> None:
    annual_rows = []
    capacities = []
    generations = []
    for year in years:
        year_dir = output_root / str(year)
        annual = json.loads((year_dir / "annual_summary.json").read_text(encoding="utf-8"))
        annual_rows.append(annual)
        capacity = pd.read_csv(year_dir / "annual_capacity_by_technology.csv")
        capacity.insert(0, "planning_year", year)
        capacities.append(capacity)
        generation = pd.read_csv(year_dir / "annual_generation_by_technology.csv")
        generation.insert(0, "planning_year", year)
        generations.append(generation)
    annual_frame = pd.DataFrame(annual_rows).sort_values("planning_year")
    capacity_frame = pd.concat(capacities, ignore_index=True)
    generation_frame = pd.concat(generations, ignore_index=True)
    annual_frame.to_csv(
        output_root / "sequence_annual_summary.csv", index=False, encoding="utf-8-sig"
    )
    capacity_frame.to_csv(
        output_root / "sequence_capacity_by_technology.csv",
        index=False,
        encoding="utf-8-sig",
    )
    generation_frame.to_csv(
        output_root / "sequence_generation_by_technology.csv",
        index=False,
        encoding="utf-8-sig",
    )

    optional_tables = {
        "annual_capacity_by_province_technology.csv": "sequence_capacity_by_province_technology.csv",
        "annual_generation_by_province_technology.csv": "sequence_generation_by_province_technology.csv",
        "annual_resource_accounting_by_province.csv": "sequence_resource_accounting_by_province.csv",
        "annual_storage_operation_by_technology.csv": "sequence_storage_operation_by_technology.csv",
        "cost_components.csv": "sequence_cost_components.csv",
        "annual_flexible_load_by_province.csv": "sequence_flexible_load_by_province.csv",
    }
    for source_name, output_name in optional_tables.items():
        frames = []
        for year in years:
            source = output_root / str(year) / source_name
            if not source.is_file():
                frames = []
                break
            frame = pd.read_csv(source)
            frame.insert(0, "planning_year", year)
            frames.append(frame)
        if frames:
            pd.concat(frames, ignore_index=True).to_csv(
                output_root / output_name,
                index=False,
                encoding="utf-8-sig",
            )

    carbon_rows = []
    for year in years:
        source = output_root / str(year) / "annual_carbon_ccs.json"
        if not source.is_file():
            carbon_rows = []
            break
        row = json.loads(source.read_text(encoding="utf-8"))
        row["planning_year"] = year
        carbon_rows.append(row)
    if carbon_rows:
        pd.DataFrame(carbon_rows).to_csv(
            output_root / "sequence_carbon_ccs.csv",
            index=False,
            encoding="utf-8-sig",
        )
    capacity_wide = (
        capacity_frame.loc[capacity_frame.unit.eq("GW")]
        .pivot_table(index="planning_year", columns="technology", values="capacity", aggfunc="sum")
        .fillna(0.0)
        .reset_index()
    )
    leading = (
        capacity_frame.groupby("technology").capacity.max().sort_values(ascending=False)
        .head(8).index.tolist()
    )
    _svg_lines(
        capacity_wide,
        [technology for technology in leading if technology in capacity_wide],
        title="Sequential CISPO installed capacity",
        path=output_root / "sequence_capacity_trajectory.svg",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the accepted CISPO planning sequence with cohort state transfer"
    )
    parser.add_argument("--config", default="config/optimization_2030.json")
    parser.add_argument(
        "--scenario-config",
        help="Optional v1 scenario override forwarded unchanged to every planning year.",
    )
    parser.add_argument(
        "--solver-config",
        help="Optional numerics-only solver profile forwarded unchanged to every year.",
    )
    parser.add_argument(
        "--formulation-config",
        help="Optional algebraically equivalent formulation profile for every year.",
    )
    parser.add_argument("--output-root", default="outputs/planning_sequence")
    parser.add_argument("--start-year", type=int, default=2030)
    parser.add_argument("--end-year", type=int, default=2060)
    parser.add_argument(
        "--state-in",
        help="Required only when starting after 2030; state from the prior configured year.",
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--recover-stale-sequence-lock",
        action="store_true",
        help=(
            "Archive and replace a stale sequence wrapper claim after verifying "
            "that its recorded local process is no longer active."
        ),
    )
    parser.add_argument(
        "--diagnostic-hours",
        type=int,
        help=(
            "Run an isolated test-only sequential solve at the given leading-hour "
            "horizon. Diagnostic states can never enter a production run."
        ),
    )
    parser.add_argument(
        "--diagnostic-start-hour",
        type=int,
        default=0,
        help=(
            "Zero-based start hour forwarded to every year of a diagnostic "
            "sequence; default 0."
        ),
    )
    args = parser.parse_args()
    if args.diagnostic_hours is not None and not 1 <= args.diagnostic_hours < 8760:
        raise SystemExit("--diagnostic-hours must be in [1, 8759]")
    if args.diagnostic_start_hour < 0:
        raise SystemExit("--diagnostic-start-hour must be non-negative")
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

    config = load_model_config(
        args.config,
        args.scenario_config,
        args.solver_config,
        args.formulation_config,
    )
    years = [
        year
        for year in config.planning_years
        if args.start_year <= year <= args.end_year
    ]
    if not years or years[0] != args.start_year or years[-1] != args.end_year:
        raise SystemExit("start/end years must select a contiguous configured planning range")
    if years[0] != config.planning_years[0] and not args.state_in:
        raise SystemExit("--state-in is required when the sequence starts after 2030")

    first_year_config = config.for_planning_year(years[0])
    initial_state = (
        PlanningState.load(
            args.state_in,
            expected_boundary_year=first_year_config.boundary_year,
            allow_test_only=args.diagnostic_hours is not None,
        )
        if args.state_in
        else PlanningState.empty(first_year_config.boundary_year)
    )
    input_identity = capture_input_identity(
        first_year_config,
        data_root=DATA_ROOT,
        planning_state=initial_state,
    )
    output_root = Path(args.output_root)
    if not output_root.is_absolute():
        output_root = PROJECT_ROOT / output_root
    try:
        sequence_claim_token = claim_sequence_directory(
            output_root,
            recover_stale=bool(args.recover_stale_sequence_lock),
        )
    except RuntimeError as error:
        raise SystemExit(f"HARD_FAIL: {error}") from error
    atexit.register(
        release_sequence_directory,
        output_root,
        sequence_claim_token,
    )
    identity = sequence_identity(
        config,
        data_root=DATA_ROOT,
        input_identity=input_identity,
        start_year=args.start_year,
        end_year=args.end_year,
        diagnostic_hours=args.diagnostic_hours,
        diagnostic_start_hour=args.diagnostic_start_hour,
    )
    identity_path = output_root / "sequence_identity.json"
    if identity_path.is_file():
        try:
            recorded_identity = json.loads(identity_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as error:
            raise SystemExit(f"Invalid sequence identity: {identity_path}") from error
        if recorded_identity != identity:
            raise SystemExit(
                "Refusing mixed-identity sequence resume; configuration, profile, "
                "formulation, scenario, or data roots changed"
            )
        if not args.resume:
            raise SystemExit(
                f"Sequence root already exists: {output_root}; use --resume only "
                "for an accepted matching chain or choose a new root"
            )
    else:
        allowed_claim_entries = {
            SEQUENCE_ACTIVE_CLAIM_FILENAME,
            SEQUENCE_CLAIM_HISTORY_DIRNAME,
        }
        if output_root.exists() and any(
            item.name not in allowed_claim_entries
            for item in output_root.iterdir()
        ):
            raise SystemExit(
                f"Refusing non-empty sequence root without identity: {output_root}"
            )
        output_root.mkdir(parents=True, exist_ok=True)
        identity_path.write_text(
            json.dumps(identity, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    prior_state = initial_state.root
    sequence_report = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "years": years,
        "status": "RUNNING",
        "result_use": (
            "TEST_ONLY_TRUNCATED_HORIZON"
            if args.diagnostic_hours is not None
            else "SCIENTIFIC_PRODUCTION"
        ),
        "diagnostic_hours": args.diagnostic_hours,
        "diagnostic_start_hour": (
            args.diagnostic_start_hour
            if args.diagnostic_hours is not None
            else None
        ),
        "scenario_id": config.raw["scenario"]["id"],
        "sequence_identity_path": str(identity_path),
        "runs": [],
    }
    expected_result_use = sequence_report["result_use"]
    nonbasic_barrier_primary = uses_nonbasic_barrier_primary(config)
    sequence_report["barrier_first_primary"] = nonbasic_barrier_primary
    sequence_report["planning_state_policy"] = (
        "ACCEPTED_OPTIMAL_NONBASIC_BARRIER_CAPACITY_STATE"
        if nonbasic_barrier_primary
        else "ACCEPTED_OPTIMAL_BASIC_OR_DEFAULT_CAPACITY_STATE"
    )

    for year in years:
        current_identity = sequence_identity(
            config,
            data_root=DATA_ROOT,
            input_identity=capture_input_identity(
                first_year_config,
                data_root=DATA_ROOT,
                planning_state=initial_state,
            ),
            start_year=args.start_year,
            end_year=args.end_year,
            diagnostic_hours=args.diagnostic_hours,
            diagnostic_start_hour=args.diagnostic_start_hour,
        )
        if current_identity != identity:
            raise SystemExit(
                "Sequence code, configuration, execution scope, initial state, "
                "or input data changed after the sequence was claimed"
            )
        output_dir = output_root / str(year)
        year_config = config.for_planning_year(year)
        if args.resume and accepted(
            output_dir,
            expected_result_use=expected_result_use,
            expected_state_in=prior_state,
            expected_scenario_id=config.raw["scenario"]["id"],
            expected_planning_year=year,
            expected_optimization_start_hour=(
                args.diagnostic_start_hour
                if args.diagnostic_hours is not None
                else 0
            ),
            expected_config=year_config,
        ):
            sequence_report["runs"].append(
                {"planning_year": year, "status": "RESUMED_ACCEPTED", "output_dir": str(output_dir)}
            )
            prior_state = output_dir / "planning_state"
            continue
        command = [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "run_cispo_2030_full_year.py"),
            "--config",
            args.config,
            "--planning-year",
            str(year),
            "--output-dir",
            str(output_dir),
        ]
        if args.scenario_config:
            command.extend(["--scenario-config", args.scenario_config])
        if args.solver_config:
            command.extend(["--solver-config", args.solver_config])
        if args.formulation_config:
            command.extend(["--formulation-config", args.formulation_config])
        if nonbasic_barrier_primary:
            command.extend(
                [
                    "--export-barrier-checkpoint",
                    "--allow-nonbasic-planning-state",
                ]
            )
        if args.diagnostic_hours is None:
            command.extend(["--horizon", "full_year"])
        else:
            command.extend(
                [
                    "--diagnostic-hours",
                    str(args.diagnostic_hours),
                    "--diagnostic-start-hour",
                    str(args.diagnostic_start_hour),
                    "--export-diagnostic-state",
                ]
            )
        if prior_state is not None:
            command.extend(["--state-in", str(prior_state)])
            if args.diagnostic_hours is not None:
                command.append("--allow-diagnostic-state-in")
        run_id = str(uuid.uuid4())
        run_record = {
            "planning_year": year,
            "run_id": run_id,
            "command": command,
            "output_dir": str(output_dir),
            "state_in": str(prior_state) if prior_state is not None else None,
        }
        sequence_report["runs"].append(run_record)
        (output_root / "sequence_report.json").write_text(
            json.dumps(sequence_report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if args.dry_run:
            run_record["status"] = "DRY_RUN"
            prior_state = output_dir / "planning_state"
            continue
        if output_dir.exists() and any(output_dir.iterdir()):
            raise SystemExit(
                f"Refusing to run into non-empty directory {output_dir}. "
                "Use --resume only for a fully accepted matching chain, or choose "
                "a new output root."
            )
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "sequence_attempt.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "planning_year": year,
                    "started_at": datetime.now().astimezone().isoformat(),
                    "expected_result_use": expected_result_use,
                    "expected_scenario_id": config.raw["scenario"]["id"],
                    "expected_optimization_start_hour": (
                        args.diagnostic_start_hour
                        if args.diagnostic_hours is not None
                        else 0
                    ),
                    "state_in": str(prior_state) if prior_state is not None else None,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        with (output_dir / "sequence_stdout.log").open("w", encoding="utf-8") as stdout, (
            output_dir / "sequence_stderr.log"
        ).open("w", encoding="utf-8") as stderr:
            completed = subprocess.run(command, cwd=PROJECT_ROOT, stdout=stdout, stderr=stderr)
        run_record["return_code"] = completed.returncode
        run_record["status"] = (
            "ACCEPTED"
            if completed.returncode == 0
            and accepted(
                output_dir,
                expected_result_use=expected_result_use,
                expected_state_in=prior_state,
                expected_run_id=run_id,
                expected_scenario_id=config.raw["scenario"]["id"],
                expected_planning_year=year,
                expected_optimization_start_hour=(
                    args.diagnostic_start_hour
                    if args.diagnostic_hours is not None
                    else 0
                ),
                expected_config=year_config,
            )
            else "HARD_FAIL"
        )
        if run_record["status"] != "ACCEPTED":
            sequence_report["status"] = "HARD_FAIL"
            (output_root / "sequence_report.json").write_text(
                json.dumps(sequence_report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            raise SystemExit(f"Sequential solve stopped at {year}; inspect {output_dir}")
        prior_state = output_dir / "planning_state"

    if args.dry_run:
        sequence_report["status"] = "DRY_RUN"
    else:
        write_sequence_summaries(output_root, years)
        sequence_report["status"] = "PASS"
    sequence_report["completed_at"] = datetime.now().astimezone().isoformat()
    (output_root / "sequence_report.json").write_text(
        json.dumps(sequence_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(sequence_report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
