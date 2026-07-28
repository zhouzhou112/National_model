"""Validate and manifest calibrated V4 demand-flexibility inputs.

This command does not synthesize availability, mobility, SOC, thermal-response
or compensation values.  It validates the five calibrated tables against the
same fail-closed loader contract used by the model, then writes the mandatory
SHA256 provenance sidecar.  Use it before moving a V4 scenario out of
``planned_not_runnable``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_components(data_root: Path, config: Any) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    provinces = pd.read_csv(
        data_root / "sets" / "provinces.csv",
        usecols=["province_code", "province_name_en", "province_name_zh"],
    ).sort_values("province_code").reset_index(drop=True)
    if len(provinces) != 31 or not provinces.province_code.is_unique:
        raise ValueError("V4 validation requires 31 canonical province rows")
    load = pd.read_csv(
        data_root / "load" / "hourly_load_2025_2060.csv.gz",
        usecols=[
            "province_code", "year", "hour_index", "base_residual_gw",
            "heating_gw", "cooling_gw", "ev_gw",
        ],
    )
    load = load.loc[load.year.eq(config.planning_year)].copy()
    expected_rows = len(provinces) * config.hours
    if len(load) != expected_rows:
        raise ValueError(
            f"{config.planning_year} load rows={len(load)} expected={expected_rows}"
        )
    if load.duplicated(["province_code", "hour_index"]).any():
        raise ValueError("Duplicate province-hour rows in immutable load input")
    province_order = provinces.province_code.astype(int).tolist()
    components: dict[str, np.ndarray] = {}
    for name, column in {
        "base_residual": "base_residual_gw",
        "heating": "heating_gw",
        "cooling": "cooling_gw",
        "ev": "ev_gw",
    }.items():
        values = load.pivot(
            index="province_code", columns="hour_index", values=column
        ).reindex(index=province_order, columns=range(config.hours)).to_numpy(float)
        if not np.isfinite(values).all() or (values < 0.0).any():
            raise ValueError(f"Immutable {name} input is non-finite or negative")
        components[name] = values
    return provinces, components


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate all calibrated V4 flexibility tables and write their provenance manifest."
    )
    parser.add_argument(
        "--scenario-config",
        default="config/scenarios/flexible_load_comfort_v4_v1g.json",
        help="V4 V1G or V2G scenario JSON",
    )
    parser.add_argument(
        "--data-root",
        default=os.environ.get("CISPO_DATA_ROOT", str(PROJECT_ROOT / "data")),
        help="CISPO model-table root containing flexibility/",
    )
    parser.add_argument(
        "--source-manifest",
        action="append",
        required=True,
        help="Source-provenance manifest used to create the calibrated tables; repeat for each independent source package",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output path; default is v4_input_files.input_manifest_file",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_root = Path(args.data_root).resolve()
    if not data_root.is_dir():
        raise FileNotFoundError(data_root)
    scenario_path = Path(args.scenario_config)
    if not scenario_path.is_absolute():
        scenario_path = PROJECT_ROOT / scenario_path

    # Import after resolving the data root because cispo_model.data snapshots
    # its default at module import.  Assigning DATA_ROOT here keeps this script
    # faithful to a caller-supplied root without changing global environment.
    from cispo_model.config import load_model_config
    from cispo_model import data as data_module

    config = load_model_config(scenario_path=scenario_path)
    if config.raw["flexible_load"].get("formulation") != "service_constrained_v4":
        raise ValueError("--scenario-config must resolve to service_constrained_v4")
    data_module.DATA_ROOT = data_root
    files = config.raw["flexible_load"]["v4_input_files"]
    source_manifests = []
    for value in args.source_manifest:
        path = Path(value).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        source_manifests.append({"path": str(path), "sha256": sha256_file(path)})

    per_year: dict[str, Any] = {}
    for planning_year in config.planning_years:
        year_config = config.for_planning_year(planning_year)
        provinces, components = load_components(data_root, year_config)
        v4 = data_module._load_flexible_load_v4_data(
            year_config,
            provinces=provinces,
            load_components_gw=components,
            expected_rows=len(provinces) * year_config.hours,
            require_manifest=False,
        )
        per_year[str(planning_year)] = {
            "province_count": int(len(provinces)),
            "hours_per_province": int(year_config.hours),
            "heating_envelope_max_gw": float(v4.thermal_envelopes_gw["heating_up"].max()),
            "cooling_envelope_max_gw": float(v4.thermal_envelopes_gw["cooling_up"].max()),
            "ev_charge_power_max_gw": float(v4.ev_availability["available_charge_power_gw"].max()),
            "ev_fleet_energy_max_gwh": float(v4.ev_availability["fleet_energy_capacity_gwh"].max()),
        }

    generated_files = {}
    for key in (
        "thermal_hourly_envelope_file",
        "thermal_parameters_file",
        "ev_availability_hourly_file",
        "ev_mobility_hourly_file",
        "enablement_cost_file",
    ):
        logical_path = str(files[key])
        path = data_root / logical_path
        generated_files[logical_path] = {
            "sha256": sha256_file(path),
            "size_bytes": int(path.stat().st_size),
        }
    output = (
        Path(args.output).resolve()
        if args.output
        else (data_root / str(files["input_manifest_file"])).resolve()
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "contract_version": "flexible_load_v4",
        "generated_at": datetime.now().astimezone().isoformat(),
        "scenario_config": {
            "path": str(scenario_path.resolve()),
            "sha256": sha256_file(scenario_path),
        },
        "source_manifests": source_manifests,
        "generated_files": generated_files,
        "year_qc": per_year,
        "qc": {
            "loader_contract": "PASS",
            "immutable_ev_reference_energy_closure": "PASS",
            "thermal_and_ev_schema_coverage": "PASS",
            "generated_file_sha256_recorded": "PASS",
        },
    }
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": "PASS", "manifest": str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
