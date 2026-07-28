from __future__ import annotations

from types import SimpleNamespace
import unittest

import numpy as np
import pandas as pd

from cispo_model.data import compute_intra_grid_vre_design


class _FakeCapacityFactors:
    def __init__(self) -> None:
        self.values = {
            "onshore_wind": {
                11: np.asarray([1.0, 0.0, 0.5, 0.0]),
            },
            "pv": {
                12: np.asarray([0.0, 1.0, 0.5, 0.0]),
                13: np.asarray([1.0, 1.0, 1.0, 1.0]),
            },
        }

    def read(self, source_technology, grid_ids, hour_start, hour_stop):
        return np.column_stack(
            [
                self.values[source_technology][int(grid_id)][hour_start:hour_stop]
                for grid_id in grid_ids
            ]
        )


class IntraGridVreDesignTests(unittest.TestCase):
    def test_equivalent_peak_preserves_wind_pv_complementarity(self):
        sites = pd.DataFrame(
            {
                "technology": ["onwind", "upv", "dpv"],
                "capacity_upper_gw": [2.0, 1.0, 99.0],
                "cf_source_technology": ["onshore_wind", "pv", "pv"],
                "cf_grid_id": [11, 12, 13],
            }
        )
        config = SimpleNamespace(
            hours=4,
            raw={"construction": {"hour_chunk_size": 2}},
        )
        data = SimpleNamespace(vre_sites=sites, cf=_FakeCapacityFactors())

        design = compute_intra_grid_vre_design(
            config,
            data,
            site_substation=["sub_a", "sub_a", "sub_b"],
            substation_ids=["sub_a", "sub_b"],
        )

        # Eq. S4-19: max_t((2*cf_wind + 1*cf_pv)/(2+1)) = 2/3.
        self.assertAlmostEqual(
            float(design.substation_equivalent_peak_cf[0]), 2.0 / 3.0, places=12
        )
        self.assertAlmostEqual(
            float(design.substation_equivalent_peak_gw[0]), 2.0, places=12
        )
        self.assertAlmostEqual(float(design.substation_potential_gw[0]), 3.0, places=12)
        self.assertEqual(int(design.site_substation_position[2]), -1)
        self.assertAlmostEqual(float(design.substation_potential_gw[1]), 0.0, places=12)

    def test_rejects_unknown_connected_substation(self):
        sites = pd.DataFrame(
            {
                "technology": ["onwind"],
                "capacity_upper_gw": [1.0],
                "cf_source_technology": ["onshore_wind"],
                "cf_grid_id": [11],
            }
        )
        config = SimpleNamespace(hours=1, raw={"construction": {"hour_chunk_size": 1}})
        data = SimpleNamespace(vre_sites=sites, cf=_FakeCapacityFactors())
        with self.assertRaisesRegex(ValueError, "unknown substations"):
            compute_intra_grid_vre_design(
                config,
                data,
                site_substation=["missing"],
                substation_ids=["sub_a"],
            )


if __name__ == "__main__":
    unittest.main()
