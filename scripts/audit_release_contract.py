"""Audit the active inherited National_model code/data release contract."""
from __future__ import annotations

import argparse
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

from cispo_model.config import load_model_config  # noqa: E402
from scripts.run_cispo_sensitivity_suite import load_scenario_catalog  # noqa: E402
from scripts.validate_provincial_aggregate_hydro_inputs import (  # noqa: E402
    build_audit as build_hydro_audit,
)


DEFAULT_CONTRACT = (
    PROJECT_ROOT / "config" / "release_contract_v0805_power_curve_v3_qc.json"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _nested(payload: dict[str, Any], dotted: str) -> Any:
    value: Any = payload
    for key in dotted.split("."):
        value = value[key]
    return value


def _load_contract(path: Path) -> dict[str, Any]:
    contract = json.loads(path.read_text(encoding="utf-8"))
    inherited = contract.get("inherits")
    if not inherited:
        return contract
    inherited_path = Path(str(inherited))
    if not inherited_path.is_absolute():
        inherited_path = PROJECT_ROOT / inherited_path
    parent = _load_contract(inherited_path.resolve())
    merged = dict(parent)
    for key, value in contract.items():
        if key not in {"inherits", "external_data_files_additional"}:
            merged[key] = value
    external_by_path = {
        row["path"]: row for row in parent.get("external_data_files", [])
    }
    external_by_path.update(
        {
            row["path"]: row
            for row in contract.get("external_data_files_additional", [])
        }
    )
    merged["external_data_files"] = list(external_by_path.values())
    merged["inherits"] = str(inherited)
    return merged


def _check(
    checks: list[dict[str, Any]],
    name: str,
    passed: bool,
    value: Any,
    expected: Any,
) -> None:
    checks.append(
        {
            "check": name,
            "status": "PASS" if passed else "HARD_FAIL",
            "value": value,
            "expected": expected,
        }
    )


def build_audit(
    data_root: Path,
    contract_path: Path = DEFAULT_CONTRACT,
    require_clean_git: bool = False,
) -> dict[str, Any]:
    contract = _load_contract(contract_path)
    checks: list[dict[str, Any]] = []
    base = load_model_config().raw
    for dotted, expected in contract["base_expectations"].items():
        actual = _nested(base, dotted)
        _check(checks, f"base:{dotted}", actual == expected, actual, expected)

    solver_contract = contract["production_solver_profile"]
    solver_path = PROJECT_ROOT / solver_contract["path"]
    solver = json.loads(solver_path.read_text(encoding="utf-8"))
    for dotted, expected in solver_contract.items():
        if dotted == "path":
            continue
        actual = _nested(solver, dotted)
        _check(checks, f"solver:{dotted}", actual == expected, actual, expected)

    catalog = load_scenario_catalog(
        PROJECT_ROOT / "config" / "scenarios" / "scenario_catalog.json"
    )
    scenario_ids = [row["scenario_id"] for row in catalog["implemented"]]
    expected_ids = contract["implemented_scenarios"]
    _check(
        checks,
        "scenario_catalog_exact_membership",
        scenario_ids == expected_ids,
        scenario_ids,
        expected_ids,
    )
    if "primary_scenarios" in contract:
        primary_ids = [
            row["scenario_id"] for row in catalog["primary_analysis"]
        ]
        _check(
            checks,
            "scenario_catalog_primary_membership",
            primary_ids == contract["primary_scenarios"],
            primary_ids,
            contract["primary_scenarios"],
        )
    _check(
        checks,
        "base_exclusions_not_overlaid_on_base",
        not base["features"]["flexible_load"]
        and base["hydro"]["provincial_aggregate_up_reserve_credit"] == 0.0
        and base["storage_design"]["phs_energy_capacity_mode"]
        == "fixed_duration_v1"
        and solver["numerics"]["crossover"] == 1,
        contract["base_exclusions"],
        "all excluded from Base",
    )

    external_files: list[dict[str, Any]] = []
    for row in contract["external_data_files"]:
        path = data_root / row["path"]
        actual = _sha256(path) if path.is_file() else None
        _check(
            checks,
            f"external_data_sha256:{row['path']}",
            actual == row["sha256"],
            actual,
            row["sha256"],
        )
        external_files.append(
            {
                "path": str(path.resolve()),
                "exists": path.is_file(),
                "sha256": actual,
                "bytes": path.stat().st_size if path.is_file() else None,
            }
        )

    hydro_audit = build_hydro_audit(data_root)
    _check(
        checks,
        "provincial_aggregate_hydro_input_audit",
        hydro_audit["status"] == "PASS",
        hydro_audit["status"],
        "PASS",
    )

    git_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    git_status = subprocess.run(
        ["git", "status", "--short", "--untracked-files=no"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if require_clean_git:
        _check(checks, "git_tracked_worktree_clean", not git_status, git_status, "")

    failures = [
        row["check"] for row in checks if row["status"] == "HARD_FAIL"
    ]
    return {
        "schema_version": "national_model_release_contract_audit_v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": "PASS" if not failures else "FAIL",
        "contract_path": str(contract_path.resolve()),
        "contract_sha256": _sha256(contract_path),
        "data_root": str(data_root.resolve()),
        "git_head": git_head,
        "git_tracked_worktree_clean": not git_status,
        "git_status": git_status,
        "scenario_catalog": catalog,
        "external_files": external_files,
        "hydro_audit": hydro_audit,
        "checks": checks,
        "failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", default=str(PROJECT_ROOT / "data"))
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    parser.add_argument("--output", required=True)
    parser.add_argument("--require-clean-git", action="store_true")
    args = parser.parse_args()
    report = build_audit(
        Path(args.data_root),
        Path(args.contract),
        require_clean_git=args.require_clean_git,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(json.dumps({"status": report["status"], "failures": report["failures"]}))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
