"""Full-data preflight, scale estimation, and stop gates."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import numpy as np

from .config import ModelConfig
from .data import DAC_TECHS, STORAGE_TECHS, THERMAL_TECHS, VRE_TECHS, ModelData


@dataclass
class ScaleEstimate:
    variables: int
    constraints: int
    nonzeros: int
    estimated_memory_gb: float
    dominant_blocks: dict[str, int]
    block_count: int
    maximum_block_hours: int
    maximum_block_variables: int
    maximum_block_nonzeros: int
    estimated_peak_block_memory_gb: float


def estimate_full_model_scale(
    config: ModelConfig,
    data: ModelData,
    hours: int | None = None,
) -> ScaleEstimate:
    p = len(data.provinces)
    h = config.hours if hours is None else int(hours)
    if h <= 0 or h > config.hours:
        raise ValueError("scale-estimate hours must be in [1, 8760]")
    v = len(VRE_TECHS)
    k = len(THERMAL_TECHS)
    s = len(STORAGE_TECHS)
    e = len(data.lines)
    d = len(DAC_TECHS)
    n_vre = len(data.vre_sites)
    n_hydro = len(data.hydro_stations)
    n_reservoir = int(
        data.hydro_stations.operation_type_model.eq("reservoir_storage").sum()
    )
    n_sub = len(data.substations)
    n_center = len(data.load_centers)
    n_intra = len(data.intra_load_center_edges)
    c = int((data.vre_points[config.raw["ccs_injection_field"]] > 0).sum())

    blocks = {
        "vre_site_capacity_and_new": 2 * n_vre,
        "vre_availability_and_dispatch": 2 * p * v * h,
        "thermal_capacity_and_new": 2 * p * k,
        "thermal_hourly_ruc": 6 * p * k * h,
        "storage_capacity_and_hourly": 2 * p * s + 7 * p * s * h,
        "hydro_site_capacity_and_hourly": (
            2 * n_hydro + 2 * p * h + 3 * n_reservoir * h
        ),
        "transmission_capacity_and_flow": 2 * e + 2 * e * h,
        "dac_capacity_and_capture": 2 * p * d,
        "co2_source_sink_flow": p * c,
        "spur_and_trunk_capacity": n_vre + n_hydro + n_sub,
        "annual_load_center_network": (
            n_center * (len(VRE_TECHS) + 5) + 4 * n_intra + 3 * p
        ),
    }
    variables = int(sum(blocks.values()))
    constraints = int(
        n_vre
        + 2 * p * v * h
        + 13 * p * k * h
        + 11 * p * s * h
        + 2 * p * h
        + 3 * n_reservoir * h
        + e * h
        + p * h
        + 3 * p * h
        + p * k
        + p * c
        + n_vre
        + n_hydro
        + n_sub
        + n_center * (len(VRE_TECHS) + 5)
        + len(data.provinces) * len(VRE_TECHS)
        + 6 * len(data.provinces)
        + 2 * n_intra
    )
    # Dense VRE availability is the dominant coefficient block. Other blocks
    # are sparse with approximately 5-12 coefficients per row.
    vre_nonzeros = int(n_vre * h)
    other_nonzeros = int(max(constraints - p * v * h, 0) * 8)
    nonzeros = vre_nonzeros + other_nonzeros
    # Conservative planning estimate, not a Gurobi guarantee.
    memory_bytes = nonzeros * 32 + variables * 240 + constraints * 180
    estimated_memory_gb = memory_bytes / (1024**3)
    block_hours = h
    block_count = 1
    maximum_block_variables = int(
        2 * p * v * block_hours
        + 6 * p * k * block_hours
        + 7 * p * s * block_hours
        + (2 * p + 3 * n_reservoir) * block_hours
        + 2 * e * block_hours
    )
    maximum_block_nonzeros = int(n_vre * block_hours + maximum_block_variables * 8)
    block_memory_bytes = (
        maximum_block_nonzeros * 32
        + maximum_block_variables * 240
        + maximum_block_variables * 1.5 * 180
    )
    return ScaleEstimate(
        variables=variables,
        constraints=constraints,
        nonzeros=nonzeros,
        estimated_memory_gb=round(estimated_memory_gb, 2),
        dominant_blocks=blocks,
        block_count=block_count,
        maximum_block_hours=block_hours,
        maximum_block_variables=maximum_block_variables,
        maximum_block_nonzeros=maximum_block_nonzeros,
        estimated_peak_block_memory_gb=round(block_memory_bytes / (1024**3), 2),
    )


def run_preflight(config: ModelConfig, data: ModelData, output_path: Path | None = None) -> dict:
    checks: list[dict] = []

    def check(name: str, condition: bool, value: object, expected: str, severity: str = "HARD") -> None:
        if condition:
            status = "PASS"
        else:
            status = "HARD_FAIL" if severity == "HARD" else "WARN"
        checks.append({"check": name, "status": status, "value": value, "expected": expected})

    check("planning_boundary", config.boundary_year == 2025, config.boundary_year, "2025")
    check("first_planning_year", config.planning_year == 2030, config.planning_year, "2030")
    check("full_hours", config.hours == 8760, config.hours, "8760")
    check("province_count", len(data.provinces) == 31, len(data.provinces), "31")
    check("load_shape", data.load_gw.shape == (31, 8760), str(data.load_gw.shape), "(31, 8760)")
    check("load_finite", np.isfinite(data.load_gw).all(), bool(np.isfinite(data.load_gw).all()), "True")
    check("load_nonnegative", float(data.load_gw.min()) >= 0, float(data.load_gw.min()), ">= 0 GW")
    check("vre_sites", len(data.vre_sites) > 0, len(data.vre_sites), "> 0")
    check("vre_bounds", bool((data.vre_sites.capacity_floor_gw <= data.vre_sites.capacity_upper_gw + 1e-9).all()), int((data.vre_sites.capacity_floor_gw > data.vre_sites.capacity_upper_gw + 1e-9).sum()), "0 violations")
    check("vre_cf_mapping", bool(data.vre_sites.cf_grid_id.ge(0).all()), int(data.vre_sites.cf_grid_id.lt(0).sum()), "0 unresolved")
    check("thermal_floor_rows", len(data.thermal_floor) == 31 * 10, len(data.thermal_floor), "310")
    check("nuclear_floor_rows", len(data.nuclear_floor) == 31, len(data.nuclear_floor), "31")
    check("ruc_technology_rows", set(data.ruc.technology) == set(THERMAL_TECHS), sorted(data.ruc.technology), "11 technologies")
    check("storage_rows", set(data.storage.technology) == set(STORAGE_TECHS), sorted(data.storage.technology), "battery and phs")
    check("allowed_candidate_corridors", len(data.lines) == 411, len(data.lines), "411 allowed rows from the 465-pair matrix")
    check("hydro_station_rows", len(data.hydro_stations) == 2030, len(data.hydro_stations), "2030")
    check("biomass_rows", len(data.biomass) == 31, len(data.biomass), "31")
    check("dac_rows", len(data.dac) == 4, len(data.dac), "4")
    check("carbon_active", bool(data.carbon.constraint_active), bool(data.carbon.constraint_active), "True")
    check("csp_source_gap_explicit", not config.raw["features"]["csp"], config.raw["features"]["csp"], "False until source exists", "SOFT")
    check("phs_floor_gap_explicit", "existing_phs" in config.raw["explicit_data_gaps"], "existing_phs" in config.raw["explicit_data_gaps"], "explicitly registered", "SOFT")
    check("natural_earth_load_center_count", len(data.load_centers) == 278, len(data.load_centers), "278")
    check(
        "natural_earth_load_center_provinces",
        data.load_centers.province_code.nunique() == 31,
        data.load_centers.province_code.nunique(),
        "31",
    )
    center_share_error = (
        data.load_centers.groupby("province_code").annual_demand_share_in_province.sum()
        .sub(1.0).abs().max()
    )
    check(
        "natural_earth_annual_demand_share_closure",
        center_share_error <= 1e-9,
        float(center_share_error),
        "<= 1e-9",
    )
    check(
        "vre_load_center_route_coverage",
        not set(data.vre_sites.grid_uid).difference(data.vre_load_center_routes.grid_uid),
        len(set(data.vre_sites.grid_uid).difference(data.vre_load_center_routes.grid_uid)),
        "0 missing active VRE sites",
    )
    check(
        "hydro_load_center_route_coverage",
        not set(data.hydro_stations.hydrochn_row_id).difference(
            data.hydro_load_center_routes.hydrochn_row_id
        ),
        len(set(data.hydro_stations.hydrochn_row_id).difference(
            data.hydro_load_center_routes.hydrochn_row_id
        )),
        "0 missing hydropower stations",
    )
    known_centers = set(data.load_centers.load_center_id.astype(str))
    intra = data.intra_load_center_edges
    endpoint_valid = (
        set(intra.from_load_center_id.astype(str)).issubset(known_centers)
        and set(intra.to_load_center_id.astype(str)).issubset(known_centers)
    )
    check("intra_load_center_endpoints", endpoint_valid, endpoint_valid, "all endpoints known")
    center_province = data.load_centers.set_index("load_center_id").province_code
    same_province = (
        intra.from_load_center_id.map(center_province).to_numpy()
        == intra.to_load_center_id.map(center_province).to_numpy()
    ).all()
    check("intra_load_center_same_province", bool(same_province), bool(same_province), "True")
    check(
        "intra_load_center_edge_costs",
        bool((intra.unit_cost_yuan_per_kw > 0).all()),
        float(intra.unit_cost_yuan_per_kw.min()),
        "> 0 yuan/kW",
    )
    check(
        "intra_load_center_initial_capacity",
        bool((intra.initial_capacity_gw >= 0).all()),
        float(intra.initial_capacity_gw.min()),
        ">= 0 GW",
    )
    check(
        "intra_load_center_long_distance_proxy",
        int(intra.distance_km.gt(1000).sum()) == 0,
        int(intra.distance_km.gt(1000).sum()),
        "0 AC500 edges beyond 1000 km source range",
        "SOFT",
    )

    scale = estimate_full_model_scale(config, data)
    stop_threshold = float(config.raw["construction"]["stop_before_build_if_estimated_memory_gb_exceeds"])
    check(
        "selected_architecture",
        config.raw["construction"]["architecture"] == "full_year_monolithic_lp",
        config.raw["construction"]["architecture"],
        "full_year_monolithic_lp",
    )
    check(
        "monolithic_memory_gate",
        scale.estimated_memory_gb <= stop_threshold,
        scale.estimated_memory_gb,
        f"<= {stop_threshold} GB configured build limit",
    )
    checks.append({
        "check": "server_memory_requirement",
        "status": "INFO",
        "value": scale.estimated_memory_gb,
        "expected": "run only when server available memory passes the runtime gate",
    })

    report = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "configuration": str(config.path),
        "boundary_interpretation": "2025 is input state only; no 2025 optimization solve",
        "planning_interpretation": "2030 is the first 8760-hour expansion decision representing 2025-2030 change",
        "scale_estimate": asdict(scale),
        "checks": checks,
        "status_counts": {
            status: sum(row["status"] == status for row in checks)
            for status in ("PASS", "WARN", "INFO", "HARD_FAIL")
        },
        "explicit_data_gaps": config.raw["explicit_data_gaps"],
    }
    report["status"] = "PASS" if report["status_counts"]["HARD_FAIL"] == 0 else "HARD_FAIL"
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
