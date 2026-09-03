from __future__ import annotations

import json
import tempfile
import shutil
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import gurobipy as gp
import numpy as np
import pandas as pd

from cispo_model.config import load_model_config
from cispo_model.offline_solution import offline_artifacts, read_snapshot, read_legacy_checkpoint, audit_saved_primal
from cispo_model.planning_state import PlanningState, STATE_COLUMNS, write_planning_state
from cispo_model.result_summary import finalize_result_manifest
from cispo_model.io_contract import sha256_file, validate_result_manifest
from cispo_model.solution_preservation import archive_model, preserve_stage_a, save_numeric_snapshot, write_json


def tiny_model():
    model = gp.Model("offline_test")
    model.Params.OutputFlag = 0
    model.Params.Method = 2
    model.Params.Crossover = 0
    model.Params.Presolve = 0  # The test must actually run Barrier, not vanish in presolve.
    x = model.addMVar(2, ub=10, name="capacity")
    balance = model.addConstr(x.sum() == 3, name="balance")
    model.addConstr(x[0] - x[1] <= 2, name="limit")
    cost = np.array([1., 3.]) @ x + 7
    model.setObjective(cost)
    model.update()
    return SimpleNamespace(model=model, variables={"x": x, "expr": 2 * x + 1},
                           cost_components={"cost": cost}, index={"balance": balance})


class PreservationTests(unittest.TestCase):
    def test_authorized_fingerprint_difference_still_checks_order_and_vectors(self):
        from cispo_model.solution_preservation import model_order
        source, target = tiny_model(), tiny_model()
        try:
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source.model.optimize()
                snapshot = save_numeric_snapshot(source.model, root)
                legacy = root / "barrier_checkpoint"
                legacy.mkdir()
                vectors = {}
                for role, attr in (("primal", "BarX"), ("dual", "BarPi")):
                    row = snapshot["attributes"][attr]
                    shutil.copy2(root / "solution_snapshot" / row["path"], legacy / row["path"])
                    vectors[role] = row
                ordering = {key: snapshot[key] for key in ("variables", "constraints", "nonzeros",
                           "gurobi_fingerprint", "variable_order_digest", "constraint_order_digest")}
                write_json(legacy / "barrier_checkpoint_manifest.json", {"lp_ordering": ordering, "vectors": vectors})
                target.model.getVarByName("capacity[0]").UB = 11
                target.model.update()
                self.assertNotEqual(target.model.Fingerprint, source.model.Fingerprint)
                with self.assertRaisesRegex(ValueError, "gurobi_fingerprint"):
                    read_legacy_checkpoint(target.model, root)
                cached = {f"{kind}_order_digest": model_order(target.model, kind)
                          for kind in ("variable", "constraint")}
                with patch("cispo_model.offline_solution.model_order", side_effect=AssertionError("redundant traversal")):
                    arrays = read_legacy_checkpoint(target.model, root, allow_fingerprint_mismatch=True,
                                                    order_digests=cached)
                for array in arrays:
                    array._mmap.close()
                target.model.getVarByName("capacity[0]").VarName = "wrong_meaning"
                target.model.update()
                with self.assertRaisesRegex(ValueError, "order mismatch"):
                    read_legacy_checkpoint(target.model, root, allow_fingerprint_mismatch=True)
                # Hash validation is still enforced when names match.
                target.model.getVarByName("wrong_meaning").VarName = "capacity[0]"
                target.model.update()
                path = legacy / vectors["primal"]["path"]
                path.write_bytes(path.read_bytes() + b"corrupt")
                with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                    read_legacy_checkpoint(target.model, root, allow_fingerprint_mismatch=True)
        finally:
            source.model.dispose()
            target.model.dispose()

    def test_named_raw_lp_violations_and_legacy_recovery(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, target = tiny_model(), tiny_model()
            try:
                archive_model(source.model, root)
                source.model.optimize()
                snapshot = save_numeric_snapshot(source.model, root)
                legacy = root / "barrier_checkpoint"
                legacy.mkdir()
                vectors = {}
                for role, attribute in (("primal", "BarX"), ("dual", "BarPi")):
                    row = snapshot["attributes"][attribute]
                    shutil.copy2(root / "solution_snapshot" / row["path"], legacy / row["path"])
                    vectors[role] = row
                ordering = {k: snapshot[k] for k in ("variables", "constraints", "nonzeros",
                           "gurobi_fingerprint", "variable_order_digest", "constraint_order_digest")}
                write_json(legacy / "barrier_checkpoint_manifest.json", {
                    "scientifically_accepted": False, "lp_ordering": ordering, "vectors": vectors})
                primal, dual = read_legacy_checkpoint(target.model, root)
                perturbed = np.array(primal)
                perturbed[0] = -1
                audit = audit_saved_primal(target.model, perturbed, violations_path=root / "violations.csv.gz")
                self.assertEqual(audit["status"], "FAIL")
                self.assertGreater(audit["violated_bound_count"], 0)
                self.assertIn("capacity[0]", pd.read_csv(root / "violations.csv.gz")["name"].tolist())
                self.assertNotEqual(float(primal[0]), -1)
                primal._mmap.close()
                dual._mmap.close()
            finally:
                source.model.dispose()
                target.model.dispose()

    def test_missing_dual_preserves_primal_and_marks_partial(self):
        source = tiny_model()
        try:
            source.model.optimize()
            class WithoutDual:
                def __getattr__(self, name):
                    return getattr(source.model, name)

                def getAttr(self, name, objects):
                    if name in {"BarPi", "Pi"}:
                        raise AttributeError("dual deliberately unavailable")
                    return source.model.getAttr(name, objects)
            with tempfile.TemporaryDirectory() as temporary:
                payload = save_numeric_snapshot(WithoutDual(), temporary)
                self.assertEqual(payload["status"], "PARTIAL")
                self.assertIsNotNone(payload["primal_attribute"])
                self.assertIsNone(payload["dual_attribute"])
                self.assertTrue((Path(temporary) / "solution_snapshot" / "BarX.npy").is_file())
        finally:
            source.model.dispose()

    def test_snapshot_rejects_rehashed_nonfinite_primal(self):
        source = tiny_model()
        try:
            source.model.optimize()
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                metadata = save_numeric_snapshot(source.model, root)
                snapshot_root = root / "solution_snapshot"
                primal_attribute = metadata["primal_attribute"]
                row = metadata["attributes"][primal_attribute]
                path = snapshot_root / row["path"]
                values = np.load(path)
                values[0] = np.nan
                np.save(path, values, allow_pickle=False)
                row["bytes"] = path.stat().st_size
                row["sha256"] = sha256_file(path)
                row["finite"] = True
                write_json(snapshot_root / "snapshot_manifest.json", metadata)
                with self.assertRaisesRegex(ValueError, "not finite"):
                    read_snapshot(source.model, snapshot_root)
        finally:
            source.model.dispose()

    def test_barrier_roundtrip_without_any_optimization_or_presolve(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = tiny_model()
            target = tiny_model()
            try:
                archive = archive_model(source.model, root, presolved=True)
                source.model.optimize()
                self.assertGreater(source.model.BarIterCount, 0)
                raw = save_numeric_snapshot(source.model, root)
                self.assertEqual(raw["status"], "COMPLETE")
                self.assertEqual(archive["status"], "COMPLETE", archive)
                self.assertFalse(archive["uncrush_mapping_saved"])
                original_path = next(row["path"] for row in archive["files"] if row["path"].startswith("original.mps"))
                reloaded = gp.read(str(root / "model_archive" / original_path))
                try:
                    archived_primal, archived_dual = read_snapshot(reloaded, root / "solution_snapshot")
                    np.testing.assert_allclose(archived_primal, source.variables["x"].BarX)
                    archived_primal._mmap.close()
                    archived_dual._mmap.close()
                finally:
                    reloaded.dispose()
                with patch.object(gp.Model, "optimize", side_effect=AssertionError("optimize forbidden")), \
                     patch.object(gp.Model, "presolve", side_effect=AssertionError("presolve forbidden")):
                    primal, dual = read_snapshot(target.model, root / "solution_snapshot")
                    view = offline_artifacts(target, primal, dual)
                    np.testing.assert_allclose(view.variables["x"].X, source.variables["x"].BarX)
                    np.testing.assert_allclose(view.variables["expr"].X, 2 * source.variables["x"].BarX + 1)
                    self.assertAlmostEqual(float(view.cost_components["cost"].getValue()), source.model.ObjVal)
                    np.testing.assert_allclose(view.index["balance"].BarPi, source.index["balance"].BarPi)
                self.assertEqual(target.model.SolCount, 0)
                target.variables["x"][0].VarName = "wrong_order_identity"
                target.model.update()
                with self.assertRaises(ValueError):
                    read_snapshot(target.model, root / "solution_snapshot")
                primal._mmap.close()
                dual._mmap.close()
            finally:
                source.model.dispose()
                target.model.dispose()

    def test_fail_qc_candidate_retains_small_negative_and_zero_values(self):
        config = load_model_config()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_json(root / "solution_qc.json", {"status": "FAIL", "hard_checks": {"balance": False}})
            write_json(root / "solve_report.json", {
                "status": "SUBOPTIMAL", "planning_year": 2030, "result_use": "TEST_ONLY_TRUNCATED_HORIZON",
                "solution_contract": {"mode": "OPTIMAL_PRIMAL_DUAL_NONBASIC", "acceptance_status": "HARD_FAIL"}})
            rows = pd.DataFrame([
                ["storage", str(i), 11, "battery", 2030, 2050, value, "GW", "new_build"]
                for i, value in enumerate([0., -1e-10, 2.])], columns=STATE_COLUMNS)
            state = write_planning_state(root, config=config, previous_state=PlanningState.empty(2025),
                                         new_cohorts=rows, source_solution_qc="solution_qc.json",
                                         state_use="TEST_ONLY_TRUNCATED_HORIZON", candidate=True)
            finalize_result_manifest(root, config)
            with self.assertRaisesRegex(ValueError, "explicit"):
                PlanningState.load(state, expected_boundary_year=2030, allow_test_only=True)
            loaded = PlanningState.load(state, expected_boundary_year=2030, allow_test_only=True,
                                        allow_unaccepted_candidate=True)
            np.testing.assert_array_equal(loaded.cohorts.capacity_delta, rows.capacity_delta)
            self.assertFalse(loaded.metadata["scientifically_accepted"])
            write_json(root / "solution_qc.json", {"status": "PASS"})
            with self.assertRaisesRegex(ValueError, "SHA256"):
                PlanningState.load(state, expected_boundary_year=2030, allow_test_only=True,
                                   allow_unaccepted_candidate=True)

    def test_accepted_stage_a_can_retain_every_finite_capacity_delta(self):
        config = load_model_config()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_json(root / "solution_qc.json", {
                "status": "PASS", "hard_checks": {"balance": True}
            })
            write_json(root / "solve_report.json", {
                "status": "OPTIMAL",
                "planning_year": 2030,
                "result_use": "SCIENTIFIC_PRODUCTION",
                "solver_profile_id": "barrier_stagea_final_full_year_cloud_v6_threads32",
                "formulation_profile_id": "annual_capacity_link_rows_8192_v1",
                "solution_contract": {
                    "mode": "OPTIMAL_BASIC_OR_DEFAULT",
                    "relative_primal_dual_objective_gap": 1e-2,
                },
            })
            rows = pd.DataFrame([
                ["storage", str(i), 11, "battery", 2030, 2050, value, "GW", "new_build"]
                for i, value in enumerate([0.0, -1e-10, 2.0])
            ], columns=STATE_COLUMNS)
            state = write_planning_state(
                root,
                config=config,
                previous_state=PlanningState.empty(2025),
                new_cohorts=rows,
                source_solution_qc="solution_qc.json",
                state_use="SCIENTIFIC_PRODUCTION",
                retain_all_capacity_deltas=True,
            )
            finalize_result_manifest(root, config)
            loaded = PlanningState.load(state, expected_boundary_year=2030)
            np.testing.assert_array_equal(
                loaded.cohorts.capacity_delta, rows.capacity_delta
            )
            self.assertTrue(loaded.metadata["retain_all_capacity_deltas"])
            self.assertEqual(loaded.metadata["omitted_small_new_cohort_rows"], 0)

    def test_failed_export_does_not_suppress_other_stages_or_manifest(self):
        config = load_model_config()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = {"status": "OPTIMAL", "result_use": "TEST_ONLY_TRUNCATED_HORIZON"}
            qc = {"status": "FAIL", "hard_checks": {"balance": False}}
            with patch("cispo_model.master.export_master_solution", side_effect=RuntimeError("disk stage failed")), \
                 patch("cispo_model.solution_export.export_operational_solution", return_value=qc) as operation, \
                 patch("cispo_model.result_summary.export_result_summary") as summary, \
                 patch("cispo_model.planning_state.export_solution_planning_state") as state:
                result = preserve_stage_a(None, None, config, root, report, snapshot=False)
            finalize_result_manifest(root, config)
            self.assertEqual(result["status"], "PARTIAL")
            operation.assert_called_once()
            summary.assert_called_once()
            self.assertTrue(state.call_args.kwargs["candidate"])
            self.assertFalse(operation.call_args.kwargs["enforce_qc"])
            manifest = json.loads((root / "result_manifest.json").read_text())
            self.assertFalse(manifest["scientifically_accepted"])
            self.assertEqual(manifest["qc_status"], "FAIL")
            self.assertTrue(validate_result_manifest(root)[0])

    def test_reused_complete_checkpoint_counts_as_complete_preservation(self):
        config = load_model_config()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkpoint = root / "barrier_checkpoint"
            checkpoint.mkdir()
            write_json(
                checkpoint / "barrier_checkpoint_manifest.json",
                {"checkpoint_status": "ENGINEERING_BARRIER_CHECKPOINT"},
            )
            report = {
                "status": "OPTIMAL",
                "result_use": "TEST_ONLY_TRUNCATED_HORIZON",
            }
            qc = {"status": "PASS", "hard_checks": {"balance": True}}
            with patch(
                "cispo_model.primal_dual_checkpoint.validate_checkpoint_vector_integrity",
                return_value=(True, []),
            ), patch(
                "cispo_model.master.export_master_solution",
                return_value={},
            ), patch(
                "cispo_model.solution_export.export_operational_solution",
                return_value=qc,
            ), patch(
                "cispo_model.result_summary.export_result_summary"
            ), patch(
                "cispo_model.planning_state.export_solution_planning_state"
            ):
                result = preserve_stage_a(
                    None, None, config, root, report, snapshot=False
                )
            self.assertEqual(result["status"], "COMPLETE")
            self.assertEqual(result["stages"]["raw_checkpoint"], "COMPLETE")
            self.assertEqual(
                result["raw_checkpoint_source"],
                "REUSED_EXISTING_CHECKPOINT",
            )

    def test_invalid_reused_checkpoint_cannot_report_complete_preservation(self):
        config = load_model_config()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkpoint = root / "barrier_checkpoint"
            checkpoint.mkdir()
            write_json(
                checkpoint / "barrier_checkpoint_manifest.json",
                {"checkpoint_status": "PENDING_ORIGINAL_UNIT_QC"},
            )
            report = {
                "status": "OPTIMAL",
                "result_use": "TEST_ONLY_TRUNCATED_HORIZON",
            }
            qc = {"status": "PASS", "hard_checks": {"balance": True}}
            with patch(
                "cispo_model.master.export_master_solution",
                return_value={},
            ), patch(
                "cispo_model.solution_export.export_operational_solution",
                return_value=qc,
            ), patch(
                "cispo_model.result_summary.export_result_summary"
            ), patch(
                "cispo_model.planning_state.export_solution_planning_state"
            ):
                result = preserve_stage_a(
                    None, None, config, root, report, snapshot=False
                )
            self.assertEqual(result["status"], "PARTIAL")
            self.assertEqual(result["stages"]["raw_checkpoint"], "ERROR")
            self.assertEqual(
                result["raw_checkpoint_source"],
                "REJECTED_INVALID_EXISTING_CHECKPOINT",
            )
            self.assertTrue(
                any(
                    row["stage"] == "raw_checkpoint"
                    for row in result["errors"]
                )
            )


if __name__ == "__main__":
    unittest.main()
