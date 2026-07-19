from __future__ import annotations

import unittest

from cispo_model.config import load_model_config
from cispo_model.data import load_model_data
from cispo_model.master import build_master
from cispo_model.timeblocks import TimeBlock


class CCSModelStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_model_config()
        cls.data = load_model_data(cls.config)
        cls.artifacts = build_master(
            cls.config,
            cls.data,
            [TimeBlock(0, 0, 24)],
            compute_max_cf=False,
        )

    def test_capture_cost_is_an_objective_component(self):
        self.assertIn("ccs_capture", self.artifacts.cost_components)
        self.assertGreater(float(self.data.ccs_cost.capture_yuan_per_tco2), 0.0)

    def test_all_five_ccs_pairs_have_retrofit_variables(self):
        retrofit = self.artifacts.variables["thermal_retrofit_to_ccs"]
        self.assertEqual(retrofit.shape, (31, 5))
        self.assertEqual(len(self.artifacts.index["ccs_pairs"]), 5)

    def test_chp_new_build_is_disabled_but_retrofit_is_available(self):
        new_capacity = self.artifacts.variables["thermal_new"]
        thermal_index = self.artifacts.index["thermal_index"]
        for technology in ("cchp", "cchpccs", "gchp", "gchpccs"):
            for province_position in range(31):
                self.assertEqual(
                    new_capacity[province_position, thermal_index[technology]].UB,
                    0.0,
                )

    def test_nuclear_upper_and_shared_biomass_upper_are_enforced(self):
        capacity = self.artifacts.variables["thermal_capacity"]
        thermal_index = self.artifacts.index["thermal_index"]
        nuclear_upper = self.artifacts.index["nuclear_capacity_upper_gw"]
        nuclear_k = thermal_index["nuclear"]
        for province_position, upper in enumerate(nuclear_upper):
            self.assertAlmostEqual(
                capacity[province_position, nuclear_k].UB,
                float(upper),
                places=9,
            )
        self.assertIsNotNone(
            self.artifacts.model.getConstrByName(
                "biomass_beccs_shared_capacity_upper_s4_34[0]"
            )
        )

    def test_battery_floor_is_applied_to_storage_capacity(self):
        storage_capacity = self.artifacts.variables["storage_capacity"]
        battery_k = self.artifacts.index["storage_index"]["battery"]
        expected = (
            self.data.battery_bounds.set_index("province_code")
            .capacity_floor_gw.reindex(self.artifacts.index["province_codes"])
            .to_numpy(float)
        )
        for province_position, floor in enumerate(expected):
            self.assertAlmostEqual(
                storage_capacity[province_position, battery_k].LB,
                float(floor),
                places=9,
            )


if __name__ == "__main__":
    unittest.main()
