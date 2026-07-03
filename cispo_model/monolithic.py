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

from .config import ModelConfig
from .data import STORAGE_TECHS, THERMAL_TECHS, VRE_TECHS, ModelData
from .hydro import HydroProfileReader
from .master import MasterArtifacts, build_master
from .timeblocks import TimeBlock


def _vector_sum(terms: list[Any], length: int):
    if not terms:
        return np.zeros(length, dtype=float)
    result = terms[0]
    for term in terms[1:]:
        result = result + term
    return result


def _attach_vre_availability(
    model: gp.Model,
    config: ModelConfig,
    data: ModelData,
    capacity: gp.MVar,
    generation: gp.MVar,
    province_index: dict[int, int],
    hours: int,
) -> gp.MVar:
    """Build exact site-CF-by-capacity expressions in bounded hour chunks."""
    available = model.addMVar(
        (len(province_index), len(VRE_TECHS), hours),
        lb=0.0,
        name="vre_available_gw",
    )
    technology_index = {technology: i for i, technology in enumerate(VRE_TECHS)}
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
                expressions.append(sparse.csr_matrix(coefficients) @ capacity[positions])
            model.addConstr(
                available[p, v, start:stop] == _vector_sum(expressions, stop - start),
                name=f"vre_availability_p{province_code}_{technology}_h{start}",
            )
    for p in range(len(province_index)):
        for v in range(len(VRE_TECHS)):
            if (p, v) not in present:
                available[p, v, :].UB = 0.0
    model.addConstr(generation <= available, name="vre_generation_availability")
    return available


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
    provinces = data.province_codes.tolist()
    p_index = artifacts.index["province_index"]
    k_index = artifacts.index["thermal_index"]
    s_index = artifacts.index["storage_index"]
    p_count = len(provinces)
    k_count = len(THERMAL_TECHS)
    s_count = len(STORAGE_TECHS)
    v_count = len(VRE_TECHS)
    load = data.load_gw[:, :hours]

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
    vre_available = _attach_vre_availability(
        model, config, data, vre_capacity, vre_generation, p_index, hours
    )

    # Continuous capacity-based RUC with a cyclic transition over the selected horizon.
    online = model.addMVar((p_count, k_count, hours), lb=0.0, name="online_capacity_gw")
    startup = model.addMVar((p_count, k_count, hours), lb=0.0, name="startup_capacity_gw")
    shutdown = model.addMVar((p_count, k_count, hours), lb=0.0, name="shutdown_capacity_gw")
    gross = model.addMVar((p_count, k_count, hours), lb=0.0, name="gross_generation_gw")
    ramp_up = model.addMVar((p_count, k_count, hours), lb=0.0, name="ramp_up_gw")
    ramp_down = model.addMVar((p_count, k_count, hours), lb=0.0, name="ramp_down_gw")
    model.addConstr(online <= thermal_capacity[:, :, None], name="online_capacity_limit")
    model.addConstr(startup <= thermal_capacity[:, :, None], name="startup_capacity_limit")
    model.addConstr(shutdown <= thermal_capacity[:, :, None], name="shutdown_capacity_limit")
    model.addConstr(
        online[:, :, 0] == online[:, :, -1] + startup[:, :, 0] - shutdown[:, :, 0],
        name="ruc_cyclic_first_hour",
    )
    model.addConstr(
        online[:, :, 1:] == online[:, :, :-1] + startup[:, :, 1:] - shutdown[:, :, 1:],
        name="ruc_hourly_transition",
    )
    ruc = data.ruc.set_index("technology").reindex(THERMAL_TECHS)
    pmin = ruc.pmin_fraction.to_numpy(dtype=float)
    pmax = ruc.pmax_fraction.to_numpy(dtype=float)
    loss = ruc.ccs_power_loss_fraction.to_numpy(dtype=float)
    ramp_fraction = ruc.ramp_fraction_per_h.to_numpy(dtype=float)
    model.addConstr(gross >= online * pmin[None, :, None], name="thermal_minimum_generation")
    model.addConstr(gross <= online * pmax[None, :, None], name="thermal_maximum_generation")
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
                ramp_up[:, k, t] >= gross[:, k, t] - gross[:, k, previous_t],
                name=f"ramp_up_{technology}_{t}",
            )
            model.addConstr(
                ramp_down[:, k, t] >= gross[:, k, previous_t] - gross[:, k, t],
                name=f"ramp_down_{technology}_{t}",
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
    rup_c = model.addMVar((p_count, s_count, hours), lb=0.0, name="storage_reserve_up_charge_gw")
    rdn_c = model.addMVar((p_count, s_count, hours), lb=0.0, name="storage_reserve_down_charge_gw")
    rup_d = model.addMVar((p_count, s_count, hours), lb=0.0, name="storage_reserve_up_discharge_gw")
    rdn_d = model.addMVar((p_count, s_count, hours), lb=0.0, name="storage_reserve_down_discharge_gw")
    storage_table = data.storage.set_index("technology").reindex(STORAGE_TECHS)
    eta_c = storage_table.charge_efficiency.to_numpy(dtype=float)
    eta_d = storage_table.discharge_efficiency.to_numpy(dtype=float)
    duration = storage_table.duration_h.to_numpy(dtype=float)
    self_discharge = 1.0 - (
        1.0 - storage_table.self_discharge_fraction_per_day.to_numpy(dtype=float)
    ) ** (1.0 / 24.0)
    model.addConstr(charge <= storage_capacity[:, :, None], name="storage_charge_power")
    model.addConstr(discharge <= storage_capacity[:, :, None], name="storage_discharge_power")
    model.addConstr(soc <= storage_capacity[:, :, None] * duration[None, :, None], name="storage_energy")
    model.addConstr(
        soc[:, :, 0]
        == (1.0 - self_discharge[None, :]) * soc[:, :, -1]
        + eta_c[None, :] * charge[:, :, 0] - discharge[:, :, 0] / eta_d[None, :],
        name="storage_cyclic_first_hour",
    )
    model.addConstr(
        soc[:, :, 1:]
        == (1.0 - self_discharge[None, :, None]) * soc[:, :, :-1]
        + eta_c[None, :, None] * charge[:, :, 1:]
        - discharge[:, :, 1:] / eta_d[None, :, None],
        name="storage_hourly_transition",
    )
    model.addConstr(charge + rdn_c <= storage_capacity[:, :, None], name="storage_s4_41")
    model.addConstr((charge[:, :, 0] + rdn_c[:, :, 0]) * eta_c[None, :]
                    <= storage_capacity * duration[None, :] - soc[:, :, -1], name="storage_s4_42_first")
    model.addConstr((charge[:, :, 1:] + rdn_c[:, :, 1:]) * eta_c[None, :, None]
                    <= storage_capacity[:, :, None] * duration[None, :, None] - soc[:, :, :-1], name="storage_s4_42")
    model.addConstr(rup_c <= charge, name="storage_s4_43")
    model.addConstr(discharge + rup_d <= storage_capacity[:, :, None] * eta_d[None, :, None], name="storage_s4_44")
    model.addConstr(discharge[:, :, 0] + rup_d[:, :, 0] <= soc[:, :, -1] * eta_d[None, :], name="storage_s4_45_first")
    model.addConstr(discharge[:, :, 1:] + rup_d[:, :, 1:] <= soc[:, :, :-1] * eta_d[None, :, None], name="storage_s4_45")
    model.addConstr(rdn_d <= discharge, name="storage_s4_46")
    model.addConstr(rup_c + rup_d <= storage_capacity[:, :, None] * eta_d[None, :, None], name="storage_s4_47")

    # Hydro coefficients preserve station-level investment decisions.
    with HydroProfileReader(config, data) as hydro_reader:
        hydro = hydro_reader.read_linear_block(block)
    ror_available = model.addMVar((p_count, hours), lb=0.0, name="ror_available_gw")
    ror_generation = model.addMVar((p_count, hours), lb=0.0, name="ror_generation_gw")
    reservoir_capacity = model.addMVar(p_count, lb=0.0, name="reservoir_capacity_gw")
    reservoir_generation = model.addMVar((p_count, hours), lb=0.0, name="reservoir_generation_gw")
    reservoir_soc = model.addMVar((p_count, hours), lb=0.0, name="reservoir_energy_gwh")
    reservoir_spill = model.addMVar((p_count, hours), lb=0.0, name="reservoir_spill_gw")
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
        reservoir_rows = hydro.reservoir_station_rows[p]
        if len(reservoir_rows):
            model.addConstr(
                reservoir_capacity[p] == hydro_capacity[reservoir_rows].sum(),
                name=f"reservoir_capacity_p{provinces[p]}",
            )
        else:
            reservoir_capacity[p].UB = 0.0
    model.addConstr(ror_generation <= ror_available, name="ror_generation_availability")
    model.addConstr(reservoir_generation <= reservoir_capacity[:, None], name="reservoir_power")
    model.addConstr(reservoir_soc <= hydro.reservoir_energy_upper_gwh[:, None], name="reservoir_energy")
    model.addConstr(
        reservoir_soc[:, 0] == reservoir_soc[:, -1] + hydro.reservoir_inflow_gwh[:, 0]
        - reservoir_generation[:, 0] - reservoir_spill[:, 0],
        name="reservoir_cyclic_first_hour",
    )
    model.addConstr(
        reservoir_soc[:, 1:] == reservoir_soc[:, :-1] + hydro.reservoir_inflow_gwh[:, 1:]
        - reservoir_generation[:, 1:] - reservoir_spill[:, 1:],
        name="reservoir_hourly_transition",
    )

    # Directed transport with receiving-end losses and shared bidirectional capacity.
    edge_count = len(data.lines)
    flow_forward = model.addMVar((edge_count, hours), lb=0.0, name="flow_forward_gw")
    flow_reverse = model.addMVar((edge_count, hours), lb=0.0, name="flow_reverse_gw")
    model.addConstr(flow_forward + flow_reverse <= line_capacity[:, None], name="line_capacity_hourly")
    forward_incidence, reverse_incidence, line_efficiency = _network_incidence(data, p_index)
    network_injection = forward_incidence @ flow_forward + reverse_incidence @ flow_reverse

    actual_thermal = gross * (1.0 - loss[None, :, None])
    dac_power = data.dac.set_index("technology").reindex(
        list(artifacts.index["dac_index"])
    ).average_power_gw_per_mtco2_per_year.to_numpy(dtype=float)
    dac_load = dac_capture @ dac_power
    province_emissions: list[gp.LinExpr] = []
    for p in range(p_count):
        model.addConstr(
            vre_generation[p].sum(axis=0) + actual_thermal[p].sum(axis=0)
            + ror_generation[p] + reservoir_generation[p]
            + discharge[p].sum(axis=0) - charge[p].sum(axis=0)
            + network_injection[p]
            == load[p] + dac_load[p],
            name=f"strict_power_balance_p{provinces[p]}",
        )

    security = config.raw["security"]
    thermal_up = (
        (pmax[None, :, None] * online - gross) * (1.0 - loss[None, :, None])
    ).sum(axis=1)
    thermal_down = (
        (gross - pmin[None, :, None] * online) * (1.0 - loss[None, :, None])
    ).sum(axis=1)
    vre_up = (vre_available - vre_generation).sum(axis=1)
    hydro_up = reservoir_capacity[:, None] - reservoir_generation + ror_available - ror_generation
    storage_up = rup_c.sum(axis=1) + rup_d.sum(axis=1)
    storage_down = rdn_c.sum(axis=1) + rdn_d.sum(axis=1)
    vre_dispatch = vre_generation.sum(axis=1)
    model.addConstr(
        thermal_up + vre_up + hydro_up + storage_up
        >= float(security["up_reserve_load_fraction"]) * load
        + float(security["up_reserve_vre_fraction"]) * vre_dispatch,
        name="up_reserve",
    )
    model.addConstr(
        thermal_down + ror_generation + reservoir_generation + storage_down
        >= float(security["down_reserve_load_fraction"]) * load
        + float(security["down_reserve_vre_fraction"]) * vre_dispatch,
        name="down_reserve",
    )
    inertia = ruc.inertia_s.to_numpy(dtype=float)
    non_sync = security["non_synchronous_inertia_seconds"]
    hydro_inertia = model.addMVar(p_count, lb=0.0, name="hydro_inertia_gw_s")
    for p in range(p_count):
        ror_rows = hydro.ror_station_rows[p]
        reservoir_rows = hydro.reservoir_station_rows[p]
        expression = gp.LinExpr()
        if len(ror_rows):
            expression += float(non_sync["ror"]) * hydro_capacity[ror_rows].sum()
        if len(reservoir_rows):
            expression += float(non_sync["reservoir"]) * hydro_capacity[reservoir_rows].sum()
        model.addConstr(hydro_inertia[p] == expression, name=f"hydro_inertia_p{provinces[p]}")
    storage_inertia = np.asarray([float(non_sync[t]) for t in STORAGE_TECHS])
    for p in range(p_count):
        model.addConstr(
            (online[p] * inertia[:, None]).sum(axis=0) + hydro_inertia[p]
            + storage_capacity[p] @ storage_inertia
            >= float(security["minimum_system_inertia_seconds"]) * load[p],
            name=f"inertia_p{provinces[p]}",
        )

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
            elif technology in {"bio", "bioccs"}:
                unit_fuel = 0.0
            else:
                value = fuel_table.loc[(province_code, technology), "fuel_cost_yuan_per_mwh"]
                unit_fuel = 0.0 if pd.isna(value) else float(value)
            fuel_cost += unit_fuel * 1e-3 * gross[p, k].sum()
            startup_cost += float(ruc.loc[technology, "startup_yuan_per_mw"]) * 1e-3 * startup[p, k].sum()
            startup_cost += float(ruc.loc[technology, "shutdown_yuan_per_mw"]) * 1e-3 * shutdown[p, k].sum()
            ramp_cost += float(config.raw["thermal"]["ramping_cost_yuan_per_mwh"]) * 1e-3 * (
                ramp_up[p, k].sum() + ramp_down[p, k].sum()
            )
    storage_vom = gp.LinExpr()
    for technology, s in s_index.items():
        storage_vom += float(storage_table.loc[technology, "variable_om_yuan_per_mwh"]) * 1e-3 * (
            charge[:, s, :].sum() + discharge[:, s, :].sum()
        )
    flow_cost = float(config.raw["network"]["flow_regularization_yuan_per_mwh"]) * 1e-3 * (
        flow_forward.sum() + flow_reverse.sum()
    )
    operating_costs = {
        "thermal_variable_om": thermal_vom,
        "fuel": fuel_cost,
        "startup_shutdown": startup_cost,
        "ramping": ramp_cost,
        "storage_variable_om": storage_vom,
        "transmission_flow_regularization": flow_cost,
    }
    model.addConstr(
        variables["operating_cost_account"][0] == gp.quicksum(operating_costs.values()),
        name="annual_operating_cost_accounting",
    )
    emission_table = data.emissions.set_index("technology")
    coal_factor = float(emission_table.loc["coal", "emission_factor_mtco2_per_gwh"])
    gas_factor = float(emission_table.loc["gas", "emission_factor_mtco2_per_gwh"])
    capture_fraction = float(emission_table.loc["coal", "ccs_capture_fraction"])
    bioccs_factor = float(emission_table.loc["bioccs", "emission_factor_mtco2_per_gwh"])
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
                emissions += bioccs_factor * generation
                captured += abs(bioccs_factor) * generation
            else:
                emissions += base_factor * generation
            if technology in {"bio", "bioccs"}:
                biomass_fuel_pj += fuel_load[k] / 1000.0 * generation
        model.addConstr(variables["annual_biomass"][0, p] == biomass_fuel_pj, name=f"annual_biomass_p{provinces[p]}")
        model.addConstr(variables["annual_captured"][0, p] == captured, name=f"annual_captured_p{provinces[p]}")
        province_emissions.append(emissions)
    model.addConstr(
        variables["annual_emissions"][0]
        == gp.quicksum(province_emissions),
        name="annual_emissions_accounting",
    )

    variables.update(
        vre_generation=vre_generation, vre_available=vre_available,
        online=online, startup=startup, shutdown=shutdown,
        thermal_gross_generation=gross, ramp_up=ramp_up, ramp_down=ramp_down,
        storage_charge=charge, storage_discharge=discharge, storage_soc=soc,
        storage_reserve_up_charge=rup_c, storage_reserve_down_charge=rdn_c,
        storage_reserve_up_discharge=rup_d, storage_reserve_down_discharge=rdn_d,
        ror_available=ror_available, ror_generation=ror_generation,
        reservoir_capacity=reservoir_capacity, reservoir_generation=reservoir_generation,
        reservoir_soc=reservoir_soc, reservoir_spill=reservoir_spill,
        flow_forward=flow_forward, flow_reverse=flow_reverse,
        hydro_inertia=hydro_inertia,
    )
    artifacts.cost_components.update({f"operating_{k}": v for k, v in operating_costs.items()})
    artifacts.index.update(
        optimization_block=block,
        line_efficiency=line_efficiency,
        architecture="full_year_monolithic_lp",
        optimization_hours=hours,
    )
    model.update()
    return artifacts
