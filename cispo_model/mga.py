"""Guarded modelling-to-generate-alternatives (MGA) support.

MGA is deliberately separate from the Base least-cost result.  A valid,
scientific full-year Base output supplies a cost cap; the rebuilt LP then
optimizes one explicitly declared capacity alternative subject to that cap.
Diagnostic horizons and alternative MGA outputs can never become an MGA
baseline or a sequential planning state.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import gurobipy as gp
import numpy as np
import pandas as pd
from gurobipy import GRB

from .config import ModelConfig
from .data import STORAGE_TECHS, VRE_TECHS, ModelData
from .io_contract import sha256_file, validate_result_manifest
from .master import MasterArtifacts
from .run_contract import solver_result_is_accepted


MGA_SCHEMA_VERSION = 1


class MGAError(ValueError):
    """Raised when an MGA request is not reproducible or scientifically scoped."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise MGAError(f"MGA {label} is missing: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise MGAError(f"MGA {label} is not valid JSON: {path}") from error
    if not isinstance(payload, dict):
        raise MGAError(f"MGA {label} must be a JSON object: {path}")
    return payload


def load_mga_spec(path: str | Path) -> tuple[Path, dict[str, Any]]:
    """Load a compact, explicit secondary-objective specification."""
    path = Path(path).resolve()
    spec = _read_json(path, "specification")
    if spec.get("schema_version") != MGA_SCHEMA_VERSION:
        raise MGAError(
            f"MGA specification schema_version must be {MGA_SCHEMA_VERSION}"
        )
    identifier = spec.get("id")
    if not isinstance(identifier, str) or not identifier.strip():
        raise MGAError("MGA specification requires a non-empty id")
    slack = spec.get("cost_slack")
    if not isinstance(slack, dict) or set(slack) != {"relative"}:
        raise MGAError("MGA cost_slack must contain exactly relative")
    try:
        relative_slack = float(slack["relative"])
    except (TypeError, ValueError) as error:
        raise MGAError("MGA cost_slack.relative must be numeric") from error
    if not np.isfinite(relative_slack) or relative_slack < 0.0:
        raise MGAError("MGA cost_slack.relative must be finite and non-negative")
    target = spec.get("secondary_objective")
    if not isinstance(target, dict):
        raise MGAError("MGA specification requires secondary_objective")
    if target.get("direction") not in {"minimize", "maximize"}:
        raise MGAError("MGA secondary_objective.direction must be minimize or maximize")
    asset_type = target.get("asset_type")
    supported = {
        "vre_new_capacity_gw",
        "wave_new_capacity_gw",
        "hydro_new_capacity_gw",
        "storage_new_power_gw",
    }
    if asset_type not in supported:
        raise MGAError(
            "MGA secondary_objective.asset_type must be one of "
            + ", ".join(sorted(supported))
        )
    if asset_type == "vre_new_capacity_gw":
        technology = target.get("technology")
        if technology not in VRE_TECHS:
            raise MGAError(f"MGA VRE technology must be one of {', '.join(VRE_TECHS)}")
    if asset_type == "storage_new_power_gw":
        technology = target.get("technology")
        if technology not in STORAGE_TECHS:
            raise MGAError(
                f"MGA storage technology must be one of {', '.join(STORAGE_TECHS)}"
            )
    for key in ("province_code", "grid_uid", "hydrochn_row_id"):
        if key in target and target[key] is None:
            raise MGAError(f"MGA selector {key} must be omitted rather than null")
    return path, spec


def _required_input_hashes(path: Path) -> dict[tuple[str, str], str]:
    frame = pd.read_csv(path)
    required = frame.required.astype(bool)
    selected = frame.loc[required, ["kind", "logical_path", "sha256"]]
    if selected.sha256.isna().any():
        raise MGAError(f"Required input manifest contains missing SHA256: {path}")
    return {
        (str(row.kind), str(row.logical_path)): str(row.sha256)
        for row in selected.itertuples(index=False)
    }


def validate_mga_baseline(
    baseline_root: str | Path,
    config: ModelConfig,
    current_input_manifest: str | Path,
) -> dict[str, Any]:
    """Return provenance for an accepted annual least-cost Base baseline.

    The comparison intentionally uses resolved configuration and required input
    hashes, rather than absolute paths or a Git commit.  The current runner can
    legitimately add MGA-only code without changing the Base mathematics.
    """
    baseline_root = Path(baseline_root).resolve()
    current_input_manifest = Path(current_input_manifest).resolve()
    valid, failures = validate_result_manifest(baseline_root)
    if not valid:
        raise MGAError(
            "MGA baseline result_manifest is not closed: " + "; ".join(failures)
        )
    scope = _read_json(baseline_root / "run_scope.json", "baseline run_scope")
    report = _read_json(baseline_root / "solve_report.json", "baseline solve_report")
    qc = _read_json(baseline_root / "solution_qc.json", "baseline solution_qc")
    snapshot = _read_json(
        baseline_root / "model_config_snapshot.json", "baseline model_config_snapshot"
    )
    if scope.get("result_use") != "SCIENTIFIC_PRODUCTION":
        raise MGAError("MGA baseline must be an accepted full-year scientific result")
    if scope.get("analysis_mode", "BASE_MINIMUM_COST") != "BASE_MINIMUM_COST":
        raise MGAError("An MGA output cannot be reused as an MGA baseline")
    if scope.get("horizon") != "full_year" or int(scope.get("optimization_hours", -1)) != config.hours:
        raise MGAError("MGA baseline must use the configured full-year horizon")
    if scope.get("scenario_id") != "base" or config.raw["scenario"]["id"] != "base":
        raise MGAError("MGA currently requires the least-cost base scenario")
    for key, expected in (
        ("planning_year", config.planning_year),
        ("boundary_year", config.boundary_year),
    ):
        if int(scope.get(key, -1)) != expected:
            raise MGAError(f"MGA baseline {key} differs from the requested run")
    if not solver_result_is_accepted(
        report,
        qc,
        result_manifest_valid=valid,
    ):
        raise MGAError(
            "MGA baseline requires an accepted solver contract, finite QC, "
            "strict hard checks and a closed result manifest"
        )
    try:
        baseline_cost = float(report["objective_value_million_cny"])
    except (KeyError, TypeError, ValueError) as error:
        raise MGAError("MGA baseline has no finite primary objective value") from error
    if not np.isfinite(baseline_cost) or baseline_cost < 0.0:
        raise MGAError("MGA baseline primary objective must be finite and non-negative")
    if snapshot.get("resolved_configuration") != config.raw:
        raise MGAError("MGA baseline resolved configuration differs from the requested run")
    baseline_hashes = _required_input_hashes(baseline_root / "input_manifest.csv")
    current_hashes = _required_input_hashes(current_input_manifest)
    if baseline_hashes != current_hashes:
        missing = sorted(set(baseline_hashes).symmetric_difference(current_hashes))
        changed = sorted(
            key
            for key in set(baseline_hashes).intersection(current_hashes)
            if baseline_hashes[key] != current_hashes[key]
        )
        details = [
            "MGA baseline required inputs differ from the requested run",
            *(f"missing_or_added={kind}:{logical}" for kind, logical in missing[:5]),
            *(f"hash_changed={kind}:{logical}" for kind, logical in changed[:5]),
        ]
        raise MGAError("; ".join(details))
    manifest_path = baseline_root / "result_manifest.json"
    return {
        "baseline_root": str(baseline_root),
        "baseline_result_manifest_sha256": sha256_file(manifest_path),
        "baseline_git_commit": json.loads(manifest_path.read_text(encoding="utf-8")).get(
            "git_commit"
        ),
        "baseline_objective_million_cny": baseline_cost,
        "planning_year": config.planning_year,
        "boundary_year": config.boundary_year,
        "scenario_id": "base",
        "input_manifest_sha256": sha256_file(current_input_manifest),
    }


def prepare_mga_request(
    spec_path: str | Path,
    baseline_root: str | Path,
    config: ModelConfig,
    current_input_manifest: str | Path,
) -> dict[str, Any]:
    """Validate immutable inputs before allocating a Gurobi model."""
    spec_path, spec = load_mga_spec(spec_path)
    baseline = validate_mga_baseline(baseline_root, config, current_input_manifest)
    baseline_cost = float(baseline["baseline_objective_million_cny"])
    relative_slack = float(spec["cost_slack"]["relative"])
    return {
        "schema_version": MGA_SCHEMA_VERSION,
        "analysis_mode": "MGA_CONSTRAINED_SECONDARY_OBJECTIVE",
        "mga_spec_path": str(spec_path),
        "mga_spec_sha256": sha256_file(spec_path),
        "mga_id": spec["id"],
        "secondary_objective": spec["secondary_objective"],
        "cost_slack_relative": relative_slack,
        "baseline": baseline,
        "cost_cap_million_cny": baseline_cost * (1.0 + relative_slack),
    }


def _selector_digest(values: list[str]) -> str:
    return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()


def _filter_frame(
    frame: pd.DataFrame,
    target: dict[str, Any],
    *,
    technology_column: str | None = None,
) -> np.ndarray:
    mask = np.ones(len(frame), dtype=bool)
    if technology_column is not None:
        mask &= frame[technology_column].astype(str).eq(str(target["technology"])).to_numpy()
    if "province_code" in target:
        mask &= frame.province_code.astype(int).eq(int(target["province_code"])).to_numpy()
    if "grid_uid" in target:
        if "grid_uid" not in frame:
            raise MGAError("MGA grid_uid selector is not available for this asset type")
        mask &= frame.grid_uid.astype(str).eq(str(target["grid_uid"])).to_numpy()
    if "hydrochn_row_id" in target:
        if "hydrochn_row_id" not in frame:
            raise MGAError("MGA hydrochn_row_id selector is not available for this asset type")
        mask &= frame.hydrochn_row_id.astype(str).eq(
            str(target["hydrochn_row_id"])
        ).to_numpy()
    return mask


def _assert_expandable(variable: gp.MVar, positions: np.ndarray, label: str) -> None:
    upper = np.asarray(variable.UB, dtype=float).reshape(-1)
    if not np.any(upper[positions] > 1e-10):
        raise MGAError(f"MGA selection has no expandable {label} variable")


def build_secondary_objective(
    artifacts: MasterArtifacts,
    data: ModelData,
    request: dict[str, Any],
) -> tuple[gp.LinExpr, dict[str, Any]]:
    """Build one explicit alternative-capacity objective without touching Base cost."""
    target = dict(request["secondary_objective"])
    asset_type = target["asset_type"]
    if asset_type == "vre_new_capacity_gw":
        mask = _filter_frame(data.vre_sites, target, technology_column="technology")
        positions = np.flatnonzero(mask)
        variable = artifacts.variables["vre_new"]
        selected = data.vre_sites.loc[mask, "grid_uid"].astype(str).tolist()
        label = "VRE"
    elif asset_type == "wave_new_capacity_gw":
        if data.wave is None or "wave_new" not in artifacts.variables:
            raise MGAError("MGA wave target requires wave-enabled Base data")
        mask = _filter_frame(data.wave.sites, target)
        positions = np.flatnonzero(mask)
        variable = artifacts.variables["wave_new"]
        selected = data.wave.sites.loc[mask, "grid_uid"].astype(str).tolist()
        label = "wave"
    elif asset_type == "hydro_new_capacity_gw":
        mask = _filter_frame(data.hydro_stations, target)
        positions = np.flatnonzero(mask)
        variable = artifacts.variables["hydro_new"]
        selected = data.hydro_stations.loc[mask, "hydrochn_row_id"].astype(str).tolist()
        label = "hydropower"
    elif asset_type == "storage_new_power_gw":
        provinces = np.asarray(artifacts.index["province_codes"], dtype=int)
        mask = np.ones(len(provinces), dtype=bool)
        if "province_code" in target:
            mask &= provinces == int(target["province_code"])
        positions = np.flatnonzero(mask)
        technology_index = artifacts.index["storage_index"]
        technology = str(target["technology"])
        variable = artifacts.variables["storage_new"][:, technology_index[technology]]
        selected = [str(value) for value in provinces[positions]]
        label = f"storage {technology}"
    else:  # Protected by load_mga_spec; retain a defensive branch for callers.
        raise MGAError(f"Unsupported MGA asset_type: {asset_type}")
    if not len(positions):
        raise MGAError("MGA secondary-objective selector matched no assets")
    _assert_expandable(variable, positions, label)
    expression = variable[positions].sum()
    return expression, {
        "asset_type": asset_type,
        "selector": target,
        "selected_asset_count": int(len(positions)),
        "selected_asset_ids_sha256": _selector_digest(selected),
        "unit": "GW",
    }


def primary_cost_expression(artifacts: MasterArtifacts) -> gp.LinExpr:
    """Return the original Base annual-cost expression, before MGA replacement."""
    return gp.quicksum(
        expression
        for name, expression in artifacts.cost_components.items()
        if not name.startswith("operating_")
    )


def apply_mga_secondary_objective(
    artifacts: MasterArtifacts,
    data: ModelData,
    request: dict[str, Any],
) -> dict[str, Any]:
    """Add a cost cap then replace only the solver's secondary objective."""
    model = artifacts.model
    # Bounds are materialized only after update; the expandability guard below
    # must therefore run after all Base variables and bounds are committed.
    model.update()
    primary_cost = primary_cost_expression(artifacts)
    target_expression, target_metadata = build_secondary_objective(artifacts, data, request)
    cap = float(request["cost_cap_million_cny"])
    if not np.isfinite(cap) or cap < 0.0:
        raise MGAError("MGA cost cap must be finite and non-negative")
    constraint_name = f"mga_primary_cost_cap_{request['mga_id']}"
    model.addConstr(primary_cost <= cap, name=constraint_name)
    direction = request["secondary_objective"]["direction"]
    model.setObjective(
        target_expression,
        GRB.MINIMIZE if direction == "minimize" else GRB.MAXIMIZE,
    )
    model.update()
    metadata = {
        **request,
        "primary_cost_constraint": constraint_name,
        "secondary_objective_metadata": target_metadata,
        "secondary_objective_direction": direction,
    }
    artifacts.index["mga"] = metadata
    artifacts.index["mga_primary_cost_expression"] = primary_cost
    return metadata


def evaluate_mga_solution(artifacts: MasterArtifacts) -> dict[str, Any] | None:
    """Evaluate Base cost and secondary target after an MGA solve."""
    metadata = artifacts.index.get("mga")
    if metadata is None:
        return None
    primary_cost = float(artifacts.index["mga_primary_cost_expression"].getValue())
    cap = float(metadata["cost_cap_million_cny"])
    return {
        **metadata,
        "primary_cost_value_million_cny": primary_cost,
        "cost_cap_slack_million_cny": cap - primary_cost,
        "secondary_objective_value_gw": float(artifacts.model.ObjVal),
    }
