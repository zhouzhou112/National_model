"""Rebuild only the province fuel-price and generation-cost runtime tables."""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.build_cispo_data_package import DATA_ROOT, build_fuel_prices, load_config


def main() -> None:
    qc: list[dict] = []
    build_fuel_prices(load_config(), qc)
    failures = [row for row in qc if row["status"] == "FAIL"]
    print(
        json.dumps(
            {"data_root": str(DATA_ROOT), "checks": qc, "failures": failures},
            ensure_ascii=False,
            indent=2,
        )
    )
    if failures:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
