"""Extract the immutable non-thermal, non-EV baseline load from model-ready load data.

The input contract is the current CISPO model-ready hourly load table.  The
output retains only the provincial/time index and ``base_residual_gw`` so it
cannot be confused with total demand or a demand-flexibility scenario.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path


REQUIRED_COLUMNS = (
    "province_code",
    "province_name_zh",
    "year",
    "hour_index",
    "datetime_bj",
    "base_residual_gw",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract base_residual_gw from the current model-ready load table."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--qa-output", required=True, type=Path)
    parser.add_argument("--annual-output", required=True, type=Path)
    args = parser.parse_args()

    if not args.input.is_file():
        raise FileNotFoundError(args.input)
    for path in (args.output, args.qa_output, args.annual_output):
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite existing archive output: {path}")

    group_hours: dict[tuple[str, int], int] = defaultdict(int)
    annual_gwh: dict[tuple[str, str, int], float] = defaultdict(float)
    rows = 0
    minimum = float("inf")
    maximum = float("-inf")

    with gzip.open(args.input, "rt", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Input is missing required columns: {missing}")

        with gzip.open(args.output, "wt", encoding="utf-8-sig", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
            for row in reader:
                value = float(row["base_residual_gw"])
                if value < 0:
                    raise ValueError(
                        f"Negative base_residual_gw at province={row['province_code']} "
                        f"year={row['year']} hour={row['hour_index']}: {value}"
                    )
                province_code = row["province_code"]
                province_name = row["province_name_zh"]
                year = int(row["year"])
                writer.writerow({column: row[column] for column in REQUIRED_COLUMNS})
                group_hours[(province_code, year)] += 1
                annual_gwh[(province_code, province_name, year)] += value
                rows += 1
                minimum = min(minimum, value)
                maximum = max(maximum, value)

    expected_groups = 31 * 5
    invalid_groups = {
        f"{province_code}-{year}": hours
        for (province_code, year), hours in group_hours.items()
        if hours != 8760
    }
    if len(group_hours) != expected_groups or invalid_groups:
        raise ValueError(
            f"Expected {expected_groups} province-year groups with 8760 hours; "
            f"found {len(group_hours)}, invalid={invalid_groups}"
        )
    if rows != expected_groups * 8760:
        raise ValueError(f"Expected {expected_groups * 8760} rows, found {rows}")

    with args.annual_output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=("province_code", "province_name_zh", "year", "base_residual_energy_gwh"),
        )
        writer.writeheader()
        for key in sorted(annual_gwh, key=lambda item: (int(item[0]), item[2])):
            province_code, province_name, year = key
            writer.writerow(
                {
                    "province_code": province_code,
                    "province_name_zh": province_name,
                    "year": year,
                    "base_residual_energy_gwh": f"{annual_gwh[key]:.12f}",
                }
            )

    qa = {
        "status": "PASS",
        "definition": (
            "base_residual_gw excludes heating_gw, cooling_gw and ev_gw; it is "
            "not total demand and does not include any flexible-load optimization."
        ),
        "input": str(args.input.resolve()),
        "input_sha256": sha256(args.input),
        "output": str(args.output.resolve()),
        "output_sha256": sha256(args.output),
        "rows": rows,
        "province_year_groups": len(group_hours),
        "hours_per_group_min": min(group_hours.values()),
        "hours_per_group_max": max(group_hours.values()),
        "minimum_base_residual_gw": minimum,
        "maximum_base_residual_gw": maximum,
        "annual_summary": str(args.annual_output.resolve()),
        "annual_summary_sha256": sha256(args.annual_output),
    }
    args.qa_output.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
