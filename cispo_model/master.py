"""Annual capacity and accounting component of the monolithic model."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gurobipy as gp
import numpy as np
import pandas as pd
from gurobipy import GRB

from .config import ModelConfig, capital_recovery_factor
from .data import (
    DAC_TECHS,
    STORAGE_TECHS,
    THERMAL_TECHS,
    VRE_TECHS,
    ModelData,
    compute_vre_max_cf,
)
from .timeblocks import TimeBlock


@dataclass
class MasterArtifacts:
    model: gp.Model
    variables: dict[str, Any]
    cost_components: dict[str, gp.LinExpr]
    index: dict[str, Any]


def export_master_solution(
    artifacts: MasterArtifacts,
    data: ModelData,
    output_dir,
) -> None:
    """Export annual decisions and the lower-bound cost decomposition."""
    from pathlib import Path

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    variables = artifacts.variables
    vre = data.vre_sites[
        ["grid_uid", "grid_id", "province_code", "technology", "capacity_floor_gw", "capacity_upper_gw"]
    ].copy()
    vre["capacity_gw"] = variables["vre_capacity"].X
    vre["new_capacity_gw"] = variables["vre_new"].X
    vre.to_csv(output_dir / "vre_capacity.csv", index=False, encoding="utf-8-sig")

    thermal_rows = []
    capacity = variables["thermal_capacity"].X
    new_capacity = variables["thermal_new"].X
    for p, province_code in enumerate(artifacts.index["province_codes"]):
        for technology, k in artifacts.index["thermal_index"].items():
            thermal_rows.append(
                {
                    "province_code": province_code,
                    "technology": technology,
                    "capacity_gw": capacity[p, k],
                    "new_capacity_gw": new_capacity[p, k],
                }
            )
    pd.DataFrame(thermal_rows).to_csv(
        output_dir / "thermal_nuclear_capacity.csv", index=False, encoding="utf-8-sig"
    )

    storage_rows = []
    capacity = variables["storage_capacity"].X
    for p, province_code in enumerate(artifacts.index["province_codes"]):
        for technology, s in artifacts.index["storage_index"].items():
            storage_rows.append(
                {
                    "province_code": province_code,
                    "technology": technology,
                    "capacity_gw": capacity[p, s],
                }
            )
    pd.DataFrame(storage_rows).to_csv(
        output_dir / "storage_capacity.csv", index=False, encoding="utf-8-sig"
    )

    line = data.lines[
        ["line_id", "from_province_code", "to_province_code", "preset_technology", "distance_km"]
    ].copy()
    line["capacity_gw"] = variables["line_capacity"].X
    line["new_capacity_gw"] = variables["line_new"].X
    line.to_csv(output_dir / "transmission_capacity.csv", index=False, encoding="utf-8-sig")

    if "intra_load_center_capacity" in variables:
        intra = data.intra_load_center_edges[
            [
                "intra_edge_id", "province_code", "from_load_center_id",
                "to_load_center_id", "distance_km", "technology",
                "initial_capacity_gw", "unit_cost_yuan_per_kw",
            ]
        ].copy()
        intra["capacity_gw"] = variables["intra_load_center_capacity"].X
        intra["new_capacity_gw"] = variables["intra_load_center_new"].X
        if "intra_load_center_flow_forward" in variables:
            intra["annual_flow_forward_gwh"] = variables["intra_load_center_flow_forward"].X
            intra["annual_flow_reverse_gwh"] = variables["intra_load_center_flow_reverse"].X
        intra.to_csv(
            output_dir / "load_center_intra_transmission.csv",
            index=False,
            encoding="utf-8-sig",
        )

    if "load_center_annual_injection" in variables:
        centers = data.load_centers[
            [
                "load_center_id", "province_code", "province_name_zh", "lon", "lat",
                "annual_demand_share_in_province",
            ]
        ].copy()
        centers["annual_injection_gwh"] = variables["load_center_annual_injection"].X
        centers["annual_effective_demand_gwh"] = variables["load_center_annual_demand"].X
        centers["annual_external_export_gwh"] = variables["load_center_external_export"].X
        centers.to_csv(
            output_dir / "load_center_annual_balance.csv",
            index=False,
            encoding="utf-8-sig",
        )
        generation_rows = []
        vre_generation = variables["load_center_vre_generation"].X
        ror_generation = variables["load_center_ror_generation"].X
        reservoir_generation = variables["load_center_reservoir_generation"].X
        for center_position, center in data.load_centers.reset_index(drop=True).iterrows():
            for technology_position, technology in enumerate(VRE_TECHS):
                generation_rows.append(
                    {
                        "load_center_id": center.load_center_id,
                        "province_code": int(center.province_code),
                        "technology": technology,
                        "annual_generation_gwh": vre_generation[
                            center_position, technology_position
                        ],
                    }
                )
            for technology, values in (
                ("ror", ror_generation),
                ("reservoir", reservoir_generation),
            ):
                generation_rows.append(
                    {
                        "load_center_id": center.load_center_id,
                        "province_code": int(center.province_code),
                        "technology": technology,
                        "annual_generation_gwh": values[center_position],
                    }
                )
        pd.DataFrame(generation_rows).to_csv(
            output_dir / "load_center_annual_generation.csv",
            index=False,
            encoding="utf-8-sig",
        )
        province_accounts = data.provinces[["province_code", "province_name_zh"]].copy()
        province_accounts["annual_non_spatial_injection_gwh"] = variables[
            "province_annual_non_spatial_injection"
        ].X
        province_accounts["annual_effective_demand_gwh"] = variables[
            "province_annual_effective_demand"
        ].X
        province_accounts["annual_external_sent_gwh"] = variables[
            "province_annual_external_sent"
        ].X
        province_accounts.to_csv(
            output_dir / "province_annual_load_center_accounts.csv",
            index=False,
            encoding="utf-8-sig",
        )
        forward = variables["intra_load_center_flow_forward"].X
        reverse = variables["intra_load_center_flow_reverse"].X
        balance_residual = (
            variables["load_center_annual_injection"].X
            - variables["load_center_annual_demand"].X
            - variables["load_center_external_export"].X
        )
        center_index = artifacts.index["load_center_index"]
        for edge, row in enumerate(data.intra_load_center_edges.itertuples(index=False)):
            origin = center_index[str(row.from_load_center_id)]
            destination = center_index[str(row.to_load_center_id)]
            balance_residual[origin] -= forward[edge]
            balance_residual[destination] += forward[edge]
            balance_residual[destination] -= reverse[edge]
            balance_residual[origin] += reverse[edge]
        province_export_residual = []
        external_sent = variables["province_annual_external_sent"].X
        for p, province_code in enumerate(artifacts.index["province_codes"]):
            positions = data.load_centers.index[
                data.load_centers.province_code.eq(province_code)
            ].to_numpy(dtype=int)
            province_export_residual.append(
                variables["load_center_external_export"].X[positions].sum()
                - external_sent[p]
            )
        design_hours = float(artifacts.index["intra_load_center_design_hours"])
        capacity_residual = (
            forward + reverse
            - design_hours * variables["intra_load_center_capacity"].X
        )
        dpv_rows = data.vre_sites.technology.eq("dpv").to_numpy()
        dpv_spur_max = (
            float(variables["spur_augmentation"].X[dpv_rows].max())
            if dpv_rows.any() else 0.0
        )
        qc = {
            "maximum_center_balance_residual_gwh": float(np.abs(balance_residual).max()),
            "maximum_province_export_residual_gwh": float(
                np.abs(province_export_residual).max()
            ),
            "maximum_intra_capacity_violation_gwh": float(
                np.maximum(capacity_residual, 0.0).max()
            ),
            "bidirectional_active_edge_count": int(
                ((forward > 1e-7) & (reverse > 1e-7)).sum()
            ),
            "dpv_spur_augmentation_max_gw": dpv_spur_max,
        }
        pd.DataFrame([qc]).to_csv(
            output_dir / "load_center_network_qc.csv",
            index=False,
            encoding="utf-8-sig",
        )
        if (
            qc["maximum_center_balance_residual_gwh"] > 1e-5
            or qc["maximum_province_export_residual_gwh"] > 1e-5
            or qc["maximum_intra_capacity_violation_gwh"] > 1e-5
            or qc["dpv_spur_augmentation_max_gw"] > 1e-8
        ):
            raise RuntimeError(f"Load-center solution QC failed: {qc}")

    pd.DataFrame(
        [
            {"cost_component": name, "value_million_cny_per_year": expression.getValue()}
            for name, expression in artifacts.cost_components.items()
        ]
    ).to_csv(output_dir / "cost_components_lower_bound.csv", index=False, encoding="utf-8-sig")


def _technology_lookup(frame: pd.DataFrame, value_column: str) -> dict[str, float]:
    return frame.set_index("technology")[value_column].astype(float).to_dict()


def _haversine_matrix_km(
    origin_lon: np.ndarray,
    origin_lat: np.ndarray,
    destination_lon: np.ndarray,
    destination_lat: np.ndarray,
) -> np.ndarray:
    lon1 = np.radians(origin_lon)[:, None]
    lat1 = np.radians(origin_lat)[:, None]
    lon2 = np.radians(destination_lon)[None, :]
    lat2 = np.radians(destination_lat)[None, :]
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    return 6371.0088 * 2.0 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def build_master(
    config: ModelConfig,
    data: ModelData,
    blocks: list[TimeBlock],
    *,
    compute_max_cf: bool = True,
) -> MasterArtifacts:
    model = gp.Model(f"CISPO_{config.planning_year}_master")
    provinces = data.province_codes.tolist()
    p_index = {code: i for i, code in enumerate(provinces)}
    k_index = {tech: i for i, tech in enumerate(THERMAL_TECHS)}
    s_index = {tech: i for i, tech in enumerate(STORAGE_TECHS)}
    d_index = {tech: i for i, tech in enumerate(DAC_TECHS)}
    b_count = len(blocks)
    p_count = len(provinces)

    variables: dict[str, Any] = {}
    costs: dict[str, gp.LinExpr] = {}
    wacc = float(config.raw["finance"]["real_wacc_fraction"])
    lifetimes = config.raw["finance"]["default_lifetime_years"]

    # VRE site capacity remains at 0.25-degree resolution.
    site_floor = data.vre_sites.capacity_floor_gw.to_numpy(dtype=float)
    site_upper = data.vre_sites.capacity_upper_gw.to_numpy(dtype=float)
    vre_new = model.addMVar(len(data.vre_sites), lb=0.0, name="vre_new_gw")
    vre_cap = model.addMVar(len(data.vre_sites), lb=site_floor, ub=site_upper, name="vre_capacity_gw")
    model.addConstr(vre_cap == site_floor + vre_new, name="vre_capacity_accounting")
    variables.update(vre_new=vre_new, vre_capacity=vre_cap)

    capex_2030 = _technology_lookup(data.capex, "capex_yuan_per_kw")
    vre_fom_fraction = {
        "onwind": 0.015, "offwind": 0.015, "upv": 0.005, "dpv": 0.005
    }
    vre_investment = gp.LinExpr()
    vre_fom = gp.LinExpr()
    for technology, group in data.vre_sites.groupby("technology"):
        positions = group.index.to_numpy(dtype=int)
        crf = capital_recovery_factor(wacc, float(lifetimes[technology]))
        capex = float(capex_2030[technology])
        vre_investment += capex * crf * vre_new[positions].sum()
        vre_fom += capex * vre_fom_fraction[technology] * vre_cap[positions].sum()
    costs["vre_investment"] = vre_investment
    costs["vre_fixed_om"] = vre_fom

    # Thermal and nuclear capacity in GW. Continuous RUC makes explicit unit
    # counts unnecessary; all unit-based equations are scaled by capacity.
    floor_table = data.thermal_floor.pivot(index="province_code", columns="technology", values="capacity_floor_gw")
    floor_table = floor_table.reindex(index=provinces, columns=THERMAL_TECHS[:-1], fill_value=0.0)
    nuclear = data.nuclear_floor.set_index("province_code").capacity_floor_gw.reindex(provinces).fillna(0.0)
    thermal_floor = np.column_stack([floor_table.to_numpy(dtype=float), nuclear.to_numpy(dtype=float)])
    thermal_new = model.addMVar((p_count, len(THERMAL_TECHS)), lb=0.0, name="thermal_new_gw")
    thermal_cap = model.addMVar((p_count, len(THERMAL_TECHS)), lb=thermal_floor, name="thermal_capacity_gw")
    model.addConstr(thermal_cap == thermal_floor + thermal_new, name="thermal_capacity_accounting")
    variables.update(thermal_new=thermal_new, thermal_capacity=thermal_cap)

    fuel_allowed = data.fuel.pivot(index="province_code", columns="technology", values="new_capacity_allowed")
    for technology in THERMAL_TECHS[:-1]:
        k = k_index[technology]
        if technology in fuel_allowed.columns:
            disabled = ~fuel_allowed[technology].reindex(provinces).fillna(False).astype(bool).to_numpy()
            for p in np.flatnonzero(disabled):
                thermal_new[p, k].UB = 0.0
    for non_ccs, ccs in (("cchp", "cchpccs"), ("gchp", "gchpccs")):
        pair = [k_index[non_ccs], k_index[ccs]]
        model.addConstr(
            thermal_cap[:, pair].sum(axis=1) == thermal_floor[:, pair].sum(axis=1),
            name=f"fixed_chp_pair_{non_ccs}",
        )

    om = data.thermal_om.set_index("technology")
    thermal_investment = gp.LinExpr()
    thermal_fom = gp.LinExpr()
    for technology in THERMAL_TECHS:
        k = k_index[technology]
        crf = capital_recovery_factor(wacc, float(lifetimes[technology]))
        capex = float(capex_2030[technology])
        thermal_investment += capex * crf * thermal_new[:, k].sum()
        thermal_fom += capex * float(om.loc[technology, "fixed_om_fraction_capex_per_year"]) * thermal_cap[:, k].sum()
    costs["thermal_nuclear_investment"] = thermal_investment
    costs["thermal_nuclear_fixed_om"] = thermal_fom

    # Hydropower station capacity is retained at station resolution.
    hydro_floor = data.hydro_stations.existing_capacity_gw.to_numpy(dtype=float)
    hydro_upper = data.hydro_stations.capacity_potential_gw.to_numpy(dtype=float)
    hydro_new = model.addMVar(len(data.hydro_stations), lb=0.0, name="hydro_new_gw")
    hydro_cap = model.addMVar(len(data.hydro_stations), lb=hydro_floor, ub=hydro_upper, name="hydro_capacity_gw")
    model.addConstr(hydro_cap == hydro_floor + hydro_new, name="hydro_capacity_accounting")
    variables.update(hydro_new=hydro_new, hydro_capacity=hydro_cap)
    hydro_capex = float(capex_2030["hydro"])
    hydro_crf = capital_recovery_factor(wacc, float(lifetimes["hydro"]))
    costs["hydro_investment"] = hydro_capex * hydro_crf * hydro_new.sum()
    costs["hydro_fixed_om"] = hydro_capex * 0.02 * hydro_cap.sum()

    # Storage has no observed 2025 floor in the current package; this is an
    # explicit input gap, not an inferred zero-observation claim.
    storage_new = model.addMVar((p_count, len(STORAGE_TECHS)), lb=0.0, name="storage_new_gw")
    storage_cap = model.addMVar((p_count, len(STORAGE_TECHS)), lb=0.0, name="storage_capacity_gw")
    model.addConstr(storage_cap == storage_new, name="storage_capacity_accounting")
    variables.update(storage_new=storage_new, storage_capacity=storage_cap)
    storage_params = data.storage.set_index("technology")
    storage_investment = gp.LinExpr()
    storage_fom = gp.LinExpr()
    for technology in STORAGE_TECHS:
        s = s_index[technology]
        capex = float(capex_2030[technology])
        crf = capital_recovery_factor(wacc, float(lifetimes[technology]))
        storage_investment += capex * crf * storage_new[:, s].sum()
        storage_fom += capex * float(storage_params.loc[technology, "fixed_om_fraction_capex_per_year"]) * storage_cap[:, s].sum()
    costs["storage_investment"] = storage_investment
    costs["storage_fixed_om"] = storage_fom

    # One technology is preset for each allowed corridor; capacity remains continuous.
    line_floor = data.lines.existing_capacity_gw.fillna(0.0).to_numpy(dtype=float)
    line_new = model.addMVar(len(data.lines), lb=0.0, name="line_new_gw")
    line_cap = model.addMVar(len(data.lines), lb=line_floor, name="line_capacity_gw")
    model.addConstr(line_cap == line_floor + line_new, name="line_capacity_accounting")
    variables.update(line_new=line_new, line_capacity=line_cap)
    line_crf = capital_recovery_factor(wacc, float(lifetimes["transmission"]))
    line_unit_cost = data.lines.preset_unit_cost_yuan_per_kw.to_numpy(dtype=float)
    costs["transmission_investment"] = (line_unit_cost * line_crf) @ line_new

    if config.raw["features"]["annual_load_center_transmission"]:
        intra_floor = data.intra_load_center_edges.initial_capacity_gw.to_numpy(dtype=float)
        intra_new = model.addMVar(
            len(data.intra_load_center_edges), lb=0.0, name="intra_load_center_new_gw"
        )
        intra_capacity = model.addMVar(
            len(data.intra_load_center_edges),
            lb=intra_floor,
            name="intra_load_center_capacity_gw",
        )
        model.addConstr(
            intra_capacity == intra_floor + intra_new,
            name="intra_load_center_capacity_accounting",
        )
        variables.update(
            intra_load_center_new=intra_new,
            intra_load_center_capacity=intra_capacity,
        )
        intra_unit_cost = data.intra_load_center_edges.unit_cost_yuan_per_kw.to_numpy(dtype=float)
        costs["load_center_intra_transmission_investment"] = (
            intra_unit_cost * line_crf
        ) @ intra_new

    # DAC annual capacity and removal.
    dac_cap = model.addMVar((p_count, len(DAC_TECHS)), lb=0.0, name="dac_capacity_mtpa")
    dac_mass = model.addMVar((p_count, len(DAC_TECHS)), lb=0.0, name="dac_capture_mt")
    model.addConstr(dac_mass <= dac_cap, name="dac_annual_capacity")
    variables.update(dac_capacity=dac_cap, dac_capture=dac_mass)
    dac_table = data.dac.set_index("technology")
    dac_cost = gp.LinExpr()
    for technology in DAC_TECHS:
        d = d_index[technology]
        dac_cost += float(dac_table.loc[technology, "annualized_capex_million_yuan_per_mtco2_per_year_capacity_year"]) * dac_cap[:, d].sum()
        dac_cost += float(dac_table.loc[technology, "fixed_om_million_yuan_per_mtco2_per_year_capacity_year"]) * dac_cap[:, d].sum()
        dac_cost += float(dac_table.loc[technology, "variable_om_yuan_per_tco2"]) * dac_mass[:, d].sum()
    costs["dac"] = dac_cost

    # One annual operating-cost and resource account. ``b_count`` is one in
    # production; the leading dimension is retained for matrix consistency.
    operating_cost_account = model.addMVar(
        b_count, lb=0.0, name="annual_operating_cost_million_cny"
    )
    annual_emissions = model.addMVar(
        b_count, lb=-GRB.INFINITY, name="annual_net_emissions_mt"
    )
    annual_biomass = model.addMVar(
        (b_count, p_count), lb=0.0, name="annual_biomass_fuel_pj"
    )
    annual_captured = model.addMVar(
        (b_count, p_count), lb=0.0, name="annual_captured_co2_mt"
    )
    storage_boundary = model.addMVar((b_count + 1, p_count, len(STORAGE_TECHS)), lb=0.0, name="storage_boundary_gwh")
    online_boundary = model.addMVar((b_count + 1, p_count, len(THERMAL_TECHS)), lb=0.0, name="online_boundary_gw")
    gross_boundary = model.addMVar((b_count + 1, p_count, len(THERMAL_TECHS)), lb=0.0, name="gross_generation_boundary_gw")
    reservoir_boundary = model.addMVar((b_count + 1, p_count), lb=0.0, name="reservoir_boundary_gwh")
    max_commitment_history = int(max(data.ruc.min_up_h.max(), data.ruc.min_down_h.max()))
    startup_history = model.addMVar(
        (b_count + 1, p_count, len(THERMAL_TECHS), max_commitment_history),
        lb=0.0,
        name="startup_boundary_history_gw",
    )
    shutdown_history = model.addMVar(
        (b_count + 1, p_count, len(THERMAL_TECHS), max_commitment_history),
        lb=0.0,
        name="shutdown_boundary_history_gw",
    )
    startup_prefix = model.addMVar(
        (b_count, p_count, len(THERMAL_TECHS), max_commitment_history),
        lb=0.0,
        name="startup_block_prefix_gw",
    )
    shutdown_prefix = model.addMVar(
        (b_count, p_count, len(THERMAL_TECHS), max_commitment_history),
        lb=0.0,
        name="shutdown_block_prefix_gw",
    )
    model.addConstr(storage_boundary[0] == storage_boundary[-1], name="storage_annual_cycle")
    model.addConstr(online_boundary[0] == online_boundary[-1], name="ruc_annual_cycle")
    model.addConstr(gross_boundary[0] == gross_boundary[-1], name="gross_generation_annual_cycle")
    model.addConstr(reservoir_boundary[0] == reservoir_boundary[-1], name="reservoir_annual_cycle")
    model.addConstr(startup_history[0] == startup_history[-1], name="startup_history_annual_cycle")
    model.addConstr(shutdown_history[0] == shutdown_history[-1], name="shutdown_history_annual_cycle")
    variables.update(
        operating_cost_account=operating_cost_account,
        annual_emissions=annual_emissions,
        annual_biomass=annual_biomass,
        annual_captured=annual_captured,
        storage_boundary=storage_boundary,
        online_boundary=online_boundary,
        gross_boundary=gross_boundary,
        reservoir_boundary=reservoir_boundary,
        startup_history=startup_history,
        shutdown_history=shutdown_history,
        startup_prefix=startup_prefix,
        shutdown_prefix=shutdown_prefix,
    )

    carbon_limit = float(data.carbon.emissions_limit_mtco2_per_year)
    effective_dac = dac_mass.sum()
    model.addConstr(annual_emissions.sum() - effective_dac <= carbon_limit, name="annual_net_carbon_limit")
    biomass_limit = (
        data.biomass.set_index("province_code")
        .thermcal_gj_per_year.reindex(provinces).to_numpy(dtype=float)
        / 1.0e6
    )
    model.addConstr(annual_biomass.sum(axis=0) <= biomass_limit, name="annual_biomass_fuel_limit")

    # Annual CCS source-sink allocation. Positive grid-point injection fields
    # remain separate sinks; no province aggregation is used here.
    injection_field = str(config.raw["ccs_injection_field"])
    sinks = data.vre_points.loc[
        data.vre_points[injection_field].gt(0),
        ["grid_uid", "lon", "lat", injection_field],
    ].reset_index(drop=True)
    co2_ship = model.addMVar((p_count, len(sinks)), lb=0.0, name="co2_ship_mt")
    for p in range(p_count):
        model.addConstr(
            co2_ship[p, :].sum()
            == annual_captured[:, p].sum() + dac_mass[p, :].sum(),
            name=f"co2_source_balance_p{provinces[p]}",
        )
    model.addConstr(
        co2_ship.sum(axis=0) <= sinks[injection_field].to_numpy(dtype=float),
        name="co2_sink_injection_capacity",
    )
    variables["co2_ship"] = co2_ship
    province_centers = (
        data.vre_points.groupby("province_code")[["lon", "lat"]]
        .mean()
        .reindex(provinces)
    )
    transport_distance = _haversine_matrix_km(
        province_centers.lon.to_numpy(dtype=float),
        province_centers.lat.to_numpy(dtype=float),
        sinks.lon.to_numpy(dtype=float),
        sinks.lat.to_numpy(dtype=float),
    )
    transport_cost = (
        float(data.ccs_cost.storage_yuan_per_tco2)
        + float(data.ccs_cost.transport_yuan_per_tco2_km) * transport_distance
    )
    costs["co2_transport_injection"] = (transport_cost * co2_ship).sum()

    # Boundary state upper bounds strengthen the monolithic LP.
    storage_duration = data.storage.set_index("technology").duration_h.reindex(STORAGE_TECHS).to_numpy(dtype=float)
    for boundary in range(b_count + 1):
        model.addConstr(
            storage_boundary[boundary] <= storage_cap * storage_duration[None, :],
            name=f"storage_boundary_capacity_b{boundary}",
        )
        model.addConstr(
            online_boundary[boundary] <= thermal_cap,
            name=f"online_boundary_capacity_b{boundary}",
        )
        ruc_boundary = data.ruc.set_index("technology").reindex(THERMAL_TECHS)
        boundary_pmin = ruc_boundary.pmin_fraction.to_numpy(dtype=float)
        boundary_pmax = ruc_boundary.pmax_fraction.to_numpy(dtype=float)
        model.addConstr(
            gross_boundary[boundary] >= online_boundary[boundary] * boundary_pmin[None, :],
            name=f"gross_boundary_minimum_b{boundary}",
        )
        model.addConstr(
            gross_boundary[boundary] <= online_boundary[boundary] * boundary_pmax[None, :],
            name=f"gross_boundary_maximum_b{boundary}",
        )
        model.addConstr(
            startup_history[boundary] <= thermal_cap[:, :, None],
            name=f"startup_history_capacity_b{boundary}",
        )
        model.addConstr(
            shutdown_history[boundary] <= thermal_cap[:, :, None],
            name=f"shutdown_history_capacity_b{boundary}",
        )
        if boundary < b_count:
            model.addConstr(
                startup_prefix[boundary] <= thermal_cap[:, :, None],
                name=f"startup_prefix_capacity_b{boundary}",
            )
            model.addConstr(
                shutdown_prefix[boundary] <= thermal_cap[:, :, None],
                name=f"shutdown_prefix_capacity_b{boundary}",
            )
    reservoir_energy_by_province = np.zeros(p_count, dtype=float)
    hydro_constants = config.raw["hydro"]
    reservoir_rows = data.hydro_stations.operation_type_model.eq("reservoir_storage")
    reservoir = data.hydro_stations.loc[reservoir_rows].copy()
    reservoir["energy_gwh"] = (
        reservoir.active_storage_gl.fillna(0.0)
        * 1.0e6
        * reservoir.head_m.fillna(0.0)
        * float(hydro_constants["reservoir_efficiency"])
        * float(hydro_constants["gravity_m_per_s2"])
        * float(hydro_constants["water_density_kg_per_m3"])
        / 3.6e12
    )
    reservoir_energy_lookup = reservoir.groupby("province_code").energy_gwh.sum()
    for province_code, p in p_index.items():
        reservoir_energy_by_province[p] = float(reservoir_energy_lookup.get(province_code, 0.0))
    for boundary in range(b_count + 1):
        model.addConstr(
            reservoir_boundary[boundary] <= reservoir_energy_by_province,
            name=f"reservoir_boundary_capacity_b{boundary}",
        )

    # Project always-on requirements to chronological block boundaries. A
    # boundary state is the online state of the hour immediately preceding the
    # block; boundary 0 therefore corresponds to the last selected hour under
    # cyclic-horizon conditions.
    hour_dates = (
        data.load[["hour_index", "datetime_bj"]]
        .drop_duplicates("hour_index")
        .sort_values("hour_index")
    )
    hour_month = pd.to_datetime(hour_dates.datetime_bj).dt.month.to_numpy()
    selected_hours = blocks[-1].hour_stop
    boundary_hours = [
        (blocks[boundary].hour_start - 1) % selected_hours
        for boundary in range(b_count)
    ]
    boundary_hours.append(selected_hours - 1)
    boundary_cf = np.zeros((b_count + 1, len(data.vre_sites)), dtype=np.float64)
    for source_technology, group in data.vre_sites.groupby("cf_source_technology", sort=False):
        boundary_cf[:, group.index.to_numpy(dtype=int)] = data.cf.read_hours(
            source_technology,
            group.cf_grid_id.to_numpy(dtype=np.int64),
            boundary_hours,
        )
    winter_months = set(config.raw["thermal"]["chp_winter_months"])
    chp_indices = [k_index[t] for t in ("cchp", "cchpccs", "gchp", "gchpccs")]
    bio_indices = [k_index[t] for t in ("bio", "bioccs")]
    bio_minimum = float(config.raw["thermal"]["biomass_minimum_online_fraction"])
    for boundary in range(b_count + 1):
        if boundary == b_count:
            previous_hour = selected_hours - 1
        else:
            previous_hour = (blocks[boundary].hour_start - 1) % selected_hours
        if int(hour_month[previous_hour]) in winter_months:
            for k in chp_indices:
                model.addConstr(
                    online_boundary[boundary, :, k] == thermal_cap[:, k],
                    name=f"chp_winter_online_boundary_b{boundary}_k{k}",
                )
        for k in bio_indices:
            model.addConstr(
                online_boundary[boundary, :, k] >= bio_minimum * thermal_cap[:, k],
                name=f"biomass_online_boundary_b{boundary}_k{k}",
            )
        boundary_load = data.load_gw[:, previous_hour]
        boundary_ruc = data.ruc.set_index("technology").reindex(THERMAL_TECHS)
        boundary_loss = boundary_ruc.ccs_power_loss_fraction.to_numpy(dtype=float)
        boundary_inertia = boundary_ruc.inertia_s.to_numpy(dtype=float)
        hydro_boundary_capacity = model.addMVar(
            p_count, lb=0.0, name=f"hydro_boundary_capacity_b{boundary}"
        )
        hydro_boundary_inertia = model.addMVar(
            p_count, lb=0.0, name=f"hydro_boundary_inertia_b{boundary}"
        )
        non_sync = config.raw["security"]["non_synchronous_inertia_seconds"]
        for province_code, p in p_index.items():
            subset = data.hydro_stations.loc[data.hydro_stations.province_code.eq(province_code)]
            ror_rows = subset.index[subset.operation_type_model.eq("run_of_river")].to_numpy(dtype=int)
            reservoir_rows = subset.index[
                subset.operation_type_model.eq("reservoir_storage")
            ].to_numpy(dtype=int)
            ror_capacity = hydro_cap[ror_rows].sum() if len(ror_rows) else 0.0
            reservoir_capacity = (
                hydro_cap[reservoir_rows].sum() if len(reservoir_rows) else 0.0
            )
            model.addConstr(
                hydro_boundary_capacity[p] == ror_capacity + reservoir_capacity,
                name=f"hydro_boundary_capacity_link_b{boundary}_p{province_code}",
            )
            model.addConstr(
                hydro_boundary_inertia[p]
                == ror_capacity * float(non_sync["ror"])
                + reservoir_capacity * float(non_sync["reservoir"]),
                name=f"hydro_boundary_inertia_link_b{boundary}_p{province_code}",
            )
        thermal_up_boundary = (
            (1.0 - boundary_loss[None, :])
            * (boundary_pmax[None, :] * online_boundary[boundary] - gross_boundary[boundary])
        ).sum(axis=1)
        thermal_down_boundary = (
            (1.0 - boundary_loss[None, :])
            * (gross_boundary[boundary] - boundary_pmin[None, :] * online_boundary[boundary])
        ).sum(axis=1)
        model.addConstr(
            thermal_up_boundary + storage_cap.sum(axis=1) + hydro_boundary_capacity
            >= float(config.raw["security"]["up_reserve_load_fraction"]) * boundary_load,
            name=f"boundary_up_reserve_b{boundary}",
        )
        model.addConstr(
            thermal_down_boundary + storage_cap.sum(axis=1)
            >= float(config.raw["security"]["down_reserve_load_fraction"]) * boundary_load,
            name=f"boundary_down_reserve_b{boundary}",
        )
        storage_inertia = np.asarray(
            [float(non_sync[technology]) for technology in STORAGE_TECHS], dtype=float
        )
        model.addConstr(
            online_boundary[boundary] @ boundary_inertia
            + storage_cap @ storage_inertia
            + hydro_boundary_inertia
            >= float(config.raw["security"]["minimum_system_inertia_seconds"]) * boundary_load,
            name=f"boundary_inertia_b{boundary}",
        )
        for province_code, p in p_index.items():
            site_positions = data.vre_sites.index[
                data.vre_sites.province_code.eq(province_code)
            ].to_numpy(dtype=int)
            vre_supply = (
                boundary_cf[boundary, site_positions] @ vre_cap[site_positions]
                if len(site_positions)
                else 0.0
            )
            import_capacity = gp.LinExpr()
            for e, line in enumerate(data.lines.itertuples(index=False)):
                efficiency = (1.0 - 3.2e-5) ** float(line.distance_km)
                if int(line.from_province_code) == province_code or int(line.to_province_code) == province_code:
                    import_capacity += efficiency * line_cap[e]
            model.addConstr(
                ((1.0 - boundary_loss) * gross_boundary[boundary, p, :]).sum()
                + vre_supply
                + storage_cap[p, :].sum()
                + hydro_boundary_capacity[p]
                + import_capacity
                >= boundary_load[p],
                name=f"boundary_power_adequacy_b{boundary}_p{province_code}",
            )

    # Capacity margin is imposed on annual capacity decisions.
    credit = config.raw["security"]["capacity_credit"]
    peak = data.load_gw.max(axis=1)
    margin = 1.0 + float(config.raw["security"]["capacity_margin_fraction"])
    for province_code, p in p_index.items():
        expr = gp.LinExpr()
        for technology in THERMAL_TECHS:
            expr += float(credit[technology]) * thermal_cap[p, k_index[technology]]
        province_sites = data.vre_sites.index[data.vre_sites.province_code.eq(province_code)].to_numpy(dtype=int)
        for technology in VRE_TECHS:
            tech_sites = data.vre_sites.index[
                data.vre_sites.province_code.eq(province_code)
                & data.vre_sites.technology.eq(technology)
            ].to_numpy(dtype=int)
            if len(tech_sites):
                expr += float(credit[technology]) * vre_cap[tech_sites].sum()
        hydro_rows = data.hydro_stations.index[data.hydro_stations.province_code.eq(province_code)].to_numpy(dtype=int)
        if len(hydro_rows):
            ror_mask = data.hydro_stations.loc[hydro_rows, "operation_type_model"].eq("run_of_river").to_numpy()
            if ror_mask.any():
                expr += float(credit["ror"]) * hydro_cap[hydro_rows[ror_mask]].sum()
            if (~ror_mask).any():
                expr += float(credit["reservoir"]) * hydro_cap[hydro_rows[~ror_mask]].sum()
        for technology in STORAGE_TECHS:
            expr += float(credit[technology]) * storage_cap[p, s_index[technology]]
        model.addConstr(expr >= margin * peak[p], name=f"capacity_margin_p{province_code}")

    # Intra-grid capacity variables are annual master decisions. Max CF is
    # precomputed from the full 8760 source, never from sampled hours.
    if config.raw["features"]["intra_grid_spur_trunk"]:
        max_cf = compute_vre_max_cf(config, data) if compute_max_cf else np.ones(len(data.vre_sites))
        connection = data.grid_connections.set_index("grid_uid")
        site_substation = data.vre_sites.grid_uid.map(connection.substation_id).astype(str)
        site_distance = np.zeros(len(data.vre_sites), dtype=float)
        distance_column = {
            "onwind": "onwind_spur_distance_km",
            "offwind": "offwind_export_distance_km",
            "upv": "upv_spur_distance_km",
            "dpv": "dpv_spur_distance_km",
        }
        for technology, group in data.vre_sites.groupby("technology"):
            distances = group.grid_uid.map(connection[distance_column[technology]]).fillna(0.0)
            site_distance[group.index] = distances.to_numpy(dtype=float)
        initial_spur_lookup = data.initial_spur.set_index(["grid_uid", "technology"]).initial_spur_capacity_gw
        initial_spur = np.asarray([
            float(initial_spur_lookup.get((row.grid_uid, row.technology), 0.0))
            for row in data.vre_sites.itertuples()
        ])
        spur_new = model.addMVar(len(data.vre_sites), lb=0.0, name="spur_augmentation_gw")
        non_dpv_positions = data.vre_sites.index[
            ~data.vre_sites.technology.eq("dpv")
        ].to_numpy(dtype=int)
        dpv_positions = data.vre_sites.index[
            data.vre_sites.technology.eq("dpv")
        ].to_numpy(dtype=int)
        if len(dpv_positions):
            spur_new[dpv_positions].UB = 0.0
        model.addConstr(
            spur_new[non_dpv_positions] + initial_spur[non_dpv_positions]
            >= max_cf[non_dpv_positions] * vre_cap[non_dpv_positions],
            name="spur_capacity_non_dpv",
        )

        hydro_route = data.hydro_load_center_routes.set_index("hydrochn_row_id")
        hydro_substation = data.hydro_stations.hydrochn_row_id.map(
            hydro_route.substation_id
        ).astype(str)
        hydro_spur_distance = data.hydro_stations.hydrochn_row_id.map(
            hydro_route.hydro_spur_distance_km
        ).to_numpy(dtype=float)
        hydro_floor = data.hydro_stations.existing_capacity_gw.to_numpy(dtype=float)
        hydro_spur_new = model.addMVar(
            len(data.hydro_stations), lb=0.0, name="hydro_spur_augmentation_gw"
        )
        model.addConstr(
            hydro_spur_new + hydro_floor >= hydro_cap,
            name="hydro_spur_capacity",
        )

        substation_ids = data.substations.substation_id.astype(str).tolist()
        sub_index = {sub: i for i, sub in enumerate(substation_ids)}
        trunk_new = model.addMVar(len(substation_ids), lb=0.0, name="trunk_augmentation_gw")
        initial_trunk = data.substations.initial_trunk_capacity_gw.to_numpy(dtype=float)
        vre_by_substation = {
            str(substation_id): grouped.loc[~grouped.technology.eq("dpv")].index.to_numpy(dtype=int)
            for substation_id, grouped in data.vre_sites.assign(_sub=site_substation).groupby("_sub")
        }
        hydro_by_substation = {
            str(substation_id): grouped.index.to_numpy(dtype=int)
            for substation_id, grouped in data.hydro_stations.assign(_sub=hydro_substation).groupby("_sub")
        }
        initial_hydro_trunk = np.zeros(len(substation_ids), dtype=float)
        for substation_id, substation_position in sub_index.items():
            vre_positions = vre_by_substation.get(substation_id, np.asarray([], dtype=int))
            hydro_positions = hydro_by_substation.get(substation_id, np.asarray([], dtype=int))
            if len(hydro_positions):
                initial_hydro_trunk[substation_position] = hydro_floor[hydro_positions].sum()
            if not len(vre_positions) and not len(hydro_positions):
                continue
            required = gp.LinExpr()
            if len(vre_positions):
                required += max_cf[vre_positions] @ vre_cap[vre_positions]
            if len(hydro_positions):
                required += hydro_cap[hydro_positions].sum()
            model.addConstr(
                trunk_new[substation_position]
                + initial_trunk[substation_position]
                + initial_hydro_trunk[substation_position]
                >= required,
                name=f"trunk_capacity_{substation_position}",
            )
        variables.update(
            spur_augmentation=spur_new,
            hydro_spur_augmentation=hydro_spur_new,
            trunk_augmentation=trunk_new,
        )
        network = config.raw["network"]
        spur_crf = capital_recovery_factor(wacc, float(lifetimes["spur"]))
        trunk_crf = capital_recovery_factor(wacc, float(lifetimes["trunk"]))
        spur_unit_cost = (
            (float(network["spur_capex_million_yuan_per_gw_km"]) * site_distance
             + float(network["substation_capex_million_yuan_per_gw"]))
            * (spur_crf + float(network["spur_fixed_om_fraction"]))
        )
        spur_unit_cost[dpv_positions] = 0.0
        costs["spur"] = spur_unit_cost @ spur_new
        costs["hydro_spur"] = (
            (float(network["spur_capex_million_yuan_per_gw_km"]) * hydro_spur_distance
             + float(network["substation_capex_million_yuan_per_gw"]))
            * (spur_crf + float(network["spur_fixed_om_fraction"]))
        ) @ hydro_spur_new
        trunk_distance = data.substations.trunk_distance_km.fillna(0.0).to_numpy(dtype=float)
        costs["trunk"] = (
            (float(network["trunk_capex_million_yuan_per_gw_km"]) * trunk_distance
             + float(network["substation_capex_million_yuan_per_gw"]))
            * (trunk_crf + float(network["trunk_fixed_om_fraction"]))
        ) @ trunk_new
        index_extra = {
            "substation_ids": substation_ids,
            "vre_max_cf": max_cf,
            "initial_hydro_trunk_capacity_gw": initial_hydro_trunk,
        }
    else:
        index_extra = {}

    costs["annual_operation"] = operating_cost_account.sum()
    objective = gp.quicksum(costs.values())
    model.setObjective(objective, GRB.MINIMIZE)
    model.update()
    index = {
        "province_codes": provinces,
        "province_index": p_index,
        "thermal_index": k_index,
        "storage_index": s_index,
        "dac_index": d_index,
        "blocks": blocks,
        "max_commitment_history": max_commitment_history,
        "ccs_sinks": sinks,
        "co2_transport_distance_km": transport_distance,
        **index_extra,
    }
    return MasterArtifacts(model=model, variables=variables, cost_components=costs, index=index)
