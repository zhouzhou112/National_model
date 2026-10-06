"""Small CISPO Barrier -> unsolved rebuild -> offline export equivalence test.

This is a diagnostic, not an annual solve or acceptance of the recovered data.
The source solve is capped at 120 s; recovery forbids optimize and presolve.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import gurobipy as gp
import numpy as np
import pandas as pd

from cispo_model.config import load_model_config
from cispo_model.data import load_model_data
from cispo_model.diagnostics import solve_and_report, configure_gurobi
from cispo_model.monolithic import build_full_year_monolithic
from cispo_model.offline_solution import offline_artifacts, read_snapshot, audit_saved_primal
from cispo_model.solution_preservation import archive_model, preserve_stage_a, write_json
from cispo_model.io_contract import validate_result_manifest
from cispo_model.planning_state import PlanningState
from cispo_model.result_summary import finalize_result_manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--hours", type=int, choices=(1, 2, 24), default=1)
    args = parser.parse_args()
    root = Path(args.output_dir).resolve()
    root.mkdir(parents=True, exist_ok=False)
    source_root, recovered_root = root / "source", root / "recovered"
    source_root.mkdir()
    recovered_root.mkdir()
    config = load_model_config()
    config.raw["numerics"].update(method=2, crossover=0, solution_target=1,
                                  threads=2, time_limit_seconds=120)
    write_json(root / "diagnostic_config.json", config.raw)
    data = load_model_data(config)
    source = build_full_year_monolithic(config, data, optimization_hours=args.hours)
    source.model.update()
    configure_gurobi(source.model, config, source_root / "gurobi.log")
    archive_model(source.model, source_root, presolved=True)
    report = solve_and_report(source.model, config, source_root, compute_iis=False)
    report.update(planning_year=config.planning_year, boundary_year=config.boundary_year,
                  optimization_hours=args.hours, optimization_start_hour=0,
                  result_use="TEST_ONLY_TRUNCATED_HORIZON")
    source_preserved = preserve_stage_a(source, data, config, source_root, report)
    finalize_result_manifest(source_root, config)
    online_root = root / "online_reference"
    online_root.mkdir()
    online = preserve_stage_a(source, data, config, online_root, report, snapshot=False)
    finalize_result_manifest(online_root, config)
    checks = {"source_export_complete": source_preserved["status"] == "COMPLETE"}
    checks["online_reference_complete"] = online["status"] == "COMPLETE"
    with patch.object(gp.Model, "optimize", side_effect=AssertionError("recovery optimize forbidden")), \
         patch.object(gp.Model, "presolve", side_effect=AssertionError("recovery presolve forbidden")):
        target = build_full_year_monolithic(config, data, optimization_hours=args.hours)
        target.model.update()
        archive_model(target.model, recovered_root)
        registry = target.index.get("annual_capacity_link_row_scaling")
        primal, dual = read_snapshot(
            target.model,
            source_root / "solution_snapshot",
            expected_row_scaling_registry=registry,
        )
        view = offline_artifacts(target, primal, dual)
        write_json(recovered_root / "raw_lp_qc.json", audit_saved_primal(
            target.model, primal, tolerance=report["solution_contract"]["maximum_primal_quality_limit"],
            violations_path=recovered_root / "raw_lp_violations.csv.gz",
            row_scaling_registry=registry))
        shutil.copytree(source_root / "solution_snapshot", recovered_root / "source_checkpoint")
        recovered = preserve_stage_a(view, data, config, recovered_root, report, snapshot=False)
        finalize_result_manifest(recovered_root, config)
        checks["recovered_export_complete"] = recovered["status"] == "COMPLETE"
        checks["target_remains_unsolved"] = target.model.SolCount == 0
    comparisons, failures = [], []
    for path in sorted(online_root.rglob("*")):
        if path.name in {"output_catalog.csv", "output_data_dictionary.csv"}:
            continue  # File inventories intentionally differ between raw/online/recovered roots.
        if not path.name.endswith((".csv", ".csv.gz", ".npz")):
            continue
        relative = path.relative_to(online_root)
        other = recovered_root / relative
        try:
            if path.suffix == ".npz":
                with np.load(path, allow_pickle=False) as left, np.load(other, allow_pickle=False) as right:
                    if set(left.files) != set(right.files):
                        raise AssertionError("array keys differ")
                    for key in left.files:
                        if np.issubdtype(left[key].dtype, np.number):
                            np.testing.assert_allclose(left[key], right[key], rtol=1e-10, atol=1e-10)
                        else:
                            np.testing.assert_array_equal(left[key], right[key])
            else:
                pd.testing.assert_frame_equal(pd.read_csv(path), pd.read_csv(other), check_exact=False,
                                               rtol=1e-10, atol=1e-10)
            comparisons.append(str(relative))
        except Exception as error:
            failures.append({"file": str(relative), "error": repr(error)})
    for name in ("annual_carbon_ccs.json",):
        checks[name] = json.loads((online_root / name).read_text()) == json.loads((recovered_root / name).read_text())
    checks["raw_lp_qc_matches"] = json.loads((source_root / "raw_lp_qc.json").read_text()) == json.loads((recovered_root / "raw_lp_qc.json").read_text())
    for location in (source_root, recovered_root):
        checks[f"{location.name}_manifest"] = validate_result_manifest(location)[0]
        state = PlanningState.load(location / "planning_state_candidate", expected_boundary_year=2030,
                                   allow_test_only=True, allow_unaccepted_candidate=True)
        checks[f"{location.name}_candidate_load"] = state.metadata["scientifically_accepted"] is False
    result = {"status": "PASS" if all(checks.values()) and not failures and comparisons else "FAIL",
              "checks": checks, "compared_files": comparisons, "failures": failures,
              "hours": args.hours, "gurobi_version": list(gp.gurobi.version()),
              "source_solver_status": report.get("status"),
              "source_solver_contract": report.get("solution_contract"),
              "source_physical_qc": source_preserved.get("qc_status"),
              "recovery_optimize_calls": 0, "recovery_presolve_calls": 0,
              "target_fingerprint": int(target.model.Fingerprint),
              "source_fingerprint": int(source.model.Fingerprint)}
    write_json(root / "validation_report.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    primal._mmap.close()
    if dual is not None:
        dual._mmap.close()
    source.model.dispose()
    target.model.dispose()
    if result["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
