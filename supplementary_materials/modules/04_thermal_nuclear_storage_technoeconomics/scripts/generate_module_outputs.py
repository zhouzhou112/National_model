"""Build the finalized Module 04 evidence package.

This script audits the technology-economic inputs actually loaded by the
current CISPO implementation. It does not mutate model inputs. All derived
tables, figure data, figures and QA records are written inside this module.

The reporting normalization converts source-grounded 2022 CNY monetary
values to 2025 constant CNY using the cumulative China CPI factor
1.002 * 1.002 * 1.000 = 1.004004. Provincial fuel-price provenance is traced
to An et al. (2025) Supplementary Note 3 and Table 2; the production values
remain unchanged here, while the separate final-candidate generator converts
the published USD/GJ values with the official 2025 average exchange rate.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image


MODULE = Path(__file__).resolve().parents[1]
NATIONAL_MODEL = MODULE.parents[2]
PROJECT_ROOT = NATIONAL_MODEL.parent
TECH_ECONOMIC = PROJECT_ROOT / "tech_economic"
THERMAL_UPSTREAM = PROJECT_ROOT / "Gis_process" / "thermal_power"

FIGURES = MODULE / "figures"
FIGURE_DATA = MODULE / "figure_data"
TABLES = MODULE / "tables"
QA = MODULE / "qa"

FIGURE_WIDTH_IN = 7.0
FIGURE_HEIGHT_IN = 5.55
PNG_DPI = 450

CPI_BY_YEAR = {2023: 1.002, 2024: 1.002, 2025: 1.000}
CPI_2022_TO_2025 = float(np.prod(list(CPI_BY_YEAR.values())))
USD_CNY_ACTIVE = 6.9
USD_CNY_2025 = 7.1429
EUR_CNY_ACTIVE = 7.8
EUR_CNY_2025 = 8.1185

YEARS = [2025, 2030, 2040, 2050, 2060]
EXPANSION_YEARS = [2030, 2040, 2050, 2060]

COLORS = {
    "coal": "#5B5B5B",
    "coal_ccs": "#9A7B4F",
    "gas": "#7E6AA2",
    "gas_ccs": "#B69ACD",
    "bio": "#4E8B65",
    "nuclear": "#D18B37",
    "battery": "#D65F5F",
    "phs": "#2E73B7",
    "policy": "#111111",
    "uncertainty": "#C95A49",
}

TECH_LABELS = {
    "onwind": "Onshore wind",
    "offwind": "Offshore wind",
    "upv": "Utility PV",
    "dpv": "Distributed PV",
    "battery": "Battery",
    "phs": "Pumped hydro",
    "coalccs": "Coal CCS",
    "nuclear": "Nuclear",
    "hydro": "Hydropower",
}


def ensure_dirs() -> None:
    for path in (FIGURES, FIGURE_DATA, TABLES, QA):
        path.mkdir(parents=True, exist_ok=True)


def write_csv(frame: pd.DataFrame, path: Path, **kwargs) -> None:
    frame.to_csv(path, index=False, encoding="utf-8-sig", **kwargs)


def read_csv(relative: str) -> pd.DataFrame:
    return pd.read_csv(NATIONAL_MODEL / relative)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def capital_recovery_factor(real_wacc: float, lifetime_years: float) -> float:
    factor = (1.0 + real_wacc) ** lifetime_years
    return real_wacc * factor / (factor - 1.0)


def configure_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 7.0,
            "axes.labelsize": 7.0,
            "axes.titlesize": 7.5,
            "xtick.labelsize": 6.2,
            "ytick.labelsize": 6.2,
            "legend.fontsize": 5.8,
            "axes.linewidth": 0.55,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def load_inputs() -> dict[str, object]:
    config_path = NATIONAL_MODEL / "config" / "optimization_2030.json"
    with config_path.open("r", encoding="utf-8") as stream:
        config = json.load(stream)

    paths = {
        "config": config_path,
        "capex": NATIONAL_MODEL / "data" / "technology" / "technology_capex_by_year.csv",
        "ruc": NATIONAL_MODEL / "data" / "technology" / "thermal_nuclear_ruc_parameters.csv",
        "om": NATIONAL_MODEL / "data" / "technology" / "thermal_nuclear_om_parameters.csv",
        "storage": NATIONAL_MODEL / "data" / "technology" / "storage_technical_parameters.csv",
        "fuel": NATIONAL_MODEL / "data" / "technology" / "province_fuel_prices.csv",
        "fuel_cost": NATIONAL_MODEL / "data" / "technology" / "province_fuel_generation_cost_by_year.csv",
        "emissions": NATIONAL_MODEL / "data" / "technology" / "emission_factors_by_year.csv",
        "dac": NATIONAL_MODEL / "data" / "technology" / "dac_parameters_by_year.csv",
        "ccs": NATIONAL_MODEL / "data" / "technology" / "ccs_cost_parameters.csv",
        "transmission": NATIONAL_MODEL / "data" / "technology" / "transmission_cost_parameters.csv",
        "unresolved": NATIONAL_MODEL / "data" / "technology" / "unresolved_parameters.csv",
        "thermal_floor": NATIONAL_MODEL / "data" / "thermal" / "capacity_floor_by_year.csv",
        "retirement": NATIONAL_MODEL / "data" / "thermal" / "retirement_schedule.csv",
        "nuclear_floor": NATIONAL_MODEL / "data" / "thermal" / "nuclear_capacity_floor_by_year.csv",
        "nuclear_upper": NATIONAL_MODEL / "data" / "thermal" / "nuclear_capacity_upper_by_year.csv",
        "battery_floor": NATIONAL_MODEL / "data" / "storage" / "battery_capacity_floor_by_province_year.csv",
        "phs_bounds": NATIONAL_MODEL / "data" / "storage" / "phs_capacity_bounds_by_province_year.csv",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing active Module 04 inputs: {missing}")

    loaded: dict[str, object] = {"config": config, "paths": paths}
    for key, path in paths.items():
        if key != "config":
            loaded[key] = pd.read_csv(path)
    return loaded


def build_active_input_register(inputs: dict[str, object]) -> pd.DataFrame:
    paths: dict[str, Path] = inputs["paths"]  # type: ignore[assignment]
    rows = [
        ("Production configuration", "config", "planning years, WACC, lifetimes, wave and network cost assumptions", "cispo_model/config.py; cispo_model/master.py", "ACTIVE_PRIMARY"),
        ("Technology CapEx trajectories", "capex", "19 technologies x 2030/2040/2050/2060", "cispo_model/data.py:700-704; cispo_model/master.py", "ACTIVE_PRIMARY"),
        ("Thermal/nuclear RUC", "ruc", "operating range, ramp, minimum up/down, startup/shutdown and fuel load", "cispo_model/data.py; cispo_model/monolithic.py", "ACTIVE_PRIMARY"),
        ("Thermal/nuclear O&M", "om", "fixed and variable O&M", "cispo_model/data.py; cispo_model/master.py; cispo_model/monolithic.py", "ACTIVE_PRIMARY"),
        ("Storage technical parameters", "storage", "efficiency, duration, self-discharge, lifetime and O&M", "cispo_model/data.py; cispo_model/master.py; cispo_model/monolithic.py", "ACTIVE_PRIMARY"),
        ("Provincial fuel prices", "fuel", "31-province coal, gas and biomass prices and availability", "scripts/rebuild_fuel_price_tables.py; cispo_model/data.py", "ACTIVE_PRIMARY_WITH_RESOLVED_EXTERNAL_PROVENANCE"),
        ("Provincial fuel generation cost", "fuel_cost", "fuel price x heat rate for ten thermal classes", "cispo_model/data.py; cispo_model/monolithic.py", "ACTIVE_DERIVED"),
        ("Emission factors", "emissions", "year-specific coal, gas and BECCS factors", "cispo_model/data.py; cispo_model/carbon_accounting.py", "ACTIVE_NON_MONETARY"),
        ("DAC parameters", "dac", "four DAC pathways, cost, energy and annualization", "cispo_model/data.py; cispo_model/master.py", "ACTIVE_PRIMARY"),
        ("CCS costs", "ccs", "capture, transport and storage", "cispo_model/data.py; cispo_model/master.py", "ACTIVE_PRIMARY"),
        ("Transmission costs", "transmission", "voltage-specific substations, lines, loss and lifetime", "cispo_model/data.py; cispo_model/master.py", "ACTIVE_PRIMARY"),
        ("Thermal capacity floor", "thermal_floor", "province-technology capacity after exogenous retirement", "cispo_model/data.py; cispo_model/master.py", "ACTIVE_PRIMARY"),
        ("Thermal retirement schedule", "retirement", "40-year existing-fleet retirement buckets", "scripts/build_cispo_data_package.py; cispo_model/planning_state.py", "ACTIVE_PRIMARY"),
        ("Nuclear lower bound", "nuclear_floor", "GEM operating/pipeline milestones", "cispo_model/data.py; cispo_model/master.py", "ACTIVE_PRIMARY"),
        ("Nuclear upper bound", "nuclear_upper", "policy-aligned national ceilings allocated by province", "cispo_model/data.py; cispo_model/master.py", "ACTIVE_PRIMARY"),
        ("Battery lower bound", "battery_floor", "CISPO Table S17 2025 provincial targets imposed at 2030", "cispo_model/data.py; cispo_model/master.py", "ACTIVE_PRIMARY"),
        ("PHS lower/upper bounds", "phs_bounds", "GHT 2026 operating floor and project-availability upper bound", "cispo_model/data.py; cispo_model/master.py", "ACTIVE_PRIMARY"),
        ("Unresolved-parameter register", "unresolved", "sidecar assumptions and data gaps; contains superseded network statements", "documentation only; not consumed by optimization equations", "ACTIVE_SIDECAR_PARTLY_STALE"),
    ]
    out = []
    for name, key, role, consumer, status in rows:
        path = paths[key]
        out.append(
            {
                "input_family": name,
                "relative_path": path.relative_to(NATIONAL_MODEL).as_posix(),
                "model_role": role,
                "effective_consumer": consumer,
                "authority_status": status,
                "row_count": "" if path.suffix == ".json" else len(pd.read_csv(path)),
                "sha256": sha256(path),
            }
        )
    frame = pd.DataFrame(out)
    write_csv(frame, TABLES / "table_m04_1_active_input_register.csv")
    return frame


def build_capacity_boundaries(inputs: dict[str, object]) -> pd.DataFrame:
    thermal: pd.DataFrame = inputs["thermal_floor"]  # type: ignore[assignment]
    nuclear_floor: pd.DataFrame = inputs["nuclear_floor"]  # type: ignore[assignment]
    nuclear_upper: pd.DataFrame = inputs["nuclear_upper"]  # type: ignore[assignment]
    battery: pd.DataFrame = inputs["battery_floor"]  # type: ignore[assignment]
    phs: pd.DataFrame = inputs["phs_bounds"]  # type: ignore[assignment]

    grouped = {
        "coal_without_ccs": ["coal", "cchp"],
        "coal_with_ccs": ["coalccs", "cchpccs"],
        "gas_without_ccs": ["gas", "gchp"],
        "gas_with_ccs": ["gasccs", "gchpccs"],
        "bio_and_beccs": ["bio", "bioccs"],
    }
    rows = []
    for year in YEARS:
        t = thermal.loc[thermal.year.eq(year)]
        row: dict[str, object] = {"year": year}
        for label, technologies in grouped.items():
            row[f"{label}_floor_gw"] = float(
                t.loc[t.technology.isin(technologies), "capacity_floor_gw"].sum()
            )
        row["thermal_excluding_nuclear_floor_gw"] = float(t.capacity_floor_gw.sum())
        row["nuclear_floor_gw"] = float(
            nuclear_floor.loc[nuclear_floor.year.eq(year), "capacity_floor_gw"].sum()
        )
        row["nuclear_upper_gw"] = (
            float(nuclear_upper.loc[nuclear_upper.year.eq(year), "capacity_upper_gw"].sum())
            if year in EXPANSION_YEARS
            else np.nan
        )
        row["battery_floor_gw"] = (
            float(battery.loc[battery.year.eq(year), "capacity_floor_gw"].sum())
            if year in EXPANSION_YEARS
            else np.nan
        )
        row["phs_floor_gw"] = (
            float(phs.loc[phs.year.eq(year), "capacity_floor_gw"].sum())
            if year in EXPANSION_YEARS
            else np.nan
        )
        row["phs_upper_gw"] = (
            float(phs.loc[phs.year.eq(year), "capacity_upper_gw"].sum())
            if year in EXPANSION_YEARS
            else np.nan
        )
        row["policy_nuclear_2030_gw"] = 110.0 if year == 2030 else np.nan
        row["policy_phs_2030_gw"] = 160.0 if year == 2030 else np.nan
        row["policy_new_storage_2030_gw"] = 300.0 if year == 2030 else np.nan
        rows.append(row)
    frame = pd.DataFrame(rows)
    write_csv(
        frame,
        TABLES / "table_m04_2_national_capacity_boundaries.csv",
        float_format="%.6f",
    )
    return frame


def build_capex_table(inputs: dict[str, object]) -> pd.DataFrame:
    capex: pd.DataFrame = inputs["capex"]  # type: ignore[assignment]
    config: dict = inputs["config"]  # type: ignore[assignment]
    lifetimes = config["finance"]["default_lifetime_years"]
    wacc = float(config["finance"]["real_wacc_fraction"])
    out = capex.copy()
    out["source_price_year_assigned"] = 2022
    out["price_year_assignment_basis"] = (
        "CISPO base year 2022; current China anchors use the 2022 renewable-energy report "
        "and future curves apply source decline rates"
    )
    out["cpi_2022_to_2025_factor"] = CPI_2022_TO_2025
    out["capex_2025_cny_per_kw_reporting"] = (
        out.capex_yuan_per_kw * CPI_2022_TO_2025
    )
    out["active_model_value_changed"] = False
    out["real_wacc_fraction"] = wacc
    out["lifetime_years"] = out.technology.map(lifetimes).astype(float)
    out["capital_recovery_factor"] = [
        capital_recovery_factor(wacc, lifetime) for lifetime in out.lifetime_years
    ]
    out["annualized_capex_active_yuan_per_kw_year"] = (
        out.capex_yuan_per_kw * out.capital_recovery_factor
    )
    out["annualized_capex_2025_cny_per_kw_year_reporting"] = (
        out.capex_2025_cny_per_kw_reporting * out.capital_recovery_factor
    )
    write_csv(
        out,
        TABLES / "table_m04_3_capex_trajectories_active_and_2025_price.csv",
        float_format="%.8f",
    )
    write_csv(
        out[
            [
                "technology",
                "year",
                "capex_yuan_per_kw",
                "capex_2025_cny_per_kw_reporting",
                "annualized_capex_active_yuan_per_kw_year",
                "annualized_capex_2025_cny_per_kw_year_reporting",
            ]
        ],
        FIGURE_DATA / "figure_m04_01_capex_trajectories.csv",
        float_format="%.8f",
    )
    return out


def build_ruc_om_table(inputs: dict[str, object]) -> pd.DataFrame:
    ruc: pd.DataFrame = inputs["ruc"]  # type: ignore[assignment]
    om: pd.DataFrame = inputs["om"]  # type: ignore[assignment]
    config: dict = inputs["config"]  # type: ignore[assignment]
    frame = ruc.merge(
        om.drop(columns=["source_page", "source_document"]),
        on="technology",
        how="left",
        validate="one_to_one",
    )
    frame["new_cohort_lifetime_years"] = frame.technology.map(
        config["finance"]["default_lifetime_years"]
    )
    frame["existing_fleet_retirement_lifetime_years"] = 40
    frame["lifetime_boundary_note"] = np.where(
        frame.new_cohort_lifetime_years.eq(40),
        "symmetric_existing_and_new",
        "existing_fleet_uses_40_year_retirement; new_cohort_uses_config_lifetime",
    )
    frame["variable_om_2025_cny_per_mwh_reporting"] = (
        frame.variable_om_yuan_per_mwh * CPI_2022_TO_2025
    )
    frame["startup_2025_cny_per_mw_reporting"] = (
        frame.startup_yuan_per_mw * CPI_2022_TO_2025
    )
    frame["shutdown_2025_cny_per_mw_reporting"] = (
        frame.shutdown_yuan_per_mw * CPI_2022_TO_2025
    )
    write_csv(
        frame,
        TABLES / "table_m04_4_thermal_nuclear_ruc_and_om.csv",
        float_format="%.8f",
    )
    return frame


def build_storage_table(inputs: dict[str, object], bounds: pd.DataFrame) -> pd.DataFrame:
    storage: pd.DataFrame = inputs["storage"]  # type: ignore[assignment]
    capex: pd.DataFrame = inputs["capex"]  # type: ignore[assignment]
    capex_2030 = capex.loc[capex.year.eq(2030)].set_index("technology")
    bounds_2030 = bounds.loc[bounds.year.eq(2030)].iloc[0]
    rows = []
    for row in storage.itertuples(index=False):
        rows.append(
            {
                "technology": row.technology,
                "duration_h": row.duration_h,
                "charge_efficiency": row.charge_efficiency,
                "discharge_efficiency": row.discharge_efficiency,
                "round_trip_efficiency": row.round_trip_efficiency,
                "self_discharge_fraction_per_day": row.self_discharge_fraction_per_day,
                "lifetime_years": row.lifetime_years,
                "fixed_om_fraction_capex_per_year": row.fixed_om_fraction_capex_per_year,
                "variable_om_yuan_per_mwh_active": row.variable_om_yuan_per_mwh,
                "variable_om_2025_cny_per_mwh_reporting": row.variable_om_yuan_per_mwh
                * CPI_2022_TO_2025,
                "capex_2030_yuan_per_kw_active": float(
                    capex_2030.loc[row.technology, "capex_yuan_per_kw"]
                ),
                "capacity_floor_2030_gw": float(
                    bounds_2030[f"{row.technology}_floor_gw"]
                    if row.technology == "battery"
                    else bounds_2030["phs_floor_gw"]
                ),
                "capacity_upper_2030_gw": (
                    np.nan
                    if row.technology == "battery"
                    else float(bounds_2030["phs_upper_gw"])
                ),
                "latest_policy_comparator_gw": (
                    300.0 if row.technology == "battery" else 160.0
                ),
                "policy_comparator_scope": (
                    "all new storage, not a mandatory battery floor"
                    if row.technology == "battery"
                    else "national pumped-storage installed capacity"
                ),
            }
        )
    frame = pd.DataFrame(rows)
    write_csv(
        frame,
        TABLES / "table_m04_5_storage_parameters_and_policy_comparison.csv",
        float_format="%.8f",
    )
    return frame


def build_fuel_table(inputs: dict[str, object]) -> pd.DataFrame:
    fuel: pd.DataFrame = inputs["fuel"]  # type: ignore[assignment]
    source_basis = {
        "coal": "2023 inferred provincial level",
        "gas": "2018 benchmark gate-station price plus 0.8 CNY/m3",
        "biomass": "Yuan et al. (2022) ex-factory price",
    }
    rows = []
    for fuel_name in ("coal", "gas", "biomass"):
        values = pd.to_numeric(fuel[f"{fuel_name}_yuan_per_gj"], errors="coerce")
        rows.append(
            {
                "fuel": fuel_name,
                "province_count": int(values.notna().sum()),
                "missing_province_count": int(values.isna().sum()),
                "active_min_yuan_per_gj": float(values.min()),
                "active_median_yuan_per_gj": float(values.median()),
                "active_max_yuan_per_gj": float(values.max()),
                "active_usd_to_cny": USD_CNY_ACTIVE,
                "official_2025_average_usd_to_cny": USD_CNY_2025,
                "fx_only_comparator_factor": USD_CNY_2025 / USD_CNY_ACTIVE,
                "source_price_year": source_basis[fuel_name],
                "temporal_method": fuel.temporal_method.iloc[0],
                "2025_price_normalization_status": (
                    "ACTIVE_VALUE_RETAINED; FINAL_CANDIDATE_USES_PUBLISHED_USD_PER_GJ"
                    "_X_7.1429_CNY_PER_USD"
                ),
            }
        )
    frame = pd.DataFrame(rows)
    write_csv(
        frame,
        TABLES / "table_m04_6_fuel_price_summary_and_fx_comparator.csv",
        float_format="%.8f",
    )
    return frame


def build_price_basis_decision(inputs: dict[str, object]) -> pd.DataFrame:
    rows = [
        {
            "parameter_family": "VRE, thermal, nuclear, hydro and storage CapEx",
            "active_basis": "CISPO 2022-base-year China anchors and projected decline rates",
            "source_price_year_status": "ASSIGNED_2022_FROM_METHOD_CONTEXT",
            "2025_treatment": "report CPI-normalized comparator; do not overwrite active model in this module",
            "factor_or_rule": f"{CPI_2022_TO_2025:.6f}",
            "decision": "NORMALIZE_FOR_REPORTING_AND_FUTURE_SCENARIO",
        },
        {
            "parameter_family": "Absolute variable O&M and startup/shutdown costs",
            "active_basis": "CISPO SI monetary inputs",
            "source_price_year_status": "ASSIGNED_2022_FROM_METHOD_CONTEXT",
            "2025_treatment": "multiply by cumulative 2022-2025 China CPI",
            "factor_or_rule": f"{CPI_2022_TO_2025:.6f}",
            "decision": "NORMALIZE_FOR_REPORTING_AND_FUTURE_SCENARIO",
        },
        {
            "parameter_family": "Fixed O&M fractions, efficiencies, durations, lifetimes and emission factors",
            "active_basis": "dimensionless or physical",
            "source_price_year_status": "NOT_APPLICABLE",
            "2025_treatment": "unchanged",
            "factor_or_rule": "1.0",
            "decision": "DO_NOT_PRICE_NORMALIZE",
        },
        {
            "parameter_family": "Provincial coal, gas and biomass prices",
            "active_basis": "An et al. (2025) Supplementary Table 2 USD/GJ converted at 6.9 CNY/USD and held constant",
            "source_price_year_status": "COAL_2023_INFERRED; GAS_2018_BENCHMARK_CONSTRUCTION; BIOMASS_2022_SOURCE",
            "2025_treatment": "final candidate converts published USD/GJ at official 2025 average 7.1429 CNY/USD; require fuel-price trajectories",
            "factor_or_rule": f"{USD_CNY_2025 / USD_CNY_ACTIVE:.6f}",
            "decision": "CORRECT_PROVENANCE_AND_FX_IN_CANDIDATE",
        },
        {
            "parameter_family": "CCS capture, transport and storage",
            "active_basis": "CISPO SI scalar costs",
            "source_price_year_status": "ASSIGNED_2022_FROM_METHOD_CONTEXT",
            "2025_treatment": "CPI-normalized comparator plus high/low sensitivity",
            "factor_or_rule": f"{CPI_2022_TO_2025:.6f}",
            "decision": "PROVISIONAL_NORMALIZATION",
        },
        {
            "parameter_family": "DAC",
            "active_basis": "explicit 2022 cost anchor",
            "source_price_year_status": "EXPLICIT_2022",
            "2025_treatment": "multiply CapEx and O&M by cumulative 2022-2025 China CPI",
            "factor_or_rule": f"{CPI_2022_TO_2025:.6f}",
            "decision": "NORMALIZE",
        },
        {
            "parameter_family": "Transmission and substation costs",
            "active_basis": "CISPO SI voltage-specific costs",
            "source_price_year_status": "ASSIGNED_2022_FROM_METHOD_CONTEXT",
            "2025_treatment": "CPI-normalized comparator; retain engineering-cost sensitivity",
            "factor_or_rule": f"{CPI_2022_TO_2025:.6f}",
            "decision": "PROVISIONAL_NORMALIZATION",
        },
        {
            "parameter_family": "Wave-energy CapEx",
            "active_basis": "EUR/kW converted at fixed 7.8 CNY/EUR; illustrative scenario",
            "source_price_year_status": "SOURCE_YEAR_NOT_EXPLICIT_IN_CONFIG",
            "2025_treatment": "retain active baseline; compare with 2025 annual-average 8.1185 CNY/EUR",
            "factor_or_rule": f"{EUR_CNY_2025 / EUR_CNY_ACTIVE:.6f}",
            "decision": "FX_SENSITIVITY_NOT_BASE_REPLACEMENT",
        },
        {
            "parameter_family": "Real WACC",
            "active_basis": "uniform 7.4% real",
            "source_price_year_status": "NOT_A_PRICE_LEVEL",
            "2025_treatment": "unchanged baseline; test technology-specific or 4-9% range",
            "factor_or_rule": "not applicable",
            "decision": "SENSITIVITY_REQUIRED",
        },
    ]
    frame = pd.DataFrame(rows)
    write_csv(frame, TABLES / "table_m04_7_price_basis_decision.csv")
    return frame


def build_objective_accounting_table() -> pd.DataFrame:
    frame = pd.DataFrame(
        [
            {
                "accounting_item": "Capacity investment",
                "implemented_equation": "CapEx × CRF × total in-service capacity",
                "implementation_scope": "VRE, thermal/nuclear, hydro, storage and transmission",
                "interpretation": "annualized planning-year system cost; existing capacity is also charged",
                "limitation": "not an incremental-only investment ledger",
            },
            {
                "accounting_item": "Fixed O&M",
                "implemented_equation": "CapEx × fixed-O&M fraction × total in-service capacity",
                "implementation_scope": "VRE, thermal/nuclear, hydro, storage and wave",
                "interpretation": "annual planning-year fixed cost",
                "limitation": "inherits the same price-basis requirement as CapEx",
            },
            {
                "accounting_item": "Variable operation",
                "implemented_equation": "yuan/MWh × annual hourly activity",
                "implementation_scope": "thermal, fuel, storage, startup/shutdown, ramping and flows",
                "interpretation": "annual operating cost for each planning-year solve",
                "limitation": "fuel prices are constructed from different source years and held constant through 2060",
            },
            {
                "accounting_item": "Planning sequence",
                "implemented_equation": "2030, 2040, 2050 and 2060 solved sequentially with cohort transfer",
                "implementation_scope": "four annual planning snapshots",
                "interpretation": "state-consistent sequence",
                "limitation": "objectives are not automatically discounted and summed to a 2025-2060 NPV",
            },
        ]
    )
    write_csv(frame, TABLES / "table_m04_8_effective_objective_accounting.csv")
    return frame


def build_policy_literature_crosswalk() -> pd.DataFrame:
    rows = [
        {
            "evidence": "New-type energy system construction plan for the 15th Five-Year Plan",
            "date": "2026-06-25",
            "identifier_or_url": "https://www.nea.gov.cn/20260625/0ccfdc1674e84868b49480edf584eb5f/202606250ccfdc1674e84868b49480edf584eb5f_27b526ec29479c4fd4bbb6f42d3ce5bbca.pdf",
            "parameter_relevance": "2030 nuclear 110 GW; PHS 160 GW; new storage 300 GW; distributed-energy hosting 900 GW",
            "module_decision": "use as policy comparator/upper-bound evidence, not as a forced technology mix",
        },
        {
            "evidence": "New storage scale-up action plan 2025-2027",
            "date": "2025-08-27",
            "identifier_or_url": "https://www.gov.cn/zhengce/zhengceku/202509/P020250912411822546143.pdf",
            "parameter_relevance": "new storage reaches at least 180 GW by 2027",
            "module_decision": "shows the inherited 65.85 GW battery floor is a legacy minimum, not a current national target",
        },
        {
            "evidence": "Renewable on-grid tariff market reform",
            "date": "2025-01-27",
            "identifier_or_url": "https://zfxxgk.ndrc.gov.cn/web/iteminfo.jsp?id=20482",
            "parameter_relevance": "post-2025 renewable energy enters market pricing with a settlement mechanism",
            "module_decision": "revenue policy does not directly replace engineering CapEx; relevant to future market-value extensions",
        },
        {
            "evidence": "China 2025 national economic and social development communiqué",
            "date": "2026-02-28",
            "identifier_or_url": "https://www.stats.gov.cn/sj/zxfb/202602/t20260228_1962662.html",
            "parameter_relevance": "2025 CPI 0.0%; annual average USD/CNY 7.1429",
            "module_decision": "supports 2025 reporting price and FX comparators",
        },
        {
            "evidence": "Integrated modeling for the transition pathway of China's power system",
            "date": "2025",
            "identifier_or_url": "https://doi.org/10.1039/D5EE00355E",
            "parameter_relevance": "primary CISPO methods and technology-economic baseline",
            "module_decision": "retain as replication baseline while separating source values from local updates",
        },
        {
            "evidence": "High-resolution gridded dataset of China's offshore wind potential and costs under technical change",
            "date": "2025",
            "identifier_or_url": "https://doi.org/10.1038/s41597-025-04428-8",
            "parameter_relevance": "grid-level offshore investment and LCOE vary with depth, distance and technical change",
            "module_decision": "national scalar offshore CapEx remains baseline only; spatial-cost sensitivity is high priority",
        },
        {
            "evidence": "Substantially lower estimates in China's offshore wind potential using farm-scale spatial modeling and wake effects",
            "date": "2026",
            "identifier_or_url": "https://doi.org/10.1038/s41467-026-68655-2",
            "parameter_relevance": "farm layout, wake and distance/depth can raise costs and reduce potential",
            "module_decision": "reinforces explicit offshore-wind uncertainty rather than a single deterministic scalar",
        },
        {
            "evidence": "Historical and future projected costs of capital for ten energy technologies across 176 countries",
            "date": "2025",
            "identifier_or_url": "https://doi.org/10.1038/s41597-025-06177-0",
            "parameter_relevance": "technology- and country-specific cost of capital",
            "module_decision": "uniform 7.4% real WACC is retained for replication but requires sensitivity",
        },
        {
            "evidence": "Heterogeneous effects of battery storage deployment strategies on provincial power-system decarbonization",
            "date": "2023",
            "identifier_or_url": "https://doi.org/10.1038/s41467-023-40337-3",
            "parameter_relevance": "battery duration and deployment strategy change system outcomes",
            "module_decision": "4-hour battery is a baseline class, not a complete storage-duration representation",
        },
    ]
    frame = pd.DataFrame(rows)
    write_csv(frame, TABLES / "table_m04_9_policy_and_literature_crosswalk.csv")
    return frame


def build_outdated_document_audit() -> pd.DataFrame:
    frame = pd.DataFrame(
        [
            {
                "document": "config/technology_parameters.json",
                "stale_statement_or_scope": "unresolved register says production uses 278 Natural Earth centers",
                "current_authority": "config/optimization_2030.json: city_337; data/load_center_network/city_337",
                "impact": "documentation-only row can misstate production network",
                "disposition": "SUPERSEDED_DO_NOT_CITE_AS_CURRENT; update during next core data-package rebuild",
            },
            {
                "document": "data/technology/unresolved_parameters.csv",
                "stale_statement_or_scope": "generated sidecar repeats 278-center production statement",
                "current_authority": "337 centers and 642 intra-provincial edges",
                "impact": "not consumed by optimization equations but can mislead supplement drafting",
                "disposition": "SUPERSEDED_SIDECAR; retained unchanged to avoid mutating active data package",
            },
            {
                "document": "supplementary_materials/MODEL_V0719_REVIEW_REPORT.md",
                "stale_statement_or_scope": "V0719 point-in-time model/server review",
                "current_authority": "CODEX_HANDOFF.md current validated snapshot and current code",
                "impact": "useful history but not current parameter authority",
                "disposition": "HISTORICAL_ONLY",
            },
            {
                "document": "supplementary_materials/National_model_Codex_implementation_plan.md",
                "stale_statement_or_scope": "implementation plan rather than verified current state",
                "current_authority": "current config, code, manifests and handoff",
                "impact": "planned actions may already be implemented or superseded",
                "disposition": "PLAN_ONLY_NOT_EVIDENCE",
            },
            {
                "document": "supplementary_materials/deep-research-report.md",
                "stale_statement_or_scope": "contains chat-internal citation markers and earlier engineering recommendations",
                "current_authority": "current code and publication-ready source references",
                "impact": "not suitable for submission citation or parameter provenance",
                "disposition": "BACKGROUND_ONLY_NOT_SUBMISSION_READY",
            },
            {
                "document": "tech_economic/outputs/techno_economic_lit_review_20260610/techno_economic_literature_review_zh.md",
                "stale_statement_or_scope": "states 32 grids and predates the June 2026 national energy plan",
                "current_authority": "31-province implementation and latest official policy crosswalk in Module 04",
                "impact": "literature synthesis remains useful, but model boundary and policy comparison are outdated",
                "disposition": "PARTIALLY_SUPERSEDED",
            },
        ]
    )
    write_csv(frame, TABLES / "table_m04_10_outdated_document_audit.csv")
    return frame


def build_figure_data(
    bounds: pd.DataFrame,
    price_decision: pd.DataFrame,
    capex: pd.DataFrame,
    inputs: dict[str, object],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    write_csv(
        bounds,
        FIGURE_DATA / "figure_m04_01_capacity_boundaries.csv",
        float_format="%.8f",
    )

    evidence_rows = [
        ("Technology CapEx", 1, 1, 1, 1),
        ("O&M / start-stop", 1, 1, 1, 1),
        ("Fuel prices", 0, 1, 1, 0),
        ("CCS", 0.5, 1, 1, 0.5),
        ("DAC", 1, 1, 1, 1),
        ("Transmission", 0.5, 1, 1, 0.5),
        ("Wave energy", 0, 1, 1, 0),
        ("Real WACC", 1, 1, 1, 0.5),
    ]
    evidence = pd.DataFrame(
        evidence_rows,
        columns=[
            "parameter_family",
            "source_year_explicit",
            "currency_or_dimension_explicit",
            "effective_use_verified",
            "deterministic_2025_conversion",
        ],
    )
    write_csv(evidence, FIGURE_DATA / "figure_m04_02_evidence_matrix.csv")

    adjustments = pd.DataFrame(
        [
            {
                "comparator": "2022 CNY → 2025 CNY\n(CPI)",
                "percent_change": (CPI_2022_TO_2025 - 1.0) * 100.0,
                "status": "reporting normalization",
            },
            {
                "comparator": "USD/CNY\n6.9 → 7.1429",
                "percent_change": (USD_CNY_2025 / USD_CNY_ACTIVE - 1.0) * 100.0,
                "status": "FX-only comparator",
            },
            {
                "comparator": "EUR/CNY\n7.8 → 8.1185",
                "percent_change": (EUR_CNY_2025 / EUR_CNY_ACTIVE - 1.0) * 100.0,
                "status": "FX-only comparator",
            },
        ]
    )
    write_csv(adjustments, FIGURE_DATA / "figure_m04_02_price_adjustments.csv")

    config: dict = inputs["config"]  # type: ignore[assignment]
    selected = [
        "onwind",
        "offwind",
        "upv",
        "coal",
        "gas",
        "nuclear",
        "battery",
        "phs",
        "transmission",
    ]
    crf_rows = []
    for technology in selected:
        lifetime = float(config["finance"]["default_lifetime_years"][technology])
        crf_rows.append(
            {
                "technology": technology,
                "lifetime_years": lifetime,
                "real_wacc_fraction": float(config["finance"]["real_wacc_fraction"]),
                "capital_recovery_factor": capital_recovery_factor(
                    float(config["finance"]["real_wacc_fraction"]), lifetime
                ),
            }
        )
    crf = pd.DataFrame(crf_rows)
    write_csv(crf, FIGURE_DATA / "figure_m04_02_crf.csv")

    risks = pd.DataFrame(
        [
            ("Fuel price year/trajectory", 5.0, 1.0, "High"),
            ("Offshore spatial cost", 4.8, 2.0, "High"),
            ("Battery duration/cost", 4.5, 2.2, "High"),
            ("Uniform WACC", 4.0, 2.6, "High"),
            ("Existing-fleet lifetime", 3.8, 2.5, "High"),
            ("CCS/DAC cost", 4.3, 2.0, "High"),
            ("CHP CapEx mapping", 3.0, 2.0, "Medium"),
            ("Hydro CapEx trajectory", 2.0, 3.0, "Medium"),
        ],
        columns=["parameter", "system_impact_score", "evidence_strength_score", "priority"],
    )
    write_csv(risks, FIGURE_DATA / "figure_m04_02_uncertainty_priorities.csv")
    return evidence, adjustments, crf, risks


def panel_label(ax, label: str) -> None:
    ax.text(
        -0.16,
        1.06,
        label,
        transform=ax.transAxes,
        fontsize=8.5,
        fontweight="bold",
        va="top",
        ha="left",
    )


def plot_capacity_and_capex(bounds: pd.DataFrame, capex: pd.DataFrame) -> None:
    configure_style()
    fig, axes = plt.subplots(2, 2, figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN))
    ax = axes[0, 0]
    stack_columns = [
        "coal_without_ccs_floor_gw",
        "coal_with_ccs_floor_gw",
        "gas_without_ccs_floor_gw",
        "gas_with_ccs_floor_gw",
        "bio_and_beccs_floor_gw",
    ]
    stack_labels = ["Coal/CHP", "Coal CCS/CHP CCS", "Gas/CHP", "Gas CCS/CHP CCS", "Bio/BECCS"]
    stack_colors = [
        COLORS["coal"],
        COLORS["coal_ccs"],
        COLORS["gas"],
        COLORS["gas_ccs"],
        COLORS["bio"],
    ]
    ax.stackplot(
        bounds.year,
        *[bounds[column] for column in stack_columns],
        labels=stack_labels,
        colors=stack_colors,
        alpha=0.92,
        linewidth=0.2,
    )
    ax.plot(
        bounds.year,
        bounds.nuclear_floor_gw,
        color=COLORS["nuclear"],
        marker="o",
        ms=3.2,
        lw=1.2,
        label="Nuclear floor",
    )
    ax.set_ylabel("Capacity floor (GW)")
    ax.set_xlabel("Planning year")
    ax.set_xticks(YEARS)
    ax.set_title("Exogenous thermal and nuclear capacity floors")
    ax.legend(ncol=2, loc="upper right", columnspacing=0.8, handlelength=1.3)
    panel_label(ax, "a")

    ax = axes[0, 1]
    b = bounds.loc[bounds.year.isin(EXPANSION_YEARS)]
    ax.fill_between(
        b.year,
        b.nuclear_floor_gw,
        b.nuclear_upper_gw,
        color="#F2D8AF",
        alpha=0.65,
        label="Allowed expansion interval",
    )
    ax.plot(
        b.year,
        b.nuclear_floor_gw,
        color=COLORS["nuclear"],
        marker="o",
        lw=1.4,
        label="GEM pipeline floor",
    )
    ax.plot(
        b.year,
        b.nuclear_upper_gw,
        color="#8D5A19",
        marker="s",
        lw=1.2,
        label="Policy/scenario upper",
    )
    ax.scatter([2030], [110], marker="D", s=24, color=COLORS["policy"], zorder=4)
    ax.text(
        2030.8,
        115.5,
        "2030 policy comparator\n110 GW",
        fontsize=5.8,
        ha="left",
        va="bottom",
    )
    ax.set_ylabel("Nuclear capacity (GW)")
    ax.set_xlabel("Planning year")
    ax.set_xticks(EXPANSION_YEARS)
    ax.set_title("Nuclear lower and upper bounds")
    ax.legend(loc="upper left")
    panel_label(ax, "b")

    ax = axes[1, 0]
    ax.fill_between(
        b.year,
        b.phs_floor_gw,
        b.phs_upper_gw,
        color="#C9DFEF",
        alpha=0.75,
        label="PHS feasible interval",
    )
    ax.plot(b.year, b.phs_floor_gw, color=COLORS["phs"], marker="o", lw=1.2, label="PHS floor")
    ax.plot(b.year, b.phs_upper_gw, color="#174A6E", marker="s", lw=1.2, label="PHS upper")
    ax.plot(
        b.year,
        b.battery_floor_gw,
        color=COLORS["battery"],
        marker="o",
        lw=1.2,
        label="Battery floor",
    )
    ax.scatter([2030, 2030], [160, 300], marker="D", s=24, color=COLORS["policy"], zorder=4)
    ax.annotate("PHS policy 160", (2030, 160), xytext=(2033, 130), fontsize=5.8)
    ax.annotate("New storage policy 300", (2030, 300), xytext=(2033, 275), fontsize=5.8)
    ax.set_ylabel("Storage power capacity (GW)")
    ax.set_xlabel("Planning year")
    ax.set_xticks(EXPANSION_YEARS)
    ax.set_title("Storage bounds and policy comparators")
    ax.legend(loc="upper left")
    panel_label(ax, "c")

    ax = axes[1, 1]
    selected = list(TECH_LABELS)
    palette = [
        "#2E73B7",
        "#174A6E",
        "#D9A441",
        "#E8C56D",
        COLORS["battery"],
        COLORS["phs"],
        COLORS["coal_ccs"],
        COLORS["nuclear"],
        "#3E8B78",
    ]
    for technology, color in zip(selected, palette):
        values = capex.loc[capex.technology.eq(technology)].sort_values("year")
        ax.plot(
            values.year,
            values.capex_yuan_per_kw,
            marker="o",
            ms=2.6,
            lw=1.0,
            color=color,
            label=TECH_LABELS[technology],
        )
    ax.set_yscale("log")
    ax.set_ylabel("Active CapEx (yuan kW$^{-1}$, log scale)")
    ax.set_xlabel("Planning year")
    ax.set_xticks(EXPANSION_YEARS)
    ax.set_title("Implemented technology CapEx trajectories")
    ax.legend(ncol=3, loc="lower left", columnspacing=0.7, handlelength=1.2)
    panel_label(ax, "d")

    fig.subplots_adjust(left=0.085, right=0.985, bottom=0.09, top=0.95, wspace=0.28, hspace=0.32)
    pdf = FIGURES / "Figure_M04_01_capacity_boundaries_and_capex.pdf"
    png = FIGURES / "Figure_M04_01_capacity_boundaries_and_capex.png"
    fig.savefig(pdf, bbox_inches=None)
    fig.savefig(png, dpi=PNG_DPI, bbox_inches=None)
    plt.close(fig)


def plot_price_basis_and_uncertainty(
    evidence: pd.DataFrame,
    adjustments: pd.DataFrame,
    crf: pd.DataFrame,
    risks: pd.DataFrame,
) -> None:
    configure_style()
    fig, axes = plt.subplots(2, 2, figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN))

    ax = axes[0, 0]
    matrix_columns = [
        "source_year_explicit",
        "currency_or_dimension_explicit",
        "effective_use_verified",
        "deterministic_2025_conversion",
    ]
    matrix = evidence[matrix_columns].to_numpy(dtype=float)
    cmap = mpl.colors.LinearSegmentedColormap.from_list(
        "evidence", ["#D9D9D9", "#F2C879", "#3E8B78"]
    )
    image = ax.imshow(matrix, vmin=0, vmax=1, cmap=cmap, aspect="auto")
    ax.set_yticks(np.arange(len(evidence)))
    ax.set_yticklabels(evidence.parameter_family)
    ax.set_xticks(np.arange(len(matrix_columns)))
    ax.set_xticklabels(["Price year", "Currency/\ndimension", "Code use", "2025\nconversion"], rotation=0)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            label = {0.0: "No", 0.5: "Partial", 1.0: "Yes"}[float(matrix[i, j])]
            ax.text(j, i, label, ha="center", va="center", fontsize=5.5, color="#222222")
    ax.tick_params(length=0)
    ax.set_title("Evidence completeness of active parameter families")
    panel_label(ax, "a")

    ax = axes[0, 1]
    colors = ["#3E8B78", "#D18B37", "#C95A49"]
    bars = ax.bar(
        np.arange(len(adjustments)),
        adjustments.percent_change,
        color=colors,
        width=0.62,
    )
    ax.axhline(0, color="#444444", lw=0.55)
    ax.set_xticks(np.arange(len(adjustments)))
    ax.set_xticklabels(adjustments.comparator)
    ax.set_ylabel("Change relative to active factor (%)")
    ax.set_title("2025 reporting and FX comparators")
    for bar, value in zip(bars, adjustments.percent_change):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.12,
            f"{value:.2f}%",
            ha="center",
            va="bottom",
            fontsize=6.2,
        )
    panel_label(ax, "b")

    ax = axes[1, 0]
    crf_plot = crf.copy()
    label_map = {
        "onwind": "Onshore",
        "offwind": "Offshore",
        "upv": "Utility PV",
        "coal": "Coal",
        "gas": "Gas",
        "nuclear": "Nuclear",
        "battery": "Battery",
        "phs": "PHS",
        "transmission": "Transmission",
    }
    crf_plot["label"] = crf_plot.technology.map(label_map)
    bar_colors = [
        "#2E73B7",
        "#174A6E",
        "#D9A441",
        COLORS["coal"],
        COLORS["gas"],
        COLORS["nuclear"],
        COLORS["battery"],
        COLORS["phs"],
        "#777777",
    ]
    bars = ax.bar(
        np.arange(len(crf_plot)),
        crf_plot.capital_recovery_factor * 100.0,
        color=bar_colors,
        width=0.68,
    )
    ax.set_xticks(np.arange(len(crf_plot)))
    ax.set_xticklabels(crf_plot.label, rotation=40, ha="right")
    ax.set_ylabel("Capital recovery factor (% yr$^{-1}$)")
    ax.set_title("Uniform 7.4% real WACC with technology lifetimes")
    for bar, life in zip(bars, crf_plot.lifetime_years):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.13,
            f"{life:.0f} y",
            ha="center",
            va="bottom",
            fontsize=5.2,
        )
    panel_label(ax, "c")

    ax = axes[1, 1]
    priority_colors = {"High": COLORS["uncertainty"], "Medium": "#D9A441"}
    for row in risks.itertuples(index=False):
        ax.scatter(
            row.evidence_strength_score,
            row.system_impact_score,
            s=28,
            color=priority_colors[row.priority],
            edgecolor="white",
            linewidth=0.4,
            zorder=3,
        )
        ax.text(
            row.evidence_strength_score + 0.05,
            row.system_impact_score + 0.03,
            row.parameter,
            fontsize=5.2,
        )
    ax.set_xlim(0.7, 4.05)
    ax.set_ylim(1.5, 5.4)
    ax.set_xlabel("Evidence strength (higher is better)")
    ax.set_ylabel("Potential system impact")
    ax.set_title("Priorities for sensitivity and replacement")
    ax.grid(color="#DDDDDD", lw=0.4, alpha=0.8)
    panel_label(ax, "d")

    fig.subplots_adjust(left=0.12, right=0.985, bottom=0.12, top=0.95, wspace=0.35, hspace=0.36)
    pdf = FIGURES / "Figure_M04_02_price_basis_and_uncertainty.pdf"
    png = FIGURES / "Figure_M04_02_price_basis_and_uncertainty.png"
    fig.savefig(pdf, bbox_inches=None)
    fig.savefig(png, dpi=PNG_DPI, bbox_inches=None)
    plt.close(fig)


def build_qa(
    inputs: dict[str, object],
    register: pd.DataFrame,
    bounds: pd.DataFrame,
    capex: pd.DataFrame,
    ruc_om: pd.DataFrame,
    storage: pd.DataFrame,
    outdated: pd.DataFrame,
) -> pd.DataFrame:
    checks: list[dict[str, object]] = []

    def add(check: str, passed: bool, observed: object, expected: object) -> None:
        checks.append(
            {
                "check": check,
                "status": "PASS" if passed else "FAIL",
                "observed": observed,
                "expected": expected,
            }
        )

    add("active_input_register_rows", len(register) == 18, len(register), 18)
    add("technology_capex_rows", len(capex) == 76, len(capex), 76)
    add(
        "technology_capex_unique",
        not capex.duplicated(["technology", "year"]).any(),
        int(capex.duplicated(["technology", "year"]).sum()),
        0,
    )
    add("technology_capex_positive", capex.capex_yuan_per_kw.gt(0).all(), float(capex.capex_yuan_per_kw.min()), ">0")
    add(
        "cpi_normalization_exact",
        np.allclose(
            capex.capex_2025_cny_per_kw_reporting,
            capex.capex_yuan_per_kw * CPI_2022_TO_2025,
        ),
        CPI_2022_TO_2025,
        1.004004,
    )
    add("capacity_boundary_years", bounds.year.tolist() == YEARS, bounds.year.tolist(), YEARS)
    expansion = bounds.loc[bounds.year.isin(EXPANSION_YEARS)]
    add(
        "nuclear_floor_not_above_upper",
        (expansion.nuclear_floor_gw <= expansion.nuclear_upper_gw + 1e-9).all(),
        float((expansion.nuclear_floor_gw - expansion.nuclear_upper_gw).max()),
        "<=0 GW",
    )
    add(
        "battery_2030_floor",
        np.isclose(float(bounds.loc[bounds.year.eq(2030), "battery_floor_gw"].iloc[0]), 65.85),
        float(bounds.loc[bounds.year.eq(2030), "battery_floor_gw"].iloc[0]),
        65.85,
    )
    add(
        "phs_floor_not_above_upper",
        (expansion.phs_floor_gw <= expansion.phs_upper_gw + 1e-9).all(),
        float((expansion.phs_floor_gw - expansion.phs_upper_gw).max()),
        "<=0 GW",
    )
    add("ruc_om_technology_rows", len(ruc_om) == 11, len(ruc_om), 11)
    add("storage_technology_rows", len(storage) == 2, len(storage), 2)
    add("dac_rows", len(inputs["dac"]) == 20, len(inputs["dac"]), 20)
    add("fuel_province_rows", len(inputs["fuel"]) == 31, len(inputs["fuel"]), 31)
    add(
        "fuel_external_provenance_resolved",
        inputs["fuel"]["source_evidence"].astype(str).str.contains(  # type: ignore[index]
            "provincial_fuel_costs_supplementary_table2.png", regex=False
        ).all(),
        "An et al. (2025) Supplementary Table 2 screenshot traced externally",
        "all 31 rows share the traced Table S2 evidence",
    )
    add(
        "outdated_network_statement_detected",
        outdated.document.isin(
            ["config/technology_parameters.json", "data/technology/unresolved_parameters.csv"]
        ).sum()
        == 2,
        int(
            outdated.document.isin(
                ["config/technology_parameters.json", "data/technology/unresolved_parameters.csv"]
            ).sum()
        ),
        2,
    )
    expected_px = (int(FIGURE_WIDTH_IN * PNG_DPI), int(FIGURE_HEIGHT_IN * PNG_DPI))
    for name in (
        "Figure_M04_01_capacity_boundaries_and_capex",
        "Figure_M04_02_price_basis_and_uncertainty",
    ):
        png = FIGURES / f"{name}.png"
        pdf = FIGURES / f"{name}.pdf"
        with Image.open(png) as image:
            size = image.size
        add(f"{name}_png_dimensions", size == expected_px, f"{size[0]}x{size[1]}", f"{expected_px[0]}x{expected_px[1]}")
        add(f"{name}_pdf_exists", pdf.exists() and pdf.stat().st_size > 0, pdf.stat().st_size if pdf.exists() else 0, ">0 bytes")

    frame = pd.DataFrame(checks)
    write_csv(frame, QA / "formal_closure_validation.csv")
    return frame


def main() -> None:
    ensure_dirs()
    inputs = load_inputs()
    register = build_active_input_register(inputs)
    bounds = build_capacity_boundaries(inputs)
    capex = build_capex_table(inputs)
    ruc_om = build_ruc_om_table(inputs)
    storage = build_storage_table(inputs, bounds)
    fuel = build_fuel_table(inputs)
    price_decision = build_price_basis_decision(inputs)
    objective = build_objective_accounting_table()
    policy = build_policy_literature_crosswalk()
    outdated = build_outdated_document_audit()
    evidence, adjustments, crf, risks = build_figure_data(
        bounds, price_decision, capex, inputs
    )
    plot_capacity_and_capex(bounds, capex)
    plot_price_basis_and_uncertainty(evidence, adjustments, crf, risks)
    qa = build_qa(inputs, register, bounds, capex, ruc_om, storage, outdated)

    summary = {
        "module": "04_thermal_nuclear_storage_technoeconomics",
        "generated_at": "2026-07-28",
        "git_head_at_audit": "701b9bc225013a5009dcce3f4e97ee2063dcd00f",
        "price_reporting_basis": "2025 constant CNY",
        "cpi_2022_to_2025_factor": CPI_2022_TO_2025,
        "active_model_inputs_mutated": False,
        "table_count": len(list(TABLES.glob("*.csv"))),
        "figure_data_count": len(list(FIGURE_DATA.glob("*.csv"))),
        "figure_count": len(list(FIGURES.glob("*"))),
        "qa_pass": int(qa.status.eq("PASS").sum()),
        "qa_fail": int(qa.status.eq("FAIL").sum()),
        "key_active_values": {
            "real_wacc_fraction": float(inputs["config"]["finance"]["real_wacc_fraction"]),  # type: ignore[index]
            "battery_2030_floor_gw": float(
                bounds.loc[bounds.year.eq(2030), "battery_floor_gw"].iloc[0]
            ),
            "phs_2030_floor_gw": float(
                bounds.loc[bounds.year.eq(2030), "phs_floor_gw"].iloc[0]
            ),
            "phs_2030_upper_gw": float(
                bounds.loc[bounds.year.eq(2030), "phs_upper_gw"].iloc[0]
            ),
            "nuclear_2030_floor_gw": float(
                bounds.loc[bounds.year.eq(2030), "nuclear_floor_gw"].iloc[0]
            ),
            "nuclear_2030_upper_gw": float(
                bounds.loc[bounds.year.eq(2030), "nuclear_upper_gw"].iloc[0]
            ),
        },
        "formal_terminal_marker": (
            "FINAL_M04_TECHNOECONOMIC_CLOSURE_PASS"
            if not qa.status.eq("FAIL").any()
            else "M04_QA_FAIL"
        ),
    }
    (QA / "run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if qa.status.eq("FAIL").any():
        raise RuntimeError(
            "Module 04 QA failed:\n"
            + qa.loc[qa.status.eq("FAIL")].to_string(index=False)
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
