from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cispo_model.solver_audit import collect_solver_run, parse_gurobi_log


class SolverAuditTests(unittest.TestCase):
    def test_parse_large_lp_log(self):
        parsed = parse_gurobi_log(
            """
Optimize a model with 68,189,325 rows, 40,912,327 columns and 515,040,080 nonzeros
Presolve time: 17932.25s
Presolved: 37,982,903 rows, 35,423,761 columns, 400,861,556 nonzeros
Ordering time: 3180.53s
 AA' NZ     : 7.425e+08
 Factor NZ  : 3.848e+10 (roughly 340.0 GB of memory)
 Factor Ops : 2.448e+15
Barrier solved model in 171 iterations and 686.50 seconds
Solved in 223903 iterations and 732.95 seconds
"""
        )
        self.assertEqual(parsed["original_columns"], 40_912_327)
        self.assertEqual(parsed["presolved_rows"], 37_982_903)
        self.assertEqual(parsed["presolve_seconds"], 17_932.25)
        self.assertEqual(parsed["factor_nonzeros"], 3.848e10)
        self.assertEqual(parsed["factor_memory_gb_log_estimate"], 340.0)
        self.assertEqual(parsed["barrier_iterations"], 171)
        self.assertEqual(parsed["total_solver_log_seconds"], 732.95)

    def test_collect_solver_run_includes_structure_audit_summary(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "solve_report.json").write_text(
                json.dumps(
                    {
                        "planning_year": 2030,
                        "status": "OPTIMAL",
                        "objective_value": 1.0,
                        "solver_runtime_seconds": 2.0,
                        "model_statistics": {
                            "variables": 3,
                            "constraints": 2,
                            "nonzeros": 4,
                        },
                    }
                ),
                encoding="utf-8",
            )
            (root / "solution_qc.json").write_text(
                json.dumps({"status": "PASS"}), encoding="utf-8"
            )
            (root / "build_report.json").write_text("{}", encoding="utf-8")
            (root / "run_scope.json").write_text("{}", encoding="utf-8")
            (root / "constraint_family_audit.json").write_text(
                json.dumps(
                    {
                        "schema_version": "constraint_family_audit_v2",
                        "constraint_families": [
                            {"family": "vre", "matrix_nonzeros": 12}
                        ],
                        "variable_families": [
                            {"family": "ruc", "matrix_nonzeros": 10}
                        ],
                    }
                ),
                encoding="utf-8",
            )

            collected = collect_solver_run(root)

        self.assertEqual(collected["constraint_family_audit_schema"], "constraint_family_audit_v2")
        self.assertEqual(collected["largest_raw_constraint_family"], "vre")
        self.assertEqual(collected["largest_raw_constraint_family_nonzeros"], 12)
        self.assertEqual(collected["largest_raw_variable_family"], "ruc")
        self.assertEqual(collected["largest_raw_variable_family_nonzeros"], 10)


if __name__ == "__main__":
    unittest.main()
