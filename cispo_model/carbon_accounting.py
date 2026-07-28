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


def evaluate_postsolve_beccs_lifecycle_sensitivity(
    resource_accounting: pd.DataFrame,
    cases: dict[str, float],
) -> pd.DataFrame:
    """Apply lifecycle burdens to a solved BECCS result without re-solving.

    ``cases`` maps a case label to lifecycle emissions expressed as a fraction
    of physically stored biogenic CO2.  The solved dispatch, capture and
    storage decisions remain fixed; this is therefore an accounting sensitivity
    only and must never be reported as a new least-cost optimum.
    """
    required = {
        "province_code",
        "beccs_stored_co2_mtco2",
        "beccs_lifecycle_emissions_mtco2",
        "net_emissions_after_dac_mtco2",
    }
    missing = sorted(required.difference(resource_accounting.columns))
    if missing:
        raise ValueError(
            "BECCS lifecycle sensitivity source lacks columns: " + ", ".join(missing)
        )
    if not cases:
        raise ValueError("BECCS lifecycle sensitivity requires at least one case")
    source = resource_accounting.loc[:, sorted(required)].copy()
    for column in required.difference({"province_code"}):
        source[column] = pd.to_numeric(source[column], errors="raise")
    if (
        source.province_code.duplicated().any()
        or not np.isfinite(source.drop(columns="province_code").to_numpy(dtype=float)).all()
        or source.beccs_stored_co2_mtco2.lt(-1e-10).any()
        or source.beccs_lifecycle_emissions_mtco2.lt(-1e-10).any()
    ):
        raise ValueError("Invalid BECCS lifecycle sensitivity source accounting")

    rows: list[pd.DataFrame] = []
    for case_id, share in cases.items():
        share = float(share)
        if not np.isfinite(share) or not 0.0 <= share <= 1.0:
            raise ValueError(
                f"Lifecycle share for {case_id!r} must be finite and in [0, 1]"
            )
        frame = source.copy()
        frame.insert(0, "case_id", str(case_id))
        frame["lifecycle_share_of_stored_biogenic_co2"] = share
        frame["assumed_lifecycle_emissions_mtco2"] = (
            share * frame.beccs_stored_co2_mtco2
        )
        frame["adjusted_beccs_net_removal_mtco2"] = (
            frame.beccs_stored_co2_mtco2
            - frame.assumed_lifecycle_emissions_mtco2
        )
        frame["net_emissions_delta_mtco2"] = (
            frame.assumed_lifecycle_emissions_mtco2
            - frame.beccs_lifecycle_emissions_mtco2
        )
        frame["adjusted_net_emissions_after_dac_mtco2"] = (
            frame.net_emissions_after_dac_mtco2
            + frame.net_emissions_delta_mtco2
        )
        rows.append(frame)
    return pd.concat(rows, ignore_index=True)
