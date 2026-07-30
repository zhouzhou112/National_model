from __future__ import annotations

import unittest

from cispo_model.master import selected_horizon_annual_fraction
from cispo_model.timeblocks import TimeBlock, make_time_blocks


class AnnualFlowScalingTests(unittest.TestCase):
    def test_short_horizons_use_exact_calendar_fraction(self):
        self.assertAlmostEqual(
            selected_horizon_annual_fraction(
                8760,
                [TimeBlock(block_id=0, hour_start=0, hour_stop=24)],
            ),
            24.0 / 8760.0,
        )
        self.assertAlmostEqual(
            selected_horizon_annual_fraction(
                8760,
                [TimeBlock(block_id=0, hour_start=0, hour_stop=744)],
            ),
            744.0 / 8760.0,
        )

    def test_full_year_fraction_is_one_across_multiple_blocks(self):
        self.assertEqual(
            selected_horizon_annual_fraction(
                8760,
                make_time_blocks(8760, 744),
            ),
            1.0,
        )

    def test_invalid_selected_horizon_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "Selected chronological hours"):
            selected_horizon_annual_fraction(8760, [])
        with self.assertRaisesRegex(ValueError, "Selected chronological hours"):
            selected_horizon_annual_fraction(
                8760,
                [TimeBlock(block_id=0, hour_start=0, hour_stop=8761)],
            )
        with self.assertRaisesRegex(ValueError, "configured_hours"):
            selected_horizon_annual_fraction(
                0,
                [TimeBlock(block_id=0, hour_start=0, hour_stop=1)],
            )


if __name__ == "__main__":
    unittest.main()
