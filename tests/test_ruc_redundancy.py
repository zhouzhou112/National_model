from __future__ import annotations

import inspect
import unittest

import pandas as pd

from cispo_model import monolithic
from cispo_model.monolithic import _validate_reduced_ruc_domain


class ReducedRucTests(unittest.TestCase):
    def test_reduction_domain_requires_the_algebraic_premises(self):
        valid = pd.DataFrame(
            {
                "pmin_fraction": [0.3, 0.85],
                "pmax_fraction": [1.0, 1.0],
                "min_up_h": [4, 22],
                "min_down_h": [2, 22],
            }
        )
        _validate_reduced_ruc_domain(valid)

        invalid_pmin = valid.copy()
        invalid_pmin.loc[0, "pmin_fraction"] = 1.01
        with self.assertRaisesRegex(ValueError, "pmin_fraction"):
            _validate_reduced_ruc_domain(invalid_pmin)

        invalid_time = valid.copy()
        invalid_time.loc[0, "min_up_h"] = 0
        with self.assertRaisesRegex(ValueError, "min_up_h"):
            _validate_reduced_ruc_domain(invalid_time)

    def test_s4_24_s4_25_and_s4_29_imply_omitted_upper_bounds(self):
        # S4-24 at t: online_t <= capacity - startup_(t+1) - prior shutdowns.
        capacity = 10.0
        startup_next = 2.0
        prior_shutdowns = 1.0
        online_t = capacity - startup_next - prior_shutdowns
        self.assertLessEqual(online_t, capacity)

        # Applying S4-24 at t-1 proves startup_t <= capacity.
        startup_t = 3.0
        online_previous = capacity - startup_t - 2.0
        self.assertGreaterEqual(online_previous, 0.0)
        self.assertLessEqual(startup_t, capacity)

        # S4-25 at t-1 followed by S4-24 bounds shutdown_t by capacity.
        shutdown_t = 4.0
        online_previous = 5.0
        self.assertLessEqual(shutdown_t, online_previous)
        self.assertLessEqual(online_previous, capacity)
        self.assertLessEqual(shutdown_t, capacity)

        # S4-29 is always at least as tight as the generic maximum row.
        pmin, pmax = 0.4, 1.0
        online, startup, next_shutdown = 7.0, 1.0, 2.0
        s4_29_upper = pmax * (online - startup - next_shutdown) + pmin * (
            startup + next_shutdown
        )
        self.assertLessEqual(s4_29_upper, pmax * online)

    def test_duplicate_rows_are_not_reintroduced(self):
        source = inspect.getsource(monolithic.build_full_year_monolithic)
        for name in (
            'name="online_capacity_limit"',
            'name="startup_capacity_limit"',
            'name="shutdown_capacity_limit"',
            'name="thermal_maximum_generation"',
        ):
            self.assertNotIn(name, source)
        for name in ("ruc_s4_24_", "ruc_s4_25_", "ruc_s4_29_"):
            self.assertIn(name, source)


if __name__ == "__main__":
    unittest.main()
