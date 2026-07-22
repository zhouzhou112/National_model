"""Explicit carbon-accounting factors for the CISPO-equivalent BECCS baseline."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BeccsCarbonFactors:
    """Per-generation BECCS carbon factors, all in MtCO2/GWh."""

    gross_biogenic: float
    captured_biogenic: float
    stored: float
    uncaptured_biogenic: float
    lifecycle_emissions: float
    net_emissions: float
    capture_fraction: float

    @property
    def net_removal(self) -> float:
        return -self.net_emissions


def resolve_beccs_carbon_factors(
    emission_table: pd.DataFrame,
) -> BeccsCarbonFactors:
    """Resolve an explicit mass balance from the CISPO reported net factor.

    CISPO treats biomass as carbon-neutral, reports a negative BECCS emission
    factor, assumes 90% capture, and requires captured CO2 to be stored.  Its
    published notation does not distinguish gross biogenic CO2 from net
    removal.  The replication baseline therefore sets lifecycle emissions to
    zero and interprets the magnitude of the reported negative factor as
    stored biogenic CO2.  This preserves the existing objective and feasible
    set while making every physical account explicit.
    """

    net_factor = float(
        emission_table.loc["bioccs", "emission_factor_mtco2_per_gwh"]
    )
    if not np.isfinite(net_factor) or net_factor >= 0.0:
        raise ValueError("BECCS net emission factor must be finite and negative")

    capture_fraction = emission_table.loc["bioccs", "ccs_capture_fraction"]
    if pd.isna(capture_fraction):
        capture_fraction = emission_table.loc["coal", "ccs_capture_fraction"]
    capture_fraction = float(capture_fraction)
    if not np.isfinite(capture_fraction) or not 0.0 < capture_fraction <= 1.0:
        raise ValueError("BECCS capture fraction must be in (0, 1]")

    lifecycle_factor = 0.0
    if "lifecycle_emission_factor_mtco2_per_gwh" in emission_table.columns:
        value = emission_table.loc[
            "bioccs", "lifecycle_emission_factor_mtco2_per_gwh"
        ]
        if not pd.isna(value):
            lifecycle_factor = float(value)
    if not np.isfinite(lifecycle_factor) or lifecycle_factor < 0.0:
        raise ValueError("BECCS lifecycle emission factor must be finite and nonnegative")

    stored_factor = lifecycle_factor - net_factor
    gross_factor = stored_factor / capture_fraction
    uncaptured_factor = gross_factor - stored_factor
    factors = BeccsCarbonFactors(
        gross_biogenic=gross_factor,
        captured_biogenic=stored_factor,
        stored=stored_factor,
        uncaptured_biogenic=uncaptured_factor,
        lifecycle_emissions=lifecycle_factor,
        net_emissions=net_factor,
        capture_fraction=capture_fraction,
    )
    closure = (
        factors.lifecycle_emissions
        + factors.uncaptured_biogenic
        - factors.gross_biogenic
        - factors.net_emissions
    )
    if abs(closure) > 1e-12:
        raise ValueError("BECCS factor mass balance does not close")
    return factors
