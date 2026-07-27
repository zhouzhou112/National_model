from __future__ import annotations

import unittest
import inspect

import numpy as np

from cispo_model.config import (
    capital_recovery_factor,
    load_model_config,
    resolve_minimum_system_inertia_seconds,
)
from cispo_model.data import load_model_data
from cispo_model.preflight import estimate_full_model_scale, run_preflight
from cispo_model.timeblocks import make_time_blocks
from cispo_model import load_center


class ModelFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_model_config()
        cls.data = load_model_data(cls.config)

    def test_boundary_and_first_planning_year(self):
        self.assertEqual(self.config.boundary_year, 2025)
        self.assertEqual(self.config.planning_year, 2030)
        self.assertEqual(self.config.hours, 8760)

    def test_sequential_year_contract(self):
        self.assertEqual(self.config.planning_years, (2030, 2040, 2050, 2060))
        expected_boundaries = {2030: 2025, 2040: 2030, 2050: 2040, 2060: 2050}
        for planning_year, boundary_year in expected_boundaries.items():
            year_config = self.config.for_planning_year(planning_year)
            self.assertEqual(year_config.boundary_year, boundary_year)

    def test_single_full_year_block_covers_every_hour_once(self):
        blocks = make_time_blocks(8760, 8760)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[-1].hours, 8760)
        covered = [hour for block in blocks for hour in range(block.hour_start, block.hour_stop)]
        self.assertEqual(covered, list(range(8760)))

    def test_supported_horizons_are_exact_and_test_scoped(self):
        one_month = self.config.horizon("one_month")
        six_months = self.config.horizon("six_months")
        full_year = self.config.horizon("full_year")
        self.assertEqual(one_month["hours"], 744)
        self.assertEqual(six_months["hours"], 4344)
        self.assertEqual(full_year["hours"], 8760)
        self.assertTrue(one_month["test_only"])
        self.assertTrue(six_months["test_only"])
        self.assertFalse(full_year["test_only"])

    def test_horizon_scale_estimates_are_monotonic(self):
        estimates = [
            estimate_full_model_scale(self.config, self.data, hours).variables
            for hours in (744, 4344, 8760)
        ]
        self.assertLess(estimates[0], estimates[1])
        self.assertLess(estimates[1], estimates[2])

    def test_scale_estimator_covers_all_current_variable_blocks(self):
        self.assertTrue(self.config.raw["features"]["wave_energy"])
        self.assertEqual(
            estimate_full_model_scale(self.config, self.data, 24).variables,
            345_992,
        )
        self.assertEqual(
            estimate_full_model_scale(self.config, self.data, 8760).variables,
            41_186_792,
        )

    def test_nuclear_biomass_and_battery_bounds_are_explicit(self):
        self.assertAlmostEqual(
            float(self.data.nuclear_floor.capacity_floor_gw.sum()), 106.764, places=6
        )
        self.assertAlmostEqual(
            float(self.data.nuclear_upper.capacity_upper_gw.sum()), 110.0, places=6
        )
        self.assertTrue(
            self.data.nuclear_floor.set_index("province_code").capacity_floor_gw.le(
                self.data.nuclear_upper.set_index("province_code").capacity_upper_gw
                + 1e-9
            ).all()
        )
        self.assertAlmostEqual(
            float(self.data.battery_bounds.capacity_floor_gw.sum()), 65.85, places=6
        )
        self.assertAlmostEqual(
            float(self.data.biomass_capacity_bounds.capacity_upper_gw.sum()),
            473.85372630036,
            places=6,
        )
        adjusted = self.data.biomass_capacity_bounds.loc[
            self.data.biomass_capacity_bounds.capacity_upper_adjusted_to_floor.astype(bool)
        ]
        self.assertEqual(adjusted.province_code.astype(int).tolist(), [31])

    def test_biomass_and_beccs_fuel_costs_are_positive_and_complete(self):
        biomass_fuel = self.data.fuel.loc[
            self.data.fuel.technology.isin(["bio", "bioccs"])
        ]
        self.assertEqual(len(biomass_fuel), 31 * 2)
        self.assertTrue(biomass_fuel.dispatch_allowed.astype(bool).all())
        self.assertTrue(biomass_fuel.fuel_cost_yuan_per_mwh.gt(0.0).all())

    def test_full_year_memory_gate_is_build_safe(self):
        self.assertEqual(
            float(self.config.horizon("full_year")["minimum_available_memory_gb"]),
            96.0,
        )

    def test_load_center_dense_expressions_are_not_duplicated(self):
        source = inspect.getsource(load_center.attach_annual_load_center_network)
        self.assertIn(
            "province_external_received[p] - province_external_sent[p]",
            source,
        )
        self.assertNotIn(
            "== received_energy[p] - sent_energy[p]",
            source,
        )
        self.assertNotIn(
            "load_center_reservoir_generation_closure_p",
            source,
        )
        self.assertIn("reservoir_route_counts", source)

    def test_full_data_preflight_has_no_hard_fail(self):
        report = run_preflight(self.config, self.data)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["status_counts"]["HARD_FAIL"], 0)
        self.assertEqual(report["scale_estimate"]["block_count"], 1)
        self.assertEqual(self.config.raw["construction"]["architecture"], "full_year_monolithic_lp")

    def test_hourly_load_components_are_complete_and_close(self):
        self.assertEqual(
            set(self.data.load_components_gw),
            {"base_residual", "heating", "cooling", "ev"},
        )
        for values in self.data.load_components_gw.values():
            self.assertEqual(values.shape, (31, 8760))
            self.assertTrue(np.isfinite(values).all())
            self.assertGreaterEqual(float(values.min()), 0.0)
        closure = np.abs(
            self.data.load_gw - sum(self.data.load_components_gw.values())
        ).max()
        self.assertLessEqual(float(closure), 1e-9)

    def test_crf_is_numerically_stable(self):
        value = capital_recovery_factor(0.074, 25)
        self.assertGreater(value, 0.08)
        self.assertLess(value, 0.10)

    def test_reviewed_security_parameters_are_explicit(self):
        security = self.config.raw["security"]
        self.assertAlmostEqual(float(security["capacity_margin_fraction"]), 0.05)
        self.assertAlmostEqual(float(security["inertia_reference_seconds"]), 3.5)
        self.assertAlmostEqual(float(security["inertia_tolerance_fraction"]), 1.0)
        self.assertAlmostEqual(
            resolve_minimum_system_inertia_seconds(security), 3.5
        )

    def test_legacy_effective_inertia_override_remains_supported(self):
        security = {
            "minimum_system_inertia_seconds": 3.0,
            "inertia_reference_seconds": 3.5,
            "inertia_tolerance_fraction": 1.0,
        }
        self.assertAlmostEqual(
            resolve_minimum_system_inertia_seconds(security), 3.0
        )

    def test_phs_floor_and_pipeline_upper_are_data_bounded(self):
        bounds_2030 = self.data.storage_bounds
        self.assertEqual(len(bounds_2030), 31)
        self.assertTrue((bounds_2030.technology == "phs").all())
        self.assertAlmostEqual(float(bounds_2030.capacity_floor_gw.sum()), 65.94, places=6)
        self.assertAlmostEqual(float(bounds_2030.capacity_upper_gw.sum()), 249.191, places=6)
        self.assertTrue(
            (bounds_2030.capacity_floor_gw <= bounds_2030.capacity_upper_gw + 1e-9).all()
        )

    def test_city_337_is_the_production_load_center_scenario(self):
        centers = self.data.load_centers
        self.assertEqual(self.config.raw["load_center_network"]["scenario"], "city_337")
        self.assertEqual(
            self.config.raw["load_center_network"]["input_subdirectory"],
            "load_center_network/city_337",
        )
        self.assertEqual(len(centers), 337)
        self.assertEqual(centers.province_code.nunique(), 31)
        share_error = (
            centers.groupby("province_code").annual_demand_share_in_province.sum()
            .sub(1.0).abs().max()
        )
        self.assertLessEqual(float(share_error), 1e-9)

    def test_spatial_generation_routes_are_complete(self):
        active_vre = set(self.data.vre_sites.grid_uid)
        routed_vre = set(self.data.vre_load_center_routes.grid_uid)
        self.assertFalse(active_vre.difference(routed_vre))
        hydro = set(self.data.hydro_stations.hydrochn_row_id)
        routed_hydro = set(self.data.hydro_load_center_routes.hydrochn_row_id)
        self.assertFalse(hydro.difference(routed_hydro))

    def test_intra_load_center_edges_are_within_province_and_initialized(self):
        centers = self.data.load_centers.set_index("load_center_id")
        edges = self.data.intra_load_center_edges
        from_province = edges.from_load_center_id.map(centers.province_code).to_numpy()
        to_province = edges.to_load_center_id.map(centers.province_code).to_numpy()
        self.assertTrue(np.array_equal(from_province, to_province))
        self.assertEqual(len(edges), 642)
        self.assertTrue((edges.initial_capacity_gw >= 0).all())
        self.assertGreater(float(edges.initial_capacity_gw.sum()), 0.0)
        self.assertTrue((edges.unit_cost_yuan_per_kw > 0).all())

    def test_city_337_2025_network_initialization_closes(self):
        self.assertAlmostEqual(
            float(self.data.initial_spur.initial_spur_capacity_gw.sum()),
            1310.0,
            places=5,
        )
        self.assertAlmostEqual(
            float(self.data.substations.initial_trunk_capacity_gw.sum()),
            1310.0,
            places=5,
        )
        self.assertEqual(
            int(self.data.intra_load_center_edges.initial_capacity_gw.gt(1e-12).sum()),
            203,
        )
        self.assertAlmostEqual(
            float(self.data.intra_load_center_edges.initial_capacity_gw.sum()),
            647.8400936079125,
            places=6,
        )

    def test_each_province_load_center_graph_is_connected(self):
        centers = self.data.load_centers
        edges = self.data.intra_load_center_edges
        for province_code, group in centers.groupby("province_code"):
            node_ids = set(group.load_center_id.astype(str))
            if len(node_ids) == 1:
                continue
            adjacency = {node_id: set() for node_id in node_ids}
            for row in edges.loc[edges.province_code.eq(province_code)].itertuples(index=False):
                adjacency[str(row.from_load_center_id)].add(str(row.to_load_center_id))
                adjacency[str(row.to_load_center_id)].add(str(row.from_load_center_id))
            visited = set()
            stack = [next(iter(node_ids))]
            while stack:
                node = stack.pop()
                if node in visited:
                    continue
                visited.add(node)
                stack.extend(adjacency[node].difference(visited))
            self.assertEqual(visited, node_ids, msg=f"disconnected province {province_code}")

    def test_interprovincial_flow_regularization_matches_cispo_units(self):
        # CISPO specifies 0.001 yuan/kWh, which is exactly 1 yuan/MWh.
        self.assertEqual(
            float(self.config.raw["network"]["flow_regularization_yuan_per_mwh"]),
            1.0,
        )
        technologies = set(
            self.data.lines.preset_technology.astype(str).str.upper()
        )
        self.assertEqual(technologies, {"AC", "DC"})
        self.assertEqual(
            int(self.data.lines.preset_technology.astype(str).str.upper().eq("AC").sum()),
            48,
        )
        self.assertEqual(
            int(self.data.lines.preset_technology.astype(str).str.upper().eq("DC").sum()),
            363,
        )


if __name__ == "__main__":
    unittest.main()
