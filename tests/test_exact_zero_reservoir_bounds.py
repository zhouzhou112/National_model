from types import SimpleNamespace
import unittest

import numpy as np
from scipy import sparse

from cispo_model.monolithic import _reservoir_release_upper_scaled
from cispo_model.zero_bound_certificate import certify


def fixture(local, *, cascade=False, transfer=None, weight=1.0):
    local = np.asarray(local, dtype=float)
    count, hours = local.shape
    return SimpleNamespace(
        reservoir_local_inflow_m3s=local,
        reservoir_active_storage_m3=np.full(count, 1e9),
        cascade_station_local_rows=(
            np.arange(count) if cascade else np.array([], dtype=int)
        ),
        cascade_edge_source_local_rows=[np.array([0])] if cascade else [],
        cascade_edge_target_local_rows=[np.array([1])] if cascade else [],
        cascade_edge_target_weights=[np.array([weight])] if cascade else [],
        cascade_edge_lag_h=[1] if cascade else [],
        cascade_edge_transfer_fraction=(
            [np.ones(hours) if transfer is None else np.array(transfer)]
            if cascade
            else []
        ),
    )


class ExactZeroReservoirTests(unittest.TestCase):
    def test_archived_row_sum_certificate(self):
        a = sparse.csr_matrix(
            [[1.0, -1.0, 3.6, 0.0], [-1.0, 1.0, 0.0, 3.6]]
        )
        names = [
            "reservoir_active_storage_million_m3[0,0]",
            "reservoir_active_storage_million_m3[0,1]",
            "reservoir_turbine_flow_1000m3s[0,0]",
            "reservoir_turbine_flow_1000m3s[0,1]",
        ]
        rows = [
            "reservoir_independent_cyclic_first_hour[0]",
            "reservoir_independent_hourly_transition[0,0]",
        ]
        for rhs, expected in (
            (np.zeros(2), "PASS"),
            (np.array([0.0, 1e-100]), "FAIL"),
        ):
            proof = certify(
                a,
                rhs,
                np.zeros(4),
                np.array([10.0, 10.0, 1e-12, 1e-12]),
                np.array([10.0, 10.0, 0.0, 0.0]),
                np.array(["=", "="]),
                rows,
                names,
            )
            self.assertEqual(proof["status"], expected)

    def test_certificate_rejects_unrelated_bound_change(self):
        with self.assertRaises(ValueError):
            certify(
                sparse.csr_matrix([[1.0]]),
                np.zeros(1),
                np.zeros(1),
                np.ones(1),
                np.zeros(1),
                np.array(["="]),
                ["balance"],
                ["other_capacity"],
            )

    def test_zero_inflow_has_exact_zero_release_even_with_nonzero_storage(self):
        upper = _reservoir_release_upper_scaled(
            fixture([[0.0, 0.0]]), flow_scale_m3s=1000.0
        )
        np.testing.assert_array_equal(upper, np.zeros((1, 2)))

    def test_positive_inflow_retains_original_outward_padding(self):
        upper = _reservoir_release_upper_scaled(
            fixture([[1000.0, 2000.0]]), flow_scale_m3s=1000.0
        )
        np.testing.assert_array_equal(
            upper, np.full((1, 2), 3.0 * (1.0 + 1e-12) + 1e-12)
        )

    def test_tiny_positive_inflow_is_not_thresholded_to_zero(self):
        for positive in (1e-12, 1e-300, 1e-320):
            with self.subTest(positive=positive):
                upper = _reservoir_release_upper_scaled(
                    fixture([[positive, 0.0]]), flow_scale_m3s=1000.0
                )
                self.assertTrue(np.all(upper > 0.0))

    def test_zero_cascade_propagates_through_lag(self):
        upper = _reservoir_release_upper_scaled(
            fixture([[0.0, 0.0], [0.0, 0.0]], cascade=True),
            flow_scale_m3s=1000.0,
        )
        np.testing.assert_array_equal(upper, np.zeros((2, 2)))

    def test_nonzero_upstream_prevents_downstream_zero_fix(self):
        upper = _reservoir_release_upper_scaled(
            fixture([[1000.0, 0.0], [0.0, 0.0]], cascade=True),
            flow_scale_m3s=1000.0,
        )
        self.assertTrue(np.all(upper[1] > 0.0))

    def test_zero_weight_or_zero_transfer_blocks_inflow_exactly(self):
        for settings in ({"weight": 0.0}, {"transfer": [0.0, 0.0]}):
            upper = _reservoir_release_upper_scaled(
                fixture(
                    [[1000.0, 0.0], [0.0, 0.0]],
                    cascade=True,
                    **settings,
                ),
                flow_scale_m3s=1000.0,
            )
            np.testing.assert_array_equal(upper[1], np.zeros(2))

    def test_positive_downstream_local_inflow_is_preserved(self):
        upper = _reservoir_release_upper_scaled(
            fixture([[0.0, 0.0], [0.0, 1e-12]], cascade=True),
            flow_scale_m3s=1000.0,
        )
        self.assertTrue(np.all(upper[1] > 0.0))


if __name__ == "__main__":
    unittest.main()
