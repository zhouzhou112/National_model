from __future__ import annotations

import unittest

from cispo_model.solver_audit import parse_gurobi_log


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


if __name__ == "__main__":
    unittest.main()
