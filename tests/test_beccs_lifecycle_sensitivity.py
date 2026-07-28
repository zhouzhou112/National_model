from __future__ import annotations

import unittest

import pandas as pd

from cispo_model.carbon_accounting import (
    evaluate_postsolve_beccs_lifecycle_sensitivity,
)


class BeccsLifecycleSensitivityTests(unittest.TestCase):
    def test_postsolve_cases_hold_physical_storage_fixed(self):
        source = pd.DataFrame(
            {
                "province_code": [11, 12],
                "beccs_stored_co2_mtco2": [10.0, 20.0],
                "beccs_lifecycle_emissions_mtco2": [0.0, 0.0],
                "net_emissions_after_dac_mtco2": [100.0, 200.0],
            }
        )
        result = evaluate_postsolve_beccs_lifecycle_sensitivity(
            source, {"low": 0.05, "base": 0.10, "high": 0.20}
        )
        base = result.loc[result.case_id.eq("base")].sort_values("province_code")
        self.assertEqual(base.assumed_lifecycle_emissions_mtco2.tolist(), [1.0, 2.0])
        self.assertEqual(base.adjusted_beccs_net_removal_mtco2.tolist(), [9.0, 18.0])
        self.assertEqual(
            base.adjusted_net_emissions_after_dac_mtco2.tolist(), [101.0, 202.0]
        )

    def test_rejects_lifecycle_share_outside_unit_interval(self):
        source = pd.DataFrame(
            {
                "province_code": [11],
                "beccs_stored_co2_mtco2": [1.0],
                "beccs_lifecycle_emissions_mtco2": [0.0],
                "net_emissions_after_dac_mtco2": [2.0],
            }
        )
        with self.assertRaisesRegex(ValueError, "in \[0, 1\]"):
            evaluate_postsolve_beccs_lifecycle_sensitivity(source, {"high": 1.1})


if __name__ == "__main__":
    unittest.main()
