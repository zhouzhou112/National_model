"""Build production inputs for the Natural Earth 278-load-center network.

The script promotes the already validated paper-method candidate without
modifying its source files.  It creates compact model-ready tables for:

* the 278 Natural Earth load centers and annual demand shares;
* VRE grid-point and hydropower-station routes to those centers;
* paper-route 2025 spur/trunk baselines;
* a connected within-province MST + 3-nearest-neighbour 500-kV proxy graph;
* a conservative 2025 initial intra-province capacity proxy.

Run from the repository root:

    python scripts/build_natural_earth_278_network.py
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.sparse.csgraph import minimum_spanning_tree


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCE = DATA / "load_centers_1km" / "paper_method_candidate"
OUTPUT = DATA / "load_center_network" / "natural_earth_278"

CENTERS_SOURCE = SOURCE / "paper_load_centers.csv"
VRE_ROUTE_SOURCE = SOURCE / "grid_point_paper_route.csv"
SUBSTATION_SOURCE = SOURCE / "substation_to_paper_load_center.csv"
INITIAL_SOURCE = SOURCE / "initial_2025"
HYDRO_SOURCE = DATA / "hydro" / "hydro_stations.csv"
LOAD_SOURCE = DATA / "load" / "annual_load_summary.csv"

DESIGN_UTILIZATION_FRACTION = 0.50
NEAREST_NEIGHBOURS = 3

# Digitized EES Figure S44 values already used by the province-corridor module.
AC_500_FIT_SAMPLES = [
    (1.0, 3.00), (2.0, 2.48), (3.0, 2.10), (4.0, 1.82), (5.0, 1.60),
    (6.0, 1.43), (7.0, 1.30), (8.0, 1.20), (9.0, 1.11), (10.0, 1.04),
]
AC_500_SUBSTATION_YUAN_PER_KW = 159.0
AC_500_LINE_THOUSAND_YUAN_PER_KM = 2640.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig", float_format="%.12g")


def haversine_matrix_km(lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    lon_r = np.radians(lon)
    lat_r = np.radians(lat)
    dlon = lon_r[:, None] - lon_r[None, :]
    dlat = lat_r[:, None] - lat_r[None, :]
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat_r[:, None]) * np.cos(lat_r[None, :])
        * np.sin(dlon / 2.0) ** 2
    )
    return 6371.0088 * 2.0 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def cross_haversine_km(
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


def fit_ac_500_curve() -> tuple[float, float, float]:
    x = np.asarray([row[0] for row in AC_500_FIT_SAMPLES], dtype=float)
    y = np.asarray([row[1] for row in AC_500_FIT_SAMPLES], dtype=float)
    best: tuple[float, float, float, float] | None = None
    for b in np.linspace(0.02, 0.8, 3000):
        z = np.exp(-b * (x - 1.0))
        c, a = np.linalg.lstsq(np.column_stack([np.ones_like(z), z]), y, rcond=None)[0]
        sse = float(np.square(y - (c + a * z)).sum())
        if best is None or sse < best[3]:
            best = (float(a), float(b), float(c), sse)
    assert best is not None
    return best[:3]


AC_500_FIT = fit_ac_500_curve()


def ac_500_reference_capacity_gw(distance_km: float) -> float:
    a, b, c = AC_500_FIT
    distance_100km = max(1.0, distance_km / 100.0)
    return max(0.0, c + a * math.exp(-b * (distance_100km - 1.0)))


def build_centers() -> pd.DataFrame:
    source = pd.read_csv(CENTERS_SOURCE)
    columns = [
        "load_center_id", "province_code", "province_name_en", "province_name_zh",
        "lon", "lat", "source_scale", "source_feature_index",
        "assigned_demand_share_in_province", "assigned_demand_point_count",
    ]
    centers = source[columns].copy()
    centers = centers.rename(
        columns={"assigned_demand_share_in_province": "annual_demand_share_in_province"}
    )
    centers["load_center_method"] = "Natural_Earth_paper_replication_278"
    centers["demand_share_source"] = "2019_1km_electricity_raster_assigned_within_province"
    centers["scenario_status"] = "production_default_2030"
    centers = centers.sort_values(["province_code", "load_center_id"]).reset_index(drop=True)
    if len(centers) != 278 or not centers.load_center_id.is_unique:
        raise ValueError("Natural Earth production input must contain 278 unique centers")
    share_error = centers.groupby("province_code").annual_demand_share_in_province.sum().sub(1.0).abs()
    if share_error.max() > 1e-9:
        raise ValueError(f"Province demand shares do not close: {share_error.max()}")
    return centers


def build_vre_routes() -> pd.DataFrame:
    routes = pd.read_csv(VRE_ROUTE_SOURCE)
    columns = [
        "grid_uid", "grid_id", "province_code", "substation_id", "substation_lon",
        "substation_lat", "substation_max_voltage_kv", "load_center_id",
        "load_center_lon", "load_center_lat", "spur_distance_km", "trunk_distance_km",
        "total_connection_distance_km", "onwind_spur_distance_km",
        "onwind_trunk_distance_km", "upv_spur_distance_km", "upv_trunk_distance_km",
        "offwind_export_distance_km", "offwind_trunk_distance_km",
        "dpv_spur_distance_km", "dpv_trunk_distance_km", "route_status",
    ]
    output = routes[columns].copy().sort_values("grid_uid").reset_index(drop=True)
    if output.grid_uid.duplicated().any() or output.load_center_id.isna().any():
        raise ValueError("Every VRE grid point must have one Natural Earth route")
    return output


def build_hydro_routes(centers: pd.DataFrame) -> pd.DataFrame:
    hydro = pd.read_csv(HYDRO_SOURCE)
    substations = pd.read_csv(SUBSTATION_SOURCE)
    rows: list[dict[str, object]] = []
    for province_code, plants in hydro.groupby("province_code", sort=True):
        candidates = substations.loc[substations.province_code.eq(province_code)].reset_index(drop=True)
        if candidates.empty:
            raise ValueError(f"No eligible paper-route substation in province {province_code}")
        spur = cross_haversine_km(
            plants.lon.to_numpy(float), plants.lat.to_numpy(float),
            candidates.lon.to_numpy(float), candidates.lat.to_numpy(float),
        )
        objective = spur + candidates.trunk_distance_km.to_numpy(float)[None, :]
        selected = objective.argmin(axis=1)
        for plant, station_position, spur_km in zip(
            plants.itertuples(index=False), selected, spur[np.arange(len(plants)), selected]
        ):
            station = candidates.iloc[int(station_position)]
            rows.append(
                {
                    "hydrochn_row_id": plant.hydrochn_row_id,
                    "province_code": int(province_code),
                    "substation_id": station.substation_id,
                    "substation_lon": float(station.lon),
                    "substation_lat": float(station.lat),
                    "substation_max_voltage_kv": float(station.max_voltage_kv),
                    "load_center_id": station.load_center_id,
                    "load_center_lon": float(station.load_center_lon),
                    "load_center_lat": float(station.load_center_lat),
                    "hydro_spur_distance_km": float(spur_km),
                    "trunk_distance_km": float(station.trunk_distance_km),
                    "total_connection_distance_km": float(spur_km + station.trunk_distance_km),
                    "route_method": "minimum_hydro_spur_plus_paper_substation_trunk_within_province",
                    "route_status": "great_circle_proxy_not_engineering_route",
                }
            )
    routes = pd.DataFrame(rows).sort_values("hydrochn_row_id").reset_index(drop=True)
    if len(routes) != len(hydro) or routes.hydrochn_row_id.duplicated().any():
        raise ValueError("Hydropower route table does not cover each station exactly once")
    if not set(routes.load_center_id).issubset(set(centers.load_center_id)):
        raise ValueError("Hydropower route references unknown load centers")
    return routes


def build_edges(centers: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for province_code, group in centers.groupby("province_code", sort=True):
        group = group.reset_index(drop=True)
        if len(group) <= 1:
            continue
        distances = haversine_matrix_km(group.lon.to_numpy(float), group.lat.to_numpy(float))
        no_diagonal = distances.copy()
        np.fill_diagonal(no_diagonal, np.inf)
        mst_input = distances.copy()
        np.fill_diagonal(mst_input, 0.0)
        mst = minimum_spanning_tree(mst_input).tocoo()
        pairs = {tuple(sorted((int(i), int(j)))) for i, j in zip(mst.row, mst.col)}
        k = min(NEAREST_NEIGHBOURS, len(group) - 1)
        for i in range(len(group)):
            for j in np.argpartition(no_diagonal[i], k - 1)[:k]:
                pairs.add(tuple(sorted((i, int(j)))))
        for i, j in sorted(pairs):
            distance = float(distances[i, j])
            reference_capacity = ac_500_reference_capacity_gw(distance)
            unit_cost = (
                AC_500_SUBSTATION_YUAN_PER_KW
                + AC_500_LINE_THOUSAND_YUAN_PER_KM * distance
                / (reference_capacity * 1000.0)
            )
            from_center = group.iloc[i]
            to_center = group.iloc[j]
            rows.append(
                {
                    "intra_edge_id": f"INTRA_{int(province_code):02d}_{from_center.load_center_id}_{to_center.load_center_id}",
                    "province_code": int(province_code),
                    "from_load_center_id": from_center.load_center_id,
                    "to_load_center_id": to_center.load_center_id,
                    "distance_km": distance,
                    "technology": "AC_500kV",
                    "reference_capacity_gw": reference_capacity,
                    "unit_cost_yuan_per_kw": unit_cost,
                    "initial_capacity_gw": 0.0,
                    "candidate_method": "within_province_mst_plus_3_nearest_neighbours_geodesic",
                    "distance_validity": (
                        "soft_exception_above_1000km_AC500_source_range"
                        if distance > 1000.0 else "within_AC500_source_range"
                    ),
                }
            )
    edges = pd.DataFrame(rows).sort_values(["province_code", "intra_edge_id"]).reset_index(drop=True)
    if edges.intra_edge_id.duplicated().any() or (edges.distance_km <= 0).any():
        raise ValueError("Invalid intra-province edge table")
    return edges


def infer_initial_capacity(
    centers: pd.DataFrame,
    edges: pd.DataFrame,
    hydro_routes: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    center_initial = pd.read_csv(INITIAL_SOURCE / "load_center_initial_capacity_2025.csv")
    hydro = pd.read_csv(HYDRO_SOURCE)[["hydrochn_row_id", "existing_capacity_gw"]]
    hydro_center = (
        hydro_routes[["hydrochn_row_id", "load_center_id"]]
        .merge(hydro, on="hydrochn_row_id", how="left", validate="one_to_one")
        .groupby("load_center_id", as_index=False).existing_capacity_gw.sum()
        .rename(columns={"existing_capacity_gw": "existing_hydro_gw"})
    )
    initial = centers[["load_center_id", "province_code", "annual_demand_share_in_province"]].merge(
        center_initial[["load_center_id", "connected_vre_nameplate_gw", "existing_dpv_local_gw"]],
        on="load_center_id", how="left", validate="one_to_one",
    ).merge(hydro_center, on="load_center_id", how="left", validate="one_to_one")
    initial[["connected_vre_nameplate_gw", "existing_dpv_local_gw", "existing_hydro_gw"]] = initial[
        ["connected_vre_nameplate_gw", "existing_dpv_local_gw", "existing_hydro_gw"]
    ].fillna(0.0)
    initial["spatial_renewable_nameplate_gw"] = (
        initial.connected_vre_nameplate_gw
        + initial.existing_dpv_local_gw
        + initial.existing_hydro_gw
    )
    load = pd.read_csv(LOAD_SOURCE)
    peak = load.loc[load.year.eq(2025)].set_index("province_code").peak_demand_gw
    edge_capacity = pd.Series(0.0, index=edges.index, dtype=float)
    audit_rows: list[dict[str, object]] = []

    for province_code, nodes in initial.groupby("province_code", sort=True):
        nodes = nodes.reset_index().rename(columns={"index": "global_center_row"})
        province_edges = edges.loc[edges.province_code.eq(province_code)].copy()
        renewable = nodes.spatial_renewable_nameplate_gw.to_numpy(float)
        shares = nodes.annual_demand_share_in_province.to_numpy(float)
        province_peak = float(peak.loc[province_code])
        conventional_proxy = max(province_peak - renewable.sum(), 0.0)
        supply = renewable + shares * conventional_proxy - shares * province_peak
        export_total = max(float(renewable.sum() - province_peak), 0.0)

        if len(nodes) == 1:
            if abs(float(supply[0]) - export_total) > 1e-7:
                raise ValueError(f"Single-center 2025 balance failed for province {province_code}")
            continue

        node_position = {center_id: i for i, center_id in enumerate(nodes.load_center_id)}
        local_edge_indices = province_edges.index.to_numpy(int)
        edge_count = len(province_edges)
        node_count = len(nodes)
        variable_count = 2 * edge_count + node_count
        objective = np.zeros(variable_count, dtype=float)
        objective[:edge_count] = province_edges.distance_km.to_numpy(float)
        objective[edge_count:2 * edge_count] = province_edges.distance_km.to_numpy(float)
        # A tiny export tie-breaker favors centers with larger renewable surplus.
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
            objective,
            A_eq=balance,
            b_eq=-supply,
            bounds=bounds,
            method="highs",
            options={"dual_feasibility_tolerance": 1e-9, "primal_feasibility_tolerance": 1e-9},
        )
        if not result.success:
            raise RuntimeError(f"2025 intra-network proxy failed for {province_code}: {result.message}")
        flows = result.x[:edge_count] + result.x[edge_count:2 * edge_count]
        edge_capacity.loc[local_edge_indices] = flows
        balance_residual = balance @ result.x + supply
        audit_rows.append(
            {
                "province_code": int(province_code),
                "center_count": node_count,
                "edge_count": edge_count,
                "peak_demand_gw": province_peak,
                "spatial_renewable_nameplate_gw": float(renewable.sum()),
                "allocated_conventional_peak_proxy_gw": conventional_proxy,
                "external_export_peak_proxy_gw": export_total,
                "initial_intra_capacity_sum_gw": float(flows.sum()),
                "maximum_balance_residual_gw": float(np.abs(balance_residual).max()),
            }
        )

    edges = edges.copy()
    edges["initial_capacity_gw"] = edge_capacity.to_numpy(float)
    edges["initial_capacity_method"] = (
        "2025_simultaneous_renewable_nameplate_spatial_balance_proxy; "
        "thermal_nuclear_biomass allocated by load share"
    )
    initial["initial_capacity_role"] = "source_for_2025_intra_network_proxy_only"
    return edges, pd.DataFrame(audit_rows)


def build_readme(centers: pd.DataFrame, edges: pd.DataFrame, hydro_routes: pd.DataFrame) -> str:
    share_error = centers.groupby("province_code").annual_demand_share_in_province.sum().sub(1.0).abs().max()
    return f"""# 278个Natural Earth负荷中心正式模型输入

本目录由 `scripts/build_natural_earth_278_network.py` 自动生成。源候选文件保持不变，
本目录是2030模型实际读取的紧凑生产数据。

## 模型口径

- 负荷中心：278个，覆盖31个省级模型区域。
- 年度需求份额：由2019年1 km电力消费栅格在省内分配得到，各省份额和为1。
- 风光路线：优化格点 → 同省最优220 kV及以上变电站 → Natural Earth负荷中心。
- 水电路线：水电站 → 使spur+trunk距离最小的同省变电站 → 负荷中心。
- 省内候选网：每省MST加每节点3个最近邻，只允许省内连接，共{len(edges)}条无向边。
- 电压与成本：EES Table S20和Figure S44的AC 500 kV参数。
- 2025初始容量：同时铭牌压力下的空间平衡代理，不是观测线路额定容量。
- 年度线路利用率基准：{DESIGN_UTILIZATION_FRACTION:.0%}，需做敏感性分析。

## 关键QC

- 负荷中心数量：{len(centers)}。
- 水电站路线数量：{len(hydro_routes)}。
- 省内边数量：{len(edges)}。
- 省级需求份额最大闭合误差：{share_error:.3e}。
- 超过EES AC 500 kV 1000 km来源范围的代理边：{int(edges.distance_km.gt(1000).sum())}条。

## 重要限制

中心间线路是地理直线距离代理，不是工程走廊。年度输电层不建立中心小时潮流；
500 kV容量由年度GWh流量和显式利用率换算。2025初值只避免把全部既有省内网架
误算为2030新增投资，不能解释为真实线路容量。
"""


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    centers = build_centers()
    vre_routes = build_vre_routes()
    hydro_routes = build_hydro_routes(centers)
    edges = build_edges(centers)
    edges, initial_audit = infer_initial_capacity(centers, edges, hydro_routes)

    write_csv(centers, OUTPUT / "load_centers.csv")
    write_csv(vre_routes, OUTPUT / "vre_routes.csv")
    write_csv(hydro_routes, OUTPUT / "hydro_routes.csv")
    write_csv(edges, OUTPUT / "intra_edges.csv")
    write_csv(initial_audit, OUTPUT / "initial_capacity_2025_audit.csv")

    # Promote the already validated paper-route 2025 upstream baselines.
    initial_spur = pd.read_csv(INITIAL_SOURCE / "initial_spur_capacity_2025_paper_route.csv")
    substations = pd.read_csv(INITIAL_SOURCE / "substation_initial_capacity_2025_paper_route.csv")
    write_csv(initial_spur, OUTPUT / "initial_spur_capacity_2025.csv")
    write_csv(substations, OUTPUT / "substation_initial_capacity_2025.csv")

    readme = build_readme(centers, edges, hydro_routes)
    (OUTPUT / "README_zh.md").write_text(readme, encoding="utf-8")
    outputs = sorted(path for path in OUTPUT.iterdir() if path.is_file())
    manifest = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "scenario": "Natural_Earth_paper_replication_278",
        "status": "production_default_2030",
        "design_utilization_fraction": DESIGN_UTILIZATION_FRACTION,
        "counts": {
            "load_centers": len(centers),
            "provinces": int(centers.province_code.nunique()),
            "vre_grid_routes": len(vre_routes),
            "hydro_routes": len(hydro_routes),
            "intra_edges": len(edges),
            "long_distance_soft_exceptions": int(edges.distance_km.gt(1000).sum()),
        },
        "source_files": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in [
                CENTERS_SOURCE,
                VRE_ROUTE_SOURCE,
                SUBSTATION_SOURCE,
                INITIAL_SOURCE / "load_center_initial_capacity_2025.csv",
                INITIAL_SOURCE / "initial_spur_capacity_2025_paper_route.csv",
                INITIAL_SOURCE / "substation_initial_capacity_2025_paper_route.csv",
                HYDRO_SOURCE,
                LOAD_SOURCE,
            ]
        },
        "output_files": {
            str(path.relative_to(OUTPUT)): sha256(path)
            for path in outputs
        },
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest["counts"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
