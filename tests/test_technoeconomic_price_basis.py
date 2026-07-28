from __future__ import annotations

import unittest

from cispo_model.config import load_model_config
from cispo_model.price_basis import (
    domestic_2022_cny_to_2025,
    load_price_basis_config,
    nuclear_capex_2025_cny,
)


class TechnoeconomicPriceBasisTests(unittest.TestCase):
    def test_price_basis_contract(self):
        basis = load_price_basis_config()
        self.assertEqual(basis["contract_version"], "technoeconomic_2025_cny_v2")
        self.assertEqual(basis["target_price_basis"], "2025 constant CNY")
        self.assertAlmostEqual(
            basis["domestic_cny_to_2025_factor"],
            (1.0 + 0.002) * (1.0 + 0.002),
        )

    def test_all_planning_years_use_one_common_rebase_factor(self):
        source_path = {2030: 5500.0, 2040: 4800.0, 2050: 4100.0, 2060: 3500.0}
        converted = {
            year: domestic_2022_cny_to_2025(value)
            for year, value in source_path.items()
        }
        for year, value in source_path.items():
            self.assertAlmostEqual(converted[year] / value, 1.004004)
        self.assertAlmostEqual(
            converted[2060] / converted[2030],
            source_path[2060] / source_path[2030],
        )

    def test_nuclear_returns_to_source_usd_trajectory(self):
        self.assertAlmostEqual(nuclear_capex_2025_cny(2030), 20000.12)
        self.assertAlmostEqual(nuclear_capex_2025_cny(2040), 18928.685)
        self.assertAlmostEqual(nuclear_capex_2025_cny(2050), 17857.25)
        self.assertAlmostEqual(nuclear_capex_2025_cny(2060), 16785.815)

    def test_runtime_config_uses_2025_constant_cny(self):
        config = load_model_config().raw
        self.assertEqual(
            config["monetary_price_basis"]["target"], "2025 constant CNY"
        )
        self.assertAlmostEqual(config["wave_energy"]["eur_to_cny"], 8.1185)
        self.assertAlmostEqual(
            config["thermal"]["nuclear_fuel_yuan_per_mwh"], 69.276276
        )
        self.assertAlmostEqual(
            config["network"]["spur_capex_million_yuan_per_gw_km"],
            1.218860856,
        )
        self.assertEqual(
            config["load_center_network"]["flow_regularization_status"],
            "numerical tie-breaker; excluded from economic price rebasing",
        )


if __name__ == "__main__":
    unittest.main()
