from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cispo_model.config import load_model_config
from scripts.run_cispo_sensitivity_suite import (
    PROJECT_ROOT,
    load_scenario_catalog,
    select_scenarios,
)


class SensitivitySuiteTests(unittest.TestCase):
    def test_catalog_configs_are_valid_and_keep_base_v2g_separate(self):
        catalog = load_scenario_catalog(
            PROJECT_ROOT / "config" / "scenarios" / "scenario_catalog.json"
        )
        implemented = {row["scenario_id"]: row for row in catalog["implemented"]}
        self.assertEqual(
            set(implemented),
            {
                "base",
                "flexible_load_v1",
                "flexible_load_state_v2",
                "flexible_load_v2g_v1",
                "flexible_load_comfort_v3",
                "flexible_load_comfort_v3_v2g_5pct",
                "wave_energy_medium_v1",
                "wave_energy_medium_v1_flexible_load_v1",
                "wave_energy_medium_v1_flexible_load_comfort_v3",
            },
        )

        base = load_model_config(scenario_path=implemented["base"]["config_path"])
        v1 = load_model_config(
            scenario_path=implemented["flexible_load_v1"]["config_path"]
        )
        v2g = load_model_config(
            scenario_path=implemented["flexible_load_v2g_v1"]["config_path"]
        )
        state = load_model_config(
            scenario_path=implemented["flexible_load_state_v2"]["config_path"]
        )
        comfort = load_model_config(
            scenario_path=implemented["flexible_load_comfort_v3"]["config_path"]
        )
        comfort_v2g = load_model_config(
            scenario_path=implemented[
                "flexible_load_comfort_v3_v2g_5pct"
            ]["config_path"]
        )
        wave = load_model_config(
            scenario_path=implemented["wave_energy_medium_v1"]["config_path"]
        )
        combined = load_model_config(
            scenario_path=implemented[
                "wave_energy_medium_v1_flexible_load_v1"
            ]["config_path"]
        )
        combined_comfort = load_model_config(
            scenario_path=implemented[
                "wave_energy_medium_v1_flexible_load_comfort_v3"
            ]["config_path"]
        )
        self.assertTrue(wave.raw["features"]["wave_energy"])
        self.assertFalse(base.raw["features"]["wave_energy"])
        self.assertEqual(
            wave.raw["wave_energy"]["profile_year_by_planning_year"]["2060"],
            2050,
        )
        self.assertFalse(base.raw["features"]["flexible_load"])
        self.assertTrue(v1.raw["features"]["flexible_load"])
        self.assertFalse(v1.raw["flexible_load"]["ev_v2g"]["enabled"])
        self.assertEqual(
            state.raw["flexible_load"]["formulation"], "state_envelope_v2"
        )
        self.assertFalse(state.raw["flexible_load"]["ev_v2g"]["enabled"])
        self.assertTrue(v2g.raw["flexible_load"]["ev_v2g"]["enabled"])
        self.assertFalse(comfort.raw["flexible_load"]["ev_v2g"]["enabled"])
        self.assertTrue(comfort_v2g.raw["flexible_load"]["ev_v2g"]["enabled"])
        self.assertTrue(combined.raw["features"]["wave_energy"])
        self.assertTrue(combined.raw["features"]["flexible_load"])
        self.assertFalse(combined.raw["flexible_load"]["ev_v2g"]["enabled"])
        self.assertTrue(combined_comfort.raw["features"]["wave_energy"])
        self.assertTrue(combined_comfort.raw["features"]["flexible_load"])
        self.assertEqual(
            combined_comfort.raw["flexible_load"]["formulation"],
            "comfort_envelope_v3",
        )

    def test_planned_scenario_cannot_be_selected(self):
        catalog = load_scenario_catalog(
            PROJECT_ROOT / "config" / "scenarios" / "scenario_catalog.json"
        )
        with self.assertRaisesRegex(ValueError, "planned_not_runnable"):
            select_scenarios(catalog, ["complementarity_point"])

    def test_dry_run_writes_isolated_suite_reports(self):
        with tempfile.TemporaryDirectory() as temporary:
            output_root = Path(temporary) / "suite"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(PROJECT_ROOT / "scripts" / "run_cispo_sensitivity_suite.py"),
                    "--scenario",
                    "base",
                    "--scenario",
                    "flexible_load_v1",
                    "--diagnostic-hours",
                    "1",
                    "--output-root",
                    str(output_root),
                    "--dry-run",
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(
                (output_root / "sensitivity_suite_report.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(report["status"], "DRY_RUN")
            self.assertEqual(
                report["scenario_ids"], ["base", "flexible_load_v1"]
            )
            self.assertEqual(
                [row["status"] for row in report["runs"]],
                ["DRY_RUN", "DRY_RUN"],
            )
            for scenario_id in report["scenario_ids"]:
                sequence = json.loads(
                    (
                        output_root
                        / scenario_id
                        / "sequence_report.json"
                    ).read_text(encoding="utf-8")
                )
                self.assertEqual(sequence["status"], "DRY_RUN")
                self.assertEqual(sequence["scenario_id"], scenario_id)
                self.assertEqual(sequence["diagnostic_hours"], 1)

            resume = subprocess.run(
                [
                    sys.executable,
                    str(PROJECT_ROOT / "scripts" / "run_cispo_sensitivity_suite.py"),
                    "--scenario",
                    "base",
                    "--scenario",
                    "flexible_load_v1",
                    "--diagnostic-hours",
                    "1",
                    "--output-root",
                    str(output_root),
                    "--resume",
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(resume.returncode, 0)
            self.assertIn("mismatched fields: mode", resume.stderr)


if __name__ == "__main__":
    unittest.main()
