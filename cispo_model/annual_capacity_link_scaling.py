"""Exact left scaling for annual rows that couple energy to capacity.

The public CISPO model remains in physical GW/GWh coordinates.  The optional
formulation profile in this module only multiplies selected zero-RHS rows by a
positive power-of-two factor.  This leaves the feasible set, objective,
variable bounds, checkpoints, and planning states unchanged while reducing
the large full-load-hour coefficients seen by the solver.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from typing import Any, Iterable

import numpy as np


PHYSICAL_V1 = "physical_v1"
BINARY_POWER2_SAFE_8192_V1 = "binary_power2_safe_8192_v1"
MAX_BINARY_EXPONENT = 13
MINIMUM_SCALED_ABS_COEFFICIENT = 1.0e-6

CONSTRAINT_PREFIX_BY_FAMILY = {
    "vre": "load_center_vre_availability_",
    "ror": "load_center_ror_availability_",
}
ANCHOR_VARIABLE_PREFIX_BY_FAMILY = {
    "vre": "load_center_vre_generation_gwh[",
    "ror": "load_center_ror_generation_gwh[",
}


@dataclass(frozen=True)
class AnnualCapacityLinkRowScale:
    """One family-wide exact left-row scale and its physical mappings."""

    profile: str
    family: str
    exponent: int
    original_min_abs: float
    original_max_abs: float
    coefficient_count: int

    @property
    def factor(self) -> float:
        return math.ldexp(1.0, -self.exponent)

    @property
    def enabled(self) -> bool:
        return self.exponent > 0

    def coefficients(self, values: Any) -> np.ndarray:
        """Return coefficients multiplied exactly by ``2**-exponent``."""
        array = np.asarray(values, dtype=np.float64)
        scaled = np.ldexp(array, -self.exponent)
        if not np.isfinite(scaled).all():
            raise ValueError(f"Nonfinite scaled coefficients for {self.family}")
        if not np.array_equal(np.ldexp(scaled, self.exponent), array):
            raise ValueError(
                f"Power-of-two coefficient roundtrip failed for {self.family}"
            )
        return scaled

    def dual_to_physical(self, solver_dual: Any) -> np.ndarray:
        """Map a scaled-row dual to the original physical-row derivative."""
        return np.ldexp(np.asarray(solver_dual, dtype=np.float64), -self.exponent)

    def slack_to_physical(self, solver_slack: Any) -> np.ndarray:
        """Map solver slack back to the original physical row units."""
        return np.ldexp(np.asarray(solver_slack, dtype=np.float64), self.exponent)

    def metadata(self) -> dict[str, Any]:
        factor = self.factor
        return {
            "profile": self.profile,
            "family": self.family,
            "constraint_prefix": CONSTRAINT_PREFIX_BY_FAMILY[self.family],
            "exponent": self.exponent,
            "row_scale": factor,
            "coefficient_count_used_for_guard": self.coefficient_count,
            "original_coefficient_min_abs": self.original_min_abs,
            "original_coefficient_max_abs": self.original_max_abs,
            "scaled_coefficient_min_abs": math.ldexp(
                self.original_min_abs, -self.exponent
            ),
            "scaled_coefficient_max_abs": math.ldexp(
                self.original_max_abs, -self.exponent
            ),
            "primal_variables_remain_in_physical_units": True,
            "physical_dual_mapping": "pi_physical = row_scale * pi_solver",
            "physical_slack_mapping": "slack_physical = slack_solver / row_scale",
            "reduced_cost_mapping": "unchanged",
        }


def _profile(config: Any) -> str:
    return str(
        config.raw.get("formulation", {}).get(
            "annual_capacity_link_row_scaling", PHYSICAL_V1
        )
    )


def select_annual_capacity_link_row_scale(
    config: Any,
    family: str,
    coefficients: Iterable[float] | np.ndarray,
) -> AnnualCapacityLinkRowScale:
    """Select the largest safe family scale, capped at ``2**-13``.

    ``coefficients`` must contain every nonzero coefficient magnitude used by
    the affected rows, including the unit coefficient on the annual-energy
    variable.  On 8760h data both targeted families select exponent 13.  Short
    diagnostic windows automatically use a smaller exponent when needed so a
    smoke test cannot manufacture new coefficients below ``1e-6``.
    """
    if family not in CONSTRAINT_PREFIX_BY_FAMILY:
        raise ValueError(f"Unsupported annual capacity-link family={family!r}")
    profile = _profile(config)
    if profile not in {PHYSICAL_V1, BINARY_POWER2_SAFE_8192_V1}:
        raise ValueError(
            "Unsupported formulation.annual_capacity_link_row_scaling="
            f"{profile!r}"
        )
    values = np.abs(np.asarray(list(coefficients), dtype=np.float64).reshape(-1))
    if not len(values) or not np.isfinite(values).all():
        raise ValueError(f"Invalid coefficient guard set for {family}")
    values = values[values > 0.0]
    if not len(values):
        raise ValueError(f"Coefficient guard set for {family} has no nonzero value")
    minimum = float(values.min())
    maximum = float(values.max())
    exponent = 0
    if profile == BINARY_POWER2_SAFE_8192_V1:
        if minimum < MINIMUM_SCALED_ABS_COEFFICIENT:
            raise ValueError(
                f"Original {family} coefficient {minimum:.17g} is already below "
                f"the {MINIMUM_SCALED_ABS_COEFFICIENT:.1e} scaling guard"
            )
        exponent = min(
            MAX_BINARY_EXPONENT,
            max(
                0,
                int(
                    math.floor(
                        math.log2(
                            minimum / MINIMUM_SCALED_ABS_COEFFICIENT
                        )
                    )
                ),
            ),
        )
        # Defend the boundary against libm rounding.  Scaling is useful only
        # when the resulting coefficient guard is actually satisfied.
        while exponent > 0 and math.ldexp(minimum, -exponent) < (
            MINIMUM_SCALED_ABS_COEFFICIENT
        ):
            exponent -= 1
    result = AnnualCapacityLinkRowScale(
        profile=profile,
        family=family,
        exponent=exponent,
        original_min_abs=minimum,
        original_max_abs=maximum,
        coefficient_count=int(len(values)),
    )
    result.coefficients(values)
    if (
        profile == BINARY_POWER2_SAFE_8192_V1
        and result.original_min_abs * result.factor
        < MINIMUM_SCALED_ABS_COEFFICIENT
    ):
        raise ValueError(f"Unsafe scaled coefficient for {family}")
    return result


def row_scaling_metadata(
    config: Any,
    scales: dict[str, AnnualCapacityLinkRowScale],
) -> dict[str, Any]:
    """Build a serializable fail-closed mapping for audits and raw dual use."""
    missing = set(CONSTRAINT_PREFIX_BY_FAMILY).difference(scales)
    if missing:
        raise ValueError(
            "Missing annual capacity-link scale families: "
            + ", ".join(sorted(missing))
        )
    return {
        "schema_version": "cispo_annual_capacity_link_row_scaling_v1",
        "profile": _profile(config),
        "maximum_binary_exponent": MAX_BINARY_EXPONENT,
        "minimum_scaled_abs_coefficient": MINIMUM_SCALED_ABS_COEFFICIENT,
        "transformation": "selected zero-RHS rows are left-multiplied by 2^-k",
        "feasible_set_and_objective_unchanged": True,
        "explicitly_not_scaled": [
            "wave: its audited capacity-column span is not pathological",
            "intra-load-center capacity: no hourly tiny-coefficient coupling",
        ],
        "families": {
            family: {
                **scales[family].metadata(),
                "constraint_rows": 0,
                "matrix_nonzeros_scaled": 0,
                "constraint_names": [],
                "constraint_name_order_sha256": ordered_name_sha256([]),
            }
            for family in CONSTRAINT_PREFIX_BY_FAMILY
        },
    }


def ordered_name_sha256(names: Iterable[str]) -> str:
    """Hash the exact ordered constraint-name registry without storing it."""
    digest = hashlib.sha256()
    digest.update(b"cispo_annual_capacity_link_constraint_order_v1\0")
    rows = [str(name) for name in names]
    digest.update(len(rows).to_bytes(8, "big"))
    for index, name in enumerate(rows):
        encoded = name.encode("utf-8")
        digest.update(index.to_bytes(8, "big"))
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _registry_integer(value: Any, label: str, *, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{label} must be an integer")
    integer = int(value)
    if integer < minimum:
        raise ValueError(f"{label} must be >= {minimum}")
    return integer


def _registry_float(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be a finite number") from error
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number")
    return number


def validate_row_scaling_registry(
    registry: Any,
    *,
    model: Any | None = None,
    allow_none: bool = True,
) -> dict[str, Any] | None:
    """Validate every field needed to interpret scaled rows and raw duals.

    Passing ``model`` additionally binds the registry to the exact ordered
    constraint names, zero right-hand sides, and row nonzero counts.  The
    check streams names in bounded blocks and retains only the small targeted
    family, so it does not materialize a full name catalogue.
    """
    if registry is None:
        if allow_none:
            return None
        raise ValueError("Annual capacity-link row-scaling registry is required")
    if not isinstance(registry, dict):
        raise ValueError("Annual capacity-link row-scaling registry must be an object")
    if registry.get("schema_version") != (
        "cispo_annual_capacity_link_row_scaling_v1"
    ):
        raise ValueError("Unknown annual capacity-link row-scaling registry")
    profile = registry.get("profile")
    if profile not in {PHYSICAL_V1, BINARY_POWER2_SAFE_8192_V1}:
        raise ValueError("Unknown annual capacity-link row-scaling profile")
    maximum_exponent = _registry_integer(
        registry.get("maximum_binary_exponent"),
        "maximum_binary_exponent",
        minimum=0,
    )
    if maximum_exponent != MAX_BINARY_EXPONENT:
        raise ValueError("Unexpected annual row-scaling exponent cap")
    guard = _registry_float(
        registry.get("minimum_scaled_abs_coefficient"),
        "minimum_scaled_abs_coefficient",
    )
    if guard != MINIMUM_SCALED_ABS_COEFFICIENT:
        raise ValueError("Unexpected annual row-scaling coefficient guard")
    if registry.get("transformation") != (
        "selected zero-RHS rows are left-multiplied by 2^-k"
    ):
        raise ValueError("Unexpected annual row-scaling transformation")
    if registry.get("feasible_set_and_objective_unchanged") is not True:
        raise ValueError(
            "Annual row scaling must preserve the feasible set and objective"
        )
    if registry.get("explicitly_not_scaled") != [
        "wave: its audited capacity-column span is not pathological",
        "intra-load-center capacity: no hourly tiny-coefficient coupling",
    ]:
        raise ValueError("Unexpected annual row-scaling exclusion scope")
    families = registry.get("families")
    if not isinstance(families, dict) or set(families) != set(
        CONSTRAINT_PREFIX_BY_FAMILY
    ):
        raise ValueError("Incomplete annual capacity-link row-scaling registry")
    prefixes = tuple(CONSTRAINT_PREFIX_BY_FAMILY.values())
    if any(
        left.startswith(right) or right.startswith(left)
        for index, left in enumerate(prefixes)
        for right in prefixes[index + 1 :]
    ):
        raise RuntimeError("Canonical annual row-scaling prefixes overlap")

    for family_name, expected_prefix in CONSTRAINT_PREFIX_BY_FAMILY.items():
        family = families[family_name]
        if not isinstance(family, dict):
            raise ValueError(f"Row-scaling family {family_name} must be an object")
        if family.get("family") != family_name:
            raise ValueError(f"Row-scaling family key mismatch for {family_name}")
        if family.get("profile") != profile:
            raise ValueError(f"Row-scaling profile mismatch for {family_name}")
        if family.get("constraint_prefix") != expected_prefix:
            raise ValueError(f"Row-scaling prefix mismatch for {family_name}")
        if family.get("primal_variables_remain_in_physical_units") is not True:
            raise ValueError(
                f"Primal-unit mapping mismatch for {family_name}"
            )
        if family.get("physical_dual_mapping") != (
            "pi_physical = row_scale * pi_solver"
        ):
            raise ValueError(f"Dual mapping mismatch for {family_name}")
        if family.get("physical_slack_mapping") != (
            "slack_physical = slack_solver / row_scale"
        ):
            raise ValueError(f"Slack mapping mismatch for {family_name}")
        if family.get("reduced_cost_mapping") != "unchanged":
            raise ValueError(f"Reduced-cost mapping mismatch for {family_name}")
        exponent = _registry_integer(
            family.get("exponent"),
            f"{family_name}.exponent",
            minimum=0,
        )
        if exponent > MAX_BINARY_EXPONENT:
            raise ValueError(f"{family_name}.exponent exceeds the safe cap")
        if profile == PHYSICAL_V1 and exponent != 0:
            raise ValueError("physical_v1 cannot declare scaled rows")
        row_scale = _registry_float(
            family.get("row_scale"), f"{family_name}.row_scale"
        )
        if row_scale != math.ldexp(1.0, -exponent):
            raise ValueError(f"Inconsistent row-scale exponent for {family_name}")
        row_count = _registry_integer(
            family.get("constraint_rows"),
            f"{family_name}.constraint_rows",
            minimum=0,
        )
        nonzeros = _registry_integer(
            family.get("matrix_nonzeros_scaled"),
            f"{family_name}.matrix_nonzeros_scaled",
            minimum=0,
        )
        if nonzeros < row_count:
            raise ValueError(f"{family_name} row nonzeros are smaller than row count")
        guard_coefficient_count = _registry_integer(
            family.get("coefficient_count_used_for_guard"),
            f"{family_name}.coefficient_count_used_for_guard",
            minimum=1,
        )
        if row_count and guard_coefficient_count != nonzeros - row_count + 1:
            raise ValueError(
                f"{family_name} coefficient guard count does not match row nonzeros"
            )
        original_min = _registry_float(
            family.get("original_coefficient_min_abs"),
            f"{family_name}.original_coefficient_min_abs",
        )
        original_max = _registry_float(
            family.get("original_coefficient_max_abs"),
            f"{family_name}.original_coefficient_max_abs",
        )
        scaled_min = _registry_float(
            family.get("scaled_coefficient_min_abs"),
            f"{family_name}.scaled_coefficient_min_abs",
        )
        scaled_max = _registry_float(
            family.get("scaled_coefficient_max_abs"),
            f"{family_name}.scaled_coefficient_max_abs",
        )
        if not 0.0 < original_min <= original_max:
            raise ValueError(f"Invalid original coefficient range for {family_name}")
        if scaled_min != math.ldexp(original_min, -exponent) or (
            scaled_max != math.ldexp(original_max, -exponent)
        ):
            raise ValueError(f"Scaled coefficient range mismatch for {family_name}")
        if scaled_min < guard:
            raise ValueError(f"Unsafe scaled coefficient for {family_name}")
        digest = family.get("constraint_name_order_sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise ValueError(f"Invalid constraint-name digest for {family_name}")
        names = family.get("constraint_names")
        if (
            not isinstance(names, list)
            or len(names) != row_count
            or len(set(names)) != len(names)
            or any(
                not isinstance(name, str) or not name.startswith(expected_prefix)
                for name in names
            )
            or ordered_name_sha256(names) != digest
        ):
            raise ValueError(f"Invalid constraint-name registry for {family_name}")

    if model is not None:
        model.update()
        for family_name, metadata in families.items():
            names = metadata["constraint_names"]
            rows = []
            actual_minimum = math.inf
            actual_maximum = 0.0
            actual_nonzeros = 0
            row_scale = float(metadata["row_scale"])
            anchor_prefix = ANCHOR_VARIABLE_PREFIX_BY_FAMILY[family_name]
            for name in names:
                constraint = model.getConstrByName(name)
                if constraint is None:
                    raise ValueError(
                        f"Model row is missing for scaling family {family_name}: {name}"
                    )
                if constraint.Sense != "<" or float(constraint.RHS) != 0.0:
                    raise ValueError(
                        f"Scaled {family_name} row must have sense <= and zero RHS"
                    )
                expression = model.getRow(constraint)
                coefficients = np.asarray(
                    [expression.getCoeff(i) for i in range(expression.size())],
                    dtype=np.float64,
                )
                variables = [
                    expression.getVar(i) for i in range(expression.size())
                ]
                if (
                    not len(coefficients)
                    or not np.isfinite(coefficients).all()
                    or np.any(coefficients == 0.0)
                ):
                    raise ValueError(f"Invalid coefficients in scaled {family_name} row")
                positive = np.flatnonzero(coefficients > 0.0)
                negative = np.flatnonzero(coefficients < 0.0)
                if (
                    len(positive) != 1
                    or len(negative) != len(coefficients) - 1
                    or coefficients[positive[0]] != row_scale
                    or not variables[positive[0]].VarName.startswith(anchor_prefix)
                ):
                    raise ValueError(
                        f"Scaled {family_name} row has an invalid anchor or sign pattern"
                    )
                absolute = np.abs(coefficients)
                actual_minimum = min(actual_minimum, float(absolute.min()))
                actual_maximum = max(actual_maximum, float(absolute.max()))
                actual_nonzeros += len(coefficients)
                rows.append(constraint)
            metadata = families[family_name]
            if actual_nonzeros != int(metadata["matrix_nonzeros_scaled"]):
                raise ValueError(
                    f"Model row nonzeros differ for scaling family {family_name}"
                )
            if rows and (
                actual_minimum != float(metadata["scaled_coefficient_min_abs"])
                or actual_maximum
                != float(metadata["scaled_coefficient_max_abs"])
            ):
                raise ValueError(
                    f"Model coefficient range differs for scaling family {family_name}"
                )
    return registry


def active_row_scaling_registry(registry: Any) -> dict[str, Any] | None:
    """Normalize a fully validated legacy/unscaled registry to ``None``."""
    validated = validate_row_scaling_registry(registry)
    if validated is None:
        return None
    return (
        validated
        if any(
            int(family["exponent"]) > 0
            for family in validated["families"].values()
        )
        else None
    )
