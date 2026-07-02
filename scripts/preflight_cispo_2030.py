"""Run full 2030/8760 CISPO input and scale preflight."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cispo_model.config import ROOT, load_model_config
from cispo_model.data import load_model_data
from cispo_model.preflight import run_preflight


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/optimization_2030.json")
    parser.add_argument(
        "--output",
        default="outputs/preflight_2030/preflight_report.json",
    )
    args = parser.parse_args()
    config = load_model_config(args.config)
    data = load_model_data(config)
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    report = run_preflight(config, data, output)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
