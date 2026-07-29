"""Validate the province-level conventional-hydro reconciliation used by CISPO.

This is a read-only gate.  It does not rebuild or alter the source tables.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CAPACITY_RELATIVE = Path("hydro/provincial_aggregate_capacity_2025.csv")
PROFILE_RELATIVE = Path(
    "hydro/provincial_aggregate_monthly_capacity_factor_2019.csv"
)
STATIONS_RELATIVE = Path("hydro/hydro_stations.csv")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def build_audit(data_root: Path, target_gw: float = 380.0) -> dict[str, Any]:
    capacity_path = data_root / CAPACITY_RELATIVE
    profile_path = data_root / PROFILE_RELATIVE
    stations_path = data_root / STATIONS_RELATIVE
    capacity = pd.read_csv(capacity_path)
    profile = pd.read_csv(profile_path)
    stations = pd.read_csv(stations_path)
    checks: list[dict[str, Any]] = []

    province_codes = capacity.province_code.astype(int)
    _check(checks, "capacity_31_unique_provinces", len(capacity) == 31 and province_codes.is_unique, len(capacity), 31)
    _check(
        checks,
        "profile_31_provinces_x_12_months",
        len(profile) == 372
        and not profile.duplicated(["province_code", "month"]).any()
        and set(profile.province_code.astype(int)) == set(province_codes)
        and set(profile.month.astype(int)) == set(range(1, 13)),
        len(profile),
        372,
    )
    capacity_numeric = (
        "identified_station_capacity_gw",
        "harmonized_conventional_capacity_gw",
        "provincial_aggregate_capacity_gw",
        "station_technical_upper_gw",
        "harmonized_future_technical_upper_gw",
    )
    finite_nonnegative = all(
        np.isfinite(capacity[column]).all() and (capacity[column] >= 0.0).all()
        for column in capacity_numeric
    )
    _check(checks, "capacity_values_finite_nonnegative", finite_nonnegative, finite_nonnegative, True)
    profile_valid = (
        np.isfinite(profile.availability_capacity_factor).all()
        and profile.availability_capacity_factor.between(0.0, 1.0).all()
    )
    _check(checks, "monthly_profile_in_unit_interval", profile_valid, profile_valid, True)

    identified = (
        stations.groupby("province_code", as_index=False).existing_capacity_gw.sum()
        .set_index("province_code")
        .reindex(province_codes, fill_value=0.0)
        .existing_capacity_gw.to_numpy(dtype=float)
    )
    identified_error = float(
        np.max(
            np.abs(
                identified
                - capacity.identified_station_capacity_gw.to_numpy(dtype=float)
            )
        )
    )
    _check(checks, "identified_station_capacity_closure_gw", identified_error <= 1e-9, identified_error, "<=1e-9")

    component_error = float(
        np.max(
            np.abs(
                capacity.identified_station_capacity_gw
                + capacity.provincial_aggregate_capacity_gw
                - capacity.harmonized_conventional_capacity_gw
            )
        )
    )
    _check(checks, "station_plus_aggregate_closure_gw", component_error <= 1e-9, component_error, "<=1e-9")
    technical_error = float(
        np.max(
            np.abs(
                capacity.station_technical_upper_gw
                + capacity.provincial_aggregate_capacity_gw
                - capacity.harmonized_future_technical_upper_gw
            )
        )
    )
    _check(checks, "technical_upper_closure_gw", technical_error <= 1e-9, technical_error, "<=1e-9")

    national_total = float(capacity.harmonized_conventional_capacity_gw.sum())
    _check(checks, "national_conventional_capacity_target_gw", abs(national_total - target_gw) <= 1e-6, national_total, target_gw)
    aggregate_total = float(capacity.provincial_aggregate_capacity_gw.sum())
    identified_total = float(capacity.identified_station_capacity_gw.sum())

    failures = [
        row["check"] for row in checks if row["status"] == "HARD_FAIL"
    ]
    return {
        "schema_version": "provincial_aggregate_hydro_input_audit_v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": "PASS" if not failures else "FAIL",
        "data_root": str(data_root.resolve()),
        "target_conventional_capacity_gw": target_gw,
        "identified_station_capacity_gw": identified_total,
        "provincial_aggregate_capacity_gw": aggregate_total,
        "harmonized_conventional_capacity_gw": national_total,
        "files": [
            {
                "path": str(path.resolve()),
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in (capacity_path, profile_path, stations_path)
        ],
        "checks": checks,
        "failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", default=str(PROJECT_ROOT / "data"))
    parser.add_argument("--target-gw", type=float, default=380.0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = build_audit(Path(args.data_root), target_gw=args.target_gw)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
