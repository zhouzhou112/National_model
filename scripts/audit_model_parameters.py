"""Export a machine-readable runtime parameter catalog and deterministic QC report."""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cispo_model.config import load_model_config


TABLES = {
    "capex": ("technology/technology_capex_by_year.csv", ["technology", "year"]),
    "ruc": ("technology/thermal_nuclear_ruc_parameters.csv", ["technology"]),
    "om": ("technology/thermal_nuclear_om_parameters.csv", ["technology"]),
    "storage": ("technology/storage_technical_parameters.csv", ["technology"]),
    "fuel": (
        "technology/province_fuel_generation_cost_by_year.csv",
        ["province_code", "year", "technology"],
    ),
    "emissions": ("technology/emission_factors_by_year.csv", ["technology", "year"]),
    "dac": ("technology/dac_parameters_by_year.csv", ["technology", "year"]),
    "ccs": ("technology/ccs_cost_parameters.csv", []),
}

REQUIRED_REGISTRY_ROWS = {
    ("scope", "scientific_case"),
    ("scope", "hybrid_weather_bundle"),
    ("scope", "weather_year"),
    ("vre", "existing_retirement_mode"),
    ("vre", "existing_capacity_cohorts"),
    ("carbon", "beccs_mass_balance"),
    ("carbon", "beccs_lifecycle_sensitivity"),
}

UNIT_BY_FIELD = {
    "capex_yuan_per_kw": "CNY/kW",
    "fixed_om_fraction_capex_per_year": "fraction/year",
    "variable_om_yuan_per_mwh": "CNY/MWh",
    "fuel_price_yuan_per_gj": "CNY/GJ",
    "fuel_load_gj_per_mwh": "GJ/MWh",
    "fuel_cost_yuan_per_mwh": "CNY/MWh",
    "lifetime_years": "year",
    "duration_h": "hour",
    "min_up_h": "hour",
    "min_down_h": "hour",
    "startup_yuan_per_mw": "CNY/MW",
    "shutdown_yuan_per_mw": "CNY/MW",
    "inertia_s": "second",
    "emission_factor_kgco2_per_kwh": "kgCO2/kWh",
    "emission_factor_mtco2_per_gwh": "MtCO2/GWh",
    "capture_yuan_per_tco2": "CNY/tCO2",
    "transport_yuan_per_tco2_km": "CNY/(tCO2 km)",
    "storage_yuan_per_tco2": "CNY/tCO2",
}


def _json_scalars(value: Any, prefix: str = "") -> list[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            rows.extend(_json_scalars(child, f"{prefix}.{key}" if prefix else key))
    elif isinstance(value, list):
        rows.append((prefix, json.dumps(value, ensure_ascii=False)))
    else:
        rows.append((prefix, value))
    return rows


def _unit(field: str) -> str:
    if field in UNIT_BY_FIELD:
        return UNIT_BY_FIELD[field]
    if field.endswith("_fraction") or "efficiency" in field or field.startswith("pmin") or field.startswith("pmax"):
        return "fraction"
    if field.endswith("_gw"):
        return "GW"
    if field.endswith("_gwh"):
        return "GWh"
    return "see_source_field"


def _check(checks: list[dict], name: str, passed: bool, value: Any, expected: Any, severity: str = "HARD") -> None:
    checks.append(
        {
            "check": name,
            "status": "PASS" if passed else ("HARD_FAIL" if severity == "HARD" else "WARN"),
            "value": value,
            "expected": expected,
        }
    )


def build_audit(data_root: Path, output_dir: Path) -> dict:
    config = load_model_config()
    output_dir.mkdir(parents=True, exist_ok=True)
    catalog: list[dict] = []
    checks: list[dict] = []
    sources: list[dict] = []
    frames: dict[str, pd.DataFrame] = {}

    registry_path = PROJECT_ROOT / str(
        config.raw["scientific_case"]["parameter_registry"]["path"]
    )
    registry = pd.read_csv(registry_path)
    required_registry_columns = {
        "parameter_group",
        "parameter_key",
        "runtime_authority",
        "unit",
        "base_value",
        "sensitivity_ready",
        "evidence_status",
        "notes",
    }
    _check(
        checks,
        "parameter_registry_columns",
        required_registry_columns.issubset(registry.columns),
        sorted(set(registry.columns)),
        sorted(required_registry_columns),
    )
    _check(
        checks,
        "parameter_registry_unique_keys",
        not registry.duplicated(["parameter_group", "parameter_key"]).any(),
        int(registry.duplicated(["parameter_group", "parameter_key"]).sum()),
        "0 duplicates",
    )
    declared = set(
        zip(registry.parameter_group.astype(str), registry.parameter_key.astype(str))
    )
    _check(
        checks,
        "parameter_registry_required_base_rows",
        REQUIRED_REGISTRY_ROWS.issubset(declared),
        sorted(REQUIRED_REGISTRY_ROWS.difference(declared)),
        "all M1 Base registry rows",
    )
    missing_authorities = []
    for authority in registry.runtime_authority.dropna().astype(str).unique():
        if authority.startswith("$"):
            # External runtime roots are validated by the normal input manifest.
            continue
        candidate = (
            data_root / Path(authority).relative_to("data")
            if authority.startswith("data/")
            else PROJECT_ROOT / authority
        )
        if not candidate.is_file():
            missing_authorities.append(authority)
    _check(
        checks,
        "parameter_registry_runtime_authorities_resolve",
        not missing_authorities,
        missing_authorities,
        "all non-environment runtime authorities exist",
    )

    for module, (relative, keys) in TABLES.items():
        path = data_root / relative
        frame = pd.read_csv(path)
        frames[module] = frame
        _check(checks, f"{module}_key_unique", not frame.duplicated(keys).any() if keys else len(frame) == 1, int(frame.duplicated(keys).sum()) if keys else len(frame), "0 duplicates" if keys else "1 row")
        source_columns = [column for column in frame.columns if column.startswith("source")]
        for column in frame.select_dtypes(include=[np.number, "bool"]).columns:
            for row in frame.itertuples(index=False):
                value = getattr(row, column)
                catalog.append(
                    {
                        "parameter_id": ".".join(
                            [module]
                            + [str(getattr(row, key)) for key in keys]
                            + [column]
                        ),
                        "module": module,
                        "technology": getattr(row, "technology", ""),
                        "province_code": getattr(row, "province_code", ""),
                        "model_year": getattr(row, "year", ""),
                        "scenario": "runtime_base",
                        "value": value,
                        "unit": _unit(column),
                        "runtime_input_file": relative,
                        "source_field": column,
                        "source_reference": " | ".join(
                            str(getattr(row, source))
                            for source in source_columns
                            if pd.notna(getattr(row, source))
                        ),
                        "status": "ACTIVE_RUNTIME",
                    }
                )
        for source_column in source_columns:
            for value in frame[source_column].dropna().astype(str).unique():
                sources.append(
                    {
                        "source_id": f"{module}.{source_column}.{len(sources) + 1}",
                        "module": module,
                        "source_field": source_column,
                        "source_reference": value,
                        "runtime_input_file": relative,
                    }
                )

    for path, value in _json_scalars(config.raw):
        if isinstance(value, (bool, int, float)) and not isinstance(value, str):
            catalog.append(
                {
                    "parameter_id": f"config.{path}",
                    "module": path.split(".")[0],
                    "technology": path.split(".")[-1] if "default_lifetime_years" in path else "",
                    "province_code": "",
                    "model_year": config.planning_year,
                    "scenario": "runtime_base",
                    "value": value,
                    "unit": "configuration_native_unit",
                    "runtime_input_file": "config/optimization_2030.json",
                    "source_field": path,
                    "source_reference": "model configuration",
                    "status": "ACTIVE_RUNTIME",
                }
            )

    years = set(config.planning_years)
    capex = frames["capex"]
    _check(checks, "capex_year_coverage", set(capex.year) == years, sorted(set(capex.year)), sorted(years))
    _check(checks, "capex_rows", len(capex) == 19 * len(years), len(capex), 19 * len(years))
    _check(checks, "capex_finite_positive", bool(np.isfinite(capex.capex_yuan_per_kw).all() and capex.capex_yuan_per_kw.gt(0).all()), float(capex.capex_yuan_per_kw.min()), "> 0")

    fuel = frames["fuel"]
    expected_fuel = {"coal", "coalccs", "cchp", "cchpccs", "gas", "gasccs", "gchp", "gchpccs", "bio", "bioccs"}
    _check(checks, "fuel_technology_coverage", set(fuel.technology) == expected_fuel, sorted(set(fuel.technology)), sorted(expected_fuel))
    _check(checks, "fuel_rows", len(fuel) == 31 * 5 * 10, len(fuel), 31 * 5 * 10)
    allowed = fuel.loc[fuel.dispatch_allowed.astype(bool)]
    _check(checks, "allowed_fuel_cost_finite_nonnegative", bool(np.isfinite(allowed.fuel_cost_yuan_per_mwh).all() and allowed.fuel_cost_yuan_per_mwh.ge(0).all()), int(allowed.fuel_cost_yuan_per_mwh.isna().sum()), "0 invalid")
    biomass = fuel.loc[fuel.technology.isin(["bio", "bioccs"])]
    _check(checks, "biomass_fuel_cost_positive", bool(len(biomass) == 31 * 5 * 2 and biomass.fuel_cost_yuan_per_mwh.gt(0).all()), [float(biomass.fuel_cost_yuan_per_mwh.min()), float(biomass.fuel_cost_yuan_per_mwh.max())], "complete and > 0")
    closure = fuel.loc[fuel.fuel_cost_yuan_per_mwh.notna()].copy()
    closure_error = (closure.fuel_cost_yuan_per_mwh - closure.fuel_price_yuan_per_gj * closure.fuel_load_gj_per_mwh).abs().max()
    _check(checks, "fuel_cost_formula_closure", bool(closure_error <= 1e-9), float(closure_error), "<= 1e-9 CNY/MWh")

    storage = frames["storage"]
    rte_error = (storage.round_trip_efficiency - storage.charge_efficiency * storage.discharge_efficiency).abs().max()
    _check(checks, "storage_round_trip_efficiency_closure", bool(rte_error <= 1e-12), float(rte_error), "<= 1e-12")
    for efficiency in ("charge_efficiency", "discharge_efficiency", "round_trip_efficiency"):
        values = storage[efficiency]
        _check(checks, f"storage_{efficiency}_range", bool(values.gt(0).all() and values.le(1).all()), [float(values.min()), float(values.max())], "(0, 1]")

    ruc = frames["ruc"]
    _check(checks, "ruc_pmin_not_above_pmax", bool(ruc.pmin_fraction.le(ruc.pmax_fraction).all()), int(ruc.pmin_fraction.gt(ruc.pmax_fraction).sum()), "0 violations")
    configured_lifetimes = config.raw["finance"]["default_lifetime_years"]
    storage_lifetime_mismatch = {
        row.technology: [float(row.lifetime_years), configured_lifetimes[row.technology]]
        for row in storage.itertuples(index=False)
        if not math.isclose(float(row.lifetime_years), float(configured_lifetimes[row.technology]))
    }
    _check(checks, "storage_lifetime_config_table_match", not storage_lifetime_mismatch, storage_lifetime_mismatch, "exact match")

    known_risks = [
        {"risk_id": "P0_BECCS_CARBON_MASS_BALANCE", "severity": "P0", "status": "CLOSED", "parameter": "bioccs carbon mass balance", "issue": "The CISPO negative net factor is now split into gross/captured/stored/uncaptured biogenic CO2, zero baseline lifecycle emissions and net removal with hard closure QC; nonzero lifecycle emissions require a sourced scenario."},
        {"risk_id": "P1_NUCLEAR_LIFETIME", "severity": "P1", "status": "SCENARIO_REQUIRED", "parameter": "finance.default_lifetime_years.nuclear", "issue": "Runtime base is 60 years while the local CISPO extraction records 40 years; do not silently change the baseline."},
        {"risk_id": "P1_CAPACITY_MARGIN", "severity": "P1", "status": "CLOSED", "parameter": "security.capacity_margin_fraction", "issue": "Runtime base now uses the reviewed CISPO-aligned 5% provincial capacity margin; alternatives require an explicit scenario override."},
        {"risk_id": "P1_INERTIA_THRESHOLD", "severity": "P1", "status": "CLOSED", "parameter": "security.inertia_reference_seconds × security.inertia_tolerance_fraction", "issue": "Runtime base now records 3.5 s reference × 1.0 tolerance = 3.5 s effective minimum inertia; legacy single-threshold overrides remain supported."},
        {"risk_id": "P1_CAPEX_DIGITIZATION", "severity": "P1", "status": "OPEN", "parameter": "future technology CapEx", "issue": "Most 2030-2060 values are visual estimates from a figure and lack low/base/high bounds and a currency basis year."},
        {"risk_id": "P1_FUEL_TRAJECTORY", "severity": "P1", "status": "OPEN", "parameter": "coal/gas/biomass prices", "issue": "Screenshot price basis year is not stated and values are held constant through 2060."},
        {"risk_id": "P1_COST_BOUNDARY", "severity": "P1", "status": "OPEN", "parameter": "complementarity cost slack", "issue": "Total objective includes fixed legacy-capacity constants; a later epsilon constraint must use decision-dependent cost or an absolute incremental budget."},
    ]

    catalog_frame = pd.DataFrame(catalog).sort_values("parameter_id")
    checks_frame = pd.DataFrame(checks)
    risks_frame = pd.DataFrame(known_risks)
    sources_frame = pd.DataFrame(sources).drop_duplicates(
        ["module", "source_field", "source_reference"]
    )
    catalog_frame.to_csv(output_dir / "model_parameters_long.csv", index=False, encoding="utf-8-sig")
    checks_frame.to_csv(output_dir / "parameter_qc.csv", index=False, encoding="utf-8-sig")
    risks_frame.to_csv(output_dir / "parameter_risk_register.csv", index=False, encoding="utf-8-sig")
    sources_frame.to_csv(output_dir / "source_registry.csv", index=False, encoding="utf-8-sig")
    registry.to_csv(
        output_dir / "critical_parameter_registry_snapshot.csv",
        index=False,
        encoding="utf-8-sig",
    )
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "data_root": str(data_root.resolve()),
        "parameter_rows": int(len(catalog_frame)),
        "qc_pass": int(checks_frame.status.eq("PASS").sum()),
        "qc_warn": int(checks_frame.status.eq("WARN").sum()),
        "qc_hard_fail": int(checks_frame.status.eq("HARD_FAIL").sum()),
        "open_risks": int(risks_frame.status.ne("CLOSED").sum()),
        "files": ["model_parameters_long.csv", "parameter_qc.csv", "parameter_risk_register.csv", "source_registry.csv", "critical_parameter_registry_snapshot.csv"],
    }
    (output_dir / "parameter_audit_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = f"""# CISPO 模型运行参数审计

生成时间：{summary['generated_at']}

## 结论

- 本次整理的是**运行时真实生效参数**，权威链为 `config/optimization_2030.json` + `$CISPO_DATA_ROOT/technology/*.csv`，而不是仅供构建或溯源的重复配置。
- 共展开 {summary['parameter_rows']:,} 条长表参数；自动 QC 为 {summary['qc_pass']} PASS、{summary['qc_warn']} WARN、{summary['qc_hard_fail']} HARD_FAIL。
- `bio/bioccs` 省级燃料成本已接入运行表和目标函数；当前范围为 {biomass.fuel_cost_yuan_per_mwh.min():.2f}–{biomass.fuel_cost_yuan_per_mwh.max():.2f} CNY/MWh。
- 核电寿命、容量裕度、惯量阈值存在“当前研究基线与 CISPO 提取口径不同”的情况，保留为显式情景，不在本轮静默改值。
- BECCS 碳质量平衡、未来 CapEx 区间、长期燃料价格轨迹和互补性成本边界仍是正式论文 case 前必须关闭的风险。

## 文件

- `model_parameters_long.csv`：模型可读/人可筛选的统一长表。
- `parameter_qc.csv`：确定性完整性、范围与公式闭合检查。
- `parameter_risk_register.csv`：未决科学口径及优先级。
- `source_registry.csv`：运行表中携带的来源字段去重登记。
- `critical_parameter_registry_snapshot.csv`：Base 科学标签、混合气象包、VRE 退役与 BECCS 非 LP 敏感性注册表快照。
- `parameter_audit_summary.json`：机器可读摘要。

## 解释边界

四个规划年当前是逐年求解并传递容量 cohort 的目标年快照，不是一次性跨期 NPV 优化。年度 objective 也不能直接相加解释为 2025–2060 路径总成本。后续成本松弛互补性模型应分离 `fixed_exogenous_cost`、`decision_dependent_cost`、`new_build_annualized_cost` 和 `operating_cost`。
"""
    # UTF-8 BOM keeps Chinese readable in legacy Windows PowerShell/Notepad
    # while remaining standards-compliant for modern editors and GitHub.
    (output_dir / "PARAMETER_AUDIT_REPORT_ZH.md").write_text(
        report, encoding="utf-8-sig"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", default=os.environ.get("CISPO_DATA_ROOT", str(PROJECT_ROOT / "data")))
    parser.add_argument("--output-dir", default="outputs/parameter_audit_20260721")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    summary = build_audit(Path(args.data_root), output_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary["qc_hard_fail"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
