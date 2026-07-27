"""Guarded Gurobi LP-basis reuse for CISPO diagnostic gates.

A ``.bas`` file preserves LP basis statuses after crossover.  It does *not*
serialize a live Gurobi model, presolve reductions, or a Barrier
factorization.  The latter are process-local and must never be assumed to be
portable across planning years.  Accordingly this module only permits basis
reuse for explicitly test-only horizons whose complete named structure can be
hashed within a conservative sparse-matrix safety limit.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import ModelConfig, ROOT
from .io_contract import sha256_file, validate_result_manifest


BASIS_SCHEMA_VERSION = "cispo_lp_basis_reuse_v1"
DEFAULT_MAX_IDENTITY_NONZEROS = 50_000_000


class BasisReuseError(ValueError):
    """Raised when a basis artifact cannot be safely reused."""


def _hash_strings(values: list[str], *, tag: str) -> str:
    digest = hashlib.sha256()
    digest.update(tag.encode("utf-8"))
    digest.update(b"\0")
    for value in values:
        encoded = str(value).encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def model_structure_identity(
    model: Any,
    *,
    max_nonzeros: int = DEFAULT_MAX_IDENTITY_NONZEROS,
) -> dict[str, Any]:
    """Hash the ordered named LP structure without inspecting coefficients.

    Coefficients and RHS values may legitimately change from 2030 to 2040;
    names, senses and raw dimensions must not.  The size guard intentionally
    keeps this diagnostic contract away from the 8760h model until a scalable
    independently validated identity method is available.
    """
    if max_nonzeros < 1:
        raise BasisReuseError("max_nonzeros must be positive")
    model.update()
    nonzeros = int(model.NumNZs)
    if nonzeros > max_nonzeros:
        raise BasisReuseError(
            "LP basis structural identity exceeds the diagnostic safety limit: "
            f"{nonzeros} > {max_nonzeros} nonzeros. "
            "Do not apply automatic basis reuse to this model."
        )
    variables = model.getVars()
    constraints = model.getConstrs()
    variable_names = [str(value) for value in model.getAttr("VarName", variables)]
    constraint_names = [str(value) for value in model.getAttr("ConstrName", constraints)]
    constraint_senses = [str(value) for value in model.getAttr("Sense", constraints)]
    return {
        "variables": int(model.NumVars),
        "constraints": int(model.NumConstrs),
        "nonzeros": nonzeros,
        "variable_names_sha256": _hash_strings(variable_names, tag="variables"),
        "constraint_name_senses_sha256": _hash_strings(
            [f"{name}\0{sense}" for name, sense in zip(constraint_names, constraint_senses)],
            tag="constraints",
        ),
        "identity_limit_nonzeros": int(max_nonzeros),
    }


def _current_git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise BasisReuseError(f"Invalid required basis sidecar: {path}") from error


def export_warm_start_basis(
    model: Any,
    config: ModelConfig,
    output_dir: str | Path,
    *,
    solve_report: dict[str, Any],
    solution_qc: dict[str, Any],
    optimization_hours: int,
    result_use: str,
    max_nonzeros: int = DEFAULT_MAX_IDENTITY_NONZEROS,
) -> dict[str, Any]:
    """Write a crossover basis plus self-contained compatibility metadata."""
    if solve_report.get("status") != "OPTIMAL" or solution_qc.get("status") != "PASS":
        raise BasisReuseError("Only OPTIMAL + solution_qc=PASS results can export a basis")
    if result_use != "TEST_ONLY_TRUNCATED_HORIZON":
        raise BasisReuseError(
            "Automatic basis export is restricted to test-only horizons pending "
            "a full-year reuse validation protocol"
        )
    if int(getattr(model, "IsMIP", 0)):
        raise BasisReuseError("A CISPO LP basis cannot be exported from a MIP model")
    if int(solve_report.get("solver_parameters", {}).get("crossover", 0)) == 0:
        raise BasisReuseError("Basis export requires crossover to be enabled")
    identity = model_structure_identity(model, max_nonzeros=max_nonzeros)
    variables = model.getVars()
    constraints = model.getConstrs()
    try:
        # Querying both attributes verifies that Gurobi has a basic solution.
        variable_basis = model.getAttr("VBasis", variables)
        constraint_basis = model.getAttr("CBasis", constraints)
    except Exception as error:  # gurobipy errors vary between supported releases
        raise BasisReuseError(
            "Gurobi did not provide a post-crossover LP basis for this result"
        ) from error
    output_root = Path(output_dir)
    basis_path = output_root / "warm_start_basis.bas"
    model.write(str(basis_path))
    if not basis_path.is_file():
        raise BasisReuseError(f"Gurobi did not create expected basis file {basis_path}")
    environment = _read_json(output_root / "run_environment.json")
    snapshot = _read_json(output_root / "model_config_snapshot.json")
    metadata = {
        "schema_version": BASIS_SCHEMA_VERSION,
        "generated_at": datetime.now().astimezone().isoformat(),
        "basis_file": basis_path.name,
        "basis_sha256": sha256_file(basis_path),
        "basis_format": "gurobi_bas",
        "basis_solution": "OPTIMAL_POST_CROSSOVER",
        "source": {
            "planning_year": int(config.planning_year),
            "boundary_year": int(config.boundary_year),
            "optimization_hours": int(optimization_hours),
            "result_use": result_use,
            "scenario_id": str(config.raw["scenario"]["id"]),
            "git_commit": environment.get("git_commit"),
            "configuration_source_sha256": snapshot.get("source_sha256"),
            "scenario_source_sha256": snapshot.get("scenario_source_sha256"),
            "solver_profile_source_sha256": snapshot.get("solver_source_sha256"),
            "gurobi_version": environment.get("packages", {}).get("gurobipy"),
        },
        "model_structure_identity": identity,
        "basis_status_counts": {
            "variables": len(variable_basis),
            "constraints": len(constraint_basis),
        },
        "limitations": [
            "Does not serialize a live Gurobi model, presolve state, Barrier factorization, or crossover tableau.",
            "Only test-only horizons with explicit named-structure checks may import this artifact.",
            "A matching basis is an engineering acceleration attempt, not evidence that a changed-year solution is scientifically accepted.",
        ],
    }
    metadata_path = output_root / "warm_start_basis_manifest.json"
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return metadata


def prepare_basis_reuse(
    source_output_dir: str | Path,
    model: Any,
    config: ModelConfig,
    *,
    optimization_hours: int,
    result_use: str,
    allow_cross_year: bool,
    max_nonzeros: int = DEFAULT_MAX_IDENTITY_NONZEROS,
) -> dict[str, Any]:
    """Validate a source result and return a basis record ready for Gurobi."""
    if result_use != "TEST_ONLY_TRUNCATED_HORIZON":
        raise BasisReuseError(
            "Automatic basis reuse is blocked for scientific full-year runs; "
            "complete the separately approved full-year validation protocol first"
        )
    source_root = Path(source_output_dir).resolve()
    manifest_ok, manifest_issues = validate_result_manifest(source_root)
    if not manifest_ok:
        raise BasisReuseError(
            "Basis source result manifest is not closed: " + "; ".join(manifest_issues)
        )
    metadata = _read_json(source_root / "warm_start_basis_manifest.json")
    if metadata.get("schema_version") != BASIS_SCHEMA_VERSION:
        raise BasisReuseError("Unsupported basis manifest schema")
    source = metadata.get("source", {})
    solve = _read_json(source_root / "solve_report.json")
    qc = _read_json(source_root / "solution_qc.json")
    if solve.get("status") != "OPTIMAL" or qc.get("status") != "PASS":
        raise BasisReuseError("Basis source is not OPTIMAL + solution_qc=PASS")
    if source.get("result_use") != "TEST_ONLY_TRUNCATED_HORIZON":
        raise BasisReuseError("Basis source is not an explicitly test-only result")
    if int(source.get("optimization_hours", -1)) != int(optimization_hours):
        raise BasisReuseError("Basis source and target optimization hours differ")
    if str(source.get("scenario_id")) != str(config.raw["scenario"]["id"]):
        raise BasisReuseError("Basis source and target scenario_id differ")
    if str(source.get("git_commit")) != _current_git_commit():
        raise BasisReuseError("Basis source git commit differs from the current code")
    source_year = int(source.get("planning_year", -1))
    if source_year != int(config.planning_year) and not allow_cross_year:
        raise BasisReuseError(
            "Cross-year basis reuse requires explicit --allow-cross-year-basis"
        )
    basis_path = source_root / str(metadata.get("basis_file", ""))
    if not basis_path.is_file() or sha256_file(basis_path) != metadata.get("basis_sha256"):
        raise BasisReuseError("Basis file is missing or its SHA256 does not match")
    target_identity = model_structure_identity(model, max_nonzeros=max_nonzeros)
    if metadata.get("model_structure_identity") != target_identity:
        raise BasisReuseError(
            "Basis source and target named LP structures differ; cold solve is required"
        )
    return {
        "schema_version": BASIS_SCHEMA_VERSION,
        "basis_source_output_dir": str(source_root),
        "basis_source_result_manifest_sha256": sha256_file(source_root / "result_manifest.json"),
        "basis_source_manifest_sha256": sha256_file(
            source_root / "warm_start_basis_manifest.json"
        ),
        "basis_path": str(basis_path),
        "basis_sha256": str(metadata["basis_sha256"]),
        "source_planning_year": source_year,
        "target_planning_year": int(config.planning_year),
        "cross_year": source_year != int(config.planning_year),
        "optimization_hours": int(optimization_hours),
        "scenario_id": str(config.raw["scenario"]["id"]),
        "model_structure_identity": target_identity,
        "lp_warm_start": 2,
        "limitations": metadata.get("limitations", []),
    }


def apply_basis_reuse(model: Any, prepared: dict[str, Any]) -> None:
    """Read a checked ``.bas`` file and keep presolve via ``LPWarmStart=2``."""
    model.read(str(prepared["basis_path"]))
    model.update()
    model.Params.LPWarmStart = int(prepared["lp_warm_start"])
