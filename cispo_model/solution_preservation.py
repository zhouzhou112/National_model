"""Quality-independent, checksummed preservation; never an acceptance gate.

The raw snapshot is written first. Semantic export and candidate state are
independent stages; a QC FAIL is data, not an exception or a file filter.
"""
from __future__ import annotations

import gzip
import json
import os
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import gurobipy as gp

from .planning_state import sha256_file

CHUNK_SIZE = 50_000


def replace_file(temporary, target):
    """Keep atomic writes despite short-lived Windows scanner/indexer locks."""
    for attempt in range(6):
        try:
            Path(temporary).replace(target)
            return
        except PermissionError:
            if os.name != "nt" or attempt == 5:
                raise
            time.sleep(0.05 * (2 ** attempt))


def write_json(path, payload):
    path = Path(path)
    temporary = path.with_name(path.name + ".part")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    replace_file(temporary, path)


def file_record(path, root):
    return {"path": Path(path).relative_to(root).as_posix(),
            "bytes": Path(path).stat().st_size, "sha256": sha256_file(Path(path))}


def model_order(model, kind, catalog=None):
    """Legacy-compatible order digest, optionally with a streamed name catalog."""
    import hashlib
    objects = model.getVars() if kind == "variable" else model.getConstrs()
    expected = int(model.NumVars if kind == "variable" else model.NumConstrs)
    if len(objects) != expected:
        raise ValueError("Model object count changed during preservation")
    digest = hashlib.sha256()
    digest.update(f"cispo_raw_lp_{kind}_order_v1\0".encode("ascii"))
    digest.update(expected.to_bytes(8, "big"))
    stream = gzip.open(catalog, "wt", encoding="utf-8") if catalog else None
    try:
        for start in range(0, expected, CHUNK_SIZE):
            chunk = objects[start:start + CHUNK_SIZE]
            names = model.getAttr("VarName" if kind == "variable" else "ConstrName", chunk)
            senses = [""] * len(chunk) if kind == "variable" else model.getAttr("Sense", chunk)
            for offset, (name, sense) in enumerate(zip(names, senses)):
                index = start + offset
                encoded = name.encode("utf-8")
                digest.update(index.to_bytes(8, "big"))
                digest.update(len(encoded).to_bytes(8, "big"))
                digest.update(encoded)
                digest.update(sense.encode("ascii") + b"\0")
                if stream:
                    stream.write(json.dumps([index, name, sense], ensure_ascii=False) + "\n")
    finally:
        if stream:
            stream.close()
    return {"entries": expected, "sha256": digest.hexdigest()}


def archive_model(
    model,
    output_dir,
    *,
    presolved=False,
    include_name_catalog=False,
):
    """Save original algebra before optimization; presolve is explicit and optional."""
    root = Path(output_dir) / "model_archive"
    root.mkdir(exist_ok=False)
    model.update()
    report = {"schema_version": "cispo_model_archive_v1", "files": [], "errors": [], "warnings": [],
              "presolved_status": "NOT_REQUESTED", "uncrush_mapping_saved": False,
              "factorization_saved": False, "gurobi_fingerprint": int(model.Fingerprint)}
    def write_model(target, name):
        path = root / name
        try:
            target.write(str(path))
        except (gp.GurobiError, OSError) as error:
            if not name.endswith(".gz"):
                raise
            # Some Windows installations cannot spawn gzip. Retain a complete
            # uncompressed model rather than silently losing the archive.
            path = root / name.removesuffix(".gz")
            target.write(str(path))
            report["warnings"].append({"file": name, "fallback": path.name, "reason": repr(error)})
        report["files"].append(file_record(path, root))

    for name in ("original.mps.gz", "parameters.prm"):
        try:
            write_model(model, name)
        except Exception as error:
            report["errors"].append({"file": name, "error": repr(error)})
    report["full_name_catalog_requested"] = bool(include_name_catalog)
    if include_name_catalog:
        for kind in ("variable", "constraint"):
            name = f"{kind}_names.jsonl.gz"
            try:
                report[f"{kind}_order_digest"] = model_order(
                    model, kind, root / name
                )
                report["files"].append(file_record(root / name, root))
            except Exception as error:
                report["errors"].append({"file": name, "error": repr(error)})
    if presolved:
        reduced = None
        try:
            reduced = model.presolve()
            write_model(reduced, "presolved_diagnostic.mps.gz")
            report["presolved_status"] = "DIAGNOSTIC_COPY_NOT_INTERNAL_OPTIMIZE_STATE"
        except Exception as error:
            report["presolved_status"] = "ERROR"
            report["errors"].append({"stage": "presolve", "error": repr(error)})
        finally:
            if reduced is not None:
                reduced.dispose()
    report["status"] = "PARTIAL" if report["errors"] else "COMPLETE"
    write_json(root / "archive_manifest.json", report)
    return report


def save_numeric_snapshot(model, output_dir, *, row_scaling_registry=None):
    """Persist available raw solution attributes, including nonfinite evidence."""
    from .annual_capacity_link_scaling import validate_row_scaling_registry

    row_scaling_registry = validate_row_scaling_registry(
        row_scaling_registry, model=model
    )
    root = Path(output_dir) / "solution_snapshot"
    root.mkdir(exist_ok=False)
    model.update()
    payload = {"schema_version": "cispo_solution_snapshot_v1", "scientifically_accepted": False,
               "gurobi_fingerprint": int(model.Fingerprint), "variables": int(model.NumVars),
               "constraints": int(model.NumConstrs), "nonzeros": int(model.NumNZs),
               "attributes": {}, "unavailable": {}}
    payload["annual_capacity_link_row_scaling"] = row_scaling_registry
    for kind, names in (("variable", ("BarX", "X", "RC", "VBasis")),
                        ("constraint", ("BarPi", "Pi", "Slack", "CBasis"))):
        objects = model.getVars() if kind == "variable" else model.getConstrs()
        for name in names:
            path = root / f"{name}.npy"
            temporary = root / f"{name}.npy.part"
            values = None
            try:
                # Query before creating a possibly misleading empty file.
                first = model.getAttr(name, objects[:CHUNK_SIZE])
                values = np.lib.format.open_memmap(temporary, mode="w+", dtype="<f8", shape=(len(objects),))
                finite = True
                for start in range(0, len(objects), CHUNK_SIZE):
                    block = first if start == 0 else model.getAttr(name, objects[start:start + CHUNK_SIZE])
                    array = np.asarray(block, dtype=float)
                    finite = finite and bool(np.isfinite(array).all())
                    values[start:start + len(array)] = array
                values.flush()
                del values
                values = None
                replace_file(temporary, path)
                payload["attributes"][name] = dict(file_record(path, root), entries=len(objects), finite=finite)
            except Exception as error:
                if values is not None:
                    values.flush()
                    del values
                payload["unavailable"][name] = repr(error)
        del objects
        payload[f"{kind}_order_digest"] = model_order(model, kind)
    payload["primal_attribute"] = next((n for n in ("BarX", "X") if n in payload["attributes"]), None)
    payload["dual_attribute"] = next((n for n in ("BarPi", "Pi") if n in payload["attributes"]), None)
    payload["status"] = "COMPLETE" if all(
        payload.get(k) and payload["attributes"][payload[k]]["finite"]
        for k in ("primal_attribute", "dual_attribute")
    ) else "PARTIAL"
    write_json(root / "snapshot_manifest.json", payload)
    return payload


def preserve_stage_a(artifacts, data, config, output_dir, report, *, snapshot=True):
    """Complete all independent exports and finalize a non-acceptance manifest."""
    from .master import export_master_solution
    from .solution_export import export_operational_solution
    from .result_summary import export_result_summary
    from .planning_state import export_solution_planning_state
    from .io_contract import write_output_catalog

    root = Path(output_dir)
    started = time.perf_counter()
    result = {"schema_version": "cispo_preservation_v1", "scientifically_accepted": False,
              "generated_at": datetime.now().astimezone().isoformat(),
              "author_decision": "PENDING", "stages": {}, "errors": [],
              "solver_contract": report.get("solution_contract"),
              "solver_quality": report.get("solution_quality"),
              "qc_status": "NOT_EVALUATED", "status": "IN_PROGRESS"}

    def stage(name, operation):
        try:
            value = operation()
            result["stages"][name] = "COMPLETE"
            return value
        except Exception as error:
            result["stages"][name] = "ERROR"
            result["errors"].append({"stage": name, "error": repr(error)})
            return None
        finally:
            write_json(root / "preservation_report.json", result)

    if snapshot:
        row_scaling_registry = artifacts.index.get(
            "annual_capacity_link_row_scaling"
        )
        raw = stage(
            "raw_snapshot",
            lambda: save_numeric_snapshot(
                artifacts.model,
                root,
                row_scaling_registry=row_scaling_registry,
            ),
        )
        if raw is not None and raw["status"] != "COMPLETE":
            result["stages"]["raw_snapshot"] = "PARTIAL"
        if raw is not None and raw.get("primal_attribute"):
            from .offline_solution import offline_artifacts, read_snapshot, audit_saved_primal
            values = stage(
                "snapshot_integrity",
                lambda: read_snapshot(
                    artifacts.model,
                    root / "solution_snapshot",
                    expected_row_scaling_registry=row_scaling_registry,
                ),
            )
            if values is not None and np.isfinite(values[0]).all():
                raw_qc = stage("raw_lp_qc", lambda: audit_saved_primal(
                    artifacts.model, values[0],
                    tolerance=float((report.get("solution_contract") or {}).get("maximum_primal_quality_limit") or 1e-5),
                    violations_path=root / "raw_lp_violations.csv.gz",
                    row_scaling_registry=row_scaling_registry))
                if raw_qc is not None:
                    write_json(root / "raw_lp_qc.json", raw_qc)
            view = (
                stage(
                    "saved_value_mapping",
                    lambda: offline_artifacts(artifacts, *values),
                )
                if values is not None
                else None
            )
            if view is not None:
                artifacts = view
                result["semantic_primal_attribute"] = raw["primal_attribute"]
            else:
                result["semantic_primal_attribute"] = "SOLVER_X_FALLBACK_AFTER_MAPPING_ERROR"
    elif (root / "barrier_checkpoint" / "barrier_checkpoint_manifest.json").is_file():
        from .primal_dual_checkpoint import validate_checkpoint_vector_integrity

        checkpoint_valid, checkpoint_failures = (
            validate_checkpoint_vector_integrity(root)
        )
        if checkpoint_valid:
            result["stages"]["raw_checkpoint"] = "COMPLETE"
            result["raw_checkpoint_source"] = "REUSED_EXISTING_CHECKPOINT"
            result["semantic_primal_attribute"] = "PERSISTED_BARRIER_VECTOR"
        else:
            result["stages"]["raw_checkpoint"] = "ERROR"
            result["raw_checkpoint_source"] = (
                "REJECTED_INVALID_EXISTING_CHECKPOINT"
            )
            result["errors"].append(
                {
                    "stage": "raw_checkpoint",
                    "error": "Checkpoint vector integrity failed: "
                    + ", ".join(checkpoint_failures),
                }
            )
        write_json(root / "preservation_report.json", result)
    stage("capacity_and_cost", lambda: export_master_solution(artifacts, data, root, enforce_qc=False))
    qc = stage("operation_carbon_dual_qc", lambda: export_operational_solution(
        artifacts, data, config, root, enforce_qc=False))
    if qc is None:
        path = root / "solution_qc.json"
        qc = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"status": "NOT_EVALUATED"}
        qc["export_incomplete"] = True
    qc["scientifically_accepted"] = False
    qc["solver_contract"] = report.get("solution_contract")
    qc["solver_quality"] = report.get("solution_quality")
    raw_qc_path = root / "raw_lp_qc.json"
    if raw_qc_path.is_file():
        qc["raw_lp_qc"] = json.loads(raw_qc_path.read_text(encoding="utf-8"))
        if qc["raw_lp_qc"]["status"] != "PASS":
            qc["status"] = "FAIL"
    write_json(root / "solution_qc.json", qc)
    result["qc_status"] = qc.get("status")
    stage("summary", lambda: export_result_summary(artifacts, data, config, root))
    dual_path = root / "dual_export_status.json"
    if dual_path.is_file():
        dual = json.loads(dual_path.read_text(encoding="utf-8"))
        dual.update(scientifically_accepted=False, interpretation="RAW_DUAL_PENDING_AUTHOR_REVIEW")
        write_json(dual_path, dual)
        if not dual.get("available"):
            result["stages"]["semantic_duals"] = "PARTIAL"
    # Freeze the source report before candidate state hashes it. Never mutate
    # it afterwards; final stage completeness belongs to preservation_report.
    report = dict(report, scientifically_accepted=False, author_decision="PENDING",
                  preservation_report="preservation_report.json", solution_qc_status=qc.get("status"))
    write_json(root / "solve_report.json", report)
    stage("candidate_state", lambda: export_solution_planning_state(
        artifacts, data, config, root, state_use=report["result_use"], candidate=True))
    stage("output_catalog", lambda: write_output_catalog(root))
    result["status"] = "COMPLETE" if all(s == "COMPLETE" for s in result["stages"].values()) else "PARTIAL"
    archive = root / "model_archive" / "archive_manifest.json"
    if archive.is_file() and json.loads(archive.read_text(encoding="utf-8")).get("status") != "COMPLETE":
        result["status"] = "PARTIAL"
    write_json(root / "preservation_report.json", result)
    result["elapsed_seconds_before_manifest"] = time.perf_counter() - started
    write_json(root / "preservation_report.json", result)
    return result
