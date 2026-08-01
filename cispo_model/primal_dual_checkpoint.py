"""Portable Barrier primal/dual checkpoints and deferred LP crossover.

The checkpoint deliberately stores the ordered raw-LP ``BarX`` and ``BarPi``
vectors, not a Barrier factorization.  It can therefore seed Gurobi's LP
warm-start crossover after the exact same LP has been rebuilt, but it cannot
resume Barrier iterations or bypass presolve/model construction.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from .config import ModelConfig
from .io_contract import (
    sha256_file,
    validate_input_manifest,
    validate_result_manifest,
)


CHECKPOINT_SCHEMA_VERSION = "cispo_barrier_primal_dual_checkpoint_v1"
CHECKPOINT_DIRECTORY = "barrier_checkpoint"
CHECKPOINT_MANIFEST = "barrier_checkpoint_manifest.json"


class PrimalDualCheckpointError(ValueError):
    """Raised when a Barrier checkpoint is incomplete or incompatible."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise PrimalDualCheckpointError(
            f"Invalid required checkpoint sidecar: {path}"
        ) from error
    if not isinstance(value, dict):
        raise PrimalDualCheckpointError(f"Expected a JSON object in {path}")
    return value


def _write_vector(model: Any, attribute: str, path: Path, expected: int) -> dict[str, Any]:
    """Write one ordered Gurobi attribute vector while bounding peak memory."""
    try:
        values = model.getAttr(attribute)
    except TypeError:
        # Retained for older object-oriented bindings that require an explicit
        # object collection. Gurobi 13 accepts the constant-interface form.
        objects = model.getVars() if attribute == "BarX" else model.getConstrs()
        values = model.getAttr(attribute, objects)
        del objects
    array = np.asarray(values, dtype="<f8")
    del values
    if array.ndim != 1 or int(array.size) != int(expected):
        raise PrimalDualCheckpointError(
            f"{attribute} length {array.size} does not match expected {expected}"
        )
    if not bool(np.isfinite(array).all()):
        raise PrimalDualCheckpointError(f"{attribute} contains non-finite values")
    temporary = path.with_suffix(path.suffix + ".part")
    with temporary.open("wb") as stream:
        np.save(stream, array, allow_pickle=False)
    temporary.replace(path)
    result = {
        "path": path.name,
        "attribute": attribute,
        "entries": int(array.size),
        "dtype": str(array.dtype),
        "bytes": int(path.stat().st_size),
        "sha256": sha256_file(path),
    }
    del array
    return result


def export_barrier_primal_dual_checkpoint(
    model: Any,
    config: ModelConfig,
    output_dir: str | Path,
    *,
    solve_report: dict[str, Any],
    optimization_hours: int,
    optimization_start_hour: int,
    result_use: str,
    solution_qc: dict[str, Any] | None,
    accepted_primary: bool,
) -> dict[str, Any]:
    """Export full ordered ``BarX``/``BarPi`` vectors plus strict identity.

    ``accepted_primary=True`` is reserved for an OPTIMAL nonbasic solve whose
    numerical contract and physics QC have both passed.  A checkpoint captured
    after an inline-crossover failure is marked recovery-only and is never, by
    itself, a scientifically accepted result.
    """
    if int(getattr(model, "IsMIP", 0)):
        raise PrimalDualCheckpointError("Barrier checkpoints require a continuous LP")
    contract = solve_report.get("solution_contract", {})
    barrier_status = contract.get("barrier_status_code")
    if barrier_status not in (None, 2):
        raise PrimalDualCheckpointError(
            f"Barrier status {barrier_status!r} is not OPTIMAL"
        )
    if accepted_primary:
        if (
            solve_report.get("status") != "OPTIMAL"
            or contract.get("mode") != "OPTIMAL_PRIMAL_DUAL_NONBASIC"
            or contract.get("acceptance_status") != "PASS"
            or solution_qc is None
            or solution_qc.get("status") != "PASS"
        ):
            raise PrimalDualCheckpointError(
                "Primary checkpoint requires OPTIMAL nonbasic contract and QC PASS"
            )
        hard_checks = solution_qc.get("hard_checks")
        if not isinstance(hard_checks, dict) or not hard_checks or not all(
            bool(value) for value in hard_checks.values()
        ):
            raise PrimalDualCheckpointError(
                "Primary checkpoint requires all solution QC hard checks to pass"
            )
    elif barrier_status != 2:
        raise PrimalDualCheckpointError(
            "Recovery checkpoint requires Gurobi 13 BarStatus=OPTIMAL"
        )

    output_root = Path(output_dir)
    checkpoint_root = output_root / CHECKPOINT_DIRECTORY
    checkpoint_root.mkdir(parents=False, exist_ok=False)
    model.update()
    primal = _write_vector(
        model,
        "BarX",
        checkpoint_root / "primal_barx.npy",
        int(model.NumVars),
    )
    dual = _write_vector(
        model,
        "BarPi",
        checkpoint_root / "dual_barpi.npy",
        int(model.NumConstrs),
    )
    run_identity = _read_json(output_root / "run_identity.json")
    run_scope = _read_json(output_root / "run_scope.json")
    input_manifest = output_root / "input_manifest.csv"
    input_valid, input_failures = validate_input_manifest(input_manifest)
    if not input_valid:
        raise PrimalDualCheckpointError(
            "Current input manifest is invalid: " + "; ".join(input_failures)
        )
    metadata = {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "generated_at": datetime.now().astimezone().isoformat(),
        "checkpoint_status": (
            "ACCEPTED_PRIMARY_BARRIER_SOLUTION"
            if accepted_primary
            else "RECOVERY_ONLY_UNACCEPTED_SOLVER_RESULT"
        ),
        "scientifically_accepted": bool(accepted_primary),
        "deferred_crossover_eligible": bool(accepted_primary),
        "source": {
            "planning_year": int(config.planning_year),
            "boundary_year": int(config.boundary_year),
            "optimization_hours": int(optimization_hours),
            "optimization_start_hour": int(optimization_start_hour),
            "result_use": result_use,
            "scenario_id": config.raw["scenario"]["id"],
            "solver_profile_id": config.raw.get("solver_profile", {}).get("id"),
            "input_manifest_sha256": sha256_file(input_manifest),
            "run_scope_result_use": run_scope.get("result_use"),
        },
        "identity_layers": {
            name: run_identity.get(name)
            for name in (
                "baseline_contract",
                "analysis_case",
                "scientific_case",
                "implementation_bundle",
                "data_roots",
                "lp_model",
            )
        },
        "solver_evidence": {
            "status": solve_report.get("status"),
            "status_code": solve_report.get("status_code"),
            "barrier_status_code": barrier_status,
            "solution_contract": contract,
            "solution_quality": solve_report.get("solution_quality"),
            "barrier_iterations": solve_report.get("iteration_counts", {}).get(
                "barrier"
            ),
            "runtime_seconds": solve_report.get("runtime_seconds"),
        },
        "vectors": {"primal": primal, "dual": dual},
        "reuse_contract": {
            "method": 2,
            "lp_warm_start": 2,
            "recommended_crossover": 1,
            "requires_exact_original_lp": True,
            "requires_full_pstart_and_dstart": True,
            "overwrites_source_result": False,
        },
        "limitations": [
            "Stores ordered primal and dual vectors, not a Barrier factorization or presolve state.",
            "Deferred crossover must rebuild the exact original LP and repeat presolve.",
            "A recovery-only checkpoint is forensic evidence and is not an accepted scientific result.",
            "Python object lists may add material transient memory during deferred start import.",
        ],
    }
    manifest_path = checkpoint_root / CHECKPOINT_MANIFEST
    manifest_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return metadata


def prepare_primal_dual_crossover(
    source_output_dir: str | Path,
    target_output_dir: str | Path,
    model: Any,
    config: ModelConfig,
    *,
    optimization_hours: int,
    optimization_start_hour: int,
    result_use: str,
) -> dict[str, Any]:
    """Validate an accepted checkpoint against the exact rebuilt target LP."""
    source_root = Path(source_output_dir).resolve()
    target_root = Path(target_output_dir).resolve()
    manifest_valid, failures = validate_result_manifest(source_root)
    if not manifest_valid:
        raise PrimalDualCheckpointError(
            "Checkpoint source result manifest is not closed: "
            + "; ".join(failures)
        )
    source_qc = _read_json(source_root / "solution_qc.json")
    source_solve = _read_json(source_root / "solve_report.json")
    if source_qc.get("status") != "PASS" or source_solve.get("status") != "OPTIMAL":
        raise PrimalDualCheckpointError("Checkpoint source is not OPTIMAL + QC PASS")
    checkpoint_root = source_root / CHECKPOINT_DIRECTORY
    metadata = _read_json(checkpoint_root / CHECKPOINT_MANIFEST)
    if metadata.get("schema_version") != CHECKPOINT_SCHEMA_VERSION:
        raise PrimalDualCheckpointError("Unsupported Barrier checkpoint schema")
    if not metadata.get("scientifically_accepted") or not metadata.get(
        "deferred_crossover_eligible"
    ):
        raise PrimalDualCheckpointError(
            "Recovery-only Barrier checkpoints cannot enter formal deferred crossover"
        )
    source = metadata.get("source", {})
    expected_scope = {
        "planning_year": int(config.planning_year),
        "optimization_hours": int(optimization_hours),
        "optimization_start_hour": int(optimization_start_hour),
        "result_use": result_use,
        "scenario_id": config.raw["scenario"]["id"],
    }
    for key, expected in expected_scope.items():
        if source.get(key) != expected:
            raise PrimalDualCheckpointError(
                f"Checkpoint source/target {key} differs: {source.get(key)!r} != {expected!r}"
            )
    source_input = source_root / "input_manifest.csv"
    target_input = target_root / "input_manifest.csv"
    target_valid, target_failures = validate_input_manifest(target_input)
    if not target_valid:
        raise PrimalDualCheckpointError(
            "Target input manifest is invalid: " + "; ".join(target_failures)
        )
    if sha256_file(source_input) != sha256_file(target_input):
        raise PrimalDualCheckpointError("Source and target input manifests differ")
    target_identity = _read_json(target_root / "run_identity.json")
    source_layers = metadata.get("identity_layers", {})
    for name in (
        "baseline_contract",
        "analysis_case",
        "scientific_case",
        "implementation_bundle",
        "data_roots",
        "lp_model",
    ):
        if source_layers.get(name) != target_identity.get(name):
            raise PrimalDualCheckpointError(
                f"Checkpoint source and target identity layer {name} differs"
            )
    model.update()
    expected_counts = {
        "primal": int(model.NumVars),
        "dual": int(model.NumConstrs),
    }
    paths: dict[str, str] = {}
    for role, expected in expected_counts.items():
        row = metadata.get("vectors", {}).get(role, {})
        path = checkpoint_root / str(row.get("path", ""))
        if (
            not path.is_file()
            or int(row.get("entries", -1)) != expected
            or int(row.get("bytes", -1)) != path.stat().st_size
            or str(row.get("sha256")) != sha256_file(path)
        ):
            raise PrimalDualCheckpointError(
                f"Checkpoint {role} vector is missing, truncated, or incompatible"
            )
        array = np.load(path, mmap_mode="r", allow_pickle=False)
        if array.ndim != 1 or int(array.size) != expected or array.dtype != np.dtype("<f8"):
            raise PrimalDualCheckpointError(
                f"Checkpoint {role} array metadata does not match target LP"
            )
        del array
        paths[role] = str(path)
    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "source_output_dir": str(source_root),
        "source_result_manifest_sha256": sha256_file(
            source_root / "result_manifest.json"
        ),
        "source_checkpoint_manifest_sha256": sha256_file(
            checkpoint_root / CHECKPOINT_MANIFEST
        ),
        "primal_path": paths["primal"],
        "dual_path": paths["dual"],
        "variables": expected_counts["primal"],
        "constraints": expected_counts["dual"],
        "lp_warm_start": 2,
        "materializes_python_model_object_lists": True,
        "result_use": result_use,
    }


def apply_primal_dual_crossover_start(model: Any, prepared: dict[str, Any]) -> None:
    """Apply full PStart/DStart vectors to an already rebuilt exact LP."""
    model.update()
    primal = np.load(prepared["primal_path"], mmap_mode="r", allow_pickle=False)
    dual = np.load(prepared["dual_path"], mmap_mode="r", allow_pickle=False)
    if int(model.NumVars) != int(primal.size):
        del primal, dual
        raise PrimalDualCheckpointError("Target variable count changed before PStart import")
    if int(model.NumConstrs) != int(dual.size):
        del primal, dual
        raise PrimalDualCheckpointError(
            "Target constraint count changed before DStart import"
        )
    variables = model.getVars()
    if len(variables) != int(primal.size):
        del variables, primal, dual
        raise PrimalDualCheckpointError("Target variable count changed before PStart import")
    model.setAttr("PStart", variables, primal)
    del variables, primal
    constraints = model.getConstrs()
    if len(constraints) != int(dual.size):
        del constraints, dual
        raise PrimalDualCheckpointError(
            "Target constraint count changed before DStart import"
        )
    model.setAttr("DStart", constraints, dual)
    del constraints, dual
    model.update()
    model.Params.LPWarmStart = int(prepared["lp_warm_start"])
