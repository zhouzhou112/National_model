"""Strict data contract and chunked time-series access for the CISPO model."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from pathlib import PureWindowsPath
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from .config import ModelConfig, ROOT


DATA_ROOT = Path(os.environ.get("CISPO_DATA_ROOT", str(ROOT / "data")))
VRE_TECHS = ("onwind", "offwind", "upv", "dpv")
THERMAL_TECHS = (
    "coal", "coalccs", "cchp", "cchpccs",
    "gas", "gasccs", "gchp", "gchpccs",
    "bio", "bioccs", "nuclear",
)
STORAGE_TECHS = ("battery", "phs")
DAC_TECHS = ("koh_b", "koh_cl", "mgo_am", "ssor")


def _read(relative_path: str, **kwargs) -> pd.DataFrame:
    path = DATA_ROOT / relative_path
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path, **kwargs)


def require_columns(frame: pd.DataFrame, columns: Iterable[str], label: str) -> None:
    missing = sorted(set(columns).difference(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing required columns: {', '.join(missing)}")


class CapacityFactorStore:
    """Read selected site/hour blocks without materializing full Zarr stores."""

    STORE_FOR_TECH = {
        "onwind": "onshore_wind",
        "offwind": "offshore_wind",
        "upv": "pv",
        "dpv": "pv",
    }

    def __init__(self, index: pd.DataFrame, weather_year: int):
        try:
            import zarr
        except ImportError as exc:  # pragma: no cover - environment diagnostic
            raise RuntimeError(
                "zarr is required in the Gurobi environment; install requirements-data.txt"
            ) from exc
        self._zarr = zarr
        current = index.loc[index.year.eq(weather_year)].copy()
        if current.technology.duplicated().any():
            raise ValueError(f"Duplicate capacity-factor stores for weather year {weather_year}")
        self.index = current.set_index("technology")
        self.groups: dict[str, object] = {}
        self.positions: dict[str, dict[int, int]] = {}
        self.dimensions: dict[str, tuple[str, ...]] = {}

    def _open(self, source_technology: str):
        if source_technology not in self.groups:
            if source_technology not in self.index.index:
                raise KeyError(f"No CF store indexed for {source_technology}")
            indexed_path = str(self.index.loc[source_technology, "zarr_path"])
            server_root = os.environ.get("CISPO_CF_ROOT")
            if server_root:
                path = Path(server_root) / source_technology / PureWindowsPath(indexed_path).name
            else:
                path = Path(indexed_path)
            if not path.exists():
                raise FileNotFoundError(
                    f"Capacity-factor store is missing: {path}. "
                    "Set CISPO_CF_ROOT on Linux servers."
                )
            group = self._zarr.open_group(str(path), mode="r")
            grid_ids = np.asarray(group["grid_id"][:], dtype=np.int64)
            if len(np.unique(grid_ids)) != len(grid_ids):
                raise ValueError(f"Duplicate grid_id values in {path}")
            dimensions = tuple(group["cf"].attrs["_ARRAY_DIMENSIONS"])
            if set(dimensions) != {"time", "grid_id"}:
                raise ValueError(f"Unexpected dimensions in {path}: {dimensions}")
            self.groups[source_technology] = group
            self.positions[source_technology] = {
                int(grid_id): position for position, grid_id in enumerate(grid_ids)
            }
            self.dimensions[source_technology] = dimensions
        return self.groups[source_technology]

    def available_grid_ids(self, source_technology: str) -> set[int]:
        self._open(source_technology)
        return set(self.positions[source_technology])

    def read(
        self,
        source_technology: str,
        grid_ids: Iterable[int],
        hour_start: int,
        hour_stop: int,
    ) -> np.ndarray:
        group = self._open(source_technology)
        positions = np.asarray(
            [self.positions[source_technology][int(grid_id)] for grid_id in grid_ids],
            dtype=np.int64,
        )
        array = group["cf"]
        dimensions = self.dimensions[source_technology]
        if dimensions == ("time", "grid_id"):
            block = np.asarray(array[hour_start:hour_stop, positions], dtype=np.float64)
        else:
            block = np.asarray(array[positions, hour_start:hour_stop], dtype=np.float64).T
        if block.shape != (hour_stop - hour_start, len(positions)):
            raise ValueError(
                f"CF block shape mismatch for {source_technology}: {block.shape}"
            )
        if not np.isfinite(block).all():
            raise ValueError(f"Non-finite CF values in {source_technology}")
        return np.clip(block, 0.0, 1.0)

    def read_hours(
        self,
        source_technology: str,
        grid_ids: Iterable[int],
        hour_indices: Iterable[int],
    ) -> np.ndarray:
        """Read an arbitrary hour/site orthogonal selection as hours x sites."""
        group = self._open(source_technology)
        positions = np.asarray(
            [self.positions[source_technology][int(grid_id)] for grid_id in grid_ids],
            dtype=np.int64,
        )
        hours = np.asarray(list(hour_indices), dtype=np.int64)
        array = group["cf"]
        dimensions = self.dimensions[source_technology]
        if dimensions == ("time", "grid_id"):
            block = np.asarray(array.oindex[hours, positions], dtype=np.float64)
        else:
            block = np.asarray(array.oindex[positions, hours], dtype=np.float64).T
        if block.shape != (len(hours), len(positions)):
            raise ValueError(
                f"CF arbitrary-hour block shape mismatch for {source_technology}: {block.shape}"
            )
        if not np.isfinite(block).all():
            raise ValueError(f"Non-finite CF values in {source_technology}")
        return np.clip(block, 0.0, 1.0)


@dataclass
class ModelData:
    provinces: pd.DataFrame
    load: pd.DataFrame
    load_gw: np.ndarray
    vre_points: pd.DataFrame
    vre_sites: pd.DataFrame
    thermal_floor: pd.DataFrame
    nuclear_floor: pd.DataFrame
    hydro_stations: pd.DataFrame
    hydro_cascade_nodes: pd.DataFrame
    hydro_cascade_edges: pd.DataFrame
    biomass: pd.DataFrame
    lines: pd.DataFrame
    carbon: pd.Series
    capex: pd.DataFrame
    ruc: pd.DataFrame
    thermal_om: pd.DataFrame
    storage: pd.DataFrame
    fuel: pd.DataFrame
    emissions: pd.DataFrame
    dac: pd.DataFrame
    ccs_cost: pd.Series
    grid_connections: pd.DataFrame
    initial_spur: pd.DataFrame
    substations: pd.DataFrame
    load_centers: pd.DataFrame
    vre_load_center_routes: pd.DataFrame
    hydro_load_center_routes: pd.DataFrame
    intra_load_center_edges: pd.DataFrame
    cf: CapacityFactorStore

    @property
    def province_codes(self) -> np.ndarray:
        return self.provinces.province_code.to_numpy(dtype=np.int64)


def compute_vre_max_cf(config: ModelConfig, data: ModelData) -> np.ndarray:
    """Return max-hour CF for every row of ``data.vre_sites`` using bounded memory."""
    maxima = np.zeros(len(data.vre_sites), dtype=np.float64)
    chunk = int(config.raw["construction"]["hour_chunk_size"])
    for source_technology, group in data.vre_sites.groupby("cf_source_technology", sort=False):
        row_positions = group.index.to_numpy(dtype=np.int64)
        grid_ids = group.cf_grid_id.to_numpy(dtype=np.int64)
        local_max = np.zeros(len(group), dtype=np.float64)
        for start in range(0, config.hours, chunk):
            stop = min(start + chunk, config.hours)
            block = data.cf.read(source_technology, grid_ids, start, stop)
            local_max = np.maximum(local_max, block.max(axis=0))
        maxima[row_positions] = local_max
    if not np.isfinite(maxima).all() or (maxima < 0).any() or (maxima > 1 + 1e-9).any():
        raise ValueError("Invalid VRE max-CF vector")
    return maxima


def _resolve_vre_cf_sites(
    points: pd.DataFrame,
    sites: pd.DataFrame,
    cf: CapacityFactorStore,
) -> pd.DataFrame:
    sites = sites.copy()
    sites["cf_source_technology"] = sites.technology.map(CapacityFactorStore.STORE_FOR_TECH)
    sites["cf_grid_id"] = sites.grid_id.astype(np.int64)
    sites["cf_fallback_method"] = "same_grid_primary_technology"
    source_available = {
        source: cf.available_grid_ids(source)
        for source in sorted(sites.cf_source_technology.unique())
    }
    mixed_available = cf.available_grid_ids("mixed_wind")

    for row_index, row in sites.iterrows():
        source = row.cf_source_technology
        grid_id = int(row.grid_id)
        if grid_id in source_available[source]:
            continue
        if row.technology in {"onwind", "offwind"} and grid_id in mixed_available:
            sites.at[row_index, "cf_source_technology"] = "mixed_wind"
            sites.at[row_index, "cf_fallback_method"] = "same_grid_mixed_wind"
            continue
        sites.at[row_index, "cf_grid_id"] = -1

    unresolved = sites.cf_grid_id.eq(-1)
    if unresolved.any():
        point_by_grid = points.set_index("grid_id")
        pv_grid_ids = sorted(source_available["pv"].intersection(point_by_grid.index))
        pv_points = point_by_grid.loc[pv_grid_ids, ["province_code", "lon", "lat"]].copy()
        for province_code, group in sites.loc[unresolved].groupby("province_code"):
            candidates = pv_points.loc[pv_points.province_code.eq(province_code)]
            if candidates.empty:
                raise ValueError(f"No PV CF fallback candidates in province {province_code}")
            tree = cKDTree(candidates[["lon", "lat"]].to_numpy(dtype=float))
            query = group[["lon", "lat"]].to_numpy(dtype=float)
            _, positions = tree.query(query, k=1)
            replacement = candidates.index.to_numpy(dtype=np.int64)[positions]
            sites.loc[group.index, "cf_source_technology"] = "pv"
            sites.loc[group.index, "cf_grid_id"] = replacement.astype(np.int64)
            sites.loc[group.index, "cf_fallback_method"] = "nearest_same_province_land_pv_grid"

    if sites.cf_grid_id.eq(-1).any():
        raise ValueError("Unresolved VRE capacity-factor sites remain")
    return sites


def load_model_data(config: ModelConfig) -> ModelData:
    provinces = _read("sets/provinces.csv").sort_values("province_code").reset_index(drop=True)
    if len(provinces) != 31 or not provinces.province_code.is_unique:
        raise ValueError("The model requires 31 unique province rows")

    load = _read(
        "load/hourly_load_2025_2060.csv.gz",
        usecols=["province_code", "year", "hour_index", "datetime_bj", "demand_gw"],
    )
    load = load.loc[load.year.eq(config.planning_year)].copy()
    expected_load_rows = len(provinces) * config.hours
    if len(load) != expected_load_rows:
        raise ValueError(f"2030 load rows={len(load)}; expected {expected_load_rows}")
    if load.duplicated(["province_code", "hour_index"]).any():
        raise ValueError("Duplicate province-hour load rows")
    province_order = provinces.province_code.tolist()
    load_pivot = load.pivot(index="province_code", columns="hour_index", values="demand_gw")
    load_pivot = load_pivot.reindex(index=province_order, columns=range(config.hours))
    if load_pivot.isna().any().any() or (load_pivot < 0).any().any():
        raise ValueError("Load matrix contains missing or negative values")

    points = _read("vre/optimization_points.csv")
    require_columns(points, ["grid_uid", "grid_id", "province_code", "lon", "lat"], "VRE points")
    if points.grid_uid.duplicated().any():
        raise ValueError("VRE grid_uid must be unique")
    site_rows = []
    for technology in VRE_TECHS:
        existing_col = f"existing_{technology}_gw"
        upper_col = f"pmax_{technology}_{config.vre_scenario}_gw"
        selected = points.loc[
            points[upper_col].gt(1e-10),
            ["grid_uid", "grid_id", "province_code", "lon", "lat", "is_land", existing_col, upper_col],
        ].copy()
        selected = selected.rename(columns={existing_col: "capacity_floor_gw", upper_col: "capacity_upper_gw"})
        selected["technology"] = technology
        site_rows.append(selected)
    vre_sites = pd.concat(site_rows, ignore_index=True)
    if (vre_sites.capacity_floor_gw > vre_sites.capacity_upper_gw + 1e-9).any():
        raise ValueError("VRE floor exceeds scenario upper bound")

    cf_index = _read("vre/hourly_cf_index.csv")
    cf = CapacityFactorStore(cf_index, config.weather_year)
    vre_sites = _resolve_vre_cf_sites(points, vre_sites, cf)

    thermal_floor = _read("thermal/capacity_floor_by_year.csv")
    thermal_floor = thermal_floor.loc[thermal_floor.year.eq(config.planning_year)].copy()
    nuclear_floor = _read("thermal/nuclear_capacity_floor_by_year.csv")
    nuclear_floor = nuclear_floor.loc[nuclear_floor.year.eq(config.planning_year)].copy()
    hydro = _read("hydro/hydro_stations.csv")
    try:
        hydro_cascade_nodes = _read("hydro/cascade_topology_nodes.csv")
        hydro_cascade_edges = _read("hydro/cascade_topology_edges.csv")
    except FileNotFoundError:
        hydro_cascade_nodes = pd.DataFrame(
            columns=[
                "node_id", "river_group_stage2", "comid", "hydrochn_row_ids",
                "model_station_count", "model_capacity_gw", "existing_capacity_gw",
                "stage2_capacity_gw", "plant_count_at_comid", "topology_in_degree",
                "topology_out_degree", "topology_role", "label_name",
            ]
        )
        hydro_cascade_edges = pd.DataFrame(
            columns=[
                "edge_id", "river_group_stage2", "source_node_id", "target_node_id",
                "source_comid", "target_comid", "source_hydrochn_row_ids",
                "target_hydrochn_row_ids", "source_model_station_count",
                "target_model_station_count", "steps_to_next_candidate",
                "traced_length_km", "travel_lag_h", "lag_correlation",
                "lag_method", "lag_quality_flag", "source_capacity_mw",
                "target_capacity_mw",
            ]
        )
    biomass = _read("biomass/fuel_potential_by_province_year.csv")
    biomass = biomass.loc[biomass.year.eq(config.planning_year)].copy()
    lines = _read("transmission/candidate_corridors.csv")
    lines = lines.loc[lines.allowed_by_model.astype(bool)].copy().reset_index(drop=True)
    lines["line_id"] = [f"CORRIDOR_{i:04d}" for i in range(len(lines))]

    carbon_table = _read("carbon/emissions_limits_by_scenario.csv")
    carbon_rows = carbon_table.loc[
        carbon_table.scenario.eq(config.raw["carbon_scenario"])
        & carbon_table.year.eq(config.planning_year)
    ]
    if len(carbon_rows) != 1:
        raise ValueError("Exactly one active carbon-scenario row is required")
    carbon = carbon_rows.iloc[0]

    capex = _read("technology/technology_capex_by_year.csv")
    capex = capex.loc[capex.year.eq(config.planning_year)].copy()
    ruc = _read("technology/thermal_nuclear_ruc_parameters.csv")
    thermal_om = _read("technology/thermal_nuclear_om_parameters.csv")
    storage = _read("technology/storage_technical_parameters.csv")
    fuel = _read("technology/province_fuel_generation_cost_by_year.csv")
    fuel = fuel.loc[fuel.year.eq(config.planning_year)].copy()
    emissions = _read("technology/emission_factors_by_year.csv")
    emissions = emissions.loc[emissions.year.eq(config.planning_year)].copy()
    dac = _read("technology/dac_parameters_by_year.csv")
    dac = dac.loc[dac.year.eq(config.planning_year)].copy()
    ccs_cost = _read("technology/ccs_cost_parameters.csv").iloc[0]

    load_center_subdirectory = str(config.raw["load_center_network"]["input_subdirectory"])
    load_centers = _read(f"{load_center_subdirectory}/load_centers.csv")
    vre_load_center_routes = _read(f"{load_center_subdirectory}/vre_routes.csv")
    hydro_load_center_routes = _read(f"{load_center_subdirectory}/hydro_routes.csv")
    intra_load_center_edges = _read(f"{load_center_subdirectory}/intra_edges.csv")
    initial_spur = _read(f"{load_center_subdirectory}/initial_spur_capacity_2025.csv")
    substations = _read(f"{load_center_subdirectory}/substation_initial_capacity_2025.csv")
    # The promoted Natural Earth route replaces the former 337-city route for
    # all production spur/trunk decisions.
    grid_connections = vre_load_center_routes

    require_columns(
        load_centers,
        ["load_center_id", "province_code", "annual_demand_share_in_province", "lon", "lat"],
        "Natural Earth load centers",
    )
    require_columns(
        vre_load_center_routes,
        ["grid_uid", "province_code", "substation_id", "load_center_id"],
        "VRE load-center routes",
    )
    require_columns(
        hydro_load_center_routes,
        ["hydrochn_row_id", "province_code", "substation_id", "load_center_id", "hydro_spur_distance_km"],
        "hydropower load-center routes",
    )
    require_columns(
        intra_load_center_edges,
        [
            "intra_edge_id", "province_code", "from_load_center_id", "to_load_center_id",
            "distance_km", "unit_cost_yuan_per_kw", "initial_capacity_gw",
        ],
        "intra-province load-center edges",
    )
    if len(load_centers) != 278 or not load_centers.load_center_id.is_unique:
        raise ValueError("Natural Earth production scenario requires 278 unique load centers")
    share_error = (
        load_centers.groupby("province_code").annual_demand_share_in_province.sum()
        .sub(1.0).abs()
    )
    if share_error.max() > 1e-9:
        raise ValueError(f"Load-center demand shares do not close by province: {share_error.max()}")
    if vre_load_center_routes.grid_uid.duplicated().any():
        raise ValueError("VRE load-center routes must be unique by grid_uid")
    if hydro_load_center_routes.hydrochn_row_id.duplicated().any():
        raise ValueError("Hydropower load-center routes must be unique by hydrochn_row_id")
    if set(vre_sites.grid_uid).difference(vre_load_center_routes.grid_uid):
        raise ValueError("Some active VRE sites have no Natural Earth load-center route")
    if set(hydro.hydrochn_row_id).difference(hydro_load_center_routes.hydrochn_row_id):
        raise ValueError("Some hydropower stations have no Natural Earth load-center route")
    if not hydro_cascade_edges.empty:
        require_columns(
            hydro_cascade_nodes,
            ["node_id", "hydrochn_row_ids", "model_station_count", "model_capacity_gw"],
            "hydropower cascade nodes",
        )
        require_columns(
            hydro_cascade_edges,
            [
                "edge_id", "source_node_id", "target_node_id",
                "source_hydrochn_row_ids", "target_hydrochn_row_ids",
                "travel_lag_h", "lag_quality_flag",
            ],
            "hydropower cascade edges",
        )
        cascade_ids: set[str] = set()
        for value in pd.concat(
            [hydro_cascade_nodes.hydrochn_row_ids, hydro_cascade_edges.source_hydrochn_row_ids,
             hydro_cascade_edges.target_hydrochn_row_ids],
            ignore_index=True,
        ).dropna():
            cascade_ids.update(part.strip() for part in str(value).split(";") if part.strip())
        missing_cascade_ids = cascade_ids.difference(hydro.hydrochn_row_id.astype(str))
        if missing_cascade_ids:
            raise ValueError(
                f"Cascade topology references missing hydropower stations: "
                f"{sorted(missing_cascade_ids)[:10]}"
            )

    return ModelData(
        provinces=provinces,
        load=load,
        load_gw=load_pivot.to_numpy(dtype=np.float64),
        vre_points=points,
        vre_sites=vre_sites,
        thermal_floor=thermal_floor,
        nuclear_floor=nuclear_floor,
        hydro_stations=hydro,
        hydro_cascade_nodes=hydro_cascade_nodes,
        hydro_cascade_edges=hydro_cascade_edges,
        biomass=biomass,
        lines=lines,
        carbon=carbon,
        capex=capex,
        ruc=ruc,
        thermal_om=thermal_om,
        storage=storage,
        fuel=fuel,
        emissions=emissions,
        dac=dac,
        ccs_cost=ccs_cost,
        grid_connections=grid_connections,
        initial_spur=initial_spur,
        substations=substations,
        load_centers=load_centers,
        vre_load_center_routes=vre_load_center_routes,
        hydro_load_center_routes=hydro_load_center_routes,
        intra_load_center_edges=intra_load_center_edges,
        cf=cf,
    )
