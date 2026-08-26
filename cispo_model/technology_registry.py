"""Validated access to the repository techno-economic source registry."""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any


REGISTRY_PATH = Path(__file__).resolve().parents[1] / "config" / "technology_parameters.json"
REQUIRED_VRE_HYDRO_TECHNOLOGIES = {"onwind", "offwind", "upv", "dpv", "hydro"}


@lru_cache(maxsize=1)
def load_technology_parameter_registry() -> dict[str, Any]:
    """Load and validate parameters consumed directly by the LP builder."""
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    source = payload.get("source")
    if not isinstance(source, dict) or not str(source.get("document", "")).strip():
        raise ValueError("Technology registry requires a non-empty source.document")

    rows = payload.get("vre_cost_anchor")
    if not isinstance(rows, list):
        raise ValueError("Technology registry vre_cost_anchor must be a list")
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not str(row.get("technology", "")).strip():
            raise ValueError("Every VRE/hydro cost anchor requires technology")
        technology = str(row["technology"])
        if technology in indexed:
            raise ValueError(f"Duplicate VRE/hydro cost anchor: {technology}")
        fixed_om = float(row["fixed_om_fraction_capex_per_year"])
        if not math.isfinite(fixed_om) or not 0.0 <= fixed_om < 1.0:
            raise ValueError(f"Invalid fixed O&M fraction for {technology}: {fixed_om}")
        source_page = int(row["source_page"])
        if source_page <= 0:
            raise ValueError(f"Invalid source page for {technology}: {source_page}")
        indexed[technology] = row
    missing = REQUIRED_VRE_HYDRO_TECHNOLOGIES.difference(indexed)
    if missing:
        raise ValueError(
            "Technology registry lacks required VRE/hydro anchors: "
            + ", ".join(sorted(missing))
        )

    transmission = payload.get("transmission")
    if not isinstance(transmission, dict):
        raise ValueError("Technology registry requires transmission parameters")
    loss = float(transmission["loss_fraction_per_km"])
    if not math.isfinite(loss) or not 0.0 <= loss < 1.0:
        raise ValueError(f"Invalid transmission loss_fraction_per_km: {loss}")
    if int(transmission["source_page"]) <= 0:
        raise ValueError("Transmission parameters require a positive source_page")

    payload["_validated_vre_hydro_by_technology"] = indexed
    return payload


def fixed_om_fraction(registry: dict[str, Any], technology: str) -> float:
    """Return a validated VRE/hydro fixed-O&M fraction."""
    return float(registry["_validated_vre_hydro_by_technology"][technology][
        "fixed_om_fraction_capex_per_year"
    ])


def transmission_loss_fraction_per_km(registry: dict[str, Any]) -> float:
    """Return the validated interprovincial line-loss fraction per kilometre."""
    return float(registry["transmission"]["loss_fraction_per_km"])
