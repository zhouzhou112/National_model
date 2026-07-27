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
)


class SensitivitySuiteTests(unittest.TestCase):
    def test_catalog_contains_only_wave_base_and_v3_v2g_overlay(self):
        catalog = load_scenario_catalog(
            PROJECT_ROOT / "config" / "scenarios" / "scenario_catalog.json"
        )
        implemented = {row["scenario_id"]: row for row in catalog["implemented"]}
        self.assertEqual(
            set(implemented),
            {
                "base",
                "flexible_load_comfort_v3_v2g_5pct",
            },
        )

        base = load_model_config(scenario_path=implemented["base"]["config_path"])
        comfort_v2g = load_model_config(
            scenario_path=implemented[
                "flexible_load_comfort_v3_v2g_5pct"
            ]["config_path"]
        )
        self.assertTrue(base.raw["features"]["wave_energy"])
        self.assertEqual(
            base.raw["wave_energy"]["profile_year_by_planning_year"]["2060"],
            2050,
        )
        self.assertFalse(base.raw["features"]["flexible_load"])
        self.assertTrue(comfort_v2g.raw["features"]["wave_energy"])
        self.assertTrue(comfort_v2g.raw["features"]["flexible_load"])
        self.assertTrue(comfort_v2g.raw["flexible_load"]["ev_v2g"]["enabled"])
        self.assertEqual(
            comfort_v2g.raw["flexible_load"]["formulation"],
            "comfort_envelope_v3",
        )

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
                    "flexible_load_comfort_v3_v2g_5pct",
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
                report["scenario_ids"], ["base", "flexible_load_comfort_v3_v2g_5pct"]
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
                    "flexible_load_comfort_v3_v2g_5pct",
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
