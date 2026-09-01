"""Selective post-solve artifacts for an accepted scientific Base LP."""
from __future__ import annotations

import gzip
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from .annual_energy_coordinate import resolve_annual_energy_coordinate
from .basis_reuse import lightweight_lp_identity
from .config import ModelConfig
from .io_contract import sha256_file


class SolverArtifactError(ValueError):
    """Raised when a requested scientific solver artifact is unsafe."""


def _gzip_and_remove(source: Path, target: Path) -> None:
    with source.open("rb") as input_handle, gzip.open(
        target, "wb", compresslevel=6
    ) as output_handle:
        shutil.copyfileobj(input_handle, output_handle, length=1024 * 1024)
    source.unlink()


def export_scientific_base_solver_artifacts(
    model: Any,
    config: ModelConfig,
    output_dir: str | Path,
    *,
    solve_report: dict[str, Any],
    solution_qc: dict[str, Any],
    result_use: str,
) -> dict[str, Any]:
    """Export a compact, opt-in Base solution/basis checkpoint.

    This saves a Gurobi solution, the post-crossover LP basis, active solver
    parameters and a constant-memory model fingerprint.  It deliberately does
    not materialize the full LP matrix or bulk-export RC/Pi/slack/sensitivity
    attributes; curated scientific dual exports remain the authoritative
    interpretable products.
    """
    if result_use != "SCIENTIFIC_PRODUCTION":
        raise SolverArtifactError(
            "Scientific solver artifacts require the configured full-year horizon"
        )
    if config.raw["scenario"].get("analysis_role") != "BASELINE":
        raise SolverArtifactError(
            "Scientific solver artifacts are restricted to the accepted Base case"
        )
    if solve_report.get("status") != "OPTIMAL":
        raise SolverArtifactError("Solver artifacts require OPTIMAL")
    if solution_qc.get("status") != "PASS":
        raise SolverArtifactError("Solver artifacts require solution_qc PASS")
    if int(getattr(model, "IsMIP", 0)):
        raise SolverArtifactError("Only a continuous LP can export this contract")
    if int(solve_report.get("solver_parameters", {}).get("crossover", 0)) == 0:
        raise SolverArtifactError(
            "A portable LP basis requires a completed crossover"
        )
    try:
        variable_basis = np.asarray(
            model.getAttr("VBasis", model.getVars()), dtype=int
        )
        constraint_basis = np.asarray(
            model.getAttr("CBasis", model.getConstrs()), dtype=int
        )
    except Exception as error:
        raise SolverArtifactError(
            "Gurobi did not expose a completed post-crossover LP basis"
        ) from error

    root = Path(output_dir)
    raw_solution = root / "base_solution.sol"
    raw_basis = root / "base_basis.bas"
    solution_path = root / "base_solution.sol.gz"
    basis_path = root / "base_basis.bas.gz"
    parameter_path = root / "base_solver.prm"
    model.write(str(raw_solution))
    model.write(str(raw_basis))
    model.write(str(parameter_path))
    _gzip_and_remove(raw_solution, solution_path)
    _gzip_and_remove(raw_basis, basis_path)

    identity = lightweight_lp_identity(model)
    fingerprint_path = root / "base_model_fingerprint.json"
    fingerprint_payload = {
        **identity,
        "schema_version": "cispo_scientific_base_model_fingerprint_v1",
        "planning_year": int(config.planning_year),
        "scenario_id": str(config.raw["scenario"]["id"]),
        "basis_status_counts": {
            "variables": {
                str(int(value)): int(count)
                for value, count in zip(
                    *np.unique(variable_basis, return_counts=True)
                )
            },
            "constraints": {
                str(int(value)): int(count)
                for value, count in zip(
                    *np.unique(constraint_basis, return_counts=True)
                )
            },
        },
        "conditioning": {
            "kappa": (
                float(model.Kappa)
                if np.isfinite(float(model.Kappa))
                else None
            ),
            "kappa_exact_computed": False,
        },
    }
    fingerprint_path.write_text(
        json.dumps(fingerprint_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    artifact_paths = [
        solution_path,
        basis_path,
        parameter_path,
        fingerprint_path,
    ]
    manifest = {
        "schema_version": "cispo_scientific_base_solver_artifacts_v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "result_use": result_use,
        "planning_year": int(config.planning_year),
        "scenario_id": str(config.raw["scenario"]["id"]),
        "analysis_role": str(config.raw["scenario"]["analysis_role"]),
        "annual_energy_coordinate": resolve_annual_energy_coordinate(
            config
        ).metadata(),
        "raw_solution_coordinate_note": (
            "base_solution.sol.gz uses solver-internal coordinates; apply the "
            "recorded annual_energy_coordinate transform before interpreting "
            "scaled annual account or intra-load-center flow values."
        ),
        "artifacts": [
            {
                "filename": path.name,
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in artifact_paths
        ],
        "reuse_scope": (
            "Checkpoint evidence only. Automatic cross-year or changed-matrix "
            "reuse is forbidden. A future MGA importer must verify this "
            "manifest, immutable inputs, Gurobi version and the pre-MGA model "
            "fingerprint before reading the basis."
        ),
        "excluded_bulk_attributes": [
            "full_variable_reduced_cost",
            "full_constraint_slack",
            "SAObjLow",
            "SAObjUp",
            "SARHSLow",
            "SARHSUp",
            "KappaExact",
        ],
    }
    manifest_path = root / "base_solver_artifact_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest
