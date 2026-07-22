"""Annual load-center energy allocation and intra-province transmission."""
from __future__ import annotations

from typing import Any

import gurobipy as gp
import numpy as np

from .config import ModelConfig
from .data import VRE_TECHS, ModelData
from .hydro import HydroLinearBlock
from .master import MasterArtifacts


def attach_annual_load_center_network(
    model: gp.Model,
    config: ModelConfig,
    data: ModelData,
    artifacts: MasterArtifacts,
    *,
    hours: int,
    vre_site_cf_hours: np.ndarray,
    vre_generation: gp.MVar,
    actual_thermal: gp.MVar,
    storage_charge: gp.MVar,
    storage_discharge: gp.MVar,
    dac_load: gp.MLinExpr,
    hydro_block: HydroLinearBlock,
    hydro_capacity: gp.MVar,
    ror_generation: gp.MVar,
    reservoir_generation: gp.MVar,
    interprovincial_flow_forward: gp.MVar,
    interprovincial_flow_reverse_ac: gp.MVar,
    interprovincial_reverse_edge_rows: np.ndarray,
    interprovincial_efficiency: np.ndarray,
    effective_load: Any,
) -> gp.LinExpr:
    """Attach an annual energy network without adding center-hour variables.

    Spatial VRE and hydropower generation are attributed to their connected
    configured load centers. Province-aggregated terms are allocated by the
    fixed annual center demand shares. Interprovincial exchange enters this
    annual layer as net received-minus-sent energy, so the center proxy cannot
    create a gross import/export loop. Summing every center balance within a
    province exactly recovers the summed provincial hourly power balance when
    intra-province losses are zero.
    """
    centers = data.load_centers.reset_index(drop=True)
    edges = data.intra_load_center_edges.reset_index(drop=True)
    center_ids = centers.load_center_id.astype(str).tolist()
    center_index = {center_id: i for i, center_id in enumerate(center_ids)}
    provinces = data.province_codes.tolist()
    province_index = artifacts.index["province_index"]
    technology_index = {technology: i for i, technology in enumerate(VRE_TECHS)}
    center_count = len(centers)
    edge_count = len(edges)
    coefficient_tolerance = float(config.raw["numerics"]["coefficient_zero_tolerance"])

    if not np.isclose(
        centers.groupby("province_code").annual_demand_share_in_province.sum().to_numpy(float),
        1.0,
        atol=1e-9,
    ).all():
        raise ValueError("Configured load-center demand shares do not close by province")

    center_vre_generation = model.addMVar(
        (center_count, len(VRE_TECHS)), lb=0.0, name="load_center_vre_generation_gwh"
    )
    center_ror_generation = model.addMVar(
        center_count, lb=0.0, name="load_center_ror_generation_gwh"
    )
    center_reservoir_generation = model.addMVar(
        center_count, lb=0.0, name="load_center_reservoir_generation_gwh"
    )
    center_injection = model.addMVar(
        center_count, lb=0.0, name="load_center_annual_injection_gwh"
    )
    center_demand = model.addMVar(
        center_count, lb=0.0, name="load_center_annual_effective_demand_gwh"
    )
    center_external_net_import = model.addMVar(
        center_count,
        lb=-gp.GRB.INFINITY,
        name="load_center_external_net_import_gwh",
    )
    intra_forward = model.addMVar(
        edge_count, lb=0.0, name="intra_load_center_flow_forward_gwh"
    )
    intra_reverse = model.addMVar(
        edge_count, lb=0.0, name="intra_load_center_flow_reverse_gwh"
    )
    province_non_spatial_injection = model.addMVar(
        len(provinces), lb=0.0, name="province_annual_non_spatial_injection_gwh"
    )
    province_effective_demand = model.addMVar(
        len(provinces), lb=0.0, name="province_annual_effective_demand_gwh"
    )
    province_external_sent = model.addMVar(
        len(provinces), lb=0.0, name="province_annual_external_sent_gwh"
    )
    province_external_received = model.addMVar(
        len(provinces), lb=0.0, name="province_annual_external_received_gwh"
    )
    province_external_net_import = model.addMVar(
        len(provinces),
        lb=-gp.GRB.INFINITY,
        name="province_annual_external_net_import_gwh",
    )

    # Attribute actual province-technology VRE generation to centers while
    # respecting the exact selected-horizon site availability envelope.
    route_lookup = data.vre_load_center_routes.set_index("grid_uid").load_center_id
    site_center = data.vre_sites.grid_uid.map(route_lookup).astype(str)
    sites_with_center = data.vre_sites.assign(_load_center_id=site_center)
    vre_capacity = artifacts.variables["vre_capacity"]
    for center_id, center_position in center_index.items():
        center_sites = sites_with_center.loc[sites_with_center._load_center_id.eq(center_id)]
        for technology, technology_position in technology_index.items():
            positions = center_sites.index[
                center_sites.technology.eq(technology)
            ].to_numpy(dtype=int)
            positions = positions[vre_site_cf_hours[positions] >= coefficient_tolerance]
            if len(positions):
                model.addConstr(
                    center_vre_generation[center_position, technology_position]
                    <= vre_site_cf_hours[positions] @ vre_capacity[positions],
                    name=f"load_center_vre_availability_{center_position}_{technology}",
                )
            else:
                center_vre_generation[center_position, technology_position].UB = 0.0
    for province_code in provinces:
        p = province_index[province_code]
        center_positions = centers.index[
            centers.province_code.eq(province_code)
        ].to_numpy(dtype=int)
        for technology, technology_position in technology_index.items():
            model.addConstr(
                center_vre_generation[center_positions, technology_position].sum()
                == vre_generation[p, technology_position, :].sum(),
                name=f"load_center_vre_generation_closure_p{province_code}_{technology}",
            )

    # Attribute province-level hydropower dispatch to spatially routed plants.
    hydro_route_lookup = data.hydro_load_center_routes.set_index("hydrochn_row_id").load_center_id
    hydro_center = data.hydro_stations.hydrochn_row_id.map(hydro_route_lookup).astype(str)
    invalid_hydro_routes = ~hydro_center.isin(center_ids)
    if invalid_hydro_routes.any():
        raise ValueError(
            "Hydropower load-center routes contain missing or unknown center IDs: "
            f"{int(invalid_hydro_routes.sum())} stations"
        )
    reservoir_global_to_local = {
        int(station_row): local_row
        for local_row, station_row in enumerate(hydro_block.reservoir_station_rows)
    }
    ror_full_load_hours = np.zeros(len(data.hydro_stations), dtype=float)
    reservoir_route_counts = np.zeros(
        len(hydro_block.reservoir_station_rows), dtype=np.int64
    )
    for p in range(len(provinces)):
        station_rows = hydro_block.ror_station_rows[p]
        if len(station_rows):
            ror_full_load_hours[station_rows] = hydro_block.ror_capacity_factor[p].sum(axis=0)
    for center_id, center_position in center_index.items():
        station_rows = data.hydro_stations.index[hydro_center.eq(center_id)].to_numpy(dtype=int)
        ror_rows = station_rows[
            data.hydro_stations.loc[station_rows, "operation_type_model"]
            .eq("run_of_river").to_numpy()
        ]
        ror_rows = ror_rows[ror_full_load_hours[ror_rows] >= coefficient_tolerance]
        reservoir_station_rows = station_rows[
            ~data.hydro_stations.loc[station_rows, "operation_type_model"]
            .eq("run_of_river").to_numpy()
        ]
        reservoir_local_rows = np.asarray(
            [
                reservoir_global_to_local[int(station_row)]
                for station_row in reservoir_station_rows
            ],
            dtype=np.int64,
        )
        reservoir_route_counts[reservoir_local_rows] += 1
        if len(ror_rows):
            model.addConstr(
                center_ror_generation[center_position]
                <= ror_full_load_hours[ror_rows] @ hydro_capacity[ror_rows],
                name=f"load_center_ror_availability_{center_position}",
            )
        else:
            center_ror_generation[center_position].UB = 0.0
        if len(reservoir_local_rows):
            model.addConstr(
                center_reservoir_generation[center_position]
                == reservoir_generation[reservoir_local_rows, :].sum(),
                name=f"load_center_reservoir_generation_{center_position}",
            )
        else:
            center_reservoir_generation[center_position].UB = 0.0
    if not np.equal(reservoir_route_counts, 1).all():
        raise ValueError(
            "Each reservoir station must be routed to exactly one load center; "
            f"violations={int(np.count_nonzero(reservoir_route_counts != 1))}"
        )
    for province_code in provinces:
        p = province_index[province_code]
        center_positions = centers.index[
            centers.province_code.eq(province_code)
        ].to_numpy(dtype=int)
        model.addConstr(
            center_ror_generation[center_positions].sum() == ror_generation[p, :].sum(),
            name=f"load_center_ror_generation_closure_p{province_code}",
        )

    received_energy: list[gp.LinExpr] = [gp.LinExpr() for _ in provinces]
    sent_energy: list[gp.LinExpr] = [gp.LinExpr() for _ in provinces]
    reverse_position_by_edge = {
        int(edge_row): position
        for position, edge_row in enumerate(interprovincial_reverse_edge_rows)
    }
    for edge, row in enumerate(data.lines.itertuples(index=False)):
        p_from = province_index[int(row.from_province_code)]
        p_to = province_index[int(row.to_province_code)]
        efficiency = float(interprovincial_efficiency[edge])
        sent_energy[p_from] += interprovincial_flow_forward[edge, :].sum()
        received_energy[p_to] += efficiency * interprovincial_flow_forward[edge, :].sum()
        reverse_position = reverse_position_by_edge.get(edge)
        if reverse_position is not None:
            sent_energy[p_to] += interprovincial_flow_reverse_ac[
                reverse_position, :
            ].sum()
            received_energy[p_from] += efficiency * interprovincial_flow_reverse_ac[
                reverse_position, :
            ].sum()

    # Aggregate each dense province-hour expression once. Reusing these scalar
    # annual accounts at the configured centers avoids duplicating millions of matrix
    # coefficients without changing the formulation.
    for province_code in provinces:
        p = province_index[province_code]
        model.addConstr(
            province_non_spatial_injection[p]
            == actual_thermal[p, :, :].sum()
            + storage_discharge[p, :, :].sum(),
            name=f"province_annual_non_spatial_injection_p{province_code}",
        )
        model.addConstr(
            province_effective_demand[p]
            == effective_load[p, :].sum()
            + storage_charge[p, :, :].sum()
            + float(hours) * dac_load[p],
            name=f"province_annual_effective_demand_p{province_code}",
        )
        model.addConstr(
            province_external_sent[p] == sent_energy[p],
            name=f"province_annual_external_sent_p{province_code}",
        )
        model.addConstr(
            province_external_received[p] == received_energy[p],
            name=f"province_annual_external_received_p{province_code}",
        )
        model.addConstr(
            province_external_net_import[p]
            == province_external_received[p] - province_external_sent[p],
            name=f"province_annual_external_net_import_p{province_code}",
        )

    # Center injection and effective demand use the same fixed annual share for
    # every non-spatial province term, so their provincial sums remain exact.
    for center_position, row in enumerate(centers.itertuples(index=False)):
        p = province_index[int(row.province_code)]
        share = float(row.annual_demand_share_in_province)
        spatial_injection = (
            center_vre_generation[center_position, :].sum()
            + center_ror_generation[center_position]
            + center_reservoir_generation[center_position]
        )
        if share >= coefficient_tolerance:
            model.addConstr(
                center_injection[center_position]
                == spatial_injection + share * province_non_spatial_injection[p],
                name=f"load_center_annual_injection_{center_position}",
            )
            model.addConstr(
                center_demand[center_position] == share * province_effective_demand[p],
                name=f"load_center_annual_demand_{center_position}",
            )
            model.addConstr(
                center_external_net_import[center_position]
                == share * province_external_net_import[p],
                name=f"load_center_external_net_import_{center_position}",
            )
        else:
            model.addConstr(
                center_injection[center_position] == spatial_injection,
                name=f"load_center_annual_injection_{center_position}",
            )
            center_demand[center_position].UB = 0.0
            center_external_net_import[center_position].LB = 0.0
            center_external_net_import[center_position].UB = 0.0

    forward_in: list[list[int]] = [[] for _ in range(center_count)]
    forward_out: list[list[int]] = [[] for _ in range(center_count)]
    reverse_in: list[list[int]] = [[] for _ in range(center_count)]
    reverse_out: list[list[int]] = [[] for _ in range(center_count)]
    for edge, row in enumerate(edges.itertuples(index=False)):
        origin = center_index[str(row.from_load_center_id)]
        destination = center_index[str(row.to_load_center_id)]
        forward_out[origin].append(edge)
        forward_in[destination].append(edge)
        reverse_out[destination].append(edge)
        reverse_in[origin].append(edge)

    for center_position in range(center_count):
        inflow = gp.LinExpr()
        outflow = gp.LinExpr()
        if forward_in[center_position]:
            inflow += intra_forward[forward_in[center_position]].sum()
        if reverse_in[center_position]:
            inflow += intra_reverse[reverse_in[center_position]].sum()
        if forward_out[center_position]:
            outflow += intra_forward[forward_out[center_position]].sum()
        if reverse_out[center_position]:
            outflow += intra_reverse[reverse_out[center_position]].sum()
        model.addConstr(
            center_injection[center_position]
            + center_external_net_import[center_position]
            + inflow
            == center_demand[center_position] + outflow,
            name=f"load_center_annual_energy_balance_{center_position}",
        )

    utilization = float(config.raw["load_center_network"]["design_utilization_fraction"])
    design_hours = utilization * float(hours)
    model.addConstr(
        intra_forward + intra_reverse
        <= design_hours * artifacts.variables["intra_load_center_capacity"],
        name="intra_load_center_annual_capacity",
    )

    artifacts.variables.update(
        load_center_vre_generation=center_vre_generation,
        load_center_ror_generation=center_ror_generation,
        load_center_reservoir_generation=center_reservoir_generation,
        load_center_annual_injection=center_injection,
        load_center_annual_demand=center_demand,
        load_center_external_net_import=center_external_net_import,
        intra_load_center_flow_forward=intra_forward,
        intra_load_center_flow_reverse=intra_reverse,
        province_annual_non_spatial_injection=province_non_spatial_injection,
        province_annual_effective_demand=province_effective_demand,
        province_annual_external_sent=province_external_sent,
        province_annual_external_received=province_external_received,
        province_annual_external_net_import=province_external_net_import,
    )
    artifacts.index.update(
        load_center_ids=center_ids,
        load_center_index=center_index,
        intra_load_center_edge_ids=edges.intra_edge_id.astype(str).tolist(),
        intra_load_center_design_hours=design_hours,
    )
    regularization = float(
        config.raw["load_center_network"]["flow_regularization_yuan_per_mwh"]
    )
    return regularization * 1e-3 * (intra_forward.sum() + intra_reverse.sum())
