"""Audit incremental CF sparsification error for wave and run-of-river hydro."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cispo_model.config import load_model_config
from cispo_model.data import load_model_data
from cispo_model.hydro import HydroProfileReader
from cispo_model.timeblocks import TimeBlock


DEFAULT_THRESHOLDS = (1e-6, 2e-6, 5e-6, 1e-5, 2e-5, 5e-5, 1e-4)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--planning-year", type=int, default=2030)
    parser.add_argument("--start-hour", type=int, default=0)
    parser.add_argument("--hours", type=int, default=8760)
    parser.add_argument("--chunk-hours", type=int, default=168)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def _empty_resource(name: str, thresholds: tuple[float, ...], hours: int) -> dict:
    return {
        "resource": name,
        "coefficient_count": 0,
        "raw_positive_coefficient_count": 0,
        "production_retained_coefficient_count": 0,
        "smallest_raw_positive_cf": None,
        "smallest_production_retained_cf": None,
        "baseline_floor_availability_energy_gwh": 0.0,
        "baseline_upper_availability_energy_gwh": 0.0,
        "_smallest_raw": np.inf,
        "_smallest_retained": np.inf,
        "_system_floor": np.zeros((len(thresholds), hours), dtype=np.float64),
        "_system_upper": np.zeros((len(thresholds), hours), dtype=np.float64),
        "thresholds": [
            {
                "candidate_threshold": threshold,
                "newly_removed_coefficient_count": 0,
                "retained_coefficient_count": 0,
                "omitted_floor_energy_gwh": 0.0,
                "omitted_upper_energy_gwh": 0.0,
                "max_group_hour_floor_gw": 0.0,
                "max_group_hour_upper_gw": 0.0,
            }
            for threshold in thresholds
        ],
    }


def _accumulate_group(
    resource: dict,
    coefficients: np.ndarray,
    floor: np.ndarray,
    upper: np.ndarray,
    thresholds: tuple[float, ...],
    baseline: float,
    hour_slice: slice,
) -> None:
    positive = coefficients > 0.0
    retained = coefficients >= baseline
    resource["coefficient_count"] += int(coefficients.size)
    resource["raw_positive_coefficient_count"] += int(np.count_nonzero(positive))
    resource["production_retained_coefficient_count"] += int(np.count_nonzero(retained))
    if positive.any():
        resource["_smallest_raw"] = min(
            resource["_smallest_raw"], float(coefficients[positive].min())
        )
    if retained.any():
        resource["_smallest_retained"] = min(
            resource["_smallest_retained"], float(coefficients[retained].min())
        )
    retained_coefficients = np.where(retained, coefficients, 0.0)
    resource["baseline_floor_availability_energy_gwh"] += float(
        retained_coefficients.sum(axis=0) @ floor
    )
    resource["baseline_upper_availability_energy_gwh"] += float(
        retained_coefficients.sum(axis=0) @ upper
    )
    for index, threshold in enumerate(thresholds):
        candidate_retained = coefficients >= threshold
        newly_removed = retained & ~candidate_retained
        removed = np.where(newly_removed, coefficients, 0.0)
        omitted_floor = removed @ floor
        omitted_upper = removed @ upper
        result = resource["thresholds"][index]
        result["newly_removed_coefficient_count"] += int(np.count_nonzero(newly_removed))
        result["retained_coefficient_count"] += int(np.count_nonzero(candidate_retained))
        result["omitted_floor_energy_gwh"] += float(omitted_floor.sum())
        result["omitted_upper_energy_gwh"] += float(omitted_upper.sum())
        result["max_group_hour_floor_gw"] = max(
            result["max_group_hour_floor_gw"], float(omitted_floor.max(initial=0.0))
        )
        result["max_group_hour_upper_gw"] = max(
            result["max_group_hour_upper_gw"], float(omitted_upper.max(initial=0.0))
        )
        resource["_system_floor"][index, hour_slice] += omitted_floor
        resource["_system_upper"][index, hour_slice] += omitted_upper


def _finalize(resource: dict) -> dict:
    retained_count = resource["production_retained_coefficient_count"]
    baseline_floor = resource["baseline_floor_availability_energy_gwh"]
    baseline_upper = resource["baseline_upper_availability_energy_gwh"]
    resource["smallest_raw_positive_cf"] = (
        float(resource.pop("_smallest_raw"))
        if np.isfinite(resource["_smallest_raw"])
        else None
    )
    resource["smallest_production_retained_cf"] = (
        float(resource.pop("_smallest_retained"))
        if np.isfinite(resource["_smallest_retained"])
        else None
    )
    system_floor = resource.pop("_system_floor")
    system_upper = resource.pop("_system_upper")
    for index, result in enumerate(resource["thresholds"]):
        result["newly_removed_fraction_of_production_retained"] = (
            result["newly_removed_coefficient_count"] / retained_count
            if retained_count
            else 0.0
        )
        result["omitted_floor_fraction_of_baseline_floor_availability"] = (
            result["omitted_floor_energy_gwh"] / baseline_floor
            if baseline_floor
            else 0.0
        )
        result["omitted_upper_fraction_of_baseline_upper_availability"] = (
            result["omitted_upper_energy_gwh"] / baseline_upper
            if baseline_upper
            else 0.0
        )
        result["max_system_hour_floor_gw"] = float(
            system_floor[index].max(initial=0.0)
        )
        result["max_system_hour_upper_gw"] = float(
            system_upper[index].max(initial=0.0)
        )
    return resource


def main() -> None:
    args = parse_args()
    if args.hours < 1 or args.start_hour < 0 or args.start_hour + args.hours > 8760:
        raise SystemExit("selected hours must lie within [0, 8760)")
    config = load_model_config(
        "config/optimization_2030.json", "config/scenarios/base.json"
    )
    if config.planning_year != args.planning_year:
        config = config.for_planning_year(args.planning_year)
    data = load_model_data(config)
    baseline = float(config.raw["numerics"]["coefficient_zero_tolerance"])
    thresholds = DEFAULT_THRESHOLDS

    wave = _empty_resource("wave", thresholds, args.hours)
    if data.wave is not None:
        for _, sites in data.wave.sites.groupby("province_code", sort=False):
            positions = sites.index.to_numpy(dtype=np.int64)
            grid_ids = sites.wave_source_grid_id.to_numpy(dtype=np.int64)
            floor = np.zeros(len(sites), dtype=np.float64)
            upper = sites.capacity_upper_gw.to_numpy(dtype=np.float64)
            for local_start in range(0, args.hours, args.chunk_hours):
                local_stop = min(local_start + args.chunk_hours, args.hours)
                coefficients = data.wave.cf.read(
                    grid_ids,
                    args.start_hour + local_start,
                    args.start_hour + local_stop,
                )
                _accumulate_group(
                    wave,
                    coefficients,
                    floor,
                    upper,
                    thresholds,
                    baseline,
                    slice(local_start, local_stop),
                )

    ror = _empty_resource("run_of_river", thresholds, args.hours)
    block = TimeBlock(0, args.start_hour, args.start_hour + args.hours)
    hydro_floor_all = data.hydro_stations.existing_capacity_gw.to_numpy(dtype=np.float64)
    hydro_upper_all = data.hydro_stations.capacity_potential_gw.to_numpy(dtype=np.float64)
    with HydroProfileReader(config, data) as reader:
        hydro = reader.read_linear_block(block)
    for province_position, rows in hydro.ror_station_rows.items():
        if not len(rows):
            continue
        _accumulate_group(
            ror,
            np.asarray(hydro.ror_capacity_factor[province_position], dtype=np.float64),
            hydro_floor_all[rows],
            hydro_upper_all[rows],
            thresholds,
            baseline,
            slice(0, args.hours),
        )

    if data.wave is not None:
        data.wave.cf.close()
    report = {
        "schema_version": "cispo_wave_ror_cf_threshold_audit_v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "planning_year": config.planning_year,
        "start_hour": args.start_hour,
        "hours": args.hours,
        "production_coefficient_zero_tolerance": baseline,
        "resources": [_finalize(wave), _finalize(ror)],
        "scientific_note": (
            "A threshold above the production value changes the physical feasible set; "
            "upper-capacity metrics are conservative error bounds."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
