"""Build traceable nuclear, biomass/BECCS, and battery capacity bounds.

The script only writes the three V0719 boundary tables consumed by the model.
It does not rebuild or overwrite unrelated model-ready inputs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "capacity_bounds_v0719.json"
DEFAULT_DATA_ROOT = ROOT / "data"
PLANNING_YEARS = (2030, 2040, 2050, 2060)


def _read_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _province_table(data_root: Path) -> pd.DataFrame:
    provinces = pd.read_csv(data_root / "sets" / "provinces.csv")
    columns = ["province_code", "province_name_en", "province_name_zh"]
    missing = sorted(set(columns).difference(provinces.columns))
    if missing:
        raise ValueError(f"Province table missing columns: {', '.join(missing)}")
    if len(provinces) != 31 or provinces.province_code.duplicated().any():
        raise ValueError("V0719 capacity bounds require 31 unique model provinces")
    return provinces[columns].sort_values("province_code").reset_index(drop=True)


def build_nuclear_upper(config: dict, data_root: Path, provinces: pd.DataFrame) -> pd.DataFrame:
    floor = pd.read_csv(data_root / "thermal" / "nuclear_capacity_floor_by_year.csv")
    floor = floor.loc[floor.year.isin(PLANNING_YEARS)].copy()
    expected_rows = len(provinces) * len(PLANNING_YEARS)
    if len(floor) != expected_rows or floor.duplicated(["province_code", "year"]).any():
        raise ValueError("Nuclear floor must contain 31 provinces x four planning years")

    weight_source = floor.loc[floor.year.eq(2050)].set_index("province_code").capacity_floor_gw
    weights = weight_source.reindex(provinces.province_code).fillna(0.0).to_numpy(float)
    if weights.sum() <= 0:
        raise ValueError("2050 GEM nuclear pipeline weights sum to zero")
    weights /= weights.sum()

    targets = {
        int(year): float(value)
        for year, value in config["nuclear"]["national_capacity_upper_gw"].items()
    }
    methods = config["nuclear"]["source_method"]
    rows: list[pd.DataFrame] = []
    for year in PLANNING_YEARS:
        year_floor = (
            floor.loc[floor.year.eq(year)]
            .set_index("province_code")
            .capacity_floor_gw.reindex(provinces.province_code)
            .fillna(0.0).to_numpy(float)
        )
        gap = targets[year] - float(year_floor.sum())
        if gap < -1e-9:
            raise ValueError(
                f"{year} nuclear national upper {targets[year]} GW is below "
                f"the {year_floor.sum()} GW exogenous floor"
            )
        upper = year_floor + weights * max(gap, 0.0)
        part = provinces.copy()
        part["year"] = year
        part["capacity_upper_gw"] = upper
        part["national_capacity_upper_gw"] = targets[year]
        part["allocation_weight"] = weights
        part["source_method"] = methods[str(year)]
        part["source_url"] = config["nuclear"]["official_2030_source_url"] if year == 2030 else ""
        rows.append(part)
    out = pd.concat(rows, ignore_index=True)
    totals = out.groupby("year").capacity_upper_gw.sum()
    for year, target in targets.items():
        if not np.isclose(float(totals.loc[year]), target, atol=1e-9):
            raise ValueError(f"{year} nuclear upper does not close to {target} GW")
    return out


def build_biomass_upper(config: dict, data_root: Path, provinces: pd.DataFrame) -> pd.DataFrame:
    fuel = pd.read_csv(data_root / "biomass" / "fuel_potential_by_province_year.csv")
    fuel = fuel.loc[fuel.year.isin(PLANNING_YEARS)].copy()
    expected_rows = len(provinces) * len(PLANNING_YEARS)
    if len(fuel) != expected_rows or fuel.duplicated(["province_code", "year"]).any():
        raise ValueError("Biomass fuel table must contain 31 provinces x four planning years")
    eta = float(config["biomass"]["thermal_efficiency"])
    full_load_hours = float(config["biomass"]["equivalent_full_load_hours"])
    if not 0 < eta <= 1 or full_load_hours <= 0:
        raise ValueError("Biomass efficiency and equivalent full-load hours must be positive")
    out = fuel.merge(provinces, on=["province_code", "province_name_en", "province_name_zh"], how="inner")
    out["formula_capacity_upper_gw"] = (
        out.thermcal_gj_per_year.astype(float) * eta / 3600.0 / full_load_hours
    )
    thermal_floor = pd.read_csv(data_root / "thermal" / "capacity_floor_by_year.csv")
    pair_floor = (
        thermal_floor.loc[
            thermal_floor.year.isin(PLANNING_YEARS)
            & thermal_floor.technology.isin(["bio", "bioccs"])
        ]
        .groupby(["province_code", "year"], as_index=False)
        .capacity_floor_gw.sum()
        .rename(columns={"capacity_floor_gw": "minimum_existing_pair_capacity_gw"})
    )
    out = out.merge(pair_floor, on=["province_code", "year"], how="left")
    out["minimum_existing_pair_capacity_gw"] = out.minimum_existing_pair_capacity_gw.fillna(0.0)
    out["capacity_upper_adjusted_to_floor"] = (
        out.minimum_existing_pair_capacity_gw > out.formula_capacity_upper_gw + 1e-9
    )
    # Never make the inherited observed fleet infeasible because the resource
    # potential and installed-capacity sources disagree. The annual fuel
    # constraint remains active and continues to cap actual consumption.
    out["capacity_upper_gw"] = np.maximum(
        out.formula_capacity_upper_gw,
        out.minimum_existing_pair_capacity_gw,
    )
    out["thermal_efficiency"] = eta
    out["equivalent_full_load_hours"] = full_load_hours
    out["source_method"] = config["biomass"]["source_method"]
    out["formula"] = config["biomass"]["formula"]
    return out[
        [
            "province_code", "province_name_en", "province_name_zh", "year",
            "thermcal_gj_per_year", "thermal_efficiency",
            "equivalent_full_load_hours", "formula_capacity_upper_gw",
            "minimum_existing_pair_capacity_gw",
            "capacity_upper_adjusted_to_floor", "capacity_upper_gw",
            "source_method", "formula",
        ]
    ].sort_values(["year", "province_code"])


def build_battery_floor(config: dict, provinces: pd.DataFrame) -> pd.DataFrame:
    floor_2030 = {
        int(code): float(value)
        for code, value in config["battery"]["capacity_floor_gw_2030_by_province_code"].items()
    }
    if set(floor_2030) != set(provinces.province_code.astype(int)):
        raise ValueError("Battery floor configuration must cover all 31 model provinces")
    rows: list[pd.DataFrame] = []
    for year in PLANNING_YEARS:
        part = provinces.copy()
        part["year"] = year
        part["technology"] = "battery"
        part["capacity_floor_gw"] = [floor_2030[int(code)] if year == 2030 else 0.0 for code in part.province_code]
        part["duration_h"] = float(config["battery"]["duration_h"])
        part["floor_method"] = (
            config["battery"]["2030_floor_basis"]
            if year == 2030
            else config["battery"]["floor_retirement_rule"]
        )
        part["source_path"] = config["battery"]["cispo_source_path"]
        rows.append(part)
    out = pd.concat(rows, ignore_index=True)
    if not np.isclose(
        float(out.loc[out.year.eq(2030), "capacity_floor_gw"].sum()), 65.85, atol=1e-9
    ):
        raise ValueError("Merged CISPO Table S17 battery floor must total 65.85 GW")
    return out.sort_values(["year", "province_code"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    args = parser.parse_args()

    config = _read_config(args.config.resolve())
    data_root = args.data_root.resolve()
    provinces = _province_table(data_root)
    outputs = {
        data_root / "thermal" / "nuclear_capacity_upper_by_year.csv": build_nuclear_upper(config, data_root, provinces),
        data_root / "biomass" / "capacity_upper_by_province_year.csv": build_biomass_upper(config, data_root, provinces),
        data_root / "storage" / "battery_capacity_floor_by_province_year.csv": build_battery_floor(config, provinces),
    }
    for path, table in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        table.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"wrote {path} rows={len(table)}")


if __name__ == "__main__":
    main()
