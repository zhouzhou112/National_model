"""Author 6d stock-bound closure and cancellation-only RHS invariants."""
import copy
import unittest
import numpy as np
import gurobipy as gp
from cispo_model.numerical_cleanup import close_capacity_columns, zero_cancellation_rhs
from cispo_model.config import load_model_config, ModelConfig


class CapacityCleanupTests(unittest.TestCase):
    def test_strict_cutoff_infinite_zero_negative_and_paired_bounds(self):
        with gp.Model() as m:
            m.Params.OutputFlag = 0
            floor = np.array([0., 0., 0., 0., 0., 38.])
            upper = np.array([0., 1e-5, 2e-5, np.inf, -1e-6, 38.+5e-6])
            cap = m.addMVar(6, lb=floor, ub=upper, name='storage_capacity_gw')
            new = m.addMVar(6, lb=0, ub=upper-floor, name='storage_new_gw')
            m.update()
            before = cap.LB.copy()
            self.assertEqual(close_capacity_columns(cap, new, floor, 0, unit='GW'), [])
            audit = close_capacity_columns(cap, new, floor, 1e-5, unit='GW')
            m.update()
            self.assertEqual(len(audit), 2)
            np.testing.assert_array_equal(cap.LB, before)
            self.assertEqual(cap.UB[-1], 38.)
            self.assertEqual(new.UB[-1], 0.)
            np.testing.assert_array_equal(cap.UB[:5], [0, 1e-5, 2e-5, np.inf, -1e-6])
            self.assertEqual(audit[0]['indices'], [5])
            self.assertEqual(audit[1]['paired_capacity'], 'storage_capacity_gw[5]')

    def test_energy_capacity_has_same_units_aware_rule(self):
        with gp.Model() as m:
            m.Params.OutputFlag = 0
            v = m.addMVar(1, lb=8, ub=8+3e-6, name='phs_energy_capacity_gwh')
            m.update()
            rows = close_capacity_columns(v, None, [8], 1e-5, unit='GWh')
            m.update()
            self.assertEqual(v.UB[0], 8)
            self.assertEqual(rows[0]['unit'], 'GWh')

    def test_rhs_cancellation_certificate_not_generic_threshold(self):
        residual = np.nextafter(1., np.inf)-1.
        values = np.array([residual, 1e-14, 1e-12, 0., -residual])
        left = np.array([1., 1e-14, 1., 1., 1.])
        right = np.array([-1., 0., -1., -1., -1.])
        cleaned, audit = zero_cancellation_rhs(values, left, right, 1e-12, 'account')
        np.testing.assert_array_equal(cleaned, [0., 1e-14, 1e-12, 0., 0.])
        self.assertEqual([r['row'] for r in audit], ['account[0]', 'account[4]'])
        off, records = zero_cancellation_rhs(values, left, right, 0., 'account')
        np.testing.assert_array_equal(off, values)
        self.assertEqual(records, [])

    def test_config_defaults_off_and_rejects_unsafe_thresholds(self):
        cfg = load_model_config('config/optimization_numeric_dac_by_year_v9.json')
        for key, maximum in [('other_capacity_headroom_zero_gw_gwh', 1e-4),
                             ('capacity_cancellation_rhs_zero', 1e-12)]:
            self.assertEqual(cfg.raw['numerics'].get(key, 0.), 0.)
            for bad in [-1., float('nan'), maximum*2]:
                raw = copy.deepcopy(cfg.raw)
                raw['numerics'][key] = bad
                with self.assertRaises(ValueError):
                    ModelConfig(cfg.path, raw).validate()


if __name__ == '__main__':
    unittest.main()
