"""Run structural and numerical smoke tests on the generated CISPO data package."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from netCDF4 import Dataset

from data_package_common import write_output_manifest


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EXPECTED_PROVINCES = 31
EXPECTED_YEARS = [2025, 2030, 2040, 2050, 2060]


class Checks:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def check(self, name: str, condition: bool, value: object, expected: str) -> None:
        self.rows.append(
            {
                "check": name,
                "status": "PASS" if bool(condition) else "FAIL",
                "value": value,
                "expected": expected,
            }
        )

    def require_all(self) -> None:
        failures = [row for row in self.rows if row["status"] == "FAIL"]
        if failures:
            details = "\n".join(f"- {row['check']}: {row['value']} ({row['expected']})" for row in failures)
            raise AssertionError(f"Data-package smoke test failed:\n{details}")


def json_default(value: object) -> object:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def read_zarr_cf_meta(store: Path) -> dict:
    metadata = json.loads((store / ".zmetadata").read_text(encoding="utf-8"))["metadata"]
    array = metadata["cf/.zarray"]
    dimensions = metadata["cf/.zattrs"]["_ARRAY_DIMENSIONS"]
    sizes = dict(zip(dimensions, array["shape"]))
    return {"dimensions": dimensions, "sizes": sizes}


def main() -> None:
    checks = Checks()
    defaults = json.loads((DATA / "model_defaults.json").read_text(encoding="utf-8"))
    checks.check("default_region_count", defaults["regions"] == EXPECTED_PROVINCES, defaults["regions"], "31")
    checks.check("default_years", defaults["planning_years"] == EXPECTED_YEARS, defaults["planning_years"], str(EXPECTED_YEARS))

    provinces = pd.read_csv(DATA / "sets" / "provinces.csv")
    checks.check("province_rows", len(provinces) == 31, len(provinces), "31")
    checks.check("inner_mongolia_single_region", provinces.province_name_en.eq("Inner Mongolia").sum() == 1, int(provinces.province_name_en.eq("Inner Mongolia").sum()), "1")
    model_years = pd.read_csv(DATA / "sets" / "model_years.csv")
    base_row = model_years.loc[model_years.year.eq(2025)].iloc[0]
    checks.check("base_year_role", base_row.year_role == "fixed_base_calibration" and not bool(base_row.capacity_expansion_enabled), f"{base_row.year_role}, expansion={base_row.capacity_expansion_enabled}", "fixed base with expansion disabled")

    points = pd.read_csv(DATA / "vre" / "optimization_points.csv")
    checks.check("optimization_point_rows", len(points) == 16609, len(points), "16609")
    checks.check("optimization_point_provinces", points.province_code.nunique() == 31, points.province_code.nunique(), "31")
    checks.check("optimization_point_unique_key", points.grid_uid.is_unique, points.grid_uid.nunique(), str(len(points)))
    capacity_columns = [column for column in points if column.startswith(("existing_", "remaining_", "pmax_"))]
    minimum_capacity = float(points[capacity_columns].min().min())
    checks.check("vre_capacity_nonnegative", minimum_capacity >= -1e-9, minimum_capacity, ">= 0 GW")
    max_bound_error = 0.0
    for scenario in ("C", "B", "O"):
        for technology in ("onwind", "offwind", "upv", "dpv"):
            error = points[f"existing_{technology}_gw"] - points[f"pmax_{technology}_{scenario}_gw"]
            max_bound_error = max(max_bound_error, float(error.max()))
    checks.check("vre_existing_within_pmax", max_bound_error <= 1e-9, max_bound_error, "<= 0 GW")

    correction = pd.read_csv(DATA / "vre" / "province_correction_audit.csv")
    correction_pairs = correction.groupby(["province_code_before", "province_code_after"]).size().to_dict()
    checks.check("shandong_correction_rows", len(correction) == 61, len(correction), "61")
    checks.check("shandong_correction_pair", correction_pairs == {(46, 37): 61}, str(correction_pairs), "{(46, 37): 61}")
    land_correction = pd.read_csv(DATA / "vre" / "land_province_correction_audit.csv")
    checks.check("land_correction_rows", len(land_correction) == 43, len(land_correction), "43")
    checks.check("land_correction_unique_key", land_correction.grid_uid.is_unique, land_correction.grid_uid.nunique(), "43")
    checks.check("land_correction_land_only", land_correction.is_land.eq(1).all(), int(land_correction.is_land.eq(1).sum()), "43")
    checks.check(
        "land_correction_changes_code",
        land_correction.province_code_before.ne(land_correction.province_code_after).all(),
        int(land_correction.province_code_before.ne(land_correction.province_code_after).sum()),
        "43",
    )
    production_codes = points.set_index("grid_uid").province_code
    applied_code = land_correction.grid_uid.map(production_codes)
    applied_mismatch_count = int(applied_code.ne(land_correction.province_code_after).sum())
    checks.check("land_correction_applied_to_production", applied_mismatch_count == 0, applied_mismatch_count, "0 mismatches")
    expected_extreme_corrections = {
        "G000033483": (33, 54),
        "G000034618": (33, 54),
        "G000019631": (15, 22),
        "G000043120": (44, 53),
    }
    actual_extreme_corrections = {
        row.grid_uid: (int(row.province_code_before), int(row.province_code_after))
        for row in land_correction.loc[
            land_correction.grid_uid.isin(expected_extreme_corrections)
        ].itertuples(index=False)
    }
    checks.check(
        "land_correction_extreme_examples",
        actual_extreme_corrections == expected_extreme_corrections,
        str(actual_extreme_corrections),
        str(expected_extreme_corrections),
    )
    land_capacity_impact = pd.read_csv(
        DATA / "vre" / "land_province_correction_capacity_impact.csv"
    )
    impact_closure = land_capacity_impact.groupby("capacity_metric").delta_gw.sum().abs()
    checks.check(
        "land_correction_capacity_impact_nonempty",
        not land_capacity_impact.empty,
        len(land_capacity_impact),
        "> 0 province-metric changes",
    )
    checks.check(
        "land_correction_capacity_national_closure",
        float(impact_closure.max()) <= 1e-9,
        float(impact_closure.max()),
        "<= 1e-9 GW",
    )
    excluded = pd.read_csv(DATA / "vre" / "out_of_scope_points.csv")
    checks.check("out_of_scope_rows", len(excluded) == 130, len(excluded), "130")
    checks.check("out_of_scope_code", set(excluded.province_code.unique()) == {71}, sorted(excluded.province_code.unique()), "[71]")

    cf_index = pd.read_csv(DATA / "vre" / "hourly_cf_index.csv")
    current_cf = cf_index.loc[cf_index.year.eq(int(defaults["default_weather_year"]))]
    checks.check("default_cf_technologies", set(current_cf.technology) == {"mixed_wind", "onshore_wind", "offshore_wind", "pv"}, sorted(current_cf.technology), "four VRE stores")
    zarr_issues = []
    for row in current_cf.itertuples(index=False):
        meta = read_zarr_cf_meta(Path(row.zarr_path))
        if set(meta["dimensions"]) != {"time", "grid_id"}:
            zarr_issues.append(f"{row.technology}: dimensions={meta['dimensions']}")
        if meta["sizes"]["time"] != 8760:
            zarr_issues.append(f"{row.technology}: time={meta['sizes']['time']}")
        if row.time_steps != meta["sizes"]["time"] or row.grid_count != meta["sizes"]["grid_id"]:
            zarr_issues.append(f"{row.technology}: index dimensions do not match metadata")
    checks.check("default_zarr_metadata", not zarr_issues, "; ".join(zarr_issues) or "valid", "time=8760 and indexed dimensions match")

    load_columns = ["province_code", "year", "hour_index", "demand_gw", "base_residual_gw", "heating_gw", "cooling_gw", "ev_gw"]
    load = pd.read_csv(DATA / "load" / "hourly_load_2025_2060.csv.gz", usecols=load_columns)
    expected_load_rows = 31 * 5 * 8760
    checks.check("load_rows", len(load) == expected_load_rows, len(load), str(expected_load_rows))
    checks.check("load_unique_index", not load.duplicated(["province_code", "year", "hour_index"]).any(), int(load.duplicated(["province_code", "year", "hour_index"]).sum()), "0 duplicates")
    load_group_sizes = load.groupby(["province_code", "year"]).size()
    checks.check("load_group_count", len(load_group_sizes) == 155, len(load_group_sizes), "155")
    checks.check("load_hours_per_group", load_group_sizes.eq(8760).all(), f"min={load_group_sizes.min()}, max={load_group_sizes.max()}", "8760")
    component_sum = load[["base_residual_gw", "heating_gw", "cooling_gw", "ev_gw"]].sum(axis=1)
    load_closure = float((load.demand_gw - component_sum).abs().max())
    checks.check("load_component_closure", load_closure <= 1e-9, load_closure, "<= 1e-9 GW")

    thermal = pd.read_csv(DATA / "thermal" / "capacity_floor_by_year.csv")
    checks.check("thermal_rows", len(thermal) == 31 * 10 * 5, len(thermal), "1550")
    thermal_ordered = thermal.sort_values(["province_code", "technology", "year"])
    thermal_increase = thermal_ordered.groupby(["province_code", "technology"]).capacity_floor_gw.diff().max()
    checks.check("thermal_floor_nonincreasing", thermal_increase <= 1e-9, float(thermal_increase), "<= 0 GW")
    thermal_existing = pd.read_csv(DATA / "thermal" / "existing_capacity_2025.csv")
    base_floor_total = float(thermal.loc[thermal.year.eq(2025), "capacity_floor_gw"].sum())
    existing_total = float(thermal_existing.existing_capacity_gw_2025.sum())
    checks.check("thermal_base_floor_equals_existing", abs(base_floor_total - existing_total) <= 1e-9, base_floor_total - existing_total, "0 GW")

    nuclear = pd.read_csv(DATA / "thermal" / "nuclear_capacity_floor_by_year.csv")
    nuclear_totals = nuclear.groupby("year").capacity_floor_gw.sum().round(6).to_dict()
    expected_nuclear = {2025: 60.898, 2030: 106.764, 2040: 146.308, 2050: 185.812, 2060: 185.812}
    checks.check("nuclear_rows", len(nuclear) == 31 * 5, len(nuclear), "155")
    checks.check("nuclear_pipeline_totals", nuclear_totals == expected_nuclear, str(nuclear_totals), str(expected_nuclear))

    hydro = pd.read_csv(DATA / "hydro" / "hydro_stations.csv")
    checks.check("hydro_rows", len(hydro) == 2030, len(hydro), "2030")
    hydro_bound_error = float((hydro.existing_capacity_gw - hydro.capacity_potential_gw).max())
    checks.check("hydro_existing_within_potential", hydro_bound_error <= 1e-9, hydro_bound_error, "<= 0 GW")
    checks.check("hydro_classified", hydro.operation_type_model.notna().all(), int(hydro.operation_type_model.isna().sum()), "0 missing")
    cascade_nodes = pd.read_csv(DATA / "hydro" / "cascade_topology_nodes.csv")
    cascade_edges = pd.read_csv(DATA / "hydro" / "cascade_topology_edges.csv")
    checks.check("hydro_cascade_nodes", len(cascade_nodes) == 142, len(cascade_nodes), "142")
    checks.check("hydro_cascade_edges", len(cascade_edges) == 124, len(cascade_edges), "124")
    checks.check(
        "hydro_cascade_lag_present",
        cascade_edges.travel_lag_h.notna().all() and cascade_edges.travel_lag_h.ge(0).all(),
        int(cascade_edges.travel_lag_h.isna().sum()),
        "non-negative lag for every edge",
    )
    cascade_ids = set()
    for value in cascade_nodes.hydrochn_row_ids.dropna():
        cascade_ids.update(part.strip() for part in str(value).split(";") if part.strip())
    cascade_hydro = hydro.loc[hydro.hydrochn_row_id.isin(cascade_ids)]
    checks.check("hydro_cascade_station_rows", len(cascade_hydro) == 146, len(cascade_hydro), "146")
    checks.check(
        "hydro_cascade_all_reservoir",
        cascade_hydro.operation_type_model.eq("reservoir_storage").all(),
        int(cascade_hydro.operation_type_model.ne("reservoir_storage").sum()),
        "0 non-reservoir cascade stations",
    )

    timeseries = pd.read_csv(DATA / "hydro" / "timeseries_index.csv")
    timeseries_issues = []
    for row in timeseries.itertuples(index=False):
        try:
            path = Path(row.path)
            if path.suffix.lower() == ".nc":
                with Dataset(path) as dataset:
                    if not dataset.dimensions or not dataset.variables:
                        timeseries_issues.append(f"{row.dataset}: empty dimensions or variables")
            elif path.suffix.lower() == ".json":
                parsed = json.loads(path.read_text(encoding="utf-8"))
                if not parsed:
                    timeseries_issues.append(f"{row.dataset}: empty JSON object")
            else:
                timeseries_issues.append(f"{row.dataset}: unsupported file type {path.suffix}")
        except Exception as exc:  # pragma: no cover - diagnostic path
            timeseries_issues.append(f"{row.dataset}: {exc}")
    checks.check("hydro_timeseries_parseability", not timeseries_issues, "; ".join(timeseries_issues) or "valid", "all indexed NetCDF and JSON files parse")

    biomass = pd.read_csv(DATA / "biomass" / "fuel_potential_by_province_year.csv")
    checks.check("biomass_rows", len(biomass) == 31 * 5, len(biomass), "155")
    checks.check("biomass_province_year_unique", not biomass.duplicated(["province_code", "year"]).any(), int(biomass.duplicated(["province_code", "year"]).sum()), "0 duplicates")
    checks.check("biomass_positive", biomass.thermcal_gj_per_year.gt(0).all(), float(biomass.thermcal_gj_per_year.min()), "> 0 GJ/yr")

    carbon = pd.read_csv(DATA / "carbon" / "emissions_limits_by_scenario.csv")
    checks.check("carbon_scenario_rows", len(carbon) == 4 * 5, len(carbon), "20")
    default_carbon = carbon.loc[carbon.scenario.eq("Base_-550Mt")].set_index("year")
    expected_carbon = {2030: 4000.0, 2040: 1300.0, 2050: -100.0, 2060: -550.0}
    actual_carbon = default_carbon.loc[list(expected_carbon), "emissions_limit_mtco2_per_year"].to_dict()
    checks.check("carbon_default_path", actual_carbon == expected_carbon, str(actual_carbon), str(expected_carbon))
    checks.check("carbon_2025_unconstrained", not bool(default_carbon.loc[2025, "constraint_active"]) and pd.isna(default_carbon.loc[2025, "emissions_limit_mtco2_per_year"]), f"active={default_carbon.loc[2025, 'constraint_active']}", "inactive and no limit")

    ruc = pd.read_csv(DATA / "technology" / "thermal_nuclear_ruc_parameters.csv")
    checks.check("technology_ruc_rows", len(ruc) == 11, len(ruc), "11")
    dac = pd.read_csv(DATA / "technology" / "dac_parameters_by_year.csv")
    checks.check("dac_rows", len(dac) == 4 * 5, len(dac), "20")
    checks.check("dac_energy_positive", dac.total_electricity_with_heat_pump_gwh_per_mtco2.gt(0).all(), float(dac.total_electricity_with_heat_pump_gwh_per_mtco2.min()), "> 0 GWh/MtCO2")
    checks.check("dac_unique_technology_year", not dac.duplicated(["technology", "year"]).any(), int(dac.duplicated(["technology", "year"]).sum()), "0 duplicates")
    emission_factors = pd.read_csv(DATA / "technology" / "emission_factors_by_year.csv")
    checks.check("emission_factor_rows", len(emission_factors) == 3 * 5, len(emission_factors), "15")

    capex = pd.read_csv(DATA / "technology" / "technology_capex_by_year.csv")
    checks.check("technology_capex_rows", len(capex) == 19 * 4, len(capex), "76")
    checks.check("technology_capex_unique", not capex.duplicated(["technology", "year"]).any(), int(capex.duplicated(["technology", "year"]).sum()), "0 duplicates")
    checks.check("technology_capex_technology_count", capex.technology.nunique() == 19, capex.technology.nunique(), "19")
    checks.check("technology_capex_years", sorted(capex.year.unique().tolist()) == [2030, 2040, 2050, 2060], sorted(capex.year.unique().tolist()), "2030, 2040, 2050, 2060")
    capex_lookup = capex.set_index(["technology", "year"]).capex_yuan_per_kw
    checks.check("technology_capex_onwind_2030", np.isclose(capex_lookup.loc[("onwind", 2030)], 5500.0), float(capex_lookup.loc[("onwind", 2030)]), "5500 yuan/kW")
    checks.check("technology_capex_nuclear_2040", np.isclose(capex_lookup.loc[("nuclear", 2040)], 18300.0), float(capex_lookup.loc[("nuclear", 2040)]), "18300 yuan/kW")
    checks.check("technology_capex_battery_2060", np.isclose(capex_lookup.loc[("battery", 2060)], 2400.0), float(capex_lookup.loc[("battery", 2060)]), "2400 yuan/kW")

    fuel = pd.read_csv(DATA / "technology" / "province_fuel_prices.csv")
    checks.check("province_fuel_price_rows", len(fuel) == 31, len(fuel), "31")
    checks.check("province_fuel_price_unique", fuel.province_code.is_unique, fuel.province_code.nunique(), "31 unique province codes")
    checks.check("province_fuel_missing_coal", set(fuel.loc[fuel.coal_yuan_per_gj.isna(), "province_code"]) == {11, 54}, sorted(fuel.loc[fuel.coal_yuan_per_gj.isna(), "province_code"].tolist()), "Beijing=11 and Tibet=54")
    checks.check("province_fuel_gas_complete", fuel.gas_yuan_per_gj.notna().all(), int(fuel.gas_yuan_per_gj.isna().sum()), "0 missing")
    inner = fuel.loc[fuel.province_code.eq(15)].iloc[0]
    checks.check("inner_mongolia_coal_mean", np.isclose(inner.coal_usd_per_gj, 2.56) and np.isclose(inner.coal_yuan_per_gj, 17.664), f"{inner.coal_usd_per_gj}, {inner.coal_yuan_per_gj}", "2.56 USD/GJ, 17.664 yuan/GJ")
    checks.check("inner_mongolia_gas_mean", np.isclose(inner.gas_usd_per_gj, 7.51) and np.isclose(inner.gas_yuan_per_gj, 51.819), f"{inner.gas_usd_per_gj}, {inner.gas_yuan_per_gj}", "7.51 USD/GJ, 51.819 yuan/GJ")
    fuel_cost = pd.read_csv(DATA / "technology" / "province_fuel_generation_cost_by_year.csv")
    checks.check("province_fuel_generation_cost_rows", len(fuel_cost) == 31 * 5 * 8, len(fuel_cost), "1240")
    unavailable_coal = fuel_cost.loc[fuel_cost.fuel.eq("coal") & fuel_cost.province_code.isin([11, 54])]
    checks.check("missing_coal_technologies_disabled", (~unavailable_coal.dispatch_allowed).all() and (~unavailable_coal.new_capacity_allowed).all(), int(unavailable_coal.dispatch_allowed.sum() + unavailable_coal.new_capacity_allowed.sum()), "0 allowed rows")
    checks.check("gas_technologies_available", fuel_cost.loc[fuel_cost.fuel.eq("gas"), "dispatch_allowed"].all(), int((~fuel_cost.loc[fuel_cost.fuel.eq("gas"), "dispatch_allowed"]).sum()), "0 disabled rows")

    unresolved = pd.read_csv(DATA / "technology" / "unresolved_parameters.csv")
    hard_objective = unresolved.status.eq("HARD_FAIL_FOR_LONG_TERM_OBJECTIVE").sum()
    checks.check("unresolved_long_term_objective_register", hard_objective == 0, int(hard_objective), "0 hard fails after CapEx and fuel-price integration")
    network_hard = unresolved.status.eq("HARD_FAIL_FOR_NETWORK_CAPACITY").sum()
    checks.check("unresolved_network_capacity_register", network_hard == 0, int(network_hard), "0 after explicit 2025 proxy adoption")
    station_proxy = unresolved.status.eq("RESOLVED_PROXY_INITIAL_ONLY").sum()
    checks.check("substation_initial_capacity_proxy_register", station_proxy == 1, int(station_proxy), "1 explicit proxy-only record")
    trunk_cost_hard = unresolved.status.eq("HARD_FAIL_FOR_TRUNK_COST").sum()
    checks.check("unresolved_trunk_cost_register", trunk_cost_hard == 0, int(trunk_cost_hard), "0 after city load-center geodesic proxy")
    trunk_proxy = unresolved.status.eq("RESOLVED_GEODESIC_PROXY").sum()
    checks.check("trunk_geodesic_proxy_register", trunk_proxy == 1, int(trunk_proxy), "1 explicit geodesic proxy record")

    substations = pd.read_csv(DATA / "grid" / "substations_osm_220kv_plus.csv")
    checks.check("eligible_substation_rows", len(substations) == 6294, len(substations), "6294")
    checks.check("eligible_substation_voltage", substations.max_voltage_kv.ge(220).all(), float(substations.max_voltage_kv.min()), ">= 220 kV")
    checks.check("eligible_substation_provinces", substations.province_code.nunique() == 31, substations.province_code.nunique(), "31")
    connections = pd.read_csv(DATA / "grid" / "grid_connection_by_point.csv")
    checks.check("grid_connection_rows", len(connections) == 16609, len(connections), "16609")
    checks.check("grid_connection_unique_point", connections.grid_uid.is_unique, connections.grid_uid.nunique(), "16609")
    checks.check("grid_connection_nonnegative", connections.nearest_substation_distance_km.ge(0).all(), float(connections.nearest_substation_distance_km.min()), ">= 0 km")
    checks.check("grid_connection_distance_band_complete", connections.distance_quality_band.notna().all(), int(connections.distance_quality_band.isna().sum()), "0 missing")
    land_connection = connections.loc[connections.is_land.eq(1)]
    checks.check("dpv_spur_zero", land_connection.dpv_spur_distance_km.eq(0).all(), float(land_connection.dpv_spur_distance_km.abs().max()), "0 km")
    substation_province = substations.set_index("substation_id").province_code
    assigned_province = connections.substation_id.map(substation_province)
    checks.check("grid_connection_same_province", assigned_province.eq(connections.province_code).all(), int((~assigned_province.eq(connections.province_code)).sum()), "0 mismatches")

    spur_initial = pd.read_csv(DATA / "grid" / "initial_spur_capacity_2025.csv")
    checks.check("initial_spur_positive_rows", len(spur_initial) == 8645, len(spur_initial), "8645 positive technology-point rows")
    checks.check("initial_spur_capacity_nonnegative", spur_initial.initial_spur_capacity_gw.ge(0).all(), float(spur_initial.initial_spur_capacity_gw.min()), ">= 0 GW")
    connected_spur = spur_initial.loc[spur_initial.connection_required]
    checks.check("initial_spur_nameplate_stress", np.allclose(connected_spur.initial_spur_capacity_gw, connected_spur.existing_capacity_gw), float((connected_spur.initial_spur_capacity_gw - connected_spur.existing_capacity_gw).abs().max()), "0 GW difference")
    dpv_spur = spur_initial.loc[spur_initial.technology.eq("dpv")]
    checks.check("initial_dpv_excluded_from_spur", dpv_spur.initial_spur_capacity_gw.eq(0).all() and (~dpv_spur.connection_required).all(), int((dpv_spur.initial_spur_capacity_gw.ne(0) | dpv_spur.connection_required).sum()), "0 invalid rows")
    fallback_counts = spur_initial.cf_fallback_method.value_counts().to_dict()
    checks.check("initial_capacity_cf_fallback_audit", fallback_counts.get("same_grid_mixed_wind_for_land_sea_mask_mismatch", 0) == 45 and fallback_counts.get("nearest_same_province_land_pv_grid", 0) == 29, str(fallback_counts), "45 mixed-wind and 29 nearest-land-PV fallbacks")
    pv_fallback = spur_initial.loc[spur_initial.cf_fallback_method.eq("nearest_same_province_land_pv_grid")]
    checks.check("initial_capacity_pv_fallback_distance", pv_fallback.cf_fallback_distance_km.le(60).all(), float(pv_fallback.cf_fallback_distance_km.max()), "<= 60 km")

    station_initial = pd.read_csv(DATA / "grid" / "substation_initial_capacity_2025.csv")
    checks.check("substation_initial_capacity_rows", len(station_initial) == len(substations), len(station_initial), "6294")
    checks.check("substation_initial_capacity_unique", station_initial.substation_id.is_unique, station_initial.substation_id.nunique(), "6294 unique")
    checks.check("substation_connected_nameplate_total", np.isclose(station_initial.connected_vre_nameplate_gw.sum(), 1310.0), float(station_initial.connected_vre_nameplate_gw.sum()), "1310 GW")
    checks.check("substation_dpv_local_total", np.isclose(station_initial.existing_dpv_local_gw.sum(), 530.0), float(station_initial.existing_dpv_local_gw.sum()), "530 GW")
    checks.check("substation_initial_nameplate_stress", np.allclose(station_initial.initial_trunk_capacity_gw, station_initial.connected_vre_nameplate_gw) and np.allclose(station_initial.initial_substation_vre_interface_capacity_gw, station_initial.connected_vre_nameplate_gw), float((station_initial.initial_trunk_capacity_gw - station_initial.connected_vre_nameplate_gw).abs().max()), "0 GW difference")
    checks.check("substation_paper_peak_bounded_by_nameplate", (station_initial.paper_proxy_coincident_peak_trunk_gw <= station_initial.connected_vre_nameplate_gw + 1e-6).all(), float((station_initial.paper_proxy_coincident_peak_trunk_gw - station_initial.connected_vre_nameplate_gw).max()), "<= 1e-6 GW")
    checks.check("substation_paper_peak_bounded_by_point_peaks", (station_initial.paper_proxy_coincident_peak_trunk_gw <= station_initial.sum_point_paper_spur_capacity_gw + 1e-6).all(), float((station_initial.paper_proxy_coincident_peak_trunk_gw - station_initial.sum_point_paper_spur_capacity_gw).max()), "<= 1e-6 GW")
    province_initial = pd.read_csv(DATA / "grid" / "province_initial_intra_grid_capacity_2025.csv")
    checks.check("province_initial_intra_grid_rows", len(province_initial) == 31, len(province_initial), "31")
    checks.check("province_initial_capacity_closure", np.isclose(province_initial.initial_trunk_capacity_gw.sum(), 1310.0), float(province_initial.initial_trunk_capacity_gw.sum()), "1310 GW")

    load_centers = pd.read_csv(DATA / "grid" / "city_load_centers.csv")
    checks.check("city_load_center_rows", len(load_centers) == 337, len(load_centers), "337")
    checks.check("city_load_center_unique", load_centers.load_center_id.is_unique, load_centers.load_center_id.nunique(), "337 unique")
    checks.check("city_load_center_provinces", load_centers.province_code.nunique() == 31, load_centers.province_code.nunique(), "31")
    checks.check("city_load_center_observed_weights", load_centers.electricity_weight_method.eq("observed_2022_city_table").sum() == 296, int(load_centers.electricity_weight_method.eq("observed_2022_city_table").sum()), "296")
    checks.check("city_load_center_imputed_weights", load_centers.electricity_weight_method.eq("imputed_province_power_per_urban_population").sum() == 41, int(load_centers.electricity_weight_method.eq("imputed_province_power_per_urban_population").sum()), "41")
    city_share_closure = load_centers.groupby("province_code").annual_city_power_share_in_province.sum().sub(1.0).abs()
    checks.check("city_load_center_share_closure", city_share_closure.max() <= 1e-9, float(city_share_closure.max()), "<= 1e-9")
    imputed_city = pd.read_csv(DATA / "grid" / "city_load_center_imputed_weights.csv")
    checks.check("city_load_center_imputation_audit_rows", len(imputed_city) == 41, len(imputed_city), "41")

    trunk_mapping = pd.read_csv(DATA / "grid" / "substation_to_load_center.csv")
    checks.check("substation_load_center_rows", len(trunk_mapping) == 6294, len(trunk_mapping), "6294")
    checks.check("substation_load_center_unique", trunk_mapping.substation_id.is_unique, trunk_mapping.substation_id.nunique(), "6294 unique")
    checks.check("substation_load_center_distance_nonnegative", trunk_mapping.trunk_distance_km.ge(0).all(), float(trunk_mapping.trunk_distance_km.min()), ">= 0 km")
    checks.check("substation_load_center_distance_p95", trunk_mapping.trunk_distance_km.quantile(0.95) <= 150, float(trunk_mapping.trunk_distance_km.quantile(0.95)), "<= 150 km")
    checks.check("substation_load_center_distance_max", trunk_mapping.trunk_distance_km.max() <= 450, float(trunk_mapping.trunk_distance_km.max()), "<= 450 km")
    checks.check("substation_initial_trunk_distance_complete", station_initial.trunk_distance_km.notna().all(), int(station_initial.trunk_distance_km.isna().sum()), "0 missing")
    checks.check("substation_initial_route_status", station_initial.load_center_route_status.eq("great_circle_proxy_not_engineering_route").all(), int((~station_initial.load_center_route_status.eq("great_circle_proxy_not_engineering_route")).sum()), "0 invalid")
    proxy_validation = pd.read_csv(DATA / "grid" / "load_center_proxy_validation.csv")
    checks.check("load_center_proxy_validation_rows", len(proxy_validation) == 2, len(proxy_validation), "2")
    checks.check("substation_proxy_not_primary", proxy_validation.recommended_role.eq("validation_and_sensitivity_only").all(), int((~proxy_validation.recommended_role.eq("validation_and_sensitivity_only")).sum()), "0 invalid")
    checks.check("substation_proxy_correlation_moderate", proxy_validation.spearman_vs_annual_city_power_share.between(0.3, 0.7).all(), proxy_validation.spearman_vs_annual_city_power_share.tolist(), "both between 0.3 and 0.7")

    corridors = pd.read_csv(DATA / "transmission" / "candidate_corridors.csv")
    checks.check("candidate_corridor_rows", len(corridors) == 465, len(corridors), "465")
    checks.check("candidate_corridor_unique_pair", not corridors.duplicated(["from_province_code", "to_province_code"]).any(), int(corridors.duplicated(["from_province_code", "to_province_code"]).sum()), "0 duplicates")

    status_counts = pd.Series([row["status"] for row in checks.rows]).value_counts().to_dict()
    report = {
        "status": "PASS" if status_counts.get("FAIL", 0) == 0 else "FAIL",
        "checks_total": len(checks.rows),
        "status_counts": status_counts,
        "checks": checks.rows,
    }
    report_path = DATA / "smoke_test_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=json_default) + "\n",
        encoding="utf-8",
    )
    write_output_manifest(DATA)
    print(json.dumps({"report": str(report_path), **report}, ensure_ascii=False, indent=2, default=json_default))
    checks.require_all()


if __name__ == "__main__":
    main()
