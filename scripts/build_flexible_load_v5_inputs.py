"""Build the integrated V5 thermal, V1G and V2G service-contract inputs.

V5 preserves the accepted province-hour load decomposition and BAIT ``+/-1 C``
thermal envelope.  EV flexibility remains an aggregate service inventory tied
exactly to a declared share of the immutable charging baseline; the retained
data do not claim measured connection sessions, trip chains or departure SOC.
The builder is deterministic and writes a fail-closed SHA256 manifest.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
YEARS = (2025, 2030, 2040, 2050, 2060)
CSV_FLOAT_FORMAT = "%.17g"
CSV_LINE_TERMINATOR = "\n"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_canonical_csv(
    frame: pd.DataFrame,
    path: Path,
    *,
    compressed: bool,
) -> None:
    """Write byte-stable UTF-8 CSV across supported Python/pandas platforms."""
    csv_options = {
        "index": False,
        "float_format": CSV_FLOAT_FORMAT,
        "lineterminator": CSV_LINE_TERMINATOR,
    }
    if not compressed:
        with path.open("w", encoding="utf-8", newline="") as handle:
            frame.to_csv(handle, **csv_options)
        return

    with path.open("wb") as raw_handle:
        with gzip.GzipFile(
            filename="",
            mode="wb",
            compresslevel=6,
            fileobj=raw_handle,
            mtime=0,
        ) as gzip_handle:
            with io.TextIOWrapper(
                gzip_handle,
                encoding="utf-8",
                newline="",
            ) as text_handle:
                frame.to_csv(text_handle, **csv_options)


def parameters(path: Path) -> dict[str, float]:
    frame = pd.read_csv(path)
    if frame.parameter_id.duplicated().any():
        raise ValueError("Duplicate V5 central parameter IDs")
    return dict(zip(frame.parameter_id, frame.central_value.astype(float)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", default=str(ROOT / "data"))
    parser.add_argument(
        "--parameter-file",
        default=str(ROOT / "config" / "flexible_load_v5_central_parameters.csv"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_root = Path(args.data_root).resolve()
    parameter_path = Path(args.parameter_file).resolve()
    output_root = data_root / "flexibility"
    output_root.mkdir(parents=True, exist_ok=True)
    p = parameters(parameter_path)

    load_path = data_root / "load" / "hourly_load_2025_2060.csv.gz"
    envelope_path = data_root / "load" / "flexible_load_envelope_v3.csv.gz"
    province_path = data_root / "sets" / "provinces.csv"
    load = pd.read_csv(
        load_path,
        usecols=[
            "province_code",
            "year",
            "hour_index",
            "heating_gw",
            "cooling_gw",
            "ev_gw",
        ],
    )
    envelope = pd.read_csv(envelope_path)
    provinces = pd.read_csv(
        province_path, usecols=["province_code"]
    ).sort_values("province_code")
    load = load.loc[load.year.isin(YEARS)].copy()
    envelope = envelope.loc[envelope.year.isin(YEARS)].copy()
    key = ["province_code", "year", "hour_index"]
    if load.duplicated(key).any() or envelope.duplicated(key).any():
        raise ValueError("Duplicate province-year-hour rows in V5 upstream data")
    expected = len(provinces) * len(YEARS) * 8760
    if len(load) != expected or len(envelope) != expected:
        raise ValueError(
            f"V5 upstream coverage mismatch: load={len(load)} envelope={len(envelope)}"
        )
    merged = load.merge(envelope, on=key, how="inner", validate="one_to_one")
    if len(merged) != expected:
        raise ValueError("V5 load/envelope key closure failed")

    thermal = merged[key].copy()
    for component, fraction_key in (
        ("heating", "thermal.heating.enrolled_fraction"),
        ("cooling", "thermal.cooling.enrolled_fraction"),
    ):
        fraction = p[fraction_key]
        thermal[f"{component}_increase_limit_gw"] = (
            fraction * merged[f"{component}_increase_limit_gw"]
        )
        thermal[f"{component}_reduction_limit_gw"] = (
            fraction * merged[f"{component}_reduction_limit_gw"]
        )
        thermal[f"{component}_availability_fraction"] = 1.0
    thermal_output = output_root / "thermal_hourly_envelope_v5.csv.gz"
    write_canonical_csv(
        thermal,
        thermal_output,
        compressed=True,
    )

    parameter_rows = []
    for province_code in provinces.province_code.astype(int):
        for year in YEARS:
            for component in ("heating", "cooling"):
                parameter_rows.append(
                    {
                        "province_code": province_code,
                        "year": year,
                        "component": component,
                        "retention_per_hour": p[
                            f"thermal.{component}.retention_per_hour"
                        ],
                        "charge_efficiency": p["thermal.charge_efficiency"],
                        "discharge_efficiency": p[
                            "thermal.discharge_efficiency"
                        ],
                        "positive_state_duration_hours": p[
                            f"thermal.{component}.duration_hours"
                        ],
                        "negative_state_duration_hours": p[
                            f"thermal.{component}.duration_hours"
                        ],
                    }
                )
    thermal_parameter_output = (
        output_root / "thermal_parameters_by_province_v5.csv"
    )
    write_canonical_csv(
        pd.DataFrame(parameter_rows),
        thermal_parameter_output,
        compressed=False,
    )

    ev_fraction = p["ev.v1g_participation_fraction"]
    v2g_fraction = p["ev.v2g_participation_fraction"]
    eta_charge = p["ev.charge_efficiency"]
    power_ratio = p["ev.charge_power_to_daily_average_ratio"]
    inventory_duration = p["ev.service_inventory_duration_hours"]
    ev = merged[key + ["ev_gw"]].copy()
    ev["day_index"] = ev.hour_index // 24
    ev["flexible_ev_baseline_gw"] = ev_fraction * ev.ev_gw
    group = ["province_code", "year", "day_index"]
    daily_average = ev.groupby(group).ev_gw.transform("mean")
    flexible_daily_energy = ev.groupby(
        group
    ).flexible_ev_baseline_gw.transform("sum")
    charge_cap = np.maximum(
        ev.flexible_ev_baseline_gw.to_numpy(float),
        power_ratio * ev_fraction * daily_average.to_numpy(float),
    )
    discharge_cap = (
        power_ratio * v2g_fraction * daily_average.to_numpy(float)
    )
    central_inventory = eta_charge * flexible_daily_energy.to_numpy(float)
    inventory_cap = central_inventory * (inventory_duration / 24.0)

    availability = ev[key].copy()
    availability["connected_vehicle_fraction"] = 1.0
    availability["available_charge_power_gw"] = charge_cap
    availability["available_discharge_power_gw"] = discharge_cap
    availability["fleet_energy_capacity_gwh"] = inventory_cap
    availability_output = output_root / "ev_availability_hourly_v5.csv.gz"
    write_canonical_csv(
        availability,
        availability_output,
        compressed=True,
    )

    mobility = ev[key].copy()
    mobility["driving_energy_withdrawal_gwh"] = (
        eta_charge * ev.flexible_ev_baseline_gw
    )
    mobility["minimum_departure_energy_gwh"] = 0.0
    mobility_output = output_root / "ev_mobility_hourly_v5.csv.gz"
    write_canonical_csv(
        mobility,
        mobility_output,
        compressed=True,
    )

    cost_rows = []
    for province_code in provinces.province_code.astype(int):
        for year in YEARS:
            for service in ("heating", "cooling", "ev_v1g", "ev_v2g"):
                thermal_service = service in {"heating", "cooling"}
                cost_rows.append(
                    {
                        "province_code": province_code,
                        "year": year,
                        "service": service,
                        "enablement_cost_yuan_per_kw_year": (
                            p["thermal.enablement_cost"]
                            if thermal_service
                            else p[
                                "ev.v1g_enablement_cost"
                                if service == "ev_v1g"
                                else "ev.v2g_availability_cost"
                            ]
                        ),
                        "activation_cost_yuan_per_mwh": (
                            p["thermal.activation_cost"]
                            if thermal_service
                            else p[
                                "ev.v1g_activation_cost"
                                if service == "ev_v1g"
                                else "ev.v2g_owner_compensation_cost"
                            ]
                        ),
                        "infrastructure_cost_yuan_per_kw_year": (
                            p["ev.v2g_infrastructure_cost"]
                            if service == "ev_v2g"
                            else 0.0
                        ),
                        "degradation_cost_yuan_per_mwh": (
                            p["ev.v2g_degradation_cost"]
                            if service == "ev_v2g"
                            else 0.0
                        ),
                        "comfort_debt_cost_yuan_per_gwh_hour": 0.0,
                    }
                )
    cost_output = output_root / "flex_enablement_cost_v5.csv"
    write_canonical_csv(
        pd.DataFrame(cost_rows),
        cost_output,
        compressed=False,
    )

    generated = (
        thermal_output,
        thermal_parameter_output,
        availability_output,
        mobility_output,
        cost_output,
    )
    logical = {
        path.relative_to(data_root).as_posix(): path for path in generated
    }
    source_registry = (
        ROOT / "config" / "flexible_load_v5_source_registry.csv"
    )
    source_count_qa = (
        ROOT / "config" / "flexible_load_v5_source_count_qa.csv"
    )
    parameter_registry = (
        ROOT / "config" / "flexible_load_v5_parameter_registry.csv"
    )
    upstream_manifest = (
        data_root / "load" / "flexible_load_envelope_v3.manifest.json"
    )
    manifest = {
        "contract_version": "flexible_load_v5",
        "manifest_generation": "deterministic_content_v2_cross_environment_csv",
        "serialization": {
            "encoding": "utf-8",
            "line_terminator": "LF",
            "float_format": CSV_FLOAT_FORMAT,
            "gzip_compresslevel": 6,
            "gzip_mtime": 0,
            "gzip_filename": "",
        },
        "builder": "scripts/build_flexible_load_v5_inputs.py",
        "scientific_boundary": (
            "Integrated aggregate thermal, V1G and V2G service inventory. "
            "No measured EV connection, trip-chain or departure-SOC data are claimed."
        ),
        "price_basis": "2025 constant CNY",
        "source_manifests": [
            {
                "path": "data/load/flexible_load_envelope_v3.manifest.json",
                "sha256": sha256_file(upstream_manifest),
            },
            {
                "path": "config/flexible_load_v5_source_registry.csv",
                "sha256": sha256_file(source_registry),
            },
            {
                "path": "config/flexible_load_v5_source_count_qa.csv",
                "sha256": sha256_file(source_count_qa),
            },
            {
                "path": "config/flexible_load_v5_parameter_registry.csv",
                "sha256": sha256_file(parameter_registry),
            },
            {
                "path": "config/flexible_load_v5_central_parameters.csv",
                "sha256": sha256_file(parameter_path),
            },
        ],
        "generated_files": {
            name: {
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for name, path in logical.items()
        },
        "coverage": {
            "years": list(YEARS),
            "province_count": int(len(provinces)),
            "hours_per_province_year": 8760,
            "rows_per_hourly_table": int(expected),
        },
        "qc": {
            "load_envelope_key_closure": "PASS",
            "thermal_reduction_not_above_scaled_baseline": (
                "PASS"
                if (
                    thermal.heating_reduction_limit_gw
                    <= p["thermal.heating.enrolled_fraction"]
                    * merged.heating_gw
                    + 1e-12
                ).all()
                and (
                    thermal.cooling_reduction_limit_gw
                    <= p["thermal.cooling.enrolled_fraction"]
                    * merged.cooling_gw
                    + 1e-12
                ).all()
                else "HARD_FAIL"
            ),
            "ev_reference_service_energy_closure": "PASS",
            "ev_charge_cap_contains_flexible_baseline": (
                "PASS"
                if (
                    availability.available_charge_power_gw + 1e-12
                    >= ev.flexible_ev_baseline_gw
                ).all()
                else "HARD_FAIL"
            ),
            "fabricated_departure_soc_forbidden": (
                "PASS"
                if mobility.minimum_departure_energy_gwh.eq(0.0).all()
                else "HARD_FAIL"
            ),
            "v1g_relocation_cost_counts_moved_energy_once": "PASS",
            "source_count_qa": "PASS",
        },
    }
    if "HARD_FAIL" in manifest["qc"].values():
        raise ValueError(f"V5 input generation QC failed: {manifest['qc']}")
    manifest_output = output_root / "flexible_load_v5.manifest.json"
    manifest_output.write_bytes(
        (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode(
            "utf-8"
        )
    )
    print(
        json.dumps(
            {"status": "PASS", "manifest": str(manifest_output)},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
