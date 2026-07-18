"""Build a readable, model-ready CISPO input package.

The script copies only moderate-size tabular inputs. Large hourly capacity-factor
and river-flow stores remain at their validated source locations and are exposed
through machine-readable path indexes.

Run with the ArcGIS Pro Python environment, which contains pandas, xlrd,
netCDF4, and scipy::

    python scripts/build_cispo_data_package.py
"""
from __future__ import annotations

import csv
import gzip
import json
import math
import re
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.sparse import csr_matrix

from data_package_common import (
    CODE_TO_EN,
    CODE_TO_ZH,
    EN_TO_CODE,
    PROVINCE_DF,
    ZH_TO_CODE,
    add_province_fields,
    normalize_zh_province,
    sha256_file,
    write_csv,
    write_output_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "model_data_config.json"
TECH_CONFIG_PATH = ROOT / "config" / "technology_parameters.json"
FUEL_CONFIG_PATH = ROOT / "config" / "fuel_prices_supplementary_table2.json"
DATA_ROOT = ROOT / "data"


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as stream:
        config = json.load(stream)
    resolved_sources = {}
    for key, value in config["sources"].items():
        path = Path(value)
        resolved_sources[key] = path if path.is_absolute() else ROOT / path
    config["sources"] = resolved_sources
    generated_sources = set()
    if (
        config.get("hydro_proxy", {}).get("environmental_flow_method")
        == "monthly_p30_from_2019_only"
    ):
        generated_sources.add("hydro_environmental_flow")
    missing = [
        str(path)
        for key, path in config["sources"].items()
        if key not in generated_sources and not path.exists()
    ]
    if missing:
        raise FileNotFoundError("Missing configured source files:\n" + "\n".join(missing))
    return config


def add_qc(qc: list[dict], check: str, value: object, status: str, note: str) -> None:
    qc.append({"check": check, "value": value, "status": status, "note": note})


def build_sets(config: dict) -> None:
    write_csv(PROVINCE_DF, DATA_ROOT / "sets" / "provinces.csv")
    years = pd.DataFrame({"year": [int(year) for year in config["planning_years"]]})
    years["year_role"] = np.where(
        years.year.eq(int(config["base_year"])), "fixed_base_calibration", "capacity_expansion"
    )
    years["capacity_expansion_enabled"] = years.year.isin(config["capacity_expansion_years"])
    years["full_8760_dispatch_enabled"] = True
    write_csv(years, DATA_ROOT / "sets" / "model_years.csv")


def build_spatial_points(config: dict, qc: list[dict]) -> pd.DataFrame:
    source = pd.read_csv(config["sources"]["vre_so2_ccs_points"])
    final_v2 = pd.read_csv(config["sources"]["final_point_v2"])
    calibration = pd.read_excel(
        config["sources"]["province_calibration_xls"], engine="xlrd"
    )
    if (
        source.grid_uid.duplicated().any()
        or final_v2.grid_uid.duplicated().any()
        or calibration.grid_uid.duplicated().any()
    ):
        raise ValueError("grid_uid must be unique in all spatial point sources")
    if not (
        set(source.grid_uid) == set(final_v2.grid_uid) == set(calibration.grid_uid)
    ):
        raise ValueError("Spatial point sources have different grid_uid sets")

    final_lookup = final_v2.set_index("grid_uid")
    corrected_columns = ["existing_onwind_mw", "existing_offwind_mw"]
    for scenario in ("C", "B", "O"):
        corrected_columns.extend(
            [f"rem_onwind_{scenario}_mw", f"rem_offwind_{scenario}_so2_mw"]
        )
    for column in corrected_columns:
        source[column] = source.grid_uid.map(final_lookup[column])
    pv_split_error = np.zeros(len(source), dtype=float)
    for scenario in ("C", "B", "O"):
        split = source[f"rem_cpv_{scenario}_mw"] + source[f"rem_dpv_{scenario}_mw"]
        total = source.grid_uid.map(final_lookup[f"rem_pv_{scenario}_mw"])
        pv_split_error = np.maximum(pv_split_error, (split - total).abs().to_numpy())
    pv_split_tolerance_mw = 1e-3
    if float(pv_split_error.max()) > pv_split_tolerance_mw:
        raise ValueError(
            "UPV/DPV remaining-capacity split does not close to final_pointV2 PV total"
        )

    province_lookup = calibration.set_index("grid_uid")["province"]
    old_code = pd.to_numeric(source["province"], errors="raise").astype(int)
    new_code = source.grid_uid.map(province_lookup).astype(int)
    correction_mask = old_code.ne(new_code)
    audit = source.loc[correction_mask, ["grid_uid", "grid_id", "lon", "lat", "is_land"]].copy()
    audit["province_code_before"] = old_code[correction_mask].to_numpy()
    audit["province_code_after"] = new_code[correction_mask].to_numpy()
    audit["province_before_zh"] = audit.province_code_before.map(CODE_TO_ZH)
    audit["province_after_zh"] = audit.province_code_after.map(CODE_TO_ZH)
    audit["calibration_source"] = str(config["sources"]["province_calibration_xls"])
    write_csv(audit, DATA_ROOT / "vre" / "province_correction_audit.csv")

    land_corrections = pd.read_csv(
        config["sources"]["land_point_province_corrections"]
    )
    required_land_columns = {
        "grid_uid",
        "grid_id",
        "lon",
        "lat",
        "is_land",
        "province_code_before",
        "province_code_after",
        "province_assignment_method",
        "distance_to_assigned_province_polygon_km",
    }
    missing_land_columns = required_land_columns.difference(land_corrections.columns)
    if missing_land_columns:
        raise ValueError(
            "Land province correction table is missing columns: "
            + ", ".join(sorted(missing_land_columns))
        )
    if len(land_corrections) != 43 or land_corrections.grid_uid.duplicated().any():
        raise ValueError("Land province correction table must contain 43 unique grid_uid rows")
    missing_land_grids = sorted(set(land_corrections.grid_uid).difference(source.grid_uid))
    if missing_land_grids:
        raise ValueError(
            "Land province correction grid_uid values are absent from the VRE source: "
            + ", ".join(missing_land_grids)
        )

    source_lookup = source.set_index("grid_uid")
    tables_code_lookup = pd.Series(new_code.to_numpy(), index=source.grid_uid)
    observed_before = land_corrections.grid_uid.map(tables_code_lookup).astype(int)
    configured_before = pd.to_numeric(
        land_corrections.province_code_before, errors="raise"
    ).astype(int)
    configured_after = pd.to_numeric(
        land_corrections.province_code_after, errors="raise"
    ).astype(int)
    if not observed_before.equals(configured_before):
        mismatched = land_corrections.loc[
            observed_before.to_numpy() != configured_before.to_numpy(),
            ["grid_uid", "province_code_before", "province_code_after"],
        ]
        raise ValueError(
            "Land correction before-state does not match TABLES_ALL_POINTS calibration:\n"
            + mismatched.to_string(index=False)
        )
    observed_grid_id = land_corrections.grid_uid.map(source_lookup.grid_id).astype(int)
    configured_grid_id = pd.to_numeric(land_corrections.grid_id, errors="raise").astype(int)
    observed_is_land = land_corrections.grid_uid.map(source_lookup.is_land).astype(int)
    configured_is_land = pd.to_numeric(land_corrections.is_land, errors="raise").astype(int)
    observed_lon = land_corrections.grid_uid.map(source_lookup.lon).astype(float)
    observed_lat = land_corrections.grid_uid.map(source_lookup.lat).astype(float)
    if not observed_grid_id.equals(configured_grid_id):
        raise ValueError("Land correction grid_id values do not match the VRE source")
    if not (observed_is_land.eq(1).all() and configured_is_land.eq(1).all()):
        raise ValueError("Land province corrections may only be applied to is_land=1 points")
    if not (
        np.allclose(observed_lon, land_corrections.lon.astype(float), atol=1e-9, rtol=0.0)
        and np.allclose(observed_lat, land_corrections.lat.astype(float), atol=1e-9, rtol=0.0)
    ):
        raise ValueError("Land correction coordinates do not match the VRE source")
    if configured_before.eq(configured_after).any():
        raise ValueError("Every land province correction must change the province code")
    if not configured_after.isin(CODE_TO_ZH).all():
        raise ValueError("Land correction target contains a code outside the 31-province model")

    land_correction_lookup = pd.Series(
        configured_after.to_numpy(), index=land_corrections.grid_uid
    )
    final_code = source.grid_uid.map(land_correction_lookup).fillna(new_code).astype(int)
    land_audit = land_corrections.copy()
    land_audit["province_code_before"] = configured_before
    land_audit["province_code_after"] = configured_after
    land_audit["province_name_en_before"] = configured_before.map(CODE_TO_EN)
    land_audit["province_name_en_after"] = configured_after.map(CODE_TO_EN)
    land_audit["applied_to_production"] = True
    land_audit["application_stage"] = "after_TABLES_ALL_POINTS_before_VRE_constraints"
    land_audit["correction_source"] = str(
        config["sources"]["land_point_province_corrections"]
    )
    write_csv(land_audit, DATA_ROOT / "vre" / "land_province_correction_audit.csv")

    source["province_code"] = final_code
    source["province_name_en"] = source.province_code.map(CODE_TO_EN)
    source["province_name_zh"] = source.province_code.map(CODE_TO_ZH)
    out_of_scope = source.loc[source.province_name_en.isna()].copy()
    if not out_of_scope.empty:
        out_of_scope["exclusion_reason"] = "outside_31_province_model_scope"
        write_csv(
            out_of_scope[
                [
                    "grid_uid", "grid_id", "province_code", "lon", "lat", "is_land",
                    "existing_wind_mw", "existing_pv_mw", "rem_total_B_so2_mw",
                    "ccs_pot_mt", "exclusion_reason",
                ]
            ],
            DATA_ROOT / "vre" / "out_of_scope_points.csv",
        )
        source = source.loc[source.province_name_en.notna()].copy()

    out = source[
        [
            "grid_uid",
            "grid_id",
            "row_idx",
            "col_idx",
            "province_code",
            "province_name_en",
            "province_name_zh",
            "lon",
            "lat",
            "is_land",
            "wind_cf",
            "solar_cf",
            "so2_high",
            "so2_factor",
            "ccs_pot_mt",
            "ccs_inj_rec_mtpa",
            "ccs_inj_max_mtpa",
        ]
    ].copy()
    out = out.rename(columns={"wind_cf": "wind_cf_annual", "solar_cf": "solar_cf_annual"})

    existing_map = {
        "onwind": "existing_onwind_mw",
        "offwind": "existing_offwind_mw",
        "upv": "existing_cpv_mw",
        "dpv": "existing_dpv_mw",
    }
    for tech, source_col in existing_map.items():
        out[f"existing_{tech}_gw"] = source[source_col] / 1000.0

    rem_map = {
        "onwind": "rem_onwind_{s}_mw",
        "offwind": "rem_offwind_{s}_so2_mw",
        "upv": "rem_cpv_{s}_mw",
        "dpv": "rem_dpv_{s}_mw",
    }
    for scenario in ("C", "B", "O"):
        for tech, template in rem_map.items():
            existing = out[f"existing_{tech}_gw"]
            remaining = source[template.format(s=scenario)] / 1000.0
            out[f"remaining_{tech}_{scenario}_gw"] = remaining
            out[f"pmax_{tech}_{scenario}_gw"] = existing + remaining

    capacity_columns = [
        column
        for column in out.columns
        if column.startswith(("existing_", "remaining_", "pmax_"))
        and column.endswith("_gw")
    ]
    before_land_correction = out.copy()
    before_code_lookup = pd.Series(
        configured_before.to_numpy(), index=land_corrections.grid_uid
    )
    before_land_correction["province_code"] = (
        before_land_correction.grid_uid.map(before_code_lookup)
        .fillna(before_land_correction.province_code)
        .astype(int)
    )
    province_index = PROVINCE_DF.province_code.astype(int)
    capacity_before = (
        before_land_correction.groupby("province_code")[capacity_columns]
        .sum()
        .reindex(province_index, fill_value=0.0)
    )
    capacity_after = (
        out.groupby("province_code")[capacity_columns]
        .sum()
        .reindex(province_index, fill_value=0.0)
    )
    capacity_impact = pd.concat(
        [
            capacity_before.stack().rename("before_gw"),
            capacity_after.stack().rename("after_gw"),
        ],
        axis=1,
    ).reset_index().rename(columns={"level_1": "capacity_metric"})
    capacity_impact["delta_gw"] = (
        capacity_impact.after_gw - capacity_impact.before_gw
    )
    capacity_impact = capacity_impact.loc[
        capacity_impact.delta_gw.abs().gt(1e-12)
    ].copy()
    capacity_impact["province_name_en"] = capacity_impact.province_code.map(CODE_TO_EN)
    capacity_impact["province_name_zh"] = capacity_impact.province_code.map(CODE_TO_ZH)
    capacity_impact["interpretation"] = (
        "administrative_reallocation_only_national_total_unchanged"
    )
    capacity_impact = capacity_impact[
        [
            "province_code",
            "province_name_en",
            "province_name_zh",
            "capacity_metric",
            "before_gw",
            "after_gw",
            "delta_gw",
            "interpretation",
        ]
    ].sort_values(["province_code", "capacity_metric"])
    write_csv(
        capacity_impact,
        DATA_ROOT / "vre" / "land_province_correction_capacity_impact.csv",
    )
    national_capacity_delta = capacity_after.sum() - capacity_before.sum()
    max_national_capacity_delta = float(national_capacity_delta.abs().max())

    numeric_nonnegative = [
        col
        for col in out.columns
        if col.startswith(("existing_", "remaining_", "pmax_", "ccs_"))
    ]
    if (out[numeric_nonnegative].fillna(0) < -1e-9).any().any():
        raise ValueError("Negative capacity or CCS value in optimization points")

    write_csv(out, DATA_ROOT / "vre" / "optimization_points.csv")
    add_qc(qc, "optimization_point_rows", len(out), "PASS" if len(out) == 16609 else "FAIL", "16,739 source grids minus 130 province-code-71 grids outside the 31-province scope")
    add_qc(qc, "optimization_point_excluded_out_of_scope", len(out_of_scope), "PASS" if len(out_of_scope) == 130 else "WARN", "Province code 71 is not reassigned to a mainland province")
    add_qc(qc, "province_correction_rows", len(audit), "PASS" if len(audit) == 61 else "WARN", "TABLES_ALL_POINTS.xls overrides source province codes")
    correction_pairs = audit.groupby(["province_code_before", "province_code_after"]).size().to_dict()
    add_qc(qc, "province_correction_pairs", json.dumps({str(k): int(v) for k, v in correction_pairs.items()}), "PASS", "Expected current correction is Hainan code 46 to Shandong code 37")
    add_qc(qc, "land_province_correction_rows", len(land_audit), "PASS" if len(land_audit) == 43 else "FAIL", "Frozen spatial audit corrections applied after TABLES_ALL_POINTS and before VRE provincial constraints")
    add_qc(qc, "land_province_correction_land_only", int(observed_is_land.eq(1).sum()), "PASS" if observed_is_land.eq(1).all() else "FAIL", "All formal corrections must be land points")
    add_qc(qc, "land_province_correction_max_polygon_distance_km", round(float(land_audit.distance_to_assigned_province_polygon_km.max()), 6), "PASS" if float(land_audit.distance_to_assigned_province_polygon_km.max()) <= 100.0 else "FAIL", "Boundary fallback corrections were admitted only within 100 km")
    add_qc(qc, "land_province_correction_capacity_national_closure_gw", max_national_capacity_delta, "PASS" if max_national_capacity_delta <= 1e-9 else "FAIL", "Province reassignment must not change any national existing, remaining, or Pmax VRE total")
    add_qc(qc, "optimization_point_unique_grid_uid", out.grid_uid.nunique(), "PASS" if out.grid_uid.nunique() == len(out) else "FAIL", "Unique model site key")
    add_qc(qc, "optimization_point_province_count", out.province_code.nunique(), "PASS" if out.province_code.nunique() == 31 else "FAIL", "31-province model scope")
    add_qc(qc, "upv_dpv_split_max_abs_error_mw", float(pv_split_error.max()), "PASS" if float(pv_split_error.max()) <= pv_split_tolerance_mw else "FAIL", "Upstream UPV/DPV split closes to final_pointV2 PV remaining total within 0.001 MW")
    for tech in existing_map:
        add_qc(qc, f"existing_{tech}_gw_total", round(float(out[f"existing_{tech}_gw"].sum()), 6), "PASS", "Model input total")
    return out


def read_zarr_metadata(path: Path) -> tuple[dict, dict]:
    with (path / ".zattrs").open("r", encoding="utf-8") as stream:
        attrs = json.load(stream)
    with (path / ".zmetadata").open("r", encoding="utf-8") as stream:
        metadata = json.load(stream)["metadata"]
    return attrs, metadata


def build_cf_index(config: dict, points: pd.DataFrame, qc: list[dict]) -> None:
    root = config["sources"]["hourly_cf_root"]
    rows: list[dict] = []
    for tech in ("mixed_wind", "onshore_wind", "offshore_wind", "pv"):
        for store in sorted((root / tech).glob("cf_hourly_*.zarr")):
            attrs, meta = read_zarr_metadata(store)
            shape = meta["cf/.zarray"]["shape"]
            chunks = meta["cf/.zarray"]["chunks"]
            dimensions = meta["cf/.zattrs"]["_ARRAY_DIMENSIONS"]
            dimension_sizes = dict(zip(dimensions, shape))
            dimension_chunks = dict(zip(dimensions, chunks))
            if set(dimensions) != {"time", "grid_id"}:
                raise ValueError(f"Unexpected cf dimensions in {store}: {dimensions}")
            year = int(attrs["year"])
            summary_csv = root / "summary" / f"cf_annual_summary_{year}.csv"
            rows.append(
                {
                    "technology": tech,
                    "year": year,
                    "zarr_path": str(store),
                    "array_name": "cf",
                    "dimension_order": ",".join(dimensions),
                    "time_steps": dimension_sizes["time"],
                    "grid_count": dimension_sizes["grid_id"],
                    "time_chunk": dimension_chunks["time"],
                    "grid_chunk": dimension_chunks["grid_id"],
                    "source_time_zone": attrs.get("source_time_zone"),
                    "output_time_zone": attrs.get("output_time_zone"),
                    "time_note": attrs.get("time_note"),
                    "annual_summary_csv": str(summary_csv),
                }
            )
    index = pd.DataFrame(rows).sort_values(["year", "technology"])
    write_csv(index, DATA_ROOT / "vre" / "hourly_cf_index.csv")

    year = int(config["default_weather_year"])
    summary = pd.read_csv(root / "summary" / f"cf_annual_summary_{year}.csv")
    coverage = points[["grid_uid", "grid_id", "is_land"]].copy()
    for tech in ("mixed_wind", "onshore_wind", "offshore_wind", "pv"):
        ids = set(summary.loc[summary.tech.eq(tech), "grid_id"].astype(int))
        coverage[f"has_{tech}_{year}"] = coverage.grid_id.astype(int).isin(ids)
    write_csv(coverage, DATA_ROOT / "vre" / f"hourly_cf_grid_coverage_{year}.csv")

    land = coverage.is_land.eq(1)
    sea = ~land
    checks = {
        "mixed_wind_all": coverage[f"has_mixed_wind_{year}"].all(),
        "onshore_land": coverage.loc[land, f"has_onshore_wind_{year}"].all(),
        "pv_land": coverage.loc[land, f"has_pv_{year}"].all(),
        "offshore_sea": coverage.loc[sea, f"has_offshore_wind_{year}"].all(),
    }
    for name, passed in checks.items():
        add_qc(qc, f"hourly_cf_coverage_{name}_{year}", bool(passed), "PASS" if passed else "FAIL", "Coverage against model grid_id")


def build_load(config: dict, qc: list[dict]) -> None:
    source = config["sources"]["future_hourly_load"]
    target_years = set(int(year) for year in config["planning_years"])
    decision_years = set(int(year) for year in config["capacity_expansion_years"])
    output = DATA_ROOT / "load" / "hourly_load_2025_2060.csv.gz"
    legacy_output = DATA_ROOT / "load" / "hourly_load_2030_2060.csv.gz"
    output.parent.mkdir(parents=True, exist_ok=True)
    summary_parts = []
    group_rows: defaultdict[tuple[int, int], int] = defaultdict(int)
    first_all = True
    first_legacy = True
    with (
        gzip.open(output, "wt", encoding="utf-8-sig", newline="") as stream,
        gzip.open(legacy_output, "wt", encoding="utf-8-sig", newline="") as legacy_stream,
    ):
        for chunk in pd.read_csv(source, compression="gzip", chunksize=150_000):
            chunk = chunk.loc[chunk.target_year.isin(target_years)].copy()
            if chunk.empty:
                continue
            chunk["province_code"] = chunk.province_cn.map(normalize_zh_province).map(ZH_TO_CODE)
            if chunk.province_code.isna().any():
                raise ValueError("Unmapped province in hourly load")
            chunk["province_code"] = chunk.province_code.astype(int)
            converted = pd.DataFrame(
                {
                    "province_code": chunk.province_code,
                    "province_name_zh": chunk.province_code.map(CODE_TO_ZH),
                    "year": chunk.target_year.astype(int),
                    "hour_index": chunk.hour_index.astype(int),
                    "datetime_bj": chunk.datetime_bj,
                    "demand_gw": chunk.future_total_load_mw / 1000.0,
                    "base_residual_gw": chunk.base_residual_load_mw / 1000.0,
                    "heating_gw": chunk.heating_load_mw / 1000.0,
                    "cooling_gw": chunk.cooling_load_mw / 1000.0,
                    "ev_gw": chunk.ev_load_mw / 1000.0,
                }
            )
            converted.to_csv(stream, index=False, header=first_all, lineterminator="\n")
            first_all = False
            legacy = converted.loc[converted.year.isin(decision_years)]
            if not legacy.empty:
                legacy.to_csv(
                    legacy_stream, index=False, header=first_legacy, lineterminator="\n"
                )
                first_legacy = False
            for (code, year), count in converted.groupby(["province_code", "year"]).size().items():
                group_rows[(int(code), int(year))] += int(count)
            summary_parts.append(
                converted.groupby(["province_code", "province_name_zh", "year"], as_index=False).agg(
                    annual_demand_gwh=("demand_gw", "sum"),
                    peak_demand_gw=("demand_gw", "max"),
                    min_demand_gw=("demand_gw", "min"),
                )
            )
    summary = pd.concat(summary_parts).groupby(
        ["province_code", "province_name_zh", "year"], as_index=False
    ).agg(
        annual_demand_gwh=("annual_demand_gwh", "sum"),
        peak_demand_gw=("peak_demand_gw", "max"),
        min_demand_gw=("min_demand_gw", "min"),
    )
    write_csv(summary, DATA_ROOT / "load" / "annual_load_summary.csv")
    counts = pd.Series(group_rows)
    expected_groups = 31 * len(target_years)
    add_qc(qc, "hourly_load_province_year_groups", len(counts), "PASS" if len(counts) == expected_groups else "FAIL", f"Expected {expected_groups}")
    add_qc(qc, "hourly_load_hours_per_group_min", int(counts.min()), "PASS" if counts.min() == 8760 else "FAIL", "Every province-year must have 8760 hours")
    add_qc(qc, "hourly_load_hours_per_group_max", int(counts.max()), "PASS" if counts.max() == 8760 else "FAIL", "Every province-year must have 8760 hours")
    add_qc(qc, "hourly_load_base_year_present", int(config["base_year"]) in counts.index.get_level_values(1), "PASS" if int(config["base_year"]) in counts.index.get_level_values(1) else "FAIL", "2025 is the fixed calibration boundary")


THERMAL_MAP = {
    "Coal": "coal",
    "Coal CCS": "coalccs",
    "Coal CHP": "cchp",
    "Coal CHP CCS": "cchpccs",
    "Gas": "gas",
    "Gas CCS": "gasccs",
    "Gas CHP": "gchp",
    "Gas CHP CCS": "gchpccs",
    "Biomass": "bio",
    "Biomass CCS": "bioccs",
}


def build_thermal_nuclear(config: dict, qc: list[dict]) -> None:
    existing = pd.read_csv(config["sources"]["thermal_existing"])
    existing = add_province_fields(existing, source_col="province", source_kind="en")
    existing["technology"] = existing.thermal_type.map(THERMAL_MAP)
    if existing.technology.isna().any():
        raise ValueError("Unmapped thermal technology")
    existing_out = existing[
        ["province_code", "province_name_en", "province_name_zh", "technology", "capacity_gw"]
    ].rename(columns={"capacity_gw": "existing_capacity_gw_2025"})
    write_csv(existing_out, DATA_ROOT / "thermal" / "existing_capacity_2025.csv")

    retire = pd.read_csv(config["sources"]["thermal_retirement"])
    retire = add_province_fields(retire, source_col="province", source_kind="en")
    retire["technology"] = retire.thermal_type.map(THERMAL_MAP)
    buckets = list(range(2025, 2061, 5))
    long_parts = []
    for year in buckets:
        long_parts.append(
            retire[
                ["province_code", "province_name_en", "province_name_zh", "technology"]
            ].assign(
                retirement_year_bucket=year,
                retired_capacity_gw=pd.to_numeric(retire[f"retired_capacity_gw_{year}"], errors="coerce").fillna(0),
            )
        )
    retirement_long = pd.concat(long_parts, ignore_index=True)
    write_csv(retirement_long, DATA_ROOT / "thermal" / "retirement_schedule.csv")

    floors = []
    base = existing_out.set_index(["province_code", "technology"])["existing_capacity_gw_2025"]
    for year in config["planning_years"]:
        if int(year) == int(config["base_year"]):
            cumulative = pd.Series(dtype=float)
        else:
            cumulative = retirement_long.loc[retirement_long.retirement_year_bucket.le(year)].groupby(
                ["province_code", "technology"]
            ).retired_capacity_gw.sum()
        floor = (base - cumulative.reindex(base.index, fill_value=0)).clip(lower=0).rename("capacity_floor_gw").reset_index()
        floor["year"] = int(year)
        floor["province_name_en"] = floor.province_code.map(CODE_TO_EN)
        floor["province_name_zh"] = floor.province_code.map(CODE_TO_ZH)
        floors.append(floor)
    floor_out = pd.concat(floors, ignore_index=True)[
        ["province_code", "province_name_en", "province_name_zh", "year", "technology", "capacity_floor_gw"]
    ]
    write_csv(floor_out, DATA_ROOT / "thermal" / "capacity_floor_by_year.csv")

    nuclear = pd.read_csv(config["sources"]["nuclear_pipeline"])
    nuclear = nuclear.loc[nuclear["province"].notna()].copy()
    nuclear = add_province_fields(nuclear, source_col="province", source_kind="en")
    nuclear_parts = []
    for year in config["planning_years"]:
        source_year = min(int(year), 2050)
        col = f"pipeline_capacity_gw_{source_year}"
        nuclear_parts.append(
            nuclear[["province_code", "province_name_en", "province_name_zh"]].assign(
                year=int(year),
                capacity_floor_gw=pd.to_numeric(nuclear[col], errors="coerce").fillna(0),
                source_method=(
                    f"GEM pipeline milestone {source_year}"
                    if year <= 2050
                    else "hold GEM 2050 pipeline floor through 2060"
                ),
            )
        )
    nuclear_out = pd.concat(nuclear_parts, ignore_index=True)
    write_csv(nuclear_out, DATA_ROOT / "thermal" / "nuclear_capacity_floor_by_year.csv")
    add_qc(qc, "thermal_existing_rows", len(existing_out), "PASS" if len(existing_out) == 310 else "FAIL", "31 provinces x 10 CISPO thermal technologies")
    add_qc(qc, "thermal_2025_capacity_gw", round(float(existing_out.existing_capacity_gw_2025.sum()), 6), "PASS", "GEM operating model scope")
    floor_2025 = floor_out.loc[floor_out.year.eq(int(config["base_year"])), "capacity_floor_gw"].sum()
    add_qc(qc, "thermal_2025_floor_equals_existing", round(float(floor_2025), 6), "PASS" if math.isclose(float(floor_2025), float(existing_out.existing_capacity_gw_2025.sum()), abs_tol=1e-9) else "FAIL", "Base-year operating capacity is not reduced by the 2025 retirement bucket")
    add_qc(qc, "nuclear_2030_pipeline_floor_gw", round(float(nuclear_out.loc[nuclear_out.year.eq(2030), "capacity_floor_gw"].sum()), 6), "PASS", "2030 committed/pipeline floor; no synthetic target forcing")
    add_qc(qc, "nuclear_2025_operating_floor_gw", round(float(nuclear_out.loc[nuclear_out.year.eq(2025), "capacity_floor_gw"].sum()), 6), "PASS", "2025 operating units only")


def best_capacity_threshold(labels: pd.DataFrame, fallback: float) -> tuple[float, float]:
    observed = labels.loc[labels.operation_type_final.isin(["run_of_river", "reservoir_storage"]), ["capacity_mw_model", "operation_type_final"]].dropna()
    if observed.empty:
        return fallback, math.nan
    y = observed.operation_type_final.eq("reservoir_storage").to_numpy()
    capacity = observed.capacity_mw_model.to_numpy(float)
    best_threshold = fallback
    best_score = -1.0
    for threshold in np.unique(capacity):
        pred = capacity >= threshold
        tpr = (pred[y]).mean() if y.any() else 0.0
        tnr = (~pred[~y]).mean() if (~y).any() else 0.0
        score = 0.5 * (tpr + tnr)
        if score > best_score:
            best_threshold, best_score = float(threshold), float(score)
    return best_threshold, best_score


def inspect_netcdf(path: Path) -> dict:
    try:
        from netCDF4 import Dataset
    except ImportError:
        return {"dimensions": "not inspected: netCDF4 unavailable", "variables": ""}
    with Dataset(path) as dataset:
        dimensions = ";".join(f"{name}={len(dim)}" for name, dim in dataset.dimensions.items())
        variables = ";".join(dataset.variables.keys())
    return {"dimensions": dimensions, "variables": variables}


def ensure_monthly_environmental_flow_proxy(config: dict) -> tuple[str, str, str]:
    """Create or reuse the configured monthly environmental-flow proxy.

    The currently available hydrology source contains only 2019 target-COMID
    hourly discharge. For the requested P30 treatment, this writes a traceable
    single-year monthly P30 proxy. It is not a substitute for the formal
    multi-year climatological P30 requirement when 1980-2019 discharge becomes
    available.
    """

    method = str(config["hydro_proxy"]["environmental_flow_method"])
    if method != "monthly_p30_from_2019_only":
        return (
            "monthly_environmental_flow_2019_p10",
            "monthly_p10_proxy_m3s",
            "Monthly P10 proxy derived only from 2019 discharge",
        )

    try:
        from netCDF4 import Dataset
    except ImportError as exc:  # pragma: no cover - production env has netCDF4
        raise RuntimeError(
            "netCDF4 is required to build the monthly P30 environmental-flow proxy"
        ) from exc

    source = config["sources"]["hydro_hourly_discharge"]
    target = config["sources"]["hydro_environmental_flow"]
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return (
            "monthly_environmental_flow_2019_p30",
            "monthly_p30_proxy_m3s",
            "Monthly P30 proxy derived only from 2019 discharge",
        )

    dates = pd.date_range("2019-01-01 00:00", periods=8760, freq="h")
    with Dataset(source, "r") as src, Dataset(target, "w", format="NETCDF4") as out:
        comids = np.asarray(src.variables["comid"][:], dtype=np.int64)
        out.createDimension("month", 12)
        out.createDimension("comid", len(comids))
        month_var = out.createVariable("month", "i4", ("month",))
        month_var[:] = np.arange(1, 13, dtype=np.int32)
        comid_var = out.createVariable("comid", "i8", ("comid",))
        comid_var[:] = comids
        p30_var = out.createVariable(
            "monthly_p30_proxy_m3s",
            "f4",
            ("month", "comid"),
            zlib=True,
            complevel=4,
        )
        p30_var.units = "m3 s-1"
        p30_var.long_name = "2019 single-year monthly P30 environmental-flow proxy"
        generic_var = out.createVariable(
            "monthly_environmental_flow_m3s",
            "f4",
            ("month", "comid"),
            zlib=True,
            complevel=4,
        )
        generic_var.units = "m3 s-1"
        generic_var.long_name = "Alias of monthly_p30_proxy_m3s"
        values = np.empty((12, len(comids)), dtype=np.float32)
        qout = src.variables["qout_model_m3s"]
        for month in range(1, 13):
            hour_positions = np.flatnonzero(dates.month.to_numpy() == month)
            monthly_q = np.ma.filled(qout[hour_positions, :], np.nan)
            values[month - 1, :] = np.nanpercentile(monthly_q, 30, axis=0).astype(
                np.float32
            )
        p30_var[:] = values
        generic_var[:] = values
        out.source_discharge = str(source)
        out.method = "single_year_monthly_p30_proxy"
        out.warning = "Not equivalent to formal 1980-2019 climatological monthly P30"
    return (
        "monthly_environmental_flow_2019_p30",
        "monthly_p30_proxy_m3s",
        "Monthly P30 proxy derived only from 2019 discharge",
    )


def _split_semicolon_ids(value: object) -> list[str]:
    if pd.isna(value):
        return []
    return [part.strip() for part in str(value).split(";") if part.strip()]


def _is_directed_acyclic(edges: pd.DataFrame) -> bool:
    nodes = set(edges.source_node_id.astype(str)).union(edges.target_node_id.astype(str))
    indegree = {node: 0 for node in nodes}
    outgoing: dict[str, list[str]] = {node: [] for node in nodes}
    for row in edges.itertuples(index=False):
        source = str(row.source_node_id)
        target = str(row.target_node_id)
        outgoing[source].append(target)
        indegree[target] += 1
    queue = deque([node for node, degree in indegree.items() if degree == 0])
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for target in outgoing[node]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    return visited == len(nodes)


def _pearson_at_lag(source: np.ndarray, target: np.ndarray, lag: int) -> float:
    if lag:
        source = source[:-lag]
        target = target[lag:]
    source = source.astype(float, copy=False)
    target = target.astype(float, copy=False)
    source = source - float(np.nanmean(source))
    target = target - float(np.nanmean(target))
    source_std = float(np.nanstd(source))
    target_std = float(np.nanstd(target))
    if source_std <= 0.0 or target_std <= 0.0:
        return -2.0
    return float(np.nanmean(source * target) / (source_std * target_std))


def estimate_cascade_lags(
    edges: pd.DataFrame,
    discharge_path: Path,
    *,
    max_lag_h: int,
    lag_step_h: int = 3,
) -> pd.DataFrame:
    """Estimate upstream-to-downstream delay by discharge cross-correlation.

    The hydropower cascade paper estimates delay time from cross-correlation on
    3-hour discharge series. Stage1 already expands the 2019 GRFR discharge to
    hourly model time, so this function searches only multiples of 3 h.
    """
    try:
        from netCDF4 import Dataset
    except ImportError as exc:  # pragma: no cover - production env has netCDF4
        raise RuntimeError("netCDF4 is required to estimate cascade lags") from exc
    needed_comids = sorted(
        set(edges.source_comid.astype(int)).union(edges.target_comid.astype(int))
    )
    with Dataset(discharge_path) as dataset:
        comids = np.asarray(dataset.variables["comid"][:], dtype=np.int64)
        position = {int(comid): i for i, comid in enumerate(comids)}
        missing = [comid for comid in needed_comids if comid not in position]
        if missing:
            raise ValueError(f"Cascade COMIDs absent from GRFR discharge: {missing[:10]}")
        selected = [position[comid] for comid in needed_comids]
        discharge = np.asarray(
            dataset.variables["qout_model_m3s"][:, selected], dtype=np.float64
        )
    series = {comid: discharge[:, i] for i, comid in enumerate(needed_comids)}
    lags: list[int] = []
    correlations: list[float] = []
    for row in edges.itertuples(index=False):
        source = series[int(row.source_comid)]
        target = series[int(row.target_comid)]
        best_lag = 0
        best_corr = -2.0
        for lag in range(0, int(max_lag_h) + 1, int(lag_step_h)):
            corr = _pearson_at_lag(source, target, lag)
            if corr > best_corr:
                best_lag = int(lag)
                best_corr = float(corr)
        lags.append(best_lag)
        correlations.append(best_corr)
    out = edges.copy()
    out["travel_lag_h"] = lags
    out["lag_correlation"] = correlations
    out["lag_method"] = f"cross_correlation_qout_model_m3s_2019_step_{lag_step_h}h"
    return out


def build_hydro_cascade(config: dict, hydro: pd.DataFrame, qc: list[dict]) -> None:
    nodes = pd.read_csv(config["sources"]["hydro_cascade_stage2_nodes"])
    edges = pd.read_csv(config["sources"]["hydro_cascade_stage2_edges"])
    qa_path = config["sources"].get("hydro_cascade_stage2_qa")
    qa_status = ""
    if qa_path and Path(qa_path).exists():
        qa_status = json.loads(Path(qa_path).read_text(encoding="utf-8")).get("status", "")

    hydro_lookup = hydro.set_index("hydrochn_row_id")
    node_rows = []
    missing_ids: list[str] = []
    non_reservoir_ids: list[str] = []
    for row in nodes.itertuples(index=False):
        ids = _split_semicolon_ids(row.hydrochn_row_ids)
        missing_ids.extend([hydro_id for hydro_id in ids if hydro_id not in hydro_lookup.index])
        present = [hydro_id for hydro_id in ids if hydro_id in hydro_lookup.index]
        if present:
            types = hydro_lookup.loc[present, "operation_type_model"].astype(str)
            non_reservoir_ids.extend(types.index[types.ne("reservoir_storage")].tolist())
            model_capacity = float(hydro_lookup.loc[present, "capacity_potential_gw"].sum())
            existing_capacity = float(hydro_lookup.loc[present, "existing_capacity_gw"].sum())
        else:
            model_capacity = 0.0
            existing_capacity = 0.0
        node_rows.append(
            {
                "node_id": str(row.node_id),
                "river_group_stage2": str(row.river_group_stage2),
                "comid": int(row.comid),
                "hydrochn_row_ids": ";".join(present),
                "model_station_count": len(present),
                "model_capacity_gw": model_capacity,
                "existing_capacity_gw": existing_capacity,
                "stage2_capacity_gw": float(row.capacity_mw) / 1000.0,
                "plant_count_at_comid": int(row.plant_count_at_comid),
                "topology_in_degree": int(row.topology_in_degree),
                "topology_out_degree": int(row.topology_out_degree),
                "topology_role": str(row.topology_role),
                "label_name": str(row.label_name),
            }
        )
    node_out = pd.DataFrame(node_rows)
    node_id_to_rows = node_out.set_index("node_id").hydrochn_row_ids.to_dict()
    edge_out = estimate_cascade_lags(
        edges,
        config["sources"]["hydro_hourly_discharge"],
        max_lag_h=int(config["hydro_proxy"]["cascade_max_lag_h"]),
    )
    edge_out["source_hydrochn_row_ids"] = edge_out.source_node_id.map(node_id_to_rows)
    edge_out["target_hydrochn_row_ids"] = edge_out.target_node_id.map(node_id_to_rows)
    edge_out["source_model_station_count"] = edge_out.source_hydrochn_row_ids.fillna("").map(
        lambda value: len(_split_semicolon_ids(value))
    )
    edge_out["target_model_station_count"] = edge_out.target_hydrochn_row_ids.fillna("").map(
        lambda value: len(_split_semicolon_ids(value))
    )
    low_threshold = float(config["hydro_proxy"]["cascade_low_correlation_warning_threshold"])
    edge_out["lag_quality_flag"] = np.select(
        [
            edge_out.lag_correlation.lt(low_threshold),
            edge_out.travel_lag_h.ge(int(config["hydro_proxy"]["cascade_max_lag_h"])),
        ],
        ["LOW_CORRELATION", "MAX_LAG_BOUND_SELECTED"],
        default="PASS",
    )
    edge_keep = [
        "edge_id", "river_group_stage2", "source_node_id", "target_node_id",
        "source_comid", "target_comid", "source_hydrochn_row_ids",
        "target_hydrochn_row_ids", "source_model_station_count",
        "target_model_station_count", "steps_to_next_candidate",
        "traced_length_km", "travel_lag_h", "lag_correlation", "lag_method",
        "lag_quality_flag", "source_capacity_mw", "target_capacity_mw",
    ]
    write_csv(node_out, DATA_ROOT / "hydro" / "cascade_topology_nodes.csv")
    write_csv(edge_out[edge_keep], DATA_ROOT / "hydro" / "cascade_topology_edges.csv")

    stage2_capacity_diff = float((node_out.model_capacity_gw - node_out.stage2_capacity_gw).abs().max())
    add_qc(qc, "hydro_cascade_stage2_qa_status", qa_status or "missing", "WARN" if qa_status == "PASS_WITH_WARNINGS" else "PASS", "Stage2 topology is a modeling scaffold and carries documented warnings")
    add_qc(qc, "hydro_cascade_node_rows", len(node_out), "PASS" if len(node_out) == 142 else "FAIL", "Unique COMID nodes in recommended core cascade groups")
    add_qc(qc, "hydro_cascade_edge_rows", len(edge_out), "PASS" if len(edge_out) == 124 else "FAIL", "MERIT downstream edges within recommended groups")
    add_qc(qc, "hydro_cascade_missing_model_rows", len(missing_ids), "PASS" if not missing_ids else "FAIL", "All Stage2 cascade stations must map into current hydro_stations")
    add_qc(qc, "hydro_cascade_non_reservoir_model_rows", len(non_reservoir_ids), "PASS" if not non_reservoir_ids else "FAIL", "Core cascade stations must remain reservoir_storage in current model")
    add_qc(qc, "hydro_cascade_capacity_alignment_gw", round(stage2_capacity_diff, 9), "PASS" if stage2_capacity_diff <= 1e-9 else "FAIL", "Node capacity equals current model station capacity after COMID aggregation")
    add_qc(qc, "hydro_cascade_topology_is_dag", _is_directed_acyclic(edge_out), "PASS" if _is_directed_acyclic(edge_out) else "FAIL", "Cascade edges must be acyclic")
    low_lag = int(edge_out.lag_quality_flag.eq("LOW_CORRELATION").sum())
    max_lag = int(edge_out.lag_quality_flag.eq("MAX_LAG_BOUND_SELECTED").sum())
    add_qc(qc, "hydro_cascade_low_lag_correlation_edges", low_lag, "WARN" if low_lag else "PASS", f"Edges with lag-correlation below {low_threshold}")
    add_qc(qc, "hydro_cascade_max_lag_bound_edges", max_lag, "WARN" if max_lag else "PASS", "Edges whose best cross-correlation occurs at the configured max lag")


def build_hydro(config: dict, points: pd.DataFrame, qc: list[dict]) -> None:
    env_dataset_name, env_variable_name, env_role = ensure_monthly_environmental_flow_proxy(config)
    hydro = pd.read_csv(config["sources"]["hydro_stage2"])
    inventory = pd.read_csv(
        config["sources"]["hydro_updated_inventory"],
        usecols=["hydrochn_row_id", "status_model"],
    )
    hydro = hydro.merge(inventory, on="hydrochn_row_id", how="left", validate="one_to_one")
    tree = cKDTree(points[["lon", "lat"]].to_numpy(float))
    distance, position = tree.query(hydro[["lon", "lat"]].to_numpy(float), k=1)
    nearest = points.iloc[position]
    hydro["province_code"] = nearest.province_code.to_numpy(int)
    hydro["province_name_en"] = hydro.province_code.map(CODE_TO_EN)
    hydro["province_name_zh"] = hydro.province_code.map(CODE_TO_ZH)
    hydro["province_assignment_distance_deg"] = distance

    fallback = float(config["hydro_proxy"]["fallback_threshold_mw"])
    threshold, balanced_accuracy = best_capacity_threshold(hydro, fallback)
    explicit = hydro.operation_type_final.isin(["run_of_river", "reservoir_storage"])
    assigned_installed_type = np.where(
        explicit,
        hydro.operation_type_final,
        np.where(hydro.capacity_mw_model.ge(threshold), "reservoir_storage", "run_of_river"),
    )
    is_operating = hydro.get(
        "status_model", pd.Series(index=hydro.index, dtype=object)
    ).eq("operating")
    potential_threshold = float(config["hydro_proxy"]["potential_reservoir_threshold_mw"])
    paper_potential_type = np.where(
        hydro.capacity_mw_model.gt(potential_threshold),
        "reservoir_storage",
        "run_of_river",
    )
    # Paper-consistent split: installed plants retain the assigned label,
    # regardless of confidence; non-operating/potential dam sites follow the
    # explicit >750 MW reservoir rule in EES SI Section S3.4.
    hydro["operation_type_model"] = np.where(
        is_operating, assigned_installed_type, paper_potential_type
    )
    hydro["operation_type_source_model"] = np.select(
        [is_operating & explicit, is_operating & ~explicit],
        ["GHT_2026_explicit_installed", f"installed_capacity_proxy_{threshold:g}_mw"],
        default=f"paper_potential_threshold_gt_{potential_threshold:g}_mw",
    )
    hydro["operation_type_confidence_model"] = np.where(explicit, "high", "low")
    hydro["installed_operation_type_assigned"] = assigned_installed_type
    hydro["potential_operation_type_paper"] = paper_potential_type
    hydro["operation_type_scope"] = np.where(is_operating, "installed", "potential_or_nonoperating")
    hydro["existing_capacity_gw"] = np.where(
        hydro.get("status_model", pd.Series(index=hydro.index, dtype=object)).eq("operating"),
        hydro.capacity_mw_model / 1000.0,
        0.0,
    )
    hydro["capacity_potential_gw"] = hydro.capacity_mw_model / 1000.0
    hydro["head_m"] = hydro.head_m_model
    hydro["q_rated_m3s"] = hydro.q_rated_inferred_m3s
    hydro["v_max_gl"] = hydro["V_Max (GL)"]
    hydro["v_min_gl"] = hydro["V_Min (GL)"]
    hydro["environmental_flow_method"] = config["hydro_proxy"]["environmental_flow_method"]
    keep = [
        "hydrochn_row_id", "plant_name_model", "lon", "lat", "comid",
        "province_code", "province_name_en", "province_name_zh", "province_assignment_distance_deg",
        "existing_capacity_gw", "capacity_potential_gw", "head_m", "q_rated_m3s", "v_max_gl", "v_min_gl",
        "active_storage_gl", "active_storage_duration_days_at_qrated", "gross_storage_duration_days_at_qrated",
        "operation_type_model", "operation_type_source_model", "operation_type_confidence_model",
        "installed_operation_type_assigned", "potential_operation_type_paper", "operation_type_scope",
        "status_model", "technology_type_ght", "duplicate_comid_flag", "river_ght", "river_group_stage2",
        "environmental_flow_method", "stage2_issue_flags",
    ]
    out = hydro[keep].copy()
    write_csv(out, DATA_ROOT / "hydro" / "hydro_stations.csv")

    index_rows = []
    for dataset_name, source_key, role in (
        ("hourly_discharge_2019", "hydro_hourly_discharge", "Hourly natural discharge for all target COMIDs"),
        (env_dataset_name, "hydro_environmental_flow", env_role),
        ("explicit_ror_profiles_2019", "hydro_explicit_ror_profiles", "Provisional profile for 204 GHT-explicit run-of-river stations"),
    ):
        path = config["sources"][source_key]
        meta = inspect_netcdf(path)
        index_rows.append(
            {
                "dataset": dataset_name,
                "role": role,
                "path": str(path),
                "dimensions": meta["dimensions"],
                "variables": meta["variables"],
                "time_zone_note": "GRFR source timezone undocumented; source-native time retained",
                "source_sha256": sha256_file(path),
            }
        )
    index_rows.append(
        {
            "dataset": "grfr_download_manifest",
            "role": "Validated source transfer manifest for raw 2019 three-hour discharge",
            "path": str(config["sources"]["grfr_manifest"]),
            "dimensions": "",
            "variables": "",
            "time_zone_note": "",
            "source_sha256": sha256_file(config["sources"]["grfr_manifest"]),
        }
    )
    write_csv(pd.DataFrame(index_rows), DATA_ROOT / "hydro" / "timeseries_index.csv")
    summary = out.groupby(
        ["operation_type_model", "operation_type_source_model", "operation_type_confidence_model"],
        as_index=False,
    ).agg(station_rows=("hydrochn_row_id", "size"), capacity_potential_gw=("capacity_potential_gw", "sum"))
    summary["installed_proxy_threshold_mw"] = threshold
    summary["potential_reservoir_threshold_mw"] = potential_threshold
    summary["threshold_balanced_accuracy_on_explicit_labels"] = balanced_accuracy
    write_csv(summary, DATA_ROOT / "hydro" / "classification_summary.csv")
    add_qc(qc, "hydro_station_rows", len(out), "PASS" if len(out) == 2030 else "FAIL", "HydroCHN rows preserved")
    add_qc(qc, "hydro_unclassified_after_rules", int(out.operation_type_model.isna().sum()), "PASS" if out.operation_type_model.notna().all() else "FAIL", "Installed plants use assigned labels; potential sites use the paper >750 MW rule")
    add_qc(qc, "hydro_installed_proxy_threshold_mw", threshold, "WARN", f"Installed unlabeled plants retain the assigned proxy label; calibration balanced accuracy={balanced_accuracy:.3f}")
    potential_mismatch = int((
        out.operation_type_scope.eq("potential_or_nonoperating")
        & out.operation_type_model.ne(out.potential_operation_type_paper)
    ).sum())
    add_qc(qc, "hydro_potential_paper_rule_mismatches", potential_mismatch, "PASS" if potential_mismatch == 0 else "FAIL", "Potential sites >750 MW are reservoir; all others are run-of-river")
    add_qc(qc, "hydro_max_province_assignment_distance_deg", round(float(distance.max()), 6), "PASS" if distance.max() <= 0.25 else "WARN", "Nearest corrected 0.25-degree grid assignment")
    add_qc(qc, "hydro_environmental_flow_dataset", env_dataset_name, "PASS", f"NetCDF variable={env_variable_name}; formal multi-year P30 still requires multi-year source data")
    build_hydro_cascade(config, out, qc)


def interpolate_biomass(raw: pd.DataFrame, year: int) -> tuple[pd.DataFrame, str]:
    components = ["agricultural_residues_pj", "forestry_residues_pj", "energy_crops_pj"]
    base = raw.loc[raw.source_year.eq(2020)].set_index("province_code")
    future = raw.loc[raw.source_year.eq(2050)].set_index("province_code")
    if year <= 2050:
        weight = (year - 2020) / 30.0
        values = base[components] + weight * (future[components] - base[components])
        method = f"linear interpolation between 2020 and 2050; weight={weight:.6f}"
    else:
        values = future[components].copy()
        method = "hold 2050 potential constant after 2050"
    values = values.reset_index()
    values["year"] = year
    values["source_method"] = method
    return values, method


def build_biomass(config: dict, qc: list[dict]) -> None:
    parts = []
    rename = {
        "agricultural residues": "agricultural_residues_pj",
        "forestry residues": "forestry_residues_pj",
        "energy crops": "energy_crops_pj",
    }
    for year in (2020, 2050):
        sheet = pd.read_excel(config["sources"]["biomass_province_workbook"], sheet_name=str(year))
        sheet = add_province_fields(sheet, source_col="Province", source_kind="en")
        sheet = sheet.rename(columns=rename)
        sheet["source_year"] = year
        parts.append(
            sheet[["province_code", "province_name_en", "province_name_zh", "source_year", *rename.values()]]
        )
    raw = pd.concat(parts, ignore_index=True)
    raw["common_three_total_pj"] = raw[list(rename.values())].sum(axis=1)
    write_csv(raw, DATA_ROOT / "biomass" / "source_potential_2020_2050.csv")

    model_parts = []
    for year in config["planning_years"]:
        values, _ = interpolate_biomass(raw, int(year))
        values["province_name_en"] = values.province_code.map(CODE_TO_EN)
        values["province_name_zh"] = values.province_code.map(CODE_TO_ZH)
        values["thermcal_gj_per_year"] = values[list(rename.values())].sum(axis=1) * 1_000_000.0
        model_parts.append(values)
    model = pd.concat(model_parts, ignore_index=True)[
        ["province_code", "province_name_en", "province_name_zh", "year", *rename.values(), "thermcal_gj_per_year", "source_method"]
    ]
    write_csv(model, DATA_ROOT / "biomass" / "fuel_potential_by_province_year.csv")
    add_qc(qc, "biomass_source_rows", len(raw), "PASS" if len(raw) == 62 else "FAIL", "31 provinces x source years 2020 and 2050")
    for year in config["planning_years"]:
        total_ej = model.loc[model.year.eq(year), "thermcal_gj_per_year"].sum() / 1e9
        add_qc(qc, f"biomass_common_three_total_ej_{year}", round(float(total_ej), 6), "PASS", "Agricultural + forestry residues + energy crops")


def build_transmission(config: dict, qc: list[dict]) -> None:
    directed = pd.read_csv(config["sources"]["transmission_existing_directed"])
    directed["from_zh"] = directed.from_province.map(normalize_zh_province)
    directed["to_zh"] = directed.to_province.map(normalize_zh_province)
    directed["from_province_code"] = directed.from_zh.map(ZH_TO_CODE)
    directed["to_province_code"] = directed.to_zh.map(ZH_TO_CODE)
    if directed[["from_province_code", "to_province_code"]].isna().any().any():
        raise ValueError("Unmapped province in existing transmission lines")
    directed["from_province_code"] = directed.from_province_code.astype(int)
    directed["to_province_code"] = directed.to_province_code.astype(int)

    candidates = pd.read_csv(config["sources"]["transmission_candidate_corridors"])
    candidates["from_zh"] = candidates.from_province.map(normalize_zh_province)
    candidates["to_zh"] = candidates.to_province.map(normalize_zh_province)
    candidates["from_province_code"] = candidates.from_zh.map(ZH_TO_CODE).astype(int)
    candidates["to_province_code"] = candidates.to_zh.map(ZH_TO_CODE).astype(int)
    distance_map = {
        tuple(sorted((int(row.from_province_code), int(row.to_province_code)))): float(row.distance_km)
        for row in candidates.itertuples()
    }
    directed["distance_km"] = [
        distance_map.get(tuple(sorted((int(a), int(b)))), math.nan)
        for a, b in zip(directed.from_province_code, directed.to_province_code)
    ]
    keep = directed.direction.eq("forward") | directed.direction.isna()
    existing = directed.loc[keep].copy()
    existing["capacity_group"] = existing.shared_capacity_group.fillna("")
    existing.loc[existing.capacity_group.eq(""), "capacity_group"] = existing.loc[
        existing.capacity_group.eq(""), "line_id"
    ]
    existing_out = existing[
        [
            "edge_id", "line_id", "line_name_cn", "technology", "voltage_kv",
            "from_province_code", "to_province_code", "is_bidirectional", "capacity_gw",
            "distance_km", "capacity_group", "capacity_basis", "source_ids", "notes",
        ]
    ].rename(columns={"edge_id": "segment_id", "capacity_gw": "existing_capacity_gw"})
    write_csv(existing_out, DATA_ROOT / "transmission" / "existing_lines.csv")

    candidate_out = candidates[
        [
            "from_province_code", "to_province_code", "distance_km", "allowed_by_model",
            "exclusion_reason", "preset_technology", "preset_option", "preset_voltage",
            "existing_capacity_gw", "preset_capacity_gw", "preset_unit_cost_yuan_per_kw",
            "preset_source", "existing_line_ids",
        ]
    ].copy()
    write_csv(candidate_out, DATA_ROOT / "transmission" / "candidate_corridors.csv")
    add_qc(qc, "transmission_existing_segment_rows", len(existing_out), "PASS", "Forward representation; AC directionality retained in is_bidirectional")
    add_qc(qc, "transmission_candidate_pairs", len(candidate_out), "PASS" if len(candidate_out) == 465 else "FAIL", "All unordered pairs among 31 provinces")


def build_carbon(config: dict, qc: list[dict]) -> None:
    raw = pd.read_excel(config["sources"]["carbon_pathways_workbook"], header=None)
    pathway_years = [2030, 2040, 2050, 2060]
    scenario_names = ["NegEmis200Mt", "Base_-550Mt", "NegEmis700Mt"]
    source_labels = {str(raw.iloc[row, 0]).strip(): row for row in range(len(raw))}
    rows = []
    for scenario in scenario_names:
        source_label = "Base (-550Mt)" if scenario == "Base_-550Mt" else scenario
        if source_label not in source_labels:
            raise ValueError(f"Missing carbon scenario row in workbook: {source_label}")
        source_row = source_labels[source_label]
        rows.append(
            {
                "scenario": scenario,
                "year": int(config["base_year"]),
                "emissions_limit_mtco2_per_year": math.nan,
                "constraint_active": False,
                "is_default": scenario == config["default_carbon_scenario"],
                "source_method": "fixed 2025 calibration year; CISPO pathway begins in 2030",
            }
        )
        for offset, year in enumerate(pathway_years, start=1):
            rows.append(
                {
                    "scenario": scenario,
                    "year": year,
                    "emissions_limit_mtco2_per_year": float(raw.iloc[source_row, offset]),
                    "constraint_active": True,
                    "is_default": scenario == config["default_carbon_scenario"],
                    "source_method": "Carbon_emission.xlsx CISPO pathway block",
                }
            )
    for year in config["planning_years"]:
        rows.append(
            {
                "scenario": "NoEmisCap",
                "year": int(year),
                "emissions_limit_mtco2_per_year": math.nan,
                "constraint_active": False,
                "is_default": False,
                "source_method": "CISPO scenario without annual emissions limitation",
            }
        )
    pathways = pd.DataFrame(rows)
    write_csv(pathways, DATA_ROOT / "carbon" / "emissions_limits_by_scenario.csv")

    reference_rows = []
    reference_years = [int(value) for value in raw.iloc[1, 1:8].tolist()]
    for source_label in ("NDC", "GM2.0", "CN2050"):
        source_row = source_labels[source_label]
        for offset, year in enumerate(reference_years, start=1):
            value = pd.to_numeric(raw.iloc[source_row, offset], errors="coerce")
            if pd.notna(value):
                reference_rows.append(
                    {
                        "reference_pathway": source_label,
                        "year": year,
                        "emissions_mtco2_per_year": float(value) * 100.0,
                        "source_unit": "10^8 tCO2/yr",
                        "source_method": "Carbon_emission.xlsx literature-reference block",
                    }
                )
    write_csv(pd.DataFrame(reference_rows), DATA_ROOT / "carbon" / "reference_pathways.csv")
    default = pathways.loc[pathways.scenario.eq(config["default_carbon_scenario"])]
    expected = {2025: math.nan, 2030: 4000.0, 2040: 1300.0, 2050: -100.0, 2060: -550.0}
    actual = dict(zip(default.year, default.emissions_limit_mtco2_per_year))
    passed = all(
        (math.isnan(expected[year]) and pd.isna(actual[year]))
        or math.isclose(float(actual[year]), expected[year], abs_tol=1e-9)
        for year in expected
    )
    add_qc(qc, "carbon_default_base_path", json.dumps(actual), "PASS" if passed else "FAIL", "2025 unconstrained base; CISPO Base pathway from 2030")


def capital_recovery_factor(rate: float, lifetime_years: float) -> float:
    return rate * (1.0 + rate) ** lifetime_years / ((1.0 + rate) ** lifetime_years - 1.0)


def build_phs_capacity_bounds(config: dict, qc: list[dict]) -> pd.DataFrame:
    """Build province-year PHS floors and pipeline potentials from GHT 2026."""
    source = Path(config["sources"]["phs_inventory"])
    phs = pd.read_csv(source)
    required = {
        "phs_id", "province", "status_ght", "capacity_mw_model",
        "is_existing_2025", "available_from_year", "duration_h",
    }
    missing = sorted(required.difference(phs.columns))
    if missing:
        raise ValueError(f"PHS inventory missing columns: {', '.join(missing)}")
    provinces = pd.read_csv(DATA_ROOT / "sets" / "provinces.csv")
    province_lookup = provinces.set_index("province_name_en").province_code.to_dict()
    unmatched = sorted(set(phs.province).difference(province_lookup))
    if unmatched:
        raise ValueError(f"Unmatched PHS provinces: {unmatched}")
    phs["province_code"] = phs.province.map(province_lookup).astype(int)
    rows = []
    for year in config["capacity_expansion_years"]:
        available = phs.available_from_year.le(int(year))
        for province in provinces.itertuples(index=False):
            local = phs.province_code.eq(int(province.province_code))
            floor = phs.loc[
                local & phs.is_existing_2025.astype(bool), "capacity_mw_model"
            ].sum() / 1000.0
            upper = phs.loc[
                local & available, "capacity_mw_model"
            ].sum() / 1000.0
            rows.append(
                {
                    "province_code": int(province.province_code),
                    "province_name_en": province.province_name_en,
                    "province_name_zh": province.province_name_zh,
                    "year": int(year),
                    "technology": "phs",
                    "capacity_floor_gw": float(floor),
                    "capacity_upper_gw": float(upper),
                    "duration_h": 8.0,
                    "floor_method": "GHT_2026_is_existing_2025_operating_projects",
                    "upper_method": "GHT_2026_projects_with_available_from_year_le_planning_year",
                    "source_path": str(source),
                }
            )
    bounds = pd.DataFrame(rows).sort_values(["year", "province_code"])
    if len(bounds) != 31 * len(config["capacity_expansion_years"]):
        raise ValueError("PHS bounds must contain 31 provinces x planning years")
    if (bounds.capacity_floor_gw > bounds.capacity_upper_gw + 1e-9).any():
        raise ValueError("PHS floor exceeds project-pipeline upper bound")
    write_csv(
        bounds,
        DATA_ROOT / "storage" / "phs_capacity_bounds_by_province_year.csv",
    )
    national = bounds.groupby("year")[["capacity_floor_gw", "capacity_upper_gw"]].sum()
    add_qc(
        qc,
        "phs_existing_2025_capacity_gw",
        float(national.capacity_floor_gw.iloc[0]),
        "PASS" if math.isclose(float(national.capacity_floor_gw.iloc[0]), 65.94, abs_tol=1e-6) else "FAIL",
        "65.94 GW GHT-cleaned operating PHS anchor",
    )
    add_qc(
        qc,
        "phs_2030_pipeline_upper_gw",
        float(national.loc[2030, "capacity_upper_gw"]),
        "PASS" if math.isclose(float(national.loc[2030, "capacity_upper_gw"]), 249.191, abs_tol=1e-6) else "FAIL",
        "249.191 GW projects available by 2030",
    )
    return bounds


def build_technology_parameters(config: dict, qc: list[dict]) -> None:
    with TECH_CONFIG_PATH.open("r", encoding="utf-8") as stream:
        tech = json.load(stream)
    source_pdf = tech["source"]["document"]
    base_year = int(config["base_year"])

    vre = pd.DataFrame(tech["vre_cost_anchor"])
    vre["model_anchor_year"] = base_year
    vre["source_document"] = source_pdf
    vre["future_cost_status"] = "AVAILABLE_AS_USER_VISUAL_ESTIMATE"
    write_csv(vre, DATA_ROOT / "technology" / "vre_hydro_cost_anchor.csv")

    ruc = pd.DataFrame(tech["thermal_ruc"])
    ruc["source_page"] = 59
    ruc["source_document"] = source_pdf
    write_csv(ruc, DATA_ROOT / "technology" / "thermal_nuclear_ruc_parameters.csv")

    economic = tech["thermal_economic"]
    economic_rows = []
    for technology, fom in economic["fixed_om_fraction_capex_per_year"].items():
        economic_rows.append(
            {
                "technology": technology,
                "fixed_om_fraction_capex_per_year": fom,
                "variable_om_yuan_per_mwh": economic["variable_om_yuan_per_mwh"][technology],
                "source_page": economic["source_page"],
                "source_document": source_pdf,
            }
        )
    write_csv(pd.DataFrame(economic_rows), DATA_ROOT / "technology" / "thermal_nuclear_om_parameters.csv")

    capex_raw = pd.read_excel(
        config["sources"]["capex_predictions_workbook"],
        sheet_name="This Study Data",
        header=2,
    ).iloc[:, :6]
    capex_raw.columns = ["source_technology", "2030", "2040", "2050", "2060", "source_figure"]
    source_to_model = {
        "Onshore wind": ["onwind"],
        "Offshore wind": ["offwind"],
        "Utility-scale solar PV": ["upv"],
        "Distributed solar PV": ["dpv"],
        "CSP": ["csp"],
        "PHS": ["phs"],
        "BAT": ["battery"],
        "Coal": ["coal", "cchp"],
        "Coal CCS": ["coalccs", "cchpccs"],
        "Nuclear": ["nuclear"],
        "Gas": ["gas", "gchp"],
        "Gas CCS": ["gasccs", "gchpccs"],
        "Biomass": ["bio"],
        "Biomass CCS": ["bioccs"],
    }
    capex_rows = []
    for row in capex_raw.itertuples(index=False):
        source_name = str(row.source_technology).split(" (")[0].strip()
        if source_name not in source_to_model:
            raise ValueError(f"Unmapped CapEx technology: {row.source_technology}")
        for technology in source_to_model[source_name]:
            mapping = "direct workbook technology row"
            if technology in {"cchp", "cchpccs", "gchp", "gchpccs"}:
                mapping = "CHP mapped to corresponding fuel and CCS curve"
            for year in config["capacity_expansion_years"]:
                capex_rows.append(
                    {
                        "technology": technology,
                        "year": int(year),
                        "capex_yuan_per_kw": float(getattr(row, f"_{list(config['capacity_expansion_years']).index(year) + 1}")),
                        "source_technology": source_name,
                        "source_figure": row.source_figure,
                        "extraction_method": "user visual estimate from CISPO figure scale",
                        "mapping_assumption": mapping,
                        "source_workbook": str(config["sources"]["capex_predictions_workbook"]),
                    }
                )
    hydro_anchor = float(vre.loc[vre.technology.eq("hydro"), "capex_yuan_per_kw"].iloc[0])
    for year in config["capacity_expansion_years"]:
        capex_rows.append(
            {
                "technology": "hydro",
                "year": int(year),
                "capex_yuan_per_kw": hydro_anchor,
                "source_technology": "Hydropower current anchor",
                "source_figure": "EES SI p.55",
                "extraction_method": "explicit SI anchor held constant",
                "mapping_assumption": "no hydro trajectory supplied in CapEx workbook",
                "source_workbook": source_pdf,
            }
        )
    capex = pd.DataFrame(capex_rows).sort_values(["technology", "year"])
    expected_capex_rows = 19 * len(config["capacity_expansion_years"])
    if len(capex) != expected_capex_rows or capex.duplicated(["technology", "year"]).any():
        raise ValueError("Technology CapEx table does not cover 19 technologies x decision years uniquely")
    write_csv(capex, DATA_ROOT / "technology" / "technology_capex_by_year.csv")
    nuclear_rows = [
        {
            "year": base_year,
            "capex_yuan_per_kw": math.nan,
            "source_method": "fixed base year; no nuclear expansion cost applied",
            "source_figure": "",
            "source_document": str(config["sources"]["capex_predictions_workbook"]),
        }
    ]
    for row in capex.loc[capex.technology.eq("nuclear")].itertuples(index=False):
        nuclear_rows.append(
            {
                "year": int(row.year),
                "capex_yuan_per_kw": float(row.capex_yuan_per_kw),
                "source_method": row.extraction_method,
                "source_figure": row.source_figure,
                "source_document": row.source_workbook,
            }
        )
    write_csv(pd.DataFrame(nuclear_rows), DATA_ROOT / "technology" / "nuclear_capex_by_year.csv")

    storage = pd.DataFrame(tech["storage"])
    storage["round_trip_efficiency"] = storage.charge_efficiency * storage.discharge_efficiency
    storage["capex_status"] = "AVAILABLE_IN_TECHNOLOGY_CAPEX_BY_YEAR_AS_VISUAL_ESTIMATE"
    storage["source_page"] = 64
    storage["source_document"] = source_pdf
    write_csv(storage, DATA_ROOT / "technology" / "storage_technical_parameters.csv")
    build_phs_capacity_bounds(config, qc)

    transmission = pd.DataFrame(tech["transmission"]["voltage_options"])
    transmission["loss_fraction_per_km"] = tech["transmission"]["loss_fraction_per_km"]
    transmission["substation_lifetime_years"] = tech["transmission"]["substation_lifetime_years"]
    transmission["overhead_line_lifetime_years"] = tech["transmission"]["overhead_line_lifetime_years"]
    transmission["source_page"] = tech["transmission"]["source_page"]
    transmission["source_document"] = source_pdf
    write_csv(transmission, DATA_ROOT / "technology" / "transmission_cost_parameters.csv")

    ccs = pd.DataFrame([{**tech["ccs"], "source_document": source_pdf}])
    write_csv(ccs, DATA_ROOT / "technology" / "ccs_cost_parameters.csv")

    emissions = tech["emissions"]
    emissions_rows = []
    for year in config["planning_years"]:
        year = int(year)
        source_year = 2030 if year == base_year else year
        method = "2030 value held backward for fixed 2025 dispatch accounting" if year == base_year else "CISPO SI value or stated linear interpolation"
        for technology, values in (
            ("coal", emissions["coal_kgco2_per_kwh"]),
            ("gas", emissions["gas_kgco2_per_kwh"]),
            ("bioccs", emissions["beccs_kgco2_per_kwh"]),
        ):
            value = float(values[str(source_year)])
            emissions_rows.append(
                {
                    "technology": technology,
                    "year": year,
                    "emission_factor_kgco2_per_kwh": value,
                    "emission_factor_mtco2_per_gwh": value / 1000.0,
                    "ccs_capture_fraction": emissions["ccs_capture_fraction"] if technology in ("coal", "gas") else math.nan,
                    "source_method": method,
                    "source_page": emissions["source_page"],
                    "source_document": source_pdf,
                }
            )
    write_csv(pd.DataFrame(emissions_rows), DATA_ROOT / "technology" / "emission_factors_by_year.csv")

    dac = tech["dac"]
    wacc = float(tech["finance"]["real_wacc_fraction"])
    dac_crf = capital_recovery_factor(wacc, float(dac["lifetime_years"]))
    gj_per_t_to_gwh_per_mt = 1_000_000.0 / 3600.0
    dac_rows = []
    for technology in dac["technologies"]:
        for year in config["planning_years"]:
            year = int(year)
            if year == base_year:
                ratio = 1.0
                method = "2022 cost anchor held to fixed non-investment 2025 base year"
            else:
                ratio = float(technology["ratios"][str(year)])
                method = "Table S23 conservative Low-uptake projection ratio"
            direct_electricity = float(technology["direct_electricity_gj_per_tco2"]) * gj_per_t_to_gwh_per_mt
            direct_heat = float(technology["direct_heat_gj_per_tco2"]) * gj_per_t_to_gwh_per_mt
            total_electricity = direct_electricity + direct_heat / float(dac["heat_pump_cop"])
            projected_capex = float(technology["capex_yuan_per_tco2_per_year_capacity"]) * ratio
            dac_rows.append(
                {
                    "technology": technology["technology"],
                    "technology_name": technology["name"],
                    "year": year,
                    "cost_projection_ratio_to_2022": ratio,
                    "capex_million_yuan_per_mtco2_per_year_capacity": projected_capex,
                    "annualized_capex_million_yuan_per_mtco2_per_year_capacity_year": projected_capex * dac_crf,
                    "fixed_om_million_yuan_per_mtco2_per_year_capacity_year": float(technology["fixed_om_yuan_per_tco2_per_year_capacity"]) * ratio,
                    "variable_om_yuan_per_tco2": float(technology["variable_om_yuan_per_tco2"]) * ratio,
                    "direct_electricity_gwh_per_mtco2": direct_electricity,
                    "direct_heat_gwh_per_mtco2": direct_heat,
                    "heat_pump_cop": float(dac["heat_pump_cop"]),
                    "total_electricity_with_heat_pump_gwh_per_mtco2": total_electricity,
                    "average_power_gw_per_mtco2_per_year": total_electricity / 8760.0,
                    "lifetime_years": float(dac["lifetime_years"]),
                    "real_wacc_fraction": wacc,
                    "capital_recovery_factor": dac_crf,
                    "source_method": method,
                    "source_pages": dac["source_pages"],
                    "source_document": source_pdf,
                }
            )
    dac_out = pd.DataFrame(dac_rows)
    write_csv(dac_out, DATA_ROOT / "technology" / "dac_parameters_by_year.csv")

    unresolved = pd.DataFrame(tech["unresolved"])
    unresolved["source_document"] = source_pdf
    write_csv(unresolved, DATA_ROOT / "technology" / "unresolved_parameters.csv")
    add_qc(qc, "technology_ruc_rows", len(ruc), "PASS" if len(ruc) == 11 else "FAIL", "10 thermal classes plus nuclear")
    add_qc(qc, "technology_capex_rows", len(capex), "PASS" if len(capex) == expected_capex_rows else "FAIL", "19 technologies x four expansion years")
    add_qc(qc, "technology_dac_rows", len(dac_out), "PASS" if len(dac_out) == 4 * len(config["planning_years"]) else "FAIL", "Four DAC technologies by model year")
    objective_hard_fails = int(unresolved.status.eq("HARD_FAIL_FOR_LONG_TERM_OBJECTIVE").sum())
    network_hard_fails = int(unresolved.status.eq("HARD_FAIL_FOR_NETWORK_CAPACITY").sum())
    trunk_cost_hard_fails = int(unresolved.status.eq("HARD_FAIL_FOR_TRUNK_COST").sum())
    add_qc(qc, "technology_long_term_objective_hard_fail_count", objective_hard_fails, "PASS" if objective_hard_fails == 0 else "FAIL", "CapEx and provincial fuel-price inputs are now present")
    add_qc(qc, "technology_network_capacity_hard_fail_count", network_hard_fails, "PASS" if network_hard_fails == 0 else "WARN", "2025 simultaneous-nameplate proxy supplies initial VRE interface capacity")
    add_qc(qc, "technology_trunk_cost_hard_fail_count", trunk_cost_hard_fails, "WARN" if trunk_cost_hard_fails else "PASS", "Load-center matching and engineering route distance remain unavailable")


def build_fuel_prices(config: dict, qc: list[dict]) -> None:
    with FUEL_CONFIG_PATH.open("r", encoding="utf-8") as stream:
        fuel_config = json.load(stream)
    raw = pd.DataFrame(fuel_config["rows"])
    if len(raw) != 32 or raw.region.duplicated().any():
        raise ValueError("Fuel-price screenshot transcription must contain 32 unique source regions")
    raw["source_evidence"] = fuel_config["source_evidence"]
    raw["price_basis_year"] = fuel_config["price_basis_year"]
    write_csv(raw, DATA_ROOT / "technology" / "fuel_price_source_table_screenshot.csv")

    inner_rows = raw.loc[raw.region.isin(["East Inner Mongolia", "West Inner Mongolia"])]
    if len(inner_rows) != 2:
        raise ValueError("Both East and West Inner Mongolia rows are required")
    numeric_columns = [
        "coal_usd_per_gj", "coal_correlation_r", "gas_usd_per_gj",
        "biomass_usd_per_gj", "biomass_cap_ej",
    ]
    inner = {column: float(inner_rows[column].mean()) for column in numeric_columns}
    inner["region"] = "Inner Mongolia"
    model = pd.concat(
        [raw.loc[~raw.region.isin(["East Inner Mongolia", "West Inner Mongolia"])], pd.DataFrame([inner])],
        ignore_index=True,
    )
    model["province_code"] = model.region.map(EN_TO_CODE)
    if model.province_code.isna().any():
        raise ValueError(f"Unmapped fuel-price regions: {model.loc[model.province_code.isna(), 'region'].tolist()}")
    model["province_code"] = model.province_code.astype(int)
    model["province_name_en"] = model.province_code.map(CODE_TO_EN)
    model["province_name_zh"] = model.province_code.map(CODE_TO_ZH)
    exchange_rate = float(fuel_config["usd_to_yuan"])
    model["coal_yuan_per_gj"] = model.coal_usd_per_gj * exchange_rate
    model["gas_yuan_per_gj"] = model.gas_usd_per_gj * exchange_rate
    model["coal_fuel_available"] = model.coal_yuan_per_gj.notna()
    model["gas_fuel_available"] = model.gas_yuan_per_gj.notna()
    model["usd_to_yuan"] = exchange_rate
    model["price_basis_year"] = fuel_config["price_basis_year"]
    model["temporal_method"] = fuel_config["temporal_method"]
    model["merge_method"] = np.where(
        model.province_name_en.eq("Inner Mongolia"),
        fuel_config["inner_mongolia_merge_method"],
        "direct screenshot province row",
    )
    model["source_evidence"] = fuel_config["source_evidence"]
    model = model.sort_values("province_code")
    write_csv(
        model[
            [
                "province_code", "province_name_en", "province_name_zh",
                "coal_usd_per_gj", "coal_correlation_r", "gas_usd_per_gj",
                "coal_yuan_per_gj", "gas_yuan_per_gj", "coal_fuel_available",
                "gas_fuel_available", "usd_to_yuan", "price_basis_year",
                "temporal_method", "merge_method", "source_evidence",
            ]
        ],
        DATA_ROOT / "technology" / "province_fuel_prices.csv",
    )

    with TECH_CONFIG_PATH.open("r", encoding="utf-8") as stream:
        tech_config = json.load(stream)
    ruc = pd.DataFrame(tech_config["thermal_ruc"]).set_index("technology")
    fuel_technology = {
        "coal": "coal", "coalccs": "coal", "cchp": "coal", "cchpccs": "coal",
        "gas": "gas", "gasccs": "gas", "gchp": "gas", "gchpccs": "gas",
    }
    cost_rows = []
    for province in model.itertuples(index=False):
        for year in config["planning_years"]:
            for technology, fuel in fuel_technology.items():
                price = getattr(province, f"{fuel}_yuan_per_gj")
                available = pd.notna(price)
                fuel_load = float(ruc.loc[technology, "fuel_load_mj_per_kwh"])
                cost_rows.append(
                    {
                        "province_code": int(province.province_code),
                        "province_name_en": province.province_name_en,
                        "province_name_zh": province.province_name_zh,
                        "year": int(year),
                        "technology": technology,
                        "fuel": fuel,
                        "fuel_price_yuan_per_gj": float(price) if available else math.nan,
                        "fuel_load_gj_per_mwh": fuel_load,
                        "fuel_cost_yuan_per_mwh": float(price) * fuel_load if available else math.nan,
                        "dispatch_allowed": bool(available),
                        "new_capacity_allowed": bool(available) and int(year) in config["capacity_expansion_years"],
                        "price_temporal_method": fuel_config["temporal_method"],
                        "source_evidence": fuel_config["source_evidence"],
                    }
                )
    generation_cost = pd.DataFrame(cost_rows)
    write_csv(generation_cost, DATA_ROOT / "technology" / "province_fuel_generation_cost_by_year.csv")
    add_qc(qc, "fuel_price_source_rows", len(raw), "PASS" if len(raw) == 32 else "FAIL", "Screenshot contains 32 regions because Inner Mongolia is split")
    add_qc(qc, "fuel_price_model_province_rows", len(model), "PASS" if len(model) == 31 else "FAIL", "East/West Inner Mongolia merged by arithmetic mean")
    add_qc(qc, "fuel_price_missing_coal_provinces", int(model.coal_yuan_per_gj.isna().sum()), "WARN", "Beijing and Tibet coal prices are blank; coal technologies disabled there")
    add_qc(qc, "fuel_price_missing_gas_provinces", int(model.gas_yuan_per_gj.isna().sum()), "PASS" if model.gas_yuan_per_gj.notna().all() else "FAIL", "All 31 provinces require gas prices")
    add_qc(qc, "fuel_generation_cost_rows", len(generation_cost), "PASS" if len(generation_cost) == 31 * len(config["planning_years"]) * 8 else "FAIL", "31 provinces x model years x eight coal/gas classes")


def lonlat_to_unit_sphere(lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    lon_rad = np.radians(lon.astype(float))
    lat_rad = np.radians(lat.astype(float))
    cos_lat = np.cos(lat_rad)
    return np.column_stack((cos_lat * np.cos(lon_rad), cos_lat * np.sin(lon_rad), np.sin(lat_rad)))


def normalize_city_zh(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = re.sub(r"\s+", "", str(value).strip())
    if not text:
        return None
    for suffix in ("藏族自治州", "回族自治州", "蒙古自治州", "哈萨克自治州", "自治州", "地区", "市", "盟"):
        if text.endswith(suffix):
            return text[: -len(suffix)]
    return text


def recover_gb18030_dbf_text(value: object) -> str:
    """Recover legacy DBF text that ArcPy exposes as latin-1 mojibake."""
    text = "" if value is None else str(value).strip()
    if re.search(r"[\u4e00-\u9fff]", text):
        return text
    try:
        return text.encode("latin1").decode("gb18030")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def build_city_load_centers(
    config: dict,
    substations: pd.DataFrame,
    qc: list[dict],
) -> None:
    """Build city-scale load centers and geodesic substation-to-center links."""
    try:
        import arcpy
    except ImportError as exc:  # pragma: no cover - environment diagnostic
        raise RuntimeError("ArcGIS Pro Python with arcpy is required for city load-center construction") from exc

    weights = pd.read_csv(config["sources"]["city_monthly_power_weights"])
    required_weight_columns = {
        "province_cn", "city_cn", "month", "city_power_mwh", "city_weight_in_province",
    }
    if not required_weight_columns.issubset(weights.columns):
        raise ValueError(f"City power weights missing columns: {sorted(required_weight_columns - set(weights.columns))}")
    weights["province_cn"] = weights.province_cn.map(normalize_zh_province)
    weights["city_cn"] = weights.city_cn.map(normalize_city_zh)
    annual_observed = (
        weights.groupby(["province_cn", "city_cn"], as_index=False)
        .agg(
            annual_city_power_mwh=("city_power_mwh", "sum"),
            monthly_weight_mean=("city_weight_in_province", "mean"),
            month_count=("month", "nunique"),
        )
    )
    if len(annual_observed) != 296 or annual_observed.province_cn.nunique() != 31 or not annual_observed.month_count.eq(12).all():
        raise ValueError("Expected 296 cities, 31 provinces and 12 months in city electricity weights")
    observed_keys = set(map(tuple, annual_observed[["province_cn", "city_cn"]].itertuples(index=False, name=None)))
    model_provinces = set(annual_observed.province_cn)

    city_path = config["sources"]["city_boundary_shapefile"]
    spatial_reference = arcpy.Describe(str(city_path)).spatialReference
    city_shapes: dict[tuple[str, str], dict[str, object]] = {}
    with arcpy.da.SearchCursor(str(city_path), ["name", "gb", "省", "SHAPE@"]) as cursor:
        for name, code, province, geometry in cursor:
            key = (normalize_zh_province(province), normalize_city_zh(name))
            if key[0] not in model_provinces:
                continue
            area_km2 = float(geometry.getArea("GEODESIC", "SQUAREKILOMETERS"))
            current = city_shapes.get(key)
            if current is None or area_km2 > float(current["area_km2"]):
                city_shapes[key] = {
                    "source_city_code": str(code),
                    "geometry": geometry,
                    "area_km2": area_km2,
                }
    missing_city_shapes = sorted(observed_keys - set(city_shapes))
    if missing_city_shapes:
        raise ValueError(f"City electricity weights lack matching boundaries: {missing_city_shapes[:20]}")

    municipality_names = {"北京", "天津", "上海", "重庆"}
    county_aggregates: defaultdict[tuple[str, str], dict[str, float]] = defaultdict(
        lambda: {"weighted_lon": 0.0, "weighted_lat": 0.0, "urban_population": 0.0, "total_population": 0.0, "county_count": 0.0}
    )
    county_path = config["sources"]["county_population_shapefile"]
    with arcpy.da.SearchCursor(str(county_path), ["省级", "地级", "合计", "城镇人口", "SHAPE@TRUECENTROID"]) as cursor:
        for province_raw, prefecture_raw, total_population, urban_population, xy in cursor:
            province = normalize_zh_province(recover_gb18030_dbf_text(province_raw))
            city = province if province in municipality_names else normalize_city_zh(recover_gb18030_dbf_text(prefecture_raw))
            key = (province, city)
            if key not in city_shapes or xy is None:
                continue
            urban = float(urban_population or 0.0)
            total = float(total_population or 0.0)
            weight = urban if urban > 0 else total
            if weight <= 0:
                continue
            aggregate = county_aggregates[key]
            aggregate["weighted_lon"] += float(xy[0]) * weight
            aggregate["weighted_lat"] += float(xy[1]) * weight
            aggregate["urban_population"] += urban
            aggregate["total_population"] += total
            aggregate["county_count"] += 1.0

    complete_keys = set(city_shapes) & set(county_aggregates)
    if not observed_keys.issubset(complete_keys):
        missing_population = sorted(observed_keys - complete_keys)
        raise ValueError(f"Observed city weights lack population/boundary support: {missing_population[:20]}")
    population_rows = [
        {
            "province_cn": key[0],
            "city_cn": key[1],
            "urban_population": values["urban_population"],
            "total_population": values["total_population"],
            "county_count": int(values["county_count"]),
        }
        for key, values in county_aggregates.items()
        if key in complete_keys and values["urban_population"] > 0
    ]
    population_table = pd.DataFrame(population_rows)
    annual = population_table.merge(
        annual_observed,
        on=["province_cn", "city_cn"],
        how="left",
        validate="one_to_one",
    )
    observed_mask = annual.annual_city_power_mwh.notna()
    observed_by_province = annual.loc[observed_mask].groupby("province_cn").agg(
        observed_power=("annual_city_power_mwh", "sum"),
        observed_urban_population=("urban_population", "sum"),
    )
    province_intensity = (observed_by_province.observed_power / observed_by_province.observed_urban_population).to_dict()
    annual["electricity_weight_method"] = np.where(
        observed_mask,
        "observed_2022_city_table",
        "imputed_province_power_per_urban_population",
    )
    annual.loc[~observed_mask, "annual_city_power_mwh"] = (
        annual.loc[~observed_mask, "urban_population"]
        * annual.loc[~observed_mask, "province_cn"].map(province_intensity)
    )
    annual["annual_city_power_share_in_province"] = annual.annual_city_power_mwh / annual.groupby("province_cn").annual_city_power_mwh.transform("sum")
    annual_share_error = annual.groupby("province_cn").annual_city_power_share_in_province.sum().sub(1.0).abs()
    if annual_share_error.max() > 1e-9:
        raise ValueError("Completed annual city electricity shares do not close within province")
    missing_weight_cities = annual.loc[
        annual.electricity_weight_method.eq("imputed_province_power_per_urban_population"),
        ["province_cn", "city_cn", "urban_population", "annual_city_power_mwh", "annual_city_power_share_in_province", "electricity_weight_method"],
    ].sort_values(["province_cn", "city_cn"])
    write_csv(missing_weight_cities, DATA_ROOT / "grid" / "city_load_center_imputed_weights.csv")

    load_center_rows = []
    outside_weighted_point_count = 0
    for row in annual.sort_values(["province_cn", "city_cn"]).itertuples(index=False):
        key = (row.province_cn, row.city_cn)
        shape_record = city_shapes[key]
        geometry = shape_record["geometry"]
        population = county_aggregates[key]
        if population["urban_population"] > 0:
            lon = population["weighted_lon"] / population["urban_population"]
            lat = population["weighted_lat"] / population["urban_population"]
            center_method = "urban_population_weighted_county_centroids"
            county_count = int(population["county_count"])
            urban_population = population["urban_population"]
            total_population = population["total_population"]
        else:
            label_point = geometry.labelPoint
            lon, lat = float(label_point.X), float(label_point.Y)
            center_method = "city_polygon_label_point_no_population_match"
            county_count = 0
            urban_population = math.nan
            total_population = math.nan
        point_geometry = arcpy.PointGeometry(arcpy.Point(float(lon), float(lat)), spatial_reference)
        if not geometry.contains(point_geometry):
            label_point = geometry.labelPoint
            lon, lat = float(label_point.X), float(label_point.Y)
            center_method += "_snapped_to_inside_label_point"
            outside_weighted_point_count += 1
        province_code = ZH_TO_CODE.get(row.province_cn)
        if province_code is None:
            raise ValueError(f"Unmapped load-center province: {row.province_cn}")
        load_center_rows.append(
            {
                "load_center_id": f"LC_{shape_record['source_city_code']}",
                "source_city_code": shape_record["source_city_code"],
                "province_code": int(province_code),
                "province_name_en": CODE_TO_EN[int(province_code)],
                "province_name_zh": row.province_cn,
                "city_name_zh": row.city_cn,
                "lon": float(lon),
                "lat": float(lat),
                "annual_city_power_mwh": float(row.annual_city_power_mwh),
                "annual_city_power_share_in_province": float(row.annual_city_power_share_in_province),
                "monthly_weight_mean": float(row.monthly_weight_mean) if pd.notna(row.monthly_weight_mean) else math.nan,
                "electricity_weight_method": row.electricity_weight_method,
                "city_area_km2": float(shape_record["area_km2"]),
                "county_count": county_count,
                "urban_population": urban_population,
                "total_population": total_population,
                "center_method": center_method,
                "electricity_weight_year": 2022,
                "population_source_note": "county urban population field; source year follows local population shapefile metadata",
            }
        )
    load_centers = pd.DataFrame(load_center_rows).sort_values(["province_code", "city_name_zh"]).reset_index(drop=True)

    mapping_parts = []
    for province_code, province_substations in substations.groupby("province_code", sort=True):
        province_centers = load_centers.loc[load_centers.province_code.eq(int(province_code))].reset_index(drop=True)
        if province_centers.empty:
            raise ValueError(f"No city load center for province {province_code}")
        tree = cKDTree(lonlat_to_unit_sphere(province_centers.lon.to_numpy(), province_centers.lat.to_numpy()))
        chord, positions = tree.query(
            lonlat_to_unit_sphere(province_substations.lon.to_numpy(), province_substations.lat.to_numpy()),
            k=1,
        )
        distance_km = 6371.0088 * 2.0 * np.arcsin(np.clip(chord / 2.0, 0.0, 1.0))
        chosen = province_centers.iloc[positions].reset_index(drop=True)
        part = province_substations[
            ["substation_id", "province_code", "province_name_en", "province_name_zh", "lon", "lat", "max_voltage_kv"]
        ].reset_index(drop=True)
        part["load_center_id"] = chosen.load_center_id.to_numpy()
        part["load_center_city_name_zh"] = chosen.city_name_zh.to_numpy()
        part["load_center_lon"] = chosen.lon.to_numpy()
        part["load_center_lat"] = chosen.lat.to_numpy()
        part["load_center_annual_power_share_in_province"] = chosen.annual_city_power_share_in_province.to_numpy()
        part["trunk_distance_km"] = distance_km
        part["load_center_assignment_method"] = "nearest_city_load_center_within_same_province"
        part["route_status"] = "great_circle_proxy_not_engineering_route"
        mapping_parts.append(part)
    mapping = pd.concat(mapping_parts, ignore_index=True).sort_values("substation_id").reset_index(drop=True)
    write_csv(mapping, DATA_ROOT / "grid" / "substation_to_load_center.csv")

    city_station_keys = []
    city_records_by_province: defaultdict[int, list[tuple[tuple[str, str], object, float]]] = defaultdict(list)
    for key, shape_record in city_shapes.items():
        province_code = ZH_TO_CODE.get(key[0])
        if province_code is not None:
            city_records_by_province[int(province_code)].append((key, shape_record["geometry"], float(shape_record["area_km2"])))
    polygon_fallback_count = 0
    nearest_center_lookup = mapping.set_index("substation_id").load_center_city_name_zh
    for row in substations.itertuples(index=False):
        point_geometry = arcpy.PointGeometry(arcpy.Point(float(row.lon), float(row.lat)), spatial_reference)
        containing = [record for record in city_records_by_province[int(row.province_code)] if record[1].contains(point_geometry)]
        if containing:
            key = min(containing, key=lambda record: record[2])[0]
        else:
            key = (normalize_zh_province(row.province_name_zh), str(nearest_center_lookup.loc[row.substation_id]))
            polygon_fallback_count += 1
        city_station_keys.append(key)
    density = substations[["substation_id", "max_voltage_kv"]].copy()
    density["province_cn"] = [key[0] for key in city_station_keys]
    density["city_cn"] = [key[1] for key in city_station_keys]
    density["voltage_weighted_units_220kv"] = density.max_voltage_kv / 220.0
    density_summary = density.groupby(["province_cn", "city_cn"], as_index=False).agg(
        substation_count_220kv_plus=("substation_id", "nunique"),
        voltage_weighted_substation_units=("voltage_weighted_units_220kv", "sum"),
        maximum_substation_voltage_kv=("max_voltage_kv", "max"),
    )
    load_centers = load_centers.merge(
        density_summary,
        left_on=["province_name_zh", "city_name_zh"],
        right_on=["province_cn", "city_cn"],
        how="left",
    ).drop(columns=["province_cn", "city_cn"], errors="ignore")
    for column in ("substation_count_220kv_plus", "voltage_weighted_substation_units", "maximum_substation_voltage_kv"):
        load_centers[column] = load_centers[column].fillna(0)
    load_centers["substations_per_10000_km2"] = load_centers.substation_count_220kv_plus / load_centers.city_area_km2 * 10000.0
    load_centers["voltage_weighted_units_per_10000_km2"] = load_centers.voltage_weighted_substation_units / load_centers.city_area_km2 * 10000.0
    load_centers["substation_count_share_in_province"] = load_centers.substation_count_220kv_plus / load_centers.groupby("province_code").substation_count_220kv_plus.transform("sum")
    load_centers["voltage_weight_share_in_province"] = load_centers.voltage_weighted_substation_units / load_centers.groupby("province_code").voltage_weighted_substation_units.transform("sum")
    load_centers["substation_density_role"] = "validation_and_sensitivity_only_not_primary_load_weight"
    write_csv(load_centers, DATA_ROOT / "grid" / "city_load_centers.csv")

    observed_city = load_centers.electricity_weight_method.eq("observed_2022_city_table")
    valid_count = observed_city & load_centers.substation_count_share_in_province.notna()
    valid_voltage = observed_city & load_centers.voltage_weight_share_in_province.notna()
    count_spearman = float(load_centers.loc[valid_count, ["annual_city_power_share_in_province", "substation_count_share_in_province"]].corr(method="spearman").iloc[0, 1])
    voltage_spearman = float(load_centers.loc[valid_voltage, ["annual_city_power_share_in_province", "voltage_weight_share_in_province"]].corr(method="spearman").iloc[0, 1])
    validation = pd.DataFrame(
        [
            {
                "proxy": "substation_count_share_in_province",
                "city_count": int(valid_count.sum()),
                "spearman_vs_annual_city_power_share": count_spearman,
                "mean_absolute_share_error": float((load_centers.loc[valid_count, "substation_count_share_in_province"] - load_centers.loc[valid_count, "annual_city_power_share_in_province"]).abs().mean()),
                "recommended_role": "validation_and_sensitivity_only",
            },
            {
                "proxy": "voltage_weight_share_in_province",
                "city_count": int(valid_voltage.sum()),
                "spearman_vs_annual_city_power_share": voltage_spearman,
                "mean_absolute_share_error": float((load_centers.loc[valid_voltage, "voltage_weight_share_in_province"] - load_centers.loc[valid_voltage, "annual_city_power_share_in_province"]).abs().mean()),
                "recommended_role": "validation_and_sensitivity_only",
            },
        ]
    )
    write_csv(validation, DATA_ROOT / "grid" / "load_center_proxy_validation.csv")

    station_initial_path = DATA_ROOT / "grid" / "substation_initial_capacity_2025.csv"
    station_initial = pd.read_csv(station_initial_path)
    station_initial = station_initial.drop(
        columns=[
            "load_center_id", "load_center_city_name_zh", "load_center_lon", "load_center_lat",
            "trunk_distance_km", "load_center_assignment_method", "load_center_route_status",
        ],
        errors="ignore",
    ).merge(
        mapping[
            [
                "substation_id", "load_center_id", "load_center_city_name_zh", "load_center_lon",
                "load_center_lat", "trunk_distance_km", "load_center_assignment_method", "route_status",
            ]
        ],
        on="substation_id",
        how="left",
        validate="one_to_one",
    )
    station_initial = station_initial.rename(columns={"route_status": "load_center_route_status"})
    write_csv(station_initial, station_initial_path)

    add_qc(qc, "city_load_center_rows", len(load_centers), "PASS" if len(load_centers) == 337 else "FAIL", "296 observed city weights plus 41 population-imputed prefectures")
    add_qc(qc, "city_load_center_observed_weight_rows", int(load_centers.electricity_weight_method.eq("observed_2022_city_table").sum()), "PASS" if int(load_centers.electricity_weight_method.eq("observed_2022_city_table").sum()) == 296 else "FAIL", "Observed 2022 city electricity rows")
    add_qc(qc, "city_load_center_imputed_weight_rows", len(missing_weight_cities), "WARN" if len(missing_weight_cities) else "PASS", "Autonomous prefectures and other uncovered cities imputed by province electricity per urban population")
    add_qc(qc, "city_load_center_province_count", load_centers.province_code.nunique(), "PASS" if load_centers.province_code.nunique() == 31 else "FAIL", "31 model provinces")
    add_qc(qc, "city_load_center_annual_share_max_error", float(annual_share_error.max()), "PASS" if annual_share_error.max() <= 1e-9 else "FAIL", "Annual city electricity shares close to one within each province")
    add_qc(qc, "city_load_center_inside_fallback_count", outside_weighted_point_count, "WARN" if outside_weighted_point_count else "PASS", "Weighted points outside multipart city polygons use inside label points")
    add_qc(qc, "substation_city_polygon_fallback_count", polygon_fallback_count, "WARN" if polygon_fallback_count else "PASS", "Boundary/coastal OSM points use nearest same-province city center for density attribution")
    add_qc(qc, "substation_load_center_mapping_rows", len(mapping), "PASS" if len(mapping) == len(substations) else "FAIL", "Every eligible OSM substation mapped within province")
    add_qc(qc, "trunk_distance_p95_km", round(float(mapping.trunk_distance_km.quantile(0.95)), 3), "PASS", "Great-circle city-load-center proxy")
    add_qc(qc, "trunk_distance_max_km", round(float(mapping.trunk_distance_km.max()), 3), "WARN", "Review remote substations and large western prefectures")
    add_qc(qc, "substation_count_share_spearman_vs_city_power", round(count_spearman, 4), "WARN", "Diagnostic of whether substation density can proxy city load share")
    add_qc(qc, "substation_voltage_share_spearman_vs_city_power", round(voltage_spearman, 4), "WARN", "Diagnostic of whether voltage-weighted density can proxy city load share")


def build_initial_intra_grid_capacity(
    config: dict,
    points: pd.DataFrame,
    connections: pd.DataFrame,
    substations: pd.DataFrame,
    qc: list[dict],
) -> None:
    """Infer 2025 VRE spur/trunk baselines without claiming observed station ratings.

    The configured default is the user-requested simultaneous-nameplate stress case.
    A weather-year hourly coincident-peak comparator is retained because it follows the
    logic of CISPO equations S4-18 and S4-19 more closely.
    """
    try:
        import zarr
    except ImportError as exc:  # pragma: no cover - environment diagnostic
        raise RuntimeError("zarr is required for initial intra-grid capacity inference") from exc

    settings = config["grid_connection"]
    weather_year = int(settings["initial_capacity_weather_year"])
    default_method = settings["initial_capacity_method"]
    if default_method != "simultaneous_2025_nameplate_stress":
        raise ValueError(f"Unsupported initial intra-grid capacity method: {default_method}")

    def read_cf_columns(group: object, positions: np.ndarray) -> np.ndarray:
        dimensions = list(group["cf"].attrs["_ARRAY_DIMENSIONS"])
        if dimensions == ["time", "grid_id"]:
            values = group["cf"].oindex[:, positions]
        elif dimensions == ["grid_id", "time"]:
            values = group["cf"].oindex[positions, :].T
        else:
            raise ValueError(f"Unexpected CF dimension order: {dimensions}")
        return np.asarray(values, dtype=np.float32)

    base = points.merge(
        connections[
            [
                "grid_uid", "substation_id", "nearest_substation_distance_km",
                "onwind_spur_distance_km", "upv_spur_distance_km",
                "dpv_spur_distance_km", "offwind_export_distance_km",
            ]
        ],
        on="grid_uid",
        how="left",
        validate="one_to_one",
    )
    if base.substation_id.isna().any():
        raise ValueError("Every model point must be assigned to a substation before capacity inference")

    technology_specs = {
        "onwind": ("existing_onwind_gw", "onshore_wind", "onwind_spur_distance_km", True),
        "offwind": ("existing_offwind_gw", "offshore_wind", "offwind_export_distance_km", True),
        "upv": ("existing_upv_gw", "pv", "upv_spur_distance_km", True),
        "dpv": ("existing_dpv_gw", None, "dpv_spur_distance_km", False),
    }
    substation_ids = substations.substation_id.tolist()
    substation_position = {substation_id: position for position, substation_id in enumerate(substation_ids)}
    station_hourly: np.ndarray | None = None
    station_technology_capacity = {
        technology: np.zeros(len(substations), dtype=np.float64) for technology in technology_specs
    }
    point_rows: list[pd.DataFrame] = []
    cf_sources: list[str] = []
    local_time_values: np.ndarray | None = None

    for technology, (capacity_column, cf_technology, distance_column, connection_required) in technology_specs.items():
        active = base.loc[
            base[capacity_column].gt(0),
            [
                "grid_uid", "grid_id", "province_code", "province_name_en", "province_name_zh",
                "lon", "lat", "is_land", "substation_id", capacity_column, distance_column,
            ],
        ].copy()
        active = active.rename(columns={capacity_column: "existing_capacity_gw", distance_column: "connection_distance_km"})
        active["technology"] = technology
        active["connection_required"] = connection_required
        active["cf_weather_year"] = weather_year if connection_required else pd.NA
        active["historical_proxy_peak_cf"] = np.nan
        active["paper_formula_spur_capacity_gw"] = 0.0
        active["simultaneous_nameplate_spur_capacity_gw"] = active.existing_capacity_gw if connection_required else 0.0
        active["initial_spur_capacity_gw"] = active.simultaneous_nameplate_spur_capacity_gw
        active["initial_capacity_method"] = default_method
        active["paper_source_document"] = str(config["sources"]["ees_supplement_pdf"])
        active["paper_source_pages"] = "PDF 47-49 and 81-82; SI sections S3.3.2 and S4.3.4"
        active["paper_source_equations"] = "S4-18 and S4-19"
        active["cf_source_path"] = ""
        active["cf_grid_id_used"] = pd.NA
        active["cf_fallback_method"] = "not_applicable"
        active["cf_fallback_distance_km"] = np.nan
        active["interpretation"] = np.where(
            connection_required,
            "conservative inferred minimum; not observed line or substation rating",
            "DPV treated at load center with zero spur/trunk capacity",
        )

        positions = active.substation_id.map(substation_position).to_numpy(dtype=int)
        np.add.at(station_technology_capacity[technology], positions, active.existing_capacity_gw.to_numpy(dtype=float))

        if connection_required and not active.empty:
            store = config["sources"]["hourly_cf_root"] / cf_technology / f"cf_hourly_{cf_technology}_{weather_year}.zarr"
            group = zarr.open_group(str(store), mode="r")
            grid_ids = np.asarray(group["grid_id"][:], dtype=np.int64)
            grid_position = {int(grid_id): position for position, grid_id in enumerate(grid_ids)}
            cf_time_size = int(group["time"].shape[0])
            cf = np.empty((cf_time_size, len(active)), dtype=np.float32)
            resolved_grid_ids = active.grid_id.astype(int).to_numpy(copy=True)
            resolved_source_paths = np.full(len(active), str(store), dtype=object)
            fallback_method = np.full(len(active), "same_grid_primary_technology", dtype=object)
            fallback_distance = np.zeros(len(active), dtype=float)
            primary_mask = active.grid_id.astype(int).isin(grid_position).to_numpy()
            if primary_mask.any():
                selected_positions = np.asarray(
                    [grid_position[int(grid_id)] for grid_id in active.loc[primary_mask, "grid_id"]],
                    dtype=int,
                )
                cf[:, primary_mask] = read_cf_columns(group, selected_positions)

            missing_mask = ~primary_mask
            if missing_mask.any() and technology in {"onwind", "offwind"}:
                fallback_store = config["sources"]["hourly_cf_root"] / "mixed_wind" / f"cf_hourly_mixed_wind_{weather_year}.zarr"
                fallback_group = zarr.open_group(str(fallback_store), mode="r")
                fallback_ids = np.asarray(fallback_group["grid_id"][:], dtype=np.int64)
                fallback_position = {int(grid_id): position for position, grid_id in enumerate(fallback_ids)}
                unresolved = active.loc[missing_mask & ~active.grid_id.astype(int).isin(fallback_position), "grid_id"].tolist()
                if unresolved:
                    raise ValueError(f"Missing mixed-wind fallback for active {technology} grid_ids: {unresolved[:10]}")
                fallback_selected = np.asarray(
                    [fallback_position[int(grid_id)] for grid_id in active.loc[missing_mask, "grid_id"]],
                    dtype=int,
                )
                cf[:, missing_mask] = read_cf_columns(fallback_group, fallback_selected)
                fallback_method[missing_mask] = "same_grid_mixed_wind_for_land_sea_mask_mismatch"
                resolved_source_paths[missing_mask] = str(fallback_store)
                cf_sources.append(str(fallback_store))
            elif missing_mask.any() and technology == "upv":
                available_grid_ids = set(grid_position)
                for province_code in sorted(active.loc[missing_mask, "province_code"].astype(int).unique()):
                    target_mask = missing_mask & active.province_code.eq(province_code).to_numpy()
                    candidates = base.loc[
                        base.province_code.eq(province_code)
                        & base.is_land.eq(1)
                        & base.grid_id.astype(int).isin(available_grid_ids),
                        ["grid_id", "lon", "lat"],
                    ].drop_duplicates("grid_id")
                    if candidates.empty:
                        raise ValueError(f"No same-province land PV fallback grids for province {province_code}")
                    tree = cKDTree(lonlat_to_unit_sphere(candidates.lon.to_numpy(), candidates.lat.to_numpy()))
                    chord, candidate_positions = tree.query(
                        lonlat_to_unit_sphere(
                            active.loc[target_mask, "lon"].to_numpy(),
                            active.loc[target_mask, "lat"].to_numpy(),
                        ),
                        k=1,
                    )
                    chosen_grid_ids = candidates.iloc[np.asarray(candidate_positions, dtype=int)].grid_id.astype(int).to_numpy()
                    target_indices = np.flatnonzero(target_mask)
                    resolved_grid_ids[target_indices] = chosen_grid_ids
                    fallback_distance[target_indices] = 6371.0088 * 2.0 * np.arcsin(np.clip(np.asarray(chord) / 2.0, 0.0, 1.0))
                    fallback_method[target_indices] = "nearest_same_province_land_pv_grid"
                    fallback_selected = np.asarray([grid_position[int(grid_id)] for grid_id in chosen_grid_ids], dtype=int)
                    cf[:, target_indices] = read_cf_columns(group, fallback_selected)
            elif missing_mask.any():
                raise ValueError(f"No CF fallback rule for {technology}")

            if cf.ndim != 2 or cf.shape[1] != len(active):
                raise ValueError(f"Unexpected CF slice shape for {technology}: {cf.shape}")
            if station_hourly is None:
                station_hourly = np.zeros((cf.shape[0], len(substations)), dtype=np.float32)
                local_time_values = np.asarray(group["time"][:], dtype=np.int64)
            elif station_hourly.shape[0] != cf.shape[0]:
                raise ValueError("Hourly CF stores do not share a common time dimension")
            peak_cf = np.nanmax(cf, axis=0).astype(float)
            active["historical_proxy_peak_cf"] = peak_cf
            active["paper_formula_spur_capacity_gw"] = active.existing_capacity_gw.to_numpy(dtype=float) * peak_cf
            active["cf_source_path"] = resolved_source_paths
            active["cf_grid_id_used"] = resolved_grid_ids
            active["cf_fallback_method"] = fallback_method
            active["cf_fallback_distance_km"] = fallback_distance
            output = cf * active.existing_capacity_gw.to_numpy(dtype=np.float32)[None, :]
            mapping = csr_matrix(
                (np.ones(len(active), dtype=np.float32), (np.arange(len(active)), positions)),
                shape=(len(active), len(substations)),
            )
            station_hourly += mapping.T.dot(output.T).T
            cf_sources.append(str(store))
        point_rows.append(active)

    spur = pd.concat(point_rows, ignore_index=True).sort_values(["province_code", "grid_id", "technology"])
    write_csv(spur, DATA_ROOT / "grid" / "initial_spur_capacity_2025.csv")

    if station_hourly is None or local_time_values is None:
        raise ValueError("No connected 2025 VRE capacity was available for trunk inference")
    peak_hour_index = np.argmax(station_hourly, axis=0)
    coincident_peak = station_hourly[peak_hour_index, np.arange(len(substations))].astype(float)
    active_station = np.sum(station_hourly, axis=0) > 0
    peak_time = np.full(len(substations), "", dtype=object)
    peak_time[active_station] = [
        (pd.Timestamp(f"{weather_year}-01-01 08:00:00") + pd.Timedelta(hours=int(local_time_values[index]))).isoformat()
        for index in peak_hour_index[active_station]
    ]

    paper_spur_by_station = (
        spur.loc[spur.connection_required]
        .groupby("substation_id", observed=True).paper_formula_spur_capacity_gw.sum()
        .reindex(substation_ids, fill_value=0.0)
        .to_numpy(dtype=float)
    )
    station = substations[
        [
            "substation_id", "province_code", "province_name_en", "province_name_zh",
            "lon", "lat", "max_voltage_kv", "substation_type",
        ]
    ].copy()
    for technology, values in station_technology_capacity.items():
        station[f"existing_{technology}_gw"] = values
    station["connected_vre_nameplate_gw"] = (
        station.existing_onwind_gw + station.existing_offwind_gw + station.existing_upv_gw
    )
    station["existing_dpv_local_gw"] = station.existing_dpv_gw
    station["sum_point_paper_spur_capacity_gw"] = paper_spur_by_station
    station["paper_proxy_coincident_peak_trunk_gw"] = coincident_peak
    station["paper_proxy_peak_hour_index"] = np.where(active_station, peak_hour_index, -1)
    station["paper_proxy_peak_time_beijing"] = peak_time
    station["simultaneous_nameplate_trunk_capacity_gw"] = station.connected_vre_nameplate_gw
    station["initial_trunk_capacity_gw"] = station.simultaneous_nameplate_trunk_capacity_gw
    station["initial_substation_vre_interface_capacity_gw"] = station.initial_trunk_capacity_gw
    station["initial_capacity_method"] = default_method
    station["paper_comparator_method"] = settings["paper_comparator_method"]
    station["cf_weather_year"] = weather_year
    station["rated_capacity_status"] = "inferred VRE interface requirement; not observed equipment rating"
    station["load_center_route_status"] = "not_available_capacity_only"
    station["paper_source_document"] = str(config["sources"]["ees_supplement_pdf"])
    station["paper_source_pages"] = "PDF 47-49 and 81-82; SI sections S3.3.2 and S4.3.4"
    station["paper_source_equations"] = "S4-18 and S4-19"
    station["cf_source_paths"] = ";".join(cf_sources)
    write_csv(station, DATA_ROOT / "grid" / "substation_initial_capacity_2025.csv")

    province_hourly = np.zeros((station_hourly.shape[0], len(PROVINCE_DF)), dtype=np.float32)
    province_position = {int(code): index for index, code in enumerate(PROVINCE_DF.province_code)}
    station_province_positions = np.asarray([province_position[int(code)] for code in station.province_code], dtype=int)
    station_to_province = csr_matrix(
        (np.ones(len(station), dtype=np.float32), (np.arange(len(station)), station_province_positions)),
        shape=(len(station), len(PROVINCE_DF)),
    )
    province_hourly += station_to_province.T.dot(station_hourly.T).T
    province_peak = np.max(province_hourly, axis=0).astype(float)
    province = (
        station.groupby(["province_code", "province_name_en", "province_name_zh"], as_index=False)
        .agg(
            connected_vre_nameplate_gw=("connected_vre_nameplate_gw", "sum"),
            existing_dpv_local_gw=("existing_dpv_local_gw", "sum"),
            sum_substation_paper_proxy_peak_gw=("paper_proxy_coincident_peak_trunk_gw", "sum"),
            initial_trunk_capacity_gw=("initial_trunk_capacity_gw", "sum"),
            active_substations=("connected_vre_nameplate_gw", lambda values: int((values > 0).sum())),
        )
        .sort_values("province_code")
    )
    province["province_coincident_peak_output_gw"] = province_peak
    province["initial_capacity_method"] = default_method
    province["cf_weather_year"] = weather_year
    write_csv(province, DATA_ROOT / "grid" / "province_initial_intra_grid_capacity_2025.csv")

    connected_nameplate = float(station.connected_vre_nameplate_gw.sum())
    expected_connected = float(points[["existing_onwind_gw", "existing_offwind_gw", "existing_upv_gw"]].sum().sum())
    dpv_local = float(station.existing_dpv_local_gw.sum())
    expected_dpv = float(points.existing_dpv_gw.sum())
    add_qc(qc, "initial_spur_positive_capacity_rows", len(spur), "PASS" if len(spur) > 0 else "FAIL", "Positive 2025 existing-capacity technology-point pairs including DPV")
    add_qc(qc, "initial_connected_vre_nameplate_gw", round(connected_nameplate, 6), "PASS" if np.isclose(connected_nameplate, expected_connected) else "FAIL", "Onshore wind + offshore wind + UPV capacity closure")
    add_qc(qc, "initial_dpv_local_capacity_gw", round(dpv_local, 6), "PASS" if np.isclose(dpv_local, expected_dpv) else "FAIL", "DPV retained but excluded from spur/trunk capacity")
    add_qc(qc, "initial_trunk_equals_nameplate_stress", float(np.abs(station.initial_trunk_capacity_gw - station.connected_vre_nameplate_gw).max()), "PASS" if np.allclose(station.initial_trunk_capacity_gw, station.connected_vre_nameplate_gw) else "FAIL", "User-requested simultaneous 2025 nameplate stress case")
    add_qc(qc, "paper_proxy_trunk_not_above_nameplate", float((station.paper_proxy_coincident_peak_trunk_gw - station.connected_vre_nameplate_gw).max()), "PASS" if (station.paper_proxy_coincident_peak_trunk_gw <= station.connected_vre_nameplate_gw + 1e-6).all() else "FAIL", "Hourly coincident peak must not exceed connected nameplate")
    add_qc(qc, "paper_proxy_trunk_not_above_sum_point_peaks", float((station.paper_proxy_coincident_peak_trunk_gw - station.sum_point_paper_spur_capacity_gw).max()), "PASS" if (station.paper_proxy_coincident_peak_trunk_gw <= station.sum_point_paper_spur_capacity_gw + 1e-6).all() else "FAIL", "Coincident aggregate peak must not exceed sum of point peaks")
    fallback_rows = spur.loc[spur.connection_required & ~spur.cf_fallback_method.eq("same_grid_primary_technology")]
    add_qc(qc, "initial_capacity_cf_fallback_rows", len(fallback_rows), "WARN" if len(fallback_rows) else "PASS", "Coastal mask mismatches use explicit mixed-wind or nearest-land-PV fallback profiles")
    add_qc(qc, "initial_capacity_pv_fallback_max_distance_km", round(float(fallback_rows.loc[fallback_rows.technology.eq("upv"), "cf_fallback_distance_km"].max()), 3), "WARN", "Review nearest-land PV fallback distances for sea-centered installed-capacity points")
    add_qc(qc, "substation_rated_capacity_status", "proxy_only", "WARN", "EES and OSM do not provide observed station ratings or available bays")


def build_grid_connections(config: dict, points: pd.DataFrame, qc: list[dict]) -> None:
    try:
        import arcpy
    except ImportError as exc:  # pragma: no cover - environment diagnostic
        raise RuntimeError("ArcGIS Pro Python with arcpy is required for OSM substation extraction") from exc

    feature_class = config["sources"]["osm_power_facilities_gdb"] / "national_substation_poly"
    minimum_voltage = int(config["grid_connection"]["minimum_substation_voltage_v"])
    excluded_types = {value.lower() for value in config["grid_connection"]["excluded_substation_types"]}
    counters = defaultdict(int)
    records = []
    fields = [
        "osm_id", "osm_type", "province", "name", "name_zh", "name_en", "voltage",
        "substation", "operator", "SHAPE@TRUECENTROID",
    ]
    with arcpy.da.SearchCursor(str(feature_class), fields) as cursor:
        for osm_id, osm_type, province, name, name_zh, name_en, voltage, substation_type, operator, xy in cursor:
            counters["source_total"] += 1
            voltage_levels = [int(value) for value in re.findall(r"\d+", str(voltage or ""))]
            if not voltage_levels:
                counters["excluded_missing_voltage"] += 1
                continue
            max_voltage = max(voltage_levels)
            if max_voltage < minimum_voltage:
                counters["excluded_below_voltage"] += 1
                continue
            normalized_type = str(substation_type or "").strip().lower()
            if normalized_type in excluded_types:
                counters["excluded_non_generation_connection_type"] += 1
                continue
            province_name = str(province or "").strip().replace("_", " ")
            province_code = EN_TO_CODE.get(province_name)
            if province_code is None:
                counters["excluded_outside_31_provinces"] += 1
                continue
            lon, lat = xy
            records.append(
                {
                    "substation_id": f"{osm_type or 'osm'}/{osm_id}/p{int(province_code)}",
                    "osm_id": osm_id,
                    "osm_type": osm_type,
                    "province_code": int(province_code),
                    "province_name_en": CODE_TO_EN[int(province_code)],
                    "province_name_zh": CODE_TO_ZH[int(province_code)],
                    "lon": float(lon),
                    "lat": float(lat),
                    "name": name or name_zh or name_en or "",
                    "voltage_levels_v": ";".join(str(value) for value in sorted(set(voltage_levels), reverse=True)),
                    "max_voltage_kv": max_voltage / 1000.0,
                    "substation_type": normalized_type or "unspecified",
                    "operator": operator or "",
                    "geometry_method": "OSM polygon true centroid",
                }
            )
            counters["eligible_31_province_220kv_plus"] += 1
    substations = pd.DataFrame(records).sort_values(["province_code", "substation_id"]).reset_index(drop=True)
    if substations.substation_id.duplicated().any():
        raise ValueError("OSM substation_id is not unique")
    write_csv(substations, DATA_ROOT / "grid" / "substations_osm_220kv_plus.csv")
    filter_summary = pd.DataFrame(
        [{"category": key, "count": int(value)} for key, value in counters.items()]
    )
    write_csv(filter_summary, DATA_ROOT / "grid" / "substation_filter_summary.csv")

    connection_parts = []
    earth_radius_km = 6371.0088
    for province_code, province_points in points.groupby("province_code", sort=True):
        province_substations = substations.loc[substations.province_code.eq(int(province_code))].reset_index(drop=True)
        if province_substations.empty:
            raise ValueError(f"No eligible >=220 kV substation for province {province_code}")
        tree = cKDTree(lonlat_to_unit_sphere(province_substations.lon.to_numpy(), province_substations.lat.to_numpy()))
        chord, positions = tree.query(lonlat_to_unit_sphere(province_points.lon.to_numpy(), province_points.lat.to_numpy()), k=1)
        angle = 2.0 * np.arcsin(np.clip(chord / 2.0, 0.0, 1.0))
        distance_km = earth_radius_km * angle
        chosen = province_substations.iloc[positions].reset_index(drop=True)
        part = province_points[
            ["grid_uid", "grid_id", "province_code", "province_name_en", "province_name_zh", "lon", "lat", "is_land"]
        ].reset_index(drop=True)
        part["substation_id"] = chosen.substation_id.to_numpy()
        part["substation_lon"] = chosen.lon.to_numpy()
        part["substation_lat"] = chosen.lat.to_numpy()
        part["substation_max_voltage_kv"] = chosen.max_voltage_kv.to_numpy()
        part["substation_type"] = chosen.substation_type.to_numpy()
        part["nearest_substation_distance_km"] = distance_km
        land = part.is_land.eq(1)
        part["onwind_spur_distance_km"] = np.where(land, distance_km, np.nan)
        part["upv_spur_distance_km"] = np.where(land, distance_km, np.nan)
        part["dpv_spur_distance_km"] = np.where(land, float(config["grid_connection"]["dpv_spur_distance_km"]), np.nan)
        part["offwind_export_distance_km"] = np.where(~land, distance_km, np.nan)
        part["distance_method"] = config["grid_connection"]["distance_method"]
        part["routing_status"] = "straight_line_proxy_not_engineering_route"
        part["distance_quality_band"] = np.select(
            [distance_km <= 50, distance_km <= 100, distance_km <= 300],
            ["le_50km", "50_100km", "100_300km"],
            default="gt_300km_high_uncertainty",
        )
        connection_parts.append(part)
    connections = pd.concat(connection_parts, ignore_index=True).sort_values("grid_uid")
    write_csv(connections, DATA_ROOT / "grid" / "grid_connection_by_point.csv")
    build_initial_intra_grid_capacity(config, points, connections, substations, qc)
    build_city_load_centers(config, substations, qc)
    add_qc(qc, "osm_substation_source_rows", counters["source_total"], "PASS" if counters["source_total"] == 37592 else "WARN", "OSM national_substation_poly")
    add_qc(qc, "osm_substation_eligible_rows", len(substations), "PASS" if len(substations) == 6294 else "WARN", "31 provinces, >=220 kV, excluding traction/distribution/industrial types")
    add_qc(qc, "osm_substation_province_count", substations.province_code.nunique(), "PASS" if substations.province_code.nunique() == 31 else "FAIL", "Each model province has an eligible substation")
    add_qc(qc, "grid_connection_rows", len(connections), "PASS" if len(connections) == len(points) else "FAIL", "Every optimization point assigned within the same province")
    add_qc(qc, "grid_connection_distance_p95_km", round(float(connections.nearest_substation_distance_km.quantile(0.95)), 3), "PASS", "Great-circle proxy; not routed length")
    add_qc(qc, "grid_connection_distance_max_km", round(float(connections.nearest_substation_distance_km.max()), 3), "WARN", "Do not cap silently; extreme western/offshore points require engineering review or exclusion rules")
    add_qc(qc, "osm_substation_missing_voltage_rows", counters["excluded_missing_voltage"], "WARN", "OSM stations without voltage are excluded and may bias distances upward")


def write_defaults(config: dict, hydro_summary_path: Path) -> None:
    defaults = {
        "regions": 31,
        "base_year": config["base_year"],
        "planning_years": config["planning_years"],
        "capacity_expansion_years": config["capacity_expansion_years"],
        "base_year_capacity_expansion_enabled": False,
        "default_vre_scenario": config["default_vre_scenario"],
        "default_weather_year": config["default_weather_year"],
        "keep_upv_dpv_separate": config["keep_upv_dpv_separate"],
        "default_ccs_injection_field": config["default_ccs_injection_field"],
        "default_carbon_scenario": config["default_carbon_scenario"],
        "nuclear_capacity_floor": "GEM committed/pipeline scenario; 2050 floor held to 2060",
        "biomass_interpolation": config["biomass_interpolation"],
        "hydro_environmental_flow": config["hydro_proxy"]["environmental_flow_method"],
        "hydro_installed_type_rule": config["hydro_proxy"]["installed_type_rule"],
        "hydro_potential_type_rule": config["hydro_proxy"]["potential_type_rule"],
        "hydro_potential_reservoir_threshold_mw": config["hydro_proxy"]["potential_reservoir_threshold_mw"],
        "hydro_reservoir_dispatch_resolution": "station",
        "hydro_cascade_hydraulic_coupling": True,
        "hydro_cascade_scope": config["hydro_proxy"]["cascade_scope"],
        "hydro_cascade_lag_method": config["hydro_proxy"]["cascade_lag_method"],
        "hydro_cascade_duplicate_comid_handling": config["hydro_proxy"]["cascade_duplicate_comid_handling"],
        "hydro_classification_summary": str(hydro_summary_path),
        "grid_connection_distance_method": config["grid_connection"]["distance_method"],
        "initial_intra_grid_capacity_method": config["grid_connection"]["initial_capacity_method"],
        "initial_intra_grid_capacity_weather_year": config["grid_connection"]["initial_capacity_weather_year"],
        "initial_intra_grid_paper_comparator": config["grid_connection"]["paper_comparator_method"],
        "dpv_connection_treatment": config["grid_connection"]["dpv_connection_treatment"],
        "load_center_method": "2022 city electricity coverage with urban-population-weighted county centroids",
        "missing_city_weight_method": "province observed power per urban population applied to uncovered prefectures",
        "trunk_distance_method": "great_circle_to_nearest_same_province_city_load_center",
        "substation_density_role": "validation_and_sensitivity_only_not_primary_load_weight",
        "technology_unresolved_register": str(DATA_ROOT / "technology" / "unresolved_parameters.csv"),
    }
    path = DATA_ROOT / "model_defaults.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        json.dump(defaults, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def build_manifest(config: dict, qc: list[dict]) -> None:
    roles = {
        "province_calibration_xls": "Correct 61 Shandong coastal grid province codes",
        "land_point_province_corrections": "Frozen 43-row land-point province correction table applied before VRE provincial constraints",
        "final_point_v2": "Authoritative 47 GW offshore correction for existing and remaining wind capacity",
        "vre_so2_ccs_points": "VRE potential, existing capacity, CF, SO2 and CCS point fields",
        "hourly_cf_root": "Large hourly VRE Zarr stores; indexed, not copied",
        "future_hourly_load": "31-province future hourly load and components",
        "thermal_existing": "GEM operating thermal capacity by CISPO class",
        "thermal_retirement": "Five-year retirement buckets",
        "nuclear_pipeline": "Committed/pipeline nuclear lower-bound scenario",
        "hydro_stage2": "HydroCHN/GHT station attributes and explicit labels",
        "hydro_cascade_stage2_nodes": "Stage2 recommended core hydropower cascade COMID nodes",
        "hydro_cascade_stage2_edges": "Stage2 MERIT downstream topology among recommended cascade nodes",
        "hydro_cascade_stage2_qa": "Stage2 cascade-topology QA report and warnings",
        "hydro_updated_inventory": "HydroCHN/GHT operating status used for existing-capacity lower bounds",
        "hydro_hourly_discharge": "2019 hourly GRFR discharge for target COMIDs",
        "hydro_environmental_flow": "2019-only monthly P30 environmental-flow proxy generated from hourly GRFR target-COMID discharge",
        "hydro_explicit_ror_profiles": "Existing 204-station provisional ROR profiles",
        "grfr_manifest": "GRFR transfer and integrity status",
        "biomass_province_workbook": "Province bioenergy common-three source years",
        "transmission_existing_directed": "2025 existing AC/DC directed edges",
        "transmission_candidate_corridors": "31-province candidate corridor matrix",
        "carbon_pathways_workbook": "CISPO and comparator annual power-sector emissions pathways",
        "ees_supplement_pdf": "Authoritative CISPO Supplementary Information for technology and DAC parameters",
        "regional_supplement_pdf": "Regional PSTE/REX-Grid Supplementary Information used only as a comparator",
        "tech_economic_parameter_inventory": "Audited extraction inventory for CISPO and comparator parameters",
        "tech_economic_framework": "Chinese parameter framework and uncertainty notes",
        "tech_economic_review": "China-focused techno-economic literature review",
        "osm_power_facilities_gdb": "OSM national power-facility geodatabase containing substation polygons",
        "city_boundary_shapefile": "City administrative boundaries used to constrain city-scale load centers",
        "city_monthly_power_weights": "Validated 2022 city electricity weights from Power_curve_V2 Module 02",
        "county_population_shapefile": "County urban population and prefecture fields used for load-center coordinates",
        "capex_predictions_workbook": "User-extracted CISPO technology CapEx trajectories from figure scales",
        "fuel_price_screenshot": "User-provided Supplementary Table 2 evidence for provincial fuel prices",
    }
    source_rows = []
    for key, path in config["sources"].items():
        if path.is_dir():
            digest = "directory; see indexed child stores"
            size = ""
        else:
            digest = sha256_file(path)
            size = path.stat().st_size
        source_rows.append(
            {
                "source_id": key,
                "role": roles[key],
                "path": str(path),
                "size_bytes": size,
                "last_modified": path.stat().st_mtime,
                "sha256": digest,
            }
        )
    write_csv(pd.DataFrame(source_rows), DATA_ROOT / "source_manifest.csv")

    write_csv(pd.DataFrame(qc), DATA_ROOT / "qc_summary.csv")
    write_output_manifest(DATA_ROOT)


def _write_readme_legacy_mojibake(config: dict) -> None:
    text = f"""# CISPO 模型输入数据包

本目录由 `scripts/build_cispo_data_package.py` 生成。目标是提供可直接读取、单位明确、来源可追溯的 31 省 CISPO 输入；原始大时序不复制，通过索引记录绝对路径、维度和校验值。

## 已固定的模型口径

- 区域：31 省，内蒙古不拆分蒙东/蒙西。
- 模型边界：`{config['base_year']}` 为固定存量与 8760 小时校准年，不允许新增容量投资；扩张决策年为 {', '.join(map(str, config['capacity_expansion_years']))}。
- 默认 VRE 土地情景：`{config['default_vre_scenario']}`；C/B/O 三套上限全部保留。
- 默认气象年：`{config['default_weather_year']}`；`vre/hourly_cf_index.csv` 同时保留 2020–2025 的可选路径。
- UPV 与 DPV：保留分项。两者共享网格光伏 CF，但资源上限、已有容量、投资参数和接入距离不同；DPV 在论文方法中接入距离为 0。
- CCS：点位表同时保留储量、推荐注入能力和最大注入能力；默认使用 `ccs_inj_rec_mtpa`。
- 碳约束：默认 `Base_-550Mt`，2025 基准年不设外生排放上限；2030/2040/2050/2060 为 4000/1300/-100/-550 MtCO2/yr。
- 核电：采用 GEM 已投运/在建/规划管线作为下界，不使用人为强制的 2050 年 300 GW 情景；2060 暂保持 2050 管线下界。
- 生物质：只采用农业残余物、林业残余物和废弃地能源作物。2030/2040 在 2020 与 2050 省级源值之间线性插值，2060 保持 2050 值。
- 水电：现有站采用当前分配标签（GHT 2026 明确标签或 115 MW 代理标签），不按置信度剔除；潜在坝址按论文 `>750 MW` 为水库式、其余为径流式。Stage2 推荐的 5 个核心干流梯级组启用 MERIT 下游拓扑和 2019 GRFR 互相关时滞；其他水库站保持独立平衡。环境流量使用 2019 单年 monthly P30 代理。

## 目录与直接读取文件

| 目录 | 文件 | 用途 |
|---|---|---|
| `sets/` | `provinces.csv` | 31省代码与中英文名称 |
| `sets/` | `model_years.csv` | 区分 2025 固定校准年与后续扩张决策年 |
| `vre/` | `optimization_points.csv` | 风光站点上下界、CF、SO2、CCS；包含山东点位修正和 UPV/DPV 分项 |
| `vre/` | `out_of_scope_points.csv` | 从31省模型排除的 province=71 网格，保留审计不并入福建 |
| `vre/` | `hourly_cf_index.csv` | 大型 Zarr 容量因子路径、维度、时区 |
| `vre/` | `hourly_cf_grid_coverage_{config['default_weather_year']}.csv` | 默认气象年网格覆盖检查 |
| `load/` | `hourly_load_2025_2060.csv.gz` | 31省、5模型年、8760小时负荷，单位GW |
| `load/` | `hourly_load_2030_2060.csv.gz` | 向后兼容的4个扩张决策年负荷视图 |
| `thermal/` | `capacity_floor_by_year.csv` | 退役后火电/气电/生物质机组容量下界 |
| `thermal/` | `nuclear_capacity_floor_by_year.csv` | GEM核电管线下界 |
| `hydro/` | `hydro_stations.csv` | 站点容量、状态、分类、库容、水头、COMID |
| `hydro/` | `timeseries_index.csv` | GRFR、环境流量和显式ROR时序路径 |
| `hydro/` | `cascade_topology_nodes.csv`、`cascade_topology_edges.csv` | 核心干流梯级节点、MERIT 下游边和互相关时滞 |
| `biomass/` | `fuel_potential_by_province_year.csv` | `thermcal_gj_per_year` 省级燃料约束 |
| `transmission/` | `existing_lines.csv` | 2025既有AC/DC线路 |
| `transmission/` | `candidate_corridors.csv` | 31省全部省对候选走廊 |
| `carbon/` | `emissions_limits_by_scenario.csv` | CISPO Base/两类负排放/无排放约束情景 |
| `technology/` | `dac_parameters_by_year.csv` | 四类 DAC 成本、电耗、热耗、COP、CRF 与年度投影 |
| `technology/` | `thermal_nuclear_ruc_parameters.csv` | 火电、核电连续 RUC 参数 |
| `technology/` | `vre_hydro_cost_anchor.csv`、`storage_technical_parameters.csv` | 可直接确认的成本锚点与储能技术参数 |
| `technology/` | `unresolved_parameters.csv` | 禁止静默补值的硬缺口和软假设 |
| `grid/` | `substations_osm_220kv_plus.csv` | 31省 OSM ≥220 kV 可接入变电站质心 |
| `grid/` | `grid_connection_by_point.csv` | 每个优化点到同省最近变电站的接入距离；DPV为0 |

## 关键单位

- 模型表容量与功率：GW；源文件 MW 已在构建时除以 1000。
- 小时电量：`GW × 1 h = GWh`。
- 生物质燃料：GJ/yr；源工作簿 PJ 已乘以 `1e6`。
- CCS 储量：MtCO2；注入能力：MtCO2/yr。
- 水电流量：m3/s；库容：GL；水头：m。
- CF：0–1 fraction。

## 必须保留的警告

1. 现有未标注水电站的容量代理分类不是事实标签，在 GHT 已标注样本上的平衡准确率约 0.677；本轮按用户决策直接使用，后续获得权威类型时再验证。
2. GRFR 时区未在源 NetCDF 中声明，当前保留 source-native 时间；不得静默平移。
3. 环境流量只由 2019 单年计算，不等同于论文的多年气候态 P30。
4. 未来负荷使用北京时间；容量因子 Zarr 的主时间也为 UTC+8，但文件年份跟随 ERA5 UTC 源年，首尾不是严格北京时间自然年。
5. transmission `capacity_group` 用于识别同一工程/共享容量；模型实现不能把多段共享容量无条件重复计入。
6. `grid_connection_by_point.csv` 是大圆直线距离，不是沿道路、地形、海缆走廊或已有线路的工程路由长度；OSM 也不提供可靠的可接入容量和间隔数量。
7. OSM 中无电压标签的变电站不进入 ≥220 kV 集合，可能使部分点位距离偏大。
8. `EES_paper.pdf` 是 CISPO 原始补充材料；同目录 `Supplementary Information.pdf` 是区域 PSTE/REX-Grid 对照材料，不得混作 CISPO 参数来源。
9. `technology/unresolved_parameters.csv` 中标为 `HARD_FAIL_FOR_LONG_TERM_OBJECTIVE` 的未来 CapEx 和燃料价格未解决前，不得宣称完整长期目标函数已可运行。
10. 接入距离超过 300 km 的点标为 `gt_300km_high_uncertainty`；不得为了降低成本静默截断距离，应先核验 OSM 漏标、跨省接入可能性或设置可解释的开发排除规则。

## 追溯与验证

- `source_manifest.csv`：原始输入路径、时间、大小和 SHA-256。
- `output_manifest.csv`：本数据包全部输出及 SHA-256。
- `qc_summary.csv`：行数、31省覆盖、8760小时、网格覆盖、容量总量和分类警告。
- `smoke_test_report.json`：独立读取主要表、Zarr 元数据、NetCDF/JSON 时序索引后的结构与数值检查结果。
- `vre/province_correction_audit.csv`：`TABLES_ALL_POINTS.xls` 对错误省份代码的逐点修正。

## 重建与独立检查

```powershell
& "D:\\Program Files\\ArcGISPro\\bin\\Python\\envs\\arcgispro-py3\\python.exe" scripts\\build_cispo_data_package.py
& "D:\\Program Files\\ArcGISPro\\bin\\Python\\envs\\arcgispro-py3\\python.exe" scripts\\smoke_test_data_package.py
```

如使用独立 Python 环境，依赖清单位于项目根目录 `requirements-data.txt`。
"""
    path = DATA_ROOT / "README.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_readme(config: dict) -> None:
    """Write a compact UTF-8 data dictionary for the generated package."""
    text = f"""# CISPO 模型输入数据包

本目录由 `scripts/build_cispo_data_package.py` 统一生成，提供可直接读取、单位明确、来源可追溯的 31 省 CISPO 输入。大型小时容量因子和水文时序不复制，通过索引记录绝对原始路径、维度和校验信息。

## 固定模型口径

- 区域：31 省，内蒙古不拆分蒙东/蒙西。
- 年份：`{config['base_year']}` 为固定存量与 8760 小时校准年；容量扩张决策年为 {', '.join(map(str, config['capacity_expansion_years']))}。
- 默认 VRE 情景：`{config['default_vre_scenario']}`；默认气象年：`{config['default_weather_year']}`。
- UPV 与 DPV 保留分项；二者共享网格 PV CF，但资源上限、既有容量、CapEx 和接入距离口径不同。
- 燃料价格：采用用户提供的 Supplementary Table 2 截图，单位由 USD/GJ 按 6.9 yuan/USD 转换；因截图未注明价格年与未来轨迹，2025–2060 暂保持不变。
- 内蒙古燃料价格：蒙东与蒙西算术平均。北京、西藏煤价为空，不作插补，并禁用当地煤类技术调度与新增容量。
- 技术 CapEx：采用 `Energy_Technologies_CapEx_Predictions.xlsx` 中 2030/2040/2050/2060 的图表目测提取值，单位 yuan/kW。
- CHP CapEx：映射到同燃料、同 CCS 状态的非 CHP 曲线；水电 13,319 yuan/kW 锚点保持不变。这两项均为显式软假设。
- CCS：点位表保留储量、推荐注入能力和最大注入能力；默认使用 `ccs_inj_rec_mtpa`。
- 省内接入初值：原论文未给出变电站额定容量。默认采用 2025 年 onwind/offwind/UPV 全部铭牌容量同时送出的保守压力情景；同时保留按 {config['grid_connection']['initial_capacity_weather_year']} 小时 CF 聚合的论文一致对照值。DPV 位于负荷侧，不占 spur/trunk 容量。
- 负荷中心：以 2022 城市用电表和县级城镇人口加权中心构建 337 个市级节点；296 城直接使用用电表，缺失的 41 个自治州/地区等按省内单位城镇人口用电强度插补。
- Trunk 距离：每个 OSM 变电站连接同省最近市级负荷中心，使用大圆距离。市级变电站密度和电压权重仅作验证与敏感性分析，不作为负荷主权重。
- 水电：现有站采用当前分配标签，不按置信度剔除；潜在坝址按论文 `>750 MW` 为水库式、其余为径流式；Stage2 推荐核心干流梯级组使用局地 GRFR 入流加上游释放传播，其他水库站独立平衡；环境流量为 2019 单年 monthly P30 代理。

## 主要直接输入

| 模块 | 文件 | 用途 |
|---|---|---|
| 集合 | `sets/provinces.csv`, `sets/model_years.csv` | 31 省与模型年份 |
| 风光/CCS | `vre/optimization_points.csv` | 点位容量上下限、CF、SO2、CCS、UPV/DPV 字段 |
| 容量因子 | `vre/hourly_cf_index.csv` | 2020–2025 大型 Zarr 路径和时间口径 |
| 负荷 | `load/hourly_load_2025_2060.csv.gz` | 31 省 × 5 年 × 8760 h，GW |
| 火电/核电 | `thermal/capacity_floor_by_year.csv`, `thermal/nuclear_capacity_floor_by_year.csv` | 存量退役后容量下界 |
| 水电 | `hydro/hydro_stations.csv`, `hydro/timeseries_index.csv`, `hydro/cascade_topology_edges.csv` | 站点属性、径流索引与核心干流梯级拓扑 |
| 生物质 | `biomass/fuel_potential_by_province_year.csv` | 省级燃料可用量，GJ/yr |
| 输电 | `transmission/existing_lines.csv`, `transmission/candidate_corridors.csv` | 既有线路与候选走廊 |
| 碳约束 | `carbon/emissions_limits_by_scenario.csv` | 各情景年度排放上限 |
| CapEx | `technology/technology_capex_by_year.csv` | 19 类技术 × 4 个扩张年，yuan/kW |
| 燃料价格 | `technology/province_fuel_prices.csv` | 31 省煤炭、天然气价格及可用性 |
| 燃料成本 | `technology/province_fuel_generation_cost_by_year.csv` | 省份-年份-技术直接燃料成本，yuan/MWh |
| DAC/RUC | `technology/dac_parameters_by_year.csv`, `technology/thermal_nuclear_ruc_parameters.csv` | DAC 与火电/核电运行参数 |
| 省内接入 | `grid/grid_connection_by_point.csv` | 点位到同省最近 OSM ≥220 kV 变电站的大圆距离；DPV 为 0 |
| Spur 初始容量 | `grid/initial_spur_capacity_2025.csv` | 2025 正装机点逐技术保守初值、论文公式对照值及 CF 回退审计 |
| Trunk/变电站初值 | `grid/substation_initial_capacity_2025.csv` | 每个 OSM 变电站的 VRE 接口容量代理；不是实测铭牌容量 |
| 省级接入汇总 | `grid/province_initial_intra_grid_capacity_2025.csv` | 31 省初始接入容量闭合和同峰值对照 |
| 市级负荷中心 | `grid/city_load_centers.csv` | 城市用电覆盖、城镇人口加权坐标、变电站密度和电压诊断 |
| 缺失城市插补 | `grid/city_load_center_imputed_weights.csv` | 41 个未被城市用电表覆盖的地级单元及其人口插补权重 |
| Trunk 映射 | `grid/substation_to_load_center.csv` | 6,294 个变电站到同省最近负荷中心的大圆距离 |
| 代理验证 | `grid/load_center_proxy_validation.csv` | 变电站数量/电压份额与城市用电份额的相关性和误差 |

## 必须保留的限制

1. CapEx 为图表尺度目测值，精确数字化误差和真实/名义价格基准未给出。
2. 燃料价格截图未给出价格基准年和时间轨迹；当前常数外推必须进入敏感性分析。
3. 北京和西藏煤价缺失，禁用煤类技术是约束处理，不代表现实中永久不存在煤电。
4. OSM 和 EES 均不提供可靠的变电站额定容量、可接入容量或间隔数量；当前值只是由 2025 已有 VRE 装机推导的最低接口容量代理。
5. 默认“全部铭牌同时满发”是用户指定的保守压力情景，明显高于论文采用的小时聚合同峰值；两套结果不得混称为实测容量。
6. Trunk 距离已可计算，但仍是变电站到市级人口加权中心的大圆距离，不是既有线路或工程路由。
7. 城市用电表未覆盖 41 个自治州、地区等地级单元；当前按省内单位城镇人口用电强度插补，正式结果应进行插补敏感性分析。
8. 变电站数量和电压权重与城市用电份额仅中等相关，不能替代城市用电/人口主权重。
9. 沿海掩膜错配点采用显式 CF 回退：风电取同格 `mixed_wind`，UPV 取同省最近陆地 PV 格点；必须保留逐点审计字段。
10. 现有未标注水电站的 115 MW 代理分类不是事实标签；本轮直接使用，待获得权威类型后验证，不开展分类阈值敏感性。

## 追溯与验证

- `source_manifest.csv`：原始输入路径、大小、修改时间和 SHA-256。
- `output_manifest.csv`：全部生成输出及 SHA-256。
- `qc_summary.csv`：构建阶段 QC。
- `smoke_test_report.json`：独立结构与数值检查。
- `technology/unresolved_parameters.csv`：所有软假设、缺口和禁止静默填补项。

```powershell
& "D:\\Program Files\\ArcGISPro\\bin\\Python\\envs\\arcgispro-py3\\python.exe" scripts\\build_cispo_data_package.py
& "D:\\Program Files\\ArcGISPro\\bin\\Python\\envs\\arcgispro-py3\\python.exe" scripts\\smoke_test_data_package.py
```
"""
    path = DATA_ROOT / "README.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    config = load_config()
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    qc: list[dict] = []
    build_sets(config)
    points = build_spatial_points(config, qc)
    build_cf_index(config, points, qc)
    build_load(config, qc)
    build_thermal_nuclear(config, qc)
    build_hydro(config, points, qc)
    build_biomass(config, qc)
    build_transmission(config, qc)
    build_carbon(config, qc)
    build_technology_parameters(config, qc)
    build_fuel_prices(config, qc)
    build_grid_connections(config, points, qc)
    write_defaults(config, DATA_ROOT / "hydro" / "classification_summary.csv")
    write_readme(config)
    build_manifest(config, qc)
    failures = [row for row in qc if row["status"] == "FAIL"]
    print(json.dumps({"data_root": str(DATA_ROOT), "qc_checks": len(qc), "failures": failures}, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
