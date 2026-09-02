from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import gurobipy as gp
import pandas as pd
from gurobipy import GRB

from cispo_model.config import load_model_config
from cispo_model.master import MasterArtifacts
from cispo_model.mga import (
    MGAError,
    apply_mga_secondary_objective,
    evaluate_mga_solution,
    load_mga_spec,
    prepare_mga_request,
)
from cispo_model.result_summary import finalize_result_manifest


def _write_baseline(
    root: Path,
    config,
    *,
    result_use: str = "SCIENTIFIC_PRODUCTION",
    scientifically_accepted: bool = True,
) -> None:
    current_inputs = pd.DataFrame(
        [
            {
                "kind": "model_table",
                "logical_path": "tables/example.csv",
                "sha256": "a" * 64,
                "required": True,
            }
        ]
    )
    current_inputs.to_csv(root / "input_manifest.csv", index=False)
    (root / "run_scope.json").write_text(
        json.dumps(
            {
                "result_use": result_use,
                "analysis_mode": "BASE_MINIMUM_COST",
                "horizon": "full_year",
                "optimization_hours": config.hours,
                "scenario_id": "base",
                "planning_year": config.planning_year,
                "boundary_year": config.boundary_year,
            }
        ),
        encoding="utf-8",
    )
    (root / "solve_report.json").write_text(
        json.dumps(
            {
                "status": "OPTIMAL",
                "objective_value_million_cny": 123.0,
                "scientifically_accepted": scientifically_accepted,
                "solution_contract": {"acceptance_status": "PASS"},
            }
        ),
        encoding="utf-8",
    )
    (root / "solution_qc.json").write_text(
        json.dumps(
            {
                "status": "PASS",
                "hard_checks": {"power_balance": True},
                "scientifically_accepted": scientifically_accepted,
            }
        ),
        encoding="utf-8",
    )
    (root / "model_config_snapshot.json").write_text(
        json.dumps({"resolved_configuration": config.raw}), encoding="utf-8"
    )
    finalize_result_manifest(root, config)


class MGAContractTests(unittest.TestCase):
    def test_load_spec_requires_explicit_supported_target(self):
        spec_path = (
            Path(__file__).resolve().parents[1]
            / "config/mga/base_min_onwind_new_national_epsilon_1pct.json"
        )
        _, spec = load_mga_spec(spec_path)
        self.assertEqual(spec["secondary_objective"]["technology"], "onwind")
        self.assertEqual(spec["cost_slack"]["relative"], 0.01)

    def test_prepare_accepts_closed_scientific_base_with_matching_inputs(self):
        config = load_model_config()
        spec_path = (
            Path(__file__).resolve().parents[1]
            / "config/mga/base_min_onwind_new_national_epsilon_1pct.json"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write_baseline(root, config)
            request = prepare_mga_request(spec_path, root, config, root / "input_manifest.csv")
        self.assertEqual(request["analysis_mode"], "MGA_CONSTRAINED_SECONDARY_OBJECTIVE")
        self.assertAlmostEqual(request["cost_cap_million_cny"], 124.23)

    def test_prepare_rejects_truncated_or_non_scientific_baseline(self):
        config = load_model_config()
        spec_path = (
            Path(__file__).resolve().parents[1]
            / "config/mga/base_min_onwind_new_national_epsilon_1pct.json"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write_baseline(root, config, result_use="TEST_ONLY_TRUNCATED_HORIZON")
            with self.assertRaisesRegex(MGAError, "full-year scientific"):
                prepare_mga_request(spec_path, root, config, root / "input_manifest.csv")

    def test_prepare_rejects_integrity_valid_preservation_result(self):
        config = load_model_config()
        spec_path = (
            Path(__file__).resolve().parents[1]
            / "config/mga/base_min_onwind_new_national_epsilon_1pct.json"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write_baseline(root, config, scientifically_accepted=False)
            with self.assertRaisesRegex(MGAError, "accepted solver contract"):
                prepare_mga_request(
                    spec_path,
                    root,
                    config,
                    root / "input_manifest.csv",
                )

    def test_cost_cap_is_retained_when_secondary_objective_replaces_solver_objective(self):
        model = gp.Model("mga_contract_test")
        model.Params.OutputFlag = 0
        vre_new = model.addMVar(2, lb=0.0, ub=10.0, name="vre_new_gw")
        artifacts = MasterArtifacts(
            model=model,
            variables={"vre_new": vre_new},
            cost_components={"vre_investment": vre_new.sum()},
            index={"province_codes": [11], "storage_index": {}},
        )
        data = SimpleNamespace(
            vre_sites=pd.DataFrame(
                {
                    "grid_uid": ["g1", "g2"],
                    "province_code": [11, 11],
                    "technology": ["onwind", "onwind"],
                }
            )
        )
        request = {
            "mga_id": "test_max_onwind",
            "secondary_objective": {
                "direction": "maximize",
                "asset_type": "vre_new_capacity_gw",
                "technology": "onwind",
            },
            "cost_cap_million_cny": 2.0,
        }
        apply_mga_secondary_objective(artifacts, data, request)
        model.optimize()
        self.assertEqual(model.Status, GRB.OPTIMAL)
        result = evaluate_mga_solution(artifacts)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result["primary_cost_value_million_cny"], 2.0, places=7)
        self.assertAlmostEqual(result["secondary_objective_value_gw"], 2.0, places=7)


if __name__ == "__main__":
    unittest.main()
