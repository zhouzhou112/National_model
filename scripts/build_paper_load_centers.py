"""Reconstruct the paper-faithful CISPO load centers and grid routes.

Structural load-center definition:

* centroids of Natural Earth 1:50m urban-area polygons in the 31-province model;
* additional Natural Earth 1:10m urban-area centroids in Tibet;
* OSM substations at 220 kV or above;
* exact within-province minimization of grid-to-substation spur distance plus
  substation-to-nearest-load-center trunk distance.

The audited 2019 1 km electricity grid is used only as a normalized spatial
demand distribution for validation and center importance. Its unconfirmed
physical unit is never converted or used as absolute energy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyproj
import rasterio
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data"
METHOD_CONFIG_PATH = ROOT / "config" / "gridded_load_center_config.json"
MODEL_CONFIG_PATH = ROOT / "config" / "model_data_config.json"
LOAD_ROOT = DATA_ROOT / "load_centers_1km"
QC_DIR = LOAD_ROOT / "qc"
INTERMEDIATE_DIR = LOAD_ROOT / "intermediate"
OUTPUT_DIR = LOAD_ROOT / "paper_method_candidate"
NE_ROOT = DATA_ROOT / "raw" / "natural_earth_urban_areas"
NE50_PATH = NE_ROOT / "extracted" / "ne_50m_urban_areas" / "ne_50m_urban_areas.shp"
NE10_PATH = NE_ROOT / "extracted" / "ne_10m_urban_areas" / "ne_10m_urban_areas.shp"
NE50_ZIP = NE_ROOT / "source" / "ne_50m_urban_areas.zip"
NE10_ZIP = NE_ROOT / "source" / "ne_10m_urban_areas.zip"
POSITIVE_CELLS_PATH = INTERMEDIATE_DIR / "annual_2019_positive_cells.csv.gz"
COVERAGE_PATH = QC_DIR / "model_city_raster_coverage.csv"
ANNUAL_RASTER_PATH = INTERMEDIATE_DIR / "annual_2019_native_units.tif"
CURRENT_CENTERS_PATH = DATA_ROOT / "grid" / "city_load_centers.csv"
SUBSTATIONS_PATH = DATA_ROOT / "grid" / "substations_osm_220kv_plus.csv"
ORIGINAL_GRID_POINTS_PATH = DATA_ROOT / "vre" / "optimization_points.csv"
GRID_POINTS_PATH = (
    INTERMEDIATE_DIR / "optimization_points_spatially_validated_candidate.csv"
)
PROVINCE_AUDIT_SUMMARY_PATH = QC_DIR / "land_point_province_audit_summary.json"
CURRENT_GRID_ROUTE_PATH = DATA_ROOT / "grid" / "grid_connection_by_point.csv"
CURRENT_SUBSTATION_CENTER_PATH = DATA_ROOT / "grid" / "substation_to_load_center.csv"
AUDIT_SUMMARY_PATH = QC_DIR / "audit_summary.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and print the plan.")
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


def write_or_verify_geojson(frame: gpd.GeoDataFrame, path: Path) -> None:
    """Write a stable GeoJSON, or reuse it only after geometry identity checks."""
    if not path.exists():
        frame.to_file(path, driver="GeoJSON")
        return
    existing = gpd.read_file(path).to_crs(frame.crs)
    if len(existing) != len(frame) or "load_center_id" not in existing.columns:
        raise ValueError(f"Existing locked GeoJSON has incompatible schema/count: {path}")
    existing = existing.sort_values("load_center_id").reset_index(drop=True)
    current = frame.sort_values("load_center_id").reset_index(drop=True)
    if not existing.load_center_id.equals(current.load_center_id):
        raise ValueError(f"Existing locked GeoJSON has different load-center IDs: {path}")
    geometry_delta = np.array(
        [left.hausdorff_distance(right) for left, right in zip(existing.geometry, current.geometry)]
    )
    if geometry_delta.max(initial=0.0) > 1e-7:
        raise ValueError(
            f"Existing locked GeoJSON geometry differs from current result: {path}; "
            f"max Hausdorff distance={geometry_delta.max()}"
        )


def weighted_quantile(values: np.ndarray, weights: np.ndarray, quantile: float) -> float:
    order = np.argsort(values, kind="mergesort")
    ordered_values = values[order]
    cumulative = np.cumsum(weights[order], dtype=np.float64)
    index = int(np.searchsorted(cumulative, quantile * cumulative[-1], side="left"))
    return float(ordered_values[min(index, len(ordered_values) - 1)])


def lonlat_to_unit_sphere(lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
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
    xyz_a = lonlat_to_unit_sphere(lon_a, lat_a)
    xyz_b = lonlat_to_unit_sphere(lon_b, lat_b)
    cosine = np.clip(xyz_a @ xyz_b.T, -1.0, 1.0)
    return 6371.0088 * np.arccos(cosine)


def load_city_polygons(model_config: dict, projected_crs: object) -> gpd.GeoDataFrame:
    centers = pd.read_csv(
        CURRENT_CENTERS_PATH,
        dtype={"source_city_code": str},
    )[
        [
            "source_city_code",
            "province_code",
            "province_name_en",
            "province_name_zh",
            "city_name_zh",
        ]
    ]
    polygons = gpd.read_file(model_config["sources"]["city_boundary_shapefile"])
    polygons["source_city_code"] = polygons["gb"].astype(str).str.strip()
    polygons = polygons.loc[polygons.source_city_code.isin(centers.source_city_code)].copy()
    polygons = polygons[["source_city_code", "geometry"]].dissolve(
        by="source_city_code", as_index=False
    )
    polygons = polygons.merge(centers, on="source_city_code", how="inner", validate="one_to_one")
    if len(polygons) != 337:
        raise ValueError(f"Expected 337 model city polygons, found {len(polygons)}")
    polygons = polygons.to_crs(projected_crs)
    polygons["city_polygon_area_km2_projected"] = polygons.geometry.area / 1e6
    return polygons


def assign_centroids_to_cities(
    urban_polygons: gpd.GeoDataFrame,
    city_polygons: gpd.GeoDataFrame,
    source_scale: str,
) -> gpd.GeoDataFrame:
    urban = urban_polygons.copy()
    urban["source_feature_index"] = urban.index.astype(int)
    urban["urban_geometry"] = urban.geometry
    urban["geometry"] = urban.geometry.centroid
    joined = gpd.sjoin(
        urban,
        city_polygons[
            [
                "source_city_code",
                "province_code",
                "province_name_en",
                "province_name_zh",
                "city_name_zh",
                "city_polygon_area_km2_projected",
                "geometry",
            ]
        ],
        how="inner",
        predicate="within",
    )
    if joined.index.duplicated().any():
        joined = (
            joined.sort_values("city_polygon_area_km2_projected")
            .loc[lambda frame: ~frame.index.duplicated(keep="first")]
        )
    joined["source_scale"] = source_scale
    joined["centroid_within_urban_polygon"] = [
        polygon.covers(point)
        for polygon, point in zip(joined.urban_geometry, joined.geometry)
    ]
    return joined


def build_paper_centers(
    city_polygons: gpd.GeoDataFrame,
    projected_crs: object,
    paper_config: dict,
) -> tuple[pd.DataFrame, gpd.GeoDataFrame]:
    ne50 = gpd.read_file(NE50_PATH).to_crs(projected_crs)
    selected50 = assign_centroids_to_cities(ne50, city_polygons, "Natural_Earth_1_50m")

    tibet_cities = city_polygons.loc[city_polygons.province_code.eq(54)]
    ne10 = gpd.read_file(NE10_PATH).to_crs(projected_crs)
    selected10 = assign_centroids_to_cities(ne10, tibet_cities, "Natural_Earth_1_10m_Tibet_supplement")
    selected = pd.concat([selected50, selected10], ignore_index=True)
    selected = gpd.GeoDataFrame(selected, geometry="geometry", crs=projected_crs)

    expected50 = int(paper_config["expected_50m_china_center_count_current_snapshot"])
    expected10 = int(paper_config["expected_10m_tibet_additional_center_count_current_snapshot"])
    if len(selected50) != expected50 or len(selected10) != expected10:
        raise ValueError(
            f"Natural Earth snapshot count mismatch: 50m={len(selected50)} expected {expected50}, "
            f"10m Tibet={len(selected10)} expected {expected10}"
        )
    if selected.province_code.nunique() != 31:
        missing = sorted(set(range(31)) - set(selected.province_code.unique()))
        raise ValueError(f"Paper centers do not cover 31 provinces; diagnostic={missing}")

    selected = selected.sort_values(
        ["province_code", "source_scale", "source_feature_index"]
    ).reset_index(drop=True)
    selected["load_center_id"] = [
        f"PLC_{int(province):02d}_{rank:03d}"
        for province, rank in zip(
            selected.province_code,
            selected.groupby("province_code").cumcount() + 1,
        )
    ]
    selected["x_albers_m"] = selected.geometry.x
    selected["y_albers_m"] = selected.geometry.y
    to_wgs84 = pyproj.Transformer.from_crs(projected_crs, "EPSG:4326", always_xy=True)
    lon, lat = to_wgs84.transform(selected.x_albers_m.to_numpy(), selected.y_albers_m.to_numpy())
    selected["lon"] = lon
    selected["lat"] = lat
    selected["urban_area_sqkm_attribute"] = pd.to_numeric(selected["area_sqkm"], errors="coerce")
    selected["urban_area_sqkm_projected"] = selected.urban_geometry.map(lambda geom: geom.area / 1e6)
    selected["centroid_crs_method"] = paper_config["centroid_crs_method"]
    selected["paper_method"] = (
        "centroid of Natural Earth urban area; 1:50m nationwide plus 1:10m Tibet supplement"
    )
    selected["candidate_status"] = paper_config["candidate_status"]

    center_columns = [
        "load_center_id",
        "source_scale",
        "source_feature_index",
        "province_code",
        "province_name_en",
        "province_name_zh",
        "source_city_code",
        "city_name_zh",
        "lon",
        "lat",
        "x_albers_m",
        "y_albers_m",
        "urban_area_sqkm_attribute",
        "urban_area_sqkm_projected",
        "centroid_within_urban_polygon",
        "centroid_crs_method",
        "paper_method",
        "candidate_status",
    ]
    centers = pd.DataFrame(selected[center_columns]).copy()
    urban_output = selected[
        [
            "load_center_id",
            "source_scale",
            "source_feature_index",
            "province_code",
            "province_name_en",
            "province_name_zh",
            "source_city_code",
            "city_name_zh",
            "urban_geometry",
        ]
    ].copy()
    urban_output = urban_output.set_geometry("urban_geometry").to_crs("EPSG:4326")
    return centers, urban_output


def build_demand_points(
    cells: pd.DataFrame,
    coverage: pd.DataFrame,
    projected_crs: object,
) -> pd.DataFrame:
    covered = coverage.loc[
        coverage.raster_covered,
        ["source_city_code", "annual_city_power_share_in_province", "annual_2019_native_value"],
    ].rename(
        columns={
            "annual_city_power_share_in_province": "city_demand_share_in_province",
            "annual_2019_native_value": "city_native_total",
        }
    )
    raster_points = cells.merge(covered, on="source_city_code", how="inner", validate="many_to_one")
    raster_points["demand_share_in_province"] = (
        raster_points.annual_2019_native_value
        / raster_points.city_native_total
        * raster_points.city_demand_share_in_province
    )
    raster_points["demand_point_id"] = (
        "R_"
        + raster_points.raster_row.astype(int).astype(str).str.zfill(4)
        + "_"
        + raster_points.raster_col.astype(int).astype(str).str.zfill(4)
    )
    raster_points["demand_point_method"] = "2019_raster_normalized_within_city"

    uncovered = coverage.loc[~coverage.raster_covered].copy()
    transformer = pyproj.Transformer.from_crs("EPSG:4326", projected_crs, always_xy=True)
    fallback_x, fallback_y = transformer.transform(
        uncovered.lon.to_numpy(float), uncovered.lat.to_numpy(float)
    )
    fallback = pd.DataFrame(
        {
            "demand_point_id": ("F_" + uncovered.source_city_code.astype(str)).to_numpy(),
            "province_code": uncovered.province_code.to_numpy(int),
            "province_name_en": uncovered.province_name_en.to_numpy(),
            "province_name_zh": uncovered.province_name_zh.to_numpy(),
            "source_city_code": uncovered.source_city_code.to_numpy(),
            "city_name_zh": uncovered.city_name_zh.to_numpy(),
            "x_albers_m": fallback_x,
            "y_albers_m": fallback_y,
            "demand_share_in_province": uncovered.annual_city_power_share_in_province.to_numpy(float),
            "demand_point_method": "uncovered_city_population_weighted_center_fallback",
        }
    )
    columns = [
        "demand_point_id",
        "province_code",
        "province_name_en",
        "province_name_zh",
        "source_city_code",
        "city_name_zh",
        "x_albers_m",
        "y_albers_m",
        "demand_share_in_province",
        "demand_point_method",
    ]
    demand = pd.concat([raster_points[columns], fallback[columns]], ignore_index=True)
    closure = demand.groupby("province_code").demand_share_in_province.sum().sub(1.0).abs()
    if closure.max() > 1e-10:
        raise ValueError(f"Province demand-share closure failed: {closure.max()}")
    return demand


def assign_demand_to_centers(
    demand: pd.DataFrame,
    centers: pd.DataFrame,
    projected_crs: object,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    assignment_parts: list[pd.DataFrame] = []
    center_parts: list[pd.DataFrame] = []
    province_rows: list[dict] = []
    to_wgs84 = pyproj.Transformer.from_crs(projected_crs, "EPSG:4326", always_xy=True)
    for province_code, points in demand.groupby("province_code", sort=True):
        province_centers = centers.loc[centers.province_code.eq(int(province_code))].reset_index(drop=True)
        point_xy = points[["x_albers_m", "y_albers_m"]].to_numpy(float)
        center_xy = province_centers[["x_albers_m", "y_albers_m"]].to_numpy(float)
        tree = cKDTree(center_xy)
        distance_m, positions = tree.query(point_xy, k=1)
        weights = points.demand_share_in_province.to_numpy(float)
        center_weights = np.bincount(positions, weights=weights, minlength=len(province_centers))
        weighted_x = np.bincount(
            positions, weights=weights * point_xy[:, 0], minlength=len(province_centers)
        )
        weighted_y = np.bincount(
            positions, weights=weights * point_xy[:, 1], minlength=len(province_centers)
        )
        supported = center_weights > 0
        weighted_x[supported] /= center_weights[supported]
        weighted_y[supported] /= center_weights[supported]
        weighted_x[~supported] = np.nan
        weighted_y[~supported] = np.nan
        weighted_lon, weighted_lat = to_wgs84.transform(weighted_x, weighted_y)

        center_part = province_centers.copy()
        center_part["assigned_demand_share_in_province"] = center_weights
        center_part["assigned_demand_point_count"] = np.bincount(
            positions, minlength=len(province_centers)
        )
        center_part["assigned_demand_weighted_x_albers_m"] = weighted_x
        center_part["assigned_demand_weighted_y_albers_m"] = weighted_y
        center_part["assigned_demand_weighted_lon"] = weighted_lon
        center_part["assigned_demand_weighted_lat"] = weighted_lat
        center_part["demand_weight_role"] = (
            "validation_and_importance_only_paper_center_remains_geometric_centroid"
        )
        center_parts.append(center_part)

        assignments = points.copy()
        assignments["load_center_id"] = province_centers.iloc[positions].load_center_id.to_numpy()
        assignments["distance_to_paper_center_km"] = distance_m / 1000.0
        assignments["assignment_method"] = "nearest_paper_defined_center_within_same_province"
        assignment_parts.append(assignments)

        distance_km = distance_m / 1000.0
        province_rows.append(
            {
                "province_code": int(province_code),
                "province_name_en": points.province_name_en.iloc[0],
                "province_name_zh": points.province_name_zh.iloc[0],
                "load_center_count": len(province_centers),
                "demand_supported_center_count": int(supported.sum()),
                "zero_assigned_demand_center_count": int((~supported).sum()),
                "demand_point_count": len(points),
                "fallback_city_point_count": int(points.demand_point_method.str.startswith("uncovered").sum()),
                "demand_share_sum": float(center_weights.sum()),
                "demand_weighted_mean_distance_to_center_km": float(np.dot(distance_km, weights)),
                "demand_weighted_p95_distance_to_center_km": weighted_quantile(distance_km, weights, 0.95),
                "demand_weighted_p99_distance_to_center_km": weighted_quantile(distance_km, weights, 0.99),
                "maximum_distance_to_center_km": float(distance_km.max()),
            }
        )
    return (
        pd.concat(center_parts, ignore_index=True),
        pd.concat(assignment_parts, ignore_index=True),
        pd.DataFrame(province_rows),
    )


def build_paper_routes(
    grid_points: pd.DataFrame,
    substations: pd.DataFrame,
    centers: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    substation_parts: list[pd.DataFrame] = []
    route_parts: list[pd.DataFrame] = []
    for province_code, province_points in grid_points.groupby("province_code", sort=True):
        province_substations = substations.loc[
            substations.province_code.eq(int(province_code))
        ].reset_index(drop=True)
        province_centers = centers.loc[
            centers.province_code.eq(int(province_code))
        ].reset_index(drop=True)
        if province_substations.empty or province_centers.empty:
            raise ValueError(f"Province {province_code} lacks substations or paper centers")

        trunk_matrix = great_circle_matrix_km(
            province_substations.lon.to_numpy(float),
            province_substations.lat.to_numpy(float),
            province_centers.lon.to_numpy(float),
            province_centers.lat.to_numpy(float),
        )
        nearest_center_position = trunk_matrix.argmin(axis=1)
        nearest_trunk_km = trunk_matrix[
            np.arange(len(province_substations)), nearest_center_position
        ]
        chosen_centers = province_centers.iloc[nearest_center_position].reset_index(drop=True)
        sub_part = province_substations[
            [
                "substation_id",
                "province_code",
                "province_name_en",
                "province_name_zh",
                "lon",
                "lat",
                "max_voltage_kv",
            ]
        ].copy()
        sub_part["load_center_id"] = chosen_centers.load_center_id.to_numpy()
        sub_part["load_center_lon"] = chosen_centers.lon.to_numpy(float)
        sub_part["load_center_lat"] = chosen_centers.lat.to_numpy(float)
        sub_part["trunk_distance_km"] = nearest_trunk_km
        sub_part["assignment_method"] = "nearest_paper_urban_center_within_same_province"
        sub_part["route_status"] = "great_circle_proxy_not_engineering_route"
        substation_parts.append(sub_part)

        points = province_points.reset_index(drop=True)
        selected_station_position = np.empty(len(points), dtype=int)
        selected_spur_km = np.empty(len(points), dtype=float)
        chunk_size = 2000
        for start in range(0, len(points), chunk_size):
            stop = min(start + chunk_size, len(points))
            spur_matrix = great_circle_matrix_km(
                points.lon.iloc[start:stop].to_numpy(float),
                points.lat.iloc[start:stop].to_numpy(float),
                province_substations.lon.to_numpy(float),
                province_substations.lat.to_numpy(float),
            )
            objective = spur_matrix + nearest_trunk_km[None, :]
            positions = objective.argmin(axis=1)
            selected_station_position[start:stop] = positions
            selected_spur_km[start:stop] = spur_matrix[
                np.arange(stop - start), positions
            ]
        chosen_substations = province_substations.iloc[selected_station_position].reset_index(drop=True)
        selected_center_position = nearest_center_position[selected_station_position]
        chosen_load_centers = province_centers.iloc[selected_center_position].reset_index(drop=True)
        selected_trunk_km = nearest_trunk_km[selected_station_position]

        route = points[
            [
                "grid_uid",
                "grid_id",
                "province_code",
                "province_name_en",
                "province_name_zh",
                "lon",
                "lat",
                "is_land",
            ]
        ].copy()
        route["substation_id"] = chosen_substations.substation_id.to_numpy()
        route["substation_lon"] = chosen_substations.lon.to_numpy(float)
        route["substation_lat"] = chosen_substations.lat.to_numpy(float)
        route["substation_max_voltage_kv"] = chosen_substations.max_voltage_kv.to_numpy(float)
        route["load_center_id"] = chosen_load_centers.load_center_id.to_numpy()
        route["load_center_lon"] = chosen_load_centers.lon.to_numpy(float)
        route["load_center_lat"] = chosen_load_centers.lat.to_numpy(float)
        route["spur_distance_km"] = selected_spur_km
        route["trunk_distance_km"] = selected_trunk_km
        route["total_connection_distance_km"] = selected_spur_km + selected_trunk_km
        route["onwind_spur_distance_km"] = selected_spur_km
        route["onwind_trunk_distance_km"] = selected_trunk_km
        route["upv_spur_distance_km"] = selected_spur_km
        route["upv_trunk_distance_km"] = selected_trunk_km
        route["offwind_export_distance_km"] = selected_spur_km
        route["offwind_trunk_distance_km"] = selected_trunk_km
        route["dpv_spur_distance_km"] = 0.0
        route["dpv_trunk_distance_km"] = 0.0
        route["matching_objective"] = (
            "exact minimum over eligible same-province substations of geodesic spur plus "
            "substation-to-nearest-paper-center trunk distance"
        )
        route["power_grid_scope"] = "31_provinces_inner_mongolia_merged"
        route["route_status"] = "great_circle_proxy_not_engineering_route"
        route_parts.append(route)

    return (
        pd.concat(substation_parts, ignore_index=True).sort_values("substation_id").reset_index(drop=True),
        pd.concat(route_parts, ignore_index=True).sort_values("grid_uid").reset_index(drop=True),
    )


def build_comparison(paper_route: pd.DataFrame) -> pd.DataFrame:
    current_grid = pd.read_csv(CURRENT_GRID_ROUTE_PATH)
    current_sub = pd.read_csv(CURRENT_SUBSTATION_CENTER_PATH)[
        ["substation_id", "trunk_distance_km"]
    ].rename(columns={"trunk_distance_km": "current_trunk_distance_km"})
    current = current_grid.merge(current_sub, on="substation_id", how="left", validate="many_to_one")
    current["current_total_connection_distance_km"] = (
        current.nearest_substation_distance_km + current.current_trunk_distance_km
    )
    merged = paper_route[
        ["grid_uid", "spur_distance_km", "trunk_distance_km", "total_connection_distance_km"]
    ].merge(
        current[
            [
                "grid_uid",
                "nearest_substation_distance_km",
                "current_trunk_distance_km",
                "current_total_connection_distance_km",
            ]
        ],
        on="grid_uid",
        how="inner",
        validate="one_to_one",
    )
    rows = []
    for scenario, spur, trunk, total in (
        (
            "current_city_proxy_nearest_substation",
            merged.nearest_substation_distance_km,
            merged.current_trunk_distance_km,
            merged.current_total_connection_distance_km,
        ),
        (
            "paper_natural_earth_minimum_total_distance",
            merged.spur_distance_km,
            merged.trunk_distance_km,
            merged.total_connection_distance_km,
        ),
    ):
        rows.append(
            {
                "scenario": scenario,
                "grid_point_count": len(merged),
                "spur_mean_km": float(spur.mean()),
                "spur_p95_km": float(spur.quantile(0.95)),
                "trunk_mean_km": float(trunk.mean()),
                "trunk_p95_km": float(trunk.quantile(0.95)),
                "total_mean_km": float(total.mean()),
                "total_p95_km": float(total.quantile(0.95)),
                "total_max_km": float(total.max()),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    method_config = load_json(METHOD_CONFIG_PATH)
    model_config = load_json(MODEL_CONFIG_PATH)
    paper_config = method_config["paper_reconstruction"]
    required = [
        NE50_PATH,
        NE10_PATH,
        NE50_ZIP,
        NE10_ZIP,
        POSITIVE_CELLS_PATH,
        COVERAGE_PATH,
        ANNUAL_RASTER_PATH,
        CURRENT_CENTERS_PATH,
        SUBSTATIONS_PATH,
        GRID_POINTS_PATH,
        CURRENT_GRID_ROUTE_PATH,
        CURRENT_SUBSTATION_CENTER_PATH,
        AUDIT_SUMMARY_PATH,
        PROVINCE_AUDIT_SUMMARY_PATH,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required inputs:\n" + "\n".join(missing))
    audit_summary = load_json(AUDIT_SUMMARY_PATH)
    if audit_summary["status"] == "HARD_FAIL":
        raise ValueError("1 km electricity-grid audit has HARD_FAIL status")
    province_audit_summary = load_json(PROVINCE_AUDIT_SUMMARY_PATH)
    if province_audit_summary["status"] != "PASS":
        raise ValueError("Land-point province spatial audit has not passed")

    plan = {
        "paper_method": paper_config,
        "inputs": [str(path) for path in required],
        "outputs": [
            "paper_load_centers.csv",
            "paper_load_centers.geojson",
            "paper_urban_areas.geojson",
            "demand_point_to_paper_load_center.csv.gz",
            "substation_to_paper_load_center.csv",
            "grid_point_paper_route.csv",
            "province_summary.csv",
            "current_vs_paper_route_comparison.csv",
            "run_manifest.json",
        ],
    }
    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with rasterio.open(ANNUAL_RASTER_PATH) as dataset:
        projected_crs = dataset.crs
    city_polygons = load_city_polygons(model_config, projected_crs)
    centers, urban_areas = build_paper_centers(city_polygons, projected_crs, paper_config)

    cells = pd.read_csv(POSITIVE_CELLS_PATH, dtype={"source_city_code": str})
    coverage = pd.read_csv(COVERAGE_PATH, dtype={"source_city_code": str})
    demand = build_demand_points(cells, coverage, projected_crs)
    centers, demand_assignment, province_demand_qc = assign_demand_to_centers(
        demand, centers, projected_crs
    )

    substations = pd.read_csv(SUBSTATIONS_PATH)
    grid_points = pd.read_csv(GRID_POINTS_PATH)
    substation_mapping, paper_route = build_paper_routes(grid_points, substations, centers)
    comparison = build_comparison(paper_route)

    route_summary = (
        paper_route.groupby(
            ["province_code", "province_name_en", "province_name_zh"], as_index=False
        )
        .agg(
            grid_point_count=("grid_uid", "size"),
            selected_substation_count=("substation_id", "nunique"),
            spur_mean_km=("spur_distance_km", "mean"),
            spur_p95_km=("spur_distance_km", lambda values: float(values.quantile(0.95))),
            trunk_mean_km=("trunk_distance_km", "mean"),
            trunk_p95_km=("trunk_distance_km", lambda values: float(values.quantile(0.95))),
            total_mean_km=("total_connection_distance_km", "mean"),
            total_p95_km=("total_connection_distance_km", lambda values: float(values.quantile(0.95))),
            total_max_km=("total_connection_distance_km", "max"),
        )
    )
    scale_counts = (
        centers.pivot_table(
            index=["province_code", "province_name_en", "province_name_zh"],
            columns="source_scale",
            values="load_center_id",
            aggfunc="count",
            fill_value=0,
        )
        .reset_index()
    )
    province_summary = province_demand_qc.merge(
        scale_counts,
        on=["province_code", "province_name_en", "province_name_zh"],
        how="left",
        validate="one_to_one",
    ).merge(
        route_summary,
        on=["province_code", "province_name_en", "province_name_zh"],
        how="left",
        validate="one_to_one",
    )

    write_csv(centers, OUTPUT_DIR / "paper_load_centers.csv")
    center_points = gpd.GeoDataFrame(
        centers.copy(),
        geometry=gpd.points_from_xy(centers.lon, centers.lat),
        crs="EPSG:4326",
    )
    write_or_verify_geojson(center_points, OUTPUT_DIR / "paper_load_centers.geojson")
    write_or_verify_geojson(urban_areas, OUTPUT_DIR / "paper_urban_areas.geojson")
    write_csv(
        demand_assignment,
        OUTPUT_DIR / "demand_point_to_paper_load_center.csv.gz",
        compressed=True,
    )
    write_csv(substation_mapping, OUTPUT_DIR / "substation_to_paper_load_center.csv")
    write_csv(paper_route, OUTPUT_DIR / "grid_point_paper_route.csv")
    write_csv(province_summary, OUTPUT_DIR / "province_summary.csv")
    write_csv(comparison, OUTPUT_DIR / "current_vs_paper_route_comparison.csv")

    paper_center_count = len(centers)
    expected_center_count = int(paper_config["expected_total_center_count_current_snapshot"])
    checks = [
        {
            "check": "paper_load_center_count",
            "status": "PASS" if paper_center_count == expected_center_count else "HARD_FAIL",
            "value": paper_center_count,
            "expected": expected_center_count,
        },
        {
            "check": "province_coverage",
            "status": "PASS" if centers.province_code.nunique() == 31 else "HARD_FAIL",
            "value": int(centers.province_code.nunique()),
            "expected": 31,
        },
        {
            "check": "tibet_10m_supplement_count",
            "status": "PASS"
            if int(centers.source_scale.eq("Natural_Earth_1_10m_Tibet_supplement").sum())
            == int(paper_config["expected_10m_tibet_additional_center_count_current_snapshot"])
            else "HARD_FAIL",
            "value": int(centers.source_scale.eq("Natural_Earth_1_10m_Tibet_supplement").sum()),
            "expected": int(paper_config["expected_10m_tibet_additional_center_count_current_snapshot"]),
        },
        {
            "check": "center_demand_share_closure",
            "status": "PASS"
            if float(centers.groupby("province_code").assigned_demand_share_in_province.sum().sub(1.0).abs().max())
            <= 1e-10
            else "HARD_FAIL",
            "value": float(
                centers.groupby("province_code").assigned_demand_share_in_province.sum().sub(1.0).abs().max()
            ),
            "expected": "<= 1e-10",
        },
        {
            "check": "substation_mapping_complete",
            "status": "PASS" if len(substation_mapping) == 6294 else "HARD_FAIL",
            "value": len(substation_mapping),
            "expected": 6294,
        },
        {
            "check": "grid_route_complete",
            "status": "PASS" if len(paper_route) == 16609 else "HARD_FAIL",
            "value": len(paper_route),
            "expected": 16609,
        },
        {
            "check": "same_province_route",
            "status": "PASS"
            if not paper_route[["substation_id", "load_center_id"]].isna().any().any()
            else "HARD_FAIL",
            "value": int(paper_route[["substation_id", "load_center_id"]].isna().sum().sum()),
            "expected": 0,
        },
        {
            "check": "dpv_zero_integration_distance",
            "status": "PASS"
            if paper_route.dpv_spur_distance_km.eq(0).all()
            and paper_route.dpv_trunk_distance_km.eq(0).all()
            else "HARD_FAIL",
            "value": float(
                paper_route.dpv_spur_distance_km.abs().max()
                + paper_route.dpv_trunk_distance_km.abs().max()
            ),
            "expected": 0.0,
        },
        {
            "check": "physical_raster_unit_not_used",
            "status": "PASS",
            "value": "normalized within city only",
            "expected": "no absolute-energy conversion",
        },
    ]
    status = "HARD_FAIL" if any(row["status"] == "HARD_FAIL" for row in checks) else "PASS"
    output_files = [
        path
        for path in sorted(OUTPUT_DIR.iterdir())
        if path.is_file() and path.name != "run_manifest.json"
    ]
    manifest = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "candidate_only": True,
        "method": paper_config,
        "paper_evidence": {
            "pdf_path": model_config["sources"]["ees_supplement_pdf"],
            "pdf_pages": paper_config["paper_pdf_pages"],
            "section": paper_config["paper_section"],
            "method_summary": (
                "1:50m Natural Earth urban-area centroids as major load centers; "
                "1:10m urban areas supplement Tibet; 220 kV+ OSM substations; "
                "minimum total geodesic spur plus trunk distance within the model grid"
            ),
        },
        "inputs": [
            {"path": str(NE50_ZIP), "role": "Natural Earth 1:50m urban areas", "sha256": sha256_file(NE50_ZIP)},
            {"path": str(NE10_ZIP), "role": "Natural Earth 1:10m Tibet supplement", "sha256": sha256_file(NE10_ZIP)},
            {"path": str(POSITIVE_CELLS_PATH), "role": "audited 2019 positive raster cells", "sha256": sha256_file(POSITIVE_CELLS_PATH)},
            {"path": str(COVERAGE_PATH), "role": "280 covered and 57 fallback city audit", "sha256": sha256_file(COVERAGE_PATH)},
            {"path": str(SUBSTATIONS_PATH), "role": "OSM 220 kV+ substations", "sha256": sha256_file(SUBSTATIONS_PATH)},
            {
                "path": str(GRID_POINTS_PATH),
                "role": "16,609 candidate optimization points with 43 audited land-province corrections",
                "sha256": sha256_file(GRID_POINTS_PATH),
            },
            {
                "path": str(PROVINCE_AUDIT_SUMMARY_PATH),
                "role": "land-point province spatial-audit gate",
                "sha256": sha256_file(PROVINCE_AUDIT_SUMMARY_PATH),
            },
            {"path": str(METHOD_CONFIG_PATH), "role": "method parameters", "sha256": sha256_file(METHOD_CONFIG_PATH)},
        ],
        "transformations": [
            "project Natural Earth and model city polygons to the source Albers equal-area CRS",
            "select 1:50m urban polygons whose projected centroids fall within the 337-city model boundary",
            "add all 1:10m urban polygons whose projected centroids fall within Tibet model cities",
            "retain geometric polygon centroids as paper-faithful load-center coordinates",
            "normalize 2019 raster values within 280 covered cities and add 57 fallback city points",
            "assign demand points to nearest paper load center within province for validation and importance only",
            "assign every 220 kV+ substation to its nearest paper load center within province",
            "for every optimization grid point, exactly minimize geodesic spur plus trunk distance over eligible same-province substations",
            "keep distributed PV spur and trunk integration distances at zero as in the paper",
        ],
        "summary": {
            "paper_load_center_count": len(centers),
            "natural_earth_50m_center_count": int(centers.source_scale.eq("Natural_Earth_1_50m").sum()),
            "natural_earth_10m_tibet_center_count": int(
                centers.source_scale.eq("Natural_Earth_1_10m_Tibet_supplement").sum()
            ),
            "demand_supported_center_count": int(centers.assigned_demand_share_in_province.gt(0).sum()),
            "zero_assigned_demand_center_count": int(centers.assigned_demand_share_in_province.eq(0).sum()),
            "eligible_substation_count": len(substations),
            "optimization_grid_point_count": len(grid_points),
        },
        "checks": checks,
        "outputs": [
            {"path": str(path), "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in output_files
        ],
    }
    with (OUTPUT_DIR / "run_manifest.json").open("w", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    if status == "HARD_FAIL":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
