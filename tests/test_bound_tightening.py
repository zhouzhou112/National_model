from __future__ import annotations

import unittest
from copy import deepcopy
from types import SimpleNamespace

import numpy as np

from cispo_model.config import ModelConfig, load_model_config
from cispo_model.data import load_model_data
from cispo_model.monolithic import (
    _reservoir_release_upper_scaled,
    build_full_year_monolithic,
)


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
            optimization_start_hour=3960,
        )

    @classmethod
    def tearDownClass(cls):
        cls.artifacts.model.dispose()

    def test_new_capacity_bounds_are_exactly_implied_by_existing_capacity_bounds(self):
        variables = self.artifacts.variables
        index = self.artifacts.index
        vre_headroom = np.asarray(
            index["vre_capacity_effective_upper_gw"], dtype=float
        ) - np.asarray(index["vre_capacity_floor_gw"], dtype=float)
        np.testing.assert_allclose(
            np.asarray(variables["vre_new"].UB),
            vre_headroom,
            rtol=0.0,
            atol=0.0,
        )
        self.assertTrue((vre_headroom >= 0.0).all())
        self.assertTrue(
            (
                np.asarray(variables["vre_capacity"].UB)
                >= np.asarray(variables["vre_capacity"].LB)
            ).all()
        )
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
        selected_horizon_sink_capacity = (
            sink_capacity
            * float(self.artifacts.index["annual_flow_scaling_factor"])
        )
        self.assertTrue(
            np.allclose(
                np.asarray(self.artifacts.variables["co2_ship"].UB),
                np.broadcast_to(
                    selected_horizon_sink_capacity,
                    np.asarray(self.artifacts.variables["co2_ship"].UB).shape,
                ),
            )
        )
        self.assertTrue(
            np.allclose(
                np.asarray(self.artifacts.variables["dac_capture"].UB),
                float(selected_horizon_sink_capacity.sum()),
            )
        )
        self.assertEqual(
            self.artifacts.index["explicit_bound_tightening"]["spur_trunk"],
            "no finite UB added: installed interface augmentation above minimum remains feasible",
        )

    def test_annual_flow_accounts_are_scaled_to_selected_horizon(self):
        index = self.artifacts.index
        fraction = 1.0 / float(self.config.hours)
        self.assertAlmostEqual(index["annual_flow_scaling_factor"], fraction)
        self.assertAlmostEqual(
            index["selected_horizon_carbon_limit_mtco2"],
            index["annual_carbon_limit_mtco2_per_year"] * fraction,
        )
        self.assertTrue(
            np.allclose(
                index["selected_horizon_biomass_limit_pj"],
                np.asarray(index["annual_biomass_limit_pj_per_year"]) * fraction,
            )
        )
        self.assertTrue(
            np.allclose(
                index["selected_horizon_co2_sink_injection_upper_mtco2"],
                np.asarray(
                    index["annual_co2_sink_injection_upper_mtco2_per_year"]
                )
                * fraction,
            )
        )

    def test_nonwinter_offset_build_uses_exact_selected_hour(self):
        self.assertEqual(
            self.artifacts.index["optimization_start_hour"],
            3960,
        )
        self.assertEqual(
            self.artifacts.index["optimization_stop_hour_exclusive"],
            3961,
        )
        np.testing.assert_allclose(
            self.artifacts.index["baseline_load_gw"],
            self.data.load_gw[:, 3960:3961],
        )

    def test_reservoir_flow_bounds_are_finite_without_extra_constraints(self):
        variables = self.artifacts.variables
        turbine = variables["reservoir_turbine_flow"]
        spill = variables["reservoir_spill_flow"]
        self.assertEqual(turbine.shape, spill.shape)
        turbine_upper = np.asarray(turbine.UB, dtype=float)
        spill_upper = np.asarray(spill.UB, dtype=float)
        self.assertTrue(np.isfinite(turbine_upper).all())
        self.assertTrue(np.isfinite(spill_upper).all())
        self.assertTrue((turbine_upper >= 0.0).all())
        self.assertTrue((spill_upper >= 0.0).all())
        self.assertTrue((turbine_upper <= spill_upper).all())
        audit = self.artifacts.index["reservoir_flow_bound_audit"]
        self.assertTrue(audit["all_bounds_finite"])
        self.assertEqual(
            audit["method"],
            "cyclic_total_plus_hourly_storage_cascade_v1",
        )
        model_variable_names = {
            variable.VarName for variable in self.artifacts.model.getVars()
        }
        self.assertFalse(
            any(
                name.startswith("reservoir_total_release_flow_1000m3s")
                for name in model_variable_names
            )
        )
        self.assertFalse(
            any(
                constraint.ConstrName.startswith(
                    "reservoir_turbine_within_total_release"
                )
                for constraint in self.artifacts.model.getConstrs()
            )
        )

    def test_reservoir_release_bounds_propagate_lagged_cascade_inflow(self):
        hydro = SimpleNamespace(
            reservoir_local_inflow_m3s=np.asarray(
                [[1000.0, 2000.0], [3000.0, 4000.0]], dtype=float
            ),
            reservoir_active_storage_m3=np.asarray([0.0, 0.0]),
            cascade_station_local_rows=np.asarray([0, 1], dtype=np.int64),
            cascade_edge_source_local_rows=[np.asarray([0], dtype=np.int64)],
            cascade_edge_target_local_rows=[np.asarray([1], dtype=np.int64)],
            cascade_edge_target_weights=[np.asarray([1.0])],
            cascade_edge_lag_h=[1],
            cascade_edge_transfer_fraction=[np.asarray([0.5, 1.0])],
        )
        upper = _reservoir_release_upper_scaled(hydro, flow_scale_m3s=1000.0)
        self.assertEqual(upper.shape, (2, 2))
        # Headwater release is bounded by its own two-hour cyclic inflow.
        np.testing.assert_allclose(upper[0], [1.0, 2.0], atol=2.0e-12)
        # At t=0/t=1, the lagged upstream bounds are 2 and 1 respectively.
        np.testing.assert_allclose(upper[1], [4.0, 5.0], atol=6.0e-12)
        self.assertGreaterEqual(float(upper[1].sum()), 9.0)

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
