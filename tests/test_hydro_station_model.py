from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from cispo_model.config import load_model_config
from cispo_model.data import load_model_data
from cispo_model.hydro import (
    HydroProfileReader,
    _connected_cascade_node_ids,
    _reconcile_cascade_natural_inflow,
    _station_flow_share_by_comid,
)
from cispo_model.timeblocks import TimeBlock


class HydroReconciliationUnitTests(unittest.TestCase):
    def test_cascade_reconciliation_is_mass_closed_and_never_adds_water(self):
        node_flow = {
            "upstream": np.asarray([10.0, 20.0, 5.0]),
            "downstream": np.asarray([8.0, 25.0, 5.0]),
        }
        local, fractions, audit, rows = _reconcile_cascade_natural_inflow(
            node_flow,
            [("upstream", "downstream", 0, "edge_1")],
        )
        np.testing.assert_allclose(fractions[0], [0.8, 1.0, 1.0])
        np.testing.assert_allclose(local["downstream"], [0.0, 5.0, 0.0])
        np.testing.assert_allclose(
            fractions[0] * node_flow["upstream"] + local["downstream"],
            node_flow["downstream"],
        )
        self.assertEqual(audit["raw_negative_node_hours"], 1)
        self.assertEqual(rows[0]["adjusted_hours"], 1)


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
        self.assertGreater(float(positive.min()), 0.0)

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

    def test_provincial_aggregate_capacity_closes_2025_conventional_hydro(self):
        aggregate = self.data.hydro_aggregate_capacity
        station_capacity = float(
            self.data.hydro_stations.existing_capacity_gw.sum()
        )
        aggregate_capacity = float(
            aggregate.provincial_aggregate_capacity_gw.sum()
        )
        harmonized_capacity = float(
            aggregate.harmonized_conventional_capacity_gw.sum()
        )
        self.assertEqual(len(aggregate), 31)
        self.assertAlmostEqual(station_capacity, 297.8895, places=9)
        self.assertAlmostEqual(aggregate_capacity, 82.1105, places=9)
        self.assertAlmostEqual(harmonized_capacity, 380.0, places=9)
        self.assertAlmostEqual(
            station_capacity + aggregate_capacity,
            harmonized_capacity,
            places=9,
        )

    def test_provincial_aggregate_profile_and_reliability_scope(self):
        availability = self.data.hydro_aggregate_availability_cf
        self.assertEqual(availability.shape, (31, self.config.hours))
        self.assertTrue(np.isfinite(availability).all())
        self.assertTrue((availability >= 0.0).all())
        self.assertTrue((availability <= 1.0).all())
        hydro = self.config.raw["hydro"]
        self.assertEqual(
            hydro["provincial_aggregate_mode"],
            "fixed_existing_monthly_profile_v1",
        )
        for key in (
            "provincial_aggregate_up_reserve_credit",
            "provincial_aggregate_down_reserve_credit",
            "provincial_aggregate_capacity_credit",
            "provincial_aggregate_inertia_seconds",
        ):
            self.assertEqual(float(hydro[key]), 0.0)
        self.assertEqual(
            hydro["provincial_aggregate_connection_treatment"],
            "province_non_spatial_existing_no_spur_trunk",
        )

    def test_duplicate_comid_flow_shares_are_explicit_and_conservative(self):
        hydro = self.data.hydro_stations
        self.assertEqual(
            self.config.raw["hydro"]["duplicate_comid_flow_allocation"],
            "static_capacity_potential_share_v1",
        )
        shares = _station_flow_share_by_comid(hydro)
        grouped = pd.Series(shares).groupby(hydro.comid.to_numpy()).sum()
        np.testing.assert_allclose(
            grouped.to_numpy(dtype=float),
            np.ones(len(grouped), dtype=float),
            rtol=0.0,
            atol=1e-12,
        )
        counts = hydro.groupby("comid").size()
        duplicate_comids = counts[counts > 1].index
        duplicate_rows = hydro.comid.isin(duplicate_comids).to_numpy()
        self.assertEqual(len(duplicate_comids), 146)
        self.assertEqual(int(duplicate_rows.sum()), 319)
        self.assertTrue((shares[duplicate_rows] < 1.0).all())

    def test_duplicate_comid_available_flow_is_allocated_once(self):
        hydro = self.data.hydro_stations
        counts = hydro.groupby("comid").size()
        duplicate_comid = int(counts[counts > 1].index[0])
        rows = np.flatnonzero(hydro.comid.eq(duplicate_comid).to_numpy())
        block = TimeBlock(0, 0, 24)
        with HydroProfileReader(self.config, self.data) as reader:
            allocated = reader._available_flow_for_rows(block, rows)
            position = int(reader.comid_position[duplicate_comid])
            qout = np.asarray(
                reader.discharge.variables["qout_model_m3s"][
                    block.hour_start:block.hour_stop, position
                ],
                dtype=float,
            )
            month = int(reader.datetime.month.iloc[0])
            month_position = {
                int(value): i for i, value in enumerate(reader.month_values)
            }[month]
            environmental_flow = float(
                reader.environment.variables[reader.environment_variable][
                    month_position, position
                ]
            )
        expected = np.maximum(qout - environmental_flow, 0.0)
        expected[
            expected
            < float(
                self.config.raw["hydro"]["hydrology_flow_zero_tolerance_m3s"]
            )
        ] = 0.0
        np.testing.assert_allclose(
            allocated.sum(axis=1),
            expected,
            rtol=0.0,
            atol=1e-10,
        )

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
