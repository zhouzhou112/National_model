"""Prelaunch fault injection. No optimize, presolve or relaxation is permitted."""
from __future__ import annotations

import json
import tempfile
import unittest
import os
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import gurobipy as gp
import numpy as np

from cispo_model.config import load_model_config
from cispo_model.offline_solution import read_snapshot, audit_saved_primal
from cispo_model.solution_preservation import (
    archive_model, save_numeric_snapshot, preserve_stage_a, preserve_solver_exception,
    inspect_recovery_files, write_json,
)
from cispo_model.primal_dual_checkpoint import (
    export_barrier_primal_dual_checkpoint, validate_barrier_primal_dual_checkpoint,
    prepare_primal_dual_crossover, apply_primal_dual_crossover_start, PrimalDualCheckpointError,
)
import test_primal_dual_checkpoint as checkpoint_tests
from test_primal_dual_checkpoint import FakeModel
from test_solution_preservation import tiny_model


class VectorModel:
    """Expose deliberately infeasible saved values on an unsolved real LP."""
    def __init__(self, model, primal=(8., 9.), dual=(1., 2.)):
        self.model, self.primal, self.dual = model, primal, dual

    def __getattr__(self, key):
        return getattr(self.model, key)

    def getAttr(self, key, objects=None):
        if key in ("BarX", "X", "BarPi", "Pi"):
            values = self.primal if key in ("BarX", "X") else self.dual
            if values is None:
                raise AttributeError(key)
            return list(values)
        return self.model.getAttr(key, objects)


class FinalPreservationNoSolveTests(unittest.TestCase):
    def setUp(self):
        for name in ("optimize", "optimizeAsync", "presolve", "feasRelax", "feasRelaxS"):
            if hasattr(gp.Model, name):
                guard = patch.object(gp.Model, name, side_effect=AssertionError(name + " FORBIDDEN"))
                guard.start()
                self.addCleanup(guard.stop)

    def model(self):
        artifacts = tiny_model()
        self.addCleanup(artifacts.model.dispose)
        return artifacts

    def test_violating_vector_and_archive_roundtrip_and_corruption_rejection(self):
        artifacts = self.model()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = archive_model(artifacts.model, root)
            self.assertEqual(archive["status"], "COMPLETE")
            snapshot = save_numeric_snapshot(VectorModel(artifacts.model), root)
            self.assertEqual(snapshot["status"], "COMPLETE")
            primal, dual = read_snapshot(artifacts.model, root / "solution_snapshot")
            self.assertEqual(audit_saved_primal(artifacts.model, primal)["status"], "FAIL")
            np.testing.assert_array_equal(primal, [8., 9.])
            primal._mmap.close()
            dual._mmap.close()
            archived_path = next(root / "model_archive" / f["path"] for f in archive["files"]
                                 if f["path"].startswith("original.mps"))
            rebuilt = gp.read(str(archived_path))
            try:
                self.assertEqual(rebuilt.Fingerprint, artifacts.model.Fingerprint)
            finally:
                rebuilt.dispose()
            readiness = inspect_recovery_files(root)
            self.assertTrue(readiness["model_archive_complete"])
            self.assertTrue(readiness["finite_primal_dual_saved"])
            self.assertFalse(readiness["barrier_hot_resume"])
            path = root / "solution_snapshot" / "BarX.npy"
            path.write_bytes(path.read_bytes() + b"corrupt")
            self.assertFalse(inspect_recovery_files(root)["finite_primal_dual_saved"])
            with self.assertRaises(ValueError):
                read_snapshot(artifacts.model, root / "solution_snapshot")

    def test_nonfinite_and_absent_vectors_still_preserve_model_and_raw_evidence(self):
        for primal, dual in (((float("nan"), 9.), (1., 2.)), (None, None)):
            with self.subTest(primal=primal), tempfile.TemporaryDirectory() as tmp:
                root, artifacts = Path(tmp), self.model()
                archive_model(artifacts.model, root)
                snapshot = save_numeric_snapshot(VectorModel(artifacts.model, primal, dual), root)
                self.assertEqual(snapshot["status"], "PARTIAL")
                self.assertTrue(inspect_recovery_files(root)["model_archive_complete"])
                self.assertFalse(inspect_recovery_files(root)["finite_primal_dual_saved"])
                if primal is not None:
                    self.assertTrue(np.isnan(np.load(root / "solution_snapshot" / "BarX.npy")[0]))

    def semantic_mocks(self):
        from contextlib import ExitStack
        stack = ExitStack()
        self.addCleanup(stack.close)
        paths = {"capacity": "cispo_model.master.export_master_solution",
                 "operation": "cispo_model.solution_export.export_operational_solution",
                 "summary": "cispo_model.result_summary.export_result_summary",
                 "state": "cispo_model.planning_state.export_solution_planning_state",
                 "catalog": "cispo_model.io_contract.write_output_catalog"}
        mocks = {key: stack.enter_context(patch(path)) for key, path in paths.items()}
        mocks["operation"].side_effect = ValueError("injected semantic export failure")
        return mocks

    def test_corrupt_qc_does_not_skip_summary_state_or_catalog(self):
        artifacts = self.model()
        mocks = self.semantic_mocks()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_model(artifacts.model, root)
            (root / "solution_qc.json").write_text('{"partial":')
            (root / "dual_export_status.json").write_text("[]")
            result = preserve_stage_a(artifacts, None, None, root,
                                     {"result_use": "TEST_ONLY_TRUNCATED_HORIZON"}, snapshot=False)
            self.assertEqual(result["status"], "PARTIAL")
            for key in ("summary", "state", "catalog"):
                mocks[key].assert_called_once()
            self.assertTrue(mocks["state"].call_args.kwargs["candidate"])
            self.assertTrue(any(row["stage"] == "read_solution_qc.json" for row in result["errors"]))

    def test_solver_exception_preserves_vectors_before_failing_semantics(self):
        artifacts = self.model()
        artifacts.model = VectorModel(artifacts.model)
        mocks = self.semantic_mocks()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_model(artifacts.model, root)
            result = preserve_solver_exception(artifacts, None, None, root, RuntimeError("solver failed"),
                scope={"result_use": "TEST_ONLY_TRUNCATED_HORIZON"})
            self.assertEqual(result["status"], "PARTIAL")
            self.assertTrue(inspect_recovery_files(root)["finite_primal_dual_saved"])
            self.assertEqual(json.loads((root / "raw_lp_qc.json").read_text())["status"], "FAIL")
            report = json.loads((root / "solve_report.json").read_text())
            self.assertFalse(report["scientifically_accepted"])
            self.assertEqual(report["status"], "SOLVER_EXCEPTION")
            mocks["catalog"].assert_called_once()
            for mocked in mocks.values():
                mocked.reset_mock(side_effect=True)
            import gc
            gc.collect()  # Release mock-held offline memmaps before Windows cleanup.

    def test_optimizer_exception_closes_telemetry_under_installed_signal_guard(self):
        from cispo_model.diagnostics import solve_and_report
        from contextlib import contextmanager
        active = []
        @contextmanager
        def termination(*args):
            active.append(True)
            try:
                yield SimpleNamespace(received_signal=None)
            finally:
                active.clear()
        model = SimpleNamespace(Status=11, Runtime=1., Work=0.)
        def fail(*args):
            self.assertTrue(active)
            raise RuntimeError("injected solver exception")
        model.optimize = fail  # A fake callback, never Gurobi.optimize.
        with tempfile.TemporaryDirectory() as tmp, patch("cispo_model.diagnostics.configure_gurobi"), \
             patch("cispo_model.diagnostics.model_statistics", return_value={}), \
             patch("cispo_model.diagnostics.GracefulSolverTermination", termination):
            with self.assertRaisesRegex(RuntimeError, "injected"):
                solve_and_report(model, None, Path(tmp))
            events = [json.loads(line)["event"] for line in
                      (Path(tmp) / "solver_telemetry.jsonl").read_text().splitlines()]
            self.assertEqual(events, ["solver_start", "solver_end"])

    def test_raw_exception_snapshot_has_explicit_same_lp_start_path(self):
        config, artifacts = load_model_config(), self.model()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save_numeric_snapshot(VectorModel(artifacts.model), root)
            scope = dict(planning_year=config.planning_year, optimization_hours=24,
                         optimization_start_hour=0, result_use="TEST_ONLY_TRUNCATED_HORIZON",
                         scenario_id=config.raw["scenario"]["id"])
            write_json(root / "solve_report.json", dict(scope, status="SOLVER_EXCEPTION"))
            kwargs = {key: scope[key] for key in ("optimization_hours", "optimization_start_hour", "result_use")}
            with self.assertRaisesRegex(PrimalDualCheckpointError, "explicit"):
                prepare_primal_dual_crossover(root, root, artifacts.model, config, **kwargs)
            with patch("cispo_model.offline_solution.verify_recovery_inputs", return_value={"identity_validated": True}):
                prepared = prepare_primal_dual_crossover(root, root, artifacts.model, config,
                                                        allow_recovery_checkpoint=True, **kwargs)
                self.assertFalse(prepared["source_scientifically_accepted"])
                apply_primal_dual_crossover_start(artifacts.model, prepared)
                self.assertEqual(artifacts.model.Params.LPWarmStart, 2)
                np.testing.assert_array_equal(np.load(prepared["primal_path"]), [8., 9.])
                with self.assertRaisesRegex(PrimalDualCheckpointError, "optimization_start_hour"):
                    prepare_primal_dual_crossover(root, root, artifacts.model, config, allow_recovery_checkpoint=True,
                                                 **dict(kwargs, optimization_start_hour=1))

    def test_wrapper_signal_waits_for_exporter_to_exit(self):
        wrapper = Path("scripts/run_cloud_portfolio_job.sh").read_text()
        git = Path(shutil.which("git"))
        bash = git.parent.parent / "bin" / "bash.exe" if os.name == "nt" else Path(shutil.which("bash"))
        self.assertTrue(bash.is_file(), "Bash required for wrapper signal self-check")
        subprocess.run([str(bash), "-n", "scripts/run_cloud_portfolio_job.sh"], check=True, timeout=5)
        function = wrapper.split("forward_signal() {", 1)[1].split("trap 'forward_signal TERM'", 1)[0]
        wait = wrapper.split('set +e\nwait "$runner_pid"', 1)[1].split("set -e", 1)[0]
        with tempfile.TemporaryDirectory() as tmp:
            script = ('control_root="$TEST_ROOT"\nforward_signal() {' + function +
                # Simulate Bash's interrupted-wait return deterministically;
                # native POSIX signal delivery is not portable on Windows.
                'wait_called=0\nwait() { if [[ "$wait_called" == 0 ]]; then wait_called=1; '
                'forward_signal TERM; return 143; else builtin wait "$@"; fi; }\n' +
                '(sleep 0.2; touch "$control_root/export_complete"; exit 7) &\nrunner_pid=$!\n' +
                'set +e\nwait "$runner_pid"' + wait + '\nexit "$runner_rc"\n')
            result = subprocess.run([str(bash), "--noprofile", "--norc", "-c", script],
                env=dict(os.environ, TEST_ROOT=Path(tmp).as_posix()), capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 7, result.stderr)
            self.assertTrue((Path(tmp) / "STOP_REQUESTED").is_file())
            self.assertTrue((Path(tmp) / "export_complete").is_file())

    def test_failed_qc_and_interrupted_starts_require_explicit_exact_lp_gate(self):
        config = load_model_config(solver_path="config/solver_profiles/barrier_16_nonbasic_primal_dual_v1.json")
        for pending in (False, True):
            with self.subTest(pending=pending), tempfile.TemporaryDirectory() as tmp, \
                 patch("cispo_model.primal_dual_checkpoint.validate_input_manifest", return_value=(True, [])):
                root = Path(tmp)
                identity = {key: {"id": key} for key in ("baseline_contract", "analysis_case", "scientific_case",
                                                        "implementation_bundle", "data_roots")}
                identity["lp_model"] = {"gurobi_fingerprint": 123, "variables": 3, "constraints": 2, "nonzeros": 4}
                write_json(root / "run_identity.json", identity)
                write_json(root / "run_environment.json", {"packages": {"gurobipy": "13.0.2"}})
                write_json(root / "run_scope.json", {"result_use": "SCIENTIFIC_PRODUCTION"})
                checkpoint_tests.PrimalDualCheckpointTests._write_input_manifest(root)
                report = {"status": "OPTIMAL" if pending else "INTERRUPTED", "status_code": 2 if pending else 11,
                          "objective_value_million_cny": 1., "solution_quality": {"maximum_constraint_violation": 0.},
                          "iteration_counts": {"barrier": 7}, "runtime_seconds": 1.,
                          "solver_parameters": {"method": 2, "crossover": 0, "solution_target": 1},
                          "solution_contract": {"mode": "OPTIMAL_PRIMAL_DUAL_NONBASIC",
                                                "acceptance_status": "PASS" if pending else "FAIL",
                                                "barrier_status_code": 2 if pending else 11}}
                write_json(root / "solve_report.json", report)
                write_json(root / "solution_qc.json", {"status": "FAIL"})
                export_barrier_primal_dual_checkpoint(FakeModel(), config, root, solve_report=report,
                    optimization_hours=8760, optimization_start_hour=0, result_use="SCIENTIFIC_PRODUCTION",
                    solution_qc=None, accepted_primary=False, pending_qc=pending,
                    allow_incomplete_barrier=not pending)
                valid, _ = validate_barrier_primal_dual_checkpoint(root, require_result_manifest=False)
                self.assertFalse(valid)
                kwargs = dict(optimization_hours=8760, optimization_start_hour=0, result_use="SCIENTIFIC_PRODUCTION")
                with self.assertRaisesRegex(PrimalDualCheckpointError, "explicit"):
                    prepare_primal_dual_crossover(root, root, FakeModel(), config, **kwargs)
                prepared = prepare_primal_dual_crossover(root, root, FakeModel(), config,
                                                        allow_recovery_checkpoint=True, **kwargs)
                self.assertFalse(prepared["source_scientifically_accepted"])
                target = FakeModel()
                apply_primal_dual_crossover_start(target, prepared)
                np.testing.assert_equal(target.assigned["PStart"], [1., 2., 3.])
                target.Fingerprint = 456
                with self.assertRaisesRegex(PrimalDualCheckpointError, "Fingerprint"):
                    prepare_primal_dual_crossover(root, root, target, config, allow_recovery_checkpoint=True, **kwargs)
                with self.assertRaisesRegex(PrimalDualCheckpointError, "optimization_start_hour"):
                    prepare_primal_dual_crossover(root, root, FakeModel(), config, allow_recovery_checkpoint=True,
                        **dict(kwargs, optimization_start_hour=1))
                path = root / "barrier_checkpoint" / "primal_barx.npy"
                path.write_bytes(path.read_bytes() + b"corrupt")
                with self.assertRaisesRegex(PrimalDualCheckpointError, "not eligible"):
                    prepare_primal_dual_crossover(root, root, FakeModel(), config, allow_recovery_checkpoint=True, **kwargs)


if __name__ == "__main__":
    unittest.main()
