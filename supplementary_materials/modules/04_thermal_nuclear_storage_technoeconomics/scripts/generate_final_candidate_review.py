"""Generate the review-ready 2025-CNY techno-economic candidate package.

The outputs in ``candidate_inputs`` are implementation-ready overlays for
author review.  This script deliberately does not modify files under
``National_model/data`` or ``National_model/config``.

Monetary conventions
--------------------
* CISPO monetary inputs assigned to the 2022 price basis are multiplied by
  China CPI for 2023--2025: 1.002 * 1.002 * 1.000 = 1.004004.
* The published provincial fuel table is retained in its reported USD/GJ
  units and converted with the official 2025 average exchange rate,
  7.1429 CNY/USD.  This is a currency conversion of published values, not a
  claim that the underlying constructed fuel series is a 2025 spot-price
  observation.
* Wave-energy EUR values are converted at 8.1185 CNY/EUR for sensitivity
  scenarios.  The current production Base enables wave; this candidate package
  recommends disabling it in the final reference case pending sensitivity.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image


MODULE = Path(__file__).resolve().parents[1]
NATIONAL_MODEL = MODULE.parents[2]
TABLES = MODULE / "tables"
FIGURES = MODULE / "figures"
FIGURE_DATA = MODULE / "figure_data"
QA = MODULE / "qa"
CANDIDATE = MODULE / "candidate_inputs"

CPI_2022_2025 = 1.004004
USD_CNY_2025 = 7.1429
EUR_CNY_2025 = 8.1185
FIGURE_WIDTH_IN = 7.0
PNG_DPI = 450

COLORS = {
    "onwind": "#2878B5",
    "offwind": "#55A6D9",
    "upv": "#E59D2A",
    "dpv": "#F2C14E",
    "coal": "#555555",
    "coalccs": "#9B7653",
    "gas": "#7563A8",
    "gasccs": "#B29BCB",
    "bio": "#4E8B65",
    "bioccs": "#8DBA91",
    "nuclear": "#D17A22",
    "hydro": "#2B8CBE",
    "battery": "#C94C4C",
    "phs": "#276FBF",
}

LABELS = {
    "onwind": "Onshore wind",
    "offwind": "Offshore wind",
    "upv": "Utility PV",
    "dpv": "Distributed PV",
    "coal": "Coal",
    "coalccs": "Coal + CCS",
    "gas": "Gas",
    "gasccs": "Gas + CCS",
    "bio": "Biomass",
    "bioccs": "BECCS",
    "nuclear": "Nuclear",
    "hydro": "Hydropower",
    "battery": "Battery (4 h)",
    "phs": "Pumped hydro",
}


def ensure_dirs() -> None:
    for path in (TABLES, FIGURES, FIGURE_DATA, QA, CANDIDATE):
        path.mkdir(parents=True, exist_ok=True)


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def configure_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 7.2,
            "axes.labelsize": 7.2,
            "axes.titlesize": 8.0,
            "xtick.labelsize": 6.6,
            "ytick.labelsize": 6.6,
            "axes.linewidth": 0.6,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
            "legend.fontsize": 6.3,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def save_figure(fig: plt.Figure, stem: str) -> None:
    # Preserve the exact journal-width canvas.  ``bbox_inches='tight'`` changes
    # physical dimensions and makes the PNG/PDF contract non-deterministic.
    fig.savefig(FIGURES / f"{stem}.pdf")
    fig.savefig(
        FIGURES / f"{stem}.png",
        dpi=PNG_DPI,
        pil_kwargs={"compress_level": 6},
    )
    plt.close(fig)


def build_candidate_capex() -> pd.DataFrame:
    source = pd.read_csv(
        NATIONAL_MODEL / "data" / "technology" / "technology_capex_by_year.csv"
    )
    out = source.copy()
    out.insert(
        out.columns.get_loc("capex_yuan_per_kw") + 1,
        "active_capex_yuan_per_kw",
        out["capex_yuan_per_kw"],
    )
    out["capex_yuan_per_kw"] = out["capex_yuan_per_kw"] * CPI_2022_2025
    out["candidate_price_basis"] = "2025 constant CNY"
    out["conversion_rule"] = "2022 CNY x 1.004004 China CPI"
    out["implementation_status"] = "PROPOSED_NOT_APPLIED"
    write_csv(out, CANDIDATE / "technology_capex_by_year_2025_candidate.csv")
    return out


def build_candidate_fuel() -> tuple[pd.DataFrame, pd.DataFrame]:
    source = pd.read_csv(
        NATIONAL_MODEL / "data" / "technology" / "province_fuel_prices.csv"
    )
    out = source.copy()
    for fuel in ("coal", "gas", "biomass"):
        out[f"active_{fuel}_yuan_per_gj"] = out[f"{fuel}_yuan_per_gj"]
        out[f"{fuel}_yuan_per_gj"] = out[f"{fuel}_usd_per_gj"] * USD_CNY_2025
    out["usd_to_yuan"] = USD_CNY_2025
    out["price_basis_year"] = (
        "coal: 2023 inferred provincial level; gas: 2018 benchmark gate-station "
        "plus 0.8 CNY/m3; biomass: Yuan et al. (2022) ex-factory price"
    )
    out["temporal_method"] = (
        "published provincial USD/GJ values held constant through 2060; "
        "fuel trajectories reserved for sensitivity"
    )
    out["source_evidence"] = (
        "An et al. (2025), Nature Communications 16, 2311, "
        "Supplementary Note 3 and Supplementary Table 2; "
        "doi:10.1038/s41467-025-57559-2"
    )
    out["currency_conversion_note"] = (
        "reported USD/GJ x official 2025 average 7.1429 CNY/USD; "
        "not a 2025 spot-price observation"
    )
    out["implementation_status"] = "PROPOSED_NOT_APPLIED"
    write_csv(out, CANDIDATE / "province_fuel_prices_2025_candidate.csv")

    derived = pd.read_csv(
        NATIONAL_MODEL
        / "data"
        / "technology"
        / "province_fuel_generation_cost_by_year.csv"
    )
    price_lookup = {
        (int(row.province_code), fuel): getattr(row, f"{fuel}_yuan_per_gj")
        for row in out.itertuples(index=False)
        for fuel in ("coal", "gas", "biomass")
    }
    derived["active_fuel_price_yuan_per_gj"] = derived["fuel_price_yuan_per_gj"]
    derived["active_fuel_cost_yuan_per_mwh"] = derived["fuel_cost_yuan_per_mwh"]
    derived["fuel_price_yuan_per_gj"] = [
        price_lookup[(int(province), fuel)]
        for province, fuel in zip(derived["province_code"], derived["fuel"])
    ]
    derived["fuel_cost_yuan_per_mwh"] = (
        derived["fuel_price_yuan_per_gj"] * derived["fuel_load_gj_per_mwh"]
    )
    derived["price_temporal_method"] = (
        "published provincial values converted at 2025 FX and held constant "
        "through 2060; sensitivity trajectories not yet applied"
    )
    derived["source_evidence"] = out["source_evidence"].iloc[0]
    derived["implementation_status"] = "PROPOSED_NOT_APPLIED"
    write_csv(
        derived,
        CANDIDATE / "province_fuel_generation_cost_by_year_2025_candidate.csv",
    )
    return out, derived


def build_candidate_other_costs() -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    def add(
        family: str,
        item: str,
        active: float,
        candidate: float,
        unit: str,
        basis: str,
        decision: str,
    ) -> None:
        rows.append(
            {
                "parameter_family": family,
                "parameter": item,
                "active_value": active,
                "candidate_final_value": candidate,
                "unit": unit,
                "candidate_price_basis": basis,
                "conversion_or_selection_rule": decision,
                "implementation_status": "PROPOSED_NOT_APPLIED",
            }
        )

    ruc = pd.read_csv(
        NATIONAL_MODEL / "data" / "technology" / "thermal_nuclear_ruc_parameters.csv"
    )
    for row in ruc.itertuples(index=False):
        for name in ("startup_yuan_per_mw", "shutdown_yuan_per_mw"):
            active = float(getattr(row, name))
            add(
                "thermal_ruc",
                f"{row.technology}.{name}",
                active,
                active * CPI_2022_2025,
                "2025 CNY/MW-event",
                "2025 constant CNY",
                "2022 CNY x 1.004004 CPI",
            )
        for name, unit in (
            ("pmin_fraction", "fraction"),
            ("pmax_fraction", "fraction"),
            ("min_up_h", "h"),
            ("min_down_h", "h"),
            ("ramp_fraction_per_h", "fraction/h"),
            ("fuel_load_mj_per_kwh", "MJ/kWh"),
            ("ccs_power_loss_fraction", "fraction"),
        ):
            value = float(getattr(row, name))
            add(
                "thermal_ruc",
                f"{row.technology}.{name}",
                value,
                value,
                unit,
                "physical parameter",
                "retain current CISPO value after literature review",
            )

    om = pd.read_csv(
        NATIONAL_MODEL / "data" / "technology" / "thermal_nuclear_om_parameters.csv"
    )
    for row in om.itertuples(index=False):
        add(
            "thermal_om",
            f"{row.technology}.fixed_om_fraction_capex_per_year",
            float(row.fixed_om_fraction_capex_per_year),
            float(row.fixed_om_fraction_capex_per_year),
            "fraction/year",
            "dimensionless",
            "retain current CISPO value",
        )
        add(
            "thermal_om",
            f"{row.technology}.variable_om",
            float(row.variable_om_yuan_per_mwh),
            float(row.variable_om_yuan_per_mwh) * CPI_2022_2025,
            "2025 CNY/MWh",
            "2025 constant CNY",
            "2022 CNY x 1.004004 CPI",
        )

    storage = pd.read_csv(
        NATIONAL_MODEL / "data" / "technology" / "storage_technical_parameters.csv"
    )
    for row in storage.itertuples(index=False):
        for name, unit in (
            ("charge_efficiency", "fraction"),
            ("discharge_efficiency", "fraction"),
            ("round_trip_efficiency", "fraction"),
            ("duration_h", "h"),
            ("lifetime_years", "year"),
            ("fixed_om_fraction_capex_per_year", "fraction/year"),
        ):
            value = float(getattr(row, name))
            add(
                "storage",
                f"{row.technology}.{name}",
                value,
                value,
                unit,
                "physical parameter",
                "retain current value; duration/site classes remain sensitivity",
            )
        add(
            "storage",
            f"{row.technology}.variable_om",
            float(row.variable_om_yuan_per_mwh),
            float(row.variable_om_yuan_per_mwh) * CPI_2022_2025,
            "2025 CNY/MWh",
            "2025 constant CNY",
            "2022 CNY x 1.004004 CPI",
        )

    ccs = pd.read_csv(
        NATIONAL_MODEL / "data" / "technology" / "ccs_cost_parameters.csv"
    ).iloc[0]
    add(
        "ccs",
        "capture_cost",
        float(ccs.capture_yuan_per_tco2),
        float(ccs.capture_yuan_per_tco2) * CPI_2022_2025,
        "2025 CNY/tCO2",
        "2025 constant CNY",
        "retain CISPO cost because An et al. reports retrofit CAPEX, not CNY/t capture",
    )
    add(
        "ccs",
        "transport_cost",
        float(ccs.transport_yuan_per_tco2_km),
        0.026 * USD_CNY_2025,
        "2025 CNY/tCO2/km",
        "2025 FX conversion",
        "An et al. (2025) central value 0.026 USD/tCO2/km",
    )
    add(
        "ccs",
        "storage_cost",
        float(ccs.storage_yuan_per_tco2),
        5.0 * USD_CNY_2025,
        "2025 CNY/tCO2",
        "2025 FX conversion",
        "An et al. (2025) central value 5 USD/tCO2",
    )

    config = json.loads(
        (NATIONAL_MODEL / "config" / "optimization_2030.json").read_text(
            encoding="utf-8"
        )
    )
    wacc = float(config["finance"]["real_wacc_fraction"])
    add(
        "finance",
        "real_wacc_fraction",
        wacc,
        wacc,
        "fraction",
        "real rate",
        "retain 7.4%; modern nominal international-financier data are not directly comparable",
    )
    for technology, lifetime in config["finance"]["default_lifetime_years"].items():
        add(
            "finance",
            f"{technology}.lifetime",
            float(lifetime),
            float(lifetime),
            "year",
            "physical parameter",
            "retain current value; existing-fleet lifetime tested separately",
        )

    for name in (
        "ramping_cost_yuan_per_mwh",
        "nuclear_fuel_yuan_per_mwh",
    ):
        active = float(config["thermal"][name])
        add(
            "thermal_system",
            name,
            active,
            active * CPI_2022_2025,
            "2025 CNY/MWh",
            "2025 constant CNY",
            "2022 CNY x 1.004004 CPI",
        )

    wave = config["wave_energy"]
    for year, value in wave["capex_eur_per_kw_by_year"].items():
        add(
            "wave_optional_only",
            f"capex_{year}",
            float(value) * float(wave["eur_to_cny"]),
            float(value) * EUR_CNY_2025,
            "2025 CNY/kW",
            "2025 FX conversion",
            "sensitivity only; recommend changing the current wave-enabled Base to a wave-disabled reference",
        )

    out = pd.DataFrame(rows)
    write_csv(out, CANDIDATE / "other_parameter_values_2025_candidate.csv")
    return out


def build_review_matrix() -> pd.DataFrame:
    rows = [
        {
            "parameter_family": "VRE CapEx",
            "current_model_value": "2030: onwind 5500; offwind 9800; UPV 2250; DPV 2650 CNY/kW",
            "latest_research_report_policy": "IRENA 2024 global TIC: onwind 1041, offwind 2852, PV 691 USD/kW; China-specific CISPO anchors remain lower",
            "comparability_and_reliability": "Global commissioned-project benchmark is not a China replacement; current China values are internally coherent. Offshore national scalar omits depth, distance and wakes.",
            "proposed_final_baseline": "current trajectory x 1.004004 CPI to 2025 CNY",
            "decision": "KEEP_AND_REBASE",
            "sensitivity_priority": "HIGH_OFFWIND; MEDIUM_OTHER_VRE",
            "source": "CISPO EES 2025; IRENA Renewable Power Generation Costs in 2024; doi:10.1038/s41597-025-04428-8; doi:10.1038/s41467-026-68655-2",
        },
        {
            "parameter_family": "Coal/gas/biomass/nuclear/hydro CapEx and O&M",
            "current_model_value": "19 technologies x 2030/2040/2050/2060; CISPO figure-digitized trajectories",
            "latest_research_report_policy": "CISPO EES 2025 remains the most directly compatible China-system source; recent global reports are cross-checks only",
            "comparability_and_reliability": "Compatible model definitions but digitization error is not quantified",
            "proposed_final_baseline": "current monetary values x 1.004004 CPI",
            "decision": "KEEP_AND_REBASE",
            "sensitivity_priority": "MEDIUM; HIGH_NUCLEAR_AND_CCS",
            "source": "doi:10.1039/D5EE00355E",
        },
        {
            "parameter_family": "Provincial fuel prices",
            "current_model_value": "An et al. Table S2 USD/GJ x 6.9 CNY/USD, constant to 2060",
            "latest_research_report_policy": "Coal inferred to 2023; gas constructed from 2018 benchmark gate price +0.8 CNY/m3; biomass from Yuan et al. 2022",
            "comparability_and_reliability": "High spatial provenance; medium temporal reliability. These are constructed planning prices, not 2025 spot observations.",
            "proposed_final_baseline": "published USD/GJ x 7.1429 official 2025 average FX, constant to 2060",
            "decision": "CORRECT_PROVENANCE_AND_FX",
            "sensitivity_priority": "VERY_HIGH",
            "source": "doi:10.1038/s41467-025-57559-2; doi:10.5281/zenodo.14836760",
        },
        {
            "parameter_family": "Coal flexibility",
            "current_model_value": "pmin 0.40; min up/down 8/8 h; ramp 0.25/h",
            "latest_research_report_policy": "An et al. explicitly tests coal pmin 0.30 and 0.50 around the central case",
            "comparability_and_reliability": "Directly comparable continuous-RUC parameter",
            "proposed_final_baseline": "retain pmin 0.40 and current RUC values",
            "decision": "KEEP",
            "sensitivity_priority": "HIGH",
            "source": "doi:10.1039/D5EE00355E; doi:10.1038/s41467-025-57559-2",
        },
        {
            "parameter_family": "CCS capture fraction and energy penalty",
            "current_model_value": "capture 90%; 5% net-output loss plus technology-specific heat rate",
            "latest_research_report_policy": "An et al.: 90% capture; 2025 energy penalty coal 24.4%, gas 18.3%, biomass 51.3%, declining over time",
            "comparability_and_reliability": "Capture is aligned. Current effective net penalties combine heat-rate and output-loss terms and differ by fuel.",
            "proposed_final_baseline": "retain 90% capture and CISPO effective penalties pending formula-consistent recoding",
            "decision": "KEEP_WITH_STRUCTURAL_REVIEW",
            "sensitivity_priority": "VERY_HIGH",
            "source": "doi:10.1038/s41467-025-57559-2",
        },
        {
            "parameter_family": "CCS transport and storage cost",
            "current_model_value": "0.8 CNY/tCO2/km; 116 CNY/tCO2",
            "latest_research_report_policy": "An et al. central 0.026 USD/tCO2/km and 5 USD/tCO2; ranges 0.020-0.036 and 3-8.5",
            "comparability_and_reliability": "Directly comparable units and China-system application",
            "proposed_final_baseline": "0.1857 CNY/tCO2/km and 35.7145 CNY/tCO2 at 2025 FX",
            "decision": "CHANGE_RECOMMENDED_REQUIRES_APPROVAL",
            "sensitivity_priority": "HIGH",
            "source": "doi:10.1038/s41467-025-57559-2",
        },
        {
            "parameter_family": "Battery storage",
            "current_model_value": "4 h; eta_ch=eta_dis=0.95; RTE=0.9025; 15 y; 2030 CapEx 3300 CNY/kW",
            "latest_research_report_policy": "NREL 2025 4 h: 2035 low/mid/high 152/247/349 USD/kWh; 2050 111/184/333; IRENA 2024 global commissioned average 192 USD/kWh; NEA reports 2024 China EPC -25% and system bids -44% y/y",
            "comparability_and_reliability": "Efficiency is reasonable; current 2030 energy-equivalent 825 CNY/kWh is aggressive versus global benchmarks but plausible for China. Power-only CapEx with fixed duration cannot represent duration substitution.",
            "proposed_final_baseline": "retain 4 h technical values; CapEx x 1.004004 CPI",
            "decision": "KEEP_BASELINE; POWER_ENERGY_SPLIT_REQUIRES_CODE_CHANGE",
            "sensitivity_priority": "VERY_HIGH",
            "source": "NREL Cost Projections for Utility-Scale Battery Storage: 2025 Update; IRENA 2024 costs; NEA China New Energy Storage Development Report 2025",
        },
        {
            "parameter_family": "Pumped-storage hydropower",
            "current_model_value": "8 h; eta_ch=eta_dis=0.88; RTE=77.44%; 40 y; 2030 CapEx 5260 CNY/kW",
            "latest_research_report_policy": "NREL 2024 central RTE around 80%, literature/resource range about 70-87%; 8/10/12 h site designs and strongly site-specific cost",
            "comparability_and_reliability": "Efficiency is well supported; nationwide fixed duration and CapEx are simplified",
            "proposed_final_baseline": "retain technical values; CapEx x 1.004004 CPI",
            "decision": "KEEP_BASELINE",
            "sensitivity_priority": "HIGH",
            "source": "NREL 2024 ATB Pumped Storage Hydropower and PSH Cost Model",
        },
        {
            "parameter_family": "Real WACC",
            "current_model_value": "uniform 7.4% real",
            "latest_research_report_policy": "2025 dataset for China reports nominal 2025 WACC 8.4-9.4% across covered technologies; IEA commonly uses real 4-9% ranges",
            "comparability_and_reliability": "Dataset is international-commercial-financier nominal WACC and excludes nuclear/battery; not directly interchangeable with a domestic real rate",
            "proposed_final_baseline": "retain 7.4% real",
            "decision": "KEEP_AFTER_REVIEW",
            "sensitivity_priority": "VERY_HIGH",
            "source": "doi:10.1038/s41597-025-06177-0; doi:10.5281/zenodo.17076925",
        },
        {
            "parameter_family": "Wave energy",
            "current_model_value": "current Base enables wave; 2030/2040/2050 2777/2012/1731 EUR/kW; potential_fraction=1",
            "latest_research_report_policy": "Applied Energy 2024 is an optimistic learning case; present commercial LCOE evidence remains much higher and heterogeneous",
            "comparability_and_reliability": "Low maturity and strong site/device dependence",
            "proposed_final_baseline": "change final reference to disabled; sensitivity costs converted at 8.1185 CNY/EUR",
            "decision": "EXCLUDE_FROM_REFERENCE",
            "sensitivity_priority": "MANDATORY_IF_ENABLED",
            "source": "doi:10.1016/j.apenergy.2024.123119",
        },
        {
            "parameter_family": "Objective cost accounting",
            "current_model_value": "CapEx x CRF and FOM charged on all in-service capacity in each planning snapshot",
            "latest_research_report_policy": "Planning-investment models normally distinguish sunk existing capacity from new investment cash flow",
            "comparability_and_reliability": "This is a structural equation issue, not a scalar input",
            "proposed_final_baseline": "no silent change in this candidate package; disclose explicitly",
            "decision": "MODEL_CODE_REVIEW_REQUIRED",
            "sensitivity_priority": "CRITICAL_BEFORE_FINAL_SOLVES",
            "source": "live cispo_model/master.py and monolithic.py audit",
        },
    ]
    out = pd.DataFrame(rows)
    write_csv(out, TABLES / "table_m04_11_parameter_evidence_and_decisions.csv")
    return out


def build_final_summary(
    capex: pd.DataFrame, fuel: pd.DataFrame, other: pd.DataFrame
) -> pd.DataFrame:
    get_capex = capex.set_index(["technology", "year"])["capex_yuan_per_kw"]
    fuel_rows = []
    for name in ("coal", "gas", "biomass"):
        values = pd.to_numeric(fuel[f"{name}_yuan_per_gj"], errors="coerce")
        fuel_rows.append(
            {
                "section": "fuel",
                "parameter": f"{name}_provincial_price",
                "candidate_final_value": (
                    f"median {values.median():.3f}; range "
                    f"{values.min():.3f}-{values.max():.3f}"
                ),
                "unit": "2025 CNY/GJ",
                "implementation_file": "candidate_inputs/province_fuel_prices_2025_candidate.csv",
                "decision": "CHANGE_RECOMMENDED_REQUIRES_APPROVAL",
            }
        )
    selected = [
        ("onwind_capex_2030", get_capex.loc[("onwind", 2030)], "2025 CNY/kW"),
        ("offwind_capex_2030", get_capex.loc[("offwind", 2030)], "2025 CNY/kW"),
        ("upv_capex_2030", get_capex.loc[("upv", 2030)], "2025 CNY/kW"),
        ("dpv_capex_2030", get_capex.loc[("dpv", 2030)], "2025 CNY/kW"),
        ("battery_capex_2030_4h", get_capex.loc[("battery", 2030)], "2025 CNY/kW"),
        ("phs_capex_2030_8h", get_capex.loc[("phs", 2030)], "2025 CNY/kW"),
        ("nuclear_capex_2030", get_capex.loc[("nuclear", 2030)], "2025 CNY/kW"),
        ("hydro_capex_2030", get_capex.loc[("hydro", 2030)], "2025 CNY/kW"),
    ]
    rows = [
        {
            "section": "capex",
            "parameter": name,
            "candidate_final_value": f"{value:.3f}",
            "unit": unit,
            "implementation_file": "candidate_inputs/technology_capex_by_year_2025_candidate.csv",
            "decision": "KEEP_AND_REBASE",
        }
        for name, value, unit in selected
    ]
    rows.extend(fuel_rows)
    for parameter in (
        "real_wacc_fraction",
        "capture_cost",
        "transport_cost",
        "storage_cost",
        "battery.duration_h",
        "battery.round_trip_efficiency",
        "phs.duration_h",
        "phs.round_trip_efficiency",
    ):
        match = other.loc[other["parameter"].eq(parameter)]
        if match.empty:
            continue
        item = match.iloc[0]
        rows.append(
            {
                "section": str(item.parameter_family),
                "parameter": parameter,
                "candidate_final_value": f"{float(item.candidate_final_value):.6g}",
                "unit": str(item.unit),
                "implementation_file": "candidate_inputs/other_parameter_values_2025_candidate.csv",
                "decision": (
                    "CHANGE_RECOMMENDED_REQUIRES_APPROVAL"
                    if parameter in ("transport_cost", "storage_cost")
                    else "KEEP_AFTER_REVIEW"
                ),
            }
        )
    rows.append(
        {
            "section": "wave",
            "parameter": "reference_case_enabled",
            "candidate_final_value": "false",
            "unit": "boolean",
            "implementation_file": "scenario boundary",
            "decision": "CHANGE_RECOMMENDED_REQUIRES_APPROVAL",
        }
    )
    out = pd.DataFrame(rows)
    write_csv(out, TABLES / "table_m04_12_final_candidate_value_summary.csv")
    return out


def build_sensitivity_register() -> pd.DataFrame:
    rows = [
        ("fuel", "coal price", "candidate provincial table", "0.8x / 1.0x / 1.2x; paper high path +5% each 5 y", "VERY_HIGH", "scalar or trajectory"),
        ("fuel", "gas price", "candidate provincial table", "0.8x / 1.0x / 1.2x; paper low path -5% each 5 y", "VERY_HIGH", "scalar or trajectory"),
        ("fuel", "biomass price", "candidate provincial table", "0.8x / 1.0x / 1.2x", "HIGH", "scalar"),
        ("finance", "real WACC", "7.4%", "4% / 7.4% / 9%", "VERY_HIGH", "scalar"),
        ("coal flexibility", "pmin", "0.40", "0.30 / 0.40 / 0.50", "HIGH", "scalar"),
        ("existing fleet", "retirement lifetime", "40 y", "30 / 40 / 50 y", "HIGH", "cohort reconstruction"),
        ("battery", "duration", "4 h", "2 / 4 / 8 / 12 h", "VERY_HIGH", "requires power-energy cost split"),
        ("battery", "4 h energy cost", "candidate CISPO trajectory", "NREL 2025 low / mid / high", "VERY_HIGH", "scenario table"),
        ("pumped hydro", "RTE", "77.44%", "70% / 80% / 87%", "HIGH", "efficiency pair"),
        ("pumped hydro", "duration", "8 h", "8 / 12 / 24 h", "HIGH", "duration and site class"),
        ("offshore wind", "spatial CapEx", "national scalar", "depth-distance/wake low / central / high", "VERY_HIGH", "grid-specific overlay"),
        ("nuclear", "CapEx and pmin", "candidate trajectory; pmin 0.85", "CapEx +/-30%; pmin 0.70 / 0.85 / 0.90", "HIGH", "two-factor"),
        ("CCS", "energy penalty", "CISPO heat rate + 5% output loss", "An et al. fuel-specific 2025-2060 paths", "VERY_HIGH", "formula-consistent recoding"),
        ("CCS", "transport cost", "0.1857 CNY/t/km candidate", "0.1429 / 0.1857 / 0.2571", "HIGH", "0.020/0.026/0.036 USD at 2025 FX"),
        ("CCS", "storage cost", "35.7145 CNY/t candidate", "21.4287 / 35.7145 / 60.7147", "HIGH", "3/5/8.5 USD at 2025 FX"),
        ("DAC", "monetary costs", "candidate CPI-rebased table", "0.5x / 1.0x / 1.5x", "VERY_HIGH", "scenario table"),
        ("wave optional", "potential and cost", "reference disabled", "potential 0.01/0.05/0.20/1.00; commercial-cost case", "MANDATORY_IF_ENABLED", "independent scenario"),
        ("objective accounting", "existing-capacity CapEx charging", "charged in current model", "current / sunk-existing-capacity treatment", "CRITICAL", "requires model code review"),
    ]
    out = pd.DataFrame(
        rows,
        columns=[
            "parameter_family",
            "parameter",
            "candidate_baseline",
            "future_sensitivity_values",
            "priority",
            "implementation_note",
        ],
    )
    write_csv(out, TABLES / "table_m04_13_sensitivity_priority_register.csv")
    return out


def build_change_map() -> pd.DataFrame:
    rows = [
        (
            "technology CapEx and absolute O&M",
            "all current 2022-basis values",
            "multiply by 1.004004",
            "candidate_inputs/technology_capex_by_year_2025_candidate.csv; candidate_inputs/other_parameter_values_2025_candidate.csv",
            "APPROVAL_REQUIRED_DATA_UPDATE",
        ),
        (
            "provincial fuel price and derived generation cost",
            "Table S2 x 6.9; provenance label incomplete",
            "Table S2 x 7.1429; exact article/price construction recorded",
            "candidate_inputs/province_fuel_prices_2025_candidate.csv; candidate_inputs/province_fuel_generation_cost_by_year_2025_candidate.csv",
            "APPROVAL_REQUIRED_DATA_UPDATE",
        ),
        (
            "CCS transport and storage",
            "0.8 CNY/t/km; 116 CNY/t",
            "0.1857 CNY/t/km; 35.7145 CNY/t",
            "candidate_inputs/other_parameter_values_2025_candidate.csv",
            "APPROVAL_REQUIRED_DATA_UPDATE",
        ),
        (
            "battery cost representation",
            "single CNY/kW CapEx and fixed 4 h",
            "retain for candidate baseline; later split cP*Kp + cE*Ke",
            "model formulation",
            "CODE_CHANGE_REQUIRES_SEPARATE_APPROVAL",
        ),
        (
            "objective investment accounting",
            "annualized CapEx charged to all in-service capacity",
            "disclose now; review sunk-existing-capacity treatment before final solves",
            "cispo_model/master.py; cispo_model/monolithic.py",
            "CODE_CHANGE_REQUIRES_SEPARATE_APPROVAL",
        ),
        (
            "wave",
            "current Base has features.wave_energy=true",
            "change final reference to disabled; 2025 FX only in independent sensitivity",
            "scenario overlay",
            "BASE_SCENARIO_CHANGE_REQUIRES_APPROVAL",
        ),
    ]
    out = pd.DataFrame(
        rows,
        columns=[
            "parameter_family",
            "current_state",
            "proposed_state",
            "candidate_or_model_location",
            "authorization_status",
        ],
    )
    write_csv(out, TABLES / "table_m04_14_proposed_change_map.csv")
    return out


def build_candidate_manifest() -> pd.DataFrame:
    roles = {
        "technology_capex_by_year_2025_candidate.csv": "19 technologies x four planning years, 2025-CNY CapEx",
        "province_fuel_prices_2025_candidate.csv": "31-province published fuel prices converted at 2025 FX",
        "province_fuel_generation_cost_by_year_2025_candidate.csv": "derived province-year-technology fuel cost",
        "other_parameter_values_2025_candidate.csv": "RUC, O&M, storage, finance, CCS and wave candidate values",
    }
    rows = []
    for name, role in roles.items():
        path = CANDIDATE / name
        rows.append(
            {
                "candidate_file": f"candidate_inputs/{name}",
                "role": role,
                "row_count": len(pd.read_csv(path)),
                "sha256": sha256(path),
                "implementation_status": "PROPOSED_NOT_APPLIED",
                "production_input_modified": False,
            }
        )
    out = pd.DataFrame(rows)
    write_csv(out, TABLES / "table_m04_15_candidate_input_manifest.csv")
    return out


def plot_vre(capex: pd.DataFrame) -> None:
    data = capex.loc[capex["technology"].isin(["onwind", "offwind", "upv", "dpv"])].copy()
    write_csv(
        data[["technology", "year", "active_capex_yuan_per_kw", "capex_yuan_per_kw"]],
        FIGURE_DATA / "figure_m04_03_vre_cost_trajectories.csv",
    )
    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH_IN, 3.35))
    for technology in ("offwind", "onwind", "dpv", "upv"):
        subset = data.loc[data["technology"].eq(technology)].sort_values("year")
        ax.plot(
            subset["year"],
            subset["capex_yuan_per_kw"],
            marker="o",
            ms=3.4,
            lw=1.5,
            color=COLORS[technology],
            label=LABELS[technology],
        )
        last = subset.iloc[-1]
        ax.annotate(
            LABELS[technology],
            (last["year"], last["capex_yuan_per_kw"]),
            xytext=(5, 0),
            textcoords="offset points",
            va="center",
            fontsize=6.6,
            color=COLORS[technology],
        )
    ax.set_xlim(2028, 2067)
    ax.set_xticks([2030, 2040, 2050, 2060])
    ax.set_ylabel("CapEx (2025 CNY kW$^{-1}$)")
    ax.set_xlabel("Planning year")
    ax.set_title("Wind and solar investment-cost assumptions")
    ax.grid(axis="y", lw=0.35, alpha=0.35)
    ax.margins(y=0.12)
    fig.subplots_adjust(left=0.10, right=0.84, bottom=0.18, top=0.90)
    save_figure(fig, "Figure_M04_03_vre_cost_trajectories")


def plot_dispatchable(capex: pd.DataFrame) -> None:
    technologies = [
        "coal",
        "coalccs",
        "gas",
        "gasccs",
        "bio",
        "bioccs",
        "nuclear",
        "hydro",
    ]
    data = capex.loc[capex["technology"].isin(technologies)].copy()
    write_csv(
        data[["technology", "year", "active_capex_yuan_per_kw", "capex_yuan_per_kw"]],
        FIGURE_DATA / "figure_m04_04_dispatchable_cost_trajectories.csv",
    )
    fig, axes = plt.subplots(1, 2, figsize=(FIGURE_WIDTH_IN, 3.6))
    panels = [
        (axes[0], ["coal", "coalccs", "gas", "gasccs"], "Fossil generation"),
        (axes[1], ["bio", "bioccs", "nuclear", "hydro"], "Firm low-carbon generation"),
    ]
    for ax, members, title in panels:
        for technology in members:
            subset = data.loc[data["technology"].eq(technology)].sort_values("year")
            ax.plot(
                subset["year"],
                subset["capex_yuan_per_kw"],
                marker="o",
                ms=2.8,
                lw=1.25,
                color=COLORS[technology],
                label=LABELS[technology],
            )
        ax.set_xticks([2030, 2040, 2050, 2060])
        ax.set_xlabel("Planning year")
        ax.set_title(title)
        ax.grid(axis="y", lw=0.35, alpha=0.35)
    axes[0].set_ylabel("CapEx (2025 CNY kW$^{-1}$)")
    axes[0].legend(
        loc="upper center", bbox_to_anchor=(0.5, -0.20), ncol=2, fontsize=5.8
    )
    axes[1].legend(
        loc="upper center", bbox_to_anchor=(0.5, -0.20), ncol=2, fontsize=5.8
    )
    fig.subplots_adjust(left=0.09, right=0.98, bottom=0.30, top=0.88, wspace=0.27)
    save_figure(fig, "Figure_M04_04_dispatchable_cost_trajectories")


def plot_storage_benchmark(capex: pd.DataFrame) -> None:
    storage = capex.loc[capex["technology"].isin(["battery", "phs"])].copy()
    battery = storage.loc[storage["technology"].eq("battery")].sort_values("year")
    battery = battery.assign(cny_per_kwh=battery["capex_yuan_per_kw"] / 4.0)
    nrel = pd.DataFrame(
        {
            "year": [2035, 2035, 2035, 2050, 2050, 2050],
            "case": ["Low", "Mid", "High", "Low", "Mid", "High"],
            "usd_per_kwh": [152, 247, 349, 111, 184, 333],
        }
    )
    nrel["cny_per_kwh"] = nrel["usd_per_kwh"] * USD_CNY_2025
    figure_data = pd.concat(
        [
            battery[["year", "cny_per_kwh"]].assign(series="CISPO candidate"),
            nrel[["year", "cny_per_kwh", "case"]]
            .assign(series=lambda x: "NREL 2025 " + x["case"])
            .drop(columns="case"),
            pd.DataFrame(
                {"year": [2024], "cny_per_kwh": [192 * USD_CNY_2025], "series": ["IRENA 2024"]}
            ),
        ],
        ignore_index=True,
    )
    figure_data["metric"] = "battery_cost"
    figure_data = pd.concat(
        [
            figure_data,
            pd.DataFrame(
                {
                    "year": [np.nan, np.nan, np.nan],
                    "cny_per_kwh": [np.nan, np.nan, np.nan],
                    "series": [
                        "CISPO PHS RTE",
                        "NREL/literature RTE low",
                        "NREL/literature RTE high",
                    ],
                    "metric": ["phs_rte", "phs_rte", "phs_rte"],
                    "value_percent": [77.44, 70.0, 87.0],
                }
            ),
        ],
        ignore_index=True,
    )
    write_csv(figure_data, FIGURE_DATA / "figure_m04_05_storage_cost_benchmarks.csv")

    fig, axes = plt.subplots(1, 2, figsize=(FIGURE_WIDTH_IN, 3.3))
    ax = axes[0]
    ax.plot(
        battery["year"],
        battery["cny_per_kwh"],
        color=COLORS["battery"],
        marker="o",
        lw=1.5,
        ms=3.2,
        label="CISPO candidate (China, 4 h)",
    )
    scenario_colors = {"Low": "#3B8C6E", "Mid": "#6E6E6E", "High": "#A6761D"}
    for case in ("Low", "Mid", "High"):
        subset = nrel.loc[nrel["case"].eq(case)]
        ax.plot(
            subset["year"],
            subset["cny_per_kwh"],
            marker="s",
            ms=3.0,
            lw=1.0,
            ls="--",
            color=scenario_colors[case],
            label=f"NREL {case}",
        )
    ax.scatter(
        [2024],
        [192 * USD_CNY_2025],
        marker="D",
        s=18,
        color="#222222",
        label="IRENA 2024 global",
        zorder=4,
    )
    ax.set_title("Battery: energy-equivalent cost")
    ax.set_ylabel("Cost (2025 CNY kWh$^{-1}$)")
    ax.set_xlabel("Year")
    ax.set_ylim(500, 2750)
    ax.grid(axis="y", lw=0.35, alpha=0.35)
    ax.legend(loc="upper right", fontsize=5.7)

    ax = axes[1]
    ax.axvspan(70, 87, color="#A6C8E3", alpha=0.30)
    ax.axvline(80, color="#4F86C6", lw=1.2, ls="--")
    ax.scatter(
        [77.44],
        [0],
        color=COLORS["phs"],
        s=40,
        zorder=4,
    )
    ax.annotate(
        "CISPO 77.44%",
        (77.44, 0),
        xytext=(6, 0),
        textcoords="offset points",
        va="center",
        fontsize=6.5,
        color=COLORS["phs"],
    )
    ax.text(
        0.04,
        0.93,
        "NREL/literature RTE: 70–87%\nRepresentative central: ~80%\n"
        "CISPO duration: 8 h\nSite designs: 8/10/12 h",
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=6.5,
        bbox={"boxstyle": "round,pad=0.35", "fc": "#F4F6F8", "ec": "none"},
    )
    ax.set_title("Pumped hydro: technical assumptions")
    ax.set_xlabel("Round-trip efficiency (%)")
    ax.set_xlim(66, 91)
    ax.set_ylim(-0.6, 0.6)
    ax.set_yticks([])
    ax.grid(axis="x", lw=0.35, alpha=0.35)
    fig.subplots_adjust(left=0.09, right=0.98, bottom=0.18, top=0.88, wspace=0.30)
    save_figure(fig, "Figure_M04_05_storage_cost_benchmarks")


def plot_review_decisions(review: pd.DataFrame) -> None:
    map_value = {
        "KEEP": 0,
        "KEEP_AFTER_REVIEW": 0,
        "KEEP_BASELINE": 0,
        "KEEP_AND_REBASE": 1,
        "CORRECT_PROVENANCE_AND_FX": 2,
        "CHANGE_RECOMMENDED_REQUIRES_APPROVAL": 3,
        "KEEP_WITH_STRUCTURAL_REVIEW": 4,
        "KEEP_BASELINE; POWER_ENERGY_SPLIT_REQUIRES_CODE_CHANGE": 4,
        "MODEL_CODE_REVIEW_REQUIRED": 4,
        "EXCLUDE_FROM_REFERENCE": 5,
    }
    labels = {
        0: "Keep",
        1: "2025 rebase",
        2: "Provenance / FX correction",
        3: "Input change proposed",
        4: "Structural review",
        5: "Exclude from reference",
    }
    colors = {
        0: "#6B8E6B",
        1: "#4F86C6",
        2: "#D4A72C",
        3: "#D97745",
        4: "#B44C43",
        5: "#5B5B5B",
    }
    plot = review.copy()
    plot["decision_code"] = plot["decision"].map(map_value)
    plot["short_family"] = [
        "VRE CapEx",
        "Firm/thermal CapEx",
        "Fuel prices",
        "Coal flexibility",
        "CCS capture/penalty",
        "CCS transport/storage",
        "Battery",
        "Pumped hydro",
        "WACC",
        "Wave",
        "Cost accounting",
    ]
    write_csv(
        plot[["short_family", "decision", "sensitivity_priority", "decision_code"]],
        FIGURE_DATA / "figure_m04_06_parameter_review_decisions.csv",
    )
    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH_IN, 3.8))
    y = np.arange(len(plot))
    for code in sorted(plot["decision_code"].unique()):
        subset = plot.loc[plot["decision_code"].eq(code)]
        ax.scatter(
            subset["decision_code"],
            subset.index,
            s=34,
            color=colors[int(code)],
            label=labels[int(code)],
            zorder=3,
        )
    ax.set_yticks(y)
    ax.set_yticklabels(plot["short_family"])
    ax.set_xticks(sorted(labels))
    ax.set_xticklabels([labels[i] for i in sorted(labels)], rotation=20, ha="right")
    ax.set_ylim(len(plot) - 0.5, -0.5)
    ax.grid(axis="x", lw=0.35, alpha=0.35)
    ax.set_title("Disposition of reviewed model inputs")
    ax.set_xlabel("Candidate-baseline decision")
    ax.set_xlim(-0.4, 5.4)
    fig.subplots_adjust(left=0.23, right=0.98, bottom=0.27, top=0.90)
    save_figure(fig, "Figure_M04_06_parameter_review_decisions")


def build_qa() -> pd.DataFrame:
    checks: list[dict[str, object]] = []

    def add(name: str, passed: bool, observed: object, expected: object) -> None:
        checks.append(
            {
                "check": name,
                "status": "PASS" if passed else "FAIL",
                "observed": observed,
                "expected": expected,
            }
        )

    capex = pd.read_csv(CANDIDATE / "technology_capex_by_year_2025_candidate.csv")
    fuel = pd.read_csv(CANDIDATE / "province_fuel_prices_2025_candidate.csv")
    fuel_cost = pd.read_csv(
        CANDIDATE / "province_fuel_generation_cost_by_year_2025_candidate.csv"
    )
    add("candidate_capex_rows", len(capex) == 76, len(capex), 76)
    add("candidate_fuel_rows", len(fuel) == 31, len(fuel), 31)
    add("candidate_fuel_cost_rows", len(fuel_cost) == 1550, len(fuel_cost), 1550)
    add(
        "candidate_capex_factor",
        np.allclose(
            capex["capex_yuan_per_kw"],
            capex["active_capex_yuan_per_kw"] * CPI_2022_2025,
        ),
        float(
            (
                capex["capex_yuan_per_kw"]
                / capex["active_capex_yuan_per_kw"]
            ).median()
        ),
        CPI_2022_2025,
    )
    valid_fuel = fuel_cost["fuel_price_yuan_per_gj"].notna()
    add(
        "fuel_cost_identity",
        np.allclose(
            fuel_cost.loc[valid_fuel, "fuel_cost_yuan_per_mwh"],
            fuel_cost.loc[valid_fuel, "fuel_price_yuan_per_gj"]
            * fuel_cost.loc[valid_fuel, "fuel_load_gj_per_mwh"],
        ),
        "all finite rows",
        "price x heat rate",
    )
    add(
        "fuel_fx",
        np.isclose(float(fuel["usd_to_yuan"].unique()[0]), USD_CNY_2025),
        float(fuel["usd_to_yuan"].unique()[0]),
        USD_CNY_2025,
    )
    add(
        "reference_wave_disabled_decision",
        pd.read_csv(TABLES / "table_m04_12_final_candidate_value_summary.csv")
        .query("parameter == 'reference_case_enabled'")["candidate_final_value"]
        .iloc[0]
        == "false",
        "false",
        "false",
    )
    for stem in (
        "Figure_M04_03_vre_cost_trajectories",
        "Figure_M04_04_dispatchable_cost_trajectories",
        "Figure_M04_05_storage_cost_benchmarks",
        "Figure_M04_06_parameter_review_decisions",
    ):
        png = FIGURES / f"{stem}.png"
        pdf = FIGURES / f"{stem}.pdf"
        with Image.open(png) as image:
            width, height = image.size
        add(f"{stem}_png_width", 3100 <= width <= 3200, width, "3100-3200 px")
        add(f"{stem}_png_height", height >= 1400, height, ">=1400 px")
        add(
            f"{stem}_pdf_exists",
            pdf.exists() and pdf.stat().st_size > 0,
            pdf.stat().st_size if pdf.exists() else 0,
            ">0 bytes",
        )
    out = pd.DataFrame(checks)
    write_csv(out, QA / "final_candidate_validation.csv")
    return out


def main() -> None:
    ensure_dirs()
    configure_style()
    capex = build_candidate_capex()
    fuel, _ = build_candidate_fuel()
    other = build_candidate_other_costs()
    review = build_review_matrix()
    build_final_summary(capex, fuel, other)
    build_sensitivity_register()
    build_change_map()
    build_candidate_manifest()
    plot_vre(capex)
    plot_dispatchable(capex)
    plot_storage_benchmark(capex)
    plot_review_decisions(review)
    qa = build_qa()
    summary = {
        "module": "04_thermal_nuclear_storage_technoeconomics",
        "package": "final_candidate_review",
        "generated_at": "2026-07-28",
        "production_inputs_modified": False,
        "candidate_price_basis": "2025 constant CNY",
        "candidate_input_files": len(list(CANDIDATE.glob("*.csv"))),
        "new_review_tables": 5,
        "new_figures": 4,
        "qa_pass": int(qa["status"].eq("PASS").sum()),
        "qa_fail": int(qa["status"].eq("FAIL").sum()),
        "terminal_marker": (
            "FINAL_M04_CANDIDATE_INPUT_REVIEW_PASS"
            if not qa["status"].eq("FAIL").any()
            else "M04_CANDIDATE_QA_FAIL"
        ),
    }
    (QA / "final_candidate_run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if qa["status"].eq("FAIL").any():
        raise RuntimeError(
            "Candidate QA failed:\n"
            + qa.loc[qa["status"].eq("FAIL")].to_string(index=False)
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
