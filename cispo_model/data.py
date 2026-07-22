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
from .planning_state import PlanningState


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
    load_components_gw: dict[str, np.ndarray]
    vre_points: pd.DataFrame
    vre_sites: pd.DataFrame
    thermal_floor: pd.DataFrame
    thermal_floor_all_years: pd.DataFrame
    nuclear_floor: pd.DataFrame
    nuclear_upper: pd.DataFrame
    hydro_stations: pd.DataFrame
    hydro_cascade_nodes: pd.DataFrame
    hydro_cascade_edges: pd.DataFrame
    biomass: pd.DataFrame
    biomass_capacity_bounds: pd.DataFrame
    lines: pd.DataFrame
    carbon: pd.Series
    capex: pd.DataFrame
    ruc: pd.DataFrame
    thermal_om: pd.DataFrame
    storage: pd.DataFrame
    storage_bounds: pd.DataFrame
    battery_bounds: pd.DataFrame
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
    planning_state: PlanningState

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


def load_model_data(
    config: ModelConfig,
    planning_state: PlanningState | None = None,
) -> ModelData:
    planning_state = planning_state or PlanningState.empty(config.boundary_year)
    provinces = _read(
        "sets/provinces.csv",
        usecols=["province_code", "province_name_en", "province_name_zh"],
    ).sort_values("province_code").reset_index(drop=True)
    if len(provinces) != 31 or not provinces.province_code.is_unique:
        raise ValueError("The model requires 31 unique province rows")

    load = _read(
        "load/hourly_load_2025_2060.csv.gz",
        usecols=[
            "province_code", "year", "hour_index", "datetime_bj", "demand_gw",
            "base_residual_gw", "heating_gw", "cooling_gw", "ev_gw",
        ],
    )
    load = load.loc[load.year.eq(config.planning_year)].copy()
    expected_load_rows = len(provinces) * config.hours
    if len(load) != expected_load_rows:
        raise ValueError(
            f"{config.planning_year} load rows={len(load)}; expected {expected_load_rows}"
        )
    if load.duplicated(["province_code", "hour_index"]).any():
        raise ValueError("Duplicate province-hour load rows")
    province_order = provinces.province_code.tolist()
    load_pivot = load.pivot(index="province_code", columns="hour_index", values="demand_gw")
    load_pivot = load_pivot.reindex(index=province_order, columns=range(config.hours))
    if load_pivot.isna().any().any() or (load_pivot < 0).any().any():
        raise ValueError("Load matrix contains missing or negative values")
    component_columns = {
        "base_residual": "base_residual_gw",
        "heating": "heating_gw",
        "cooling": "cooling_gw",
        "ev": "ev_gw",
    }
    load_components_gw: dict[str, np.ndarray] = {}
    for component, column in component_columns.items():
        pivot = load.pivot(index="province_code", columns="hour_index", values=column)
        pivot = pivot.reindex(index=province_order, columns=range(config.hours))
        values = pivot.to_numpy(dtype=np.float64)
        if not np.isfinite(values).all() or (values < 0.0).any():
            raise ValueError(f"{component} load matrix contains missing or negative values")
        load_components_gw[component] = values
    component_sum = sum(load_components_gw.values())
    closure_error = float(
        np.abs(load_pivot.to_numpy(dtype=np.float64) - component_sum).max()
    )
    if closure_error > 1e-9:
        raise ValueError(
            f"Load-component closure error {closure_error:.6g} GW exceeds 1e-9 GW"
        )

    point_columns = [
        "grid_uid", "grid_id", "province_code", "lon", "lat", "is_land",
        str(config.raw["ccs_injection_field"]),
    ]
    for technology in VRE_TECHS:
        point_columns.extend(
            [
                f"existing_{technology}_gw",
                f"pmax_{technology}_{config.vre_scenario}_gw",
            ]
        )
    points = _read("vre/optimization_points.csv", usecols=point_columns)
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

    cf_index = _read(
        "vre/hourly_cf_index.csv",
        usecols=["technology", "year", "zarr_path"],
    )
    cf = CapacityFactorStore(cf_index, config.weather_year)
    vre_sites = _resolve_vre_cf_sites(points, vre_sites, cf)

    thermal_floor_all_years = _read(
        "thermal/capacity_floor_by_year.csv",
        usecols=["province_code", "year", "technology", "capacity_floor_gw"],
    )
    thermal_floor = thermal_floor_all_years.loc[
        thermal_floor_all_years.year.eq(config.planning_year)
    ].copy()
    nuclear_floor = _read(
        "thermal/nuclear_capacity_floor_by_year.csv",
        usecols=["province_code", "year", "capacity_floor_gw"],
    )
    nuclear_floor = nuclear_floor.loc[nuclear_floor.year.eq(config.planning_year)].copy()
    nuclear_upper = _read(
        "thermal/nuclear_capacity_upper_by_year.csv",
        usecols=["province_code", "year", "capacity_upper_gw"],
    )
    nuclear_upper = nuclear_upper.loc[
        nuclear_upper.year.eq(config.planning_year)
    ].copy()
    if len(nuclear_floor) != len(provinces) or len(nuclear_upper) != len(provinces):
        raise ValueError("Nuclear capacity bounds must cover all 31 model provinces")
    if (
        nuclear_floor.duplicated("province_code").any()
        or nuclear_upper.duplicated("province_code").any()
    ):
        raise ValueError("Duplicate province rows in nuclear capacity bounds")
    if (
        set(nuclear_floor.province_code) != set(province_order)
        or set(nuclear_upper.province_code) != set(province_order)
    ):
        raise ValueError("Nuclear capacity bounds must match the model province set")
    nuclear_check = nuclear_floor[["province_code", "capacity_floor_gw"]].merge(
        nuclear_upper[["province_code", "capacity_upper_gw"]],
        on="province_code",
        validate="one_to_one",
    )
    if nuclear_check.capacity_floor_gw.gt(
        nuclear_check.capacity_upper_gw + 1e-9
    ).any():
        raise ValueError("Nuclear capacity floor exceeds the configured upper bound")
    hydro = _read(
        "hydro/hydro_stations.csv",
        usecols=[
            "hydrochn_row_id", "plant_name_model", "lon", "lat", "comid",
            "province_code", "existing_capacity_gw", "capacity_potential_gw",
            "head_m", "q_rated_m3s", "active_storage_gl",
            "operation_type_model", "status_model",
            "installed_operation_type_assigned", "potential_operation_type_paper",
            "operation_type_scope", "river_group_stage2", "stage2_issue_flags",
        ],
    )
    try:
        hydro_cascade_nodes = _read(
            "hydro/cascade_topology_nodes.csv",
            usecols=[
                "node_id", "hydrochn_row_ids", "model_station_count",
                "model_capacity_gw",
            ],
        )
        hydro_cascade_edges = _read(
            "hydro/cascade_topology_edges.csv",
            usecols=[
                "edge_id", "source_node_id", "target_node_id",
                "source_hydrochn_row_ids", "target_hydrochn_row_ids",
                "travel_lag_h", "lag_quality_flag",
            ],
        )
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
    biomass = _read(
        "biomass/fuel_potential_by_province_year.csv",
        usecols=["province_code", "year", "thermcal_gj_per_year"],
    )
    biomass = biomass.loc[biomass.year.eq(config.planning_year)].copy()
    biomass_capacity_bounds = _read(
        "biomass/capacity_upper_by_province_year.csv",
        usecols=[
            "province_code", "year", "capacity_upper_gw",
            "formula_capacity_upper_gw", "minimum_existing_pair_capacity_gw",
            "capacity_upper_adjusted_to_floor",
        ],
    )
    biomass_capacity_bounds = biomass_capacity_bounds.loc[
        biomass_capacity_bounds.year.eq(config.planning_year)
    ].copy()
    if (
        len(biomass) != len(provinces)
        or len(biomass_capacity_bounds) != len(provinces)
        or biomass.duplicated("province_code").any()
        or biomass_capacity_bounds.duplicated("province_code").any()
    ):
        raise ValueError("Biomass fuel and capacity bounds require one row per province")
    if (
        set(biomass.province_code) != set(province_order)
        or set(biomass_capacity_bounds.province_code) != set(province_order)
    ):
        raise ValueError("Biomass bounds must match the model province set")
    if biomass_capacity_bounds.capacity_upper_gw.lt(-1e-9).any():
        raise ValueError("Biomass capacity upper bounds must be nonnegative")
    lines = _read(
        "transmission/candidate_corridors.csv",
        usecols=[
            "from_province_code", "to_province_code", "distance_km",
            "allowed_by_model", "preset_technology", "preset_option",
            "preset_voltage", "existing_capacity_gw",
            "preset_unit_cost_yuan_per_kw",
        ],
    )
    lines = lines.loc[lines.allowed_by_model.astype(bool)].copy().reset_index(drop=True)
    lines["line_id"] = [f"CORRIDOR_{i:04d}" for i in range(len(lines))]

    carbon_table = _read(
        "carbon/emissions_limits_by_scenario.csv",
        usecols=[
            "scenario", "year", "emissions_limit_mtco2_per_year",
            "constraint_active",
        ],
    )
    carbon_rows = carbon_table.loc[
        carbon_table.scenario.eq(config.raw["carbon_scenario"])
        & carbon_table.year.eq(config.planning_year)
    ]
    if len(carbon_rows) != 1:
        raise ValueError("Exactly one active carbon-scenario row is required")
    carbon = carbon_rows.iloc[0]

    capex = _read(
        "technology/technology_capex_by_year.csv",
        usecols=["technology", "year", "capex_yuan_per_kw"],
    )
    capex = capex.loc[capex.year.eq(config.planning_year)].copy()
    ruc = _read(
        "technology/thermal_nuclear_ruc_parameters.csv",
        usecols=[
            "technology", "pmin_fraction", "pmax_fraction", "min_up_h",
            "min_down_h", "startup_yuan_per_mw", "shutdown_yuan_per_mw",
            "inertia_s", "ramp_fraction_per_h", "fuel_load_mj_per_kwh",
            "ccs_power_loss_fraction",
        ],
    )
    thermal_om = _read(
        "technology/thermal_nuclear_om_parameters.csv",
        usecols=[
            "technology", "fixed_om_fraction_capex_per_year",
            "variable_om_yuan_per_mwh",
        ],
    )
    storage = _read(
        "technology/storage_technical_parameters.csv",
        usecols=[
            "technology", "fixed_om_fraction_capex_per_year",
            "variable_om_yuan_per_mwh", "charge_efficiency",
            "discharge_efficiency", "self_discharge_fraction_per_day",
            "duration_h", "lifetime_years",
        ],
    )
    storage_bounds = _read(
        "storage/phs_capacity_bounds_by_province_year.csv",
        usecols=[
            "province_code", "year", "technology", "capacity_floor_gw",
            "capacity_upper_gw", "duration_h",
        ],
    )
    storage_bounds = storage_bounds.loc[
        storage_bounds.year.eq(config.planning_year)
    ].copy()
    if len(storage_bounds) != len(provinces):
        raise ValueError(
            f"{config.planning_year} PHS bounds rows={len(storage_bounds)}; "
            f"expected {len(provinces)}"
        )
    if storage_bounds.duplicated(["province_code", "technology"]).any():
        raise ValueError("Duplicate province-technology PHS capacity bounds")
    if set(storage_bounds.technology) != {"phs"}:
        raise ValueError("PHS capacity bounds must contain only technology='phs'")
    if set(storage_bounds.province_code) != set(province_order):
        raise ValueError("PHS capacity bounds must cover all 31 model provinces")
    if (
        storage_bounds.capacity_floor_gw.lt(-1e-9).any()
        or storage_bounds.capacity_upper_gw.lt(
            storage_bounds.capacity_floor_gw - 1e-9
        ).any()
    ):
        raise ValueError("Invalid PHS capacity floor or upper bound")
    battery_bounds = _read(
        "storage/battery_capacity_floor_by_province_year.csv",
        usecols=[
            "province_code", "year", "technology", "capacity_floor_gw",
            "duration_h",
        ],
    )
    battery_bounds = battery_bounds.loc[
        battery_bounds.year.eq(config.planning_year)
    ].copy()
    if len(battery_bounds) != len(provinces):
        raise ValueError(
            f"{config.planning_year} battery floor rows={len(battery_bounds)}; "
            f"expected {len(provinces)}"
        )
    if battery_bounds.duplicated(["province_code", "technology"]).any():
        raise ValueError("Duplicate province-technology battery capacity floors")
    if set(battery_bounds.technology) != {"battery"}:
        raise ValueError("Battery capacity floor table must use technology='battery'")
    if set(battery_bounds.province_code) != set(province_order):
        raise ValueError("Battery capacity floors must cover all 31 model provinces")
    if battery_bounds.capacity_floor_gw.lt(-1e-9).any():
        raise ValueError("Battery capacity floors must be nonnegative")
    fuel = _read(
        "technology/province_fuel_generation_cost_by_year.csv",
        usecols=[
            "province_code", "year", "technology", "fuel_cost_yuan_per_mwh",
            "dispatch_allowed", "new_capacity_allowed",
        ],
    )
    fuel = fuel.loc[fuel.year.eq(config.planning_year)].copy()
    expected_fuel_technologies = set(THERMAL_TECHS).difference({"nuclear"})
    if len(fuel) != len(provinces) * len(expected_fuel_technologies):
        raise ValueError(
            f"Fuel cost rows for {config.planning_year}={len(fuel)}; expected "
            f"{len(provinces) * len(expected_fuel_technologies)}"
        )
    if fuel.duplicated(["province_code", "technology"]).any():
        raise ValueError("Duplicate province-technology fuel cost rows")
    if set(fuel.province_code) != set(province_order):
        raise ValueError("Fuel cost table must cover all model provinces")
    if set(fuel.technology) != expected_fuel_technologies:
        raise ValueError(
            "Fuel cost technology coverage mismatch: "
            f"{sorted(set(fuel.technology))}"
        )
    available_fuel = fuel.loc[fuel.dispatch_allowed.astype(bool)]
    if (
        available_fuel.fuel_cost_yuan_per_mwh.isna().any()
        or not np.isfinite(
            available_fuel.fuel_cost_yuan_per_mwh.to_numpy(dtype=float)
        ).all()
        or available_fuel.fuel_cost_yuan_per_mwh.lt(0.0).any()
    ):
        raise ValueError("Allowed fuel cost rows must have finite nonnegative cost")
    emissions = _read(
        "technology/emission_factors_by_year.csv",
        usecols=[
            "technology", "year", "emission_factor_mtco2_per_gwh",
            "ccs_capture_fraction",
        ],
    )
    emissions = emissions.loc[emissions.year.eq(config.planning_year)].copy()
    dac = _read(
        "technology/dac_parameters_by_year.csv",
        usecols=[
            "technology", "year",
            "annualized_capex_million_yuan_per_mtco2_per_year_capacity_year",
            "fixed_om_million_yuan_per_mtco2_per_year_capacity_year",
            "variable_om_yuan_per_tco2", "average_power_gw_per_mtco2_per_year",
            "lifetime_years",
        ],
    )
    dac = dac.loc[dac.year.eq(config.planning_year)].copy()
    ccs_cost = _read(
        "technology/ccs_cost_parameters.csv",
        usecols=[
            "capture_yuan_per_tco2", "transport_yuan_per_tco2_km",
            "storage_yuan_per_tco2",
        ],
    ).iloc[0]

    load_center_subdirectory = str(config.raw["load_center_network"]["input_subdirectory"])
    load_centers = _read(
        f"{load_center_subdirectory}/load_centers.csv",
        usecols=[
            "load_center_id", "province_code", "province_name_zh",
            "annual_demand_share_in_province", "lon", "lat",
        ],
    )
    vre_load_center_routes = _read(
        f"{load_center_subdirectory}/vre_routes.csv",
        usecols=[
            "grid_uid", "province_code", "substation_id", "load_center_id",
            "onwind_spur_distance_km", "offwind_export_distance_km",
            "upv_spur_distance_km", "dpv_spur_distance_km",
        ],
    )
    hydro_load_center_routes = _read(
        f"{load_center_subdirectory}/hydro_routes.csv",
        usecols=[
            "hydrochn_row_id", "province_code", "substation_id",
            "load_center_id", "hydro_spur_distance_km",
        ],
    )
    intra_load_center_edges = _read(
        f"{load_center_subdirectory}/intra_edges.csv",
        usecols=[
            "intra_edge_id", "province_code", "from_load_center_id",
            "to_load_center_id", "distance_km", "technology",
            "unit_cost_yuan_per_kw", "initial_capacity_gw",
        ],
    )
    initial_spur = _read(
        f"{load_center_subdirectory}/initial_spur_capacity_2025.csv",
        usecols=["grid_uid", "technology", "initial_spur_capacity_gw"],
    )
    substations = _read(
        f"{load_center_subdirectory}/substation_initial_capacity_2025.csv",
        usecols=[
            "substation_id", "province_code", "initial_trunk_capacity_gw",
            "trunk_distance_km",
        ],
    )
    # The configured load-center route controls all production spur/trunk
    # decisions; alternative packages remain isolated under versioned folders.
    grid_connections = vre_load_center_routes

    require_columns(
        load_centers,
        ["load_center_id", "province_code", "annual_demand_share_in_province", "lon", "lat"],
        "configured load centers",
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
    expected_load_center_count = int(
        config.raw["load_center_network"]["expected_load_center_count"]
    )
    if (
        len(load_centers) != expected_load_center_count
        or not load_centers.load_center_id.is_unique
    ):
        raise ValueError(
            "Configured load-center scenario requires "
            f"{expected_load_center_count} unique load centers"
        )
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
        raise ValueError("Some active VRE sites have no configured load-center route")
    if set(hydro.hydrochn_row_id).difference(hydro_load_center_routes.hydrochn_row_id):
        raise ValueError("Some hydropower stations have no configured load-center route")
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
        load_components_gw=load_components_gw,
        vre_points=points,
        vre_sites=vre_sites,
        thermal_floor=thermal_floor,
        thermal_floor_all_years=thermal_floor_all_years,
        nuclear_floor=nuclear_floor,
        nuclear_upper=nuclear_upper,
        hydro_stations=hydro,
        hydro_cascade_nodes=hydro_cascade_nodes,
        hydro_cascade_edges=hydro_cascade_edges,
        biomass=biomass,
        biomass_capacity_bounds=biomass_capacity_bounds,
        lines=lines,
        carbon=carbon,
        capex=capex,
        ruc=ruc,
        thermal_om=thermal_om,
        storage=storage,
        storage_bounds=storage_bounds,
        battery_bounds=battery_bounds,
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
        planning_state=planning_state,
    )
