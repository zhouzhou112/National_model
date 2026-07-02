"""Audit the official 1 km electricity grids and build spatial-weight inputs.

This stage does not identify final load centres. It verifies the source archive,
audits all monthly rasters, builds the 2019 annual native-unit raster, intersects
positive cells with the existing 337-city boundary system, and writes explicit
coverage and lineage tables.

Run from the project root with the RL Python environment::

    python scripts/audit_gridded_electricity.py
    python scripts/audit_gridded_electricity.py --dry-run
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
import rasterio
from shapely.geometry import Point


ROOT = Path(__file__).resolve().parents[1]
METHOD_CONFIG_PATH = ROOT / "config" / "gridded_load_center_config.json"
MODEL_CONFIG_PATH = ROOT / "config" / "model_data_config.json"
RAW_ROOT = ROOT / "data" / "raw" / "electricity_consumption_1km_2012_2019"
SOURCE_DIR = RAW_ROOT / "source"
RASTER_DIR = RAW_ROOT / "extracted" / "China_1km_Ele_201204_201912"
OUTPUT_ROOT = ROOT / "data" / "load_centers_1km"
QC_DIR = OUTPUT_ROOT / "qc"
INTERMEDIATE_DIR = OUTPUT_ROOT / "intermediate"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate paths and print the planned outputs without reading raster arrays.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def md5_file(path: Path, chunk_size: int = 4 * 1024 * 1024) -> str:
    digest = hashlib.md5()
    with path.open("rb") as stream:
        while block := stream.read(chunk_size):
            digest.update(block)
    return digest.hexdigest()


def sha256_file(path: Path, chunk_size: int = 4 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(chunk_size):
            digest.update(block)
    return digest.hexdigest()


def write_csv(frame: pd.DataFrame, path: Path, *, compressed: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    compression = "gzip" if compressed else None
    frame.to_csv(
        path,
        index=False,
        encoding="utf-8-sig" if not compressed else "utf-8",
        lineterminator="\n",
        compression=compression,
    )


def recover_dbf_text(value: object) -> str:
    text = "" if value is None else str(value).strip()
    if any("\u4e00" <= char <= "\u9fff" for char in text):
        return text
    try:
        return text.encode("latin1").decode("gb18030")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def expected_months(source_config: dict) -> list[str]:
    start = pd.Period(source_config["expected_first_month"], freq="M")
    end = pd.Period(source_config["expected_last_month"], freq="M")
    return [period.strftime("%Y%m") for period in pd.period_range(start, end, freq="M")]


def clean_source_city_inventory(source_csv: Path) -> pd.DataFrame:
    source = pd.read_csv(source_csv, dtype=str)
    source["source_province_raw"] = source["Province"]
    source["source_province_filled"] = source["Province"].replace("", np.nan).ffill()
    source["source_city_raw"] = source["City"]
    source["province_name_en_normalized"] = source["source_province_filled"].replace(
        {"Bejing": "Beijing"}
    )
    source["city_name_en_normalized"] = source["City"].str.strip()
    source["normalization_note"] = np.where(
        source["source_province_filled"].eq("Bejing"),
        "corrected source typo Bejing to Beijing in processed field only",
        "no spelling correction",
    )
    source.insert(0, "source_row", np.arange(1, len(source) + 1))
    return source[
        [
            "source_row",
            "source_province_raw",
            "source_province_filled",
            "source_city_raw",
            "province_name_en_normalized",
            "city_name_en_normalized",
            "normalization_note",
        ]
    ]


def raster_signature(dataset: rasterio.io.DatasetReader) -> dict:
    return {
        "driver": dataset.driver,
        "band_count": dataset.count,
        "dtype": dataset.dtypes[0],
        "width": dataset.width,
        "height": dataset.height,
        "crs_wkt": dataset.crs.to_wkt() if dataset.crs else None,
        "transform": [float(value) for value in tuple(dataset.transform)],
        "resolution_x": float(dataset.res[0]),
        "resolution_y": float(dataset.res[1]),
        "bounds_left": float(dataset.bounds.left),
        "bounds_bottom": float(dataset.bounds.bottom),
        "bounds_right": float(dataset.bounds.right),
        "bounds_top": float(dataset.bounds.top),
        "nodata": dataset.nodata,
    }


def signatures_match(left: dict, right: dict) -> bool:
    exact_keys = ("driver", "band_count", "dtype", "width", "height", "crs_wkt", "nodata")
    if any(left[key] != right[key] for key in exact_keys):
        return False
    numeric_keys = (
        "transform",
        "resolution_x",
        "resolution_y",
        "bounds_left",
        "bounds_bottom",
        "bounds_right",
        "bounds_top",
    )
    return all(np.allclose(left[key], right[key], rtol=0.0, atol=1e-9) for key in numeric_keys)


def load_city_polygons(model_config: dict, raster_crs: object) -> gpd.GeoDataFrame:
    city_centers = pd.read_csv(
        ROOT / "data" / "grid" / "city_load_centers.csv",
        dtype={"source_city_code": str},
    )[
        [
            "source_city_code",
            "province_code",
            "province_name_en",
            "province_name_zh",
            "city_name_zh",
            "annual_city_power_share_in_province",
        ]
    ]
    city_centers["source_city_code"] = city_centers["source_city_code"].astype(str)

    polygons = gpd.read_file(model_config["sources"]["city_boundary_shapefile"])
    if "gb" not in polygons.columns:
        raise ValueError("City boundary shapefile is missing the gb city-code field")
    polygons["source_city_code"] = polygons["gb"].astype(str).str.strip()
    polygons = polygons.loc[polygons.source_city_code.isin(city_centers.source_city_code)].copy()
    polygons = polygons[["source_city_code", "geometry"]].dissolve(
        by="source_city_code", as_index=False
    )
    polygons = polygons.merge(city_centers, on="source_city_code", how="inner", validate="one_to_one")
    if len(polygons) != len(city_centers):
        missing = sorted(set(city_centers.source_city_code) - set(polygons.source_city_code))
        raise ValueError(f"Missing model city polygons: {missing[:20]}")
    if polygons.crs is None:
        raise ValueError("City boundary shapefile has no CRS")
    return polygons.to_crs(raster_crs)


def assign_positive_cells_to_cities(
    annual: np.ndarray,
    transform: rasterio.Affine,
    raster_crs: object,
    city_polygons: gpd.GeoDataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, cols = np.nonzero(annual > 0)
    values = annual[rows, cols].astype(np.float64)
    x = transform.c + (cols.astype(np.float64) + 0.5) * transform.a
    y = transform.f + (rows.astype(np.float64) + 0.5) * transform.e
    base = pd.DataFrame(
        {
            "raster_row": rows.astype(np.int32),
            "raster_col": cols.astype(np.int32),
            "x_albers_m": x,
            "y_albers_m": y,
            "annual_2019_native_value": values,
        }
    )
    points = gpd.GeoDataFrame(
        base,
        geometry=gpd.points_from_xy(base.x_albers_m, base.y_albers_m),
        crs=raster_crs,
    )
    joined = gpd.sjoin(
        points,
        city_polygons[
            [
                "source_city_code",
                "province_code",
                "province_name_en",
                "province_name_zh",
                "city_name_zh",
                "geometry",
            ]
        ],
        how="left",
        predicate="within",
    )
    if joined.index.duplicated().any():
        duplicated = int(joined.index.duplicated(keep=False).sum())
        raise ValueError(f"Positive raster cells matched multiple city polygons: {duplicated}")
    joined = joined.drop(columns=["geometry", "index_right"]).reset_index(drop=True)
    joined["spatial_assignment_method"] = np.where(
        joined.source_city_code.notna(),
        "cell_centroid_within_model_city_polygon",
        "unmatched_not_used_in_city_weights",
    )

    unmatched = joined.loc[joined.source_city_code.isna()].copy()
    matched = joined.loc[joined.source_city_code.notna()].copy()
    matched["province_code"] = matched.province_code.astype(int)
    return matched, unmatched


def main() -> None:
    args = parse_args()
    method_config = load_json(METHOD_CONFIG_PATH)
    model_config = load_json(MODEL_CONFIG_PATH)
    source_config = method_config["source"]
    audit_config = method_config["audit"]

    archive_path = SOURCE_DIR / "China_1km_Ele_201204_201912.zip"
    source_city_csv = SOURCE_DIR / "China_280_cities.csv"
    required = [archive_path, source_city_csv, RASTER_DIR, ROOT / "data" / "grid" / "city_load_centers.csv"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required inputs:\n" + "\n".join(missing))

    expected = expected_months(source_config)
    raster_paths = sorted(RASTER_DIR.glob("*.tif"))
    planned = {
        "archive": str(archive_path),
        "raster_directory": str(RASTER_DIR),
        "raster_count_found": len(raster_paths),
        "expected_raster_count": len(expected),
        "output_root": str(OUTPUT_ROOT),
        "outputs": [
            "qc/raster_inventory.csv",
            "qc/audit_summary.json",
            "qc/source_city_inventory_clean.csv",
            "qc/model_city_raster_coverage.csv",
            "qc/province_raster_coverage_summary.csv",
            "qc/annual_2019_boundary_leakage_cells.csv.gz",
            "intermediate/annual_2019_native_units.tif",
            "intermediate/annual_2019_positive_cells.csv.gz",
            "data_lineage.json",
        ],
    }
    if args.dry_run:
        print(json.dumps(planned, ensure_ascii=False, indent=2))
        return

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    QC_DIR.mkdir(parents=True, exist_ok=True)
    INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)

    checks: list[dict] = []
    archive_size = archive_path.stat().st_size
    archive_md5 = md5_file(archive_path)
    checks.append(
        {
            "check": "official_archive_size",
            "status": "PASS" if archive_size == int(source_config["archive_size_bytes"]) else "HARD_FAIL",
            "value": archive_size,
            "expected": int(source_config["archive_size_bytes"]),
        }
    )
    checks.append(
        {
            "check": "official_archive_md5",
            "status": "PASS" if archive_md5.lower() == source_config["archive_md5"].lower() else "HARD_FAIL",
            "value": archive_md5,
            "expected": source_config["archive_md5"],
        }
    )

    names = [path.stem for path in raster_paths]
    checks.append(
        {
            "check": "monthly_raster_count",
            "status": "PASS" if len(raster_paths) == int(source_config["expected_raster_count"]) else "HARD_FAIL",
            "value": len(raster_paths),
            "expected": int(source_config["expected_raster_count"]),
        }
    )
    checks.append(
        {
            "check": "monthly_sequence_complete",
            "status": "PASS" if names == expected else "HARD_FAIL",
            "value": names,
            "expected": expected,
        }
    )
    if any(check["status"] == "HARD_FAIL" for check in checks):
        raise ValueError("Archive/month inventory failed before raster-array audit")

    inventory_rows: list[dict] = []
    reference_signature: dict | None = None
    reference_profile: dict | None = None
    reference_transform: rasterio.Affine | None = None
    reference_crs = None
    annual_2019: np.ndarray | None = None
    for path in raster_paths:
        with rasterio.open(path) as dataset:
            signature = raster_signature(dataset)
            if reference_signature is None:
                reference_signature = signature
                reference_profile = dataset.profile.copy()
                reference_transform = dataset.transform
                reference_crs = dataset.crs
                annual_2019 = np.zeros((dataset.height, dataset.width), dtype=np.float64)
            metadata_consistent = signatures_match(signature, reference_signature)
            array = dataset.read(1)

        finite = np.isfinite(array)
        positive = finite & (array > 0)
        negative = finite & (array < 0)
        value_sum = float(np.sum(array[finite], dtype=np.float64))
        if path.stem.startswith(str(audit_config["spatial_weight_year"])):
            annual_2019 += np.where(finite, array, 0.0)
        inventory_rows.append(
            {
                "month": path.stem,
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "metadata_consistent_with_first_raster": metadata_consistent,
                "width": signature["width"],
                "height": signature["height"],
                "dtype": signature["dtype"],
                "band_count": signature["band_count"],
                "resolution_x_m": signature["resolution_x"],
                "resolution_y_m": signature["resolution_y"],
                "nodata": signature["nodata"],
                "finite_cell_count": int(finite.sum()),
                "zero_cell_count": int((finite & (array == 0)).sum()),
                "positive_cell_count": int(positive.sum()),
                "negative_cell_count": int(negative.sum()),
                "nonfinite_cell_count": int((~finite).sum()),
                "minimum_native_value": float(np.min(array[finite])) if finite.any() else np.nan,
                "maximum_native_value": float(np.max(array[finite])) if finite.any() else np.nan,
                "sum_native_value": value_sum,
                "twh_if_one_native_unit_equals_10000_kwh": value_sum / 100000.0,
                "unit_interpretation_status": "hypothetical_conversion_only_source_unit_unconfirmed",
            }
        )
        del array

    inventory = pd.DataFrame(inventory_rows)
    write_csv(inventory, QC_DIR / "raster_inventory.csv")
    checks.extend(
        [
            {
                "check": "raster_metadata_consistency",
                "status": "PASS" if inventory.metadata_consistent_with_first_raster.all() else "HARD_FAIL",
                "value": int(inventory.metadata_consistent_with_first_raster.sum()),
                "expected": len(inventory),
            },
            {
                "check": "raster_dimensions",
                "status": "PASS"
                if inventory.width.eq(int(audit_config["expected_width"])).all()
                and inventory.height.eq(int(audit_config["expected_height"])).all()
                else "HARD_FAIL",
                "value": sorted(set(zip(inventory.width, inventory.height))),
                "expected": [int(audit_config["expected_width"]), int(audit_config["expected_height"])],
            },
            {
                "check": "raster_resolution_m",
                "status": "PASS"
                if np.allclose(inventory.resolution_x_m, float(audit_config["expected_resolution_m"]))
                and np.allclose(inventory.resolution_y_m, float(audit_config["expected_resolution_m"]))
                else "HARD_FAIL",
                "value": sorted(set(zip(inventory.resolution_x_m, inventory.resolution_y_m))),
                "expected": float(audit_config["expected_resolution_m"]),
            },
            {
                "check": "no_negative_raster_values",
                "status": "PASS" if inventory.negative_cell_count.sum() == 0 else "HARD_FAIL",
                "value": int(inventory.negative_cell_count.sum()),
                "expected": 0,
            },
            {
                "check": "no_nonfinite_raster_values",
                "status": "PASS" if inventory.nonfinite_cell_count.sum() == 0 else "HARD_FAIL",
                "value": int(inventory.nonfinite_cell_count.sum()),
                "expected": 0,
            },
            {
                "check": "source_raster_unit",
                "status": "WARN",
                "value": source_config["unit_status"],
                "expected": "confirmed physical unit before any absolute-energy conversion",
            },
        ]
    )

    if annual_2019 is None or reference_profile is None or reference_transform is None or reference_crs is None:
        raise RuntimeError("No reference raster was initialized")
    annual_path = INTERMEDIATE_DIR / "annual_2019_native_units.tif"
    if audit_config["write_annual_raster"]:
        profile = reference_profile.copy()
        profile.update(
            dtype="float64",
            count=1,
            nodata=float(audit_config["annual_raster_nodata"]),
            compress="deflate",
            predictor=3,
            tiled=True,
            blockxsize=512,
            blockysize=512,
            BIGTIFF="IF_SAFER",
        )
        if annual_path.exists():
            with rasterio.open(annual_path) as existing_dataset:
                existing_annual = existing_dataset.read(1)
                existing_matches = (
                    existing_dataset.crs == reference_crs
                    and existing_dataset.transform == reference_transform
                    and existing_annual.shape == annual_2019.shape
                    and np.array_equal(existing_annual, annual_2019)
                )
            del existing_annual
            if not existing_matches:
                raise ValueError(
                    "Existing annual raster differs from the current verified source; "
                    f"manual review required before replacement: {annual_path}"
                )
        else:
            with rasterio.open(annual_path, "w", **profile) as destination:
                destination.write(annual_2019, 1)
                destination.update_tags(
                    source_data_doi=source_config["data_doi"],
                    aggregation="sum of monthly native raster values for 2019",
                    physical_unit_status=source_config["unit_status"],
                    model_role="within-city spatial weight only",
                )

    city_polygons = load_city_polygons(model_config, reference_crs)
    spatially_matched_cells, unmatched_cells = assign_positive_cells_to_cities(
        annual_2019,
        reference_transform,
        reference_crs,
        city_polygons,
    )
    write_csv(
        unmatched_cells,
        QC_DIR / "annual_2019_unmatched_positive_cells.csv.gz",
        compressed=True,
    )

    source_city_inventory = clean_source_city_inventory(source_city_csv)
    write_csv(source_city_inventory, QC_DIR / "source_city_inventory_clean.csv")
    source_counts = (
        source_city_inventory.groupby("province_name_en_normalized")
        .size()
        .rename("source_documented_city_count_in_province")
    )
    city_centers = pd.read_csv(
        ROOT / "data" / "grid" / "city_load_centers.csv",
        dtype={"source_city_code": str},
    )
    city_native = (
        spatially_matched_cells.groupby("source_city_code", as_index=False)
        .agg(
            annual_2019_native_value=("annual_2019_native_value", "sum"),
            positive_cell_count=("annual_2019_native_value", "size"),
        )
    )
    coverage = city_centers[
        [
            "source_city_code",
            "province_code",
            "province_name_en",
            "province_name_zh",
            "city_name_zh",
            "annual_city_power_share_in_province",
            "electricity_weight_method",
            "lon",
            "lat",
        ]
    ].merge(city_native, on="source_city_code", how="left", validate="one_to_one")
    coverage["annual_2019_native_value"] = coverage.annual_2019_native_value.fillna(0.0)
    coverage["positive_cell_count"] = coverage.positive_cell_count.fillna(0).astype(int)
    coverage = coverage.join(source_counts, on="province_name_en")
    coverage["source_documented_city_count_in_province"] = (
        coverage.source_documented_city_count_in_province.fillna(0).astype(int)
    )
    coverage["raster_positive_any"] = coverage.annual_2019_native_value > 0
    coverage["raster_positive_rank_in_province"] = coverage.groupby("province_code")[
        "annual_2019_native_value"
    ].rank(method="first", ascending=False)
    coverage["raster_covered"] = coverage.raster_positive_any & (
        coverage.raster_positive_rank_in_province
        <= coverage.source_documented_city_count_in_province
    )
    coverage["boundary_leakage_detected"] = (
        coverage.raster_positive_any & ~coverage.raster_covered
    )
    coverage["spatial_weight_method"] = np.where(
        coverage.raster_covered,
        "2019_raster_cells_normalized_within_city",
        "fallback_existing_city_center_point",
    )
    write_csv(coverage, QC_DIR / "model_city_raster_coverage.csv")

    covered_codes = set(coverage.loc[coverage.raster_covered, "source_city_code"])
    matched_cells = spatially_matched_cells.loc[
        spatially_matched_cells.source_city_code.isin(covered_codes)
    ].copy()
    boundary_leakage_cells = spatially_matched_cells.loc[
        ~spatially_matched_cells.source_city_code.isin(covered_codes)
    ].copy()
    boundary_leakage_cells["exclusion_reason"] = (
        "positive cells fell in a city absent from the official per-province city count; "
        "fallback city point is used instead"
    )
    write_csv(
        matched_cells,
        INTERMEDIATE_DIR / "annual_2019_positive_cells.csv.gz",
        compressed=True,
    )
    write_csv(
        boundary_leakage_cells,
        QC_DIR / "annual_2019_boundary_leakage_cells.csv.gz",
        compressed=True,
    )

    province_summary = (
        coverage.groupby(
            ["province_code", "province_name_en", "province_name_zh"], as_index=False
        )
        .agg(
            model_city_count=("source_city_code", "size"),
            raster_covered_city_count=("raster_covered", "sum"),
            raster_uncovered_city_count=("raster_covered", lambda values: int((~values).sum())),
            boundary_leakage_city_count=("boundary_leakage_detected", "sum"),
            covered_city_demand_share=(
                "annual_city_power_share_in_province",
                lambda values: float(values[coverage.loc[values.index, "raster_covered"]].sum()),
            ),
            annual_2019_native_value=("annual_2019_native_value", "sum"),
            positive_cell_count=("positive_cell_count", "sum"),
        )
    )
    write_csv(province_summary, QC_DIR / "province_raster_coverage_summary.csv")

    annual_total = float(np.sum(annual_2019, dtype=np.float64))
    unmatched_total = float(unmatched_cells.annual_2019_native_value.sum())
    unmatched_share = unmatched_total / annual_total if annual_total > 0 else np.nan
    boundary_leakage_total = float(boundary_leakage_cells.annual_2019_native_value.sum())
    boundary_leakage_share = boundary_leakage_total / annual_total if annual_total > 0 else np.nan
    checks.extend(
        [
            {
                "check": "annual_2019_positive_cells",
                "status": "PASS" if len(matched_cells) > 0 else "HARD_FAIL",
                "value": len(matched_cells),
                "expected": "> 0",
            },
            {
                "check": "positive_cell_city_assignment_share",
                "status": "PASS"
                if unmatched_share <= float(audit_config["maximum_unmatched_native_value_share"])
                else "HARD_FAIL",
                "value": 1.0 - unmatched_share,
                "expected": 1.0 - float(audit_config["maximum_unmatched_native_value_share"]),
            },
            {
                "check": "raster_covered_model_city_count",
                "status": "PASS"
                if int(coverage.raster_covered.sum()) == int(source_config["documented_city_count"])
                else "HARD_FAIL",
                "value": int(coverage.raster_covered.sum()),
                "expected": int(source_config["documented_city_count"]),
            },
            {
                "check": "boundary_leakage_native_value_share",
                "status": "PASS"
                if boundary_leakage_share
                <= float(audit_config["maximum_boundary_leakage_native_value_share"])
                else "HARD_FAIL",
                "value": boundary_leakage_share,
                "expected": float(audit_config["maximum_boundary_leakage_native_value_share"]),
            },
            {
                "check": "model_city_count",
                "status": "PASS" if len(coverage) == 337 else "HARD_FAIL",
                "value": len(coverage),
                "expected": 337,
            },
            {
                "check": "province_count",
                "status": "PASS" if coverage.province_code.nunique() == 31 else "HARD_FAIL",
                "value": int(coverage.province_code.nunique()),
                "expected": 31,
            },
        ]
    )

    summary = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": "HARD_FAIL"
        if any(check["status"] == "HARD_FAIL" for check in checks)
        else "PASS_WITH_WARNINGS"
        if any(check["status"] == "WARN" for check in checks)
        else "PASS",
        "checks": checks,
        "annual_2019": {
            "native_value_sum": annual_total,
            "twh_if_one_native_unit_equals_10000_kwh": annual_total / 100000.0,
            "physical_unit_status": source_config["unit_status"],
            "positive_cell_count_total": int((annual_2019 > 0).sum()),
            "positive_cell_count_matched": len(matched_cells),
            "positive_cell_count_unmatched": len(unmatched_cells),
            "unmatched_native_value_share": unmatched_share,
            "positive_cell_count_boundary_leakage": len(boundary_leakage_cells),
            "boundary_leakage_city_count": int(coverage.boundary_leakage_detected.sum()),
            "boundary_leakage_native_value_share": boundary_leakage_share,
        },
    }
    with (QC_DIR / "audit_summary.json").open("w", encoding="utf-8") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

    lineage = {
        "generated_at": summary["generated_at"],
        "stage": "gridded_electricity_source_audit_and_2019_spatial_weights",
        "source": method_config["source"],
        "inputs": [
            {
                "role": "official_verified_archive",
                "path": str(archive_path),
                "size_bytes": archive_size,
                "md5": archive_md5,
                "sha256": sha256_file(archive_path),
            },
            {
                "role": "official_city_inventory",
                "path": str(source_city_csv),
                "size_bytes": source_city_csv.stat().st_size,
                "md5": md5_file(source_city_csv),
                "sha256": sha256_file(source_city_csv),
            },
            {
                "role": "model_city_boundaries",
                "path": model_config["sources"]["city_boundary_shapefile"],
                "note": "337 model city polygons selected by source_city_code",
            },
            {
                "role": "model_city_demand_shares_and_fallback_centres",
                "path": str(ROOT / "data" / "grid" / "city_load_centers.csv"),
                "sha256": sha256_file(ROOT / "data" / "grid" / "city_load_centers.csv"),
            },
        ],
        "transformations": [
            "verify official archive byte size and MD5",
            "verify 93 consecutive monthly GeoTIFFs from 2012-04 to 2019-12",
            "audit raster metadata and values without changing source files",
            "sum the 12 native-unit monthly grids for 2019",
            "select cells with annual native value greater than zero",
            "assign cell centroids to the existing 337 model city polygons",
            "use official per-province city counts and native-value rank to isolate 280 covered cities",
            "exclude boundary-leakage cells from raster weights and retain affected cities on fallback points",
            "retain physical unit as unconfirmed native unit",
        ],
        "outputs": planned["outputs"],
        "result_status": summary["status"],
    }
    with (OUTPUT_ROOT / "data_lineage.json").open("w", encoding="utf-8") as stream:
        json.dump(lineage, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary["status"] == "HARD_FAIL":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
