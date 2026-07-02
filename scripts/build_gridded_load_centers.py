"""Build candidate load centres from audited 1 km electricity spatial weights.

The outputs are candidates only and never overwrite ``data/grid`` production
files. Absolute raster units are not used: the 2019 raster is normalized within
each covered city, then scaled by the existing city share within its province.
Uncovered cities retain their existing population-weighted point and city share.

Run from the project root with the RL Python environment::

    python scripts/build_gridded_load_centers.py
    python scripts/build_gridded_load_centers.py --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pyproj
import rasterio
import scipy
import sklearn
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "gridded_load_center_config.json"
DATA_ROOT = ROOT / "data"
INPUT_ROOT = DATA_ROOT / "load_centers_1km"
QC_DIR = INPUT_ROOT / "qc"
INTERMEDIATE_DIR = INPUT_ROOT / "intermediate"
CANDIDATE_DIR = INPUT_ROOT / "candidate"
ANNUAL_RASTER_PATH = INTERMEDIATE_DIR / "annual_2019_native_units.tif"
POSITIVE_CELLS_PATH = INTERMEDIATE_DIR / "annual_2019_positive_cells.csv.gz"
COVERAGE_PATH = QC_DIR / "model_city_raster_coverage.csv"
CURRENT_CENTERS_PATH = DATA_ROOT / "grid" / "city_load_centers.csv"
SUBSTATIONS_PATH = DATA_ROOT / "grid" / "substations_osm_220kv_plus.csv"
CURRENT_MAPPING_PATH = DATA_ROOT / "grid" / "substation_to_load_center.csv"
AUDIT_SUMMARY_PATH = QC_DIR / "audit_summary.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and print parameters only.")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def sha256_file(path: Path, chunk_size: int = 4 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(chunk_size):
            digest.update(block)
    return digest.hexdigest()


def write_csv(frame: pd.DataFrame, path: Path, *, compressed: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(
        path,
        index=False,
        encoding="utf-8" if compressed else "utf-8-sig",
        lineterminator="\n",
        compression="gzip" if compressed else None,
    )


def weighted_quantile(values: np.ndarray, weights: np.ndarray, quantile: float) -> float:
    if not 0.0 <= quantile <= 1.0:
        raise ValueError(f"quantile must be in [0, 1], got {quantile}")
    order = np.argsort(values, kind="mergesort")
    sorted_values = values[order]
    sorted_weights = weights[order]
    cumulative = np.cumsum(sorted_weights, dtype=np.float64)
    if cumulative[-1] <= 0:
        raise ValueError("Weighted quantile received non-positive total weight")
    position = int(np.searchsorted(cumulative, quantile * cumulative[-1], side="left"))
    return float(sorted_values[min(position, len(sorted_values) - 1)])


def distance_metrics(distance_km: np.ndarray, weights: np.ndarray) -> dict[str, float]:
    total_weight = float(weights.sum())
    return {
        "weighted_mean_km": float(np.dot(distance_km, weights) / total_weight),
        "weighted_p50_km": weighted_quantile(distance_km, weights, 0.50),
        "weighted_p95_km": weighted_quantile(distance_km, weights, 0.95),
        "weighted_p99_km": weighted_quantile(distance_km, weights, 0.99),
        "maximum_km": float(distance_km.max()),
    }


def build_demand_points(
    cells: pd.DataFrame,
    coverage: pd.DataFrame,
    projected_crs: object,
) -> pd.DataFrame:
    covered = coverage.loc[
        coverage.raster_covered,
        [
            "source_city_code",
            "annual_city_power_share_in_province",
            "annual_2019_native_value",
        ],
    ].copy()
    covered = covered.rename(
        columns={
            "annual_city_power_share_in_province": "city_demand_share_in_province",
            "annual_2019_native_value": "city_annual_2019_native_value",
        }
    )
    raster_points = cells.merge(covered, on="source_city_code", how="inner", validate="many_to_one")
    raster_points["demand_share_in_province"] = (
        raster_points.annual_2019_native_value
        / raster_points.city_annual_2019_native_value
        * raster_points.city_demand_share_in_province
    )
    raster_points["demand_point_id"] = (
        "R_"
        + raster_points.raster_row.astype(int).astype(str).str.zfill(4)
        + "_"
        + raster_points.raster_col.astype(int).astype(str).str.zfill(4)
    )
    raster_points["demand_point_method"] = "2019_raster_normalized_within_city"
    raster_points["fallback_city_lon"] = np.nan
    raster_points["fallback_city_lat"] = np.nan

    uncovered = coverage.loc[
        ~coverage.raster_covered,
        [
            "source_city_code",
            "province_code",
            "province_name_en",
            "province_name_zh",
            "city_name_zh",
            "annual_city_power_share_in_province",
            "lon",
            "lat",
        ],
    ].copy()
    transformer = pyproj.Transformer.from_crs("EPSG:4326", projected_crs, always_xy=True)
    fallback_x, fallback_y = transformer.transform(
        uncovered.lon.to_numpy(float), uncovered.lat.to_numpy(float)
    )
    fallback = pd.DataFrame(
        {
            "raster_row": pd.Series([pd.NA] * len(uncovered), dtype="Int64"),
            "raster_col": pd.Series([pd.NA] * len(uncovered), dtype="Int64"),
            "x_albers_m": fallback_x,
            "y_albers_m": fallback_y,
            "annual_2019_native_value": np.nan,
            "source_city_code": uncovered.source_city_code.to_numpy(),
            "province_code": uncovered.province_code.to_numpy(int),
            "province_name_en": uncovered.province_name_en.to_numpy(),
            "province_name_zh": uncovered.province_name_zh.to_numpy(),
            "city_name_zh": uncovered.city_name_zh.to_numpy(),
            "spatial_assignment_method": "existing_city_center_point",
            "city_demand_share_in_province": uncovered.annual_city_power_share_in_province.to_numpy(float),
            "city_annual_2019_native_value": np.nan,
            "demand_share_in_province": uncovered.annual_city_power_share_in_province.to_numpy(float),
            "demand_point_id": ("F_" + uncovered.source_city_code.astype(str)).to_numpy(),
            "demand_point_method": "uncovered_city_population_weighted_center_fallback",
            "fallback_city_lon": uncovered.lon.to_numpy(float),
            "fallback_city_lat": uncovered.lat.to_numpy(float),
        }
    )

    common_columns = [
        "demand_point_id",
        "province_code",
        "province_name_en",
        "province_name_zh",
        "source_city_code",
        "city_name_zh",
        "demand_point_method",
        "raster_row",
        "raster_col",
        "x_albers_m",
        "y_albers_m",
        "annual_2019_native_value",
        "city_annual_2019_native_value",
        "city_demand_share_in_province",
        "demand_share_in_province",
        "fallback_city_lon",
        "fallback_city_lat",
    ]
    demand_points = pd.concat(
        [raster_points[common_columns], fallback[common_columns]],
        ignore_index=True,
    )
    if demand_points.demand_point_id.duplicated().any():
        raise ValueError("Demand-point IDs are not unique")
    if (demand_points.demand_share_in_province <= 0).any():
        raise ValueError("Demand-point weights must be positive")

    city_closure = (
        demand_points.groupby("source_city_code").demand_share_in_province.sum()
        - coverage.set_index("source_city_code").annual_city_power_share_in_province
    ).abs()
    if float(city_closure.max()) > 1e-10:
        raise ValueError(f"City demand-share closure failed: {city_closure.max()}")
    province_closure = demand_points.groupby("province_code").demand_share_in_province.sum().sub(1.0).abs()
    if float(province_closure.max()) > 1e-10:
        raise ValueError(f"Province demand-share closure failed: {province_closure.max()}")
    return demand_points


def project_substations(substations: pd.DataFrame, projected_crs: object) -> pd.DataFrame:
    transformer = pyproj.Transformer.from_crs("EPSG:4326", projected_crs, always_xy=True)
    x, y = transformer.transform(substations.lon.to_numpy(float), substations.lat.to_numpy(float))
    projected = substations.copy()
    projected["x_albers_m"] = x
    projected["y_albers_m"] = y
    return projected


def snap_centroids_unique(
    centroids: np.ndarray,
    centroid_weights: np.ndarray,
    substations: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    station_xy = substations[["x_albers_m", "y_albers_m"]].to_numpy(float)
    distances = cdist(centroids, station_xy, metric="euclidean")
    centroid_order = np.argsort(-centroid_weights, kind="mergesort")
    used: set[int] = set()
    chosen = np.full(len(centroids), -1, dtype=int)
    for centroid_index in centroid_order:
        for station_index in np.argsort(distances[centroid_index], kind="mergesort"):
            index = int(station_index)
            if index not in used:
                chosen[centroid_index] = index
                used.add(index)
                break
    if (chosen < 0).any():
        raise ValueError("Could not assign a unique eligible substation to every centroid")
    snap_distance_km = distances[np.arange(len(centroids)), chosen] / 1000.0
    return chosen, snap_distance_km


def fit_and_snap(
    coordinates: np.ndarray,
    weights: np.ndarray,
    substations: pd.DataFrame,
    center_count: int,
    random_seed: int,
    n_init: int,
) -> dict:
    model = KMeans(
        n_clusters=center_count,
        random_state=random_seed,
        n_init=n_init,
        algorithm="lloyd",
    )
    labels = model.fit_predict(coordinates, sample_weight=weights)
    centroids = model.cluster_centers_
    centroid_weights = np.bincount(labels, weights=weights, minlength=center_count)
    fitted_distance_km = np.linalg.norm(coordinates - centroids[labels], axis=1) / 1000.0
    chosen_station_positions, snap_distance_km = snap_centroids_unique(
        centroids, centroid_weights, substations
    )
    station_xy = substations.iloc[chosen_station_positions][["x_albers_m", "y_albers_m"]].to_numpy(float)
    snapped_tree = cKDTree(station_xy)
    snapped_distance_m, snapped_labels = snapped_tree.query(coordinates, k=1)
    snapped_distance_km = snapped_distance_m / 1000.0
    snapped_weights = np.bincount(snapped_labels, weights=weights, minlength=center_count)
    active = snapped_weights > 0
    if not active.all():
        station_xy = station_xy[active]
        chosen_station_positions = chosen_station_positions[active]
        centroids = centroids[active]
        snap_distance_km = snap_distance_km[active]
        snapped_tree = cKDTree(station_xy)
        snapped_distance_m, snapped_labels = snapped_tree.query(coordinates, k=1)
        snapped_distance_km = snapped_distance_m / 1000.0
        snapped_weights = np.bincount(snapped_labels, weights=weights, minlength=len(station_xy))
    return {
        "centroids": centroids,
        "chosen_station_positions": chosen_station_positions,
        "centroid_snap_distance_km": snap_distance_km,
        "labels": snapped_labels,
        "center_weights": snapped_weights,
        "fit_metrics": distance_metrics(fitted_distance_km, weights),
        "snapped_metrics": distance_metrics(snapped_distance_km, weights),
    }


def select_center_count(
    coordinates: np.ndarray,
    weights: np.ndarray,
    substations: pd.DataFrame,
    parameters: dict,
) -> tuple[int, dict, list[dict]]:
    maximum = min(
        int(parameters["maximum_centers_per_province"]),
        len(coordinates),
        len(substations),
    )
    target_p95 = float(parameters["target_weighted_p95_distance_km"])
    target_p99 = float(parameters["target_weighted_p99_distance_km"])
    cache: dict[int, dict] = {}
    trace: list[dict] = []

    def evaluate(k: int) -> dict:
        if k not in cache:
            result = fit_and_snap(
                coordinates,
                weights,
                substations,
                k,
                int(parameters["random_seed"]),
                int(parameters["kmeans_n_init"]),
            )
            metrics = result["snapped_metrics"]
            passed = metrics["weighted_p95_km"] <= target_p95 and metrics["weighted_p99_km"] <= target_p99
            result["criteria_met"] = passed
            cache[k] = result
            trace.append(
                {
                    "requested_center_count": k,
                    "active_center_count_after_snap": len(result["center_weights"]),
                    "weighted_p95_km": metrics["weighted_p95_km"],
                    "weighted_p99_km": metrics["weighted_p99_km"],
                    "maximum_km": metrics["maximum_km"],
                    "criteria_met": passed,
                }
            )
        return cache[k]

    lower_fail = 0
    upper_pass: int | None = None
    k = 1
    while True:
        result = evaluate(k)
        if result["criteria_met"]:
            upper_pass = k
            break
        lower_fail = k
        if k >= maximum:
            break
        k = min(maximum, k * 2)

    if upper_pass is None:
        selected = maximum
        return selected, evaluate(selected), trace

    low = lower_fail + 1
    high = upper_pass
    while low < high:
        middle = (low + high) // 2
        if evaluate(middle)["criteria_met"]:
            high = middle
        else:
            low = middle + 1
    selected = low
    return selected, evaluate(selected), trace


def build_candidates(
    demand_points: pd.DataFrame,
    substations: pd.DataFrame,
    parameters: dict,
    projected_crs: object,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    to_wgs84 = pyproj.Transformer.from_crs(projected_crs, "EPSG:4326", always_xy=True)
    candidate_parts: list[pd.DataFrame] = []
    assignment_parts: list[pd.DataFrame] = []
    qc_rows: list[dict] = []
    trace_rows: list[dict] = []

    for province_code, points in demand_points.groupby("province_code", sort=True):
        province_stations = substations.loc[substations.province_code.eq(int(province_code))].reset_index(drop=True)
        if province_stations.empty:
            raise ValueError(f"Province {province_code} has no eligible substation")
        coordinates = points[["x_albers_m", "y_albers_m"]].to_numpy(float)
        weights = points.demand_share_in_province.to_numpy(float)
        selected_k, result, trace = select_center_count(
            coordinates,
            weights,
            province_stations,
            parameters,
        )
        for row in trace:
            trace_rows.append({"province_code": int(province_code), **row})

        selected_stations = province_stations.iloc[result["chosen_station_positions"]].reset_index(drop=True)
        center_weights = result["center_weights"]
        order = np.argsort(-center_weights, kind="mergesort")
        old_to_rank = np.empty(len(order), dtype=int)
        old_to_rank[order] = np.arange(len(order))
        labels_ranked = old_to_rank[result["labels"]]
        selected_stations = selected_stations.iloc[order].reset_index(drop=True)
        center_weights = center_weights[order]
        centroids = result["centroids"][order]
        snap_distance = result["centroid_snap_distance_km"][order]
        centroid_lon, centroid_lat = to_wgs84.transform(centroids[:, 0], centroids[:, 1])

        ids = [f"GLC_{int(province_code):02d}_{index + 1:03d}" for index in range(len(order))]
        centers = pd.DataFrame(
            {
                "load_center_id": ids,
                "province_code": int(province_code),
                "province_name_en": selected_stations.province_name_en.to_numpy(),
                "province_name_zh": selected_stations.province_name_zh.to_numpy(),
                "center_rank_in_province": np.arange(1, len(order) + 1),
                "demand_share_in_province": center_weights,
                "substation_id": selected_stations.substation_id.to_numpy(),
                "substation_lon": selected_stations.lon.to_numpy(float),
                "substation_lat": selected_stations.lat.to_numpy(float),
                "substation_max_voltage_kv": selected_stations.max_voltage_kv.to_numpy(float),
                "substation_name": selected_stations.name.to_numpy(),
                "substation_operator": selected_stations.operator.to_numpy(),
                "cluster_centroid_x_albers_m": centroids[:, 0],
                "cluster_centroid_y_albers_m": centroids[:, 1],
                "cluster_centroid_lon": centroid_lon,
                "cluster_centroid_lat": centroid_lat,
                "centroid_to_substation_distance_km": snap_distance,
                "identification_method": "adaptive_weighted_kmeans_then_unique_220kv_plus_substation_snap",
                "spatial_weight_year": 2019,
                "physical_raster_unit_used": False,
                "candidate_status": "candidate_only_not_production_default",
            }
        )
        candidate_parts.append(centers)

        assignments = points.copy()
        assignments["load_center_id"] = np.asarray(ids, dtype=object)[labels_ranked]
        station_xy = selected_stations[["x_albers_m", "y_albers_m"]].to_numpy(float)
        assignments["distance_to_snapped_load_center_km"] = (
            np.linalg.norm(coordinates - station_xy[labels_ranked], axis=1) / 1000.0
        )
        assignment_parts.append(assignments)

        metrics = result["snapped_metrics"]
        qc_rows.append(
            {
                "province_code": int(province_code),
                "province_name_en": points.province_name_en.iloc[0],
                "province_name_zh": points.province_name_zh.iloc[0],
                "demand_point_count": len(points),
                "raster_demand_point_count": int(points.demand_point_method.str.startswith("2019_raster").sum()),
                "fallback_city_point_count": int(points.demand_point_method.str.startswith("uncovered").sum()),
                "requested_center_count": selected_k,
                "active_center_count": len(centers),
                "target_weighted_p95_km": float(parameters["target_weighted_p95_distance_km"]),
                "target_weighted_p99_km": float(parameters["target_weighted_p99_distance_km"]),
                "weighted_mean_distance_km": metrics["weighted_mean_km"],
                "weighted_p50_distance_km": metrics["weighted_p50_km"],
                "weighted_p95_distance_km": metrics["weighted_p95_km"],
                "weighted_p99_distance_km": metrics["weighted_p99_km"],
                "maximum_distance_km": metrics["maximum_km"],
                "maximum_centroid_to_substation_distance_km": float(snap_distance.max()),
                "demand_share_sum": float(center_weights.sum()),
                "distance_criteria_met": bool(result["criteria_met"]),
                "status": "PASS" if result["criteria_met"] else "WARN_MAXIMUM_CENTER_CAP_REACHED",
            }
        )

    return (
        pd.concat(candidate_parts, ignore_index=True),
        pd.concat(assignment_parts, ignore_index=True),
        pd.DataFrame(qc_rows),
        pd.DataFrame(trace_rows),
    )


def map_substations_to_candidates(
    substations: pd.DataFrame,
    candidates: pd.DataFrame,
) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for province_code, province_stations in substations.groupby("province_code", sort=True):
        centers = candidates.loc[candidates.province_code.eq(int(province_code))].reset_index(drop=True)
        tree = cKDTree(centers[["substation_lon", "substation_lat"]].to_numpy(float))
        # Query in unit-sphere coordinates to avoid longitude/latitude distance distortion.
        station_lon = np.deg2rad(province_stations.lon.to_numpy(float))
        station_lat = np.deg2rad(province_stations.lat.to_numpy(float))
        center_lon = np.deg2rad(centers.substation_lon.to_numpy(float))
        center_lat = np.deg2rad(centers.substation_lat.to_numpy(float))
        station_xyz = np.column_stack(
            [np.cos(station_lat) * np.cos(station_lon), np.cos(station_lat) * np.sin(station_lon), np.sin(station_lat)]
        )
        center_xyz = np.column_stack(
            [np.cos(center_lat) * np.cos(center_lon), np.cos(center_lat) * np.sin(center_lon), np.sin(center_lat)]
        )
        sphere_tree = cKDTree(center_xyz)
        chord, positions = sphere_tree.query(station_xyz, k=1)
        distance_km = 6371.0088 * 2.0 * np.arcsin(np.clip(chord / 2.0, 0.0, 1.0))
        selected = centers.iloc[positions].reset_index(drop=True)
        part = province_stations[
            [
                "substation_id",
                "province_code",
                "province_name_en",
                "province_name_zh",
                "lon",
                "lat",
                "max_voltage_kv",
            ]
        ].reset_index(drop=True)
        part["load_center_id"] = selected.load_center_id.to_numpy()
        part["load_center_substation_id"] = selected.substation_id.to_numpy()
        part["load_center_lon"] = selected.substation_lon.to_numpy(float)
        part["load_center_lat"] = selected.substation_lat.to_numpy(float)
        part["load_center_demand_share_in_province"] = selected.demand_share_in_province.to_numpy(float)
        part["trunk_distance_km"] = distance_km
        part["assignment_method"] = "nearest_gridded_demand_center_substation_within_same_province"
        part["route_status"] = "great_circle_proxy_not_engineering_route"
        parts.append(part)
    return pd.concat(parts, ignore_index=True).sort_values("substation_id").reset_index(drop=True)


def main() -> None:
    args = parse_args()
    config = load_json(CONFIG_PATH)
    parameters = config["load_center_identification"]
    required = [
        AUDIT_SUMMARY_PATH,
        ANNUAL_RASTER_PATH,
        POSITIVE_CELLS_PATH,
        COVERAGE_PATH,
        CURRENT_CENTERS_PATH,
        SUBSTATIONS_PATH,
        CURRENT_MAPPING_PATH,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required inputs:\n" + "\n".join(missing))
    audit_summary = load_json(AUDIT_SUMMARY_PATH)
    if audit_summary["status"] == "HARD_FAIL":
        raise ValueError("Raster audit has HARD_FAIL status; load-centre construction is blocked")

    plan = {
        "status": parameters["status"],
        "inputs": [str(path) for path in required],
        "parameters": parameters,
        "outputs": [
            "intermediate/demand_points_2019_spatial_2022_city_weights.csv.gz",
            "candidate/load_center_candidates.csv",
            "candidate/demand_point_to_load_center.csv.gz",
            "candidate/province_load_center_qc.csv",
            "candidate/center_count_search_trace.csv",
            "candidate/substation_to_load_center_gridded_candidate.csv",
            "candidate/current_vs_gridded_comparison.csv",
            "candidate/run_manifest.json",
        ],
    }
    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return

    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    cells = pd.read_csv(POSITIVE_CELLS_PATH, dtype={"source_city_code": str})
    coverage = pd.read_csv(COVERAGE_PATH, dtype={"source_city_code": str})
    substations = pd.read_csv(SUBSTATIONS_PATH)
    if len(substations) != 6294 or substations.province_code.nunique() != 31:
        raise ValueError("Expected 6,294 eligible substations across 31 provinces")
    if float(substations.max_voltage_kv.min()) < float(parameters["minimum_substation_voltage_kv"]):
        raise ValueError("Substation input contains voltage below configured minimum")

    with rasterio.open(ANNUAL_RASTER_PATH) as annual_dataset:
        projected_crs = annual_dataset.crs
    demand_points = build_demand_points(cells, coverage, projected_crs)
    write_csv(
        demand_points,
        INTERMEDIATE_DIR / "demand_points_2019_spatial_2022_city_weights.csv.gz",
        compressed=True,
    )
    projected_substations = project_substations(substations, projected_crs)
    candidates, assignments, province_qc, search_trace = build_candidates(
        demand_points,
        projected_substations,
        parameters,
        projected_crs,
    )
    mapping = map_substations_to_candidates(projected_substations, candidates)

    write_csv(candidates, CANDIDATE_DIR / "load_center_candidates.csv")
    write_csv(assignments, CANDIDATE_DIR / "demand_point_to_load_center.csv.gz", compressed=True)
    write_csv(province_qc, CANDIDATE_DIR / "province_load_center_qc.csv")
    write_csv(search_trace, CANDIDATE_DIR / "center_count_search_trace.csv")
    write_csv(mapping, CANDIDATE_DIR / "substation_to_load_center_gridded_candidate.csv")

    current_mapping = pd.read_csv(CURRENT_MAPPING_PATH)
    comparison = pd.DataFrame(
        [
            {
                "scenario": "current_every_city_proxy",
                "load_center_count": pd.read_csv(CURRENT_CENTERS_PATH).load_center_id.nunique(),
                "substation_mapping_rows": len(current_mapping),
                "substation_trunk_distance_mean_km": float(current_mapping.trunk_distance_km.mean()),
                "substation_trunk_distance_p95_km": float(current_mapping.trunk_distance_km.quantile(0.95)),
                "substation_trunk_distance_max_km": float(current_mapping.trunk_distance_km.max()),
                "demand_weighted_distance_mean_km": np.nan,
                "demand_weighted_distance_p95_km": np.nan,
                "demand_weighted_distance_p99_km": np.nan,
                "status": "production_proxy_before_gridded_candidate_review",
            },
            {
                "scenario": "gridded_2019_adaptive_weighted_candidate",
                "load_center_count": candidates.load_center_id.nunique(),
                "substation_mapping_rows": len(mapping),
                "substation_trunk_distance_mean_km": float(mapping.trunk_distance_km.mean()),
                "substation_trunk_distance_p95_km": float(mapping.trunk_distance_km.quantile(0.95)),
                "substation_trunk_distance_max_km": float(mapping.trunk_distance_km.max()),
                "demand_weighted_distance_mean_km": float(
                    np.average(
                        assignments.distance_to_snapped_load_center_km,
                        weights=assignments.demand_share_in_province,
                    )
                ),
                "demand_weighted_distance_p95_km": weighted_quantile(
                    assignments.distance_to_snapped_load_center_km.to_numpy(float),
                    assignments.demand_share_in_province.to_numpy(float),
                    0.95,
                ),
                "demand_weighted_distance_p99_km": weighted_quantile(
                    assignments.distance_to_snapped_load_center_km.to_numpy(float),
                    assignments.demand_share_in_province.to_numpy(float),
                    0.99,
                ),
                "status": "candidate_only_not_production_default",
            },
        ]
    )
    write_csv(comparison, CANDIDATE_DIR / "current_vs_gridded_comparison.csv")

    checks = [
        {
            "check": "province_count",
            "status": "PASS" if candidates.province_code.nunique() == 31 else "HARD_FAIL",
            "value": int(candidates.province_code.nunique()),
            "expected": 31,
        },
        {
            "check": "candidate_substation_unique",
            "status": "PASS" if not candidates.substation_id.duplicated().any() else "HARD_FAIL",
            "value": int(candidates.substation_id.nunique()),
            "expected": len(candidates),
        },
        {
            "check": "province_demand_share_closure",
            "status": "PASS"
            if float(candidates.groupby("province_code").demand_share_in_province.sum().sub(1.0).abs().max()) <= 1e-10
            else "HARD_FAIL",
            "value": float(candidates.groupby("province_code").demand_share_in_province.sum().sub(1.0).abs().max()),
            "expected": "<= 1e-10",
        },
        {
            "check": "distance_criteria_all_provinces",
            "status": "PASS" if province_qc.distance_criteria_met.all() else "WARN",
            "value": int(province_qc.distance_criteria_met.sum()),
            "expected": 31,
        },
        {
            "check": "substation_mapping_complete",
            "status": "PASS" if len(mapping) == len(substations) else "HARD_FAIL",
            "value": len(mapping),
            "expected": len(substations),
        },
        {
            "check": "physical_raster_unit_not_used",
            "status": "PASS" if not candidates.physical_raster_unit_used.any() else "HARD_FAIL",
            "value": bool(candidates.physical_raster_unit_used.any()),
            "expected": False,
        },
    ]
    status = (
        "HARD_FAIL"
        if any(check["status"] == "HARD_FAIL" for check in checks)
        else "PASS_WITH_WARNINGS"
        if any(check["status"] == "WARN" for check in checks)
        else "PASS"
    )
    output_paths = [CANDIDATE_DIR / relative.split("candidate/")[-1] for relative in plan["outputs"] if relative.startswith("candidate/")]
    manifest = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "scenario": "gridded_2019_adaptive_weighted_candidate",
        "candidate_only": True,
        "parameters": parameters,
        "input_lineage": {
            "raster_audit_summary": str(AUDIT_SUMMARY_PATH),
            "raster_audit_status": audit_summary["status"],
            "positive_cells_sha256": sha256_file(POSITIVE_CELLS_PATH),
            "city_coverage_sha256": sha256_file(COVERAGE_PATH),
            "city_weights_sha256": sha256_file(CURRENT_CENTERS_PATH),
            "substations_sha256": sha256_file(SUBSTATIONS_PATH),
            "method_config_sha256": sha256_file(CONFIG_PATH),
        },
        "transformations": [
            "normalize 2019 native raster values within each of 280 covered cities",
            "scale within-city cells by existing city demand share within province",
            "represent each of 57 uncovered cities by its existing population-weighted center and demand share",
            "verify city and province demand-share closure",
            "select center count per province by adaptive weighted KMeans distance criteria",
            "snap centers to unique OSM substations at 220 kV or above",
            "reassign demand points to snapped centers and recompute demand shares",
            "map every eligible substation to the nearest candidate load center within the same province",
        ],
        "software": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "rasterio": rasterio.__version__,
            "pyproj": pyproj.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "summary": {
            "demand_point_count": len(demand_points),
            "raster_demand_point_count": int(demand_points.demand_point_method.str.startswith("2019_raster").sum()),
            "fallback_city_point_count": int(demand_points.demand_point_method.str.startswith("uncovered").sum()),
            "candidate_load_center_count": len(candidates),
            "province_count": int(candidates.province_code.nunique()),
            "eligible_substation_count": len(substations),
        },
        "checks": checks,
        "outputs": [
            {
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in output_paths
            if path.exists() and path.name != "run_manifest.json"
        ],
    }
    with (CANDIDATE_DIR / "run_manifest.json").open("w", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    if status == "HARD_FAIL":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
