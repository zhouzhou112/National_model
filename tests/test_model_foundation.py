from __future__ import annotations

import unittest

from cispo_model.config import capital_recovery_factor, load_model_config
from cispo_model.data import load_model_data
from cispo_model.preflight import run_preflight
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
