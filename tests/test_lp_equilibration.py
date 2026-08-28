import unittest
import gzip
import hashlib
import io

import numpy as np
from scipy import sparse

from cispo_model.lp_equilibration import (Scaling, propose_scaling, transform,
    verify_roundtrip, pulled_back_tolerances, original_quality)
from cispo_model.mps_stream_audit import audit_lines
from scripts.audit_saved_mps_stream import HashReader


MPS = """NAME demo
ROWS
 N OBJ
 E balance
 L cap
COLUMNS
    x OBJ 2 balance 6250
    x cap 1e-6
    y OBJ -3 balance -1
RHS
    RHS1 OBJ -100000 balance 5
    RHS1 cap 2
BOUNDS
 LO BND x -2
 UP BND x 10
 FR BND y
ENDATA
"""


class TestScaling(unittest.TestCase):
    def setUp(self):
        self.a = sparse.csr_matrix([[6250., -1., 0.], [1e-6, 0., 1.], [0., 0., 0.]])
        self.data = (self.a, np.array([3., 1e-7, 0.]), np.array([1e-6, 3853., -2.]),
                     np.array([0., -np.inf, -5.]), np.array([1e-11, np.inf, 2.]))

    def test_roundtrip_preserves_every_value_and_sparsity(self):
        s = propose_scaling(self.a, self.data[2], exponent_limit=9)
        self.assertTrue(all(verify_roundtrip(self.data, transform(*self.data, s), s).values()))
        self.assertEqual(s.row_exponents[2], 0)

    def test_primal_objective_and_stationarity_mapping(self):
        s = Scaling(np.array([2, -3, 0]), np.array([-2, 4, 1]))
        sa, sb, sc, slb, sub = transform(*self.data, s)
        x, pi, rc = np.array([.1, -3., 1.]), np.array([3., -2., 0.]), np.array([2., 4., 1.])
        z, sp, sr = x / s.columns, pi / s.rows, rc * s.columns
        np.testing.assert_allclose(sa @ z - sb, s.rows * (self.a @ x - self.data[1]))
        np.testing.assert_allclose(sc @ z, self.data[2] @ x)
        np.testing.assert_allclose(sc - sa.T @ sp - sr, s.columns * (self.data[2] - self.a.T @ pi - rc))
        np.testing.assert_array_equal(s.primal_to_original(z), x)
        np.testing.assert_array_equal(s.dual_to_original(sp), pi)
        np.testing.assert_array_equal(s.reduced_cost_to_original(sr), rc)

    def test_tolerance_budget_rejects_excessive_scaling(self):
        with self.assertRaises(ValueError):
            pulled_back_tolerances(Scaling(np.array([20]), np.array([-20])))

    def test_budget_mapping_for_rows_bounds_duals(self):
        budget = pulled_back_tolerances(Scaling(np.array([-9, 9]), np.array([-9, 9])))
        self.assertEqual(budget["FeasibilityTol"], 1e-6 / 512)
        self.assertEqual(budget["OptimalityTol"], 1e-6 / 512)

    def test_overflow_rejected(self):
        data = (sparse.csr_matrix([[1e308]]), np.array([1.]), np.array([1.]), np.array([0.]), np.array([1.]))
        with np.errstate(over="ignore"), self.assertRaises(ValueError):
            transform(*data, Scaling(np.array([20]), np.array([20])))

    def test_invalid_coefficients_rejected(self):
        with self.assertRaises(ValueError):
            propose_scaling(sparse.csr_matrix([[np.nan]]), np.array([1.]))

    def test_known_optimum_quality(self):
        a = sparse.csr_matrix([[1., 1.]])
        q = original_quality(a, np.array([3.]), np.array([2., 1.]), np.zeros(2),
                             np.array([np.inf, 2.]), np.array([">"]),
                             np.array([1., 2.]), np.array([2.]), np.array([0., -1.]), 7.)
        for key in ("maximum_constraint_violation", "maximum_bound_violation", "maximum_stationarity_residual",
                    "maximum_dual_sign_violation", "maximum_complementarity", "relative_objective_gap"):
            self.assertEqual(q[key], 0.)
        self.assertEqual(q["primal_objective"], 11.)


class TestMPSStream(unittest.TestCase):
    def test_gzip_stream_hashes_original_compressed_bytes(self):
        data = gzip.compress(MPS.encode("ascii"))
        reader = HashReader(io.BytesIO(data))
        with io.BufferedReader(reader) as buffered:
            with gzip.GzipFile(fileobj=buffered) as stream:
                report = audit_lines(stream)
            self.assertEqual(reader.digest.hexdigest(), hashlib.sha256(data).hexdigest())
            self.assertEqual(reader.bytes_read, len(data))
        self.assertEqual(report["constraints"], 2)

    def test_truncated_gzip_is_rejected(self):
        data = gzip.compress(MPS.encode("ascii"))[:-8]
        with self.assertRaises(EOFError):
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
                audit_lines(stream)

    def test_counts_ranges_and_objective_offset_separation(self):
        report = audit_lines(MPS.splitlines(True))
        self.assertEqual(report["constraints"], 2)
        self.assertEqual(report["columns_contiguous_mps"], 2)
        self.assertEqual(report["ranges"]["matrix"]["nonzero_entries"], 3)
        self.assertEqual(report["ranges"]["rhs"]["maximum"]["absolute"], 5.)
        self.assertEqual(report["ranges"]["objective_offset_mps_sign"]["maximum"]["absolute"], 100000.)
        self.assertEqual(report["ranges"]["column_coefficient_ratio"]["maximum"]["absolute"], 6250/1e-6)

    def test_incomplete_and_unsupported_fail_closed(self):
        for text in (MPS.replace("ENDATA", ""), MPS.replace("BOUNDS", "RANGES"),
                     MPS.replace(" LO BND x -2", " BV BND x"), MPS.replace("6250", "nan"),
                     MPS.replace("    RHS1 cap 2", "    RHS2 cap 2")):
            with self.subTest(text=text), self.assertRaises(ValueError):
                audit_lines(text.splitlines(True))


if __name__ == "__main__":
    unittest.main()
