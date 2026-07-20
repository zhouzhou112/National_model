from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from cispo_model.config import load_model_config
from cispo_model.data import DAC_TECHS, STORAGE_TECHS, THERMAL_TECHS
from cispo_model.planning_state import (
    PlanningState,
    STATE_COLUMNS,
    export_solution_planning_state,
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
            self.assertTrue((state_dir / "state_transition_summary.csv").is_file())
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

    def test_state_rejects_modified_source_solve_or_qc(self):
        config = load_model_config().for_planning_year(2030)
        new_cohorts = pd.DataFrame(columns=STATE_COLUMNS)
        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary)
            qc_path = output_dir / "solution_qc.json"
            solve_path = output_dir / "solve_report.json"
            qc_path.write_text('{"status":"PASS"}\n', encoding="utf-8")
            solve_path.write_text(
                '{"status":"OPTIMAL","result_use":"SCIENTIFIC_PRODUCTION",'
                '"planning_year":2030}\n',
                encoding="utf-8",
            )
            state_dir = write_planning_state(
                output_dir,
                config=config,
                previous_state=PlanningState.empty(2025),
                new_cohorts=new_cohorts,
                source_solution_qc="solution_qc.json",
            )
            PlanningState.load(state_dir, expected_boundary_year=2030)
            solve_path.write_text(
                '{"status":"SUBOPTIMAL","result_use":"SCIENTIFIC_PRODUCTION",'
                '"planning_year":2030}\n',
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                PlanningState.load(state_dir, expected_boundary_year=2030)

    def test_solution_export_maps_capacity_decisions_to_checksummed_cohorts(self):
        class Value:
            def __init__(self, values):
                self.X = np.asarray(values, dtype=float)

        config = load_model_config().for_planning_year(2030)
        thermal_new = np.zeros((1, len(THERMAL_TECHS)))
        thermal_new[0, 0] = 0.4
        storage_new = np.zeros((1, len(STORAGE_TECHS)))
        storage_new[0, 0] = 0.2
        dac_new = np.zeros((1, len(DAC_TECHS)))
        dac_new[0, 0] = 0.05
        variables = {
            "vre_new": Value([0.3]),
            "thermal_new": Value(thermal_new),
            "thermal_retrofit_to_ccs": Value(np.zeros((1, 5))),
            "hydro_new": Value([0.1]),
            "storage_new": Value(storage_new),
            "line_new": Value([0.6]),
            "dac_new": Value(dac_new),
        }
        ccs_pairs = (
            ("coal", "coalccs"), ("cchp", "cchpccs"),
            ("gas", "gasccs"), ("gchp", "gchpccs"),
            ("bio", "bioccs"),
        )
        artifacts = SimpleNamespace(
            variables=variables,
            index={
                "vre_asset_ids": [stable_asset_id("G1", "onwind")],
                "province_codes": [11],
                "thermal_index": {t: i for i, t in enumerate(THERMAL_TECHS)},
                "ccs_pairs": ccs_pairs,
                "storage_index": {t: i for i, t in enumerate(STORAGE_TECHS)},
                "dac_index": {t: i for i, t in enumerate(DAC_TECHS)},
            },
        )
        data = SimpleNamespace(
            vre_sites=pd.DataFrame(
                [{"grid_uid": "G1", "province_code": 11, "technology": "onwind"}]
            ),
            hydro_stations=pd.DataFrame(
                [{"hydrochn_row_id": "H1", "province_code": 11}]
            ),
            lines=pd.DataFrame(
                [{"line_id": "L1", "preset_technology": "AC_500kV"}]
            ),
            dac=pd.DataFrame(
                {
                    "technology": list(DAC_TECHS),
                    "lifetime_years": [20] * len(DAC_TECHS),
                }
            ),
            planning_state=PlanningState.empty(2025),
        )
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = export_solution_planning_state(
                artifacts, data, config, Path(temporary)
            )
            state = PlanningState.load(state_dir, expected_boundary_year=2030)
            self.assertEqual(
                set(state.cohorts.asset_class),
                {"vre", "thermal", "hydro", "storage", "interprovincial_transmission", "dac"},
            )
            self.assertAlmostEqual(
                float(state.cohorts.capacity_delta.sum()), 1.65, places=9
            )


if __name__ == "__main__":
    unittest.main()
