from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from cispo_model.result_dashboard import (
    build_result_dashboard,
    collect_result_dashboard,
)


class ResultDashboardTests(unittest.TestCase):
    def _write_fixture(
        self,
        root: Path,
        *,
        result_use: str = "TEST_ONLY_TRUNCATED_HORIZON",
        optimization_hours: int = 168,
        period_baseline_load_gwh: float = 100.0,
    ) -> None:
        (root / "solve_report.json").write_text(
            json.dumps(
                {
                    "status": "OPTIMAL",
                    "runtime_seconds": 12.5,
                    "objective_value_million_cny": 150.0,
                    "iteration_counts": {"barrier": 42},
                    "runtime_memory": {"peak_process_tree_rss_gib": 3.5},
                }
            ),
            encoding="utf-8",
        )
        (root / "solution_qc.json").write_text(
            json.dumps(
                {
                    "status": "PASS",
                    "objective_value_million_cny": 150.0,
                    "hard_checks": {
                        "power_balance": True,
                        "carbon": True,
                    },
                    "total_v5_firm_capacity_credit_gw": 2.0,
                    "minimum_capacity_margin_gw": 0.0,
                    "minimum_up_reserve_margin_gw": 0.1,
                    "minimum_down_reserve_margin_gw": 0.2,
                    "minimum_inertia_margin_gw_s": 0.3,
                }
            ),
            encoding="utf-8",
        )
        (root / "run_summary.json").write_text(
            json.dumps(
                {
                    "planning_year": 2030,
                    "scenario_id": "flex_integrated_v5_central",
                    "scenario_family": "integrated_demand_flexibility",
                    "optimization_hours": optimization_hours,
                    "configured_hours": 8760,
                    "result_use": result_use,
                    "full_year_reference_baseline_load_gwh": 1000.0,
                    "period_baseline_load_gwh": period_baseline_load_gwh,
                    "period_load_gwh": period_baseline_load_gwh + 1.0,
                    "period_baseline_peak_load_gw": 20.0,
                    "period_effective_peak_load_gw": 19.0,
                    "period_generation_gwh": 110.0,
                    "period_vre_curtailment_gwh": 3.0,
                    "period_storage_charge_gwh": 4.0,
                    "period_storage_discharge_gwh": 3.0,
                }
            ),
            encoding="utf-8",
        )
        pd.DataFrame(
            [
                {
                    "cost_component": "vre_investment",
                    "value_million_cny_model_accounting_period": 120.0,
                    "accounting_scope": "ANNUALIZED_PLANNING_COST",
                },
                {
                    "cost_component": "operating_fuel",
                    "value_million_cny_model_accounting_period": 30.0,
                    "accounting_scope": "SELECTED_HORIZON_OPERATION_COST",
                },
                {
                    "cost_component": "annual_operation",
                    "value_million_cny_model_accounting_period": 30.0,
                    "accounting_scope": "COMPOSITE_SEE_COMPONENT_ROWS",
                },
            ]
        ).to_csv(root / "cost_components.csv", index=False)
        pd.DataFrame(
            [
                {
                    "asset_group": "generation",
                    "technology": "onwind",
                    "unit": "GW",
                    "capacity": 10.0,
                    "new_capacity": 5.0,
                },
                {
                    "asset_group": "generation",
                    "technology": "upv",
                    "unit": "GW",
                    "capacity": 8.0,
                    "new_capacity": 2.0,
                },
            ]
        ).to_csv(root / "annual_capacity_by_technology.csv", index=False)
        pd.DataFrame(
            [
                {"technology": "onwind", "generation_gwh": 60.0},
                {"technology": "upv", "generation_gwh": 40.0},
            ]
        ).to_csv(root / "annual_generation_by_technology.csv", index=False)
        pd.DataFrame(
            [
                {
                    "contracted_heating_flexibility_gw": 1.0,
                    "contracted_cooling_flexibility_gw": 2.0,
                    "contracted_ev_v1g_flexibility_gw": 3.0,
                    "contracted_ev_v2g_flexibility_gw": 4.0,
                    "ev_v2g_charge_gwh": 0.5,
                    "ev_v2g_discharge_gwh": 0.4,
                }
            ]
        ).to_csv(root / "annual_flexible_load_by_province.csv", index=False)
        pd.DataFrame(
            [
                {
                    "technology": "battery",
                    "power_capacity_gw": 5.0,
                    "energy_capacity_gwh": 20.0,
                    "charge_gwh": 4.0,
                    "discharge_gwh": 3.0,
                }
            ]
        ).to_csv(root / "annual_storage_operation_by_technology.csv", index=False)
        (root / "annual_carbon_ccs.json").write_text(
            json.dumps(
                {
                    "accounting_scope": "SELECTED_HORIZON_ANNUAL_FLOW_SCALED",
                    "configured_hours": 8760,
                    "annual_net_emissions_mtco2": 7.0,
                    "selected_horizon_carbon_limit_mtco2": 8.0,
                }
            ),
            encoding="utf-8",
        )

    def test_truncated_gate_separates_cost_intensities(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_fixture(root)
            payload = build_result_dashboard(root)
            costs = payload["cost_accounting"]

            self.assertAlmostEqual(
                costs["annualized_planning_cost_intensity_cny_per_kwh"],
                0.12,
            )
            self.assertAlmostEqual(
                costs["selected_horizon_operating_cost_intensity_cny_per_kwh"],
                0.30,
            )
            self.assertIsNone(
                costs["scientific_full_year_system_cost_intensity_cny_per_kwh"]
            )
            self.assertEqual(
                costs["composite_operation_rollup_million_cny_excluded_from_sum"],
                30.0,
            )
            self.assertAlmostEqual(
                costs["objective_reconstruction_residual_million_cny"],
                0.0,
            )
            self.assertTrue((root / "result_dashboard_summary.json").is_file())
            self.assertTrue((root / "result_analysis_metrics.csv").is_file())
            svg = root / "visualizations" / "core_result_dashboard.svg"
            self.assertTrue(svg.is_file())
            self.assertIn(
                "must not be added or reported as LCOE",
                svg.read_text(encoding="utf-8"),
            )

    def test_full_year_reports_total_system_cost_intensity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_fixture(
                root,
                result_use="SCIENTIFIC_PRODUCTION",
                optimization_hours=8760,
                period_baseline_load_gwh=1000.0,
            )
            payload = collect_result_dashboard(root)
            self.assertTrue(
                payload["identity"]["is_full_year_scientific_result"]
            )
            self.assertAlmostEqual(
                payload["cost_accounting"][
                    "scientific_full_year_system_cost_intensity_cny_per_kwh"
                ],
                0.15,
            )

    def test_cost_scope_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_fixture(root)
            frame = pd.read_csv(root / "cost_components.csv")
            frame.loc[
                frame.cost_component.eq("operating_fuel"),
                "value_million_cny_model_accounting_period",
            ] = 31.0
            frame.to_csv(root / "cost_components.csv", index=False)
            with self.assertRaisesRegex(
                ValueError,
                "do not reconstruct the reported objective",
            ):
                collect_result_dashboard(root)


if __name__ == "__main__":
    unittest.main()
