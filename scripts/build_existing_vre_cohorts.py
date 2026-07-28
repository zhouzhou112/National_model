"""Build traceable 2025 observed-VRE retirement cohorts.

The production optimisation points are closed to national totals by a mixture
of identified GEM projects, isolated OSM geometries and residual allocation.
Only GEM provides project start years.  This builder preserves that evidence
boundary: all capacity without a usable project start year is recorded as a
2025 boundary-censored cohort, rather than being assigned an invented age.

The resulting table is a lower-bound trajectory.  Retirement removes only the
observed-capacity floor; the original 0.25-degree site potential remains
available for an economically chosen replacement build.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TECH_SPECS = {
    "onwind": {
        "project_technology": "wind",
        "project_install_type": "onwind",
        "gem_column": "identified_gem_onwind_mw",
        "total_column": "final_existing_onwind_mw",
        "point_column": "existing_onwind_gw",
    },
    "offwind": {
        "project_technology": "wind",
        "project_install_type": "offwind",
        "gem_column": "identified_gem_offwind_mw",
        "total_column": "final_existing_offwind_mw",
        "point_column": "existing_offwind_gw",
    },
    "upv": {
        "project_technology": "solar",
        "project_install_type": "utility_pv",
        "gem_column": "identified_gem_utility_pv_mw",
        "total_column": None,
        "point_column": "existing_upv_gw",
    },
    "dpv": {
        "project_technology": None,
        "project_install_type": None,
        "gem_column": None,
        "total_column": None,
        "point_column": "existing_dpv_gw",
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-file",
        type=Path,
        required=True,
        help="GEM operating projects assigned to 0.25-degree grid cells.",
    )
    parser.add_argument(
        "--grid-capacity-file",
        type=Path,
        required=True,
        help="Versioned grid capacity closure table containing GEM/OSM/residual fields.",
    )
    parser.add_argument(
        "--optimization-points",
        type=Path,
        default=ROOT / "data" / "vre" / "optimization_points.csv",
        help="Current production optimisation-point capacity table.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "optimization_2030.json",
        help="Production configuration supplying the VRE lifetimes.",
    )
    parser.add_argument("--base-year", type=int, default=2025)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "vre" / "existing_capacity_cohorts_2025.csv",
    )
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=ROOT / "data" / "vre" / "existing_capacity_cohorts_2025_manifest.json",
    )
    return parser.parse_args()


def _coerce_start_year(values: pd.Series, base_year: int) -> tuple[pd.Series, pd.Series]:
    numeric = pd.to_numeric(values, errors="coerce")
    valid = numeric.between(1900, base_year, inclusive="both")
    start_year = numeric.where(valid, base_year).fillna(base_year).astype(int)
    status = np.where(
        numeric.isna(),
        "gem_missing_start_year_boundary_censored",
        np.where(
            numeric.gt(base_year),
            "gem_post_boundary_start_year_censored",
            "gem_reported_start_year",
        ),
    )
    return start_year, pd.Series(status, index=values.index, dtype="string")


def _require_close(label: str, observed: pd.Series, expected: pd.Series, tolerance_mw: float = 1e-5) -> None:
    difference = (observed.reindex(expected.index, fill_value=0.0) - expected).abs()
    if float(difference.max()) > tolerance_mw:
        raise ValueError(
            f"{label} does not close; maximum grid-level difference is "
            f"{float(difference.max()):.6g} MW"
        )


def main() -> None:
    args = parse_args()
    for path in (
        args.project_file,
        args.grid_capacity_file,
        args.optimization_points,
        args.config,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)

    config = json.loads(args.config.read_text(encoding="utf-8"))
    lifetimes = config["finance"]["default_lifetime_years"]
    project = pd.read_csv(
        args.project_file,
        usecols=["technology", "install_type", "capacity_mw", "start_year", "grid_uid"],
    )
    capacity_grid = pd.read_csv(args.grid_capacity_file)
    points = pd.read_csv(args.optimization_points)
    if points.grid_uid.duplicated().any() or capacity_grid.grid_uid.duplicated().any():
        raise ValueError("Optimisation points and grid capacity rows must each have unique grid_uid")

    required_grid_columns = {"grid_uid"}
    for spec in TECH_SPECS.values():
        if spec["gem_column"]:
            required_grid_columns.add(spec["gem_column"])
    missing_grid = required_grid_columns.difference(capacity_grid.columns)
    if missing_grid:
        raise ValueError(f"Grid capacity table is missing: {', '.join(sorted(missing_grid))}")
    required_point_columns = {"grid_uid"}.union(
        spec["point_column"] for spec in TECH_SPECS.values()
    )
    missing_points = required_point_columns.difference(points.columns)
    if missing_points:
        raise ValueError(f"Optimisation points are missing: {', '.join(sorted(missing_points))}")

    grid = capacity_grid.set_index("grid_uid")
    points = points.set_index("grid_uid")
    if not set(points.index).issubset(grid.index):
        raise ValueError("Some optimisation-point grid_uid values are absent from the capacity source")

    rows: list[dict[str, object]] = []
    closure_rows: list[dict[str, object]] = []
    for technology, spec in TECH_SPECS.items():
        expected_mw = points[spec["point_column"]].astype(float) * 1000.0
        if (expected_mw < -1e-8).any():
            raise ValueError(f"Negative current capacity for {technology}")
        if spec["gem_column"] is not None:
            source_gem = grid.loc[points.index, spec["gem_column"]].astype(float)
            selected = project.loc[
                project.technology.eq(spec["project_technology"])
                & project.install_type.eq(spec["project_install_type"])
            ].copy()
            selected["capacity_mw"] = pd.to_numeric(
                selected.capacity_mw, errors="raise"
            )
            if (selected.capacity_mw <= 0.0).any():
                raise ValueError(f"Non-positive GEM capacity in {technology}")
            selected["start_year"], selected["start_year_status"] = _coerce_start_year(
                selected.start_year, args.base_year
            )
            observed_gem = selected.groupby("grid_uid").capacity_mw.sum()
            _require_close(f"{technology} GEM capacity", observed_gem, source_gem)
            grouped = (
                selected.groupby(["grid_uid", "start_year", "start_year_status"], as_index=False)
                .capacity_mw.sum()
            )
            for row in grouped.itertuples(index=False):
                rows.append(
                    {
                        "grid_uid": str(row.grid_uid),
                        "technology": technology,
                        "start_year": int(row.start_year),
                        "capacity_gw": float(row.capacity_mw) / 1000.0,
                        "provenance": "identified_gem_project",
                        "start_year_status": str(row.start_year_status),
                    }
                )
            unidentified_mw = expected_mw - source_gem
        else:
            unidentified_mw = expected_mw.copy()

        if (unidentified_mw < -1e-5).any():
            raise ValueError(f"{technology} identified GEM capacity exceeds model capacity")
        for grid_uid, capacity_mw in unidentified_mw.clip(lower=0.0).items():
            if capacity_mw <= 1e-8:
                continue
            rows.append(
                {
                    "grid_uid": str(grid_uid),
                    "technology": technology,
                    "start_year": int(args.base_year),
                    "capacity_gw": float(capacity_mw) / 1000.0,
                    "provenance": "unidentified_osm_or_residual_capacity",
                    "start_year_status": "boundary_censored_2025",
                }
            )

        closure_rows.append(
            {
                "technology": technology,
                "model_existing_capacity_gw": float(expected_mw.sum() / 1000.0),
                "identified_gem_capacity_gw": float(
                    source_gem.sum() / 1000.0
                )
                if spec["gem_column"] is not None
                else 0.0,
                "boundary_censored_capacity_gw": float(
                    unidentified_mw.clip(lower=0.0).sum() / 1000.0
                ),
            }
        )

    cohorts = pd.DataFrame(rows)
    if cohorts.empty:
        raise ValueError("No existing VRE cohorts were generated")
    cohorts["retire_year"] = [
        max(int(start_year) + int(lifetimes[str(technology)]), args.base_year + 1)
        for technology, start_year in zip(cohorts.technology, cohorts.start_year)
    ]
    cohorts["retirement_status"] = np.where(
        cohorts.retire_year.eq(args.base_year + 1)
        & cohorts.start_year.lt(args.base_year),
        "reported_operating_at_boundary_lifetime_capped",
        "technology_lifetime_from_start_year",
    )
    cohorts = cohorts[
        [
            "grid_uid",
            "technology",
            "start_year",
            "retire_year",
            "capacity_gw",
            "provenance",
            "start_year_status",
            "retirement_status",
        ]
    ].sort_values(["technology", "grid_uid", "start_year", "provenance"])

    output_closure = cohorts.groupby("technology").capacity_gw.sum()
    expected_closure = pd.Series(
        {
            row["technology"]: row["model_existing_capacity_gw"]
            for row in closure_rows
        }
    )
    if not np.allclose(
        output_closure.reindex(expected_closure.index, fill_value=0.0),
        expected_closure,
        rtol=0.0,
        atol=1e-9,
    ):
        raise ValueError("Generated VRE cohorts do not close nationally")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    cohorts.to_csv(args.output, index=False, encoding="utf-8-sig", lineterminator="\n")
    manifest = {
        "schema_version": "existing_vre_cohorts_v1",
        "base_year": int(args.base_year),
        "retirement_rule": "active_when_planning_year_lt_retire_year",
        "unknown_start_year_policy": "boundary_censored_2025_v1",
        "site_rebuild_policy": "retain_same_site_technical_upper_v1",
        "inputs": {
            "project_file": str(args.project_file),
            "project_file_sha256": sha256_file(args.project_file),
            "grid_capacity_file": str(args.grid_capacity_file),
            "grid_capacity_file_sha256": sha256_file(args.grid_capacity_file),
            "optimization_points": str(args.optimization_points),
            "optimization_points_sha256": sha256_file(args.optimization_points),
            "config": str(args.config),
            "config_sha256": sha256_file(args.config),
        },
        "output": {
            "path": str(args.output),
            "sha256": sha256_file(args.output),
            "row_count": int(len(cohorts)),
            "capacity_by_technology_gw": {
                str(key): float(value) for key, value in output_closure.items()
            },
            "closure": closure_rows,
        },
    }
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest["output"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
