import json
from pathlib import Path
import unittest

import numpy as np
from scipy import sparse

from cispo_model.physical_lp_diff import compare_physical_lp_arrays


WHITELIST = json.loads(
    (
        Path(__file__).resolve().parents[1]
        / "config"
        / "physical_lp_diff_whitelist_v1.json"
    ).read_text(encoding="utf-8")
)


class PhysicalLPDiffTests(unittest.TestCase):
    def compare(self, candidate_matrix, candidate_upper):
        reference = sparse.csr_matrix([[1.0, -2.0], [0.0, 3.6]])
        return compare_physical_lp_arrays(
            reference_matrix=reference,
            candidate_matrix=sparse.csr_matrix(candidate_matrix),
            reference_rhs=np.zeros(2),
            candidate_rhs=np.zeros(2),
            reference_lower=np.zeros(2),
            candidate_lower=np.zeros(2),
            reference_upper=np.array([10.0, 1e-12]),
            candidate_upper=np.asarray(candidate_upper, dtype=float),
            reference_objective=np.array([1.0, 0.0]),
            candidate_objective=np.array([1.0, 0.0]),
            reference_senses=["<", "="],
            candidate_senses=["<", "="],
            row_names=[
                "load_center_ror_availability_0",
                "reservoir_independent_cyclic_first_hour[0]",
            ],
            variable_names=[
                "hydro_capacity_gw[0]",
                "reservoir_turbine_flow_1000m3s[0,0]",
            ],
            whitelist=WHITELIST,
        )

    def test_reviewed_matrix_and_exact_zero_bound_changes_pass(self):
        report = self.compare([[1.5, -2.0], [0.0, 3.6]], [10.0, 0.0])
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(
            report["approved_change_counts"],
            {
                "exact_zero_reservoir_release_upper_bound": 1,
                "ror_full_load_hour_threshold_correction": 1,
            },
        )

    def test_unlisted_matrix_change_fails_closed(self):
        report = self.compare([[1.0, -1.0], [0.0, 3.6]], [10.0, 0.0])
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["checks"]["matrix_changes_whitelisted"])

    def test_nonzero_or_unrelated_upper_bound_change_fails_closed(self):
        report = self.compare([[1.0, -2.0], [0.0, 3.6]], [9.0, 1e-12])
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(
            report["checks"][
                "upper_bound_changes_are_exact_zero_certificate_candidates"
            ]
        )


if __name__ == "__main__":
    unittest.main()
