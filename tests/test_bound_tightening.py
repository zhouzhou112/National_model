from __future__ import annotations

import unittest
from copy import deepcopy

import numpy as np

from cispo_model.config import ModelConfig, load_model_config
from cispo_model.data import load_model_data
from cispo_model.monolithic import build_full_year_monolithic


class BoundTighteningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_model_config()
        cls.data = load_model_data(cls.config)
        cls.artifacts = build_full_year_monolithic(
            cls.config,
            cls.data,
            compute_max_cf=False,
            optimization_hours=1,
        )

    @classmethod
    def tearDownClass(cls):
        cls.artifacts.model.dispose()

    def test_new_capacity_bounds_are_exactly_implied_by_existing_capacity_bounds(self):
        variables = self.artifacts.variables
        index = self.artifacts.index
        self.assertTrue(
            np.allclose(
                np.asarray(variables["wave_new"].UB),
                self.data.wave.sites.capacity_upper_gw.to_numpy(dtype=float)
                - np.asarray(index["wave_capacity_floor_gw"]),
            )
        )
        self.assertTrue(
            np.allclose(
                np.asarray(variables["hydro_new"].UB),
                self.data.hydro_stations.capacity_potential_gw.to_numpy(dtype=float)
                - np.asarray(index["hydro_capacity_floor_gw"]),
            )
        )
        nuclear = index["thermal_index"]["nuclear"]
        self.assertTrue(
            np.allclose(
                np.asarray(variables["thermal_new"].UB)[:, nuclear],
                np.asarray(index["nuclear_capacity_upper_gw"])
                - np.asarray(index["thermal_capacity_floor_gw"])[:, nuclear],
            )
        )
        phs = index["storage_index"]["phs"]
        self.assertTrue(
            np.allclose(
                np.asarray(variables["storage_new"].UB)[:, phs],
                np.asarray(index["storage_capacity_upper_gw"])[:, phs]
                - np.asarray(index["storage_capacity_floor_gw"])[:, phs],
            )
        )
        self.assertTrue(
            np.isinf(np.asarray(variables["storage_new"].UB)[:, index["storage_index"]["battery"]]).all()
        )

    def test_co2_and_dac_bounds_are_implied_by_sink_capacity(self):
        sinks = self.artifacts.index["ccs_sinks"]
        injection_field = self.config.raw["ccs_injection_field"]
        sink_capacity = sinks[injection_field].to_numpy(dtype=float)
        self.assertTrue(
            np.allclose(
                np.asarray(self.artifacts.variables["co2_ship"].UB),
                np.broadcast_to(
                    sink_capacity,
                    np.asarray(self.artifacts.variables["co2_ship"].UB).shape,
                ),
            )
        )
        self.assertTrue(
            np.allclose(
                np.asarray(self.artifacts.variables["dac_capture"].UB),
                float(sink_capacity.sum()),
            )
        )
        self.assertEqual(
            self.artifacts.index["explicit_bound_tightening"]["spur_trunk"],
            "no finite UB added: installed interface augmentation above minimum remains feasible",
        )

    def test_independent_phs_energy_adds_only_province_level_annual_variables(self):
        raw = deepcopy(self.config.raw)
        phs_total_capex = {
            "2030": 5281.06104,
            "2040": 4758.9789599999995,
            "2050": 4758.9789599999995,
            "2060": 4256.97696,
        }
        raw["storage_design"]["phs_energy_capacity_mode"] = (
            "independent_power_energy_v1"
        )
        raw["storage_design"][
            "phs_power_capex_yuan_per_kw_by_planning_year"
        ] = {
            year: value / 2.0
            for year, value in phs_total_capex.items()
        }
        raw["storage_design"][
            "phs_energy_capex_yuan_per_kwh_by_planning_year"
        ] = {
            year: value / 16.0
            for year, value in phs_total_capex.items()
        }
        separated = ModelConfig(
            self.config.path,
            raw,
            self.config.scenario_path,
            self.config.solver_path,
            self.config.formulation_path,
        )
        separated.validate()
        artifacts = build_full_year_monolithic(
            separated,
            self.data,
            compute_max_cf=False,
            optimization_hours=1,
        )
        try:
            self.assertIn("phs_energy_capacity", artifacts.variables)
            self.assertEqual(
                artifacts.variables["phs_energy_capacity"].shape,
                (len(self.data.provinces),),
            )
            self.assertEqual(
                artifacts.model.NumVars - self.artifacts.model.NumVars,
                len(self.data.provinces),
            )
        finally:
            artifacts.model.dispose()


if __name__ == "__main__":
    unittest.main()
