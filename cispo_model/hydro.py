"""Chunked 2019 hydrology proxy mapped to 2030 chronological blocks."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from pathlib import PureWindowsPath

import numpy as np
import pandas as pd
from netCDF4 import Dataset

from .config import ModelConfig
from .data import DATA_ROOT, ModelData
from .timeblocks import TimeBlock


@dataclass
class HydroBlock:
    ror_available_gw: np.ndarray
    reservoir_inflow_gwh: np.ndarray
    reservoir_energy_upper_gwh: np.ndarray
    reservoir_capacity_gw: np.ndarray


@dataclass
class HydroLinearBlock:
    """Hydrology coefficients that remain linear in station capacity."""

    ror_station_rows: dict[int, np.ndarray]
    ror_capacity_factor: dict[int, np.ndarray]
    reservoir_station_rows: dict[int, np.ndarray]
    reservoir_inflow_gwh: np.ndarray
    reservoir_energy_upper_gwh: np.ndarray


class HydroProfileReader:
    def __init__(self, config: ModelConfig, data: ModelData):
        self.config = config
        self.data = data
        index = pd.read_csv(DATA_ROOT / "hydro" / "timeseries_index.csv")
        discharge_indexed = str(index.loc[index.dataset.eq("hourly_discharge_2019"), "path"].iloc[0])
        environment_indexed = str(index.loc[index.dataset.eq("monthly_environmental_flow_2019_p10"), "path"].iloc[0])
        server_root = os.environ.get("CISPO_HYDRO_ROOT")
        if server_root:
            discharge_path = Path(server_root) / PureWindowsPath(discharge_indexed).name
            environment_path = Path(server_root) / PureWindowsPath(environment_indexed).name
        else:
            discharge_path = Path(discharge_indexed)
            environment_path = Path(environment_indexed)
        if not discharge_path.exists() or not environment_path.exists():
            raise FileNotFoundError(
                "Hydrology inputs are missing. Set CISPO_HYDRO_ROOT on Linux servers: "
                f"{discharge_path}; {environment_path}"
            )
        self.discharge = Dataset(discharge_path)
        self.environment = Dataset(environment_path)
        discharge_comids = np.asarray(self.discharge.variables["comid"][:], dtype=np.int64)
        environment_comids = np.asarray(self.environment.variables["comid"][:], dtype=np.int64)
        if not np.array_equal(discharge_comids, environment_comids):
            raise ValueError("Discharge and environmental-flow COMID axes differ")
        self.comid_position = {int(comid): i for i, comid in enumerate(discharge_comids)}
        self.month_values = np.asarray(self.environment.variables["month"][:], dtype=int)
        self.provinces = data.province_codes.tolist()
        self.province_index = {code: i for i, code in enumerate(self.provinces)}
        self.datetime = (
            data.load[["hour_index", "datetime_bj"]]
            .drop_duplicates("hour_index")
            .sort_values("hour_index")
        )
        self.datetime["month"] = pd.to_datetime(self.datetime.datetime_bj).dt.month
        if len(self.datetime) != config.hours:
            raise ValueError("Cannot map hydrology months to every planning hour")

    def close(self) -> None:
        self.discharge.close()
        self.environment.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()

    def _available_flow_for_rows(self, block: TimeBlock, station_rows: np.ndarray) -> np.ndarray:
        """Return environmental-flow-adjusted discharge for selected station rows."""
        stations = self.data.hydro_stations
        if len(station_rows) == 0:
            return np.zeros((block.hours, 0), dtype=np.float64)
        positions = stations.iloc[station_rows].comid.map(self.comid_position)
        valid = positions.notna().to_numpy()
        position_values = positions.fillna(-1).astype(int).to_numpy()
        qout = np.zeros((block.hours, len(station_rows)), dtype=np.float64)
        if valid.any():
            qout[:, valid] = np.asarray(
                self.discharge.variables["qout_model_m3s"][
                    block.hour_start:block.hour_stop,
                    position_values[valid],
                ],
                dtype=np.float64,
            )
        months = self.datetime.month.to_numpy(dtype=int)[block.hour_start:block.hour_stop]
        month_position = {int(month): i for i, month in enumerate(self.month_values)}
        q_environment = np.zeros_like(qout)
        for month in np.unique(months):
            if int(month) not in month_position:
                raise ValueError(f"Environmental-flow month {month} is absent")
            selected_hours = np.flatnonzero(months == month)
            if valid.any():
                values = np.asarray(
                    self.environment.variables["monthly_p10_proxy_m3s"][
                        month_position[int(month)], position_values[valid]
                    ],
                    dtype=np.float64,
                )
                q_environment[np.ix_(selected_hours, valid)] = values[None, :]
        return np.maximum(qout - q_environment, 0.0)

    def read_linear_block(self, block: TimeBlock) -> HydroLinearBlock:
        """Read one chronological block without fixing hydro capacity decisions."""
        stations = self.data.hydro_stations
        ror_mask = stations.operation_type_model.eq("run_of_river").to_numpy()
        reservoir_mask = stations.operation_type_model.eq("reservoir_storage").to_numpy()
        q_rated = stations.q_rated_m3s.to_numpy(dtype=float)
        head = stations.head_m.fillna(0.0).to_numpy(dtype=float)
        constants = self.config.raw["hydro"]
        conversion = (
            float(constants["reservoir_efficiency"])
            * float(constants["gravity_m_per_s2"])
            * float(constants["water_density_kg_per_m3"])
            / 1.0e9
        )
        ror_rows: dict[int, np.ndarray] = {}
        ror_cf: dict[int, np.ndarray] = {}
        reservoir_rows: dict[int, np.ndarray] = {}
        reservoir_inflow = np.zeros((len(self.provinces), block.hours), dtype=np.float64)
        reservoir_energy_upper = np.zeros(len(self.provinces), dtype=np.float64)
        energy_upper_station = (
            stations.active_storage_gl.fillna(0.0).to_numpy(dtype=float)
            * 1.0e6
            * head
            * conversion
            / 3600.0
        )
        province_values = stations.province_code.to_numpy(dtype=int)
        for province_code, p in self.province_index.items():
            selected_ror = np.flatnonzero((province_values == province_code) & ror_mask)
            ror_rows[p] = selected_ror
            q_available = self._available_flow_for_rows(block, selected_ror)
            if len(selected_ror):
                factors = np.divide(
                    q_available,
                    q_rated[selected_ror][None, :],
                    out=np.zeros_like(q_available),
                    where=q_rated[selected_ror][None, :] > 0,
                )
                ror_cf[p] = np.clip(factors, 0.0, 1.0).astype(np.float32)
            else:
                ror_cf[p] = np.zeros((block.hours, 0), dtype=np.float32)

            selected_reservoir = np.flatnonzero((province_values == province_code) & reservoir_mask)
            reservoir_rows[p] = selected_reservoir
            if len(selected_reservoir):
                q_available = self._available_flow_for_rows(block, selected_reservoir)
                reservoir_inflow[p] = (
                    q_available * head[selected_reservoir][None, :] * conversion
                ).sum(axis=1)
                reservoir_energy_upper[p] = energy_upper_station[selected_reservoir].sum()
        return HydroLinearBlock(
            ror_station_rows=ror_rows,
            ror_capacity_factor=ror_cf,
            reservoir_station_rows=reservoir_rows,
            reservoir_inflow_gwh=reservoir_inflow,
            reservoir_energy_upper_gwh=reservoir_energy_upper,
        )

    def read_block(self, block: TimeBlock, hydro_capacity_gw: np.ndarray) -> HydroBlock:
        stations = self.data.hydro_stations.copy()
        q_available = self._available_flow_for_rows(block, np.arange(len(stations)))
        q_rated = stations.q_rated_m3s.to_numpy(dtype=float)
        ror_mask = stations.operation_type_model.eq("run_of_river").to_numpy()
        reservoir_mask = stations.operation_type_model.eq("reservoir_storage").to_numpy()

        ror_available = np.zeros((len(self.provinces), block.hours), dtype=np.float64)
        for province_code, p in self.province_index.items():
            rows = np.flatnonzero(
                stations.province_code.eq(province_code).to_numpy() & ror_mask
            )
            if len(rows):
                cf = np.divide(
                    q_available[:, rows],
                    q_rated[rows][None, :],
                    out=np.zeros((block.hours, len(rows)), dtype=np.float64),
                    where=q_rated[rows][None, :] > 0,
                )
                ror_available[p] = (
                    np.clip(cf, 0.0, 1.0) * hydro_capacity_gw[rows][None, :]
                ).sum(axis=1)

        constants = self.config.raw["hydro"]
        conversion = (
            float(constants["reservoir_efficiency"])
            * float(constants["gravity_m_per_s2"])
            * float(constants["water_density_kg_per_m3"])
            / 1.0e9
        )
        head = stations.head_m.fillna(0.0).to_numpy(dtype=float)
        inflow_power_gw = q_available * head[None, :] * conversion
        reservoir_inflow = np.zeros((len(self.provinces), block.hours), dtype=np.float64)
        reservoir_capacity = np.zeros(len(self.provinces), dtype=np.float64)
        reservoir_energy_upper = np.zeros(len(self.provinces), dtype=np.float64)
        energy_upper_station = (
            stations.active_storage_gl.fillna(0.0).to_numpy(dtype=float)
            * 1.0e6
            * head
            * conversion
            / 3600.0
        )
        for province_code, p in self.province_index.items():
            rows = np.flatnonzero(
                stations.province_code.eq(province_code).to_numpy() & reservoir_mask
            )
            if len(rows):
                reservoir_inflow[p] = inflow_power_gw[:, rows].sum(axis=1)
                reservoir_capacity[p] = hydro_capacity_gw[rows].sum()
                reservoir_energy_upper[p] = energy_upper_station[rows].sum()
        return HydroBlock(
            ror_available_gw=ror_available,
            reservoir_inflow_gwh=reservoir_inflow,
            reservoir_energy_upper_gwh=reservoir_energy_upper,
            reservoir_capacity_gw=reservoir_capacity,
        )
