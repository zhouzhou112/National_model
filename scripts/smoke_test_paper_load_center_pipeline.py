"""Smoke tests for the paper-faithful load-center candidate pipeline."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data"
LOAD_ROOT = DATA_ROOT / "load_centers_1km"
PAPER_ROOT = LOAD_ROOT / "paper_method_candidate"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def lonlat_to_unit(lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    lon_rad = np.deg2rad(lon.astype(float))
    lat_rad = np.deg2rad(lat.astype(float))
    cos_lat = np.cos(lat_rad)
    return np.column_stack(
        [cos_lat * np.cos(lon_rad), cos_lat * np.sin(lon_rad), np.sin(lat_rad)]
    )


def great_circle_matrix_km(
    lon_a: np.ndarray,
    lat_a: np.ndarray,
    lon_b: np.ndarray,
    lat_b: np.ndarray,
) -> np.ndarray:
    cosine = np.clip(
        lonlat_to_unit(lon_a, lat_a) @ lonlat_to_unit(lon_b, lat_b).T,
        -1.0,
        1.0,
    )
    return 6371.0088 * np.arccos(cosine)


def main() -> None:
    checks: list[dict] = []

    def add(name: str, passed: bool, value: object, expected: object) -> None:
        checks.append(
            {
                "check": name,
                "status": "PASS" if passed else "FAIL",
                "value": value,
                "expected": expected,
            }
        )

    raster_audit = load_json(LOAD_ROOT / "qc" / "audit_summary.json")
    province_audit = load_json(LOAD_ROOT / "qc" / "land_point_province_audit_summary.json")
    paper_manifest = load_json(PAPER_ROOT / "run_manifest.json")
    capacity_manifest = load_json(PAPER_ROOT / "initial_2025" / "run_manifest.json")
    add("raster_audit_gate", raster_audit["status"] == "PASS_WITH_WARNINGS", raster_audit["status"], "PASS_WITH_WARNINGS only because physical unit is unresolved")
    add("province_audit_gate", province_audit["status"] == "PASS", province_audit["status"], "PASS")
    add("paper_route_gate", paper_manifest["status"] == "PASS", paper_manifest["status"], "PASS")
    add("initial_capacity_gate", capacity_manifest["status"] == "PASS", capacity_manifest["status"], "PASS")

    centers = pd.read_csv(PAPER_ROOT / "paper_load_centers.csv")
    demand = pd.read_csv(PAPER_ROOT / "demand_point_to_paper_load_center.csv.gz")
    substations = pd.read_csv(DATA_ROOT / "grid" / "substations_osm_220kv_plus.csv")
    substation_center = pd.read_csv(PAPER_ROOT / "substation_to_paper_load_center.csv")
    routes = pd.read_csv(PAPER_ROOT / "grid_point_paper_route.csv")
    corrections = pd.read_csv(LOAD_ROOT / "qc" / "land_point_province_corrections.csv")
    station_capacity = pd.read_csv(
        PAPER_ROOT / "initial_2025" / "substation_initial_capacity_2025_paper_route.csv"
    )
    center_capacity = pd.read_csv(
        PAPER_ROOT / "initial_2025" / "load_center_initial_capacity_2025.csv"
    )

    add("paper_center_rows", len(centers) == 278, len(centers), 278)
    add("paper_center_unique", centers.load_center_id.nunique() == 278, centers.load_center_id.nunique(), 278)
    add("paper_center_provinces", centers.province_code.nunique() == 31, centers.province_code.nunique(), 31)
    add(
        "paper_center_scale_counts",
        centers.source_scale.value_counts().to_dict()
        == {"Natural_Earth_1_50m": 272, "Natural_Earth_1_10m_Tibet_supplement": 6},
        centers.source_scale.value_counts().to_dict(),
        {"Natural_Earth_1_50m": 272, "Natural_Earth_1_10m_Tibet_supplement": 6},
    )
    demand_closure = demand.groupby("province_code").demand_share_in_province.sum().sub(1.0).abs().max()
    add("demand_share_closure", demand_closure <= 1e-10, float(demand_closure), "<= 1e-10")

    add("substation_input_rows", len(substations) == 6294, len(substations), 6294)
    add("substation_center_rows", len(substation_center) == 6294, len(substation_center), 6294)
    add(
        "substation_center_ids_valid",
        set(substation_center.load_center_id).issubset(set(centers.load_center_id)),
        substation_center.load_center_id.nunique(),
        "all IDs in paper_load_centers.csv",
    )
    add("grid_route_rows", len(routes) == 16609, len(routes), 16609)
    add("grid_route_unique", routes.grid_uid.nunique() == 16609, routes.grid_uid.nunique(), 16609)
    add(
        "grid_route_nonnegative",
        routes[["spur_distance_km", "trunk_distance_km", "total_connection_distance_km"]].min().min() >= 0,
        float(routes[["spur_distance_km", "trunk_distance_km", "total_connection_distance_km"]].min().min()),
        ">= 0 km",
    )
    total_error = (
        routes.spur_distance_km + routes.trunk_distance_km - routes.total_connection_distance_km
    ).abs().max()
    add("grid_route_distance_closure", total_error <= 1e-9, float(total_error), "<= 1e-9 km")
    add(
        "dpv_zero_distance",
        routes.dpv_spur_distance_km.eq(0).all() and routes.dpv_trunk_distance_km.eq(0).all(),
        float(routes.dpv_spur_distance_km.abs().max() + routes.dpv_trunk_distance_km.abs().max()),
        0.0,
    )

    sample = routes.sample(n=100, random_state=20260702)
    exact_errors = []
    station_trunk = substation_center.set_index("substation_id").trunk_distance_km
    for province_code, points in sample.groupby("province_code"):
        province_stations = substations.loc[substations.province_code.eq(province_code)].reset_index(drop=True)
        spur = great_circle_matrix_km(
            points.lon.to_numpy(float),
            points.lat.to_numpy(float),
            province_stations.lon.to_numpy(float),
            province_stations.lat.to_numpy(float),
        )
        trunk = province_stations.substation_id.map(station_trunk).to_numpy(float)
        exact_minimum = np.min(spur + trunk[None, :], axis=1)
        exact_errors.extend(
            np.abs(exact_minimum - points.total_connection_distance_km.to_numpy(float)).tolist()
        )
    exact_error = max(exact_errors)
    add("sample_exact_minimum_route", exact_error <= 1e-6, exact_error, "<= 1e-6 km for 100 deterministic samples")

    add("land_correction_rows", len(corrections) == 43, len(corrections), 43)
    extreme_expected = {
        "G000033483": 54,
        "G000034618": 54,
        "G000019631": 22,
        "G000043120": 53,
    }
    extreme_actual = corrections.set_index("grid_uid").province_code_after.to_dict()
    add(
        "extreme_land_province_corrections",
        all(int(extreme_actual.get(key, -1)) == value for key, value in extreme_expected.items()),
        {key: int(extreme_actual.get(key, -1)) for key in extreme_expected},
        extreme_expected,
    )

    add("station_capacity_rows", len(station_capacity) == 6294, len(station_capacity), 6294)
    add("center_capacity_rows", len(center_capacity) == 278, len(center_capacity), 278)
    connected_total = station_capacity.connected_vre_nameplate_gw.sum()
    dpv_total = station_capacity.existing_dpv_local_gw.sum()
    add("connected_nameplate_gw", np.isclose(connected_total, 1310.0, atol=1e-6), float(connected_total), 1310.0)
    add("dpv_local_gw", np.isclose(dpv_total, 530.0, atol=1e-6), float(dpv_total), 530.0)
    bound_error = (
        station_capacity.paper_proxy_coincident_peak_trunk_gw
        - station_capacity.connected_vre_nameplate_gw
    ).max()
    add("coincident_peak_nameplate_bound", bound_error <= 1e-6, float(bound_error), "<= 1e-6 GW")

    status = "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL"
    report = {"status": status, "checks_total": len(checks), "checks": checks}
    output_path = PAPER_ROOT / "smoke_test_report.json"
    with output_path.open("w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if status != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

