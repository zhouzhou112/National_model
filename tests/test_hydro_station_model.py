from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from cispo_model.config import load_model_config
from cispo_model.data import load_model_data
from cispo_model.hydro import HydroProfileReader, _connected_cascade_node_ids
from cispo_model.timeblocks import TimeBlock


class HydroStationModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_model_config()
        cls.data = load_model_data(cls.config)

    def test_installed_and_potential_classification_rules(self):
        hydro = self.data.hydro_stations
        operating = hydro.status_model.eq("operating")
        self.assertTrue(
            hydro.loc[operating, "operation_type_model"].equals(
                hydro.loc[operating, "installed_operation_type_assigned"]
            )
        )
        potential = ~operating
        expected = np.where(
            hydro.loc[potential, "capacity_potential_gw"].to_numpy(float) > 0.75,
            "reservoir_storage",
            "run_of_river",
        )
        self.assertTrue(
            np.array_equal(
                hydro.loc[potential, "operation_type_model"].to_numpy(str), expected
            )
        )

    def test_station_level_reservoir_hydrology(self):
        with HydroProfileReader(self.config, self.data) as reader:
            block = reader.read_linear_block(TimeBlock(0, 0, 24))
        expected_reservoirs = int(
            self.data.hydro_stations.operation_type_model.eq(
                "reservoir_storage"
            ).sum()
        )
        self.assertEqual(len(block.reservoir_station_rows), expected_reservoirs)
        self.assertEqual(block.reservoir_inflow_gwh.shape, (expected_reservoirs, 24))
        self.assertEqual(
            block.reservoir_energy_upper_gwh.shape, (expected_reservoirs,)
        )
        self.assertTrue(np.isfinite(block.reservoir_inflow_gwh).all())
        self.assertTrue((block.reservoir_inflow_gwh >= 0.0).all())
        self.assertTrue((block.reservoir_energy_upper_gwh >= 0.0).all())
        local_rows = np.concatenate(
            list(block.reservoir_local_rows_by_province.values())
        )
        self.assertEqual(set(local_rows.tolist()), set(range(expected_reservoirs)))
        self.assertEqual(block.reservoir_local_inflow_m3s.shape, (expected_reservoirs, 24))
        self.assertEqual(block.reservoir_active_storage_m3.shape, (expected_reservoirs,))
        self.assertEqual(
            block.reservoir_generation_conversion_gw_per_m3s.shape,
            (expected_reservoirs,),
        )
        self.assertTrue((block.reservoir_local_inflow_m3s >= 0.0).all())
        positive = block.reservoir_local_inflow_m3s[
            block.reservoir_local_inflow_m3s > 0.0
        ]
        self.assertGreaterEqual(
            float(positive.min()),
            float(self.config.raw["hydro"]["hydrology_flow_zero_tolerance_m3s"]),
        )

    def test_reservoir_variable_scaling_preserves_physical_equations(self):
        hydro = self.config.raw["hydro"]
        flow_scale = float(hydro["reservoir_flow_variable_scale_m3s"])
        volume_scale = float(hydro["reservoir_volume_variable_scale_m3"])
        physical_flow_m3s = 2750.0
        model_flow = physical_flow_m3s / flow_scale
        physical_volume_change_m3 = physical_flow_m3s * 3600.0
        model_volume_change = model_flow * flow_scale * 3600.0 / volume_scale
        self.assertAlmostEqual(
            model_volume_change * volume_scale,
            physical_volume_change_m3,
            places=9,
        )
        conversion_gw_per_m3s = 8.5e-4
        self.assertAlmostEqual(
            model_flow * flow_scale * conversion_gw_per_m3s,
            physical_flow_m3s * conversion_gw_per_m3s,
            places=12,
        )

    def test_production_numerics_use_crossover_and_all_logical_cpus(self):
        numerics = self.config.raw["numerics"]
        self.assertEqual(int(numerics["crossover"]), 1)
        self.assertEqual(int(numerics["threads"]), -1)

    def test_environmental_flow_uses_p30_proxy(self):
        hydro = self.config.raw["hydro"]
        self.assertEqual(
            hydro["environmental_flow_dataset"],
            "monthly_environmental_flow_2019_p30",
        )
        self.assertEqual(hydro["environmental_flow_variable"], "monthly_p30_proxy_m3s")
        timeseries = self.data_root_timeseries()
        self.assertIn("monthly_environmental_flow_2019_p30", set(timeseries.dataset))
        row = timeseries.loc[
            timeseries.dataset.eq("monthly_environmental_flow_2019_p30")
        ].iloc[0]
        self.assertIn("monthly_p30_proxy_m3s", str(row.variables))

    def test_core_cascade_topology_loads(self):
        self.assertEqual(len(self.data.hydro_cascade_nodes), 142)
        self.assertEqual(len(self.data.hydro_cascade_edges), 124)
        with HydroProfileReader(self.config, self.data) as reader:
            block = reader.read_linear_block(TimeBlock(0, 0, 24))
        self.assertEqual(len(block.cascade_station_local_rows), 138)
        self.assertEqual(len(block.cascade_isolated_node_ids), 8)
        self.assertEqual(len(block.cascade_edge_ids), 124)
        self.assertEqual(len(block.cascade_edge_lag_h), 124)
        self.assertTrue((block.cascade_edge_lag_h >= 0).all())
        for source_rows, target_rows, weights in zip(
            block.cascade_edge_source_local_rows,
            block.cascade_edge_target_local_rows,
            block.cascade_edge_target_weights,
        ):
            self.assertGreater(len(source_rows), 0)
            self.assertGreater(len(target_rows), 0)
            self.assertAlmostEqual(float(weights.sum()), 1.0, places=9)

    def test_isolated_single_station_nodes_use_identical_independent_inflow(self):
        nodes = self.data.hydro_cascade_nodes
        edges = self.data.hydro_cascade_edges
        connected, isolated = _connected_cascade_node_ids(nodes, edges)
        self.assertEqual(len(connected), 134)
        self.assertEqual(len(isolated), 8)
        self.assertTrue(
            nodes.loc[nodes.node_id.isin(isolated), "model_station_count"].eq(1).all()
        )
        isolated_station_ids = {
            str(value)
            for value in nodes.loc[nodes.node_id.isin(isolated), "hydrochn_row_ids"]
        }
        global_rows = np.flatnonzero(
            self.data.hydro_stations.hydrochn_row_id.astype(str).isin(
                isolated_station_ids
            )
        )
        with HydroProfileReader(self.config, self.data) as reader:
            block = reader.read_linear_block(TimeBlock(0, 0, 24))
            expected_local_inflow = reader._available_flow_for_rows(
                TimeBlock(0, 0, 24), global_rows
            )
        local_by_global = {
            int(global_row): local_row
            for local_row, global_row in enumerate(block.reservoir_station_rows)
        }
        isolated_local_rows = np.asarray(
            [local_by_global[int(global_row)] for global_row in global_rows], dtype=int
        )
        self.assertFalse(
            set(isolated_local_rows.tolist()).intersection(
                set(block.cascade_station_local_rows.tolist())
            )
        )
        np.testing.assert_allclose(
            block.reservoir_local_inflow_m3s[isolated_local_rows],
            expected_local_inflow.T,
            rtol=0.0,
            atol=0.0,
        )

    def test_isolated_multi_station_node_is_rejected(self):
        node_frame = pd.DataFrame(
            {
                "node_id": ["connected", "isolated"],
                "hydrochn_row_ids": ["a", "b;c"],
                "model_station_count": [1, 2],
            }
        )
        edge_frame = pd.DataFrame(
            {"source_node_id": ["connected"], "target_node_id": ["connected"]}
        )
        with self.assertRaisesRegex(ValueError, "isolated cascade node"):
            _connected_cascade_node_ids(node_frame, edge_frame)

    @staticmethod
    def data_root_timeseries():
        import pandas as pd

        from cispo_model.data import DATA_ROOT

        return pd.read_csv(DATA_ROOT / "hydro" / "timeseries_index.csv")


if __name__ == "__main__":
    unittest.main()
