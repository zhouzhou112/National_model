"""Configuration loading and validation for the CISPO optimization model."""
from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "optimization_2030.json"


@dataclass(frozen=True)
class ModelConfig:
    path: Path
    raw: dict[str, Any]
    scenario_path: Path | None = None

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
        config = ModelConfig(self.path, raw, self.scenario_path)
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
        if self.hours != 8760:
            raise ValueError("Production configuration must use all 8760 hours")
        if self.vre_scenario not in {"C", "B", "O"}:
            raise ValueError("vre_scenario must be one of C, B, O")
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
        resolve_minimum_system_inertia_seconds(security)
        if self.raw["features"].get("csp", False):
            raise ValueError("CSP cannot be enabled until site potential and hourly profiles exist")
        flexible = self.raw.get("flexible_load", {})
        if "flexible_load" not in self.raw.get("features", {}):
            raise ValueError("features.flexible_load must be explicit")
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
        }:
            raise ValueError(
                "flexible_load.formulation must be daily_energy_shift_v1 "
                "or state_envelope_v2"
            )
        for component in ("heating", "cooling"):
            settings = flexible.get(component, {})
            reduction = float(settings.get("maximum_reduction_fraction", -1.0))
            increase = float(
                settings.get("maximum_increase_fraction_of_daily_peak", -1.0)
            )
            if not 0.0 <= reduction <= 1.0 or not 0.0 <= increase <= 1.0:
                raise ValueError(
                    f"flexible_load.{component} fractions must be in [0, 1]"
                )
            if flexible_formulation == "state_envelope_v2":
                if float(settings.get("duration_hours", 0.0)) <= 0.0:
                    raise ValueError(
                        f"flexible_load.{component}.duration_hours must be positive"
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
        if flexible_formulation == "state_envelope_v2":
            if float(ev_v1g.get("maximum_queue_duration_hours", 0.0)) <= 0.0:
                raise ValueError(
                    "flexible_load.ev_v1g.maximum_queue_duration_hours must be positive"
                )
        ev_v2g = flexible.get("ev_v2g", {})
        for key in ("charge_efficiency", "discharge_efficiency"):
            if not 0.0 < float(ev_v2g.get(key, 0.0)) <= 1.0:
                raise ValueError(f"flexible_load.ev_v2g.{key} must be in (0, 1]")
        if not 0.0 <= float(ev_v2g.get("participation_fraction", -1.0)) <= 1.0:
            raise ValueError("flexible_load.ev_v2g.participation_fraction must be in [0, 1]")
        if float(ev_v2g.get("power_duration_hours", 0.0)) <= 0.0:
            raise ValueError("flexible_load.ev_v2g.power_duration_hours must be positive")
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
        if hydro.get("environmental_flow_dataset") != "monthly_environmental_flow_2019_p30":
            raise ValueError("Hydropower environmental-flow dataset must remain monthly_environmental_flow_2019_p30")
        if hydro.get("environmental_flow_variable") != "monthly_p30_proxy_m3s":
            raise ValueError("Hydropower environmental-flow variable must remain monthly_p30_proxy_m3s")
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
        overrides = payload.get("overrides")
        if not isinstance(overrides, dict):
            raise ValueError("Scenario override requires an object-valued overrides field")
        raw = _deep_merge(raw, overrides)
        raw["scenario"] = {
            "id": str(payload["scenario_id"]),
            "family": str(payload["scenario_family"]),
            "description": str(payload.get("description", "")),
            "evidence_status": str(payload.get("evidence_status", "UNSPECIFIED")),
        }
        resolved_scenario = resolved_scenario.resolve()
    config = ModelConfig(config_path.resolve(), raw, resolved_scenario)
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
