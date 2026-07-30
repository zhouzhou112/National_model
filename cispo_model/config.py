"""Configuration loading and validation for the CISPO optimization model."""
from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "optimization_2030.json"
ALLOWED_SCENARIO_OVERRIDE_ROOTS = {
    "features",
    "flexible_load",
    "hydro",
    "security",
    "storage_design",
}
ANALYSIS_ROLES = {
    "BASELINE",
    "CENTRAL_COUNTERFACTUAL",
    "SENSITIVITY",
    "LEGACY_VALIDATION",
    "TEMPLATE",
}


@dataclass(frozen=True)
class ModelConfig:
    path: Path
    raw: dict[str, Any]
    scenario_path: Path | None = None
    solver_path: Path | None = None
    formulation_path: Path | None = None

    @property
    def boundary_year(self) -> int:
        return int(self.raw["boundary_year"])

    @property
    def planning_year(self) -> int:
        return int(self.raw["planning_year"])

    @property
    def weather_year(self) -> int:
        return int(self.raw["weather_year"])

    @property
    def weather_time_alignment(self) -> str:
        return str(self.raw["weather_time_alignment"])

    @property
    def weather_source_years(self) -> tuple[int, ...]:
        if self.weather_time_alignment == "beijing_natural_year_drop_feb29_v1":
            return (self.weather_year - 1, self.weather_year)
        if self.weather_time_alignment == "source_utc_year_first_8760_v1":
            return (self.weather_year,)
        raise ValueError(
            f"Unsupported weather_time_alignment={self.weather_time_alignment!r}"
        )

    @property
    def hours(self) -> int:
        return int(self.raw["hours"])

    @property
    def vre_scenario(self) -> str:
        return str(self.raw["vre_scenario"])

    def horizon(self, name: str) -> dict[str, Any]:
        horizons = self.raw["construction"]["horizons"]
        if name not in horizons:
            raise ValueError(
                f"Unknown horizon {name!r}; choose one of {', '.join(sorted(horizons))}"
            )
        return dict(horizons[name])

    @property
    def planning_years(self) -> tuple[int, ...]:
        return tuple(int(year) for year in self.raw["planning_sequence"]["years"])

    def for_planning_year(self, planning_year: int) -> "ModelConfig":
        """Return a validated year-specific view of the sequential configuration."""
        planning_year = int(planning_year)
        if planning_year not in self.planning_years:
            raise ValueError(
                f"planning_year must be one of {', '.join(map(str, self.planning_years))}"
            )
        position = self.planning_years.index(planning_year)
        boundary_year = (
            int(self.raw["planning_sequence"]["initial_boundary_year"])
            if position == 0
            else self.planning_years[position - 1]
        )
        raw = deepcopy(self.raw)
        raw["boundary_year"] = boundary_year
        raw["planning_year"] = planning_year
        raw["planning_interval_years"] = planning_year - boundary_year
        config = ModelConfig(
            self.path,
            raw,
            self.scenario_path,
            self.solver_path,
            self.formulation_path,
        )
        config.validate()
        return config

    def validate(self) -> None:
        sequence = self.raw.get("planning_sequence", {})
        years = tuple(int(year) for year in sequence.get("years", ()))
        if years != (2030, 2040, 2050, 2060):
            raise ValueError("planning_sequence.years must be [2030, 2040, 2050, 2060]")
        if int(sequence.get("initial_boundary_year", 0)) != 2025:
            raise ValueError("planning_sequence.initial_boundary_year must remain 2025")
        if self.planning_year not in years:
            raise ValueError("planning_year must be one of the configured sequential years")
        position = years.index(self.planning_year)
        expected_boundary = 2025 if position == 0 else years[position - 1]
        if self.boundary_year != expected_boundary:
            raise ValueError(
                f"planning year {self.planning_year} requires boundary year {expected_boundary}"
            )
        if self.planning_year <= self.boundary_year:
            raise ValueError("planning_year must be later than boundary_year")
        if int(self.raw.get("planning_interval_years", 0)) != (
            self.planning_year - self.boundary_year
        ):
            raise ValueError("planning_interval_years must equal planning_year - boundary_year")
        if sequence.get("state_format") != "capacity_cohorts_v2":
            raise ValueError("planning_sequence.state_format must be capacity_cohorts_v2")
        if sequence.get("retirement_rule") != "active_when_planning_year_lt_retire_year":
            raise ValueError(
                "planning_sequence.retirement_rule must remain active_when_planning_year_lt_retire_year"
            )
        existing_vre_retirement = sequence.get("existing_vre_retirement", {})
        if not isinstance(existing_vre_retirement, dict):
            raise ValueError("planning_sequence.existing_vre_retirement must be a mapping")
        retirement_mode = str(existing_vre_retirement.get("mode", ""))
        supported_retirement_modes = {
            "fixed_floor_v1",
            "cohort_survival_v1",
            # Compatibility alias for pre-M1 artifacts only.  New production
            # configuration must use the explicit cohort-survival name.
            "observed_cohort_boundary_censored_v1",
        }
        if retirement_mode not in supported_retirement_modes:
            raise ValueError(
                "existing_vre_retirement.mode must be fixed_floor_v1 or "
                "cohort_survival_v1"
            )
        if retirement_mode != "fixed_floor_v1" and not str(
            existing_vre_retirement.get("cohort_file", "")
        ):
            raise ValueError(
                "cohort_survival_v1 requires an explicit existing-VRE cohort_file"
            )
        if int(existing_vre_retirement.get("baseline_year", 0)) != 2025:
            raise ValueError("existing_vre_retirement.baseline_year must remain 2025")
        if retirement_mode != "fixed_floor_v1":
            if existing_vre_retirement.get("unknown_start_year_policy") != (
                "boundary_censored_2025_v1"
            ):
                raise ValueError(
                    "existing VRE unknown-start policy must remain boundary_censored_2025_v1"
                )
            if existing_vre_retirement.get("site_rebuild_policy") != (
                "retain_same_site_technical_upper_v1"
            ):
                raise ValueError(
                    "existing VRE site rebuild policy must retain the technical upper bound"
                )
        if self.hours != 8760:
            raise ValueError("Production configuration must use all 8760 hours")
        if self.weather_year not in range(2020, 2026):
            raise ValueError("weather_year must be covered by the 2020-2025 CF index")
        if self.weather_time_alignment not in {
            "beijing_natural_year_drop_feb29_v1",
            "source_utc_year_first_8760_v1",
        }:
            raise ValueError("Unsupported weather_time_alignment")
        if (
            self.weather_time_alignment
            == "beijing_natural_year_drop_feb29_v1"
            and self.weather_year <= 2020
        ):
            raise ValueError(
                "Strict Beijing-year alignment requires the preceding indexed UTC year"
            )
        if self.vre_scenario not in {"C", "B", "O"}:
            raise ValueError("vre_scenario must be one of C, B, O")
        scientific_case = self.raw.get("scientific_case", {})
        if scientific_case.get("contract_version") != "scientific_case_v1":
            raise ValueError("scientific_case.contract_version must be scientific_case_v1")
        if scientific_case.get("case_id") != "base_2024_vre_wave_on_flex_off_v1":
            raise ValueError("Production Base scientific_case.case_id is not explicit")
        weather_bundle = scientific_case.get("weather_bundle", {})
        if weather_bundle.get("contract_version") != "hybrid_weather_bundle_v1":
            raise ValueError("scientific_case.weather_bundle must be explicit")
        parameter_registry = scientific_case.get("parameter_registry", {})
        if parameter_registry.get("path") != "config/critical_parameter_registry.csv":
            raise ValueError("scientific_case.parameter_registry.path must be explicit")
        if not self.raw["strict_load_balance"]:
            raise ValueError("Production configuration requires strict load balance")
        if self.raw.get("capacity_bound_profile") != (
            "V0719_nuclear_biomass_battery_corrected"
        ):
            raise ValueError(
                "Production requires the V0719 nuclear/biomass/battery capacity-bound profile"
            )
        if self.raw["allow_debug_slacks"]:
            raise ValueError("Debug slacks must be disabled in production configuration")
        security = self.raw.get("security", {})
        capacity_margin = float(security.get("capacity_margin_fraction", -1.0))
        if not 0.0 <= capacity_margin <= 1.0:
            raise ValueError("security.capacity_margin_fraction must be in [0, 1]")
        capacity_margin_load_basis = str(
            security.get("capacity_margin_load_basis", "")
        )
        if capacity_margin_load_basis not in {
            "baseline_peak_v1",
            "effective_peak_endogenous_v1",
            "firm_flexibility_derated_v1",
        }:
            raise ValueError(
                "security.capacity_margin_load_basis must be "
                "baseline_peak_v1, effective_peak_endogenous_v1, or "
                "firm_flexibility_derated_v1"
            )
        reliability = self.raw.get("flexible_load", {}).get(
            "reliability_treatment", {}
        )
        legacy_baseline_flag = bool(
            reliability.get("planning_capacity_margin_uses_baseline_peak", True)
        )
        if legacy_baseline_flag != (
            capacity_margin_load_basis
            in {"baseline_peak_v1", "firm_flexibility_derated_v1"}
        ):
            raise ValueError(
                "flexible_load.reliability_treatment legacy baseline-peak flag "
                "must agree with security.capacity_margin_load_basis"
            )
        if (
            capacity_margin_load_basis
            in {"effective_peak_endogenous_v1", "firm_flexibility_derated_v1"}
            and not bool(self.raw["features"].get("flexible_load", False))
        ):
            raise ValueError(
                f"{capacity_margin_load_basis} requires features.flexible_load=true"
            )
        resolve_minimum_system_inertia_seconds(security)
        if self.raw["features"].get("csp", False):
            raise ValueError("CSP cannot be enabled until site potential and hourly profiles exist")
        storage_design = self.raw.get("storage_design", {})
        phs_energy_mode = storage_design.get("phs_energy_capacity_mode")
        if phs_energy_mode not in {
            "fixed_duration_v1",
            "independent_power_energy_v1",
        }:
            raise ValueError(
                "storage_design.phs_energy_capacity_mode must be "
                "fixed_duration_v1 or independent_power_energy_v1"
            )
        phs_existing_duration = float(
            storage_design.get("phs_existing_duration_h", 0.0)
        )
        phs_min_duration = float(
            storage_design.get("phs_new_duration_min_h", 0.0)
        )
        phs_max_duration = float(
            storage_design.get("phs_new_duration_max_h", 0.0)
        )
        phs_reference_duration = float(
            storage_design.get("phs_reference_duration_h", 0.0)
        )
        if min(
            phs_existing_duration,
            phs_min_duration,
            phs_max_duration,
            phs_reference_duration,
        ) <= 0.0:
            raise ValueError("All PHS duration parameters must be positive")
        if phs_min_duration > phs_existing_duration + 1e-12:
            raise ValueError(
                "PHS minimum duration cannot exceed the inherited-fleet duration"
            )
        if phs_min_duration > phs_max_duration:
            raise ValueError("PHS minimum duration cannot exceed maximum duration")
        closure_tolerance = float(
            storage_design.get(
                "phs_reference_capex_closure_tolerance_fraction",
                0.0,
            )
        )
        if not 0.0 < closure_tolerance <= 1e-3:
            raise ValueError(
                "PHS reference-CAPEX closure tolerance must be in (0, 1e-3]"
            )
        if phs_energy_mode == "independent_power_energy_v1":
            expected_years = {str(year) for year in years}
            for key in (
                "phs_power_capex_yuan_per_kw_by_planning_year",
                "phs_energy_capex_yuan_per_kwh_by_planning_year",
            ):
                values = storage_design.get(key)
                if not isinstance(values, dict) or set(values) != expected_years:
                    raise ValueError(
                        f"storage_design.{key} must contain exactly "
                        f"{sorted(expected_years)}"
                    )
                try:
                    numeric_values = [
                        float(value) for value in values.values()
                    ]
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"storage_design.{key} values must be sourced positive numbers"
                    ) from exc
                if any(value <= 0.0 for value in numeric_values):
                    raise ValueError(
                        f"storage_design.{key} values must be positive"
                    )
        if "wave_energy" not in self.raw.get("features", {}):
            raise ValueError("features.wave_energy must be explicit")
        intra_grid = self.raw.get("network", {}).get("intra_grid_vre_connection", {})
        if intra_grid.get("spur_rule") != "site_full_weather_max_cf_v1":
            raise ValueError("intra-grid spur rule must be site_full_weather_max_cf_v1")
        if intra_grid.get("trunk_rule") != (
            "cispo_potential_weighted_equivalent_peak_cf_v1"
        ):
            raise ValueError(
                "intra-grid trunk rule must be cispo_potential_weighted_equivalent_peak_cf_v1"
            )
        if intra_grid.get("initial_vre_interface_rule") != (
            "same_design_rule_observed_2025_v1"
        ):
            raise ValueError(
                "intra-grid initial VRE interface must use the same observed-2025 design rule"
            )
        if intra_grid.get("existing_interface_reuse") != (
            "proxy_reused_independent_of_generator_cohort_v1"
        ):
            raise ValueError(
                "intra-grid existing-interface reuse policy is not explicit"
            )
        wave = self.raw.get("wave_energy", {})
        if wave.get("contract_version") != "wave_existing_grid_v2":
            raise ValueError(
                "wave_energy.contract_version must be wave_existing_grid_v2"
            )
        if not 0.0 <= float(wave.get("potential_fraction", -1.0)) <= 1.0:
            raise ValueError("wave_energy.potential_fraction must be in [0, 1]")
        if float(wave.get("eur_to_cny", 0.0)) <= 0.0:
            raise ValueError("wave_energy.eur_to_cny must be positive")
        if int(wave.get("time_reference_year", 0)) <= 0:
            raise ValueError("wave_energy.time_reference_year must be explicit")
        if not 0.0 <= float(wave.get("capacity_credit", -1.0)) <= 1.0:
            raise ValueError("wave_energy.capacity_credit must be in [0, 1]")
        if not 0.0 <= float(
            wave.get("reserve_requirement_fraction", -1.0)
        ) <= 1.0:
            raise ValueError(
                "wave_energy.reserve_requirement_fraction must be in [0, 1]"
            )
        if wave.get("connection_treatment") != (
            "independent_cost_adders_no_shared_offwind_export"
        ):
            raise ValueError(
                "The first wave implementation requires independent cost adders "
                "and no shared offshore-wind export capacity"
            )
        allowed_wave_scenarios = {"conservative", "medium", "aggressive"}
        for planning_year in years:
            year_key = str(planning_year)
            if year_key not in wave.get("scenario_by_planning_year", {}):
                raise ValueError(
                    f"wave_energy.scenario_by_planning_year lacks {year_key}"
                )
            if (
                str(wave["scenario_by_planning_year"][year_key]).lower()
                not in allowed_wave_scenarios
            ):
                raise ValueError(
                    "Wave scenario must be conservative, medium, or aggressive"
                )
            profile_year = int(
                wave.get("profile_year_by_planning_year", {}).get(year_key, 0)
            )
            cost_year = int(
                wave.get("cost_year_by_planning_year", {}).get(year_key, 0)
            )
            if profile_year not in {2030, 2040, 2050}:
                raise ValueError(
                    "Wave profile year must be one of 2030, 2040, 2050; "
                    "2060 may explicitly hold the 2050 profile"
                )
            if cost_year not in {2030, 2040, 2050}:
                raise ValueError(
                    "Wave cost year must be one of 2030, 2040, 2050; "
                    "2060 may explicitly hold the 2050 cost"
                )
        for cost_year in ("2030", "2040", "2050"):
            for field in (
                "capex_eur_per_kw_by_year",
                "fixed_om_fraction_by_year",
                "lifetime_years_by_year",
                "depth_adder_eur_per_kw_m_by_year",
                "distance_adder_eur_per_kw_km_by_year",
            ):
                value = float(wave.get(field, {}).get(cost_year, -1.0))
                if value < 0.0 or (
                    field == "lifetime_years_by_year" and value <= 0.0
                ):
                    raise ValueError(
                        f"wave_energy.{field}.{cost_year} must be nonnegative"
                    )
        flexible = self.raw.get("flexible_load", {})
        if "flexible_load" not in self.raw.get("features", {}):
            raise ValueError("features.flexible_load must be explicit")
        if (
            str(self.raw.get("scenario", {}).get("id")) == "base"
            and bool(self.raw["features"]["flexible_load"])
        ):
            raise ValueError(
                "Production Base scientific_case requires flexible_load=false; "
                "use an explicit scenario override"
            )
        if flexible.get("energy_conservation_window_hours") != 24:
            raise ValueError(
                "The first flexible-load implementation requires 24-hour energy conservation"
            )
        flexible_formulation = str(
            flexible.get("formulation", "daily_energy_shift_v1")
        )
        if flexible_formulation not in {
            "daily_energy_shift_v1",
            "state_envelope_v2",
            "comfort_envelope_v3",
            "service_constrained_v4",
            "integrated_service_constrained_v5",
        }:
            raise ValueError(
                "flexible_load.formulation must be daily_energy_shift_v1 "
                "or state_envelope_v2 or comfort_envelope_v3 or "
                "service_constrained_v4 or integrated_service_constrained_v5"
            )
        if flexible_formulation == "service_constrained_v4":
            if flexible.get("contract_version") != "v4":
                raise ValueError("service_constrained_v4 requires contract_version=v4")
            required_v4_files = (
                "thermal_hourly_envelope_file",
                "thermal_parameters_file",
                "ev_availability_hourly_file",
                "ev_mobility_hourly_file",
                "enablement_cost_file",
                "input_manifest_file",
            )
            v4_files = flexible.get("v4_input_files", {})
            missing_v4_files = [
                key for key in required_v4_files
                if not str(v4_files.get(key, "")).strip()
            ]
            if missing_v4_files:
                raise ValueError(
                    "service_constrained_v4 requires v4_input_files: "
                    + ", ".join(missing_v4_files)
                )
            if flexible.get("state_boundary") != "periodic_selected_horizon_v1":
                raise ValueError(
                    "service_constrained_v4 requires "
                    "state_boundary=periodic_selected_horizon_v1"
                )
            if float(
                flexible.get("v4_reference_energy_closure_tolerance_fraction", 0.0)
            ) < 0.0:
                raise ValueError(
                    "service_constrained_v4 EV reference-energy tolerance must be nonnegative"
                )
            for component in ("heating", "cooling"):
                if not bool(flexible.get(component, {}).get("enabled", False)):
                    raise ValueError(
                        f"service_constrained_v4 requires flexible_load.{component}.enabled=true"
                    )
            if not bool(flexible.get("ev_v1g", {}).get("enabled", False)):
                raise ValueError("service_constrained_v4 requires ev_v1g.enabled=true")
        if flexible_formulation == "integrated_service_constrained_v5":
            if flexible.get("contract_version") != "v5":
                raise ValueError(
                    "integrated_service_constrained_v5 requires contract_version=v5"
                )
            required_v5_files = (
                "thermal_hourly_envelope_file",
                "thermal_parameters_file",
                "ev_availability_hourly_file",
                "ev_mobility_hourly_file",
                "enablement_cost_file",
                "input_manifest_file",
            )
            v5_files = flexible.get("v5_input_files", {})
            missing_v5_files = [
                key
                for key in required_v5_files
                if not str(v5_files.get(key, "")).strip()
            ]
            if missing_v5_files:
                raise ValueError(
                    "integrated_service_constrained_v5 requires v5_input_files: "
                    + ", ".join(missing_v5_files)
                )
            if flexible.get("state_boundary") != "periodic_selected_horizon_v1":
                raise ValueError(
                    "integrated_service_constrained_v5 requires "
                    "state_boundary=periodic_selected_horizon_v1"
                )
            if float(
                flexible.get(
                    "v5_reference_energy_closure_tolerance_fraction", 0.0
                )
            ) < 0.0:
                raise ValueError(
                    "integrated_service_constrained_v5 EV reference-energy "
                    "tolerance must be nonnegative"
                )
            for component in ("heating", "cooling"):
                if not bool(flexible.get(component, {}).get("enabled", False)):
                    raise ValueError(
                        "integrated_service_constrained_v5 requires "
                        f"flexible_load.{component}.enabled=true"
                    )
            if not bool(flexible.get("ev_v1g", {}).get("enabled", False)):
                raise ValueError(
                    "integrated_service_constrained_v5 requires ev_v1g.enabled=true"
                )
            if not bool(flexible.get("ev_v2g", {}).get("enabled", False)):
                raise ValueError(
                    "integrated_service_constrained_v5 requires ev_v2g.enabled=true"
                )
            if capacity_margin_load_basis != "firm_flexibility_derated_v1":
                raise ValueError(
                    "integrated_service_constrained_v5 requires "
                    "security.capacity_margin_load_basis="
                    "firm_flexibility_derated_v1"
                )
            firm = flexible.get("firm_capacity_credit", {})
            if firm.get("contract_version") != "derated_peak_service_v1":
                raise ValueError(
                    "V5 firm capacity credit contract must be "
                    "derated_peak_service_v1"
                )
            event_duration = float(
                firm.get("required_event_duration_hours", 0.0)
            )
            if (
                event_duration <= 0.0
                or event_duration > self.hours
                or not event_duration.is_integer()
            ):
                raise ValueError(
                    "V5 firm capacity credit event duration must be a positive "
                    "integer no greater than the configured full year"
                )
            derating = firm.get("derating_fraction", {})
            for service in ("heating", "cooling", "ev_v1g", "ev_v2g"):
                value = float(derating.get(service, -1.0))
                if not 0.0 <= value <= 1.0:
                    raise ValueError(
                        f"V5 firm derating for {service} must be in [0, 1]"
                    )
            caps = flexible["ev_v2g"].get(
                "national_contracted_power_cap_gw_by_planning_year", {}
            )
            if set(caps) != {str(year) for year in years}:
                raise ValueError(
                    "V5 V2G national power caps must cover all planning years"
                )
            if any(float(value) < 0.0 for value in caps.values()):
                raise ValueError("V5 V2G national power caps must be nonnegative")
        if flexible_formulation == "comfort_envelope_v3":
            envelope_file = str(flexible.get("hourly_envelope_file", "")).strip()
            if not envelope_file:
                raise ValueError(
                    "comfort_envelope_v3 requires flexible_load.hourly_envelope_file"
                )
        for component in ("heating", "cooling"):
            settings = flexible.get(component, {})
            if flexible_formulation == "comfort_envelope_v3":
                if float(settings.get("comfort_band_delta_c", 0.0)) <= 0.0:
                    raise ValueError(
                        f"flexible_load.{component}.comfort_band_delta_c must be positive"
                    )
                if float(
                    settings.get("equivalent_storage_duration_hours", 0.0)
                ) <= 0.0:
                    raise ValueError(
                        f"flexible_load.{component}."
                        "equivalent_storage_duration_hours must be positive"
                    )
            elif flexible_formulation not in {
                "service_constrained_v4",
                "integrated_service_constrained_v5",
            }:
                reduction = float(
                    settings.get("maximum_reduction_fraction", -1.0)
                )
                increase = float(
                    settings.get("maximum_increase_fraction_of_daily_peak", -1.0)
                )
                if not 0.0 <= reduction <= 1.0 or not 0.0 <= increase <= 1.0:
                    raise ValueError(
                        f"flexible_load.{component} fractions must be in [0, 1]"
                    )
            if flexible_formulation in {
                "state_envelope_v2",
                "comfort_envelope_v3",
            }:
                duration_key = (
                    "equivalent_storage_duration_hours"
                    if flexible_formulation == "comfort_envelope_v3"
                    else "duration_hours"
                )
                if float(settings.get(duration_key, 0.0)) <= 0.0:
                    raise ValueError(
                        f"flexible_load.{component}.{duration_key} must be positive"
                    )
                retention = float(settings.get("retention_per_hour", 0.0))
                if not 0.0 < retention <= 1.0:
                    raise ValueError(
                        f"flexible_load.{component}.retention_per_hour must be in (0, 1]"
                    )
                for key in ("charge_efficiency", "discharge_efficiency"):
                    efficiency = float(settings.get(key, 0.0))
                    if not 0.0 < efficiency <= 1.0:
                        raise ValueError(
                            f"flexible_load.{component}.{key} must be in (0, 1]"
                        )
        ev_v1g = flexible.get("ev_v1g", {})
        if not 0.0 <= float(ev_v1g.get("shiftable_energy_fraction", -1.0)) <= 1.0:
            raise ValueError("flexible_load.ev_v1g.shiftable_energy_fraction must be in [0, 1]")
        if float(ev_v1g.get("maximum_power_to_daily_average_ratio", 0.0)) < 1.0:
            raise ValueError(
                "flexible_load.ev_v1g.maximum_power_to_daily_average_ratio must be >= 1"
            )
        if flexible_formulation in {
            "state_envelope_v2",
            "comfort_envelope_v3",
        }:
            if float(ev_v1g.get("maximum_queue_duration_hours", 0.0)) <= 0.0:
                raise ValueError(
                    "flexible_load.ev_v1g.maximum_queue_duration_hours must be positive"
                )
        ev_v2g = flexible.get("ev_v2g", {})
        if (
            flexible_formulation
            in {"service_constrained_v4", "integrated_service_constrained_v5"}
            and ev_v2g.get("state_boundary") != "periodic_selected_horizon_v1"
        ):
            raise ValueError(
                "service-constrained flexibility requires "
                "ev_v2g.state_boundary=periodic_selected_horizon_v1"
            )
        for key in ("charge_efficiency", "discharge_efficiency"):
            if not 0.0 < float(ev_v2g.get(key, 0.0)) <= 1.0:
                raise ValueError(f"flexible_load.ev_v2g.{key} must be in (0, 1]")
        if float(ev_v2g.get("power_duration_hours", 0.0)) <= 0.0:
            raise ValueError("flexible_load.ev_v2g.power_duration_hours must be positive")
        if flexible_formulation == "comfort_envelope_v3":
            v2g_power_fraction = float(
                ev_v2g.get("power_fraction_of_daily_baseline_peak", -1.0)
            )
            if not 0.0 <= v2g_power_fraction <= 1.0:
                raise ValueError(
                    "flexible_load.ev_v2g."
                    "power_fraction_of_daily_baseline_peak must be in [0, 1]"
                )
            if ev_v2g.get("state_boundary") != "daily_zero_causal":
                raise ValueError(
                    "comfort_envelope_v3 requires "
                    "flexible_load.ev_v2g.state_boundary=daily_zero_causal"
                )
        else:
            if not 0.0 <= float(
                ev_v2g.get("participation_fraction", -1.0)
            ) <= 1.0:
                raise ValueError(
                    "flexible_load.ev_v2g.participation_fraction must be in [0, 1]"
                )
        if flexible_formulation == "state_envelope_v2" and bool(
            ev_v2g.get("enabled", False)
        ):
            raise ValueError(
                "state_envelope_v2 cannot enable V2G until calibrated hourly vehicle "
                "availability, battery-energy and departure-service inputs exist"
            )
        for key in (
            "shift_throughput_cost_yuan_per_mwh",
            "degradation_cost_yuan_per_mwh",
        ):
            if float(flexible.get(key, -1.0)) < 0.0:
                raise ValueError(f"flexible_load.{key} must be nonnegative")
        if flexible_formulation == "comfort_envelope_v3":
            activation_costs = flexible.get(
                "activation_costs_yuan_per_mwh", {}
            )
            required_costs = (
                "heating_reduction",
                "heating_increase",
                "cooling_reduction",
                "cooling_increase",
                "ev_v1g_relocated",
                "ev_v2g_discharged",
            )
            for key in required_costs:
                if float(activation_costs.get(key, -1.0)) < 0.0:
                    raise ValueError(
                        "flexible_load.activation_costs_yuan_per_mwh."
                        f"{key} must be nonnegative"
                    )
        if not self.raw["features"].get("annual_load_center_transmission", False):
            raise ValueError("Production requires the annual load-center transmission layer")
        center_network = self.raw.get("load_center_network", {})
        if center_network.get("scenario") != "city_337":
            raise ValueError("Production load-center scenario must be city_337")
        if int(center_network.get("expected_load_center_count", 0)) != 337:
            raise ValueError("city_337 requires expected_load_center_count=337")
        if int(center_network.get("expected_intra_edge_count", 0)) != 642:
            raise ValueError("city_337 requires expected_intra_edge_count=642")
        if center_network.get("voltage_class") != "AC_500kV":
            raise ValueError("The current intra-province cost basis must remain AC_500kV")
        utilization = float(center_network.get("design_utilization_fraction", 0.0))
        if not 0.0 < utilization <= 1.0:
            raise ValueError("load-center design_utilization_fraction must be in (0, 1]")
        if float(center_network.get("intra_loss_fraction_per_km", -1.0)) != 0.0:
            raise ValueError(
                "The annual layer currently requires zero intra loss; nonzero loss must first be "
                "fed back into the hourly provincial energy balance"
            )
        if self.raw["construction"].get("architecture") != "full_year_monolithic_lp":
            raise ValueError("Production architecture must be full_year_monolithic_lp")
        hydro = self.raw.get("hydro", {})
        if float(hydro.get("reservoir_flow_variable_scale_m3s", 0.0)) <= 0.0:
            raise ValueError("reservoir_flow_variable_scale_m3s must be positive")
        if float(hydro.get("reservoir_volume_variable_scale_m3", 0.0)) <= 0.0:
            raise ValueError("reservoir_volume_variable_scale_m3 must be positive")
        if float(hydro.get("hydrology_flow_zero_tolerance_m3s", -1.0)) < 0.0:
            raise ValueError("hydrology_flow_zero_tolerance_m3s must be nonnegative")
        if hydro.get("duplicate_comid_flow_allocation") != (
            "static_capacity_potential_share_v1"
        ):
            raise ValueError(
                "Hydropower duplicate-COMID flow allocation must remain "
                "static_capacity_potential_share_v1"
            )
        if hydro.get("environmental_flow_dataset") != "monthly_environmental_flow_2019_p30":
            raise ValueError("Hydropower environmental-flow dataset must remain monthly_environmental_flow_2019_p30")
        if hydro.get("environmental_flow_variable") != "monthly_p30_proxy_m3s":
            raise ValueError("Hydropower environmental-flow variable must remain monthly_p30_proxy_m3s")
        aggregate_mode = hydro.get("provincial_aggregate_mode")
        supported_aggregate_modes = {
            "fixed_existing_monthly_profile_v1",
            "fixed_existing_monthly_energy_budget_v2",
        }
        if aggregate_mode not in supported_aggregate_modes:
            raise ValueError(
                "Unsupported hydro.provincial_aggregate_mode; expected "
                "fixed_existing_monthly_profile_v1 or "
                "fixed_existing_monthly_energy_budget_v2"
            )
        for key in (
            "provincial_aggregate_capacity_file",
            "provincial_aggregate_monthly_profile_file",
        ):
            if not str(hydro.get(key, "")).strip():
                raise ValueError(f"hydro.{key} must be explicit")
        if not 0.0 < float(
            hydro.get(
                "provincial_aggregate_national_conventional_target_gw",
                0.0,
            )
        ):
            raise ValueError(
                "Provincial aggregate national conventional-hydro target "
                "must be positive"
            )
        aggregate_up_credit = float(
            hydro.get("provincial_aggregate_up_reserve_credit", -1.0)
        )
        aggregate_down_credit = float(
            hydro.get("provincial_aggregate_down_reserve_credit", -1.0)
        )
        aggregate_capacity_credit = float(
            hydro.get("provincial_aggregate_capacity_credit", -1.0)
        )
        aggregate_inertia_seconds = float(
            hydro.get("provincial_aggregate_inertia_seconds", -1.0)
        )
        for key, value in (
            ("provincial_aggregate_up_reserve_credit", aggregate_up_credit),
            ("provincial_aggregate_down_reserve_credit", aggregate_down_credit),
            ("provincial_aggregate_capacity_credit", aggregate_capacity_credit),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"hydro.{key} must be in [0, 1]")
        if aggregate_inertia_seconds < 0.0:
            raise ValueError(
                "hydro.provincial_aggregate_inertia_seconds must be nonnegative"
            )
        if aggregate_mode == "fixed_existing_monthly_profile_v1" and any(
            abs(value) > 1e-12
            for value in (
                aggregate_up_credit,
                aggregate_down_credit,
                aggregate_capacity_credit,
                aggregate_inertia_seconds,
            )
        ):
            raise ValueError(
                "fixed_existing_monthly_profile_v1 requires zero reserve, "
                "capacity-margin and inertia credits"
            )
        if abs(aggregate_capacity_credit) > 1e-12:
            raise ValueError(
                "Provincial aggregate hydropower capacity-margin credit must "
                "remain zero until an adequacy/ELCC calibration is available"
            )
        if hydro.get("provincial_aggregate_connection_treatment") != (
            "province_non_spatial_existing_no_spur_trunk"
        ):
            raise ValueError(
                "Provincial aggregate hydropower must remain a non-spatial "
                "existing injection without spur/trunk construction"
            )
        numerics = self.raw.get("numerics", {})
        coefficient_tolerance = float(
            numerics.get("coefficient_zero_tolerance", 0.0)
        )
        if not 0.0 < coefficient_tolerance <= 1e-4:
            raise ValueError(
                "coefficient_zero_tolerance must be in (0, 1e-4]"
            )
        threads = int(numerics.get("threads", 0))
        if threads == 0 or threads < -1:
            raise ValueError(
                "numerics.threads must be -1 (all logical CPUs) or a positive count"
            )
        if int(numerics.get("crossover", -1)) not in {-1, 0, 1, 2, 3, 4}:
            raise ValueError("numerics.crossover is outside the Gurobi-supported range")
        if int(numerics.get("crossover_basis", -1)) not in {-1, 0, 1}:
            raise ValueError(
                "numerics.crossover_basis is outside the Gurobi-supported range"
            )
        if int(numerics.get("dual_reductions", 1)) not in {0, 1}:
            raise ValueError("numerics.dual_reductions must be 0 or 1")
        if int(numerics.get("inf_unbd_info", 0)) not in {0, 1}:
            raise ValueError("numerics.inf_unbd_info must be 0 or 1")
        if int(numerics.get("bar_iter_limit", 1000)) < 0:
            raise ValueError("numerics.bar_iter_limit must be nonnegative")
        formulation = self.raw.get("formulation", {})
        if formulation.get("annual_emissions_accounting") not in {
            "national_dense_v1",
            "province_hierarchical_v2",
        }:
            raise ValueError(
                "formulation.annual_emissions_accounting must be "
                "national_dense_v1 or province_hierarchical_v2"
            )
        chunk = int(self.raw["construction"].get("build_hour_chunk_size", 0))
        if chunk <= 0 or chunk > self.hours:
            raise ValueError("build_hour_chunk_size must be in [1, 8760]")
        horizons = self.raw["construction"].get("horizons", {})
        expected_hours = {"one_month": 744, "six_months": 4344, "full_year": 8760}
        if set(horizons) != set(expected_hours):
            raise ValueError("horizons must contain one_month, six_months, and full_year")
        for name, expected in expected_hours.items():
            if int(horizons[name]["hours"]) != expected:
                raise ValueError(f"{name} must contain exactly {expected} chronological hours")
            if float(horizons[name]["minimum_available_memory_gb"]) <= 0:
                raise ValueError(f"{name} memory gate must be positive")
        if bool(horizons["full_year"]["test_only"]):
            raise ValueError("full_year cannot be marked test-only")
        if not bool(horizons["one_month"]["test_only"]) or not bool(
            horizons["six_months"]["test_only"]
        ):
            raise ValueError("truncated horizons must remain test-only")


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge a small, recorded scenario override into the base config."""
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def load_model_config(
    path: str | Path | None = None,
    scenario_path: str | Path | None = None,
    solver_path: str | Path | None = None,
    formulation_path: str | Path | None = None,
) -> ModelConfig:
    config_path = Path(path) if path else DEFAULT_CONFIG
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    resolved_scenario: Path | None = None
    if scenario_path is not None:
        resolved_scenario = Path(scenario_path)
        if not resolved_scenario.is_absolute():
            resolved_scenario = ROOT / resolved_scenario
        payload = json.loads(resolved_scenario.read_text(encoding="utf-8"))
        if payload.get("scenario_override_version") != "v1":
            raise ValueError("Scenario override must declare scenario_override_version=v1")
        if not payload.get("scenario_id") or not payload.get("scenario_family"):
            raise ValueError("Scenario override requires scenario_id and scenario_family")
        analysis_role = str(payload.get("analysis_role", "")).strip()
        publication_status = str(payload.get("publication_status", "")).strip()
        if analysis_role not in ANALYSIS_ROLES:
            raise ValueError(
                "Scenario override requires an explicit supported analysis_role"
            )
        if not publication_status:
            raise ValueError(
                "Scenario override requires an explicit publication_status"
            )
        parent_baseline_case_id = payload.get("parent_baseline_case_id")
        if analysis_role == "BASELINE":
            if parent_baseline_case_id is not None:
                raise ValueError("A BASELINE scenario cannot declare a parent baseline")
        elif parent_baseline_case_id != raw["scientific_case"]["case_id"]:
            raise ValueError(
                "Non-Base scenario parent_baseline_case_id must match the "
                "immutable scientific_case.case_id"
            )
        overrides = payload.get("overrides")
        if not isinstance(overrides, dict):
            raise ValueError("Scenario override requires an object-valued overrides field")
        unknown_roots = sorted(
            set(overrides).difference(ALLOWED_SCENARIO_OVERRIDE_ROOTS)
        )
        if unknown_roots:
            raise ValueError(
                "Scenario override changes disallowed model roots: "
                + ", ".join(unknown_roots)
            )
        raw = _deep_merge(raw, overrides)
        raw["scenario"] = {
            "id": str(payload["scenario_id"]),
            "family": str(payload["scenario_family"]),
            "description": str(payload.get("description", "")),
            "evidence_status": str(payload.get("evidence_status", "UNSPECIFIED")),
            "analysis_role": analysis_role,
            "publication_status": publication_status,
            "parent_baseline_case_id": parent_baseline_case_id,
            "supersedes": payload.get("supersedes"),
        }
        resolved_scenario = resolved_scenario.resolve()
    resolved_solver: Path | None = None
    if solver_path is not None:
        resolved_solver = Path(solver_path)
        if not resolved_solver.is_absolute():
            resolved_solver = ROOT / resolved_solver
        payload = json.loads(resolved_solver.read_text(encoding="utf-8"))
        if payload.get("solver_profile_version") != "v1":
            raise ValueError(
                "Solver profile must declare solver_profile_version=v1"
            )
        if not payload.get("profile_id"):
            raise ValueError("Solver profile requires profile_id")
        overrides = payload.get("numerics")
        if not isinstance(overrides, dict):
            raise ValueError(
                "Solver profile requires an object-valued numerics field"
            )
        allowed_optional = {
            "aggregate",
            "agg_fill",
            "bar_iter_limit",
            "bar_correctors",
            "bar_homogeneous",
            "bar_order",
            "crossover_basis",
            "dual_reductions",
            "inf_unbd_info",
            "pdhg_gpu",
            "pre_dual",
            "pre_passes",
            "pre_sparsify",
        }
        allowed = set(raw["numerics"]).union(allowed_optional)
        unknown = set(overrides).difference(allowed)
        if unknown:
            raise ValueError(
                "Unsupported solver-profile numerics keys: "
                + ", ".join(sorted(unknown))
            )
        raw["numerics"] = _deep_merge(raw["numerics"], overrides)
        raw["solver_profile"] = {
            "id": str(payload["profile_id"]),
            "description": str(payload.get("description", "")),
        }
        resolved_solver = resolved_solver.resolve()
    resolved_formulation: Path | None = None
    if formulation_path is not None:
        resolved_formulation = Path(formulation_path)
        if not resolved_formulation.is_absolute():
            resolved_formulation = ROOT / resolved_formulation
        payload = json.loads(resolved_formulation.read_text(encoding="utf-8"))
        if payload.get("formulation_profile_version") != "v1":
            raise ValueError(
                "Formulation profile must declare formulation_profile_version=v1"
            )
        if not payload.get("profile_id"):
            raise ValueError("Formulation profile requires profile_id")
        overrides = payload.get("formulation")
        if not isinstance(overrides, dict):
            raise ValueError(
                "Formulation profile requires an object-valued formulation field"
            )
        allowed_formulation = {"annual_emissions_accounting"}
        unknown = set(overrides).difference(allowed_formulation)
        if unknown:
            raise ValueError(
                "Unsupported formulation-profile keys: "
                + ", ".join(sorted(unknown))
            )
        raw["formulation"] = _deep_merge(raw["formulation"], overrides)
        raw["formulation_profile"] = {
            "id": str(payload["profile_id"]),
            "description": str(payload.get("description", "")),
        }
        resolved_formulation = resolved_formulation.resolve()
    config = ModelConfig(
        config_path.resolve(),
        raw,
        resolved_scenario,
        resolved_solver,
        resolved_formulation,
    )
    config.validate()
    return config


def capital_recovery_factor(real_wacc: float, lifetime_years: float) -> float:
    if lifetime_years <= 0:
        raise ValueError("lifetime_years must be positive")
    if abs(real_wacc) < 1e-15:
        return 1.0 / lifetime_years
    factor = (1.0 + real_wacc) ** lifetime_years
    return real_wacc * factor / (factor - 1.0)


def resolve_minimum_system_inertia_seconds(
    security: dict[str, Any],
) -> float:
    """Resolve the effective inertia threshold with legacy override support."""
    legacy = security.get("minimum_system_inertia_seconds")
    if legacy is not None:
        effective = float(legacy)
    else:
        if "inertia_reference_seconds" not in security:
            raise ValueError("security.inertia_reference_seconds is required")
        if "inertia_tolerance_fraction" not in security:
            raise ValueError("security.inertia_tolerance_fraction is required")
        reference = float(security["inertia_reference_seconds"])
        tolerance = float(security["inertia_tolerance_fraction"])
        if reference <= 0.0:
            raise ValueError("security.inertia_reference_seconds must be positive")
        if not 0.0 < tolerance <= 1.0:
            raise ValueError(
                "security.inertia_tolerance_fraction must be in (0, 1]"
            )
        effective = reference * tolerance
    if effective <= 0.0:
        raise ValueError("Effective minimum system inertia must be positive")
    return effective
