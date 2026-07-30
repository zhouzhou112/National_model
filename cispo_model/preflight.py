"""Full-data preflight, scale estimation, and stop gates."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import numpy as np

from .config import ModelConfig
from .data import DAC_TECHS, STORAGE_TECHS, THERMAL_TECHS, VRE_TECHS, ModelData
from .flexible_load_numerics import (
    _compressed_thermal_state_mask,
    _service_effective_load_lower_bound,
)


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
    e_reverse = int(
        data.lines.preset_technology.astype(str).str.upper().eq("AC").sum()
    )
    d = len(DAC_TECHS)
    n_vre = len(data.vre_sites)
    n_hydro = len(data.hydro_stations)
    n_reservoir = int(
        data.hydro_stations.operation_type_model.eq("reservoir_storage").sum()
    )
    n_sub = len(data.substations)
    n_center = len(data.load_centers)
    n_intra = len(data.intra_load_center_edges)
    n_wave = 0 if data.wave is None else len(data.wave.sites)
    c = int((data.vre_points[config.raw["ccs_injection_field"]] > 0).sum())
    flex = config.raw["flexible_load"]
    flex_enabled = bool(config.raw["features"]["flexible_load"])
    flex_formulation = str(
        flex.get("formulation", "daily_energy_shift_v1")
    )
    flexible_variable_multiplier = 0
    flexible_daily_modules = 0
    flexible_capacity_variables = 0
    v5_service_data = None
    v5_fixed_zero_thermal_controls = 0
    v5_redundant_thermal_states = 0
    v4_formulation = flex_formulation == "service_constrained_v4"
    v5_formulation = (
        flex_formulation == "integrated_service_constrained_v5"
    )
    service_contract_formulation = v4_formulation or v5_formulation
    state_formulation = flex_formulation in {
        "state_envelope_v2",
        "comfort_envelope_v3",
    }
    if flex_enabled and service_contract_formulation:
        # Two non-negative thermal-service blocks (up/down/state), one EV fleet
        # charge/SOC/accounting block, optional V2G discharge, and annual
        # contracted-capacity decisions. V5 replaces the unused deviation
        # epigraph with a one-sided relocation epigraph and adds four firm
        # credit variables, so its hourly multiplier remains unchanged while
        # its annual capacity block doubles.
        flexible_variable_multiplier = 9 + int(bool(flex["ev_v2g"]["enabled"]))
        flexible_capacity_variables = (8 if v5_formulation else 4) * p
        if v5_formulation:
            v5_service_data = data.flexible_load_v4
            if v5_service_data is None:
                raise ValueError(
                    "V5 scale estimation requires validated flexibility inputs"
                )
            v5_fixed_zero_thermal_controls = sum(
                int(
                    np.count_nonzero(
                        v5_service_data.thermal_envelopes_gw[
                            f"{component}_{direction}"
                        ][:, :h]
                        == 0.0
                    )
                )
                for component in ("heating", "cooling")
                for direction in ("up", "down")
            )
            v5_redundant_thermal_states = 0
            for component in ("heating", "cooling"):
                control_support = (
                    v5_service_data.thermal_envelopes_gw[
                        f"{component}_up"
                    ][:, :h]
                    > 0.0
                ) | (
                    v5_service_data.thermal_envelopes_gw[
                        f"{component}_down"
                    ][:, :h]
                    > 0.0
                )
                retained_state = _compressed_thermal_state_mask(
                    control_support,
                    v5_service_data.thermal_parameters[component][
                        "retention_per_hour"
                    ],
                )
                v5_redundant_thermal_states += int(
                    retained_state.size - retained_state.sum()
                )
    elif flex_enabled:
        for component in ("heating", "cooling"):
            if bool(flex[component]["enabled"]):
                flexible_variable_multiplier += (
                    3 if state_formulation else 2
                )
                flexible_daily_modules += 1
        if bool(flex["ev_v1g"]["enabled"]):
            flexible_variable_multiplier += (
                3 if state_formulation else 2
            )
            flexible_daily_modules += 1
        if bool(flex["ev_v2g"]["enabled"]):
            flexible_variable_multiplier += 3
    flexible_variables = (
        flexible_variable_multiplier * p * h
        + flexible_capacity_variables
        - v5_fixed_zero_thermal_controls
        - v5_redundant_thermal_states
    )
    flexible_constraints = 0
    if flex_enabled and v4_formulation:
        # effective-load non-negativity (1), two thermal components each with
        # two contracted-power rows, one state-bound row and one transition
        # (8 total), and EV contract/departure/deviation/transition rows (5).
        flexible_constraints = p * h * (
            14 + int(bool(flex["ev_v2g"]["enabled"]))
        )
    elif flex_enabled and v5_formulation:
        service_data = v5_service_data
        if service_data is None:
            raise AssertionError("V5 service data was not loaded")
        components = {
            name: values[:, :h]
            for name, values in data.load_components_gw.items()
        }
        shiftable_fraction = float(
            flex["ev_v1g"]["shiftable_energy_fraction"]
        )
        effective_load_lower_bound = _service_effective_load_lower_bound(
            components=components,
            thermal_down_upper={
                component: service_data.thermal_envelopes_gw[
                    f"{component}_down"
                ][:, :h]
                for component in ("heating", "cooling")
            },
            fixed_ev_baseline=(
                (1.0 - shiftable_fraction) * components["ev"]
            ),
            ev_discharge_upper=(
                service_data.ev_availability[
                    "available_discharge_power_gw"
                ][:, :h]
                if bool(flex["ev_v2g"]["enabled"])
                else np.zeros((p, h), dtype=float)
            ),
        )
        effective_load_rows = int(
            np.count_nonzero(effective_load_lower_bound < 1e-6)
        )
        minimum_departure_rows = int(
            np.count_nonzero(
                service_data.ev_mobility[
                    "minimum_departure_energy_gwh"
                ][:, :h]
                > 0.0
            )
        )
        # Thermal service contributes 8 rows per province-hour. EV contributes
        # charge, relocation and SOC transition rows plus sparse positive
        # departure-SOC rows and an optional V2G discharge-contract row.
        # The five province-level V5 contract/firm bounds and one national
        # V2G cap are also explicit.
        flexible_constraints = (
            p * h * (11 + int(bool(flex["ev_v2g"]["enabled"])))
            + effective_load_rows
            + minimum_departure_rows
            + 5 * p
            + 1
            - v5_fixed_zero_thermal_controls
            - 2 * v5_redundant_thermal_states
        )
    elif flex_enabled:
        days = int(np.ceil(h / 24))
        if state_formulation:
            # Effective-load nonnegativity plus hourly state/queue transitions
            # and one terminal reset per province-day-module.
            flexible_constraints = (
                p * h
                + flexible_daily_modules * p * h
                + flexible_daily_modules * p * days
            )
        else:
            flexible_constraints = p * h + flexible_daily_modules * p * days
        if bool(flex["ev_v2g"]["enabled"]):
            flexible_constraints += p * h
            if flex_formulation == "comfort_envelope_v3":
                flexible_constraints += p * days + p * h

    blocks = {
        "vre_site_capacity_and_new": 2 * n_vre,
        "vre_availability_and_dispatch": 2 * p * v * h,
        "thermal_capacity_new_and_retrofit": 2 * p * k + 5 * p,
        "thermal_hourly_ruc": 5 * p * k * h,
        "storage_capacity_and_hourly": 2 * p * s + 5 * p * s * h,
        "hydro_site_capacity_and_hourly": (
            2 * n_hydro + 2 * p * h + 3 * n_reservoir * h
        ),
        "transmission_capacity_and_flow": 2 * e + (e + e_reverse) * h,
        "dac_capacity_and_capture": 3 * p * d,
        "annual_resource_accounts": 2 * p + 1,
        "capacity_margin_credited_capacity": p,
        "co2_source_sink_flow": p * c,
        "spur_and_trunk_capacity": n_vre + n_hydro + n_sub,
        "annual_load_center_network": (
            n_center * (len(VRE_TECHS) + 5) + 4 * n_intra + 5 * p
        ),
        "optional_flexible_load": flexible_variables,
        "optional_wave_energy": (
            0 if data.wave is None else 2 * n_wave + p * h + n_center
        ),
    }
    variables = int(sum(blocks.values()))
    capacity_margin_load_basis = str(
        config.raw["security"]["capacity_margin_load_basis"]
    )
    capacity_margin_constraints = p + (
        p * h
        if capacity_margin_load_basis == "effective_peak_endogenous_v1"
        else p
    )
    constraints = int(
        n_vre
        + 2 * p * v * h
        # Four simple RUC upper-bound rows are strictly implied by the
        # retained S4-24, S4-25 and S4-29 rows after domain validation.
        + 9 * p * k * h
        + 9 * p * s * h
        + 2 * p * h
        + 3 * n_reservoir * h
        + e * h
        + p * h
        + 3 * p * h
        + p * k
        + p * c
        + capacity_margin_constraints
        + n_vre
        + n_hydro
        + n_sub
        + n_center * (len(VRE_TECHS) + 5)
        + len(data.provinces) * len(VRE_TECHS)
        + 5 * len(data.provinces)
        + 2 * n_intra
        + flexible_constraints
        + (0 if data.wave is None else n_wave + p * h + n_center + p)
    )
    # Dense VRE availability is the dominant coefficient block. The remaining
    # rows use a conservative 3-coefficient structural average calibrated
    # against the accepted 24 h and 744 h monolithic builds. This is a static
    # model-memory planning estimate; barrier factorization remains a separate
    # and potentially much larger solve-time risk.
    vre_nonzeros = int(n_vre * h)
    other_nonzeros = int(max(constraints - p * v * h, 0) * 3.0)
    wave_nonzeros = 0 if data.wave is None else int(n_wave * h)
    nonzeros = vre_nonzeros + wave_nonzeros + other_nonzeros
    # Conservative planning estimate, not a Gurobi guarantee.
    memory_bytes = nonzeros * 32 + variables * 240 + constraints * 180
    estimated_memory_gb = memory_bytes / (1024**3)
    block_hours = h
    block_count = 1
    maximum_block_variables = int(
        2 * p * v * block_hours
        + 5 * p * k * block_hours
        + 5 * p * s * block_hours
        + (2 * p + 3 * n_reservoir) * block_hours
        + (e + e_reverse) * block_hours
        + flexible_variables
    )
    maximum_block_nonzeros = int(
        n_vre * block_hours + maximum_block_variables * 3.0
    )
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

    expected_boundary = (
        2025
        if config.planning_year == config.planning_years[0]
        else config.planning_years[config.planning_years.index(config.planning_year) - 1]
    )
    check(
        "planning_boundary",
        config.boundary_year == expected_boundary,
        config.boundary_year,
        str(expected_boundary),
    )
    check(
        "sequential_planning_year",
        config.planning_year in config.planning_years,
        config.planning_year,
        str(config.planning_years),
    )
    check("full_hours", config.hours == 8760, config.hours, "8760")
    check(
        "planning_state_boundary",
        config.boundary_year == 2025 or data.planning_state.root is not None,
        str(data.planning_state.root) if data.planning_state.root else None,
        "no state for initial 2025 boundary; checksummed prior state thereafter",
    )
    check("province_count", len(data.provinces) == 31, len(data.provinces), "31")
    check("load_shape", data.load_gw.shape == (31, 8760), str(data.load_gw.shape), "(31, 8760)")
    check("load_finite", np.isfinite(data.load_gw).all(), bool(np.isfinite(data.load_gw).all()), "True")
    check("load_nonnegative", float(data.load_gw.min()) >= 0, float(data.load_gw.min()), ">= 0 GW")
    expected_component_shape = (31, 8760)
    for component in ("base_residual", "heating", "cooling", "ev"):
        values = data.load_components_gw[component]
        check(
            f"load_component_{component}_shape",
            values.shape == expected_component_shape,
            str(values.shape),
            str(expected_component_shape),
        )
        check(
            f"load_component_{component}_nonnegative",
            bool(np.isfinite(values).all() and values.min() >= 0.0),
            float(values.min()),
            ">= 0 GW and finite",
        )
    load_component_error = float(
        np.abs(data.load_gw - sum(data.load_components_gw.values())).max()
    )
    check(
        "load_component_closure",
        load_component_error <= 1e-9,
        load_component_error,
        "<= 1e-9 GW",
    )
    flexible_formulation = str(
        config.raw["flexible_load"].get("formulation")
    )
    if (
        bool(config.raw["features"]["flexible_load"])
        and flexible_formulation
        in {
            "service_constrained_v4",
            "integrated_service_constrained_v5",
        }
    ):
        service_contract = data.flexible_load_v4
        contract_label = (
            "v5"
            if flexible_formulation == "integrated_service_constrained_v5"
            else "v4"
        )
        check(
            f"{contract_label}_calibration_contract_loaded",
            service_contract is not None,
            service_contract is not None,
            "validated province-year thermal, EV and cost inputs",
        )
        if service_contract is not None:
            expected_service_shape = (len(data.provinces), config.hours)
            for label, values in {
                **service_contract.thermal_envelopes_gw,
                "heating_availability": (
                    service_contract.thermal_availability["heating"]
                ),
                "cooling_availability": (
                    service_contract.thermal_availability["cooling"]
                ),
                **service_contract.ev_availability,
                **service_contract.ev_mobility,
            }.items():
                check(
                    f"{contract_label}_{label}_shape",
                    values.shape == expected_service_shape,
                    str(values.shape),
                    str(expected_service_shape),
                )
    check("vre_sites", len(data.vre_sites) > 0, len(data.vre_sites), "> 0")
    check("vre_bounds", bool((data.vre_sites.capacity_floor_gw <= data.vre_sites.capacity_upper_gw + 1e-9).all()), int((data.vre_sites.capacity_floor_gw > data.vre_sites.capacity_upper_gw + 1e-9).sum()), "0 violations")
    check("vre_cf_mapping", bool(data.vre_sites.cf_grid_id.ge(0).all()), int(data.vre_sites.cf_grid_id.lt(0).sum()), "0 unresolved")
    cross_technology_cf = (
        data.vre_sites.technology.isin({"onwind", "offwind"})
        & data.vre_sites.cf_source_technology.eq("pv")
    ) | (
        data.vre_sites.technology.isin({"upv", "dpv"})
        & data.vre_sites.cf_source_technology.eq("mixed_wind")
    )
    check(
        "vre_cf_cross_technology_fallback",
        not bool(cross_technology_cf.any()),
        int(cross_technology_cf.sum()),
        "0 wind-to-PV or PV-to-wind mappings",
    )
    pv_fallback = data.vre_sites.cf_fallback_method.eq(
        "nearest_same_province_land_pv_grid"
    )
    source_is_land = data.vre_sites.cf_grid_id.map(
        data.vre_points.set_index("grid_id").is_land
    )
    non_land_pv_fallback = pv_fallback & ~source_is_land.eq(1)
    check(
        "vre_cf_pv_fallback_uses_land_grid",
        not bool(non_land_pv_fallback.any()),
        int(non_land_pv_fallback.sum()),
        "0 non-land PV fallback source grids",
    )
    check("thermal_floor_rows", len(data.thermal_floor) == 31 * 10, len(data.thermal_floor), "310")
    check("nuclear_floor_rows", len(data.nuclear_floor) == 31, len(data.nuclear_floor), "31")
    check("nuclear_upper_rows", len(data.nuclear_upper) == 31, len(data.nuclear_upper), "31")
    nuclear_bounds = data.nuclear_floor[["province_code", "capacity_floor_gw"]].merge(
        data.nuclear_upper[["province_code", "capacity_upper_gw"]],
        on="province_code",
        validate="one_to_one",
    )
    check(
        "nuclear_capacity_bounds",
        bool(
            nuclear_bounds.capacity_floor_gw.le(
                nuclear_bounds.capacity_upper_gw + 1e-9
            ).all()
        ),
        int(
            nuclear_bounds.capacity_floor_gw.gt(
                nuclear_bounds.capacity_upper_gw + 1e-9
            ).sum()
        ),
        "0 floor-above-upper violations",
    )
    check("ruc_technology_rows", set(data.ruc.technology) == set(THERMAL_TECHS), sorted(data.ruc.technology), "11 technologies")
    check("storage_rows", set(data.storage.technology) == set(STORAGE_TECHS), sorted(data.storage.technology), "battery and phs")
    check(
        "phs_bound_rows",
        len(data.storage_bounds) == 31,
        len(data.storage_bounds),
        "31 province rows for the planning year",
    )
    check(
        "battery_bound_rows",
        len(data.battery_bounds) == 31,
        len(data.battery_bounds),
        "31 province rows for the planning year",
    )
    check(
        "battery_capacity_floor_nonnegative",
        bool(data.battery_bounds.capacity_floor_gw.ge(-1e-9).all()),
        float(data.battery_bounds.capacity_floor_gw.min()),
        ">= 0 GW",
    )
    check(
        "phs_bounds",
        bool(
            data.storage_bounds.capacity_floor_gw.le(
                data.storage_bounds.capacity_upper_gw + 1e-9
            ).all()
        ),
        int(
            data.storage_bounds.capacity_floor_gw.gt(
                data.storage_bounds.capacity_upper_gw + 1e-9
            ).sum()
        ),
        "0 floor-above-upper violations",
    )
    checks.append(
        {
            "check": "phs_national_capacity_bounds_gw",
            "status": "INFO",
            "value": {
                "floor": float(data.storage_bounds.capacity_floor_gw.sum()),
                "upper": float(data.storage_bounds.capacity_upper_gw.sum()),
            },
            "expected": "GHT 2026 operating floor and year-available project upper",
        }
    )
    check("allowed_candidate_corridors", len(data.lines) == 411, len(data.lines), "411 allowed rows from the 465-pair matrix")
    check("hydro_station_rows", len(data.hydro_stations) == 2030, len(data.hydro_stations), "2030")
    check("biomass_rows", len(data.biomass) == 31, len(data.biomass), "31")
    check(
        "biomass_capacity_bound_rows",
        len(data.biomass_capacity_bounds) == 31,
        len(data.biomass_capacity_bounds),
        "31",
    )
    check(
        "biomass_capacity_upper_nonnegative",
        bool(data.biomass_capacity_bounds.capacity_upper_gw.ge(-1e-9).all()),
        float(data.biomass_capacity_bounds.capacity_upper_gw.min()),
        ">= 0 GW",
    )
    check("dac_rows", len(data.dac) == 4, len(data.dac), "4")
    check("carbon_active", bool(data.carbon.constraint_active), bool(data.carbon.constraint_active), "True")
    check("csp_source_gap_explicit", not config.raw["features"]["csp"], config.raw["features"]["csp"], "False until source exists", "SOFT")
    check(
        "wave_feature_data_contract",
        bool(config.raw["features"]["wave_energy"]) == (data.wave is not None),
        {
            "feature_enabled": bool(config.raw["features"]["wave_energy"]),
            "wave_data_loaded": data.wave is not None,
        },
        "feature flag and loaded data agree",
    )
    if data.wave is not None:
        check(
            "wave_existing_grid_uid_unique",
            data.wave.sites.grid_uid.is_unique,
            int(data.wave.sites.grid_uid.nunique()),
            str(len(data.wave.sites)),
        )
        existing_grid_uids = set(data.vre_points.grid_uid.astype(str))
        check(
            "wave_grid_uid_is_existing_optimization_grid",
            set(data.wave.sites.grid_uid.astype(str)).issubset(existing_grid_uids),
            int(data.wave.sites.grid_uid.isin(existing_grid_uids).sum()),
            str(len(data.wave.sites)),
        )
        check(
            "wave_existing_grid_is_marine",
            bool(data.wave.sites.is_land.eq(0).all()),
            int(data.wave.sites.is_land.eq(0).sum()),
            str(len(data.wave.sites)),
        )
        point_lookup = data.vre_points.set_index("grid_uid")
        matched_points = point_lookup.loc[
            data.wave.sites.grid_uid.astype(str)
        ].reset_index()
        coordinate_difference = np.maximum(
            np.abs(
                matched_points.lon.to_numpy(dtype=float)
                - data.wave.sites.lon.to_numpy(dtype=float)
            ),
            np.abs(
                matched_points.lat.to_numpy(dtype=float)
                - data.wave.sites.lat.to_numpy(dtype=float)
            ),
        )
        check(
            "wave_coordinates_equal_existing_grid",
            bool((coordinate_difference <= 1e-9).all()),
            float(coordinate_difference.max()),
            "<= 1e-9 degrees",
        )
        route_lookup = data.vre_load_center_routes.set_index("grid_uid")
        matched_routes = route_lookup.loc[
            data.wave.sites.grid_uid.astype(str)
        ].reset_index()
        exact_routes = (
            matched_routes.load_center_id.astype(str).to_numpy()
            == data.wave.sites.load_center_id.astype(str).to_numpy()
        ) & (
            matched_routes.substation_id.astype(str).to_numpy()
            == data.wave.sites.substation_id.astype(str).to_numpy()
        )
        check(
            "wave_routes_equal_existing_grid_routes",
            bool(exact_routes.all()),
            int(exact_routes.sum()),
            str(len(data.wave.sites)),
        )
        check(
            "wave_capacity_upper_nonnegative",
            bool(data.wave.sites.capacity_upper_gw.ge(0.0).all()),
            float(data.wave.sites.capacity_upper_gw.min()),
            ">= 0 GW",
        )
        check(
            "wave_province_route_valid",
            set(data.wave.sites.province_code.astype(int)).issubset(
                set(data.province_codes.astype(int))
            ),
            sorted(set(data.wave.sites.province_code.astype(int))),
            "subset of active province codes",
        )
        check(
            "wave_load_center_route_valid",
            set(data.wave.sites.load_center_id.astype(str)).issubset(
                set(data.load_centers.load_center_id.astype(str))
            ),
            int(data.wave.sites.load_center_id.nunique()),
            "all routed centers known",
        )
    check(
        "phs_representation_gap_explicit",
        "phs_water_pairing" in config.raw["explicit_data_gaps"],
        "phs_water_pairing" in config.raw["explicit_data_gaps"],
        "province-level representation explicitly registered",
        "SOFT",
    )
    expected_load_center_count = int(
        config.raw["load_center_network"]["expected_load_center_count"]
    )
    expected_intra_edge_count = int(
        config.raw["load_center_network"]["expected_intra_edge_count"]
    )
    check(
        "configured_load_center_count",
        len(data.load_centers) == expected_load_center_count,
        len(data.load_centers),
        str(expected_load_center_count),
    )
    check(
        "configured_load_center_provinces",
        data.load_centers.province_code.nunique() == 31,
        data.load_centers.province_code.nunique(),
        "31",
    )
    center_share_error = (
        data.load_centers.groupby("province_code").annual_demand_share_in_province.sum()
        .sub(1.0).abs().max()
    )
    check(
        "configured_load_center_annual_demand_share_closure",
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
    check("hydro_cascade_nodes", len(data.hydro_cascade_nodes) == 142, len(data.hydro_cascade_nodes), "142")
    check("hydro_cascade_edges", len(data.hydro_cascade_edges) == 124, len(data.hydro_cascade_edges), "124")
    if not data.hydro_cascade_nodes.empty:
        cascade_ids: set[str] = set()
        for value in data.hydro_cascade_nodes.hydrochn_row_ids.dropna():
            cascade_ids.update(part.strip() for part in str(value).split(";") if part.strip())
        cascade_hydro = data.hydro_stations.loc[
            data.hydro_stations.hydrochn_row_id.astype(str).isin(cascade_ids)
        ]
        non_reservoir = int(
            cascade_hydro.operation_type_model.ne("reservoir_storage").sum()
        )
        check("hydro_cascade_station_rows", len(cascade_hydro) == 146, len(cascade_hydro), "146")
        check("hydro_cascade_all_reservoir", non_reservoir == 0, non_reservoir, "0")
    if not data.hydro_cascade_edges.empty:
        check(
            "hydro_cascade_lag_nonnegative",
            bool(data.hydro_cascade_edges.travel_lag_h.ge(0).all()),
            float(data.hydro_cascade_edges.travel_lag_h.min()),
            ">= 0 h",
        )
        low_lag = int(
            data.hydro_cascade_edges.lag_quality_flag.eq("LOW_CORRELATION").sum()
        )
        check(
            "hydro_cascade_low_lag_correlation_edges",
            low_lag == 0,
            low_lag,
            "0 low-correlation lag estimates",
            "SOFT",
        )
        max_bound_lag = int(
            data.hydro_cascade_edges.lag_quality_flag.eq(
                "MAX_LAG_BOUND_SELECTED"
            ).sum()
        )
        check(
            "hydro_cascade_max_lag_bound_edges",
            max_bound_lag == 0,
            max_bound_lag,
            "0 lag estimates selected at the configured maximum bound",
            "SOFT",
        )
    known_centers = set(data.load_centers.load_center_id.astype(str))
    intra = data.intra_load_center_edges
    check(
        "configured_intra_load_center_edge_count",
        len(intra) == expected_intra_edge_count,
        len(intra),
        str(expected_intra_edge_count),
    )
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
        "boundary_interpretation": (
            f"{config.boundary_year} is the inherited input state; no optimization "
            "is performed for the boundary inside this solve"
        ),
        "planning_interpretation": (
            f"{config.planning_year} is one sequential 8760-hour expansion decision "
            f"representing {config.boundary_year}-{config.planning_year} change"
        ),
        "scale_estimate": asdict(scale),
        "checks": checks,
        "status_counts": {
            status: sum(row["status"] == status for row in checks)
            for status in ("PASS", "WARN", "INFO", "HARD_FAIL")
        },
        "explicit_data_gaps": config.raw["explicit_data_gaps"],
        "planning_state": {
            "path": str(data.planning_state.root) if data.planning_state.root else None,
            "format": data.planning_state.metadata.get("format"),
            "source_planning_year": data.planning_state.metadata.get("planning_year"),
            "cohort_rows": int(len(data.planning_state.cohorts)),
        },
    }
    report["status"] = "PASS" if report["status_counts"]["HARD_FAIL"] == 0 else "HARD_FAIL"
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
