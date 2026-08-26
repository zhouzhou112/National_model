"""Strict data contract and chunked time-series access for the CISPO model."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from pathlib import PureWindowsPath
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.spatial import cKDTree

from .config import ModelConfig, ROOT
from .planning_state import PlanningState
from .technology_registry import load_technology_parameter_registry
from .wave_energy import WaveEnergyData, load_wave_energy_data


DATA_ROOT = Path(os.environ.get("CISPO_DATA_ROOT", str(ROOT / "data")))
VRE_TECHS = ("onwind", "offwind", "upv", "dpv")
# DPV is behind its assigned load center in the production contract and does
# not use the spur/trunk interface.  The other technologies follow CISPO
# S4.3.4's two-stage intra-grid connection representation.
INTRA_GRID_VRE_TECHS = ("onwind", "offwind", "upv")
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


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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

    def __init__(
        self,
        index: pd.DataFrame,
        weather_year: int,
        time_alignment: str = "source_utc_year_first_8760_v1",
    ):
        try:
            import zarr
        except ImportError as exc:  # pragma: no cover - environment diagnostic
            raise RuntimeError(
                "zarr is required in the Gurobi environment; install requirements-data.txt"
            ) from exc
        self._zarr = zarr
        self.weather_year = int(weather_year)
        self.time_alignment = str(time_alignment)
        selected = index.copy()
        selected["year"] = selected["year"].astype(int)
        if selected.duplicated(["year", "technology"]).any():
            raise ValueError("Duplicate capacity-factor stores for year/technology")
        self.index = selected.set_index(["year", "technology"]).sort_index()
        self.model_source_year, self.model_source_hour, self.model_local_time = (
            self._build_model_hour_mapping()
        )
        self.source_years = tuple(
            int(year) for year in np.unique(self.model_source_year)
        )
        self.groups: dict[tuple[int, str], object] = {}
        self.positions: dict[tuple[int, str], dict[int, int]] = {}
        self.dimensions: dict[tuple[int, str], tuple[str, ...]] = {}

    def _build_model_hour_mapping(
        self,
    ) -> tuple[np.ndarray, np.ndarray, pd.DatetimeIndex]:
        if self.time_alignment == "source_utc_year_first_8760_v1":
            local_time = pd.date_range(
                f"{self.weather_year}-01-01 00:00:00",
                periods=8760,
                freq="h",
            )
            return (
                np.full(8760, self.weather_year, dtype=np.int64),
                np.arange(8760, dtype=np.int64),
                local_time,
            )
        if self.time_alignment != "beijing_natural_year_drop_feb29_v1":
            raise ValueError(
                f"Unsupported capacity-factor time alignment {self.time_alignment!r}"
            )
        local_time = pd.date_range(
            f"{self.weather_year}-01-01 00:00:00",
            f"{self.weather_year}-12-31 23:00:00",
            freq="h",
        )
        local_time = local_time[
            ~((local_time.month == 2) & (local_time.day == 29))
        ]
        if len(local_time) != 8760:
            raise ValueError(
                "Beijing natural-year capacity-factor mapping must contain 8760 hours"
            )
        utc_time = local_time - pd.Timedelta(hours=8)
        source_year = utc_time.year.to_numpy(dtype=np.int64)
        source_start = pd.to_datetime(
            {
                "year": source_year,
                "month": np.ones(len(source_year), dtype=np.int64),
                "day": np.ones(len(source_year), dtype=np.int64),
            }
        )
        source_hour = (
            (utc_time.to_numpy() - source_start.to_numpy())
            / np.timedelta64(1, "h")
        ).astype(np.int64)
        return source_year, source_hour, local_time

    def _open(self, source_technology: str, source_year: int | None = None):
        source_year = self.weather_year if source_year is None else int(source_year)
        key = (source_year, source_technology)
        if key not in self.groups:
            if key not in self.index.index:
                raise KeyError(
                    f"No CF store indexed for {source_technology}:{source_year}"
                )
            indexed_path = str(self.index.loc[key, "zarr_path"])
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
            required_source_hours = self.model_source_hour[
                self.model_source_year == source_year
            ]
            time_axis = dimensions.index("time")
            if (
                required_source_hours.size
                and int(required_source_hours.max()) >= int(group["cf"].shape[time_axis])
            ):
                raise ValueError(
                    f"CF store {path} does not cover required source hour "
                    f"{int(required_source_hours.max())}"
                )
            self.groups[key] = group
            self.positions[key] = {
                int(grid_id): position for position, grid_id in enumerate(grid_ids)
            }
            self.dimensions[key] = dimensions
        return self.groups[key]

    def available_grid_ids(self, source_technology: str) -> set[int]:
        reference: set[int] | None = None
        for source_year in self.source_years:
            self._open(source_technology, source_year)
            current = set(self.positions[(source_year, source_technology)])
            if reference is None:
                reference = current
            elif current != reference:
                raise ValueError(
                    f"CF grid IDs differ across source years for {source_technology}"
                )
        return reference or set()

    def read(
        self,
        source_technology: str,
        grid_ids: Iterable[int],
        hour_start: int,
        hour_stop: int,
    ) -> np.ndarray:
        return self.read_hours(
            source_technology,
            grid_ids,
            range(int(hour_start), int(hour_stop)),
        )

    def read_hours(
        self,
        source_technology: str,
        grid_ids: Iterable[int],
        hour_indices: Iterable[int],
    ) -> np.ndarray:
        """Read an arbitrary hour/site orthogonal selection as hours x sites."""
        grid_ids = [int(grid_id) for grid_id in grid_ids]
        model_hours = np.asarray(list(hour_indices), dtype=np.int64)
        if (
            model_hours.size
            and (
                int(model_hours.min()) < 0
                or int(model_hours.max()) >= len(self.model_source_year)
            )
        ):
            raise IndexError("Capacity-factor model hour is outside [0, 8759]")
        block = np.empty((len(model_hours), len(grid_ids)), dtype=np.float64)
        for source_year in np.unique(self.model_source_year[model_hours]):
            row_mask = self.model_source_year[model_hours] == source_year
            group = self._open(source_technology, int(source_year))
            key = (int(source_year), source_technology)
            positions = np.asarray(
                [self.positions[key][grid_id] for grid_id in grid_ids],
                dtype=np.int64,
            )
            source_hours = self.model_source_hour[model_hours[row_mask]]
            array = group["cf"]
            dimensions = self.dimensions[key]
            if dimensions == ("time", "grid_id"):
                current = np.asarray(
                    array.oindex[source_hours, positions], dtype=np.float64
                )
            else:
                current = np.asarray(
                    array.oindex[positions, source_hours], dtype=np.float64
                ).T
            block[row_mask, :] = current
        if block.shape != (len(model_hours), len(grid_ids)):
            raise ValueError(
                f"CF arbitrary-hour block shape mismatch for {source_technology}: {block.shape}"
            )
        if not np.isfinite(block).all():
            raise ValueError(f"Non-finite CF values in {source_technology}")
        return np.clip(block, 0.0, 1.0)


@dataclass
class FlexibleLoadV4Data:
    """Validated V4/V5 service-contract inputs in province-hour order.

    The class name is retained for API compatibility with the accepted V4
    implementation. ``contract_version`` makes the V5 identity explicit.
    """

    thermal_envelopes_gw: dict[str, np.ndarray]
    thermal_availability: dict[str, np.ndarray]
    thermal_parameters: dict[str, dict[str, np.ndarray]]
    ev_availability: dict[str, np.ndarray]
    ev_mobility: dict[str, np.ndarray]
    service_costs: dict[str, dict[str, np.ndarray]]
    contract_version: str = "v4"


@dataclass
class ModelData:
    provinces: pd.DataFrame
    load: pd.DataFrame
    load_gw: np.ndarray
    load_components_gw: dict[str, np.ndarray]
    flexible_load_envelopes_gw: dict[str, np.ndarray]
    flexible_load_v4: FlexibleLoadV4Data | None
    vre_points: pd.DataFrame
    vre_sites: pd.DataFrame
    vre_existing_cohorts: pd.DataFrame
    thermal_floor: pd.DataFrame
    thermal_floor_all_years: pd.DataFrame
    nuclear_floor: pd.DataFrame
    nuclear_upper: pd.DataFrame
    hydro_stations: pd.DataFrame
    hydro_aggregate_capacity: pd.DataFrame
    hydro_aggregate_availability_cf: np.ndarray
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
    technology_parameter_registry: dict[str, Any]
    grid_connections: pd.DataFrame
    initial_spur: pd.DataFrame
    substations: pd.DataFrame
    load_centers: pd.DataFrame
    vre_load_center_routes: pd.DataFrame
    hydro_load_center_routes: pd.DataFrame
    intra_load_center_edges: pd.DataFrame
    cf: CapacityFactorStore
    wave: WaveEnergyData | None
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


@dataclass(frozen=True)
class IntraGridVreDesign:
    """Full-weather design factors for the CISPO-style VRE connection layer.

    ``substation_equivalent_peak_cf`` implements Eq. S4-19 using the fixed
    site potential as the aggregation weight.  It is deliberately a compact
    annual design coefficient, rather than an hourly trunk-flow formulation.
    """

    site_max_cf: np.ndarray
    site_substation_position: np.ndarray
    substation_potential_gw: np.ndarray
    substation_equivalent_peak_gw: np.ndarray
    substation_equivalent_peak_cf: np.ndarray


def compute_intra_grid_vre_design(
    config: ModelConfig,
    data: ModelData,
    *,
    site_substation: Iterable[str],
    substation_ids: Iterable[str],
) -> IntraGridVreDesign:
    """Compute bounded-memory spur and shared-trunk design factors.

    For each site, the spur requirement remains ``max_t(cf) * capacity``
    (CISPO Eq. S4-18).  For each substation, the wind/PV trunk coefficient is

    ``max_t(sum_z(cf[z, t] * potential[z]) / sum_z(potential[z]))``.

    This is the linear CISPO Eq. S4-19 approximation: it preserves the
    potential-weighted wind/PV complementarity without adding hourly trunk
    variables or constraints.  All 8,760 model-weather hours are scanned even
    when the caller builds a truncated diagnostic LP.
    """

    substation_ids = np.asarray([str(value) for value in substation_ids], dtype=object)
    if len(np.unique(substation_ids)) != len(substation_ids):
        raise ValueError("Intra-grid substation IDs must be unique")

    site_substation = np.asarray([str(value) for value in site_substation], dtype=object)
    if len(site_substation) != len(data.vre_sites):
        raise ValueError("VRE-site/substation mapping length mismatch")

    site_technology = data.vre_sites.technology.astype(str).to_numpy()
    connected_mask = np.isin(site_technology, INTRA_GRID_VRE_TECHS)
    substation_index = {value: position for position, value in enumerate(substation_ids)}
    site_substation_position = np.full(len(data.vre_sites), -1, dtype=np.int64)
    missing = sorted(
        set(site_substation[connected_mask]).difference(substation_index)
    )
    if missing:
        raise ValueError(
            "Connected VRE sites reference unknown substations: "
            + ", ".join(missing[:10])
        )
    site_substation_position[connected_mask] = np.asarray(
        [substation_index[value] for value in site_substation[connected_mask]],
        dtype=np.int64,
    )

    potential = data.vre_sites.capacity_upper_gw.to_numpy(dtype=np.float64)
    if (
        not np.isfinite(potential).all()
        or (potential[connected_mask] <= 0.0).any()
    ):
        raise ValueError("Connected VRE site potentials must be finite and positive")
    substation_potential = np.bincount(
        site_substation_position[connected_mask],
        weights=potential[connected_mask],
        minlength=len(substation_ids),
    )

    group_specs = []
    for source_technology, group in data.vre_sites.groupby(
        "cf_source_technology", sort=False
    ):
        positions = group.index.to_numpy(dtype=np.int64)
        connected_positions = positions[connected_mask[positions]]
        if len(connected_positions):
            incidence = csr_matrix(
                (
                    potential[connected_positions],
                    (
                        np.arange(len(connected_positions), dtype=np.int64),
                        site_substation_position[connected_positions],
                    ),
                ),
                shape=(len(connected_positions), len(substation_ids)),
            )
            connected_local = np.isin(positions, connected_positions)
        else:
            incidence = None
            connected_local = np.zeros(len(positions), dtype=bool)
        group_specs.append(
            (
                str(source_technology),
                positions,
                group.cf_grid_id.to_numpy(dtype=np.int64),
                connected_local,
                incidence,
            )
        )

    maxima = np.zeros(len(data.vre_sites), dtype=np.float64)
    substation_peak = np.zeros(len(substation_ids), dtype=np.float64)
    chunk = int(config.raw["construction"]["hour_chunk_size"])
    for start in range(0, config.hours, chunk):
        stop = min(start + chunk, config.hours)
        station_output = np.zeros((stop - start, len(substation_ids)), dtype=np.float64)
        for source_technology, positions, grid_ids, connected_local, incidence in group_specs:
            block = data.cf.read(source_technology, grid_ids, start, stop)
            maxima[positions] = np.maximum(maxima[positions], block.max(axis=0))
            if incidence is not None:
                station_output += np.asarray(block[:, connected_local] @ incidence)
        substation_peak = np.maximum(substation_peak, station_output.max(axis=0))

    if (
        not np.isfinite(maxima).all()
        or (maxima < 0.0).any()
        or (maxima > 1.0 + 1e-9).any()
    ):
        raise ValueError("Invalid full-weather VRE maximum-CF vector")
    equivalent_cf = np.divide(
        substation_peak,
        substation_potential,
        out=np.zeros_like(substation_peak),
        where=substation_potential > 0.0,
    )
    if (
        not np.isfinite(equivalent_cf).all()
        or (equivalent_cf < -1e-12).any()
        or (equivalent_cf > 1.0 + 1e-9).any()
    ):
        raise ValueError("Invalid substation equivalent peak capacity factors")
    return IntraGridVreDesign(
        site_max_cf=maxima,
        site_substation_position=site_substation_position,
        substation_potential_gw=substation_potential,
        substation_equivalent_peak_gw=substation_peak,
        substation_equivalent_peak_cf=np.clip(equivalent_cf, 0.0, 1.0),
    )


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
        unresolved_wind = unresolved & sites.technology.isin({"onwind", "offwind"})
        if unresolved_wind.any():
            examples = sites.loc[
                unresolved_wind,
                ["grid_uid", "grid_id", "province_code", "technology"],
            ].head(10)
            raise ValueError(
                "Wind CF is missing from both the technology-specific and "
                f"same-grid mixed-wind stores; wind-to-PV fallback is forbidden: "
                f"{examples.to_dict(orient='records')}"
            )

        unresolved_non_pv = unresolved & ~sites.technology.isin({"upv", "dpv"})
        if unresolved_non_pv.any():
            raise ValueError(
                "No capacity-factor fallback rule for technologies: "
                f"{sorted(sites.loc[unresolved_non_pv, 'technology'].unique())}"
            )

        point_by_grid = points.set_index("grid_id")
        land_grid_ids = set(
            points.loc[points.is_land.eq(1), "grid_id"].astype(np.int64)
        )
        pv_grid_ids = sorted(
            source_available["pv"].intersection(point_by_grid.index).intersection(
                land_grid_ids
            )
        )
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


_VRE_COHORT_COLUMNS = {
    "grid_uid",
    "technology",
    "start_year",
    "retire_year",
    "capacity_gw",
    "provenance",
    "start_year_status",
}


def _apply_existing_vre_cohort_floors(
    config: ModelConfig,
    vre_sites: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Replace the static 2025 VRE floor with active observed cohorts.

    Existing wind/PV may retire, but its site remains technically eligible for
    rebuilding because ``capacity_upper_gw`` is unchanged.  The input cohort
    table is therefore a lower-bound trajectory only; it never removes the
    optimiser's ability to build at the original grid cell.
    """

    retirement = config.raw["planning_sequence"]["existing_vre_retirement"]
    mode = str(retirement["mode"])
    vre_sites = vre_sites.copy()
    vre_sites["capacity_floor_2025_gw"] = vre_sites.capacity_floor_gw.to_numpy(
        dtype=float
    )
    if mode == "fixed_floor_v1":
        # Explicit no-retirement control: preserve the observed boundary floor
        # at every planning snapshot, without fabricating cohort ages.
        vre_sites["active_observed_capacity_floor_gw"] = vre_sites[
            "capacity_floor_2025_gw"
        ].to_numpy(dtype=float)
        vre_sites["existing_vre_floor_mode"] = mode
        return vre_sites, pd.DataFrame(columns=sorted(_VRE_COHORT_COLUMNS))
    if mode not in {
        "cohort_survival_v1",
        "observed_cohort_boundary_censored_v1",
    }:
        raise ValueError(f"Unsupported existing VRE retirement mode: {mode}")
    cohort_path = str(retirement["cohort_file"])
    cohort = _read(cohort_path)
    require_columns(cohort, _VRE_COHORT_COLUMNS, "Existing VRE cohort table")
    cohort = cohort.loc[:, sorted(_VRE_COHORT_COLUMNS)].copy()
    cohort["grid_uid"] = cohort.grid_uid.astype(str)
    cohort["technology"] = cohort.technology.astype(str)
    cohort["start_year"] = pd.to_numeric(cohort.start_year, errors="raise").astype(int)
    cohort["retire_year"] = pd.to_numeric(cohort.retire_year, errors="raise").astype(int)
    cohort["capacity_gw"] = pd.to_numeric(cohort.capacity_gw, errors="raise")
    if not set(cohort.technology).issubset(VRE_TECHS):
        raise ValueError("Existing VRE cohort table contains unsupported technologies")
    if (
        cohort.empty
        or not np.isfinite(cohort.capacity_gw).all()
        or (cohort.capacity_gw <= 0.0).any()
    ):
        raise ValueError("Existing VRE cohorts must have finite positive capacities")
    if (cohort.start_year > config.boundary_year).any():
        raise ValueError("Existing VRE cohorts cannot start after the boundary year")
    if (cohort.retire_year <= cohort.start_year).any():
        raise ValueError("Existing VRE cohort retire_year must exceed start_year")

    reference = vre_sites[["grid_uid", "technology", "capacity_floor_gw"]].copy()
    reference["grid_uid"] = reference.grid_uid.astype(str)
    reference = reference.rename(columns={"capacity_floor_gw": "capacity_2025_gw"})
    baseline = (
        cohort.groupby(["grid_uid", "technology"], as_index=False)["capacity_gw"]
        .sum()
        .rename(columns={"capacity_gw": "cohort_capacity_2025_gw"})
    )
    closure = reference.merge(
        baseline,
        on=["grid_uid", "technology"],
        how="outer",
        validate="one_to_one",
    ).fillna(0.0)
    unmatched = closure.loc[
        (closure.capacity_2025_gw - closure.cohort_capacity_2025_gw).abs() > 1e-8
    ]
    if not unmatched.empty:
        raise ValueError(
            "Existing VRE cohort table does not close to optimization-point "
            f"capacity floors; mismatched site-technologies={len(unmatched)}"
        )

    active = cohort.loc[cohort.retire_year.gt(config.planning_year)]
    active_floor = (
        active.groupby(["grid_uid", "technology"], as_index=False)["capacity_gw"]
        .sum()
        .rename(columns={"capacity_gw": "active_observed_capacity_floor_gw"})
    )
    vre_sites = vre_sites.merge(
        active_floor,
        on=["grid_uid", "technology"],
        how="left",
        validate="one_to_one",
    )
    vre_sites["active_observed_capacity_floor_gw"] = (
        vre_sites.active_observed_capacity_floor_gw.fillna(0.0)
    )
    vre_sites["capacity_floor_gw"] = vre_sites[
        "active_observed_capacity_floor_gw"
    ].to_numpy(dtype=float)
    vre_sites["existing_vre_floor_mode"] = "cohort_survival_v1"
    if (vre_sites.capacity_floor_gw > vre_sites.capacity_upper_gw + 1e-9).any():
        raise ValueError("Active existing VRE cohort floor exceeds site potential")
    return vre_sites, cohort


def _load_flexible_load_v4_data(
    config: ModelConfig,
    *,
    provinces: pd.DataFrame,
    load_components_gw: dict[str, np.ndarray],
    expected_rows: int,
    require_manifest: bool = True,
) -> FlexibleLoadV4Data:
    """Load an explicit V4 or V5 thermal and aggregate EV-service contract.

    The contract is intentionally fail-closed.  The retained upstream data do
    not observe connection sessions, trip chains or departure SOC, so V4 uses
    an aggregate schedulable-service inventory that closes exactly to an
    explicit share of the immutable EV charging baseline.
    """
    flexible = config.raw["flexible_load"]
    contract_version = str(flexible.get("contract_version", "v4"))
    if contract_version not in {"v4", "v5"}:
        raise ValueError(
            "Service-constrained flexible-load inputs require contract_version "
            "v4 or v5"
        )
    contract_label = contract_version.upper()
    files_key = f"{contract_version}_input_files"
    files = flexible.get(files_key, {})
    required_files = (
        "thermal_hourly_envelope_file",
        "thermal_parameters_file",
        "ev_availability_hourly_file",
        "ev_mobility_hourly_file",
        "enablement_cost_file",
        "input_manifest_file",
    )
    missing_files = [key for key in required_files if not str(files.get(key, "")).strip()]
    if missing_files:
        raise ValueError(
            f"{contract_label} service contract missing {files_key}: "
            + ", ".join(missing_files)
        )
    if require_manifest:
        manifest_path = DATA_ROOT / str(files["input_manifest_file"])
        if not manifest_path.is_file():
            raise FileNotFoundError(
                f"{contract_label} service contract requires a calibration manifest: "
                f"{manifest_path}"
            )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("contract_version") != f"flexible_load_{contract_version}":
            raise ValueError(
                f"{contract_label} calibration manifest has an unsupported "
                "contract_version"
            )
        source_manifests = manifest.get("source_manifests")
        if not isinstance(source_manifests, list) or not source_manifests:
            raise ValueError("V4 calibration manifest must record nonempty source_manifests")
        generated_files = manifest.get("generated_files", {})
        if not isinstance(generated_files, dict):
            raise ValueError("V4 calibration manifest is missing generated_files")
        for key in required_files:
            if key == "input_manifest_file":
                continue
            logical_path = str(files[key])
            record = generated_files.get(logical_path, {})
            expected_sha = str(record.get("sha256", ""))
            resolved = DATA_ROOT / logical_path
            if not expected_sha or not resolved.is_file():
                raise ValueError(
                    f"V4 calibration manifest does not close generated input {logical_path}"
                )
            if _sha256_file(resolved) != expected_sha:
                raise ValueError(
                    f"V4 calibration manifest SHA256 mismatch for {logical_path}"
                )
    province_order = provinces.province_code.astype(int).tolist()
    hours = config.hours

    def hourly_matrix(
        frame: pd.DataFrame,
        *,
        value: str,
        label: str,
        lower: float = 0.0,
        upper: float | None = None,
    ) -> np.ndarray:
        selected = frame.loc[frame.year.eq(config.planning_year)].copy()
        if len(selected) != expected_rows:
            raise ValueError(
                f"{config.planning_year} {label} rows={len(selected)}; "
                f"expected {expected_rows}"
            )
        if selected.duplicated(["province_code", "hour_index"]).any():
            raise ValueError(f"Duplicate province-hour rows in {label}")
        pivot = selected.pivot(
            index="province_code", columns="hour_index", values=value
        ).reindex(index=province_order, columns=range(hours))
        values = pivot.to_numpy(dtype=np.float64)
        if not np.isfinite(values).all() or (values < lower - 1e-12).any():
            raise ValueError(f"{label}.{value} contains non-finite or below-bound values")
        if upper is not None and (values > upper + 1e-12).any():
            raise ValueError(f"{label}.{value} exceeds {upper}")
        return values

    envelope_columns = {
        "heating_up": "heating_increase_limit_gw",
        "heating_down": "heating_reduction_limit_gw",
        "cooling_up": "cooling_increase_limit_gw",
        "cooling_down": "cooling_reduction_limit_gw",
        "heating_availability": "heating_availability_fraction",
        "cooling_availability": "cooling_availability_fraction",
    }
    envelope = _read(
        str(files["thermal_hourly_envelope_file"]),
        usecols=["province_code", "year", "hour_index", *envelope_columns.values()],
    )
    require_columns(envelope, ["province_code", "year", "hour_index"], "V4 thermal envelope")
    thermal_values = {
        name: hourly_matrix(
            envelope,
            value=column,
            label="V4 thermal envelope",
            upper=1.0 if name.endswith("availability") else None,
        )
        for name, column in envelope_columns.items()
    }
    thermal_envelopes = {
        "heating_up": thermal_values["heating_up"],
        "heating_down": thermal_values["heating_down"],
        "cooling_up": thermal_values["cooling_up"],
        "cooling_down": thermal_values["cooling_down"],
    }
    thermal_availability = {
        "heating": thermal_values["heating_availability"],
        "cooling": thermal_values["cooling_availability"],
    }
    for component in ("heating", "cooling"):
        if float(
            (thermal_envelopes[f"{component}_down"] - load_components_gw[component]).max()
        ) > 1e-9:
            raise ValueError(f"V4 {component} reduction envelope exceeds baseline load")
        active = np.maximum(
            thermal_envelopes[f"{component}_up"],
            thermal_envelopes[f"{component}_down"],
        ) > 1e-12
        if (active & (thermal_availability[component] <= 1e-12)).any():
            raise ValueError(
                f"V4 {component} has a positive envelope with zero availability"
            )

    thermal_parameter_columns = (
        "retention_per_hour",
        "charge_efficiency",
        "discharge_efficiency",
        "positive_state_duration_hours",
        "negative_state_duration_hours",
    )
    thermal_parameters_raw = _read(
        str(files["thermal_parameters_file"]),
        usecols=["province_code", "year", "component", *thermal_parameter_columns],
    )
    selected_parameters = thermal_parameters_raw.loc[
        thermal_parameters_raw.year.eq(config.planning_year)
        & thermal_parameters_raw.component.isin(["heating", "cooling"])
    ].copy()
    expected_parameter_rows = len(province_order) * 2
    if len(selected_parameters) != expected_parameter_rows:
        raise ValueError(
            f"V4 thermal parameter rows={len(selected_parameters)}; "
            f"expected {expected_parameter_rows}"
        )
    if selected_parameters.duplicated(["province_code", "component"]).any():
        raise ValueError("Duplicate province-component rows in V4 thermal parameters")
    thermal_parameters: dict[str, dict[str, np.ndarray]] = {}
    for component in ("heating", "cooling"):
        subset = selected_parameters.loc[
            selected_parameters.component.eq(component)
        ].set_index("province_code").reindex(province_order)
        if subset.isna().any().any():
            raise ValueError(f"Missing province rows in V4 {component} parameters")
        values = {
            column: subset[column].to_numpy(dtype=np.float64)
            for column in thermal_parameter_columns
        }
        if not (np.isfinite(np.stack(tuple(values.values()))).all()):
            raise ValueError(f"Non-finite V4 {component} parameters")
        if not ((values["retention_per_hour"] > 0.0) & (values["retention_per_hour"] <= 1.0)).all():
            raise ValueError(f"V4 {component} retention_per_hour must be in (0, 1]")
        for column in (
            "charge_efficiency",
            "discharge_efficiency",
        ):
            if not ((values[column] > 0.0) & (values[column] <= 1.0)).all():
                raise ValueError(f"V4 {component} {column} must be in (0, 1]")
        for column in (
            "positive_state_duration_hours",
            "negative_state_duration_hours",
        ):
            if not (values[column] > 0.0).all():
                raise ValueError(f"V4 {component} {column} must be positive")
        thermal_parameters[component] = values

    availability_columns = (
        "connected_vehicle_fraction",
        "available_charge_power_gw",
        "available_discharge_power_gw",
        "fleet_energy_capacity_gwh",
    )
    ev_availability_raw = _read(
        str(files["ev_availability_hourly_file"]),
        usecols=["province_code", "year", "hour_index", *availability_columns],
    )
    ev_availability = {
        column: hourly_matrix(
            ev_availability_raw,
            value=column,
            label="V4 EV availability",
            upper=1.0 if column == "connected_vehicle_fraction" else None,
        )
        for column in availability_columns
    }
    if not np.allclose(
        ev_availability["connected_vehicle_fraction"], 1.0, atol=1e-12
    ):
        raise ValueError(
            "Data-supported V4 requires connected_vehicle_fraction=1 as a "
            "service-normalisation field; it is not a measured connection profile"
        )
    shiftable_fraction = float(flexible["ev_v1g"]["shiftable_energy_fraction"])
    flexible_ev_baseline = shiftable_fraction * load_components_gw["ev"]
    if (
        ev_availability["available_charge_power_gw"]
        + 1e-12
        < flexible_ev_baseline
    ).any():
        raise ValueError(
            "V4 EV available_charge_power_gw must retain the immutable "
            "shiftable share of the EV baseline as a feasible reference"
        )

    mobility_columns = (
        "driving_energy_withdrawal_gwh",
        "minimum_departure_energy_gwh",
    )
    ev_mobility_raw = _read(
        str(files["ev_mobility_hourly_file"]),
        usecols=["province_code", "year", "hour_index", *mobility_columns],
    )
    ev_mobility = {
        column: hourly_matrix(
            ev_mobility_raw,
            value=column,
            label="V4 EV mobility",
        )
        for column in mobility_columns
    }
    if (
        ev_mobility["minimum_departure_energy_gwh"]
        > ev_availability["fleet_energy_capacity_gwh"] + 1e-9
    ).any():
        raise ValueError("V4 EV minimum departure energy exceeds fleet energy capacity")
    if not np.allclose(
        ev_mobility["minimum_departure_energy_gwh"], 0.0, atol=1e-12
    ):
        raise ValueError(
            "Data-supported V4 forbids fabricated departure-SOC floors; "
            "minimum_departure_energy_gwh must be zero"
        )
    eta_charge = float(flexible["ev_v2g"]["charge_efficiency"])
    reference_grid_energy = flexible_ev_baseline.sum(axis=1)
    reconstructed_grid_energy = (
        ev_mobility["driving_energy_withdrawal_gwh"].sum(axis=1) / eta_charge
    )
    closure_fraction = np.divide(
        np.abs(reconstructed_grid_energy - reference_grid_energy),
        np.maximum(reference_grid_energy, 1e-9),
    )
    tolerance_fraction = float(
        flexible.get(
            f"{contract_version}_reference_energy_closure_tolerance_fraction",
            1e-6,
        )
    )
    if (closure_fraction > tolerance_fraction).any():
        raise ValueError(
            "V4 EV mobility withdrawals do not close to the immutable EV "
            f"baseline within {tolerance_fraction:g}"
        )

    base_service_columns = (
        "enablement_cost_yuan_per_kw_year",
        "activation_cost_yuan_per_mwh",
        "comfort_debt_cost_yuan_per_gwh_hour",
    )
    optional_service_columns = (
        "infrastructure_cost_yuan_per_kw_year",
        "degradation_cost_yuan_per_mwh",
    )
    service_columns = base_service_columns + optional_service_columns
    service_cost_raw = _read(str(files["enablement_cost_file"]))
    require_columns(
        service_cost_raw,
        ["province_code", "year", "service", *base_service_columns],
        f"{contract_label} service cost",
    )
    for column in optional_service_columns:
        if column not in service_cost_raw:
            service_cost_raw[column] = 0.0
    selected_cost = service_cost_raw.loc[
        service_cost_raw.year.eq(config.planning_year)
        & service_cost_raw.service.isin(["heating", "cooling", "ev_v1g", "ev_v2g"])
    ].copy()
    expected_cost_rows = len(province_order) * 4
    if len(selected_cost) != expected_cost_rows:
        raise ValueError(
            f"V4 service-cost rows={len(selected_cost)}; expected {expected_cost_rows}"
        )
    if selected_cost.duplicated(["province_code", "service"]).any():
        raise ValueError("Duplicate province-service rows in V4 service costs")
    service_costs: dict[str, dict[str, np.ndarray]] = {}
    for service in ("heating", "cooling", "ev_v1g", "ev_v2g"):
        subset = selected_cost.loc[selected_cost.service.eq(service)].set_index(
            "province_code"
        ).reindex(province_order)
        values = {
            column: subset[column].to_numpy(dtype=np.float64)
            for column in service_columns
        }
        if not np.isfinite(np.stack(tuple(values.values()))).all() or any(
            (value < 0.0).any() for value in values.values()
        ):
            raise ValueError(f"V4 {service} costs must be finite and nonnegative")
        service_costs[service] = values
    return FlexibleLoadV4Data(
        thermal_envelopes_gw=thermal_envelopes,
        thermal_availability=thermal_availability,
        thermal_parameters=thermal_parameters,
        ev_availability=ev_availability,
        ev_mobility=ev_mobility,
        service_costs=service_costs,
        contract_version=contract_version,
    )


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

    flexible_load_envelopes_gw: dict[str, np.ndarray] = {}
    flexible_load_v4: FlexibleLoadV4Data | None = None
    flexible_formulation = str(
        config.raw["flexible_load"].get("formulation", "daily_energy_shift_v1")
    )
    if (
        bool(config.raw["features"]["flexible_load"])
        and flexible_formulation == "comfort_envelope_v3"
    ):
        envelope_relative_path = str(
            config.raw["flexible_load"]["hourly_envelope_file"]
        )
        envelope_columns = {
            "heating_up": "heating_increase_limit_gw",
            "heating_down": "heating_reduction_limit_gw",
            "cooling_up": "cooling_increase_limit_gw",
            "cooling_down": "cooling_reduction_limit_gw",
        }
        envelope = _read(
            envelope_relative_path,
            usecols=[
                "province_code",
                "year",
                "hour_index",
                "heating_comfort_band_c",
                "cooling_comfort_band_c",
                *envelope_columns.values(),
            ],
        )
        envelope = envelope.loc[
            envelope.year.eq(config.planning_year)
        ].copy()
        if len(envelope) != expected_load_rows:
            raise ValueError(
                f"{config.planning_year} flexible-load envelope rows={len(envelope)}; "
                f"expected {expected_load_rows}"
            )
        if envelope.duplicated(["province_code", "hour_index"]).any():
            raise ValueError("Duplicate province-hour flexible-load envelope rows")
        expected_bands = {
            "heating_comfort_band_c": float(
                config.raw["flexible_load"]["heating"]["comfort_band_delta_c"]
            ),
            "cooling_comfort_band_c": float(
                config.raw["flexible_load"]["cooling"]["comfort_band_delta_c"]
            ),
        }
        for column, expected in expected_bands.items():
            values = envelope[column].to_numpy(dtype=np.float64)
            if not np.isfinite(values).all() or not np.allclose(
                values, expected, atol=1e-12, rtol=0.0
            ):
                raise ValueError(
                    f"{column} does not match configured value {expected}"
                )
        for name, column in envelope_columns.items():
            pivot = envelope.pivot(
                index="province_code", columns="hour_index", values=column
            )
            pivot = pivot.reindex(index=province_order, columns=range(config.hours))
            values = pivot.to_numpy(dtype=np.float64)
            if not np.isfinite(values).all() or (values < 0.0).any():
                raise ValueError(
                    f"{name} flexible-load envelope contains missing or negative values"
                )
            flexible_load_envelopes_gw[name] = values
        for component in ("heating", "cooling"):
            violation = (
                flexible_load_envelopes_gw[f"{component}_down"]
                - load_components_gw[component]
            )
            if float(violation.max()) > 1e-9:
                raise ValueError(
                    f"{component} reduction envelope exceeds baseline load by "
                    f"{float(violation.max()):.6g} GW"
                )
    if (
        bool(config.raw["features"]["flexible_load"])
        and flexible_formulation
        in {"service_constrained_v4", "integrated_service_constrained_v5"}
    ):
        flexible_load_v4 = _load_flexible_load_v4_data(
            config,
            provinces=provinces,
            load_components_gw=load_components_gw,
            expected_rows=expected_load_rows,
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
    vre_sites, vre_existing_cohorts = _apply_existing_vre_cohort_floors(
        config, vre_sites
    )

    cf_index = _read(
        "vre/hourly_cf_index.csv",
        usecols=["technology", "year", "zarr_path"],
    )
    cf = CapacityFactorStore(
        cf_index,
        config.weather_year,
        config.weather_time_alignment,
    )
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
    hydro_config = config.raw["hydro"]
    hydro_aggregate_capacity = _read(
        str(hydro_config["provincial_aggregate_capacity_file"]),
        usecols=[
            "province_code",
            "province_name_en",
            "province_name_zh",
            "identified_station_capacity_gw",
            "non_additive_union_floor_gw",
            "harmonized_conventional_capacity_gw",
            "provincial_aggregate_capacity_gw",
            "station_technical_upper_gw",
            "harmonized_future_technical_upper_gw",
            "allocation_method",
            "aggregate_physical_scope",
        ],
    ).sort_values("province_code").reset_index(drop=True)
    if (
        len(hydro_aggregate_capacity) != len(provinces)
        or hydro_aggregate_capacity.duplicated("province_code").any()
        or set(hydro_aggregate_capacity.province_code) != set(province_order)
    ):
        raise ValueError(
            "Provincial aggregate hydropower capacity must cover all 31 provinces"
        )
    hydro_aggregate_capacity = (
        provinces.merge(
            hydro_aggregate_capacity,
            on=["province_code", "province_name_en", "province_name_zh"],
            how="left",
            validate="one_to_one",
        )
        .sort_values("province_code")
        .reset_index(drop=True)
    )
    aggregate_capacity = hydro_aggregate_capacity[
        "provincial_aggregate_capacity_gw"
    ].to_numpy(dtype=float)
    harmonized_capacity = hydro_aggregate_capacity[
        "harmonized_conventional_capacity_gw"
    ].to_numpy(dtype=float)
    if (
        not np.isfinite(aggregate_capacity).all()
        or (aggregate_capacity < -1e-9).any()
        or not np.isfinite(harmonized_capacity).all()
    ):
        raise ValueError("Provincial aggregate hydropower capacity is invalid")
    station_capacity_by_province = (
        hydro.groupby("province_code").existing_capacity_gw.sum()
        .reindex(province_order, fill_value=0.0)
        .to_numpy(dtype=float)
    )
    table_station_capacity = hydro_aggregate_capacity[
        "identified_station_capacity_gw"
    ].to_numpy(dtype=float)
    if not np.allclose(
        table_station_capacity,
        station_capacity_by_province,
        rtol=0.0,
        atol=1e-9,
    ):
        raise ValueError(
            "Provincial aggregate hydropower table does not match the station floor"
        )
    national_target = float(
        hydro_config["provincial_aggregate_national_conventional_target_gw"]
    )
    if (
        not np.isclose(harmonized_capacity.sum(), national_target, atol=1e-8)
        or not np.allclose(
            station_capacity_by_province + aggregate_capacity,
            harmonized_capacity,
            rtol=0.0,
            atol=1e-9,
        )
    ):
        raise ValueError(
            "Station plus provincial aggregate hydropower does not close to "
            f"{national_target:g} GW"
        )
    hydro_aggregate_profile = _read(
        str(hydro_config["provincial_aggregate_monthly_profile_file"]),
        usecols=[
            "province_code",
            "month",
            "availability_capacity_factor",
            "profile_source",
            "hydrology_year",
            "environmental_flow_method",
            "dispatch_treatment",
        ],
    )
    if (
        len(hydro_aggregate_profile) != len(provinces) * 12
        or hydro_aggregate_profile.duplicated(["province_code", "month"]).any()
        or set(hydro_aggregate_profile.province_code) != set(province_order)
        or set(hydro_aggregate_profile.month) != set(range(1, 13))
    ):
        raise ValueError(
            "Provincial aggregate hydropower profile requires 12 months for "
            "each of 31 provinces"
        )
    aggregate_profile_pivot = hydro_aggregate_profile.pivot(
        index="province_code",
        columns="month",
        values="availability_capacity_factor",
    ).reindex(index=province_order, columns=range(1, 13))
    aggregate_profile_values = aggregate_profile_pivot.to_numpy(dtype=float)
    if (
        not np.isfinite(aggregate_profile_values).all()
        or (aggregate_profile_values < 0.0).any()
        or (aggregate_profile_values > 1.0).any()
    ):
        raise ValueError(
            "Provincial aggregate hydropower availability factors must be in [0, 1]"
        )
    model_time = (
        load[["hour_index", "datetime_bj"]]
        .drop_duplicates("hour_index")
        .sort_values("hour_index")
    )
    if len(model_time) != config.hours:
        raise ValueError(
            "Provincial aggregate hydropower cannot resolve the model time axis"
        )
    model_month = pd.to_datetime(model_time.datetime_bj).dt.month.to_numpy(dtype=int)
    hydro_aggregate_availability_cf = aggregate_profile_values[:, model_month - 1]
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

    wave = load_wave_energy_data(config)

    return ModelData(
        provinces=provinces,
        load=load,
        load_gw=load_pivot.to_numpy(dtype=np.float64),
        load_components_gw=load_components_gw,
        flexible_load_envelopes_gw=flexible_load_envelopes_gw,
        flexible_load_v4=flexible_load_v4,
        vre_points=points,
        vre_sites=vre_sites,
        vre_existing_cohorts=vre_existing_cohorts,
        thermal_floor=thermal_floor,
        thermal_floor_all_years=thermal_floor_all_years,
        nuclear_floor=nuclear_floor,
        nuclear_upper=nuclear_upper,
        hydro_stations=hydro,
        hydro_aggregate_capacity=hydro_aggregate_capacity,
        hydro_aggregate_availability_cf=hydro_aggregate_availability_cf,
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
        technology_parameter_registry=load_technology_parameter_registry(),
        grid_connections=grid_connections,
        initial_spur=initial_spur,
        substations=substations,
        load_centers=load_centers,
        vre_load_center_routes=vre_load_center_routes,
        hydro_load_center_routes=hydro_load_center_routes,
        intra_load_center_edges=intra_load_center_edges,
        cf=cf,
        wave=wave,
        planning_state=planning_state,
    )
