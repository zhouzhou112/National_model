"""Configuration loading and validation for the CISPO optimization model."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "optimization_2030.json"


@dataclass(frozen=True)
class ModelConfig:
    path: Path
    raw: dict[str, Any]

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

    def validate(self) -> None:
        if self.boundary_year != 2025:
            raise ValueError("The current production boundary must remain 2025")
        if self.planning_year <= self.boundary_year:
            raise ValueError("planning_year must be later than boundary_year")
        if self.planning_year != 2030:
            raise ValueError("This version is the first 2030 sequential expansion model")
        if self.hours != 8760:
            raise ValueError("Production configuration must use all 8760 hours")
        if self.vre_scenario not in {"C", "B", "O"}:
            raise ValueError("vre_scenario must be one of C, B, O")
        if not self.raw["strict_load_balance"]:
            raise ValueError("Production configuration requires strict load balance")
        if self.raw["allow_debug_slacks"]:
            raise ValueError("Debug slacks must be disabled in production configuration")
        if self.raw["features"].get("csp", False):
            raise ValueError("CSP cannot be enabled until site potential and hourly profiles exist")
        if self.raw["construction"].get("architecture") != "full_year_monolithic_lp":
            raise ValueError("Production architecture must be full_year_monolithic_lp")
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


def load_model_config(path: str | Path | None = None) -> ModelConfig:
    config_path = Path(path) if path else DEFAULT_CONFIG
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    config = ModelConfig(config_path.resolve(), raw)
    config.validate()
    return config


def capital_recovery_factor(real_wacc: float, lifetime_years: float) -> float:
    if lifetime_years <= 0:
        raise ValueError("lifetime_years must be positive")
    if abs(real_wacc) < 1e-15:
        return 1.0 / lifetime_years
    factor = (1.0 + real_wacc) ** lifetime_years
    return real_wacc * factor / (factor - 1.0)
