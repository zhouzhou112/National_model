from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import gurobipy as gp

from cispo_model.config import load_model_config
from cispo_model.solver_artifacts import (
    SolverArtifactError,
    export_scientific_base_solver_artifacts,
)


class SolverArtifactTests(unittest.TestCase):
    def _solved_lp(self) -> gp.Model:
        model = gp.Model("scientific_artifact_test")
        model.Params.OutputFlag = 0
        model.Params.Crossover = 1
        value = model.addVar(lb=0.0, name="value")
        model.addConstr(value >= 1.0, name="minimum")
        model.setObjective(value, gp.GRB.MINIMIZE)
        model.optimize()
        return model

    def test_selective_scientific_base_artifact_contract(self):
        model = self._solved_lp()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = export_scientific_base_solver_artifacts(
                model,
                load_model_config(),
                root,
                solve_report={
                    "status": "OPTIMAL",
                    "solver_parameters": {"crossover": 1},
                },
                solution_qc={"status": "PASS"},
                result_use="SCIENTIFIC_PRODUCTION",
            )
            self.assertEqual(
                manifest["schema_version"],
                "cispo_scientific_base_solver_artifacts_v1",
            )
            self.assertTrue((root / "base_solution.sol.gz").is_file())
            self.assertTrue((root / "base_basis.bas.gz").is_file())
            self.assertTrue((root / "base_solver.prm").is_file())
            self.assertTrue((root / "base_model_fingerprint.json").is_file())
            self.assertFalse((root / "base_solution.sol").exists())
            self.assertFalse((root / "base_basis.bas").exists())

    def test_truncated_horizon_is_rejected(self):
        model = self._solved_lp()
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(
                SolverArtifactError, "full-year"
            ):
                export_scientific_base_solver_artifacts(
                    model,
                    load_model_config(),
                    temporary,
                    solve_report={
                        "status": "OPTIMAL",
                        "solver_parameters": {"crossover": 1},
                    },
                    solution_qc={"status": "PASS"},
                    result_use="TEST_ONLY_TRUNCATED_HORIZON",
                )


if __name__ == "__main__":
    unittest.main()
