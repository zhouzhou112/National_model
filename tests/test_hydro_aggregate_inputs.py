from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

from scripts.validate_provincial_aggregate_hydro_inputs import (
    PROJECT_ROOT,
    build_audit,
)


class ProvincialAggregateHydroInputTests(unittest.TestCase):
    def test_current_data_closes_to_380_gw(self) -> None:
        data_root = Path(
            os.environ.get("CISPO_DATA_ROOT", str(PROJECT_ROOT / "data"))
        )
        report = build_audit(data_root)
        self.assertEqual(report["status"], "PASS", report["failures"])
        self.assertAlmostEqual(
            report["harmonized_conventional_capacity_gw"],
            380.0,
            places=6,
        )
        self.assertAlmostEqual(
            report["identified_station_capacity_gw"]
            + report["provincial_aggregate_capacity_gw"],
            380.0,
            places=6,
        )
        json.dumps(report)


if __name__ == "__main__":
    unittest.main()
