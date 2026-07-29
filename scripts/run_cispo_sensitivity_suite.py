"""Run a versioned diagnostic suite from the checked-in scenario catalog.

This wrapper only orchestrates the existing sequential driver. It does not
change model parameters, share planning states across scenarios, or authorize
full-year production runs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cispo_model.config import load_model_config


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_project_path(path: str | Path) -> Path:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = PROJECT_ROOT / resolved
    return resolved.resolve()


def load_scenario_catalog(path: str | Path) -> dict[str, Any]:
    catalog_path = resolve_project_path(path)
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    if payload.get("catalog_version") not in {"v1", "v2", "v3"}:
        raise ValueError(
            "Scenario catalog must declare catalog_version=v1, v2 or v3"
        )

    implemented = payload.get("implemented")
    planned = payload.get("planned_not_runnable")
    if not isinstance(implemented, list) or not isinstance(planned, list):
        raise ValueError(
            "Scenario catalog requires implemented and planned_not_runnable lists"
        )

    seen: set[str] = set()
    normalized_implemented: list[dict[str, Any]] = []
    for row in implemented:
        scenario_id = str(row.get("scenario_id", "")).strip()
        config_value = row.get("config")
        if not scenario_id or not config_value:
            raise ValueError("Every implemented scenario requires scenario_id and config")
        if scenario_id in seen:
            raise ValueError(f"Duplicate scenario_id in catalog: {scenario_id}")
        seen.add(scenario_id)
        config_path = resolve_project_path(str(config_value))
        if not config_path.is_file():
            raise ValueError(f"Scenario config is missing: {config_path}")
        scenario_payload = json.loads(config_path.read_text(encoding="utf-8"))
        if scenario_payload.get("scenario_override_version") != "v1":
            raise ValueError(
                f"Scenario {scenario_id} must declare scenario_override_version=v1"
            )
        if str(scenario_payload.get("scenario_id")) != scenario_id:
            raise ValueError(
                f"Catalog/config scenario_id mismatch for {scenario_id}: "
                f"{scenario_payload.get('scenario_id')}"
            )
        load_model_config(scenario_path=config_path)
        normalized_implemented.append(
            {
                **row,
                "scenario_id": scenario_id,
                "config_path": config_path,
                "config_sha256": sha256_file(config_path),
                "scenario_family": scenario_payload.get("scenario_family"),
                "description": scenario_payload.get("description"),
                "evidence_status": scenario_payload.get("evidence_status"),
                "analysis_role": scenario_payload.get("analysis_role"),
                "publication_status": scenario_payload.get(
                    "publication_status"
                ),
            }
        )

    normalized_planned: list[dict[str, Any]] = []
    for row in planned:
        scenario_id = str(row.get("scenario_id", "")).strip()
        reason = str(row.get("reason", "")).strip()
        if not scenario_id or not reason:
            raise ValueError(
                "Every planned_not_runnable scenario requires scenario_id and reason"
            )
        if scenario_id in seen:
            raise ValueError(f"Duplicate scenario_id in catalog: {scenario_id}")
        seen.add(scenario_id)
        normalized_planned.append(
            {"scenario_id": scenario_id, "reason": reason}
        )

    return {
        "catalog_path": catalog_path,
        "catalog_sha256": sha256_file(catalog_path),
        "implemented": normalized_implemented,
        "planned_not_runnable": normalized_planned,
    }


def select_scenarios(
    catalog: dict[str, Any], requested: list[str] | None
) -> list[dict[str, Any]]:
    implemented = {row["scenario_id"]: row for row in catalog["implemented"]}
    planned = {
        row["scenario_id"]: row["reason"]
        for row in catalog["planned_not_runnable"]
    }
    if not requested:
        return [
            row
            for row in catalog["implemented"]
            if row.get("analysis_role")
            in {"BASELINE", "CENTRAL_COUNTERFACTUAL"}
        ]

    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for scenario_id in requested:
        if scenario_id in seen:
            raise ValueError(f"Scenario selected more than once: {scenario_id}")
        seen.add(scenario_id)
        if scenario_id in planned:
            raise ValueError(
                f"Scenario {scenario_id} is planned_not_runnable: {planned[scenario_id]}"
            )
        if scenario_id not in implemented:
            raise ValueError(f"Scenario is not present in the catalog: {scenario_id}")
        selected.append(implemented[scenario_id])
    return selected


def write_suite_report(output_root: Path, report: dict[str, Any]) -> None:
    (output_root / "sensitivity_suite_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    rows = []
    for run in report.get("runs", []):
        rows.append(
            {
                "scenario_id": run["scenario_id"],
                "scenario_family": run.get("scenario_family"),
                "evidence_status": run.get("evidence_status"),
                "scenario_config": run["scenario_config"],
                "scenario_config_sha256": run["scenario_config_sha256"],
                "output_root": run["output_root"],
                "status": run.get("status"),
                "return_code": run.get("return_code"),
                "sequence_status": run.get("sequence_status"),
            }
        )
    with (output_root / "sensitivity_suite_index.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "scenario_id",
                "scenario_family",
                "evidence_status",
                "scenario_config",
                "scenario_config_sha256",
                "output_root",
                "status",
                "return_code",
                "sequence_status",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run independent diagnostic planning chains from the checked-in "
            "scenario catalog"
        )
    )
    parser.add_argument(
        "--catalog", default="config/scenarios/scenario_catalog.json"
    )
    parser.add_argument("--config", default="config/optimization_2030.json")
    parser.add_argument(
        "--scenario",
        action="append",
        help="Implemented scenario_id to run; repeat as needed. Defaults to all implemented.",
    )
    parser.add_argument(
        "--output-root",
        help="Required versioned suite root; each scenario receives an isolated child root.",
    )
    parser.add_argument(
        "--diagnostic-hours",
        type=int,
        help="Required leading-hour diagnostic horizon in [1, 8759].",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--list-scenarios", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        catalog = load_scenario_catalog(args.catalog)
        selected = select_scenarios(catalog, args.scenario)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

    if args.list_scenarios:
        print(
            json.dumps(
                {
                    "implemented": [
                        {
                            "scenario_id": row["scenario_id"],
                            "scenario_family": row.get("scenario_family"),
                            "evidence_status": row.get("evidence_status"),
                            "config": str(row["config_path"]),
                            "sha256": row["config_sha256"],
                        }
                        for row in catalog["implemented"]
                    ],
                    "planned_not_runnable": catalog["planned_not_runnable"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.output_root is None:
        raise SystemExit("--output-root is required unless --list-scenarios is used")
    if args.diagnostic_hours is None or not 1 <= args.diagnostic_hours < 8760:
        raise SystemExit("--diagnostic-hours must be in [1, 8759]")
    if args.dry_run and args.resume:
        raise SystemExit("--dry-run and --resume are mutually exclusive")

    base_config_path = resolve_project_path(args.config)
    if not base_config_path.is_file():
        raise SystemExit(f"Base config is missing: {base_config_path}")
    try:
        for scenario in selected:
            load_model_config(base_config_path, scenario["config_path"])
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"Scenario/base config validation failed: {exc}") from exc

    output_root = resolve_project_path(args.output_root)
    resume_source_report: dict[str, str] | None = None
    existing_nonempty = output_root.exists() and any(output_root.iterdir())
    if existing_nonempty:
        if not args.resume:
            raise SystemExit(
                f"Refusing to overwrite non-empty suite root {output_root}; "
                "choose a new versioned root or use --resume for accepted chains"
            )
        existing_report_path = output_root / "sensitivity_suite_report.json"
        try:
            existing_report = json.loads(
                existing_report_path.read_text(encoding="utf-8")
            )
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
            raise SystemExit(
                f"Cannot resume suite without a readable identity report: "
                f"{existing_report_path}"
            ) from exc
        expected_scenario_ids = [row["scenario_id"] for row in selected]
        expected_scenario_hashes = {
            row["scenario_id"]: row["config_sha256"] for row in selected
        }
        existing_scenario_hashes = {
            row.get("scenario_id"): row.get("scenario_config_sha256")
            for row in existing_report.get("runs", [])
        }
        resume_mismatches = []
        if existing_report.get("mode") != "DIAGNOSTIC_EXECUTION":
            resume_mismatches.append("mode")
        if existing_report.get("diagnostic_hours") != args.diagnostic_hours:
            resume_mismatches.append("diagnostic_hours")
        if existing_report.get("catalog_sha256") != catalog["catalog_sha256"]:
            resume_mismatches.append("catalog_sha256")
        if existing_report.get("base_config_sha256") != sha256_file(base_config_path):
            resume_mismatches.append("base_config_sha256")
        if existing_report.get("scenario_ids") != expected_scenario_ids:
            resume_mismatches.append("scenario_ids")
        if existing_scenario_hashes != expected_scenario_hashes:
            resume_mismatches.append("scenario_config_sha256")
        if resume_mismatches:
            raise SystemExit(
                "Refusing mixed-identity suite resume; mismatched fields: "
                + ", ".join(resume_mismatches)
            )
        history_dir = output_root / "sensitivity_suite_history"
        history_dir.mkdir(parents=True, exist_ok=True)
        history_stamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
        history_path = history_dir / f"sensitivity_suite_report_{history_stamp}.json"
        history_path.write_text(
            json.dumps(existing_report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        resume_source_report = {
            "path": str(history_path),
            "sha256": sha256_file(history_path),
        }
    output_root.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now().astimezone()
    run_tag = generated_at.strftime("%Y%m%dT%H%M%S%z")
    report: dict[str, Any] = {
        "generated_at": generated_at.isoformat(),
        "run_tag": run_tag,
        "status": "RUNNING",
        "mode": "DRY_RUN" if args.dry_run else "DIAGNOSTIC_EXECUTION",
        "diagnostic_hours": args.diagnostic_hours,
        "catalog_path": str(catalog["catalog_path"]),
        "catalog_sha256": catalog["catalog_sha256"],
        "base_config": str(base_config_path),
        "base_config_sha256": sha256_file(base_config_path),
        "scenario_ids": [row["scenario_id"] for row in selected],
        "state_isolation": "one independent planning-state chain per scenario",
        "full_year_authorization": "not supported by this diagnostic suite wrapper",
        "resume_source_report": resume_source_report,
        "runs": [],
    }
    write_suite_report(output_root, report)

    sequence_script = PROJECT_ROOT / "scripts" / "run_cispo_planning_sequence.py"
    for scenario in selected:
        scenario_id = scenario["scenario_id"]
        scenario_output = output_root / scenario_id
        command = [
            sys.executable,
            str(sequence_script),
            "--config",
            str(base_config_path),
            "--scenario-config",
            str(scenario["config_path"]),
            "--diagnostic-hours",
            str(args.diagnostic_hours),
            "--output-root",
            str(scenario_output),
        ]
        if args.dry_run:
            command.append("--dry-run")
        if args.resume:
            command.append("--resume")
        run: dict[str, Any] = {
            "scenario_id": scenario_id,
            "scenario_family": scenario.get("scenario_family"),
            "description": scenario.get("description"),
            "evidence_status": scenario.get("evidence_status"),
            "scenario_config": str(scenario["config_path"]),
            "scenario_config_sha256": scenario["config_sha256"],
            "output_root": str(scenario_output),
            "command": command,
            "started_at": datetime.now().astimezone().isoformat(),
            "status": "RUNNING",
        }
        stdout_path = output_root / f"{scenario_id}.{run_tag}.stdout.log"
        stderr_path = output_root / f"{scenario_id}.{run_tag}.stderr.log"
        run["stdout_log"] = str(stdout_path)
        run["stderr_log"] = str(stderr_path)
        report["runs"].append(run)
        write_suite_report(output_root, report)
        with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open(
            "w", encoding="utf-8"
        ) as stderr:
            completed = subprocess.run(
                command, cwd=PROJECT_ROOT, stdout=stdout, stderr=stderr
            )
        run["return_code"] = completed.returncode
        run["completed_at"] = datetime.now().astimezone().isoformat()
        sequence_path = scenario_output / "sequence_report.json"
        sequence_report = None
        if sequence_path.is_file():
            try:
                sequence_report = json.loads(sequence_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError, OSError):
                sequence_report = None
        run["sequence_status"] = (
            sequence_report.get("status") if sequence_report else None
        )
        run["sequence_scenario_id"] = (
            sequence_report.get("scenario_id") if sequence_report else None
        )
        expected_status = "DRY_RUN" if args.dry_run else "PASS"
        accepted = bool(
            completed.returncode == 0
            and sequence_report is not None
            and sequence_report.get("status") == expected_status
            and sequence_report.get("scenario_id") == scenario_id
            and sequence_report.get("diagnostic_hours") == args.diagnostic_hours
        )
        run["status"] = expected_status if accepted else "HARD_FAIL"
        if not accepted:
            report["status"] = "HARD_FAIL"
            report["completed_at"] = datetime.now().astimezone().isoformat()
            write_suite_report(output_root, report)
            raise SystemExit(
                f"Sensitivity suite stopped at {scenario_id}; inspect {stderr_path}"
            )

    report["status"] = "DRY_RUN" if args.dry_run else "PASS"
    report["completed_at"] = datetime.now().astimezone().isoformat()
    write_suite_report(output_root, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
