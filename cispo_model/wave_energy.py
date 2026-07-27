"""Grid-resolved wave-energy capacity and hourly availability.

Wave remains isolated from ``VRE_TECHS`` so its existing-marine-grid data
contract stays distinct from wind/PV, but it is enabled in the Base model.
Wave capacity is continuous and grid resolved; hourly dispatch is aggregated
only after applying every site's own capacity-factor series.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .config import ModelConfig


SCENARIO_CODE = {
    "conservative": 0,
    "medium": 1,
    "aggressive": 2,
}


@dataclass
class WaveEnergyData:
    sites: pd.DataFrame
    cf: "WaveCapacityFactorStore"


class WaveCapacityFactorStore:
    """Chunked reader for the scenario x time x grid wave NetCDF contract."""

    def __init__(
        self,
        path: Path,
        *,
        profile_year: int,
        scenario: str,
        expected_hours: int,
        weather_year: int = 2023,
    ):
        try:
            import xarray as xr
        except ImportError as exc:  # pragma: no cover - environment diagnostic
            raise RuntimeError(
                "xarray and netCDF4 are required when wave energy is enabled; "
                "install requirements-data.txt"
            ) from exc
        if not path.is_file():
            raise FileNotFoundError(
                f"Wave capacity-factor file is missing: {path}. "
                "Set CISPO_WAVE_ROOT to the directory containing wave_grid.nc."
            )
        self.path = path
        self.dataset = xr.open_dataset(path, decode_times=True)
        required = {
            "capacity_factor",
            "grid_id",
            "scenario_year",
            "scenario_code",
            "time",
        }
        missing = sorted(required.difference(self.dataset.variables))
        if missing:
            raise ValueError(f"Wave NetCDF is missing variables: {', '.join(missing)}")
        if tuple(self.dataset["capacity_factor"].dims) != (
            "scenario",
            "time",
            "grid",
        ):
            raise ValueError(
                "Wave capacity_factor dimensions must be "
                "('scenario', 'time', 'grid')"
            )
        if int(self.dataset.sizes["time"]) != expected_hours:
            raise ValueError(
                f"Wave NetCDF hours={self.dataset.sizes['time']}; "
                f"expected {expected_hours}"
            )
        time = pd.DatetimeIndex(self.dataset["time"].values)
        expected_time = pd.date_range(
            f"{int(weather_year)}-01-01 00:00:00",
            periods=int(expected_hours),
            freq="h",
        )
        if not time.equals(expected_time):
            raise ValueError(
                "Wave time coordinate must be a gap-free naive hourly sequence "
                f"for weather year {weather_year}"
            )
        scenario_key = str(scenario).lower()
        if scenario_key not in SCENARIO_CODE:
            raise ValueError(
                "Wave scenario must be conservative, medium, or aggressive"
            )
        years = np.asarray(self.dataset["scenario_year"].values, dtype=int)
        codes = np.asarray(self.dataset["scenario_code"].values, dtype=int)
        matches = np.flatnonzero(
            (years == int(profile_year)) & (codes == SCENARIO_CODE[scenario_key])
        )
        if len(matches) != 1:
            raise ValueError(
                "Wave NetCDF must contain exactly one scenario for "
                f"year={profile_year}, scenario={scenario_key}; found {len(matches)}"
            )
        self.scenario_position = int(matches[0])
        grid_ids = np.asarray(self.dataset["grid_id"].values, dtype=np.int64)
        if len(np.unique(grid_ids)) != len(grid_ids):
            raise ValueError("Wave NetCDF grid_id values must be unique")
        self.positions = {
            int(grid_id): position for position, grid_id in enumerate(grid_ids)
        }

    def read(
        self,
        grid_ids: Iterable[int],
        hour_start: int,
        hour_stop: int,
    ) -> np.ndarray:
        positions = np.asarray(
            [self.positions[int(grid_id)] for grid_id in grid_ids],
            dtype=np.int64,
        )
        block = np.asarray(
            self.dataset["capacity_factor"].isel(
                scenario=self.scenario_position,
                time=slice(int(hour_start), int(hour_stop)),
                grid=positions,
            ).values,
            dtype=np.float64,
        )
        expected_shape = (int(hour_stop) - int(hour_start), len(positions))
        if block.shape != expected_shape:
            raise ValueError(
                f"Wave CF block shape={block.shape}; expected {expected_shape}"
            )
        if not np.isfinite(block).all():
            raise ValueError("Wave CF block contains non-finite values")
        if (block < -1e-7).any() or (block > 1.0 + 1e-7).any():
            raise ValueError("Wave CF block contains values outside [0, 1]")
        return np.clip(block, 0.0, 1.0)

    def close(self) -> None:
        """Release the NetCDF file handle, primarily for tests and short tools."""
        self.dataset.close()


def load_wave_energy_data(config: ModelConfig) -> WaveEnergyData | None:
    """Load the optional model-ready wave sites and external hourly NetCDF."""
    if not bool(config.raw["features"].get("wave_energy", False)):
        return None
    settings = config.raw["wave_energy"]
    sites_path = Path(settings["sites_file"])
    if not sites_path.is_absolute():
        from .data import DATA_ROOT

        sites_path = DATA_ROOT / sites_path
    if not sites_path.is_file():
        raise FileNotFoundError(
            f"Model-ready wave site table is missing: {sites_path}. "
            "Run scripts/build_wave_energy_inputs.py first."
        )
    sites = pd.read_csv(sites_path)
    required_columns = {
        "grid_uid",
        "grid_id",
        "wave_source_grid_id",
        "lon",
        "lat",
        "is_land",
        "province_code",
        "load_center_id",
        "substation_id",
        "capacity_upper_gw_raw",
        "distance_to_shore_km",
        "water_depth_m",
        "wave_nc_imputed",
    }
    missing = sorted(required_columns.difference(sites.columns))
    if missing:
        raise ValueError(
            f"Wave site table is missing columns: {', '.join(missing)}"
        )
    if sites.grid_uid.duplicated().any() or sites.grid_id.duplicated().any():
        raise ValueError("Wave site table must be unique by grid_uid and grid_id")
    if sites.wave_source_grid_id.duplicated().any():
        raise ValueError("Wave site table must be unique by wave_source_grid_id")
    if not sites.is_land.eq(0).all():
        raise ValueError("Wave expansion may only use existing marine grid rows")
    numeric_columns = [
        "lon",
        "lat",
        "province_code",
        "capacity_upper_gw_raw",
        "distance_to_shore_km",
        "water_depth_m",
    ]
    if not np.isfinite(sites[numeric_columns].to_numpy(dtype=float)).all():
        raise ValueError("Wave site table contains non-finite numeric values")
    if (sites.capacity_upper_gw_raw < 0.0).any():
        raise ValueError("Wave capacity potential cannot be negative")

    potential_fraction = float(settings["potential_fraction"])
    sites = sites.copy()
    sites["capacity_upper_gw"] = (
        sites.capacity_upper_gw_raw.to_numpy(dtype=float) * potential_fraction
    )
    maximum_distance = settings.get("maximum_distance_to_shore_km")
    if maximum_distance is not None:
        sites.loc[
            sites.distance_to_shore_km.gt(float(maximum_distance)),
            "capacity_upper_gw",
        ] = 0.0
    maximum_depth = settings.get("maximum_water_depth_m")
    if maximum_depth is not None:
        sites.loc[
            sites.water_depth_m.gt(float(maximum_depth)),
            "capacity_upper_gw",
        ] = 0.0
    if bool(settings.get("exclude_imputed_cf", False)):
        sites.loc[sites.wave_nc_imputed.astype(bool), "capacity_upper_gw"] = 0.0
    sites = sites.loc[sites.capacity_upper_gw.gt(1e-10)].reset_index(drop=True)
    if sites.empty:
        raise ValueError("Wave-energy screening leaves no active capacity sites")

    profile_year = int(
        settings["profile_year_by_planning_year"][str(config.planning_year)]
    )
    scenario = str(
        settings["scenario_by_planning_year"][str(config.planning_year)]
    )
    wave_root = os.environ.get("CISPO_WAVE_ROOT")
    if not wave_root:
        raise RuntimeError(
            "CISPO_WAVE_ROOT must point to the raw wave-energy directory "
            "when features.wave_energy=true"
        )
    cf_path = Path(wave_root) / str(settings["cf_filename"])
    store = WaveCapacityFactorStore(
        cf_path,
        profile_year=profile_year,
        scenario=scenario,
        expected_hours=config.hours,
        weather_year=config.weather_year,
    )
    missing_grid_ids = set(
        sites.wave_source_grid_id.astype(int)
    ).difference(store.positions)
    if missing_grid_ids:
        raise ValueError(
            "Wave site table contains grid IDs absent from the NetCDF: "
            f"{sorted(missing_grid_ids)[:10]}"
        )
    return WaveEnergyData(sites=sites, cf=store)


def wave_cost_parameters(config: ModelConfig, sites: pd.DataFrame) -> tuple[np.ndarray, float, float]:
    """Return site CAPEX in CNY/kW, FOM fraction, and lifetime for the year."""
    settings = config.raw["wave_energy"]
    cost_year = int(
        settings["cost_year_by_planning_year"][str(config.planning_year)]
    )
    key = str(cost_year)
    base = float(settings["capex_eur_per_kw_by_year"][key])
    depth_adder = float(settings["depth_adder_eur_per_kw_m_by_year"][key])
    distance_adder = float(
        settings["distance_adder_eur_per_kw_km_by_year"][key]
    )
    capex_eur = (
        base
        + depth_adder * sites.water_depth_m.to_numpy(dtype=float)
        + distance_adder * sites.distance_to_shore_km.to_numpy(dtype=float)
    )
    capex_cny = capex_eur * float(settings["eur_to_cny"])
    fixed_om_fraction = float(settings["fixed_om_fraction_by_year"][key])
    lifetime_years = float(settings["lifetime_years_by_year"][key])
    return capex_cny, fixed_om_fraction, lifetime_years


def reconstruct_wave_availability(
    config: ModelConfig,
    wave: WaveEnergyData,
    capacity_gw: np.ndarray,
    province_codes: Iterable[int],
    hours: int,
) -> np.ndarray:
    """Reconstruct province-hour wave availability for exports and hard QC."""
    province_codes = [int(code) for code in province_codes]
    province_index = {code: i for i, code in enumerate(province_codes)}
    available = np.zeros((len(province_codes), int(hours)), dtype=np.float64)
    chunk = int(config.raw["construction"]["build_hour_chunk_size"])
    for province_code, group in wave.sites.groupby("province_code", sort=False):
        p = province_index[int(province_code)]
        positions = group.index.to_numpy(dtype=int)
        grid_ids = group.wave_source_grid_id.to_numpy(dtype=np.int64)
        for start in range(0, int(hours), chunk):
            stop = min(start + chunk, int(hours))
            coefficients = wave.cf.read(grid_ids, start, stop)
            available[p, start:stop] = coefficients @ capacity_gw[positions]
    return available
