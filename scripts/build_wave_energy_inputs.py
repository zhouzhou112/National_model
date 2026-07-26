"""Map raw wave data onto the existing CISPO optimization grid.

The 735 MB hourly NetCDF remains outside the repository and is read at solve
time through ``CISPO_WAVE_ROOT``.  The generated site table contains only raw
wave cells that coincide with an existing marine ``optimization_points.csv``
row.  It therefore adds a technology option, not a second spatial grid.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def map_to_existing_marine_grid(
    source_lon: np.ndarray,
    source_lat: np.ndarray,
    points: pd.DataFrame,
    *,
    tolerance_degrees: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return source mask, matched point positions and coordinate differences.

    A tolerance is needed because the wave latitude coordinate carries roughly
    5e-5 degree floating-point offsets from the existing 0.25-degree grid.  The
    function rejects non-marine rows and refuses many-to-one mappings.
    """
    required = {"grid_uid", "grid_id", "lon", "lat", "is_land"}
    missing = sorted(required.difference(points.columns))
    if missing:
        raise ValueError(
            "optimization_points.csv is missing columns: " + ", ".join(missing)
        )
    coordinates = points[["lon", "lat"]].to_numpy(dtype=float)
    distances, positions = cKDTree(coordinates).query(
        np.column_stack((source_lon, source_lat)), k=1
    )
    positions = np.asarray(positions, dtype=np.int64)
    marine = points.iloc[positions].is_land.to_numpy(dtype=int) == 0
    keep = (np.asarray(distances, dtype=float) <= float(tolerance_degrees)) & marine
    matched_positions = positions[keep]
    matched_grid_uids = points.iloc[matched_positions].grid_uid.astype(str)
    if matched_grid_uids.duplicated().any():
        duplicates = matched_grid_uids[matched_grid_uids.duplicated()].unique()
        raise ValueError(
            "Multiple wave source rows map to one optimization grid: "
            f"{duplicates[:10].tolist()}"
        )
    return keep, matched_positions, np.asarray(distances, dtype=float)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build model-ready wave sites and provenance manifest"
    )
    parser.add_argument(
        "--wave-netcdf",
        type=Path,
        default=ROOT.parent / "wave_energy" / "wave_grid.nc",
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=ROOT / "data" / "wave",
    )
    parser.add_argument(
        "--coordinate-tolerance-degrees",
        type=float,
        default=0.02,
        help="Maximum source-to-existing-grid coordinate difference.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = args.wave_netcdf.resolve()
    output_directory = args.output_directory.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)

    points = pd.read_csv(ROOT / "data" / "vre" / "optimization_points.csv")
    if args.coordinate_tolerance_degrees <= 0.0:
        raise ValueError("--coordinate-tolerance-degrees must be positive")
    routes = pd.read_csv(
        ROOT / "data" / "load_center_network" / "city_337" / "vre_routes.csv",
        usecols=[
            "grid_uid",
            "grid_id",
            "province_code",
            "substation_id",
            "load_center_id",
        ],
    )
    if routes.grid_uid.duplicated().any():
        raise ValueError("Existing VRE routes must be unique by grid_uid")

    with xr.open_dataset(source, decode_times=True) as dataset:
        required = {
            "grid_id",
            "lon",
            "lat",
            "water_depth_m",
            "distance_km",
            "wave_nc_imputed",
            "impute_distance_deg",
            "grid_capacity_mw",
            "capacity_factor",
            "scenario_year",
            "scenario_code",
            "time",
        }
        missing = sorted(required.difference(dataset.variables))
        if missing:
            raise ValueError(
                f"Wave NetCDF is missing variables: {', '.join(missing)}"
            )
        if tuple(dataset.capacity_factor.dims) != ("scenario", "time", "grid"):
            raise ValueError("capacity_factor must have scenario,time,grid dimensions")
        if int(dataset.sizes["time"]) != 8760:
            raise ValueError("Wave source must contain exactly 8760 hourly records")
        time = pd.DatetimeIndex(dataset.time.values)
        expected_time = pd.date_range(time[0], periods=8760, freq="h")
        if not time.equals(expected_time):
            raise ValueError("Wave source time coordinate is not gap-free hourly data")
        potential = np.asarray(dataset.grid_capacity_mw.values, dtype=float)
        if potential.ndim != 2 or potential.shape[0] != dataset.sizes["scenario"]:
            raise ValueError("grid_capacity_mw must have scenario x grid dimensions")
        maximum_potential_scenario_difference_mw = float(
            np.max(np.abs(potential - potential[0:1, :]))
        )
        if maximum_potential_scenario_difference_mw > 1e-6:
            raise ValueError(
                "Source capacity potential differs by scenario; update the input "
                "contract before collapsing it to one upper-bound column"
            )
        source_lon = np.asarray(dataset.lon.values, dtype=float)
        source_lat = np.asarray(dataset.lat.values, dtype=float)
        keep, matched_positions, coordinate_difference = (
            map_to_existing_marine_grid(
                source_lon,
                source_lat,
                points,
                tolerance_degrees=args.coordinate_tolerance_degrees,
            )
        )
        matched = points.iloc[matched_positions][
            ["grid_uid", "grid_id", "lon", "lat", "province_code", "is_land"]
        ].reset_index(drop=True)
        matched = matched.merge(
            routes,
            on=["grid_uid", "grid_id", "province_code"],
            how="left",
            validate="one_to_one",
        )
        if matched[["substation_id", "load_center_id"]].isna().any().any():
            raise ValueError("Some matched optimization grids lack existing routes")
        source_grid_ids = np.asarray(dataset.grid_id.values, dtype=np.int64)
        sites = pd.DataFrame(
            {
                "grid_uid": matched.grid_uid.astype(str),
                "grid_id": matched.grid_id.to_numpy(dtype=np.int64),
                "wave_source_grid_id": source_grid_ids[keep],
                "lon": matched.lon.to_numpy(dtype=float),
                "lat": matched.lat.to_numpy(dtype=float),
                "wave_source_lon": source_lon[keep],
                "wave_source_lat": source_lat[keep],
                "coordinate_difference_degrees": coordinate_difference[keep],
                "is_land": matched.is_land.to_numpy(dtype=np.int64),
                "province_code": matched.province_code.to_numpy(dtype=np.int64),
                "load_center_id": matched.load_center_id.astype(str),
                "substation_id": matched.substation_id.astype(str),
                "capacity_upper_gw_raw": potential[0, keep] / 1000.0,
                "distance_to_shore_km": np.asarray(
                    dataset.distance_km.values, dtype=float
                )[keep],
                "water_depth_m": np.asarray(
                    dataset.water_depth_m.values, dtype=float
                )[keep],
                "wave_nc_imputed": np.asarray(
                    dataset.wave_nc_imputed.values, dtype=bool
                )[keep],
                "impute_distance_deg": np.asarray(
                    dataset.impute_distance_deg.values, dtype=float
                )[keep],
            }
        )
        scenario_rows = [
            {
                "scenario_position": int(position),
                "profile_year": int(year),
                "scenario_code": int(code),
            }
            for position, (year, code) in enumerate(
                zip(
                    np.asarray(dataset.scenario_year.values, dtype=int),
                    np.asarray(dataset.scenario_code.values, dtype=int),
                )
            )
        ]
        cf_min = float(dataset.capacity_factor.min().values)
        cf_max = float(dataset.capacity_factor.max().values)

    output_directory.mkdir(parents=True, exist_ok=True)
    sites_path = output_directory / "wave_sites.csv"
    sites.to_csv(sites_path, index=False, encoding="utf-8-sig")
    manifest = {
        "contract_version": "wave_existing_grid_v2",
        "generated_at": datetime.now().astimezone().isoformat(),
        "source_file": str(source),
        "source_sha256": sha256_file(source),
        "sites_file": str(sites_path),
        "sites_sha256": sha256_file(sites_path),
        "grid_mapping_method": (
            "nearest coordinate within configured tolerance, followed by "
            "is_land == 0 intersection with existing optimization_points.csv"
        ),
        "coordinate_tolerance_degrees": float(
            args.coordinate_tolerance_degrees
        ),
        "routing_method": (
            "exact reuse of the matched grid_uid row in city_337/vre_routes.csv"
        ),
        "grid_rows": int(len(sites)),
        "unique_grid_uids": int(sites.grid_uid.nunique()),
        "unique_grid_ids": int(sites.grid_id.nunique()),
        "unique_wave_source_grid_ids": int(sites.wave_source_grid_id.nunique()),
        "raw_source_grid_rows": int(len(keep)),
        "excluded_nonmatching_or_nonmarine_rows": int((~keep).sum()),
        "excluded_raw_capacity_upper_gw": float(potential[0, ~keep].sum() / 1000.0),
        "active_provinces": sorted(sites.province_code.unique().astype(int).tolist()),
        "total_raw_capacity_upper_gw": float(sites.capacity_upper_gw_raw.sum()),
        "maximum_raw_capacity_upper_gw": float(
            sites.capacity_upper_gw_raw.max()
        ),
        "maximum_potential_scenario_difference_mw": (
            maximum_potential_scenario_difference_mw
        ),
        "imputed_cf_grid_rows": int(sites.wave_nc_imputed.sum()),
        "maximum_distance_to_shore_km": float(sites.distance_to_shore_km.max()),
        "maximum_water_depth_m": float(sites.water_depth_m.max()),
        "maximum_coordinate_difference_degrees": float(
            sites.coordinate_difference_degrees.max()
        ),
        "capacity_factor_min": cf_min,
        "capacity_factor_max": cf_max,
        "scenario_rows": scenario_rows,
        "warnings": [
            "Raw capacity potential is identical across all source scenarios.",
            "The source has no 2060 CF scenario; model configuration must state an explicit hold or replacement.",
            "Potential is a theoretical/technical upper bound and requires sensitivity scaling.",
            "Only raw wave cells coincident with existing marine optimization grids are retained.",
            "Matched rows reuse the existing grid_uid province and city_337 route exactly.",
        ],
    }
    (output_directory / "wave_input_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
