"""Shared 2025-constant-CNY normalization for model monetary inputs."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PRICE_BASIS_CONFIG_PATH = ROOT / "config" / "technoeconomic_price_basis_2025.json"


@lru_cache(maxsize=1)
def load_price_basis_config() -> dict[str, Any]:
    with PRICE_BASIS_CONFIG_PATH.open("r", encoding="utf-8") as stream:
        config = json.load(stream)
    if config["target_price_basis"] != "2025 constant CNY":
        raise ValueError("Production cost basis must be 2025 constant CNY")
    return config


def domestic_2022_cny_to_2025(value: float) -> float:
    """Convert a 2022-constant-CNY monetary value to 2025 constant CNY."""
    factor = float(load_price_basis_config()["domestic_cny_to_2025_factor"])
    return float(value) * factor


def usd_2025_to_cny(value: float) -> float:
    """Convert a source value denominated in 2025 USD to 2025 CNY."""
    rate = float(load_price_basis_config()["foreign_exchange_2025"]["usd_to_cny"])
    return float(value) * rate


def eur_2025_to_cny(value: float) -> float:
    """Convert a source value denominated in EUR to 2025 CNY."""
    rate = float(load_price_basis_config()["foreign_exchange_2025"]["eur_to_cny"])
    return float(value) * rate


def nuclear_capex_2025_cny(year: int) -> float:
    """Return the approved nuclear CapEx trajectory in 2025 CNY/kW."""
    values = load_price_basis_config()["nuclear_capex"]["source_values_by_year"]
    return usd_2025_to_cny(float(values[str(int(year))]))
