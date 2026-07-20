"""Run 2030/2040/2050/2060 as isolated sequential full-year processes."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cispo_model.config import load_model_config
from cispo_model.io_contract import validate_result_manifest
from cispo_model.planning_state import PlanningState
from cispo_model.result_summary import _svg_lines


def accepted(output_dir: Path, *, require_state: bool = True) -> bool:
    solve_path = output_dir / "solve_report.json"
    qc_path = output_dir / "solution_qc.json"
    state_path = output_dir / "planning_state" / "state_metadata.json"
    if not solve_path.is_file() or not qc_path.is_file():
        return False
    solve = json.loads(solve_path.read_text(encoding="utf-8"))
    qc = json.loads(qc_path.read_text(encoding="utf-8"))
    accepted_core = bool(
        solve.get("status") == "OPTIMAL"
        and solve.get("result_use") == "SCIENTIFIC_PRODUCTION"
        and qc.get("status") == "PASS"
        and (state_path.is_file() or not require_state)
    )
    if not accepted_core:
        return False
    manifest_ok, _ = validate_result_manifest(output_dir)
    if not manifest_ok:
        return False
    if require_state:
        try:
            PlanningState.load(
                output_dir / "planning_state",
                expected_boundary_year=int(solve["planning_year"]),
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
    parser.add_argument("--output-root", default="outputs/planning_sequence")
    parser.add_argument("--start-year", type=int, default=2030)
    parser.add_argument("--end-year", type=int, default=2060)
    parser.add_argument(
        "--state-in",
        help="Required only when starting after 2030; state from the prior configured year.",
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = load_model_config(args.config)
    years = [
        year
        for year in config.planning_years
        if args.start_year <= year <= args.end_year
    ]
    if not years or years[0] != args.start_year or years[-1] != args.end_year:
        raise SystemExit("start/end years must select a contiguous configured planning range")
    if years[0] != config.planning_years[0] and not args.state_in:
        raise SystemExit("--state-in is required when the sequence starts after 2030")

    output_root = Path(args.output_root)
    if not output_root.is_absolute():
        output_root = PROJECT_ROOT / output_root
    output_root.mkdir(parents=True, exist_ok=True)
    prior_state = Path(args.state_in).resolve() if args.state_in else None
    sequence_report = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "years": years,
        "status": "RUNNING",
        "runs": [],
    }

    for year in years:
        output_dir = output_root / str(year)
        if args.resume and accepted(output_dir):
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
            "--horizon",
            "full_year",
            "--output-dir",
            str(output_dir),
        ]
        if prior_state is not None:
            command.extend(["--state-in", str(prior_state)])
        run_record = {
            "planning_year": year,
            "command": command,
            "output_dir": str(output_dir),
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
        output_dir.mkdir(parents=True, exist_ok=True)
        with (output_dir / "sequence_stdout.log").open("w", encoding="utf-8") as stdout, (
            output_dir / "sequence_stderr.log"
        ).open("w", encoding="utf-8") as stderr:
            completed = subprocess.run(command, cwd=PROJECT_ROOT, stdout=stdout, stderr=stderr)
        run_record["return_code"] = completed.returncode
        run_record["status"] = "ACCEPTED" if accepted(output_dir) else "HARD_FAIL"
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
