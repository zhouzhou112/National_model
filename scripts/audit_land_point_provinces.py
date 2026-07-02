"""Spatially audit land-grid province codes without changing production inputs.

Land points are assigned to a province polygon by point-in-polygon. Points just
outside the boundary dataset are assigned to the nearest province only when the
distance is no more than 100 km. Offshore points retain their calibrated source
province because administrative land polygons do not define offshore allocation.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MODEL_CONFIG_PATH = ROOT / "config" / "model_data_config.json"
SOURCE_PATH = ROOT / "data" / "vre" / "optimization_points.csv"
CITY_CENTERS_PATH = ROOT / "data" / "grid" / "city_load_centers.csv"
OUTPUT_ROOT = ROOT / "data" / "load_centers_1km"
QC_DIR = OUTPUT_ROOT / "qc"
INTERMEDIATE_DIR = OUTPUT_ROOT / "intermediate"
AUDIT_PATH = QC_DIR / "land_point_province_spatial_audit.csv"
CORRECTION_PATH = QC_DIR / "land_point_province_corrections.csv"
OUTPUT_PATH = INTERMEDIATE_DIR / "optimization_points_spatially_validated_candidate.csv"
SUMMARY_PATH = QC_DIR / "land_point_province_audit_summary.json"
PROJECTED_CRS = "ESRI:102012"
MAXIMUM_NEAREST_DISTANCE_M = 100000.0


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def sha256_file(path: Path, chunk_size: int = 4 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(chunk_size):
            digest.update(block)
    return digest.hexdigest()


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig", lineterminator="\n")


def main() -> None:
    model_config = load_json(MODEL_CONFIG_PATH)
    points = pd.read_csv(SOURCE_PATH)
    points.insert(0, "source_row_index", np.arange(len(points), dtype=int))
    centers = pd.read_csv(
        CITY_CENTERS_PATH,
        dtype={"source_city_code": str},
    )[
        [
            "source_city_code",
            "province_code",
            "province_name_en",
            "province_name_zh",
        ]
    ]
    province_names = centers.drop_duplicates("province_code").set_index("province_code")

    cities = gpd.read_file(model_config["sources"]["city_boundary_shapefile"])[
        ["gb", "geometry"]
    ]
    cities["source_city_code"] = cities.gb.astype(str).str.strip()
    provinces = (
        cities.merge(centers, on="source_city_code", how="inner")
        .dissolve("province_code")
        .reset_index()[["province_code", "geometry"]]
        .to_crs(PROJECTED_CRS)
    )
    if len(provinces) != 31:
        raise ValueError(f"Expected 31 dissolved province polygons, found {len(provinces)}")

    land = points.loc[points.is_land.eq(1)].copy()
    land_geo = gpd.GeoDataFrame(
        land,
        geometry=gpd.points_from_xy(land.lon, land.lat),
        crs="EPSG:4326",
    ).to_crs(PROJECTED_CRS)
    within = gpd.sjoin(
        land_geo,
        provinces,
        how="left",
        predicate="within",
        lsuffix="source",
        rsuffix="spatial",
    )
    if within.source_row_index.duplicated().any():
        raise ValueError("A land point matched multiple dissolved province polygons")
    within = within.set_index("source_row_index", drop=False)
    assignment = pd.DataFrame(index=land.source_row_index)
    assignment["province_code_spatial"] = within.province_code_spatial
    assignment["province_assignment_method"] = np.where(
        assignment.province_code_spatial.notna(),
        "point_centroid_within_dissolved_province_polygon",
        "pending_nearest_province",
    )
    assignment["distance_to_assigned_province_polygon_km"] = np.where(
        assignment.province_code_spatial.notna(), 0.0, np.nan
    )

    unmatched_ids = assignment.index[assignment.province_code_spatial.isna()]
    unmatched = land_geo.loc[land_geo.source_row_index.isin(unmatched_ids)].copy()
    unmatched = unmatched.drop(
        columns=[
            "index_right",
            "index_spatial",
            "province_code_spatial",
        ],
        errors="ignore",
    )
    nearest = gpd.sjoin_nearest(
        unmatched,
        provinces,
        how="left",
        distance_col="nearest_province_distance_m",
    )
    nearest_province_column = next(
        (
            column
            for column in ("province_code", "province_code_right", "province_code_spatial")
            if column in nearest.columns
        ),
        None,
    )
    if nearest_province_column is None:
        raise ValueError(
            "Could not identify the right-table province code after nearest spatial join; "
            f"columns={nearest.columns.tolist()}"
        )
    nearest = nearest.sort_values(
        ["source_row_index", "nearest_province_distance_m", nearest_province_column],
        kind="mergesort",
    )
    nearest = nearest.drop_duplicates("source_row_index", keep="first").set_index(
        "source_row_index"
    )
    if nearest.nearest_province_distance_m.max() > MAXIMUM_NEAREST_DISTANCE_M:
        failed = nearest.loc[
            nearest.nearest_province_distance_m > MAXIMUM_NEAREST_DISTANCE_M,
            ["grid_uid", "lon", "lat", "nearest_province_distance_m"],
        ]
        raise ValueError(
            "Land points exceed nearest-province distance threshold:\n"
            + failed.to_string(index=False)
        )
    assignment.loc[nearest.index, "province_code_spatial"] = nearest[
        nearest_province_column
    ].to_numpy()
    assignment.loc[nearest.index, "province_assignment_method"] = (
        "nearest_dissolved_province_polygon_within_100km"
    )
    assignment.loc[
        nearest.index, "distance_to_assigned_province_polygon_km"
    ] = nearest.nearest_province_distance_m.to_numpy(float) / 1000.0
    assignment["province_code_spatial"] = assignment.province_code_spatial.astype(int)

    land_audit = land[
        [
            "source_row_index",
            "grid_uid",
            "grid_id",
            "lon",
            "lat",
            "is_land",
            "province_code",
            "province_name_en",
            "province_name_zh",
        ]
    ].copy()
    land_audit = land_audit.rename(
        columns={
            "province_code": "province_code_before",
            "province_name_en": "province_name_en_before",
            "province_name_zh": "province_name_zh_before",
        }
    ).merge(
        assignment.reset_index(),
        on="source_row_index",
        how="left",
        validate="one_to_one",
    )
    land_audit["province_code_after"] = land_audit.province_code_spatial.astype(int)
    land_audit["province_name_en_after"] = land_audit.province_code_after.map(
        province_names.province_name_en
    )
    land_audit["province_name_zh_after"] = land_audit.province_code_after.map(
        province_names.province_name_zh
    )
    land_audit["province_code_changed"] = (
        land_audit.province_code_before != land_audit.province_code_after
    )
    land_audit["validation_role"] = (
        "candidate_spatial_correction_not_applied_to_production_optimization_points"
    )
    write_csv(land_audit, AUDIT_PATH)
    corrections = land_audit.loc[land_audit.province_code_changed].copy()
    write_csv(corrections, CORRECTION_PATH)

    candidate = points.copy()
    candidate["province_code_before_spatial_validation"] = candidate.province_code
    candidate["province_name_en_before_spatial_validation"] = candidate.province_name_en
    candidate["province_name_zh_before_spatial_validation"] = candidate.province_name_zh
    candidate["province_assignment_validation_method"] = "offshore_source_assignment_preserved"
    candidate["distance_to_assigned_province_polygon_km"] = np.nan
    land_index = land_audit.source_row_index.to_numpy(int)
    candidate.loc[land_index, "province_code"] = land_audit.province_code_after.to_numpy(int)
    candidate.loc[land_index, "province_name_en"] = land_audit.province_name_en_after.to_numpy()
    candidate.loc[land_index, "province_name_zh"] = land_audit.province_name_zh_after.to_numpy()
    candidate.loc[land_index, "province_assignment_validation_method"] = (
        land_audit.province_assignment_method.to_numpy()
    )
    candidate.loc[land_index, "distance_to_assigned_province_polygon_km"] = (
        land_audit.distance_to_assigned_province_polygon_km.to_numpy(float)
    )
    candidate["province_code_changed_by_spatial_validation"] = (
        candidate.province_code != candidate.province_code_before_spatial_validation
    )
    candidate["candidate_status"] = (
        "spatially_validated_candidate_not_production_default"
    )
    write_csv(candidate, OUTPUT_PATH)

    checks = [
        {
            "check": "total_point_count",
            "status": "PASS" if len(candidate) == 16609 else "HARD_FAIL",
            "value": len(candidate),
            "expected": 16609,
        },
        {
            "check": "land_point_count",
            "status": "PASS" if len(land_audit) == 15309 else "HARD_FAIL",
            "value": len(land_audit),
            "expected": 15309,
        },
        {
            "check": "land_spatial_assignment_complete",
            "status": "PASS" if land_audit.province_code_after.notna().all() else "HARD_FAIL",
            "value": int(land_audit.province_code_after.notna().sum()),
            "expected": len(land_audit),
        },
        {
            "check": "nearest_polygon_maximum_distance_km",
            "status": "PASS"
            if land_audit.distance_to_assigned_province_polygon_km.max()
            <= MAXIMUM_NEAREST_DISTANCE_M / 1000.0
            else "HARD_FAIL",
            "value": float(land_audit.distance_to_assigned_province_polygon_km.max()),
            "expected": MAXIMUM_NEAREST_DISTANCE_M / 1000.0,
        },
        {
            "check": "offshore_assignment_unchanged",
            "status": "PASS"
            if not candidate.loc[candidate.is_land.eq(0), "province_code_changed_by_spatial_validation"].any()
            else "HARD_FAIL",
            "value": int(
                candidate.loc[
                    candidate.is_land.eq(0), "province_code_changed_by_spatial_validation"
                ].sum()
            ),
            "expected": 0,
        },
        {
            "check": "land_correction_count",
            "status": "PASS",
            "value": len(corrections),
            "expected": "data-derived; every change is listed in land_point_province_corrections.csv",
        },
    ]
    status = "HARD_FAIL" if any(row["status"] == "HARD_FAIL" for row in checks) else "PASS"
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "candidate_only": True,
        "method": {
            "land_within": "point centroid within dissolved 337-city province polygon",
            "land_boundary_fallback": "nearest province polygon within 100 km",
            "offshore": "preserve TABLES_ALL_POINTS/final_pointV2 calibrated province",
            "projected_crs": PROJECTED_CRS,
        },
        "inputs": [
            {"path": str(SOURCE_PATH), "sha256": sha256_file(SOURCE_PATH)},
            {"path": model_config["sources"]["city_boundary_shapefile"], "role": "337-city boundary source"},
            {"path": str(CITY_CENTERS_PATH), "sha256": sha256_file(CITY_CENTERS_PATH)},
            {
                "path": model_config["sources"]["province_calibration_xls"],
                "role": "original TABLES_ALL_POINTS calibration source retained for offshore assignments",
                "sha256": sha256_file(Path(model_config["sources"]["province_calibration_xls"])),
            },
        ],
        "summary": {
            "total_points": len(candidate),
            "land_points": int(candidate.is_land.eq(1).sum()),
            "offshore_points": int(candidate.is_land.eq(0).sum()),
            "land_points_within_polygon": int(
                land_audit.province_assignment_method.eq(
                    "point_centroid_within_dissolved_province_polygon"
                ).sum()
            ),
            "land_points_nearest_polygon_fallback": int(
                land_audit.province_assignment_method.eq(
                    "nearest_dissolved_province_polygon_within_100km"
                ).sum()
            ),
            "land_province_corrections": len(corrections),
        },
        "checks": checks,
        "outputs": [
            {"path": str(path), "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in (AUDIT_PATH, CORRECTION_PATH, OUTPUT_PATH)
        ],
    }
    with SUMMARY_PATH.open("w", encoding="utf-8") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if status == "HARD_FAIL":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
