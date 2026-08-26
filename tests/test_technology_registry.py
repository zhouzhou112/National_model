import unittest

from cispo_model.technology_registry import (
    fixed_om_fraction,
    load_technology_parameter_registry,
    transmission_loss_fraction_per_km,
)


class TechnologyRegistryTests(unittest.TestCase):
    def test_runtime_registry_values_match_validated_model_boundary(self) -> None:
        registry = load_technology_parameter_registry()
        self.assertEqual(transmission_loss_fraction_per_km(registry), 3.2e-5)
        self.assertEqual(fixed_om_fraction(registry, "onwind"), 0.015)
        self.assertEqual(fixed_om_fraction(registry, "offwind"), 0.015)
        self.assertEqual(fixed_om_fraction(registry, "upv"), 0.005)
        self.assertEqual(fixed_om_fraction(registry, "dpv"), 0.005)
        self.assertEqual(fixed_om_fraction(registry, "hydro"), 0.02)


if __name__ == "__main__":
    unittest.main()
