from __future__ import annotations

import unittest

import pandas as pd

from cispo_model.data import _resolve_vre_cf_sites


class _CoverageOnlyCF:
    def __init__(self, coverage: dict[str, set[int]]):
        self.coverage = coverage

    def available_grid_ids(self, source_technology: str) -> set[int]:
        return set(self.coverage.get(source_technology, set()))


def _points() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "grid_uid": "G1",
                "grid_id": 1,
                "province_code": 11,
                "lon": 116.0,
                "lat": 40.0,
                "is_land": 1,
            },
            {
                "grid_uid": "G2",
                "grid_id": 2,
                "province_code": 11,
                "lon": 116.2,
                "lat": 40.0,
                "is_land": 1,
            },
            {
                "grid_uid": "G3",
                "grid_id": 3,
                "province_code": 11,
                "lon": 116.1,
                "lat": 39.9,
                "is_land": 0,
            },
        ]
    )


def _site(technology: str, grid_id: int = 1) -> pd.DataFrame:
    point = _points().set_index("grid_id").loc[grid_id]
    return pd.DataFrame(
        [
            {
                "grid_uid": point.grid_uid,
                "grid_id": grid_id,
                "province_code": int(point.province_code),
                "lon": float(point.lon),
                "lat": float(point.lat),
                "technology": technology,
            }
        ]
    )


class VRECapacityFactorFallbackTests(unittest.TestCase):
    def test_missing_wind_primary_uses_same_grid_mixed_wind(self):
        cf = _CoverageOnlyCF(
            {
                "onshore_wind": set(),
                "mixed_wind": {1},
                "pv": {2},
            }
        )
        resolved = _resolve_vre_cf_sites(_points(), _site("onwind"), cf)
        self.assertEqual(resolved.loc[0, "cf_source_technology"], "mixed_wind")
        self.assertEqual(resolved.loc[0, "cf_grid_id"], 1)
        self.assertEqual(resolved.loc[0, "cf_fallback_method"], "same_grid_mixed_wind")

    def test_unresolved_wind_never_falls_back_to_pv(self):
        cf = _CoverageOnlyCF(
            {
                "offshore_wind": set(),
                "mixed_wind": set(),
                "pv": {2},
            }
        )
        with self.assertRaisesRegex(ValueError, "wind-to-PV fallback is forbidden"):
            _resolve_vre_cf_sites(_points(), _site("offwind"), cf)

    def test_pv_uses_nearest_same_province_land_pv_grid(self):
        cf = _CoverageOnlyCF({"pv": {2, 3}, "mixed_wind": set()})
        resolved = _resolve_vre_cf_sites(_points(), _site("dpv", grid_id=3), cf)
        self.assertEqual(resolved.loc[0, "cf_source_technology"], "pv")
        self.assertEqual(resolved.loc[0, "cf_grid_id"], 3)
        self.assertEqual(
            resolved.loc[0, "cf_fallback_method"],
            "same_grid_primary_technology",
        )

        cf_missing_same_grid = _CoverageOnlyCF({"pv": {2}, "mixed_wind": set()})
        resolved = _resolve_vre_cf_sites(
            _points(), _site("dpv", grid_id=3), cf_missing_same_grid
        )
        self.assertEqual(resolved.loc[0, "cf_grid_id"], 2)
        self.assertEqual(
            resolved.loc[0, "cf_fallback_method"],
            "nearest_same_province_land_pv_grid",
        )

    def test_pv_fallback_excludes_water_centroid_candidate(self):
        cf = _CoverageOnlyCF({"pv": {2, 3}, "mixed_wind": set()})
        points = _points()
        site = _site("upv", grid_id=1)
        resolved = _resolve_vre_cf_sites(points, site, cf)
        self.assertEqual(resolved.loc[0, "cf_grid_id"], 2)


if __name__ == "__main__":
    unittest.main()
