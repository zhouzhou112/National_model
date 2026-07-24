from __future__ import annotations

import unittest

import numpy as np

from cispo_model.config import load_model_config
from cispo_model.flexible_load import (
    _ev_backlog_bounds,
    _ev_v1g_shift_bounds,
    _thermal_state_bounds,
    _thermal_shift_bounds,
    make_day_slices,
)


class FlexibleLoadContractTests(unittest.TestCase):
    def test_base_and_optional_scenarios_are_explicit(self):
        base = load_model_config()
        flexible = load_model_config(
            scenario_path="config/scenarios/flexible_load_v1.json"
        )
        v2g = load_model_config(
            scenario_path="config/scenarios/flexible_load_v2g_v1.json"
        )
        state = load_model_config(
            scenario_path="config/scenarios/flexible_load_state_v2.json"
        )
        self.assertEqual(base.raw["scenario"]["id"], "base")
        self.assertFalse(base.raw["features"]["flexible_load"])
        self.assertTrue(flexible.raw["features"]["flexible_load"])
        self.assertFalse(flexible.raw["flexible_load"]["ev_v2g"]["enabled"])
        self.assertTrue(v2g.raw["flexible_load"]["ev_v2g"]["enabled"])
        self.assertEqual(
            state.raw["flexible_load"]["formulation"], "state_envelope_v2"
        )
        self.assertFalse(state.raw["flexible_load"]["ev_v2g"]["enabled"])
        self.assertNotIn("formulation", flexible.raw["flexible_load"])

    def test_day_slices_cover_partial_horizon_once(self):
        slices = make_day_slices(25, 24)
        covered = [hour for item in slices for hour in range(item.start, item.stop)]
        self.assertEqual(covered, list(range(25)))
        self.assertEqual([(item.start, item.stop) for item in slices], [(0, 24), (24, 25)])

    def test_thermal_shift_bounds_follow_daily_peak_and_baseline(self):
        baseline = np.asarray([[0.0, 2.0, 4.0, 1.0]])
        up, down = _thermal_shift_bounds(
            baseline, (slice(0, 4),), 0.25, 0.5
        )
        np.testing.assert_allclose(down, 0.25 * baseline)
        np.testing.assert_allclose(up, np.full_like(baseline, 2.0))

    def test_ev_v1g_bounds_preserve_fixed_share_and_power_envelope(self):
        baseline = np.asarray([[0.0, 1.0, 2.0, 1.0]])
        up, down = _ev_v1g_shift_bounds(
            baseline, (slice(0, 4),), 0.5, 2.0
        )
        np.testing.assert_allclose(down, 0.5 * baseline)
        np.testing.assert_allclose(up, [[2.0, 1.0, 0.0, 1.0]])

    def test_thermal_state_bounds_add_duration_scaled_inventory(self):
        baseline = np.asarray([[0.0, 2.0, 4.0, 1.0]])
        up, down, state = _thermal_state_bounds(
            baseline,
            (slice(0, 4),),
            maximum_reduction_fraction=0.25,
            maximum_increase_fraction_of_daily_peak=0.5,
            duration_hours=3.0,
        )
        np.testing.assert_allclose(down, 0.25 * baseline)
        np.testing.assert_allclose(up, np.full_like(baseline, 2.0))
        np.testing.assert_allclose(state, np.full_like(baseline, 6.0))

    def test_ev_backlog_bounds_keep_baseline_feasible(self):
        baseline = np.asarray([[0.0, 1.0, 4.0, 1.0]])
        up, down, queue = _ev_backlog_bounds(
            baseline,
            (slice(0, 4),),
            shiftable_energy_fraction=0.5,
            maximum_power_to_daily_average_ratio=2.0,
            maximum_queue_duration_hours=6.0,
        )
        np.testing.assert_allclose(down, 0.5 * baseline)
        # The observed baseline peak is retained even when it exceeds
        # ratio * daily mean, so the zero-shift solution remains feasible.
        np.testing.assert_allclose(up, [[4.0, 3.0, 0.0, 3.0]])
        np.testing.assert_allclose(queue, np.full_like(baseline, 4.5))


if __name__ == "__main__":
    unittest.main()
