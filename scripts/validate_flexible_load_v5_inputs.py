"""Validate the integrated V5 flexibility input and evidence contracts."""
from __future__ import annotations

import argparse
import json
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


def _load_components(
    data_root: Path, config: Any
) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    provinces = pd.read_csv(
        data_root / "sets" / "provinces.csv",
        usecols=["province_code", "province_name_en", "province_name_zh"],
    ).sort_values("province_code").reset_index(drop=True)
    load = pd.read_csv(
        data_root / "load" / "hourly_load_2025_2060.csv.gz",
        usecols=[
            "province_code",
            "year",
            "hour_index",
            "base_residual_gw",
            "heating_gw",
            "cooling_gw",
            "ev_gw",
        ],
    )
    load = load.loc[load.year.eq(config.planning_year)].copy()
    expected_rows = len(provinces) * config.hours
    if len(provinces) != 31 or len(load) != expected_rows:
        raise ValueError("V5 validation requires complete 31-province coverage")
    province_order = provinces.province_code.astype(int).tolist()
    components = {}
    for name, column in {
        "base_residual": "base_residual_gw",
        "heating": "heating_gw",
        "cooling": "cooling_gw",
        "ev": "ev_gw",
    }.items():
        values = load.pivot(
            index="province_code", columns="hour_index", values=column
        ).reindex(
            index=province_order, columns=range(config.hours)
        ).to_numpy(float)
        if not np.isfinite(values).all() or (values < 0.0).any():
            raise ValueError(f"Invalid immutable {name} load component")
        components[name] = values
    return provinces, components


def build_audit(data_root: Path) -> dict[str, Any]:
    from cispo_model import data as data_module
    from cispo_model.config import load_model_config

    scenario_path = (
        PROJECT_ROOT
        / "config"
        / "scenarios"
        / "flex_integrated_v5_central.json"
    )
    config = load_model_config(scenario_path=scenario_path)
    data_module.DATA_ROOT = data_root
    per_year = {}
    for planning_year in config.planning_years:
        year_config = config.for_planning_year(planning_year)
        provinces, components = _load_components(data_root, year_config)
        service = data_module._load_flexible_load_v4_data(
            year_config,
            provinces=provinces,
            load_components_gw=components,
            expected_rows=len(provinces) * year_config.hours,
        )
        if service.contract_version != "v5":
            raise ValueError("V5 loader returned the wrong contract identity")
        cap = float(
            year_config.raw["flexible_load"]["ev_v2g"][
                "national_contracted_power_cap_gw_by_planning_year"
            ][str(planning_year)]
        )
        per_year[str(planning_year)] = {
            "province_count": len(provinces),
            "hours_per_province": year_config.hours,
            "v1g_shiftable_energy_fraction": float(
                year_config.raw["flexible_load"]["ev_v1g"][
                    "shiftable_energy_fraction"
                ]
            ),
            "v2g_national_contracted_power_cap_gw": cap,
            "maximum_ev_charge_power_gw": float(
                service.ev_availability[
                    "available_charge_power_gw"
                ].max()
            ),
            "maximum_ev_discharge_power_gw": float(
                service.ev_availability[
                    "available_discharge_power_gw"
                ].max()
            ),
        }

    source_count = pd.read_csv(
        PROJECT_ROOT / "config" / "flexible_load_v5_source_count_qa.csv"
    )
    sources = pd.read_csv(
        PROJECT_ROOT / "config" / "flexible_load_v5_source_registry.csv"
    )
    parameter = pd.read_csv(
        PROJECT_ROOT / "config" / "flexible_load_v5_central_parameters.csv"
    )
    referenced_by_parameter = {
        str(source_id).strip()
        for value in parameter.source_ids
        for source_id in str(value).split(";")
        if str(source_id).strip()
    }
    registered_source_ids = set(sources.source_id.astype(str))
    unknown_source_ids = sorted(
        referenced_by_parameter - registered_source_ids
    )
    duplicated_source_ids = sorted(
        sources.loc[
            sources.source_id.astype(str).duplicated(keep=False), "source_id"
        ].astype(str).unique()
    )

    def evidence_counts(parameter_mask: pd.Series) -> dict[str, int]:
        selected_ids = {
            str(source_id).strip()
            for value in parameter.loc[parameter_mask, "source_ids"]
            for source_id in str(value).split(";")
            if str(source_id).strip()
        }
        selected = sources.loc[sources.source_id.isin(selected_ids)].copy()
        china_text = (
            selected.title.astype(str)
            + " "
            + selected.scope.astype(str)
        )
        china_specific = selected.source_type.eq(
            "China_official"
        ) | china_text.str.contains(
            r"China|Chinese|Beijing|Shanghai|Zhejiang|Anhui|Quzhou",
            case=False,
            regex=True,
        )
        return {
            "independent_source_groups": int(len(selected_ids)),
            "china_specific_groups": int(china_specific.sum()),
            "peer_reviewed_groups": int(
                selected.source_type.eq("peer_reviewed").sum()
            ),
        }

    calculated_source_counts = {
        "thermal_service_and_cost": evidence_counts(
            parameter.parameter_id.astype(str).str.startswith("thermal.")
        ),
        "ev_v1g_v2g_and_cost": evidence_counts(
            parameter.parameter_id.astype(str).str.startswith("ev.")
        ),
        "firm_capacity_accreditation": evidence_counts(
            parameter.parameter_id.astype(str).str.startswith("firm.")
            | parameter.parameter_id.astype(str).str.startswith(
                "ev.v2g_national_cap_"
            )
        ),
    }
    declared_source_counts = source_count.set_index("review_unit")
    source_count_rows_match = True
    for review_unit, calculated in calculated_source_counts.items():
        if review_unit not in declared_source_counts.index:
            source_count_rows_match = False
            continue
        declared = declared_source_counts.loc[review_unit]
        source_count_rows_match = source_count_rows_match and all(
            int(declared[field]) == value
            for field, value in calculated.items()
        )
    source_count_pass = bool(
        not unknown_source_ids
        and not duplicated_source_ids
        and set(declared_source_counts.index) == set(calculated_source_counts)
        and source_count_rows_match
        and source_count.status.eq("PASS").all()
        and (
            source_count.independent_source_groups
            >= source_count.required_minimum
        ).all()
    )
    parameter_pass = bool(
        parameter.parameter_id.is_unique
        and np.isfinite(parameter.central_value.astype(float)).all()
        and np.isfinite(parameter.low_value.astype(float)).all()
        and np.isfinite(parameter.high_value.astype(float)).all()
        and (
            parameter.low_value.astype(float)
            <= parameter.central_value.astype(float)
        ).all()
        and (
            parameter.central_value.astype(float)
            <= parameter.high_value.astype(float)
        ).all()
    )
    checks = {
        "loader_manifest_and_sha256_contract": True,
        "all_planning_years_covered": set(per_year)
        == {"2030", "2040", "2050", "2060"},
        "source_count_qa": source_count_pass,
        "all_parameter_source_ids_resolve": not unknown_source_ids,
        "source_registry_ids_unique": not duplicated_source_ids,
        "low_central_high_parameter_order": parameter_pass,
        "v1g_central_participation_is_15_percent": all(
            np.isclose(row["v1g_shiftable_energy_fraction"], 0.15)
            for row in per_year.values()
        ),
    }
    failures = [name for name, passed in checks.items() if not passed]
    return {
        "schema_version": "flexible_load_v5_input_audit_v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": "PASS" if not failures else "HARD_FAIL",
        "data_root": str(data_root.resolve()),
        "checks": checks,
        "failures": failures,
        "evidence": {
            "calculated_source_counts": calculated_source_counts,
            "unknown_source_ids": unknown_source_ids,
            "duplicated_source_ids": duplicated_source_ids,
        },
        "per_year": per_year,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-root",
        default=os.environ.get(
            "CISPO_DATA_ROOT", str(PROJECT_ROOT / "data")
        ),
    )
    parser.add_argument("--output")
    args = parser.parse_args()
    report = build_audit(Path(args.data_root).resolve())
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps({"status": report["status"], "failures": report["failures"]}))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
