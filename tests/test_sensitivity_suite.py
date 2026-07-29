from __future__ import annotations

import csv
import json
import os
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
    def test_catalog_contains_implemented_base_flex_and_hydro_overlays(self):
        catalog = load_scenario_catalog(
            PROJECT_ROOT / "config" / "scenarios" / "scenario_catalog.json"
        )
        implemented = {row["scenario_id"]: row for row in catalog["implemented"]}
        self.assertEqual(
            set(implemented),
            {
                "base",
                "flexible_load_comfort_v3_v2g_5pct",
                "hydro_aggregate_flex_v1",
                "flexible_load_comfort_v4_v1g",
                "flexible_load_comfort_v4_v2g_sensitivity",
                "phs_power_energy_separated_central_v1",
                "phs_power_energy_separated_low_energy_cost_v1",
                "phs_power_energy_separated_high_energy_cost_v1",
            },
        )

        base = load_model_config(scenario_path=implemented["base"]["config_path"])
        comfort_v2g = load_model_config(
            scenario_path=implemented[
                "flexible_load_comfort_v3_v2g_5pct"
            ]["config_path"]
        )
        hydro_flex = load_model_config(
            scenario_path=implemented["hydro_aggregate_flex_v1"]["config_path"]
        )
        phs_central = load_model_config(
            scenario_path=implemented[
                "phs_power_energy_separated_central_v1"
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
        self.assertEqual(
            hydro_flex.raw["hydro"]["provincial_aggregate_mode"],
            "fixed_existing_monthly_energy_budget_v2",
        )
        self.assertEqual(
            hydro_flex.raw["hydro"]["provincial_aggregate_up_reserve_credit"],
            1.0,
        )
        self.assertEqual(
            hydro_flex.raw["hydro"]["provincial_aggregate_down_reserve_credit"],
            1.0,
        )
        self.assertEqual(
            hydro_flex.raw["hydro"]["provincial_aggregate_inertia_seconds"],
            3.0,
        )
        self.assertEqual(
            hydro_flex.raw["hydro"]["provincial_aggregate_capacity_credit"],
            0.0,
        )
        self.assertEqual(
            phs_central.raw["storage_design"]["phs_energy_capacity_mode"],
            "independent_power_energy_v1",
        )
        with (
            Path(os.environ.get("CISPO_DATA_ROOT", str(PROJECT_ROOT / "data")))
            / "technology"
            / "technology_capex_by_year.csv"
        ).open(encoding="utf-8-sig", newline="") as handle:
            phs_2030_capex = next(
                float(row["capex_yuan_per_kw"])
                for row in csv.DictReader(handle)
                if row["technology"] == "phs" and row["year"] == "2030"
            )
        self.assertAlmostEqual(
            phs_central.raw["storage_design"][
                "phs_power_capex_yuan_per_kw_by_planning_year"
            ]["2030"]
            + 8.0
            * phs_central.raw["storage_design"][
                "phs_energy_capex_yuan_per_kwh_by_planning_year"
            ]["2030"],
            phs_2030_capex,
            places=5,
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

    def test_phs_power_energy_template_fails_closed_without_cost_split(self):
        with self.assertRaisesRegex(
            ValueError,
            "values must be sourced positive numbers",
        ):
            load_model_config(
                scenario_path=(
                    PROJECT_ROOT
                    / "config"
                    / "scenarios"
                    / "phs_power_energy_separated_template_v1.json"
                )
            )

    def test_phs_cost_calibrated_scenarios_close_to_active_8h_capex(self):
        base = load_model_config()
        base_storage = base.raw["storage_design"]
        self.assertEqual(
            base_storage["phs_energy_capacity_mode"],
            "fixed_duration_v1",
        )
        expected_shares = {
            "low_energy_cost": 0.30,
            "central": 0.365,
            "high_energy_cost": 0.45,
        }
        active_total = {
            "2030": 5281.06104,
            "2040": 4758.9789599999995,
            "2050": 4758.9789599999995,
            "2060": 4256.97696,
        }
        for case, share in expected_shares.items():
            scenario = load_model_config(
                scenario_path=(
                    PROJECT_ROOT
                    / "config"
                    / "scenarios"
                    / f"phs_power_energy_separated_{case}_v1.json"
                )
            )
            storage = scenario.raw["storage_design"]
            self.assertEqual(
                storage["phs_energy_capacity_mode"],
                "independent_power_energy_v1",
            )
            for year, total in active_total.items():
                power = storage[
                    "phs_power_capex_yuan_per_kw_by_planning_year"
                ][year]
                energy = storage[
                    "phs_energy_capex_yuan_per_kwh_by_planning_year"
                ][year]
                self.assertAlmostEqual(power + 8.0 * energy, total, places=5)
                self.assertAlmostEqual(8.0 * energy / total, share, places=8)


if __name__ == "__main__":
    unittest.main()
