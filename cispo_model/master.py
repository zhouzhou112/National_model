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
from .planning_state import stable_asset_id
from .wave_energy import wave_cost_parameters


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
    vre = vre.rename(columns={"capacity_floor_gw": "exogenous_capacity_floor_gw"})
    vre["capacity_floor_gw"] = np.asarray(
        artifacts.index["vre_capacity_floor_gw"], dtype=float
    )
    vre["inherited_capacity_adjustment_gw"] = (
        vre.capacity_floor_gw - vre.exogenous_capacity_floor_gw
    )
    vre["capacity_gw"] = variables["vre_capacity"].X
    vre["new_capacity_gw"] = variables["vre_new"].X
    vre.to_csv(output_dir / "vre_capacity.csv", index=False, encoding="utf-8-sig")
    if data.wave is not None and "wave_capacity" in variables:
        wave = data.wave.sites[
            [
                "grid_uid",
                "grid_id",
                "wave_source_grid_id",
                "lon",
                "lat",
                "province_code",
                "load_center_id",
                "substation_id",
                "capacity_upper_gw_raw",
                "capacity_upper_gw",
                "distance_to_shore_km",
                "water_depth_m",
                "wave_nc_imputed",
            ]
        ].copy()
        wave["capacity_floor_gw"] = np.asarray(
            artifacts.index["wave_capacity_floor_gw"], dtype=float
        )
        wave["capacity_gw"] = variables["wave_capacity"].X
        wave["new_capacity_gw"] = variables["wave_new"].X
        wave.to_csv(
            output_dir / "wave_capacity.csv", index=False, encoding="utf-8-sig"
        )

    thermal_rows = []
    capacity = variables["thermal_capacity"].X
    new_capacity = variables["thermal_new"].X
    retrofit = variables.get("thermal_retrofit_to_ccs")
    retrofit_values = retrofit.X if retrofit is not None else None
    ccs_pair_index = {
        technology: (pair_position, direction)
        for pair_position, pair in enumerate(artifacts.index.get("ccs_pairs", ()))
        for technology, direction in ((pair[0], "out"), (pair[1], "in"))
    }
    thermal_floor = np.asarray(artifacts.index["thermal_capacity_floor_gw"])
    thermal_exogenous = np.asarray(artifacts.index["thermal_exogenous_floor_gw"])
    retrofit_survivor_upper = np.asarray(
        artifacts.index.get(
            "thermal_retrofit_survivor_upper_gw",
            np.zeros(
                (
                    len(artifacts.index["province_codes"]),
                    len(artifacts.index.get("ccs_pairs", ())),
                )
            ),
        )
    )
    for p, province_code in enumerate(artifacts.index["province_codes"]):
        for technology, k in artifacts.index["thermal_index"].items():
            thermal_rows.append(
                {
                    "province_code": province_code,
                    "technology": technology,
                    "exogenous_capacity_floor_gw": thermal_exogenous[p, k],
                    "inherited_capacity_adjustment_gw": (
                        thermal_floor[p, k] - thermal_exogenous[p, k]
                    ),
                    "capacity_floor_gw": thermal_floor[p, k],
                    "capacity_gw": capacity[p, k],
                    "new_capacity_gw": new_capacity[p, k],
                    "retrofit_out_gw": (
                        retrofit_values[p, ccs_pair_index[technology][0]]
                        if retrofit_values is not None
                        and technology in ccs_pair_index
                        and ccs_pair_index[technology][1] == "out"
                        else 0.0
                    ),
                    "retrofit_in_gw": (
                        retrofit_values[p, ccs_pair_index[technology][0]]
                        if retrofit_values is not None
                        and technology in ccs_pair_index
                        and ccs_pair_index[technology][1] == "in"
                        else 0.0
                    ),
                    "retrofit_survivor_upper_gw": (
                        retrofit_survivor_upper[p, ccs_pair_index[technology][0]]
                        if technology in ccs_pair_index
                        else 0.0
                    ),
                }
            )
    pd.DataFrame(thermal_rows).to_csv(
        output_dir / "thermal_nuclear_capacity.csv", index=False, encoding="utf-8-sig"
    )

    storage_rows = []
    capacity = variables["storage_capacity"].X
    new_capacity = variables["storage_new"].X
    storage_floor = np.asarray(artifacts.index["storage_capacity_floor_gw"])
    storage_exogenous_floor = np.asarray(
        artifacts.index["storage_exogenous_floor_gw"]
    )
    storage_upper = np.asarray(artifacts.index["storage_capacity_upper_gw"])
    for p, province_code in enumerate(artifacts.index["province_codes"]):
        for technology, s in artifacts.index["storage_index"].items():
            storage_rows.append(
                {
                    "province_code": province_code,
                    "technology": technology,
                    "exogenous_capacity_floor_gw": storage_exogenous_floor[p, s],
                    "inherited_capacity_adjustment_gw": (
                        storage_floor[p, s] - storage_exogenous_floor[p, s]
                    ),
                    "capacity_floor_gw": storage_floor[p, s],
                    "capacity_upper_gw": storage_upper[p, s],
                    "capacity_gw": capacity[p, s],
                    "new_capacity_gw": new_capacity[p, s],
                }
            )
    pd.DataFrame(storage_rows).to_csv(
        output_dir / "storage_capacity.csv", index=False, encoding="utf-8-sig"
    )

    hydro = data.hydro_stations[
        [
            "hydrochn_row_id", "plant_name_model", "province_code", "lon", "lat",
            "comid", "operation_type_model", "status_model", "river_group_stage2",
            "existing_capacity_gw", "capacity_potential_gw",
        ]
    ].copy()
    hydro["capacity_floor_gw"] = np.asarray(
        artifacts.index["hydro_capacity_floor_gw"], dtype=float
    )
    hydro["inherited_capacity_adjustment_gw"] = (
        hydro.capacity_floor_gw - hydro.existing_capacity_gw
    )
    hydro["capacity_gw"] = variables["hydro_capacity"].X
    hydro["new_capacity_gw"] = variables["hydro_new"].X
    hydro.to_csv(output_dir / "hydro_capacity.csv", index=False, encoding="utf-8-sig")

    dac_rows = []
    dac_capacity = variables["dac_capacity"].X
    dac_new = variables["dac_new"].X
    dac_capture = variables["dac_capture"].X
    dac_floor = np.asarray(artifacts.index["dac_capacity_floor_mtpa"])
    for p, province_code in enumerate(artifacts.index["province_codes"]):
        for technology, d in artifacts.index["dac_index"].items():
            dac_rows.append(
                {
                    "province_code": province_code,
                    "technology": technology,
                    "capacity_floor_mtpa": dac_floor[p, d],
                    "capacity_mtpa": dac_capacity[p, d],
                    "new_capacity_mtpa": dac_new[p, d],
                    "capture_mtco2": dac_capture[p, d],
                }
            )
    pd.DataFrame(dac_rows).to_csv(
        output_dir / "dac_capacity_capture.csv", index=False, encoding="utf-8-sig"
    )

    co2_ship = variables["co2_ship"].X
    sinks = artifacts.index["ccs_sinks"]
    positive = np.argwhere(co2_ship > 1e-9)
    co2_rows = []
    for p, sink_position in positive:
        sink = sinks.iloc[int(sink_position)]
        co2_rows.append(
            {
                "province_code": artifacts.index["province_codes"][int(p)],
                "sink_grid_uid": sink.grid_uid,
                "sink_lon": sink.lon,
                "sink_lat": sink.lat,
                "shipped_mtco2": co2_ship[int(p), int(sink_position)],
            }
        )
    pd.DataFrame(
        co2_rows,
        columns=[
            "province_code", "sink_grid_uid", "sink_lon", "sink_lat",
            "shipped_mtco2",
        ],
    ).to_csv(
        output_dir / "co2_source_sink_flows.csv", index=False, encoding="utf-8-sig"
    )

    line = data.lines[
        ["line_id", "from_province_code", "to_province_code", "preset_technology", "distance_km"]
    ].copy()
    line["capacity_gw"] = variables["line_capacity"].X
    line["capacity_floor_gw"] = np.asarray(
        artifacts.index["line_capacity_floor_gw"], dtype=float
    )
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
        centers["annual_external_net_import_gwh"] = variables[
            "load_center_external_net_import"
        ].X
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
            if "load_center_wave_generation" in variables:
                generation_rows.append(
                    {
                        "load_center_id": center.load_center_id,
                        "province_code": int(center.province_code),
                        "technology": "wave",
                        "annual_generation_gwh": variables[
                            "load_center_wave_generation"
                        ].X[center_position],
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
        province_accounts["annual_external_received_gwh"] = variables[
            "province_annual_external_received"
        ].X
        province_accounts["annual_external_net_import_gwh"] = variables[
            "province_annual_external_net_import"
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
            + variables["load_center_external_net_import"].X
            - variables["load_center_annual_demand"].X
        )
        center_index = artifacts.index["load_center_index"]
        for edge, row in enumerate(data.intra_load_center_edges.itertuples(index=False)):
            origin = center_index[str(row.from_load_center_id)]
            destination = center_index[str(row.to_load_center_id)]
            balance_residual[origin] -= forward[edge]
            balance_residual[destination] += forward[edge]
            balance_residual[destination] -= reverse[edge]
            balance_residual[origin] += reverse[edge]
        province_net_exchange_residual = []
        external_net_import = variables["province_annual_external_net_import"].X
        for p, province_code in enumerate(artifacts.index["province_codes"]):
            positions = data.load_centers.index[
                data.load_centers.province_code.eq(province_code)
            ].to_numpy(dtype=int)
            province_net_exchange_residual.append(
                variables["load_center_external_net_import"].X[positions].sum()
                - external_net_import[p]
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
            "maximum_province_net_exchange_residual_gwh": float(
                np.abs(province_net_exchange_residual).max()
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
            or qc["maximum_province_net_exchange_residual_gwh"] > 1e-5
            or qc["maximum_intra_capacity_violation_gwh"] > 1e-5
            or qc["bidirectional_active_edge_count"] > 0
            or qc["dpv_spur_augmentation_max_gw"] > 1e-8
        ):
            raise RuntimeError(f"Load-center solution QC failed: {qc}")

    cost_frame = pd.DataFrame(
        [
            {
                "cost_component": name,
                "value_million_cny_per_year": expression.getValue(),
                "included_directly_in_objective": not name.startswith("operating_"),
                "included_in_primary_cost": not name.startswith("operating_"),
                "included_directly_in_solver_objective": (
                    not name.startswith("operating_")
                    and "mga" not in artifacts.index
                ),
            }
            for name, expression in artifacts.cost_components.items()
        ]
    )
    cost_frame.to_csv(output_dir / "cost_components.csv", index=False, encoding="utf-8-sig")


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
    constraint_handles: dict[str, Any] = {}
    wacc = float(config.raw["finance"]["real_wacc_fraction"])
    lifetimes = config.raw["finance"]["default_lifetime_years"]

    # VRE site capacity remains at 0.25-degree resolution. Sequential years
    # add only active model-built cohorts to the unchanged observed baseline.
    vre_asset_ids = [
        stable_asset_id(row.grid_uid, row.technology)
        for row in data.vre_sites.itertuples(index=False)
    ]
    vre_inherited = data.planning_state.active_adjustment(
        "vre", vre_asset_ids, planning_year=config.planning_year, unit="GW"
    )
    site_floor = (
        data.vre_sites.capacity_floor_gw.to_numpy(dtype=float) + vre_inherited
    )
    site_upper = data.vre_sites.capacity_upper_gw.to_numpy(dtype=float)
    if (site_floor < -1e-9).any() or (site_floor > site_upper + 1e-9).any():
        raise ValueError("Inherited VRE capacity is outside the active site bounds")
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
        vre_investment += capex * crf * vre_cap[positions].sum()
        vre_fom += capex * vre_fom_fraction[technology] * vre_cap[positions].sum()
    costs["vre_investment"] = vre_investment
    costs["vre_fixed_om"] = vre_fom

    # Wave energy is a separate opt-in asset class.  This leaves the validated
    # wind/PV arrays and their spur/trunk contract untouched in Base.
    if data.wave is not None:
        wave_sites = data.wave.sites
        wave_asset_ids = [
            stable_asset_id(grid_uid, "wave")
            for grid_uid in wave_sites.grid_uid
        ]
        wave_inherited = data.planning_state.active_adjustment(
            "wave",
            wave_asset_ids,
            planning_year=config.planning_year,
            unit="GW",
        )
        wave_floor = np.asarray(wave_inherited, dtype=float)
        wave_upper = wave_sites.capacity_upper_gw.to_numpy(dtype=float)
        if (wave_floor < -1e-9).any() or (wave_floor > wave_upper + 1e-9).any():
            raise ValueError(
                "Inherited wave capacity is outside the active site bounds"
            )
        wave_new = model.addMVar(
            len(wave_sites), lb=0.0, name="wave_new_gw"
        )
        wave_capacity = model.addMVar(
            len(wave_sites),
            lb=wave_floor,
            ub=wave_upper,
            name="wave_capacity_gw",
        )
        model.addConstr(
            wave_capacity == wave_floor + wave_new,
            name="wave_capacity_accounting",
        )
        wave_capex, wave_fom_fraction, wave_lifetime = wave_cost_parameters(
            config, wave_sites
        )
        wave_crf = capital_recovery_factor(wacc, wave_lifetime)
        costs["wave_investment"] = (
            wave_capex * wave_crf
        ) @ wave_capacity
        costs["wave_fixed_om"] = (
            wave_capex * wave_fom_fraction
        ) @ wave_capacity
        variables.update(wave_new=wave_new, wave_capacity=wave_capacity)
    else:
        wave_asset_ids = []
        wave_floor = np.asarray([], dtype=float)

    # Thermal and nuclear capacity in GW. Continuous RUC makes explicit unit
    # counts unnecessary; all unit-based equations are scaled by capacity.
    floor_table = data.thermal_floor.pivot(index="province_code", columns="technology", values="capacity_floor_gw")
    floor_table = floor_table.reindex(index=provinces, columns=THERMAL_TECHS[:-1], fill_value=0.0)
    nuclear = data.nuclear_floor.set_index("province_code").capacity_floor_gw.reindex(provinces).fillna(0.0)
    thermal_exogenous_floor = np.column_stack(
        [floor_table.to_numpy(dtype=float), nuclear.to_numpy(dtype=float)]
    )
    thermal_asset_ids = [
        stable_asset_id(province_code, technology)
        for province_code in provinces
        for technology in THERMAL_TECHS
    ]
    thermal_inherited = data.planning_state.active_adjustment(
        "thermal",
        thermal_asset_ids,
        planning_year=config.planning_year,
        unit="GW",
    ).reshape(p_count, len(THERMAL_TECHS))
    thermal_floor = thermal_exogenous_floor + thermal_inherited
    if (thermal_floor < -1e-9).any():
        raise ValueError(
            "Inherited thermal retrofit/build cohorts make a capacity floor negative"
        )
    thermal_floor = np.maximum(thermal_floor, 0.0)
    nuclear_k = k_index["nuclear"]
    nuclear_upper = (
        data.nuclear_upper.set_index("province_code")
        .capacity_upper_gw.reindex(provinces).to_numpy(dtype=float)
    )
    if (thermal_floor[:, nuclear_k] > nuclear_upper + 1e-9).any():
        raise ValueError(
            "Inherited nuclear capacity exceeds the configured province upper bound"
        )
    thermal_new = model.addMVar(
        (p_count, len(THERMAL_TECHS)), lb=0.0, name="thermal_new_gw"
    )
    thermal_cap = model.addMVar(
        (p_count, len(THERMAL_TECHS)), lb=0.0, name="thermal_capacity_gw"
    )
    thermal_cap[:, nuclear_k].UB = nuclear_upper
    ccs_pairs = (
        ("coal", "coalccs"),
        ("cchp", "cchpccs"),
        ("gas", "gasccs"),
        ("gchp", "gchpccs"),
        ("bio", "bioccs"),
    )
    thermal_retrofit = model.addMVar(
        (p_count, len(ccs_pairs)), lb=0.0, name="thermal_retrofit_to_ccs_gw"
    )
    retrofit_survivor_upper = np.zeros((p_count, len(ccs_pairs)), dtype=float)
    for pair_position, (non_ccs, ccs) in enumerate(ccs_pairs):
        non_ccs_k = k_index[non_ccs]
        ccs_k = k_index[ccs]
        # A retrofit inherits the source fleet's remaining modeled life.  The
        # aggregate input has no unit vintages, so only capacity that remains
        # present at every later planning snapshot while this retrofit cohort
        # is active may be converted.  This conservative envelope prevents a
        # negative non-CCS floor when the exogenous fleet retires in 2040+.
        survivor_upper = thermal_floor[:, non_ccs_k].copy()
        retrofit_retire_year = (
            config.planning_year
            + int(round(float(config.raw["finance"]["default_lifetime_years"][non_ccs])))
        )
        for future_year in (
            year
            for year in config.planning_years
            if config.planning_year < year < retrofit_retire_year
        ):
            future_table = data.thermal_floor_all_years.loc[
                data.thermal_floor_all_years.year.eq(future_year)
            ].pivot(
                index="province_code",
                columns="technology",
                values="capacity_floor_gw",
            )
            future_exogenous = (
                future_table.reindex(index=provinces, columns=[non_ccs], fill_value=0.0)
                .iloc[:, 0]
                .to_numpy(dtype=float)
            )
            future_inherited = data.planning_state.active_adjustment(
                "thermal",
                thermal_asset_ids,
                planning_year=future_year,
                unit="GW",
            ).reshape(p_count, len(THERMAL_TECHS))[:, non_ccs_k]
            survivor_upper = np.minimum(
                survivor_upper,
                np.maximum(future_exogenous + future_inherited, 0.0),
            )
        retrofit_survivor_upper[:, pair_position] = survivor_upper
        thermal_retrofit[:, pair_position].UB = survivor_upper
        model.addConstr(
            thermal_cap[:, non_ccs_k]
            == thermal_floor[:, non_ccs_k]
            - thermal_retrofit[:, pair_position]
            + thermal_new[:, non_ccs_k],
            name=f"thermal_non_ccs_capacity_accounting_{non_ccs}",
        )
        model.addConstr(
            thermal_cap[:, ccs_k]
            == thermal_floor[:, ccs_k]
            + thermal_retrofit[:, pair_position]
            + thermal_new[:, ccs_k],
            name=f"thermal_ccs_capacity_accounting_{ccs}",
        )
    model.addConstr(
        thermal_cap[:, nuclear_k]
        == thermal_floor[:, nuclear_k] + thermal_new[:, nuclear_k],
        name="nuclear_capacity_accounting",
    )
    bio_k = k_index["bio"]
    bioccs_k = k_index["bioccs"]
    biomass_pair_upper = (
        data.biomass_capacity_bounds.set_index("province_code")
        .capacity_upper_gw.reindex(provinces).to_numpy(dtype=float)
    )
    biomass_pair_floor = thermal_floor[:, bio_k] + thermal_floor[:, bioccs_k]
    if (biomass_pair_floor > biomass_pair_upper + 1e-9).any():
        raise ValueError(
            "Inherited biomass plus BECCS capacity exceeds the configured shared upper bound"
        )
    constraint_handles["biomass_beccs_capacity_upper"] = model.addConstr(
        thermal_cap[:, bio_k] + thermal_cap[:, bioccs_k]
        <= biomass_pair_upper,
        name="biomass_beccs_shared_capacity_upper_s4_34",
    )
    variables.update(
        thermal_new=thermal_new,
        thermal_capacity=thermal_cap,
        thermal_retrofit_to_ccs=thermal_retrofit,
    )

    fuel_allowed = data.fuel.pivot(index="province_code", columns="technology", values="new_capacity_allowed")
    for technology in THERMAL_TECHS[:-1]:
        k = k_index[technology]
        if technology in fuel_allowed.columns:
            disabled = ~fuel_allowed[technology].reindex(provinces).fillna(False).astype(bool).to_numpy()
            for p in np.flatnonzero(disabled):
                thermal_new[p, k].UB = 0.0
    for non_ccs, ccs in (("cchp", "cchpccs"), ("gchp", "gchpccs")):
        thermal_new[:, k_index[non_ccs]].UB = 0.0
        thermal_new[:, k_index[ccs]].UB = 0.0

    om = data.thermal_om.set_index("technology")
    thermal_investment = gp.LinExpr()
    thermal_fom = gp.LinExpr()
    for technology in THERMAL_TECHS:
        k = k_index[technology]
        crf = capital_recovery_factor(wacc, float(lifetimes[technology]))
        capex = float(capex_2030[technology])
        # CISPO SI Eq. 4.3 annualizes total thermal/nuclear capacity. This also
        # gives a source-grounded incremental cost for non-CCS to CCS retrofit
        # through the technology-specific CapEx difference.
        thermal_investment += capex * crf * thermal_cap[:, k].sum()
        thermal_fom += capex * float(om.loc[technology, "fixed_om_fraction_capex_per_year"]) * thermal_cap[:, k].sum()
    costs["thermal_nuclear_investment"] = thermal_investment
    costs["thermal_nuclear_fixed_om"] = thermal_fom

    # Hydropower station capacity is retained at station resolution.
    hydro_asset_ids = data.hydro_stations.hydrochn_row_id.astype(str).tolist()
    hydro_inherited = data.planning_state.active_adjustment(
        "hydro",
        hydro_asset_ids,
        planning_year=config.planning_year,
        unit="GW",
    )
    hydro_floor = (
        data.hydro_stations.existing_capacity_gw.to_numpy(dtype=float)
        + hydro_inherited
    )
    hydro_upper = data.hydro_stations.capacity_potential_gw.to_numpy(dtype=float)
    if (hydro_floor < -1e-9).any() or (hydro_floor > hydro_upper + 1e-9).any():
        raise ValueError("Inherited hydropower capacity is outside station bounds")
    hydro_new = model.addMVar(len(data.hydro_stations), lb=0.0, name="hydro_new_gw")
    hydro_cap = model.addMVar(len(data.hydro_stations), lb=hydro_floor, ub=hydro_upper, name="hydro_capacity_gw")
    model.addConstr(hydro_cap == hydro_floor + hydro_new, name="hydro_capacity_accounting")
    variables.update(hydro_new=hydro_new, hydro_capacity=hydro_cap)
    hydro_capex = float(capex_2030["hydro"])
    hydro_crf = capital_recovery_factor(wacc, float(lifetimes["hydro"]))
    costs["hydro_investment"] = hydro_capex * hydro_crf * hydro_cap.sum()
    costs["hydro_fixed_om"] = hydro_capex * 0.02 * hydro_cap.sum()

    # Province-level PHS retains the GHT 2026 operating floor and is capped by
    # projects available by the planning year. Battery potential remains open.
    storage_asset_ids = [
        stable_asset_id(province_code, technology)
        for province_code in provinces
        for technology in STORAGE_TECHS
    ]
    storage_exogenous_floor = np.zeros((p_count, len(STORAGE_TECHS)), dtype=float)
    storage_upper = np.full((p_count, len(STORAGE_TECHS)), np.inf, dtype=float)
    phs_bounds = data.storage_bounds.set_index("province_code")
    battery_bounds = data.battery_bounds.set_index("province_code")
    battery_index = s_index["battery"]
    phs_index = s_index["phs"]
    for p, province_code in enumerate(provinces):
        storage_exogenous_floor[p, battery_index] = float(
            battery_bounds.loc[province_code, "capacity_floor_gw"]
        )
        storage_exogenous_floor[p, phs_index] = float(
            phs_bounds.loc[province_code, "capacity_floor_gw"]
        )
        storage_upper[p, phs_index] = float(
            phs_bounds.loc[province_code, "capacity_upper_gw"]
        )
    storage_inherited = data.planning_state.active_adjustment(
        "storage",
        storage_asset_ids,
        planning_year=config.planning_year,
        unit="GW",
    ).reshape(p_count, len(STORAGE_TECHS))
    storage_floor = storage_exogenous_floor + storage_inherited
    if (
        (storage_floor < -1e-9).any()
        or (storage_floor > storage_upper + 1e-9).any()
    ):
        raise ValueError("Inherited storage capacity is outside configured bounds")
    storage_new = model.addMVar((p_count, len(STORAGE_TECHS)), lb=0.0, name="storage_new_gw")
    storage_cap = model.addMVar(
        (p_count, len(STORAGE_TECHS)),
        lb=storage_floor,
        ub=storage_upper,
        name="storage_capacity_gw",
    )
    model.addConstr(
        storage_cap == storage_floor + storage_new,
        name="storage_capacity_accounting",
    )
    variables.update(storage_new=storage_new, storage_capacity=storage_cap)
    storage_params = data.storage.set_index("technology")
    storage_investment = gp.LinExpr()
    storage_fom = gp.LinExpr()
    for technology in STORAGE_TECHS:
        s = s_index[technology]
        capex = float(capex_2030[technology])
        crf = capital_recovery_factor(wacc, float(lifetimes[technology]))
        storage_investment += capex * crf * storage_cap[:, s].sum()
        storage_fom += capex * float(storage_params.loc[technology, "fixed_om_fraction_capex_per_year"]) * storage_cap[:, s].sum()
    costs["storage_investment"] = storage_investment
    costs["storage_fixed_om"] = storage_fom

    # One technology is preset for each allowed corridor; capacity remains continuous.
    line_asset_ids = data.lines.line_id.astype(str).tolist()
    line_inherited = data.planning_state.active_adjustment(
        "interprovincial_transmission",
        line_asset_ids,
        planning_year=config.planning_year,
        unit="GW",
    )
    line_floor = (
        data.lines.existing_capacity_gw.fillna(0.0).to_numpy(dtype=float)
        + line_inherited
    )
    line_new = model.addMVar(len(data.lines), lb=0.0, name="line_new_gw")
    line_cap = model.addMVar(len(data.lines), lb=line_floor, name="line_capacity_gw")
    model.addConstr(line_cap == line_floor + line_new, name="line_capacity_accounting")
    variables.update(line_new=line_new, line_capacity=line_cap)
    line_crf = capital_recovery_factor(wacc, float(lifetimes["transmission"]))
    line_unit_cost = data.lines.preset_unit_cost_yuan_per_kw.to_numpy(dtype=float)
    costs["transmission_investment"] = (line_unit_cost * line_crf) @ line_cap

    if config.raw["features"]["annual_load_center_transmission"]:
        intra_asset_ids = data.intra_load_center_edges.intra_edge_id.astype(str).tolist()
        intra_floor = (
            data.intra_load_center_edges.initial_capacity_gw.to_numpy(dtype=float)
            + data.planning_state.active_adjustment(
                "intra_load_center_transmission",
                intra_asset_ids,
                planning_year=config.planning_year,
                unit="GW",
            )
        )
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
        ) @ intra_capacity

    # DAC annual capacity and removal.
    dac_asset_ids = [
        stable_asset_id(province_code, technology)
        for province_code in provinces
        for technology in DAC_TECHS
    ]
    dac_floor = data.planning_state.active_adjustment(
        "dac",
        dac_asset_ids,
        planning_year=config.planning_year,
        unit="MtCO2_per_year",
    ).reshape(p_count, len(DAC_TECHS))
    dac_new = model.addMVar(
        (p_count, len(DAC_TECHS)), lb=0.0, name="dac_new_capacity_mtpa"
    )
    dac_cap = model.addMVar((p_count, len(DAC_TECHS)), lb=0.0, name="dac_capacity_mtpa")
    dac_mass = model.addMVar((p_count, len(DAC_TECHS)), lb=0.0, name="dac_capture_mt")
    model.addConstr(dac_cap == dac_floor + dac_new, name="dac_capacity_accounting")
    model.addConstr(dac_mass <= dac_cap, name="dac_annual_capacity")
    variables.update(dac_new=dac_new, dac_capacity=dac_cap, dac_capture=dac_mass)
    dac_table = data.dac.set_index("technology")
    dac_cost = gp.LinExpr()
    for technology in DAC_TECHS:
        d = d_index[technology]
        dac_cost += float(dac_table.loc[technology, "annualized_capex_million_yuan_per_mtco2_per_year_capacity_year"]) * dac_cap[:, d].sum()
        dac_cost += float(dac_table.loc[technology, "fixed_om_million_yuan_per_mtco2_per_year_capacity_year"]) * dac_cap[:, d].sum()
        dac_cost += float(dac_table.loc[technology, "variable_om_yuan_per_tco2"]) * dac_mass[:, d].sum()
    costs["dac"] = dac_cost

    # Annual resource accounts. Operating cost is attached directly to the
    # objective after hourly variables exist, avoiding a badly scaled dense
    # accounting equality.
    annual_emissions = model.addMVar(
        b_count, lb=-GRB.INFINITY, name="annual_net_emissions_mt"
    )
    annual_biomass = model.addMVar(
        (b_count, p_count), lb=0.0, name="annual_biomass_fuel_pj"
    )
    annual_captured = model.addMVar(
        (b_count, p_count), lb=0.0, name="annual_captured_co2_mt"
    )
    variables.update(
        annual_emissions=annual_emissions,
        annual_biomass=annual_biomass,
        annual_captured=annual_captured,
    )

    carbon_limit = float(data.carbon.emissions_limit_mtco2_per_year)
    effective_dac = dac_mass.sum()
    constraint_handles["annual_net_carbon_limit"] = model.addConstr(
        annual_emissions.sum() - effective_dac <= carbon_limit,
        name="annual_net_carbon_limit",
    )
    biomass_limit = (
        data.biomass.set_index("province_code")
        .thermcal_gj_per_year.reindex(provinces).to_numpy(dtype=float)
        / 1.0e6
    )
    constraint_handles["annual_biomass_fuel_limit"] = model.addConstr(
        annual_biomass.sum(axis=0) <= biomass_limit,
        name="annual_biomass_fuel_limit",
    )

    # Annual CCS source-sink allocation. Positive grid-point injection fields
    # remain separate sinks; no province aggregation is used here.
    injection_field = str(config.raw["ccs_injection_field"])
    sinks = data.vre_points.loc[
        data.vre_points[injection_field].gt(0),
        ["grid_uid", "lon", "lat", injection_field],
    ].reset_index(drop=True)
    co2_ship = model.addMVar((p_count, len(sinks)), lb=0.0, name="co2_ship_mt")
    co2_source_constraints = []
    for p in range(p_count):
        co2_source_constraints.append(model.addConstr(
            co2_ship[p, :].sum()
            == annual_captured[:, p].sum() + dac_mass[p, :].sum(),
            name=f"co2_source_balance_p{provinces[p]}",
        ))
    constraint_handles["co2_source_balance"] = co2_source_constraints
    constraint_handles["co2_sink_injection_capacity"] = model.addConstr(
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
    # yuan/tCO2 multiplied by MtCO2 equals million CNY. Capture cost is
    # separate from the CCS efficiency penalty and transport/injection cost.
    costs["ccs_capture"] = (
        float(data.ccs_cost.capture_yuan_per_tco2) * annual_captured.sum()
    )
    costs["co2_transport_injection"] = (transport_cost * co2_ship).sum()

    # Capacity margin is imposed on annual capacity decisions.
    credit = config.raw["security"]["capacity_credit"]
    peak = data.load_gw.max(axis=1)
    margin = 1.0 + float(config.raw["security"]["capacity_margin_fraction"])
    capacity_margin_constraints = []
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
        if data.wave is not None:
            wave_rows = data.wave.sites.index[
                data.wave.sites.province_code.eq(province_code)
            ].to_numpy(dtype=int)
            if len(wave_rows):
                expr += (
                    float(config.raw["wave_energy"]["capacity_credit"])
                    * variables["wave_capacity"][wave_rows].sum()
                )
        capacity_margin_constraints.append(
            model.addConstr(
                expr >= margin * peak[p], name=f"capacity_margin_p{province_code}"
            )
        )
    constraint_handles["capacity_margin"] = capacity_margin_constraints

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
        initial_spur += data.planning_state.active_adjustment(
            "vre_spur",
            vre_asset_ids,
            planning_year=config.planning_year,
            unit="GW",
        )
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
        hydro_spur_floor = (
            data.hydro_stations.existing_capacity_gw.to_numpy(dtype=float)
            + data.planning_state.active_adjustment(
                "hydro_spur",
                hydro_asset_ids,
                planning_year=config.planning_year,
                unit="GW",
            )
        )
        hydro_spur_new = model.addMVar(
            len(data.hydro_stations), lb=0.0, name="hydro_spur_augmentation_gw"
        )
        model.addConstr(
            hydro_spur_new + hydro_spur_floor >= hydro_cap,
            name="hydro_spur_capacity",
        )

        substation_ids = data.substations.substation_id.astype(str).tolist()
        sub_index = {sub: i for i, sub in enumerate(substation_ids)}
        trunk_new = model.addMVar(len(substation_ids), lb=0.0, name="trunk_augmentation_gw")
        trunk_asset_ids = data.substations.substation_id.astype(str).tolist()
        initial_trunk = (
            data.substations.initial_trunk_capacity_gw.to_numpy(dtype=float)
            + data.planning_state.active_adjustment(
                "trunk",
                trunk_asset_ids,
                planning_year=config.planning_year,
                unit="GW",
            )
        )
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
                initial_hydro_trunk[substation_position] = (
                    data.hydro_stations.existing_capacity_gw.to_numpy(dtype=float)[
                        hydro_positions
                    ].sum()
                )
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
            "vre_spur_floor_gw": initial_spur,
            "hydro_spur_floor_gw": hydro_spur_floor,
            "trunk_floor_gw": initial_trunk,
            "trunk_asset_ids": trunk_asset_ids,
        }
    else:
        index_extra = {}

    costs["annual_operation"] = gp.LinExpr()
    objective = gp.quicksum(costs.values())
    model.setObjective(objective, GRB.MINIMIZE)
    model.update()
    index = {
        "province_codes": provinces,
        "province_index": p_index,
        "thermal_index": k_index,
        "storage_index": s_index,
        "dac_index": d_index,
        "ccs_pairs": ccs_pairs,
        "blocks": blocks,
        "ccs_sinks": sinks,
        "co2_transport_distance_km": transport_distance,
        "vre_asset_ids": vre_asset_ids,
        "wave_asset_ids": wave_asset_ids,
        "wave_capacity_floor_gw": wave_floor,
        "vre_capacity_floor_gw": site_floor,
        "thermal_asset_ids": thermal_asset_ids,
        "thermal_exogenous_floor_gw": thermal_exogenous_floor,
        "thermal_capacity_floor_gw": thermal_floor,
        "thermal_retrofit_survivor_upper_gw": retrofit_survivor_upper,
        "nuclear_capacity_upper_gw": nuclear_upper,
        "biomass_pair_capacity_upper_gw": biomass_pair_upper,
        "hydro_asset_ids": hydro_asset_ids,
        "hydro_capacity_floor_gw": hydro_floor,
        "storage_asset_ids": storage_asset_ids,
        "storage_exogenous_floor_gw": storage_exogenous_floor,
        "storage_capacity_floor_gw": storage_floor,
        "storage_capacity_upper_gw": storage_upper,
        "line_asset_ids": line_asset_ids,
        "line_capacity_floor_gw": line_floor,
        "dac_asset_ids": dac_asset_ids,
        "dac_capacity_floor_mtpa": dac_floor,
        "constraint_handles": constraint_handles,
        **index_extra,
    }
    if config.raw["features"]["annual_load_center_transmission"]:
        index["intra_asset_ids"] = intra_asset_ids
        index["intra_capacity_floor_gw"] = intra_floor
    return MasterArtifacts(model=model, variables=variables, cost_components=costs, index=index)
