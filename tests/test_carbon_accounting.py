import unittest

import pandas as pd

from cispo_model.carbon_accounting import resolve_beccs_carbon_factors


class BeccsCarbonAccountingTests(unittest.TestCase):
    def test_cispo_net_factor_is_split_without_changing_net_emissions(self):
        table = pd.DataFrame(
            {
                "technology": ["coal", "bioccs"],
                "emission_factor_mtco2_per_gwh": [0.00082, -0.00177],
                "ccs_capture_fraction": [0.9, float("nan")],
            }
        ).set_index("technology")
        factors = resolve_beccs_carbon_factors(table)
        self.assertAlmostEqual(factors.capture_fraction, 0.9)
        self.assertAlmostEqual(factors.stored, 0.00177)
        self.assertAlmostEqual(factors.gross_biogenic, 0.00177 / 0.9)
        self.assertAlmostEqual(
            factors.lifecycle_emissions
            + factors.uncaptured_biogenic
            - factors.gross_biogenic,
            factors.net_emissions,
        )

    def test_optional_lifecycle_emissions_preserve_mass_balance(self):
        table = pd.DataFrame(
            {
                "technology": ["coal", "bioccs"],
                "emission_factor_mtco2_per_gwh": [0.00082, -0.00170],
                "ccs_capture_fraction": [0.9, 0.9],
                "lifecycle_emission_factor_mtco2_per_gwh": [0.0, 0.00007],
            }
        ).set_index("technology")
        factors = resolve_beccs_carbon_factors(table)
        self.assertAlmostEqual(factors.stored, 0.00177)
        self.assertAlmostEqual(factors.net_removal, 0.00170)


if __name__ == "__main__":
    unittest.main()
