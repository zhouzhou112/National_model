from __future__ import annotations

import unittest

import pandas as pd

from cispo_model.config import load_model_config
from cispo_model.data import CapacityFactorStore


class WeatherTimeAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.config = load_model_config()
        self.index = pd.DataFrame(
            {
                "technology": ["pv", "pv"],
                "year": [2023, 2024],
                "zarr_path": ["unused_2023.zarr", "unused_2024.zarr"],
            }
        )

    def test_2024_beijing_natural_year_is_8760_hours_without_february_29(self):
        store = CapacityFactorStore(
            self.index,
            self.config.weather_year,
            self.config.weather_time_alignment,
        )
        self.assertEqual(len(store.model_local_time), 8760)
        self.assertEqual(str(store.model_local_time[0]), "2024-01-01 00:00:00")
        self.assertEqual(str(store.model_local_time[-1]), "2024-12-31 23:00:00")
        self.assertFalse(
            bool(
                (
                    (store.model_local_time.month == 2)
                    & (store.model_local_time.day == 29)
                ).any()
            )
        )

    def test_beijing_year_uses_2023_tail_and_skips_2024_leap_day(self):
        store = CapacityFactorStore(
            self.index,
            self.config.weather_year,
            self.config.weather_time_alignment,
        )
        self.assertEqual(store.source_years, (2023, 2024))
        self.assertEqual(store.model_source_year[:9].tolist(), [2023] * 8 + [2024])
        self.assertEqual(
            store.model_source_hour[:9].tolist(),
            list(range(8752, 8760)) + [0],
        )
        march_first = store.model_local_time.get_loc("2024-03-01 00:00:00")
        previous = store.model_local_time.get_loc("2024-02-28 23:00:00")
        self.assertEqual(march_first, previous + 1)
        self.assertEqual(
            int(store.model_source_hour[march_first])
            - int(store.model_source_hour[previous]),
            25,
        )
        self.assertEqual(int(store.model_source_hour[-1]), 8775)

    def test_config_records_both_required_source_years(self):
        self.assertEqual(self.config.weather_year, 2024)
        self.assertEqual(
            self.config.weather_time_alignment,
            "beijing_natural_year_drop_feb29_v1",
        )
        self.assertEqual(self.config.weather_source_years, (2023, 2024))


if __name__ == "__main__":
    unittest.main()
