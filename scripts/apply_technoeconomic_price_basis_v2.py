"""Apply the approved V2 monetary basis to the existing local data package.

This migration updates only monetary columns. Physical parameters, efficiencies,
heat rates, lifetimes, WACC and capacity constraints are unchanged. The script
is idempotent: an already-normalized package is validated rather than multiplied
again.

Run from the repository root:

    python scripts/apply_technoeconomic_price_basis_v2.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_package_common import sha256_file, write_csv, write_output_manifest
from cispo_model.price_basis import (
    domestic_2022_cny_to_2025,
    load_price_basis_config,
    nuclear_capex_2025_cny,
)


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TECH = DATA / "technology"
MANIFEST = TECH / "technoeconomic_price_basis_manifest.json"
CONTRACT = "technoeconomic_2025_cny_v2"
TARGET_BASIS = "2025 constant CNY"


def _read(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def _stamp(frame: pd.DataFrame) -> pd.DataFrame:
    frame["monetary_price_basis"] = TARGET_BASIS
    frame["price_basis_contract"] = CONTRACT
    return frame


def _write(frame: pd.DataFrame, path: Path, records: list[dict[str, object]]) -> None:
    write_csv(frame, path)
    records.append(
        {
            "relative_path": path.relative_to(DATA).as_posix(),
            "rows": int(len(frame)),
            "sha256": sha256_file(path),
        }
    )


def _already_applied(paths: list[Path]) -> bool:
    for path in paths:
        frame = _read(path)
        if "price_basis_contract" not in frame.columns:
            return False
        if not frame["price_basis_contract"].eq(CONTRACT).all():
            return False
    return True


def _validate() -> dict[str, object]:
    config = load_price_basis_config()
    capex = _read(TECH / "technology_capex_by_year.csv").set_index(
        ["technology", "year"]
    )
    ccs = _read(TECH / "ccs_cost_parameters.csv").iloc[0]
    fuel = _read(TECH / "province_fuel_prices.csv")
    inner = fuel.loc[fuel.province_code.eq(15)].iloc[0]
    checks = {
        "contract_config": config["contract_version"] == CONTRACT,
        "onwind_2030": bool(np.isclose(
            capex.loc[("onwind", 2030), "capex_yuan_per_kw"],
            domestic_2022_cny_to_2025(5500.0),
        )),
        "nuclear_2040": bool(np.isclose(
            capex.loc[("nuclear", 2040), "capex_yuan_per_kw"],
            nuclear_capex_2025_cny(2040),
        )),
        "battery_2060": bool(np.isclose(
            capex.loc[("battery", 2060), "capex_yuan_per_kw"],
            domestic_2022_cny_to_2025(2400.0),
        )),
        "ccs_capture": bool(np.isclose(
            ccs.capture_yuan_per_tco2, domestic_2022_cny_to_2025(260.0)
        )),
        "ccs_transport": bool(np.isclose(ccs.transport_yuan_per_tco2_km, 0.5)),
        "ccs_storage": bool(np.isclose(ccs.storage_yuan_per_tco2, 45.0)),
        "fuel_fx": bool(np.isclose(inner.usd_to_yuan, 7.1429)),
        "fuel_inner_mongolia": bool(np.isclose(
            inner.coal_yuan_per_gj, 2.56 * 7.1429
        )),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise ValueError(f"2025-CNY migration validation failed: {failed}")
    return {"checks": checks, "status": "PASS"}


def apply() -> None:
    price_config = load_price_basis_config()
    factor = float(price_config["domestic_cny_to_2025_factor"])
    usd_to_cny = float(price_config["foreign_exchange_2025"]["usd_to_cny"])
    paths_with_stamp = [
        TECH / "vre_hydro_cost_anchor.csv",
        TECH / "thermal_nuclear_ruc_parameters.csv",
        TECH / "thermal_nuclear_om_parameters.csv",
        TECH / "technology_capex_by_year.csv",
        TECH / "storage_technical_parameters.csv",
        TECH / "transmission_cost_parameters.csv",
        TECH / "ccs_cost_parameters.csv",
        TECH / "dac_parameters_by_year.csv",
        TECH / "province_fuel_prices.csv",
        TECH / "province_fuel_generation_cost_by_year.csv",
        DATA / "transmission" / "candidate_corridors.csv",
        DATA / "load_center_network" / "city_337" / "intra_edges.csv",
        DATA / "load_center_network" / "natural_earth_278" / "intra_edges.csv",
    ]
    if _already_applied(paths_with_stamp):
        validation = _validate()
        records = [
            {
                "relative_path": path.relative_to(DATA).as_posix(),
                "rows": int(len(_read(path))),
                "sha256": sha256_file(path),
            }
            for path in paths_with_stamp
        ]
        status = (
            "ALREADY_APPLIED"
            if MANIFEST.exists()
            else "RECOVERED_AFTER_COMPLETED_TABLE_WRITES"
        )
        manifest = {
            "contract_version": CONTRACT,
            "status": "APPLIED_PRODUCTION_LOCAL_DATA_PACKAGE",
            "applied_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "target_price_basis": TARGET_BASIS,
            "domestic_cny_factor": factor,
            "usd_to_cny": usd_to_cny,
            "eur_to_cny": float(
                price_config["foreign_exchange_2025"]["eur_to_cny"]
            ),
            "planning_year_rule": price_config["planning_year_rule"],
            "updated_files": records,
            "validation": validation,
        }
        MANIFEST.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        write_output_manifest(DATA)
        print(
            json.dumps(
                {"migration_status": status, **validation},
                ensure_ascii=False,
            )
        )
        return

    records: list[dict[str, object]] = []

    vre = _read(TECH / "vre_hydro_cost_anchor.csv")
    vre["capex_yuan_per_kw"] *= factor
    _write(_stamp(vre), TECH / "vre_hydro_cost_anchor.csv", records)

    ruc = _read(TECH / "thermal_nuclear_ruc_parameters.csv")
    for column in ("startup_yuan_per_mw", "shutdown_yuan_per_mw"):
        ruc[column] *= factor
    _write(_stamp(ruc), TECH / "thermal_nuclear_ruc_parameters.csv", records)

    om = _read(TECH / "thermal_nuclear_om_parameters.csv")
    om["variable_om_yuan_per_mwh"] *= factor
    _write(_stamp(om), TECH / "thermal_nuclear_om_parameters.csv", records)

    capex = _read(TECH / "technology_capex_by_year.csv")
    non_nuclear = ~capex.technology.eq("nuclear")
    capex.loc[non_nuclear, "capex_yuan_per_kw"] *= factor
    capex.loc[~non_nuclear, "capex_yuan_per_kw"] = capex.loc[
        ~non_nuclear, "year"
    ].map(nuclear_capex_2025_cny)
    capex.loc[non_nuclear, "extraction_method"] = (
        capex.loc[non_nuclear, "extraction_method"].astype(str)
        + "; rebased from 2022 to 2025 constant CNY"
    )
    capex.loc[~non_nuclear, "extraction_method"] = (
        "approved USD trajectory converted at 2025 USD/CNY"
    )
    _write(_stamp(capex), TECH / "technology_capex_by_year.csv", records)

    nuclear = _read(TECH / "nuclear_capex_by_year.csv")
    expansion = nuclear.year.ne(2025)
    nuclear.loc[expansion, "capex_yuan_per_kw"] = nuclear.loc[
        expansion, "year"
    ].map(nuclear_capex_2025_cny)
    nuclear.loc[expansion, "source_method"] = (
        "approved USD trajectory converted at 2025 USD/CNY"
    )
    _write(_stamp(nuclear), TECH / "nuclear_capex_by_year.csv", records)

    storage = _read(TECH / "storage_technical_parameters.csv")
    storage["variable_om_yuan_per_mwh"] *= factor
    _write(_stamp(storage), TECH / "storage_technical_parameters.csv", records)

    transmission = _read(TECH / "transmission_cost_parameters.csv")
    for column in ("substation_yuan_per_kw", "overhead_line_thousand_yuan_per_km"):
        transmission[column] *= factor
    _write(
        _stamp(transmission),
        TECH / "transmission_cost_parameters.csv",
        records,
    )

    ccs = _read(TECH / "ccs_cost_parameters.csv")
    ccs["capture_yuan_per_tco2"] = domestic_2022_cny_to_2025(260.0)
    ccs["transport_yuan_per_tco2_km"] = float(
        price_config["ccs"]["transport_yuan_per_tco2_km_2025"]
    )
    ccs["storage_yuan_per_tco2"] = float(
        price_config["ccs"]["storage_yuan_per_tco2_2025"]
    )
    _write(_stamp(ccs), TECH / "ccs_cost_parameters.csv", records)

    dac = _read(TECH / "dac_parameters_by_year.csv")
    for column in (
        "capex_million_yuan_per_mtco2_per_year_capacity",
        "annualized_capex_million_yuan_per_mtco2_per_year_capacity_year",
        "fixed_om_million_yuan_per_mtco2_per_year_capacity_year",
        "variable_om_yuan_per_tco2",
    ):
        dac[column] *= factor
    dac["source_method"] = (
        dac["source_method"].astype(str)
        + "; monetary values rebased from 2022 to 2025 constant CNY"
    )
    _write(_stamp(dac), TECH / "dac_parameters_by_year.csv", records)

    fuel = _read(TECH / "province_fuel_prices.csv")
    for source_column, target_column in (
        ("coal_usd_per_gj", "coal_yuan_per_gj"),
        ("gas_usd_per_gj", "gas_yuan_per_gj"),
        ("biomass_usd_per_gj", "biomass_yuan_per_gj"),
    ):
        fuel[target_column] = fuel[source_column] * usd_to_cny
    fuel["usd_to_yuan"] = usd_to_cny
    fuel["price_basis_year"] = "2025 constant CNY after source-currency conversion"
    fuel["temporal_method"] = (
        "convert published USD/GJ values to 2025 CNY/GJ and hold constant "
        "in real terms through 2060"
    )
    _write(_stamp(fuel), TECH / "province_fuel_prices.csv", records)

    fuel_lookup = fuel.set_index("province_code")
    generation = _read(TECH / "province_fuel_generation_cost_by_year.csv")
    generation["fuel_price_yuan_per_gj"] = [
        fuel_lookup.loc[int(province_code), f"{fuel_name}_yuan_per_gj"]
        for province_code, fuel_name in zip(
            generation.province_code, generation.fuel
        )
    ]
    generation["fuel_cost_yuan_per_mwh"] = (
        generation["fuel_price_yuan_per_gj"]
        * generation["fuel_load_gj_per_mwh"]
    )
    generation["price_temporal_method"] = (
        "published USD/GJ value converted to 2025 CNY and held constant "
        "in real terms through 2060"
    )
    _write(
        _stamp(generation),
        TECH / "province_fuel_generation_cost_by_year.csv",
        records,
    )

    corridors = _read(DATA / "transmission" / "candidate_corridors.csv")
    corridors["preset_unit_cost_yuan_per_kw"] *= factor
    _write(
        _stamp(corridors),
        DATA / "transmission" / "candidate_corridors.csv",
        records,
    )

    for scenario in ("city_337", "natural_earth_278"):
        path = DATA / "load_center_network" / scenario / "intra_edges.csv"
        edges = _read(path)
        edges["unit_cost_yuan_per_kw"] *= factor
        _write(_stamp(edges), path, records)

    validation = _validate()
    manifest = {
        "contract_version": CONTRACT,
        "status": "APPLIED_PRODUCTION_LOCAL_DATA_PACKAGE",
        "applied_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "target_price_basis": TARGET_BASIS,
        "domestic_cny_factor": factor,
        "usd_to_cny": usd_to_cny,
        "eur_to_cny": float(price_config["foreign_exchange_2025"]["eur_to_cny"]),
        "planning_year_rule": price_config["planning_year_rule"],
        "updated_files": records,
        "validation": validation,
    }
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_output_manifest(DATA)
    print(
        json.dumps(
            {
                "status": "APPLIED",
                "updated_files": len(records),
                "validation": validation["status"],
                "manifest": str(MANIFEST),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    apply()
