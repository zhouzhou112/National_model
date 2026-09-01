"""Exact coordinate transforms for the annual load-center energy subsystem.

The scientific model and all public outputs use physical GWh.  An optional
formulation profile represents annual accounting and intra-load-center flow
variables in units of 8192 GWh inside the LP.  Resource-generation variables
and their CF/hydrology availability rows remain in physical GWh.  The scale is
a power of two, so the coordinate conversion itself is exact for finite
IEEE-754 binary64 values in the model's safe magnitude range.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


PHYSICAL_GWH_V1 = "physical_gwh_v1"
BINARY_8192_GWH_V1 = "binary_8192_gwh_v1"
ANNUAL_ENERGY_SCALE_GWH = 8192.0

SCALED_ANNUAL_ENERGY_VARIABLE_KEYS = (
    "load_center_annual_injection",
    "load_center_annual_demand",
    "load_center_external_net_import",
    "intra_load_center_flow_forward",
    "intra_load_center_flow_reverse",
    "province_annual_non_spatial_injection",
    "province_annual_effective_demand",
    "province_annual_external_sent",
    "province_annual_external_received",
    "province_annual_external_net_import",
)

PHYSICAL_RESOURCE_ENERGY_VARIABLE_KEYS = (
    "load_center_vre_generation",
    "load_center_wave_generation",
    "load_center_ror_generation",
    "load_center_reservoir_generation",
)

ANNUAL_ENERGY_CONSTRAINT_PREFIXES = (
    "province_annual_non_spatial_injection_",
    "province_annual_effective_demand_",
    "province_annual_external_sent_",
    "province_annual_external_received_",
    "province_annual_external_net_import_",
    "load_center_annual_injection_",
    "load_center_annual_demand_",
    "load_center_external_net_import_",
    "load_center_annual_energy_balance_",
    "intra_load_center_annual_capacity",
)

PHYSICAL_RESOURCE_ENERGY_CONSTRAINT_PREFIXES = (
    "load_center_vre_availability_",
    "load_center_vre_generation_closure_",
    "load_center_wave_availability_",
    "load_center_wave_generation_closure_",
    "load_center_ror_availability_",
    "load_center_ror_generation_closure_",
    "load_center_reservoir_generation_",
)


@dataclass(frozen=True)
class AnnualEnergyCoordinate:
    profile: str
    variable_scale_gwh: float

    @property
    def row_scale_per_gwh(self) -> float:
        return 1.0 / self.variable_scale_gwh

    @property
    def enabled(self) -> bool:
        return self.variable_scale_gwh != 1.0

    def internal_variable_name(self, physical_name: str) -> str:
        if not self.enabled:
            return physical_name
        stem = (
            physical_name[:-4]
            if physical_name.endswith("_gwh")
            else physical_name
        )
        return f"{stem}_internal_8192gwh"

    def to_internal(self, physical_value: Any) -> Any:
        return np.asarray(physical_value) / self.variable_scale_gwh

    def to_physical(self, internal_value: Any) -> Any:
        return np.asarray(internal_value) * self.variable_scale_gwh

    def variable_to_physical(self, key: str, value: Any) -> Any:
        values = np.asarray(value)
        if key in SCALED_ANNUAL_ENERGY_VARIABLE_KEYS:
            return self.to_physical(values)
        return values

    def dual_to_physical(self, internal_dual: Any) -> Any:
        """Map scaled-row duals to million CNY per physical GWh RHS."""
        return np.asarray(internal_dual) * self.row_scale_per_gwh

    def reduced_cost_to_physical(self, internal_reduced_cost: Any) -> Any:
        """Map internal-variable reduced costs to physical-GWh coordinates."""
        return np.asarray(internal_reduced_cost) / self.variable_scale_gwh

    def metadata(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "enabled": self.enabled,
            "physical_unit": "GWh",
            "internal_unit": (
                "8192_GWh_per_internal_unit" if self.enabled else "GWh"
            ),
            "variable_scale_gwh": self.variable_scale_gwh,
            "row_scale_per_gwh": self.row_scale_per_gwh,
            "primal_physical_from_internal": "x_physical = D * x_internal",
            "dual_physical_from_internal": "dual_physical = R^T * dual_internal",
            "reduced_cost_physical_from_internal": (
                "reduced_cost_physical = D^(-T) * reduced_cost_internal"
            ),
            "scaled_variable_keys": list(SCALED_ANNUAL_ENERGY_VARIABLE_KEYS),
            "physical_resource_energy_variable_keys": list(
                PHYSICAL_RESOURCE_ENERGY_VARIABLE_KEYS
            ),
            "scaled_constraint_prefixes": list(
                ANNUAL_ENERGY_CONSTRAINT_PREFIXES
            ),
            "physical_resource_energy_constraint_prefixes": list(
                PHYSICAL_RESOURCE_ENERGY_CONSTRAINT_PREFIXES
            ),
            "raw_solver_vectors_are_internal_coordinates": self.enabled,
        }


def resolve_annual_energy_coordinate(config: Any) -> AnnualEnergyCoordinate:
    profile = str(
        config.raw.get("formulation", {}).get(
            "annual_energy_coordinate", PHYSICAL_GWH_V1
        )
    )
    if profile == PHYSICAL_GWH_V1:
        scale = 1.0
    elif profile == BINARY_8192_GWH_V1:
        scale = ANNUAL_ENERGY_SCALE_GWH
    else:
        raise ValueError(f"Unsupported annual_energy_coordinate={profile!r}")
    return AnnualEnergyCoordinate(profile=profile, variable_scale_gwh=scale)
