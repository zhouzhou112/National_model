from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import xarray as xr
except ModuleNotFoundError:
    xr = None

from cispo_model.config import load_model_config
from cispo_model.wave_energy import (
    WaveCapacityFactorStore,
    wave_cost_parameters,
)
if xr is not None:
    from scripts.build_wave_energy_inputs import map_to_existing_marine_grid
else:
    map_to_existing_marine_grid = None


class WaveEnergyTests(unittest.TestCase):
    def test_base_is_disabled_and_overlay_is_explicit(self):
        base = load_model_config()
        wave = load_model_config(
            scenario_path="config/scenarios/wave_energy_medium_v1.json"
        )
        self.assertFalse(base.raw["features"]["wave_energy"])
        self.assertTrue(wave.raw["features"]["wave_energy"])
        self.assertEqual(
            wave.raw["wave_energy"]["profile_year_by_planning_year"]["2060"],
            2050,
        )
        self.assertEqual(
            wave.raw["wave_energy"]["connection_treatment"],
            "independent_cost_adders_no_shared_offwind_export",
        )
        self.assertEqual(
            wave.raw["wave_energy"]["contract_version"],
            "wave_existing_grid_v2",
        )

    @unittest.skipIf(xr is None, "optional wave preprocessing tests require xarray")
    def test_mapping_keeps_only_unique_existing_marine_grids(self):
        points = pd.DataFrame(
            {
                "grid_uid": ["G1", "G2", "G3"],
                "grid_id": [1, 2, 3],
                "lon": [120.0, 120.25, 121.0],
                "lat": [30.0, 30.0, 31.0],
                "is_land": [0, 1, 0],
            }
        )
        keep, positions, differences = map_to_existing_marine_grid(
            np.asarray([120.0, 120.25, 125.0]),
            np.asarray([30.00005, 30.0, 35.0]),
            points,
            tolerance_degrees=0.02,
        )
        np.testing.assert_array_equal(keep, [True, False, False])
        np.testing.assert_array_equal(positions, [0])
        self.assertLess(differences[0], 0.02)

    @unittest.skipIf(xr is None, "optional wave NetCDF tests require xarray")
    def test_netcdf_reader_selects_exact_scenario_and_grid_order(self):
        hours = 8760
        grid_ids = np.asarray([11, 22], dtype=np.int64)
        capacity_factor = np.zeros((3, hours, 2), dtype=np.float32)
        capacity_factor[1, :, 0] = 0.25
        capacity_factor[1, :, 1] = 0.75
        dataset = xr.Dataset(
            data_vars={
                "capacity_factor": (
                    ("scenario", "time", "grid"),
                    capacity_factor,
                ),
                "scenario_year": ("scenario", [2030, 2030, 2030]),
                "scenario_code": ("scenario", [0, 1, 2]),
                "grid_id": ("grid", grid_ids),
            },
            coords={
                "time": np.arange(
                    np.datetime64("2023-01-01T00"),
                    np.datetime64("2024-01-01T00"),
                    np.timedelta64(1, "h"),
                ),
                "scenario": np.arange(3),
                "grid": np.arange(2),
            },
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "wave.nc"
            dataset.to_netcdf(path)
            store = WaveCapacityFactorStore(
                path,
                profile_year=2030,
                scenario="medium",
                expected_hours=hours,
            )
            block = store.read([22, 11], 0, 24)
            store.close()
        self.assertEqual(block.shape, (24, 2))
        np.testing.assert_allclose(block[:, 0], 0.75)
        np.testing.assert_allclose(block[:, 1], 0.25)

    def test_cost_adders_are_site_specific_and_convert_currency(self):
        config = load_model_config(
            scenario_path="config/scenarios/wave_energy_medium_v1.json"
        )
        sites = __import__("pandas").DataFrame(
            {
                "water_depth_m": [0.0, 100.0],
                "distance_to_shore_km": [0.0, 50.0],
            }
        )
        capex, fixed_om, lifetime = wave_cost_parameters(config, sites)
        self.assertAlmostEqual(capex[0], 2777.0 * 7.8)
        self.assertAlmostEqual(
            capex[1], (2777.0 + 0.66 * 100.0 + 2.97 * 50.0) * 7.8
        )
        self.assertAlmostEqual(fixed_om, 0.027)
        self.assertAlmostEqual(lifetime, 25.0)


if __name__ == "__main__":
    unittest.main()
