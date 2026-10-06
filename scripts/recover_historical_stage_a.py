"""Recover a checksummed historical Stage A using its isolated source release.

Run inside the historical release plus audited preservation-only overlay.
Requires an explicit prefix path map, source backup, and new output directory.
Never optimizes/presolves. --preflight-only validates without building any LP.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import shutil
import sys
import tarfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def mapped(value, mapping):
    if isinstance(value, dict):
        return {k: mapped(v, mapping) for k, v in value.items()}
    if isinstance(value, list):
        return [mapped(v, mapping) for v in value]
    if isinstance(value, str):
        for old, new in sorted(mapping.items(), key=lambda x: -len(x[0])):
            if value == old or value.startswith(old + "/"):
                return new + value[len(old):]
    return value


def verify_release(backup):
    """Validate all original bytes and forbid changes outside the export overlay."""
    from cispo_model.planning_state import sha256_file
    original = []
    with (backup / "downloaded_files_sha256.csv").open(encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            path = (backup / row["path"]).resolve()
            path.relative_to(backup)
            if path.stat().st_size != int(row["bytes"]) or sha256_file(path) != row["sha256"]:
                raise ValueError(f"Original backup checksum mismatch: {row['path']}")
            original.append(row)
    allowed = {"cispo_model/master.py", "cispo_model/solution_export.py",
               "cispo_model/planning_state.py", "cispo_model/result_summary.py"}
    changes = []
    source_rows = []
    archive = backup / "source_bundle/code_3f739fd_linux.tar"
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            name = member.name.removeprefix("./")
            if not member.isfile() or not (name.startswith("cispo_model/") and name.endswith(".py")
                    or name in {"scripts/run_cispo_2030_full_year.py", "scripts/run_cispo_planning_sequence.py"}
                    or name.startswith("config/")):
                continue
            content = tar.extractfile(member).read()
            path = (ROOT / name).resolve()
            path.relative_to(ROOT)
            current = path.read_bytes()
            old_hash = hashlib.sha256(content).hexdigest()
            if name.endswith(".py"):
                source_rows.append({"path": name, "sha256": old_hash})
            if current != content:
                if name not in allowed:
                    raise ValueError(f"Unaudited historical source change: {name}")
                if name == "cispo_model/master.py":
                    def builder_ast(payload):
                        tree = ast.parse(payload)
                        tree.body = [node for node in tree.body if not (
                            isinstance(node, ast.FunctionDef) and node.name == "export_master_solution")]
                        return ast.dump(tree, include_attributes=False)
                    if builder_ast(content) != builder_ast(current):
                        raise ValueError("Historical master builder AST changed")
                changes.append({"path": name, "original_sha256": old_hash,
                                "recovery_sha256": hashlib.sha256(current).hexdigest()})
    canonical = json.dumps(sorted(source_rows, key=lambda r: r["path"]), ensure_ascii=False,
                           sort_keys=True, separators=(",", ":")).encode()
    expected = read_json(backup / "output/run_identity.json")["implementation_bundle"]
    if len(source_rows) != expected["source_file_count"] or hashlib.sha256(canonical).hexdigest() != expected["source_bundle_sha256"]:
        raise ValueError("Archived implementation differs from original run identity")
    return {"original_backup_files_verified": len(original), "original_source_identity": expected,
            "preservation_only_changes": changes,
            "driver_sha256": sha256_file(Path(__file__)),
            "added_modules": {name: sha256_file(ROOT / "cispo_model" / name)
                              for name in ("offline_solution.py", "solution_preservation.py")}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-backup", required=True)
    parser.add_argument("--path-map", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--allow-fingerprint-mismatch", action="store_true",
                        help="Author-authorized recovery: record differing fingerprint, retain exact dimensions/order/hash checks")
    args = parser.parse_args()
    import gurobipy as gp
    import pandas as pd
    import psutil
    from cispo_model.config import load_model_config
    from cispo_model.data import DATA_ROOT, load_model_data
    from cispo_model.planning_state import PlanningState, sha256_file
    from cispo_model.io_contract import write_run_provenance, validate_input_manifest, validate_result_manifest
    from cispo_model.run_contract import configuration_identity
    from cispo_model.solution_preservation import write_json, archive_model, preserve_stage_a
    from cispo_model.offline_solution import read_legacy_checkpoint, offline_artifacts, audit_saved_primal
    from cispo_model.basis_reuse import lightweight_lp_identity
    from cispo_model.runtime_monitor import PeakMemoryMonitor
    from cispo_model.result_summary import finalize_result_manifest

    backup, output = Path(args.source_backup).resolve(), Path(args.output_dir).resolve()
    if output.is_relative_to(backup) or backup.is_relative_to(output):
        raise ValueError("Recovery output must be disjoint from original backup")
    output.mkdir(parents=True, exist_ok=False)
    source = backup / "output"
    mapping = read_json(args.path_map)
    monitor = PeakMemoryMonitor().start()
    progress = {"started_at": datetime.now().astimezone().isoformat(), "status": "VALIDATING",
                "optimize_calls": 0, "presolve_calls": 0, "scientifically_accepted": False}

    def event(status, **extra):
        progress.update(status=status, updated_at=datetime.now().astimezone().isoformat(), **extra)
        write_json(output / "recovery_progress.json", progress)
        print(json.dumps(progress, ensure_ascii=False), flush=True)

    def forbidden(*unused_args, **unused_kwargs):
        raise RuntimeError("Optimization/presolve is forbidden in historical offline recovery")

    try:
        with patch.object(gp.Model, "optimize", forbidden), patch.object(gp.Model, "presolve", forbidden):
            evidence = verify_release(backup)
            write_json(output / "recovery_release_audit.json", evidence)
            write_json(output / "path_mapping.json", mapping)
            scope = read_json(source / "run_scope.json")
            if scope["planning_year"] != 2030 or scope.get("state_in"):
                raise ValueError("This entry currently supports boundary-year Stage A without predecessor state")
            original_identity = read_json(source / "run_identity.json")
            target_expected = mapped(original_identity, mapping)
            config = load_model_config(path=Path(target_expected["analysis_case"]["configuration_path"]),
                                       solver_path=Path(target_expected["solver_runtime"]["solver_configuration"]["path"]))
            write_run_provenance(output, config, data_root=DATA_ROOT, planning_state=PlanningState.empty(config.boundary_year))
            current_identity = configuration_identity(config, data_root=DATA_ROOT)
            for key in ("baseline_contract", "analysis_case", "scientific_case", "data_roots", "solver_runtime"):
                if current_identity[key] != target_expected[key]:
                    raise ValueError(f"Mapped historical identity differs: {key}")
            original_manifest = pd.read_csv(source / "input_manifest.csv")
            migrated = original_manifest.copy()
            for field in ("logical_path", "resolved_path"):
                migrated[field] = migrated[field].map(lambda v: mapped(v, mapping))
            migrated_path = output / "source_input_manifest_mapped.csv"
            migrated.to_csv(migrated_path, index=False, lineterminator="\n")
            for path in (migrated_path, output / "input_manifest.csv"):
                ok, failures = validate_input_manifest(path)
                if not ok:
                    raise ValueError(f"Historical inputs invalid: {failures}")
            fresh = pd.read_csv(output / "input_manifest.csv")
            fields = list(original_manifest.columns)
            pd.testing.assert_frame_equal(migrated[fields].reset_index(drop=True), fresh[fields].reset_index(drop=True),
                                          check_dtype=False, check_exact=True)
            source_env = read_json(source / "run_environment.json")
            target_env = read_json(output / "run_environment.json")
            write_json(output / "recovery_environment_comparison.json", {
                "source_python": source_env["python"], "target_python": target_env["python"],
                "source_packages": source_env["packages"], "target_packages": target_env["packages"],
                "all_recorded_packages_match": source_env["packages"] == target_env["packages"]})
            if source_env["packages"]["gurobipy"] != target_env["packages"]["gurobipy"]:
                raise ValueError("Gurobi version mismatch")
            source_config = read_json(source / "model_config_snapshot.json")["resolved_configuration"]
            if mapped(source_config, mapping) != config.raw:
                raise ValueError("Historical resolved configuration mismatch")
            shutil.copytree(source / "barrier_checkpoint", output / "source_checkpoint")
            shutil.copy2(source / "solve_report.json", output / "source_solve_report.json")
            shutil.copy2(source / "run_identity.json", output / "source_run_identity.json")
            write_json(output / "run_scope.json", dict(scope, recovery_only=True, source_output=str(source)))
            write_json(output / "run_identity.json", current_identity)
            event("PREFLIGHT_PASS", input_rows_verified=len(fresh),
                  memory_available_gib=psutil.virtual_memory().available / 1024**3)
            if args.preflight_only:
                return
            if psutil.virtual_memory().available < 90 * 1024**3:
                raise RuntimeError("Recovery requires at least 90 GiB available RAM")
            from cispo_model.monolithic import build_full_year_monolithic
            event("LOADING_MODEL_DATA")
            data = load_model_data(config)
            event("BUILDING_ORIGINAL_LP")
            started = time.monotonic()
            artifacts = build_full_year_monolithic(config, data, compute_max_cf=True,
                optimization_hours=int(scope["optimization_hours"]),
                optimization_start_hour=int(scope["optimization_start_hour"]))
            lp = lightweight_lp_identity(artifacts.model)
            write_json(output / "build_report.json", {"lp_model": lp, "build_seconds": time.monotonic() - started,
                                                       "memory_after_build": monitor.snapshot()})
            differences = {key: {"source": value, "rebuilt": lp.get(key)}
                           for key, value in original_identity["lp_model"].items() if lp.get(key) != value}
            write_json(output / "recovery_model_identity.json", {
                "source_lp": original_identity["lp_model"], "rebuilt_lp": lp,
                "differences": differences,
                "fingerprint_mismatch_authorized": args.allow_fingerprint_mismatch,
                "scientifically_accepted": False})
            current_identity["lp_model"] = lp
            write_json(output / "run_identity.json", current_identity)
            # Always preserve the built algebra before a mismatch can exit.
            event("ARCHIVING_REBUILT_LP", lp_model=lp, identity_differences=differences)
            archive = archive_model(artifacts.model, output)
            blocking = set(differences) - ({"gurobi_fingerprint"} if args.allow_fingerprint_mismatch else set())
            if blocking:
                raise ValueError(f"Original LP identity mismatch (model archived): {differences}")
            event("VERIFYING_FULL_ORDER_AND_VECTORS", lp_model=lp)
            row_scaling_registry = artifacts.index.get(
                "annual_capacity_link_row_scaling"
            )
            primal, dual = read_legacy_checkpoint(
                artifacts.model,
                source,
                allow_fingerprint_mismatch=args.allow_fingerprint_mismatch,
                order_digests=archive,
                expected_row_scaling_registry=row_scaling_registry,
            )
            event("AUDITING_RAW_LP")
            report = read_json(source / "solve_report.json")
            tolerance = float(report["solution_contract"]["maximum_primal_quality_limit"])
            audit_error = None
            try:
                raw_qc = audit_saved_primal(artifacts.model, primal, tolerance=tolerance,
                                           violations_path=output / "raw_lp_violations.csv.gz",
                                           row_scaling_registry=row_scaling_registry)
            except Exception as error:
                audit_error = repr(error)
                raw_qc = {"status": "NOT_EVALUATED", "error": audit_error,
                          "optimize_called": False, "presolve_called": False}
            write_json(output / "raw_lp_qc.json", raw_qc)
            event("EXPORTING_RESULTS", raw_lp_qc_status=raw_qc["status"])
            view = offline_artifacts(artifacts, primal, dual)
            write_json(output / "offline_recovery.json", {
                "source_output": str(source), "source_solve_report_sha256": sha256_file(source / "solve_report.json"),
                "exact_lp_identity_and_full_order_verified": not bool(differences),
                "exact_variable_constraint_order_verified": True,
                "model_identity_differences": differences,
                "fingerprint_mismatch_authorized": args.allow_fingerprint_mismatch,
                "interpretation": "ORDER_MATCHED_SAVED_VALUES_REBUILT_MODEL_AUDIT_NOT_SCIENTIFIC_ACCEPTANCE",
                "path_mapping": mapping,
                "recomputed_objective": float(view.model.ObjVal),
                "source_objective": report.get("objective_value_million_cny"),
                "optimize_called": False, "presolve_called": False,
                "target_sol_count": int(artifacts.model.SolCount), "scientifically_accepted": False})
            result = preserve_stage_a(view, data, config, output, dict(report, recovery="offline_recovery.json"), snapshot=False)
            if audit_error is not None:
                result["status"] = "PARTIAL"
                result["stages"]["raw_lp_qc"] = "ERROR"
                result["errors"].append({"stage": "raw_lp_qc", "error": audit_error})
                write_json(output / "preservation_report.json", result)
            event(result["status"], qc_status=result["qc_status"])
            write_json(output / "preservation_runtime_memory.json", monitor.stop())
            finalize_result_manifest(output, config)
            ok, failures = validate_result_manifest(output)
            if not ok:
                raise ValueError(f"Recovered result manifest invalid: {failures}")
            PlanningState.load(output / "planning_state_candidate", expected_boundary_year=config.planning_year,
                               allow_test_only=scope["result_use"] == "TEST_ONLY_TRUNCATED_HORIZON",
                               allow_unaccepted_candidate=True)
            if result["status"] != "COMPLETE":
                raise RuntimeError("Recovery exports PARTIAL; inspect preservation_report.json")
    except BaseException as error:
        event("FAILED", error=repr(error))
        raise
    finally:
        if not (output / "preservation_runtime_memory.json").is_file():
            write_json(
                output / "preservation_runtime_memory.json", monitor.stop()
            )


if __name__ == "__main__":
    main()
