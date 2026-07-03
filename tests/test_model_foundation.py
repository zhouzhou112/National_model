from __future__ import annotations

import unittest

from cispo_model.config import capital_recovery_factor, load_model_config
from cispo_model.data import load_model_data
from cispo_model.preflight import estimate_full_model_scale, run_preflight
from cispo_model.timeblocks import make_time_blocks


class ModelFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_model_config()
        cls.data = load_model_data(cls.config)

    def test_boundary_and_first_planning_year(self):
        self.assertEqual(self.config.boundary_year, 2025)
        self.assertEqual(self.config.planning_year, 2030)
        self.assertEqual(self.config.hours, 8760)

    def test_single_full_year_block_covers_every_hour_once(self):
        blocks = make_time_blocks(8760, 8760)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[-1].hours, 8760)
        covered = [hour for block in blocks for hour in range(block.hour_start, block.hour_stop)]
        self.assertEqual(covered, list(range(8760)))

    def test_supported_horizons_are_exact_and_test_scoped(self):
        one_month = self.config.horizon("one_month")
        six_months = self.config.horizon("six_months")
        full_year = self.config.horizon("full_year")
        self.assertEqual(one_month["hours"], 744)
        self.assertEqual(six_months["hours"], 4344)
        self.assertEqual(full_year["hours"], 8760)
        self.assertTrue(one_month["test_only"])
        self.assertTrue(six_months["test_only"])
        self.assertFalse(full_year["test_only"])

    def test_horizon_scale_estimates_are_monotonic(self):
        estimates = [
            estimate_full_model_scale(self.config, self.data, hours).variables
            for hours in (744, 4344, 8760)
        ]
        self.assertLess(estimates[0], estimates[1])
        self.assertLess(estimates[1], estimates[2])

    def test_full_data_preflight_has_no_hard_fail(self):
        report = run_preflight(self.config, self.data)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["status_counts"]["HARD_FAIL"], 0)
        self.assertEqual(report["scale_estimate"]["block_count"], 1)
        self.assertEqual(self.config.raw["construction"]["architecture"], "full_year_monolithic_lp")

    def test_crf_is_numerically_stable(self):
        value = capital_recovery_factor(0.074, 25)
        self.assertGreater(value, 0.08)
        self.assertLess(value, 0.10)


if __name__ == "__main__":
    unittest.main()
