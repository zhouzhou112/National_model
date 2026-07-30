from __future__ import annotations

import unittest

import numpy as np

from cispo_model.solution_export import assess_interprovincial_bidirectionality


CONTRACT = {
    "enabled": True,
    "reference_hours": 168,
    "maximum_edge_hours_per_reference": 4,
    "maximum_opposing_flow_gw": 0.25,
    "maximum_opposing_fraction_of_line_capacity": 0.15,
    "maximum_opposing_energy_gwh_per_reference": 0.75,
    "maximum_excess_loss_gwh_per_reference": 0.025,
    "maximum_opposing_share_of_gross_flow": 5e-5,
    "maximum_excess_loss_share_of_system_load": 1e-7,
}


def assess(
    forward: np.ndarray,
    reverse: np.ndarray,
    *,
    hours: int = 168,
    configured_hours: int = 8760,
    capacity: np.ndarray | None = None,
    load_gwh: float = 300_000.0,
) -> dict:
    if capacity is None:
        capacity = np.full(forward.shape[0], 2.0)
    return assess_interprovincial_bidirectionality(
        flow_forward=forward,
        flow_reverse=reverse,
        line_capacity_gw=capacity,
        line_efficiency=np.full(forward.shape[0], 0.985),
        system_load_gwh=load_gwh,
        optimization_hours=hours,
        configured_hours=configured_hours,
        tolerance_gw=1e-6,
        warning_contract=CONTRACT,
    )


class DirectionalityQcTests(unittest.TestCase):
    def test_strict_zero_counterflow_passes(self) -> None:
        result = assess(
            np.array([[1.0, 0.0], [0.0, 0.5]]),
            np.array([[0.0, 0.4], [0.2, 0.0]]),
        )
        self.assertTrue(result["accepted"])
        self.assertTrue(result["strict_pass"])
        self.assertFalse(result["warning_applied"])
        self.assertEqual(result["classification"], "STRICT_PASS")

    def test_de_minimis_counterflow_is_warning_only_for_truncated_horizon(self) -> None:
        forward = np.full((1, 168), 100.0)
        reverse = np.zeros((1, 168))
        forward[0, [28, 94, 95]] = [0.083989, 0.176374, 0.120643]
        reverse[0, [28, 94, 95]] = [1.562011, 1.469626, 1.525357]
        result = assess(
            forward,
            reverse,
            capacity=np.array([1.646]),
        )
        self.assertTrue(result["accepted"])
        self.assertFalse(result["strict_pass"])
        self.assertTrue(result["warning_applied"])
        self.assertEqual(
            result["classification"], "TEST_ONLY_DE_MINIMIS_WARNING"
        )
        self.assertEqual(result["observed"]["edge_hours"], 3)

    def test_same_counterflow_fails_full_year_scientific_scope(self) -> None:
        forward = np.full((1, 8760), 100.0)
        reverse = np.zeros((1, 8760))
        forward[0, 28] = 0.1
        reverse[0, 28] = 1.5
        result = assess(
            forward,
            reverse,
            hours=8760,
            configured_hours=8760,
            capacity=np.array([1.646]),
            load_gwh=15_000_000.0,
        )
        self.assertFalse(result["accepted"])
        self.assertFalse(result["warning_applied"])
        self.assertEqual(result["classification"], "HARD_FAIL")

    def test_any_exceeded_budget_remains_hard_fail(self) -> None:
        forward = np.full((1, 168), 100.0)
        reverse = np.zeros((1, 168))
        forward[0, 28] = 0.3
        reverse[0, 28] = 1.3
        result = assess(
            forward,
            reverse,
            capacity=np.array([1.646]),
        )
        self.assertFalse(result["accepted"])
        self.assertFalse(result["within_warning_budget"])
        self.assertEqual(result["classification"], "HARD_FAIL")

    def test_shape_and_domain_validation(self) -> None:
        with self.assertRaisesRegex(ValueError, "matching 2-D"):
            assess_interprovincial_bidirectionality(
                flow_forward=np.zeros((1, 2)),
                flow_reverse=np.zeros((2, 1)),
                line_capacity_gw=np.ones(1),
                line_efficiency=np.ones(1),
                system_load_gwh=1.0,
                optimization_hours=2,
                configured_hours=8760,
                tolerance_gw=1e-6,
                warning_contract=CONTRACT,
            )


if __name__ == "__main__":
    unittest.main()
