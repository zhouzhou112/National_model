"""Small tests for read-only historical Barrier-log extraction."""
import copy
import unittest

from scripts.report_8760_convergence import parse_stdout, validate_series


class ConvergenceLogTests(unittest.TestCase):
    def setUp(self):
        self.rows = parse_stdout(
            "Presolve removed 12 rows and 34 columns\n"
            " 0 1.00000000e+03 -2.00000000e+03 1.2e+2 3.4e+1 5.6e-1 12s\n"
            " 1* 1.10000000e+02 -2.10000000e+02 1.2e+1 3.4e+0 5.6e-2 22s\n"
        )
        self.callback = copy.deepcopy(self.rows)

    def test_parse_source_lines_and_star(self):
        self.assertEqual([r["source_line"] for r in self.rows], [2, 3])
        self.assertEqual([r["starred"] for r in self.rows], [False, True])
        self.assertEqual(self.rows[0]["primal_objective"], 1000)

    def test_residual_channels_must_not_be_forced_equal(self):
        self.callback[0]["primal_infeasibility"] *= 100
        validate_series(self.rows, self.callback)

    def test_duplicate_iteration_rejected(self):
        self.callback[1]["iteration"] = 0
        with self.assertRaises(ValueError):
            validate_series(self.rows, self.callback)

    def test_objective_mismatch_rejected(self):
        self.callback[1]["dual_objective"] = 0
        with self.assertRaises(ValueError):
            validate_series(self.rows, self.callback)

    def test_nonfinite_rejected(self):
        self.callback[1]["complementarity"] = float("nan")
        with self.assertRaises(ValueError):
            validate_series(self.rows, self.callback)

    def test_clock_mismatch_rejected(self):
        self.callback[1]["runtime_seconds"] += 2
        with self.assertRaises(ValueError):
            validate_series(self.rows, self.callback)


if __name__ == "__main__":
    unittest.main()
