from __future__ import annotations

import unittest

import numpy as np

from cispo_model.config import capital_recovery_factor, load_model_config
from cispo_model.data import load_model_data
from cispo_model.preflight import estimate_full_model_scale, run_preflight
from cispo_model.timeblocks import make_time_blocks


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

    def test_full_data_preflight_has_no_hard_fail(self):
        report = run_preflight(self.config, self.data)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["status_counts"]["HARD_FAIL"], 0)
        self.assertEqual(report["scale_estimate"]["block_count"], 1)
        self.assertEqual(self.config.raw["construction"]["architecture"], "full_year_monolithic_lp")

    def test_crf_is_numerically_stable(self):
        value = capital_recovery_factor(0.074, 25)
        self.assertGreater(value, 0.08)
        self.assertLess(value, 0.10)

    def test_phs_floor_and_pipeline_upper_are_data_bounded(self):
        bounds_2030 = self.data.storage_bounds
        self.assertEqual(len(bounds_2030), 31)
        self.assertTrue((bounds_2030.technology == "phs").all())
        self.assertAlmostEqual(float(bounds_2030.capacity_floor_gw.sum()), 65.94, places=6)
        self.assertAlmostEqual(float(bounds_2030.capacity_upper_gw.sum()), 249.191, places=6)
        self.assertTrue(
            (bounds_2030.capacity_floor_gw <= bounds_2030.capacity_upper_gw + 1e-9).all()
        )

    def test_natural_earth_278_is_the_production_load_center_scenario(self):
        centers = self.data.load_centers
        self.assertEqual(self.config.raw["load_center_network"]["scenario"], "Natural_Earth_paper_replication_278")
        self.assertEqual(len(centers), 278)
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
        self.assertEqual(len(edges), 517)
        self.assertTrue((edges.initial_capacity_gw >= 0).all())
        self.assertGreater(float(edges.initial_capacity_gw.sum()), 0.0)
        self.assertTrue((edges.unit_cost_yuan_per_kw > 0).all())

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


if __name__ == "__main__":
    unittest.main()
