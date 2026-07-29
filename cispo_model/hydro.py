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
    reservoir_station_rows: np.ndarray
    reservoir_station_rows_by_province: dict[int, np.ndarray]
    reservoir_local_rows_by_province: dict[int, np.ndarray]
    reservoir_province_positions: np.ndarray
    reservoir_inflow_gwh: np.ndarray
    reservoir_energy_upper_gwh: np.ndarray
    reservoir_local_inflow_m3s: np.ndarray
    reservoir_generation_conversion_gw_per_m3s: np.ndarray
    reservoir_active_storage_m3: np.ndarray
    cascade_station_local_rows: np.ndarray
    cascade_edge_source_local_rows: list[np.ndarray]
    cascade_edge_target_local_rows: list[np.ndarray]
    cascade_edge_target_weights: list[np.ndarray]
    cascade_edge_lag_h: np.ndarray
    cascade_edge_ids: list[str]
    cascade_isolated_node_ids: list[str]


def _split_semicolon_ids(value: object) -> list[str]:
    if pd.isna(value):
        return []
    return [part.strip() for part in str(value).split(";") if part.strip()]


def _cyclic_shift_previous(values: np.ndarray, lag_h: int) -> np.ndarray:
    """Return values[t-lag_h] on the selected cyclic horizon."""
    lag = int(lag_h) % values.shape[0]
    if lag == 0:
        return values.copy()
    return np.concatenate([values[-lag:], values[:-lag]])


def _connected_cascade_node_ids(
    cascade_nodes: pd.DataFrame,
    cascade_edges: pd.DataFrame,
) -> tuple[set[str], list[str]]:
    """Return hydraulically connected nodes and validate skipped singleton nodes.

    A topology node with neither an incoming nor outgoing cascade edge has no
    upstream-release term and, when it represents exactly one reservoir
    station, its cascade balance is algebraically identical to the vectorized
    independent-reservoir balance.  Keep it in the source topology for
    provenance, but do not send it through the per-hour cascade construction.
    Reject a multi-station isolated node so this optimization cannot silently
    aggregate or change a hydraulic relationship in a future data refresh.
    """
    if cascade_edges.empty:
        return set(), []
    connected = set(cascade_edges.source_node_id.astype(str)).union(
        cascade_edges.target_node_id.astype(str)
    )
    isolated: list[str] = []
    for row in cascade_nodes.itertuples(index=False):
        node_id = str(row.node_id)
        if node_id in connected:
            continue
        station_ids = _split_semicolon_ids(row.hydrochn_row_ids)
        if int(row.model_station_count) != 1 or len(station_ids) != 1:
            raise ValueError(
                "An isolated cascade node must represent exactly one station "
                f"before it can use the independent-reservoir balance: {node_id}"
            )
        isolated.append(node_id)
    return connected, sorted(isolated)


def _station_flow_share_by_comid(stations: pd.DataFrame) -> np.ndarray:
    """Allocate one reach-level discharge series across co-mapped stations.

    GRFR provides one natural-discharge series per COMID.  When multiple
    HydroCHN rows map to the same COMID, assigning that full series to every
    row would duplicate the same reach-level water.  Use the station technical
    potential as a static allocation proxy, consistent with the existing
    within-node cascade split.  The allocation is intentionally independent
    of endogenous build decisions so the optimization remains linear.
    """
    required = {"comid", "capacity_potential_gw"}
    missing = sorted(required.difference(stations.columns))
    if missing:
        raise ValueError(
            "Cannot allocate duplicate-COMID discharge without columns: "
            + ", ".join(missing)
        )
    comid = pd.to_numeric(stations.comid, errors="coerce")
    capacity = pd.to_numeric(
        stations.capacity_potential_gw, errors="coerce"
    ).to_numpy(dtype=float)
    if comid.isna().any():
        raise ValueError("Every hydropower station must have a finite COMID")
    if not np.isfinite(capacity).all() or (capacity <= 0.0).any():
        raise ValueError(
            "capacity_potential_gw must be finite and positive for COMID flow allocation"
        )
    capacity_series = pd.Series(capacity, index=stations.index)
    group_total = capacity_series.groupby(comid, sort=False).transform("sum")
    share = (capacity_series / group_total).to_numpy(dtype=float)
    if not np.isfinite(share).all() or (share <= 0.0).any():
        raise ValueError("Invalid duplicate-COMID station flow share")
    group_share = pd.Series(share, index=stations.index).groupby(
        comid, sort=False
    ).sum()
    if not np.allclose(group_share.to_numpy(dtype=float), 1.0, rtol=0.0, atol=1e-12):
        raise ValueError("Station flow shares must sum to one within every COMID")
    return share


class HydroProfileReader:
    def __init__(self, config: ModelConfig, data: ModelData):
        self.config = config
        self.data = data
        allocation_rule = str(
            config.raw["hydro"].get("duplicate_comid_flow_allocation", "")
        )
        if allocation_rule != "static_capacity_potential_share_v1":
            raise ValueError(
                "Unsupported duplicate-COMID hydrology allocation rule: "
                f"{allocation_rule!r}"
            )
        self.station_flow_share = _station_flow_share_by_comid(
            data.hydro_stations
        )
        index = pd.read_csv(DATA_ROOT / "hydro" / "timeseries_index.csv")
        discharge_indexed = str(index.loc[index.dataset.eq("hourly_discharge_2019"), "path"].iloc[0])
        hydro_config = config.raw["hydro"]
        environment_dataset = str(
            hydro_config.get(
                "environmental_flow_dataset",
                "monthly_environmental_flow_2019_p30",
            )
        )
        environment_variable = str(
            hydro_config.get(
                "environmental_flow_variable",
                "monthly_p30_proxy_m3s",
            )
        )
        environment_rows = index.loc[index.dataset.eq(environment_dataset), "path"]
        if environment_rows.empty:
            available = ", ".join(index.dataset.astype(str).tolist())
            raise ValueError(
                f"Hydrology index does not contain {environment_dataset}; "
                f"available datasets: {available}"
            )
        environment_indexed = str(environment_rows.iloc[0])
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
        self.environment_variable = environment_variable
        if self.environment_variable not in self.environment.variables:
            if "monthly_environmental_flow_m3s" in self.environment.variables:
                self.environment_variable = "monthly_environmental_flow_m3s"
            else:
                available = ", ".join(self.environment.variables.keys())
                raise ValueError(
                    f"Environmental-flow variable {environment_variable} is absent; "
                    f"available variables: {available}"
                )
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
                    self.environment.variables[self.environment_variable][
                        month_position[int(month)], position_values[valid]
                    ],
                    dtype=np.float64,
                )
                q_environment[np.ix_(selected_hours, valid)] = values[None, :]
        available = np.maximum(qout - q_environment, 0.0)
        tolerance = float(
            self.config.raw["hydro"]["hydrology_flow_zero_tolerance_m3s"]
        )
        available[available < tolerance] = 0.0
        available *= self.station_flow_share[station_rows][None, :]
        return available

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
        province_values = stations.province_code.to_numpy(dtype=int)
        all_reservoir_rows = np.flatnonzero(reservoir_mask)
        reservoir_row_to_local = {
            int(station_row): local_row
            for local_row, station_row in enumerate(all_reservoir_rows)
        }
        reservoir_rows_by_province: dict[int, np.ndarray] = {}
        reservoir_local_rows_by_province: dict[int, np.ndarray] = {}
        reservoir_province_positions = np.asarray(
            [
                self.province_index[int(province_code)]
                for province_code in province_values[all_reservoir_rows]
            ],
            dtype=np.int64,
        )
        reservoir_q_available = self._available_flow_for_rows(
            block, all_reservoir_rows
        )
        reservoir_q_available_station = reservoir_q_available.T.copy()
        reservoir_local_inflow_m3s = reservoir_q_available_station.copy()
        reservoir_inflow = (
            reservoir_q_available
            * head[all_reservoir_rows][None, :]
            * conversion
        ).T
        reservoir_conversion = head[all_reservoir_rows] * conversion
        reservoir_active_storage_m3 = (
            stations.active_storage_gl.fillna(0.0).to_numpy(dtype=float)[all_reservoir_rows]
            * 1.0e6
        )
        energy_upper_station = (
            stations.active_storage_gl.fillna(0.0).to_numpy(dtype=float)
            * 1.0e6
            * head
            * conversion
            / 3600.0
        )
        cascade_station_local_rows: set[int] = set()
        cascade_edge_source_local_rows: list[np.ndarray] = []
        cascade_edge_target_local_rows: list[np.ndarray] = []
        cascade_edge_target_weights: list[np.ndarray] = []
        cascade_edge_lag_h: list[int] = []
        cascade_edge_ids: list[str] = []
        cascade_edges = getattr(self.data, "hydro_cascade_edges", pd.DataFrame())
        cascade_nodes = getattr(self.data, "hydro_cascade_nodes", pd.DataFrame())
        connected_cascade_node_ids, isolated_cascade_node_ids = (
            _connected_cascade_node_ids(cascade_nodes, cascade_edges)
        )
        if not cascade_edges.empty:
            station_id_to_global = {
                str(hydro_id): int(row)
                for row, hydro_id in enumerate(stations.hydrochn_row_id.astype(str))
            }
            station_id_to_local = {
                str(stations.hydrochn_row_id.iloc[station_row]): reservoir_row_to_local[int(station_row)]
                for station_row in all_reservoir_rows
            }
            node_to_local_rows: dict[str, np.ndarray] = {}
            node_to_weights: dict[str, np.ndarray] = {}
            node_to_natural: dict[str, np.ndarray] = {}
            capacity = stations.capacity_potential_gw.to_numpy(dtype=float)
            for row in cascade_nodes.itertuples(index=False):
                node_id = str(row.node_id)
                if node_id not in connected_cascade_node_ids:
                    continue
                station_ids = _split_semicolon_ids(row.hydrochn_row_ids)
                local_rows = np.asarray(
                    [
                        station_id_to_local[station_id]
                        for station_id in station_ids
                        if station_id in station_id_to_local
                    ],
                    dtype=np.int64,
                )
                if not len(local_rows):
                    continue
                global_rows = np.asarray(
                    [station_id_to_global[station_id] for station_id in station_ids],
                    dtype=np.int64,
                )
                weights = capacity[global_rows]
                if not np.isfinite(weights).all() or weights.sum() <= 0.0:
                    weights = np.ones(len(local_rows), dtype=float)
                weights = weights / weights.sum()
                node_to_local_rows[node_id] = local_rows
                node_to_weights[node_id] = weights.astype(float)
                node_to_natural[node_id] = reservoir_q_available_station[
                    local_rows
                ].sum(axis=0)
                cascade_station_local_rows.update(int(local) for local in local_rows)

            node_local_inflow = {
                node_id: values.copy() for node_id, values in node_to_natural.items()
            }
            for row in cascade_edges.itertuples(index=False):
                source = str(row.source_node_id)
                target = str(row.target_node_id)
                if source not in node_to_natural or target not in node_local_inflow:
                    continue
                lag = int(row.travel_lag_h)
                node_local_inflow[target] -= _cyclic_shift_previous(
                    node_to_natural[source], lag
                )
                cascade_edge_source_local_rows.append(node_to_local_rows[source])
                cascade_edge_target_local_rows.append(node_to_local_rows[target])
                cascade_edge_target_weights.append(node_to_weights[target])
                cascade_edge_lag_h.append(lag)
                cascade_edge_ids.append(str(row.edge_id))

            for node_id, local_rows in node_to_local_rows.items():
                local = np.maximum(node_local_inflow[node_id], 0.0)
                weights = node_to_weights[node_id]
                for row_position, local_row in enumerate(local_rows):
                    reservoir_local_inflow_m3s[local_row] = local * weights[row_position]
            reservoir_inflow = reservoir_local_inflow_m3s * reservoir_conversion[:, None]
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

            selected_reservoir = np.flatnonzero(
                (province_values == province_code) & reservoir_mask
            )
            reservoir_rows_by_province[p] = selected_reservoir
            reservoir_local_rows_by_province[p] = np.asarray(
                [reservoir_row_to_local[int(row)] for row in selected_reservoir],
                dtype=np.int64,
            )
        cascade_station_local_rows_array = np.asarray(
            sorted(cascade_station_local_rows), dtype=np.int64
        )
        return HydroLinearBlock(
            ror_station_rows=ror_rows,
            ror_capacity_factor=ror_cf,
            reservoir_station_rows=all_reservoir_rows,
            reservoir_station_rows_by_province=reservoir_rows_by_province,
            reservoir_local_rows_by_province=reservoir_local_rows_by_province,
            reservoir_province_positions=reservoir_province_positions,
            reservoir_inflow_gwh=reservoir_inflow,
            reservoir_energy_upper_gwh=energy_upper_station[all_reservoir_rows],
            reservoir_local_inflow_m3s=reservoir_local_inflow_m3s,
            reservoir_generation_conversion_gw_per_m3s=reservoir_conversion,
            reservoir_active_storage_m3=reservoir_active_storage_m3,
            cascade_station_local_rows=cascade_station_local_rows_array,
            cascade_edge_source_local_rows=cascade_edge_source_local_rows,
            cascade_edge_target_local_rows=cascade_edge_target_local_rows,
            cascade_edge_target_weights=cascade_edge_target_weights,
            cascade_edge_lag_h=np.asarray(cascade_edge_lag_h, dtype=np.int64),
            cascade_edge_ids=cascade_edge_ids,
            cascade_isolated_node_ids=isolated_cascade_node_ids,
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
