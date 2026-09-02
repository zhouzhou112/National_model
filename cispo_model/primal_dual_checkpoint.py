"""Portable Barrier primal/dual checkpoints and deferred LP crossover.

The checkpoint deliberately stores the ordered raw-LP ``BarX`` and ``BarPi``
vectors, not a Barrier factorization.  It can therefore seed Gurobi's LP
warm-start crossover after the exact same LP has been rebuilt, but it cannot
resume Barrier iterations or bypass presolve/model construction.
"""
from __future__ import annotations

import csv
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from .config import ModelConfig
from .annual_capacity_link_scaling import (
    active_row_scaling_registry,
    validate_row_scaling_registry,
)
from .io_contract import (
    input_manifest_scientific_resume_identity,
    sha256_file,
    validate_input_manifest,
    validate_result_manifest,
)
from .run_contract import (
    qc_hard_checks_are_strictly_true,
    qc_payload_numbers_are_finite,
)


CHECKPOINT_SCHEMA_VERSION = "cispo_barrier_primal_dual_checkpoint_v1"
CHECKPOINT_DIRECTORY = "barrier_checkpoint"
CHECKPOINT_MANIFEST = "barrier_checkpoint_manifest.json"
ACCEPTED_CHECKPOINT_STATUS = "ACCEPTED_PRIMARY_BARRIER_SOLUTION"
ENGINEERING_CHECKPOINT_STATUS = "ENGINEERING_BARRIER_CHECKPOINT_ONLY"
RECOVERY_CHECKPOINT_STATUS = "RECOVERY_ONLY_UNACCEPTED_SOLVER_RESULT"
PENDING_QC_CHECKPOINT_STATUS = "PENDING_ORIGINAL_UNIT_QC"
DEFERRED_CROSSOVER_OPTIONAL_UNUSED_DATA_ROOTS = frozenset(
    {"CISPO_RAW_GRFR_ROOT"}
)


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


def _scientific_manifest_resolved_paths(manifest_path: Path) -> tuple[str, ...]:
    """Read solve-consumed paths while excluding the solver profile row."""
    try:
        with manifest_path.open(
            "r", encoding="utf-8-sig", newline=""
        ) as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None or not {
                "kind",
                "resolved_path",
            }.issubset(reader.fieldnames):
                raise PrimalDualCheckpointError(
                    f"Input manifest lacks root-usage columns: {manifest_path}"
                )
            return tuple(
                str(row["resolved_path"])
                for row in reader
                if row.get("kind") != "solver_configuration"
                and row.get("resolved_path")
            )
    except (OSError, UnicodeDecodeError, csv.Error) as error:
        raise PrimalDualCheckpointError(
            f"Cannot audit input-manifest data-root usage: {manifest_path}"
        ) from error


def _count_paths_under_root(paths: tuple[str, ...], root: object) -> int:
    if not isinstance(root, str) or not root:
        return 0
    normalized = root.rstrip("/\\")
    prefixes = (normalized + "/", normalized + "\\")
    return sum(
        path == normalized or path.startswith(prefixes)
        for path in paths
    )


def validate_checkpoint_data_root_compatibility(
    source_roots: object,
    target_roots: object,
    source_manifest: str | Path,
    target_manifest: str | Path,
) -> dict[str, Any]:
    """Allow only audited, unconsumed optional environment-root drift.

    Scientific source/target manifest equality is checked separately before
    this function.  ``CISPO_RAW_GRFR_ROOT`` is a readiness/provenance input for
    current solve packages and may be absent from an older shell environment.
    Its path may differ only when neither validated manifest consumes a file
    under the declared root.  Every consumed or non-allowlisted root remains
    exact-match fail-closed.
    """
    if not isinstance(source_roots, dict) or not isinstance(target_roots, dict):
        raise PrimalDualCheckpointError(
            "Checkpoint source or target data_roots identity is not an object"
        )
    source_paths = _scientific_manifest_resolved_paths(Path(source_manifest))
    target_paths = _scientific_manifest_resolved_paths(Path(target_manifest))
    differences: list[dict[str, Any]] = []
    for key in sorted(set(source_roots) | set(target_roots)):
        source_value = source_roots.get(key)
        target_value = target_roots.get(key)
        if source_value == target_value:
            continue
        source_usage = _count_paths_under_root(source_paths, source_value)
        target_usage = _count_paths_under_root(target_paths, target_value)
        difference = {
            "key": key,
            "source": source_value,
            "target": target_value,
            "source_scientific_manifest_path_count": source_usage,
            "target_scientific_manifest_path_count": target_usage,
        }
        if (
            key not in DEFERRED_CROSSOVER_OPTIONAL_UNUSED_DATA_ROOTS
            or source_usage
            or target_usage
        ):
            raise PrimalDualCheckpointError(
                "Checkpoint source and target identity layer data_roots differs "
                f"for {key}: source_usage={source_usage}, "
                f"target_usage={target_usage}"
            )
        differences.append(difference)
    return {
        "status": "PASS",
        "exact_match": not differences,
        "allowed_unused_optional_differences": differences,
        "allowlisted_optional_unused_roots": sorted(
            DEFERRED_CROSSOVER_OPTIONAL_UNUSED_DATA_ROOTS
        ),
        "policy": (
            "All consumed and non-allowlisted data roots must match exactly; "
            "an allowlisted optional root may differ only with zero manifest usage."
        ),
    }


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


def _compare_saved_vector_to_current_solution(
    model: Any,
    *,
    current_attribute: str,
    saved_path: Path,
    expected: int,
) -> dict[str, Any]:
    """Bind a saved Barrier vector to Gurobi's quality-audited current solution."""
    try:
        try:
            values = model.getAttr(current_attribute)
        except TypeError:
            objects = (
                model.getVars()
                if current_attribute == "X"
                else model.getConstrs()
            )
            values = model.getAttr(current_attribute, objects)
            del objects
        current = np.asarray(values, dtype="<f8")
        del values
        if current.ndim != 1 or int(current.size) != int(expected):
            raise ValueError(
                f"{current_attribute} length {current.size} != {expected}"
            )
        if not bool(np.isfinite(current).all()):
            raise ValueError(f"{current_attribute} contains non-finite values")
        saved = np.load(saved_path, mmap_mode="r", allow_pickle=False)
        maximum = 0.0
        chunk_size = 1_000_000
        for start in range(0, expected, chunk_size):
            stop = min(start + chunk_size, expected)
            difference = np.abs(current[start:stop] - saved[start:stop])
            if len(difference):
                maximum = max(maximum, float(difference.max()))
        del saved, current
        return {
            "status": "COLLECTED",
            "current_attribute": current_attribute,
            "maximum_absolute_difference": maximum,
            "entries_compared": int(expected),
        }
    except Exception as error:
        return {
            "status": "UNAVAILABLE_OR_INVALID",
            "current_attribute": current_attribute,
            "maximum_absolute_difference": None,
            "entries_compared": 0,
            "error_type": type(error).__name__,
            "error": str(error),
        }


def _current_solution_comparison_failures(
    vectors: dict[str, Any],
    *,
    expected_entries: dict[str, Any] | None = None,
) -> list[str]:
    """Require persisted Barrier vectors to be bitwise identical to X/Pi.

    Gurobi's reported primal/dual quality is attached to the current ``X`` and
    ``Pi`` solution.  A per-coordinate tolerance is not sufficient to transfer
    that certificate to ``BarX``/``BarPi`` because a large row or column
    1-norm can amplify individually small differences.  Scientific pending and
    accepted checkpoints therefore require exact float64 identity; engineering
    and forensic checkpoints may still be written, but cannot pass this gate.
    """
    failures: list[str] = []
    expected_attributes = {"primal": "X", "dual": "Pi"}
    for role in ("primal", "dual"):
        vector = vectors.get(role, {})
        comparison = vectors.get(role, {}).get(
            "current_solution_comparison", {}
        )
        try:
            difference = float(comparison["maximum_absolute_difference"])
            raw_compared_entries = comparison["entries_compared"]
            raw_vector_entries = vector["entries"]
            raw_expected_count = (expected_entries or {}).get(
                role, raw_vector_entries
            )
            if any(
                isinstance(value, bool)
                for value in (
                    raw_compared_entries,
                    raw_vector_entries,
                    raw_expected_count,
                )
            ):
                raise TypeError("Boolean vector count")
            compared_entries = int(raw_compared_entries)
            vector_entries = int(raw_vector_entries)
            expected_count = int(
                raw_expected_count
            )
        except (KeyError, TypeError, ValueError):
            failures.append(f"{role}_current_solution_comparison_metadata")
            continue
        if (
            comparison.get("status") != "COLLECTED"
            or comparison.get("current_attribute")
            != expected_attributes[role]
            or compared_entries <= 0
            or compared_entries != vector_entries
            or vector_entries != expected_count
            or not np.isfinite(difference)
            or difference != 0.0
        ):
            failures.append(f"{role}_current_solution_comparison")
    return failures


def _last_barrier_telemetry(path: Path) -> dict[str, Any] | None:
    """Return the last persisted Barrier callback sample without loading the log."""
    if not path.is_file():
        return None
    latest: dict[str, Any] | None = None
    try:
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if (
                    isinstance(record, dict)
                    and record.get("event") == "solver_progress"
                    and record.get("phase") == "barrier"
                ):
                    latest = record
    except OSError:
        return None
    if latest is None:
        return None
    primal = latest.get("primal_objective")
    dual = latest.get("dual_objective")
    if isinstance(primal, (int, float)) and isinstance(dual, (int, float)):
        absolute_gap = abs(float(primal) - float(dual))
        latest["absolute_primal_dual_objective_gap"] = absolute_gap
        latest["relative_primal_dual_objective_gap"] = absolute_gap / max(
            1.0, abs(float(primal)), abs(float(dual))
        )
    return latest


def _solver_evidence_failures(
    evidence: Any,
    solve_report: dict[str, Any],
    *,
    require_complete: bool,
) -> list[str]:
    """Bind checkpoint numerical evidence to the exact source solve report."""
    if not isinstance(evidence, dict):
        return ["solver_evidence_object"]
    expected = {
        "status": solve_report.get("status"),
        "status_code": solve_report.get("status_code"),
        "barrier_status_code": solve_report.get("solution_contract", {}).get(
            "barrier_status_code"
        ),
        "solution_contract": solve_report.get("solution_contract"),
        "solution_quality": solve_report.get("solution_quality"),
        "barrier_iterations": solve_report.get("iteration_counts", {}).get(
            "barrier"
        ),
        "objective_value_million_cny": solve_report.get(
            "objective_value_million_cny"
        ),
    }
    failures: list[str] = []
    for key, value in expected.items():
        try:
            recorded = json.dumps(
                evidence.get(key),
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            current = json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        except (TypeError, ValueError):
            failures.append(f"solver_evidence_nonfinite_or_invalid:{key}")
            continue
        if recorded != current:
            failures.append(f"solver_evidence_mismatch:{key}")
    if require_complete:
        objective = expected["objective_value_million_cny"]
        iterations = expected["barrier_iterations"]
        if (
            expected["status"] != "OPTIMAL"
            or expected["status_code"] != 2
            or expected["barrier_status_code"] != 2
            or not isinstance(expected["solution_contract"], dict)
            or expected["solution_contract"].get("acceptance_status")
            != "PASS"
            or not isinstance(expected["solution_quality"], dict)
            or not expected["solution_quality"]
            or isinstance(iterations, bool)
            or not isinstance(iterations, (int, np.integer))
            or int(iterations) <= 0
            or isinstance(objective, bool)
            or not isinstance(objective, (int, float, np.integer, np.floating))
            or not np.isfinite(float(objective))
        ):
            failures.append("solver_evidence_incomplete_for_acceptance")
    return failures


def _ordered_name_digest(
    model: Any,
    *,
    kind: str,
    chunk_size: int = 100_000,
) -> dict[str, Any]:
    """Hash the complete raw-LP object order without retaining all names."""
    if kind == "variable":
        objects = model.getVars()
        name_attribute = "VarName"
        auxiliary_attribute = None
        expected = int(model.NumVars)
    elif kind == "constraint":
        objects = model.getConstrs()
        name_attribute = "ConstrName"
        auxiliary_attribute = "Sense"
        expected = int(model.NumConstrs)
    else:
        raise PrimalDualCheckpointError(f"Unsupported order-digest kind: {kind}")
    if len(objects) != expected:
        del objects
        raise PrimalDualCheckpointError(
            f"{kind} object count changed while hashing LP order"
        )
    digest = hashlib.sha256()
    digest.update(f"cispo_raw_lp_{kind}_order_v1\0".encode("ascii"))
    digest.update(expected.to_bytes(8, "big", signed=False))
    for start in range(0, expected, chunk_size):
        chunk = objects[start : start + chunk_size]
        names = model.getAttr(name_attribute, chunk)
        auxiliaries = (
            model.getAttr(auxiliary_attribute, chunk)
            if auxiliary_attribute is not None
            else [""] * len(chunk)
        )
        for offset, (name, auxiliary) in enumerate(zip(names, auxiliaries)):
            index = start + offset
            encoded = str(name).encode("utf-8")
            digest.update(index.to_bytes(8, "big", signed=False))
            digest.update(len(encoded).to_bytes(8, "big", signed=False))
            digest.update(encoded)
            digest.update(str(auxiliary).encode("ascii"))
            digest.update(b"\0")
        del chunk, names, auxiliaries
    del objects
    return {
        "schema_version": f"cispo_raw_lp_{kind}_order_v1",
        "entries": expected,
        "sha256": digest.hexdigest(),
        "chunk_size": int(chunk_size),
    }


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
    engineering_only: bool = False,
    allow_incomplete_barrier: bool = False,
    pending_qc: bool = False,
    row_scaling_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Export full ordered ``BarX``/``BarPi`` vectors plus strict identity.

    ``accepted_primary=True`` is reserved for an OPTIMAL nonbasic solve whose
    numerical contract and physics QC have both passed. ``engineering_only``
    preserves an otherwise non-scientific Barrier result for an explicitly
    authorized deferred crossover. A checkpoint captured after an inline-
    crossover failure remains recovery-only and cannot enter that workflow.
    """
    if sum(bool(value) for value in (
        accepted_primary,
        engineering_only,
        allow_incomplete_barrier,
        pending_qc,
    )) > 1:
        raise PrimalDualCheckpointError(
            "A checkpoint can have only one accepted, engineering or incomplete mode"
        )
    if int(getattr(model, "IsMIP", 0)):
        raise PrimalDualCheckpointError("Barrier checkpoints require a continuous LP")
    contract = solve_report.get("solution_contract", {})
    barrier_status = contract.get("barrier_status_code")
    if barrier_status not in (None, 2) and not allow_incomplete_barrier:
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
        if not qc_hard_checks_are_strictly_true(solution_qc):
            raise PrimalDualCheckpointError(
                "Primary checkpoint requires all solution QC hard checks to pass"
            )
        if not qc_payload_numbers_are_finite(solution_qc):
            raise PrimalDualCheckpointError(
                "Primary checkpoint requires finite solution QC values"
            )
    elif pending_qc:
        if (
            solve_report.get("status") != "OPTIMAL"
            or contract.get("mode") != "OPTIMAL_PRIMAL_DUAL_NONBASIC"
            or contract.get("acceptance_status") != "PASS"
            or barrier_status != 2
        ):
            raise PrimalDualCheckpointError(
                "Pending-QC checkpoint requires an OPTIMAL nonbasic Barrier "
                "contract before semantic export"
            )
    elif not allow_incomplete_barrier and barrier_status != 2:
        raise PrimalDualCheckpointError(
            "Non-primary checkpoint requires Gurobi 13 BarStatus=OPTIMAL"
        )
    if engineering_only or allow_incomplete_barrier:
        parameters = solve_report.get("solver_parameters", {})
        if not (
            int(parameters.get("method", -1)) == 2
            and int(parameters.get("crossover", -1)) == 0
            and int(parameters.get("solution_target", -1)) == 1
        ):
            raise PrimalDualCheckpointError(
                "Barrier checkpoint requires Method=2, Crossover=0, "
                "SolutionTarget=1"
            )
    if allow_incomplete_barrier and int(
        solve_report.get("iteration_counts", {}).get("barrier", 0)
    ) <= 0:
        raise PrimalDualCheckpointError(
            "Incomplete Barrier recovery requires at least one Barrier iteration"
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
    primal["current_solution_comparison"] = (
        _compare_saved_vector_to_current_solution(
            model,
            current_attribute="X",
            saved_path=checkpoint_root / primal["path"],
            expected=int(model.NumVars),
        )
    )
    dual["current_solution_comparison"] = (
        _compare_saved_vector_to_current_solution(
            model,
            current_attribute="Pi",
            saved_path=checkpoint_root / dual["path"],
            expected=int(model.NumConstrs),
        )
    )
    comparison_failures = _current_solution_comparison_failures(
        {"primal": primal, "dual": dual},
        expected_entries={
            "primal": int(model.NumVars),
            "dual": int(model.NumConstrs),
        },
    )
    if (accepted_primary or pending_qc) and comparison_failures:
        raise PrimalDualCheckpointError(
            "Barrier checkpoint vectors differ from the quality-audited current "
            "solution: " + ", ".join(comparison_failures)
        )
    variable_order = _ordered_name_digest(model, kind="variable")
    constraint_order = _ordered_name_digest(model, kind="constraint")
    run_identity = _read_json(output_root / "run_identity.json")
    run_scope = _read_json(output_root / "run_scope.json")
    run_environment = _read_json(output_root / "run_environment.json")
    input_manifest = output_root / "input_manifest.csv"
    input_valid, input_failures = validate_input_manifest(input_manifest)
    if not input_valid:
        raise PrimalDualCheckpointError(
            "Current input manifest is invalid: " + "; ".join(input_failures)
        )
    validated_row_scaling_registry = validate_row_scaling_registry(
        row_scaling_registry, model=model
    )
    if accepted_primary:
        checkpoint_status = ACCEPTED_CHECKPOINT_STATUS
    elif engineering_only:
        checkpoint_status = ENGINEERING_CHECKPOINT_STATUS
    elif pending_qc:
        checkpoint_status = PENDING_QC_CHECKPOINT_STATUS
    else:
        checkpoint_status = RECOVERY_CHECKPOINT_STATUS
    lp_model = run_identity.get("lp_model") or {}
    metadata = {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "generated_at": datetime.now().astimezone().isoformat(),
        "checkpoint_status": checkpoint_status,
        "scientifically_accepted": bool(accepted_primary),
        "deferred_crossover_eligible": bool(accepted_primary or engineering_only),
        "eligibility_scope": (
            "CLOSED_ACCEPTED_SOURCE"
            if accepted_primary
            else (
                "EXPLICIT_ENGINEERING_ACKNOWLEDGEMENT_REQUIRED"
                if engineering_only
                else (
                    "PENDING_ORIGINAL_UNIT_QC"
                    if pending_qc
                    else "FORENSIC_ONLY"
                )
            )
        ),
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
            "scenario_config_sha256": (
                sha256_file(config.scenario_path) if config.scenario_path else None
            ),
            "solver_config_sha256": (
                sha256_file(config.solver_path) if config.solver_path else None
            ),
            "planning_state_in": run_environment.get("planning_state_in"),
            "gurobipy_version": run_environment.get("packages", {}).get(
                "gurobipy"
            ),
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
            "objective_value_million_cny": solve_report.get(
                "objective_value_million_cny"
            ),
            "last_persisted_barrier_telemetry": _last_barrier_telemetry(
                output_root / "solver_telemetry.jsonl"
            ),
        },
        "vectors": {"primal": primal, "dual": dual},
        "annual_capacity_link_row_scaling": validated_row_scaling_registry,
        "lp_ordering": {
            "variable_vector": "raw_original_model_variable_index_order",
            "constraint_vector": "raw_original_model_linear_constraint_index_order",
            "variables": int(model.NumVars),
            "constraints": int(model.NumConstrs),
            "nonzeros": int(model.NumNZs),
            "gurobi_fingerprint": lp_model.get("gurobi_fingerprint"),
            "variable_order_digest": variable_order,
            "constraint_order_digest": constraint_order,
            "validation": (
                "exact deterministic LP rebuild plus matching layered identity, "
                "input manifest, Gurobi Fingerprint and dimensions"
            ),
            "full_name_catalog_persisted": False,
            "full_name_catalog_omission_reason": (
                "complete ordered names are cryptographically hashed in chunks "
                "instead of persisting a multi-gigabyte string catalog"
            ),
        },
        "engineering_shadow_prices": {
            "available": True,
            "attribute": "BarPi",
            "path": dual["path"],
            "index_semantics": "raw_original_model_linear_constraint_index_order",
            "publication_status": (
                "SCIENTIFICALLY_ACCEPTED"
                if accepted_primary
                else (
                    "PENDING_ORIGINAL_UNIT_QC"
                    if pending_qc
                    else "ENGINEERING_ONLY_NOT_FOR_PUBLICATION"
                )
            ),
            "warning": (
                "Barrier duals may be non-unique on a degenerate LP and do not "
                "provide basis sensitivity ranges."
            ),
        },
        "reuse_contract": {
            "method": 2,
            "lp_warm_start": 2,
            "recommended_crossover": 2,
            "recommended_crossover_basis": 1,
            "requires_exact_original_lp": True,
            "requires_full_pstart_and_dstart": True,
            "overwrites_source_result": False,
        },
        "limitations": [
            "Stores ordered primal and dual vectors, not a Barrier factorization or presolve state.",
            "Deferred crossover must rebuild the exact original LP and repeat presolve.",
            "An engineering-only checkpoint is not an accepted scientific result; candidate capacity state requires explicit author adoption.",
            "A recovery-only checkpoint is forensic evidence and cannot seed the formal deferred crossover.",
            "Python object lists may add material transient memory during deferred start import.",
        ],
    }
    solver_evidence_failures = _solver_evidence_failures(
        metadata.get("solver_evidence"),
        solve_report,
        require_complete=bool(accepted_primary or pending_qc),
    )
    if solver_evidence_failures:
        raise PrimalDualCheckpointError(
            "Checkpoint solver evidence is incomplete or inconsistent: "
            + ", ".join(solver_evidence_failures)
        )
    manifest_path = checkpoint_root / CHECKPOINT_MANIFEST
    manifest_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    return metadata


def _array_is_finite(array: np.ndarray, chunk_size: int = 1_000_000) -> bool:
    return all(
        bool(np.isfinite(array[start : start + chunk_size]).all())
        for start in range(0, int(array.size), chunk_size)
    )


def _checkpoint_vector_integrity_failures(
    checkpoint_root: Path,
    metadata: dict[str, Any],
) -> list[str]:
    """Validate both ordered vectors independently of acceptance status."""
    failures: list[str] = []
    ordering = metadata.get("lp_ordering", {})
    expected_entries = {
        "primal": ordering.get("variables"),
        "dual": ordering.get("constraints"),
    }
    for role, attribute in (("primal", "BarX"), ("dual", "BarPi")):
        row = metadata.get("vectors", {}).get(role, {})
        relative = Path(str(row.get("path", "")))
        if relative.is_absolute() or len(relative.parts) != 1:
            failures.append(f"vector_path:{role}")
            continue
        path = checkpoint_root / relative
        if not path.is_file():
            failures.append(f"vector_missing:{role}")
            continue
        if row.get("attribute") != attribute:
            failures.append(f"vector_attribute:{role}")
        try:
            recorded_bytes = int(row.get("bytes", -1))
        except (TypeError, ValueError):
            recorded_bytes = -1
        if recorded_bytes != int(path.stat().st_size):
            failures.append(f"vector_bytes:{role}")
        if str(row.get("sha256")) != sha256_file(path):
            failures.append(f"vector_sha256:{role}")
        try:
            recorded_entries = int(row.get("entries", -1))
            lp_entries = int(expected_entries[role])
        except (TypeError, ValueError):
            recorded_entries = -1
            lp_entries = -2
        try:
            array = np.load(path, mmap_mode="r", allow_pickle=False)
            if (
                array.ndim != 1
                or int(array.size) != recorded_entries
                or recorded_entries != lp_entries
                or array.dtype != np.dtype("<f8")
            ):
                failures.append(f"vector_shape_or_dtype:{role}")
            elif not _array_is_finite(array):
                failures.append(f"vector_nonfinite:{role}")
            del array
        except (OSError, ValueError, TypeError):
            failures.append(f"vector_unreadable:{role}")
    return failures


def validate_checkpoint_vector_integrity(
    source_output_dir: str | Path,
) -> tuple[bool, list[str]]:
    """Check persisted BarX/BarPi before claiming preservation completeness."""
    source_root = Path(source_output_dir).resolve()
    checkpoint_root = source_root / CHECKPOINT_DIRECTORY
    try:
        metadata = _read_json(checkpoint_root / CHECKPOINT_MANIFEST)
    except PrimalDualCheckpointError as error:
        return False, [str(error)]
    failures: list[str] = []
    if metadata.get("schema_version") != CHECKPOINT_SCHEMA_VERSION:
        failures.append("schema_version")
    failures.extend(
        _checkpoint_vector_integrity_failures(checkpoint_root, metadata)
    )
    return not failures, failures


def promote_pending_qc_checkpoint(
    output_dir: str | Path,
    *,
    solve_report: dict[str, Any],
    solution_qc: dict[str, Any],
) -> dict[str, Any]:
    """Atomically promote already persisted BarX/BarPi after physical QC."""
    output_root = Path(output_dir)
    checkpoint_root = output_root / CHECKPOINT_DIRECTORY
    manifest_path = checkpoint_root / CHECKPOINT_MANIFEST
    metadata = _read_json(manifest_path)
    if metadata.get("checkpoint_status") != PENDING_QC_CHECKPOINT_STATUS:
        raise PrimalDualCheckpointError(
            "Only a pending-QC checkpoint can be promoted"
        )
    contract = solve_report.get("solution_contract", {})
    solution_qc_path = output_root / "solution_qc.json"
    persisted_solution_qc = _read_json(solution_qc_path)
    if (
        solve_report.get("status") != "OPTIMAL"
        or contract.get("mode") != "OPTIMAL_PRIMAL_DUAL_NONBASIC"
        or contract.get("acceptance_status") != "PASS"
        or persisted_solution_qc != solution_qc
        or persisted_solution_qc.get("status") != "PASS"
        or not qc_hard_checks_are_strictly_true(persisted_solution_qc)
        or not qc_payload_numbers_are_finite(persisted_solution_qc)
    ):
        raise PrimalDualCheckpointError(
            "Checkpoint promotion requires solver-contract PASS and every "
            "original-unit QC hard check to pass"
        )
    solver_evidence_failures = _solver_evidence_failures(
        metadata.get("solver_evidence"),
        solve_report,
        require_complete=True,
    )
    if solver_evidence_failures:
        raise PrimalDualCheckpointError(
            "Pending checkpoint solver evidence differs from solve report: "
            + ", ".join(solver_evidence_failures)
        )
    validate_row_scaling_registry(
        metadata.get("annual_capacity_link_row_scaling")
    )
    stored_registry = active_row_scaling_registry(
        metadata.get("annual_capacity_link_row_scaling")
    )
    report_registry = active_row_scaling_registry(
        solve_report.get("annual_capacity_link_row_scaling")
    )
    if stored_registry != report_registry:
        raise PrimalDualCheckpointError(
            "Pending checkpoint row-scaling registry differs from solve report"
        )
    comparison_failures = _current_solution_comparison_failures(
        metadata.get("vectors", {}),
        expected_entries={
            "primal": metadata.get("lp_ordering", {}).get("variables"),
            "dual": metadata.get("lp_ordering", {}).get("constraints"),
        },
    )
    if comparison_failures:
        raise PrimalDualCheckpointError(
            "Pending checkpoint current-solution comparison failed: "
            + ", ".join(comparison_failures)
        )
    vector_failures = _checkpoint_vector_integrity_failures(
        checkpoint_root, metadata
    )
    if vector_failures:
        raise PrimalDualCheckpointError(
            "Pending checkpoint vector integrity failed: "
            + ", ".join(vector_failures)
        )
    metadata.update(
        checkpoint_status=ACCEPTED_CHECKPOINT_STATUS,
        scientifically_accepted=True,
        deferred_crossover_eligible=True,
        eligibility_scope="CLOSED_ACCEPTED_SOURCE",
        promoted_at=datetime.now().astimezone().isoformat(),
        acceptance_evidence={
            "solution_qc_status": persisted_solution_qc.get("status"),
            "solution_qc_sha256": sha256_file(solution_qc_path),
            "all_hard_checks_pass": True,
        },
    )
    metadata["engineering_shadow_prices"]["publication_status"] = (
        "SCIENTIFICALLY_ACCEPTED"
    )
    temporary = manifest_path.with_suffix(manifest_path.suffix + ".part")
    temporary.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(manifest_path)
    return metadata


def validate_barrier_primal_dual_checkpoint(
    source_output_dir: str | Path,
    *,
    require_result_manifest: bool = True,
    allow_engineering: bool = False,
) -> tuple[bool, list[str]]:
    """Validate a Barrier checkpoint without rebuilding the LP.

    The default remains the strict accepted-source gate used by planning-state
    export and sequence resume. Engineering checkpoints require an explicit
    opt-in and can only be consumed by the second exact-LP gate in
    :func:`prepare_primal_dual_crossover`.
    """
    source_root = Path(source_output_dir).resolve()
    failures: list[str] = []
    try:
        solve = _read_json(source_root / "solve_report.json")
        run_identity = _read_json(source_root / "run_identity.json")
        checkpoint_root = source_root / CHECKPOINT_DIRECTORY
        metadata = _read_json(checkpoint_root / CHECKPOINT_MANIFEST)
    except PrimalDualCheckpointError as error:
        failures.append(str(error))
        return False, failures
    try:
        validate_row_scaling_registry(
            metadata.get("annual_capacity_link_row_scaling")
        )
    except ValueError as error:
        failures.append(f"row_scaling_registry:{error}")

    checkpoint_status = metadata.get("checkpoint_status")
    engineering = checkpoint_status == ENGINEERING_CHECKPOINT_STATUS
    accepted = checkpoint_status == ACCEPTED_CHECKPOINT_STATUS
    if engineering and not allow_engineering:
        failures.append("engineering_checkpoint_requires_explicit_allow")
    if not accepted and not engineering:
        failures.append("checkpoint_status")
    failures.extend(
        _solver_evidence_failures(
            metadata.get("solver_evidence"),
            solve,
            require_complete=accepted,
        )
    )
    if require_result_manifest:
        manifest_valid, manifest_failures = validate_result_manifest(source_root)
        if not manifest_valid:
            failures.extend(
                f"result_manifest:{failure}" for failure in manifest_failures
            )
    contract = solve.get("solution_contract", {})
    if accepted:
        try:
            qc = _read_json(source_root / "solution_qc.json")
        except PrimalDualCheckpointError as error:
            failures.append(str(error))
            qc = {}
        if solve.get("status") != "OPTIMAL":
            failures.append("solve_status")
        if contract.get("mode") != "OPTIMAL_PRIMAL_DUAL_NONBASIC":
            failures.append("solution_contract_mode")
        if contract.get("acceptance_status") != "PASS":
            failures.append("solution_contract_acceptance")
        if qc.get("status") != "PASS":
            failures.append("solution_qc_status")
        if not qc_hard_checks_are_strictly_true(qc):
            failures.append("solution_qc_hard_checks")
        if not qc_payload_numbers_are_finite(qc):
            failures.append("solution_qc_nonfinite")
        failures.extend(
            "checkpoint_" + failure
            for failure in _current_solution_comparison_failures(
                metadata.get("vectors", {}),
                expected_entries={
                    "primal": metadata.get("lp_ordering", {}).get(
                        "variables"
                    ),
                    "dual": metadata.get("lp_ordering", {}).get(
                        "constraints"
                    ),
                },
            )
        )
        evidence = metadata.get("acceptance_evidence")
        solution_qc_path = source_root / "solution_qc.json"
        if not isinstance(evidence, dict):
            failures.append("acceptance_evidence")
        else:
            if evidence.get("solution_qc_status") != qc.get("status"):
                failures.append("acceptance_evidence_solution_qc_status")
            if evidence.get("all_hard_checks_pass") is not True:
                failures.append("acceptance_evidence_hard_checks")
            if (
                not solution_qc_path.is_file()
                or evidence.get("solution_qc_sha256")
                != sha256_file(solution_qc_path)
            ):
                failures.append("acceptance_evidence_solution_qc_sha256")
    elif engineering:
        parameters = solve.get("solver_parameters", {})
        if contract.get("barrier_status_code") != 2:
            failures.append("barrier_status")
        if not (
            int(parameters.get("method", -1)) == 2
            and int(parameters.get("crossover", -1)) == 0
            and int(parameters.get("solution_target", -1)) == 1
        ):
            failures.append("engineering_solver_contract")
        ordering = metadata.get("lp_ordering", {})
        for kind in ("variable", "constraint"):
            row = ordering.get(f"{kind}_order_digest", {})
            if not (
                isinstance(row, dict)
                and int(row.get("entries", -1))
                == int(
                    metadata.get("vectors", {})
                    .get("primal" if kind == "variable" else "dual", {})
                    .get("entries", -2)
                )
                and len(str(row.get("sha256", ""))) == 64
            ):
                failures.append(f"engineering_{kind}_order_digest")
    if metadata.get("schema_version") != CHECKPOINT_SCHEMA_VERSION:
        failures.append("schema_version")
    if accepted and not metadata.get("scientifically_accepted"):
        failures.append("scientifically_accepted")
    if engineering and metadata.get("scientifically_accepted"):
        failures.append("engineering_scientifically_accepted")
    if not metadata.get("deferred_crossover_eligible"):
        failures.append("deferred_crossover_eligible")

    input_manifest = source_root / "input_manifest.csv"
    input_valid, input_failures = validate_input_manifest(input_manifest)
    if not input_valid:
        failures.extend(f"input_manifest:{failure}" for failure in input_failures)
    elif metadata.get("source", {}).get("input_manifest_sha256") != sha256_file(
        input_manifest
    ):
        failures.append("input_manifest_sha256")

    source_layers = metadata.get("identity_layers", {})
    for name in (
        "baseline_contract",
        "analysis_case",
        "scientific_case",
        "implementation_bundle",
        "data_roots",
        "lp_model",
    ):
        if source_layers.get(name) != run_identity.get(name):
            failures.append(f"identity_layer:{name}")

    failures.extend(
        _checkpoint_vector_integrity_failures(checkpoint_root, metadata)
    )
    return not failures, failures


def prepare_primal_dual_crossover(
    source_output_dir: str | Path,
    target_output_dir: str | Path,
    model: Any,
    config: ModelConfig,
    *,
    optimization_hours: int,
    optimization_start_hour: int,
    result_use: str,
    allow_engineering_checkpoint: bool = False,
    allow_compatible_implementation_bundle: bool = False,
    row_scaling_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate an eligible checkpoint against the exact rebuilt target LP."""
    source_root = Path(source_output_dir).resolve()
    target_root = Path(target_output_dir).resolve()
    checkpoint_root = source_root / CHECKPOINT_DIRECTORY
    metadata = _read_json(checkpoint_root / CHECKPOINT_MANIFEST)
    source_row_scaling_registry = validate_row_scaling_registry(
        metadata.get("annual_capacity_link_row_scaling"), model=model
    )
    target_row_scaling_registry = validate_row_scaling_registry(
        row_scaling_registry
    )
    if active_row_scaling_registry(source_row_scaling_registry) != (
        active_row_scaling_registry(target_row_scaling_registry)
    ):
        raise PrimalDualCheckpointError(
            "Checkpoint source and target annual capacity-link row scaling differs"
        )
    engineering_source = (
        metadata.get("checkpoint_status") == ENGINEERING_CHECKPOINT_STATUS
    )
    if engineering_source and not allow_engineering_checkpoint:
        raise PrimalDualCheckpointError(
            "Engineering Barrier checkpoint requires explicit acknowledgement"
        )
    checkpoint_valid, failures = validate_barrier_primal_dual_checkpoint(
        source_root,
        require_result_manifest=not engineering_source,
        allow_engineering=allow_engineering_checkpoint,
    )
    if not checkpoint_valid:
        raise PrimalDualCheckpointError(
            "Checkpoint source is not eligible for deferred crossover: "
            + "; ".join(failures)
        )
    source_solve = _read_json(source_root / "solve_report.json")
    if not engineering_source:
        source_qc = _read_json(source_root / "solution_qc.json")
        if (
            source_qc.get("status") != "PASS"
            or source_solve.get("status") != "OPTIMAL"
        ):
            raise PrimalDualCheckpointError(
                "Accepted checkpoint source is not OPTIMAL + QC PASS"
            )
    if metadata.get("schema_version") != CHECKPOINT_SCHEMA_VERSION:
        raise PrimalDualCheckpointError("Unsupported Barrier checkpoint schema")
    if not metadata.get("deferred_crossover_eligible"):
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
    try:
        source_manifest_identity = input_manifest_scientific_resume_identity(
            source_input
        )
        target_manifest_identity = input_manifest_scientific_resume_identity(
            target_input
        )
    except ValueError as error:
        raise PrimalDualCheckpointError(str(error)) from error
    if (
        source_manifest_identity["sha256"]
        != target_manifest_identity["sha256"]
        or source_manifest_identity["row_count"]
        != target_manifest_identity["row_count"]
    ):
        raise PrimalDualCheckpointError(
            "Source and target scientific input manifests differ"
        )
    target_identity = _read_json(target_root / "run_identity.json")
    target_environment = _read_json(target_root / "run_environment.json")
    source_gurobi_version = source.get("gurobipy_version")
    target_gurobi_version = (
        target_environment.get("packages", {}).get("gurobipy")
    )
    if source_gurobi_version != target_gurobi_version:
        raise PrimalDualCheckpointError(
            "Checkpoint source and target Gurobi version differs: "
            f"{source_gurobi_version!r} != {target_gurobi_version!r}"
        )
    source_layers = metadata.get("identity_layers", {})
    for name in (
        "baseline_contract",
        "analysis_case",
        "scientific_case",
        "lp_model",
    ):
        if source_layers.get(name) != target_identity.get(name):
            raise PrimalDualCheckpointError(
                f"Checkpoint source and target identity layer {name} differs"
            )
    data_root_compatibility = validate_checkpoint_data_root_compatibility(
        source_layers.get("data_roots"),
        target_identity.get("data_roots"),
        source_input,
        target_input,
    )
    source_implementation = source_layers.get("implementation_bundle")
    target_implementation = target_identity.get("implementation_bundle")
    implementation_bundle_matches = (
        source_implementation == target_implementation
    )
    if (
        not implementation_bundle_matches
        and not allow_compatible_implementation_bundle
    ):
        raise PrimalDualCheckpointError(
            "Checkpoint source and target implementation bundle differs; "
            "an explicit compatibility acknowledgement is required before "
            "the exact LP Fingerprint and ordering checks may authorize reuse"
        )
    model.update()
    ordering = metadata.get("lp_ordering", {})
    try:
        target_fingerprint = int(model.Fingerprint)
    except (AttributeError, TypeError, ValueError):
        target_fingerprint = int(model.getAttr("Fingerprint"))
    source_fingerprint = ordering.get("gurobi_fingerprint")
    if source_fingerprint is None:
        # Backward-compatible path for accepted v1 checkpoints created before
        # the explicit ordering block was added. The same value was already
        # persisted in the lp_model identity layer.
        source_fingerprint = (
            source_layers.get("lp_model") or {}
        ).get("gurobi_fingerprint")
    if int(source_fingerprint if source_fingerprint is not None else -1) != (
        target_fingerprint
    ):
        raise PrimalDualCheckpointError(
            "Checkpoint source and target Gurobi Fingerprint differs"
        )
    for kind in ("variable", "constraint"):
        expected_order = ordering.get(f"{kind}_order_digest")
        if expected_order is None:
            continue
        actual_order = _ordered_name_digest(model, kind=kind)
        if (
            int(expected_order.get("entries", -1))
            != int(actual_order["entries"])
            or str(expected_order.get("sha256")) != actual_order["sha256"]
        ):
            raise PrimalDualCheckpointError(
                f"Checkpoint source and target {kind} order differs"
            )
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
        if not _array_is_finite(array):
            raise PrimalDualCheckpointError(
                f"Checkpoint {role} vector contains nonfinite values"
            )
        del array
        paths[role] = str(path)
    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "source_output_dir": str(source_root),
        "source_checkpoint_status": metadata.get("checkpoint_status"),
        "source_scientifically_accepted": bool(
            metadata.get("scientifically_accepted")
        ),
        "engineering_checkpoint_explicitly_allowed": bool(
            engineering_source and allow_engineering_checkpoint
        ),
        "compatible_implementation_bundle_explicitly_allowed": bool(
            not implementation_bundle_matches
            and allow_compatible_implementation_bundle
        ),
        "implementation_bundle_matches": implementation_bundle_matches,
        "source_implementation_bundle": source_implementation,
        "target_implementation_bundle": target_implementation,
        "source_gurobi_version": source_gurobi_version,
        "target_gurobi_version": target_gurobi_version,
        "data_root_compatibility": data_root_compatibility,
        "scientific_input_manifest_identity": {
            "schema_version": source_manifest_identity["schema_version"],
            "sha256": source_manifest_identity["sha256"],
            "row_count": source_manifest_identity["row_count"],
            "excluded_runtime_kinds": source_manifest_identity[
                "excluded_runtime_kinds"
            ],
            "source_solver_configuration": source_manifest_identity[
                "solver_configuration"
            ],
            "target_solver_configuration": target_manifest_identity[
                "solver_configuration"
            ],
            "source_full_manifest_sha256": source_manifest_identity[
                "full_manifest_sha256"
            ],
            "target_full_manifest_sha256": target_manifest_identity[
                "full_manifest_sha256"
            ],
        },
        "source_result_manifest_sha256": (
            sha256_file(source_root / "result_manifest.json")
            if (source_root / "result_manifest.json").is_file()
            else None
        ),
        "source_checkpoint_manifest_sha256": sha256_file(
            checkpoint_root / CHECKPOINT_MANIFEST
        ),
        "primal_path": paths["primal"],
        "dual_path": paths["dual"],
        "variables": expected_counts["primal"],
        "constraints": expected_counts["dual"],
        "gurobi_fingerprint": target_fingerprint,
        "annual_capacity_link_row_scaling": row_scaling_registry,
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
