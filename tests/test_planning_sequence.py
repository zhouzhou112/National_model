from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from cispo_model.config import load_model_config
from cispo_model.planning_state import (
    PlanningState,
    STATE_COLUMNS,
    stable_asset_id,
    write_planning_state,
)


class PlanningSequenceTests(unittest.TestCase):
    def test_year_specific_boundaries_are_exact(self):
        base = load_model_config()
        expected = {2030: 2025, 2040: 2030, 2050: 2040, 2060: 2050}
        self.assertEqual(base.planning_years, tuple(expected))
        for planning_year, boundary_year in expected.items():
            config = base.for_planning_year(planning_year)
            self.assertEqual(config.planning_year, planning_year)
            self.assertEqual(config.boundary_year, boundary_year)
            self.assertEqual(
                config.raw["planning_interval_years"], planning_year - boundary_year
            )

    def test_capacity_cohort_expires_by_technology_lifetime(self):
        config = load_model_config().for_planning_year(2030)
        asset_id = stable_asset_id(11, "battery")
        new_cohorts = pd.DataFrame(
            [
                {
                    "asset_class": "storage",
                    "asset_id": asset_id,
                    "province_code": 11,
                    "technology": "battery",
                    "build_year": 2030,
                    "retire_year": 2045,
                    "capacity_delta": 2.5,
                    "unit": "GW",
                    "action": "new_build",
                }
            ],
            columns=STATE_COLUMNS,
        )
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = write_planning_state(
                Path(temporary),
                config=config,
                previous_state=PlanningState.empty(2025),
                new_cohorts=new_cohorts,
                source_solution_qc="solution_qc.json",
            )
            state = PlanningState.load(state_dir, expected_boundary_year=2030)
            self.assertAlmostEqual(
                state.active_adjustment(
                    "storage", [asset_id], planning_year=2040, unit="GW"
                )[0],
                2.5,
            )
            self.assertAlmostEqual(
                state.active_adjustment(
                    "storage", [asset_id], planning_year=2050, unit="GW"
                )[0],
                0.0,
            )
            with self.assertRaises(ValueError):
                PlanningState.load(state_dir, expected_boundary_year=2040)


if __name__ == "__main__":
    unittest.main()
