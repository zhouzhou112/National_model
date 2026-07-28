"""Evaluate non-LP BECCS lifecycle screening cases for a closed result.

This script deliberately holds the solved generation, capture and physical
storage fixed.  It is a post-solve accounting screen, not an alternative
optimization case and not a replacement for sourced lifecycle coefficients in
the scientific LP.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cispo_model.carbon_accounting import (
    evaluate_postsolve_beccs_lifecycle_sensitivity,
)
from cispo_model.io_contract import sha256_file, validate_result_manifest


def load_spec(path: Path) -> tuple[dict[str, float], dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("contract_version") != "beccs_lifecycle_postsolve_sensitivity_v1":
        raise ValueError("Unsupported BECCS lifecycle sensitivity contract")
    reference = payload.get("reference_case", {})
    if float(reference.get("lifecycle_share_of_stored_biogenic_co2", float("nan"))) != 0.0:
        raise ValueError("CISPO-equivalent reference lifecycle burden must remain zero")
    cases = {str(reference.get("id", "")): 0.0}
    for row in payload.get("screening_cases", []):
        case_id = str(row.get("id", ""))
        if not case_id or case_id in cases:
            raise ValueError("BECCS lifecycle sensitivity case IDs must be unique")
        cases[case_id] = float(row["lifecycle_share_of_stored_biogenic_co2"])
    if {"low", "base", "high"}.difference(cases):
        raise ValueError("BECCS lifecycle sensitivity requires low/base/high screening cases")
    return cases, payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-dir", required=True, type=Path)
    parser.add_argument(
        "--spec",
        type=Path,
        default=PROJECT_ROOT / "config" / "beccs_lifecycle_sensitivity_v1.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Sibling output root; source result artifacts are never modified.",
    )
    args = parser.parse_args()
    result_dir = args.result_dir.resolve()
    valid, issues = validate_result_manifest(result_dir)
    if not valid:
        raise SystemExit("Closed source result manifest required: " + "; ".join(issues))
    source = result_dir / "annual_resource_accounting_by_province.csv"
    if not source.is_file():
        raise SystemExit(f"Missing source accounting table: {source}")
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir is not None
        else result_dir.parent / f"{result_dir.name}_beccs_lifecycle_sensitivity_v1"
    )
    if output_dir == result_dir or result_dir in output_dir.parents:
        raise SystemExit("BECCS lifecycle sensitivity output must be outside the source result root")
    output_dir.mkdir(parents=True, exist_ok=False)

    cases, spec = load_spec(args.spec.resolve())
    detailed = evaluate_postsolve_beccs_lifecycle_sensitivity(
        pd.read_csv(source), cases
    )
    summary = (
        detailed.groupby("case_id", as_index=False)
        .agg(
            lifecycle_share_of_stored_biogenic_co2=(
                "lifecycle_share_of_stored_biogenic_co2", "first"
            ),
            stored_biogenic_co2_mtco2=("beccs_stored_co2_mtco2", "sum"),
            assumed_lifecycle_emissions_mtco2=(
                "assumed_lifecycle_emissions_mtco2", "sum"
            ),
            adjusted_beccs_net_removal_mtco2=(
                "adjusted_beccs_net_removal_mtco2", "sum"
            ),
            adjusted_net_emissions_after_dac_mtco2=(
                "adjusted_net_emissions_after_dac_mtco2", "sum"
            ),
        )
        .sort_values("lifecycle_share_of_stored_biogenic_co2")
    )
    detailed.to_csv(
        output_dir / "beccs_lifecycle_sensitivity_by_province.csv",
        index=False,
        encoding="utf-8-sig",
    )
    summary.to_csv(
        output_dir / "beccs_lifecycle_sensitivity_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )
    manifest = {
        "schema_version": "beccs_lifecycle_postsolve_sensitivity_result_v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "source_result_dir": str(result_dir),
        "source_result_manifest_sha256": sha256_file(result_dir / "result_manifest.json"),
        "source_accounting_sha256": sha256_file(source),
        "spec_path": str(args.spec.resolve()),
        "spec_sha256": sha256_file(args.spec.resolve()),
        "cases": cases,
        "scope": spec["scope"],
        "interpretation_limit": spec["interpretation_limit"],
        "files": [
            "beccs_lifecycle_sensitivity_by_province.csv",
            "beccs_lifecycle_sensitivity_summary.csv",
        ],
    }
    (output_dir / "beccs_lifecycle_sensitivity_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output_dir": str(output_dir), "cases": cases}, ensure_ascii=False))


if __name__ == "__main__":
    main()
