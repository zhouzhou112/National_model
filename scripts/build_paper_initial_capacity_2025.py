"""Recompute 2025 spur/trunk/interface capacity on paper-faithful routes.

Two initial-capacity interpretations are retained:

* conservative simultaneous-nameplate stress, requested by the user;
* hourly coincident-peak comparator using the same resolved 2023 CF profiles as
  the existing audited point table, consistent with CISPO equations S4-18/S4-19.

Outputs are candidates and never overwrite ``data/grid`` production files.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data"
PAPER_ROOT = DATA_ROOT / "load_centers_1km" / "paper_method_candidate"
OUTPUT_DIR = PAPER_ROOT / "initial_2025"
SOURCE_SPUR_PATH = DATA_ROOT / "grid" / "initial_spur_capacity_2025.csv"
SUBSTATIONS_PATH = DATA_ROOT / "grid" / "substations_osm_220kv_plus.csv"
PAPER_ROUTE_PATH = PAPER_ROOT / "grid_point_paper_route.csv"
PAPER_SUBSTATION_CENTER_PATH = PAPER_ROOT / "substation_to_paper_load_center.csv"
PAPER_CENTERS_PATH = PAPER_ROOT / "paper_load_centers.csv"
PAPER_MANIFEST_PATH = PAPER_ROOT / "run_manifest.json"
PROVINCE_AUDIT_SUMMARY_PATH = (
    DATA_ROOT / "load_centers_1km" / "qc" / "land_point_province_audit_summary.json"
)
WEATHER_YEAR = 2023


def sha256_file(path: Path, chunk_size: int = 4 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(chunk_size):
            digest.update(block)
    return digest.hexdigest()


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig", lineterminator="\n")


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def read_cf_columns(group: object, positions: np.ndarray) -> np.ndarray:
    dimensions = list(group["cf"].attrs["_ARRAY_DIMENSIONS"])
    if dimensions == ["time", "grid_id"]:
        values = group["cf"].oindex[:, positions]
    elif dimensions == ["grid_id", "time"]:
        values = group["cf"].oindex[positions, :].T
    else:
        raise ValueError(f"Unexpected CF dimension order: {dimensions}")
    return np.asarray(values, dtype=np.float32)


def main() -> None:
    try:
        import zarr
    except ImportError as exc:
        raise RuntimeError("zarr is required for 2025 hourly capacity reconstruction") from exc

    required = [
        SOURCE_SPUR_PATH,
        SUBSTATIONS_PATH,
        PAPER_ROUTE_PATH,
        PAPER_SUBSTATION_CENTER_PATH,
        PAPER_CENTERS_PATH,
        PAPER_MANIFEST_PATH,
        PROVINCE_AUDIT_SUMMARY_PATH,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required inputs:\n" + "\n".join(missing))
    paper_manifest = load_json(PAPER_MANIFEST_PATH)
    province_audit = load_json(PROVINCE_AUDIT_SUMMARY_PATH)
    if paper_manifest["status"] != "PASS" or province_audit["status"] != "PASS":
        raise ValueError("Paper-route and province-audit gates must both pass")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source_spur = pd.read_csv(SOURCE_SPUR_PATH)
    route = pd.read_csv(PAPER_ROUTE_PATH)
    substations = pd.read_csv(SUBSTATIONS_PATH)
    substation_center = pd.read_csv(PAPER_SUBSTATION_CENTER_PATH)
    centers = pd.read_csv(PAPER_CENTERS_PATH)

    route_columns = [
        "grid_uid",
        "province_code",
        "province_name_en",
        "province_name_zh",
        "substation_id",
        "load_center_id",
        "spur_distance_km",
        "trunk_distance_km",
        "onwind_spur_distance_km",
        "upv_spur_distance_km",
        "offwind_export_distance_km",
        "dpv_spur_distance_km",
        "matching_objective",
        "power_grid_scope",
        "route_status",
    ]
    routed = source_spur.merge(
        route[route_columns],
        on="grid_uid",
        how="left",
        validate="many_to_one",
        suffixes=("_before", "_paper"),
    )
    if routed.substation_id_paper.isna().any():
        raise ValueError("Positive-capacity point rows have missing paper route")
    routed["province_code_before_paper_route"] = routed.province_code_before
    routed["province_name_en_before_paper_route"] = routed.province_name_en_before
    routed["province_name_zh_before_paper_route"] = routed.province_name_zh_before
    routed["substation_id_before_paper_route"] = routed.substation_id_before
    routed["connection_distance_km_before_paper_route"] = routed.connection_distance_km
    routed["province_code"] = routed.province_code_paper.astype(int)
    routed["province_name_en"] = routed.province_name_en_paper
    routed["province_name_zh"] = routed.province_name_zh_paper
    routed["substation_id"] = routed.substation_id_paper
    routed["connection_distance_km"] = np.select(
        [
            routed.technology.eq("onwind"),
            routed.technology.eq("upv"),
            routed.technology.eq("offwind"),
            routed.technology.eq("dpv"),
        ],
        [
            routed.onwind_spur_distance_km,
            routed.upv_spur_distance_km,
            routed.offwind_export_distance_km,
            routed.dpv_spur_distance_km,
        ],
        default=np.nan,
    )
    routed["load_center_id"] = routed.load_center_id
    routed["trunk_distance_km"] = routed.trunk_distance_km
    routed["initial_capacity_method"] = "simultaneous_2025_nameplate_stress"
    routed["paper_comparator_method"] = "hourly_coincident_peak_from_resolved_2023_cf"
    routed["candidate_status"] = "paper_route_candidate_not_production_default"

    drop_columns = [
        column
        for column in routed.columns
        if column.endswith("_before") or column.endswith("_paper")
    ]
    routed = routed.drop(columns=drop_columns)
    ordered_front = [
        "grid_uid",
        "grid_id",
        "province_code",
        "province_name_en",
        "province_name_zh",
        "lon",
        "lat",
        "is_land",
        "technology",
        "existing_capacity_gw",
        "connection_required",
        "substation_id",
        "load_center_id",
        "connection_distance_km",
        "trunk_distance_km",
    ]
    routed = routed[ordered_front + [column for column in routed.columns if column not in ordered_front]]

    substation_ids = substations.substation_id.tolist()
    substation_position = {value: index for index, value in enumerate(substation_ids)}
    connected = routed.loc[routed.connection_required].copy()
    connected_positions = connected.substation_id.map(substation_position)
    if connected_positions.isna().any():
        raise ValueError("Paper route references a substation outside the eligible input")
    connected_positions = connected_positions.to_numpy(int)

    station_hourly: np.ndarray | None = None
    time_values: np.ndarray | None = None
    recomputed_peak_cf = np.empty(len(connected), dtype=float)
    connected_row_position = {index: position for position, index in enumerate(connected.index)}
    for source_path, group_rows in connected.groupby("cf_source_path", sort=True):
        if not source_path or source_path == "nan":
            raise ValueError("Connected capacity row has no resolved CF source path")
        store = zarr.open_group(str(source_path), mode="r")
        grid_ids = np.asarray(store["grid_id"][:], dtype=np.int64)
        grid_position = {int(grid_id): position for position, grid_id in enumerate(grid_ids)}
        requested = group_rows.cf_grid_id_used.astype(int).to_numpy()
        missing_ids = sorted(set(requested) - set(grid_position))
        if missing_ids:
            raise ValueError(f"Resolved CF grid IDs are absent from {source_path}: {missing_ids[:10]}")
        positions = np.asarray([grid_position[int(grid_id)] for grid_id in requested], dtype=int)
        cf = read_cf_columns(store, positions)
        if station_hourly is None:
            station_hourly = np.zeros((cf.shape[0], len(substations)), dtype=np.float32)
            time_values = np.asarray(store["time"][:], dtype=np.int64)
        elif cf.shape[0] != station_hourly.shape[0]:
            raise ValueError("CF stores do not share a common hourly dimension")
        row_positions = np.asarray([connected_row_position[index] for index in group_rows.index], dtype=int)
        recomputed_peak_cf[row_positions] = np.max(cf, axis=0)
        output = cf * group_rows.existing_capacity_gw.to_numpy(np.float32)[None, :]
        station_positions = group_rows.substation_id.map(substation_position).to_numpy(int)
        mapping = csr_matrix(
            (
                np.ones(len(group_rows), dtype=np.float32),
                (np.arange(len(group_rows)), station_positions),
            ),
            shape=(len(group_rows), len(substations)),
        )
        station_hourly += mapping.T.dot(output.T).T
        del cf, output

    if station_hourly is None or time_values is None:
        raise ValueError("No connected 2025 VRE capacity was reconstructed")
    connected["recomputed_peak_cf"] = recomputed_peak_cf
    peak_cf_error = float(
        np.max(np.abs(connected.recomputed_peak_cf - connected.historical_proxy_peak_cf))
    )

    technology_capacity = (
        routed.pivot_table(
            index="substation_id",
            columns="technology",
            values="existing_capacity_gw",
            aggfunc="sum",
            fill_value=0.0,
        )
        .reindex(substation_ids, fill_value=0.0)
    )
    for technology in ("onwind", "offwind", "upv", "dpv"):
        if technology not in technology_capacity.columns:
            technology_capacity[technology] = 0.0

    station = substations[
        [
            "substation_id",
            "province_code",
            "province_name_en",
            "province_name_zh",
            "lon",
            "lat",
            "max_voltage_kv",
            "substation_type",
        ]
    ].copy()
    for technology in ("onwind", "offwind", "upv", "dpv"):
        station[f"existing_{technology}_gw"] = technology_capacity[technology].to_numpy(float)
    station["connected_vre_nameplate_gw"] = (
        station.existing_onwind_gw + station.existing_offwind_gw + station.existing_upv_gw
    )
    station["existing_dpv_local_gw"] = station.existing_dpv_gw
    paper_spur_sum = (
        routed.loc[routed.connection_required]
        .groupby("substation_id").paper_formula_spur_capacity_gw.sum()
        .reindex(substation_ids, fill_value=0.0)
    )
    station["sum_point_paper_spur_capacity_gw"] = paper_spur_sum.to_numpy(float)
    peak_hour_index = np.argmax(station_hourly, axis=0)
    coincident_peak = station_hourly[
        peak_hour_index, np.arange(len(substations))
    ].astype(float)
    active_station = station.connected_vre_nameplate_gw.to_numpy(float) > 0
    peak_time = np.full(len(station), "", dtype=object)
    peak_time[active_station] = [
        (
            pd.Timestamp(f"{WEATHER_YEAR}-01-01 08:00:00")
            + pd.Timedelta(hours=int(time_values[index]))
        ).isoformat()
        for index in peak_hour_index[active_station]
    ]
    station["paper_proxy_coincident_peak_trunk_gw"] = coincident_peak
    station["paper_proxy_peak_hour_index"] = np.where(active_station, peak_hour_index, -1)
    station["paper_proxy_peak_time_beijing"] = peak_time
    station["simultaneous_nameplate_trunk_capacity_gw"] = station.connected_vre_nameplate_gw
    station["initial_trunk_capacity_gw"] = station.simultaneous_nameplate_trunk_capacity_gw
    station["initial_substation_vre_interface_capacity_gw"] = station.initial_trunk_capacity_gw
    station["initial_capacity_method"] = "simultaneous_2025_nameplate_stress"
    station["paper_comparator_method"] = "hourly_coincident_peak_from_resolved_2023_cf"
    station["cf_weather_year"] = WEATHER_YEAR
    station["rated_capacity_status"] = (
        "inferred VRE interface requirement; not observed equipment rating"
    )
    station = station.merge(
        substation_center[
            [
                "substation_id",
                "load_center_id",
                "load_center_lon",
                "load_center_lat",
                "trunk_distance_km",
                "assignment_method",
                "route_status",
            ]
        ],
        on="substation_id",
        how="left",
        validate="one_to_one",
    )
    station["candidate_status"] = "paper_route_candidate_not_production_default"

    load_center_capacity = (
        station.groupby("load_center_id", as_index=False)
        .agg(
            connected_substation_count=("substation_id", "size"),
            active_substation_count=("connected_vre_nameplate_gw", lambda values: int((values > 0).sum())),
            connected_vre_nameplate_gw=("connected_vre_nameplate_gw", "sum"),
            existing_dpv_local_gw=("existing_dpv_local_gw", "sum"),
            sum_substation_hourly_coincident_peak_gw=("paper_proxy_coincident_peak_trunk_gw", "sum"),
            simultaneous_nameplate_interface_capacity_gw=("initial_trunk_capacity_gw", "sum"),
        )
        .merge(
            centers[
                [
                    "load_center_id",
                    "province_code",
                    "province_name_en",
                    "province_name_zh",
                    "lon",
                    "lat",
                    "source_scale",
                    "assigned_demand_share_in_province",
                ]
            ],
            on="load_center_id",
            how="right",
            validate="one_to_one",
        )
    )
    numeric_fill = [
        "connected_substation_count",
        "active_substation_count",
        "connected_vre_nameplate_gw",
        "existing_dpv_local_gw",
        "sum_substation_hourly_coincident_peak_gw",
        "simultaneous_nameplate_interface_capacity_gw",
    ]
    load_center_capacity[numeric_fill] = load_center_capacity[numeric_fill].fillna(0.0)
    load_center_capacity["initial_capacity_method"] = "simultaneous_2025_nameplate_stress"
    load_center_capacity["candidate_status"] = "paper_route_candidate_not_production_default"

    province_hourly_parts = []
    province_rows = []
    for province_code, province_stations in station.groupby("province_code", sort=True):
        positions = province_stations.index.to_numpy(int)
        province_hourly = station_hourly[:, positions].sum(axis=1)
        province_hourly_parts.append(province_hourly)
        province_rows.append(
            {
                "province_code": int(province_code),
                "province_name_en": province_stations.province_name_en.iloc[0],
                "province_name_zh": province_stations.province_name_zh.iloc[0],
                "connected_vre_nameplate_gw": float(province_stations.connected_vre_nameplate_gw.sum()),
                "existing_dpv_local_gw": float(province_stations.existing_dpv_local_gw.sum()),
                "sum_substation_hourly_coincident_peak_gw": float(
                    province_stations.paper_proxy_coincident_peak_trunk_gw.sum()
                ),
                "province_coincident_peak_output_gw": float(province_hourly.max()),
                "initial_trunk_capacity_gw": float(province_stations.initial_trunk_capacity_gw.sum()),
                "active_substations": int((province_stations.connected_vre_nameplate_gw > 0).sum()),
                "initial_capacity_method": "simultaneous_2025_nameplate_stress",
                "cf_weather_year": WEATHER_YEAR,
                "candidate_status": "paper_route_candidate_not_production_default",
            }
        )
    province = pd.DataFrame(province_rows)

    spur_path = OUTPUT_DIR / "initial_spur_capacity_2025_paper_route.csv"
    station_path = OUTPUT_DIR / "substation_initial_capacity_2025_paper_route.csv"
    center_path = OUTPUT_DIR / "load_center_initial_capacity_2025.csv"
    province_path = OUTPUT_DIR / "province_initial_intra_grid_capacity_2025_paper_route.csv"
    write_csv(routed, spur_path)
    write_csv(station, station_path)
    write_csv(load_center_capacity, center_path)
    write_csv(province, province_path)

    connected_total = float(station.connected_vre_nameplate_gw.sum())
    dpv_total = float(station.existing_dpv_local_gw.sum())
    checks = [
        {
            "check": "positive_capacity_route_rows",
            "status": "PASS" if len(routed) == len(source_spur) else "HARD_FAIL",
            "value": len(routed),
            "expected": len(source_spur),
        },
        {
            "check": "hour_count",
            "status": "PASS" if station_hourly.shape[0] == 8760 else "HARD_FAIL",
            "value": station_hourly.shape[0],
            "expected": 8760,
        },
        {
            "check": "resolved_cf_peak_reproduction_max_error",
            "status": "PASS" if peak_cf_error <= 1e-6 else "HARD_FAIL",
            "value": peak_cf_error,
            "expected": "<= 1e-6",
        },
        {
            "check": "connected_nameplate_capacity_gw",
            "status": "PASS" if np.isclose(connected_total, 1310.0, atol=1e-6) else "HARD_FAIL",
            "value": connected_total,
            "expected": 1310.0,
        },
        {
            "check": "dpv_local_capacity_gw",
            "status": "PASS" if np.isclose(dpv_total, 530.0, atol=1e-6) else "HARD_FAIL",
            "value": dpv_total,
            "expected": 530.0,
        },
        {
            "check": "coincident_peak_not_above_nameplate",
            "status": "PASS"
            if (station.paper_proxy_coincident_peak_trunk_gw <= station.connected_vre_nameplate_gw + 1e-6).all()
            else "HARD_FAIL",
            "value": float(
                (station.paper_proxy_coincident_peak_trunk_gw - station.connected_vre_nameplate_gw).max()
            ),
            "expected": "<= 1e-6 GW",
        },
        {
            "check": "coincident_peak_not_above_sum_point_peaks",
            "status": "PASS"
            if (station.paper_proxy_coincident_peak_trunk_gw <= station.sum_point_paper_spur_capacity_gw + 1e-6).all()
            else "HARD_FAIL",
            "value": float(
                (station.paper_proxy_coincident_peak_trunk_gw - station.sum_point_paper_spur_capacity_gw).max()
            ),
            "expected": "<= 1e-6 GW",
        },
        {
            "check": "paper_center_rows",
            "status": "PASS" if len(load_center_capacity) == 278 else "HARD_FAIL",
            "value": len(load_center_capacity),
            "expected": 278,
        },
        {
            "check": "province_rows",
            "status": "PASS" if len(province) == 31 else "HARD_FAIL",
            "value": len(province),
            "expected": 31,
        },
    ]
    status = "HARD_FAIL" if any(row["status"] == "HARD_FAIL" for row in checks) else "PASS"
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "candidate_only": True,
        "methods": {
            "default_initial_capacity": "simultaneous 2025 nameplate stress",
            "paper_comparator": "hourly coincident peak from resolved 2023 CF profiles",
            "dpv": "local at load center; excluded from spur/trunk capacity",
            "rated_capacity_status": "inferred requirement, not observed equipment rating",
        },
        "inputs": [
            {"path": str(SOURCE_SPUR_PATH), "sha256": sha256_file(SOURCE_SPUR_PATH)},
            {"path": str(PAPER_ROUTE_PATH), "sha256": sha256_file(PAPER_ROUTE_PATH)},
            {"path": str(PAPER_SUBSTATION_CENTER_PATH), "sha256": sha256_file(PAPER_SUBSTATION_CENTER_PATH)},
            {"path": str(SUBSTATIONS_PATH), "sha256": sha256_file(SUBSTATIONS_PATH)},
            {"path": str(PAPER_MANIFEST_PATH), "sha256": sha256_file(PAPER_MANIFEST_PATH)},
        ],
        "summary": {
            "positive_capacity_point_technology_rows": len(routed),
            "connected_vre_nameplate_gw": connected_total,
            "dpv_local_gw": dpv_total,
            "active_substation_count": int((station.connected_vre_nameplate_gw > 0).sum()),
            "active_load_center_count": int(
                (load_center_capacity.connected_vre_nameplate_gw > 0).sum()
            ),
            "sum_substation_hourly_coincident_peak_gw": float(
                station.paper_proxy_coincident_peak_trunk_gw.sum()
            ),
            "national_hourly_coincident_peak_gw": float(station_hourly.sum(axis=1).max()),
        },
        "checks": checks,
        "outputs": [
            {"path": str(path), "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in (spur_path, station_path, center_path, province_path)
        ],
    }
    summary_path = OUTPUT_DIR / "run_manifest.json"
    with summary_path.open("w", encoding="utf-8") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if status == "HARD_FAIL":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

