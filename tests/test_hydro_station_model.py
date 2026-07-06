from __future__ import annotations

import unittest

import numpy as np

from cispo_model.config import load_model_config
from cispo_model.data import load_model_data
from cispo_model.hydro import HydroProfileReader
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


if __name__ == "__main__":
    unittest.main()
