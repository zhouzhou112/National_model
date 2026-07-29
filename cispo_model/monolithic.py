"""Single-model 2030 capacity expansion and chronological 8760-hour operation.

This module deliberately contains no decomposition, representative periods, or
time weights. Annual decisions and every hourly operational variable live in
one continuous Gurobi model.
"""
from __future__ import annotations

from typing import Any

import gurobipy as gp
import numpy as np
import pandas as pd
from gurobipy import GRB
from scipy import sparse

from .carbon_accounting import resolve_beccs_carbon_factors
from .config import ModelConfig, resolve_minimum_system_inertia_seconds
from .data import STORAGE_TECHS, THERMAL_TECHS, VRE_TECHS, ModelData
from .flexible_load import attach_flexible_load
from .hydro import HydroProfileReader
from .load_center import attach_annual_load_center_network
from .master import MasterArtifacts, build_master
from .timeblocks import TimeBlock


def _vector_sum(terms: list[Any], length: int):
    if not terms:
        return np.zeros(length, dtype=float)
    result = terms[0]
    for term in terms[1:]:
        result = result + term
    return result


def _validate_reduced_ruc_domain(ruc: pd.DataFrame) -> None:
    """Validate the assumptions that make four RUC upper bounds redundant.

    The reduced implementation retains S4-24, S4-25 and S4-29.  With
    nonnegative ``online``, ``startup`` and ``shutdown`` variables, positive
    minimum up/down times, and ``pmin <= pmax``, those rows imply the omitted
    S4-22 upper bounds and the generic S4-26 maximum-generation bound exactly.
    Keep this guard adjacent to the formulation so future parameter changes
    cannot silently invalidate the algebraic reduction.
    """
    required = ("pmin_fraction", "pmax_fraction", "min_up_h", "min_down_h")
    if ruc[list(required)].isna().any().any():
        raise ValueError("RUC reduction requires complete pmin/pmax and minimum-time parameters")
    if (ruc.pmin_fraction > ruc.pmax_fraction + 1e-12).any():
        raise ValueError("RUC reduction requires pmin_fraction <= pmax_fraction")
    if (ruc.min_up_h < 1).any() or (ruc.min_down_h < 1).any():
        raise ValueError("RUC reduction requires min_up_h and min_down_h >= 1")


def _attach_vre_availability(
    model: gp.Model,
    config: ModelConfig,
    data: ModelData,
    capacity: gp.MVar,
    generation: gp.MVar,
    province_index: dict[int, int],
    hours: int,
) -> tuple[gp.MVar, np.ndarray]:
    """Build exact site-CF availability once to preserve matrix sparsity."""
    available = model.addMVar(
        (len(province_index), len(VRE_TECHS), hours),
        lb=0.0,
        name="vre_available_gw",
    )
    technology_index = {technology: i for i, technology in enumerate(VRE_TECHS)}
    site_cf_hours = np.zeros(len(data.vre_sites), dtype=float)
    chunk = int(config.raw["construction"]["build_hour_chunk_size"])
    grouped = data.vre_sites.groupby(["province_code", "technology"], sort=False)
    present: set[tuple[int, int]] = set()
    for (province_code, technology), province_technology in grouped:
        p = province_index[int(province_code)]
        v = technology_index[str(technology)]
        present.add((p, v))
        for start in range(0, hours, chunk):
            stop = min(start + chunk, hours)
            expressions = []
            for source, source_rows in province_technology.groupby(
                "cf_source_technology", sort=False
            ):
                positions = source_rows.index.to_numpy(dtype=int)
                coefficients = data.cf.read(
                    str(source),
                    source_rows.cf_grid_id.to_numpy(dtype=np.int64),
                    start,
                    stop,
                )
                tolerance = float(config.raw["numerics"]["coefficient_zero_tolerance"])
                coefficients[np.abs(coefficients) < tolerance] = 0.0
                site_cf_hours[positions] += coefficients.sum(axis=0)
                expressions.append(sparse.csr_matrix(coefficients) @ capacity[positions])
            model.addConstr(
                available[p, v, start:stop]
                == _vector_sum(expressions, stop - start),
                name=f"vre_availability_p{province_code}_{technology}_h{start}",
            )
    for p in range(len(province_index)):
        for v in range(len(VRE_TECHS)):
            if (p, v) not in present:
                available[p, v, :].UB = 0.0
    model.addConstr(generation <= available, name="vre_generation_availability")
    if not np.isfinite(site_cf_hours).all() or (site_cf_hours < 0.0).any():
        raise ValueError("Invalid selected-horizon VRE full-load-hour coefficients")
    return available, site_cf_hours


def _attach_wave_generation(
    model: gp.Model,
    config: ModelConfig,
    data: ModelData,
    capacity: gp.MVar,
    province_index: dict[int, int],
    hours: int,
) -> tuple[gp.MVar, np.ndarray]:
    """Attach grid-CF wave dispatch without a duplicate availability MVar.

    Wave provides no upward reserve in the first implementation, so a direct
    dispatch upper bound preserves the exact feasible set while avoiding one
    province-hour auxiliary variable per hour.
    """
    if data.wave is None:
        raise ValueError("Wave generation requested without wave data")
    generation = model.addMVar(
        (len(province_index), hours), lb=0.0, name="wave_generation_gw"
    )
    site_cf_hours = np.zeros(len(data.wave.sites), dtype=float)
    chunk = int(config.raw["construction"]["build_hour_chunk_size"])
    tolerance = float(config.raw["numerics"]["coefficient_zero_tolerance"])
    present: set[int] = set()
    for province_code, group in data.wave.sites.groupby(
        "province_code", sort=False
    ):
        p = province_index[int(province_code)]
        present.add(p)
        positions = group.index.to_numpy(dtype=int)
        grid_ids = group.wave_source_grid_id.to_numpy(dtype=np.int64)
        for start in range(0, hours, chunk):
            stop = min(start + chunk, hours)
            coefficients = data.wave.cf.read(grid_ids, start, stop)
            coefficients[np.abs(coefficients) < tolerance] = 0.0
            site_cf_hours[positions] += coefficients.sum(axis=0)
            model.addConstr(
                generation[p, start:stop]
                <= sparse.csr_matrix(coefficients) @ capacity[positions],
                name=f"wave_availability_p{int(province_code)}_h{start}",
            )
    for p in range(len(province_index)):
        if p not in present:
            generation[p, :].UB = 0.0
    if not np.isfinite(site_cf_hours).all() or (site_cf_hours < 0.0).any():
        raise ValueError("Invalid selected-horizon wave full-load-hour coefficients")
    return generation, site_cf_hours


def _network_incidence(data: ModelData, province_index: dict[int, int]):
    edge_count = len(data.lines)
    forward = sparse.lil_matrix((len(province_index), edge_count), dtype=float)
    reverse = sparse.lil_matrix((len(province_index), edge_count), dtype=float)
    efficiency = np.power(1.0 - 3.2e-5, data.lines.distance_km.to_numpy(dtype=float))
    for edge, row in enumerate(data.lines.itertuples(index=False)):
        p_from = province_index[int(row.from_province_code)]
        p_to = province_index[int(row.to_province_code)]
        forward[p_from, edge] = -1.0
        forward[p_to, edge] = efficiency[edge]
        reverse[p_from, edge] = efficiency[edge]
        reverse[p_to, edge] = -1.0
    return forward.tocsr(), reverse.tocsr(), efficiency


def build_full_year_monolithic(
    config: ModelConfig,
    data: ModelData,
    *,
    compute_max_cf: bool = True,
    optimization_hours: int | None = None,
) -> MasterArtifacts:
    """Build one chronological LP over the selected number of leading hours."""
    if config.raw["construction"]["architecture"] != "full_year_monolithic_lp":
        raise ValueError("Refusing to build a non-monolithic production configuration")
    hours = config.hours if optimization_hours is None else int(optimization_hours)
    if hours <= 0 or hours > config.hours:
        raise ValueError("optimization_hours must be in [1, 8760]")
    block = TimeBlock(block_id=0, hour_start=0, hour_stop=hours)
    artifacts = build_master(config, data, [block], compute_max_cf=compute_max_cf)
    model = artifacts.model
    variables = artifacts.variables
    constraint_handles = artifacts.index["constraint_handles"]
    provinces = data.province_codes.tolist()
    p_index = artifacts.index["province_index"]
    k_index = artifacts.index["thermal_index"]
    s_index = artifacts.index["storage_index"]
    p_count = len(provinces)
    k_count = len(THERMAL_TECHS)
    s_count = len(STORAGE_TECHS)
    v_count = len(VRE_TECHS)
    baseline_load = data.load_gw[:, :hours]
    flexible_load = attach_flexible_load(model, config, data, hours=hours)
    load = flexible_load.effective_load_gw

    vre_capacity = variables["vre_capacity"]
    thermal_capacity = variables["thermal_capacity"]
    storage_capacity = variables["storage_capacity"]
    hydro_capacity = variables["hydro_capacity"]
    line_capacity = variables["line_capacity"]
    dac_capture = variables["dac_capture"]

    # VRE generation and exact 0.25-degree hourly availability.
    vre_generation = model.addMVar(
        (p_count, v_count, hours), lb=0.0, name="vre_generation_gw"
    )
    vre_available, vre_site_cf_hours = _attach_vre_availability(
        model, config, data, vre_capacity, vre_generation, p_index, hours
    )
    if data.wave is not None:
        wave_generation, wave_site_cf_hours = _attach_wave_generation(
            model,
            config,
            data,
            variables["wave_capacity"],
            p_index,
            hours,
        )
    else:
        wave_generation = np.zeros((p_count, hours), dtype=float)
        wave_site_cf_hours = np.asarray([], dtype=float)

    # Continuous capacity-based RUC with a cyclic transition over the selected horizon.
    online = model.addMVar((p_count, k_count, hours), lb=0.0, name="online_capacity_gw")
    startup = model.addMVar((p_count, k_count, hours), lb=0.0, name="startup_capacity_gw")
    shutdown = model.addMVar((p_count, k_count, hours), lb=0.0, name="shutdown_capacity_gw")
    gross = model.addMVar((p_count, k_count, hours), lb=0.0, name="gross_generation_gw")
    ramp_magnitude = model.addMVar(
        (p_count, k_count, hours), lb=0.0, name="ramp_magnitude_gw"
    )
    model.addConstr(
        online[:, :, 0] == online[:, :, -1] + startup[:, :, 0] - shutdown[:, :, 0],
        name="ruc_cyclic_first_hour",
    )
    model.addConstr(
        online[:, :, 1:] == online[:, :, :-1] + startup[:, :, 1:] - shutdown[:, :, 1:],
        name="ruc_hourly_transition",
    )
    ruc = data.ruc.set_index("technology").reindex(THERMAL_TECHS)
    _validate_reduced_ruc_domain(ruc)
    pmin = ruc.pmin_fraction.to_numpy(dtype=float)
    pmax = ruc.pmax_fraction.to_numpy(dtype=float)
    loss = ruc.ccs_power_loss_fraction.to_numpy(dtype=float)
    ramp_fraction = ruc.ramp_fraction_per_h.to_numpy(dtype=float)

    # Exact row reduction, not a scientific relaxation:
    # - S4-24 at t gives online_t <= capacity.  At t-1 it gives
    #   startup_t <= capacity because online_(t-1) and every shutdown term are
    #   nonnegative.
    # - S4-25 at t-1 gives shutdown_t <= online_(t-1), which combines with
    #   S4-24 to give shutdown_t <= capacity.
    # - S4-29 is pmax*online - (pmax-pmin)*(startup+next_shutdown), hence it
    #   is no weaker than gross <= pmax*online when pmin <= pmax.
    # Therefore do not instantiate duplicate S4-22 upper rows or the generic
    # S4-26 maximum-generation row.  The lower generation bound remains.
    model.addConstr(gross >= online * pmin[None, :, None], name="thermal_minimum_generation")
    for technology, k in k_index.items():
        up_time = int(ruc.loc[technology, "min_up_h"])
        down_time = int(ruc.loc[technology, "min_down_h"])
        for t in range(hours):
            next_t = (t + 1) % hours
            stop_terms = [shutdown[:, k, (t - offset) % hours] for offset in range(up_time - 1)]
            start_terms = [startup[:, k, (t - offset) % hours] for offset in range(down_time - 1)]
            model.addConstr(
                online[:, k, t]
                <= thermal_capacity[:, k] - startup[:, k, next_t]
                - _vector_sum(stop_terms, p_count),
                name=f"ruc_s4_24_{technology}_{t}",
            )
            model.addConstr(
                online[:, k, t]
                >= shutdown[:, k, next_t] + _vector_sum(start_terms, p_count),
                name=f"ruc_s4_25_{technology}_{t}",
            )
            model.addConstr(
                gross[:, k, t]
                <= pmax[k] * (online[:, k, t] - startup[:, k, t] - shutdown[:, k, next_t])
                + pmin[k] * (startup[:, k, t] + shutdown[:, k, next_t]),
                name=f"ruc_s4_29_{technology}_{t}",
            )
            previous_t = (t - 1) % hours
            model.addConstr(
                gross[:, k, t] - gross[:, k, previous_t]
                <= ramp_fraction[k]
                * (online[:, k, t] - startup[:, k, t] - shutdown[:, k, next_t])
                + pmax[k] * (startup[:, k, t] - shutdown[:, k, t]),
                name=f"ruc_s4_27_{technology}_{t}",
            )
            model.addConstr(
                gross[:, k, previous_t] - gross[:, k, t]
                <= ramp_fraction[k]
                * (online[:, k, t] - startup[:, k, t] - startup[:, k, previous_t])
                - pmin[k] * (startup[:, k, t] - shutdown[:, k, t]),
                name=f"ruc_s4_28_{technology}_{t}",
            )
            model.addConstr(
                ramp_magnitude[:, k, t]
                >= gross[:, k, t] - gross[:, k, previous_t],
                name=f"ramp_absolute_up_{technology}_{t}",
            )
            model.addConstr(
                ramp_magnitude[:, k, t]
                >= gross[:, k, previous_t] - gross[:, k, t],
                name=f"ramp_absolute_down_{technology}_{t}",
            )

    dispatch_allowed = data.fuel.pivot(
        index="province_code", columns="technology", values="dispatch_allowed"
    )
    for technology in THERMAL_TECHS[:-1]:
        if technology in dispatch_allowed.columns:
            allowed = dispatch_allowed[technology].reindex(provinces).fillna(False).astype(bool)
            disabled = np.flatnonzero(~allowed.to_numpy())
            if len(disabled):
                gross[disabled, k_index[technology], :].UB = 0.0
                online[disabled, k_index[technology], :].UB = 0.0
    dates = (
        data.load[["hour_index", "datetime_bj"]]
        .drop_duplicates("hour_index")
        .sort_values("hour_index")
    )
    winter = np.flatnonzero(
        np.isin(
            pd.to_datetime(dates.datetime_bj).dt.month.to_numpy()[:hours],
            config.raw["thermal"]["chp_winter_months"],
        )
    )
    for technology in ("cchp", "cchpccs", "gchp", "gchpccs"):
        model.addConstr(
            online[:, k_index[technology], winter] == thermal_capacity[:, k_index[technology], None],
            name=f"chp_winter_{technology}",
        )
    for technology in ("bio", "bioccs"):
        model.addConstr(
            online[:, k_index[technology], :]
            >= float(config.raw["thermal"]["biomass_minimum_online_fraction"])
            * thermal_capacity[:, k_index[technology], None],
            name=f"biomass_minimum_online_{technology}",
        )

    # Storage: exact cyclic SOC and reserve feasibility, without weekly resets.
    charge = model.addMVar((p_count, s_count, hours), lb=0.0, name="storage_charge_gw")
    discharge = model.addMVar((p_count, s_count, hours), lb=0.0, name="storage_discharge_gw")
    soc = model.addMVar((p_count, s_count, hours), lb=0.0, name="storage_soc_gwh")
    storage_up = model.addMVar(
        (p_count, s_count, hours), lb=0.0, name="storage_reserve_up_gw"
    )
    storage_down = model.addMVar(
        (p_count, s_count, hours), lb=0.0, name="storage_reserve_down_gw"
    )
    storage_table = data.storage.set_index("technology").reindex(STORAGE_TECHS)
    eta_c = storage_table.charge_efficiency.to_numpy(dtype=float)
    eta_d = storage_table.discharge_efficiency.to_numpy(dtype=float)
    duration = storage_table.duration_h.to_numpy(dtype=float)
    self_discharge = 1.0 - (
        1.0 - storage_table.self_discharge_fraction_per_day.to_numpy(dtype=float)
    ) ** (1.0 / 24.0)
    model.addConstr(charge <= storage_capacity[:, :, None], name="storage_charge_power")
    model.addConstr(discharge <= storage_capacity[:, :, None], name="storage_discharge_power")
    phs_energy_mode = artifacts.index["phs_energy_capacity_mode"]
    battery_index = s_index["battery"]
    phs_index = s_index["phs"]
    model.addConstr(
        soc[:, battery_index, :]
        <= storage_capacity[:, battery_index, None]
        * duration[battery_index],
        name="battery_storage_energy",
    )
    if phs_energy_mode == "independent_power_energy_v1":
        phs_energy_capacity = variables["phs_energy_capacity"]
        model.addConstr(
            soc[:, phs_index, :] <= phs_energy_capacity[:, None],
            name="phs_storage_energy",
        )
    else:
        phs_energy_capacity = (
            storage_capacity[:, phs_index] * duration[phs_index]
        )
        model.addConstr(
            soc[:, phs_index, :]
            <= storage_capacity[:, phs_index, None] * duration[phs_index],
            name="phs_storage_energy",
        )
    model.addConstr(
        soc[:, :, 0]
        == (1.0 - self_discharge[None, :]) * soc[:, :, -1]
        + eta_c[None, :] * charge[:, :, 0] - discharge[:, :, 0] / eta_d[None, :],
        name="storage_cyclic_first_hour",
    )
    if hours > 1:
        model.addConstr(
            soc[:, :, 1:]
            == (1.0 - self_discharge[None, :, None]) * soc[:, :, :-1]
            + eta_c[None, :, None] * charge[:, :, 1:]
            - discharge[:, :, 1:] / eta_d[None, :, None],
            name="storage_hourly_transition",
        )
    # Exact projection of the four CISPO charge/discharge reserve components
    # onto aggregate up/down reserve. It preserves the feasible aggregate set
    # while removing two province-technology-hour variable arrays.
    discharge_headroom = (
        storage_capacity[:, :, None] * eta_d[None, :, None] - discharge
    )
    model.addConstr(
        storage_up <= charge + discharge_headroom,
        name="storage_projected_up_component_limits",
    )
    model.addConstr(
        storage_up <= storage_capacity[:, :, None] * eta_d[None, :, None],
        name="storage_projected_up_total_limit",
    )
    model.addConstr(
        storage_up[:, :, 0]
        <= charge[:, :, 0] + soc[:, :, -1] * eta_d[None, :]
        - discharge[:, :, 0],
        name="storage_projected_up_energy_first",
    )
    if hours > 1:
        model.addConstr(
            storage_up[:, :, 1:]
            <= charge[:, :, 1:] + soc[:, :, :-1] * eta_d[None, :, None]
            - discharge[:, :, 1:],
            name="storage_projected_up_energy",
        )
    model.addConstr(
        storage_down <= discharge + storage_capacity[:, :, None] - charge,
        name="storage_projected_down_power_limit",
    )
    model.addConstr(
        storage_down[:, battery_index, 0]
        <= discharge[:, battery_index, 0]
        + (
            storage_capacity[:, battery_index] * duration[battery_index]
            - soc[:, battery_index, -1]
        )
        / eta_c[battery_index]
        - charge[:, battery_index, 0],
        name="battery_projected_down_energy_first",
    )
    model.addConstr(
        storage_down[:, phs_index, 0]
        <= discharge[:, phs_index, 0]
        + (phs_energy_capacity - soc[:, phs_index, -1])
        / eta_c[phs_index]
        - charge[:, phs_index, 0],
        name="phs_projected_down_energy_first",
    )
    if hours > 1:
        model.addConstr(
            storage_down[:, battery_index, 1:]
            <= discharge[:, battery_index, 1:]
            + (
                storage_capacity[:, battery_index, None]
                * duration[battery_index]
                - soc[:, battery_index, :-1]
            )
            / eta_c[battery_index]
            - charge[:, battery_index, 1:],
            name="battery_projected_down_energy",
        )
        model.addConstr(
            storage_down[:, phs_index, 1:]
            <= discharge[:, phs_index, 1:]
            + (
                phs_energy_capacity[:, None]
                - soc[:, phs_index, :-1]
            )
            / eta_c[phs_index]
            - charge[:, phs_index, 1:],
            name="phs_projected_down_energy",
        )

    # Hydro coefficients preserve station-level investment decisions.
    with HydroProfileReader(config, data) as hydro_reader:
        hydro = hydro_reader.read_linear_block(block)
    hydro_aggregate_capacity = data.hydro_aggregate_capacity[
        "provincial_aggregate_capacity_gw"
    ].to_numpy(dtype=float)
    hydro_aggregate_available = (
        hydro_aggregate_capacity[:, None]
        * data.hydro_aggregate_availability_cf[:, :hours]
    )
    hydro_aggregate_mode = config.raw["hydro"]["provincial_aggregate_mode"]
    hydro_aggregate_upper = (
        hydro_aggregate_available
        if hydro_aggregate_mode == "fixed_existing_monthly_profile_v1"
        else np.broadcast_to(
            hydro_aggregate_capacity[:, None],
            (p_count, hours),
        )
    )
    hydro_aggregate_generation = model.addMVar(
        (p_count, hours),
        lb=0.0,
        ub=hydro_aggregate_upper,
        name="hydro_aggregate_generation_gw",
    )
    hydro_aggregate_month_slices: list[np.ndarray] = []
    if hydro_aggregate_mode == "fixed_existing_monthly_energy_budget_v2":
        selected_months = (
            pd.to_datetime(dates.datetime_bj)
            .dt.to_period("M")
            .astype(str)
            .to_numpy()[:hours]
        )
        for month in pd.unique(selected_months):
            month_hours = np.flatnonzero(selected_months == month)
            hydro_aggregate_month_slices.append(month_hours)
            model.addConstr(
                hydro_aggregate_generation[:, month_hours].sum(axis=1)
                <= hydro_aggregate_available[:, month_hours].sum(axis=1),
                name=f"hydro_aggregate_monthly_energy_budget_{month}",
            )
    ror_available = model.addMVar(
        (p_count, hours), lb=0.0, name="ror_available_gw"
    )
    ror_generation = model.addMVar((p_count, hours), lb=0.0, name="ror_generation_gw")
    reservoir_rows = hydro.reservoir_station_rows
    reservoir_count = len(reservoir_rows)
    hydro_constants = config.raw["hydro"]
    reservoir_flow_scale_m3s = float(
        hydro_constants["reservoir_flow_variable_scale_m3s"]
    )
    reservoir_volume_scale_m3 = float(
        hydro_constants["reservoir_volume_variable_scale_m3"]
    )
    flow_to_volume_scaled = (
        reservoir_flow_scale_m3s * 3600.0 / reservoir_volume_scale_m3
    )
    reservoir_turbine_flow = model.addMVar(
        (reservoir_count, hours),
        lb=0.0,
        name="reservoir_turbine_flow_1000m3s",
    )
    reservoir_spill_flow = model.addMVar(
        (reservoir_count, hours),
        lb=0.0,
        name="reservoir_spill_flow_1000m3s",
    )
    reservoir_volume = model.addMVar(
        (reservoir_count, hours),
        lb=0.0,
        name="reservoir_active_storage_million_m3",
    )
    conversion = hydro.reservoir_generation_conversion_gw_per_m3s
    scaled_flow_to_power = conversion * reservoir_flow_scale_m3s
    scaled_volume_to_energy = (
        conversion * reservoir_volume_scale_m3 / 3600.0
    )
    reservoir_soc = reservoir_volume * scaled_volume_to_energy[:, None]
    reservoir_spill = reservoir_spill_flow * scaled_flow_to_power[:, None]
    reservoir_generation = (
        reservoir_turbine_flow * scaled_flow_to_power[:, None]
    )
    reservoir_incidence = sparse.csr_matrix(
        (
            np.ones(reservoir_count, dtype=float),
            (
                hydro.reservoir_province_positions,
                np.arange(reservoir_count, dtype=np.int64),
            ),
        ),
        shape=(p_count, reservoir_count),
    )
    reservoir_capacity_by_province = (
        reservoir_incidence @ hydro_capacity[reservoir_rows]
    )
    reservoir_power_incidence = reservoir_incidence @ sparse.diags(
        scaled_flow_to_power
    )
    reservoir_generation_by_province = (
        reservoir_power_incidence @ reservoir_turbine_flow
    )
    chunk = int(config.raw["construction"]["build_hour_chunk_size"])
    for p in range(p_count):
        rows = hydro.ror_station_rows[p]
        if len(rows):
            for start in range(0, hours, chunk):
                stop = min(start + chunk, hours)
                model.addConstr(
                    ror_available[p, start:stop]
                    == sparse.csr_matrix(
                        np.where(
                            hydro.ror_capacity_factor[p][start:stop]
                            >= float(config.raw["numerics"]["coefficient_zero_tolerance"]),
                            hydro.ror_capacity_factor[p][start:stop],
                            0.0,
                        )
                    ) @ hydro_capacity[rows],
                    name=f"ror_availability_p{provinces[p]}_h{start}",
                )
        else:
            ror_available[p, :].UB = 0.0
    model.addConstr(
        ror_generation <= ror_available,
        name="ror_generation_availability",
    )
    model.addConstr(
        reservoir_generation <= hydro_capacity[reservoir_rows, None],
        name="reservoir_station_power",
    )
    model.addConstr(
        reservoir_volume
        <= hydro.reservoir_active_storage_m3[:, None] / reservoir_volume_scale_m3,
        name="reservoir_s4_12_active_storage",
    )
    cascade_rows = np.asarray(hydro.cascade_station_local_rows, dtype=np.int64)
    all_reservoir_local_rows = np.arange(reservoir_count, dtype=np.int64)
    independent_rows = np.setdiff1d(
        all_reservoir_local_rows, cascade_rows, assume_unique=True
    )
    if len(independent_rows):
        local = (
            hydro.reservoir_local_inflow_m3s[independent_rows]
            / reservoir_flow_scale_m3s
        )
        model.addConstr(
            reservoir_volume[independent_rows, 0]
            == reservoir_volume[independent_rows, -1]
            + (
                local[:, 0]
                - reservoir_turbine_flow[independent_rows, 0]
                - reservoir_spill_flow[independent_rows, 0]
            )
            * flow_to_volume_scaled,
            name="reservoir_independent_cyclic_first_hour",
        )
        if hours > 1:
            model.addConstr(
                reservoir_volume[independent_rows, 1:]
                == reservoir_volume[independent_rows, :-1]
                + (
                    local[:, 1:]
                    - reservoir_turbine_flow[independent_rows, 1:]
                    - reservoir_spill_flow[independent_rows, 1:]
                )
                * flow_to_volume_scaled,
                name="reservoir_independent_hourly_transition",
            )
    upstream_terms_by_target: dict[int, list[tuple[np.ndarray, float, int]]] = {
        int(row): [] for row in cascade_rows
    }
    for source_rows, target_rows, target_weights, lag in zip(
        hydro.cascade_edge_source_local_rows,
        hydro.cascade_edge_target_local_rows,
        hydro.cascade_edge_target_weights,
        hydro.cascade_edge_lag_h,
    ):
        for target_row, weight in zip(target_rows, target_weights):
            upstream_terms_by_target.setdefault(int(target_row), []).append(
                (source_rows, float(weight), int(lag))
            )
    for target_row in cascade_rows:
        terms = upstream_terms_by_target.get(int(target_row), [])
        for t in range(hours):
            previous_t = (t - 1) % hours
            upstream_release = gp.LinExpr()
            for source_rows, weight, lag in terms:
                source_t = (t - lag) % hours
                upstream_release += weight * (
                    reservoir_turbine_flow[source_rows, source_t].sum()
                    + reservoir_spill_flow[source_rows, source_t].sum()
                )
            model.addConstr(
                reservoir_volume[target_row, t]
                == reservoir_volume[target_row, previous_t]
                + (
                    float(hydro.reservoir_local_inflow_m3s[target_row, t])
                    / reservoir_flow_scale_m3s
                    + upstream_release
                    - reservoir_turbine_flow[target_row, t]
                    - reservoir_spill_flow[target_row, t]
                )
                * flow_to_volume_scaled,
                name=f"reservoir_cascade_s4_8_9_12_row{target_row}_h{t}",
            )

    # Directed transport with receiving-end losses. Reverse variables exist
    # only for AC corridors; DC corridors keep their committed direction and
    # therefore do not create fixed-zero reverse columns.
    edge_count = len(data.lines)
    flow_forward = model.addMVar((edge_count, hours), lb=0.0, name="flow_forward_gw")
    dc_edge_rows = np.flatnonzero(
        data.lines.preset_technology.astype(str).str.upper().eq("DC").to_numpy()
    )
    ac_edge_rows = np.flatnonzero(
        data.lines.preset_technology.astype(str).str.upper().eq("AC").to_numpy()
    )
    if len(ac_edge_rows) + len(dc_edge_rows) != edge_count:
        raise ValueError("Every interprovincial corridor must be classified as AC or DC")
    flow_reverse_ac = model.addMVar(
        (len(ac_edge_rows), hours), lb=0.0, name="flow_reverse_ac_gw"
    )
    if len(ac_edge_rows):
        constraint_handles["ac_line_shared_capacity_hourly"] = model.addConstr(
            flow_forward[ac_edge_rows, :] + flow_reverse_ac
            <= line_capacity[ac_edge_rows][:, None],
            name="ac_line_shared_capacity_hourly",
        )
    if len(dc_edge_rows):
        constraint_handles["dc_line_forward_capacity_hourly"] = model.addConstr(
            flow_forward[dc_edge_rows, :]
            <= line_capacity[dc_edge_rows][:, None],
            name="dc_line_forward_capacity_hourly",
        )
    forward_incidence, reverse_incidence, line_efficiency = _network_incidence(data, p_index)
    network_injection = (
        forward_incidence @ flow_forward
        + reverse_incidence[:, ac_edge_rows] @ flow_reverse_ac
    )

    actual_thermal = gross * (1.0 - loss[None, :, None])
    dac_power = data.dac.set_index("technology").reindex(
        list(artifacts.index["dac_index"])
    ).average_power_gw_per_mtco2_per_year.to_numpy(dtype=float)
    dac_load = dac_capture @ dac_power
    province_emissions: list[gp.LinExpr] = []
    power_balance_constraints = []
    for p in range(p_count):
        power_balance_constraints.append(model.addConstr(
            vre_generation[p].sum(axis=0) + wave_generation[p]
            + actual_thermal[p].sum(axis=0)
            + ror_generation[p] + reservoir_generation_by_province[p]
            + hydro_aggregate_generation[p]
            + discharge[p].sum(axis=0) - charge[p].sum(axis=0)
            + network_injection[p]
            == load[p] + dac_load[p],
            name=f"strict_power_balance_p{provinces[p]}",
        ))
    constraint_handles["strict_power_balance"] = power_balance_constraints

    if config.raw["features"]["annual_load_center_transmission"]:
        intra_load_center_flow_cost = attach_annual_load_center_network(
            model,
            config,
            data,
            artifacts,
            hours=hours,
            vre_site_cf_hours=vre_site_cf_hours,
            vre_generation=vre_generation,
            wave_site_cf_hours=wave_site_cf_hours,
            wave_generation=wave_generation,
            actual_thermal=actual_thermal,
            storage_charge=charge,
            storage_discharge=discharge,
            dac_load=dac_load,
            hydro_block=hydro,
            hydro_capacity=hydro_capacity,
            ror_generation=ror_generation,
            reservoir_generation=reservoir_generation,
            hydro_aggregate_generation=hydro_aggregate_generation,
            interprovincial_flow_forward=flow_forward,
            interprovincial_flow_reverse_ac=flow_reverse_ac,
            interprovincial_reverse_edge_rows=ac_edge_rows,
            interprovincial_efficiency=line_efficiency,
            effective_load=load,
        )
    else:
        intra_load_center_flow_cost = gp.LinExpr()

    security = config.raw["security"]
    thermal_up = (
        (pmax[None, :, None] * online - gross) * (1.0 - loss[None, :, None])
    ).sum(axis=1)
    thermal_down = (
        (gross - pmin[None, :, None] * online) * (1.0 - loss[None, :, None])
    ).sum(axis=1)
    vre_up = (vre_available - vre_generation).sum(axis=1)
    hydro_up = (
        reservoir_capacity_by_province[:, None]
        - reservoir_generation_by_province
        + ror_available
        - ror_generation
    )
    aggregate_up_credit = float(
        hydro_constants["provincial_aggregate_up_reserve_credit"]
    )
    aggregate_down_credit = float(
        hydro_constants["provincial_aggregate_down_reserve_credit"]
    )
    hydro_aggregate_up = aggregate_up_credit * (
        hydro_aggregate_capacity[:, None] - hydro_aggregate_generation
    )
    hydro_aggregate_down = (
        aggregate_down_credit * hydro_aggregate_generation
    )
    storage_up_by_province = storage_up.sum(axis=1)
    storage_down_by_province = storage_down.sum(axis=1)
    vre_dispatch = vre_generation.sum(axis=1)
    wave_reserve_requirement = (
        float(config.raw["wave_energy"]["reserve_requirement_fraction"])
        * wave_generation
        if data.wave is not None
        else 0.0
    )
    constraint_handles["up_reserve"] = model.addConstr(
        thermal_up + vre_up + hydro_up + hydro_aggregate_up
        + storage_up_by_province
        >= float(security["up_reserve_load_fraction"]) * load
        + float(security["up_reserve_vre_fraction"]) * vre_dispatch
        + wave_reserve_requirement,
        name="up_reserve",
    )
    constraint_handles["down_reserve"] = model.addConstr(
        thermal_down + ror_generation + reservoir_generation_by_province
        + hydro_aggregate_down
        + storage_down_by_province
        >= float(security["down_reserve_load_fraction"]) * load
        + float(security["down_reserve_vre_fraction"]) * vre_dispatch
        + wave_reserve_requirement,
        name="down_reserve",
    )
    inertia = ruc.inertia_s.to_numpy(dtype=float)
    non_sync = security["non_synchronous_inertia_seconds"]
    hydro_inertia = gp.MLinExpr.zeros(p_count)
    for p in range(p_count):
        ror_rows = hydro.ror_station_rows[p]
        reservoir_rows_p = hydro.reservoir_station_rows_by_province[p]
        expression = gp.LinExpr()
        if len(ror_rows):
            expression += float(non_sync["ror"]) * hydro_capacity[ror_rows].sum()
        if len(reservoir_rows_p):
            expression += float(non_sync["reservoir"]) * hydro_capacity[reservoir_rows_p].sum()
        expression += (
            float(hydro_constants["provincial_aggregate_inertia_seconds"])
            * hydro_aggregate_capacity[p]
        )
        hydro_inertia[p] = expression
    storage_inertia = np.asarray([float(non_sync[t]) for t in STORAGE_TECHS])
    minimum_inertia_seconds = resolve_minimum_system_inertia_seconds(security)
    inertia_constraints = []
    for p in range(p_count):
        inertia_constraints.append(model.addConstr(
            (online[p] * inertia[:, None]).sum(axis=0) + hydro_inertia[p]
            + storage_capacity[p] @ storage_inertia
            >= minimum_inertia_seconds * load[p],
            name=f"inertia_p{provinces[p]}",
        ))
    constraint_handles["inertia"] = inertia_constraints

    # Annual operating costs and exact carbon/biomass/CCS accounting.
    om = data.thermal_om.set_index("technology").reindex(THERMAL_TECHS)
    fuel_table = data.fuel.set_index(["province_code", "technology"])
    thermal_vom = gp.LinExpr()
    fuel_cost = gp.LinExpr()
    startup_cost = gp.LinExpr()
    ramp_cost = gp.LinExpr()
    for p, province_code in enumerate(provinces):
        for technology, k in k_index.items():
            thermal_vom += float(om.loc[technology, "variable_om_yuan_per_mwh"]) * 1e-3 * actual_thermal[p, k].sum()
            if technology == "nuclear":
                unit_fuel = float(config.raw["thermal"]["nuclear_fuel_yuan_per_mwh"])
            else:
                value = fuel_table.loc[(province_code, technology), "fuel_cost_yuan_per_mwh"]
                unit_fuel = 0.0 if pd.isna(value) else float(value)
            fuel_cost += unit_fuel * 1e-3 * gross[p, k].sum()
            startup_cost += float(ruc.loc[technology, "startup_yuan_per_mw"]) * 1e-3 * startup[p, k].sum()
            startup_cost += float(ruc.loc[technology, "shutdown_yuan_per_mw"]) * 1e-3 * shutdown[p, k].sum()
            ramp_cost += (
                float(config.raw["thermal"]["ramping_cost_yuan_per_mwh"])
                * 1e-3
                * ramp_magnitude[p, k].sum()
            )
    storage_vom = gp.LinExpr()
    for technology, s in s_index.items():
        storage_vom += float(storage_table.loc[technology, "variable_om_yuan_per_mwh"]) * 1e-3 * (
            charge[:, s, :].sum() + discharge[:, s, :].sum()
        )
    flow_cost = float(config.raw["network"]["flow_regularization_yuan_per_mwh"]) * 1e-3 * (
        flow_forward.sum() + flow_reverse_ac.sum()
    )
    operating_costs = {
        "thermal_variable_om": thermal_vom,
        "fuel": fuel_cost,
        "startup_shutdown": startup_cost,
        "ramping": ramp_cost,
        "storage_variable_om": storage_vom,
        "transmission_flow_regularization": flow_cost,
        "load_center_intra_flow_regularization": intra_load_center_flow_cost,
        **flexible_load.costs,
    }
    artifacts.cost_components["annual_operation"] = gp.quicksum(
        operating_costs.values()
    )
    emission_table = data.emissions.set_index("technology")
    coal_factor = float(emission_table.loc["coal", "emission_factor_mtco2_per_gwh"])
    gas_factor = float(emission_table.loc["gas", "emission_factor_mtco2_per_gwh"])
    capture_fraction = float(emission_table.loc["coal", "ccs_capture_fraction"])
    beccs_carbon = resolve_beccs_carbon_factors(emission_table)
    fuel_load = ruc.fuel_load_mj_per_kwh.to_numpy(dtype=float)
    for p in range(p_count):
        emissions = gp.LinExpr()
        captured = gp.LinExpr()
        biomass_fuel_pj = gp.LinExpr()
        for technology, k in k_index.items():
            generation = gross[p, k].sum()
            if technology.startswith("coal") or technology.startswith("cchp"):
                base_factor = coal_factor
            elif technology.startswith("gas") or technology.startswith("gchp"):
                base_factor = gas_factor
            else:
                base_factor = 0.0
            if technology.endswith("ccs") and technology != "bioccs":
                emissions += base_factor * (1.0 - capture_fraction) * generation
                captured += base_factor * capture_fraction * generation
            elif technology == "bioccs":
                emissions += beccs_carbon.net_emissions * generation
                captured += beccs_carbon.stored * generation
            else:
                emissions += base_factor * generation
            if technology in {"bio", "bioccs"}:
                biomass_fuel_pj += fuel_load[k] / 1000.0 * generation
        model.addConstr(variables["annual_biomass"][0, p] == biomass_fuel_pj, name=f"annual_biomass_p{provinces[p]}")
        model.addConstr(variables["annual_captured"][0, p] == captured, name=f"annual_captured_p{provinces[p]}")
        province_emissions.append(emissions)
    emissions_accounting = artifacts.index["annual_emissions_accounting"]
    if emissions_accounting == "province_hierarchical_v2":
        for p, province_code in enumerate(provinces):
            model.addConstr(
                variables["annual_emissions"][0, p] == province_emissions[p],
                name=f"annual_emissions_accounting_p{province_code}",
            )
    else:
        model.addConstr(
            variables["annual_emissions"][0]
            == gp.quicksum(province_emissions),
            name="annual_emissions_accounting",
        )

    variables.update(
        vre_generation=vre_generation, vre_available=vre_available,
        wave_generation=wave_generation,
        online=online, startup=startup, shutdown=shutdown,
        thermal_gross_generation=gross, actual_thermal_generation=actual_thermal,
        ramp_magnitude=ramp_magnitude,
        storage_charge=charge, storage_discharge=discharge, storage_soc=soc,
        storage_reserve_up_technology=storage_up,
        storage_reserve_down_technology=storage_down,
        ror_available=ror_available, ror_generation=ror_generation,
        hydro_aggregate_generation=hydro_aggregate_generation,
        reservoir_station_rows=reservoir_rows,
        reservoir_capacity_by_province=reservoir_capacity_by_province,
        reservoir_generation=reservoir_generation,
        reservoir_generation_by_province=reservoir_generation_by_province,
        reservoir_turbine_flow=reservoir_turbine_flow,
        reservoir_spill_flow=reservoir_spill_flow,
        reservoir_volume=reservoir_volume,
        reservoir_soc=reservoir_soc, reservoir_spill=reservoir_spill,
        flow_forward=flow_forward, flow_reverse_ac=flow_reverse_ac,
        network_injection=network_injection, dac_load=dac_load,
        thermal_reserve_up=thermal_up, thermal_reserve_down=thermal_down,
        vre_reserve_up=vre_up,
        hydro_reserve_up=hydro_up + hydro_aggregate_up,
        hydro_aggregate_reserve_up=hydro_aggregate_up,
        hydro_aggregate_reserve_down=hydro_aggregate_down,
        storage_reserve_up=storage_up_by_province,
        storage_reserve_down=storage_down_by_province,
        hydro_inertia=hydro_inertia,
        **flexible_load.variables,
    )
    artifacts.cost_components.update({f"operating_{k}": v for k, v in operating_costs.items()})
    model.setObjective(
        gp.quicksum(
            expression
            for name, expression in artifacts.cost_components.items()
            if not name.startswith("operating_")
        ),
        GRB.MINIMIZE,
    )
    artifacts.index.update(
        optimization_block=block,
        line_efficiency=line_efficiency,
        architecture="full_year_monolithic_lp",
        optimization_hours=hours,
        configured_hours=config.hours,
        selected_load_gw=load,
        baseline_load_gw=baseline_load,
        baseline_load_components_gw={
            name: values[:, :hours]
            for name, values in data.load_components_gw.items()
        },
        actual_load_components_gw=flexible_load.actual_components_gw,
        flexible_load_day_slices=flexible_load.day_slices,
        interprovincial_reverse_edge_rows=ac_edge_rows,
        reservoir_inflow_gwh=hydro.reservoir_inflow_gwh,
        reservoir_energy_upper_gwh=hydro.reservoir_energy_upper_gwh,
        reservoir_local_inflow_m3s=hydro.reservoir_local_inflow_m3s,
        reservoir_active_storage_m3=hydro.reservoir_active_storage_m3,
        reservoir_flow_scale_m3s=reservoir_flow_scale_m3s,
        reservoir_volume_scale_m3=reservoir_volume_scale_m3,
        reservoir_generation_conversion_gw_per_m3s=hydro.reservoir_generation_conversion_gw_per_m3s,
        hydro_aggregate_available_gw=hydro_aggregate_available,
        hydro_aggregate_power_upper_gw=hydro_aggregate_upper,
        hydro_aggregate_month_slices=hydro_aggregate_month_slices,
        cascade_station_local_rows=hydro.cascade_station_local_rows,
        cascade_edge_source_local_rows=hydro.cascade_edge_source_local_rows,
        cascade_edge_target_local_rows=hydro.cascade_edge_target_local_rows,
        cascade_edge_target_weights=hydro.cascade_edge_target_weights,
        cascade_edge_lag_h=hydro.cascade_edge_lag_h,
        cascade_edge_ids=hydro.cascade_edge_ids,
        cascade_isolated_node_ids=hydro.cascade_isolated_node_ids,
    )
    model.update()
    return artifacts
