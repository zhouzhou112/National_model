"""Build the production-ready 337-city load-center network.

The workflow is additive: it writes ``data/load_center_network/city_337`` and
never overwrites the retained Natural Earth 278-node package.  For every VRE
grid point and hydropower station, the selected same-province route minimizes
the great-circle resource-to-substation spur plus the substation-to-nearest-
city-center trunk distance.  The 2025 spur, substation/trunk and intraprovincial
capacity floors are then rebuilt on those routes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linprog

from build_natural_earth_278_network import build_edges
from build_paper_load_centers import great_circle_matrix_km


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUT = DATA / "load_center_network" / "city_337"

CENTERS_SOURCE = DATA / "grid" / "city_load_centers.csv"
SUBSTATIONS_SOURCE = DATA / "grid" / "substations_osm_220kv_plus.csv"
VRE_SOURCE = DATA / "vre" / "optimization_points.csv"
HYDRO_SOURCE = DATA / "hydro" / "hydro_stations.csv"
SOURCE_SPUR = DATA / "grid" / "initial_spur_capacity_2025.csv"
LOAD_SOURCE = DATA / "load" / "annual_load_summary.csv"
LEGACY_GRID_ROUTE = DATA / "grid" / "grid_connection_by_point.csv"
LEGACY_SUBSTATION_ROUTE = DATA / "grid" / "substation_to_load_center.csv"

EXPECTED_CENTERS = 337
EXPECTED_PROVINCES = 31
EXPECTED_SUBSTATIONS = 6294
EXPECTED_VRE_ROUTES = 16609
EXPECTED_HYDRO_ROUTES = 2030
EXPECTED_EDGES = 642
CHUNK_SIZE = 2000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def sha256_file(path: Path, chunk_size: int = 4 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(chunk_size):
            digest.update(block)
    return digest.hexdigest()


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig", lineterminator="\n")


def build_centers() -> pd.DataFrame:
    source = pd.read_csv(CENTERS_SOURCE)
    centers = source.copy()
    centers["annual_demand_share_in_province"] = (
        centers.annual_city_power_share_in_province.astype(float)
    )
    centers["load_center_method"] = "city_337_urban_population_weighted_centroid"
    centers["demand_share_source"] = (
        "2022_city_electricity; 296_observed_41_imputed_by_province_power_per_urban_population"
    )
    centers["scenario_status"] = "production_default_city_337"
    front = [
        "load_center_id", "province_code", "province_name_en", "province_name_zh",
        "city_name_zh", "source_city_code", "lon", "lat",
        "annual_demand_share_in_province", "annual_city_power_mwh",
        "electricity_weight_method", "center_method", "load_center_method",
        "demand_share_source", "scenario_status",
    ]
    centers = centers[front + [column for column in centers.columns if column not in front]]
    centers = centers.sort_values(["province_code", "load_center_id"]).reset_index(drop=True)
    if len(centers) != EXPECTED_CENTERS or not centers.load_center_id.is_unique:
        raise ValueError("Expected 337 unique city load centers")
    share_error = (
        centers.groupby("province_code").annual_demand_share_in_province.sum()
        .sub(1.0).abs().max()
    )
    if centers.province_code.nunique() != EXPECTED_PROVINCES or share_error > 1e-9:
        raise ValueError(f"City-center province/share closure failed: {share_error}")
    return centers


def build_joint_routes(
    points: pd.DataFrame,
    substations: pd.DataFrame,
    centers: pd.DataFrame,
    *,
    point_id: str,
    point_spur_name: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return nearest-center substation mapping and exact joint point routes."""

    substation_parts: list[pd.DataFrame] = []
    route_parts: list[pd.DataFrame] = []
    for province_code, province_points in points.groupby("province_code", sort=True):
        province_substations = substations.loc[
            substations.province_code.eq(int(province_code))
        ].reset_index(drop=True)
        province_centers = centers.loc[
            centers.province_code.eq(int(province_code))
        ].reset_index(drop=True)
        if province_substations.empty or province_centers.empty:
            raise ValueError(f"Province {province_code} lacks substations or city centers")

        trunk_matrix = great_circle_matrix_km(
            province_substations.lon.to_numpy(float),
            province_substations.lat.to_numpy(float),
            province_centers.lon.to_numpy(float),
            province_centers.lat.to_numpy(float),
        )
        nearest_center_position = trunk_matrix.argmin(axis=1)
        nearest_trunk_km = trunk_matrix[
            np.arange(len(province_substations)), nearest_center_position
        ]
        chosen_centers = province_centers.iloc[nearest_center_position].reset_index(drop=True)
        if point_id == "grid_uid":
            sub_part = province_substations[
                [
                    "substation_id", "province_code", "province_name_en",
                    "province_name_zh", "lon", "lat", "max_voltage_kv",
                    "substation_type",
                ]
            ].copy()
            sub_part["load_center_id"] = chosen_centers.load_center_id.to_numpy()
            sub_part["load_center_city_name_zh"] = chosen_centers.city_name_zh.to_numpy()
            sub_part["load_center_lon"] = chosen_centers.lon.to_numpy(float)
            sub_part["load_center_lat"] = chosen_centers.lat.to_numpy(float)
            sub_part["trunk_distance_km"] = nearest_trunk_km
            sub_part["assignment_method"] = "nearest_city_load_center_within_same_province"
            sub_part["route_status"] = "great_circle_proxy_not_engineering_route"
            substation_parts.append(sub_part)

        local_points = province_points.reset_index(drop=True)
        selected_station_position = np.empty(len(local_points), dtype=int)
        selected_spur_km = np.empty(len(local_points), dtype=float)
        for start in range(0, len(local_points), CHUNK_SIZE):
            stop = min(start + CHUNK_SIZE, len(local_points))
            spur_matrix = great_circle_matrix_km(
                local_points.lon.iloc[start:stop].to_numpy(float),
                local_points.lat.iloc[start:stop].to_numpy(float),
                province_substations.lon.to_numpy(float),
                province_substations.lat.to_numpy(float),
            )
            objective = spur_matrix + nearest_trunk_km[None, :]
            positions = objective.argmin(axis=1)
            selected_station_position[start:stop] = positions
            selected_spur_km[start:stop] = spur_matrix[
                np.arange(stop - start), positions
            ]

        chosen_substations = province_substations.iloc[
            selected_station_position
        ].reset_index(drop=True)
        selected_center_position = nearest_center_position[selected_station_position]
        selected_centers = province_centers.iloc[selected_center_position].reset_index(drop=True)
        selected_trunk_km = nearest_trunk_km[selected_station_position]

        identifier_columns = [point_id, "province_code", "lon", "lat"]
        if point_id == "grid_uid":
            identifier_columns = [
                "grid_uid", "grid_id", "province_code", "province_name_en",
                "province_name_zh", "lon", "lat", "is_land",
            ]
        elif point_id == "hydrochn_row_id":
            identifier_columns = [
                "hydrochn_row_id", "province_code", "lon", "lat",
                "existing_capacity_gw", "operation_type_model",
            ]
        route = local_points[identifier_columns].copy()
        route["substation_id"] = chosen_substations.substation_id.to_numpy()
        route["substation_lon"] = chosen_substations.lon.to_numpy(float)
        route["substation_lat"] = chosen_substations.lat.to_numpy(float)
        route["substation_max_voltage_kv"] = chosen_substations.max_voltage_kv.to_numpy(float)
        route["load_center_id"] = selected_centers.load_center_id.to_numpy()
        route["load_center_city_name_zh"] = selected_centers.city_name_zh.to_numpy()
        route["load_center_lon"] = selected_centers.lon.to_numpy(float)
        route["load_center_lat"] = selected_centers.lat.to_numpy(float)
        route[point_spur_name] = selected_spur_km
        route["trunk_distance_km"] = selected_trunk_km
        route["total_connection_distance_km"] = selected_spur_km + selected_trunk_km
        route["matching_objective"] = (
            "exact minimum over eligible same-province substations of geodesic spur plus "
            "substation-to-nearest-city-center trunk distance"
        )
        route["route_status"] = "great_circle_proxy_not_engineering_route"
        route_parts.append(route)

    substations_out = (
        pd.concat(substation_parts, ignore_index=True)
        .sort_values("substation_id").reset_index(drop=True)
        if substation_parts else pd.DataFrame()
    )
    routes_out = (
        pd.concat(route_parts, ignore_index=True)
        .sort_values(point_id).reset_index(drop=True)
    )
    return substations_out, routes_out


def finalize_vre_routes(routes: pd.DataFrame) -> pd.DataFrame:
    routes = routes.copy()
    routes["spur_distance_km"] = routes.resource_spur_distance_km
    routes["onwind_spur_distance_km"] = routes.resource_spur_distance_km
    routes["onwind_trunk_distance_km"] = routes.trunk_distance_km
    routes["upv_spur_distance_km"] = routes.resource_spur_distance_km
    routes["upv_trunk_distance_km"] = routes.trunk_distance_km
    routes["offwind_export_distance_km"] = routes.resource_spur_distance_km
    routes["offwind_trunk_distance_km"] = routes.trunk_distance_km
    routes["dpv_spur_distance_km"] = 0.0
    routes["dpv_trunk_distance_km"] = 0.0
    return routes.drop(columns="resource_spur_distance_km")


def build_initial_capacity_tables(
    vre_routes: pd.DataFrame,
    substation_routes: pd.DataFrame,
    substations: pd.DataFrame,
    centers: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    source = pd.read_csv(SOURCE_SPUR)
    route_columns = [
        "grid_uid", "substation_id", "load_center_id", "spur_distance_km",
        "trunk_distance_km", "onwind_spur_distance_km", "upv_spur_distance_km",
        "offwind_export_distance_km", "dpv_spur_distance_km", "matching_objective",
        "route_status",
    ]
    routed = source.merge(
        vre_routes[route_columns], on="grid_uid", how="left", validate="many_to_one",
        suffixes=("_source", "_city337"),
    )
    if routed.substation_id_city337.isna().any():
        raise ValueError("A positive-capacity VRE row is missing its city-337 route")
    routed["source_substation_id_before_city337"] = routed.substation_id_source
    routed["substation_id"] = routed.substation_id_city337
    routed["load_center_id"] = routed.load_center_id
    routed["trunk_distance_km"] = routed.trunk_distance_km
    routed["connection_distance_km"] = np.select(
        [
            routed.technology.eq("onwind"), routed.technology.eq("upv"),
            routed.technology.eq("offwind"), routed.technology.eq("dpv"),
        ],
        [
            routed.onwind_spur_distance_km, routed.upv_spur_distance_km,
            routed.offwind_export_distance_km, routed.dpv_spur_distance_km,
        ],
        default=np.nan,
    )
    routed["initial_capacity_method"] = "simultaneous_2025_nameplate_stress_city337_route"
    routed["scenario_status"] = "production_default_city_337"
    routed = routed.drop(
        columns=[
            column for column in routed.columns
            if column.endswith("_source") or column.endswith("_city337")
        ]
    )

    substation_ids = substations.substation_id.astype(str).tolist()
    technology_capacity = (
        routed.pivot_table(
            index="substation_id", columns="technology", values="existing_capacity_gw",
            aggfunc="sum", fill_value=0.0,
        ).reindex(substation_ids, fill_value=0.0)
    )
    for technology in ("onwind", "offwind", "upv", "dpv"):
        if technology not in technology_capacity.columns:
            technology_capacity[technology] = 0.0

    station = substations[
        [
            "substation_id", "province_code", "province_name_en", "province_name_zh",
            "lon", "lat", "max_voltage_kv", "substation_type",
        ]
    ].copy()
    for technology in ("onwind", "offwind", "upv", "dpv"):
        station[f"existing_{technology}_gw"] = technology_capacity[technology].to_numpy(float)
    station["connected_vre_nameplate_gw"] = (
        station.existing_onwind_gw + station.existing_offwind_gw + station.existing_upv_gw
    )
    station["existing_dpv_local_gw"] = station.existing_dpv_gw
    station["simultaneous_nameplate_trunk_capacity_gw"] = station.connected_vre_nameplate_gw
    station["initial_trunk_capacity_gw"] = station.connected_vre_nameplate_gw
    station["initial_substation_vre_interface_capacity_gw"] = station.connected_vre_nameplate_gw
    station["initial_capacity_method"] = "simultaneous_2025_nameplate_stress_city337_route"
    station["rated_capacity_status"] = (
        "inferred VRE interface requirement; not observed equipment rating"
    )
    station = station.merge(
        substation_routes[
            [
                "substation_id", "load_center_id", "load_center_city_name_zh",
                "load_center_lon", "load_center_lat", "trunk_distance_km",
                "assignment_method", "route_status",
            ]
        ],
        on="substation_id", how="left", validate="one_to_one",
    )
    station["scenario_status"] = "production_default_city_337"

    center_initial = (
        station.groupby("load_center_id", as_index=False)
        .agg(
            connected_substation_count=("substation_id", "size"),
            active_substation_count=(
                "connected_vre_nameplate_gw", lambda values: int((values > 0).sum())
            ),
            connected_vre_nameplate_gw=("connected_vre_nameplate_gw", "sum"),
            existing_dpv_local_gw=("existing_dpv_local_gw", "sum"),
            simultaneous_nameplate_interface_capacity_gw=("initial_trunk_capacity_gw", "sum"),
        )
        .merge(
            centers[
                [
                    "load_center_id", "province_code", "province_name_en",
                    "province_name_zh", "city_name_zh", "lon", "lat",
                    "annual_demand_share_in_province",
                ]
            ],
            on="load_center_id", how="right", validate="one_to_one",
        )
    )
    fill = [
        "connected_substation_count", "active_substation_count",
        "connected_vre_nameplate_gw", "existing_dpv_local_gw",
        "simultaneous_nameplate_interface_capacity_gw",
    ]
    center_initial[fill] = center_initial[fill].fillna(0.0)
    center_initial["initial_capacity_method"] = (
        "simultaneous_2025_nameplate_stress_city337_route"
    )
    return routed, station, center_initial


def infer_intra_initial_capacity(
    centers: pd.DataFrame,
    edges: pd.DataFrame,
    center_initial: pd.DataFrame,
    hydro_routes: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    hydro = pd.read_csv(HYDRO_SOURCE)[["hydrochn_row_id", "existing_capacity_gw"]]
    hydro_center = (
        hydro_routes[["hydrochn_row_id", "load_center_id"]]
        .merge(hydro, on="hydrochn_row_id", how="left", validate="one_to_one")
        .groupby("load_center_id", as_index=False).existing_capacity_gw.sum()
        .rename(columns={"existing_capacity_gw": "existing_hydro_gw"})
    )
    initial = centers[
        ["load_center_id", "province_code", "annual_demand_share_in_province"]
    ].merge(
        center_initial[
            ["load_center_id", "connected_vre_nameplate_gw", "existing_dpv_local_gw"]
        ],
        on="load_center_id", how="left", validate="one_to_one",
    ).merge(hydro_center, on="load_center_id", how="left", validate="one_to_one")
    fill = ["connected_vre_nameplate_gw", "existing_dpv_local_gw", "existing_hydro_gw"]
    initial[fill] = initial[fill].fillna(0.0)
    initial["spatial_renewable_nameplate_gw"] = initial[fill].sum(axis=1)

    peak = (
        pd.read_csv(LOAD_SOURCE).loc[lambda frame: frame.year.eq(2025)]
        .set_index("province_code").peak_demand_gw
    )
    edge_capacity = pd.Series(0.0, index=edges.index, dtype=float)
    audit_rows: list[dict[str, object]] = []
    for province_code, nodes in initial.groupby("province_code", sort=True):
        nodes = nodes.reset_index(drop=True)
        province_edges = edges.loc[edges.province_code.eq(province_code)].copy()
        renewable = nodes.spatial_renewable_nameplate_gw.to_numpy(float)
        shares = nodes.annual_demand_share_in_province.to_numpy(float)
        province_peak = float(peak.loc[province_code])
        conventional_proxy = max(province_peak - renewable.sum(), 0.0)
        supply = renewable + shares * conventional_proxy - shares * province_peak
        export_total = max(float(renewable.sum() - province_peak), 0.0)
        if len(nodes) == 1:
            if abs(float(supply[0]) - export_total) > 1e-7:
                raise ValueError(f"Single-center balance failed in province {province_code}")
            audit_rows.append(
                {
                    "province_code": int(province_code), "center_count": 1,
                    "edge_count": 0, "peak_demand_gw": province_peak,
                    "spatial_renewable_nameplate_gw": float(renewable.sum()),
                    "allocated_conventional_peak_proxy_gw": conventional_proxy,
                    "external_export_peak_proxy_gw": export_total,
                    "initial_intra_capacity_sum_gw": 0.0,
                    "maximum_balance_residual_gw": abs(float(supply[0]) - export_total),
                }
            )
            continue

        node_position = {node_id: i for i, node_id in enumerate(nodes.load_center_id)}
        local_edge_indices = province_edges.index.to_numpy(int)
        edge_count = len(province_edges)
        node_count = len(nodes)
        variable_count = 2 * edge_count + node_count
        objective = np.zeros(variable_count, dtype=float)
        distance = province_edges.distance_km.to_numpy(float)
        objective[:edge_count] = distance
        objective[edge_count:2 * edge_count] = distance
        objective[2 * edge_count:] = 1e-8 / np.maximum(renewable, 1e-6)
        balance = np.zeros((node_count, variable_count), dtype=float)
        for local_edge, row in enumerate(province_edges.itertuples(index=False)):
            i = node_position[row.from_load_center_id]
            j = node_position[row.to_load_center_id]
            balance[i, local_edge] = -1.0
            balance[j, local_edge] = 1.0
            balance[i, edge_count + local_edge] = 1.0
            balance[j, edge_count + local_edge] = -1.0
        balance[:, 2 * edge_count:] = -np.eye(node_count)
        bounds = [(0.0, None)] * (2 * edge_count)
        bounds += [(0.0, export_total) if export_total > 0 else (0.0, 0.0)] * node_count
        result = linprog(
            objective, A_eq=balance, b_eq=-supply, bounds=bounds, method="highs",
            options={"dual_feasibility_tolerance": 1e-9, "primal_feasibility_tolerance": 1e-9},
        )
        if not result.success:
            raise RuntimeError(f"2025 city-337 intra-network proxy failed: {result.message}")
        flows = result.x[:edge_count] + result.x[edge_count:2 * edge_count]
        edge_capacity.loc[local_edge_indices] = flows
        residual = balance @ result.x + supply
        audit_rows.append(
            {
                "province_code": int(province_code), "center_count": node_count,
                "edge_count": edge_count, "peak_demand_gw": province_peak,
                "spatial_renewable_nameplate_gw": float(renewable.sum()),
                "allocated_conventional_peak_proxy_gw": conventional_proxy,
                "external_export_peak_proxy_gw": export_total,
                "initial_intra_capacity_sum_gw": float(flows.sum()),
                "maximum_balance_residual_gw": float(np.abs(residual).max()),
            }
        )

    output = edges.copy()
    output["initial_capacity_gw"] = edge_capacity.to_numpy(float)
    output["initial_capacity_method"] = (
        "2025_simultaneous_wind_solar_hydro_nameplate_spatial_balance_proxy; "
        "thermal_nuclear_biomass_allocated_by_city_demand_share"
    )
    return output, pd.DataFrame(audit_rows)


def legacy_route_regret(vre_routes: pd.DataFrame) -> pd.DataFrame:
    legacy_grid = pd.read_csv(LEGACY_GRID_ROUTE)[
        ["grid_uid", "substation_id", "nearest_substation_distance_km"]
    ]
    legacy_sub = pd.read_csv(LEGACY_SUBSTATION_ROUTE)[
        ["substation_id", "trunk_distance_km"]
    ].rename(columns={"trunk_distance_km": "legacy_trunk_distance_km"})
    legacy = legacy_grid.merge(
        legacy_sub, on="substation_id", how="left", validate="many_to_one"
    )
    legacy["legacy_total_distance_km"] = (
        legacy.nearest_substation_distance_km + legacy.legacy_trunk_distance_km
    )
    comparison = vre_routes[
        ["grid_uid", "province_code", "spur_distance_km", "trunk_distance_km", "total_connection_distance_km"]
    ].merge(
        legacy[["grid_uid", "legacy_total_distance_km"]],
        on="grid_uid", how="left", validate="one_to_one",
    )
    comparison["distance_improvement_km"] = (
        comparison.legacy_total_distance_km - comparison.total_connection_distance_km
    )
    return comparison


def build_readme(edges: pd.DataFrame) -> str:
    return f"""# 337 个市级负荷中心正式模型输入

本目录由 `scripts/build_city_337_network.py` 自动生成，并保留
`data/load_center_network/natural_earth_278/` 作为可回滚的 CISPO 复现情景。

- 负荷中心：337 个，每个模型地级单元一个，覆盖 31 个省级模型区域。
- 年度权重：2022 城市用电省内份额；296 个观测城市，41 个按省内用电/城镇人口强度插补。
- 风光路线：格点 → 同省联合最优 220 kV 及以上 OSM 变电站 → 最近市级负荷中心。
- 水电路线：站点 → 同省联合最优变电站 → 最近市级负荷中心。
- 路由目标：在同省全部合格变电站中精确最小化大圆 `spur + trunk` 距离。
- 省内网络：每省 MST 与每节点三个最近邻的并集，共 {len(edges)} 条无向 AC 500 kV 代理边。
- 2025 初始化：已有风光、水电装机和城市需求份额形成空间平衡代理；线路容量不是观测额定容量。
- 年度设计利用率：50%；省内线路损耗：0；二者均需在敏感性分析中检验。
"""


def main() -> None:
    args = parse_args()
    required = [
        CENTERS_SOURCE, SUBSTATIONS_SOURCE, VRE_SOURCE, HYDRO_SOURCE,
        SOURCE_SPUR, LOAD_SOURCE, LEGACY_GRID_ROUTE, LEGACY_SUBSTATION_ROUTE,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing city-337 inputs:\n" + "\n".join(missing))
    if args.dry_run:
        print(json.dumps({"output": str(OUTPUT), "inputs": [str(p) for p in required]}, indent=2))
        return

    centers = build_centers()
    substations = pd.read_csv(SUBSTATIONS_SOURCE)
    vre_points = pd.read_csv(VRE_SOURCE)
    hydro = pd.read_csv(HYDRO_SOURCE)
    substation_routes, raw_vre_routes = build_joint_routes(
        vre_points, substations, centers,
        point_id="grid_uid", point_spur_name="resource_spur_distance_km",
    )
    vre_routes = finalize_vre_routes(raw_vre_routes)
    _, hydro_routes = build_joint_routes(
        hydro, substations, centers,
        point_id="hydrochn_row_id", point_spur_name="hydro_spur_distance_km",
    )
    initial_spur, station_initial, center_initial = build_initial_capacity_tables(
        vre_routes, substation_routes, substations, centers
    )
    edges = build_edges(centers)
    edges, initial_audit = infer_intra_initial_capacity(
        centers, edges, center_initial, hydro_routes
    )
    comparison = legacy_route_regret(vre_routes)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    outputs = {
        "load_centers.csv": centers,
        "vre_routes.csv": vre_routes,
        "hydro_routes.csv": hydro_routes,
        "intra_edges.csv": edges,
        "initial_spur_capacity_2025.csv": initial_spur,
        "substation_initial_capacity_2025.csv": station_initial,
        "load_center_initial_capacity_2025.csv": center_initial,
        "initial_capacity_2025_audit.csv": initial_audit,
        "route_optimization_comparison.csv": comparison,
    }
    for name, frame in outputs.items():
        write_csv(frame, OUTPUT / name)
    (OUTPUT / "README_zh.md").write_text(build_readme(edges), encoding="utf-8")

    share_error = float(
        centers.groupby("province_code").annual_demand_share_in_province.sum()
        .sub(1.0).abs().max()
    )
    known = centers.set_index("load_center_id").province_code
    same_edge_province = bool(
        (
            edges.from_load_center_id.map(known).to_numpy()
            == edges.to_load_center_id.map(known).to_numpy()
        ).all()
    )
    connected_vre = float(station_initial.connected_vre_nameplate_gw.sum())
    local_dpv = float(station_initial.existing_dpv_local_gw.sum())
    max_regret = float((-comparison.distance_improvement_km).max())
    max_balance_residual = float(initial_audit.maximum_balance_residual_gw.max())
    checks = [
        ("load_center_count", len(centers) == EXPECTED_CENTERS, len(centers)),
        ("province_count", centers.province_code.nunique() == EXPECTED_PROVINCES, centers.province_code.nunique()),
        ("province_share_closure", share_error <= 1e-9, share_error),
        ("substation_route_count", len(substation_routes) == EXPECTED_SUBSTATIONS, len(substation_routes)),
        ("vre_route_count", len(vre_routes) == EXPECTED_VRE_ROUTES, len(vre_routes)),
        ("hydro_route_count", len(hydro_routes) == EXPECTED_HYDRO_ROUTES, len(hydro_routes)),
        ("intra_edge_count", len(edges) == EXPECTED_EDGES, len(edges)),
        ("intra_edge_same_province", same_edge_province, same_edge_province),
        ("connected_vre_nameplate_gw", np.isclose(connected_vre, 1310.0, atol=1e-6), connected_vre),
        ("local_dpv_gw", np.isclose(local_dpv, 530.0, atol=1e-6), local_dpv),
        ("joint_route_not_worse_than_legacy", max_regret <= 1e-7, max_regret),
        ("initial_balance_residual", max_balance_residual <= 1e-7, max_balance_residual),
        ("initial_edge_capacity_nonnegative", bool(edges.initial_capacity_gw.ge(0).all()), float(edges.initial_capacity_gw.min())),
    ]
    check_rows = [
        {"check": name, "status": "PASS" if passed else "HARD_FAIL", "value": value}
        for name, passed, value in checks
    ]
    status = "HARD_FAIL" if any(row["status"] == "HARD_FAIL" for row in check_rows) else "PASS"
    output_paths = [OUTPUT / name for name in outputs] + [OUTPUT / "README_zh.md"]
    manifest = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "scenario": "city_337",
        "status": status,
        "scenario_status": "production_default_city_337",
        "route_method": "exact_same_province_minimum_geodesic_spur_plus_nearest_city_center_trunk",
        "topology_method": "within_province_mst_plus_3_nearest_neighbours_geodesic",
        "design_utilization_fraction": 0.5,
        "counts": {
            "load_centers": len(centers), "provinces": centers.province_code.nunique(),
            "substations": len(substation_routes), "vre_grid_routes": len(vre_routes),
            "hydro_routes": len(hydro_routes), "intra_edges": len(edges),
            "initialized_intra_edges": int(edges.initial_capacity_gw.gt(1e-12).sum()),
        },
        "2025_initialization": {
            "connected_wind_utility_pv_nameplate_gw": connected_vre,
            "local_dpv_gw": local_dpv,
            "existing_hydro_gw": float(hydro.existing_capacity_gw.sum()),
            "intra_capacity_sum_gw": float(edges.initial_capacity_gw.sum()),
            "method": "simultaneous spatial renewable nameplate balance proxy",
            "rated_capacity_status": "inferred requirement; not observed line/substation rating",
        },
        "route_comparison": {
            "mean_improvement_km": float(comparison.distance_improvement_km.mean()),
            "p95_improvement_km": float(comparison.distance_improvement_km.quantile(0.95)),
            "maximum_negative_improvement_km": max_regret,
        },
        "checks": check_rows,
        "source_files": {str(path.relative_to(ROOT)): sha256_file(path) for path in required},
        "output_files": {
            str(path.relative_to(OUTPUT)): sha256_file(path) for path in output_paths
        },
    }
    with (OUTPUT / "manifest.json").open("w", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    if status != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
