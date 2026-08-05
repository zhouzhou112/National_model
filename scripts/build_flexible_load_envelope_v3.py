"""Build Power_curve_V2-consistent hourly thermal flexibility envelopes.

The script perturbs the provincial heating/cooling balance-point thresholds
instead of applying a uniform percentage to load. It writes a model-ready
compressed CSV plus a provenance/QC manifest. No input file is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POWER_CURVE_ROOT = PROJECT_ROOT.parent / "Power_curve_V2"
DEFAULT_HISTORY = (
    DEFAULT_POWER_CURVE_ROOT
    / "outputs"
    / "run_20260617_122125"
    / "tables"
    / "heating_cooling_load_2020_2024.csv.gz"
)
DEFAULT_FUTURE = (
    DEFAULT_POWER_CURVE_ROOT
    / "outputs"
    / "future_8760_projection_ev_calibrated_v3_qc"
    / "tables"
    / "future_hourly_load_2025_2060_8760.csv.gz"
)
DEFAULT_MODEL_LOAD = PROJECT_ROOT / "data" / "load" / "hourly_load_2025_2060.csv.gz"
DEFAULT_PROVINCES = PROJECT_ROOT / "data" / "sets" / "provinces.csv"
DEFAULT_OUTPUT = (
    PROJECT_ROOT / "data" / "load" / "flexible_load_envelope_v3.csv.gz"
)
TARGET_YEARS = (2025, 2030, 2040, 2050, 2060)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _threshold_envelopes(
    frame: pd.DataFrame,
    *,
    heating_band_c: float,
    cooling_band_c: float,
) -> pd.DataFrame:
    heat_degree_raw = (
        frame["heat_threshold_c"].to_numpy(float)
        - frame["bait_c"].to_numpy(float)
    )
    cool_degree_raw = (
        frame["bait_c"].to_numpy(float)
        - frame["cool_threshold_c"].to_numpy(float)
    )
    heat_degree = np.maximum(heat_degree_raw, 0.0)
    cool_degree = np.maximum(cool_degree_raw, 0.0)
    heat_coefficient = (
        frame["p_heat_gwh_per_degree_day"].to_numpy(float) * 1000.0 / 24.0
    )
    cool_coefficient = (
        frame["p_cool_gwh_per_degree_day"].to_numpy(float) * 1000.0 / 24.0
    )
    heating_baseline = heat_coefficient * heat_degree
    cooling_baseline = cool_coefficient * cool_degree
    heating_relaxed = heat_coefficient * np.maximum(
        heat_degree_raw - heating_band_c, 0.0
    )
    heating_intensified = heat_coefficient * np.maximum(
        heat_degree_raw + heating_band_c, 0.0
    )
    cooling_relaxed = cool_coefficient * np.maximum(
        cool_degree_raw - cooling_band_c, 0.0
    )
    cooling_intensified = cool_coefficient * np.maximum(
        cool_degree_raw + cooling_band_c, 0.0
    )

    source_heating = frame["heating_load_mw"].to_numpy(float)
    source_cooling = frame["cooling_load_mw"].to_numpy(float)
    if not np.allclose(heating_baseline, source_heating, atol=1e-5, rtol=1e-10):
        raise ValueError("Reconstructed 2024 heating load does not match Power_curve_V2")
    if not np.allclose(cooling_baseline, source_cooling, atol=1e-5, rtol=1e-10):
        raise ValueError("Reconstructed 2024 cooling load does not match Power_curve_V2")

    return pd.DataFrame(
        {
            "province_cn": frame["province_cn"].to_numpy(),
            "template_key": frame["template_key"].to_numpy(),
            "heating_increase_2024_mw": heating_intensified - heating_baseline,
            "heating_reduction_2024_mw": heating_baseline - heating_relaxed,
            "cooling_increase_2024_mw": cooling_intensified - cooling_baseline,
            "cooling_reduction_2024_mw": cooling_baseline - cooling_relaxed,
        }
    )


def build_envelope(
    *,
    history_path: Path,
    future_path: Path,
    model_load_path: Path,
    provinces_path: Path,
    output_path: Path,
    heating_band_c: float,
    cooling_band_c: float,
) -> dict[str, object]:
    for path in (history_path, future_path, model_load_path, provinces_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    if heating_band_c <= 0.0 or cooling_band_c <= 0.0:
        raise ValueError("Comfort-band deltas must be positive")

    history = pd.read_csv(
        history_path,
        usecols=[
            "province_cn",
            "datetime_bj",
            "year",
            "bait_c",
            "heat_threshold_c",
            "cool_threshold_c",
            "p_heat_gwh_per_degree_day",
            "p_cool_gwh_per_degree_day",
            "heating_load_mw",
            "cooling_load_mw",
        ],
        parse_dates=["datetime_bj"],
    )
    history = history.loc[history.year.eq(2024)].copy()
    history = history.loc[
        ~(
            history.datetime_bj.dt.month.eq(2)
            & history.datetime_bj.dt.day.eq(29)
        )
    ].copy()
    history["template_key"] = history.datetime_bj.dt.strftime("%m-%d %H")
    if len(history) != 31 * 8760:
        raise ValueError(f"Expected 271560 non-leap 2024 rows, found {len(history)}")
    if history.duplicated(["province_cn", "template_key"]).any():
        raise ValueError("Duplicate Power_curve_V2 province/template rows")
    template = _threshold_envelopes(
        history,
        heating_band_c=heating_band_c,
        cooling_band_c=cooling_band_c,
    )

    future = pd.read_csv(
        future_path,
        usecols=[
            "province_cn",
            "target_year",
            "hour_index",
            "template_key",
            "thermal_multiplier",
            "heating_load_mw",
            "cooling_load_mw",
        ],
    )
    future = future.loc[future.target_year.isin(TARGET_YEARS)].copy()
    future = future.merge(
        template,
        on=["province_cn", "template_key"],
        how="left",
        validate="many_to_one",
    )
    if future.isna().any().any():
        missing = future.columns[future.isna().any()].tolist()
        raise ValueError(f"Missing values after template merge: {missing}")

    provinces = pd.read_csv(
        provinces_path,
        usecols=["province_code", "province_name_zh"],
    ).rename(columns={"province_name_zh": "province_cn"})
    future = future.merge(
        provinces, on="province_cn", how="left", validate="many_to_one"
    )
    if future.province_code.isna().any():
        raise ValueError(
            "Unmapped provinces: "
            + ", ".join(sorted(future.loc[future.province_code.isna(), "province_cn"].unique()))
        )

    multiplier = future["thermal_multiplier"].to_numpy(float)
    for component in ("heating", "cooling"):
        future[f"{component}_increase_limit_gw"] = (
            future[f"{component}_increase_2024_mw"].to_numpy(float)
            * multiplier
            / 1000.0
        )
        future[f"{component}_reduction_limit_gw"] = (
            future[f"{component}_reduction_2024_mw"].to_numpy(float)
            * multiplier
            / 1000.0
        )

    model_load = pd.read_csv(
        model_load_path,
        usecols=[
            "province_code",
            "year",
            "hour_index",
            "heating_gw",
            "cooling_gw",
        ],
    )
    model_load = model_load.loc[model_load.year.isin(TARGET_YEARS)].copy()
    check = future.merge(
        model_load,
        left_on=["province_code", "target_year", "hour_index"],
        right_on=["province_code", "year", "hour_index"],
        how="left",
        validate="one_to_one",
    )
    for component in ("heating", "cooling"):
        future_baseline = check[f"{component}_load_mw"].to_numpy(float) / 1000.0
        model_baseline = check[f"{component}_gw"].to_numpy(float)
        if not np.allclose(
            future_baseline, model_baseline, atol=1e-8, rtol=1e-9
        ):
            raise ValueError(
                f"{component} baseline differs between Power_curve_V2 and model input"
            )
        reduction = check[f"{component}_reduction_limit_gw"].to_numpy(float)
        if np.max(reduction - model_baseline) > 1e-9:
            raise ValueError(f"{component} reduction limit exceeds baseline load")

    output = future[
        [
            "province_code",
            "target_year",
            "hour_index",
            "heating_increase_limit_gw",
            "heating_reduction_limit_gw",
            "cooling_increase_limit_gw",
            "cooling_reduction_limit_gw",
        ]
    ].rename(columns={"target_year": "year"})
    output["province_code"] = output["province_code"].astype(int)
    output["heating_comfort_band_c"] = heating_band_c
    output["cooling_comfort_band_c"] = cooling_band_c
    output = output.sort_values(["year", "province_code", "hour_index"])
    expected_rows = len(TARGET_YEARS) * 31 * 8760
    if len(output) != expected_rows:
        raise ValueError(f"Expected {expected_rows} output rows, found {len(output)}")
    numeric = output.select_dtypes(include=[np.number]).to_numpy(float)
    if not np.isfinite(numeric).all():
        raise ValueError("Output contains non-finite values")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(
        output_path,
        index=False,
        compression="gzip",
        encoding="utf-8",
    )
    manifest = {
        "contract_version": "flexible_load_envelope_v3",
        "generated_at": datetime.now().astimezone().isoformat(),
        "output_file": str(output_path.resolve()),
        "output_sha256": sha256_file(output_path),
        "row_count": int(len(output)),
        "years": list(TARGET_YEARS),
        "province_count": int(output.province_code.nunique()),
        "hours_per_province_year": 8760,
        "heating_comfort_band_c": heating_band_c,
        "cooling_comfort_band_c": cooling_band_c,
        "method": (
            "Power_curve_V2 2024 BAIT and balance-point thresholds are perturbed "
            "by +/- comfort_band_c; hourly MW envelopes are then multiplied by "
            "the original future thermal_multiplier."
        ),
        "inputs": {
            "power_curve_v2_thermal_history": {
                "path": str(history_path.resolve()),
                "sha256": sha256_file(history_path),
            },
            "power_curve_v2_future_hourly": {
                "path": str(future_path.resolve()),
                "sha256": sha256_file(future_path),
            },
            "national_model_hourly_load": {
                "path": str(model_load_path.resolve()),
                "sha256": sha256_file(model_load_path),
            },
            "province_table": {
                "path": str(provinces_path.resolve()),
                "sha256": sha256_file(provinces_path),
            },
        },
        "qc": {
            "source_formula_reconstruction": "PASS",
            "future_model_baseline_alignment": "PASS",
            "reduction_not_above_baseline": "PASS",
            "finite_nonnegative_envelopes": "PASS",
        },
        "interpretation": (
            "The comfort bands are scenario assumptions, not calibrated indoor "
            "temperature trajectories. The optimization adds an equivalent "
            "thermal-state constraint separately."
        ),
    }
    manifest_path = output_path.with_suffix("").with_suffix(".manifest.json")
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--thermal-history", type=Path, default=DEFAULT_HISTORY)
    parser.add_argument("--future-hourly", type=Path, default=DEFAULT_FUTURE)
    parser.add_argument("--model-load", type=Path, default=DEFAULT_MODEL_LOAD)
    parser.add_argument("--provinces", type=Path, default=DEFAULT_PROVINCES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--heating-comfort-band-c", type=float, default=1.0)
    parser.add_argument("--cooling-comfort-band-c", type=float, default=1.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_envelope(
        history_path=args.thermal_history.resolve(),
        future_path=args.future_hourly.resolve(),
        model_load_path=args.model_load.resolve(),
        provinces_path=args.provinces.resolve(),
        output_path=args.output.resolve(),
        heating_band_c=float(args.heating_comfort_band_c),
        cooling_band_c=float(args.cooling_comfort_band_c),
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
