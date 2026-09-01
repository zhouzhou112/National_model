"""Audit the physical error budget of VRE capacity-factor sparsification.

The production model already replaces hourly VRE coefficients below
``numerics.coefficient_zero_tolerance`` with exact zero.  This script measures
the incremental effect of larger candidate thresholds without building or
solving a Gurobi model.  All error metrics use the actual site capacity bounds:

* ``capacity_floor_gw`` gives the omitted availability for mandatory capacity;
* ``capacity_upper_gw`` gives a conservative feasible-set error bound.

The source Zarr stores are read-only and scanned in bounded-memory chunks.
"""
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


DEFAULT_THRESHOLDS = (1e-6, 2e-6, 5e-6, 1e-5, 2e-5, 5e-5, 1e-4)


def _parse_thresholds(value: str) -> tuple[float, ...]:
    thresholds = tuple(sorted({float(part) for part in value.split(",")}))
    if not thresholds or thresholds[0] <= 0.0 or thresholds[-1] > 1.0:
        raise argparse.ArgumentTypeError("thresholds must lie in (0, 1]")
    return thresholds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/optimization_2030.json")
    parser.add_argument("--scenario-config", default="config/scenarios/base.json")
    parser.add_argument("--planning-year", type=int, default=2030)
    parser.add_argument("--start-hour", type=int, default=0)
    parser.add_argument("--hours", type=int, default=8760)
    parser.add_argument("--chunk-hours", type=int, default=168)
    parser.add_argument(
        "--thresholds",
        type=_parse_thresholds,
        default=DEFAULT_THRESHOLDS,
        help="comma-separated candidate CF thresholds",
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.hours < 1 or args.start_hour < 0 or args.start_hour + args.hours > 8760:
        raise SystemExit("selected hours must lie within [0, 8760)")
    if args.chunk_hours < 1:
        raise SystemExit("--chunk-hours must be positive")

    config = load_model_config(args.config, args.scenario_config)
    if config.planning_year != args.planning_year:
        config = config.for_planning_year(args.planning_year)
    data = load_model_data(config)
    baseline = float(config.raw["numerics"]["coefficient_zero_tolerance"])
    thresholds = tuple(float(value) for value in args.thresholds)
    if min(thresholds) < baseline:
        raise SystemExit(
            f"candidate thresholds must be >= production baseline {baseline:g}"
        )

    threshold_count = len(thresholds)
    metrics = [
        {
            "candidate_threshold": threshold,
            "newly_removed_coefficient_count": 0,
            "retained_coefficient_count": 0,
            "omitted_floor_energy_gwh": 0.0,
            "omitted_upper_energy_gwh": 0.0,
            "max_province_technology_hour_floor_gw": 0.0,
            "max_province_technology_hour_upper_gw": 0.0,
        }
        for threshold in thresholds
    ]
    system_floor = np.zeros((threshold_count, args.hours), dtype=np.float64)
    system_upper = np.zeros((threshold_count, args.hours), dtype=np.float64)
    baseline_floor_energy = 0.0
    baseline_upper_energy = 0.0
    raw_positive_count = 0
    baseline_retained_count = 0
    total_coefficient_count = 0
    smallest_positive = np.inf
    smallest_baseline_retained = np.inf
    by_technology: dict[str, list[dict[str, float | int]]] = {}

    grouped = data.vre_sites.groupby(["province_code", "technology"], sort=False)
    for (_, technology), province_technology in grouped:
        technology = str(technology)
        technology_metrics = by_technology.setdefault(
            technology,
            [
                {
                    "newly_removed_coefficient_count": 0,
                    "omitted_floor_energy_gwh": 0.0,
                    "omitted_upper_energy_gwh": 0.0,
                }
                for _ in thresholds
            ],
        )
        for local_start in range(0, args.hours, args.chunk_hours):
            local_stop = min(local_start + args.chunk_hours, args.hours)
            absolute_start = args.start_hour + local_start
            absolute_stop = args.start_hour + local_stop
            group_floor = np.zeros((threshold_count, local_stop - local_start))
            group_upper = np.zeros((threshold_count, local_stop - local_start))
            for source, source_rows in province_technology.groupby(
                "cf_source_technology", sort=False
            ):
                coefficients = data.cf.read(
                    str(source),
                    source_rows.cf_grid_id.to_numpy(dtype=np.int64),
                    absolute_start,
                    absolute_stop,
                )
                floor = source_rows.capacity_floor_gw.to_numpy(dtype=np.float64)
                upper = source_rows.capacity_upper_gw.to_numpy(dtype=np.float64)
                positive = coefficients > 0.0
                retained = coefficients >= baseline
                total_coefficient_count += int(coefficients.size)
                raw_positive_count += int(np.count_nonzero(positive))
                baseline_retained_count += int(np.count_nonzero(retained))
                if positive.any():
                    smallest_positive = min(
                        smallest_positive, float(coefficients[positive].min())
                    )
                if retained.any():
                    smallest_baseline_retained = min(
                        smallest_baseline_retained,
                        float(coefficients[retained].min()),
                    )
                retained_coefficients = np.where(retained, coefficients, 0.0)
                baseline_floor_energy += float(retained_coefficients.sum(axis=0) @ floor)
                baseline_upper_energy += float(retained_coefficients.sum(axis=0) @ upper)

                for index, threshold in enumerate(thresholds):
                    candidate_retained = coefficients >= threshold
                    newly_removed = retained & ~candidate_retained
                    removed_coefficients = np.where(newly_removed, coefficients, 0.0)
                    newly_removed_count = int(np.count_nonzero(newly_removed))
                    retained_count = int(np.count_nonzero(candidate_retained))
                    omitted_floor = removed_coefficients @ floor
                    omitted_upper = removed_coefficients @ upper
                    metrics[index]["newly_removed_coefficient_count"] += newly_removed_count
                    metrics[index]["retained_coefficient_count"] += retained_count
                    metrics[index]["omitted_floor_energy_gwh"] += float(omitted_floor.sum())
                    metrics[index]["omitted_upper_energy_gwh"] += float(omitted_upper.sum())
                    technology_metrics[index]["newly_removed_coefficient_count"] += newly_removed_count
                    technology_metrics[index]["omitted_floor_energy_gwh"] += float(omitted_floor.sum())
                    technology_metrics[index]["omitted_upper_energy_gwh"] += float(omitted_upper.sum())
                    group_floor[index] += omitted_floor
                    group_upper[index] += omitted_upper

            for index in range(threshold_count):
                metrics[index]["max_province_technology_hour_floor_gw"] = max(
                    float(metrics[index]["max_province_technology_hour_floor_gw"]),
                    float(group_floor[index].max(initial=0.0)),
                )
                metrics[index]["max_province_technology_hour_upper_gw"] = max(
                    float(metrics[index]["max_province_technology_hour_upper_gw"]),
                    float(group_upper[index].max(initial=0.0)),
                )
                system_floor[index, local_start:local_stop] += group_floor[index]
                system_upper[index, local_start:local_stop] += group_upper[index]

    load_energy = float(
        data.load_gw[:, args.start_hour : args.start_hour + args.hours].sum()
    )
    for index, result in enumerate(metrics):
        result["newly_removed_fraction_of_production_retained"] = (
            float(result["newly_removed_coefficient_count"]) / baseline_retained_count
            if baseline_retained_count
            else 0.0
        )
        result["omitted_floor_fraction_of_baseline_floor_availability"] = (
            float(result["omitted_floor_energy_gwh"]) / baseline_floor_energy
            if baseline_floor_energy
            else 0.0
        )
        result["omitted_upper_fraction_of_baseline_upper_availability"] = (
            float(result["omitted_upper_energy_gwh"]) / baseline_upper_energy
            if baseline_upper_energy
            else 0.0
        )
        result["omitted_upper_energy_fraction_of_load"] = (
            float(result["omitted_upper_energy_gwh"]) / load_energy
            if load_energy
            else 0.0
        )
        result["max_system_hour_floor_gw"] = float(system_floor[index].max(initial=0.0))
        result["max_system_hour_upper_gw"] = float(system_upper[index].max(initial=0.0))
        result["technology_breakdown"] = {
            technology: values[index] for technology, values in by_technology.items()
        }

    report = {
        "schema_version": "cispo_vre_cf_threshold_audit_v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "planning_year": config.planning_year,
        "weather_year": config.weather_year,
        "start_hour": args.start_hour,
        "hours": args.hours,
        "production_coefficient_zero_tolerance": baseline,
        "site_count": int(len(data.vre_sites)),
        "coefficient_count": total_coefficient_count,
        "raw_positive_coefficient_count": raw_positive_count,
        "production_retained_coefficient_count": baseline_retained_count,
        "smallest_raw_positive_cf": (
            float(smallest_positive) if np.isfinite(smallest_positive) else None
        ),
        "smallest_production_retained_cf": (
            float(smallest_baseline_retained)
            if np.isfinite(smallest_baseline_retained)
            else None
        ),
        "baseline_floor_availability_energy_gwh": baseline_floor_energy,
        "baseline_upper_availability_energy_gwh": baseline_upper_energy,
        "selected_load_energy_gwh": load_energy,
        "capacity_floor_total_gw": float(data.vre_sites.capacity_floor_gw.sum()),
        "capacity_upper_total_gw": float(data.vre_sites.capacity_upper_gw.sum()),
        "thresholds": metrics,
        "interpretation": {
            "newly_removed": "production-retained CF >= baseline and < candidate threshold",
            "floor_error": "availability removed at mandatory VRE capacity floors",
            "upper_error": "conservative availability loss at independent site capacity upper bounds",
            "scientific_note": (
                "Any candidate above the production threshold changes the physical feasible set; "
                "it is not an algebraically equivalent scaling."
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
